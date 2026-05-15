# Key Design Decisions — v1 Lockport Build

> One section per decision. Each has the Decision (what we chose) + Rationale (why over alternatives) + Reference (where it's documented in the repo).

---

## 1. Single asset (Lockport only) for v1; multi-asset deferred

**Decision**: v1 models exactly one asset — Lockport Energy Associates (EIA Plant ID 54041). No support for adding a second asset until 2-3 deals are done end-to-end.

**Rationale**: Per consolidation plan §5 D4. Building multi-asset abstraction upfront is premature — better to discover what the abstraction needs by doing 2-3 assets end-to-end, then factor out. v1 keeps everything asset-specific so the patterns can emerge organically.

**Reference**: `docs/plans/consolidation_plan.md` §5 D4; `docs/guides/asset_profile_dimensions.md` §11 "v1 scope".

---

## 2. Five-dimension asset profile structure

**Decision**: Each asset's static profile lives in 5 YAML files under `data/assets/<asset>/`:
- `identity.yaml` — who/where/when
- `engineering.yaml` — physical specs
- `operating_profile.yaml` — empirical behavior (MOR-derived)
- `market_context.yaml` — market connections
- `ltsa_terms.yaml` — OEM contract terms

Plus prose support: `caveats.md` (operational notes) + `provenance.md` (source lineage).

**Rationale**: Considered single mega-YAML and per-section folders. The 5-dimension approach balances:
- Different update cadences (identity rarely changes; LTSA changes when contract renegotiated; operating_profile evolves with MOR data)
- Different data sources (EIA-860 vs MOR vs data-room)
- Different status-maturity (engineering is mostly real_reported; ltsa_terms is mostly placeholder)

Future dimensions (`outage_history`, `offtake_contracts`, `fixed_opex`) designed in `docs/guides/future_dimensions.md` as design specs for when data arrives.

**Reference**: `docs/guides/asset_profile_dimensions.md` §1-§7.

---

## 3. MOR (Monthly Operating Reports) as ground-truth backtest source; NOT EIA-923

**Decision**: For backtest validation, MOR data extracted from `diligence-extractor` repo is the truth source. EIA Form 923 is sidebar-only.

**Rationale**: Verified empirically (Notebook 5 §N): EIA-923 matches MOR within ±10% for older years (2021-2022) but has ~6-12 month federal reporting lag. For 2024-2025, EIA-923 was largely empty while MOR had complete daily data. MOR is plant-self-reported with no lag.

Cost: MOR is only available for assets in the data room. For most plants (in the renewablesinfo_org platform with 15K+ assets), EIA-923 is the only option — and it's fine for historical work.

**Reference**: `notebooks/05_model_vs_actual.ipynb` §N; `docs/methodology/extra/backtest_findings.md` §3.2.

---

## 4. Henry Hub for gas (ADR-001), not Algonquin basis

**Decision**: v1 uses Henry Hub spot price directly as the delivered gas cost benchmark. Algonquin Citygate basis (the real delivery point for Western NY plants like Lockport) deferred to v2.

**Rationale**: Algonquin Citygate data is sparse (2014-2017 only in our sources); Henry Hub has 1997-2026 coverage. For a 9-year backtest 2017-2025, Henry Hub is the only continuous series. Real Lockport pays Algonquin basis (typically +$2-5/MMBtu winter), so v1 understates fuel cost slightly. v2 should add basis modeling using Tennessee Gas Pipeline data (the actual pipeline serving Lockport per EIA-860).

**Reference**: `docs/decisions/001-gas-hub-treatment-v1.md`; `data/assets/lockport/market_context.yaml.gas_market.v1_modeling_choice`.

---

## 5. Three-bucket calibration inventory (ADR-002)

**Decision**: Every calibrated value in the model is tagged as one of three buckets:
- **Bucket A** — Lockport-specific (`real_*` status): mode heat rates from MOR, ambient derates from EIA-860, cold-start gas from MOR
- **Bucket B** — Generic F-class defaults (`assumed_*` status): Athens-prototype state-evolution constants (creep/fatigue rates, TBC Weibull, HRSG age scaling)
- **Bucket C** — Placeholder pending data room (`placeholder` status): all LTSA contract values

**Rationale**: Distinguishes "this value is real for this plant" from "this value is a class default that may not fit" from "this value is a typed guess pending data room." Drives Phase L Monte Carlo design — Bucket B constants are the prime candidates for sensitivity sweeps; Bucket C waits for data room.

ADR-002 Correction 1 also applied: MOR-observed cold-start warming gas (2,537 MMBtu/cold start, Lockport-specific) replaces prototype default; wired into N3 fuel cost.

**Reference**: `docs/decisions/002-lockport-specific-vs-generic-calibration.md`; `notebooks/03_daily_loop_feedback.py` constants block.

---

## 6. Steam-only mode added to N4 (correcting prior dispatch_mechanics.md §6 claim)

**Decision**: N4 now has a steam-only branch in must-run logic. On must-run days where peak LMP × 3xCC HR can't clear break-even, plant runs steam-only for the day (0 MWh, 0 EOH wear, only gas + RGGI cost for ~871 MMBtu/day per MOR median).

**Rationale**: MOR data revealed 460 days (25.2% of 2021-2025) with 0 MWh + non-zero gas + non-zero DHTS — steam-only operation via duct burner. EIA-860 confirmed mechanism: GEN4 boiler ID 4 type = "Db" (Duct Burner), CTs can bypass HRSG. v1 originally forced 1×CC dispatch on must-run uneconomic days, over-counting MWh + EOH wear + fuel cost.

After implementation: over-commit dropped from 2.22× to 2.07× vs MOR; Mode A Net P&L improved +$35.9M/9yr; Mode B improved +$70.6M (avoided MI trigger).

Trade-off: trigger is conservative (peak LMP basis) — catches only 18% of MOR's real steam-only days. Refinement to avg-LMP basis flagged as future work.

**Reference**: `docs/methodology/dispatch_mechanics.md` §6 (corrected); `docs/methodology/extra/backtest_findings.md` §3.4, §3.6; `notebooks/04_full_path_mode_comparison.py` `run_mode()` steam-only branch.

---

## 7. Annual as primary unit, not 9-year totals

**Decision**: All dollar magnitudes in docs are reported per year first; 9-year totals are derivations. The model_card structure should lead with annual averages.

**Rationale**: Annual is the natural unit for a power plant — budgets, contracts, MOR filings, LTSA escalation, RGGI auctions, ICAP commitments are all annual. 9-year totals can hide year-to-year variance (e.g., a $14M MI in one year of nine). The plausible-magnitude logic also naturally works annually.

**Reference**: `docs/methodology/gaps_and_priorities.md` §7; `docs/methodology/pnl_ledger.md` §1.1 (all tables annual-primary).

---

## 8. Survivorship-bias sanity check on Net P&L reconciliation

**Decision**: Any reconciliation of "real Lockport Net P&L" must pass the constraint that the plant has been operating continuously since 1992. Sustained-negative annual cash flow over decades isn't consistent with continued operation.

**Rationale**: User correctly pushed back on initial reconciliation that put Real Economic Net P&L at −$15 to $0M/yr. Recalibrated to +$0 to +$8M/yr (central tendency +$2-4M/yr) with explicit survivorship constraint. Without this anchor, range estimates can be too pessimistic by compounding worst-case assumptions across legs.

**Reference**: `docs/methodology/pnl_ledger.md` §4.1 (the survivorship constraint).

---

## 9. Five-doc methodology + extra/ subfolder for findings

**Decision**: Methodology folder has 5 main docs (`pnl_ledger`, `architecture`, `dispatch_mechanics`, `gaps_and_priorities`, `glossary`) at top level. Findings docs that don't belong in the main flow live in `methodology/extra/` (currently `backtest_findings.md`).

**Rationale**: User directed: "If we have backtesting results in methodology, that doesn't look good — we don't want to clutter the main files." The `extra/` pattern keeps the main methodology focused on architecture/conventions/reading-order, while still letting backtest findings live near methodology.

**Reference**: `docs/methodology/` structure; `docs/methodology/extra/backtest_findings.md` header.

---

## 10. Bracketing plot uses monthly view, not cumulative

**Decision**: N5 §E.5's Mode A | Mode C | MOR comparison uses monthly line plot + annual bars. Cumulative-over-time view removed because it compounds errors.

**Rationale**: User insight: cumulative compounds errors and obscures the real signal (band width vs absolute bias). Monthly view shows both the band's collapse (4 of 5 years have 0 GWh width) AND the level shift (MOR consistently below band) cleanly. The cumulative view was hiding seasonality.

**Reference**: `notebooks/05_model_vs_actual.py` §E.5 (current version).

---

## 11. Plant archetype framework proposed but not implemented in YAML

**Decision**: Eight-archetype taxonomy (peaker / mid_merit / baseload / cogen / qf_purpa / rmr / battery / hybrid) documented as the "single most useful prior" for asset modeling. Field design proposed for `identity.yaml.plant.archetype` block but NOT added to Lockport's YAML in v1.

**Rationale**: Per user direction: "right now we don't need to add it in our Lockport case. We will go back to the drawing board with the instance of the information we already have in a data room." Framework documented; implementation waits until v2 or until a second asset onboards (multi-asset abstraction shouldn't happen with sample size of 1).

**Reference**: `docs/guides/asset_profile_dimensions.md` §13.

---

## 12. Future dimensions documented as design stubs, not created as YAMLs

**Decision**: Three anticipated YAML files (`outage_history`, `offtake_contracts`, `fixed_opex`) have full design specs in `docs/guides/future_dimensions.md`. Actual YAML files NOT created until real data exists.

**Rationale**: "Don't create empty/placeholder YAMLs for these. Wait until real data exists." Pre-design has value (location, schema, downstream consumption pre-decided when data arrives) but premature implementation creates technical debt.

**Reference**: `docs/guides/future_dimensions.md` §1.

---

## 13. Multi-account SSH for repo separation

**Decision**: This repo (`aamani-ai/GT_Modeling`, work organization) uses `git@github.com-work` SSH alias (D-ivyy work account). Personal repos (`renewablesinfo_org`) continue using `git@github.com-personal` alias (Divi-patel).

**Rationale**: User has 3 GitHub accounts with separate SSH keys. Default `git@github.com` resolves to Divi-patel (personal); pushing aamani-ai/GT_Modeling content from personal account would mis-attribute the push. Verified via `ssh -T git@github.com-X 2>&1 | head -1` before push: work alias = `Hi D-ivyy!`, personal = `Hi Divi-patel!`.

**Reference**: `CLAUDE.md` "GitHub setup (multi-account)" section; `AGENTS.md` "Multi-account SSH" table.

---

## 14. Local cross-repo symlinks (gitignored)

**Decision**: Repo root contains 4 dot-prefixed symlinks pointing to related local repos:
- `.model-gpr` → model-gpr (price forecaster)
- `.diligence-extractor` → diligence-extractor (data-room raw)
- `.renewablesinfo` → renewablesinfo (lab)
- `.renewablesinfo_org` → renewablesinfo_org (platform)

Added to `.gitignore` — local-machine convenience, not part of the modeling repo.

**Rationale**: Per user request: "I know it not gonna be in github but locally doing that help in management a lot." Hidden from default `ls`, excluded from git. Lets `cd .renewablesinfo_org/` etc. from inside `gt_models/`.

**Reference**: `gt_models/.gitignore` (symlinks block); `AGENTS.md` "Cross-repo navigation" section.

---

## 15. Task-history pattern for context continuity

**Decision**: Task documentation pattern adopted from `renewablesinfo_org`'s `.cursor/commands/PROMPT_CREATE_TASK_DOCS.md`. Each multi-day workstream produces 4 docs (`task_context.md` / `decisions.md` / `notes.md` / `handoff.md`) in `docs/extra/tasks_history/YYYY-MM-DD__area__short-slug/`.

**Rationale**: Per user direction at session end: "let's now have this .claude .cursor and those kind of things in the GT_Modeling folder as well... so whenever I next time interact with you in a new chat from the GT models folder itself, I can give this as a reference to get the context ready." Task docs serve as conversation-continuity scaffolding.

**Reference**: `.cursor/commands/PROMPT_CREATE_TASK_DOCS.md`; THIS task folder.

---

## 16. The bracketing framework + low-CF mismatch noted but not redesigned in v1

**Decision**: Mode A/B/C wear-penalty framework retained as-is in v1 despite Lockport's CF profile making it produce zero band-width for 80% of the run.

**Rationale**: User direction: "leave the current framework in v1, but DOCUMENT this limitation clearly." Changing the framework asset-by-asset risks inconsistency. The right move is to make this a v2 design conversation about archetype-tagged policy frameworks (different policy axes for low-CF cogens vs mid-merit CCGTs). Documented in `dispatch_mechanics.md` §3 + `backtest_findings.md` §3.7 (newly added).

**Reference**: `docs/methodology/extra/backtest_findings.md` §3.7; `docs/guides/asset_profile_dimensions.md` §13 (archetype framework).
