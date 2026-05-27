# forward — Code Architecture

> Module layout, the analog method, and the data flow in [`src/forward/`](../../../src/forward/).
> Conceptual companion: [`plans/forward_engine_plan.md`](../../plans/forward_engine_plan.md).

---

## System overview

**Four small, single-responsibility modules** in a linear pipeline, all functions (no classes):

```
data.py    load price(basis)/weather/gas over full history, in run_path's schema
   │
select.py  score Apr→Mar windows vs SEAS5 temperature anomaly → probabilities
   │
build.py   selected windows → scenario specs (date spans + probability)
   │
run.py     gt_engine.run_path over each scenario → probability-weighted P10/P50/P90 + artifacts
```

Each module is runnable standalone (`python src/forward/<module>.py`) via a `sys.path` bootstrap + a `__main__` block, and importable as `forward.<module>`.

---

## Module responsibilities

### `data.py` — the basis-aware loader
Builds the three objects `gt_engine.run_path` expects, over the **full available range** (the engine's own globals are pre-sliced to 2017–2025, too short for RT's 1999 windows):
- `load_price_hourly(basis)` → `DataFrame[datetime_local (Eastern), price]`. Built from `interval_start_utc` → **floor to hour in UTC** (avoids a DST fall-back `AmbiguousTimeError`) → convert to Eastern → average within the hour (no-op for DA; collapses sub-hourly RT). `basis="DA"` reads `lmp_da_hourly`; `"RT"` reads `lmp_rt_intervals`.
- `load_weather()` → full hourly weather, Eastern-indexed, with `temp_f` (°C·9/5+32).
- `load_gas()` → Henry Hub with `trade_date_dt`.
- `load_market(basis)` → `(lmp_window, weather_window, henry)`.

### `select.py` — the temperature-analog selection (the ported method)
Scores each continuous **Apr→Mar window**:
1. `monthly_climatology(weather)` → historical year-month means → per-month `mu`, `sigma`.
2. `s2s_monthly(seas5, mu, sigma)` → SEAS5 ensemble-mean monthly temp → standardized anomaly `z_s2s[m]`, with the **coverage gate** (a month counts only if ≥80% of its calendar days are in the forecast — Apr–Oct for the current file).
3. `candidate_windows(weather, price, gas)` → eligible windows where price+weather+gas all cover ≥99% (price history sets the pool: RT→25, DA→8; gas is business-day so coverage is checked forward-fillable).
4. `score_windows(...)` → window distance `D(w) = sqrt(Σ αₘ (z_hist − z_s2s)²)` over valid months → **softmax** (τ=0.5) → **floor** (0.02) → renormalized probabilities.
Returns a `SelectionResult` (window_weights, month_scores, contributions, valid_months, seas5_init).

### `build.py` — scenario specs
`build_scenarios(selection, basis)` → one row per eligible window: `path_id`, `source_window_id`, `source_start_year`, `probability`, `sim_start`, `sim_end` (the native Apr→Mar span). No hour-by-hour rebasing (see §native-date design below).

### `run.py` — the forward run + aggregation
`run_forward(mode, seed, basis, aged_start=True)`:
- `sel = select(basis)`, `scen = build_scenarios(sel, basis)`, `lmp_full, wx_full, henry = load_market(basis)`.
- If `aged_start` (default): `init_override = run_mode(mode)["final_state"]` (one historical replay) — passed to every scenario's `run_path` so the A/B/C wear policy starts from realistic accumulated wear (ADR-009).
- For each scenario: slice `lmp_full`/`wx_full` to the window span → `gt_engine.run_path(..., init_state_override=init_override)` → collect spark, LTSA, Net P&L, MWh, fired hours.
- `weighted_quantile(values, weights, q)` → probability-weighted P10/P50/P90 (+ mean) per metric.
- Save `per_path.parquet`, `quantiles.json`, `manifest.json`.

---

## Data flow

```
data/paths/lockport/  (weather_hourly, lmp_{da_hourly,rt_intervals}, gas, weather_forecast_seas5.json)
        │
        ├─ select.load_inputs(basis) ─► windows scored vs SEAS5 ─► probabilities ─┐
        │                                                                         │
        └─ data.load_market(basis) ─► full-range (lmp,weather,gas) ───────────────┤
                                                                                  ▼
                build.build_scenarios ─► per-window specs ─► run.run_forward
                                                              for each window: slice → gt_engine.run_path
                                                              → per_path → weighted quantiles → artifacts
```

The engine import in `run.py` is wrapped in `redirect_stdout` to suppress the engine's import-time diagnostic prints (useful for the historical driver, noise here).

---

## Key patterns & conventions

- **Basis-agnostic pipeline**: `basis` threads through `select`/`build`/`run` (default `"RT"`); the engine runs whatever price it's fed. Switching DA↔RT is a one-arg change, not a rebuild — this is why the [DA→RT switch](../../plans/forward_engine_plan.md) was localized.
- **Native-date design (no rebasing)**: each window runs over its real Apr→Mar dates. Valid because the engine's aging is relative to each run's `sim_start` and a fresh 1-yr run never crosses an EOH inspection threshold → runs are comparable. Rebasing onto a common 2026 calendar is only needed for fan-chart presentation + forward-price anchoring (deferred).
- **Probability-weighted quantiles**: with a handful of weighted scenario outcomes, `weighted_quantile` uses centered cumulative weight + interpolation — honest for a small ensemble (no fake smoothing).
- **Self-contained `src/` (no model-gpr runtime dependency)**: the method was *ported* (model-gpr's was an in-memory prototype). The model-gpr scenario package can later substitute at the `select`/`build` seam.
- **Import bootstrap**: each module inserts `src/` on `sys.path` so it runs both as a script and as `forward.<module>`.

## Where to go next
- [`03_function_reference.md`](03_function_reference.md) — per-function API.
- [`04_io_schemas.md`](04_io_schemas.md) — scenario spec + output schemas.
