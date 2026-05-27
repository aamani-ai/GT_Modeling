# AGENTS.md — gt_models

Agent-style essentials for working in this repo. This is the **short, action-oriented** version. For full project context read [`CLAUDE.md`](CLAUDE.md). For deeper methodology read [`docs/methodology/`](docs/methodology/).

## What this repo is

Gas turbine digital-twin modeling repo. v1 models a single asset (Lockport Energy Associates, NYISO Zone A, 1992 vintage, 3-on-1 CCGT cogen, 221 MW). 9-year deterministic backtest (2017–2025) × 3 dispatch policy modes (A/B/C) × 7 LTSA cost streams. Live at `https://github.com/aamani-ai/GT_Modeling`.

**Status**: v1 complete. 98/98 tests pass. v2 priorities documented in `docs/methodology/gaps_and_priorities.md` §6.

## Tools / commands

```bash
# Environment
python3 -m venv .venv && source .venv/bin/activate
pip install pandas numpy matplotlib pyyaml jupyter jupytext xlrd pyarrow nbconvert pytest

# Test
pytest tests/                            # → 98 passed

# Run a notebook (script form, fast)
cd notebooks && MPLBACKEND=Agg python3 04_full_path_mode_comparison.py

# Sync .py → .ipynb + execute with embedded plots
jupytext --to ipynb 04_full_path_mode_comparison.py
jupyter nbconvert --to notebook --execute --inplace 04_full_path_mode_comparison.ipynb

# Verify latest run
ls data/outputs/lockport/runs/    # find newest notebook4_<ts>/
cat data/outputs/lockport/runs/notebook4_<latest>/model_card.md
```

## Read order for new sessions

```
1. CLAUDE.md / AGENTS.md (this file) — project context
2. README.md — entry point + quick start + reading order
3. docs/methodology/pnl_ledger.md — economic ledger (what's modeled vs not)
4. notebooks/05_model_vs_actual.ipynb — model vs MOR backtest (13 plots)
5. docs/methodology/extra/backtest_findings.md — honest limitations
6. docs/methodology/gaps_and_priorities.md §6 — v2 priorities (where to invest next)
```

## Key conventions

| Topic | Convention |
|---|---|
| Notebook format | jupytext pairs: `.py` (percent format) is canonical, `.ipynb` is regenerated |
| YAML status taxonomy | Every leaf has `{value, status, source}` — 9 status codes in `docs/assumptions/status_taxonomy.md` |
| ADRs | Substantive decisions live in `docs/decisions/NNN-topic.md` with full reasoning trail |
| Asset profile | 7 YAMLs per asset: 5 core (`identity`/`engineering`/`operating_profile`/`market_context`/`ltsa_terms`) + 2 regime-decomposition (`capability_envelope`/`realized_operating_profile`, per ADR-003) + caveats.md + provenance.md |
| Plant archetype | Tag asset as one of: peaker / mid_merit / baseload / cogen / qf_purpa / rmr / battery / hybrid. Drives modeling defaults. Lockport = cogen + qf_purpa (TBD) + low_cf. |
| Outputs | `data/outputs/<asset>/runs/notebook4_<ts>/` — gitignored, regenerable from `run_config.yaml` |
| Annual primary | All dollar magnitudes in docs are annual averages; 9-year totals are derivations |
| Survivorship | Lockport has operated since 1992 → any "real" Net P&L conclusion must pass `≥0 on average` plausibility |

## Don'ts

| Don't | Reason |
|---|---|
| Don't push without explicit `cd /absolute/path && pwd && git ...` | Bash cwd doesn't reliably persist; previously caused a wrong-repo push |
| Don't change `git config user.name/email` | Per safety rule; user manages identity |
| Don't commit `data/outputs/` | Regenerable; gitignored |
| Don't try to "fix" documented findings before team weighs in | Steam-only trigger, generic starting state, Mode A/B/C late divergence are all KNOWN — v2 work, not bugs to silently patch |
| Don't use default `git@github.com:...` for aamani-ai org pushes | Default resolves to Divi-patel (personal); use `github.com-work` alias instead |

## Multi-account SSH (verified 2026-05-15)

| Alias | Authenticates as | Use for |
|---|---|---|
| `github.com-work` | D-ivyy | aamani-ai org (this repo) |
| `github.com-personal` | Divi-patel | personal repos (renewablesinfo / renewablesinfo_org / etc.) |
| `github.com-divy` | D-ivy | data-centers-info lab |
| `github.com` (default) | Divi-patel | (resolves to personal — avoid for work pushes) |

Verify with: `ssh -T git@github.com-X 2>&1 | head -1`

## Cross-repo navigation (gitignored symlinks in repo root)

```
.model-gpr/            → /Users/divy/code/work/infrasure_git_codes/model-gpr
.diligence-extractor/  → /Users/divy/code/personal/diligence-extractor
.renewablesinfo/       → /Users/divy/code/personal/renewablesinfo
.renewablesinfo_org/   → /Users/divy/code/personal/renewablesinfo_org
```

The `gt_models` repo doesn't include these — they're local-machine conveniences for cross-repo navigation. From inside `gt_models/` you can `cd .renewablesinfo_org/` etc.

## What v1 does NOT have

Explicit non-goals (documented in `docs/methodology/extra/backtest_findings.md` §3.7 + `gaps_and_priorities.md`):

- ❌ No Monte Carlo (Phase L work)
- ❌ No multi-asset support (v2+)
- ❌ No `src/` package (Phase K refactor target — currently logic lives in notebooks)
- ❌ No real LTSA values (all Athens placeholder, pending data-room extraction)
- ❌ No steam revenue / capacity revenue / ancillary revenue (R2/R3/R4 in p&l_ledger)
- ❌ No per-generator state (block-level state vector)
- ❌ No forecast-error modeling (v1 has perfect foresight)
- ❌ No historical inspection events modeled (e.g., Fall 2018 HGP outage on Unit 1)
- ❌ No archetype-tagged policy frameworks (Mode A/B/C is one-size for now)

## v1 headline numbers (latest run)

| Mode | Spark (9-yr) | LTSA (9-yr) | **Net P&L** | Annual |
|---|---:|---:|---:|---:|
| A | $36.08M | $203.24M | **−$167.16M** | −$18.57M/yr |
| B | $33.15M | $175.62M | **−$142.47M** | −$15.83M/yr |
| C | $33.11M | $175.60M | **−$142.50M** | −$15.83M/yr |

**Over-commit ratio (Mode A vs MOR 2021–2025)**: 2.07×. Real Lockport's plausible Net P&L (after closing all input gaps): **+$2 to +$4M/yr** per `docs/methodology/pnl_ledger.md` §4.

## Common patterns

### Reading a model_card honestly

Check assumption distribution at the top (80% real / 17.5% placeholder for Lockport). Treat:
- **Mode comparison delta**, not absolutes → meaningful
- **LTSA stream breakdown** → directionally meaningful (proportions), absolute dollars driven by placeholders
- **MOR backtest table** → the real validation signal
- **Cumulative Net P&L** → NOT a financial projection; use annual averages and adjust per `pnl_ledger.md` §4 reconciliation

### Onboarding a new asset (when this happens)

1. Read [`docs/guides/asset_profile_dimensions.md`](docs/guides/asset_profile_dimensions.md) for the framework
2. Read [`docs/guides/pulling_specs_from_powerplantsinfo.md`](docs/guides/pulling_specs_from_powerplantsinfo.md) for the lift-from-platform workflow
3. Classify by archetype (peaker / mid_merit / baseload / cogen / qf_purpa)
4. Build the 5 core YAMLs + caveats + provenance (then capability_envelope + realized_operating_profile per the capability-envelope skill / `extracting_capability_from_thermal_archive.md`)
5. Pull time-series spine into `data/paths/<new-asset>/`
6. Add tests at `tests/test_<new-asset>_static_profile.py`
7. Run N1 to validate spine; iterate

### When to write a new doc vs extend existing

- New ADR if: substantive decision with ≥2 alternatives + downstream consequences (`docs/decisions/NNN-topic.md`)
- New finding doc if: backtest-level observation or analytical artifact (`docs/methodology/extra/`)
- Extend existing methodology doc if: incremental clarification or new section
- New guide if: how-to that scales beyond one asset (`docs/guides/`)
- Update caveats.md if: non-obvious convention baked into data

## Project state at v1 close (2026-05-15)

- 2 commits on `main` pushed to `aamani-ai/GT_Modeling`
- Initial commit: 138 tracked files
- Follow-up: `.gitignore` updated for local symlinks
- Tests passing, all 5 notebooks executable, all docs cross-linked

## Where to ask questions

1. The user (project owner) — this is a single-person project so far
2. The team — pulled in for v1 review; their priorities feed v2 direction
3. For modeling physics questions: `docs/learning/` (currently sparse; expands with knowledge-base work)
4. For decision history: `docs/decisions/` ADRs + `docs/plans/consolidation_plan.md` §13 status log
