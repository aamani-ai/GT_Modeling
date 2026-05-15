# Market And Operations Index

## Purpose

This folder is for the market-facing and operating-curve layer of the gas plant model.

The basics docs explain physical and contract concepts. The degradation docs explain how operation changes plant condition. This folder should explain how operating data, Pmin/Pmax, heat-rate curves, marginal cost, offer curves, weather adjustment, and dispatch constraints fit together.

The layer separation is:

```text
plant physics and contracts
        |
        v
operating capability curves
        |
        v
market offer / dispatch economics
        |
        v
daily state feedback
```

## Why This Is Separate From The Basics

Capacity and heat rate are already covered in the basics. But market modeling needs extra detail:

| Topic | Why it needs its own layer |
| :--- | :--- |
| Pmax | Maximum feasible MW changes with weather, outages, degradation, and operating mode. |
| Pmin | Minimum stable MW can force uneconomic run hours after startup. |
| Incremental heat rate | Marginal fuel cost can differ from average heat rate. |
| Offer curves | Market bids need MW/price blocks or continuous curves. |
| Historical operating envelopes | Useful calibration evidence, but not a forecast by itself. |
| Weather adjustment | Pmax(T), Pmin(T), and HR(T) can all matter. |
| Operational constraints | Ramp, min up/down, start time, emissions, and fuel limits affect feasible dispatch. |

## Planned Guide Set

These files are planned as future guides, not fully written yet.

| Order | Planned file | Main question answered | Status |
| :--- | :--- | :--- | :--- |
| 0 | `00_market_and_operations_index.md` | What belongs in this layer? | Current file. |
| 1 | `01_operating_range_pmin_pmax.md` | What are minimum stable output and maximum capability? | Implemented. |
| 2 | `02_marginal_cost_and_offer_curves.md` | How do heat-rate curves become market offers? | Implemented. |
| 3 | `03_historical_vs_forecast_inputs.md` | What is calibration evidence versus a true forecast? | Implemented. |
| 4 | `04_weather_adjusted_operating_curves.md` | How do temperature and weather change Pmax, Pmin, and heat rate? | Implemented. |
| 5 | `05_dispatch_constraints.md` | How do ramp, min up/down, and start time affect Step 2? | Planned. |

## Concepts To Keep Separate

| Concept | Plain meaning | Common mistake |
| :--- | :--- | :--- |
| Pmax | Maximum feasible output. | Treating nameplate or ISO capacity as available in every hour. |
| Pmin | Minimum stable output when online. | Assuming the plant can always run at any low MW level. |
| Average heat rate | Total fuel divided by total MWh. | Using it as marginal cost without checking load shape. |
| Incremental heat rate | Extra fuel needed for one more MWh. | Ignoring it when building offer blocks. |
| Historical curve | What the plant did in past data. | Calling it a forecast without future weather or market inputs. |
| Dispatch schedule | What the model chooses to run. | Confusing it with an ISO/RTO offer curve. |
| Offer curve | What the plant bids or offers into the market. | Treating it as the same thing as physical capability. |

## Basic Workflow

```text
1. Clean historical operating data
        |
        v
2. Estimate Pmin/Pmax and heat-rate behavior
        |
        v
3. Apply weather and plant-condition adjustments
        |
        v
4. Convert fuel, VOM, start cost, and wear into marginal economics
        |
        v
5. Build offer or dispatch constraints
        |
        v
6. Feed realized operation into the daily state update
```

## Plant-Type Dependence

Market and operating curves are strongly plant-type dependent.

| Plant type | Operating-curve warning |
| :--- | :--- |
| Simple-cycle GT | Pmin/Pmax may be simpler, but fast-start and reserve behavior matter. |
| Combined-cycle GT | 1x1 vs 2x1 modes create blocky capacity, heat-rate, and start-cost behavior. |
| Frame GT | Start time, ramping, and thermal constraints can make short dispatch windows infeasible. |
| Aeroderivative GT | Fast-start capability and flexible ramping can materially change offer value. |
| CHP / cogeneration | Steam demand can determine minimum output or must-run behavior. |

## Lessons From The Local Plant-Model Reference

The local reference reviewed at:

```text
/Users/divy/code/personal/other/gas-to-power/code/plant model
```

adds useful market/operations discipline:

| Lesson | Why it matters here |
| :--- | :--- |
| Estimate Pmin and Pmax carefully. | Dispatch needs feasible MW ranges, not only ISO capacity. |
| Separate historical ranges from forecasts. | Past data supports calibration, but future scenarios need future inputs. |
| Use weather-adjusted curves. | Hot weather can reduce Pmax and worsen heat rate. |
| Treat offer curves as their own output layer. | Offers are related to dispatch economics but not identical to degradation logic. |
| Filter noisy data before curve fitting. | Bad data can create false heat-rate or capacity conclusions. |
| Keep monotonic offer blocks. | MW/price blocks should be economically coherent. |

## How This Connects To Existing Guides

| Existing guide | Market/operations connection |
| :--- | :--- |
| [Capacity](../basics/01_capacity.md) | Adds Pmax/Pmin and weather-adjusted operating envelopes. |
| [Heat Rate](../basics/02_heat_rate.md) | Adds average vs incremental heat rate and marginal fuel cost. |
| [Start Costs And VOM](../basics/04_start_costs_and_vom.md) | Adds start-cost recovery across short runs and offer hurdles. |
| [Dispatch And The Daily Loop](../basics/05_dispatch_and_daily_loop.md) | Adds market constraints, offer curves, and unit commitment details. |
| [State Vector And Feedback](../basics/07_state_vector_and_feedback.md) | Adds possible Pmin/Pmax, ramp, and offer-mode state variables. |

Implemented detailed guide:

- [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md)
- [Marginal Cost And Offer Curves](./02_marginal_cost_and_offer_curves.md)
- [Historical Vs Forecast Inputs](./03_historical_vs_forecast_inputs.md)
- [Weather-Adjusted Operating Curves](./04_weather_adjusted_operating_curves.md)

## Guardrails

Do not blur these boundaries:

```text
historical operating envelope != forecast
offer curve != physical dispatch schedule
average heat rate != incremental heat rate
ISO capacity != hourly available Pmax
Athens 2x1 CCGT offer behavior != every gas plant
```

## Open Questions

| Question | Why it matters |
| :--- | :--- |
| Does the current InfraSure model need explicit market offer curves or only internal dispatch? | Decides how much detail this folder needs. |
| Which market rules matter first: NYISO energy, capacity, reserves, or bilateral dispatch? | Offer-curve design depends on market product. |
| Is historical CEMS or EMS data available by unit? | Determines whether Pmin/Pmax and heat-rate curves can be calibrated. |
| Should Pmin/Pmax be state variables? | Weather, degradation, and outages can change feasible dispatch. |
| How should 1x1 vs 2x1 CCGT offers be represented? | Athens partial operation can materially change economics. |
