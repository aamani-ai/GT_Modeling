# Thermal Barrier Coating Life

Start here for the broader plant-type map: [Gas Plant Type Map](../basics/00_gas_plant_type_map.md).

Start here if plant acronyms are new: [Combined-Cycle Plant Anatomy](../basics/00_combined_cycle_plant_anatomy.md).

Read this guide first if hot-section life accounting is new: [EOH Accumulation With Creep-Fatigue Coupling](./01_eoh_creep_fatigue_coupling.md).

> Plant-Type Applicability
> TBC life is a GT hot-section topic. It can apply to GT-based simple-cycle, CCGT, and CHP assets when the machine uses coated hot gas path components. It is not an HRSG/ST, generator, or gas reciprocating engine degradation model.

## Why This Matters

Thermal barrier coating life answers a hot-section protection question:

> Is the coating that protects turbine blades and vanes still doing its job?

Thermal barrier coating is usually shortened to TBC. It is a protective coating system on hot gas path components. It helps insulate the metal from the hottest combustion gas and helps resist oxidation.

The framework treats TBC life as a medium-priority stress factor because coating failure can lead to:

| Impact | Plain-English meaning |
| :--- | :--- |
| Accelerated base-metal oxidation | If the coating is gone, the underlying metal is exposed to harsher conditions. |
| Forced outage between inspections | Significant coating spallation may require taking the unit offline. |
| Blade or vane replacement cost | Damaged hot-section parts can be expensive to repair or replace. |
| Higher inspection uncertainty | Coating condition can vary across parts and operating histories. |

Simple flow:

```text
high firing temperature + time at temperature + thermal cycling
        |
        v
TBC aging, oxidation, cracking, or spallation
        |
        v
base metal loses protection
        |
        v
higher hot-section failure risk
        |
        v
forced outage or blade/vane replacement
```

The financial point is that TBC failure is not mainly a spark-spread problem. It is an availability, repair-cost, and tail-risk problem.

## Plain-English Concept

A TBC is a heat shield for turbine hot-section parts.

Beginner version:

```text
Hot gas path metal is expensive and highly stressed.
TBC helps keep that metal cooler and protected.
If the coating cracks or falls off, the metal underneath is more exposed.
```

The word "spallation" means coating material has flaked, detached, or fallen away from the protected surface.

```text
healthy coating  -> metal protected
spalled coating  -> metal exposed locally
```

## Plant-Type Applicability

The coating topic follows the hot-section hardware, not the market role of the plant.

| Plant type | What still applies | What changes |
| :--- | :--- | :--- |
| Simple-cycle GT | TBC aging can affect hot-section outage risk. | Peaking/cycling duty may emphasize thermal cycles over long steady hours. |
| Combined-cycle GT | TBC aging applies to each GT. | 1x1 vs 2x1 dispatch can make unit-level TBC histories different. |
| Frame GT | High firing temperature and HGP intervals matter. | OEM coating system and inspection findings are critical. |
| Aeroderivative GT | Coated hot parts may still matter. | Module overhaul and replacement logic can differ. |
| CHP / cogeneration | GT hot-section coating still matters if a GT is used. | Heat-led dispatch may change time-at-temperature patterns. |

## Where This Happens In The Plant

TBC is mainly a gas turbine hot gas path topic.

| Area | Why TBC matters |
| :--- | :--- |
| Turbine blades | Rotating airfoils exposed to hot gas and high stress. |
| Turbine vanes / nozzles | Stationary airfoils that guide hot gas into rotating stages. |
| Shrouds and hot-section surfaces | Experience high temperature and local thermal gradients. |
| Combustion-adjacent hot parts | Can see local hot streaks, thermal cycling, and coating stress. |

Basic location:

```text
Air -> compressor -> combustor -> turbine blades/vanes -> exhaust
                                      ^
                                      |
                                TBC on hot parts
```

The framework starts the Athens-type plant just after an HGP inspection. It sets TBC time-at-temperature to 0.0 hours because blades are treated as new or refurbished at HGP.

## What A TBC System Is

A simplified TBC system has layers.

```text
hot combustion gas
        |
        v
ceramic top coat        <- thermal insulation
bond coat               <- oxidation/corrosion protection and adhesion
superalloy base metal   <- structural blade or vane material
```

A thin thermally grown oxide layer, often called TGO, can form between the top coat and bond coat during high-temperature service.

| Layer | Plain-English role |
| :--- | :--- |
| Ceramic top coat | Insulates the metal from hot gas. |
| Bond coat | Helps the ceramic stay attached and resists oxidation. |
| TGO | Oxide layer that grows during service; necessary at small levels, harmful if excessive. |
| Base metal | Structural hot-section component. |

TBC failure is usually not one simple event. It can involve oxidation, thermal mismatch stress, sintering, cracking, erosion, foreign object damage, contaminants, and repeated thermal cycles.

## Why TBCs Fail

The framework focuses on peak firing temperature, thermal cycling severity, fuel contaminants, and cumulative fired hours at temperature.

Plain-English mechanisms:

| Driver | Why it hurts TBC life |
| :--- | :--- |
| High firing temperature | Speeds oxidation and coating aging. |
| Time at temperature | More exposure means more opportunity for degradation. |
| Thermal cycling | Repeated expansion and contraction can drive cracks and delamination. |
| Fuel contaminants | Can accelerate corrosion, deposits, or coating attack. |
| Local hot streaks | Uneven combustor pattern can overheat specific blades or vanes. |
| Prior repairs | Repaired coatings may not behave like new OEM coatings. |

Spallation risk rises when cracks and interface stresses grow enough that the ceramic layer detaches.

```text
high temperature exposure
        +
thermal cycles
        +
oxidation / contaminants
        v
interface damage and cracking
        v
coating spallation
```

## Framework TBC Model

The framework uses a Weibull failure model.

Local framework assumptions:

| Parameter | Framework value | Meaning |
| :--- | :--- | :--- |
| Shape parameter, `beta` | 3.0 central, range 2.5 to 4.0 | Controls how failure risk rises with age/exposure. |
| Scale parameter, `eta` | 28,000 equivalent fired hours | Characteristic life in the Weibull model. |
| Starting state | 0.0 hours after HGP | New/refurbished blades at HGP. |
| Failure threshold | Sampled per simulation path | Each path gets its own TBC failure threshold. |
| Main state variable | TBC time-at-temperature | Accumulated severity-weighted exposure. |

This means the model does not say:

```text
Every plant fails exactly at 28,000 hours.
```

It says:

```text
TBC failure timing is uncertain.
Each simulation path samples a different threshold.
Risk rises as time-at-temperature accumulates.
```

That is a better fit for coating life than a deterministic straight-line counter because some coatings fail early and others last longer.

## Weibull In Plain Language

Weibull is a common reliability model for failure times.

For a two-parameter Weibull:

```text
F(t) = 1 - exp(-((t / eta) ^ beta))
```

Where:

| Term | Meaning |
| :--- | :--- |
| `F(t)` | Probability failure has occurred by exposure time `t`. |
| `t` | Exposure time, here treated as equivalent fired hours or time-at-temperature. |
| `eta` | Scale parameter, often called characteristic life. |
| `beta` | Shape parameter; controls how sharply risk rises. |

Useful beginner interpretation:

| `beta` behavior | Meaning |
| :--- | :--- |
| `beta` less than 1 | Early failures dominate; hazard falls over time. |
| `beta` about 1 | Roughly constant failure rate. |
| `beta` greater than 1 | Wear-out behavior; hazard rises with age/exposure. |

The framework's `beta` range of 2.5 to 4.0 means wear-out behavior: risk is low early, then rises faster as exposure accumulates.

## ASCII Plot: Weibull Wear-Out Shape

```text
TBC failure probability

100% |                              /
     |                           __/
 75% |                        __/
     |                     __/
 50% |                  __/
     |              ___/
 25% |          ___/
     |      ___/
  0% |_____/
     +--------------------------------
       low exposure      high exposure
```

This is conceptual. The exact curve depends on `beta`, `eta`, severity scaling, and plant-specific TBC condition.

## Daily Model Inputs

TBC life uses hot-section operating data and asset assumptions.

| Input | Frequency | Source | Why it matters |
| :--- | :--- | :--- | :--- |
| Fired hours | Daily summary from hourly dispatch | Step 2 dispatch | Adds time-at-temperature exposure. |
| Load profile | Hourly | Step 2 dispatch | Higher load generally means higher firing temperature exposure. |
| Peak firing temperature proxy | Hourly or daily estimate | Asset specs / model | Main TBC severity driver. |
| Start and trip events | Event-level | Dispatch / operations | Thermal cycling can accelerate coating damage. |
| Fuel quality / contaminants | Static or periodic | Fuel specs | Contaminants can increase coating attack. |
| Current TBC time-at-temperature | Daily state | Engineering model | Accumulated coating exposure. |
| Path-specific TBC threshold | Path state | Weibull sample | Determines when that simulation path fails. |
| HGP / MI event state | Maintenance module | Inspection schedule | Resets or renews coating state if blades/vanes are repaired or replaced. |
| Inspection findings | Event data | Borescope / outage reports | Can recalibrate risk if coating damage is observed. |

## Model Outputs

| Output | Used by | Meaning |
| :--- | :--- | :--- |
| Updated TBC time-at-temperature | Engineering state | Accumulated coating exposure. |
| TBC Weibull state | Forced outage module | How close the path is to the sampled failure threshold. |
| `P_TBC` | GT forced outage probability | Coating-related contribution to GT outage risk. |
| TBC forced outage trigger | Maintenance/failure module | Event if threshold is exceeded. |
| Repair or blade replacement cost exposure | Financial layer | Potential outage cost if coating failure damages parts. |
| Updated hot-section state | Tomorrow's dispatch | Availability and risk state carried forward. |

## Daily Update Logic

The daily loop for TBC is path-specific.

| Step | Update | Plain-English purpose |
| :--- | :--- | :--- |
| 1 | Read opening TBC state. | Start with current time-at-temperature and path threshold. |
| 2 | Check forced outage risk. | If threshold was already crossed, the unit may be unavailable. |
| 3 | Run Step 2 dispatch if available. | Determine fired hours, load, starts, trips, and temperature exposure. |
| 4 | Convert operation into TBC exposure. | Add severity-weighted time-at-temperature. |
| 5 | Compare exposure with sampled threshold. | See whether this path's TBC life is exhausted. |
| 6 | Update `P_TBC`. | Below threshold, use conditional Weibull hazard; above threshold, force outage. |
| 7 | Apply maintenance reset if HGP/MI occurs. | New/refurbished coating resets or reduces exposure. |
| 8 | Carry state into tomorrow. | Tomorrow's outage risk sees the updated TBC state. |

ASCII version:

```text
hourly dispatch and load
        |
        v
severity-weighted time at temperature
        |
        v
cumulative TBC exposure
        |
        +--> compare to path-specific Weibull threshold
        |
        v
P_TBC or forced outage trigger
```

## How It Feeds Step 2 Dispatch

TBC life does not usually change heat rate or capacity hour by hour until a failure or maintenance event occurs.

Instead, it feeds Step 2 through availability risk:

| Feedback path | Dispatch effect |
| :--- | :--- |
| `P_TBC` rises | Higher chance the GT is unavailable before a run day. |
| TBC outage occurs | Capacity is zero or reduced during outage. |
| Blade/vane work is needed | Planned or forced outage timing changes future dispatch availability. |
| High-risk state near threshold | Conservative dispatch may be considered if the model penalizes stress exposure. |

Flow:

```text
today's dispatch creates time-at-temperature
        |
        v
TBC Weibull state ages
        |
        v
future P_TBC rises
        |
        v
forced outage risk can block future Step 2 runs
```

This is different from compressor degradation:

```text
compressor degradation -> gradually changes HR and capacity
TBC life              -> mostly changes failure risk until an event occurs
```

## Worked Example 1: Daily Time-At-Temperature

Assume one GT has:

| Operating block | Fired hours | Severity multiplier |
| :--- | ---: | ---: |
| Moderate load | 6 | 1.0 |
| High load / hotter firing | 4 | 1.2 |

Equivalent TBC exposure:

```text
TBC exposure = (6 * 1.0) + (4 * 1.2)
TBC exposure = 6.0 + 4.8
TBC exposure = 10.8 equivalent fired hours
```

The severity multiplier is illustrative. The framework says TBC life depends on peak firing temperature and time-at-temperature, but the exact severity curve must be calibrated to plant/OEM data.

## Worked Example 2: Weibull Failure Probability

Use the framework central values:

| Parameter | Value |
| :--- | ---: |
| `beta` | 3.0 |
| `eta` | 28,000 equivalent fired hours |

Formula:

```text
F(t) = 1 - exp(-((t / eta) ^ beta))
```

Illustrative probabilities:

| Exposure `t` | Approx. `F(t)` | Plain-English meaning |
| :--- | ---: | :--- |
| 10,000 hours | 4.5% | Low but non-zero cumulative failure probability. |
| 20,000 hours | 30.5% | Risk is becoming material. |
| 24,000 hours | 46.8% | Around half of comparable paths may have failed by this point. |
| 28,000 hours | 63.2% | Characteristic life; not a hard deadline. |

The important point is the curve shape. Risk does not rise evenly. It accelerates as exposure approaches the characteristic life region.

## Worked Example 3: Path-Specific Threshold

Suppose the simulation samples a TBC failure threshold for one path:

```text
sampled threshold = 22,000 equivalent fired hours
opening TBC exposure = 21,990 equivalent fired hours
today's exposure = 15 equivalent fired hours
```

End-of-day state:

```text
closing exposure = 21,990 + 15
closing exposure = 22,005 equivalent fired hours
```

Because 22,005 is above the sampled threshold, the model triggers a TBC-related forced outage on that path.

Another path might have a threshold of 31,000 hours and continue operating. That is the reason for sampling path-specific thresholds in the first place.

## Worked Example 4: Forced Outage Revenue Exposure

Assume a TBC-related forced outage lasts 8 days.

| Item | Value |
| :--- | ---: |
| Outage duration | 8 days |
| Potential dispatch output | 500 MW |
| Economic run hours per day | 10 hours |
| Dispatch margin | $30/MWh |

Lost margin:

```text
Lost MWh = 8 * 10 * 500
Lost MWh = 40,000 MWh

Lost margin = 40,000 * 30
Lost margin = $1,200,000
```

This ignores repair cost. It only shows why availability risk matters financially.

## TBC Vs Other Hot-Section Damage

TBC life overlaps with other hot-section topics but is not the same thing.

| Topic | Main question |
| :--- | :--- |
| Contractual EOH | When does the service contract say inspection is due? |
| Creep-fatigue coupling | How much physical life has hot-section material consumed? |
| Combustion cycling fatigue | How much cycling stress is on combustion liners and transition pieces? |
| TBC life | Is protective coating still intact enough to protect blades and vanes? |
| Rotor life | How much low-probability tail risk is building in rotating discs? |

Same dispatch day, different stress states:

```text
fired hours
  +--> EOH
  +--> creep
  +--> TBC time-at-temperature

starts and trips
  +--> fatigue
  +--> combustion cycling damage
  +--> TBC thermal cycling stress
```

## What The Framework Includes

The high-level framework includes:

| Included item | Why it matters |
| :--- | :--- |
| TBC as separate stress factor | Avoids hiding coating failure inside generic hot-section life. |
| Peak firing temperature and time-at-temperature drivers | Connects dispatch severity to coating aging. |
| Thermal cycling severity | Captures starts/trips as coating stress, not only fired hours. |
| Fuel contaminant severity multiplier | Allows coating risk to change with fuel quality assumptions. |
| Weibull failure model | Captures uncertain failure timing and early/late path variation. |
| Path-specific threshold sampling | Makes TBC failure stochastic across simulation paths. |
| `P_TBC` in GT outage risk | Converts coating state into forced outage probability. |
| HGP reset starting state | Reflects new/refurbished blades after HGP. |

## What The Framework Leaves Out

The high-level framework still simplifies several important items:

| Missing or simplified detail | Why it matters |
| :--- | :--- |
| Exact coating system | APS, EB-PVD, bond coat chemistry, and repair method affect life. |
| Blade/vane-specific coating condition | Coating may be healthy on some parts and damaged on others. |
| Direct borescope findings | Visual evidence should override generic Weibull assumptions. |
| Real firing temperature history | TBC life is sensitive to actual thermal exposure. |
| Hot streak and pattern factor data | Local combustor nonuniformity can drive localized spallation. |
| CMAS or contaminant chemistry | Dust, ash, salts, and fuel contaminants can change failure mode. |
| Coating repair quality | Repaired coating may not have the same life as new OEM coating. |
| Event severity curve | The guide uses simple equivalent fired hours, but true damage is temperature-dependent and non-linear. |

## Source Basis And Certainty

| Topic | Main source basis | Certainty |
| :--- | :--- | :--- |
| TBC function as insulation and oxidation protection | NASA TBC experience and NASA TBC materials references. | Green. |
| TBC failure dependence on high temperature cycling, bond coat oxidation, and coating condition | NASA thermal barrier coating references. | Green for mechanism, Amber for asset-specific life. |
| Weibull model form | NIST reliability handbook. | Green for statistical method. |
| Framework `beta` range 2.5 to 4.0 | Local framework Appendix B.7, based on EPRI fleet reports. | Amber because source reports and plant data are needed. |
| Framework `eta` 28,000 equivalent fired hours | Local framework Appendix B.7. | Amber because coating system and duty cycle are asset-specific. |
| Path-specific threshold sampling | Local framework Sections 3.2 and 3.3. | Green for architecture, Amber for calibration. |
| Fuel contaminant severity | Local framework Section 3.2; NASA stationary gas turbine TBC work. | Amber because fuel and deposit chemistry need data. |
| `P_TBC` outage link | Local framework Section 3.2.2. | Amber because forced outage conversion needs calibration. |

External references used for validation:

- NASA NTRS, "Thermal barrier coating experience in the gas turbine engine": https://ntrs.nasa.gov/citations/19950019705
- NASA NTRS, "Thermal Barrier Coatings for Advanced Gas Turbine and Diesel Engines": https://ntrs.nasa.gov/citations/20000003013
- NIST/SEMATECH e-Handbook, "Weibull Distribution": https://www.itl.nist.gov/div898/handbook/apr/section1/apr162.htm

## Open Questions Before Investment Use

Before using this factor in an investment committee deck, answer these:

| Question | Why it matters |
| :--- | :--- |
| What exact TBC system is on the blades and vanes? | Coating type and repair history drive life. |
| Did the last HGP replace, repair, or simply inspect coated parts? | The reset assumption depends on actual work scope. |
| Are borescope photos or inspection findings available? | Actual coating condition is better than a generic Weibull prior. |
| Is firing temperature measured, estimated, or inferred from load? | Time-at-temperature is only useful if the temperature proxy is credible. |
| Are fuel contaminants or deposits known? | Contaminants can accelerate coating attack. |
| How should starts, trips, and load swings change TBC exposure? | Thermal cycling severity needs calibration. |
| Should `beta` and `eta` be sensitivity-tested? | They strongly control failure timing. |
| How does a TBC failure translate into repair scope and outage days? | Financial impact depends on whether parts can be repaired or must be replaced. |

## One-Sentence Takeaway

TBC life is the model's way of tracking whether hot-section coatings are still protecting blades and vanes; the framework uses a Weibull model so coating failure risk rises probabilistically with severity-weighted time-at-temperature instead of failing on one fixed date.
