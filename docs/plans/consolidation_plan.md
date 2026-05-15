# gt_models Consolidation Plan

> **Status**: Draft, 2026-05-14. The foundational planning block for the gas turbine model work — written once, read often as the reference for *why* the structure looks the way it does.
>
> **Audience**: anyone (including future-self) walking into gt_models cold and needing to understand what this repo is, what it consumes, what it produces, and what the rest of the model build looks like.
>
> **Related docs**:
> - [`docs/plans/step_1_climate_price_scenario_plan.md`](./step_1_climate_price_scenario_plan.md) — exogenous scenario package definition
> - [`docs/plans/step_2_execution_blueprint_plan.md`](./step_2_execution_blueprint_plan.md) — dispatch execution blueprint
> - [`docs/extra/understanding_of_gas_turbine_digital_twin.md`](../extra/understanding_of_gas_turbine_digital_twin.md) — reader's guide to the prototype that this plan treats as architectural reference (not as the source of code to copy)
> - [`docs/InfraSure_ModelingFramework_V2.md`](../InfraSure_ModelingFramework_V2.md) — full framework V2

---

## Quick orientation

We have four repositories that touch the gas turbine asset modeling problem — each with a different and legitimate purpose. Right now plant information, market scenario data, raw diligence files, the prototype implementation, framework documentation, and the lab tech-class lookup all live in different places. The model itself is mostly synthetic-data-only, because the prototype was designed in isolation before we had clarity on the real data shapes.

This plan defines how gt_models becomes the **single home for the model**, with a clean, self-contained data spine fed from the other three repos through explicit interfaces (not code merges). It establishes the folder architecture, the assumption-tracking discipline that runs through every data artifact, and the phased execution sequence that gets us from today's prototype to a first end-to-end Lockport run using real data.

After this plan is approved, the next thing we build is Phase 1 of §8 (the scaffold), not any model code.

---

## §1. The four-repo system

Each repo has a role. None of them is going away, none is merging into another. The consolidation is about clean interfaces, not unification.

| Repo | Path | Role | Boundary |
|---|---|---|---|
| **renewablesinfo_org** | `~/code/personal/renewablesinfo_org` | Public-data fleet ETL. Plant identities, capacities, EIA-860 schedule extracts, eGRID emissions, financial coverage; plus the dispatch_params tech-class lookup (lab pass shipped 2026-05-08). | Fleet-wide, standardized schemas, no proprietary data. Cousin to diligence-extractor, not sibling. |
| **diligence-extractor** | `~/code/personal/diligence-extractor` | M&A data room → `asset_profile.md` per asset. Evidence-traceable extraction from PDFs + Excel into structured outputs. Currently has the Lockport heat-rate-by-mode analysis as its first analytical deliverable. | Explicitly NOT a dispatch model. Produces inputs *for* downstream models; doesn't run them. (See diligence-extractor CLAUDE.md.) |
| **model-gpr** | `~/code/work/infrasure_git_codes/model-gpr` | Step 1 implementation home. Scenario engine producing hourly price/gas/weather paths. Currently has Lockport-specific historical data: LMP at NYISO PTID 23791 + WEST zone (DA hourly + RT 5-min), gas at 8 hubs incl. Algonquin Citygate (29 yr daily), weather (46 yr hourly, 19 variables), plus SEAS5 forecast. | Asset-agnostic where possible; produces the exogenous path package that gt_models consumes. |
| **gt_models** | `~/code/work/infrasure_git_codes/gt_models` | **The model itself.** Step 2 dispatch + engineering twin + LTSA contract layer + Step 3/4 feedback. Currently has: framework V2 doc, Athens prototype in `docs/extra/gas-turbine-digital-twin/`, learning materials, Step 1 and Step 2 plans. | This is the modeling home. Inputs land here; outputs originate here. |

### Data flow at one glance

```
                              ┌───────────────────────────┐
                              │ renewablesinfo_org        │
                              │  - public plant data      │
                              │  - dispatch_params lookup │
                              └─────────────┬─────────────┘
                                            │ tech-class defaults
                                            │ plant public identity / capacity / market context
                                            ▼
┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
│ diligence-extractor       │    │ gt_models  (THIS REPO)    │◄───│ model-gpr                 │
│  - data room extraction   │───►│  - data/ (spine)          │    │  - Step 1 scenario engine │
│  - asset_profile.md       │    │  - src/  (the model)      │    │  - LMP/gas/weather paths  │
│  - heat-rate-by-mode      │    │  - docs/ (plans+learning) │    │                           │
│  - LTSA contract terms    │    │  - dashboard/ (future)    │    │                           │
└───────────────────────────┘    └─────────────┬─────────────┘    └───────────────────────────┘
                                               │
                                               ▼
                                   model outputs (P10/P50/P90,
                                   spark, LTSA, EOH, inspection
                                   timing) for downstream finance
```

The arrows are **read-only data flows**, not code dependencies. gt_models doesn't import from any of the other three repos; it consumes copied data artifacts at known paths.

---

## §2. Hard constraints

These are decisions explicitly made and recorded in upstream documents. Honor them.

### Non-merge boundaries

| Constraint | Source of authority | Why |
|---|---|---|
| **Do not merge diligence-extractor with renewablesinfo.** | `diligence-extractor/CLAUDE.md` — explicit | Different scale (fleet vs single deal), different format (standardized vs arbitrary), different audience. Cousins, not siblings. |
| **diligence-extractor is not a dispatch model.** | `diligence-extractor/CLAUDE.md` — explicit | Its deliverable ends at `asset_profile.md`. Modeling lives elsewhere (here). |
| **Do not pull diligence-extractor pipeline code into gt_models.** | This plan | It's a specialized PDF/Excel extraction pipeline. Keep it where it is; consume its outputs. |
| **Do not pull renewablesinfo ETL into gt_models.** | This plan | Same reason. Public-data fleet ETL is a different concern from single-asset modeling. |
| **Do not restructure model-gpr as part of this work.** | This plan | model-gpr is actively used. The consolidation is about giving gt_models a clean inbox, not reorganizing the world. |

### What we WILL do

Copy snapshots of the artifacts the model consumes, into a self-contained `data/` spine inside gt_models. Each artifact carries provenance metadata pointing back to its source. Refresh is a deliberate act, not a magic synchronization.

---

## §3. What gt_models becomes

A self-contained gas turbine modeling repository. Owns:

1. The actual model code (rebuilt cleanly using the Athens prototype as architectural reference — see §5 D1).
2. A self-contained data spine that the model consumes — copied from upstream sources, not symlinked.
3. The documentation: framework, learning materials, plans, per-asset profiles.
4. The dashboard layer (future) — placeholder folder reserved.
5. Outputs: simulation results, attribution reports, P10/P50/P90 distributions.

After consolidation, an analyst should be able to clone gt_models, run the Lockport simulation end-to-end with no external dependencies on the other three repos (other than refreshing data when needed).

What gt_models is **not**:
- Not a fleet ETL platform — see renewablesinfo
- Not a PDF/Excel extractor — see diligence-extractor
- Not the Step 1 scenario engine — see model-gpr (gt_models consumes Step 1's output, doesn't re-implement it)
- Not a multi-asset framework yet — Lockport-only for v1; multi-asset comes later when there's evidence what shape it should take

---

## §4. Folder architecture

### Top-level layout

```
gt_models/
├── README.md                  # one-page entry point
├── VERSION
├── requirements.txt
├── cloudbuild.yaml
│
├── docs/                      # all documentation (existing)
├── data/                      # NEW — self-contained data spine
├── src/                       # NEW — the model itself
├── dashboard/                 # NEW — future scope, placeholder only
│
├── lab/                       # existing — exploratory work (unchanged)
├── data_analytics_notebooks/  # existing — analysis notebooks (unchanged)
├── scripts/                   # existing — utility scripts (unchanged)
├── tests/                     # existing — model tests (will grow)
└── backups/                   # existing
```

The four new/upgraded top-level folders (`docs/`, `data/`, `src/`, `dashboard/`) are siblings. Each has its own README explaining what it owns.

### 4.1 `docs/`

Stays roughly as it is today. Grows in two ways:

```
docs/
├── README.md                                   # docs map
├── InfraSure_ModelingFramework_V2.md           # unchanged
├── InfraSure_GT_DigitalTwin_v2.pdf             # unchanged
├── plans/
│   ├── consolidation_plan.md                   # THIS DOC
│   ├── step_1_climate_price_scenario_plan.md   # existing
│   ├── step_2_execution_blueprint_plan.md      # existing
│   └── step_2_execution_blueprint/             # planned (per step_2 plan §"Proposed Output Folder")
│       ├── 00_index.md
│       ├── 01_time_resolution_and_frequency.md
│       └── ...                                 # 10 more files per step_2 plan
├── learning/                                   # existing — keep all
│   ├── basics/
│   ├── degradation_factors/
│   ├── examples/
│   ├── market_and_operations/
│   ├── plans/
│   └── plant_types/
├── reference/                                  # NEW — digests of upstream work
│   ├── README.md
│   ├── tech_class_dispatch_params_summary.md   # ← digest of renewablesinfo lab pass
│   ├── public_data_inputs_summary.md           # ← digest of renewablesinfo plant audit
│   └── diligence_data_inventory_summary.md     # ← digest of diligence-extractor inventory
├── assumptions/                                # NEW — central assumption registry (see §6)
│   ├── README.md
│   └── status_taxonomy.md
└── extra/                                      # existing
    ├── gas-turbine-digital-twin/               # the prototype — REFERENCE ONLY (do not edit)
    ├── understanding_of_gas_turbine_digital_twin.md
    ├── basics_of_gas_prices.md
    ├── stateful_historical_replay_flow.md
    ├── stateful_historical_replay_flowchart.mmd
    └── stateful_historical_replay_flowchart.svg
```

Key principle: `docs/extra/gas-turbine-digital-twin/` is preserved as a frozen architectural reference. **No edits to it as part of this consolidation.** When the prototype's logic gets reimplemented in `src/`, the prototype stays put as the canonical "what we were aiming to replicate."

### 4.2 `data/` — the spine (new)

Self-contained, copied (not symlinked) from upstream. The model reads from here and nowhere else.

```
data/
├── README.md                       # data spine layout + provenance rules + refresh discipline
│
├── tech_class_defaults/            # ← copied from renewablesinfo lab pass
│   ├── README.md                   # what this is, when last refreshed, cite the lab AUDIT.md
│   ├── dispatch_params_lookup.parquet
│   ├── dispatch_params_values.csv  # human-editable mirror
│   └── refs/                       # source PDFs (Kumar 2012, NREL ATB 2024, EIA AEO 2026, PJM M-15)
│
├── assets/                         # one folder per asset; v1 has Lockport only
│   └── lockport/
│       ├── README.md               # entry point: what's known, what's pending, where each value came from
│       ├── identity.yaml           # plant ID, location, operator, cross-system IDs
│       ├── engineering.yaml        # capacity, generators, derates, dual-fuel, prime movers
│       ├── operating_profile.yaml  # heat rate by mode, cold-start gas, EOH burn, run-streak patterns
│       ├── market_context.yaml     # NYISO node, hub, BA, eGRID subregion, RGGI exposure
│       ├── ltsa_terms.yaml         # contract structure (placeholders flagged until data room extraction)
│       ├── caveats.md              # cogen / mothball question / fuel switching / multi-mode dispatch
│       └── provenance.md           # where each artifact came from + last refresh date
│
├── paths/                          # ← copied from model-gpr Step 1 outputs (or model-gpr historical data while Step 1 is in development)
│   ├── README.md                   # what each path file is, refresh procedure, scenario IDs
│   └── lockport/
│       ├── lmp_da_hourly.parquet   # ← from model-gpr/local_data/lockport_energy_associates_lp/NEG WEST_LEA_LOCKPORT/da_hourly.parquet
│       ├── lmp_rt_intervals.parquet # ← from .../rt_hourly.parquet
│       ├── lmp_west_zone_da.parquet # ← from .../WEST/da_hourly.parquet (backup zone)
│       ├── gas_price_history.parquet # ← from .../gas_price_history.parquet
│       ├── weather_hourly.parquet    # ← from .../lockport_energy_associates_lp_weather_hourly.parquet
│       └── weather_forecast_seas5.json # ← from .../lockport_..._seas_daily_forecast_ECMWF_IFS_init_*.json
│
└── outputs/                        # simulation outputs (gitignored, regenerable)
    └── lockport/
        ├── runs/                   # per-run output bundles
        └── reports/                # aggregated reports per run
```

Notes:
- `data/outputs/` is gitignored. Inputs are versioned; outputs are not.
- `data/paths/lockport/` will be tens of MB (weather alone is ~15 MB). Acceptable — self-contained > clever.
- Each `data/assets/lockport/*.yaml` is the source of truth for that asset, with assumption tracking on every value (see §6).

### 4.3 `src/` — the model (new)

This is the rebuilt clean implementation. Per D1 in §5, we **do not copy-paste from the prototype**. The prototype is the architectural reference; the new code is designed knowing the real data spine.

Proposed initial layout (will evolve during execution):

```
src/
├── README.md                       # what's here + module map
├── __init__.py
│
├── io/                             # data loading layer
│   ├── __init__.py
│   ├── asset_loader.py             # reads data/assets/<asset>/*.yaml with assumption metadata
│   ├── path_loader.py              # reads data/paths/<asset>/*.parquet
│   ├── tech_defaults_loader.py     # reads data/tech_class_defaults/
│   └── schemas.py                  # pydantic/dataclass schemas for YAML files
│
├── engineering/                    # engineering twin (analog to prototype's EnggDTwin_model.py)
│   ├── __init__.py
│   ├── state.py                    # state vector + init_state
│   ├── stress.py                   # stress accumulators (EOH, creep, fatigue, fouling, TBC, HRSG, rotor)
│   ├── capacity.py                 # cap_eff(temp_f) — ambient derate
│   ├── heat_rate.py                # hr_clean and hr_degraded — mode-aware for our use
│   ├── forced_outage.py            # endogenous p_forced from state
│   └── inspection.py               # CI / MI reset semantics
│
├── dispatch/                       # dispatch engine (analog to prototype's dispatch_model.py)
│   ├── __init__.py
│   ├── modes.py                    # Mode A / B / C policy definitions
│   ├── hourly.py                   # hourly commit/dispatch decision
│   ├── daily.py                    # daily loop and feedback orchestration
│   ├── maintenance_schedule.py     # calendar shoulder-snapping
│   └── multi_mode.py               # NEW vs prototype — 1×CC / 2×CC / 3×CC mode choice per hour (Lockport-specific need)
│
├── ltsa/                           # LTSA contract wrapper (analog to prototype's LTSAContract.py)
│   ├── __init__.py
│   ├── contract.py                 # daily fee accruals, EOH reserve, escalation
│   ├── inspections.py              # CI / MI event cost classification
│   ├── overage.py                  # start overage charges
│   ├── penalties.py                # availability + HR penalties
│   └── forced_outage_classify.py   # in-scope vs owner-uncovered classification
│
├── cogen/                          # NEW vs prototype — Lockport-specific cogen constraints
│   ├── __init__.py
│   ├── host_steam_constraint.py    # must-run logic when DHTS > threshold (from MOR data)
│   └── vom_adjustment.py           # cogen +30–50% VOM markup over merchant default
│
├── markets/                        # NEW vs prototype — RGGI etc.
│   ├── __init__.py
│   ├── rggi.py                     # CO2 cost from emissions rate × allowance price
│   └── capacity_market.py          # NYISO ICAP (future — see §9 open questions)
│
└── runners/                        # end-to-end orchestration
    ├── __init__.py
    ├── single_path.py              # one path × N years
    └── monte_carlo.py              # N paths × M modes
```

This is a *proposal*. Final structure crystallizes during Phase G–I execution. The principle: each module corresponds to a concept in the framework V2 doc; the structure is more granular than the prototype's flat-file layout because we have clarity on the real moving parts.

### 4.4 `dashboard/` — future scope (new, placeholder only)

```
dashboard/
└── README.md   # "Future scope: visualization and UI for model outputs.
                #  Not in v1 build. Will be designed once we have a working
                #  Lockport simulation producing real outputs and we know
                #  what views the deal team actually wants."
```

That's it. Placeholder. No design work as part of this consolidation.

---

## §5. Decisions locked

Each decision below was discussed and agreed during the planning session. Recorded here so future-self doesn't re-litigate them.

### D1. The prototype is architectural reference, not a source for copy-paste

**Decision**: Rebuild the model in `src/` as a clean implementation. The Athens prototype in `docs/extra/gas-turbine-digital-twin/` is the *reference* — same conceptual goals (three layers, daily feedback loop, Mode A/B/C trade-off, P10/P50/P90 outputs, endogenous forced outage from stress state, recursive state update). Different *implementation* because we now have clarity on real data shapes.

**Why not copy-paste?** The teammate who built the prototype designed it in isolation, before we had clarity on:
- What heat rate data we actually get (we now know: mode-segmented from MOR; cold-start gas separately accountable)
- What plant-specific operating constraints matter (Lockport has cogen / steam host, dual-fuel switching, multi-mode 1×CC/2×CC/3×CC dispatch — none of which the prototype handles)
- What market path data we actually have (real NYISO LMP at the Lockport node, real Algonquin Citygate gas, 46 years of weather — not synthetic AR(1) generators)
- What the LTSA contract terms actually look like (still pending data room extraction, but the structure will inform schema choices the prototype guessed at)

**What carries over from the prototype unchanged**:
- The three-layer architecture (engineering / dispatch / LTSA)
- The daily feedback loop and order of operations
- The clean-vs-degraded twin dispatch attribution trick
- The state vector concept and inspection-reset semantics
- The Mode A/B/C policy framework
- The calendar-snapped maintenance scheduling with hard-stop overage
- The endogenous forced outage from state
- The LTSA cost taxonomy

**What's redesigned for our use**:
- Data ingest: reads from `data/` spine, not from `gt_market_inputs.npz` synthetic blob
- Multi-mode dispatch: 1×CC / 2×CC / 3×CC mode choice for Lockport, with mode-specific heat rate
- Cogen constraint: host-steam must-run logic (Lockport-specific)
- RGGI carbon cost: integrated into delivered fuel cost (NYUP exposure)
- Assumption metadata: every parameter carries provenance (see §6)

**Eventually better than the prototype** (out of v1 scope but the trajectory):
- Replace heuristic spark-vs-hurdle dispatch with rolling-window optimization (per understanding doc §5.1 — "true optimization is the planned next phase")
- Add NYISO ICAP capacity revenue
- Add ancillary services
- Add tail-event scenarios (Uri-class)
- Add 1×1 → 2×1 mode-switching within a day

### D2. YAML for static specs, parquet for time series

**Decision**: All plant-static facts (identity, capacity, generators, dual-fuel matrix, LTSA terms) live in human-readable YAML files. All time series (LMP paths, gas history, weather, simulation outputs) live in parquet.

**Why**: YAML diffs cleanly, is human-editable, is the right format for sparse structured facts with metadata. Parquet is the right format for dense time series — efficient I/O, schema enforcement, columnar.

**Where the line lies**:
- Anything we'd hand-edit → YAML
- Anything we'd plot or scan numerically → parquet
- Anything between (e.g. heat rate by mode summary) → YAML if it's <50 rows, parquet if it's a multi-thousand-row mode×month×year fact table

### D3. Copy path data from model-gpr (not symlink)

**Decision**: `data/paths/lockport/` contains *copied* parquet files from model-gpr, not symlinks.

**Why**: Self-contained gt_models is more valuable than disk-space savings. Symlinks create cross-repo dependencies that break checkouts, freeze incorrectly during model runs, and fail silently when model-gpr changes shape. Copies make refresh a deliberate act.

**Cost**: ~20–30 MB per asset for the time series data. Trivial.

**Refresh discipline**: `data/paths/<asset>/provenance.md` records source path + copy date + file checksums. Refresh = re-copy + update provenance + commit. No automatic sync.

### D4. Lockport-only for v1. No Athens reference asset. No calibration phase distraction.

**Decision**: Build the actual Lockport model end-to-end as v1. Skip Athens-as-reference-asset. Skip calibration mode entirely.

**Why**:
- Athens is the *prototype's worked example*, not our asset. Setting up Athens as a parallel reference asset in our `data/assets/` spine would conflate "framework architectural reference" (which is what Athens really is, via `docs/extra/`) with "real asset we're modeling" (which is Lockport).
- Calibration (back-testing modeled vs realized dispatch) is a phase that comes **after** we have a working model for a real site. Right now there's no working model to calibrate against. Trying to design for calibration mode now distracts from building the actual model.
- Multi-asset abstraction comes from doing 2–3 deals end-to-end, not from designing for it upfront. The framework north-star in diligence-extractor makes this explicit; same logic applies here.

**Consequence**: `data/assets/` has exactly one subfolder (`lockport/`) in v1. The directory structure is *designed to be multi-asset* (so adding `deal_2/` later is trivial), but only Lockport is populated.

### D5. diligence-extractor outputs are digested into our YAML

**Decision**: When we need a fact from diligence-extractor (heat rate by mode, LTSA terms, GADS-derived EFOR, DMNC capacity), we *extract that fact* into the appropriate `data/assets/lockport/*.yaml` file with full provenance metadata. We don't symlink to or import from `diligence-extractor/outputs/lockport/asset_profile.md`.

**Why**:
- The model consumes structured data (YAML, parquet), not Markdown prose
- Provenance metadata in our YAML carries forward into model outputs, which is the only way LTSA cost claims become defensible downstream
- diligence-extractor's `asset_profile.md` is the *deal-team-facing* deliverable, not the *model-facing* one. Both can exist.
- If diligence-extractor refines a value, refresh is a deliberate update to our YAML — not invisible drift

**Cross-link**: each value in our YAML cites the diligence-extractor output it came from (e.g. `notebooks/daily_heat_rate_analysis.ipynb` final-summary table) so the trail is traversable.

---

## §6. Assumption-tracking schema (first-class principle)

This is non-negotiable. Every value in every YAML carries provenance. Whether a number is *observed* or *assumed* is at least as important as the number itself.

### Why this is first-class

The model's output is a P10/P50/P90 distribution that someone will use to commit capital. The defensibility of that output depends entirely on whether every input can be traced back to a source. Mixing real-and-assumed numbers without tracking is the single biggest way the model becomes uncredible.

The dispatch_params lab pass (renewablesinfo, 2026-05-08) demonstrated this discipline at scale: 144 cells, each with status + source + confidence + cross-check. The same discipline applies to every cell in `data/assets/lockport/*.yaml`.

### Status taxonomy

Every leaf value has a `status` field that takes one of these values:

| Status | Meaning | Example |
|---|---|---|
| `real_observed` | Measured directly from this plant's own operating data | Heat rate by mode from MOR Excel daily aggregation |
| `real_reported` | This plant's value as reported in regulatory or contractual filings | Nameplate capacity from EIA-860 schedule 3_1; LTSA fixed fee from contract |
| `real_computed` | Derived deterministically from `real_observed` or `real_reported` values | Plant total capacity = sum of generator nameplate capacities |
| `assumed_techclass` | Tech-class default from public methodology references | VOM from NREL ATB 2024 F-Frame CC row 256; startup cost C&M from Kumar 2012 Tbl 1-1 |
| `assumed_vendor` | Vendor literature for the specific model | Siemens 501F start times via CCJ |
| `assumed_industry` | Industry-typical default with no canonical public source | Min up time / min down time for `<2000` CCGT |
| `assumed_derived` | Derived from other assumed values (compounds uncertainty) | Cogen VOM markup = merchant_VOM × 1.35 |
| `placeholder` | Waiting on a known-pending source extraction or analysis | LTSA fixed fee until data room extraction completes |
| `not_applicable` | Field exists in schema but doesn't apply to this asset | Boiler design specs for a generator with no boiler |

### Confidence (for assumed values only)

| Confidence | Meaning |
|---|---|
| `HIGH` | Cross-validated by ≥2 primary sources within ±20% |
| `MEDIUM` | Single primary source, no cross-validation; or extrapolated within tech class |
| `LOW` | Single low-quality source (vendor marketing, single academic study, undocumented industry default) |

### YAML structural format

The proposed format is **nested with metadata co-located**:

```yaml
# Example: data/assets/lockport/engineering.yaml (excerpt)

plant:
  id:
    value: 54041
    status: real_reported
    source: "EIA-860M Jan 2026"
  name:
    value: "Lockport Energy Associates LP"
    status: real_reported
    source: "EIA-860M Jan 2026"

generators:
  GEN1:
    prime_mover_code:
      value: CT
      status: real_reported
      source: "EIA-860 schedule 3_1 Y2024"
    nameplate_capacity_mw:
      value: 48.7
      status: real_reported
      source: "EIA-860 schedule 3_1 Y2024"
    min_load_mw:
      value: 30.0
      status: real_reported
      source: "EIA-860 schedule 3_1 Y2024"
      caveat: "Design/permit floor, not observed economic min"
    vom_per_mwh:
      value: 1.02
      usd_year: 2011
      status: assumed_techclass
      source: "Kumar 2012 NREL/SR-5500-55433 Table 1-1 'Gas-CC' baseload"
      confidence: MEDIUM
      caveat: "Baseload-only lower-bound; cogen markup of +30-50% likely applies (see caveats.md)"
    hot_start_time_hr:
      value: 3.0
      status: assumed_vendor
      source: "Siemens 501F field-operations via Combined Cycle Journal"
      confidence: MEDIUM
    min_up_hr:
      value: 6.0
      status: assumed_industry
      source: "Industry-typical default for <2000 F-class CCGT; no public canonical source"
      confidence: LOW
      validation_path: "CEMS observed run-length distribution when NYISO data ingested"
    boiler_efficiency_100pct:
      value: null
      status: placeholder
      source: "EIA 6_2 reporting gap for this plant"
      validation_path: "Data room boiler design specs if available"
```

### Loader convention

The verbose nested format is what's *stored*. The *model code* shouldn't pay the tax of writing `data.generators.GEN1.min_load_mw.value` everywhere. So `src/io/asset_loader.py` provides an interface where:

- `asset.generators['GEN1'].min_load_mw` returns the *value* directly (clean for modeling)
- `asset.generators['GEN1'].min_load_mw_meta` returns a dataclass with `{status, source, confidence, caveat, ...}` for cases where the model needs to introspect (e.g. flagging LOW-confidence values in output reports)

Implementation detail for Phase G; the principle is what matters here.

### Central assumption registry

`docs/assumptions/` holds two files:

- `status_taxonomy.md` — the table above, plus rules for how each status maps to UI/report disclosure
- `README.md` — pointer to the per-asset assumption summary that the loader can auto-generate (count of each status, distribution by confidence, list of all `placeholder` values pending resolution)

The auto-generated summary is what stakeholders read to know "how much of this model is real vs assumed."

---

## §7. Migration mapping

What lands in `data/`, from where, how.

| Destination in gt_models | Source repo | Source path | Mechanism | Refresh |
|---|---|---|---|---|
| `data/tech_class_defaults/dispatch_params_lookup.parquet` | renewablesinfo (lab) | `~/code/personal/renewablesinfo/integration/dispatch_params/dispatch_params_lookup.parquet` | Copy | Manual when lab pass updates |
| `data/tech_class_defaults/dispatch_params_values.csv` | renewablesinfo (lab) | Same folder | Copy | Same |
| `data/tech_class_defaults/refs/*.pdf` | renewablesinfo (lab) | `.../dispatch_params/refs/` | Copy | Rare |
| `docs/reference/tech_class_dispatch_params_summary.md` | renewablesinfo_org | `docs/design/dispatch_operating_params.md` | Digest-write (new doc, not verbatim copy) | When source design doc updates materially |
| `data/assets/lockport/identity.yaml` | renewablesinfo_org | `docs/extra/data_samples/plant_54041_lockport_data_brief.md` §1 + §"At a glance" | Digest-write into YAML with assumption metadata | When public data refreshes |
| `data/assets/lockport/engineering.yaml` | renewablesinfo_org | `docs/extra/data_samples/plant_54041_lockport_data_brief.md` §3, §4, §5, §6 | Digest-write into YAML | Same |
| `data/assets/lockport/market_context.yaml` | renewablesinfo_org | `docs/extra/data_samples/plant_54041_lockport_data_brief.md` §7 | Digest-write into YAML | Same |
| `data/assets/lockport/operating_profile.yaml` (heat rate by mode, cold-start gas) | diligence-extractor | `notebooks/daily_heat_rate_analysis.ipynb` Stage 2 final-summary table | Digest-write into YAML | When MOR refresh or new yearly data lands |
| `data/assets/lockport/operating_profile.yaml` (min up/down empirical, if extracted later) | diligence-extractor | TBD — derived from MOR run-streak analysis (future) | Digest-write | Same |
| `data/assets/lockport/ltsa_terms.yaml` | diligence-extractor | Data room (pending) | All values `placeholder` until extraction; then digest-write | When data room contract extraction completes |
| `data/assets/lockport/caveats.md` | renewablesinfo_org + diligence-extractor | Composition of public + private caveats | Hand-written, sourced | When new caveats surface |
| `data/paths/lockport/lmp_da_hourly.parquet` | model-gpr | `local_data/lockport_energy_associates_lp/NEG WEST_LEA_LOCKPORT/da_hourly.parquet` | Copy | When new historical data extends or new forwards refresh |
| `data/paths/lockport/lmp_rt_intervals.parquet` | model-gpr | `.../rt_hourly.parquet` | Copy | Same |
| `data/paths/lockport/lmp_west_zone_da.parquet` | model-gpr | `local_data/lockport_energy_associates_lp/WEST/da_hourly.parquet` | Copy (backup zone reference) | Same |
| `data/paths/lockport/gas_price_history.parquet` | model-gpr | `local_data/lockport_energy_associates_lp/gas_price_history.parquet` | Copy | When gas data refreshes |
| `data/paths/lockport/weather_hourly.parquet` | model-gpr | `local_data/lockport_energy_associates_lp/lockport_energy_associates_lp_weather_hourly.parquet` | Copy | Rare (46 yr archive) |
| `data/paths/lockport/weather_forecast_seas5.json` | model-gpr | `local_data/lockport_energy_associates_lp/lockport_energy_associates_lp_seas_daily_forecast_*.json` | Copy | When new forecast initialization |

Each migration is its own Phase 2–6 step in §8 below.

---

## §8. Execution plan

The principle: **one phase at a time, each independently shippable, each with explicit deliverables and acceptance criteria.** No timeline estimates — pacing is whatever-it-takes.

**Sequencing principle (revised 2026-05-14):** Build the data spine first, then validate the design by writing notebooks that walk through the modeling logic end-to-end on real Lockport data. Only after the notebooks prove the design and surface the natural module boundaries do we graduate to `src/`. The notebook-first approach forces understanding before abstraction — exactly the discipline that was missing when the prototype was designed in isolation.

Phases are grouped into three tracks:

- **Track 1: Data spine** (Phases A–F) — gets the data into place
- **Track 2: Notebook validation** (Phases G–J) — proves the modeling logic on real data, in human-readable form; each notebook's logical sections become the natural module boundaries
- **Track 3: Graduate to `src/` + first run** (Phases K–L) — refactor validated notebooks into modules; first Monte Carlo run

Detailed per-notebook plans live in [`consolidation_plan/notebooks/`](./consolidation_plan/). Notebook plans are written incrementally — Notebook 2's plan is informed by what Notebook 1 actually surfaces, not pre-specified blind.

Track 1 can largely proceed in parallel internally (Phases B–F after A). Track 2 is strictly sequential (Notebook 1 before 2 before 3 before 4). Track 3 starts only after Track 2's notebooks have stabilized.

### Phase A — Scaffold

**Goal**: Empty folder skeleton with READMEs explaining what each folder owns. No data, no code.

**Deliverables**:
- `data/README.md`, `data/tech_class_defaults/README.md`, `data/assets/README.md`, `data/assets/lockport/README.md`, `data/paths/README.md`, `data/paths/lockport/README.md`, `data/outputs/README.md`
- `src/README.md` with the proposed module map
- `dashboard/README.md` with future-scope placeholder
- `docs/reference/README.md`
- `docs/assumptions/README.md`, `docs/assumptions/status_taxonomy.md`
- This consolidation plan (already done)
- `.gitignore` updates: `data/outputs/`, ignore patterns

**Acceptance**: A team member cloning the repo can navigate the folder structure and understand what each folder is supposed to contain, even with no data yet.

**Depends on**: nothing.

### Phase B — Migrate tech-class defaults

**Goal**: `data/tech_class_defaults/` populated with the dispatch_params lookup from the lab pass.

**Deliverables**:
- Copy `dispatch_params_lookup.parquet` + `dispatch_params_values.csv` + `refs/*.pdf` from lab
- `data/tech_class_defaults/README.md` cites the lab AUDIT.md, names the version, records copy date
- `docs/reference/tech_class_dispatch_params_summary.md` digests the key methodology decisions (PJM publishes no defaults → Kumar 2012 primary; the 7 critical methodology decisions; the confidence-tier distribution)
- A short unit-range test in `tests/test_tech_class_defaults.py` (verifies VOM ∈ [0, 30], startup cost ∈ [0, 200] $/MW, etc.)

**Acceptance**: `pytest tests/test_tech_class_defaults.py` passes.

**Depends on**: Phase A.

### Phase C — Lockport public-data profile (YAMLs from renewablesinfo)

**Goal**: `data/assets/lockport/{identity, engineering, market_context}.yaml` filled with assumption-tracked values from the renewablesinfo data brief.

**Deliverables**:
- `identity.yaml` — plant ID, name, operator, sector, status, cross-system IDs (EIA / ORISPL / NYISO PTID / eGRID subregion)
- `engineering.yaml` — 4 generators with capacity matrix, dual-fuel matrix, min loads, cold-start times, CHP / HRSG / duct burner flags
- `market_context.yaml` — NYISO node assignments, hub, BA, eGRID subregion, voltage, regulatory status
- Every value carries `status` + `source`; assumed values carry `confidence` + `caveat` where relevant
- `caveats.md` — initial draft covering operational status, ambient sensitivity flag, multi-mode dispatch flexibility
- `provenance.md` — records the source brief version and date

**Acceptance**: A YAML loader smoke test can read all three files and recover every documented value (e.g. plant total nameplate = 221.3 MW from summing generator capacities).

**Depends on**: Phase A. Parallelizable with B.

### Phase D — Lockport operating profile (YAMLs from diligence-extractor)

**Goal**: `data/assets/lockport/operating_profile.yaml` filled with mode-segmented heat rate, cold-start gas cost, run-streak patterns from the MOR analysis.

**Deliverables**:
- Heat rate by mode (3 modes × `value/source/confidence`):
  - 1×CC: 10,424 Btu/kWh (vol-weighted, 26 days, MEDIUM confidence — small N)
  - 2×CC: 9,598 Btu/kWh (76 days, HIGH)
  - 3×CC_full: 8,901 Btu/kWh (189 days, HIGH)
- Cold-start gas: 35 warming days observed, ~$6,342 per cold start at $2.50/MMBtu gas
- Mode distribution: 64.9% 3×CC / 26.1% 2×CC / 8.9% 1×CC
- Annual operating-day pattern + 2024 operational-status correction (192,494 MWh actual — striking the public-data "mothballed" inference)
- Caveat block: cogen / DHTS / CHP markup; values are merchant-CCGT proxy

**Acceptance**: Loader can read; values match the MOR notebook final-summary table cell-for-cell.

**Depends on**: Phase A. Parallelizable with B and C.

### Phase E — Copy Lockport paths from model-gpr

**Goal**: `data/paths/lockport/` populated with copied parquet files.

**Deliverables**:
- 7 parquet/JSON files per the §7 migration table
- `data/paths/lockport/README.md` lists each file: source path, copy date, file size, row count, date range
- `data/paths/lockport/provenance.md` per file with SHA256 checksums

**Acceptance**: All files copy cleanly; row counts match source; date ranges documented in README.

**Depends on**: Phase A. Parallelizable with B/C/D.

### Phase F — Lockport LTSA terms (placeholder)

**Goal**: `data/assets/lockport/ltsa_terms.yaml` with the expected contract structure and all values flagged `placeholder` until data room extraction completes.

**Deliverables**:
- YAML schema covering the seven LTSA cost streams (fixed fee, EOH reserve, CI/MI events, overage, availability penalty, HR penalty, forced outage classification)
- Every value `status: placeholder`, with a `validation_path` pointing to the diligence-extractor data room path where the eventual answer lives
- Initial best-guess defaults from Athens prototype `[ASSUME]` values, clearly flagged as placeholder

**Acceptance**: A modeler can run the daily loop with these placeholder values and get a numerically valid (if not deal-realistic) output.

**Depends on**: Phase A. Parallelizable.

### Phase G — Notebook 1: Data spine — load + validate

**Goal**: First end-to-end load of the data spine. Verifies every file exists, schemas conform, values are self-consistent. Doubles as the de-facto loader spec and surfaces what the loader API needs.

**Deliverables**:
- `notebooks/01_data_spine_load_validate.ipynb`
- Detailed plan: [`consolidation_plan/notebooks/01_data_spine_load_validate.md`](./consolidation_plan/notebooks/01_data_spine_load_validate.md)
- Loads all YAMLs, all path parquets, tech-class defaults
- Cross-validation: generator capacities sum to plant total, LMP/weather/gas timestamps align, gas date range covers LMP date range, assumption-status codes valid, placeholders all have `validation_path` notes
- Assumption-status distribution summary (preview of model_card content)
- Stage 1 findings cell at the bottom — what we learned, what to change

**Acceptance**: Notebook runs end-to-end without errors; the assumption-status summary cleanly shows the real-vs-assumed split; findings cell identifies any schema awkwardness to fix before Notebook 2.

**Depends on**: Phases A–F (all data spine).

### Phase H — Notebook 2: One day of dispatch — the inner loop

**Goal**: Pick one representative Lockport day, walk through hourly commit/dispatch end-to-end. Surfaces the dispatch logic + cogen constraint + mode choice + RGGI in linear, inspectable form.

**Deliverables**:
- `notebooks/02_one_day_dispatch.ipynb`
- Detailed plan: `consolidation_plan/notebooks/02_one_day_dispatch.md` (to be written after Notebook 1 runs)
- One day's worth of hourly: spark_clean, spark_degraded, mode choice (1×CC / 2×CC / 3×CC_full), commit decision, fuel burn, gross margin
- Clean-vs-degraded twin attribution applied
- Cogen host-steam constraint check (from operating_profile.yaml DHTS data)
- RGGI cost layered into delivered fuel cost
- Mode-specific heat rate selection from operating_profile.yaml
- Stage 1 findings cell

**Acceptance**: Reproduces a sensible daily dispatch profile for the chosen day; mode choice logic is explainable hour-by-hour.

**Depends on**: Phase G (Notebook 1) — needs validated data spine + working load logic.

### Phase I — Notebook 3: Daily loop — state and feedback

**Goal**: 30-day window with state carry-forward. Shows EOH accumulation, stress accumulators evolving, capacity/HR drift, forced outage check, inspection threshold logic. The recursive feedback loop is the whole point of the architecture; this notebook proves it.

**Deliverables**:
- `notebooks/03_daily_loop_feedback.ipynb`
- Detailed plan: `consolidation_plan/notebooks/03_daily_loop_feedback.md` (to be written after Notebook 2 runs)
- Engineering state vector with stress accumulators (EOH, creep, fatigue, fouling, TBC, HRSG, rotor)
- Day-N closing state → day-N+1 opening state
- Endogenous `P_forced` from current state
- Inspection threshold crossing (CI / MI) with reset semantics
- Calendar-snapped maintenance scheduling preview
- Stage 1 findings cell

**Acceptance**: 30-day trajectory shows physically sensible state evolution; forced outage probability responds to stress correctly.

**Depends on**: Phase H (Notebook 2).

### Phase J — Notebook 4 *(optional v1)*: Full path + Mode A/B/C + LTSA cost streams

**Goal**: One full 10-year path × 3 modes. First cut at the seven LTSA cost streams. First model_card. Optional in v1 — can run with placeholder LTSA terms or defer until contract extraction completes.

**Deliverables**:
- `notebooks/04_full_path_mode_comparison.ipynb`
- Detailed plan: `consolidation_plan/notebooks/04_full_path_mode_comparison.md` (to be written after Notebook 3 runs)
- Single 10-year path × Mode A / B / C comparison
- All seven LTSA cost streams produced as daily arrays
- First version of model_card.md output
- Mode-comparison summary: spark, LTSA, EOH burn, inspection timing

**Acceptance**: All three modes produce numerically valid outputs; mode comparison shows the expected directional trade-off (Mode C sacrifices spark, saves LTSA).

**Depends on**: Phase I + Phase F (LTSA terms YAML, even if placeholder).

### Phase K — Graduate to `src/`: refactor notebooks into modules

**Goal**: The notebooks have proven the modeling logic on real data and surfaced the natural module boundaries. Now refactor that logic into reusable `src/` modules.

**Deliverables**:
- `src/io/` — asset_loader, path_loader, tech_defaults_loader, schemas (built from Notebook 1)
- `src/engineering/` — state, stress, capacity, heat_rate, forced_outage, inspection (built from Notebook 3)
- `src/dispatch/` — hourly, multi_mode, daily, modes, maintenance_schedule (built from Notebook 2)
- `src/cogen/` — host_steam_constraint, vom_adjustment (built from Notebook 2)
- `src/markets/` — rggi, capacity_market (built from Notebook 2)
- `src/ltsa/` — contract, inspections, overage, penalties (built from Notebook 4)
- `src/runners/` — single_path, monte_carlo (built from Notebook 4)
- Tests in `tests/` covering each module
- Notebooks become reference / onboarding material; their numerical results are reproduced from `src/` for parity validation

**Acceptance**: A test suite covers each module; rerunning any notebook by calling `src/` produces identical numerical results. **This is the gate from "notebook-time" to "model-time."** No further notebook-only work after Phase K.

**Depends on**: Phases G–J (notebook validation complete).

### Phase L — First end-to-end Monte Carlo Lockport run

**Goal**: Full multi-path multi-mode Lockport simulation using `src/` modules. First defensible model output.

**Deliverables**:
- Configuration file for the run (paths count, year horizon, mode list, gas-price reference assumption)
- Output bundles in `data/outputs/lockport/runs/<run_id>/` — daily arrays per the prototype's output schema, plus assumption-traced metadata header
- First analysis notebook in `data_analytics_notebooks/lockport_first_run_review/` — sanity checks (annual generation matches MOR? spark spread distribution sensible? LTSA cost split plausible?)
- A `model_card.md` per run summarizing: data vintages, assumption status distribution, list of LOW-confidence values flagged, list of placeholders still pending

**Acceptance**: A Lockport simulation runs without crashing, produces P10/P50/P90 distributions for spark, LTSA, and EOH; the model_card explains which results depend most on assumed vs real values.

**Depends on**: Phase K.

### Track-level dependencies

```
A (scaffold)
  ├─ B (tech defaults)
  ├─ C (Lockport public YAMLs)   ──┐
  ├─ D (Lockport operational)    ──┤
  ├─ E (Lockport paths)          ──┼─→ G (Notebook 1: load + validate)
  ├─ F (LTSA placeholder)        ──┘    │
                                        ▼
                                  H (Notebook 2: one day)
                                        │
                                        ▼
                                  I (Notebook 3: daily loop + feedback)
                                        │
                                        ▼
                                  J (Notebook 4: full path, optional v1)
                                        │
                                        ▼
                                  K (Graduate to src/)  ← parity gate
                                        │
                                        ▼
                                  L (Monte Carlo run)
```

Phases B–F parallelizable. Phases G–L strictly sequential. Phase K is the non-optional gate that flips notebooks from runtime to reference material.

---

## §9. Open questions

To resolve during execution, not before.

| Question | Phase to resolve in | Why it matters |
|---|---|---|
| What's the YAML loader's exact API for metadata access? `min_load_mw_meta` attribute, separate `meta()` method, or pydantic field metadata? | Phase G | Affects ergonomics of every modeling code call |
| Should `operating_profile.yaml` carry the full 5-year MOR daily DataFrame as parquet, or just the aggregated summary stats? | Phase D | If model needs day-level observed data for backcasting, it's parquet; if just for parameter seeding, summary is enough |
| How do we represent cogen must-run constraints in dispatch? Hour-by-hour minimum MW from DHTS schedule, or a fraction-of-month flag? | Phase I | DHTS is daily in MOR; need to decide how to translate to hourly constraint |
| Should RGGI allowance price be a static model parameter or a time series in `data/paths/`? | Phase I | RGGI clears auction-by-auction; if we want to capture price variation, it's a time series |
| Do we model NYISO ICAP capacity revenue in v1 or v2? | Phase K (or v2 follow-on) | ICAP is 20–40% of typical CCGT revenue but Lockport's mothball question complicates it |
| What's the right way to surface the operational-status flag (the "is Lockport actually running?" question) in model outputs? | Phase K | If the model assumes a plant that may be mothballed is fully available, outputs are not realistic |
| Does the prototype's `[ASSUME]` LTSA parameter set work as a first-pass default for Lockport, or do we need to swap it for Lockport-specific guesses? | Phase F | Lockport is a 1992 PURPA-era cogen; the Athens prototype assumes a modern merchant CCGT |
| When data room LTSA extraction completes, what's the refresh ceremony — overwrite `ltsa_terms.yaml`, version it, diff against placeholder? | Phase F + post | Avoid silent drift; keep the placeholder→real transition explicit |

---

## §10. Anti-patterns (Ulysses pact against future-self)

Things we will **not** do. Recording so we don't drift back into them.

| Anti-pattern | Why we won't |
|---|---|
| **Merge any of the four repos.** | diligence-extractor explicitly forbids this; the other boundaries are similar by analogy |
| **Pull diligence-extractor or renewablesinfo code into gt_models.** | They're specialized; their value is staying separate. Consume their outputs, not their internals. |
| **Symlink data instead of copying.** | Per D3 — self-contained > clever |
| **Build the Athens reference asset in `data/assets/`.** | Per D4 — Athens is architectural reference in `docs/extra/`, not a data-spine asset. Avoid the conflation. |
| **Build calibration mode before the model exists.** | Per D4 — calibration is a phase after a working model. |
| **Optimize before Lockport runs end-to-end.** | Phase K is the gate. Optimization (true MIP, capacity market, ancillaries) waits for v2. |
| **Copy-paste the prototype into `src/`.** | Per D1 — stepping stone, not source. |
| **Put model code in `docs/extra/`.** | The prototype stays there as frozen reference. New code goes in `src/`. |
| **Skip the notebook-validation track and build `src/` first.** | Per §8 revised sequencing — the notebooks force understanding before abstraction. Skipping them risks repeating the prototype's "designed in isolation" failure mode. |
| **Let notebooks live forever as runtime code.** | Phase K is the gate. After K, notebooks are reference/onboarding material; `src/` is the runtime. Don't let notebooks accumulate hidden state past graduation. |
| **Lose assumption tracking on any value.** | Per §6 — first-class principle. A YAML without status/source for every value is a bug. |
| **Write `src/` code that imports from `data/` via relative paths.** | The loader layer (`src/io/`) is the only place data paths live. Models import from the loader. |
| **Run a model and call it valid because it doesn't crash.** | Phase K acceptance is the model_card with assumption-status distribution — outputs without that context aren't shippable. |
| **Build the dashboard before there's a working model with outputs.** | Future-scope only. |
| **Restructure model-gpr or renewablesinfo as part of this work.** | Out of scope. |
| **Build for hypothetical future assets (Deal #2, Deal #3) before Lockport ships end-to-end.** | Multi-asset abstraction comes from doing 2–3 assets, not designing for it upfront. |

---

## §11. Glossary + cross-references

### Cross-reference back to upstream work

- **renewablesinfo lab pass for dispatch params**: `~/code/personal/renewablesinfo/integration/dispatch_params/` — AUDIT.md is the per-cell source attribution
- **renewablesinfo Lockport brief**: `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_data_brief.md` — team-shareable public-data summary
- **renewablesinfo Lockport equipment profile**: `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_equipment_profile.md` — internal working version with planning context
- **renewablesinfo dispatch input audit**: `~/code/personal/renewablesinfo_org/docs/extra/dispatch_modeling/01_input_audit.md` — what's available in public data
- **renewablesinfo dispatch_operating_params design doc**: `~/code/personal/renewablesinfo_org/docs/design/dispatch_operating_params.md` — the platform-side decision to defer UI; gt_models inherits the lookup as data only
- **diligence-extractor MOR analysis**: `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb` — heat rate by mode + cold-start gas + operational-status correction
- **diligence-extractor framework north-star**: `~/code/personal/diligence-extractor/docs/plans/framework_north_star.md` — long-horizon vision; explicitly bounds diligence-extractor away from being a dispatch model
- **diligence-extractor tabular data inventory**: `~/code/personal/diligence-extractor/docs/tabular_data_inventory.md` — maps 760+ Excel/CSV files in Lockport data room to specific modeling inputs
- **model-gpr Lockport data folder**: `~/code/work/infrasure_git_codes/model-gpr/local_data/lockport_energy_associates_lp/` — NEG WEST_LEA_LOCKPORT node + gas history + weather
- **model-gpr Step 1 plan**: `~/code/work/infrasure_git_codes/model-gpr/local_docs/plans/price_forwards/01_phase1_forward_adjusted_forecast.md`
- **gt_models prototype**: `docs/extra/gas-turbine-digital-twin/` — Athens implementation; the architectural reference
- **gt_models understanding doc**: `docs/extra/understanding_of_gas_turbine_digital_twin.md` — reader's guide to the prototype
- **gt_models framework V2**: `docs/InfraSure_ModelingFramework_V2.md` — full methodology
- **gt_models Step 1 plan**: `docs/plans/step_1_climate_price_scenario_plan.md`
- **gt_models Step 2 plan**: `docs/plans/step_2_execution_blueprint_plan.md`

### Glossary

| Term | Meaning |
|---|---|
| **the four-repo system** | renewablesinfo_org + diligence-extractor + model-gpr + gt_models |
| **data spine** | the `data/` folder in gt_models — self-contained inputs the model consumes |
| **code spine** | the `src/` folder in gt_models — the rebuilt model |
| **the prototype** | the Athens implementation in `docs/extra/gas-turbine-digital-twin/`. Architectural reference; not edited, not copied verbatim. |
| **stepping stone** | per D1 — the prototype's role: replicate the conceptual model + architecture, redesign the implementation with real data clarity |
| **D1–D5** | the five locked decisions in §5 |
| **assumption status** | per §6 — every value carries one of nine status codes (real_observed, real_reported, real_computed, assumed_techclass, assumed_vendor, assumed_industry, assumed_derived, placeholder, not_applicable) |
| **provenance** | the data lineage for an artifact — where it came from, when it was copied, what version |
| **model_card** | the assumption-status distribution + caveat summary that accompanies every model output bundle |
| **Lockport-only v1** | per D4 — Lockport is the only asset in `data/assets/` for v1. Multi-asset abstraction comes later. |
| **calibration** | back-testing modeled vs realized dispatch. Out of scope for v1; happens after we have a working model. |

---

## §12. How this gets executed

Per `feedback_design_doc_workflow`:

1. **This doc** is the research → reason → decide artifact. Reviewing now.
2. **Each phase from §8** gets its own focused execution session. Don't run multiple phases in parallel unless the dependency graph in §8 explicitly allows it.
3. **Update this doc** with status checkmarks per phase as they complete (or with deviations recorded if a phase's deliverables change).
4. **When all Track 1 phases complete**, write a "Track 1 complete" status update at the top of this doc.
5. **When Phase K passes acceptance**, this doc moves toward `docs/plans/completed/` and a "what we learned" addendum is added.

No timelines (per `feedback_no_timelines`). Phases are independently shippable; order is firm but pacing is whatever-it-takes.

---

## §13. Status log

| Date | Event |
|---|---|
| 2026-05-14 | Plan drafted. Awaiting user review. |
| 2026-05-14 | §8 revised — notebook-first sequencing. Phases G–J become notebooks; Phase K becomes "graduate to `src/`"; Phase L is the first Monte Carlo run. Sub-plan folder `consolidation_plan/notebooks/` created with detailed plan for Notebook 1. |
| 2026-05-14 | **Phase A complete** — scaffold built. 13 README/reference files across `data/`, `src/`, `dashboard/`, `notebooks/`, `docs/reference/`, `docs/assumptions/`. Top-level `.gitignore` added (excludes `data/outputs/` and standard Python/Jupyter ignores). Ready for Phase B (migrate tech-class defaults). |
| 2026-05-14 | **Phase B complete** — tech-class dispatch params migrated from lab. `data/tech_class_defaults/` populated with parquet (20×35) + CSV + 4 source refs (Kumar 2012, ATB 2024, AEO 2026, PJM M-15) + AUDIT.md. `docs/reference/tech_class_dispatch_params_summary.md` written (digest of methodology decisions). `tests/test_tech_class_defaults.py` — 31 tests, all passing. SHA256 checksums recorded in `data/tech_class_defaults/README.md` provenance. |
| 2026-05-14 | **Phase E complete** — Lockport paths migrated from model-gpr. 6 files copied (lmp_da_hourly 81,742 rows; lmp_rt_intervals 231,813 rows; lmp_west_zone_da 81,742 rows; gas_price_history 14,701 rows × 8 hubs incl. Algonquin Citygate; weather_hourly 403,248 rows × 19 cols, 46 yr UTC index; seas5 JSON forecast). 32 MB total. SHA256 + date ranges recorded in `data/paths/lockport/README.md`. |
| 2026-05-14 | **Phase C complete** — Lockport public YAMLs written. `identity.yaml`, `engineering.yaml`, `market_context.yaml`, `caveats.md`, `provenance.md`. Every leaf value carries `{value, status, source}` per §6 + status_taxonomy.md. Engineering covers 4 generators (3 CT + 1 CA) with capacity matrix, dual-fuel matrix, min loads, ambient sensitivity, CHP flags. `caveats.md` documents the 10 modeling caveats (operational status correction, cogen markup, multi-mode dispatch, dual-fuel switching, EIA cold-start clustering, steam-host constraint, ambient sensitivity, vintage, merchant cogen). |
| 2026-05-14 | **Phase D complete** — `operating_profile.yaml` written from diligence-extractor MOR notebook. Mode-segmented heat rate (3×CC_full 8,901 / 2×CC 9,598 / 1×CC 10,424 Btu/kWh, volume-weighted from 291 clean CC days), 2023 cross-validation within <1% of eGRID placeholder, cold-start gas summary (35 warming days, 88,785 MMBtu / 5 yr), 2024 generation correction (192,494 MWh actual), DHTS host-steam patterns (~80K MMBtu/yr), mode-classifier thresholds. All values `real_observed` from the MOR Stage 2 analysis. |
| 2026-05-14 | **Phase F complete** — `ltsa_terms.yaml` written with all ~40 values flagged `status: placeholder`. Seeded from Athens prototype `[ASSUME]` defaults. Every placeholder has a `validation_path` pointing to data room file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` or original PURPA contract filings. Covers the 7 LTSA cost streams + forced-outage coverage classification. |
| 2026-05-14 | **Track 1 complete** — full data spine populated. 98 tests across `test_tech_class_defaults.py` (31) and `test_lockport_static_profile.py` (67) all passing. Assumption-tracking discipline enforced at the schema level (every leaf has valid status + source; placeholders have validation_path; assumed values have confidence). Ready for Track 2 (notebooks). |
| 2026-05-14 | **Phase G complete (Notebook 1)** — `notebooks/01_data_spine_load_validate.ipynb` + paired `.py` (jupytext percent format). Runs end-to-end with 8 hard cross-validation checks passing. Helper functions `v()` and `m()` define the assumption-tracked access pattern. **266 leaf values aggregated**: 80.1% real_*, 17.7% placeholder, 1.5% assumed_industry, 0.8% not_applicable. **Two soft warnings surfaced as real findings**: (1) **Algonquin Citygate gas hub has only 2014-2017 coverage (698 rows) — only Henry Hub has deep history** — needs resolution before Notebook 2's gross-margin proxy can model 2018+ delivered gas; (2) Weather data ends 2025-12-31, 4-month gap before LMP through 2026-04-29 — sufficient for 2017-2025 modeling. Stage 1 findings + decision log captured at notebook end. `docs/assumptions/placeholder_caveats.md` documents the LTSA-placeholder situation per user request. Weather TZ-conversion recipe documented in `data/paths/lockport/README.md`. |
| 2026-05-14 | **`docs/decisions/` folder established** + first ADR. Pattern: one Markdown file per substantive decision with full reasoning trail (context → decision → reasoning → consequences → alternatives → references). **ADR-001 "Gas hub treatment for v1 dispatch model"** documents the Frame A choice: use Henry Hub directly for v1, defer Algonquin basis modeling to v2. Captures the dual-fuel discussion, the honest reconsideration of "central modeling capability" framing, and the alternatives rejected (B/C/D). `market_context.yaml.gas_market.v1_modeling_choice` records the structured decision (`hub_used_for_delivered_gas = "Henry Hub"`, `status: assumed_industry`, `confidence: LOW`, validation_path to future ADR). `caveats.md` §11 cross-references. **Phase E.b (basis-derivation notebook) cancelled** — Frame A doesn't need it. Next step: Phase H — Notebook 2 (one day of dispatch). |
| 2026-05-14 | **Notebook 2 plan drafted** at `docs/plans/consolidation_plan/notebooks/02_one_day_dispatch.md`. ~13 sections, ~500 lines. Inherits decisions from Notebook 1 + ADR-001 (Henry Hub, helper pattern, TZ convention). Adds dispatch-specific decisions: programmatic day picker (2023 P75-P90 daily-peak-LMP), RGGI at $17/short ton CO2 with EPA-standard 117 lb CO2/MMBtu for NG, mode-choice heuristic (max gross margin per mode, no min-load enforcement yet), clean-vs-degraded scaffolding (identical in N2; differs in N3 once state evolves), cogen "both modes" comparison (must-run-yes vs must-run-no for the chosen day), VOM/ambient/startup/dual-fuel all explicitly deferred to N3+. Ready for execution. |
| 2026-05-14 | **Phase H complete (Notebook 2)** — `notebooks/02_one_day_dispatch.{ipynb,py}` paired via jupytext. Runs end-to-end in 3.3s; 11 code cells, 0 errored. **Day picker landed on 2023-07-12 (Wed)** — peak LMP $61.50/MWh, mean $35.96, within the P75-P90 band of 52 candidate summer mid-week days. **Dispatch behavior clean**: 13 hours 3×CC_full (peak demand 11am-11pm), 11 hours offline (off-peak), exactly 1 mode transition (no whipsawing). **No-constraint daily summary**: 2,877 MWh dispatched, $129K revenue, $35,354 gross margin. **Must-run daily summary**: 4,240 MWh, $164K revenue, $18,283 gross margin — i.e., cogen constraint costs ~$17K of margin that day. **RGGI sensitivity**: at $30/ton (vs base $17/ton), off-hours rise from 11 to 16 — confirms RGGI should be a Phase L parameter, not a hardcoded constant. All 5 sanity checks pass (P&L consistency, mode-stability, MW ≤ plant max, etc.). Stage 1 findings + 7 open questions for Notebook 3 captured. |
| 2026-05-14 | **Notebook 3 plan drafted** at `docs/plans/consolidation_plan/notebooks/03_daily_loop_feedback.md`. ~13 sections, ~600 lines. Phase I — proves the recursive feedback architecture. 30-day window, state vector with 9 engineering accumulators (EOH, hr_recov, fouling, dc, df, tbc_time, tbc_thresh, hrsg_cycles, rotor_life) + 5 operational continuity flags. Per-day loop follows prototype's 9-step order. **First notebook with diagnostic plots** (4 plots: state trajectory, P_forced decomposition, daily MWh + cumulative margin, clean-vs-degraded attribution). New decisions: block-level state (not per-generator), cogen synthetic must-run flag (temp-based proxy until MOR DHTS extraction), cogen VOM markup ×1.35, ambient derate via linear interp between summer/winter, prototype constants inherited with Lockport-override opportunities flagged for N4. Inspection threshold tracking only (events deferred to N4). Forced-outage probability computed but no event sampling (deferred to N4). Ready for execution. |
| 2026-05-14 | **Phase I complete (Notebook 3)** — `notebooks/03_daily_loop_feedback.{ipynb,py}` paired via jupytext. Runs in 3.3s; 15 code cells, **4 plots embedded**, 0 errored. **Window chosen**: 2023-07-01 → 2023-07-31 (full July; 24 high-LMP-days in July 2023, the most-dispatched-friendly summer month). **30-day headline numbers**: 415 fired hours, 27 starts, 83,948 MWh dispatched, **$913K cumulative gross margin (degraded)**, $11,535 cumulative loss to degradation. **State evolution**: EOH 24,000 → 24,650 (+650 over 30 days), HR drift 0.0% → 0.885%, P_forced 1.0% → 1.19% (modest growth — low-CF asset). **6 cogen must-run days flagged** by synthetic temp ≤ 69.8°F proxy (e.g., July 8-9, 19, 21, 29) — these days plant runs 24h even at negative margin (visible $4K-$33K losses on those days). **Single high-LMP day (July 28, peak $200.6/MWh)** generated $278K — illustrates Lockport's peaker economics. All 10 sanity checks pass. Ready for Notebook 4 (full path + Mode A/B/C + LTSA cost streams). |
| 2026-05-14 | **ADR-002 written + Correction 1 applied to N3.** Post-N3 review: user clarified Lockport has more granular configuration than prototype assumed; should use Lockport-specific data not Athens defaults. **ADR-002 "Lockport-specific vs Generic F-class — calibration inventory"** writes the comprehensive map: Bucket A (Lockport-specific, e.g., heat rate by mode, LMP at PTID 23791, ambient sensitivity), Bucket B (generic F-class defaults — state evolution constants, START_EOH_COST, TBC Weibull, HRSG age scaling), Bucket C (placeholder pending data room — LTSA terms). **Correction 1**: MOR-observed cold-start warming gas (2,537 MMBtu/cold start) now wired into N3 fuel cost as `real_observed` Lockport data. **Honest finding**: in this July 2023 high-LMP window, 0 of 27 starts classified as cold (plant cycles daily; hrs_off never reaches 72h) — correction is structurally correct but $0 impact in this window. MOR observed ~7 cold starts/year (35/5yr), predominantly winter/shoulder months. Phase L 10-yr Monte Carlo will accumulate ~70 cold starts → ~$620K warming gas cost captured by this correction. Also documented: RGGI uses EPA AP-42 (117 lb/MMBtu fuel-side, dispatch-correct) not Lockport eGRID (1,097 lb/MWh plant-side, would double-count HR). `caveats.md` §12 + `decisions/README.md` index updated. |
| 2026-05-14 | **Notebook 4 plan drafted** at `docs/plans/consolidation_plan/notebooks/04_full_path_mode_comparison.md`. ~600 lines, 13 sections. The v1 capstone: 9-year historical replay 2017→2025 × 3 modes (A/B/C) × 7 LTSA cost streams + inspection event triggering + forced outage event sampling. Cell-by-cell sketch covers: Mode A/B/C wear-penalty mechanic (GT_WEAR_FRACTION × Kumar start C&M × mode-dependent EOH-headroom multiplier; B caps at 2.5×, C caps at 4.0×), maintenance schedule pre-builder with calendar shoulder-snap (April / October) and hard-stop overage trigger (+1,500 EOH), inspection state-reset machinery (CI partial; MI more aggressive incl. tbc_thresh resample), forced-outage event sampling (Bernoulli daily; cause weighted by P_GT/P_HRSG/P_BG; lognormal duration), LTSA accrual logic for all 7 streams, MOR backtest validation (target 192,494 MWh 2024 + ~7 cold starts/yr + 65/26/9 mode mix), `model_card.md` generation per `assumptions/README.md`, and 6 plots (state by mode, P_forced by mode, cumulative spark, LTSA stacked-area, mode-comparison summary, inspection timeline). Ready for execution. |
| 2026-05-15 | **Phase J complete (Notebook 4 — v1 capstone)** — `notebooks/04_full_path_mode_comparison.{ipynb,py}` paired via jupytext. **9-year × 3-mode = 9,861 day-mode executions in ~50s.** All 16 sanity checks pass. **6 plots embedded** (state-by-mode, P_forced-by-mode, cumulative-margin, LTSA-stream stacked-area, mode-comparison bars, inspection-timeline). **First `model_card.md` generated** — bundled at `data/outputs/lockport/runs/notebook4_<ts>/` along with daily/state/ltsa/inspection/forced-outage parquets + `run_config.yaml`. **Headline mode-comparison (seed=42, single-path)**: Mode A spark $15.81M, LTSA $218.89M, **Net –$203.1M**; Mode B $7.88M / $221.0M / **–$213.1M**; Mode C $10.08M / $220.4M / **–$210.3M**. Mode A wins Net P&L by ~$10M but pays ~$32M HR penalty + $14M MI cost. **LTSA stream breakdown (Mode A)**: fixed monthly fee 49.2% of total; start overage 18.0%; HR penalty 14.6%; forced outage 9.0%; MI events 6.4%; EOH reserve 2.6%; CI 0%; avail penalty 0.2%. **Each mode triggers 1 inspection** (Mode A calendar-fires MI 2025-04-01 as projected; Modes B/C hard-stop-fire MI at end-of-sim when EOH overage > 1,500). **Forced outage events**: 35 per mode over 9 yr (was 86-87 before fixing inherited aging-formula bug from N3 — `year_frac` was being treated as years-elapsed when formula expects fraction-of-10-yr-aging-window; fix capped at min(years_elapsed/10, 1.0)). **MOR backtest divergences (documented honestly, not fail-gated)**: modeled 2024 generation 468K MWh vs MOR-observed 192K (model over-commits ~2.4×; missing planned outages, dispatch derates, ramp constraints); modeled 2xCC share 0% vs MOR 26% (single-CT-down scenarios not modeled in v1); cold starts 14/yr modeled vs ~7/yr MOR. **Mode A vs C trade-off in v1**: doesn't survive Lockport's low-CF profile cleanly — wear-penalty barely activates because EOH headroom stays > 4,000 for most of the horizon (Lockport's CF is too low for the mechanic to bind hard). **Phase L Monte Carlo needed for headline conclusions** — single-path realization has too much RNG noise to validate the prototype's Athens trade-off direction. **5 sensitivity-hot-spots flagged** for Phase L sweeps per ADR-002 Bucket B: P_BG_AGE_MAX, FATIGUE_PER_*_START, TBC_WEIBULL_ETA, FOULING_*, EOH_RATE_ESTIMATE_PER_DAY. Ready for Phase K (graduate notebooks → src/) or Phase L (Monte Carlo) — user decision next. |
| 2026-05-15 | **MOR ground-truth backtest + steam-only mode added.** Extracted 5 years of daily MOR data (1,826 rows, 2021-2025) from diligence-extractor data room → `data/paths/lockport/mor_daily.parquet`. **Discovered Lockport operates in steam-only mode 25.2% of days** (460/1826) — 0 MWh + non-zero gas + non-zero DHTS delivery. Mechanism confirmed via EIA-860 6_2 boiler_type="Db" (Duct Burner). Updated N4 with steam-only branch in must-run logic: when peak LMP × 3×CC HR can't clear break-even, plant runs steam-only for the day (0 MWh, 0 EOH wear, ~871 MMBtu gas/day from MOR median). **Re-run results (Mode A)**: spark $15.81M → $36.08M; LTSA $218.89M → $203.24M; **Net P&L −$203.1M → −$167.2M (+$35.9M improvement)**. Mode B improved further (−$213M → −$143M) because its reduced cycling no longer triggers MI in 9-yr. Over-commit ratio vs MOR: **2.22× → 2.07×**. Also added `boiler_type/id/count` to engineering.yaml (GEN4), wired `min_load_mw` constants into N4 (no-op in v1 partial-dispatch but documented for v2). **New methodology folder**: `docs/methodology/{pnl_ledger, architecture, dispatch_mechanics, gaps_and_priorities, glossary}.md` + `extra/backtest_findings.md` (~2,500 lines total). **New guides folder**: `docs/guides/pulling_specs_from_powerplantsinfo.md`. |
| 2026-05-15 | **Notebook 5 complete — Model-vs-MOR deep-dive.** `notebooks/05_model_vs_actual.{ipynb,py}` paired via jupytext. 17 code cells, **11 plots embedded**, 0 errors. Three themes: (1) **Volume** — annual/monthly/cumulative generation comparison + capacity factor by year; (2) **Mode mix** — operating mode share comparison (model vs MOR-inferred); structural math showing why 2×CC never wins; steam-only days head-to-head with calendar dot plot; policy mode A/B/C divergence point analysis; (3) **Mechanics** — cold start frequency, heat rate by mode, dispatch decision examples. Includes EIA-923 sidebar showing federal data lag. **Window-matched steam-only recall corrected: 18% (not 47% as earlier estimated)**; precision 95.4%. **Headline takeaway**: model's structural divergence is concentrated in mode-mix (50% 3xCC vs MOR's ~30%; 0% 2xCC vs MOR's ~14%) which needs per-generator state in v2. The conservative steam-only trigger catches 1 in 5 real steam-only days — refinement opportunity. |
