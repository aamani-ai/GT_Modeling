# Asset Profile Dimensions — What Each YAML Captures and Why

> **The single most important data discipline in the modeling repo**: every asset under `data/assets/<asset>/` is a stack of structured YAML files (the **asset profile**) plus time-series parquets in `data/paths/<asset>/`. The asset profile is the foundation; downstream dispatch / wear / LTSA / revenue logic reads from it. **Get the profile right and most downstream accuracy follows.**
>
> This doc explains: the principle, the five current dimensions, what lives in each, where the gaps are, and when to add a new dimension.
>
> **Companion guide**: [`pulling_specs_from_powerplantsinfo.md`](./pulling_specs_from_powerplantsinfo.md) — how to populate each YAML from the platform's enriched dimensions.

---

## §1. The principle — plant profile is upstream of everything

Two kinds of data feed the model:

```
┌───────────────────────────────────────────────────────────────┐
│ ASSET PROFILE (the YAMLs in data/assets/<asset>/)              │
│   - Physical specs: capacities, heat rates, equipment          │
│   - Operational empirics: mode distribution, cold-start gas    │
│   - Market connections: ISO zone, RGGI, gas hub                │
│   - Contractual terms: LTSA, PPA, steam, capacity              │
│                                                               │
│ These describe HOW the plant responds to a given input.        │
└───────────────────────────────────────────────────────────────┘
                              +
┌───────────────────────────────────────────────────────────────┐
│ TIME-SERIES INPUTS (parquets in data/paths/<asset>/)           │
│   - LMP hourly                                                 │
│   - Gas prices                                                 │
│   - Weather                                                    │
│   - MOR-observed daily generation (when in data room)          │
│                                                               │
│ These are the changing conditions the plant operates in.       │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │   Model output (Net P&L,    │
                │   spark, LTSA, etc.)        │
                └─────────────────────────────┘
```

**Wrong inputs in time series**: model gets a different reality than what happened. But the model is otherwise behaviorally correct.

**Wrong inputs in asset profile**: model is **structurally** wrong. It doesn't matter what time series you feed it — the responses are systematically off. This is what produces over-commit, wrong LTSA accruals, missing revenue streams, and mode-mix divergence.

### §1.1 Evidence from the v1 build

We have direct evidence that profile fidelity drives downstream accuracy:

| Profile change | Downstream effect |
|---|---|
| Added `steam_only_mode` empirics + boiler_type "Db" to YAML, plumbed into N4 | **Over-commit: 2.22× → 2.07× in one change**, Net P&L improved by $36-71M across modes |
| Added `min_load_mw` constants to N4 (currently no-op but documents the constraint) | Wired for v2 partial-dispatch — without it, v2 work would have to retrofit |
| Added MOR-derived heat rates (8,901 / 9,598 / 10,424) vs prototype defaults | **Bucket A correctness** — Lockport heat rate confirmed real_observed not assumed |

If we'd never added these to the profile, no amount of dispatch-loop or LTSA-accrual refinement would have caught them. The profile is upstream.

### §1.2 The implication for scaling

For one asset (Lockport), we can hand-tune the profile. For 10, 100, 1000+ assets, **the profile setup is the bottleneck**. That's why:

- We have a **pipeline** (renewablesinfo_org) that pre-enriches federal data into typed dimensions
- We have a **guide** ([`pulling_specs_from_powerplantsinfo.md`](./pulling_specs_from_powerplantsinfo.md)) that explains how to lift from pipeline to asset profile
- We have a **status-tagging discipline** (every leaf has `value`/`status`/`source`) that surfaces uncertainty
- We have a **schema** (this doc) that says what goes where

Without all four, asset onboarding is artisanal. With them, it scales.

---

## §2. The five current dimensions at a glance

```
data/assets/<asset>/
├── identity.yaml          ← who, where, when                       (~30 leaves)
├── engineering.yaml       ← physical specs                         (~120 leaves/asset)
├── operating_profile.yaml ← empirical behavior (MOR-driven)        (~30+ leaves)
├── market_context.yaml    ← market connections                     (~40 leaves)
├── ltsa_terms.yaml        ← OEM contract (placeholder by default)  (~46 leaves)
├── caveats.md             ← operational caveats baked into data    (prose)
└── provenance.md          ← where each YAML value came from        (prose)
```

| Dimension | Captures | Primary data source | Maturity |
|---|---|---|---|
| **identity** | Who/where/what the asset is | EIA-860 Plant + admin data | High — federal data is authoritative |
| **engineering** | Physical specs (capacity, HR, equipment) | EIA-860 Generator + Multifuel + Environmental → platform enriched dimension | High — federally documented |
| **operating_profile** | Observed operational behavior (mode mix, heat rates by mode, cold-start gas, steam-only) | MOR daily data → derived | Asset-specific; only high when MOR available |
| **market_context** | ISO zone, eGRID region, RGGI applicability, gas hub | EIA Plant + ISO public data + asset-specific decision | High |
| **ltsa_terms** | LTSA contract financial terms | Data-room trial balance + PURPA contract filings | **Low** — placeholder defaults until data-room extraction |

---

## §3. `identity.yaml` — who/where/when

**Purpose**: the unique-identification + basic-fact layer. Everything else keys off the identifiers here.

**Sections**:
- `plant`: id, name, short_name, sector, status, configuration label, combined-cycle unit code
- `operator`: operating company, parent, ownership chain
- `operating_dates`: online date, planned retirement, repower status
- `location`: lat/lon, county, city, state, NERC region, balancing authority
- `cross_system_ids`: EIA Plant ID, NYISO PTID(s), EPA eGRID ID, FERC ID, Wikidata Q-ID
- `regulatory`: FERC cogen status, sector NAICS, regulatory status
- `ownership`: utility ID, current owner

**Primary fields and where to get them**:

| Field | Source | Example (Lockport) |
|---|---|---|
| `plant.id` | EIA-860 Plant Code | 54041 |
| `plant.name` | EIA-860 Plant Name | Lockport Energy Associates LP |
| `plant.configuration` | EIA-860 + Wikipedia | "3-on-1 CCGT cogeneration, dual-fuel" |
| `plant.combined_cycle_unit_code` | EIA-860 6_2 Y2024 | LEA1 |
| `operating_dates.online` | EIA-860 Generator | 1992 |
| `location.lat`, `location.lon` | EIA-860 Plant | 43.16, -78.74 |
| `cross_system_ids.nyiso_ptid` | NYISO public data | 23791 (CT block) / 323769 (ST block) |

**When to update**: rarely — only on ownership change, repower, retirement, ISO node remapping.

**Status codes typical**: mostly `real_reported` (federal data is authoritative for identifiers).

---

## §4. `engineering.yaml` — physical specs

**Purpose**: the static engineering layer. Captures the plant's physical capability — what it CAN do, before considering economics.

**Sections**:
- `plant` (block-level): total nameplate, HRSG count, CHP flag, configuration label, has_repower_planned, has_carbon_capture
- `generators` (per-generator): one block per generator (GEN1, GEN2, GEN3, GEN4 for Lockport)

**Per-generator fields** (~30 each):
- **Identity**: id, technology, prime_mover_code, ownership
- **Capacity**: nameplate, summer, winter, derate %, boost %
- **Min-load**: min_load_mw, min_load_pct
- **CC topology**: has_hrsg, can_bypass_hrsg, has_duct_burners, topping_or_bottoming
- **Boiler** (if applicable): boiler_id, boiler_type, boiler_count
- **Dual-fuel**: is_dual_fuel, secondary_energy_source, switch times, capacity_with_gas/oil
- **CHP flag**: is_chp_flagged
- **Vintage**: operating_year, time_to_full_load_min

**Primary data source**: `data/dimensions/engineering/thermal_enriched.parquet` in the renewablesinfo_org pipeline (already extracts most of these). Fall back to raw EIA-860 schedules 3_1, 3_5, 6_1, 6_2.

**Pattern when filling**:

```yaml
# Direct EIA → real_reported
nameplate_capacity_mw:
  value: 48.7
  status: real_reported
  source: "EIA-860 schedule 3_1 Y2024"

# Derived from real_observed → real_computed
min_load_pct:
  value: 62.0
  status: real_computed
  source: "min_load_mw / nameplate_capacity_mw × 100"

# Class default → assumed_techclass
vom_per_mwh:
  value: 1.02
  status: assumed_techclass
  source: "tech_class_defaults: (CT, <2000, non-aero)"
  confidence: MEDIUM
```

**When to update**: on repower events, retrofits (carbon capture, controls), capacity uprates.

**Status codes typical**: mostly `real_reported` (federal data is good here) with some `real_computed` derivations and a few `assumed_techclass` for missing federal fields.

---

## §5. `operating_profile.yaml` — empirical operational behavior

**Purpose**: this is where **observed plant behavior** lives, distilled from MOR or operational data. It bridges what the plant CAN do (engineering) with what it ACTUALLY does (dispatch reality). Most asset-specific intelligence concentrates here.

**Sections** (extensible — Lockport's current set):
- `heat_rate_by_mode` — volume-weighted HR per operating mode (3xCC, 2xCC, 1xCC)
- `cross_validation` — checks against eGRID public values
- `cold_start_gas` — MOR-derived gas consumed during cold-start warming (Lockport-specific calibration vs prototype default)
- `annual_generation` — typical pattern, year-to-year variance
- `mode_classifier` — thresholds for inferring operating mode from net output
- `dhts` — daily heat tape schedule (cogen steam delivery pattern)
- **`steam_only_mode`** — NEW: when the plant operates via duct burner with 0 MWh
- `modeling_notes` — how downstream code consumes this data

**Why this is the most-valuable dimension**:
1. It encodes **observed reality**, not just specs
2. Most fields are `real_observed` (highest confidence in the status taxonomy)
3. Without MOR data, this dimension is sparse → fallback to engineering+assumed values, which causes the modeling errors we documented (steam-only mode missing, etc.)

**Status codes typical**: mostly `real_observed` if MOR is available; `assumed_techclass` if not.

**When you fill this**:
- After MOR data extraction is complete (via diligence-extractor pattern)
- Should also include any **observed empirics from outside MOR** — e.g., known dispatch patterns from NYISO settlement data, or operator-reported maintenance windows

**Primary data source**: MOR daily parquet (`data/paths/<asset>/mor_daily.parquet`) — NOT in the platform pipeline.

**Worked example — `steam_only_mode` block (Lockport)**:

```yaml
steam_only_mode:
  days_observed:
    value: 460
    status: real_observed
    source: "MOR daily 2021-2025: 460 days with 0 MWh + non-zero gas + non-zero DHTS"
  share_of_all_days_pct:
    value: 25.2
    status: real_observed
    source: "460 / 1826"
    caveat: "1 in 4 days at Lockport operates in steam-only mode. ..."
  gas_mmbtu_per_day_median:
    value: 871
    status: real_observed
    source: "Median of total_gas_mmbtu across 460 steam-only days"
  mechanism:
    value: "HRSG duct burner — gas fired directly into HRSG, bypasses CTs"
    status: real_reported
    source: "EIA-860 6_2 Y2024 — boiler_type='Db' for boiler ID 4 linked to GEN4"
```

This block alone is what enabled the steam-only branch in N4 — without it, no amount of model code changes would have helped.

---

## §6. `market_context.yaml` — market connections

**Purpose**: where the plant sells, what regulatory regime it's in, what fuel inputs it uses.

**Sections**:
- `iso`: ISO/RTO name, control area, node identifier
- `pricing`: LMP node ID, zone, real-time vs day-ahead market participation
- `emissions`: eGRID subregion, CO2/NOx/SO2 factors (Lockport: NYUP)
- `capacity_market`: ICAP/RA program eligibility (NYISO ICAP details)
- `rggi_program`: applicability, price assumption
- `gas_market`: pipeline, hub, basis (Lockport: Tennessee Gas Pipeline; v1 modeling uses Henry Hub per ADR-001)
- `dual_fuel_market`: oil delivery, storage capacity

**Primary data source**: EIA-860 Plant + ISO public data + asset-specific decisions (ADRs).

**When to update**: rarely — only on market structure changes (e.g., NYISO capacity market rule change, RGGI price reset).

**Status codes typical**: `real_reported` for ISO and emissions data; `assumed_industry` for forward gas-hub price assumptions; `placeholder` if the gas hub treatment is still pending (Lockport: Henry Hub per ADR-001).

---

## §7. `ltsa_terms.yaml` — OEM/operations contract terms

**Purpose**: financial structure of the Long-Term Service Agreement with the OEM. Drives the LTSA cost stream in the model.

**Current scope** (Lockport's current pattern):
- `fixed_fee` — monthly fee + escalation
- `eoh_reserve` — $/EOH reserve rate
- `inspection_ci` / `inspection_mi` — costs + OEM share + outage duration + EOH thresholds
- `start_overage` — annual baselines + per-excess-start charges
- `availability_penalty` — guarantee % + penalty formula
- `hr_penalty` — guarantee Btu/kWh + tolerance + penalty multiplier
- `forced_outage_coverage` — which causes (GT/HRSG/BG/ST) are OEM-covered vs owner-uncovered

**Status codes typical**: ALL `placeholder` until data-room extraction completes. This is the lowest-maturity dimension in v1.

**When to update**: once data-room extraction completes (`3.X Trial Balances` workbooks + original PURPA contract filings).

**Primary data source**: data-room (NOT in platform pipeline; asset-specific).

### §7.1 Where contracts OTHER than OEM-LTSA go (the gap)

This dimension is **named for the OEM/LTSA contract specifically**, but real plants have other contracts that v1 doesn't have a clean home for:

| Contract type | Where it currently lives (or doesn't) | Proposal |
|---|---|---|
| **OEM Long-Term Service Agreement** | `ltsa_terms.yaml` ✓ | (no change) |
| **Steam tariff with cogen host** | Nowhere; DHTS pattern is in `operating_profile.yaml` but tariff $ is missing | Add `cogen_host_contract.yaml` or section in new `offtake_contracts.yaml` |
| **PPA with offtaker** | Nowhere; PURPA mention in `ltsa_terms.yaml.contract_metadata` | Same as above |
| **NYISO ICAP capacity contract** | Nowhere | Same as above |
| **Gas supply contract** | `market_context.yaml.gas_market` partial | Could expand or move to `offtake_contracts.yaml` |
| **Insurance / property tax / O&M staffing** | Nowhere | Add `fixed_opex.yaml` (separate from LTSA) |

**Recommendation for future**: when a plant has any of these as live contractual terms (with $ amounts), introduce **two new YAMLs**:
- `offtake_contracts.yaml` — outbound: steam tariff, PPA, ICAP, ancillary services revenue
- `fixed_opex.yaml` — costs not in LTSA: Fixed O&M, property tax, insurance, sustaining capex

For Lockport v1, these are still TBD/placeholder so we haven't added the files yet. **When the data room provides the steam tariff or capacity payments**, that's the trigger.

---

## §8. Two supporting files

### §8.1 `caveats.md`

Free-form prose. The "things baked into the data that future-self / the team must remember." Examples from Lockport:
- Cogen VOM markup (×1.35) is industry mid-range, not asset-calibrated
- DHTS pattern is synthetic temp-based proxy in v1; real DHTS needs separate extraction
- Dual-fuel switching never fires in v1 (capability is there; logic isn't)
- RGGI uses EPA AP-42 fuel-side, not plant-side eGRID (would double-count)
- Gas hub for v1 is Henry Hub per ADR-001 (Algonquin basis deferred)

**When to update**: any time a non-obvious convention is baked into a YAML value or downstream code. Don't trust future-self to remember.

### §8.2 `provenance.md`

Table of where each YAML value came from. Useful for diligence/audit: when someone asks "where did 8,901 Btu/kWh come from?", `provenance.md` answers without having to dig through git history.

**When to update**: any time you add or change a YAML value, update the corresponding row.

---

## §9. Where ambiguous fields go (decision tree)

When you have a piece of data and aren't sure which YAML owns it:

```
Is the data a unique identifier (plant ID, NYISO node, owner)?
└─→ identity.yaml

Is it a physical/equipment specification (capacity, heat rate, fuel type, equipment present)?
└─→ engineering.yaml

Is it an empirically-observed operational pattern (mode mix, cold-start gas, DHTS)?
└─→ operating_profile.yaml

Is it about the markets the plant sells into (ISO, zone, RGGI, gas hub)?
└─→ market_context.yaml

Is it about the LTSA / OEM contract specifically (fixed fee, inspection cost, outage coverage)?
└─→ ltsa_terms.yaml

Is it a non-LTSA contract (steam tariff, PPA, ICAP)?
└─→ TBD — add new offtake_contracts.yaml when first needed

Is it a non-OEM cost (Fixed O&M, property tax, insurance)?
└─→ TBD — add new fixed_opex.yaml when first needed

Is it a non-obvious convention baked into how the data is used?
└─→ caveats.md (prose, not YAML)

Is it the source/lineage of a value?
└─→ provenance.md
```

---

## §10. When to add a NEW dimension (new YAML file)

Triggers that justify creating a new YAML file in `data/assets/<asset>/`:

1. **Multiple new fields** that don't naturally belong to any existing dimension (3+ fields → consider new file; 1-2 → extend existing)
2. **Different update cadence** than existing dimensions (e.g., a contract that gets re-negotiated annually vs equipment that lasts decades)
3. **Different data source / extraction method** (e.g., insurance from a PDF vs EIA from XLSX)
4. **Different status-tagging pattern** (e.g., all `placeholder` until data room — like `ltsa_terms.yaml`)

Don't add a new YAML for one-off fields — extend the closest existing dimension.

**Currently anticipated new dimensions** (when first asset needs them):
- `offtake_contracts.yaml` — when an asset has real steam tariff or capacity contract data
- `fixed_opex.yaml` — when an asset has Fixed O&M or property tax data from financial statements
- `outage_history.yaml` — when an asset has multi-year planned + forced outage records (could also live in `data/paths/<asset>/outage_events.parquet`)

---

## §11. The full data layer for an asset (recap)

```
data/
├── assets/<asset>/
│   ├── identity.yaml          ← who/where/when
│   ├── engineering.yaml       ← physical specs
│   ├── operating_profile.yaml ← empirical behavior
│   ├── market_context.yaml    ← market connections
│   ├── ltsa_terms.yaml        ← OEM contract
│   ├── caveats.md             ← non-obvious conventions
│   ├── provenance.md          ← source lineage
│   ├── (offtake_contracts.yaml) ← future: PPA / steam / ICAP
│   └── (fixed_opex.yaml)        ← future: Fixed O&M / tax / insurance
│
├── paths/<asset>/
│   ├── lmp_da_hourly.parquet  ← time series: market prices
│   ├── gas_price_history.parquet
│   ├── weather_hourly.parquet
│   ├── mor_daily.parquet      ← time series: observed operation
│   └── README.md              ← describes each time-series file
│
└── tech_class_defaults/
    ├── dispatch_params_lookup.parquet ← cross-asset reference (NOT per-asset)
    └── refs/
```

**Asset profile = the YAMLs + caveats + provenance.**
**Asset spine = the parquet time series.**
**The combination is everything the model needs for one asset.**

---

## §12. Setup checklist for a new asset

(Cross-references `pulling_specs_from_powerplantsinfo.md` §4 which has the implementation-level checklist; this one is dimension-by-dimension.)

```
[ ] identity.yaml          plant ID, name, location, dates, operator, IDs
[ ] engineering.yaml       Pull from platform thermal_enriched.parquet for 60+ fields
                           Audit: duct burner? bypass? min-load? dual-fuel? boiler type?
[ ] market_context.yaml    ISO node, eGRID, RGGI, gas hub decision (ADR if needed)
[ ] operating_profile.yaml MOR-derived: heat rates, mode mix, cold-start gas, steam-only
                           (Only fillable if asset has MOR data in diligence-extractor)
[ ] ltsa_terms.yaml        Start with Athens placeholder defaults; status=placeholder
                           Update once data-room trial balance extracted
[ ] caveats.md             Document non-obvious conventions
[ ] provenance.md          Source lineage for every YAML value
[ ] data/paths/<asset>/    Pull LMP, gas, weather; extract MOR daily if available
[ ] Test                   Run tests/test_<asset>_static_profile.py
[ ] Verify                 Run N1 to validate spine loads cleanly
[ ] Asset-specific docs    Update any methodology / backtest docs with asset findings
```

---

## §13. Plant archetypes — the prior that makes dimensions interpretable

**The single most useful prior in plant modeling**: knowing the archetype before reading any values. A 10% capacity factor means very different things for a peaker (over-running for an idle asset) vs a cogen (driven by steam-host needs). Without an archetype tag, every dimension needs context derived from scratch.

### §13.1 Why archetype matters

Plant archetype drives:

| What it drives | Why |
|---|---|
| **Revenue mix expectations** | Peaker = ICAP-heavy; baseload = energy-spark heavy; cogen = steam + capacity |
| **LTSA contract structure** | Different EOH multipliers, different inspection cadence, different fixed-fee scales |
| **Wear regime** | Peaker = cycling-driven (df, fatigue); baseload = creep-driven (dc); cogen = mixed + steam-side wear |
| **Bucket B calibration defaults** | Athens-prototype state-evolution constants are appropriate for some archetypes more than others |
| **What valuation questions matter** | Peaker: "will ICAP prices clear?"; baseload: "what's HR trajectory?"; cogen: "is the steam contract solid?" |
| **What to skip in modeling** | Peaker doesn't need fine HR-by-mode detail; baseload doesn't need cycling cost obsession |

### §13.2 Standard archetype taxonomy

Eight common categories (proposed controlled vocabulary):

| Archetype | Typical CF | Dominant revenue | Wear regime | Modeling drivers | Lockport-fit? |
|---|---|---|---|---|---|
| **peaker** | < 10% | Capacity (ICAP) | Start-cycling | ICAP price; fast-start cost | No — runs longer streaks than typical peaker |
| **mid_merit** | 15–40% | Energy spark | Mixed | Spark spread × hours; cycling | Partially |
| **baseload** | 60–85% | Energy spark | Creep | HR degradation; MI cost | No |
| **cogen** | 5–60% (steam-driven) | Steam + capacity | Cycling + steam-side | Steam-contract reliability; must-run economics | **Yes — Lockport is here** |
| **qf_purpa** | varies | Above-market PPA | Whatever PPA dictates | PPA rate vs market; PPA term | **Possibly (status TBD)** |
| **rmr** | varies | Reliability payments | Driven by grid mandate | RMR contract terms; cost-of-service basis | No |
| **battery** | N/A (arb cycles) | Arbitrage + capacity | Cycle-driven degradation | LMP volatility; round-trip efficiency | Not applicable to gas plants |
| **hybrid** | varies | Multi-stream | Mixed | Combined logic per component | No |

**Lockport's classification**: most accurately **"cogen + qf_purpa (TBD)"** — low CF (10%), steam-driven must-run pattern, possibly active PURPA-era PPA. The dual tag captures both the operational character and the contract context.

### §13.3 Where it should live in the profile

**Proposal — not yet implemented for Lockport** (per consolidation plan §5 D4, v1 is single-asset; multi-asset abstraction comes after 2-3 deals end-to-end):

Add a `plant.archetype` block to `identity.yaml`:

```yaml
# data/assets/<asset>/identity.yaml

plant:
  id: 54041
  name: "Lockport Energy Associates LP"
  # ... existing fields ...

  archetype:
    primary:
      value: "cogen"
      status: real_computed
      source: "Inferred from EIA-860 is_chp=Y + MOR 25% steam-only days + 10% CF"
      confidence: HIGH
    secondary:
      value: "qf_purpa"
      status: placeholder
      source: "PURPA contract status not yet confirmed from data room"
      validation_path: "Data room: 3.1 Commercial Agreements"
      confidence: LOW
    operational_modifier:
      value: "low_cf"
      status: real_observed
      source: "MOR 2021-2025: avg 188 GWh/yr at 221 MW nameplate → ~10% CF"
      caveat: "10% CF is unusual for cogen — typical cogens run 30-60% CF. This is structurally a low-CF cogen, which has implications for revenue mix (capacity becomes more important relative to energy)."
```

### §13.4 How modeling code would consume archetype

Once archetype tagging is in place, downstream defaults can be archetype-scoped:

```python
ARCHETYPE_DEFAULTS = {
    "peaker": {
        "vom_per_mwh": 2.50,           # Higher than baseload
        "start_cm_cold_per_mw": 100,   # Higher cycling cost
        "expected_starts_per_yr": 200, # Many starts
        "ltsa_fixed_monthly_factor": 0.3,  # Peakers often have smaller LTSA fees
        "revenue_mix": {"energy": 0.20, "capacity": 0.75, "ancillary": 0.05},
    },
    "baseload": {
        "vom_per_mwh": 0.80,           # Lower
        "start_cm_cold_per_mw": 60,    # Less critical
        "expected_starts_per_yr": 15,  # Few starts
        "ltsa_fixed_monthly_factor": 1.0,  # Standard LTSA
        "revenue_mix": {"energy": 0.85, "capacity": 0.12, "ancillary": 0.03},
    },
    "cogen": {
        "vom_per_mwh": 1.38,           # Cogen markup +30-50%
        "must_run_logic": "steam_obligation_driven",
        "supports_steam_only_mode": True,
        "ltsa_fixed_monthly_factor": 0.6,  # Cogen LTSAs often smaller
        "revenue_mix": {"energy": 0.35, "steam": 0.30, "capacity": 0.30, "ancillary": 0.05},
    },
    # ... etc
}

# At asset-load time:
archetype = v(identity["plant"]["archetype"]["primary"])
defaults = ARCHETYPE_DEFAULTS[archetype]
# Now downstream code can fall back to archetype defaults for any
# field marked status=assumed_techclass without an asset-specific value
```

This is **the core extensibility pattern** for multi-asset scaling — every new asset gets onboarded with an archetype tag, and the model has reasonable defaults for that archetype before any asset-specific calibration.

### §13.5 What goes deeper in the learning folder

This section gives the high-level taxonomy. The **deep dive on each archetype** — its typical revenue patterns, LTSA conventions, wear regimes, valuation drivers, common modeling traps — belongs in `docs/learning/plant_archetypes/` when knowledge-base work resumes. Topics for that future doc set:

| Doc | Content |
|---|---|
| `01_peaker_economics.md` | How peakers make money (capacity dominant), why heat rate matters less, ICAP forecast risk |
| `02_baseload_economics.md` | Spark spread + HR degradation focus, MI cost cycle, planned-outage importance |
| `03_cogen_economics.md` | Steam revenue mechanics, DHTS constraint logic, why CCGT-cogens have flexibility (duct burners) |
| `04_qf_purpa.md` | PURPA contract mechanics, above-market avoided-cost, contract expiration cliff |
| `05_rmr.md` | Reliability-must-run designations, cost-of-service tariffs |
| `06_lifecycle_phases.md` | Greenfield → ramp-up → mature → late-life → retirement; how modeling differs |

For now: the taxonomy in §13.2 + the asset profile field design in §13.3 is enough. Deep archetype guidance is a Phase L+ workstream.

### §13.6 Lockport in the archetype frame

Putting it all together for Lockport:

- **Primary**: cogen (high confidence)
- **Secondary**: qf_purpa (low confidence — TBD on contract status)
- **Modifier**: low_cf (high confidence — ~10% CF observed)

What this tells us about modeling Lockport:
- Steam revenue is structurally important → **must add `offtake_contracts.yaml` when data available**
- Low CF + steam-driven → **must-run logic matters more than dispatch optimization**
- Duct burner + steam-only mode → **adds operational flexibility beyond standard CCGT**
- 1992 vintage + PURPA possibly → **LTSA structure likely different from modern merchant CCGT** (lower fixed fee likely)
- Capacity revenue should add 30%+ to revenue stream → **NYISO ICAP modeling priority is HIGH**

This is the kind of pattern-recognition that becomes automatic once archetypes are in the framework, but is hard to articulate without it.

---

## §14. Anticipated future dimensions

See [`future_dimensions.md`](./future_dimensions.md) for design specs on three YAMLs we expect to add when data arrives:

- **`outage_history.yaml`** — observed planned + forced outage events
- **`offtake_contracts.yaml`** — revenue contracts (energy / steam / PPA / capacity / ancillary)
- **`fixed_opex.yaml`** — non-LTSA operating costs (Fixed O&M, property tax, insurance, capex)

These are not v1 deliverables. Design specs exist so when data shows up, location + schema + downstream consumption is pre-decided.

---

## §15. Cross-references

| Concept | Where |
|---|---|
| Step-by-step asset onboarding from the platform | [`pulling_specs_from_powerplantsinfo.md`](./pulling_specs_from_powerplantsinfo.md) |
| Anticipated future dimensions (outage / offtake / fixed_opex) | [`future_dimensions.md`](./future_dimensions.md) |
| Status code grammar (9 codes) | [`../assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md) |
| ADRs for substantive decisions | [`../decisions/README.md`](../decisions/README.md) |
| Architecture — how dimensions are consumed by the model | [`../methodology/architecture.md`](../methodology/architecture.md) |
| Backtest findings (steam-only mode discovery) | [`../methodology/extra/backtest_findings.md`](../methodology/extra/backtest_findings.md) |
| Glossary of model terms | [`../methodology/glossary.md`](../methodology/glossary.md) |
| Lockport YAMLs (worked reference) | [`../../data/assets/lockport/`](../../data/assets/lockport/) |
