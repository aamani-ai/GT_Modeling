# data/tech_class_defaults/ — Tech-class generic dispatch parameters

> Lookup table of generic operating parameters (startup cost, VOM, min up/down, hot-start time, ramp rate) keyed on `(prime_mover_code, vintage_class, aero_derivative)`. Sourced from the **renewablesinfo dispatch_params lab pass** (shipped 2026-05-08).

## What this is

Tech-class-typical values for parameters that no plant-level source carries. Used as defaults when a specific asset's value isn't observable. Per the lab pass:

- Kumar 2012 NREL/SR-5500-55433 is the **primary** for startup C&M cost + startup fuel (NOT PJM Manual 15 — see below)
- NREL ATB 2024 Moderate is canonical for VOM + heat rate + ramp + min load
- EIA AEO 2026 EMM is the cross-check for VOM at modern vintages
- Siemens 501F / GE LM6000 vendor literature for start times
- Industry-typical defaults (LOW confidence) for min up/min down — no public canonical source exists

**Critical methodology note**: PJM Manual 15 publishes no default $/MW values — only the formula and unit-specific filings. This contradicts an earlier assumption. Kumar 2012 is our actual primary for $/MW startup cost values.

## Status

✅ **Populated 2026-05-14 (Phase B).** Files copied from renewablesinfo lab pass v1 (shipped 2026-05-08).

## Files (when populated by Phase B)

| File | Description |
|---|---|
| `dispatch_params_lookup.parquet` | 20 rows × 35 cols — the lookup itself |
| `dispatch_params_values.csv` | Human-readable mirror (same data, CSV for easy diff/edit) |
| `refs/kumar_2012.pdf` | Kumar et al. 2012 NREL/SR-5500-55433 — primary for startup cost C&M + startup fuel |
| `refs/atb_2024.xlsx` | NREL ATB 2024 v3 workbook — primary for VOM + heat rate + ramp |
| `refs/emm_2026.pdf` | EIA AEO 2026 EMM Assumptions, April 2026 — VOM cross-check |
| `refs/pjm_m15.pdf` | PJM Manual 15 Rev 47 — methodology only, no default values |
| `refs/AUDIT.md` | Cell-by-cell source attribution (mirrors the lab AUDIT.md) |

## Shape

20 rows = 4 prime movers × 4 vintage classes × {aero=False for non-GT; aero={False, True} for GT}.

Key columns:
- `prime_mover_code` — CT / CA / CC / GT
- `vintage_class` — `<2000` / `2000-2010` / `2010-2020` / `2020+`
- `aero_derivative` — True for aero (LM6000, LMS100), False otherwise
- Value columns: `vom_per_mwh`, `startup_cost_{cold,warm,hot}_p{25,50,75}_per_mw`, `startup_fuel_{cold,warm,hot}_mmbtu_per_mw`, `min_up_hr`, `min_down_hr`, `{hot,warm,cold}_start_time_hr`, `ramp_rate_pct_per_min`
- Confidence columns (HIGH/MEDIUM/LOW per parameter group)
- Provenance columns (`primary_source_label`, `assumption_vintage`, `notes`)

## Confidence-tier distribution (from lab pass)

11 HIGH / 40 MEDIUM / 74 LOW / 19 NoSource across 144 cells. The LOW count is structural — no public source carries min_up/min_down values, and the `2020+` vintage falls outside Kumar's database. Documented in detail in `refs/AUDIT.md`.

## Source

Lab repo: `~/code/personal/renewablesinfo/integration/dispatch_params/`
- Canonical AUDIT.md lives there (single source of truth for cell-by-cell attribution)
- Build script: `build_lookup.py`
- Lab pass status: shipped 2026-05-08 (v1, lab-only / no UI surfacing)

## Refresh procedure

1. In the lab repo, re-run `build_lookup.py` if values change
2. Copy these 7 files into `data/tech_class_defaults/`
3. Recompute SHA256 checksums (see Provenance below)
4. Update this README's "last refreshed" date + checksums
5. Commit

**Last refreshed**: 2026-05-14

## Provenance

Files copied from `~/code/personal/renewablesinfo/integration/dispatch_params/` on 2026-05-14. Lab pass version: v1 (shipped 2026-05-08).

| File | SHA256 |
|---|---|
| `dispatch_params_lookup.parquet` | `779059e6b049489939fef29ccf5d04cd47c1282da2eb8c1baa9a9901e989fd32` |
| `dispatch_params_values.csv` | `325575ad38a3c977b6b90a2eddac3377533fbd6af7721b946d0f04fafae0b56b` |
| `refs/AUDIT.md` | `55b406abf0c0fc85935532f1ef92d360e2bc317537fc221ec36af26045aa24ec` |
| `refs/kumar_2012.pdf` | `697a2cece96f438e24248e868981af4a12a0aad0d0758a051dc34c78d94825be` |
| `refs/atb_2024.xlsx` | `34316344383535a8bf9eb220bc54282cff75bcbc332a38e8c10a17c487dc8e46` |
| `refs/emm_2026.pdf` | `ae21fcea7110c6efac978fa9bf28670998392e72959077f7a07d5aa3045e00bb` |
| `refs/pjm_m15.pdf` | `d82338fd05bc1acadaf2184b20ca1cad76bc14760921fddb8f91f9a6d986df18` |

Verify with: `shasum -a 256 dispatch_params_lookup.parquet dispatch_params_values.csv refs/*.{md,pdf,xlsx}`

## Verification at load time

[`tests/test_tech_class_defaults.py`](../../tests/test_tech_class_defaults.py) provides unit-range smoke tests covering:
- Schema presence (all 35 columns)
- Row count = 20
- Confidence-tier values in allowed set
- Numeric ranges per parameter group
- Internal consistency (cold start > warm > hot for CCGT block; cold start time > hot start time)
- Lockport-applicable rows exist: `(CT, <2000, False)` and `(CA, <2000, False)`

Run with: `pytest tests/test_tech_class_defaults.py -v` from the repo root.

## Cross-asset use

For each asset's generators, derive the join key:
- `prime_mover_code` from `data/assets/<asset>/engineering.yaml`
- `vintage_class` from `operating_year` via the cut: `<2000`, `2000-2010`, `2010-2020`, `2020+`
- `aero_derivative` — True for GT prime mover with nameplate < ~100 MW (heuristic; refined in Phase G/H)

Lockport example:
- GEN1, GEN2, GEN3 (CT, 1992, non-aero) → row `(CT, <2000, False)`
- GEN4 (CA, 1992, non-aero) → row `(CA, <2000, False)`

Both rows carry identical Kumar block-level values (Kumar's "Gas-CC" doesn't split CT-in-CCGT from CA bottoming-cycle).

## See also

- [consolidation plan §7](../../docs/plans/consolidation_plan.md#7-migration-mapping) — migration mapping
- [docs/reference/tech_class_dispatch_params_summary.md](../../docs/reference/tech_class_dispatch_params_summary.md) — digest of the lab pass methodology decisions (to be written in Phase B)
- Lab AUDIT.md: `~/code/personal/renewablesinfo/integration/dispatch_params/AUDIT.md`
- Lab pass design doc: `~/code/personal/renewablesinfo_org/docs/design/dispatch_operating_params.md`
