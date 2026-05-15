# Task Context — gt_models v1 Lockport build + shared with team

> **Folder**: `2026-05-15__gt-models__v1-lockport-shipped`
> **Date completed**: 2026-05-15
> **Repo**: `gt_models` → pushed to https://github.com/aamani-ai/GT_Modeling
> **Duration**: Multi-day session spanning 2026-05-14 → 2026-05-15

## §1. Objective

Build v1 of a gas-turbine digital-twin model for Lockport Energy Associates (NYISO Zone A, 1992 vintage, 3-on-1 CCGT cogeneration, 221 MW), validate against MOR-observed reality, document architecture/methodology/limitations honestly, and ship to a fresh remote repo (`aamani-ai/GT_Modeling`) for team review and v2 direction-setting.

## §2. Background

Initial query was a tactical question about gas/non-renewable data sources in the `renewablesinfo_org` platform that could feed dispatch modeling. That triggered cascading discovery work that grew into a full v1 modeling repo:

- The Athens-prototype digital-twin framework (3-layer engineering↔dispatch↔LTSA loop) existed as reference but had never been applied to a real asset with real MOR data
- Lockport was selected as the first asset (single-asset v1 per consolidation_plan §5 D4)
- The diligence-extractor repo had 5 years (2021-2025) of daily MOR data already extracted via `daily_heat_rate_analysis.ipynb`
- The renewablesinfo_org platform's `data/dimensions/engineering/thermal_enriched.parquet` had pre-enriched EIA-860 data (65 columns including `boiler_type`, `has_duct_burners`, `min_load_mw`, etc.)
- No coherent v1 model existed; this session built one end-to-end

## §3. Problems encountered

### Modeling / analytical
- **Heat rate by mode** required MOR-derived volume-weighted calculation across 5 years, not generic prototype defaults
- **Aging-formula bug** in N3: `year_frac = day_idx / 365.0` was interpreted as "years elapsed" but the formula `age_mult = 1 + year_frac × (MAX-1)` expects fraction-of-10-yr-aging-window. Invisible at N3's 30-day window; compounded to 5.5× by year 9 of N4 (should cap at 1.5×). Surfaced when forced-outage count was 86-87 per mode vs expected ~35-50.
- **Steam-only mode discovery**: MOR data revealed 460 days (25.2% of 2021-2025) with 0 MWh + non-zero gas + non-zero DHTS delivery. Original architecture doc had claimed Lockport can't produce steam without electricity — this was wrong. EIA-860 confirmed: GEN4 has `Duct Burners=Y`, CTs have `Can Bypass HRSG=Y`, boiler ID 4 type = "Db" (Duct Burner). The HRSG can fire duct burners directly.
- **Athens-prototype LTSA placeholders** made Net P&L artificially negative (−$203M/9yr Mode A before steam-only addition; −$167M after). Real Lockport survives since 1992 → not consistent with sustained-negative cash flow.
- **Survivorship-bias sanity check failed** initially: my reconciliation put Real Economic Net P&L at −$15 to $0M/yr. User correctly pushed back — plant operating since 1992 must be at least breakeven. Recalibrated to +$0 to +$8M/yr (central +$2-4M/yr).
- **Mode A/B/C bracketing fails on TWO axes for Lockport**: (a) band is collapsed for 4 of 5 years because wear-penalty mechanic only activates when EOH headroom < 4,000 (happens at end of 9-yr window at Lockport's CF); (b) MOR is BELOW the band even in the year it has width — absolute bias dwarfs policy choice.
- **Starting-state assumption** wrong: model initializes with state.eoh = 24,000 at 2017-01-01 (generic prototype default). Lockport operated 25 years prior; real 2017 state is asset-specific. Known 2018 HGP outage on Unit 1 (data room: `3.4.2 Lockport Unit 1 (295770) Mod HGP Final Report - Fall 2018.pdf`) not modeled as state-reset event.

### Process / infrastructure
- **Wrong-repo push** (2026-05-15): I assumed Bash cwd persisted across calls. It did for explicit-cd commands but reverted to Primary working directory (`renewablesinfo_org`) for subsequent commands. Result: `git push` from `renewablesinfo_org`'s main branch went to `aamani-ai/GT_Modeling-` (the original GT_Modeling- remote with trailing dash). User deleted the remote; renewablesinfo_org's origin URL had to be restored.
- **Multi-account SSH** required: default `git@github.com` resolves to Divi-patel (personal); aamani-ai org requires `git@github.com-work` alias (D-ivyy account). Verified via `ssh -T git@github.com-X 2>&1 | head -1` before any push.
- **EIA-923 data lag**: 2024 data was largely empty (Feb-Dec showed 0 generation). Confirmed via cross-validation that EIA-923 has ~6-12 month federal reporting lag; only reliable for historical years (2021-2022 within ±10% of MOR).
- **Conservative steam-only trigger**: initial implementation uses peak LMP × 3xCC HR < break-even as the trigger — only catches 18% of MOR's real steam-only days (95% precision but low recall).

## §4. What we fixed / built

### Data foundation (Phases A–F)
1. Built Lockport asset profile: 5 YAMLs in `data/assets/lockport/` with proper status taxonomy
2. Lifted EIA-860-enriched fields from renewablesinfo_org pipeline (3 boiler fields newly added in this session: `boiler_id`, `boiler_type="Db"`, `boiler_count`)
3. Time-series spine: `data/paths/lockport/{lmp_da_hourly, gas_price_history, weather_hourly}.parquet`
4. Extracted MOR daily (1,826 rows, 2021-2025) → `data/paths/lockport/mor_daily.parquet` using diligence-extractor pattern
5. Added `steam_only_mode` section in `operating_profile.yaml` with MOR-derived empirics (median 871 MMBtu/day gas, 589 MMBtu/day DHTS, 25.2% of days)
6. Tech-class defaults parquet copied from renewablesinfo lab

### Notebooks (Phases G–J + supplement)
1. **N1** (`01_data_spine_load_validate`) — loads + validates spine, 266 leaves aggregated, 80.1% real_*
2. **N2** (`02_one_day_dispatch`) — single-day dispatch, day 2023-07-12 picked algorithmically
3. **N3** (`03_daily_loop_feedback`) — 30-day window state evolution, 4 plots
4. **N4** (`04_full_path_mode_comparison`) — 9-yr × 3-mode capstone + model_card output, 6 plots. Added: steam-only branch in must-run logic; min-load constants wired (no-op in v1 partial-dispatch); aging-formula fix.
5. **N5** (`05_model_vs_actual`) — MOR backtest deep-dive with 13 plots. Themes: volume / mode-mix / mechanics. Includes perfect-foresight diagnostic (§M.5), can/cannot-conclude boundaries (§M.6), error decomposition into modeling/input/structural (§O.1/O.2/O.3), and the bracketing view (§E.5).

### Methodology folder (5 + extra/)
1. `pnl_ledger.md` (~275 lines) — economic ledger; entry point. Three-tier Net P&L reconciliation (v1 / improved / real economic) with survivorship calibration.
2. `architecture.md` (~880 lines) — how v1 works; 11 sections including engine, daily loop, headline numbers, what's missing.
3. `dispatch_mechanics.md` (~450 lines) — operating mode × policy mode deep dive. Two-axes disambiguation, why 2×CC never wins, cogen must-run physics.
4. `gaps_and_priorities.md` (~360 lines) — ranked v2 priority list with dollar magnitudes. Three-leg framing (LTSA / revenue / dispatch realism).
5. `glossary.md` (~275 lines) — 8-section term reference.
6. `extra/backtest_findings.md` (~350 lines) — model-vs-MOR analysis. 7 findings including the bracketing collapse + starting-state issue (§3.7).
7. `assets/modeled_vs_mor_vs_eia923.png` — 4-panel comparison chart.

### Guides folder
1. `pulling_specs_from_powerplantsinfo.md` (~345 lines) — step-by-step lift-from-platform workflow with 3-path steam-only mechanism check.
2. `asset_profile_dimensions.md` (~585 lines) — dimensional framework + plant archetypes (§13 with proposed taxonomy of 8 archetypes).
3. `future_dimensions.md` (~465 lines) — design specs for 3 anticipated YAMLs (`outage_history`, `offtake_contracts`, `fixed_opex`).

### ADRs
1. **001-gas-hub-treatment-v1.md** — Henry Hub only for v1, Algonquin basis deferred (sparse history only 2014-2017)
2. **002-lockport-specific-vs-generic-calibration.md** — Three-bucket inventory (Bucket A Lockport-specific / B generic F-class / C placeholder pending data room). Correction 1: cold-start warming gas (2,537 MMBtu/start, MOR-observed) wired into N3.

### Asset profile docs
- `data/assets/lockport/caveats.md` — 12 sections of operational caveats baked into data
- `data/assets/lockport/provenance.md` — source lineage for YAML values
- `data/assets/README.md` (existing) — updated cross-links to new guides

### Status taxonomy + assumptions
- `docs/assumptions/status_taxonomy.md` — 9-code grammar (already existed; referenced throughout)
- `docs/assumptions/placeholder_caveats.md`

### Tests
- `tests/test_lockport_static_profile.py` (67 tests)
- `tests/test_tech_class_defaults.py` (31 tests)
- Total 98/98 passing

### Repo infrastructure (this session's final push)
1. `README.md` at repo root (~280 lines) — entry point with quick-start + reading order
2. `CLAUDE.md` (~210 lines) — project context for future Claude Code sessions
3. `AGENTS.md` (~180 lines) — parallel agent-focused short version
4. `.cursor/commands/` + `.cursor/plans/` structure with placeholder docs
5. `.cursor/commands/PROMPT_CREATE_TASK_DOCS.md` — the task-history command template
6. `.claude/` (gitignored) for local Claude Code settings
7. **Local symlinks (gitignored)** in repo root for cross-repo navigation:
   - `.model-gpr` → `/Users/divy/code/work/infrasure_git_codes/model-gpr`
   - `.diligence-extractor` → `/Users/divy/code/personal/diligence-extractor`
   - `.renewablesinfo` → `/Users/divy/code/personal/renewablesinfo`
   - `.renewablesinfo_org` → `/Users/divy/code/personal/renewablesinfo_org`
8. **Git init + initial commit + push** to https://github.com/aamani-ai/GT_Modeling (via `github.com-work` SSH alias = D-ivyy account)
9. **Two follow-up commits**: gitignore for symlinks; CLAUDE.md/AGENTS.md/.cursor/

## §5. Files touched (categorized)

### Created
- `README.md`, `CLAUDE.md`, `AGENTS.md` (3 root-level docs)
- `docs/methodology/{pnl_ledger,architecture,dispatch_mechanics,gaps_and_priorities,glossary}.md` (5 docs)
- `docs/methodology/extra/backtest_findings.md`
- `docs/methodology/assets/modeled_vs_mor_vs_eia923.png`
- `docs/guides/{asset_profile_dimensions,pulling_specs_from_powerplantsinfo,future_dimensions}.md` (3 guides)
- `notebooks/05_model_vs_actual.{py,ipynb}` (new in this session)
- `notebooks/scratch/modeled_vs_mor_vs_eia923.py`
- `notebooks/scratch/monthly_comparison_2021_2025.parquet`
- `data/paths/lockport/mor_daily.parquet` (extracted from MOR workbooks)
- `data/extra/tasks_history/2026-05-15__gt-models__v1-lockport-shipped/{task_context,decisions,notes,handoff}.md` (this task doc)
- `.cursor/commands/PROMPT_CREATE_TASK_DOCS.md`
- `.cursor/{commands,plans}/README.md`

### Modified
- `notebooks/04_full_path_mode_comparison.{py,ipynb}` — steam-only branch + min-load constants + aging-formula fix + cold-start warming gas (ADR-002 Correction 1)
- `data/assets/lockport/engineering.yaml` — added boiler_id/type/count to GEN4
- `data/assets/lockport/operating_profile.yaml` — added steam_only_mode section with MOR-derived empirics
- `data/assets/README.md` — cross-links to new guides
- `docs/plans/consolidation_plan.md` §13 status log — 3 new entries
- `.gitignore` — added .claude/ + symlink entries
- `docs/methodology/{architecture,dispatch_mechanics,gaps_and_priorities,pnl_ledger}.md` — link audit fixes (./backtest_findings.md → ./extra/backtest_findings.md)

### Memory entries (in user's Claude memory at `~/.claude/projects/`)
- `feedback_explicit_cd_for_git.md` — captures the wrong-repo-push lesson + SSH alias table

### Git/repo
- `git init` in gt_models, first commit (138 files)
- 3 commits on `main` branch
- Pushed to https://github.com/aamani-ai/GT_Modeling (via github.com-work SSH = D-ivyy work account)

## §6. Current status (acceptance criteria)

- [x] Lockport asset profile complete (5 YAMLs + caveats + provenance)
- [x] 5 notebooks executable end-to-end with embedded plots
- [x] Methodology folder: 5 docs + extra/backtest_findings.md
- [x] Guides folder: 3 docs
- [x] 2 ADRs with full reasoning trails
- [x] 98/98 tests passing
- [x] Steam-only mode added to N4 (over-commit 2.22× → 2.07×)
- [x] Top-level README at repo root
- [x] CLAUDE.md + AGENTS.md for project context
- [x] .cursor/ structure with task-history command
- [x] Git initialized + pushed to aamani-ai/GT_Modeling (work account)
- [x] Multi-account SSH verified before push
- [x] renewablesinfo_org origin restored after wrong-repo-push incident
- [x] Memory lesson saved on explicit-cd-for-git

## §7. Next steps

In priority order (per `docs/methodology/gaps_and_priorities.md` §6):

1. **Team review** — share GitHub URL; collect feedback on framework + v2 priorities
2. **Data-room LTSA extraction** — replace 47 placeholder values (+$5-9M/yr Net P&L improvement)
3. **Add NYISO ICAP revenue layer** — currently $0; +$5-9M/yr
4. **Add cogen steam revenue** — currently $0; +$3-7M/yr (requires DHTS daily extraction + tariff)
5. **MOR-replay mode (Mode M)** in N4 — uses real daily dispatch trace for backtest validation
6. **Less conservative steam-only trigger** — switch from peak-LMP to avg-LMP basis
7. **Per-generator state (v2 architecture)** — unlocks 2×CC dispatch (currently 0% modeled vs 14% MOR)
8. **State initialization (L2 fix)** — add `known_inspections.yaml` + apply historical events as state-reset
9. **Phase L Monte Carlo** — quantify uncertainty bands; sweep Bucket B Athens constants
10. **Phase K refactor** — graduate notebooks → `src/` package

See `docs/methodology/gaps_and_priorities.md` for full ranked list with dollar magnitudes.
