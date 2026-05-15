# dashboard/ — Future scope (placeholder)

> Reserved folder for the future visualization / UI layer over model outputs. **Not in v1 build.**

## Status

🅿️ **Future scope.** Will be designed once there's a working Lockport simulation producing real outputs (Phase L of the consolidation plan) and we know what views the deal team actually wants.

## Why a placeholder now

Two reasons:

1. **Reserved naming** — establishing the folder name early prevents future "where should the dashboard live?" relitigation. It's a sibling to `docs/`, `data/`, `src/`, and `notebooks/` — visualization is its own concern, not a sub-concern of any of those.
2. **Clear non-scope** — by writing this README, anyone walking into gt_models understands the dashboard doesn't exist yet and isn't blocking other work.

## What it will contain (eventually)

Open. Possible candidates when the time comes:

- Streamlit or Dash app for interactive exploration of model outputs
- Plotly-based static reports
- A web app that consumes the `data/outputs/<asset>/runs/<run_id>/` bundles
- Mode A/B/C trade-off visualizations
- P10/P50/P90 distributional views
- LTSA cost stream decomposition charts
- Assumption-status drill-downs from the model_card

These are speculations. Real design comes when there's a deal team asking specific questions of specific outputs.

## See also

- [consolidation plan §4.4](../docs/plans/consolidation_plan.md#44-dashboard--future-scope-new-placeholder-only)
- [consolidation plan §10](../docs/plans/consolidation_plan.md#10-anti-patterns-ulysses-pact-against-future-self) — anti-pattern: "Build the dashboard before there's a working model with outputs"
