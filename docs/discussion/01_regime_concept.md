# 01. Regime as a Higher-Level Concept

> **Status**: Open. Exploring the concept; not yet a committed part of methodology.
>
> **Folder context**: This is a discussion doc (per `docs/discussion/README.md`). It exists to think out loud about what *regime* should mean for this project, what its drawbacks would be, and what would need to be true for it to graduate into methodology.

---

## §1. What prompted this discussion

In the 2026-05-22 advisory conversation with Siddharth Deshpande, the idea of **defining "regimes"** for a gas plant — frequency regulation, cogeneration, peaker dispatch, baseload — came up as a way to give the model an explicit handle on the *strategic operating posture* the plant is in.

Subsequent conversations sharpened the observation that **regime is not the same thing as either of the two "mode" concepts we already have in the codebase**, and that conflating them would be a real source of confusion. This doc explores the distinction and what it would take to treat regime as a first-class concept.

The immediate trigger: when reviewing the gt_models structure, it became visible that the current vocabulary has two distinct "mode" concepts (operating mode, policy mode) but no concept for *what strategic posture the plant is operating under*. That gap is what regime would fill.

---

## §2. What we mean by regime (preliminary)

A **regime** is the **strategic operating posture** the plant is in over a *window of time* — what it is *trying to do*, given its market context, contract structure, scheduling obligations, and the operator's intent.

Examples of regimes for a gas plant:

- **Baseload** — runs at high capacity factor, low cycling, primary revenue from energy + capacity payments
- **Peaker / load-follower** — runs only during high-price hours, many starts, $/start economics binding on dispatch
- **Frequency regulation** — provides ancillary services, intraday load swings, regime characterized by ramp behavior
- **Cogeneration (DHTS-driven)** — must-run obligations driven by host steam demand, often 1×CC at off-peak prices
- **Must-run contractual** — capacity-firm obligation forcing dispatch regardless of economic signal
- **Curtailment regime** — extended offline periods driven by grid constraints, regulatory action, or own choice
- **Maintenance-deferral regime** — operator deliberately stretches between inspections (the Mode C "policy" cousin)

A regime is *not* an hour-by-hour decision. It is the *envelope* within which hour-by-hour decisions get made. A plant can switch regimes (e.g., shift from baseload to peaker as the merit order changes around it) but not several times a day.

---

## §3. Why regime is distinct from what we already have

The terminology confusion this concept would resolve is real. Our codebase already has two "mode"-like concepts:

| Term | What it actually means | Decision cadence |
| :--- | :--- | :--- |
| **Operating mode** (3×CC, 2×CC, 1×CC) | A *physical configuration* — how many CTs are firing into the HRSG. An engineering reality. | Hour-by-hour |
| **Policy mode** (A, B, C) | A *modeling abstraction* — the wear-aggressive vs wear-conservative dispatch policy bookend. Used in the simulation to bracket operator behavior. | Static per simulation run |
| **Regime** (proposed) | A *strategic operating posture* — what the plant is trying to do under a given market + contract context. | Slow-changing (weeks to seasons) |

These are three different axes. Regime sits *above* operating mode (a plant in cogen regime makes different operating-mode choices than the same plant in peaker regime, even at identical prices). It sits *adjacent to* policy mode (both are modeling abstractions, but policy mode is about how aggressively to manage wear; regime is about what business posture the plant is in).

The risk in the current codebase: a reader who encounters "mode" without qualification has to figure out which kind. The word is over-loaded. Introducing "regime" as a clearly distinct, slow-changing posture concept gives us a way to talk about the plant's *operating identity* without conflating it with hour-by-hour engineering decisions or with the modeling-side policy bracket.

---

## §4. Why we think regime matters (the gap it fills)

The model today can do this:

- Describe an asset's engineering configuration (`engineering.yaml`)
- Describe its contract structure (`ltsa_terms.yaml`)
- Describe its market context (`market_context.yaml`)
- Run hour-by-hour dispatch decisions across the operating modes

It cannot do this:

- Tell you *what kind of plant Lockport is* in a single sentence ("Lockport is a 3-on-1 cogen running in DHTS-driven regime during winter, mid-merit regime during summer")
- Calibrate parameters *per regime* (wear rate per fired hour is different in baseload vs peaker dispatch, even at identical EOH)
- Predict regime *transitions* (when does a plant shift from baseload to peaker due to market changes?)
- Frame the operator's choices in language a person uses ("which regime is this plant in?" vs "what's its operating mode at hour 17 of day 234?")

Each of these is a capability that regime as a first-class concept would unlock. The current model does fine *within* a regime, but cannot reason *about* regimes.

### How this connects to the Friday meeting

Siddharth's specific suggestion was: define regimes from historical data, tag dispatch history by regime, and integrate regimes into the dispatch schedule so the performance code automatically adjusts based on which regime is active. That's three concrete capabilities:

1. **Definitional** — name the canonical regimes
2. **Inferential** — classify historical dispatch into regimes
3. **Conditional** — let model parameters and dispatch behavior depend on active regime

All three are missing today. Regime as a first-class concept is what would make them implementable.

---

## §5. Nuances worth being careful about

### 5.1 Regime is partly latent, partly observable

Like policy mode (per the framework's Section 3 on latent conditioning), regime is *not declared* — it's inferred. You can read it from the data:

- Capacity factor distribution → suggests baseload vs peaker vs cycling
- Start frequency and hot/warm/cold mix → suggests cycling regime
- DHTS / steam delivery patterns → indicates cogen regime
- Contract structure (tolling, capacity firm, merchant) → indicates contractual obligation regime

But it is not labeled directly in operational data. Any regime concept we adopt has to come with a *classification methodology* — how do you decide, from observed behavior, what regime a plant is in?

This is the "Friday meeting" action item that hasn't been done yet.

### 5.2 Regimes are not mutually exclusive

A plant can be *simultaneously* in cogen regime (because of DHTS obligations) and peaker regime (because it dispatches only at high merit-order positions when not steam-bound). Regimes layer; they don't partition.

This matters because the natural impulse is to assign each plant-hour to one regime. That's often the wrong abstraction. Better to think of regime as a *vector of postures*: cogen-active=1, peaker-merit=0.7, frequency-regulation=0.

### 5.3 Regimes change over time

A plant's regime mix evolves with market conditions, contract renewals, plant life-stage. A peaker built in 2005 might run baseload-style today as gas prices changed the merit order. The same physical asset has different regimes at different points in its life.

This means regime is *not a fixed attribute of the asset*. It is an attribute of the asset *at a point in time*. Any modeling treatment has to allow regimes to vary over the projection window.

### 5.4 Regime ↔ policy mode interaction

Policy mode (A/B/C) is about how aggressively to manage wear. Regime is about what business posture the plant is in. They interact: a *peaker regime* under *policy A* (run-hard) looks very different from a *peaker regime* under *policy C* (preserve hardware) — the peaker policy-C plant might actually convert toward baseload regime over time because it refuses cycle-intensive starts.

This interaction makes regime and policy mode hard to disentangle in practice. Worth being explicit about — we don't currently know how to *separate* them in inference.

### 5.5 The "what regime is this plant in?" question is sometimes contested

For some plants, the answer is obvious (a true single-purpose peaker). For others — and Lockport is one — it is genuinely contested. Lockport could plausibly be classified as cogen (the DHTS obligation matters), as mid-merit (its capacity factor sits between peaker and baseload), or as a *seasonal hybrid* (cogen in winter, mid-merit in summer). Reasonable analysts could disagree on which is most accurate.

Any regime concept has to make peace with the fact that the *primary* regime for some plants is ambiguous. The vector representation in §5.2 helps; a categorical assignment would force a false choice.

---

## §6. Drawbacks of adopting regime as a first-class concept

It would be irresponsible to introduce regime without naming the costs:

1. **Adds a new vocabulary that needs adoption.** Every doc, every code reference, every conversation about an asset needs to be careful about regime vs mode vs policy mode. Cognitive load increases. We'd need to enforce the terminology consistently or risk new conflations.
2. **Requires a classification methodology that doesn't exist yet.** Regime is meaningless until we can say *how* we infer it. Building a classifier is non-trivial: requires labeled training data (which we don't have), or an unsupervised approach (which has its own validation challenges).
3. **Adds a conditioning axis to almost every model parameter.** If wear rate, EFOR, dispatch heuristic, and LTSA cost interpretation all become regime-conditional, the model's parameter space grows. More degrees of freedom = more calibration burden = more risk of overfitting.
4. **Risks becoming a label rather than a tool.** "Lockport is a cogen plant" is a label. The value of regime should be in *what it lets you compute or predict*. If we end up just attaching labels without using them to condition anything, the concept is dead weight.
5. **The naming itself is sensitive.** "Regime" has overlapping uses (regulatory regime, climate regime, market regime). We'd be adding another meaning to a polysemous word. Could cause confusion across teams.

---

## §7. Open questions

Things we don't yet know but will need to know before committing:

1. **What is the canonical list of regimes for gas plants?** The §2 list is preliminary. Are there 5? 10? Is the list fleet-wide or asset-specific?
2. **How do we infer regime from operational data?** Threshold-based on capacity factor + start frequency? Unsupervised clustering on dispatch patterns? Supervised classifier trained on labeled examples (do those exist)?
3. **Is regime a categorical, an ordinal, or a vector?** §5.2 leans toward vector. Worth committing to a representation before building.
4. **How does regime relate to operating mode and policy mode in the model's actual code?** Do regime parameters condition `dispatch_day_mode_aware()` directly? Or do they live in a separate layer that the dispatch logic consults?
5. **Does regime live at the asset level, the asset-year level, or the asset-day level?** The "regime changes over time" point in §5.3 suggests at least asset-year; maybe asset-month.
6. **What's the validation story?** If we tag historical Lockport dispatch with regime labels, how do we know the labels are right? What's the ground truth?
7. **Does adopting regime require an ADR?** Probably yes, if we commit to a specific representation and classification methodology — that's a substantive choice with downstream consequences. The ADR would be the artifact that promotes the concept from "discussion" to "methodology."
8. **Does the framework doc (`performance_and_risk_framework.md`) need to incorporate regime?** Possibly as a manifestation of the policy-mode-as-latent-variable discussion (§3 of that doc) — but at a *coarser* time scale than policy mode. Worth considering whether regime is policy mode's slow-changing parent, or a separate latent dimension entirely.

---

## §8. What "committed" would look like

If we eventually decide regime is real and worth adopting, here's what would happen:

| Artifact | Change |
| :--- | :--- |
| `docs/methodology/architecture.md` | Add regime as a layer in the engine description; clarify how regime interacts with operating mode and policy mode |
| `docs/methodology/glossary.md` | Add formal definition of regime; explicit distinction from operating mode and policy mode |
| `docs/methodology/dispatch_mechanics.md` | Add a section on regime-conditional dispatch |
| `docs/decisions/` | New ADR documenting the regime classification choice (categorical vs vector; threshold-based vs unsupervised vs supervised) |
| `data/assets/lockport/` | New YAML or field capturing inferred regime (e.g., regime history per year, or active regime weights) |
| `data/assets/<asset>/` (future) | Same field structure for any new asset |
| `notebooks/` | New notebook for regime inference from historical MOR data; updates to N4 to use regime-conditional parameters |
| This doc (`01_regime_concept.md`) | Status updated from "Open" to "Graduated to methodology" (or "Closed — chose not to adopt" if we decide against) |

The order matters: the ADR is the gating step. Until there's an ADR, the discussion stays in this folder.

---

## §9. Where regime would *not* go

To be clear about scope, the following are *not* what regime would touch:

- The Max − CL − EL causal decomposition (per `gas_plant_workflow.md`) — regime conditions *parameters within* the decomposition; it doesn't add a new bucket
- The bracketing posture (Policy A/C) — those are modeling abstractions over operator behavior; regime is the realized business posture
- The hazard team's EL pipeline — regime doesn't change what hazards exist or how they're modeled
- The two-output view (revenue + risk arms) — regime would condition both arms but doesn't restructure them

The concept is targeted: it gives us a *handle on plant identity at a strategic level* without restructuring the rest of the framework.

---

## §10. Working notes

A space for thoughts as they arise. Not committed; just captured.

- The "vector of postures" framing (§5.2) is appealing because it gracefully handles ambiguous cases like Lockport. But it makes inference harder than a categorical assignment would. Worth thinking about whether the inference complexity is worth the representational fidelity.
- One way to *start* without committing: tag historical MOR data with an *informal* regime guess (analyst-judged, not algorithmic) and see if the resulting per-regime parameter calibration looks reasonable. If yes, that motivates investing in a proper classifier. If no, we learn something about whether regime as a concept actually does work for this asset class.
- The Friday meeting's specific phrasing — "integrate regimes into the dispatch schedule" — implies regime is a *signal that feeds dispatch decisions* rather than just a metadata tag. That distinction matters for where regime lives in the code.
- The discussion of "what regime is Lockport in?" is itself an interesting calibration question. If two experienced gas analysts disagree, the concept is either (a) genuinely fuzzy, (b) under-specified, or (c) we're not yet asking the right question. Worth running this exercise informally to see.
- A related concept worth checking against literature: the *technology / operations profile* used in fleet modeling (e.g., NREL ATB has plant archetypes). That might be the same idea under a different name. If so, we should pick the existing name rather than coining "regime."

---

## §11. Next steps for this discussion

In rough order:

1. Run a Lockport-specific *informal regime tagging* exercise (analyst-judged, weekly or monthly) using the MOR data. See how it looks.
2. Survey the literature for prior art on operating-regime classification in power systems. NERC reliability standards, NREL ATB plant archetypes, ENTSO-E grid codes, academic literature on dispatch regimes — see if there's a standard taxonomy we should adopt.
3. Draft an ADR proposing a specific regime representation + classification methodology. The ADR is the artifact that promotes this from discussion to methodology.
4. If the ADR is accepted, update the methodology docs per §8.

None of this is blocked; none of it is in this week's scope. The point of writing this doc is to preserve the thinking so the eventual ADR has a record of what was considered.
