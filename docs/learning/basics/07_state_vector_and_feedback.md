# State Vector And Feedback

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

Read these first if dispatch, EOH, start costs, or outages are new:

- [EOH And Starts](./03_eoh_and_starts.md)
- [Start Costs And VOM](./04_start_costs_and_vom.md)
- [Dispatch And The Daily Loop](./05_dispatch_and_daily_loop.md)
- [Outages, Availability, And LTSA](./06_outages_availability_and_ltsa.md)

> Plant-Type Note
> The state-vector idea is universal, but the schema changes by plant type. A simple-cycle GT does not need HRSG/ST cycling state. A CCGT may need GT-A, GT-B, HRSG, ST, cooling, and block-level state. A CHP plant may also need steam/heat obligation state.

## First-Time Reader Map

If this topic is new, ignore the word "vector" for a minute. Start with the simple memory problem:

```text
Yesterday the plant ran, started, fouled, aged, or maybe had an outage.
Tomorrow's model needs to remember that.
The state vector is how the model remembers.
```

The guide uses several terms that are easy to make too abstract:

| Term | First-time meaning |
| :--- | :--- |
| State | The current condition of the plant at a point in time. |
| Variable | One named item the model tracks, such as EOH or heat rate. |
| State vector | A structured list of state variables carried from one day to the next. |
| Opening state | Plant condition at the start of a day. |
| Closing state | Plant condition after that day's dispatch and engineering update. |
| Feedback | The closing state from one day becomes an input to the next day. |
| State update | The calculation that turns opening state plus today's operation into closing state. |
| State schema | The exact list and names of variables the code stores. |
| Reset | A maintenance event that partly or fully restores a state variable. |
| Path state | The state history for one simulated future path. |

The mental stack is:

```text
remember plant condition -> make dispatch decision -> update condition -> remember new condition
```

## A Simple Memory Analogy

Think of a notebook kept by the model.

At the start of the day, the notebook says:

```text
EOH = 24,000
heat rate = 7,070 Btu/kWh
capacity = 531 MW
outage status = available
compressor fouling = 0.0%
```

The plant runs during the day. At the end of the day, the model writes a new note:

```text
EOH = 24,058
heat rate = slightly worse
capacity = still 531 MW before tomorrow's weather adjustment
outage status = available
compressor fouling = slightly higher
```

Tomorrow, the dispatch model reads the new note, not the old one.

That is the core idea:

```text
No memory  -> every day starts as if the plant is fresh.
With memory -> every day starts from the plant's actual modeled condition.
```

## Why A Vector?

The word "vector" just means the model stores many state variables together.

Tiny example:

```text
state = [
  EOH,
  heat_rate,
  capacity,
  fouling,
  outage_status
]
```

The real framework has more variables, but the idea is the same. It is a structured bundle of remembered plant condition.

For a first-time reader:

```text
state vector = model memory bundle
```

## How One Day Changes State

One dispatch day changes multiple state variables.

```text
opening state
  |
  +--> dispatch decides run/start/shutdown
  |
  +--> fired hours and starts are counted
  |
  +--> EOH increases
  |
  +--> fouling and degradation may increase
  |
  +--> outage risk may change
  |
  +--> inspection headroom changes
  |
  v
closing state
```

Simple before/after table:

| Variable | Opening state | Today's operation | Closing state |
| :--- | :--- | :--- | :--- |
| EOH | 24,000 | 8 fired hours + 1 hot start | 24,058 |
| CI headroom | 8,000 EOH | 58 EOH consumed | 7,942 EOH |
| Heat rate | 7,070 Btu/kWh | Operation adds small degradation | Slightly worse |
| Fouling | 0.0% | Fired hours add fouling | Slightly higher |
| Outage status | Available | No forced outage triggered | Available |

The exact numbers depend on the detailed model logic. The learning point is that state moves forward, day by day.

## What State Is Not

It helps to separate state from inputs and outputs.

| Category | Example | Does the model remember it as state? |
| :--- | :--- | :--- |
| Market input | Hourly power price tomorrow | No. It is an external input for dispatch. |
| Weather input | Hourly temperature tomorrow | No. It is an external input, although it affects capacity and heat rate. |
| Plant state | Current EOH | Yes. It carries forward. |
| Plant state | Compressor fouling | Yes. It carries forward until wash or reset. |
| Dispatch output | MWh generated today | Usually output, then summarized into state changes. |
| Financial output | EBITDA for the month | Output, not physical plant state. |

The state vector is not everything in the model. It is the remembered plant condition needed for future days.

## Plant-Type Variations

The same modeling pattern applies across plant types:

```text
opening state + today's operation -> closing state -> tomorrow's dispatch
```

But the list of state variables should change with the equipment and operating role.

| Plant type | Core state examples | Extra state likely needed |
| :--- | :--- | :--- |
| Simple-cycle GT | EOH, starts, heat rate, capacity, fouling, outage status. | GT-only start class, Pmin/Pmax, ramp capability, emissions limits. |
| Combined-cycle GT | GT state plus HRSG/ST cycling, 1x1/2x1 mode, steam-side outage state. | Separate GT-A/GT-B and HRSG train histories. |
| Frame GT | GT hot-section and rotor state. | Longer start/cooldown memory and inspection outage planning. |
| Aeroderivative GT | Module hours, starts, package condition, outage status. | Module-swap maintenance state and faster-start operating modes. |
| CHP / cogeneration | Power state plus steam/heat-service state. | Steam demand, host contract state, heat-delivery reliability, backup boiler state. |

Do not use one Athens 2x1 CCGT state schema for every future gas plant.

## Why This Matters

The state vector answers a simple question:

> What does the model remember about the plant from one day to the next?

Without a state vector, every day would look independent. The dispatch model would treat the plant as if yesterday never happened. That would miss the core idea of the InfraSure framework:

```text
Operation today changes plant condition.
Plant condition tomorrow changes dispatch economics.
```

The state vector is the model's memory. It carries the plant's current condition through the daily simulation.

## Plain-English Concept

A state vector is just a structured list of the plant's current condition.

In plain language:

```text
State vector = everything the model needs to remember before tomorrow starts
```

Examples:

- current EOH
- current heat rate
- current capacity
- compressor fouling
- outage status
- distance to next inspection
- start-cost multipliers
- creep and fatigue damage
- HRSG cycling damage
- TBC life state
- rotor life state

The dispatch model does not need every engineering detail. It needs the pieces that affect tomorrow's economics and availability.

## The Daily Feedback Loop

The framework's daily loop can be read as:

```text
Read state
  |
  v
Run today's dispatch
  |
  v
Update engineering and contract state
  |
  v
Write tomorrow's state
```

Expanded:

```text
Start of Day D
  |
  v
State from Day D-1:
  EOH, capacity, heat rate, fouling, outage status, start costs
  |
  v
Step 2 dispatch:
  hourly prices, hourly weather, daily gas price, constraints
  |
  v
Operating profile:
  fired hours, starts, load profile, MWh, trips, swings
  |
  v
Engineering update:
  EOH, degradation, stress, outage risk, inspection proximity
  |
  v
State for Day D+1
```

That is feedback. The output of one day becomes an input to the next day.

## Why This Is Different From A Static Model

A static model might assume:

```text
Capacity = 531 MW every day
Heat rate = 7,070 Btu/kWh every day
Start cost = $36K every hot start
Forced outage rate = fixed percentage
```

The InfraSure framework instead updates state:

```text
Capacity changes with temperature and degradation.
Heat rate changes with ambient conditions, load, and fouling.
Start costs change as EOH thresholds approach.
Forced outage risk changes with stress state.
```

This is why the model is called a simplified digital twin. It is not an OEM-grade physics model, but it does carry a living representation of plant condition.

## What Is In The State Vector

The framework's initial state table includes these variables:

| State variable | Initial value | Why it matters |
| :--- | ---: | :--- |
| Contractual EOH, GT-A | 24,000 | Tracks inspection timing for GT-A. |
| Contractual EOH, GT-B | 24,000 | Tracks inspection timing for GT-B. |
| Next inspection threshold | 32,000 EOH | Defines current CI headroom. |
| Creep damage fraction | 0.0 | Tracks time-at-temperature damage. |
| Fatigue damage fraction | 0.0 | Tracks cycling damage. |
| Interaction damage | 0.0 | Tracks coupled creep-fatigue risk. |
| HR at ISO | 7,070 Btu/kWh | Baseline fuel intensity. |
| Recoverable HR degradation | 0.0% | Tracks degradation since HGP reset. |
| Compressor fouling index | 0.0% | Tracks recoverable compressor loss. |
| Compressor erosion | +1.8% HR penalty | Tracks non-recoverable age-related loss. |
| TBC time-at-temperature | 0.0 hours | Tracks coating life exposure. |
| TBC Weibull threshold | Sampled per path | Makes coating failure timing path-specific. |
| HRSG drum cycle count | 0.0 | Tracks steam-side cycling in current interval. |
| HRSG drum fatigue life | About 0.30 | Captures pre-existing HRSG life consumption. |
| Rotor life consumed | About 0.35 | Captures long-term rotor tail risk. |
| Hours since last shutdown | 720+ hours | Helps classify next start as hot, warm, or cold. |

For learning, group those into simpler buckets:

| Bucket | Examples | Used by |
| :--- | :--- | :--- |
| Dispatch economics | capacity, heat rate, start costs, VOM | Step 2 dispatch |
| Contract state | EOH, next threshold, start counts | LTSA and dispatch modes |
| Degradation state | fouling, erosion, HGP wear | Engineering and dispatch |
| Damage state | creep, fatigue, TBC, HRSG, rotor | Forced outage and maintenance |
| Availability state | planned outage, forced outage, duration remaining | Dispatch and finance |

## What Gets Fed Back To Dispatch

The framework explicitly feeds these outputs back to the dispatch model:

| Feedback item | Meaning | Dispatch impact |
| :--- | :--- | :--- |
| Effective capacity | Current MW limit. | Caps hourly generation and revenue opportunity. |
| Effective heat rate | Current fuel intensity. | Converts gas price into fuel cost. |
| Start costs by type | Current hot/warm/cold/trip start hurdle. | Determines whether starts are economic. |
| VOM | Current non-fuel variable cost. | Raises or lowers marginal dispatch cost. |

Those four items are the daily bridge from engineering state to market behavior.

```text
Engineering state
  |
  +--> effective capacity
  +--> effective heat rate
  +--> start costs
  +--> VOM
  |
  v
Tomorrow's dispatch economics
```

## Example: One Day Of Feedback

Start of Day 1:

| State item | Value |
| :--- | ---: |
| EOH | 24,000 |
| CI threshold | 32,000 |
| ISO heat rate | 7,070 Btu/kWh |
| Effective capacity | 531 MW |
| Compressor fouling | 0.0% |
| Hot start cost | $36K |

Day 1 dispatch result:

| Operating result | Value |
| :--- | ---: |
| Fired hours | 8 |
| Start type | Hot |
| Average output | 500 MW |
| MWh | 4,000 |
| Large load swings | 0 |

Daily update:

```text
EOH added = 8 fired hours + 50 hot-start EOH
EOH added = 58

New EOH = 24,000 + 58
New EOH = 24,058
```

End of Day 1 state:

| State item | New value | Why it matters tomorrow |
| :--- | ---: | :--- |
| EOH | 24,058 | Slightly closer to CI. |
| CI headroom | 7,942 EOH | Still far from threshold. |
| Fouling | Slightly higher | Heat rate may be slightly worse. |
| Heat rate | Slightly worse | Fuel cost may be slightly higher. |
| Hot start cost | Same or slightly adjusted | Depends on mode and EOH proximity. |

Tomorrow's dispatch sees the updated plant, not the original plant.

## Example: Feedback Near An Inspection Threshold

Feedback becomes more visible near a threshold.

Start of a later day:

| State item | Value |
| :--- | ---: |
| EOH | 31,300 |
| CI threshold | 32,000 |
| CI headroom | 700 EOH |
| Base hot start cost | $36K |
| GT wear component of hot start | $15K |

Mode B may apply a higher wear multiplier near the threshold:

```text
Adjusted GT wear = $15K * 2.5
Adjusted GT wear = $37.5K

Adjusted hot start cost = fuel + adjusted wear + aux + HRSG/ST
Adjusted hot start cost = $12K + $37.5K + $3K + $6K
Adjusted hot start cost = $58.5K
```

Mode C may apply an even higher multiplier:

```text
Adjusted GT wear = $15K * 4.0
Adjusted GT wear = $60K

Adjusted hot start cost = $12K + $60K + $3K + $6K
Adjusted hot start cost = $81K
```

Same plant. Same hot start. Different state and mode. Different dispatch economics.

## State By Timescale

Not every state variable moves at the same speed.

| Timescale | State variables | Example |
| :--- | :--- | :--- |
| Hourly input | temperature, price, load profile | Hot afternoon reduces capacity. |
| Daily update | EOH, fouling, outage risk, start classification | One hot start adds 50 EOH. |
| Inspection interval | HGP wear, CI/HGP/MI resets, reserve true-up | HGP partially resets degradation. |
| Long-term state | erosion, rotor life, HRSG fatigue history | 22 years of service create residual risk. |

The daily loop is the organizing rhythm, but the state vector contains both short-term and long-term memory.

## State And Simulation Paths

The framework runs many correlated simulation paths. Each path gets its own state trajectory.

```text
Path 001:
  hot summer, high prices, more dispatch, faster EOH growth

Path 002:
  mild weather, weaker prices, less dispatch, slower EOH growth

Path 003:
  TBC threshold reached earlier, forced outage occurs
```

The engineering model does not generate the market and climate paths. It processes each path and updates the plant state day by day.

This is why outputs are distributions rather than one number:

```text
Different paths -> different state histories -> different cashflows
```

## State And Forced Outages

Forced outage probability depends on state.

Examples:

| State variable | Outage connection |
| :--- | :--- |
| Combustion fatigue | Raises GT forced outage risk as fatigue budget is consumed. |
| TBC time-at-temperature | Can trigger path-specific coating failure. |
| Rotor life fraction | Adds low-probability tail risk. |
| HRSG drum cycles | Raises HRSG outage risk. |
| Background age multiplier | Raises unmodeled BOP/control risk over time. |

Forced outage check happens before dispatch. That means state can block revenue even when market prices are high.

```text
Stress state high
  |
  v
Forced outage triggered
  |
  v
Plant unavailable
  |
  v
No dispatch revenue during outage
```

## What The Framework Includes

The high-level framework includes these state-vector and feedback ideas:

- The digital twin carries a state vector.
- The state vector is updated at the end of each simulated day.
- The updated state is carried into the next day.
- Dispatch receives effective capacity, heat rate, start costs, and VOM from the prior day's engineering output.
- Forced outage checks use the current stress state.
- Creep and fatigue are coupled, not independent.
- Compressor fouling uses non-linear accumulation and daily air-quality scaling.
- TBC failure is path-specific through Weibull threshold sampling.
- HRSG drum cycles and rotor life are tracked separately.
- The framework clarified that Monte Carlo paths are generated upstream and processed by the engineering model.

## What The Framework Leaves Out

The framework describes the state vector concept well, but implementation details still need to be specified for production use.

| Missing detail | Why it matters |
| :--- | :--- |
| Exact state schema | Needed to implement clean code and avoid inconsistent variable names. |
| Unit-level vs plant-level state | A 2x1 plant may need separate GT-A, GT-B, HRSG, and plant-block state. |
| Reset rules at each inspection | Determines how much degradation and damage is recovered. |
| State update order | Forced outage, dispatch, degradation, and inspection checks must occur consistently. |
| Persistence format | Needed for saving and auditing path/day state histories. |
| Random seed and sampled thresholds | Required for reproducible stochastic results. |
| Treatment of missing data | Needed if a path lacks hourly temperature, AQI, or dispatch information. |
| Calibration hooks | Needed to update state assumptions with plant historian or inspection data. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.1 | Digital twin carries a state vector updated daily. | Green for model architecture. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.3 | Inputs, outputs, and feedback to dispatch. | Green for daily-loop design. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.8 | Initial state vector for the Athens-type plant. | Amber because several values are assumptions. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 5.2 corrections | Clarifies feedback and upstream path generation. | Green for framework intent. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Pipeline, dispatch-to-damage flow, and daily state-update diagram. | Green for communication. |

## Open Questions Before Investment Use

Before relying on state-vector outputs in a final investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| What is the exact state schema used in code? | Avoids ambiguity between docs and implementation. |
| Which variables are tracked per GT vs plant-level? | Prevents double-counting or averaging away unit-specific risk. |
| What resets at CI, HGP, and MI? | Determines post-inspection performance and risk. |
| How are sampled stochastic thresholds stored? | Required for reproducibility and auditability. |
| What is the update order inside each day? | Changes results if outage, dispatch, degradation, and inspections are ordered differently. |
| How are missing or bad hourly inputs handled? | Prevents silent path corruption. |
| How will historian or inspection data override assumptions? | Needed for asset-specific calibration. |
| How much state history should be retained for review? | Important for explaining P10/P50/P90 outcomes. |

## Quick Recap

The state vector is the model's memory. It carries plant condition from one day to the next.

For this model:

```text
State from yesterday drives today's dispatch.
Today's dispatch creates operating stress.
Operating stress updates state.
Updated state changes tomorrow's economics and outage risk.
```

This final basics guide connects the earlier basics:

```text
Capacity -> MW limit in state
Heat rate -> fuel cost in state
EOH -> inspection proximity in state
Start costs and VOM -> dispatch hurdle in state
Outages and LTSA -> availability and cost classification in state
```

With this foundation, the next docs can move into the detailed degradation factors one by one.
