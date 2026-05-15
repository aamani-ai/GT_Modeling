# Athens 7FA 2x1 CCGT Worked Example

## What This File Is

This file collects the Athens-specific assumptions used across the learning docs.

Read these first if the plant type is still unclear:

- [Gas Plant Type Map](../basics/00_gas_plant_type_map.md)
- [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md)

> Plant-Type Note
> Athens is the first worked example, not the universal gas-plant rule. It is a GE 7FA 2x1 combined-cycle case. Do not copy its HRSG/ST costs, EOH thresholds, capacity curve, start classes, or degradation starting states into a simple-cycle GT, aeroderivative GT, CHP plant, or gas reciprocating engine without plant-specific review.

The purpose is to make examples concrete:

```text
universal concept
        |
        v
plant-type variation
        |
        v
Athens 7FA 2x1 CCGT worked assumption
```

## Plant Identity

| Item | Athens worked-example value |
| :--- | :--- |
| Asset type | Combined-cycle gas turbine plant |
| Configuration | 2 GTs, 2 HRSGs, 1 ST |
| Short name | 2x1 CCGT |
| GT model | GE 7FA.03 x 2 |
| Market / location context | NYISO Zone F / Hudson Valley |
| Cooling assumption | Mechanical draft cooling towers |
| Starting model state | Just after Hot Gas Path inspection |
| Primary use in docs | First concrete case for capacity, heat rate, starts, LTSA, dispatch, and degradation |

## Configuration Map

```text
          natural gas + air
                 |
        +--------+--------+
        |                 |
        v                 v
      GT-A              GT-B
        |                 |
        | hot exhaust     | hot exhaust
        v                 v
     HRSG-A            HRSG-B
        |                 |
        +--------+--------+
                 |
                 v
                ST
                 |
                 v
            electricity
```

Important modeling consequence:

```text
2x1 mode = both GT/HRSG trains plus shared ST
1x1 mode = one GT/HRSG train plus partial steam-cycle contribution
```

That means some costs and state variables may need train-level tracking:

| State area | Why train-level tracking can matter |
| :--- | :--- |
| GT-A and GT-B EOH | One GT can run or start more often than the other. |
| Compressor fouling | One GT may foul or be washed at a different time. |
| HRSG-A and HRSG-B cycles | 1x1 operation can cycle one HRSG more than the other. |
| Rotor and hot-section condition | Start-stop exposure can diverge by GT. |

## Performance Assumptions

### Capacity

The pilot `Pmax` style capacity curve is:

| Ambient temperature | GT output, each | ST output | Net plant capacity | Framework delta label |
| :--- | ---: | ---: | ---: | :--- |
| 0 deg F | 185 MW | 195 MW | 565 MW | +4.6% |
| 20 deg F | 180 MW | 192 MW | 552 MW | +2.2% |
| 59 deg F ISO | 171 MW | 189 MW | 531 MW | baseline |
| 80 deg F | 159 MW | 181 MW | 499 MW | -7.6% |
| 95 deg F | 148 MW | 173 MW | 469 MW | -13.1% |

Learning note:

```text
ISO capacity = clean reference condition
hot-day capacity = weather-adjusted dispatch cap
effective capacity = weather + degradation + outage condition
```

ASCII view:

```text
Net plant capacity

565 MW |*  0 deg F
552 MW |  * 20 deg F
531 MW |       * 59 deg F ISO
499 MW |              * 80 deg F
469 MW |                    * 95 deg F
       +--------------------------------
        cold       ISO        hot
```

### Heat Rate

| Condition | Heat rate | Notes |
| :--- | ---: | :--- |
| Post-HGP baseline at ISO | 7,070 Btu/kWh | Starting heat-rate baseline in the model. |
| At 90 deg F ambient | 7,230 Btu/kWh | Hot-weather correction worsens performance. |
| At 50% minimum load, ISO | 8,215 Btu/kWh | Part-load operation is less efficient. |
| Heat-rate guarantee | Within 2.0% of 7,070 Btu/kWh | Contract-style performance threshold. |

Fuel-cost example:

```text
7,070 Btu/kWh = 7.070 MMBtu/MWh
Gas price = $4.00/MMBtu

Fuel cost = 7.070 * 4.00
Fuel cost = $28.28/MWh
```

## Contract And Inspection Assumptions

The Athens case uses a GE CSA-style contract assumption.

| Item | Worked-example assumption |
| :--- | :--- |
| Contract type | GE Contractual Service Agreement, comprehensive style |
| Units covered | GT-A and GT-B |
| Billing structure | Fixed monthly base plus variable EOH reserve |
| Fixed base fee | $850,000/month |
| Variable EOH reserve | $175/EOH accrued |
| LTSA VOM portion | $1.50/MWh dispatched |
| Availability guarantee | 95.0%, excluding planned outages |
| Heat-rate guarantee | Within 2.0% of 7,070 Btu/kWh |

Inspection timing:

| Event | EOH trigger | EOH from starting state | Outage duration | Owner / OEM cost warning |
| :--- | ---: | ---: | :--- | :--- |
| CI | 32,000 | 8,000 | 10 to 15 days | Cost split is contract-specific. |
| CI | 40,000 | 16,000 | 10 to 15 days | Cost split is contract-specific. |
| MI | 48,000 | 24,000 | 45 to 60 days | Major owner exposure can remain. |

Starting EOH state:

```text
GT-A EOH = 24,000
GT-B EOH = 24,000
next CI  = 32,000
headroom = 8,000 EOH
```

## EOH And Start-Type Assumptions

The Athens-style start classes are:

| Start type | Shutdown definition | EOH impact per GT |
| :--- | :--- | ---: |
| Hot | Less than 8 hours | 50 |
| Warm | 8 to 72 hours | 150 |
| Cold | More than 72 hours | 350 |
| Emergency trip | Forced shutdown from full load | 500 |
| Large load swing | Greater than 40% rated | 0.3 per swing cycle |

ASCII view:

```text
Shutdown duration

0 hr             8 hr                         72 hr
 |---------------|-----------------------------|
      hot start            warm start              cold start

Athens-style example only.
```

Why this matters:

```text
hourly dispatch
  -> starts, trips, fired hours, load swings
  -> EOH added today
  -> inspection headroom tomorrow
  -> dispatch economics tomorrow
```

## Start Cost Assumptions

### GT Start Costs

| Start type | GT fuel | GT wear | GT aux | GT subtotal | EOH charged per GT |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Hot | $12K | $15K | $3K | $30K | 50 |
| Warm | $22K | $45K | $5K | $72K | 150 |
| Cold | $35K | $105K | $8K | $148K | 350 |
| Trip | $0K | $150K | $10K | $160K | 500 |

### HRSG/ST Start Costs

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

Key warning:

```text
HRSG/ST start cost only applies because Athens is a CCGT.
Simple-cycle GT = no HRSG/ST cost bucket.
```

## Overage Assumptions

| Start type | Annual contracted limit | Overage charge per excess event |
| :--- | ---: | ---: |
| Hot | 150 starts/yr | $8,500 |
| Warm | 35 starts/yr | $42,000 |
| Cold | 5 starts/yr | $125,000 |
| Emergency trip | 3 events/yr | $80,000 |

This is not the same thing as start cost:

```text
start cost = modeled cost each time the plant starts
overage charge = contract charge after annual limit is exceeded
```

## Degradation Starting State

| State variable | Starting value | Meaning |
| :--- | :--- | :--- |
| Contractual EOH, GT-A | 24,000 | HGP just completed. |
| Contractual EOH, GT-B | 24,000 | HGP just completed. |
| Creep damage fraction | 0.0 | Reset at HGP in the framework. |
| Fatigue damage fraction | 0.0 | Reset at HGP in the framework. |
| ISO heat rate | 7,070 Btu/kWh | Includes non-recoverable age degradation. |
| Recoverable heat-rate degradation | 0.0% | Reset at HGP. |
| Compressor fouling index | 0.0% | Washed during HGP outage. |
| Compressor fouling model | A=2.5%, tau=1000h | Humid coastal / Hudson Valley class. |
| Compressor erosion | +1.8% HR penalty | Long-term non-recoverable degradation. |
| TBC time-at-temperature | 0.0 hours | New/refurbished blades at HGP. |
| TBC failure threshold | Sampled per path | beta=3.0, eta=28,000 equivalent fired hours. |
| HRSG drum cycle count | 0.0 | Reset for tracking interval. |
| HRSG drum fatigue life fraction | About 0.30 | Estimated cumulative from prior service. |
| Rotor life fraction consumed | About 0.35 | Estimated prior service tail-risk state. |
| Hours since last shutdown | 720+ hours | Cold state after HGP outage. |

## Daily Loop Example

Assume one Athens dispatch day:

| Item | Value |
| :--- | ---: |
| Fired hours | 8 |
| Start type | Hot |
| Large load swings | 0 |
| Opening EOH | 24,000 |

EOH update:

```text
fired-hour EOH = 8
hot-start EOH  = 50
load swings    = 0

daily EOH added = 8 + 50 + 0
daily EOH added = 58

closing EOH = 24,000 + 58
closing EOH = 24,058
```

Inspection headroom:

```text
opening headroom = 32,000 - 24,000 = 8,000 EOH
closing headroom = 32,000 - 24,058 = 7,942 EOH
```

That is the central feedback idea:

```text
today's dispatch -> today's EOH/degradation -> tomorrow's economics
```

## What Is Athens-Specific

| Athens-specific item | Why it should not be generalized blindly |
| :--- | :--- |
| 2x1 CCGT equipment stack | Simple-cycle plants do not have HRSG/ST costs or damage. |
| GE 7FA.03 model | Other OEMs and machines have different curves and contracts. |
| Capacity table | Site, ambient correction, cooling, and degradation are asset-specific. |
| 7,070 Btu/kWh baseline | Heat-rate test basis and plant condition are asset-specific. |
| CI/HGP/MI thresholds | Contract and OEM maintenance program define timing. |
| Start EOH multipliers | Contract/OEM assumptions, not universal physics. |
| Availability and heat-rate guarantees | Negotiated contract terms. |
| Degradation starting states | Due-diligence assumptions pending plant records. |

## What Is General

| General concept | Why it transfers |
| :--- | :--- |
| Capacity affects revenue opportunity. | Every dispatch model needs feasible MW. |
| Heat rate affects fuel cost. | Every fuel-fired plant needs marginal fuel economics. |
| Starts consume cost and life. | Every thermal plant has start economics, even if the buckets differ. |
| Outages block or derate dispatch. | Availability matters across plant types. |
| State feedback matters. | Operation today changes tomorrow's plant condition. |
| Plant-type applicability matters. | Equipment present decides which variables belong in the model. |

## Source Basis And Uncertainty

| Source | Use in this file | Certainty |
| :--- | :--- | :--- |
| `docs/InfraSure_ModelingFramework_V2.md`, Section 4 | Athens pilot identity, capacity, heat rate, CSA, start cost, and state assumptions. | Green for local framework values; Amber for asset-specific investment use. |
| `docs/learning/basics/01_capacity.md` | Beginner capacity framing and capacity table. | Amber until reconciled with actual plant/OEM data. |
| `docs/learning/basics/02_heat_rate.md` | Heat-rate framing and fuel-cost examples. | Green for concept; Amber for plant-specific values. |
| `docs/learning/basics/03_eoh_and_starts.md` | EOH and start-class explanations. | Amber because contract terms must be verified. |
| `docs/learning/basics/04_start_costs_and_vom.md` | Start cost and VOM split. | Amber because cost values are assumptions. |
| `docs/learning/degradation_factors/` | Degradation starting-state interpretation. | Amber to Red depending on factor calibration. |

## Open Questions Before Investment Use

| Question | Why it matters |
| :--- | :--- |
| Are the actual CSA/LTSA terms available? | Replaces assumed EOH, overage, coverage, and guarantee values. |
| Are GT-A and GT-B EOH histories separate and verified? | Prevents false symmetry in a 2x1 plant. |
| Are actual performance test records available? | Validates capacity and heat-rate baselines. |
| Are compressor wash and inspection records available? | Improves fouling, erosion, and heat-rate recovery assumptions. |
| Are HRSG inspection findings available? | Validates the 0.30 HRSG fatigue-life assumption. |
| Is there an OEM rotor life assessment? | Validates the 0.35 rotor-life assumption and tail-risk treatment. |
| How should 1x1 operation be represented in dispatch? | Affects start costs, capacity blocks, and train-level damage. |
| Which values are guaranteed, assumed, or sensitivity-only? | Prevents investment outputs from overclaiming precision. |

## Quick Recap

Athens is useful because it gives concrete numbers for learning.

```text
Use Athens to understand the model.
Do not treat Athens as every gas plant.
```
