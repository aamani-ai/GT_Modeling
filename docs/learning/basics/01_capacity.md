# Capacity

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Read this if combined-cycle acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

> Plant-Type Note
> Capacity is a universal gas-plant concept, but the numeric capacity curve is plant-specific. The Athens values in this guide are worked-example assumptions for a 2x1 GE 7FA combined-cycle plant. Simple-cycle GTs, aeroderivative units, frame units, CHP plants, inlet cooling systems, and different site conditions can have different Pmax, Pmin, ambient derate, and auxiliary-load behavior.

## Why This Matters

Capacity answers a simple question:

> How many MW can the plant actually produce right now?

For the InfraSure model, capacity is not just the nameplate number printed on a plant summary. It changes with weather, plant condition, and configuration. A hot summer day can reduce available MW even if the plant is mechanically healthy. Long-term equipment condition can also reduce available MW if compressor erosion or other degradation lowers airflow.

Capacity matters because dispatch revenue is based on MWh sold:

```text
MWh = MW output * hours operated
```

If the plant can produce 531 MW at ISO conditions but only 469 MW during a hot period, the dispatch model has fewer MWh available to sell during that period. That can be financially important because hot days can also be high-price days.

## Plain-English Concept

Think of capacity as the plant's "maximum safe output under current conditions."

There are three beginner-level ideas to separate:

| Term | Plain meaning | Why it matters |
| :--- | :--- | :--- |
| Nameplate capacity | The broad plant size people quote in conversation. | Useful for quick context, but too coarse for dispatch modeling. |
| ISO capacity | Output at standard reference conditions, usually around 59 deg F. | Gives a clean baseline for comparing performance. |
| Effective capacity | Output available under the actual day's conditions and plant state. | This is what matters for hourly dispatch and revenue. |

In the Athens-type pilot, the reference net plant capacity is 531 MW at ISO conditions. But on a 95 deg F day, the framework table gives 469 MW.

That does not mean the plant broke. It means the same turbine produces less output when inlet air is hotter and less dense.

## ISO Capacity Vs Effective Capacity

ISO capacity is a reference point. It asks:

```text
What could the plant produce under standard test-like conditions?
```

Effective capacity asks:

```text
What can the plant produce under today's actual conditions?
```

The model needs effective capacity because Step 2 dispatch is an economic decision using the plant that exists today, not the plant that exists in a brochure.

```text
ISO capacity
    |
    | apply ambient temperature correction
    | apply site and plant-condition adjustments
    v
Effective capacity
```

### Important Distinction

Ambient derating is usually temporary. If the air is hot at 3pm and cooler at 2am, the available MW can recover as the weather changes.

Long-term degradation is different. If compressor erosion permanently reduces mass flow, the capacity loss does not disappear just because tomorrow is cooler. That is why this basics guide separates temporary ambient derating from long-term degradation.

## Pmax And Pmin

The current framework examples focus mostly on maximum output. For broader gas-plant modeling, capacity also needs a minimum stable output.

| Term | Plain meaning | Why it matters |
| :--- | :--- | :--- |
| `Pmax` | Maximum feasible MW under current conditions. | Caps revenue opportunity and dispatch output. |
| `Pmin` | Minimum stable MW when the unit is online. | Sets the lower bound after commitment; affects offer blocks and minimum-run economics. |
| `Pmax(T)` | Maximum MW as a function of temperature. | Hot weather can reduce maximum available MW. |
| `Pmin(T)` | Minimum stable MW as a function of temperature. | Some units may need a higher minimum load under difficult conditions. |

Beginner picture:

```text
Offline
  |
  v
If committed online:
  plant usually must operate between Pmin and Pmax

      feasible online range
      |-------------------|
      Pmin              Pmax
```

Why this matters:

```text
Pmax tells the model the most MW it can sell.
Pmin tells the model the smallest online block it must carry.
```

The Athens CCGT capacity table in this guide is a `Pmax` style example. It does not fully define `Pmin`, ramp rates, minimum run time, or offer-curve blocks.

Historical operating data can help estimate normal `Pmin` and `Pmax` ranges. But historical ranges are calibration evidence, not a forecast by themselves. A true forward-looking model needs future weather, plant state, and market assumptions.

## Why Temperature Changes Gas Turbine Output

A gas turbine is an air-breathing machine. It pulls in air, compresses it, adds fuel, burns the mixture, and expands the hot gas through the turbine.

Hotter air is less dense. Less dense air means less mass of air enters the compressor for the same inlet volume. With less air mass available, the turbine generally cannot burn as much fuel and produce as much power without violating operating limits.

Beginner version:

```text
Cold dense air  -> more air mass -> more possible MW
Hot thin air    -> less air mass -> less possible MW
```

This is why the framework treats hourly temperature as a capacity input. The climate simulation does not just affect market conditions; it changes what the plant can physically deliver.

## Plant-Type Variations

The physical idea is broad: gas turbines are air-breathing machines, so ambient conditions and plant condition affect output. The details differ by plant type.

| Plant type | What stays the same | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Effective capacity caps dispatch. | No HRSG/ST contribution; `Pmax` is GT/generator/BOP limited. |
| Combined-cycle GT | GT output still depends on ambient conditions. | Net plant capacity also includes HRSG, ST, cooling system, and auxiliary-load effects. |
| Frame GT | Ambient derate and compressor condition matter. | Larger thermal mass and OEM curves can differ from aero units. |
| Aeroderivative GT | Ambient derate and `Pmax/Pmin` still matter. | Start/ramp flexibility and performance curves can differ materially. |
| CHP / cogeneration | Feasible MW range still matters. | Steam or heat obligations may constrain electric output. |

Plant-type warning:

```text
Do not copy a CCGT capacity curve into a simple-cycle or CHP model.
Use the plant's actual equipment, site conditions, operating data,
and OEM/contract assumptions.
```

## Plant Context: Athens Worked Example

The framework uses an Athens-type 2x1 combined-cycle plant as its first worked example:

| Item | Value |
| :--- | :--- |
| Configuration | 2 GT + 1 ST + 2 HRSG |
| GT model | GE 7FA.03 x 2 |
| ISO net plant capacity | 531 MW |
| Location context | NYISO Zone F / Hudson Valley |
| Cooling | Mechanical draft cooling towers |

The pilot `Pmax` style capacity curve in the framework is:

| Ambient temperature | GT output, each | ST output | Net plant capacity | Framework delta label |
| :--- | ---: | ---: | ---: | :--- |
| 0 deg F | 185 MW | 195 MW | 565 MW | +4.6% |
| 20 deg F | 180 MW | 192 MW | 552 MW | +2.2% |
| 59 deg F ISO | 171 MW | 189 MW | 531 MW | baseline |
| 80 deg F | 159 MW | 181 MW | 499 MW | -7.6% |
| 95 deg F | 148 MW | 173 MW | 469 MW | -13.1% |

For learning and modeling, the MW values are the key numbers. The percentage labels in the high-level framework should be verified before being used in a final investment deck, because simple net-plant arithmetic from the MW values gives slightly different percentages. That does not change the main point: capacity materially declines as ambient temperature rises.

## ASCII Plot: Capacity Vs Temperature

```text
Net plant capacity

565 MW |* 0 deg F
552 MW |   * 20 deg F
531 MW |        * 59 deg F ISO
499 MW |              * 80 deg F
469 MW |                    * 95 deg F
       +---------------------------------
        cold       ISO      warm     hot
```

The curve is not just a financial curve. It is a physical operating curve. The dispatch model needs it because it cannot sell MW that the plant cannot produce.

## Daily Model Inputs And Outputs

Capacity is connected to the daily model loop, but the temperature inputs are hourly.

### Inputs

| Input | Frequency | Source | What it does |
| :--- | :--- | :--- | :--- |
| Ambient temperature | Hourly | Climate simulation | Drives hourly capacity derating. |
| Humidity and altitude | Site-fixed or assumed | Asset specs | Can adjust the correction curve if modeled. |
| Inlet cooling status | Asset specs / operating assumption | Plant configuration | Can offset some hot-weather derate if available. |
| Current compressor condition | Daily state | Engineering model | Erosion or severe fouling can reduce mass flow. |
| Current outage status | Daily state | Maintenance/failure module | If unavailable, effective capacity is zero for dispatch. |

### Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Hourly effective capacity | Dispatch model | Maximum MW available in each hour. |
| Daily capacity summary | Engineering / financial layer | Helps calculate revenue opportunity and losses. |
| Degraded capacity state | Next day's dispatch | Carries non-weather plant condition forward. |

The exact implementation can separate these into two pieces:

```text
Weather part:
hourly temperature -> hourly ambient derate

Plant-condition part:
compressor erosion / persistent degradation -> capacity state

Combined:
hourly ambient derate * degraded capacity state -> hourly effective capacity
```

## How Capacity Feeds Step 2 Dispatch

Step 2 is the dispatch model. It decides whether to commit the plant and how much to generate based on economics and constraints.

Capacity affects Step 2 in three ways:

| Dispatch question | How capacity matters |
| :--- | :--- |
| Can the plant meet the target MW? | Effective capacity is the upper bound. |
| How much revenue is available? | Lower MW means fewer MWh can be sold during high-price hours. |
| Is the run still worth it? | Lower output can make start costs and fixed operating costs harder to recover. |

Simple flow:

```text
Hourly price + gas price + start cost
        |
        v
Dispatch model checks economics
        |
        v
Effective capacity caps MW output
        |
        v
Revenue and operating profile are calculated
```

If the plant is economically "in the money" but hot weather reduces maximum output, the plant may still run, but it earns less than it would under ISO conditions.

## Worked Example: Hot Day Capacity Loss

Assume a high-price summer afternoon:

| Item | Value |
| :--- | ---: |
| ISO net capacity | 531 MW |
| Capacity at 95 deg F | 469 MW |
| Capacity difference | 62 MW |
| High-price duration | 6 hours |
| Power price | $85/MWh |

Potential gross revenue difference:

```text
Lost MWh = 62 MW * 6 hours
Lost MWh = 372 MWh

Lost gross revenue = 372 MWh * $85/MWh
Lost gross revenue = $31,620
```

This is not saying the plant loses exactly $31,620 of EBITDA. Fuel burn, heat rate, variable O&M, start costs, and commitment constraints still matter. The example only isolates the capacity effect:

```text
Hot weather -> lower MW cap -> fewer MWh available -> lower gross revenue opportunity
```

## Capacity, Energy, And Capacity Factor

These terms are easy to mix up.

| Concept | Unit | Plain-English meaning |
| :--- | :--- | :--- |
| Capacity | MW | How much power the plant can produce at a moment. |
| Energy | MWh | How much electricity the plant produces over time. |
| Capacity factor | % | Actual MWh divided by maximum possible MWh over a period. |

Example:

```text
Plant runs at 469 MW for 6 hours

Energy = 469 MW * 6 hours
Energy = 2,814 MWh
```

Capacity is the instantaneous limit. Energy is the accumulated production.

## Temporary Derate Vs Long-Term Degradation

This is one of the most important beginner distinctions.

| Type | Example | Does it reset when weather changes? | Model treatment |
| :--- | :--- | :--- | :--- |
| Temporary ambient derate | Hot air lowers output at 95 deg F. | Yes. Cooler air can restore output. | Driven by hourly climate input. |
| Persistent degradation | Compressor erosion lowers airflow. | No. It stays until overhaul or repair. | Carried in the state vector. |
| Outage derate | Forced outage makes the unit unavailable. | Only after repair or outage ends. | Handled by maintenance/failure module. |

This guide is mostly about capacity as a basic concept. Later degradation guides will explain the persistent mechanisms in more detail, especially compressor degradation.

## What The Framework Includes

The high-level framework includes these capacity ideas:

- Hourly temperature from the climate simulation drives capacity derating.
- Capacity derating is a high-priority stress/performance factor.
- The Athens-type plant has a capacity curve from 0 deg F to 95 deg F.
- The model feeds effective capacity back to the dispatch model for the next day.
- Effective capacity is degraded by ambient conditions and compressor erosion.
- Ambient derating is part of the climate-dispatch-engineering feedback loop.

The framework also labels the ambient temperature derating coefficient as a Green-certainty assumption in Appendix B.5, using OEM correction curves and ISO 2314 performance methodology as the basis.

## What The Framework Leaves Out

The high-level framework intentionally does not include every detail needed for an OEM-grade capacity model.

| Missing detail | Why it matters |
| :--- | :--- |
| Exact OEM correction curves | The framework summarizes the curve but does not provide full curve data. |
| Humidity correction method | Humidity can affect performance but is not detailed in the basics table. |
| Inlet cooling behavior | Inlet chilling or evaporative cooling could change hot-day output if present. |
| Altitude and site pressure details | Air density depends on pressure as well as temperature. |
| Auxiliary load details | Net plant capacity depends on plant auxiliary consumption. |
| Degradation split | Compressor fouling, erosion, and other losses are not fully separated in the capacity guide. |
| Delta-column convention | The framework's MW values and percentage labels should be reconciled before final external use. |

For investment due diligence, this level is usually acceptable if the goal is to understand risk and dispatch economics. For final engineering validation, plant-specific correction curves and performance test data would be better.

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.2 | Capacity derating as a high-priority stress/performance factor. | Green for concept, Amber for exact plant calibration. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.3 | Hourly temperature input and effective capacity feedback to dispatch. | Green for model architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.2 | Athens-type capacity table by ambient temperature. | Amber until reconciled with actual plant/OEM data. |
| `docs/InfraSure_ModelingFramework_V2.md`, Appendix B.5 | Ambient derating coefficient and bounds. | Green for broad methodology, Amber for bounds. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Five-step pipeline and daily feedback framing. | Green for framework communication. |
| ISO 2314:2009 | General gas turbine acceptance-test context, including applicability to gas turbines in combined-cycle plants. | Green for standards context. |

## Open Questions Before Investment Use

Before using capacity outputs in a final investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| Do we have the actual OEM correction curve for this plant and configuration? | Replaces generic curve assumptions with asset-specific data. |
| Does the plant have inlet cooling, and how is it dispatched? | Can materially reduce hot-day derates. |
| Are the framework table's percentage deltas measured against net plant MW, GT-only MW, or another convention? | Avoids confusion in investment materials. |
| What auxiliary loads are included in "net plant" output? | Net output is what matters for revenue. |
| What is the plant's actual `Pmin`, and does it change with season or temperature? | Minimum stable output affects dispatch, offer blocks, and short-run economics. |
| Is compressor erosion already embedded in the baseline 531 MW, or applied separately as degradation? | Prevents double-counting degradation. |
| Which plant type is being modeled: simple-cycle, CCGT, aero, frame, CHP, or something else? | Prevents applying Athens CCGT assumptions to the wrong asset. |
| Are capacity market obligations modeled separately from energy dispatch? | Capacity shortfall risk may have a different financial treatment than energy revenue. |

## Quick Recap

Capacity is the plant's available MW limit. ISO capacity is the clean reference point. Effective capacity is what the plant can actually deliver under current weather and plant condition.

For this model:

```text
Hourly temperature changes capacity.
Effective capacity caps dispatch.
Lower capacity reduces MWh opportunity.
Persistent degradation can lower tomorrow's capacity state.
```

That is why capacity appears early in the learning path. It is the simplest place to see how climate inputs become financial impact through Step 2 dispatch.
