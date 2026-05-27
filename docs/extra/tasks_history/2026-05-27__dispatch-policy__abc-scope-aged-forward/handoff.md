# Handoff — A/B/C scope + aged-state forward (2026-05-27)

> **60-second summary**: Fixed the forward engine's "A=B=C byte-identical" result, which was caused by a self-imposed assumption (fresh-start + 1-yr horizon), NOT a model limitation. Separated **plant state from policy posture**: `run_path` now takes `init_state_override`, and the forward carries each mode's **aged historical end-state**. Regression stays byte-identical (6/6). Wrote **ADR-009** scoping A/B/C as a **what-if/dashboard knob, not a valuation optimizer**, and **deferring** the premium-magnitude re-derivation. Diagnosed honestly: A's forward separation is mostly *inherited* state (A overhauled in-history); B≈C (differ ~$0.14M, below display) because a 1-yr forward never enters C's distinctive headroom<1,000 regime. Documented once in `dispatch_mechanics.md` §3.7 + spine + dashboard-plan. **Next chat = the dashboard** (a transparent what-if *showcase of what exists*, NOT a valuation; capacity+steam deliberately deferred). **Nothing committed this session.**

## 10-bullet summary
1. **Root cause**: forward reset to fresh `init_state` (EOH 24k) + 1-yr → EOH stays ~20k from the 48k MI threshold → `wear_mult` pinned at 1.0 for all policies → A=B=C byte-identical. A config choice, not engine behavior.
2. **Fix**: `run_path(..., init_state_override=None)` (engine.py) — start from an injected aged `PlantState`; `run_forward(..., aged_start=True)` (run.py) seeds each scenario from `run_mode(mode)["final_state"]`.
3. **Regression byte-identical** (6/6) — default `None` keeps the historical path unchanged.
4. **ADR-009 written** — A/B/C scope: (a) separate state from posture NOW; (b) A/B/C = bracketing knob (myopic/NPV-rational/risk-averse), not optimizer; (c) defer premium re-derivation until revenue + LTSA are real.
5. **Aged forward result**: P50 A −16.35, B −16.58, C −16.58 ($M). A separates; B≈C.
6. **Honest caveat #1**: A's edge is mostly *inherited* state (A did its MI in-history → enters fresh-overhauled, EOH 42,138; B/C carry the deferred MI, EOH 42,370). In-forward policy effect is small.
7. **Honest caveat #2**: B≈C (differ ~$0.14M) — a 1-yr forward never enters C's distinctive headroom<1,000 region, so C's extra conservatism is dormant. A definition/regime mismatch. Real bite needs a **multi-year forward**.
8. **Corrected a wrong draft finding** ("MI fires in-window regardless") — verified against numbers, rewrote.
9. **Documented once** (per user's "don't document twice"): `dispatch_mechanics.md` §3.7, spine §2.4, `dashboard_plan.md` §7, memory `project_abc_scope_adr009.md`.
10. **Dashboard readiness**: ready to START; capacity+steam deferred by choice; near-term = clarity/concision + a *showcase* framed as not-a-valuation.

## Files touched (quick map)
**Created**: `docs/decisions/009-abc-policy-scope.md`; this task folder; memory `project_abc_scope_adr009.md`.
**Modified**: `src/gt_engine/engine.py` (`run_path` +param); `src/forward/run.py` (`run_forward` aged_start + manifest); `docs/decisions/README.md` (index); `docs/methodology/dispatch_mechanics.md` (§3.7 + §3.6 fix); `docs/plans/00_strategic_spine.md` (§2.4); `docs/plans/dashboard_plan.md` (§7).

## Repro commands
```bash
source .venv/bin/activate
python -m pytest tests/test_gt_engine_regression.py -q            # 6 passed (byte-identical gate)
cd /Users/divy/code/work/infrasure_git_codes/gt_models
python -c "import sys; sys.path.insert(0,'src'); from forward.run import run_forward; \
  [print(m, run_forward(m, basis='RT', save=False, aged_start=True)['quantiles']['net_pl_usd']['P50']/1e6) for m in 'ABC']"
```

## Next action — THE DASHBOARD (next chat's primary focus)

**Frame**: a transparent **what-if / mechanism SHOWCASE of what exists today** — NOT a valuation. Communicate the engine + ranges clearly and concisely. (User's explicit steer: make existing work *clear, short, to the point* before expanding scope.)

**Deliberately deferred (do NOT build in the dashboard chat)**: capacity revenue (ICAP) + steam revenue — they need much more info/assumptions. The headline stays energy-only and **must be labeled "energy-only / not a valuation"** so it's never misread. The constant-calibration/reference task (`parameter_calibration_plan.md`) runs in a SEPARATE process, in parallel.

**Build roadmap** (from `dashboard_plan.md` §5/§7):
- **Phase A — `AssetConfig` refactor**: engine config is module-level globals; introduce a config object so "user knobs → config → `run_path`" is clean. The key enabler.
- **Phase B — backend**: map a knob dict → `AssetConfig` → `run_path`/`run_forward`; return decomposed P&L + forward P10/P50/P90 + a sensitivity/tornado.
- **Phase C — frontend** (the "dashboard folder"): knobs = initial EOH, gas, LTSA fee, **policy A/B/C**, scenario selector; outputs = P&L decomposition, forward distribution, what-if/sensitivity. Energy-only / not-a-valuation banner front-and-centre.

**Read before starting**:
- `docs/plans/dashboard_plan.md` (whole; esp. §3 knobs, §4 messages, §5 architecture, §7 readiness)
- `docs/plans/00_strategic_spine.md` §2.4 (the credibility pivot + destination)
- `docs/decisions/009-abc-policy-scope.md` (why A/B/C + initial EOH are *knobs*)
- `docs/implementation/gt_engine/` + `docs/implementation/forward/` (the backend the dashboard calls)
- `src/gt_engine/engine.py` (`run_path` is the entry point; config = module globals → the refactor target)
- `src/forward/run.py` (`run_forward` is the forward-distribution entry point)

**Gotchas**:
- Use the `.venv` (pandas<3; pandas 3 breaks the notebooks via removed `fillna(method=)`).
- `data/outputs/` is gitignored/regenerable — don't commit it.
- This repo pushes to `aamani-ai/GT_Modeling` via `git@github.com-work:` — verify `cd + pwd + remote` before any push (CLAUDE.md "Don'ts").
- `docs/decisions/` is local-only (gitignored) — ADR-009 won't appear in the GitHub repo.
- Nothing from this session is committed; review `git status` first.
