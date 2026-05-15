# HRSG Cycling Damage

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read this basics guide first if start costs are new: [Start Costs And VOM](../basics/04_start_costs_and_vom.md).

> Plant-Type Applicability
> HRSG cycling damage is not universal to all gas plants. It applies when the plant has HRSG, steam-generator, or steam-side heat-recovery equipment, such as CCGT and some CHP/cogeneration plants. It does not apply to a simple-cycle GT with no HRSG/ST equipment.

## Why This Matters

HRSG cycling damage answers a combined-cycle question:

> What damage does starting, stopping, ramping, and tripping create on the steam side of the plant?

The previous guide focused on GT combustion cycling fatigue. This guide focuses on the HRSG and steam-side equipment.

In a combined-cycle plant, a start is not only a gas turbine event. The GT heats up, but its hot exhaust also heats the HRSG. The HRSG makes steam. The steam turbine and steam piping warm up. Pressure rises. Spray attemperators may operate to control steam temperature. Those thermal and pressure changes create cycling damage.

```text
GT start
  |
  v
hot exhaust into HRSG
  |
  v
steam drum, headers, tubes, attemperators heat and pressurize
  |
  v
steam turbine warming
  |
  v
HRSG/ST cycling damage and start cost
```

The financial point is direct:

```text
more cycling
  -> more HRSG/ST wear
  -> higher start cost
  -> higher forced outage risk
  -> fewer available high-value dispatch hours
```

## Plain-English Concept

The HRSG is the heat recovery steam generator. It sits downstream of the gas turbine exhaust and turns water into steam for the steam turbine.

HRSG cycling damage means repeated heating, cooling, pressurizing, depressurizing, and temperature-control actions slowly consume life in steam-side components.

Beginner version:

```text
Hot start  = steam-side equipment is still warm.
Warm start = steam-side equipment cooled part way.
Cold start = steam-side equipment cooled deeply.
Trip       = rapid pressure and temperature disturbance.
```

The colder the steam-side equipment is before restart, the larger the temperature change during startup. Larger temperature change generally means higher thermal stress.

## Plant-Type Applicability

This is the clearest example where plant type changes whether the guide applies at all.

| Plant type | Applies? | Why |
| :--- | :---: | :--- |
| Simple-cycle GT | No | There is no HRSG or steam turbine in the basic plant stack. |
| Combined-cycle GT | Yes | GT exhaust heats HRSGs, creates steam, and warms the ST. |
| 1x1 CCGT mode | Yes | One GT/HRSG train cycles; cost and damage can be lower than full 2x1. |
| 2x1 CCGT mode | Yes | Both GT/HRSG trains and the shared ST may participate. |
| CHP / cogeneration | Maybe | Applies if steam-generation or heat-recovery equipment cycles with the GT. |
| Gas reciprocating engine | No, unless paired with a heat-recovery steam system | Engine-only degradation needs different logic. |

The Athens cost and fatigue-index tables below are CCGT examples, not simple-cycle assumptions.

## Where This Happens In The Plant

The framework names three main HRSG damage areas:

| Area | Plain-English role | Why cycling matters |
| :--- | :--- | :--- |
| HP drum | High-pressure steam drum separating steam and water. | Thick metal sees temperature gradients during startup and shutdown. |
| Headers | Large pipes that collect and distribute steam/water. | Thermal expansion and pressure cycling can lead to cracking. |
| Attemperators | Spray systems used to control steam temperature. | Frequent cycling can increase valve, spray, and thermal shock wear. |
| Steam turbine warming | Controlled warming of the ST before loading. | Too-fast warming can create rotor and casing thermal stress. |
| HRSG tubes | Heat-transfer surfaces in GT exhaust path. | Startup/shutdown changes flow, pressure, and metal temperature. |

Plant map:

```text
GT hot exhaust
      |
      v
   +------+
   | HRSG |-- steam --> ST
   +------+
      |
      +-- HP drum
      +-- headers
      +-- attemperators
      +-- tubes
```

## Why HRSG Damage Is Separate From GT Damage

The framework splits GT and HRSG/ST start costs because the damage mechanisms are different.

| Area | Main stress driver | Framework cost behavior |
| :--- | :--- | :--- |
| GT | EOH, starts, hot gas path wear, combustion fatigue. | GT wear cost can be adjusted by EOH proximity penalty. |
| HRSG/ST | Temperature differential, pressure transients, steam-side warmup. | HRSG/ST costs scale with thermal differential, not GT EOH proximity. |

This distinction matters in Step 2 dispatch. A start can be cheap or expensive depending on both:

```text
GT wear economics
        +
HRSG/ST steam-side cycling cost
```

If the model ignored HRSG/ST damage, it would understate the true cost of cycling a combined-cycle plant.

## Framework HRSG/ST Start Cost Table

The framework gives HRSG/ST start costs at plant level:

| Start type | HRSG thermal stress | ST warming | Attemperator wear | HRSG/ST subtotal | HRSG drum fatigue index |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Hot | $3K | $2K | $1K | $6K | 1.0 |
| Warm | $8K | $5K | $3K | $16K | 2.5 |
| Cold | $15K | $8K | $5K | $28K | 5.0 |
| Trip | $5K | $3K | $2K | $10K | 3.0 |

Beginner interpretation:

```text
Hot start  = reference HRSG cycle.
Warm start = about 2.5x hot-start drum fatigue.
Cold start = about 5.0x hot-start drum fatigue.
Trip       = severe pressure transient, but lower drum index than cold start.
```

This ranking is different from the GT combustion fatigue ranking. For the HRSG drum, cold restart thermal differential is the dominant concern.

## HRSG Drum Fatigue Index

For learning, the daily HRSG drum fatigue index can be written as:

```text
daily_hrsg_drum_fatigue =
  1.0 * hot_starts
  + 2.5 * warm_starts
  + 5.0 * cold_starts
  + 3.0 * trips
```

The framework does not list a separate load-swing partial-cycle credit for HRSG drum damage in the same way it does for combustion fatigue. It does mention ramp rate and thermal cycles as drivers, so a future version could add a more detailed ramp/cycle counting method.

## Damage Severity Ladder

```text
Relative HRSG drum fatigue severity

Hot start       |##########                              | 1.0
Warm start      |#########################               | 2.5
Trip            |##############################          | 3.0
Cold start      |##################################################| 5.0
```

The bars show the framework's relative weights, not measured crack growth.

## Why Cold Starts Are So Severe For HRSGs

Cold starts matter because thick steam-side components can have large temperature differences between the inside and outside metal.

Simple picture:

```text
cold metal + hot exhaust / steam
        |
        v
inside surface heats faster than outside surface
        |
        v
temperature gradient through thick metal
        |
        v
thermal stress
        |
        v
fatigue damage over repeated cycles
```

That is why the framework says HP drum fatigue life is primarily driven by restart temperature differential, and why cold starts impose about 3x to 5x the drum fatigue damage of hot starts.

## 1x1 And 2x1 Operating Nuance

The Athens-type plant is a 2x1 combined cycle:

```text
GT-A -> HRSG-A --+
                 +--> common steam system -> ST
GT-B -> HRSG-B --+
```

The framework also allows 1x1 operation:

```text
one GT + one HRSG + partial steam-cycle operation
```

This matters because 1x1 operation can reduce start cost:

| Start case | Framework total start cost | Why it matters |
| :--- | ---: | :--- |
| 2x1 hot start | $36K | Both GTs and the fuller steam cycle are involved. |
| 1x1 hot start | $19K | Single GT plus partial HRSG/ST operation. |

The HRSG/ST portion of the 1x1 hot start is $4K in the framework, compared with $6K for a full 2x1 hot start. This enables lower-cost partial dispatch, but it also means the model should track which train is being cycled.

## Daily Model Inputs

HRSG cycling damage uses dispatch outputs and plant state.

| Input | Frequency | Source | Why it matters |
| :--- | :--- | :--- | :--- |
| Start type | Event-level, daily summary | Step 2 dispatch | Hot, warm, and cold starts have different thermal differential. |
| Hours since shutdown | Daily state | Dispatch / operations | Determines whether the start is hot, warm, or cold. |
| Ramp rate | Hourly or event summary | Dispatch profile | Faster ramps can create stronger steam-side transients. |
| GT load profile | Hourly | Step 2 dispatch | Controls HRSG heat input and steam generation. |
| Trip events | Event-level | Operations / failure module | Rapid pressure transient and interruption of normal startup/shutdown path. |
| HRSG train configuration | Hourly or daily | Dispatch model | 1x1 vs 2x1 determines which HRSG train cycles. |
| Current HRSG drum cycle count | Daily state | Engineering model | Carries steam-side cycling damage forward. |
| HRSG drum fatigue life fraction | Daily state | Engineering model | Indicates how much life has been consumed. |
| Attemperator condition | Daily or inspection state | Maintenance records | Affects HRSG forced outage risk. |
| Plant age | Static / annual | Asset specs | Scales background HRSG risk in the framework. |

## Model Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| HRSG drum fatigue index | Engineering state | Relative steam-drum cycling damage. |
| HRSG/ST start cost | Step 2 dispatch | Steam-side cost added to GT start cost. |
| `P_HRSG` | Forced outage module | HRSG-related forced outage probability. |
| HRSG outage duration draw | Financial layer | Downtime if an HRSG-related outage occurs. |
| Owner O&M exposure | Financial layer | HRSG/ST may be outside GT-focused CSA coverage. |
| Updated HRSG state | Tomorrow's dispatch | Carries steam-side stress into the next day. |

## Daily Update Logic

The daily logic is similar to combustion cycling fatigue, but the equipment is different.

| Step | Update | Plain-English purpose |
| :--- | :--- | :--- |
| 1 | Read opening HRSG state. | Start with drum cycle count, fatigue life fraction, outage status, and train configuration. |
| 2 | Check forced outage risk. | If HRSG risk triggers an outage, dispatch cannot execute normally. |
| 3 | Run Step 2 dispatch if available. | Determine GT starts, HRSG heat input, 1x1 or 2x1 mode, and ramps. |
| 4 | Classify start type. | Use shutdown duration to classify hot, warm, or cold. |
| 5 | Add HRSG drum fatigue index. | Apply hot/warm/cold/trip weights. |
| 6 | Add HRSG/ST start cost. | Add thermal stress, ST warming, and attemperator wear cost. |
| 7 | Update `P_HRSG`. | Scale outage probability with drum cycles, attemperator condition, and age. |
| 8 | Carry HRSG state forward. | Tomorrow's dispatch sees updated cost and risk state. |

ASCII version:

```text
hourly dispatch profile
        |
        v
start type + ramp rate + HRSG train used
        |
        v
HRSG drum fatigue index
        |
        +--> HRSG/ST start cost
        |
        v
P_HRSG forced outage risk
        |
        v
next day's plant state
```

## How It Feeds Step 2 Dispatch

HRSG cycling damage affects Step 2 in two main ways.

| Dispatch effect | What Step 2 sees |
| :--- | :--- |
| Higher start cost | HRSG/ST cost is added to GT start cost before deciding whether a run clears. |
| Higher outage risk | `P_HRSG` can make the unit unavailable before high-value dispatch hours. |

Important distinction:

```text
GT wear cost can rise with EOH proximity in Modes B and C.
HRSG/ST start cost is not multiplied by GT EOH proximity in the framework.
```

The HRSG/ST cost is still real. It just follows a different driver:

```text
GT wear driver       = EOH proximity and GT starts
HRSG/ST wear driver  = steam-side temperature differential and cycling
```

This is why the framework decomposes the start cost instead of using one undifferentiated plant start cost.

## Worked Example 1: One Hot Start Day

Assume a 2x1 hot start:

| Item | Value |
| :--- | ---: |
| Hot starts | 1 |
| Warm starts | 0 |
| Cold starts | 0 |
| Trips | 0 |

HRSG drum fatigue:

```text
daily_hrsg_drum_fatigue = 1.0 * 1
daily_hrsg_drum_fatigue = 1.0
```

HRSG/ST cost:

```text
HRSG thermal stress = $3K
ST warming = $2K
Attemperator wear = $1K

HRSG/ST subtotal = $6K
```

This is the reference steam-side cycling event.

## Worked Example 2: Cold Start Vs Hot Start

Compare one hot start with one cold start:

| Start type | HRSG/ST cost | HRSG drum fatigue index |
| :--- | ---: | ---: |
| Hot | $6K | 1.0 |
| Cold | $28K | 5.0 |

Difference:

```text
Cold start extra HRSG/ST cost = $28K - $6K
Cold start extra HRSG/ST cost = $22K

Cold start fatigue multiple = 5.0 / 1.0
Cold start fatigue multiple = 5x hot start
```

This is why avoiding unnecessary cold starts can be valuable even before considering GT EOH.

## Worked Example 3: 1x1 Hot Start

The framework includes a 1x1 hot start option.

| Item | Full 2x1 hot start | 1x1 hot start |
| :--- | ---: | ---: |
| GT subtotal | $30K | $15K |
| HRSG/ST subtotal | $6K | $4K |
| Total plant start cost | $36K | $19K |

Savings:

```text
Start cost reduction = $36K - $19K
Start cost reduction = $17K
```

This lower hurdle can make partial dispatch economic in hours where full 2x1 operation would not clear. The tradeoff is that the model should track which GT/HRSG train is accumulating starts and steam-side cycles.

## Worked Example 4: Illustrative P_HRSG Scaling

The framework lists a baseline HRSG daily probability:

```text
P_HRSG baseline = 0.75% per day
range = 0.5% to 1.0% per day
```

It says this risk is driven by HP drum, attemperator, and header failure, and scales with age and thermal cycles.

Illustrative example:

| Item | Value |
| :--- | ---: |
| Baseline `P_HRSG` | 0.75% per day |
| Thermal-cycle multiplier | 1.50 |
| Age multiplier | 1.10 |

```text
Adjusted P_HRSG = 0.75% * 1.50 * 1.10
Adjusted P_HRSG = 1.2375% per day
```

This is not a calibrated Athens result. It shows the structure: HRSG risk should rise when thermal-cycle damage and age increase.

## HRSG Cycling Vs Contractual EOH

HRSG cycling is not the same as GT contractual EOH.

| Counter | Equipment focus | Main use |
| :--- | :--- | :--- |
| GT contractual EOH | Gas turbine service contract | CI/HGP/MI timing and LTSA billing. |
| HRSG drum fatigue index | Steam-side HRSG equipment | HRSG forced outage risk and HRSG/ST start cost. |
| Plant start cost | Economic dispatch model | Determines whether a run is worth starting. |

The same start can update all three, but they answer different questions.

```text
one cold start
  |
  +--> GT EOH counter
  +--> GT combustion fatigue
  +--> HRSG drum fatigue
  +--> HRSG/ST start cost
  +--> future outage risk
```

## What The Framework Includes

The high-level framework includes:

| Included item | Why it matters |
| :--- | :--- |
| Separate HRSG cycling stress factor | Avoids treating combined-cycle starts as GT-only events. |
| HP drum fatigue index by start type | Gives a simple way to track steam-side thermal-cycle damage. |
| Attemperator wear cost | Recognizes that steam-temperature control equipment is affected by cycling. |
| ST warming cost | Includes steam turbine warmup in start economics. |
| Split GT and HRSG/ST start costs | Enables proper 1x1 and 2x1 dispatch modeling. |
| `P_HRSG` forced outage path | Converts HRSG condition into availability risk. |
| HRSG outage duration assumption | Lets the financial layer estimate lost revenue and repair timing. |
| Owner O&M treatment for HRSG | Recognizes HRSG/ST can sit outside a GT-focused CSA scope. |

## What The Framework Leaves Out

The high-level framework still simplifies several important items:

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| HRSG-specific thermal stress model | A real model would account for drum wall thickness, ramp rates, pressure, and temperature history. |
| Per-train HRSG tracking | A 2x1 plant can cycle HRSG-A and HRSG-B differently. |
| Detailed attemperator duty | Spray frequency, spray quality, and valve condition affect wear and thermal shock. |
| Header and tube inspection findings | Actual cracks, leaks, or repairs should recalibrate risk. |
| Steam turbine thermal stress model | ST rotor and casing warming are simplified as a start-cost component. |
| Duct burner behavior | If present, duct firing changes HRSG heat input and thermal stress. |
| Water chemistry and layup condition | Chemistry can interact with cycling damage and corrosion fatigue. |
| Exact LTSA/O&M coverage | HRSG/ST coverage often differs from GT coverage and must be verified. |

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| HRSG cycling as separate stress factor | Local framework Section 3.2 and digital-twin PDF. | Green for model structure. |
| HRSG/ST start cost split | Local framework Section 4.5. | Green as framework assumption; asset-specific cost needs validation. |
| HP drum fatigue indices | Local framework Appendix B.10, calibrated to NREL cycling-cost basis. | Green for relative direction; Amber for exact multiplier. |
| Trip HRSG fatigue index | Local framework Appendix B.10. | Amber because trip severity depends on event details. |
| `P_HRSG` baseline daily probability | Local framework Appendix B.8. | Amber because it needs fleet/plant calibration. |
| HRSG outage duration | Local framework Appendix B.9. | Amber because duration depends on failure mode and spare-part availability. |
| Cycling cost and reliability linkage | NREL Power Plant Cycling Costs. | Green for general concept; Amber for asset-specific transfer. |
| Availability and outage reporting context | NERC GADS data reporting instructions. | Green for reporting context; not a plant-specific failure-rate source by itself. |

External references used for validation:

- NREL, "Power Plant Cycling Costs": https://www.nrel.gov/docs/fy12osti/55433.pdf
- NERC, "2024 GADS Data Reporting Instructions": https://www.nerc.com/globalassets/programs/rapa/gads/conventional/gads_dri_2024.pdf

## Open Questions Before Investment Use

Before using this factor in an investment committee deck, answer these:

| Question | Why it matters |
| :--- | :--- |
| Is HRSG-A tracked separately from HRSG-B? | 2x1 operation can create uneven train-level cycling. |
| What are the actual HRSG OEM ramp-rate limits? | Ramp limits determine safe startup and load-following behavior. |
| Do we have attemperator spray history and valve maintenance records? | Attemperator condition is a direct HRSG risk driver. |
| What did the last HRSG inspection find? | Cracks, leaks, repairs, or tube issues should recalibrate risk. |
| Are HRSG/ST repairs covered by the CSA, owner O&M, or insurance? | Coverage decides who pays after a failure. |
| Is 1x1 operation modeled with train-level state tracking? | Without train tracking, starts may be allocated incorrectly. |
| Should ramp cycles be counted separately from starts? | Flexible operation may create HRSG damage without full starts. |
| How should HRSG risk scale with age and thermal cycles? | `P_HRSG` is a key uncertainty and should be sensitivity-tested. |

## One-Sentence Takeaway

HRSG cycling damage is the steam-side cost of combined-cycle flexibility: starts, trips, and ramps create thermal stress in drums, headers, attemperators, and the steam turbine, so the model tracks HRSG/ST wear separately from GT EOH.
