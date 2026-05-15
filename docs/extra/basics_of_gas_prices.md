# Basics Of Gas Prices

## Purpose

This note explains how to think about natural gas prices for the gas turbine model.

The short version:

```text
The plant does not burn Henry Hub.
The plant burns delivered gas.
```

So the Step 1 scenario engine should not hand Step 2 a generic "gas price." It should hand Step 2 a defensible delivered fuel price path.

```text
delivered_gas_price
  = benchmark gas price
  + location basis
  + transport / delivery adders
  + daily shape
  + explicit scenario adjustments, if any
```

That delivered gas price then feeds dispatch economics:

```text
fuel_cost_per_MWh = heat_rate_MMBtu_per_MWh * delivered_gas_USD_per_MMBtu
```

If heat rate is `7.5 MMBtu/MWh`, a `0.50 USD/MMBtu` gas-price error creates:

```text
7.5 * 0.50 = 3.75 USD/MWh
```

That is large enough to change dispatch, starts, EBITDA, EOH, and maintenance timing.

## The Main Mental Model

Natural gas pricing has three layers.

```text
                    +-------------------------------+
                    |  1. BENCHMARK                 |
                    |  Henry Hub / NYMEX / CME       |
                    |  Broad North American price    |
                    +-------------------------------+
                                      |
                                      v
                    +-------------------------------+
                    |  2. LOCATION BASIS             |
                    |  Waha, Katy, TGP Zone 6,       |
                    |  Transco Zone 6 NY, Algonquin, |
                    |  Chicago, SoCal, etc.          |
                    +-------------------------------+
                                      |
                                      v
                    +-------------------------------+
                    |  3. PLANT DELIVERY             |
                    |  pipeline transport, fuel      |
                    |  contract, balancing, firm      |
                    |  vs interruptible service      |
                    +-------------------------------+
                                      |
                                      v
                              delivered gas
```

The power-market equivalent is:

```text
power forward hub price + node basis = settlement price
```

The gas-market equivalent is:

```text
Henry Hub + gas basis + delivery economics = fuel cost
```

But the objects are not identical. A power node is an electrical settlement point. A gas pricing location is usually a pipeline zone, trading hub, citygate, pooling point, or index location.

## Do Not Treat Gas Locations As Power Nodes

This is the first terminology trap.

| Power market term | Gas market analogue | Important difference |
| :--- | :--- | :--- |
| Electrical node / PNode | Gas index location, hub, citygate, pipeline zone | Gas index locations are not hourly LMP nodes. |
| LMP | Spot gas index or assessed price | Gas prices are often daily or monthly index prices, not 5-minute/hourly dispatch prices. |
| Hub | Henry Hub, Waha, Katy, Houston Ship Channel, Transco Zone 6, TGP Zone 6 | Gas hubs are physical/financial trading locations, not ISO electrical hubs. |
| Node-minus-hub basis | Location basis to Henry Hub | Gas basis is usually quoted as differential to Henry Hub. |
| DA/RT settlement | Daily gas / bidweek / monthly index / forward basis | Gas calendar and nomination timing differ from power settlement. |

Good wording for the model:

- gas pricing location
- gas delivery point
- gas index
- pipeline zone
- citygate
- delivered gas price
- Henry Hub plus basis

Avoid saying "gas node" unless a specific vendor or dataset uses that word.

## Basic Vocabulary

| Term | Plain-English meaning | Modeling use |
| :--- | :--- | :--- |
| Henry Hub | The main US natural gas benchmark in Louisiana. | Benchmark level for historical and forward gas. |
| NYMEX / CME Henry Hub futures | Exchange-traded monthly Henry Hub futures. | Market-consistent forward level. |
| Spot gas | Physical gas price for near-term delivery. | Historical daily/monthly shape. |
| Bidweek | Trading window for next-month physical gas. | Monthly physical index formation. |
| Daily gas index | Daily physical gas assessment at a location. | Daily dispatch fuel cost shape. |
| Monthly index | Monthly physical gas index, often bidweek-based. | Monthly fuel cost anchor or contract index. |
| Basis | Price difference between a local location and Henry Hub. | Converts benchmark gas into regional/local gas. |
| Fixed price | Absolute price at a location. | Sometimes available directly instead of Henry Hub plus basis. |
| Citygate | Delivery area near utility/load region. | Often relevant for constrained winter markets. |
| Pipeline zone | Segment or pricing zone on a gas pipeline. | Important for plant fuel supply. |
| Pooling point | Trading/aggregation point on a pipeline. | May be the contract index. |
| Firm transport | Contracted pipeline capacity. | Reduces delivery risk but has fixed cost. |
| Interruptible transport | Non-firm pipeline access. | Cheaper but can fail when constrained. |
| Fuel gas quality / HHV / LHV | Energy-content basis of gas and heat rate. | Must match heat-rate basis. |

## Why Gas Prices Matter So Much For Dispatch

A gas plant dispatches on spark spread:

```text
spark_spread_t
  = power_price_t
  - heat_rate_t * delivered_gas_price_t
  - VOM_t
  - wear_or_start_allocation_t
```

Gas price enters two different places:

```text
1. Plant fuel cost:
   higher delivered gas makes the plant more expensive to run.

2. Market-clearing power price:
   when gas is on the margin, higher gas can raise LMPs.
```

Do not double count this.

| Effect | Correct owner | Common mistake |
| :--- | :--- | :--- |
| Henry Hub forward level | Gas path level | Also shifting plant fuel cost again in Step 2. |
| Gas-driven LMP level | Power price scenario / forward curve | Treating it as separate plant fuel cost uplift. |
| Local plant delivery basis | Delivered gas path | Embedding plant-specific fuel basis inside the power price. |
| Node power basis | Power basis layer | Confusing electrical basis with gas basis. |

## Data Source Stack

The gas price source stack should be tiered by what question is being answered.

| Need | Source type | Example sources | Best use | Limitation |
| :--- | :--- | :--- | :--- | :--- |
| Public historical benchmark | Government data | EIA Henry Hub spot | Historical Henry Hub daily/monthly path. | Not plant-delivered gas. |
| Public regional context | Government/market summaries | EIA natural gas data and market notes | Understanding broad regional spreads and storage/weather context. | Not a full commercial gas-index feed. |
| Forward benchmark | Exchange | CME / NYMEX Henry Hub futures | Forward market anchor for Henry Hub. | Does not include local basis. |
| Exchange-cleared basis | Exchange | ICE basis and fixed-price gas products | Tradable or cleared location differentials. | Coverage/liquidity varies by location/tenor. |
| Daily/monthly physical gas indices | Price reporting agencies | Platts Gas Daily, Inside FERC, Argus Natural Gas Americas, NGI | Commercial location indices used by market participants. | Usually subscription. |
| Forward gas curves | Vendor/market data | Argus forward curves, Platts forward curves, ICE, brokers | Location-specific forward fuel assumptions. | Methodology and liquidity differ by location. |
| Actual plant fuel cost | Plant data / filings | Fuel invoices, EIA-923 plant fuel cost, internal settlement files | Validation of delivered gas assumptions. | May be monthly, lagged, confidential, or averaged. |
| Fuel burn validation | Operations data | CEMS, plant historian, EMS/SCADA | Check heat rate and fuel burn. | Does not give market price by itself. |

## Source Notes

### EIA

EIA is the first public source to use for broad historical Henry Hub data.

Use it for:

- daily Henry Hub spot price history
- monthly Henry Hub history
- high-level regional natural gas context
- storage and market balance context

Do not use it alone as the final plant fuel price unless the model explicitly says:

```text
Gen 1 simplification: Henry Hub used as fuel proxy.
```

### CME / NYMEX

CME Henry Hub futures are the cleanest liquid forward benchmark for US natural gas.

Use them for:

- monthly forward Henry Hub level
- forward gas sensitivity cases
- Q-ish market anchor for the fuel benchmark

But:

```text
CME Henry Hub futures != delivered gas at the plant
```

The model still needs basis and delivery economics.

### ICE

ICE lists many physical, fixed-price, basis, and index natural gas products.

ICE is useful because it shows how the market itself defines:

- fixed price at a location
- basis to NYMEX Henry Hub
- monthly bidweek / Inside FERC style settlement
- daily index relationships

Example:

```text
Waha basis future = Waha monthly index - NYMEX Henry Hub settlement
```

That is exactly the kind of object the model means by gas basis.

### Platts / Inside FERC

Platts Gas Daily and Inside FERC are important because many physical gas contracts reference these indices.

Use them for:

- daily physical gas indices
- monthly bidweek indices
- location-specific spot/basis history
- contract index references

Watch item:

```text
Subscription data is often needed for proper plant-specific work.
```

### Argus

Argus publishes natural gas price assessments and forward-curve products.

Use them for:

- daily gas price assessments
- bidweek/monthly indices
- North American natural gas forward curves
- basis differentials to CME Henry Hub futures

Argus is especially useful when we need a vendor curve that covers many locations and tenors consistently.

### NGI

Natural Gas Intelligence is another common commercial index and market data source.

Use it for:

- daily gas price indices
- regional gas market color
- location spreads

For model docs, treat NGI as a commercial source, not a free public baseline.

### EIA-923 And Plant Data

For an actual plant, EIA-923 can sometimes help validate monthly delivered fuel cost.

But EIA-923 is not a forward curve and is not always clean enough to use directly as daily dispatch fuel cost.

Use it as:

```text
validation / calibration:
  Is our delivered gas assumption plausible relative to reported plant fuel cost?
```

## Historical Gas Path Construction

For Gen 1, the practical historical gas path should usually be daily, not hourly.

```text
historical_daily_shape_d
  = historical_gas_index_d
  - average(historical_gas_index in same month)
```

Then anchor that shape to the forecast month:

```text
forecast_delivered_gas_d
  = Henry_Hub_forward_month
  + location_basis_month
  + transport_adder_month
  + historical_daily_shape_d
```

This preserves daily volatility while forcing the monthly average to match the forecast fuel anchor.

If the historical gas index is already the local delivered proxy:

```text
historical_daily_shape_d
  = local_gas_index_d - average(local_gas_index in same month)
```

If only Henry Hub history is available:

```text
historical_daily_shape_d
  = Henry_Hub_daily_d - average(Henry_Hub_daily in same month)
```

Then basis becomes a separate assumption.

## Forward Gas Path Construction

For a forecast month:

```text
delivered_gas_forward_month
  = Henry_Hub_forward_month
  + local_basis_forward_month
  + transport_adder_month
```

Where:

| Component | Best source | Gen 1 fallback |
| :--- | :--- | :--- |
| Henry Hub forward | CME / NYMEX monthly futures | Vendor or broker HH curve. |
| Local basis forward | ICE basis product, Argus/Platts/broker basis curve | Static historical average basis or explicit scenario assumption. |
| Transport adder | Fuel contract / pipeline tariff / plant data | Fixed assumed adder. |
| Daily shape | Historical daily index | Henry Hub daily deviations. |

The model should store each component separately:

```text
delivered_gas_price
henry_hub_component
location_basis_component
transport_component
daily_shape_component
source_tags
snapshot_date
```

Do not only store the final number. If the number is challenged, we need to know what caused it.

## How To Choose The Gas Location

This is the most important practical question.

Use this order:

```text
1. Actual fuel contract index
2. Pipeline interconnect / delivery point
3. Plant operator/trader convention
4. Closest liquid regional gas index
5. Henry Hub plus explicit basis assumption
```

Checklist:

| Question | Why it matters |
| :--- | :--- |
| What pipeline serves the plant? | Pipeline zone often determines relevant index. |
| What gas index is in the fuel contract? | Contract settlement should drive delivered fuel cost. |
| Is the plant buying at citygate, pooling point, receipt point, or delivered meter? | Different points can have different basis. |
| Does the plant hold firm transport? | Firm transport cost and reliability differ from interruptible service. |
| Is gas tolling handled by an offtaker? | The plant owner may not bear the same gas price exposure. |
| Is the plant in a winter-constrained region? | Basis can dominate Henry Hub during cold snaps. |
| Is the plant near production with takeaway constraints? | Basis can be deeply negative in some periods. |
| Is there a monthly bidweek index or daily index exposure? | Dispatch model frequency should match exposure. |

## Major Hubs And Index Locations

Major hubs are useful because they give the model a practical map of liquid gas references. They are not perfect asset-level answers.

The right use is:

```text
major hub list = proxy-selection map
actual fuel contract = final truth when available
```

The trade-off:

| Benefit of using major hubs | Risk if overused |
| :--- | :--- |
| Easier to choose a defensible proxy when plant-specific fuel data is missing. | A hub may be near the plant but not the plant's actual contract index. |
| Better basis accuracy than Henry Hub-only modeling. | A regional hub can hide pipeline-zone or meter-level delivery cost. |
| Better communication with traders, lenders, and market data vendors. | Different vendors may define similarly named locations differently. |
| Easier forward-curve sourcing through ICE, Platts, Argus, brokers, or terminals. | Some hubs are liquid nearby but thin further out on the curve. |
| Helps build scenario groups by region. | A "major" hub may still be wrong during local constraint events. |

So yes, highlight the major hubs, but label them as candidate gas pricing references, not automatic plant delivery prices.

### Major US And North American Gas References

This is a practical modeling list, not an official exhaustive taxonomy. Exact names vary across ICE, Platts, Argus, NGI, broker screens, and fuel contracts.

| Region | Major hubs / index locations | Why they matter | GT modeling watch item |
| :--- | :--- | :--- | :--- |
| National benchmark | Henry Hub | Main US benchmark and NYMEX/CME futures delivery reference. | Good benchmark, bad final delivered-gas proxy if local basis matters. |
| Gulf Coast / Louisiana / Southeast | Henry Hub, Transco Zone 4, Transco Station 85, TGP 500 Leg Pool, Texas Gas Zone 1, Sonat Zone 0 | Major supply, pipeline, LNG, and power-market region. | LNG/export demand and pipeline constraints can affect basis. |
| East Texas / Houston | Houston Ship Channel, Katy Hub, NGPL TxOk East Pool, TETCO South Texas Zone, TGP Zone 0 South | Common ERCOT Gulf Coast references. | Choose based on plant pipeline/interconnect, not only ERCOT hub. |
| South Texas | Agua Dulce, NGPL South Texas, TGP Zone 0 South, Texas intrastate points | Important for South Texas supply and LNG-adjacent flows. | Local basis may diverge from Houston/Katy. |
| Permian / West Texas | Waha, El Paso Permian Basin, Permian Basin pool points | Key production-region references. | Takeaway constraints can make basis very different from Henry Hub. |
| Midcontinent | Panhandle, ANR Oklahoma, NGPL Midcontinent Pool, Enable Flex Pool, ONEOK, Southern Star | Common SPP/MISO-adjacent gas references. | Pipeline choice matters because several hubs may look close geographically. |
| Upper Midwest | Chicago Citygate, MichCon, NNG Ventura, Northern Border Ventura, REX Zone 3, Alliance into interstates | Important load and storage-connected references. | Chicago is useful, but plant-specific index may be another pipeline point. |
| Appalachia | Eastern Gas South / Dominion South, Columbia Gas Appalachia/TCO, TETCO M-2 receipts, Transco Leidy, TGP Marcellus | Major supply-basin and PJM-adjacent references. | Production abundance can make basis discounted; takeaway constraints matter. |
| Northeast / New York / New England | Transco Zone 6 NY, Transco Zone 6 Non-NY, Algonquin Citygate, Tennessee Zone 6 / TGP Zone 6, Iroquois Zone 2 | Critical for NYISO/ISO-NE winter fuel economics. | Winter pipeline constraints can dominate dispatch cost and power prices. |
| Rockies / Northwest | Opal, Cheyenne Hub, CIG Rockies, White River Hub, PGT Malin, Sumas | Western supply and flow references. | Regional constraints and weather can create large spreads. |
| California / Southwest | SoCal Citygate, SoCal Border, PG&E Citygate, PG&E Malin, El Paso San Juan, Kern receipt | Critical for CAISO and western gas-electric risk. | Storage/pipeline outages and import constraints can dominate basis. |
| Canada | AECO / NIT, Dawn Ontario, Station 2, Empress | Important cross-border and North American market references. | Useful for broader gas curves; US plant use depends on flow path. |

### How To Use This Hub List

Use the hubs as a funnel.

```text
plant location
  -> served pipeline(s)
  -> likely pipeline zone / citygate / hub
  -> available daily/monthly index
  -> available forward basis/fixed price curve
  -> delivered gas assumption
```

Example:

```text
ERCOT Houston plant
  -> do not automatically use ERCOT Houston electrical hub
  -> identify gas supply pipe
  -> candidate gas references: Katy, Houston Ship Channel, TETCO South Texas, TGP Zone 0 South
  -> choose the one tied to contract/interconnect/liquid proxy
```

Example:

```text
NYISO / Athens-style CCGT
  -> local docs mention Tennessee Gas Pipeline / TGP Zone 6
  -> candidate references: TGP Zone 6, Transco Zone 6 NY/non-NY, Iroquois, Algonquin depending actual location and contract
  -> choose actual fuel contract index if available
```

### Accuracy Trade-Off

There are three possible levels of gas-location accuracy.

| Level | What it uses | Accuracy | Cost / complexity | When to use |
| :--- | :--- | :--- | :--- | :--- |
| Henry Hub proxy | Henry Hub only | Low for local dispatch, okay for prototype mechanics | Very low | Testing dispatch code only. |
| Major hub proxy | Closest/liquid regional hub plus basis | Medium | Medium | Gen 1 scenario modeling when plant fuel contract is unknown. |
| Contract-delivered gas | Actual contract index, pipeline charges, transport rights, invoices | High | High | Asset diligence, lender/investor model, serious backtest. |

Major hubs are the right middle step. They are much better than Henry Hub-only modeling, but they should not be presented as final plant fuel economics unless we can tie the hub to the plant's contract or interconnect.

## Regional Examples

These are illustrative, not universal mappings.

| Power market / region | Common gas-price concepts | Modeling watch item |
| :--- | :--- | :--- |
| ERCOT Gulf Coast / Houston | Houston Ship Channel, Katy, Texas Eastern, regional basis to Henry Hub | Gas is usually liquid, but basis can matter by location. |
| ERCOT West / Permian | Waha basis, Permian takeaway constraints | Waha can behave very differently from Henry Hub. |
| NYISO / New York | Transco Zone 6 NY, TGP Zone 6, Iroquois, citygate indices | Winter pipeline constraints can create major basis spikes. |
| ISO-NE | Algonquin Citygate, Tennessee Zone 6, Iroquois | Gas-electric winter risk is central. |
| PJM Mid-Atlantic | Transco Zone 6 non-NY, TETCO M3, Dominion South, Columbia Gas Appalachia | Basis depends heavily on pipeline and subregion. |
| MISO / Midwest | Chicago citygate, ANR, MichCon, regional pipeline zones | Regional basis and storage matter. |
| CAISO / West | SoCal Citygate, PG&E Citygate, Malin, Opal | Pipeline outages and storage constraints can dominate. |
| SPP / Midcontinent | Panhandle, NGPL Midcon, Southern Star, ONEOK-related locations | Need plant-specific pipeline context. |

For Athens-style documentation, the local learning docs mention:

```text
TGP Zone 6 = Tennessee Gas Pipeline Zone 6
Tennessee Gas Pipeline gas interconnect
```

Treat this as an Athens worked-example reference until the actual fuel contract and pipeline delivery point are confirmed.

## Frequency

Gas price frequency should match the model question.

| Frequency | Use | When sufficient | Caveat |
| :--- | :--- | :--- | :--- |
| Monthly | Long-horizon planning, annual revenue, high-level dispatch | Baseload or coarse forecast studies. | Can miss daily winter/scarcity volatility. |
| Daily | Gen 1 dispatch and spark spread | Most GT Step 2 studies. | Does not capture intraday gas nomination stress. |
| Hourly | Rare stress cases | Extreme winter gas-electric coordination studies. | Data and assumptions become much harder. |
| Event / constraint tag | Pipeline outages, freeze-offs, fuel curtailment | Stress testing. | Usually scenario-driven, not purely statistical. |

Recommended Gen 1:

```text
daily delivered gas price
monthly forward anchor
historical daily shape
explicit location basis
```

## Gas Day And Calendar Nuance

Gas and power calendars do not line up perfectly.

Model notes:

- Gas is often nominated on a gas-day basis.
- Power dispatch is hourly by local market time.
- Some gas price indices are for next-day delivery.
- Weekend/holiday gas trading can cover multiple gas days.
- Bidweek indices are for next-month delivery.

For Gen 1, do not overcomplicate this. Use a daily gas price mapped to local power-market dates, but include a timestamp/calendar warning in validation.

```text
Gen 1 simplification:
  one delivered gas price per local power-market date
```

Gen 2 can add weekend/holiday and gas-day treatment if the first backtests show it matters.

## Basis: The Part That Usually Causes Confusion

Basis is simply:

```text
local_gas_price - Henry_Hub_price
```

If local gas is cheaper than Henry Hub:

```text
basis < 0
```

If local gas is more expensive than Henry Hub:

```text
basis > 0
```

Examples:

```text
Henry Hub: 4.00 USD/MMBtu
Local gas: 3.70 USD/MMBtu
Basis:    -0.30 USD/MMBtu
```

```text
Henry Hub: 4.00 USD/MMBtu
Local gas: 7.50 USD/MMBtu
Basis:    +3.50 USD/MMBtu
```

For a gas plant, basis matters because dispatch cost changes directly:

```text
dispatch_cost_change = heat_rate * basis_change
```

At `7.5 MMBtu/MWh`, a `+3.50 USD/MMBtu` winter basis event adds:

```text
7.5 * 3.50 = 26.25 USD/MWh
```

That can completely change whether the plant is economic.

## Fixed Price Vs Basis Price

Natural gas forward products can be quoted in two ways.

### Fixed Price

```text
Waha fixed price = 3.25 USD/MMBtu
```

This is an outright gas price at the location.

### Basis

```text
Waha basis = -0.45 USD/MMBtu
Henry Hub forward = 3.70 USD/MMBtu

Waha fixed equivalent = 3.70 - 0.45 = 3.25 USD/MMBtu
```

For modeling, both are acceptable as long as the decomposition is clear.

Preferred storage:

```text
Henry Hub component
plus basis component
equals local fixed-price equivalent
```

That makes sensitivities easier.

## Daily Index Vs Monthly Index

Physical gas contracts may settle against daily or monthly indices.

| Index type | Meaning | Dispatch implication |
| :--- | :--- | :--- |
| Daily index | Price varies day by day. | Best for daily dispatch economics. |
| Monthly index / bidweek | One index for the month. | Dispatch fuel cost may be flat unless daily shape is modeled separately. |
| First-of-month / Inside FERC style index | Common monthly physical index. | Useful for monthly fuel budget and forward basis. |
| Gas Daily style index | Daily physical market assessment. | Useful for daily volatility and weather stress. |

Gen 1 recommendation:

```text
Use monthly forward/basis for level.
Use historical daily index deviations for shape.
```

## Delivered Gas Construction Options

### Option 1: Henry Hub Proxy

```text
delivered_gas_d = Henry_Hub_forward_month + HH_daily_shape_d
```

Use only for a very early prototype.

Pros:

- easiest
- public data
- good enough to test dispatch mechanics

Cons:

- misses local basis
- can be wrong in constrained regions
- not investment-grade

### Option 2: Henry Hub Plus Static Basis

```text
delivered_gas_d
  = Henry_Hub_forward_month
  + static_basis_month
  + HH_daily_shape_d
```

Good Gen 1 default when local vendor curve is unavailable.

Pros:

- simple
- transparent
- makes basis explicit

Cons:

- basis may be regime-dependent
- winter constraints may be under-modeled

### Option 3: Henry Hub Plus Forward Basis Curve

```text
delivered_gas_d
  = Henry_Hub_forward_month
  + basis_forward_month
  + local_daily_shape_d
```

Best practical Gen 1 / Gen 2 bridge.

Pros:

- market-consistent benchmark and local basis
- basis can be point-in-time
- easier to defend

Cons:

- often requires paid data
- liquidity varies

### Option 4: Vendor Fixed-Price Location Curve

```text
delivered_gas_d
  = local_fixed_price_forward_month
  + local_daily_shape_d
  + delivery_adder
```

Good if the vendor curve directly maps to the plant's gas index.

Pros:

- straightforward
- avoids manual basis math

Cons:

- hides Henry Hub vs basis contribution unless decomposed separately

### Option 5: Contract / Invoice Based

```text
delivered_gas_d
  = contract_index_d
  + negotiated_basis
  + transport
  + balancing
```

Best for actual asset diligence.

Pros:

- matches true economics
- best for validation

Cons:

- requires confidential contract and invoice data
- may not be available for early modeling

## Recommended Model Path

### Gen 1

Use:

```text
Henry Hub forward
+ explicit basis assumption
+ historical daily shape
+ optional transport adder
```

Store:

```text
gas_location
gas_index_name
henry_hub_source
basis_source
basis_value
transport_adder
daily_shape_source
snapshot_date
```

This is enough to run dispatch and test the Step 2 engine.

### Gen 2

Upgrade to:

```text
local gas index history
+ location basis forward curve
+ basis residual calibration
+ regime-specific volatility scaling
+ validation against EIA-923 / invoices
```

Add backtests:

```text
forecast delivered gas -> compare to realized local index
forecast dispatch fuel cost -> compare to reported fuel cost
forecast spark spread -> compare to actual generation behavior
```

### Gen 3

Only if needed:

```text
pipeline constraint scenarios
firm vs interruptible transport modeling
gas-day calendar modeling
intraday gas stress
gas-electric co-movement tails
physical supply curtailment risk
```

Do not start here. It is easy to spend too much time on gas-network detail before the core dispatch model is working.

## How Gas Should Enter Step 1

Step 1 should produce:

```text
daily_path_table:
  scenario_id
  date
  delivered_gas_price
  henry_hub_price
  gas_basis
  transport_adder
  gas_location
  gas_index_name
  gas_source
  gas_snapshot_date
```

Hourly gas is optional:

```text
hourly_path_table:
  delivered_gas_price_hourly
```

For Gen 1, hourly gas should usually be omitted. Step 2 can use daily gas for every hour in that day.

## How Gas Should Enter Step 2

Step 2 should not forecast gas.

Step 2 should receive:

```text
date
delivered_gas_price
```

Then it calculates:

```text
fuel_cost_t = heat_rate_t * delivered_gas_price_date
```

If Step 2 receives only Henry Hub, it should either:

```text
reject input as incomplete
```

or:

```text
run with explicit flag:
  gas_basis_mode = "Henry Hub proxy"
```

Silent Henry Hub proxy use is dangerous.

## Co-Movement With Power And Weather

Gas should not be simulated independently if we care about realistic dispatch.

Important relationships:

- cold weather can raise gas demand and power demand
- hot weather can raise power demand and gas-fired generation demand
- high gas prices can raise power prices when gas is marginal
- regional gas constraints can coincide with power scarcity
- low gas basis in production regions can improve local gas plant economics

Gen 1 should preserve co-movement where possible:

```text
draw historical calendar block:
  weather from month Y
  power price shape from month Y
  gas daily shape from month Y
```

Then anchor levels separately:

```text
power level -> power forward
gas level   -> gas forward + basis
```

If gas data is missing for the same block, document the fallback.

## P And Q Framing

Gas follows the same broad P-vs-Q idea as power.

| Question | Use |
| :--- | :--- |
| What is the market level for Henry Hub in July 2027? | CME/NYMEX forward, Q-ish. |
| What is the market basis for Waha or TGP Zone 6 in July 2027? | ICE/vendor/broker basis, Q-ish where liquid. |
| What daily volatility shape should the month have? | Historical analog / P-world scenario. |
| What if a 2022-style gas shock repeats? | Stress scenario / perturbation. |
| What delivered fuel cost does the plant actually face? | Contract + basis + transport + scenario. |

The forward curve anchors the average. The scenario engine supplies path shape and uncertainty.

## Athens-Style Worked Example

The current learning docs mention Tennessee Gas Pipeline context for the Athens-style example.

For a first Athens-style gas path, use a clear placeholder:

```text
gas_location: TGP Zone 6
gas_index_name: Tennessee Gas Pipeline Zone 6 proxy
henry_hub_forward: from CME / NYMEX or vendor
basis: TGP Zone 6 minus Henry Hub, from vendor/broker or assumption
transport_adder: 0 unless fuel contract gives a value
daily_shape: historical daily TGP Zone 6 if available, otherwise Henry Hub daily shape
```

Example:

```text
July Henry Hub forward:       4.20 USD/MMBtu
TGP Zone 6 basis assumption:  0.35 USD/MMBtu
transport adder:              0.05 USD/MMBtu
daily shape on July 14:       0.18 USD/MMBtu

delivered gas July 14:
  4.20 + 0.35 + 0.05 + 0.18 = 4.78 USD/MMBtu
```

If the effective heat rate is `7.2 MMBtu/MWh`:

```text
fuel cost = 7.2 * 4.78 = 34.42 USD/MWh
```

Then Step 2 compares hourly power prices to:

```text
fuel cost + VOM + start/wear hurdle
```

This example is illustrative. The actual Athens fuel index and transport economics must come from the real fuel contract or plant diligence package.

## ERCOT Worked Example

For a Gulf Coast ERCOT plant:

```text
gas_location: Katy or Houston Ship Channel
benchmark: CME Henry Hub
basis: Katy minus Henry Hub or HSC minus Henry Hub
daily_shape: local daily index if available
```

For a West Texas / Permian-linked plant:

```text
gas_location: Waha
benchmark: CME Henry Hub
basis: Waha minus Henry Hub
daily_shape: Waha daily index if available
```

Example:

```text
Henry Hub forward:          4.00 USD/MMBtu
Katy basis:                -0.15 USD/MMBtu
transport adder:            0.08 USD/MMBtu
daily shape:                0.20 USD/MMBtu

delivered gas:
  4.00 - 0.15 + 0.08 + 0.20 = 4.13 USD/MMBtu
```

At `10.5 MMBtu/MWh` peaker heat rate:

```text
fuel cost = 10.5 * 4.13 = 43.37 USD/MWh
```

## Lockport Energy Associates LP Working Recommendation

This is the first concrete plant-level gas-price mapping example.

### Plant Facts From Public Data

Public EIA-derived plant data identifies Lockport Energy Associates LP as:

| Item | Working value |
| :--- | :--- |
| Plant | Lockport Energy Associates LP |
| EIA plant id | 54041 |
| Location | Lockport, Niagara County, New York |
| Power market | NYISO |
| Technology | Natural gas fired combined cycle / CHP-style plant with CT and steam components |
| Primary fuel | Natural gas, with distillate fuel oil capability shown for generators |
| Reported gas pipeline | Tennessee Gas Pipeline Company |
| Electrical node clue | NYISO PTID 23791 in EIA-derived generator records |

The gas clue is the important part:

```text
reported pipeline = Tennessee Gas Pipeline Company
plant location    = Lockport / Niagara County, NY
```

Tennessee Gas Pipeline's own Zone 5 map shows Lockport-related points in Rate Zone 5, including:

```text
LOCKPORT NY-420221
LOCKPORT/230C
420870-ZONE 5 NIAGARA POOL
50763-ZONE 5 LEG 200 WEST POOL
```

So the first-pass fuel-price hypothesis is:

```text
Lockport delivered gas is a TGP Zone 5 / Niagara / western NY gas problem,
not a generic Henry Hub problem and not automatically a Transco Zone 6 NY problem.
```

### Recommended Historical Gas Price Hierarchy

Use this order for Lockport.

| Rank | Gas price input | Confidence | Why |
| :--- | :--- | :--- | :--- |
| 1 | Actual fuel contract index, transport terms, and invoices | High | This is the plant's true delivered fuel economics. |
| 2 | TGP Zone 5 / Niagara / Zone 5 200 West Pool commercial index, if available from vendor | Medium-high | Best match to the public TGP location clues. |
| 3 | Platts Gas Daily `Niagara` and/or `Tennessee, zone 5-200 leg` daily index as a proxy | Medium | Relevant Northeast/TGP/NY pricing points, but confirm exact pool and station coverage. |
| 4 | Henry Hub daily plus static TGP Zone 5 / Niagara basis assumption | Low-medium | Useful Gen 1 fallback if commercial local history is unavailable. |
| 5 | Henry Hub only | Low | Acceptable only for dispatch-engine testing, not fuel economics. |

Do not use these as base case without a reason:

| Avoid as base | Why |
| :--- | :--- |
| Transco Zone 6 NY | New York City / downstream constraint pricing can be very different from western NY / TGP Zone 5. |
| Algonquin Citygate | New England winter constraint signal, not Lockport delivered gas. |
| New York residential/industrial retail gas prices | Retail tariffs include utility, distribution, and customer-class effects; not a plant fuel index. |

### Practical Gen 1 Choice

For a first historical gas path, use this if commercial data is available:

```text
daily_shape_source = Platts Gas Daily Niagara or TGP Zone 5-related daily index
monthly_level      = same-location monthly index or HH + basis
forward_anchor     = CME Henry Hub + TGP Zone 5/Niagara basis assumption
```

If only public data is available:

```text
daily_shape_source = EIA Henry Hub daily spot
monthly_level      = CME Henry Hub or EIA Henry Hub history
basis              = static Lockport/TGP Zone 5 basis assumption
confidence         = low, prototype only
```

Suggested Gen 1 formula:

```text
lockport_delivered_gas_d
  = HH_forward_month
  + TGP_Zone5_or_Niagara_basis_month
  + transport_adder_month
  + local_or_HH_daily_shape_d
```

Where:

```text
local_or_HH_daily_shape_d
  = daily_index_d - average(daily_index in same month)
```

### What To Ask A Data Vendor Or Trader

For Lockport, ask specifically:

```text
Do you have daily and monthly history for:
  - Niagara
  - Tennessee Zone 5 / TGP Zone 5
  - TGP Zone 5 200 West Pool
  - TGP Zone 5 Niagara Pool

Do you have forward basis for:
  - TGP Zone 5 / Niagara versus Henry Hub
  - nearby western NY / Tennessee Gas Pipeline locations
```

Also ask whether the plant's fuel contract references:

```text
Gas Daily
Inside FERC
Platts
Argus
NGI
ICE physical gas
NYMEX plus physical basis
```

The contract index matters more than the nearest hub name.

### Validation Data

Use these checks once a first Lockport gas path is built:

| Validation input | Use |
| :--- | :--- |
| EIA-923 plant fuel receipts / fuel cost, if available | Check monthly delivered fuel cost against modeled delivered gas. |
| CEMS fuel burn and generation | Check implied heat rate and dispatch behavior. |
| NYISO LMP at PTID 23791 or relevant zone/node | Check spark spread and realized dispatch. |
| Known oil-switching periods | Check whether gas price or gas availability may have driven fuel switching. |

### Lockport Confidence Label

Use this label until the actual fuel contract is reviewed:

```yaml
gas_location_confidence: "medium"
gas_location_reason: "Public EIA-derived data points to Tennessee Gas Pipeline; TGP map places Lockport in Rate Zone 5 with Lockport/230C and Zone 5 Niagara/200 West pool context."
gas_proxy_warning: "Exact fuel contract index not yet confirmed."
```

## Common Mistakes

| Mistake | Why it is wrong | Fix |
| :--- | :--- | :--- |
| Using Henry Hub as delivered gas with no label | Hides basis risk. | Label as proxy or add basis. |
| Mixing HHV heat rate with LHV fuel pricing assumption | Creates unit inconsistency. | Keep heat rate and gas energy basis aligned. |
| Using monthly gas for peaker dispatch with no daily shape | Misses daily scarcity/fuel-cost variation. | Add historical daily shape. |
| Letting Step 2 create gas prices | Breaks scenario ownership. | Step 1 owns gas path. |
| Treating gas basis like power node basis | Different markets and calendars. | Use gas-location terminology. |
| Ignoring firm transport | Plant may pay fixed transport to ensure fuel. | Separate commodity price from delivery/transport. |
| Ignoring winter regional basis | Understates constrained-region fuel cost. | Add regional basis scenarios. |
| Embedding plant gas basis inside power price | Double counts or hides economics. | Keep power price and delivered gas separate. |
| Not storing source/snapshot date | Cannot reproduce the forecast. | Store provenance fields. |

## What To Put In The Model Config

Minimum config:

```yaml
gas:
  gas_location: "TGP Zone 6"
  gas_index_name: "TGP Zone 6 proxy"
  benchmark: "Henry Hub"
  benchmark_forward_source: "CME/NYMEX or vendor"
  basis_source: "vendor/broker/assumption"
  basis_mode: "monthly"
  daily_shape_source: "local index or Henry Hub"
  transport_adder_mode: "fixed assumption"
  units: "USD/MMBtu"
  heat_rate_basis_check: "HHV"
```

Recommended scenario metadata:

```yaml
gas_source_snapshot_date: "YYYY-MM-DD"
gas_basis_snapshot_date: "YYYY-MM-DD"
gas_proxy_flag: false
gas_basis_uncertainty_case: "base"
gas_location_confidence: "medium"
```

## Decision Tree

```text
Do we have the plant fuel contract?
  |
  +-- yes
  |     -> use contract index + transport/delivery terms
  |     -> validate against invoices / EIA-923 if available
  |
  +-- no
        |
        v
Do we know the pipeline interconnect?
  |
  +-- yes
  |     -> choose the relevant pipeline zone / citygate / hub
  |     -> use vendor/broker basis if available
  |
  +-- no
        |
        v
Do we know the region and plant type?
  |
  +-- yes
  |     -> choose closest liquid regional index
  |     -> label as proxy
  |
  +-- no
        |
        v
Use Henry Hub proxy only for dispatch-engine testing.
Do not call it delivered gas.
```

## Open Questions For Our GT Work

| Question | Why it matters |
| :--- | :--- |
| What is the first target asset: Athens CCGT, ERCOT peaker, or generic gas plant? | Determines gas location and basis. |
| Do we have the actual fuel contract or only public assumptions? | Contract index is the best source. |
| Which pipeline serves the asset? | Needed for gas-location selection. |
| Is gas bought daily, monthly, under tolling, or through an energy manager? | Determines price exposure. |
| Does the plant hold firm transport? | Changes cost and availability risk. |
| Should Gen 1 use local daily gas shape or Henry Hub daily shape? | Affects dispatch volatility. |
| Should basis be deterministic, scenario-based, or stochastic? | Affects P50/P90 and stress cases. |
| How should EIA-923 fuel cost be used for validation? | Helps check delivered gas realism. |

## Recommended Next Step

For the first implementation, make a small gas-location table:

| Asset | Market | Candidate gas location | Confidence | Reason |
| :--- | :--- | :--- | :--- | :--- |
| Athens-style CCGT | NYISO / Zone G-style context | TGP Zone 6 proxy | Medium until contract confirmed | Local docs mention TGP Zone 6 / Tennessee Gas Pipeline. |
| ERCOT Gulf Coast peaker | ERCOT Houston | Katy or Houston Ship Channel | Medium | Common liquid Gulf Coast gas references. |
| ERCOT West peaker | ERCOT West | Waha | Medium | Common Permian gas basis reference. |

Then build the Gen 1 formula:

```text
delivered_gas_d
  = HH_forward_month
  + gas_basis_month
  + transport_adder_month
  + daily_shape_d
```

And keep all components auditable.

## References

Primary and market-facing references:

- EIA Henry Hub daily spot price: https://www.eia.gov/dnav/ng/hist/rngwhhdd.htm
- EIA Natural Gas data and market context: https://www.eia.gov/naturalgas/
- EIA electricity data browser / plant operations data entry point: https://www.eia.gov/electricity/data/browser/
- EIA-923 detailed power plant operations data: https://www.eia.gov/electricity/data/eia923/
- CME Henry Hub Natural Gas futures contract specs: https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.contractSpecs.html
- ICE Waha Basis Future product definition: https://www.ice.com/products/6590171
- ICE Waha Fixed Price Future product definition: https://www.ice.com/products/69723181/Waha-Fixed-Price-Future
- ICE US Physical Natural Gas Markets hub overview: https://www.ice.com/physical-gas-markets
- Platts Gas Daily: https://www.spglobal.com/energy/en/products-solutions/gas-power/platts-gas-daily
- S&P Global US and Canada Natural Gas methodology: https://www.spglobal.com/platts/en/our-methodology/methodology-specifications/natural-gas/us-and-canada-natural-gas-methodology
- S&P Global note on US natural gas supply/demand index locations: https://www.spglobal.com/energy/en/pricing-benchmarks/our-methodology/subscriber-notes/103125-platts-publishes-us-natural-gas-daily-and-monthly-supply-and-demand-indices
- Argus Natural Gas Americas: https://www.argusmedia.com/en/solutions/products/argus-natural-gas-americas
- Argus North American Natural Gas Forward Curves: https://www.argusmedia.com/en/solutions/products/argus-north-american-natural-gas-forward-curves
- EIA discussion of key natural gas pricing hubs: https://www.eia.gov/todayinenergy/detail.php?id=63504
- FERC Form 552 natural gas transaction data context: https://data.ferc.gov/form-no.-552-download-data
- Tennessee Gas Pipeline Rate Zone 5 map: https://pipeline2.kindermorgan.com/Documents/TGP/TGP_Map_Zone_5.pdf
- Tennessee Gas Pipeline Zone 5/6 pooling services note: https://pipeline2.kindermorgan.com/Documents/TGP/New_TGP_ZN_5_and_6_POOLS_final-20180911140554.pdf
- Platts note defining Tennessee zone 5-200 leg transition: https://www.spglobal.com/energy/en/pricing-benchmarks/our-methodology/subscriber-notes/103118-platts-transitions-ice-daily-natural-gas-locations-to-platts-locations
- Public EIA-derived Lockport plant summary: https://www.gridinfo.com/plant/lockport-energy-associates-lp/54041

Local references:

- `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/plans/step_1_climate_price_scenario_plan.md`
- `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/plans/step_2_execution_blueprint_plan.md`
- `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/learning/basics/00_combined_cycle_plant_anatomy.md`
- `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/learning/basics/02_heat_rate.md`
- `/Users/divy/code/work/infrasure_git_codes/gt_models/docs/learning/basics/05_dispatch_and_daily_loop.md`
- `/Users/divy/code/personal/renewablesinfo_com/docs/modeling/revenue_forecasting_methodology/data_catalog/03_price_data.md`
