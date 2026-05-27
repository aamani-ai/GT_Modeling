"""Regression gate for the extracted engine (src/gt_engine).

Locks the byte-identical Mode-A headline numbers the engine produced at extraction
time (2026-05-27, post ADR-006/007). If anyone edits the engine and these move, this
fails — which is what makes it safe to keep the engine as the single source of truth
while notebook 4 (the historical driver) is graduated separately.

Runs one mode (~5s) rather than all three to keep the suite fast.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# Known-good Mode A headline at extraction time (seed=42, full 2017-2025 replay).
EXPECTED = {
    "spark_margin_usd": 33_586_821.986678,
    "ltsa_owner_usd": 179_789_296.0,   # sum of the 8 LTSA streams
    "fired_hours": 11_838,
    "inspections": 1,
    "forced_outages": 35,
}
LTSA_KEYS = [
    "fixed_fee_cum", "eoh_reserve_cum", "ci_owner_cum", "mi_owner_cum",
    "overage_cum", "avail_penalty_cum", "hr_penalty_cum", "outage_forced_cum",
]


@pytest.fixture(scope="module")
def mode_a():
    from gt_engine import run_mode
    return run_mode("A", seed=42)


def test_spark_margin_unchanged(mode_a):
    spark = mode_a["daily"]["margin_degraded"].sum()
    assert spark == pytest.approx(EXPECTED["spark_margin_usd"], rel=1e-9)


def test_ltsa_owner_unchanged(mode_a):
    ltsa = sum(mode_a["final_ltsa"][k] for k in LTSA_KEYS)
    assert ltsa == pytest.approx(EXPECTED["ltsa_owner_usd"], rel=1e-6)


def test_fired_hours_unchanged(mode_a):
    assert int(mode_a["daily"]["fired_hours"].sum()) == EXPECTED["fired_hours"]


def test_inspection_count_unchanged(mode_a):
    n = 0 if mode_a["inspections"].empty else len(mode_a["inspections"])
    assert n == EXPECTED["inspections"]


def test_forced_outage_count_unchanged(mode_a):
    n = 0 if mode_a["forced_outages"].empty else len(mode_a["forced_outages"])
    assert n == EXPECTED["forced_outages"]


def test_run_path_matches_run_mode(mode_a):
    """run_mode is just run_path over the historical windows -> identical result."""
    from gt_engine import run_path
    import gt_engine.engine as eng
    via_path = run_path("A", 42, eng.sim_dates, eng.sim_start, eng.sim_end,
                        eng.lmp_window, eng.weather_window, eng.henry)
    assert via_path["daily"]["margin_degraded"].sum() == pytest.approx(
        mode_a["daily"]["margin_degraded"].sum(), rel=1e-12)
