"""Smoke tests for Lockport's static profile YAMLs.

Validates that identity.yaml + engineering.yaml + market_context.yaml load
cleanly, the assumption-tracking structure is respected, and key derived
quantities recover correctly (e.g. plant total nameplate = 221.3 MW).

Per consolidation plan §8 Phase C acceptance criterion.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCKPORT_DIR = REPO_ROOT / "data" / "assets" / "lockport"

# Valid status codes per docs/assumptions/status_taxonomy.md
VALID_STATUSES = {
    "real_observed",
    "real_reported",
    "real_computed",
    "assumed_techclass",
    "assumed_vendor",
    "assumed_industry",
    "assumed_derived",
    "placeholder",
    "not_applicable",
}

VALID_CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def identity() -> dict:
    return yaml.safe_load((LOCKPORT_DIR / "identity.yaml").read_text())


@pytest.fixture(scope="module")
def engineering() -> dict:
    return yaml.safe_load((LOCKPORT_DIR / "engineering.yaml").read_text())


@pytest.fixture(scope="module")
def market_context() -> dict:
    return yaml.safe_load((LOCKPORT_DIR / "market_context.yaml").read_text())


@pytest.fixture(scope="module")
def operating_profile() -> dict:
    return yaml.safe_load((LOCKPORT_DIR / "operating_profile.yaml").read_text())


@pytest.fixture(scope="module")
def ltsa_terms() -> dict:
    return yaml.safe_load((LOCKPORT_DIR / "ltsa_terms.yaml").read_text())


# ---------------------------------------------------------------------------
# Helper — walk a nested dict and yield every leaf "value" block
# ---------------------------------------------------------------------------

def iter_leaf_blocks(node, path="") -> "Iterator[tuple[str, dict]]":
    """Yield (path, block) for every dict that contains a 'value' key.

    A "leaf block" is the {value, status, source, ...} envelope per the
    assumption-tracking schema. Skips strings, ints, lists, etc.
    """
    if isinstance(node, dict):
        if "value" in node and "status" in node:
            yield path, node
        else:
            for k, v in node.items():
                yield from iter_leaf_blocks(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from iter_leaf_blocks(v, f"{path}[{i}]")


# ---------------------------------------------------------------------------
# Files exist and load
# ---------------------------------------------------------------------------

def test_files_exist() -> None:
    for fn in (
        "identity.yaml",
        "engineering.yaml",
        "market_context.yaml",
        "operating_profile.yaml",
        "ltsa_terms.yaml",
        "caveats.md",
        "provenance.md",
    ):
        path = LOCKPORT_DIR / fn
        assert path.exists(), f"Missing {path}"
        assert path.stat().st_size > 0, f"Empty {path}"


def test_identity_loads(identity: dict) -> None:
    assert isinstance(identity, dict)
    assert "plant" in identity
    assert "operator" in identity
    assert "location" in identity


def test_engineering_loads(engineering: dict) -> None:
    assert isinstance(engineering, dict)
    assert "plant" in engineering
    assert "generators" in engineering


def test_market_context_loads(market_context: dict) -> None:
    assert isinstance(market_context, dict)
    assert "iso" in market_context
    assert "lmp_nodes" in market_context


# ---------------------------------------------------------------------------
# Assumption-tracking schema compliance
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("file_name", ["identity", "engineering", "market_context", "operating_profile", "ltsa_terms"])
def test_all_leaf_values_have_valid_status(file_name: str, request) -> None:
    """Every leaf block has a status code in the valid taxonomy."""
    doc = request.getfixturevalue(file_name)
    for path, block in iter_leaf_blocks(doc):
        assert "value" in block, f"{file_name}.{path}: missing 'value' key"
        assert "status" in block, f"{file_name}.{path}: missing 'status' key"
        assert block["status"] in VALID_STATUSES, (
            f"{file_name}.{path}: invalid status '{block['status']}'. "
            f"Must be one of {VALID_STATUSES}"
        )


@pytest.mark.parametrize("file_name", ["identity", "engineering", "market_context", "operating_profile", "ltsa_terms"])
def test_all_non_na_leaves_have_source(file_name: str, request) -> None:
    """Every leaf block (except not_applicable) cites a source."""
    doc = request.getfixturevalue(file_name)
    for path, block in iter_leaf_blocks(doc):
        if block["status"] == "not_applicable":
            continue
        assert "source" in block, f"{file_name}.{path}: missing 'source' key"
        assert isinstance(block["source"], str) and len(block["source"]) > 0, (
            f"{file_name}.{path}: source must be a non-empty string"
        )


@pytest.mark.parametrize("file_name", ["identity", "engineering", "market_context", "operating_profile", "ltsa_terms"])
def test_assumed_values_have_confidence(file_name: str, request) -> None:
    """Any assumed_* status carries a confidence field (HIGH/MEDIUM/LOW)."""
    doc = request.getfixturevalue(file_name)
    for path, block in iter_leaf_blocks(doc):
        if not block["status"].startswith("assumed_"):
            continue
        assert "confidence" in block, (
            f"{file_name}.{path}: status '{block['status']}' requires 'confidence' field"
        )
        assert block["confidence"] in VALID_CONFIDENCE_LEVELS, (
            f"{file_name}.{path}: invalid confidence '{block['confidence']}'"
        )


@pytest.mark.parametrize("file_name", ["identity", "engineering", "market_context", "operating_profile", "ltsa_terms"])
def test_placeholders_have_validation_path(file_name: str, request) -> None:
    """Any placeholder status has a non-empty validation_path."""
    doc = request.getfixturevalue(file_name)
    for path, block in iter_leaf_blocks(doc):
        if block["status"] != "placeholder":
            continue
        assert "validation_path" in block, (
            f"{file_name}.{path}: placeholder requires 'validation_path' field"
        )


# ---------------------------------------------------------------------------
# Identity-specific tests
# ---------------------------------------------------------------------------

def test_eia_plant_id_is_54041(identity: dict) -> None:
    assert identity["plant"]["id"]["value"] == 54041


def test_orispl_matches_eia(identity: dict) -> None:
    """EPA ORISPL is identical to EIA Plant ID."""
    eia_id = identity["cross_system_ids"]["eia_plant_id"]["value"]
    orispl = identity["cross_system_ids"]["epa_orispl"]["value"]
    assert eia_id == orispl == 54041


def test_sector_is_ipp_chp(identity: dict) -> None:
    assert identity["plant"]["sector"]["value"] == "IPP CHP"


def test_entity_type_q(identity: dict) -> None:
    """Entity Type Q = cogeneration entity."""
    assert identity["operator"]["entity_type_code"]["value"] == "Q"


# ---------------------------------------------------------------------------
# Engineering-specific tests
# ---------------------------------------------------------------------------

def test_four_generators_present(engineering: dict) -> None:
    """All four expected generator IDs are present."""
    assert set(engineering["generators"].keys()) == {"GEN1", "GEN2", "GEN3", "GEN4"}


def test_plant_total_nameplate_matches_sum(engineering: dict) -> None:
    """Plant total nameplate = sum of generator nameplates = 221.3 MW.

    This is the canonical Phase C acceptance check per consolidation plan §8.
    """
    gen_total = sum(
        engineering["generators"][gid]["nameplate_capacity_mw"]["value"]
        for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]
    )
    plant_total = engineering["plant"]["total_nameplate_mw"]["value"]
    assert gen_total == pytest.approx(221.3, rel=1e-3)
    assert plant_total == pytest.approx(221.3, rel=1e-3)
    assert gen_total == pytest.approx(plant_total, rel=1e-3)


def test_plant_total_summer_matches_sum(engineering: dict) -> None:
    gen_total = sum(
        engineering["generators"][gid]["net_summer_capacity_mw"]["value"]
        for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]
    )
    assert gen_total == pytest.approx(219.0, rel=1e-3)


def test_plant_total_winter_matches_sum(engineering: dict) -> None:
    gen_total = sum(
        engineering["generators"][gid]["net_winter_capacity_mw"]["value"]
        for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]
    )
    assert gen_total == pytest.approx(230.0, rel=1e-3)


def test_three_cts_and_one_ca(engineering: dict) -> None:
    """GEN1-3 are CTs, GEN4 is CA — the 3-on-1 CCGT topology."""
    assert engineering["generators"]["GEN1"]["prime_mover_code"]["value"] == "CT"
    assert engineering["generators"]["GEN2"]["prime_mover_code"]["value"] == "CT"
    assert engineering["generators"]["GEN3"]["prime_mover_code"]["value"] == "CT"
    assert engineering["generators"]["GEN4"]["prime_mover_code"]["value"] == "CA"


def test_all_generators_chp_flagged(engineering: dict) -> None:
    """All four generators are CHP-flagged (cogen)."""
    for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]:
        assert engineering["generators"][gid]["is_chp_flagged"]["value"] is True


def test_all_generators_dual_fuel(engineering: dict) -> None:
    for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]:
        assert engineering["generators"][gid]["is_dual_fuel"]["value"] is True
        assert engineering["generators"][gid]["secondary_energy_source_code"]["value"] == "DFO"


def test_only_gen4_has_duct_burners(engineering: dict) -> None:
    """Duct burners are only on the bottoming ST (GEN4)."""
    assert engineering["generators"]["GEN1"]["has_duct_burners"]["value"] is False
    assert engineering["generators"]["GEN2"]["has_duct_burners"]["value"] is False
    assert engineering["generators"]["GEN3"]["has_duct_burners"]["value"] is False
    assert engineering["generators"]["GEN4"]["has_duct_burners"]["value"] is True


def test_ct_min_load_62_percent(engineering: dict) -> None:
    """1992 F-class CT min load = 30 MW = 62% of 48.7 MW nameplate."""
    for gid in ["GEN1", "GEN2", "GEN3"]:
        assert engineering["generators"][gid]["min_load_mw"]["value"] == 30.0
        assert engineering["generators"][gid]["min_load_pct"]["value"] == pytest.approx(62.0, rel=1e-2)


def test_st_min_load_19_percent(engineering: dict) -> None:
    """ST is highly flexible — 19% min load."""
    assert engineering["generators"]["GEN4"]["min_load_mw"]["value"] == 14.0
    assert engineering["generators"]["GEN4"]["min_load_pct"]["value"] == pytest.approx(19.0, rel=1e-2)


def test_st_summer_gain_not_derate(engineering: dict) -> None:
    """GEN4's summer derate is NEGATIVE (capacity gain), distinct from CTs."""
    assert engineering["generators"]["GEN4"]["summer_derate_pct"]["value"] < 0


def test_gen1_gas_capacity_42_6(engineering: dict) -> None:
    """GEN1 gas capacity per EIA 3_5 is 42.6 MW (slight difference from GEN2/3)."""
    assert engineering["generators"]["GEN1"]["capacity_mw_with_gas_summer"]["value"] == 42.6


def test_gen2_gen3_gas_capacity_41_6(engineering: dict) -> None:
    """GEN2 and GEN3 gas capacity per EIA 3_5 is 41.6 MW."""
    assert engineering["generators"]["GEN2"]["capacity_mw_with_gas_summer"]["value"] == 41.6
    assert engineering["generators"]["GEN3"]["capacity_mw_with_gas_summer"]["value"] == 41.6


def test_dual_fuel_switch_time_1_hour(engineering: dict) -> None:
    for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]:
        gen = engineering["generators"][gid]
        assert gen["switch_time_gas_to_oil_hr"]["value"] == 1.0
        assert gen["switch_time_oil_to_gas_hr"]["value"] == 1.0


def test_plant_chp_flag(engineering: dict) -> None:
    assert engineering["plant"]["is_chp"]["value"] is True


def test_plant_ambient_sensitive_flag(engineering: dict) -> None:
    assert engineering["plant"]["is_ambient_sensitive"]["value"] is True


def test_no_carbon_capture(engineering: dict) -> None:
    """1992 cogen plant — no CCS."""
    assert engineering["plant"]["has_carbon_capture"]["value"] is False
    for gid in ["GEN1", "GEN2", "GEN3", "GEN4"]:
        assert engineering["generators"][gid]["has_carbon_capture"]["value"] is False


# ---------------------------------------------------------------------------
# Market-context-specific tests
# ---------------------------------------------------------------------------

def test_iso_is_nyiso(market_context: dict) -> None:
    assert market_context["iso"]["name"]["value"] == "NYISO"
    assert market_context["balancing_authority"]["code"]["value"] == "NYIS"


def test_nyiso_zone_a(market_context: dict) -> None:
    assert market_context["iso"]["zone"]["value"] == "Zone A"


def test_lmp_node_ct_side(market_context: dict) -> None:
    """CTs (GEN1-3) → PTID 23791, HIGH confidence."""
    cts = market_context["lmp_nodes"]["primary_cts"]
    assert cts["ptid"]["value"] == 23791
    assert cts["confidence"]["value"] == "HIGH"


def test_lmp_node_st_side(market_context: dict) -> None:
    """ST (GEN4) → PTID 323769, MEDIUM confidence."""
    st = market_context["lmp_nodes"]["primary_st"]
    assert st["ptid"]["value"] == 323769
    assert st["confidence"]["value"] == "MEDIUM"


def test_egrid_subregion_nyup(market_context: dict) -> None:
    assert market_context["egrid"]["subregion_code"]["value"] == "NYUP"


def test_rggi_exposed(market_context: dict) -> None:
    """NY state → RGGI exposure True."""
    assert market_context["rggi"]["exposed"]["value"] is True


def test_gas_market_algonquin(market_context: dict) -> None:
    assert market_context["gas_market"]["delivery_hub"]["value"] == "Algonquin Citygate"


def test_capacity_market_not_modeled_v1(market_context: dict) -> None:
    """v1 is energy-only; capacity revenue deferred to v2."""
    assert market_context["capacity_market"]["modeled_in_v1"]["value"] is False


# ---------------------------------------------------------------------------
# Cross-file consistency
# ---------------------------------------------------------------------------

def test_eia_plant_id_consistent(identity: dict) -> None:
    """plant.id and cross_system_ids.eia_plant_id agree."""
    assert identity["plant"]["id"]["value"] == identity["cross_system_ids"]["eia_plant_id"]["value"]


def test_ptid_consistent_across_files(identity: dict, market_context: dict) -> None:
    """PTIDs in identity.cross_system_ids match market_context.lmp_nodes."""
    assert (
        identity["cross_system_ids"]["nyiso_ptid_cts"]["value"]
        == market_context["lmp_nodes"]["primary_cts"]["ptid"]["value"]
    )
    assert (
        identity["cross_system_ids"]["nyiso_ptid_st"]["value"]
        == market_context["lmp_nodes"]["primary_st"]["ptid"]["value"]
    )


def test_egrid_subregion_consistent(identity: dict, market_context: dict) -> None:
    assert (
        identity["cross_system_ids"]["egrid_subregion_code"]["value"]
        == market_context["egrid"]["subregion_code"]["value"]
    )


# ---------------------------------------------------------------------------
# Operating-profile-specific tests (Phase D — MOR-derived)
# ---------------------------------------------------------------------------

def test_operating_profile_loads(operating_profile: dict) -> None:
    assert isinstance(operating_profile, dict)
    assert "heat_rate_by_mode" in operating_profile
    assert "cold_start_gas" in operating_profile
    assert "dhts" in operating_profile


def test_three_cc_modes_present(operating_profile: dict) -> None:
    """1×CC / 2×CC / 3×CC_full all populated from MOR Stage 2."""
    modes = operating_profile["heat_rate_by_mode"]
    assert "1xCC" in modes
    assert "2xCC" in modes
    assert "3xCC_full" in modes


def test_heat_rate_ranges(operating_profile: dict) -> None:
    """All mode heat rates are in physically sensible range 5000-15000 Btu/kWh."""
    for mode in ("1xCC", "2xCC", "3xCC_full"):
        hr = operating_profile["heat_rate_by_mode"][mode]["btu_per_kwh"]["value"]
        assert 5000 <= hr <= 15000, f"{mode} HR {hr} outside 5000-15000 range"


def test_mode_hierarchy_more_cts_better_hr(operating_profile: dict) -> None:
    """Physics: more CTs online = better efficiency. 3×CC_full < 2×CC < 1×CC."""
    hr_3x = operating_profile["heat_rate_by_mode"]["3xCC_full"]["btu_per_kwh"]["value"]
    hr_2x = operating_profile["heat_rate_by_mode"]["2xCC"]["btu_per_kwh"]["value"]
    hr_1x = operating_profile["heat_rate_by_mode"]["1xCC"]["btu_per_kwh"]["value"]
    assert hr_3x < hr_2x < hr_1x, (
        f"Mode hierarchy violated: 3×CC={hr_3x}, 2×CC={hr_2x}, 1×CC={hr_1x}"
    )


def test_2023_cross_validation_within_1pct(operating_profile: dict) -> None:
    """MOR 2023 HR reproduces eGRID 2023 placeholder within 1% — strong validation."""
    delta = operating_profile["cross_validation"]["delta_pct"]["value"]
    assert abs(delta) <= 1.0, f"2023 cross-validation delta {delta}% exceeds 1% tolerance"


def test_2024_correction_value(operating_profile: dict) -> None:
    """Lockport actually generated 192,494 MWh in 2024 (not zero as public brief said)."""
    actual_2024 = operating_profile["annual_generation"]["corrected_2024_annual_mwh"]["value"]
    assert actual_2024 == 192494


def test_cold_start_warming_days_observed(operating_profile: dict) -> None:
    """35 warming days observed over 5 years per MOR Stage 2."""
    assert operating_profile["cold_start_gas"]["warming_days_observed_5yr"]["value"] == 35


def test_cold_start_followed_by_active_mode(operating_profile: dict) -> None:
    """97% of warming days are followed by active CC mode — confirms they are pre-start warming."""
    pct = operating_profile["cold_start_gas"]["pct_followed_by_active_cc_mode"]["value"]
    assert pct >= 95.0


# ---------------------------------------------------------------------------
# LTSA-specific tests (Phase F — all placeholder until data room extraction)
# ---------------------------------------------------------------------------

def test_ltsa_loads(ltsa_terms: dict) -> None:
    assert isinstance(ltsa_terms, dict)
    # The seven LTSA cost streams (per framework V2 §"LTSA cost taxonomy")
    for stream in (
        "fixed_fee",
        "eoh_reserve",
        "inspection_ci",
        "inspection_mi",
        "start_overage",
        "availability_penalty",
        "hr_penalty",
        "forced_outage_coverage",
    ):
        assert stream in ltsa_terms, f"Missing LTSA stream: {stream}"


def test_ltsa_all_values_placeholder(ltsa_terms: dict) -> None:
    """Per Phase F design: every value in ltsa_terms.yaml is placeholder until data room extraction.

    This will REGRESS when extraction completes — at that point the test should be updated
    or split per-value to track real vs placeholder counts.
    """
    placeholder_count = 0
    non_placeholder_count = 0
    non_placeholder_paths = []
    for path, block in iter_leaf_blocks(ltsa_terms):
        if block["status"] == "placeholder":
            placeholder_count += 1
        else:
            non_placeholder_count += 1
            non_placeholder_paths.append((path, block["status"]))
    assert non_placeholder_count == 0, (
        f"Phase F expects ALL ltsa_terms values to be placeholder. "
        f"Non-placeholder values found: {non_placeholder_paths}"
    )
    assert placeholder_count > 0, "No leaf blocks found in ltsa_terms.yaml"


def test_ltsa_all_placeholders_have_validation_path(ltsa_terms: dict) -> None:
    """Per Phase F design: every placeholder names where the real value comes from."""
    for path, block in iter_leaf_blocks(ltsa_terms):
        assert "validation_path" in block, (
            f"ltsa_terms.{path}: placeholder missing validation_path"
        )
        assert isinstance(block["validation_path"], str), (
            f"ltsa_terms.{path}: validation_path must be a string"
        )
        assert len(block["validation_path"]) > 0, (
            f"ltsa_terms.{path}: validation_path must be non-empty"
        )
