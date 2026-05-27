"""src/forward — the forward scenario engine for gt_models.

Generates conditioned forward scenario paths (weather + price + gas) from the local
data spine and runs the gt_engine over them to produce a P10/P50/P90 view. See
docs/plans/forward_engine_plan.md.

Modules:
  select.py  — temperature-conditioned continuous-window analog selection (ported)
  build.py   — (next) rebase selected windows to the target horizon; assemble paths
  run.py     — (next) run gt_engine.run_path over each scenario; aggregate quantiles
"""

from .select import select, SelectionResult

__all__ = ["select", "SelectionResult"]
