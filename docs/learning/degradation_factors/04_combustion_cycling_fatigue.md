# Combustion Cycling Fatigue

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read these first if starts and EOH are new:

- [EOH And Starts](../basics/03_eoh_and_starts.md)
- [EOH Accumulation With Creep-Fatigue Coupling](./01_eoh_creep_fatigue_coupling.md)

> Plant-Type Applicability
> This is a GT combustor topic. It can apply to simple-cycle GTs, CCGTs, and GT-based CHP plants, but combustor hardware, emissions tuning, fuel system, start sequence, and fatigue weights differ by OEM and machine. It is not an HRSG, ST, generator, or gas reciprocating engine fatigue model.

## First-Time Reader Map

If this topic is new, start with the equipment question:

```text
The combustor is where fuel burns.
Every start, stop, trip, and large ramp changes heat and pressure.
Repeated changes can crack or distress combustion hardware.
That is combustion cycling fatigue.
```

The guide uses several terms that should be clear before the damage-index math:

| Term | First-time meaning |
| :--- | :--- |
| Combustor | GT section where fuel and compressed air burn. |
| Combustion liner | Metal shell that contains and shapes the flame region. |
| Transition piece | Hot-gas duct from combustor outlet to turbine inlet. |
| Fuel nozzle | Hardware that meters and mixes fuel into the air stream. |
| Crossfire tube | Hardware that helps ignition spread between combustor cans in some designs. |
| Flow sleeve | Combustor flow and cooling hardware around the liner. |
| Cycling | Repeated starts, stops, ramps, trips, and load swings. |
| LCF | Low-cycle fatigue, damage from fewer but more severe cycles. |
| HCF | High-cycle fatigue, often vibration-driven damage from many small cycles. |
| Fatigue index | Simplified damage points used by the framework. |
| CI | Combustion Inspection, the planned inspection tier focused on combustion hardware. |
| `P_combustion` | Combustion-related contribution to GT forced outage probability. |

The mental stack is:

```text
combustor hardware -> thermal cycles -> fatigue index -> outage risk + CI pressure
```

## Combustion System Before The Math

The combustor sits between the compressor and turbine.

```text
Air -> compressor -> combustor -> turbine -> exhaust
                         ^
                         |
                    fuel burns here
```

The combustor has to handle flame, heat release, pressure, cooling air, emissions tuning, and hot-gas delivery to the turbine. During a start or ramp, those conditions change quickly.

Simple physical story:

```text
start the GT
  |
  v
flame lights and hardware heats
  |
  v
metal expands, temperatures shift, pressures change
  |
  v
shutdown or ramp reverses part of that movement
  |
  v
repeat many times and small cracks can grow
```

The model does not inspect actual cracks every day. It uses dispatch events as a proxy for cycling stress.

## Why This Is Not Just EOH

The same start can create several model signals.

```text
one cold start
  |
  +--> adds contractual EOH
  |
  +--> adds start cost
  |
  +--> adds combustion fatigue index
  |
  +--> may move the unit closer to CI or outage risk
```

Contractual EOH and combustion fatigue are related, but they are not the same:

| Counter | What it counts | Main use |
| :--- | :--- | :--- |
| Contractual EOH | Contract-defined maintenance life. | LTSA billing and inspection timing. |
| Combustion fatigue index | Relative combustion cycling severity. | Physical stress state and forced outage risk. |

That is why this guide has its own damage-index table instead of only reusing the EOH table.

## What A Fatigue Index Is

A fatigue index is a simplified scoring system.

```text
small event  -> low points
severe event -> high points
many events  -> points add up
```

The index is not a direct crack length, invoice amount, or OEM-certified life value. It is a model signal that helps compare operating patterns.

Example:

```text
One hot start may be a small cycling signal.
One cold start is larger.
One emergency trip is larger again.
Many large load swings can add up over time.
```

For investment analysis, the value is not perfect precision. The value is that Mode A, B, and C dispatch can be compared with a consistent cycling-stress measure.

## Plant-Type Applicability

The combustor exists wherever a gas turbine burns fuel, but the fatigue model should still be plant-specific.

| Plant type | What still applies | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Starts, trips, and load swings create combustor cycling. | No HRSG/ST cost layer; dispatch may cycle more often. |
| Combined-cycle GT | Combustor fatigue still applies to each GT. | 1x1 vs 2x1 dispatch can make GT-A and GT-B fatigue histories diverge. |
| Aeroderivative GT | Combustor cycling still matters. | Hardware design and maintenance model may differ from large-frame assumptions. |
| CHP / cogeneration | GT combustor fatigue still applies if a GT is used. | Steam obligations can force runs or starts that pure power dispatch would avoid. |
| Gas reciprocating engine | Not directly applicable. | Engine cylinders, ignition, and overhaul logic need a different guide. |

## Why This Matters

Combustion cycling fatigue answers a specific damage question:

> How much stress did starts, trips, ramps, and load swings put on the combustion hardware?

This guide is narrower than the first creep-fatigue guide. The first guide explains the whole hot-section life accounting problem. This guide focuses on the combustion system, especially liners and transition pieces.

The framework treats combustion cycling fatigue as a high-priority stress factor because it can lead to:

| Impact | Plain-English meaning |
| :--- | :--- |
| Unplanned forced outage | Combustion hardware fails or creates a condition that requires taking the GT offline. |
| Accelerated CI schedule | More cycling can pull combustion inspection needs closer. |
| Uncovered repair cost | Some repairs or overage conditions may fall partly outside expected LTSA coverage. |
| Higher start/wear economics | Step 2 dispatch should recognize that cycling is not free. |

Simple flow:

```text
starts + trips + large load swings
        |
        v
thermal and pressure cycling in combustor
        |
        v
fatigue damage in liners and transition pieces
        |
        v
higher combustion failure risk
        |
        v
forced outage and repair cost exposure
```

The financial point is not only the cost of a future combustion inspection. The bigger risk is that the plant is unavailable during high-value hours because a cycling-related fault appears between planned inspections.

## Plain-English Concept

Combustion cycling fatigue is damage from repeated thermal and mechanical changes in the GT combustion system.

Beginner version:

```text
Start the GT       -> metal heats and expands.
Stop the GT        -> metal cools and contracts.
Ramp the GT        -> temperatures and pressures shift.
Trip the GT        -> severe fast transient.
Repeat many times  -> small cracks can grow.
```

The important word is "cycling." A combustion system can survive high temperature when it is designed for that condition, but repeated changes in temperature, pressure, and flame behavior can create fatigue damage.

## Where This Happens In The Plant

The framework points to low-cycle fatigue on liners and transition pieces.

| Component | What it does | Why cycling matters |
| :--- | :--- | :--- |
| Combustion liner | Contains and shapes the flame region. | Repeated heat-up, cool-down, pressure pulsation, and local hot spots can drive cracking. |
| Transition piece | Carries hot gas from combustor to turbine inlet. | Thermal gradients and vibration can create fatigue damage. |
| Fuel nozzles | Deliver and mix fuel. | Uneven fuel distribution can create hot streaks and dynamics. |
| Crossfire tubes / flow sleeves | Support ignition, cooling, and combustor flow management. | Hardware sees cyclic thermal and flow stress. |
| Thermal barrier coating near combustor | Protects metal from hot gas. | Cycling and dynamics can contribute to spallation or cracking. |

The Athens-type LTSA scope says a CI covers combustion liners, transition pieces, fuel nozzles, crossfire tubes, flow sleeves, and included labor. That is why combustion cycling fatigue connects directly to CI timing and cost.

## Low-Cycle Fatigue In Plain Language

Low-cycle fatigue, or LCF, means damage from a smaller number of relatively severe cycles.

It is different from vibration fatigue:

| Fatigue type | Cycle count | Cycle severity | Beginner example |
| :--- | :--- | :--- | :--- |
| Low-cycle fatigue | Lower number of cycles | Higher strain/thermal change | Starts, trips, cold restarts. |
| High-cycle fatigue | Very high number of cycles | Lower strain, often vibration-driven | Combustion dynamics or mechanical vibration. |

The framework's combustion cycling fatigue guide is mainly about LCF from dispatch behavior. Combustion dynamics monitoring is related, but it is a more detailed sensor-driven fault detection topic than the current model implements.

## What Drives The Fatigue Index

The framework uses a simplified damage index per event type.

| Event | Framework damage index | Why it is more or less severe |
| :--- | ---: | :--- |
| Hot start | 1.0 | Reference event; equipment is still warm, so temperature change is lower. |
| Warm start | 2.5 | More cooling has occurred, so restart thermal stress is higher. |
| Cold start | 4.0 | Largest normal heat-up from a cold state. |
| Emergency trip | 5.0 | Severe fast transient from load, treated as highest event severity. |
| Load swing greater than 40% rated | 0.3 | Partial cycle from a large intra-day load change. |

This is not the same as contractual EOH.

| Counter | Unit | Main purpose |
| :--- | :--- | :--- |
| Contractual EOH | Equivalent operating hours | LTSA billing and inspection thresholds. |
| Combustion fatigue index | Relative damage points | Physical stress tracking for combustion hardware. |
| Forced outage probability | Daily probability | Risk that the stress state causes an outage event. |

The same start can affect all three, but they are not interchangeable.

## Simple Formula

For learning, the daily combustion fatigue index can be written as:

```text
daily_combustion_fatigue =
  1.0 * hot_starts
  + 2.5 * warm_starts
  + 4.0 * cold_starts
  + 5.0 * trips
  + 0.3 * large_load_swings
```

Where `large_load_swings` means load swings greater than 40% of rated output.

Important uncertainty:

```text
Hot/warm/cold/trip severity factors: framework confidence is Green to Amber.
Load swing 0.3 credit: framework confidence is Red.
```

The load-swing credit should be sensitivity-tested before investment use.

## Damage Severity Ladder

```text
Relative combustion fatigue severity

Hot start       |##########                              | 1.0
Warm start      |#########################               | 2.5
Cold start      |########################################| 4.0
Emergency trip  |##################################################| 5.0
Load swing      |###                                     | 0.3
```

The bars are illustrative. They show relative weighting, not measured crack growth.

## Daily Model Inputs

Combustion cycling fatigue uses dispatch outputs and a few state variables.

| Input | Frequency | Source | Why it matters |
| :--- | :--- | :--- | :--- |
| Hot starts | Daily event count | Step 2 dispatch summary | Reference start damage. |
| Warm starts | Daily event count | Step 2 dispatch summary | Higher restart thermal stress. |
| Cold starts | Daily event count | Step 2 dispatch summary | Highest normal restart thermal stress. |
| Emergency trips | Event count | Operations / failure module | Severe transient and high fatigue event. |
| Hourly load profile | Hourly | Step 2 dispatch | Used to detect large load swings and ramp cycles. |
| Load swing magnitude | Hourly summary | Step 2 dispatch | Determines whether a swing exceeds the 40% threshold. |
| Ramp frequency | Hourly summary | Step 2 dispatch | More repeated ramps can increase cycling exposure. |
| Current fatigue index | Daily state | Engineering model | Carries accumulated combustion damage forward. |
| Current creep state | Daily state | Engineering model | Combustion fatigue is evaluated with creep interaction, not alone. |
| Inspection state | Event state | Maintenance module | CI/HGP/MI may reset or reduce relevant damage. |

Possible future inputs that the current high-level framework does not fully use:

| Future input | Why it would improve the model |
| :--- | :--- |
| Combustion dynamics data | Detects pressure oscillation and vibration risk. |
| Exhaust temperature spread | Can indicate combustor imbalance or hot streaks. |
| Start ramp profile | Differentiates gentle and aggressive starts. |
| Fuel nozzles / tuning history | Combustion tuning affects dynamics, emissions, and local temperatures. |
| Borescope findings | Direct evidence of cracks, coating loss, or distress. |

## Daily Update Logic

The daily loop is easiest to understand in order.

| Step | Update | Plain-English purpose |
| :--- | :--- | :--- |
| 1 | Read opening state. | Start with current fatigue index, EOH, outage status, and inspection headroom. |
| 2 | Check forced outage risk from opening state. | If already high risk, the unit may be unavailable before today's dispatch executes. |
| 3 | Run Step 2 dispatch if available. | Determine today's starts, hours, load, and ramps. |
| 4 | Classify starts. | Convert shutdown duration into hot, warm, or cold starts. |
| 5 | Count trips and large load swings. | Capture severe transients and partial cycles. |
| 6 | Calculate daily fatigue index. | Apply the framework severity weights. |
| 7 | Add the daily index to cumulative state. | Carry physical cycling stress forward. |
| 8 | Evaluate with creep interaction. | Do not treat fatigue as a standalone pass/fail counter. |
| 9 | Update `P_combustion`. | Raise GT forced outage risk as the fatigue budget is consumed. |
| 10 | Carry state into tomorrow. | Tomorrow's dispatch sees updated risk and economics. |

ASCII version:

```text
hourly dispatch profile
        |
        v
starts + trips + load swings
        |
        v
daily combustion fatigue index
        |
        v
cumulative fatigue state
        |
        +--> coupled with creep state
        |
        v
P_combustion for future forced outage risk
```

## How It Feeds Step 2 Dispatch

Combustion cycling fatigue affects Step 2 dispatch indirectly.

Step 2 does not usually say:

```text
Do not run because fatigue index increased by 1.0.
```

Instead, the fatigue index changes the plant state that dispatch receives:

| Feedback path | How dispatch feels it |
| :--- | :--- |
| Higher forced outage risk | More chance the unit is unavailable before a run day. |
| Higher start/wear economics | More reason to avoid marginal starts if the mode penalizes cycling. |
| Less headroom to CI/HGP | More reason to self-curtail near maintenance thresholds. |
| More uncovered repair exposure | Financial layer sees higher tail risk. |

The daily feedback loop:

```text
yesterday's combustion fatigue state
        |
        v
forced outage check
        |
        v
today's Step 2 dispatch
        |
        v
starts, trips, ramps, load swings
        |
        v
updated combustion fatigue state
        |
        v
tomorrow's risk and dispatch economics
```

This is another example of why the analysis can look daily while still being built from hourly dispatch behavior.

## Worked Example 1: One Cycling Day

Assume one GT has:

| Event | Count |
| :--- | ---: |
| Hot starts | 1 |
| Warm starts | 0 |
| Cold starts | 0 |
| Emergency trips | 0 |
| Large load swings | 2 |

Daily fatigue index:

```text
daily index = (1 * 1.0) + (2 * 0.3)
daily index = 1.0 + 0.6
daily index = 1.6
```

This is a mild cycling day: one hot start plus two partial cycles.

## Worked Example 2: Cold Start And Trip Day

Assume:

| Event | Count |
| :--- | ---: |
| Hot starts | 0 |
| Warm starts | 0 |
| Cold starts | 1 |
| Emergency trips | 1 |
| Large load swings | 1 |

Daily fatigue index:

```text
daily index = (1 * 4.0) + (1 * 5.0) + (1 * 0.3)
daily index = 4.0 + 5.0 + 0.3
daily index = 9.3
```

This day consumes far more combustion fatigue budget than the hot-start example, even if fired hours are similar.

## Worked Example 3: Same Contractual EOH, Different Fatigue Shape

Two days can have similar EOH but different fatigue patterns.

| Day | Fired hours | Events | Contractual EOH idea | Combustion fatigue idea |
| :--- | ---: | :--- | :--- | :--- |
| A | Many hours, no starts | Mostly fired-hour EOH | More creep/time exposure | Low combustion cycling fatigue |
| B | Few hours, cold start and trip | Event-driven EOH | Less fired-hour exposure | High combustion cycling fatigue |

This is why the framework separates:

```text
contractual EOH counter
combustion fatigue index
creep-fatigue interaction state
```

The same daily dispatch summary feeds all of them, but they answer different questions.

## P_combustion Hockey-Stick Logic

The framework converts the combustion fatigue index into forced outage risk using a hockey-stick shape.

Plain-English version:

```text
Below about 60% of budget:
  P_combustion is near zero.

Above about 60% of budget:
  risk rises faster as damage approaches the budget.
```

ASCII view:

```text
P_combustion

high |                         /
     |                      __/
     |                   __/
     |                __/
low  |_______________/
     +--------------------------------
       0%       60%             100%
          combustion fatigue budget used
```

The exact shape is an assumption, not a measured law. The framework marks this as Amber because it needs calibration to plant history, fleet data, or expert review.

## Relationship To Creep-Fatigue Coupling

This guide focuses on combustion fatigue, but the framework says fatigue damage should not be evaluated alone.

Why:

```text
fatigue cycles
        +
time at high temperature
        =
combined creep-fatigue damage risk
```

So the combustion fatigue index is a driver of `D_f`, but the full life assessment still needs the interaction envelope from the first degradation guide.

| Item | Role |
| :--- | :--- |
| Combustion fatigue index | Tracks cycling severity for combustion hardware. |
| Creep damage `D_c` | Tracks time-at-temperature damage. |
| Fatigue damage `D_f` | Converts cycles into fatigue damage. |
| Interaction envelope | Checks whether combined damage is acceptable. |
| `P_combustion` | Converts high combustion stress into forced outage probability. |

## What The Framework Includes

The high-level framework includes:

| Included item | Why it matters |
| :--- | :--- |
| Start type classification | Hot/warm/cold starts have different thermal severity. |
| Trip tracking | Trips are severe fatigue events. |
| Load swing partial cycle credit | Captures flexible dispatch damage beyond starts. |
| Simplified damage index | Makes fatigue measurable without OEM FEA data. |
| Coupling with creep | Avoids treating fatigue as an independent safe/unsafe meter. |
| `P_combustion` outage link | Converts stress state into forced outage risk. |
| CI scope linkage | Connects combustion hardware stress to inspection and repair cost. |
| Daily feedback | Carries cycling damage into tomorrow's risk state. |

## What The Framework Leaves Out

The current high-level framework does not fully specify:

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| OEM-specific combustion life curves | Needed for true life prediction of liners and transition pieces. |
| Actual start ramp temperature profiles | A gentle start and aggressive start may not have the same fatigue damage. |
| Combustion mode-transfer details | DLN mode transfers can create dynamics during part-load and transient operation. |
| Combustion dynamics sensor data | Pressure oscillations can reveal faults before failure. |
| Exhaust temperature spread history | EGT spread can help detect combustor imbalance or local faults. |
| Rainflow counting of load cycles | Better cycle counting could replace the 0.3 load-swing shortcut. |
| Inspection findings | Borescope and CI results should reset or recalibrate the damage state. |
| Repair coverage detail | Actual LTSA language decides whether a combustion repair is covered, shared, or excluded. |

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| Combustion cycling as a high-priority factor | Local framework Section 3.2. | Green for model structure. |
| Hot/warm/cold start severity indices | Local framework note 1 and Appendix B.2, based on GER-3620K and EPRI 1012586 references. | Green for relative ranking; Amber for exact multiplier without OEM contract/data. |
| Trip damage index | Local framework Appendix B.2. | Amber because trip severity depends on operating state and event details. |
| Load swing 0.3 credit | Local framework Appendix B.2. | Red because the framework labels it engineering judgment needing sensitivity testing. |
| `P_combustion` hockey-stick shape | Local framework Sections 3.2.2 and Appendix B.2. | Amber; needs calibration. |
| Cycling damage and forced-outage linkage | NREL Power Plant Cycling Costs. | Green for general concept; Amber for unit-specific transfer. |
| LCF, Miner damage, and cycle counting concepts | NASA NASALife reference. | Green for method family; not plant-specific. |
| Combustion fault monitoring context | MDPI combustion fault detection paper and CCJ combustion dynamics monitoring article. | Green for monitoring relevance; not directly a fatigue-index calibration. |

External references used for validation:

- NREL, "Power Plant Cycling Costs": https://www.nrel.gov/docs/fy12osti/55433.pdf
- NASA NTRS, "NASALIFE - Component Fatigue and Creep Life Prediction Program": https://ntrs.nasa.gov/citations/20110015541
- MDPI Energies, "A Comparative Study on Fault Detection Methods for Gas Turbine Combustion Systems": https://www.mdpi.com/1996-1073/14/2/389
- Combined Cycle Journal, "Advanced combustion-dynamics monitoring detects impending combustor failure, prevents forced outage": https://www.ccj-online.com/advanced-combustion-dynamics-monitoring-detects-impending-combustor-failure-prevents-forced-outage/

## Open Questions Before Investment Use

Before using this factor in an investment committee deck, answer these:

| Question | Why it matters |
| :--- | :--- |
| What OEM combustion life model applies to this exact GT frame and hardware set? | Public multipliers are not enough for final life claims. |
| How does the actual LTSA count starts, trips, and combustion inspections? | Contract economics can differ from the simplified framework. |
| Do we have historian data for starts, trips, ramps, and load swings? | Real operating traces can replace simplified assumptions. |
| Are combustion dynamics and EGT spread available? | They can reveal faults not captured by start counts alone. |
| What did the last CI/HGP borescope show? | Inspection findings should recalibrate the fatigue state. |
| Should load swings use rainflow counting instead of the 0.3 shortcut? | This is the weakest parameter in the current guide. |
| How should a CI reset the combustion fatigue index? | Replacing liners may reset more damage than cleaning or minor repair. |
| How should combustion fatigue feed dispatch mode penalties? | The model needs a defensible link from stress to operating decisions. |

## One-Sentence Takeaway

Combustion cycling fatigue is the damage from repeatedly heating, cooling, tripping, and ramping the GT combustion system; the framework turns those events into a fatigue index that feeds forced-outage risk and future dispatch economics.
