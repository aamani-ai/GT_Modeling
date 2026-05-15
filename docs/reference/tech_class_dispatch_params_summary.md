# Tech-Class Dispatch Parameters — Digest of the Lab Pass

> Digest of the renewablesinfo dispatch_params lab pass (shipped 2026-05-08). The canonical AUDIT.md lives at [`data/tech_class_defaults/refs/AUDIT.md`](../../data/tech_class_defaults/refs/AUDIT.md). This doc summarizes the methodology decisions a gt_models reader needs to know to use the lookup correctly.

## What the lab pass produced

A tech-class generic lookup of dispatch operating parameters (VOM, startup cost C&M + fuel, min up/down, hot/warm/cold start time, ramp rate) for thermal generators. Currently gas-only (v1 scope: CT, CA, CC, GT prime movers; aero-derivative flag for GT).

| Artifact | Location in gt_models |
|---|---|
| `dispatch_params_lookup.parquet` | [`data/tech_class_defaults/`](../../data/tech_class_defaults/) |
| `dispatch_params_values.csv` (human-readable mirror) | Same |
| `AUDIT.md` (cell-by-cell source attribution) | [`data/tech_class_defaults/refs/AUDIT.md`](../../data/tech_class_defaults/refs/AUDIT.md) |
| Source PDFs (Kumar 2012, ATB 2024, EIA AEO 2026, PJM M-15) | [`data/tech_class_defaults/refs/`](../../data/tech_class_defaults/refs/) |

Shape: **20 rows × 35 columns**. 20 = 4 prime movers × 4 vintage classes (`<2000` / `2000-2010` / `2010-2020` / `2020+`), with aero-derivative variants for GT only.

## The headline finding — PJM publishes no defaults

**PJM Manual 15 publishes no default $/MW values for startup cost or min up/down time.** Sections 5–6 specify the *formula* and require unit-specific Start Fuel Consumed (MMBtu/Start), Performance Factor, Station Service, and unit-specific Start Maintenance Adders to be filed by each Market Seller. The only quantitative defaults are Soak-Time fractions of Min Run Time (Cold = 0.73×, Intermediate = 0.61×, Hot = 0.43×) — but Min Run Time itself is "unit specific."

**Consequence**: Kumar 2012 NREL/SR-5500-55433 is our actual primary for $/MW startup cost values. The lab pass design originally assumed PJM Manual 15 was primary; this finding from the research phase corrected that.

**Secondary consequence**: PJM does NOT lock a fixed gas-price assumption. Each Market Seller declares its own fuel price per its documented Fuel Cost Policy. So there is no single "PJM gas price" that converts MMBtu/start to $/start — the conversion is unit- and day-specific.

For our model: we'll use a documented reference gas price (Henry Hub forward + Algonquin Citygate basis for Lockport) as the conversion assumption, and flag it as a model parameter.

## The seven methodology decisions

Locked during the lab pass research phase. Each propagates into how we use the lookup in gt_models.

### Decision 1: Kumar 2012 is primary for startup cost (not PJM)

Reasoning: PJM publishes no default $/MW values (see above). Kumar reports lower-bound C&M cost ranges by tech class with explicit median + 25th/75th percentiles.

We adopt Kumar median as the central estimate, with the IQR (p25/p75) preserved in the lookup for UI range presentation later.

### Decision 2: CT, CA, CC share Kumar block-level values

Kumar reports "Gas-CC [GT+HRSG+ST]" as a single technology class — does not separate CT (in CCGT) from CA (steam-bottoming side) from CC (single-shaft bundled).

**No public source separately quantifies $/MW startup damage on the GT vs ST half of a CCGT block.** All three prime mover codes receive the same Kumar block-level values.

The only parameter where CT and CA likely differ is ramp rate — CA is HRSG-limited and slower. We apply ATB block-level ramp (5%/min) to all three for v1 simplicity; per-prime-mover refinement is v2.

### Decision 3: Kumar 2012 doesn't separate vintages

Kumar's database aggregates 1990s–2010s plants without explicit vintage segmentation. We use the **same Kumar values across vintage classes for startup cost**, but downgrade confidence (HIGH → MEDIUM) for `<2000` and `2010-2020`, and to LOW for `2020+` (which falls outside Kumar's database entirely).

For `2020+`, ATB Advanced scenario 2025–2030 projection is the proxy with explicit LOW confidence.

### Decision 4: VOM has wide cross-source spread — disclose ranges

Kumar (2011$ baseload-only lower bound) ≈ $1/MWh inflates to ≈$1.40/MWh (2025$); ATB 2024 (2022$ new-build) ≈ $2.17/MWh inflates to ≈$2.39/MWh; EIA AEO 2026 (2025$ new-build) = $3.49/MWh.

The 2.5× spread is real and reflects how the parameter is defined (baseload-only vs new-build all-in vs post-inflation S&L 2024 update).

**Canonical for the lookup**: ATB 2024 Moderate (mid-range). Kumar low and AEO high are recorded as `vom_per_mwh_low` and `vom_per_mwh_high` side columns for range disclosure.

### Decision 5: min_up_hr / min_down_hr have no public source

PJM publishes only the formula. Kumar provides "Warm Start Offline Hours" boundaries (5–40 hr for CC, 2–3 hr for large frame CT, 0–1 hr for aero-derivative) — that's the hot/warm threshold, not min-up/min-down.

**Population**: industry-typical defaults from operator-survey literature (NREL WWSIS-2 derives from Kumar with NREL operating assumptions added). Confidence LOW.

**Validation path**: observed CEMS run-length distributions once that lab pass extends to NYISO data.

### Decision 6: Hot/cold start time for F-class CC sourced from Siemens vendor reportage

3 / 6 / 8 hr (hot/warm/cold) for F-class CC block, via Combined Cycle Journal (Athens plant best-practices article).

**Not regulatory-cited.** Confidence MEDIUM. EPA's 2023 Subpart KKKKa proposed rule TSD likely contains regulatory-cited values; flagged for follow-up.

EIA-860 schedule 3_1 reports 12 hr cold-start for 86% of CCGTs — but that's a reporting clustering convention, not actual. **Use the vendor 8 hr value for dispatch modeling; EIA's 12 hr is for compliance reporting context only.**

### Decision 7: `2020+` vintage relies on ATB Advanced scenario projections

Neither Kumar (2012, predates fleet-scale H-class) nor ATB 2024 base-year nor EIA AEO 2026 (only models H-class CC) cleanly populates this vintage. We use ATB 2024 Advanced scenario 2025–2030 column as proxy. Confidence LOW. Validation pending CEMS data for actual 2020+ commissioned plants.

## Confidence distribution

Across 144 cells (16 tech-vintage combinations × 9 parameters) — note the parquet has 20 rows because GT splits into aero/non-aero, but the methodology decisions tally to 144 distinct cells per the AUDIT.md):

| Parameter group | HIGH | MEDIUM | LOW |
|---|---|---|---|
| VOM | 9 / 20 | 11 / 20 | 0 / 20 |
| Startup cost | 5 / 20 | 10 / 20 | 5 / 20 |
| Startup fuel | 20 / 20 | 0 / 20 | 0 / 20 |
| Min up / down | 0 / 20 | 0 / 20 | **20 / 20** |
| Start time | 0 / 20 | 13 / 20 | 7 / 20 |
| Ramp rate | 10 / 20 | 6 / 20 | 4 / 20 |

The min_up/min_down LOW count is structural — no public source exists. CEMS validation is the path.

## What Lockport gets from the lookup

Lockport's four generators (all 1992-commissioned) map to:

| EIA Generator | Prime Mover | Vintage Class | aero_derivative | Lookup row |
|---|---|---|---|---|
| GEN1 | CT | `<2000` | False | `(CT, <2000, False)` |
| GEN2 | CT | `<2000` | False | `(CT, <2000, False)` |
| GEN3 | CT | `<2000` | False | `(CT, <2000, False)` |
| GEN4 | CA | `<2000` | False | `(CA, <2000, False)` |

Per Decision 2, both lookup rows carry identical block-level values:

| Parameter | Value | Source | Confidence |
|---|---|---|---|
| `vom_per_mwh` | $1.02 / MWh (2011$) | Kumar 2012 Tbl 1-1 "Gas-CC" baseload | MEDIUM |
| `startup_cost_cold_p50_per_mw` | $79 / MW (2011$) | Kumar 2012 Tbl 1-1 Cold Start C&M | MEDIUM |
| `startup_cost_warm_p50_per_mw` | $55 / MW (2011$) | Kumar 2012 Tbl 1-1 Warm Start C&M | MEDIUM |
| `startup_cost_hot_p50_per_mw` | $35 / MW (2011$) | Kumar 2012 Tbl 1-1 Hot Start C&M | MEDIUM |
| `startup_fuel_cold_mmbtu_per_mw` | 0.24 MMBtu/MW | Kumar 2012 Tbl 1-3 | HIGH |
| `startup_fuel_warm_mmbtu_per_mw` | 0.20 MMBtu/MW | Kumar 2012 Tbl 1-3 | HIGH |
| `startup_fuel_hot_mmbtu_per_mw` | 0.19 MMBtu/MW | Kumar 2012 Tbl 1-3 | HIGH |
| `min_up_hr` | 6 hr | Industry-typical for `<2000` F-class CCGT | LOW |
| `min_down_hr` | 8 hr | Industry-typical | LOW |
| `hot_start_time_hr` | 3 hr | Siemens 501F via CCJ | MEDIUM |
| `cold_start_time_hr` | 8 hr | Siemens 501F via CCJ | MEDIUM |
| `ramp_rate_pct_per_min` | 4 %/min | Industry estimate (older steam-bottoming, slower than ATB 5%/min reference) | LOW |

**Important caveats specific to Lockport:**

1. **Cogen markup**: Lockport is CHP-flagged. Merchant-CCGT defaults likely understate cogen VOM by 30–50%. Apply markup at dispatch-model time; not encoded in the lookup directly.
2. **Multi-mode dispatch**: Lookup gives block-level values. Lockport's 1×CC / 2×CC / 3×CC operating modes have mode-specific heat rates from the diligence-extractor MOR notebook (8,901 / 9,598 / 10,424 Btu/kWh) that override the tech-class default.
3. **Dual-fuel**: Lockport can switch gas↔oil in 1 hr. Lookup carries gas-mode values only; oil-mode adjustment is a model-side correction.

## How to use the lookup (join key derivation)

```python
import pandas as pd

lookup = pd.read_parquet("data/tech_class_defaults/dispatch_params_lookup.parquet")

# For each generator in the asset:
#   1. Read prime_mover_code from data/assets/<asset>/engineering.yaml
#   2. Derive vintage_class from operating_year:
#        <2000 / 2000-2010 / 2010-2020 / 2020+
#   3. Derive aero_derivative for GT (heuristic: nameplate < ~100 MW for v1)
#   4. Filter the lookup

def get_tech_defaults(prime_mover, vintage_class, aero_derivative=False):
    rows = lookup[
        (lookup.prime_mover_code == prime_mover)
        & (lookup.vintage_class == vintage_class)
        & (lookup.aero_derivative == aero_derivative)
    ]
    assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
    return rows.iloc[0]

# Lockport GEN1 example:
defaults = get_tech_defaults("CT", "<2000", aero_derivative=False)
print(defaults.vom_per_mwh)              # 1.02
print(defaults.startup_cost_cold_p50_per_mw)  # 79.0
print(defaults.confidence_vom)           # MEDIUM
```

## Refresh from upstream

If the lab pass updates (e.g., v2 incorporates CEMS-observed min_up/min_down values, or EPA Subpart KKKKa TSD parsing fills missing cells), the refresh procedure is documented in [`data/tech_class_defaults/README.md`](../../data/tech_class_defaults/README.md) §"Refresh procedure".

## Cross-references

- **Canonical AUDIT** (cell-by-cell sources): [`data/tech_class_defaults/refs/AUDIT.md`](../../data/tech_class_defaults/refs/AUDIT.md)
- **Source PDFs**: [`data/tech_class_defaults/refs/`](../../data/tech_class_defaults/refs/)
- **Lab pass canonical home**: `~/code/personal/renewablesinfo/integration/dispatch_params/`
- **Lab pass design doc** (the original `[ASSUME]` design): `~/code/personal/renewablesinfo_org/docs/design/dispatch_operating_params.md`
- **Unit-range smoke tests**: [`tests/test_tech_class_defaults.py`](../../tests/test_tech_class_defaults.py)
- **Consolidation plan §6 (assumption tracking)**: [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle)
