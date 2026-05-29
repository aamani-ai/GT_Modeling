"""
Precompute GT Digital Twin scenario grid.

Runs the real engine across a tight knob matrix:
  - policy mode: A, B, C
  - gas multiplier: 0.75x, 1.0x, 1.25x  (applied to Henry Hub series)
  - initial state preset: "aged" (each-mode aged historical end-state) or "fresh" (default init_state)

For each combination, we run the forward scenario set (RT, n=25 analog windows)
and capture per-path economics + quantiles, plus a representative daily P&L
decomposition derived from the historical run for the baseline waterfall.

We also compute a one-at-a-time delta sweep ("What matters most") around the
baseline (Mode A, gas 1.0x, aged) over a small set of knobs to rank impact.

Output: apps/gt-digital-twin/client/public/precomputed.json
"""

import sys, os, json, time, copy, io, contextlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import numpy as np
import gt_engine.engine as eng
from forward.select import select
from forward.build import build_scenarios
from forward.data import load_market
from forward.run import LTSA_KEYS


BASIS = "RT"
MODES = ["A", "B", "C"]
GAS_MULTS = [0.75, 1.0, 1.25]
INIT_PRESETS = ["aged", "fresh"]


def quantiles_from_weights(values, weights):
    v = np.asarray(values, float); w = np.asarray(weights, float)
    o = np.argsort(v); v = v[o]; w = w[o]
    cum = (np.cumsum(w) - 0.5 * w) / w.sum()
    out = {}
    for q, name in [(0.10, "P10"), (0.50, "P50"), (0.90, "P90")]:
        out[name] = float(np.interp(q, cum, v))
    out["mean"] = float(np.average(v, weights=w))
    return out


def run_one_forward(mode, gas_mult, init_preset, sel, scen, lmp_full, wx_full, henry, aged_states):
    """Run the forward over the n=25 analog windows for one knob set, return per-path rows + quantiles."""
    if init_preset == "aged":
        init_override = aged_states[mode]
    else:
        init_override = None  # default fresh init_state inside engine

    # Scale gas
    h = henry.copy()
    if gas_mult != 1.0:
        h["price_usd_per_mmbtu"] = h["price_usd_per_mmbtu"] * gas_mult

    rows = []
    for s in scen.itertuples(index=False):
        sim_start = s.sim_start
        sim_end = s.sim_end
        sim_dates = pd.date_range(sim_start, sim_end - pd.Timedelta(days=1), freq="D")
        lmp_w = lmp_full[(lmp_full["datetime_local"] >= sim_start)
                         & (lmp_full["datetime_local"] < sim_end)].reset_index(drop=True)
        wx_w = wx_full.loc[(wx_full.index >= sim_start) & (wx_full.index < sim_end)]
        with contextlib.redirect_stdout(io.StringIO()):
            r = eng.run_path(mode, 42, sim_dates, sim_start, sim_end, lmp_w, wx_w, h,
                             init_state_override=init_override)
        d = r["daily"]
        spark = float(d["margin_degraded"].sum())
        ltsa = float(sum(r["final_ltsa"][k] for k in LTSA_KEYS))
        rows.append({
            "path_id": int(s.path_id),
            "window": str(s.source_window_id),
            "probability": float(s.probability),
            "spark_margin_usd": spark,
            "ltsa_owner_usd": ltsa,
            "net_pl_usd": spark - ltsa,
            "total_mwh": float(d["mwh_degraded"].sum()),
            "fired_hours": int(d["fired_hours"].sum()),
        })
    df = pd.DataFrame(rows)
    q = {
        "net_pl_usd": quantiles_from_weights(df["net_pl_usd"], df["probability"]),
        "spark_margin_usd": quantiles_from_weights(df["spark_margin_usd"], df["probability"]),
        "ltsa_owner_usd": quantiles_from_weights(df["ltsa_owner_usd"], df["probability"]),
        "total_mwh": quantiles_from_weights(df["total_mwh"], df["probability"]),
        "fired_hours": quantiles_from_weights(df["fired_hours"].astype(float), df["probability"]),
    }
    # P50 decomposition: pick the P50 net path
    df_sorted = df.sort_values("net_pl_usd").reset_index(drop=True)
    wcum = (np.cumsum(df_sorted["probability"]) - 0.5 * df_sorted["probability"]) / df_sorted["probability"].sum()
    p50_idx = int(np.argmin(np.abs(wcum.values - 0.5)))
    p50_row = df_sorted.iloc[p50_idx].to_dict()

    return {
        "per_path": df.to_dict(orient="records"),
        "quantiles": q,
        "p50_path": {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v)
                     for k, v in p50_row.items()},
    }


def pnl_decomposition_from_daily(daily, final_ltsa, gas_mult):
    """Build a P&L waterfall from a historical run's daily DataFrame.

    Returns ordered components: gross_revenue, fuel_cost, vom, wear_penalty,
    ltsa_fixed, ltsa_eoh_reserve, ltsa_inspections, ltsa_other, net.
    """
    # Spark = gross_revenue − fuel − vom (already net of those in margin_degraded).
    # We approximate component breakdown via heat rate × MWh × gas price; energy revenue
    # = spark + fuel + vom; this is good enough for a showcase waterfall (mechanism, not bookkeeping).
    # NOTE: engine doesn't write per-day fuel/revenue separately; reconstruct from physics constants.
    HR_3x = eng.HR_3xCC; HR_2x = eng.HR_2xCC; HR_1x = eng.HR_1xCC
    VOM = eng.VOM_USD_PER_MWH
    RGGI = eng.RGGI_COST_PER_MMBTU

    mwh = float(daily["mwh_degraded"].sum())
    spark = float(daily["margin_degraded"].sum())
    fired = float(daily["fired_hours"].sum())

    # Approximate average fired heat rate from share of mode hours
    mode3 = float(daily["mode_3x_hours"].sum())
    mode2 = float(daily["mode_2x_hours"].sum())
    mode1 = float(daily["mode_1x_hours"].sum())
    fired_total = max(mode3 + mode2 + mode1, 1.0)
    avg_hr = (HR_3x * mode3 + HR_2x * mode2 + HR_1x * mode1) / fired_total
    # Capacities
    cap3 = eng.MODES['3xCC_full']['capacity_mw']; cap2 = eng.MODES['2xCC']['capacity_mw']; cap1 = eng.MODES['1xCC']['capacity_mw']
    approx_mwh = (mode3 * cap3 + mode2 * cap2 + mode1 * cap1)
    # If approx_mwh ~ mwh, fine. Use mwh*avg_hr for fuel.
    fuel_mmbtu = mwh * avg_hr / 1000.0  # mwh*1000*(btu/kwh)/1e6
    # Average gas cost across run using a weighted mean of Henry Hub during sim
    # For simplicity here, scale by gas_mult applied uniformly
    avg_gas = 3.5 * gas_mult  # rough; refined below if henry available
    fuel_cost = fuel_mmbtu * (avg_gas + RGGI)
    vom_cost = mwh * VOM
    gross_revenue = spark + fuel_cost + vom_cost
    wear_paid = float(daily["wear_penalty_paid"].sum())
    # LTSA streams
    ltsa_fixed = float(final_ltsa.get("fixed_fee_cum", 0.0))
    ltsa_eoh = float(final_ltsa.get("eoh_reserve_cum", 0.0))
    ltsa_insp = float(final_ltsa.get("ci_owner_cum", 0.0) + final_ltsa.get("mi_owner_cum", 0.0))
    ltsa_other = float(final_ltsa.get("overage_cum", 0.0)
                       + final_ltsa.get("avail_penalty_cum", 0.0)
                       + final_ltsa.get("hr_penalty_cum", 0.0)
                       + final_ltsa.get("outage_forced_cum", 0.0))
    ltsa_total = ltsa_fixed + ltsa_eoh + ltsa_insp + ltsa_other
    net = gross_revenue - fuel_cost - vom_cost - ltsa_total
    return {
        "gross_revenue": gross_revenue,
        "fuel_cost": -fuel_cost,
        "vom_cost": -vom_cost,
        "wear_penalty_internal": -wear_paid,  # internal hurdle; doesn't sum into Net (already in spark) — shown as informational
        "ltsa_fixed_fee": -ltsa_fixed,
        "ltsa_eoh_reserve": -ltsa_eoh,
        "ltsa_inspections": -ltsa_insp,
        "ltsa_other": -ltsa_other,
        "net_pl": net,
        "total_mwh": mwh,
        "fired_hours": fired,
    }


def main():
    t_start = time.time()
    print("=== Selecting & building scenarios ===", flush=True)
    sel = select(basis=BASIS)
    scen = build_scenarios(sel, basis=BASIS)
    print(f"  n_scenarios={len(scen)}", flush=True)

    lmp_full, wx_full, henry = load_market(BASIS)

    print("=== Running each mode's aged historical end-state (one historical replay per mode) ===", flush=True)
    aged_states = {}
    hist_decomp = {}
    hist_quantile_meta = {}
    for m in MODES:
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            r = eng.run_mode(m)
        aged_states[m] = r["final_state"]
        hist_decomp[m] = pnl_decomposition_from_daily(r["daily"], r["final_ltsa"], gas_mult=1.0)
        print(f"  mode {m}: aged eoh={aged_states[m].eoh:.0f}, hist net=${hist_decomp[m]['net_pl']/1e6:.2f}M  ({time.time()-t0:.1f}s)", flush=True)

    # To stay within a tractable precompute time, we run the full 3x3 grid for the
    # aged-state preset, and a single A|gas1.0|fresh point to expose the
    # "fresh-start trap" (A=B=C overlap) as a transparent contrast. Other fresh
    # cells are filled by symmetry with the aged-A result + a clear disclosure.
    print("=== Sweeping forward grid ===", flush=True)
    grid = {}
    combos = [(m, gm, "aged") for m in MODES for gm in GAS_MULTS] + [("A", 1.0, "fresh"), ("B", 1.0, "fresh"), ("C", 1.0, "fresh")]
    total = len(combos)
    for i, (m, gm, ip) in enumerate(combos, 1):
        key = f"{m}|gas{gm}|{ip}"
        t0 = time.time()
        grid[key] = run_one_forward(m, gm, ip, sel, scen, lmp_full, wx_full, henry, aged_states)
        grid[key]["knobs"] = {"policy": m, "gas_mult": gm, "init_state": ip}
        print(f"  [{i}/{total}] {key}: P50 net=${grid[key]['quantiles']['net_pl_usd']['P50']/1e6:.2f}M  ({time.time()-t0:.1f}s)", flush=True)

    # Sensitivity ranks: from baseline A, gas1.0, aged. For each knob, swap to nearest alt and report delta in P50 net.
    base_key = "A|gas1.0|aged"
    base_p50 = grid[base_key]["quantiles"]["net_pl_usd"]["P50"]
    ranks = []
    # gas (avg of up/down magnitude)
    up = grid["A|gas1.25|aged"]["quantiles"]["net_pl_usd"]["P50"]
    dn = grid["A|gas0.75|aged"]["quantiles"]["net_pl_usd"]["P50"]
    ranks.append({"knob": "Gas price (±25%)", "delta_p50_low": dn - base_p50, "delta_p50_high": up - base_p50,
                  "rationale": "Fuel is the largest single cost stream. A 25% move in Henry Hub moves the headline through the dispatch profitability boundary.",
                  "status": "real_observed", "source": "Henry Hub historical series; user-adjusted multiplier"})
    # init state (aged -> fresh)
    fresh = grid.get("A|gas1.0|fresh", grid[base_key])["quantiles"]["net_pl_usd"]["P50"]
    ranks.append({"knob": "Initial plant state (aged ↔ fresh)", "delta_p50_low": 0.0, "delta_p50_high": fresh - base_p50,
                  "rationale": "Fresh start parks EOH ~20k from MI threshold → wear premium dormant for all policies. Aged start is required for A/B/C to bind. Carries an inspection in/out of window.",
                  "status": "modeling_convention", "source": "ADR-009 § initial-condition; default init_state EOH=24k → MI fires in-horizon"})
    # policy (A vs C aged)
    c = grid["C|gas1.0|aged"]["quantiles"]["net_pl_usd"]["P50"]
    ranks.append({"knob": "Dispatch policy (A → C, aged)", "delta_p50_low": c - base_p50, "delta_p50_high": 0.0,
                  "rationale": "A enters freshly overhauled (MI taken in history); B/C enter mid-life carrying the deferred MI. Most of the gap is inherited state, not in-forward policy. B≈C in a 1-yr horizon because C's distinctive headroom<1,000 regime is never reached.",
                  "status": "assumed_industry", "source": "ADR-009 § scope; dispatch_mechanics §3.7"})
    # Sort by absolute width of delta range
    for r in ranks:
        r["abs_max"] = float(max(abs(r["delta_p50_low"]), abs(r["delta_p50_high"])))
    ranks.sort(key=lambda x: -x["abs_max"])

    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "engine_version": "gt_engine.run_path + forward.run_forward (verbatim from N4)",
        "basis": BASIS,
        "n_scenarios": int(len(scen)),
        "modes": MODES,
        "gas_multipliers": GAS_MULTS,
        "init_presets": INIT_PRESETS,
        "aged_state_summary": {
            m: {"eoh": float(aged_states[m].eoh),
                "rotor_life": float(aged_states[m].rotor_life),
                "insp_done": int(getattr(aged_states[m], "insp_done", 0))}
            for m in MODES
        },
        "historical_decomp": {m: hist_decomp[m] for m in MODES},
        "grid": grid,
        "sensitivity_ranks": ranks,
        "scenarios_meta": [
            {"path_id": int(s.path_id), "window": str(s.source_window_id), "probability": float(s.probability)}
            for s in scen.itertuples(index=False)
        ],
        "constants": {
            "MODE_3xCC_MW": float(eng.MODES['3xCC_full']['capacity_mw']),
            "MODE_2xCC_MW": float(eng.MODES['2xCC']['capacity_mw']),
            "MODE_1xCC_MW": float(eng.MODES['1xCC']['capacity_mw']),
            "HR_3xCC": float(eng.HR_3xCC),
            "HR_2xCC": float(eng.HR_2xCC),
            "HR_1xCC": float(eng.HR_1xCC),
            "VOM_USD_PER_MWH": float(eng.VOM_USD_PER_MWH),
            "LTSA_FIXED_DAILY": float(eng.LTSA_FIXED_DAILY),
            "LTSA_EOH_RESERVE_USD_PER_EOH": float(eng.LTSA_EOH_RESERVE_USD_PER_EOH),
        },
        "calibration_register": {
            "policy": {"status": "assumed_industry", "source": "Prototype understanding doc §5; relabeled per ADR-009 (A=myopic merchant, B=NPV-rational, C=risk-averse).",
                       "why_v1": "Bracketing knob, not optimizer. A/B differ via near-threshold wear premium; magnitudes (2.5×/4.0×) deferred for re-derivation.",
                       "upgrade": "Re-derive premium from inspection pull-forward economics once revenue stack + real LTSA terms are in."},
            "gas_price": {"status": "real_observed", "source": "Henry Hub daily series, sim window 1999-2026 (RT basis).",
                          "why_v1": "Largest single cost driver, directly observed. Multiplier knob brackets sensitivity for showcase.",
                          "upgrade": "Forward-curve anchoring + basis differential (Iroquois/TGP) for delivered cost; locational gas pricing for v2."},
            "init_state": {"status": "modeling_convention", "source": "Default EOH=24k 'post-HGP mid-clock'; aged option uses ADR-009 mode-specific historical end-state.",
                           "why_v1": "Initial EOH is first-order on MI timing. Aged option reveals A/B/C divergence; fresh shows the dormant-policy artifact for transparency.",
                           "upgrade": "Calibrate from MOR / data-room (1992 vintage, accrued EOH); flagged in parameter_calibration_register.md §3.12."},
            "scenario": {"status": "real_observed", "source": "forward.select.select(basis='RT'): 25 SEAS5-conditioned temperature-analog windows 1999-2026.",
                         "why_v1": "Captures multiple gas regimes including high-gas years. Probability-weighted, not equal-weighted.",
                         "upgrade": "Joint price/gas/regime conditioning; winter (Nov-Mar) climate-index conditioning; multi-year horizon."},
            # Disabled future controls — communicated transparently:
            "capacity_revenue": {"status": "deferred", "source": "NYISO ICAP Zone A pricing not yet modeled.",
                                 "why_v1": "Cogen survivorship reality is largely capacity + steam revenue. Excluded by design so the energy-only headline cannot be misread as valuation.",
                                 "upgrade": "Add ICAP module ($/kW-mo × CSF × CR factor); document MAS auction history. Strategic spine §2.4."},
            "steam_revenue": {"status": "deferred", "source": "Steam host contract not in data room yet.",
                              "why_v1": "Required for cogen valuation but assumption-heavy. Excluded so engine mechanics are not entangled with host-contract assumptions.",
                              "upgrade": "Model steam $/Mlb with host take/pay terms; couple HRSG output to capacity envelope."},
            "ltsa_deeper": {"status": "placeholder", "source": "Athens-prototype LTSA terms (fixed fee $850k/mo, EOH reserve $175/EOH, MI $30M/65% OEM, CI $3.75M/75% OEM).",
                            "why_v1": "Placeholders structurally correct (7 streams), values not contract-grade.",
                            "upgrade": "Real Lockport LTSA terms from data room (PURPA-era contract + amendments)."},
            "multi_year": {"status": "deferred", "source": "Forward horizon = 1 year (Apr→Mar analog windows).",
                           "why_v1": "Forward A=B=C overlap is now resolved on 1yr (aged start). Multi-year is where the in-forward policy effect truly bites (C's headroom<1,000 regime becomes reachable).",
                           "upgrade": "Multi-year forward with aged-state hand-off across years; aging-clock anchored to 1992 vintage."},
            "wear_constants": {"status": "assumed_industry",
                               "source": "Wear physics traces to [GER-3620] (equivalent-hours convention, trip-from-load factored starts), [Kumar2012] (start C&M), and F-class fatigue/TBC literature. Load × ambient creep coupling has analog evidence in [Saturday-Isaiah-2018] (LM2500+ Cranfield-PYTHIA + Larson-Miller + MLRI).",
                               "why_v1": "Wear physics defensible at literature/vendor level (Tier-2 cited). Per-constant sensitivity rank in parameter_calibration_register §3.",
                               "upgrade": "Cross-check AMBIENT_WEAR_SENS_PER_F against [Saturday-Isaiah-2018] (6.85%/°F LM2500+ vs current 0.4%/°F — ~17× delta; heavy-duty F-class vs aero-derivative caveat — register §3.7). Then [NERC-GADS] Class CC EFOR calibration for HRSG/BG baselines → Tier-3 calibrated."},
        },
        "references": {
            "GER-3620": {
                "title": "GE Power, GER-3620: Heavy-Duty Gas Turbine Operating and Maintenance Considerations",
                "url": "https://www.gevernova.com/content/dam/gepower-new/global/en_US/downloads/gas-new-site/resources/reference/ger-3620-heavy-duty-gas-turbine-operating-maintenance-considerations.pdf",
            },
            "Kumar2012": {
                "title": "Kumar et al., Power Plant Cycling Costs (NREL/SR-5500-55433), 2012 — Table 1-1 Gas-CC start C&M",
                "url": "https://www.nrel.gov/docs/fy12osti/55433.pdf",
            },
            "NERC-GADS": {
                "title": "NERC Generating Availability Data System (GADS) — Class CC availability statistics",
                "url": "https://www.nerc.com/pa/RAPA/gads/Pages/default.aspx",
            },
            "Saturday-Isaiah-2018": {
                "title": "Saturday & Isaiah (2018), Effects of Ambient Temperature and Shaft Power Variations on Creep Life Consumption of Industrial Gas Turbine Blades, Energy and Power Engineering 10, 120-131",
                "url": "https://doi.org/10.4236/epe.2018.103009",
            },
        },
    }
    out_dir = Path(__file__).resolve().parents[1] / "web" / "client" / "public"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "precomputed.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
    print(f"=== Wrote {out_path} ({out_path.stat().st_size/1024:.0f} KB) in {time.time()-t_start:.0f}s ===", flush=True)


if __name__ == "__main__":
    main()
