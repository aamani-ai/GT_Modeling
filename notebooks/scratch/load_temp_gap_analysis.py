"""Temperature + load fidelity — gap quantification (Stream B, B1).

Sizes how much the v1 model's two simplifications cost, using real MOR data:
  1. "100% load when on" — no within-mode part-load heat-rate penalty
  2. "fired-hours-only" degradation — no load or ambient weighting on wear

KEY REFINEMENT over the first-pass sizing: mode-normalization. The model
ALREADY captures mode-pick (3xCC / 2xCC / 1xCC) via mode-specific heat rates.
The actual missing gap is *within-mode* part-load (running 3xCC at 70% vs 100%),
NOT the capacity difference between modes. So we compute load as a fraction of
the CHOSEN mode's capacity, not of total nameplate. This isolates the true
incremental part-load gap from the mode effect the model already has.

This is a SIZING analysis, not an engine change. It tells us whether B2
(part-load HR) and B3 (load x temp degradation) are worth the engine work for
Lockport specifically.

Run:
    /Users/divy/code/personal/renewablesinfo_org/.venv/bin/python \
        notebooks/scratch/load_temp_gap_analysis.py

Reads: data/paths/lockport/mor_daily.parquet
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MOR = REPO / "data/paths/lockport/mor_daily.parquet"

# Nameplate mode capacities (engineering.yaml: 3x48.7 CT + 75.2 CA)
CT_MW, CA_MW = 48.7, 75.2
MODE_CAP = {"3xCC": 3 * CT_MW + CA_MW, "2xCC": 2 * CT_MW + CA_MW, "1xCC": 1 * CT_MW + CA_MW}
CT_ON_MWH = 5.0

# Part-load HR multiplier.
# NOTE: the polynomial transcribed in 02_load_as_a_dimension.md §4.1 /
# performance_and_risk_framework.md §4.6 as "2.648 - 4.296L + 2.648L^2" is
# INTERNALLY INCONSISTENT — it dips below 1.0 in the interior (unphysical; a
# part-load HR multiplier must be >= 1.0) and does NOT reproduce its own stated
# values (gives 0.927 at L=0.9, not the documented 1.015). See temperature_load_
# fidelity.md. We instead fit a quadratic to the PUBLISHED ANCHOR VALUES, which
# are the physically-sensible target:
_ANCHOR_L   = np.array([1.00, 0.90, 0.80, 0.70, 0.60, 0.50])
_ANCHOR_MULT = np.array([1.000, 1.015, 1.038, 1.068, 1.107, 1.162])
_COEF = np.polyfit(_ANCHOR_L, _ANCHOR_MULT, 2)  # monotonic-decreasing-efficiency fit

def hr_mult(L: float) -> float:
    L = np.clip(L, 0.5, 1.0)
    return float(np.polyval(_COEF, L))


def classify_mode(row) -> str:
    n = sum(row[c] > CT_ON_MWH for c in ("ctg1_mwh", "ctg2_mwh", "ctg3_mwh"))
    return {3: "3xCC", 2: "2xCC", 1: "1xCC"}.get(n, "1xCC")


def main() -> None:
    df = pd.read_parquet(MOR)
    op = df[(df["net_output_mwh"] > 0) & (df["plant_run_time_hrs"] > 0)].copy()
    op["mode"] = op.apply(classify_mode, axis=1)
    op["mode_cap"] = op["mode"].map(MODE_CAP)

    # --- (A) NAIVE load fraction (vs total nameplate) — conflates mode + within-mode ---
    op["load_naive"] = (op["net_output_mwh"] / op["plant_run_time_hrs"]) / MODE_CAP["3xCC"]
    # --- (B) MODE-NORMALIZED load fraction (vs chosen mode's capacity) — the true part-load gap ---
    op["load_modenorm"] = (op["net_output_mwh"] / op["plant_run_time_hrs"]) / op["mode_cap"]

    op["hr_pen_naive"] = op["load_naive"].map(hr_mult) - 1.0
    op["hr_pen_modenorm"] = op["load_modenorm"].map(hr_mult) - 1.0

    print(f"Operating days: {len(op)}  (modes: {op['mode'].value_counts().to_dict()})")
    print("\n=== (A) NAIVE load fraction vs total nameplate (mixes mode + within-mode) ===")
    print(op["load_naive"].describe(percentiles=[.25, .5, .75, .9]).round(3).to_string())
    print(f"  mean HR penalty (naive): {op['hr_pen_naive'].mean() * 100:.1f}%  <- overstates the gap")

    print("\n=== (B) MODE-NORMALIZED within-mode load fraction (the TRUE part-load gap) ===")
    print(op["load_modenorm"].describe(percentiles=[.25, .5, .75, .9]).round(3).to_string())
    print(f"  mean HR penalty (mode-normalized): {op['hr_pen_modenorm'].mean() * 100:.1f}%  <- the real B2 prize")
    print("\n  within-mode load by mode (median):")
    print(op.groupby("mode")["load_modenorm"].median().round(3).to_string())

    # generation-weighted HR penalty (what actually hits the P&L)
    genwt = (op["hr_pen_modenorm"] * op["net_output_mwh"]).sum() / op["net_output_mwh"].sum()
    print(f"\n  generation-weighted within-mode HR penalty: {genwt * 100:.1f}%")
    print("  (this is the ~fuel-cost overstatement-avoidance B2 would buy, isolated from mode)")

    # --- (C) Ambient + load degradation sizing (ILLUSTRATIVE, pending Friday paper) ---
    print("\n=== (C) Degradation weighting sensitivity (ILLUSTRATIVE — pending the load-temp paper) ===")
    # current: wear ~ fired_hours (flat). illustrative: wear ~ fired_hours * load^p (creep-like superlinear)
    op["fh"] = op["plant_run_time_hrs"]
    flat = op["fh"].sum()
    for p in (1.0, 2.0, 3.0):
        weighted = (op["fh"] * op["load_modenorm"].clip(0, 1) ** (p - 1)).sum()
        print(f"  wear ~ fh * load^{int(p-1)}: weighted/flat = {weighted / flat:.2f}  "
              f"({'baseline (current model)' if p == 1 else 'load-weighted'})")
    hot = op[op["ambient_temp_f"] > 80]
    print(f"\n  operating fired-hours at ambient>80F (extra-stress band): "
          f"{hot['fh'].sum():.0f} / {op['fh'].sum():.0f} = {hot['fh'].sum() / op['fh'].sum() * 100:.0f}%")
    print(f"  total operating fired hours 2021-2025: {op['fh'].sum():,.0f} (~{op['fh'].sum()/5:,.0f}/yr)")

    print("\n=== TAKEAWAYS ===")
    print(f"  - True within-mode part-load HR gap (B2): ~{genwt*100:.1f}% gen-weighted "
          f"(vs ~{op['hr_pen_naive'].mean()*100:.0f}% if you don't mode-normalize)")
    print("  - Load-weighting degradation (B3) moves total wear modestly for Lockport "
          "(low CF, mostly part-load not peak-fire); matters more for high-CF assets")
    print("  - Both effects are real but Lockport's economics care more about B2 (HR) than B3 (wear)")


if __name__ == "__main__":
    main()
