# Start Costs And VOM

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](./00_combined_cycle_plant_anatomy.md).

Read this first if EOH, hot/warm/cold starts, CI, HGP, or MI are new: [EOH And Starts](./03_eoh_and_starts.md).

Read this if LTSA fixed fees, EOH reserve, or start overages are new: [LTSA And Service Contracts](./08_ltsa_and_service_contracts.md).

> Plant-Type Note
> Start cost and VOM are broad gas-plant concepts, but the cost buckets depend on the equipment present. HRSG/ST start costs only apply when the plant has steam-side equipment. A simple-cycle GT has GT/BOP start costs without HRSG/ST cycling. A CHP plant may also need steam-host cost or reliability terms.

## First-Time Reader Map

If this topic is new, do not start with the cost tables. Start with the simple dispatch problem:

```text
The plant can earn revenue if it runs.
But turning it on costs money and consumes life.
Running it also creates non-fuel operating cost.
The dispatch model must decide whether the run is still worth it.
```

The guide uses several terms that are easy to mix together:

| Term | Stands for | First-time meaning |
| :--- | :--- | :--- |
| GT | Gas turbine | Burns gas, spins, and directly makes power. |
| HRSG | Heat recovery steam generator | Uses hot GT exhaust to make steam. |
| ST | Steam turbine | Uses HRSG steam to make extra power. |
| VOM | Variable operating and maintenance | Cost that scales with MWh produced. |
| O&M | Operating and maintenance | Broad cost category for running and maintaining the plant. |
| MWh | Megawatt-hour | Unit of energy sold. A 500 MW plant running 2 hours makes 1,000 MWh. |
| Start cost | Not an acronym | Cost assigned to turning the plant on. |
| Aux / auxiliary | Not an acronym | Supporting equipment power, fuel, or systems needed during start/run. |
| Wear cost | Not an exact invoice | Modeled cost for consuming equipment life. |
| EOH reserve | Equivalent Operating Hours reserve | LTSA reserve billing tied to life consumed. |
| Start overage | Contract excess-start charge | Extra charge if annual contracted start limits are exceeded. |
| Dispatch hurdle | Not an acronym | Minimum margin needed before it is worth starting or running. |
| 1x1 | One GT, one HRSG, one ST train | Partial combined-cycle configuration. |
| 2x1 | Two GTs, two HRSGs, one ST | Common combined-cycle block configuration. |

The mental stack is:

```text
physical start -> cost buckets -> dispatch hurdle -> cash-flow impact
```

## The Physical Story Before The Cost Table

A combined-cycle start is not only a gas turbine event.

Simplified sequence:

```text
GT starts and burns fuel
        |
        v
GT exhaust heats the HRSG
        |
        v
HRSG builds steam pressure and temperature
        |
        v
ST warms and accepts steam
        |
        v
plant reaches useful combined-cycle output
```

Each part creates a different cost signal:

| Plant area | What happens during start | Why cost appears |
| :--- | :--- | :--- |
| GT | Ignition, acceleration, synchronization, loading. | Start fuel, auxiliaries, and GT wear. |
| HRSG | Metal heats, pressure rises, drums and headers cycle. | Thermal stress and cycling damage. |
| ST | Steam path warms and expands. | Warming cost and thermal stress. |
| BOP | Pumps, fans, water, emissions, controls operate. | Auxiliary and consumable cost. |

That is why this guide separates GT costs from HRSG/ST costs. The same start affects more than one machine.

## Four Cost Lenses

The same operating decision can be viewed through four lenses.

| Lens | Question it answers | Example |
| :--- | :--- | :--- |
| Dispatch lens | Should the plant run today? | Compare power revenue to fuel, VOM, start cost, and wear. |
| Maintenance lens | How much equipment life did we consume? | EOH, HRSG cycling, combustion fatigue. |
| Contract lens | Did we cross a billing or overage threshold? | Annual start limits and EOH reserve. |
| Cash-flow lens | What dollars hit the model this month/year? | Fixed LTSA fee, VOM, reserves, overages. |

This distinction matters because not every modeled cost is a literal invoice on the day of the start.

Example:

```text
GT wear cost in dispatch = economic signal for life consumption
EOH reserve = contractual reserve accrual
start overage = extra charge only after contract limit is exceeded
```

They are related, but they are not the same cost line.

## How One Start Becomes Model Signals

One start can touch several parts of the model:

```text
plant starts today
  |
  +--> start type is classified as hot, warm, or cold
  |
  +--> GT start cost is added
  |
  +--> HRSG/ST start cost is added
  |
  +--> EOH is added to the maintenance counter
  |
  +--> start count moves toward annual LTSA overage limits
  |
  +--> physical damage trackers may increase
  |
  +--> Step 2 dispatch sees a higher hurdle for the run
```

For a first-time reader, the important point is:

```text
The start is one operating event,
but the model records several consequences.
```

## Why This Matters

Start costs and VOM answer a simple question:

> Besides fuel, what does it cost to start and run the plant?

The dispatch model does not only compare power price to fuel cost. It also needs to know the cost of starting the plant, the variable non-fuel cost of running, and the extra wear created by starts. These costs can decide whether a dispatch opportunity is actually worth taking.

The beginner dispatch idea is:

```text
Run if expected revenue is greater than expected variable cost.
```

For this model, variable cost includes more than fuel:

```text
Variable dispatch cost =
  fuel cost
  + variable O&M
  + allocated start cost
  + EOH/wear penalty when near inspection thresholds
```

Start costs are especially important for cycling plants. A plant that starts frequently can have good spark spreads but still poor economics after wear, LTSA charges, and inspection timing are considered.

## Plain-English Concept

There are four cost ideas that are easy to mix up:

| Cost concept | Unit | Plain meaning |
| :--- | :--- | :--- |
| Start cost | Dollars per start | Cost of turning the plant on. |
| VOM | Dollars per MWh | Variable operating and maintenance cost while producing energy. |
| EOH reserve | Dollars per EOH | LTSA reserve billing tied to equivalent operating hours. |
| Start overage charge | Dollars per excess start | Contract penalty/uplift after annual start limits are exceeded. |

They are related, but they are not the same thing.

Simple example:

```text
One hot start creates:
  start cost
  plus EOH consumption
  plus possible annual start overage exposure

Then each MWh generated creates:
  fuel cost
  plus VOM
```

## Start Cost Vs VOM

Start cost is event-based. It happens when the unit starts.

VOM is production-based. It scales with MWh generated.

| Cost | Trigger | Example |
| :--- | :--- | :--- |
| Start cost | One hot/warm/cold start or trip event | $36K hot start in the framework. |
| VOM | Every MWh generated | $2.50/MWh base VOM in the framework. |

If the plant starts and runs for only a few hours, the start cost is spread over fewer MWh. That makes short runs expensive.

```text
Same hot start cost, different run length:

Short run -> few MWh -> high start cost per MWh
Long run  -> many MWh -> lower start cost per MWh
```

## Why Start Costs Are Split

The Athens CCGT framework splits start costs into:

- GT costs
- HRSG/ST costs

This matters because the physical damage mechanisms are different.

| Area | Main driver | Why it is separate |
| :--- | :--- | :--- |
| GT | EOH, hot gas path wear, fuel, auxiliaries | GT wear moves closer to LTSA thresholds. |
| HRSG/ST | Temperature and pressure swings | Steam-side cycling creates separate damage and costs. |

In a combined-cycle plant, starting the gas turbine also creates steam-side stress. The HRSG and steam turbine need warming, pressure control, and attemperator operation. That is why the framework does not treat the start as GT-only.

## Plant-Type Variations

The idea "starting costs money" is universal. The buckets are plant-type-specific.

| Plant type | Start-cost structure | Modeling warning |
| :--- | :--- | :--- |
| Simple-cycle GT | GT fuel, GT wear, auxiliaries, and BOP cost. | Do not add HRSG/ST cost when no steam-side equipment exists. |
| Combined-cycle GT | GT cost plus HRSG/ST warm-up and steam-side cycling. | Track 1x1 vs 2x1 starts carefully to avoid double-counting. |
| Frame GT | Same broad GT buckets. | Start time, purge, thermal mass, and OEM EOH multipliers may be higher. |
| Aeroderivative GT | GT start cost and maintenance reserve. | Faster start capability does not mean zero wear or zero cost. |
| CHP / cogeneration | Power start cost plus steam/heat service implications. | Steam-host penalties or must-run obligations can dominate dispatch economics. |

Read the Athens tables below as one 2x1 CCGT worked example.

## Before Reading The Framework Tables

The framework tables have several columns. Read them as cost buckets, not as separate physical invoices that always arrive separately.

| Table column | Beginner meaning |
| :--- | :--- |
| GT fuel | Fuel burned during start before full economic generation. |
| GT wear | Modeled cost for using GT maintenance life during the start. |
| GT aux | Supporting power/systems needed for the GT start. |
| GT subtotal | GT-side start cost before adding HRSG/ST cost. |
| EOH charged per GT | Contractual maintenance-life counter added to each GT. |
| HRSG thermal stress | Steam-generator cycling cost from heating and pressure changes. |
| ST warming | Steam-turbine warming and thermal-stress cost. |
| Attemperator wear | Wear from steam temperature-control equipment during starts. |
| HRSG/ST subtotal | Steam-side start cost added at plant level. |
| Plant total | Combined modeled cost for the full plant start. |

Simple map:

```text
GT start cost
  = fuel + wear + auxiliaries

HRSG/ST start cost
  = HRSG thermal stress + ST warming + attemperator wear

Plant start cost
  = GT start cost + HRSG/ST start cost
```

The `EOH charged per GT` column is different. It is not dollars. It is the maintenance-life counter that later affects inspection timing and EOH reserve billing.

## Framework Start Cost Tables

### GT Start Costs

The framework gives GT start costs for both GTs:

| Start type | Shutdown definition | GT fuel | GT wear | GT aux | GT subtotal | EOH charged per GT |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| Hot | Less than 8 hours | $12K | $15K | $3K | $30K | 50 |
| Warm | 8 to 72 hours | $22K | $45K | $5K | $72K | 150 |
| Cold | More than 72 hours | $35K | $105K | $8K | $148K | 350 |
| Trip | Emergency shutdown | $0K | $150K | $10K | $160K | 500 |

### HRSG/ST Start Costs

The framework gives HRSG/ST start costs at plant level:

| Start type | HRSG thermal stress | ST warming | Attemperator wear | HRSG/ST subtotal | HRSG drum fatigue index |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Hot | $3K | $2K | $1K | $6K | 1.0 |
| Warm | $8K | $5K | $3K | $16K | 2.5 |
| Cold | $15K | $8K | $5K | $28K | 5.0 |
| Trip | $5K | $3K | $2K | $10K | 3.0 |

### Combined Plant Start Costs

| Start type | GT subtotal | HRSG/ST subtotal | Plant total |
| :--- | ---: | ---: | ---: |
| Hot | $30K | $6K | $36K |
| Warm | $72K | $16K | $88K |
| Cold | $148K | $28K | $176K |
| Trip | $160K | $10K | $170K |
| 1x1 hot start | $15K | $4K | $19K |

Beginner takeaway:

```text
Hot start  = lowest start cost
Warm start = materially higher
Cold start = very expensive
Trip       = severe wear event, not a normal economic start
```

## ASCII Plot: Start Cost By Type

```text
Plant start cost

Hot   |############                                    | $36K
Warm  |#############################                   | $88K
Cold  |################################################| $176K
Trip  |##############################################  | $170K
```

The exact visual scale is approximate. The important point is that cold starts and trips are much more expensive than hot starts.

## Variable O&M

VOM means variable operating and maintenance cost. It is charged per MWh generated.

The framework's base VOM stack is:

| Component | Cost |
| :--- | ---: |
| LTSA variable component | $1.50/MWh |
| Non-LTSA consumables | $0.40/MWh |
| Water / cooling | $0.25/MWh |
| Emissions compliance | $0.15/MWh |
| BOP wear allowance | $0.20/MWh |
| Total base VOM | $2.50/MWh |

VOM is smaller than fuel cost in many gas-plant cases, but it still matters for marginal dispatch decisions.

Example:

```text
If the plant generates 3,000 MWh:

VOM = 3,000 MWh * $2.50/MWh
VOM = $7,500
```

## How Start Costs Become Dollars Per MWh

A start cost is paid once, but dispatch economics often need to compare costs per MWh.

Example hot start:

| Item | Value |
| :--- | ---: |
| Hot start cost | $36,000 |
| Average output | 500 MW |
| Run length | 8 hours |
| Energy generated | 4,000 MWh |

Allocated start cost:

```text
Energy = 500 MW * 8 hours
Energy = 4,000 MWh

Allocated start cost = $36,000 / 4,000 MWh
Allocated start cost = $9.00/MWh
```

If the same start only supports a 2-hour run:

```text
Energy = 500 MW * 2 hours
Energy = 1,000 MWh

Allocated start cost = $36,000 / 1,000 MWh
Allocated start cost = $36.00/MWh
```

This is why minimum run time matters. Short starts can look profitable hour-by-hour but fail after start costs are allocated.

## Dynamic EOH Proximity Penalty

The framework changes start economics when the plant gets close to an inspection threshold.

The GT wear component is adjusted by the dispatch mode's EOH proximity penalty. HRSG/ST start costs are not adjusted by EOH proximity in this framework because they are driven by thermal cycling, not GT EOH threshold distance.

Mode summary:

| Mode | EOH proximity penalty | Start-cost behavior |
| :--- | :--- | :--- |
| A: Maximize dispatch | 1.0x | Base start costs only. |
| B: Balanced | Up to 2.5x near threshold | GT wear component scales with proximity. |
| C: Minimize LTSA cost | Up to 4.0x near threshold | GT wear scales aggressively; cold starts strongly penalized. |

### Example: Hot Start Near Threshold

Base hot start:

```text
GT fuel = $12K
GT wear = $15K
GT aux = $3K
HRSG/ST = $6K

Base plant hot start = $36K
```

If Mode B applies a 2.5x multiplier to GT wear:

```text
Adjusted GT wear = $15K * 2.5
Adjusted GT wear = $37.5K

Adjusted start cost = $12K + $37.5K + $3K + $6K
Adjusted start cost = $58.5K
```

If Mode C applies a 4.0x multiplier:

```text
Adjusted GT wear = $15K * 4.0
Adjusted GT wear = $60K

Adjusted start cost = $12K + $60K + $3K + $6K
Adjusted start cost = $81K
```

Same physical hot start. Different dispatch mode. Different economic hurdle.

## Start Cost Vs Start Overage Charge

Do not confuse start cost with start overage charge.

| Item | What it means | When it appears |
| :--- | :--- | :--- |
| Start cost | Economic cost of starting the plant. | Every start in dispatch economics. |
| Start overage charge | LTSA charge after exceeding contracted annual start limits. | Only after annual limits are exceeded. |

Framework start overage terms:

| Start type | Annual contracted limit | Overage charge |
| :--- | ---: | ---: |
| Hot start | 150 starts/yr | $8,500 per excess start |
| Warm start | 35 starts/yr | $42,000 per excess start |
| Cold start | 5 starts/yr | $125,000 per excess start |
| Emergency trip | 3 events/yr | $80,000 per excess event |

Example:

```text
Hot starts in year = 170
Contracted hot starts = 150
Excess hot starts = 20
Overage charge = 20 * $8,500
Overage charge = $170,000
```

The start cost still applied to every hot start. The overage charge only applied after the threshold was exceeded.

## LTSA Fixed Fee And EOH Reserve

The framework also includes LTSA costs that are related to operations but should not be confused with VOM.

| LTSA cost item | Rate | Trigger |
| :--- | ---: | :--- |
| Fixed base fee | $850,000/month | Paid monthly, regardless of dispatch. |
| Variable EOH reserve | $175/EOH | Accrues with EOH. |
| LTSA VOM component | $1.50/MWh | Accrues with dispatched MWh. |

Simple EOH reserve example:

```text
Daily EOH = 60
EOH reserve rate = $175/EOH

EOH reserve accrual = 60 * $175
EOH reserve accrual = $10,500
```

The fixed monthly fee is not a marginal dispatch cost in the same way VOM is. It matters for cashflow, but it usually does not decide whether one extra hour should run.

## How Start Costs And VOM Feed Step 2 Dispatch

Step 2 dispatch is the unit commitment and economic dispatch step. It asks whether the plant should start, stay online, shut down, or remain idle.

Start costs and VOM enter the dispatch decision like this:

```text
Power revenue
  - fuel cost
  - VOM
  - allocated start cost
  - EOH proximity penalty
  = dispatch margin
```

If dispatch margin is positive, the model may run. If dispatch margin is negative, it should avoid the run unless some other constraint or value applies.

ASCII flow:

```text
Hourly prices + gas price
        |
        v
Fuel cost from heat rate
        |
        v
Add VOM and start cost
        |
        v
Adjust GT wear if close to EOH threshold
        |
        v
Run only if margin clears the hurdle
```

## Worked Dispatch Example

Assume a hot start and 8-hour run:

| Item | Value |
| :--- | ---: |
| Power price | $55/MWh |
| Fuel cost | $30/MWh |
| VOM | $2.50/MWh |
| Hot start cost | $36,000 |
| Average output | 500 MW |
| Run length | 8 hours |

Calculate energy:

```text
Energy = 500 MW * 8 hours
Energy = 4,000 MWh
```

Allocate start cost:

```text
Start cost per MWh = $36,000 / 4,000 MWh
Start cost per MWh = $9/MWh
```

Dispatch margin:

```text
Margin = power price - fuel cost - VOM - allocated start cost
Margin = $55 - $30 - $2.50 - $9
Margin = $13.50/MWh
```

In this simple case, the run clears the hurdle.

Now suppose the plant is close to an EOH threshold and Mode B raises the hot start cost to $58.5K:

```text
Adjusted start cost per MWh = $58,500 / 4,000 MWh
Adjusted start cost per MWh = $14.63/MWh

Adjusted margin = $55 - $30 - $2.50 - $14.63
Adjusted margin = $7.87/MWh
```

The run still clears, but the margin is weaker. A lower-price day might no longer dispatch.

## What The Framework Includes

The high-level framework includes these cost concepts:

- GT start costs are split into fuel, wear, and auxiliary components.
- HRSG/ST start costs are tracked separately from GT costs.
- Combined plant start costs are listed for hot, warm, cold, trip, and 1x1 hot start cases.
- GT wear cost scales with EOH proximity in Modes B and C.
- HRSG/ST start costs do not scale with EOH proximity in this framework.
- Base VOM is $2.50/MWh.
- LTSA fixed fee, EOH reserve, and LTSA VOM are separate cost lines.
- Start overage charges apply after contracted annual start limits are exceeded.

## What The Framework Leaves Out

The framework gives a useful due-diligence structure, but several details need confirmation.

| Missing detail | Why it matters |
| :--- | :--- |
| Actual LTSA start-cost definitions | Current values are assumptions pending contract review. |
| Whether start costs are per plant, per GT, or per operating block in every case | Prevents double-counting in a 2x1 plant. |
| Actual fuel used during each start type | Improves start fuel cost estimates. |
| Failed-start treatment | Failed starts may incur cost and EOH without producing MWh. |
| Startup emissions or permit constraints | Could add cost or restrict dispatch. |
| Actual HRSG/ST cycling cost basis | Needed to validate steam-side cost split. |
| Overage billing timing | Quarterly, monthly, or contract-year treatment changes cashflow timing. |
| Whether VOM escalates separately from LTSA rates | Changes long-term cost projection. |

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 3.4 | Dispatch modes and EOH proximity penalties. | Green for model design. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.4.3 | LTSA payment structure, fixed fee, EOH reserve, and LTSA VOM. | Amber because contract values are assumed. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.4.4 | Contracted start limits and overage charges. | Amber because contract values are assumed. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.5 | GT and HRSG/ST start-cost decomposition. | Amber until validated against asset data. |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.6 | Base VOM stack. | Amber until validated against plant budget. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Daily flowchart, dynamic start-cost adjustment, and dispatch-mode framing. | Green for framework communication. |
| NREL Power Plant Cycling Costs | Cycling cost context for fossil plants and dispatch/utility planning. | Green for general cycling-cost context, not asset-specific values. |

## Open Questions Before Investment Use

Before relying on start-cost and VOM outputs in a final investment decision, resolve these:

| Question | Why it matters |
| :--- | :--- |
| Are the start-cost values actual contract/equipment values or placeholders? | Sets dispatch hurdle accuracy. |
| Are GT start costs listed for both GTs, one GT, or the plant block? | Prevents double-counting. |
| How should 1x1 operation allocate HRSG/ST cost? | Important for partial dispatch. |
| Does the LTSA explicitly define EOH proximity penalties, or are they modeling constructs? | Separates contract cash cost from dispatch optimization penalty. |
| Are start overage charges billed monthly, quarterly, or annually? | Affects cashflow timing. |
| Is VOM fixed at $2.50/MWh or escalated over time? | Affects long-run dispatch and EBITDA. |
| Are emissions costs fully captured in VOM? | Missing emissions costs can overstate margins. |
| Are failed starts and trips treated as starts, overages, EOH events, or separate events? | Important for high-cycling risk. |

## Quick Recap

Start costs are paid when the plant starts. VOM is paid for every MWh produced. EOH reserve is tied to life consumption. Start overage charges apply only after contracted limits are exceeded.

For this model:

```text
Start type sets start cost.
MWh output sets VOM.
EOH proximity can raise GT wear cost.
Start overages add contract exposure.
Step 2 dispatch uses all of this to decide whether a run is worth it.
```

That is why start costs and VOM come after EOH in the basics path. EOH explains how operation consumes life; this guide explains how that life consumption becomes a dispatch hurdle and cashflow item.
