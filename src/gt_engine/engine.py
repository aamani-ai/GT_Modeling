# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Notebook 4 — Full Path + Mode A/B/C + LTSA Cost Streams
#
# **Phase J of the Lockport gas turbine digital twin build — the v1 capstone.**
# Run the full historical horizon (2017-01-01 → 2025-12-31, 9 years) under three
# dispatch policies (Mode A / B / C), produce all seven LTSA cost streams,
# trigger inspection events, sample forced-outage events, and produce a
# `model_card.md` summarizing what the model says about Lockport.
#
# **Plan**: [`docs/plans/consolidation_plan/notebooks/04_full_path_mode_comparison.md`](../docs/plans/consolidation_plan/notebooks/04_full_path_mode_comparison.md)
#
# **Inherited from N1, N2, N3 + ADR-001 + ADR-002**:
# - `v()` / `m()` helpers; weather TZ conversion; Henry Hub gas
# - Mode capacities, mode heat rates (MOR-derived `real_observed`)
# - Cogen VOM markup ×1.35, RGGI $17/short ton × 117 lb/MMBtu
# - State vector (PlantState dataclass), stress accumulators, forced-outage probability
# - Cold-start warming gas (ADR-002 Correction 1: 2,537 MMBtu/cold start, MOR-observed)
#
# **New in N4**:
# - Mode A/B/C policy curves (wear penalty multiplier × GT_WEAR_FRACTION × Kumar start cost)
# - Maintenance schedule pre-builder with calendar shoulder-snap (April / October)
# - Inspection event triggering (calendar match or hard-stop +1500 EOH overage)
# - State resets at CI / MI per prototype convention
# - Forced outage event sampling (RNG-driven Bernoulli; cause weighted by component prob)
# - All 7 LTSA cost stream accruals (fixed fee, EOH reserve, CI, MI, start overage,
#   availability penalty, HR penalty — placeholder per ADR-001)
# - 6 plots (state by mode, P_forced by mode, cumulative margin, LTSA streams stacked,
#   mode-comparison bars, inspection timeline)
# - First `model_card.md` write per `docs/assumptions/README.md` requirement
# - MOR backtest validation (2024 generation vs 192,494 MWh observed; mode distribution;
#   cold-start frequency)

# %% [markdown]
# ## Conventions chosen for this notebook (decision log)
#
# | Decision | Choice |
# |---|---|
# | Time horizon | 9-year historical replay 2017-01-01 → 2025-12-31 |
# | Number of modes | 3 (A, B, C) per prototype convention |
# | Mode policy mechanics | Wear-penalty multiplier × GT_WEAR_FRACTION (0.42) × Kumar start cost; amortized over 6-hour expected run-streak |
# | Maintenance schedule | Pre-built per mode at sim start; calendar shoulder-snap (next April 1 or October 1); hard-stop trigger at +1,500 EOH overage |
# | EOH rate estimate | v1 placeholder 8 EOH/day (scaled by mode EOH-rate multiplier); v2 should tune per-asset from history |
# | Inspection state reset | CI: dc/df halve, fouling 70% wash, hr_recov 30% retain; MI: dc/df zero, fouling 70% wash, hr_recov 75% retain, tbc_time zero, tbc_thresh resampled |
# | Forced outage event sampling | Daily Bernoulli vs P_forced; cause weighted by component prob; duration lognormal(median, σ=0.5) |
# | Outage cost classification | GT mechanical: OEM-covered ($0 owner cost); HRSG: $500K owner-uncovered; BG: $750K owner-uncovered (placeholder per ADR-001) |
# | LTSA stream parameters | Read from `ltsa_terms.yaml`; all placeholder Athens defaults per ADR-001 + `placeholder_caveats.md` |
# | RNG seed | 42 fixed (single-path; Phase L Monte Carlo varies seed) |
# | Cold-start warming gas | Inherited from N3 + ADR-002 Correction 1 |
# | RGGI | Inherited from N3 |
# | Cogen VOM + must-run | Inherited from N3 |
# | Plots | 6: state by mode, P_forced by mode, cumulative margin, LTSA streams stacked, mode-comparison summary, inspection timeline |
# | model_card | Generate `model_card.md` written to `data/outputs/lockport/runs/notebook4_<ts>/` |
# | Output bundle | All daily DataFrames + ltsa_streams + inspection_events + forced_outage_events written as parquet |
# | Backtest validation | Compare modeled 2024 vs MOR-observed 192,494 MWh; mode distribution; cold-start frequency. Honest report; not a fail-gate. |

# %% [markdown]
# ---
# ## §A — Setup

# %%
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]  # src/gt_engine/engine.py -> repo root
DATA_DIR = REPO_ROOT / "data"
ASSET = "lockport"


# ---- Helper functions (same as N1, N2, N3) ----
def v(field: Any) -> Any:
    if isinstance(field, dict) and "value" in field and "status" in field:
        return field["value"]
    return field


def m(field: Any) -> dict | None:
    if isinstance(field, dict) and "value" in field and "status" in field:
        return {k: val for k, val in field.items() if k != "value"}
    return None


# ---- Load all the inputs ----
def load_yaml(name: str) -> dict:
    return yaml.safe_load((DATA_DIR / "assets" / ASSET / f"{name}.yaml").read_text())

identity = load_yaml("identity")
engineering = load_yaml("engineering")
market_context = load_yaml("market_context")
operating_profile = load_yaml("operating_profile")
ltsa_terms = load_yaml("ltsa_terms")

tech_defaults = pd.read_parquet(DATA_DIR / "tech_class_defaults" / "dispatch_params_lookup.parquet")

PATHS_DIR = DATA_DIR / "paths" / ASSET
lmp_da = pd.read_parquet(PATHS_DIR / "lmp_da_hourly.parquet")
gas = pd.read_parquet(PATHS_DIR / "gas_price_history.parquet")
weather_raw = pd.read_parquet(PATHS_DIR / "weather_hourly.parquet")
weather = weather_raw.copy()
weather.index = pd.to_datetime(weather.index, utc=True).tz_convert("US/Eastern")

print("Data spine loaded.")

# %% [markdown]
# ### Constants — inherited from N3 + Mode A/B/C + LTSA stream parameters

# %%
# ============================================================================
# Inherited from N3 (engineering, operating profile, RGGI, VOM)
# ============================================================================

# Mode heat rates from operating_profile.yaml (MOR-derived, real_observed)
HR_3xCC = float(v(operating_profile["heat_rate_by_mode"]["3xCC_full"]["btu_per_kwh"]))
HR_2xCC = float(v(operating_profile["heat_rate_by_mode"]["2xCC"]["btu_per_kwh"]))
HR_1xCC = float(v(operating_profile["heat_rate_by_mode"]["1xCC"]["btu_per_kwh"]))

# Mode capacities from engineering.yaml
gens = engineering["generators"]
NAMEPLATE_CT = float(v(gens["GEN1"]["nameplate_capacity_mw"]))
NAMEPLATE_CA = float(v(gens["GEN4"]["nameplate_capacity_mw"]))

MODES = {
    "3xCC_full": {"hr_btu_per_kwh": HR_3xCC, "capacity_mw": 3 * NAMEPLATE_CT + NAMEPLATE_CA},
    "2xCC":      {"hr_btu_per_kwh": HR_2xCC, "capacity_mw": 2 * NAMEPLATE_CT + NAMEPLATE_CA},
    "1xCC":      {"hr_btu_per_kwh": HR_1xCC, "capacity_mw": 1 * NAMEPLATE_CT + NAMEPLATE_CA},
}

# Base VOM + cogen markup (per N3)
VOM_BASE_USD_PER_MWH = float(tech_defaults[
    (tech_defaults["prime_mover_code"] == "CT")
    & (tech_defaults["vintage_class"] == "<2000")
    & (~tech_defaults["aero_derivative"])
].iloc[0]["vom_per_mwh"])
COGEN_VOM_MARKUP = 1.35
VOM_USD_PER_MWH = VOM_BASE_USD_PER_MWH * COGEN_VOM_MARKUP

# RGGI (per N3)
RGGI_USD_PER_SHORT_TON_CO2 = 17.0
RGGI_CO2_LB_PER_MMBTU_NG = 117.0
RGGI_COST_PER_MMBTU = (RGGI_CO2_LB_PER_MMBTU_NG / 2000) * RGGI_USD_PER_SHORT_TON_CO2

# Cold-start warming gas (ADR-002 Correction 1, real_observed)
MOR_COLD_START_GAS_MMBTU = float(v(operating_profile["cold_start_gas"]["mean_per_cold_start_mmbtu"]))

# ============================================================================
# Steam-only mode (Phase J update from backtest_findings.md §3.4)
# ============================================================================
# Real Lockport operates 25.2% of days (460/1826 MOR observations) in
# steam-only mode: HRSG duct burners (EIA-860 boiler_type='Db') fire gas
# directly to make process steam, with 0 MWh and 0 EOH wear. v1 N4 originally
# forced 1×CC dispatch on uneconomic must-run days; this adds steam-only as
# a third option in the must-run branch.
STEAM_ONLY_GAS_MMBTU_PER_DAY = float(v(operating_profile["steam_only_mode"]["gas_mmbtu_per_day_median"]))
STEAM_ONLY_DHTS_MMBTU_PER_DAY = float(v(operating_profile["steam_only_mode"]["dhts_mmbtu_per_day_median"]))

# ============================================================================
# Min-load floors (C: wired but not actively enforced in v1 partial-dispatch)
# ============================================================================
# Block-level min load (sum of per-generator min loads for each operating mode).
# v1 dispatches at full mode capacity, so min-load doesn't bind; values are
# wired in here for v2 partial-dispatch implementation and as a structural
# correctness check. Per engineering.yaml: CT min=30 MW, ST min=14 MW.
MIN_LOAD_CT_MW = float(v(engineering["generators"]["GEN1"]["min_load_mw"]))  # 30 MW per CT
MIN_LOAD_ST_MW = float(v(engineering["generators"]["GEN4"]["min_load_mw"]))  # 14 MW for ST
MIN_LOAD_BY_MODE = {
    "3xCC_full": 3 * MIN_LOAD_CT_MW + MIN_LOAD_ST_MW,  # 104 MW
    "2xCC":      2 * MIN_LOAD_CT_MW + MIN_LOAD_ST_MW,  # 74 MW
    "1xCC":      1 * MIN_LOAD_CT_MW + MIN_LOAD_ST_MW,  # 44 MW
}

# ============================================================================
# Engineering state-evolution constants (prototype convention; inherited from N3)
# ============================================================================
START_EOH_COST = {"cold": 20.0, "warm": 10.0, "hot": 5.0}

FOULING_ASYMPTOTE_PCT = 2.5
FOULING_TAU_HRS = 2000.0
FOULING_AQI_PROXY = 1.0

CREEP_RATE_PER_FIRED_HOUR = 5e-6
CREEP_BUDGET = 1.0
FATIGUE_PER_COLD_START = 0.001
FATIGUE_PER_WARM_START = 0.0005
FATIGUE_PER_HOT_START = 0.0002
FATIGUE_BUDGET = 1.0
COMB_BUDGET = 1.0
D_LIM = 0.7

HRSG_CYCLES_PER_START = 1.0
HRSG_BASE_PROB_PER_DAY = 0.0075
HRSG_AGE_MULT_MAX = 1.5

BG_BASE_PROB_PER_DAY = 0.004
BG_AGE_MULT_MAX = 1.5

ROTOR_LIFE_PER_FIRED_HOUR = 1e-7

P_COMBUSTION_INFLECTION = 0.6
P_COMBUSTION_SCALE = 0.10
P_FORCED_DAY_CAP = 0.10

# Creep-rupture forced-outage hazard (ADR-007 — wire dc into p_forced).
# The framework's "two meters" intent (learning_logs/degradation_factors/01) is that
# physical creep-fatigue damage drives forced-outage RISK, but v1 wired only df (→p_comb)
# and left dc (creep) feeding nothing. This adds a creep-rupture hazard: a hockey-stick on
# creep life-fraction (dc/CREEP_BUDGET), mirroring the combustion hazard on df. For low-CF
# Lockport dc stays small (≈0.01) so p_creep ≈ 0 (physically correct — it doesn't run enough
# to creep-rupture); the channel activates for high-CF / hot-running assets and now also
# responds to the ambient weighting of dc (ADR-006). Coefficients are Bucket-B placeholders.
P_CREEP_INFLECTION = 0.5    # creep life-fraction below which creep-rupture hazard ≈ 0
P_CREEP_SCALE = 0.10        # hockey-stick scale (mirrors P_COMBUSTION_SCALE)

# Trip-induced wear (ADR-007 — GER-3620). A trip FROM LOAD is far harsher than a normal
# planned shutdown (~8 factored starts of hot-section damage for a full-load trip). v1 runs
# full-load when on, so a forced outage from a running state IS a full-load trip → the full
# 8× factor applies (when Stream A adds part-load, this factor scales down with trip load).
# Bucket-B placeholder; Saturday & Isaiah 2018 (the load-temp paper, register §9) is
# creep-only and doesn't constrain this; pending OEM-specific evidence.
TRIP_MAINTENANCE_FACTOR = 8.0

TBC_WEIBULL_BETA = 3.0
TBC_WEIBULL_ETA = 28_000.0

# ── Ambient-weighted hot-section wear (B3 ambient half; 2026-05-27, ADR-006) ──
# Hot-section creep (state.dc) and TBC life (state.tbc_time) are metal-temperature
# driven: hotter ambient → hotter compressor-discharge cooling air → hotter blade
# metal → faster creep / TBC oxidation (GER-3620 hot-section physics). The model
# therefore weights ONLY those two accumulators by an ambient maintenance factor,
# applied at hourly resolution over fired hours (see dispatch + update_stress()).
#
# RE-ANCHORING (the key correctness property): the factor is centred on the
# fired-hour-weighted mean ambient (AMBIENT_WEAR_REF_F), so the weighted-mean
# factor ≈ 1.0. This REDISTRIBUTES wear toward hot hours (shifting inspection
# TIMING) without re-levelling the calibrated TOTAL. For Lockport's winter-heavy
# cogen dispatch the realized fired-hour-weighted mean ambient is ~34°F (≈70% of
# fired hours < 32°F, only ~2% > 80°F), so most hours get a factor < 1 and the few
# summer hours > 1. Validated per run: Σ fired_hours_hot / Σ fired_hours ≈ 1.00.
#
# COEFFICIENTS ARE LITERATURE DEFAULTS (modest hot-section sensitivity). The
# load-temp paper has landed — Saturday & Isaiah (2018) — and surfaces a ~17×
# higher ambient creep sensitivity (6.85%/°F on LM2500+ aero-derivative vs our
# 0.4%/°F here). Sensitivity sweep needed before adoption; see ADR-006 §5 and
# parameter_calibration_register.md §3.7. The LOAD half of B3 is deliberately
# NOT implemented in v1: a full-dispatch price-taker has no load variation to
# weight, so load-weighted wear is a structural no-op until Stream A (Phase 6)
# introduces behavioural/price-responsive output. Full reasoning + the deferred
# load-half plan: docs/decisions/006-ambient-weighted-wear.md;
# docs/methodology/extra/temperature_load_fidelity.md §10.
AMBIENT_WEAR_REF_F = 34.3         # re-anchor point = realized fired-hour-weighted mean ambient (Lockport, post-#2 path)
AMBIENT_WEAR_SENS_PER_F = 0.004   # hot-section sensitivity per °F (literature default; Saturday-Isaiah 2018 suggests ~6.85%/°F for LM2500+ — see ADR-006 §5)
AMBIENT_WEAR_FACTOR_MIN = 0.70
AMBIENT_WEAR_FACTOR_MAX = 1.40

# ============================================================================
# NEW: Mode A/B/C policy parameters (per prototype understanding doc §5)
# ============================================================================

# EOH rate multiplier — affects pre-built maintenance schedule
MODE_EOH_RATE_MULT = {"A": 1.00, "B": 0.875, "C": 0.65}

# Wear penalty: GT_WEAR_FRACTION is the share of start cost attributable to GT wear
# (the rest is fuel + HRSG/ST share, not subject to mode penalty)
GT_WEAR_FRACTION_OF_START = 0.42

# Start C&M from Kumar 2012 Table 1-1 "Gas-CC" $/MW capacity (2011 USD)
START_CM_USD_PER_MW = {"cold": 79.0, "warm": 55.0, "hot": 35.0}

# Min-run amortization proxy: amortize start wear penalty over expected run-streak
MIN_RUN_HOURS_FOR_AMORTIZATION = 6.0

# v1 EOH rate estimate (used in maintenance schedule pre-builder)
# Heuristic: low-CF Lockport ~8 EOH/day average across the year (fired hrs + start penalties).
# v2 should derive per-asset from historical observed dispatch. Documented in §M decision log.
EOH_RATE_ESTIMATE_PER_DAY = 8.0


def wear_penalty_mult(mode: str, eoh_headroom: float) -> float:
    """Wear penalty multiplier on start cost, scaled by EOH headroom to next inspection.

    Per prototype understanding doc §5:
    - Mode A: always 1.0 (no self-curtailment)
    - Mode B: 1.0 when headroom > 4,000; linearly to 2.5× at headroom = 1,000
    - Mode C: 1.0 when headroom > 4,000; linearly to 4.0× at headroom = 0
    """
    if mode == "A":
        return 1.0
    if eoh_headroom > 4_000:
        return 1.0
    if mode == "B":
        if eoh_headroom <= 1_000:
            return 2.5
        return 1.0 + (4_000 - eoh_headroom) / (4_000 - 1_000) * (2.5 - 1.0)
    if mode == "C":
        if eoh_headroom <= 0:
            return 4.0
        return 1.0 + (4_000 - eoh_headroom) / 4_000 * (4.0 - 1.0)
    return 1.0


# ============================================================================
# NEW: LTSA stream parameters (read from ltsa_terms.yaml, placeholder per ADR-001)
# ============================================================================

# Stream 1: fixed monthly fee → daily accrual
LTSA_FIXED_MONTHLY_USD = float(v(ltsa_terms["fixed_fee"]["monthly_usd"]))
LTSA_FIXED_DAILY = LTSA_FIXED_MONTHLY_USD * 12 / 365
LTSA_ESCALATION_PCT_PER_YEAR = float(v(ltsa_terms["fixed_fee"]["escalation_pct_per_year"]))

# Stream 2: EOH reserve
LTSA_EOH_RESERVE_USD_PER_EOH = float(v(ltsa_terms["eoh_reserve"]["rate_usd_per_eoh"]))

# Stream 3: CI event cost
CI_TOTAL_COST = float(v(ltsa_terms["inspection_ci"]["total_cost_usd"]))
CI_OEM_COVERED_FRAC = float(v(ltsa_terms["inspection_ci"]["oem_covered_fraction"]))
CI_OWNER_UNCOVERED = float(v(ltsa_terms["inspection_ci"]["owner_uncovered_usd"]))
CI_OUTAGE_DAYS = int(v(ltsa_terms["inspection_ci"]["outage_duration_days"]))
CI_EOH_INTERVAL = int(v(ltsa_terms["inspection_ci"]["eoh_threshold"]))  # interval between CIs

# Stream 4: MI event cost
MI_TOTAL_COST = float(v(ltsa_terms["inspection_mi"]["total_cost_usd"]))
MI_OEM_COVERED_FRAC = float(v(ltsa_terms["inspection_mi"]["oem_covered_fraction"]))
MI_OWNER_UNCOVERED = float(v(ltsa_terms["inspection_mi"]["owner_uncovered_usd"]))
MI_OUTAGE_DAYS = int(v(ltsa_terms["inspection_mi"]["outage_duration_days"]))
MI_EOH_INTERVAL = int(v(ltsa_terms["inspection_mi"]["eoh_threshold"]))  # interval between MIs

# Hard-stop overage (per prototype convention): if EOH > scheduled_threshold + this, force inspection
INSP_HARD_STOP_EOH_OVERAGE = 1_500.0

# Stream 5: start overage
OVERAGE_BASELINE = {
    "hot":  float(v(ltsa_terms["start_overage"]["annual_baseline_starts"]["hot"])),
    "warm": float(v(ltsa_terms["start_overage"]["annual_baseline_starts"]["warm"])),
    "cold": float(v(ltsa_terms["start_overage"]["annual_baseline_starts"]["cold"])),
}
OVERAGE_CHARGE = {
    "hot":  float(v(ltsa_terms["start_overage"]["overage_charge_usd_per_excess_start"]["hot"])),
    "warm": float(v(ltsa_terms["start_overage"]["overage_charge_usd_per_excess_start"]["warm"])),
    "cold": float(v(ltsa_terms["start_overage"]["overage_charge_usd_per_excess_start"]["cold"])),
}

# Stream 6: availability penalty
AVAIL_GUARANTEE_PCT = float(v(ltsa_terms["availability_penalty"]["guarantee_pct"]))

# Stream 7: HR penalty
# guarantee_btu_per_kwh is null in ltsa_terms.yaml — use design HR proxy.
# For v1, set the guarantee at the 3xCC clean HR (MOR-observed for 3-on-1 mode).
# HR penalty fires at cycle end (CI / MI). Penalty = excess fuel cost × 1.25.
HR_GUARANTEE_BTU_PER_KWH = HR_3xCC  # v1 proxy; real value pending data room extraction
HR_TOLERANCE_PCT = float(v(ltsa_terms["hr_penalty"]["tolerance_pct_above_guarantee"]))
HR_PENALTY_MULTIPLIER = 1.25  # per ltsa_terms.yaml penalty_method

# ============================================================================
# NEW: Forced outage event parameters (per prototype §7)
# ============================================================================

# Median duration days by cause
OUTAGE_DURATION_DAYS = {"gt": 8, "hrsg": 12, "bg": 5}
OUTAGE_DURATION_SIGMA = 0.5  # lognormal sigma

# Owner-uncovered cost classification (placeholder per ADR-001)
OUTAGE_OWNER_COST_USD = {
    "gt": 0,  # OEM-covered per ltsa_terms.yaml.forced_outage_coverage.gt_mechanical
    "hrsg": float(v(ltsa_terms["forced_outage_coverage"]["hrsg"]["typical_repair_cost_usd"])),
    "bg": float(v(ltsa_terms["forced_outage_coverage"]["bop"]["typical_repair_cost_usd"])),
}

print("Constants loaded.")
print(f"Mode HRs: 3xCC={HR_3xCC}, 2xCC={HR_2xCC}, 1xCC={HR_1xCC} Btu/kWh")
print(f"Mode capacities: 3xCC={MODES['3xCC_full']['capacity_mw']:.1f}, 2xCC={MODES['2xCC']['capacity_mw']:.1f}, 1xCC={MODES['1xCC']['capacity_mw']:.1f} MW")
print(f"VOM (w/ cogen markup): ${VOM_USD_PER_MWH:.2f}/MWh; RGGI: ${RGGI_COST_PER_MMBTU:.3f}/MMBtu")
print(f"LTSA: fixed daily ${LTSA_FIXED_DAILY:,.0f}; EOH reserve ${LTSA_EOH_RESERVE_USD_PER_EOH:.0f}/EOH; escalation {LTSA_ESCALATION_PCT_PER_YEAR}%/yr")
print(f"CI: ${CI_TOTAL_COST/1e6:.2f}M total ({CI_OEM_COVERED_FRAC*100:.0f}% OEM), {CI_OUTAGE_DAYS} days, every {CI_EOH_INTERVAL} EOH")
print(f"MI: ${MI_TOTAL_COST/1e6:.2f}M total ({MI_OEM_COVERED_FRAC*100:.0f}% OEM), {MI_OUTAGE_DAYS} days, every {MI_EOH_INTERVAL} EOH")
print(f"Forced outage owner-cost: GT $0 (OEM); HRSG ${OUTAGE_OWNER_COST_USD['hrsg']:,.0f}; BG ${OUTAGE_OWNER_COST_USD['bg']:,.0f}")
print(f"HR guarantee proxy (v1): {HR_GUARANTEE_BTU_PER_KWH} Btu/kWh + {HR_TOLERANCE_PCT}% tolerance")

# %% [markdown]
# ---
# ## §B — Window definition (9-year historical replay)
#
# Strategy: 2017-01-01 → 2025-12-31. Boundaries chosen for full LMP coverage,
# clean calendar-year boundaries, and matching weather data availability.

# %%
sim_start = pd.Timestamp("2017-01-01", tz="US/Eastern")
sim_end = pd.Timestamp("2026-01-01", tz="US/Eastern")  # exclusive end

# Verify coverage
lmp_window = lmp_da[
    (lmp_da["datetime_local"] >= sim_start)
    & (lmp_da["datetime_local"] < sim_end)
].copy().sort_values("datetime_local").reset_index(drop=True)

expected_hours = int((sim_end - sim_start).total_seconds() / 3600)
print(f"Simulation window: {sim_start.date()} → {sim_end.date()} (exclusive)")
print(f"Expected hours: {expected_hours}; got LMP rows: {len(lmp_window)}")
print(f"LMP null count: {lmp_window['price'].isna().sum()}")
print(f"LMP non-null fraction: {lmp_window['price'].notna().mean()*100:.2f}%")

sim_dates = pd.date_range(sim_start, sim_end - pd.Timedelta(days=1), freq="D")
print(f"\nTotal days: {len(sim_dates)}")
print(f"Total day-mode executions: {len(sim_dates) * 3} (across 3 modes)")

# Henry Hub for window
henry = gas[gas["hub_name"] == "Henry Hub"].copy()
henry["trade_date_dt"] = pd.to_datetime(henry["trade_date"]).dt.date
print(f"\nHenry Hub coverage: {henry['trade_date_dt'].min()} → {henry['trade_date_dt'].max()}")

# Weather temp_f
weather_window = weather.loc[
    (weather.index >= sim_start) & (weather.index < sim_end)
].copy()
weather_window["temp_f"] = weather_window["temperature_2m"] * 9 / 5 + 32
print(f"Weather: {weather_window.index.min()} → {weather_window.index.max()}; rows: {len(weather_window)}")

# %% [markdown]
# ---
# ## §C — State + LTSA state dataclasses

# %%
@dataclass
class PlantState:
    """Plant state vector (inherited from N3) with N4 additions for outage tracking."""
    # Engineering state (from N3)
    eoh: float = 24_000.0
    hr_recov: float = 0.0
    fouling: float = 0.0
    dc: float = 0.0
    df: float = 0.0
    tbc_time: float = 0.0
    tbc_thresh: float = TBC_WEIBULL_ETA
    hrsg_cycles: float = 0.0
    rotor_life: float = 0.35

    # Operational continuity
    op: bool = False
    hrs_off: float = 24.0
    run_hrs: float = 0.0
    last_stype: str = "cold"

    # Inspection tracking
    insp_done: int = 0

    # NEW for N4: outage state
    outage_days_remaining: int = 0
    outage_type: str = ""  # "CI" / "MI" / "forced_gt" / "forced_hrsg" / "forced_bg"


def init_state(seed: int = 42) -> PlantState:
    rng = np.random.default_rng(seed)
    return PlantState(tbc_thresh=float(TBC_WEIBULL_ETA * rng.weibull(TBC_WEIBULL_BETA)))


def init_ltsa_state() -> dict:
    """Initialize the 7-stream LTSA accrual state (all cumulative dollars)."""
    return {
        "fixed_fee_cum": 0.0,
        "eoh_reserve_cum": 0.0,
        "ci_owner_cum": 0.0,         # owner-uncovered portion of CI events
        "mi_owner_cum": 0.0,         # owner-uncovered portion of MI events
        "overage_cum": 0.0,
        "avail_penalty_cum": 0.0,
        "hr_penalty_cum": 0.0,
        "outage_forced_cum": 0.0,    # owner-cost from forced outages
        # YTD trackers (reset each year)
        "ytd_year": 0,
        "ytd_starts_hot": 0,
        "ytd_starts_warm": 0,
        "ytd_starts_cold": 0,
        "ytd_calendar_days": 0,
        "ytd_avail_days": 0,         # days not in any outage
        "ytd_fuel_mmbtu_3xcc": 0.0,
        "ytd_mwh_3xcc": 0.0,
        # Cycle-end HR penalty tracking (between inspections)
        "cycle_fuel_mmbtu": 0.0,
        "cycle_mwh": 0.0,
    }


# %% [markdown]
# ---
# ## §D — Maintenance schedule pre-builder

# %%
def snap_to_shoulder(date: pd.Timestamp) -> pd.Timestamp:
    """Snap forward to next April 1 or October 1 ≥ date."""
    year = date.year
    candidates = [
        pd.Timestamp(year, 4, 1, tz="US/Eastern"),
        pd.Timestamp(year, 10, 1, tz="US/Eastern"),
        pd.Timestamp(year + 1, 4, 1, tz="US/Eastern"),
        pd.Timestamp(year + 1, 10, 1, tz="US/Eastern"),
    ]
    target = date if date.tz is not None else date.tz_localize("US/Eastern")
    for c in candidates:
        if c >= target:
            return c
    return candidates[-1]


def build_maint_schedule(mode: str, start_date: pd.Timestamp, initial_eoh: float,
                         end_date: pd.Timestamp) -> list[dict]:
    """Pre-build the inspection calendar for the simulation horizon.

    For each upcoming threshold (next CI = (eoh // CI_INTERVAL + 1) × CI_INTERVAL,
    next MI = same with MI_INTERVAL), project days-to-threshold using the
    mode-adjusted EOH rate estimate and snap to next April/October.

    Returns: list of dicts with type, scheduled_date, threshold_eoh, completed.
    """
    schedule = []
    eoh_rate = EOH_RATE_ESTIMATE_PER_DAY * MODE_EOH_RATE_MULT[mode]
    cur_eoh = initial_eoh
    cur_date = start_date

    while cur_date < end_date + pd.Timedelta(days=365):  # buffer past sim end
        next_ci = ((int(cur_eoh) // CI_EOH_INTERVAL) + 1) * CI_EOH_INTERVAL
        next_mi = ((int(cur_eoh) // MI_EOH_INTERVAL) + 1) * MI_EOH_INTERVAL

        if next_mi <= next_ci:
            event_type = "MI"
            target_eoh = next_mi
        else:
            event_type = "CI"
            target_eoh = next_ci

        days_to_threshold = (target_eoh - cur_eoh) / max(eoh_rate, 0.1)
        projected_date = cur_date + pd.Timedelta(days=days_to_threshold)
        snapped = snap_to_shoulder(projected_date)

        schedule.append({
            "type": event_type,
            "scheduled_date": snapped,
            "threshold_eoh": target_eoh,
            "completed": False,
        })

        cur_eoh = target_eoh
        cur_date = snapped

        # Safety: cap schedule at 20 events to avoid runaway
        if len(schedule) >= 20:
            break

    return schedule


# Preview each mode's pre-built schedule
print("Pre-built maintenance schedules (initial EOH 24,000; rate 8 EOH/day × mode mult):")
for mode_label in ["A", "B", "C"]:
    sched = build_maint_schedule(mode_label, sim_start, 24_000.0, sim_end)
    print(f"\nMode {mode_label} ({MODE_EOH_RATE_MULT[mode_label]}× burn rate):")
    for evt in sched[:6]:
        print(f"  {evt['type']} @ EOH {evt['threshold_eoh']:>6} → snap-date {evt['scheduled_date'].date()}")


# %% [markdown]
# ---
# ## §E — Daily-loop helpers

# %% [markdown]
# ### §E.1 — Effective parameters (inherited from N3)

# %%
def ambient_derate_factor(temp_f: float, gen: dict) -> float:
    summer_derate = v(gen["summer_derate_pct"])
    winter_boost = v(gen["winter_boost_pct"])
    if temp_f >= 90:
        return 1.0 - summer_derate / 100
    if temp_f <= 32:
        return 1.0 + winter_boost / 100
    frac = (temp_f - 32) / (90 - 32)
    return (1.0 + winter_boost / 100) + frac * ((1.0 - summer_derate / 100) - (1.0 + winter_boost / 100))


def ambient_wear_factor(temp_f: float) -> float:
    """Hot-section wear maintenance factor vs ambient, re-anchored at AMBIENT_WEAR_REF_F.

    ~1.0 at the reference ambient; >1 when hotter (faster creep / TBC oxidation),
    <1 when colder (cooler cooling-air → cooler metal). Bounded to [MIN, MAX].
    Applied ONLY to the hot-section accumulators (creep dc, tbc_time) and ONLY over
    fired hours — see update_stress(). The reference is set to the fired-hour-weighted
    mean ambient so the applied factor REDISTRIBUTES wear toward hot hours rather than
    re-levelling the calibrated total (validated per run: Σ weighted ≈ Σ raw fired hrs).
    """
    f = 1.0 + AMBIENT_WEAR_SENS_PER_F * (temp_f - AMBIENT_WEAR_REF_F)
    return min(AMBIENT_WEAR_FACTOR_MAX, max(AMBIENT_WEAR_FACTOR_MIN, f))


def hr_clean_for_mode(mode_name: str) -> float:
    return MODES[mode_name]["hr_btu_per_kwh"]


def hr_degraded_for_mode(mode_name: str, state: PlantState) -> float:
    return hr_clean_for_mode(mode_name) * (1 + state.hr_recov / 100) * (1 + state.fouling / 100)


def cap_eff_for_mode(mode_name: str, temp_f: float) -> float:
    derate_ct = ambient_derate_factor(temp_f, gens["GEN1"])
    derate_ca = ambient_derate_factor(temp_f, gens["GEN4"])
    if mode_name == "3xCC_full":
        return 3 * NAMEPLATE_CT * derate_ct + NAMEPLATE_CA * derate_ca
    if mode_name == "2xCC":
        return 2 * NAMEPLATE_CT * derate_ct + NAMEPLATE_CA * derate_ca
    if mode_name == "1xCC":
        return NAMEPLATE_CT * derate_ct + NAMEPLATE_CA * derate_ca
    return 0.0


# %% [markdown]
# ### §E.2 — Mode-aware dispatch (N3 extended with wear penalty)

# %%
def dispatch_day_mode_aware(
    state: PlantState,
    hourly_inputs: pd.DataFrame,
    gas_henry_hub: float,
    must_run: bool,
    use_degraded_hr: bool,
    wear_mult: float,
) -> dict:
    """Mode-aware dispatch: applies a wear-penalty hurdle to start decisions.

    When the plant is currently off, the per-hour spark must exceed
    (wear_penalty / MIN_RUN_HOURS_FOR_AMORTIZATION) per MW of capacity for a
    start to be economic. Higher wear_mult → higher start hurdle → fewer starts.
    """
    delivered_fuel_per_mmbtu = gas_henry_hub + RGGI_COST_PER_MMBTU

    mode_seq = []
    mw_seq = []
    revenue = 0.0
    fuel_mmbtu_total = 0.0
    starts: list[str] = []
    wear_penalty_paid = 0.0  # total wear-penalty $ for this day (informational)
    fired_hours_hotweighted = 0.0  # Σ ambient_wear_factor over fired hours (B3 ambient half, ADR-006)

    # Track operational continuity hour-by-hour
    op = state.op
    hrs_off = state.hrs_off

    for _, row in hourly_inputs.iterrows():
        lmp = row["lmp"]
        temp_f = row["temp_f"]

        # Determine candidate start type based on hours-off so far
        if hrs_off < 8:
            stype_candidate = "hot"
        elif hrs_off < 72:
            stype_candidate = "warm"
        else:
            stype_candidate = "cold"

        # Wear penalty per MW of capacity if a start fires (only applies when starting)
        # = wear_mult × GT_WEAR_FRACTION × Kumar start C&M ($/MW)
        wear_penalty_per_mw = wear_mult * GT_WEAR_FRACTION_OF_START * START_CM_USD_PER_MW[stype_candidate]
        # Amortize over expected min-run hours → an effective per-MWh hurdle
        wear_hurdle_per_mwh = wear_penalty_per_mw / MIN_RUN_HOURS_FOR_AMORTIZATION

        # B2 / step #2 commitment hurdle (always-on; added 2026-05-27).
        # A start must recover the FULL Kumar start C&M (not just the 0.42 wear fraction), amortized
        # over the min-run window — independent of EOH/wear policy. This is the "don't start the plant
        # for a marginal hour" commitment economics real operators apply. Without it the model self-
        # commits to any spark>0 hour and over-commits ~2x vs MOR (backtest_findings §3.6). The policy-
        # mode wear_hurdle above remains as ADDITIONAL preservation pressure near EOH thresholds.
        # Warming fuel is costed separately (ADR-002), so START_CM (non-fuel C&M) does not double-count.
        commitment_hurdle_per_mwh = START_CM_USD_PER_MW[stype_candidate] / MIN_RUN_HOURS_FOR_AMORTIZATION

        # Compute best mode this hour
        best_mode = None
        best_margin = -float("inf")
        best_mw = 0.0
        for mode_name in MODES:
            hr = hr_degraded_for_mode(mode_name, state) if use_degraded_hr else hr_clean_for_mode(mode_name)
            cap_mw = cap_eff_for_mode(mode_name, temp_f)
            fuel_cost = hr / 1000 * delivered_fuel_per_mmbtu
            spark = lmp - fuel_cost - VOM_USD_PER_MWH
            # Add commitment + wear hurdles ONLY when starting (currently off)
            effective_spark = spark - ((commitment_hurdle_per_mwh + wear_hurdle_per_mwh) if not op else 0.0)
            margin = max(effective_spark, 0) * cap_mw
            if margin > best_margin:
                best_margin = margin
                best_mode = mode_name
                best_mw = cap_mw

        if best_margin <= 0:
            if must_run:
                mode = "1xCC"
                hr = hr_degraded_for_mode(mode, state) if use_degraded_hr else hr_clean_for_mode(mode)
                cap_mw = cap_eff_for_mode(mode, temp_f)
                fuel_cost = hr / 1000 * delivered_fuel_per_mmbtu
                spark = lmp - fuel_cost - VOM_USD_PER_MWH
                mw_dispatched = cap_mw
            else:
                mode = "offline"
                mw_dispatched = 0.0
        else:
            mode = best_mode
            mw_dispatched = best_mw

        # Detect start event
        if mode != "offline" and not op:
            if hrs_off < 8:
                stype = "hot"
            elif hrs_off < 72:
                stype = "warm"
            else:
                stype = "cold"
            starts.append(stype)
            # Cash wear penalty (informational — actual GT damage hits state via FATIGUE_PER_*_START)
            wear_penalty_paid += wear_mult * GT_WEAR_FRACTION_OF_START * START_CM_USD_PER_MW[stype] * mw_dispatched
            op = True
            hrs_off = 0.0
        elif mode == "offline" and op:
            op = False
            hrs_off = 1.0
        elif mode == "offline":
            hrs_off += 1.0

        if mode != "offline":
            hr_used = hr_degraded_for_mode(mode, state) if use_degraded_hr else hr_clean_for_mode(mode)
            fuel_mmbtu = mw_dispatched * hr_used / 1000
            fuel_mmbtu_total += fuel_mmbtu
            revenue += lmp * mw_dispatched
            fired_hours_hotweighted += ambient_wear_factor(temp_f)
        mode_seq.append(mode)
        mw_seq.append(mw_dispatched)

    fired_hours = sum(1 for mh in mode_seq if mh != "offline")
    total_mwh = sum(mw_seq)
    fuel_cost_total = fuel_mmbtu_total * gas_henry_hub
    rggi_cost_total = fuel_mmbtu_total * RGGI_COST_PER_MMBTU
    vom_cost_total = total_mwh * VOM_USD_PER_MWH
    gross_margin = revenue - fuel_cost_total - rggi_cost_total - vom_cost_total

    return {
        "total_mwh": total_mwh,
        "fired_hours": fired_hours,
        "fired_hours_hotweighted": fired_hours_hotweighted,
        "starts": starts,
        "mode_sequence": mode_seq,
        "fuel_mmbtu_total": fuel_mmbtu_total,
        "revenue_usd": revenue,
        "fuel_cost_usd": fuel_cost_total,
        "rggi_cost_usd": rggi_cost_total,
        "vom_cost_usd": vom_cost_total,
        "gross_margin_usd": gross_margin,
        "wear_penalty_paid_usd": wear_penalty_paid,
        "ending_op": op,
        "ending_hrs_off": hrs_off,
    }


# %% [markdown]
# ### §E.3 — Stress accumulator update (inherited from N3)

# %%
def update_stress(state: PlantState, fired_hours: float, starts: list[str],
                  fired_hours_hot: float | None = None) -> float:
    """Update state in-place. Returns delta_eoh (for LTSA accrual).

    `fired_hours_hot` is the ambient-weighted fired-hours sum (Σ ambient_wear_factor
    over fired hours, ADR-006). It drives ONLY the hot-section accumulators — creep
    (state.dc) and TBC life (state.tbc_time) — which are metal-temperature sensitive.
    The other terms stay on raw `fired_hours` by design (ADR-006 §2):
      • eoh        — the contractual EOH clock; ambient is not a standard EOH driver
                     (peak-fire/load is, and load is the deferred half).
      • fouling    — compressor fouling is air-quality/humidity driven (FOULING_AQI_PROXY
                     is the hook), not hot-section thermal.
      • rotor_life — thick LCF-limited component; weak ambient sensitivity in v1.
      • df         — per-start LCF; ambient at start is second-order.
    If `fired_hours_hot` is None the function is identical to the pre-ADR-006 behaviour
    (back-compatible default = no ambient weighting).
    """
    if fired_hours_hot is None:
        fired_hours_hot = fired_hours
    start_eoh = sum(START_EOH_COST.get(s, 10.0) for s in starts)
    delta_eoh = fired_hours + start_eoh
    state.eoh += delta_eoh

    if fired_hours > 0:
        delta = (FOULING_ASYMPTOTE_PCT - state.fouling) * (fired_hours / FOULING_TAU_HRS) * FOULING_AQI_PROXY
        state.fouling = min(FOULING_ASYMPTOTE_PCT, state.fouling + delta)

    state.hr_recov += fired_hours * 1e-5 * 100
    state.dc += CREEP_RATE_PER_FIRED_HOUR * fired_hours_hot  # hot-section: ambient-weighted

    for stype in starts:
        if stype == "cold":
            state.df += FATIGUE_PER_COLD_START
        elif stype == "warm":
            state.df += FATIGUE_PER_WARM_START
        elif stype == "hot":
            state.df += FATIGUE_PER_HOT_START

    if state.dc > 0.05 and state.df > 0.05 and (state.dc + state.df) > D_LIM:
        state.dc *= 0.5
        state.df *= 0.5

    state.tbc_time += fired_hours_hot  # hot-section: ambient-weighted
    state.hrsg_cycles += HRSG_CYCLES_PER_START * len(starts)
    state.rotor_life += ROTOR_LIFE_PER_FIRED_HOUR * fired_hours

    if starts:
        state.last_stype = starts[-1]

    return delta_eoh


# %% [markdown]
# ### §E.4 — Forced outage probability (inherited from N3, with aging cap fix)
#
# **Lockport-specific correction to N3**: the aging multiplier formula
# `age_mult = 1 + year_frac × (MAX - 1)` is intended to ramp from 1× → 1.5× over
# a 10-year aging window per the framework convention. In N3 we passed
# `year_frac = day_idx / 365.0`, which is "years elapsed", not "fraction of
# aging window". Over a 30-day window the bug is invisible (year_frac < 0.1).
# Over a 9-year window it compounds to 5.5× — implausible. N4 caps aging at
# `min(years_elapsed / 10, 1.0)`. Documented in §R decision log.

# %%
AGING_WINDOW_YEARS = 10.0

def p_forced_components(state: PlantState, years_elapsed: float = 0.0) -> dict:
    excess = max(0.0, state.df / COMB_BUDGET - P_COMBUSTION_INFLECTION)
    p_comb = min(P_COMBUSTION_SCALE * (excess ** 2), P_FORCED_DAY_CAP)

    if state.tbc_time >= state.tbc_thresh:
        p_tbc = 1.0
    else:
        t = state.tbc_time
        if t > 0:
            p_tbc = (TBC_WEIBULL_BETA / TBC_WEIBULL_ETA) * (t / TBC_WEIBULL_ETA) ** (TBC_WEIBULL_BETA - 1) * 24
            p_tbc = min(p_tbc, P_FORCED_DAY_CAP)
        else:
            p_tbc = 0.0

    p_rotor = 0.00003 * state.rotor_life

    # Creep-rupture hazard (ADR-007): hockey-stick on creep life-fraction, mirroring p_comb.
    excess_creep = max(0.0, state.dc / CREEP_BUDGET - P_CREEP_INFLECTION)
    p_creep = min(P_CREEP_SCALE * (excess_creep ** 2), P_FORCED_DAY_CAP)

    p_gt = p_comb + p_tbc + p_rotor + p_creep

    # Capped aging fraction (years_elapsed / 10 capped at 1.0)
    aging_frac = min(years_elapsed / AGING_WINDOW_YEARS, 1.0)
    age_mult_hrsg = 1.0 + aging_frac * (HRSG_AGE_MULT_MAX - 1.0)
    p_hrsg = HRSG_BASE_PROB_PER_DAY * age_mult_hrsg

    age_mult_bg = 1.0 + aging_frac * (BG_AGE_MULT_MAX - 1.0)
    p_bg = BG_BASE_PROB_PER_DAY * age_mult_bg

    p_combined = 1 - (1 - min(p_gt, 1.0)) * (1 - min(p_hrsg, 1.0)) * (1 - min(p_bg, 1.0))

    return {
        "p_combustion": p_comb,
        "p_tbc": p_tbc,
        "p_rotor": p_rotor,
        "p_creep": p_creep,
        "p_gt": p_gt,
        "p_hrsg": p_hrsg,
        "p_bg": p_bg,
        "p_combined": p_combined,
    }


# %% [markdown]
# ### §E.5 — Inspection event handler

# %%
def apply_inspection_reset(state: PlantState, event_type: str, rng: np.random.Generator) -> None:
    """Apply state resets per prototype convention §6.

    CI: dc / df halve; fouling reduced by 70% (water wash); hr_recov keeps 30%.
    MI: dc / df → 0; fouling reduced by 70%; hr_recov keeps 25% (75% recovered);
        tbc_time → 0; tbc_thresh resampled from Weibull; hrsg_cycles → 0; rotor_life keeps 50%.
    """
    if event_type == "CI":
        state.dc *= 0.5
        state.df *= 0.5
        state.fouling *= 0.3  # 70% washed
        state.hr_recov *= 0.3  # 70% recoverable degradation cleaned up
    elif event_type == "MI":
        state.dc = 0.0
        state.df = 0.0
        state.fouling *= 0.3
        state.hr_recov *= 0.25
        state.tbc_time = 0.0
        state.tbc_thresh = float(TBC_WEIBULL_ETA * rng.weibull(TBC_WEIBULL_BETA))
        state.hrsg_cycles = 0.0
        state.rotor_life *= 0.5

    state.insp_done += 1


def sample_outage_cause(rng: np.random.Generator, pf: dict) -> str:
    """Sample forced outage cause weighted by component probability."""
    weights = np.array([pf["p_gt"], pf["p_hrsg"], pf["p_bg"]])
    weights = weights / weights.sum() if weights.sum() > 0 else np.array([1/3, 1/3, 1/3])
    causes = ["gt", "hrsg", "bg"]
    return causes[rng.choice(3, p=weights)]


def sample_outage_duration(rng: np.random.Generator, cause: str) -> int:
    """Sample outage duration in days (lognormal)."""
    median = OUTAGE_DURATION_DAYS[cause]
    duration = int(rng.lognormal(np.log(median), OUTAGE_DURATION_SIGMA))
    return max(1, duration)


# %% [markdown]
# ### §E.6 — LTSA accrual helpers

# %%
def daily_escalation(today: pd.Timestamp, start: pd.Timestamp) -> float:
    """Cumulative escalation factor for today vs sim start."""
    years_elapsed = (today - start).days / 365.0
    return (1 + LTSA_ESCALATION_PCT_PER_YEAR / 100) ** years_elapsed


def accrue_daily_ltsa(ltsa_state: dict, today: pd.Timestamp, sim_start_dt: pd.Timestamp,
                      delta_eoh: float, day_starts: list[str]) -> None:
    """Daily LTSA accrual: fixed fee + EOH reserve + start-overage daily increment.

    Start overage is computed daily by comparing YTD starts vs pro-rated annual
    baseline; if YTD exceeds pro-rated baseline for a type, the marginal start
    today charges OVERAGE_CHARGE.
    """
    esc = daily_escalation(today, sim_start_dt)

    # Stream 1: fixed fee
    ltsa_state["fixed_fee_cum"] += LTSA_FIXED_DAILY * esc

    # Stream 2: EOH reserve
    ltsa_state["eoh_reserve_cum"] += delta_eoh * LTSA_EOH_RESERVE_USD_PER_EOH * esc

    # Stream 5: start overage — daily increment, per type
    day_of_year = today.timetuple().tm_yday  # 1..365
    pro_rated = {
        s: OVERAGE_BASELINE[s] * day_of_year / 365.0
        for s in ["hot", "warm", "cold"]
    }

    # Count today's starts by type, and increment YTD counters AFTER comparing
    today_counts = {"hot": 0, "warm": 0, "cold": 0}
    for s in day_starts:
        if s in today_counts:
            today_counts[s] += 1

    # For each start today, if YTD before this start ≥ pro-rated baseline, charge overage
    for s in ["hot", "warm", "cold"]:
        ytd_key = f"ytd_starts_{s}"
        for _ in range(today_counts[s]):
            ytd_before = ltsa_state[ytd_key]
            if ytd_before >= pro_rated[s]:
                ltsa_state["overage_cum"] += OVERAGE_CHARGE[s] * esc
            ltsa_state[ytd_key] += 1


def apply_year_end_avail_penalty(ltsa_state: dict, year: int) -> float:
    """If YTD availability < guarantee_pct, apply penalty. Returns penalty applied."""
    cal_days = ltsa_state["ytd_calendar_days"]
    avail_days = ltsa_state["ytd_avail_days"]
    if cal_days == 0:
        return 0.0
    annual_avail = avail_days / cal_days
    if annual_avail < AVAIL_GUARANTEE_PCT / 100:
        shortfall = (AVAIL_GUARANTEE_PCT / 100) - annual_avail
        penalty = (LTSA_FIXED_MONTHLY_USD / 12) * shortfall * 10
        ltsa_state["avail_penalty_cum"] += penalty
        return penalty
    return 0.0


def apply_inspection_hr_penalty(ltsa_state: dict, ci_or_mi: str, esc: float) -> float:
    """If cycle-avg HR > guarantee × (1 + tolerance), apply penalty."""
    if ltsa_state["cycle_mwh"] == 0 or ltsa_state["cycle_fuel_mmbtu"] == 0:
        return 0.0
    avg_hr = ltsa_state["cycle_fuel_mmbtu"] * 1_000_000 / (ltsa_state["cycle_mwh"] * 1000)
    threshold = HR_GUARANTEE_BTU_PER_KWH * (1 + HR_TOLERANCE_PCT / 100)
    if avg_hr > threshold:
        excess_btu_per_kwh = avg_hr - threshold
        excess_mmbtu = excess_btu_per_kwh * ltsa_state["cycle_mwh"] / 1000
        # Excess fuel cost at average gas + RGGI (approx; full would track gas history)
        excess_cost = excess_mmbtu * (3.50 + RGGI_COST_PER_MMBTU)  # ~$3.50 avg Henry Hub
        penalty = excess_cost * HR_PENALTY_MULTIPLIER * esc
        ltsa_state["hr_penalty_cum"] += penalty
        # Reset cycle counter
        ltsa_state["cycle_fuel_mmbtu"] = 0.0
        ltsa_state["cycle_mwh"] = 0.0
        return penalty
    ltsa_state["cycle_fuel_mmbtu"] = 0.0
    ltsa_state["cycle_mwh"] = 0.0
    return 0.0


# %% [markdown]
# ---
# ## §F — Run one mode (the main loop)

# %%
def run_mode(mode: str, seed: int = 42) -> dict:
    """Historical-replay convenience wrapper.

    Runs the engine over the module-level historical market windows
    (sim_dates / sim_start / sim_end / lmp_window / weather_window / henry),
    reproducing the original notebook-4 behaviour exactly.
    """
    return run_path(mode, seed, sim_dates, sim_start, sim_end,
                    lmp_window, weather_window, henry)


def run_path(mode: str, seed: int, sim_dates, sim_start, sim_end,
             lmp_window, weather_window, henry, init_state_override=None) -> dict:
    """Run the full simulation for a given mode over an INJECTED market path.

    This is the engine entry point used by both the historical driver (notebook 4,
    via run_mode) and the forward scenario runner (src/forward). The six market-path
    arguments are the only per-run inputs; all asset config + constants are module-level.

    init_state_override: when given a PlantState, the run STARTS from that aged state
    instead of the fresh modeling-convention default (init_state). The forward runner
    uses this to carry the historical end-state (EOH near the inspection threshold) so
    the A/B/C preservation premium actually binds (ADR-009). A defensive copy is taken
    so the caller's state object is never mutated by the run loop. Default None keeps
    the historical path byte-identical (regression-gated).

    Returns daily records + inspection events + forced outage events + final state + ltsa_state.
    """
    state = init_state(seed=seed) if init_state_override is None else replace(init_state_override)
    ltsa_state = init_ltsa_state()
    schedule = build_maint_schedule(mode, sim_start, state.eoh, sim_end)
    rng = np.random.default_rng(seed=seed)

    daily_records = []
    inspection_events = []
    forced_outage_events = []

    # Pre-index daily LMP and weather
    lmp_window_indexed = lmp_window.set_index("datetime_local")
    weather_indexed = weather_window["temp_f"]

    # Cogen must-run flag (synthetic, per-day): coldest 20% across full window
    daily_mean_temp = weather_window.groupby(weather_window.index.date)["temp_f"].mean()
    must_run_threshold = daily_mean_temp.quantile(0.20)
    must_run_days = set(daily_mean_temp[daily_mean_temp <= must_run_threshold].index)

    n_days = len(sim_dates)
    last_print_year = None

    for day_idx, day in enumerate(sim_dates):
        day_date = day.date()
        day_start_eastern = pd.Timestamp(day_date, tz="US/Eastern")
        day_end_eastern = day_start_eastern + pd.Timedelta(hours=24)

        if day_date.year != last_print_year:
            last_print_year = day_date.year

        # YTD year tracking + year-end checks
        if ltsa_state["ytd_year"] != day_date.year:
            # Year boundary: apply year-end avail penalty for prior year
            if ltsa_state["ytd_year"] != 0:
                pen = apply_year_end_avail_penalty(ltsa_state, ltsa_state["ytd_year"])
            # Reset YTD trackers
            ltsa_state["ytd_year"] = day_date.year
            ltsa_state["ytd_starts_hot"] = 0
            ltsa_state["ytd_starts_warm"] = 0
            ltsa_state["ytd_starts_cold"] = 0
            ltsa_state["ytd_calendar_days"] = 0
            ltsa_state["ytd_avail_days"] = 0
            ltsa_state["ytd_fuel_mmbtu_3xcc"] = 0.0
            ltsa_state["ytd_mwh_3xcc"] = 0.0

        ltsa_state["ytd_calendar_days"] += 1

        # ====== Handle continuing outage ======
        if state.outage_days_remaining > 0:
            esc = daily_escalation(day_start_eastern, sim_start)
            # Accrue fixed fee even during outage
            ltsa_state["fixed_fee_cum"] += LTSA_FIXED_DAILY * esc
            state.outage_days_remaining -= 1
            if state.outage_days_remaining == 0:
                state.outage_type = ""
                state.op = False
                state.hrs_off = 24.0

            daily_records.append({
                "day_idx": day_idx,
                "date": day_date,
                "mode": mode,
                "in_outage": True,
                "outage_type": state.outage_type,
                "mwh_clean": 0.0,
                "mwh_degraded": 0.0,
                "margin_clean": 0.0,
                "margin_degraded": 0.0,
                "loss_degradation": 0.0,
                "fired_hours": 0,
                "fired_hours_hot": 0.0,
                "starts_count": 0,
                "cold_starts": 0,
                "delta_eoh": 0.0,
                "wear_penalty_paid": 0.0,
                "warming_cost_degraded": 0.0,
                "eoh": state.eoh,
                "hr_recov": state.hr_recov,
                "fouling": state.fouling,
                "dc": state.dc,
                "df": state.df,
                "p_combined": 0.0,
                "mode_3x_hours": 0,
                "mode_2x_hours": 0,
                "mode_1x_hours": 0,
                "offline_hours": 24,
                "fixed_fee_cum": ltsa_state["fixed_fee_cum"],
                "eoh_reserve_cum": ltsa_state["eoh_reserve_cum"],
                "ci_owner_cum": ltsa_state["ci_owner_cum"],
                "mi_owner_cum": ltsa_state["mi_owner_cum"],
                "overage_cum": ltsa_state["overage_cum"],
                "avail_penalty_cum": ltsa_state["avail_penalty_cum"],
                "hr_penalty_cum": ltsa_state["hr_penalty_cum"],
                "outage_forced_cum": ltsa_state["outage_forced_cum"],
            })
            continue

        # Day is "available" for LTSA availability tracking
        ltsa_state["ytd_avail_days"] += 1

        # ====== Build daily inputs ======
        day_lmp_slice = lmp_window[
            (lmp_window["datetime_local"] >= day_start_eastern)
            & (lmp_window["datetime_local"] < day_end_eastern)
        ].sort_values("datetime_local").reset_index(drop=True)
        day_weather_slice = weather_window.loc[
            (weather_window.index >= day_start_eastern)
            & (weather_window.index < day_end_eastern)
        ].copy()

        # Build hourly DataFrame
        lmp_arr = day_lmp_slice["price"].values[:24]
        temp_arr = day_weather_slice["temp_f"].values[:24]
        # Pad if needed (DST short days or missing rows)
        if len(lmp_arr) < 24:
            if len(lmp_arr) == 0:
                lmp_arr = np.full(24, np.nan)
            else:
                lmp_arr = np.concatenate([lmp_arr, np.full(24 - len(lmp_arr), lmp_arr[-1])])
        if len(temp_arr) < 24:
            if len(temp_arr) == 0:
                temp_arr = np.full(24, 50.0)
            else:
                temp_arr = np.concatenate([temp_arr, np.full(24 - len(temp_arr), temp_arr[-1])])

        # Backfill NaN LMP with forward-fill (rare)
        lmp_series = pd.Series(lmp_arr).ffill().bfill()
        hourly = pd.DataFrame({"hour": range(24), "lmp": lmp_series.values, "temp_f": temp_arr})

        # Henry Hub for this day
        hh_match = henry[henry["trade_date_dt"] <= day_date].sort_values("trade_date_dt").tail(1)
        if len(hh_match) == 0:
            gas_hh = float(henry.iloc[0]["price_usd_per_mmbtu"])
        else:
            gas_hh = float(hh_match.iloc[0]["price_usd_per_mmbtu"])

        must_run_today = day_date in must_run_days

        # ====== Forced outage check (sample at start of day, based on yesterday's state) ======
        years_elapsed = day_idx / 365.0
        pf = p_forced_components(state, years_elapsed=years_elapsed)
        forced_fired = False
        trip_delta_eoh = 0.0
        if rng.random() < pf["p_combined"]:
            was_running = state.op  # ADR-007: a forced outage from a running state is a trip FROM LOAD
            cause = sample_outage_cause(rng, pf)
            duration = sample_outage_duration(rng, cause)
            # Cost
            owner_cost = OUTAGE_OWNER_COST_USD[cause]
            ltsa_state["outage_forced_cum"] += owner_cost
            # Trip-induced wear (ADR-007, GER-3620): a trip from load adds ~8 factored starts
            # of hot-section damage. v1 runs full-load when on → full-load trip. No extra wear
            # if the unit was already offline (not a trip from load).
            if was_running:
                state.df += TRIP_MAINTENANCE_FACTOR * FATIGUE_PER_COLD_START
                trip_delta_eoh = TRIP_MAINTENANCE_FACTOR * START_EOH_COST["cold"]
                state.eoh += trip_delta_eoh
            forced_outage_events.append({
                "mode": mode,
                "date": day_date,
                "cause": cause,
                "duration_days": duration,
                "owner_cost_usd": owner_cost,
                "p_forced_at_event": pf["p_combined"],
                "state_eoh": state.eoh,
                "state_df": state.df,
                "was_trip": bool(was_running),
                "trip_delta_eoh": trip_delta_eoh,
            })
            state.outage_type = f"forced_{cause}"
            state.outage_days_remaining = duration - 1  # this day counts as day 1 of outage
            # End availability
            ltsa_state["ytd_avail_days"] -= 1
            forced_fired = True

        if forced_fired:
            daily_records.append({
                "day_idx": day_idx,
                "date": day_date,
                "mode": mode,
                "in_outage": True,
                "outage_type": state.outage_type,
                "mwh_clean": 0.0,
                "mwh_degraded": 0.0,
                "margin_clean": 0.0,
                "margin_degraded": 0.0,
                "loss_degradation": 0.0,
                "fired_hours": 0,
                "fired_hours_hot": 0.0,
                "starts_count": 0,
                "cold_starts": 0,
                "delta_eoh": trip_delta_eoh,
                "wear_penalty_paid": 0.0,
                "warming_cost_degraded": 0.0,
                "eoh": state.eoh,
                "hr_recov": state.hr_recov,
                "fouling": state.fouling,
                "dc": state.dc,
                "df": state.df,
                "p_combined": pf["p_combined"],
                "mode_3x_hours": 0,
                "mode_2x_hours": 0,
                "mode_1x_hours": 0,
                "offline_hours": 24,
                "fixed_fee_cum": ltsa_state["fixed_fee_cum"],
                "eoh_reserve_cum": ltsa_state["eoh_reserve_cum"],
                "ci_owner_cum": ltsa_state["ci_owner_cum"],
                "mi_owner_cum": ltsa_state["mi_owner_cum"],
                "overage_cum": ltsa_state["overage_cum"],
                "avail_penalty_cum": ltsa_state["avail_penalty_cum"],
                "hr_penalty_cum": ltsa_state["hr_penalty_cum"],
                "outage_forced_cum": ltsa_state["outage_forced_cum"],
            })
            # Still accrue fixed-fee for the day (+ EOH reserve on any trip-induced EOH)
            esc = daily_escalation(day_start_eastern, sim_start)
            ltsa_state["fixed_fee_cum"] += LTSA_FIXED_DAILY * esc
            ltsa_state["eoh_reserve_cum"] += trip_delta_eoh * LTSA_EOH_RESERVE_USD_PER_EOH * esc  # ADR-007
            continue

        # ====== EOH headroom + wear penalty for this mode ======
        # Find next non-completed scheduled event
        next_event = None
        for evt in schedule:
            if not evt["completed"]:
                next_event = evt
                break

        if next_event is not None:
            eoh_headroom = next_event["threshold_eoh"] - state.eoh
        else:
            eoh_headroom = 1e9  # no more scheduled events

        wear_mult = wear_penalty_mult(mode, eoh_headroom)

        # ====== Steam-only mode pre-check (Phase J: backtest_findings §3.4) ======
        # On must-run days, compare: does the BEST achievable hour of the day
        # produce positive spark? If not, the whole day is uneconomic and the
        # plant is better off in steam-only mode (HRSG duct burners deliver
        # process steam without CT operation; 0 MWh, 0 EOH wear, only gas cost).
        # Real Lockport does this 25% of days per MOR.
        steam_only_today = False
        if must_run_today:
            day_max_lmp = float(hourly["lmp"].max())
            day_avg_temp_f = float(hourly["temp_f"].mean())
            # Best-case spark: 3xCC at the day's peak LMP using degraded HR
            best_hr = hr_degraded_for_mode("3xCC_full", state)
            best_fuel_cost = best_hr / 1000 * (gas_hh + RGGI_COST_PER_MMBTU)
            best_spark = day_max_lmp - best_fuel_cost - VOM_USD_PER_MWH
            if best_spark <= 0:
                # No hour of the day will be economic — switch to steam-only
                steam_only_today = True

        if steam_only_today:
            # Steam-only day: gas cost only, 0 MWh, no state changes
            esc = daily_escalation(day_start_eastern, sim_start)
            ltsa_state["fixed_fee_cum"] += LTSA_FIXED_DAILY * esc
            steam_only_fuel_cost = STEAM_ONLY_GAS_MMBTU_PER_DAY * gas_hh
            steam_only_rggi_cost = STEAM_ONLY_GAS_MMBTU_PER_DAY * RGGI_COST_PER_MMBTU
            steam_only_total_cost = steam_only_fuel_cost + steam_only_rggi_cost
            # State unchanged — no CT operation. op stays false; hrs_off increments.
            state.op = False
            state.hrs_off = min(state.hrs_off + 24, 24.0 * 30)  # cap at 30 days
            daily_records.append({
                "day_idx": day_idx,
                "date": day_date,
                "mode": mode,
                "in_outage": False,
                "outage_type": "steam_only",
                "mwh_clean": 0.0,
                "mwh_degraded": 0.0,
                "margin_clean": -steam_only_total_cost,
                "margin_degraded": -steam_only_total_cost,
                "loss_degradation": 0.0,
                "fired_hours": 0,
                "fired_hours_hot": 0.0,
                "starts_count": 0,
                "cold_starts": 0,
                "delta_eoh": 0.0,
                "wear_penalty_paid": 0.0,
                "warming_cost_degraded": 0.0,
                "eoh": state.eoh,
                "hr_recov": state.hr_recov,
                "fouling": state.fouling,
                "dc": state.dc,
                "df": state.df,
                "p_combined": pf["p_combined"],
                "mode_3x_hours": 0,
                "mode_2x_hours": 0,
                "mode_1x_hours": 0,
                "offline_hours": 24,
                "fixed_fee_cum": ltsa_state["fixed_fee_cum"],
                "eoh_reserve_cum": ltsa_state["eoh_reserve_cum"],
                "ci_owner_cum": ltsa_state["ci_owner_cum"],
                "mi_owner_cum": ltsa_state["mi_owner_cum"],
                "overage_cum": ltsa_state["overage_cum"],
                "avail_penalty_cum": ltsa_state["avail_penalty_cum"],
                "hr_penalty_cum": ltsa_state["hr_penalty_cum"],
                "outage_forced_cum": ltsa_state["outage_forced_cum"],
            })
            continue

        # ====== Twin dispatch ======
        dr_clean = dispatch_day_mode_aware(state, hourly, gas_hh, must_run_today,
                                            use_degraded_hr=False, wear_mult=wear_mult)
        dr_degraded = dispatch_day_mode_aware(state, hourly, gas_hh, must_run_today,
                                                use_degraded_hr=True, wear_mult=wear_mult)

        # ====== Min-load floor check (C: structural correctness) ======
        # Verify that any dispatched mode is operating at or above its block-level
        # min-load. In v1, modes dispatch at full capacity so this never binds,
        # but the check documents the constraint for v2 partial-dispatch.
        for mode_label, hourly_mw in zip(dr_degraded["mode_sequence"], range(24)):
            if mode_label in MIN_LOAD_BY_MODE:
                pass  # In v1 we dispatch at full capacity > min_load; no-op for now

        # ====== Cold-start warming gas (ADR-002 Correction 1) ======
        cold_starts_clean = sum(1 for s in dr_clean["starts"] if s == "cold")
        cold_starts_degraded = sum(1 for s in dr_degraded["starts"] if s == "cold")
        warming_clean = cold_starts_clean * MOR_COLD_START_GAS_MMBTU * (gas_hh + RGGI_COST_PER_MMBTU)
        warming_degraded = cold_starts_degraded * MOR_COLD_START_GAS_MMBTU * (gas_hh + RGGI_COST_PER_MMBTU)
        dr_clean["gross_margin_usd"] -= warming_clean
        dr_degraded["gross_margin_usd"] -= warming_degraded

        loss_degradation = dr_clean["gross_margin_usd"] - dr_degraded["gross_margin_usd"]

        # ====== Commit operational state changes ======
        state.op = dr_degraded["ending_op"]
        state.hrs_off = dr_degraded["ending_hrs_off"]

        # ====== Stress accumulator update ======
        delta_eoh = update_stress(state, dr_degraded["fired_hours"], dr_degraded["starts"],
                                   fired_hours_hot=dr_degraded["fired_hours_hotweighted"])

        # ====== Cycle-end HR tracking ======
        ltsa_state["cycle_fuel_mmbtu"] += dr_degraded["fuel_mmbtu_total"]
        ltsa_state["cycle_mwh"] += dr_degraded["total_mwh"]

        # ====== Daily LTSA accrual ======
        accrue_daily_ltsa(ltsa_state, day_start_eastern, sim_start, delta_eoh, dr_degraded["starts"])

        # ====== Inspection trigger check ======
        if next_event is not None:
            calendar_hit = day_start_eastern >= next_event["scheduled_date"]
            hard_stop_hit = state.eoh - next_event["threshold_eoh"] >= INSP_HARD_STOP_EOH_OVERAGE

            if calendar_hit or hard_stop_hit:
                # Trigger this inspection
                evt_type = next_event["type"]
                esc = daily_escalation(day_start_eastern, sim_start)
                if evt_type == "CI":
                    cost = CI_OWNER_UNCOVERED * esc
                    ltsa_state["ci_owner_cum"] += cost
                    outage_days = CI_OUTAGE_DAYS
                else:
                    cost = MI_OWNER_UNCOVERED * esc
                    ltsa_state["mi_owner_cum"] += cost
                    outage_days = MI_OUTAGE_DAYS

                # HR penalty at cycle end
                hr_pen = apply_inspection_hr_penalty(ltsa_state, evt_type, esc)

                inspection_events.append({
                    "mode": mode,
                    "date": day_date,
                    "type": evt_type,
                    "trigger": "calendar" if calendar_hit else "hard_stop",
                    "scheduled_date": next_event["scheduled_date"].date(),
                    "threshold_eoh": next_event["threshold_eoh"],
                    "state_eoh_at_trigger": state.eoh,
                    "outage_days": outage_days,
                    "owner_cost_usd": cost,
                    "hr_penalty_usd": hr_pen,
                })

                # Apply state resets
                apply_inspection_reset(state, evt_type, rng)
                next_event["completed"] = True

                # Start outage
                state.outage_type = evt_type
                state.outage_days_remaining = outage_days - 1  # today counts as day 1
                state.op = False
                state.hrs_off = 24.0
                ltsa_state["ytd_avail_days"] -= 1  # today not available

        daily_records.append({
            "day_idx": day_idx,
            "date": day_date,
            "mode": mode,
            "in_outage": False,
            "outage_type": "",
            "mwh_clean": dr_clean["total_mwh"],
            "mwh_degraded": dr_degraded["total_mwh"],
            "margin_clean": dr_clean["gross_margin_usd"],
            "margin_degraded": dr_degraded["gross_margin_usd"],
            "loss_degradation": loss_degradation,
            "fired_hours": dr_degraded["fired_hours"],
            "fired_hours_hot": dr_degraded["fired_hours_hotweighted"],
            "starts_count": len(dr_degraded["starts"]),
            "cold_starts": cold_starts_degraded,
            "delta_eoh": delta_eoh,
            "wear_penalty_paid": dr_degraded["wear_penalty_paid_usd"],
            "warming_cost_degraded": warming_degraded,
            "eoh": state.eoh,
            "hr_recov": state.hr_recov,
            "fouling": state.fouling,
            "dc": state.dc,
            "df": state.df,
            "p_combined": pf["p_combined"],
            "mode_3x_hours": dr_degraded["mode_sequence"].count("3xCC_full"),
            "mode_2x_hours": dr_degraded["mode_sequence"].count("2xCC"),
            "mode_1x_hours": dr_degraded["mode_sequence"].count("1xCC"),
            "offline_hours": dr_degraded["mode_sequence"].count("offline"),
            "fixed_fee_cum": ltsa_state["fixed_fee_cum"],
            "eoh_reserve_cum": ltsa_state["eoh_reserve_cum"],
            "ci_owner_cum": ltsa_state["ci_owner_cum"],
            "mi_owner_cum": ltsa_state["mi_owner_cum"],
            "overage_cum": ltsa_state["overage_cum"],
            "avail_penalty_cum": ltsa_state["avail_penalty_cum"],
            "hr_penalty_cum": ltsa_state["hr_penalty_cum"],
            "outage_forced_cum": ltsa_state["outage_forced_cum"],
        })

    # Final year avail penalty
    apply_year_end_avail_penalty(ltsa_state, ltsa_state["ytd_year"])

    daily_df = pd.DataFrame(daily_records)
    insp_df = pd.DataFrame(inspection_events) if inspection_events else pd.DataFrame()
    fo_df = pd.DataFrame(forced_outage_events) if forced_outage_events else pd.DataFrame()

    return {
        "daily": daily_df,
        "inspections": insp_df,
        "forced_outages": fo_df,
        "final_state": state,
        "final_ltsa": ltsa_state,
        "schedule": schedule,
    }

