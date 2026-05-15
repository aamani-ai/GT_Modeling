# Notebook 3 — Daily Loop: State and Feedback

> **Status**: Plan drafted 2026-05-14. Awaiting user review before execution.
> **Notebook path (when built)**: `notebooks/03_daily_loop_feedback.ipynb`
> **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) — execution Phase I
> **Sibling plans**: [`README.md`](./README.md); [`01_data_spine_load_validate.md`](./01_data_spine_load_validate.md); [`02_one_day_dispatch.md`](./02_one_day_dispatch.md)
> **Prerequisites**: Phase H complete (Notebook 2 ran end-to-end with sensible dispatch). Phases A–F (data spine) populated.

---

## §1. Purpose

**Prove the recursive feedback architecture works** — the central design move of the gas turbine digital twin, per the prototype's framework V2 doc. Run a 30-day window where today's dispatch updates the plant's stress accumulators, which feed tomorrow's degraded heat rate + capacity + forced-outage probability, which feeds tomorrow's dispatch decision, and so on. This is the loop that distinguishes the twin from a static dispatch model.

Goals, in priority order:

1. **State vector lives day-to-day.** Each day produces a closing state that becomes the next day's opening state. EOH accumulates. Compressor fouling drifts up (HR degrades). Creep + fatigue damage compound. HRSG cycles count up. **The state is the load-bearing concept of the architecture** — N3 proves it.

2. **Degraded dispatch matters.** N2 had `spark_clean == spark_degraded`. N3 makes them diverge: as `hr_degraded` drifts up day-by-day, fuel cost rises, mode preference shifts, some hours that were economic become uneconomic. **Loss-to-degradation is real and quantifiable** in N3 for the first time.

3. **Endogenous forced outage probability.** `P_forced(t) = P_GT + P_HRSG + P_BG` computed from the *current state*, not a static FOR. As stress accumulates, the probability rises — Lockport-modeled forced outage risk responds to dispatch history, which is the prototype's strongest design move per understanding doc §7.

4. **Visualize the trajectory.** State evolution is not a table; it's a time-series. **First notebook with diagnostic plots** — state accumulators, P_forced components, daily MWh + cumulative margin, clean vs degraded spark attribution.

5. **Inspection threshold preview.** Don't trigger inspections (that's N4 with full CI/MI cost machinery), but compute the EOH headroom + project days-to-next-threshold + flag if hard-stop would force an inspection.

**Read-only on the data spine.** Optional outputs to `data/outputs/lockport/runs/notebook3_<window>/` for N4 to inherit (state trajectories, daily summaries).

**Decisions inherited from Notebooks 1+2 + ADR-001**:
- `v()` / `m()` helpers
- Weather TZ conversion at load
- Henry Hub direct for delivered gas (ADR-001 Frame A)
- RGGI at $17/short ton CO2 with 117 lb CO2/MMBtu factor
- Mode capacities derived from `engineering.yaml` (3×CC=221.3, 2×CC=172.6, 1×CC=123.9)
- Mode-choice heuristic from N2 (max margin per mode)
- VOM base $1.02/MWh from `tech_class_defaults`

---

## §2. Inputs

| File | Purpose | New in N3? |
|---|---|---|
| `data/assets/lockport/identity.yaml` | Plant ID, status | inherited |
| `data/assets/lockport/engineering.yaml` | Generators, capacity, **ambient sensitivity flags**, **summer/winter derates** | inherited (new use: derate curves) |
| `data/assets/lockport/market_context.yaml` | NYISO node, RGGI exposure | inherited |
| `data/assets/lockport/operating_profile.yaml` | Mode heat rates, DHTS | inherited (no change) |
| `data/assets/lockport/ltsa_terms.yaml` | EOH thresholds for CI / MI | **new in N3** (read CI/MI thresholds; LTSA cost stream computation is N4) |
| `data/paths/lockport/lmp_da_hourly.parquet` | 30 days × 24 hours | inherited |
| `data/paths/lockport/gas_price_history.parquet` | Henry Hub daily | inherited |
| `data/paths/lockport/weather_hourly.parquet` | Hourly ambient temperature for **ambient derate** | inherited (new use: derate calc) |
| `data/tech_class_defaults/dispatch_params_lookup.parquet` | VOM | inherited |

---

## §3. Cell-by-cell sketch

### §3.A — Setup

Same imports as N2 + `matplotlib` for plots.

```python
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt

# Same v() / m() helpers from N2
# Same data loading pattern from N2
# Same TZ-conversion pattern for weather
```

### §3.B — Window picker (30-day window)

Pick a 30-day window that contains both operating days and idle days, so the state evolution shows realistic interleaved patterns.

**Strategy**: extend N2's day picker logic:
1. Find a 2023 summer month (Jun-Sep) with at least 15 high-LMP days (peak LMP ≥ P50 of 2023)
2. Pick a 30-day window starting from the first high-LMP day of that month
3. Confirm the window has non-null LMP for all 720 hours
4. Document the chosen window with: number of days with peak LMP > $50, mean LMP, max LMP

**Why 30 days**: enough for state evolution to be visible (multiple operating + idle cycles), short enough to keep the notebook fast (~10s execution). The original prototype uses 10 years for a "full" simulation; 30 days is the inner-loop validator.

### §3.C — State vector definition + initialization

Match the prototype's `init_state` (per `docs/extra/understanding_of_gas_turbine_digital_twin.md` §6) **with Lockport-specific values where possible from our YAMLs**, defaults where not.

```python
@dataclass
class PlantState:
    # Engineering state
    eoh: float = 24_000.0  # Equivalent Operating Hours (post-HGP start, prototype convention)
    hr_recov: float = 0.0  # Recoverable HGP HR degradation (%) — resets at MI/CI
    fouling: float = 0.0   # Compressor fouling (% HR impact)
    dc: float = 0.0        # Creep damage fraction (Robinson)
    df: float = 0.0        # Fatigue damage fraction (Miner)
    tbc_time: float = 0.0  # TBC time-at-temperature (hrs)
    tbc_thresh: float = 28_000.0  # Per-path Weibull threshold (β=3, η=28,000)
    hrsg_cycles: float = 0.0  # HRSG HP drum cycle accumulation
    rotor_life: float = 0.35  # Rotor life fraction consumed at sim start

    # Operational continuity (carries across day boundaries)
    op: bool = False           # Online flag
    hrs_off: float = 24.0      # Hours since last shutdown (for start-type classification)
    run_hrs: float = 0.0       # Hours since current start
    last_stype: str = "cold"   # Last start type (cold/warm/hot)

    # Inspection tracking
    insp_done: int = 0   # CI+MI completed in simulation


def init_state(seed: int = 42) -> PlantState:
    """Day-0 plant state vector.

    Initial values match the prototype's convention (post-HGP at 24,000 EOH).
    TBC threshold sampled per path from Weibull(β=3, η=28,000).
    """
    rng = np.random.default_rng(seed)
    state = PlantState(
        tbc_thresh=float(28_000 * rng.weibull(3))  # Weibull threshold per path
    )
    return state
```

**Note**: the prototype's `init_state` is Athens-specific (24,000 EOH post-HGP, Weibull β=3 η=28,000 for TBC, rotor life 0.35). For Lockport we **inherit these defaults for v1** since LTSA-derived per-plant values aren't extracted yet. This is a known approximation; flag in §K findings.

**State per generator?** Athens prototype is 2×1 (one CT track + one ST track) treated as a single state. Lockport is 3-on-1 (3 CTs + 1 ST). For v1 we model **block-level state** (single state for the whole CCGT block) — refinement to per-generator state is a v2 concern. Document.

### §3.D — Per-day loop (the recursive feedback core)

This is the heart of N3. The loop must run in the order from the prototype's [§4 daily feedback loop](../../../extra/understanding_of_gas_turbine_digital_twin.md#4-the-daily-feedback-loop--order-of-operations):

```python
def run_day(state: PlantState, day_inputs: dict, modes_dict: dict, cfg: dict) -> tuple[PlantState, dict]:
    """Execute one day. Returns (new_state, day_summary).

    Order:
    1. Compute today's effective plant parameters (hr_clean, hr_degraded, cap_eff)
    2. Compute EOH headroom to next inspection threshold
    3. Run clean reference dispatch (no degradation) — counterfactual
    4. Run degraded actual dispatch (with current state) — but don't commit state yet
    5. Check inspection threshold crossing (preview only in N3; no event in N3)
    6. Compute forced outage probability (no event sampling in N3)
    7. Execute dispatch — commit operational flags
    8. Update stress accumulators — today's dispatch becomes tomorrow's degraded state
    9. (LTSA accrual deferred to N4)
    """
    ...
```

The per-day work breaks into:

#### §3.D.1 — Compute today's effective parameters

- `hr_clean(temp_f)`: mode HR + ambient correction (per `engineering.yaml` ambient sensitivity)
- `hr_degraded(state, temp_f)`: clean HR × (1 + hr_recov/100) × (1 + fouling/100)
- `cap_eff(temp_f, generator_id)`: nameplate × ambient derate factor (linear interpolation from summer/winter derate per generator)
- Delivered fuel cost (Henry Hub + RGGI; same as N2)

#### §3.D.2 — Twin dispatch (clean vs degraded)

Reuses N2's mode-choice + cogen-constraint logic, called twice:
- Once with `hr_clean` → produces `cr` (clean reference)
- Once with `hr_degraded` → produces `dr` (degraded actual)

`loss_degradation = cr['spark'] - dr['spark']` is the per-day attribution.

#### §3.D.3 — Inspection threshold preview

```python
eoh_headroom_to_ci = ci_threshold - state.eoh - 1.0  # 1 hr buffer
eoh_headroom_to_mi = mi_threshold - state.eoh - 1.0
```

Where `ci_threshold` and `mi_threshold` come from `ltsa_terms.yaml.inspection_ci.eoh_threshold` and `inspection_mi.eoh_threshold` (currently placeholder values 24,000 and 48,000 from Athens defaults).

For N3, just **track** the headroom; no event triggering. Plot it.

#### §3.D.4 — Forced outage probability from state

```python
p_combustion = max(0, (state.df / COMB_BUDGET - 0.6) ** 2 * 0.10)  # hockey-stick after 60%
p_tbc = 1.0 if state.tbc_time >= state.tbc_thresh else weibull_hazard(state.tbc_time, state.tbc_thresh)
p_rotor = 0.00003 * state.rotor_life
p_gt = p_combustion + p_tbc + p_rotor
p_hrsg = 0.0075 * (1.0 + (year_frac * 0.5))  # baseline + age scaling
p_bg = 0.004 * (1.0 + (year_frac * 0.5))
p_forced = 1 - (1 - p_gt) * (1 - p_hrsg) * (1 - p_bg)
```

For N3, **compute and log** `p_forced` daily. No event sampling (no actual forced outage). Plot the trajectory.

#### §3.D.5 — Update stress accumulators

After dispatch commits, update state per the prototype's `update_stress` ([:146](../../../extra/gas-turbine-digital-twin/EnggDTwin_model.py#L146)):

```python
state.eoh += fired_hours + START_PENALTY[start_type]  # GER-3620K counting
state.fouling = state.fouling + FOULING_RATE * fired_hours * aqi_factor  # asymptotic to 2.5%
state.dc += creep_rate(stress, temp, fired_hours)  # Robinson
state.df += fatigue_rate(starts, ramps)  # Miner
state.tbc_time += fired_hours  # all running hours count
state.hrsg_cycles += starts + ramps_per_day
# Check creep-fatigue interaction envelope
if state.dc + state.df > D_LIM:
    state.dc *= 0.5
    state.df *= 0.5  # inspection-equivalent halving
```

Constants: borrow from prototype defaults; flag any Lockport-specific override opportunities (e.g., FOULING_RATE could be derived from MOR observations someday).

### §3.E — Plot 1: State trajectory (3-panel)

Three panels stacked vertically, x-axis = day-of-window:

| Panel | Y-axis | What it shows |
|---|---|---|
| Top | EOH (left), HR degradation % (right, twin axis) | EOH accumulates day-by-day; HR drift up as fouling + hr_recov build |
| Middle | Damage fractions: dc (creep), df (fatigue) | Both compound from dispatch decisions; interaction envelope crossing visible if it happens |
| Bottom | TBC time / threshold (left), HRSG cycles (right, twin axis) | Per-path random threshold visible; HRSG cycling proportional to starts |

This is the visual proof that "today's dispatch updates tomorrow's state."

### §3.F — Plot 2: Forced outage probability decomposition

Single chart, x-axis = day-of-window, y-axis = probability/day. Three component lines + total stacked:
- `p_combustion` (df-driven)
- `p_tbc` (state.tbc_time vs threshold)
- `p_rotor` (rotor_life-scaled)
- `p_hrsg + p_bg` (baseline scaled by age)
- Combined `p_forced`

**Interpretation guide**: at start of the window, p_forced should be very small (< 0.1%/day). As the window progresses, if dispatch is heavy, p_combustion and p_tbc should drift up.

### §3.G — Plot 3: Daily MWh + cumulative gross margin

Two-panel stacked:
- Top: daily MWh (3 lines: 3×CC mode hours, 2×CC mode hours, 1×CC mode hours, offline)
- Bottom: cumulative gross margin (degraded actual) + cumulative if-clean-also reference (the counterfactual)

**Interpretation guide**: the gap between the two cumulative lines IS loss_degradation summed over the window.

### §3.H — Plot 4: Clean vs degraded daily spark attribution

Time-series of:
- `spark_clean` (counterfactual, no degradation)
- `spark_degraded_actual` (with current state)
- `loss_degradation` (the difference)

For a 30-day window with light operation, `loss_degradation` should be small (a few cents per MWh, growing slowly). For a heavy operation window, it should be more visible. Use the chosen window's dispatch pattern to interpret.

### §3.I — Sanity checks

Mirror N2's discipline. New checks for N3:

- [ ] State vector evolves monotonically where physics demands: `eoh` strictly increasing, `hr_recov` and `fouling` strictly non-decreasing between inspections
- [ ] `loss_degradation >= 0` every day (degraded HR ≥ clean HR by construction)
- [ ] `p_forced` strictly increases over the window if dispatch is heavy (no resets)
- [ ] `p_forced ∈ [0, 1]` always (no overflow)
- [ ] EOH headroom decreases day-by-day during operating days
- [ ] All ambient-derated capacities ≤ nameplate × 1.05 (winter boost cap)
- [ ] Mode choice + cogen logic identical to N2 on dispatch days (no regression in the inner loop)
- [ ] No state field becomes NaN or Inf

### §3.J — Stage 1 findings

Markdown cell. Captures what we learned. Inputs to Notebook 4's plan.

Expected findings to surface:
- State evolution scale: how much does HR degrade over 30 days? (Probably small, but should be measurable.)
- P_forced trajectory: does it rise materially in 30 days? (Probably small for a low-CF asset like Lockport — flag if it doesn't move at all, which might indicate the constants need calibration.)
- Loss_degradation magnitude: $/MWh-day. Sets expectations for the 10-year horizon.
- Mode-choice changes: did any mode-preference flips happen as HR degraded? (If yes, important — means HR drift crosses dispatch decision boundaries.)
- Cumulative cogen cost: extrapolating N2's $17K/day finding × the must-run-day count over the window.

### §3.K — Decision log

Conventions chosen during this notebook. Inherited by Notebook 4.

---

## §4. Conventions chosen for this notebook

| Decision | Choice | Rationale |
|---|---|---|
| Window size | 30 days | Long enough for state evolution to be visible, short enough to run in seconds |
| Window picker | 2023 summer, starts from first high-LMP day of chosen month, full 720 hours non-null required | Reproducible; documented criteria |
| State grain | Block-level (single state for whole CCGT) | v1 simplification; per-generator state is v2 concern |
| Initial state | Prototype's defaults: 24,000 EOH post-HGP, Weibull β=3 η=28,000 TBC, rotor_life 0.35 | Athens-derived; Lockport-specific values pending LTSA extraction |
| Inspection threshold (CI/MI) | Read from `ltsa_terms.yaml.inspection_*.eoh_threshold.value` (currently placeholder Athens values 24,000/48,000) | Documented as `placeholder` in YAML; N3 reads them; actual threshold-crossing event in N4 |
| Inspection event triggering | **N3 tracks headroom but doesn't trigger events** | Event-triggering needs CI/MI cost machinery → N4 |
| Forced outage event sampling | **N3 computes probability but doesn't sample** | Event sampling → N4 |
| Ambient derate | Linear interpolation between summer derate and winter boost per generator | Simple v1 approach; refine with vendor curves later |
| Cogen VOM markup | Applied as a multiplier (×1.35, midpoint of +30–50% range) on base VOM | Per caveats.md §2 |
| Cogen DHTS must-run | Synthetic flag per day: assume must-run on days with mean ambient temp < 50°F (proxy for winter host steam demand) | We don't have day-level DHTS from MOR in the data spine; document as proxy until MOR extraction extends |
| Min-load enforcement | Each mode dispatches at full capacity_mw if economic; offline otherwise | v1 simplification; full min-load is v2 |
| Mode-switch stickiness | None (inherited from N2) — only add if §I sanity checks show whipsawing | If whipsawing appears, add min-run-time per mode |
| Twin dispatch (clean + degraded) | Run dispatch heuristic twice per day | Per prototype convention; produces loss_degradation attribution |
| Constants (creep budget, fouling rate, Weibull, etc.) | Borrow from prototype's `EnggDTwin_model.py`; document Lockport-specific override opportunities in §K | Avoid invention; document where the prototype's Athens-calibrated numbers are inherited |

---

## §5. Validation checks (acceptance criteria)

Notebook is "done" when:

- [ ] §3.A loads all data + defines helpers without errors
- [ ] §3.B picks a 30-day window with documented criteria + non-null LMP for all 720 hours
- [ ] §3.C initializes state vector with all expected fields
- [ ] §3.D runs the day loop for all 30 days without errors
- [ ] All §3.I sanity checks pass
- [ ] §3.E-H produce 4 readable plots
- [ ] §3.J findings cell filled in
- [ ] §3.K decision log captured
- [ ] Notebook runs from fresh kernel without state pollution

**Specific numerical expectations**:

- EOH at day-30 should be in `(start_eoh, start_eoh + 720)` (can't increase faster than 1 EOH per running hour, with start penalties potentially adding more)
- `loss_degradation` cumulative over 30 days should be in `(0, $50K)` (rough envelope — small but non-zero)
- `p_forced` at day-30 should be < 5% (small for a low-CF asset)
- HR degradation at day-30 should be < 3% (in 30 days of light operation, not much drift)

---

## §6. What this notebook surfaces

Inputs to Notebook 4's plan. After N3 runs we should know:

| Question | How N3 answers it |
|---|---|
| Does state evolution work mechanically? | §3.D run completes; §3.E plot shows monotonic accumulators |
| What's the scale of loss_degradation over 30 days? | §3.H + §3.I cumulative sum |
| Does mode preference flip due to HR drift? | §3.D mode_chosen sequence — visible if 3×CC becomes uneconomic earlier in the window's tail |
| Does forced outage probability behave physically? | §3.F plot — components should rise with operation |
| Is the prototype's constant set sensible for Lockport? | §3.K findings — if EOH evolves implausibly fast, constants need refinement |
| Are the placeholder LTSA inspection thresholds workable for tracking-only? | §3.D §3.G — confirm headroom decreases sensibly |
| Does the cogen synthetic must-run flag produce reasonable dispatch differences? | §3.G P&L panel — must-run days should show different output |

---

## §7. What this notebook does NOT cover

- **Multi-path Monte Carlo.** Phase L.
- **Mode A/B/C policies.** N4 — the inspection-proximity dispatch penalty logic is what makes A/B/C differ.
- **LTSA cost streams.** N4 — fixed fee, EOH reserve, CI/MI events, overage, HR penalty, availability penalty.
- **Actual maintenance events / inspection completion.** N4 — needs LTSA cost machinery to make events meaningful.
- **Actual forced outage events.** N4 — needs the event-classification + cost-attribution logic.
- **Capacity market revenue.** Out of v1.
- **Dual-fuel switching.** Per ADR-001, never fires in v1.
- **Per-generator state.** v2 — block-level state in v1.
- **DHTS day-level data.** Currently synthetic temperature-based flag; real MOR extraction is a v2 ask of the diligence-extractor.

---

## §8. How this informs Notebook 4

Notebook 4 ("Full path + Mode A/B/C + LTSA cost streams") expects:

1. **A working stateful day-loop** — N4 extends N3's loop to a 10-year (3,650-day) simulation and adds:
   - Mode A/B/C policy curves (the per-mode EOH-proximity penalty on start cost)
   - Inspection event triggering (when headroom crosses zero with calendar shoulder-snap)
   - LTSA cost stream accrual (the 7 streams per `ltsa_terms.yaml`)
   - Forced outage event sampling (with cost classification per coverage)
2. **State vector definition is stable** — N4 doesn't add state fields; just consumes the N3 vector.
3. **Loss_degradation attribution baseline** — N4 inherits N3's clean-vs-degraded structure to break down each year into spark_actual + loss_degradation + loss_planned + loss_forced.
4. **Constants set is documented** — N4 inherits the same defaults; flagged Lockport-specific calibration opportunities propagate forward.
5. **Plots become templates** — N3's 4 plots become the basis for N4's per-year + per-mode-comparison plots.

---

## §9. Open questions to resolve during execution

| Question | How it gets answered |
|---|---|
| Does the window picker land on a meaningful 30-day window? | §3.B output |
| What's the EOH burn rate per operating day for Lockport? | §3.E top panel slope |
| Does fouling accumulate to 2.5% asymptote within the window or barely move? | §3.E top panel; depends on AQI proxy |
| How sensitive is p_forced to the 30-day window's operating intensity? | §3.F final-day value |
| Does the cogen synthetic must-run flag overcount or undercount? | §3.G — compare must-run-flagged days against §B window's typical pattern |
| Are there Lockport-specific constants we should override from the prototype defaults? | §3.K findings — flag any implausible evolution rates |

---

## §10. Risks / things that could go wrong

| Risk | Mitigation |
|---|---|
| Prototype's Athens-calibrated constants produce implausible Lockport behavior | §3.K findings cell explicitly checks evolution rates against intuition; flag overrides for N4 |
| Synthetic must-run flag (temp-based) doesn't match Lockport reality | Document as proxy; flag MOR DHTS extraction as v2 ask |
| State accumulators overflow / blow up due to wrong constant | §3.I sanity checks catch this |
| Plots are unreadable for 30-day window (too dense or too sparse) | Use 30-day x-axis with daily ticks; supplement with cumulative-views where relevant |
| Forced outage probability doesn't move in 30 days (constants miscalibrated) | Expected for low-CF asset; flag for calibration with longer Phase L horizon |

---

## §11. Output artifacts

- The notebook itself (`notebooks/03_daily_loop_feedback.ipynb` paired with `.py`)
- 4 plots embedded in the notebook outputs (state trajectory, p_forced decomposition, daily P&L, clean-vs-degraded attribution)
- Optional: `data/outputs/lockport/runs/notebook3_<window>/state_trajectory.parquet` — daily state vector (gitignored)
- Optional: `data/outputs/lockport/runs/notebook3_<window>/daily_summary.parquet` — daily dispatch + P&L (gitignored)
- Stage 1 findings + decision log updates to this plan if any conventions change

---

## §12. Reference

- **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) §8 Phase I
- **Notebook 2 plan + notebook**: [`02_one_day_dispatch.md`](./02_one_day_dispatch.md), [`../../../../notebooks/02_one_day_dispatch.ipynb`](../../../../notebooks/02_one_day_dispatch.ipynb)
- **Understanding doc**: [`../../../extra/understanding_of_gas_turbine_digital_twin.md`](../../../extra/understanding_of_gas_turbine_digital_twin.md) §4 (daily feedback loop), §6 (state vector), §7 (endogenous forced outage)
- **Prototype implementation** (architectural reference): [`../../../extra/gas-turbine-digital-twin/EnggDTwin_model.py`](../../../extra/gas-turbine-digital-twin/EnggDTwin_model.py)
- **Step 2 plan** (broader execution blueprint): [`../../step_2_execution_blueprint_plan.md`](../../step_2_execution_blueprint_plan.md) §"Recursive Plant-State Input"
- **Status taxonomy**: [`../../../assumptions/status_taxonomy.md`](../../../assumptions/status_taxonomy.md)
- **Caveats**: [`../../../../data/assets/lockport/caveats.md`](../../../../data/assets/lockport/caveats.md) §2 (cogen markup), §7 (ambient sensitivity)
- **LTSA placeholder caveats**: [`../../../assumptions/placeholder_caveats.md`](../../../assumptions/placeholder_caveats.md) §1, §3
- **ADR-001** (gas hub): [`../../../decisions/001-gas-hub-treatment-v1.md`](../../../decisions/001-gas-hub-treatment-v1.md)

---

## §13. Suggested execution sequence

When ready to build the notebook:

1. **Write `notebooks/03_daily_loop_feedback.py`** following §3 cell-by-cell sketch
2. **Run as Python script** to verify execution end-to-end
3. **Convert to `.ipynb`** via `jupytext --to ipynb 03_daily_loop_feedback.py`
4. **Execute with nbclient** to embed outputs (including plots)
5. **Visual review of plots** — most important review step for N3. State trajectory should look like a clean accumulation curve; p_forced should rise sensibly; clean-vs-degraded gap should widen over the window.
6. **Update this plan** with findings if conventions changed
7. **Update consolidation plan §13 status log** with Phase I completion + observed scale of state evolution + loss_degradation
8. **Write Notebook 4 plan** informed by Notebook 3's findings — especially the constants calibration question, mode-preference flip question, and plot template choices
