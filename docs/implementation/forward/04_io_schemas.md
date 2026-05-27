# forward — I/O Schemas

> Inputs the forward pipeline reads, the intermediate scenario spec, and the run outputs.

---

## Inputs (the local data spine)

| File | Used for |
|---|---|
| `data/paths/lockport/weather_hourly.parquet` | climatology + conditioning + `temp_f` for dispatch (full history) |
| `data/paths/lockport/lmp_rt_intervals.parquet` (RT) / `lmp_da_hourly.parquet` (DA) | window eligibility + the dispatch price (basis-selectable) |
| `data/paths/lockport/gas_price_history.parquet` | Henry Hub gas (eligibility + dispatch fuel cost) |
| `data/paths/lockport/weather_forecast_seas5.json` | the SEAS5 ensemble that conditions window selection |

**SEAS5 JSON shape** (read by `s2s_monthly`): `d["data"]["temperature_2m"]["time"]` (length-N daily index) and `["data"][0]["values"]` = `{member_id: [..N..]}` (51 members). Init date = `time[0]`.

---

## Intermediate — the scenario spec (`build_scenarios` output)

`DataFrame`, one row per eligible analog window:

| Column | Meaning |
|---|---|
| `path_id` | scenario index (1..N) |
| `source_window_id` | e.g. `"2019_2020"` (the Apr→Mar historical window) |
| `source_start_year` | window start year |
| `probability` | temperature-analog selection probability (sums to 1) |
| `sim_start`, `sim_end` | the window's native Apr→Mar span (tz=Eastern; `sim_end` exclusive) |

(This is the v1 "scenario path" — a window spec, not a rebased hourly ensemble. The hourly values are read by the engine from the spine at run time.)

---

## Outputs — `data/outputs/lockport/forward_runs/forward_<ts>/`

### `per_path.parquet` — one row per scenario
`path_id`, `source_window_id`, `probability`, `spark_margin_usd`, `ltsa_owner_usd`, `net_pl_usd`, `total_mwh`, `fired_hours`, `forced_outages`.

### `quantiles.json`
For each metric (`net_pl_usd`, `spark_margin_usd`, `ltsa_owner_usd`, `total_mwh`): `{P10, P50, P90, prob_weighted_mean}` — probability-weighted across scenarios.

### `manifest.json` (provenance)
`mode`, `seed`, `basis`, `anchoring` (`raw_historical_levels`), `n_paths`, `horizon`, `seas5_init`, `valid_months`, `note`, `generated`.

### Via notebook 06
`forward_summary.png` (4-panel: SEAS5 anomaly · window probabilities · per-scenario Net P&L · weighted CDF) + `forward_model_card.md`.

---

## The `run_forward` result dict (in-memory)

| Key | Type |
|---|---|
| `mode`, `seed`, `seas5_init` | str/int |
| `per_path` | DataFrame (as above) |
| `quantiles` | dict (as above) |
| `out_dir` | str (when `save=True`) |

### Headline read
```python
res = run_forward("A", basis="RT")
q = res["quantiles"]["net_pl_usd"]      # P10 / P50 / P90 / prob_weighted_mean ($)
```

> **Reminder**: absolute levels are not representative (energy-only + placeholder LTSA). The forward output's value is the *distribution shape* and the scenario *spread* — e.g. RT surfacing the high-gas-year downside (Net to −$21M) that a DA-only pool excludes. See [`plans/forward_engine_plan.md`](../../plans/forward_engine_plan.md) §6.
