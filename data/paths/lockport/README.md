# Lockport — Exogenous Paths

> Hourly LMP, daily gas, hourly weather for Lockport. Copied from model-gpr per consolidation plan §5 D3.

## Files (planned)

| File | Source path in model-gpr | Format | What it contains |
|---|---|---|---|
| `lmp_da_hourly.parquet` | `local_data/lockport_energy_associates_lp/NEG WEST_LEA_LOCKPORT/da_hourly.parquet` | Parquet | NYISO Day-Ahead LMP at PTID 23791 (Lockport node) — ~81,742 hourly intervals (~9 yr) |
| `lmp_rt_intervals.parquet` | `local_data/lockport_energy_associates_lp/NEG WEST_LEA_LOCKPORT/rt_hourly.parquet` | Parquet | NYISO Real-Time LMP at same node — ~231,813 intervals |
| `lmp_west_zone_da.parquet` | `local_data/lockport_energy_associates_lp/WEST/da_hourly.parquet` | Parquet | NYISO WEST zone DA reference (backup) — same shape |
| `gas_price_history.parquet` | `local_data/lockport_energy_associates_lp/gas_price_history.parquet` | Parquet | 8 hubs incl. Algonquin Citygate (NYISO-relevant), Henry Hub, Chicago Citygate; 1997-01-07 → 2026-04-20 (29 yr daily); 14,701 rows × 17 cols |
| `weather_hourly.parquet` | `local_data/lockport_energy_associates_lp/lockport_energy_associates_lp_weather_hourly.parquet` | Parquet | 1980-01-01 → 2026-01-01 hourly (46 yr); 403,248 records × 19 cols (temp, humidity, cloud cover 3 levels, wind 10m+100m, precip, snowfall, radiation, pressure) |
| `weather_forecast_seas5.json` | `local_data/lockport_energy_associates_lp/lockport_energy_associates_lp_seas_daily_forecast_ECMWF_IFS_init_2026-04-02.json` | JSON | SEAS5 daily forecast, init Apr 2026 |

## Status

✅ **Populated 2026-05-14 (Phase E).** All 6 files copied from `~/code/work/infrasure_git_codes/model-gpr/local_data/lockport_energy_associates_lp/`.

Total size: 32 MB. Self-contained per consolidation plan §5 D3.

## Provenance

Copy date: **2026-05-14**

| File | Rows / records | Date range | SHA256 |
|---|---:|---|---|
| `lmp_da_hourly.parquet` | 81,742 | 2017-01-01 → 2026-04-29 (NYISO local TZ) | `c2192e95a9c788a1e5c3b9d5947a6c2a2588d8662a345d58f4f9289fb4e7475f` |
| `lmp_rt_intervals.parquet` | 231,813 | 1999-11-18 → 2026-04-28 (NYISO local TZ) | `4a9024ce71bd5d5503b09458971741af190e85769fb903461ae23c484327f2ca` |
| `lmp_west_zone_da.parquet` | 81,742 | 2017-01-01 → 2026-04-29 (NYISO local TZ) | `61de71df31e3498892eea4a371dee8e7f81c021af391abd85b30500aa938f5ee` |
| `gas_price_history.parquet` | 14,701 | 1997-01-07 → 2026-04-20 (trade dates) | `eb5d9dac6e848e47f61215990cf75efb311cf4709ac6eb6521ae79f29280874a` |
| `weather_hourly.parquet` | 403,248 | 1980-01-01T04:00:00+0000 → 2026-01-01T03:00:00+0000 (UTC index) | `5b7f45507beea4ebd888053c3d70488d1deb3644bbfe95e23f567f86599c6d3f` |
| `weather_forecast_seas5.json` | (JSON; ECMWF IFS init 2026-04-02) | seasonal forecast | `5869c3af96b6afc420d236634adaa73cac162e8e91f21b09856f22276119b340` |

Verify with: `shasum -a 256 *.parquet *.json`

## Schema notes (from copied files)

### `lmp_da_hourly.parquet`, `lmp_rt_intervals.parquet`, `lmp_west_zone_da.parquet`
11 columns: `market`, `location`, `location_type`, `datetime_local`, `price`, `energy`, plus raw-LMP columns (`interval_start_utc`, `interval_end_utc`, `lmp`, etc.). `datetime_local` is the NYISO local time column.

### `gas_price_history.parquet`
17 columns including `hub_id`, `hub_name`, `trade_date`, `delivery_start_date`, `delivery_end_date`, `price_usd_per_mmbtu`, `high_price_usd_per_mmbtu`, `low_price_usd_per_mmbtu`. **8 hubs** covered: Algonquin Citygate (NYISO-relevant for Lockport), Chicago Citygate, Henry Hub, Malin, PG&E Citygate, and others.

### `weather_hourly.parquet`
19 columns: `temperature_2m`, `relative_humidity_2m`, `dew_point_2m`, `cloud_cover` (full/low/mid/high), `surface_pressure`, `wind_direction_100m`/`_10m`, `wind_speed_100m`/`_10m`, `wind_gusts_10m`, `precipitation`, `rain`, `snowfall`, `shortwave_radiation`, `diffuse_radiation`, `direct_normal_irradiance`. Units in column names (°C, percent, hPa, m/s).

**⚠ Index timestamp format requires conversion at load time.**

The parquet's `datetime` index is stored as **ISO 8601 strings** with explicit UTC offset (e.g. `"1980-01-01T04:00:00+0000"`), not as a native parquet TIMESTAMP. This is an artifact of how Open-Meteo's API returns data in model-gpr's fetcher.

Recovery is one line — every loader (including Notebook 1) must do:

```python
import pandas as pd

df = pd.read_parquet("data/paths/lockport/weather_hourly.parquet")
df.index = pd.to_datetime(df.index, utc=True)               # → datetime64[ns, UTC]
df.index = df.index.tz_convert("US/Eastern")                 # → NYISO local (DST-aware)
```

After conversion, `df.index` is tz-aware and aligns with the `datetime_local` column on the LMP parquets (both are then US/Eastern). The LMP files store `datetime_local` as a regular column with mixed `-05:00`/`-04:00` DST offsets; weather, after the above two lines, matches that convention.

**Decision (consolidation plan §5 D3)**: do NOT re-save with a native DatetimeIndex. The source file in model-gpr is the source of truth; conversion is a consumption-time concern, captured in the loader.

Verified end-to-end: pyarrow parquet schema shows `datetime: string` with `pandas_type: unicode`; the conversion produces a `DatetimeIndex` from `1980-01-01T04:00:00+0000` to `2026-01-01T03:00:00+0000` (UTC) which converts to `1979-12-31 23:00:00-05:00` to `2025-12-31 22:00:00-05:00` (US/Eastern).

### `weather_forecast_seas5.json`
Top-level keys: `lat`, `lon`, `fetched_variables`, `data`, `errors`, `model`. ECMWF IFS initialization 2026-04-02. Seasonal forecast for use as a Step-1-conditioning signal (per Step 1 plan §"What 'Climate Simulation' Means In Gen 1"), not as deterministic forecast.

## Notes

### Gas hub relevance

Lockport is in NYISO Zone A (Western NY). The gas hub relevant to dispatch economics is **Algonquin Citygate** (Northeast US delivery). The 8 hubs in `gas_price_history.parquet` give flexibility for scenario construction; for Lockport's actual fuel cost path, use Algonquin Citygate.

Henry Hub is the forward-anchor reference per [Step 1 plan](../../../docs/plans/step_1_climate_price_scenario_plan.md) §"Gas Price Path Construction":

```
delivered_gas_t = Henry_Hub_forward_month + delivery_basis_month + historical_daily_shape_t
```

For Lockport: `delivery_basis_month` = Algonquin Citygate − Henry Hub spread.

### LMP node

- Primary (CTs): PTID 23791 — HIGH confidence (source: `eia_direct`)
- Steam side (GEN4): PTID 323769 — MEDIUM confidence (source: `eia_crossref`)

Both settle in NYISO Zone A. For dispatch modeling, joining on PTID 23791 is sufficient for whole-plant economics; the steam-side node is for finer attribution if needed.

### Weather

46 years of hourly data — sufficient for climatology, analog years, return-period analysis. Variables include irradiance (shortwave / diffuse / DNI) even though Lockport is gas — useful if we ever expand to nearby solar or to weather-correlated load modeling.

### Forecast

SEAS5 forecast is the seasonal climate signal (per [Step 1 plan](../../../docs/plans/step_1_climate_price_scenario_plan.md) §"What Climate Simulation Means In Gen 1"). Used for analog reweighting, not as a deterministic forecast.

## See also

- [data/paths/README.md](../README.md) — path folder conventions
- [data/assets/lockport/README.md](../../assets/lockport/README.md) — the asset profile this pairs with
- [consolidation plan §7 Phase E rows](../../../docs/plans/consolidation_plan.md#7-migration-mapping)
- [Step 1 plan](../../../docs/plans/step_1_climate_price_scenario_plan.md) — eventual upgrade path: replace direct historical with conditioned analog blocks anchored to forward curves
