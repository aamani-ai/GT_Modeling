# EOH And Starts

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

Read this if LTSA/CSA service-contract structure is new: [LTSA And Service Contracts](./08_ltsa_and_service_contracts.md).

Read this if you want to see how starts, load modes, seasons, price regimes, and stress counters fit together: [Operating Partitions And Model Signals](./09_operating_partitions_and_model_signals.md).

> Plant-Type Note
> EOH and start classes are universal modeling ideas, but the numeric rules are not universal. Hot/warm/cold thresholds, start EOH multipliers, trip penalties, and inspection thresholds depend on the OEM, turbine model, LTSA/CSA, operating procedures, and plant type. The Athens values in this guide are worked-example assumptions for a GE 7FA 2x1 CCGT.

## First-Time Reader Map

If this topic is new, do not start with the formula. Start with the simple business problem:

```text
A gas turbine can make money by running today.
But running, starting, stopping, and tripping all consume maintenance life.
The model needs a way to count that life consumption.
That counter is EOH.
```

The guide uses several terms that show up throughout the framework:

| Term | Stands for | First-time meaning |
| :--- | :--- | :--- |
| GT | Gas turbine | The machine that burns fuel, spins, and makes power. |
| EOH | Equivalent Operating Hours | A contract/maintenance counter that converts running and starts into "life used." |
| Fired hour | Not an acronym | One hour with fuel burning in the GT. |
| Start | Not an acronym | Turning the GT from offline to online. |
| Hot/warm/cold start | Start categories | Labels based on how long the unit has been shut down. |
| Trip | Not an acronym | An unplanned or emergency shutdown from operation. |
| Load swing | Not an acronym | A large movement in output, such as going from low load to high load. |
| LTSA / CSA | Long-Term Service Agreement / Contractual Service Agreement | Service contract that defines inspections, payments, coverage, and limits. |
| CI | Combustion Inspection | A planned inspection focused mainly on combustion-system parts. |
| HGP | Hot Gas Path inspection | A deeper inspection of turbine hot-section parts exposed to hot gas. |
| MI | Major Inspection | The largest planned inspection in this simplified cycle. |
| Headroom | Not an acronym | Distance from today's EOH to the next inspection threshold. |

The mental stack is:

```text
physical operation -> contract counter -> inspection timing -> dispatch economics
```

## The Physical Story Before The Math

A start is not just pressing an on button.

Simplified sequence:

```text
offline
  |
  v
purge / prepare the unit
  |
  v
ignite fuel
  |
  v
warm up metal parts
  |
  v
synchronize to the grid
  |
  v
load up to produce MW
```

During this sequence, the GT metal heats up and expands. During shutdown, it cools and contracts. Repeating that heating and cooling creates stress.

That is the core idea behind starts:

```text
temperature change
        |
        v
metal expansion / contraction
        |
        v
thermal stress
        |
        v
life consumption
```

The colder the unit is before start, the larger the temperature change tends to be. That is why a cold start usually consumes more life than a warm start, and a warm start consumes more life than a hot start.

## Why Inspections Exist

Inspections exist because high-temperature GT parts wear out, crack, oxidize, foul, or lose coating over time.

Beginner version:

```text
The plant earns revenue by operating.
Operation creates wear.
Inspections find, repair, or replace worn parts before failure risk gets too high.
```

This is especially important for a gas turbine because the machine has:

| Area | Why it needs inspection |
| :--- | :--- |
| Combustor | Handles flame, fuel mixing, vibration, and thermal cycling. |
| Turbine blades and vanes | Sit in very hot gas and carry high mechanical stress. |
| Compressor | Can foul, erode, corrode, or suffer blade issues. |
| Rotor and bearings | High-speed rotating parts need condition checks. |
| Seals and clearances | Wear can reduce performance or increase risk. |

The model does not inspect parts physically. It estimates when inspections are due based on EOH and contract thresholds.

## CI, HGP, And MI In Plain Language

Think of `CI`, `HGP`, and `MI` as planned service visits with different depth.

| Event | Full name | Simple meaning | Typical reason |
| :--- | :--- | :--- | :--- |
| CI | Combustion Inspection | Smaller planned inspection focused on combustion hardware. | Combustor parts see flame, cycling, vibration, and wear. |
| HGP | Hot Gas Path inspection | Deeper inspection of turbine hot-section parts. | Hot gas path parts see high temperature, coatings, creep, and fatigue. |
| MI | Major Inspection | Largest planned inspection in this simplified sequence. | Checks broader GT condition, including deeper mechanical items. |

Very simplified depth ladder:

```text
CI   |##########                    | combustion focus
HGP  |######################        | hot-section focus
MI   |########################################| broad major scope
```

The exact scope depends on the OEM and contract. In the local framework, the Athens-type plant starts just after an HGP at 24,000 EOH, then moves toward CI and MI thresholds.

```text
24,000 EOH: HGP just completed
32,000 EOH: next CI threshold
40,000 EOH: next CI threshold
48,000 EOH: MI threshold
```

This is why `CI` matters in the rest of the guide: it is the next planned inspection that the EOH counter is moving toward.

## How One Start Becomes A Model Signal

One real-world start becomes several model signals.

```text
plant starts today
  |
  +--> start type is classified as hot, warm, or cold
  |
  +--> EOH is added to the maintenance counter
  |
  +--> start cost may be charged in dispatch economics
  |
  +--> annual start limits may move closer to overage
  |
  +--> physical stress trackers may increase
```

So when the framework says "start," it is not only talking about one event in the operations log. It is also talking about a cost, a maintenance counter, a contract limit, and a physical stress signal.

## Why This Matters

EOH answers a simple question:

> How much maintenance life did the plant consume?

EOH means Equivalent Operating Hours. It converts different types of operation into a common maintenance-life counter. A normal fired hour consumes some life. A start consumes additional life. A cold start consumes much more life than a hot start. A trip can consume even more.

This matters because the LTSA/CSA inspection schedule is tied to EOH thresholds. In the Athens-type framework, the plant starts just after a Hot Gas Path inspection at 24,000 EOH. The next combustion inspection is at 32,000 EOH. That means the model begins with 8,000 EOH of headroom.

```text
24,000 EOH today
        |
        | 8,000 EOH headroom
        v
32,000 EOH next CI threshold
```

If dispatch is aggressive, EOH accumulates faster and inspections arrive sooner. If dispatch is conservative near thresholds, the plant may sacrifice some revenue to delay maintenance cost.

## Plain-English Concept

EOH is not the same as clock hours.

If the plant runs for 10 hours, that is 10 fired hours. But if it had to start before those 10 hours, the start also consumes life. The LTSA converts that start into additional equivalent hours.

Beginner version:

```text
Fired hours = time spent running
Starts      = thermal stress from turning on
Trips       = severe stress from emergency shutdown
EOH         = common counter for maintenance life
```

The key idea is that cycling can make a plant age faster than its run hours suggest.

## Fired Hours Vs EOH

Fired hours are easy:

```text
If the GT is burning fuel for 8 hours, it has 8 fired hours.
```

EOH adds factored events:

```text
EOH = fired-hour EOH + start EOH + trip EOH + load-swing EOH
```

A plant can have low fired hours but high EOH if it starts and stops frequently.

| Operating pattern | Fired hours | Starts | EOH behavior |
| :--- | ---: | :--- | :--- |
| Baseload-like | High | Low | EOH mostly follows fired hours. |
| Daily cycling | Medium | High | EOH grows faster than fired hours. |
| Peaking / reserve | Low | High | EOH can be dominated by starts. |
| Trip-heavy operation | Variable | Severe trips | EOH and outage risk can jump quickly. |

## Start Types

The Athens-type framework classifies starts by shutdown duration:

| Start type | Shutdown duration | Plain-English meaning |
| :--- | :--- | :--- |
| Hot start | Less than 8 hours | Equipment is still hot; thermal shock is lower. |
| Warm start | 8 to 72 hours | Equipment cooled part way; thermal stress is higher. |
| Cold start | More than 72 hours | Equipment is cold; thermal stress is highest. |
| Emergency trip | Forced shutdown from load | Not a normal start, but a severe event for life accounting. |

ASCII timeline:

```text
Shutdown duration

0 hr             8 hr                         72 hr
 |---------------|-----------------------------|
      hot start            warm start              cold start
```

Why cold starts are expensive:

```text
Hot metal expands less from already-hot condition.
Cold metal must warm up much more.
More temperature change -> more thermal stress -> more life consumed.
```

## Plant-Type Variations

The concept of "start severity" exists across gas plants, but the classification can change.

| Plant type | What stays the same | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Starts still create GT thermal stress and contract counters. | No HRSG/ST warm-up; start cost and timing are GT-only. |
| Combined-cycle GT | GT starts still matter. | HRSG and ST warm-up can make the plant start class and cost more complex. |
| Frame GT | Starts still consume life. | Larger thermal mass can make warm-up, cool-down, and EOH rules different from aero units. |
| Aeroderivative GT | Starts still consume maintenance life. | Start capability, module maintenance, and contract multipliers may differ materially. |
| CHP / cogeneration | Starts still affect equipment life. | Steam-host obligations can decide whether a restart is necessary even when power prices are weak. |

Use the shutdown-duration plot above as the Athens-style teaching example, not as a universal rule.

## Framework EOH Counting Rules

The Athens-type LTSA assumptions use these EOH rates:

| Operation | EOH impact |
| :--- | ---: |
| Fired hour on natural gas at base load | 1.0 EOH/hr |
| Hot start | 50 EOH per start |
| Warm start | 150 EOH per start |
| Cold start | 350 EOH per start |
| Emergency trip from full load | 500 EOH per event |
| Load swing greater than 40% rated | 0.3 EOH per swing cycle |

This table is the bridge between daily dispatch and maintenance timing.

```text
Hourly dispatch schedule
        |
        v
fired hours + start type + trips + load swings
        |
        v
EOH added today
        |
        v
distance to next inspection threshold
```

## Simple EOH Examples

### Example 1: One Hot Start Day

Assume one GT has:

| Item | Value |
| :--- | ---: |
| Fired hours | 10 |
| Hot starts | 1 |
| Large load swings | 2 |

EOH calculation:

```text
EOH = fired hours + hot start EOH + load swing EOH
EOH = 10 + 50 + (2 * 0.3)
EOH = 60.6
```

The GT only ran for 10 hours, but it consumed 60.6 EOH under this simplified contract logic.

### Example 2: One Cold Start Day

Assume:

| Item | Value |
| :--- | ---: |
| Fired hours | 10 |
| Cold starts | 1 |
| Large load swings | 0 |

EOH calculation:

```text
EOH = 10 + 350
EOH = 360
```

The same 10 fired hours can consume much more maintenance life if they follow a cold start.

### Example 3: Trip Event

Assume:

| Item | Value |
| :--- | ---: |
| Fired hours before trip | 6 |
| Emergency trip | 1 |

EOH calculation:

```text
EOH = 6 + 500
EOH = 506
```

That is why trips matter. They are not just lost operating hours; they can consume a large block of equivalent life and can raise outage risk.

## ASCII Comparison: Same Fired Hours, Different EOH

```text
10 fired hours only       |##########                    | 10 EOH
10 hr + hot start         |##############################| 60 EOH
10 hr + warm start        |############################################| 160 EOH
10 hr + cold start        |############################################################| 360 EOH
6 hr + trip               |####################################################################| 506 EOH
```

The bars are illustrative, not to exact scale. The point is directionally important: start type can dominate the day's EOH.

## Plant Context: Athens-Type GE 7FA

The framework starts the plant at:

| State variable | Initial value | Meaning |
| :--- | ---: | :--- |
| Contractual EOH, GT-A | 24,000 | HGP just completed. |
| Contractual EOH, GT-B | 24,000 | HGP just completed. |
| Next inspection threshold | 32,000 EOH | First CI threshold. |
| EOH headroom | 8,000 EOH | Distance from 24,000 to 32,000. |

The planned inspection thresholds are:

| Event | EOH trigger | EOH from starting state | Estimated outage duration |
| :--- | ---: | ---: | :--- |
| CI | 32,000 | 8,000 | 10 to 15 days |
| CI | 40,000 | 16,000 | 10 to 15 days |
| MI | 48,000 | 24,000 | 45 to 60 days |

So the model needs to know not only whether the plant earns money today, but also whether today's dispatch pulls an inspection closer.

## How EOH Feeds Step 2 Dispatch

Step 2 dispatch decides whether to run the plant. EOH changes the decision because it changes future maintenance economics.

The framework has three dispatch modes:

| Mode | EOH behavior | Dispatch intuition |
| :--- | :--- | :--- |
| Mode A: Maximize dispatch | No EOH proximity penalty. | Run whenever short-term margin is positive. |
| Mode B: Balanced | Start costs rise near threshold. | Run freely when far from inspection, self-curtail marginal days near threshold. |
| Mode C: Minimize LTSA cost | Stronger penalty near threshold. | Avoid marginal starts to defer maintenance. |

Simple dispatch logic:

```text
Far from CI threshold:
  hot start may be acceptable if power margin is positive

Near CI threshold:
  same hot start may be rejected if it pulls inspection closer
```

The plant can be "in the money" on fuel and power price but still unattractive after considering EOH proximity.

## Daily Model Inputs And Outputs

EOH is updated at the daily checkpoint using the hourly operating profile.

### Inputs

| Input | Frequency | Source | What it does |
| :--- | :--- | :--- | :--- |
| Fired hours | Hourly schedule summarized daily | Dispatch model | Adds operating-hour EOH. |
| Start type | Event-level / daily summary | Dispatch model | Adds hot, warm, or cold start EOH. |
| Shutdown duration | State variable | Engineering model / dispatch history | Determines hot, warm, or cold classification. |
| Trips | Event-level | Dispatch / failure module | Adds severe trip EOH. |
| Load swings | Hourly load profile | Dispatch model | Adds partial EOH for large swings. |
| Fuel type | Asset/dispatch input | Asset specs | Can change EOH rate if contract says so. |
| Current EOH | Daily state | Engineering model | Determines headroom to next inspection. |

### Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Updated contractual EOH | LTSA schedule | Determines CI/MI timing and reserve billing. |
| EOH headroom | Dispatch model | Distance to next inspection threshold. |
| Start-cost multiplier | Dispatch model | Penalizes starts near thresholds in Modes B/C. |
| Inspection trigger flag | Maintenance module | Indicates planned outage and cost event. |
| Stress summary | Engineering model | Helps align contractual EOH with physical damage trackers. |

Simple daily flow:

```text
Start of day state:
  EOH = 24,000
  next CI = 32,000

Dispatch output:
  10 fired hours
  1 hot start

Daily EOH update:
  +60 EOH

End of day state:
  EOH = 24,060
  headroom = 7,940 EOH
```

## Contractual EOH Vs Physical Damage

This basics guide is about contractual EOH. The later degradation guide will go deeper into creep-fatigue coupling.

Still, it is important to know that the framework tracks two related but different ideas:

| Tracker | Main use | Beginner explanation |
| :--- | :--- | :--- |
| Contractual EOH | LTSA billing and inspection timing | The contract's way of counting life. |
| Physical damage | Forced outage risk and stress state | The engineering model's way of estimating actual component stress. |

These can diverge.

Example:

```text
Contract may say:
  one hot start = 50 EOH

Physics may say:
  actual fatigue damage depends on metal temperature, ramp profile,
  load swing severity, and creep-fatigue interaction.
```

For investment modeling, both views matter:

- Contractual EOH tells us when inspections and LTSA costs happen.
- Physical damage tells us whether forced outage risk is rising between inspections.

## Start Overage Charges

EOH is not the only start-related commercial exposure. The framework also includes annual contracted start limits.

| Start type | Annual contracted limit | Overage charge |
| :--- | ---: | ---: |
| Hot start | 150 starts/yr | $8,500 per excess start |
| Warm start | 35 starts/yr | $42,000 per excess start |
| Cold start | 5 starts/yr | $125,000 per excess start |
| Emergency trip | 3 events/yr | $80,000 per excess event |

This means starts can affect economics in two ways:

```text
Start today
  |
  +--> adds EOH and pulls inspection closer
  |
  +--> may create start overage charge if annual limit is exceeded
```

The framework notes that the static prototype dispatch schedule creates many hot and warm starts, which can create material overage charges. The later dynamic dispatch modes are expected to reduce starts near thresholds.

## EOH Reserve Billing

The framework includes a variable EOH reserve:

```text
$175 per EOH accrued
```

Example:

```text
Daily EOH = 60.6
EOH reserve rate = $175/EOH

Daily EOH reserve accrual = 60.6 * $175
Daily EOH reserve accrual = $10,605
```

This is not the full maintenance cost. It is the reserve billing mechanism in the assumed LTSA structure. Inspection events later reconcile the reserve against actual covered and uncovered costs.

## Why Step 2 Needs Yesterday's EOH

The dispatch model should not treat the plant as brand new every day. Yesterday's EOH determines today's distance to the next inspection.

```text
Day 1:
  EOH = 24,000
  headroom = 8,000
  marginal hot start looks acceptable

Later:
  EOH = 31,400
  headroom = 600
  same hot start may be expensive because CI is close
```

This is the reason the model has daily feedback. The economic cost of a start depends on where the plant is in the inspection cycle.

## What The Framework Includes

The high-level framework includes these EOH and start concepts:

- Hourly dispatch provides fired hours, start type, and load profile.
- Contractual EOH drives LTSA inspection timing and billing.
- Hot, warm, cold, trip, and load-swing EOH multipliers are defined.
- The plant starts at 24,000 EOH after HGP.
- The next CI threshold is 32,000 EOH.
- Start costs can rise near EOH thresholds in Modes B and C.
- Start overage charges apply when annual contracted limits are exceeded.
- Physical creep-fatigue damage is tracked separately from contractual EOH.

## What The Framework Leaves Out

The high-level framework is enough for a learning model, but several details need confirmation before investment use.

| Missing detail | Why it matters |
| :--- | :--- |
| Actual LTSA start and EOH terms | The current values are assumptions pending contract review. |
| Unit-level 1x1 vs 2x1 start accounting | A single-GT start may not consume EOH the same way as both GTs starting. |
| Exact start classification logic | Need clear treatment for shutdown duration boundaries and failed starts. |
| Actual historical start counts | Needed to calibrate expected overage charges. |
| Load-swing counting method | The framework's 0.3 EOH per swing is a sensitivity item. |
| Trip severity categories | A full-load trip may differ from lower-load trips. |
| Whether EOH applies per GT or plant block in every table | Prevents double-counting in a 2x1 plant. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.3 | Daily dispatch inputs include fired hours, start type, and load profile. | Green for model architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.4 | EOH proximity changes dispatch behavior by mode. | Green for model design. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.4.2 | Inspection thresholds and EOH counting rules. | Amber because values are assumed pending LTSA review. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.4.4 | Contracted start baselines and overage charges. | Amber because values are assumed pending LTSA review. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Dispatch-to-damage flow and daily time-stepping framing. | Green for framework communication. |
| Cambridge Aeronautical Journal EOH paper | EOH as a life-consumption and maintenance-planning concept; starts and operating hours as key drivers. | Green for general concept, not plant-specific calibration. |

## Open Questions Before Investment Use

Before relying on EOH outputs in a final investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| What are the exact LTSA EOH multipliers for this asset? | Contract values control inspection timing and billing. |
| Are EOH thresholds tracked separately for GT-A and GT-B? | The 2x1 plant can have asymmetric operation. |
| How are 1x1 starts counted against plant-level start limits? | Important for partial dispatch economics. |
| How are failed starts counted? | Failed starts can consume life and may trigger charges. |
| How are trips categorized by load level? | Trip severity may not be one-size-fits-all. |
| Does the contract use both starts and EOH, or EOH only? | Some structures track starts separately from hours. |
| How should load swings be counted from hourly dispatch data? | Affects fatigue and EOH estimates. |
| Are start overages measured annually, quarterly, or by contract year? | Changes timing of cashflow impact. |

## Quick Recap

EOH turns operating behavior into maintenance life consumption.

For this model:

```text
Hourly dispatch creates fired hours and starts.
Start type depends on shutdown duration.
Fired hours + starts + trips + load swings create daily EOH.
Daily EOH reduces headroom to inspection thresholds.
EOH proximity changes tomorrow's Step 2 dispatch economics.
```

That is why EOH and starts come early in the basics path. They explain how a dispatch decision today can create a maintenance cost tomorrow.
