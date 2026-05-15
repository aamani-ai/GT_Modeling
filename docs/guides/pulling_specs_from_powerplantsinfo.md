# Pulling Engineering & Modeling Specs from powerplantsinfo.org Pipeline

> **For**: anyone setting up a new asset's `engineering.yaml` / `operating_profile.yaml` / `identity.yaml` in `data/assets/<asset>/`, or auditing what an existing asset's spec is missing.
>
> **Premise**: the `renewablesinfo_org` (a.k.a. powerplantsinfo.org) repo runs a full pipeline that ingests raw EIA / EPA / Wikipedia / OSM data for 15,528 US plants and enriches it into typed dimensions. **Most engineering parameters you need for modeling already exist in those dimensions.** This guide explains how to pull them.
>
> **Outcome**: by the end of this guide you'll know exactly which fields to lift, how to status-tag them, and how to spot what's missing.

---

## §1. The two-repo workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│  ~/code/personal/renewablesinfo_org/                                │
│  (a.k.a. powerplantsinfo.org)                                       │
│                                                                     │
│  ├── data/sources/eia/eia860/eia8602024/   ← raw EIA-860 XLSXs      │
│  ├── data/sources/eia_generation/          ← raw EIA Form 923       │
│  ├── data/sources/epa_egrid/               ← raw EPA emissions      │
│  ├── data/sources/wikipedia/               ← Wikipedia narrative    │
│  └── data/dimensions/                      ← ENRICHED outputs       │
│      ├── engineering/thermal_enriched.parquet   ← 65 cols/gen       │
│      ├── emissions/                                                  │
│      ├── context/                          ← Wikipedia + LLM        │
│      ├── financial/                        ← FERC Form 1            │
│      └── generation/                       ← Annual generation     │
│                                                                     │
│  Pipeline code: riorg/dimensions/<name>/build.py                    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │  pull what you need
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ~/code/work/infrasure_git_codes/gt_models/                         │
│  (the modeling repo)                                                │
│                                                                     │
│  └── data/assets/<asset>/                                           │
│      ├── identity.yaml                                              │
│      ├── engineering.yaml         ← copy enriched fields here       │
│      ├── operating_profile.yaml   ← MOR-derived data goes here      │
│      ├── market_context.yaml                                        │
│      └── ltsa_terms.yaml                                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Rule of thumb**: always check the **enriched dimension parquet first**. If the field you need is there, copy it. Only fall back to raw EIA XLSXs for fields the enricher doesn't surface.

---

## §2. What lives where — quick reference

### §2.1 Engineering & physical specs

| You need | First check | Fall back to |
|---|---|---|
| Generator inventory (count, prime mover, nameplate, vintage) | `data/dimensions/engineering/thermal_enriched.parquet` | `data/sources/eia/eia860/eia8602024/3_1_Generator_Y2024.xlsx` |
| Summer/winter capacities, ambient derate | `thermal_enriched.parquet` | EIA-860 3_1 |
| Combined-cycle topology (HRSG, duct burners, bypass) | `thermal_enriched.parquet` (`has_hrsg`, `has_duct_burners`, `can_bypass_hrsg`) | EIA-860 3_1 + 6_2 |
| Dual-fuel capability + switch times + fuel-specific capacities | `thermal_enriched.parquet` (`is_dual_fuel`, `switch_time_*`, `capacity_mw_with_gas`, `capacity_mw_with_oil`) | EIA-860 3_5 (Multifuel) |
| Min-load floors | `thermal_enriched.parquet` (`min_load_mw`, `min_load_pct`) | EIA-860 3_1 |
| Cold-start time | `thermal_enriched.parquet` (`time_to_full_load_min`) | EIA-860 3_1 |
| Boiler type (HRSG, duct burner, etc.) | `thermal_enriched.parquet` (`boiler_type`) | EIA-860 6_2 |
| CHP flag, topping/bottoming | `thermal_enriched.parquet` (`is_chp`, `topping_or_bottoming`) | EIA-860 3_1 |
| Cooling system | `thermal_enriched.parquet` (`cooling_*` — often NaN) | EIA-860 8 (if present) |
| Plant location, lat/lon, county, NYISO/PJM zone | `data/dimensions/engineering/` plant join + `2___Plant_Y2024.xlsx` | — |
| Gas pipeline | `2___Plant_Y2024.xlsx` (`Natural Gas Pipeline Name 1`) | — |

### §2.2 Market and pricing

| You need | First check |
|---|---|
| LMP node, ISO zone | `data/dimensions/pricing/` (Lockport: `node_crosswalk.parquet`) |
| eGRID emission factors | `data/dimensions/emissions/` |
| Historical LMP time series | NOT in pipeline — pull from NYISO / PJM / ERCOT / CAISO data sources externally; for gt_models, place in `data/paths/<asset>/lmp_da_hourly.parquet` |
| Gas hub history | NOT in pipeline — EIA daily spot in `data/paths/<asset>/gas_price_history.parquet` |
| Weather (NCEP, ERA5, Open-Meteo) | NOT in pipeline — pull separately |
| RGGI emission factor + price | RGGI is a static convention; document in `market_context.yaml` |

### §2.3 Operational and financial

| You need | First check |
|---|---|
| Monthly generation (multi-year) | `data/sources/eia_generation/eia_generation_monthly.parquet` |
| Annual generation | `data/dimensions/generation/generation_enriched.parquet` |
| FERC Form 1 financial | `data/dimensions/financial/` |
| Wikipedia narrative + sources | `data/dimensions/context/` |
| Forced-outage events / EFOR | NOT in pipeline — separate NERC GADS data extraction would be needed |
| MOR (Monthly Operating Report) data | NOT in pipeline — only available via data-room PDFs/XLSXs. For Lockport: see `~/code/personal/diligence-extractor/data/lockport/3.0 Lockport/3.4 O&M Reports/3.4.20 Monthly Operating Reports/`. Extract per the heat_rate_analysis notebook pattern. |

### §2.4 Contracts & LTSA

Not in the pipeline at all. **Pulled from data-room files** (`diligence-extractor` repo) and digested into `ltsa_terms.yaml`. Until extracted, all values are `status: placeholder` with Athens-prototype defaults.

---

## §3. Step-by-step: pulling specs for a new asset

Use Lockport (Plant ID 54041) as the worked example.

### §3.1 Step 1 — Confirm the asset is in the pipeline

```python
import pandas as pd
PLANT_ID = 54041

# Quick existence check
df = pd.read_parquet(
    "/Users/divy/code/personal/renewablesinfo_org/data/dimensions/engineering/thermal_enriched.parquet"
)
asset = df[df['plant_id'] == PLANT_ID]
print(f"Found {len(asset)} generator rows for plant {PLANT_ID}")
print(asset[['generator_id', 'prime_mover_code', 'nameplate_capacity_mw']].to_string())
```

Expected output for Lockport: 4 generator rows (GEN1, GEN2, GEN3, GEN4).

If asset returns 0 rows: plant may not be in the gas dataset (could be solar/wind/storage). Try `data/dimensions/engineering/solar_enriched.parquet` or `wind_enriched.parquet`.

### §3.2 Step 2 — Pull the full enriched record

```python
# Pull all 65 columns for the asset
asset_full = df[df['plant_id'] == PLANT_ID]
# Transpose so each column is a row (easier to read)
print(asset_full.T.to_string())
```

Save the output. This is your **input** for the YAML files.

### §3.3 Step 3 — Categorize fields into YAML sections

| Goes into | Fields |
|---|---|
| `identity.yaml` | `plant_id`, plant name, operator, lat/lon, county, NYISO/ISO node, online year |
| `engineering.yaml` (plant section) | `total_nameplate_mw` (computed), `hrsg_count`, `is_chp`, `combined_cycle_unit_code`, `is_ambient_sensitive`, `has_carbon_capture`, `has_repower_planned` |
| `engineering.yaml` (per-generator section) | All per-generator engineering fields: capacities, derate, min-load, boiler info, dual-fuel info, time-to-full-load |
| `market_context.yaml` | NYISO zone, eGRID subregion, RGGI applicability, gas pipeline name, gas hub treatment decision |
| `operating_profile.yaml` | MOR-derived: heat rates by mode, cold-start gas, DHTS pattern, steam-only mode params, mode distribution |
| `ltsa_terms.yaml` | Placeholder (Athens defaults) until data-room extraction |

### §3.4 Step 4 — Status-tag every leaf

Every value in YAML needs a `status` code per [`docs/assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md):

```yaml
# Pulled directly from EIA-860 → real_reported
min_load_mw:
  value: 30.0
  status: real_reported
  source: "EIA-860 schedule 3_1 Y2024 — Minimum Load (MW)"
  caveat: "Design/permit floor (62% of nameplate). Not observed economic min."

# Derived from real values via formula → real_computed
min_load_pct:
  value: 62.0
  status: real_computed
  source: "min_load_mw / nameplate_capacity_mw × 100"

# Class-default for similar plants → assumed_techclass
vom_per_mwh:
  value: 1.02
  status: assumed_techclass
  source: "tech_class_defaults: prime_mover=CT, vintage<2000, non-aero"
  confidence: MEDIUM

# Pending real data from contract → placeholder
ltsa_fixed_monthly_fee:
  value: 850000.0
  status: placeholder
  source: "Athens prototype [ASSUME] default"
  validation_path: "Data room: '3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx'"
```

### §3.5 Step 5 — What if a field is NaN in the enriched dimension?

Federal data is sparse. Cooling info, boiler efficiency, firing rates, turndown ratio — these are often NaN. Three options:

1. **Skip the field** in YAML (don't include it; let downstream code raise if needed)
2. **Mark `not_applicable`**:
   ```yaml
   cooling_intake_gpm:
     value: null
     status: not_applicable
     source: "EIA-860 has no cooling intake data for this plant"
   ```
3. **Mark `placeholder` with research path**:
   ```yaml
   max_steam_flow_klb_per_hr:
     value: null
     status: placeholder
     source: "Not in EIA-860"
     validation_path: "Could pull from plant nameplate or NDA-protected technical spec"
   ```

### §3.6 Step 6 — Cross-validate where possible

For Lockport, the heat rate, mode distribution, and cold-start frequency were **cross-validated** against MOR data (the gold-standard plant-self-reported source). This is the highest-confidence way to status-tag operational values as `real_observed`.

Check `data/dimensions/generation/generation_enriched.parquet` for cross-validation of annual MWh totals.

---

## §4. Worked example — Lockport new-asset setup checklist

This is the checklist I followed to set up Lockport. Use as template for new assets.

### Phase 1: Skeleton

- [ ] Create `data/assets/<asset>/` folder
- [ ] Write `identity.yaml` (plant ID, name, location, owner, online date, ISO node)
- [ ] Verify the asset exists in `data/dimensions/engineering/thermal_enriched.parquet`
- [ ] Verify the asset exists in `data/dimensions/generation/generation_enriched.parquet`
- [ ] Skim `data/dimensions/context/` (Wikipedia summary) for narrative

### Phase 2: Engineering YAML

- [ ] Pull `thermal_enriched.parquet` for the plant — transpose, eyeball all 65 fields
- [ ] Generate plant-level summary (total MW, HRSG count, CHP flag) → `engineering.yaml` `plant:` section
- [ ] Per-generator: copy capacity, derate, min-load, dual-fuel, boiler topology fields
- [ ] **Critical:** check for `has_duct_burners=Y` and `boiler_type=Db` — flag that the plant may have steam-only mode capability
- [ ] **Critical:** check `is_dual_fuel` and `secondary_energy_source` — note if dual-fuel is real
- [ ] **Steam-only-mode check** (cogen plants only): use the 3-path framework below to determine whether the plant can deliver steam without producing electricity:

  | Path | Required equipment | EIA-860 signal |
  |---|---|---|
  | 1. **Fresh-air-fired duct burner** | `boiler_type="Db"` + air permit allowing standalone DB firing | `has_duct_burners=Y` + `boiler_type="Db"` in 6_2 |
  | 2. **Auxiliary boiler** | Separate package boiler with own stack | Additional non-Db boiler row in 6_2 (rare) |
  | 3. **Off-site steam supply** | Shared header with neighbor facility | Not in EIA-860; check site context |

  **If NONE of the three paths exist** → plant cannot do steam-only; must run at least 1 CT to deliver steam. Document in `caveats.md`: "Plant has no steam-only mode — steam delivery requires CT operation."

  **If Path 1 (duct burner) exists** → also check Title V air permit in the data room (`3.3.* Title V`) to confirm standalone DB firing is permitted.

  **Cross-validate against MOR if available**: count days with 0 MWh + non-zero gas + non-zero DHTS in MOR data. If material count → confirmed steam-only behavior; pull empirical gas/day, DHTS/day, share-of-days into `operating_profile.yaml.steam_only_mode`.

- [ ] Status-tag everything: `real_reported` for direct EIA values

### Phase 3: Market context

- [ ] Pull from `2___Plant_Y2024.xlsx`: NERC region, BA, gas pipeline name
- [ ] Pull from `data/dimensions/pricing/`: LMP node ID(s)
- [ ] Pull from `data/dimensions/emissions/`: eGRID subregion + emission factor
- [ ] Decide on gas hub treatment (Henry Hub vs basis) → ADR if needed
- [ ] RGGI applicability based on state + eGRID

### Phase 4: Operating profile (MOR-driven)

- [ ] If asset has MOR in diligence-extractor: extract per the `daily_heat_rate_analysis.ipynb` pattern
- [ ] Derive: heat rate by mode, mode distribution (3xCC/2xCC/1xCC share), cold-start frequency
- [ ] **Critical:** check for steam-only days (0 MWh + non-zero gas + non-zero DHTS) → quantify mode share
- [ ] Annual generation pattern — compare to `data/dimensions/generation/`
- [ ] Status-tag as `real_observed` (MOR is plant-self-reported truth)

### Phase 5: LTSA placeholder

- [ ] Copy Athens-prototype defaults from existing assets' `ltsa_terms.yaml`
- [ ] Status-tag everything as `placeholder` with `validation_path` to data-room file
- [ ] Note in `caveats.md` that all LTSA dollar magnitudes are not deal-realistic

### Phase 6: Caveats

- [ ] Write `caveats.md` enumerating: cogen markup, must-run synthesis, dual-fuel never fires, gas hub treatment, RGGI calculation method, any other v1 simplifications
- [ ] Write `provenance.md` mapping each YAML value to source

### Phase 7: Verification

- [ ] Run tests in `tests/test_<asset>_static_profile.py`
- [ ] Verify YAML loads cleanly in N1 (`notebooks/01_data_spine_load_validate.py`)
- [ ] Sanity-check assumption distribution: aim for >75% real_* by leaf count

---

## §5. Common gotchas

### §5.1 EIA Form 923 lags ~6-12 months

Recent-year generation data from EIA-923 is often incomplete (only 1-2 months populated). For backtesting use either:
- Older complete years (2017-2022 generally OK as of mid-2026)
- MOR data when available (no lag)

See [`../methodology/extra/backtest_findings.md` §3.2](../methodology/extra/backtest_findings.md) for the EIA-923 vs MOR data-quality check.

### §5.2 Boiler/cooling fields are often NaN

EIA-860 has detailed boiler/cooling schedules but plant-level reporting is sparse. Don't assume all fields are populated — handle NaN gracefully.

### §5.3 The "boiler" entry in EIA-860 might not be what you think

For a CCGT, the HRSG technically is a boiler under EIA classification — but it may be reported as `Db` (Duct Burner) if it has supplemental firing capability. **Look at `boiler_type` not just `has_hrsg`**.

### §5.4 Time-from-cold-to-full-load is often the clustering value "12H"

EIA reports this in coarse buckets. 86% of CCGTs report exactly 720 min. Use vendor/MOR data for more granular cold-start timing.

### §5.5 Capacities vary across fuel types

Dual-fuel plants have separate capacity figures for gas vs oil. Don't assume `nameplate_capacity_mw` is what fires on oil. Check `capacity_mw_with_gas` and `capacity_mw_with_oil` separately.

### §5.6 EIA reports per-generator; aggregate to block at modeling time

The pipeline reports each generator (GEN1, GEN2, GEN3, GEN4 for Lockport) as a row. For block-level modeling, you aggregate. But preserve per-generator detail in YAML — v2 per-generator state will need it.

---

## §6. When to push updates back to the platform pipeline

If during asset setup you find that a useful EIA-860 field is **NOT being extracted** by the platform's `riorg/dimensions/engineering/build.py`:

1. **Confirm the field is in raw EIA-860** by reading the XLSX directly
2. **Check if it's a Lockport-specific gap** or a pipeline-wide gap (might be NaN for many plants)
3. **If pipeline-wide gap and field is broadly useful**: add to platform extractor in a separate PR (`riorg/dimensions/engineering/build.py`)
4. **If Lockport-specific gap**: just put the value directly in `engineering.yaml` with `status: real_reported` and reference the raw XLSX

For example, when building Lockport's profile we found `boiler_type='Db'` was already in the enriched dimension — pipeline was working. But cooling/turndown/firing-rate were NaN, which is a federal data limitation, not a pipeline gap.

---

## §7. Quick reference: file paths

| Path | What |
|---|---|
| `~/code/personal/renewablesinfo_org/data/sources/eia/eia860/eia8602024/` | Raw EIA-860 (12 XLSX files) |
| `~/code/personal/renewablesinfo_org/data/sources/eia_generation/eia_generation_monthly.parquet` | Raw EIA Form 923 monthly generation |
| `~/code/personal/renewablesinfo_org/data/dimensions/engineering/thermal_enriched.parquet` | Enriched thermal generators (65 cols) |
| `~/code/personal/renewablesinfo_org/data/dimensions/generation/generation_enriched.parquet` | Annual generation enriched |
| `~/code/personal/renewablesinfo_org/data/dimensions/emissions/` | eGRID emission factors |
| `~/code/personal/renewablesinfo_org/data/dimensions/pricing/node_crosswalk.parquet` | LMP node IDs |
| `~/code/personal/renewablesinfo_org/data/dimensions/context/` | Wikipedia narrative |
| `~/code/personal/renewablesinfo_org/data/dimensions/financial/` | FERC Form 1 |
| `~/code/personal/renewablesinfo_org/riorg/dimensions/engineering/build.py` | Engineering dimension builder code |
| `~/code/personal/diligence-extractor/data/<asset>/3.0 <Asset>/3.4 O&M Reports/3.4.20 Monthly Operating Reports/` | MOR raw workbooks (asset-specific) |
| `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb` | MOR extraction pattern (Lockport-tested) |
| `~/code/work/infrasure_git_codes/gt_models/data/assets/<asset>/` | Target YAML location for new asset |

---

## §8. Cross-references

- [`../methodology/architecture.md`](../methodology/architecture.md) — overall v1 architecture
- [`../methodology/pnl_ledger.md`](../methodology/pnl_ledger.md) — the economic ledger
- [`../methodology/extra/backtest_findings.md`](../methodology/extra/backtest_findings.md) — Lockport-specific backtest + data-quality findings
- [`../assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md) — the 9-code status grammar
- [`../decisions/README.md`](../decisions/README.md) — ADRs (when a data-pulling decision warrants one)
- [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) §5 D2 — locked decision: YAML for static config
