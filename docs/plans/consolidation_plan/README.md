# Consolidation Plan — Detailed Sub-Plans

> Sibling subfolder to [`../consolidation_plan.md`](../consolidation_plan.md). Contains the detailed per-phase execution plans referenced by §8 of the parent doc.

The parent `consolidation_plan.md` is the architectural anchor — read it first to understand the four-repo system, the five locked decisions, the folder architecture, the assumption-tracking discipline, and the high-level phase sequence.

This subfolder holds the **execution-level detail** for the phases that earn their own dedicated plan:

```
consolidation_plan/
├── README.md           (this file — navigation)
└── notebooks/          (Track 2 — notebook-by-notebook plans)
    ├── README.md
    ├── 01_data_spine_load_validate.md
    ├── 02_one_day_dispatch.md         (TBD — written after Nb 1 runs)
    ├── 03_daily_loop_feedback.md      (TBD — written after Nb 2 runs)
    └── 04_full_path_mode_comparison.md (TBD — written after Nb 3 runs)
```

## Why sub-plans get written incrementally, not upfront

Per the parent plan's §8 sequencing principle and §10 anti-patterns: each notebook's plan is informed by what the previous notebook actually surfaces. Pre-specifying Notebook 3 before Notebook 1 has run is exactly the design-in-isolation failure mode we're avoiding.

The pattern:

1. Write the plan for Notebook N
2. Run Notebook N (after the parent plan's earlier-phase prerequisites are met)
3. Document findings at the bottom of Notebook N (Stage 1 findings pattern from the MOR notebook)
4. Use those findings to write the plan for Notebook N+1
5. Repeat

This is why only `01_data_spine_load_validate.md` exists today. The others will appear in order.

## Naming convention

`NN_<topic>.md` where NN matches the notebook number (`notebooks/NN_<topic>.ipynb` in the eventual `notebooks/` folder at the repo root). One-to-one mapping between plan and notebook.

## Other sub-plans (future)

If Phase K (graduate to `src/`) or any other phase grows beyond what `consolidation_plan.md` can comfortably hold, it earns a sub-plan here. Possible future sub-plans:

- `graduation_to_src.md` — written when Track 2 finishes
- `ltsa_extraction_handoff.md` — when data room LTSA extraction completes and we replace placeholders
- `data_spine_schema_evolution.md` — if the YAML schemas need a major version bump

None of these get written speculatively. They earn their place when there's a concrete reason.
