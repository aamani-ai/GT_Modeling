# Multi-Gas-Plant Learning Docs Generalization Plan

## Purpose

This plan corrects a scope problem in the current learning docs.

The current docs use the Athens-type GE 7FA 2x1 combined-cycle plant as the main teaching example. That is useful, but it can accidentally imply that every gas plant is a CCGT with GTs, HRSGs, an ST, CI/HGP/MI thresholds, and HRSG/ST start costs.

The long-term learning system should support gas-plant modeling more generally:

- Simple-cycle gas turbines
- Combined-cycle gas turbines
- Frame GTs and aeroderivative GTs
- Peaking, cycling, mid-merit, and baseload duty patterns
- CHP / cogeneration plants where steam or heat obligations matter
- Optional future scope: gas reciprocating engines, if the project decides "gas plant" means more than gas turbines

The better structure is:

```text
universal gas-plant concepts
        +
plant-type-specific modules
        +
worked example case studies
```

Athens should remain the first worked example, not the hidden default.

## What We Are Fixing

The current learning docs are strong for the Athens CCGT use case, but several ideas are plant-type dependent:

| Current topic | Why it is plant-type dependent |
| :--- | :--- |
| `00_combined_cycle_plant_anatomy.md` | CCGT-specific anatomy does not apply to simple-cycle GTs. |
| HRSG/ST start costs | Only apply when HRSG/ST equipment exists. |
| HRSG cycling damage | CCGT-specific or CHP-specific; not simple-cycle GT. |
| Shutdown duration thresholds | Hot/warm/cold definitions can vary by OEM, contract, and plant duty. |
| EOH multipliers | LTSA/CSA-specific, not universal physics. |
| Inspection sequence | CI/HGP/MI timing depends on OEM, model, service contract, and operating history. |
| Capacity and heat-rate examples | Athens 7FA CCGT values are useful examples, not universal gas-plant values. |
| Dispatch constraints | Simple-cycle peakers, CCGTs, and CHP assets have different start times, min run, and steam constraints. |
| Outage categories | CCGT has HRSG/ST failure modes that simple-cycle plants do not. |

The fix is not to delete the CCGT content. The fix is to label it correctly and add a plant-type layer above it.

## Core Design Principle

Every learning guide should make this distinction:

```text
Universal concept:
  idea that applies across most gas-fired generation assets

Plant-type variation:
  how the idea changes by simple-cycle, combined-cycle, aero, frame, CHP, etc.

Athens worked example:
  the specific 2x1 GE 7FA CCGT assumptions used in the current framework
```

Example:

```text
Universal:
  Starts consume cost, time, fuel, and maintenance life.

Plant-type variation:
  A simple-cycle GT does not have HRSG/ST start cost.
  A CCGT start also heats HRSG and ST equipment.
  A CHP plant may be constrained by steam-host obligations.

Athens example:
  Hot start = $36K plant total, with GT and HRSG/ST components.
```

## Proposed Folder Structure

Do not immediately rename existing files. That would create link churn. Add the plant-type layer first.

Proposed structure:

```text
docs/
  plans/
    step_2_execution_blueprint_plan.md
  learning/
    plans/
      00_learning_plan.md
      archive_learning_plan_snapshot_2026-04-28_ccgt_focused.md
      01_multi_gas_plant_generalization_plan.md
    basics/
      00_gas_plant_type_map.md
      00_combined_cycle_plant_anatomy.md
      01_capacity.md
      02_heat_rate.md
      03_eoh_and_starts.md
      04_start_costs_and_vom.md
      05_dispatch_and_daily_loop.md
      06_outages_availability_and_ltsa.md
      07_state_vector_and_feedback.md
      08_ltsa_and_service_contracts.md
      09_operating_partitions_and_model_signals.md
    plant_types/
      00_plant_types_index.md
      01_simple_cycle_gt.md
      02_combined_cycle_gt.md
      03_frame_vs_aeroderivative_gt.md
      04_chp_and_cogeneration.md
      05_optional_reciprocating_engines.md
    examples/
      athens_7fa_2x1_ccgt.md
    market_and_operations/
      00_market_and_operations_index.md
      01_operating_range_pmin_pmax.md
      02_marginal_cost_and_offer_curves.md
      03_historical_vs_forecast_inputs.md
      04_weather_adjusted_operating_curves.md
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

Why this structure:

| Folder | Purpose |
| :--- | :--- |
| `basics/` | Universal concepts that almost every gas-plant learner needs. |
| `plant_types/` | Explains how plant anatomy and assumptions change by plant type. |
| `examples/` | Holds specific worked examples, starting with Athens 7FA 2x1 CCGT. |
| `degradation_factors/` | Keeps framework stress/degradation guides, with plant-type applicability notes. |
| `plans/` | Keeps planning history and migration plans separate from finished guides. |

## Plant Types To Support

### 1. Simple-Cycle GT

Also called open-cycle gas turbine in some contexts.

Basic map:

```text
natural gas + air -> GT -> generator -> electricity
                         |
                         v
                       exhaust stack
```

Key differences from CCGT:

| Topic | Simple-cycle GT behavior |
| :--- | :--- |
| HRSG/ST | Not present. |
| Start time | Often faster than CCGT, especially aero units. |
| Heat rate | Usually worse than CCGT but simpler operation. |
| Start cost | GT-only; no HRSG/ST cost bucket. |
| Dispatch role | Peaking, reserves, fast response, high-price hours. |
| Degradation | GT compressor, combustor, TBC, rotor still matter. |

### 2. Combined-Cycle GT

Basic map:

```text
GT -> HRSG -> ST
|              |
v              v
electricity    electricity
```

Key differences:

| Topic | Combined-cycle behavior |
| :--- | :--- |
| HRSG/ST | Present and important. |
| Efficiency | Better heat rate than simple-cycle because waste heat is recovered. |
| Start cost | GT plus HRSG/ST start cost. |
| Dispatch role | Cycling, mid-merit, baseload, or flexible operation depending on market. |
| Degradation | GT and steam-side cycling both matter. |

### 3. Frame GT Vs Aeroderivative GT

This is not exactly plant type; it is turbine technology type.

| Topic | Frame GT | Aeroderivative GT |
| :--- | :--- | :--- |
| Typical role | Large blocks, CCGT or large simple cycle. | Peaking, fast start, flexible duty. |
| Start behavior | Usually slower/heavier thermal mass. | Often faster and more start-capable. |
| Maintenance logic | OEM/service-contract specific. | Often more module-swap style maintenance. |
| Modeling implication | Different start costs, ramp rates, EOH multipliers, inspection logic. | Different start/ramp constraints and maintenance assumptions. |

### 4. CHP / Cogeneration

CHP plants create electricity and useful heat/steam.

```text
GT or boiler system -> electricity
                    -> process steam / heat host
```

Key differences:

| Topic | CHP behavior |
| :--- | :--- |
| Dispatch objective | Not only power price; steam or heat obligation may dominate. |
| Availability | Heat-host reliability may matter as much as electricity revenue. |
| Constraints | Must meet steam demand, pressure, temperature, or host contract. |
| Financial model | Has power revenue plus steam/heat revenue or host penalties. |

### 5. Optional Future: Gas Reciprocating Engines

This should be a scope decision.

Gas reciprocating engines are gas-fired power assets but not gas turbines.

| If included | What changes |
| :--- | :--- |
| Engine starts | Different start wear and maintenance logic. |
| Heat rate | Different efficiency and part-load behavior. |
| Maintenance | Engine overhauls, cylinders, lube oil, spark plugs, etc. |
| Degradation guides | GT-specific TBC, rotor, and hot gas path guides would not apply directly. |

Recommendation: keep this optional until the project decides whether "gas plant" means all gas-fired generation or gas-turbine generation only.

## Standard Plant-Type Note

Each guide should use a short note when assumptions are plant-type dependent.

Standard block:

```text
> Plant-Type Note
> This example uses the Athens 2x1 GE 7FA combined-cycle case.
> The concept is broader, but the numeric values and equipment buckets
> may change for simple-cycle GTs, aeroderivative units, CHP plants,
> or other service-contract structures.
```

Use this note especially in:

- Capacity
- Heat rate
- EOH and starts
- Start costs and VOM
- Dispatch and daily loop
- Outages and LTSA
- HRSG cycling damage
- Rotor life consumption

## Example: Shutdown Duration Thresholds

The current docs use a simple hot/warm/cold classification:

| Start type | Current Athens-style threshold |
| :--- | :--- |
| Hot | Less than 8 hours shutdown |
| Warm | 8 to 72 hours shutdown |
| Cold | More than 72 hours shutdown |

This is useful for learning, but it should be labeled as an example.

Plant-type-aware note:

```text
> Plant-Type Note
> Hot/warm/cold thresholds are not universal. They can depend on OEM,
> turbine model, thermal mass, service contract, plant configuration,
> and how the operator defines shutdown state. Use the Athens thresholds
> as the worked example, not as a universal rule.
```

Why this matters:

| Plant or contract difference | Possible effect |
| :--- | :--- |
| Aeroderivative GT | May cool differently and have different start categories. |
| Large frame CCGT | HRSG/ST warm-up can matter as much as GT shutdown duration. |
| CHP plant | Steam-host constraints may define restart economics differently. |
| OEM LTSA | Contract may define start classes differently from engineering intuition. |

## Degradation Factor Applicability Matrix

The degradation guides should include an applicability table.

Draft matrix:

| Degradation factor | Simple-cycle GT | CCGT | CHP / cogeneration | Notes |
| :--- | :---: | :---: | :---: | :--- |
| EOH accumulation with creep-fatigue coupling | Yes | Yes | Yes | GT-specific logic, contract-specific values. |
| Capacity derating from ambient temperature | Yes | Yes | Yes | Curves differ by equipment and cooling systems. |
| Heat rate degradation | Yes | Yes | Yes | CCGT includes steam-cycle effects; simple-cycle does not. |
| Combustion cycling fatigue | Yes | Yes | Yes | GT combustor topic. |
| HRSG cycling damage | No | Yes | Maybe | Applies when HRSG or steam generator exists. |
| Compressor degradation | Yes | Yes | Yes | GT compressor topic. |
| Thermal barrier coating life | Yes | Yes | Yes | GT hot-section topic, if applicable to machine design. |
| Rotor life consumption | Yes | Yes | Yes | GT rotor topic; ST/generator rotors are separate. |

This matrix should appear in `00_gas_plant_type_map.md` and be summarized in each relevant degradation guide.

## Guide-by-Guide Migration Plan

### Phase 1: Planning And Guardrails

Status: this file.

Tasks:

- Create `docs/learning/plans/`.
- Archive current `00_learning_plan.md`.
- Create this plant-type generalization plan.
- Do not rewrite all guides yet.

### Phase 2: Add The Plant-Type Map

Create:

```text
docs/learning/basics/00_gas_plant_type_map.md
```

Status: implemented.

It should explain:

- Simple-cycle GT
- Combined-cycle GT
- Frame vs aeroderivative GT
- CHP / cogeneration
- Optional gas reciprocating engine scope
- Which current learning docs are universal vs CCGT-specific
- How the Athens CCGT example should be interpreted

Follow-on status: `docs/learning/plant_types/01_simple_cycle_gt.md` is implemented as the first detailed non-CCGT plant-type guide. `docs/learning/plant_types/02_combined_cycle_gt.md` is also implemented so the CCGT material now has a plant-type home instead of living only in the anatomy guide.

### Phase 3: Reframe The Existing Anatomy Guide

Current file:

```text
docs/learning/basics/00_combined_cycle_plant_anatomy.md
```

Status: initial top note implemented. Deeper reframing can happen later if needed.

Do not pretend this is the universal anatomy guide. Add a top note:

```text
This guide is specifically about combined-cycle plant anatomy.
For the broader gas-plant type map, read 00_gas_plant_type_map.md first.
```

The plant-type guide now exists at:

```text
docs/learning/plant_types/02_combined_cycle_gt.md
```

### Phase 4: Add Plant-Type Notes To Basics

Patch each basics guide with short notes:

| File | Needed note |
| :--- | :--- |
| `01_capacity.md` | Done: added plant-type note, `Pmax/Pmin` framing, plant-type variation table, and Athens worked-example language. |
| `02_heat_rate.md` | Done: added plant-type note, average vs incremental heat-rate framing, plant-type variation table, and Athens worked-example language. |
| `03_eoh_and_starts.md` | Done: added plant-type note and variation table for start classes, EOH multipliers, OEM/contract thresholds, and Athens assumptions. |
| `04_start_costs_and_vom.md` | Done: added plant-type note and variation table clarifying HRSG/ST costs apply only where steam-side equipment exists. |
| `05_dispatch_and_daily_loop.md` | Done: added plant-type note and variation table for simple-cycle, CCGT, frame, aero, and CHP dispatch constraints. |
| `06_outages_availability_and_ltsa.md` | Done: added plant-type note and variation table for outage categories, coverage, partial operation, and CHP service obligations. |
| `07_state_vector_and_feedback.md` | Done: added plant-type note and variation table showing how state schema changes by plant type. |

### Phase 5: Add Plant-Type Notes To Degradation Guides

Patch each degradation guide with applicability notes.

Priority:

| Priority | File | Why |
| :--- | :--- | :--- |
| 1 | `05_hrsg_cycling_damage.md` | Most clearly CCGT-specific. |
| 2 | `02_capacity_derating.md` | Curves differ materially by plant type and inlet/cooling system. |
| 3 | `03_heat_rate_degradation.md` | CCGT, simple-cycle, and CHP heat-rate logic differ. |
| 4 | `06_compressor_degradation.md` | Broadly GT-applicable, but recovery/wash assumptions differ. |
| 5 | `07_tbc_life.md` | Applies to GT hot-section designs but not every gas-fired asset. |
| 6 | `08_rotor_life_consumption.md` | GT rotor, ST rotor, and generator rotor must stay separated. |

Status: implemented initial plant-type applicability notes in all eight degradation-factor guides. The HRSG guide now explicitly says it does not apply to simple-cycle GTs without steam-side equipment.

### Phase 6: Create Athens As A Case Study

Create:

```text
docs/learning/examples/athens_7fa_2x1_ccgt.md
```

Status: implemented as the first worked-example case-study file.

This should collect all Athens-specific assumptions in one place:

- GE 7FA combined-cycle framing
- 2x1 configuration
- Capacity table
- Heat-rate baseline
- EOH starting state
- CI/HGP/MI thresholds
- Start cost table
- LTSA assumptions
- Degradation starting states
- What is known vs assumed

Then the basics guides can say:

```text
For the Athens worked example, see examples/athens_7fa_2x1_ccgt.md.
```

## Strict Migration Guardrails

This migration should be treated as a careful architecture change, not a quick cleanup.

Rules:

- Do not remove the Athens CCGT content. Re-label it as a worked example.
- Do not present Athens values as universal gas-plant rules.
- Do not rewrite many files in one pass without a clear scope and verification checklist.
- Do not split every guide by plant type unless the content truly becomes different enough to justify separate files.
- Do not add new numeric assumptions unless the guide clearly labels the source and applicability.
- Do not mix engineering degradation, dispatch optimization, and offer-curve construction without explaining which layer is being discussed.
- Do not treat contract terms as physics. Hot/warm/cold thresholds, EOH multipliers, starts, and overage charges can be OEM/contract-specific.
- Do not treat historical operating ranges as forecasts unless a future-weather or future-market input is actually used.
- Do not treat simple-cycle, CCGT, aeroderivative, frame, CHP, and reciprocating-engine concepts as interchangeable.

Migration discipline:

```text
read current guide
  |
  v
identify universal concept vs plant-type-specific assumption
  |
  v
add plant-type note or variation table
  |
  v
preserve Athens as worked example
  |
  v
verify links, examples, ASCII, and wording
```

## External Plant Model Reference Reviewed

Local reference reviewed:

```text
/Users/divy/code/personal/other/gas-to-power/code/plant model
```

Relevant files:

| File | Useful idea for this migration |
| :--- | :--- |
| `production_planning_simple_plant_model.md` | General gas-generator offer-curve pipeline: data collection, heat-rate curve fitting, marginal cost, Pmin/Pmax, offer blocks, validation, and later operational constraints. |
| `pminimum_pmaximum.md` | Robust monthly Pmin/Pmax estimation using operating data percentiles and smoothing. |
| `offer_curve_info/OFFER_CURVE_STEP_VS_LINEAR.md` | Step vs piecewise-linear offer curve framing and guardrails around monotonic MW/price blocks. |
| `weather_effects/implementing_weather_adjustments_for_gas_plants.md` | Intuitive weather-adjustment workflow for `Pmax(T)`, `Pmin(T)`, and heat-rate sensitivity. |
| `weather_effects/weather_impact_study.md` | Research plan for weather, air density, temperature envelopes, and backtesting weather-adjusted offers. |
| `FILTERING_GUIDE.md` | Data-quality discipline for fitting plant curves from noisy operating data. |
| `is_it_forecasted.md` | Clear distinction between historical performance model, user-provided inputs, and true forecasting. |

Key lessons to import into the learning docs:

| Lesson | Why it matters |
| :--- | :--- |
| Pmin/Pmax are first-class plant constraints. | Capacity is not only maximum MW; minimum stable output also matters for dispatch and offers. |
| Historical operating envelopes are not forecasts. | A monthly Pmax/Pmin range from history is useful but should not be labeled as future forecast unless weather/market forecasts are used. |
| Weather can affect both Pmax and heat rate. | The current capacity and heat-rate guides should eventually discuss `Pmax(T)`, `Pmin(T)`, and heat-rate correction as general methods. |
| Offer curves are a separate market-output layer. | Dispatch economics and market offer construction are related but not identical. |
| Data filtering matters. | Heat-rate and capacity curves built from CEMS-like data need clear filters, outlier handling, and diagnostics. |
| Operational constraints belong in the roadmap. | Ramp rates, min up/down, start time, and min load can change real dispatch and offers. |

These lessons should inform future docs, but they should not be copy-pasted blindly. The external plant model appears focused on gas-generator offer curves and historical operating data; the InfraSure learning docs also cover degradation, LTSA, forced outages, and investment risk.

## Additional Learning Layer: Market And Operating Curves

The current learning tree has basics, plant types, examples, and degradation factors. The external plant-model docs suggest a fifth layer may be useful later:

```text
market_and_operations/
  01_operating_range_pmin_pmax.md
  02_marginal_cost_and_offer_curves.md
  03_historical_vs_forecast_inputs.md
  04_weather_adjusted_operating_curves.md
```

Recommended scope:

| Candidate guide | Purpose |
| :--- | :--- |
| `01_operating_range_pmin_pmax.md` | Explain Pmin/Pmax, min stable load, max capability, monthly ranges, and weather-dependent envelopes. |
| `02_marginal_cost_and_offer_curves.md` | Explain heat-rate curves, incremental heat rate, gas price, VOM, step offers, and linear offers. |
| `03_historical_vs_forecast_inputs.md` | Explain what is historical calibration, what is user input, and what is true forecasting. |
| `04_weather_adjusted_operating_curves.md` | Explain `Pmax(T)`, `Pmin(T)`, `HR(T)`, temperature bins, and backtesting. |

Status: initial index implemented at `docs/learning/market_and_operations/00_market_and_operations_index.md`. The first four detailed guides are implemented:

- `docs/learning/market_and_operations/01_operating_range_pmin_pmax.md`
- `docs/learning/market_and_operations/02_marginal_cost_and_offer_curves.md`
- `docs/learning/market_and_operations/03_historical_vs_forecast_inputs.md`
- `docs/learning/market_and_operations/04_weather_adjusted_operating_curves.md`

The next likely market/operations guide is `05_dispatch_constraints.md`, if ramp limits, minimum up/down time, start time, and unit-commitment feasibility become the next priority.

## Implications For Existing Basics Guides

The external plant model changes how we should eventually improve several current basics guides.

| Existing guide | Future improvement |
| :--- | :--- |
| `01_capacity.md` | Add Pmax/Pmin distinction, not just net maximum capacity. Add plant-type note for simple-cycle, CCGT, aero, frame, and CHP. |
| `02_heat_rate.md` | Add average vs incremental heat rate distinction more explicitly, and connect incremental heat rate to marginal cost / offer curves. |
| `04_start_costs_and_vom.md` | Clarify which costs affect dispatch vs offer construction vs contract cashflow. |
| `05_dispatch_and_daily_loop.md` | Add a note that offer curves, unit commitment, and dispatch are related but not the same layer. |
| `07_state_vector_and_feedback.md` | Add possible state variables for Pmin/Pmax, ramp rate, min up/down, and offer-curve mode if the model uses market bidding outputs. |

This should be a second-stage improvement after the plant-type map is created.

## What Not To Do Yet

Do not immediately split every file into many plant-type versions. That would make the docs harder to maintain.

Avoid this structure for now:

```text
capacity_simple_cycle.md
capacity_combined_cycle.md
capacity_chp.md
heat_rate_simple_cycle.md
heat_rate_combined_cycle.md
...
```

Instead, keep one concept guide and add:

- Universal explanation
- Plant-type variation table
- Athens worked example
- Open questions

Split into separate files only when the content becomes too different to explain cleanly in one guide.

## Standard Section To Add Where Needed

Use this section title in future edits:

```text
## Plant-Type Variations
```

Recommended table:

| Plant type | What stays the same | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | GT concept still applies. | No HRSG/ST; start and heat-rate logic differ. |
| Combined-cycle GT | GT concept plus steam cycle. | HRSG/ST costs, constraints, and damage apply. |
| Aeroderivative GT | GT concept still applies. | Faster start/ramp and maintenance assumptions may differ. |
| CHP | GT/steam concepts may apply. | Steam-host constraints can dominate dispatch. |

## Test Plan For The Migration

After each migration edit:

- Confirm the file still teaches the original concept clearly.
- Confirm Athens values are labeled as worked-example assumptions.
- Confirm plant-type-specific assumptions are not presented as universal rules.
- Confirm all links still work.
- Confirm tables remain readable in plain text.
- Confirm ASCII-only text unless a source title requires otherwise.

Specific checks:

```text
rg -n "Plant-Type Note|Plant-Type Variations|Athens" docs/learning
LC_ALL=C rg -n "[^ -~]" docs/learning
```

## Open Decisions

Before implementing the full migration, decide:

| Decision | Options | Recommendation |
| :--- | :--- | :--- |
| Scope of "gas plant" | Gas turbines only vs all gas-fired generation | Start with gas turbines; keep reciprocating engines optional. |
| Rename existing CCGT anatomy file? | Rename now vs keep path and add notes | Keep path for now to avoid link churn. |
| New folder name | `plant_types` vs `asset_types` | Use `plant_types`; clearer for learners. |
| Athens case study location | `examples/` vs `plant_types/` | Use `examples/`; Athens is a case, not a type. |
| How much to rewrite now | Big bang vs incremental notes | Incremental notes; preserve momentum and readability. |

## Recommended Next Step

The broad map, CCGT anatomy note, basics plant-type notes, degradation applicability notes, Athens example, and initial `plant_types` / `market_and_operations` indexes are now in place.

Next, choose one detailed follow-on guide:

- `docs/step_2_execution_blueprint/00_index.md` if the next priority is beginning the execution-blueprint folder;
- `docs/step_2_execution_blueprint/01_time_resolution_and_frequency.md` if the next priority is resolving hourly, daily, monthly, and annual frequency choices;
- `market_and_operations/05_dispatch_constraints.md` if ramp limits, min up/down, start time, and unit-commitment feasibility are the next priority;
- a deeper pass on any existing guide if the current Athens CCGT docs need more beginner grounding.
