# Notebook-by-Notebook Plans (Track 2)

> Detailed plans for the notebooks that validate the modeling design end-to-end on real Lockport data, before any code graduates to `src/`. Per parent plan §8.
>
> Parent plan: [`../../consolidation_plan.md`](../../consolidation_plan.md)
> Sub-plan navigation: [`../README.md`](../README.md)

## Why notebooks before `src/`

Three reasons, summarized from parent plan §8:

1. **Force understanding before abstraction.** Writing modules first locks in the wrong seams. A notebook that does one path through the daily loop in linear cells exposes what the actual computation IS before deciding where the boundaries should go.
2. **Surface assumptions at the call site.** Per the assumption-tracking discipline (parent §6), every value carries provenance metadata. In a notebook, each cell can name what's real vs assumed. In `src/`, that metadata gets buried.
3. **The MOR notebook proved the pattern.** `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb` is the working precedent. Extend it; don't replace it.

## The four notebooks

| # | Notebook | Purpose | Becomes (in Phase K refactor) |
|---|---|---|---|
| **1** | **Load + validate the data spine** | Read all YAMLs + paths + tech defaults; cross-check consistency; print assumption-status summary. Surfaces the loader API needs. | `src/io/` |
| **2** | **One day of dispatch — the inner loop** | Pick one representative day; walk hourly through commit, mode choice (1×/2×/3×CC), spark clean vs degraded, cogen constraint, RGGI cost layering. | `src/dispatch/` + `src/cogen/` + `src/markets/` |
| **3** | **Daily loop — state and feedback** | 30-day window with state carry-forward; EOH accumulates, stress accumulators evolve, capacity/HR drift, forced outage check, inspection threshold. Proves the recursive feedback architecture. | `src/engineering/` + `src/dispatch/daily.py` |
| **4** *(optional v1)* | **Full path + Mode A/B/C + LTSA** | One full 10-year path × 3 modes; all seven LTSA cost streams; first model_card. | `src/runners/` + `src/ltsa/` |

## Sequencing

Strictly sequential. Each notebook's plan is written *after* the previous notebook has run and produced findings:

```
Write plan for Nb 1
  → Run Nb 1 (after data spine Phases A-F complete)
    → Findings cell at bottom
      → Write plan for Nb 2 (informed by Nb 1 findings)
        → Run Nb 2
          → Findings
            → Write plan for Nb 3 (informed by Nb 2 findings)
              → ...
```

Why: each notebook teaches us something about the data, the API, or the modeling logic that should shape what the next notebook does. Pre-specifying all four upfront is exactly the failure mode we're avoiding.

## Plan structure (template)

Each notebook plan follows roughly this shape, adapted from the MOR notebook + the user's `notebook_methodology.md`:

1. **Header** — status, prerequisites, plan version, related docs
2. **§1 Purpose** — what this notebook proves
3. **§2 Inputs** — files consumed, with paths
4. **§3 Cell-by-cell sketch** — section-by-section outline (§A schema / §B units / §C completeness / §D conventions / §E cross-source / §F reproducibility, adapted per notebook)
5. **§4 Conventions** — decisions logged at the top of the notebook
6. **§5 Validation checks** — what passes/fails before we move on
7. **§6 What this notebook surfaces** — design questions for future notebooks / phases
8. **§7 What it does NOT cover** — explicit out-of-scope
9. **§8 How this informs the next notebook** — handoff to Notebook N+1

## Output conventions (apply to all notebooks)

- **Notebooks live at**: `notebooks/NN_<topic>.ipynb` (repo root, sibling to `data/`, `src/`, `docs/`)
- **Hygiene**: `nbstripout` configured per `notebook_methodology.md` from diligence-extractor; outputs gitignored
- **Findings cell**: every notebook ends with a Stage findings markdown cell — what we learned, what should change, what's deferred
- **Decision log**: convention/threshold choices recorded at the top of the notebook, replicated in the notebook plan in this folder
- **Assumption metadata access pattern**: notebooks should make assumption status visible in cell output (e.g., when displaying a value, also display its status code + source)
