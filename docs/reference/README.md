# docs/reference/ — Digests of upstream work

> Digests of the relevant work happening in the other three repos. Read these for context; the canonical sources live elsewhere.

## Why digests, not links

Upstream repos (renewablesinfo, diligence-extractor, model-gpr) have their own design docs, audit trails, and methodology notes. We don't duplicate those — but we *do* need a single place in gt_models where a reader can understand the upstream context without chasing files across four repos.

A digest:
- Summarizes the key methodology decisions from the upstream work
- States which findings are load-bearing for our model
- Links back to the upstream canonical sources for the full detail
- Is frozen in time — refreshed deliberately when upstream materially updates

## Planned files

| File | Phase | What it digests |
|---|---|---|
| `tech_class_dispatch_params_summary.md` | B | renewablesinfo dispatch_params lab pass: methodology decisions, the PJM-no-defaults finding, confidence-tier distribution, what Lockport gets from the lookup |
| `public_data_inputs_summary.md` | C | renewablesinfo public-data brief on Lockport: what fields exist, what gaps the public data has |
| `diligence_data_inventory_summary.md` | D / F | diligence-extractor tabular data inventory: what's in the data room, what was extracted, what's still pending |

## Status

🟡 **Empty in v1 until corresponding phases.**

## Refresh discipline

A digest is refreshed when:
- The upstream source materially updates (e.g., dispatch_params lab pass v2)
- A new methodology decision is made that affects our model
- A new finding contradicts a previous claim (like the "Lockport mothballed?" correction from the MOR notebook)

Refresh = update the digest + bump its date stamp + commit. The upstream source doesn't need to be edited.

## Cross-references — where the canonical sources live

| Topic | Canonical location |
|---|---|
| Tech-class dispatch params methodology + AUDIT.md | `~/code/personal/renewablesinfo/integration/dispatch_params/` |
| renewablesinfo dispatch_operating_params design doc | `~/code/personal/renewablesinfo_org/docs/design/dispatch_operating_params.md` |
| Lockport public-data brief | `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_data_brief.md` |
| Lockport equipment profile (internal version) | `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_equipment_profile.md` |
| Dispatch input audit (fleet-wide) | `~/code/personal/renewablesinfo_org/docs/extra/dispatch_modeling/01_input_audit.md` |
| diligence-extractor framework north-star | `~/code/personal/diligence-extractor/docs/plans/framework_north_star.md` |
| diligence-extractor tabular data inventory | `~/code/personal/diligence-extractor/docs/tabular_data_inventory.md` |
| diligence-extractor MOR notebook | `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb` |
| model-gpr Step 1 plan | `~/code/work/infrasure_git_codes/model-gpr/local_docs/plans/price_forwards/01_phase1_forward_adjusted_forecast.md` |
| model-gpr Lockport data | `~/code/work/infrasure_git_codes/model-gpr/local_data/lockport_energy_associates_lp/` |

## See also

- [consolidation plan §1](../plans/consolidation_plan.md#1-the-four-repo-system) — four-repo system map
- [consolidation plan §11](../plans/consolidation_plan.md#11-glossary--cross-references) — full cross-reference index
