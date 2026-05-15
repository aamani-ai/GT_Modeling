# Operating Range: Pmin And Pmax

## What This Guide Is

This guide explains the plant's feasible operating range:

```text
Pmin <= online MW <= Pmax
```

Read these first if the terms are new:

- [Capacity](../basics/01_capacity.md)
- [Dispatch And The Daily Loop](../basics/05_dispatch_and_daily_loop.md)
- [Simple-Cycle Gas Turbine](../plant_types/01_simple_cycle_gt.md)
- [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md)

> Plant-Type Note
> Pmin and Pmax are universal dispatch concepts, but the values are plant-specific. A simple-cycle GT, aeroderivative peaker, frame CT, 1x1 CCGT, 2x1 CCGT, and CHP plant can all have different feasible operating ranges, start behavior, heat-rate curves, and offer blocks.

## First-Time Reader Map

If this topic is new, start with a simple question:

> If the plant is online, what MW range can it actually operate within?

There are three possible states:

```text
offline
  |
  v
online at or above Pmin
  |
  v
online up to Pmax
```

Key terms:

| Term | First-time meaning |
| :--- | :--- |
| MW | Instantaneous power output. |
| MWh | Energy produced over time. |
| Pmin | Minimum stable MW when the unit is online. |
| Pmax | Maximum feasible MW under current conditions. |
| Operating range | MW interval between Pmin and Pmax. |
| Nameplate capacity | Broad quoted plant size; not always dispatchable every hour. |
| ISO capacity | Reference capacity at standard conditions. |
| Effective capacity | Capacity after weather, degradation, outages, and operating mode. |
| Offer block | MW segment submitted or represented in a market offer curve. |
| Historical envelope | Pmin/Pmax estimated from past operating data. |
| Forecast | A future estimate using explicit future inputs such as weather, outages, or market assumptions. |

The mental stack is:

```text
equipment capability -> operating range -> dispatch feasibility -> offer blocks
```

## Why This Matters

Dispatch is not just:

```text
run if price is high
```

The plant must respect its feasible MW range.

```text
If online:

          feasible output
      |----------------------|
     Pmin                  Pmax
```

Pmax matters because it caps revenue opportunity:

```text
lower Pmax -> fewer MWh available to sell
```

Pmin matters because it can force the plant to run through weak-price hours:

```text
once online, plant may not be able to run below Pmin
```

For Step 2 dispatch, Pmin/Pmax answer:

| Question | Why it matters |
| :--- | :--- |
| Can the plant physically produce the target MW? | Pmax is the upper bound. |
| Can the plant stay online at low MW? | Pmin is the lower bound. |
| How should offer blocks be shaped? | Blocks must fit inside the feasible range. |
| Can a short run recover start cost? | Pmax affects MWh available; Pmin affects forced online volume. |
| Does weather change feasible output? | Hot weather can lower Pmax and sometimes raise Pmin. |
| Does plant condition change feasible output? | Outages and degradation can reduce Pmax. |

## Plain-English Concept

Think of Pmin/Pmax as the guardrails around dispatch.

```text
offline                  online feasible range
  0 MW        Pmin                              Pmax
   |----------|----------------------------------|
       not normally stable          dispatch can choose here
```

If the plant is offline, output is zero.

If the plant is online, it usually cannot choose any MW from zero to maximum. It often needs to stay above a minimum stable output. That is Pmin.

Pmax is not always the plant's nameplate capacity. It changes with:

- ambient temperature
- outage or derate state
- inlet cooling status
- compressor fouling or erosion
- operating mode, such as 1x1 vs 2x1 CCGT
- emissions or permit limits
- fuel or auxiliary-system constraints

## What Pmax Is Not

Pmax is easy to overstate.

| Pmax is not | Why |
| :--- | :--- |
| Nameplate capacity | Nameplate is a broad reference, not hourly available MW. |
| ISO capacity | ISO capacity is a standard-condition reference. |
| Always the highest historical MW | One extreme hour may be a data error or special operating condition. |
| Always the market offer upper MW | Offer limits may be more conservative than physical limits. |
| Always forecasted | A historical monthly Pmax is calibration evidence unless future inputs are used. |

Better wording:

```text
Pmax = maximum feasible MW for the relevant hour, plant state, and operating mode
```

## What Pmin Is Not

Pmin is also easy to misunderstand.

| Pmin is not | Why |
| :--- | :--- |
| Zero | Zero means offline, not minimum stable online operation. |
| Always the lowest historical positive MW | Startup, shutdown, testing, and transient hours can create false lows. |
| Always a fixed percent of Pmax | Minimum stable output depends on unit design, emissions, controls, mode, and market rules. |
| Always the first offer block | Market offers may start at economic minimum, emergency minimum, or other market-defined limits. |

Better wording:

```text
Pmin = lowest MW the online unit can sustainably carry under the modeled operating condition
```

## How Pmin/Pmax Feed Step 2

Step 2 dispatch should use Pmin/Pmax before choosing hourly MW.

```text
Start of hour
  |
  v
Is plant available?
  |
  +-- no -> MW = 0
  |
  +-- yes
        |
        v
     compute Pmin/Pmax for hour
        |
        v
     choose offline or online
        |
        v
     if online, choose MW between Pmin and Pmax
```

Important:

```text
Pmin/Pmax are feasibility constraints.
Heat rate and prices decide whether operating inside that range is economic.
```

Example:

| Hour | Price | Pmin | Pmax | Dispatch implication |
| :--- | ---: | ---: | ---: | :--- |
| 10:00 | $28/MWh | 120 MW | 500 MW | Probably offline if fuel cost is high. |
| 15:00 | $160/MWh | 120 MW | 470 MW | Run if margin can recover start and wear cost. |
| 22:00 | $35/MWh | 120 MW | 500 MW | May need to stay online if min-run constraint binds. |

## Pmin/Pmax By Timescale

Different values belong at different timescales.

| Timescale | Example | Use |
| :--- | :--- | :--- |
| Design / nameplate | 500 MW class plant | Rough plant size. |
| ISO test basis | 531 MW at 59 deg F | Reference performance comparison. |
| Seasonal historical envelope | August Pmax from past August data | Calibration and offer baseline. |
| Hourly weather-adjusted range | Pmax at 96 deg F today | Hourly dispatch feasibility. |
| State-adjusted range | Pmax after compressor degradation or derate | Daily state feedback. |
| Offer limit | Submitted market MW block limit | Commercial / market output layer. |

Do not mix these without naming the basis.

```text
same plant, different basis:

nameplate Pmax
ISO Pmax
monthly historical Pmax
hourly weather-adjusted Pmax
degraded-state Pmax
market-offer Pmax
```

## Historical Monthly Operating Range Method

The local plant-model reference uses a simple, robust approach to estimate historical Pmin/Pmax from operating data.

The key idea:

```text
use historical data to estimate normal seasonal operating range
```

It pools data by calendar month, not by each month in time.

```text
All January hours across years -> January bucket
All February hours across years -> February bucket
...
All December hours across years -> December bucket
```

Why:

| Reason | Plain-English meaning |
| :--- | :--- |
| Seasonal awareness | Summer and winter capability can differ. |
| More data per bucket | Pooling across years gives more observations. |
| Robustness | Percentiles avoid extreme one-off outliers. |
| Simplicity | Produces 12 Pmin/Pmax pairs that are easy to inspect. |

### Step 1: Filter To Valid Operating Data

Use operating data only after basic quality filters.

| Filter | Why |
| :--- | :--- |
| `opTime == 1.0` if available | Keeps full operating hours; avoids startup/shutdown fragments. |
| `grossLoad > 0` | Removes offline hours. |
| `heatInput > 0` if fitting heat-rate curves | Removes invalid fuel data. |
| measured-only flag if available | Avoids substituted or estimated data when possible. |
| outlier checks | Removes sensor errors and unusual transient points. |

For Pmin/Pmax, the point is not to find one strange low or high hour. The point is to estimate normal feasible range.

### Step 2: Pool By Calendar Month

Example:

| Dataset span | January bucket contains |
| :--- | :--- |
| 2022 to 2024 | January 2022 + January 2023 + January 2024 hours |

This creates twelve buckets:

```text
Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec
```

### Step 3: Use Robust Percentiles

The local reference uses:

| Quantity | Percentile | Why |
| :--- | :--- | :--- |
| Pmin | 5th percentile of positive load | Avoids startup/shutdown and rare low outliers. |
| Pmax | 98th percentile of positive load | Avoids spikes, meter issues, and unusual one-off highs. |

Conceptual example:

```text
Sort all July operating MW values:

low outliers      normal operating range                 high outliers
   |                       |----------------------------------|   |
   v                       v                                  v
  20  30  45  70  75  80 ... 410  420  430  435  450  490  520
             ^                                   ^
             |                                   |
          Pmin p05                            Pmax p98
```

### Step 4: Smooth Month-To-Month

The local reference smooths the twelve monthly values with a circular rolling average.

Why circular:

```text
December should be close to January,
not treated as the end of a hard line.
```

Example:

| Month | Raw Pmax | Smoothed idea |
| :--- | ---: | :--- |
| December | 515 MW | Average with November and January. |
| January | 520 MW | Average with December and February. |
| February | 518 MW | Average with January and March. |

This avoids artificial jumps:

```text
bad signal:
Jun 465 -> Jul 430 -> Aug 460 -> Sep 480

better signal:
smooth transition through summer capability
```

### Step 5: Use The Month For A Bid Or Dispatch Date

For a target day:

```text
bid date = August 15
month = 8
use historical August Pmin/Pmax
```

That is useful for baseline offers or initial dispatch assumptions.

But this is not the same as a true forecast.

## Historical Envelope Is Not A Forecast

This distinction is important.

| Component | Historical calibration? | Forecast? | Why |
| :--- | :---: | :---: | :--- |
| Monthly Pmin/Pmax from past data | Yes | No | Uses historical seasonal pattern. |
| Fuel curve fitted from past operations | Yes | No | Describes past thermodynamic behavior. |
| User-entered future gas price | Maybe | External | The tool receives the number; it does not forecast it. |
| Hourly weather forecast | No, unless added | Yes | Future temperature would make Pmax/Pmin forward-looking. |
| Future outage state | No, unless modeled | Yes / stochastic | Requires planned outage schedule or forced-outage model. |

Safe wording:

```text
Historical monthly Pmin/Pmax = calibrated seasonal operating envelope.
Weather-adjusted future Pmin/Pmax = forecast-aware operating capability.
```

Unsafe wording:

```text
Past August Pmax is the forecast for next August.
```

## Weather-Adjusted Operating Range

Gas turbine capability often changes with ambient temperature.

The weather-adjusted method estimates:

```text
Pmax(T) = maximum feasible MW as a function of temperature
Pmin(T) = minimum stable MW as a function of temperature
```

The simple workflow:

| Step | What to do | Why |
| :--- | :--- | :--- |
| 1 | Join hourly load data to hourly temperature. | Align plant output with weather conditions. |
| 2 | Filter to valid operating hours. | Remove offline, startup, and bad data noise. |
| 3 | Bin temperature. | Groups similar weather hours together. |
| 4 | Compute high and low load percentiles in each temperature bin. | Estimates upper and lower operating envelopes. |
| 5 | Fit a line or simple curve. | Converts noisy envelope points into usable Pmax(T)/Pmin(T). |

Example:

| Temperature bin | Pmin percentile | Pmax percentile |
| :--- | ---: | ---: |
| 10 to 15 deg C | 68 MW | 172 MW |
| 15 to 20 deg C | 70 MW | 170 MW |
| 20 to 25 deg C | 72 MW | 166 MW |
| 25 to 30 deg C | 75 MW | 160 MW |

Possible fitted relationships:

```text
Pmax(T) = 182 - 0.8 * T
Pmin(T) =  58 + 0.6 * T
```

Interpretation:

```text
Each 1 deg C increase lowers Pmax by about 0.8 MW.
Each 1 deg C increase raises Pmin by about 0.6 MW.
```

ASCII picture:

```text
MW
180 |* Pmax cool
170 |  *
160 |     * Pmax hot
150 |
140 |
130 |
120 |
110 |
100 |
 90 |
 80 |      * Pmin hot
 70 |  * Pmin cool
 60 |*
    +-------------------------
      cool              hot
            temperature
```

## Monthly Vs Weather-Adjusted Ranges

Both approaches can be useful, but they answer different questions.

| Method | What it uses | Best use | Main limitation |
| :--- | :--- | :--- | :--- |
| Monthly historical Pmin/Pmax | Past load by calendar month | Simple seasonal baseline. | Does not know tomorrow's actual temperature. |
| Pmax(T)/Pmin(T) | Past load plus temperature | Weather-aware dispatch and offers. | Needs good weather data and enough observations. |
| State-adjusted Pmax/Pmin | Plant state plus weather | Dynamic dispatch with degradation/outages. | Needs model state and calibration. |

Recommended progression:

```text
start:
  monthly historical Pmin/Pmax

then:
  weather-adjusted Pmax(T), Pmin(T)

then:
  weather + degradation + outage state
```

## Plant-Type Variations

Pmin/Pmax should be plant-type aware.

| Plant type | Pmax behavior | Pmin behavior | Modeling warning |
| :--- | :--- | :--- | :--- |
| Simple-cycle GT | Mostly GT/generator/BOP capability. | Minimum stable GT load. | No HRSG/ST contribution. |
| Aeroderivative GT | Often flexible and fast-starting. | May have different minimum and ramp behavior. | Do not assume large-frame limits. |
| Frame simple-cycle GT | Ambient derate and thermal constraints matter. | May have higher minimum stable output. | Start/ramp limits can bind. |
| 1x1 CCGT | One GT/HRSG train plus shared steam-cycle contribution. | Minimum depends on GT and steam-cycle operation. | Partial steam-cycle behavior matters. |
| 2x1 CCGT | Both GTs plus HRSG/ST block. | Minimum may be blocky by mode. | Offer blocks may need 1x1 and 2x1 modes. |
| CHP / cogeneration | Electric Pmax may depend on steam host. | Steam demand may force minimum electric output. | Heat obligation can dominate economics. |

## Athens CCGT Context

The Athens example provides a Pmax-style capacity table, not a full Pmin/Pmax offer model.

| Ambient temperature | Net plant capacity |
| :--- | ---: |
| 0 deg F | 565 MW |
| 20 deg F | 552 MW |
| 59 deg F ISO | 531 MW |
| 80 deg F | 499 MW |
| 95 deg F | 469 MW |

What that table gives:

```text
Pmax-style ambient capacity curve
```

What it does not fully give:

```text
Pmin by mode
1x1 minimum and maximum
2x1 minimum and maximum
ramp rates
minimum run time
offer block structure
temperature-adjusted Pmin
```

For Athens Step 2, a fuller operating range might need:

| Mode | Need to define |
| :--- | :--- |
| Offline | Output = 0 MW. |
| 1x1 CCGT | Pmin_1x1, Pmax_1x1, heat-rate curve, start cost. |
| 2x1 CCGT | Pmin_2x1, Pmax_2x1, heat-rate curve, start cost. |
| Derated operation | Pmax reduction and whether Pmin changes. |
| Outage state | Whether full block, one train, or no output is available. |

## Worked Example 1: Monthly Historical Range

Assume all July operating hours from three years are pooled.

| Step | Example result |
| :--- | :--- |
| Valid operating observations | 2,200 hours |
| Pmin percentile | 5th percentile |
| Pmax percentile | 98th percentile |
| July Pmin | 75 MW |
| July Pmax | 430 MW |

Interpretation:

```text
During normal July operation,
this plant often operated between about 75 MW and 430 MW.
```

What not to say:

```text
The plant is guaranteed to have 430 MW next July.
```

Better:

```text
Historical July data suggests a normal operating envelope near 75 to 430 MW,
before explicit future weather, outage, or degradation adjustments.
```

## Worked Example 2: Pmin Forces Uneconomic MWh

Assume a plant starts for a high-price evening peak.

| Hour | Price | Pmin | Pmax | Constraint |
| :--- | ---: | ---: | ---: | :--- |
| 17:00 | $150/MWh | 100 MW | 430 MW | High price, run near Pmax. |
| 18:00 | $170/MWh | 100 MW | 430 MW | High price, run near Pmax. |
| 19:00 | $90/MWh | 100 MW | 430 MW | Still likely economic. |
| 20:00 | $35/MWh | 100 MW | 430 MW | Weak price, but min-run may force operation. |

If the unit is still committed at 20:00, it may not be able to produce 20 MW just to stay warm. It may need to carry at least Pmin.

```text
wanted output: 20 MW
minimum stable output: 100 MW

actual online output must be at least 100 MW
```

That can create uneconomic MWh after the high-price window.

## Worked Example 3: Hot Weather Shrinks Pmax

Assume:

| Item | Cool hour | Hot hour |
| :--- | ---: | ---: |
| Pmax | 500 MW | 455 MW |
| Power price | $140/MWh | $180/MWh |
| Run hours | 4 | 4 |

The hot hour has higher price but lower available MW.

Lost MWh from derate:

```text
lost MW = 500 - 455
lost MW = 45

lost MWh over 4 hours = 45 * 4
lost MWh = 180
```

Lost gross revenue opportunity at $180/MWh:

```text
lost revenue = 180 MWh * $180/MWh
lost revenue = $32,400
```

This is why Pmax(T) matters most during hot high-price periods.

## Worked Example 4: Offer Blocks Inside Pmin/Pmax

Assume:

| Item | Value |
| :--- | ---: |
| Pmin | 100 MW |
| Pmax | 400 MW |
| Number of offer blocks | 3 |

One simple block layout:

```text
MW
0        100        200        300        400
|---------|----------|----------|----------|
 offline    block 1    block 2    block 3
           Pmin      mid       mid       Pmax
```

The exact market format may differ, but the guardrail is the same:

```text
offer MW breakpoints should stay inside feasible operating range
```

## Data Quality Checklist

Before trusting historical Pmin/Pmax, check the data.

| Check | Why |
| :--- | :--- |
| Timezone alignment | Weather and plant data must refer to the same hour. |
| Online filter | Offline hours should not pull Pmin toward zero. |
| Startup/shutdown filter | Transient hours can create false low loads. |
| Outage/derate flags | Forced derates can make Pmax look lower than normal capability. |
| Unit vs plant aggregation | Multiple units can make plant-level envelopes look misleading. |
| Seasonal sample size | Sparse months need fallback or caution. |
| Outlier handling | Sensor spikes can distort Pmax. |
| Plant configuration | CCGT 1x1 and 2x1 modes should not be mixed blindly. |

Beginner rule:

```text
bad data can turn Pmin/Pmax into false constraints
```

## How This Connects To Offer Curves

Offer curves need MW breakpoints.

Pmin/Pmax provide the physical range:

```text
Pmin -> first online MW boundary
Pmax -> highest offered MW boundary
```

Then marginal cost or offer-price logic fills in prices:

```text
MW range from Pmin to Pmax
        |
        v
split into blocks
        |
        v
price each block using heat rate, gas price, VOM, emissions, wear, etc.
```

This guide only defines the MW range. The next guide should explain how marginal cost and offer curves price the range.

## What The Framework Includes

The current InfraSure framework already includes pieces of the operating range idea.

| Included item | Where it appears |
| :--- | :--- |
| Hourly dispatch layer | Step 2 dispatch model. |
| Ambient capacity derating | Capacity and degradation guides. |
| Effective capacity feedback | Daily state loop. |
| Plant-type notes | Basics and plant-type guides. |
| 1x1 vs 2x1 importance | Athens CCGT example and HRSG cycling guide. |

## What The Framework Leaves Out

The current framework does not fully specify a production-ready Pmin/Pmax layer.

| Missing detail | Why it matters |
| :--- | :--- |
| Pmin by plant type and mode | Dispatch cannot choose feasible low-load operation without it. |
| Pmax by mode | CCGT 1x1 and 2x1 operation need separate ranges. |
| Historical calibration method | Needed if using operating data to fit ranges. |
| Weather-adjusted Pmin/Pmax | Needed for hot/cold hourly dispatch realism. |
| Ramp and min up/down | Pmin/Pmax are not enough by themselves. |
| Market-offer block rules | Offer format depends on market and product. |
| Unit-level vs plant-level ranges | Multi-unit sites need careful aggregation. |

## Source Basis And Certainty

| Source | Use in this guide | Certainty |
| :--- | :--- | :--- |
| [Capacity](../basics/01_capacity.md) | Defines Pmax/Pmin basics and ambient capacity concept. | Green for concept; plant values need asset data. |
| [Dispatch And The Daily Loop](../basics/05_dispatch_and_daily_loop.md) | Shows how hourly dispatch sits inside daily state update. | Green for framework logic. |
| [Simple-Cycle Gas Turbine](../plant_types/01_simple_cycle_gt.md) | Shows simple-cycle Pmin/Pmax differences from CCGT. | Green for learning structure. |
| [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md) | Provides Pmax-style Athens capacity table and CCGT mode warnings. | Amber for investment use pending actual plant data. |
| `plant model/pminimum_pmaximum.md` | Historical monthly percentile method and smoothing logic. | Green as local method; Amber as forecast proxy. |
| `plant model/weather_effects/implementing_weather_adjustments_for_gas_plants.md` | Temperature-bin approach for Pmax(T)/Pmin(T). | Amber until calibrated per plant. |
| `plant model/FILTERING_GUIDE.md` | Data filtering discipline for operating data. | Green for quality-control concept. |
| `plant model/is_it_forecasted.md` | Historical vs forecast boundary. | Green for methodology boundary. |

## Open Questions Before Investment Use

| Question | Why it matters |
| :--- | :--- |
| Are Pmin and Pmax defined by unit, plant block, or market offer? | Prevents mixing physical and commercial limits. |
| Does the asset have multiple operating modes? | CCGTs may need 1x1 and 2x1 ranges. |
| Are historical data filtered for startup, shutdown, outages, and derates? | Prevents false Pmin/Pmax estimates. |
| Is future weather available? | Needed for forecast-aware Pmax(T)/Pmin(T). |
| Does Pmin change with temperature or emissions constraints? | Can affect low-load dispatch and offer blocks. |
| Should Pmax include a safety margin? | Avoids overcommitment. |
| Are ramp, min up/down, and start time known? | Pmin/Pmax do not fully define dispatch feasibility. |
| Are market offer rules known? | Offer MW breakpoints and formats are market-specific. |
| Should Pmin/Pmax be state variables? | Degradation, outages, and repairs can change feasible range over time. |

## Quick Recap

Pmin and Pmax are the dispatch guardrails.

```text
Pmin says:
  if the plant is online, do not assume it can run near zero.

Pmax says:
  do not assume nameplate or ISO MW is available every hour.
```

Use historical monthly ranges for a transparent first operating envelope. Use weather-adjusted and state-adjusted ranges when the model needs true hourly forward-looking dispatch realism.
