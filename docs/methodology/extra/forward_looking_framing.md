# Forward-Looking Framing — Why This Model Looks Different From Solar / Wind Revenue Forecasts

> **Audience**: anyone (internal, investor, team member) reading this model's outputs and asking "what is this actually telling me?" — particularly anyone comparing it to physics-based probabilistic revenue forecasts for renewable assets.
>
> **Companion to**: [`backtest_findings.md`](backtest_findings.md). Both sit in `docs/methodology/extra/` as analytical positioning docs that inform but don't constrain the main methodology flow.
>
> **Status**: positioning statement. Not an ADR (no choice between viable alternatives). Not a guide (not how-to). Not in the main methodology flow (which describes the model's mechanics). This doc explains *what we're trying to deliver and why the model has the shape it does*.

---

## §1. The methodological question this model answers

Given a specific gas-fired generation asset, a forward market environment (uncertain), and a contract structure (LTSA terms), produce a **probabilistic distribution of operating cashflows over a multi-year horizon** that is usable for investment decisions — credible at the P10 / P50 / P90 level, defensible in due diligence, and explicit about the dimensions of uncertainty being modeled.

The deliverable is not a single forecast number. It's a **distribution shape** — and critically, the question is what dimensions of uncertainty feed that distribution. For a renewable asset, the answer is mostly weather + price. For a thermal asset, the answer includes **operator behavior** as a first-class uncertainty source. This doc is about why.

---

## §2. Why thermal asset probabilistic revenue ≠ renewable asset probabilistic revenue

For a solar farm or wind farm, projecting one year of probabilistic revenue is structurally simple at the physics layer:

```
Revenue = f(weather_path) × LMP_path
```

The operator is a price-taker. There is no economic dispatch decision — when the resource is available, the asset produces (modulo curtailment, which is mostly grid-driven, not operator-driven). The P10 / P50 / P90 envelope falls out of:

- Weather realizations (a physical / meteorological distribution)
- Price realizations (a market distribution)
- Their joint correlation (some weather conditions correlate with high LMP)

A physics-based simulation across N weather paths × N price paths produces the envelope directly. The operator's discretion barely enters.

For a gas-fired CCGT, the structure is fundamentally different:

```
Revenue = f(LMP, gas, weather, plant_state) × dispatch_decisions(LMP, gas, weather, plant_state, operator_policy)
```

The operator is a merit-order participant. Every hour, they decide whether to commit, which configuration to run, whether to absorb a marginal start cost to capture a short price spike, whether to defer wear by skipping a profitable day to push an inspection out a quarter. **Two operators with identical plants, identical contracts, and identical market exposure will generate different annual revenues based on their dispatch policies.**

| Dimension | Solar / Wind | Gas-fired CCGT (this model) |
| :--- | :--- | :--- |
| Asset's role in the market | Price taker — produces when resource is available | Merit-order participant — produces when economic |
| Locus of uncertainty | Resource availability (irradiance, wind, weather) | Dispatch decisions (commit/decommit hourly under hurdle rates) |
| Operator degrees of freedom | Minimal — produce when resource permits, accept curtailment | High — start type / mode pick / wear deferral / maintenance scheduling |
| What sets revenue | `production(weather) × LMP` | `dispatch(LMP, gas, plant state, operator policy) × LMP − fuel − wear − contract costs` |
| Probabilistic envelope decomposition | Weather paths × price paths | Weather × price × gas paths **× operator policy** |
| Is a physics + market model sufficient? | Largely yes — operator is passive | **No** — operator's choices materially shift outcomes |

The implication: a physics + market model produces a credible probabilistic envelope for a renewable asset. For a thermal asset, a physics + market model produces *a single deterministic operator-policy trajectory*, which is one slice of the true probabilistic envelope — not the envelope itself.

---

## §3. Policy modes as the missing dimension

The model treats operator dispatch policy as **the first-class uncertainty dimension** that traditional physics-based modeling omits. The implementation: three deliberately-chosen policy bookends.

| Mode | Operating posture | What it represents |
| :--- | :--- | :--- |
| **A — maximize dispatch** | Take every profitable hour; ignore EOH proximity; let inspections trigger when they will | "Operator who runs the plant hard, treats LTSA as overhead" |
| **C — minimize LTSA cost** | Heavily self-curtail near inspection thresholds to defer wear; sacrifice marginal revenue to push CIs / MIs into later contract periods | "Operator who treats LTSA cost as the dominant lever, accepts revenue loss to preserve EOH" |
| **B — balanced** | Mild self-curtailment near thresholds; less aggressive than C | A heuristic middle ground; not strictly necessary to bracket the envelope but useful as a comparator |

The critical framing: **Modes A and C are not realistic plant operations.** They are extremes. Every real operator operates between them, with the realized position varying day-by-day based on market conditions, contract incentives, portfolio context, and risk preferences. The model does not try to predict that realized position.

What the model *does* is produce two simulations under the same market scenario — one at each extreme — so the analyst can read **the spread A↔C as the operator-policy contribution to the envelope**. That spread is real, it's economically meaningful, and it's invisible to any pure physics + market model.

This spread has independent value beyond bounding the revenue distribution. It's a quantification of the asset's **dispatch optionality** — the value the operator can extract by exercising discretion. Timera Energy and the broader CCGT-valuation literature treat this as "extrinsic value" or "optionality value" of flexible gas assets. The mode comparison surfaces that value in dollar terms without requiring a stochastic optimal-control solution.

See [`docs/methodology/architecture.md §5.5`](../architecture.md) for the mechanical implementation (wear-penalty multiplier curve) and [`docs/methodology/architecture.md §5.8`](../architecture.md) for the execution-nesting that runs each mode independently.

---

## §4. What "forward-looking" means concretely

The model's v1 runs against historical replay (2017–2025 actual LMP, gas, weather). That is *not* forward-looking in the investor-grade sense — it's a backtest with synthetic dispatch policy comparison. To deliver the probabilistic forward goal, three input regimes need to be available:

| Input regime | What it delivers | Status in v1 |
| :--- | :--- | :--- |
| **Single forecast trajectory** (deterministic LMP / gas / weather from a base-case forecast) | A single forward simulation per policy mode → 3 paths total; informative but not probabilistic | Not built. v1 uses historical replay instead. |
| **N forecast paths** (Monte Carlo from a forward-anchored synthetic scenario engine) | A probabilistic forward simulation per policy mode → 3 × N paths; P10 / P50 / P90 over market uncertainty only | Phase L scope. The machinery exists in [`.model-gpr/`](../../../.model-gpr/) (Step 1). |
| **N forecast paths × 3 policy modes** | **The full envelope** → joint distribution over `(market scenario × policy)`; the actual investor-grade deliverable | Phase L target. Combines the above with v1's existing policy-mode infrastructure. |

The path to forward-looking is **not a model rewrite** — it's an input swap. The daily-loop architecture, the engineering twin, the LTSA wrapper, the policy modes are *already* compatible with stochastic forward inputs. They were built that way deliberately, following the prototype's convention (see [`docs/extra/understanding_of_gas_turbine_digital_twin.md §10`](../../extra/understanding_of_gas_turbine_digital_twin.md)). What's missing is hooking up the synthetic scenario engine.

This is why the [consolidation plan](../../plans/consolidation_plan.md) treats Phase L as the natural follow-on to v1: the conceptual heavy lifting is done in v1; Phase L is wiring + Monte Carlo orchestration.

---

## §5. The full probabilistic envelope — what investors would actually see

The deliverable, fully realized, is a 2-axis grid of outcomes:

```
                              Policy mode
                  A (max dispatch) ─────── B (balanced) ─────── C (min LTSA)
                  ──────────────────────────────────────────────────────────
   Market         path 1:  A1                  path 1:  B1            path 1:  C1
   scenario       path 2:  A2                  path 2:  B2            path 2:  C2
   (N paths)      ...                          ...                    ...
                  path N:  AN                  path N:  BN            path N:  CN

                  ▼ distribution within        ▼ within column        ▼ within column
                    column                                              
                  → P10/P50/P90 of A           → P10/P50/P90 of B     → P10/P50/P90 of C
                  → "operator runs hard"       → "balanced"           → "operator preserves wear"
                    max-revenue policy bound                            min-LTSA policy bound

                                          │
                                          ▼
                  Joint envelope across (market × policy):
                    • P10 = 10th percentile across the full N × 3 grid
                    • P50 = median across N × 3
                    • P90 = 90th percentile across N × 3

                  Plus the explicit decomposition:
                    • Market-driven variance ≈ spread within each column
                    • Policy-driven variance ≈ spread between columns
                    • Joint variance = both combined
```

What this gives an investor that a pure physics + market model can't:

1. **A genuine probabilistic range** that includes operator-policy uncertainty
2. **An explicit decomposition** between market risk and policy risk — the columns separate them
3. **A quantified optionality value** — `(Mode A revenue) − (Mode C revenue)` at the P50 line is roughly the dispatch flexibility value at median market conditions
4. **A defensible answer to "what assumption are you making about how the plant is run?"** — the answer is "we're not assuming; we're bracketing"

---

## §6. The two claims to separate when pitching this externally

When making the case for this framework to investors, partners, or technical reviewers, **two distinct claims often get conflated**. Separating them strengthens both.

### Claim 1 (uncontroversial, methodologically standard)

> *Probabilistic revenue forecasts for thermal generation assets require operator-policy assumptions on top of physics + market models, because dispatch decisions are economic choices, not physics outcomes.*

This is widely accepted in dispatch-optimization literature (Timera Energy, MIT power-systems texts, NREL cycling-cost methodology). No reviewer should push back on this.

### Claim 2 (the actual contribution)

> *Bracketing operator policy with deliberately-chosen extremes (max-revenue vs min-LTSA-cost) is a tractable, defensible way to expose policy-driven variance to investors without claiming to predict the operator's exact behavior. The framework's posture is to make policy uncertainty visible and bounded rather than hidden inside a single forecast assumption.*

This is what's novel and useful about the framework. It's a **modeling posture**, not just a technical approach.

Conflating the two — pitching "we model operator policy" — invites the reasonable pushback "how do you know what the operator will actually do?" Separating them — "we bracket operator policy" — sidesteps that pushback while still delivering the methodological value.

---

## §7. What's needed to deliver the goal

The model architecture is the right scaffold; what remains is execution. Three workstreams in rough priority.

### 7.1 Phase L scenario engine (the gating item)

Replace historical replay with N forward-anchored synthetic paths. The machinery exists in [`.model-gpr/`](../../../.model-gpr/) (Step 1 — forward anchoring + analog-block sampling). Once integrated, the existing daily-loop runs unchanged against N inputs instead of 1. Single largest delivery item.

### 7.2 Triage the six findings from the 2026-05-15 review

See [`docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/notes.md`](../../extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/notes.md) for the full diagnostic detail. **Prioritize the findings by their effect on the policy-mode spread, not by their effect on the absolute model_card numbers** — because the spread *is* the deliverable.

| Finding | Effect on policy-mode spread | Priority for forward-looking goal |
| :--- | :--- | :--- |
| CI scheduler bug | Affects all three modes equally; spread mostly unchanged | Medium (fidelity matters but doesn't widen envelope) |
| HR-guarantee proxy biased | Affects all three modes equally | Medium (cosmetic for envelope; bad for headline dollars) |
| 2×CC dispatch lockout | Compresses achievable revenue → **narrows the A↔C spread** | **High** — closing this widens the credible envelope |
| Must-run on coldest 20% | Forces dispatch on those days regardless of policy → **suppresses the spread there** | **High** — closing this widens the envelope on must-run days |
| N3 aging-formula not backported | N3 not used in Phase L | Low |
| Hardcoded constants in YAML | None directly; matters for sensitivity sweeps | Low |

This is a reordering of how to think about the findings: a fix that affects modes equally is lower priority than a fix that asymmetrically affects one mode's outcome — even if the latter is a "smaller" code change.

### 7.3 Data-room LTSA extraction

Until placeholder LTSA values are replaced with deal-realistic ones, the absolute dollar magnitudes in the envelope aren't usable externally. The *envelope shape* is informative even with placeholders (because the same placeholders apply consistently to all three modes), but the *headline numbers* aren't. Parallel to 7.1 and 7.2, not strictly sequenced.

### 7.4 Phase K refactor is orthogonal

The `src/` refactor of v1 notebooks is code hygiene, not capability. Phase L can be built on top of the v1 notebooks; the refactor can happen any time without blocking the forward-looking goal.

---

## §8. Implications for v2 prioritization

The standard v2 priority list (per [`gaps_and_priorities.md §6`](../gaps_and_priorities.md)) is roughly:

1. Data-room LTSA extraction
2. NYISO ICAP revenue
3. Cogen steam revenue
4. Per-generator state
5. Less conservative steam-only trigger

Read through the lens of "what expands the credible policy envelope," that ranking shifts:

| Original rank | Item | Effect on the envelope | Re-ranked priority |
| :--- | :--- | :--- | :--- |
| 1 | Data-room LTSA extraction | Replaces placeholder magnitudes; envelope *shape* unchanged but real dollars unlock external use | Stays #1 (necessary for any external use of the dollars) |
| 4 | Per-generator state | Enables 2×CC dispatch → widens A↔C spread on borderline-price days | **Moves to #2** (most direct effect on envelope width) |
| 2 | NYISO ICAP revenue | Adds a revenue line that's independent of policy mode (availability-driven) → narrows the policy spread proportionally to total revenue | Stays around #3 (positive-NPV but doesn't directly widen the policy envelope) |
| 3 | Cogen steam revenue | Same as ICAP — policy-independent revenue line | Stays around #4 |
| 5 | Less conservative steam-only trigger | Affects backtest fidelity, not policy envelope | Drops in priority |
| — | **Phase L scenario engine** | *The* gating item for the envelope deliverable | **Implicit #0** — nothing else matters externally without it |

This is not a recommendation to formally reorder `gaps_and_priorities.md`. It's an explanation of *why* the apparent priority order might change as the project moves toward the forward-looking goal. Each item still has its own justification; they just sort differently under different framings.

---

## §9. Honest acknowledgement of what this doesn't claim

To preempt obvious pushback:

- **The model does not predict operator behavior.** It brackets it. The realized operator path lives between A and C; the framework does not claim to know where.
- **Modes A and C are not the only dimensions of operator-policy uncertainty.** Real operators also choose which plant in a portfolio to dispatch, when to schedule voluntary outages, how to bid into capacity markets, whether to enter long-term hedges. These are not bracketed by A/B/C. The framework brackets *one specific axis* — the start-wear vs revenue trade-off — which happens to be the most directly impactful for an LTSA-bound CCGT but is not exhaustive of operator discretion.
- **The bracketing does not claim equal probability over A vs C.** The distribution over operator policies is itself unknown — and modeling it explicitly would re-introduce the assumption-creation problem this framework was designed to avoid. The framework's posture: present the envelope, let the investor weight it according to their view of the operator.
- **The current v1 dispatch is heuristic, not optimization.** A true MIP-based optimizer would produce a tighter inner bound on each policy mode than the current heuristic does. That's a fidelity gap, not a methodological gap — the framing of "we bracket operator policy" still holds; the bracket just gets narrower with better dispatch internals (the prototype's understanding-doc §5.1 discusses this).
- **The single-asset focus is a v1 scope choice, not a methodological limitation.** Portfolio-level effects (cross-asset dispatch trade-offs, fleet-level LTSA coverage pools) are out of scope. The framework's primitives are asset-level; portfolio extensions are additive, not architectural.

These caveats matter when explaining the framework to a quantitatively-sophisticated reviewer. They strengthen rather than weaken the pitch — by explicitly limiting what's claimed.

---

## §10. How to use this doc

This is a positioning statement, not an operating manual. Practical applications:

- **Pitching the framework externally** — §6 separates the two claims; §5 visualizes the deliverable; §9 preempts common pushback.
- **Triaging open findings** — §7.2's reordering by "effect on policy-mode spread" gives a sharper criterion than "effect on headline numbers."
- **Re-evaluating v2 priorities** — §8 shows how the existing priority list reads under a forward-looking lens.
- **Onboarding new team members** — §2 and §3 communicate why the model has the architecture it does in fewer pages than `architecture.md`.
- **Defending modeling choices in internal review** — §1 and §9 make the framework's *scope* explicit, which is the most common point of conflation in technical critique.

---

*Companion docs:*
- [`backtest_findings.md`](backtest_findings.md) — model vs reality (calibration honesty)
- *This doc* — model vs purpose (positioning honesty)
