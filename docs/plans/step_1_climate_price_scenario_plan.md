# Step 1 Climate And Price Scenario Plan

> **Post-2026-05-25 status**: This plan defines the **Stream A** (forward-looking) upstream scenario package. Activation of Stream A is **Phase 6** in [`00_strategic_spine.md`](./00_strategic_spine.md) — *after* the framework operationalization (Phases 1–4) and the fidelity work (Phase 5) so that forward simulations run against the full conditioning structure (capability envelope + realized operating profile + load + temperature). The contents of this plan remain valid for Phase 6 execution; read the strategic spine first to understand where this fits in the overall sequence.

## Purpose

This plan defines the upstream scenario package that feeds the gas turbine Step 2 dispatch model.

Step 2 asks:

```text
Given today's market path,
given today's weather path,
given today's gas path,
given today's opening plant state,

how should the plant run?
```

This file is about the first three inputs:

```text
market path
weather path
gas path
```

The goal is to create a defensible exogenous scenario package before dispatch starts. Step 2 should not have to invent prices, gas, or weather. It should consume them.

## Relationship To Step 2

Step 1 creates exogenous paths. Step 2 uses them.

```text
Step 1:
  climate / weather path
  power price path
  gas price path
  ancillary price path, if needed
  scenario tags and metadata

        |
        v

Step 2:
  dispatch and operating economics
  generation
  starts
  fuel burn
  EOH signals

        |
        v

Step 3 / Step 4:
  degradation
  outage
  maintenance
  LTSA / CSA state
```

Step 1 does not decide whether the plant runs. Step 1 creates the world in which the plant decides whether to run.

## What Already Exists

Most of the architecture already exists in the revenue-forecasting methodology folder. It is not yet packaged as a GT-specific Step 1 plan.

| Existing local reference | What it already gives us |
| :--- | :--- |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/02_scenario_engine_architecture.md` | Block sampling, level-shape decomposition, conditioning, forward anchoring. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/03_layer_methodology.md` | Weather scenarios, price scenarios, generation branches, and revenue assembly. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/02_weather_data.md` | ERA5, NSRDB, WIND Toolkit, S2S, and ERCOT hindcast context. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/03_price_data.md` | ISO LMP data, GridStatus, ISO sources, gas price sources. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/08_forward_curves.md` | Power forward curves, hub/node basis, DA/RT, P-vs-Q distinction, Gen 1/2/3 curve stack. |
| `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/extra/basics_of_gas_prices.md` | Gas price primer: Henry Hub, basis, delivered gas, major hubs, index locations, and Gen 1/2 construction choices. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/probabilistic_methods/01_out_of_sample_problem.md` | Four out-of-sample problem types. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/probabilistic_methods/02_five_methods.md` | EVT, copulas, perturbed historical, bootstrap amplification, parametric fitting. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/probabilistic_methods/03_hybrid_construction.md` | Core-plus-augmentation approach for hybrid distributions. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/execution/01_gen1_scope.md` | Gen 1 scope: block sampling, forward anchoring, joint conditioning. |
| `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/execution/02_gen2_additions.md` | Gen 2 additions: empirical calibration, perturbations, residual correction, richer availability. |

So the right move is not to invent a new architecture. The right move is to translate the existing scenario-engine architecture into a GT-specific Step 1 plan.

## Core Decision

The first important decision:

```text
Step 1 should not run independent climate, power, and gas simulations.
```

Independent simulations would destroy the co-movement that matters for dispatch:

- hot weather and high prices
- cold weather and gas stress
- high gas prices and high LMPs when gas is marginal
- scarcity clusters across consecutive days
- power and ancillary service co-movement

Instead, Step 1 should use a common scenario-engine frame:

```text
historical blocks = shape and co-movement
conditioning      = pulls analogs toward the forecast regime
forward curves    = market-consistent price and gas levels
dispatch model    = converts the scenario into generation
```

## What "Climate Simulation" Means In Gen 1

For Gen 1, "climate simulation" should not mean a brand-new climate model producing synthetic weather.

It means:

```text
conditioned historical weather path selection
```

We draw real historical weather blocks, then weight them using forecast-relevant climate signals.

```text
ERA5 / reanalysis history
        +
S2S / ENSO / climate-state signals
        +
asset-location mapping
        |
        v
weighted analog weather paths
```

This is a selection process, not a full physical climate simulation.

Why this matters:

| Phrase | Safe meaning for Gen 1 | Not safe for Gen 1 |
| :--- | :--- | :--- |
| Climate simulation | Weighted historical analog weather paths. | New synthetic weather states outside history. |
| S2S use | Reweight analog blocks toward forecast climate regime. | Directly produce hourly power revenue paths out several years. |
| Climate signal | Conditioning input. | Deterministic forecast truth. |
| Weather path | Hourly weather from a real historical block. | Independently sampled weather unrelated to price. |

## What "Price Simulation" Means In Gen 1

For Gen 1, "price simulation" should not mean a black-box price model that generates hourly LMPs independently.

It means:

```text
historical hourly price shape
        +
forward-curve level anchor
        +
basis / structural adjustment where needed
        |
        v
forecast hourly price path
```

The historical block provides the shape:

- hourly volatility
- scarcity clusters
- day/night pattern
- weekday/weekend pattern
- weather-price relationship
- energy/ancillary co-movement if ancillary data is included

The forward curve provides the market-consistent level:

- monthly on-peak / off-peak average
- hub or zonal anchor
- DA or RT settlement basis
- market wedge / Q-ish anchor

## Whole Step 1 Workflow

The short version:

```text
define target
  -> build historical block archive
  -> compute conditioning signals
  -> weight analog blocks
  -> draw scenario paths
  -> anchor power level
  -> anchor gas level
  -> package exogenous paths for Step 2
```

The detailed workflow:

```text
                         STEP 1 SCENARIO WORKFLOW

  +------------------------------------------------------------------------+
  | 0. TARGET DEFINITION                                                   |
  |                                                                        |
  | Define the forecast problem:                                           |
  |   - asset / plant                                                      |
  |   - ISO / market                                                       |
  |   - hub, zone, or node settlement                                      |
  |   - DA or RT price basis                                               |
  |   - forecast months / years                                            |
  |   - hour blocks needed                                                 |
  |   - gas delivery point and basis assumption                            |
  |   - whether ancillary services matter                                  |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 1. HISTORICAL ARCHIVE                                                  |
  |                                                                        |
  | Build aligned historical blocks:                                       |
  |   - hourly weather                                                     |
  |   - hourly hub LMP                                                     |
  |   - hourly node LMP, if available                                      |
  |   - ancillary prices, if needed                                        |
  |   - daily gas prices                                                   |
  |   - structural metadata by period                                      |
  |                                                                        |
  | Blocks are usually calendar months.                                    |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 2. FORECAST ANCHORS AND SIGNALS                                        |
  |                                                                        |
  | Read forward-looking signals:                                          |
  |   - power forward curve by hub / block / month                         |
  |   - Henry Hub or delivered gas forward                                 |
  |   - gas delivery basis assumption                                      |
  |   - S2S / ENSO / climate outlook                                       |
  |   - reserve margin / fleet buildout                                    |
  |   - storage, solar, wind, load, and policy assumptions                 |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 3. ANALOG WEIGHTING                                                    |
  |                                                                        |
  | For each candidate historical block:                                   |
  |   - climate similarity                                                 |
  |   - market similarity                                                  |
  |   - structural similarity                                              |
  |   - gas / spark-spread similarity                                      |
  |                                                                        |
  | Convert similarities into sampling weights.                            |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 4. PATH DRAW                                                           |
  |                                                                        |
  | For each scenario path:                                                |
  |   - draw one weighted historical block                                 |
  |   - keep weather and prices from the same block                        |
  |   - keep spatial correlation if portfolio assets are included          |
  |                                                                        |
  | The draw preserves co-movement by construction.                        |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 5. WEATHER PATH CONSTRUCTION                                           |
  |                                                                        |
  | Use the selected analog's hourly weather:                              |
  |   - temperature                                                        |
  |   - humidity                                                           |
  |   - wind speed                                                         |
  |   - pressure                                                           |
  |   - optional AQI / fouling proxy                                       |
  |                                                                        |
  | For GT Step 2, temperature is the minimum required field.              |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 6. POWER PRICE PATH CONSTRUCTION                                       |
  |                                                                        |
  | Use selected analog's hourly price shape.                              |
  | Anchor bucket average to forward curve.                                |
  | Add node / basis overlay if needed.                                    |
  | Apply caps, floors, and settlement-basis checks.                       |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 7. GAS PRICE PATH CONSTRUCTION                                         |
  |                                                                        |
  | Use selected analog's gas shape where available.                       |
  | Anchor monthly average to gas forward.                                 |
  | Add delivery basis.                                                    |
  | Produce delivered gas path for dispatch.                               |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 8. CONSISTENCY CHECKS                                                  |
  |                                                                        |
  | Check:                                                                 |
  |   - power bucket average equals forward anchor                         |
  |   - gas average equals forward + basis anchor                          |
  |   - weather and price are from same analog period                      |
  |   - timestamps align                                                   |
  |   - DA / RT basis is explicit                                          |
  |   - hub / node / basis is explicit                                     |
  |   - units are consistent                                               |
  +------------------------------------------------------------------------+
                                      |
                                      v
  +------------------------------------------------------------------------+
  | 9. STEP 2 INPUT PACKAGE                                                |
  |                                                                        |
  | Output one package per path:                                           |
  |   - hourly weather                                                     |
  |   - hourly power price                                                 |
  |   - daily or hourly delivered gas price                                |
  |   - ancillary prices if modeled                                        |
  |   - scenario metadata                                                  |
  |   - validation diagnostics                                             |
  +------------------------------------------------------------------------+
```

## Gen 1 Path Construction

The Gen 1 path construction should be simple enough to implement and audit.

```text
For each forecast month:
  For each scenario path:
    1. draw a historical calendar-month block
    2. keep its weather and price together
    3. rescale power price to the power forward bucket
    4. shift gas price to the gas forward + basis bucket
    5. export the exogenous path package
```

### Weather Path

Minimum fields for GT Step 2:

| Field | Frequency | Source | Step 2 use |
| :--- | :--- | :--- | :--- |
| Ambient temperature | Hourly | ERA5 or other reanalysis | Capacity derate, heat-rate correction, load/price regime context. |
| Relative humidity | Hourly or daily | ERA5 or reanalysis | Optional cooling / performance modifier. |
| Wind speed | Hourly | ERA5 or reanalysis | Optional cooling / weather regime context. |
| Pressure | Hourly | ERA5 or reanalysis | Optional air-density correction. |
| AQI / fouling proxy | Daily or hourly if available | External AQI or site class | Optional compressor fouling modifier. |

For Gen 1, temperature is mandatory. Other variables should be included where available but not allowed to block the first version.

### Power Price Path

Start with hub price.

```text
analog_hourly_power_shape
        x target_forward_bucket_average
        = forecast_hourly_hub_price
```

For on-peak/off-peak products, anchor each bucket separately:

```text
on-peak hours:
  analog on-peak shape -> on-peak forward average

off-peak hours:
  analog off-peak shape -> off-peak forward average
```

Use node pricing later:

```text
forecast_node_price_t = forecast_hub_price_t + basis_t
```

Basis can come from:

- analog node-minus-hub basis
- static basis assumption
- vendor / broker basis where available
- Gen 2 basis model

### Gas Price Path

Use delivered gas for dispatch, not Henry Hub alone.

Detailed gas-price terminology and source guidance lives in [Basics Of Gas Prices](../extra/basics_of_gas_prices.md). The key rule for Step 1 is that major gas hubs are useful proxy-selection references, but the actual fuel contract or delivered plant index is the final authority when available.

```text
delivered_gas_t = Henry_Hub_forward_month
                + delivery_basis_month
                + historical_daily_shape_t
```

For Gen 1:

```text
historical_daily_shape_t
  = historical_gas_t - average_historical_gas_for_month
```

This keeps daily variation while anchoring to the forward level.

| Gas item | Gen 1 treatment | Watch item |
| :--- | :--- | :--- |
| Henry Hub level | Use monthly forward. | Confirm source and snapshot date. |
| Delivery basis | Use known contract, broker/vendor curve, or explicit assumption. | Plant economics can be wrong if basis is wrong. |
| Daily shape | Historical daily deviation from monthly average. | Better than flat monthly gas for dispatch. |
| Hourly gas | Usually not needed. | Consider only for extreme gas-stress studies. |
| Gas volatility | Historical shape. | Gen 2 can scale volatility by regime. |

### Ancillary Price Path

Only include ancillary prices if they can materially affect the asset.

| Asset | Gen 1 ancillary treatment |
| :--- | :--- |
| Baseload / mid-merit CCGT with no AS strategy | Optional, maybe omit initially. |
| Flexible CCGT | Include if reserve participation is material. |
| Simple-cycle peaker | Include early; ancillary may be a major revenue stream. |
| Storage | Required, but storage is outside this GT Step 1 plan. |

If ancillary is included, it should be drawn from the same historical block as energy prices.

## Scenario Package Schema

Step 1 should output a path table and metadata table.

### Hourly Path Table

Minimum hourly table:

| Column | Frequency | Units | Required? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `scenario_id` | path id | text/int | Yes | Stable path key. |
| `timestamp` | hourly | local market time + UTC if possible | Yes | Must handle DST explicitly. |
| `iso` | static | text | Yes | ERCOT, NYISO, PJM, etc. |
| `power_location` | static | text | Yes | Hub first; node later. |
| `power_basis` | static | DA/RT | Yes | Day-ahead or real-time settlement basis. |
| `power_price` | hourly | $/MWh | Yes | Forward-anchored price path. |
| `ambient_temp` | hourly | deg F or deg C | Yes | Unit must be explicit. |
| `relative_humidity` | hourly | percent | Optional | Include if available. |
| `wind_speed` | hourly | m/s or mph | Optional | Include if available. |
| `pressure` | hourly | hPa | Optional | Include if available. |
| `ancillary_price_*` | hourly | $/MW-h | Optional | Product-specific. |

### Daily Path Table

Minimum daily table:

| Column | Frequency | Units | Required? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `scenario_id` | path id | text/int | Yes | Matches hourly table. |
| `date` | daily | local date | Yes | Market calendar. |
| `delivered_gas_price` | daily | $/MMBtu | Yes | Henry Hub forward + basis + shape. |
| `henry_hub_price` | daily | $/MMBtu | Recommended | Keeps level and basis auditable. |
| `gas_basis` | daily/monthly | $/MMBtu | Recommended | Delivery-point economics. |
| `aqi_or_fouling_proxy` | daily | index | Optional | Treat as proxy, not truth. |

### Metadata Table

Minimum metadata:

| Field | Example | Why |
| :--- | :--- | :--- |
| `scenario_id` | `ERCOT_HOUSTON_2027_07_path_001` | Joins all tables. |
| `analog_year` | 2023 | Auditability. |
| `analog_month` | July | Auditability. |
| `analog_weight` | 0.18 | Shows conditioning. |
| `power_forward_source` | ICE / OTCGH / Argus / Platts | Market anchor provenance. |
| `power_forward_snapshot_date` | YYYY-MM-DD | Point-in-time reproducibility. |
| `gas_forward_source` | CME / broker / vendor | Fuel anchor provenance. |
| `gas_forward_snapshot_date` | YYYY-MM-DD | Point-in-time reproducibility. |
| `basis_assumption_source` | contract / vendor / assumption | Delivery basis provenance. |
| `conditioning_tags` | warm S2S, tight reserve margin | Explains why the path was sampled. |

## Conditioning Plan

Conditioning should reweight analog blocks. It should not break the within-block weather-price relationship.

```text
analog_weight
  = f(climate_similarity, market_similarity, structural_similarity, gas_similarity)
```

### Climate Similarity

| Signal | Use | Notes |
| :--- | :--- | :--- |
| S2S temperature anomaly | Reweight near-term months toward warmer/cooler analogs. | Useful mostly weeks to a few months ahead. |
| ENSO / Nino 3.4 state | Seasonal regime signal. | Skill varies by region and season. |
| Soil moisture / drought | Summer heat persistence signal. | Useful for hot-weather dispatch risk. |
| Historical temperature distribution | Baseline climate analog. | Always available through reanalysis. |

### Market Similarity

| Signal | Use | Notes |
| :--- | :--- | :--- |
| Power forward level | Pull analogs with similar native price regime. | Prevents extreme rescaling. |
| Term structure | Distinguish near-term tightness from flat structure. | More useful when multiple tenor points exist. |
| Gas forward level | Pull analogs with similar fuel regime. | Critical for gas assets. |
| Reserve margin | Pull scarcity-like analogs. | Important for CCGT and peaker revenue. |
| Ancillary price regime | Pull reserve-rich analogs. | Important for peakers and storage. |

### Structural Similarity

| Signal | Use | Notes |
| :--- | :--- | :--- |
| Solar MW | Captures midday price pressure. | Important for price shape. |
| Storage MW | Captures peak shaving and trough filling. | Gen 2 priority. |
| Wind MW | Captures overnight / regional price pressure. | Market-specific. |
| Load growth | Captures demand regime. | Data center load may be zonal. |
| Transmission state | Captures basis and congestion. | Often best treated through scenario tags. |

## Gen 1 Boundary

Gen 1 should be honest about what it is and is not.

| Item | Gen 1 approach | Not Gen 1 |
| :--- | :--- | :--- |
| Weather | Historical analog weather, conditioned by climate signals. | Synthetic climate model output. |
| Power prices | Historical hourly shape anchored to forward curve. | Full production-cost simulation. |
| Gas prices | Historical daily shape shifted to forward + basis. | Stochastic gas market model with storage/pipeline physics. |
| Basis | Hub first; basis overlay if easy. | Full nodal congestion model. |
| Ancillary | Include where material and data exists. | Full co-optimized market simulation. |
| Out-of-sample | Basic conditioning and scenario tags. | Full structural simulation or tail augmentation. |

## Gen 2 Upgrade Path

Gen 2 starts when we have enough realized-vs-forecast history and enough backtests to know where Gen 1 fails.

| Upgrade | What it changes | Why it matters |
| :--- | :--- | :--- |
| Empirical conditioning calibration | Replaces hand-tuned weights with validated weights. | Better probabilistic calibration. |
| Perturbed historical | Adjusts analogs for gas, solar, storage, reserve margin, and transmission differences. | Handles driver combinations and modest regime shifts. |
| Residual correction | Learns layer-specific bias: hub, basis, gas, weather, dispatch. | Corrects repeated misses without replacing the engine. |
| Gas volatility model | Scales gas daily shape by forward regime. | Higher gas level may come with higher volatility. |
| Basis model | Forecasts node-minus-hub or zone-minus-hub. | Needed for asset settlement realism. |
| Ancillary regime model | Conditions AS prices on scarcity, reserves, and storage buildout. | Important for peakers and storage. |
| EVT tails | Extends scarcity or spark-spread tails for stress/insurance. | Not needed for basic P10/P90, useful for deep tail products. |
| Copula tail layer | Adds joint tail dependence across regions/assets/variables. | Portfolio and insurance use cases. |
| Structural simulation bridge | Uses vendor or internal production-cost model output where history is no longer representative. | Needed for large long-horizon regime shifts. |

## Gen 2 Perturbation Ownership

Gen 2 should be careful about double-counting. Each layer needs an owner.

| Effect | Owner layer | Do not double-count by |
| :--- | :--- | :--- |
| Market-consistent average power level | Power forward anchor | Adding the same level change again as a perturbation. |
| Market-consistent average gas level | Gas forward anchor | Also shifting plant fuel cost by the same forward change twice. |
| Gas-driven LMP shape change | Price perturbation layer | Confusing plant fuel cost with market-clearing price effect. |
| Plant delivered fuel cost | Dispatch model | Embedding asset-specific gas basis in hub LMP. |
| Node congestion / basis | Basis layer | Treating hub price as if it were node settlement. |
| Solar/storage shape effect | Structural perturbation layer | Flattening shape through a second forward rescale. |
| Weather-driven derate | Step 2 dispatch / plant performance | Adjusting price path for plant derate. |

## Validation Plan

Step 1 validation should happen before Step 2 dispatch validation.

| Test | What it checks |
| :--- | :--- |
| Forward average test | Power price path averages match forward anchors by bucket. |
| Gas average test | Delivered gas path averages match Henry Hub forward plus basis. |
| Timestamp test | Weather, power, gas, and AS align by market calendar. |
| Co-movement test | Hot analogs still have high-price behavior after anchoring. |
| Rescale factor test | Large power rescaling factors are flagged. |
| Gas-shape sanity | Daily gas shape is not creating impossible negative delivered gas. |
| Historical backcast | Earlier analogs can reproduce later realized price/gas/weather patterns after anchoring and perturbation. |
| Step 2 readiness | Output schema contains every exogenous field dispatch needs. |

Backtest pattern:

```text
fit / design using earlier history
  -> forecast a later historical period
  -> compare simulated Step 1 paths to realized weather, LMP, gas, and AS
```

## Proposed Detailed Step 1 Folder

This plan should eventually become a detailed execution folder:

```text
docs/
  step_1_climate_price_scenario_blueprint/
    00_index.md
    01_target_definition_and_path_schema.md
    02_historical_archive_and_block_design.md
    03_weather_and_climate_conditioning.md
    04_power_price_forward_anchoring.md
    05_gas_price_path_construction.md
    06_joint_path_assembly.md
    07_basis_and_location_handling.md
    08_ancillary_price_paths.md
    09_validation_and_backtesting.md
    10_gen2_out_of_sample_extensions.md
    11_open_questions_and_red_assumptions.md
```

The first detailed file should probably be `01_target_definition_and_path_schema.md`, because the schema forces clarity on frequency, units, settlement basis, and what Step 2 expects.

## Immediate Work Plan

Recommended order:

| Order | Work item | Why |
| :--- | :--- | :--- |
| 1 | Confirm target market and first example asset. | ERCOT peaker and Athens NYISO CCGT require different data choices. |
| 2 | Define Step 1 output schema. | Step 2 cannot be written cleanly without exact exogenous inputs. |
| 3 | Decide hub-first or node-first for first example. | Hub-first is simpler; node-first is more settlement-realistic. |
| 4 | Decide gas delivery basis assumption. | Delivered gas drives dispatch. |
| 5 | Define historical block archive requirements. | Prevents hidden data gaps. |
| 6 | Write detailed weather/climate conditioning doc. | Clarifies what S2S does and does not do. |
| 7 | Write power and gas path construction docs. | Anchoring mechanics are central. |
| 8 | Write validation plan. | Avoids building a scenario engine that cannot be checked. |

## Open Questions

| Question | Why it matters |
| :--- | :--- |
| What is the first target asset: Athens NYISO CCGT, ERCOT peaker, or generic ERCOT gas asset? | Determines ISO data, hub, gas basis, and weather location. |
| Should Gen 1 hub-first use DA or RT LMP? | Must match settlement and dispatch framing. |
| What delivered gas point should be used? | Henry Hub alone is usually not enough for plant dispatch. |
| Do we include ancillary prices in the first Step 1 package? | Required for peakers; optional for simple energy-only CCGT. |
| Do we model node basis in Step 1 or leave it for a later overlay? | Affects revenue accuracy and complexity. |
| What is the S2S source and forecast horizon? | S2S is useful for near-term conditioning, not all horizons. |
| How are DST and market calendars handled? | Hourly dispatch breaks if timestamps are inconsistent. |
| What forward curve source is assumed for power? | Needed for point-in-time reproducibility. |
| What forward source is assumed for gas? | Needed for fuel-cost reproducibility. |

## External Source Anchors

| Topic | Source anchor | Why it matters |
| :--- | :--- | :--- |
| ERA5 reanalysis | Copernicus ERA5 hourly data: `https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels` | Primary weather history and analog archive. |
| S2S forecasts | ECMWF S2S dataset: `https://ecds-prod.ecmwf.int/datasets/s2s` | Candidate near-term climate conditioning source. |
| ENSO outlook | NOAA CPC ENSO probabilities: `https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths.php` | Seasonal climate-state conditioning signal. |
| ISO LMP access | GridStatus LMP docs: `https://opensource.gridstatus.io/en/api-refactor/lmp.html` | Practical multi-ISO historical LMP access. |
| Historical gas | EIA Henry Hub spot price: `https://www.eia.gov/dnav/ng/hist/rngwhhda.htm` | Historical gas shape and benchmark. |
| Gas forwards | CME Henry Hub Natural Gas futures: `https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.contractSpecs.html` | Forward fuel anchor. |
| Thermal operation | EPA CEMS hourly data: `https://www.epa.gov/air-emissions-inventories/where-can-i-obtain-hourly-data-continuous-emissions-monitors-cems` | Later calibration of heat rate and dispatch behavior. |

## Link To Step 2

The Step 2 plan should treat this file as its upstream dependency.

```text
Step 1 output:
  hourly power price
  hourly weather
  daily / hourly delivered gas
  ancillary price, if modeled
  scenario metadata

Step 2 input:
  Step 1 output
  +
  opening plant state
```

If Step 1 is weak, Step 2 will look precise but rest on unstable inputs. This is why Step 1 must be written and validated before detailed dispatch docs are finalized.
