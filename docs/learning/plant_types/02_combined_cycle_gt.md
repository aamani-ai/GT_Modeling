# Combined-Cycle Gas Turbine

## What This Guide Is

This guide explains the combined-cycle gas turbine plant type.

Read these first:

- [Gas Plant Type Map](../basics/00_gas_plant_type_map.md)
- [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md)
- [Simple-Cycle Gas Turbine](./01_simple_cycle_gt.md)
- [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md)

> Plant-Type Note
> This guide is about CCGT plants. It is not a universal gas-plant guide. A simple-cycle GT does not have HRSG/ST start cost or HRSG cycling damage. A CHP plant may have steam obligations that are not captured by a merchant CCGT example.

## First-Time Reader Map

A CCGT uses two linked cycles:

```text
gas turbine cycle
  +
steam cycle using recovered exhaust heat
```

Key terms:

| Term | First-time meaning |
| :--- | :--- |
| CCGT | Combined-cycle gas turbine. |
| GT | Gas turbine; burns fuel and makes electricity directly. |
| HRSG | Heat recovery steam generator; uses GT exhaust to make steam. |
| ST | Steam turbine; uses HRSG steam to make more electricity. |
| 1x1 | One GT, one HRSG, one ST configuration or operating mode. |
| 2x1 | Two GTs, two HRSGs, one ST configuration or operating mode. |
| BOP | Balance of plant support systems. |
| Duct firing | Optional extra firing in HRSG duct, if present. |
| Condenser / cooling | Steam-cycle heat rejection equipment. |

The mental stack is:

```text
GT output + steam-cycle recovery -> better heat rate but more constraints
```

## Equipment Map

```text
natural gas + air
      |
      v
     GT ---- electricity
      |
      | hot exhaust
      v
    HRSG ---- steam ---- ST ---- electricity
      |
      v
    stack
```

A 2x1 CCGT looks like:

```text
GT-A -> HRSG-A --+
                 +--> common steam system -> ST -> electricity
GT-B -> HRSG-B --+
```

## Why CCGT Is Different From Simple-Cycle

| Topic | Simple-cycle GT | CCGT |
| :--- | :--- | :--- |
| Exhaust heat | Leaves through stack. | Recovered in HRSG. |
| Efficiency | Usually lower. | Usually higher. |
| Equipment | GT + generator + stack. | GT + HRSG + ST + cooling + BOP. |
| Start cost | GT/BOP only. | GT plus HRSG/ST warm-up. |
| Degradation | GT-focused. | GT plus steam-side cycling. |
| Outages | GT/generator/BOP. | GT, HRSG, ST, cooling, BOP, generator. |
| Dispatch | Peaking/reserve often. | Mid-merit, baseload, cycling, flexible operation. |

Beginner shortcut:

```text
CCGT = more efficient, but more complicated
```

## 1x1 And 2x1 Modes

The CCGT configuration changes dispatch and cost.

| Mode | Meaning | Why it matters |
| :--- | :--- | :--- |
| Offline | No GT running. | Output is zero; start may be needed. |
| 1x1 | One GT/HRSG train supports steam cycle. | Lower capacity and lower start cost than full 2x1. |
| 2x1 | Two GT/HRSG trains support shared ST. | Higher capacity and often better full-block efficiency. |
| Derated | One or more systems limit output. | Pmax falls; Pmin may also change. |

Important:

```text
1x1 and 2x1 are not just capacity labels.
They can change heat rate, start cost, HRSG cycling, EOH by GT, and outage state.
```

## Capacity And Operating Range

CCGT capacity is not just GT output.

```text
net CCGT output =
  GT electrical output
  + ST electrical output
  - auxiliary load
```

Pmin/Pmax should be mode-specific:

| Mode | Needs |
| :--- | :--- |
| 1x1 | Pmin_1x1, Pmax_1x1, heat-rate curve, start cost. |
| 2x1 | Pmin_2x1, Pmax_2x1, heat-rate curve, start cost. |
| Duct-fired mode | Separate Pmax and heat-rate behavior if used. |
| Derated mode | Reduced Pmax and availability treatment. |

Athens gives a Pmax-style 2x1 table:

| Ambient temperature | Net plant capacity |
| :--- | ---: |
| 0 deg F | 565 MW |
| 20 deg F | 552 MW |
| 59 deg F ISO | 531 MW |
| 80 deg F | 499 MW |
| 95 deg F | 469 MW |

That table does not fully define Pmin or 1x1 operation.

## Heat Rate

CCGT heat rate is usually better than simple-cycle heat rate because the ST makes extra power from recovered heat.

```text
same GT fuel input
  -> GT power
  -> plus steam-cycle power
  -> lower net heat rate
```

But CCGT heat rate depends on:

- load level
- 1x1 vs 2x1 mode
- ambient temperature
- condenser and cooling performance
- HRSG condition
- GT compressor condition
- duct firing, if present
- auxiliary loads

Athens example values:

| Condition | Heat rate |
| :--- | ---: |
| Post-HGP baseline at ISO | 7,070 Btu/kWh |
| At 90 deg F ambient | 7,230 Btu/kWh |
| At 50% minimum load, ISO | 8,215 Btu/kWh |

These are Athens worked-example values, not universal CCGT constants.

## Starts And Warm-Up

A CCGT start has multiple thermal systems:

```text
GT starts
  |
  v
GT exhaust heats HRSG
  |
  v
steam pressure and temperature rise
  |
  v
ST warms and accepts steam
  |
  v
combined-cycle output
```

This is why CCGT start costs include more than GT start cost.

| Equipment | Start-related issue |
| :--- | :--- |
| GT | Fuel, auxiliaries, EOH, hot-section wear. |
| HRSG | Drum, headers, tubes, and attemperator cycling. |
| ST | Rotor/casing warming and steam admission. |
| BOP | Pumps, fans, water, controls, emissions systems. |

Hot/warm/cold thresholds are still contract- and OEM-specific.

## Start Costs And VOM

The Athens CCGT example separates:

```text
GT start cost
  +
HRSG/ST start cost
  =
plant start cost
```

Example Athens totals:

| Start type | GT subtotal | HRSG/ST subtotal | Plant total |
| :--- | ---: | ---: | ---: |
| Hot | $30K | $6K | $36K |
| Warm | $72K | $16K | $88K |
| Cold | $148K | $28K | $176K |
| Trip | $160K | $10K | $170K |
| 1x1 hot start | $15K | $4K | $19K |

Modeling warning:

```text
If dispatch can choose 1x1 or 2x1,
start cost should follow the actual mode and train started.
```

## Dispatch Role

CCGTs can play several roles.

| Role | Dispatch behavior |
| :--- | :--- |
| Baseload | Runs many hours, fewer starts. |
| Mid-merit | Runs when spreads are good, may cycle seasonally. |
| Daily cycling | Starts and stops around price shape. |
| Flexible CCGT | Uses 1x1/2x1 and part-load operation to follow market value. |
| Reliability / contracted | Runs under contract or reliability obligations. |

Step 2 dispatch must respect:

- Pmin/Pmax by mode
- ramp limits
- min up/down
- start time
- heat-rate curve by mode
- start costs
- EOH and inspection headroom
- outage and derate state

## Outages And Availability

CCGT outages can be full or partial.

| Outage area | Possible dispatch effect |
| :--- | :--- |
| GT-A outage | GT-B may still support 1x1 operation. |
| GT-B outage | GT-A may still support 1x1 operation. |
| HRSG-A outage | GT-A train may be blocked or simple-cycle bypass may be unavailable. |
| ST outage | GT-only operation may or may not be possible depending plant design. |
| Cooling system limitation | Net output and heat rate may worsen. |
| BOP / controls outage | Can block entire plant. |
| Generator/switchyard issue | Can block output even if turbines are healthy. |

Do not assume every outage means zero MW. Do not assume every outage leaves partial operation available. The plant design and interconnection matter.

## Degradation Applicability

| Degradation guide | Applies to CCGT? | Why |
| :--- | :---: | :--- |
| [EOH accumulation with creep-fatigue coupling](../degradation_factors/01_eoh_creep_fatigue_coupling.md) | Yes | GT hot-section and contract-life concept. |
| [Capacity derating from ambient temperature](../degradation_factors/02_capacity_derating.md) | Yes | GT and steam-cycle output change with weather. |
| [Heat rate degradation](../degradation_factors/03_heat_rate_degradation.md) | Yes | GT, HRSG, ST, BOP, and cooling can affect net heat rate. |
| [Combustion cycling fatigue](../degradation_factors/04_combustion_cycling_fatigue.md) | Yes | GT combustor cycles with starts/trips/load swings. |
| [HRSG cycling damage](../degradation_factors/05_hrsg_cycling_damage.md) | Yes | HRSG and steam-side equipment cycle during starts. |
| [Compressor degradation](../degradation_factors/06_compressor_degradation.md) | Yes | GT compressor condition affects MW and heat rate. |
| [Thermal barrier coating life](../degradation_factors/07_tbc_life.md) | Yes, if coated GT hot parts | GT hot-section protection. |
| [Rotor life consumption](../degradation_factors/08_rotor_life_consumption.md) | Yes | GT rotor start/stop and hours-at-speed risk remain. |

## State Vector For A CCGT

A CCGT state vector may need unit, train, and block-level state.

| State variable | Why it matters |
| :--- | :--- |
| EOH by GT | GT-A and GT-B can diverge. |
| Start counts by GT and type | Contract and wear accounting. |
| Current operating mode | 1x1 vs 2x1 changes economics. |
| Pmin/Pmax by mode | Dispatch feasibility. |
| Heat rate by mode | Fuel cost and offers. |
| Compressor fouling by GT | Unit-level performance. |
| HRSG cycle count by train | Steam-side damage. |
| ST/cooling condition | Net capacity and heat rate. |
| Outage status by component | Full vs partial availability. |
| Inspection headroom | Dispatch penalty and maintenance timing. |

## Athens Worked Example

Athens is the current first CCGT case:

| Item | Athens assumption |
| :--- | :--- |
| Configuration | 2 GTs, 2 HRSGs, 1 ST |
| GT model | GE 7FA.03 x 2 |
| ISO net capacity | 531 MW |
| Baseline heat rate | 7,070 Btu/kWh |
| Starting EOH | 24,000 per GT |
| Next CI | 32,000 EOH |
| Start state | Just after HGP |

Use [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md) for detailed values.

## What The Framework Includes

| Included item | Why it helps |
| :--- | :--- |
| Athens CCGT pilot | Gives concrete values for learning. |
| 1x1 hot-start example | Shows partial-operation economics matter. |
| HRSG/ST start cost split | Captures steam-side cycling cost. |
| HRSG drum fatigue tracker | Adds CCGT-specific degradation beyond GT. |
| State feedback loop | Lets CCGT condition affect future dispatch. |

## What The Framework Leaves Out

| Missing detail | Why it matters |
| :--- | :--- |
| Full 1x1 and 2x1 Pmin/Pmax curves | Needed for Step 2 dispatch and offers. |
| Mode-specific heat-rate curves | Needed for marginal cost by mode. |
| Detailed ramp and min up/down constraints | Needed for realistic unit commitment. |
| Actual plant configuration details | Duct firing, bypass stack, cooling limits, and controls matter. |
| Per-train outage logic | Determines partial availability. |
| Actual CSA/LTSA terms | Contract values are assumptions until reviewed. |

## Source Basis And Certainty

| Source | Use in this guide | Certainty |
| :--- | :--- | :--- |
| [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md) | Equipment and acronym foundation. | Green for learning structure. |
| [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md) | First concrete CCGT values. | Green as local example; Amber for investment use. |
| [Operating Range: Pmin And Pmax](../market_and_operations/01_operating_range_pmin_pmax.md) | Mode-specific operating range warning. | Green for concept. |
| [Marginal Cost And Offer Curves](../market_and_operations/02_marginal_cost_and_offer_curves.md) | Mode-specific offer and marginal-cost logic. | Green for concept. |
| `docs/InfraSure_ModelingFramework_V2.md` | Athens framework assumptions and degradation stack. | Green for framework intent; Amber for asset-specific values. |

## Open Questions Before Modeling A CCGT

| Question | Why it matters |
| :--- | :--- |
| What operating modes are physically allowed? | 1x1, 2x1, duct firing, bypass, and derates need clear treatment. |
| What are Pmin/Pmax curves by mode and temperature? | Dispatch feasibility depends on them. |
| What are heat-rate curves by mode? | Marginal cost changes by mode and load. |
| How are start costs allocated by train? | Prevents double-counting in 2x1 operation. |
| Can the plant run GT-only if ST or HRSG is unavailable? | Determines partial outage economics. |
| Are HRSG and ST covered by contract or owner O&M? | Drives cost and risk allocation. |
| Are GT-A and GT-B histories symmetric? | EOH and degradation may differ. |

## Quick Recap

```text
CCGT = GT output + recovered steam-cycle output
```

That improves efficiency but adds HRSG/ST costs, steam-side damage, mode-specific operating ranges, and more complex outage logic.
