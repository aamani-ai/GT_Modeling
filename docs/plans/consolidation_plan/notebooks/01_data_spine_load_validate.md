# Notebook 1 — Data Spine: Load + Validate

> **Status**: Plan drafted 2026-05-14. Awaiting user review before execution.
> **Notebook path (when built)**: `notebooks/01_data_spine_load_validate.ipynb`
> **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) — execution Phase G
> **Sibling plans**: [`README.md`](./README.md) — notebook-track overview
> **Prerequisites**: Parent plan Phases A–F complete (data spine populated)

---

## §1. Purpose

First end-to-end load of the gt_models data spine. Verifies that every file we'll need actually exists, reads cleanly, conforms to its schema, and is self-consistent. **Doubles as the de-facto loader specification** — by writing the loading code linearly, we surface exactly what the eventual `src/io/` loader needs to support.

Goals, in priority order:

1. **Catch schema problems early.** If the YAML structure is awkward, or the YAML loader has to do gymnastics to access a value, that's the time to fix the schema — before three more notebooks depend on the awkward shape.
2. **Cross-validate the data spine.** Files exist + read + conform individually is necessary but not sufficient. Do the timestamps in LMP align with weather? Does gas history cover the LMP date range? Do generator capacities sum to plant total? Are all assumption-status codes valid?
3. **Produce the first assumption-status summary.** Preview of what every model_card output will eventually contain: count of values by status (real_observed / real_reported / assumed_techclass / placeholder / etc.), distribution by confidence, list of LOW-confidence cells flagged, list of placeholders still pending.
4. **Demonstrate the loader convention.** Show — by example, in a notebook — how a modeler will eventually call `asset.engineering.generators['GEN1'].min_load_mw` and get the value, while `asset.engineering.generators['GEN1'].min_load_mw_meta` returns provenance.

This notebook is **read-only and computation-free**. No dispatch, no state update, no forecasting. The point is to prove the inputs are sound before we start using them.

---

## §2. Inputs (files this notebook reads)

| File | Format | Source phase | What it contains |
|---|---|---|---|
| `data/assets/lockport/identity.yaml` | YAML | C | Plant ID, name, operator, sector, status, cross-system IDs |
| `data/assets/lockport/engineering.yaml` | YAML | C | 4 generators with capacity, dual-fuel matrix, min loads, cold-start times |
| `data/assets/lockport/market_context.yaml` | YAML | C | NYISO node assignments, hub, BA, eGRID subregion, voltage, regulatory status |
| `data/assets/lockport/operating_profile.yaml` | YAML | D | Mode-segmented heat rate, cold-start gas, run-streak patterns from MOR |
| `data/assets/lockport/ltsa_terms.yaml` | YAML | F | LTSA contract structure (placeholder values until data room extraction) |
| `data/assets/lockport/caveats.md` | Markdown | C/D | Cogen / mothball / fuel-switching caveats |
| `data/assets/lockport/provenance.md` | Markdown | C/D/E/F | Where each artifact came from + dates |
| `data/paths/lockport/lmp_da_hourly.parquet` | Parquet | E | NYISO DA LMP at PTID 23791 (Lockport node) |
| `data/paths/lockport/lmp_rt_intervals.parquet` | Parquet | E | NYISO RT LMP at same node |
| `data/paths/lockport/lmp_west_zone_da.parquet` | Parquet | E | NYISO WEST zone DA backup reference |
| `data/paths/lockport/gas_price_history.parquet` | Parquet | E | 29 yr gas history across 8 hubs incl. Algonquin Citygate |
| `data/paths/lockport/weather_hourly.parquet` | Parquet | E | 46 yr hourly weather (19 variables) at plant coordinates |
| `data/paths/lockport/weather_forecast_seas5.json` | JSON | E | SEAS5 forecast init Apr 2026 |
| `data/tech_class_defaults/dispatch_params_lookup.parquet` | Parquet | B | 20 rows × 35 cols tech-class lookup |
| `data/tech_class_defaults/dispatch_params_values.csv` | CSV | B | Human-readable mirror |

No external dependencies. No model-gpr / renewablesinfo / diligence-extractor reads at notebook runtime — everything has been copied into `data/` per the parent plan §5 D3.

---

## §3. Cell-by-cell sketch

Adapted from the dimensions framework in diligence-extractor's `notebook_methodology.md` (§A schema / §B units / §C completeness / §D conventions / §E cross-source / §F reproducibility).

### §3.A — Setup

Imports, conventions, repo-root resolution, dataset version stamps.

```python
import pandas as pd
import yaml
from pathlib import Path
from dataclasses import dataclass
import json

REPO_ROOT = Path("..").resolve()  # notebook lives in notebooks/, repo root is parent
DATA_DIR = REPO_ROOT / "data"

ASSET = "lockport"  # v1 scope per parent plan §5 D4
```

Also print: data vintage banner (refresh dates from `provenance.md` files).

### §3.B — Inventory the data spine

Walk the `data/` tree. Confirm every expected file exists. List filesizes + row counts (for parquet).

| Check | Pass criterion |
|---|---|
| All 15 §2 files present | None missing |
| YAMLs are non-empty | All files > 0 bytes |
| Parquets are non-empty | All files have ≥ 1 row |
| Total `data/` size sane | < 100 MB (gut check) |

Output: an inventory DataFrame `(file, format, size_kb, rows, last_modified)`. If anything is missing, halt with a clear message — the rest of the notebook can't proceed.

### §3.C — Load + display tech-class defaults

The simplest artifact to load — no nested structure, no metadata convention to invent. Validates that parquet loading works and the dispatch_params lookup has the right shape.

```python
tech_defaults = pd.read_parquet(DATA_DIR / "tech_class_defaults" / "dispatch_params_lookup.parquet")
```

Display:
- Row count + column list (expect 20 rows × 35 cols)
- Coverage: `tech_defaults.groupby(['prime_mover_code', 'aero_derivative']).size()`
- Confidence-tier distribution per parameter (recovers the lab pass distribution: 11 HIGH / 40 MEDIUM / 74 LOW / 19 NoSource across 144 cells)
- Filter to the 2 rows that apply to Lockport: `prime_mover_code in ('CT', 'CA') & vintage_class == '<2000' & ~aero_derivative` — should be 2 rows

### §3.D — Load + display Lockport asset YAMLs

The first real test of the assumption-tracked YAML convention. For each of the 5 YAML files, load and display with metadata visible.

```python
def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

identity = load_yaml(DATA_DIR / "assets" / ASSET / "identity.yaml")
engineering = load_yaml(DATA_DIR / "assets" / ASSET / "engineering.yaml")
market_context = load_yaml(DATA_DIR / "assets" / ASSET / "market_context.yaml")
operating_profile = load_yaml(DATA_DIR / "assets" / ASSET / "operating_profile.yaml")
ltsa_terms = load_yaml(DATA_DIR / "assets" / ASSET / "ltsa_terms.yaml")
```

For each, show:
- Top-level keys
- A sample leaf value with full metadata block (e.g., `engineering.generators.GEN1.min_load_mw` → `{value: 30.0, status: real_reported, source: "EIA-860 schedule 3_1 Y2024", caveat: ...}`)
- Count of leaf values
- Status histogram (how many `real_*` / `assumed_*` / `placeholder`)

This is where we feel out whether the nested-with-metadata format works in practice. **If it's painful here, change the schema before Notebook 2.**

### §3.E — Load + display Lockport paths

The time series. Validate schemas, date ranges, timestamp handling.

```python
lmp_da = pd.read_parquet(DATA_DIR / "paths" / ASSET / "lmp_da_hourly.parquet")
lmp_rt = pd.read_parquet(DATA_DIR / "paths" / ASSET / "lmp_rt_intervals.parquet")
lmp_west = pd.read_parquet(DATA_DIR / "paths" / ASSET / "lmp_west_zone_da.parquet")
gas = pd.read_parquet(DATA_DIR / "paths" / ASSET / "gas_price_history.parquet")
weather = pd.read_parquet(DATA_DIR / "paths" / ASSET / "weather_hourly.parquet")
with open(DATA_DIR / "paths" / ASSET / "weather_forecast_seas5.json") as f:
    weather_forecast = json.load(f)
```

For each, show:
- Shape (rows × cols)
- Date range (min, max of time index)
- Column list
- Null counts per column (especially LMP — outages show as nulls)
- Time-zone handling: confirm everything is UTC or NYISO local, document explicitly
- Currency / unit columns: confirm $/MWh for LMP, $/MMBtu for gas, °F or °C for temperature (must be explicit — see Step 1 plan §"Weather Path" required fields)

### §3.F — Cross-validation checks

This is the most important section. Catch inconsistencies between sources before they corrupt downstream modeling.

| Check | What it confirms | Halt if fails? |
|---|---|---|
| `sum(generator.nameplate_capacity_mw for generator in engineering.generators) ≈ 221.3` | Generator capacities sum to plant total | Yes |
| `engineering.plant.id == identity.plant.id == 54041` | Plant ID consistent across YAMLs | Yes |
| `lmp_da` date range covers a meaningful subset of `weather` date range | LMP and weather overlap | Warn, don't halt |
| `gas` date range covers `lmp_da` date range | Gas history covers LMP history | Warn |
| All `status` codes in YAMLs are in the §6 taxonomy from parent plan | No typos / invalid statuses | Yes |
| All `placeholder` values have a non-empty `validation_path` | Placeholders point to where the real value will come from | Warn |
| `market_context.lmp_node.value` matches a node present in `lmp_da.location` | NYISO PTID consistent | Yes |
| Tech-class defaults filter for Lockport `(CT, <2000, False)` and `(CA, <2000, False)` returns exactly 2 rows | Tech-class join logic works | Yes |
| Confidence-tier distribution in `tech_defaults` matches lab pass numbers | Lab pass parquet not corrupted | Warn |
| `operating_profile.heat_rate_by_mode.3xCC_full.value ≈ 8901` Btu/kWh | MOR analysis value preserved through YAML | Yes |

Output: a `validation_results` DataFrame `(check, pass/fail/warn, detail)`.

### §3.G — Assumption-status distribution (model_card preview)

Aggregate across all loaded YAML leaf values.

| Output | Format |
|---|---|
| Total values loaded (count) | Single number |
| Count by status code | Table — `real_observed`, `real_reported`, `real_computed`, `assumed_techclass`, `assumed_vendor`, `assumed_industry`, `assumed_derived`, `placeholder`, `not_applicable` |
| Count by confidence (for assumed values only) | Table — HIGH / MEDIUM / LOW |
| Percent of total that is `real_*` | % |
| Percent of total that is `assumed_*` | % |
| Percent of total that is `placeholder` | % |
| List of all LOW-confidence values | Full table with field path + value + source |
| List of all `placeholder` values | Full table with field path + validation_path |

This is the kernel of what every model_card will eventually show. The asymmetry that matters for downstream defensibility: **the lower the % of real values, the more the model output is an assumption about an assumption**.

### §3.H — Lockport ↔ tech-class lookup join

Sanity check that the modeling-side join works. For each Lockport generator, derive its (prime_mover_code, vintage_class, aero_derivative) key, look it up in tech_defaults, and display the values that would flow into the model.

```python
for gen_id, gen in engineering.generators.items():
    pm = gen.prime_mover_code.value
    op_year = identity.plant.operating_year.value  # or per-generator
    vintage = derive_vintage_class(op_year)  # → "<2000"
    aero = False  # for CT/CA, not GT
    row = tech_defaults[
        (tech_defaults.prime_mover_code == pm) &
        (tech_defaults.vintage_class == vintage) &
        (tech_defaults.aero_derivative == aero)
    ]
    display(gen_id, pm, vintage, row)
```

Expected: 3 generators (GEN1-3, CT) get the (CT, <2000, False) row; 1 generator (GEN4, CA) gets the (CA, <2000, False) row. Both rows carry identical Kumar block-level values per the lab pass methodology Decision 2.

### §3.I — Stage 1 findings

Markdown cell at the end of the notebook. Records:

1. **What loaded cleanly** — list the artifacts that worked without intervention
2. **What needed schema adjustment** — any YAML structures that were awkward to access; recommend the parent plan §6 schema update if any
3. **What cross-validation surfaced** — any failed or warning checks; what they imply about the data spine
4. **Assumption-status distribution headline** — one-sentence summary of the real-vs-assumed split for Lockport v1
5. **Open issues for Notebook 2** — what unresolved questions need to be settled before the dispatch notebook can be written

This cell becomes the input to writing `02_one_day_dispatch.md`.

### §3.J — Decision log

Conventions chosen during this notebook's execution. Captures the choices that future code (including `src/io/`) inherits.

| Decision | Choice | Rationale |
|---|---|---|
| YAML loader library | `pyyaml.safe_load` for v1; pydantic for schema validation in `src/io/` later | Simple now, structured later |
| Metadata access pattern | Nested dict access — `gen['min_load_mw']['value']` for direct, `gen['min_load_mw']['source']` for provenance. Wrapper class in `src/io/` later. | TBD — may be revised in stage 1 findings |
| Time-zone handling | UTC for storage; convert to NYISO local at display time | Per Step 1 plan path-table schema |
| LMP location filter | Use primary node (PTID 23791) for CTs; PTID 323769 for ST (GEN4) | Per market_context.yaml |
| Tech-class join key derivation | `(prime_mover_code, vintage_class, aero_derivative)` triple from engineering.yaml + lab-pass-defined vintage cuts | Per parent plan §7 |
| Outlier handling | Out of scope — pure load + validate, no computation | — |
| Missing values | Halt if structural (file missing); warn if data-quality (null LMPs); document if intentional (placeholders) | — |

---

## §4. Conventions chosen for this notebook

Top of the notebook, displayed in the header cell so a reader can scan them quickly. Mirrors the MOR notebook's "Conventions used in this notebook (decision log)" pattern.

(Same content as §3.J above — repeated in the notebook itself for in-context discoverability.)

---

## §5. Validation checks (acceptance criteria)

Notebook is "done" when:

- [ ] All §3.B inventory checks pass (no missing files)
- [ ] All §3.C–§3.E loads complete without errors
- [ ] All §3.F cross-validation checks pass (or fail with documented exceptions)
- [ ] §3.G assumption-status distribution table generated successfully
- [ ] §3.H Lockport ↔ tech-class join returns the expected 2 rows
- [ ] §3.I Stage 1 findings cell is filled in with concrete observations
- [ ] §3.J Decision log is recorded (any new conventions captured)
- [ ] No cells crash the notebook on re-run from a fresh kernel (reproducibility check per `notebook_methodology.md` §F)

---

## §6. What this notebook surfaces

Questions / observations this notebook is designed to expose. **These are the inputs to writing Notebook 2's plan.**

| Question | How this notebook answers it |
|---|---|
| Does the nested-with-metadata YAML format actually work in practice? | §3.D leaf-access patterns — is `gen['min_load_mw']['value']` painful enough to want a wrapper class? |
| Is the assumption-status taxonomy complete? | §3.G — any leaf value that didn't fit one of the 9 statuses surfaces a taxonomy gap |
| Are the time-series schemas (LMP, gas, weather) cleanly aligned? | §3.E + §3.F — timezone, units, date-range cross-checks |
| Does the dispatch_params lookup table contain the right rows for Lockport? | §3.H — exactly 2 rows expected |
| Is the placeholder-value handling sufficient? | §3.G + §3.F — placeholders need validation_path notes |
| What % of Lockport's v1 inputs are real vs assumed? | §3.G — first concrete answer to the "how defensible is this" question |

---

## §7. What this notebook does NOT cover

- **Any modeling computation.** No dispatch, no state update, no fuel cost, no spark spread, no forecasting. Pure load + validate.
- **Time-series operations.** Doesn't compute heat rate from generation × fuel, doesn't compute spark spread from LMP and gas. Those are downstream notebooks.
- **Outlier detection in the time series.** Just confirms schemas; doesn't filter or clean.
- **Forecast path generation.** No Step 1 scenario engine work here.
- **Tech-class lookup updates.** The lab pass parquet is read-only; updates happen in the lab repo.
- **Asset_loader API design in `src/io/`.** This notebook *inspires* the loader API; doesn't implement it. Phase K does that.
- **Multi-asset support.** Lockport only per parent plan §5 D4.

---

## §8. How this informs Notebook 2

After Notebook 1 runs successfully, we should have:

1. **A working data-spine load pattern** — Notebook 2 can reuse the same conventions
2. **Cleanly-loaded asset + paths + tech_defaults** — Notebook 2 inherits these data structures, not the loading logic
3. **A clear sense of which assumption-status codes are most prevalent** — informs what caveats to display when Notebook 2 computes spark spread
4. **An identified day-to-day timestamp convention** — Notebook 2 will pick "one representative day" using this convention
5. **The Lockport ↔ tech-class join verified** — Notebook 2 uses this to access startup costs, VOM, etc. without re-deriving

Notebook 2's plan (`02_one_day_dispatch.md`) gets written based on:
- What Stage 1 findings revealed
- Which day to pick (high-output summer day? winter cold snap? shoulder month?)
- How to handle the cogen DHTS constraint (must-run threshold from `operating_profile.yaml`)
- How to layer RGGI cost (single allowance price assumption vs. time series)

These decisions are deferred — they'll be obvious (or at least debatable) after Notebook 1 surfaces the data.

---

## §9. Risks / things that could go wrong

| Risk | Mitigation |
|---|---|
| YAML schema turns out to be too verbose for practical use | Stage 1 findings cell explicitly calls this out; revise parent plan §6 before Notebook 2 |
| Time-series timestamps don't align cleanly between LMP / weather / gas | §3.F cross-checks surface this; fix at the data-copy step (Phase E) before continuing |
| Assumption-status codes accumulate variants beyond the 9 in the taxonomy | §3.G surfaces every distinct code seen; update taxonomy if needed |
| Tech-class lookup join returns wrong row count for Lockport | §3.H halts the notebook; debug join key derivation logic |
| File sizes turn out larger than expected (weather is 15 MB, but maybe parquet inflates) | §3.B size check — if > 100 MB total, reconsider copy-vs-symlink for v1 (revisit parent §5 D3) |

---

## §10. Output artifacts (what the notebook produces)

- The notebook itself (`notebooks/01_data_spine_load_validate.ipynb`)
- A `notebooks/outputs/01_validation_report.json` (optional) — machine-readable summary of validation results for use in tests later
- Stage 1 findings + Decision log updates to this plan doc — if any conventions change

No data is written by this notebook; it's read-only.

---

## §11. Reference

- Parent plan: [`../../consolidation_plan.md`](../../consolidation_plan.md) §8 Phase G
- Notebook-track overview: [`README.md`](./README.md)
- Assumption status taxonomy: parent plan §6
- MOR notebook (reference pattern): `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb`
- Notebook methodology: `~/code/personal/diligence-extractor/docs/notebook_methodology.md`
- Step 1 plan (path schema): [`../../step_1_climate_price_scenario_plan.md`](../../step_1_climate_price_scenario_plan.md) §"Scenario Package Schema"
