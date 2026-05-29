"""DEPRECATED — superseded by build_monthly_forecast_panel.py.

The original implementation distributed real annual run_forward endpoints over
an idealized NYISO Zone F CCGT seasonality and shipped climatology / forward-
curve-shape arrays for temperature, LMP, and gas. That is illustrative shape,
not real model output, and it caused Section 01 of the dashboard to mis-label
itself.

The replacement (`build_monthly_forecast_panel.py`) keeps the per-path daily
series from `run_forward(..., return_paths=True)` and aggregates them to real
monthly P10/P50/P90 envelopes — mirroring notebook 06 §5 exactly. It also
loads the actual SEAS5 ensemble JSON for the temperature panel.

Running this file now raises an error to prevent accidental regeneration of
the illustrative artifact.
"""

import sys


def _refuse(*_args, **_kwargs):
    msg = (
        "build_monthly_trajectories.py is deprecated.\n"
        "The illustrative monthly-seasonality builder has been removed.\n"
        "Run apps/gt-digital-twin/scripts/build_monthly_forecast_panel.py\n"
        "to produce the real monthly_forecast_panel.json that Section 01 now consumes."
    )
    print(msg, file=sys.stderr)
    raise SystemExit(2)


# Preserve callable names so anything that imported this module surfaces the
# error immediately instead of silently no-op'ing.
build = _refuse
main = _refuse


if __name__ == "__main__":
    _refuse()
