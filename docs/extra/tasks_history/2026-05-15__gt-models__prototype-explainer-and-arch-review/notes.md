# Implementation Notes — Prototype Explainer + Arch Review

## Chronological session log

### Phase 1 — Clone the prototype repo (got it wrong twice, then right)

User asked to clone `https://github.com/aamani-ai/gas-turbine-digital-twin.git` "under the extra folder."

**First attempt** (incorrect): ran `ls` only at the repo root, didn't see `extra/`, created `extra/` at top level, cloned there.

**User correction**: pointed out `docs/extra/` already existed; gave strong feedback "never give a shallow answer if you haven't done a deep analysis." Saved this as a feedback memory.

**Second attempt**: removed wrong top-level folder, cloned into `docs/extra/gas-turbine-digital-twin/`. Verified contents.

**Third correction**: user said the `sdeshp0/gas-turbine-digital-twin.git` fork is more updated. Removed and re-cloned from sdeshp0. Final commit on cloned repo: `c31c5e8` (2026-05-08).

### Phase 2 — Deep read of the prototype

Read in parallel:
- `EnggDTwin_model.py` (251 lines — engineering library, state vector, stress accumulators, P_forced)
- `dispatch_model.py` (567 lines — daily driver, hourly heuristic, calendar maintenance, three modes)
- `LTSAContract.py` (284 lines — contract parameters, 7 cost streams, OEM/owner coverage classification)
- `InfraSure_ModelingFramework_V2.md` (~29K tokens — read in two chunks; the framework spec)
- Plus `backcast_comparison.py`, `sensitivity_analysis.py`, `generate_dummy_data.py` (support scripts)

Key understanding consolidated:
- Tri-layer architecture: engineering twin (stateful library) ← dispatch engine (heuristic) ← LTSA wrapper (financial)
- Daily feedback loop: state → dispatch → stress update → contract events
- Twin dispatch trick: each day runs hourly_dispatch twice (clean vs degraded HR) for loss attribution
- Three policy modes A/B/C with EOH-proximity wear penalty
- Calendar shoulder-snap maintenance with hard-stop overage
- Endogenous P_forced from state (not static FOR)
- TBC Weibull threshold sampled per path (genuine path heterogeneity)

### Phase 3 — Wrote the explainer doc

Asked the user three clarifying questions via `AskUserQuestion` to pin depth, audience, and critique framing. Picked: reader's-guide depth + internal-team audience + frank critical assessment.

Wrote `docs/extra/understanding_of_gas_turbine_digital_twin.md` in one pass: 18 sections, ~400 lines, file:line references throughout.

### Phase 4 — Follow-up on modes-as-optimization

User asked "does this allow optimization for max profit vs min LTSA?" Answered: no, modes are heuristic policies; three levels of capability the architecture supports (mode comparison today, parametric sweep cheap, true MIP/LP missing). User asked to add this to the doc — created §5.1 as a subsection.

### Phase 5 — Read the Lockport v1 build cold

System reminder loaded the latest `architecture.md` (706 lines) and notebooks folder listing. Read all four notebooks in full (3,344 lines total: N1=770, N2=583, N3=1,025, N4=1,966) and the latest model_card at `data/outputs/lockport/runs/notebook4_20260515_002901/model_card.md`.

### Phase 6 — Internal consistency assessment

Produced an assessment confirming the arch doc faithfully describes the code. Surfaced six things to push on:
1. Net P&L $-200M with LTSA dwarfing spark 14× (structural, not just placeholder)
2. HR-guarantee proxy systematically broken
3. Mode A beats B and C (opposite of Athens prototype headline)
4. N3 buggy aging formula not backported
5. Hardcoded constants that should be in YAML
6. Over-commitment cascade inflates dispatch-proportional costs

### Phase 7 — Q&A walkthrough on basics

User explicitly asked to "start with basics" rather than launching into the questions list. Sequence:

1. **Twin dispatch + RGGI** — explained the two dispatches per day (clean reference + degraded actual) and what RGGI is (Regional Greenhouse Gas Initiative cap-and-trade in 11–12 Northeast states, ~$1/MMBtu fuel-side adder).

2. **How §5.3 formulas change per mode** — pulled apart the dual meaning of "mode" (policy mode A/B/C vs operating mode 3×CC/2×CC/1×CC). Showed concrete worked example with LMP=$50, gas=$4 delivered: 3×CC spark = $13/MWh, 2×CC = $10/MWh, 1×CC = $7/MWh; cold-start wear hurdle differs by policy mode (A: $5.53/MWh, B up to $13.83, C up to $22.13).

3. **What is MI** — Major Inspection. Covered the CI/MI taxonomy, state resets, and discovered the **CI scheduler bug** while explaining the inspection-events plot (see "Findings" section below).

4. **Why cumulative spark margin is mostly negative** — five compounding causes: must-run cogen on coldest 20%, 2×CC structurally locked out of heuristic, historical 2017–2024 conditions, cold-start warming gas, over-commitment 2.4×.

5. **Confirming mode independence** — each policy mode runs `run_mode()` independently with its own PlantState, LTSA accumulators, schedule, RNG. They share only inputs + seed.

6. **Twin dispatch inside policy modes** — confirmed yes; built the three-level execution-nesting tree.

7. **Adding §5.8 to architecture.md** — at user's request, added the ASCII tree as a permanent section.

8. **Quick RGGI refresher** at session end.

## Commands used

```bash
# Clone prototype (final, correct location)
mkdir -p /Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra
rm -rf /Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/gas-turbine-digital-twin
git clone https://github.com/sdeshp0/gas-turbine-digital-twin.git \
    /Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/gas-turbine-digital-twin

# Verify clone
git -C /Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/gas-turbine-digital-twin \
    log -1 --format="%h %ai %s"
# → c31c5e8 2026-05-08 14:48:51 -0400 small fix to charts_inputs.py to make it runnable

# Confirm latest model_card exists
ls /Users/divy/code/work/infrasure_git_codes/gt_models/data/outputs/lockport/runs/

# Confirm LTSA YAML thresholds (for CI bug diagnosis)
grep -A 3 "eoh_threshold\|inspection_ci\|inspection_mi" \
    /Users/divy/code/work/infrasure_git_codes/gt_models/data/assets/lockport/ltsa_terms.yaml

# Create task-doc folder
mkdir -p /Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review
```

## Findings — the six items that need follow-up

### Finding 1: CI scheduler bug — CI events never fire

**Symptom**: model_card shows `CI events: $0.00M` across all three modes; only one MI event fires per mode in the 9-year horizon. Visually obvious in the inspection-events Gantt plot (no orange CI bars anywhere, only red MI bars at the end of 2025/early 2026).

**Diagnosis** (traced step-by-step during the Q&A):

YAML values in `data/assets/lockport/ltsa_terms.yaml`:
```yaml
inspection_ci:
  eoh_threshold:
    value: 24000
    status: placeholder
inspection_mi:
  eoh_threshold:
    value: 48000
    status: placeholder
```

Code in [N4:467-475](../../../../notebooks/04_full_path_mode_comparison.py#L467-L475):
```python
next_ci = ((int(cur_eoh) // CI_EOH_INTERVAL) + 1) * CI_EOH_INTERVAL
next_mi = ((int(cur_eoh) // MI_EOH_INTERVAL) + 1) * MI_EOH_INTERVAL
if next_mi <= next_ci:
    event_type = "MI"
    target_eoh = next_mi
else:
    event_type = "CI"
    target_eoh = next_ci
```

Math with `cur_eoh = 24000`:
- `next_ci = ((24000//24000) + 1) × 24000 = 2 × 24000 = 48000`
- `next_mi = ((24000//48000) + 1) × 48000 = 1 × 48000 = 48000`
- Tie at 48,000 → tie-breaker `<=` hands it to MI
- CI never gets picked
- After MI fires at 48K and EOH bumps to ~49–51K, next CI is at 72K, next MI at 96K — neither reached in 9 years

**Root cause is two bugs stacking**:

(a) The YAML field is named `eoh_threshold` but the scheduler uses it as an *interval* between events. The Athens-prototype framework (§4.4.2 of `InfraSure_ModelingFramework_V2.md`) had cumulative thresholds — CI at 32K, second CI at 40K, MI at 48K. The Lockport placeholder YAML simplified that into single "threshold" values that only make sense as intervals.

(b) The scheduler's `next = ((cur // interval) + 1) × interval` computes the next periodic multiple, which ignores any starting offset. So a 24K interval and a 48K interval, both evaluated from cur=24K, both produce 48K as the next event.

**Fix path (two sub-decisions for next session)**:

1. **Decide YAML semantics**: switch to the Athens-style sequence (e.g. `inspection_ci.sequence = [32000, 40000]`, `inspection_mi.sequence = [48000, 96000, ...]`), OR keep "interval" semantics but rename the YAML field to `eoh_interval` and set CI interval to something like 8,000–16,000 so CIs land between MIs.

2. **Update the scheduler** to either consume a sequence (option 1) or use `next = last_event_eoh + interval` (option 2).

**Downstream impact of the fix**: introduces 2+ CI events in 9 years at $937K owner-uncovered each → ~$2M additional LTSA owner cost; changes inspection cadence which affects state resets, which cascades into HR penalty timing, forced-outage probabilities.

### Finding 2: HR-guarantee proxy is structurally biased

**Symptom**: HR penalty contributes $31.94M (14.6%) of total LTSA in Mode A — disproportionate share.

**Diagnosis**: [N4:298](../../../../notebooks/04_full_path_mode_comparison.py#L298) sets `HR_GUARANTEE_BTU_PER_KWH = HR_3xCC` (the 3×CC clean HR = 8,901 BTU/kWh). Lockport actually operates in 1×CC ~26% of fired hours per the backtest, and 1×CC HR is 10,424 — that's a structural 17% gap, way above the 2% tolerance. So the HR penalty fires every inspection cycle by construction, regardless of degradation. The proxy isn't measuring "did we degrade beyond 2%" — it's measuring "did we ever run in a non-3×CC mode."

**Fix path**:
- Wait for data-room extraction to get the actual HR guarantee (per `ltsa_terms.yaml` validation_path)
- Or change the proxy to a load-weighted blend of mode HRs (acknowledging that real CSAs typically guarantee HR at design conditions only)
- Acknowledged in model card caveats but the *mechanism* is not documented

### Finding 3: 2×CC operating mode is locked out of the dispatch heuristic

**Symptom**: model dispatches 0% in 2×CC vs MOR's actual 26%. Headline backtest divergence.

**Diagnosis**: The mode-choice loop at [N4:599-610](../../../../notebooks/04_full_path_mode_comparison.py#L599-L610) picks the mode with highest `max(spark, 0) × capacity`. Break-even LMPs:

| Mode | Break-even LMP | Capacity |
| :--- | ---: | ---: |
| 3×CC | $37/MWh | 221 MW |
| 2×CC | $40/MWh | 173 MW |
| 1×CC | $43/MWh | 124 MW |

When LMP > $43, all three are positive — but 3×CC wins because lower fuel cost AND bigger capacity. When LMP < $37, all three negative → offline. The narrow "2×CC-only" window (LMP $40–$43) almost never gets picked because 3×CC's small positive margin × 221 MW beats 2×CC's tiny positive margin × 173 MW.

**Fix path**:
- Add a per-CT availability layer (would let "1 CT down" → 2×CC become natural)
- Add a tiered priority that picks the smallest mode with positive margin above a threshold (heuristic)
- Add a stochastic perturbation around mode capacity to break ties statistically
- Real fix is per-generator state (block-level state is the deeper limitation; documented in arch doc §7.3 / §7.5 as v2 work)

### Finding 4: Cogen must-run on coldest 20% is the largest negative-cumulative driver

**Symptom**: cumulative spark margin is $-5M to $-12M for most of 2017–2024; only recovers to positive in 2025.

**Diagnosis**: [N4:921-924](../../../../notebooks/04_full_path_mode_comparison.py#L921-L924) forces 1×CC dispatch on the coldest 20% of days (657 days over 9 years). On a typical winter must-run day with LMP=$30, gas=$4 delivered:
```
spark = $30 - (10.424 × $4) - $1.38 = $30 - $43.08 = -$13.08/MWh
loss = -$13.08 × 123.9 MW × 24 hr ≈ -$39K per must-run day
657 days × ~$30K avg = ~$20M cumulative forced losses
```

That's most of the negativity.

**Fix path**:
- Extract real MOR DHTS daily data from `data/paths/lockport/mor_daily.parquet` (already available — `dhts_net_thermal_mmbtu` column per prior session's handoff §C)
- Replace the temp-proxy must-run flag with real per-day steam-demand obligation
- Acknowledged in arch doc §7.3 as v2 work

### Finding 5: N3 still has the buggy aging-multiplier formula

**Symptom**: [N3:684](../../../../notebooks/03_daily_loop_feedback.py#L684) calls `p_forced_components(state, year_frac=day_idx/365.0)`. N4 fixed this to `years_elapsed = day_idx/365.0` with `aging_frac = min(years_elapsed/10, 1.0)` capping at 1.0.

**Status**: arch doc §7.6 explicitly flags "backport this fix into N3 (or document why N3's short horizon makes it moot)" as an action item. Hasn't been done.

**Diagnosis**: Over N3's 30-day window the bug is invisible (year_frac < 0.1). Over a 9-year window it compounds to 5.5× when it should cap at 1.5×. Anyone re-running N3 with a wider window would get bad numbers silently.

**Fix path**: 5-minute edit to [N3:684](../../../../notebooks/03_daily_loop_feedback.py#L684) and the `p_forced_components` function signature in N3 to match N4's pattern.

### Finding 6: Hardcoded constants that should live in YAML

These constants are buried in code and behave like settings:

| Constant | Where | Should live in |
| :--- | :--- | :--- |
| `COGEN_VOM_MARKUP = 1.35` | N3, N4 | `operating_profile.yaml.cogen_vom_markup` |
| `MIN_RUN_HOURS_FOR_AMORTIZATION = 6.0` | N4:219 | `tech_class_defaults` or `operating_profile.yaml` |
| `GT_WEAR_FRACTION_OF_START = 0.42` | N4:213 | `tech_class_defaults.gt_wear_fraction` |
| `EOH_RATE_ESTIMATE_PER_DAY = 8.0` | N4:224 | derived per-asset from historical observed dispatch |

Note: The Bucket B engineering constants (`FATIGUE_PER_*_START`, `FOULING_*`, `TBC_WEIBULL_*`, etc.) are already flagged for ADR-002 / Phase L sweeps — those are not this finding.

## Minor items not promoted to "findings"

These came up during the review but don't warrant a code change:

- **Arch doc terminology**: §5.7 says "7 LTSA streams" but actually 8 (parenthetical "7 above + forced outage" is the giveaway). Cosmetic; pick a label.
- **N3 `update_stress` unused param**: takes `avg_temp_f` but doesn't use it. N4 dropped this cleanly. Cosmetic.

## Key insights worth carrying forward

1. **The "mode" word's dual meaning is a real source of confusion.** §5.8 now documents this; future docs and code comments should be careful to specify "policy mode" vs "operating mode."

2. **All three policy modes are identical until late 2024** (in this run). EOH headroom doesn't drop below 4,000 until then, so `wear_penalty_mult` returns 1.0 for all modes. Mode B/C only diverge from A in the final ~12 months. Visible directly in the cumulative spark margin plot (single line until 2025, three lines after).

3. **The twin dispatch's loss attribution isolates degradation cost only.** It does NOT isolate policy cost — the wear penalty is held constant between the clean and degraded dispatches. Policy cost is captured cross-mode (A vs B vs C cumulative margins), not within-day. Worth noting if future model_card output decomposes "where did the cost go" further.

4. **The model's headline numbers are structurally honest within their assumptions.** The $-200M Net P&L isn't a bug; it's `(placeholder LTSA at Athens values) + (over-committed dispatch driving inflated wear) + (must-run forcing losses) + (HR proxy guaranteeing penalty)`. Each cause is documented. The model is consistent with what it's told to do — the question is whether what it's told reflects Lockport reality.

5. **Lockport's actual operating economics must be positive on average** (survivorship anchor from prior session's `pnl_ledger.md §4`). The model's $-200M result reflects modeling artifacts, not reality. The fix path is the items in `gaps_and_priorities.md` and the findings above — not a tuning exercise.

## Verification (post-session checklist)

To verify this session's deliverables are intact:

```bash
cd /Users/divy/code/work/infrasure_git_codes/gt_models

# Prototype clone present
ls docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py

# Explainer doc present
wc -l docs/extra/understanding_of_gas_turbine_digital_twin.md
# → ~400 lines

# §5.8 in architecture doc
grep -n "§5.8 Execution nesting" docs/methodology/architecture.md
# → should find one match

# Memory files exist
ls ~/.claude/projects/-Users-divy-code-work-infrasure-git-codes-gt-models/memory/

# Task docs present
ls docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/

# Git status — should show only this task-docs folder as untracked + a pre-existing .ipynb modification
# (the deliverables — prototype clone, explainer doc, §5.8 edit — were committed mid-session)
git status
```

To re-verify any of the findings:

```bash
# Finding 1 (CI scheduler bug): confirm the math
python3 -c "
ci_int, mi_int, cur = 24000, 48000, 24000
next_ci = ((cur // ci_int) + 1) * ci_int
next_mi = ((cur // mi_int) + 1) * mi_int
print(f'next_ci={next_ci}, next_mi={next_mi}, tie={next_mi<=next_ci} → MI wins')
"

# Finding 2 (HR proxy): grep for the assignment
grep -n "HR_GUARANTEE_BTU_PER_KWH" notebooks/04_full_path_mode_comparison.py

# Finding 5 (N3 aging bug): compare to N4
grep -n "year_frac\|years_elapsed" notebooks/0{3,4}_*.py
```
