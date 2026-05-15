# CLAUDE.md — gt_models

Gas turbine digital-twin modeling repo. v1 models **Lockport Energy Associates** (NYISO Zone A, 1992 vintage, 3-on-1 CCGT cogeneration, 221 MW) across 9 years (2017–2025). Three dispatch policy modes (A/B/C), seven LTSA cost streams, full MOR-driven backtest. Live at GitHub: `aamani-ai/GT_Modeling`.

**This is the MODELING repo** — not the data platform (`renewablesinfo_org`), not the data-room extractor (`diligence-extractor`), not the price forecaster (`model-gpr`). It consumes from the others and produces dispatch / wear / LTSA / Net P&L analytics for a single asset at a time.

**Status**: v1 substantively complete. Notebooks run end-to-end, 98/98 tests pass, methodology + guides documented. v2 priorities documented in [`docs/methodology/gaps_and_priorities.md`](docs/methodology/gaps_and_priorities.md) §6.

## Quick commands

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install pandas numpy matplotlib pyyaml jupyter jupytext xlrd pyarrow nbconvert pytest

# Tests
pytest tests/                                       # 98 tests, should all pass

# Run a notebook (as script, fast)
cd notebooks && MPLBACKEND=Agg python3 04_full_path_mode_comparison.py

# Convert .py → .ipynb + execute with embedded plots
cd notebooks && jupytext --to ipynb 04_full_path_mode_comparison.py
cd notebooks && jupyter nbconvert --to notebook --execute --inplace 04_full_path_mode_comparison.ipynb

# Inspect latest model_card
cat data/outputs/lockport/runs/notebook4_*/model_card.md | tail -1   # last run
```

## Architecture (the 3-layer engine)

```
ENGINEERING LAYER
  - 9-field plant state vector (EOH, hr_recov, fouling, dc, df, tbc_*, hrsg_cycles, rotor_life)
  - State evolves daily based on yesterday's dispatch
  - Forced-outage probability derives from state
              ↓
DISPATCH LAYER
  - Per-hour mode pick (3xCC / 2xCC / 1xCC / steam-only / offline)
  - Twin dispatch: clean vs degraded — loss-attribution
  - Mode A/B/C policy adds wear-penalty hurdle on start decisions
              ↓
LTSA / CONTRACTS LAYER
  - 7 cost streams accrue (fixed fee, EOH reserve, CI/MI events,
    start overage, availability penalty, HR penalty) + forced-outage cost
  - Inspection events trigger on EOH threshold + calendar
  - Forced-outage events sampled vs P_forced
              ↓
        Daily P&L → cumulative model_card
```

Full deep dive: [`docs/methodology/architecture.md`](docs/methodology/architecture.md) §5.
Two-axes mode disambiguation (operating mode vs policy mode): [`docs/methodology/dispatch_mechanics.md`](docs/methodology/dispatch_mechanics.md) §1.

## Notebook sequence (Phases G–J)

```
notebooks/01_data_spine_load_validate.{py,ipynb}     ← Phase G: load + validate + status-track
notebooks/02_one_day_dispatch.{py,ipynb}             ← Phase H: single-day dispatch decision
notebooks/03_daily_loop_feedback.{py,ipynb}          ← Phase I: 30-day state evolution
notebooks/04_full_path_mode_comparison.{py,ipynb}    ← Phase J: 9-yr × 3-mode + model_card
notebooks/05_model_vs_actual.{py,ipynb}              ← MOR backtest deep-dive (13 plots)
```

**Convention**: `.py` (jupytext percent format) is canonical. `.ipynb` is regenerated for embedded plot outputs.

## Asset profile structure (the data foundation)

Every modeled asset lives at `data/assets/<asset>/` with 5 YAML dimensions:

| YAML | Captures | Status maturity (Lockport) |
|---|---|---|
| `identity.yaml` | Plant ID, location, operator, online date, ISO node | High — federal data |
| `engineering.yaml` | Capacities, derate, min-load, boiler, dual-fuel, etc. | High — EIA-860 enriched |
| `operating_profile.yaml` | Heat rate by mode, cold-start gas, DHTS, steam-only empirics | High — MOR-derived |
| `market_context.yaml` | ISO zone, eGRID, RGGI, gas hub treatment | High |
| `ltsa_terms.yaml` | OEM contract terms (placeholder by default) | **LOW — all placeholder** |

Plus `caveats.md` (operational notes) + `provenance.md` (source lineage).

Time-series spine at `data/paths/<asset>/`: LMP, gas, weather, MOR daily.

Full dimensional framework: [`docs/guides/asset_profile_dimensions.md`](docs/guides/asset_profile_dimensions.md).

## Documentation map (read in this order for new sessions)

| Doc | What | Length |
|---|---|---|
| `README.md` | Repo entry point — quick-start + reading order | ~280 lines |
| `docs/methodology/pnl_ledger.md` | The economic ledger — every revenue + cost component | ~275 |
| `docs/methodology/architecture.md` | How v1 works (engine, daily loop, state vector) | ~880 |
| `docs/methodology/dispatch_mechanics.md` | Operating mode × policy mode deep dive | ~450 |
| `docs/methodology/gaps_and_priorities.md` | What's missing + ranked priority list with $ magnitudes | ~360 |
| `docs/methodology/glossary.md` | Term definitions | ~275 |
| `docs/methodology/extra/backtest_findings.md` | Model-vs-MOR analysis + known divergences | ~350 |
| `docs/guides/asset_profile_dimensions.md` | The 5-dimension framework + plant archetypes | ~585 |
| `docs/guides/pulling_specs_from_powerplantsinfo.md` | How to lift specs from renewablesinfo_org pipeline | ~345 |
| `docs/guides/future_dimensions.md` | Stubs for anticipated YAMLs (outage / offtake / fixed_opex) | ~465 |
| `docs/decisions/` | ADRs — substantive decisions with reasoning trail | 2 ADRs |
| `docs/assumptions/status_taxonomy.md` | The 9-code grammar for YAML leaf values | ~100 |
| `docs/plans/consolidation_plan.md` | Full build plan + status log (Phases A–L) | ~870 |

## Key conventions

### Status taxonomy (every YAML leaf)
Every leaf value carries `{value, status, source}` with one of 9 status codes:
- `real_observed` — measured directly (MOR, SCADA, EIA-860)
- `real_reported` — from regulatory filings / contracts
- `real_computed` — derived from real values via formula
- `assumed_techclass` — class-level default
- `assumed_vendor` — OEM-published spec
- `assumed_industry` — industry rule-of-thumb
- `assumed_derived` — assumption derived from another assumption
- `placeholder` — typed value awaiting real source (most LTSA values)
- `not_applicable` — doesn't apply

Lockport's distribution: 80% real_* / 17.5% placeholder / 2% assumed_industry.

### ADRs (Architectural Decision Records)
Substantive decisions live in `docs/decisions/NNN-topic.md`. Current ADRs:
- **001** — Gas hub treatment: Henry Hub for v1, Algonquin basis deferred
- **002** — Lockport-specific vs generic F-class calibration (the 3-bucket inventory)

When to write a new ADR: when there's a real choice with ≥2 viable alternatives + downstream consequences.

### Plant archetypes (proposed framework)
Single most useful prior: peaker / mid_merit / baseload / cogen / qf_purpa / rmr / battery / hybrid. Drives revenue mix expectations, LTSA structure, wear regime, valuation questions. Lockport = **cogen + qf_purpa (TBD) + low_cf**. Framework documented in [`docs/guides/asset_profile_dimensions.md`](docs/guides/asset_profile_dimensions.md) §13; not yet implemented in YAML.

## Don'ts

- **Don't push without explicit cd + pwd verification.** Lesson from 2026-05-15: assuming the Bash tool's cwd persists caused a wrong-repo push to GT_Modeling. ALWAYS do `cd /absolute/path && pwd && git ...` in the same Bash call.
- **Don't commit `data/outputs/`** — regenerable; tracked in `.gitignore`. Reproducible from `run_config.yaml`.
- **Don't change `git config user.name/email`** unless explicitly asked.
- **Don't try to "fix" findings before team weighs in.** Documented limitations (steam-only trigger conservative, Mode A/B/C late divergence, generic 2017 starting state) are v2 work — wait for direction.
- **Don't run notebooks 1-4 as a single batch without N1 passing first** — N1 validates the data spine; later notebooks assume it succeeds.

## Cross-repo references (symlinks, gitignored)

```
gt_models/.model-gpr           → /Users/divy/code/work/infrasure_git_codes/model-gpr
gt_models/.diligence-extractor → /Users/divy/code/personal/diligence-extractor
gt_models/.renewablesinfo      → /Users/divy/code/personal/renewablesinfo
gt_models/.renewablesinfo_org  → /Users/divy/code/personal/renewablesinfo_org
```

Use these for cross-repo navigation. They don't get committed (in `.gitignore`).

Specifically:
- **`.renewablesinfo_org/`** is the data platform. Pull from `data/dimensions/engineering/thermal_enriched.parquet` to populate `data/assets/<asset>/engineering.yaml`. See [`docs/guides/pulling_specs_from_powerplantsinfo.md`](docs/guides/pulling_specs_from_powerplantsinfo.md).
- **`.diligence-extractor/`** has the raw data-room files. MOR workbooks at `data/<asset>/3.0 <Asset>/3.4 O&M Reports/3.4.20 Monthly Operating Reports/`. Heat-rate-analysis notebook at `notebooks/daily_heat_rate_analysis.ipynb` is the canonical MOR extraction pattern.
- **`.model-gpr/`** is for price forecasting (Phase L Monte Carlo will pull from this).
- **`.renewablesinfo/`** is the lab repo for integrations.

## GitHub setup (multi-account)

This repo lives at `https://github.com/aamani-ai/GT_Modeling` (work organization). SSH push uses the `github.com-work` alias which authenticates as **D-ivyy** (work account).

```
git@github.com-work:aamani-ai/GT_Modeling.git    ← THIS repo (work account D-ivyy)
git@github.com-personal:Divi-patel/...           ← personal repos (Divi-patel)
git@github.com-divy:...                          ← third account (D-ivy)
```

Default `git@github.com:...` resolves to Divi-patel (personal). **Do not use default for work-account repos** — confirmed via `ssh -T git@github.com-X 2>&1 | head -1`.

Local commits are still attributed to `Divi-patel / divy2023@gmail.com` (your personal identity); push goes through D-ivyy. If you want commits also attributed to work, you'd need to change `git config user.name/email` locally — not done automatically.

## Current v1 headline numbers

From the latest run (Lockport, 2017–2025, seed=42, post-steam-only-mode addition):

| Mode | Spark margin (9-yr) | LTSA owner | **Net P&L (9-yr)** |
|---|---:|---:|---:|
| A | $36.08M | $203.24M | **−$167.16M** |
| B | $33.15M | $175.62M | **−$142.47M** |
| C | $33.11M | $175.60M | **−$142.50M** |

**Over-commit vs MOR**: 2.07× (model 1,945 GWh vs MOR 939 GWh over 2021–2025).

⚠️ **These numbers are NOT representative of Lockport's real economics**. LTSA values are Athens placeholders; revenue side is electricity-only (no steam, no capacity, no ancillary). Survivorship-calibrated real Net P&L is plausibly **+$2 to +$4M/yr** after closing input gaps. See `pnl_ledger.md` §4.

## Top-5 v2 priorities (from `gaps_and_priorities.md` §6)

1. **Data-room LTSA extraction** — replace 47 placeholder values (+$5–9M/yr Net)
2. **Add NYISO ICAP revenue** — currently $0; should add ~$5–9M/yr
3. **Add cogen steam revenue** — currently $0; should add ~$3–7M/yr
4. **Per-generator state** — unlocks 2×CC dispatch (0% in model vs 14% MOR)
5. **Less conservative steam-only trigger** — currently 18% recall of real days

## Key file-path patterns

```
data/assets/<asset>/           ← per-asset YAML profile (5 dimensions + caveats/provenance)
data/paths/<asset>/            ← per-asset time series (LMP, gas, weather, MOR daily)
data/tech_class_defaults/      ← cross-asset reference
data/outputs/<asset>/runs/notebook4_<timestamp>/   ← simulation outputs (gitignored)

docs/methodology/{pnl_ledger,architecture,gaps_and_priorities,dispatch_mechanics,glossary}.md
docs/methodology/extra/        ← findings docs that don't belong in main flow
docs/methodology/assets/       ← plot assets used by methodology docs
docs/guides/{asset_profile_dimensions,pulling_specs_from_powerplantsinfo,future_dimensions}.md
docs/decisions/NNN-topic.md   ← ADRs
docs/assumptions/{status_taxonomy,placeholder_caveats}.md
docs/plans/consolidation_plan.md   ← build plan + §13 status log
docs/extra/                    ← prototype reference (frozen architectural source)

notebooks/0N_topic.{py,ipynb}  ← jupytext pairs
notebooks/scratch/             ← ad-hoc analysis scripts
tests/test_*.py                ← 98 tests
```

## What v1 produces (every run)

`data/outputs/<asset>/runs/notebook4_<timestamp>/`:
- `model_card.md` — headline summary doc
- `run_config.yaml` — reproducibility config
- `daily_summary_mode_{a,b,c}.parquet` — full daily record per mode
- `state_trajectory_mode_{a,b,c}.parquet` — engineering state columns
- `ltsa_streams_mode_{a,b,c}.parquet` — 8 cumulative cost streams
- `inspection_events.parquet`, `forced_outage_events.parquet`

## When to ask vs proceed

- **Substantive choice with downstream consequences** → propose + wait (likely an ADR moment)
- **Data discovery/audit** → proceed; report findings; don't change YAMLs without confirmation
- **Code refinements that change model output** → propose + wait
- **Doc edits / cross-link audits / typo fixes** → proceed
- **New asset onboarding** → wait until user confirms which asset + provides data-room access
- **Anything touching `git push`, `git remote`, or anything that affects renewablesinfo_org or other repos** → explicitly cd + pwd + verify remote URL before action
