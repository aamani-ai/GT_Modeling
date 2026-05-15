# Heat Rate Degradation

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read this basics guide first if heat rate is new: [Heat Rate](../basics/02_heat_rate.md).

> Plant-Type Applicability
> Heat-rate degradation is broadly relevant to gas plants, but the mechanism stack changes by plant type. Simple-cycle GTs are mostly GT performance. CCGTs add HRSG, ST, condenser/cooling, and BOP effects. CHP plants may need steam-credit or heat-allocation logic. Gas reciprocating engines need a separate engine-maintenance model.

## Why This Matters

Heat rate degradation answers a direct financial question:

> Is the plant needing more gas to produce the same MWh?

For a gas-fired plant, fuel is usually the largest variable cost. Heat rate converts gas price into fuel cost:

```text
Fuel cost per MWh = heat rate in MMBtu/MWh * gas price in $/MMBtu
```

If heat rate gets worse, fuel cost rises. That narrows spark spread, makes marginal dispatch less attractive, and can create exposure under the heat-rate guarantee in the CSA/LTSA.

```text
higher heat rate
        |
        v
more fuel per MWh
        |
        v
higher dispatch cost
        |
        v
lower spark spread
        |
        v
fewer economic run hours in Step 2
```

The key beginner point:

```text
Capacity degradation reduces how many MWh can be sold.
Heat-rate degradation increases the cost of each MWh sold.
```

Both affect dispatch, but through different channels.

## Plain-English Concept

Heat rate is fuel intensity. Lower is better.

Heat rate degradation means the plant becomes less efficient over time:

```text
same MWh output
        +
worse heat rate
        =
more gas burned
```

The framework does not model heat-rate degradation as one vague annual number. It breaks the problem into mechanisms:

| Mechanism | Recoverable? | Beginner explanation |
| :--- | :--- | :--- |
| Compressor fouling | Mostly recoverable | Dirt, salts, oil mist, and other deposits make the compressor less efficient. Washing can recover part of the loss. |
| Hot gas path wear | Partly recoverable | Blades, vanes, seals, and clearances degrade between inspections. HGP/MI work can restore much of the loss. |
| Compressor erosion | Mostly non-recoverable between major work | Airfoil surface and shape damage permanently reduces performance until major repair. |
| HRSG / BOP drift | Mostly non-recoverable in the framework | Balance-of-plant and heat-recovery losses slowly reduce net efficiency. |
| Ambient temperature overlay | Temporary, not degradation | Hot weather worsens heat rate even if the plant is mechanically healthy. |
| Part-load overlay | Operating condition, not degradation | Combined cycles are less efficient away from full load. |

This separation matters because different causes have different fixes. Washing can help fouling. A CI can partially help some hot-section issues. An HGP or MI can restore more. Ambient temperature cannot be repaired; it must be corrected for in dispatch and performance tests.

## Plant-Type Applicability

Use the same heat-rate concept, but do not use the same component allocation everywhere.

| Plant type | What still applies | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Fuel per MWh is still the key marginal-cost driver. | No HRSG/ST recovery; degradation is mostly GT and BOP. |
| Combined-cycle GT | Fuel per net MWh still drives spark spread. | Steam-cycle degradation and part-load combined-cycle behavior matter. |
| Frame GT | Heat-rate degradation is GT-specific. | Large-frame inspection and hot-section restoration assumptions matter. |
| Aeroderivative GT | Heat rate still drives dispatch cost. | Module swaps and maintenance intervals can change recovery assumptions. |
| CHP / cogeneration | Fuel intensity still matters. | Electric-only heat rate can mislead if useful steam/heat has economic value. |

## Plant Context: Athens-Type GE 7FA

The framework starts the Athens-type plant after a Hot Gas Path inspection.

| State item | Framework value | Meaning |
| :--- | ---: | :--- |
| Post-HGP baseline heat rate at ISO | 7,070 Btu/kWh | Starting heat rate for the model. |
| Heat rate at 90 deg F ambient | 7,230 Btu/kWh | Hot-weather correction makes heat rate worse. |
| Heat rate at 50% minimum load, ISO | 8,215 Btu/kWh | Part-load operation is much less efficient. |
| Recoverable HR degradation at start | 0.0% | Reset at HGP. |
| Compressor fouling index at start | 0.0% | Water washed during HGP outage. |
| Compressor erosion already embedded | +1.8% HR penalty | Reflects 22 years of non-recoverable degradation. |
| CSA heat-rate guarantee | Within 2.0% of 7,070 Btu/kWh | Owner pays penalty if cycle-average overage exceeds guarantee. |

The 2.0% guarantee threshold is:

```text
Guarantee threshold = 7,070 * 1.02
Guarantee threshold = 7,211.4 Btu/kWh
```

Do not compare every hot-hour heat rate directly to this number without checking the contract correction basis. Performance guarantees usually specify correction methods and test conditions. The framework's point is that cycle-average heat-rate underperformance can become a real owner cost.

## Physical Mechanisms

### Compressor Fouling

Compressor fouling is usually the first heat-rate degradation topic to understand.

The compressor pulls in a large volume of air. Tiny contaminants can stick to compressor blades and change their surface condition. That can reduce compressor efficiency and airflow.

```text
air contaminants
        |
        v
deposits on compressor blades
        |
        v
lower compressor efficiency / mass flow
        |
        v
more fuel needed for same net output
        |
        v
higher heat rate
```

The framework treats fouling as non-linear:

```text
fouling_loss(t) = A * (1 - e^(-t / tau))
```

Plain-English translation:

| Term | Meaning |
| :--- | :--- |
| `fouling_loss(t)` | Heat-rate penalty from fouling after time `t`. |
| `A` | Asymptotic fouling loss for the site class. |
| `tau` | Time constant; lower `tau` means fouling builds faster. |
| `t` | Fired hours since the relevant clean/wash state. |

For the Hudson Valley class in the framework:

```text
A = 2.5% HR impact
tau = 1,000 fired hours
```

The intuition is that fouling can build faster early, then slow as it approaches an equilibrium. Offline washing recovers part of the accumulated fouling, but not necessarily all of it.

### Hot Gas Path Wear

Hot gas path wear is the heat-rate penalty from parts exposed to the hottest flow path:

| Area | Why it affects heat rate |
| :--- | :--- |
| Turbine blades and vanes | Aerodynamic losses and surface condition affect expansion efficiency. |
| Seals and shrouds | Clearances can increase leakage losses. |
| Nozzles | Fouling, wear, or damage changes flow and efficiency. |
| Coatings and repaired parts | Surface condition and temperature protection affect long-run performance. |

The framework models HGP recoverable degradation as:

```text
0.2% to 0.4% heat-rate increase per year
```

The central assumption is 0.3% per year between overhauls.

### Compressor Erosion

Erosion is more permanent than fouling. It changes the airfoil surface or shape and does not wash away.

The framework uses:

```text
0.05% to 0.10% HR impact per year
central value = 0.075% per year
```

This is carried as non-recoverable degradation until major repair or overhaul. In the starting state, the framework says the Athens-type plant already has a +1.8% HR penalty from 22 years of compressor erosion.

### HRSG / BOP Drift

The framework also includes a small non-recoverable HRSG/BOP contribution:

```text
0.02% to 0.05% per year
central value = 0.035% per year
```

This is a plant-level efficiency drag, not just a GT air-path issue. It can come from heat-recovery, auxiliary load, cooling, or balance-of-plant condition.

## Temporary Effects Vs Degradation

This distinction is critical.

| Effect | Example | Is it degradation? | How to model it |
| :--- | :--- | :---: | :--- |
| Ambient heat-rate correction | 90 deg F raises HR from 7,070 to 7,230 Btu/kWh. | No | Recompute from hourly weather. |
| Part-load heat-rate penalty | 50% load raises HR to 8,215 Btu/kWh at ISO. | No | Apply from hourly dispatch load. |
| Compressor fouling | Deposits build over fired hours. | Yes | Accumulate and partially reset with washes. |
| HGP wear | Hot-section efficiency worsens between inspections. | Yes | Accumulate and partially reset at CI/HGP/MI. |
| Compressor erosion | Airfoil damage accumulates over years. | Yes | Carry forward until major repair. |

The model should not accidentally treat a hot day or part-load hour as permanent degradation. Those are operating overlays. The persistent state is fouling, HGP wear, erosion, and other plant condition.

## Model Inputs

Heat-rate degradation uses both operating data and plant-condition state.

| Input | Frequency | Source | What it does |
| :--- | :--- | :--- | :--- |
| Fired hours | Daily summary from hourly dispatch | Step 2 dispatch | Drives fouling and time-based degradation. |
| Load profile | Hourly | Step 2 dispatch | Applies part-load heat-rate multiplier. |
| Ambient temperature | Hourly | Climate simulation | Applies ambient heat-rate correction. |
| Air quality index | Hourly or daily summary | Climate simulation | Scales compressor fouling rate. |
| Time since wash | Daily state | Maintenance/wash schedule | Determines accumulated recoverable fouling. |
| Time since CI/HGP/MI | Daily state | Maintenance module | Determines HGP wear and recovery timing. |
| Current fouling index | Daily state | Engineering model | Recoverable compressor loss. |
| Current HGP degradation | Daily state | Engineering model | Recoverable hot-section loss. |
| Current erosion penalty | Daily state | Engineering model | Non-recoverable compressor loss. |
| Daily gas price | Daily | Gas market simulation | Converts HR penalty into fuel cost. |
| Hourly power price | Hourly | Power market simulation | Determines whether the degraded plant clears dispatch. |

## Model Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Effective heat rate | Step 2 dispatch | Fuel intensity used in economic dispatch. |
| Fuel cost per MWh | Step 2 dispatch / financial layer | Heat rate multiplied by gas price. |
| Spark spread impact | Investor metrics | Margin lost because the plant burns more gas. |
| CSA heat-rate guarantee exposure | Contract module | Potential owner penalty if cycle-average HR exceeds guarantee. |
| Degradation-loss attribution | Financial reporting | Separates heat-rate loss from forced outage and planned outage loss. |
| Updated HR state | Tomorrow's dispatch | Carries persistent degradation forward. |

## Daily Update Logic

The daily loop is easiest to read as two layers: hourly overlays and daily persistent state.

### Hourly Dispatch Layer

```text
hourly ambient temperature
        +
hourly load level
        +
opening persistent HR state
        |
        v
hourly effective heat rate
        |
        v
fuel cost and dispatch margin
```

Step 2 uses the heat rate it sees at the start of the decision. Hot weather and part-load operation can change the hourly effective heat rate inside the day.

### Daily State Update Layer

```text
today's fired hours + air quality + wash/inspection status
        |
        v
update fouling, HGP wear, erosion, HRSG/BOP drift
        |
        v
apply any wash or inspection recovery
        |
        v
carry updated persistent HR state into tomorrow
```

A practical checklist:

| Step | Update | Plain-English purpose |
| :--- | :--- | :--- |
| 1 | Read opening heat-rate state. | Start with current fouling, HGP wear, erosion, and baseline HR. |
| 2 | Run hourly dispatch with current effective HR. | Determine whether the plant runs and at what load. |
| 3 | Summarize fired hours and load. | Convert hourly operation into daily degradation drivers. |
| 4 | Add compressor fouling. | Use fired hours and air quality to update recoverable fouling. |
| 5 | Add HGP wear. | Add time-based hot-section efficiency loss. |
| 6 | Add erosion and HRSG/BOP drift. | Add slow non-recoverable loss. |
| 7 | Apply wash or inspection recovery. | Reduce recoverable degradation if a wash, CI, HGP, or MI occurs. |
| 8 | Check heat-rate guarantee exposure. | Track cycle-average HR against CSA terms. |
| 9 | Feed updated HR to tomorrow. | Tomorrow's Step 2 sees the new persistent state. |

## Framework Component Table

The framework's heat-rate degradation table can be read like this:

| Component | Framework model | Recovery logic |
| :--- | :--- | :--- |
| Compressor fouling | Non-linear `A * (1 - e^(-t / tau))`, scaled by AQI. | Offline wash recovers 60% to 80%; CI 70% to 85%; HGP 90%; MI 95%. |
| Hot gas path wear | 0.2% to 0.4% per year linear HR increase. | CI partial recovery; HGP 70% to 80%; MI 90%. |
| Compressor erosion | 0.05% to 0.10% per year linear HR impact. | No wash recovery; partial recovery only at MI. |
| HRSG / BOP | 0.02% to 0.05% per year plant-level loss. | No recovery in the framework. |
| Total first-year range | 0.8% to 1.5%. | Higher in year 1 because fouling accumulates non-linearly after a clean state. |

This table is one of the most important parts of the degradation model. It explains why a single "1% per year degradation" assumption is too blunt.

## ASCII Plot: Sawtooth Heat-Rate Degradation

```text
Heat-rate degradation %

2.5 |                  /|
2.0 |             /---/ |         HGP/MI reset more
1.5 |        /---/      |
1.0 |   /---/           |   offline washes reset some fouling
0.5 |--/                |
0.0 +-------------------+----------------
     clean       wash   CI       HGP/MI

Pattern:
degradation builds while running
washes and inspections recover part of the loss
non-recoverable erosion remains underneath
```

The actual shape depends on dispatch hours, air quality, wash schedule, and inspection timing.

## Worked Example 1: Fuel Cost From A 1% HR Degradation

Assume:

| Item | Value |
| :--- | ---: |
| Baseline heat rate | 7,070 Btu/kWh |
| Degradation | 1.0% |
| Gas price | $5.50/MMBtu |
| Annual generation | 1,500,000 MWh |

Heat-rate increase:

```text
Delta HR = 7,070 * 1.0%
Delta HR = 70.7 Btu/kWh
Delta HR = 0.0707 MMBtu/MWh
```

Extra fuel cost per MWh:

```text
Extra fuel cost = 0.0707 * 5.50
Extra fuel cost = $0.38885/MWh
```

Annual fuel cost impact:

```text
Annual impact = 1,500,000 * 0.38885
Annual impact = $583,275
```

This lines up with the framework's intuition that a 1% heat-rate penalty can be worth hundreds of thousands of dollars per year, depending on MWh and gas price.

## Worked Example 2: Spark Spread Narrowing

Assume:

| Item | Clean case | Degraded case |
| :--- | ---: | ---: |
| Power price | $55/MWh | $55/MWh |
| Gas price | $4.00/MMBtu | $4.00/MMBtu |
| Heat rate | 7.070 MMBtu/MWh | 7.211 MMBtu/MWh |
| VOM | ignored | ignored |

Fuel cost:

```text
Clean fuel cost = 7.070 * 4.00 = $28.28/MWh
Degraded fuel cost = 7.211 * 4.00 = $28.84/MWh
```

Spark spread:

```text
Clean spark spread = 55.00 - 28.28 = $26.72/MWh
Degraded spread    = 55.00 - 28.84 = $26.16/MWh
Spread loss        = $0.56/MWh
```

The plant may still run. The issue is that every dispatched MWh is less profitable.

## Worked Example 3: Guarantee Threshold

The framework's heat-rate guarantee is within 2.0% of the post-HGP baseline.

| Item | Value |
| :--- | ---: |
| Baseline HR | 7,070 Btu/kWh |
| Guarantee band | 2.0% |
| Threshold HR | 7,211.4 Btu/kWh |

Calculation:

```text
Threshold = 7,070 * 1.02
Threshold = 7,211.4 Btu/kWh
```

If the cycle-average corrected heat rate is 7,260 Btu/kWh:

```text
Excess HR = 7,260 - 7,211.4
Excess HR = 48.6 Btu/kWh
```

The framework then converts the excess heat rate into excess fuel cost using MWh and delivered gas price.

Important: this is a contract calculation. The exact correction method, averaging period, exclusions, and test conditions must come from the CSA/LTSA.

## How Heat-Rate Degradation Feeds Step 2 Dispatch

Step 2 dispatch needs heat rate because it determines fuel cost.

```text
power price
  - gas price * heat rate
  - VOM
  - allocated start cost
  - EOH wear penalty
  = dispatch margin
```

As heat rate worsens:

| Dispatch effect | What happens |
| :--- | :--- |
| Fuel cost rises | Each MWh costs more gas. |
| Spark spread narrows | Less margin is left between power price and gas cost. |
| Marginal hours drop out | Hours near breakeven may no longer clear. |
| Starts become harder to justify | Same start cost must be recovered from lower margin. |
| Conservative dispatch can become more attractive | Running less can slow EOH and fouling accumulation, depending on economics. |

This is why heat-rate degradation is part of the daily feedback loop:

```text
yesterday's HR state
        |
        v
today's Step 2 dispatch
        |
        v
today's fired hours and load profile
        |
        v
updated fouling and HGP wear
        |
        v
tomorrow's HR state
```

## What The Framework Includes

The high-level framework includes:

| Included item | Why it matters |
| :--- | :--- |
| Component-level HR degradation | Avoids a single blunt annual degradation assumption. |
| Non-linear compressor fouling | Captures rapid early fouling and slower approach to an asymptote. |
| AQI-scaled fouling | Connects climate/air-quality inputs to plant performance. |
| Wash recovery fractions | Lets maintenance actions restore part of the loss. |
| HGP, CI, and MI recovery logic | Connects inspections to performance resets. |
| Ambient heat-rate correction | Reflects hot-weather efficiency loss. |
| Part-load heat-rate polynomial | Makes dispatch sensitive to load level, not just on/off status. |
| CSA heat-rate guarantee | Converts underperformance into potential contract exposure. |
| Daily feedback to dispatch | Lets degraded HR change future operating economics. |

## What The Framework Leaves Out

The high-level framework still leaves several important details for diligence:

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| Actual compressor wash records | Needed to calibrate fouling accumulation and recovery. |
| Online vs offline wash schedule optimization | The economics depend on wash cost, downtime, recovery, and fuel savings. |
| Plant-specific OEM correction curves | Needed for defensible heat-rate corrections. |
| Exact CSA/LTSA heat-rate test protocol | Determines whether an apparent overage is actually billable. |
| Sensor-quality and test-data validation | Bad measurements can look like degradation. |
| Separate GT vs ST/HRSG efficiency attribution | Combined-cycle net heat rate can hide where the loss occurs. |
| Fuel quality and water/steam injection effects | Can affect performance and hot-section condition. |
| Degradation uncertainty by dispatch regime | Baseload, cycling, and peaking operation may degrade differently. |

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| Heat rate definition and efficiency conversion | EIA heat-rate FAQ; basics heat-rate guide. | Green. |
| Athens baseline HR values | Local framework Section 4.2. | Green as framework inputs; asset-specific values require test data. |
| Compressor fouling model form | Local framework Appendix B.3; external gas-turbine degradation literature. | Green for mechanism, Amber for site coefficients. |
| Hudson Valley fouling coefficients | Local framework Appendix B.3. | Amber because field calibration is needed. |
| Offline wash recovery | Local framework Appendix B.3. | Amber because recovery depends on wash method and condition. |
| HGP degradation rate | Local framework Appendix B.4. | Green for framework assumption, Amber for exact unit without OEM data. |
| Compressor erosion rate | Local framework Appendix B.3. | Amber because it is slow, plant-specific, and hard to isolate. |
| CSA heat-rate guarantee exposure | Local framework Section 4.4.5. | Amber until actual contract language is reviewed. |
| Part-load HR polynomial | Local framework Section 4.6 and Appendix B.6. | Green as model fit, needs verification against OEM data. |

External references used for validation:

- U.S. EIA, "What is the efficiency of different types of power plants?": https://www.eia.gov/tools/faqs/faq.php?id=107
- Dai, Zhang, and Luo, "A Novel Data-Driven Approach for Predicting the Performance Degradation of a Gas Turbine," Energies 2024: https://www.mdpi.com/1996-1073/17/4/781

## Open Questions Before Investment Use

Before using this factor in an investment deck or final model, answer these:

| Question | Why it matters |
| :--- | :--- |
| What is the actual post-HGP corrected heat-rate test result? | It should anchor the baseline, not just a generic frame assumption. |
| What is the exact CSA/LTSA heat-rate guarantee formula? | Contract language defines the billable exposure. |
| Do we have compressor wash dates and measured recovery? | Needed to calibrate fouling and wash economics. |
| Is air quality measured at the site or proxied from a broader dataset? | Fouling coefficients depend heavily on local conditions. |
| How much of current HR gap is fouling vs erosion vs HGP wear? | Recoverable and non-recoverable losses have different fixes. |
| Are part-load and ambient corrections applied before judging degradation? | Otherwise the model may mistake operating condition for degradation. |
| Does the model optimize wash timing or use a fixed wash schedule? | Wash timing can materially affect fuel cost and downtime. |
| Can historical dispatch and fuel data back-calculate realized heat rate? | Back-testing improves confidence in the degradation state. |

## One-Sentence Takeaway

Heat-rate degradation is the plant getting more fuel-hungry over time; the model turns that physical efficiency loss into higher fuel cost, weaker spark spread, and potential heat-rate guarantee exposure.
