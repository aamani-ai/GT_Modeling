# Handoff — gt_models v1 Lockport Build (2026-05-15)

> **The 60-second summary**: v1 of the gas-turbine digital-twin model is complete for Lockport. 5 notebooks + 5 methodology docs + 3 guides + 2 ADRs + README/CLAUDE.md/AGENTS.md. 98/98 tests pass. Shipped to https://github.com/aamani-ai/GT_Modeling via D-ivyy work account. Net P&L numbers are structurally meaningful but absolutely biased (placeholder LTSA values + missing revenue streams) — survivorship-calibrated real economics plausibly +$2-4M/yr. Team review is the next step.

---

## 10-bullet summary

1. **Asset**: Lockport Energy Associates LP (EIA Plant ID 54041) — NYISO Zone A, 1992 vintage, 3-on-1 CCGT cogen, 221 MW. Per consolidation plan D4 (single asset for v1).
2. **5 notebooks built** (Phases G-J + supplement): N1 data spine → N2 one-day dispatch → N3 30-day feedback loop → N4 9-yr capstone (model_card output) → N5 MOR backtest deep-dive (13 plots).
3. **Steam-only mode added** to N4 mid-session after MOR data revealed 460 days (25.2%) of 0-MWh + non-zero-gas operation via duct burner (EIA-860 `boiler_type="Db"`). Over-commit dropped 2.22× → 2.07× vs MOR.
4. **5-doc methodology folder** + extra/backtest_findings.md: pnl_ledger (economic ledger entry point), architecture (how v1 works), dispatch_mechanics (operating mode × policy mode), gaps_and_priorities (ranked v2 priorities), glossary, plus the backtest findings as the analytical companion.
5. **3-guide folder**: pulling_specs_from_powerplantsinfo (lift-from-platform workflow), asset_profile_dimensions (5-dimension framework + plant archetypes proposal), future_dimensions (design specs for outage_history/offtake_contracts/fixed_opex when data arrives).
6. **2 ADRs**: 001 (Henry Hub for v1, Algonquin basis deferred), 002 (3-bucket calibration inventory — Lockport-specific / generic F-class / placeholder pending data room).
7. **MOR data extracted**: `data/paths/lockport/mor_daily.parquet` — 1,826 daily rows (2021-2025) from diligence-extractor. **This is the truth source** for backtests; EIA-923 has ~6-12 month federal reporting lag.
8. **Repo infrastructure shipped**: README.md (entry point), CLAUDE.md (project context for future Claude sessions), AGENTS.md (parallel agent-focused version), .cursor/commands/ + .cursor/plans/ structure, 4 local symlinks (gitignored) for cross-repo navigation (.model-gpr, .diligence-extractor, .renewablesinfo, .renewablesinfo_org).
9. **Git/push setup**: pushed via `github.com-work` SSH alias (D-ivyy work account) to https://github.com/aamani-ai/GT_Modeling. Multi-account verified before push (`ssh -T git@github.com-work` → "Hi D-ivyy!"). DON'T use default github.com — resolves to Divi-patel personal.
10. **Wrong-repo-push incident** (recovered): mid-session I pushed renewablesinfo_org content to wrong remote due to assumed Bash cwd persistence. User deleted the GT_Modeling- repo and provided new URL. Restored renewablesinfo_org origin. Lesson saved as `feedback_explicit_cd_for_git.md` memory. **Always `cd /abs/path && pwd && git ...` in same Bash call.**

---

## Files touched (quick map)

### Created (in this session)
```
README.md, CLAUDE.md, AGENTS.md                                        # repo-root entry
docs/methodology/{pnl_ledger,architecture,dispatch_mechanics,gaps_and_priorities,glossary}.md
docs/methodology/extra/backtest_findings.md
docs/methodology/assets/modeled_vs_mor_vs_eia923.png
docs/guides/{asset_profile_dimensions,pulling_specs_from_powerplantsinfo,future_dimensions}.md
docs/extra/tasks_history/2026-05-15__gt-models__v1-lockport-shipped/{task_context,decisions,notes,handoff}.md   # THIS doc
docs/decisions/00{1,2}-*.md                                            # 2 ADRs
docs/assumptions/{status_taxonomy,placeholder_caveats}.md
data/assets/lockport/{identity,engineering,operating_profile,market_context,ltsa_terms}.yaml
data/assets/lockport/{caveats,provenance}.md
data/paths/lockport/{lmp_da_hourly,gas_price_history,weather_hourly,mor_daily}.parquet
notebooks/0{1,2,3,4,5}_*.{py,ipynb}
notebooks/scratch/modeled_vs_mor_vs_eia923.py
tests/test_{lockport_static_profile,tech_class_defaults}.py            # 98 tests passing
.cursor/{commands,plans}/                                              # task-history infra
```

### Modified (in this session)
```
notebooks/04_full_path_mode_comparison.{py,ipynb}                      # +steam-only branch, +min-load, +aging fix
data/assets/lockport/engineering.yaml                                  # +boiler_id/type/count to GEN4
data/assets/lockport/operating_profile.yaml                            # +steam_only_mode section
docs/methodology/{architecture,dispatch_mechanics,gaps_and_priorities,pnl_ledger}.md  # link audit fixes
docs/plans/consolidation_plan.md §13                                   # 3 new status log entries
data/assets/README.md                                                  # cross-links to new guides
.gitignore                                                             # +.claude/ +symlink entries
```

### Memory (persistent across sessions, at `~/.claude/projects/`)
```
feedback_explicit_cd_for_git.md   # the wrong-repo-push lesson + SSH alias table
```

### Local-only (gitignored)
```
.claude/settings.json                                                  # Claude Code permissions
.model-gpr → /Users/divy/code/work/infrasure_git_codes/model-gpr
.diligence-extractor → /Users/divy/code/personal/diligence-extractor
.renewablesinfo → /Users/divy/code/personal/renewablesinfo
.renewablesinfo_org → /Users/divy/code/personal/renewablesinfo_org
```

---

## Repro commands

```bash
# Open repo
cd /Users/divy/code/work/infrasure_git_codes/gt_models
pwd  # confirm

# Verify state
git log --oneline | head -5
git remote -v
git status

# Run tests
pytest tests/

# Run latest notebook
cd notebooks
MPLBACKEND=Agg python3 04_full_path_mode_comparison.py

# Inspect latest model_card
ls data/outputs/lockport/runs/                # find newest notebook4_<ts>
cat data/outputs/lockport/runs/notebook4_*/model_card.md

# Cross-repo navigation (uses local symlinks)
cd .diligence-extractor                       # → /Users/divy/code/personal/diligence-extractor
cd .renewablesinfo_org                        # → /Users/divy/code/personal/renewablesinfo_org
```

---

## Next session: execution roadmap

### Phase 0 — Read this first (5 min)

Before starting work in a new session, read in this order:
1. `CLAUDE.md` — project context, conventions, file paths, don'ts
2. `README.md` §"Reading order" — entry-point doc map
3. `docs/methodology/pnl_ledger.md` — the economic ledger
4. **THIS handoff.md** — what was done in the prior session

After that, you have full context to start.

### Phase A — Most likely next work: data-room LTSA extraction

If team approves data-room extraction as priority #1 (most likely):

1. **Locate the data**: `.diligence-extractor/data/lockport/3.0 Lockport/3.2 Financial Statements/` and `.diligence-extractor/data/lockport/3.0 Lockport/3.4 O&M Reports/`
2. **Target file**: `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` (per `ltsa_terms.yaml.extraction_status.validation_path`)
3. **Read the schema**: `docs/methodology/pnl_ledger.md §3.C` — 8 LTSA streams + L-codes
4. **Read the placeholders**: `data/assets/lockport/ltsa_terms.yaml` — what to replace
5. **Replace values** following status taxonomy: `status: placeholder` → `status: real_reported` with proper `source`
6. **Re-run N4** + verify model_card shows updated LTSA stream breakdown
7. **Update**: `docs/methodology/extra/backtest_findings.md` with new headline numbers
8. **Likely follow-up**: write ADR-003 documenting any non-obvious extraction choices

**Critical context for LTSA extraction**:
- Athens-prototype placeholders are likely 2-3× too high for Lockport (32-year-old cogen)
- Plausible Lockport range per pnl_ledger.md §4: fixed fee $3.6-7.2M/yr (vs $11.96M/yr placeholder)
- Survivorship-bias anchor: real LTSA must allow plant to be at least breakeven on average
- Don't forget to check PURPA contract status (R5 in pnl_ledger) — might add to revenue side

### Phase B — Add NYISO ICAP revenue layer (parallel to A)

If priority #2:
1. Read `docs/guides/future_dimensions.md` §3 for `offtake_contracts.yaml` design spec
2. Get Lockport UCAP rating from NYISO MOC test results (data room: `3.6.19 03202026 LEA NYISO Escrow.pdf` may have related info)
3. Pull NYISO Zone A capacity prices time series (public NYISO data)
4. Create `data/assets/lockport/offtake_contracts.yaml` per design spec
5. Add ICAP revenue layer in N4's daily loop (monthly accrual: `ucap_mw × $/kW-month × months_in_period`)
6. Re-run + verify

### Phase C — Add cogen steam revenue

If priority #3:
1. Extract DHTS daily from MOR data (already in `mor_daily.parquet` as `dhts_net_thermal_mmbtu`)
2. Get steam tariff from `.diligence-extractor/data/lockport/3.0 Lockport/3.1 Commercial Agreements/` (if available)
3. Add to N4: `steam_revenue_daily = mor_dhts_mmbtu × tariff_per_mmbtu`
4. Currently dhts is in operating_profile.yaml but no tariff field — add to new offtake_contracts.yaml

### Phase D — MOR-replay Mode M (validates everything)

Per `gaps_and_priorities.md §5`:
1. Add `mode == "M"` branch in N4's `run_mode()`
2. Skip spark optimization; use `mor_daily.parquet`'s observed daily mode/MWh directly
3. Run LTSA accrual against real dispatch
4. Compare model_card outputs: "what would v1 say the LTSA bill should have been for the actually-observed dispatch?"
5. Cross-check against any LTSA invoices in data room

### Phase E — Phase K refactor (graduate notebooks to src/)

When ready for code cleanup:
1. Read `docs/plans/consolidation_plan.md` §8 Phase K + `docs/methodology/gaps_and_priorities.md` §6
2. Target layout: `src/gt_models/{state, dispatch, stress, schedule, ltsa, inspection, outage, policy, io}.py`
3. Pull out PlantState, dispatch_day_mode_aware, etc. from N4 into reusable modules
4. Add unit tests for each module
5. Notebooks become thin drivers

### Phase F — Phase L Monte Carlo (uncertainty bands)

When ready:
1. Read `docs/methodology/gaps_and_priorities.md` §6 + `architecture.md` §8.2
2. Replace fixed-seed RNG with 50+ paths
3. Sweep Bucket B constants (Athens defaults) — fatigue per start, TBC eta, fouling rates, HRSG/BG age multipliers
4. Replace historical replay with synthetic scenario engine (Step 1 from .model-gpr/)
5. Produce P10/P50/P90 distributions per mode

---

## Critical context / gotchas

### Multi-account SSH (re-verify before any push)
```bash
ssh -T git@github.com-work 2>&1 | head -1     # → "Hi D-ivyy!" (work)
ssh -T git@github.com-personal 2>&1 | head -1 # → "Hi Divi-patel!" (personal)
ssh -T git@github.com 2>&1 | head -1          # → "Hi Divi-patel!" (default = personal — DON'T USE for work repos)
```

Work repos (aamani-ai org): use `git@github.com-work:aamani-ai/...`
Personal repos: use `git@github.com-personal:Divi-patel/...`

### Explicit cd in every git Bash call
Always: `cd /absolute/path && pwd && git ...` in the SAME Bash invocation. The Bash tool's cwd reverts to env's Primary working directory (`renewablesinfo_org`) when not explicit. This caused the wrong-repo-push incident.

### What v1's Net P&L numbers DON'T mean
- They're NOT a financial projection
- They're NOT a claim that Lockport is unprofitable
- The −$167M/9yr Mode A figure is structurally biased by:
  - Placeholder LTSA values (likely 2× too high)
  - Missing revenue streams (steam, ICAP, ancillary)
  - Over-commit dispatch (2.07× vs MOR)
  - Perfect-foresight advantage (real operator with forecast error would dispatch less)

The CORRECT interpretation is in `pnl_ledger.md §4`: real Lockport Net P&L plausibly +$2-4M/yr after closing input gaps. Survivorship constraint: plant has operated since 1992, so it must be at least breakeven on average.

### What IS available vs needs fetching

| Available now | Needs work-room access / extraction |
|---|---|
| Lockport EIA-860 enriched (in `.renewablesinfo_org` pipeline) | Trial balance LTSA invoice line items |
| Lockport MOR daily 2021-2025 (`data/paths/lockport/mor_daily.parquet`) | Steam tariff contract terms |
| Lockport time-series spine (LMP, gas, weather) | Historical inspection events (Fall 2018 HGP outage known but not modeled) |
| 98 passing tests | NYISO ICAP commitment terms |
| Latest N4 model_card at `data/outputs/lockport/runs/notebook4_*/` | PURPA contract status |
| 5 methodology docs + 3 guides + 2 ADRs | Insurance / property tax / Fixed O&M values |

### Known issues / open questions for team

1. **N3 aging-formula bug not backported** — fix in N4 (year_frac capped) doesn't propagate to N3. Functionally invisible at N3's 30-day window. Worth backporting? (User asked this in README.md "Feedback the team can help with")
2. **Steam-only trigger conservative** — 18% recall of real MOR steam-only days. Refinement to avg-LMP basis would lift recall. Wait for team direction.
3. **Mode A/B/C framework doesn't fit low-CF assets** — wear-penalty mechanic activates only near inspection threshold (end of 9-yr sim at Lockport's CF). Different policy frameworks needed for cogens / peakers. v2 work.
4. **Starting-state initialization** — model assumes state.eoh = 24,000 at 2017-01-01 (generic prototype default). Real Lockport had 25-year operating history; should initialize based on data-room records. L1 fix: tune state.eoh in YAML. L2 fix: add `known_inspections.yaml`. Documented in backtest_findings.md §3.7.

### Files to consult before changes

| If changing... | Read first |
|---|---|
| Asset profile YAMLs | `docs/guides/asset_profile_dimensions.md`, `docs/guides/pulling_specs_from_powerplantsinfo.md` |
| N4 dispatch logic | `docs/methodology/architecture.md` §5, `docs/methodology/dispatch_mechanics.md`, `docs/decisions/00{1,2}-*.md` |
| LTSA cost streams | `docs/methodology/pnl_ledger.md` §3.C, `data/assets/lockport/ltsa_terms.yaml` |
| Status codes | `docs/assumptions/status_taxonomy.md` |
| Adding a new YAML dimension | `docs/guides/future_dimensions.md` |
| New asset onboarding | `docs/guides/pulling_specs_from_powerplantsinfo.md` |
| Modeling decision | Should it be an ADR? See `docs/decisions/README.md` |

---

## Conversation summary (for context if needed)

The session started as a tactical question about non-renewable/gas data sources for dispatch modeling. It evolved through:

1. **Discovery phase**: identifying Lockport's CT/CA configuration, exploring renewablesinfo_org platform data
2. **Build phase**: Phases G-J — 5 notebooks, asset YAMLs, methodology docs, ADRs
3. **Refinement phase**: steam-only mode discovery from MOR, multiple corrections (aging bug, recall calculation, Net P&L reconciliation)
4. **Documentation phase**: 5 methodology docs + 3 guides + assumption taxonomy
5. **Conceptual phase**: plant archetype framework, future dimensions design, perfect-foresight caveat, bracketing view
6. **Polish phase**: README, link audit, error decomposition (§O.1/O.2/O.3 in N5)
7. **Ship phase**: git init, push (with recovery from wrong-repo-push incident), multi-account SSH setup
8. **Continuity phase**: CLAUDE.md, AGENTS.md, .cursor/ structure, task history docs (this one)

User's recurring patterns:
- **Honest analysis preferred over polished claims** — repeatedly pushed back on over-optimistic framings
- **Annual unit preferred over multi-year totals** — natural for plant economics
- **Survivorship-bias anchor** — real operating asset must be at least breakeven
- **Lab-first then production pattern** — explore raw data before deciding what to extract
- **Documentation discipline** — every substantive decision gets an ADR or caveat entry
- **Cross-repo awareness** — gt_models consumes from renewablesinfo_org + diligence-extractor

User's preferences:
- Take time, get it right
- Plot when visualization helps; not for its own sake
- Document limitations clearly; don't hide them
- Status-tag everything (the 9-code taxonomy)
- Test before committing
- Pull from the platform pipeline whenever possible

---

## Final state at session end

```
Repo: gt_models (local at /Users/divy/code/work/infrasure_git_codes/gt_models)
Remote: https://github.com/aamani-ai/GT_Modeling (work account D-ivyy via github.com-work SSH)
Branch: main
Commits: 4 (initial + symlinks gitignore + claude/agents/cursor + this task doc)
Working tree: clean
Tests: 98/98 passing
Latest run: data/outputs/lockport/runs/notebook4_20260515_093651/
Tracked files: ~145 (138 + 4 new this session + task docs)
Documentation: ~5,000 lines methodology+guides+decisions+README

Next: team review → likely data-room LTSA extraction as Phase A
```
