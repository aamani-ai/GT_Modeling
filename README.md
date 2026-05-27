# gt_models — Gas Turbine Digital Twin (v1)

> **A deterministic single-asset digital-twin model for natural gas combined-cycle plants.** v1 models Lockport Energy Associates (NYISO Zone A, 1992 vintage, 3-on-1 CCGT cogeneration, 221 MW) across 9 years (2017–2025) with three dispatch policy modes, seven LTSA cost streams, and a full MOR-driven backtest.
>
> **Status**: v1 substantively complete. Notebooks run end-to-end, methodology + guides documented, 98/98 tests pass. Sharing with the team for review + direction-setting on v2.

---

## What this is — and what it isn't

**What v1 IS**:
- A **deterministic backtest** with perfect-foresight dispatch over 9 years (2017–2025)
- A **structural validation** that the engineering ↔ dispatch ↔ LTSA feedback architecture is internally consistent
- A **proof-of-concept** that asset-specific MOR data can be lifted, modeled, and backtested
- A **framework** for onboarding more assets — asset profile dimensions, status taxonomy, modeling spine all defined

**What v1 is NOT**:
- A financial projection or forecast
- A Monte Carlo (Phase L work)
- A multi-asset portfolio model (v2+)
- Production-grade (no `src/` package yet; everything lives in notebooks)

The headline Net P&L numbers in this model are **structurally meaningful but absolutely biased**: LTSA values are all Athens-prototype placeholders (pending data-room extraction), revenue side is electricity-only (steam + capacity + ancillary not modeled), and dispatch over-commits 2.07× vs MOR-observed reality. **These are all documented and intentional v1 limitations.**

---

## Quick start (10 minutes)

```bash
# Clone
git clone <this-repo>
cd gt_models

# Set up env (Python 3.9+)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install pandas numpy matplotlib pyyaml jupyter jupytext xlrd pyarrow nbconvert

# Run tests
pytest tests/                              # → 98 passed

# Open the capstone notebook
jupyter notebook notebooks/04_full_path_mode_comparison.ipynb

# Or open the backtest deep-dive
jupyter notebook notebooks/05_model_vs_actual.ipynb
```

After running notebooks 1–4 in order, the **headline output** is `data/outputs/lockport/runs/notebook4_<timestamp>/model_card.md`. That's the single-page summary of the run.

---

## Reading order

### 10-minute orientation
1. **This README**
2. **[`docs/methodology/pnl_ledger.md`](docs/methodology/pnl_ledger.md)** — the economic view: every revenue + cost component, what v1 models, what it ignores
3. **Latest `model_card.md`** in `data/outputs/lockport/runs/notebook4_<timestamp>/`

### 1-hour deep dive
Above plus:
4. **[`notebooks/05_model_vs_actual.ipynb`](notebooks/05_model_vs_actual.ipynb)** — model vs MOR backtest with 13 plots
5. **[`docs/methodology/architecture.md`](docs/methodology/architecture.md)** — how the model works (engine, daily loop, state vector)
   - **[`docs/methodology/flowcharts.md`](docs/methodology/flowcharts.md)** — the visual companion: end-to-end + daily loop + wear/failure + creep-fatigue (Mermaid). Start here if you think in pictures.
6. **[`docs/methodology/extra/backtest_findings.md`](docs/methodology/extra/backtest_findings.md)** — honest limitations + the 7 documented findings
7. **[`docs/methodology/gaps_and_priorities.md`](docs/methodology/gaps_and_priorities.md)** §6 — ranked v2 priority list with dollar magnitudes

### Full understanding (browse as needed)
- [`docs/methodology/`](docs/methodology/) — methodology docs incl. [`flowcharts.md`](docs/methodology/flowcharts.md) (visual), `architecture.md`, `pnl_ledger.md`, `glossary.md` + `extra/`
- [`docs/implementation/`](docs/implementation/) — **how the `src/` code works** (gt_engine + forward: overview · architecture · function reference · IO schemas · worked example)
- [`docs/guides/`](docs/guides/) — how-to guides
- [`docs/decisions/`](docs/decisions/) — ADRs
- [`docs/assumptions/`](docs/assumptions/) — status code taxonomy
- [`notebooks/01–05`](notebooks/) — end-to-end historical build sequence
- **Forward engine (Stream A / Phase 6, v1)**: [`src/gt_engine/`](src/gt_engine/) (importable engine) + [`src/forward/`](src/forward/) (select → build → run) + [`notebooks/06_forward_scenarios.py`](notebooks/06_forward_scenarios.py) — SEAS5-conditioned P10/P50/P90 on RT analog windows. Plan: [`docs/plans/forward_engine_plan.md`](docs/plans/forward_engine_plan.md)
- [`docs/plans/consolidation_plan.md`](docs/plans/consolidation_plan.md) — build history + status log

---

## Repo structure

```
gt_models/
├── notebooks/                         ← 5 jupytext .py/.ipynb pairs
│   ├── 01_data_spine_load_validate    ← Phase G: data spine + assumption tracking
│   ├── 02_one_day_dispatch            ← Phase H: single-day dispatch
│   ├── 03_daily_loop_feedback         ← Phase I: state evolution + feedback
│   ├── 04_full_path_mode_comparison   ← Phase J: 9-yr capstone + model_card output
│   └── 05_model_vs_actual             ← MOR backtest deep-dive (13 plots)
│
├── data/
│   ├── assets/                        ← per-asset profiles (YAML)
│   │   └── lockport/                  ← 7 YAMLs + caveats + provenance
│   ├── paths/                         ← per-asset time-series (parquet)
│   │   └── lockport/                  ← LMP, gas, weather, MOR daily
│   ├── tech_class_defaults/           ← cross-asset reference table
│   └── outputs/                       ← simulation outputs (gitignored)
│
├── docs/
│   ├── methodology/                   ← architecture + analysis
│   │   ├── pnl_ledger.md              ← entry: economic ledger
│   │   ├── architecture.md            ← how v1 works
│   │   ├── dispatch_mechanics.md      ← operating mode × policy mode
│   │   ├── gaps_and_priorities.md     ← what's missing + priority order
│   │   ├── glossary.md                ← term definitions
│   │   └── extra/
│   │       └── backtest_findings.md   ← model vs MOR analysis
│   ├── guides/                        ← how-to docs
│   │   ├── asset_profile_dimensions.md      ← the dimensional framework
│   │   ├── pulling_specs_from_powerplantsinfo.md  ← lift from platform pipeline
│   │   └── future_dimensions.md       ← anticipated YAMLs (outage/offtake/fixed_opex)
│   ├── decisions/                     ← ADRs (substantive decisions)
│   ├── assumptions/                   ← status code grammar
│   └── plans/                         ← consolidation plan + per-notebook plans
│
├── src/                               ← (empty in v1; Phase K refactor target)
├── tests/                             ← 98 tests (Lockport profile + tech defaults)
└── README.md
```

---

## What v1 produces

Running notebook 4 produces a **run bundle** at `data/outputs/lockport/runs/notebook4_<timestamp>/`:

```
notebook4_<timestamp>/
├── model_card.md                       ← the headline summary
├── run_config.yaml                     ← reproducibility config
├── daily_summary_mode_{a,b,c}.parquet  ← full daily record per mode (3,287 rows × ~30 cols)
├── state_trajectory_mode_{a,b,c}.parquet  ← engineering state columns
├── ltsa_streams_mode_{a,b,c}.parquet   ← 8 cumulative cost streams
├── inspection_events.parquet           ← CI / MI events across all modes
└── forced_outage_events.parquet        ← forced events across all modes
```

The `model_card.md` contains:
- Run metadata + data vintages
- Assumption-status distribution (currently 80% real / 17.5% placeholder)
- Mode comparison: spark / LTSA / Net P&L per policy mode (A/B/C)
- LTSA stream breakdown by cost category
- MOR backtest table (model vs actual 2024 generation, mode mix, cold-start frequency)
- Caveats + known limitations

---

## Current v1 headline numbers

From the latest run (Lockport, 2017–2025, seed=42):

| Metric | Mode A | Mode B | Mode C |
|---|---:|---:|---:|
| Spark margin (9-yr) | $36.08M | $33.15M | $33.11M |
| LTSA owner-uncovered | $203.24M | $175.62M | $175.60M |
| **Net P&L (9-yr)** | **−$167.16M** | **−$142.47M** | **−$142.50M** |
| Annual avg Net P&L | −$18.57M/yr | −$15.83M/yr | −$15.83M/yr |
| Fired hours | 13,879 | 13,471 | 13,446 |
| Inspections | 1 (MI) | 0 | 0 |
| Forced outage events | 35 | 36 | 36 |

**Over-commit vs MOR**: 2.07× (modeled 1,945 GWh vs MOR-observed 939 GWh over 2021–2025).

**Important**: these numbers are NOT representative of Lockport's real economics. The Net P&L is artificially negative because LTSA values are placeholder Athens defaults (likely 2× too high) and the revenue side excludes steam + capacity + ancillary. See [`docs/methodology/pnl_ledger.md §4`](docs/methodology/pnl_ledger.md) for the survivorship-calibrated real-economics reconciliation: real Lockport Net P&L is plausibly +$2 to +$4M/yr after closing input gaps.

---

## Status: what's done, what's pending

### ✅ v1 complete

- 5 notebooks (N1–N5), all with embedded plots
- 5 methodology docs + 1 in `extra/` (1,700+ lines of structured analysis)
- 3 how-to guides (1,400+ lines)
- 2 ADRs (gas hub treatment, Lockport-specific calibration)
- Lockport asset profile (7 YAMLs + caveats + provenance)
- Time-series spine (LMP, gas, weather, MOR daily — 1,826 days)
- Tech-class defaults (cross-asset reference)
- 98/98 tests pass

### 🚧 v2 priorities (documented in `gaps_and_priorities.md §6`)

In rough order of leverage × effort:

1. **Data-room LTSA extraction** — replace 47 placeholder values with real contract data (+$5–9M/yr Net P&L improvement)
2. **Add NYISO ICAP revenue layer** — currently 0; should add ~$5–9M/yr (R2 in p&l_ledger)
3. **Add cogen steam revenue** — currently 0; should add ~$3–7M/yr (R3)
4. **Per-generator state** — unlocks 2×CC dispatch (currently 0% in model; ~14% in MOR)
5. **Less conservative steam-only trigger** — currently catches 18% of MOR's days; could lift to 50%+
6. **Phase L Monte Carlo** — quantify uncertainty bands; sweep Bucket B Athens constants

### 🚧 Structural v1 simplifications (documented in `backtest_findings.md §3.7`)

- Perfect foresight (model knows future LMP/gas/weather — see notebook 5 §M.5)
- Generic starting state at 2017 (state.eoh = 24,000 default; doesn't reflect Lockport's 1992-2017 history)
- No historical inspections modeled (e.g., Fall 2018 HGP outage on Unit 1 known from data room)
- Mode A/B/C framework's design assumptions don't fit low-CF assets

These are all intentional v1 simplifications — Phase L Monte Carlo + per-generator state + state-initialization fixes are how they get addressed.

---

## How v1 is calibrated for sharing

Three explicit framing choices to be aware of:

1. **Plant profile is upstream of everything**. The YAMLs in `data/assets/lockport/` are the foundation. Most downstream accuracy improvements come from improving the profile (real LTSA, steam contract, etc.), not from refining the dispatch code. See [`docs/guides/asset_profile_dimensions.md`](docs/guides/asset_profile_dimensions.md) §1 for the principle.

2. **Annual is the unit, not 9-year totals**. Every dollar magnitude in the docs is reported per year first, with cumulative-over-9-years as a derivation. See [`docs/methodology/gaps_and_priorities.md`](docs/methodology/gaps_and_priorities.md) §7 for why.

3. **Survivorship calibration is a sanity check**. Lockport has been operating since 1992. Any v1 conclusion that puts the asset materially negative on real cash flow is failing a basic plausibility test. See [`docs/methodology/pnl_ledger.md`](docs/methodology/pnl_ledger.md) §4.1.

---

## Feedback the team can help with

This is an invitation to extend, not just review. Specific questions:

1. **Which v2 priorities to tackle first?** The ranked list in `gaps_and_priorities.md §6` is my best guess; team input would re-rank if you have additional context (data-room availability, deal urgency, etc.).

2. **Does the dimensional framework work for multi-asset scaling?** The core 5-dimension structure (`identity` / `engineering` / `operating_profile` / `market_context` / `ltsa_terms`) plus the 2 regime-decomposition dimensions (`capability_envelope` / `realized_operating_profile`, added 2026-05 per ADR-003) is the proposed pattern for asset onboarding. Want to validate before applying to a second asset.

3. **Are the asset archetypes useful as a prior?** See `asset_profile_dimensions.md` §13 — proposed taxonomy (peaker / mid-merit / baseload / cogen / qf_purpa / rmr / battery / hybrid) with Lockport as "cogen + qf_purpa (TBD) + low_cf". Not implemented in YAML yet.

4. **What's the data-room extraction priority order?** From `pnl_ledger.md` and `gaps_and_priorities.md`, the highest-value extractions are LTSA fixed fee + steam tariff + ICAP terms. Are these accessible? Pending? Other priorities?

5. **Should we backport bug fixes to N3?** N3 has an aging-formula bug we fixed in N4 (`year_frac = day_idx / 365.0` should be `min(years_elapsed / 10, 1.0)`). N3's short window doesn't surface the issue, but it's technically wrong. Worth backporting or leave?

---

## Build history

The v1 build is documented in [`docs/plans/consolidation_plan.md`](docs/plans/consolidation_plan.md). Phases A–J complete; phases K (graduate notebooks to `src/`) and L (Monte Carlo) are scoped but not built. The §13 status log has detailed per-phase entries with findings.

Key milestone dates:
- Phase A–F (data spine + asset profile) — 2026-05-14
- Phase G–I (notebooks 1–3) — 2026-05-14
- Phase J (notebook 4 capstone + steam-only mode) — 2026-05-15
- Notebook 5 (MOR backtest deep-dive) — 2026-05-15

---

## Conventions to know before contributing

- **Notebooks**: `.py` (jupytext percent format) is canonical; `.ipynb` is regenerated for embedded plots
- **Status taxonomy**: every YAML leaf carries `{value, status, source}` with one of 9 status codes (see `docs/assumptions/status_taxonomy.md`)
- **Decisions**: substantive choices get an ADR in `docs/decisions/`
- **Caveats**: non-obvious conventions baked into the data go in `data/assets/<asset>/caveats.md`
- **Run outputs**: `data/outputs/` is gitignored (regenerable; reproducible from `run_config.yaml`)

---

## Questions, feedback, next steps

Open an issue, ping the model owner, or send notes directly. The v1 framework is meant to be evolved with team input — not preserved as-is.

**Next step**: team review → prioritization conversation on v2 → first v2 work (likely data-room LTSA extraction).
