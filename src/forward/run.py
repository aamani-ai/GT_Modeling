"""Forward run — execute the engine over each scenario path; aggregate to P10/P50/P90.

For each eligible Apr->Mar window (a scenario), run gt_engine.run_path over the window's
native dates (fixed seed) and collect the 1-year economics. Then compute
PROBABILITY-WEIGHTED quantiles across scenarios (weights = the temperature-analog
selection probabilities from select.py).

Initial state (ADR-009): by default each scenario starts from the AGED historical
end-state for that mode (run_mode(mode)["final_state"], EOH near the inspection
threshold), NOT a fresh plant. This is what makes the A/B/C preservation premium bind
in the forward — a fresh 1-yr start parks EOH ~20k hours from any threshold, where the
premium is inert and A=B=C. Pass aged_start=False to recover the old fresh-start behavior.

v1 scope (per forward_engine_plan.md): DA basis, raw historical levels, scenario-driven
uncertainty only. NOT yet included: engine-RNG Monte Carlo (run each window x many seeds),
forward-price anchoring, behavioral output (#3). Each scenario uses a fixed seed, so the
spread here reflects WHICH future (price/gas/weather analog), not outage-draw noise.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make src/ importable

# The engine prints data-spine/config diagnostics on import (useful for the historical
# driver, noise here). Suppress them for the forward run.
with contextlib.redirect_stdout(io.StringIO()):
    import gt_engine.engine as eng      # noqa: E402  (run_path lives here)
from forward.build import build_scenarios   # noqa: E402
from forward.select import select, DEFAULT_BASIS   # noqa: E402
from forward.data import load_market           # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "outputs" / "lockport" / "forward_runs"
TZ = "US/Eastern"
LTSA_KEYS = ["fixed_fee_cum", "eoh_reserve_cum", "ci_owner_cum", "mi_owner_cum",
             "overage_cum", "avail_penalty_cum", "hr_penalty_cum", "outage_forced_cum"]


def weighted_quantile(values, weights, q):
    """Probability-weighted quantile (values need not be sorted)."""
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = (np.cumsum(w) - 0.5 * w) / w.sum()   # centered cumulative weight
    return float(np.interp(q, cum, v))


def run_forward(mode: str = "A", seed: int = 42, basis: str = DEFAULT_BASIS, save: bool = True,
                return_paths: bool = False, aged_start: bool = True) -> dict:
    sel = select(basis=basis)
    scen = build_scenarios(sel, basis=basis)
    # Full-range market for the chosen basis (RT reaches back to 1999, unlike the
    # engine's pre-sliced 2017-2025 historical windows). Sliced per scenario below.
    lmp_full, wx_full, henry = load_market(basis)

    # ADR-009: seed each scenario from the aged historical end-state for THIS mode
    # (EOH near the inspection threshold) so the A/B/C premium binds. Computed once
    # (one historical replay over the module-level 2017-2025 windows), reused across
    # scenarios; run_path takes a defensive copy so the object is not mutated.
    init_override = None
    if aged_start:
        with contextlib.redirect_stdout(io.StringIO()):
            init_override = eng.run_mode(mode)["final_state"]

    rows = []
    paths_detail = []   # per-scenario daily series (for visualization), if return_paths
    for s in scen.itertuples(index=False):
        sim_start = s.sim_start
        sim_end = s.sim_end
        sim_dates = pd.date_range(sim_start, sim_end - pd.Timedelta(days=1), freq="D")
        lmp_w = lmp_full[(lmp_full["datetime_local"] >= sim_start)
                         & (lmp_full["datetime_local"] < sim_end)].reset_index(drop=True)
        wx_w = wx_full.loc[(wx_full.index >= sim_start) & (wx_full.index < sim_end)]
        r = eng.run_path(mode, seed, sim_dates, sim_start, sim_end, lmp_w, wx_w, henry,
                         init_state_override=init_override)
        d = r["daily"]
        spark = float(d["margin_degraded"].sum())
        ltsa = float(sum(r["final_ltsa"][k] for k in LTSA_KEYS))
        rows.append({
            "path_id": s.path_id,
            "source_window_id": s.source_window_id,
            "probability": s.probability,
            "spark_margin_usd": spark,
            "ltsa_owner_usd": ltsa,
            "net_pl_usd": spark - ltsa,
            "total_mwh": float(d["mwh_degraded"].sum()),
            "fired_hours": int(d["fired_hours"].sum()),
            "forced_outages": 0 if r["forced_outages"].empty else len(r["forced_outages"]),
        })
        if return_paths:
            # daily driver series (input forecast) + engine daily output, for fan charts
            lw = lmp_w.copy(); lw["d"] = lw["datetime_local"].dt.normalize()
            lmp_daily = lw.groupby("d")["price"].mean()
            tw = wx_w[["temp_f"]].copy(); tw["d"] = tw.index.normalize()
            temp_daily = tw.groupby("d")["temp_f"].mean()
            gd = henry.copy(); gd["dt"] = pd.to_datetime(gd["trade_date_dt"])
            gd = gd.groupby("dt")["price_usd_per_mmbtu"].mean().sort_index()  # dedupe dups/date
            gas_daily = gd.reindex(pd.date_range(sim_start.tz_localize(None),
                                                 sim_end.tz_localize(None) - pd.Timedelta(days=1))).ffill()
            paths_detail.append({
                "source_window_id": s.source_window_id,
                "probability": s.probability,
                "daily": d,                 # engine output (date, mwh_degraded, margin_degraded, ...)
                "lmp_daily": lmp_daily,      # input forecast: daily mean LMP ($/MWh)
                "gas_daily": gas_daily,      # input forecast: daily Henry Hub ($/MMBtu)
                "temp_daily": temp_daily,    # input forecast: daily mean ambient (°F)
            })
    per_path = pd.DataFrame(rows)

    metrics = ["net_pl_usd", "spark_margin_usd", "ltsa_owner_usd", "total_mwh"]
    quantiles = {}
    for met in metrics:
        quantiles[met] = {
            "P10": weighted_quantile(per_path[met], per_path["probability"], 0.10),
            "P50": weighted_quantile(per_path[met], per_path["probability"], 0.50),
            "P90": weighted_quantile(per_path[met], per_path["probability"], 0.90),
            "prob_weighted_mean": float(np.average(per_path[met], weights=per_path["probability"])),
        }

    result = {"mode": mode, "seed": seed, "per_path": per_path, "quantiles": quantiles,
              "seas5_init": sel.seas5_init}
    if return_paths:
        result["paths"] = paths_detail
        result["seas5_month_scores"] = sel.month_scores

    if save:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = OUT_DIR / f"forward_{run_id}"
        out.mkdir(parents=True, exist_ok=True)
        per_path.to_parquet(out / "per_path.parquet")
        (out / "quantiles.json").write_text(json.dumps(quantiles, indent=2))
        (out / "manifest.json").write_text(json.dumps({
            "mode": mode, "seed": seed, "basis": basis, "anchoring": "raw_historical_levels",
            "n_paths": len(per_path), "horizon": "Apr-Mar (native window dates)",
            "init_state": ("aged_historical_end_state" if aged_start else "fresh"),
            "init_eoh": (float(init_override.eoh) if init_override is not None else 24000.0),
            "seas5_init": sel.seas5_init, "valid_months": sel.valid_months,
            "note": "v1: scenario-driven spread, fixed seed; raw historical levels (no anchoring); aged-start per ADR-009",
            "generated": run_id,
        }, indent=2))
        result["out_dir"] = str(out)
    return result


if __name__ == "__main__":
    import sys as _sys
    basis = _sys.argv[1].upper() if len(_sys.argv) > 1 else DEFAULT_BASIS
    res = run_forward("A", basis=basis)
    pp = res["per_path"].sort_values("net_pl_usd")
    print(f"Per-scenario 1-year economics (Mode A, {basis}, raw levels):")
    show = pp.copy()
    for c in ["spark_margin_usd", "ltsa_owner_usd", "net_pl_usd"]:
        show[c] = (show[c] / 1e6).round(2)
    print(show[["source_window_id", "probability", "spark_margin_usd",
                "ltsa_owner_usd", "net_pl_usd", "fired_hours"]].to_string(index=False))
    print("\nProbability-weighted Net P&L distribution ($M):")
    q = res["quantiles"]["net_pl_usd"]
    for k in ["P10", "P50", "P90", "prob_weighted_mean"]:
        print(f"  {k:18s} = {q[k]/1e6:8.2f}")
    if "out_dir" in res:
        print(f"\nSaved -> {res['out_dir']}")
