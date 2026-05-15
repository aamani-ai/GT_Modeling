# Implementation Notes — v1 Lockport Build

> Topical sections covering implementation details, commands used, verification steps, metrics, and key insights from the session.

---

## §1. Notebook sequence + run patterns

### Workflow established
1. Write `.py` file (jupytext percent format) — canonical source
2. Run as script first to verify: `MPLBACKEND=Agg python3 NN_topic.py`
3. Convert to `.ipynb`: `jupytext --to ipynb NN_topic.py`
4. Execute to embed plots: `jupyter nbconvert --to notebook --execute --inplace NN_topic.ipynb`
5. Verify with: `python3 -c "import json; nb = json.loads(open('NN_topic.ipynb').read()); ..."`

### Notebook outputs
| Notebook | Code cells | PNGs embedded | Run time |
|---|---:|---:|---|
| N1 — data_spine | ~10 | 0 | <2s |
| N2 — one_day_dispatch | 11 | 0 (text-only) | 3.3s |
| N3 — daily_loop_feedback | 15 | 4 | ~10s |
| N4 — full_path_mode_comparison | 22 | 6 | ~50s |
| N5 — model_vs_actual | 19 | 13 | ~30s |

### Latest N4 run bundle
`data/outputs/lockport/runs/notebook4_20260515_093651/` — contains:
- `model_card.md` (headline summary)
- `run_config.yaml` (seed, mode params, escalation, etc.)
- `daily_summary_mode_{a,b,c}.parquet`
- `state_trajectory_mode_{a,b,c}.parquet`
- `ltsa_streams_mode_{a,b,c}.parquet`
- `inspection_events.parquet`, `forced_outage_events.parquet`

---

## §2. MOR data extraction

### Source
`/Users/divy/code/personal/diligence-extractor/data/lockport/3.0 Lockport/3.4 O&M Reports/3.4.20 Monthly Operating Reports/`

5 yearly Excel workbooks (`3.4.20.N <year>/monthly_report_data <year>.xls`) with monthly sheets.

### Extraction script
`notebooks/scratch/modeled_vs_mor_vs_eia923.py` — inlines the parsing logic from diligence-extractor's `notebooks/daily_heat_rate_analysis.ipynb`. Key columns extracted:

| Col index | Semantic name | Unit |
|---:|---|---|
| 1 | `ambient_temp_f` | °F |
| 2 | `net_output_mwh` | MWh |
| 3 | `gross_output_mwh` | MWh |
| 6 | `net_station_output` | MWh |
| 7 | `dhts_steam_load_mmbtu` | MMBtu |
| 9 | `dhts_net_thermal_mmbtu` | MMBtu |
| 11 | `ctg1_mwh` | MWh |
| 12 | `ctg2_mwh` | MWh |
| 14 | `ctg3_mwh` | MWh |
| 15 | `stg_mwh` | MWh |
| 16 | `plant_run_time_hrs` | hrs |
| 17 | `total_gas_mmbtu` | MMBtu |

### Result
`data/paths/lockport/mor_daily.parquet`:
- 1,826 daily rows (2021-01-01 → 2025-12-31)
- 16 columns
- 90 KB

### Required dependency
`xlrd` (not in default env): `pip install xlrd`

### Key MOR-derived findings extracted into YAML
- Heat rate by mode (volume-weighted across 5 years):
  - 3xCC: 8,901 Btu/kWh (189 operating days)
  - 2xCC: 9,598 Btu/kWh (76 operating days)
  - 1xCC: 10,424 Btu/kWh (26 operating days)
- Cold start warming gas: 2,537 MMBtu per cold start (mean across 35 cold-start events)
- **Steam-only mode**: 460 days (25.2% of 1,826) with 0 MWh + non-zero gas + non-zero DHTS
  - Median gas burn: 871 MMBtu/day
  - Median DHTS: 589 MMBtu/day
  - Gas-to-steam efficiency: 45.8% (ratio of totals)

---

## §3. The aging-formula bug saga

### Symptom
N4 produced 86-87 forced-outage events per mode per 9-year run. Expected ~30-50.

### Root cause
The formula in N3 (inherited from prototype):
```python
age_mult = 1.0 + year_frac * (HRSG_AGE_MULT_MAX - 1.0)
```
With `year_frac = day_idx / 365.0` and `HRSG_AGE_MULT_MAX = 1.5`:
- year 1: age_mult = 1.0 + 1.0 × 0.5 = 1.5 ✓
- year 9: age_mult = 1.0 + 9.0 × 0.5 = **5.5** ✗ (should cap at 1.5)

The formula was intended for `year_frac = fraction of 10-year aging window`, NOT `years elapsed`. N3's 30-day window made `year_frac < 0.1` — bug invisible. N4's 9-year horizon compounded it.

### Fix
N4 §E.4 now uses:
```python
AGING_WINDOW_YEARS = 10.0
aging_frac = min(years_elapsed / AGING_WINDOW_YEARS, 1.0)
age_mult_hrsg = 1.0 + aging_frac * (HRSG_AGE_MULT_MAX - 1.0)
```

### Verification
After fix: forced-outage events dropped to 35-36 per mode per 9-year. Sanity check bound widened to `0 ≤ n ≤ 100`. All checks pass.

### Backport status
N3 was NOT backported (its short window makes the bug functionally invisible). Documented in CLAUDE.md as a known open question for team review.

---

## §4. The steam-only mode discovery sequence

### Step 1: Plot showed cumulative-negative spark in N4 output
User asked: "why a lot of historical data shows negative spark? At least for a few years, we have actual generation, so would you be able to give me a plot of that actual generation path versus what we are modeling?"

### Step 2: First comparison plot using EIA-923
- Built `notebooks/scratch/modeled_vs_mor_vs_eia923.py`
- Found EIA-923 had 39K MWh for Jan 2024 only; rest of 2024 zero
- Conclusion: EIA-923 data lag — needed better source

### Step 3: User pointed to diligence-extractor
- `/Users/divy/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb`
- Extracted 1,826 daily MOR rows from 2021-2025 workbooks

### Step 4: Anomalous days revealed steam-only mode
```python
anomaly = mor_daily[
    (mor_daily['net_output_mwh'].fillna(0) == 0)
    & (mor_daily['total_gas_mmbtu'].fillna(0) > 100)
    & (mor_daily['dhts_net_thermal_mmbtu'].fillna(0) > 100)
]
# Found 460 days, 584K MMBtu gas, 268K MMBtu DHTS, all years 2021-2025
```

### Step 5: Mechanism confirmed via EIA-860
Looking at `/Users/divy/code/personal/renewablesinfo_org/data/sources/eia/eia860/eia8602024/`:
- `3_1_Generator_Y2024.xlsx`: GEN4 (steam) `Duct Burners = Y`; CTs `Can Bypass HRSG = Y`
- `6_2_EnviroEquip_Y2024.xlsx` `Boiler Info & Design Parameters` sheet: Boiler ID 4, `Type of Boiler = Db` (Duct Burner)

### Step 6: Doc correction
Originally `dispatch_mechanics.md §6` said: "at Lockport, you can't produce steam without also producing electricity — they're physically coupled." MOR data contradicted this. Corrected §6 with explicit acknowledgment + new "two modes of steam delivery" ASCII diagram.

### Step 7: N4 implementation
Added steam-only branch in `run_mode()`:
```python
if must_run_today:
    day_max_lmp = float(hourly["lmp"].max())
    best_hr = hr_degraded_for_mode("3xCC_full", state)
    best_fuel_cost = best_hr / 1000 * (gas_hh + RGGI_COST_PER_MMBTU)
    best_spark = day_max_lmp - best_fuel_cost - VOM_USD_PER_MWH
    if best_spark <= 0:
        steam_only_today = True

if steam_only_today:
    # 0 MWh, no state changes, only gas cost
    steam_only_total_cost = STEAM_ONLY_GAS_MMBTU_PER_DAY * (gas_hh + RGGI_COST_PER_MMBTU)
    state.op = False
    state.hrs_off = min(state.hrs_off + 24, 24.0 * 30)
    # ... record day, continue
```

### Step 8: Impact verification
Before: 2.22× over-commit, Mode A Net P&L −$203M/9yr
After: 2.07× over-commit, Mode A Net P&L −$167M/9yr (Mode B: −$143M)

Trigger is conservative — catches 18% of MOR steam-only days (95% precision). Future refinement: avg-LMP basis.

---

## §5. Multi-account SSH for repo push

### Initial mistake
Pushed `renewablesinfo_org`'s main branch to `https://github.com/aamani-ai/GT_Modeling-.git` (the original GT_Modeling- with trailing dash).

### Root cause
Bash tool's working directory doesn't reliably persist across separate Bash calls. After `cd /Users/divy/code/work/infrasure_git_codes/gt_models && git init` succeeded, subsequent `git remote -v` and `git remote add` commands ran in the env's Primary working directory (`renewablesinfo_org`) — modifying that repo's origin and pushing its main branch.

### Recovery
1. User deleted the GT_Modeling- remote on GitHub
2. Restored `renewablesinfo_org` origin: `cd /path && git remote set-url origin git@github.com-personal:Divi-patel/renewablesinfo_org.git`
3. Fetched to verify connectivity: `git fetch origin` → all branches OK
4. User created new remote with cleaner name: `https://github.com/aamani-ai/GT_Modeling.git` (no trailing dash)

### Correct approach (used for the actual gt_models push)
```bash
# Verify SSH alias authenticates as expected work account
ssh -T git@github.com-work 2>&1 | head -1   # → "Hi D-ivyy!" ✓

# All git commands in same Bash call with explicit cd + pwd verification
cd /Users/divy/code/work/infrasure_git_codes/gt_models && pwd \
  && git branch --show-current \
  && git log --oneline | head -3 \
  && git remote -v
# Verified: cwd correct, main branch with 2 commits, no leftover origin

# Then in another Bash call (still with explicit cd):
pwd \
  && git remote add origin git@github.com-work:aamani-ai/GT_Modeling.git \
  && git remote -v \
  && git push -u origin main
```

### Memory lesson saved
`/Users/divy/.claude/projects/-Users-divy-code-personal-renewablesinfo-org/memory/feedback_explicit_cd_for_git.md` — captures the pattern + SSH alias table.

---

## §6. The bracketing-view plot evolution

### Iteration 1: cumulative band (rejected)
First N5 §E.5 implementation used cumulative-over-time generation with shaded band between Mode A and Mode C, MOR overlaid.

User feedback: "we don't want to accumulate your generation plot, because that would kind of compound the errors and doesn't showcase what we really want to show."

### Iteration 2: monthly view (accepted)
Replaced with:
- Top panel: monthly line plot (Mode A red / Mode C green / MOR black) + shaded band fill
- Bottom panel: annual bars (Mode A / Mode C / MOR side by side per year) with INSIDE/OUTSIDE labels

### Year-by-year diagnostic that emerged
```
2021: Mode A=159  Mode C=159  band_width=0    MOR=56   OUTSIDE -103 GWh
2022: Mode A=330  Mode C=330  band_width=0    MOR=196  OUTSIDE -134 GWh
2023: Mode A=205  Mode C=205  band_width=0    MOR=88   OUTSIDE -117 GWh
2024: Mode A=518  Mode C=518  band_width=0    MOR=192  OUTSIDE -325 GWh
2025: Mode A=734  Mode C=630  band_width=104  MOR=408  OUTSIDE -222 GWh
```

### What the plot revealed
1. **Band collapsed** for 4 of 5 years (wear-penalty mechanic only activates near inspection threshold, which is end of 9-yr sim at Lockport's low CF)
2. **MOR below band** every year (absolute bias dwarfs policy choice)
3. **Two-axis failure** of the bracketing framework — both axes traceable to v1 limitations, not framework conceptual flaw

---

## §7. Survivorship-bias sanity check

### User insight
Initial Net P&L reconciliation in `pnl_ledger.md §4` put "Real Economic Net P&L = −$15 to $0M/yr." User pushed back: Lockport has been operating since 1992; sustained-negative cash flow over decades isn't consistent with continued operation.

### What was wrong with the initial estimate
1. Compounded conservative-end ranges (low revenue + high cost)
2. Used Athens-scale LTSA fixed fee ($11.96M/yr placeholder → $3.6-7.2M/yr "real") when a 32-year-old plant past its original CSA likely renegotiated to $3-5M/yr
3. Weighted steam revenue at low end ($2M/yr) when cogen contracts of this scale typically run $4-8M/yr
4. Gave PURPA premium $0 weight when contract status is TBD

### Corrected approach
Add explicit survivorship anchor: any reconciliation that produces sustained-negative cash flow is automatically suspect.

Revised ranges:
- "Improved" Net P&L (Legs 1+2+3 fixed): +$0 to +$20M/yr, central ~+$10M/yr
- Real economic Net P&L (after Fixed OPEX F1-F7): +$0 to +$8M/yr, central ~+$2-4M/yr

Documented in `pnl_ledger.md §4.1` (the survivorship constraint) and as a "what I did wrong with my earlier numbers" subsection (§4.4).

---

## §8. Doc cross-linking + link audit

### Move: backtest_findings.md → methodology/extra/
User instruction: "If we have the backtesting results file that doesn't look good, we don't want to clutter the main files, so that's why I created this extra folder."

### Link audit before push
After move, 6 broken refs found in:
- `docs/methodology/gaps_and_priorities.md` (2 refs)
- `docs/methodology/architecture.md` (1)
- `docs/methodology/pnl_ledger.md` (1)
- `docs/methodology/dispatch_mechanics.md` (2)

Fixed via:
```bash
for f in <files>; do
  sed -i.bak 's|\](./backtest_findings.md|\](./extra/backtest_findings.md|g' "$f"
  rm "$f.bak"
done
```

---

## §9. Test verification

### Test command
```bash
cd /Users/divy/code/work/infrasure_git_codes/gt_models && pytest tests/ 2>&1 | tail -5
```

### Result
```
98 passed in 1.21s
```

### Coverage
- `tests/test_lockport_static_profile.py` — 67 tests
- `tests/test_tech_class_defaults.py` — 31 tests

Tests cover:
- YAML structure (every leaf has value+status+source)
- Status code validity (one of 9 codes)
- Cross-references between YAMLs
- Tech-class defaults lookup correctness
- Lockport-specific field validation

---

## §10. Repo infrastructure setup

### Files at repo root (final state)
```
gt_models/
├── README.md                     ~280 lines — entry point
├── CLAUDE.md                     ~210 lines — Claude Code project context
├── AGENTS.md                     ~180 lines — Agent-focused short version
├── .gitignore                    Standard + .claude/ + symlinks
├── .claude/                      (gitignored) Local Claude Code settings
├── .cursor/
│   ├── commands/
│   │   └── PROMPT_CREATE_TASK_DOCS.md
│   └── plans/
│       └── README.md
├── data/
├── docs/
├── notebooks/
├── src/                          (empty — Phase K target)
├── tests/                        98 passing
├── dashboard/
├── img/
├── .pytest_cache/                (gitignored)
├── .model-gpr → ...              (symlink, gitignored)
├── .diligence-extractor → ...    (symlink, gitignored)
├── .renewablesinfo → ...         (symlink, gitignored)
└── .renewablesinfo_org → ...     (symlink, gitignored)
```

### Git history (4 commits at session end)
```bash
$ git log --oneline
<latest>  Add task history doc for v1 Lockport build session
c19f349   Add CLAUDE.md, AGENTS.md, and .cursor/ structure
bdbfa86   Add local symlinks to .gitignore
197f808   Initial commit: gt_models v1 — Lockport gas turbine digital twin
```

### Push verification
```bash
$ git remote -v
origin  git@github.com-work:aamani-ai/GT_Modeling.git (fetch)
origin  git@github.com-work:aamani-ai/GT_Modeling.git (push)

$ ssh -T git@github.com-work 2>&1 | head -1
Hi D-ivyy! You've successfully authenticated, ...
```

---

## §11. Key metrics & headline numbers

### v1 model_card (latest run)
| Mode | Spark margin (9-yr) | LTSA owner-uncovered | **Net P&L (9-yr)** | Annual avg |
|---|---:|---:|---:|---:|
| A | $36.08M | $203.24M | **−$167.16M** | −$18.57M/yr |
| B | $33.15M | $175.62M | **−$142.47M** | −$15.83M/yr |
| C | $33.11M | $175.60M | **−$142.50M** | −$15.83M/yr |

### MOR backtest
- Mode A over-commit: **2.07×** (modeled 1,945 GWh vs MOR 939 GWh over 2021-2025)
- Mode A modeled 2024: 517,929 MWh vs MOR 192,494 MWh (2.69×)
- 1×CC share: 18.1% modeled vs 8.9% MOR
- 2×CC share: 0% modeled vs 26.1% MOR (structural lockout — no per-generator state)
- Cold starts: 14/yr modeled vs ~7/yr MOR

### Steam-only mode (post-addition)
- Modeled days: 218 (6.6% of 9-yr) or 87 (4.8% of 5-yr MOR window)
- MOR days: 460 (25.2% of 5-yr window)
- **Recall**: 18.0% (model catches 1 in 5 real steam-only days)
- **Precision**: 95.4% (when model fires steam-only, it's a real steam-only day)

### Plausible real Lockport economics (after gap closure, per pnl_ledger.md §4)
- Improved Net P&L (Legs 1+2+3 fixed): +$0 to +$20M/yr, central ~+$10M/yr
- Real economic Net P&L (after Fixed OPEX): +$0 to +$8M/yr, central +$2-4M/yr
- Passes survivorship sanity check (modest positive cash flow consistent with 32-year operating history)

### Assumption distribution (Lockport YAMLs)
- Total leaves: 268
- `real_observed`: 31 (11.6%)
- `real_reported`: 160 (59.7%)
- `real_computed`: 22 (8.2%)
- `assumed_industry`: 6 (2.2%)
- `placeholder`: 47 (17.5%)
- `not_applicable`: 2 (0.7%)
- **80% real_* / 17.5% placeholder** (placeholder concentrates in ltsa_terms.yaml)

### Documentation totals
- 5 methodology docs: ~2,240 lines
- 3 guide docs: ~1,395 lines
- 2 ADRs: ~700 lines combined
- README + CLAUDE.md + AGENTS.md: ~670 lines
- **Total methodology + guides + decisions**: ~5,000 lines structured analysis

---

## §12. Verification commands

```bash
# Tests pass
cd /Users/divy/code/work/infrasure_git_codes/gt_models && pytest tests/

# Latest run available
ls /Users/divy/code/work/infrasure_git_codes/gt_models/data/outputs/lockport/runs/
# → notebook4_20260515_093651/ (or newer)

# Model card readable
cat /Users/divy/code/work/infrasure_git_codes/gt_models/data/outputs/lockport/runs/notebook4_*/model_card.md | head -50

# MOR data spine
python3 -c "
import pandas as pd
mor = pd.read_parquet('/Users/divy/code/work/infrasure_git_codes/gt_models/data/paths/lockport/mor_daily.parquet')
print(f'MOR daily: {len(mor)} rows, {mor.date.min()} → {mor.date.max()}')
"

# Git state
cd /Users/divy/code/work/infrasure_git_codes/gt_models && git log --oneline | head -5 && git remote -v

# Notebooks executable
cd /Users/divy/code/work/infrasure_git_codes/gt_models/notebooks
MPLBACKEND=Agg python3 04_full_path_mode_comparison.py 2>&1 | tail -10
```

---

## §13. Insights / lessons

### Plant profile is upstream of everything (v1 evidence)
Direct evidence: adding `steam_only_mode` empirics + `boiler_type="Db"` to YAML, then plumbing into N4, dropped over-commit from 2.22× → 2.07× and improved Net P&L by $36-71M across modes. **One YAML change cascaded through every downstream calculation.** That's the multiplier of getting the profile right.

### For Lockport specifically: input gaps dominate modeling errors
Annual dollar analysis (`pnl_ledger.md §4`):
- Modeling errors (code fixes): +$6-10M/yr
- Input gaps (data extraction): +$10-18M/yr
- **Fixing data is higher-leverage than fixing code** in v1 → v2 transition for this asset

### EIA-923 vs MOR data quality
- EIA-923 reliable for historical (2021-2022 within ±10% of MOR)
- EIA-923 useless for recent (2024-2025): ~0 reported due to federal reporting lag
- MOR is plant-self-reported with no lag — use whenever asset is in diligence-extractor data room

### Perfect-foresight assumption matters
N5 §M.5 quantified: Mode A captures more high-LMP upside (15-pp CF gap at LMP quintile Q4) than MOR's real operator. The 2.07× over-commit is a CEILING — real operator with forecast error would have even bigger gap. Phase L Monte Carlo closes some of this gap.

### Mode A/B/C framework is asset-class-dependent
Doesn't differentiate meaningfully for low-CF assets like Lockport — wear-penalty mechanic activates only near inspection threshold, which is end of 9-yr sim at Lockport's CF. For higher-CF assets (mid-merit / baseload) the framework would have more signal. Different policy frameworks needed for different archetypes (peakers, cogens, etc.) — proposed but not implemented in v1.

### Process: explicit cd in every git bash call
Bash tool's working directory doesn't reliably persist across separate calls. Always `cd /absolute/path && pwd && git ...` in same Bash call. Especially before any destructive remote operation (`git remote add/remove`, `git push`).
