# Glossary — Lockport Gas Turbine Digital Twin

> Single-page reference for every model-specific term. Organized by domain so related concepts read together; use Ctrl-F for direct lookups. Cross-references point to where the term is *implemented* (code) or *decided* (docs).
>
> If you're reading the model cold, start with [`pnl_ledger.md`](./pnl_ledger.md) (the one-glance economic view), then [`architecture.md`](./architecture.md) (the engine), then [`gaps_and_priorities.md`](./gaps_and_priorities.md) (what's missing). This doc is the lookup companion.

---

## §1. Markets and dispatch

**Ambient derate** — Adjustment to a generator's effective capacity based on outdoor temperature. Combustion turbines lose output in hot weather (denser air = more mass flow at cold; ~3% summer derate at 90°F for Lockport) and gain in cold (winter boost ~3%). v1 interpolates linearly between summer and winter values. *Code: [`dispatch_day_mode_aware`](../../notebooks/04_full_path_mode_comparison.py) §E.1.*

**Clean heat rate** — The mode's design heat rate before any degradation is applied (8,901 / 9,598 / 10,424 Btu/kWh for 3xCC / 2xCC / 1xCC). The "counterfactual" path in twin dispatch.

**Cogen / cogeneration** — A plant that produces electricity AND useful thermal output (process steam to an industrial host). Lockport is a cogen under a PURPA-era contract. Cogen plants often have higher VOM than pure-electricity plants and constraints from steam-host demand.

**Cold / warm / hot start** — Three start classifications based on hours-off since the last shutdown:
- **Hot**: `hrs_off < 8` (HRSG steam pressure still maintained)
- **Warm**: `8 ≤ hrs_off < 72` (some thermal reset)
- **Cold**: `hrs_off ≥ 72` (full overnight cool-down)
Each type has different fuel, EOH, fatigue, and Kumar 2012 C&M cost.

**Degraded heat rate** — The mode's heat rate scaled up by current state's `(1 + hr_recov/100)(1 + fouling/100)`. This is what the plant *actually* burns per MWh after engineering wear. The "actual" path in twin dispatch.

**DHTS (Daily Heat Tape Schedule)** — Lockport's daily steam-host obligation. Specifies how much process steam the plant must deliver to the industrial customer each day; functionally a must-run flag on cold days. In v1, modeled as a synthetic temp-based proxy (coldest 20% of days) until MOR DHTS data is extracted directly.

**Gas hub** — Pricing point for the natural gas the plant burns. v1 uses **Henry Hub** (the U.S. benchmark in Louisiana) per [ADR-001](../decisions/001-gas-hub-treatment-v1.md). Lockport actually burns gas delivered through Algonquin Citygate (New England zone), which sometimes trades at a premium ("basis"). v1 ignores this basis until v2.

**Henry Hub** — Louisiana natural gas pricing point; the U.S. benchmark for gas spot prices. Used as v1's delivered-gas proxy per ADR-001.

**LMP (Locational Marginal Price)** — The hourly clearing price of electricity at a specific NYISO node. Lockport's node is PTID 23791 (for the CTs) and 323769 (for the ST). v1 uses **day-ahead hourly** LMP from `lmp_da_hourly.parquet`.

**Must-run** — Flag that forces the plant online even when spark is negative. In v1, set on cogen-DHTS-style cold days; 1×CC operating mode fires at whatever loss the spark dictates. *Synthetic proxy in v1 — coldest 20% of days in the window.* See [`dispatch_mechanics.md §6`](./dispatch_mechanics.md) for the cogen physics.

**Mode** — **Ambiguous term — use one of the two specific names below.** In the codebase and earlier docs, "mode" was used for two completely different concepts. See [`dispatch_mechanics.md §1`](./dispatch_mechanics.md) for full disambiguation.

**Operating mode (3×CC / 2×CC / 1×CC)** — The plant's **physical configuration**: how many CTs are spinning. Three options: three CTs + 1 ST (3×CC, full block), two CTs + 1 ST (2×CC), one CT + 1 ST (1×CC). Each has its own heat rate and capacity. The dispatch picks one operating mode per hour. **In v1, 2×CC never wins** — see [`dispatch_mechanics.md §5`](./dispatch_mechanics.md).

**Operating mode capacity** — Block-level max output for an operating mode (3×CC = 221.3 MW; 2×CC = 172.6 MW; 1×CC = 123.9 MW), ambient-derated each hour.

**Operating mode heat rate** — Block-level Btu/kWh for an operating mode. Lockport's MOR-derived values: 3×CC 8,901; 2×CC 9,598; 1×CC 10,424. Lower is better; 3×CC is the most efficient operating mode.

**NYISO Zone A** — The Western New York electricity pricing zone (covers Buffalo / Lockport area). Lockport's electricity is priced in this zone.

**PTID** — NYISO node identifier. Lockport's PTID is 23791 (combustion turbines block) and 323769 (steam turbine block).

**PURPA** — Public Utility Regulatory Policies Act of 1978. Established Qualifying Facility (QF) status; many 1990s-era cogen plants (including Lockport) operate under PURPA contracts with above-market avoided-cost payments. Original terms vary; some are still active.

**RGGI (Regional Greenhouse Gas Initiative)** — NY's carbon-allowance program. The plant pays for CO2 emissions at the auction-clearing price (v1 uses $17/short ton). With EPA AP-42's 117 lb-CO2/MMBtu factor for natural gas, this works out to **$0.995/MMBtu** added to fuel cost. v1 keeps RGGI flat; Phase L can vary.

**Spark margin** — Hour-by-hour gross margin from selling electricity: `LMP × MWh − fuel cost − RGGI − VOM`. Note: gross — does **not** include LTSA costs, fixed O&M, financing, taxes, OR cogen-steam revenue OR capacity payments. See [architecture.md §6.4](./architecture.md) for the full breakdown and what's missing.

**Spark spread** — Power price minus the marginal fuel cost of generating that power. `LMP − HR/1000 × gas_$/MMBtu`. Industry shorthand; "spark margin" = spark spread net of VOM and RGGI.

**Steam host** — The industrial customer that buys process steam from Lockport under the cogen contract. Identity and contract terms TBD pending data-room extraction.

**Twin dispatch** — Each day, dispatch is computed **twice**: once with clean heat rate (counterfactual, ignores degradation) and once with degraded heat rate (actual). The difference is **loss to degradation** — the dollars per day that wear is costing the plant. Implemented in [`dispatch_day_mode_aware`](../../notebooks/04_full_path_mode_comparison.py).

**VOM (Variable Operations & Maintenance)** — Per-MWh non-fuel variable cost. v1 uses CT base default $1.02/MWh × cogen markup 1.35 = **$1.38/MWh**. The cogen markup is `assumed_industry` (mid-range of +30–50%); see [`caveats.md`](../../data/assets/lockport/caveats.md) §2.

---

## §2. Engineering — the state vector

**Combustion damage (df)** — Cumulative fatigue damage to combustion-section parts (Miner's rule). Increments by per-start values: cold +0.001, warm +0.0005, hot +0.0002. Drives the combustion forced-outage hockey-stick (P rises sharply when df / budget > 0.60). Halves at CI, resets to 0 at MI.

**Creep damage (dc)** — Cumulative high-temperature creep damage on hot-gas-path parts (Robinson's rule). Increments by `CREEP_RATE_PER_FIRED_HOUR (5e-6)` × fired hours. Halves at CI, resets to 0 at MI.

**EOH (Equivalent Operating Hours)** — The unit currency of GT wear. One fired hour at base load = 1 EOH. A start adds extra EOH (cold = 20; warm = 10; hot = 5 per `START_EOH_COST`). The metric LTSA contracts use to trigger inspections (CI at every 24,000 EOH; MI at every 48,000 EOH per Athens placeholder).

**Fatigue damage** — Synonym for **df** above.

**Fouling** — Compressor aerodynamic degradation from particulate buildup. Modeled as exponential approach to asymptote `FOULING_ASYMPTOTE_PCT (2.5%)` with time constant `FOULING_TAU_HRS (2000)`. Reduced by 70% at every CI (water wash).

**Heat rate (HR)** — Btu of fuel per kWh of electricity output. Lower is better. Lockport mode HRs: 3×CC 8,901; 2×CC 9,598; 1×CC 10,424 (real_observed from MOR). Multiply by `(1 + hr_recov/100)(1 + fouling/100)` for degraded value.

**hr_recov** — Recoverable HR degradation in %. Drifts up slowly with fired hours (~1e-5 per hour). Largely cleaned up at CI (70% recovered) and almost fully at MI (75%). Represents stuff like blade dirt, seal wear, valve calibration drift.

**HRSG (Heat Recovery Steam Generator)** — The boiler downstream of the CT exhaust that produces steam for the ST and (for cogen) for the steam host. A critical component; HRSG failures are typically owner-uncovered ($500K placeholder).

**HRSG cycles** — Number of thermal cycles (= number of starts). Drives HRSG fatigue. Reset to 0 at MI.

**Policy mode EOH-rate multiplier** — How much faster (Policy A = 1.0) or slower (Policy B = 0.875; Policy C = 0.65) each policy mode is *projected* to burn EOH. Affects only the pre-built maintenance schedule's projected calendar dates, NOT the actual EOH burn during simulation.

**Plant state vector** — The 12-field `PlantState` dataclass that propagates from day N to day N+1: 9 stress accumulators + 3 operational continuity fields. In N4, extended with 2 outage-tracking fields. *Code: [`PlantState`](../../notebooks/04_full_path_mode_comparison.py) §C.*

**P_forced (forced-outage probability)** — Combined daily probability of any forced outage, assembled from 3 components: P_GT (combustion + TBC + rotor), P_HRSG, P_BG. Independence assumption: `P_combined = 1 − (1−P_GT)(1−P_HRSG)(1−P_BG)`. Capped at 10%/day. *Code: [`p_forced_components`](../../notebooks/04_full_path_mode_comparison.py) §E.4.*

**Rotor life** — Fraction of rotor's design life consumed. Increments by `ROTOR_LIFE_PER_FIRED_HOUR (1e-7)` × fired hours. Halved at MI.

**Stress accumulator** — Any of the 9 state-vector fields that accumulate damage / wear and drive engineering behavior. The model's memory of plant history.

**TBC (Thermal Barrier Coating)** — Ceramic coating on hot-section blades that insulates them from combustion temps. Fails by a Weibull-distributed time-at-temp process. Once TBC fails, blades cook. v1 uses a path-specific TBC threshold sampled at sim start; resampled at every MI.

**TBC threshold** — The Weibull-sampled value (β=3, η=28,000 hours) above which TBC is presumed failed. Below threshold, hazard rate scales as a power function; at threshold, P_TBC jumps to 1.0. Resampled at every MI to reflect new coating after refurbishment.

**tbc_time** — Cumulative time-at-temperature (= fired hours) on the current TBC coating. Reset to 0 at MI. Drives `P_TBC` via Weibull hazard rate.

---

## §3. Contracts — LTSA structure

**Availability penalty** — Annual true-up at year-end: if the plant was available less than the guarantee (95% in placeholder), the owner pays `(monthly_fee / 12) × shortfall × 10`. Small but compounds across years.

**CI (Combustion Inspection)** — Mid-life inspection focused on combustion-section parts. Triggers at every 24,000 EOH (placeholder Athens threshold). $3.75M total cost, 75% OEM-covered → $937K owner-uncovered. 12-day outage.

**CI owner-uncovered** — The 25% of CI cost the owner pays beyond what the OEM contract covers. $937K in placeholder; real value from data room.

**Cycle (LTSA sense)** — The period between two inspection events (CI or MI). At cycle-end, the HR penalty is computed against the cycle-average heat rate vs the contract guarantee.

**Cycle-end HR penalty** — Charged at every CI / MI: if `cycle_avg_HR > guarantee × (1 + tolerance)`, owner pays `excess_fuel_$ × 1.25`. Fires only if the plant's degradation pushed HR past the contract tolerance.

**EOH reserve** — Stream 2 of the LTSA. Daily accrual: `delta_eoh × $175/EOH × escalation`. Accrues every fired hour and every start. Goes to a maintenance fund the OEM manages.

**Fixed monthly fee** — Stream 1 of the LTSA. $850K/month placeholder. Daily accrual: `$27,945/day × escalation`. **Dominant LTSA cost over 9 years (49% of total in Mode A).** Owner pays even if plant is in outage.

**Forced outage owner-cost** — Cost charged when a forced outage fires. Classified by cause:
- GT mechanical → $0 (OEM-covered, the "core" warranty)
- HRSG → $500K (outside CSA scope, owner-uncovered)
- BG (BoP / controls / generator) → $750K (outside CSA scope, owner-uncovered)
All placeholder values.

**Hard stop** — Inspection trigger condition: fires when `state.eoh > scheduled_threshold + 1,500 EOH`. Prevents EOH from drifting far past the contract threshold even if the calendar projection was off. *Code: N4 §E daily-loop step 11.*

**HR penalty** — Stream 7 of the LTSA. Fires at each CI / MI if cycle-avg HR > guarantee × (1 + tolerance). Owner pays excess fuel cost × 1.25 penalty multiplier. v1 uses 3×CC clean HR as the guarantee proxy (real value pending data-room extraction).

**Inspection event** — A CI or MI firing. Triggers: (a) calendar date reached, OR (b) hard-stop EOH overage. Effects: owner cost charged, HR penalty computed, state resets applied, plant offline for outage duration.

**LTSA (Long-Term Service Agreement)** — The maintenance contract between plant owner and OEM (likely GE for Lockport). Defines the 7 cost streams, the OEM-covered vs owner-uncovered scope, the inspection cadence, and the performance guarantees. Lockport's actual contract terms are in the data-room file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx`; v1 uses Athens-prototype placeholders for all values.

**MI (Major Inspection)** — Full overhaul. Triggers at every 48,000 EOH (placeholder). $30M total cost, 65% OEM-covered → $10.5M owner-uncovered. 52-day outage. Resets most state accumulators aggressively (see "MI resets" below).

**MI owner-uncovered** — The 35% of MI cost the owner pays beyond what the OEM contract covers. $10.5M in placeholder.

**MI resets** — State changes at every MI: `dc → 0; df → 0; fouling × 0.3; hr_recov × 0.25; tbc_time → 0; tbc_thresh ← Weibull resample; hrsg_cycles → 0; rotor_life × 0.5`. Reflects refurbished hot-section parts.

**CI resets** — State changes at every CI: `dc × 0.5; df × 0.5; fouling × 0.3; hr_recov × 0.3`. Less aggressive than MI; only combustion-related accumulators touched.

**OEM (Original Equipment Manufacturer)** — The party that designed and sold the turbines. For 1992 F-class, GE Power Systems. Counterparty to the LTSA.

**OEM-covered** — LTSA scope items the OEM bears the cost of: most GT mechanical repairs, hot-gas-path parts at scheduled inspections, combustion components. Funded by the owner's fixed fee + EOH reserve.

**Owner-uncovered** — Anything outside the OEM's scope, paid directly by the owner: HRSG repairs, BoP / controls / generator / ST repairs, the 25-35% portion of inspection costs above the OEM share, start overage, availability/HR penalties.

**Owner scope** — The owner's side of the contract: paying the fixed fee + EOH reserve, plus any costs not in OEM scope.

**Shoulder-snap** — Maintenance scheduling convention: scheduled inspection dates are snapped forward to the next April 1 or October 1 (the "shoulder" seasons between summer peak and winter peak), avoiding outages during high-LMP periods. *Code: [`snap_to_shoulder`](../../notebooks/04_full_path_mode_comparison.py) §D.*

**Start overage** — Stream 5 of the LTSA. If YTD count of starts (by type) exceeds the pro-rated annual baseline (placeholder: 150 hot / 35 warm / 5 cold per year), each excess start charges an overage fee ($8,500 hot / $42,000 warm / $125,000 cold per placeholder).

---

## §4. Policy mode (also called "dispatch policy mode")

**Policy mode** — The **outer-axis policy** that determines `wear_mult` for the dispatch decision. Three options (A / B / C) with different self-curtailment behavior near inspection thresholds. Distinct from operating mode (3×CC / 2×CC / 1×CC) — see [`dispatch_mechanics.md §1`](./dispatch_mechanics.md) for the disambiguation.

**Policy mode A** — "No self-curtailment" policy. Wear penalty multiplier always 1.0×. Plant dispatches purely on economics; ignores EOH proximity to inspection. Highest spark margin; earliest inspection trigger.

**Policy mode B** — "Moderate self-curtailment" policy. Wear penalty ramps from 1.0× to 2.5× as EOH headroom shrinks from 4,000 → 1,000 below the next inspection threshold. Caps at 2.5×.

**Policy mode C** — "Aggressive self-curtailment" policy. Wear penalty ramps from 1.0× to 4.0× as EOH headroom shrinks from 4,000 → 0. Caps at 4.0×.

**Wear penalty multiplier (`wear_mult`)** — A scalar set once per simulation day from `(policy_mode, eoh_headroom)`. Applied to GT-share (42%) of the Kumar 2012 start C&M cost; amortized over a 6-hour expected min-run-streak to produce an effective per-MWh hurdle when starting. Higher multiplier → higher hurdle → fewer starts → slower EOH burn → delayed inspection. Only applies when the plant is currently off (start decision); has no effect on continue-running decisions.

**EOH headroom** — `scheduled_threshold − state.eoh`. The buffer of EOH the plant has before the next inspection fires. Drives the wear penalty curve in Policy modes B / C.

---

## §5. Events and run mechanics

**Calendar trigger** — Inspection trigger condition: fires when today ≥ scheduled_date for the next event in the pre-built schedule.

**Cycle (event sense)** — See "Cycle (LTSA sense)" in §3.

**Daily loop** — The 12-step sequence run every simulation day, per asset, per mode. See [architecture.md §5.2](./architecture.md) for the full flow.

**Forced outage** — Unplanned outage event sampled daily against `P_forced`. Cause weighted by component probabilities (GT / HRSG / BG); duration sampled lognormal (median 8 / 12 / 5 days respectively); cost charged per cause classification.

**Forced-outage cause weighting** — Probability of each cause given that an outage fires: `weights = [P_GT, P_HRSG, P_BG] / (P_GT + P_HRSG + P_BG)`. *Code: [`sample_outage_cause`](../../notebooks/04_full_path_mode_comparison.py) §E.5.*

**Hot / warm / cold start** — See §1.

**Inspection event** — See §3.

**Lognormal duration** — Forced outage duration drawn from `LogNormal(ln(median), σ=0.5)`, then floored at 1 day.

**Pre-built schedule** — Maintenance schedule projected at sim start, mode-by-mode, from current EOH and the EOH-rate estimate. Projects next 5–20 inspection events with calendar shoulder-snap. Re-checked daily; events fire on calendar or hard-stop.

---

## §6. Outputs

**Daily summary parquet** — Per-mode, one row per simulation day with all dispatch and LTSA columns. Use for any "what happened on day N" pivot. File: `daily_summary_mode_{a,b,c}.parquet`.

**Forced outage event record** — One row per fired event with date, cause, duration, owner cost, state at trigger. File: `forced_outage_events.parquet`.

**Inspection event record** — One row per fired CI / MI with date, trigger (calendar or hard-stop), threshold, state at trigger, outage days, owner cost, HR penalty. File: `inspection_events.parquet`.

**LTSA streams parquet** — Per-mode, cumulative daily values for each of the 8 LTSA cost streams (7 stream contract + forced outage cost). File: `ltsa_streams_mode_{a,b,c}.parquet`.

**Loss to degradation** — Daily metric: `margin_clean − margin_degraded`. The dollars per day that current engineering wear is costing the plant in spark margin. Always non-negative.

**Model card** — `model_card.md` written into each run bundle. Single-page summary of the run: data vintages, assumption distribution, mode comparison, LTSA breakdown, MOR backtest, caveats, output artifacts. Required per [`assumptions/README.md`](../assumptions/README.md).

**Net P&L** — Headline output: `spark margin − LTSA owner-uncovered`. **In v1, severely understates real economics** because (a) LTSA values are placeholder, (b) steam revenue is not modeled, (c) capacity revenue is not modeled, (d) dispatch over-commits vs MOR. See [architecture.md §6.4](./architecture.md) for the full caveat list.

**Run bundle** — Directory at `data/outputs/lockport/runs/notebook4_<timestamp>/`. Contains model_card.md, run_config.yaml, and per-mode parquets. Gitignored. Reproducible from `run_config.yaml`.

**run_config.yaml** — Reproducibility file capturing the seed, mode params, escalation rate, every input constant. With identical inputs + this config, the run is reproducible.

**State trajectory parquet** — Per-mode, daily state-vector columns (eoh, hr_recov, fouling, dc, df, p_combined, etc.). File: `state_trajectory_mode_{a,b,c}.parquet`. Use for "how did state evolve" pivots.

---

## §7. Methodology and modeling concepts

**ADR (Architectural Decision Record)** — A markdown doc in [`docs/decisions/`](../decisions/) capturing a substantive decision with full reasoning trail: context, decision, reasoning, alternatives, consequences, references. Pattern: one file per decision; index in `decisions/README.md`. Current ADRs: 001 (gas hub), 002 (calibration buckets).

**Assumed_industry** — Status code for values pulled from broad industry rules-of-thumb. Lower confidence than `real_*` but typed and sourced.

**Assumed_techclass** — Status code for class-level defaults (e.g., "F-class mean from Kumar 2012"). Used for cross-asset priors.

**Assumed_vendor** — Status code for OEM-published specifications for the equipment family.

**Assumption status** — One of 9 codes attached to every YAML leaf value: `real_observed`, `real_reported`, `real_computed`, `assumed_techclass`, `assumed_vendor`, `assumed_industry`, `assumed_derived`, `placeholder`, `not_applicable`. See [`assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md).

**Bucket A / B / C (per ADR-002)** — Calibration map for Lockport:
- **A**: Lockport-specific real_* values (heat rates, LMP, ambient, cold-start gas)
- **B**: Generic-F-class assumed_* defaults (state-evolution constants from Athens prototype)
- **C**: Placeholder pending data room (all LTSA contract values)

**Bucket B sensitivity** — The Athens-prototype state-evolution constants are the model's largest unverified parameters; per the prototype's tornado, `P_BG_AGE_MAX` and `FATIGUE_PER_*_START` dominate. Phase L Monte Carlo sweeps these.

**Historical replay** — v1 simulation strategy: play actual 2017–2025 LMP / gas / weather forward as a single deterministic path. Gives us a real MOR backtest target. Phase L flips to synthetic.

**Loss attribution** — See "Loss to degradation" in §6.

**Monte Carlo (Phase L)** — Multi-path simulation: run N≥50 paths with sampled RNG seeds and sampled Bucket B constants. Produces P10 / P50 / P90 distributions on every output. Not yet built.

**MOR (Monthly Operating Report)** — Regulatory filing every U.S. plant submits to the EIA + NYISO with monthly generation, fuel use, mode hours, planned and forced outages. The truth-table for backtests. Lockport's 2024 MOR: 192,494 MWh, ~7 cold starts, 65/26/9 mode-day mix.

**MOR backtest** — Comparison of model output (typically Mode A in 2024) against MOR-observed reality. v1 backtest divergence: modeled 2.4× more generation than MOR. Causes documented in [architecture.md §7.4](./architecture.md).

**Placeholder** — Status code for typed values without a real source. Common for LTSA fields awaiting data-room extraction. Numerically valid but not deal-realistic.

**Real_computed** — Status code for values derived from `real_observed` data via a deterministic formula. Example: cold-start warming gas mean = `sum(cold_start_gas) / count(cold_starts)` from MOR.

**Real_observed** — Status code for values measured directly from the asset's operating data (MOR, SCADA, EIA-860).

**Real_reported** — Status code for values pulled from a regulatory filing or contract document.

**Single-path** — One realization of the daily-loop simulation with one fixed RNG seed. v1 is single-path. Forced outage timing and TBC threshold are RNG-dependent → different seeds produce different (often materially different) numbers.

**Status taxonomy** — The 9-code grammar plus the schema requirements (every leaf must have `value`, `status`, `source`; placeholders must have `validation_path`; assumed values should have `confidence`). See [`assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md).

**Synthetic scenario** — Alternative to historical replay: sample LMP / gas / weather paths from a scenario engine (Step 1 in model-gpr's roadmap). Phase L Monte Carlo will use these.

---

## §8. Quick reference: dollar units used in v1

All dollar amounts in the model and outputs are **nominal USD** unless explicitly noted otherwise.

- **Gas prices**: USD per MMBtu (e.g., Henry Hub ~$3.50)
- **LMP**: USD per MWh
- **VOM**: USD per MWh
- **Spark margin**: USD per hour, summed to per-day, summed to per-window
- **LTSA fixed fee**: USD per month, escalated at 3.5%/yr
- **LTSA EOH reserve**: USD per EOH burned
- **Inspection costs**: USD total cost, with OEM-covered fraction and owner-uncovered amount specified
- **Forced outage repair costs**: USD per event by cause
- **Net P&L**: USD per simulation window (typically 9 years in N4)
- **Cumulative LTSA stream**: USD over the simulation window, in nominal terms

Year-over-year inflation in nominal USD is captured by the LTSA escalation factor (3.5%/yr placeholder). Spark side is **not** inflation-adjusted in v1 — LMP, gas, RGGI all in the year-of-record nominal dollars they were observed in.
