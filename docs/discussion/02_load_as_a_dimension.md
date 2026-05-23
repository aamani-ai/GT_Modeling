# 02. Load Level as a Missing Dimension

> **Status**: Open. Exploring the concept; not yet a committed part of methodology.
>
> **Folder context**: This is a discussion doc (per `docs/discussion/README.md`). It explores what *load level* should mean as a first-class concept in the gas plant model, distinct from operating mode, regime, and policy mode.

---

## §1. What prompted this discussion

Two converging signals from recent work surfaced load as a distinct concept that the model is missing:

1. **The 2026-05-22 advisory conversation** with Siddharth Deshpande explicitly flagged that gas turbine degradation is driven not only by operating hours but significantly by **load percentage** and **ambient temperature**. Running closer to max output (or peak fire) puts disproportionate stress on the unit. Load *swings* from intraday dispatch changes also matter. Siddharth shared a research paper on load and temperature dependency for turbine fatigue and creep, scheduled for incorporation into the model.

2. **The subsequent project recap** that surfaced the regime concept also surfaced an adjacent confusion: within a given operating mode (3×CC / 2×CC / 1×CC), the plant isn't running at a single point — it's running at *some load level*, and that load level matters for heat rate, degradation, fuel consumption, and emissions. The current model implicitly assumes 100% of mode capacity at all times. That assumption is silent, never named, and quietly wrong.

The current model captures:
- Operating mode (3×CC / 2×CC / 1×CC) — categorical, hour-by-hour
- Policy mode (A / B / C) — modeling abstraction over operator wear preferences

The current model does *not* capture:
- **Load level** — continuous intensity within the chosen mode
- **Regime** — strategic operating posture (separate discussion, see `01_regime_concept.md`)

This doc explores what load as a first-class concept would mean and what it would take to commit to it.

---

## §2. What we mean by load level (preliminary)

A **load level** is the **continuous fraction of available capacity** at which the plant is producing in a given hour, given its chosen operating mode.

Formally:

```
   load_level(t) ∈ [load_min, load_max]
   where load_max = 1.0 (full load) or slightly higher (peak fire)
         load_min = ~0.5 (typical minimum stable load for CCGT)
   
   MW_produced(t) = load_level(t) × mode_capacity(operating_mode(t), ambient(t))
```

Examples of load levels at a given operating mode:

- **3×CC at 100% load** — full output, max efficiency at design conditions
- **3×CC at 70% load** — partial output, heat rate ~1.07× full-load HR
- **3×CC at 50% load** — minimum stable load, heat rate ~1.16× full-load HR
- **3×CC at peak fire** — over-firing for short bursts, ~3–5% above nameplate, significantly accelerated wear
- **1×CC at 80% load** — typical when serving cogen demand below 1×CC's full capacity

Load level is *not* an hour-by-hour categorical decision (like operating mode). It is a *continuous* variable that the dispatch process selects from the available range, conditioned by the operating mode's capacity envelope, the plant's minimum stable load, and economic / contractual / grid signals.

---

## §3. Why load is distinct from the three other concepts

The "mode" vocabulary in this codebase is already crowded. It is important to be explicit about why load is its own thing, not subsumed by any of the existing concepts.

| Concept | What it is | Type | Cadence | Where in the code |
| :--- | :--- | :--- | :--- | :--- |
| **Regime** | Strategic operating posture (business positioning) | Categorical or vector | Slow (weeks–seasons) | Not yet built; see `01_regime_concept.md` |
| **Policy mode** | Operator's wear–revenue trade-off preference | Categorical (modeling abstraction) | Static per simulation | `wear_penalty_mult` in N4 |
| **Operating mode** | Physical configuration — how many CTs are firing | Categorical | Hour-by-hour | `MODES` dict in N4 |
| **Load level** | Continuous intensity within the chosen mode | **Continuous** (% of mode max) | Hour-by-hour | **Nowhere — currently assumed 100%** |

### Why load is not the same as operating mode

Operating mode is *categorical* — a discrete configuration choice (3×CC vs 2×CC vs 1×CC). Load is *continuous* — a fraction of whatever capacity the chosen mode provides. They have completely different mathematical structures:

- Mode pick is a *unit commitment* decision (which CTs are firing)
- Load level is an *economic dispatch* decision (how hard to push the chosen configuration)

These are distinct stages in any real dispatch optimization (UC then ED). Collapsing them into one — as the current model does by assuming load = 100% — loses information that a real plant operator uses every hour.

### Why load is not the same as regime

Regime defines *typical load patterns* over a long horizon, not the exact load at each hour. A peaker regime implies *max-load when running*; a frequency regulation regime implies *swinging load*; a baseload regime implies *steady high load*. But these are *patterns*, not point values. Within a given regime, the load at hour 14 of day 234 is still a specific dispatch decision.

Regime constrains the *distribution* of load levels you'd expect to see; load level is the realized value at each hour.

### Why load is not the same as policy mode

Policy mode is a *modeling abstraction* over the operator's wear management preference (A = run hard, C = preserve wear). Load is the *physical realized intensity*. The operator's policy could *influence* load decisions (a Policy C operator might prefer 80% load over 100% load even when 100% is economic, to reduce stress), but load itself is a real physical quantity, not a modeling abstraction.

### Why this distinction has been quietly costly

The current model treats the dispatch decision as binary: either you run at mode's full capacity, or you're offline. This implicit "100% load when on" assumption is a known simplification but has never been named as such. Without naming it, it propagates silently into:

- Heat rate calculations (uses mode HR as if load = 100%)
- Fuel consumption (computed from full capacity × HR)
- Degradation accumulation (load-percent dependency missing)
- Spark spread economics (no part-load alternative considered)
- Revenue projections (no "throttled" hours)

Each of these is partly wrong because load isn't being modeled.

---

## §4. Why we think load matters (the gaps it fills)

### 4.1 Part-load heat rate

Real CCGT heat rate is a strong function of load. The framework's reference doc (`extra/performance_and_risk_framework.md` §4.6) actually fits a polynomial for part-load HR:

```
   HR_multiplier(L) = 2.648 - 4.296×L + 2.648×L²   for L ∈ [0.5, 1.0]
   
   Yielding:
   1.000×  at 100% load
   1.015×  at  90%
   1.038×  at  80%
   1.068×  at  70%
   1.107×  at  60%
   1.162×  at  50% (minimum stable load)
```

A plant running 3×CC at 60% load has an *effective heat rate* ~10.7% worse than its full-load HR. The current model doesn't see this. A more efficient dispatch (e.g., 2×CC at 100% instead of 3×CC at 60%) might be the *correct* operator choice on a given hour, but the model can't even evaluate that comparison.

### 4.2 Load-dependent degradation

Per Siddharth at the 2026-05-22 meeting:

> *"Gas turbine performance degradation is driven not only by operating hours but significantly by load percentage and ambient temperature. High ambient temperatures and high-load operation put additional stress on the unit."*

The physical chain:

```
   High load (close to peak fire) → higher metal temperatures
                                  → higher creep rate
                                  → higher fatigue per cycle
                                  → accelerated EOH consumption
   
   High ambient temperature  → reduced delta-T (inlet to combustion)
                             → unit "works harder" for same output
                             → additional stress for same MWh
   
   The two effects compound: high load + high ambient = disproportionate stress
```

The current model is *fired-hours-driven*. Two plants with identical fired hours but different load profiles (one always at 60%, one always at 100%) would degrade identically in the model. In reality they degrade quite differently. This is a known calibration gap that load as a dimension would close.

### 4.3 Frequency regulation regime is invisible

A plant in frequency regulation regime *is defined by* its load swings — fast load changes responding to grid frequency. Without a load dimension, "frequency reg regime" and "baseload regime at the same average load" look identical to the model. The cycling stress, the partial-load efficiency penalty, and the ramp-related wear are all invisible.

This is the most explicit "regime is hollow without load" example. You cannot model a frequency reg regime without modeling load swings within hours.

---

## §5. Nuances worth being careful about

### 5.1 Load is constrained by both physics and contract

Load is not freely chosen across [0, 1]. It is bounded:

- **Below by minimum stable load** (typically 50% for CCGT — below this, combustion becomes unstable and the unit must offline)
- **Above by mode max capacity** (which is itself ambient-dependent — high ambient temps reduce max)
- **Above by peak fire limits** (over-firing limited in duration; OEMs typically cap peak fire to 10% of operating hours)
- **By ramp rate** (load can't change instantly; CCGT ramp rates ~10–30 MW/min)
- **By must-run contractual obligations** (cogen DHTS sets a load *floor* for some hours)
- **By dispatch instructions** (grid operator may direct a specific MW output)

Load is *chosen* within these constraints. Any model that treats load as continuous over [0, 1] without these constraints will produce nonsense.

### 5.2 Load patterns are themselves a regime signal

The *distribution* of load levels over time tells you something about the regime:

```
   Baseload regime         → load distribution: tight, high (85–95%)
   Peaker regime           → load distribution: bimodal (100% or 0%)
   Mid-merit               → load distribution: spread across 60–100%
   Frequency regulation    → load distribution: high variance within hours
   Cogen (DHTS-bound)      → load distribution: shaped by steam demand
```

This means load and regime are *related* — regime sets the typical pattern; load is the realized value — but they are still distinct concepts. Regime is the *characterization*; load is the *measurement*.

### 5.3 The load–temperature coupling

Per §4.2, load and ambient temperature *interact* in their degradation effect. You cannot treat them as independent additive contributions; the stress is *multiplicative* in the worst-case combinations.

This means any load-aware degradation model also has to be ambient-temperature-aware. They come together or not at all.

### 5.4 Peak fire as a distinct operating regime within "max load"

"Peak fire" or "over-firing" is the practice of running the turbine inlet temperature *above* design point to extract 3–5% extra power output. This is:

- Time-limited (usually <10% of operating hours per OEM agreement)
- Disproportionately wear-intensive
- Economically attractive in extreme price events (Uri-class, ERCOT scarcity)
- Often subject to specific contract terms

The current load representation (continuous fraction of nameplate) doesn't capture peak fire well. A "load > 1.0" interpretation works mathematically but loses the *contractual / wear* distinction. May need a separate flag or sub-category.

### 5.5 Load is what the operator actually decides

Of all the four concepts (regime, policy mode, operating mode, load), load is the one that the operator *directly chooses* every hour. Operating mode is downstream of load (you wouldn't fire 3 CTs if you only need 60 MW of output). Regime is the slow strategic context. Policy mode is the operator's preference structure.

Load is *the* hour-by-hour decision variable that everything else conditions. This is worth noting because it suggests load deserves more attention in the model's dispatch logic than it currently gets (which is none).

---

## §6. Drawbacks of adopting load as a first-class concept

It would be irresponsible to introduce load without naming the costs:

1. **Changes the dispatch logic from "binary on/off per mode" to "optimize load within mode."** The current heuristic (`max(spark, 0) × capacity` per mode, pick the best mode) becomes more complex: now there's a continuous optimization layer. The simplest approach — run each mode at 100% — is exactly what we have today; anything more accurate requires actual optimization.

2. **Requires a part-load heat rate model.** The framework references a polynomial, but the model doesn't use it. Adding it means more parameter complexity per asset.

3. **Requires a load-temperature dependent degradation model.** This is the Friday meeting action item. It's not trivial — needs calibration against real data, otherwise it's just adding parameters without adding fidelity.

4. **Computational cost.** A continuous-load dispatch optimization is heavier than mode-pick. For a 9-year × 3-mode simulation, the cost compounds.

5. **Cross-coupling with regime.** Once load is part of dispatch, regime-conditional load distributions become a real thing — which means committing to regime as a methodology piece becomes more pressing.

6. **Calibration burden.** More degrees of freedom = more risk of overfitting. Without good historical load data per hour (not just daily totals), calibration is hard.

---

## §7. Open questions

Things we don't yet know but will need to know before committing:

1. **What representation does load take in the model?** A single number per hour? A within-hour profile (for frequency-reg regimes)? Both?

2. **Do we use the part-load HR polynomial from the framework, or fit our own?** The polynomial in `performance_and_risk_framework.md` §4.6 is GE 7FA-derived. Lockport's CTs are F-class but the specific multiplier might differ.

3. **How is load *chosen* in the model?** Is it an optimization output (the dispatch optimizer picks load), or a heuristic (e.g., always 100% unless cogen demand sets a lower floor)?

4. **What's the relationship to operating mode in the dispatch logic?** Today, mode is picked per hour. With load, the choice is *(mode, load)*. Does the optimization consider all combinations? Or does mode get picked first, then load adjusted?

5. **What load data do we have?** MOR gives daily MWh but not per-hour load. Without per-hour load data, we can't calibrate against realized load levels.

6. **How do we handle peak fire?** As load > 1.0, or as a separate flag/category? Each has trade-offs.

7. **What's the validation story?** If we add load as a dimension, how do we know the model's load decisions match reality? What's the ground truth?

8. **Does this require an ADR?** Probably yes — committing to a load representation, a heat-rate model, and a degradation model is a substantive choice with downstream consequences. The ADR would be the artifact that promotes this from discussion to methodology.

9. **Does this interact with the regime ADR (when that gets written)?** Yes — regime-conditional load distributions are a real thing. The two ADRs may need to be written together, or one may need to wait for the other.

---

## §8. What "committed" would look like

If we eventually decide load is real and worth adopting, here's what would happen:

| Artifact | Change |
| :--- | :--- |
| `docs/methodology/architecture.md` | Add load as part of the dispatch decision; update §5.2 (the 12-step daily loop) to show load selection alongside mode pick |
| `docs/methodology/dispatch_mechanics.md` | New section on load level mechanics — how it's chosen, how it conditions HR, how it conditions degradation |
| `docs/methodology/glossary.md` | Formal definitions of load level, operating point, peak fire, minimum stable load |
| `docs/methodology/pnl_ledger.md` | Update fuel cost calculation to use load-conditional HR (part-load multiplier) |
| `docs/methodology/modeling_flow.md` | Update Step 4 (forward projection) to acknowledge load as a tactical decision |
| `docs/decisions/` | New ADR documenting the load representation, heat-rate model, and degradation model choices |
| `data/assets/lockport/operating_profile.yaml` | Add part-load HR multiplier (or polynomial coefficients); add minimum stable load; add peak fire policy |
| `notebooks/` | Update N4 dispatch logic to include load as a decision variable; possibly add a notebook for load-aware degradation calibration |
| This doc (`02_load_as_a_dimension.md`) | Status updated to "Graduated to methodology" |

The order matters: the ADR is the gating step. Until there's an ADR, the discussion stays in this folder.

---

## §9. Where load would *not* go

To be clear about scope, the following are *not* what load would touch:

- The Max − CL − EL causal decomposition (per `gas_plant_workflow.md`) — load conditions *parameters within* the decomposition; it doesn't add a new bucket
- The hazard team's EL pipeline — load doesn't change what hazards exist
- The two-output view (revenue + risk arms) — load conditions both arms but doesn't restructure them
- The status taxonomy or audit trail — load values are data; they get tagged like anything else

The concept is targeted: it adds a continuous tactical dimension to the existing mode-pick logic without restructuring the rest of the framework.

---

## §10. Working notes

A space for thoughts as they arise. Not committed; just captured.

- The "binary 100% load when on" assumption in the current model is a *known simplification* but isn't named anywhere. That's arguably as much a documentation gap as a modeling gap. Even before load is committed as a dimension, a caveat saying "load is implicitly 100%" should probably be added to the existing methodology docs.
- The part-load HR polynomial from `performance_and_risk_framework.md` §4.6 is GE 7FA-derived. Lockport's CTs (F-class vintage 1992) may have slightly different characteristics. Worth checking before adopting the polynomial wholesale.
- The relationship between load and operating mode is interesting: at low MW output requirements, the *correct* dispatch choice is often a lower-mode-at-high-load rather than a higher-mode-at-low-load. The model's current binary-load assumption forces "higher mode" picks that don't reflect what a real operator would do.
- The frequency regulation case (§4.3) is the cleanest motivating example: there is no way to model freq-reg regime without modeling load swings. Until then, the "regime" concept is hollow for that specific case.
- Wisely, the Friday meeting action item is *the temperature dependency*, not load by itself. That suggests the natural first step is to add temperature-conditional degradation (which is part of what load + ambient enables), and then load itself follows as the harder concept.
- One pragmatic intermediate: instead of fully continuous load, introduce *3 load bands per mode* (low / medium / high — like 60% / 80% / 100%). This sacrifices some fidelity for tractability. Worth considering as a stepping stone.
- The "operating point = (mode, load)" terminology from §2 of `01_regime_concept.md`'s updated framing is useful because it explicitly names the tuple that gets decided each hour. Worth using consistently.

---

## §11. Next steps for this discussion

In rough order:

1. **Add a caveat to existing methodology docs** acknowledging that the current model assumes 100% load when on. This is independent of any load-modeling work and just makes the implicit assumption explicit.
2. **Get hourly load data from MOR / SCADA** (or determine whether it's available). Without it, calibration is impossible.
3. **Decide on representation** (continuous vs banded) and propose an ADR.
4. **Coordinate with the regime ADR** — these two are deeply coupled and probably benefit from being designed together.
5. **Pull the load-temperature dependency paper** Siddharth shared and incorporate it as a starting point for the degradation model.

None of this is blocked; none of it is in this week's scope. The point of writing this doc is to preserve the thinking so the eventual ADR has a record of what was considered, and to flag the "100% load when on" assumption as a *known* simplification rather than an invisible one.

---

## §12. Cross-references

- `docs/discussion/01_regime_concept.md` — regime as a distinct posture concept; the doc that motivated naming load as a separate axis
- `docs/discussion/03_four_concepts_vocabulary.md` — the cheatsheet mapping all four concepts (regime, policy mode, operating mode, load) on their two orthogonal dimensions
- [`04_industry_vocabulary_and_references.md`](04_industry_vocabulary_and_references.md) **§3.4 + §3.5** — *industry equivalents for load level* (load point, set point, % MCR, part-load operation, peak fire, minimum stable load, turn-down ratio) and authoritative references (GE GER-3620, GER-3567, ANSI/ASME PTC 22, Kumar 2012). Also §3.5 on how ambient conditions are embedded in our framing rather than first-class.
- `docs/methodology/architecture.md` — the engine that currently lacks load as a dimension
- `docs/methodology/dispatch_mechanics.md` — where the load mechanics would eventually be documented
- `docs/methodology/extra/performance_and_risk_framework.md` §4.6 — the part-load HR polynomial that already exists in the framework reference
- `docs/extra/tasks_history/` — the 2026-05-22 Friday meeting notes that surfaced this gap
