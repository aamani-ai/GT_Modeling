# LTSA And Service Contracts

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

Read these related guides when the contract terms start touching operations:

- [EOH And Starts](./03_eoh_and_starts.md)
- [Start Costs And VOM](./04_start_costs_and_vom.md)
- [Outages, Availability, And LTSA](./06_outages_availability_and_ltsa.md)
- [State Vector And Feedback](./07_state_vector_and_feedback.md)

> Plant-Type Note
> LTSA and CSA structures are contract-specific. The broad ideas apply across many gas plants, but the covered equipment, inspection triggers, start limits, payment terms, guarantees, exclusions, and remedies depend on the OEM, asset type, negotiated contract, and plant configuration. The Athens values in this guide are worked-example assumptions for a GE 7FA 2x1 CCGT.

## First-Time Reader Map

If this topic is new, start with the business problem:

```text
A gas plant has expensive equipment.
That equipment needs planned inspections and repair work.
The owner may sign a service contract with the OEM or service provider.
The contract decides what is paid, what is covered, what is excluded,
and what performance guarantees apply.
```

LTSA means Long-Term Service Agreement. CSA means Contractual Service Agreement. In this learning path, the terms are used closely together because the Athens example assumes a GE CSA-style service contract.

The beginner mental model:

```text
physical operation
  -> EOH, starts, MWh, outages, heat rate
  -> contract rules
  -> fees, reserves, coverage, exclusions, guarantees
  -> cashflow and investment risk
```

## Why This Guide Exists

The earlier basics guides already mention LTSA:

| Guide | What it explains |
| :--- | :--- |
| [EOH And Starts](./03_eoh_and_starts.md) | How fired hours, starts, trips, and load swings become contractual EOH and inspection timing. |
| [Start Costs And VOM](./04_start_costs_and_vom.md) | How fixed fees, EOH reserve, LTSA VOM, and start overages enter cost modeling. |
| [Outages, Availability, And LTSA](./06_outages_availability_and_ltsa.md) | How outage cause, coverage, exclusions, and guarantees affect financial treatment. |

Those are correct, but they are application-specific views. This guide explains the contract itself first.

## Plain-English Concept

An LTSA is a long-term service contract for major equipment.

For a gas turbine plant, it usually defines:

- which units are covered;
- which inspections are scheduled;
- when inspections are triggered;
- which parts and labor are included;
- which equipment is excluded;
- how fixed and variable payments are billed;
- how starts and EOH are counted;
- what performance guarantees apply;
- what happens when guarantees are missed;
- how costs are split between OEM and owner.

Simple version:

```text
The plant owner pays predictable service fees.
The service provider takes responsibility for defined work.
The contract limits what is covered.
Anything outside those limits can still become owner risk.
```

## What An LTSA Is Not

This is important for modeling.

| Misunderstanding | Better view |
| :--- | :--- |
| "The LTSA covers all maintenance." | It covers defined scope only. Many systems can be excluded. |
| "LTSA cost is just one annual number." | It can include fixed fees, variable reserves, VOM components, overages, true-ups, and penalties. |
| "The contract EOH counter is the same as physical damage." | Contractual EOH drives billing and inspections; physical damage drives failure risk. |
| "If there is an outage, the OEM always pays." | Coverage depends on cause, scope, exclusions, owner actions, and contract wording. |
| "Availability guarantee means the plant will always be available." | It creates a commercial remedy if defined availability is missed for covered reasons. |

## The Main Parties

| Party | Plain-English role | Modeling relevance |
| :--- | :--- | :--- |
| Owner / asset company | Owns the plant and receives revenue. | Pays fees, pays uncovered costs, receives credits or penalties if applicable. |
| OEM / service provider | Maintains covered equipment under contract. | Performs inspections, supplies covered parts/labor, may owe remedies. |
| Operator | Runs the plant day to day. | Dispatch and operating practices affect starts, EOH, trips, and damage. |
| Insurer | Covers some large property or business interruption risks. | Separate from LTSA; subject to deductibles, waiting periods, and exclusions. |
| Lender / investor | Cares about cashflow and downside risk. | Needs clarity on covered vs uncovered cost and outage exposure. |

## Contract Layers

An LTSA usually has several layers, not one single rule.

```text
1. Equipment scope
       |
       v
2. Inspection schedule and life counters
       |
       v
3. Payment structure
       |
       v
4. Coverage and exclusions
       |
       v
5. Guarantees and remedies
       |
       v
6. True-up, escalation, and cashflow timing
```

Each layer can change the model. For example, a start can create EOH, consume a start allowance, increase start overage exposure, and push the next inspection closer.

## Athens Worked-Example Contract Snapshot

The framework assumes the Athens pilot has a GE CSA-style comprehensive contract.

| Item | Framework assumption |
| :--- | :--- |
| Contract type | GE Contractual Service Agreement, comprehensive |
| Covered units | GT-A and GT-B, GE 7FA.03 x 2 |
| Starting state | Just completed HGP at 24,000 EOH |
| Next inspection | CI at 32,000 EOH |
| Fixed base fee | $850,000/month |
| Variable EOH reserve | $175/EOH |
| LTSA VOM component | $1.50/MWh |
| Availability guarantee | 95.0% |
| Heat-rate guarantee | Within 2.0% of post-HGP baseline |

Important caution:

```text
These are framework assumptions, not confirmed contract terms.
Use the actual LTSA / CSA before investment use.
```

## Inspection Schedule

The service contract usually defines planned inspections. In the Athens framework, the simplified cycle after the current HGP is:

| Event | EOH trigger | EOH from current state | Estimated total cost, 2 GTs | Owner uncovered share | Outage duration |
| :--- | ---: | ---: | :--- | :--- | :--- |
| CI | 32,000 | 8,000 | $3.0M to $4.5M | About 25% | 10 to 15 days |
| CI | 40,000 | 16,000 | $3.0M to $4.5M | About 25% | 10 to 15 days |
| MI | 48,000 | 24,000 | $25M to $35M | About 35% | 45 to 60 days |

Beginner translation:

```text
The plant starts at 24,000 EOH.
At 32,000 EOH, the next CI is due.
That gives 8,000 EOH of headroom.
Every fired hour and start consumes some of that headroom.
```

## CI, HGP, And MI

The inspection names can be confusing.

| Term | Stands for | Simple meaning |
| :--- | :--- | :--- |
| CI | Combustion Inspection | Focused inspection of combustion hardware. |
| HGP | Hot Gas Path inspection | Deeper inspection of turbine parts exposed to hot gas. |
| MI | Major Inspection | Broadest inspection in the simplified cycle, including larger rotating and stationary scope. |

In the current framework, the starting point is just after an HGP. That matters because some damage and degradation states are reset or partially reset at that point.

## Covered Scope

Coverage means the contract is expected to pay for defined work, subject to the exact terms.

In the framework, the assumed covered scope is:

| Inspection tier | Covered examples |
| :--- | :--- |
| CI | Combustion liners, transition pieces, fuel nozzles, crossfire tubes, flow sleeves, labor. |
| MI | CI scope plus turbine stage 1 and 2 blades/nozzles/shrouds, compressor inspection, rotor inspection, bearings, seals, labor. |

Coverage does not mean the owner has zero cost. The framework still assumes owner uncovered shares at inspection events.

## Exclusions

Exclusions are equipment, events, or costs outside the contract scope.

In the Athens framework, excluded categories include:

| Excluded category | Typical modeling treatment |
| :--- | :--- |
| Generator rotor/stator repair | Owner O&M budget. |
| HRSG HP drum, headers, attemperators | Owner O&M budget or HRSG cycling model. |
| Steam turbine rotor and seals | Owner O&M budget. |
| Cooling tower and BOP electrical | Owner O&M budget. |
| Controls / DCS upgrades | Owner O&M or capital budget. |
| Foreign object damage | Property damage insurance, subject to policy terms. |
| Over-temperature or over-firing damage | Verify insurance and contract exclusions. |
| Fuel system modifications | Owner capital budget. |

This is why a CCGT model cannot say:

```text
CCGT maintenance = GT LTSA
```

The GT contract may be material, but HRSG, ST, generator, controls, and BOP can still create owner risk.

## Payment Structure

The Athens framework has three recurring LTSA payment ideas.

| Payment item | Framework rate | Trigger | Dispatch meaning |
| :--- | ---: | :--- | :--- |
| Fixed base fee | $850,000/month | Time passing. | Usually not a marginal dispatch cost. |
| Variable EOH reserve | $175/EOH | Contractual EOH accrued. | More starts/running can increase reserve accrual. |
| LTSA VOM component | $1.50/MWh | MWh dispatched. | Variable cost tied to generation. |

The model should keep these separate.

```text
Fixed fee:
  paid because the contract exists

EOH reserve:
  paid because life was consumed

LTSA VOM:
  paid because MWh were generated
```

## EOH Reserve Example

Assume one day creates 60.6 EOH.

| Item | Value |
| :--- | ---: |
| Daily EOH | 60.6 |
| EOH reserve rate | $175/EOH |

Calculation:

```text
EOH reserve = 60.6 * $175
EOH reserve = $10,605
```

This is not the full inspection cost. It is a reserve or billing mechanism. The actual inspection event may later reconcile the accumulated reserve against actual cost and covered/uncovered shares.

## True-Up Mechanism

The framework describes a true-up at inspection events.

Beginner version:

```text
During operation:
  the model accrues EOH reserve each month

At inspection:
  actual inspection cost is compared with reserve balance

If reserve is high:
  surplus may roll forward

If reserve is low:
  a catch-up invoice may occur
```

ASCII view:

```text
monthly EOH reserve accruals
        |
        v
reserve balance
        |
        v
inspection event
        |
        +--> enough reserve -> roll forward surplus or reduce balance
        |
        +--> not enough -> catch-up payment / owner shortfall
```

The exact mechanics must come from the actual contract.

## Start Limits And Overage Charges

Some service contracts assume a baseline number of starts per year. If actual starts exceed the allowance, the owner may pay an overage charge.

Framework start overage assumptions:

| Start type | Annual contracted limit | Overage charge |
| :--- | ---: | ---: |
| Hot start | 150 starts/yr | $8,500 per excess start |
| Warm start | 35 starts/yr | $42,000 per excess start |
| Cold start | 5 starts/yr | $125,000 per excess start |
| Emergency trip | 3 events/yr | $80,000 per excess event |

Example:

```text
Actual hot starts = 170
Contracted hot starts = 150
Excess hot starts = 20

Hot start overage = 20 * $8,500
Hot start overage = $170,000
```

This is different from start cost.

```text
Start cost:
  applies to starting the plant

Start overage charge:
  applies only after the contract allowance is exceeded
```

## Guarantees

Guarantees are contract promises. They do not stop bad events from happening. They define a remedy if the measured outcome misses the contract threshold for covered reasons.

The framework includes these Athens assumptions:

| Guarantee | Framework assumption | Beginner meaning |
| :--- | :--- | :--- |
| Availability | 95.0%, annual rolling basis, planned outages excluded | Plant should be available for at least the guaranteed share of relevant time. |
| Heat rate | Within 2.0% of post-HGP baseline | Plant efficiency should not drift beyond the allowed contract band. |
| CI outage duration | <= 15 days per event | CI should not exceed the agreed duration without remedy. |
| MI outage duration | <= 60 days per event | MI should not exceed the agreed duration without remedy. |

Guarantee math is contract-specific. The exact denominator, exclusions, and remedy formula matter.

## Availability Guarantee Example

Assume one year:

| Item | Value |
| :--- | ---: |
| Year hours | 8,760 |
| Planned outage hours | 360 |
| Forced outage hours | 500 |
| Availability guarantee | 95.0% |

If planned outage hours are excluded from the denominator:

```text
Relevant hours = 8,760 - 360
Relevant hours = 8,400

Available hours = 8,400 - 500
Available hours = 7,900

Availability = 7,900 / 8,400
Availability = 94.05%
```

This misses a 95.0% guarantee.

But the commercial result still depends on cause:

```text
Covered CSA cause:
  possible service-provider remedy

Excluded owner / BOP / insurance cause:
  may not create CSA remedy
```

## Heat-Rate Guarantee Example

Assume:

| Item | Value |
| :--- | ---: |
| Post-HGP baseline heat rate | 7,070 BTU/kWh |
| Guarantee band | 2.0% |

Allowed heat-rate threshold:

```text
Threshold = 7,070 * 1.02
Threshold = 7,211.4 BTU/kWh
```

If measured heat rate is 7,250 BTU/kWh:

```text
Overage = 7,250 - 7,211.4
Overage = 38.6 BTU/kWh
```

That does not automatically mean cash is owed. The actual contract must define measurement method, correction basis, allowed exclusions, cure rights, and penalty formula.

## Fixed Fee Watch Item

The framework states a fixed base fee of:

```text
$850,000/month
```

One availability penalty example elsewhere divides `$850,000 / 12`, which looks like annual-to-monthly conversion.

That creates a diligence question:

```text
Is $850,000 a monthly fee or annual fee?
```

For this guide, the payment table follows the stated framework assumption of `$850,000/month`. Before using the penalty formula in an investment case, confirm the actual fee frequency and remedy formula.

## How LTSA Feeds Step 2 Dispatch

LTSA does not only affect accounting after the fact. It can change dispatch economics.

Step 2 asks:

```text
Should the plant run today?
```

LTSA-related factors can change that answer:

| LTSA-related item | How it can affect dispatch |
| :--- | :--- |
| EOH reserve | More operation creates more EOH accrual. |
| Inspection headroom | Running today can bring the next outage closer. |
| Start overage limit | Extra starts late in the contract year can become expensive. |
| EOH proximity penalty | Model can avoid marginal runs near inspection thresholds. |
| Heat-rate guarantee | Degraded efficiency can create contract and dispatch risk. |
| Availability guarantee | Outage state can block dispatch and affect remedies. |

Daily loop view:

```text
opening contract state
  -> dispatch decision
  -> fired hours, starts, MWh, outages
  -> EOH and start counters
  -> fees, reserves, overages, guarantee status
  -> closing contract state
```

## Contractual EOH Vs Physical Damage

This is one of the most important distinctions in the whole framework.

| Tracker | What it is | What it drives |
| :--- | :--- | :--- |
| Contractual EOH | Contract counter based on fired hours, starts, trips, and agreed multipliers. | Inspection timing, reserve billing, start/EOH limits. |
| Physical damage | Engineering estimate of creep, fatigue, fouling, TBC, rotor, HRSG, and other stress. | Forced outage risk, derates, heat-rate degradation, capacity degradation. |

They can diverge.

```text
Contract says:
  next inspection is based on EOH threshold

Physics says:
  damage risk may rise faster or slower than the contract counter
```

That is why the model keeps both views.

## Plant-Type Variations

Service contracts change materially by plant type.

| Plant type | Contract warning |
| :--- | :--- |
| Simple-cycle GT | No HRSG/ST scope unless separate systems exist. Contract may focus on GT package, starts, inspections, and parts. |
| Combined-cycle GT | GT CSA may not cover HRSG, ST, generator, cooling, controls, or BOP. 1x1 vs 2x1 operation can complicate counters. |
| Frame GT | Major outage scope, long-lead parts, and inspection planning can dominate. |
| Aeroderivative GT | Module exchange and package service arrangements may differ from large frame contracts. |
| CHP / cogeneration | Heat/steam service obligations may create additional guarantees outside a standard power-only LTSA. |

Do not copy Athens 2x1 CCGT values into another plant without checking the actual service agreement.

## Model Inputs

The model needs contract inputs before it can use LTSA logic.

| Input | Example |
| :--- | :--- |
| Covered units | GT-A, GT-B. |
| Inspection thresholds | CI at 32,000 EOH, CI at 40,000 EOH, MI at 48,000 EOH. |
| Payment rates | Fixed fee, EOH reserve, LTSA VOM, start overage rates. |
| Start limits | Hot, warm, cold, trip annual allowances. |
| Coverage scope | CI and MI covered components. |
| Exclusions | HRSG, ST, generator, BOP, controls, insurance-dependent events. |
| Guarantees | Availability, heat rate, outage duration. |
| Escalation | PPI cap, rate escalation rules. |
| Initial state | Current EOH, starts year-to-date, post-HGP state, reserve balance if known. |

## Model Outputs

LTSA logic should create transparent outputs.

| Output | Why it matters |
| :--- | :--- |
| EOH added | Drives reserve accrual and inspection timing. |
| EOH headroom | Shows distance to next inspection. |
| Start counts by type | Determines overage exposure. |
| Fixed LTSA fee | Monthly cashflow item. |
| EOH reserve accrual | Variable contract cashflow item. |
| LTSA VOM | MWh-linked variable cost. |
| Start overage charges | High-cycling commercial exposure. |
| Inspection event schedule | Planned outage timing and cost. |
| Covered vs uncovered cost | Owner risk and OEM/service-provider risk split. |
| Guarantee status | Availability, heat-rate, and outage-duration compliance. |

## What The Framework Includes

The high-level framework includes these LTSA ideas:

- LTSA/CSA terms constrain inspection schedule and maintenance cost allocation.
- Scheduled inspections are triggered by EOH or factored-start thresholds.
- The Athens pilot assumes a GE CSA-style comprehensive contract.
- GT-A and GT-B are the covered units.
- CI, HGP, and MI inspection logic is included.
- Fixed fee, EOH reserve, LTSA VOM, and start overage rates are included.
- Availability, heat-rate, CI duration, and MI duration guarantees are included.
- Coverage exclusions are listed for generator, HRSG, ST, BOP, controls, insurance-dependent events, and fuel-system modifications.
- LTSA costs are separated from spark spread in sensitivity outputs.
- Dispatch Modes B and C can sacrifice some gross margin to reduce LTSA cost and risk.

## What The Framework Leaves Out

The framework still needs actual contract review before investment use.

| Missing detail | Why it matters |
| :--- | :--- |
| Actual LTSA / CSA text | Controls every payment, coverage, exclusion, and guarantee rule. |
| Exact fee frequency | The fixed-fee watch item must be resolved. |
| Actual true-up mechanics | Determines cashflow timing at inspection events. |
| Reserve balance at acquisition date | Changes near-term cash needs. |
| Exact start-counting rules | Failed starts, trips, 1x1 starts, and restarts may be treated differently. |
| Actual inspection history | Confirms current EOH, post-HGP condition, and remaining headroom. |
| Covered vs excluded cause-code mapping | Determines whether forced outages become owner cost or contract remedy. |
| Guarantee cure rights | Some contracts allow correction before damages apply. |
| Heat-rate test protocol | Measurement method can change guarantee exposure. |
| Escalation index and caps | Long-term fees depend on escalation rules. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 1 | LTSA role in the overall framework. | Green for framework intent. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.4 | Athens CSA assumptions, payment terms, guarantees, exclusions, and parameter summary. | Amber because values are assumptions pending actual contract review. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.5 and 4.6 | Start cost, HRSG/ST cost split, and VOM stack. | Amber until validated against actual plant data. |
| `docs/InfraSure_ModelingFramework_V2.md`, Appendix C | Simulated LTSA cost impact and Mode A/B/C comparison. | Amber because prototype results depend on assumed contract values. |
| [EOH And Starts](./03_eoh_and_starts.md) | Beginner explanation of EOH, starts, and inspection thresholds. | Green for learning structure. |
| [Start Costs And VOM](./04_start_costs_and_vom.md) | Beginner explanation of EOH reserve, overages, VOM, and dispatch hurdle. | Green for learning structure. |
| [Outages, Availability, And LTSA](./06_outages_availability_and_ltsa.md) | Beginner explanation of availability, outage cause, coverage, exclusions, and guarantees. | Green for learning structure. |

## Open Questions Before Investment Use

| Question | Why it matters |
| :--- | :--- |
| What is the actual LTSA / CSA text? | It overrides all framework assumptions. |
| Is the fixed fee monthly or annual? | Changes cashflow materially and affects remedy examples. |
| Which units and systems are covered? | Prevents assuming HRSG/ST/BOP risks are covered by a GT contract. |
| What are the exact CI, HGP, and MI triggers? | Determines planned outage timing. |
| What is the current reserve balance? | Determines whether future inspections create catch-up invoices. |
| How are 1x1 starts counted in a 2x1 CCGT? | Affects start limits, overages, and train-level state. |
| Are trips, failed starts, and emergency shutdowns counted separately? | High-cycling years can create hidden exposure. |
| What are the exact guarantee formulas? | Availability and heat-rate remedies depend on definitions and exclusions. |
| Which outage causes are covered, excluded, or insured? | Determines owner downside risk. |
| Are Mode B/C EOH proximity penalties contract terms or modeling choices? | Separates actual cash cost from optimization behavior. |

## Quick Recap

LTSA is the service-contract layer that turns plant operation into maintenance timing, fees, reserves, coverage decisions, exclusions, guarantees, and remedies.

For this model:

```text
EOH and starts drive inspection timing.
MWh drives LTSA VOM.
EOH drives reserve accrual.
Starts can drive overage charges.
Outage cause drives covered vs excluded cost.
Guarantee formulas drive credits, penalties, or remedies.
```

The key beginner lesson:

```text
LTSA is not just a maintenance cost.
It is a contract map from operation to cashflow and risk allocation.
```
