# Assumption Status Taxonomy

> The 9-code status taxonomy that every leaf value in `data/assets/<asset>/*.yaml` files must use. Plus confidence levels for assumed values, YAML format conventions, and disclosure rules.
>
> Per [consolidation plan §6](../plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle) — non-negotiable for v1 and forward.

---

## Why this taxonomy

Every value in the model carries one of nine statuses. The status is not a footnote — it's the structural fact about whether the model's output is anchored in reality or in assumption. Stakeholders reading model outputs must be able to distinguish a number measured from this plant's actual operation from a number that came from a 2012 NREL paper that didn't separate vintages, from a number waiting for someone to read a PDF in the data room.

The 9 codes cover the realistic provenance space. They're exhaustive (every value fits somewhere) and mutually exclusive (no value gets two codes).

---

## The 9 status codes

### 1. `real_observed`

**Meaning**: Measured directly from this plant's own operating data.

**Examples**:
- Heat rate by mode from Lockport MOR Excel daily aggregation (8,901 / 9,598 / 10,424 Btu/kWh for 3×CC / 2×CC / 1×CC)
- Cold-start gas burn pattern (35 warming days observed, mean 2,537 MMBtu/day)
- Run-streak distributions from MOR daily data

**When to use**: The value came out of an analysis of this specific plant's measured operations (CEMS, MOR, GADS, trial balances, etc.). Not from a regulatory filing — from actual instrumented or recorded operation.

**Confidence required?** No (it's measured; confidence applies to assumed-class statuses).

---

### 2. `real_reported`

**Meaning**: Reported by this plant in regulatory or contractual filings. The plant said so itself, but it's not the same as measured operation.

**Examples**:
- Nameplate capacity from EIA-860 schedule 3_1 (48.7 MW per CT for Lockport)
- Min load from EIA-860 schedule 3_1 (30 MW per CT — note: design/permit floor, not observed economic min)
- Dual-fuel capability flags from EIA-860 schedule 3_5
- LTSA fixed monthly fee from contract (when extracted)
- Emissions rates from EPA eGRID

**When to use**: The value comes from a filing — EIA forms, FERC forms, eGRID, NYISO declarations, signed contracts. The plant has attested to the value; it's not a third-party assumption.

**Confidence required?** No.

**Caveat field common here**: many real_reported values have caveats. E.g., EIA-860 reports min load as a design floor — the plant *can* run at 30 MW but might not run there economically. Document this with a `caveat` field.

---

### 3. `real_computed`

**Meaning**: Derived deterministically from `real_observed` or `real_reported` values. No assumptions added.

**Examples**:
- Plant total nameplate (221.3 MW) = sum of generator nameplates
- Annual capacity factor = generation_mwh / (nameplate × 8760)
- Implied annual heat rate = annual heat input / annual generation
- Summer derate % = (nameplate - summer_capacity) / nameplate

**When to use**: Pure algebra over `real_*` inputs. If any input is assumed, the result is `assumed_derived`, not `real_computed`.

**Confidence required?** No.

**Provenance**: source field should describe the calculation, not name an external source. E.g., `source: "computed from generators[*].nameplate_capacity_mw"`.

---

### 4. `assumed_techclass`

**Meaning**: Tech-class default from a public methodology reference. Not plant-specific.

**Examples**:
- VOM from NREL ATB 2024 F-Frame CC (Moderate scenario): $2.17/MWh
- Startup cost C&M from Kumar 2012 Table 1-1 "Gas-CC" cold start median: $79/MW (2011 USD)
- Heat rate from NREL ATB H-Frame 2x1 CC: 6,196 Btu/kWh
- Ramp rate from NREL ATB F-Frame 2x1 CC: 5%/min sustained

**When to use**: The value comes from NREL ATB / RTO cost development manuals / EIA AEO / Kumar 2012 / similar published references. Tech-class typical, not plant-specific.

**Confidence required?** Yes — HIGH / MEDIUM / LOW per §"Confidence levels".

**Source field**: cite the document + table/page. E.g., `source: "Kumar 2012 NREL/SR-5500-55433 Table 1-1 'Gas-CC' Cold Start C&M, page 12"`.

---

### 5. `assumed_vendor`

**Meaning**: Vendor literature for the specific equipment model.

**Examples**:
- Hot/warm/cold start time for Siemens 501F via Combined Cycle Journal: 3 / 6 / 8 hr
- LM6000 PC/PD/PF fast-start time: 5–10 min
- LMS100 cold-start to full load: 8 min

**When to use**: Manufacturer-published spec for the specific turbine/generator model. Usually more specific than `assumed_techclass` but with marketing-flavor risk.

**Confidence required?** Yes — typically MEDIUM (vendor specifies but field operations may differ) or LOW (vendor marketing only).

**Caveat field common here**: vendor specs often quote best-case conditions (cold ambient, no cycling, ideal fuel). Mark this.

---

### 6. `assumed_industry`

**Meaning**: Industry-typical default with no single canonical public source.

**Examples**:
- Min up time / min down time for `<2000` F-class CCGT (no public source carries these — PJM Manual 15 publishes only the formula, not defaults)
- Estimated ramp rate for pre-2000 steam-bottoming CCGT (older than ATB's reference fleet)
- Cogen VOM markup factor (+30–50%) for CHP plants vs merchant-CCGT defaults

**When to use**: We know the value approximately from industry experience but can't point to a single defensible primary source.

**Confidence required?** Yes — typically **LOW** by definition. If we can't cite a primary source, confidence shouldn't be HIGH.

**Validation_path field important here**: where would the *real* value come from if we had it? E.g., "CEMS observed run-length distribution when NYISO data ingested" or "Operator interview / data room operational reports".

---

### 7. `assumed_derived`

**Meaning**: Derived from other assumed values. Uncertainty compounds.

**Examples**:
- Total cold start cost = `startup_cost_cold_C&M` (Kumar) + `startup_fuel_cold_mmbtu_per_mw` × gas_price (Kumar) — the result is `assumed_derived` because both inputs are `assumed_techclass`
- Cogen-adjusted VOM = `vom_per_mwh` × 1.35 — the markup factor is `assumed_industry`, so the product is `assumed_derived`

**When to use**: The value is a computation, but at least one input is `assumed_*`.

**Confidence required?** Yes — minimum of input confidences (a HIGH × LOW chain produces LOW).

**Source field**: describe the calculation + name the input sources. E.g., `source: "Kumar 2012 Tbl 1-1 cold C&M + Kumar Tbl 1-3 fuel × $4/MMBtu Henry Hub reference"`.

---

### 8. `placeholder`

**Meaning**: Waiting on a known-pending source extraction or analysis. The value will eventually be real, but it isn't yet.

**Examples**:
- LTSA fixed monthly fee, pending data room extraction
- LTSA EOH reserve rate, pending data room extraction
- Lockport's boiler 6_2 design specs (efficiency 50% / 100% load), pending — EIA reporting gap
- Min up/down empirical from CEMS, pending Phase 2c of natural-gas-thermal expansion

**When to use**: We know what the value *should* eventually be, where it should come from, and that we can't fill it today. The model can still run with a placeholder, but flagging it explicitly is critical.

**Value field**: should hold a reasonable default if the model needs to run (e.g., the Athens prototype's `[ASSUME]` value, or a tech-class proxy). Use null only if the model can handle null safely.

**Validation_path field required**: cite where the real value will come from. E.g., `validation_path: "Data room file 3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx — LTSA invoice line"`.

**Confidence?** Not applicable — it's a placeholder, not an estimate.

---

### 9. `not_applicable`

**Meaning**: Field exists in the schema but doesn't apply to this asset.

**Examples**:
- `aero_derivative` flag set for a CT (in a CCGT) generator — aero classification is meaningful for simple-cycle GT only
- Boiler design specs for a generator that has no associated boiler
- LBNL solar/wind crosswalk fields for a gas plant
- Carbon capture flag for a plant without CCS

**When to use**: The schema is generic (covers many asset types), but this asset doesn't have the feature. Distinguish from `placeholder` (waiting for data) and from null/missing (which suggests an error).

**Value field**: null is correct here.

**Confidence?** Not applicable.

---

## Confidence levels (for assumed values only)

Applied to `assumed_techclass`, `assumed_vendor`, `assumed_industry`, `assumed_derived`.

### `HIGH`

Cross-validated by ≥2 primary sources within ±20%.

**Example**: VOM at $2.17/MWh from NREL ATB 2024 F-Frame CC + EIA AEO 2026 EMM agreement (within ±15%) → HIGH for `assumed_techclass`.

### `MEDIUM`

Single primary source, no cross-validation available. Or: extrapolated within tech class (applying a CCGT value to a sub-class where the source didn't differentiate).

**Example**: Kumar 2012 startup cost C&M for "Gas-CC" applied to Lockport's specific 3-on-1 configuration — Kumar doesn't separate 3-on-1 from 2-on-1, so the value is single-source-extrapolated → MEDIUM.

### `LOW`

Single low-quality source (vendor marketing, single academic study, undocumented industry default).

**Example**: Min up time = 6 hr from "industry typical for `<2000` F-class CCGT" with no public canonical source → LOW.

---

## YAML format conventions

### Basic value

```yaml
generators:
  GEN1:
    prime_mover_code:
      value: CT
      status: real_reported
      source: "EIA-860 schedule 3_1 Y2024"
```

### Real value with caveat

```yaml
min_load_mw:
  value: 30.0
  status: real_reported
  source: "EIA-860 schedule 3_1 Y2024"
  caveat: "Design/permit floor, not observed economic min. Validation: CEMS observed minimum stable output."
```

### Assumed value with confidence and source detail

```yaml
vom_per_mwh:
  value: 1.02
  usd_year: 2011
  status: assumed_techclass
  source: "Kumar 2012 NREL/SR-5500-55433 Table 1-1 'Gas-CC' Baseload Variable Cost, page 13"
  confidence: MEDIUM
  caveat: "Baseload-only lower-bound. Cogen markup of +30-50% likely applies (see caveats.md)."
```

### Vendor-sourced value

```yaml
hot_start_time_hr:
  value: 3.0
  status: assumed_vendor
  source: "Siemens 501F field-operations via Combined Cycle Journal"
  source_url: "https://www.ccj-online.com/501f-best-practices-athens/"
  confidence: MEDIUM
  caveat: "Vendor field-operations reportage, not regulatory citation."
```

### Industry-typical (LOW) with validation_path

```yaml
min_up_hr:
  value: 6.0
  status: assumed_industry
  source: "Industry-typical default for <2000 F-class CCGT; no public canonical source"
  confidence: LOW
  validation_path: "Empirical extraction from CEMS observed run-length distribution when NYISO data ingested; or operator interview"
```

### Placeholder

```yaml
ltsa_fixed_monthly_fee_usd:
  value: 850000.0
  status: placeholder
  source: "Athens prototype [ASSUME] default — not Lockport-specific"
  validation_path: "Data room — 3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx LTSA invoice line items"
  caveat: "Placeholder for v1 modeling. Replace with real value when data room extraction completes."
```

### Derived (compound uncertainty)

```yaml
cogen_adjusted_vom_per_mwh:
  value: 1.38  # = 1.02 × 1.35
  status: assumed_derived
  source: "vom_per_mwh × cogen_vom_markup_factor"
  confidence: LOW  # min(MEDIUM, LOW) = LOW
  caveat: "Compound of Kumar 2012 baseload VOM (MEDIUM) and industry-typical cogen markup factor (LOW)."
```

### Not applicable

```yaml
boiler_efficiency_50pct:
  value: null
  status: not_applicable
  source: "GEN1 is a combustion turbine (CT) with HRSG bypass; not directly associated with a boiler"
```

### Computed from real values

```yaml
plant_total_nameplate_mw:
  value: 221.3
  status: real_computed
  source: "Sum of generators[*].nameplate_capacity_mw"
```

---

## Required vs optional fields by status

| Status | Required | Optional |
|---|---|---|
| `real_observed` | value, status, source | caveat |
| `real_reported` | value, status, source | caveat, source_url |
| `real_computed` | value, status, source (describing calculation) | caveat |
| `assumed_techclass` | value, status, source, confidence | caveat, source_url, usd_year, etc. |
| `assumed_vendor` | value, status, source, confidence | caveat, source_url |
| `assumed_industry` | value, status, source, confidence, validation_path | caveat |
| `assumed_derived` | value, status, source (with formula + input sources), confidence | caveat |
| `placeholder` | value (may be null), status, source, validation_path | caveat |
| `not_applicable` | value (null), status, source (explaining why N/A) | — |

---

## Disclosure rules — how each status surfaces in outputs

| Status | UI / report treatment |
|---|---|
| `real_observed` | Use without flag |
| `real_reported` | Use without flag; surface caveat if present |
| `real_computed` | Use without flag |
| `assumed_techclass` | HIGH: footnote with source. MEDIUM: visible "tech-class default" tag. LOW: prominent confidence badge. |
| `assumed_vendor` | Visible "vendor literature" tag |
| `assumed_industry` | Prominent "industry-typical assumption" tag — these are the values most likely to be wrong |
| `assumed_derived` | Inherit the most-prominent flag from inputs |
| `placeholder` | Highly visible "placeholder — pending [validation_path]" callout |
| `not_applicable` | Don't render |

Per the renewablesinfo dispatch_operating_params decision (2026-05-08): a model that surfaces LOW-confidence assumed values as KPIs without confidence badges is *worse* than a model that hides them. The misread risk is real.

---

## Anti-patterns

| Anti-pattern | Why not |
|---|---|
| **Status = `real` without specifying `observed` / `reported` / `computed`** | Loses critical distinction — measured-from-operations vs filed-with-regulator vs algebra |
| **Missing `confidence` on an assumed value** | Defeats the purpose. HIGH/MEDIUM/LOW is required for `assumed_*` statuses. |
| **`placeholder` without `validation_path`** | The whole point is to track where the real value will come from. |
| **`assumed_derived` claiming HIGH confidence when an input is LOW** | Confidence of a derived value is the *minimum* of input confidences. |
| **Using `not_applicable` when the right answer is `placeholder`** | If we plan to fill it eventually, it's a placeholder, not N/A. |
| **Editing a value without updating its status / source** | The metadata is what makes the value defensible. Treat them as a unit. |
| **Storing the value in YAML without the metadata wrapper** | The schema requires the `{value, status, source, ...}` structure. Bare values fail validation. |

---

## How this taxonomy gets enforced

1. **In Notebook 1** (Phase G) — cross-validation checks include "every leaf value has a valid status code"; "every placeholder has a validation_path"; "every assumed has confidence". Failures surface immediately.
2. **In `src/io/schemas.py`** (Phase K) — pydantic models enforce the field requirements per status code. YAML files that violate the schema fail loading.
3. **In `model_card.md`** (Phase L) — every run's card lists the status distribution. A run with high `placeholder` count or high LOW-confidence count is honest about its limitations.

---

## See also

- [consolidation plan §6](../plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle) — full discipline rationale + design context
- [README.md](./README.md) — this folder's overview
- [data/assets/README.md](../../data/assets/README.md) — where this taxonomy gets applied per-asset
- renewablesinfo dispatch_params AUDIT.md (the precedent that demonstrated this at scale): `~/code/personal/renewablesinfo/integration/dispatch_params/AUDIT.md`
