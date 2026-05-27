# Decisions — A/B/C scope + aged-state forward (2026-05-27)

Full reasoning trail in [ADR-009](../../../decisions/009-abc-policy-scope.md). Summarized here.

## 1. Separate plant state from policy posture (do now)
**Decision**: Initial EOH (and accrued wear) is a **world input**, not a policy parameter or hidden constant. Plumb `init_state_override` into `run_path`; the forward carries each mode's aged historical end-state instead of resetting fresh.
**Rationale**: This is a correctness fix worth doing on its own merits — it ends the byte-identical A=B=C overlap, makes the historical run honest (the 1992 plant wasn't fresh in 2017), and gives the dashboard its single most important knob. It serves the forward, historical honesty, *and* the dashboard simultaneously, independent of any further A/B/C work.

## 2. A/B/C is a what-if bracket / dashboard knob — NOT a valuation optimizer
**Decision**: Relabel A = myopic merchant, B = NPV-rational, C = risk-averse. Ship as "the spread between run-hard and protect-the-asset," never "the model recommends policy X."
**Rationale**: For Lockport, A/B/C is second-order (low-CF cogen driven by steam host / capacity / must-run, none modeled yet); the revenue sign is still wrong (energy-only); and under an LTSA the owner may not even bear marginal wear cost. So it's a demonstration of the feedback loop + a knob, not where v1 credibility is won.

## 3. Defer the premium re-derivation
**Decision**: Keep the existing ramp for v1, honestly labeled as *operator-posture config* (not physical constants). Defer replacing the magic `2.5×/4.0×` magnitudes with an inspection-pull-forward-cost derivation (× a {0,1,premium} posture multiplier) until the revenue stack is complete and LTSA terms are real.
**Rationale**: The premium only carries meaning against a correct P&L; deriving it now is gold-plating a second-order lever on an incomplete foundation. (This collapsed the earlier "Option L vs Option D" fork → do L now, defer D.)

## 4. Document once, after the solution works
**Decision**: No methodology writing until the fix was validated; then update `dispatch_mechanics.md` §3.7 + spine + ADR in one pass.
**Rationale**: User's explicit instruction — avoid documenting twice. The detail + worked example only went in once the numbers were real.

## 5. Aged start uses each mode's OWN history (per-mode), carried as-is
**Decision**: `run_forward` computes `run_mode(mode)["final_state"]` once per call and reuses it across scenarios (a defensive copy is taken inside `run_path` via `replace()`). In-progress outage state is carried as-is for v1.
**Rationale**: The forward should continue from where *that policy* left the plant. Per-mode is correct: A took its MI in-history (enters fresh-overhauled), B/C deferred it (enter mid-life). Carrying as-is is simplest and honest for v1; flagged in ADR-009 consequences.

## 6. Corrected an overclaim rather than letting it stand
**Decision**: After diagnosing B≈C, rewrote the §3.7 "honest finding" — the first draft claimed "the MI fires in-window regardless of policy," which is false (no mode reaches 48k in the 1-yr window). Replaced with the true mechanism (inherited-state dominance + B≈C as a definition/regime mismatch).
**Rationale**: Methodology must be accurate; trust-but-verify the model's own output before writing it down. (Aligns with the "no shallow answers / verify" feedback.)

## 7. Readiness verdict for the dashboard
**Decision**: Ready to *start*. Capacity + steam revenue are **deliberately deferred** (they need much more information/assumptions). The near-term dashboard is therefore a **transparent mechanism / what-if showcase of what exists**, NOT a valuation — the energy-only headline is acceptable *provided it is explicitly framed as energy-only / revenue-incomplete*. The actual near-term priority is **clarity + concision** of the existing work. (This refines an earlier draft that wrongly called revenue completeness a hard prerequisite.)
**Rationale**: Layering assumption-heavy revenue modeling before the existing work is cleanly articulated is backwards. A showcase that communicates the engine + ranges honestly does not need a valuation-grade headline — it needs the headline *labeled* so it's never mistaken for one. Per `dashboard_plan.md` §6 (non-goal: not a single valuation) and §7.
