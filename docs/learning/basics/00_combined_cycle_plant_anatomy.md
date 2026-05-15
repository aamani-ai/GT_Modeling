# Combined-Cycle Plant Anatomy

Start here for the broader plant-type map: [Gas Plant Type Map](./00_gas_plant_type_map.md).

> Plant-Type Note
> This guide is specifically about combined-cycle gas turbine plants. It is not the universal anatomy guide for every gas plant. Simple-cycle GTs, aeroderivative peakers, CHP plants, and possible future reciprocating-engine assets have different equipment, constraints, cost buckets, and degradation applicability.

## Why This Matters

This guide answers a basic question:

> What are GT, ST, HRSG, BOP, and the other plant terms used in the model?

The earlier basics guides explain model variables like capacity, heat rate, EOH, start cost, dispatch, outages, and state vector. But those variables sit on top of a physical power plant. If the plant equipment is unfamiliar, the model can feel abstract too quickly.

This guide is the physical map. Read it before the other basics guides if terms like GT, ST, HRSG, BOP, HGP, CI, MI, LTSA, or OEM are new.

## The Plant In One Picture

A combined-cycle plant makes electricity in two linked cycles:

1. The gas turbine burns fuel and makes electricity directly.
2. The hot exhaust from the gas turbine makes steam in the HRSG.
3. The steam turbine uses that steam to make additional electricity.

```text
Natural gas + air
      |
      v
   +------+
   |  GT  |------ electricity
   +------+
      |
      | hot exhaust
      v
   +------+
   | HRSG |------ steam ------+
   +------+                   |
      |                       v
      |                    +------+
      |                    |  ST  |------ electricity
      |                    +------+
      |                       |
      v                       v
 emissions stack          condenser / cooling system
```

This is why it is called "combined cycle": it combines a gas-turbine cycle with a steam cycle.

## Main Equipment Terms

| Term | Full name | Plain-English meaning |
| :--- | :--- | :--- |
| GT | Gas turbine | Burns gas with compressed air and directly drives a generator. |
| ST | Steam turbine | Uses steam from recovered exhaust heat to make more electricity. |
| HRSG | Heat recovery steam generator | Captures hot GT exhaust and turns water into steam. |
| Generator | Electric generator | Converts rotating shaft energy into electricity. |
| BOP | Balance of plant | Supporting systems around the main GT/ST/HRSG equipment. |
| Stack | Exhaust stack | Where cleaned exhaust gas exits the plant. |
| Cooling tower | Heat rejection equipment | Helps condense steam back into water for reuse. |
| Condenser | Steam-cycle heat exchanger | Turns exhaust steam from the ST back into water. |
| Transformer | Electrical equipment | Steps voltage up for grid interconnection. |
| DCS | Distributed control system | Plant control system. |

In the InfraSure framework, the pilot plant is a 2x1 combined cycle:

```text
2 GT + 2 HRSG + 1 ST
```

That means two gas turbines feed two HRSGs, and the steam system supports one steam turbine.

## Gas Turbine: GT

The gas turbine is the front end of the combined-cycle plant.

Basic GT flow:

```text
Air -> compressor -> combustor -> turbine -> exhaust
                         ^
                         |
                    natural gas
```

| GT part | What it does | Why the model cares |
| :--- | :--- | :--- |
| Compressor | Squeezes inlet air before combustion. | Fouling and erosion hurt heat rate and capacity. |
| Combustor | Mixes fuel and air and burns the mixture. | Starts, trips, and cycling create fatigue risk. |
| Turbine section | Expands hot gas through blades and vanes. | Hot gas path parts see creep, fatigue, and TBC wear. |
| Generator | Produces electricity from shaft rotation. | Generator issues may be outside LTSA scope. |
| Exhaust | Hot gas leaving the GT. | Feeds the HRSG to make steam. |

GT is where many degradation guides begin because it sees very high temperature, high speed, and frequent thermal cycling.

## Heat Recovery Steam Generator: HRSG

The HRSG sits downstream of the gas turbine exhaust. It is not "behind" the GT in an accounting sense; it is physically downstream in the exhaust path.

The HRSG captures heat that would otherwise leave through the stack.

```text
GT hot exhaust -> HRSG tubes -> water becomes steam -> ST
```

| HRSG part / concept | Plain meaning | Why the model cares |
| :--- | :--- | :--- |
| HP drum | High-pressure steam drum. | Thermal cycling can create fatigue. |
| Headers | Large pipes distributing steam/water. | Can experience thermal stress and cracking. |
| Attemperator | Controls steam temperature using spray water. | Cycling can increase wear and failure risk. |
| Duct burner | Optional extra firing in HRSG duct. | Can increase steam production; not central in current framework. |
| Stack | Exhaust exit after heat recovery and emissions control. | End of gas path. |

HRSG damage matters because a combined-cycle start is not only a GT event. Starting also heats and pressurizes steam-side equipment.

## Steam Turbine: ST

The steam turbine uses steam from the HRSG to make additional electricity.

```text
HRSG steam -> ST -> generator -> electricity
```

The ST is why combined-cycle plants are more efficient than simple-cycle gas turbines. The plant gets extra electricity from heat that would otherwise be wasted.

| ST-related item | Plain meaning | Why the model cares |
| :--- | :--- | :--- |
| Steam turbine rotor | Rotating steam-turbine shaft/blades. | Thermal stress can matter during starts. |
| Condenser | Cools exhaust steam back to water. | Cooling performance affects plant output. |
| Cooling tower | Rejects heat to atmosphere. | Hot weather can reduce steam-cycle performance. |
| Steam seals / valves | Steam control hardware. | Maintenance may be owner-funded if outside CSA scope. |

In the framework, some ST-related costs are excluded from the GT-focused CSA and reserved in owner O&M.

## Balance Of Plant: BOP

BOP means the supporting plant systems that make the main equipment usable.

Examples:

| BOP system | What it supports |
| :--- | :--- |
| Gas supply and metering | Delivers fuel to the GT. |
| Water treatment | Provides clean water/steam-cycle chemistry. |
| Cooling tower / circulating water | Rejects heat from the steam cycle. |
| Electrical switchyard and transformers | Connects the plant to the grid. |
| Plant controls / DCS | Operates and monitors equipment. |
| Instrument air | Supports valves and controls. |
| Fire protection | Safety system. |
| Emissions monitoring | Compliance and reporting. |

BOP matters because not every outage is a GT outage. Controls, electrical systems, cooling systems, and other support systems can force the plant offline even if the GT itself is healthy.

## Emissions Equipment

The framework mentions DLN 2.6 combustion, SCR, and CO catalyst.

| Term | Full name | Plain-English meaning |
| :--- | :--- | :--- |
| DLN | Dry low NOx combustor | GT combustion system designed to reduce NOx without water/steam injection. |
| SCR | Selective catalytic reduction | Uses catalyst and reagent to reduce NOx emissions. |
| CO catalyst | Carbon monoxide catalyst | Reduces CO emissions in the exhaust path. |
| CEMS | Continuous emissions monitoring system | Measures emissions for compliance. |

These systems can matter for dispatch because emissions limits, catalyst condition, or controls problems may restrict operation or create maintenance costs.

## Configuration Language: 1x1 And 2x1

Combined-cycle plants are often described by how many gas turbines and steam turbines are in a power block.

| Configuration | Meaning |
| :--- | :--- |
| 1x1 | One GT, one HRSG, one ST. |
| 2x1 | Two GTs, two HRSGs, one ST. |
| 3x1 | Three GTs, three HRSGs, one ST. |

The Athens-type pilot is 2x1:

```text
GT-A -> HRSG-A --+
                 +--> common steam system -> ST
GT-B -> HRSG-B --+
```

The framework also allows 1x1 operation, meaning one GT can run with partial steam-cycle operation instead of both GTs running.

Why this matters:

| Modeling topic | Why configuration matters |
| :--- | :--- |
| Capacity | One GT online produces less than two GTs online. |
| Heat rate | 1x1 and part-load operation can have different efficiency. |
| Start cost | Starting one GT is cheaper than starting both. |
| EOH | GT-A and GT-B may accumulate EOH differently. |
| HRSG cycling | Each HRSG can see different thermal cycles. |
| Outages | One train might be unavailable while another can still run. |

## Inspection And Contract Acronyms

The model uses many service-contract terms.

| Term | Full name | Plain-English meaning |
| :--- | :--- | :--- |
| OEM | Original equipment manufacturer | Company that made/services the equipment, e.g. GE. |
| LTSA | Long-term service agreement | Long-term maintenance/service contract. |
| CSA | Contractual service agreement | GE-style service contract term used similarly here. |
| CI | Combustion inspection | Inspection focused on combustor hardware. |
| HGP | Hot gas path inspection | Inspection of turbine hot-section parts. |
| MI | Major inspection | Larger overhaul including more GT components. |
| EOH | Equivalent operating hours | Contractual life-consumption counter. |
| VOM | Variable O&M | Variable operating and maintenance cost per MWh. |
| FOR | Forced outage rate | Unplanned outage rate concept. |

The inspection sequence in the framework starts after HGP:

```text
24,000 EOH: HGP just completed
32,000 EOH: next CI
40,000 EOH: next CI
48,000 EOH: MI
```

## Units And Market Acronyms

These units appear throughout the learning docs.

| Term | Meaning | Example |
| :--- | :--- | :--- |
| MW | Megawatt, instantaneous power | Plant can produce 531 MW at ISO. |
| MWh | Megawatt-hour, energy over time | 500 MW for 8 hours = 4,000 MWh. |
| Btu | British thermal unit, heat energy | Used in heat rate. |
| MMBtu | One million Btu | Gas price often quoted in $/MMBtu. |
| Btu/kWh | Heat rate unit | 7,070 Btu/kWh. |
| HHV | Higher heating value | Fuel-energy basis used in framework heat rate. |
| LHV | Lower heating value | Another fuel-energy basis; do not mix with HHV. |
| ISO | Standard reference condition | Usually around 59 deg F for performance reference. |
| NYISO | New York Independent System Operator | Power market operator for New York. |
| TGP Zone 6 | Tennessee Gas Pipeline Zone 6 | Gas price/location reference in framework. |

The key beginner warning:

```text
Always keep units consistent.
HHV vs LHV and gross vs net can change heat-rate comparisons.
```

## How Anatomy Connects To Model Variables

The physical plant explains why the model tracks different variables.

| Equipment / system | Model variable it affects |
| :--- | :--- |
| GT compressor | Capacity, heat rate, compressor fouling, erosion. |
| GT combustor | Start cost, combustion fatigue, trip risk. |
| GT turbine hot section | Creep, fatigue, TBC life, HGP inspection timing. |
| HRSG | HRSG cycling damage, start cost, forced outage risk. |
| ST and condenser | Net plant capacity, heat rate, owner O&M exclusions. |
| Cooling tower | Hot-weather performance and BOP outage risk. |
| Controls / DCS | Background forced outage risk. |
| Generator / transformer | Electrical forced outage and owner-funded exclusions. |
| LTSA/CSA | Inspection timing, covered vs uncovered cost, guarantees. |

This is why the model cannot only look at market prices. Physical equipment condition changes dispatch economics and cashflow risk.

## Simple Example: One Hot Start In A 2x1 Plant

Suppose the plant starts both GTs after a short shutdown.

Physical sequence:

```text
1. GT-A and GT-B start.
2. Each GT burns gas and makes electricity.
3. Each GT sends hot exhaust into its HRSG.
4. HRSG-A and HRSG-B make steam.
5. Steam goes to the common ST.
6. ST makes additional electricity.
```

Model consequences:

| Consequence | Why it happens |
| :--- | :--- |
| Hot start cost | GT fuel, GT wear, auxiliaries, HRSG/ST thermal stress. |
| EOH added | Contract assigns EOH to the starts and fired hours. |
| HRSG cycle count increases | Steam-side equipment heats up. |
| Heat rate changes during startup and load | Part-load and startup operation are less efficient. |
| State vector updates | Tomorrow's plant condition changes. |

## What The Framework Includes

The framework gives enough plant identity to build the learning docs:

- Athens-type, Selkirk NY reference plant.
- 2x1 combined-cycle configuration.
- GE 7FA.03 gas turbines.
- Mechanical draft cooling towers.
- Tennessee Gas Pipeline gas interconnect.
- DLN 2.6 combustion, SCR, and CO catalyst.
- GT, HRSG, ST, BOP, and contract coverage concepts.
- 1x1 operation is permitted at about 55% plant capacity.

## What The Framework Leaves Out

The framework is not a plant design manual.

| Missing detail | Why it matters |
| :--- | :--- |
| Full process flow diagram | Would show actual equipment arrangement and valves. |
| Single-shaft vs multi-shaft layout | Affects operation and start sequencing. |
| Actual HRSG pressure levels | Needed for detailed HRSG thermal modeling. |
| Duct burner status | Could affect capacity, heat rate, and emissions. |
| Detailed emissions permit limits | Could constrain dispatch. |
| Electrical one-line diagram | Needed for generator/transformer/switchyard risk. |
| Cooling system performance curve | Needed for detailed summer derate modeling. |
| Unit-level operating history | Needed to know GT-A vs GT-B condition. |

For the current learning path, the goal is not to replace those details. The goal is to make the model vocabulary readable.

## Source Basis And Certainty

| Source | What it supports | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4.1 | Athens-type plant identity and configuration. | Green for local framework context. |
| `docs/InfraSure_ModelingFramework_V2.md`, Sections 4.3-4.6 | 1x1 operation, start costs, HRSG/ST split, VOM. | Amber until asset-specific validation. |
| `docs/InfraSure_GT_DigitalTwin_v2.pdf` | Five-step pipeline and equipment-to-damage framing. | Green for communication. |
| EIA combined-cycle overview | Combined-cycle plants use combustion turbines, HRSGs, and steam turbines to improve efficiency. | Green for general concept. |
| EIA combined-cycle glossary | Combined-cycle definition and HRSG/steam-turbine relationship. | Green for general vocabulary. |

## Open Questions Before Investment Use

Before using plant-anatomy assumptions in investment materials, resolve these:

| Question | Why it matters |
| :--- | :--- |
| Is the plant single-shaft or multi-shaft? | Affects operational flexibility and start sequencing. |
| Is duct firing present and modeled? | Can change capacity, heat rate, emissions, and HRSG stress. |
| Are GT-A and GT-B operated symmetrically? | Affects unit-level EOH and degradation. |
| What HRSG pressure levels and design details are present? | Needed for deeper HRSG cycling analysis. |
| What systems are inside vs outside the LTSA? | Determines owner risk. |
| Are emissions constraints binding in dispatch? | Could restrict high-price operation. |
| What BOP systems have historical reliability issues? | Helps calibrate background outage risk. |

## Quick Recap

A combined-cycle plant uses a gas turbine and a steam turbine together. The GT makes electricity directly. The HRSG captures GT exhaust heat and makes steam. The ST uses that steam to make more electricity. BOP systems support the whole plant.

For this learning path:

```text
GT explains capacity, heat rate, EOH, hot gas path damage, and starts.
HRSG explains steam-side cycling and combined-cycle start costs.
ST explains extra power from recovered heat.
BOP explains non-GT outage and owner-cost risk.
LTSA explains how maintenance and coverage become cashflow.
```

This is the physical foundation for the rest of the basics guides.
