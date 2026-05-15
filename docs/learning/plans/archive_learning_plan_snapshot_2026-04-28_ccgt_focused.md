# Gas Turbine Learning Docs Plan

## Purpose

This learning area is for building up gas turbine modeling knowledge from the basics before going deep into degradation factors. The target reader is new to gas turbine performance modeling, LTSA terms, and daily dispatch feedback. The docs should explain the ideas slowly enough to learn from, while staying tied to the InfraSure model and the Athens-type GE 7FA combined-cycle example.

The first writing phase should cover core vocabulary and plant anatomy:

- Combined-cycle plant anatomy and acronyms
- Capacity
- Heat rate
- EOH and starts
- Start costs and variable O&M
- Dispatch and the daily loop
- Outages, availability, and LTSA coverage
- State vector and feedback

The second writing phase should cover the eight degradation and stress factors in the framework:

- EOH accumulation with creep-fatigue coupling
- Capacity derating from ambient temperature
- Heat rate degradation
- Combustion cycling fatigue
- HRSG cycling damage
- Compressor degradation: fouling plus erosion
- Thermal barrier coating life
- Rotor life consumption

No code or model logic changes are part of this learning-doc track.

## Folder Structure

```text
docs/
  learning/
    00_learning_plan.md
    basics/
      00_combined_cycle_plant_anatomy.md
      01_capacity.md
      02_heat_rate.md
      03_eoh_and_starts.md
      04_start_costs_and_vom.md
      05_dispatch_and_daily_loop.md
      06_outages_availability_and_ltsa.md
      07_state_vector_and_feedback.md
    degradation_factors/
      01_eoh_creep_fatigue_coupling.md
      02_capacity_derating.md
      03_heat_rate_degradation.md
      04_combustion_cycling_fatigue.md
      05_hrsg_cycling_damage.md
      06_compressor_degradation.md
      07_tbc_life.md
      08_rotor_life_consumption.md
```

Only this planning file is created in the first implementation pass. The other files above are the planned roadmap and should be written one at a time.

## Big Picture Learning Path

The model can be learned as one repeated daily loop:

```text
Yesterday's plant condition
        |
        v
Hourly weather + hourly power prices + daily gas price
        |
        v
Step 2 dispatch model
        |
        v
Hourly operating profile for the day
        |
        v
Daily engineering update
        |
        v
New EOH, heat rate, capacity, start costs, VOM, outage risk
        |
        v
Tomorrow's dispatch economics
```

The important learning point is that "daily" does not mean the model ignores hourly dispatch. The dispatch model still reasons over hourly price and operating conditions. The daily level is the checkpoint where hourly operation is compressed into state updates like fired hours, starts, load profile, degradation, outage risk, and LTSA proximity.

## Writing Standards

Each guide should be detailed and descriptive, but not written like an academic paper. Use this style:

- Start from plain language before formulas.
- Add a first-time-reader layer before technical sections when hidden assumptions or acronyms appear.
- Use short sections with clear headings.
- Include tables for definitions, inputs, outputs, and assumptions.
- Include ASCII diagrams where a flow, relationship, or curve is easier to see visually.
- Use simple numbers from the Athens-type GE 7FA example when possible.
- Separate "what the framework says" from "what we still need to research or calibrate."
- Mark uncertainty honestly: Green, Amber, Red.
- Avoid claiming OEM-specific precision where the framework uses public data or assumptions.
- Keep formulas visible but explain what each term means.

Beginner-grounding checklist:

- Define important acronyms before using them heavily.
- Explain the physical equipment or plant behavior before the model variable.
- Explain why the concept exists in the real plant, not only how the model calculates it.
- Include a small "one event becomes model signals" flow when the topic touches dispatch.
- Call out where a term is contractual, physical, financial, or dispatch-related.
- Add a simple example before advanced caveats.

Good guide shape:

```text
# Topic Name

## First-Time Reader Map
## Why This Matters
## Plain-English Concept
## Plant Context
## Inputs Used By The Model
## Daily Update Logic
## Worked Example
## Tables / ASCII Plots
## What The Framework Includes
## What The Framework Leaves Out
## Source Basis And Certainty
## Open Questions Before Investment Use
```

## Beginner Grounding Review Backlog

As the docs mature, run a beginner-grounding pass before adding more advanced material. This pass should find places where the guide assumes the reader already knows plant parts, contract terms, inspection acronyms, or dispatch vocabulary.

Priority review order:

| Priority | File | Why review it |
| :--- | :--- | :--- |
| Done | `basics/03_eoh_and_starts.md` | Adds first-time explanation for starts, EOH, CI, HGP, MI, inspections, and why starts become model signals. |
| Done | `basics/04_start_costs_and_vom.md` | Adds first-time explanation for cost buckets, GT/HRSG/ST split, VOM, overages, and how one start becomes model signals. |
| Done | `basics/06_outages_availability_and_ltsa.md` | Adds first-time explanation for plant states, outage causes, coverage, guarantees, insurance, and financial classification. |
| Done | `basics/05_dispatch_and_daily_loop.md` | Adds first-time explanation for dispatch, unit commitment, economic dispatch, hourly prices, daily state updates, and feedback. |
| Done | `basics/07_state_vector_and_feedback.md` | Adds first-time explanation for state as model memory, opening/closing state, feedback, state updates, and what is not state. |
| Done | `degradation_factors/01_eoh_creep_fatigue_coupling.md` | Adds first-time explanation for contract EOH vs physical creep-fatigue damage, two-meter logic, and why both views matter. |
| Done | `degradation_factors/04_combustion_cycling_fatigue.md` | Adds first-time explanation for combustor hardware, LCF/HCF, fatigue index, and why combustion fatigue is not just EOH. |
| 1 | Remaining degradation guides | Check for hidden acronyms and add beginner maps where needed. |

## Basics Guide Roadmap

| Order | Planned file | Main question answered | Must include |
| :--- | :--- | :--- | :--- |
| 0 | `basics/00_combined_cycle_plant_anatomy.md` | What are GT, ST, HRSG, BOP, LTSA, and the plant acronyms? | Combined-cycle flow, equipment map, 2x1/1x1 meaning, BOP, emissions systems, inspection acronyms, units glossary. |
| 1 | `basics/01_capacity.md` | How much power can the plant produce? | MW, ISO capacity, net plant capacity, ambient derate, effective capacity, simple derate table. |
| 2 | `basics/02_heat_rate.md` | How much fuel does the plant need per MWh? | BTU/kWh, lower is better, gas cost conversion, spark spread impact, heat rate degradation. |
| 3 | `basics/03_eoh_and_starts.md` | How does operation become maintenance life consumption? | Fired hours, hot/warm/cold starts, trips, load swings, EOH accounting, CI/HGP/MI meanings, LTSA thresholds. |
| 4 | `basics/04_start_costs_and_vom.md` | What does it cost to start and run the plant besides fuel? | GT start cost, HRSG/ST start cost, wear cost, VOM, overage charges, EOH proximity penalty. |
| 5 | `basics/05_dispatch_and_daily_loop.md` | Why is Step 2 hourly but the model loop daily? | Hourly commitment, daily summary, dynamic state feedback, Mode A/B/C dispatch behavior. |
| 6 | `basics/06_outages_availability_and_ltsa.md` | How do outages and the service contract affect risk? | Planned outage, forced outage, availability, LTSA/CSA coverage, covered vs uncovered cost. |
| 7 | `basics/07_state_vector_and_feedback.md` | What plant condition is carried into tomorrow? | State vector, degraded capacity, degraded heat rate, start costs, VOM, risk state, feedback loop. |

### Basics Guide Details

#### 0. Combined-Cycle Plant Anatomy

Core teaching goal: make the physical plant vocabulary understandable before introducing model variables.

Must explain:

- GT as the gas turbine that burns fuel and directly produces electricity.
- HRSG as the heat recovery steam generator downstream of GT exhaust.
- ST as the steam turbine that uses HRSG steam to produce additional electricity.
- BOP as the supporting systems around the main equipment.
- 2x1 and 1x1 combined-cycle configuration language.
- OEM, LTSA/CSA, CI, HGP, MI, EOH, VOM, HHV/LHV, MW/MWh, and related acronyms.

Use this basic plant map:

```text
Natural gas + air
      |
      v
     GT ---- electricity
      |
      | hot exhaust
      v
    HRSG ---- steam ---- ST ---- electricity
      |
      v
 stack / emissions controls
```

#### 1. Capacity

Core teaching goal: capacity is the maximum output available under current conditions, not a fixed number.

Use the Athens-type values from the framework:

| Ambient condition | Net plant capacity | Meaning |
| :--- | ---: | :--- |
| 59 deg F ISO | 531 MW | Reference clean baseline. |
| 80 deg F | 499 MW | Hotter air reduces output. |
| 95 deg F | 469 MW | Summer conditions can materially reduce revenue opportunity. |

Possible ASCII plot:

```text
Capacity
565 MW |*  cold day
531 MW |      *  ISO
499 MW |              *  warm day
469 MW |                    *  hot day
       +--------------------------------
        0F     59F     80F      95F
```

#### 2. Heat Rate

Core teaching goal: heat rate is fuel intensity. A higher heat rate means more fuel cost per MWh and weaker dispatch economics.

Key example:

```text
Fuel cost per MWh = heat rate in MMBtu/MWh * gas price in $/MMBtu

7,070 BTU/kWh = 7.070 MMBtu/MWh
At $4.00/MMBtu gas:
7.070 * 4.00 = $28.28/MWh fuel cost
```

The guide should explain why a 1% heat-rate increase is financially meaningful across many dispatched MWh.

#### 3. EOH And Starts

Core teaching goal: EOH is not just clock hours. Starts, trips, and cycling consume equivalent life.

Use the framework's EOH table:

| Operation | EOH impact |
| :--- | ---: |
| Fired hour on natural gas at base load | 1 EOH/hr |
| Hot start | 50 EOH |
| Warm start | 150 EOH |
| Cold start | 350 EOH |
| Emergency trip | 500 EOH |
| Large load swing | 0.3 EOH per swing |

Simple example:

```text
One day:
- 10 fired hours
- 1 hot start
- 2 large load swings

EOH = 10 + 50 + (2 * 0.3)
EOH = 60.6
```

#### 4. Start Costs And VOM

Core teaching goal: start cost is a real economic hurdle, and the model splits GT wear from HRSG/ST thermal stress.

Explain:

- GT fuel and auxiliaries
- GT wear cost linked to EOH
- HRSG/ST start cost linked to thermal differential
- VOM per MWh
- LTSA overage charges
- EOH proximity penalty in dispatch Modes B and C

#### 5. Dispatch And Daily Loop

Core teaching goal: the dispatch model makes hourly decisions, but the plant state updates daily.

Include this diagram:

```text
Hourly level inside the day:

Hour 01 02 03 ... 24
     |  |  |      |
     price, temp, gas economics, unit commitment

Daily checkpoint:

fired hours + starts + load profile + outages
        |
        v
updated state for tomorrow
```

#### 6. Outages, Availability, And LTSA

Core teaching goal: not every non-running hour means the same thing.

Include:

| Term | Meaning | Financial effect |
| :--- | :--- | :--- |
| Planned outage | Scheduled inspection or maintenance | Lost revenue plus planned maintenance cost. |
| Forced outage | Unexpected failure or trip-related downtime | Lost revenue, repair cost, possible insurance/LTSA question. |
| Availability | Share of time plant is available to run | Affects revenue, guarantees, and investor risk. |
| LTSA/CSA | Long-term service agreement | Defines inspections, coverage, exclusions, and cost split. |

#### 7. State Vector And Feedback

Core teaching goal: the state vector is the model's memory.

Examples of state variables:

- Contractual EOH
- Creep damage fraction
- Fatigue damage fraction
- Heat rate degradation
- Compressor fouling
- TBC time-at-temperature
- HRSG drum cycle count
- Rotor life fraction
- Effective capacity
- Effective heat rate
- Start cost multipliers

## Degradation-Factor Guide Roadmap

| Order | Planned file | Factor | Why it matters |
| :--- | :--- | :--- | :--- |
| 1 | `degradation_factors/01_eoh_creep_fatigue_coupling.md` | EOH accumulation with creep-fatigue coupling | Drives inspection timing, LTSA cost, and hidden physical failure risk. |
| 2 | `degradation_factors/02_capacity_derating.md` | Capacity derating from ambient temperature | Reduces MW output exactly when hot-weather prices may be high. |
| 3 | `degradation_factors/03_heat_rate_degradation.md` | Heat rate degradation | Raises fuel cost and weakens dispatch competitiveness. |
| 4 | `degradation_factors/04_combustion_cycling_fatigue.md` | Combustion cycling fatigue | Converts starts, trips, and load swings into LCF damage and outage risk. |
| 5 | `degradation_factors/05_hrsg_cycling_damage.md` | HRSG cycling damage | Captures combined-cycle start stress outside the GT-only view. |
| 6 | `degradation_factors/06_compressor_degradation.md` | Compressor fouling and erosion | Explains a major recoverable and non-recoverable source of heat-rate loss. |
| 7 | `degradation_factors/07_tbc_life.md` | Thermal barrier coating life | Models path-specific coating failure risk using Weibull sampling. |
| 8 | `degradation_factors/08_rotor_life_consumption.md` | Rotor life consumption | Tracks low-probability, high-severity tail risk. |

### Degradation Guide Required Sections

Each degradation-factor guide should use this fixed structure.

| Section | Purpose |
| :--- | :--- |
| Beginner summary | Explain the factor in plain language without formulas. |
| Why it matters financially | Connect the factor to revenue, cost, outages, LTSA, or insurance. |
| Physical mechanism | Explain what is physically changing in the plant. |
| Model inputs | List hourly, daily, asset, and contract inputs used by this factor. |
| Daily update logic | Explain how the factor updates at the daily checkpoint. |
| Worked example | Use a simple numerical example from the Athens-type plant where possible. |
| Tables and ASCII plots | Include visual aids for thresholds, curves, or flow. |
| Framework coverage | Quote or summarize what the high-level framework already says. |
| Missing detail | Call out what the high-level framework does not fully specify. |
| Source basis | List local and external references, with certainty rating. |
| Open questions | Identify what should be calibrated before investor use. |

## Degradation Guide Notes

### 1. EOH Accumulation With Creep-Fatigue Coupling

Begin with the distinction between contractual EOH and physics-based damage.

```text
Contractual view:
hours + starts + trips -> EOH -> inspection timing and billing

Physics view:
time-at-temperature -> creep damage
thermal cycles       -> fatigue damage
combined damage      -> outage risk
```

Must explain:

- Why one fired hour is not equivalent to one start.
- Why creep and fatigue are coupled rather than independent.
- Robinson life-fraction rule for creep, at a beginner level.
- Miner's rule for fatigue, at a beginner level.
- Interaction envelope: combined damage limit can be lower when both mechanisms contribute.
- Why a heavily cycled unit can look acceptable by contractual EOH but riskier by physical damage.

What the framework leaves out:

- Actual OEM material data.
- Actual blade metal temperature measurements.
- Plant-specific stress model.
- Calibrated S-N curves for exact components.

### 2. Capacity Derating

Begin with the idea that gas turbines breathe air. Hot air is less dense, so the machine has less mass flow and less output.

Must explain:

- ISO capacity vs effective capacity.
- Hourly ambient temperature effect.
- Why derating matters most during high-price hot days.
- Difference between temporary ambient derate and permanent degradation.

What the framework leaves out:

- Humidity-specific correction details.
- Exact OEM correction curves.
- Inlet cooling configuration and performance if not specified.

### 3. Heat Rate Degradation

Begin with fuel efficiency: lower heat rate is better.

Must explain:

- Baseline heat rate.
- Ambient correction.
- Part-load correction.
- Recoverable degradation after fouling or HGP wear.
- Non-recoverable degradation such as erosion or age-related plant losses.
- Why heat-rate degradation feeds back into dispatch.

Example logic:

```text
Clean HR = 7,070 BTU/kWh
1% degradation = 7,140.7 BTU/kWh
Extra HR = 70.7 BTU/kWh = 0.0707 MMBtu/MWh
At $4/MMBtu, extra fuel = $0.28/MWh
```

What the framework leaves out:

- Measured plant heat-rate test data.
- Actual compressor wash history.
- Exact allocation between compressor, HGP, HRSG, and BOP losses.

### 4. Combustion Cycling Fatigue

Begin with the idea that starts are thermal shocks. More severe starts create larger expansion/contraction cycles.

Must explain:

- Low-cycle fatigue.
- Hot vs warm vs cold starts.
- Emergency trip as severe event.
- Load swings as partial cycles.
- How fatigue damage affects forced outage probability.
- Why this factor couples with creep.

What the framework leaves out:

- Exact combustor component S-N curves.
- Plant-specific thermal transient measurements.
- Firm basis for the load-swing partial-cycle credit.

### 5. HRSG Cycling Damage

Begin with the HRSG as the steam-side equipment that sees temperature and pressure swings during starts.

Must explain:

- HP drum fatigue.
- Headers, attemperators, and steam turbine warming.
- Why HRSG/ST costs are split from GT costs.
- Why cold starts are much more damaging than hot starts.
- Why HRSG damage can be excluded or only partly covered under CSA terms.

What the framework leaves out:

- Actual HRSG design details.
- Drum wall temperature gradients.
- Attribution data for forced outage causes.
- Plant-specific inspection findings.

### 6. Compressor Degradation

Begin with the compressor as the front end of the GT that compresses inlet air. Dirty or eroded blades reduce airflow and efficiency.

Must explain:

- Fouling as recoverable deposit buildup.
- Erosion as non-recoverable material loss.
- Non-linear fouling accumulation: fast early loss, slower later loss.
- Offline wash vs online wash.
- Air quality index scaling.
- Why compressor condition affects both heat rate and capacity.

Use this basic curve:

```text
Fouling loss
High |                 ______ asymptote A
     |             ___/
     |         ___/
     |     ___/
Low  |____/
     +-------------------------
        fired hours since wash
```

What the framework leaves out:

- Actual inlet filtration condition.
- Wash schedule records.
- Measured compressor efficiency trend.
- Site-specific particulate and humidity history.

### 7. Thermal Barrier Coating Life

Begin with TBC as a protective coating on hot gas path parts. It helps keep metal cooler, but it can crack or spall.

Must explain:

- Why coating failure is not best represented as a fixed deterministic date.
- Weibull distribution as a way to represent path-specific failure timing.
- Shape parameter beta and scale parameter eta at a beginner level.
- Time-at-temperature as the main accumulator.
- Forced outage behavior when threshold is crossed.

What the framework leaves out:

- Exact coating composition.
- Actual coating inspection condition.
- Fuel contaminant measurements.
- OEM repair/replacement criteria.

### 8. Rotor Life Consumption

Begin with the rotor as a high-energy rotating component where failure is rare but severe.

Must explain:

- Start-stop cycles and thermal transients.
- Centrifugal stress during operation.
- Life fraction consumed.
- Why this is a tail risk rather than a normal recurring cost item.
- Why the daily probability is very low but financially important.

What the framework leaves out:

- Actual rotor serial history.
- OEM rotor life assessment.
- NDE findings.
- Long-lead replacement and repair logistics.

## Source Register

Use local sources first. External references should deepen the learning docs but not replace model-specific assumptions in the framework.

| Source | Link or path | Use in learning docs |
| :--- | :--- | :--- |
| InfraSure framework | `docs/InfraSure_ModelingFramework_V2.md` | Primary local source for model architecture, factors, assumptions, Athens pilot values, and guide scope. |
| InfraSure digital twin PDF | `docs/InfraSure_GT_DigitalTwin_v2.pdf` | High-level 5-step pipeline, daily loop framing, investor explanation. |
| NREL Power Plant Cycling Costs | https://www.nrel.gov/docs/fy12osti/55433.pdf | HRSG/ST cycling, start cost context, cycling cost structure. |
| Cambridge creep-LCF EOH article | https://resolve.cambridge.org/core/journals/aeronautical-journal/article/gas-turbine-equivalent-operating-hour-estimation-considering-creeplcf-interactions/71B12D0158F2AD4FEC97A50B214AB918 | Physics-based EOH, creep-LCF interaction, damage summation framing. |
| NASA NASALife | https://ntrs.nasa.gov/citations/20110015541 | Fatigue and creep life-prediction methods, mission damage concepts, rainflow/cycle counting context. |
| ISO 2314 | https://www.iso.org/standard/42989.html | Gas turbine performance and acceptance-test context for capacity and heat-rate concepts. |
| NERC GADS DRI | https://www.nerc.com/globalassets/programs/rapa/gads/conventional/gads_dri_2024.pdf | Outage and availability vocabulary, forced outage reporting context. |

## Certainty Rating Standard

Use the same rating language as the framework.

| Rating | Meaning | How to write it |
| :--- | :--- | :--- |
| Green | Well-supported by published standards, public references, or stable engineering practice. | State with confidence, but still avoid OEM-specific overclaiming. |
| Amber | Reasonable industry benchmark or model assumption with moderate uncertainty. | Explain why it is plausible and what data would improve it. |
| Red | Sensitivity-test required before investment decisions. | Make the uncertainty visible and do not bury it in prose. |

## What The High-Level Framework Does Not Do

The learning docs should repeatedly make this boundary clear:

- The framework is not an OEM design model.
- It does not use proprietary material databases.
- It does not run finite element stress analysis.
- It does not use real-time sensor streams unless added later.
- It does not know the exact condition of every blade, vane, combustor liner, HRSG tube, or rotor disc.
- It uses public references, contract terms, asset assumptions, and daily operating profiles to create a due-diligence-grade probabilistic model.

That distinction matters. The docs should teach users what the model is strong at: connecting dispatch, degradation, maintenance timing, outage risk, and cashflow. They should also teach where plant-specific data would improve confidence.

## Acceptance Checklist

The planning file is complete when:

- `docs/learning/00_learning_plan.md` exists.
- `docs/learning/basics/` exists.
- `docs/learning/degradation_factors/` exists.
- The plan lists all eight basics guides, including the plant-anatomy foundation.
- The plan lists all eight degradation-factor guides.
- Plant anatomy, capacity, heat rate, EOH, start cost, dispatch, outages, LTSA, and state feedback are all covered in the basics roadmap.
- The daily loop and Step 2 dispatch relationship are explained.
- Markdown tables are readable.
- ASCII diagrams are readable in plain text.
- Local and external source links are captured.

## Recommended Next Step

After the basics sequence is complete, start the degradation-factor guides with `docs/learning/degradation_factors/01_eoh_creep_fatigue_coupling.md`. That guide should build on `basics/00_combined_cycle_plant_anatomy.md` and `basics/03_eoh_and_starts.md`.
