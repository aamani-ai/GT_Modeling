# forward — Function Reference

> Every function in [`src/forward/`](../../../src/forward/), by module. Default `basis="RT"` throughout.

---

## `data.py` — basis-aware market loader

#### `load_price_hourly(basis="RT", asset="lockport") -> DataFrame`
Hourly LMP as `DataFrame[datetime_local (Eastern), price]`. Reads `lmp_da_hourly` (DA) or `lmp_rt_intervals` (RT); builds the hour key by flooring `interval_start_utc` **in UTC** (avoids a DST `AmbiguousTimeError`) then converting to Eastern; averages within the hour (no-op for DA, collapses sub-hourly RT). Drops null prices.

#### `load_weather(asset="lockport") -> DataFrame`
Full historical hourly weather, index → Eastern, adds `temp_f = temperature_2m·9/5+32`.

#### `load_gas(asset="lockport") -> DataFrame`
Henry Hub rows with `trade_date_dt` (date).

#### `load_market(basis="RT", asset="lockport") -> (lmp_window, weather_window, henry)`
Convenience bundle for `run.py` — the three objects `gt_engine.run_path` expects.

---

## `select.py` — temperature-analog selection

#### `load_inputs(basis="RT", asset) -> (weather, price, gas, seas5)`
Loads the conditioning inputs (weather + the basis's hourly price + gas + the SEAS5 JSON).

#### `daily_local_temp(weather) -> Series`
Local-date daily mean temperature (two-step hourly→daily to avoid DST-day bias).

#### `monthly_climatology(weather) -> (t_hist, mu, sigma)`
Historical year-month mean temps `t_hist[(year,month)]`, and per-month climatological `mu`/`sigma` across years.

#### `s2s_monthly(seas5, mu, sigma) -> (month_scores, valid_months)`
SEAS5 ensemble-mean monthly temp → standardized anomaly `z_s2s[m] = (F_s2s − mu)/sigma`. Applies the **coverage gate** (`forecast_days/calendar_days ≥ 0.80`). Returns the per-month score table + the list of valid (used) months.

#### `_source_year(window_start_year, month) -> int`
Apr–Mar mapping: Apr–Dec belong to the start year, Jan–Mar to start+1.

#### `candidate_windows(weather, price, gas, coverage_min=0.99) -> DataFrame`
Eligible Apr→Mar windows where price + weather + gas all cover ≥99% (gas checked forward-fillable since it's business-day). The price history start sets the pool size (RT 1999→~25; DA 2017→~8).

#### `score_windows(cw, t_hist, mu, sigma, month_scores, valid_months, tau=0.5, p_floor=0.02) -> (weights, contributions)`
Per eligible window: distance `D(w)=sqrt(Σ αₘ(z_hist−z_s2s)²)` over valid months → softmax(τ) → floor → renormalize. Returns the `window_weights` table (window_id, source_start_year, distance, probability) + the month-by-month contribution table.

#### `select(basis="RT", asset, tau=0.5, p_floor=0.02) -> SelectionResult`
Orchestrates the above. `SelectionResult` fields: `window_weights`, `month_scores`, `contributions`, `valid_months`, `seas5_init`.

---

## `build.py` — scenario specs

#### `build_scenarios(selection=None, basis="RT", asset="lockport") -> DataFrame`
One row per eligible window: `path_id`, `source_window_id`, `source_start_year`, `probability`, `sim_start`, `sim_end` (tz-aware Eastern; `sim_end` exclusive). If `selection` is None, calls `select(basis)`. Re-normalizes probabilities defensively.

---

## `run.py` — forward run + aggregation

#### `weighted_quantile(values, weights, q) -> float`
Probability-weighted quantile via centered cumulative weight + linear interpolation (honest for a small weighted ensemble).

#### `run_forward(mode="A", seed=42, basis="RT", save=True, return_paths=False, aged_start=True) -> dict`
The forward run. `select(basis)` → `build_scenarios` → `load_market(basis)`; for each scenario, slice the full-range market to the window span and call `gt_engine.run_path`; collect per-scenario spark/LTSA/Net P&L/MWh/fired hours; compute probability-weighted P10/P50/P90 (+ mean) per metric. `aged_start=True` (default) seeds every scenario from this mode's aged historical end-state (`run_mode(mode)["final_state"]`, computed once) via `run_path`'s `init_state_override` — so the A/B/C wear policy reflects realistic accumulated wear (ADR-009); `aged_start=False` recovers the old fresh-start behavior. **Returns** `{mode, seed, per_path (DataFrame), quantiles (dict), seas5_init, out_dir}`. If `save`, writes `per_path.parquet` + `quantiles.json` + `manifest.json` to `data/outputs/lockport/forward_runs/forward_<ts>/`.
CLI: `python src/forward/run.py [RT|DA]`.
