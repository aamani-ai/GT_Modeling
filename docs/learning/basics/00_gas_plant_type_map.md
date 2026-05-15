# Gas Plant Type Map

## Why This Guide Exists

The learning docs use the Athens GE 7FA 2x1 combined-cycle plant as the first worked example. That is useful, but it should not accidentally become the definition of every gas plant.

This guide creates the broader map.

```text
Gas plant modeling
  |
  +--> universal gas-plant ideas
  |
  +--> plant-type-specific equipment and constraints
  |
  +--> worked examples such as Athens 2x1 CCGT
```

Read this guide before the CCGT anatomy guide if you are trying to understand how the same modeling ideas change across simple-cycle, combined-cycle, frame, aeroderivative, and CHP plants.

## First-Time Reader Map

If this topic is new, start with one question:

> What kind of gas plant are we modeling?

That question matters because plant type changes the equipment, costs, constraints, degradation factors, and dispatch logic.

Key terms:

| Term | First-time meaning |
| :--- | :--- |
| Gas plant | Power plant that uses gas fuel to produce electricity, steam, or both. |
| Gas turbine | Machine that compresses air, burns fuel, and extracts power from hot gas. |
| Simple-cycle GT | Gas turbine plant without a steam bottoming cycle. |
| Combined-cycle GT | Gas turbine plant that uses GT exhaust heat to make steam and extra power. |
| CCGT | Combined-cycle gas turbine. |
| CT | Combustion turbine; often used for simple-cycle gas turbines. |
| Frame GT | Large industrial gas turbine, often used in big CCGT blocks. |
| Aeroderivative GT | Gas turbine derived from aircraft-engine technology, often faster-starting and flexible. |
| CHP / cogeneration | Plant that produces electricity and useful steam or heat. |
| Reciprocating engine | Gas-fired piston engine generator; optional future scope because it is not a GT. |
| Worked example | A specific plant case used to make the concepts concrete. |

The mental stack is:

```text
plant type -> equipment present -> constraints -> model variables -> dispatch and risk
```

## Universal Vs Plant-Type-Specific

Some ideas are broad. Other ideas only apply to certain plant types.

| Concept | Universal gas-plant idea | Plant-type-specific detail |
| :--- | :--- | :--- |
| Capacity | Every plant has a feasible MW range. | Pmax/Pmin shape differs by GT type, steam cycle, cooling system, and weather. |
| Heat rate | Fuel intensity affects marginal cost. | Simple-cycle, CCGT, aero, frame, and CHP heat-rate behavior differs. |
| Starts | Starting consumes cost, time, and wear. | Hot/warm/cold definitions and start costs are OEM/contract/plant specific. |
| Dispatch | The model decides when running is economic. | CCGTs, peakers, and CHP assets have different constraints and objectives. |
| Outages | Unavailability blocks or reduces output. | HRSG/ST outages only apply where those systems exist. |
| Degradation | Operation changes equipment condition. | HRSG cycling is CCGT/CHP-specific; GT compressor degradation is GT-specific. |
| Contracts | Service agreements define commercial treatment. | LTSA/CSA terms differ by OEM, technology, plant, and negotiated scope. |

Use this rule:

```text
Teach the universal concept first.
Then show plant-type variations.
Then use Athens as a worked CCGT example.
```

## Plant Types At A Glance

| Plant type | Basic equipment | Common role | Modeling warning |
| :--- | :--- | :--- | :--- |
| Simple-cycle GT | GT + generator + stack | Peaking, reserves, fast response | No HRSG/ST cost or damage bucket. |
| Combined-cycle GT | GT + HRSG + ST + generator(s) | Mid-merit, cycling, baseload, flexible operation | GT and steam-side constraints both matter. |
| Frame GT | Large industrial GT | Large simple-cycle or CCGT blocks | Heavier thermal mass; start logic can differ from aero units. |
| Aeroderivative GT | Smaller/faster GT technology | Fast start, peaking, flexibility | Maintenance, starts, ramping, and module swaps can differ. |
| CHP / cogeneration | GT/boiler plus steam or heat host | Electricity plus useful heat/steam | Steam-host obligation can dominate power dispatch. |
| Gas reciprocating engine | Gas piston engine generator | Fast flexible generation, distributed assets | Optional future scope; GT degradation guides do not directly apply. |

## Simple-Cycle Gas Turbine

A simple-cycle gas turbine makes electricity directly from the gas turbine.

```text
natural gas + air
      |
      v
   +------+
   |  GT  |------ generator ------ electricity
   +------+
      |
      v
 exhaust stack
```

Key modeling points:

| Topic | Simple-cycle treatment |
| :--- | :--- |
| HRSG/ST | Not present. |
| Start costs | GT-only start cost bucket. |
| Heat rate | Usually higher than CCGT because exhaust heat is not recovered. |
| Dispatch | Often focused on high-price hours, reserves, and fast response. |
| Degradation | GT compressor, combustor, hot section, TBC, and rotor can still matter. |
| Outages | No HRSG/ST outage category, but GT, controls, generator, and BOP still matter. |

Beginner takeaway:

```text
Simple-cycle GT = simpler equipment stack, faster dispatch logic,
but usually worse fuel efficiency than CCGT.
```

Detailed guide: [Simple-Cycle Gas Turbine](../plant_types/01_simple_cycle_gt.md).

## Combined-Cycle Gas Turbine

A combined-cycle plant uses GT exhaust heat to make steam and produce extra electricity.

```text
natural gas + air
      |
      v
     GT ---- electricity
      |
      | hot exhaust
      v
    HRSG ---- steam ---- ST ---- electricity
      |
      v
    stack
```

Key modeling points:

| Topic | CCGT treatment |
| :--- | :--- |
| HRSG/ST | Present and important. |
| Start costs | GT plus HRSG/ST start cost buckets. |
| Heat rate | Usually better than simple-cycle because exhaust heat is recovered. |
| Dispatch | Can be baseload, mid-merit, cycling, or flexible depending on market. |
| Degradation | GT damage plus HRSG cycling and steam-side effects. |
| Outages | GT, HRSG, ST, BOP, controls, and generator outage categories can all matter. |

The existing guide [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md) explains the physical equipment in detail.

Detailed plant-type guide: [Combined-Cycle Gas Turbine](../plant_types/02_combined_cycle_gt.md).

## Frame GT Vs Aeroderivative GT

Frame and aeroderivative describe turbine technology, not only plant layout.

| Topic | Frame GT | Aeroderivative GT |
| :--- | :--- | :--- |
| Typical size | Larger industrial unit. | Smaller modular unit, though still utility-scale in many cases. |
| Start behavior | Often slower and more thermally constrained. | Often faster-starting and more flexible. |
| Common use | Large CCGT blocks or large simple-cycle plants. | Peaking, fast response, reserves, flexible operation. |
| Maintenance | Large outage scope, OEM-specific intervals. | Can involve module swap or different maintenance model. |
| Modeling impact | Start time, EOH, ramp rate, heat-rate curve, and inspection assumptions differ. | Start/ramp constraints and maintenance cost structure differ. |

Important:

```text
A simple-cycle plant can use a frame GT or an aeroderivative GT.
A combined-cycle plant usually uses frame GTs, but plant designs vary.
```

## CHP And Cogeneration

CHP means combined heat and power. Cogeneration means the plant produces electricity and useful heat or steam.

```text
fuel -> GT / heat system -> electricity
                       |
                       v
                 useful steam / heat
```

Key modeling points:

| Topic | CHP treatment |
| :--- | :--- |
| Dispatch objective | Not only power margin; steam or heat obligation can dominate. |
| Revenue | May include electricity revenue and steam/heat revenue. |
| Constraints | Must meet host steam pressure, temperature, flow, or reliability terms. |
| Outage impact | Lost steam/heat service can matter as much as lost power revenue. |
| Heat rate | Electric-only heat rate may not tell the full economic story. |

Beginner takeaway:

```text
CHP dispatch can be heat-led, power-led, or contract-led.
Do not model it like a merchant power-only CCGT without checking steam obligations.
```

## Optional Future: Gas Reciprocating Engines

Gas reciprocating engines are gas-fired power plants, but they are not gas turbines.

```text
natural gas -> piston engine -> generator -> electricity
```

If the learning system later includes reciprocating engines, many GT-specific guides will need applicability warnings.

| Topic | Why recips differ |
| :--- | :--- |
| Degradation | Cylinders, pistons, lube oil, spark plugs, and engine overhauls replace GT hot-section logic. |
| Heat rate | Different part-load and start behavior. |
| Maintenance | Different service intervals and cost buckets. |
| Rotor/TBC/HGP | GT-specific concepts do not directly apply. |

Recommendation:

```text
Keep reciprocating engines optional until the project decides whether
"gas plant" means gas turbines only or all gas-fired generation assets.
```

## Athens Is A Worked Example, Not The Rule

The current InfraSure learning docs use an Athens-type GE 7FA 2x1 CCGT example.

That example is useful because it gives numbers:

| Athens example item | Why it helps |
| :--- | :--- |
| 2x1 CCGT layout | Makes GT, HRSG, and ST interactions concrete. |
| GE 7FA framing | Gives a realistic large-frame CCGT anchor. |
| Capacity table | Shows temperature derate with numbers. |
| Heat-rate baseline | Lets fuel-cost examples be calculated. |
| EOH and inspection thresholds | Shows how contract maintenance timing works. |
| Start cost table | Shows GT and HRSG/ST cost buckets. |
| Degradation starting states | Shows why the model needs memory. |

But Athens values are not universal:

```text
Athens values = worked example assumptions
not universal gas-plant constants
```

## Plant-Type Variations By Topic

| Topic | Simple-cycle GT | Combined-cycle GT | CHP / cogeneration |
| :--- | :--- | :--- | :--- |
| Capacity | GT Pmax/Pmin only. | GT plus steam-cycle and cooling effects. | Capacity may be constrained by steam host. |
| Heat rate | GT-only fuel intensity. | Combined GT+ST efficiency. | Electric heat rate may need steam-credit treatment. |
| Starts | GT start sequence. | GT plus HRSG/ST warm-up. | Start may also depend on heat/steam service needs. |
| VOM | GT/BOP variable cost. | GT, HRSG, ST, cooling, and BOP cost. | Power plus heat-service cost allocation. |
| Outages | GT/generator/BOP outage focus. | GT/HRSG/ST/BOP outage focus. | Power and steam-service availability both matter. |
| State vector | GT condition and dispatch state. | GT, HRSG, ST, cooling, and contract state. | Adds steam/heat obligation state. |
| Degradation | GT degradation factors. | GT plus HRSG/ST cycling. | Depends on steam/heat equipment and contract. |

## Degradation Applicability Matrix

| Degradation factor | Simple-cycle GT | CCGT | CHP / cogeneration | Notes |
| :--- | :---: | :---: | :---: | :--- |
| EOH accumulation with creep-fatigue coupling | Yes | Yes | Yes | GT-specific concept; values are contract/OEM-specific. |
| Capacity derating from ambient temperature | Yes | Yes | Yes | Curves differ by equipment, cooling, and configuration. |
| Heat rate degradation | Yes | Yes | Yes | CCGT includes steam-cycle effects; CHP may need heat credit. |
| Combustion cycling fatigue | Yes | Yes | Yes | GT combustor topic. |
| HRSG cycling damage | No | Yes | Maybe | Applies when HRSG or steam generator exists. |
| Compressor degradation | Yes | Yes | Yes | GT compressor topic. |
| Thermal barrier coating life | Yes | Yes | Yes | Applies to relevant GT hot-section designs. |
| Rotor life consumption | Yes | Yes | Yes | GT rotor topic; ST and generator rotors are separate. |

## Example: Start-Type Thresholds Are Not Universal

The current docs use this Athens-style start classification:

| Start type | Athens-style threshold |
| :--- | :--- |
| Hot | Less than 8 hours shutdown |
| Warm | 8 to 72 hours shutdown |
| Cold | More than 72 hours shutdown |

This is a good teaching example, but not a universal rule.

```text
Shutdown duration

0 hr             8 hr                         72 hr
 |---------------|-----------------------------|
      hot start            warm start              cold start

Athens-style example only.
```

Why it can change:

| Driver | Why it changes thresholds |
| :--- | :--- |
| OEM definition | Service contract may define categories differently. |
| Turbine model | Thermal mass and cooling behavior differ. |
| Frame vs aero | Aeroderivative units may have different start behavior. |
| CCGT vs simple-cycle | HRSG/ST warm-up can matter in CCGT economics. |
| CHP obligations | Steam-host requirements can change start economics. |
| Operator procedure | Purge, warm-up, ramp, and synchronization practices differ. |

Standard note for future guides:

```text
> Plant-Type Note
> Hot/warm/cold thresholds are not universal. The Athens thresholds are
> worked-example assumptions. Use OEM, LTSA/CSA, and operating data for
> plant-specific modeling.
```

## Pmin And Pmax Need Their Own Attention

The external gas plant model notes highlight an important improvement:

```text
Capacity is not only maximum MW.
Dispatch and offer curves also need minimum stable MW.
```

| Term | Meaning |
| :--- | :--- |
| Pmax | Maximum feasible output under current conditions. |
| Pmin | Minimum stable output when online. |
| Pmax(T) | Maximum output as a function of temperature. |
| Pmin(T) | Minimum stable output as a function of temperature. |

Why this matters:

| Modeling layer | Why Pmin/Pmax matter |
| :--- | :--- |
| Dispatch | Determines feasible MW range after the plant starts. |
| Offer curves | Defines valid MW block boundaries. |
| Weather adjustment | Hot days can lower Pmax and sometimes raise Pmin. |
| Plant type | Simple-cycle, CCGT, aero, frame, and CHP ranges differ. |

Important distinction:

```text
Historical Pmin/Pmax ranges are calibration evidence.
They are not forecasts unless future weather or future operating inputs are used.
```

This topic should eventually get a dedicated market/operations guide.

## Standard Plant-Type Note

Use this block in future guide edits where a value is plant-type dependent:

```text
> Plant-Type Note
> This guide explains the general concept first. Numeric values and equipment
> buckets may change for simple-cycle GTs, combined-cycle GTs, frame units,
> aeroderivative units, CHP plants, and specific LTSA/CSA terms.
> Athens values are worked-example assumptions, not universal constants.
```

## How To Read The Current Learning Docs

Until the migration is complete:

| Current doc type | How to read it |
| :--- | :--- |
| Basics guides | Mostly universal concepts, but examples often use Athens CCGT values. |
| CCGT anatomy guide | Specifically about combined-cycle plants, not all gas plants. |
| Degradation guides | Mostly GT-focused, except HRSG cycling which is steam-side and CCGT/CHP-specific. |
| Start cost guide | Universal idea, but HRSG/ST buckets only apply where steam-side equipment exists. |
| Outage guide | Universal idea, but outage categories and coverage differ by plant type and contract. |

## Recommended Next Reads

For the current Athens CCGT learning path:

1. Read this guide.
2. Read [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).
3. Continue through capacity, heat rate, EOH, starts, dispatch, outages, and state feedback.

For future non-CCGT modeling:

```text
start with this type map
  |
  v
choose plant type
  |
  v
read the universal concept guide
  |
  v
apply the plant-type variation table
  |
  v
use a worked example only if it matches the plant type
```

## Open Questions Before The Full Migration

| Question | Why it matters |
| :--- | :--- |
| Does "gas plant" mean gas turbines only, or all gas-fired generation? | Determines whether reciprocating engines belong in scope. |
| Which plant type comes after Athens CCGT? | Helps choose next worked example. |
| Should market/offer-curve guides live in this learning tree? | External plant-model docs show this is useful, but it is a separate layer. |
| How much plant-type specificity belongs in each guide? | Prevents duplicating every topic across every plant type. |
| Which values should remain Athens-only? | Prevents accidental universal assumptions. |

## Quick Recap

The learning docs should teach general gas-plant modeling without hiding that the current worked example is a CCGT.

```text
Universal concepts first.
Plant-type variations second.
Athens CCGT example third.
```

That structure keeps the docs useful now and expandable later.
