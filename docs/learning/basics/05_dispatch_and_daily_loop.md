# Dispatch And The Daily Loop

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

Read these first if capacity, heat rate, EOH, starts, VOM, or outages are new:

- [Capacity](./01_capacity.md)
- [Heat Rate](./02_heat_rate.md)
- [EOH And Starts](./03_eoh_and_starts.md)
- [Start Costs And VOM](./04_start_costs_and_vom.md)
- [Outages, Availability, And LTSA](./06_outages_availability_and_ltsa.md)
- [Operating Partitions And Model Signals](./09_operating_partitions_and_model_signals.md)

> Plant-Type Note
> Dispatch is a universal modeling layer, but the feasible operating choices are plant-type-specific. Simple-cycle GTs, CCGTs, frame units, aeroderivatives, and CHP plants can have different start times, Pmin/Pmax ranges, ramp rates, min up/down constraints, steam constraints, and market-offer behavior.

## First-Time Reader Map

If this topic is new, start with the operator's question:

```text
Should the plant run?
If yes, when should it start?
How many MW should it produce?
When should it shut down?
```

That decision is called dispatch.

The guide uses several terms that are easy to mix together:

| Term | First-time meaning |
| :--- | :--- |
| Dispatch | Deciding whether the plant runs and how much power it produces. |
| Unit commitment | The on/off decision: start, stay online, shut down, or stay offline. |
| Economic dispatch | The MW output decision once the unit is available and committed. |
| Hourly power price | Electricity price for each hour; revenue changes hour by hour. |
| Daily gas price | Fuel price used to estimate fuel cost for the day. |
| State | The plant condition remembered from yesterday. |
| State update | The end-of-day step that changes EOH, degradation, outage risk, and tomorrow's economics. |
| Simulation path | One possible future weather/price/operation story. |
| Mode A/B/C | Three operating strategies, from aggressive dispatch to conservative LTSA-cost control. |
| Feedback | Yesterday's operation changes tomorrow's plant condition and dispatch economics. |
| Static schedule | A precomputed dispatch schedule that does not re-optimize after state changes. |
| Dynamic dispatch | Dispatch that re-optimizes using the latest plant state. |

The mental stack is:

```text
market opportunity -> dispatch decision -> operating profile -> daily state update -> tomorrow's dispatch
```

## What Dispatch Means In Real Life

Dispatch is not the same as "the plant runs whenever prices are high."

A gas plant has to consider:

| Question | Why it matters |
| :--- | :--- |
| Is the plant available? | Outage status can block dispatch completely. |
| Is power price high enough? | Revenue must cover cost. |
| Is gas expensive today? | Fuel cost changes the margin. |
| What is the current heat rate? | Worse heat rate means more fuel per MWh. |
| How much capacity is available? | Hot weather or degradation can reduce MW output. |
| What start type is required? | Hot, warm, and cold starts have very different costs. |
| Is the plant close to CI/MI? | EOH proximity can make starts more expensive in Modes B/C. |
| Are min run or ramp constraints binding? | The plant may need to run through weak-price hours after starting. |

Simple dispatch hurdle:

```text
expected revenue
  must be greater than
fuel + VOM + start cost + wear + operating constraints
```

If that hurdle is not cleared, the plant may stay offline even if the power price is positive.

## Plant-Type Variations

Step 2 should ask the same economic question for every plant, but it should not use the same constraint set for every plant.

| Plant type | Dispatch focus | Constraint differences |
| :--- | :--- | :--- |
| Simple-cycle GT | High-price hours, reserves, fast response. | No steam-cycle lag; Pmin/Pmax and start costs are GT-only. |
| Combined-cycle GT | Energy margin plus steam-cycle economics. | 1x1 vs 2x1 modes, HRSG/ST warm-up, min load, and ramp limits matter. |
| Frame GT | Large MW blocks and thermal limits. | Slower starts and heavier thermal constraints can make short runs harder. |
| Aeroderivative GT | Flexibility and fast response. | Faster starts and modular maintenance can change commitment economics. |
| CHP / cogeneration | Power economics plus steam/heat service. | Heat demand, host reliability, and steam pressure can override pure power-price dispatch. |

That is why a later `market_and_operations` layer is useful: dispatch, offer curves, and historical operating envelopes are related, but they are not the same thing.

## Unit Commitment Vs Economic Dispatch

Two decisions happen together, but they are not the same.

| Decision | Plain question | Example |
| :--- | :--- | :--- |
| Unit commitment | Should the plant be on or off? | Start at 14:00 and shut down at 22:00. |
| Economic dispatch | If online, how many MW should it produce? | Run at 500 MW during high-price hours. |

ASCII view:

```text
Unit commitment:
  off off off ON  ON  ON  ON  off

Economic dispatch:
  0   0   0   450 500 520 480 0   MW
```

For a first-time reader, Step 2 is mostly this:

```text
choose the on/off schedule
and choose the MW output
while respecting costs and constraints
```

## Why Hourly Prices Still Matter

Power prices can change a lot inside one day. That is why dispatch is hourly.

Example:

```text
Morning:  price too low -> stay offline
Afternoon: price high   -> start and run
Night:     price weak   -> shut down
```

If the model only used one average daily power price, it could miss the value of running during a few high-value hours.

```text
Hourly dispatch captures:
  high-price windows
  low-price hours to avoid
  start timing
  shutdown timing
  ramp and minimum-run constraints
```

So the model is not "daily instead of hourly." It is:

```text
hourly economics inside the day
daily plant-condition update after the day
```

## How One Dispatch Day Becomes Model Signals

One day of dispatch creates several model signals:

```text
hourly dispatch schedule
  |
  +--> MWh generated and revenue
  |
  +--> fired hours
  |
  +--> hot/warm/cold start count
  |
  +--> shutdown duration for tomorrow's start classification
  |
  +--> fuel burn from heat rate
  |
  +--> VOM and start costs
  |
  +--> EOH and degradation updates
  |
  +--> outage-risk state for tomorrow
```

For a first-time reader, the important point is:

```text
Step 2 decides how the plant runs today.
The daily loop records what that did to the plant.
```

## Why This Matters

This guide answers the question that often causes confusion:

> If dispatch is hourly, why does the framework look daily?

The short answer:

```text
Dispatch is hourly inside the day.
The plant condition update is daily at the checkpoint.
```

The model does not ignore hourly power prices, hourly temperature, or hourly operating decisions. It uses those hourly details to decide how the plant runs during the day. Then, at the end of the day, the engineering model summarizes what happened and updates the plant state for tomorrow.

That daily checkpoint is where the model updates:

- fired hours
- start type
- load profile summary
- EOH
- heat rate
- capacity
- start costs
- VOM
- fouling
- cycling damage
- outage risk
- distance to the next inspection threshold

## Plain-English Concept

Think of the model as a daily notebook.

During the day, the plant operates hour by hour. At the end of the day, the model writes down what happened and updates the plant condition.

```text
Hour-by-hour dispatch:
  What should the plant do in each hour?

Daily engineering update:
  What did that operation do to the plant?

Tomorrow's dispatch:
  How does the new plant condition change tomorrow's economics?
```

The daily loop is not a loss of detail. It is the point where hourly operating detail becomes physical state.

## The Five-Step Pipeline

The framework has five stages:

| Step | Name | Plain meaning |
| :--- | :--- | :--- |
| 1 | Climate and market simulation | Creates weather, power price, and gas price paths. |
| 2 | Dispatch model | Decides hourly commitment and generation. |
| 3 | Engineering model | Converts operation into degradation and stress. |
| 4 | Maintenance and failure | Checks inspections, outages, duration, and cost classification. |
| 5 | Financial metrics | Converts operations and costs into P10/P50/P90 investor outputs. |

Step 2 is the main focus of this guide.

```text
Step 1 inputs
    |
    v
Step 2 hourly dispatch
    |
    v
Step 3 daily engineering state update
    |
    v
Step 4 outage and maintenance effects
    |
    v
Step 5 cashflow distribution
```

## What Step 2 Actually Does

Step 2 is the dispatch model. It answers questions like:

- Should the plant start?
- Should it stay online?
- Should it shut down?
- How many MW should it produce each hour?
- Is 1x1 operation better than 2x1 operation?
- Is a run worth it after fuel, VOM, start cost, and wear cost?

The dispatch model uses hourly information:

| Input | Frequency | Why dispatch needs it |
| :--- | :--- | :--- |
| Power price | Hourly | Revenue changes by hour. |
| Ambient temperature | Hourly | Capacity and heat rate change by hour. |
| Load profile / operating constraints | Hourly | Determines feasible MW, ramping, and part-load behavior. |
| Effective capacity | State input | Caps maximum MW. |
| Effective heat rate | State input | Converts gas price into fuel cost. |
| Start cost by type | State input | Determines whether starts clear the economic hurdle. |
| VOM | State input | Adds non-fuel variable cost. |
| EOH proximity | State input | Raises wear cost near inspection thresholds in Modes B/C. |
| Daily gas price | Daily | Fuel price for dispatch economics. |

Step 2 is therefore not just "run if power price is positive." It is closer to:

```text
Run if expected dispatch value clears:
  fuel cost
  + VOM
  + start cost
  + EOH/wear penalty
  + operating constraints
```

## Why The Outer Loop Is Daily

A 10-year model across many stochastic paths has to be detailed enough to capture degradation, but not so detailed that it becomes an OEM controls simulator.

The framework uses daily time-stepping because the key engineering state variables move naturally at a daily checkpoint:

| State variable | Why daily update is reasonable |
| :--- | :--- |
| EOH | Can be summed from the day's fired hours, starts, trips, and load swings. |
| Heat-rate degradation | Accumulates with operation and can be updated after the day's run. |
| Compressor fouling | Accumulates with fired hours and air quality over the day. |
| HRSG cycling | Depends on start type and thermal cycles during the day. |
| TBC time-at-temperature | Can be accumulated from the day's operating profile. |
| Forced outage probability | Evaluated from current state at the daily checkpoint. |
| Start cost multipliers | Depend on distance to inspection thresholds at the start of tomorrow. |

The model keeps hourly dispatch detail where hourly detail matters: prices, temperature, load, starts, and operating profile. It uses daily state updates where accumulated physical condition matters.

## Hourly Inside, Daily Outside

This is the most important mental model:

```text
For each simulation path:
  For each day:
    1. Read yesterday's plant state.
    2. Read today's hourly prices and weather.
    3. Check whether the plant is available.
    4. Dispatch the plant hour by hour if available.
    5. Summarize the operating day.
    6. Update EOH, degradation, costs, and outage risk.
    7. Feed updated state into tomorrow.
```

Expanded version:

```text
Day D starts
  |
  v
Plant state from Day D-1:
  capacity, heat rate, EOH, start costs, VOM, outage state
  |
  v
Hourly dispatch for Day D:
  hour 1 ... hour 24
  prices, temperature, load, starts, shutdown status
  |
  v
Daily summary:
  fired hours, start type, MWh, load swings, gas burn
  |
  v
Engineering update:
  EOH, fouling, heat rate, HRSG cycles, TBC time, rotor life
  |
  v
Day D+1 state
```

## A Simple Day Example

Assume the day starts with:

| State item | Value |
| :--- | ---: |
| Effective capacity | 531 MW |
| Effective heat rate | 7,070 Btu/kWh |
| Hot start cost | $36K |
| VOM | $2.50/MWh |
| Current EOH | 24,000 |
| Next CI threshold | 32,000 EOH |

Hourly market shape:

| Period | Power price | Dispatch result |
| :--- | ---: | :--- |
| 00:00-08:00 | $25/MWh | Stay offline. |
| 08:00-14:00 | $42/MWh | Still marginal, stay offline. |
| 14:00-22:00 | $75/MWh | Start and run. |
| 22:00-24:00 | $30/MWh | Shut down after run. |

Daily dispatch summary:

| Output | Value |
| :--- | ---: |
| Fired hours | 8 |
| Start type | Hot |
| Approximate average output | 500 MW |
| MWh generated | 4,000 MWh |
| EOH added | 58 EOH |

The EOH comes from:

```text
EOH = 8 fired hours + 50 hot-start EOH
EOH = 58
```

End-of-day state:

| State item | New value |
| :--- | ---: |
| EOH | 24,058 |
| CI headroom | 7,942 EOH |
| Fouling | Slightly higher |
| Heat rate | Slightly worse |
| Tomorrow's dispatch | Uses updated state |

That is the daily loop in one example.

## Dispatch Modes A, B, And C

The framework runs the simulation under three dispatch modes. The modes are not different weather or price paths. They are different operating strategies applied to the same kind of market/climate uncertainty.

| Mode | Start-cost / EOH behavior | Dispatch behavior | Investor interpretation |
| :--- | :--- | :--- | :--- |
| A: Maximize dispatch | No EOH proximity penalty. | Runs whenever energy margin is positive. | Highest gross revenue, fastest EOH accumulation. |
| B: Balanced | Wear cost rises near threshold, up to 2.5x close to CI/MI. | Self-curtails on marginal days near thresholds. | Middle path between revenue and maintenance risk. |
| C: Minimize LTSA cost | Wear cost rises more aggressively, up to 4.0x. | Runs only on high-margin days near thresholds. | Lower revenue, slower EOH accumulation. |

ASCII view:

```text
Aggressive dispatch                                      Conservative dispatch

Mode A -------------------- Mode B -------------------- Mode C
more run hours              balanced                    fewer marginal starts
more EOH                    moderate EOH                lower EOH
earlier inspections          delayed inspections         latest inspections
```

## Why Feedback Matters

Without feedback, dispatch would treat the plant as if it had the same capacity, heat rate, and start costs every day.

That would miss a key economic reality:

```text
Running today changes the plant.
The changed plant affects tomorrow's dispatch.
```

Feedback captures this:

```text
More dispatch
  -> more fired hours and starts
  -> more EOH and degradation
  -> higher heat rate and start-cost penalty
  -> fewer marginal future runs
```

This is why the framework says no explicit simultaneous solver is needed. The model solves the problem sequentially:

```text
Day 1 state -> Day 1 dispatch -> Day 1 update
Day 2 state -> Day 2 dispatch -> Day 2 update
...
```

Each day carries the consequences of prior days.

## Forced Outage Timing In The Daily Loop

The framework says the forced outage check occurs before executing the dispatch schedule.

Beginner interpretation:

```text
Before asking "should the plant run today?"
first ask "is the plant available today?"
```

If a forced outage is triggered, the unit is unavailable for that day regardless of what the hourly price signal says.

```text
High price day
  |
  v
Forced outage triggered?
  |
  +-- yes -> no dispatch, record outage cost/duration
  |
  +-- no  -> dispatch model can run if economics work
```

This matters because a high-price day does not create revenue if the plant is unavailable.

## Prototype Vs Full Framework

The framework distinguishes the target architecture from the prototype.

| Version | Dispatch feedback behavior |
| :--- | :--- |
| Target framework | Dispatch re-optimizes each day using yesterday's updated plant state. |
| Initial prototype | Uses pre-computed static dispatch schedules; full feedback loop comes later. |

This distinction is important when reading results. If the prototype uses static dispatch, it can still process degradation from a schedule, but it does not yet let degradation reshape the next day's schedule dynamically.

Simple difference:

```text
Prototype:
  fixed schedule -> engineering update -> outputs

Full framework:
  updated plant state -> new dispatch decision -> engineering update -> feedback
```

## How Dispatch Captures Flexibility Value

Gas plants have value because they can respond to changing prices. The framework calls this plant optionality or extrinsic value.

In simple terms:

```text
If prices are low:
  stay idle

If prices are high enough:
  start or increase output

If prices are high but start/wear costs are too high:
  stay idle or wait for a better opportunity
```

Across many simulated price and weather paths, this creates a distribution of outcomes. The value is not just the average spark spread. It is the ability to capture good hours while avoiding bad hours, subject to physical and contractual constraints.

## What The Framework Includes

The high-level framework includes these dispatch-loop ideas:

- The model uses 1,000 correlated simulation paths in the target framework.
- Hourly power prices and hourly temperature feed dispatch economics.
- Daily gas price feeds fuel cost.
- The engineering model updates plant state daily.
- Effective capacity, heat rate, start costs, and VOM feed back to dispatch.
- Forced outage checks occur before executing the dispatch schedule.
- Modes A/B/C test different operating strategies.
- The initial prototype has static dispatch schedules, while full dynamic feedback is a later build phase.

## What The Framework Leaves Out

The high-level framework does not specify every dispatch implementation detail.

| Missing detail | Why it matters |
| :--- | :--- |
| Exact unit commitment algorithm | Determines how starts, min run, and min down constraints are optimized. |
| Forecast horizon used by dispatch | Operators may optimize over one day, several days, or rolling windows. |
| Perfect vs imperfect foresight | Real operators do not know future prices perfectly. |
| Treatment of ancillary services | Reserves and regulation can change dispatch value. |
| Detailed 1x1 vs 2x1 logic | Partial operation can materially affect costs and flexibility. |
| Startup/shutdown ramp energy | Start-to-full-load time affects revenue and fuel burn. |
| Minimum run and down-time implementation | Can force the plant to run through weak-price hours. |
| How static prototype schedules were generated | Needed to interpret prototype results. |

These are not problems for a learning guide. They are the next level of detail needed before turning the framework into production-grade dispatch software.

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Sections 1-2 | Five-stage architecture and daily feedback design. | Green for framework design. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.3 | Daily time-stepping inputs, outputs, and forced-outage timing. | Green for model architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.4 | Dispatch modes A/B/C and prototype vs full feedback distinction. | Green for model design. |
| `docs/InfraSure_ModelingFramework_V2.md`, Sections 4.3-4.6 | Operating constraints, start costs, VOM, and part-load heat rate. | Amber until validated against asset data. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Pipeline diagram, dispatch-to-damage flow, and daily-loop framing. | Green for communication. |
| Timera Energy power methodology / dispatch-cost articles | General support for stochastic asset dispatch and plant optionality framing. | Green for market-methodology context, not asset-specific values. |

## Open Questions Before Investment Use

Before relying on dispatch outputs for final investment use, resolve these:

| Question | Why it matters |
| :--- | :--- |
| Does dispatch optimize one day at a time or over a rolling multi-day horizon? | Multi-day foresight changes start/stop decisions. |
| Does the model assume perfect foresight of hourly prices? | Perfect foresight can overstate dispatch value. |
| Are ancillary service revenues included or excluded? | Could materially change flexible plant value. |
| How is 1x1 operation modeled against 2x1 operation? | Important for partial-load economics and start costs. |
| How are start ramps and shutdown ramps represented? | Affects MWh, fuel burn, and starts. |
| Are min run and min down constraints hard constraints? | They can force uneconomic hours after a start. |
| How exactly are load swings counted from hourly dispatch? | Affects EOH and fatigue damage. |
| When will the prototype connect full dynamic dispatch feedback? | Needed to interpret current results vs target architecture. |

## Quick Recap

Dispatch is hourly. The engineering state update is daily.

For this model:

```text
Hourly prices and weather drive dispatch.
Daily summaries update plant condition.
Updated condition changes tomorrow's dispatch.
Modes A/B/C test operating strategy.
The target framework is dynamic; the prototype may still use static schedules.
```

This guide is the bridge between the first four basics guides and the degradation guides. Capacity, heat rate, EOH, start costs, and VOM all become meaningful because Step 2 dispatch uses them to decide how the plant actually runs.
