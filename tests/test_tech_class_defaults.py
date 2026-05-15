"""Unit-range smoke tests for the tech-class dispatch parameters lookup.

Validates that data/tech_class_defaults/dispatch_params_lookup.parquet is
present, structurally sound, internally consistent, and contains the rows
that apply to Lockport (the v1 asset).

Per consolidation plan §8 Phase B acceptance criterion. Discipline mirrors
the renewablesinfo dispatch_params lab pass tests.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LOOKUP_PATH = REPO_ROOT / "data" / "tech_class_defaults" / "dispatch_params_lookup.parquet"

# Expected schema columns (35 total per parent plan §7)
EXPECTED_COLUMNS = {
    # Keys
    "prime_mover_code",
    "vintage_class",
    "aero_derivative",
    # VOM
    "vom_per_mwh",
    "vom_per_mwh_low",
    "vom_per_mwh_high",
    "vom_usd_year",
    # Startup cost (3 start types × 3 percentiles)
    "startup_cost_cold_p50_per_mw",
    "startup_cost_cold_p25_per_mw",
    "startup_cost_cold_p75_per_mw",
    "startup_cost_warm_p50_per_mw",
    "startup_cost_warm_p25_per_mw",
    "startup_cost_warm_p75_per_mw",
    "startup_cost_hot_p50_per_mw",
    "startup_cost_hot_p25_per_mw",
    "startup_cost_hot_p75_per_mw",
    "startup_cost_usd_year",
    # Startup fuel
    "startup_fuel_cold_mmbtu_per_mw",
    "startup_fuel_warm_mmbtu_per_mw",
    "startup_fuel_hot_mmbtu_per_mw",
    # Min up / down
    "min_up_hr",
    "min_down_hr",
    # Start times
    "hot_start_time_hr",
    "warm_start_time_hr",
    "cold_start_time_hr",
    # Ramp
    "ramp_rate_pct_per_min",
    # Confidence (6 parameter groups)
    "confidence_vom",
    "confidence_startup_cost",
    "confidence_startup_fuel",
    "confidence_min_up_down",
    "confidence_start_time",
    "confidence_ramp",
    # Provenance
    "primary_source_label",
    "assumption_vintage",
    "notes",
}

EXPECTED_PRIME_MOVERS = {"CT", "CA", "CC", "GT"}
EXPECTED_VINTAGE_CLASSES = {"<2000", "2000-2010", "2010-2020", "2020+"}
VALID_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}


@pytest.fixture(scope="module")
def lookup() -> pd.DataFrame:
    """Load the dispatch_params lookup parquet once per test module."""
    assert LOOKUP_PATH.exists(), (
        f"Lookup not found at {LOOKUP_PATH}. "
        "Run Phase B of the consolidation plan to populate."
    )
    return pd.read_parquet(LOOKUP_PATH)


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------

def test_lookup_loads(lookup: pd.DataFrame) -> None:
    """Lookup parquet exists and loads without error."""
    assert isinstance(lookup, pd.DataFrame)


def test_row_count(lookup: pd.DataFrame) -> None:
    """20 rows expected: 4 prime movers × 4 vintage classes, with aero-derivative split for GT."""
    assert len(lookup) == 20, f"Expected 20 rows, got {len(lookup)}"


def test_schema_columns(lookup: pd.DataFrame) -> None:
    """All 35 expected columns present, no extras."""
    actual = set(lookup.columns)
    missing = EXPECTED_COLUMNS - actual
    extra = actual - EXPECTED_COLUMNS
    assert not missing, f"Missing columns: {missing}"
    assert not extra, f"Unexpected columns: {extra}"


def test_key_uniqueness(lookup: pd.DataFrame) -> None:
    """Each (prime_mover, vintage_class, aero_derivative) triple is unique."""
    duplicates = lookup.duplicated(subset=["prime_mover_code", "vintage_class", "aero_derivative"])
    assert not duplicates.any(), (
        f"Duplicate key rows: "
        f"{lookup.loc[duplicates, ['prime_mover_code', 'vintage_class', 'aero_derivative']].to_dict('records')}"
    )


def test_prime_movers_complete(lookup: pd.DataFrame) -> None:
    """All 4 expected prime movers present."""
    assert set(lookup.prime_mover_code.unique()) == EXPECTED_PRIME_MOVERS


def test_vintage_classes_complete(lookup: pd.DataFrame) -> None:
    """All 4 expected vintage classes present."""
    assert set(lookup.vintage_class.unique()) == EXPECTED_VINTAGE_CLASSES


def test_aero_only_for_gt(lookup: pd.DataFrame) -> None:
    """aero_derivative=True only appears on GT rows."""
    aero_rows = lookup[lookup.aero_derivative == True]
    assert all(aero_rows.prime_mover_code == "GT"), (
        "aero_derivative=True must only appear with prime_mover_code=GT"
    )


# ---------------------------------------------------------------------------
# Confidence-tier tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("col", [
    "confidence_vom",
    "confidence_startup_cost",
    "confidence_startup_fuel",
    "confidence_min_up_down",
    "confidence_start_time",
    "confidence_ramp",
])
def test_confidence_values_valid(lookup: pd.DataFrame, col: str) -> None:
    """All confidence values are HIGH / MEDIUM / LOW."""
    actual_values = set(lookup[col].dropna().unique())
    invalid = actual_values - VALID_CONFIDENCE_LEVELS
    assert not invalid, f"{col} has invalid confidence values: {invalid}"


def test_min_up_down_all_low_confidence(lookup: pd.DataFrame) -> None:
    """Per lab pass Decision 5: min_up/min_down has no public source — all LOW confidence."""
    assert (lookup.confidence_min_up_down == "LOW").all(), (
        "All min_up_down values must be LOW confidence "
        "(no public source carries these values)"
    )


def test_startup_fuel_all_high_confidence(lookup: pd.DataFrame) -> None:
    """Startup fuel from Kumar 2012 Tbl 1-3 is HIGH confidence across all rows."""
    assert (lookup.confidence_startup_fuel == "HIGH").all()


# ---------------------------------------------------------------------------
# Unit-range tests (catches transcription / unit-misinterpretation bugs)
# ---------------------------------------------------------------------------

def test_vom_range(lookup: pd.DataFrame) -> None:
    """VOM in [0, 30] $/MWh — typical CCGT range."""
    assert (lookup.vom_per_mwh >= 0).all()
    assert (lookup.vom_per_mwh <= 30).all(), (
        f"vom_per_mwh exceeds 30 $/MWh in rows: "
        f"{lookup[lookup.vom_per_mwh > 30][['prime_mover_code', 'vintage_class', 'vom_per_mwh']].to_dict('records')}"
    )


@pytest.mark.parametrize("col", [
    "startup_cost_cold_p50_per_mw",
    "startup_cost_warm_p50_per_mw",
    "startup_cost_hot_p50_per_mw",
])
def test_startup_cost_range(lookup: pd.DataFrame, col: str) -> None:
    """Startup C&M cost in [0, 200] $/MW — Kumar 2012 envelope."""
    assert (lookup[col] >= 0).all()
    assert (lookup[col] <= 200).all(), f"{col} exceeds 200 $/MW envelope"


@pytest.mark.parametrize("col", [
    "startup_fuel_cold_mmbtu_per_mw",
    "startup_fuel_warm_mmbtu_per_mw",
    "startup_fuel_hot_mmbtu_per_mw",
])
def test_startup_fuel_range(lookup: pd.DataFrame, col: str) -> None:
    """Startup fuel in [0, 5] MMBtu/MW — Kumar 2012 envelope (aero up to 1.53)."""
    assert (lookup[col] >= 0).all()
    assert (lookup[col] <= 5).all(), f"{col} exceeds 5 MMBtu/MW envelope"


def test_min_up_down_range(lookup: pd.DataFrame) -> None:
    """Min up / down in (0, 48] hours."""
    assert (lookup.min_up_hr > 0).all()
    assert (lookup.min_up_hr <= 48).all()
    assert (lookup.min_down_hr > 0).all()
    assert (lookup.min_down_hr <= 48).all()


def test_start_time_range(lookup: pd.DataFrame) -> None:
    """Hot start in [0, 12]h; cold start in [0, 24]h."""
    assert (lookup.hot_start_time_hr >= 0).all()
    assert (lookup.hot_start_time_hr <= 12).all()
    assert (lookup.cold_start_time_hr >= 0).all()
    assert (lookup.cold_start_time_hr <= 24).all()


def test_ramp_rate_range(lookup: pd.DataFrame) -> None:
    """Ramp in [0, 50] %/min — bounds aero-derivative max."""
    assert (lookup.ramp_rate_pct_per_min >= 0).all()
    assert (lookup.ramp_rate_pct_per_min <= 50).all()


# ---------------------------------------------------------------------------
# Internal consistency tests
# ---------------------------------------------------------------------------

def test_cold_start_time_exceeds_hot(lookup: pd.DataFrame) -> None:
    """Cold start must take at least as long as hot start."""
    bad = lookup[lookup.cold_start_time_hr < lookup.hot_start_time_hr]
    assert bad.empty, (
        f"Cold start time < hot start time in rows: "
        f"{bad[['prime_mover_code', 'vintage_class', 'hot_start_time_hr', 'cold_start_time_hr']].to_dict('records')}"
    )


def test_ccgt_block_startup_cost_monotonic(lookup: pd.DataFrame) -> None:
    """For CCGT block (CT, CA, CC non-aero): cold C&M >= warm >= hot C&M (Kumar 'Gas-CC' is monotonic)."""
    ccgt = lookup[
        lookup.prime_mover_code.isin(["CT", "CA", "CC"])
        & ~lookup.aero_derivative
    ]
    cold_warm = ccgt.startup_cost_cold_p50_per_mw >= ccgt.startup_cost_warm_p50_per_mw
    warm_hot = ccgt.startup_cost_warm_p50_per_mw >= ccgt.startup_cost_hot_p50_per_mw
    assert cold_warm.all(), "CCGT block: cold C&M not >= warm C&M everywhere"
    assert warm_hot.all(), "CCGT block: warm C&M not >= hot C&M everywhere"


def test_usd_year_present(lookup: pd.DataFrame) -> None:
    """Every row has a vom_usd_year and startup_cost_usd_year (per consolidation plan §5 D2 — original-year USD)."""
    assert lookup.vom_usd_year.notna().all()
    assert lookup.startup_cost_usd_year.notna().all()


# ---------------------------------------------------------------------------
# Lockport-specific tests
# ---------------------------------------------------------------------------

def test_lockport_ct_row_exists(lookup: pd.DataFrame) -> None:
    """Lockport's GEN1-3 (CT, 1992) maps to (CT, <2000, False)."""
    row = lookup[
        (lookup.prime_mover_code == "CT")
        & (lookup.vintage_class == "<2000")
        & (~lookup.aero_derivative)
    ]
    assert len(row) == 1, f"Expected 1 row for Lockport CTs, got {len(row)}"


def test_lockport_ca_row_exists(lookup: pd.DataFrame) -> None:
    """Lockport's GEN4 (CA, 1992) maps to (CA, <2000, False)."""
    row = lookup[
        (lookup.prime_mover_code == "CA")
        & (lookup.vintage_class == "<2000")
        & (~lookup.aero_derivative)
    ]
    assert len(row) == 1, f"Expected 1 row for Lockport CA, got {len(row)}"


def test_lockport_ct_and_ca_identical_kumar_values(lookup: pd.DataFrame) -> None:
    """Per lab pass Decision 2: CT-in-CCGT and CA share identical Kumar block-level values."""
    ct = lookup[
        (lookup.prime_mover_code == "CT")
        & (lookup.vintage_class == "<2000")
        & (~lookup.aero_derivative)
    ].iloc[0]
    ca = lookup[
        (lookup.prime_mover_code == "CA")
        & (lookup.vintage_class == "<2000")
        & (~lookup.aero_derivative)
    ].iloc[0]
    # Kumar block-level: startup C&M + fuel should match
    for col in [
        "startup_cost_cold_p50_per_mw",
        "startup_cost_warm_p50_per_mw",
        "startup_cost_hot_p50_per_mw",
        "startup_fuel_cold_mmbtu_per_mw",
        "startup_fuel_warm_mmbtu_per_mw",
        "startup_fuel_hot_mmbtu_per_mw",
    ]:
        assert ct[col] == ca[col], f"{col}: CT={ct[col]} != CA={ca[col]} — Decision 2 violated"
