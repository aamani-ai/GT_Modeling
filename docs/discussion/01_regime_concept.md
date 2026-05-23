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

A **regime** is the **strategic business positioning** of the plant — what role it is playing in the market, given its contract structure, market context, and the operator's intent. It is one of *four* concepts the model needs to distinguish (see [`03_four_concepts_vocabulary.md`](03_four_concepts_vocabulary.md) for the full map): alongside policy mode, operating mode, and load level.

Importantly, regime is **specifically about business positioning** — *what the plant is trying to do in this market context*. It is **not** about how the operator manages wear (that is policy mode), and it is **not** about the realized load level at each hour (that is its own dimension). Regime sets *typical patterns* of load and start behavior over a long horizon, but it doesn't *determine* those values directly.

Examples of regimes for a gas plant:

- **Baseload** — runs at high capacity factor, low cycling, primary revenue from energy + capacity payments
- **Peaker / load-follower** — runs only during high-price hours, many starts, $/start economics binding on dispatch
- **Frequency regulation** — provides ancillary services, intraday load swings, regime characterized by ramp behavior
- **Cogeneration (DHTS-driven)** — must-run obligations driven by host steam demand, often 1×CC at off-peak prices
- **Must-run contractual** — capacity-firm obligation forcing dispatch regardless of economic signal
- **Curtailment regime** — extended offline periods driven by grid constraints, regulatory action, or own choice
- **Maintenance-deferral regime** — operator deliberately stretches between inspections (note: this overlaps with policy mode and may not be a distinct regime — see §3 below)

A regime is *not* an hour-by-hour decision. It is the *envelope* within which hour-by-hour decisions get made. A plant can switch regimes (e.g., shift from baseload to peaker as the merit order changes around it) but not several times a day.

---

## §3. Why regime is distinct from what we already have (and from load level)

The terminology in this codebase is crowded. Regime needs to be cleanly distinguished from **three** other concepts, not just two. Subsequent discussion (see [`02_load_as_a_dimension.md`](02_load_as_a_dimension.md)) surfaced that *load level* is also a missing axis — distinct from regime, operating mode, and policy mode. The full picture is four concepts on two orthogonal dimensions:

| Concept | What it is | Type | Decision cadence | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Regime** (this doc) | Strategic business positioning | Categorical (or vector) | Slow (weeks–seasons) | Discussion |
| **Policy mode** (A, B, C) | Operator's wear–revenue trade-off preference (modeling abstraction) | Categorical | Static per simulation | Committed |
| **Operating mode** (3×CC, 2×CC, 1×CC) | Physical configuration — how many CTs are firing | Categorical | Hour-by-hour | Committed |
| **Load level** | Continuous intensity within the chosen mode | **Continuous** (% of mode max) | Hour-by-hour | Discussion (see `02_load_as_a_dimension.md`) |

### What regime is NOT

These four concepts each answer a *different* question. Confusing them is what produced the original "mode" overload problem in our docs. Concretely:

- **Regime ≠ operating mode.** Operating mode is the hour-by-hour *physical configuration* decision (which CTs are firing). Regime is the slow-changing *business position*. A plant in cogen regime might use 1×CC most of the time, but the regime is "cogen," not "1×CC." Same operating mode in different regimes means different things (1×CC in cogen serving DHTS ≠ 1×CC in peaker waiting for prices).
- **Regime ≠ load level.** Regime defines *typical load patterns* (peaker → max-when-running; baseload → steady high; frequency-reg → swinging). It does not define the load value at hour 14 of day 234. Load level is the realized value; regime is the pattern.
- **Regime ≠ policy mode.** Both are "posture" concepts at a slow cadence, but they are on *different axes*. Regime is about **business positioning** (what the plant does in the market). Policy mode is about **wear management** (how the operator trades near-term revenue against long-term wear). A plant in *peaker regime* can be operated under *policy A* (run hard) or *policy C* (skip marginal cycle-intensive starts). The combinations are real and distinct.

### The 2×2 orthogonal layout

```
                  SLOW-CHANGING (posture / strategic)
                              │
       ┌──────────────────────┼──────────────────────┐
       │                                              │
   REGIME                                       POLICY MODE
   (business positioning)                       (wear management)
       │                                              │
       └──────────────────────┬───────────────────────┘
                              │
                              │  jointly condition the parameters of
                              ▼
                  FAST-CHANGING (tactical / hour-by-hour)
                              │
       ┌──────────────────────┼──────────────────────┐
       │                                              │
   OPERATING MODE                                LOAD LEVEL
   (physical config)                             (intensity)
       │                                              │
       └──────────────────────┬───────────────────────┘
                              │
                              ▼
                      OPERATING POINT
                   = (mode, load) tuple per hour
```

The risk in the current codebase: a reader who encounters "mode" without qualification has to figure out which kind. The word is over-loaded. Introducing "regime" as a clearly distinct, slow-changing *business positioning* concept — alongside policy mode as its wear-management sibling — gives us a way to talk about the plant's *operating identity* without conflating it with the hour-by-hour engineering decisions (operating mode and load level).

For the full vocabulary map, see [`03_four_concepts_vocabulary.md`](03_four_concepts_vocabulary.md).

### Two layers within regime: capability vs. realization

Even after distinguishing regime from operating mode, load level, and policy mode, there is one more layer that the single word "regime" actually contains. **"Regime"** is ambiguous between two questions, and they have different answers, different drivers, and different cadences of change.

| Layer | Question it answers | What constrains it | Cadence of change |
| :--- | :--- | :--- | :--- |
| **Regime capability / envelope** | What regimes is this plant *capable of being in*? | Physical design + contracts + certifications + crew & infrastructure | Very slow — years; only changes with major investment, contract renewal, recertification, infrastructure changes |
| **Realized regime** | What regime is the plant *actually in* right now? | Operator choice + market conditions, *within the capability envelope* | Slow — weeks to seasons |

The realized regime is always a *subset* of the capability envelope. You cannot realize a regime that isn't in the envelope. This makes them genuinely different objects: the first is a *feasibility set*; the second is a *point within that set*.

#### Examples that show why this distinction matters

- A plant with **DHTS infrastructure + a steam offtake contract** → its capability envelope *includes* cogen regime. This *cannot* be removed by operator choice. The plant might still be in mid-merit *realized* regime during shoulder months, but the capability is structurally there.
- A plant with **no fast-start certification + slow ramp rate** → its capability envelope *excludes* fast peaker regime and frequency regulation, no matter how aggressively the operator wants to use it.
- A plant in **NYISO Zone A with AGC qualification** → its capability envelope *includes* frequency regulation. Whether it *realizes* that regime depends on whether AS clearing prices justify the cycling stress.
- An **OCGT peaker with no steam side** → its capability envelope *excludes* cogen entirely.

The realized regime is always *constrained by* the capability envelope. A plant cannot suddenly "become" a cogen plant; it either has the capability or it doesn't.

#### Why this matters for the project

This isn't just a vocabulary refinement — it changes how Step 1 and Step 2 of the modeling flow connect:

- **Step 1 (configure the asset) outputs include the regime capability envelope** — this is what the engineering + contractual + scheduling configuration *implies* about what regimes are possible
- **Step 2 (characterize regime) operates within that envelope** — you cannot classify the plant into a realized regime that isn't in its capability envelope
- **Calibration** of regime-conditional parameters needs to know which regimes are even *possible* before trying to classify history into them
- **Counterfactual analysis** ("what if this plant operated as a peaker instead of cogen?") requires distinguishing capability (it *cannot* be a fast peaker — capability gap) from realization (it *is currently* mid-merit but *could be* baseload — realization variation)

#### Industry terminology — both sides are well-established

The capability-side and realization-side concepts have *distinct* industry vocabulary, even though "regime" itself isn't a standard term:

**Capability-side**: plant archetype, capability statement, service classification, resource qualification, capability curve, performance envelope, resource type. Found in OEM service contracts, ISO/RTO resource registries, NREL ATB, engineering specifications.

**Realization-side**: duty cycle (sometimes — see ambiguity note), operating profile, current operations, realized capacity factor band. Found in NERC GADS, fleet trending, asset management reporting.

**Note on industry ambiguity**: the term *"duty cycle"* gets used for both sides depending on context. OEM service contracts often use it on the capability side ("this unit is rated for peaking duty"). NERC GADS uses it on the realized side ("this unit has cycled at peaking-class frequency in the last year"). Be explicit which side you mean when you write or read the term.

For the full industry vocabulary mapping and authoritative references, see [`04_industry_vocabulary_and_references.md`](04_industry_vocabulary_and_references.md) §3.1.

#### Lockport's two layers — a worked example

- **Capability envelope** (from configuration): cogen (DHTS infrastructure), mid-merit (3×1 CCGT, F-class, 1992 vintage), must-run (PURPA-era contract structure). Excludes fast-start peaker (slow ramp, no fast-start cert), pure baseload (low CF observed, not designed for it), and frequency regulation (status unknown — would need to check NYISO AGC qualification status).
- **Realized regime** (from history): seasonal hybrid — cogen + mid-merit. Skews toward cogen in winter (DHTS demand high), toward mid-merit in summer (DHTS demand lower, dispatch follows merit order).

The capability envelope is wider than what's realized today; some of the envelope (e.g., must-run availability) is unused but structurally present. This is the kind of nuance the "regime" concept cannot capture without the two-layer split.

#### Implication for the rest of this doc

This distinction means several other parts of this doc should be read carefully:

- §2 (preliminary definition) uses "regime" loosely — it covers *both* layers. When the regime concept eventually graduates to methodology (via an ADR), both layers should be named explicitly.
- §5 (nuances), §7 (open questions), and §8 (committed treatment) implicitly reference whichever layer is relevant in each case. Future versions of this doc should disambiguate.
- The Friday meeting action item ("define regimes from historical data") is specifically about the *realized* side. The capability side comes from configuration, not history.

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
3. **Coordinate with the load-as-a-dimension discussion** ([`02_load_as_a_dimension.md`](02_load_as_a_dimension.md)) — these concepts are coupled. Regime-conditional load distributions are a real thing; any ADR for regime should be aware of where the load ADR is heading, and vice versa.
4. Draft an ADR proposing a specific regime representation + classification methodology. The ADR is the artifact that promotes this from discussion to methodology.
5. If the ADR is accepted, update the methodology docs per §8.

None of this is blocked; none of it is in this week's scope. The point of writing this doc is to preserve the thinking so the eventual ADR has a record of what was considered.

---

## §12. Cross-references

- [`02_load_as_a_dimension.md`](02_load_as_a_dimension.md) — load level as its own axis, distinct from regime; the coupled discussion that motivated cleaning up the "what regime is not" section in §3
- [`03_four_concepts_vocabulary.md`](03_four_concepts_vocabulary.md) — the cheatsheet mapping regime + policy mode + operating mode + load level on their two orthogonal dimensions
- [`04_industry_vocabulary_and_references.md`](04_industry_vocabulary_and_references.md) **§3.1** — *industry equivalents for "regime"* (duty cycle, operating profile, plant archetype, service classification) and authoritative references (NERC GADS, NREL ATB, GE GER-3620 series, EPRI fleet studies). Use industry vocabulary for external communication; keep "regime" internally with explicit definition.
- `docs/methodology/modeling_flow.md` §3 — where regime fits in the project workflow (currently marked "planned, not committed")
- `docs/methodology/architecture.md` — engine internals that currently lack the regime layer
- `docs/methodology/dispatch_mechanics.md` — where operating-mode × policy-mode mechanics are documented (regime would condition both)
- `docs/methodology/extra/performance_and_risk_framework.md` §3 — the policy mode latent-variable discussion at the generic-framework level; regime is the asset-specific counterpart at a coarser time scale
