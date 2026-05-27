# gt_engine — I/O Schemas

> The exact inputs `run_path` consumes and the outputs it returns. (Conceptual data map: [`architecture.md`](../../methodology/architecture.md) §3/§6.)

---

## Inputs — the market path (arguments to `run_path`)

| Arg | Type | Schema / notes |
|---|---|---|
| `mode` | str | `"A"` / `"B"` / `"C"` (policy mode) |
| `seed` | int | drives forced-outage draws + TBC threshold sampling (determinism) |
| `sim_start`, `sim_end` | `pd.Timestamp` (tz=US/Eastern) | run window; `sim_end` exclusive |
| `sim_dates` | `pd.DatetimeIndex` | one entry per simulated day (Eastern) |
| `lmp_window` | `pd.DataFrame` | must have **`datetime_local`** (tz=Eastern, hourly) + **`price`** ($/MWh). Sliced per day; `price[:24]` taken |
| `weather_window` | `pd.DataFrame` | indexed by Eastern datetime; must have **`temp_f`** (°F). Used for the per-day temp array + the must-run set + ambient weighting |
| `henry` | `pd.DataFrame` | must have **`trade_date_dt`** (date) + **`price_usd_per_mmbtu`**. Forward-filled (most-recent trade ≤ day) for the daily gas cost |

**Module-level config** (not args — loaded on import from `data/assets/lockport/*.yaml` + `data/paths/lockport/`): `MODES` (heat rate + capacity per mode), `RGGI_COST_PER_MMBTU`, `VOM_USD_PER_MWH`, `START_CM_USD_PER_MW`, the wear/forced-outage/LTSA constants. Single-asset (Lockport) for v1.

> The **historical** run feeds DA 2017–2025 (the module globals); the **forward** run ([`src/forward/`](../forward/)) feeds RT 1999–2026 analog windows. Same schema, different data.

---

## Output — the `run_path` result dict

### `daily` — `pd.DataFrame`, one row per day

| Column | Meaning |
|---|---|
| `day_idx`, `date`, `mode` | index / calendar / policy mode |
| `in_outage`, `outage_type` | outage flag + type (`CI`/`MI`/`forced_*`/`""`) |
| `mwh_clean`, `mwh_degraded` | dispatched MWh under clean vs degraded HR |
| `margin_clean`, `margin_degraded` | gross margin ($) under each |
| `loss_degradation` | `margin_clean − margin_degraded` (the $ cost of degradation that day) |
| `fired_hours`, `fired_hours_hot` | raw + ambient-weighted fired hours (ADR-006) |
| `starts_count`, `cold_starts` | starts that day |
| `delta_eoh` | EOH added that day (incl. trip EOH on a forced-outage day) |
| `wear_penalty_paid`, `warming_cost_degraded` | policy wear-penalty $ (informational) + cold-start warming gas $ |
| `eoh`, `hr_recov`, `fouling`, `dc`, `df` | engineering state at end of day |
| `p_combined` | the day's forced-outage probability |
| `mode_3x_hours`, `mode_2x_hours`, `mode_1x_hours`, `offline_hours` | hours in each operating mode |
| `fixed_fee_cum` … `outage_forced_cum` | the 8 cumulative LTSA streams |

### `inspections` — `pd.DataFrame` (empty if none)
`mode`, `date`, `type` (CI/MI), `trigger` (`calendar`/`hard_stop`), `scheduled_date`, `threshold_eoh`, `state_eoh_at_trigger`, `outage_days`, `owner_cost_usd`, `hr_penalty_usd`.

### `forced_outages` — `pd.DataFrame` (empty if none)
`mode`, `date`, `cause` (gt/hrsg/bg), `duration_days`, `owner_cost_usd`, `p_forced_at_event`, `state_eoh`, `state_df`, `was_trip` (bool), `trip_delta_eoh` (ADR-007).

### `final_state` — `PlantState`
The accumulators at end of run (see [`03_function_reference.md`](03_function_reference.md)).

### `final_ltsa` — `dict`
The 8 cumulative streams + YTD trackers. Owner-uncovered LTSA total = sum of: `fixed_fee_cum`, `eoh_reserve_cum`, `ci_owner_cum`, `mi_owner_cum`, `overage_cum`, `avail_penalty_cum`, `hr_penalty_cum`, `outage_forced_cum`.

### `schedule` — `list[dict]`
The pre-built inspection schedule (`type`, `threshold_eoh`, `scheduled_date`, `completed`).

---

## Derived headline metrics (how the driver reads the result)

```python
spark_margin = daily["margin_degraded"].sum()
ltsa_owner   = sum(final_ltsa[k] for k in LTSA_8_STREAMS)
net_pl       = spark_margin - ltsa_owner
fired_hours  = daily["fired_hours"].sum()
```

These are exactly the numbers the regression test (`tests/test_gt_engine_regression.py`) pins for Mode A, and the per-scenario metrics the forward runner aggregates into P10/P50/P90.

> **Reminder**: absolute Net P&L is **not representative** — energy-only revenue + placeholder Athens LTSA. See [`pnl_ledger.md`](../../methodology/pnl_ledger.md) §4. The engine's value is the *mechanism* and the *relative* comparisons.
