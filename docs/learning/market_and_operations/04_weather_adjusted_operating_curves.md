# Weather-Adjusted Operating Curves

## What This Guide Is

This guide explains how weather can change:

```text
Pmax(T)
Pmin(T)
heat rate(T)
```

Read these first:

- [Capacity](../basics/01_capacity.md)
- [Heat Rate](../basics/02_heat_rate.md)
- [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md)
- [Historical Vs Forecast Inputs](./03_historical_vs_forecast_inputs.md)

> Plant-Type Note
> Weather adjustment is plant-specific. Simple-cycle GTs, CCGTs, frame units, aeroderivatives, CHP plants, inlet cooling systems, duct firing, cooling towers, and steam-host obligations can all change the correct weather response.

## First-Time Reader Map

Gas turbines breathe air. Weather changes the air.

```text
hotter air
  -> lower density
  -> less compressor mass flow
  -> lower output
  -> often worse heat rate
```

Key terms:

| Term | First-time meaning |
| :--- | :--- |
| Ambient temperature | Outside air temperature at or near the plant. |
| Pmax(T) | Maximum MW as a function of temperature. |
| Pmin(T) | Minimum stable MW as a function of temperature. |
| HR(T) | Heat rate as a function of temperature. |
| Temperature bin | Group of hours with similar temperature. |
| Envelope | Upper or lower edge of observed operating data. |
| Weather correction | Adjustment to capacity or heat rate based on weather. |
| Forecast-aware curve | Curve evaluated using future weather input. |

## Why This Matters

Hot weather can hit the plant in two ways at once:

```text
less MW available
  +
more fuel needed per MWh
```

That is financially important because high-temperature periods can also be high-price periods.

| Weather effect | Dispatch impact |
| :--- | :--- |
| Pmax falls | Fewer MWh can be sold. |
| Pmin rises | More minimum online MW may be forced. |
| Heat rate worsens | Fuel cost rises. |
| Cooling system struggles | CCGT net output and heat rate may worsen. |
| Emissions limits bind | Operating range can narrow. |

## What We Are Trying To Estimate

There are three practical curves:

| Curve | Question answered |
| :--- | :--- |
| `Pmax(T)` | What is the maximum feasible output at this temperature? |
| `Pmin(T)` | What is the minimum stable online output at this temperature? |
| `HR(P,T)` or `HR_inc(P,T)` | What is the fuel intensity at this load and temperature? |

Simple view:

```text
temperature
  |
  +--> Pmax adjustment
  +--> Pmin adjustment
  +--> heat-rate adjustment
```

## Data Needed

At minimum:

| Data | Why |
| :--- | :--- |
| Timestamped plant load | Needed for Pmin/Pmax and heat-rate analysis. |
| Timestamped heat input | Needed for heat-rate analysis. |
| Timestamped ambient temperature | Needed for weather response. |
| Online / operating flag | Needed to filter out offline hours. |
| Unit or plant mode | Needed for multi-unit or CCGT modes. |

Useful additions:

- humidity
- air pressure or elevation
- inlet cooling status
- duct firing status
- outage/derate flags
- emissions mode
- 1x1 vs 2x1 CCGT mode

## Data Join And Filtering

Weather data and plant data must align by time.

```text
plant timestamp_local
        |
        v
join to weather timestamp in same timezone
```

Basic filters:

| Filter | Why |
| :--- | :--- |
| `opTime == 1.0` if available | Keeps full operating hours. |
| `grossLoad > 0` | Removes offline hours. |
| `heatInput > 0` for HR analysis | Removes invalid fuel data. |
| remove obvious outliers | Avoids false curve shape. |
| separate modes if possible | Prevents mixing simple-cycle, 1x1, 2x1, or duct-fired behavior. |

Timezone warning:

```text
wrong timezone join can create fake weather effects
```

## First Visual Checks

Before fitting curves, make simple plots.

| Plot | What it shows |
| :--- | :--- |
| Load vs temperature | Whether high-temperature Pmax falls. |
| Heat rate vs load and temperature | Whether hot hours are less efficient. |
| Binned load-temperature heat map | Cleaner view of noisy hourly data. |
| Residual heat-rate view | Temperature effect after base fuel curve. |

Beginner reason for binning:

```text
raw hourly points are noisy
bins group similar conditions
percentiles find the envelope inside each group
```

## Estimating Pmax(T)

Simple method:

```text
1. Bin temperature.
2. In each bin, take high percentile of load.
3. Fit a line or simple curve through those high-percentile points.
```

Example:

| Temperature bin | Pmax percentile |
| :--- | ---: |
| 10 to 15 deg C | 172 MW |
| 15 to 20 deg C | 170 MW |
| 20 to 25 deg C | 166 MW |
| 25 to 30 deg C | 160 MW |

Possible fitted curve:

```text
Pmax(T) = 182 - 0.8 * T
```

Interpretation:

```text
each 1 deg C increase reduces Pmax by about 0.8 MW
```

## Estimating Pmin(T)

Simple method:

```text
1. Bin temperature.
2. In each bin, take low percentile of online load.
3. Fit a line or simple curve through those low-percentile points.
```

Example:

| Temperature bin | Pmin percentile |
| :--- | ---: |
| 10 to 15 deg C | 68 MW |
| 15 to 20 deg C | 70 MW |
| 20 to 25 deg C | 72 MW |
| 25 to 30 deg C | 75 MW |

Possible fitted curve:

```text
Pmin(T) = 58 + 0.6 * T
```

Interpretation:

```text
each 1 deg C increase raises Pmin by about 0.6 MW
```

## Estimating Heat-Rate Weather Effect

There are two levels:

| Level | What it estimates |
| :--- | :--- |
| Average heat rate vs temperature | Broad efficiency trend. |
| Incremental heat rate vs temperature | Marginal cost impact for offers. |

Simple incremental approach:

```text
1. Fit base fuel curve F(P).
2. Compute HR_inc(P) = 2 * a * P + b.
3. Group data by load band.
4. In each load band, examine HR_inc or residual heat rate vs temperature.
5. Fit a temperature adder if the pattern is stable.
```

Example:

| Load band | HR temperature slope | Meaning |
| :--- | ---: | :--- |
| Low load | 0.00 MMBtu/MWh per deg C | Little visible effect. |
| Mid load | 0.01 MMBtu/MWh per deg C | Small fuel-cost adder. |
| High load | 0.03 MMBtu/MWh per deg C | Hot high-load hours are more expensive. |

Fuel-cost impact:

```text
HR adder = 0.03 MMBtu/MWh per deg C
gas price = $4/MMBtu

cost adder = 0.03 * 4
cost adder = $0.12/MWh per deg C
```

## ASCII Picture

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

The feasible range narrows if Pmax falls and Pmin rises.

## Monthly Vs Weather-Adjusted Method

| Method | Input | Strength | Weakness |
| :--- | :--- | :--- | :--- |
| Monthly historical range | Past load by month | Simple seasonal baseline. | Does not know actual future temperature. |
| Pmax(T)/Pmin(T) | Past load plus temperature | Weather-aware capability. | Needs enough data and clean joins. |
| HR(P,T) | Load, fuel, temperature | Weather-aware marginal cost. | More complex and noisy. |
| State-adjusted curves | Weather plus plant state | Best for dynamic Step 2. | Needs degradation and outage model. |

Recommended progression:

```text
monthly baseline
  |
  v
weather-adjusted Pmax/Pmin
  |
  v
weather-adjusted heat rate
  |
  v
weather + degradation + outage state
```

## Plant-Type Variations

| Plant type | Weather issue |
| :--- | :--- |
| Simple-cycle GT | Direct GT output and heat-rate weather sensitivity. |
| Aeroderivative GT | Often flexible, but OEM weather curves differ. |
| Frame GT | Ambient derate and thermal constraints can be material. |
| CCGT | GT output, HRSG steam production, ST output, condenser/cooling all matter. |
| CHP / cogeneration | Steam/heat demand can change apparent electric output response. |

## Athens CCGT Context

The Athens example includes a Pmax-style temperature table:

| Ambient temperature | Net plant capacity |
| :--- | ---: |
| 0 deg F | 565 MW |
| 20 deg F | 552 MW |
| 59 deg F ISO | 531 MW |
| 80 deg F | 499 MW |
| 95 deg F | 469 MW |

This is useful as a worked CCGT example.

But it does not fully specify:

- Pmin(T)
- 1x1 Pmax(T)
- 1x1 Pmin(T)
- 2x1 Pmin(T)
- heat-rate temperature correction by operating mode
- cooling tower / condenser limits
- outage and derate overlays

## How Weather Curves Feed Step 2

For each hour:

```text
temperature forecast or scenario
        |
        v
compute Pmax(T) and Pmin(T)
        |
        v
compute heat-rate adjustment
        |
        v
dispatch chooses online/offline and MW
        |
        v
daily state update records what happened
```

If no forecast weather is used, the model can still use monthly historical curves, but it should not claim weather-aware hourly capability.

## Worked Example: Hot Afternoon

Assume:

| Item | Cool hour | Hot hour |
| :--- | ---: | ---: |
| Temperature | 15 deg C | 30 deg C |
| Pmax(T) | 170 MW | 158 MW |
| Pmin(T) | 67 MW | 76 MW |
| HR adder | 0.00 MMBtu/MWh | 0.20 MMBtu/MWh |
| Gas price | $4/MMBtu | $4/MMBtu |

Pmax loss:

```text
lost MW = 170 - 158
lost MW = 12
```

Fuel-cost adder:

```text
cost adder = 0.20 * 4
cost adder = $0.80/MWh
```

Dispatch impact:

```text
hot hour:
  lower maximum output
  higher minimum stable load
  higher marginal cost
```

## Data Quality Checklist

| Check | Why |
| :--- | :--- |
| Timezone alignment | Prevents false weather relationship. |
| Online filter | Removes zero-load hours. |
| Startup/shutdown filter | Avoids false Pmin and heat-rate noise. |
| Unit/mode separation | Avoids mixing 1x1, 2x1, duct firing, and derates. |
| Enough observations per bin | Sparse bins create unstable slopes. |
| Outlier handling | Sensor spikes can distort envelopes. |
| Weather source location | Temperature should represent plant inlet conditions reasonably. |
| Backtesting | Confirms curve improves out-of-sample accuracy. |

## What The Framework Includes

| Included item | Why it helps |
| :--- | :--- |
| Climate and weather path concept | Supports future hourly weather input. |
| Capacity derating guide | Explains why hot air lowers output. |
| Heat-rate guide | Explains fuel intensity and marginal cost. |
| Pmin/Pmax guide | Defines operating range. |
| Athens temperature table | Gives a first CCGT Pmax example. |

## What The Framework Leaves Out

| Missing detail | Why it matters |
| :--- | :--- |
| Calibrated Pmax(T) by mode | Needed for actual hourly dispatch. |
| Calibrated Pmin(T) | Needed for low-load and offer constraints. |
| Heat-rate temperature correction | Needed for hot-hour marginal cost. |
| Humidity / air density model | Temperature alone may be incomplete. |
| Inlet cooling operation | Can change hot-weather response. |
| Backtest protocol | Needed before using curves in investment work. |

## Source Basis And Certainty

| Source | Use in this guide | Certainty |
| :--- | :--- | :--- |
| [Capacity](../basics/01_capacity.md) | Air-breathing GT output and Athens capacity table. | Green for concept; Amber for asset values. |
| [Heat Rate](../basics/02_heat_rate.md) | Heat-rate and fuel-cost impact. | Green for concept. |
| [Operating Range: Pmin And Pmax](./01_operating_range_pmin_pmax.md) | Pmin/Pmax method and weather-aware range. | Green for concept. |
| `plant model/weather_effects/implementing_weather_adjustments_for_gas_plants.md` | Temperature binning, Pmax(T), Pmin(T), HR vs temperature workflow. | Amber until calibrated and backtested per plant. |
| `plant model/FILTERING_GUIDE.md` | Data-quality discipline. | Green for filtering concept. |

## Open Questions Before Implementation

| Question | Why it matters |
| :--- | :--- |
| Which weather variable should be used: temperature, humidity, air density, or all? | Determines physical correction quality. |
| Is weather measured at site or nearby grid/station? | Bad weather location can distort curves. |
| Should curves be unit-level or plant-level? | Multi-unit sites can hide mode behavior. |
| How should CCGT 1x1 and 2x1 modes be separated? | Weather response differs by mode. |
| Is inlet cooling available and dispatched? | It can offset hot-weather derate. |
| How will the curve be backtested? | Needed before investment use. |

## Quick Recap

Weather-adjusted curves make Step 2 more realistic:

```text
temperature -> Pmax(T), Pmin(T), HR(T) -> dispatch economics
```

Monthly historical ranges are a good baseline. Weather-adjusted curves are the next step when hourly temperature matters.
