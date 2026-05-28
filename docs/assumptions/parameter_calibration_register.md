# Parameter Calibration Register

> **What this is.** The tracked inventory of the engine's constants — `current value · status · source · sensitivity rank · defensibility target · blocked-on · owner`. Operationalizes [`parameter_calibration_plan.md`](../plans/parameter_calibration_plan.md) §3.
>
> **How to read it.** Two tiers:
> 1. **[§3 Priority register — Gen 1 cited rows](#section-3)** — the 17 high-impact constants we've already attached a citation / target to. These are the rows defensible enough to anchor a v2 conversation. Each carries an inline reference key (e.g. `[GER-3620]`); full URLs in [§9 References](#section-9).
> 2. **[§4 Inventory backlog](#section-4)** — the broader set (~50 distinct constants, ~80 rows across 6 sub-tables) reconstructed from `wear_mechanics.md`, `outage_mechanics.md`, `src/gt_engine/engine.py`, and `data/assets/lockport/ltsa_terms.yaml`. Rows are **pending** sensitivity-rank, citation, or calibration. The backlog uses a compact column set (constant · current value · status · source · rank · blocked-on); the required full schema (`defensibility target` + `owner`) is satisfied via the section-level defaults in the per-section header. Rows already in §3 are referenced by anchor, not duplicated.
>
> **Status**: Gen 1.1 (2026-05-28) — first cited pass + load-temp paper landing. The paper earlier referenced as `[Friday]` (a placeholder named after the day the 2026-05-22 advisory meeting fell on) was acquired 2026-05-27 and is **Saturday & Isaiah (2018)** — see [§9 References](#section-9). It directly informs §3.2 (creep) and surfaces a cross-check flag on §3.7 (ambient sensitivity ~17× higher in the paper than our current value; sensitivity sweep needed before adoption). It does **not** address fatigue (§3.3), TBC (§3.5), or aging multipliers (§3.10) — those rows now point to `vendor-spec` / `literature` instead of the paper. v2 work continues per [§5 Next execution pass](#section-5).

---

<a id="section-1"></a>
## §1. v1 philosophy — sourced/justified, not "the true value"

The achievable goal is to move each high-impact constant from *"unsourced placeholder"* to *"here's the source / target / sensitivity."* Tiers (from `parameter_calibration_plan.md` §2):

| Tier | Source | Status earned |
|---|---|---|
| **1 — measured** | asset's MOR / data room / GADS / SCADA | `real_observed` / `real_reported` |
| **2 — vendor / literature** | OEM specs (GER-3620), Kumar 2012, F-class published data, **Saturday & Isaiah (2018) load-temp paper** | `assumed_vendor` / `assumed_industry` with citation |
| **3 — calibrated** | tune to a known target — wear → MI timing matches contract interval; `P_forced` → modeled EFOR matches MOR/GADS | `assumed_derived` (target recorded) |

For Lockport (3-on-1 1992 F-class cogen, ADR-002 Bucket-B): most wear / hazard constants live in Tier 2; most LTSA monetary constants are Tier-1 candidates (data-room blocked) currently sitting at Athens-prototype placeholders.

---

<a id="section-2"></a>
## §2. Column semantics

| Column | Meaning |
|---|---|
| **constant** | Symbol / YAML path / engine constant. Code constants are in `src/gt_engine/engine.py`. |
| **current value** | What v1 uses today. |
| **status** | Per [`status_taxonomy.md`](status_taxonomy.md). The 9-code grammar. |
| **source** | Where the current value came from (e.g. "Athens prototype default", "GER-3620 standard CI", "literature default; cross-check vs Saturday-Isaiah 2018"). |
| **sensitivity rank** | High / Medium / Low / TBD. High = Phase-L tornado top quartile or theoretically dominant. TBD = pending the §5 sensitivity sweep. |
| **defensibility target** | The tier this row should land at (Tier 1 measured / Tier 2 cited / Tier 3 calibrated). |
| **blocked-on** | What needs to land before this row can graduate: `data-room`, `GADS`, `vendor-spec`, `literature`, `sensitivity-sweep`, `none`. (Earlier drafts used `friday-paper` as a placeholder for the load-temp paper — that paper has since landed as Saturday & Isaiah 2018; see §3.7 cross-check.) |
| **owner** | The team / person on the hook. Default for v1: **modeling**. Data-room blocked rows: **diligence**. |

> **Backlog compaction (§4)**: to keep the broader inventory readable, the §4 sub-tables show `constant · current value · status · source · rank · blocked-on`. **Defensibility target** defaults to **Tier 2 (cited)** for wear/hazard constants and **Tier 1 (measured/data-room)** for LTSA monetary constants — overridden inline only where it differs. **Owner** defaults to **modeling** for code constants and **diligence** for `ltsa_terms.yaml` rows.

---

<a id="section-3"></a>
## §3. Priority register — Gen 1 cited rows (17 rows)

The high-impact constants we've already attached a target / citation to. These are the rows worth defending in a v2 review.

| # | Constant | Current value | Status | Source / citation | Sensitivity rank | Defensibility target | Blocked-on | Owner |
|---|---|---|---|---|---|---|---|---|
| 3.1 | `START_EOH_COST` (cold/warm/hot) | 20 / 10 / 5 EOH per start | `assumed_industry` | GE GER-3620 equivalent-hours convention `[GER-3620]` | **High** — sets EOH→MI timing | Tier 2 cited | none | modeling |
| 3.2 | `CREEP_RATE_PER_FIRED_HOUR` | 5e-6 /h | `assumed_industry` | Robinson cumulative-damage proxy; F-class hot-section creep `[GER-3620]`; **analog evidence** for the load × ambient creep coupling `[Saturday-Isaiah-2018]` (LM2500+ aero-derivative, Larson-Miller) | High — drives `P_creep` & life | Tier 2 cited (Tier 3 calibrate to MI) | sensitivity-sweep | modeling |
| 3.3 | `FATIGUE_PER_COLD_START` | 0.001 /start | `assumed_industry` | Miner's-rule per-cycle damage; F-class fatigue literature `[GER-3620]` | **High** — Phase-L tornado top driver | Tier 2 cited | sensitivity-sweep | modeling |
| 3.4 | `TRIP_MAINTENANCE_FACTOR` | 8.0 × cold-start damage | `assumed_vendor` | GER-3620 trip-from-load factored-start convention `[GER-3620]` (ADR-007) | High when trip rate non-zero | Tier 2 cited | none | modeling |
| 3.5 | `TBC_WEIBULL_BETA` / `TBC_WEIBULL_ETA` | β=3, η=28,000 h | `assumed_industry` | Standard TBC oxidation Weibull fit; F-class coating life `[GER-3620]` (NOT addressed by `[Saturday-Isaiah-2018]` — creep-only) | **High** — Phase-L tornado dominant | Tier 2 cited | vendor-spec | modeling |
| 3.6 | `FOULING_TAU_HRS` / asymptote | 2000 h / 2.5% | `assumed_industry` | Compressor-fouling exponential approach (industry rule-of-thumb) `[Kumar2012]` | **High** — Phase-L tornado top driver | Tier 2 cited (Tier 3 calibrate to MOR HR) | none | modeling |
| 3.7 | `AMBIENT_WEAR_SENS_PER_F` | 0.004 /°F | `assumed_industry` | Literature default for hot-section ambient sensitivity (ADR-006). **Cross-check flag** vs `[Saturday-Isaiah-2018]`: paper measures 12.33%/°C ≈ 6.85%/°F creep-life decrease on LM2500+ aero-derivative — **~17× higher** than current 0.4%/°F. Heavy-duty F-class vs aero-derivative likely explains some of the gap (thicker blade alloys, lower TIT margin) but not all. Sensitivity sweep needed before adopting any new number. | Medium (Lockport mean ≈34°F → modest swing in current calibration; could be material if sweep validates the higher coefficient) | Tier 2 cited | sensitivity-sweep | modeling |
| 3.8 | `HRSG_BASE_PROB_PER_DAY` | 0.0075 /day | `assumed_industry` | Industry CCGT HRSG forced-outage baseline; cross-check to NERC GADS Class CC `[NERC-GADS]` | **High** — dominant for low-CF Lockport | Tier 3 calibrated (target: MOR EFOR) | GADS | modeling |
| 3.9 | `BG_BASE_PROB_PER_DAY` | 0.004 /day | `assumed_industry` | Balance-of-plant baseline; NERC GADS Class CC `[NERC-GADS]` | **High** — co-dominant with HRSG | Tier 3 calibrated (target: MOR EFOR) | GADS | modeling |
| 3.10 | `HRSG_AGE_MULT_MAX` / `BG_AGE_MULT_MAX` | 1.5× / 1.5× | `assumed_industry` | Aging-multiplier convention (prototype) — NOT addressed by `[Saturday-Isaiah-2018]` (creep-only paper); needs separate aging-curve literature or GADS-derived calibration | **High** — Phase-L tornado #1 driver | Tier 2 cited | literature | modeling |
| 3.11 | `AGING_WINDOW_YEARS` (sim-start anchor) | 10.0 yr from 2017 | `assumed_industry` | Modeling convention — **flagged**: should anchor to 1992 vintage, not sim-start (`parameter_calibration_plan.md` §1) | High — first-order on outage rate | Tier 3 calibrated | none (modeling decision) | modeling |
| 3.12 | Initial `state.eoh` | 24,000 h | `assumed_industry` | Modeling convention "post-HGP, mid-clock" — **flagged**: MI fires ~2025 only because EOH starts at 24k (`parameter_calibration_plan.md` §1) | **High** — sets when MI fires | Tier 1 measured (asset history) | data-room | diligence |
| 3.13 | Initial `state.rotor_life` | 0.35 | `assumed_industry` | Modeling convention (mid-life) | Medium | Tier 1 measured | data-room | diligence |
| 3.14 | `inspection_ci.eoh_threshold` | 24,000 EOH | `placeholder` | GE 7FA.03 GER-3620K standard CI interval `[GER-3620]` (Athens default) | High — schedules CI events | Tier 1 measured (contract) | data-room | diligence |
| 3.15 | `inspection_mi.eoh_threshold` | 48,000 EOH | `placeholder` | GE 7FA.03 GER-3620K standard MI interval `[GER-3620]` (Athens default) | **High** — schedules MI (dominant LTSA cost) | Tier 1 measured (contract) | data-room | diligence |
| 3.16 | `inspection_mi.total_cost_usd` | $30,000,000 | `placeholder` | Athens prototype default | **High** — single largest LTSA stream (#1 v2 priority) | Tier 1 measured | data-room | diligence |
| 3.17 | `START_CM_USD_PER_MW` (cold/warm/hot) | 79 / 55 / 35 $/MW | `assumed_vendor` | Kumar 2012 Table 1-1 "Gas-CC" 2011 USD `[Kumar2012]` | Medium — drives Mode B/C wear hurdle | Tier 2 cited | none | modeling |

**Citation key inline above → URLs in [§9 References](#section-9).**

---

<a id="section-4"></a>
## §4. Inventory backlog — pending citation/calibration

Broader inventory across 6 sub-tables. Rows already covered in §3 are linked by `→ §3.N` rather than duplicated. Compact column set per [§2](#section-2) backlog note.

### §4.1 Wear / state-evolution constants (`wear_mechanics.md` §7, `engine.py` lines 195–272)

| Constant | Current value | Status | Source | Rank | Blocked-on |
|---|---|---|---|---|---|
| `START_EOH_COST` | → §3.1 | — | — | — | — |
| `FOULING_ASYMPTOTE_PCT` | 2.5% | `assumed_industry` | Athens prototype | High | vendor-spec |
| `FOULING_TAU_HRS` | → §3.6 | — | — | — | — |
| `FOULING_AQI_PROXY` | 1.0 (no AQI scaling) | `assumed_industry` | Athens prototype; v1 simplification | Low | none |
| `hr_recov` rate | 0.001 %/h | `assumed_industry` | Athens prototype | Medium — drives HR creep | vendor-spec |
| `CREEP_RATE_PER_FIRED_HOUR` | → §3.2 | — | — | — | — |
| `CREEP_BUDGET` | 1.0 (life-fraction) | `assumed_industry` | Robinson convention | Low (definitional) | none |
| `FATIGUE_PER_COLD_START` | → §3.3 | — | — | — | — |
| `FATIGUE_PER_WARM_START` | 0.0005 /start | `assumed_industry` | Athens prototype; Miner's-rule scaling | High | sensitivity-sweep |
| `FATIGUE_PER_HOT_START` | 0.0002 /start | `assumed_industry` | Athens prototype; Miner's-rule scaling | High | sensitivity-sweep |
| `FATIGUE_BUDGET` / `COMB_BUDGET` | 1.0 / 1.0 | `assumed_industry` | Miner convention | Low (definitional) | none |
| `D_LIM` (creep-fatigue interaction) | 0.7 | `assumed_industry` | Athens prototype convention | Low — never fires on Lockport paths | none |
| `P_COMBUSTION_INFLECTION` | 0.6 (df threshold) | `assumed_industry` | Hockey-stick hazard convention | Medium | sensitivity-sweep |
| `P_COMBUSTION_SCALE` | 0.10 | `assumed_industry` | Hockey-stick hazard convention | Medium | sensitivity-sweep |
| `P_CREEP_INFLECTION` | 0.5 (dc threshold) | `assumed_industry` | ADR-007 mirror of combustion | Medium | sensitivity-sweep |
| `P_CREEP_SCALE` | 0.10 | `assumed_industry` | ADR-007 mirror | Medium | sensitivity-sweep |
| `P_FORCED_DAY_CAP` | 0.10 /day | `assumed_industry` | Engine safety cap | Low — rarely binds | none |
| `TRIP_MAINTENANCE_FACTOR` | → §3.4 | — | — | — | — |
| `TBC_WEIBULL_BETA` / `_ETA` | → §3.5 | — | — | — | — |
| `ROTOR_LIFE_PER_FIRED_HOUR` | 1e-7 /h | `assumed_industry` | Heavy-rotor life convention | Low — slow accumulator | none |
| `HRSG_CYCLES_PER_START` | 1.0 | `assumed_industry` | Definitional (1 cycle per start) | Low — tracked-but-not-wired | none |
| `AMBIENT_WEAR_REF_F` | 34.3°F | `assumed_derived` | Realized fired-hour-weighted mean ambient (Lockport post-#2 path); re-anchor property | Low — calibration anchor | none |
| `AMBIENT_WEAR_SENS_PER_F` | → §3.7 | — | — | — | — |
| `AMBIENT_WEAR_FACTOR_MIN` / `_MAX` | 0.70 / 1.40 | `assumed_industry` | Engine clamps (ADR-006) | Low | sensitivity-sweep |

### §4.2 Initial-state / aging-clock anchors

| Constant | Current value | Status | Source | Rank | Blocked-on |
|---|---|---|---|---|---|
| Initial `state.eoh` | → §3.12 | — | — | — | — |
| Initial `state.rotor_life` | → §3.13 | — | — | — | — |
| Initial `state.dc` | 0.0 | `assumed_industry` | "Fresh off HGP" convention | Medium | data-room |
| Initial `state.df` | 0.0 | `assumed_industry` | "Fresh off HGP" convention | Medium | data-room |
| Initial `state.tbc_time` | 0.0 | `assumed_industry` | "Fresh coating" convention | Medium | data-room |
| Initial `state.fouling` / `hr_recov` | 0.0 / 0.0 | `assumed_industry` | "Just-washed" convention | Low | data-room |
| Initial `state.hrsg_cycles` | 0 | `assumed_industry` | Tracked-only field | Low | none |
| `AGING_WINDOW_YEARS` anchoring | → §3.11 | — | — | — | — |
| `HRSG_AGE_MULT_MAX` / `BG_AGE_MULT_MAX` | → §3.10 | — | — | — | — |

### §4.3 Operational hazard baselines (`outage_mechanics.md` §B, `engine.py` lines 212–217, 376–377)

| Constant | Current value | Status | Source | Rank | Blocked-on |
|---|---|---|---|---|---|
| `HRSG_BASE_PROB_PER_DAY` | → §3.8 | — | — | — | — |
| `BG_BASE_PROB_PER_DAY` | → §3.9 | — | — | — | — |
| `OUTAGE_DURATION_DAYS["gt"]` | 8 days median | `placeholder` | Athens prototype (lognormal median) | Medium | data-room / GADS |
| `OUTAGE_DURATION_DAYS["hrsg"]` | 12 days median | `placeholder` | Athens prototype | Medium | data-room / GADS |
| `OUTAGE_DURATION_DAYS["bg"]` | 5 days median | `placeholder` | Athens prototype | Medium | data-room / GADS |
| `OUTAGE_DURATION_SIGMA` | 0.5 (lognormal σ) | `assumed_industry` | Engineering convention for repair-time spread | Low | GADS |
| `forced_outage_coverage.hrsg.typical_repair_cost_usd` | $500,000 | `placeholder` | Athens prototype | Medium | data-room |
| `forced_outage_coverage.bop.typical_repair_cost_usd` | $750,000 | `placeholder` | Athens prototype | Medium | data-room |
| `forced_outage_coverage.st.typical_repair_cost_usd` | $200,000 | `placeholder` | Athens prototype | Low — ST events rare | data-room |
| `forced_outage_coverage.gt_mechanical.typical_repair_cost_usd` | null (OEM-covered) | `placeholder` | CSA scope convention | Low | data-room |

### §4.4 LTSA monetary constants (`ltsa_terms.yaml`) — **all `placeholder`, all blocked on data-room**

Section-level defaults: **defensibility target = Tier 1 (measured)**, **owner = diligence**.

| Constant | Current value | Status | Source | Rank | Blocked-on |
|---|---|---|---|---|---|
| `fixed_fee.monthly_usd` | $850,000 | `placeholder` | Athens prototype | High — recurring stream | data-room |
| `fixed_fee.escalation_pct_per_year` | 3.5% | `placeholder` | Athens prototype | Medium | data-room |
| `eoh_reserve.rate_usd_per_eoh` | $175 / EOH | `placeholder` | Athens prototype | High — EOH-reserve stream | data-room |
| `eoh_reserve.escalation_pct_per_year` | 3.5% | `placeholder` | Athens prototype | Medium | data-room |
| `inspection_ci.total_cost_usd` | $3,750,000 | `placeholder` | Athens prototype | High | data-room |
| `inspection_ci.oem_covered_fraction` | 0.75 | `placeholder` | Athens prototype | High — sets owner-uncovered | data-room |
| `inspection_ci.owner_uncovered_usd` | $937,500 | `placeholder` (derived) | 3.75M × 0.25 | High (derived from above) | data-room |
| `inspection_ci.outage_duration_days` | 12 | `placeholder` | Athens prototype | Medium | data-room |
| `inspection_ci.eoh_threshold` | → §3.14 | — | — | — | — |
| `inspection_mi.total_cost_usd` | → §3.16 | — | — | — | — |
| `inspection_mi.oem_covered_fraction` | 0.65 | `placeholder` | Athens prototype | High — sets owner-uncovered | data-room |
| `inspection_mi.owner_uncovered_usd` | $10,500,000 | `placeholder` (derived) | 30M × 0.35 | **High** — largest LTSA event cost | data-room |
| `inspection_mi.outage_duration_days` | 52 | `placeholder` | Athens prototype | High — long downtime | data-room |
| `inspection_mi.eoh_threshold` | → §3.15 | — | — | — | — |
| `start_overage.annual_baseline_starts` (h/w/c/t) | 150 / 35 / 5 / 3 | `placeholder` | Athens prototype | Medium | data-room |
| `start_overage.overage_charge_usd_per_excess_start` (h/w/c/t) | 8.5k / 42k / 125k / 80k | `placeholder` | Athens prototype | Medium — fires when over baseline | data-room |
| `availability_penalty.guarantee_pct` | 95.0% | `placeholder` | Athens prototype | Medium | data-room |
| `availability_penalty.penalty_formula` | `(monthly_fee/12) × shortfall × 10` | `placeholder` | Athens convention | Medium | data-room |
| `hr_penalty.guarantee_btu_per_kwh` | null | `placeholder` | Pending design HR | Medium | data-room (also EIA-860 gap) |
| `hr_penalty.tolerance_pct_above_guarantee` | 2.0% | `placeholder` | Athens prototype | Low | data-room |
| `hr_penalty.penalty_method` | `excess_fuel_cost × 1.25` | `placeholder` | Athens convention | Low | data-room |

### §4.5 Policy / mode constants (`engine.py` lines 273–340)

| Constant | Current value | Status | Source | Rank | Blocked-on |
|---|---|---|---|---|---|
| `MODE_EOH_RATE_MULT` (A/B/C) | 1.00 / 0.875 / 0.65 | `assumed_industry` | Prototype understanding doc §5 | High — defines A/B/C divergence | sensitivity-sweep |
| `GT_WEAR_FRACTION_OF_START` | 0.42 | `assumed_industry` | Prototype convention (GT-share of start cost) | Medium | none |
| `START_CM_USD_PER_MW` | → §3.17 | — | — | — | — |
| `MIN_RUN_HOURS_FOR_AMORTIZATION` | 6.0 h | `assumed_industry` | Heuristic for expected run-streak | Medium — sets hurdle magnitude | sensitivity-sweep |
| `EOH_RATE_ESTIMATE_PER_DAY` | 8.0 EOH/day | `assumed_industry` | Heuristic ("low-CF Lockport ~8 EOH/day"); v2 = per-asset historical | Medium | none |
| `wear_penalty_mult(mode, eoh_headroom)` curve | hardcoded per mode | `assumed_industry` | Prototype understanding doc §5 | Medium | sensitivity-sweep |

### §4.6 Schema / definitional constants (not v2-blocking)

Reset multipliers, budgets that equal 1.0 by definition, and other model-shape constants that aren't independent calibration targets. Tracked here so the inventory is complete; **rank = Low**, **blocked-on = none** unless flagged.

| Constant | Current value | Status | Source |
|---|---|---|---|
| CI resets — `dc×0.5, df×0.5, fouling×0.3, hr_recov×0.3` | per `apply_inspection_reset` | `assumed_industry` | Athens prototype |
| MI resets — `dc=0, df=0, tbc_time=0, hrsg_cycles=0, rotor×0.5, fouling×0.3, hr_recov×0.25` | per `apply_inspection_reset` | `assumed_industry` | Athens prototype |
| Hot/warm/cold cutoffs (`hrs_off < 8 / < 72 / ≥ 72`) | 8 / 72 hours | `assumed_industry` | GER-3620 start-type convention `[GER-3620]` |

---

<a id="section-5"></a>
## §5. Next execution pass

Per `parameter_calibration_plan.md` §4:

1. **Sensitivity rank** — reuse the Phase-L sweep machinery (or a local sweep) to fill the `TBD` ranks and promote/demote Low/Medium/High labels. Update the rank columns in §3 + §4.
2. **Public-literature citation pass** — replace Athens-prototype provenance with cited sources for the Tier-2 backlog rows: GER-3620 for hot-section physics, Kumar 2012 for start C&M, NERC GADS for HRSG/BG baselines, **Saturday & Isaiah 2018** (acquired 2026-05-27) for ambient/load creep coefficients — see §3.7 cross-check; aging-multiplier curves still pending separate literature.
3. **MOR / data-room pass** — populate Tier-1 candidates: initial-state EOH (§3.12), inspection thresholds (§3.14, §3.15), all of §4.4. Owner = diligence; blocked on data-room file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` + original PURPA contract filings.
4. **Calibration pass** — Tier-3 rows: tune `HRSG_BASE_PROB_PER_DAY` / `BG_BASE_PROB_PER_DAY` so modeled EFOR matches MOR/GADS; tune wear rates so modeled EOH→MI timing matches contract MI interval.
5. **Regression-gate strategy** — every constant change must pass the byte-identical engine regression (`tests/test_gt_engine_regression.py`); calibration upgrades will require a baseline-refresh PR documenting the delta. Keep a `calibration_changelog.md` (future) or annotate in commit messages.

---

<a id="section-6"></a>
## §6. Cross-references

- [`parameter_calibration_plan.md`](../plans/parameter_calibration_plan.md) — the process this register tracks.
- [`status_taxonomy.md`](status_taxonomy.md) — the 9-code status grammar.
- [`placeholder_caveats.md`](placeholder_caveats.md) — what each placeholder means operationally.
- [`methodology/wear_mechanics.md`](../methodology/wear_mechanics.md) §7–§8 — constants + current placeholder status.
- [`methodology/outage_mechanics.md`](../methodology/outage_mechanics.md) §B — operational hazard math.
- [`methodology/gaps_and_priorities.md`](../methodology/gaps_and_priorities.md) #1 (data-room LTSA), #8 (per-asset Bucket-B calibration).
- `data/assets/lockport/ltsa_terms.yaml` — LTSA placeholder values (the §4.4 source).
- `src/gt_engine/engine.py` — code constants (lines 195–340 for wear / hazard / policy; lines 841–871 for aging).

---

<a id="section-9"></a>
## §9. References

| Key | Title / source | URL |
|---|---|---|
| `[GER-3620]` | GE Power, *GER-3620: Heavy-Duty Gas Turbine Operating and Maintenance Considerations* | https://www.gevernova.com/content/dam/gepower-new/global/en_US/downloads/gas-new-site/resources/reference/ger-3620-heavy-duty-gas-turbine-operating-maintenance-considerations.pdf |
| `[Kumar2012]` | N. Kumar et al., *Power Plant Cycling Costs* (NREL/SR-5500-55433), 2012 — Table 1-1 Gas-CC start C&M | https://www.nrel.gov/docs/fy12osti/55433.pdf |
| `[NERC-GADS]` | NERC Generating Availability Data System (GADS) — Class CC (Combined-Cycle) availability statistics | https://www.nerc.com/pa/RAPA/gads/Pages/default.aspx |
| `[Saturday-Isaiah-2018]` | Saturday, E.G. & Isaiah, T.-G. (2018), *Effects of Ambient Temperature and Shaft Power Variations on Creep Life Consumption of Industrial Gas Turbine Blades*, Energy and Power Engineering, 10, 120–131. Cranfield-PYTHIA engine model + Larson-Miller + Mean Life Reduction Index for LM2500+ aero-derivative. **Acquired 2026-05-27** (received from S. Deshpande). Provides creep MLRI: ambient 0.2451 per °C (life halves at +8.11°C); shaft power 0.1466 per 1% (life halves at +13.64%). Heavy-duty F-class vs aero-derivative caveat applies — see §3.7 cross-check. (Originally tagged `[Friday]` in earlier drafts — the meeting it came from was on a Friday; the actual lead author is Saturday.) | https://doi.org/10.4236/epe.2018.103009 |
