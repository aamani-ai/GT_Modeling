"""Build the REAL monthly forecast panel JSON for Section 01.

Mirrors notebook 06 (notebooks/06_forward_scenarios.py §5) exactly:

  - For each grid cell (policy × gas multiplier × init-state preset), runs the
    forward engine with `return_paths=True` so we keep per-path daily series:
      r["lmp_daily"], r["gas_daily"], r["daily"]["mwh_degraded"],
      r["daily"]["margin_degraded"].
  - Aggregates each path to Apr→Mar monthly arrays:
      LMP/gas = monthly mean, MWh/margin = monthly sum.
  - Across paths, computes probability-weighted P10/P50/P90 at each month using
    `forward.run.weighted_quantile` (the same helper notebook 06 imports).
  - Builds a CDF over real per-path annual Net P&L.
  - Loads SEAS5 raw JSON `data/paths/lockport/weather_forecast_seas5.json` and
    computes daily P10/P50/P90 across the 51 ensemble members (the
    conditioning signal).

Output: apps/gt-digital-twin/web/client/public/monthly_forecast_panel.json

No illustrative shapes. No idealized seasonality weights. Every series in the
chart is computed from real run_forward / SEAS5 data.

Run from repo root:
    python apps/gt-digital-twin/scripts/build_monthly_forecast_panel.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import gt_engine.engine as eng  # noqa: E402
from forward.select import select  # noqa: E402
from forward.build import build_scenarios  # noqa: E402
from forward.data import load_market  # noqa: E402
from forward.run import LTSA_KEYS, weighted_quantile  # noqa: E402


BASIS = "RT"
MODES = ["A", "B", "C"]
GAS_MULTS = [0.75, 1.0, 1.25]
SEED = 42

MONTH_ORDER = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]  # Apr -> Mar
MONTH_LABEL = ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
               "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

SEAS5_PATH = ROOT / "data" / "paths" / "lockport" / "weather_forecast_seas5.json"
OUT_DIR = Path(__file__).resolve().parents[1] / "web" / "client" / "public"
OUT_PATH = OUT_DIR / "monthly_forecast_panel.json"
DIST_PATH = (Path(__file__).resolve().parents[1] / "web" / "dist"
             / "public" / "monthly_forecast_panel.json")


# ---------- helpers (mirror notebook 06 exactly) ----------

def _scn_monthly_series(s: pd.Series, agg: str) -> dict[int, float]:
    """Series indexed by datetime -> {month: agg}."""
    g = s.groupby(pd.DatetimeIndex(s.index).month).agg(agg)
    return {int(k): float(v) for k, v in g.items()}


def _scn_monthly_df(df: pd.DataFrame, col: str, agg: str) -> dict[int, float]:
    """Engine daily DataFrame (with 'date' col) -> {month: agg}."""
    d = df.copy()
    d["m"] = pd.to_datetime(d["date"]).dt.month
    g = d.groupby("m")[col].agg(agg)
    return {int(k): float(v) for k, v in g.items()}


def _fan(per_scn: list[dict[int, float]], probs: list[float]) -> dict[str, list[float]]:
    """Per-scenario monthly dicts -> P10/P50/P90 arrays in Apr->Mar order."""
    P = {0.1: [], 0.5: [], 0.9: []}
    probs_arr = np.array(probs, float)
    for mo in MONTH_ORDER:
        vals = np.array([d.get(mo, np.nan) for d in per_scn], float)
        mask = ~np.isnan(vals)
        for qq in P:
            if mask.sum():
                P[qq].append(float(weighted_quantile(vals[mask], probs_arr[mask], qq)))
            else:
                P[qq].append(float("nan"))
    return {"P10": P[0.1], "P50": P[0.5], "P90": P[0.9]}


def _per_path_monthly(paths: list[dict], col_kind: str) -> list[dict[int, float]]:
    """col_kind in {"lmp", "gas", "mwh", "margin"} -> per-path monthly dicts."""
    if col_kind == "lmp":
        return [_scn_monthly_series(p["lmp_daily"], "mean") for p in paths]
    if col_kind == "gas":
        return [_scn_monthly_series(p["gas_daily"], "mean") for p in paths]
    if col_kind == "mwh":
        return [_scn_monthly_df(p["daily"], "mwh_degraded", "sum") for p in paths]
    if col_kind == "margin":
        return [_scn_monthly_df(p["daily"], "margin_degraded", "sum") for p in paths]
    raise ValueError(col_kind)


def _build_cdf(per_path_records: list[dict]) -> list[dict]:
    """Real probability-weighted CDF over per-path annual Net P&L."""
    s = sorted(per_path_records, key=lambda p: p["net_pl_usd"])
    total_w = sum(p["probability"] for p in s)
    out = []
    acc = 0.0
    for p in s:
        acc += p["probability"]
        out.append({
            "x": float(p["net_pl_usd"]),
            "F": float(acc / total_w),
            "window": p["source_window_id"],
            "path_id": int(p["path_id"]),
        })
    return out


# ---------- engine driver ----------

def _run_grid_cell(mode, gas_mult, init_preset, sel, scen, lmp_full, wx_full, henry,
                   aged_states):
    """Run forward grid cell with per-path daily series retained."""
    init_override = aged_states[mode] if init_preset == "aged" else None
    h = henry.copy()
    if gas_mult != 1.0:
        h["price_usd_per_mmbtu"] = h["price_usd_per_mmbtu"] * gas_mult

    paths = []
    rows = []
    for s in scen.itertuples(index=False):
        sim_start = s.sim_start
        sim_end = s.sim_end
        sim_dates = pd.date_range(sim_start, sim_end - pd.Timedelta(days=1), freq="D")
        lmp_w = lmp_full[(lmp_full["datetime_local"] >= sim_start)
                        & (lmp_full["datetime_local"] < sim_end)].reset_index(drop=True)
        wx_w = wx_full.loc[(wx_full.index >= sim_start) & (wx_full.index < sim_end)]
        with contextlib.redirect_stdout(io.StringIO()):
            r = eng.run_path(mode, SEED, sim_dates, sim_start, sim_end, lmp_w, wx_w, h,
                             init_state_override=init_override)
        d = r["daily"]
        spark = float(d["margin_degraded"].sum())
        ltsa = float(sum(r["final_ltsa"][k] for k in LTSA_KEYS))
        # Daily input series (verbatim from forward.run.run_forward)
        lw = lmp_w.copy(); lw["d"] = lw["datetime_local"].dt.normalize()
        lmp_daily = lw.groupby("d")["price"].mean()
        gd = h.copy(); gd["dt"] = pd.to_datetime(gd["trade_date_dt"])
        gd = gd.groupby("dt")["price_usd_per_mmbtu"].mean().sort_index()
        gas_daily = gd.reindex(pd.date_range(sim_start.tz_localize(None),
                                              sim_end.tz_localize(None) - pd.Timedelta(days=1))).ffill()
        paths.append({
            "source_window_id": str(s.source_window_id),
            "probability": float(s.probability),
            "daily": d,
            "lmp_daily": lmp_daily,
            "gas_daily": gas_daily,
        })
        rows.append({
            "path_id": int(s.path_id),
            "source_window_id": str(s.source_window_id),
            "probability": float(s.probability),
            "spark_margin_usd": spark,
            "ltsa_owner_usd": ltsa,
            "net_pl_usd": spark - ltsa,
            "total_mwh": float(d["mwh_degraded"].sum()),
            "fired_hours": int(d["fired_hours"].sum()),
        })
    return paths, rows


def _aggregate_cell(paths, rows):
    """Build the monthly Apr->Mar envelopes and CDF for one grid cell."""
    probs = [p["probability"] for p in paths]
    lmp_envelope = _fan(_per_path_monthly(paths, "lmp"), probs)
    gas_envelope = _fan(_per_path_monthly(paths, "gas"), probs)
    mwh_envelope = _fan(_per_path_monthly(paths, "mwh"), probs)
    margin_envelope = _fan(_per_path_monthly(paths, "margin"), probs)
    cdf = _build_cdf(rows)
    return {
        "lmp_usd_per_mwh_monthly_mean": lmp_envelope,
        "henry_hub_usd_per_mmbtu_monthly_mean": gas_envelope,
        "generation_mwh_monthly_sum": mwh_envelope,
        "gross_margin_usd_monthly_sum": margin_envelope,
        "net_pl_cdf": cdf,
    }


# ---------- SEAS5 ensemble ----------

def _seas5_temperature_ensemble():
    """Load SEAS5 raw JSON and compute daily P10/P50/P90 across 51 members.

    Mirrors notebook 06 exactly:
        _var = seas5["data"]["temperature_2m"]
        _times = pd.to_datetime(_var["time"])
        _arr = np.array([_var["data"][0]["values"][k] for k in _var["data"][0]["values"]], float) * 9/5 + 32
        np.nanpercentile(_arr, [10, 50, 90], axis=0)
    """
    seas5 = json.loads(SEAS5_PATH.read_text())
    var = seas5["data"]["temperature_2m"]
    times = pd.to_datetime(var["time"])
    arr = np.array(
        [var["data"][0]["values"][k] for k in var["data"][0]["values"]], float
    ) * 9.0 / 5.0 + 32.0  # Celsius -> Fahrenheit
    p10 = np.nanpercentile(arr, 10, axis=0)
    p50 = np.nanpercentile(arr, 50, axis=0)
    p90 = np.nanpercentile(arr, 90, axis=0)
    return {
        "dates": [t.isoformat() for t in times],
        "P10": [float(v) for v in p10],
        "P50": [float(v) for v in p50],
        "P90": [float(v) for v in p90],
        "n_members": int(arr.shape[0]),
        "source_file": str(SEAS5_PATH.relative_to(ROOT)),
    }


# ---------- main ----------

def main():
    t_start = time.time()
    print("=== Selecting & building scenarios ===", flush=True)
    sel = select(basis=BASIS)
    scen = build_scenarios(sel, basis=BASIS)
    print(f"  n_scenarios={len(scen)}", flush=True)

    lmp_full, wx_full, henry = load_market(BASIS)

    print("=== Loading SEAS5 temperature ensemble ===", flush=True)
    temperature_panel = _seas5_temperature_ensemble()
    print(f"  members={temperature_panel['n_members']}, days={len(temperature_panel['dates'])}", flush=True)

    print("=== Running each mode's aged historical end-state ===", flush=True)
    aged_states = {}
    for m in MODES:
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            r = eng.run_mode(m)
        aged_states[m] = r["final_state"]
        print(f"  mode {m}: aged eoh={aged_states[m].eoh:.0f}  ({time.time()-t0:.1f}s)", flush=True)

    combos = (
        [(m, gm, "aged") for m in MODES for gm in GAS_MULTS]
        + [("A", 1.0, "fresh"), ("B", 1.0, "fresh"), ("C", 1.0, "fresh")]
    )

    grid = {}
    print(f"=== Sweeping forward grid ({len(combos)} cells × {len(scen)} paths) ===", flush=True)
    for i, (m, gm, ip) in enumerate(combos, 1):
        t0 = time.time()
        paths, rows = _run_grid_cell(m, gm, ip, sel, scen, lmp_full, wx_full, henry, aged_states)
        cell = _aggregate_cell(paths, rows)
        cell["knobs"] = {"policy": m, "gas_mult": gm, "init_state": ip}
        key = f"{m}|gas{gm}|{ip}"
        grid[key] = cell
        cdf_p50 = cell["net_pl_cdf"][len(cell["net_pl_cdf"]) // 2]["x"] / 1e6
        print(f"  [{i}/{len(combos)}] {key}: ~mid Net P&L ${cdf_p50:.2f}M  ({time.time()-t0:.1f}s)",
              flush=True)

    payload = {
        "schema_version": "v1.3-real-monthly",
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "basis": BASIS,
        "seed": SEED,
        "n_scenarios": int(len(scen)),
        "seas5_init": sel.seas5_init,
        "month_labels": MONTH_LABEL,
        "month_order": MONTH_ORDER,
        "provenance": {
            "engine": "src.gt_engine.engine.run_path (verbatim from N4)",
            "forward": "src.forward.run.run_forward(..., return_paths=True) — re-implemented inline so daily series are retained per path",
            "weighted_quantile": "src.forward.run.weighted_quantile (probability-weighted, used in notebook 06)",
            "weights": "SEAS5 softmax probabilities from forward.select.select (basis=RT)",
            "aggregation": {
                "lmp_usd_per_mwh_monthly_mean": "per-path: groupby(month).mean of lmp_daily; across paths: weighted_quantile(P10/P50/P90) at each month",
                "henry_hub_usd_per_mmbtu_monthly_mean": "per-path: groupby(month).mean of gas_daily; across paths: weighted_quantile(P10/P50/P90) at each month",
                "generation_mwh_monthly_sum": "per-path: groupby(month).sum of daily.mwh_degraded; across paths: weighted_quantile(P10/P50/P90) at each month",
                "gross_margin_usd_monthly_sum": "per-path: groupby(month).sum of daily.margin_degraded; across paths: weighted_quantile(P10/P50/P90) at each month",
                "net_pl_cdf": "real per-path annual Net P&L sorted, cumulative SEAS5 probability",
                "temperature_f_daily": f"SEAS5 {temperature_panel['n_members']}-member ensemble daily P10/P50/P90 from data/paths/lockport/weather_forecast_seas5.json (the conditioning signal)",
            },
            "notebook_mirror": "notebooks/06_forward_scenarios.py §5 (lines 167-255)",
        },
        "temperature_f_daily": temperature_panel,
        "grid": grid,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2,
                                   default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o)))
    print(f"=== Wrote {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.0f} KB) ===", flush=True)

    # Copy to dist if present so already-built bundles also serve the new file
    if DIST_PATH.parent.exists():
        DIST_PATH.write_text(OUT_PATH.read_text())
        print(f"=== Copied to {DIST_PATH} ===", flush=True)

    print(f"Total {time.time()-t_start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
