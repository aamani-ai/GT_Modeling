# Architecture — Lockport Gas Turbine Digital Twin (v1)

> **Read [`pnl_ledger.md`](./pnl_ledger.md) first.** It's the single-table view of every revenue and cost component that affects Lockport's economics, what v1 models, what v1 ignores, and rough annual magnitudes. *This* doc explains how each modeled component actually works.
>
> **Audience**: someone reading this cold who needs to understand what the model does, why it exists, what it eats, what it produces, and where its limits are. Assumes no prior context from earlier conversations.
>
> **Scope**: the v1 build that lives in this repo today — Phases A–J of [`consolidation_plan.md`](../plans/consolidation_plan.md). Phase K (graduate to `src/`) and Phase L (Monte Carlo) are scoped at the end but not yet built.
>
> **Sister docs**:
> - [`pnl_ledger.md`](./pnl_ledger.md) — the one-glance economic ledger (entry point)
> - [`dispatch_mechanics.md`](./dispatch_mechanics.md) — deep dive on the dispatch decision (operating mode × policy mode); read after §5 of this doc
> - [`backtest_findings.md`](./extra/backtest_findings.md) — modeled vs real MOR data comparison; revealed steam-only mode and quantifies 2.22× over-commit
> - [`gaps_and_priorities.md`](./gaps_and_priorities.md) — what v1 ISN'T and what to fix first
> - [`glossary.md`](./glossary.md) — term definitions
> - [`../decisions/README.md`](../decisions/README.md) — ADRs (substantive choices)
> - [`../assumptions/README.md`](../assumptions/README.md) — status taxonomy
>
> **A note on terminology**: the word "mode" gets used for two completely different things in this model — **operating mode** (`3×CC` / `2×CC` / `1×CC`, the physical config) and **policy mode** (`A` / `B` / `C`, the wear-penalty curve). They live on different axes. This doc uses both terms with the qualifier; [`dispatch_mechanics.md §1`](./dispatch_mechanics.md) is the full disambiguation if you find any usage ambiguous.

---

## §1. What we are trying to do

### §1.1 The asset

**Lockport Energy Associates LP** (EIA Plant ID 54041) is a 221 MW natural gas combined-cycle cogeneration plant in Lockport, NY, online since 1992. The configuration is "3-on-1": three combustion turbines (CTs, F-class vintage) exhaust into one heat-recovery steam generator (HRSG) feeding a single steam turbine (ST). The plant sells electricity into NYISO Zone A and supplies process steam to an industrial host under a PURPA-era contract (the "DHTS" — Daily Heat Tape Schedule).

The plant has three **operating modes** (physical configurations of how many CTs are running):

| Operating mode | What runs | Block capacity | Block heat rate |
|---|---|---:|---:|
| **3×CC full** | 3 CTs + 1 ST | 221.3 MW | 8,901 Btu/kWh |
| **2×CC** | 2 CTs + 1 ST | 172.6 MW | 9,598 Btu/kWh |
| **1×CC** | 1 CT + 1 ST | 123.9 MW | 10,424 Btu/kWh |

(All three numbers from MOR-derived `real_observed` values in [`operating_profile.yaml`](../../data/assets/lockport/operating_profile.yaml).)

**Don't confuse operating mode with policy mode**: operating mode (3×CC / 2×CC / 1×CC) is the physical configuration picked per hour by the dispatcher; policy mode (A / B / C, introduced in §5.5) is the investor-policy wear-penalty curve that influences when the dispatcher will start the plant. Both are called "mode" colloquially; this doc keeps them distinguished. See [`dispatch_mechanics.md §1`](./dispatch_mechanics.md) for the full disambiguation.

### §1.2 The modeling problem

A gas turbine isn't a free-running revenue machine. Every fired hour, every start, every cycle compounds engineering wear that **eventually triggers expensive Long-Term Service Agreement (LTSA) costs**: scheduled inspections (CI / MI), forced outages, heat-rate penalties, availability penalties, and start-overage charges. These costs are highly **non-linear in dispatch behavior** — an extra 100 starts/year can move LTSA cost by millions even when the marginal spark margin looks attractive.

The dispatch decision and the LTSA cost are **coupled through a state vector that evolves daily** based on what happened yesterday. We can't decide whether to run today without knowing what wear we've already accumulated; we can't price LTSA cost without simulating dispatch; we can't simulate dispatch without knowing degradation; and on and on.

**That's the problem this model solves**: a tractable approximation of the engineering-dispatch-LTSA feedback loop, so you can ask **what-if questions** like "what if we run aggressively (Mode A)?" vs "what if we self-curtail near inspections (Mode C)?" and get coherent answers on spark, LTSA, and net P&L.

### §1.3 What v1 produces

A `model_card.md` that, for a single chosen asset (Lockport) over a single chosen horizon (9 years 2017–2025), reports:

- **Per mode** (A / B / C): total spark margin, total LTSA owner-uncovered cost, net P&L, inspection count, forced-outage count, mode-comparison delta
- **LTSA stream breakdown**: where the cost went (fixed fee / EOH reserve / inspections / overage / penalties / forced outage)
- **Assumption-status distribution**: how much of the model's inputs are `real_observed` vs `placeholder` vs `assumed_industry`
- **MOR backtest table**: model 2024 generation vs MOR-observed 192,494 MWh; mode distribution vs 65/26/9 split; cold-start frequency vs ~7/yr
- **Caveats list**: known limitations of v1

Plus a parquet bundle with per-day state, LTSA accruals, inspection events, and forced-outage events that downstream analysis can pivot on.

---

## §2. The mental model — three layers, one feedback loop

> **Visual companion**: [`flowcharts.md`](flowcharts.md) renders this loop and the wear/failure internals as Mermaid diagrams — start there if you think better in pictures, then come back for the words.

The whole model can be drawn as three layers and a clock:

```
         ┌─────────────────────────────────────────────────────────────┐
         │  ENGINEERING LAYER                                          │
         │  - Plant state vector (9 stress accumulators)               │
         │  - Heat-rate degradation (recoverable + non-recoverable)    │
         │  - Forced-outage probability P_forced from current state    │
         └─────────────────────────────────────────────────────────────┘
                 │
                 │  yesterday's closing state
                 │  feeds today's decision
                 ▼
         ┌─────────────────────────────────────────────────────────────┐
         │  DISPATCH LAYER                                             │
         │  - Hour-by-hour mode choice (3xCC / 2xCC / 1xCC / offline)  │
         │  - Spark = LMP − fuel cost − VOM − (mode wear penalty)      │
         │  - Twin: clean spark vs degraded spark (loss attribution)   │
         └─────────────────────────────────────────────────────────────┘
                 │
                 │  today's dispatch (fired hours, starts) updates
                 │  the stress accumulators
                 ▼
         ┌─────────────────────────────────────────────────────────────┐
         │  LTSA / CONTRACTS LAYER                                     │
         │  - 7 cost streams accrue daily (fixed, EOH, overage, etc.)  │
         │  - Inspection events trigger on EOH threshold + calendar    │
         │  - Forced-outage events sampled vs P_forced                 │
         │  - Cycle-end HR penalty on each inspection                  │
         └─────────────────────────────────────────────────────────────┘
                 │
                 │  cost-of-this-day rolls into model_card
                 ▼
         (advance clock by one day; repeat for 3,287 days × 3 modes)
```

A few framing facts to anchor on:

- **Block-level, not per-generator.** v1 treats the whole 3-on-1 CCGT as one engineering object with one state vector. Per-generator state (GEN1 / GEN2 / GEN3 / GEN4 separately) is a v2 concern. The trade-off: simpler v1 code; can't model "one CT down for maintenance, the other two running" — which is a real gap (see §7.5).
- **Daily grain.** State updates once per day. Dispatch decisions are hourly within the day. The daily grain is the smallest unit at which forced outage and inspection events can fire.
- **Single asset, single path.** v1 simulates one realization for one asset. Monte Carlo (multiple paths, P10/P50/P90) is Phase L; multi-asset is Phase v2+.
- **Historical replay, not synthetic scenario.** v1 plays the actual 2017–2025 LMP, gas, and weather history forward. The Phase L Monte Carlo replaces this with a synthetic scenario engine that samples paths.

---

## §3. Inputs — what we have to work with

Everything the model consumes is either a static **YAML** file (per-asset configuration with assumption-status tags) or a time-series **parquet** file (price/weather history). No other input modalities.

### §3.1 Static configuration — `data/assets/lockport/`

Seven YAML files describe Lockport (5 core + `capability_envelope` + `realized_operating_profile`, the two regime-decomposition dimensions added 2026-05 per ADR-003). Every leaf value carries a `{value, status, source, confidence?, caveat?, validation_path?}` schema per the status taxonomy.

| File | What it holds | Approx leaves | Real share |
|---|---|---:|---:|
| [`identity.yaml`](../../data/assets/lockport/identity.yaml) | Plant ID, name, lat/lon, owner, online date, NYISO node IDs | ~30 | ~100% real |
| [`engineering.yaml`](../../data/assets/lockport/engineering.yaml) | 4 generators (GEN1–GEN3 CTs + GEN4 CA-steam) with prime mover, fuel codes, nameplate, summer/winter derate, vintage, prime-mover-specific defaults | ~122 | mixed real + assumed |
| [`market_context.yaml`](../../data/assets/lockport/market_context.yaml) | NYISO market info (zone, eGRID subregion, RGGI applicability, gas hub treatment, ICAP eligibility) | ~40 | mixed |
| [`operating_profile.yaml`](../../data/assets/lockport/operating_profile.yaml) | Mode heat rates, cold-start warming gas, DHTS, mode classifier thresholds — MOR-derived | ~30 | mostly `real_observed` |
| [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml) | All 7 LTSA stream parameters + forced-outage coverage table + contract metadata | ~46 | **all `placeholder`** |

**Two important reads next to the YAMLs**:
- [`data/assets/lockport/caveats.md`](../../data/assets/lockport/caveats.md) — 12 sections of "things baked into the data that future-self / the team must remember" (e.g., cogen VOM markup is ×1.35; multi-mode dispatch produces different heat rates; dual-fuel switching modeled as never-fires in v1; v1 gas hub is Henry Hub per ADR-001).
- [`data/assets/lockport/provenance.md`](../../data/assets/lockport/provenance.md) — where each YAML value came from (file path + extraction method).

### §3.2 Time-series spine — `data/paths/lockport/`

Hourly or daily time series for the asset's market context. v1 consumes three of these directly; the others are reference for v2.

| File | What | Coverage | Used in |
|---|---|---|---|
| [`lmp_da_hourly.parquet`](../../data/paths/lockport/lmp_da_hourly.parquet) | NYISO DA LMP at Lockport node (PTID 23791) | 2017-01-01 → 2026-04-29 | N2, N3, N4 |
| [`gas_price_history.parquet`](../../data/paths/lockport/gas_price_history.parquet) | EIA daily spot at 8 hubs (we use Henry Hub for v1 per ADR-001) | 1997-01-07 → 2026-04-20 | N2, N3, N4 |
| [`weather_hourly.parquet`](../../data/paths/lockport/weather_hourly.parquet) | Open-Meteo ERA5 hourly at Lockport lat/lon | 1980-01-01 → 2026-01-01 | N3, N4 |
| `lmp_rt_intervals.parquet` | NYISO RT LMP 5-min intervals | — | reference (v2) |
| `lmp_west_zone_da.parquet` | NYISO Zone A West DA LMP | — | reference (v2) |
| `weather_forecast_seas5.json` | ECMWF SEAS5 seasonal forecast | — | reference (v2 / Phase L scenario engine) |

**Weather TZ trap** (documented in `data/paths/lockport/README.md`): the parquet stores timestamps as strings, not native TIMESTAMP. Load-time conversion required: `pd.to_datetime(df.index, utc=True).tz_convert("US/Eastern")`.

### §3.3 Tech-class defaults — `data/tech_class_defaults/`

Cross-asset reference table (not Lockport-specific) keyed by `(prime_mover_code, vintage_class, aero_derivative)`. For Lockport this resolves to `(CT, <2000, False)`, giving us VOM, baseline start costs, and other priors per Kumar 2012 + EIA-derived F-class statistics.

| File | What |
|---|---|
| [`dispatch_params_lookup.parquet`](../../data/tech_class_defaults/dispatch_params_lookup.parquet) | 20 rows × 35 cols; one row per `(prime_mover, vintage, aero)` combo |
| `dispatch_params_values.csv` | Human-readable companion |
| `refs/` | Audit trail of where each value came from |

Built originally in the `renewablesinfo` lab repo; copied here per the consolidation-plan D3 decision (copy not symlink).

### §3.4 Reference documentation

| Folder | What |
|---|---|
| [`docs/decisions/`](../decisions/) | ADRs — substantive decisions with full reasoning trail. Currently: ADR-001 (gas hub treatment) and ADR-002 (Lockport-specific vs generic-F-class calibration). |
| [`docs/assumptions/`](../assumptions/) | Status taxonomy + placeholder caveats. The 9-code grammar that every YAML leaf follows. |
| [`docs/extra/`](../extra/) | Prototype reference: `gas-turbine-digital-twin/` (the source code that informs our daily-loop convention) + `understanding_of_gas_turbine_digital_twin.md` (a long-form explanation of the prototype's mechanics). |
| [`docs/plans/consolidation_plan.md`](../plans/consolidation_plan.md) | The build plan: 5 locked decisions, 11 phases (A–L), status log. |
| [`docs/plans/consolidation_plan/notebooks/0{1,2,3,4}_*.md`](../plans/consolidation_plan/notebooks/) | Per-notebook cell-by-cell sketches written BEFORE each notebook was built. |
| [`docs/learning/`](../learning/) | Long-form learning material on gas turbines (read these before touching engineering parameters in v2). |
| [`docs/InfraSure_GT_DigitalTwin_v2.pdf`](../InfraSure_GT_DigitalTwin_v2.pdf), [`docs/InfraSure_ModelingFramework_V2.md`](../InfraSure_ModelingFramework_V2.md) | The original modeling framework and twin spec; foundational reference. |

---

## §4. What we are assuming

This is the most important section to be honest about. Every model is a stack of assumptions; the question is whether you've labeled them.

### §4.1 The status grammar

Every leaf value across the YAML files carries one of **9 status codes** (per [`assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md)):

| Code | Meaning |
|---|---|
| `real_observed` | Measured directly from the asset's data (MOR, EIA-860, SCADA) |
| `real_reported` | Pulled from a regulatory filing or contract document |
| `real_computed` | Derived from real_observed + a deterministic formula |
| `assumed_techclass` | A class-level default (e.g., F-class mean from Kumar 2012) |
| `assumed_vendor` | OEM-published spec for the equipment family |
| `assumed_industry` | A broader industry rule-of-thumb |
| `assumed_derived` | An assumption derived from another assumption (compound uncertainty) |
| `placeholder` | A typed value with no real source yet; awaiting data-room extraction |
| `not_applicable` | The field doesn't apply for this asset |

**Across all 268 leaves in the 5 Lockport YAML files**, the v1 distribution is:

| Status | Count | Share |
|---|---:|---:|
| `real_observed` | 31 | 11.6% |
| `real_reported` | 160 | 59.7% |
| `real_computed` | 22 | 8.2% |
| `assumed_industry` | 6 | 2.2% |
| `placeholder` | 47 | 17.5% |
| `not_applicable` | 2 | 0.7% |

**Headline**: 79.5% of inputs are real_*; 17.5% are placeholder (almost all in `ltsa_terms.yaml`). The model_card surfaces this distribution alongside the headline numbers so you never read a number without knowing how much of its provenance is real vs guessed.

### §4.2 The three buckets (per ADR-002)

A second axis cuts across the model's internals: **which constants are Lockport-specific vs generic-F-class vs awaiting-data-room.**

| Bucket | What | Examples |
|---|---|---|
| **A — Lockport-specific** (`real_*`) | Calibrated from Lockport's own data | Mode heat rates (MOR), LMP at PTID 23791, ambient derate from EIA-860, cold-start warming gas 2,537 MMBtu/start (MOR-observed) |
| **B — Generic F-class** (`assumed_*`) | Inherited from the prototype's Athens-calibrated defaults | State-evolution constants (`START_EOH_COST`, `FOULING_*`, `TBC_WEIBULL_*`, `HRSG_BASE_PROB_*`), creep/fatigue per start, hockey-stick inflection point |
| **C — Placeholder** (`placeholder`) | Numerically valid but not deal-realistic | All 7 LTSA stream parameters (fixed monthly fee $850K, CI cost $3.75M, MI cost $30M, etc.), forced-outage repair cost table |

[`docs/decisions/002-lockport-specific-vs-generic-calibration.md`](../decisions/002-lockport-specific-vs-generic-calibration.md) is the definitive inventory of which constant is in which bucket.

### §4.3 Decisions already locked

Per [`consolidation_plan.md`](../plans/consolidation_plan.md) §5 + the ADRs:

| Decision | What | Reference |
|---|---|---|
| **D1** | Prototype-as-reference, not copy-paste. We learn from it, we don't run it. | consolidation plan §5 |
| **D2** | YAML for static config; parquet for time series. No JSON for either. | consolidation plan §5 |
| **D3** | Copy data files into this repo, not symlinks. | consolidation plan §5 |
| **D4** | Lockport only for v1. No Athens. No multi-asset. | consolidation plan §5 |
| **D5** | Digest diligence-extractor outputs into YAML; don't import the extractor at runtime. | consolidation plan §5 |
| **ADR-001** | Gas hub = Henry Hub only for v1. Algonquin basis deferred to v2 (sparse history). | [001-gas-hub-treatment-v1.md](../decisions/001-gas-hub-treatment-v1.md) |
| **ADR-002** | Three-bucket calibration map. Cold-start warming gas correction applied to N3. | [002-lockport-specific-vs-generic-calibration.md](../decisions/002-lockport-specific-vs-generic-calibration.md) |

### §4.4 Stuff we know is wrong-ish but accept for v1

The cogen-VOM markup (×1.35), the synthetic must-run flag (coldest 20% of days), the HR-guarantee proxy (= 3×CC clean HR), the EOH-rate estimate for the maintenance scheduler (8 EOH/day flat), the dual-fuel switching (never fires in v1) — these are all known v1 approximations. Each is documented in either `caveats.md` or the relevant notebook's decision log.

---

## §5. The core engine — how the daily loop works

This is the heart of the model. Once you understand §5, the rest is bookkeeping.

> **Where the code lives.** The engine described in §5 was extracted from notebook 4 into an importable package, [`src/gt_engine/`](../../src/gt_engine/) — exposed as `run_path()` (over an injected market path) with `run_mode()` as the historical-replay wrapper. The line-by-line code walkthrough is in [`docs/implementation/gt_engine/`](../implementation/gt_engine/) (incl. a one-day worked example). The forward scenario engine that runs this over conditioned analog windows is [`src/forward/`](../../src/forward/) / [`docs/implementation/forward/`](../implementation/forward/).

### §5.1 The plant state vector

> **Worked-example deep dive**: [`wear_mechanics.md`](wear_mechanics.md) walks the state vector + step [8] (`update_stress`) field-by-field with the daily math, the accumulator→consequence map (which fields drive heat rate vs failure hazard vs inspection timing), the creep/fatigue laws, where washing/recovery is costed, and a one-day example.

Twelve fields, one Python dataclass, propagates from day N to day N+1:

```
┌─────────────────────────────────────────────────────────────┐
│ class PlantState (block-level for v1)                       │
├─────────────────────────────────────────────────────────────┤
│ STRESS ACCUMULATORS (9 fields, engineering):                │
│   eoh            float  Equivalent Operating Hours           │
│   hr_recov       float  Recoverable HR degradation %         │
│   fouling        float  Compressor fouling % (asymptote 2.5) │
│   dc             float  Creep damage (Robinson; 0 → 1)       │
│   df             float  Fatigue damage (Miner; 0 → 1)        │
│   tbc_time       float  Time-at-temp on TBC coating (hrs)    │
│   tbc_thresh     float  Weibull-sampled TBC failure thresh   │
│   hrsg_cycles    float  HRSG thermal cycles                  │
│   rotor_life     float  Rotor life consumed (0.35 → 1.0)     │
├─────────────────────────────────────────────────────────────┤
│ OPERATIONAL CONTINUITY (carries hour-by-hour):              │
│   op             bool   Currently online?                    │
│   hrs_off        float  Hours since last shutdown            │
│   last_stype     str    Last start type (hot/warm/cold)      │
├─────────────────────────────────────────────────────────────┤
│ OUTAGE TRACKING (added in N4):                              │
│   outage_days_remaining   int    Days left in current outage│
│   outage_type             str    CI / MI / forced_gt / etc. │
└─────────────────────────────────────────────────────────────┘
```

The accumulators are the model's memory. Heat-rate degradation drifts with `hr_recov + fouling`; forced-outage probability comes from `df` (combustion hockey-stick), `tbc_time` (Weibull hazard rate), `rotor_life`, and — since [ADR-007](../decisions/007-creep-wiring-and-trip-wear.md) — `dc` (creep-rupture hockey-stick); inspection events fire when `eoh` crosses thresholds. Damage doesn't go away on its own; only inspection events reset specific accumulators.

> **Hot-section ambient weighting ([ADR-006](../decisions/006-ambient-weighted-wear.md))**: the two metal-temperature-driven accumulators — `dc` (creep) and `tbc_time` (TBC) — advance by an *ambient-weighted* fired-hours sum (hotter ambient → faster, re-anchored to the fired-hour-weighted mean ambient so the calibrated total is preserved and only the seasonal *distribution* shifts). The other accumulators advance on raw fired hours / starts. See [`flowcharts.md`](flowcharts.md) for the wear-accumulation and wear→failure diagrams.

Defined and initialized in [`notebooks/03_daily_loop_feedback.py`](../../notebooks/03_daily_loop_feedback.py) §C; extended for outage tracking in [`notebooks/04_full_path_mode_comparison.py`](../../notebooks/04_full_path_mode_comparison.py) §C.

### §5.2 The 12-step daily loop

> **Deep dive on steps [1]–[2] (the outage gates)**: [`outage_mechanics.md`](outage_mechanics.md) is an example-driven walkthrough of "am I already down?" + "do I break down today?" — the Bernoulli draw, the weighted cause attribution, the lognormal duration, trip wear, and a full multi-day trace.

```
Day N begins (state = closing state of day N-1)
    │
    ▼
[1] Is plant in continuing outage (CI / MI / forced)?
    │
    ├── YES → Accrue fixed LTSA fee, decrement outage days, exit day.
    │
    NO
    │
    ▼
[2] Sample forced-outage event vs P_forced(state)
    │
    ├── Bernoulli draw < P_forced?
    │     YES → Pick cause (GT / HRSG / BG) weighted by component probs.
    │           Sample duration (lognormal, median by cause).
    │           Charge owner-cost ($0 / $500K / $750K).
    │           TRIP WEAR (ADR-007): if plant was RUNNING, this is a
    │             full-load trip → df += 8×cold-start fatigue,
    │             eoh += 8×cold-start EOH (+ EOH-reserve accrual).
    │           Set outage_type = "forced_*", outage_days_remaining.
    │           Exit day.
    │
    NO
    │
    ▼
[3] Find next scheduled inspection event from pre-built schedule.
    Compute EOH headroom = next_threshold − state.eoh.
    │
    ▼
[4] Compute mode wear penalty multiplier from (mode, eoh_headroom).
    Mode A: always 1.0  (no self-curtailment)
    Mode B: ramps 1.0 → 2.5 as headroom shrinks below 4,000
    Mode C: ramps 1.0 → 4.0 as headroom shrinks below 4,000
    │
    ▼
[5] Twin dispatch (24 hours, both clean-HR and degraded-HR paths):
    For each hour:
      For each mode (3xCC / 2xCC / 1xCC):
        spark = LMP − (HR/1000) × (gas + RGGI) − VOM
        if currently_off: spark -= wear_penalty / 6  (hurdle for starting)
        margin = max(spark, 0) × mode_capacity
      Pick best mode (highest margin).
      If best_margin = 0 and must_run (DHTS day): force 1xCC at loss.
      Detect start type (cold/warm/hot from hrs_off).
      Accumulate revenue, fuel_mmbtu, fired_hours, starts.
    │
    ▼
[6] Apply cold-start warming gas correction (ADR-002 Correction 1):
    cold_starts × 2,537 MMBtu × (gas + RGGI)  ← subtracted from gross margin
    │
    ▼
[7] Commit operational state (state.op, state.hrs_off from dispatch result).
    │
    ▼
[8] Update stress accumulators:
    state.eoh        += fired_hours + start_eoh_penalty
    state.fouling    += exponential approach to asymptote 2.5%
    state.hr_recov   += slow drift with fired hours
    state.dc         += creep_rate × fired_hours_AMBIENT_WEIGHTED   ← ADR-006
    state.df         += fatigue per start (by type)
    state.tbc_time   += fired_hours_AMBIENT_WEIGHTED               ← ADR-006
    state.hrsg_cycles+= 1 × n_starts
    state.rotor_life += rotor rate × fired_hours
    (ambient-weighted = Σ ambient_wear_factor(temp) over fired hours;
     re-anchored so Σ weighted ≈ Σ raw → redistributes, doesn't re-level)
    │
    ▼
[9] Cycle-end HR tracking: cumulative fuel_mmbtu and MWh since last inspection
    (used to fire HR penalty on next inspection).
    │
    ▼
[10] Accrue daily LTSA streams:
     stream 1: fixed daily fee × escalation
     stream 2: EOH reserve = delta_eoh × $175/EOH × escalation
     stream 5: start overage (if YTD count > pro-rated baseline, charge per excess)
    │
    ▼
[11] Inspection trigger check:
     calendar_hit = today >= scheduled_date
     hard_stop_hit = state.eoh > threshold + 1,500
     If either:
       Charge owner-uncovered cost ($937K CI or $10.5M MI).
       Apply HR penalty if cycle-avg HR > guarantee × (1 + tolerance).
       Apply state resets (CI partial; MI more aggressive).
       Set outage_type, outage_days_remaining.
    │
    ▼
[12] Record day. (year-end? apply availability penalty.)  Advance to day N+1.
```

This is what runs 3,287 times for each of 3 modes in Notebook 4 (= 9,861 day-mode executions, ~50 seconds wall-clock).

### §5.3 Dispatch decision detail — what makes an operating mode pick

> **Worked-example deep dive**: [`dispatch_economics.md`](dispatch_economics.md) decomposes the per-hour margin (`fuel_cost → spark → effective_spark → margin`) with numbers — including the start hurdles ("run if on" vs "won't start") and exactly where temperature enters (capacity, not the per-MWh spark).

The dispatch decision is the single most-touched piece of logic. Per hour, the loop iterates over the three **operating modes** (3×CC / 2×CC / 1×CC) and picks the highest margin:

```
fuel_cost      = HR_btu_per_kwh / 1000 × (gas + RGGI)         $/MWh
spark          = LMP − fuel_cost − VOM                         $/MWh
effective_spark = spark − (wear_penalty / 6)                   $/MWh  (only if currently off)
margin         = max(effective_spark, 0) × operating_capacity  $/hr
```

Where:
- **`HR_btu_per_kwh`** is operating-mode-dependent (8,901 / 9,598 / 10,424 from MOR) AND degraded by `(1 + hr_recov/100)(1 + fouling/100)` if using the degraded path.
- **`gas`** is daily Henry Hub price (per ADR-001).
- **`RGGI`** = $17/short-ton × 117 lb-CO2/MMBtu / 2000 = $0.995/MMBtu (EPA AP-42 fuel-side, dispatch-correct — see [`caveats.md`](../../data/assets/lockport/caveats.md) §12).
- **`VOM`** = base CT default $1.02 × 1.35 cogen markup = $1.38/MWh.
- **`operating_capacity`** is ambient-derated linearly between summer-derate-at-90°F and winter-boost-at-32°F.
- **`wear_penalty / 6`** is the **policy-mode-driven** start hurdle: `wear_mult × 0.42 × Kumar_start_$/MW`, amortized over a 6-hour expected min-run streak. **Only applied when starting** (currently off). `wear_mult` is determined by the policy mode (A / B / C) and current EOH headroom — see §5.5.

The dispatch picks the best-margin operating mode for the hour; if all operating modes have negative margin, the plant goes offline — unless `must_run` is set (cogen DHTS flag), in which case 1×CC fires at whatever loss the spark dictates.

> **Where operating mode and policy mode interact**: `HR_btu_per_kwh` and `operating_capacity` change per **operating mode** (the inner loop). `wear_mult` changes per **policy mode** (set once per day from the outer simulation). The hourly dispatch loop runs the spark formula across all three operating modes and picks the best margin — and that picking is biased by the policy mode's wear penalty. **[`dispatch_mechanics.md §4`](./dispatch_mechanics.md) has a worked numerical walkthrough** of how the two axes combine in one decision.

> **2×CC never wins in v1**: notice the structure of the formula — 3×CC has the lowest HR (best spark/MWh) and highest capacity, so its margin always dominates 2×CC and 1×CC when economic. 2×CC literally never appears in v1's dispatch output. Real Lockport runs 2×CC ~26% of the time because of single-CT outages (planned and forced) that v1's block-level state can't represent. [`dispatch_mechanics.md §5`](./dispatch_mechanics.md) unpacks this.

### §5.4 Forced-outage probability — `P_forced(state)`

A daily probability assembled from three components per the prototype's understanding doc §7:

```
P_GT   = P_combustion(df)          ← hockey-stick: P scale × max(0, df/budget − 0.60)²
       + P_TBC(tbc_time)           ← Weibull hazard rate: (β/η)(t/η)^(β-1) × 24
       + P_rotor(rotor_life)       ← 0.00003 × rotor_life (linear)
       + P_creep(dc)               ← hockey-stick: scale × max(0, dc/budget − 0.50)²  (ADR-007)

P_HRSG = HRSG_BASE × age_mult      ← 0.0075 × (1 + (years_elapsed/10) × 0.5)
P_BG   = BG_BASE   × age_mult      ← 0.004  × (1 + (years_elapsed/10) × 0.5)

P_forced = 1 − (1 − P_GT)(1 − P_HRSG)(1 − P_BG)   ← independence assumption
```

A few notes:
- The aging multiplier is capped at `(years_elapsed/10, 1.0)`. Earlier versions of the code (N3) treated `year_frac = day_idx / 365.0` as fraction-of-aging-window when the formula expects fraction. N3's 30-day window kept the bug invisible. N4 caught it during 9-year integration → fix applied (see N4 §E.4 + N4 status-log entry).
- Each `P_combined` is capped at 10%/day per `P_FORCED_DAY_CAP` to prevent runaway hazard rates if `tbc_time` exceeds threshold.
- `P_creep(dc)` ([ADR-007](../decisions/007-creep-wiring-and-trip-wear.md)) closed a gap where `dc` was accumulated but fed nothing. For low-CF Lockport `dc` stays far below the 0.50 inflection so `P_creep ≈ 0` (physically correct — it doesn't run enough to creep-rupture); the channel activates for high-CF / hot-running assets and is what makes the ADR-006 ambient weighting of `dc` consequential.
- The constants are all from Bucket B (Athens-prototype defaults). These are the model's biggest tornado-driver per the prototype's sensitivity analysis; Phase L Monte Carlo sweeps them.

### §5.5 Policy mode A/B/C — the wear-penalty curve

This is the lever that produces **policy-mode** divergence (note: A/B/C, the outer policy axis; not 3×CC/2×CC/1×CC operating modes). Per [`docs/extra/understanding_of_gas_turbine_digital_twin.md`](../extra/understanding_of_gas_turbine_digital_twin.md) §5:

```
wear_mult
   ▲
4.0│                                  ┐ Mode C (caps at 4.0×, headroom ≤ 0)
   │                              ╱╱
   │                           ╱╱
3.0│                        ╱╱
   │                     ╱╱
2.5│                  ╱╱─────────────  Mode B (caps at 2.5×, headroom ≤ 1,000)
   │                ╱  ╱
2.0│              ╱   ╱
   │            ╱   ╱
1.5│          ╱   ╱
   │        ╱   ╱
1.0│──────╱───╱─────────────────────  Mode A (always 1.0×, no curtailment)
   │
   └──────────────────────────────────→ EOH headroom to next inspection
   0    1K   2K   3K   4K              (= scheduled threshold − current eoh)
```

The multiplier is applied to the GT-share (42%) of the Kumar 2012 start C&M cost; that wear-penalty cash is amortized over a 6-hour min-run proxy to produce an effective hurdle rate on start decisions. Effect: as EOH approaches an inspection threshold, Mode B / C make starts more expensive → fewer starts → less wear → inspection delayed.

**Honest finding in v1 (corrected)**: `wear_mult ≈ 1.0` for *most* hours (low CF → headroom usually > 4,000), but the policies still **diverge meaningfully on Net P&L** — **A ≈ −$146M vs B = C ≈ −$123M (~$23M)**. The driver is *inspection timing*: the per-policy schedule places the MI at A → 2025-04-01 (inside the window) but B → 2026-10 / C → 2029 (outside), so **A incurs the MI while B/C defer it past the horizon**; **B and C are identical** (C's extra conservatism never bites at this CF). ⚠️ Read this with the **finite-horizon caveat** — B/C look better partly because the deferred MI just falls past the window. Full treatment + caveats: [`dispatch_mechanics.md`](dispatch_mechanics.md) §3.5–§3.6.

### §5.6 Inspection event triggering

Two trigger conditions, OR'd together:

| Trigger | Fires when |
|---|---|
| **Calendar** | today ≥ scheduled_date (snapped to next April 1 or October 1 in the pre-builder) |
| **Hard stop** | state.eoh > scheduled_threshold + 1,500 (overage caps how far past threshold we let EOH drift) |

When an inspection fires:
- Owner-uncovered cost accrues (CI = $937K; MI = $10.5M per Athens placeholders).
- HR penalty checked: if `cycle_avg_HR > guarantee × (1 + tolerance)`, charge `excess_fuel × 1.25`.
- State resets apply:

| Reset | CI (combustion inspection) | MI (major inspection) |
|---|---|---|
| `dc` (creep) | × 0.5 | → 0 |
| `df` (fatigue) | × 0.5 | → 0 |
| `fouling` | × 0.3 (70% wash) | × 0.3 (70% wash) |
| `hr_recov` | × 0.3 (70% recovered) | × 0.25 (75% recovered) |
| `tbc_time` | unchanged | → 0 |
| `tbc_thresh` | unchanged | resampled from Weibull |
| `hrsg_cycles` | unchanged | → 0 |
| `rotor_life` | unchanged | × 0.5 |

- Plant goes offline for the inspection duration (CI = 12 days; MI = 52 days per placeholders).

### §5.7 The 7 LTSA cost streams

```
Daily events                        LTSA streams accrue
────────────                        ───────────────────
day passes                  ──→     Stream 1: Fixed monthly fee (daily slice)
EOH accumulates             ──→     Stream 2: EOH reserve ($/EOH × Δeoh)
start fires (YTD > base)    ──→     Stream 5: Start overage ($ per excess)

year boundary               ──→     Stream 6: Availability penalty
                                    (if YTD avail < 95% guarantee)

inspection fires            ──┬──→  Stream 3: CI owner-uncovered ($937K)
                              ├──→  Stream 4: MI owner-uncovered ($10.5M)
                              └──→  Stream 7: HR penalty (cycle-end)

forced outage fires         ──→     Forced-outage owner-cost
                                    (GT $0; HRSG $500K; BG $750K)
```

All 8 streams (the 7 above + forced outage owner-cost) are stored as cumulative daily arrays in the run-bundle parquets, so any downstream pivot ("how much HR penalty did Mode A pay over years 1-3 vs 7-9?") is one groupby away.

Every parameter (`$850K/month fixed fee`, `$175/EOH reserve`, `$3.75M total CI`, `$30M total MI`, etc.) reads from [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml) and **all 7 are status `placeholder` in v1**. The model_card surfaces this so the reader knows the absolute magnitudes aren't deal-realistic until the data room extracts.

### §5.8 Execution nesting — how the simulation actually runs

The mechanics above describe what happens inside one day. At runtime the daily loop is wrapped in two outer loops and one inner loop:

```
Outer: 3 policy modes (A / B / C)                   ← run independently, sequentially
  │
  └─ Middle: 3,287 days in the 9-year horizon       ← the daily loop from §5.2
       │
       └─ Inner: 2 dispatches per day                ← the twin (loss attribution)
            │     • clean    (use_degraded_hr=False)
            │     • degraded (use_degraded_hr=True)
            │
            └─ Per dispatch: 24 hours                ← hourly commit decision
                 │
                 └─ Per hour: 3 operating modes evaluated   ← 3×CC / 2×CC / 1×CC
                      (pick the one with highest margin)
```

Each policy mode is a fully independent simulation — its own `PlantState`, LTSA accumulators, maintenance schedule, and RNG instance (seeded identically). They share only the input data and the seed. Inside any mode's run, the twin dispatch fires every operating day: the clean reference is a counterfactual probe that produces `loss_degradation` for attribution but never updates state; **only the degraded dispatch result feeds back into state evolution, LTSA accrual, and inspection triggers** ([N4:1143-1155](../../notebooks/04_full_path_mode_comparison.py#L1143-L1155)). Each hour within a dispatch evaluates all three operating modes independently and picks the highest-margin one — that's the spark-spread heuristic from §5.3.

**Note on the word "mode."** It gets used for two different things in this codebase. *Policy mode* = A / B / C (investor choice — wear-penalty curve, §5.5). *Operating mode* = 3×CC / 2×CC / 1×CC (physical configuration — which CTs are running). The outer loop iterates over policy modes; the per-hour pick chooses an operating mode.

Per-mode evaluation count: 3,287 days × 2 dispatches × 24 hours × 3 operating modes = ~473K mode-margin checks. Across all three policy modes: ~1.42M. Total wall-clock ~50 seconds per N4's measurements.

---

## §6. Outputs — what the model produces

Built as four sequential notebooks (Phases G–J), each adding capability on top of the prior.

### §6.1 Per-notebook output map

| Notebook | What it produces | Where |
|---|---|---|
| **N1** — Data spine load + validate | Validation report on the YAML/parquet spine; status-code aggregation; 8 cross-validation checks | [`notebooks/01_data_spine_load_validate.ipynb`](../../notebooks/01_data_spine_load_validate.ipynb) |
| **N2** — One day of dispatch | Single-day dispatch trace; mode choice per hour; clean-vs-degraded comparison; cogen must-run sensitivity | [`notebooks/02_one_day_dispatch.ipynb`](../../notebooks/02_one_day_dispatch.ipynb) |
| **N3** — Daily loop + feedback | 30-day window with state carry-forward; 4 plots (state trajectory, P_forced decomposition, P&L attribution, daily cumulative) | [`notebooks/03_daily_loop_feedback.ipynb`](../../notebooks/03_daily_loop_feedback.ipynb) |
| **N4** — Full path + Mode A/B/C + LTSA | 9-year × 3-mode capstone; 6 plots; `model_card.md`; run-bundle parquets | [`notebooks/04_full_path_mode_comparison.ipynb`](../../notebooks/04_full_path_mode_comparison.ipynb) |

Each notebook is paired (jupytext) with a `.py` percent-format file. The `.py` is the canonical source; the `.ipynb` is regenerated for embedded plots + outputs.

### §6.2 Notebook 4 — the headline deliverable

The capstone run writes a complete output bundle to `data/outputs/lockport/runs/notebook4_<timestamp>/`:

```
notebook4_<timestamp>/
├── model_card.md                       ← the headline summary doc
├── run_config.yaml                     ← reproducibility config (seed, mode params, etc.)
├── daily_summary_mode_{a,b,c}.parquet  ← full daily record per mode (3,287 rows × ~30 cols)
├── state_trajectory_mode_{a,b,c}.parquet  ← engineering state columns only
├── ltsa_streams_mode_{a,b,c}.parquet   ← 8 cumulative cost streams
├── inspection_events.parquet           ← CI / MI events across all modes
└── forced_outage_events.parquet        ← forced events across all modes
```

The `model_card.md` is the single sheet to read first. Its structure:

```
1. Run metadata           — asset, window, seed, dates
2. Data spine vintages    — which parquet was loaded, when refreshed
3. Assumption distribution — 268 leaves: 80% real_* / 17.5% placeholder breakdown
4. Mode comparison        — spark / LTSA / Net P&L per mode + A→C delta
5. LTSA stream breakdown  — where the cost went, for Mode A
6. Backtest vs MOR        — 2024 generation, mode dist, cold-start frequency
7. Caveats                — known limitations of v1
8. Phase L roadmap        — what Monte Carlo would extend
9. Output artifacts       — paths to the parquets
```

**Headline numbers from the most recent run** (seed=42, 2026-05-15 build):

| | Mode A | Mode B | Mode C |
|---|---:|---:|---:|
| Spark margin | $15.81M | $7.88M | $10.08M |
| LTSA owner-uncovered | $218.89M | $220.97M | $220.41M |
| **Net P&L** | **−$203.1M** | **−$213.1M** | **−$210.3M** |
| Inspections | 1 (MI) | 1 (MI) | 1 (MI) |
| Forced outages | 35 | 35 | 35 |

**Caveat on the headline**: every LTSA parameter is placeholder. The absolute dollar magnitudes are not deal-realistic; what's meaningful is the **directional comparison across modes** and the **proportional breakdown of streams**.

### §6.3 Visualizations

Notebook 4 produces 6 plots:

1. **State trajectory by mode** — EOH, HR drift, dc+df, each panel overlays the 3 modes over 9 years
2. **P_forced trajectory by mode** — combined daily probability, year-by-year
3. **Cumulative spark margin by mode** — line chart, 3 colors
4. **LTSA cost stream stacked area, one panel per mode** — the where-did-the-cost-go chart
5. **Mode comparison bar summary** — 5 metrics × 3 modes
6. **Inspection event timeline** — Gantt-style; CI orange / MI red bars + forced outages as purple ▼

These are embedded in the `.ipynb` and visible in [`notebooks/04_full_path_mode_comparison.ipynb`](../../notebooks/04_full_path_mode_comparison.ipynb).

### §6.4 Reading the headline numbers — what spark, LTSA, and Net P&L mean

The three numbers that dominate the model_card and any verbal summary are **spark margin**, **LTSA owner-uncovered**, and **Net P&L**. They have specific meanings and important limitations. Definitions in [`glossary.md`](./glossary.md); this section explains the *interpretation*.

> **A note on framing**: this section reports values at **both annual and 9-year grain**, with annual as the primary number. Annual is the natural unit for thinking about a power plant (budgets, contracts, MOR filings, capacity payments are all annual). The 9-year totals are derivations. See [`gaps_and_priorities.md` §7](./gaps_and_priorities.md) for the full argument.

#### §6.4.1 Spark margin — what it is and what it's missing

**Definition**: the gross margin from selling electricity into the hourly market.

```
revenue   = LMP × MWh_dispatched                       [per hour]
fuel      = (HR / 1000) × MWh × gas_$/MMBtu            [per hour]
RGGI      = same fuel quantity × $0.995/MMBtu          [per hour]
VOM       = MWh × $1.38/MWh                            [per hour]

spark_margin = revenue − fuel − RGGI − VOM             [per hour]
             summed over every fired hour              [per window]
```

**Example for one good hour at Lockport (3×CC mode)**:
- LMP = $60/MWh, 221 MW dispatched → revenue = $13,260
- Fuel = (8,901 / 1000) × 221 × $3.50 = $6,884
- RGGI = (8,901 / 1000) × 221 × $0.995 = $1,957
- VOM = 221 × $1.38 = $305
- **Spark margin this hour = $4,114**

Summed for Mode A:
- **$1.76M/yr** (annual average across 9 years)
- $15.81M (9-year cumulative)

Small annual figure because Lockport runs only ~5–10% of hours; most hours have unprofitable LMP.

**What spark margin does NOT include — and this is critical**:

| Missing revenue stream | Plausible annual range | What it would add |
|---|---:|---|
| **Steam revenue** from cogen host (DHTS contract) | **+$2 to +$8M/yr** | The cogen's reason for existing; v1 = $0. Magnitude depends on DHTS daily volume and steam tariff (TBD from data room). |
| **NYISO ICAP / capacity payments** | **+$4 to +$12M/yr** | 200 MW UCAP × Zone A capacity price ($1.50–5/kW-month range); per [`consolidation_plan.md`](../plans/consolidation_plan.md) §5 D4, explicitly out of v1 scope. |
| **Ancillary services** (reg, spin) | +$0.5 to +$1.5M/yr | Asset-level v1 doesn't model. |
| **PURPA above-market avoided-cost** | TBD | If still active for Lockport's original PURPA contract. Contract status TBD. |
| **Combined missing revenue** | **+$6 to +$20M/yr** | |

So Mode A's $1.76M/yr spark is **probably less than half of Lockport's real annual revenue**. See [`gaps_and_priorities.md` §3](./gaps_and_priorities.md) for the full revenue-side accounting.

#### §6.4.2 LTSA owner-uncovered — what it is and the OEM-vs-owner split

**Definition**: every dollar the plant owner is on the hook for under the LTSA (Long-Term Service Agreement) maintenance contract. Includes both predictable streams (fixed fee, EOH reserve) and event-driven costs (inspections, forced outages, penalties).

The contract has two parties' scopes:

```
┌─────────────────────────────────┬────────────────────────────────────┐
│ OEM scope (paid for by fees)    │ Owner scope (owner pays directly)  │
├─────────────────────────────────┼────────────────────────────────────┤
│ • Most GT mechanical repairs    │ • Fixed monthly fee (TO the OEM)   │
│ • Hot-gas-path parts            │ • EOH-based reserve (TO the OEM)   │
│ • Combustion components         │ • 25% of CI cost (uncovered share) │
│ • Standard CI / MI scope        │ • 35% of MI cost (uncovered share) │
│                                 │ • Start overage (excess starts)    │
│                                 │ • Availability penalty (annual)    │
│                                 │ • HR penalty (cycle-end)           │
│                                 │ • HRSG repairs (outside CSA)       │
│                                 │ • BoP / controls / ST / generator  │
│                                 │   repairs (outside CSA)            │
└─────────────────────────────────┴────────────────────────────────────┘
```

**The owner-uncovered total** for Mode A = **$24.32M/yr** ($218.89M over 9 years), broken down:

| Stream | Annual avg | 9-yr cumulative | Share | What it really is |
|---|---:|---:|---:|---|
| Fixed monthly fee | **$11.96M/yr** | $107.66M | 49.2% | The recurring contract fee, paid every month no matter what |
| Start overage | $4.37M/yr | $39.36M | 18.0% | Cycling more than the annual baseline triggers extra fees |
| HR penalty | $3.55M/yr | $31.94M | 14.6% | Plant's degraded HR exceeded the contract guarantee at MI (lumpy — fires once in 9 yr) |
| Forced outage owner-cost | $2.19M/yr | $19.75M | 9.0% | HRSG / BoP failures (GT failures are OEM-covered → $0) |
| MI events (owner share) | $1.55M/yr | $13.95M | 6.4% | The 35% of the Major Inspection bill that's owner-paid (lumpy — fires once) |
| EOH reserve | $0.63M/yr | $5.71M | 2.6% | Per-EOH fee that accrues with operation |
| Availability penalty | $0.06M/yr | $0.52M | 0.2% | Year-end true-up when annual avail < 95% guarantee |
| CI events (owner share) | $0.00M/yr | $0.00M | 0.0% | No CI fired in 9 years for Mode A |

**Plain reading**: about half of Mode A's annual LTSA cost is the recurring fixed fee (paid even if plant is idle). The rest is cycling/wear-related charges plus inspection costs.

**Every single dollar above is computed from a `placeholder` value in [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml).** That fixed fee is Athens's $850K/month — not Lockport's actual fee. Real Lockport's fee for a 1992 cogen could plausibly be very different (likely lower, given older asset and PURPA-era contract structure). See §7.2.

#### §6.4.3 Net P&L — what the negative number does and doesn't say

**Definition**: `Net P&L = spark margin − LTSA owner-uncovered`. For Mode A:
- **−$22.6M/yr** annual avg
- −$203.1M cumulative 9-year

**The annual number says "Lockport loses $22.6M every year."** This is **not a real claim about Lockport's economics.** It's an artifact of *four* v1 modeling choices that make the comparison apples-to-oranges:

1. **Placeholder LTSA dollars** (§7.2). Every cost in the $24.32M/yr LTSA is from Athens defaults. Real values could shift LTSA down by **$5–14M/yr** alone — see [`gaps_and_priorities.md` §2](./gaps_and_priorities.md).
2. **Missing revenue streams** (§6.4.1). Steam revenue, capacity payments, ancillary services — none modeled in v1. These could plausibly add **$6–20M/yr** to the revenue side once included.
3. **Over-commit on dispatch** (§7.4). Model thinks the plant should run 2.4× more than MOR-observed 2024. More fired hours → more EOH → more LTSA accrual → bigger negative. Fixing this dispatch realism shifts another **$3–5M/yr**.
4. **Single-path RNG noise**. 35 forced-outage events in Mode A is one realization; different seeds produce different counts and durations.

**What the negative number IS useful for**:

| ✓ Valid use | ✗ Invalid use |
|---|---|
| Directional comparison across modes (A vs B vs C) | "This asset is unprofitable" |
| Stream-by-stream breakdown (where the cost concentrates) | "We can underwrite at this Net P&L" |
| Tracking the structural shape of LTSA accrual over time | "Phase L will give us forecast P&L" |
| Sensitivity to mode policy under placeholder economics | The mode trade-off thesis is "validated" |

**What would move Net P&L positive (annual-first magnitudes, calibrated against survivorship)**:

| Fix | Direction | Plausible annual shift | 9-yr derived |
|---|---|---:|---:|
| Real LTSA fixed fee (1992 plant past original CSA → much lower) | Net ↑ | +$7 to +$9M/yr | +$63 to +$81M |
| Real inspection / repair costs (data room) | Net ↑ | +$1 to +$6M/yr | +$9 to +$54M |
| Add cogen steam revenue | Net ↑ | +$3 to +$7M/yr | +$27 to +$63M |
| Add NYISO ICAP capacity revenue | Net ↑ | +$5 to +$9M/yr | +$45 to +$81M |
| PURPA premium (if contract active) | Net ↑ | +$0 to +$5M/yr | +$0 to +$45M |
| Realistic dispatch (planned outages, derates, ramps) | Net ↑ | +$3 to +$5M/yr | +$27 to +$45M |
| Subtract Fixed OPEX layer (F1–F7 + sustaining capex) | Net ↓ | −$6 to −$12M/yr | −$54 to −$108M |
| **Combined mid-range** | **Net ↑** | **+$13 to +$29M/yr** | **+$117 to +$261M** |

That would move annual Net P&L from **−$22.6M/yr → roughly +$0 to +$8M/yr** with central tendency **+$2 to +$4M/yr**. This passes the survivorship sanity check: an asset operating continuously since 1992 must be at least breakeven on average. Sustained negative cash flow over decades isn't consistent with a plant still operating. See [`pnl_ledger.md` §4](./pnl_ledger.md) for the full reconciliation walk including the Fixed OPEX layer.

#### §6.4.4 The mental model for reading any model_card

When you open a model_card, read the numbers in this order:

1. **Assumption distribution** at the top — what fraction of the model is real vs placeholder? Currently 80% real / 17.5% placeholder. The placeholder share concentrates in LTSA, so the LTSA dollar magnitudes carry the placeholder taint.
2. **Annual averages first**, 9-year totals second. A −$203M cumulative is harder to reason about than −$22.6M/yr.
3. **Mode comparison delta**, not absolutes. The interesting number is "Mode A vs Mode B in Net P&L" (~$1.1M/yr favoring A), not the absolute Net P&L of any individual mode.
4. **LTSA stream breakdown** — where is the money going? Fixed fee 49% means contract terms matter way more than dispatch policy at this horizon.
5. **MOR backtest** — does the model over- or under-commit vs reality? If over-commits, the LTSA accrual is inflated and so is the negative Net P&L.
6. **Forced outage count** — for v1, 35 events is one realization; Phase L will give the distribution.

The "headline number" trap is reading "Net P&L = −$22.6M/yr" as forecast. It's not. It's the output of a model with known, documented gaps that all push in the same negative direction. See [`gaps_and_priorities.md`](./gaps_and_priorities.md) for the priority order on fixing them.

---

## §7. Caveats — what v1 does NOT do (or does badly)

Lifted from `caveats.md`, the notebook-4 findings, and the consolidation plan.

### §7.1 Single-path, no Monte Carlo

The headline numbers are one realization with seed=42. Forced-outage timing, TBC threshold, and (under v1) some dispatch tie-breaking is RNG-sensitive. A different seed produces different (often materially different) numbers. **Mode B and Mode C ordering can flip** in single-path runs due to RNG-driven outage variance. Phase L Monte Carlo addresses this.

### §7.2 Placeholder LTSA values

All 7 LTSA stream parameters in [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml) are Athens-prototype `placeholder` values. The $850K/month fixed fee, $3.75M CI cost, $30M MI cost, etc., are numerically valid but not deal-realistic for Lockport's actual contract. Each carries a `validation_path` pointing to the data-room file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx`. Until that extraction completes, treat absolute dollar magnitudes as "structural shape correct; dollar levels TBD."

### §7.3 v1 modeling limitations baked in

| Limitation | Why | Fix path |
|---|---|---|
| **Block-level state**, not per-generator | Simpler v1 code | v2 — per-generator state + outage availability |
| **No 2×CC mode emergence** from one-CT-down scenarios | Block-level can't model "1 of 3 CTs offline" | v2 — per-generator |
| **No planned outage modeling** outside CI/MI | We don't have a planned-outage schedule | v2 — add planned outage from MOR |
| **No dispatch derates or ramp constraints** | Hour-by-hour optimization is a heuristic | v2 — optimization step (per understanding doc §5.1) |
| **No grid curtailment** | Out of scope for asset-level model | v2+ |
| **No capacity market revenue** | Per D4 (consolidation plan §5) | v2 — add ICAP/RA |
| **Single asset (Lockport)** | v1 scope | v2 — multi-asset portfolio |
| **Henry Hub only**, no Algonquin basis | Per ADR-001 (sparse basis data) | v2 — add basis modeling |
| **No DHTS daily extraction** — synthetic cold-day proxy | MOR DHTS extraction is a separate workstream | v2 — wire MOR DHTS directly |
| **Cogen VOM markup ×1.35** is industry mid-range | No Lockport-specific calibration data | v2 — calibrate from MOR fuel/MWh |
| **Dual-fuel switching never fires** | v1 simplification | v2 — implement switching logic |

### §7.4 Backtest divergences

For Mode A vs MOR-observed 2024:

| Metric | MOR | Mode A | Direction of divergence |
|---|---:|---:|---|
| Annual generation | 192,494 MWh | 468,331 MWh | Model over-commits ~2.4× |
| 3×CC share of fired hours | 64.9% | 74.1% | Model favors 3×CC more |
| 2×CC share | 26.1% | 0.0% | Model never picks 2×CC |
| 1×CC share | 8.9% | 25.9% | Model favors 1×CC more |
| Cold starts/year | ~7 | 14.3 | Model cycles too aggressively |

**Causes of over-commitment**: no planned outages modeled, no dispatch derates / ramps, no grid curtailment, no DHTS realism. The model "thinks" Lockport should run more than it actually does. **These are v1 limitations, not bugs**, but they tell you not to read the absolute MWh as a forecast.

### §7.5 Calibration uncertainty (Bucket B — the biggest unknown)

The state-evolution constants (`FATIGUE_PER_*_START`, `FOULING_*`, `TBC_WEIBULL_ETA`, `HRSG_BASE_PROB_*`, `BG_BASE_PROB_*`, the combustion hockey-stick inflection point at 0.60) are all Athens-prototype defaults. They drive P_forced and inspection cadence. The prototype's own sensitivity analysis flags `P_BG_AGE_MAX` and fatigue-per-cold-start as the dominant tornado drivers.

Phase L Monte Carlo treats these as sweep parameters; v2 ideally calibrates them per-asset from MOR + Lockport's own outage history.

### §7.6 Bug found and fixed during N4 build

The aging-multiplier formula `age_mult = 1 + year_frac × (MAX - 1)` was being called with `year_frac = day_idx / 365.0` in N3. The intent of the formula is `year_frac = fraction of 10-year aging window`. Over a 30-day window (N3) the bug is invisible. Over a 9-year window (N4) it compounds to 5.5× when it should cap at 1.5×. **N4 fixed this** by clamping `aging_frac = min(years_elapsed / 10, 1.0)`. The fix dropped forced-outage event count from 86 → 35 per mode over 9 years.

**Action item**: backport this fix into N3 (or document why N3's short horizon makes it moot).

**Second fix (2026-05-27, Sanity-6 calendar exemption)**: the in-notebook sanity check "inspections triggered near threshold" flagged *any* inspection firing >5K EOH below threshold as an anomaly. But **calendar**-triggered inspections legitimately fire below the EOH threshold (they're time-driven, not wear-driven). After the commitment-hurdle change reduced fired hours, EOH lagged the calendar and a valid calendar MI tripped the assert — **aborting the whole run before the output bundle (incl. `model_card.md`) was written**, so the card silently went stale. Fixed: Sanity-6 now exempts `trigger == "calendar"` and only enforces EOH-proximity on hard-stop triggers. (See [`data/assets/lockport/caveats.md`](../../data/assets/lockport/caveats.md) §12.)

---

## §8. Next steps — Phase K, Phase L, and beyond

> **The full priority order with annual dollar impacts is in [`gaps_and_priorities.md` §6](./gaps_and_priorities.md).** The summary below covers the two near-term phases scoped in [`consolidation_plan.md`](../plans/consolidation_plan.md); the gaps doc adds the substantive *what to actually fix first* prioritization (data-room LTSA → NYISO ICAP → MOR-replay mode → steam → dispatch realism) which is what should drive day-to-day work.

### §8.1 Phase K — Graduate notebooks to `src/`

The N1–N4 notebooks are "thinking out loud" — exploratory, monolithic, with constants and helper functions defined inline. Phase K refactors the working code into a proper Python package layout:

```
src/gt_models/
├── state.py              ← PlantState dataclass + init_state
├── dispatch.py           ← dispatch_day_mode_aware + ambient_derate
├── stress.py             ← update_stress + p_forced_components
├── schedule.py           ← build_maint_schedule + snap_to_shoulder
├── ltsa.py               ← LTSA accrual helpers (7 streams)
├── inspection.py         ← apply_inspection_reset + trigger logic
├── outage.py             ← sample_outage_cause + sample_outage_duration
├── policy.py             ← wear_penalty_mult (A/B/C curves)
├── io/
│   ├── load.py           ← YAML/parquet loaders with assumption tracking
│   └── output.py         ← run-bundle writer + model_card.md generator
└── pipelines/
    └── run_horizon.py    ← the orchestrator that N4 inlines today
```

Plus unit tests for the math (especially edge cases the notebooks don't exercise). Notebooks then become thin drivers that call into `src/`.

### §8.2 Phase L — Monte Carlo

Replace fixed seed with N≥50 paths. Sample over:

| Parameter | What it controls |
|---|---|
| RNG seed | Forced-outage timing, TBC threshold |
| `FATIGUE_PER_*_START` | Combustion damage per start |
| `TBC_WEIBULL_ETA` | TBC failure timing |
| `FOULING_TAU_HRS` | Compressor fouling rate |
| `HRSG_BASE_PROB_PER_DAY` | HRSG forced-outage baseline |
| `BG_BASE_PROB_PER_DAY` | BoP / controls / generator outage baseline |
| Combustion inflection (0.60) | Hockey-stick onset |

Outputs: P10 / P50 / P90 distributions on spark, LTSA, Net P&L, per mode. Plus named tail-event scenarios (2022-Uri-style gas shock, extreme cold week, etc.).

Phase L also replaces **historical replay** (N4) with **synthetic scenario engine** — the analog-block sampler + forward-anchoring machinery currently in `model-gpr`'s Step 1.

### §8.3 v2 priorities (post-Phase L)

In rough order of expected impact:

1. **Data-room LTSA extraction** — replace all 47 placeholder values with real contract data. This is the single highest-impact unblock for the model_card's absolute dollar magnitudes.
2. **Per-generator state** — unblocks 2×CC mode, planned-outage modeling, single-CT-down scenarios.
3. **MOR DHTS daily extraction** — replaces the synthetic must-run flag with real daily steam-host schedule.
4. **Per-asset Bucket B calibration** — derive fouling, fatigue, and outage-baseline constants from Lockport's own MOR + outage history.
5. **Algonquin basis modeling** (resolves ADR-001 deferral).
6. **Capacity market revenue** — adds ICAP / NYISO Reliability dollars to the Net P&L line.
7. **Multi-asset portfolio** — extend the framework beyond Lockport.
8. **Real optimization** — replace hour-by-hour greedy heuristic with a proper LP/MIP per understanding doc §5.1.

---

## §9. How to read the model cold (a 10-minute path)

If a new teammate / future-self lands here and needs to come up to speed fast:

1. **Read this doc** (§1–§3 are enough for a mental model; ~10 min).
2. **Skim** [`data/assets/lockport/caveats.md`](../../data/assets/lockport/caveats.md) (12 sections; 5 min) — understands what's baked into the data.
3. **Open the [model_card.md](../../data/outputs/lockport/runs/)** from the most recent N4 run (3 min) — see the headline numbers.
4. **Browse** [`notebooks/04_full_path_mode_comparison.ipynb`](../../notebooks/04_full_path_mode_comparison.ipynb) — the 6 plots tell the story; skim the markdown cells for context (10 min).
5. **When something seems off**, check the relevant ADR in [`docs/decisions/`](../decisions/) — the reasoning trail is there.
6. **When something looks too sharp / too clean**, check the assumption status — if it's `placeholder`, the magnitude is not real.

---

## §10. Cross-reference index

A compact map from concept to file:

| Concept | Where it lives |
|---|---|
| **Flow charts (visual companion to this doc)** | [`docs/methodology/flowcharts.md`](flowcharts.md) — end-to-end + daily loop + wear/failure + creep-fatigue (Mermaid) |
| **Outage mechanics (daily-loop steps 1–2, detailed + examples)** | [`docs/methodology/outage_mechanics.md`](outage_mechanics.md) — continuing-outage gate + forced-outage sampling (Bernoulli, cause, lognormal, trip wear), multi-day trace |
| **Dispatch economics (the per-hour margin, detailed + examples)** | [`docs/methodology/dispatch_economics.md`](dispatch_economics.md) — spark → effective_spark → margin; start hurdles; where temperature enters (capacity vs spark) |
| **Wear mechanics (state vector + step 8, detailed + examples)** | [`docs/methodology/wear_mechanics.md`](wear_mechanics.md) — the 9 accumulators field-by-field; accumulator→consequence map; creep/fatigue laws; recovery/cost + gaps; one-day example |
| **Engine code (importable) + how it works** | [`src/gt_engine/`](../../src/gt_engine/) · impl docs [`docs/implementation/gt_engine/`](../implementation/gt_engine/) (overview, architecture, function ref, IO, worked example) |
| **Forward scenario engine + how it works** | [`src/forward/`](../../src/forward/) · impl docs [`docs/implementation/forward/`](../implementation/forward/) · design [`docs/plans/forward_engine_plan.md`](../plans/forward_engine_plan.md) |
| ADR-006: ambient-weighted hot-section wear | [`docs/decisions/006-ambient-weighted-wear.md`](../decisions/006-ambient-weighted-wear.md) |
| ADR-007: creep wiring + trip wear | [`docs/decisions/007-creep-wiring-and-trip-wear.md`](../decisions/007-creep-wiring-and-trip-wear.md) |
| Build plan + 5 locked decisions | [`docs/plans/consolidation_plan.md`](../plans/consolidation_plan.md) §5 + §8 |
| ADR-001: gas hub Henry Hub for v1 | [`docs/decisions/001-gas-hub-treatment-v1.md`](../decisions/001-gas-hub-treatment-v1.md) |
| ADR-002: Lockport-specific vs generic calibration | [`docs/decisions/002-lockport-specific-vs-generic-calibration.md`](../decisions/002-lockport-specific-vs-generic-calibration.md) |
| Status taxonomy (9 codes) | [`docs/assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md) |
| Placeholder caveats | [`docs/assumptions/placeholder_caveats.md`](../assumptions/placeholder_caveats.md) |
| Lockport static config | [`data/assets/lockport/*.yaml`](../../data/assets/lockport/) |
| Lockport time-series | [`data/paths/lockport/*.parquet`](../../data/paths/lockport/) |
| Tech-class defaults | [`data/tech_class_defaults/`](../../data/tech_class_defaults/) |
| Lockport caveats | [`data/assets/lockport/caveats.md`](../../data/assets/lockport/caveats.md) |
| Lockport provenance | [`data/assets/lockport/provenance.md`](../../data/assets/lockport/provenance.md) |
| Prototype reference code | [`docs/extra/gas-turbine-digital-twin/`](../extra/gas-turbine-digital-twin/) |
| Prototype mental-model long-form | [`docs/extra/understanding_of_gas_turbine_digital_twin.md`](../extra/understanding_of_gas_turbine_digital_twin.md) |
| Foundational framework spec | [`docs/InfraSure_ModelingFramework_V2.md`](../InfraSure_ModelingFramework_V2.md) + PDF |
| Notebook plans (sketches before the build) | [`docs/plans/consolidation_plan/notebooks/0{1,2,3,4}_*.md`](../plans/consolidation_plan/notebooks/) |
| Notebooks (executable) | [`notebooks/0{1,2,3,4}_*.ipynb`](../../notebooks/) (+ paired `.py`) |
| Most recent N4 output bundle | [`data/outputs/lockport/runs/`](../../data/outputs/lockport/runs/) — latest timestamp |

---

## §11. Questions / things to push on

Things the author of this doc would expect a careful reader to ask:

1. **"How sensitive is Net P&L to the placeholder LTSA values?"** — currently unknown; will be answered by Phase L sweeps + (decisively) by data-room extraction.
2. **"Why does the model over-commit 2.4× vs MOR?"** — see §7.4. Multiple v1 limitations stack here; no single fix.
3. **"Is the wear-penalty mechanic worth keeping if it barely binds for Lockport?"** — yes; it'll bind harder for higher-CF assets (peaker → mid-merit transition) and is the only mechanic that can produce mode divergence. v2 might tune the multiplier curves per-asset.
4. **"Are the 9 stress accumulators all necessary, or could we collapse some?"** — open question for Phase K refactor. The prototype kept them separate because they reset differently at inspections; collapsing would require equivalent reset semantics.
5. **"What's the model's blast radius if the Athens-prototype constants are wrong?"** — that's what the Phase L tornado is meant to quantify. The prototype's own tornado (per understanding doc §13) identifies `P_BG_AGE_MAX` as dominant.
6. **"Why daily, not hourly, state grain?"** — dispatch is hourly within each day; state updates apply to the closing of the day. Going to hourly state grain would multiply runtime ~24× without clear gain (fouling, EOH, fatigue all evolve on time scales >> 1 hour).
7. **"Why historical replay rather than synthetic for v1?"** — gives us a real backtest target (MOR-observed 2024) which a synthetic scenario can't anchor to. Phase L flips to synthetic for Monte Carlo.
