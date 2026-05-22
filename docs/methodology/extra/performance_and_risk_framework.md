# Power Plant Performance & Risk Modeling: A Framework

**Purpose.** A unified way to think about what determines a power plant's
output, and how that output feeds into two parallel but distinct decision-
relevant artifacts: a **revenue projection** and a **risk metrics suite**.
Applicable across asset types (solar, wind, gas, BESS, hybrids) and across
horizons (1 year to project life).

**Core identity for output:**

```
Output(t) = Max(t) - ContinuousLoss(t) - EventLoss(t)
```

**Core identity for what gets produced from it:**

```
{Revenue projection, Risk metrics} = Routing( Output(t) distribution )
```

The framework is about *both* identities — how output is decomposed, and
how the decomposition's components are routed into either a central
projection, a risk overlay, or both.

---

## 1. The Two-Output View

The most important conceptual move in this framework: **the model has two
parallel outputs, not one.**

```
+------------------------------------------------------------------------+
|                                                                        |
|                    Output(t) = Max(t) - CL(t) - EL(t)                  |
|                                                                        |
+------------------------------------------------------------------------+
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
+----------------+      +-------------------+      +-----------------+
|    Max(t)      |      |  ContinuousLoss   |      |   EventLoss     |
|  (the ceiling) |      |       (CL)        |      |      (EL)       |
+----------------+      +-------------------+      +-----------------+
        |                         |                         |
        |                         |                         |
   What CAPS the           What CHIPS AWAY            What KNOCKS OUT
   asset at this           every period, in           the asset in
   timestep?               accumulating ways          discrete shocks
        |                         |                         |
        v                         v                         v
+----------------+      +-------------------+      +-----------------+
| Physics-bound: |      | Deterministic:    |      | Hazard catalog: |
|  - Irradiance  |      |  - Degradation    |      |  - Hurricane    |
|  - Wind speed  |      |  - Soiling curve  |      |  - Hail         |
|  - Ambient     |      |  - Heat rate drift|      |  - Ice / freeze |
|    derate      |      |                   |      |  - Flood        |
|                |      | Stochastic:       |      |  - Wildfire     |
| Economic-bound:|      |  - Forced outage  |      |  - Lightning    |
|  - Dispatch    |      |    rate (small)   |      |                 |
|    envelope    |      |  - Availability   |      | Grid events:    |
|  - Spark spread|      |    variance       |      |  - Transmission |
|  - LMP / offer |      |  - Baseline       |      |    fault        |
|    floor       |      |    congestion     |      |  - Emergency    |
|                |      |                   |      |    directive    |
| Contractual:   |      | Step / scheduled: |      |                 |
|  - PPA cap     |      |  - LTSA outage    |      | Operational:    |
|  - Must-run /  |      |  - Major overhaul |      |  - Large forced |
|    must-not-run|      |  - BESS augment   |      |    outage       |
|  - Tolling     |      |  - Known TX       |      |    (gen trip)   |
|    constraints |      |    constraint     |      |                 |
|                |      |                   |      | Contractual /   |
|                |      |                   |      | regulatory:     |
|                |      |                   |      |  - Counterparty |
|                |      |                   |      |    default      |
|                |      |                   |      |  - Force majeure|
|                |      |                   |      |  - Regulatory   |
|                |      |                   |      |    shutdown     |
+----------------+      +-------------------+      +-----------------+
        |                         |                         |
        |                         |                         |
        +-------------------------+-------------------------+
                                  |
                                  v
              +---------------------------------------+
              |        ROUTING / CONVICTION TEST      |
              |                                       |
              |   For each component, ask:            |
              |   1. Horizon vs. recurrence interval? |
              |   2. Stationarity of the process?     |
              |   3. Data quality for the fit?        |
              |   4. Correlation structure known?     |
              +---------------------------------------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
   +--------------------+ +-----------------+ +-------------------+
   |   HIGH CONVICTION  | |   GRAY AREA     | |  LOW CONVICTION   |
   |                    | |                 | |  OR TAIL-DRIVEN   |
   | Max, deterministic | | Some stoch CL,  | |                   |
   | CL, step CL,       | | small / freq EL,| | Catastrophic EL,  |
   | well-fit stoch CL  | | regime-shifting | | rare hazards,     |
   |                    | | components      | | non-stationary    |
   |                    | |                 | | hazards           |
   +--------------------+ +-----------------+ +-------------------+
              |                   |                   |
              |          (mean to revenue,            |
              |           distribution to             |
              |              risk)                    |
              |                   |                   |
              +-------------------+                   |
              |                   |                   |
              v                   v                   v
   +--------------------+   (both routes)   +-------------------+
   | REVENUE PROJECTION | <----+----+---->  |   RISK METRICS    |
   |                    |                   |                   |
   | Output(t) * Price  |                   | EP curve          |
   | + ancillary        |                   | EAL / AAL         |
   | + capacity pmt     |                   | PML (1-in-N)      |
   | + RECs / PTC       |                   | VaR / CVaR        |
   |                    |                   | Scenario stress   |
   | -> P&L, NPV,       |                   | -> portfolio risk,|
   |    pro forma       |                   |    capital,       |
   |                    |                   |    reinsurance    |
   +--------------------+                   +-------------------+
              |                                       |
              +-------------------+-------------------+
                                  |
                                  v
                    +-----------------------------+
                    |  COMBINED VIEW for          |
                    |  decision-making:           |
                    |  - Expected NPV +/- bands   |
                    |  - Risk-adjusted return     |
                    |  - Tail exposure            |
                    |  - Hedge / insurance need   |
                    +-----------------------------+
```

### Why two outputs, not one

A pro forma without risk metrics is incomplete; risk metrics without a
revenue projection are incomplete; neither alone tells a capital allocator
whether to deploy. The output of the framework is the **joint view**, with
revenue and risk as parallel artifacts produced from the same underlying
stochastic model.

### Loss → revenue impact: two distinctions worth naming

Physical loss and owner revenue impact are not the same thing. The
framework names **two distinct moves** that sit between them. Both are
already implicit in §6.6 and Appendix A; this subsection makes them
explicit so they are unambiguous in deliverables.

#### Move 1: The contractual transition layer (gross vs. net)

Physical loss does not directly equal owner revenue impact. There is a
**contract layer** between them — LTSA performance guarantees, FSA
availability LDs, OEM heat-rate makegood, BI / PD insurance payouts,
PPA force majeure clauses, tolling counterparty terms. Each partially
papers over the physical loss before it lands on the owner's bottom line.

```
   Physical loss (gross)
          │
          │  ← apply contracts:
          │     LTSA LDs / OEM makegood / BI & PD payouts /
          │     FM clauses / tolling counterparty terms
          ▼
   Owner's NET revenue impact
```

**Routing implication**: physical CL and EL components have their
*gross* distribution feed the risk layer (the risk exists whether or not
the contract papers it over), but the *net* expected value (after
recovery) feeds the revenue line. The two outputs use different numbers
from the same underlying loss distribution. §6.6 has the full treatment.

#### Move 2: Causal vs. consequential lenses on the same loss

The decomposition `Output = Max - CL - EL` is a *causal* lens — it
separates losses by mechanism (which bucket produced this loss).
**Consequential measurements are different**: they aggregate the dollar
impact across causes on a specific KPI (revenue, EBITDA, DSCR).

The most common consequential measurement is **Business Interruption (BI)**:

    BI(t) = Σ (output_gap(t) × price(t))   summed across all causal buckets
          = contributions from CL_det + CL_stoch + CL_step + EL + contractual

BI is **not a fourth bucket** in the causal decomposition. It is an
**attribution view on top of the decomposition** — used for insurance
design, hedge structuring, and the "decision-ready view" at the bottom
of the Section 1 flowchart.

#### How the two moves fit together

Move 1 is a *transformation* (gross loss → net loss, via contracts).
Move 2 is a *lens choice* (causal mechanism vs. consequential dollar
aggregate), applicable to either the gross or net side.

Insurance products specifically interact with both moves:

- **Premium** is a continuous cost → CL deterministic → revenue line.
  *(Move 2 routing only; no Move 1 transition — premiums are paid
  regardless of events.)*
- **Payout** is an event-triggered recovery on covered EL events →
  contractual shock absorber → modifies *net* loss feeding revenue,
  while *gross* loss still feeds risk. *(Move 1 transition + Move 2
  routing.)*

#### How BI is actually computed (the join across arms)

BI payout is not produced by either arm alone — it is a **computational
join** requiring three inputs:

1. **Counterfactual baseline** (from the revenue arm): what the asset
   would have produced and earned absent the event — Max(t), price(t),
   and the CL trajectory.
2. **Event indicator** (from the hazard arm): which days an EL event
   takes the asset offline, with severity — the hazard team's IDF +
   fragility output.
3. **Contract transformation** (the Move 1 layer): policy limit,
   retention, waiting period, covered-causes filter applied to the
   join output.

```
   Revenue arm baseline   ⊗   Hazard arm event indicator
   (Max, prices, CL)          (peril × duration × severity)
              │                              │
              └──────────────┬───────────────┘
                             ▼
                  Gross BI per event per peril
                  = Σ (event-day output_gap × price)
                             │
                             │ ← apply contract terms
                             ▼
                       Net BI (owner-paid)
```

**Institutional implication**: the revenue arm's Max(t) and price
series propagate into the hazard team's dollar-denominated risk metrics
too. Hazard outputs in physical units (MWh lost, event count) need the
revenue arm's $/MWh conversion to become EAL, PML, or BI dollars in
the first place. The revenue arm is not just a producer of pro-forma
cashflow — it is a **shared baseline input** for the entire downstream
risk + insurance stack.

(The BI premium side does not need this join — premiums are paid
regardless of events, so they live in CL deterministic on the revenue
arm with no transformation.)

Neither move changes the framework's decomposition structure. They
clarify how the existing structure handles the gap between physical
loss and owner revenue impact, and where BI sits in that picture.

### What "routing" really means

Each component of `Max - CL - EL` is not exclusively a revenue input or a
risk input. The routing logic decides, for each component:

- **Revenue only:** when conviction is high enough that the expected value
  is a useful summary of the realization over the horizon.
- **Risk only:** when conviction is low, the recurrence is long relative
  to the horizon, or the process is non-stationary — i.e., when committing
  to a point estimate would mislead.
- **Both:** the most common routing for hazard-like components at long
  horizons. Mean feeds the revenue line; distribution feeds the risk layer.

---

## 2. The Conviction Test

The four criteria that decide where a component lives:

```
+--------------------------+------------------------------------------+
| Criterion                | Question                                 |
+--------------------------+------------------------------------------+
| 1. Horizon vs. recurrence| Is horizon >> recurrence interval, so    |
|                          | that the mean is a meaningful summary?   |
+--------------------------+------------------------------------------+
| 2. Process stationarity  | Is the underlying generating process     |
|                          | stable enough that a historical fit      |
|                          | generalizes to the projection period?    |
+--------------------------+------------------------------------------+
| 3. Data quality          | Is the dataset deep and clean enough to  |
|                          | fit the distribution we're committing to,|
|                          | *and do we know which policy mode        |
|                          | produced that data*? (See Section 3)     |
+--------------------------+------------------------------------------+
| 4. Correlation structure | Do we understand how this component co-  |
|                          | moves with others (across assets, across |
|                          | hazards, across markets)?                |
+--------------------------+------------------------------------------+
```

### Scoring and routing

A component scoring well on all four → consider for **revenue projection**
(and almost always also in risk, as a distribution).

A component scoring poorly on **any one** → route to **risk layer only**.

The conviction test is where InfraSure's hazard frameworks earn their keep:

- **SCVR** (Stochastic Climate Variability & Risk) — addresses criterion 2
  (stationarity) for long-horizon hazard distributions.
- **HCR** (Hazard Component Risk) — addresses criteria 1 and 3 for specific
  perils.
- **EFR** (Environmental Forcing Resource) — addresses criterion 2 for the
  *resource* side (irradiance, wind speed) under climate forcing.

### Example routings

```
Component                          | Conviction      | Revenue | Risk
-----------------------------------+-----------------+---------+--------
Solar irradiance (climate-scenario)| High            | Yes     | Yes
Solar degradation curve            | Very high       | Yes     | Minor
Inverter forced outage rate        | High            | Yes     | Yes
Inverter major replacement step    | High (scheduled)| Yes     | No
Solar hail catalog                 | Medium-low      | EAL if  | Yes
                                   |                 | long    | (full
                                   |                 | horizon | dist)
Solar hurricane (Gulf coast)       | Low (non-       | Risk    | Yes
                                   | stationary)     | only    |
Wind gearbox MTBF                  | High            | Yes     | Yes
Wind tornado (Plains)              | Low (tail-      | Risk    | Yes
                                   | dominant)       | only    |
Gas EFOR                           | High            | Yes     | Yes
Gas LTSA scheduled outage          | Very high       | Yes     | No
Gas freeze (correlated regional)   | Low (Uri-class  | Risk    | Yes
                                   | tail)           | only    |
BESS calendar/cycle fade           | High            | Yes     | Minor
BESS thermal runaway               | Very low (sparse| Risk    | Yes
                                   | data)           | only    |
Economic curtailment               | Lives in Max    | Yes     | Yes
                                   |                 | (via    | (via
                                   |                 | Max)    | price
                                   |                 |         | dist)
```

---

## 3. Policy Mode: The Latent Conditioning Variable

Every component of the output decomposition has parameters: degradation
curves have slopes, forced outage distributions have means, gearbox
failure distributions have shape and scale. The framework so far has
treated these parameters as if they were properties of the asset.

They are not. They are properties of the asset *as operated*.

The same wind turbine on the same site can be operated to extract every
available MWh — pushing past conservative cut-out thresholds, accepting
icing risk, deferring inspections — or to preserve hardware life —
stopping early on icing risk, doing preventive blade inspections,
accepting forgone MWh in exchange for predictability and longevity.
These are not just operational quirks. They are coherent strategies, and
they change the parameters of nearly every component in the loss
decomposition simultaneously.

We call these **policy modes**. They range along a spectrum:

```
  Revenue-max                                       Asset-preservation
  <===========================================================>
  Push hardware                                     Protect hardware
  Higher MWh today                                  Higher MWh later
  Higher wear                                       Lower wear
  Earlier major events                              Later major events
  Higher FSA / LTSA LD triggers                     Cleaner contract perf
```

### Why this is a latent variable, not an input

Policy mode is rarely declared. You don't see it in a spec sheet. It's
inferred from operational data — capacity factors relative to wind /
irradiance resource, frequency of minor maintenance events, MTBF
performance vs. spec, curtailment response patterns, ramp behavior
during volatile hours.

This matters because the framework's parameters are *conditional* on the
unobserved policy mode. If you fit a forced outage rate from operational
data without knowing the policy mode, you've fit a marginal that's
implicitly averaging over whatever mode was in effect. If you then
project the asset forward assuming a different policy mode, the
parameters are wrong.

### Why it isn't a fourth axis

Policy mode touches Max, CL, and EL simultaneously, so it might look like
it deserves its own top-level axis. It doesn't, for three reasons:

1. **Parsimony.** It doesn't introduce new components into the
   decomposition. It conditions the parameters of components that already
   exist. A new axis would be redundant structure.
2. **Latency.** Policy mode isn't observed directly. Promoting it to a
   top-level axis would suggest a precision the data doesn't support.
   Treating it as a latent conditioner is more honest.
3. **Continuity.** Policy mode is a spectrum, not a category. Most assets
   sit somewhere in between the extremes, and where they sit changes
   over the asset's life. A categorical axis would force false
   discretization.

The cleaner statement: **the parameters of Max(t), CL(t), and EL(t) are
conditional on policy mode π, which is a latent variable inferred from
operational data.**

```
Output(t) = Max(t | π) - CL(t | π) - EL(t | π)
```

### How policy mode manifests by asset type (the attention asymmetry)

The intensity and observability of policy mode differs sharply by asset:

```
+---------+----------------+----------------+----------------------+
| Asset   | Decision       | Observability  | Modal range          |
|         | cadence        | of mode        |                      |
+---------+----------------+----------------+----------------------+
| Gas     | Continuous —   | High — dispatch| Wide. Same plant can |
|         | dispatch desk, | logs, mainten- | run baseload vs.     |
|         | fuel scheduler,| ance records,  | peaker mode based on |
|         | operators all  | operations     | spark spread regime, |
|         | making hourly  | meetings       | with very different  |
|         | trade-offs     |                | wear profiles        |
+---------+----------------+----------------+----------------------+
| BESS    | Continuous —   | High — every   | Wide. Cycle-per-day  |
|         | every cycle    | cycle is       | rate is a direct     |
|         | trades revenue | logged in BMS  | policy choice with   |
|         | today vs.      |                | first-order          |
|         | degradation    |                | degradation impact   |
|         | tomorrow       |                |                      |
+---------+----------------+----------------+----------------------+
| Wind    | Configuration  | Medium —       | Medium. Differences  |
|         | + periodic     | inferred from  | show up as 2-5%      |
|         | review. Mostly | SCADA patterns,| capacity factor      |
|         | hands-off once | maintenance    | gaps and material    |
|         | thresholds set | frequency      | timing differences   |
|         |                |                | for major repairs    |
+---------+----------------+----------------+----------------------+
| Solar   | Set-and-forget | Low — limited  | Narrow. Real policy  |
|         | with annual    | operational    | differences exist    |
|         | reviews        | discretion in  | mostly in cleaning   |
|         |                | day-to-day     | schedule and         |
|         |                | operation      | inverter response    |
+---------+----------------+----------------+----------------------+
```

This asymmetry matters because the *importance* of modeling policy mode
correctly scales with the modal range. For gas and BESS, getting policy
mode wrong can change projected revenue and risk metrics by 10-30%. For
wind, perhaps 3-7%. For solar, often within model noise.

### Path-dependence and life-stage

Two further wrinkles worth being explicit about:

**Policy mode is path-dependent.** An asset that has been operated
aggressively for five years cannot suddenly switch to asset-preservation
mode without first absorbing the accumulated wear. The state of the
hardware constrains what modes are even available going forward. This
means a model that allows policy mode to "switch" between projections
needs to also propagate the accumulated-wear state forward, not just
update the parameters.

**Policy mode has a life-stage dimension.** Early-life, mid-life, and
end-of-life assets have different optimal modes. An asset 3 years into a
30-year life can afford aggressive operation because wear has lots of
room to accumulate. An asset 25 years into a 30-year life is in a
different regime — "harvest residual value" mode (run hard, extract
remaining value, accept higher EL probability) and "preserve final
years" mode (run conservatively, push out replacement capex) are *both*
coherent end-of-life strategies, with very different revenue and risk
profiles.

### Policy mode and the contract layer

Policy mode interacts with the maintenance contract structure discussed
in Section 6.6. An FSA with strong availability guarantees creates OEM
incentives that may conflict with the owner's revenue-max preferences —
the OEM, on the hook for LDs, prefers asset-preservation. The negotiated
equilibrium is written into FSA scope-of-work documents, LTSA
constraints, and O&M contract terms. So policy mode isn't purely an
owner choice; it's a contractual equilibrium.

For modeling: when you have explicit contract documents, use them. When
you don't, the inferred policy mode from operational data is your best
estimate.

### Implication for the conviction test

Policy mode adds a wrinkle to criterion 3 of the conviction test (data
quality). A well-fit distribution from historical data is only as
trustworthy as your understanding of which policy mode produced that
data. If the historical operator ran aggressively and the projected
operator will run conservatively, the historical fit overstates expected
losses. If it's the other way around, the historical fit understates
them.

This is one of several places where the third-party platform's
population-level view matters: characterizing the *distribution* of
policy modes across the fleet, and then matching a specific asset to
its likely mode given owner, contract structure, and observed behavior,
is something an in-house team cannot easily do.

---

## 4. Curtailment Decomposition

The single most-mis-bucketed item. Four flavors, three different homes,
each with its own routing.

```
+-------------------------+-----------------------+-------------------+
| Flavor                  | Cause                 | Lives in          |
+-------------------------+-----------------------+-------------------+
| Economic                | LMP < offer floor /   | Max(t)            |
|                         | uneconomic dispatch   | (not a loss)      |
+-------------------------+-----------------------+-------------------+
| Baseline congestion     | Recurring TX limits,  | CL stochastic     |
|                         | local export caps     |                   |
+-------------------------+-----------------------+-------------------+
| Known constraint window | Specific outage or    | CL deterministic  |
|                         | study-binding limit   | or step           |
|                         | until upgrade X       |                   |
+-------------------------+-----------------------+-------------------+
| Grid emergency / fault  | Line trip, voltage    | EL                |
|                         | event, SO directive   | (often hazard-    |
|                         |                       |  correlated)      |
+-------------------------+-----------------------+-------------------+
```

**Routing implications:**
- Economic curtailment → revenue (via dispatch in Max); distribution feeds
  risk via price scenario variability.
- Baseline congestion → revenue (expected haircut); distribution feeds
  risk for portfolios with concentrated POI exposure.
- Known constraint window → revenue (deterministic); minor risk role.
- Grid emergency → risk only; correlated with hazard catalog and feeds
  PML / CVaR.

Why attribution matters: each flavor has a different sensitivity to the
world. Economic curtailment scales with renewables overbuild and gas
prices. Congestion scales with TX upgrade schedules and load growth.
Emergency curtailment correlates with the hazard catalog. A single "8%
curtailment haircut" lumps these together and will diverge from reality
as soon as the market or grid changes.

---

## 5. Modeling Treatment by Loss Sub-Type

```
+-------------------+-----------------------+----------------------------+
| Sub-type          | Treatment             | Example                    |
+-------------------+-----------------------+----------------------------+
| Deterministic     | Curve applied each    | Solar 0.5%/yr degradation; |
| continuous        | timestep              | gas heat rate drift        |
+-------------------+-----------------------+----------------------------+
| Stochastic        | Distribution sampled  | Forced outage rate (small),|
| continuous        | each timestep or      | availability variance,     |
|                   | aggregated to month   | baseline congestion        |
+-------------------+-----------------------+----------------------------+
| Step continuous   | Scheduled drops in    | LTSA major inspection,     |
|                   | the production        | BESS augmentation,         |
|                   | trajectory            | transformer replacement    |
+-------------------+-----------------------+----------------------------+
| Event-stochastic  | Frequency-severity    | Hurricane, hail, freeze    |
|                   | catalog -> EP curve   | catalog                    |
+-------------------+-----------------------+----------------------------+
```

---

## 6. Asset-Specific Frameworks

Each asset section below tags components with their **routing**: `[R]` =
revenue projection, `[K]` = risk metrics, `[B]` = both.

### 6.1 Solar PV

```
Max(t)         = Irradiance(t) * Capacity * f_temp(T_amb, T_module)
                 - clipping_above_inverter_AC_rating
                 - (if PPA-capped) min(Max, PPA_cap)

Economic dispatch: typically NOT binding (marginal cost ~ 0), except in
deep negative-price hours -> then Max collapses to zero for that hour.
```

**Continuous losses:**
- `[R]` Annual degradation curve (0.4-0.7%/yr c-Si)
- `[R]` Soiling baseline curve (region-specific)
- `[B]` Inverter forced outage rate — dominant solar availability hit
- `[R]` Inverter replacement step events (~yr 12-15)
- `[R]` Tracker / DC health drift

**Event losses:**
- `[B]` if long horizon, `[K]` if short — hail catalog (dominant solar peril)
- `[K]` Hurricane wind (rack uplift, tracker stow failure)
- `[B]` Wildfire smoke effect on irradiance (continuous-stochastic in fire season)
- `[K]` Direct wildfire burn
- `[K]` Flood (DC combiners, tracker drives)

**Curtailment patterns specific to solar:**
- `[R]` Economic (duck-curve midday, CAISO; in Max)
- `[B]` Congestion (chronic in high-penetration zones)
- `[K]` Emergency (rare; correlated with grid events)

**Horizon notes:**
- 1-3 yr: degradation small (~1-2% cumulative). Hail EAL ~ 0.3-1% of
  revenue but realized variance is huge — route hail to risk layer only.
- Project life (30-35 yr): degradation is now 12-18%, hail catalog can
  enter revenue as EAL if SCVR/HCR support stationarity; full distribution
  always feeds risk.

**Policy mode notes (solar):** Modal range is narrow. Real differences
show up mostly in cleaning schedule (more frequent → higher Max,
marginal opex bump) and inverter response policy (conservative
trip-and-reset vs. aggressive auto-restart, affecting CL stochastic).
Policy mode is the *least* important modeling consideration for solar
across asset types.

---

### 6.2 Wind

```
Max(t)         = PowerCurve(WindSpeed(t), air_density(t))
                 * (1 - wake_loss(direction, layout))
                 - hysteresis_cutout_effects
                 - (if curtailed) min(Max, dispatch_signal)
```

**Continuous losses:**
- `[R]` Blade leading-edge erosion (1-3% AEP cumulative)
- `[R]` Gearbox / drivetrain efficiency drift
- `[B]` Forced outage rate per turbine
- `[B]` Gearbox / generator / converter MTBF failures
- `[B]` Icing days (climate-zone-specific)
- `[B]` Major component replacement step events (gearbox ~yr 7-10; stochastic timing within window)

**Event losses:**
- `[K]` Hurricane / extreme wind (>50 m/s survival regime)
- `[B]` Lightning strikes (high freq, moderate severity — can lean toward CL stochastic in high-strike regions)
- `[K]` Ice storm blade damage
- `[K]` Tornado (Midwest portfolios — CVaR-tail driver)

**Curtailment patterns specific to wind:**
- `[R]` Economic (ERCOT West nighttime, MISO South — in Max)
- `[B]` Congestion (CREZ-era West Texas, Panhandle)
- `[R]` Bat / bird / noise curtailment (regulatory, seasonal — step-continuous)
- `[K]` Icing-mode stop and emergency curtailment

**Horizon notes:**
- More material continuous losses than solar — drivetrain components are
  real costs in normal operation.
- Step events (major component replacement) big enough to swing 1-yr
  numbers if they land in that year.
- EL is geography-specific: Gulf coast → hurricane dominates;
  Plains → tornado tail + ice; Mountain → low EL overall.

**Policy mode notes (wind):** Modal range is medium. Aggressive operation
(running closer to cut-out, deferred minor maintenance, looser icing
protocols) typically shows up as 2-5% higher capacity factor with
materially earlier expected timing on gearbox / blade events. The
inferred policy mode is usually identifiable from SCADA data —
distribution of operating hours near cut-out, frequency of unplanned
service visits, MTBF vs. nameplate. FSA contracts with availability
guarantees create OEM incentives toward preservation that may conflict
with owner revenue-max preferences; the realized mode is a negotiated
equilibrium.

---

### 6.3 Natural Gas (CCGT / Peaker)

```
Max(t)         = NameplateMW * AmbientDerate(T_amb, RH)
                 * (1 - station_service)
                 * Availability(t)

EconomicMax(t) = Max(t) IF SparkSpread(t) > VOM + start_cost_amort
                 ELSE 0  (or min-load if must-run / committed)

For revenue modeling, use EconomicMax. The gap from physical Max to
EconomicMax is not a loss — it's the dispatch decision.
```

**Continuous losses:**
- `[R]` Heat rate degradation between MIs (curve resetting at each inspection)
- `[B]` EFOR (forced outage rate, 3-8% typical for CCGTs)
- `[R]` LTSA-driven combustion / hot gas path / major inspections (step events, scheduled)
- `[B]` Partial outages, ramp-rate degradation

**Event losses:**
- `[K]` Hurricane / flood (Gulf coast, low-elevation fuel handling)
- `[K]` Freeze (Uri-class — correlated regional risk, fat-tailed)
- `[K]` Gas supply interruption (compressor outage, pipeline FM)
- `[K]` Lightning / transformer fire

**Curtailment patterns specific to gas:**
- `[R]` Economic dispatch decisions live in Max — NOT a loss. Most common
  pro forma error: booking economic non-dispatch as a curtailment loss.
- `[R]` Must-run obligations as Max constraint (negative direction)
- `[R]` Ramp-rate limits during volatility hours (Max constraint)

**Horizon notes:**
- Gas plants live or die by spark spread distribution and capacity payments,
  not physical loss factors. Continuous losses modest in percent terms;
  LTSA step events drive year-to-year noise.
- EL dominated by region: Uri demonstrated that fleet-wide correlated
  freeze can dwarf fitted EAL by an order of magnitude in a single event.
  This is the textbook case for "tail-driven, risk-only" routing.

**Policy mode notes (gas):** Modal range is wide. The *same physical
asset* can be run as a baseload CCGT (high capacity factor, low starts/yr,
LTSA dollars dominated by EOH) or as a peaker/load-follower (lower CF,
many starts, LTSA dollars dominated by ES). These produce materially
different wear profiles, different MI intervals, and different EL
correlations (a peaker has lower freeze exposure simply because it runs
less). Operating mode is continuously observable from dispatch and fuel
records, and modeling without policy mode being explicit is the most
common pro forma error after the economic-curtailment-as-loss mistake.
The contract layer matters too: tolling agreements constrain mode; fully
merchant operations leave the owner with full mode discretion.

---

### 6.4 Battery Storage (BESS)

```
Max(t)         = SoC(t) * RoundTripEff
                 bounded by  (PowerRating, EnergyRating)
                 bounded by  (cycle constraints, throughput limits)

EconomicMax(t) = optimal dispatch over price signal
                 (arbitrage + ancillary co-optimization)

For BESS, Max is almost entirely an economic / state-dependent quantity,
not a physics quantity.
```

**Continuous losses:**
- `[R]` Calendar fade + cycle fade (capacity degradation curve)
- `[R]` Round-trip efficiency degradation
- `[B]` Availability (forced outage of inverter / racks)
- `[R]` Augmentation events (step, every 2-5 yr)

**Event losses:**
- `[K]` Thermal runaway / fire (low frequency, high severity, often total
  loss at module or container level — classic risk-only component)
- `[K]` Flood (especially containerized at grade)
- `[K]` Hurricane / wind (site infrastructure)

**Curtailment patterns specific to BESS:**
- `[R]` SoC limits, throughput caps under warranty — these are dispatch
  constraints in EconomicMax, not losses.

**Horizon notes:**
- BESS revenue uniquely dominated by economic / market modeling. Physics
  losses are secondary.
- Cycle-life degradation interacts with revenue: more cycling = more
  revenue today, but faster degradation = less revenue tomorrow.
  Augmentation schedule decisions are first-order to project NPV.

**Policy mode notes (BESS):** Modal range is wide and the cycle policy is
*the* central modeling decision. Cycles-per-day is observable from BMS
data and directly conditions both Max (more cycles = more revenue
opportunity, subject to power and energy bounds) and CL deterministic
(more cycles = faster cycle fade). Warranty contracts often impose a
throughput cap that effectively forces a mode; staying inside the cap
preserves warranty, exceeding it shifts augmentation cost to the owner.
For BESS more than any other asset, policy mode is not just a parameter
condition — it's the *primary lever* the operator pulls.

---

### 6.5 Hybrids (e.g., Solar + BESS, Wind + BESS, Gas + BESS)

Hybrids don't get a new framework — they get a *joint* Max function with
shared coupling constraints, and the loss buckets aggregate from the
component assets with attention to correlations.

```
Max_hybrid(t) = OptimalDispatch(
                  Solar_Max(t),
                  BESS_state(t),
                  POI_limit,
                  PPA_terms,
                  Price(t)
                )

CL_hybrid     = CL_solar + CL_BESS - overlap_when_POI_binds
EL_hybrid     = EL_solar + EL_BESS + correlated_site_perils
```

**Routing implications specific to hybrids:**
- `[R]` POI export limit creates a *shared cap* — Max is not the sum of
  component maxes. When POI binds, one component's outage may not reduce
  Output if the other absorbs it.
- `[K]` Correlated site perils (hurricane hits the whole site, flood
  inundates shared transformer pad) make EL aggregation non-additive —
  this is a risk-layer treatment because the correlation structure
  amplifies the tail.
- `[R]` PPA structures dictate which component a given MWh is "from" —
  matters for PTC / ITC accounting, not physics.

---

### 6.6 Maintenance Contracts and Their Revenue Impact

The framework so far has implicitly assumed that physical losses translate
directly into revenue losses. In practice, there's a **contractual layer**
between physical outages / degradation and revenue impact — the maintenance
contract. This layer differs materially by asset type, and the differences
matter for both modeling treatment and the magnitude of revenue dependence.

#### Unified view of contract structures

```
+---------+----------------+------------------+-----------------------+
| Asset   | Contract type  | What it covers   | Modeling treatment    |
+---------+----------------+------------------+-----------------------+
| Gas     | LTSA / CSA     | Scheduled        | Step events at known  |
|         | (counter-      | inspections tied | counter thresholds;   |
|         | driven)        | to EOH / ES      | heat rate resets at   |
|         |                | counters; major  | each MI; high         |
|         |                | parts; perf      | conviction `[R]`      |
|         |                | guarantees       |                       |
+---------+----------------+------------------+-----------------------+
| Wind    | FSA / warranty | Routine annual   | Routine = continuous  |
|         | / self-perform | service + major  | det; major component  |
|         | (hybrid time + | component        | repair = stochastic   |
|         | failure driven)| repair;          | step `[B]`; timing    |
|         |                | availability     | matters at 1-3 yr     |
|         |                | guarantee        | horizons              |
+---------+----------------+------------------+-----------------------+
| Solar   | O&M ($/kW-yr   | Cleaning,        | Almost entirely       |
|         | or $/MWh)      | monitoring,      | continuous det;       |
|         | (calendar      | scheduled        | inverter replacement  |
|         | driven)        | service;         | as one large step     |
|         |                | inverter service | event around yr 12-15 |
+---------+----------------+------------------+-----------------------+
| BESS    | O&M + aug      | Routine service; | Aug is half-capex/    |
|         | (warranty      | augmentation     | half-opex; first-     |
|         | driven)        | every 2-5 yr to  | order to NPV; treat   |
|         |                | maintain         | as scheduled step     |
|         |                | warranted        |                       |
|         |                | capacity         |                       |
+---------+----------------+------------------+-----------------------+
```

#### Approximate cost ranges and share of revenue

The numbers below are industry rough ranges (NREL ATB, EIA, LevelTen, OEM
disclosures). They vary materially by site, vintage, contract structure,
and PPA price — these are orientation, not pro forma inputs.

```
+---------------+----------------+------------------+------------------+
| Asset         | Total O&M cost | of which maint   | % of revenue     |
|               |                | contract         | (PPA / merchant) |
+---------------+----------------+------------------+------------------+
| Gas CCGT      | $4-9 / MWh     | LTSA: $2-5 / MWh | 8-20% revenue    |
| (baseload)    |                |                  | 15-35% gross     |
|               |                |                  | margin           |
+---------------+----------------+------------------+------------------+
| Gas Peaker    | $6-15 / MWh    | LTSA: $3-8 / MWh | Highly variable; |
|               |                | (dominated by    | $/start economics|
|               |                | $/start)         | often binding on |
|               |                |                  | dispatch         |
+---------------+----------------+------------------+------------------+
| Wind onshore  | $35-55 /kW-yr  | FSA: 60-75% of   | 20-40% revenue   |
|               | (~$10-18/MWh)  | total O&M        |                  |
+---------------+----------------+------------------+------------------+
| Solar PV      | $8-15 /kW-yr   | Inverter service | 7-15% revenue    |
| utility-scale | (~$3-5/MWh)    | + cleaning =     | (rising as PPA   |
|               |                | most of it       | prices fall)     |
+---------------+----------------+------------------+------------------+
| BESS (4 hr)   | $15-30 /kW-yr  | Augmentation is  | Highly variable; |
|               | excl. aug      | a separate large | aug typically    |
|               |                | step item        | capex-treated    |
+---------------+----------------+------------------+------------------+
```

#### The qualitative point: does maintenance reshape the *optimization*?

The bigger story isn't the cost level — it's whether the contract
structure changes the dispatch optimization itself.

```
+---------+----------------------+--------------------------------------+
| Asset   | Does maintenance     | Why                                  |
|         | change dispatch?     |                                      |
+---------+----------------------+--------------------------------------+
| Gas     | YES — first-order    | LTSA is counter-driven, so every hour|
|         |                      | of operation and every start consumes|
|         |                      | EOH/ES toward the next inspection.   |
|         |                      | Peaker $/start economics can make a  |
|         |                      | marginal start uneconomic even with  |
|         |                      | a positive spark spread. CCGT MI     |
|         |                      | scheduling shapes multi-year dispatch|
|         |                      | strategy. Heat rate resets at each MI|
|         |                      | change marginal cost trajectory.     |
+---------+----------------------+--------------------------------------+
| Wind    | Mostly NO            | Marginal cost ~ 0; turbines run when |
|         | (but availability    | wind blows. FSA availability         |
|         | guarantee matters    | guarantee creates owner indifference |
|         | for the contract     | up to the LD threshold — physical    |
|         | layer)               | outage doesn't fully translate to    |
|         |                      | revenue outage.                      |
+---------+----------------------+--------------------------------------+
| Solar   | NO                   | Marginal cost ~ 0; no operational    |
|         |                      | decision interacts with O&M cost     |
|         |                      | structure. Inverter replacement is a |
|         |                      | capex event, not a dispatch decision.|
+---------+----------------------+--------------------------------------+
| BESS    | YES                  | Throughput / cycle limits under      |
|         |                      | warranty cap optimization. Each      |
|         |                      | cycle consumes warranted life, so    |
|         |                      | arbitrage decisions trade off today's|
|         |                      | revenue vs. tomorrow's degradation / |
|         |                      | augmentation cost.                   |
+---------+----------------------+--------------------------------------+
```

This is the qualitative difference that matters: **for gas and BESS, the
maintenance contract is part of the optimization itself, not just a cost
on the side.** For solar and wind, it's a cost line that doesn't reshape
when or how the asset runs.

#### Availability and performance guarantees: the contractual shock absorber

Every long-term maintenance contract includes some form of performance
guarantee that creates a *contractual layer* between physical losses and
revenue losses. The framework should model this explicitly:

- **Gas LTSA performance guarantees**: heat rate and capability are
  warranted between inspections. Physical degradation that exceeds spec
  triggers OEM makegood. This is why the heat rate degradation curve in
  the model *resets* at each MI — contractually required.
- **Wind FSA availability guarantees**: typically 95-97%. Physical
  availability below the guarantee triggers liquidated damages from the
  OEM. So if turbines are physically down 5% but the guarantee is 97%,
  the owner sees revenue impact on ~3%, not 5%.
- **Solar O&M performance guarantees**: typically structured around
  degradation rate or P50 production. If module degradation exceeds the
  warranted curve, LDs flow.
- **BESS warranty**: capacity warranties drive augmentation events. The
  contract guarantees a minimum capacity at each year; falling below
  triggers augmentation at OEM (or owner) cost.

**Routing implication**: physical CL and EL components have their *gross*
distribution feed into the risk layer (because the physical risk exists
whether or not the contract papers over it for the owner), but the *net*
expected value (after LDs and OEM makegood) feeds the revenue line. The
two outputs use different numbers from the same underlying loss
distribution.

#### Modeling notes by asset

- **Gas**: The LTSA cost is the single largest non-fuel cost line. Model
  it as $/EOH and $/ES applied to dispatch counters, with discrete
  inspection step events scheduled by counter thresholds. Heat rate
  trajectory between inspections is the deterministic curve; resets are
  contractually guaranteed.
- **Wind**: Separate routine service (continuous deterministic, ~25-40%
  of total O&M) from major component repairs (stochastic step, ~60-75%).
  FSA availability guarantee is a wedge between physical and revenue
  outage rates — model it explicitly if the contract is in place.
- **Solar**: Routine O&M is small enough that a flat $/kW-yr is usually
  adequate. The one event that matters is inverter replacement around
  year 12-15 — model as a scheduled step.
- **BESS**: Augmentation is the dominant maintenance-driven cash item,
  and the optimization interaction (cycle today vs. degrade tomorrow)
  needs to live inside EconomicMax, not as a side cost.

---

## 7. Horizon Discipline (Critical)

```
+-------------------+------------------+---------------------------------+
| Horizon           | Revenue line     | Risk metrics layer              |
+-------------------+------------------+---------------------------------+
| 1-3 years         | Max - CL only    | Full EL distribution; CL        |
|                   | (deterministic + | variance; scenario stress       |
|                   |  expected stoch) | (P50/P90 sim, named events,     |
|                   |                  | VaR/CVaR)                       |
+-------------------+------------------+---------------------------------+
| 5-10 years        | Max - CL,        | Full distribution; EL begins    |
|                   | begin folding in | crossing into revenue but       |
|                   | expected EL where| always with risk-side support;  |
|                   | SCVR/HCR support | report range                    |
+-------------------+------------------+---------------------------------+
| Project life      | Max - CL - EAL   | EP curve, EAL, PML, VaR, CVaR;  |
| (20-35 yr)        | (long-run avg    | non-stationary hazards still    |
|                   |  honest here)    | risk-only even at long horizons |
+-------------------+------------------+---------------------------------+
```

The single biggest pro forma mistake in the industry is **applying a
long-horizon EAL to a short-horizon central forecast.** It produces a
number that's neither the expected outcome (because EAL doesn't realize
over 2 years) nor a useful risk metric (because the distribution is
hidden inside a point estimate).

The corollary: **even at long horizons, a component that fails the
conviction test should stay in the risk layer only.** Non-stationary or
sparse-data hazards don't earn their way into the revenue line just
because the horizon is long.

---

## 8. Checklist When Modeling a New Asset

1. What's the dominant determinant of Max — physics, economics, or
   contract? (Solar/wind: physics. Gas/BESS: economics. PPA-capped: contract.)
2. Have I separated *economic* curtailment (which belongs in Max) from
   *physical* curtailment (which belongs in CL or EL)?
3. Are my continuous losses broken into deterministic / stochastic / step?
   Have I scheduled the step events (LTSA, augmentation, inverter
   replacement) onto a specific year?
4. For each component, have I run the conviction test? Is it routed to
   `[R]`, `[K]`, or `[B]`?
5. Is my hazard catalog appropriate for the *region* of this asset, and
   does SCVR/HCR support its inclusion in the revenue line (if at all)?
6. Am I applying EL to the right horizon — and if not, am I moving it to
   the risk overlay rather than letting it pollute the central forecast?
7. For hybrids: does my POI-binding logic correctly handle the case where
   one component's outage doesn't reduce Output because the other component
   absorbs it?
8. Do my revenue and risk outputs come from the *same* underlying
   stochastic model, with consistent assumptions across both?
9. What is the inferred policy mode for this asset (revenue-max,
   asset-preservation, somewhere between)? Are the parameters of my Max,
   CL, and EL components conditioned on that mode, or am I implicitly
   using a population-average that may not fit?
10. For gas and BESS especially: is the policy mode I'm projecting
    consistent with the contract structure (LTSA terms, BESS warranty
    throughput caps)? If the contract enforces a different mode than I'm
    assuming, my parameters are wrong.

---

## Appendix A: Where Common Loss Items Belong (Bucket + Routing)

```
Item                            | Bucket              | Routing
--------------------------------+---------------------+--------------
Solar degradation               | CL deterministic    | R
Solar soiling baseline          | CL deterministic    | R
Solar soiling event (dust storm)| EL                  | B / K
Inverter forced outage          | CL stochastic       | B
Inverter replacement            | CL step             | R
Wind blade erosion              | CL deterministic    | R
Wind gearbox failure            | CL stochastic       | B
Wind lightning strike           | CL stochastic / EL  | B
Wind icing days                 | CL stochastic       | B
Wind ice storm damage           | EL                  | K
Hurricane (any asset)           | EL                  | K (B at long horizon if stationary)
Hail (especially solar)         | EL                  | B
Tornado (wind, Plains)          | EL                  | K
Freeze (gas)                    | EL                  | K
Gas heat rate degradation       | CL deterministic    | R
Gas LTSA major inspection       | CL step             | R
Gas EFOR                        | CL stochastic       | B
Gas-supply interruption         | EL                  | K
BESS calendar fade              | CL deterministic    | R
BESS cycle fade                 | CL deterministic    | R
BESS augmentation               | CL step             | R
BESS thermal runaway            | EL                  | K
Economic curtailment            | Max (not a loss)    | R (price dist -> K)
Baseline TX congestion          | CL stochastic       | B
Known constraint window         | CL deterministic    | R
Grid emergency curtailment      | EL                  | K
PPA cap (when binding)          | Max (contractual)   | R
Must-run obligation             | Max (contractual)   | R
PPA counterparty default        | EL (contractual)    | K
Force majeure (any cause)       | EL (contractual)    | K
Regulatory shutdown order       | EL (contractual)    | K
Tolling counterparty insolvency | EL (contractual)    | K
BI insurance premium            | CL deterministic    | R
BI insurance payout             | Contractual offset  | net -> R,
                                | on EL               | gross -> K
PD insurance premium            | CL deterministic    | R
PD insurance payout             | Contractual offset  | net -> R,
                                | on EL               | gross -> K

Routing legend:
  R = revenue projection only
  K = risk metrics only
  B = both (mean -> revenue, distribution -> risk)

Note: BI itself is not a routable component — it is the consequential
aggregate across all causes above (CL + EL + contractual EL). See §1's
"Causal decomposition vs. consequential measurement" subsection.
```

---

## Appendix B: How This Maps to InfraSure Frameworks

```
+-----------+--------------------------------------------------+
| Framework | Role in this view                                |
+-----------+--------------------------------------------------+
| SCVR      | Stationarity test for long-horizon hazard        |
|           | distributions; gatekeeper for whether a hazard   |
|           | can earn its way into the revenue line.          |
+-----------+--------------------------------------------------+
| HCR       | Hazard-specific component risk; supplies the     |
|           | distributions consumed by the risk layer and     |
|           | the EALs consumed (conditionally) by revenue.    |
+-----------+--------------------------------------------------+
| EFR       | Environmental forcing on the resource side       |
|           | (irradiance, wind speed); applies the            |
|           | stationarity question to Max(t) itself, not just |
|           | to losses.                                       |
+-----------+--------------------------------------------------+
| EAL, PML, | Core risk-layer outputs. EAL crosses into        |
| VaR, CVaR | revenue at long horizons when conviction passes; |
|           | the others stay in risk.                         |
+-----------+--------------------------------------------------+
| EP curve  | The compact representation of the joint EL       |
|           | distribution that feeds the risk metrics layer.  |
+-----------+--------------------------------------------------+
```
