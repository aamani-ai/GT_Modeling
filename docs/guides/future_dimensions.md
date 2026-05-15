# Future Asset Profile Dimensions — Design Stubs for YAMLs to Add When Data Arrives

> **Status**: design specifications for YAMLs we know we'll need, written BEFORE the data is available. The point: when the data shows up (from a data room, MOR extraction, or financial statements), the location, schema, and downstream consumption is already designed.
>
> **Companion doc**: [`asset_profile_dimensions.md`](./asset_profile_dimensions.md) — the current 5 dimensions. This doc covers the 3 anticipated additions.
>
> **Important**: do NOT create empty/placeholder YAMLs for these. Wait until real data exists. Stubs in this doc are designs, not implementations.

---

## §1. Why "future dimensions"?

The current 5 dimensions (`identity`, `engineering`, `operating_profile`, `market_context`, `ltsa_terms`) cover **what we have data for in v1**. But we know several other meaningful aspects of a power plant exist — we just don't have the data yet for Lockport. Rather than wait until the data drops and then design under pressure, we sketch the design now.

Each future dimension here has:
- **Purpose**: what aspect of the asset it captures
- **Trigger**: when to create the actual YAML (what data event prompts it)
- **Schema**: rough structure with example field
- **Primary source**: where the data will come from
- **Downstream consumption**: how the model uses it
- **Status-tagging pattern**: what the leaves typically look like

The three anticipated dimensions are:

| YAML | Captures | Trigger |
|---|---|---|
| `outage_history.yaml` | Planned + forced outage events from operational records | MOR data extracted (Lockport: have it; just haven't loaded yet) |
| `offtake_contracts.yaml` | Revenue contracts — PPA, steam tariff, ICAP, ancillary | Steam tariff or PPA terms surface in data room |
| `fixed_opex.yaml` | Non-LTSA, non-contract operating costs — staff, taxes, insurance, capex | Financial statements or trial balance extracted |

---

## §2. `outage_history.yaml`

### §2.1 Purpose

Capture **observed outage events** — both planned (CI / MI / refurb) and forced (GT trip, HRSG leak, BOP failure) — as a structured history that the model can backtest against and use to calibrate forced-outage parameters.

### §2.2 Trigger

We have it for Lockport now (MOR daily data flags outages). Should be created when:
- An asset's MOR daily data has clear outage day markers (0 MWh + 0 gas across multiple days)
- A separate outage log is provided in the data room (NERC GADS data, plant operator logs)

### §2.3 Schema sketch

```yaml
# data/assets/<asset>/outage_history.yaml

planned_outages:
  - event_id: "CI-2018-04"
    type: "CI"  # CI / MI / refurb / planned_other
    start_date: "2018-04-10"
    end_date: "2018-04-22"
    duration_days:
      value: 12
      status: real_observed
      source: "MOR 2018-04: 12 consecutive days of 0 MWh + 0 gas"
    generators_affected:
      - "GEN1"
    documented_in:
      value: "3.4.* Lockport Unit 1 (295770) Mod HGP Final Report - Fall 2018"
      status: real_reported
    cost_owner_uncovered_usd:
      value: null
      status: placeholder
      validation_path: "Trial balance line items for 2018 Q2"

forced_outages:
  - event_id: "FO-2021-08-15"
    start_date: "2021-08-15"
    end_date: "2021-08-19"
    duration_days:
      value: 4
      status: real_observed
      source: "MOR 2021-08-15..19: unplanned 0 MWh"
    cause:
      value: "hrsg"  # gt / hrsg / bg / unknown
      status: assumed_industry
      source: "Cause classification heuristic; verify against operator log"
    cost_owner_uncovered_usd:
      value: null
      status: placeholder

summary:
  total_planned_outage_days_2021_2025:
    value: <int>
    status: real_observed
    source: "Aggregated from planned_outages list"
  forced_outage_rate_per_yr:
    value: <float>
    status: real_observed
    source: "Annual avg from forced_outages list"
  avg_planned_outage_duration_days:
    value: <float>
    status: real_computed
```

### §2.4 Primary data source

Two layers:
- **MOR daily parquet** (`data/paths/<asset>/mor_daily.parquet`) for outage day-flagging
- **Operator outage logs / vendor inspection reports** (e.g., Lockport's `3.4.* HGP outage report` PDFs) for cause classification and cost

### §2.5 Downstream consumption

Model uses for:
- **Backtest target**: do modeled forced-outage events line up with observed in count + timing?
- **Calibrate forced-outage probability**: replace generic prototype constants (`P_BG_AGE_MAX`, etc.) with asset-specific rates
- **Planned outage schedule modeling**: real planned outages should appear in N4's planned-outage spine (currently we project synthetic inspections only)
- **Validate steam-only mode count**: distinguish actual outages from steam-only days in MOR classification

### §2.6 Status-tagging pattern

- Date / type / duration: typically `real_observed` from MOR
- Cause classification: often `assumed_industry` or `assumed_derived` unless operator log directly states cause
- Cost: typically `placeholder` until trial balance extraction

### §2.7 Implementation note

Could also live as a parquet (`data/paths/<asset>/outage_events.parquet`) rather than YAML if events grow numerous (>100). The YAML pattern is good for ≤30 events with rich metadata; parquet is better for large event tables.

---

## §3. `offtake_contracts.yaml`

### §3.1 Purpose

Capture **all revenue-side contracts** — anything the plant gets paid for. Currently v1 models only spark margin (energy DA wholesale). Real plants also have:
- Steam contract with cogen host
- Long-term PPA (if any)
- ICAP / capacity market commitment
- Ancillary services bids
- PURPA above-market avoided-cost (legacy)

Without this dimension, the model's revenue side is structurally incomplete. See [`pnl_ledger.md §3.A`](../methodology/pnl_ledger.md) for the gap quantification.

### §3.2 Trigger

Create when ANY of these is available:
- Steam tariff in data room (Lockport: pending)
- PPA contract document (Lockport: PURPA status TBD)
- ICAP commitment letter or auction-clearing record
- Operator-reported ancillary services revenue

For Lockport specifically: trigger likely fires after data-room extraction of `3.1 Commercial Agreements` folder.

### §3.3 Schema sketch

```yaml
# data/assets/<asset>/offtake_contracts.yaml

# CONTRACT 1: Energy market (DA wholesale)
energy_market:
  type:
    value: "merchant"  # merchant / fixed_ppa / hybrid
    status: real_reported
    source: "EIA-860 + market_context.yaml.iso"
  primary_market:
    value: "NYISO DA"
    status: real_reported

# CONTRACT 2: Steam delivery (cogen host)
steam_contract:
  host_identity:
    value: "<industrial customer name>"
    status: real_reported
    source: "Data room: 3.1.* Commercial Agreements"
  steam_tariff_usd_per_mmbtu:
    value: <float>
    status: real_reported
    source: "Contract section X.Y"
    caveat: "Tariff may have time-of-day or season escalator"
  monthly_minimum_mmbtu:
    value: <float>
    status: real_reported
  contract_start: "YYYY-MM-DD"
  contract_end: "YYYY-MM-DD"
  reliability_penalty_clause:
    value: <string description>
    status: real_reported

# CONTRACT 3: PURPA / PPA (if applicable)
ppa:
  active:
    value: <bool>
    status: real_reported
    source: "PURPA filings + contract docs"
  type:
    value: "avoided_cost"  # avoided_cost / fixed_price / spark_adjusted
    status: real_reported
  rate_usd_per_mwh:
    value: <float>
    status: real_reported
  rate_methodology:
    value: <string>
    status: real_reported
  termination_date: "YYYY-MM-DD"

# CONTRACT 4: NYISO ICAP / capacity
icap:
  participates:
    value: <bool>
    status: real_reported
    source: "NYISO commitment records"
  zone:
    value: "Zone A"
    status: real_reported
  ucap_mw:
    value: <float>
    status: real_reported
    source: "NYISO MOC test results"
    caveat: "UCAP is derate from nameplate; often 85-95% of summer capacity"
  forward_capability_period_strip_usd_per_kw_month:
    value: <float>
    status: real_reported
    source: "NYISO auction-clearing records"
  spot_period_strip_usd_per_kw_month:
    value: <float>
    status: real_reported

# CONTRACT 5: Ancillary services
ancillary:
  participates:
    value: <bool>
    status: real_reported
  products:
    - regulation_up
    - spinning_reserve_10min
    - operating_reserve_30min
  typical_annual_revenue_usd:
    value: <float>
    status: real_observed
    source: "NYISO settlement statements"
```

### §3.4 Primary data sources

| Contract | Source |
|---|---|
| Energy market | EIA-860 + market_context.yaml |
| Steam tariff | Data room `Commercial Agreements` folder |
| PPA | Data room + PURPA filings (NYS PSC) |
| ICAP | NYISO public auction data + commitment letters in data room |
| Ancillary | NYISO settlement statements (data room) |

### §3.5 Downstream consumption

Add these as **new revenue line items** in the model:
- Energy revenue (already in spark margin via `LMP × MWh`)
- Steam revenue: `dhts_delivered_mmbtu × steam_tariff` — add to daily margin
- PPA premium (if applicable): `(ppa_rate − LMP) × MWh` — add to daily margin
- ICAP revenue: `ucap_mw × capacity_price_$/kW-month × months` — added monthly
- Ancillary: `annual_revenue / 12 / days_per_month` — added daily

Net P&L formula evolves:
```
Net P&L = Energy_spark + Steam_revenue + PPA_premium + ICAP_revenue + Ancillary
          − LTSA_owner_uncovered − Fixed_OPEX
```

vs current v1:
```
Net P&L = Energy_spark − LTSA_owner_uncovered
```

### §3.6 Status-tagging pattern

- Contract identifiers and structure: `real_reported`
- Dollar amounts: `real_reported` if from contract docs; `placeholder` if from industry benchmarks
- Capacity prices: `real_reported` for historical (NYISO auction); `placeholder` for forward

### §3.7 Implementation note

Cap rev forecasts often need their own time series (capacity prices vary by year/month). Consider:
- Static fields in YAML (UCAP, tariff structure)
- Time series in `data/paths/<asset>/capacity_prices.parquet` for $/kW-month history

---

## §4. `fixed_opex.yaml`

### §4.1 Purpose

Capture **operating costs not in LTSA** — Fixed O&M, property tax, insurance, environmental compliance, G&A, sustaining capex. v1 ignores these entirely (Net P&L is just spark − LTSA), which is why our "Real economic Net P&L" reconciliation in [`pnl_ledger.md §4`](../methodology/pnl_ledger.md) requires applying these as adjustments.

### §4.2 Trigger

Create when financial statements / trial balances are extracted that surface these line items. For Lockport: trigger likely fires when `3.2 Financial Statements` data-room folder is extracted (multiple PDFs present).

### §4.3 Schema sketch

```yaml
# data/assets/<asset>/fixed_opex.yaml

fixed_om:
  annual_total_usd:
    value: <float>
    status: real_reported
    source: "Data room: 3.2.* Financial Statements, year X"
  staffing:
    headcount:
      value: <int>
      status: real_reported
      source: "Operator's staffing plan in data room"
    annual_payroll_usd:
      value: <float>
      status: real_reported
  contracted_services_annual_usd:
    value: <float>
    status: real_reported
    caveat: "Includes things like Veracity inspections (separate from NAES O&M)"

property_tax:
  annual_usd:
    value: <float>
    status: real_reported
    source: "Niagara County assessor records + operator tax filings"
  assessed_value_usd:
    value: <float>
    status: real_reported
    caveat: "Older plants typically have lower assessed value than nameplate suggests"

insurance:
  property_annual_usd:
    value: <float>
    status: real_reported
  liability_annual_usd:
    value: <float>
    status: real_reported
  business_interruption_annual_usd:
    value: <float>
    status: real_reported
  total_annual_usd:
    value: <float>
    status: real_computed
    source: "property + liability + BI"

environmental:
  compliance_fees_annual_usd:
    value: <float>
    status: real_reported
    source: "Data room: 3.3 Environmental records"
  permit_renewal_periodic_usd:
    value: <float>
    status: real_reported
    caveat: "Title V permit renewal periodic; amortize over renewal cycle"

ga_overhead:
  spv_or_operator_allocation_annual_usd:
    value: <float>
    status: real_reported
    source: "Parent company allocation methodology in data room"

sustaining_capex:
  five_year_average_annual_usd:
    value: <float>
    status: real_observed
    source: "Capex reports in data room (e.g., 3.2.5 Lockport 2023 Capex)"
    caveat: "Lumpy — averaged over a window. Discrete projects (e.g., HRSG upgrade) handled separately."

decommissioning_reserve:
  annual_accrual_usd:
    value: <float>
    status: real_reported
    source: "Reserve fund methodology in operating agreement"

summary:
  total_annual_fixed_opex_usd:
    value: <float>
    status: real_computed
    source: "Sum of fixed_om + property_tax + insurance + environmental + ga + sustaining_capex"
```

### §4.4 Primary data sources

| Cost | Source |
|---|---|
| Fixed O&M | Operator service contract (e.g., NAES for Lockport) + payroll records |
| Property tax | County assessor + operator tax filings |
| Insurance | Operator's insurance binders in data room |
| Environmental | Title V permits + compliance reports |
| G&A | Parent company financial reports |
| Sustaining capex | Capex history (e.g., `3.2.5 Lockport 2023 Capex.pdf`) |

### §4.5 Downstream consumption

Subtract from Net P&L:
```
Real economic Net P&L = Net P&L (from offtake_contracts - ltsa_terms)
                        - fixed_om.annual_total
                        - property_tax.annual
                        - insurance.total_annual
                        - environmental.compliance_fees_annual
                        - ga_overhead.spv_allocation_annual
                        - sustaining_capex.five_year_average_annual
                        - decommissioning_reserve.annual_accrual
```

### §4.6 Status-tagging pattern

- From data-room financial statements: `real_reported`
- Industry benchmarks (e.g., EIA Form 1 $20-30/kW-yr Fixed O&M): `assumed_industry` with confidence MEDIUM
- Sustaining capex 5-year avg: `real_observed` if multi-year history; `real_computed` from individual project list

### §4.7 Why this matters for valuation

Without this dimension, you cannot answer "is this asset cash positive?" honestly. v1's −$22.6M/yr Mode A Net P&L is misleading partly because it's ALREADY before $5-10M/yr of Fixed OPEX that real Lockport pays. See [`pnl_ledger.md §4`](../methodology/pnl_ledger.md) for the survivorship-calibrated reconciliation.

---

## §5. When to add each (recap)

| YAML | Trigger event | Estimated effort once data arrives |
|---|---|---|
| `outage_history.yaml` | MOR daily + outage report PDFs extracted | Small (1-2 hours) — most data is in `mor_daily.parquet`; structured aggregation is mechanical |
| `offtake_contracts.yaml` | Steam tariff or PPA or ICAP data surfaces | Medium (half-day) — multiple sub-contracts, each needs its own section |
| `fixed_opex.yaml` | Financial statements or trial balance extracted | Medium (half-day) — requires reading multi-year financial reports |

**Rule**: don't create these YAMLs speculatively. Create them when real data exists. Stub designs in this doc are reference material, not implementations.

---

## §6. How these interact with current dimensions

```
┌──────────────────────────────────────────────────────────────────┐
│ CURRENT 5 (v1)                                                    │
├──────────────────────────────────────────────────────────────────┤
│ identity.yaml         ─┐                                          │
│ engineering.yaml      ─┼─→ Static specs                           │
│ operating_profile.yaml─┘   Observed behavior                      │
│ market_context.yaml      ─→ Market connections                    │
│ ltsa_terms.yaml          ─→ OEM contract (revenue → OEM)          │
└──────────────────────────────────────────────────────────────────┘
                          +
┌──────────────────────────────────────────────────────────────────┐
│ ANTICIPATED (this doc — future)                                   │
├──────────────────────────────────────────────────────────────────┤
│ outage_history.yaml   ─→ Observed events; backtest spine          │
│ offtake_contracts.yaml─→ Revenue contracts (energy/steam/cap/anc) │
│ fixed_opex.yaml       ─→ Non-LTSA operating costs                 │
└──────────────────────────────────────────────────────────────────┘
                          =
                          Complete asset profile
                          (covers ~95% of Net P&L drivers per pnl_ledger.md ladder)
```

When all three future dimensions are populated alongside the current 5, the model can produce a **real economic Net P&L** that passes the survivorship calibration check from [`pnl_ledger.md §4.1`](../methodology/pnl_ledger.md).

---

## §7. Cross-references

| Concept | Where |
|---|---|
| Current dimensions framework | [`asset_profile_dimensions.md`](./asset_profile_dimensions.md) |
| Status code grammar | [`../assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md) |
| Why revenue gaps matter (R3/R4 in ledger) | [`../methodology/pnl_ledger.md §3.A`](../methodology/pnl_ledger.md) |
| Why fixed-OPEX gap matters (F1-F7 in ledger) | [`../methodology/pnl_ledger.md §3.D`](../methodology/pnl_ledger.md) |
| Survivorship calibration constraint | [`../methodology/pnl_ledger.md §4.1`](../methodology/pnl_ledger.md) |
| Priority order across all gaps | [`../methodology/gaps_and_priorities.md §6`](../methodology/gaps_and_priorities.md) |
