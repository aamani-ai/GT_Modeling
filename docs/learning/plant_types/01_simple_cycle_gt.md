# Simple-Cycle Gas Turbine

## What This Guide Is

This guide explains what changes when the plant is a simple-cycle gas turbine instead of a combined-cycle gas turbine.

Read these first if the words are new:

- [Gas Plant Type Map](../basics/00_gas_plant_type_map.md)
- [Capacity](../basics/01_capacity.md)
- [Heat Rate](../basics/02_heat_rate.md)
- [EOH And Starts](../basics/03_eoh_and_starts.md)
- [Start Costs And VOM](../basics/04_start_costs_and_vom.md)

> Plant-Type Note
> A simple-cycle GT has a gas turbine, generator, stack, and supporting systems. It does not have an HRSG or steam turbine in the basic plant stack. Do not apply Athens CCGT HRSG/ST start costs, HRSG cycling damage, 1x1/2x1 steam-cycle logic, or steam-turbine outage categories to a simple-cycle GT.

## First-Time Reader Map

If this topic is new, start with the equipment question:

```text
Does the plant recover GT exhaust heat to make steam?

No  -> simple-cycle GT
Yes -> combined-cycle GT or CHP/cogeneration with heat recovery
```

The guide uses these terms:

| Term | First-time meaning |
| :--- | :--- |
| GT | Gas turbine; compresses air, burns fuel, spins, and makes power. |
| Simple-cycle GT | Gas turbine plant that sends hot exhaust to the stack instead of using it for a steam cycle. |
| CT | Combustion turbine; often used in power markets to mean a simple-cycle gas turbine. |
| Open-cycle GT | Another name often used for simple-cycle GT. |
| Generator | Converts rotating mechanical energy into electricity. |
| Stack | Exhaust path where hot gases leave the plant. |
| BOP | Balance of plant; support systems around the GT and generator. |
| Pmax | Maximum feasible MW under current conditions. |
| Pmin | Minimum stable MW once the unit is online. |
| Peaker | Plant that mainly runs during high-price or high-demand hours. |
| Reserve | Capacity kept available for reliability or fast response. |

The mental stack is:

```text
simple equipment stack -> faster/flexible operation -> GT-only cost and damage model
```

## Equipment Map

A simple-cycle GT is the direct gas-turbine power block.

```text
natural gas + air
      |
      v
   +------+
   |  GT  |------ generator ------ electricity
   +------+
      |
      v
 exhaust stack
```

The basic energy path is:

```text
fuel energy
  -> hot gas in the turbine
  -> shaft power
  -> generator output
  -> electricity
```

The plant still needs support systems:

| System | Why it matters |
| :--- | :--- |
| Fuel gas system | Delivers gas at the pressure and quality the GT needs. |
| Inlet air system | Filters and conditions the air entering the compressor. |
| Exhaust stack / emissions controls | Routes exhaust and controls compliance obligations. |
| Lube oil and hydraulic systems | Protect bearings, actuators, and moving parts. |
| Controls and protection | Starts, trips, synchronization, alarms, and safety logic. |
| Generator and electrical equipment | Converts and exports power. |
| Fire protection and auxiliaries | Supports safe operation and startup. |

## What A Simple-Cycle GT Does Not Have

The easiest way to avoid modeling mistakes is to list what is absent.

| CCGT item | Simple-cycle status | Modeling consequence |
| :--- | :--- | :--- |
| HRSG | Not present in basic simple-cycle plant. | No HRSG thermal-stress cost and no HRSG drum fatigue tracker. |
| ST | Not present. | No steam-turbine warm-up cost or ST outage category. |
| Steam cycle | Not present. | No steam-bottoming contribution to heat rate or capacity. |
| 1x1 / 2x1 steam mode | Not relevant. | Dispatch is unit-level or GT-block-level, not combined-cycle block mode. |
| HRSG attemperator wear | Not present. | Do not add attemperator wear to start cost. |
| Steam-host obligation | Usually not present. | Unless it is actually CHP, do not add steam-service constraints. |

Simple warning:

```text
Simple-cycle GT = GT-only power conversion.
CCGT = GT power plus recovered exhaust heat through HRSG/ST.
```

## Why This Matters

Simple-cycle GT modeling is not "smaller CCGT modeling." The economics and risk stack are different.

| Topic | Simple-cycle effect |
| :--- | :--- |
| Efficiency | Usually worse heat rate than CCGT because exhaust heat is not recovered. |
| Flexibility | Often valuable for starts, peaks, reserves, and fast response. |
| Start costs | GT and BOP costs only; no HRSG/ST cost bucket. |
| Degradation | GT compressor, combustor, hot section, TBC, and rotor still matter. |
| Outages | GT, generator, controls, fuel, emissions, and BOP matter; HRSG/ST categories do not. |
| Dispatch | Often fewer run hours, more starts, and stronger sensitivity to start cost and Pmin/Pmax. |

Financially, simple-cycle plants often make money from scarcity and flexibility:

```text
few operating hours
  +
high-price windows / reserve value
  -
fuel + VOM + start cost + wear
  =
economic value
```

## Simple-Cycle Vs Combined-Cycle

| Topic | Simple-cycle GT | Combined-cycle GT |
| :--- | :--- | :--- |
| Main equipment | GT + generator + stack. | GT + HRSG + ST + generator(s). |
| Exhaust heat | Leaves through stack. | Recovered to make steam. |
| Heat rate | Usually higher. | Usually lower because extra power is made from exhaust heat. |
| Start complexity | GT-focused. | GT plus HRSG/ST warm-up. |
| Start cost buckets | GT/BOP. | GT plus HRSG/ST. |
| Degradation scope | GT-focused. | GT plus steam-side cycling. |
| Dispatch style | Peaking, reserves, fast response, short runs. | Mid-merit, cycling, baseload, or flexible operation. |
| State variables | GT and plant support state. | GT, HRSG, ST, cooling, and block-level state. |

ASCII comparison:

```text
Simple-cycle:

fuel + air -> GT -> electricity
              |
              v
            stack

Combined-cycle:

fuel + air -> GT -> electricity
              |
              v
            HRSG -> steam -> ST -> electricity
```

## Frame Vs Aeroderivative Simple-Cycle Units

Simple-cycle describes the plant layout. Frame and aeroderivative describe the turbine technology.

| Topic | Frame simple-cycle GT | Aeroderivative simple-cycle GT |
| :--- | :--- | :--- |
| Typical size | Larger industrial machine. | Smaller or modular utility machine. |
| Common role | Peaking, reserve, grid support, sometimes seasonal capacity. | Fast-start peaking, reserves, flexible response. |
| Start behavior | Often heavier thermal mass and more thermal limits. | Often faster-starting and more start-capable. |
| Maintenance style | Larger outage scope and OEM-specific inspection logic. | Can involve module swaps and different maintenance intervals. |
| Modeling warning | Do not assume aero start/ramp behavior. | Do not assume large-frame inspection and cost behavior. |

The plant-type guide only tells you there is no steam bottoming cycle. It does not tell you the exact start time, ramp rate, EOH multiplier, or maintenance contract. Those still need asset data.

## Capacity, Pmax, And Pmin

A simple-cycle GT still needs a feasible output range.

```text
offline
  |
  v
if online, dispatch usually chooses output between:

Pmin ------------------------- Pmax
```

| Term | Simple-cycle meaning |
| :--- | :--- |
| Pmax | Maximum GT/generator output after weather, degradation, and outage condition. |
| Pmin | Minimum stable GT output when online. |
| Pmax(T) | Hot-weather maximum output curve. |
| Pmin(T) | Minimum stable load under current conditions, if modeled. |

Ambient temperature still matters because the GT is an air-breathing machine:

```text
hotter air
  -> lower air density
  -> lower compressor mass flow
  -> lower GT output
  -> lower Pmax
```

What changes from Athens:

| Athens CCGT capacity item | Simple-cycle treatment |
| :--- | :--- |
| GT output plus ST output | GT/generator output only. |
| HRSG/ST contribution | Not present. |
| 1x1 vs 2x1 capacity blocks | Not relevant unless the simple-cycle site has multiple GTs. |
| Cooling-system steam-cycle effects | Not relevant unless site-specific aux/cooling effects exist. |

## Heat Rate

Simple-cycle heat rate is GT-only net fuel intensity.

```text
Fuel cost per MWh = heat rate in MMBtu/MWh * gas price in $/MMBtu
```

Simple-cycle heat rate is usually worse than combined-cycle heat rate because the hot exhaust is not used to make additional steam-turbine power.

Beginner picture:

```text
Simple-cycle:
  fuel -> GT power -> stack loses hot exhaust

Combined-cycle:
  fuel -> GT power + steam-cycle power from exhaust heat
```

Modeling details that matter:

| Item | Why it matters |
| :--- | :--- |
| Average heat rate | Useful for simple fuel-cost examples and performance reporting. |
| Incremental heat rate | Important for dispatch and offer curves. |
| Part-load heat rate | Short runs may spend time at inefficient output levels. |
| Ambient correction | Hot weather can worsen heat rate. |
| Degradation | Fouling, erosion, and hot-section condition can increase fuel intensity. |

Do not use the Athens CCGT `7,070 Btu/kWh` baseline as a simple-cycle value. It is a combined-cycle worked-example number.

## Starts, EOH, And Cycling

Simple-cycle GTs can be start-heavy.

```text
Peaking day:
  offline most hours
  start for high-price window
  run a few hours
  shut down
```

That means starts can dominate maintenance life even when fired hours are low.

| Operating pattern | Fired hours | Starts | Main modeling concern |
| :--- | ---: | ---: | :--- |
| Rare peaker | Low | Low to medium | Few revenue hours, high value per start. |
| Daily peaker | Medium | High | Start cost and EOH can dominate economics. |
| Reserve / fast response | Low | Variable | Start reliability and availability matter. |
| Emergency or trip-heavy duty | Variable | Severe events | Tail risk and forced outage exposure rise. |

The same warning from the basics guide applies:

```text
hot/warm/cold thresholds are not universal
EOH multipliers are not universal
contract limits are not universal
```

Use OEM, LTSA/CSA, operating procedures, and actual start logs before setting final values.

## Start Costs And VOM

A simple-cycle start cost is usually a GT/BOP cost stack.

```text
simple-cycle start cost
  = GT fuel during start
  + GT wear / maintenance life cost
  + auxiliaries and consumables
  + any contract start charge or overage effect
```

What to remove from the Athens CCGT start-cost logic:

| Athens CCGT bucket | Simple-cycle treatment |
| :--- | :--- |
| HRSG thermal stress | Remove unless heat-recovery equipment exists. |
| ST warming | Remove. |
| Attemperator wear | Remove. |
| HRSG drum fatigue index | Remove. |
| 1x1 hot start | Replace with unit-specific multi-GT logic if the site has multiple simple-cycle GTs. |

VOM still matters:

```text
running cost = fuel cost + VOM + wear cost
```

For short runs, start cost per MWh can be very high:

```text
same start cost spread over fewer MWh
  -> higher $/MWh hurdle
```

## Dispatch Role

Simple-cycle GTs often run for flexibility value.

| Dispatch use | What it means |
| :--- | :--- |
| Peaking energy | Run only in high-price hours. |
| Reserve | Stay available for grid reliability products. |
| Fast response | Start or ramp quickly when the system needs capacity. |
| Seasonal capacity | Earn value by being available during stressed periods. |
| Reliability support | Local grid or voltage/reliability role, if contracted. |

Step 2 still works hourly:

```text
hourly price and weather
        |
        v
commit or stay offline
        |
        v
choose MW between Pmin and Pmax
        |
        v
daily state update
```

The daily update is still needed:

```text
starts + fired hours + trips + derates
        |
        v
EOH, degradation, outage risk, next-day economics
```

## Outages And Availability

Simple-cycle outage categories should match the equipment present.

| Outage category | Simple-cycle relevance |
| :--- | :--- |
| GT forced outage | Yes. |
| Compressor / combustor / hot-section issue | Yes. |
| Generator outage | Yes. |
| Controls / protection issue | Yes. |
| Fuel gas issue | Yes. |
| Emissions or permit constraint | Yes. |
| BOP / auxiliary issue | Yes. |
| HRSG outage | No, unless heat-recovery equipment exists. |
| Steam turbine outage | No. |
| HRSG attemperator issue | No. |

Availability still comes before dispatch economics:

```text
if unavailable:
  no dispatch revenue

if available:
  dispatch decides whether the run is economic
```

## Degradation Applicability

Simple-cycle plants still have GT degradation. They do not have steam-side CCGT degradation.

| Degradation guide | Applies to simple-cycle GT? | Why |
| :--- | :---: | :--- |
| [EOH accumulation with creep-fatigue coupling](../degradation_factors/01_eoh_creep_fatigue_coupling.md) | Yes | GT hot-section and contract-life concept. |
| [Capacity derating from ambient temperature](../degradation_factors/02_capacity_derating.md) | Yes | GT output depends on inlet air conditions. |
| [Heat rate degradation](../degradation_factors/03_heat_rate_degradation.md) | Yes | Fouling, erosion, and GT condition affect fuel intensity. |
| [Combustion cycling fatigue](../degradation_factors/04_combustion_cycling_fatigue.md) | Yes | Starts, trips, and load swings stress combustor hardware. |
| [HRSG cycling damage](../degradation_factors/05_hrsg_cycling_damage.md) | No | No HRSG/ST in a basic simple-cycle plant. |
| [Compressor degradation](../degradation_factors/06_compressor_degradation.md) | Yes | Compressor condition affects both MW and heat rate. |
| [Thermal barrier coating life](../degradation_factors/07_tbc_life.md) | Maybe / yes | Applies if the GT uses coated hot gas path components. |
| [Rotor life consumption](../degradation_factors/08_rotor_life_consumption.md) | Yes | GT rotor start-stop and hours-at-speed risk remain. |

ASCII view:

```text
Simple-cycle degradation stack

GT compressor       yes
GT combustor        yes
GT hot section      yes
GT TBC              machine-specific
GT rotor            yes
HRSG drum           no
ST warming          no
```

## State Vector For A Simple-Cycle GT

A simple-cycle state vector should be smaller than a CCGT state vector.

Possible state variables:

| State variable | Why it matters |
| :--- | :--- |
| Current EOH | Inspection timing and contract reserve. |
| Fired hours | Runtime and degradation exposure. |
| Hot/warm/cold start counts | Start cost, EOH, and contract limits. |
| Trips | Severe stress and forced outage signal. |
| Effective Pmax | Dispatch cap after weather, outage, and degradation. |
| Effective Pmin | Minimum online output, if modeled. |
| Heat rate | Fuel cost and dispatch competitiveness. |
| Compressor fouling | Recoverable heat-rate and capacity loss. |
| Compressor erosion | Persistent performance loss. |
| Combustion fatigue index | GT forced outage risk. |
| TBC state | Hot-section coating risk, if applicable. |
| Rotor life fraction | Low-probability, high-severity tail risk. |
| Outage status | Blocks or derates dispatch. |

Variables that usually should not appear:

| CCGT state variable | Why not |
| :--- | :--- |
| HRSG drum fatigue | No HRSG in simple-cycle plant. |
| ST warming state | No steam turbine. |
| 1x1 vs 2x1 CCGT mode | Not a simple-cycle block concept. |
| Steam-host obligation | Not unless the asset is CHP. |

## Worked Example: One Simple-Cycle Peaking Day

This is a teaching example, not a universal cost assumption.

Assume one simple-cycle GT has:

| Item | Example value |
| :--- | ---: |
| Pmax today | 100 MW |
| Pmin today | 45 MW |
| Dispatched output | 90 MW |
| Run time | 4 hours |
| Start type | Hot start |
| Heat rate | 10.5 MMBtu/MWh |
| Gas price | $4.00/MMBtu |
| VOM | $4/MWh |
| GT start cost | $20,000 |

Energy:

```text
MWh = 90 MW * 4 hours
MWh = 360
```

Fuel cost:

```text
fuel cost per MWh = 10.5 * 4.00
fuel cost per MWh = $42/MWh
```

Start cost spread over MWh:

```text
start cost per MWh = 20,000 / 360
start cost per MWh = $55.56/MWh
```

Dispatch hurdle before other wear or contract penalties:

```text
fuel cost       = $42.00/MWh
VOM             =  $4.00/MWh
start cost/MWh  = $55.56/MWh
--------------------------------
simple hurdle   = $101.56/MWh
```

Why short runs are hard:

```text
same $20,000 start cost

2 hour run  -> fewer MWh -> higher start cost per MWh
8 hour run  -> more MWh  -> lower start cost per MWh
```

ASCII view:

```text
Start-cost burden

High $/MWh |########## 2 hour run
           |#####      4 hour run
Low $/MWh  |##         8 hour run
           +-------------------------
              longer run spreads start cost
```

## How This Feeds Step 2 Dispatch

For a simple-cycle GT, Step 2 needs:

| Input | Why Step 2 needs it |
| :--- | :--- |
| Hourly power prices | Decides which hours may be worth running. |
| Daily or hourly gas price | Converts heat rate into fuel cost. |
| Pmax and Pmin | Defines feasible MW range. |
| Start cost | Sets the hurdle for short runs. |
| Start type / shutdown duration | Changes cost and EOH. |
| Heat rate curve | Converts output into fuel burn. |
| Availability state | Blocks dispatch if unavailable. |
| EOH / inspection headroom | Can create conservative dispatch near thresholds. |

Simplified decision:

```text
run if:
  expected margin over online hours
  >
  start cost + VOM + wear + operating constraints
```

## How To Read Existing Learning Docs For Simple-Cycle

| Existing guide | How to read it for simple-cycle |
| :--- | :--- |
| [Capacity](../basics/01_capacity.md) | Use Pmax/Pmin and ambient derate concepts, but remove ST output. |
| [Heat Rate](../basics/02_heat_rate.md) | Use fuel-intensity logic, but do not use Athens CCGT heat-rate values. |
| [EOH And Starts](../basics/03_eoh_and_starts.md) | Use the concept, but verify simple-cycle OEM/LTSA start rules. |
| [Start Costs And VOM](../basics/04_start_costs_and_vom.md) | Use cost-bucket logic, but remove HRSG/ST buckets. |
| [Dispatch And The Daily Loop](../basics/05_dispatch_and_daily_loop.md) | Use hourly dispatch inside daily state update; constraints are simpler than CCGT. |
| [Outages, Availability, And LTSA](../basics/06_outages_availability_and_ltsa.md) | Use outage/availability logic, but remove HRSG/ST outage categories. |
| [State Vector And Feedback](../basics/07_state_vector_and_feedback.md) | Use model-memory logic, but simplify the state schema. |

## What The Current Framework Includes

The current high-level framework is anchored on an Athens 2x1 CCGT worked example. For simple-cycle use, it still gives helpful structure:

| Framework idea | Reusable for simple-cycle? | Note |
| :--- | :---: | :--- |
| Five-step simulation pipeline | Yes | Climate/market, dispatch, engineering update, LTSA, cashflow still apply. |
| Hourly dispatch inside daily state update | Yes | Same modeling pattern. |
| Capacity and heat-rate feedback | Yes | Use simple-cycle curves instead of Athens CCGT values. |
| EOH and start accounting | Yes, with calibration | Contract/OEM values must change if the LTSA differs. |
| GT forced-outage risk from stress state | Yes | Combustion, TBC, rotor, and compressor states still matter. |
| HRSG cycling damage | No | Remove unless heat-recovery equipment exists. |
| HRSG/ST start cost split | No | Use GT/BOP start cost instead. |

## What The Framework Leaves Out For Simple-Cycle Use

Before using this for investment work, a simple-cycle case needs its own data.

| Missing item | Why it matters |
| :--- | :--- |
| Simple-cycle asset identity | Model, vintage, site, fuel, emissions controls, and operating role matter. |
| OEM performance curves | Pmax(T), heat rate, part-load, and start behavior are machine-specific. |
| Actual LTSA/CSA terms | EOH, starts, inspections, coverage, and overages are contract-specific. |
| Start time and ramp rates | Determines whether short high-price windows are reachable. |
| Pmin and min up/down | Determines feasible dispatch after commitment. |
| Emissions constraints | Starts and run hours may be permit-limited. |
| Real outage history | Validates forced-outage assumptions. |
| Compressor wash history | Improves fouling and heat-rate degradation modeling. |

## Source Basis And Certainty

| Source | Use in this guide | Certainty |
| :--- | :--- | :--- |
| [Gas Plant Type Map](../basics/00_gas_plant_type_map.md) | Plant-type separation and applicability matrix. | Green for learning structure. |
| [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md) | Contrast case showing what not to copy into simple-cycle. | Green for local example; not a simple-cycle source. |
| `docs/InfraSure_ModelingFramework_V2.md` | Five-step model structure, GT degradation factors, LTSA/dispatch feedback pattern. | Green for framework structure; Amber for transfer to non-Athens assets. |
| Existing basics guides | Capacity, heat rate, EOH, dispatch, outage, and state concepts. | Green for concepts; plant-specific values need calibration. |
| Existing degradation guides | GT damage factors and HRSG exclusion boundary. | Green for learning applicability; factor parameters need asset data. |

## Open Questions Before Modeling A Simple-Cycle Asset

| Question | Why it matters |
| :--- | :--- |
| Is the unit frame or aeroderivative? | Changes start, ramp, maintenance, and degradation assumptions. |
| What is the exact GT model and vintage? | Determines performance curves and inspection logic. |
| What are Pmax(T), Pmin(T), and heat-rate curves? | Needed for dispatch and offers. |
| What LTSA/CSA terms apply? | Defines EOH, starts, coverage, inspections, and overages. |
| What is the unit's market role? | Peaker, reserve, reliability, or energy dispatch changes value. |
| Are starts or emissions permit-limited? | Can cap dispatch even when economics look attractive. |
| Is there multiple-unit site logic? | A site with several simple-cycle GTs may need unit-level state. |
| What is the historical start/trip/outage record? | Validates risk and maintenance assumptions. |
| Is inlet cooling or special emissions equipment installed? | Can change Pmax, heat rate, starts, and outage categories. |

## Quick Recap

A simple-cycle GT is not a CCGT without the steam cycle hidden in the background. The steam cycle is absent, so the model must be simpler in the right places.

```text
Keep:
  GT capacity, heat rate, starts, EOH, compressor, combustor, TBC, rotor,
  outages, dispatch, and state feedback.

Remove:
  HRSG/ST start costs, HRSG drum fatigue, ST warming, CCGT 1x1/2x1 logic,
  and steam-side outage categories.
```

That is the main modeling discipline: use the universal concepts, but only keep the variables that match the equipment actually present.
