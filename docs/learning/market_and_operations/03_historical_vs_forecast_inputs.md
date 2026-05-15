# Historical Vs Forecast Inputs

## What This Guide Is

This guide separates three things that are easy to mix up:

```text
historical calibration
user-provided future assumptions
true forecasts or stochastic future paths
```

Read these first:

- [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md)
- [Marginal Cost And Offer Curves](./02_marginal_cost_and_offer_curves.md)
- [Dispatch And The Daily Loop](../basics/05_dispatch_and_daily_loop.md)
- [State Vector And Feedback](../basics/07_state_vector_and_feedback.md)

> Plant-Type Note
> This guide is about input classification, not one plant design. The same classification problem appears for simple-cycle GTs, CCGTs, aeroderivatives, frame units, and CHP plants. Plant type changes the inputs, but not the need to label them correctly.

## First-Time Reader Map

The model can use past data and still simulate the future. The important point is to say which part is doing what.

| Input type | Plain meaning | Example |
| :--- | :--- | :--- |
| Historical calibration | Past data used to estimate plant behavior. | Fitted fuel curve from prior CEMS data. |
| User assumption | Future input supplied by user or scenario. | Gas price = $4.00/MMBtu. |
| Forecast | Future estimate from a forecast source or model. | Tomorrow's hourly temperature. |
| Stochastic path | Random or scenario-based future path. | Forced outage draw or Monte Carlo power-price path. |
| State feedback | Future condition derived from prior simulated operation. | Tomorrow's EOH after today's dispatch. |

The mental stack is:

```text
past data calibrates model behavior
future assumptions drive the scenario
state feedback evolves the plant
```

## Why This Matters

Investment and dispatch discussions can become confused if historical evidence is called a forecast.

Bad wording:

```text
Past August Pmax forecasts next August Pmax.
```

Better wording:

```text
Past August data calibrates a seasonal operating envelope.
Future August Pmax still depends on weather, outages, degradation, and plant state.
```

This matters because:

| Mistake | Why it is risky |
| :--- | :--- |
| Calling history a forecast | Overstates model certainty. |
| Calling user gas price a model forecast | Hides who provided the future assumption. |
| Ignoring plant state | Treats the plant as fresh every day. |
| Ignoring weather | Misses hot/cold capability and heat-rate effects. |
| Ignoring outages | Assumes availability when the plant may be unavailable. |

## Input Classification Table

| Model item | Historical calibration? | Forecast / scenario? | Notes |
| :--- | :---: | :---: | :--- |
| Fuel curve coefficients | Yes | No by themselves | Past operating data estimates fuel behavior. |
| Monthly Pmin/Pmax | Yes | No by themselves | Historical seasonal envelope, not a weather forecast. |
| Incremental heat rate curve | Yes | No by itself | Derived from fitted fuel curve. |
| Future gas price | No | Yes if forward/user scenario | The model may receive it rather than forecast it. |
| Future power price | No | Yes | Needed for dispatch economics. |
| Future weather | No | Yes | Needed for forecast-aware Pmax(T), Pmin(T), HR(T). |
| Initial EOH | Historical/current state | Scenario starting point | Must come from records or assumption. |
| Future EOH | No | State feedback | Created by simulated operation. |
| Planned outage schedule | Sometimes historical pattern | Future schedule | Should come from known maintenance plan. |
| Forced outage | Historical calibration | Stochastic path | Hazard model can use historical data. |

## Historical Calibration

Historical calibration means:

```text
Use past data to estimate how the plant behaves.
```

Examples:

| Calibrated item | Data source | What it estimates |
| :--- | :--- | :--- |
| Fuel curve | CEMS-like load and heat input | Fuel burn vs MW. |
| Pmin/Pmax envelope | Historical gross load | Normal operating range. |
| Heat-rate degradation trend | Performance history | Efficiency drift over time. |
| Forced outage frequency | Outage history | Baseline reliability behavior. |
| Start classifications | Operations logs | Hot/warm/cold start patterns. |

Historical calibration is valuable because it makes the model less generic. But it is not automatically forward-looking.

## User-Provided Scenario Inputs

Some future inputs may be provided directly.

| Input | Example | Who owns the assumption |
| :--- | :--- | :--- |
| Gas price | $4.00/MMBtu | User, market forward curve, or scenario team. |
| VOM | $3/MWh | User or asset model. |
| Emissions price | $0/MWh or scenario value | Market/scenario assumption. |
| Contract term | CSA fixed fee, EOH reserve | Contract review or assumption. |
| Dispatch mode | aggressive vs conservative | Model design choice. |

Safe wording:

```text
The model uses a user-provided gas price.
```

Unsafe wording:

```text
The model forecasts gas price.
```

Only call it a forecast if the model or an external forecast source actually produces it.

## True Forecast Inputs

True forecast inputs look forward using explicit future information.

Examples:

| Forecast input | Why it matters |
| :--- | :--- |
| Hourly power prices | Dispatch value changes hour by hour. |
| Hourly temperature | Pmax, Pmin, and heat rate can change hourly. |
| Gas forward prices | Fuel cost changes dispatch economics. |
| Planned outage dates | Blocks dispatch in known periods. |
| Ancillary-service prices | Can change value of flexibility. |

Forecast inputs do not have to be perfect. They must be labeled as forecasts or scenarios.

## State Feedback Is Different

The model also creates future plant state from its own simulated operation.

```text
opening state today
  + today's dispatch
  = closing state today
  = opening state tomorrow
```

Examples:

| State variable | How it moves forward |
| :--- | :--- |
| EOH | Increases from fired hours, starts, trips, and swings. |
| Compressor fouling | Builds with operation and resets partly after wash. |
| Heat-rate degradation | Worsens with condition and can reset after maintenance. |
| Outage status | Carries active outage duration forward. |
| Start classification | Depends on shutdown duration from prior operation. |

State feedback is neither pure history nor external forecast. It is model-evolved plant condition.

## Current Historical Offer Pipeline Boundary

The local plant-model reference describes a pipeline like this:

```text
historical CEMS data
  |
  v
fit fuel curve
  |
  v
calculate monthly Pmin/Pmax from history
  |
  v
user provides bid date and gas price
  |
  v
calculate marginal costs
  |
  v
generate offer blocks
```

This is useful, but mostly historical and user-input driven.

| Component | Forecasted by that pipeline? | Why |
| :--- | :---: | :--- |
| Fuel curve | No | Fitted from past data. |
| Monthly Pmin/Pmax | No | Pooled from past months. |
| Gas price | No | User input. |
| Weather | No | Not included unless added. |
| Availability | No | Often assumed available unless modeled. |
| Dispatch decision | No | Offer generated; market or dispatch model decides. |

## What Changes In InfraSure Step 2

InfraSure Step 2 needs more than a static offer generator.

It needs:

```text
hourly power price paths
hourly weather paths
daily or hourly gas price paths
plant state feedback
availability gate
dispatch decision
daily engineering update
```

That means the learning docs should keep this boundary:

| Layer | Historical role | Future role |
| :--- | :--- | :--- |
| Fuel curve | Calibrate physical fuel behavior. | Evaluate future dispatch cost. |
| Pmin/Pmax | Calibrate operating range. | Adjust with weather/state for future hours. |
| Weather | Past data can calibrate sensitivity. | Future path drives hourly Pmax/Pmin/HR. |
| Outage history | Calibrate hazard and duration. | Future outage state blocks dispatch. |
| EOH history | Set starting state. | Future EOH evolves from dispatch. |

## Worked Example 1: Historical Envelope

Assume:

| Item | Value |
| :--- | :--- |
| Data | 2022 to 2024 operating hours |
| Method | Pool all July hours |
| July Pmin | 75 MW |
| July Pmax | 430 MW |

Correct interpretation:

```text
Historical July operation suggests a normal range of 75 to 430 MW.
```

Incorrect interpretation:

```text
The model has forecasted 430 MW for next July.
```

To forecast next July more rigorously, add:

- future hourly temperature
- planned outage state
- expected degradation state
- operating mode constraints
- market and fuel scenario

## Worked Example 2: Gas Price

Assume the model run uses:

```text
gas price = $4.00/MMBtu
```

If the user typed this value, it is a scenario assumption.

If the value came from a forward curve, it is an external market input.

If the model generated it from a gas price model, then it is a model forecast.

Do not hide the source.

## Worked Example 3: Weather

Historical calibration:

```text
Past data says Pmax falls about 0.8 MW per deg C.
```

Forecast input:

```text
Tomorrow at 15:00 is expected to be 34 deg C.
```

Forecast-aware Pmax:

```text
Pmax(34 deg C) = baseline Pmax + temperature adjustment
```

The first line is calibration. The second line is forecast input. The third line is model application.

## Documentation Standard

Every future Step 2 file should label inputs like this:

| Field | Required label |
| :--- | :--- |
| Source | Historical data, user input, forecast vendor, contract, model state, stochastic draw. |
| Frequency | Hourly, daily, monthly, annual, event-level. |
| Basis | Unit-level, plant-level, mode-level, market-level. |
| Confidence | Green, Amber, or Red. |
| Update method | Fixed, recalibrated, scenario-provided, forecast-fed, state-updated. |

## What The Framework Includes

| Included item | Why it helps |
| :--- | :--- |
| Daily state feedback | Separates starting state from simulated future operation. |
| Climate and market simulation layer | Makes future paths explicit. |
| Step 2 dispatch layer | Uses future prices/weather and current plant state. |
| Pmin/Pmax guide | Separates historical envelopes from forecast-aware capability. |
| Athens worked example | Labels asset-specific values. |

## What The Framework Leaves Out

| Missing detail | Why it matters |
| :--- | :--- |
| Exact source registry for every input | Needed for auditability. |
| Forecast vendor or method | Needed if using actual future weather/price forecasts. |
| Versioning for calibrated curves | Needed when refitting fuel curves or Pmin/Pmax. |
| Data freshness rules | Needed to know when historical calibration is stale. |
| Scenario governance | Needed to separate base, downside, and upside cases. |

## Source Basis And Certainty

| Source | Use in this guide | Certainty |
| :--- | :--- | :--- |
| [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md) | Historical envelope vs forecast-aware range. | Green for concept. |
| [Marginal Cost And Offer Curves](./02_marginal_cost_and_offer_curves.md) | Offer pipeline and fuel-curve dependencies. | Green for concept. |
| [State Vector And Feedback](../basics/07_state_vector_and_feedback.md) | Model-evolved future plant condition. | Green for framework logic. |
| `plant model/is_it_forecasted.md` | Clear local boundary between historical method and true forecast. | Green for methodology boundary. |
| `plant model/pminimum_pmaximum.md` | Historical monthly Pmin/Pmax method. | Green as historical calibration method. |

## Open Questions Before Implementation

| Question | Why it matters |
| :--- | :--- |
| Which inputs are user scenario assumptions? | Prevents accidental claims of forecasting. |
| Which inputs come from forward curves or forecast vendors? | Defines source responsibility. |
| How often are fuel and operating curves recalibrated? | Keeps history from becoming stale. |
| How is plant state initialized and audited? | Starting EOH/degradation can dominate results. |
| Are outage paths deterministic or stochastic? | Changes interpretation of future availability. |
| How are base, upside, and downside scenarios governed? | Required for investment communication. |

## Quick Recap

```text
historical data calibrates behavior
forecast/scenario inputs describe the future
state feedback evolves plant condition
```

Do not call historical calibration a forecast unless future inputs actually enter the model.
