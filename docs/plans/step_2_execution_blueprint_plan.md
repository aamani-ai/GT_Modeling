# Step 2 Execution Blueprint Plan

## Purpose

This plan defines how to turn the gas turbine framework and learning notes into the second-stage execution blueprint.

The current docs explain the concepts:

- gas plant anatomy
- plant-type differences
- capacity and heat rate
- EOH and starts
- start costs and VOM
- dispatch and the daily loop
- outages, availability, and LTSA terms
- degradation and forced outage drivers
- operating range through Pmin and Pmax
- marginal cost and offer curves
- historical calibration versus forecast inputs
- weather-adjusted operating curves
- combined-cycle plant-type execution details
- state vector and recursive plant-state feedback

The next step is different. Step 2 is about making the dispatch and operating-economics layer precise enough that the model can eventually be implemented, tested, and defended.

This plan should be used before creating the detailed Step 2 docs.

Upstream dependency: Step 2 assumes the exogenous scenario package defined in [Step 1 Climate And Price Scenario Plan](step_1_climate_price_scenario_plan.md). Step 2 consumes those hourly weather, power-price, gas-price, optional ancillary-price, and scenario-metadata paths. It should not silently create its own market and climate paths inside the dispatch layer.

## What Step 2 Means

Step 2 is the operating decision layer.

It answers:

```text
Given today's plant state,
given hourly power prices,
given gas price,
given weather,
given plant constraints,

how should the plant run today?
```

It is not only a finance layer and not only an engineering layer. It sits between them.

```text
today's market and weather paths
        +
opening plant state from yesterday
        |
        v
Step 2 dispatch and operating economics
        |
        v
hourly operating profile
        |
        v
Step 3 engineering state update
        |
        v
Step 4 maintenance / outage / LTSA update
        |
        v
closing plant state
        |
        v
tomorrow's Step 2 input
```

## Recursive Plant-State Input

The most important correction is that Step 2 does not only receive external inputs like power prices, gas prices, and weather.

Step 2 also receives the current plant condition.

That current condition is not static. It is the closing state created by prior engineering, maintenance, outage, and LTSA updates.

```text
Yesterday's Step 2 dispatch
  -> Step 3 degradation and performance update
  -> Step 4 outage, maintenance, and contract update
  -> today's opening plant state
  -> today's Step 2 dispatch
```

So Steps 3 and 4 are not only downstream reporting steps. They are recursive state producers for the next Step 2 decision.

Opening plant state should include at least:

| State input to Step 2 | Why it changes dispatch |
| :--- | :--- |
| Effective capacity | Caps hourly MW and revenue opportunity. |
| Effective heat rate | Changes fuel cost and spark spread. |
| Current Pmin/Pmax by mode | Defines feasible operating range. |
| Outage or derate status | Blocks dispatch or reduces capability. |
| EOH and inspection headroom | Changes wear cost, start-cost multipliers, and outage timing. |
| Compressor fouling / erosion state | Changes heat rate and capacity. |
| Start costs by type | Changes the hurdle for cycling. |
| VOM and LTSA cost state | Changes variable dispatch economics and cashflow. |
| Start counts and overage headroom | Changes contract exposure from additional starts. |
| Train-level state for CCGTs | Determines whether 1x1, 2x1, or partial operation is feasible. |

This means the Step 2 input package has two different kinds of inputs:

| Input type | Examples | Source |
| :--- | :--- | :--- |
| Exogenous path inputs | Hourly power prices, gas prices, weather, AQI, market scenario tags. | Step 1 climate and price scenario package. |
| Recursive state inputs | Degraded capacity, degraded heat rate, outage state, EOH headroom, start-cost multipliers, LTSA counters. | Yesterday's Step 3/4 closing state. |

If the implementation misses the recursive state input, the model becomes a static dispatch model with after-the-fact degradation accounting. That is not the target InfraSure idea.

## Core Mental Model

The most important modeling rule is:

```text
hourly economics inside the day
opening plant state before dispatch
daily plant-state update after the day
monthly and annual contract / finance rollups
```

The model should not force every variable into one frequency.

| Layer | Natural frequency | Why this frequency fits |
| :--- | :--- | :--- |
| Power prices | Hourly | Dispatch value depends on hourly price shape, high-price windows, and low-price hours to avoid. |
| Ambient temperature | Hourly | Capacity and heat rate can change materially within the day. |
| Dispatch commitment and MW | Hourly or sub-hourly simplified to hourly | The model needs starts, shutdowns, Pmin, Pmax, and hourly generation. |
| Starts, trips, shutdown duration | Event-level, summarized daily | A start is an event, but EOH and fatigue can be updated at the daily checkpoint. |
| Gas price | Daily or monthly, depending source | Daily is better for dispatch; monthly may be acceptable for long-range forecast simplification. |
| Opening plant state | Daily input to Step 2 | Yesterday's closing state tells dispatch today's capacity, heat rate, outage status, start costs, and EOH proximity. |
| Engineering state update | Daily checkpoint after dispatch | EOH, fouling, degradation, outage risk, and inspection headroom update cleanly once per day. |
| Planned outage and forced outage status | Event-level with daily state | The model needs to know whether the plant is available before dispatch. |
| LTSA fixed fees and reserves | Monthly or contract-period | Billing and accrual timing is usually contractual. |
| Availability guarantees | Annual or contract-year | Guarantees are usually measured across a defined period, not one hour. |
| Investor outputs | Monthly, annual, multi-year path | P50, P90, EBITDA, DSCR, and downside metrics need rollups. |

## Whole Step 2 Workflow

The Step 2 execution blueprint should be organized around one full input-process-output loop.

The short version:

```text
exogenous path inputs + recursive opening plant state
  -> availability gate
  -> hourly dispatch decision
  -> operating profile
  -> Step 3/4 daily state update
  -> contract and cashflow rollup
  -> closing plant state for tomorrow
  -> validation and calibration feedback
```

The detailed version:

```text
                         STEP 2 EXECUTION WORKFLOW

  +------------------------------------------------------------------------+
  | 0. STATIC SETUP                                                        |
  |                                                                        |
  | Plant specs                                                            |
  |   - configuration: simple-cycle, 1x1 CCGT, 2x1 CCGT, CHP, etc.         |
  |   - Pmax / Pmin curves                                                 |
  |   - heat-rate curves                                                   |
  |   - start fuel, start time, ramp, min up/down constraints              |
  |   - emissions, fuel, cooling, and operating limits                     |
  |                                                                        |
  | Contract specs                                                         |
  |   - LTSA / CSA fixed fees                                              |
  |   - EOH reserve rates                                                  |
  |   - start limits and overage charges                                   |
  |   - inspection thresholds                                              |
  |   - availability and heat-rate guarantees                              |
  |                                                                        |
  | Initial state                                                          |
  |   - EOH by GT / train                                                  |
  |   - starts by type                                                     |
  |   - degradation indices                                                |
  |   - outage status                                                      |
  |   - distance to next inspection                                        |
  |   - opening heat-rate and capacity state                               |
  |   - LTSA / CSA counters and reserve state                              |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 1. SCENARIO / PATH INPUTS                                              |
  |                                                                        |
  | For each simulation path:                                              |
  |   - hourly power prices                                                |
  |   - daily or hourly gas price                                          |
  |   - hourly weather                                                     |
  |   - optional ancillary-service prices                                  |
  |   - planned outage schedule                                            |
  |   - stochastic forced-outage draws or hazard inputs                    |
  |   - forward-curve / market scenario tags                               |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 2. DAILY OPENING STATE                                                 |
  |                                                                        |
  | At the start of day D, read yesterday's closing state:                 |
  |   - available or unavailable                                           |
  |   - current Pmax / Pmin state                                          |
  |   - current heat-rate state                                            |
  |   - EOH and start-count state                                          |
  |   - fouling, erosion, rotor, TBC, HRSG, and fatigue states             |
  |   - inspection headroom                                                |
  |   - LTSA / CSA period counters                                         |
  |                                                                        |
  | This is the recursive input from prior Step 3/4 updates. It sits       |
  | beside today's market and weather inputs before dispatch is solved.    |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 3. AVAILABILITY GATE                                                   |
  |                                                                        |
  | Is the plant physically available today?                               |
  |                                                                        |
  |   planned outage?                                                      |
  |      yes -> no dispatch, record planned outage day                     |
  |      no  -> continue                                                   |
  |                                                                        |
  |   forced outage active?                                                |
  |      yes -> no dispatch or partial derate, record outage day           |
  |      no  -> continue                                                   |
  |                                                                        |
  |   derate active?                                                       |
  |      yes -> reduce feasible Pmax                                       |
  |      no  -> use normal feasible Pmax                                   |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 4. HOURLY OPERATING CAPABILITY                                         |
  |                                                                        |
  | For each hour h in day D:                                              |
  |   - compute ambient Pmax(h)                                            |
  |   - compute ambient heat rate(h)                                       |
  |   - apply degradation multipliers                                      |
  |   - apply current outage / derate limits                               |
  |   - define feasible operating modes                                    |
  |                                                                        |
  | Example modes for Athens-type 2x1 CCGT:                                |
  |   - offline                                                            |
  |   - 1x1 operation                                                      |
  |   - 2x1 operation                                                      |
  |   - partial-load operation                                             |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 5. HOURLY DISPATCH / COMMITMENT DECISION                               |
  |                                                                        |
  | Choose commitment and generation for each hour, subject to constraints. |
  |                                                                        |
  | Dispatch economics compare:                                            |
  |   expected power revenue                                               |
  |     minus fuel cost                                                    |
  |     minus VOM                                                          |
  |     minus start cost recovery                                          |
  |     minus wear / EOH penalty if modeled                                |
  |     minus emissions or fuel constraints if modeled                     |
  |                                                                        |
  | Key constraints:                                                       |
  |   - Pmin / Pmax                                                        |
  |   - ramp limits                                                        |
  |   - min up / min down                                                  |
  |   - start time                                                         |
  |   - 1x1 vs 2x1 mode feasibility                                        |
  |   - heat-rate curve                                                    |
  |   - fuel availability                                                  |
  |   - planned outage or derate limits                                    |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 6. HOURLY OPERATING PROFILE OUTPUT                                     |
  |                                                                        |
  | Step 2 should produce an hourly profile:                               |
  |   - online / offline flag                                              |
  |   - operating mode                                                     |
  |   - MW generated                                                       |
  |   - MWh by hour                                                        |
  |   - fuel burn                                                          |
  |   - gross margin                                                       |
  |   - starts and shutdowns                                               |
  |   - load swings and ramps                                              |
  |   - curtailment or unavailable MW                                      |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 7. DAILY SUMMARY / STATE HANDOFF                                       |
  |                                                                        |
  | Compress the hourly profile into daily model signals:                  |
  |   - fired hours                                                        |
  |   - MWh generated                                                      |
  |   - fuel burned                                                        |
  |   - hot / warm / cold starts                                           |
  |   - trips or failed starts                                             |
  |   - load-swing count and ramp severity                                 |
  |   - equivalent operating hours added                                   |
  |   - compressor fouling increment                                       |
  |   - heat-rate degradation increment                                    |
  |   - capacity degradation increment                                     |
  |   - HRSG cycling damage                                                |
  |   - TBC / rotor / creep-fatigue damage indices                         |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 8. DAILY CLOSING STATE UPDATE                                          |
  |                                                                        |
  | Update the state carried into tomorrow:                                |
  |   - EOH by GT / train                                                  |
  |   - start counts by type                                               |
  |   - degradation indices                                                |
  |   - inspection headroom                                                |
  |   - outage hazard inputs                                               |
  |   - current availability / derate status                               |
  |   - wash / inspection / maintenance status                             |
  |   - LTSA / CSA counters                                                |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 9. CONTRACT AND CASHFLOW ROLLUP                                        |
  |                                                                        |
  | Convert operations into money and contract metrics:                    |
  |   - energy revenue                                                     |
  |   - fuel cost                                                          |
  |   - VOM                                                               |
  |   - start cost                                                         |
  |   - EOH reserve accrual                                                |
  |   - LTSA fixed fees                                                    |
  |   - start overage charges                                              |
  |   - planned outage cost                                                |
  |   - forced outage cost                                                 |
  |   - availability or heat-rate guarantee exposure                       |
  |   - insurance recovery or deductible if modeled                        |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 10. PATH OUTPUTS AND VALIDATION                                        |
  |                                                                        |
  | Store outputs by hour, day, month, year, and scenario path:            |
  |   - dispatch profile                                                   |
  |   - plant-state trajectory                                             |
  |   - outage and maintenance events                                      |
  |   - revenue and cost stack                                             |
  |   - EBITDA / cashflow                                                  |
  |   - P10 / P50 / P90 investor metrics                                   |
  |                                                                        |
  | Compare against validation evidence:                                   |
  |   - historical dispatch                                                |
  |   - historical generation                                              |
  |   - historical heat rate                                               |
  |   - outage history                                                     |
  |   - GADS-style availability metrics                                    |
  |   - known LTSA / CSA invoices and events                               |
  +------------------------------------------------------------------------+
```

## Workflow By Input, Process, Output

The detailed Step 2 docs should keep this input-process-output map visible.

| Stage | Inputs | Process | Outputs |
| :--- | :--- | :--- | :--- |
| Static setup | Plant specs, contract terms, initial state | Normalize assumptions and units. | Model configuration and opening state. |
| Scenario input | Hourly power, gas, weather, outage assumptions | Read path-specific market and physical conditions. | Daily input package. |
| Daily opening state | Yesterday's closing state: capacity, heat rate, EOH, outage status, degradation, LTSA counters | Build today's recursive plant-state input package. | Step 2 state inputs before dispatch. |
| Availability gate | Planned outage, active forced outage, derates, opening state | Decide if the plant can dispatch today. | Available MW or unavailable status. |
| Capability calculation | Pmax/Pmin curves, weather, degradation state | Compute feasible hourly operating range. | Hourly Pmin, Pmax, heat-rate, mode set. |
| Dispatch decision | Prices, gas, costs, constraints, capability, opening state | Choose hourly commitment and generation. | Hourly online flag, MW, MWh, mode. |
| Operating profile | Hourly dispatch and mode sequence | Calculate fuel, margin, starts, ramps, and swings. | Hourly revenue, costs, fuel burn, start events. |
| Daily state handoff | Hourly profile | Summarize operation into engineering signals. | Daily fired hours, starts, EOH, damage increments. |
| State update | Prior state and daily signals | Step 3/4 update plant health, outage state, and contract counters. | Closing state for next day's Step 2. |
| Contract rollup | Dispatch, state, LTSA terms, outage events | Convert operations into contract cashflows. | Fees, reserves, penalties, outage costs. |
| Scenario output | Hourly, daily, monthly, annual results | Aggregate across time and simulation paths. | P10/P50/P90 metrics and diagnostics. |

## Minimum Output Set

The first implementation blueprint should require these outputs even before advanced refinements.

| Output group | Minimum fields | Why it matters |
| :--- | :--- | :--- |
| Hourly dispatch | timestamp, online flag, mode, MW, MWh, price, fuel burn, margin | Proves Step 2 is actually dispatching hourly. |
| Daily operation summary | date, fired hours, starts by type, trips, load swings, EOH added | Feeds degradation and LTSA logic. |
| Daily state | date, EOH, heat-rate state, capacity state, fouling, outage risk, inspection headroom | Shows feedback from operation to tomorrow's economics. |
| Outage log | start, end, type, cause, derate MW, covered/excluded flag | Needed for availability and LTSA analysis. |
| Monthly cashflow | revenue, fuel, VOM, start cost, LTSA fees, reserves, penalties, EBITDA | Connects operations to finance. |
| Path summary | scenario id, annual generation, availability, forced outage hours, cashflow, P50/P90 metrics | Supports investor-facing risk outputs. |
| Validation diagnostics | realized vs modeled dispatch, heat rate, capacity factor, outage rate | Prevents the model from being only internally consistent. |

## Feedback Loops To Make Explicit

Step 2 is not a one-way calculation. The valuable part of the framework is feedback.

```text
opening plant state today
    -> dispatch today
        -> starts, fired hours, load swings
            -> EOH, degradation, outage state, LTSA counters
                -> opening plant state tomorrow
                    -> tomorrow's dispatch economics
```

```text
High prices
    -> more running
        -> faster maintenance life consumption
            -> inspection or outage risk sooner
                -> lower future availability
                    -> changed cashflow distribution
```

```text
Hot weather
    -> lower Pmax and worse heat rate
        -> narrower spark spread
            -> changed dispatch decision
                -> changed EOH and degradation path
```

```text
Outage or derate
    -> lower available MW
        -> missed dispatch revenue
            -> LTSA / insurance / availability treatment
                -> investor downside metric
```

## Critical Design Decision: Price, Gas, And Generation

The core confusion to resolve before writing the detailed Step 2 files is this:

```text
Do we use historical blocks?
Do we use forward curves?
Do we forecast generation directly?
Do we simulate gas and power together?
```

The recommended answer is a hybrid:

```text
historical blocks = shape, co-movement, scarcity clusters, operating realism
forward curves    = market-consistent average level
dispatch model    = converts price + gas + plant constraints into generation
```

Do not choose "historical only" or "forwards only."

| Approach | Why tempting | Why insufficient |
| :--- | :--- | :--- |
| Historical-only | Preserves real hourly shapes and correlations. | Misses current market expectations, gas forwards, fleet buildout, and today's hedgeable level. |
| Forward-only | Uses market-consistent price levels. | Forwards are bucket averages; they do not provide hourly shape, scarcity clustering, weather co-movement, or dispatch realism. |
| Independent power/gas/generation forecasts | Looks modular and easy to explain. | Breaks the economics of gas assets; generation is endogenous to spark spread and constraints. |
| Hybrid historical + forwards + dispatch | Uses each source for what it is good at. | Requires more careful documentation and validation. This is the recommended path. |

For gas turbines, generation should not be an independent forecast input. It is an output of dispatch.

```text
power price path + gas price path + plant economics + availability
        |
        v
dispatch model
        |
        v
hourly generation
        |
        v
revenue, starts, EOH, degradation, and cashflow
```

This is the key difference from renewable assets:

| Asset type | Generation driver | Price role | Revenue construction |
| :--- | :--- | :--- | :--- |
| Solar / wind | Weather creates generation. | Price monetizes generation. | `weather -> generation`, then `generation x price`. |
| Gas turbine / CCGT | Price, gas, plant constraints, and state create dispatch. | Price is both the dispatch signal and the revenue price. | `price + gas + constraints -> generation`, then `generation x price`. |
| Storage | Price spreads and constraints create charge/discharge schedule. | Price is the optimization signal. | `price path + SOC constraints -> dispatch`, then revenue streams. |

## Gen 1 Construction: Together, Then Anchored Separately

For Gen 1, power price, gas price, and weather should be drawn from the same historical calendar block when possible. This keeps the broad co-movement intact.

Then anchor power and gas to their own forward levels.

```text
For target month M and simulation path i:

  1. Select historical analog block:
       analog = same ISO / region, same calendar month, year Y

  2. Pull together:
       hourly hub LMP from year Y
       hourly weather from year Y
       daily gas price from year Y, if available
       ancillary prices from year Y, if relevant

  3. Anchor power level:
       historical hourly LMP shape
         x target power forward level
         = forecast hourly power path

  4. Anchor gas level:
       historical gas daily shape
         + target gas forward level and basis
         = forecast delivered gas path

  5. Compute dispatch economics:
       spark spread_t = power_price_t - heat_rate_t * delivered_gas_t - VOM

  6. Run dispatch:
       spark spread path + starts + Pmin/Pmax + outage state
         = hourly MW generation

  7. Roll forward:
       generation -> starts / fired hours / EOH / state update / cashflow
```

The important nuance is:

```text
Power, gas, and weather are selected together at the analog-block level.
Power and gas are anchored separately to their own forward curves.
Generation is simulated after the anchoring step.
```

### Power Price Construction

Initial scope should use hub price first.

```text
historical hub LMP shape
        x monthly / block forward curve level
        = forecast hourly hub price
```

Then node pricing can be layered:

```text
forecast hourly node price
        = forecast hourly hub price + node_minus_hub_basis
```

| Choice | Gen 1 treatment | Later upgrade |
| :--- | :--- | :--- |
| Hub vs node | Start with liquid hub. | Add node basis once dispatch logic is stable. |
| DA vs RT | Match the settlement basis of the asset or hedge. | Add DA/RT spread model if needed. |
| On-peak / off-peak | Anchor each product bucket separately. | Move to richer block structures if vendor data supports it. |
| Ancillary prices | Include only if material to the asset. | Add joint AS-energy blocks for peakers and storage. |

Starting with hub price is not saying node basis is unimportant. It is a sequencing decision:

```text
hub forward curve = clean market anchor
node basis        = second layer
dispatch model    = third layer
```

Trying to solve node basis, gas, dispatch, and degradation all at once makes the first implementation hard to validate.

### Gas Price Construction

For gas assets, gas is not just another input. It is the cost side of the option.

```text
delivered_gas_t = Henry_Hub_forward_month
                + delivery_basis_month
                + historical_daily_shape_t
```

Where:

```text
historical_daily_shape_t = historical_gas_t - average_historical_gas_for_month
```

This additive version is usually safer for Gen 1 than pure multiplicative scaling because gas is already a price level and the key objective is to preserve daily variation around the forward average. If volatility clearly scales with gas level, Gen 2 can move to log-return or percentage-shape treatment.

| Gas component | Gen 1 treatment | Why |
| :--- | :--- | :--- |
| Henry Hub level | NYMEX / CME monthly forward | Market-consistent gas level. |
| Delivery basis | Fixed assumption or vendor/broker basis curve | Plant burns delivered gas, not Henry Hub. |
| Daily shape | Historical same-month gas deviations | Keeps intra-month gas variation without ignoring the forward. |
| Intraday gas | Usually not modeled | Hourly gas is often unnecessary for Gen 1 dispatch. |
| Basis uncertainty | Scenario or sensitivity | Delivered basis can matter materially in constrained regions. |

### Dispatch-Generated Generation

Historical generation should calibrate and validate the dispatch model. It should not be replayed as the forecast generation path for a gas turbine.

```text
Use historical generation for:
  - heat-rate curve calibration
  - Pmin / Pmax inference
  - start behavior
  - outage and availability calibration
  - dispatch-model validation

Do not use historical generation as:
  - the future hourly generation forecast after prices and gas have changed
```

The forecast generation path should come from:

```text
dispatch(power_t, gas_t, heat_rate_state, VOM, starts, Pmin, Pmax, outage_state)
```

Minimum Gen 1 dispatch output:

| Output | Why needed |
| :--- | :--- |
| Hourly online flag | Defines when the plant is committed. |
| Hourly MW / MWh | Drives energy revenue. |
| Operating mode | Needed for 1x1 vs 2x1 CCGT state tracking. |
| Starts by type | Drives EOH, start cost, and LTSA overage. |
| Fired hours | Drives degradation and EOH. |
| Fuel burn | Drives fuel cost and heat-rate validation. |
| Gross margin | Validates that dispatch is economically coherent. |

## Concrete Gen 1 Path Example

Illustrative example for one monthly path:

```text
Target:
  July 2027, ERCOT Houston hub, gas-fired asset

Analog selected:
  July 2023

Raw analog data:
  July 2023 hourly Houston hub LMP
  July 2023 hourly Houston-area weather
  July 2023 daily Henry Hub or delivered gas proxy

Market anchors:
  July 2027 Houston hub power forward = $74/MWh
  July 2027 Henry Hub gas forward     = $4.20/MMBtu
  delivery basis assumption           = -$0.15/MMBtu

Power construction:
  July 2023 hourly LMP shape
    scaled so July 2027 bucket average = $74/MWh

Gas construction:
  July 2023 daily gas deviations
    shifted so July 2027 delivered average = $4.05/MMBtu

Dispatch construction:
  for each hour:
    variable_cost_t = heat_rate_t * delivered_gas_t + VOM
    run if LMP_t clears variable cost + start / wear hurdle
    respect Pmin, Pmax, ramp, outage, and min-run constraints

Outputs:
  hourly generation
  starts and fired hours
  EOH and degradation increments
  monthly cashflow and path metrics
```

This is exactly why the first two detailed files are so important:

| File | What it must settle |
| :--- | :--- |
| `01_time_resolution_and_frequency.md` | Power is hourly with monthly anchors; gas is daily/monthly with monthly anchors; generation is hourly dispatch output; state updates daily; cashflow rolls monthly/annual. |
| `02_dispatch_problem_definition.md` | The dispatch model consumes power, gas, plant constraints, starts, and outage state; it produces generation and operating signals. |

## Gen 2 Upgrade: Out-Of-Sample And Regime Handling

Gen 1 should be deliberately simple:

```text
block sampling core
  + forward anchoring
  + simple gas anchoring
  + hub-first dispatch
  + validation against historical operation
```

Gen 2 is where the model starts addressing out-of-sample problems explicitly.

The local revenue methodology separates four different "out-of-sample" problems. Step 2 should reuse that taxonomy.

| Out-of-sample problem | Gas Step 2 version | Primary tool | Why it matters |
| :--- | :--- | :--- | :--- |
| Tail magnitude | Scarcity prices or extreme spark spreads beyond history. | EVT for single-variable tails. | Needed for P99-style stress or insurance, not core P10/P90. |
| Joint dependence | Simultaneous extreme power prices, gas prices, weather, and outage stress. | Copulas or joint-tail augmentation. | Needed for portfolio or insurance products where co-occurrence matters. |
| Regime shift | Forecast market has fleet, storage, gas, or policy state not present in history. | Structural simulation. | Needed when history is no longer representative. |
| Driver combination | Each driver is familiar, but the combination is not. | Perturbed historical. | Near-term gas forecasts often sit here: high gas plus high renewables plus tight reserve margin. |

For Step 2 gas modeling, the most important Gen 2 methods are likely:

| Method | Step 2 use | Notes |
| :--- | :--- | :--- |
| Perturbed historical | Adjust analog prices for gas, solar, storage, reserve margin, or transmission differences. | Best first Gen 2 upgrade because it stays grounded in history. |
| Empirical conditioning calibration | Learn better analog weights from held-out validation. | Replaces hand-tuned weights with measured forecast skill. |
| Residual correction per layer | Correct repeated bias in hub price, basis, gas, dispatch, or generation. | Requires realized-vs-forecast history. |
| EVT | Add deeper tail treatment for scarcity or extreme margin cases. | Useful for stress, not the first core revenue forecast. |
| Copulas | Add joint-tail behavior across assets or variables. | Use carefully; wrong copula choice can silently misstate tails. |
| Structural simulation | Handle large long-horizon regime shifts. | Gen 3-like for full production-cost modeling; Gen 2 can use vendor model outputs as proxy. |

### Gen 2 Perturbed Historical For Gas Step 2

The natural Gen 2 upgrade is not to throw away analogs. It is to adjust analogs for known driver gaps.

```text
forecast_hourly_power_t
  = forward_anchored_analog_power_t
  + gas_price_perturbation_t
  + solar_buildout_perturbation_t
  + storage_perturbation_t
  + transmission_basis_perturbation_t
  + reserve_margin_perturbation_t
```

For gas dispatch, gas perturbation has two roles:

```text
1. Delivered gas changes the plant's own variable cost.
2. System gas price changes the market-clearing LMP when gas is on the margin.
```

Those are different channels and should not be double-counted.

| Channel | Where it enters | Example |
| :--- | :--- | :--- |
| Plant fuel cost | Dispatch variable cost | Higher delivered gas makes the unit harder to dispatch. |
| Market LMP level | Power price path | Higher gas can raise LMP if gas is marginal. |
| Gas basis | Delivered gas cost and local competitiveness | Waha basis can change plant economics without moving Henry Hub equally. |
| Fuel constraint | Availability / dispatch constraint | Physical gas curtailment can limit generation even if spark spread is positive. |

Gen 2 should explicitly document which layer owns each gas effect.

```text
Power forward anchor owns:
  market-consistent power level

Gas forward anchor owns:
  market-consistent fuel level

Dispatch model owns:
  asset-specific conversion from spark spread to generation

Perturbation layer owns:
  shape changes caused by structural differences not captured by flat anchoring
```

### Gen 2 Validation Requirements

The Gen 2 upgrade should not be accepted because it sounds more sophisticated. It should be accepted only if it validates.

| Validation test | What it checks |
| :--- | :--- |
| Backcast July 2024 from July 2020 analogs | Whether perturbations can reproduce a known regime change. |
| Hub price level error | Whether forward anchoring is preserving monthly averages. |
| Hourly shape error | Whether perturbations improve the within-month shape, not just the average. |
| Spark-spread distribution error | Whether power and gas are jointly reasonable for dispatch. |
| Dispatch hit rate | Whether modeled on/off decisions match historical operation. |
| Starts and fired-hours error | Whether dispatch is creating realistic operating stress. |
| Heat-rate calibration error | Whether fuel burn and generation imply plausible efficiency. |
| Basis residual tracking | Whether node-minus-hub is biased or structurally shifting. |

The test should be:

```text
fit on earlier years
  -> forecast later historical years
  -> compare against realized price, gas, dispatch, and generation
```

This mirrors the existing revenue methodology's Gen 2 idea: use 12+ months of realized-vs-forecast history to calibrate conditioning, residual correction, and perturbation models.

## Cross-References To Existing Methodology

This Step 2 plan should not duplicate the full revenue methodology. It should reuse it.

| Existing local reference | What Step 2 should reuse |
| :--- | :--- |
| `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/plans/step_1_climate_price_scenario_plan.md` | Immediate upstream Step 1 package: weather paths, power price paths, gas price paths, ancillary paths, scenario IDs, and validation rules. |
| `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/stateful_historical_replay_flow.md` | First-run historical replay flow: exogenous inputs, static config, opening state vector, dispatch decision, daily state update, and output schemas. |
| `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/basics_of_gas_prices.md` | Delivered-gas construction, major gas hubs, gas basis, daily/monthly gas frequency, and source hierarchy. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/02_scenario_engine_architecture.md` | Block sampling, level-shape decomposition, conditioning, and forward anchoring. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/03_layer_methodology.md` | Layered view: price scenarios, generation branches, and revenue assembly. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/03_price_data.md` | ISO LMP data, gas price data, GridStatus / ISO sources, EIA / NYMEX gas framing. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/05_generation_data.md` | CEMS, SCED, EIA-923, and GADS as calibration / validation inputs. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/08_forward_curves.md` | Power forward curve taxonomy, P-vs-Q distinction, hub/node basis, Gen 1/2/3 curve stack. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/probabilistic_methods/01_out_of_sample_problem.md` | Four out-of-sample problem types. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/probabilistic_methods/02_five_methods.md` | EVT, copulas, perturbed historical, bootstrap amplification, and parametric fitting. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/probabilistic_methods/03_hybrid_construction.md` | Core-plus-augmentation structure for combining block sampling, perturbations, and tails. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/execution/02_gen2_additions.md` | Gen 2 additions: empirical calibration, perturbation layer, residual correction, Monte Carlo, richer availability. |

## External Source Anchors

The detailed files should cite primary or market-facing sources where possible. These are anchors, not the full bibliography.

| Topic | Source anchor | Why it matters |
| :--- | :--- | :--- |
| Historical gas spot | EIA Henry Hub spot price data: `https://www.eia.gov/dnav/ng/hist/rngwhhda.htm` | Public historical gas benchmark for calibration and shape. |
| Forward gas | CME Henry Hub Natural Gas futures: `https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.contractSpecs.html` | Market-consistent fuel anchor for forward dispatch economics. |
| Thermal generation / fuel burn | EPA Clean Air Markets Program Data: `https://www.epa.gov/air-emissions-inventories/where-can-i-obtain-hourly-data-continuous-emissions-monitors-cems` | CEMS data supports hourly heat-rate and dispatch calibration. |
| ISO market prices | NYISO MIS public pricing index: `https://mis.nyiso.com/public/menu.htm` | Example of public ISO hourly price and outage data availability. |
| Cycling cost concepts | NREL Power Plant Cycling Costs: `https://research-hub.nrel.gov/en/publications/power-plant-cycling-costs/` | Supports start/cycling cost framing. |
| Outage terminology | NERC GADS Data Reporting Instructions: `https://www.nerc.com/pa/RAPA/gads/DataReportingInstructions/2025_GADS_DRI.pdf` | Standard terminology for outage, derate, and availability treatment. |

## Why This Plan Exists

The learning docs are now broad and useful, but they are still concept docs. They are not yet an implementation blueprint.

The execution blueprint should resolve questions like:

| Question | Why it matters |
| :--- | :--- |
| What exactly enters the dispatch model each day? | Prevents hidden assumptions and inconsistent data feeds. |
| Does dispatch use perfect foresight, rolling foresight, or myopic daily optimization? | Perfect foresight can overstate plant optionality. |
| How are Pmin and Pmax represented? | The plant cannot dispatch below minimum stable load or above feasible capability. |
| How are 1x1 and 2x1 CCGT modes represented? | Athens-style partial operation affects heat rate, starts, costs, and train-level damage. |
| Are average heat rate and incremental heat rate separated? | Average heat rate is useful for reporting; incremental heat rate is needed for marginal dispatch and offers. |
| Which costs are marginal dispatch costs versus fixed cashflow costs? | Prevents fixed LTSA fees from being treated as hourly avoidable costs. |
| How is outage timing handled? | A plant should not earn dispatch revenue while unavailable. |
| How are hourly operating profiles compressed into daily state updates? | This is the bridge from Step 2 to degradation and outage risk. |
| Which assumptions are Athens-specific? | Prevents the GE 7FA 2x1 case from becoming the hidden default for all gas plants. |

## Proposed Output Folder

The detailed Step 2 docs should live in a new folder:

```text
docs/
  step_2_execution_blueprint/
    00_index.md
    01_time_resolution_and_frequency.md
    02_dispatch_problem_definition.md
    03_input_data_contracts.md
    04_operating_range_pmin_pmax.md
    05_heat_rate_and_marginal_cost.md
    06_start_costs_vom_and_wear_cost.md
    07_dispatch_modes_and_constraints.md
    08_outage_timing_and_availability_gate.md
    09_hourly_to_daily_state_handoff.md
    10_validation_and_backtesting.md
    11_athens_step_2_worked_example.md
    12_open_questions_and_red_assumptions.md
```

This folder should not replace the learning docs. The learning docs teach the concepts. The Step 2 blueprint should specify how the model will use those concepts.

## Relationship To Existing Docs

| Existing location | Current role | How Step 2 should use it |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md` | High-level architecture and Athens pilot assumptions | Source of original framework intent, but not enough detail for implementation. |
| `docs/learning/basics/05_dispatch_and_daily_loop.md` | Beginner explanation of hourly dispatch inside daily loop | Foundation for `01_time_resolution_and_frequency.md` and `02_dispatch_problem_definition.md`. |
| `docs/learning/basics/01_capacity.md` | Capacity, Pmax/Pmin introduction | Foundation for operating range and weather-adjusted capacity. |
| `docs/learning/basics/02_heat_rate.md` | Heat rate concept and average vs incremental framing | Foundation for marginal cost and dispatch hurdle logic. |
| `docs/learning/basics/04_start_costs_and_vom.md` | Start cost, VOM, and LTSA cost framing | Foundation for marginal and non-marginal cost separation. |
| `docs/learning/basics/06_outages_availability_and_ltsa.md` | Availability, LTSA, forced outage overview | Foundation for outage gate and guarantee period handling. |
| `docs/learning/basics/07_state_vector_and_feedback.md` | State vector and feedback explanation | Foundation for hourly-to-daily state handoff. |
| `docs/learning/basics/08_ltsa_and_service_contracts.md` | Beginner service-contract guide | Foundation for LTSA fees, reserves, overages, coverage, exclusions, guarantees, and contract-state outputs. |
| `docs/learning/basics/09_operating_partitions_and_model_signals.md` | Cross-cutting operating partition guide | Foundation for turning hourly operation into load-mode, start-type, seasonal, stress, and price-regime signals. |
| `docs/learning/market_and_operations/00_market_and_operations_index.md` | Index for operating curves and market layer | Starting map for Pmin/Pmax, offer curves, marginal cost, and weather adjustment. |
| `docs/learning/market_and_operations/01_operating_range_pmin_pmax.md` | Detailed Pmin/Pmax operating-range guide | Foundation for the Step 2 operating range file and offer MW boundaries. |
| `docs/learning/market_and_operations/02_marginal_cost_and_offer_curves.md` | Marginal-cost and offer-curve guide | Foundation for Step 2 marginal cost, offer blocks, and average-vs-incremental heat-rate separation. |
| `docs/learning/market_and_operations/03_historical_vs_forecast_inputs.md` | Input-source boundary guide | Helps classify calibration evidence, scenario assumptions, true forecasts, and state-feedback outputs. |
| `docs/learning/market_and_operations/04_weather_adjusted_operating_curves.md` | Weather-adjusted Pmin/Pmax and heat-rate guide | Foundation for hourly weather capability, hot-day derates, and weather-sensitive dispatch cost. |
| `docs/learning/plant_types/02_combined_cycle_gt.md` | CCGT plant-type guide | Foundation for 1x1/2x1 CCGT modes, GT/HRSG/ST constraints, and train-level state variables. |
| `docs/learning/examples/athens_7fa_2x1_ccgt.md` | Worked Athens assumptions | Source for the first concrete Step 2 example, with all Athens-specific assumptions labeled. |

## One-File-At-A-Time Workflow

Each detailed Step 2 file should follow the same process.

```text
1. Read existing local docs.
2. Research outside references where needed.
3. Identify what is concept, what is assumption, and what is implementation choice.
4. Write a short plan for that file.
5. Create or update the file.
6. Check links, tables, formulas, and examples.
7. Record open questions and red assumptions.
```

The goal is not speed. The goal is to avoid creating impressive-looking docs that hide weak assumptions.

## Detailed File Plan

| Order | File | Main purpose | Key tables / examples |
| :--- | :--- | :--- | :--- |
| 0 | `00_index.md` | Explain the Step 2 folder, reader path, and how it connects to learning docs. | Folder map, dependency map, "what Step 2 is / is not" table. |
| 1 | `01_time_resolution_and_frequency.md` | Resolve the hourly vs daily vs monthly confusion. | Frequency matrix for power, gas, generation, state, LTSA, and cashflow; hourly-inside-daily ASCII loop; examples of wrong frequency choices. |
| 2 | `02_dispatch_problem_definition.md` | Define the dispatch problem before adding complexity. | Opening state input, power-forward anchor, gas-forward anchor, dispatch-generated generation, objective function, decision variables, constraints, perfect vs rolling foresight table. |
| 3 | `03_input_data_contracts.md` | Define required input schemas and data quality checks. | Input matrix by source, required columns, units, missing-data treatment, hub/node/DA/RT and Henry Hub/delivered-gas identifiers. |
| 4 | `04_operating_range_pmin_pmax.md` | Define feasible MW range and operating modes. | Pmin/Pmax definitions, 1x1 vs 2x1 mode table, weather-adjusted capacity curve sketch. |
| 5 | `05_heat_rate_and_marginal_cost.md` | Convert heat-rate curves and gas price into dispatch economics. | Average vs incremental heat-rate table, marginal cost formula, part-load example. |
| 6 | `06_start_costs_vom_and_wear_cost.md` | Separate fuel, VOM, start cost, EOH wear, LTSA reserves, and fixed fees. | Marginal vs fixed cost table, start cost recovery example, EOH proximity penalty sketch. |
| 7 | `07_dispatch_modes_and_constraints.md` | Define Mode A/B/C dispatch, ramp, min up/down, start time, and mode-switching. | Constraint matrix, operating-mode examples, partial CCGT dispatch case. |
| 8 | `08_outage_timing_and_availability_gate.md` | Define when forced and planned outages block dispatch. | Availability gate flow, outage-state table, partial derate vs full outage distinction. |
| 9 | `09_hourly_to_daily_state_handoff.md` | Specify how hourly operations become daily state updates. | Handoff schema, daily summary table, state-update ordering diagram. |
| 10 | `10_validation_and_backtesting.md` | Define how to prove the model is useful and not just plausible. | Backtest matrix, acceptance criteria, NYISO hourly data plan, GADS/outage calibration plan. |
| 11 | `11_athens_step_2_worked_example.md` | Walk through one concrete Athens day and one multi-day scenario. | One-day dispatch table, start/EOH update, 1x1 vs 2x1 comparison. |
| 12 | `12_open_questions_and_red_assumptions.md` | Centralize unresolved assumptions and diligence items. | Red/amber/green register, owner questions, data requests. |

## Research Grounding Needed By File

| File area | Primary research need | Candidate source types |
| :--- | :--- | :--- |
| Cycling and start costs | Validate cycling cost concepts and distinguish cost categories. | NREL cycling cost studies, industry maintenance literature, OEM or LTSA docs if available. |
| Outages and availability | Use standard outage, derating, and availability vocabulary. | NERC GADS Data Reporting Instructions, asset outage logs, cause-code records. |
| Dispatch optionality | Explain why flexible thermal assets are spread options. | Market-facing power asset valuation articles, dispatch-cost methodology notes. |
| NYISO validation | Build historical hourly backtest data plan. | NYISO MIS LBMP, outage, load, and generator public data. |
| Heat-rate and capacity curves | Avoid treating average heat rate as marginal heat rate. | Plant performance tests, CEMS/EMS data, OEM correction curves, operating historian data. |
| LTSA / CSA terms | Translate operating events into contract cashflows. | Actual contract, amendments, invoices, outage reports, guarantee formulas. |

## Important Modeling Distinctions

These distinctions should appear repeatedly across the Step 2 docs.

| Distinction | Why it matters |
| :--- | :--- |
| Historical calibration vs forecast | Historical Pmin/Pmax and heat-rate curves are evidence, not a future forecast by themselves. |
| Exogenous inputs vs recursive state inputs | Prices, gas, and weather come from scenario paths; capacity, heat rate, outage state, EOH headroom, and LTSA counters come from yesterday's closing plant state. |
| Average heat rate vs incremental heat rate | Average heat rate reports efficiency; incremental heat rate drives marginal offer cost. |
| Nameplate capacity vs hourly Pmax | The plant cannot sell nameplate MW if weather, degradation, or outage state reduces capability. |
| Pmax vs Pmin | Maximum output caps upside; minimum stable output can force uneconomic generation after commitment. |
| Dispatch schedule vs market offer curve | Internal model dispatch is not automatically the same as an ISO offer curve. |
| Fixed cost vs marginal cost | Fixed LTSA fees affect cashflow but usually should not decide one extra dispatch hour. |
| Contractual EOH vs physical damage | EOH may drive billing and inspections; physical damage may drive failure risk. |
| Plant-level state vs train-level state | A 2x1 CCGT can have different GT-A, GT-B, HRSG-A, and HRSG-B histories. |
| Full outage vs partial derate | A derated plant may still earn revenue, so not every availability event is zero MW. |
| Target architecture vs prototype | Current prototype simplifications should not be confused with the final dynamic feedback model. |

## Initial Corrections And Watch Items

Before writing the detailed Step 2 docs, keep these watch items visible.

| Item | Concern | Recommended treatment |
| :--- | :--- | :--- |
| LTSA fixed fee example | Current docs say `$850,000/month`, but one penalty example divides `$850,000 / 12`. | Decide whether `$850,000` is monthly or annual, then correct the example. |
| Forced outage probability | Component probabilities need clear hazard/probability semantics. | Use a state-conditioned hazard framework in the detailed outage file. |
| Recursive state input | Step 2 can be misread as using only today's market and weather inputs. | Every Step 2 file should show the opening plant state as an input before dispatch. |
| Outage timing | Current simplified logic checks outage before dispatch. | Keep as prototype logic, but explain alternatives for running-state and startup-failure hazards. |
| AQI-driven fouling | Generic AQI may not map cleanly to compressor foulants. | Treat as proxy until site-specific fouling data is available. |
| 1x1 vs 2x1 dispatch | Partial CCGT operation requires train-level state. | Make train-level tracking explicit in Step 2 assumptions. |
| Perfect foresight | Full-day or multi-day perfect foresight may overstate optionality. | Document the assumed foresight horizon and sensitivity-test it. |
| Static prototype schedules | Prototype schedules may not reflect dynamic feedback. | Separate prototype results from target architecture. |

## Recommended Writing Standard

Each detailed Step 2 file should use this shape:

```text
# Topic

## Purpose
## Plain-English Version
## Why This Matters For Step 2
## Where It Fits In The Daily Loop
## Opening State / Recursive Inputs
## Inputs
## Outputs
## Frequency / Time Resolution
## Modeling Choices
## Worked Example
## Tables / ASCII Diagrams
## What The Current Framework Assumes
## What Needs Calibration
## Open Questions Before Investment Use
## References
```

Use examples before formulas where the topic is difficult.

Use tables where a reader needs to compare:

- frequency
- source
- model use
- caveat
- certainty
- plant-type variation

## Step 2 Folder Creation Plan

Recommended first pass:

| Pass | Action | Why |
| :--- | :--- | :--- |
| 1 | Create `docs/step_2_execution_blueprint/00_index.md`. | Establish the folder purpose and map before details. |
| 2 | Create `01_time_resolution_and_frequency.md`. | Frequency confusion affects every later modeling decision. |
| 3 | Create `02_dispatch_problem_definition.md`. | Defines what Step 2 actually optimizes. |
| 4 | Create `03_input_data_contracts.md`. | Prevents vague discussion by naming required data and units. |
| 5 | Then proceed one file at a time. | Keeps assumptions reviewable and avoids big-bang documentation drift. |

## Open Decisions

| Decision | Options | Initial recommendation |
| :--- | :--- | :--- |
| Folder location | `docs/step_2_execution_blueprint/` vs `docs/learning/step_2/` | Use `docs/step_2_execution_blueprint/` because this is execution guidance, not beginner learning. |
| First detailed file | Dispatch definition vs frequency | Start with frequency because it reduces confusion across all later docs. |
| Dispatch sophistication | Static schedules, daily myopic optimization, rolling horizon, full unit commitment | Document all, but implement/explain from simple to advanced. |
| Market offer curves | Include now or later | Explain boundary now; build detailed offer-curve doc after Pmin/Pmax and marginal cost. |
| Athens role | Default model vs worked example | Keep Athens as the first worked example only. |
| Validation depth | High-level checks vs full backtest specification | Create a real validation plan early, even if implementation comes later. |

## Test Plan For This Documentation Track

After each Step 2 file is created:

```text
rg -n "Athens|worked example|assumption|frequency|hourly|daily|monthly|annual" docs/step_2_execution_blueprint
LC_ALL=C rg -n "[^ -~]" docs/step_2_execution_blueprint
```

Manual checks:

- A non-specialist should understand the plain-English version.
- A model builder should understand the required inputs and outputs.
- Athens assumptions should be labeled as worked-example assumptions.
- Frequency should be explicit for each input and output.
- Fixed costs and marginal costs should not be mixed.
- Historical calibration should not be mislabeled as forecast.
- Prototype simplifications should not be presented as final architecture.

## Immediate Next Step

Create the Step 2 folder and start with:

```text
docs/step_2_execution_blueprint/00_index.md
docs/step_2_execution_blueprint/01_time_resolution_and_frequency.md
```

Do not write all files at once. The better workflow is:

```text
one file
  -> research
  -> reason
  -> plan
  -> write
  -> review assumptions
  -> then move to the next file
```
