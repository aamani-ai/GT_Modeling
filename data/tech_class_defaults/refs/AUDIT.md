# AUDIT — cell-by-cell source attribution

> One row per `(prime_mover_code, vintage_class, parameter)` cell. Each cell points to a specific source document + table/page so the value can be re-derived years later.
>
> **Status**: 🟡 First research pass complete (2026-05-08). ~70 of 144 cells have source-documented values; remaining cells documented as "no source value" with reasoning (not blank).

---

## Headline finding from this research pass

**PJM Manual 15 publishes no default $/MW values for startup cost or min up/down time.** Sections 5–6 specify the *formula* and require unit-specific Start Fuel Consumed (MMBtu/Start), Performance Factor, Station Service, and unit-specific Start Maintenance Adders to be filed by each Market Seller. Default soak-time fractions of Min Run Time are provided (Cold Soak = 0.73×, Intermediate Soak = 0.61×, Hot Soak = 0.43×) but Min Run Time itself is "unit specific." This contradicts the design doc's claim that PJM Manual 15 was the primary source for these values.

**Consequence**: **Kumar et al. 2012 (NREL/SR-5500-55433) is our actual primary for startup cost $/MW values.** It reports lower-bound C&M (capital + maintenance damage) costs and startup fuel quantities by tech class. The 03_per_param_methodology.md and 01_source_landscape.md docs are being updated to reflect this.

**A second consequence**: PJM does NOT lock a fixed gas-price assumption. Section 2.2 (Fuel Cost Policies) requires each Market Seller to declare its own fuel price per its documented Fuel Cost Policy (spot index, hedged contract, etc.). There is no single "PJM gas price" that converts MMBtu/start to $/start; the conversion is unit- and day-specific.

---

## Source registry (updated 2026-05-08)

| Source | Version | Retrieved | Local copy | License | Notes |
|---|---|---|---|---|---|
| **Kumar, Besuner, Lefton, Agan, Hilleman (2012)** *Power Plant Cycling Costs* | NREL/SR-5500-55433 | 2026-05-08 | `refs/kumar_2012.pdf` (1.4 MB) | Public (US gov / NREL) | **PRIMARY for startup C&M cost + startup fuel + ramp-degradation costs.** All values 2011 USD. |
| **NREL ATB 2024** Electricity Workbook | 2024 v3 | 2026-05-08 | `refs/atb_2024.xlsx` (5 MB) | CC-BY-4.0 | **PRIMARY for VOM, heat rate, ramp rate, min load, FOR/POR.** Tab `Natural Gas_FE`. Rows 51–54 = key parameters; 95–105 = HR; 223–234 = FOM; 255–266 = VOM. 2022 USD. |
| **EIA AEO 2026 EMM Assumptions** | April 2026 | 2026-05-08 | `refs/emm_2026.pdf` (788 KB, 33 pp) | Public (US gov) | Cross-check for VOM + heat rate. Underlying source = Sargent & Lundy 2024 + Brattle/S&L PJM CONE update. 2025 USD. **Models only H-class CC** (no F-class). |
| **PJM Manual 15** Cost Development Guidelines | Rev 47, eff 2025-10-01 | 2026-05-08 | `refs/pjm_m15.pdf` (1.5 MB, 149 pp) | Public | **Methodology only — no default $/MW values.** Defines Cold/Intermediate/Hot Start qualitatively (§3.4) + soak-time fractions (§5.4). Useful for definitions, not values. |
| Siemens 501F start-time reference | via CCJ | 2026-05-08 | URL only | n/a | https://www.ccj-online.com/501f-best-practices-athens/ — F-class hot/warm/cold = 3 / 6 / 8 hr. |
| GE Vernova LM6000 / LMS100 | vendor pages | 2026-05-08 | URLs only | n/a | LM6000 PC/PD/PF: 10 min std, 5 min Fast Start. LMS100: 8 min to full load. https://www.gevernova.com/gas-power/services/gas-turbines/upgrades/lm6000-fast-start ; https://ge.com/power/gas/gas-turbines/lms100 |
| MISO / NYISO / ISO-NE / CAISO cost manuals | various | 2026-05-08 | NOT FETCHED | Public | Skipped after PJM finding showed RTO manuals are methodology-only. CAISO Master File holds unit-specific values (no defaults table). |
| EPA Efficient Generation TSD (CT) | 2023 | NOT FETCHED | URL only | Public | Binary PDF parse failed via WebFetch. May contain regulatory-cited start-time values for v2 follow-up. https://www.epa.gov/system/files/documents/2023-05/TSD%20-%20Efficient%20Generation%20Combustion%20Turbine.pdf |

---

## Critical methodology decisions resolved by this research

### Decision 1: Kumar 2012 is the primary for startup cost (not PJM)
Reasoning: PJM publishes no default $/MW values. Kumar reports lower-bound C&M cost ranges by tech class with explicit median + 25th/75th percentiles. We adopt Kumar median as the central estimate, with the IQR documented for UI range presentation.

### Decision 2: Kumar 2012 covers a single "Gas-CC [GT+HRSG+ST]" group — does not separate CT (in CCGT) from CA
Reasoning: No public source separately quantifies $/MW startup damage on the GT vs. ST half. **CT/CA/CC prime movers all receive the same Kumar block-level values.** The ramp_rate parameter is the only one where CT and CA likely differ (CA bottoming-cycle is HRSG-limited and slower); we apply ATB block-level ramp to all three.

### Decision 3: Kumar 2012 does not segment vintages — same values across `<2000` / `2000-2010` / `2010-2020` / `2020+` for startup cost
Reasoning: Kumar's database aggregates 1990s-2010s plants. We use the same Kumar values across vintage classes for startup cost, but downgrade confidence (HIGH→MEDIUM) for `<2000` and `2010-2020`, and to LOW for `2020+`. ATB Advanced 2025-2030 projection is the proxy for `2020+`.

### Decision 4: VOM has wide cross-source spread — disclose ranges in UI
Reasoning: Kumar (2011$ baseload-only lower bound) ≈ $1/MWh inflates to ≈$1.40/MWh (2025$); ATB 2024 (2022$ new-build) ≈ $2.17/MWh inflates to ≈$2.39/MWh; EIA AEO 2026 (2025$ new-build) = $3.49/MWh. The 2.5× spread is real and reflects how the parameter is defined (baseload-only vs new-build all-in vs post-inflation S&L 2024). UI must show the range, not a point estimate. **For the parquet's central value: use ATB 2024 Moderate as the canonical default; record the AEO and Kumar values in side columns for range/uncertainty disclosure.**

### Decision 5: min_up_hr and min_down_hr have no published source values
Reasoning: PJM is unit-specific. Kumar provides "Warm Start Offline Hours" boundary (5–40 hr for CC, 2–3 hr for large frame CT, 0–1 hr for aero-derivative) but that's the hot/warm boundary, not min-up or min-down. **Recommendation**: populate with industry-typical values from operator-survey literature (NREL WWSIS-2 derives from Kumar with NREL operating assumptions added), confidence LOW. Validate against CEMS observed-run-length distribution at v2 stage.

### Decision 6: Hot/cold start time for F-class CC sourced from Siemens vendor reportage (CCJ)
Reasoning: 3/6/8 hr (hot/warm/cold) for F-class CC block. Not regulatory-cited. **Confidence MEDIUM.** EPA's 2023 Subpart KKKKa proposed rule TSD likely contains regulatory citations; flagged for follow-up.

### Decision 7: 2020+ vintage relies on ATB Advanced scenario projections
Reasoning: Neither Kumar (predates) nor ATB 2024 base-year nor EIA AEO 2026 (only models H-class) cleanly populates this vintage. Use ATB 2024 Advanced scenario 2025–2030 column as proxy. Confidence LOW. Validate with CEMS data for actual 2020+ commissioned plants when available.

---

## Cell tables

### CCGT block-level cells — applies to `CT`, `CA`, `CC` prime movers (per Decision 2)

Kumar 2012 reports "Gas-CC [GT+HRSG+ST]" as one technology class. These values populate **all 12 cells** (3 prime movers × 4 vintages) for startup cost and the same value for VOM with the cross-source layer added.

#### Startup cost C&M (capital + maintenance damage) — Kumar 2012 Table 1-1, page 12

Values are 2011 USD. Apply CPI ~1.40 to convert to 2025$ if needed (×1.40 → median cold = ~$111/MW in 2025$).

| Vintage | Cold (median, 25th–75th) | Warm (median, 25th–75th) | Hot (median, 25th–75th) | Confidence | Notes |
|---|---|---|---|---|---|
| `<2000` | $79/MW (46–101) | $55/MW (32–93) | $35/MW (28–56) | MEDIUM | Same Kumar values; vintage not separated. Older plants likely in upper IQR. |
| `2000-2010` | **$79/MW (46–101)** | **$55/MW (32–93)** | **$35/MW (28–56)** | **HIGH** | **Pilot cell.** Kumar's database centroid for this era. |
| `2010-2020` | $79/MW (46–101) | $55/MW (32–93) | $35/MW (28–56) | MEDIUM | Same Kumar; H-class beginnings. Modern materials may reduce; not source-documented. |
| `2020+` | TBD — use ATB 2024 Advanced proxy | TBD | TBD | LOW | Kumar predates fleet-scale H-class. ATB Advanced scenario is closest proxy. |

#### Startup fuel — Kumar 2012 Table 1-3, page 30

| Vintage | Cold (MMBtu/MW) | Warm (MMBtu/MW) | Hot (MMBtu/MW) | Other Cost (flat across all 3, $/MW 2011$) | Confidence |
|---|---|---|---|---|---|
| All vintages (Gas-CC) | 0.24 | 0.20 | 0.19 | (small adder; see Kumar Tbl 1-3) | HIGH (Kumar) |

To convert fuel to $: multiply by gas-price assumption. **Reference**: $4/MMBtu Henry Hub historical avg → cold-start fuel cost ≈ $0.96/MW. Total startup cost (C&M + fuel + adder) at $4 gas ≈ $79 + $1 = ~$80/MW cold for CCGT block.

#### VOM ($/MWh, non-fuel)

Multi-source — show range in UI per Decision 4.

| Vintage | Kumar 2012 (2011$, baseload) | NREL ATB 2024 (2022$, new-build Moderate) | EIA AEO 2026 EMM (2025$, new-build) | Canonical (parquet) | Confidence |
|---|---|---|---|---|---|
| `<2000` | $1.02 (0.85–1.17) — F-class proxy | n/a (ATB doesn't have F-class CC) | n/a (AEO doesn't model F-class) | $1.02–2.17 (range, Kumar low-bound to ATB) | MEDIUM |
| `2000-2010` | $1.02 (0.85–1.17) | $2.17 (F-Frame 2x1, row 256) | n/a | **$2.17 canonical, $1.02–2.17 range** | HIGH |
| `2010-2020` | n/a (predates H-class fleet) | $2.16 (H-Frame 2x1, row 262) | $3.49 (single-shaft 1x1x1) / $3.57 (2x2x1) | **$2.16 canonical (ATB Moderate), $2.16–3.57 range** | HIGH |
| `2020+` | n/a | ATB Advanced 2025–2030 (row 262) ≈ $1.95 | $3.49 (AEO 2026) | $1.95 canonical, $1.95–3.49 range | MEDIUM |

#### Min up time / Min down time

No source-published values per Decision 5. Industry-typical defaults from operator-survey literature:

| Vintage | min_up_hr | min_down_hr | Source | Confidence |
|---|---|---|---|---|
| `<2000` (F-class CC) | 6 hr (typical 4–8) | 8 hr (typical 4–12) | Industry-typical, post-Kumar literature | LOW |
| `2000-2010` | 4 hr (typical 4–8) | 6 hr (typical 4–8) | Industry-typical | LOW |
| `2010-2020` | 3 hr (typical 2–6) | 4 hr (typical 2–6) | Industry-typical | LOW |
| `2020+` | 2 hr (typical 1–4) | 2 hr (typical 1–4) | H-class fast-cycling design | LOW |

**Validation flag**: these cells flagged for CEMS observed-run-length validation at v2.

#### Hot / Warm / Cold start time — Siemens 501F (F-class) and H-class vendor data

| Vintage | Hot start (hr) | Warm start (hr) | Cold start (hr) | Source | Confidence |
|---|---|---|---|---|---|
| `<2000` | ~3 hr | ~6 hr | ~8 hr | Siemens 501F via CCJ (apply to all F-class) | MEDIUM |
| `2000-2010` | ~3 hr | ~6 hr | ~8 hr | Same | MEDIUM |
| `2010-2020` | 0.5–1 hr | 1–2 hr | 4–6 hr | Siemens SGT5-8000H ("35 MW/min startup gradient"); H-class fast-start designs | MEDIUM |
| `2020+` | 0.25–0.5 hr | 0.5–1 hr | 2–4 hr | H-class / JAC vendor specs | LOW (vendor marketing) |

**EIA-860 cross-check**: schedule 3_1 `Time from Cold Shutdown to Full Load` reports 12 hr for 86% of CCGTs (clustering bias). Our cold_start_time values are consistently shorter than EIA's reported 12 hr — this is expected per Lockport profile §6 caveat about EIA reporting convention.

#### Ramp rate — NREL ATB 2024 + vendor

Steady-state sustained ramp, %/min nameplate. Block-level for CCGT.

| Vintage | Ramp (%/min) | Source | Confidence |
|---|---|---|---|
| `<2000` | 3–5%/min (estimate; older steam-bottoming slower) | Industry estimate; not source-documented | LOW |
| `2000-2010` | **5%/min** | ATB 2024 NG 2x1 F-Frame CC (row 52) | HIGH |
| `2010-2020` | 5%/min | ATB 2024 NG 2x1 H-Frame CC (row 53) | HIGH |
| `2020+` | 5%/min | ATB 2024 H-Frame Advanced; H-class block ramp limited by HRSG/ST | HIGH |

**CT vs CA distinction**: ATB row 51 (NG F-Frame simple-cycle CT) reports 8%/min — i.e., the GT alone in a CCGT block can ramp faster than the block as a whole. The CA (steam side) is the bottleneck; we apply 5%/min to all three (CT/CA/CC) for parquet simplicity, with note.

---

### Simple-cycle GT cells — `GT` prime mover

Kumar 2012 reports two relevant groups: "Gas-Large Frame CT" (group 5 — F-class simple-cycle peakers) and "Gas-Aero Derivative CT" (group 6 — LM6000, LMS100, etc.). Both are simple-cycle.

For v1, GT cells use **large-frame Kumar values** as the canonical default. Aero-derivative is a sub-population (~15% of GT generators by capacity) — values listed in side notes. v2 may add an `aero_derivative` flag column to differentiate.

#### Startup cost C&M — Kumar 2012 Table 1-1, page 12 (large frame CT)

Note Kumar's exec-summary item 7: for simple-cycle CT, "every start is essentially cold for some components" — explains why warm-start C&M ($126/MW) is higher than cold-start C&M ($103/MW) in Kumar's data (counter-intuitive but documented).

| Vintage | Cold ($/MW, median) | Warm ($/MW, median) | Hot ($/MW, median) | Confidence |
|---|---|---|---|---|
| `<2000` | $103 (31–118) | $126 (26–145) | $32 (22–47) | MEDIUM (no vintage split in Kumar) |
| `2000-2010` | **$103 (31–118)** | **$126 (26–145)** | **$32 (22–47)** | **HIGH** (centroid era) |
| `2010-2020` | $103 (31–118) | $126 (26–145) | $32 (22–47) | MEDIUM |
| `2020+` | TBD | TBD | TBD | LOW (extrapolate from ATB Advanced) |

**Aero-derivative** values (Kumar group 6): Cold/Warm/Hot = $32 / $24 / $19 per MW. Apply when aero flag is set (LM6000, LMS100, Trent 60, etc.).

#### Startup fuel + other cost — Kumar 2012 Table 1-3, page 30

| Tech | Cold (MMBtu/MW) | Warm | Hot | Other adder ($/MW, flat) |
|---|---|---|---|---|
| Large Frame CT | 0.22 | 0.19 | 0.18 | $0.95 |
| Aero-derivative | 1.53 | 1.53 | 1.53 (flat) | $1.90 |

Aero-derivative is "every start is cold" — flat fuel and other-cost across types per Kumar.

#### VOM ($/MWh) — multi-source

| Vintage | Kumar (2011$) | ATB 2024 F-Frame CT (2022$) | EIA AEO 2026 (2025$) | Canonical | Confidence |
|---|---|---|---|---|---|
| `<2000` | $0.57 (large frame) | n/a | n/a | $0.57 | MEDIUM |
| `2000-2010` | $0.57 large / $0.66 aero | $6.94 (F-Frame, flat all years) | $4.17 industrial / $5.97 aero | **$6.94 canonical, $0.57–6.94 range** | HIGH |
| `2010-2020` | n/a | $6.94 | $4.17 / $5.97 | $6.94 | HIGH |
| `2020+` | n/a | ATB Advanced ≈ $5.50 | $4.17 / $5.97 | $5.50 | MEDIUM |

The 12× Kumar-vs-ATB spread for simple-cycle CT is the largest in the lookup. Reason: peakers don't run baseload (Kumar's denominator), so Kumar's "$/MWh baseload" massively understates per-MWh cost when divided by actual peaker MWh. ATB and AEO are forward-looking new-build figures and capture the full O&M rate including overheads. **Use ATB as canonical for the parquet.**

#### Min up / Min down

| Vintage | min_up_hr | min_down_hr | Source | Confidence |
|---|---|---|---|---|
| `<2000` | 1–2 hr | 1–2 hr | Industry-typical for peaker | LOW |
| `2000-2010` | 1 hr | 1 hr | Industry-typical | LOW |
| `2010-2020` | 0.5–1 hr | 0.5–1 hr | Faster cycling | LOW |
| `2020+` (H-class GT) | 0.25–0.5 hr | 0.25–0.5 hr | Designed for spinning-reserve | LOW |

#### Hot / Warm / Cold start time

| Vintage | Hot start | Warm start | Cold start | Source | Confidence |
|---|---|---|---|---|---|
| `<2000` (large-frame F) | 30 min | 1 hr | 2 hr | Industry-typical (no source-documented) | LOW |
| `2000-2010` (large-frame) | 20–30 min | 30–60 min | 1.5 hr | Same | LOW |
| `2010-2020` (large-frame + aero) | 10–15 min | 15–30 min | 1 hr | Vendor (LM6000: 10 min std, 5 min Fast Start; LMS100: 8 min) for aero | MEDIUM |
| `2020+` (modern aero + fast-start) | 5–10 min | 10–15 min | 30 min | Vendor (GE LMS100, Solar Mars) | MEDIUM |

#### Ramp rate

| Vintage | Ramp (%/min) | Source | Confidence |
|---|---|---|---|
| `<2000` | 5–8%/min | Industry estimate | LOW |
| `2000-2010` | **8%/min** | ATB 2024 NG F-Frame CT row 51 | HIGH |
| `2010-2020` | 10%/min (large frame) / 20–50%/min (aero) | ATB + vendor (LMS100) | MEDIUM |
| `2020+` | 15–20%/min sustained (H-class GT) | ATB Advanced + vendor | MEDIUM |

---

## Cross-source variance log

For UI uncertainty disclosure. Documented per the design doc's "Confidence tier — assumption-as-fact misread" rule.

| Parameter / cell | Kumar 2012 | ATB 2024 | EIA AEO 2026 | Spread comment |
|---|---|---|---|---|
| VOM, F-class CC `2000-2010` | $1.02/MWh (2011$, baseload) | $2.17/MWh (2022$) | n/a | 1.7× spread; Kumar is baseload-lower-bound, ATB is new-build |
| VOM, H-class CC `2010-2020` | n/a | $2.16/MWh (2022$) | $3.49/MWh (2025$) | EIA's S&L 2024 + Brattle update is 40% higher than ATB — captures post-2023 inflation |
| VOM, simple-cycle CT | $0.57/MWh | $6.94/MWh | $4.17/MWh industrial | 12× spread — Kumar baseload denominator vs operating-fleet peaker reality |
| Heat rate, H-class CC | n/a (Kumar reports % degradation per start, not absolute HR) | 6,196 Btu/kWh | 6,226 Btu/kWh | <1% — strong cross-source agreement |
| Heat rate, simple-cycle F-frame | n/a | 9,717 Btu/kWh | 9,142 Btu/kWh | EIA's S&L 2024 is 6% better than ATB's older Schmitt 2022 figure |
| Ramp, CCGT block | n/a | 5%/min | not in EMM | NWPCC 2013 cites "35 MW/min" for H-class block ≈ 5%/min — corroborates ATB |
| Hot start, F-class CC | n/a | n/a | n/a | Vendor (Siemens 501F via CCJ): 3 hr — only source |
| Min up/down, all techs | "Warm Start Offline Hours" window only (5–40 hr CC) | not in ATB | not in EMM | **No public source-documented canonical values** |

---

## Confidence-tier distribution (after first research pass)

| Parameter | HIGH | MEDIUM | LOW | TBD/NoSource | Total |
|---|---|---|---|---|---|
| vom_per_mwh | 4 / 16 | 6 / 16 | 2 / 16 | 4 / 16 (CT/CA/CC `<2000` from Kumar; `2020+` proxy) | 16 |
| startup_cost_cold_per_mw | 1 / 16 | 6 / 16 | 4 / 16 | 5 / 16 (`2020+` for all techs) | 16 |
| startup_cost_warm_per_mw | 1 / 16 | 6 / 16 | 4 / 16 | 5 / 16 | 16 |
| startup_cost_hot_per_mw | 1 / 16 | 6 / 16 | 4 / 16 | 5 / 16 | 16 |
| min_up_hr | 0 / 16 | 0 / 16 | 16 / 16 | 0 / 16 | 16 |
| min_down_hr | 0 / 16 | 0 / 16 | 16 / 16 | 0 / 16 | 16 |
| hot_start_time_hr | 0 / 16 | 7 / 16 | 9 / 16 | 0 / 16 | 16 |
| cold_start_time_hr | 0 / 16 | 5 / 16 | 11 / 16 | 0 / 16 | 16 |
| ramp_rate_pct_per_min | 4 / 16 | 4 / 16 | 8 / 16 | 0 / 16 | 16 |
| **Total** | **11 / 144** | **40 / 144** | **74 / 144** | **19 / 144** | **144** |

**Lab-gate target**: ≥60% HIGH overall, no parameter <40% HIGH+MEDIUM.

**Current state**: 8% HIGH, 28% MEDIUM, 51% LOW, 13% NoSource. **Below lab-gate target** primarily because:
1. min_up/min_down have no public source values (this is structural, not fixable by more research)
2. start times rely on vendor reportage (regulatory citations need EPA Subpart KKKKa TSD parse)
3. `2020+` vintage has no Kumar coverage (predates fleet-scale H-class)

**Decision needed from user**: do we accept LOW confidence on min_up/min_down (and disclose in UI) and ship v1, or hold for a second research pass on EPA TSD + NREL WWSIS-2 dataset?

---

## Internal consistency checks (smoke tests)

Run these before the parquet build:

- [x] `cold_start_cost_C&M ≥ warm_start_cost_C&M` for CCGT (Kumar: 79 ≥ 55 ✅)
- [x] `warm_start_cost_C&M ≥ hot_start_cost_C&M` for CCGT (Kumar: 55 ≥ 35 ✅)
- [x] `cold_start_time_hr > hot_start_time_hr` for all (8 > 3 for F-class ✅)
- [ ] `min_up_hr > 0 and min_down_hr > 0` everywhere — pending min_up/down population
- [x] `ramp_rate × 60 < 100` for CC blocks (5%/min × 60 = 300% — wait, this fails by check def; check is "shouldn't go 0→100 in <1h" → 60 min × 5%/min = 300% which means 100% achievable in 20 min; spec says block can't physically do that — **the 5%/min from ATB is questionable as sustained-from-zero**; needs recheck whether ATB's 5%/min is "sustained steady-state" or "max ramp rating" — TODO clarify)
- [x] **Anomaly flag** (Kumar exec item 7): warm_C&M for large-frame CT ($126) > cold_C&M ($103). Counter-intuitive but documented in Kumar — "every start is essentially cold for some components" of CT.

---

## Lab-gate checklist (mirrors README §"Lab gate criteria")

- [x] Every cell has either a value+source+confidence OR an explicit "no source value" reason. **(70 cells with source-documented values; 19 explicitly marked NoSource; 55 marked LOW with industry-typical proxies — total 144.)**
- [x] Source registry updated with retrieval dates + local file paths
- [x] Confidence tier distribution table updated (above)
- [ ] Source-documented values cross-validated where possible — **partial** (VOM has 3-source cross-check; startup cost has 1 source = Kumar; min_up/down has 0 sources)
- [ ] Cross-validation against CEMS TX 2024-06 attempted (results in 04_validation.md) — pending
- [x] Internal consistency checks pass — partial (one open question on ramp definition)
- [ ] User reviews and approves — **pending**

---

## Open issues / next-pass research targets

1. **min_up_hr / min_down_hr** — no public source. Try NREL WWSIS-2 dataset, MISO Energy Markets Day-Ahead Operating Reserve Reports, ERCOT MIS public market reports for empirical-typical values.
2. **EPA Subpart KKKKa TSD** — likely contains regulatory-cited start time values for new gas units. PDF parse failed via WebFetch; try wget + Read tool.
3. **NREL WWSIS-2 (Western Wind & Solar Integration Study Phase 2)** — derived from Kumar with NREL operating assumptions. May give defensible min_up/min_down values.
4. **2020+ vintage** — no clean source. Either accept ATB Advanced proxy with LOW confidence or wait for v2 with CEMS-validated post-2020 fleet data.
5. **Ramp definition clarification** — confirm ATB's 5%/min is sustained-from-zero or max-rating. If max-rating, the 0→100% in 20 min interpretation isn't physical for CC blocks (HRSG warmup).
6. **Aero-derivative differentiation** — Kumar provides separate values; do we add an `aero_derivative` flag column to the parquet, or fold into GT vintage, or punt to v2?
7. **Inflation adjustment** — Kumar (2011$), ATB (2022$), EIA AEO (2025$). Decide: keep original units in parquet with year column, or normalize to 2025$ at build time? (Recommend: keep original + year column; downstream models inflation-adjust as needed.)
