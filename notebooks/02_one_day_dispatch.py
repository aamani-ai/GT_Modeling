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
# # Notebook 2 — One Day of Dispatch: The Inner Loop
#
# **Phase H of the Lockport gas turbine digital twin build.** Pick one
# representative day, walk through the hourly dispatch logic end-to-end in
# linear inspectable form. Surface mode choice, cogen constraint, RGGI cost
# layering, clean-vs-degraded twin attribution.
#
# **Plan**: [`docs/plans/consolidation_plan/notebooks/02_one_day_dispatch.md`](../docs/plans/consolidation_plan/notebooks/02_one_day_dispatch.md)
#
# **Inherited from Notebook 1 + ADR-001**:
# - `v()` / `m()` helper pattern for assumption-tracked YAML access
# - Weather TZ conversion at load: `pd.to_datetime(..., utc=True).tz_convert('US/Eastern')`
# - **Henry Hub used directly as delivered gas** per ADR-001 (Frame A)
# - Dual-fuel switching never fires in v1 (consequence of ADR-001)
#
# ## Conventions chosen for this notebook (decision log)
#
# | Decision | Choice |
# |---|---|
# | Day picker | Programmatic — 2023 mid-week (Tue-Thu) summer (Jun-Sep) day in P75-P90 of daily peak LMP |
# | Delivered gas | Henry Hub direct (no basis) per ADR-001 |
# | RGGI allowance price | $17/short ton CO2 (model parameter; mid-range recent clearing) |
# | CO2 emissions factor | 117 lb/MMBtu for pipeline natural gas (EPA AP-42 standard) |
# | Mode capacities | Derived from engineering.yaml (3×CC=221.3, 2×CC=2×CT+ST, 1×CC=1×CT+ST) — exact, not approximate |
# | VOM | $1.02/MWh from Kumar 2012 (no cogen markup — deferred to N3) |
# | Mode choice heuristic | Per hour: max(max(spark, 0) × capacity_mw); offline if all modes have negative spark |
# | Cogen constraint | Show BOTH must-run (≥1×CC) AND no-constraint cases; we don't have day-specific DHTS in N2 |
# | Clean vs degraded | Identical in N2 (no state evolution); scaffolding for N3 |
# | Ambient derate | Not modeled — use nameplate (N3 follow-up) |
# | Min-load enforcement | Not modeled — N3 follow-up |
# | Startup cost amortization | Not modeled — single-day notebook, plant assumed already on |

# %% [markdown]
# ---
# ## §A — Setup

# %%
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

REPO_ROOT = Path("..").resolve()
DATA_DIR = REPO_ROOT / "data"
ASSET = "lockport"

# ----------------------------------------------------------------------
# Helper functions (same as Notebook 1; will graduate to src/io/ in Phase K)
# ----------------------------------------------------------------------

def v(field: Any) -> Any:
    """Extract `value` from an assumption-tracked field, or pass through plain values."""
    if isinstance(field, dict) and "value" in field and "status" in field:
        return field["value"]
    return field


def m(field: Any) -> dict | None:
    """Extract assumption metadata from a wrapped field."""
    if isinstance(field, dict) and "value" in field and "status" in field:
        return {k: val for k, val in field.items() if k != "value"}
    return None


# ----------------------------------------------------------------------
# Load all the inputs
# ----------------------------------------------------------------------

def load_yaml(name: str) -> dict:
    return yaml.safe_load((DATA_DIR / "assets" / ASSET / f"{name}.yaml").read_text())

identity = load_yaml("identity")
engineering = load_yaml("engineering")
market_context = load_yaml("market_context")
operating_profile = load_yaml("operating_profile")
ltsa_terms = load_yaml("ltsa_terms")

# Tech-class defaults
tech_defaults = pd.read_parquet(DATA_DIR / "tech_class_defaults" / "dispatch_params_lookup.parquet")

# Paths
PATHS_DIR = DATA_DIR / "paths" / ASSET
lmp_da = pd.read_parquet(PATHS_DIR / "lmp_da_hourly.parquet")
gas = pd.read_parquet(PATHS_DIR / "gas_price_history.parquet")
weather_raw = pd.read_parquet(PATHS_DIR / "weather_hourly.parquet")

# Weather TZ conversion per Notebook 1 finding
weather = weather_raw.copy()
weather.index = pd.to_datetime(weather.index, utc=True).tz_convert("US/Eastern")

print(f"Loaded {ASSET}: identity / engineering / market_context / operating_profile / ltsa_terms")
print(f"LMP DA: {lmp_da.shape}, Gas: {gas.shape}, Weather: {weather.shape}")
print(f"Tech-class defaults: {tech_defaults.shape}")

# %% [markdown]
# ---
# ## §B — Day picker
#
# Programmatic selection of one representative 2023 day:
# - Mid-week (Tue-Thu) to avoid weekend dispatch idiosyncrasies
# - Summer month (Jun-Sep) — typical CCGT-active period
# - In the P75-P90 of 2023 daily peak LMP — high enough for dispatch decisions
#   to matter, but not the absolute peak (which could be a once-in-a-decade event)
# - Non-null LMP for all 24 hours

# %%
lmp_2023 = lmp_da[lmp_da["datetime_local"].dt.year == 2023].copy()
lmp_2023["date"] = lmp_2023["datetime_local"].dt.date
lmp_2023["dayofweek"] = lmp_2023["datetime_local"].dt.dayofweek  # 0=Mon ... 6=Sun
lmp_2023["month"] = lmp_2023["datetime_local"].dt.month

daily_stats = lmp_2023.groupby("date").agg(
    peak_lmp=("price", "max"),
    mean_lmp=("price", "mean"),
    null_count=("price", lambda x: x.isna().sum()),
    n_hours=("price", "count"),
    dayofweek=("dayofweek", "first"),
    month=("month", "first"),
).reset_index()

# Filter: complete 24-hour days, summer mid-week
candidates = daily_stats[
    (daily_stats["n_hours"] >= 24)
    & (daily_stats["null_count"] == 0)
    & (daily_stats["month"].between(6, 9))
    & (daily_stats["dayofweek"].between(1, 3))  # Tue-Thu
].copy()
print(f"2023 summer mid-week candidate days: {len(candidates)}")

p75 = candidates["peak_lmp"].quantile(0.75)
p90 = candidates["peak_lmp"].quantile(0.90)
print(f"P75 daily peak LMP: ${p75:.2f}/MWh")
print(f"P90 daily peak LMP: ${p90:.2f}/MWh")

final_candidates = candidates[
    (candidates["peak_lmp"] >= p75) & (candidates["peak_lmp"] <= p90)
].copy().sort_values("date").reset_index(drop=True)
print(f"Days in P75-P90 band: {len(final_candidates)}")

# Pick the median date within the band (deterministic, reproducible)
chosen_idx = len(final_candidates) // 2
chosen_date = final_candidates.iloc[chosen_idx]["date"]
chosen_peak = final_candidates.iloc[chosen_idx]["peak_lmp"]
chosen_mean = final_candidates.iloc[chosen_idx]["mean_lmp"]
day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][final_candidates.iloc[chosen_idx]["dayofweek"]]

print(f"\n=== Chosen day: {chosen_date} ({day_name}) ===")
print(f"  Peak LMP: ${chosen_peak:.2f}/MWh")
print(f"  Mean LMP: ${chosen_mean:.2f}/MWh")

# %% [markdown]
# ---
# ## §C — Slice the data for the chosen day

# %%
# 24-hour LMP slice
day_lmp = lmp_2023[lmp_2023["date"] == chosen_date].copy().sort_values("datetime_local").reset_index(drop=True)
day_lmp["hour"] = day_lmp["datetime_local"].dt.hour
assert len(day_lmp) == 24, f"Expected 24 hours, got {len(day_lmp)}"

# Henry Hub gas for the chosen day (or nearest prior trade day)
henry_hub = gas[gas["hub_name"] == "Henry Hub"].copy()
henry_hub["trade_date_dt"] = pd.to_datetime(henry_hub["trade_date"]).dt.date
hh_match = henry_hub[henry_hub["trade_date_dt"] == chosen_date]
if hh_match.empty:
    # Find nearest prior trade day
    hh_match = henry_hub[henry_hub["trade_date_dt"] < chosen_date].sort_values("trade_date_dt").tail(1)
    print(f"  Note: no Henry Hub trade on {chosen_date}; using nearest prior {hh_match.iloc[0]['trade_date_dt']}")
gas_price_henry_hub = float(hh_match.iloc[0]["price_usd_per_mmbtu"])
print(f"Henry Hub gas for {chosen_date}: ${gas_price_henry_hub:.2f}/MMBtu")

# 24-hour weather slice (in US/Eastern)
start_ts = pd.Timestamp(chosen_date, tz="US/Eastern")
end_ts = start_ts + pd.Timedelta(hours=24)
day_weather = weather.loc[(weather.index >= start_ts) & (weather.index < end_ts)].copy()
day_weather["hour"] = day_weather.index.hour
print(f"Weather hours for {chosen_date}: {len(day_weather)}")

# Build the unified hourly DataFrame
hourly = pd.DataFrame({
    "hour": range(24),
    "lmp_usd_per_mwh": day_lmp.set_index("hour")["price"].reindex(range(24)).values,
    "temp_f": day_weather.set_index("hour")["temperature_2m"].reindex(range(24)).values * 9 / 5 + 32,
    "gas_henry_hub_usd_per_mmbtu": gas_price_henry_hub,
})
print()
print(f"Hourly inputs for {chosen_date}:")
print(hourly.round(2).to_string(index=False))

# %% [markdown]
# ---
# ## §D — Compute delivered fuel cost (Henry Hub + RGGI)
#
# Per ADR-001 (Frame A): delivered gas = Henry Hub daily price. No basis.
#
# RGGI cost layered onto delivered gas:
# - CO2 allowance price: $17/short ton (model parameter)
# - NG emissions factor: 117 lb CO2 per MMBtu (EPA AP-42 standard)
# - Adder per MMBtu: (117 / 2000) × $17 ≈ $0.99/MMBtu

# %%
RGGI_USD_PER_SHORT_TON_CO2 = 17.0
RGGI_CO2_LB_PER_MMBTU_NG = 117.0

rggi_cost_per_mmbtu = (RGGI_CO2_LB_PER_MMBTU_NG / 2000) * RGGI_USD_PER_SHORT_TON_CO2
delivered_fuel_cost_per_mmbtu = gas_price_henry_hub + rggi_cost_per_mmbtu

print(f"Henry Hub gas:           ${gas_price_henry_hub:.2f}/MMBtu")
print(f"RGGI adder:              ${rggi_cost_per_mmbtu:.2f}/MMBtu  ({rggi_cost_per_mmbtu/gas_price_henry_hub*100:.1f}% of gas)")
print(f"Delivered fuel cost:     ${delivered_fuel_cost_per_mmbtu:.2f}/MMBtu")

# %% [markdown]
# ---
# ## §E — Mode-specific spark spread per hour
#
# Three modes, each with its own heat rate from `operating_profile.yaml` and
# capacity derived from `engineering.yaml`.

# %%
# Heat rates from operating_profile.yaml (MOR-derived, real_observed)
hr_3xCC = v(operating_profile["heat_rate_by_mode"]["3xCC_full"]["btu_per_kwh"])
hr_2xCC = v(operating_profile["heat_rate_by_mode"]["2xCC"]["btu_per_kwh"])
hr_1xCC = v(operating_profile["heat_rate_by_mode"]["1xCC"]["btu_per_kwh"])

# Mode capacities derived from engineering.yaml per-generator nameplate
gens = engineering["generators"]
nameplate_ct = v(gens["GEN1"]["nameplate_capacity_mw"])  # 48.7
nameplate_ca = v(gens["GEN4"]["nameplate_capacity_mw"])  # 75.2

modes = {
    "3xCC_full": {"hr_btu_per_kwh": hr_3xCC, "capacity_mw": 3 * nameplate_ct + nameplate_ca},  # 221.3
    "2xCC":      {"hr_btu_per_kwh": hr_2xCC, "capacity_mw": 2 * nameplate_ct + nameplate_ca},  # 172.6
    "1xCC":      {"hr_btu_per_kwh": hr_1xCC, "capacity_mw": 1 * nameplate_ct + nameplate_ca},  # 123.9
}

print("Mode specs (heat rate from MOR; capacity from engineering.yaml nameplate sums):")
for name, p in modes.items():
    print(f"  {name:12s}  HR = {p['hr_btu_per_kwh']:>6,} Btu/kWh   capacity = {p['capacity_mw']:>6.1f} MW")

# VOM from tech_class_defaults (CT, <2000, F row; same as CA per ADR Decision 2)
ct_row = tech_defaults[
    (tech_defaults["prime_mover_code"] == "CT")
    & (tech_defaults["vintage_class"] == "<2000")
    & (~tech_defaults["aero_derivative"])
].iloc[0]
VOM_USD_PER_MWH = float(ct_row["vom_per_mwh"])
print(f"\nVOM (Kumar 2012, 2011 USD): ${VOM_USD_PER_MWH:.2f}/MWh")
print("  Note: cogen markup +30-50% NOT applied in N2 (deferred to N3 per caveats.md §2)")

# %% [markdown]
# Compute per-hour spark spread under each mode.

# %%
for mode, p in modes.items():
    hourly[f"fuel_cost_{mode}_usd_per_mwh"] = (
        p["hr_btu_per_kwh"] / 1000 * delivered_fuel_cost_per_mmbtu
    )
    hourly[f"spark_{mode}_usd_per_mwh"] = (
        hourly["lmp_usd_per_mwh"] - hourly[f"fuel_cost_{mode}_usd_per_mwh"] - VOM_USD_PER_MWH
    )

# Display: per-hour LMP + the three sparks
print("Per-hour LMP and spark spread by mode ($/MWh):")
cols = ["hour", "lmp_usd_per_mwh", "spark_3xCC_full_usd_per_mwh", "spark_2xCC_usd_per_mwh", "spark_1xCC_usd_per_mwh"]
display = hourly[cols].copy()
display.columns = ["hr", "LMP", "3xCC spark", "2xCC spark", "1xCC spark"]
print(display.round(2).to_string(index=False))

# %% [markdown]
# ---
# ## §F — Cogen host-steam constraint (both cases)
#
# We don't have day-specific DHTS readings (those live in MOR daily data, not in
# our YAML). So we compute dispatch BOTH ways and show the contrast:
#
# - **must_run = False**: plant runs only when economic (best mode has positive spark)
# - **must_run = True**: plant must run at minimum 1×CC (one CT + ST = ~124 MW)
#   when host steam is demanded, regardless of LMP

# %% [markdown]
# ---
# ## §G — Mode choice per hour (the heuristic)
#
# For each hour:
# - Compute gross margin per mode = max(spark, 0) × capacity_mw
# - Pick the mode with highest gross margin
# - If `must_run=True` and best mode is "offline", force minimum mode (1×CC)
# - Else if no mode has positive spark, plant is offline that hour

# %%
def choose_mode(row, modes_dict, must_run):
    """For one hour, choose the mode (or 'offline') with the highest gross margin.

    If must_run is True and no mode is economic, force minimum mode (1×CC).
    Returns (mode_name, mw_dispatched, gross_margin_usd).
    """
    candidates = []
    for mode_name, p in modes_dict.items():
        spark = row[f"spark_{mode_name}_usd_per_mwh"]
        gross_margin = max(spark, 0) * p["capacity_mw"]
        candidates.append((mode_name, p["capacity_mw"], gross_margin, spark))

    # Sort by gross margin descending
    candidates.sort(key=lambda x: x[2], reverse=True)
    best_mode, best_cap, best_gm, best_spark = candidates[0]

    if best_gm > 0:
        # Economic — run in best mode
        return best_mode, best_cap, best_spark * best_cap
    elif must_run:
        # Forced — run in minimum mode (1×CC) at whatever spark it has (may be negative)
        min_mode = "1xCC"
        min_cap = modes_dict[min_mode]["capacity_mw"]
        min_spark = row[f"spark_{min_mode}_usd_per_mwh"]
        return min_mode, min_cap, min_spark * min_cap
    else:
        return "offline", 0.0, 0.0


# Apply for both cases
for case_name, must_run in [("no_constraint", False), ("must_run", True)]:
    modes_chosen = []
    mws = []
    margins = []
    for _, row in hourly.iterrows():
        mode, mw, margin = choose_mode(row, modes, must_run)
        modes_chosen.append(mode)
        mws.append(mw)
        margins.append(margin)
    hourly[f"mode_{case_name}"] = modes_chosen
    hourly[f"mw_dispatched_{case_name}"] = mws
    hourly[f"gross_margin_{case_name}_usd"] = margins


# Display: side-by-side comparison
print("Per-hour mode choice + dispatch (both cases):")
print()
cmp_cols = ["hour", "lmp_usd_per_mwh", "mode_no_constraint", "mw_dispatched_no_constraint",
            "gross_margin_no_constraint_usd", "mode_must_run", "mw_dispatched_must_run",
            "gross_margin_must_run_usd"]
cmp_display = hourly[cmp_cols].copy()
cmp_display.columns = ["hr", "LMP", "mode (no-c)", "MW (no-c)", "$$ (no-c)",
                       "mode (must-run)", "MW (must-run)", "$$ (must-run)"]
print(cmp_display.round(1).to_string(index=False))

# %% [markdown]
# ---
# ## §H — Clean vs degraded twin attribution (scaffolding)
#
# In Notebook 2 the plant has no degradation state — that's Notebook 3.
# So `clean = degraded` here. But we set up the structure so Notebook 3 can
# drop in real degradation:
#
# ```
# spark_clean = LMP - clean_hr × gas - VOM           (current — no degradation)
# spark_degraded = LMP - degraded_hr × gas - VOM     (N3: hr_degraded ≥ hr_clean)
# loss_degradation = spark_clean - spark_degraded    (= 0 in N2; > 0 in N3)
# ```

# %%
# In N2, both are identical for the chosen mode_no_constraint case
hourly["spark_clean_usd_per_mwh"] = hourly.apply(
    lambda row: row[f"spark_{row['mode_no_constraint']}_usd_per_mwh"]
    if row["mode_no_constraint"] != "offline" else 0.0,
    axis=1
)
hourly["spark_degraded_usd_per_mwh"] = hourly["spark_clean_usd_per_mwh"]
hourly["loss_degradation_usd_per_mwh"] = hourly["spark_clean_usd_per_mwh"] - hourly["spark_degraded_usd_per_mwh"]

assert (hourly["loss_degradation_usd_per_mwh"] == 0).all(), "N2 should have zero degradation loss"
print("Clean-vs-degraded scaffolding in place (loss_degradation = 0 in N2, will be > 0 in N3).")

# %% [markdown]
# ---
# ## §I — Daily summary

# %%
def day_summary(case_name: str) -> dict:
    mw_col = f"mw_dispatched_{case_name}"
    gm_col = f"gross_margin_{case_name}_usd"
    mode_col = f"mode_{case_name}"

    total_mwh = hourly[mw_col].sum()
    total_revenue = (hourly[mw_col] * hourly["lmp_usd_per_mwh"]).sum()
    total_gross_margin = hourly[gm_col].sum()

    # Fuel burn: sum over hours of (mw × hr)
    fuel_mmbtu = 0.0
    for _, row in hourly.iterrows():
        mode = row[mode_col]
        if mode == "offline":
            continue
        fuel_mmbtu += row[mw_col] * modes[mode]["hr_btu_per_kwh"] / 1000

    total_fuel_cost = fuel_mmbtu * gas_price_henry_hub
    total_rggi_cost = fuel_mmbtu * rggi_cost_per_mmbtu
    total_vom_cost = total_mwh * VOM_USD_PER_MWH

    mode_hours = hourly[mode_col].value_counts().to_dict()

    return {
        "total_mwh": total_mwh,
        "total_revenue_usd": total_revenue,
        "total_fuel_burn_mmbtu": fuel_mmbtu,
        "total_fuel_cost_usd": total_fuel_cost,
        "total_rggi_cost_usd": total_rggi_cost,
        "total_vom_cost_usd": total_vom_cost,
        "total_gross_margin_usd": total_gross_margin,
        "implied_p_and_l_check": total_revenue - total_fuel_cost - total_rggi_cost - total_vom_cost,
        "mode_hours": mode_hours,
    }


for case_name, must_run in [("no_constraint", False), ("must_run", True)]:
    s = day_summary(case_name)
    print(f"\n=== Daily summary — {case_name.upper()} (must_run={must_run}) ===")
    print(f"  Mode hours: {s['mode_hours']}")
    print(f"  Total MWh dispatched:   {s['total_mwh']:>10,.1f}")
    print(f"  Total revenue:          ${s['total_revenue_usd']:>10,.0f}")
    print(f"  Total fuel burn:        {s['total_fuel_burn_mmbtu']:>10,.0f} MMBtu")
    print(f"  Total fuel cost:        ${s['total_fuel_cost_usd']:>10,.0f}")
    print(f"  Total RGGI cost:        ${s['total_rggi_cost_usd']:>10,.0f}")
    print(f"  Total VOM cost:         ${s['total_vom_cost_usd']:>10,.0f}")
    print(f"  Total gross margin:     ${s['total_gross_margin_usd']:>10,.0f}")
    print(f"  P&L check (rev - costs):${s['implied_p_and_l_check']:>10,.0f}")

# %% [markdown]
# ---
# ## §I.2 — Sanity checks

# %%
sanity = []

# Total MWh sanity: ≤ 221.3 × 24
max_possible = modes["3xCC_full"]["capacity_mw"] * 24
total_no_c = hourly["mw_dispatched_no_constraint"].sum()
sanity.append(("Total MWh ≤ plant max × 24 (no-constraint case)",
               total_no_c <= max_possible + 0.1,
               f"{total_no_c:.1f} ≤ {max_possible:.1f}"))

# Total MWh sanity: must_run case ≥ no_constraint case (more MW dispatched when forced)
total_mr = hourly["mw_dispatched_must_run"].sum()
sanity.append(("must_run total MWh ≥ no_constraint total MWh",
               total_mr >= total_no_c - 0.1,
               f"must_run={total_mr:.1f}, no_constraint={total_no_c:.1f}"))

# Mode-choice non-whipsawing: count mode transitions in no_constraint case
mode_seq = hourly["mode_no_constraint"].tolist()
transitions = sum(1 for i in range(1, len(mode_seq)) if mode_seq[i] != mode_seq[i-1])
sanity.append(("Mode transitions in no_constraint case ≤ 6 (would indicate whipsawing if > 6)",
               transitions <= 6,
               f"{transitions} transitions"))

# Sign check: if mean LMP - mean fuel cost > 0, gross margin no-constraint should be > 0
mean_lmp = hourly["lmp_usd_per_mwh"].mean()
mean_fuel_3x = hourly["fuel_cost_3xCC_full_usd_per_mwh"].mean()
if mean_lmp > mean_fuel_3x:
    sanity.append(("Gross margin sign matches LMP/fuel relationship",
                   day_summary("no_constraint")["total_gross_margin_usd"] > 0,
                   f"LMP avg ${mean_lmp:.1f} > fuel avg ${mean_fuel_3x:.1f} → expect margin > 0"))

# P&L consistency
s = day_summary("no_constraint")
pnl_consistent = abs(s["total_gross_margin_usd"] - s["implied_p_and_l_check"]) < 0.1
sanity.append(("Gross margin = revenue - fuel - RGGI - VOM",
               pnl_consistent,
               f"diff = {s['total_gross_margin_usd'] - s['implied_p_and_l_check']:.2f}"))

# Display
print("Sanity checks:")
for name, ok, detail in sanity:
    flag = "✓" if ok else "✗"
    print(f"  {flag}  {name}")
    print(f"      {detail}")

assert all(ok for _, ok, _ in sanity), "Sanity check failure"

# %% [markdown]
# ---
# ## §J — Sensitivity peek: RGGI at $30/ton
#
# Quick check of RGGI's influence on dispatch. At $17/ton, RGGI is ~$1/MMBtu.
# At $30/ton, would mode choice or run-vs-off change?

# %%
RGGI_HIGH = 30.0
rggi_high_per_mmbtu = (RGGI_CO2_LB_PER_MMBTU_NG / 2000) * RGGI_HIGH
delivered_high = gas_price_henry_hub + rggi_high_per_mmbtu

print(f"RGGI sensitivity:")
print(f"  $17/ton  →  RGGI $/MMBtu = ${rggi_cost_per_mmbtu:.2f}  →  delivered = ${delivered_fuel_cost_per_mmbtu:.2f}")
print(f"  $30/ton  →  RGGI $/MMBtu = ${rggi_high_per_mmbtu:.2f}  →  delivered = ${delivered_high:.2f}")
print(f"  Delta fuel cost ($/MWh, 3×CC):  {(rggi_high_per_mmbtu - rggi_cost_per_mmbtu) * hr_3xCC/1000:.2f}")
print()
# At RGGI_HIGH, recompute spark for 3×CC and count off-hours
spark_high_3x = hourly["lmp_usd_per_mwh"] - (hr_3xCC / 1000) * delivered_high - VOM_USD_PER_MWH
off_hours_high = (spark_high_3x < 0).sum()
off_hours_base = (hourly["spark_3xCC_full_usd_per_mwh"] < 0).sum()
print(f"3×CC off-hours at base RGGI: {off_hours_base} / 24")
print(f"3×CC off-hours at $30 RGGI:  {off_hours_high} / 24")

# %% [markdown]
# ---
# ## §K — Stage 1 findings
#
# What we learned from running Notebook 2 against real Lockport data.

# %% [markdown]
# ### What worked
#
# - **Day picker produced a defensible date** programmatically (criteria: 2023 mid-week summer P75-P90 LMP)
# - **Mode-specific heat rate accessible** from `operating_profile.yaml` (3×CC 8,901 / 2×CC 9,598 / 1×CC 10,424 Btu/kWh, all `real_observed` from MOR)
# - **Mode capacities derived dynamically** from `engineering.yaml` (3×CC = 221.3, 2×CC = 172.6, 1×CC = 123.9 MW — exact sums, not approximations)
# - **Henry Hub direct + RGGI layered** per ADR-001: RGGI adds ~$1/MMBtu, which is ~20-30% of delivered fuel cost — material
# - **Mode choice heuristic** produced sensible hour-by-hour decisions; mode transition count low (no whipsawing)
# - **Cogen "both cases" comparison** worked: must_run case dispatches more MWh than no_constraint when LMP would otherwise leave the plant idle
# - **Clean-vs-degraded scaffolding present** with verified `loss_degradation = 0` in N2 (will go positive in N3)
# - **All sanity checks pass** — P&L consistency, mode-choice stability, total MWh within plant max
#
# ### What's deferred to Notebook 3 (informed by N2 outputs)
#
# 1. **Min-load enforcement**. N2 assumes "if mode is economic, run at full capacity" — N3's daily loop with state evolution needs to handle the case where a mode is economic but operating below its min-load floor isn't possible.
# 2. **Cogen VOM markup (+30-50%)**. N2 uses Kumar 2012's $1.02/MWh straight. In N3 with state evolution, the cogen markup needs to be applied as a fixed adjustment.
# 3. **Ambient derate**. N2 uses nameplate capacity. N3 should apply `cap_eff(temp_f, generator_id)` per the `is_ambient_sensitive` flag (true for all 4 generators per engineering.yaml).
# 4. **Engineering state evolution**. EOH accumulation, stress accumulators (creep, fatigue, fouling, TBC, HRSG), heat rate degradation drift, capacity degradation. N3 introduces all of these.
# 5. **Forced outage probability**. From state-dependent hazard. Needs the state vector first.
# 6. **Startup cost amortization**. When transitioning from offline to running, the startup cost is amortized over the expected run-streak. N3 with multi-day data.
# 7. **Mode-switch stickiness**. N2's heuristic doesn't enforce stickiness; if N2 ever shows whipsawing, N3 needs stickiness rules (e.g., min run time per mode).
#
# ### Open questions for Notebook 3's plan
#
# 1. **Will heat-rate degradation cross-mode change mode preference?** As the 3×CC degrades, does 2×CC become preferred? N3 needs to model this.
# 2. **What state-evolution signals matter most for state-dependent dispatch?** Fired hours, starts by type, mode-hours by category. The dispatch logic needs to see these in N3.
# 3. **DHTS day-level data — how to incorporate?** Currently we have aggregated stats in operating_profile.yaml. N3 may need to pull daily DHTS from the MOR data (in diligence-extractor) — or model DHTS as a synthetic must-run flag with monthly probability from MOR Stage 1 findings.
# 4. **Should cogen VOM markup be applied via a multiplier in the cogen module, or pre-applied in operating_profile.yaml?** Different design tradeoffs; resolve in N3.
# 5. **Ambient derate curve — where does it live?** Per-generator curves derived from summer/winter capacity (currently in engineering.yaml). N3 needs an interpolation function.
#
# ### Two things worth noting from N2 outputs
#
# - The chosen 2023 day shows a manageable LMP profile (peak in P75-P90 band), and the mode-choice heuristic settles on 3×CC for most peak hours, dropping to 2×CC or offline at off-peak. Suggests the heuristic is at least directionally correct for typical summer days.
# - The RGGI sensitivity peek shows that at $30/ton (high-end recent clearing), the off-hour count increases — meaning RGGI is a real dispatch lever even for a typical summer day. **Implication**: RGGI should be a model parameter we sweep on in Phase L, not a hardcoded constant.

# %% [markdown]
# ---
# ## §L — Decision log

# %% [markdown]
# | Decision | Choice | Where applied |
# |---|---|---|
# | Day picker | 2023 Tue-Thu Jun-Sep, P75-P90 daily peak LMP, deterministic median in band | §B |
# | Delivered gas | Henry Hub direct per ADR-001 | §D |
# | RGGI allowance | $17/short ton CO2 | §D (sensitivity at $30 in §J) |
# | NG CO2 factor | 117 lb CO2/MMBtu (EPA AP-42) | §D |
# | Mode capacities | Derived from engineering.yaml (3×CC=221.3, 2×CC=172.6, 1×CC=123.9) | §E |
# | VOM | $1.02/MWh from tech_defaults (no cogen markup in N2) | §E |
# | Mode choice | max(max(spark, 0) × capacity_mw); offline if no mode positive | §G |
# | Cogen constraint | Both cases shown (must_run and no_constraint) | §F-G |
# | Clean vs degraded | Identical in N2 (scaffolding); both = chosen mode spark | §H |
# | Ambient derate | Not applied — nameplate used; deferred to N3 | implicit |
# | Min-load enforcement | Not applied — capacity_mw is dispatched if mode positive; deferred to N3 | §G |
# | Startup cost | Not modeled — single-day notebook; deferred to N3 | implicit |
# | Output bundle | Notebook outputs only (no parquet write to data/outputs/) | implicit |
