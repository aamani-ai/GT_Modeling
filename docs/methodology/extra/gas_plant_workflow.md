# Gas Plant Modeling Workflow

> **Purpose**: A navigational ASCII flowchart for thinking through gas-fired generation modeling, using the conceptual framework `Output = Max − CL − EL` plus routing, policy mode, and horizon discipline. Applied to gas specifically.
>
> **Scope**: this doc focuses specifically on the **gas-revenue-projection arm** of the broader risk framework — what `gt_models` produces. The risk arm (hazard catalog, EP / EAL / PML, BI metrics) is owned by a separate team via a different pipeline. EL items appear in the routing tables below for *decomposition completeness*, but their actual modeling is deliberately out of scope here. See §1.1 for the institutional split and the InfraSure risk-spine doc (`the_risk_spine.md`) for the full revenue + risk composition picture.
>
> **Why this exists**: Gas plant modeling components get mixed up in practice — economic curtailment booked as a loss, EL events lumped with CL stochastic, policy mode hidden inside parameter fits, single-horizon analysis claimed as both pro forma and risk. This doc separates them visually so each component can be placed and routed deliberately.
>
> **Companion to**: [`forward_looking_framing.md`](forward_looking_framing.md) (the *why*) and the framework reference doc (the generic version that covers all asset types).
>
> **Not a code structure.** This is a way of thinking. The code in `gt_models` does not have a literal `Max − CL − EL` line of arithmetic; the decomposition is implicit in its architecture. Use this doc to *think clearly* about what's where, not to refactor the code.
>
> **Architecture as scaffolding, not constraint.** The buckets, routing rules, and workflow ordering below are tools that catch common errors. They are not a specification to implement faithfully. In practice you will find components that fit imperfectly, routing decisions that aren't crisp, and transition layers that have gaps — these are normal. Document deviations as you encounter them; the deviation log is often more valuable than framework adherence. The decomposition is a starting position, the modeling work is the destination, and the two are in dialogue throughout. See [`performance_and_risk_framework.md`](performance_and_risk_framework.md) (posture note at top) and `the_risk_spine.md` §11 for the canonical version of this principle.

---

## §1. The big picture

```
                    ┌──────────────────────────────────┐
                    │  THE GAS PLANT AS AN ASSET       │
                    │  (e.g. Lockport 3-on-1 CCGT,     │
                    │   221 MW, NYISO Zone A)          │
                    └────────────┬─────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────┐
                  │  CONDITIONED BY POLICY MODE π   │
                  │  (latent — inferred, not given) │
                  └────────────┬────────────────────┘
                               │
                               ▼
   ┌───────────────────────────────────────────────────────────────┐
   │  OUTPUT DECOMPOSITION                                         │
   │                                                               │
   │    Output(t | π) =  Max(t | π)  −  CL(t | π)  −  EL(t | π)    │
   │                                                               │
   │    "what the plant   "what caps   "what chips   "what KOs     │
   │     produces this    it at this   away every    it in         │
   │     timestep"        timestep"    timestep"     discrete      │
   │                                                  shocks"      │
   └────────┬──────────────────┬─────────────────┬─────────────────┘
            │                  │                 │
            ▼                  ▼                 ▼
       [§2 Max]           [§3 CL]            [§4 EL]
            │                  │                 │
            └──────────┬───────┴─────────┬───────┘
                       ▼                 ▼
            ┌──────────────────────────────────────┐
            │  ROUTING / CONVICTION TEST           │
            │  For each component, ask:            │
            │   1. Horizon vs. recurrence?         │
            │   2. Stationarity?                   │
            │   3. Data quality (and policy mode)? │
            │   4. Correlation structure known?    │
            └────────────────┬─────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       [HIGH CONV.]   [GRAY AREA]     [LOW / TAIL]
        revenue+risk  case-by-case    risk only
              │              │              │
              └──────────────┴──────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
   ┌───────────────────┐         ┌────────────────────┐
   │ REVENUE PROJECTION│         │  RISK METRICS      │
   │                   │         │                    │
   │ Output × Price    │         │ EP curve           │
   │ + ancillary       │         │ EAL / AAL          │
   │ + capacity pmt    │         │ PML (1-in-N)       │
   │ − O&M             │         │ VaR / CVaR         │
   │ − LTSA            │         │ Scenario stress    │
   │                   │         │                    │
   │ → P&L, NPV,       │         │ → portfolio risk,  │
   │   pro forma       │         │   capital,         │
   │                   │         │   reinsurance need │
   └─────────┬─────────┘         └─────────┬──────────┘
             │                             │
             └──────────────┬──────────────┘
                            ▼
              ┌─────────────────────────────┐
              │  DECISION-READY VIEW        │
              │                             │
              │  • Expected NPV ± P10/P90   │
              │  • Risk-adjusted return     │
              │  • Tail exposure            │
              │  • Hedge / insurance need   │
              └─────────────────────────────┘
```

---

## §1.1. Institutional scope — gt_models is the revenue arm only

Within InfraSure, the framework's two output arms are owned by different teams. This affects how to read the rest of this doc:

```
                ┌───────────────────────────────────────────────┐
                │       ASSET-LEVEL DELIVERABLE                  │
                └─────────────────────┬─────────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                ▼                                           ▼
   ┌──────────────────────────┐         ┌────────────────────────────┐
   │  gt_models (THIS repo)   │         │  Hazard team (separate)    │
   │                          │         │                            │
   │  Scope: generation       │         │  Scope: event loss from    │
   │  revenue probabilistic   │         │  hazards (EL)              │
   │  paths                   │         │                            │
   │                          │         │  Two-phase pipeline:       │
   │  Covers:                 │         │   1. Hazard IDF (intensity │
   │   ▸ Max                  │         │      / duration / freq)    │
   │   ▸ CL deterministic     │         │   2. Fragility / damage    │
   │   ▸ CL stochastic        │         │      curve per asset       │
   │   ▸ CL step              │         │                            │
   │                          │         │  Output: EP curve, EAL,    │
   │  Output: P10/P50/P90     │         │  PML — feeds to portfolio  │
   │  of spark margin −       │         │  risk artifact             │
   │  LTSA cost (revenue arm) │         │                            │
   └──────────┬───────────────┘         └──────────────┬─────────────┘
              │                                        │
              └────────────────┬───────────────────────┘
                               ▼
                  Portfolio / asset-evaluation
                  combination (revenue +
                  hazard-adjusted risk)
```

**Key implication for this doc**:

EL events are NOT "missing" from gt_models. They are deliberately scoped to the hazard team's separate two-phase pipeline (IDF + fragility / damage curves). The two arms compose at the portfolio level, not within either codebase.

This scope statement shapes how to read what follows:

- **§4 (EL)** lists what the hazard team covers, for completeness of the decomposition picture. It is NOT a roadmap of work for gt_models.
- **§8 (implementation status)** marks EL components as `⚙` (hazard-team scope), not `❌` (missing).
- The framework's "two-output view" (revenue + risk) is realized at the **organizational level**, not within a single codebase.

---

## §2. Max(t | π) — the ceiling on what the plant can produce

This is the *most-confused* part of gas modeling. Economic non-dispatch is NOT a loss — it lives here.

```
Max(t) for a gas plant comprises three sub-categories:

   ┌──────────────────────────────────────────────────────────────┐
   │  PHYSICS-BOUND (constrains the asset's capability)           │
   │                                                              │
   │  ▸ Nameplate capacity                                        │
   │  ▸ Ambient temperature derate                                │
   │  ▸ Station service load                                      │
   │  ▸ Min stable load / max load                                │
   │  ▸ Ramp rate limits                                          │
   └──────────────────────────────────────────────────────────────┘
                              ⊕
   ┌──────────────────────────────────────────────────────────────┐
   │  ECONOMIC-BOUND (constrains when it actually runs)           │
   │                                                              │
   │  ▸ Spark spread > VOM + start_cost_amort?  (commit/decommit) │
   │  ▸ Mode pick: 3×CC vs 2×CC vs 1×CC                           │
   │  ▸ LMP forecast horizon (offer floor logic)                  │
   │  ▸ Wear-penalty hurdle (policy-mode dependent)               │
   │                                                              │
   │  ★ THE COMMON MISTAKE: booking economic non-dispatch as      │
   │    a "loss" or "curtailment." It is NOT a loss — it is the   │
   │    operator's correct decision under negative spark.         │
   └──────────────────────────────────────────────────────────────┘
                              ⊕
   ┌──────────────────────────────────────────────────────────────┐
   │  CONTRACT-BOUND (overrides physics + economic)               │
   │                                                              │
   │  ▸ Must-run obligation (cogen DHTS, PPA, capacity-firm)      │
   │  ▸ PPA cap (when binding)                                    │
   │  ▸ Tolling counterparty dispatch direction                   │
   │  ▸ Capacity-firm availability commitment                     │
   └──────────────────────────────────────────────────────────────┘

   →  EconomicMax(t) = Max(t)  IF  spark > VOM + start_amort
                       ELSE   0   (or min-load if must-run)

         For revenue modeling: use EconomicMax(t).
         The gap from physical Max to EconomicMax is NOT a loss.
         It is the dispatch decision (a feature, not a bug).
```

---

## §3. CL(t | π) — continuous losses (chip-away)

Three sub-flavors, all in CL, but each with a different modeling treatment.

```
   ┌────────────────────────────────────────────────────────────┐
   │  CL — DETERMINISTIC                                        │
   │  (curve applied each timestep; predictable trajectory)     │
   │                                                            │
   │  ▸ Heat rate degradation between MIs                       │
   │    - Sawtooth: drifts up, resets at each MI                │
   │    - HGP wear, compressor fouling                          │
   │  ▸ Non-recoverable HR floor (HRSG / BOP)                   │
   │    - Permanent; only resets at major overhaul              │
   │  ▸ Compressor erosion (non-recoverable)                    │
   └────────────────────────────────────────────────────────────┘
                                ⊕
   ┌────────────────────────────────────────────────────────────┐
   │  CL — STOCHASTIC                                           │
   │  (distribution sampled each timestep; daily-ish variance)  │
   │                                                            │
   │  ▸ EFOR / small forced outages (≤ 24h, repaired in-house)  │
   │  ▸ Endogenous P_forced from engineering state:             │
   │      P_GT   = P_comb(D_f) + P_TBC(t) + P_rotor             │
   │      P_HRSG = baseline × age_mult                          │
   │      P_BG   = baseline × age_mult                          │
   │  ▸ Availability variance                                   │
   │  ▸ Baseline congestion (if site has chronic TX limit)      │
   └────────────────────────────────────────────────────────────┘
                                ⊕
   ┌────────────────────────────────────────────────────────────┐
   │  CL — STEP                                                 │
   │  (scheduled / triggered discrete events; multi-day outage) │
   │                                                            │
   │  ▸ LTSA Combustion Inspection (CI)                         │
   │    - Triggered at EOH threshold (or calendar shoulder snap)│
   │    - ~12 days outage, ~$3-4M total cost                    │
   │  ▸ LTSA Major Inspection (MI)                              │
   │    - ~52 days outage, ~$25-30M total cost                  │
   │  ▸ Hot Gas Path inspection (HGP) — sometimes               │
   │  ▸ Boiler / transformer replacement (if applicable)        │
   │                                                            │
   │  ★ STATE RESETS at each step event (key mechanic)          │
   │    - CI: partial reset of dc, df, fouling, hr_recov        │
   │    - MI: stronger reset, plus tbc_thresh resampled         │
   └────────────────────────────────────────────────────────────┘
```

---

## §4. EL(t | π) — event losses (discrete shocks)

**These are hazard-team scope, not gt_models scope** (per §1.1). The hazard team handles EL through a separate two-phase pipeline (IDF + fragility / damage curves). The list below documents what their catalog covers for a NYISO Zone A gas asset — included here so the revenue/risk decomposition stays complete *in this doc*, not because gt_models needs to implement any of it.

```
EL for a gas plant in NYISO Zone A (Lockport region):

   ┌────────────────────────────────────────────────────────────┐
   │  WEATHER / CLIMATE HAZARDS                                 │
   │                                                            │
   │  ▸ Polar vortex / extreme cold (Uri-class)                 │
   │    - Most important for Northeast gas — correlated         │
   │      regional risk, fat-tailed                             │
   │  ▸ Ice storm (TX damage + plant freeze)                    │
   │  ▸ Lake-effect blizzard (TX, plant access)                 │
   │  ▸ Wildfire smoke (intake filtration, output derate)       │
   │  ▸ Lightning strikes (transformer / switchyard)            │
   │  ▸ Flood (low-elevation gas handling, transformer pad)     │
   └────────────────────────────────────────────────────────────┘
                                ⊕
   ┌────────────────────────────────────────────────────────────┐
   │  FUEL / SUPPLY HAZARDS                                     │
   │                                                            │
   │  ▸ Gas supply interruption (TGP Zone 6 pipeline FM)        │
   │  ▸ Compressor station outage upstream                      │
   │  ▸ Algonquin / NEMP basis spike (price-side shock)         │
   │  ▸ Dual-fuel switch failure (when applicable)              │
   └────────────────────────────────────────────────────────────┘
                                ⊕
   ┌────────────────────────────────────────────────────────────┐
   │  GRID HAZARDS                                              │
   │                                                            │
   │  ▸ Transmission line trip (forced curtailment)             │
   │  ▸ NYISO emergency directive                               │
   │  ▸ Voltage / frequency event                               │
   │  ▸ Substation fault                                        │
   └────────────────────────────────────────────────────────────┘
                                ⊕
   ┌────────────────────────────────────────────────────────────┐
   │  OPERATIONAL HAZARDS (catastrophic, not routine)           │
   │                                                            │
   │  ▸ Large mechanical forced outage (gen trip, blade failure)│
   │  ▸ HRSG tube rupture                                       │
   │  ▸ Transformer fire                                        │
   │  ▸ Generator stator failure                                │
   │  ▸ Foreign object damage in turbine                        │
   └────────────────────────────────────────────────────────────┘

   These compose into the hazard team's HAZARD CATALOG (frequency
   × severity per peril) which feeds the risk-metrics layer of the
   asset-level deliverable. Out of gt_models scope per §1.1.
```

---

## §5. Policy mode π — the latent conditioner

```
Policy mode π is NOT a top-level axis. It conditions the
parameters of Max, CL, and EL simultaneously.

                   ┌───────────────────────────┐
                   │  Policy mode π (latent)   │
                   │  inferred from:           │
                   │   ▸ Dispatch logs         │
                   │   ▸ Maintenance records   │
                   │   ▸ Capacity factor       │
                   │   ▸ Start frequency       │
                   │   ▸ Contract structure    │
                   │     (LTSA, PPA, tolling)  │
                   └─────────────┬─────────────┘
                                 │ touches simultaneously
              ┌──────────────────┼─────────────────┐
              ▼                  ▼                 ▼
   ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐
   │  Max(π)        │  │  CL(π)           │  │  EL(π)         │
   │                │  │                  │  │                │
   │ ▸ Hurdle rate  │  │ ▸ Wear rate per  │  │ ▸ Exposure to  │
   │ ▸ Mode pick    │  │   fired hour     │  │   freeze (lower│
   │ ▸ When to start│  │ ▸ EOH per start  │  │   for peaker — │
   │ ▸ Self-curtail │  │ ▸ EFOR baseline  │  │   runs less)   │
   │   near insp.   │  │ ▸ MI interval    │  │ ▸ Tail risk    │
   │                │  │   timing         │  │ ▸ Catastrophic │
   │                │  │ ▸ HRSG cycling   │  │   outage corr. │
   └────────────────┘  └──────────────────┘  └────────────────┘

The policy-mode SPECTRUM (gas — modal range is WIDE):

  Revenue-max  ◄──────────────────────────────────────►  Asset-preservation
  "Run hard"                                            "Protect hardware"
  ▸ Take every $$$ hour                                ▸ Skip marginal starts
  ▸ Ignore EOH proximity                               ▸ Self-curtail near MI
  ▸ LTSA = overhead                                    ▸ LTSA = main lever
  ▸ Earlier MI events                                  ▸ Push MI events out
  ▸ Higher EL exposure (more uptime)                   ▸ Lower EL exposure
  ▸ Higher gross revenue                               ▸ Lower wear cost

gt_models brackets this with three discrete bookends:
    Mode A  (revenue-max bookend)
    Mode B  (heuristic middle)
    Mode C  (asset-preservation bookend)

Real operator lives somewhere INSIDE the bracket — position varies
day-by-day, shaped by market conditions + contract + portfolio context.
```

### Why policy mode is so wide for gas (vs. solar, wind, BESS)

```
   Asset    Decision cadence      Modal range      Importance
   ──────   ─────────────────     ────────────     ──────────────
   Gas      Continuous (hourly)   Wide (10-30%)    HIGHEST
   BESS     Continuous (cycle)    Wide (10-25%)    Very high
   Wind     Periodic (config)     Medium (3-7%)    Moderate
   Solar    Set-and-forget        Narrow (1-2%)    Low

Gas has the widest modal range AND the highest decision cadence — the
operator is constantly trading near-term revenue against long-term wear.
Solar by contrast has near-zero modal range because the operator has
near-zero dispatch discretion.

This is why bracketing matters most for gas and why the framework
flags "policy mode error" as the most common pro forma mistake for
gas after the economic-curtailment-as-loss mistake.
```

---

## §6. Routing table — where each component lives

Letters: `R` = revenue projection; `K` = risk metrics; `B` = both (mean → revenue, distribution → risk).

```
┌──────────────────────────────────────────┬──────────────┬─────────┐
│ Component                                 │ Bucket       │ Route   │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ Ambient temperature derate                │ Max          │ R       │
│ Nameplate capacity                        │ Max          │ R       │
│ Station service                           │ Max          │ R       │
│ Ramp rate limits                          │ Max          │ R       │
│ Economic dispatch decision                │ Max          │ R       │
│ PPA cap (when binding)                    │ Max          │ R       │
│ Must-run / cogen DHTS                     │ Max          │ R       │
│ Tolling counterparty dispatch             │ Max          │ R       │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ Heat rate degradation (between MIs)       │ CL det.      │ R       │
│ Non-recoverable HR floor                  │ CL det.      │ R       │
│ Compressor erosion                        │ CL det.      │ R       │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ EFOR / small forced outage                │ CL stoch.    │ B       │
│ Endogenous P_forced (state-driven)        │ CL stoch.    │ B       │
│ Baseline congestion (if chronic)          │ CL stoch.    │ B       │
│ Availability variance                     │ CL stoch.    │ B       │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ LTSA CI (Combustion Inspection)           │ CL step      │ R       │
│ LTSA MI (Major Inspection)                │ CL step      │ R       │
│ Heat rate reset at MI                     │ CL step      │ R       │
│ Boiler/transformer replacement            │ CL step      │ R       │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ Polar vortex / freeze (Uri-class)         │ EL           │ K       │
│ Ice storm                                 │ EL           │ K       │
│ Lake-effect blizzard                      │ EL           │ K       │
│ Lightning / transformer fire              │ EL           │ K       │
│ Flood                                     │ EL           │ K       │
│ Gas supply interruption (TGP Zone 6)      │ EL           │ K       │
│ Compressor station outage upstream        │ EL           │ K       │
│ Algonquin basis spike                     │ EL           │ K       │
│   (becomes B at long horizon if SCVR ok)  │              │         │
│ Transmission line trip                    │ EL           │ K       │
│ NYISO emergency directive                 │ EL           │ K       │
│ Large mechanical forced outage            │ EL           │ K       │
│ HRSG tube rupture                         │ EL           │ K       │
│ Wildfire smoke (derate, not outage)       │ EL           │ B       │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ PPA counterparty default                  │ EL contract. │ K       │
│ Force majeure                             │ EL contract. │ K       │
│ Regulatory shutdown                       │ EL contract. │ K       │
├──────────────────────────────────────────┼──────────────┼─────────┤
│ BI insurance premium                      │ CL det.      │ R       │
│ BI insurance payout (covered EL)          │ Contractual  │ net → R │
│                                           │ offset on EL │ gross→K │
└──────────────────────────────────────────┴──────────────┴─────────┘
```

**Note**: BI itself is not in this table — it is the *consequential aggregate* across the CL + EL + contractual-EL rows above, not a routable component. See §6.5 for the attribution view.

---

## §6.5. BI as a cross-cutting attribution view (not a fourth bucket)

The framework's `Max − CL − EL` decomposition is *causal*. **Business Interruption (BI)** is *consequential* — it measures the dollar revenue impact of output loss, aggregated across all causal buckets. BI is not a fourth row in the routing table; it sits on top of the routing table as an attribution view.

### What contributes to BI for a gas plant

```
BI(t) = Σ (output_gap × price)
      = degradation contribution         (CL det)
      + small forced outage contribution (CL stoch)
      + planned inspection contribution  (CL step)
      + EL hazard contribution           (EL)
      + contractual / counterparty       (EL contractual)

NOT in BI:
   ▸ Economic non-dispatch     (that's a Max constraint, not loss)
   ▸ Policy self-curtailment   (operator choice — Modes B/C deferring
                                wear — not a loss)
```

### Where each BI contribution lives institutionally

| Cause | Where it's computed | gt_models status |
| :--- | :--- | :--- |
| CL det (HR drift, fouling) | gt_models | ✓ via `loss_degradation` |
| CL stoch (small forced outage) | gt_models | ✓ via `loss_forced` |
| CL step (CI / MI outage) | gt_models | ✓ via `loss_planned` |
| EL (weather, fuel, grid hazards) | hazard team | ⚙ separate pipeline |
| Contractual EL (PPA default etc.) | currently nobody | (real gap — portfolio scope) |

### Insurance interaction (BI policy specifically)

- **BI premium** — continuous cost; CL deterministic; would live in gt_models's Fixed O&M line if that existed (currently not modeled in v1).
- **BI payout** — event-triggered recovery against covered EL causes; modifies the *net* EL loss feeding the revenue arm; *gross* EL loss still feeds the hazard team's risk artifact. Out of gt_models scope.

### Why this is worth pinning down

The twin-dispatch loss-attribution columns gt_models already produces (`loss_degradation`, `loss_planned`, `loss_forced`) are **exactly the CL contributions to BI**. If a colleague asks "where is BI in your model?" — the answer is:

> *The CL portion is already in the loss-attribution columns; the EL portion comes from the hazard team's pipeline; combined BI is the asset-level deliverable. BI itself is not a row in the model — it is a reporting view on top of the loss decomposition.*

See [`performance_and_risk_framework.md`](performance_and_risk_framework.md) §1 (*Causal decomposition vs. consequential measurement*) for the generic framework treatment.

---

## §7. Horizon discipline — what changes with the time window

```
                  1-3 yrs               5-10 yrs             Project life
                  ────────              ─────────             ──────────────
                  (DD / DA)             (PPA term /           (full equity
                                        refinancing)          life: 20-35 yr)

Revenue line     Max − CL only          Max − CL,            Max − CL − EAL
                 (det + expected        fold in expected      (long-run avg
                  stochastic)           EL where stationary    honest here)
                                        (SCVR/HCR support)

Risk metrics    Full EL distribution    Full distribution    EP curve, EAL,
                CL variance             EL crossing into     PML, VaR, CVaR;
                Named events            revenue with risk    non-stationary
                Scenario stress         support;             hazards STILL
                VaR/CVaR                report range         risk-only

Common mistake  Applying long-horizon   Treating EL fit as   Folding ALL EL
                EAL to short-horizon    stationary when      into central
                forecast (the most      underlying process   forecast (loses
                common pro forma error) has regime shift     distributional
                                        potential            information)
```

### The big takeaway

A component that fails the conviction test **stays in the risk layer at every horizon** — even at 35 years. Sparse-data or non-stationary hazards don't earn their way into the revenue line just because the horizon is long.

---

## §8. Where gt_models lives in this workflow

The practical bridge: which framework concepts are implemented today, which are partial, which are missing.

```
┌─────────────────────────┬─────────────────┬─────────────────────┐
│ Framework concept       │ gt_models       │ Where it lives in   │
│                         │ status          │ the code (file/§)   │
├─────────────────────────┼─────────────────┼─────────────────────┤
│ Max — physics bound     │ ✓ implemented   │ N4 cap_eff_for_mode │
│ Max — ambient derate    │ ✓ implemented   │ N4 ambient_derate_..│
│ Max — economic dispatch │ ✓ implemented   │ N4 dispatch_day_..  │
│ Max — must-run override │ ⚠ synthetic     │ N4 must_run_days    │
│                         │   (temp proxy)  │                     │
│ Max — PPA cap           │ ⚠ unmodeled     │ —                   │
│ Max — tolling           │ ⚠ unmodeled     │ —                   │
├─────────────────────────┼─────────────────┼─────────────────────┤
│ CL det — HR drift       │ ✓ implemented   │ N4 hr_degraded_..   │
│ CL det — fouling        │ ✓ implemented   │ N4 update_stress    │
│ CL det — HR reset @ MI  │ ✓ implemented   │ N4 apply_inspection │
│ CL stoch — EFOR         │ ✓ endogenous    │ N4 p_forced_compon. │
│ CL stoch — congestion   │ ⚠ unmodeled     │ —                   │
│ CL step — CI            │ ⚠ BUGGY         │ N4 build_maint_sch. │
│                         │   (never fires) │   findings #1       │
│ CL step — MI            │ ✓ implemented   │ N4 build_maint_sch. │
├─────────────────────────┼─────────────────┼─────────────────────┤
│ EL — polar vortex       │ ⚙ hazard team   │ separate IDF +      │
│                         │                 │   fragility pipeline│
│ EL — ice storm          │ ⚙ hazard team   │ separate pipeline   │
│ EL — gas supply intr.   │ ⚙ hazard team   │ separate pipeline   │
│ EL — lightning / fire   │ ⚙ hazard team   │ separate pipeline   │
│ EL — flood              │ ⚙ hazard team   │ separate pipeline   │
│ EL — grid emergency     │ ⚙ hazard team   │ separate pipeline   │
│ EL — catastrophic mech  │ ⚙ hazard team   │ separate pipeline   │
│   outage (tail)         │                 │   (small/med mech   │
│                         │                 │   in CL stoch EFOR) │
├─────────────────────────┼─────────────────┼─────────────────────┤
│ Policy mode bracketing  │ ✓ A/B/C         │ N4 wear_penalty_..  │
│ Policy mode inference   │ ❌ not done     │ —                   │
├─────────────────────────┼─────────────────┼─────────────────────┤
│ Conviction test routing │ ❌ no discipline│ —                   │
│ Revenue projection      │ ✓ produced      │ model_card.md       │
│ Risk metrics suite      │ ⚙ hazard team   │ separate pipeline   │
│   (EP, EAL, PML,        │                 │   (out of gt_models │
│    VaR, CVaR)           │                 │   scope per §1.1)   │
│ Horizon-conditional     │ ❌ single horiz │ —                   │
│   reporting             │                 │                     │
└─────────────────────────┴─────────────────┴─────────────────────┘

Legend:
  ✓ = implemented in gt_models, working
  ⚠ = partial / has known issue in gt_models
  ❌ = in gt_models scope, not done
  ⚙ = out of gt_models scope; owned by hazard team (per §1.1)
```

### What §8 tells you at a glance

- **Max layer**: mostly solid; small gaps around contract types (PPA cap, tolling) and a known weak link in the synthetic must-run proxy.
- **CL layer**: solid in concept; one real bug (CI scheduler) and one known proxy bias (HR guarantee).
- **EL layer**: scoped to the hazard team's separate IDF + fragility pipeline (per §1.1). Not a gap; not in gt_models scope.
- **Policy mode**: implemented as bracketing (A/B/C); not yet implemented as inference.
- **Risk-metrics arm**: produced by the hazard team's pipeline, not gt_models. gt_models is the revenue arm.

---

## §9. How to use this doc

Three practical uses:

**1. When categorizing a new component.** Whenever a new modeling consideration comes up ("should we model wildfire smoke?"), trace it through:

```
   ▸ Which bucket: Max / CL det / CL stoch / CL step / EL?
   ▸ Which route: R / K / B?
   ▸ At what horizon does it matter?
   ▸ Does it interact with policy mode?
   ▸ Where does it land in the §6 routing table?
```

**2. When auditing existing modeling decisions.** Use §8 as a checklist. The ❌ rows are visible gaps. The ⚠ rows need attention. The ✓ rows can still be wrong (e.g. CI scheduler is ⚠ inside a ✓ CL-step concept).

**3. When walking a colleague through gt_models.** Use §1's big-picture diagram as the spine. Trace each block to where it lives in §8. Surface gaps explicitly rather than letting them be implicit.

---

## §10. What's deliberately NOT in this doc

- **Specific dollar values** — those live in [`ltsa_terms.yaml`](../../../data/assets/lockport/ltsa_terms.yaml), [`model_card.md`](../../../data/outputs/lockport/runs/), and the data spine. This doc is *structural*, not parametric.
- **Time-series mechanics** — the daily-loop sequence (12 steps, twin dispatch, state evolution) is in [`architecture.md`](../architecture.md) §5. This doc is *conceptual*, not procedural.
- **Code references beyond §8** — the rest of the doc is framework-only and asset-agnostic for gas.
- **Specific findings or bugs** — those live in [`docs/extra/tasks_history/.../notes.md`](../../extra/tasks_history/). This doc is the *lens* through which findings can be categorized.

---

## §11. Suggested reading order for someone new to gt_models

```
   1. THIS doc (gas_plant_workflow.md)         ← decomposition lens
   2. forward_looking_framing.md               ← why the model is structured this way
   3. architecture.md                          ← how the daily loop runs
   4. dispatch_mechanics.md                    ← operating-mode × policy-mode detail
   5. pnl_ledger.md                            ← where every dollar comes from / goes
   6. gaps_and_priorities.md                   ← what we know is missing
   7. understanding_of_gas_turbine_digital_twin.md   (in docs/extra/)
                                                ← the prototype reference
   8. backtest_findings.md                     ← model vs reality
   9. latest model_card.md                     ← what the current numbers say
   10. Latest task-history handoff.md          ← what was done in the most recent session
```

This sequence goes from the *most abstract* (lens) to the *most concrete* (latest numbers), which matches the natural cognitive flow for understanding a complex model.

---

*Companion docs:*
- [`forward_looking_framing.md`](forward_looking_framing.md) — *why* the model has the structure it does (positioning)
- [`backtest_findings.md`](backtest_findings.md) — *how* the model compares to reality (calibration)
- *This doc* — *what* the model decomposes a gas plant into (workflow / lens)
