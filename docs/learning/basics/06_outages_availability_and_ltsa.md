# Outages, Availability, And LTSA

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

Read these first if EOH, starts, VOM, or start costs are new:

- [EOH And Starts](./03_eoh_and_starts.md)
- [Start Costs And VOM](./04_start_costs_and_vom.md)
- [LTSA And Service Contracts](./08_ltsa_and_service_contracts.md)

> Plant-Type Note
> Outage and availability concepts are universal, but outage categories, covered equipment, guarantees, exclusions, and repair durations are plant-type- and contract-specific. HRSG/ST outage categories only apply when those systems exist. CHP plants may also need steam/heat-service availability.

## First-Time Reader Map

If this topic is new, start with the operating question before the contract math:

```text
Can the plant physically run today?
If not, why not?
How long will it be unavailable?
Who pays for the repair or lost performance?
```

The guide uses several terms that are easy to confuse:

| Term | First-time meaning |
| :--- | :--- |
| Outage | The plant, or part of the plant, cannot operate as expected. |
| Planned outage | Scheduled downtime for inspection or maintenance. |
| Forced outage | Unplanned downtime caused by failure, trip, or unexpected unavailability. |
| Maintenance outage | Work that is not immediate emergency work but cannot wait until the next planned outage. |
| Derating | The plant can run, but below full capability. |
| Startup failure | The plant tries to start but fails to reach service. |
| Availability | Whether the plant is physically able to run when needed. |
| Dispatch | Economic decision to run or not run if the plant is available. |
| LTSA / CSA | Service contract that defines scope, payment, exclusions, and guarantees. |
| Covered cost | Cost the contract is expected to pay for, subject to terms. |
| Excluded cost | Cost outside the contract, usually owner-funded or insurance-dependent. |
| Guarantee | Contract promise, such as minimum availability or outage duration limit. |
| Penalty / credit | Commercial remedy if a guarantee is missed and the cause is within scope. |
| Insurance | Separate risk-transfer layer for some large events, subject to deductibles and exclusions. |

The mental stack is:

```text
plant state -> outage cause -> duration -> coverage -> financial impact
```

## Plant States Before Contract Terms

A plant can be offline for very different reasons. Those reasons should not be mixed.

| State | Can it produce MW? | Is equipment the blocker? | Simple meaning |
| :--- | :--- | :--- | :--- |
| Running | Yes | No | Plant is online and producing. |
| Available but idle | No, by choice | No | Plant could run, but economics are weak. |
| Planned outage | No | Yes, scheduled | Plant is down for known inspection or maintenance. |
| Forced outage | No | Yes, unexpected | Plant failed or tripped and cannot run. |
| Derated | Partly | Yes, partly | Plant can run, but not at full MW. |
| Startup failure | No | Yes | Plant attempted to start but failed to reach service. |

Simple operating-state map:

```text
Can the plant run?
  |
  +-- yes -> dispatch decides whether economics justify running
  |
  +-- partly -> derated dispatch may still earn some revenue
  |
  +-- no, scheduled -> planned outage
  |
  +-- no, unexpected -> forced outage or startup failure
```

This distinction is the foundation for the whole guide. A plant that is available but idle is not the same as a plant that is unavailable.

## Plant-Type Variations

Every plant can be running, idle, derated, or unavailable. The cause tree changes by plant type.

| Plant type | Outage focus | Modeling warning |
| :--- | :--- | :--- |
| Simple-cycle GT | GT, generator, controls, fuel, emissions, and BOP. | Do not include HRSG/ST outage categories if no steam cycle exists. |
| Combined-cycle GT | GT, HRSG, ST, cooling, generator, controls, and BOP. | A partial outage can leave a 1x1 mode available even when full 2x1 is not. |
| Frame GT | Major outage scope and long-lead parts can dominate. | Inspection duration and repair lead time should be contract-specific. |
| Aeroderivative GT | Module swap and package support may matter. | Forced-outage duration can differ from large frame assumptions. |
| CHP / cogeneration | Power and steam/heat service availability. | Lost steam service may create penalties even if electricity revenue is small. |

The Athens availability guarantee and outage scopes below are CCGT/LTSA examples, not default rules for every gas asset.

## Coverage, Guarantees, And Insurance

Three commercial ideas sit on top of outage events.

| Commercial idea | Question it answers | Example |
| :--- | :--- | :--- |
| Coverage | Who pays for the repair scope? | Is the combustor repair covered by the LTSA? |
| Guarantee | Did the service provider meet a promised performance level? | Was annual availability at least 95%? |
| Insurance | Does a separate policy respond to a large event? | Is foreign object damage covered after deductible/waiting period? |

These are related, but they are not the same.

```text
An outage can be:
  real but excluded from LTSA coverage
  covered but still create lost revenue
  insured but subject to deductible or waiting period
  planned and therefore excluded from availability guarantee math
```

That is why the model does not stop at "outage happened." It also needs cause, duration, coverage, and financial treatment.

## How One Outage Becomes Model Signals

One outage can touch several model outputs:

```text
equipment problem occurs
  |
  +--> outage state blocks or derates dispatch
  |
  +--> outage duration creates lost MWh
  |
  +--> cause category maps to GT, HRSG, BOP, controls, or background
  |
  +--> LTSA coverage decides covered vs owner-funded cost
  |
  +--> guarantee logic decides whether penalty/credit applies
  |
  +--> financial model sees revenue loss, repair cost, and cash-flow timing
```

For a first-time reader, the important point is:

```text
Outage modeling is not only about failure probability.
It is also about commercial classification.
```

## Why This Matters

Outages and availability answer a simple question:

> Is the plant available to run when the market wants it?

A plant can have strong spark spreads, good capacity, and reasonable heat rate, but still fail to earn revenue if it is unavailable. Outages also decide whether a cost is planned, unexpected, covered by the LTSA, excluded from the LTSA, or possibly covered by insurance.

In the daily dispatch loop, outage status comes before dispatch economics:

```text
First question:
  Is the plant available?

Second question:
  If available, is it economic to run?
```

That order matters. A high-price day does not create revenue if the plant is on forced outage.

## Plain-English Concept

An outage means the plant cannot fully operate.

Availability means the plant is physically able to run when called.

LTSA means Long-Term Service Agreement. It is the service contract that defines scheduled inspections, covered work, exclusions, guarantees, cost sharing, and penalties.

The beginner distinction:

| Term | Plain meaning | Main financial effect |
| :--- | :--- | :--- |
| Planned outage | Scheduled maintenance or inspection. | Known downtime and planned cost. |
| Forced outage | Unexpected failure or unplanned unavailability. | Lost revenue, repair cost, and risk classification. |
| Availability | Share of relevant time the plant is available. | Affects revenue and contractual guarantees. |
| LTSA/CSA | Long-term service contract. | Defines who pays for what and when. |

## Planned Outage Vs Forced Outage

A planned outage is expected. It is usually scheduled around inspection windows, shoulder months, or lower-margin periods.

A forced outage is unexpected. It occurs because something fails, trips, or becomes unavailable outside the planned schedule.

```text
Planned outage:
  "We know the CI is due, so schedule it in April."

Forced outage:
  "The plant failed today, so it cannot dispatch."
```

Why this matters:

| Question | Planned outage | Forced outage |
| :--- | :--- | :--- |
| Is it expected? | Yes | No |
| Can it be scheduled around lower-price periods? | Usually yes | Usually no |
| Does it block dispatch? | Yes | Yes |
| Does it create surprise cashflow risk? | Less | More |
| Is it treated the same in availability guarantees? | Often excluded | Often included, depending on cause and contract |

## Availability

Availability is about whether the plant is able to run, not whether it actually runs.

This is important:

```text
Available but idle:
  Plant could run, but prices are too low.

Unavailable:
  Plant cannot run, even if prices are high.
```

Simple availability logic:

```text
Availability = available hours / relevant period hours
```

The framework's contract guarantee is:

```text
Availability >= 95.0%
```

The framework says the guarantee is measured on an annual rolling basis and excludes planned outages. That means planned inspection downtime is not supposed to penalize the availability guarantee in the same way as covered forced outages.

The exact denominator and exclusions must come from the actual LTSA.

## Availability Example

Assume one year:

| Item | Value |
| :--- | ---: |
| Year hours | 8,760 |
| Planned outage hours | 360 |
| Forced outage hours | 120 |

If the availability guarantee excludes planned outage hours:

```text
Relevant hours = 8,760 - 360
Relevant hours = 8,400

Available hours = 8,400 - 120
Available hours = 8,280

Availability = 8,280 / 8,400
Availability = 98.57%
```

In this example, the plant clears a 95% guarantee.

If forced outage hours were 500 instead:

```text
Available hours = 8,400 - 500
Available hours = 7,900

Availability = 7,900 / 8,400
Availability = 94.05%
```

That would fall below the 95% threshold.

## ASCII View: Available Vs Unavailable Time

```text
One simplified month

Available and running     |########## ########## ####|
Available but idle        |...... ...... ....... .....|
Planned outage            |PPPP|
Forced outage             |FFFFF|

Dispatch revenue only comes from running hours.
Availability cares whether the plant could run.
```

## LTSA / CSA Basics

The LTSA/CSA is the contract layer that translates engineering events into commercial consequences.

It usually answers questions like:

- What inspections are scheduled?
- At what EOH thresholds?
- Which parts and labor are covered?
- Which systems are excluded?
- How are fixed fees and variable reserves billed?
- What availability and heat-rate guarantees apply?
- What happens if outage duration exceeds the guarantee?

In the framework, the Athens pilot assumes a GE CSA-style structure with:

| Cost or guarantee item | Framework assumption |
| :--- | :--- |
| Fixed monthly base fee | $850,000/month |
| Variable EOH reserve | $175/EOH |
| LTSA VOM component | $1.50/MWh |
| Availability guarantee | 95.0% |
| Heat-rate guarantee | Within 2.0% of post-HGP baseline |
| CI outage duration guarantee | <= 15 days |
| MI outage duration guarantee | <= 60 days |

These are flagged as assumptions in the framework and should be replaced with actual contract values when available.

## Inspection Outages

The framework starts after a Hot Gas Path inspection at 24,000 EOH. The next scheduled inspection cycle is:

| Event | EOH trigger | EOH from start | Estimated total cost | Owner uncovered share | Outage duration |
| :--- | ---: | ---: | :--- | :--- | :--- |
| CI | 32,000 | 8,000 | $3.0M to $4.5M | About 25% | 10 to 15 days |
| CI | 40,000 | 16,000 | $3.0M to $4.5M | About 25% | 10 to 15 days |
| MI | 48,000 | 24,000 | $25M to $35M | About 35% | 45 to 60 days |

Planned inspection outages reduce dispatch hours, but they are expected. The model can schedule them in lower-value periods when possible.

## Forced Outage Prediction

The framework does not simply impose a static forced outage rate. It generates forced outage risk from the engineering stress state.

The composite daily forced outage probability is:

```text
P_forced(day) = 1 - (1 - P_GT) * (1 - P_HRSG) * (1 - P_background)
```

Where:

| Component | Plain meaning |
| :--- | :--- |
| P_GT | Gas-turbine forced outage risk from combustion fatigue, TBC condition, and rotor life. |
| P_HRSG | HRSG-related outage risk from drum cycles, attemperator condition, and plant age. |
| P_background | Residual risk from controls, generator, BOP electrical, human error, and other unmodeled causes. |

Beginner interpretation:

```text
The model asks:
  What is the chance at least one major outage category hits today?
```

If a forced outage is triggered, the model samples a duration and classifies the repair cost based on LTSA coverage.

## Daily Loop Outage Order

The framework says forced outage checks happen before executing the dispatch schedule.

```text
Start of day
  |
  v
Read current stress state
  |
  v
Forced outage check
  |
  +-- outage triggered -> unavailable, no dispatch
  |
  +-- no outage -> run Step 2 dispatch
```

This prevents the model from earning revenue on days when the plant should be unavailable.

## Outage Duration

The framework samples forced outage duration from a lognormal distribution.

Plain-English version:

```text
Most outages are relatively short.
A few outages are much longer.
```

Framework median duration assumptions:

| Outage type | Median duration assumption |
| :--- | :--- |
| GT-related outage | 8 days, range 5 to 12 |
| HRSG-related outage | 12 days, range 8 to 15 |
| BOP/background outage | 5 days, range 3 to 7 |

The lognormal shape matters because outage risk is not symmetric. A rare long outage can dominate tail risk and insurance adequacy.

## Covered Vs Excluded Costs

This is one of the most important LTSA learning points:

```text
An outage can be real even if the LTSA does not cover it.
```

The framework's assumed covered scope:

| Inspection tier | Covered examples |
| :--- | :--- |
| CI | Combustion liners, transition pieces, fuel nozzles, crossfire tubes, flow sleeves, labor. |
| MI | CI scope plus turbine stage 1 and 2 blades/nozzles/shrouds, compressor inspection, rotor inspection, bearings, seals, labor. |

The framework's excluded categories:

| Excluded category | Provision or coverage source |
| :--- | :--- |
| Generator rotor/stator repair | Owner O&M budget |
| HRSG HP drum, headers, attemperators | Owner O&M budget / HRSG cycling model |
| Steam turbine rotor and seals | Owner O&M budget |
| Cooling tower and BOP electrical | Owner O&M budget |
| Mark VIe controls / DCS upgrades | Owner O&M budget |
| Foreign object damage | Property damage insurance |
| Over-temperature / over-firing damage | Property damage insurance, verify |
| Fuel system modifications | Owner capital budget |

So the model must classify not only:

```text
Did an outage happen?
```

but also:

```text
What caused it?
How long did it last?
Is the repair covered?
Is it owner cost?
Is it insurance cost?
Does it count against availability guarantees?
```

## Availability Penalty Example

The framework uses this availability penalty formula:

```text
Availability penalty =
  ($850,000 / 12) * (0.95 - actual availability) * 10
```

It applies only when the shortfall is attributable to within-scope CSA failures, not excluded causes.

Example:

| Item | Value |
| :--- | ---: |
| Actual availability | 94.0% |
| Guarantee | 95.0% |
| Monthly fixed fee basis | $850,000 / 12 |

Calculation:

```text
Shortfall = 0.95 - 0.94
Shortfall = 0.01

Monthly fee basis = $850,000 / 12
Monthly fee basis = $70,833.33

Penalty = $70,833.33 * 0.01 * 10
Penalty = $7,083.33
```

This example is only as good as the assumed contract formula. The actual LTSA should be checked before using the penalty in investment materials.

## NERC GADS Context

NERC GADS is useful because it gives standardized outage and performance reporting language for generating units.

The current GADS instructions distinguish outage and derating categories such as:

| Category | Beginner meaning |
| :--- | :--- |
| Planned outage | Scheduled outage reported as planned outage hours. |
| Unplanned / forced outage | Immediate, delayed, postponed outage, or startup failure. |
| Maintenance outage | Work that can be deferred but must occur before the next planned outage. |
| Derating | Unit can run but below full capability. |
| Startup failure | Unit fails to reach service after the normal startup period. |

For this learning guide, the key value of GADS is vocabulary discipline. It helps avoid mixing up:

```text
offline because economics are weak
offline because planned inspection is underway
offline because equipment failed
online but derated
```

Those are different states with different financial meanings.

## How Outages Feed Step 2 Dispatch

Outages affect dispatch before economics are evaluated.

```text
If unavailable:
  dispatch = 0 MW
  revenue = $0 for unavailable hours

If available:
  dispatch model evaluates price, gas, heat rate, capacity, VOM, and start cost
```

Availability also changes the investor outputs:

| Output | Outage effect |
| :--- | :--- |
| Revenue | Lost MWh during unavailable hours. |
| Capacity factor | Lower actual generation. |
| EBITDA | Lower revenue and possibly higher repair cost. |
| DSCR | Lower cashflow can reduce coverage. |
| Insurance adequacy | Large uncovered outages test coverage limits. |
| LTSA cost | Inspections, covered work, uncovered work, and penalties can shift cashflow. |

## What The Framework Includes

The high-level framework includes these outage, availability, and LTSA ideas:

- Planned inspections are triggered by EOH thresholds.
- Forced outages are generated from the engineering stress state.
- Forced outage duration is sampled from a lognormal distribution.
- Outage cause affects cost classification.
- Availability guarantee is assumed at 95.0%, excluding planned outages.
- CI and MI outage duration guarantees are included.
- LTSA-covered and excluded categories are listed.
- Forced outage checks occur before dispatch.
- Outage results feed financial metrics such as EBITDA, DSCR, capacity factor, and insurance adequacy.

## What The Framework Leaves Out

The high-level framework still needs contract and operating detail before investment use.

| Missing detail | Why it matters |
| :--- | :--- |
| Actual LTSA text | Determines exact coverage, exclusions, guarantees, and penalty formulas. |
| Actual outage history | Needed to calibrate forced outage probabilities and duration assumptions. |
| Cause-code mapping | Needed to classify GT, HRSG, BOP, controls, owner-caused, and insured events. |
| Exact availability formula | Denominator and exclusions can change guarantee results. |
| Treatment of deratings | Partial unavailability may matter differently than full outage. |
| Startup failure treatment | Can affect both availability and EOH/start accounting. |
| Insurance policy terms | Determines deductibles, waiting periods, exclusions, and limits. |
| Planned outage scheduling rule | Shoulder-month assumptions should be validated against market and maintenance constraints. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.2.2 | Endogenous forced outage probability and cause categories. | Amber because several probability assumptions require calibration. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.3 | Forced outage check before dispatch. | Green for model architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.4 | Inspection schedule, LTSA payment structure, guarantees, and exclusions. | Amber because contract values are assumed pending review. |
| `docs/InfraSure_ModelingFramework_V2.md`, Appendix B.8-B.9 | Forced outage probability and duration assumptions. | Amber/Red depending on parameter. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Daily loop, outage check, and dispatch-mode framing. | Green for framework communication. |
| NERC 2025 GADS Data Reporting Instructions | Standardized outage, derating, startup failure, and reporting terminology. | Green for reporting vocabulary, not plant-specific failure rates. |

## Open Questions Before Investment Use

Before relying on outage and availability outputs in a final investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| What is the exact LTSA availability formula? | Determines whether a guarantee is breached. |
| Which outage causes are within-scope CSA failures? | Determines whether penalties or coverage apply. |
| Which causes are excluded and owner-funded? | Drives uncovered cashflow risk. |
| How are HRSG and steam-turbine outages treated in the contract? | These can be material and may sit outside GT CSA coverage. |
| How are partial deratings modeled? | A derated plant may still earn some revenue. |
| What historical outage records are available? | Needed to calibrate probabilities and durations. |
| How should planned outages be scheduled in the simulation? | Timing changes lost revenue. |
| What insurance deductibles and waiting periods apply? | Determines whether large forced outages are truly covered. |

## Quick Recap

Outages decide whether the plant can run. Availability measures whether it is able to run. LTSA terms decide how inspections, guarantees, coverage, exclusions, and penalties convert engineering events into financial exposure.

For this model:

```text
Planned inspections create scheduled downtime.
Forced outages are generated from stress state.
Outage checks happen before dispatch.
Availability affects guarantees and investor metrics.
LTSA coverage decides who pays for each event.
```

This guide completes the basic vocabulary needed before the final basics guide on the state vector and feedback.
