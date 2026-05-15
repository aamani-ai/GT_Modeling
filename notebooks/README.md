# notebooks/ — Validation notebooks (Track 2)

> Where the validation notebooks live. The model is built by writing these first, then refactoring into `src/` in Phase K.

## Naming convention

`NN_<topic>.ipynb` — sequential numbering matches the per-notebook plans in [`../docs/plans/consolidation_plan/notebooks/`](../docs/plans/consolidation_plan/notebooks/).

## Notebooks (planned)

| # | File | Plan | Status |
|---|---|---|---|
| 1 | `01_data_spine_load_validate.ipynb` | [01_data_spine_load_validate.md](../docs/plans/consolidation_plan/notebooks/01_data_spine_load_validate.md) | Pending Phases A–F |
| 2 | `02_one_day_dispatch.ipynb` | TBD (written after Nb 1 runs) | — |
| 3 | `03_daily_loop_feedback.ipynb` | TBD (written after Nb 2 runs) | — |
| 4 *(opt v1)* | `04_full_path_mode_comparison.ipynb` | TBD (written after Nb 3 runs) | — |

## Hygiene

- **`nbstripout`** — outputs are stripped before commit. Reproducibility comes from re-running, not from committed outputs. Install:
  ```bash
  pip install nbstripout
  nbstripout --install
  ```
- **Decision log** — every notebook records its conventions at the top, mirroring the [MOR notebook](https://github.com/Divi-patel/diligence-extractor/blob/main/notebooks/daily_heat_rate_analysis.ipynb) pattern.
- **Stage findings** — every notebook ends with a markdown cell summarizing what was learned and what should change.
- **Pure read** unless explicitly noted — notebooks shouldn't write to `data/` (that's done by the migration phases B–F).

## After Phase K

When Phase K (graduate to `src/`) completes, these notebooks become **reference and onboarding material**, not runtime code. Their numerical results are reproduced by the `src/` modules; rerunning a notebook is a parity check, not a model run.

Do not let notebooks accumulate hidden state past Phase K. Per [consolidation plan §10 anti-patterns](../docs/plans/consolidation_plan.md#10-anti-patterns-ulysses-pact-against-future-self).

## See also

- [consolidation plan §8](../docs/plans/consolidation_plan.md#8-execution-plan) — Phases G–J (notebooks), K (graduate to src/)
- [Notebook-track overview](../docs/plans/consolidation_plan/notebooks/README.md)
- diligence-extractor's notebook methodology: `~/code/personal/diligence-extractor/docs/notebook_methodology.md`
