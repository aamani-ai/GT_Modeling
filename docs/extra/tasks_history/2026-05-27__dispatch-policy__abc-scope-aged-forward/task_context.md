# Task Context — A/B/C policy scope + aged-state forward (2026-05-27)

## Objective
Resolve the A/B/C dispatch-policy confusion honestly: define what A/B/C is and whether it's useful, fix the forward engine's "A=B=C overlap" bug, and decide the v1 scope — then document it once and confirm readiness for the dashboard.

## Background
The forward engine had been returning **byte-identical** P10/P50/P90 for policies A, B, and C (P50 = −$16.15M for all three). This had been reported as a model limitation ("A/B/C can't diverge in the forward"). It was traced to a **self-imposed assumption**: the forward reset every scenario to a *fresh* plant state (`init_state`: EOH 24,000) and ran only **one year**, parking EOH ~20,000 hours from the 48,000 MI threshold — the region where the wear-penalty multiplier (`wear_mult`) is pinned at 1.0 for every policy. So the policy knob was structurally inert, not broken.

The user (correctly, pointedly) flagged that inventing an assumption that becomes an artificial blocker, then presenting it as a model limitation, is the wrong pattern. This task corrects that.

## Problems encountered / addressed
1. **Forward A=B=C byte-identical** — caused by fresh-start + 1-yr horizon (a config choice, not engine behavior).
2. **A/B/C definition was murky** — the only thing separating the policies is a near-threshold preservation premium with **unsourced magic-number geometry** (`2.5×`/`4.0×`, breakpoints `4000/1000/0`), and that premium was **entangled with plant state** (`eoh_headroom`), fusing a posture choice with a world fact.
3. **Is A/B/C even worth perfecting?** — needed an honest usefulness call before investing.

## What we did
1. **Wrote ADR-009** (`docs/decisions/009-abc-policy-scope.md`) — the scope decision (below).
2. **Added `init_state_override` to `run_path`** (`src/gt_engine/engine.py`) — lets a run start from an injected aged `PlantState` instead of fresh; defaults to `None` (historical path byte-identical, regression-gated).
3. **Modified `run_forward`** (`src/forward/run.py`) — `aged_start=True` (default) seeds each scenario from that mode's aged historical end-state (`run_mode(mode)["final_state"]`).
4. **Validated** — regression 6/6 byte-identical; forward A now separates from B/C.
5. **Diagnosed B≈C with evidence** and **corrected an overclaim** I'd initially written (the "MI fires in-window regardless" finding was wrong).
6. **Documented once** — methodology `dispatch_mechanics.md` §3.7, strategic spine §2.4, dashboard readiness `dashboard_plan.md` §7.
7. **Readiness call for the dashboard** + a memory entry.

## Files touched
**Created**
- `docs/decisions/009-abc-policy-scope.md`
- `docs/extra/tasks_history/2026-05-27__dispatch-policy__abc-scope-aged-forward/` (this folder)
- memory: `project_abc_scope_adr009.md` (+ MEMORY.md index line)

**Modified**
- `src/gt_engine/engine.py` — `run_path(..., init_state_override=None)`
- `src/forward/run.py` — `run_forward(..., aged_start=True)` + manifest fields
- `docs/decisions/README.md` — ADR-009 index row
- `docs/methodology/dispatch_mechanics.md` — §3.7 (new) + §3.6 forward paragraph corrected
- `docs/plans/00_strategic_spine.md` — §2.4 lines 77/93 + §2.4 line 76
- `docs/plans/dashboard_plan.md` — §7 readiness & build order (renumbered cross-refs to §8)

## Current status
- [x] ADR-009 written + indexed
- [x] `init_state_override` plumbed; regression byte-identical (6/6)
- [x] forward carries aged per-mode state; A separates from B/C
- [x] B≈C diagnosed; docs corrected to the honest finding
- [x] methodology + spine + dashboard-plan updated (documented once)
- [x] readiness assessed; memory saved
- [ ] **Nothing committed this session** (user has not asked to commit)

## Next steps (next chat = dashboard)
The near-term dashboard is a **transparent mechanism / what-if showcase of what exists** — NOT a valuation. Capacity + steam revenue are **deliberately deferred** (need much more info/assumptions). Near-term priority = **clarity + concision** of existing work. Build order: (1) `AssetConfig` refactor (globals → config), (2) backend knobs→config→`run_path`/`run_forward`, (3) frontend with energy-only / not-a-valuation framing front-and-centre. The constant-calibration/reference task (`parameter_calibration_plan.md`) runs **separately, in parallel** — not in the dashboard chat. See `dashboard_plan.md` §7.
