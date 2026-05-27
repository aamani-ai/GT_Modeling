# gt_engine — Code Architecture

> Module layout, the core objects, the per-run loop, and the data flow in [`src/gt_engine/engine.py`](../../../src/gt_engine/engine.py).
> Conceptual companion: [`architecture.md`](../../methodology/architecture.md) §5; visual: [`flowcharts.md`](../../methodology/flowcharts.md).

---

## System overview

**Single-module, function-style engine** (not a class). `engine.py` is one namespace that, on import, loads the asset config + historical data into module-level globals, then defines the engine functions and the `run_path` loop that operate on them.

- **Config-on-import**: YAMLs + constants + historical windows are built at import time (module globals).
- **Injected market path**: `run_path` takes the per-run time series as arguments; everything else (constants, MODES, gas cost rate, LTSA terms) is a module global.
- **Vectorized where it counts, explicit loop for the day-by-day state machine** (state evolution is inherently sequential — each day depends on yesterday).
- **Deterministic given seed** — one `np.random.default_rng(seed)` drives forced-outage draws + TBC threshold sampling.

---

## Module layout (in load order)

```
engine.py
 ├─ imports + REPO_ROOT/DATA_DIR (file-relative)        ← path resolution
 ├─ helpers: v(), m(), load_yaml()                      ← YAML {value,status,source} unwrap
 ├─ CONFIG (module globals, built on import):
 │    identity / engineering / market_context /
 │    operating_profile / ltsa_terms  (YAML dicts)
 │    MODES, gens, NAMEPLATE_*        (capacities + heat rates)
 │    VOM_USD_PER_MWH, RGGI_COST_PER_MMBTU
 │    wear constants (CREEP_*, FATIGUE_*, TBC_*, FOULING_*, AMBIENT_WEAR_*, TRIP_*)
 │    forced-outage constants (P_COMBUSTION_*, P_CREEP_*, HRSG/BG base, AGING)
 │    LTSA constants (fixed fee, EOH reserve, overage, inspection costs)
 │    HISTORICAL WINDOWS: sim_start/sim_end/sim_dates/lmp_window/weather_window/henry
 ├─ STATE: PlantState (dataclass), init_state(), init_ltsa_state()
 ├─ SCHEDULE: snap_to_shoulder(), build_maint_schedule()
 ├─ POLICY: wear_penalty_mult()                         ← Mode A/B/C hurdle curve
 ├─ PHYSICS: ambient_derate_factor(), ambient_wear_factor(),
 │           hr_clean_for_mode(), hr_degraded_for_mode(), cap_eff_for_mode()
 ├─ DISPATCH: dispatch_day_mode_aware()                 ← the hourly mode pick (one day)
 ├─ WEAR: update_stress(), p_forced_components()        ← state evolution + failure hazard
 ├─ LTSA: daily_escalation(), accrue_daily_ltsa(),
 │        apply_inspection_reset(), apply_inspection_hr_penalty(),
 │        apply_year_end_avail_penalty(), sample_outage_cause/duration()
 └─ ENTRY: run_path(...)   +   run_mode(...) wrapper
```

`__init__.py` re-exports the public surface: `run_mode`, `run_path`, `PlantState`, `init_state`, `init_ltsa_state`.

---

## The core object — `PlantState`

A 14-field dataclass that is the engine's memory, propagated day → day:

- **9 stress accumulators** (engineering): `eoh`, `hr_recov`, `fouling`, `dc` (creep), `df` (fatigue), `tbc_time`, `tbc_thresh`, `hrsg_cycles`, `rotor_life`.
- **operational continuity**: `op`, `hrs_off`, `last_stype`.
- **outage tracking**: `outage_days_remaining`, `outage_type`.

These are the only things that carry between days. Damage never decays on its own — only inspection resets reduce it. (Field-by-field meaning: [`architecture.md`](../../methodology/architecture.md) §5.1.)

---

## The per-run loop — `run_path`

`run_path(mode, seed, sim_dates, sim_start, sim_end, lmp_window, weather_window, henry, init_state_override=None)` is the daily state machine (the optional `init_state_override` lets a run start from an injected aged state — ADR-009; default `None` = fresh). Setup → loop → return:

```
SETUP
  state = init_state(seed); ltsa_state = init_ltsa_state()
  schedule = build_maint_schedule(mode, sim_start, state.eoh, sim_end)
  rng = default_rng(seed)
  must_run_days = coldest 20% of days (cogen must-run proxy, from weather_window)

FOR each day in sim_dates:
  [1] year-boundary? → apply year-end availability penalty; reset YTD trackers
  [2] in a continuing outage? → accrue fixed fee, decrement, record, continue
  [3] sample forced outage vs p_forced_components(state):
        if hit → owner cost; TRIP WEAR if was running (df+eoh); set outage; record; continue
  [4] look up next inspection; compute EOH headroom
  [5] wear_penalty_mult(mode, headroom)            ← Mode A/B/C hurdle
  [6] gas_hh = most-recent Henry Hub price ≤ today  (henry, forward-filled)
  [7] build the day's 24-hour (lmp, temp_f) frame from lmp_window + weather_window
  [8] TWIN dispatch: dispatch_day_mode_aware() twice (clean-HR and degraded-HR)
        → loss attribution = clean margin − degraded margin
  [9] cold-start warming-gas correction
  [10] commit op state; update_stress(degraded fired_hours, starts, fired_hours_hot)
  [11] accrue_daily_ltsa(); cycle-end HR tracking
  [12] inspection trigger (EOH hard-stop OR calendar) → cost + HR penalty + state reset
  record the day
RETURN {daily, inspections, forced_outages, final_state, final_ltsa, schedule}
```

`run_mode(mode, seed)` = `run_path(mode, seed, <the module-level historical windows>)`.

---

## Data flow

```
data/assets/lockport/*.yaml  ─┐
data/paths/lockport/*         ─┤ (import time)
data/tech_class_defaults/     ─┘ → MODES, constants, historical windows (module globals)

(per run) market path ──► run_path ──► daily loop ──► result dict
   lmp_window  ─────────────► [7] hourly frame ─► dispatch_day_mode_aware
   weather_window ──────────► [7] temp_f + must-run set + ambient weighting
   henry ───────────────────► [6] daily gas cost
   PlantState (carried) ◄────────────────────────── update_stress / inspection resets
```

For the **historical** run the market path is the module globals (DA 2017–2025). For the **forward** run, [`src/forward/`](../forward/) builds a different market path (RT analog windows, full 1999–2026) and injects it — the engine code is identical.

---

## Key patterns & conventions

- **Verbatim extraction**: the logic is byte-for-byte from notebook 4. The *only* structural change was `run_mode → run_path` (parameterize the 6 market-path inputs) + a `run_mode` wrapper. This is why the regression test reproduces the old numbers exactly — and why future logic edits must update the regression baseline deliberately.
- **`run_path` vs `run_mode`**: put new dispatch/wear logic in `run_path` (it's the real engine); `run_mode` should stay a one-line wrapper.
- **Module globals for config**: acceptable for single-asset v1; the known refactor is to pass an `AssetConfig`. Functions read globals like `MODES`, `RGGI_COST_PER_MMBTU`, `START_CM_USD_PER_MW` directly.
- **Twin dispatch**: every day is dispatched twice (clean vs degraded heat rate) purely to attribute the $ cost of degradation; only the degraded run drives state.
- **Forced outage `continue`s the day**: on a forced-outage day the normal dispatch/`update_stress` path is skipped — wear that day comes only from the trip penalty (ADR-007), and the EOH-reserve accrual is done inline.

## Where to go next

- [`03_function_reference.md`](03_function_reference.md) — each function's params/returns/side-effects.
- [`04_io_schemas.md`](04_io_schemas.md) — the market-path input schemas + the result DataFrames.
