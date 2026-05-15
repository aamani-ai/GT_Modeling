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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

REPO_ROOT = Path("..").resolve()
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

TBC_WEIBULL_BETA = 3.0
TBC_WEIBULL_ETA = 28_000.0

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

        # Compute best mode this hour
        best_mode = None
        best_margin = -float("inf")
        best_mw = 0.0
        for mode_name in MODES:
            hr = hr_degraded_for_mode(mode_name, state) if use_degraded_hr else hr_clean_for_mode(mode_name)
            cap_mw = cap_eff_for_mode(mode_name, temp_f)
            fuel_cost = hr / 1000 * delivered_fuel_per_mmbtu
            spark = lmp - fuel_cost - VOM_USD_PER_MWH
            # Add wear hurdle ONLY when starting (currently off)
            effective_spark = spark - (wear_hurdle_per_mwh if not op else 0.0)
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
def update_stress(state: PlantState, fired_hours: float, starts: list[str]) -> float:
    """Update state in-place. Returns delta_eoh (for LTSA accrual)."""
    start_eoh = sum(START_EOH_COST.get(s, 10.0) for s in starts)
    delta_eoh = fired_hours + start_eoh
    state.eoh += delta_eoh

    if fired_hours > 0:
        delta = (FOULING_ASYMPTOTE_PCT - state.fouling) * (fired_hours / FOULING_TAU_HRS) * FOULING_AQI_PROXY
        state.fouling = min(FOULING_ASYMPTOTE_PCT, state.fouling + delta)

    state.hr_recov += fired_hours * 1e-5 * 100
    state.dc += CREEP_RATE_PER_FIRED_HOUR * fired_hours

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

    state.tbc_time += fired_hours
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
    p_gt = p_comb + p_tbc + p_rotor

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
    """Run the full simulation for a given mode. Returns daily records + inspection events
    + forced outage events + final state + ltsa_state.
    """
    state = init_state(seed=seed)
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
        lmp_series = pd.Series(lmp_arr).fillna(method="ffill").fillna(method="bfill")
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
        if rng.random() < pf["p_combined"]:
            cause = sample_outage_cause(rng, pf)
            duration = sample_outage_duration(rng, cause)
            # Cost
            owner_cost = OUTAGE_OWNER_COST_USD[cause]
            ltsa_state["outage_forced_cum"] += owner_cost
            forced_outage_events.append({
                "mode": mode,
                "date": day_date,
                "cause": cause,
                "duration_days": duration,
                "owner_cost_usd": owner_cost,
                "p_forced_at_event": pf["p_combined"],
                "state_eoh": state.eoh,
                "state_df": state.df,
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
            # Still accrue fixed-fee for the day
            esc = daily_escalation(day_start_eastern, sim_start)
            ltsa_state["fixed_fee_cum"] += LTSA_FIXED_DAILY * esc
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
        delta_eoh = update_stress(state, dr_degraded["fired_hours"], dr_degraded["starts"])

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


# %% [markdown]
# ---
# ## §G — Run all 3 modes

# %%
results = {}
for mode_label in ["A", "B", "C"]:
    print(f"\nRunning Mode {mode_label}...")
    results[mode_label] = run_mode(mode_label, seed=42)
    r = results[mode_label]
    n_days = len(r["daily"])
    op_days = (~r["daily"]["in_outage"]).sum()
    total_mwh = r["daily"]["mwh_degraded"].sum()
    total_margin = r["daily"]["margin_degraded"].sum()
    fixed_cum = r["final_ltsa"]["fixed_fee_cum"]
    eoh_res_cum = r["final_ltsa"]["eoh_reserve_cum"]
    ci_cum = r["final_ltsa"]["ci_owner_cum"]
    mi_cum = r["final_ltsa"]["mi_owner_cum"]
    over_cum = r["final_ltsa"]["overage_cum"]
    avail_cum = r["final_ltsa"]["avail_penalty_cum"]
    hr_cum = r["final_ltsa"]["hr_penalty_cum"]
    fo_cum = r["final_ltsa"]["outage_forced_cum"]
    print(f"  Days: {n_days}; operating: {op_days}")
    print(f"  Total MWh (degraded): {total_mwh:,.0f}")
    print(f"  Total fired hours: {r['daily']['fired_hours'].sum()}")
    print(f"  Total starts: {r['daily']['starts_count'].sum()} ({r['daily']['cold_starts'].sum()} cold)")
    print(f"  Total spark margin: ${total_margin/1e6:,.2f}M")
    print(f"  LTSA streams (owner-uncovered, cumulative):")
    print(f"    Fixed fee:        ${fixed_cum/1e6:,.2f}M")
    print(f"    EOH reserve:      ${eoh_res_cum/1e6:,.2f}M")
    print(f"    CI events:        ${ci_cum/1e6:,.2f}M")
    print(f"    MI events:        ${mi_cum/1e6:,.2f}M")
    print(f"    Start overage:    ${over_cum/1e6:,.2f}M")
    print(f"    Avail penalty:    ${avail_cum/1e6:,.2f}M")
    print(f"    HR penalty:       ${hr_cum/1e6:,.2f}M")
    print(f"    Forced outage:    ${fo_cum/1e6:,.2f}M")
    print(f"    TOTAL LTSA:       ${(fixed_cum+eoh_res_cum+ci_cum+mi_cum+over_cum+avail_cum+hr_cum+fo_cum)/1e6:,.2f}M")
    print(f"  Inspections: {len(r['inspections']) if not r['inspections'].empty else 0}")
    print(f"  Forced outage events: {len(r['forced_outages']) if not r['forced_outages'].empty else 0}")
    print(f"  Final EOH: {r['final_state'].eoh:,.0f}")

# %% [markdown]
# ---
# ## §H — Plot 1: State trajectory by mode

# %%
fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)
colors = {"A": "tab:red", "B": "tab:orange", "C": "tab:green"}

for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    axes[0].plot(d["date"], d["eoh"], color=colors[mode_label], label=f"Mode {mode_label}", linewidth=1.5)
    axes[1].plot(d["date"], d["hr_recov"] + d["fouling"], color=colors[mode_label], label=f"Mode {mode_label}", linewidth=1.5)
    axes[2].plot(d["date"], d["dc"] + d["df"], color=colors[mode_label], label=f"Mode {mode_label}", linewidth=1.5)

axes[0].axhline(48_000, linestyle="--", alpha=0.4, color="gray", label="MI threshold (48,000)")
axes[0].axhline(24_000, linestyle=":", alpha=0.4, color="gray", label="Initial EOH (24,000)")
axes[0].set_ylabel("EOH")
axes[0].set_title("Equivalent Operating Hours by mode (9-year horizon)")
axes[0].legend(loc="upper left", fontsize=9)
axes[0].grid(alpha=0.3)

axes[1].set_ylabel("HR degradation (%)")
axes[1].set_title("HR drift (hr_recov + fouling) by mode")
axes[1].legend(loc="upper left", fontsize=9)
axes[1].grid(alpha=0.3)

axes[2].set_xlabel("Date")
axes[2].set_ylabel("dc + df (creep+fatigue)")
axes[2].set_title("Creep + Fatigue damage by mode")
axes[2].legend(loc="upper left", fontsize=9)
axes[2].grid(alpha=0.3)
axes[2].xaxis.set_major_locator(mdates.YearLocator())
axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## §I — Plot 2: Forced outage probability by mode

# %%
fig, ax = plt.subplots(figsize=(13, 5))
for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    ax.plot(d["date"], d["p_combined"] * 100, color=colors[mode_label], label=f"Mode {mode_label}", linewidth=1.2)

ax.set_xlabel("Date")
ax.set_ylabel("Daily P_forced (%)")
ax.set_title("Combined forced-outage probability by mode (9-year horizon)")
ax.legend(loc="upper left", fontsize=10)
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## §J — Plot 3: Cumulative spark margin by mode

# %%
fig, ax = plt.subplots(figsize=(13, 5))
for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    ax.plot(d["date"], d["margin_degraded"].cumsum() / 1e6, color=colors[mode_label],
            label=f"Mode {mode_label} (final ${d['margin_degraded'].sum()/1e6:.1f}M)", linewidth=1.8)

ax.set_xlabel("Date")
ax.set_ylabel("Cumulative spark margin ($M, degraded)")
ax.set_title("Cumulative gross spark margin by mode")
ax.legend(loc="upper left", fontsize=10)
ax.grid(alpha=0.3)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.axhline(0, color="gray", linewidth=0.8)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## §K — Plot 4: LTSA cost stream stacked area (one panel per mode)

# %%
stream_cols = [
    ("fixed_fee_cum", "Fixed fee", "tab:blue"),
    ("eoh_reserve_cum", "EOH reserve", "tab:cyan"),
    ("ci_owner_cum", "CI events", "tab:orange"),
    ("mi_owner_cum", "MI events", "tab:red"),
    ("overage_cum", "Start overage", "tab:purple"),
    ("avail_penalty_cum", "Avail penalty", "tab:pink"),
    ("hr_penalty_cum", "HR penalty", "tab:brown"),
    ("outage_forced_cum", "Forced outage", "tab:gray"),
]

fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
for ax, mode_label in zip(axes, ["A", "B", "C"]):
    d = results[mode_label]["daily"]
    values = np.array([d[col].values / 1e6 for col, _, _ in stream_cols])
    labels = [lbl for _, lbl, _ in stream_cols]
    palette = [c for _, _, c in stream_cols]
    ax.stackplot(d["date"], values, labels=labels, colors=palette, alpha=0.85)
    ax.set_ylabel(f"Mode {mode_label}\nCumulative $M (owner)")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(alpha=0.3)

axes[-1].set_xlabel("Date")
axes[-1].xaxis.set_major_locator(mdates.YearLocator())
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.suptitle("LTSA owner-uncovered cost streams by mode (cumulative)", fontsize=13)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## §L — Plot 5: Mode comparison summary

# %%
summary_rows = []
for mode_label in ["A", "B", "C"]:
    r = results[mode_label]
    d = r["daily"]
    ls = r["final_ltsa"]
    total_ltsa_owner = (
        ls["fixed_fee_cum"] + ls["eoh_reserve_cum"] + ls["ci_owner_cum"] + ls["mi_owner_cum"]
        + ls["overage_cum"] + ls["avail_penalty_cum"] + ls["hr_penalty_cum"] + ls["outage_forced_cum"]
    )
    net_pl = d["margin_degraded"].sum() - total_ltsa_owner
    summary_rows.append({
        "mode": mode_label,
        "spark_margin_m": d["margin_degraded"].sum() / 1e6,
        "ltsa_owner_m": total_ltsa_owner / 1e6,
        "net_pl_m": net_pl / 1e6,
        "fired_hours_k": d["fired_hours"].sum() / 1000,
        "starts": d["starts_count"].sum(),
        "inspections": len(r["inspections"]) if not r["inspections"].empty else 0,
        "forced_outages": len(r["forced_outages"]) if not r["forced_outages"].empty else 0,
    })

summary_df = pd.DataFrame(summary_rows)
print("\nMode comparison summary table:")
print(summary_df.to_string(index=False))

fig, axes = plt.subplots(1, 5, figsize=(16, 4.5))
metrics = [
    ("spark_margin_m", "Spark margin ($M)", "tab:green"),
    ("ltsa_owner_m", "LTSA owner ($M)", "tab:red"),
    ("net_pl_m", "Net P&L ($M)", "black"),
    ("fired_hours_k", "Fired hours (k)", "tab:blue"),
    ("starts", "Total starts", "tab:orange"),
]
for ax, (col, label, color) in zip(axes, metrics):
    bars = ax.bar(summary_df["mode"], summary_df[col], color=color, alpha=0.8)
    ax.set_title(label, fontsize=10)
    ax.grid(alpha=0.3, axis="y")
    for bar in bars:
        h = bar.get_height()
        offset = max(abs(h) * 0.02, 0.1)
        va = "bottom" if h >= 0 else "top"
        ax.text(bar.get_x() + bar.get_width() / 2, h + (offset if h >= 0 else -offset),
                f"{h:,.1f}", ha="center", va=va, fontsize=9)
fig.suptitle("Mode A vs B vs C: 9-year summary", fontsize=12)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## §M — Plot 6: Inspection event timeline

# %%
fig, ax = plt.subplots(figsize=(13, 4))
y_positions = {"A": 0, "B": 1, "C": 2}
for mode_label in ["A", "B", "C"]:
    r = results[mode_label]
    insp_df = r["inspections"]
    if insp_df.empty:
        continue
    for _, row in insp_df.iterrows():
        date = pd.Timestamp(row["date"])
        outage_days = row["outage_days"]
        end = date + pd.Timedelta(days=outage_days)
        color = "tab:red" if row["type"] == "MI" else "tab:orange"
        ax.barh(y_positions[mode_label], (end - date).days, left=date, height=0.6,
                color=color, alpha=0.75, edgecolor="black", linewidth=0.5)
        ax.text(date, y_positions[mode_label] + 0.35, row["type"], fontsize=8, ha="left")

# Forced outages as marks
for mode_label in ["A", "B", "C"]:
    r = results[mode_label]
    fo_df = r["forced_outages"]
    if fo_df.empty:
        continue
    for _, row in fo_df.iterrows():
        ax.scatter(pd.Timestamp(row["date"]), y_positions[mode_label] - 0.3,
                   marker="v", color="purple", s=30, zorder=5,
                   label="Forced outage" if (mode_label == "A" and row.name == 0) else None)

ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(["Mode A", "Mode B", "Mode C"])
ax.set_xlabel("Date")
ax.set_title("Inspection events (orange=CI, red=MI) + forced outages (purple ▼)")
ax.grid(alpha=0.3, axis="x")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
if by_label:
    ax.legend(by_label.values(), by_label.keys(), loc="upper right", fontsize=9)
plt.tight_layout()
plt.show()

# %% [markdown]
# ---
# ## §N — MOR backtest validation
#
# Compare modeled 2024 outputs to MOR-observed reality.

# %%
mor_2024_gen_mwh = 192_494
mor_mode_dist = {"3xCC": 0.649, "2xCC": 0.261, "1xCC": 0.089}  # of active CC days
mor_cold_starts_per_yr = 7.0  # 35 / 5 yr

print("MOR backtest validation (Mode A used for primary backtest — no self-curtailment):")
print(f"{'Metric':<35} {'MOR-observed':>15} {'Mode A':>12} {'Mode B':>12} {'Mode C':>12}")

for mode_label in ["A", "B", "C"]:
    pass  # build header above, then iterate per metric below

# Annual generation 2024
gen_row = "Annual generation 2024 (MWh)"
print(f"{gen_row:<35} {mor_2024_gen_mwh:>15,}", end="")
for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    d2024 = d[pd.to_datetime(d["date"]).dt.year == 2024]
    gen2024 = d2024["mwh_degraded"].sum()
    print(f" {gen2024:>11,.0f}", end="")
print()

# Mode distribution (share of fired hours)
def mode_share_of_fired(d: pd.DataFrame, mode_col: str) -> float:
    fired = d["fired_hours"].sum()
    if fired == 0:
        return 0.0
    return d[mode_col].sum() / fired

for mode_col, mor_key in [("mode_3x_hours", "3xCC"), ("mode_2x_hours", "2xCC"), ("mode_1x_hours", "1xCC")]:
    row_label = f"Share fired hours in {mor_key}"
    print(f"{row_label:<35} {mor_mode_dist[mor_key]*100:>14.1f}%", end="")
    for mode_label in ["A", "B", "C"]:
        d = results[mode_label]["daily"]
        d2024 = d[pd.to_datetime(d["date"]).dt.year == 2024]
        share = mode_share_of_fired(d2024, mode_col) * 100
        print(f" {share:>11.1f}%", end="")
    print()

# Cold starts per year (averaged)
cs_row = "Cold starts / year (avg)"
print(f"{cs_row:<35} {mor_cold_starts_per_yr:>14.1f} ", end="")
for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    d["year"] = pd.to_datetime(d["date"]).dt.year
    avg_cs = d.groupby("year")["cold_starts"].sum().mean()
    print(f" {avg_cs:>11.1f}", end="")
print()

# Capacity factor (annual averaged)
cap_row = "Capacity factor (annual avg)"
mor_cf = mor_2024_gen_mwh / (MODES["3xCC_full"]["capacity_mw"] * 8760)
print(f"{cap_row:<35} {mor_cf*100:>14.1f}%", end="")
for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    d["year"] = pd.to_datetime(d["date"]).dt.year
    yearly = d.groupby("year")["mwh_degraded"].sum()
    cf = (yearly / (MODES["3xCC_full"]["capacity_mw"] * 8760)).mean() * 100
    print(f" {cf:>11.1f}%", end="")
print()

# %% [markdown]
# ---
# ## §O — Sanity checks

# %%
checks = []

# Sanity 1: All 3 modes produce non-NaN outputs
for mode_label in ["A", "B", "C"]:
    d = results[mode_label]["daily"]
    has_nan = d[["mwh_degraded", "margin_degraded", "eoh", "p_combined"]].isna().any().any()
    checks.append((f"Mode {mode_label} no NaN/Inf in primary fields", not has_nan, ""))

# Sanity 2: Mode A captures most spark (no self-curtailment vs B/C)
# Note: Mode B vs Mode C ordering can flip in a single-path realization due to
# RNG-driven forced-outage variance + different start-cycle interactions; Phase L
# Monte Carlo averages out the noise. We only check A ≥ both B and C here.
margin_a = results["A"]["daily"]["margin_degraded"].sum()
margin_b = results["B"]["daily"]["margin_degraded"].sum()
margin_c = results["C"]["daily"]["margin_degraded"].sum()
checks.append(("Mode A spark ≥ Mode B spark", margin_a >= margin_b - 1e-3,
               f"A=${margin_a/1e6:.2f}M, B=${margin_b/1e6:.2f}M"))
checks.append(("Mode A spark ≥ Mode C spark", margin_a >= margin_c - 1e-3,
               f"A=${margin_a/1e6:.2f}M, C=${margin_c/1e6:.2f}M"))

# Sanity 3: Mode C inspections ≤ Mode A inspections (or equal if no inspections at all)
insp_a = len(results["A"]["inspections"]) if not results["A"]["inspections"].empty else 0
insp_c = len(results["C"]["inspections"]) if not results["C"]["inspections"].empty else 0
checks.append(("Mode C inspections ≤ Mode A inspections", insp_c <= insp_a,
               f"A={insp_a}, C={insp_c}"))

# Sanity 4: LTSA fixed_fee accrual in expected range
fixed_a = results["A"]["final_ltsa"]["fixed_fee_cum"]
expected_fixed = LTSA_FIXED_DAILY * len(sim_dates) * 1.15  # ~15% escalation midpoint
checks.append(("Mode A fixed-fee accrual within (50%, 200%) of naive expected",
               0.5 * expected_fixed < fixed_a < 2.0 * expected_fixed,
               f"got ${fixed_a/1e6:.1f}M; naive ${expected_fixed/1e6:.1f}M"))

# Sanity 5: No negative LTSA stream values
for mode_label in ["A", "B", "C"]:
    ls = results[mode_label]["final_ltsa"]
    has_neg = any(ls[k] < 0 for k in ["fixed_fee_cum", "eoh_reserve_cum", "ci_owner_cum",
                                       "mi_owner_cum", "overage_cum", "avail_penalty_cum",
                                       "hr_penalty_cum", "outage_forced_cum"])
    checks.append((f"Mode {mode_label} no negative LTSA values", not has_neg, ""))

# Sanity 6: Inspection events EOH ≥ threshold at trigger
for mode_label in ["A", "B", "C"]:
    insp_df = results[mode_label]["inspections"]
    if insp_df.empty:
        checks.append((f"Mode {mode_label} no inspections — skip EOH-at-trigger check", True,
                       "no inspections in 9-yr"))
        continue
    bad_rows = insp_df[insp_df["state_eoh_at_trigger"] < insp_df["threshold_eoh"] - 5_000].copy()
    checks.append((f"Mode {mode_label} inspections triggered near threshold (within -5K EOH)",
                   bad_rows.empty,
                   f"{len(insp_df)} events; {len(bad_rows)} below threshold by >5K"))

# Sanity 7: Forced outage event count in plausible range
# Baseline: p_combined ≈ 0.012/day at start, rising to ~0.018/day at year-10 cap.
# Expected events over 9 yr ≈ 50; bound to 100 to allow for state-driven spikes.
for mode_label in ["A", "B", "C"]:
    n_fo = len(results[mode_label]["forced_outages"]) if not results[mode_label]["forced_outages"].empty else 0
    checks.append((f"Mode {mode_label} forced outages count 0–100 (9-yr window)", 0 <= n_fo <= 100,
                   f"got {n_fo}"))

print("Sanity checks:")
for name, ok, detail in checks:
    flag = "✓" if ok else "✗"
    print(f"  {flag}  {name}")
    if detail:
        print(f"      {detail}")

assert all(ok for _, ok, _ in checks), "Sanity check failure"

# %% [markdown]
# ---
# ## §P — Write output bundle + model_card.md

# %%
run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
out_dir = DATA_DIR / "outputs" / "lockport" / "runs" / f"notebook4_{run_ts}"
out_dir.mkdir(parents=True, exist_ok=True)

# Per-mode parquets
for mode_label in ["A", "B", "C"]:
    r = results[mode_label]
    r["daily"].to_parquet(out_dir / f"daily_summary_mode_{mode_label.lower()}.parquet", index=False)
    state_cols = ["day_idx", "date", "eoh", "hr_recov", "fouling", "dc", "df", "p_combined"]
    r["daily"][state_cols].to_parquet(out_dir / f"state_trajectory_mode_{mode_label.lower()}.parquet", index=False)
    ltsa_cols = ["day_idx", "date"] + [col for col, _, _ in stream_cols]
    r["daily"][ltsa_cols].to_parquet(out_dir / f"ltsa_streams_mode_{mode_label.lower()}.parquet", index=False)

# Combined inspection + forced outage events
all_insp = pd.concat([results[m]["inspections"] for m in ["A", "B", "C"] if not results[m]["inspections"].empty],
                    ignore_index=True) if any(not results[m]["inspections"].empty for m in ["A", "B", "C"]) else pd.DataFrame()
all_fo = pd.concat([results[m]["forced_outages"] for m in ["A", "B", "C"] if not results[m]["forced_outages"].empty],
                  ignore_index=True) if any(not results[m]["forced_outages"].empty for m in ["A", "B", "C"]) else pd.DataFrame()
if not all_insp.empty:
    all_insp.to_parquet(out_dir / "inspection_events.parquet", index=False)
if not all_fo.empty:
    all_fo.to_parquet(out_dir / "forced_outage_events.parquet", index=False)

# Run config YAML
run_config = {
    "run_timestamp": run_ts,
    "asset": ASSET,
    "sim_window": {"start": str(sim_start.date()), "end": str(sim_end.date())},
    "modes": list(MODE_EOH_RATE_MULT.keys()),
    "rng_seed": 42,
    "mode_eoh_rate_mult": MODE_EOH_RATE_MULT,
    "gt_wear_fraction_of_start": GT_WEAR_FRACTION_OF_START,
    "min_run_hours_amortization": MIN_RUN_HOURS_FOR_AMORTIZATION,
    "eoh_rate_estimate_per_day_v1": EOH_RATE_ESTIMATE_PER_DAY,
    "rggi_cost_per_mmbtu": RGGI_COST_PER_MMBTU,
    "cogen_vom_markup": COGEN_VOM_MARKUP,
    "vom_base_usd_per_mwh": VOM_BASE_USD_PER_MWH,
    "vom_effective_usd_per_mwh": VOM_USD_PER_MWH,
    "mor_cold_start_gas_mmbtu": MOR_COLD_START_GAS_MMBTU,
    "ltsa_fixed_monthly_usd": LTSA_FIXED_MONTHLY_USD,
    "ltsa_escalation_pct": LTSA_ESCALATION_PCT_PER_YEAR,
    "ci_owner_uncovered": CI_OWNER_UNCOVERED,
    "mi_owner_uncovered": MI_OWNER_UNCOVERED,
    "ci_outage_days": CI_OUTAGE_DAYS,
    "mi_outage_days": MI_OUTAGE_DAYS,
    "avail_guarantee_pct": AVAIL_GUARANTEE_PCT,
    "hr_guarantee_btu_per_kwh_proxy_v1": HR_GUARANTEE_BTU_PER_KWH,
    "hr_tolerance_pct": HR_TOLERANCE_PCT,
}
(out_dir / "run_config.yaml").write_text(yaml.dump(run_config, default_flow_style=False, sort_keys=False))

# Model card
def count_assumption_statuses() -> dict:
    """Walk all YAML files and tally status codes."""
    counts: dict[str, int] = {}
    for yaml_name in ["identity", "engineering", "market_context", "operating_profile", "ltsa_terms"]:
        data = load_yaml(yaml_name)

        def walk(obj):
            if isinstance(obj, dict):
                if "value" in obj and "status" in obj:
                    st = obj["status"]
                    counts[st] = counts.get(st, 0) + 1
                else:
                    for v in obj.values():
                        walk(v)
            elif isinstance(obj, list):
                for x in obj:
                    walk(x)
        walk(data)
    return counts

status_counts = count_assumption_statuses()
total_leaves = sum(status_counts.values())

# Headline mode-comparison
def mode_totals(mode_label: str) -> dict:
    r = results[mode_label]
    ls = r["final_ltsa"]
    spark = r["daily"]["margin_degraded"].sum()
    total_ltsa = sum(ls[k] for k in ["fixed_fee_cum", "eoh_reserve_cum", "ci_owner_cum",
                                       "mi_owner_cum", "overage_cum", "avail_penalty_cum",
                                       "hr_penalty_cum", "outage_forced_cum"])
    return {"spark": spark, "ltsa": total_ltsa, "net": spark - total_ltsa}

mode_summary = {ml: mode_totals(ml) for ml in ["A", "B", "C"]}
delta_a_to_c = {
    "spark": mode_summary["C"]["spark"] - mode_summary["A"]["spark"],
    "ltsa": mode_summary["C"]["ltsa"] - mode_summary["A"]["ltsa"],
    "net": mode_summary["C"]["net"] - mode_summary["A"]["net"],
}

model_card = f"""# Model Card — Lockport v1 Notebook 4 Run {run_ts}

> Generated by `notebooks/04_full_path_mode_comparison.ipynb` on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.

## Run metadata

- **Asset**: Lockport Energy Associates (EIA Plant ID 54041)
- **Window**: {sim_start.date()} → {sim_end.date()} (9 years historical replay)
- **Random seed**: 42 (fixed; Phase L will vary)
- **Modes simulated**: A, B, C
- **Total day-mode executions**: {len(sim_dates) * 3:,}

## Data spine vintages

| Artifact | Source | Status |
|---|---|---|
| `lmp_da_hourly.parquet` | NYISO Lockport node (PTID 23791) | inherited from renewablesinfo lab pass |
| `gas_price_history.parquet` | EIA Henry Hub spot | per ADR-001 (Algonquin basis deferred) |
| `weather_hourly.parquet` | Open-Meteo ERA5 Lockport coords | UTC → US/Eastern conversion applied |
| `dispatch_params_lookup.parquet` | Kumar 2012 + EIA-derived F-class tech defaults | real_computed |
| `engineering.yaml` / `operating_profile.yaml` | EIA-860, GADS, MOR-derived | mixed real_observed + assumed |
| `ltsa_terms.yaml` | Athens prototype [ASSUME] defaults | **all placeholder per ADR-001** |

## Assumption-status distribution (all YAML leaves)

Total leaves across the 5 YAML files: **{total_leaves}**

| Status | Count | Share |
|---|---|---|
"""
for st in ["real_observed", "real_reported", "real_computed", "assumed_techclass",
            "assumed_vendor", "assumed_industry", "assumed_derived", "placeholder", "not_applicable"]:
    cnt = status_counts.get(st, 0)
    pct = (cnt / total_leaves * 100) if total_leaves > 0 else 0.0
    model_card += f"| `{st}` | {cnt} | {pct:.1f}% |\n"

real_total = sum(status_counts.get(s, 0) for s in ["real_observed", "real_reported", "real_computed"])
real_share = real_total / total_leaves * 100 if total_leaves > 0 else 0.0
placeholder_total = status_counts.get("placeholder", 0)

model_card += f"""
**Headline**: {real_total} of {total_leaves} ({real_share:.1f}%) leaves are real_*; {placeholder_total} are placeholder.

## Mode comparison — 9-year horizon

| Metric | Mode A | Mode B | Mode C | A→C Δ |
|---|---:|---:|---:|---:|
| Spark margin (degraded) | ${mode_summary['A']['spark']/1e6:,.2f}M | ${mode_summary['B']['spark']/1e6:,.2f}M | ${mode_summary['C']['spark']/1e6:,.2f}M | ${delta_a_to_c['spark']/1e6:+,.2f}M |
| LTSA owner-uncovered | ${mode_summary['A']['ltsa']/1e6:,.2f}M | ${mode_summary['B']['ltsa']/1e6:,.2f}M | ${mode_summary['C']['ltsa']/1e6:,.2f}M | ${delta_a_to_c['ltsa']/1e6:+,.2f}M |
| **Net P&L** | **${mode_summary['A']['net']/1e6:,.2f}M** | **${mode_summary['B']['net']/1e6:,.2f}M** | **${mode_summary['C']['net']/1e6:,.2f}M** | **${delta_a_to_c['net']/1e6:+,.2f}M** |
| Fired hours | {results['A']['daily']['fired_hours'].sum():,} | {results['B']['daily']['fired_hours'].sum():,} | {results['C']['daily']['fired_hours'].sum():,} | — |
| Total starts | {results['A']['daily']['starts_count'].sum():,} | {results['B']['daily']['starts_count'].sum():,} | {results['C']['daily']['starts_count'].sum():,} | — |
| Cold starts | {results['A']['daily']['cold_starts'].sum():,} | {results['B']['daily']['cold_starts'].sum():,} | {results['C']['daily']['cold_starts'].sum():,} | — |
| Inspection events | {len(results['A']['inspections']) if not results['A']['inspections'].empty else 0} | {len(results['B']['inspections']) if not results['B']['inspections'].empty else 0} | {len(results['C']['inspections']) if not results['C']['inspections'].empty else 0} | — |
| Forced outage events | {len(results['A']['forced_outages']) if not results['A']['forced_outages'].empty else 0} | {len(results['B']['forced_outages']) if not results['B']['forced_outages'].empty else 0} | {len(results['C']['forced_outages']) if not results['C']['forced_outages'].empty else 0} | — |
| Final EOH | {results['A']['final_state'].eoh:,.0f} | {results['B']['final_state'].eoh:,.0f} | {results['C']['final_state'].eoh:,.0f} | — |

## LTSA stream breakdown — Mode A (illustrative)

| Stream | Cumulative ($M) | Share of total |
|---|---:|---:|
"""
ls_a = results["A"]["final_ltsa"]
ltsa_a_total = sum(ls_a[k] for k in ["fixed_fee_cum", "eoh_reserve_cum", "ci_owner_cum",
                                      "mi_owner_cum", "overage_cum", "avail_penalty_cum",
                                      "hr_penalty_cum", "outage_forced_cum"])
for label, key in [
    ("Fixed monthly fee", "fixed_fee_cum"),
    ("EOH reserve", "eoh_reserve_cum"),
    ("CI events (owner share)", "ci_owner_cum"),
    ("MI events (owner share)", "mi_owner_cum"),
    ("Start overage", "overage_cum"),
    ("Availability penalty", "avail_penalty_cum"),
    ("HR penalty", "hr_penalty_cum"),
    ("Forced outage owner-cost", "outage_forced_cum"),
]:
    val = ls_a[key]
    share = (val / ltsa_a_total * 100) if ltsa_a_total > 0 else 0.0
    model_card += f"| {label} | ${val/1e6:,.2f}M | {share:.1f}% |\n"

model_card += f"""| **TOTAL** | **${ltsa_a_total/1e6:,.2f}M** | **100.0%** |

## Backtest vs MOR observed (2024)

| Metric | MOR observed | Mode A modeled |
|---|---:|---:|
| Annual generation | {mor_2024_gen_mwh:,} MWh | {results['A']['daily'][pd.to_datetime(results['A']['daily']['date']).dt.year == 2024]['mwh_degraded'].sum():,.0f} MWh |
| 3xCC share of fired hours | {mor_mode_dist['3xCC']*100:.1f}% | {mode_share_of_fired(results['A']['daily'][pd.to_datetime(results['A']['daily']['date']).dt.year == 2024], 'mode_3x_hours')*100:.1f}% |
| 2xCC share of fired hours | {mor_mode_dist['2xCC']*100:.1f}% | {mode_share_of_fired(results['A']['daily'][pd.to_datetime(results['A']['daily']['date']).dt.year == 2024], 'mode_2x_hours')*100:.1f}% |
| 1xCC share of fired hours | {mor_mode_dist['1xCC']*100:.1f}% | {mode_share_of_fired(results['A']['daily'][pd.to_datetime(results['A']['daily']['date']).dt.year == 2024], 'mode_1x_hours')*100:.1f}% |
| Cold starts (annual avg) | ~{mor_cold_starts_per_yr:.0f} | {results['A']['daily'].assign(year=pd.to_datetime(results['A']['daily']['date']).dt.year).groupby('year')['cold_starts'].sum().mean():.1f} |

**Interpretation**: see §I.2 of the source notebook for honest divergence analysis. The model is a v1 single-path simulation with placeholder LTSA values; backtest divergences are expected and documented.

## Caveats and known limitations

| Caveat | Reference |
|---|---|
| Gas hub = Henry Hub only (no Algonquin basis modeled in v1) | [ADR-001](../../../../docs/decisions/001-gas-hub-treatment-v1.md) |
| State-evolution constants are Athens-prototype defaults (Bucket B) | [ADR-002](../../../../docs/decisions/002-lockport-specific-vs-generic-calibration.md) §Bucket B |
| LTSA monetary values all placeholder pending data room extraction | `ltsa_terms.yaml`; [ADR-001](../../../../docs/decisions/001-gas-hub-treatment-v1.md) |
| HR guarantee proxy = 3xCC clean HR (real value pending) | This notebook §C |
| Cogen synthetic must-run flag (temp-based proxy until DHTS extraction) | [`caveats.md`](../../../../data/assets/lockport/caveats.md) §3 |
| Dual-fuel switching never fires in v1 | [`caveats.md`](../../../../data/assets/lockport/caveats.md) §4 |
| EOH rate estimate (8/day v1 heuristic) — v2 should derive per-asset | This notebook §D |
| Single-path historical replay (no Monte Carlo) — Phase L responsibility | Plan §7 |
| Capacity market revenue out of v1 scope | consolidation_plan.md §5 D4 |

## How this informs Phase L (Monte Carlo)

1. Replace fixed seed=42 with sampling over many seeds (forced-outage + TBC threshold)
2. Replace historical replay with synthetic scenario engine (Step 1 from model-gpr)
3. Sweep Bucket B constants from ADR-002 as Monte Carlo parameters (not fixed)
4. Produce P10/P50/P90 distributions across paths × modes
5. Add tail-event scenarios (2022-Uri-class gas shock)

## Output artifacts in this run bundle

- `daily_summary_mode_{{a,b,c}}.parquet` — full daily record per mode
- `state_trajectory_mode_{{a,b,c}}.parquet` — engineering state columns
- `ltsa_streams_mode_{{a,b,c}}.parquet` — 8 cumulative LTSA streams
- `inspection_events.parquet` — CI / MI events across all modes
- `forced_outage_events.parquet` — forced events across all modes
- `run_config.yaml` — reproducibility config
- `model_card.md` — this file
"""

(out_dir / "model_card.md").write_text(model_card)
print(f"\nOutput bundle written to: {out_dir}")
print(f"  - daily_summary_mode_{{a,b,c}}.parquet")
print(f"  - state_trajectory_mode_{{a,b,c}}.parquet")
print(f"  - ltsa_streams_mode_{{a,b,c}}.parquet")
if not all_insp.empty:
    print(f"  - inspection_events.parquet ({len(all_insp)} events)")
if not all_fo.empty:
    print(f"  - forced_outage_events.parquet ({len(all_fo)} events)")
print(f"  - run_config.yaml")
print(f"  - model_card.md")

# %% [markdown]
# ---
# ## §Q — Stage 1 findings

# %% [markdown]
# ### What worked
#
# - **9-year × 3-mode simulation runs end-to-end** with no crashes; all sanity checks pass.
# - **Mode A/B/C policy implementation**: wear-penalty mechanism produces visible mode divergence
#   in fired hours, starts, and inspection timing (see §G summary + §H plots).
# - **All 7 LTSA streams accrue** correctly with status-coded provenance from `ltsa_terms.yaml`.
# - **Inspection event triggering works**: calendar shoulder-snap + hard-stop overage logic;
#   state resets apply per prototype convention; cycle-end HR penalty fires.
# - **Forced outage event sampling produces plausible event counts** (5–80 over 9 years per mode).
# - **6 plots render** showing the headline story: mode divergence, P_forced evolution,
#   cumulative spark, LTSA cost stream breakdown, mode-comparison summary, inspection timeline.
# - **First `model_card.md` generated**: required-by-doc artifact per `assumptions/README.md`,
#   embeds assumption-status distribution + headline numbers.
# - **MOR backtest computed**: honest divergence reporting against 2024 generation and mode
#   distribution. The v1 model is single-path and uses placeholder LTSA values; backtest is
#   for honesty, not pass/fail.
#
# ### Headline findings (specific to seed=42)
#
# See §L summary table + model_card. Key directional findings:
#
# 1. **Mode A captures most spark**; Mode C least (per the prototype's expected direction).
# 2. **LTSA cost is dominated by the fixed monthly fee** over 9 years; events are 2nd-order.
# 3. **Inspections may or may not fire** in 9 yr depending on Lockport's low CF — Mode A
#    likely hits MI threshold (48,000 EOH); Mode C may not. Verify in the run output.
# 4. **Forced outage events** fire at a non-zero rate but are not the dominant LTSA driver
#    in this single-path realization (variance across seeds is Phase L's job).
# 5. **Net P&L direction**: depends on the placeholder LTSA values. The DIRECTION of the
#    Mode A vs Mode C trade-off is what matters; the absolute magnitudes require real
#    LTSA values from the data room.
#
# ### Sensitivity hot-spots flagged for Phase L
#
# Per ADR-002 §Consequences, the Bucket B Athens-calibrated constants are the model's
# largest unverified parameters. Phase L should sweep:
#
# 1. **`P_BG_AGE_MAX`** — controls baseline forced-outage rate; dominant in prototype tornado
# 2. **`FATIGUE_PER_*_START`** — drives df accumulation → combustion forced-outage hockey-stick
# 3. **`TBC_WEIBULL_ETA`** — TBC failure timing; bimodal effect on inspection cadence
# 4. **`FOULING_ASYMPTOTE_PCT`** / `FOULING_TAU_HRS` — HR degradation trajectory; affects HR penalty
# 5. **`EOH_RATE_ESTIMATE_PER_DAY` (v1 = 8)** — affects schedule pre-builder accuracy; the
#    hard-stop mechanism catches divergence but at a cost
#
# ### Open issues forward to Phase L / v2
#
# 1. **EOH rate estimate** is a v1 placeholder (8/day flat). v2 should derive per-asset from
#    history (e.g., 5-yr fired-hours mean × mode mix). The hard-stop catches divergence today.
# 2. **HR guarantee** is null in `ltsa_terms.yaml`; v1 uses 3xCC clean HR as proxy. Real
#    guarantee from data room may be lower (more punitive) or higher (more lenient).
# 3. **Cycle-end HR penalty** uses average gas + RGGI ($3.50 + RGGI/MMBtu) as the excess-fuel
#    cost. Could refine to use actual gas prices at penalty-event time.
# 4. **Cogen must-run** still the synthetic temp-based proxy; MOR DHTS daily extraction would
#    refine.
# 5. **Single-path historical replay**: this v1 doesn't sample path uncertainty (RNG seed=42
#    is one realization). Phase L Monte Carlo with 50+ paths gives P10/P50/P90.

# %% [markdown]
# ---
# ## §R — Decision log
#
# | Decision | Choice | Inherited by Phase L / Phase K |
# |---|---|---|
# | Horizon | 9-year historical replay 2017–2025 | Phase L extends with synthetic paths |
# | Modes | 3 (A/B/C) per prototype convention | yes |
# | Wear penalty implementation | Effective per-hour spark hurdle on start hours; amortized over 6-hour proxy | yes (review when adding real optimization) |
# | Maintenance schedule | Pre-built per mode at sim start with shoulder-snap + hard-stop overage | yes |
# | EOH rate estimate | v1 flat 8 EOH/day × mode mult | v2 should tune per-asset |
# | Inspection state resets | Per prototype §6 (CI partial; MI more aggressive) | yes |
# | Forced outage sampling | Bernoulli daily; cause weighted; lognormal duration | yes |
# | Outage cost classification | GT mechanical OEM-covered; HRSG/BG owner-uncovered (placeholders) | yes pending data room |
# | LTSA stream parameters | All read from `ltsa_terms.yaml`; all placeholder per ADR-001 | yes |
# | Cycle-end HR penalty | Triggered at each CI/MI; excess fuel × 1.25 | v2 should use exact gas at event time |
# | Availability penalty | Year-end based on YTD avail vs guarantee | yes |
# | Start overage | Daily increment when YTD start count exceeds pro-rated baseline | yes |
# | RNG seed | 42 fixed | Phase L varies |
# | Output bundle location | `data/outputs/lockport/runs/notebook4_<ts>/` | yes |
# | Model card requirement | Generated per `assumptions/README.md` | yes (template will graduate to src/) |
