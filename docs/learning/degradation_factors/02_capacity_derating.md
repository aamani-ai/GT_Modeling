# Capacity Derating From Ambient Temperature

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read this basics guide first if capacity is new: [Capacity](../basics/01_capacity.md).

> Plant-Type Applicability
> Ambient capacity derating is broadly relevant to GT-based plants, but the curve is plant-specific. Simple-cycle GTs, CCGTs, frame units, aeroderivatives, inlet cooling systems, evaporative coolers, chillers, cooling towers, auxiliary loads, and CHP steam constraints can all change effective Pmax and sometimes Pmin.

## Why This Matters

Capacity derating answers a practical dispatch question:

> How many MW can the plant actually sell in this hour, given today's weather and plant condition?

A gas turbine is an air-breathing machine. When the air is hot, it is less dense. Less dense inlet air means less air mass enters the compressor. Less air mass usually means less fuel can be burned within operating limits, so the gas turbine produces fewer MW.

For the InfraSure model, this matters because many valuable dispatch hours can happen during hot weather. If power prices are high during a heat wave, the plant may be economically attractive but physically unable to produce its ISO capacity.

```text
hotter ambient air
        |
        v
lower inlet air density
        |
        v
lower GT mass flow and output
        |
        v
lower plant effective capacity
        |
        v
fewer MWh available to sell in Step 2 dispatch
```

The key financial point is simple:

```text
Lost MWh = unavailable MW * high-price hours
```

Even when the plant still runs, lower available MW can reduce revenue, reduce capacity factor, and create capacity-market or resource-adequacy concerns if the plant's deliverable summer capacity is below the quoted nameplate number.

## Plain-English Concept

Capacity is not one fixed number.

| Term | Beginner meaning | Example |
| :--- | :--- | :--- |
| ISO capacity | Output under standard reference conditions. | Athens-type plant: 531 MW at 59 deg F ISO. |
| Ambient derate | Temporary output reduction caused by current weather. | 95 deg F output is lower than 59 deg F output. |
| Effective capacity | MW available for dispatch after weather, degradation, and outages. | The MW cap Step 2 dispatch should use. |
| Persistent capacity degradation | Long-term loss from plant condition, such as compressor erosion. | Does not reset just because tomorrow is cooler. |

Beginner shortcut:

```text
ISO capacity       = clean reference point
ambient derate     = today's weather adjustment
plant degradation  = condition adjustment carried in the state vector
effective capacity = what dispatch can actually use
```

## Plant-Type Applicability

Capacity derating should be modeled from the equipment actually present.

| Plant type | What still applies | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Hot air reduces GT output. | No steam-cycle recovery; GT Pmax is the main capacity curve. |
| Combined-cycle GT | GT derate affects total plant output. | Lower GT exhaust energy also changes HRSG/ST output and 1x1 vs 2x1 economics. |
| Aeroderivative GT | Inlet-air conditions still matter. | Manufacturer curves, inlet systems, and fast-start operating modes can differ. |
| CHP / cogeneration | Ambient effects still affect GT output. | Steam demand or heat recovery needs can constrain electric output. |
| Gas reciprocating engine | Temperature may affect output. | This guide's GT air-breathing curve should not be reused without an engine-specific model. |

## Why This Is In The Degradation-Factor Folder

Ambient temperature derating is not permanent degradation by itself. If a hot afternoon turns into a cool evening, the temporary ambient derate can improve quickly.

So why is it listed with degradation factors?

Because the framework's engineering model needs to return a realistic effective capacity to dispatch. Step 2 does not care whether lower capacity came from hot air, compressor erosion, or an outage. It cares how many MW can be committed and sold.

| Capacity loss type | Temporary or persistent? | State treatment |
| :--- | :--- | :--- |
| Hot ambient air | Temporary | Recomputed from hourly climate inputs. |
| High humidity / site altitude | Mostly site/weather condition | Included in correction curve if modeled. |
| Inlet cooling availability | Operating configuration | Offsets some hot-weather loss if available. |
| Compressor fouling | Partly recoverable | Carried in plant condition; may reset after wash. |
| Compressor erosion | Persistent | Carried until major repair or overhaul. |
| Forced outage | Temporary but event-driven | Capacity is zero while unavailable. |

This guide is about the ambient-temperature part. Later guides cover persistent compressor degradation.

## Physical Mechanism

A GT compressor moves volume, but power output depends heavily on mass flow.

Hot air is less dense than cold air:

```text
cold dense air -> more air mass entering compressor -> more possible MW
hot thin air   -> less air mass entering compressor -> fewer possible MW
```

This effect is especially important for simple-cycle and combined-cycle gas turbines because the gas turbine is the upstream engine. In a combined-cycle plant, lower GT output can also change the heat available to the HRSG and steam turbine.

The simplified chain is:

```text
ambient temperature
        |
        v
GT compressor inlet condition
        |
        v
GT output
        |
        v
HRSG steam production
        |
        v
ST output
        |
        v
net plant capacity
```

The exact curve is OEM- and site-specific. The framework uses an Athens-type GE 7FA curve and a simplified coefficient as prototype assumptions.

## Plant Context: Athens-Type GE 7FA

The framework's capacity table is:

| Ambient temperature | GT output, each | ST output | Net plant capacity | Framework delta label |
| :--- | ---: | ---: | ---: | :--- |
| 0 deg F | 185 MW | 195 MW | 565 MW | +4.6% |
| 20 deg F | 180 MW | 192 MW | 552 MW | +2.2% |
| 59 deg F ISO | 171 MW | 189 MW | 531 MW | baseline |
| 80 deg F | 159 MW | 181 MW | 499 MW | -7.6% |
| 95 deg F | 148 MW | 173 MW | 469 MW | -13.1% |

For learning, focus first on the MW values:

```text
531 MW at 59 deg F ISO
469 MW at 95 deg F
62 MW lower on the hot case
```

That is a large enough difference to matter in dispatch and valuation.

### Calibration Note

The high-level framework also lists a simplified derating coefficient:

```text
ambient derating coefficient = -0.5% per deg F above 59 deg F ISO
```

That coefficient is useful as a transparent modeling approximation, but it should not be blindly mixed with the table above. A single straight-line coefficient, an OEM correction curve, and the table values may not produce exactly the same answer.

For investment use, reconcile these three items:

| Item | Why reconcile it? |
| :--- | :--- |
| Athens MW table | Gives the plant example used in the docs. |
| -0.5% per deg F coefficient | Gives a simple formula for simulation. |
| OEM correction curve / test basis | Gives the defensible plant-specific source. |

The basics capacity guide already flags that the framework's percentage delta labels should be verified. This degradation guide keeps that warning because derating is financially meaningful.

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

The direction is the main lesson: hotter weather reduces available MW.

## Model Inputs

Capacity derating uses climate, asset, and plant-state inputs.

| Input | Frequency | Source | What it controls |
| :--- | :--- | :--- | :--- |
| Ambient temperature | Hourly | Climate simulation | Main driver of hourly capacity derate. |
| Humidity | Hourly or site assumption | Climate / asset specs | Can affect correction curve if modeled. |
| Altitude / site elevation | Site-fixed | Asset specs | Changes air density baseline. |
| Inlet cooling system | Asset config / dispatch assumption | Asset specs | Can reduce hot-weather derate if available and operating. |
| ISO net capacity | Static plant parameter | Asset specs | Reference capacity before corrections. |
| Current persistent capacity degradation | Daily state | Engineering model | Compressor erosion/fouling capacity penalty. |
| Outage status | Daily state | Maintenance/failure module | If unavailable, effective capacity is zero. |
| Plant configuration | Hourly or dispatch mode | Dispatch model | 2x1 or 1x1 operation changes available MW blocks. |

## Model Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Hourly effective capacity | Step 2 dispatch | Maximum MW the plant can commit each hour. |
| Daily lost-MWh summary | Financial layer | Estimate of revenue opportunity lost to hot-weather derate. |
| Capacity factor impact | Investor metrics | Derating can reduce realized MWh even when the plant is available. |
| Capacity shortfall flag | Risk layer | Identifies periods where deliverable capacity is materially below reference capacity. |
| Next-day plant capacity baseline | Dispatch feedback | Persistent condition is carried forward; ambient portion is recomputed from weather. |

## The Daily Loop Nuance

This is where the "daily" model can be confusing.

The dispatch decision is hourly, but the engineering state update is daily. Ambient capacity derating sits across both levels:

```text
Hourly level:
hourly temperature -> hourly effective capacity -> hourly dispatch cap

Daily checkpoint:
hourly derates + dispatch results -> daily summary -> updated state for tomorrow
```

Important implementation distinction:

| Item | Should it be hourly? | Should it be carried as a daily state? |
| :--- | :---: | :---: |
| Ambient temperature derate | Yes | No, except as daily summary metrics. |
| Compressor erosion capacity loss | Can affect every hour | Yes. |
| Forced outage availability | Usually day/event state | Yes, until outage ends. |
| ISO nameplate capacity | Static | Yes, as asset parameter. |

So when the framework says effective capacity feeds back daily, read it carefully:

```text
Persistent plant-condition capacity is carried forward daily.
Hourly ambient derating should be recomputed from the next day's hourly weather.
```

This keeps the model from accidentally treating yesterday's hot-weather derate as permanent degradation.

## How Capacity Derating Feeds Step 2 Dispatch

Step 2 dispatch asks whether the plant should run and how much it can generate.

Capacity derating affects that decision in four ways:

| Dispatch effect | Explanation |
| :--- | :--- |
| MW cap | Effective capacity is the upper bound on generation. |
| Revenue opportunity | Lower MW means fewer MWh sold in high-price hours. |
| Start cost recovery | Same start cost spread over fewer MWh can make marginal starts less attractive. |
| 1x1 vs 2x1 operation | Derating can change whether partial operation is more attractive than full 2x1 operation. |

Flow:

```text
hourly power price + gas price + heat rate + VOM + start cost
        |
        v
dispatch margin check
        |
        v
hourly effective capacity cap
        |
        v
MWh sold and operating profile
```

If the plant is in the money but derated, it usually still runs, but earns less than it would at ISO capacity.

## Worked Example 1: Hot Afternoon Gross Revenue

Assume:

| Item | Value |
| :--- | ---: |
| ISO net capacity | 531 MW |
| Capacity at 95 deg F | 469 MW |
| Capacity difference | 62 MW |
| High-price duration | 6 hours |
| Power price | $85/MWh |

Gross revenue opportunity lost:

```text
Lost MWh = 62 MW * 6 hours
Lost MWh = 372 MWh

Lost gross revenue = 372 MWh * $85/MWh
Lost gross revenue = $31,620
```

This is not full EBITDA impact. It ignores fuel, VOM, start cost, and heat-rate changes. It only isolates the capacity effect.

## Worked Example 2: Energy Margin Impact

Now include a simple dispatch margin.

Assume:

| Item | Value |
| :--- | ---: |
| Power price | $85/MWh |
| Gas price | $4.00/MMBtu |
| Hot-day heat rate | 7.230 MMBtu/MWh |
| VOM | $2.50/MWh |
| Start cost allocation | ignored for simplicity |

Fuel cost:

```text
Fuel cost = 7.230 * 4.00
Fuel cost = $28.92/MWh
```

Energy margin:

```text
Energy margin = power price - fuel cost - VOM
Energy margin = 85.00 - 28.92 - 2.50
Energy margin = $53.58/MWh
```

Margin opportunity lost from derate:

```text
Lost margin = 372 MWh * $53.58/MWh
Lost margin = $19,931.76
```

This is closer to operating economics than the gross revenue example, but it still excludes start costs and commitment constraints.

## Worked Example 3: Why Start Cost Recovery Gets Harder

Assume the plant must incur a $40,000 start cost for a high-price run.

| Case | Available capacity | Run hours | MWh produced | Start cost per MWh |
| :--- | ---: | ---: | ---: | ---: |
| ISO case | 531 MW | 6 | 3,186 MWh | $12.55/MWh |
| Hot derated case | 469 MW | 6 | 2,814 MWh | $14.21/MWh |

Same start cost, fewer MWh:

```text
hot weather -> fewer MWh -> higher start cost per MWh
```

This is why capacity derating can change a dispatch decision even when spark spread is positive.

## Simple Formula View

A simple effective-capacity structure is:

```text
effective_capacity_hour =
  ISO_capacity
  * ambient_capacity_multiplier_hour
  * persistent_capacity_multiplier_day
  * availability_multiplier_day
```

Where:

| Multiplier | Example value | Meaning |
| :--- | ---: | :--- |
| `ambient_capacity_multiplier_hour` | 0.883 at 95 deg F using table values | Temporary hourly weather effect. |
| `persistent_capacity_multiplier_day` | 0.990 | Long-term compressor or plant-condition loss. |
| `availability_multiplier_day` | 1.0 or 0.0 | Available or unavailable. |

Using table values at 95 deg F:

```text
ambient multiplier = 469 / 531
ambient multiplier = 0.883
```

If persistent capacity degradation is 1.0%:

```text
effective capacity = 531 * 0.883 * 0.990
effective capacity = 464.3 MW
```

The table-driven result is easier to explain than a black-box correction curve, but the final model should still be calibrated to the plant's actual OEM curve.

## What The Framework Includes

The high-level framework includes:

| Included item | Why it matters |
| :--- | :--- |
| Hourly temperature input | Captures intra-day weather-driven capacity changes. |
| Climate simulation paths | Captures heat-wave persistence and future weather uncertainty. |
| Athens-type capacity table | Gives a concrete GE 7FA-style example. |
| Effective capacity feedback | Lets dispatch see a realistic MW cap. |
| Capacity-market shortfall risk | Recognizes that derate can matter outside energy revenue. |
| Derating coefficient assumption | Provides a simple simulation parameter. |
| Derating bounds | Prevents unrealistic extreme capacity values in simulation. |

## What The Framework Leaves Out

The high-level framework does not fully specify:

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| Exact OEM correction curve | Needed to defend plant-specific MW outputs. |
| Whether the table or coefficient is authoritative | Table values and straight-line coefficient should be reconciled. |
| Humidity correction | Humidity can affect gas turbine output and heat rate. |
| Inlet cooling operation | Inlet chilling or evaporative cooling can materially change summer output. |
| Degradation-vs-ambient separation in implementation | Prevents temporary weather derate from being carried as permanent degradation. |
| Capacity-market accreditation rules | Market capacity value may depend on seasonal tests and market rules. |
| Auxiliary load changes | Net capacity depends on internal plant loads, which can vary with cooling demand. |
| Validation against test data | Acceptance-test or seasonal performance data should confirm the curve. |

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| Direction of ambient derating | Local framework, gas turbine physics, OEM correction-curve concept. | Green. |
| Athens capacity table | Local framework Section 4.2. | Amber until percentages and plant-specific curve are verified. |
| -0.5% per deg F coefficient | Local framework Appendix B.5. | Green as a framework assumption; Amber for exact asset use without OEM curve. |
| Derating bounds [0.80, 1.05] x ISO | Local framework Appendix B.5. | Amber because it is an engineering constraint. |
| ISO acceptance-test context | ISO 2314:2009 gas turbine acceptance-test standard. | Green for context; not a substitute for buying/applying the full standard. |
| Hourly-to-daily treatment | Local framework Section 3.3 and digital-twin PDF. | Green for model architecture; implementation detail should be checked in code. |

External reference used for validation:

- ISO, "ISO 2314:2009 Gas turbines - Acceptance tests": https://www.iso.org/standard/42989.html

As of the ISO page checked for this guide, ISO 2314:2009 is published, was last reviewed and confirmed in 2018, and is expected to be replaced by ISO/DIS 2314 in the coming months. That means the framework's ISO 2314 basis is valid context, but a final diligence package should confirm the current standard version at the time of use.

## Open Questions Before Investment Use

Before using this factor in an investment model or investment committee deck, answer these:

| Question | Why it matters |
| :--- | :--- |
| Do we have the actual OEM capacity correction curve for this unit? | It is the best source for hourly capacity limits. |
| Should the model use the Athens table or the -0.5% per deg F coefficient? | Using both without reconciliation can create inconsistent MW outputs. |
| How are humidity and inlet pressure handled? | Temperature alone may be too simple for final performance modeling. |
| Does the plant have inlet cooling, and when is it dispatched? | It can materially reduce hot-weather derate. |
| Are net auxiliary loads modeled dynamically? | Cooling tower and balance-of-plant loads affect net output. |
| How does derated summer output affect capacity accreditation? | Energy revenue is not the only capacity-related financial exposure. |
| Is ambient derate recomputed hourly in Step 2? | It should not be carried forward as permanent daily degradation. |
| Do historical test data or summer operating records support the curve? | Back-testing improves confidence in revenue and capacity-factor estimates. |

## One-Sentence Takeaway

Ambient capacity derating is a temporary weather-driven MW limit, but Step 2 dispatch must treat it as real capacity because the plant cannot sell MWh it cannot physically produce.
