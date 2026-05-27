# Dashboard Plan — scope & vision (the shareable showcase layer)

> **Status**: Vision captured 2026-05-27 (build is "soon, not yet"). The dashboard is the **shareable showcase layer** on top of the engine — a transparent *what-if* tool where a user explores one asset's economics under **their own assumptions**.
>
> **Why it's the right framing**: it turns the model's placeholder constants from *"hidden wrong numbers"* into *"explicit, user-adjustable scenario inputs."* For diligence, letting an analyst stress-test *their* assumptions is often more valuable than one "answer." And it's **feasible now** because the engine is already importable (`src/gt_engine.run_path`) — a dashboard backend just calls it with a user-set config.

---

## §1. Purpose & audience
A transparent what-if engine for a single asset (Lockport first): *"explore this plant's economics under your assumptions."* Audience = the team + diligence/showcase viewers. **It communicates a transparent engine + ranges, NOT a single truth-number.**

## §2. The guardrail (so "assume anything" ≠ "never defensible")
The dashboard does **not** replace the credibility work — it **scopes** it:
1. **Sensible, labeled defaults** — best-available (calibrated where we can, literature otherwise); every knob tagged **real vs assumed** (the status taxonomy).
2. **Revenue structure complete** — energy + capacity + steam present (even as adjustable placeholders), or the default headline mis-states the *sign* for a cogen.
3. **Show ranges + mechanism, not a single figure** — never present one number as "the valuation."

So the dashboard **requires** the [sensitivity rank](parameter_calibration_plan.md) (which knobs to expose) + the [revenue-stack scaffolding](00_strategic_spine.md) (a headline worth showing). It gives that credibility work a *destination*.

## §3. Scope — the knobs (tight, high-impact; from the sensitivity rank, not all ~30 constants)
- **Scenario selector**: historical replay year · forward analog ensemble · a price scenario
- **Initial condition**: starting EOH / last-overhaul (the uncalibrated assumption — see `caveats.md` §16)
- **Prices**: gas (level/path) · capacity (ICAP $/kW-mo) · steam revenue
- **LTSA terms**: fixed fee · inspection cost/thresholds
- **Wear/aging**: the aging multiplier (the dominant sensitivity driver) · maybe fatigue/TBC
- **Policy**: mode A / B / C (so A/B/C becomes a *knob*, not a separate analysis)

The rest of the constants get defensible defaults (not exposed — avoid overwhelming the user).

## §4. What it communicates — three messages, in order
1. **P&L decomposition** — Net built from the **revenue stack** (energy + capacity + steam) − the **cost stack** (fuel + VOM + LTSA), so the user *sees where value/cost come from*, not a bare number.
2. **Forward distribution** — P10/P50/P90 under the selected scenarios (uncertainty, not a point).
3. **Sensitivity / what-if** — how the headline moves as each knob turns; which assumptions matter most (the tornado). The honest core.

## §5. Architecture (how it's built — leans on what exists)
```
user knobs (a config dict)  →  src/gt_engine.run_path / src/forward.run_forward
                            →  decomposed P&L + forward distribution + sensitivity
                            →  dashboard frontend (the "dashboard folder")
```
The engine extraction (`src/gt_engine`) + the forward pipeline (`src/forward`) are the backend. Build order: **complete revenue structure + parameterize an asset/scenario config object → backend that maps knobs→config→`run_path` → frontend.** (A full `AssetConfig` refactor — currently module-level globals — is the natural enabler; see implementation docs.)

## §6. Non-goals (v1 dashboard)
- Not a multi-asset portfolio tool (Lockport first).
- Not exposing all ~30 constants (only the high-impact, interpretable knobs).
- Not presenting a single "valuation" — it's a ranges/what-if engine.
- Not real-time market data — it runs on the local spine / scenarios.

## §7. Readiness & build order (assessed 2026-05-27)

**Verdict: ready to *start* the build.** The backend the dashboard calls now exists end-to-end — `run_path` is importable, the forward pipeline runs, A/B/C is a clean knob, and (the last structural blocker, just closed via ADR-009) **initial EOH is an explicit `init_state_override` input**, not a hidden constant. A backend can map a user config → `run_path` today.

**Revenue (capacity + steam) is deliberately deferred — and that's the right call.** Both need substantially more information and assumptions to do credibly; layering them on now would pile assumption on assumption before the *existing* work is cleanly articulated. So the near-term dashboard is **NOT a valuation** — it is a **transparent mechanism / what-if showcase of what exists today** (the wear→dispatch→cost feedback loop, the forward P10/P50/P90, the sensitivity of the headline to each knob). The energy-only headline (≈ −$16M/yr) is fine **provided it is explicitly framed as energy-only / revenue-incomplete** so it is never read as a valuation — that honest framing *is* the mitigation; revenue completeness is **not a hard build-blocker for a showcase** (it would be for a valuation claim). This is consistent with §6 (non-goal: not a single valuation) and the §2 guardrail (show mechanism + ranges, not a truth-number).

**The actual near-term priority: clarity + concision.** Make everything done so far *clear, short, and to the point* before expanding scope. The showcase's job is to communicate the engine and the what-if capability cleanly — not to assert a number.

**Mechanical enabler (sequencing, not a gap)**: engine config is module-level globals; mapping knobs→config→`run_path` wants an `AssetConfig` object. Natural first refactor of the dashboard build.

**Recommended build order**: (1) `AssetConfig` refactor (globals → config object) → (2) backend that maps knobs→config→`run_path`/`run_forward` → (3) frontend with the energy-only / not-a-valuation framing front-and-centre. Capacity + steam slot in later as labeled modules when the information exists; the constant-calibration process (`parameter_calibration_plan.md`) runs in parallel and only improves *defaults*. The §3 knob list is a fine v1 starting set.

**Not blocking** (deliberately deferred, see ADR-009): capacity + steam revenue, the A/B/C premium re-derivation, multi-year forward, forward-price anchoring. A/B/C and initial EOH ship as *knobs* with honest labels.

## §8. Cross-references
- [`parameter_calibration_plan.md`](parameter_calibration_plan.md) — the sensitivity rank picks the knobs; defaults need defending
- [`00_strategic_spine.md`](00_strategic_spine.md) §2.4 — the credibility pivot (revenue + calibration) that feeds this
- [`forward_engine_plan.md`](forward_engine_plan.md) — the forward distribution the dashboard shows
- [`../implementation/gt_engine/`](../implementation/gt_engine/) + [`../implementation/forward/`](../implementation/forward/) — the backend the dashboard calls
- [`../learning_logs/market_and_operations/06_revenue_stack.md`](../learning_logs/market_and_operations/06_revenue_stack.md), [`07_merchant_economics_and_valuation.md`](../learning_logs/market_and_operations/07_merchant_economics_and_valuation.md) — what the P&L decomposition should show
