# Lockport — Modeling Caveats

> Things that materially affect how Lockport should be modeled. Each caveat is referenced from the relevant YAML fields via the `caveat:` metadata.

This document is the place to read **before** writing dispatch code for Lockport. The YAML files are the structured facts; this is the narrative context that explains why those facts matter.

---

## §1. Operational status correction

The public renewablesinfo brief (`plant_54041_lockport_data_brief.md` §8) originally flagged Lockport as "likely mothballed" based on EIA-923 monthly generation reporting 0 MWh for 11 of 12 months of 2024.

**That inference was wrong.** The diligence-extractor MOR notebook (`daily_heat_rate_analysis.ipynb`) analyzed 5 years of daily Monthly Operating Reports and found Lockport generated **192,494 MWh in 2024** — similar to 2022. The public-data zero pattern was an artifact of the one PDF page that captured a non-operating period.

**Implication for modeling**:
- Treat Lockport as an **active dispatch resource** for 2024.
- Do not propagate "likely mothballed" framing from the public brief.
- For consistency with the corrected understanding, see `operating_profile.yaml` (Phase D) which carries the MOR-derived heat-rate-by-mode and operational pattern.

---

## §2. Cogen / CHP markup over tech-class merchant defaults

Lockport is **CHP-flagged** (`is_chp = True` for all 4 generators). The tech-class defaults in `data/tech_class_defaults/dispatch_params_lookup.parquet` are calibrated against **merchant CCGT operations**. Cogen plants systematically deviate:

- **VOM**: cogen plants run steam-host coordination overhead, water-treatment chemicals for steam delivery, etc. Kumar 2012's $1.02/MWh baseload value (which the lookup gives Lockport's `(CT, <2000, False)` row) likely understates true operating VOM by **30–50%**.
- **Min up / min down**: may be driven by host steam contract, not turbine constraints. Lockport's original GM Powertrain steam-host arrangement could have imposed minimums of 8–24 hr at times.
- **Startup cost**: includes host-coordination overhead and steam-system warming if host steam is required.
- **Start times**: longer if HRSG steam delivery to host must stabilize before electric ramp.

**Implication for modeling**:
- Apply a **+20–40% markup across cycling-related parameters** as a conservative correction in `src/cogen/vom_adjustment.py` (Phase I).
- The lookup is the merchant-CCGT proxy; v1 ships with the markup applied at consumption time, not encoded in the lookup.
- v2 may add a CHP-specific override path.

---

## §3. Multi-mode dispatch

Lockport can run in multiple operating modes (verified in MOR data, captured in `operating_profile.yaml`):

| Mode | Composition | Approx output |
|---|---|---|
| 3×CC_full | 3 CTs + ST | ~221 MW |
| 2×CC | 2 CTs + ST | ~170 MW |
| 1×CC | 1 CT + ST | ~120 MW |
| ST-only | ST alone on duct-burner steam | ~78 MW |
| Thermal-only | Aux + steam to host, no electric | 0 MW electric (host steam only) |

Each mode has a **distinct heat rate** (from MOR Stage 2 volume-weighted aggregation):

- 3×CC_full: **8,901 Btu/kWh** (189 days observed; 65% of active operation)
- 2×CC: **9,598 Btu/kWh** (76 days; 26%)
- 1×CC: **10,424 Btu/kWh** (26 days; 9%)

The tech-class lookup gives **block-level** values only — not mode-specific. The dispatch model must pick which mode to commit per hour based on LMP, then apply the correct mode heat rate.

**Implication for modeling**:
- `src/dispatch/multi_mode.py` (Phase I) chooses mode per hour based on spark spread under each mode.
- Heat rate read from `operating_profile.yaml` (mode-keyed), not from the tech-class lookup directly.
- Startup cost for partial-block starts (e.g., starting only 1 CT + ST) scales with MW being started, not the full block.

---

## §4. Dual-fuel switching

Lockport can switch between natural gas and distillate fuel oil (DFO) **in 1 hour** while operating, both directions.

| Constraint | Detail |
|---|---|
| Switch time | 1.0 hr (gas→oil, oil→gas) |
| Storage-limited | On-site oil tank ~3–7 days of full-burn capacity |
| Air-permit-limited | Title V cap on hours/year of oil firing |

**Implication for modeling**:
- Relevant in NYISO winter polar-vortex scenarios when Algonquin Citygate gas spikes (>$30/MMBtu).
- v1 model can model gas-only dispatch with a fuel-switch flag for sensitivity analysis.
- Oil dispatch has different heat rate (typically +3–8% on DFO vs NG per dispatch_params methodology); not modeled in v1.

---

## §5. EIA cold-start reporting clustering

EIA-860 schedule 3_1 reports `Time from Cold Shutdown to Full Load = 720 minutes (12 hr)` for all 4 Lockport generators.

**Caveat**: 86% of CCGTs in EIA-860 cluster on exactly 720 minutes — this is a reporting convention, not actual hot-start time. Vendor field-operations data for Siemens 501F (the relevant F-class reference) gives hot 3 hr / warm 6 hr / cold 8 hr.

**Implication for modeling**:
- Use **vendor 8 hr cold-start** value from `data/tech_class_defaults/dispatch_params_lookup.parquet` (or the asset-specific override in `operating_profile.yaml` when populated).
- EIA's 720-min value is for compliance reporting context; preserved in `engineering.yaml` per-generator for traceability but not used as the dispatch input.

---

## §6. Steam-host (DHTS) constraint

Lockport delivers steam to an industrial host customer ("Distributed Heat to Steam" — DHTS in MOR terminology). The MOR Stage 1 analysis identified ~80,000 MMBtu/year of host thermal delivery, with patterns visible at daily resolution.

**The steam-host obligation is a must-run constraint when the host needs steam**, regardless of LMP. A pure energy-margin dispatch model would turn the plant off in hours it physically cannot be off.

**Implication for modeling**:
- `src/cogen/host_steam_constraint.py` (Phase I) must encode this constraint.
- Approach for v1: tag days/hours where DHTS > threshold (from `operating_profile.yaml`) as must-run; force minimum dispatch.
- A pure energy-only dispatch ignoring this constraint will produce unrealistic outputs — this is the single biggest Phase 1 trap for a cogen plant.

The MOR notebook also surfaced **35 "warming days"** (gas burn before electric generation begins) — these are cold-start preparation days. Treat separately from operating heat-rate computation.

---

## §7. Ambient sensitivity

All four generators are flagged `is_ambient_sensitive = True` (sum of |summer derate| + |winter boost| > 5%).

- CTs (GEN1–3): summer derate ~3.5%, winter boost ~+2.7%
- ST (GEN4): summer **gain** ~3.7% (negative derate — condenser efficiency on cool days outweighs ambient effects), winter boost ~+6.4%

**Implication for modeling**:
- `src/engineering/capacity.py` (Phase H/K) applies `cap_eff(temp_f, generator_id)` per generator — not a uniform plant-level derate.
- The 46-year hourly weather data at plant coordinates (in `data/paths/lockport/weather_hourly.parquet`) is the temperature input.
- Treat the ST's summer gain explicitly; defaulting to a positive derate is wrong for this generator.

---

## §8. 1992 F-class vintage

Lockport's vintage is `<2000` per the tech-class lookup classification. 1990s-vintage F-class CCGTs differ from modern fleet in:

- **Slower sustained ramp** — assumed ~4%/min vs ATB's reference 5%/min for newer F-Frame fleet. (LOW confidence; industry estimate.)
- **62% min load on CTs** — inflexible compared to H-class units (typically <50%).
- **Cycling-damage cost** — Kumar 2012 database covers this era well; tech-class lookup values are appropriate confidence.

**Implication for modeling**:
- Don't apply modern H-class fast-cycling capabilities. Lockport's behavior is bounded by 1992 metallurgy.
- The mode min-load floor (62% per CT, 19% per ST) is the dispatchability constraint.

---

## §9. Merchant cogen status — no FERC Form 1

Lockport is a Non-Regulated merchant. Implications:

- **No FERC Form 1 cost recovery data.** Financial coverage in the public-data brief is limited to a 2013 EIA aggregated-cost proxy ($965/kW capex) — not modeling-grade.
- **LTSA contract structure pending data room extraction.** `ltsa_terms.yaml` (Phase F) carries placeholder values until extraction completes.
- **No NYISO ICAP tracking** in our public data (capacity revenue is 20–40% of typical CCGT revenue — significant omission for v1).

**Implication for modeling**:
- v1 ships with energy-only revenue.
- Document model_card disclaimers about omitted revenue streams.
- v2 follow-on: layer in NYISO ICAP from data room DMNC test results (`3.6.1.5 Lockport DMNC CC 1-3 Winter 2025.xls`).

---

## §10. The 2024 zero-generation pattern — what it actually means

Even with the operational status correction (§1), 2024 generation pattern from the MOR shows distinct on/off operating modes. Lockport is **not a baseload merchant CCGT**:

- Annual capacity factor: ~5% (eGRID 2023) and lower in 2024 — peaker/reliability profile
- Multi-day strings of zero generation followed by sustained operating periods
- Cold-start warming days observed (35 over 5 years)
- Operating mode distribution: 65% 3×CC / 26% 2×CC / 9% 1×CC

**Implication for modeling**:
- Treat Lockport as a **nonbaseload / reliability / cogen asset** (per eGRID `nonbaseload_factor = 1.0`).
- Annual capacity factor expectations should be 5–15%, not 60%+.
- Mode A (maximize dispatch) policy should still produce low CF outputs for this asset; if it produces high CF, the model is mis-calibrated.

---

## §11. v1 gas hub treatment (Henry Hub only)

**Where**: `market_context.yaml.gas_market.v1_modeling_choice`, ADR-001, Notebook 2 setup.

**The decision**: v1 uses Henry Hub daily prices directly as delivered gas, NOT Algonquin Citygate (the asset's actual delivery point). Algonquin basis modeling is deferred to v2.

**Why this happened**: the `gas_price_history.parquet` migrated from model-gpr has 8 hubs, but only Henry Hub has 1997-2026 coverage. Every other hub — including Algonquin Citygate — has only 2014-2017 (~700 rows each). Applying 2014-2017 Algonquin basis forward to 2018-2025 would overstate the basis due to Atlantic Sunrise pipeline (2018) and other Northeast capacity expansions that tightened the basis. Henry Hub-only is a known limitation; 2014-2017-basis-applied-everywhere is a likely-wrong imputation. Frame A (plumbing validation) prefers the known limitation.

**Modeling consequences**:

1. **Dual-fuel switching never fires in v1.** Henry Hub winter peaks (~$7-10/MMBtu) never cross the oil-switching threshold (~$14-22/MMBtu delivered gas). The fuel-switching logic in `src/dispatch/` is present but unfired. Acceptable for typical-day modeling; misses Lockport's winter reliability value.
2. **Winter polar-vortex days backtest wrong.** Specifically January 2014 (peak Algonquin >$100/MMBtu) — our model says "run on gas at $7"; actual was "switch to oil because Algonquin is $100". Backtest acceptance criteria need to allow for this.
3. **P10 spark spread (rare-bad-days) too optimistic.** Real Lockport had downside protection from dual-fuel; our v1 model doesn't capture it.
4. **Lockport's NYISO Zone A reliability story partially obscured.** The plant exists economically partly because of winter scarcity capture; v1 doesn't show that.

**Mitigations baked into the data**:
- `market_context.yaml.gas_market.delivery_hub` still shows "Algonquin Citygate" (the asset's reality) with `status: real_reported`
- `market_context.yaml.gas_market.v1_modeling_choice.hub_used_for_delivered_gas` = "Henry Hub" with `status: assumed_industry`, `confidence: LOW`, and a `validation_path` pointing to the v2 follow-on ADR
- Every v1 model_card must surface this — banner content drafted in ADR-001

**Tested-and-reverted (2026-05-27)**: A 2014-2017 Algonquin-minus-Henry-Hub *seasonal basis overlay* (monthly median basis added to Henry Hub: winter ≈ +$2.60, summer ≈ −$0.56/MMBtu) was implemented in N4 and run end-to-end. Two findings reverted it: (1) **it overstates 2018-2025 winter gas** for exactly the reason above (the 2014-2017 basis reflects the pre-Atlantic-Sunrise constrained era) — confirming the original §11 judgment; and (2) **it did not reduce the over-commit** — 9-yr spark fell ~$36M → $27M (more honest *margin-per-MWh*) but generation/over-commit stayed ~2.2× MOR and 2×CC stayed 0%. This **empirically confirms the over-commit is the price-taker *self-commitment* paradigm** (the model runs full output whenever spark > 0), not the gas-price level. So flat Henry Hub stands for v1; the real over-commit lever is dispatch realism (commitment hurdle + price-responsive output), not gas basis. Don't re-attempt the overlay without a real post-2018 delivered-gas series. See `docs/methodology/extra/temperature_load_fidelity.md`.

**Reference**: [`../../../docs/decisions/001-gas-hub-treatment-v1.md`](../../../docs/decisions/001-gas-hub-treatment-v1.md)

---

## §12. Parameter calibration status — what's Lockport-specific vs generic F-class

**Where**: ADR-002 (canonical inventory), this section (Lockport-modeling-facing summary), various YAML files (per-parameter `status` flags).

The model's parameters fall into three calibration buckets:

### Bucket A — Lockport-specific data (use as-is)

- LMP at PTID 23791, Henry Hub gas, weather at plant coordinates
- **Heat rate by mode** from MOR (3×CC 8,901 / 2×CC 9,598 / 1×CC 10,424 Btu/kWh) — `real_observed`
- Mode capacities, per-generator ambient sensitivity, min loads — all from EIA-860 — `real_reported`
- Plant identity, ownership, dual-fuel matrix — from EIA-860 — `real_reported`
- **MOR-observed cold-start warming gas** (2,537 MMBtu/cold start, 88,785 MMBtu over 5 yr) — **now used in N3 fuel cost calculation** per ADR-002 Correction 1 — `real_observed`

### Bucket B — Generic F-class defaults (Athens-derived; honest placeholders)

- Initial state: EOH=24,000 ("post-HGP simulation start"), rotor_life=0.35 — modeling convention, NOT Lockport-specific
- Stress accumulator constants: fouling rate (asymptote 2.5%, tau 2,000 hrs), creep rate, fatigue per start (cold/warm/hot), HRSG cycles per start, rotor-life rate — all `assumed_industry` LOW
- TBC Weibull parameters (β=3, η=28,000) — generic F-class
- START_EOH_COST (cold=20, warm=10, hot=5) — GE 7FA per GER-3620K (assumes Lockport is GE; OEM not yet confirmed)
- Forced-outage probability constants: HRSG baseline 0.75%/day, BG baseline 0.4%/day, age scaling 1.0×→1.5× over 10 yr — `assumed_industry` LOW; the age-scaling is the dominant tornado driver per prototype §13

### Bucket C — Placeholder pending data room extraction

- All LTSA contract terms — see `placeholder_caveats.md` §1
- Inspection thresholds (CI=24,000, MI=48,000 EOH) — `placeholder`
- Inspection costs ($3.75M / $30M) — `placeholder` (Athens-scaled)
- OEM coverage fractions (75% CI / 65% MI) — `placeholder`

### Implications for modeling outputs

- **For dispatch logic** (per-day spark, mode choice, P&L): outputs are Lockport-specific and defensible.
- **For state evolution** over 30-day windows: directionally correct, with modest exposure to Bucket B constants.
- **For Phase L 10-year Monte Carlo**: Bucket B constants compound. **The model_card must treat Bucket B parameters as sweepable**, not fixed inputs. Particularly `P_BG_AGE_MAX` (the dominant tornado driver).
- **For LTSA cost streams**: all currently `placeholder`. Real values land when data room extraction completes.

### Reference

Full inventory + reasoning + corrections: [`docs/decisions/002-lockport-specific-vs-generic-calibration.md`](../../../docs/decisions/002-lockport-specific-vs-generic-calibration.md)

---

## See also

- `identity.yaml` — plant identification and status fields (cross-referenced by §1, §9)
- `engineering.yaml` — capacity / generators / dual-fuel / ambient sensitivity (cross-referenced by §3, §4, §7, §8)
- `market_context.yaml` — NYISO node, RGGI exposure, gas market (cross-referenced by §4)
- `operating_profile.yaml` (Phase D) — mode-segmented heat rate, cold-start gas, DHTS host steam patterns (cross-referenced by §3, §6, §10)
- `ltsa_terms.yaml` (Phase F) — contract structure (cross-referenced by §9)
- `provenance.md` — where each value came from
- `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb` — MOR analysis source for §1, §3, §6, §10
- Consolidation plan §6 (assumption tracking) — the discipline that makes these caveats discoverable
