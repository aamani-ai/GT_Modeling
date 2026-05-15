# data/paths/ — Exogenous scenario paths

> Hourly/daily time-series inputs the dispatch model consumes — power prices, gas prices, weather. **Copied from model-gpr**, per consolidation plan §5 D3.

## What lives here

The exogenous path package that Step 2 (dispatch) needs to run. Currently sourced from:

- **model-gpr historical data** — Lockport-specific LMP node (NYISO PTID 23791 + WEST zone reference), 29-yr gas history at 8 hubs including Algonquin Citygate, 46-yr hourly weather at plant coordinates, SEAS5 forecast init Apr 2026
- *Eventually*: Step 1 scenario engine outputs — the forecast-anchored, conditioned, analog-sampled scenario paths defined in [docs/plans/step_1_climate_price_scenario_plan.md](../../docs/plans/step_1_climate_price_scenario_plan.md)

While Step 1 is in development, we use the model-gpr historical data directly as a stand-in. When Step 1 ships, this folder gets the proper scenario packages.

## Structure

```
paths/
├── README.md           (this file)
└── <asset>/            (one folder per asset)
    ├── README.md       (per-asset file inventory + provenance)
    ├── lmp_da_hourly.parquet
    ├── lmp_rt_intervals.parquet
    ├── lmp_<backup_zone>_da.parquet  (backup reference)
    ├── gas_price_history.parquet
    ├── weather_hourly.parquet
    └── weather_forecast_<source>.json
```

## Conventions

Per [Step 1 plan](../../docs/plans/step_1_climate_price_scenario_plan.md) "Scenario Package Schema":

### Hourly path table

| Field | Frequency | Units | Required |
|---|---|---|---|
| `timestamp` | hourly | local market time + UTC | Yes |
| `iso` | static | text (NYISO, ERCOT, PJM, ...) | Yes |
| `power_location` | static | text (hub or PTID) | Yes |
| `power_basis` | static | DA / RT | Yes |
| `power_price` | hourly | $/MWh | Yes |
| `ambient_temp` | hourly | °F or °C (explicit) | Yes |
| `relative_humidity` | hourly | percent | Optional |
| `wind_speed` | hourly | m/s or mph | Optional |
| `pressure` | hourly | hPa | Optional |

### Daily path table

| Field | Frequency | Units | Required |
|---|---|---|---|
| `date` | daily | local date | Yes |
| `delivered_gas_price` | daily | $/MMBtu | Yes |
| `henry_hub_price` | daily | $/MMBtu | Recommended |
| `gas_basis` | daily/monthly | $/MMBtu | Recommended |

## v1 scope: Lockport only

Per consolidation plan §5 D4, only `lockport/` is populated. Future assets get their own folders following the same convention.

## Status

| Asset folder | Phase | Status |
|---|---|---|
| `lockport/` | E | Empty — populated by Phase E (copy from model-gpr) |

## Refresh procedure

1. In model-gpr, ensure the latest data is in `local_data/<asset>/`
2. Copy each parquet/JSON into `data/paths/<asset>/` using the migration table in [consolidation plan §7](../../docs/plans/consolidation_plan.md#7-migration-mapping)
3. Compute SHA256 for each file
4. Update `<asset>/README.md` provenance section (source path + copy date + SHA + row counts + date range)
5. Commit

No automatic sync. Copy is deliberate (per consolidation plan §5 D3).

## Why copy and not symlink

Per consolidation plan §5 D3:
- Self-contained gt_models is more valuable than disk-space savings (~30 MB per asset)
- Symlinks create cross-repo dependencies that break checkouts, freeze incorrectly during model runs, and fail silently when source shape changes
- Copies make refresh a deliberate human act

## See also

- [consolidation plan §4.2](../../docs/plans/consolidation_plan.md#42-data--the-spine-new) — folder architecture
- [consolidation plan §5 D3](../../docs/plans/consolidation_plan.md#d3-copy-path-data-from-model-gpr-not-symlink)
- [consolidation plan §7](../../docs/plans/consolidation_plan.md#7-migration-mapping) — migration mapping with exact source paths
- [docs/plans/step_1_climate_price_scenario_plan.md](../../docs/plans/step_1_climate_price_scenario_plan.md) — Step 1 scenario engine plan (eventual replacement for direct historical-data use)
