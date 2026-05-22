# Handoff — Prototype Explainer + Architecture Review (2026-05-15)

> **The 60-second summary**: Cloned the InfraSure GT Digital Twin prototype repo from `sdeshp0/gas-turbine-digital-twin.git` into [docs/extra/gas-turbine-digital-twin/](../../gas-turbine-digital-twin/). Wrote a comprehensive 18-section reader's guide at [docs/extra/understanding_of_gas_turbine_digital_twin.md](../../understanding_of_gas_turbine_digital_twin.md) (~400 lines). Read the Lockport v1 build cold (arch doc + 4 notebooks + latest model_card) and surfaced **6 substantive findings** — including a real bug where CI inspection events never fire. Added §5.8 "Execution nesting" to [docs/methodology/architecture.md](../../../methodology/architecture.md). **The deliverables (prototype clone, explainer doc, §5.8 edit) are already at git HEAD — committed mid-session. Only this task-docs folder is uncommitted at session end. Findings still need triage in next session before any code fixes ship.**

---

## 10-bullet summary

1. **Cloned `sdeshp0/gas-turbine-digital-twin.git`** into `docs/extra/gas-turbine-digital-twin/` (replacing an earlier wrong clone from the `aamani-ai` fork). Latest commit `c31c5e8` (2026-05-08). Lesson: always recursively search before assuming a folder doesn't exist (saved as `feedback_no_shallow_answers.md` memory).
2. **Wrote `docs/extra/understanding_of_gas_turbine_digital_twin.md`** — 18 sections, ~400 lines, reader's-guide depth, internal-team audience, includes critical assessment of what's solid / prototype / genuinely missing. File:line pointers throughout.
3. **Added §5.1 to the explainer** clarifying that modes A/B/C are heuristic policies (not optimization) and laying out the three levels of capability the architecture supports: mode comparison (today), parametric sweep (cheap next step), true MIP/LP optimization (genuinely missing — the planned next phase).
4. **Read Lockport v1 cold** — `docs/methodology/architecture.md` (706 lines), all 4 notebooks (N1=770, N2=583, N3=1025, N4=1966 lines), and the latest model_card at `data/outputs/lockport/runs/notebook4_20260515_002901/`. Confirmed the architecture doc faithfully describes the code.
5. **Found a real bug: CI inspection events never fire.** YAML `eoh_threshold` values (24K for CI, 48K for MI) are used as intervals; the scheduler's periodic-multiple formula produces a tie at 48,000 EOH from the starting 24,000; the `<=` tie-breaker hands every event to MI. Net effect: zero CI events, one MI per mode in 9 years. Full diagnosis + fix path in [notes.md](notes.md) §Finding-1.
6. **Surfaced 5 more findings**: HR-guarantee proxy is structurally biased (drives $32M of LTSA by construction), 2×CC operating mode is locked out of the dispatch heuristic (explains 0% vs MOR's 26%), cogen must-run on coldest 20% drives ~$20M of forced losses (the largest negative-cumulative driver), N3 still has the buggy aging-multiplier formula that N4 fixed, several constants are hardcoded that should live in YAML/tech_defaults.
7. **Q&A walkthrough on basics** (user's pedagogical preference): twin dispatch + RGGI + how §5.3 formulas change per mode + what is MI + why cumulative is negative + mode-independence confirmation. The walkthrough surfaced Finding 1 (CI scheduler) and disambiguated the dual-meaning of "mode" (policy vs operating).
8. **Added §5.8 "Execution nesting" to `architecture.md`** with the three-level ASCII tree (policy modes → daily loop → twin dispatch → hourly 3-operating-mode pick), a callout box disambiguating policy mode vs operating mode, and the evaluation-count flavor stat (~1.42M mode-margin checks total, ~50s wall-clock).
9. **Saved 2 memory files**: `feedback_no_shallow_answers.md` (always search recursively before assuming) and `project_gt_digital_twin.md` (the engineering-twin-as-bridge framing — *the value of this framework is being the bridge between pure dispatch and pure financial, with the engineering twin as the missing middleware; modes A/B/C are heuristic policies, not joint NPV optimization*).
10. **Most deliverables are already at git HEAD.** The prototype clone, the explainer doc, and the §5.8 arch-doc edit were committed mid-session (verified via `git ls-files docs/extra/`). Only this task-docs folder is uncommitted at session end. The 6 findings (especially the CI scheduler bug) have NOT been turned into code changes — those are next-session work.

---

## Files touched (quick map)

### Created (in this session)
```
docs/extra/gas-turbine-digital-twin/                                    # cloned from sdeshp0 fork (14 files)
docs/extra/understanding_of_gas_turbine_digital_twin.md                 # 18-section reader's guide (+§5.1)
docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/
    ├── task_context.md
    ├── decisions.md
    ├── notes.md
    └── handoff.md                                                      # THIS file
```

### Modified (in this session)
```
docs/methodology/architecture.md                                        # +§5.8 Execution nesting (with ASCII tree + mode-word callout)
```

### Memory (persistent across sessions)
```
~/.claude/projects/-Users-divy-code-work-infrasure-git-codes-gt-models/memory/
    ├── feedback_no_shallow_answers.md                                  # NEW — search recursively before assuming
    ├── project_gt_digital_twin.md                                      # NEW — Athens pilot + bridge framing
    └── MEMORY.md                                                       # updated index (2 entries)
```

### Read but not modified
```
docs/methodology/architecture.md                                        # 706 lines
notebooks/0{1,2,3,4}_*.py                                              # 3,344 lines total
data/outputs/lockport/runs/notebook4_20260515_002901/model_card.md     # latest run output
data/assets/lockport/ltsa_terms.yaml                                    # confirmed CI/MI threshold values
docs/extra/gas-turbine-digital-twin/*.py                                # ~2,000 lines of prototype code
docs/extra/gas-turbine-digital-twin/InfraSure_ModelingFramework_V2.md   # ~29K tokens — read in chunks
```

---

## Repro commands

```bash
# Open repo
cd /Users/divy/code/work/infrasure_git_codes/gt_models
pwd

# Verify session deliverables
ls docs/extra/gas-turbine-digital-twin/                                 # prototype clone
wc -l docs/extra/understanding_of_gas_turbine_digital_twin.md           # ~400 lines
grep -n "§5.8 Execution nesting" docs/methodology/architecture.md       # 1 match

# View task docs
ls docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/

# Confirm working tree state
git status

# Re-verify the CI scheduler bug
python3 -c "
ci_int, mi_int, cur = 24000, 48000, 24000
next_ci = ((cur // ci_int) + 1) * ci_int
next_mi = ((cur // mi_int) + 1) * mi_int
print(f'next_ci={next_ci}, next_mi={next_mi}, tie={next_mi<=next_ci} → MI wins')
"

# Latest model_card (the baseline this review is anchored against)
cat data/outputs/lockport/runs/notebook4_20260515_002901/model_card.md | head -60
```

---

## Next session: execution roadmap

### Phase 0 — Read this first (5 min)

Before starting work:

1. `CLAUDE.md` — project context, conventions, file paths, don'ts
2. **THIS handoff.md** — what was done this session
3. [notes.md](notes.md) — the 6 findings in full diagnostic detail (especially §Finding-1 for the CI scheduler bug)
4. [decisions.md](decisions.md) — particularly §9 (why CI bug was documented not fixed) and §10 (why nothing committed)

### Phase A — Highest-value next work: fix the CI scheduler bug

This is the single biggest model-realism improvement available right now. Currently $0 of CI cost gets attributed across all three modes in 9 years; with the fix, ~2 CI events fire per mode, adding ~$2M owner-uncovered LTSA cost per mode plus changing state-reset cadence (which cascades into HR penalty timing and forced-outage probabilities). See [notes.md §Finding-1](notes.md) for the full diagnosis.

The fix has **two sub-decisions** that need user direction:

1. **YAML field semantics**: should `eoh_threshold` mean *interval between events* (current code usage) or *cumulative threshold value* (what the Athens framework intended — CI at 32K, 40K; MI at 48K)?

2. **Scheduler algorithm**: should the scheduler track `last_event_eoh` and compute `next = last + interval`, or move to a sequence-based design like `[32000, 40000]` for CI sequence and `[48000, 96000]` for MI?

**Recommended approach** (subject to user confirmation):

- Option (a) — sequence-based, Athens-faithful: edit `ltsa_terms.yaml` to use `inspection_ci.sequence: [32000, 40000]` and `inspection_mi.sequence: [48000, 96000]`. Edit `build_maint_schedule` in N4 to consume sequences. Minimal logic, easy to verify.
- Option (b) — interval-based, semantics-corrected: rename YAML field to `eoh_interval` (CI=8000, MI=24000 say). Edit `build_maint_schedule` to compute `next = last_event_eoh + interval`. Slightly more code change, but matches more LTSA contract structures.

Either way, after the fix:
1. Re-run N4 (`cd notebooks && MPLBACKEND=Agg python3 04_full_path_mode_comparison.py`)
2. Check `data/outputs/lockport/runs/notebook4_<new-ts>/model_card.md` — should now show 2 CI events per mode + 1 MI per mode
3. Compare new headline numbers to baseline (Mode A: spark $15.81M, LTSA $218.89M, Net P&L $-203.08M)
4. Document the resulting numbers in [notes.md](notes.md) under a new "post-fix" section, and update `data/assets/lockport/caveats.md` if the inspection schedule materially changed

### Phase B — Small cleanup: backport N3 aging-multiplier fix

5-minute change. See [notes.md §Finding-5](notes.md). Arch doc §7.6 flagged it as action item. Edit [notebooks/03_daily_loop_feedback.py](../../../../notebooks/03_daily_loop_feedback.py) line ~684:

```python
# OLD (buggy at wider windows):
year_frac = day_idx / 365.0
pf = p_forced_components(state, year_frac=year_frac)

# NEW (matches N4):
years_elapsed = day_idx / 365.0
# ... and inside p_forced_components, replace year_frac usage with:
#     aging_frac = min(years_elapsed / AGING_WINDOW_YEARS, 1.0)
```

Also update the `p_forced_components` function signature in N3 to match N4's pattern: `def p_forced_components(state, years_elapsed=0.0):` instead of `year_frac=0.1`.

### Phase C — ADR for the 2×CC dispatch-heuristic gap

The 0% vs 26% (MOR) 2×CC dispatch gap is a known limitation called out in arch doc §7.4 but never written up as an ADR. See [notes.md §Finding-3](notes.md). Decision worth documenting:

- Block-level state inherently can't model "1 CT down → 2×CC active"
- Even with full-availability block, the `max(spark,0) × capacity` heuristic structurally prefers 3×CC

ADR-003 framing options:
- *"Accept the 2×CC gap as v1 limitation; per-generator state is v2 (per consolidation plan §5 D4)"*
- *"Add tiered priority heuristic as v1 patch — 1 day of work, reduces backtest divergence"*

Recommend writing the ADR so future readers don't re-derive the diagnosis from scratch.

### Phase D — Decide what to do about the HR-guarantee proxy

See [notes.md §Finding-2](notes.md). The HR penalty contributing 14.6% of LTSA by construction (regardless of degradation) is misleading. Options:

1. **Wait for data-room extraction** — the real guarantee is in the LTSA contract. Lower-bound that's a v2 / Phase L item.
2. **Change the proxy to load-weighted blend** — `HR_GUARANTEE = (3xCC_share × HR_3xCC + 2xCC_share × HR_2xCC + 1xCC_share × HR_1xCC)`. Still a proxy but at least accounts for actual operating mix.
3. **Disable HR penalty in v1** with a caveat — if the real guarantee is unknown, $0 might be more honest than a structurally-biased number.

Recommend (2) as a v1 stopgap with caveat, (1) as v2 work pending data room.

### Phase E — Commit task docs + any Phase A/B/C/D fixes

The session's deliverables (prototype clone, explainer doc, §5.8 edit) are already committed. The remaining uncommitted item from this session is the task-docs folder itself. The natural next commit batch:

```bash
cd /Users/divy/code/work/infrasure_git_codes/gt_models && pwd
git status                                                              # confirm

# Stage task docs (this folder)
git add docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/

# Plus whatever was fixed in Phases A/B/C/D — e.g. for the CI scheduler fix:
# git add notebooks/04_full_path_mode_comparison.{py,ipynb}
# git add data/assets/lockport/ltsa_terms.yaml
# git add data/outputs/lockport/runs/notebook4_<new-ts>/   # if not gitignored

# Confirm SSH alias is the work account before push (per CLAUDE.md)
ssh -T git@github.com-work 2>&1 | head -1                              # → "Hi D-ivyy!"

# Commit
git commit -m "Add prototype-review task docs + <whatever else>"

# Then user-decides on push
```

Note: `notebooks/01_data_spine_load_validate.ipynb` shows as modified in `git status` but that pre-dates this session — not part of this session's work.

---

## Critical context / gotchas

### The CI scheduler bug is real, not cosmetic

It affects the headline model_card numbers. The diagnosis is correct (verified twice — once by tracing the math during the user Q&A, once by inspecting the actual YAML values via grep). The fix changes inspection cadence which cascades through state resets → HR penalty timing → forced-outage probabilities. Don't underestimate the downstream effect of the fix.

### The model_card numbers are NOT representative of reality

They are *structurally consistent with what the model is told to do*, but what it's told reflects:
- Placeholder LTSA values (Athens prototype defaults at ~2× Lockport-realistic levels)
- Missing revenue streams (steam, ICAP, ancillary)
- Over-commitment 2.4× vs MOR (driven by must-run + 2×CC lockout + no planned outages)
- HR proxy guaranteeing penalty by construction (Finding 2)
- CI scheduler never firing CI (Finding 1)

The arch doc and the prior session's `pnl_ledger.md §4` both call this out. Anyone reviewing the model should read those caveats first.

### Don't try to "fix" findings before the team weighs in

`CLAUDE.md`'s "Don'ts" section explicitly says: *"Don't try to 'fix' findings before team weighs in. Documented limitations (steam-only trigger conservative, Mode A/B/C late divergence, generic 2017 starting state) are v2 work — wait for direction."*

The CI scheduler bug is borderline — it's a *real bug* not a *documented limitation*, so a fix is justified. But the fix has design sub-decisions (sequence vs interval YAML semantics) that warrant user input. Don't autonomously commit to one design.

### Git push protocol unchanged from prior session

From prior session's handoff:
```bash
ssh -T git@github.com-work 2>&1 | head -1     # → "Hi D-ivyy!" (work account)
# Work repo: git@github.com-work:aamani-ai/GT_Modeling.git
# Always: cd /absolute/path && pwd && git ... in the SAME Bash call
```

The wrong-repo-push incident from the prior session is documented in `feedback_explicit_cd_for_git.md` memory.

### What IS available vs what needs work this session

| Available now | Needs work |
| :--- | :--- |
| Prototype reference code (cloned) | CI scheduler fix |
| Reader's-guide explainer doc | N3 aging-formula backport |
| §5.8 Execution nesting in arch doc | 2×CC ADR write-up |
| 6 findings documented in [notes.md](notes.md) | HR-guarantee proxy decision |
| Latest model_card at 2026-05-15 00:29:01 | Commit + push the session's work |
| Memory updated with bridge-framing context | Re-run N4 after any code fix |

---

## Files to consult before changes (additions since prior handoff)

| If changing... | Read first |
| :--- | :--- |
| Inspection scheduler logic | [notes.md §Finding-1](notes.md), `docs/extra/understanding_of_gas_turbine_digital_twin.md` §8, `architecture.md` §5.6 |
| HR penalty mechanics | [notes.md §Finding-2](notes.md), `LTSAContract.py.hr_penalty_cycle` (in `docs/extra/gas-turbine-digital-twin/`), `architecture.md` §5.7 |
| Dispatch heuristic / 2×CC | [notes.md §Finding-3](notes.md), `architecture.md` §5.3 + §7.4, `dispatch_mechanics.md` |
| Must-run cogen logic | [notes.md §Finding-4](notes.md), [notebooks/04_full_path_mode_comparison.py:921-924](../../../../notebooks/04_full_path_mode_comparison.py#L921-L924), `caveats.md` §3 |
| Aging formula in any notebook | [notes.md §Finding-5](notes.md), `architecture.md` §7.6 |
| Anything about modes (the word) | `architecture.md` §5.8 callout, `understanding_of_gas_turbine_digital_twin.md` §5 |

---

## Conversation summary (for context if needed)

The session followed a pedagogical arc:

1. **Repo cloning + first correction** — wrong fork, wrong path; user gave the "no shallow answers" feedback. Saved as memory.
2. **Deep prototype read** — read all the Python + framework MD; built mental model of tri-layer architecture.
3. **Discussion before writing** — confirmed framing ("more than a dispatch model — the engineering twin is the bridge"); refined the user's mental model ("modes aren't optimization, they're scenario comparison"); asked clarifying questions about depth/audience/critique.
4. **Wrote the explainer doc** — 18 sections in one pass.
5. **Follow-up: modes-as-optimization** — added §5.1 to the explainer.
6. **Pivot to v1 review** — user opened `architecture.md`, asked for assessment.
7. **Read v1 cold, surfaced 6 findings** — the assessment included internal-consistency confirmation + 6 push-on items.
8. **Q&A on basics** — twin dispatch + RGGI + per-mode formulas + MI + why cumulative is negative + mode independence. During the MI explanation, discovered the CI scheduler bug.
9. **Added §5.8 to arch doc** — at user's request, captured the three-level execution-nesting tree.
10. **Quick RGGI refresher** — user circled back to make sure they had it.
11. **Recap + task-docs creation** — this folder.

User's recurring patterns (consistent with prior session's handoff):
- **Honest analysis preferred over polished claims** — pushed back when I would have been less direct
- **Start with basics, build up** — explicit pedagogical preference
- **Be wrong out loud, then correct** — used the "no shallow answers" feedback constructively (better to surface the failure mode than hide it)
- **Documentation discipline** — the request to capture the §5.8 ASCII tree, then to capture the whole session as task docs, both reflect the "document what you learned" pattern

User's preferences (consistent):
- Take time, get it right
- Plot/diagram when visualization helps
- Document limitations clearly; don't hide them
- Always pull receipts (file:line, commands, values from YAML)

---

## Final state at session end

```
Repo: gt_models (local at /Users/divy/code/work/infrasure_git_codes/gt_models)
Remote: https://github.com/aamani-ai/GT_Modeling (work account D-ivyy via github.com-work SSH)
Branch: main

Already at git HEAD (committed mid-session):
    - docs/extra/gas-turbine-digital-twin/  (prototype clone, tracked except its own .git/)
    - docs/extra/understanding_of_gas_turbine_digital_twin.md
    - docs/methodology/architecture.md (with §5.8 added)

Still uncommitted (session-end):
    - docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/
    - notebooks/01_data_spine_load_validate.ipynb (M — pre-dates this session)

Tests: not run this session (no code changes made)
Latest model_card baseline: data/outputs/lockport/runs/notebook4_20260515_002901/
Memory: 2 entries (feedback_no_shallow_answers + project_gt_digital_twin)

6 findings open for next session:
  1. CI scheduler bug — CI never fires (HIGHEST PRIORITY)
  2. HR-guarantee proxy structurally biased
  3. 2×CC operating mode locked out of dispatch heuristic
  4. Cogen must-run on coldest 20% too aggressive
  5. N3 aging-formula fix not backported
  6. Hardcoded constants that should live in YAML/tech_defaults

Next: commit task docs → triage findings → fix CI scheduler → re-run N4 → commit + push
```
