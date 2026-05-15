# Lockport — Asset Profile Provenance

> Tracks where each YAML / markdown file in this folder came from and when it was last refreshed. Per consolidation plan §6 + §7.

## Last refresh: 2026-05-14

| File | Created | Source(s) | Notes |
|---|---|---|---|
| `identity.yaml` | 2026-05-14 (Phase C) | EIA-860M Jan 2026, EIA-860 schedules 1, 2, 3_1, 4, 6_2 Y2024, EPA eGRID 2023 rev2, EIA Atlas, NYISO node_crosswalk (lab-built) | Digested from public-data brief at `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_data_brief.md` §1 + §"At a glance". All values cited to original EIA-860 schedule, not to the brief itself. |
| `engineering.yaml` | 2026-05-14 (Phase C) | EIA-860 schedules 3_1, 3_5, 6_2 Y2024, derived totals from per-generator data | Public-data brief §3–§6. Per-generator data with full provenance. CHP flag, dual-fuel, ambient sensitivity, multi-mode dispatch capability. |
| `market_context.yaml` | 2026-05-14 (Phase C) | EIA-860 schedule 2 Y2024, NYISO node_crosswalk (lab-built), EPA eGRID 2023 rev2, Step 1 plan §"Gas Price Path Construction" | Public-data brief §7. NYISO nodes (PTID 23791 for CTs, PTID 323769 for ST), Algonquin Citygate gas hub, NYUP eGRID subregion, RGGI exposure flag. |
| `operating_profile.yaml` | 2026-05-14 (Phase D) | diligence-extractor MOR notebook Stage 2 final-summary table + Stage 1 findings | Written from `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb`. Mode-segmented heat rate (3×CC_full 8,901; 2×CC 9,598; 1×CC 10,424 Btu/kWh), cold-start gas (35 warming days, 88,785 MMBtu over 5 yr), DHTS host-steam patterns, 2024 corrected generation (192,494 MWh). Cross-validation: 2023 MOR HR (9,293) reproduces eGRID 2023 placeholder (9,228) within <1%. |
| `ltsa_terms.yaml` | 2026-05-14 (Phase F) | Athens prototype `[ASSUME]` defaults (placeholder until data room extraction) | All values flagged `status: placeholder`. Data room file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` is the eventual source. Covers the 7 LTSA cost streams: fixed_fee, eoh_reserve, inspection_ci, inspection_mi, start_overage, availability_penalty, hr_penalty, forced_outage_coverage. |
| `caveats.md` | 2026-05-14 (Phase C) | Composition of public-data brief §6 + diligence-extractor MOR Stage 1 findings + dispatch_params lab methodology | Read first before writing dispatch code. Documents the operational status correction, cogen markup, multi-mode dispatch, dual-fuel switching, EIA cold-start clustering, steam-host constraint, ambient sensitivity, vintage-specific behavior, merchant cogen status. |
| `provenance.md` | 2026-05-14 (Phase C) | This file | Updated whenever any artifact in this folder is refreshed. |

## Canonical source paths (where to look for refreshes)

| Type | Path |
|---|---|
| renewablesinfo public-data brief | `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_data_brief.md` |
| renewablesinfo equipment profile (internal working version) | `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_equipment_profile.md` |
| diligence-extractor MOR notebook | `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb` |
| diligence-extractor tabular inventory | `~/code/personal/diligence-extractor/docs/tabular_data_inventory.md` |
| EIA-860 raw (public) | `~/code/personal/renewablesinfo_org/data/sources/eia/eia8602024/` |
| EPA eGRID raw (public) | `~/code/personal/renewablesinfo_org/data/sources/epa_egrid/` |
| NYISO node_crosswalk | `~/code/personal/renewablesinfo_org/data/dimensions/pricing/node_crosswalk.parquet` |

## Refresh procedure

When upstream sources update:

1. Identify which fields are affected (e.g., EIA-860 annual release in early Q2 updates capacity, status, ownership).
2. Update the affected YAML files leaf-by-leaf. Preserve the `status` / `source` / `caveat` metadata.
3. Update this `provenance.md` table's "Created / refreshed" column.
4. If the change is material (a value moved by >10% or a flag flipped), add a note to `caveats.md` if the change has modeling implications.
5. Commit.

Refresh is a deliberate human act, not automated synchronization. Per consolidation plan §5 D3.

## Cross-references

- Consolidation plan §6 (assumption tracking discipline): [`../../../docs/plans/consolidation_plan.md`](../../../docs/plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle)
- Consolidation plan §7 (migration mapping): [`../../../docs/plans/consolidation_plan.md`](../../../docs/plans/consolidation_plan.md#7-migration-mapping)
- Status taxonomy: [`../../../docs/assumptions/status_taxonomy.md`](../../../docs/assumptions/status_taxonomy.md)
- Asset folder convention: [`../README.md`](../README.md)
