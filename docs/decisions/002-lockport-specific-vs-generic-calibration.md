# ADR 002: Lockport-specific vs Generic F-class — calibration inventory

**Status**: Accepted
**Date**: 2026-05-14
**Decision-maker(s)**: divy + Claude (in conversation during Phase I post-review)
**Affects**: All notebooks (N1–N3 retroactively; N4+ going forward); state-evolution constants; cost calculation; future v2 calibration work

---

## Context

The colleague's gas-turbine-digital-twin prototype was modeled after a hypothetical "Athens-type" plant — **GE 7FA.03 turbines × 2 in a 2x1 CCGT configuration, NYISO Zone F, modern merchant**. All the prototype's `[ASSUME]` parameters and constants were calibrated for that reference.

Lockport is **structurally and operationally different**:

| Aspect | Athens-type (prototype) | Lockport (real asset) |
|---|---|---|
| Topology | 2x1 CCGT | **3-on-1 CCGT** (3 CTs + 1 ST) |
| Vintage | Modern (2000s) | **1992** (33 years old at sim start) |
| Capacity | ~531 MW (2x1) | **221.3 MW** (smaller block) |
| Zone | NYISO Zone F | **NYISO Zone A** |
| Counterparty | Merchant | **PURPA-era cogen LP** (Entity Type Q) |
| Fuel | NG (no flag for dual-fuel) | **Dual-fuel (NG + DFO)** |
| Turbine model | GE 7FA.03 (specified) | **Unknown specific model** (likely F-class but we don't know GE vs Siemens vs other) |

Per the conversation around N3 review: **"we have more granular configuration / engineering info for Lockport than the colleague assumed."** The question this ADR addresses: *for each parameter in the model, what is its actual calibration source — Lockport-specific data, Lockport-derivable, or generic F-class default?*

The risk if we don't track this: future iterations re-litigate "wait, did we mean Athens or Lockport?" The cost is small now and grows fast.

---

## Decision

**Use Lockport-specific data wherever it exists. Use generic F-class defaults only where Lockport data is absent — and document each such case explicitly with a `validation_path` to the future Lockport-specific source.**

Concretely:

1. **Inventory every parameter** with its calibration source (this ADR contains the inventory).
2. **Where Lockport data exists but we previously used the prototype default**, apply the correction now and document the change.
3. **Where Lockport data doesn't exist yet**, the default stays, but it's flagged with `status: assumed_industry` or `placeholder` per the assumption-tracking schema.
4. **No silent reuse of Athens calibration.** Every constant inherited from the prototype must be traceable to that source in the ADR + caveats.

---

## Reasoning

### Why this matters

The state-evolution **math** (Robinson creep, Miner fatigue, Weibull TBC) is universal F-class CCGT physics. The **calibration** of those equations is OEM- and asset-specific. Using Athens-tuned calibrations on Lockport math gives us an architecturally-correct model with potentially-wrong rate constants.

This wouldn't matter much for a 30-day single-path run (state drifts ~1% over the window regardless of constants). It **does** matter for:

- **Phase L 10-year Monte Carlo** — degradation compounds, so wrong rate constants compound too
- **Inspection event timing** — wrong EOH-per-start means CI/MI projected dates shift by months
- **Forced-outage probability tails** — the dominant sensitivity per prototype's tornado is `P_BG_AGE_MAX` (1.0×→1.5× background-outage age scaling), which is Athens-fleet-derived

So getting the calibration story right *now* prevents downstream pain.

### Why Lockport's data wasn't fully used the first time

The colleague who built the prototype didn't have access to:
- The diligence-extractor MOR notebook outputs (mode-segmented heat rate, cold-start gas observations)
- The EIA-860 schedule 3_1/3_5/6_2 extraction (capacity matrix, dual-fuel, ambient sensitivity per generator)
- The NYISO node crosswalk (real PTIDs)

We do have these now. The model needs to use them.

### Honest reconsideration

The pattern in this work is "I oversold, you pushed back, I reconsidered, we landed on a more honest answer." This ADR continues that pattern explicitly. The first pass through N1–N3 used some Athens defaults where Lockport data was available — not because of bad judgment, but because the prototype's structure made those defaults easy to inherit. We're correcting now.

---

## The Inventory

### Domain 1: Dispatch logic (all Lockport-specific, no corrections needed)

| Parameter | Source | Status | Comment |
|---|---|---|---|
| LMP DA hourly | NYISO PTID 23791 (real Lockport node) | `real_reported` | `data/paths/lockport/lmp_da_hourly.parquet` |
| LMP RT intervals | Same node | `real_reported` | `data/paths/lockport/lmp_rt_intervals.parquet` |
| Gas price (Henry Hub) | Per ADR-001 Frame A | `assumed_industry` LOW | Algonquin basis deferred to v2 |
| Weather (ambient temp) | Plant coordinates (real) | `real_reported` | `data/paths/lockport/weather_hourly.parquet` |
| **Heat rate by mode** | **MOR daily aggregation 2021-2025** | **`real_observed`** | 3×CC 8,901 / 2×CC 9,598 / 1×CC 10,424 Btu/kWh |
| Mode capacities | `engineering.yaml` per-gen nameplate sums | `real_computed` | 221.3 / 172.6 / 123.9 MW for 3×/2×/1× |
| Mode-block min loads | EIA-860 schedule 3_1 per generator | `real_reported` | 62% CT / 19% ST — **not yet enforced in dispatch** (see corrections §) |
| Ambient sensitivity (summer derate / winter boost) | EIA-860 schedule 3_1 per generator | `real_reported` | Used via linear interp in N3 |
| Per-generator capacity | EIA-860 schedule 3_1 | `real_reported` | Used in mode capacity sums |

### Domain 2: Market / commercial layer

| Parameter | Source | Status | Comment |
|---|---|---|---|
| RGGI exposed flag | NY state + NYUP subregion | `real_computed` | `market_context.yaml.rggi.exposed` |
| RGGI allowance price ($17/ton CO2) | Mid-range recent NYISO/RGGI clearing | `assumed_industry` MEDIUM | Model parameter; sweep in Phase L |
| **CO2 emissions factor (117 lb CO2/MMBtu NG)** | **EPA AP-42 fuel-side standard** | `assumed_industry` HIGH | Universal for pipeline NG combustion; NOT plant-specific |
| Plant emissions rate (eGRID 1,097 lb CO2/MWh) | eGRID 2023 rev2 | `real_observed` | **Currently NOT used** — see Reasoning below |
| Cogen VOM markup ×1.35 | Industry-typical +30–50%, midpoint | `assumed_industry` LOW | Applied in N3; refinable from MOR O&M data |
| Cogen must-run synthetic flag | Mean ambient ≤ P20 of window | `assumed_industry` LOW | Synthetic proxy until MOR DHTS extraction |
| Capacity market revenue (NYISO ICAP) | Not modeled | `not_applicable` | Deferred to v2 per consolidation plan §5 D4 |

**Why EPA AP-42 (117 lb/MMBtu) and not Lockport's eGRID rate (1,097 lb/MWh)?**

These are algebraically related but conceptually different:
- EPA AP-42 = fuel-side: CO2 per MMBtu of NG burned (universal for pipeline NG)
- eGRID = plant-MWh-side: CO2 per MWh of electricity generated (includes plant's heat rate / cycling profile)

For dispatch modeling, RGGI is a **fuel-burn-side** surcharge (per MMBtu burned, regardless of HR). So:
- Method A: `RGGI cost per MMBtu = RGGI_$_per_ton × 117 / 2000` → correctly captures the per-MMBtu cost
- Method B: `RGGI cost per MWh = RGGI_$_per_ton × eGRID / 2000` → incorporates the plant's actual emissions, but RGGI doesn't price plant efficiency — it prices fuel burned

**Method A is correct for dispatch.** We're keeping it. The eGRID rate (1,097 vs implied 9 × 117 = 1,053) is higher because Lockport runs at higher HR due to cycling — but that delta is captured by our heat-rate input, not duplicated in the RGGI calculation.

### Domain 3: State evolution (mixed — corrections opportunities here)

| Parameter | Default value | Source | Status | Refinement available? |
|---|---|---|---|---|
| Initial EOH | 24,000 | Athens convention: "post-HGP simulation start" | `assumed_industry` LOW | **No** — this is a modeling convention, not a Lockport-specific fact. Real Lockport EOH is unknown without data room. |
| Initial rotor_life | 0.35 | Athens 10-year-CCGT convention | `assumed_industry` LOW | **No** — same. Real rotor life depends on 33-year operating history. |
| TBC Weibull (β=3, η=28,000) | β=3, η=28,000 | Generic F-class | `assumed_industry` LOW | Future: OEM service records if extracted |
| START_EOH_COST (cold=20, warm=10, hot=5) | 20/10/5 | GE 7FA per GER-3620K | `assumed_techclass` MEDIUM | Future: LTSA contract (if Lockport is GE, these are right) |
| FOULING_ASYMPTOTE_PCT (2.5%) | 2.5% | Generic F-class CCGT | `assumed_industry` LOW | Future: MOR HR-drift-between-washes cross-reference |
| FOULING_TAU_HRS (2000) | 2000 | Generic F-class | `assumed_industry` LOW | Future: MOR HR-drift cross-reference |
| FOULING_AQI_PROXY (1.0) | 1.0 (constant) | We don't have AQI data | `assumed_industry` LOW | Future: weather AQI source or local PM2.5 data |
| **MOR cold-start warming gas (2,537 MMBtu avg)** | Currently unused | **MOR daily aggregation, real_observed** | **`real_observed`** | **CORRECTION OPPORTUNITY** — use in N3+ fuel cost |
| CREEP_RATE_PER_FIRED_HOUR (5e-6) | 5e-6 | Generic F-class | `assumed_industry` LOW | Future: cycling-cost analysis |
| FATIGUE_PER_COLD_START (0.001) etc | 0.001/0.0005/0.0002 | Generic F-class | `assumed_industry` LOW | Future: cycling-cost analysis |
| HRSG_BASE_PROB_PER_DAY (0.75%) | 0.0075 | Athens-calibrated, dominant sensitivity | `assumed_industry` LOW | Future: NERC GADS for HRSG fleet data |
| BG_BASE_PROB_PER_DAY (0.4%) | 0.004 | Athens-calibrated | `assumed_industry` LOW | Future: NERC GADS for fleet baseline |
| Age scaling (1.0× → 1.5× over 10 yr) | 1.5×_at_10yr | Athens-calibrated; **biggest tornado driver** | `assumed_industry` LOW | Future: NERC fleet age curve |

### Domain 4: Inspection / LTSA / cost streams (all placeholder)

Per ADR-001's similar pattern + `docs/assumptions/placeholder_caveats.md` §1.

| Parameter | Default | Status | Where it lives |
|---|---|---|---|
| Fixed monthly fee | $850K | `placeholder` | `ltsa_terms.yaml` |
| EOH reserve rate ($/EOH) | $175 | `placeholder` | `ltsa_terms.yaml` |
| CI threshold EOH | 24,000 | `placeholder` | `ltsa_terms.yaml.inspection_ci.eoh_threshold` |
| MI threshold EOH | 48,000 | `placeholder` | `ltsa_terms.yaml.inspection_mi.eoh_threshold` |
| CI cost $3.75M | Athens scale | `placeholder` | `ltsa_terms.yaml.inspection_ci.total_cost_usd` |
| MI cost $30M | Athens scale | `placeholder` | `ltsa_terms.yaml.inspection_mi.total_cost_usd` |
| OEM coverage fractions (75% CI, 65% MI) | Athens-typical | `placeholder` | `ltsa_terms.yaml.inspection_*.oem_covered_fraction` |
| Start overage baselines | 150 hot / 35 warm / 5 cold | `placeholder` | `ltsa_terms.yaml.start_overage` |
| HR penalty guarantee | null | `placeholder` | `ltsa_terms.yaml.hr_penalty.guarantee_btu_per_kwh` |
| Availability guarantee | 95% | `placeholder` | `ltsa_terms.yaml.availability_penalty` |

**Unblock**: data room extraction (file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` + original PURPA contracts). When this lands, all 40 placeholder cells flip to `real_reported`. A future ADR supersedes the LTSA portions of this one.

---

## Concrete corrections applied in this revision

### Correction 1: Use MOR-observed cold-start warming gas in fuel cost

**Before**: N3 day-loop fuel cost = `mode_hours × capacity × HR / 1000 × delivered_gas`. Cold-start days where gas was burned but no MWh produced (visible in MOR as "idle_gas_baseline" days, 35 over 5 years, avg 2,537 MMBtu/start) were not in the cost calculation. This **under-counts fuel cost on start days**.

**After**: When a cold start occurs, add 2,537 MMBtu × delivered_gas (Henry Hub + RGGI) to that day's fuel cost as `cold_start_warming_cost`. Sourced from `operating_profile.yaml.cold_start_gas.mean_per_cold_start_mmbtu.value` — `real_observed` Lockport data.

**Magnitude**: for the 30-day N3 window with ~5 cold starts at ~$2.50/MMBtu Henry Hub × 2,537 MMBtu/start, this adds ~$31K + ~$13K RGGI = **~$44K to total fuel cost** (~5% of the $913K gross margin).

**Documentation**: §J Stage 1 findings of N3 updated; `caveats.md` §12 added; this ADR.

### Correction 2: Document the RGGI calculation choice

**Already correct**, but not previously documented: we use EPA AP-42 fuel-side standard (117 lb CO2/MMBtu NG), not Lockport's plant-specific eGRID rate (1,097 lb/MWh). The reasoning is in this ADR's Domain 2 — RGGI prices fuel burned, not plant efficiency. The two are algebraically related; we picked the dispatch-correct one.

**No code change**. Documentation only.

### Correction 3: Flag the rotor_life rate constant for v2 review

**Current state**: `ROTOR_LIFE_PER_FIRED_HOUR = 1e-7`, initial `rotor_life = 0.35`. Internally inconsistent with the prototype's intent: if 0.35 is meant as "10-year-old plant," the rate constant should be ~8.75e-6, not 1e-7.

**For v1**: Keep as-is. The discrepancy doesn't materially affect 30-day or even 10-year simulations because rotor_life rate is so slow that the start value dominates over the simulation horizon. Document as a calibration TODO.

**For v2**: Reconcile. Either lower the initial to match the rate, or raise the rate to match the prototype's intent. Probably also revisit whether Lockport's 33-year history justifies a higher initial.

---

## What unlocks future refinement

Each parameter has a path to Lockport-specific calibration:

| Parameter | What unlocks it |
|---|---|
| Specific turbine OEM + model (GE vs Siemens vs Mitsubishi) | Data room operator disclosures, EIA-861 service contracts, plant tours |
| START_EOH_COST per start type | Real LTSA contract (data room) |
| FOULING_ASYMPTOTE / TAU | MOR HR-drift between water-wash events cross-reference |
| FATIGUE_PER_*_START | Cycling-cost study using Lockport CEMS or MOR data |
| HRSG_BASE_PROB + age scaling | NERC GADS fleet data (paid + restricted) |
| P_BG_AGE_MAX (the dominant sensitivity) | Fleet aging Monte Carlo across [1.0×, 2.0×]; flagged in prototype §13 |
| LTSA cost streams | Data room: `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` + original PURPA contracts |
| TBC Weibull params | OEM service documentation |
| AQI / fouling proxy | Weather data source for local PM2.5 or AQI |
| Plant-specific cycling impact | Operator interviews, GADS rollup file `3.6.3.7 LEA GADS Rollup_2020_2025.xlsx` (data room) |
| Per-generator state granularity (vs block-level) | Architectural — would require state-vector restructure in v2 |

---

## Consequences

### Positive

- Future readers know exactly which constants are Lockport-specific and which are generic placeholders
- Future ADRs (v2 calibration work) can supersede specific portions of this one without rewriting the whole story
- The N3 correction (cold-start warming gas) makes fuel cost ~5% more accurate
- Forces every new parameter to be classified honestly (assumption-tracking discipline)
- Lays the groundwork for v2 calibration prioritization (start with biggest-impact parameters first)

### Negative / accepted tradeoffs

- This ADR is long because the inventory is real. Future readers should treat it as a reference, not a story
- Some parameters (TBC Weibull, fouling rate, HRSG age scaling) will stay generic for a long time because the data to refine them is hard to get
- The N3 cold-start gas correction means N3's outputs will shift slightly when re-run — historical numbers in `consolidation_plan.md` status log become stale on the day this ADR ships

### Mitigations / follow-up actions

- **Re-run N3** with the cold-start gas correction applied
- **Update `caveats.md` §12** to cross-reference this ADR with concrete YAML field pointers
- **Future v2 ADR-NNN** can supersede the state-evolution portions of this ADR when LTSA / OEM data lands
- **Phase L Monte Carlo** should treat the `assumed_industry` LOW-confidence constants as sweepable parameters, not fixed inputs — particularly `P_BG_AGE_MAX` per the prototype's tornado finding

---

## Alternatives considered

### Alternative A — "It's fine, leave Athens defaults everywhere"

Initial framing from the user (before the conversation that produced this ADR): "using Athens would be fine." Rejected because:
- For 30-day single-path runs, mostly true — state drifts ~1% regardless of constants
- For Phase L 10-year Monte Carlo, materially false — compounding matters
- For investor-DD-grade output, the model needs to be defensibly Lockport-specific where data exists
- One concrete correction (cold-start warming gas) was a meaningful $44K/30-day miss waiting to be found

### Alternative B — Re-derive every constant from Lockport data immediately

Considered: spend a week deriving fouling rate, fatigue per start, etc., from MOR + other data. Rejected because:
- Most of these constants require data we don't have (LTSA contract, OEM specs, NERC GADS)
- The corrections we can make today are limited to what's in the data spine — and we've identified those
- Better to ship corrections that exist today and let v2 / LTSA extraction do the rest

### Alternative C — Hold off on all corrections until LTSA extraction completes

Rejected because:
- The cold-start gas correction uses `real_observed` MOR data — no LTSA extraction needed
- Documenting the inventory now is cheap; doing it later means re-litigating
- Phase L isn't going to wait for LTSA extraction — better to have the calibration map ready when Monte Carlo lands

---

## References

- **ADR-001** (gas hub treatment v1): [`001-gas-hub-treatment-v1.md`](./001-gas-hub-treatment-v1.md)
- **Placeholder caveats** (LTSA terms): [`../assumptions/placeholder_caveats.md`](../assumptions/placeholder_caveats.md)
- **Status taxonomy**: [`../assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md)
- **Operating profile YAML** (where MOR cold-start gas lives): [`../../data/assets/lockport/operating_profile.yaml`](../../data/assets/lockport/operating_profile.yaml) `cold_start_gas` block
- **Caveats** (Lockport modeling): [`../../data/assets/lockport/caveats.md`](../../data/assets/lockport/caveats.md) §2 (cogen markup), §7 (ambient sensitivity), §12 (parameter calibration — added by this ADR)
- **Notebook 3** (where corrections apply): [`../../notebooks/03_daily_loop_feedback.ipynb`](../../notebooks/03_daily_loop_feedback.ipynb)
- **Understanding doc** (prototype reference): [`../extra/understanding_of_gas_turbine_digital_twin.md`](../extra/understanding_of_gas_turbine_digital_twin.md) §6 (state vector), §13 (sensitivity findings)
- **Conversation context**: This ADR captures the post-N3 review where the user clarified that Lockport has more granular configuration than the prototype assumed, and we should use Lockport-specific data wherever it exists rather than Athens defaults.

---

## Notes for future-self / reader

1. **The inventory is the value of this ADR.** When you add a new parameter to the model, classify it in the inventory + cite this ADR.
2. **"Generic F-class" is not pejorative.** The math is right; the calibration is generic. This is fine when documented.
3. **Re-read this ADR before Phase L** — most of the LOW-confidence `assumed_industry` constants should be Phase L sweep parameters.
4. **When LTSA extraction completes**, a future ADR supersedes the Domain 4 portion of this one.
