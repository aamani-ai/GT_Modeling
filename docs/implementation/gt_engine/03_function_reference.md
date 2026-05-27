# gt_engine — Function Reference

> Every function in [`src/gt_engine/engine.py`](../../../src/gt_engine/engine.py), grouped by category. Signatures are current as of the 2026-05-27 extraction (post ADR-006/007).

---

## Helpers (YAML unwrap)

#### `v(field) -> Any`
Unwrap a status-tagged YAML leaf: if `field` is a `{value, status, source}` dict, return `field["value"]`; else return `field` as-is. Used everywhere config is read.

#### `m(field) -> dict | None`
Return the *metadata* (status/source) of a status-tagged leaf, or `None` if not tagged.

#### `load_yaml(name) -> dict`
Read `data/assets/lockport/{name}.yaml`. Called at import for `identity`, `engineering`, `market_context`, `operating_profile`, `ltsa_terms`.

---

## State

#### `PlantState` (dataclass)
The engine's memory (14 fields): 9 stress accumulators (`eoh`, `hr_recov`, `fouling`, `dc`, `df`, `tbc_time`, `tbc_thresh`, `hrsg_cycles`, `rotor_life`), continuity (`op`, `hrs_off`, `last_stype`), outage tracking (`outage_days_remaining`, `outage_type`). Field meanings: [`architecture.md`](../../methodology/architecture.md) §5.1.

#### `init_state(seed=42) -> PlantState`
Fresh state at the v1 starting point (EOH=24,000, rotor_life=0.35, etc.). Samples `tbc_thresh` from the TBC Weibull using a seeded RNG, so the TBC failure point is reproducible per seed.

#### `init_ltsa_state() -> dict`
The LTSA accrual accumulator: the 8 cumulative cost streams + YTD trackers (starts by type, calendar/avail days, fuel/MWh for the HR-guarantee cycle) all zeroed.

---

## Inspection schedule

#### `snap_to_shoulder(date) -> Timestamp`
Snap a date to the next maintenance "shoulder" (April 1 or October 1) — inspections are scheduled in spring/fall, not mid-summer/winter.

#### `build_maint_schedule(mode, start_date, initial_eoh, sim_end) -> list[dict]`
Pre-build the CI/MI inspection schedule for a run: project EOH forward at the mode's burn-rate multiplier, place each inspection at its EOH threshold, snap the date to a shoulder. Returns a list of events `{type, threshold_eoh, scheduled_date, completed}`. Consumed by the inspection-trigger step of `run_path`.

---

## Policy (Mode A/B/C)

#### `wear_penalty_mult(mode, eoh_headroom) -> float`
The policy-mode hurdle curve. Mode A → always 1.0 (no self-curtailment); Mode B/C ramp the multiplier up (to 2.5×/4.0×) as EOH headroom to the next inspection shrinks below ~4,000. The multiplier scales the start-decision wear hurdle. (Lockport's low CF means headroom rarely binds → B/C barely diverge from A; see [`architecture.md`](../../methodology/architecture.md) §5.5.)

---

## Physics (per-hour capacity + heat rate + wear weighting)

#### `ambient_derate_factor(temp_f, gen) -> float`
Capacity derate vs ambient: winter boost below 32°F, summer derate above 90°F, linear between, per the generator's EIA-860 sensitivity. (Air-breathing-machine physics: hot air is thin air.)

#### `ambient_wear_factor(temp_f) -> float`  *(ADR-006)*
Hot-section wear maintenance factor, re-anchored at `AMBIENT_WEAR_REF_F` (34.3°F) so its fired-hour-weighted mean ≈ 1.0. >1 hotter, <1 colder; bounded [0.7, 1.4]. Applied only to creep (`dc`) and `tbc_time`, only over fired hours — **redistributes** wear toward hot hours without re-levelling the total.

#### `hr_clean_for_mode(mode_name) -> float`
The mode's clean (undegraded) heat rate from `operating_profile.yaml` (MOR-derived).

#### `hr_degraded_for_mode(mode_name, state) -> float`
Clean HR scaled up by current degradation: `× (1 + hr_recov/100) × (1 + fouling/100)`.

#### `cap_eff_for_mode(mode_name, temp_f) -> float`
Effective capacity (MW) for the mode at this ambient = sum of per-generator nameplate × `ambient_derate_factor`.

---

## Dispatch (one day)

#### `dispatch_day_mode_aware(state, hourly_inputs, gas_henry_hub, must_run, use_degraded_hr, wear_mult) -> dict`
The hourly mode pick for one day. For each hour and each mode, computes `spark = LMP − (HR/1000)(gas+RGGI) − VOM`; when starting from off, subtracts the **commitment hurdle** (full start C&M / min-run amortization) + the **policy wear hurdle** (`wear_mult`); picks the mode with the highest `max(eff_spark,0) × capacity`. Handles must-run/steam-only fallback, start-type detection (cold/warm/hot from `hrs_off`), and accumulates the **ambient-weighted fired hours** (`fired_hours_hotweighted`).
**Returns** a dict: `total_mwh`, `fired_hours`, `fired_hours_hotweighted`, `starts` (list of types), `mode_sequence` (24), fuel/revenue/cost components, `gross_margin_usd`, `ending_op`, `ending_hrs_off`. Called **twice per day** (clean + degraded HR) for loss attribution.

---

## Wear & failure (state evolution)

#### `update_stress(state, fired_hours, starts, fired_hours_hot=None) -> float`
Advance the accumulators in place; returns `delta_eoh`. Hot-section terms (`dc`, `tbc_time`) advance on `fired_hours_hot` (ambient-weighted, ADR-006); `eoh`/`fouling`/`hr_recov`/`rotor_life` on raw `fired_hours`; `df` per start. Applies the `dc+df > D_LIM` creep-fatigue interaction halving. If `fired_hours_hot is None`, falls back to raw (pre-ADR-006 behaviour).

#### `p_forced_components(state, years_elapsed=0.0) -> dict`
Daily forced-outage hazard. GT-side = `p_combustion(df)` + `p_tbc(tbc_time)` + `p_rotor(rotor_life)` + `p_creep(dc)` (ADR-007); plus aged `p_hrsg`, `p_bg`. Combined by independence, capped at 10%/day. **Returns** all components + `p_combined`.

---

## LTSA & events

#### `daily_escalation(today, start) -> float`
Contract escalation factor for the day (compounding annual escalation since `start`).

#### `accrue_daily_ltsa(ltsa_state, today, sim_start_dt, delta_eoh, day_starts) -> None`
Accrue the daily streams in place: fixed fee, EOH reserve (`delta_eoh × rate × esc`), and start-overage (per-type, when YTD starts exceed the pro-rated baseline).

#### `apply_inspection_reset(state, event_type, rng) -> None`
Apply CI vs MI state resets (CI: `dc`/`df` ×0.5, fouling ×0.3, hr_recov ×0.3; MI: `dc`/`df`→0, tbc_time→0 + resample `tbc_thresh`, hrsg_cycles→0, rotor ×0.5). The only thing that reduces wear.

#### `apply_inspection_hr_penalty(ltsa_state, ci_or_mi, esc) -> float`
At cycle end, if the cycle-average heat rate exceeds the guarantee + tolerance, charge `excess_fuel × 1.25`. Returns the penalty.

#### `apply_year_end_avail_penalty(ltsa_state, year) -> float`
If YTD availability < guarantee, charge a penalty proportional to the shortfall. Returns it.

#### `sample_outage_cause(rng, pf) -> str`
Pick the forced-outage cause (`gt`/`hrsg`/`bg`) weighted by the component probabilities in `pf`.

#### `sample_outage_duration(rng, cause) -> int`
Sample outage duration in days (lognormal, median by cause).

---

## Entry points

#### `run_path(mode, seed, sim_dates, sim_start, sim_end, lmp_window, weather_window, henry, init_state_override=None) -> dict`
**The engine.** The daily state machine over an injected market path (see [`02_code_architecture.md`](02_code_architecture.md) for the loop). **Returns** `{daily, inspections, forced_outages, final_state, final_ltsa, schedule}`. `init_state_override` (a `PlantState`) starts the run from an injected **aged** state instead of the fresh `init_state` default — used by the forward to carry the historical end-state (ADR-009); a defensive copy is taken. Default `None` keeps the historical path byte-identical (regression-gated).

#### `run_mode(mode, seed=42) -> dict`
Historical-replay convenience wrapper — calls `run_path` with the module-level historical windows (`sim_dates`/`sim_start`/`sim_end`/`lmp_window`/`weather_window`/`henry`). Reproduces notebook 4 exactly. Keep this a one-liner; put logic in `run_path`.
