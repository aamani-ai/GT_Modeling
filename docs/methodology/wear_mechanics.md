# Wear Mechanics — the state vector & step [8] (`update_stress`), with the maths

> **What this doc is.** The deep-dive on the **engineering heart** of the model: the `PlantState` vector and **step [8] of the daily loop (`update_stress`)** — how a day's run-hours + starts become *wear*, and how each of the 9 accumulators maps to a specific consequence (heat rate / failure hazard / inspection timing). It's the *state-evolution* companion to [`outage_mechanics.md`](outage_mechanics.md) (steps 1–2) and [`dispatch_economics.md`](dispatch_economics.md) (the per-hour margin), and expands [`architecture.md`](architecture.md) §5.1 + [`flowcharts.md`](flowcharts.md) chart 3.
>
> **Code**: `src/gt_engine/engine.py` — `PlantState`, `update_stress`, `p_forced_components`, `apply_inspection_reset`. Field meanings cross-ref [`architecture.md`](architecture.md) §5.1.

---

## §0. Framing — the state vector is the model's *memory*

`PlantState` is the only thing that carries day → day. **Step [8] (`update_stress`)** is the one place each day where *"the plant ran X hours and did Y starts"* becomes *"the plant is now this much more worn."* That is the **engineering→economics bridge**: more wear → worse heat rate (costs $) and higher failure odds (lost MWh + repair $) and a faster-ticking inspection clock.

It is **block-level** (the whole 3-on-1 plant is *one* state, not per-turbine — a v1 simplification; per-generator is `gaps_and_priorities.md` #9) and updates **once per day**.

The three field groups do three different jobs:

| Group | Fields | Job |
|---|---|---|
| **Stress accumulators** | 9 | the *wear* — drive heat rate, failure hazard, inspection timing |
| **Operational continuity** | `op`, `hrs_off`, `last_stype` | "on now? how long off?" → the start *type* |
| **Outage tracking** | `outage_days_remaining`, `outage_type` | the outage countdown (see [`outage_mechanics.md`](outage_mechanics.md)) |

---

## §1. The key view — which accumulator drives *what* (division of labour)

The 9 accumulators are **not** generic "wear that does everything." Each routes to **one** consequence:

```
hr_recov, fouling ─────────────────────────►  HEAT RATE      → higher fuel cost → fewer economic hours
df, dc, tbc_time/tbc_thresh, rotor_life ────►  FAILURE HAZARD → forced outages: lost MWh + repair $
eoh ────────────────────────────────────────►  INSPECTION TIMING → CI/MI downtime + LTSA $ + state RESET
hrsg_cycles ────────────────────────────────►  (tracked, not wired in v1)
```

| Consequence (the "thing adjusted") | Driven by | Mechanism |
|---|---|---|
| **Heat rate** ($/MWh fuel) | `hr_recov`, `fouling` | `HR_degraded = HR_clean × (1 + hr_recov/100) × (1 + fouling/100)` |
| **Failure hazard** (`P_forced`) | `df`→P_comb · `dc`→P_creep · `tbc_time` vs `tbc_thresh`→P_TBC · `rotor_life`→P_rotor | summed into `P_GT`, combined with HRSG/BG baselines |
| **Inspection timing** | `eoh` | CI/MI fire on EOH threshold (hard-stop) or calendar; `eoh` also meters the EOH-reserve $ |
| *(none yet)* | `hrsg_cycles` | accumulated + reset at MI, but `P_HRSG` uses a flat baseline, not the cycle count |

**Two distinct economic channels per consequence**: heat-rate accumulators thin the **margin** (more gas/MWh → fewer hours clear); hazard accumulators cause **random outages**; `eoh` triggers **scheduled maintenance**. Three separate cause→effect chains under one "wear" umbrella.

---

## §2. Group 1 — the 9 stress accumulators, field by field

### §2.1 The contractual clock
| Field | Physical meaning | Daily math | Drives | Reset |
|---|---|---|---|---|
| **eoh** | Equivalent Operating Hours — the *contract's* maintenance clock | `+= fired_hours + start_eoh`, where `start_eoh` = **cold 20 / warm 10 / hot 5** per start | inspection scheduling; EOH-reserve $ | not reset (lifetime clock); starts at **24,000** |

> A **start** ages the machine far more than an hour of running (a cold start = 20 equivalent hours). That's why heavy *cycling* ages a turbine fast.

### §2.2 Heat-rate degradation (affects $/MWh)
| Field | Physical meaning | Daily math | Reset |
|---|---|---|---|
| **fouling** | Compressor blades fouling (air contaminants) | exponential approach to a **2.5%** ceiling: `+= (2.5 − fouling) × (fired_hours / 2000)` — fast when clean, saturates near 2.5% | CI/MI **×0.3** (70% washed) |
| **hr_recov** | Other *recoverable* efficiency loss | `+= fired_hours × 0.001 %` | CI ×0.3, MI ×0.25 |

> "Recoverable" = cleaning/overhaul brings it back. So heat rate **creeps up between inspections, drops at each inspection** (see §6 for where that recovery is *costed*).

### §2.3 Physical damage → failure hazard (affects forced outages)
| Field | Physical meaning | Daily math | Drives | Reset |
|---|---|---|---|---|
| **dc** (creep) | Slow plastic deformation of hot metal under stress (Robinson, 0→1) | `+= 5e-6 × fired_hours_hot` (ambient-weighted, ADR-006) | `P_creep = 0.10 × max(0, dc − 0.50)²` (ADR-007) | CI ×0.5, MI →0 |
| **df** (fatigue) | Thermal-cycling micro-crack growth (Miner, 0→1) | `+= per start`: **cold 0.001 / warm 0.0005 / hot 0.0002** (+ a **trip** adds 8× cold, ADR-007) | `P_comb = 0.10 × max(0, df − 0.60)²` | CI ×0.5, MI →0 |
| **tbc_time** | Hours-at-temp on the current TBC coating | `+= fired_hours_hot` (ambient-weighted) | `P_TBC` (Weibull hazard) | MI →0 (new coating) |
| **tbc_thresh** | The *random* hours-at-temp this coating fails at | sampled from **Weibull(β=3, η=28,000)**; not accumulated | when `tbc_time ≥ tbc_thresh` → `P_TBC = 1` | MI: resampled |
| **rotor_life** | Heavy-rotor consumed life fraction (0.35→1.0) | `+= 1e-7 × fired_hours` | `P_rotor = 0.00003 × rotor_life` | MI ×0.5; starts at **0.35** |
| **hrsg_cycles** | HRSG thermal cycles (1 per start) | `+= 1 per start` | *not wired* (P_HRSG = baseline×aging) | MI →0 |

---

## §3. The two cumulative-damage laws (the "Robinson / Miner" labels)

Classic engineering "damage adds up until the part fails" models:
- **Creep — Robinson's rule**: `dc` is a **life fraction** = Σ `time / time-to-rupture` while hot. → 1 = creep failure.
- **Fatigue — Miner's rule**: `df` is a **life fraction** = Σ `cycles / cycles-to-failure` from cycling. → 1 = fatigue failure.
- **Creep–fatigue interaction**: they reinforce each other; the model captures it crudely — if `dc > 0.05 AND df > 0.05 AND dc+df > 0.7 (D_LIM)` → **halve both**. (Never fires on realistic Lockport paths — dc+df stays small.)

Both are **linear cumulative-damage** proxies; real creep is Larson-Miller/Arrhenius (exponential in metal temp) and real fatigue is rainflow-counted — v1 trades that for simple, transparent accumulation (good for *direction & feedback*, not absolute life).

---

## §4. Groups 2 & 3 — continuity and outage tracking

| Field | Meaning | Role |
|---|---|---|
| **op** | online now? | set by the day's dispatch; used next day for trip-vs-not |
| **hrs_off** | hours since last shutdown | decides start **type**: `<8` hot, `<72` warm, `≥72` cold |
| **last_stype** | most recent start type | record-keeping |
| **outage_days_remaining** | days left in current outage | the countdown ([`outage_mechanics.md`](outage_mechanics.md)) |
| **outage_type** | CI / MI / forced_* / "" | what kind of outage / "available" |

`hrs_off` is what links idleness to cost: idle 3+ days → next start is **cold** (expensive, high `df`/`eoh`); cycling daily → **hot** starts (cheap).

---

## §5. The driver split — hours vs starts (why the fields are separate)

Different operating patterns wear different parts, which is *why* there are separate accumulators:

| Grows with **fired hours** (running time) | Grows with **starts** (cycling) |
|---|---|
| `fouling`, `hr_recov`, `dc`, `tbc_time`, `rotor_life`, (hours part of `eoh`) | `df`, `hrsg_cycles`, (start-EOH part of `eoh`) |

So a **baseload** year grows the "hours" group; a **heavy-cycling/peaking** year grows the "starts" group. A start is a double hit — it adds `df` *and* a chunk of `eoh` (and warming fuel). This is the model's way of saying "cycling is harder on a turbine than steady running."

---

## §6. Recovery & cost — what washing/overhaul *is counted as*

This answers "where does the cleaning effect go?":

- **The recovery (fouling/HR drop) happens *only* at CI/MI inspection resets** — there is **no standalone water-wash event** in v1. `apply_inspection_reset` is the only thing that reduces the accumulators.
- **The cost is the inspection cost** (CI ≈ $3.75M total / ~$0.94M owner; MI ≈ $30M / ~$10.5M owner) **+ downtime + the HR-guarantee penalty** — all in the **LTSA cost streams** (`ci_owner_cum` / `mi_owner_cum` / `hr_penalty_cum`). It is **not** a separate "washing" or routine-O&M line.
- **Two honest gaps**:
  1. **No routine compressor wash** — real plants wash the compressor a few times a year (cheap, little downtime) and recover fouling *between* inspections; v1 recovers it only at the infrequent CI/MI, so it **slightly over-states mid-cycle fouling**.
  2. **No Fixed-O&M layer** — routine maintenance/labour isn't costed (only fuel + RGGI + VOM + LTSA). Gap **#6** in [`gaps_and_priorities.md`](gaps_and_priorities.md).

So: **recovery = inspection resets (LTSA/scheduling), cost = LTSA inspection streams** — not O&M, not a standalone wash.

---

## §7. The math in one block + the constants

```text
update_stress(state, fired_hours, starts, fired_hours_hot):
  start_eoh   = Σ START_EOH_COST[s]            # cold 20 / warm 10 / hot 5
  eoh        += fired_hours + start_eoh
  fouling    += (2.5 − fouling) × fired_hours / 2000     (capped at 2.5)
  hr_recov   += fired_hours × 0.001
  dc         += 5e-6  × fired_hours_hot          ← hot-section, ambient-weighted
  df         += FATIGUE_PER_{COLD,WARM,HOT}      per start
  if dc>0.05 and df>0.05 and dc+df>0.7:  dc*=0.5; df*=0.5      # creep-fatigue interaction
  tbc_time   += fired_hours_hot                  ← hot-section, ambient-weighted
  hrsg_cycles += 1 per start
  rotor_life += 1e-7  × fired_hours
```

| Constant | Value | | Constant | Value |
|---|---|---|---|---|
| START_EOH_COST (cold/warm/hot) | 20 / 10 / 5 | | FOULING asymptote / tau | 2.5% / 2000 h |
| hr_recov rate | 0.001 %/h | | CREEP_RATE | 5e-6 /h |
| FATIGUE per start (c/w/h) | .001/.0005/.0002 | | ROTOR_LIFE rate | 1e-7 /h |
| TBC Weibull β / η | 3 / 28,000 | | D_LIM | 0.7 |
| P_comb / P_creep scale, inflection | 0.10, df>0.60 / dc>0.50 | | initial EOH / rotor | 24,000 / 0.35 |

**Resets** — CI: `dc×0.5, df×0.5, fouling×0.3, hr_recov×0.3`. MI: `dc=0, df=0, tbc_time=0 (+ resample tbc_thresh), hrsg_cycles=0, rotor×0.5, fouling×0.3, hr_recov×0.25`.

---

## §8. Assumptions (be honest about these)

- **Rates are mostly Bucket-B placeholders** — generic F-class / Athens-prototype defaults, `assumed_industry` LOW, **not Lockport-measured** (ADR-002). Right *shape*, placeholder *magnitude*; Phase L Monte Carlo sweeps them.
- **Forms are simplified physics proxies** (linear creep/rotor, per-start fatigue, exponential fouling, Weibull TBC) — capture direction & feedback, not absolute component life.
- **Initial state is a convention** (EOH 24,000 "post-HGP start", rotor 0.35).
- **Wired vs latent**: `df`/`tbc_time`/`rotor_life`/`dc` → hazards (wired); `hr_recov`/`fouling` → heat rate (wired); `eoh` → inspections (wired); **`hrsg_cycles` is tracked but not consumed** (HRSG hazard is a baseline). For low-CF Lockport the GT-side hazards stay near zero (sub-threshold) — physically correct.

---

## §9. Worked example — one day

**Normal winter day**: `fired_hours = 24`, no starts, ambient ~22°F → `fired_hours_hot ≈ 22.9`:
```
eoh        += 24 + 0           → +24
fouling    += (2.5−2.1)×(24/2000) = +0.0048%
hr_recov   += 24×0.001         = +0.024%
dc         += 5e-6 × 22.9      = +0.000115     (ambient-weighted; cold → factor<1)
tbc_time   += 22.9             (cold day → <24)
rotor_life += 1e-7 × 24        = +0.0000024
df, hrsg_cycles: unchanged (no starts)
```
**Same day but with a cold start** (fired 20, one cold start):
```
eoh         += 20 + 20 = 40    (start_eoh = 20 for a cold start — the double hit)
df          += 0.001
hrsg_cycles += 1 ; last_stype = "cold"
```

**Across a year**: the hours-group climbs steadily and the starts-group jumps at each start, the heat rate creeps up (fouling toward 2.5% + hr_recov), `P_forced` inches up — until an **inspection** fires, which resets the accumulators (and pays the LTSA cost), and the cycle restarts. That sawtooth is the whole engineering story.

---

## §10. Cross-references
- [`architecture.md`](architecture.md) §5.1 (state vector), §5.4 (`P_forced`), §5.6 (inspection resets)
- [`flowcharts.md`](flowcharts.md) chart 3 (wear accumulation), chart 4 (wear→failure), chart 8 (two meters)
- [`outage_mechanics.md`](outage_mechanics.md) · [`dispatch_economics.md`](dispatch_economics.md) — the sibling step deep-dives
- [`implementation/gt_engine/03_function_reference.md`](../implementation/gt_engine/03_function_reference.md) (`update_stress`, `p_forced_components`, `apply_inspection_reset`)
- ADRs [002](../decisions/002-lockport-specific-vs-generic-calibration.md) (Bucket-B), [006](../decisions/006-ambient-weighted-wear.md) (ambient weighting), [007](../decisions/007-creep-wiring-and-trip-wear.md) (creep wiring + trip wear)
- [`gaps_and_priorities.md`](gaps_and_priorities.md) #6 (Fixed-O&M gap), #9 (per-generator state)
