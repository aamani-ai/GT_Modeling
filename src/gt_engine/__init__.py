"""gt_engine — the importable Lockport dispatch / wear / LTSA engine.

Extracted from notebooks/04_full_path_mode_comparison.py (Phase K / forward-engine
foundation; design in docs/plans/forward_engine_plan.md, basis decision in ADR-008).
The engine logic is verbatim from N4; the only
structural change is that the daily loop is exposed as `run_path(...)` taking an
injected market path, with `run_mode(...)` as a historical-replay wrapper over the
module-level historical windows.

Both the historical notebook and the forward scenario runner (src/forward) call the
same engine here, so there is one source of truth for dispatch + wear + LTSA.
"""

from .engine import run_mode, run_path, PlantState, init_state, init_ltsa_state

__all__ = ["run_mode", "run_path", "PlantState", "init_state", "init_ltsa_state"]
