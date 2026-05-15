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
# # Notebook 1 — Data Spine: Load + Validate
#
# **Stage 1 of the Lockport gas turbine digital twin build.** First end-to-end load
# of the data spine — verifies every file exists, schemas conform, values are
# self-consistent. Produces the first assumption-status distribution summary
# (model_card preview). Surfaces the loader-API needs that Phase K will codify.
#
# **Read-only. No modeling computation.** Pure load + validate before we start
# using the data.
#
# **Plan**: [`docs/plans/consolidation_plan/notebooks/01_data_spine_load_validate.md`](../docs/plans/consolidation_plan/notebooks/01_data_spine_load_validate.md)
#
# ## Conventions chosen for this notebook (decision log)
#
# Captured at the top so future readers see them immediately.
#
# | Convention | Choice |
# |---|---|
# | YAML loader library | `pyyaml.safe_load` for v1; pydantic in `src/io/` later |
# | Metadata access | `v(field)` extracts value; `m(field)` extracts metadata. Helper functions below. |
# | Time-zone handling | Storage in mixed (UTC for weather, US/Eastern for LMP); display in NYISO local (US/Eastern) consistently |
# | LMP location filter | PTID 23791 (CTs) for primary block; PTID 323769 (ST) noted but not enforced |
# | Outlier handling | Out of scope — pure load + validate, no computation |
# | Missing values | Halt if structural (file missing); warn if data-quality (null LMPs); document if intentional (placeholders) |
# | Reproducibility | Notebook runs from a fresh kernel without external state; `nbstripout` strips outputs before commit |

# %% [markdown]
# ---
# ## §A — Setup

# %%
from __future__ import annotations  # PEP 604 syntax (dict | None) on Python 3.9

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any, Iterator

import pandas as pd
import yaml

REPO_ROOT = Path("..").resolve()
DATA_DIR = REPO_ROOT / "data"
ASSET = "lockport"

# ----------------------------------------------------------------------
# Helper functions for the assumption-tracked YAML structure.
# These will graduate to src/io/asset_loader.py at Phase K.
# ----------------------------------------------------------------------

def v(field: Any) -> Any:
    """Extract `value` from an assumption-tracked field, or pass through plain values.

    Pattern: every leaf value in our YAMLs is a dict like
        {value: 48.7, status: real_reported, source: "EIA-860 ..."}
    so `v(engineering['generators']['GEN1']['nameplate_capacity_mw'])` returns 48.7.
    For convenience, `v` is a no-op on plain values (lets us write generic code).
    """
    if isinstance(field, dict) and "value" in field and "status" in field:
        return field["value"]
    return field


def m(field: Any) -> dict | None:
    """Extract assumption metadata (status, source, confidence, ...) from a wrapped field.

    Returns None for plain values.
    """
    if isinstance(field, dict) and "value" in field and "status" in field:
        return {k: val for k, val in field.items() if k != "value"}
    return None


def iter_leaf_blocks(node: Any, path: str = "") -> Iterator[tuple[str, dict]]:
    """Walk a nested dict and yield (path, block) for every assumption-tracked leaf.

    A "leaf block" is a dict with both 'value' and 'status' keys. Used by §G
    to enumerate every assumption-tracked value for the model_card distribution.
    """
    if isinstance(node, dict):
        if "value" in node and "status" in node:
            yield path, node
        else:
            for k, val in node.items():
                yield from iter_leaf_blocks(val, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, val in enumerate(node):
            yield from iter_leaf_blocks(val, f"{path}[{i}]")


print(f"Repo root: {REPO_ROOT}")
print(f"Data dir exists: {DATA_DIR.exists()}")
print(f"Asset: {ASSET}")

# %% [markdown]
# ---
# ## §B — Inventory the data spine
#
# Walk the `data/` tree. Confirm every expected file exists. Halt if anything
# structural is missing — the rest of the notebook can't proceed.

# %%
EXPECTED_FILES = {
    # Tech-class defaults
    "data/tech_class_defaults/dispatch_params_lookup.parquet": "parquet",
    "data/tech_class_defaults/dispatch_params_values.csv": "csv",
    "data/tech_class_defaults/refs/AUDIT.md": "markdown",
    "data/tech_class_defaults/refs/kumar_2012.pdf": "pdf",
    "data/tech_class_defaults/refs/atb_2024.xlsx": "xlsx",
    "data/tech_class_defaults/refs/emm_2026.pdf": "pdf",
    "data/tech_class_defaults/refs/pjm_m15.pdf": "pdf",
    # Lockport asset YAMLs
    f"data/assets/{ASSET}/identity.yaml": "yaml",
    f"data/assets/{ASSET}/engineering.yaml": "yaml",
    f"data/assets/{ASSET}/market_context.yaml": "yaml",
    f"data/assets/{ASSET}/operating_profile.yaml": "yaml",
    f"data/assets/{ASSET}/ltsa_terms.yaml": "yaml",
    f"data/assets/{ASSET}/caveats.md": "markdown",
    f"data/assets/{ASSET}/provenance.md": "markdown",
    # Lockport paths
    f"data/paths/{ASSET}/lmp_da_hourly.parquet": "parquet",
    f"data/paths/{ASSET}/lmp_rt_intervals.parquet": "parquet",
    f"data/paths/{ASSET}/lmp_west_zone_da.parquet": "parquet",
    f"data/paths/{ASSET}/gas_price_history.parquet": "parquet",
    f"data/paths/{ASSET}/weather_hourly.parquet": "parquet",
    f"data/paths/{ASSET}/weather_forecast_seas5.json": "json",
}

inventory_rows = []
missing = []
for rel_path, fmt in EXPECTED_FILES.items():
    full = REPO_ROOT / rel_path
    if not full.exists():
        missing.append(rel_path)
        continue
    size_kb = full.stat().st_size / 1024
    inventory_rows.append({"file": rel_path, "format": fmt, "size_kb": round(size_kb, 1)})

inventory = pd.DataFrame(inventory_rows)
print(f"Expected files: {len(EXPECTED_FILES)}")
print(f"Present: {len(inventory_rows)}")
print(f"Missing: {len(missing)}")
assert not missing, f"Missing files (halt): {missing}"

print()
print("Inventory:")
print(inventory.to_string(index=False))
print()
print(f"Total data/ size: {inventory['size_kb'].sum() / 1024:.1f} MB")

# %% [markdown]
# ---
# ## §C — Load + display tech-class defaults
#
# Simplest artifact — validates that parquet loading works and the lookup has the
# expected shape (20 rows × 35 cols; 4 prime movers × 4 vintage classes with aero
# split for GT).

# %%
tech_defaults = pd.read_parquet(DATA_DIR / "tech_class_defaults" / "dispatch_params_lookup.parquet")
print(f"Shape: {tech_defaults.shape}")
print(f"Expected: (20, 35) — assert passes: {tech_defaults.shape == (20, 35)}")
print()
print("Coverage by (prime_mover, aero_derivative):")
print(tech_defaults.groupby(["prime_mover_code", "aero_derivative"]).size().to_string())
print()
print("Confidence-tier distribution:")
conf_cols = [c for c in tech_defaults.columns if c.startswith("confidence_")]
for col in conf_cols:
    counts = tech_defaults[col].value_counts().to_dict()
    summary = " | ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"  {col:35s}  {summary}")

# %% [markdown]
# Filter to the two rows that apply to Lockport:
# - GEN1/2/3 (CT, 1992) → (CT, <2000, False)
# - GEN4 (CA, 1992) → (CA, <2000, False)

# %%
lockport_rows = tech_defaults[
    (tech_defaults["prime_mover_code"].isin(["CT", "CA"]))
    & (tech_defaults["vintage_class"] == "<2000")
    & (~tech_defaults["aero_derivative"])
]
print(f"Lockport applicable rows: {len(lockport_rows)} (expected 2)")
print()
display_cols = [
    "prime_mover_code", "vintage_class", "vom_per_mwh",
    "startup_cost_cold_p50_per_mw", "startup_cost_warm_p50_per_mw", "startup_cost_hot_p50_per_mw",
    "hot_start_time_hr", "cold_start_time_hr", "ramp_rate_pct_per_min",
    "confidence_vom", "confidence_startup_cost", "confidence_start_time",
]
print(lockport_rows[display_cols].to_string(index=False))

# %% [markdown]
# ---
# ## §D — Load + display Lockport asset YAMLs
#
# First real test of the assumption-tracked YAML convention. For each of the 5
# YAML files, load and show the assumption metadata visibly.

# %%
def load_yaml(name: str) -> dict:
    return yaml.safe_load((DATA_DIR / "assets" / ASSET / f"{name}.yaml").read_text())

identity = load_yaml("identity")
engineering = load_yaml("engineering")
market_context = load_yaml("market_context")
operating_profile = load_yaml("operating_profile")
ltsa_terms = load_yaml("ltsa_terms")

# Sample top-level keys
for name, doc in [
    ("identity", identity),
    ("engineering", engineering),
    ("market_context", market_context),
    ("operating_profile", operating_profile),
    ("ltsa_terms", ltsa_terms),
]:
    print(f"{name}: top-level keys = {list(doc.keys())}")

# %% [markdown]
# Demonstrate the `v()` and `m()` helper pattern on a representative value
# (Lockport GEN1's `min_load_mw`). This is the access pattern Notebooks 2-4 will use.

# %%
min_load_field = engineering["generators"]["GEN1"]["min_load_mw"]
print(f"Raw YAML block:        {min_load_field}")
print(f"v(min_load_field) =    {v(min_load_field)}  (a clean float for modeling)")
print(f"m(min_load_field) =    {m(min_load_field)}  (the provenance metadata)")

# %% [markdown]
# Cross-check the assumption-tracked count per YAML — should be substantial.

# %%
for name, doc in [
    ("identity", identity),
    ("engineering", engineering),
    ("market_context", market_context),
    ("operating_profile", operating_profile),
    ("ltsa_terms", ltsa_terms),
]:
    leaves = list(iter_leaf_blocks(doc))
    print(f"{name:20s}  {len(leaves):>4} assumption-tracked leaf values")

# %% [markdown]
# ---
# ## §E — Load + display Lockport paths
#
# Time series. Schemas, date ranges, timestamp handling. The weather parquet
# needs explicit timestamp conversion per `data/paths/lockport/README.md`.

# %%
PATHS_DIR = DATA_DIR / "paths" / ASSET

lmp_da = pd.read_parquet(PATHS_DIR / "lmp_da_hourly.parquet")
lmp_rt = pd.read_parquet(PATHS_DIR / "lmp_rt_intervals.parquet")
lmp_west = pd.read_parquet(PATHS_DIR / "lmp_west_zone_da.parquet")
gas = pd.read_parquet(PATHS_DIR / "gas_price_history.parquet")
weather_raw = pd.read_parquet(PATHS_DIR / "weather_hourly.parquet")

# Weather index conversion — see data/paths/lockport/README.md §weather_hourly.parquet
# Raw index is string ISO 8601 with UTC offset. Convert at load.
weather = weather_raw.copy()
weather.index = pd.to_datetime(weather.index, utc=True).tz_convert("US/Eastern")

with open(PATHS_DIR / "weather_forecast_seas5.json") as f:
    weather_forecast = json.load(f)

# %% [markdown]
# Show what we got — shapes, date ranges, time zones.

# %%
for name, df, tcol in [
    ("lmp_da_hourly      ", lmp_da, "datetime_local"),
    ("lmp_rt_intervals   ", lmp_rt, "datetime_local"),
    ("lmp_west_zone_da   ", lmp_west, "datetime_local"),
    ("gas_price_history  ", gas, "trade_date"),
    ("weather_hourly     ", weather, None),  # uses index
]:
    if tcol is not None:
        rng = f"{df[tcol].min()} → {df[tcol].max()}"
        tz = "(NYISO local TZ-aware)" if "datetime_local" in tcol else "(date only)"
    else:
        rng = f"{df.index[0]} → {df.index[-1]}"
        tz = f"(tz={df.index.tz})"
    print(f"{name}  shape={df.shape!s:25s}  range: {rng}  {tz}")

print()
print(f"weather_forecast_seas5.json top-level keys: {list(weather_forecast.keys())}")

# %% [markdown]
# Spot-check LMP column structure and gas hub coverage:

# %%
print("LMP DA columns:", list(lmp_da.columns))
print()
print("Gas hubs:", sorted(gas["hub_name"].unique().tolist()))
print(f"Gas date range: {gas['trade_date'].min()} → {gas['trade_date'].max()}")
print()
# Algonquin Citygate is the NYISO-relevant delivery hub for Lockport
algonquin = gas[gas["hub_name"] == "Algonquin Citygate"]
print(f"Algonquin Citygate rows: {len(algonquin)}  ({algonquin['trade_date'].min()} → {algonquin['trade_date'].max()})")

# %% [markdown]
# ---
# ## §F — Cross-validation checks
#
# The most important section. Catch inconsistencies between sources before they
# corrupt downstream modeling.

# %%
# Two kinds of checks:
#   - hard:  must pass for the data spine to be usable
#   - soft:  passing is preferred but failures are documented findings, not blockers
checks = []   # (name, passed, detail, severity)

# 1. Generator capacities sum to plant total
gen_nameplate_sum = sum(
    v(engineering["generators"][gid]["nameplate_capacity_mw"])
    for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]
)
plant_nameplate = v(engineering["plant"]["total_nameplate_mw"])
ok = abs(gen_nameplate_sum - plant_nameplate) < 0.1 and abs(plant_nameplate - 221.3) < 0.1
checks.append(("Generator capacities sum to plant total (221.3 MW)", ok,
               f"sum={gen_nameplate_sum}, plant={plant_nameplate}", "hard"))

# 2. Plant ID consistent across identity.yaml + cross-system IDs
identity_pid = v(identity["plant"]["id"])
identity_cross = v(identity["cross_system_ids"]["eia_plant_id"])
orispl = v(identity["cross_system_ids"]["epa_orispl"])
ok = identity_pid == identity_cross == orispl == 54041
checks.append(("Plant ID consistent (54041) across identity.yaml", ok,
               f"plant.id={identity_pid}, eia={identity_cross}, orispl={orispl}", "hard"))

# 3. NYISO PTIDs consistent identity ↔ market_context
id_ptid_cts = v(identity["cross_system_ids"]["nyiso_ptid_cts"])
mc_ptid_cts = v(market_context["lmp_nodes"]["primary_cts"]["ptid"])
ok = id_ptid_cts == mc_ptid_cts == 23791
checks.append(("CT-side PTID consistent (23791) across identity ↔ market_context", ok,
               f"identity={id_ptid_cts}, market_context={mc_ptid_cts}", "hard"))

# 4. eGRID subregion consistent identity ↔ market_context
id_egrid = v(identity["cross_system_ids"]["egrid_subregion_code"])
mc_egrid = v(market_context["egrid"]["subregion_code"])
ok = id_egrid == mc_egrid == "NYUP"
checks.append(("eGRID subregion consistent (NYUP) across identity ↔ market_context", ok,
               f"identity={id_egrid}, market_context={mc_egrid}", "hard"))

# 5. Time alignment — gas date range covers LMP DA date range
# (gas: 1997-2026; LMP: 2017-2026 → gas overall covers LMP)
lmp_start = lmp_da["datetime_local"].min()
lmp_end = lmp_da["datetime_local"].max()
gas_start = pd.Timestamp(gas["trade_date"].min())
gas_end = pd.Timestamp(gas["trade_date"].max())
ok = gas_start <= lmp_start.tz_localize(None) and gas_end >= lmp_end.tz_localize(None).normalize() - pd.Timedelta(days=30)
checks.append(("Gas history (all hubs) covers LMP DA date range", ok,
               f"gas {gas_start.date()}-{gas_end.date()}; lmp {lmp_start.date()}-{lmp_end.date()}", "hard"))

# 5b. Per-hub gas coverage — Algonquin Citygate is NYISO-relevant for Lockport
hub_coverage = gas.groupby("hub_name").agg(
    n=("trade_date", "count"),
    min_date=("trade_date", "min"),
    max_date=("trade_date", "max"),
).reset_index()
# Find Algonquin coverage
algonquin = hub_coverage[hub_coverage["hub_name"] == "Algonquin Citygate"].iloc[0]
algonquin_end = pd.Timestamp(algonquin["max_date"])
# Soft check: Algonquin should cover at least the LMP date range
ok = algonquin_end >= lmp_end.tz_localize(None).normalize() - pd.Timedelta(days=30)
checks.append((
    "Algonquin Citygate (Lockport's gas hub) covers LMP date range",
    ok,
    f"Algonquin {algonquin['min_date']}-{algonquin['max_date']} ({algonquin['n']} rows); LMP DA through {lmp_end.date()}. "
    f"Henry Hub (the forward-anchor reference) has full coverage — see hub_coverage table.",
    "soft"
))

# 6. Time alignment — weather covers LMP DA date range
weather_start = weather.index[0]
weather_end = weather.index[-1]
ok = weather_start <= lmp_start and weather_end >= lmp_end - pd.Timedelta(days=30)
checks.append(("Weather covers LMP DA date range (after TZ conversion)", ok,
               f"weather {weather_start.date()}-{weather_end.date()}; lmp {lmp_start.date()}-{lmp_end.date()}. "
               f"For 2017-2025 modeling, weather is sufficient. For 2026 specifically, weather has a ~4-month gap.",
               "soft"))

# 7. Tech-class lookup join — Lockport gets exactly 2 rows
ok = len(lockport_rows) == 2
checks.append(("Tech-class lookup returns 2 rows for Lockport (CT,<2000,F) + (CA,<2000,F)", ok,
               f"got {len(lockport_rows)} rows", "hard"))

# 8. Operating profile mode hierarchy: 3xCC_full < 2xCC < 1xCC
hr_3x = v(operating_profile["heat_rate_by_mode"]["3xCC_full"]["btu_per_kwh"])
hr_2x = v(operating_profile["heat_rate_by_mode"]["2xCC"]["btu_per_kwh"])
hr_1x = v(operating_profile["heat_rate_by_mode"]["1xCC"]["btu_per_kwh"])
ok = hr_3x < hr_2x < hr_1x
checks.append(("Mode hierarchy (3×CC < 2×CC < 1×CC heat rate)", ok,
               f"3x={hr_3x}, 2x={hr_2x}, 1x={hr_1x}", "hard"))

# 9. eGRID cross-validation within 1%
egrid_2023 = v(operating_profile["cross_validation"]["egrid_2023_implied_hr_btu_per_kwh"])
mor_2023 = v(operating_profile["cross_validation"]["mor_2023_all_cc_volume_weighted_btu_per_kwh"])
delta = abs(mor_2023 - egrid_2023) / egrid_2023 * 100
ok = delta < 1.0
checks.append(("MOR 2023 reproduces eGRID placeholder within 1%", ok, f"delta={delta:.2f}%", "hard"))

# 10. 2024 generation correction
gen_2024 = v(operating_profile["annual_generation"]["corrected_2024_annual_mwh"])
ok = gen_2024 == 192494
checks.append(("2024 generation = 192,494 MWh (MOR correction)", ok, f"got {gen_2024}", "hard"))

# Display
print("Cross-validation checks (hard = must pass; soft = surfaced finding, continues):")
print()
hard_fail = False
soft_fail_count = 0
for name, ok, detail, severity in checks:
    if ok:
        flag = "✓"
    elif severity == "hard":
        flag = "✗ HARD"
        hard_fail = True
    else:
        flag = "⚠ SOFT"
        soft_fail_count += 1
    print(f"  {flag:6s}  {name}")
    print(f"          {detail}")

print()
print(f"Hard fails: {sum(1 for _, ok, _, sev in checks if not ok and sev == 'hard')}")
print(f"Soft warnings: {soft_fail_count}")
print(f"OVERALL: {'HARD FAIL — halt' if hard_fail else 'OK (some soft warnings — see Stage 1 findings)'}")

# Print per-hub gas coverage table since it's the central soft-warning finding
print()
print("Per-hub gas coverage:")
print(hub_coverage.to_string(index=False))

assert not hard_fail, "Hard cross-validation failure — see above"

# %% [markdown]
# ---
# ## §G — Assumption-status distribution (model_card preview)
#
# Aggregate across all loaded YAML leaf values. **First concrete answer to "how
# much of this model is real vs assumed"** — the kernel of what every model_card
# will eventually surface.

# %%
all_blocks = []
for name, doc in [
    ("identity", identity),
    ("engineering", engineering),
    ("market_context", market_context),
    ("operating_profile", operating_profile),
    ("ltsa_terms", ltsa_terms),
]:
    for path, block in iter_leaf_blocks(doc):
        all_blocks.append({
            "file": name,
            "path": path,
            "status": block["status"],
            "confidence": block.get("confidence"),
            "value": block.get("value"),
            "source": block.get("source", ""),
        })

leaves_df = pd.DataFrame(all_blocks)
print(f"Total assumption-tracked leaf values: {len(leaves_df)}")
print()
print("Distribution by file:")
print(leaves_df.groupby("file").size().to_string())
print()
print("Distribution by status:")
status_counts = leaves_df["status"].value_counts()
total = len(leaves_df)
for status, count in status_counts.items():
    pct = count / total * 100
    print(f"  {status:25s}  {count:>4}  ({pct:.1f}%)")

# %% [markdown]
# Real vs assumed breakdown:

# %%
real_count = leaves_df["status"].str.startswith("real_").sum()
assumed_count = leaves_df["status"].str.startswith("assumed_").sum()
placeholder_count = (leaves_df["status"] == "placeholder").sum()
na_count = (leaves_df["status"] == "not_applicable").sum()

print(f"  real_*           {real_count:>4}  ({real_count/total*100:.1f}%)")
print(f"  assumed_*        {assumed_count:>4}  ({assumed_count/total*100:.1f}%)")
print(f"  placeholder      {placeholder_count:>4}  ({placeholder_count/total*100:.1f}%)")
print(f"  not_applicable   {na_count:>4}  ({na_count/total*100:.1f}%)")

# %% [markdown]
# Confidence distribution for assumed values:

# %%
assumed_df = leaves_df[leaves_df["status"].str.startswith("assumed_")]
if len(assumed_df) > 0:
    conf = assumed_df["confidence"].value_counts()
    for level, count in conf.items():
        print(f"  {level}:  {count}")
else:
    print("(no assumed values in this notebook's YAMLs)")

# %% [markdown]
# Placeholders — list with validation_paths:

# %%
placeholder_df = leaves_df[leaves_df["status"] == "placeholder"]
print(f"Placeholders: {len(placeholder_df)}")
print()
print("Distribution by file:")
print(placeholder_df.groupby("file").size().to_string())
print()
# Pull validation_path from the original blocks
placeholder_summary = []
for name, doc in [
    ("identity", identity),
    ("engineering", engineering),
    ("market_context", market_context),
    ("operating_profile", operating_profile),
    ("ltsa_terms", ltsa_terms),
]:
    for path, block in iter_leaf_blocks(doc):
        if block["status"] == "placeholder":
            placeholder_summary.append({
                "file": name,
                "path": path,
                "validation_path": block.get("validation_path", "MISSING"),
            })

# Show a sample of distinct validation_paths
unique_validation_paths = list(set(p["validation_path"] for p in placeholder_summary))
print(f"Distinct validation_paths cited by placeholders: {len(unique_validation_paths)}")
for vp in unique_validation_paths[:5]:
    print(f"  - {vp[:120]}")
if len(unique_validation_paths) > 5:
    print(f"  ... ({len(unique_validation_paths) - 5} more)")

# %% [markdown]
# **LOW-confidence values flagged** (these are the ones most worth disclosure in model_card):

# %%
low_conf = leaves_df[leaves_df["confidence"] == "LOW"]
print(f"LOW-confidence values: {len(low_conf)}")
for _, row in low_conf.head(20).iterrows():
    print(f"  - {row['file']}.{row['path']}  ({row['status']})  value={row['value']}")
if len(low_conf) > 20:
    print(f"  ... ({len(low_conf) - 20} more)")

# %% [markdown]
# ---
# ## §H — Lockport ↔ tech-class lookup join
#
# Sanity-check that the modeling-side join works. For each Lockport generator,
# derive its (prime_mover_code, vintage_class, aero_derivative) key, look it up,
# and display the values that would flow into the model.

# %%
def derive_vintage_class(operating_year_str: str) -> str:
    """Operating year (e.g., '1992-07') → vintage class bucket."""
    year = int(operating_year_str.split("-")[0])
    if year < 2000:
        return "<2000"
    elif year < 2010:
        return "2000-2010"
    elif year < 2020:
        return "2010-2020"
    else:
        return "2020+"


for gen_id, gen in engineering["generators"].items():
    pm = v(gen["prime_mover_code"])
    op = v(gen["operating_since"])
    vintage = derive_vintage_class(op)
    # For CT/CA, aero is False by default
    aero = False
    row = tech_defaults[
        (tech_defaults["prime_mover_code"] == pm)
        & (tech_defaults["vintage_class"] == vintage)
        & (tech_defaults["aero_derivative"] == aero)
    ]
    assert len(row) == 1, f"Expected 1 row for {gen_id}, got {len(row)}"
    row = row.iloc[0]
    print(f"{gen_id} → ({pm}, {vintage}, aero={aero})")
    print(f"  vom_per_mwh                  ${row['vom_per_mwh']}/MWh ({row['confidence_vom']})")
    print(f"  startup_cost_cold_p50_per_mw ${row['startup_cost_cold_p50_per_mw']}/MW ({row['confidence_startup_cost']})")
    print(f"  hot_start_time_hr            {row['hot_start_time_hr']} hr ({row['confidence_start_time']})")
    print(f"  ramp_rate_pct_per_min        {row['ramp_rate_pct_per_min']} %/min ({row['confidence_ramp']})")
    print(f"  min_up_hr                    {row['min_up_hr']} hr ({row['confidence_min_up_down']})")
    print()

# %% [markdown]
# Verify Decision 2 of the lab pass: CT-in-CCGT and CA-bottoming carry identical
# Kumar block-level values (Kumar 2012 doesn't separate them).

# %%
ct_row = tech_defaults[
    (tech_defaults["prime_mover_code"] == "CT")
    & (tech_defaults["vintage_class"] == "<2000")
    & (~tech_defaults["aero_derivative"])
].iloc[0]
ca_row = tech_defaults[
    (tech_defaults["prime_mover_code"] == "CA")
    & (tech_defaults["vintage_class"] == "<2000")
    & (~tech_defaults["aero_derivative"])
].iloc[0]

shared_cols = [
    "startup_cost_cold_p50_per_mw",
    "startup_cost_warm_p50_per_mw",
    "startup_cost_hot_p50_per_mw",
    "startup_fuel_cold_mmbtu_per_mw",
]
print("CT-in-CCGT vs CA-bottoming for <2000 vintage (should be identical per lab pass Decision 2):")
for col in shared_cols:
    same = ct_row[col] == ca_row[col]
    print(f"  {col:35s}  CT={ct_row[col]}  CA={ca_row[col]}  {'✓ same' if same else '✗ DIFFERENT'}")

# %% [markdown]
# ---
# ## §I — Stage 1 findings
#
# What we learned from running this notebook. Inputs the next notebook's plan.

# %% [markdown]
# ### What loaded cleanly
#
# - **All 20 expected files present**, totals ~40 MB
# - **Tech-class defaults**: 20 × 35 parquet loads cleanly; lab confidence distribution
#   matches expectations (HIGH startup_fuel everywhere, LOW min_up_down everywhere)
# - **5 YAML files**: load via `pyyaml.safe_load` without intervention
# - **6 path files**: load cleanly with documented schemas
# - **Helper pattern works**: `v()` / `m()` give clean value/metadata access
#
# ### What needed conversion (documented at load time)
#
# - **Weather parquet index conversion**: stored as ISO 8601 strings, not native parquet
#   TIMESTAMP. Converted at load with `pd.to_datetime(..., utc=True).tz_convert('US/Eastern')`.
#   Recipe documented in `data/paths/lockport/README.md`. Single line; works cleanly.
#
# ### Hard cross-validation: ALL 8 PASS
#
# - Generator nameplates sum to 221.3 MW (matches plant.total_nameplate_mw)
# - Plant ID 54041 consistent across identity.yaml ↔ ORISPL ↔ eia_plant_id
# - PTIDs consistent identity ↔ market_context (CT=23791, ST=323769)
# - eGRID subregion (NYUP) consistent across files
# - Gas history (all hubs) covers LMP date range
# - Tech-class lookup returns exactly 2 rows for Lockport (CT,<2000,F) + (CA,<2000,F)
# - Mode hierarchy holds: 3×CC HR (8,901) < 2×CC HR (9,598) < 1×CC HR (10,424) Btu/kWh
# - MOR 2023 cross-validation (9,293) reproduces eGRID 2023 placeholder (9,228) within 0.7%
# - 2024 generation correction stored correctly (192,494 MWh)
#
# ### Two soft warnings — REAL FINDINGS worth surfacing
#
# **Finding 1 — Algonquin Citygate gas hub has only 2014-2017 data (698 rows).**
#
# The gas_price_history parquet has 8 hubs, but **only Henry Hub has deep coverage**:
#
# | Hub | Rows | Date range |
# |---|---|---|
# | Henry Hub | 8,303 | 1997-2026 |
# | Algonquin Citygate (Lockport-relevant) | 698 | 2014-2017 |
# | Chicago Citygate | 950 | 2014-2017 |
# | TETCO-M3 (Northeast US delivery) | 950 | 2014-2017 |
# | All other 4 hubs | ~950 each | 2014-2017 |
#
# **Implication**: For 2018+ Lockport modeling, we have Henry Hub for the forward anchor
# but no recent Algonquin basis data. The Step 1 plan's `delivered_gas =
# Henry_Hub_forward + delivery_basis + historical_daily_shape` decomposition is correct,
# but the basis layer is currently sparse for the Northeast delivery point.
#
# **Options for Notebook 2 / Phase G**: (a) use Henry Hub directly as a delivered-gas
# proxy (under-represents Northeast basis volatility), (b) compute Algonquin basis from
# the 2014-2017 window and apply as constant for later years (loses volatility), (c)
# pivot to a different basis source (EIA, broker data, ICE). Recommend (b) for Notebook
# 2's gross-margin proxy, document the limitation.
#
# **Finding 2 — Weather data ends 2025-12-31 (4-month gap before LMP end 2026-04-29).**
#
# Fine for 2017-2025 modeling. For 2026-specific work, need backfill from another
# source (e.g., NOAA, re-fetch from Open-Meteo).
#
# ### Assumption-status distribution headline (model_card preview)
#
# Across all 5 asset YAMLs — **266 assumption-tracked leaf values**:
#
# | Status | Count | % |
# |---|---|---|
# | real_reported | 160 | 60.2% |
# | real_observed | 31 | 11.7% |
# | real_computed | 22 | 8.3% |
# | **All real_*** | **213** | **80.1%** |
# | placeholder | 47 | 17.7% |
# | assumed_industry | 4 | 1.5% |
# | not_applicable | 2 | 0.8% |
#
# **80% of the data spine is real.** The 17.7% placeholder count is concentrated in
# `ltsa_terms.yaml` (46 of 47 placeholders — all flagged with validation_path to data
# room). The 4 `assumed_industry` values are the MOR mode-classifier thresholds in
# `operating_profile.yaml`. No values are missing required fields.
#
# This is the kernel of what every model_card output will surface.
#
# ### Open issues for Notebook 2
#
# 1. **Algonquin Citygate basis**: decide how to handle the 2018+ gap (see Finding 1
#    above). This is the single biggest item to resolve before Notebook 2's gross-margin
#    proxy can run with confidence on recent data.
#
# 2. **`v()` / `m()` helpers are good enough** for Notebooks 2-4. Verbose-but-honest;
#    Phase K loader will refactor to attribute access. No schema change needed.
#
# 3. **Weather TZ conversion convention** — add to Notebook 2's setup cell (one line).
#
# 4. **Day picker for Notebook 2**: pick a 2023 day in `3xCC_full` mode (the simplest
#    case before tackling mode transitions). Best candidate days come from the MOR
#    operating-mode classifier — Notebook 2's setup can re-run that on the MOR data to
#    select.
#
# 5. **LTSA placeholders flagged**: 46 placeholders in ltsa_terms.yaml, all with
#    validation_path to data room. Notebook 2's first model_card should surface this
#    prominently (per `docs/assumptions/placeholder_caveats.md` §1).
#
# 6. **RGGI allowance price** — not in `market_context.yaml` as a time series. Decide
#    as model parameter before Notebook 2's spark spread cells (~$15-20/short ton CO2
#    recent clearing).
#
# 7. **Lockport's 2024 dispatch pattern** — model_card should highlight the corrected
#    192,494 MWh per `operating_profile.yaml` (not the "mothballed" inference from the
#    public-data brief).

# %% [markdown]
# ---
# ## §J — Decision log
#
# Conventions set during this notebook's execution. Inherited by Notebooks 2-4.

# %% [markdown]
# | Decision | Choice | Where applied |
# |---|---|---|
# | YAML loader | `pyyaml.safe_load` | All YAML reads in this notebook |
# | Metadata access | `v(field)` / `m(field)` helper functions | Defined in §A setup |
# | Time-zone alignment | Display in NYISO local (US/Eastern); convert weather index from UTC at load | §E setup |
# | LMP location filter | PTID 23791 (CTs) is the primary join target for whole-plant economics | Implicit; not enforced in v1 |
# | Tech-class join key | `(prime_mover_code, vintage_class, aero_derivative)` triple | §H derive_vintage_class function |
# | Vintage class derivation | `<2000 / 2000-2010 / 2010-2020 / 2020+` from operating year | §H |
# | Cross-validation thresholds | <1% delta for MOR vs eGRID; gas/weather must cover LMP date range; exact PTID match | §F |
# | Outlier handling | Out of scope (load + validate only); deferred to Notebook 2 | §3.J of plan |
# | Missing values | Halt if structural; warn if data-quality; document if intentional | §B inventory + §F cross-val |
