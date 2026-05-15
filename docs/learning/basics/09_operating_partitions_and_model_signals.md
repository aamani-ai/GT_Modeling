# Operating Partitions And Model Signals

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Read these first if the individual concepts are new:

- [Capacity](./01_capacity.md)
- [Heat Rate](./02_heat_rate.md)
- [EOH And Starts](./03_eoh_and_starts.md)
- [Dispatch And The Daily Loop](./05_dispatch_and_daily_loop.md)
- [LTSA And Service Contracts](./08_ltsa_and_service_contracts.md)

> Plant-Type Note
> The partitions in this guide are general modeling lenses. The exact thresholds, labels, and commercial meaning depend on plant type, turbine model, service contract, market rules, and operating history. Use the examples here as teaching examples, not universal rules.

## First-Time Reader Map

Gas plant operation can be sliced in more than one way.

That is not a problem. It is the point.

Each slice answers a different modeling question:

```text
load mode          -> how hard is the machine working right now?
start type         -> how stressful was the restart?
dispatch profile   -> what kind of plant behavior is this overall?
season             -> when does it tend to run?
stress accumulation-> how much maintenance life did operation consume?
price regime       -> why did it run or stay off economically?
```

The important beginner lesson:

```text
No single partition explains the plant.
The model needs several partitions at once.
```

## Why This Guide Exists

The earlier basics guides teach the pieces:

| Existing guide | Piece it teaches |
| :--- | :--- |
| [Capacity](./01_capacity.md) | MW capability, ambient derate, effective capacity. |
| [Heat Rate](./02_heat_rate.md) | Fuel efficiency, part-load penalty, spark spread. |
| [EOH And Starts](./03_eoh_and_starts.md) | Fired hours, starts, trips, EOH, inspection timing. |
| [Dispatch And The Daily Loop](./05_dispatch_and_daily_loop.md) | Hourly dispatch inside a daily state update. |
| [State Vector And Feedback](./07_state_vector_and_feedback.md) | How today's operation changes tomorrow's state. |
| [Marginal Cost And Offer Curves](../market_and_operations/02_marginal_cost_and_offer_curves.md) | How heat-rate curves and gas prices become market economics. |

This guide connects them.

It explains how one hourly operating trace becomes multiple model signals:

```text
hourly MW output
  -> load mode
  -> start/shutdown events
  -> fired hours
  -> factored hours / EOH
  -> fuel cost and spark spread
  -> seasonal and price-regime behavior
  -> maintenance, outage, LTSA, and cashflow effects
```

## The Six Partitions

| Partition | Plain question | Primary model use |
| :--- | :--- | :--- |
| Load mode | How hard is the turbine working right now? | Heat rate, part-load behavior, load swings, stress intensity. |
| Start type | How long was the unit off before restart? | Start cost, EOH, thermal fatigue, LTSA start limits. |
| Dispatch profile | What kind of plant is this overall? | Modeling approach, revenue style, constraint priority. |
| Season | When does it run and why? | Calibration, weather effects, fuel-price context, outage scheduling. |
| Stress accumulation | How much maintenance life did operation consume? | Inspection timing, EOH headroom, forced-outage risk. |
| Price regime | What economic condition caused running or not running? | Dispatch, marginal cost, offer curves, spread capture. |

These are not competing definitions. They are different lenses.

## One Hour Can Have Many Labels

Take one example hour:

| Lens | Label for the same hour |
| :--- | :--- |
| Load mode | Base load, because the plant is above 97% of available load. |
| Start type | Hot-start run hour, because the plant restarted after 4 hours offline. |
| Dispatch profile | Cycling CCGT behavior, because the plant started for a high-price window. |
| Season | Summer peak. |
| Stress accumulation | Fired hour plus one hot-start event for the day. |
| Price regime | High spark-spread hour. |

The same hour is not just "running." It is running in a specific physical, commercial, and historical context.

```text
one operating hour
  |
  +--> MW level label
  +--> start/shutdown context
  +--> season label
  +--> price-regime label
  +--> stress contribution
  +--> cashflow contribution
```

## Partition 1: Load Mode

Load mode asks:

```text
How hard is the machine working right now?
```

Simple teaching labels:

| Load mode | Example threshold | Plain meaning |
| :--- | :--- | :--- |
| No load / offline | 0 MW | Plant is not producing energy. |
| Minimum load | Around Pmin, often 40% to 50% load | Online but near minimum stable output. |
| Part load | Above minimum, below near-full output | Producing, but not at most efficient/full output point. |
| Base load / full load | Around 97%+ of available output | Running near full available capability. |

The exact threshold is plant-specific. A simple-cycle aero, large frame simple-cycle unit, 1x1 CCGT, 2x1 CCGT, and CHP plant can have different definitions.

### Load Profile Example: Baseload-Style Day

This plant is either off or near full load. It does not spend much time at part load.

```text
Hour: 00  01  02  03  04  05  06  07  08  09  10  11
MW:   000 000 000 000 000 000 500 500 500 500 500 500
Mode: O   O   O   O   O   O   B   B   B   B   B   B

Hour: 12  13  14  15  16  17  18  19  20  21  22  23
MW:   500 500 500 500 500 500 500 500 500 500 500 500
Mode: B   B   B   B   B   B   B   B   B   B   B   B
```

Legend:

```text
O = offline
B = base load / near full load
```

ASCII plot:

```text
MW
500 |            ##################
400 |            ##################
300 |            ##################
200 |            ##################
100 |            ##################
  0 |############
     00 03 06 09 12 15 18 21 24
```

Model interpretation:

| Signal | What this profile suggests |
| :--- | :--- |
| Fired hours | High. |
| Starts | Low if the plant stays on for long blocks. |
| Heat rate | Often better because the unit is near efficient output. |
| EOH ratio | Often closer to fired hours, unless load or temperature multipliers apply. |
| Revenue style | Energy-margin capture over many hours. |

### Load Profile Example: Peaker-Style Day

This plant runs only during a short high-price window.

```text
Hour: 00  01  02  03  04  05  06  07  08  09  10  11
MW:   000 000 000 000 000 000 000 000 000 000 000 000
Mode: O   O   O   O   O   O   O   O   O   O   O   O

Hour: 12  13  14  15  16  17  18  19  20  21  22  23
MW:   000 000 100 250 400 450 450 300 000 000 000 000
Mode: O   O   M   P   P   B   B   P   O   O   O   O
```

Legend:

```text
M = minimum load
P = part load
B = base load
O = offline
```

ASCII plot:

```text
MW
500 |
450 |                                  ## ##
400 |                               ## ## ##
300 |                            ## ## ## ##
200 |                         ## ## ## ## ##
100 |                      ## ## ## ## ## ##
  0 |######################               ########
     00 03 06 09 12 15 18 21 24
```

Model interpretation:

| Signal | What this profile suggests |
| :--- | :--- |
| Fired hours | Low to medium. |
| Starts | Can be high relative to fired hours. |
| Heat rate | May be worse if many hours are part-load or startup/shutdown hours. |
| EOH ratio | Can be much higher than fired hours because starts dominate. |
| Revenue style | Optionality: capture only high-price windows. |

### Load Profile Example: Intermediate / Cycling Day

This plant runs through a broad afternoon/evening block but changes output.

```text
Hour: 00  01  02  03  04  05  06  07  08  09  10  11
MW:   000 000 000 000 000 150 250 300 350 400 450 500
Mode: O   O   O   O   O   M   P   P   P   P   P   B

Hour: 12  13  14  15  16  17  18  19  20  21  22  23
MW:   500 500 450 400 350 250 150 000 000 000 000 000
Mode: B   B   P   P   P   P   M   O   O   O   O   O
```

This kind of day creates more information than a simple on/off flag:

```text
start happened
load ramped up
plant spent hours at part load
plant reached base load for only part of the day
load ramped down
shutdown happened
```

Those details matter for heat rate, load swings, starts, EOH, and fatigue.

## Why Load Mode Matters

Load mode affects multiple parts of the model.

| Model area | Why load mode matters |
| :--- | :--- |
| Heat rate | Part-load operation is usually less efficient than full-load operation. |
| Marginal cost | Incremental heat rate can change with MW level. |
| Capacity | Pmax defines the top of the load range; Pmin defines the minimum stable output. |
| EOH / stress | Some frameworks count high-load hours or large load swings differently. |
| Emissions | Emissions rates can change with load and startup/shutdown behavior. |
| Offers | Offer blocks must sit within feasible Pmin/Pmax and mode limits. |

## Partition 2: Start Type

Start type asks:

```text
How long was the unit off before it came back on?
```

The Athens teaching example uses:

| Start type | Shutdown duration | EOH impact in framework |
| :--- | :--- | ---: |
| Hot start | Less than 8 hours | 50 EOH |
| Warm start | 8 to 72 hours | 150 EOH |
| Cold start | More than 72 hours | 350 EOH |
| Emergency trip | Forced shutdown from full load | 500 EOH |

ASCII shutdown-duration view:

```text
shutdown duration before restart

0 hr             8 hr                         72 hr
 |---------------|-----------------------------|
      hot start            warm start              cold start
```

Start type is different from load mode.

```text
Start type:
  context before the run

Load mode:
  how hard the unit runs during the hour
```

Example:

| Day | Start type | Later load mode | Interpretation |
| :--- | :--- | :--- | :--- |
| Day A | Hot start | Base load | Less severe restart, then hard running. |
| Day B | Cold start | Minimum load | Severe restart, then low-output operation. |
| Day C | No start | Base load | Continued operation, no start event today. |

This is why a cold-start low-output day can be economically weak but still stressful.

## Partition 3: Dispatch Profile

Dispatch profile asks:

```text
What kind of plant behavior is this overall?
```

This is a plant-level or period-level label, not an hour-level label.

| Dispatch profile | Typical pattern | Modeling implication |
| :--- | :--- | :--- |
| Baseload | Runs many hours, often near high load. | Long-term average models may work better than for peakers, but outages and degradation still matter. |
| Intermediate / mid-merit | Runs when spreads are good, often seasonal or daily cycling. | Needs hourly or sub-hourly dispatch logic to capture starts and part-load behavior. |
| Peaker | Runs few hours, usually high-price windows. | Starts, ramp limits, minimum run, and high-price optionality dominate. |
| Seasonal | Runs mainly in winter, summer, or other seasonal windows. | Needs season labels and price/fuel/weather context. |
| Must-run / CHP-like | Runs because of steam/heat or reliability need. | Power price may not be the only dispatch driver. |

### Profile Comparison

```text
Baseload-style month:
Run:  ##########################
Off:  ....

Intermediate-style month:
Run:  ####..####...#####..###..
Off:  ....##....###.....##...##

Peaker-style month:
Run:  #....#......##.......#...
Off:  .####.######..#######.###
```

The same turbine technology can behave differently depending on market conditions, contract strategy, and operator choices.

## Partition 4: Season

Season asks:

```text
When does it run and why?
```

Seasonal labels are useful because gas plant economics often change with:

- power demand;
- heating and cooling load;
- gas prices;
- ambient temperature;
- outages scheduled around shoulder months;
- capacity or reliability needs.

Example seasonal split:

| Season label | Possible operating reason |
| :--- | :--- |
| Winter peak | Heating demand and gas/power volatility. |
| Spring shoulder | Lower demand; good window for planned outage. |
| Summer peak | Cooling demand, high temperatures, derates, high prices. |
| Fall shoulder | Lower demand; another possible maintenance window. |

### Seasonal Operating Cluster Example

This example shows a plant that runs heavily in January/February, lightly in summer, and again in December.

```text
Month: Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec
Run:   ### ### .   .   .   #   ##  #   .   .   .   ###
```

Legend:

```text
### = many running days
##  = moderate running days
#   = few running days
.   = mostly off
```

Model use:

| Signal | Why season matters |
| :--- | :--- |
| Historical calibration | Monthly clusters can reveal plant role. |
| Weather adjustment | Summer hot weather can lower Pmax and worsen heat rate. |
| Outage planning | Shoulder months may be preferred for planned inspections. |
| Price regime | Winter and summer can have different spreads. |
| Fuel risk | Gas price volatility may be seasonal. |

## Partition 5: Stress Accumulation

Stress accumulation asks:

```text
How much maintenance life did operation consume?
```

The meeting note framed this as:

```text
factored hours / fired hours = accumulated stress factor
```

This is useful because fired hours alone can hide how stressful the operation was.

## Fired Hours, Factored Hours, And EOH

| Term | Plain meaning |
| :--- | :--- |
| Fired hours | Hours with fuel burning in the turbine. |
| Factored hours | Hours adjusted for operating severity, depending on OEM/contract logic. |
| EOH | Equivalent operating hours; broad contract/maintenance counter used in this learning path. |
| Stress factor | Ratio showing how much faster factored life grows than fired hours. |

Simple ratio:

```text
stress factor = factored hours / fired hours
```

Example:

| Day | Fired hours | Factored hours / EOH | Stress factor |
| :--- | ---: | ---: | ---: |
| Smooth high-load day | 10 | 10 | 1.0x |
| Hot-start cycling day | 10 | 60 | 6.0x |
| Cold-start day | 10 | 360 | 36.0x |
| Trip day | 6 | 506 | 84.3x |

The exact numbers depend on the framework or contract. The learning point is that the ratio is not automatically constant.

### Stress Factor By Load Example

The meeting note also raised an important idea: stress per hour can vary with load.

Illustrative example:

| Load mode | Fired hours | Factored hours | Stress factor |
| :--- | ---: | ---: | ---: |
| Minimum load | 4 | 3.2 | 0.8x |
| Part load | 4 | 4.4 | 1.1x |
| Base load | 4 | 5.2 | 1.3x |

ASCII plot:

```text
Stress factor
1.4x |                         *
1.2x |              *
1.0x |
0.8x |   *
     +--------------------------------
        min load   part load   base load
```

This is not saying every plant has these exact multipliers. It is showing why the model should not assume:

```text
factored hours = fired hours
```

unless that simplification is deliberate.

## Partition 6: Price Regime

Price regime asks:

```text
Why did the plant run or stay off economically?
```

For gas plants, economics often drive dispatch. Unlike wind or solar, a gas plant usually has a large variable fuel cost.

Simple dispatch test:

```text
power price > fuel cost + VOM + start/wear hurdle
```

Fuel cost depends on heat rate:

```text
fuel cost per MWh = heat rate in MMBtu/MWh * gas price in $/MMBtu
```

Price-regime labels:

| Price regime | Plain meaning | Likely behavior |
| :--- | :--- | :--- |
| Deep out-of-money | Power price far below variable cost. | Stay off unless must-run. |
| Marginal | Price near operating cost. | Dispatch depends on start cost, Pmin, min run, and EOH penalty. |
| In-the-money | Price above variable cost. | Run if available and constraints allow. |
| Scarcity / spike | Very high price. | Run hard if available; outage or derate is costly. |

### Price Regime Example

Assume:

```text
Heat rate = 7.5 MMBtu/MWh
Gas price = $4.00/MMBtu
VOM = $3.00/MWh

Fuel cost = 7.5 * 4.00
Fuel cost = $30.00/MWh

Simple variable cost = 30.00 + 3.00
Simple variable cost = $33.00/MWh
```

Hourly classification:

| Hour | Power price | Simple variable cost | Price regime |
| :--- | ---: | ---: | :--- |
| 08:00 | $25/MWh | $33/MWh | Deep out-of-money. |
| 12:00 | $35/MWh | $33/MWh | Marginal. |
| 17:00 | $70/MWh | $33/MWh | In-the-money. |
| 18:00 | $180/MWh | $33/MWh | Scarcity / spike. |

ASCII view:

```text
$/MWh
180 |                              *
140 |
100 |
 70 |                         *
 35 |              *
 33 |------------- variable cost line
 25 |     *
    +--------------------------------
      08:00   12:00   17:00   18:00
```

The plant may still avoid the 12:00 marginal hour if starting requires running through weak hours or if it is close to an inspection threshold.

## How The Partitions Interact

The partitions are useful because they interact.

Example feedback loop:

```text
high summer prices
  -> plant runs more hours
  -> load mode shifts toward base load
  -> fired hours and stress accumulation increase
  -> EOH headroom shrinks
  -> next inspection moves closer
  -> dispatch strategy may become more conservative
  -> future load profile changes
```

Another loop:

```text
approaching major inspection
  -> Mode B/C raises wear cost
  -> marginal price hours no longer dispatch
  -> fewer starts and fired hours
  -> inspection may be deferred
  -> summer revenue window may be protected
```

This is why the model needs recursive feedback rather than one static schedule.

## Worked Example: One Operating Day

Assume one simplified day for a CCGT block.

| Hour block | MW | Load mode | Price regime | Comment |
| :--- | ---: | :--- | :--- | :--- |
| 00-05 | 0 | Offline | Out-of-money | Plant remains off. |
| 06-08 | 150 | Minimum load | Marginal | Plant starts and reaches stable load. |
| 09-13 | 350 | Part load | In-the-money | Plant follows profitable daytime hours. |
| 14-18 | 500 | Base load | Scarcity / spike | Runs near full available output. |
| 19-21 | 300 | Part load | In-the-money | Ramps down as prices fall. |
| 22-23 | 0 | Offline | Out-of-money | Shuts down. |

ASCII operating shape:

```text
MW
500 |                            #####
400 |                            #####
350 |                 #####      #####
300 |                 #####      #####  ###
200 |        ###      #####      #####  ###
150 |        ###      #####      #####  ###
  0 |######                         #####  ##
     00 03 06 09 12 15 18 21 24
```

This one day produces several signals:

| Signal | Example value | Why it matters |
| :--- | ---: | :--- |
| Fired hours | 16 | Feeds EOH, fouling, TBC, rotor exposure. |
| Starts | 1 | Feeds start cost, EOH, fatigue, start limits. |
| Start type | Warm start | Sets start EOH and start cost. |
| Load modes | Minimum, part, base | Feeds heat rate, stress, and operating diagnostics. |
| Load swings | Several ramps | Can feed fatigue or load-swing EOH logic. |
| Seasonal label | Summer | Affects temperature, Pmax, heat rate, outage planning. |
| Price regime | Mixed | Explains why some hours ran and others did not. |
| MWh | Sum of hourly MW | Feeds revenue, VOM, LTSA VOM. |

## Same Day, Different Model Lenses

The same dispatch day can be summarized by different teams in different ways.

| Team lens | Summary |
| :--- | :--- |
| Market analyst | The plant captured afternoon scarcity prices. |
| Operations engineer | The plant cycled from off to minimum load to base load and back down. |
| Maintenance planner | One warm start plus 16 fired hours consumed life. |
| Contract analyst | Starts, EOH reserve, and possible start allowance usage changed. |
| Investor | Gross margin was earned, but future inspection timing moved closer. |

All of those summaries can be true at the same time.

## Load Duration View

A load profile shows when MW happened. A load duration curve sorts the hours from highest to lowest output.

Hourly sequence:

```text
Hour order:  00 01 02 03 04 05 06 07 08 09
MW:          000 000 150 250 500 500 350 200 000 000
```

Load duration:

```text
Sorted MW:   500 500 350 250 200 150 000 000 000 000
```

ASCII comparison:

```text
Chronological load profile:
MW
500 |            ## ##
350 |            ## ## ##
200 |      ##    ## ## ## ##
  0 |## ##                ## ##
     00 01 02 03 04 05 06 07 08 09

Load duration curve:
MW
500 |## ##
350 |## ## ##
200 |## ## ## ## ##
  0 |            ## ## ## ##
     highest output hours -> lowest output hours
```

Why both matter:

| View | Best use |
| :--- | :--- |
| Chronological profile | Starts, shutdowns, ramps, min up/down, warm/cold start classification. |
| Load duration curve | How often the plant ran at high, part, or low output. |

Do not use a load duration curve when the ordering of hours matters.

## Dispatch Profile Vs Load Mode

These two are easy to mix up.

| Concept | Time scale | Example |
| :--- | :--- | :--- |
| Load mode | One hour or operating interval. | This hour is base load. |
| Dispatch profile | Many days, months, or years. | This plant behaves like a peaker. |

Example:

```text
A peaker can run at base load during the few hours it runs.
A baseload plant can still have part-load hours during ramps or constraints.
```

So this statement is wrong:

```text
Peaker = always part load
```

Better:

```text
Peaker = runs infrequently, usually when prices are high.
When it runs, it may run at high load.
```

## Start Type Vs Dispatch Profile

Start type is event-level. Dispatch profile is period-level.

| Concept | Time scale | Example |
| :--- | :--- | :--- |
| Start type | One startup event. | Cold start after 5 days offline. |
| Dispatch profile | Plant behavior over time. | Seasonal peaker. |

A seasonal peaker may have many cold starts if it sits idle for long periods. A daily cycling plant may have many hot or warm starts.

## Season Vs Price Regime

Season and price regime are related but not identical.

| Concept | What it says | What it does not say |
| :--- | :--- | :--- |
| Season | Calendar/weather context. | Whether the plant was profitable in a specific hour. |
| Price regime | Economic spread context. | Whether the pattern is winter, summer, or shoulder season. |

Example:

```text
Summer hour:
  high demand may raise power price
  hot weather may lower Pmax
  hot weather may worsen heat rate
  gas price may or may not be high
```

The model needs all of those, not just a season label.

## How Step 2 Should Use These Partitions

Step 2 should not treat these partitions as decorative labels. They should become inputs, intermediate calculations, or outputs.

| Partition | Step 2 role |
| :--- | :--- |
| Load mode | Derived from hourly MW divided by available Pmax or mode-specific Pmax. |
| Start type | Derived from shutdown duration before startup. |
| Dispatch profile | Derived from many days of operation; useful for diagnostics and strategy comparison. |
| Season | Input label from date/weather calendar; useful for calibration and outage planning. |
| Stress accumulation | Derived from fired hours, load, starts, trips, and swings. |
| Price regime | Derived from power price, gas price, heat rate, VOM, and start/wear hurdle. |

Daily handoff:

```text
hourly dispatch output
  |
  +--> classify load modes
  +--> identify starts and shutdown durations
  +--> classify price regimes
  +--> summarize fired hours and MWh
  +--> calculate EOH / factored hours
  +--> update state and contract counters
```

## Model Signal Dictionary

| Signal | Built from | Used by |
| :--- | :--- | :--- |
| Online flag | Dispatch schedule | Fired hours, starts, availability diagnostics. |
| Hourly MW | Dispatch schedule | MWh, load mode, heat rate, revenue. |
| Load mode | MW / available Pmax | Heat-rate correction, stress intensity, diagnostics. |
| Start event | Offline-to-online transition | Start cost, EOH, fatigue, LTSA start limits. |
| Shutdown duration | Time since last online hour | Hot/warm/cold start classification. |
| Fired hours | Online hours with fuel burning | EOH, fouling, TBC, rotor, heat-rate degradation. |
| MWh | MW summed over hours | Revenue, VOM, LTSA VOM, capacity factor. |
| Load swings | Large changes in MW | EOH adders, fatigue, ramp diagnostics. |
| Price regime | Price minus marginal cost | Dispatch diagnostics and strategy analysis. |
| Season | Date/calendar/weather | Calibration, outage planning, seasonal diagnostics. |
| EOH / factored hours | Fired hours plus events and multipliers | Inspection timing, LTSA reserve, maintenance planning. |

## What We Already Cover

| Topic | Current coverage |
| :--- | :--- |
| Start type | Covered in [EOH And Starts](./03_eoh_and_starts.md). |
| Heat rate at part load | Covered in [Heat Rate](./02_heat_rate.md). |
| Dispatch and daily state update | Covered in [Dispatch And The Daily Loop](./05_dispatch_and_daily_loop.md). |
| Pmin/Pmax and feasible operating range | Covered in [Operating Range: Pmin And Pmax](../market_and_operations/01_operating_range_pmin_pmax.md). |
| Marginal cost and price regime | Covered in [Marginal Cost And Offer Curves](../market_and_operations/02_marginal_cost_and_offer_curves.md). |
| Weather and seasonal effects | Covered in [Weather-Adjusted Operating Curves](../market_and_operations/04_weather_adjusted_operating_curves.md). |
| State feedback | Covered in [State Vector And Feedback](./07_state_vector_and_feedback.md). |

This guide's role is to put those pieces on one page.

## What The Framework Includes

The high-level framework already includes the main ingredients:

- Hourly dispatch creates hourly operating profiles.
- Daily state updates summarize fired hours, starts, load profile, outages, and degradation.
- Heat rate changes with ambient temperature, part load, and degradation.
- EOH is driven by fired hours, starts, trips, and load swings.
- Dispatch Modes A/B/C change behavior near LTSA thresholds.
- Market economics connect power price, gas price, heat rate, VOM, start cost, and wear.
- Degraded heat rate, capacity, start costs, VOM, and outage risk feed back into dispatch.

## What The Framework Leaves Out

The framework still needs more explicit implementation choices.

| Missing detail | Why it matters |
| :--- | :--- |
| Exact load-mode thresholds | No load, min load, part load, and base load need plant-specific definitions. |
| Factored-hour formula by load | The meeting note suggests stress factor can vary by load; the model needs the actual rule or calibration. |
| Load-swing detection rule | Need thresholds, time window, and treatment of ramps vs normal following. |
| Seasonal clustering method | Monthly labels may be too coarse for some plants. |
| Price-regime thresholds | Need clear rules for marginal, in-the-money, and scarcity classifications. |
| Dispatch profile classification | Need data-driven rules for baseload, intermediate, peaker, and seasonal labels. |
| Train-level operating profile | A 2x1 CCGT needs GT-A, GT-B, HRSG-A, HRSG-B, and ST context if partial operation matters. |
| Validation against historical operations | Classifications should be checked against actual historian, CEMS, or ISO data. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Sections 2-3 | Hourly dispatch, daily state update, EOH/degradation feedback, Mode A/B/C framing. | Green for architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Sections 4.3-4.6 | Athens operating constraints, part-load heat rate, start costs, VOM, LTSA parameters. | Amber until validated against asset data. |
| [EOH And Starts](./03_eoh_and_starts.md) | Fired hours, start types, EOH examples, start stress. | Green for learning structure. |
| [Dispatch And The Daily Loop](./05_dispatch_and_daily_loop.md) | Hourly dispatch inside daily checkpoint. | Green for learning structure. |
| [Marginal Cost And Offer Curves](../market_and_operations/02_marginal_cost_and_offer_curves.md) | Price regime and marginal-cost framing. | Green for concept; plant data needed. |
| Meeting note provided by user | Six-partition learning framing: load mode, start type, dispatch profile, season, stress accumulation, price regime. | Amber as internal reasoning input; thresholds still need validation. |

## Open Questions Before Implementation

| Question | Why it matters |
| :--- | :--- |
| What exact load-mode bands should be used for each plant type? | Determines load distribution and heat-rate diagnostics. |
| Does the LTSA/OEM define factored hours by load level? | Controls stress accumulation and inspection timing. |
| How should minimum-load hours be detected for CCGT 1x1 vs 2x1 operation? | Mode-specific Pmin matters. |
| Should season labels be calendar-based, weather-based, or cluster-based? | Affects historical calibration and forecast scenarios. |
| What price-regime thresholds should be used? | Needed for dispatch diagnostics and strategy comparison. |
| Should dispatch profile be classified by capacity factor, starts, run blocks, or revenue capture? | Different definitions can label the same plant differently. |
| How should outage timing interact with season? | Planned inspection timing can sacrifice or protect high-value seasons. |
| Do we have historical hourly MW, starts, prices, gas, and weather for validation? | Needed to test whether the partitions explain real behavior. |

## Quick Recap

Gas plant operation should be read through multiple partitions.

```text
Load mode tells how hard the turbine is working.
Start type tells how stressful the restart was.
Dispatch profile tells what kind of plant behavior exists over time.
Season tells when the pattern occurs.
Stress accumulation tells how operation converts into maintenance life.
Price regime tells why the plant ran or stayed off economically.
```

The value of the model is in the interactions:

```text
prices and weather drive dispatch
dispatch creates load modes, starts, and fired hours
load modes and starts create stress accumulation
stress changes EOH, degradation, outage risk, and LTSA exposure
updated state changes tomorrow's dispatch
```

That is the bridge from simple operating data to the dynamic gas-turbine model.
