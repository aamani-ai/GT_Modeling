# Compressor Degradation: Fouling Plus Erosion

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read these first if capacity and heat rate are new:

- [Capacity](../basics/01_capacity.md)
- [Heat Rate](../basics/02_heat_rate.md)
- [Heat Rate Degradation](./03_heat_rate_degradation.md)

> Plant-Type Applicability
> This guide is about gas turbine compressor condition. It applies to GT-based simple-cycle, CCGT, and CHP assets, but wash schedules, filtration, site air quality, recovery percentages, and erosion rates are plant-specific. It does not directly apply to gas reciprocating engines.

## Why This Matters

Compressor degradation answers a front-end gas turbine question:

> Is the compressor still moving and compressing air as efficiently as it should?

The compressor is at the front of the gas turbine. It pulls in a very large amount of air and compresses it before fuel is burned. If the compressor gets dirty or physically worn, the whole GT performance stack suffers.

```text
dirty or worn compressor
        |
        v
lower airflow and compressor efficiency
        |
        v
lower GT output and worse heat rate
        |
        v
lower capacity + higher fuel cost
        |
        v
weaker Step 2 dispatch economics
```

The framework treats compressor degradation as a medium-priority stress factor, but it is financially important because it affects both:

| Output affected | What happens |
| :--- | :--- |
| Heat rate | More fuel is needed per MWh. |
| Capacity | Less air mass can mean lower MW output. |

That means compressor condition can reduce revenue and increase fuel cost at the same time.

## Plain-English Concept

Compressor degradation has two main pieces in the framework:

| Type | Recoverable? | Beginner meaning |
| :--- | :--- | :--- |
| Fouling | Mostly recoverable | Dirt, salts, oil mist, pollen, dust, or industrial contaminants stick to compressor blades. Washing can recover part of the loss. |
| Erosion | Mostly non-recoverable | Physical wear changes blade shape or surface. Washing does not fix it; major repair or overhaul may partially restore it. |

Beginner shortcut:

```text
Fouling = dirty blade surface.
Erosion = damaged blade surface.
```

Both can hurt airflow and compressor efficiency, but the maintenance answer is different.

```text
fouling -> wash / clean / improve filtration
erosion -> inspect / repair / overhaul / replace parts
```

## Plant-Type Applicability

Compressor degradation follows the GT, not the plant label.

| Plant type | What still applies | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | Compressor fouling and erosion affect MW and heat rate. | Wash economics may be tied to peaking duty and offline windows. |
| Combined-cycle GT | Each GT compressor can foul differently. | GT-A and GT-B histories may diverge; HRSG/ST output also changes downstream. |
| Aeroderivative GT | Compressor condition still matters. | Filtration, module maintenance, and recovery assumptions can differ. |
| CHP / cogeneration | GT compressor condition still matters if a GT is used. | Steam demand may limit when washing or derating can be tolerated. |
| Gas reciprocating engine | Not directly applicable. | Intake/filter and engine wear need a separate engine-specific model. |

## Where This Happens In The Plant

The compressor is inside the gas turbine.

```text
Air -> compressor -> combustor -> turbine -> exhaust -> HRSG
```

The compressor matters because the combustor and turbine depend on it. If the compressor cannot deliver the expected air mass and pressure, the GT cannot produce the same output and efficiency.

| Compressor role | Why degradation matters |
| :--- | :--- |
| Moves air mass | Less air mass can reduce output. |
| Raises pressure | Lower pressure ratio can reduce cycle efficiency. |
| Sets combustor inlet condition | Combustion and turbine operation depend on compressor delivery. |
| Consumes turbine work | A large share of turbine work is used just to drive the compressor. |

External compressor-fouling literature emphasizes the same physical direction: fouling reduces airflow, pressure ratio, and compressor efficiency, which lowers power output and thermal efficiency.

## Fouling Mechanism

Fouling happens when airborne material deposits on compressor surfaces.

Common foulants can include:

| Foulant source | Example |
| :--- | :--- |
| Natural air contaminants | Dust, pollen, salt, humidity-related deposits. |
| Industrial environment | Fine particles, hydrocarbons, chemical aerosols. |
| Plant condition | Oil mist or leakage that creates sticky deposits. |
| Coastal / humid conditions | Salt and moisture that help deposits adhere. |

Simple chain:

```text
airborne contaminants
        |
        v
deposits on compressor blades and vanes
        |
        v
rougher airfoil surface and changed blade profile
        |
        v
lower airflow / lower efficiency
        |
        v
lower MW and higher heat rate
```

The front compressor stages often matter a lot because downstream stages receive whatever flow condition the upstream stages create.

## Erosion Mechanism

Erosion is physical wear. It is not just dirt on the surface.

```text
particles / droplets / long-term wear
        |
        v
blade leading-edge and surface damage
        |
        v
permanent shape and roughness change
        |
        v
persistent performance loss
```

Erosion is treated differently in the framework:

| Type | Reset by offline wash? | Reset by CI/HGP? | Reset by MI? |
| :--- | :---: | :---: | :---: |
| Fouling | Partly yes | Partly yes | Mostly yes |
| Erosion | No | No | Partial |

That is why the framework calls fouling recoverable and erosion non-recoverable.

## Framework Model: Fouling

The framework uses a non-linear fouling model:

```text
fouling_loss(t) = A * (1 - e^(-t / tau))
```

Plain-English translation:

| Term | Meaning |
| :--- | :--- |
| `fouling_loss(t)` | Heat-rate penalty from recoverable compressor fouling. |
| `A` | Site-class asymptotic fouling loss. |
| `tau` | Time constant in fired hours. Lower `tau` means faster fouling. |
| `t` | Fired hours since the relevant clean or wash state. |

The model shape is important:

```text
early fired hours -> fouling builds faster
later fired hours -> fouling approaches an asymptote
```

This is better than a simple straight-line fouling assumption because compressor deposits do not always build at a constant rate forever.

## Framework Site Classes

The framework uses site-class coefficients:

| Site class | `A` HR impact | `tau` fired hours | Plain-English meaning |
| :--- | ---: | ---: | :--- |
| Clean inland | 1.5% | 1,500 | Slower and lower fouling. |
| Humid coastal / Hudson Valley | 2.5% | 1,000 | Middle case used for the Athens-type plant. |
| Industrial / dusty | 4.0% | 500 | Faster and higher fouling. |

The Athens-type starting state uses:

```text
A = 2.5%
tau = 1,000 fired hours
compressor fouling index = 0.0% after HGP wash
```

The air quality index from the climate simulation can scale the fouling rate dynamically each day.

## Framework Model: Wash Recovery

The framework assumes compressor washing recovers only part of the accumulated fouling.

| Maintenance action | Framework recovery |
| :--- | :--- |
| Offline wash | 60% to 80% of accumulated fouling |
| Online wash | About 45% of offline wash benefit |
| CI | 70% to 85% |
| HGP | 90% |
| MI | 95% |

Beginner warning:

```text
wash recovery is not the same as returning to new-and-clean condition
```

A wash can recover recoverable fouling, but it does not undo long-term erosion or every plant-level efficiency loss.

## Framework Model: Erosion

The framework treats compressor erosion as a slow non-recoverable heat-rate penalty:

```text
range = 0.05% to 0.10% HR impact per year
central value = 0.075% per year
```

For the Athens-type starting state:

```text
compressor erosion = +1.8% HR penalty
```

This is already embedded because the plant is assumed to be a 22-year mid-life asset.

## How Compressor Degradation Affects Heat Rate And Capacity

Compressor degradation has two economic paths.

### Heat-Rate Path

```text
lower compressor efficiency
        |
        v
more fuel needed per MWh
        |
        v
higher heat rate
        |
        v
lower spark spread
```

This path raises fuel cost.

### Capacity Path

```text
lower mass flow
        |
        v
less air available for combustion
        |
        v
lower GT output
        |
        v
lower effective plant capacity
```

This path reduces MWh that can be sold.

Both paths feed Step 2 dispatch.

## Daily Model Inputs

Compressor degradation uses operating, climate, and maintenance inputs.

| Input | Frequency | Source | Why it matters |
| :--- | :--- | :--- | :--- |
| Fired hours | Daily summary from hourly dispatch | Step 2 dispatch | Fouling accumulates with operation. |
| Hourly air quality index | Hourly or daily summary | Climate simulation | Scales fouling rate. |
| Site class | Static assumption | Asset specs / environment | Sets `A` and `tau`. |
| Time since offline wash | Daily state | Maintenance schedule | Determines accumulated recoverable fouling. |
| Online wash events | Event state | Maintenance records | Provides partial recovery while operating. |
| CI/HGP/MI events | Event state | Maintenance module | Apply larger recovery fractions. |
| Current fouling index | Daily state | Engineering model | Recoverable performance loss. |
| Current erosion penalty | Daily state | Engineering model | Non-recoverable performance loss. |
| Ambient temperature | Hourly | Climate simulation | Separately affects capacity and heat rate. |
| Current compressor condition | Daily state | Engineering model | Feeds effective HR and capacity. |

## Model Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Fouling HR penalty | Heat-rate model | Recoverable efficiency loss from deposits. |
| Erosion HR penalty | Heat-rate model | Persistent compressor loss. |
| Compressor capacity penalty | Capacity model | Output reduction from degraded mass flow. |
| Effective heat rate | Step 2 dispatch | Fuel cost per MWh. |
| Effective capacity | Step 2 dispatch | MW cap for hourly dispatch. |
| Wash benefit estimate | Maintenance planning | Fuel and revenue savings from washing. |
| Updated compressor state | Tomorrow's dispatch | Carries fouling and erosion forward. |

## Daily Update Logic

Daily compressor logic is a state update:

| Step | Update | Plain-English purpose |
| :--- | :--- | :--- |
| 1 | Read opening fouling and erosion state. | Start with yesterday's compressor condition. |
| 2 | Run Step 2 dispatch. | Determine fired hours and load profile. |
| 3 | Summarize air quality exposure. | Determine whether the day is clean, humid, dusty, or polluted. |
| 4 | Add fouling increment. | Use fired hours, site class, and AQI scaling. |
| 5 | Add erosion increment. | Add slow non-recoverable trend. |
| 6 | Apply wash or inspection recovery. | Reduce recoverable fouling if maintenance occurred. |
| 7 | Recompute effective HR and capacity. | Translate compressor state into dispatch inputs. |
| 8 | Carry state into tomorrow. | Tomorrow's Step 2 sees updated compressor condition. |

ASCII version:

```text
fired hours + AQI + site class
        |
        v
recoverable fouling index
        |
        +--> offline / online wash recovery
        |
        v
compressor condition state
        |
        +--> heat-rate penalty
        |
        +--> capacity penalty
        |
        v
next day's dispatch economics
```

## How It Feeds Step 2 Dispatch

Compressor degradation affects dispatch through two variables that Step 2 already understands:

```text
effective heat rate
effective capacity
```

Dispatch impact:

| Dispatch effect | What happens |
| :--- | :--- |
| Fuel cost rises | Worse heat rate makes each MWh more expensive. |
| Spark spread narrows | More hours fall below the economic run threshold. |
| MW cap falls | Less output is available in profitable hours. |
| Start recovery gets harder | Same start cost must be recovered from fewer or lower-margin MWh. |
| Wash timing gains value | Washing can restore margin if enough future run hours exist. |

Flow:

```text
opening compressor state
        |
        v
Step 2 sees HR and capacity
        |
        v
dispatch creates fired hours
        |
        v
fired hours and AQI update fouling
        |
        v
tomorrow's HR and capacity change
```

## Worked Example 1: Fouling After 500 Fired Hours

Use the Athens-type humid-coastal coefficients:

| Item | Value |
| :--- | ---: |
| `A` | 2.5% HR impact |
| `tau` | 1,000 fired hours |
| Fired hours since wash | 500 |

Formula:

```text
fouling_loss = A * (1 - e^(-t / tau))
fouling_loss = 2.5% * (1 - e^(-500 / 1000))
fouling_loss = 2.5% * (1 - e^-0.5)
fouling_loss = 2.5% * 0.393
fouling_loss = 0.98%
```

Interpretation:

```text
After 500 fired hours, recoverable fouling adds about 0.98% HR penalty
under the simplified Athens site-class assumption.
```

## Worked Example 2: Offline Wash Recovery

Assume the accumulated fouling penalty is 0.98% and an offline wash recovers 70% of it.

```text
Recovered fouling = 0.98% * 70%
Recovered fouling = 0.686%

Residual fouling = 0.98% - 0.686%
Residual fouling = 0.294%
```

After the wash, the plant is cleaner, but not perfectly new-and-clean.

```text
before wash: 0.98% HR penalty
after wash:  0.29% HR penalty
```

## Worked Example 3: Fuel Cost Impact

Assume:

| Item | Value |
| :--- | ---: |
| Baseline heat rate | 7,070 Btu/kWh |
| Fouling penalty | 0.98% |
| Gas price | $4.50/MMBtu |
| Generation before next wash | 300,000 MWh |

Extra heat rate:

```text
Delta HR = 7,070 * 0.98%
Delta HR = 69.3 Btu/kWh
Delta HR = 0.0693 MMBtu/MWh
```

Extra fuel cost per MWh:

```text
Extra fuel = 0.0693 * 4.50
Extra fuel = $0.31/MWh
```

Fuel cost impact:

```text
Impact = 300,000 * 0.31
Impact = $93,000
```

This is why wash timing can matter. The economics depend on wash cost, outage time, expected recovery, gas price, and expected future MWh.

## Worked Example 4: Slow Erosion

Assume the framework central erosion rate:

```text
erosion rate = 0.075% HR impact per year
```

Over 10 years:

```text
10-year erosion penalty = 0.075% * 10
10-year erosion penalty = 0.75%
```

This is slow compared with fouling, but it is persistent. A water wash does not remove it.

## ASCII Plot: Fouling Build And Wash Reset

```text
Recoverable fouling HR penalty

2.5% |                         asymptote A
     |                    _____
2.0% |               ____/
     |          ____/
1.5% |     ____/
     | ___/
1.0% |/             wash
     |              |
0.5% |              v____
     |                   \____ builds again
0.0% +------------------------------------
      clean     fired hours      after wash
```

The model shape is non-linear because fouling builds toward an asymptote, then washing creates a partial reset.

## Fouling Vs Erosion Summary

| Feature | Fouling | Erosion |
| :--- | :--- | :--- |
| Cause | Deposits on blades and vanes. | Physical surface or airfoil damage. |
| Speed | Can build over hundreds of fired hours. | Slow annual trend. |
| Recovery | Partial with online/offline wash. | Not recovered by washing. |
| Model shape | Non-linear exponential. | Linear annual trend. |
| Main data needed | Fired hours, AQI, wash records. | Inspection findings, long-term test data. |
| Dispatch impact | HR and capacity penalty until cleaned. | Persistent HR and capacity penalty. |

## What The Framework Includes

The high-level framework includes:

| Included item | Why it matters |
| :--- | :--- |
| Separate fouling and erosion logic | Distinguishes recoverable and non-recoverable loss. |
| Non-linear fouling model | Captures rapid early degradation and slowing near asymptote. |
| Site-class coefficients | Lets local environment change fouling severity. |
| AQI scaling | Connects climate/air-quality simulation to compressor condition. |
| Offline and online wash recovery | Lets maintenance partly restore performance. |
| Erosion annual trend | Carries persistent compressor degradation forward. |
| HR and capacity outputs | Connects compressor state to dispatch economics. |
| Starting erosion penalty | Reflects the Athens plant as a mid-life asset. |

## What The Framework Leaves Out

The high-level framework still simplifies several important details:

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| Actual inlet filtration condition | Filter performance strongly affects fouling. |
| Compressor wash history | Wash frequency and measured recovery calibrate the model. |
| Online wash operating details | Droplet size, nozzle condition, detergent, and load affect results. |
| Fouling by compressor stage | Front-stage fouling can affect performance differently from rear-stage fouling. |
| Erosion inspection evidence | Borescope and blade measurements are needed to validate erosion. |
| Compressor surge margin | Severe fouling can affect operability, not just economics. |
| Train-level compressor state | In a 2x1 plant, GT-A and GT-B can foul or wash differently. |
| Plant-specific performance tests | Needed to separate compressor loss from HGP, ambient, and part-load effects. |

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| Fouling as a major GT degradation mechanism | Texas A&M Turbomachinery Lab paper; Cranfield/ASME review. | Green. |
| Fouling impact on airflow, pressure ratio, efficiency, output, and heat rate | Texas A&M Turbomachinery Lab paper. | Green for direction; exact magnitude is site-specific. |
| Non-linear fouling model | Local framework note 2 and Appendix B.3. | Green for framework structure; Amber for calibration. |
| Hudson Valley coefficients `A=2.5%`, `tau=1000h` | Local framework Appendix B.3. | Amber because site-specific data is needed. |
| Offline wash recovery 60% to 80% | Local framework Appendix B.3 and fouling/washing literature. | Amber because recovery depends on method and condition. |
| Online wash benefit | Local framework Appendix B.3. | Amber because it is operating-practice dependent. |
| Erosion annual trend | Local framework Appendix B.3. | Amber because erosion is slow and hard to isolate from other degradation. |
| Compressor state feeding HR and capacity | Local framework Sections 3.2 and 3.3. | Green for model architecture. |

External references used for validation:

- Texas A&M Turbomachinery Laboratory, "Gas Turbine Axial Compressor Fouling And Washing": https://oaktrust.library.tamu.edu/items/352355bb-3f06-4bd3-b0d8-ab5f0d5aaf2c
- Direct PDF for the same paper: https://oaktrust.library.tamu.edu/bitstream/handle/1969.1/163249/t33-18.pdf
- Cranfield/ASME review, "Gas turbine compressor fouling and washing in power and aerospace propulsion": https://cran-test-dspace.koha-ptfs.co.uk/items/b35653c3-e3f8-44a6-a01f-4b7ab8385ceb

## Open Questions Before Investment Use

Before using this factor in an investment committee deck, answer these:

| Question | Why it matters |
| :--- | :--- |
| Do GT-A and GT-B have separate compressor state histories? | A 2x1 plant can have uneven fouling and wash timing. |
| What inlet filtration system is installed and how has it performed? | Filtration strongly controls fouling rate. |
| What are the actual offline and online wash dates? | Wash timing is needed to calibrate recoverable fouling. |
| How much performance recovery was measured after each wash? | The assumed 60% to 80% range may be wrong for this asset. |
| Is AQI a good proxy for local compressor foulants? | Local salt, pollen, oil mist, and industrial aerosols may not map cleanly to generic AQI. |
| Are compressor borescope or blade inspection records available? | Needed to distinguish fouling from erosion. |
| Can historical fuel and output data back-calculate compressor condition? | Performance back-testing improves confidence. |
| Should wash timing be optimized economically? | The best wash time depends on gas price, dispatch outlook, wash cost, and downtime. |

## One-Sentence Takeaway

Compressor degradation is the front-end performance loss that makes the GT breathe worse; fouling is partly washable, erosion is mostly persistent, and both can weaken dispatch by raising heat rate and reducing capacity.
