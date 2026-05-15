# Plant Types Index

## Purpose

This folder separates plant-type knowledge from the universal basics guides.

The basics guides teach ideas such as capacity, heat rate, starts, EOH, outages, and state feedback. Those ideas are broad. But the details change when the asset is a simple-cycle GT, combined-cycle GT, aeroderivative unit, frame unit, CHP plant, or possible future gas reciprocating engine.

Use this folder for that second layer:

```text
universal basics
        |
        v
plant-type-specific equipment and constraints
        |
        v
worked example assumptions
```

Start here first:

- [Gas Plant Type Map](../basics/00_gas_plant_type_map.md)
- [Athens 7FA 2x1 CCGT Worked Example](../examples/athens_7fa_2x1_ccgt.md)

## Why This Folder Exists

The first worked example in the learning docs is Athens, a GE 7FA 2x1 CCGT. That is useful, but it can create a hidden assumption:

```text
gas plant = combined-cycle plant = GT + HRSG + ST
```

That is not always true.

| Plant type | Equipment reality | Modeling consequence |
| :--- | :--- | :--- |
| Simple-cycle GT | GT and generator, no HRSG/ST. | No HRSG/ST start cost or HRSG cycling damage. |
| Combined-cycle GT | GTs, HRSGs, ST, cooling, BOP. | GT and steam-side constraints both matter. |
| Frame GT | Large industrial turbine technology. | Start/cooldown, inspection, and outage scope can be heavy. |
| Aeroderivative GT | Smaller/faster turbine technology. | Fast start and module maintenance can change economics. |
| CHP / cogeneration | Electricity plus useful steam/heat. | Steam-host obligation can dominate dispatch. |
| Gas reciprocating engine | Piston engine generator, not a GT. | GT hot-section degradation guides do not directly apply. |

## Planned Guide Set

These are planned guides. They should be written only when needed, using the same beginner-first style as the basics docs.

| Order | Planned file | Main question answered | Status |
| :--- | :--- | :--- | :--- |
| 0 | `00_plant_types_index.md` | How should plant-type guides be organized? | Current file. |
| 1 | `01_simple_cycle_gt.md` | What changes when the plant has no HRSG/ST? | Implemented. |
| 2 | `02_combined_cycle_gt.md` | What makes CCGT modeling different from simple-cycle? | Implemented. |
| 3 | `03_frame_vs_aeroderivative_gt.md` | How does turbine technology change starts, ramps, maintenance, and degradation? | Planned. |
| 4 | `04_chp_and_cogeneration.md` | How do steam/heat obligations change dispatch and economics? | Planned. |
| 5 | `05_optional_reciprocating_engines.md` | Should gas engines be included in this learning system? | Optional scope decision. |

## What Each Plant-Type Guide Should Cover

Each plant-type guide should answer the same core questions:

| Section | What it should explain |
| :--- | :--- |
| Equipment map | What equipment exists and what does not exist. |
| Dispatch role | Peaking, reserves, mid-merit, baseload, CHP, or other role. |
| Capacity behavior | Pmax, Pmin, weather sensitivity, and derates. |
| Heat-rate behavior | Average and incremental heat rate, part-load shape, and correction basis. |
| Start behavior | Start time, start cost, EOH rules, and hot/warm/cold caveats. |
| Degradation applicability | Which degradation guides apply, partly apply, or do not apply. |
| Outage categories | Which outage modes are relevant for this plant type. |
| State variables | What the daily loop must remember. |
| Open questions | What must be verified before investor use. |

## Applicability Matrix

| Topic | Simple-cycle GT | CCGT | Frame GT | Aeroderivative GT | CHP |
| :--- | :---: | :---: | :---: | :---: | :---: |
| GT compressor degradation | Yes | Yes | Yes | Yes | If GT-based |
| Combustion cycling fatigue | Yes | Yes | Yes | Yes | If GT-based |
| TBC life | If coated GT hot parts | If coated GT hot parts | Usually relevant | Machine-specific | If GT-based |
| GT rotor life | Yes | Yes | Yes | Module-specific | If GT-based |
| HRSG cycling damage | No | Yes | If in CCGT | If in CCGT | Maybe |
| ST warming cost | No | Yes | If in CCGT | If in CCGT | Maybe |
| Steam-host constraint | No | Usually no | Usually no | Usually no | Yes |
| Gas-engine overhaul logic | No | No | No | No | Only if gas engines included |

## Standard Warning For Future Guides

Use this warning when a guide uses values from a specific asset:

```text
> Plant-Type Note
> These values are worked-example assumptions for one plant type.
> Use OEM data, contract terms, site data, and operating history before
> applying them to another asset.
```

## How To Use This Folder

For the current learning path:

```text
Gas Plant Type Map
  |
  v
Combined-Cycle Plant Anatomy
  |
  v
Athens 7FA 2x1 CCGT Worked Example
  |
  v
Basics + degradation guides
```

For a future non-CCGT plant:

```text
Gas Plant Type Map
  |
  v
plant-type guide
  |
  v
universal basics guide
  |
  v
only the degradation guides that apply
```

Current implemented plant-type guide:

- [Simple-Cycle Gas Turbine](./01_simple_cycle_gt.md)
- [Combined-Cycle Gas Turbine](./02_combined_cycle_gt.md)

## Open Questions

| Question | Why it matters |
| :--- | :--- |
| Should the next worked example be simple-cycle, aero peaker, or CHP? | It decides which plant-type guide should be written first. |
| Does this repo need gas reciprocating engines? | If yes, several GT-specific degradation guides need stronger boundaries. |
| Should the CCGT anatomy guide eventually merge with this folder? | The plant-type guide now exists, but keeping the anatomy path avoids link churn while learners still use it. |
| Which plant types are in the investment pipeline? | Documentation effort should follow real modeling needs. |
