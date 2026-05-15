# Rotor Life Consumption

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read this guide first if starts, hot/warm/cold definitions, or EOH are new: [EOH And Starts](../basics/03_eoh_and_starts.md).

Useful related guides:

- [EOH Accumulation With Creep-Fatigue Coupling](./01_eoh_creep_fatigue_coupling.md)
- [Combustion Cycling Fatigue](./04_combustion_cycling_fatigue.md)
- [Outages, Availability, And LTSA](../basics/06_outages_availability_and_ltsa.md)

> Plant-Type Applicability
> This guide is about the gas turbine rotor. It can apply to simple-cycle GTs, CCGTs, and GT-based CHP plants. It should not be confused with steam-turbine rotor, generator rotor, or reciprocating-engine crankshaft/rotating-equipment risk.

## Why This Matters

Rotor life consumption answers a severe-risk question:

> How much of the gas turbine rotor's life budget has already been used, and how much tail risk remains hidden inside the machine?

The rotor is not a normal consumable part. It is a large, high-energy rotating assembly inside the gas turbine. If rotor damage becomes serious, the impact can be very large:

| Impact | Plain-English meaning |
| :--- | :--- |
| Forced outage | The unit may have to come offline immediately or stay offline after inspection. |
| Long repair or replacement lead time | Rotor replacement can take months, not days. |
| High uncovered cost risk | Some rotor work may sit outside routine hot-gas-path or combustor scope. |
| Safety and collateral damage concern | A rotating component stores large kinetic energy. A severe failure can damage nearby equipment. |
| Investment tail risk | The probability is low, but the cash-flow impact can be extreme. |

The framework classifies rotor life as a lower-priority degradation factor because it usually does not change daily fuel cost or capacity in a smooth way. But "lower priority" does not mean "unimportant." It means the model treats it as a low-probability, high-consequence tail-risk item.

Simple flow:

```text
starts + stops + trips + hours at speed + thermal transients
        |
        v
rotor life fraction consumed
        |
        v
small increase in GT forced outage tail risk
        |
        v
possible long outage, rotor inspection, repair, or replacement
```

## Plain-English Concept

A gas turbine rotor is the rotating core of the machine.

Beginner version:

```text
Compressor rotor pulls air in and compresses it.
Turbine rotor extracts energy from hot gas.
The shaft/discs spin at high speed and carry blades.
```

In a large frame gas turbine, the rotor includes shafts, discs/wheels, blade attachment regions, bolts or tie-bolts, spacers, and interfaces. Exact construction depends on the OEM and machine model.

The rotor sees two big stress families:

| Stress family | What causes it | Why it matters |
| :--- | :--- | :--- |
| Centrifugal stress | High-speed rotation | The rotor is being pulled outward by its own rotation. |
| Thermal stress | Heating and cooling during starts, stops, trips, and load changes | Different parts expand and cool at different rates, creating local stress. |

The model simplifies all of that into a life budget:

```text
rotor life budget = allowed equivalent starts before life assessment / replacement concern
life consumed     = accumulated severity-weighted starts
life fraction     = life consumed / design life budget
```

## Do Not Confuse These Rotors

The word "rotor" appears in several plant areas. This guide is about the gas turbine rotor.

| Term | Location | Is this guide about it? |
| :--- | :--- | :--- |
| GT rotor | Inside the gas turbine compressor/turbine | Yes. |
| ST rotor | Inside the steam turbine | No, except HRSG cycling can affect steam-turbine thermal stress. |
| Generator rotor | Inside the electrical generator | No. It has its own electrical/mechanical failure modes. |
| Compressor wheel/disc | Compressor section of the GT rotor | Yes, if part of the GT rotor life assessment. |
| Turbine wheel/disc | Hot turbine section of the GT rotor | Yes, if part of the GT rotor life assessment. |

The framework also lists owner budget reserves for steam turbine rotor/seals and generator rotor/stator repair. Those are different from the GT rotor life factor in this guide.

## Plant-Type Applicability

Rotor life follows the GT unit and its start/stop severity.

| Plant type | What still applies | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | GT rotor starts, stops, trips, and hours at speed matter. | Peaking duty may create many start-stop cycles with fewer fired hours. |
| Combined-cycle GT | Each GT rotor needs its own life state. | GT-A and GT-B can diverge under 1x1 dispatch. |
| Frame GT | Rotor inspection and life assessment can be long-lead, high-severity issues. | OEM life limits and NDE findings are central. |
| Aeroderivative GT | Rotating module life still matters. | Module replacement and maintenance structure may differ from frame GT assumptions. |
| CHP / cogeneration | GT rotor life applies if a GT is used. | Steam or heat obligations can force starts or sustained operation. |

## Where This Happens In The Plant

Basic combined-cycle location:

```text
Air -> compressor -> combustor -> turbine -> HRSG -> steam turbine -> generator
          ^                         ^
          |                         |
     GT compressor rotor       GT turbine rotor
```

The highest concern locations are not always visible from normal operations data. Rotor life can depend on:

| Area | Example concern |
| :--- | :--- |
| Bore / near-bore regions | High stress and fracture mechanics sensitivity. |
| Wheel rims and dovetails | Blade attachment cracking, fretting, local stress concentration. |
| Compressor discs | Corrosion, pitting, stress corrosion, low-cycle fatigue. |
| Turbine discs | Creep, thermal fatigue, crack initiation, oxidation effects. |
| Bolted or rabbet interfaces | Fretting, slip, assembly stress, local cracking. |

That is why a real rotor life assessment requires inspection history, non-destructive examination, material data, and OEM or expert engineering review. The framework does not claim to replace that.

## Why Starts Matter So Much

Steady operation is stressful because the rotor spins at high speed. But starts and stops are special because they create large temperature changes.

A hot start is usually less severe because the machine has not fully cooled down. A cold start is more severe because metal temperatures are farther from operating temperature.

Conceptual severity ladder:

```text
Hot start  |##########                              | 1x
Warm start |####################                    | 2x
Cold start |########################################| 4x
```

The exact OEM factors can differ. The framework uses this simple weighting:

| Start type | Rotor equivalent-start weight | Plain-English meaning |
| :--- | ---: | :--- |
| Hot start | 1.0x | Reference start severity. |
| Warm start | 2.0x | More thermal movement than a hot start. |
| Cold start | 4.0x | Highest simplified thermal transient severity. |

The purpose is not to perfectly model every stress location. The purpose is to convert different start types into one simple rotor-life counter.

## Equivalent Starts

"Equivalent starts" means starts adjusted for severity.

Example:

```text
1 hot start  = 1 equivalent start
1 warm start = 2 equivalent starts
1 cold start = 4 equivalent starts
```

So a week with 3 hot starts, 2 warm starts, and 1 cold start becomes:

```text
equivalent starts = (3 * 1) + (2 * 2) + (1 * 4)
                  = 3 + 4 + 4
                  = 11 equivalent starts
```

This lets the model compare different cycling patterns on the same scale.

## Framework Rotor Assumptions

The local framework uses these central rotor assumptions:

| Assumption | Framework value | Meaning |
| :--- | :--- | :--- |
| Starting rotor life fraction consumed | About 0.35 | The Athens-type unit is estimated to have used about 35% of its rotor life budget. |
| Rotor design life | 7,500 equivalent starts | Central denominator for the life-fraction calculation. |
| Rotor design-life range | 5,000 to 10,000 equivalent starts | Sensitivity range around the central assumption. |
| Hot/warm/cold weights | 1x / 2x / 4x | Converts daily start types into equivalent starts. |
| `P_rotor` baseline daily probability | 0.003% per day | Very low daily probability term for disc-cracking tail risk. |
| `P_rotor` range | 0.001% to 0.005% per day | Sensitivity range. |
| Certainty rating | Amber for design life, Red for `P_rotor` probability | These assumptions need sensitivity testing and asset-specific review. |

Important: the framework does not say the rotor will fail at exactly 7,500 equivalent starts. It uses 7,500 as a modeling benchmark so different dispatch policies can be compared consistently.

## Life Fraction In Plain Language

Life fraction is the percent of the rotor life budget already consumed.

```text
rotor life fraction = consumed equivalent starts / design equivalent starts
```

If design life is 7,500 equivalent starts:

| Consumed equivalent starts | Life fraction | Plain-English state |
| ---: | ---: | :--- |
| 0 | 0% | New in this simplified counter. |
| 1,875 | 25% | One quarter of the simplified budget used. |
| 2,625 | 35% | Framework starting estimate for the Athens-type unit. |
| 3,750 | 50% | Half of the simplified budget used. |
| 7,500 | 100% | Counter has reached the benchmark design-life budget. |

ASCII bar:

```text
Rotor life budget, framework starting state

0%        25%        50%        75%       100%
|----------|----------|----------|----------|
|##############----------------------------| 35% consumed
```

At 35% consumed:

```text
consumed equivalent starts = 0.35 * 7,500
                           = 2,625 equivalent starts

remaining benchmark budget = 7,500 - 2,625
                           = 4,875 equivalent starts
```

## Daily Model Inputs

Rotor life is updated from the daily operating pattern.

| Input | Frequency | Source | Why it matters |
| :--- | :--- | :--- | :--- |
| Hot starts | Daily count from hourly dispatch/events | Step 2 dispatch / operations | Adds lower-severity equivalent starts. |
| Warm starts | Daily count from hourly dispatch/events | Step 2 dispatch / operations | Adds medium-severity equivalent starts. |
| Cold starts | Daily count from hourly dispatch/events | Step 2 dispatch / operations | Adds high-severity equivalent starts. |
| Total start-stop cycles | Daily/event-level | Dispatch / operations | Main simplified rotor-life driver. |
| Cumulative hours at speed | Daily summary | Dispatch / plant historian | Captures time under centrifugal stress. |
| Thermal transient severity | Event-level or proxy | Start type, ramp history, shutdown duration | Explains why not all starts are equal. |
| Trips | Event-level | Operations / outage logs | Potentially severe, but the framework does not define a rotor trip weight. |
| Current rotor life fraction | Daily state vector | Engineering model | Opening state before today's update. |
| Rotor design life | Static or scenario assumption | OEM / framework | Denominator for life fraction. |
| Inspection findings | Outage event data | MI, borescope, NDE, OEM report | Can recalibrate the simple counter. |

Trips deserve special care. The framework defines trip weighting for combustion and HRSG fatigue, but it does not provide a rotor-specific trip weighting in Appendix B.11. For investment use, trip treatment should be an explicit calibration question rather than silently borrowing another factor.

## Daily Model Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Daily rotor equivalent starts | Engineering model | Today's severity-weighted rotor cycling. |
| Updated rotor life fraction | State vector | Closing rotor life state after today's operation. |
| `P_rotor` contribution | Forced outage module | Small GT forced-outage tail-risk term. |
| Forced outage event flag | Maintenance/failure module | Whether stochastic outage draw triggered an event. |
| Outage duration and cost classification | Financial model | Cash-flow impact if rotor-related outage occurs. |
| Investment risk signal | Scenario comparison | Whether aggressive cycling increases low-probability downside. |

Rotor life normally does not directly reduce MW capacity or increase heat rate. It mainly changes the risk state.

## Daily Update Logic

The model is daily because the dispatch decision and the stress state feed each other.

```text
start of day state
        |
        v
check forced outage probability from yesterday's stress state
        |
        v
if available, run Step 2 dispatch for today's market/weather
        |
        v
count hot/warm/cold starts and hours at speed
        |
        v
convert starts to rotor equivalent starts
        |
        v
update rotor life fraction and tomorrow's `P_rotor`
```

Simplified calculation:

```text
daily_rotor_equivalent_starts =
    1.0 * hot_starts
  + 2.0 * warm_starts
  + 4.0 * cold_starts

rotor_life_increment =
    daily_rotor_equivalent_starts / rotor_design_equivalent_starts

closing_rotor_life_fraction =
    opening_rotor_life_fraction + rotor_life_increment
```

The forced-outage check uses the opening state. Today's starts then update the closing state, which affects tomorrow's risk.

## How This Feeds Step 2 Dispatch

Step 2 is the dispatch model. It decides whether the plant runs, starts, stays offline, or cycles based on market prices, weather, and current plant parameters.

Rotor life affects Step 2 differently from heat rate or capacity:

| Factor | Direct Step 2 effect? | How dispatch sees it |
| :--- | :--- | :--- |
| Capacity derate | Yes | Less MW available in profitable hours. |
| Heat rate degradation | Yes | Higher fuel cost, lower spark spread. |
| Start cost | Yes | Higher cost to turn on. |
| Rotor life fraction | Usually indirect | Higher tail risk and possible forced outage state. |

In a simple dispatch run, Step 2 may not bid differently just because rotor life is 35% instead of 36%. But across scenarios, rotor life matters because aggressive cycling can increase future forced-outage risk and long-lead repair exposure.

Daily feedback:

```text
Dispatch chooses starts today
        |
        v
starts consume rotor life
        |
        v
rotor life increases future `P_rotor`
        |
        v
future availability and downside risk change
```

This is why the analysis looks daily rather than purely monthly or annual. A month-level model can count total starts, but it loses the order of events, forced-outage timing, and how yesterday's stress state affects today's availability.

## Worked Example 1: One Cycling Day

Assume:

| Item | Value |
| :--- | ---: |
| Opening rotor life fraction | 35.000% |
| Rotor design life | 7,500 equivalent starts |
| Hot starts today | 1 |
| Warm starts today | 1 |
| Cold starts today | 0 |

Calculation:

```text
daily equivalent starts = (1 * 1) + (1 * 2) + (0 * 4)
                        = 3 equivalent starts

life increment = 3 / 7,500
               = 0.0004
               = 0.040 percentage points

closing life fraction = 35.000% + 0.040%
                      = 35.040%
```

Plain-English reading:

```text
One mixed cycling day barely changes the visible percentage.
But repeated cycling days slowly move the rotor toward higher tail risk.
```

## Worked Example 2: Cold Starts Add Up Faster

Assume 10 cold starts over a period.

```text
equivalent starts = 10 * 4
                  = 40 equivalent starts

life increment = 40 / 7,500
               = 0.00533
               = 0.533 percentage points
```

Compare that with 10 hot starts:

```text
hot-start equivalent starts = 10 * 1 = 10
hot-start life increment    = 10 / 7,500 = 0.133 percentage points
```

Same number of physical starts. Very different rotor-life impact.

| Pattern | Physical starts | Equivalent starts | Life increment |
| :--- | ---: | ---: | ---: |
| 10 hot starts | 10 | 10 | 0.133 percentage points |
| 10 warm starts | 10 | 20 | 0.267 percentage points |
| 10 cold starts | 10 | 40 | 0.533 percentage points |

## Worked Example 3: Why The Design-Life Assumption Matters

The same 40 equivalent starts has a different impact depending on the assumed design life.

| Design-life assumption | 40 equivalent starts consume |
| ---: | ---: |
| 5,000 equivalent starts | 0.800 percentage points |
| 7,500 equivalent starts | 0.533 percentage points |
| 10,000 equivalent starts | 0.400 percentage points |

This is why the framework marks rotor design life as Amber certainty. The assumption is plausible for a learning model, but actual investment diligence should confirm the OEM life basis for the specific unit.

## ASCII Plot: Linear Life Counter

The framework's life counter is linear against equivalent starts.

```text
Rotor life fraction consumed

100% |                              X benchmark design-life budget
     |                           __/
 75% |                       ___/
     |                   ___/
 50% |               ___/
     |           ___/
 35% |       X__/        framework starting estimate
     |   ___/
  0% |__/
     +--------------------------------
       0        2,625              7,500
              equivalent starts
```

The risk curve does not have to be exactly linear. The framework only says `P_rotor` scales with life fraction. The exact shape should be sensitivity-tested.

## `P_rotor` In The Forced Outage Model

The framework's GT forced outage term is:

```text
P_GT = P_combustion(fatigue_index)
     + P_TBC(Weibull_state)
     + P_rotor(life_fraction)
```

`P_rotor` is the rotor-related piece. It is very small on any single day:

```text
central baseline = 0.003% per day
range            = 0.001% to 0.005% per day
```

Beginner interpretation:

```text
This is not saying rotor failure is expected tomorrow.
It is saying rotor condition contributes a small daily chance
of a severe forced-outage event.
```

Why this still matters:

| Feature | Why investors care |
| :--- | :--- |
| Low daily probability | It can disappear inside average-case economics. |
| Severe event size | One event can dominate a downside case. |
| Long lead time | Lost revenue can persist for months. |
| Coverage uncertainty | LTSA/insurance terms may not fully cover the event. |
| Dispatch link | More cycling can move the tail-risk state over time. |

Conceptual tail-risk shape:

```text
Rotor outage tail risk

high |                              /
     |                           __/
     |                       ___/
     |                   ___/
low  |__________________/
     +--------------------------------
       lower life fraction     higher life fraction
```

This plot is conceptual. The current framework does not provide a detailed rotor hazard curve.

## What The Framework Includes

The high-level framework includes the parts needed for scenario comparison:

| Included item | Where it appears | Why it matters |
| :--- | :--- | :--- |
| Rotor life as a degradation factor | Stress factor table | Keeps rotor risk visible even though it is lower priority. |
| Start-stop cycles and thermal severity | Causal variables | Connects dispatch cycling to rotor life. |
| Design-life denominator | Appendix B.11 | Converts equivalent starts into life fraction. |
| Hot/warm/cold weighting | Appendix B.11 | Distinguishes mild starts from severe starts. |
| Starting life fraction | Starting-state assumptions | Avoids pretending the plant begins as new. |
| `P_rotor` in GT forced outage | Section 3.2.2 and Appendix B.8 | Converts rotor life state into tail-risk probability. |
| MI rotor inspection | LTSA scope | Recognizes that major inspections can include rotor inspection. |
| Uncertainty rating | Appendix B | Flags assumptions requiring sensitivity testing. |

## What The Framework Leaves Out

The framework is honest about being an investment-grade digital twin, not an OEM rotor-life assessment.

Missing or simplified items:

| Missing detail | Why it matters |
| :--- | :--- |
| Actual rotor serial history | Different rotors can have different design basis, repairs, and service history. |
| OEM life bulletin details | Actual factored-start and factored-hour rules are model-specific. |
| Complete historical starts and trips | The starting 35% estimate may be wrong without history. |
| Rotor-specific trip weighting | Trips may be severe, but Appendix B.11 does not define a rotor trip factor. |
| Hours-at-speed weighting | Framework names hours at speed as causal but uses starts as the main simple counter. |
| Overspeed or abnormal event history | Rare events can matter more than normal dispatch starts. |
| NDE findings | Crack indications, dimensional changes, and material condition can override simple counters. |
| FEA / fracture mechanics | Public learning docs cannot replace detailed stress and crack-growth analysis. |
| GT-by-GT tracking | A 2x1 site needs separate rotor state for each gas turbine. |
| Repair and replacement logistics | Lead time, spare availability, shop capacity, and insurance treatment drive cash impact. |

This is the key limitation:

```text
The framework can estimate rotor tail-risk pressure.
It cannot certify rotor remaining life.
```

## Source Basis And Uncertainty

| Source | How it supports this guide | Uncertainty |
| :--- | :--- | :--- |
| [InfraSure_ModelingFramework_V2.md](../../InfraSure_ModelingFramework_V2.md) | Provides the actual framework assumptions: 7,500 equivalent starts, 5,000-10,000 range, hot/warm/cold weights, `P_rotor`, and starting life fraction. | This is the controlling model source. |
| [InfraSure_GT_DigitalTwin_v2.pdf](../../InfraSure_GT_DigitalTwin_v2.pdf) | Confirms rotor life is a low-priority stress factor tied to start-stop cycles, dispatch, catastrophic risk, and life fraction vs design life. | High-level presentation, not a detailed calculation spec. |
| [EPRI / ETN Global rotor life paper](https://etn.global/wp-content/uploads/2017/11/21_EPRI_JS.pdf) | Supports the idea that rotor life management depends on OEM limits, actual operational history, inspection, material condition, and engineering assessment. | Public paper is general; unit-specific OEM data is still needed. |
| [NASA NASALife reference](https://ntrs.nasa.gov/citations/20110015541) | Supports the general fatigue/creep life-prediction idea: cyclic thermo-mechanical loading, LCF, creep, material data, and load counting matter. | Aerospace methodology reference, not a GE 7FA rotor rulebook. |
| [NERC GADS DRI](https://www.nerc.com/globalassets/programs/rapa/gads/conventional/gads_dri_2024.pdf) | Supports outage and availability reporting context and the use of reliability/availability data for benchmarking and outage analysis. | Reporting framework, not a rotor failure probability source. |

Confidence by item:

| Item | Confidence | Reason |
| :--- | :--- | :--- |
| Rotor risk belongs in the model | High | Local framework and external rotor-life literature agree it is a real tail-risk category. |
| Hot/warm/cold starts matter | High | Thermal transient severity is a core driver. |
| 7,500 equivalent-start central denominator | Medium | Plausible framework assumption, but actual OEM/model-specific basis must be checked. |
| 1x/2x/4x rotor weighting | Medium | Useful simplification, but actual factored-start rules can differ. |
| `P_rotor = 0.003%/day` baseline | Low | Framework itself marks this Red and sensitivity-test required. |
| Exact outage cost or duration | Low to Medium | Strongly depends on spare rotor availability, scope, contract, and insurance. |

## Open Questions Before Investment Use

Before using rotor life for a serious investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| What exact GT model, rotor design, and rotor serial numbers are installed? | Rotor life rules are model-specific. |
| What does the OEM say about factored starts, factored hours, inspections, and extensions? | The framework denominator may need replacement. |
| What is the actual historical start, stop, trip, and fired-hour history for each GT? | Starting life fraction may be materially different from 35%. |
| Were there overspeed, severe trip, vibration, rub, or abnormal thermal events? | Rare events can dominate rotor risk. |
| What did the last MI rotor inspection or NDE report show? | Inspection findings can override simplified counters. |
| Are GT rotor events covered under the LTSA, excluded, capped, or shared? | Determines cash-flow impact. |
| Is a spare rotor available, and what is the realistic lead time? | Drives outage duration and downside severity. |
| Should trips receive a separate rotor weighting? | Current framework does not specify one. |
| Should hours at speed be included separately from starts? | Framework names hours at speed as causal but simplifies life consumption to starts. |
| Should rotor life be tracked separately for each GT? | A fleet or multi-GT site can have uneven cycling histories. |

## Simple Mental Model

Use this mental model:

```text
Capacity degradation asks:
"How many MW can I sell?"

Heat-rate degradation asks:
"How much fuel do I need per MWh?"

Start-cost degradation asks:
"How expensive is it to turn on?"

Rotor life asks:
"How much severe low-probability mechanical risk am I carrying?"
```

Rotor life is not mainly a daily margin variable. It is a downside-risk variable that accumulates through daily dispatch decisions.

## Final Takeaway

Rotor life consumption is a simplified daily counter for severe GT rotating-component risk: starts consume equivalent-start life, the life fraction updates the forced-outage tail-risk state, and asset-specific OEM/inspection data is required before relying on the result for investment decisions.
