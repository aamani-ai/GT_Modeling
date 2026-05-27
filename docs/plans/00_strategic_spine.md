# 00. Strategic Spine — gt_models Forward Path

> **Status**: Active. The top-level reference for *where the project is going and why the next step is the next step*. Lives above the per-stream plans (`consolidation_plan.md`, `step_1_climate_price_scenario_plan.md`, `step_2_execution_blueprint_plan.md`). Reflects the post-[ADR-003](../decisions/003-regime-decomposition.md) framework (May 2026).
>
> **Audience**: anyone walking into gt_models needing to understand (a) what state the project is in today, (b) what the next several phases are, and (c) the reasoning behind that ordering. Read this *first* — then the depth lives in the per-stream plans.
>
> **What this is not**: a TODO list, an effort estimate, a project-tracking artifact. It's the *spine* — the load-bearing structural decision about where the project is going. Effort estimates are deliberately omitted (per project convention) because they decay quickly and divert attention from dependency reasoning.

---

## §1. Why this doc exists

The project has, over the past several months, accumulated:

- A v1 implementation (notebooks N1–N5; end-to-end Lockport backtest)
- A methodology spine (`docs/methodology/`)
- A discussion track for emerging concepts (`docs/discussion/`)
- Two decision records (ADR-001 gas hub treatment; ADR-002 Lockport calibration buckets)
- A third decision record (ADR-003 regime decomposition; local-only)
- A learning-log track for fundamentals (`docs/learning_logs/`)
- Three planning docs (consolidation, Step 1 scenarios, Step 2 execution)

Each artifact answers a *local* question. None of them answers the global question: **what's next, in what order, and why?**

That global question matters because we are about to make a substantive architectural commitment (operationalizing the five-concept framework, adding load-and-temperature fidelity, switching from historical to forward-looking) — and the order of those commitments determines how much work gets done twice.

This spine resolves the global question. It does *not* re-litigate the local decisions — each per-stream plan stays the authoritative source for its own depth. The spine just holds the shape.

---

## §2. Where we are now

### 2.1 v1 implementation state

- **End-to-end Lockport backtest works.** Notebooks N1–N5 run; 98/98 tests pass; model_card.md is produced per simulation.
- **Three policy modes (A/B/C) bracket the wear–revenue tradeoff.** Engine + LTSA accruals + forced-outage sampling work as designed.
- **The numbers are NOT representative of real Lockport economics.** LTSA values are Athens placeholders; revenue side is electricity-only (no steam, no capacity, no ancillary). See `docs/methodology/pnl_ledger.md` §4 and `docs/methodology/gaps_and_priorities.md`.

### 2.2 Framework state (post-ADR-003)

What's *conceptually settled* but not yet code:

- **Five concepts** on three cadence bands: capability envelope, realized operating profile, policy mode, operating mode, load level. See [`docs/discussion/03_four_concepts_vocabulary.md`](../discussion/03_four_concepts_vocabulary.md).
- **"Regime" decomposed** into capability envelope + realized operating profile per [ADR-003](../decisions/003-regime-decomposition.md). Structural decision committed; graduation ADRs (per concept) still pending.
- **Load level surfaced as missing dimension.** Currently silent assumption of 100% load when on. Discussion-doc-only; graduation pending.
- **Temperature dependency surfaced.** From Friday 2026-05-22 advisory meeting. Discussion-doc-only; graduation pending.

What's *committed in code*: operating mode + policy mode (both in the N4 engine).

What's *fully implemented in YAMLs*: engineering data (EIA-860 derived); market context (NYISO zone, eGRID, RGGI); LMP/gas/weather time-series spine.

What's *placeholder*: ~47 LTSA-related values; steam-host details; PURPA QF status; AGC qualification status; fast-start certification.

### 2.3 What's in flight

Three workstreams are already running (some recent; some longer):

- **gt_models discussion + learning logs** — recent work; ADR-003 + learning logs 10/11/12 + market-and-ops walkthrough 05 (all local-only since 2026-05-23)
- **diligence-extractor (separate repo)** — being worked on independently; the agent-based pipeline for navigating data rooms and producing structured outputs to feed back into gt_models YAMLs
- **model-gpr (separate repo)** — Step 1 scenario engine; Lockport historical data extracted; forward scenarios in development

These are not yet integrated. Integration is what the next phases are about.

---

## §3. The strategic view — three streams + a data layer

The forward path has three conceptual streams plus a cross-cutting data layer underneath all three.

### 3.1 Stream A — Forward-looking

**What it changes**: Step 2 (gt_models) consumes scenario inputs (price / gas / weather paths) from Step 1 (model-gpr) instead of using historical paths.

**Type of improvement**: Architectural. Changes the input contract between Step 1 and Step 2.

**Why it matters**: The current v1 model has a "god's-eye view" — it knows what prices will be because they already happened. For diligence and valuation, the model needs to operate on forward scenarios (or distributions of scenarios) without this advance knowledge.

**Detailed plan**: [`step_1_climate_price_scenario_plan.md`](step_1_climate_price_scenario_plan.md) (Step 1 side); the Step 2 consumer side is to be expanded in `step_2_execution_blueprint_plan.md`.

### 3.2 Stream B — Temperature + load fidelity (Friday-meeting items)

**What it changes**: Adds load-conditional and ambient-conditional dependencies into degradation, dispatch, and heat-rate calculations.

**Type of improvement**: Content / fidelity. Improves model accuracy at Step 2.

**Why it matters**: Per the 2026-05-22 advisory meeting with Siddharth, gas turbine degradation is driven not only by operating hours but significantly by load percentage and ambient temperature. Current model treats wear as fired-hour-driven; this is a known calibration gap.

**Discussion docs**: [`docs/discussion/02_load_as_a_dimension.md`](../discussion/02_load_as_a_dimension.md); [Friday paper] referenced in `docs/methodology/extra/forward_looking_framing.md`.

### 3.3 Stream C — Capability envelope + framework operationalization

**What it changes**: Makes the five-concept framework load-bearing in YAMLs, engine, and calibration. Specifically:

- Capability envelope becomes a first-class data structure (per-asset)
- Realized operating profile classification becomes a first-class workflow (from MOR data)
- Parameter conditioning by envelope and realization becomes possible

**Type of improvement**: Conceptual / structural. Changes how the model reasons about a plant.

**Why it matters**: Without this, A and B both operate on a single global parameter set — the engine can't condition wear rates, dispatch heuristics, or degradation parameters on what the plant *is* or *can be*. Doing A or B before C creates rework when C eventually lands.

**Discussion docs**: [`docs/discussion/01_regime_concept.md`](../discussion/01_regime_concept.md); [`docs/decisions/003-regime-decomposition.md`](../decisions/003-regime-decomposition.md).

### 3.4 Data layer — D1 open data + D2 diligence extractor

The data layer is a *foundation* underneath all three streams, not a fourth peer.

**D1 — Open-data normalization**: EIA-860 / EIA-923, NYISO public records (ICAP, AGC qualification, fast-start certification), NREL ATB, NERC GADS where accessible, FERC PURPA QF database. *We have clarity on what exists in this domain; the gap is integration into YAMLs.* See §5.2 for the audit checklist.

**D2 — Diligence-extractor outputs**: Per-asset due diligence material parsed into structured YAMLs. Provides LTSA terms, contract structure, steam-host details, regulatory-status evidence. *Longer-running effort*; runs in a separate repo (`diligence-extractor`).

Both D1 and D2 feed the same destination: per-asset YAML files in `data/assets/<asset>/`. The output schema is the same; the source pipelines differ.

### 3.5 Cross-stream dependencies

```text
                 ┌─────────────────────────────────────┐
                 │   D — Data layer (D1 + D2)          │
                 │   Feeds capability envelope fields  │
                 │   + LTSA terms + market context     │
                 └────────────────────┬────────────────┘
                                      │ supplies real values to
                                      ▼
                 ┌─────────────────────────────────────┐
                 │   C — Capability envelope +         │
                 │       framework operationalization  │
                 │   Sets up conditioning structure    │
                 └────────────────────┬────────────────┘
                                      │ provides conditioning for
              ┌───────────────────────┴───────────────────────┐
              │                                                │
              ▼                                                ▼
   ┌────────────────────┐                       ┌────────────────────┐
   │   B — Temperature  │                       │   A — Forward-     │
   │   + load fidelity  │──── feeds into ──────►│   looking model    │
   │                    │  conditional dispatch │   (Step 1 ↔ Step 2)│
   └────────────────────┘                       └────────────────────┘
```

**Key dependency claims** (this is the load-bearing reasoning):

- **C depends on D** — without real values in YAMLs, capability envelope is mostly placeholder
- **A and B depend on C** — without conditioning structure, both produce single-global-parameter models that don't reflect the framework
- **B and A interact** — load-conditional degradation (B) is what forward-looking scenarios (A) ought to be running against
- **D is largely independent of A/B/C** but its outputs are required by all three

Therefore the natural order is: **plan + D-prep → C-skeleton → D-fill → C-graduation → realized profile → B → A**.

---

## §4. The phase structure

Phases are numbered for sequencing but the structure should be read as a *dependency graph*, not a Gantt chart. Effort estimates are deliberately omitted.

### Phase 0 — Strategic spine + plan updates *(current phase)*

**Deliverables**:

- This doc (`00_strategic_spine.md`)
- Surgical updates to existing plans (consolidation_plan, step_1, step_2, gaps_and_priorities) with status callouts linking to this spine

**Why now**: The framework refinements of May 2026 (ADR-003, learning logs, the load + temperature discussions) outpaced the planning docs. Without this spine, the next phase risks pulling in inherited assumptions from pre-framework planning.

**Exit criteria**: Spine published; existing plans carry callouts pointing to the spine.

### Phase 1 — Capability envelope skeleton (Stream C) + D2 ramp (Data layer)

**gt_models side** (C-skeleton):

- Decide capability envelope representation (categorical set, vector, richer object)
- Identify required fields (which duties, what evidence each needs)
- Identify storage location (extend `engineering.yaml`, separate `capability_envelope.yaml`, or other)
- Draft the skeleton for Lockport — fields with `placeholder` / `not_yet_extracted` / `assumed_industry` statuses where data is missing
- Identify the D1 + D2 gaps the skeleton surfaces

**diligence-extractor side** (D2, in parallel; user-led):

- Continue work on the extraction pipeline
- Prioritize Lockport asset (since gt_models is asset-1)
- Target the fields the capability envelope skeleton has flagged as needed

**Why parallel**: C-skeleton tells D2 what to extract; D2 produces evidence to fill C-skeleton. They converge in Phase 2.

**Exit criteria**: Capability envelope skeleton lives in `data/assets/lockport/`; gap list is written; D2 has a target set of fields to prioritize.

### Phase 2 — Data-fill (Data layer integration)

The phase you specifically called out as needing to exist. Without this, the framework operationalizes on placeholder values.

**Deliverables**:

- **D1 open-data audit**: a half-page checklist of every open-data source vs whether it's integrated into Lockport YAMLs. See §5.2 below for the initial scope.
- **D1 integration**: close the audit gaps (ICAP rates, AGC qualification check, PURPA QF status, fast-start cert, NREL ATB archetype reference)
- **D2 outputs landed**: take whatever the diligence extractor has produced and integrate into YAMLs (LTSA terms, steam-host details, regulatory evidence)
- **Capability envelope populated**: replace `placeholder` / `not_yet_extracted` statuses with real values where evidence is now available
- **Updated status taxonomy**: every leaf value carries the right status code (`real_observed`, `real_reported`, `real_computed`, etc.)

**Why this phase exists separately**: It would be tempting to graduate the capability envelope in Phase 1 right after the skeleton lands. That would mean graduating with placeholders. By making Phase 2 explicit, we commit to graduating on real data — and the data-fill work has its own discipline (audit, fill, verify, status-tag).

**Exit criteria**: Lockport YAMLs are *substantively complete* — placeholders down to what genuinely requires future extraction; status taxonomy is right; capability envelope draft is populated with real values.

### Phase 3 — Capability envelope graduation (Stream C)

**Deliverables**:

- ADR-004 (or next number): Capability envelope methodology — commits representation, storage location, refresh cadence, audit discipline
- Cross-references from `architecture.md`, `glossary.md`, `modeling_flow.md` §3
- Methodology section in `docs/methodology/` describing capability envelope as committed
- Status update on discussion doc 01: capability envelope side marked "Graduated"

**Why now**: The methodology graduation should follow data-fill, not precede it. We graduate a structure backed by populated, audited values — not by intent.

**Exit criteria**: ADR-004 written; methodology updated; capability envelope is a first-class concept in the project (not just a discussion concept).

### Phase 4 — Realized operating profile (Stream C, second half)

**Deliverables**:

- Skeleton: representation for realized operating profile (categorical, vector, vector-with-cadence)
- Inference exploration: informal analyst-judged tagging of Lockport historical MOR data into realized-profile labels per period
- Classification methodology candidate: threshold-based vs unsupervised vs supervised approach
- Validation strategy: how do we know the labels are right?
- ADR-005 (or next): Realized operating profile methodology

**Why after capability envelope**: Realized profile is constrained to be a subset of capability envelope. Without capability committed, the inference target is ill-defined ("what duties can we even classify into?"). Capability first, realization second.

**Exit criteria**: ADR-005 written; methodology updated; realized profile is a first-class concept; per-period classification can be applied to MOR data.

### Phase 5 — Temperature + load fidelity (Stream B) — **largely RESOLVED 2026-05-27**

**Outcome** (full detail: [`../methodology/extra/temperature_load_fidelity.md`](../methodology/extra/temperature_load_fidelity.md) §9):

The framing (B1) surfaced a root insight that reshaped this phase: **the over-commit is the price-taker self-commitment paradigm, not gas price or part-load HR.** Consequences:

- ✅ **#2 commitment hurdle — COMMITTED** (d429d18): always-on full-start-C&M recovery. Over-commit 2.07× → **1.94×**, fired hours −15%. The one principled dispatch-realism win for the price-taker model.
- **Part-load HR — no-op** for a price-taker (always dispatches full when economic); the framework polynomial was *corrected* (a0b2e18) regardless.
- **Gas-basis overlay (#1) — tested and reverted** (4e2ff49): overstates post-2018 winter gas (caveats §11) and didn't fix over-commit. Flat Henry Hub stands for v1.
- **Realistic (price-responsive) output (#3) — deferred to Phase 6 (Stream A).** There's no *principled* price-taker version of part-load output; it's inherently a **behavioral/dispatched** model — which is exactly the forward dispatch rule Stream A needs. **#3 ≡ Stream A's dispatch rule.**
- **Temperature × load degradation (B3) — deferred**: modest/redistributive for low-CF Lockport; wants the Friday paper.

**The v1 stance**: the model is an **honest economic upper bound** — the over-commit is the economic *ceiling*, not a realized-output forecast. The behavioral output model that turns it into a realized-output predictor is Phase 6.

**Gaps mapping**: this phase landed gap #5 (dispatch realism — partially, via #2). Gaps #2/#4/#6 (revenue/OPEX integration) and #9 (per-generator state, for 2×CC) remain.

**Exit status**: closed at the principled point (#2 in, model labeled upper-bound). The remaining load/output fidelity is Phase 6 (it's the same behavioral dispatch rule).

### Phase 6 — Forward-looking model (Stream A)

**Deliverables**:

- Step 1 ↔ Step 2 coupling: gt_models consumes price/gas/weather paths from model-gpr
- **Behavioral dispatch rule (absorbed from Stream B #3, 2026-05-27)**: a price-responsive / dispatched-quantity output model that turns the v1 *economic upper bound* into a *realized-output predictor*. This is the realistic-output work deferred from Phase 5 — it's the same dispatch rule a forward model needs, so it's done here, once, properly. (Where 2×CC can finally emerge economically.)
- Single-scenario forward run capability
- Multi-scenario / Monte Carlo orchestration (Phase L from the original consolidation plan)
- Forward conditioning: capability envelope + realized profile (from Phases 3 + 4) inform dispatch in forward simulations

**Why last in the dependency chain**: Forward-looking benefits from having all the conditioning structure (capability, realization, load, temperature) in place. Doing it earlier means re-doing it once those land. **Note**: the v1 model (Phase 5 endpoint) is an *economic upper bound*; Phase 6's behavioral dispatch rule is what makes forward outputs *realized-output predictions* rather than ceilings.

**Gaps_and_priorities mapping**: this phase absorbs gap #7 (Phase L Monte Carlo). Possibly also gap #9 (per-generator state) if the engine refactor is bundled.

**Exit criteria**: gt_models can run forward simulations against model-gpr scenarios; outputs reflect the full conditioning structure.

---

## §5. Mapping existing artifacts onto the spine

### 5.1 `gaps_and_priorities.md` priorities → strategic phases

Mapping the 9 priorities from `docs/methodology/gaps_and_priorities.md` §6 onto the strategic phases:

| Priority | Description | Strategic phase |
| --: | :--- | :--- |
| **#1** | Data-room LTSA extraction (+$8–15M/yr) | Phase 2 (D2 integration into YAMLs) |
| **#2** | Add NYISO ICAP revenue (+$5–9M/yr) | Phase 2 (D1 — open-data audit closes ICAP gap) + Phase 5 (engine integration of capacity revenue stream) |
| **#3** | MOR-replay mode (Mode M) + Phase K refactor | Can run in parallel with Phase 2; diagnostic for validating gap fills |
| **#4** | Add cogen steam revenue (+$3–7M/yr) | Phase 2 (D2 — DHTS extraction) + Phase 5 (engine integration) |
| **#5** | Dispatch realism — outages, ramp, derates | Phase 5 (fidelity work) |
| **#6** | Add Fixed OPEX layer | Phase 2 (D1 — fixed-cost data from EIA/FERC filings) + Phase 5 (engine integration) |
| **#7** | Phase L Monte Carlo | Phase 6 (forward-looking model) |
| **#8** | Per-asset Bucket B calibration | Phase 5 (parameter conditioning) and partly Phase 4 (per-realized-profile calibration) |
| **#9** | Per-generator state (v2 architecture) | Phase 5 (engine refactor) |

The 9 priorities still hold; this spine just gives them strategic order.

### 5.2 Open-data audit — initial scope

For Phase 2, the D1 audit checklist. Each source × what it provides × current integration status:

| Source | Provides | Current Lockport status |
| :--- | :--- | :--- |
| EIA-860 | Capacity, vintage, prime mover, fuel type, ownership | ✓ Integrated → `engineering.yaml` |
| EIA-923 | Generation, fuel use, fuel cost | Partial — Lockport-relevant data not fully extracted |
| eGRID | Emission factors | ✓ Integrated → `market_context.yaml` |
| NYISO LMP | Day-ahead + real-time prices | ✓ Integrated → `data/paths/lockport/` |
| Gas hub prices | Algonquin / Henry Hub | ✓ Integrated → `data/paths/lockport/` (Henry Hub for v1 per ADR-001) |
| Weather (NOAA / NCEI) | Hourly weather, 19 variables | ✓ Integrated → `data/paths/lockport/` |
| **NYISO ICAP** | Capacity market clearing prices | ✗ Not integrated (gap #2) |
| **NYISO AGC qualification record** | Frequency-reg capability check | ✗ Not integrated (envelope question) |
| **FERC PURPA QF database** | QF status verification | ✗ Not integrated (placeholder in `ltsa_terms.yaml`) |
| **NYISO fast-start cert status** | Peaker capability check | ✗ Not integrated (currently asserted) |
| **NREL ATB** | Plant archetype reference (capability-side) | ✗ Not actively pulled |
| **NERC GADS classifications** | Realized duty-cycle reference (realization-side) | ✗ Not integrated (requires membership) |
| **FERC Form 1** | Utility-side cost data (Fixed OPEX) | ✗ Not actively pulled (gap #6 component) |

The audit's deliverable in Phase 2 is closing the ✗ rows where the data is reachable.

### 5.3 Existing plans — status callouts

Each existing plan file gets a callout linking to this spine:

- **`consolidation_plan.md`** — foundational; defines 4-repo system + folder architecture. Predates ADR-003 but its load-bearing decisions (status taxonomy, asset-onboarding pattern, 4-repo boundaries) are still active. Status callout points to this spine and notes the framework refinements.
- **`step_1_climate_price_scenario_plan.md`** — Stream A upstream; defines the exogenous scenario package. Status callout notes that Stream A activation is Phase 6 in this spine; the plan itself stays valid for that phase.
- **`step_2_execution_blueprint_plan.md`** — Stream A downstream; defines how Step 2 consumes scenarios. Status callout notes the framework refinements (five concepts, conditioning structure) that should inform this plan when Phase 6 starts.
- **`gaps_and_priorities.md`** — bottom-up engineering priorities. Status callout points to §5.1 above for the strategic-phase mapping.

---

## §6. What's not in scope of this spine

To prevent drift, the following are explicitly *out of scope* for this doc:

- **Code refactors that don't affect the framework or data layer.** Engine performance optimizations, test reorganizations, dependency upgrades — these are routine maintenance, not strategic shifts.
- **Asset onboarding for assets other than Lockport.** The framework graduations happen on Lockport because Lockport is the v1 target. Once C/B/A are landed for Lockport, asset-onboarding methodology can be productized.
- **Hazard team's EL pipeline.** The two-arm split (revenue arm = gt_models; risk arm = hazard team's IDF + fragility pipeline) means the risk arm is out of scope. See `docs/methodology/extra/gas_plant_workflow.md`.
- **The diligence-extractor pipeline implementation itself.** That work lives in `diligence-extractor` repo. Its outputs are inputs to gt_models; the implementation is not gt_models's concern.
- **Cross-asset patterns / multi-asset valuation.** Until Lockport is fully landed, multi-asset is premature.

---

## §7. How to use this spine

### When starting a new session

1. Read this spine to confirm the strategic phase you're in
2. Read the relevant per-phase deliverables in §4
3. Go to the per-stream plan for execution-level depth

### When making a substantive decision

1. Check whether the decision fits within the current phase
2. If the decision crosses phases, flag it explicitly (does it accelerate a future phase? defer a current one?)
3. Substantive decisions get their own ADR; reference this spine in the ADR's context

### When updating the spine itself

The spine should change when:

- A phase completes (mark it complete in §4)
- A phase reveals dependencies not anticipated here (update §3.5)
- The strategic streams themselves change (rare — would require a new ADR)
- The existing plans get major updates (refresh §5.3)

The spine should *not* change when:

- An individual artifact is added or updated
- A specific number / placeholder is closed
- A learning log or discussion doc is written

---

## §8. Cross-references

### Per-stream plans (the depth)

- [`consolidation_plan.md`](consolidation_plan.md) — 4-repo system + folder architecture + status taxonomy
- [`step_1_climate_price_scenario_plan.md`](step_1_climate_price_scenario_plan.md) — Stream A upstream (Step 1 scenario package)
- [`step_2_execution_blueprint_plan.md`](step_2_execution_blueprint_plan.md) — Stream A downstream (Step 2 execution blueprint)
- [`consolidation_plan/`](consolidation_plan/) — execution-level subplans (Track 2 notebooks; historical)

### Framework artifacts

- [`docs/discussion/01_regime_concept.md`](../discussion/01_regime_concept.md) — capability envelope + realized operating profile (Stream C foundation)
- [`docs/discussion/02_load_as_a_dimension.md`](../discussion/02_load_as_a_dimension.md) — load level (Stream B foundation)
- [`docs/discussion/03_four_concepts_vocabulary.md`](../discussion/03_four_concepts_vocabulary.md) — five-concept cheatsheet
- [`docs/discussion/04_industry_vocabulary_and_references.md`](../discussion/04_industry_vocabulary_and_references.md) — industry vocabulary mapping
- [`docs/decisions/003-regime-decomposition.md`](../decisions/003-regime-decomposition.md) — ADR-003

### Methodology

- [`docs/methodology/architecture.md`](../methodology/architecture.md) — engine + daily loop + state vector
- [`docs/methodology/modeling_flow.md`](../methodology/modeling_flow.md) — end-to-end project workflow
- [`docs/methodology/gaps_and_priorities.md`](../methodology/gaps_and_priorities.md) — bottom-up v2 priorities (mapped onto strategic phases in §5.1)
- [`docs/methodology/dispatch_mechanics.md`](../methodology/dispatch_mechanics.md) — operating mode × policy mode
- [`docs/methodology/pnl_ledger.md`](../methodology/pnl_ledger.md) — revenue + cost components

### Learning logs (the fundamentals)

- [`docs/learning_logs/basics/10_plant_duty_classifications.md`](../learning_logs/basics/10_plant_duty_classifications.md) — duty vocabulary
- [`docs/learning_logs/basics/11_capability_vs_realization.md`](../learning_logs/basics/11_capability_vs_realization.md) — two-layer framework with human analogy
- [`docs/learning_logs/market_and_operations/05_operating_profiles_walkthrough.md`](../learning_logs/market_and_operations/05_operating_profiles_walkthrough.md) — regime-by-regime walkthrough
- [`docs/learning_logs/basics/12_five_concepts_intuition.md`](../learning_logs/basics/12_five_concepts_intuition.md) — capstone summary

### Cross-repo

- `~/code/personal/diligence-extractor` — D2 pipeline (separate repo; user-led)
- `~/code/work/infrasure_git_codes/model-gpr` — Step 1 scenario engine (separate repo)
- `~/code/personal/renewablesinfo_org` — Open-data fleet ETL (separate repo)

---

## §9. Maintenance notes

This spine is a *living* document but should change rarely. The structural skeleton (three streams + data layer; phases 0–6; the dependency reasoning in §3.5) should be stable for the duration of the v2 push. Specifically:

- **The phase numbers should not be renumbered** even if a phase is split or merged in execution. Splitting Phase 2 into 2a/2b is fine; renumbering Phase 5 → Phase 4 is not.
- **Phase content can refine.** New deliverables can be added; deliverables can be moved between phases if a dependency reveal demands it (with explicit reasoning).
- **The §5 mapping table should refresh** when `gaps_and_priorities.md` itself changes — they should stay in sync.
- **Update §2 (where we are now)** whenever a phase completes or a major artifact lands.

When in doubt about whether something belongs in the spine: ask whether the decision is *strategic* (cross-phase, cross-stream, cross-repo) or *tactical* (within one phase, one artifact, one file). The spine is strategic only.
