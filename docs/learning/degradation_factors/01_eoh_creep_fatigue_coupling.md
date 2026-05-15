# EOH Accumulation With Creep-Fatigue Coupling

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read this basics guide first if EOH is new: [EOH And Starts](../basics/03_eoh_and_starts.md).

> Plant-Type Applicability
> This is mainly a GT hot-section and contract-life concept. It can apply to simple-cycle GTs, CCGTs, and GT-based CHP plants, but the actual EOH multipliers, inspection thresholds, and creep-fatigue calibration are OEM-, machine-, duty-, and contract-specific. It does not directly apply to gas reciprocating engines without a different engine-life model.

## First-Time Reader Map

If this topic is new, start with the two different questions being asked:

```text
Contract question:
  When does the service agreement say inspection or billing is due?

Engineering question:
  How much physical damage did the hot parts actually consume?
```

The guide uses several terms that can sound similar but mean different things:

| Term | First-time meaning |
| :--- | :--- |
| EOH | Equivalent Operating Hours, the contract-style life counter. |
| Contractual EOH | EOH used for LTSA/CSA inspection timing, reserve billing, and dispatch penalties. |
| Physical damage | Engineering estimate of actual component life consumed. |
| Creep | Slow high-temperature damage from holding hot stressed metal in service. |
| Fatigue | Repeated-cycle damage from starts, trips, ramps, and load swings. |
| Creep-fatigue coupling | The idea that creep and fatigue together can be worse than treating them separately. |
| Damage fraction | A simplified 0-to-1 style life-consumption measure. |
| Interaction envelope | The allowed combined creep and fatigue region. |
| Hot gas path | GT parts exposed to hot combustion gas, such as turbine blades, vanes, shrouds, and related hardware. |
| Forced outage risk | Probability that damage state contributes to unexpected unavailability. |

The mental stack is:

```text
dispatch today -> contract EOH + physical damage -> inspection timing + outage risk
```

## The Basic Problem Before The Math

A gas turbine can age in two ways at the same time.

```text
Running hot for many hours
  -> creep pressure

Starting, stopping, tripping, and ramping
  -> fatigue pressure
```

The contract needs a simple auditable counter, so it uses EOH. Engineering risk needs a stress view, so the framework also tracks physical damage.

That means one day of operation can create two different signals:

| Signal | What it tells you | Example |
| :--- | :--- | :--- |
| Contractual EOH | How much contract maintenance life was used. | A hot start adds 50 EOH. |
| Physical creep-fatigue damage | How much component stress was created. | A hot loaded run plus cycling raises damage state. |

The first signal helps schedule and bill maintenance. The second signal helps explain hidden forced-outage risk between scheduled inspections.

## Two Meters, Not One Meter

Think of the model as carrying two meters.

```text
Contract meter:
  fired hours + starts + trips -> EOH -> CI/HGP/MI timing

Physics meter:
  temperature + stress + cycles -> creep + fatigue -> forced outage risk
```

These meters usually move together, but not always at the same speed.

Example:

```text
Two plants can have similar EOH.
One plant ran steady.
The other plant cycled hard with many starts and trips.
The cycled plant can carry more physical damage risk.
```

That is why this guide exists. It explains why EOH is necessary but not enough.

## Where This Sits In The Learning Path

The basics guide [EOH And Starts](../basics/03_eoh_and_starts.md) explains the contract counter. This guide adds the physical-damage layer.

```text
Basics:
  starts and fired hours -> EOH

This guide:
  EOH plus operating severity -> creep-fatigue damage state
```

For investment modeling, both views matter:

| View | Financial use |
| :--- | :--- |
| Contractual EOH | Inspection timing, LTSA reserve, start overage economics. |
| Physical damage | Forced outage probability, downside risk, conservative dispatch logic. |

## Why This Matters

This degradation factor answers a more advanced version of the EOH question:

> Did today's operation consume contract maintenance life, physical component life, or both?

The framework does not treat EOH as only an accounting number. It keeps two related but different views of life consumption:

| View | Plain-English meaning | Main model use |
| :--- | :--- | :--- |
| Contractual EOH | The LTSA/CSA maintenance-life counter. | Inspection timing, billing, EOH reserve, start overage economics. |
| Physical creep-fatigue damage | The engineering estimate of actual hot-section damage. | Forced outage risk, stress state, warning that the plant may be riskier before the next scheduled inspection. |

This matters financially because a plant can look acceptable on the LTSA clock while its physical stress state is getting worse. A heavily cycled gas turbine can accumulate damage from hot operation, starts, trips, and load swings before the next formal inspection threshold arrives.

```text
Contractual view:
dispatch -> fired hours + starts + trips -> EOH -> inspection timing

Physical view:
dispatch -> temperature + load + cycles -> creep + fatigue -> outage risk
```

The key idea: EOH tells us when the contract says maintenance is due. Creep-fatigue coupling helps estimate whether the equipment is physically becoming fragile between those scheduled events.

## Plain-English Concept

This guide has four terms to learn.

| Term | Beginner meaning | Gas turbine example |
| :--- | :--- | :--- |
| EOH | A common life counter that converts hours, starts, trips, and cycling into equivalent maintenance hours. | One hot start may count like many fired hours. |
| Creep | Slow damage from high temperature and stress over time. | Blades and vanes spend hours at high metal temperature while the GT is loaded. |
| Fatigue | Damage from repeated cycling. | Starts, stops, trips, ramps, and large load swings bend hot-section parts through thermal stress cycles. |
| Coupling | Creep and fatigue make each other worse when they act together. | A component that is both hot for many hours and cycled frequently can fail earlier than independent checks imply. |

Beginner analogy:

```text
Creep   = slow stretching from holding a hot loaded condition.
Fatigue = bending from repeated starts, stops, and ramps.
Coupling = hot material that is also repeatedly bent can lose life faster.
```

The coupling part is the important upgrade. The framework says creep and fatigue should not be treated as two independent meters where each is safe as long as it is below 100%. Instead, the combined state is checked against an interaction envelope.

## What Parts Of The Plant This Is About

This first degradation guide is mainly about the gas turbine hot gas path.

| Component area | Why it is exposed |
| :--- | :--- |
| Turbine blades and vanes | High temperature, high stress, thermal cycling. |
| Combustion liners and transition pieces | Strong thermal gradients during starts, trips, and load changes. |
| Hot gas path seals and shrouds | Heat exposure and cyclic clearances. |
| Rotor-related hot-section interfaces | Start-stop thermal transients plus hours at speed. |

The HRSG and steam turbine also have cycling damage, but the framework separates that into a later guide: [HRSG cycling damage](./05_hrsg_cycling_damage.md). This guide stays focused on GT EOH and GT hot-section creep-fatigue coupling.

## Contractual EOH Vs Physical Damage

This split is the heart of the method.

### Contractual EOH

Contractual EOH is the service-contract counter. It is practical, auditable, and tied to LTSA/CSA terms.

The Athens-type assumptions use these counting rules:

| Operation | Contractual EOH impact |
| :--- | ---: |
| Fired hour on natural gas at base load | 1.0 EOH/hr |
| Hot start | 50 EOH per start |
| Warm start | 150 EOH per start |
| Cold start | 350 EOH per start |
| Emergency trip from full load | 500 EOH per event |
| Load swing greater than 40% rated | 0.3 EOH per swing cycle |

This counter drives questions like:

- How close are we to the next CI, HGP, or MI?
- How much EOH reserve should be accrued?
- Are we above contracted start limits?
- Should Step 2 dispatch self-curtail near a maintenance threshold?

### Physical Damage

Physical damage is the engineering stress estimate. It asks:

```text
Given the actual load, temperature, fired hours, starts, trips, and swings,
how much hot-section life did the equipment consume today?
```

The framework tracks:

| Damage type | Simple driver | Framework method |
| :--- | :--- | :--- |
| Creep damage, `D_c` | Time at high effective metal temperature and stress. | Robinson life-fraction rule using rupture life estimates. |
| Fatigue damage, `D_f` | Number and severity of starts, trips, ramps, and load swings. | Miner's rule applied to simplified cycle counting. |
| Coupled damage | Creep and fatigue together. | Interaction envelope, not independent pass/fail checks. |

The two clocks can diverge:

```text
Contractual EOH may say:  still below CI threshold
Physical damage may say:  combined damage is already in a high-risk region
```

That divergence is exactly why the framework keeps both.

## Why Creep Happens

Creep is time-dependent damage. It matters when a metal component is held at high temperature and stress.

For a GT hot gas path, the model logic is:

```text
more fired hours at high load
        +
higher effective metal temperature
        v
faster creep life consumption
```

The framework uses a Robinson life-fraction idea:

```text
D_c = sum(delta_t_i / t_r(T_i, sigma_i))
```

Plain-English translation:

| Term | Meaning |
| :--- | :--- |
| `D_c` | Cumulative creep damage fraction. |
| `delta_t_i` | Time spent at operating condition `i`. |
| `T_i` | Effective metal temperature at that condition. |
| `sigma_i` | Stress at that condition. |
| `t_r` | Estimated rupture life at that temperature and stress. |

If the component spends more time at a hotter, more stressful condition, the daily creep increment is larger.

## Why Fatigue Happens

Fatigue is cycle-dependent damage. It grows when the equipment is repeatedly heated, cooled, loaded, unloaded, tripped, or ramped.

Beginner version:

```text
steady hot operation -> mostly creep
starts and trips     -> mostly fatigue
large load swings    -> partial fatigue cycles
```

The framework uses Miner's rule for fatigue:

```text
D_f = sum(n_j / N_f(delta_epsilon_j))
```

Plain-English translation:

| Term | Meaning |
| :--- | :--- |
| `D_f` | Cumulative fatigue damage fraction. |
| `n_j` | Number of cycles of type `j`. |
| `N_f` | Estimated allowable cycles before failure at that cycle severity. |
| `delta_epsilon_j` | Strain range, or how severe the cycle is. |

For learning, think of the fatigue severity ranking like this:

| Event type | Relative fatigue intuition |
| :--- | :--- |
| Hot start | Lower thermal change; reference start event. |
| Warm start | More cooling has occurred; higher thermal stress. |
| Cold start | Largest normal thermal change; high stress. |
| Emergency trip | Severe transient; high fatigue and outage relevance. |
| Large load swing | Partial cycle; smaller than a full start but can add up. |

## The Coupling Problem

The framework's critical design decision is that creep and fatigue are not independent.

An independent check would ask:

```text
Is D_c below 1.0?  yes
Is D_f below 1.0?  yes
Then the component is okay.
```

The coupled check asks a stricter question:

```text
Is D_c + D_f still inside the allowed interaction envelope?
```

Framework form:

```text
D_c + D_f <= D_interaction
```

Where `D_interaction` is:

| Region | Framework value | Meaning |
| :--- | :--- | :--- |
| One damage mechanism dominates | About 1.0 | Mostly creep or mostly fatigue; less interaction penalty. |
| Mixed creep and fatigue region | 0.60 to 0.80 | Both mechanisms matter; allowed combined damage is lower. |

ASCII view:

```text
Fatigue damage, D_f

1.0 |\
    | \
0.8 |  \      independent thinking says much of this area is okay
    |   \
0.6 |----\    coupled envelope can fail earlier in the mixed region
    |     \
0.4 |      \
    |       \
0.2 |        \
    |         \
0.0 +----------\----------------
    0.0        0.6       1.0
          Creep damage, D_c
```

This plot is conceptual, not a calibrated engineering diagram. Its purpose is to show why two components with the same total EOH can have different physical risk if one has more cycling and mixed creep-fatigue exposure.

## How This Feeds Step 2 Dispatch

Step 2 dispatch uses today's plant state to decide whether the next day's hourly run is worth it.

This degradation factor feeds dispatch in two ways.

| Feedback item | How Step 2 uses it |
| :--- | :--- |
| Distance to next EOH threshold | Raises start/wear cost in Mode B and Mode C as inspections approach. |
| Physical damage state | Raises forced outage risk and can make aggressive cycling less attractive. |

Flow:

```text
Yesterday's EOH and damage state
        |
        v
Step 2 hourly dispatch for today
        |
        v
fired hours + starts + trips + load swings
        |
        v
contractual EOH update + physical damage update
        |
        v
tomorrow's dispatch sees the new state
```

This is one reason the analysis can look "daily" even though dispatch is hourly. The model uses hourly operation inside each day, then compresses the result into a daily state update.

## Daily Model Inputs

The model needs both dispatch outputs and engineering assumptions.

| Input | Frequency | Why it matters |
| :--- | :--- | :--- |
| Hourly on/off status | Hourly, summarized daily | Determines fired hours and starts. |
| Hourly load factor | Hourly, summarized daily | Higher load generally raises temperature and stress. |
| Start type | Event-level, daily summary | Hot, warm, and cold starts have different thermal severity. |
| Emergency trips | Event-level | Adds severe EOH and fatigue stress. |
| Large load swings | Hourly profile, daily summary | Captures partial cycles from flexible dispatch. |
| Ambient temperature | Hourly | Affects capacity and effective thermal stress assumptions. |
| Fuel type | Operating assumption | EOH multipliers and hot-section exposure can depend on fuel. |
| Current contractual EOH | Daily state | Determines distance to inspection thresholds. |
| Current creep damage, `D_c` | Daily state | Carries time-at-temperature damage forward. |
| Current fatigue damage, `D_f` | Daily state | Carries cycling damage forward. |
| Current inspection state | Event state | Determines whether maintenance resets or partially resets damage. |

## Daily Update Logic

The daily update can be read as a checklist.

| Step | Update | Plain-English purpose |
| :--- | :--- | :--- |
| 1 | Read opening state. | Start with yesterday's EOH, damage, outage status, and inspection headroom. |
| 2 | Run hourly dispatch. | Decide today's operating hours and load profile. |
| 3 | Classify starts and events. | Count hot/warm/cold starts, trips, and large load swings. |
| 4 | Add contractual EOH. | Update the LTSA/CSA maintenance counter. |
| 5 | Estimate metal-temperature exposure. | Convert load and ambient conditions into creep-relevant severity. |
| 6 | Add creep damage. | Apply Robinson life-fraction logic. |
| 7 | Add fatigue damage. | Apply cycle severity logic and Miner's rule. |
| 8 | Check interaction envelope. | Evaluate combined creep-fatigue damage. |
| 9 | Update outage risk. | Raise forced outage probability if the stress state is high. |
| 10 | Carry state forward. | Tomorrow's Step 2 dispatch sees the new plant condition. |

ASCII version:

```text
hourly dispatch
      |
      v
daily operating summary
      |
      +--> contractual EOH counter --> inspection timing and LTSA cost
      |
      +--> creep increment
      |
      +--> fatigue increment
                |
                v
        interaction envelope
                |
                v
        forced outage risk state
```

## Worked Example 1: Contractual EOH For One Cycling Day

Assume one GT has this operating day:

| Item | Value |
| :--- | ---: |
| Fired hours | 10 |
| Hot starts | 1 |
| Warm starts | 0 |
| Cold starts | 0 |
| Emergency trips | 0 |
| Large load swings | 2 |

Contractual EOH:

```text
EOH = fired hours + hot start EOH + load swing EOH
EOH = 10 + 50 + (2 * 0.3)
EOH = 60.6
```

The key lesson is that the plant ran for 10 fired hours, but consumed 60.6 contractual EOH. The hot start dominates the day.

## Worked Example 2: Same Day, Physical Damage View

The framework would also update physical creep-fatigue damage. The exact values require material calibration and metal-temperature estimates, so the numbers below are illustrative.

Assume:

| Damage increment | Illustrative value | Why it happened |
| :--- | ---: | :--- |
| Creep increment, `delta_D_c` | 0.002 | Ten fired hours at load and temperature. |
| Fatigue increment, `delta_D_f` | 0.004 | One hot start plus two load swings. |
| Combined increment | 0.006 | Creep plus fatigue for the day. |
| Mixed-region interaction budget | 0.70 | Example value inside the framework's 0.60 to 0.80 range. |

Budget used today:

```text
Combined increment = 0.002 + 0.004
Combined increment = 0.006

Share of interaction budget used = 0.006 / 0.70
Share of interaction budget used = 0.86%
```

Do not treat the 0.86% as a real Athens plant result. It is a teaching number. The real model would need calibrated rupture-life curves, fatigue curves, effective metal temperature, and inspection reset assumptions.

## Worked Example 3: Why Independent Checks Can Mislead

Suppose a component has:

| Damage measure | Value |
| :--- | ---: |
| Creep damage, `D_c` | 0.35 |
| Fatigue damage, `D_f` | 0.35 |
| Independent creep limit | 1.00 |
| Independent fatigue limit | 1.00 |
| Mixed-region interaction limit | 0.65 |

Independent view:

```text
D_c = 0.35 < 1.00  -> pass
D_f = 0.35 < 1.00  -> pass
```

Coupled view:

```text
D_c + D_f = 0.35 + 0.35
D_c + D_f = 0.70

0.70 > 0.65 interaction limit
```

So the independent view says the component is fine, but the coupled view says the mixed creep-fatigue state is already beyond the allowed envelope. This is the framework's main reason for tracking coupling.

## ASCII Plot: Contract Clock Vs Physics Clock

```text
Life tracking over time

Contractual EOH
0%   |####----------------------------| far from threshold
50%  |###############-----------------| inspection getting closer
100% |##############################--| inspection due

Physical damage
0%   |###-----------------------------| low stress state
50%  |################----------------| risk building
100% |#########################-------| high risk before threshold

Important: these two bars do not have to move at the same speed.
```

A plant with frequent starts can move faster on the physical fatigue side than a simple fired-hour view would suggest.

## What The Framework Includes

The high-level framework includes the important structure:

| Included item | Why it matters |
| :--- | :--- |
| Contractual EOH counter | Keeps LTSA inspection timing and billing tied to auditable rules. |
| Fired hours, starts, trips, and load swings | Connects hourly dispatch to daily maintenance-life consumption. |
| Parallel creep and fatigue damage states | Separates physical stress from contract accounting. |
| Coupled interaction envelope | Avoids treating creep and fatigue as independent pass/fail accumulators. |
| Daily feedback to dispatch | Lets EOH proximity and damage state reshape future dispatch economics. |
| Endogenous forced outage path | Allows outage risk to rise from stress state rather than using only a static forced outage rate. |

This is enough for a credible learning model and a structured investment discussion. It is not enough for OEM-grade life prediction by itself.

## What The Framework Leaves Out

The high-level framework intentionally simplifies several things.

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| Direct metal-temperature measurement | Creep is very sensitive to metal temperature; inferred temperature creates uncertainty. |
| Asset-specific blade and vane material data | IN738/GTD111 public parameters are useful, but actual hardware and coatings may differ. |
| Detailed stress/strain history | Miner's rule needs cycle severity; simplified start categories lose detail. |
| Rainflow cycle counting on real load traces | Better cycle counting could improve fatigue estimates from partial load swings. |
| OEM-specific EOH rules | Contract multipliers can vary by OEM, frame, service agreement, and operating mode. |
| Inspection reset fractions | A CI, HGP, or MI may reset some damage states more than others. |
| Fuel contaminants and water/steam injection details | These can affect hot-section life and coating condition. |
| Validation against plant records | Model credibility improves if predicted stress and inspection timing match actual history. |

For investment use, the biggest red flag is not the existence of uncertainty. The red flag would be hiding it. The right treatment is to show the uncertainty, sensitivity-test it, and separate contract-driven costs from physics-driven outage risk.

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| Contractual EOH concept and inspection linkage | Local framework Section 4.4.2 and LTSA assumptions. | Green for the model structure; contract-specific values require actual LTSA review. |
| EOH as a life-consumption concept | Cambridge creep-LCF EOH paper and OEM-style maintenance concepts. | Green for concept, Amber for transfer from aero example to this plant without calibration. |
| Creep life-fraction logic | Local framework Section 3.2.1; Cambridge paper; NASA NASALife methodology context. | Green for general method family, Amber for site-specific calibration. |
| Fatigue cycle damage logic | Local framework Section 3.2.1 and Appendix B.2; NASA NASALife context. | Green for general method family, Amber for simplified start categories. |
| Creep-fatigue interaction envelope | Local framework Section 3.2.1 and Appendix B.1; Cambridge paper. | Amber because envelope shape is material- and component-specific. |
| Effective metal temperature estimate | Local framework Appendix B.1. | Amber because the framework infers it from load and ambient conditions. |
| Load swing partial-cycle credit | Local framework Appendix B.2. | Red because the framework itself marks it as engineering judgment needing sensitivity testing. |

External references used for validation:

- Cambridge University Press, "Gas turbine equivalent operating hour estimation considering creep-LCF interactions": https://www.cambridge.org/core/journals/aeronautical-journal/article/gas-turbine-equivalent-operating-hour-estimation-considering-creeplcf-interactions/71B12D0158F2AD4FEC97A50B214AB918
- NASA NTRS, "NASALIFE - Component Fatigue and Creep Life Prediction Program": https://ntrs.nasa.gov/citations/20110015541

## Open Questions Before Investment Use

Before using this factor in an investment committee deck, answer these:

| Question | Why it matters |
| :--- | :--- |
| What exact LTSA/CSA EOH formula applies to the asset? | Contractual EOH drives real billing and inspection events. |
| Does the OEM count hot/warm/cold starts exactly as assumed? | Start classification can materially change EOH and overage cost. |
| Which GT hot-section materials and coating systems are installed? | Material choice changes creep, fatigue, and interaction parameters. |
| How should CI, HGP, and MI reset physical damage states? | Reset assumptions strongly affect long-run risk. |
| Is there historian data for starts, trips, load ramps, and fired hours? | Real operating traces can validate or replace simplified assumptions. |
| Can effective metal temperature be estimated from OEM curves or plant data? | Creep estimates are only as good as the temperature proxy. |
| Should load swings use rainflow counting instead of the 0.3 credit? | Flexible dispatch can create many partial cycles. |
| How should high physical damage translate into forced outage probability? | This is where engineering damage becomes financial risk. |

## One-Sentence Takeaway

Contractual EOH tells the model when maintenance is due, while creep-fatigue coupling tells the model whether the GT hot section is physically becoming riskier before that maintenance date arrives.
