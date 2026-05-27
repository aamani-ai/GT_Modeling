# gt_engine — Overview

> **Source**: [`src/gt_engine/`](../../../src/gt_engine/) (`engine.py`, `__init__.py`)
> **Concept docs**: [`methodology/architecture.md`](../../methodology/architecture.md) §5 (the engine in words), [`methodology/flowcharts.md`](../../methodology/flowcharts.md) (the same loop, visually).

## What it is

`gt_engine` is the **dispatch + wear + LTSA engine** for one gas-turbine asset — the daily simulation loop that takes a market path (prices, gas, weather) and a policy mode, and produces the daily record of dispatch, engineering wear, forced outages, inspections, and LTSA cost streams.

It was **extracted verbatim from notebook 4** (`notebooks/04_full_path_mode_comparison.py`) so that the same engine can be called by both:
- the **historical replay** (notebook 4 — runs over 2017–2025), and
- the **forward scenario runner** ([`src/forward/`](../../../src/forward/) — runs over conditioned analog windows).

One engine, one source of truth. The extraction is **regression-gated byte-identical** (`tests/test_gt_engine_regression.py` pins the Mode-A headline numbers).

## What it produces

For a single (mode, seed, market-path) run, `run_path(...)` returns a dict:

| Key | What |
|---|---|
| `daily` | DataFrame, one row per simulated day — dispatch (MWh, fired hours, starts), engineering state (eoh, dc, df, tbc_time, fouling…), and cumulative LTSA streams |
| `inspections` | DataFrame of CI/MI inspection events (trigger, EOH-at-trigger, cost) |
| `forced_outages` | DataFrame of forced-outage events (cause, duration, owner cost, was_trip) |
| `final_state` | the `PlantState` at end of run |
| `final_ltsa` | the LTSA accrual dict (the 8 cost streams + YTD trackers) |
| `schedule` | the pre-built inspection schedule for the run |

## The two entry points

```python
from gt_engine import run_mode, run_path

# Historical replay (uses the module-level historical windows; reproduces notebook 4):
result = run_mode("A", seed=42)

# Arbitrary injected market path (used by the forward runner):
result = run_path("A", seed=42, sim_dates, sim_start, sim_end,
                  lmp_window, weather_window, henry)
```

`run_mode` is a thin convenience wrapper: it calls `run_path` with the module-level historical market windows. **All the logic lives in `run_path`.**

## The three layers (what the loop does each day)

```
ENGINEERING   yesterday's PlantState (wear accumulators) → degraded heat rate + forced-outage hazard
     ↓
DISPATCH      hourly mode pick (3xCC/2xCC/1xCC/steam-only/off) on spark spread + commitment/wear hurdles
     ↓
LTSA          accrue cost streams; fire inspections (EOH/calendar); sample forced outages → tomorrow's state
```

Full conceptual treatment: [`architecture.md`](../../methodology/architecture.md) §2 (three-layer loop) and §5 (the 12-step daily loop). The wear→failure physics (ambient-weighted creep/TBC, `p_creep`, trip wear) is [ADR-006](../../decisions/006-ambient-weighted-wear.md)/[ADR-007](../../decisions/007-creep-wiring-and-trip-wear.md).

## Scope — what gt_engine is and isn't

**Is**: the per-asset daily dispatch/wear/LTSA simulator for Lockport, with module-level asset config loaded from `data/assets/lockport/*.yaml` at import.

**Isn't**:
- **Not multi-asset** — config is Lockport-specific module globals (v1). A future refactor would pass an `AssetConfig` object; for now it's one asset.
- **Not the scenario generator** — it consumes a market path; producing conditioned forward paths is [`src/forward/`](../../../src/forward/)'s job.
- **Not the reporting layer** — plots, the model_card, and sanity checks stay in notebook 4 (the driver); the engine module ends at `run_path`/`run_mode`.

## Key facts to know before reading the code

- **Block-level, not per-generator** — the whole 3-on-1 CCGT is one state vector (per-CT state is v2).
- **Daily grain** — state updates once/day; dispatch is hourly within the day; outages/inspections fire daily.
- **Module-level config + data load on import** — importing `gt_engine.engine` reads the Lockport YAMLs and the historical price/gas/weather, builds the constants and historical windows, and prints a few diagnostics. (The forward runner suppresses those prints; see [`forward` docs](../forward/).)
- **Asset config path** is resolved file-relative (`Path(__file__).resolve().parents[2] / "data"`), so the module works regardless of the caller's working directory.

## Where to go next

- [`02_code_architecture.md`](02_code_architecture.md) — the module layout, `PlantState`, the `run_path` loop, and the data flow.
- [`03_function_reference.md`](03_function_reference.md) — every function's API.
- [`04_io_schemas.md`](04_io_schemas.md) — exact input/output schemas.
