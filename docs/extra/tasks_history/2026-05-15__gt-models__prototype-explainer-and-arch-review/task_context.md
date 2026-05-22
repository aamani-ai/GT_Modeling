# Task Context — gt_models Prototype Explainer + v1 Architecture Review

## Objective

Two-part documentation session: (1) clone the cousin "InfraSure GT Digital Twin" prototype repo as a reference and write a comprehensive reader's guide explaining what it is and how it works; (2) review the Lockport v1 build (architecture doc + 4 notebooks + latest model_card output) for internal consistency and surface findings that need follow-up.

## Background

After the v1 Lockport build shipped (per the prior task doc `2026-05-15__gt-models__v1-lockport-shipped`), the user wanted to anchor the Lockport build against the source-of-truth prototype that informed its conventions. The prototype lives in a separate repo (`sdeshp0/gas-turbine-digital-twin.git`). Although it had been referenced across the gt_models docs (in particular `docs/methodology/architecture.md` §3.4 calls it out), it had never been:

- Cloned into the repo as a navigable reference
- Explained in plain English with file:line pointers
- Cross-checked against the Lockport implementation for consistency

The session also surfaced several substantive findings about the Lockport v1 build that hadn't been captured anywhere persistent.

## Problems encountered

1. **Initially cloned the wrong prototype repo** (`aamani-ai/gas-turbine-digital-twin.git`) and to the wrong location (top-level `extra/` instead of `docs/extra/`). User caught this with strong "no shallow answers" feedback. Corrected to clone `sdeshp0/gas-turbine-digital-twin.git` into `docs/extra/gas-turbine-digital-twin/`.

2. **Identified a real bug in the inspection scheduler**: CI events never fire in any of the three policy modes across the 9-year horizon. Root cause is a two-part issue — the YAML field `eoh_threshold` is used as an interval rather than as a threshold value, and the scheduler's `next = ((cur // interval) + 1) × interval` formula produces equal next-events for CI (interval 24,000) and MI (interval 48,000) from the starting EOH of 24,000. The tie-breaker `if next_mi <= next_ci` hands the event to MI. Result: zero CI events, one MI event per mode in 9 years.

3. **HR-guarantee proxy is structurally biased**: `HR_GUARANTEE_BTU_PER_KWH = HR_3xCC` (the 3×CC clean HR of 8,901). Lockport actually operates in 1×CC ~26% of fired hours, and 1×CC has HR of 10,424 — that's 17% above the guarantee, far past the 2% tolerance. So the HR penalty fires every inspection cycle by construction, contributing $31.94M (14.6% of LTSA) regardless of any real degradation.

4. **Cumulative spark margin is negative for most of the 9-year horizon** (~$5–12M negative until 2025). Compound cause: cogen must-run flag forces 1×CC dispatch on the coldest 20% of days at structural losses (~$20M cumulative); the dispatch heuristic structurally locks out 2×CC (which is why backtest shows 0% 2×CC vs MOR's 26%); over-commitment 2.4× amplifies all loss-making hours.

5. **N3 still has the buggy aging-multiplier formula** that N4 fixed. Arch doc §7.6 flagged "backport this fix into N3" but it hadn't been done. [N3:684](../../../../notebooks/03_daily_loop_feedback.py#L684) still uses `year_frac = day_idx / 365.0`.

6. **Terminology confusion in arch doc**: §5.3 uses "per mode" without disambiguating *policy mode* (A/B/C) from *operating mode* (3×CC/2×CC/1×CC). Both meanings appear in the same formulas — `HR_btu_per_kwh` and `mode_capacity_mw` are operating-mode parameters; `wear_penalty` is parameterized by policy mode.

## What we did

1. Cloned `sdeshp0/gas-turbine-digital-twin.git` into [docs/extra/gas-turbine-digital-twin/](../../gas-turbine-digital-twin/).

2. Wrote [docs/extra/understanding_of_gas_turbine_digital_twin.md](../../understanding_of_gas_turbine_digital_twin.md) — an 18-section reader's guide:
   - §1–2: What this repo is + why it's "more than dispatch"
   - §3: The three layers (engineering / dispatch / LTSA) with file:line pointers per function
   - §4: Daily feedback loop (11-step order of operations)
   - §5: Three dispatch modes + §5.1 modes-as-optimization clarification (added on follow-up question)
   - §6–9: State vector, endogenous forced outage, calendar maintenance, LTSA cost taxonomy
   - §10–13: I/O, how to run, backcast validation, sensitivity findings
   - §14: What it achieves without OEM data
   - §15: Critical assessment (solid / prototype / genuinely missing)
   - §16–17: Position in InfraSure pipeline + open questions
   - §18: Glossary

3. Read the Lockport v1 build cold and produced an internal-consistency assessment:
   - `docs/methodology/architecture.md` (706 lines)
   - All 4 notebook `.py` files (3,344 lines total)
   - Latest N4 model_card at `data/outputs/lockport/runs/notebook4_20260515_002901/`
   - Confirmed the arch doc faithfully describes the code; surfaced 6 substantive findings (above).

4. Q&A walkthrough on basics with the user (per their pedagogical request "let me start with basics"):
   - What is twin dispatch + RGGI
   - How §5.3 formulas change per mode (operating mode vs policy mode disambiguation)
   - What is MI (and discovered the CI scheduler bug while explaining the plot)
   - Why cumulative spark margin is mostly negative
   - Confirmed each policy mode runs independently
   - Confirmed twin dispatch fires every day inside each policy mode

5. Added §5.8 "Execution nesting — how the simulation actually runs" to `docs/methodology/architecture.md` with:
   - The three-level ASCII tree (policy modes → daily loop → twin dispatch → hourly 3-operating-mode pick)
   - A "Note on the word 'mode'" callout disambiguating policy vs operating mode
   - File:line link to N4:1143-1155 (state commit logic)
   - Evaluation-count flavor stat (~473K per mode, ~1.42M total, ~50s wall-clock)

## Files touched

### Created

```
docs/extra/gas-turbine-digital-twin/                                    # cloned sdeshp0 fork (14 files)
docs/extra/understanding_of_gas_turbine_digital_twin.md                 # 18-section reader's guide
docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/
    ├── task_context.md                                                 # THIS file
    ├── decisions.md
    ├── notes.md
    └── handoff.md
```

### Modified

```
docs/methodology/architecture.md                                        # +§5.8 Execution nesting
```

### Memory (persistent across sessions, at `~/.claude/projects/-Users-divy-code-work-infrasure-git-codes-gt-models/memory/`)

```
feedback_no_shallow_answers.md                                          # always search recursively before assuming a folder doesn't exist
project_gt_digital_twin.md                                              # Athens pilot context + the engineering-twin-as-bridge framing
MEMORY.md                                                                # index — 2 entries
```

### Not yet on disk (in-conversation findings)

The 6 findings in "Problems encountered" above exist in this task doc + the conversation transcript but have **not yet** been:
- Turned into code fixes
- Documented as ADRs
- Filed as GitHub issues
- Added as caveats to model_card or methodology docs

That's the explicit handoff to the next session.

## Current status

- [x] Prototype repo cloned at correct location (`docs/extra/gas-turbine-digital-twin/`)
- [x] Reader's-guide explainer doc complete (18 sections + §5.1 supplement)
- [x] Lockport v1 build read cold (arch doc + 4 notebooks + model_card)
- [x] Internal consistency confirmed
- [x] §5.8 Execution nesting added to architecture.md
- [x] Memory files updated
- [x] Task documentation written (this folder)
- [x] **Deliverables already at git HEAD** — prototype clone, explainer doc, and §5.8 edit are committed (verified via `git ls-files`). Only the task-docs folder itself is uncommitted at session end.
- [ ] **Findings not yet propagated**: 6 substantive findings captured here but not turned into code fixes or ADRs
- [ ] **Pending commit**: this task-docs folder + (eventually) the Phase A/B/C/D fixes from [handoff.md](handoff.md)

## Next steps (proposed priority)

1. **Fix the CI scheduler bug** so CI events actually fire (single biggest model-realism win — see [decisions.md](decisions.md) §1 and [notes.md](notes.md) §CI-scheduler-bug for the diagnosis and fix path)
2. **Backport the N3 aging-formula fix** (small change; listed as action item in arch doc §7.6 but unaddressed)
3. **Decide ADR vs caveat** for the 2×CC dispatch-heuristic lockout (it's the real cause of the 26%→0% backtest divergence)
4. **Decide whether to relax the must-run-on-coldest-20% rule** (currently driving ~$20M of forced losses; real Lockport probably has flexibility)
5. **Commit + push** the explainer doc + arch doc edit once findings are triaged
