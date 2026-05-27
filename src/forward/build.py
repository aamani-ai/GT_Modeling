"""Forward scenario build — turn selected windows into engine-runnable path specs.

v1 design (per forward_engine_plan.md, raw historical levels, no anchoring):
each eligible Apr->Mar window is run over its NATIVE historical dates as a fresh
1-year scenario. Because the engine computes aging relative to each run's own
sim_start and a fresh plant never hits an EOH inspection threshold within one year,
the per-window runs are directly comparable WITHOUT hour-by-hour rebasing onto a
common 2026 calendar. (Rebasing onto a shared future calendar is only needed for
fan-chart presentation and forward-price anchoring — both deferred.)

So a "scenario path" here is a lightweight spec: which historical window, its Apr->Mar
span, and its selection probability. The hourly price/gas/weather values are read by the
engine from the local data spine at run time (src/forward/run.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make src/ importable
from forward.select import SelectionResult, select, DEFAULT_BASIS  # noqa: E402

TZ = "US/Eastern"


def build_scenarios(selection: SelectionResult | None = None, basis: str = DEFAULT_BASIS,
                    asset: str = "lockport") -> pd.DataFrame:
    """Return one row per eligible window: the engine-runnable scenario spec.

    Columns: path_id, source_window_id, source_start_year, probability,
             sim_start, sim_end  (tz-aware Eastern; sim_end exclusive).
    """
    if selection is None:
        selection = select(basis=basis, asset=asset)
    rows = []
    for i, w in enumerate(selection.window_weights.itertuples(index=False), start=1):
        y = int(w.source_start_year)
        rows.append({
            "path_id": i,
            "source_window_id": w.window_id,
            "source_start_year": y,
            "probability": float(w.probability),
            "sim_start": pd.Timestamp(f"{y}-04-01", tz=TZ),
            "sim_end": pd.Timestamp(f"{y+1}-04-01", tz=TZ),   # exclusive
        })
    df = pd.DataFrame(rows)
    # Probabilities come from the eligible set already normalized; re-normalize defensively.
    df["probability"] = df["probability"] / df["probability"].sum()
    return df


if __name__ == "__main__":
    s = build_scenarios()
    print(f"{len(s)} scenario paths (Apr->Mar windows):")
    print(s[["path_id", "source_window_id", "probability", "sim_start", "sim_end"]].to_string(index=False))
