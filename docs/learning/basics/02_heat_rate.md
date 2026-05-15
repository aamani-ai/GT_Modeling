# Heat Rate

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Read this if combined-cycle acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

> Plant-Type Note
> Heat rate is a universal gas-plant concept, but the curve and interpretation are plant-specific. The Athens values in this guide are worked-example assumptions for a 2x1 GE 7FA combined-cycle plant. Simple-cycle GTs, aeroderivative units, frame units, CHP plants, duct firing, auxiliary loads, and steam or heat-credit treatment can all change the right heat-rate model.

## Why This Matters

Heat rate answers a simple question:

> How much fuel energy does the plant need to produce electricity?

For a gas-fired power plant, heat rate is one of the most important operating metrics because fuel is usually the largest variable cost. A lower heat rate means the plant converts fuel into electricity more efficiently. A higher heat rate means the plant needs more gas for the same MWh output.

In dispatch economics, heat rate directly turns gas price into fuel cost:

```text
Fuel cost per MWh = heat rate * gas price
```

That is why even a small heat-rate degradation can matter. If the plant produces a lot of MWh, a small extra fuel cost per MWh becomes a large annual cashflow impact.

## Plain-English Concept

Heat rate is fuel intensity.

| Term | Plain meaning | Better direction |
| :--- | :--- | :--- |
| Low heat rate | Less fuel needed per MWh. | Better |
| High heat rate | More fuel needed per MWh. | Worse |
| Heat-rate degradation | Heat rate gets higher over time. | Worse |

The common U.S. unit is:

```text
Btu/kWh
```

The InfraSure framework uses net heat rate on an HHV basis:

| Word | Meaning in this guide |
| :--- | :--- |
| Net | Measured after internal plant auxiliary loads, so it is closer to sellable output. |
| HHV | Higher heating value fuel convention. Keep this consistent when comparing numbers. |
| Btu/kWh | Fuel heat input per kWh of net electricity output. |

Beginner shortcut:

```text
Heat rate is like miles-per-gallon, but inverted.

Car MPG: higher is better.
Plant heat rate: lower is better.
```

## Heat Rate Vs Efficiency

Heat rate and efficiency are two ways to talk about the same basic idea.

Efficiency asks:

```text
What percent of fuel energy becomes electricity?
```

Heat rate asks:

```text
How much fuel energy is needed for each kWh?
```

The conversion uses 3,412 Btu per kWh of electric energy:

```text
Efficiency = 3,412 / heat rate
```

Example:

```text
Heat rate = 7,070 Btu/kWh
Efficiency = 3,412 / 7,070
Efficiency = 0.483
Efficiency = 48.3%
```

This is a simplified conversion. In real comparisons, always check whether the heat rate is HHV or LHV and whether it is gross or net.

## Average Vs Incremental Heat Rate

For first learning, heat rate usually means average heat rate:

```text
Average heat rate = total fuel input / total electric output
```

Dispatch and offer curves often need incremental heat rate:

```text
Incremental heat rate = extra fuel needed for the next extra MWh
```

The distinction:

| Type | Plain question | Common use |
| :--- | :--- | :--- |
| Average heat rate | How much fuel did the plant use per MWh overall? | Performance reporting, efficiency comparisons, simple fuel-cost examples. |
| Incremental heat rate | How much extra fuel is needed to produce one more MWh at this load? | Marginal cost, dispatch, offer curves, part-load pricing. |

Simple picture:

```text
Average HR:
  total fuel / total MWh

Incremental HR:
  slope of the fuel curve at the current MW
```

Why this matters:

```text
A plant can have a good average heat rate at full load
but a worse incremental heat rate at part load.
```

The InfraSure learning examples mostly use average net heat-rate values to teach fuel cost and degradation. A later market/operations guide can go deeper on fuel curves, incremental heat rate, and offer blocks.

## Plant-Type Variations

The idea is broad: heat rate measures fuel intensity. The right calculation depends on plant type and commercial use.

| Plant type | What stays the same | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Fuel cost still depends on heat rate. | Heat rate is GT-only and usually higher than CCGT. |
| Combined-cycle GT | Fuel intensity still drives dispatch cost. | Net heat rate includes GT plus steam-cycle output and auxiliary loads. |
| Frame GT | Heat-rate curve still depends on load and ambient conditions. | OEM curves and part-load behavior differ by model. |
| Aeroderivative GT | Heat-rate curve still drives marginal cost. | Faster flexible operation may come with different part-load and start behavior. |
| CHP / cogeneration | Fuel intensity still matters. | Electric-only heat rate may be misleading unless steam/heat output is credited correctly. |

Plant-type warning:

```text
Do not compare heat rates unless the basis is consistent:
HHV vs LHV, gross vs net, electric-only vs CHP credited,
simple-cycle vs combined-cycle, and actual plant configuration.
```

## Plant Context: Athens Worked Example

The framework gives these heat-rate values for the Athens-type CCGT worked example:

| Condition | Heat rate | Notes |
| :--- | ---: | :--- |
| Post-HGP baseline at ISO | 7,070 Btu/kWh | Reflects 22-year non-recoverable degradation. |
| At 90 deg F ambient | 7,230 Btu/kWh | Higher heat rate because hot weather worsens performance. |
| At 50% minimum load, ISO | 8,215 Btu/kWh | Part-load operation is less efficient. |

The key point is that heat rate is not one fixed number. It changes with:

- ambient temperature
- load level
- compressor condition
- hot gas path condition
- time since inspection or wash
- recoverable and non-recoverable degradation

## Converting Heat Rate To Fuel Cost

The easiest way to use heat rate in dispatch economics is to convert Btu/kWh into MMBtu/MWh.

The conversion is simple:

```text
1,000 Btu/kWh = 1.000 MMBtu/MWh
7,070 Btu/kWh = 7.070 MMBtu/MWh
```

Then multiply by gas price:

```text
Fuel cost per MWh = heat rate in MMBtu/MWh * gas price in $/MMBtu
```

Example at $4.00/MMBtu gas:

| Heat rate | MMBtu/MWh | Fuel cost |
| :--- | ---: | ---: |
| 7,070 Btu/kWh | 7.070 | $28.28/MWh |
| 7,230 Btu/kWh | 7.230 | $28.92/MWh |
| 8,215 Btu/kWh | 8.215 | $32.86/MWh |

So the 90 deg F heat rate is not just an engineering detail. At $4.00/MMBtu gas, it costs about $0.64/MWh more fuel than the ISO baseline.

## ASCII Plot: Lower Is Better

```text
Fuel needed per MWh

8,215 Btu/kWh |                    * 50% load
7,230 Btu/kWh |            * 90 deg F
7,070 Btu/kWh |        * ISO baseline
              +------------------------------
                    better          worse
                  lower HR       higher HR
```

Heat rate goes up when the plant is less efficient. In dispatch, that makes the plant more expensive to run.

## Heat Rate And Spark Spread

Spark spread is one of the most important market signals for a gas plant.

At the simplest level, spark spread is:

```text
Spark spread = electricity price - gas fuel cost
```

More formally:

```text
Spark spread ($/MWh) =
  power price ($/MWh)
  - [gas price ($/MMBtu) * heat rate (MMBtu/MWh)]
```

It is called a "spread" because it measures the difference between the output price and the input fuel cost. For a gas plant, the output is electricity and the fuel input is natural gas.

### What Spark Spread Signals

Spark spread is a quick signal of whether a gas plant has enough energy margin to run.

| Spark spread signal | Plain meaning | Dispatch implication |
| :--- | :--- | :--- |
| Positive and high | Power price is well above gas fuel cost. | Plant is more likely to run. |
| Positive but small | Fuel cost is covered, but other costs may not be. | Need to check VOM, start cost, and EOH wear. |
| Near zero | Power price barely covers fuel. | Usually not enough for a cycling plant start. |
| Negative | Fuel cost exceeds power revenue. | Plant usually should not run for energy-only value. |

Spark spread is not the same thing as EBITDA. It is a market margin before many other costs.

### Clean Spark Spread

A clean spark spread usually means the spread after fuel cost, before other plant-specific costs.

In this guide:

```text
Clean spark spread = power price - fuel cost
```

If power price is $55/MWh and gas is $4.00/MMBtu:

| Case | Heat rate | Fuel cost | Simple spark spread |
| :--- | ---: | ---: | ---: |
| ISO baseline | 7,070 Btu/kWh | $28.28/MWh | $26.72/MWh |
| 90 deg F ambient | 7,230 Btu/kWh | $28.92/MWh | $26.08/MWh |
| 50% load | 8,215 Btu/kWh | $32.86/MWh | $22.14/MWh |

The power price and gas price are the same in all three rows. Only the heat rate changes. As heat rate worsens, fuel cost rises and spark spread falls.

### Spark Spread Vs Dispatch Margin

Spark spread is useful, but it is not the final dispatch decision.

The model still needs to subtract:

- VOM
- start cost
- EOH/wear penalty near inspection thresholds
- emissions costs
- startup and shutdown effects
- minimum run and minimum down constraints
- outage status

So the model's dispatch margin is closer to:

```text
Dispatch margin =
  power price
  - fuel cost
  - VOM
  - allocated start cost
  - EOH/wear penalty
```

Beginner distinction:

| Metric | Includes | Does not include |
| :--- | :--- | :--- |
| Clean spark spread | Power price, gas price, heat rate. | VOM, starts, outages, LTSA costs, fixed costs. |
| Dispatch margin | Fuel, VOM, start allocation, wear penalty. | Some longer-term fixed costs and financing items. |
| EBITDA / cashflow | Operating revenue and broader cost stack. | Depends on full financial model structure. |

This is why the framework notes that LTSA inspection costs, fixed fees, and start overage charges show near-zero impact on spark spread. Spark spread is not meant to include those LTSA costs. Those costs show up later in financial outputs.

### Implied Heat Rate

Another useful market idea is implied heat rate.

Implied heat rate asks:

```text
At today's power price and gas price, what heat rate would break even on fuel?
```

Formula:

```text
Implied heat rate (MMBtu/MWh) =
  power price ($/MWh) / gas price ($/MMBtu)
```

Example:

```text
Power price = $55/MWh
Gas price = $4/MMBtu

Implied heat rate = 55 / 4
Implied heat rate = 13.75 MMBtu/MWh
Implied heat rate = 13,750 Btu/kWh
```

If the plant's actual heat rate is below the implied heat rate, it covers fuel cost.

```text
Plant heat rate = 7,070 Btu/kWh
Market implied heat rate = 13,750 Btu/kWh

7,070 < 13,750
Fuel cost is covered.
```

But fuel cost being covered does not automatically mean the plant should start. The start cost and VOM still need to clear.

### Spark Spread Examples

#### Example 1: Strong Spread

```text
Power price = $75/MWh
Gas price = $4/MMBtu
Heat rate = 7.070 MMBtu/MWh

Fuel cost = 7.070 * 4
Fuel cost = $28.28/MWh

Spark spread = 75 - 28.28
Spark spread = $46.72/MWh
```

This is likely attractive before considering start cost, VOM, and constraints.

#### Example 2: Weak Spread

```text
Power price = $35/MWh
Gas price = $4/MMBtu
Heat rate = 7.070 MMBtu/MWh

Fuel cost = $28.28/MWh

Spark spread = 35 - 28.28
Spark spread = $6.72/MWh
```

Fuel is covered, but a cycling start may not be worth it after VOM and start cost.

#### Example 3: Negative Spread

```text
Power price = $25/MWh
Gas price = $4/MMBtu
Heat rate = 7.070 MMBtu/MWh

Fuel cost = $28.28/MWh

Spark spread = 25 - 28.28
Spark spread = -$3.28/MWh
```

For energy-only economics, this is usually not a run hour.

### ASCII View

```text
Power price line: $55/MWh

Fuel cost at good HR:       $28/MWh  |############
Fuel cost at worse HR:      $33/MWh  |##############
Power price:                $55/MWh  |########################

Spark spread is the space between fuel cost and power price.
Worse heat rate narrows that space.
```

### How The Framework Treats Spark Spread

The framework uses spark spread in a few different ways:

| Use | Meaning |
| :--- | :--- |
| Dispatch economics | Hourly power price and daily gas price help decide whether the plant runs. |
| Revenue attribution | Spark spread output shows energy margin before full LTSA/financial costs. |
| Mode comparison | Modes A/B/C compare how much spark spread is sacrificed to reduce LTSA cost and risk. |
| Back-cast validation | Synthetic spark spreads are compared against historical market/climate data. |
| Stress scenarios | 2022-type gas price shocks can test upside/downside dispatch and LTSA effects. |

The framework reports examples like "average annual spark spread" in dollars per year. That is not the same as a single hourly $/MWh spread. It is the accumulated spread value over dispatched energy in the simulation.

Simple aggregation:

```text
Hourly spark spread value =
  spark spread ($/MWh) * MWh generated in that hour

Annual spark spread value =
  sum of hourly spark spread values over the year
```

### What Spark Spread Does Not Tell You

Spark spread is useful, but incomplete.

It does not fully answer:

- Did the unit have to start?
- Was it already online?
- Was it in forced outage?
- Was it derated by temperature?
- Was the run long enough to recover start cost?
- Did the run accelerate EOH and inspection timing?
- Did the plant breach an LTSA guarantee?
- Did high operation create future degradation?

So spark spread is a signal, not the full answer.

The core idea:

```text
Higher heat rate -> higher fuel cost -> lower spark spread
Lower spark spread -> fewer economic dispatch hours
Fewer economic dispatch hours -> lower revenue opportunity
```

## Daily Model Inputs And Outputs

Heat rate is updated inside the daily model loop, but several inputs are hourly.

### Inputs

| Input | Frequency | Source | What it does |
| :--- | :--- | :--- | :--- |
| Load profile | Hourly | Dispatch model | Part-load operation changes the heat-rate multiplier. |
| Ambient temperature | Hourly | Climate simulation | Hotter ambient conditions worsen heat rate. |
| Fired hours | Daily summary from hourly dispatch | Dispatch model | Drives time-based degradation. |
| Compressor fouling state | Daily state | Engineering model | Adds recoverable heat-rate loss. |
| Compressor erosion state | Daily or annual trend | Engineering model | Adds non-recoverable heat-rate loss. |
| HGP wear state | Daily or interval trend | Engineering model | Adds recoverable heat-rate loss between inspections. |
| Gas price | Daily | Gas market simulation | Converts heat rate into fuel cost. |

### Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Effective heat rate | Dispatch model | Current fuel intensity used for dispatch economics. |
| Fuel cost per MWh | Dispatch and financial layer | Variable fuel cost for each operating hour. |
| Heat-rate degradation state | Engineering model | Tracks how much performance has worsened since reset. |
| Heat-rate guarantee exposure | LTSA / financial layer | Helps evaluate whether contractual heat-rate limits may be breached. |

Simple flow:

```text
Hourly load + hourly temperature
        |
        v
Base heat rate adjusted for ambient and part load
        |
        v
Add fouling, erosion, and HGP degradation
        |
        v
Effective heat rate
        |
        v
Fuel cost and dispatch margin
```

## How Heat Rate Feeds Step 2 Dispatch

Step 2 dispatch decides whether the plant should run. Heat rate matters because it sets the fuel cost side of that decision.

The dispatch model is effectively asking:

```text
Will power revenue cover fuel cost, VOM, start cost, and wear cost?
```

Heat rate directly affects the fuel cost:

```text
Fuel cost = effective heat rate * gas price
```

If heat rate worsens, the plant becomes less competitive. Marginal runs can disappear first.

```text
Before degradation:
power price - fuel cost - VOM - start allocation > 0
        -> dispatch

After degradation:
power price - higher fuel cost - VOM - start allocation <= 0
        -> do not dispatch
```

This is why the daily feedback loop matters. Yesterday's operation can worsen today's heat-rate state, and today's heat-rate state can change tomorrow's dispatch decision.

## Worked Example: One Percent Heat-Rate Degradation

Assume:

| Item | Value |
| :--- | ---: |
| Baseline heat rate | 7,070 Btu/kWh |
| Degradation | 1.0% |
| Gas price | $4.00/MMBtu |
| Annual dispatched energy | 1,500,000 MWh |

Calculate degraded heat rate:

```text
Degraded heat rate = 7,070 * 1.01
Degraded heat rate = 7,140.7 Btu/kWh
```

Convert to extra fuel cost:

```text
Extra heat rate = 7,140.7 - 7,070
Extra heat rate = 70.7 Btu/kWh
Extra heat rate = 0.0707 MMBtu/MWh

Extra fuel cost per MWh = 0.0707 * $4.00
Extra fuel cost per MWh = $0.2828/MWh
```

Annual impact:

```text
Annual extra fuel cost = 1,500,000 MWh * $0.2828/MWh
Annual extra fuel cost = $424,200
```

This lines up with the framework's statement that a 1% heat-rate change can create hundreds of thousands of dollars per year of fuel-cost impact.

## Part-Load Heat Rate

Combined-cycle plants are usually less efficient at part load. The framework uses a polynomial rather than a step table:

```text
HR_multiplier(L) = 2.648 - 4.296 * L + 2.648 * L^2
```

Where:

| Symbol | Meaning |
| :--- | :--- |
| L | Fractional load from 0.5 to 1.0 |
| 1.0 | Full load |
| 0.5 | 50% load / minimum load in the framework |

Framework values:

| Load | Multiplier | Heat rate if ISO baseline is 7,070 Btu/kWh |
| :--- | ---: | ---: |
| 100% | 1.000 | 7,070 Btu/kWh |
| 90% | 1.015 | 7,176 Btu/kWh |
| 80% | 1.038 | 7,339 Btu/kWh |
| 70% | 1.068 | 7,553 Btu/kWh |
| 60% | 1.107 | 7,826 Btu/kWh |
| 50% | 1.162 | 8,215 Btu/kWh |

Part-load heat rate matters because the dispatch model may choose to run the plant at minimum load during some hours. Those MWh are usually less fuel-efficient than full-load MWh.

## Heat-Rate Degradation Components

The framework separates heat-rate degradation into recoverable and non-recoverable pieces.

| Component | Basic meaning | Reset or recovery |
| :--- | :--- | :--- |
| Compressor fouling | Dirt/deposits reduce compressor efficiency. | Partly recovered by water wash. |
| Hot gas path wear | Turbine section condition worsens between inspections. | Partly recovered at CI/HGP/MI. |
| Compressor erosion | Physical material loss changes blade shape. | Not recovered by wash; partial recovery only at major work. |
| HRSG/BOP degradation | Plant-level losses outside the GT core. | Generally non-recoverable in this framework. |

The beginner idea:

```text
Recoverable degradation:
can improve after wash or inspection

Non-recoverable degradation:
stays in the plant baseline unless major repair/overhaul changes it
```

## Temporary Effects Vs Long-Term Degradation

Heat rate can worsen for different reasons. Do not mix them up.

| Type | Example | Does it reset quickly? | Model treatment |
| :--- | :--- | :--- | :--- |
| Ambient effect | 90 deg F heat rate is higher than ISO heat rate. | Yes, when weather changes. | Driven by hourly climate input. |
| Part-load effect | 50% load heat rate is worse than full load. | Yes, when dispatch load changes. | Driven by hourly load profile. |
| Recoverable degradation | Compressor fouling. | Partly, after wash or inspection. | Carried in state vector until reset event. |
| Non-recoverable degradation | Compressor erosion or age-related BOP losses. | No normal daily reset. | Carried as persistent state. |

This matters for interpretation. A bad heat rate on a hot day does not necessarily mean the plant is permanently degraded. A persistent heat-rate trend after correcting for load and ambient conditions is more concerning.

## What The Framework Includes

The high-level framework includes these heat-rate ideas:

- Post-HGP baseline heat rate at ISO is 7,070 Btu/kWh.
- Heat rate worsens at high ambient temperature.
- Heat rate worsens at part load.
- Heat rate degradation between inspections is modeled as 0.8% to 1.5% in the first year.
- Compressor fouling is non-linear and recoverable.
- Hot gas path degradation is recoverable through inspection events.
- Compressor erosion and HRSG/BOP degradation are treated as non-recoverable trends.
- Effective heat rate is fed back to the dispatch model for the next day's economics.

## What The Framework Leaves Out

The high-level framework is suitable for due-diligence modeling, but it is not a full OEM performance model.

| Missing detail | Why it matters |
| :--- | :--- |
| Actual plant heat-rate test data | Needed to validate the 7,070 Btu/kWh baseline. |
| Full OEM correction curves | Needed for more precise ambient and load corrections. |
| HHV/LHV reconciliation against market data | Avoids comparing heat rates on different fuel bases. |
| Compressor wash history | Needed to calibrate fouling and recovery. |
| Unit-level GT split | A 2x1 plant may have different condition by GT. |
| Duct firing or supplemental firing assumptions | Could change heat rate and dispatch economics if present. |
| Gross vs net auxiliary load detail | Net heat rate depends on internal plant loads. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.3 | Effective heat rate is fed back to dispatch. | Green for model architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.2 | Athens-type heat-rate values and degradation components. | Amber until plant test data is available. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.6 | Part-load heat-rate polynomial and VOM context. | Green for model structure, Amber for asset calibration. |
| `docs/InfraSure_ModelingFramework_V2.md`, Appendix B.3-B.4 | Compressor and HGP degradation assumptions. | Green/Amber depending on component. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Pipeline framing and climate-dispatch-performance link. | Green for communication. |
| U.S. EIA heat-rate FAQ | Heat rate as fuel energy per net kWh and efficiency conversion using 3,412 Btu/kWh. | Green for basic definition. |
| U.S. EIA spark-spread explainer | Spark spread formula, benchmark heat-rate context, and limitation that spark spread excludes other costs. | Green for market definition. |

## Open Questions Before Investment Use

Before relying on heat-rate outputs in a final investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| Is 7,070 Btu/kWh based on a recent actual test or an assumed post-HGP baseline? | Sets the starting point for all fuel-cost projections. |
| Are all heat-rate values consistently HHV and net? | Prevents basis mismatch. |
| Are we using average heat rate or incremental heat rate for the decision at hand? | Average heat rate is useful for reporting; incremental heat rate is often needed for marginal dispatch and offers. |
| Do we have plant-specific ambient and part-load correction curves? | Improves dispatch precision. |
| Which plant type is being modeled: simple-cycle, CCGT, aero, frame, CHP, or something else? | Prevents applying Athens CCGT heat-rate behavior to the wrong asset. |
| For CHP, how is useful steam or heat credited? | Electric-only heat rate can misstate CHP economics. |
| What is the actual compressor wash schedule and recovery history? | Calibrates fouling and reset assumptions. |
| How different are GT-A and GT-B conditions? | A 2x1 average may hide unit-level imbalance. |
| How is heat-rate guarantee exposure calculated in the actual LTSA? | Converts engineering degradation into contractual cost. |
| Are degradation and ambient corrections applied in the right order? | Prevents double-counting or undercounting losses. |

## Quick Recap

Heat rate is the plant's fuel intensity. Lower is better. Higher means the plant burns more fuel for the same MWh.

For this model:

```text
Hourly temperature changes heat rate.
Hourly load changes heat rate.
Daily operation worsens degradation state.
Effective heat rate sets fuel cost.
Fuel cost changes Step 2 dispatch economics.
```

That is why heat rate comes immediately after capacity in the learning path. Capacity tells us how many MW the plant can sell. Heat rate tells us how expensive those MWh are to produce.
