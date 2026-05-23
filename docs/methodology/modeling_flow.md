# Modeling a Gas Plant: End-to-End Project Flow

> **What this doc is**: a top-down walkthrough of *how to model a gas plant* from the moment an asset enters the project to the moment the model produces a `model_card`. Generalized for any gas plant; Lockport is the **worked example** at each step.
>
> **What it is not**: a description of how the engine works internally (see [`architecture.md`](architecture.md)), the conceptual decomposition lens (see [`extra/gas_plant_workflow.md`](extra/gas_plant_workflow.md)), or the economic ledger (see [`pnl_ledger.md`](pnl_ledger.md)).

## Audience

Anyone landing on this project who needs to understand the *project-level workflow* — what you do, in what order, with which inputs, to produce a defensible model for a gas plant. New team members. Reviewers. Future-self after a hiatus. Anyone evaluating whether the framework would apply to a new asset.

## Why this doc exists

Until now, the gt_models project had docs for:

- The engine's mechanics ([`architecture.md`](architecture.md))
- The decomposition lens ([`extra/gas_plant_workflow.md`](extra/gas_plant_workflow.md))
- The economic ledger ([`pnl_ledger.md`](pnl_ledger.md))
- The operating mode × policy mode mechanics ([`dispatch_mechanics.md`](dispatch_mechanics.md))
- Gaps and priorities ([`gaps_and_priorities.md`](gaps_and_priorities.md))

None of these answers the question *"Given a new gas plant, what do I do to model it?"* in a single top-down read. That answer has been assembled piecemeal across the docs. This doc consolidates it.

The framing it uses generalizes — the project is not *just* about Lockport. Lockport is the **initial guinea pig**: a complex 3-on-1 cogen with placeholder LTSA terms, a partial data-room extraction, and a non-trivial regime mix. If the workflow works for Lockport, it works for almost anything else. But the workflow itself is asset-agnostic.

---

## §0. Posture note

This doc, like the rest of the methodology folder, is **scaffolding, not specification**. The workflow below is a starting position. In practice, you will find:

- Configuration data that doesn't fit the file structure cleanly
- Regimes that defy categorization
- Calibration that requires bending the engine's parameters
- Forward projections that require scenarios the model doesn't yet support

These are normal. Document deviations explicitly; the deviation log is more valuable than workflow adherence. See the posture note at the top of [`extra/performance_and_risk_framework.md`](extra/performance_and_risk_framework.md) for the canonical statement of this principle.

---

## §1. The workflow at a glance

```
   ┌──────────────────────────────────────────────────────────────────┐
   │  STEP 1: CONFIGURE THE ASSET                                     │
   │  ▸ Open-source data → identity, engineering, market, operating   │
   │  ▸ Personal data room → contracts, real operations, schedules    │
   │  ▸ Engineering + Contractual + Scheduling dimensions             │
   │  Output: 5 status-tagged YAML files + provenance + caveats        │
   └─────────────────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  STEP 2: IDENTIFY OPERATING REGIME(S)                            │
   │  ▸ From history + contract structure                             │
   │  ▸ Baseload / peaker / cogen / freq-reg / must-run / hybrid      │
   │  Status: planned (regime concept currently in discussion;        │
   │          see docs/discussion/01_regime_concept.md)               │
   │  Output (when built): regime tags per time window                │
   └─────────────────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  STEP 3: CALIBRATE AGAINST HISTORY                               │
   │  ▸ Engineering params (HR degradation, fouling, EFOR baselines)  │
   │  ▸ LTSA params (contract values, once extracted)                 │
   │  ▸ Dispatch params (per regime, once regime is committed)        │
   │  ▸ Backtest against observed MOR data                            │
   │  Output: parameter set tuned to the specific asset               │
   └─────────────────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  STEP 4: RUN FORWARD PROJECTION                                  │
   │  ▸ Daily loop × 3 policy modes × N market scenarios              │
   │  ▸ Twin dispatch (clean vs degraded) for loss attribution        │
   │  ▸ Horizon: 1-3 yr primary; 5-10 yr extension; project life      │
   │  Output: daily / hourly trajectories per mode per scenario        │
   └─────────────────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  STEP 5: PROPAGATE LOSSES TO REVENUE                             │
   │  ▸ Continuous losses (CL) → revenue side via HR / capacity       │
   │  ▸ Step events (CI / MI) → owner-uncovered cost                  │
   │  ▸ Stochastic outages (EFOR) → revenue gap + repair cost         │
   │  ▸ Event losses (EL) → hazard team's pipeline (separate scope)   │
   │  Output: P&L by stream, attributed by cause                       │
   └─────────────────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  STEP 6: PRODUCE THE DELIVERABLE                                 │
   │  ▸ model_card.md (headline summary)                              │
   │  ▸ Parquet bundle (per-day records, per-mode comparisons)        │
   │  ▸ Audit trail (status taxonomy, caveats, provenance)            │
   │  Output: a deliverable that can be reviewed, defended, iterated  │
   └──────────────────────────────────────────────────────────────────┘
```

Each step is detailed below. The Lockport-specific instance of each step is given inline as **the worked example**.

---

## §2. Step 1 — Configure the asset

### §2.1 The two data sources

A gas plant's configuration comes from **two distinct sourcing workflows**, and confusing them is a common cause of project drift.

| Source side | What it covers | How you get it | What can go wrong |
| :--- | :--- | :--- | :--- |
| **Public / open-source** | Plant identity (EIA-860 / ORISPL), nameplate, ISO node IDs, eGRID subregion, RGGI eligibility, prime-mover specs, generic tech-class defaults | Public regulatory filings, ISO databases, NREL ATB, vendor datasheets | Generic tech defaults may not reflect this asset's specific tuning |
| **Personal / data-room** | Real LTSA / FSA contract values, MOR-derived heat rates, cogen / steam tariff terms, maintenance & cleaning schedules, inspection history, real degradation curves from O&M reports | Diligence extraction from the asset's actual documentation | Most diligence projects have *partial* extraction — some fields end up as placeholders pending extraction |

**Why this matters at the workflow level**: the two sides require different effort and have different reliability profiles. Public data is cheap and uniform across assets but lacks asset-specific calibration. Personal data is expensive and asset-specific but partial. Most projects end up with a *mix* — high-confidence public values for half the configuration, placeholder personal values for the other half.

**Worked example — Lockport**:

| Side | Status | Files / artifacts |
| :--- | :--- | :--- |
| Public | ✓ mostly complete | `identity.yaml` (EIA Plant ID 54041, ORISPL, NYISO PTIDs), most of `engineering.yaml` (EIA-860 enriched), `market_context.yaml` (NYISO Zone A, NYUP eGRID, RGGI applicable) |
| Personal | ⚠ partial | `operating_profile.yaml` (MOR-derived heat rates ✓, DHTS partial, scheduling missing), `ltsa_terms.yaml` (**all placeholder** — Athens-prototype defaults pending data-room extraction) |

The current overall split is **79.5% `real_*` / 17.5% `placeholder` / 2% `assumed_industry`** across 268 leaf values (per `model_card.md` § Assumption-status distribution).

### §2.2 The three configuration dimensions

Configuration is not just engineering. It has **three distinct dimensions**, each requiring different sourcing and modeling treatment.

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  ENGINEERING                                                    │
   │  ▸ Nameplate, prime mover, generators, derate curves            │
   │  ▸ Heat rates by mode, cold-start gas, design specs             │
   │  ▸ Mostly real_observed / real_reported when public data exists │
   └─────────────────────────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────────────────────────┐
   │  CONTRACTUAL                                                    │
   │  ▸ LTSA / CSA / FSA terms — fees, overages, guarantees          │
   │  ▸ PPA / tolling / offtake structure                            │
   │  ▸ ICAP / capacity payment commitments                          │
   │  ▸ Mostly personal data room; placeholder pending extraction    │
   └─────────────────────────────────────────────────────────────────┘
   ┌─────────────────────────────────────────────────────────────────┐
   │  SCHEDULING                                                     │
   │  ▸ Cleaning / maintenance / inspection schedules                │
   │  ▸ Planned outage calendars                                     │
   │  ▸ Operator-set thresholds (e.g., water wash cadence)           │
   │  ▸ Currently the weakest dimension across most projects         │
   └─────────────────────────────────────────────────────────────────┘
```

All three are *configuration*. None of them is *operational data* — that comes in Step 3. Configuration is *what the plant is and what it has agreed to*; operational data is *what it has done*.

**Worked example — Lockport**:

- Engineering: covered by `engineering.yaml` (4 generators with prime-mover codes, derates, vintage) and the engineering-relevant parts of `operating_profile.yaml` (mode heat rates from MOR).
- Contractual: covered by `ltsa_terms.yaml` (7 LTSA streams: fixed fee, EOH reserve, CI / MI costs, overages, availability penalty, HR penalty, forced-outage coverage). All values are placeholder. The Friday 2026-05-22 advisory meeting confirmed this is *priority 1* gap to close.
- Scheduling: **not yet extracted**. The Friday meeting flagged this as an action item — cleaning schedules, water-wash cadence, inspection history all need to come from the plant's actual documentation. No file exists yet.

### §2.3 The status taxonomy as the workflow's audit trail

Every leaf value in the YAML files carries a `{value, status, source}` triple. The status code documents **how the value was sourced** and therefore **how trustworthy it is at that stage of the project**.

The 9 status codes (per `docs/assumptions/status_taxonomy.md`):

```
real_observed        — measured directly from MOR / SCADA / EIA-860
real_reported        — from regulatory filings / contracts
real_computed        — derived from real_observed via deterministic formula
assumed_techclass    — class-level default (e.g., F-class fleet mean)
assumed_vendor       — OEM-published spec
assumed_industry     — broader industry rule of thumb
assumed_derived      — derived from another assumption (compound uncertainty)
placeholder          — typed value awaiting real source
not_applicable       — doesn't apply for this asset
```

This taxonomy *is* the workflow's audit trail. At any point in the project, you can ask: "What share of this asset's configuration is `real_*` vs `placeholder`?" and get a number that tells you how mature the configuration is.

**The graduation pattern**: a value starts as `placeholder` (typed default, no real source), moves to `assumed_*` (industry / class / vendor default), eventually to `real_*` (asset-specific data source confirmed). The workflow's progress is visible in the distribution of these codes.

**Worked example — Lockport's current distribution**:

| Status | Count | Share |
| :--- | --: | --: |
| `real_observed` | 31 | 11.6% |
| `real_reported` | 160 | 59.7% |
| `real_computed` | 22 | 8.2% |
| **All real_*** | **213** | **79.5%** |
| `placeholder` | 47 | 17.5% |
| `assumed_industry` | 6 | 2.2% |
| `not_applicable` | 2 | 0.7% |

47 placeholders concentrated in `ltsa_terms.yaml` — exactly the dimension we know is missing (contractual / personal data room).

### §2.4 The output of Step 1

By the end of Step 1, the asset should have:

```
data/assets/<asset>/
├── identity.yaml              (public: plant ID, location, owner, ISO IDs)
├── engineering.yaml           (mixed: per-generator nameplate, derates, vintage)
├── operating_profile.yaml     (mixed: heat rates, DHTS, mode classifier)
├── market_context.yaml        (public: ISO zone, eGRID, RGGI, gas hub)
├── ltsa_terms.yaml            (personal: 7 LTSA streams + forced-outage table)
├── caveats.md                 (notes on what's baked into the data)
└── provenance.md              (source lineage per value)
```

If `ltsa_terms.yaml` is fully placeholder, that's a Step 1 gap to close. If scheduling configuration is missing, that's a Step 1 gap to close. The methodology can run on a partial Step 1 (with placeholders flagged), but the model output should be read with the corresponding caveats.

---

## §3. Step 2 — Identify the plant's operating regime(s)

### §3.1 What this step would do

A plant's **operating regime** is the *strategic operating posture* it is in — what it is trying to do under its market and contract context. Examples: baseload, peaker / load-follower, cogeneration, frequency regulation, must-run, hybrid.

Regime is **distinct from** the codebase's existing "mode" concepts (see `docs/discussion/01_regime_concept.md` §3 for the full distinction):

| Term | What it means | Decision cadence |
| :--- | :--- | :--- |
| **Operating mode** (3×CC / 2×CC / 1×CC) | A physical configuration | Hour-by-hour |
| **Policy mode** (A / B / C) | A modeling abstraction over operator behavior | Static per simulation |
| **Regime** | The strategic operating posture | Slow-changing (weeks to seasons) |

### §3.2 Current status — planned, not committed

**The regime concept is currently under discussion** and not yet a first-class part of the methodology. See [`docs/discussion/01_regime_concept.md`](../discussion/01_regime_concept.md) for the full exploration of what regime should mean, why it matters, and what would need to be true to commit to it.

In the flow as it stands today, Step 2 is **placeholder** — analyst-judged informal characterization until the regime concept graduates to methodology (via an ADR).

**Worked example — Lockport (informal characterization)**:

- Likely a **cogen + mid-merit hybrid** regime — DHTS-driven obligations bias toward 1×CC during low-LMP hours; the rest of dispatch follows merit-order economics.
- **Contested classification** — different analysts could reasonably argue cogen vs mid-merit vs seasonal-hybrid. See `docs/discussion/01_regime_concept.md` §5.5.
- **Implication for the model today**: regime-conditional calibration is not yet possible. The model uses a single global parameter set; per-regime parameters await regime concept commitment.

### §3.3 Why this step still belongs in the workflow even as a placeholder

It would be cleaner to leave Step 2 out of the workflow until regimes are committed. But that would hide a missing capability rather than name it. Naming it explicitly — even as "planned" — does three things:

1. Makes visible that the current model is *unconditional* on regime (and what that means for outputs)
2. Tells future readers where regime classification will eventually plug in
3. Prevents premature crystallization of regime as a first-class concept before the methodology is ready

When the discussion in `01_regime_concept.md` matures into an ADR, this section gets updated to reflect committed methodology.

---

## §4. Step 3 — Calibrate against history

### §4.1 What gets calibrated

Three categories of parameters need calibration to the specific asset:

| Category | Examples | Source for calibration |
| :--- | :--- | :--- |
| **Engineering parameters** | HR degradation rate, compressor fouling rate, EFOR baselines, EOH consumption rates | Historical operational data (MOR daily, SCADA where available); cross-reference with vendor / fleet defaults |
| **LTSA parameters** | Fixed monthly fee, EOH reserve rate, CI / MI costs, overage charges | Contract document extraction (personal data room) |
| **Dispatch parameters** | Spark-spread hurdle calibration, must-run flag thresholds, mode-pick logic | Historical dispatch patterns; per-regime once regime is committed |

The calibration step takes the configuration from Step 1 and the historical operational data, and *tunes* the model to match observed behavior. This is the bridge between "what the plant is" (configuration) and "what the plant does" (operations).

### §4.2 The backtest as the calibration check

A model isn't calibrated until you can **backtest it against actual operational outcomes**. The backtest answers: "Given the configuration and the calibrated parameters, does the model reproduce the observed dispatch + revenue + LTSA accruals over a historical period?"

If the answer is no, the calibration is incomplete or the model structure has gaps.

**Worked example — Lockport's backtest**:

- N5 notebook (`notebooks/05_model_vs_actual.ipynb`) compares model output against MOR-observed 2024 data
- **2.4× over-commit** — model dispatches ~468K MWh/year vs MOR's ~192K MWh/year
- Mode share divergence: model favors 3×CC and 1×CC; MOR shows real 2×CC use (26%) that the heuristic never picks
- Documented in `docs/methodology/extra/backtest_findings.md`
- The over-commit doesn't mean the model is "broken" — it means *known gaps exist* (no planned outages, no curtailment, synthetic must-run flag, no 2×CC heuristic). Each is a calibration gap, tracked in [`gaps_and_priorities.md`](gaps_and_priorities.md).

### §4.3 Calibration vs validation

These are distinct activities:

- **Calibration** is parameter-tuning to match historical data — happens during Step 3, modifies parameters
- **Validation** is *checking* whether the calibrated model produces reasonable outputs on held-out conditions — happens after calibration, doesn't modify parameters

The current Lockport workflow does both, but they are *not* clearly separated in the notebooks. A future improvement is to formalize the train/validate/test split (or rolling-origin validation per Hyndman's terminology).

---

## §5. Step 4 — Run the forward projection

### §5.1 What runs

The engine (described in detail in [`architecture.md`](architecture.md) §5) runs the calibrated model forward, day-by-day, hour-by-hour, across the projection horizon.

Key mechanics:

- **Daily loop** with 12 ordered steps (continuing outage check → forced outage Bernoulli → calendar maintenance → wear-penalty headroom → twin dispatch → cold-start warming gas → state commit → stress update → LTSA accrual). Full sequence in `architecture.md` §5.2.
- **Three policy modes (A / B / C)** run as independent simulations. Each has its own pre-built maintenance calendar. The policy-mode-as-bracketing posture is documented in [`extra/forward_looking_framing.md`](extra/forward_looking_framing.md).
- **Twin dispatch per day** — same hour-by-hour mechanic, run once with clean reference parameters and once with degraded parameters, so the difference is loss attribution. See `architecture.md` §5.2 step 5 and `extra/forward_looking_framing.md` §3.
- **Multiple market scenarios (planned)** — the v1 build uses historical replay (2017–2025 actual LMP, gas, weather). Phase L (Monte Carlo) replaces this with N forward-anchored synthetic paths from the scenario engine.

**Worked example — Lockport**:

- N4 runs 9-year × 3-mode simulation on historical replay (2017–2025)
- Generates per-day parquet outputs by mode (state trajectories, LTSA streams, inspection events, forced-outage events)
- Phase L (Monte Carlo) is the planned forward-looking extension; scenario engine machinery exists in `model-gpr` Step 1

### §5.2 Horizon choices

The projection horizon is a **methodological commitment**, not just a scope choice (see `framing_a_modeling_problem.md` §2 in the personal Learning folder):

| Horizon | Information available | Method |
| :--- | :--- | :--- |
| 1–3 years (primary deliverable) | Forward fuel curves, contracted PPA structure, plant nameplate, climatological inputs | Stochastic simulation on historical analogs; bounded projections |
| 5–10 years | Long-run trends; technology cost trajectories; broad climate signals | Scenario-based; sensitivity analysis |
| Project life (20–35 years) | Almost no specific information; structural priors only | Climate scenarios as inputs; wide brackets |

**Lockport's primary deliverable**: 1–3 year probabilistic revenue projection. Climate scenarios kept separate from base case.

### §5.3 The two-output view

The output of Step 4 is **the revenue arm only**. The hazard arm (EP curves, EAL, PML, BI metrics) is produced by a *separate team* via a separate IDF + fragility pipeline. See [`extra/gas_plant_workflow.md`](extra/gas_plant_workflow.md) §1.1 for the institutional split diagram.

This is important: gt_models doesn't pretend to do everything. It does the revenue arm well. The full risk + revenue deliverable composes the two arms at the portfolio level.

---

## §6. Step 5 — Propagate losses through the model

This is the step that traces each loss source through to its *revenue or cost impact*. The propagation chains are the mechanism by which physical or operational events become P&L lines.

### §6.1 The propagation chains

Five canonical chains, each tracing from a loss source to a terminal P&L impact:

#### Chain 1 — Compressor fouling → spark spread compression

```
   Operating hours accumulate
              │
              ▼
   Compressor fouling rises (exponential approach to asymptote)
              │
              ▼  (cleaning resets — currently not extracted; see Step 1 scheduling gap)
              │
   Effective heat rate ↑
              │
              ▼
   Fuel cost per MWh ↑
              │
              ▼
   Spark spread ↓
              │
              ▼
   Revenue: less attractive hours → fewer dispatch decisions
   OR forced dispatch → negative-margin MWh
              │
              ▼
   Daily margin ↓  →  Cumulative spark margin ↓
```

Implementation today: `state.fouling` accumulator in N4; FOULING_AQI_PROXY currently = 1.0 (no AQI adjustment).

#### Chain 2 — EOH consumption → inspection trigger → owner cost

```
   Fired hours + starts (weighted by start type)
              │
              ▼
   state.eoh advances
              │
              ▼
   Calendar shoulder-snap check (April / October) vs EOH threshold
              │
              ▼  (if at hard-stop overage: force immediate inspection)
              │
   CI or MI fires
              │
              ▼
   Owner-uncovered cost → ltsa_major_uncov (one of 7 LTSA streams)
              │
              ▼
   Plant offline 12 days (CI) or 52 days (MI)
              │
              ▼
   Revenue gap during outage + HR penalty if cycle-avg HR > guarantee
              │
              ▼
   P&L: $937K (CI) or $10.5M (MI) owner cost + revenue gap
```

Implementation today: `apply_inspection_reset()` in N4; calendar pre-builder per mode; hard-stop at +1,500 EOH overage. *Caveat*: known CI scheduler bug — CI never fires because YAML `eoh_threshold` is used as interval and tie-breaker hands all events to MI. See task history doc.

#### Chain 3 — Endogenous forced outage → revenue gap + repair cost

```
   Engineering state drives daily P_forced
              │
              ├──→ P_GT (combustion + TBC Weibull + rotor)
              ├──→ P_HRSG (baseline × age multiplier)
              └──→ P_BG (controls / generator / BOP × age)
              │
              ▼  P_total = 1 − (1−P_GT)(1−P_HRSG)(1−P_BG)
              │
   Bernoulli draw fires
              │
              ▼
   Cause sampled (weighted by component probs)
              │
              ├──→ GT in-scope: OEM-covered; $0 owner cost
              ├──→ HRSG: $500K owner-uncovered (placeholder)
              └──→ BOP: $750K owner-uncovered (placeholder)
              │
              ▼
   Outage duration sampled (lognormal: GT 8d / HRSG 12d / BOP 5d median)
              │
              ▼
   Revenue gap during outage + repair cost
```

Implementation today: `p_forced_components()` and `sample_outage_cause()` in N4.

#### Chain 4 — Cogen DHTS obligation → forced 1×CC at uneconomic hours

```
   Cogen must-run flag (currently synthetic: coldest 20% of days)
              │
              ▼
   Force 1×CC dispatch even when spark < 0
              │
              ▼
   Revenue collected at LMP × 1×CC capacity (123.9 MW)
   Fuel + VOM cost incurred
              │
              ▼  (1×CC has HR = 10,424 BTU/kWh, highest of three modes)
              │
   Spark spread typically negative on low-LMP cold days
              │
              ▼
   Forced losses → ~$20M of negative cumulative margin over 9 years
```

Implementation today: `must_run_days` flag in N4 based on temperature proxy. **Gap**: real DHTS schedule should come from MOR; not extracted.

#### Chain 5 — Climate scenario shift → derate + load + degradation amplification

```
   Climate scenario forecast (RCP 8.5 or analog)
              │
              ▼
   Ambient temperature distribution shifts higher
              │
              ├──→ Capacity derate (max output ↓ at high ambient)
              ├──→ Heat rate adjustment (efficiency drops with smaller Δt)
              └──→ Cycling stress amplification (higher load + higher ambient)
              │
              ▼
   On high-LMP hot days: less capacity to sell at peak prices
              │
              ▼
   Annual generation ↓ in scenario-shift years; degradation rate slightly ↑
              │
              ▼
   Long-horizon revenue trajectory bent down vs base case
```

Implementation today: ambient derate is wired (`ambient_derate_factor()` per generator). Load-and-temperature dependency for degradation is NOT yet wired (action item from 2026-05-22 meeting).

### §6.2 The mechanism inventory

A compact table mapping each loss type to its propagation path, terminal cost line, and implementation status:

| Loss source | Propagation path | Terminal P&L line | Status |
| :--- | :--- | :--- | :--- |
| Compressor fouling | → HR ↑ → spark ↓ | Spark margin ↓ | ✓ in CL det |
| HGP wear (recoverable) | → HR ↑ → spark ↓; partial reset at CI | Spark margin ↓ | ✓ in CL det |
| EOH consumption | → CI / MI trigger → owner cost + outage | LTSA owner uncov + revenue gap | ⚠ CI bug; otherwise ✓ |
| Endogenous EFOR | → outage → revenue gap + repair cost | Forced outage owner cost + revenue gap | ✓ in CL stoch |
| Heavy cycling | → start overage charges | Start overage stream | ✓ |
| Annual availability shortfall | → availability penalty | Availability penalty stream | ✓ |
| HR exceedance at cycle end | → HR penalty | HR penalty stream | ⚠ proxy biased |
| Cogen DHTS obligation | → forced uneconomic 1×CC | Negative spark on those hours | ⚠ synthetic proxy |
| Climate temp shift | → derate + degradation rate ↑ | Multi-pathway | ⚠ partial; load-temp deg not wired |
| EL hazards (storms, freeze, etc.) | → hazard team's pipeline | EP / EAL / PML | ⚙ hazard team scope |

`gas_plant_workflow.md` §3-§5 has the per-bucket detail; this section captures the *propagation flows* across buckets.

### §6.3 What's not yet fully captured

The chains above are the *modeled* propagations. Three real propagations are not yet wired:

- **Load + ambient temperature dependency on degradation** (Friday 2026-05-22 meeting action item; research paper referenced by Siddharth) — degradation today is mostly a function of fired hours; the chain "high-load operation + high ambient → accelerated stress → faster degradation" exists physically but isn't yet in the model
- **Regime-conditional behavior** — per `discussion/01_regime_concept.md`, regime conditions almost every parameter; until regime is committed, the model uses a global parameter set
- **Scheduled mitigations** — cleaning, water washes, planned inspections per the plant's actual schedule. The "5% recovery per monthly wash" pattern Siddharth suggested isn't yet wired because the schedule data isn't extracted (Step 1 scheduling gap)

These are documented as gaps in [`gaps_and_priorities.md`](gaps_and_priorities.md) and the latest task-history handoff.

---

## §7. Step 6 — Produce the deliverable

### §7.1 The `model_card.md`

The headline deliverable per simulation run. Auto-generated by N4. Structure:

```
1. Run metadata          — asset, window, seed, dates
2. Data spine vintages   — which parquet was loaded, when refreshed
3. Assumption distribution — 268 leaves: 80% real_* / 17.5% placeholder breakdown
4. Mode comparison       — spark / LTSA / Net P&L per mode + A→C delta
5. LTSA stream breakdown — where the cost went, for Mode A
6. Backtest vs MOR       — 2024 generation, mode dist, cold-start frequency
7. Caveats              — known limitations of v1
8. Phase L roadmap      — what Monte Carlo would extend
9. Output artifacts     — paths to the parquets
```

The model_card is the *single sheet a reviewer reads first*. Everything else in the run bundle supports it.

**Worked example — Lockport latest run**: `data/outputs/lockport/runs/notebook4_20260515_002901/model_card.md`.

### §7.2 The parquet bundle

Per simulation run, the bundle contains:

```
data/outputs/<asset>/runs/notebook4_<timestamp>/
├── model_card.md
├── run_config.yaml                      (reproducibility config)
├── daily_summary_mode_{a,b,c}.parquet   (full daily record per mode)
├── state_trajectory_mode_{a,b,c}.parquet (engineering state columns)
├── ltsa_streams_mode_{a,b,c}.parquet    (8 cumulative cost streams)
├── inspection_events.parquet            (CI / MI events across all modes)
└── forced_outage_events.parquet         (forced events across all modes)
```

Downstream analysis pivots on these parquets — quarterly attribution, per-stream cost allocation, mode comparisons, scenario sensitivity studies.

### §7.3 The audit trail

Every value in the model_card is traceable through the status taxonomy, the caveats document, and the provenance document. A reader can ask "where does this number come from?" and follow the trail.

This is the workflow's defensibility property. A model whose values can't be traced is a model that can't be defended in review. The status taxonomy + caveats + provenance trio make the model defensible by construction.

---

## §8. Generalizing to a new gas plant

If a new asset arrives — call it Plant Y — the workflow is the same. Only the data changes.

### §8.1 The asset-onboarding sequence

```
1. Stand up data/assets/plant_y/
   ├── identity.yaml          (from EIA-860 / ORISPL lookup)
   ├── engineering.yaml       (from EIA-860 + vendor specs)
   ├── market_context.yaml    (from ISO + RGGI / eGRID lookup)
   ├── operating_profile.yaml (from MOR extraction)
   └── ltsa_terms.yaml        (placeholders until data room extracted)

2. Stand up data/paths/plant_y/
   ├── lmp_da_hourly.parquet  (from ISO data pull)
   ├── gas_price_history.parquet (from EIA + ISO basis)
   ├── weather_hourly.parquet (from Open-Meteo / NOAA at plant lat/lon)
   └── mor_daily.parquet      (from diligence extraction)

3. Run N1 (data spine validation) for plant_y
4. Adjust per-asset calibration (real_observed values replace defaults)
5. Run N4 with plant_y configuration
6. Verify backtest against plant_y's MOR
7. Iterate on calibration if backtest divergence is large
```

The methodology code in `notebooks/` doesn't change. The methodology docs don't change. Only:

- Per-asset YAML files
- Per-asset time series
- Per-asset caveats and provenance

This separation between **code** (which is asset-agnostic) and **data** (which is per-asset) is the property that makes the framework generalizable. Lockport happens to be the first asset; Plant Y, Z, etc. would follow the same flow.

### §8.2 What might break for a different asset

Some asset characteristics could expose limitations in the methodology:

| Asset characteristic | What might need adaptation |
| :--- | :--- |
| Different prime mover (e.g., aero-derivative) | Different tech-class defaults; possibly different start-cost / EOH treatment |
| Different configuration (e.g., 2×1 instead of 3×1) | Mode definitions need updating; capacities and heat rates re-derived |
| Different contract structure (e.g., tolling vs merchant) | `ltsa_terms.yaml` schema may need extension; revenue side may shift |
| Different region (e.g., ERCOT instead of NYISO) | `market_context.yaml` lookup tables; possibly different hazard correlations on the risk-arm side |
| Different vintage / life-stage | Initial state vector tuning; possibly different policy mode emphasis |

None of these is an architectural break — each is an extension within the existing framework. The framework's generality is *robust to asset variation*; what it's not generalizable to is *different asset classes* (battery storage, wind, solar) — those need their own methodology, even if some primitives can be shared.

---

## §9. Cross-references

This doc connects to many others. Map for navigation:

| Doc | Relationship to this flow doc |
| :--- | :--- |
| [`architecture.md`](architecture.md) | What this flow's Step 4 (forward projection) does internally — the engine mechanics |
| [`dispatch_mechanics.md`](dispatch_mechanics.md) | Operating mode × policy mode interaction — Step 4 detail |
| [`pnl_ledger.md`](pnl_ledger.md) | Economic ledger — Step 6 detail |
| [`gaps_and_priorities.md`](gaps_and_priorities.md) | What's missing across the workflow + v2 priority list |
| [`glossary.md`](glossary.md) | Term definitions used across the flow |
| [`extra/gas_plant_workflow.md`](extra/gas_plant_workflow.md) | The Max − CL − EL decomposition lens; underlies Steps 5 and 6 |
| [`extra/forward_looking_framing.md`](extra/forward_looking_framing.md) | Positioning for Step 4 — why the model brackets operator policy |
| [`extra/performance_and_risk_framework.md`](extra/performance_and_risk_framework.md) | Generic framework that underlies the gas-specific flow |
| [`extra/backtest_findings.md`](extra/backtest_findings.md) | Step 3 calibration check for Lockport |
| [`../decisions/`](../decisions/) | ADRs for choices made in the flow (gas hub, calibration buckets) |
| [`../discussion/01_regime_concept.md`](../discussion/01_regime_concept.md) | What Step 2 will eventually be — currently in discussion |
| [`../assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md) | The status codes underlying Step 1's audit trail |
| [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) | The phased build plan (A–L) that produced this asset-level workflow |

For the upstream generic discipline of *what to scope before modeling any asset*, see `framing_a_modeling_problem.md` in the personal Learning knowledge base (not in this repo).

---

## §10. What this doc deliberately does not do

To preempt scope confusion:

- **Does not replace `architecture.md`** — the engine's mechanics live there. This doc orients; that doc explains.
- **Does not define regime** — regime is still in discussion. This doc names Step 2 and points to the discussion doc.
- **Does not include the risk arm** — the hazard team's IDF + fragility pipeline is out of gt_models scope. Step 5 mentions it only as the EL row.
- **Does not validate the model** — validation (N5 + model_card backtest) is a downstream concern; this doc points to where it lives.
- **Does not write the ADR for any of the open choices** — discussion comes first (in `discussion/`), then ADR (in `decisions/`), then methodology updates back here.

The doc is a navigational artifact, not a substantive one. Its value is making the workflow visible top-down. The substantive work happens in the docs and code it references.

---

## §11. Closing — when to update this doc

Update this doc when:

- A new step is introduced (e.g., when regime classification graduates from discussion to methodology, §3 gets rewritten)
- A workflow step changes shape (e.g., when Phase L scenario engine wires in, §5.1 needs updating)
- A new asset's onboarding reveals a gap in §8 (e.g., a tolling-contract asset reveals that `ltsa_terms.yaml` schema needs extension)
- A propagation chain becomes obsolete or a new one is added (§6)

Don't update this doc for:

- Routine calibration improvements (those live in the run-bundle model_cards)
- Notebook refactoring (no impact on the workflow)
- New analytical companions (those go in `extra/`)

This doc is the *project flow*. It changes when the *flow* changes, not when individual components change.
