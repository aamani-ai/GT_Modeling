# Understanding the Gas Turbine Digital Twin

A reader's guide to the implementation living in [docs/extra/gas-turbine-digital-twin/](docs/extra/gas-turbine-digital-twin/). Written for someone on the InfraSure team who has read `InfraSure_ModelingFramework_V2.md` and wants to know what is actually in the code, how the layers fit together, what is prototype, and where the gaps are.

---

## 1. What this repo is, in one paragraph

The InfraSure Gas Turbine Digital Twin is a probabilistic asset twin for a specific CCGT (Athens-type GE 7FA.03 ×2, NYISO Zone F) that couples three layers on a daily time step over a 10-year investment horizon. It is **not** a pure dispatch model and **not** a pure financial waterfall — it is the feedback loop between them, with an engineering state vector as the missing middleware. Each day, dispatch decisions update engineering stress, engineering stress reshapes next-day plant economics and event probabilities, and the LTSA contract is the price list that converts everything into owner cashflow. The output is a P10 / P50 / P90 distribution of spark spread, LTSA cost, capacity factor, and inspection timing across simulation paths and dispatch policies.

## 2. Why "more than a dispatch model"

A standard merchant dispatch model answers "given hourly prices, heat rate, capacity, and start costs, what's the maximum spark spread?" It treats the plant as static. That model cannot tell you:

- **When the next CI / MI hits** — these are lumpy $3.75M / $30M events that depend on EOH burn, which depends on how the unit was dispatched.
- **What share of forced-outage repair cost is owner-uncovered** — HRSG, BOP, ST, generator are all *excluded* from CSA scope. So aggressive cycling that drives HRSG drum fatigue produces owner-paid repair bills the dispatch model can't see.
- **How much spark spread is being eroded by degradation between inspections** — HR drifts up, capacity drifts down, and dispatch hours move with them.
- **How close you are to availability / HR / overage breach** — each of which triggers contractual penalties.

A pure engineering model tracks all of the above but cannot price it. A pure financial model can price LTSA events but has no idea when they will happen. The digital twin sits between the two: dispatch generates stress → stress drives state and event probabilities → LTSA converts events to cashflow → degraded state feeds back to tomorrow's dispatch.

The investor view is `EBITDA ≈ spark − LTSA_total − non_LTSA_O&M`. Only the twin produces a credible distributional path for `LTSA_total`, because that quantity is driven by *how* the plant was operated, not just by the contract.

## 3. The three layers

### 3.1 Engineering twin — [EnggDTwin_model.py](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py)

A **stateful library**, not a runner. Owns the plant constants (HR_ISO=7,070 BTU/kWh; CAP_ISO=531 MW; start costs by type), the eight stress accumulators, and the inspection reset semantics.

Key entry points:

| Function | What it does |
| :--- | :--- |
| `init_state(rng)` ([:118](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L118)) | Returns the day-0 plant state vector (post-HGP at 24,000 EOH, all stress counters reset, TBC threshold sampled per path) |
| `cap_eff(temp_f)` ([:72](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L72)) | Effective capacity after ambient derate (−0.5%/°F above 59°F ISO, clipped to [0.80, 1.05] × ISO) |
| `hr_clean(temp_f)` ([:78](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L78)) | Baseline HR with ambient correction only — the "clean reference" |
| `hr_degraded(hr_recov_pct, fouling_pct, temp_f)` ([:83](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L83)) | Adds HGP recoverable degradation and compressor fouling on top of clean |
| `update_stress(state, fired_hrs, starts, avg_temp, avg_aqi)` ([:146](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L146)) | Daily accumulator update: EOH, creep `D_c`, fatigue `D_f`, fouling, HGP wear, TBC time, HRSG cycles, rotor life |
| `p_forced_outage(state, year_frac)` ([:191](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L191)) | Daily endogenous forced outage probability decomposed into GT / HRSG / BOP |
| `apply_inspection_reset(state, itype, ...)` ([:220](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L220)) | Resets the appropriate stress counters at CI or MI completion; also returns the HR cycle-end penalty (delegated to `LTSAContract`) |

The engineering twin owns no time loop — the dispatch module drives it day-by-day.

### 3.2 Dispatch engine — [dispatch_model.py](docs/extra/gas-turbine-digital-twin/dispatch_model.py)

The day-by-day driver across `N_LONG_PATHS × N_YEARS × N_DAYS × 24` (50 paths × 10 years × 365 days × 24 hrs per current prototype config). The hourly dispatch is **heuristic**, not a true MIP: each hour decides commit / decommit by comparing spark spread to a start-cost-based hurdle, respecting min-run and min-down by start type.

| Function | What it does |
| :--- | :--- |
| `hourly_dispatch(...)` ([:173](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L173)) | 24-hour commit/dispatch for one day. Determines start type from hours-off (hot < 8 hrs / warm < 72 / cold ≥ 72), computes hurdle from start cost amortized over min-run, applies mode EOH-proximity penalty to the wear fraction (42%) of start cost. |
| `run_path(j, mode, inp, maint_schedule, rng)` ([:249](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L249)) | 10-year sequential daily simulation for one path × mode. This is where the feedback loop lives. |
| `build_maint_schedule(eoh_rate)` ([:101](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L101)) | Pre-builds the inspection calendar by projecting EOH burn forward and snapping to next April/Oct shoulder month. |
| `estimate_eoh_rate(inp)` ([:133](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L133)) | Heuristic to estimate average EOH/year from the market inputs (fraction of hours with positive clean spark spread → fired hours → EOH from hours + EOH from a typical start mix). |

**The "twin dispatch" attribution trick.** On every non-outage day, `run_path` calls `hourly_dispatch` *twice*:

1. Once with `hr_clean` and base mode A → `cr` ("clean reference")
2. Once with `hr_degraded` and the real mode → `dr` ("degraded actual")

`loss_degradation = cr['spark'] − dr['spark']` is the attribution to degradation. This is what splits realized spark spread cleanly into:

```
spark_clean = spark_actual + loss_degradation + loss_planned + loss_forced
```

Each loss component is stored daily (see [dispatch_model.py:226-243](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L226-L243)) so quarterly / annual attribution is trivial downstream.

### 3.3 LTSA contract wrapper — [LTSAContract.py](docs/extra/gas-turbine-digital-twin/LTSAContract.py)

Converts engineering events into owner cashflow. All numbers are tagged `[ASSUME]` pending actual contract review. The contract structure is hybrid: **fixed base + variable EOH + event-based**.

| Cost component | Source | Calculation |
| :--- | :--- | :--- |
| Fixed monthly fee | `daily_fixed_fee` ([:84](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L84)) | $850K/month × 12 / 365, escalated 3.5%/yr |
| Variable EOH reserve | `daily_eoh_reserve` ([:99](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L99)) | $175/EOH × daily EOH accumulated, escalated |
| CI inspection event | `inspection_cost('CI')` ([:114](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L114)) | $3.75M total: 75% OEM-covered, 25% owner-uncovered (~$937K); 12-day outage |
| MI inspection event | `inspection_cost('MI')` | $30M total: 65% OEM-covered, 35% owner-uncovered (~$10.5M); 52-day outage |
| Start overage charges | `overage_charge` ([:142](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L142)) | YTD start counts pro-rated vs. annual baseline (150 hot / 35 warm / 5 cold / 3 trip); excess × $8.5K / $42K / $125K / $80K |
| Availability penalty | `availability_penalty_annual` ([:173](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L173)) | If annual avail < 95%: `(monthly_fee / 12) × shortfall × 10` |
| HR penalty (cycle-end) | `hr_penalty_cycle` ([:197](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L197)) | If cycle-avg HR > 2% above guarantee: excess fuel cost × 1.25 |
| Forced outage repair classification | `classify_forced_outage_cost` ([:235](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L235)) | GT mechanical in-scope = OEM-covered; HRSG / BOP / ST = owner-uncovered ($500K / $750K / $200K typical repair) |

The critical asymmetry: a sizeable portion of failure modes — HRSG, BOP, ST, generator — sit **outside** the CSA scope. So dispatch policies that drive HRSG cycling damage hit owner cashflow directly without OEM cushion. This is why the twin must track HRSG drum cycles separately from GT EOH.

## 4. The daily feedback loop — order of operations

Inside [run_path](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L249), the order on each day matters. It is, in sequence:

1. **Load today's inputs**: hourly temp, AQI, power, daily gas price for `(path, sim, day)`.
2. **Compute today's effective plant parameters**: `hr_clean`, `hr_degraded(state)`, `cap_eff(temp)`, delivered gas price, daily fixed LTSA fee.
3. **Compute EOH headroom** to next pending inspection threshold — this drives the mode penalty.
4. **Run clean reference dispatch** (mode A, no EOH penalty) — produces the counterfactual baseline.
5. **Run degraded actual dispatch** (current mode, current state, current headroom) — but **don't apply state changes yet**.
6. **Check continuing outage**: if `outage_days > 0`, decrement, attribute loss to `loss_planned` or `loss_forced + loss_degradation`, and skip to next day. On the final day of a planned outage, call `apply_inspection_reset` (which also computes the HR cycle penalty).
7. **Check calendar maintenance triggers** (in priority order):
   - **Hard stop**: if `eoh ≥ next_threshold + 1,500`, force inspection immediately regardless of season.
   - **Calendar match**: if `gd ≥ scheduled_gd`, trigger the inspection.
8. **Check forced outage**: compute `p_forced` from state, apply EOH overage multiplier (up to 2.5×), draw against random number. If triggered, classify cause (GT / HRSG / BOP) weighted by component probability, sample lognormal outage duration, attribute loss, skip to next day.
9. **Execute dispatch**: now commit to the degraded dispatch result. Update state operating flags (`op`, `hrs_off`, `run_hrs`).
10. **Update stress accumulators** via `update_stress` — this is where today's dispatch becomes tomorrow's degraded state.
11. **Accrue LTSA charges**: daily EOH reserve, incremental YTD overage, increment cycle counters for the next inspection HR penalty.

At year end, compute annual availability and post the availability penalty if `< 95%`.

The forced-outage check happens **before** dispatch execution, on purpose: if the unit is going to fail today, it cannot generate today's spark even if prices are excellent.

## 5. The three dispatch modes

The investor question is "how much gross margin do you sacrifice by self-curtailing near EOH thresholds to push CI/MI into a more favorable shoulder window?" The three modes are heuristic answers; the model compares them ex-post.

| Mode | EOH proximity penalty on start-cost wear | EOH rate multiplier (for calendar) | Behavior |
| :--- | :--- | :--- | :--- |
| **A** — maximize dispatch | None (1.0× always) | 1.00 | Dispatches whenever energy margin > 0. Accelerates EOH. Baseline for attribution. |
| **B** — balanced | 1.0× when headroom > 4,000 EOH, scaling linearly to 2.5× at 1,000 EOH | 0.875 | Self-curtails on marginal days as inspection approaches. |
| **C** — minimize LTSA | 1.0× when > 4,000 EOH, scaling to 4.0× at 0 EOH | 0.65 | Heavy self-curtailment near thresholds; cold starts strongly penalized. Defers inspections into later shoulder windows. |

Two subtleties worth flagging:

- **The wear penalty applies only to the 42% GT wear fraction of start cost**, not to the HRSG/ST share. Cold start = $176K total, of which $73.9K is GT wear and gets the multiplier; the rest is unchanged. See [dispatch_model.py:181-196](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L181-L196).
- **Each mode gets its own maintenance calendar.** Because Mode C accumulates EOH slower, `build_maint_schedule` is called with `EOH_RATE_ESTIMATE × 0.65`, projecting inspections later in time. They may slip into a *different* April / October shoulder window than Mode A's calendar. So mode differences are not just about start curtailment — they include genuinely different inspection cadences.

Per the Athens pilot summary (Appendix C of the framework doc): Mode C sacrifices ~$1.3M/yr in spark spread to save ~$80M in LTSA over 10 years — net ~$67M benefit. That is the headline trade-off this framework is built to surface.

### 5.1 Are the modes "optimization"? — what the architecture does and doesn't support

A natural question: *"Can I tell this model to optimize for maximum profit, or for minimum LTSA cost?"* The answer needs to be stated precisely, because the modes look like objectives but aren't.

**Strictly: no — there is no optimizer.** The model runs three fixed heuristic policies (A/B/C), simulates outcomes, and the user compares results ex-post. Each mode is just two knobs — the start-cost penalty curve in `eoh_penalty_mult` ([dispatch_model.py:71-84](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L71-L84)) and the EOH-rate multiplier in `MODE_EOH_MULT` ([dispatch_model.py:66](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L66)). The Athens result that "Mode C nets +$67M over Mode A" is a trade-off illustration, not proof Mode C is the optimum — almost certainly there's a parameter setting between B and C that's better, and the model doesn't search.

**Mapping modes to objectives:**

| Mode | Implicit objective | What it does mechanically |
| :--- | :--- | :--- |
| A | Maximize gross spark spread | Ignores EOH proximity entirely. Dispatches whenever energy margin > 0. |
| C | Minimize 10-year LTSA cost | Self-curtails aggressively near inspection thresholds; pre-builds the calendar assuming slower EOH burn so inspections project further out. |
| B | Heuristic middle ground | Same shape as C but milder penalty + milder calendar adjustment. |

So Mode A ≈ "purely chase revenue" and Mode C ≈ "purely manage LTSA cost." But neither is a true math-optimization solution — they're hand-crafted policy bookends.

**What the architecture supports — three levels of capability:**

1. **Mode comparison (what exists today).** Pick a handful of hand-crafted policies, simulate, compare. Good for showing investors a trade-off curve. Bad for actually *finding* the best policy.

2. **Parametric sweep (cheap next step, ~1 day of work).** Wrap the existing code in a loop over (penalty curve steepness × headroom breakpoint × EOH-rate multiplier). Compute a chosen objective per simulation — e.g. `NPV(spark_actual − ltsa_uncovered_total − non_LTSA_O&M)` — and pick the parameter combination that maximizes it. Still heuristic, but searches a real parameter space and would likely beat any of A/B/C as currently tuned.

3. **True optimization (genuinely missing — the planned next phase).** A rolling-window MIP/LP that, each day, takes forecast prices and current degraded state and solves: *"given my probability of forced outage and projected inspection timing, what's the dispatch and maintenance plan that maximizes 10-year expected NPV subject to availability and other constraints?"* This would replace the heuristic spark-vs-hurdle commit at [dispatch_model.py:187-213](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L187-L213). The framework doc §3.4 explicitly names this as a future phase ("the dispatch model will re-optimize each day's schedule using the prior day's degraded plant state").

**Architectural verdict.** The daily-loop scaffold (engineering twin ← dispatch decision ← LTSA wrapper, feeding back day-by-day) is **the right structure for any of the three levels above**. The state vector, the LTSA cost decomposition, and the clean-vs-degraded attribution outputs are all in place. Nothing in the current code blocks a true optimizer from being dropped in as a replacement for the heuristic. What's missing is the optimizer itself — not the framework around it. So when an investor asks "can this thing optimize for X?", the honest answer today is: it shows you the trade-off via A/B/C, and the scaffolding is ready for a proper optimizer once we build one.

## 6. State vector reference

The plant state, initialized in [init_state](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L118):

| Field | Meaning | Reset by |
| :--- | :--- | :--- |
| `eoh` | Contractual equivalent operating hours | Never (cumulative); inspection schedule is offset from initial value |
| `hr_recov` | Recoverable HGP HR degradation (%) | Partial at CI (30%), strong at MI (75%) |
| `fouling` | Compressor fouling (% HR impact, exponential approach to A=2.5%) | CI water wash (70%) |
| `dc` | Creep damage fraction (Robinson life-fraction) | CI halves; MI zeros |
| `df` | Fatigue damage fraction (Miner's rule) | CI halves; MI zeros |
| `tbc_time` | TBC time-at-temperature (hrs) | MI zeros |
| `tbc_thresh` | Per-path Weibull failure threshold (β=3, η=28,000) | Re-sampled at CI and MI |
| `hrsg_cycles` | HRSG HP drum cycle accumulation | MI zeros |
| `rotor_life` | Rotor life fraction consumed (starts at 0.35) | Never (no rotor replacement) |
| `insp_done` | Inspections completed so far | Increments at each inspection |
| `outage_type`, `outage_days` | Current outage classification + remaining days | Set on outage entry, cleared on exit |
| `op`, `hrs_off`, `run_hrs`, `min_run`, `last_stype` | Dispatch continuity (carries across day boundaries) | Updated each hour by `hourly_dispatch` |

**Why creep and fatigue are coupled, not parallel.** Standard EOH-only LTSA accounting tracks creep and fatigue as independent counters. The materials-science literature is clear that they interact synergistically — components fail earlier than either mechanism alone would predict. The model implements an ASME N-47 / RCC-MRx interaction envelope: if either dominates, the limit is `D_c + D_f ≤ 1.0`; in the mixed regime (both > 0.05), the limit drops to 0.7 ([EnggDTwin_model.py:168-171](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L168-L171)). When the envelope is reached, both counters halve (an inspection-equivalent reset).

The contractual EOH counter and the physics-based damage counter are **tracked separately and can diverge**. A heavily cycled unit can exhaust its physics-based damage budget before reaching contractual EOH — producing elevated forced-outage risk between scheduled inspections that a pure EOH-based model cannot see.

## 7. Endogenous forced outage

This is one of the strongest design moves in the model. Rather than imposing a static forced outage rate (FOR), the model computes daily `P_forced` from the current stress state ([EnggDTwin_model.py:191-217](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L191-L217)):

```
P_forced = 1 − (1 − P_GT)(1 − P_HRSG)(1 − P_BG)
```

Component breakdown:

- **P_GT = P_combustion + P_TBC + P_rotor**
  - `P_combustion` rises as `D_f / COMB_BUDGET` crosses the hockey-stick inflection (60%). Below that, it's near zero. Above, `excess² × 0.10` capped at 10%/day.
  - `P_TBC` is Weibull hazard. If `tbc_time` exceeds the path-specific sampled threshold → `P_TBC = 1.0` (forced outage guaranteed). Below threshold, conditional hazard rate.
  - `P_rotor` is a tiny baseline (~0.003%/day) scaled by rotor life fraction.
- **P_HRSG** — baseline 0.75%/day, scaled by HRSG drum cycles and plant age (1.0× → 1.5× over 10 years).
- **P_BG** — residual non-GT, non-HRSG (controls, generator, BOP) at 0.4%/day, also age-scaled.

When the random draw fires, the cause is selected by weighted probability across `(p_gt, p_hrsg, p_bg)`, an outage duration is sampled from a lognormal (medians: 8d / 12d / 5d), and the repair cost is classified per the LTSA coverage rules. The EOH overage multiplier (up to 2.5×) is applied to `P_forced` when the unit is running past a calendar-scheduled inspection while waiting for shoulder season.

## 8. Calendar maintenance scheduling

Real plants don't do MIs in July when prices are highest. The model captures this with shoulder-month snapping ([dispatch_model.py:90-131](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L90-L131)):

1. Project the day the EOH threshold will be hit using the estimated EOH burn rate.
2. Snap forward to the next April 1 or October 1 ≥ projected date.
3. If the unit accumulates EOH past threshold while waiting → `P_forced` overage multiplier kicks in (linear from 1.0× at threshold to 2.5× at +1,500 EOH).
4. Hard stop at +1,500 EOH overage forces the inspection immediately regardless of season.

Each mode's maintenance schedule is pre-built once at run start using `EOH_RATE_ESTIMATE × MODE_EOH_MULT[mode]`. The pre-build is deterministic given inputs — the actual EOH path is stochastic, so the calendar is an *intention*, and the hard-stop / overage-penalty machinery handles realized deviation.

## 9. LTSA cost taxonomy

Owner cashflow attributable to LTSA decomposes into seven streams. Knowing which is which is essential for interpreting outputs.

| Stream | Per-day or event | Owner-paid? | Driven by |
| :--- | :--- | :--- | :--- |
| `ltsa_fixed` | Daily accrual of fixed monthly fee | Yes (full) | Calendar — accrues even during outages |
| `ltsa_eoh_reserve` | Daily, proportional to EOH accumulated | Yes (full) — but builds OEM coverage | Fired hours + start-type EOH multipliers |
| `ltsa_major_cov` | Event (CI / MI / forced GT in-scope) | No — OEM covered | Inspection events + GT-covered forced outages |
| `ltsa_major_uncov` | Event (CI / MI / forced HRSG / forced BOP / HR penalty) | Yes (full) | Owner share of inspections + excluded-scope forced outages + cycle-end HR penalty |
| `ltsa_overage` | Daily increment (cumulative YTD vs. pro-rated baseline) | Yes (full) | Excess starts beyond contracted baseline |
| `ltsa_avail_penalty` | Annual (posted on last day of year) | Yes (full) | Availability < 95% |

The `oem_covered` line is informational — it doesn't hit owner cashflow, but tracking it matters because the EOH reserve is built specifically to fund those events, and the contract trues up at each inspection.

## 10. Inputs and outputs

### Inputs

The dispatch model consumes a single file `gt_market_inputs.npz` produced by [generate_dummy_data.py](docs/extra/gas-turbine-digital-twin/generate_dummy_data.py), with shape conventions:

| Field | Shape | Notes |
| :--- | :--- | :--- |
| `temperature_f` | `(N_SIMS, N_DAYS, 24)` | Hourly °F. Sinusoidal seasonal + AR(1) daily + hourly noise. |
| `air_quality_idx` | `(N_SIMS, N_DAYS, 24)` | Hourly AQI 0–200. Scales compressor fouling rate daily. |
| `power_price_mwh` | `(N_SIMS, N_DAYS, 24)` | Hourly $/MWh, NYISO Zone F shape, with Poisson price spikes. |
| `gas_price_mmbtu` | `(N_SIMS, N_DAYS)` | Daily $/MMBtu, TGP Zone 6 with winter spike events. |

`N_SIMS = 1000` is generated; `dispatch_model.py` uses 50 paths × 10 years (one year of inputs per path-year).

### Outputs

Two `.npz` files in `outputs/`:

- `gt_outputs_10yr.npz` — Mode A only, all daily arrays shaped `(N_LONG_PATHS, TOTAL_DAYS)`: 36 fields covering spark spreads (clean / actual / losses), revenue, fuel, hours (clean / actual / planned / forced by cause), state (eoh, hr%, fouling, creep, fatigue, tbc, hrsg, rotor), LTSA cost streams, and inspection event markers.
- `gt_mode_comparison.npz` — All three modes, three key metrics: `spark`, `hrs`, `ltsa` — each shaped `(3 modes, N_PATHS, TOTAL_DAYS)`.

The asymmetry (Mode A full vs. modes B/C summary) is a deliberate I/O trade-off; Mode A is the reference case for detailed analysis, the mode comparison is for aggregate trade-off curves.

## 11. How to run it

End-to-end pipeline:

```bash
# 1. Generate synthetic market + climate inputs (one-time)
python generate_dummy_data.py

# 2. Run the simulation (50 paths × 3 modes × 10 years)
python dispatch_model.py

# 3. Charts (input validation, output attribution)
python charts_inputs.py
python charts_outputs.py

# 4. Sensitivity tornado (10 paths, Mode A only, ~20s)
python sensitivity_analysis.py

# 5. Back-cast validation vs 2015-2024 actual NYISO/EIA data
python backcast_comparison.py
```

`src/main.py` is a stub from project bootstrapping — it does nothing useful. Ignore.

## 12. Backcast validation — how well does it match reality?

[backcast_comparison.py](docs/extra/gas-turbine-digital-twin/backcast_comparison.py) compares the synthetic input distributions to 2015–2024 actual NYISO Zone F + TGP Zone 6 + Albany temperature.

| Variable | Synthetic avg | Actual 2015–24 avg | Match |
| :--- | :--- | :--- | :--- |
| Power | $41.8/MWh | $43.3/MWh | Excellent (−4%) |
| Gas (delivered) | $4.14/MMBtu | $3.49/MMBtu | +19% — model calibrated to 2025 forwards, intentional |
| Spark spread | $10.0/MWh | $16.2/MWh | Lower; synthetic P10–P90 (−$11 to +$31) covers most years |
| Temperature | 53.0°F | 51.8°F | Excellent (−1.2°F) |

**The crisis tail.** 2021–22 (Winter Storm Uri + Russia/Ukraine) drove Zone F spark spread to $25–38/MWh — at or above the synthetic P90. The model **does not** include correlated commodity price shock scenarios of this severity. For tail risk on the upside (high gas favors efficient dispatch) and the downside (high dispatch at elevated prices accelerates EOH and pushes overage cost), a separate 2022-type stress scenario should be run with adjusted gas distribution parameters.

## 13. Sensitivity findings

From [sensitivity_analysis.py](docs/extra/gas-turbine-digital-twin/sensitivity_analysis.py) (one-at-a-time tornado, 17 assumptions, ±20% Amber/Green, ±50% Red, 10 paths Mode A):

1. **Dominant — `P_BG_AGE_MAX`** (the 1.0× → 1.5× linear background-outage age multiplier): ±50% → −$2.0M to +$1.6M/yr spark impact. This is marked Red in Appendix B because there's no primary reference for the curve. **It is the single biggest unverified driver in the model.**
2. **Tier 2 — `P_HRSG_BASE` and `P_BG_BASE`** (Amber, ±20%): direct effect on available dispatch hours, ~$0.4–1.0M/yr.
3. **Surprising — `DERATE_COEFF`** (Green, ±20%): ~$0.5–0.65M/yr, driven by summer dispatch losing capacity at peak prices.
4. **Near-zero on spark — LTSA inspection costs, fixed fees, start overages**: correct, because spark spread excludes LTSA. They show up on the LTSA-cost tornado instead.
5. **Near-zero — TBC and combustion parameters**: because the plant starts post-HGP with stress counters at zero, so TBC/combustion failure modes are unlikely to fire within the 10-year window in most paths. Sensitivity here will look different for a mid-life asset.

## 14. What this framework achieves *without* OEM proprietary data

A genuinely thoughtful piece of the design. The model deliberately avoids any dependency on:

- OEM material property databases or component S-N curves
- FEA stress models
- Coating composition or blade-specific life data
- Plant sensor streams (vibration, exhaust spread, combustion dynamics)

Instead it leans on **public references**:

- GE GER-3620K for EOH counting
- EPRI fleet experience reports (1026609, 1025357, 1012586) for failure distributions and Weibull parameters
- ASME N-47 for creep-fatigue interaction methodology
- Published Larson-Miller parameters for IN738 / GTD111
- NREL/TP-5500-55433 for HRSG/ST cycling cost decomposition
- NERC GADS ranges for forced outage durations

This is the right call for an investor-DD model: defensible, reproducible, no IP entanglement. The **future upgrade path** flagged in §5.1 of the framework doc is PINNs (physics-informed neural networks) once plant-specific historian data becomes available.

## 15. What is prototype, what is production-ready

A frank inventory. This is the part to read before any external commitment.

### 15.1 Solid

- **Engineering state machine** — coverage of stress mechanisms is comprehensive, the creep-fatigue interaction is genuinely correct, the inspection reset semantics are mechanism-specific (not blanket).
- **Endogenous forced outage from state** — beats static FOR.
- **Twin clean+degraded dispatch attribution** — gives clean spark vs. realized spark separation that's straightforward to chart and explain to an investor.
- **Calendar-snapped maintenance with hard-stop** — realistic operational constraint.
- **LTSA cost taxonomy** — captures the right structure (fixed / variable / event / penalty / covered-vs-uncovered).
- **Per-path TBC Weibull threshold** — gives genuine path heterogeneity.
- **Backcast machinery exists** — even if the synthetic distribution misses tails, the framework for validating against real history is in place.

### 15.2 Prototype / placeholder

- **All LTSA parameters marked `[ASSUME]`** ([LTSAContract.py:20-77](docs/extra/gas-turbine-digital-twin/LTSAContract.py#L20-L77)) — fixed fee, EOH rate, OEM coverage fractions, baselines, overage charges, guarantees, penalty factors. These need the actual Athens CSA in hand.
- **Market inputs are entirely synthetic** ([generate_dummy_data.py](docs/extra/gas-turbine-digital-twin/generate_dummy_data.py)) — not calibrated to a real forward curve. The framework expects external climate + forward energy sims to drop in.
- **Dispatch is heuristic spark-vs-hurdle, not optimization** — no rolling-window MIP, no day-ahead vs. real-time split, single hourly price series. Per the framework doc, this is "static prototype dispatch" — the dynamic re-optimization with full feedback is a planned next phase.
- **EOH rate estimate is a coarse heuristic** ([dispatch_model.py:133](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L133)) — fraction of hours with positive clean spark spread, times a rough start-mix assumption. Reasonable for calendar pre-building, but won't track stress accurately for paths that dispatch very differently from average.
- **Inspection cost-cycle HR penalty** is computed but only attributed via the planned-outage day ([dispatch_model.py:343-346](docs/extra/gas-turbine-digital-twin/dispatch_model.py#L343-L346)). True-up reconciliation between EOH reserve balance and actual covered cost (mentioned in framework §4.4.3) is not implemented.
- **No 1×1 dispatch mode** — the framework discusses single-GT operation at ~55% capacity, but the code only dispatches the full 2×1 block at `cap_eff(temp)`.
- **Damage interaction envelope is binary** ([EnggDTwin_model.py:168-171](docs/extra/gas-turbine-digital-twin/EnggDTwin_model.py#L168-L171)) — `D_c + D_f ≥ D_lim` halves both. The actual bilinear envelope in §3.2.1 of the framework doc is smoother than that.
- **`P_BG_AGE_MAX` (the 1.5× year-10 multiplier) is the single biggest unverified driver** per the sensitivity analysis. Treat any outputs that depend strongly on year 8–10 forced-outage cost as soft.

### 15.3 Genuinely missing

- **Joint NPV optimization across modes.** Modes A/B/C are heuristic policies, not solutions to a stated objective. A model that says "minimize 10-year NPV(LTSA cost + opportunity cost of curtailed dispatch) subject to availability ≥ X" doesn't exist yet.
- **Capacity market revenue** (ICAP / UCAP, NYISO Zone F installed capacity payments). Currently only energy revenue is modeled — for a Zone F asset this is a meaningful omission.
- **Ancillary services revenue** (regulation, reserves, ramping product).
- **Carbon / RGGI compliance cost** — Zone F sits inside RGGI; allowance cost should be in delivered fuel cost.
- **Insurance recoveries** on FOD and over-temperature damage — flagged as covered by property damage insurance in §4.4.6 but not modeled (currently classified as owner-uncovered).
- **Financing / tax layer → EBITDA → DSCR.** The framework names these but they sit downstream of this repo.
- **No 1×1 (single-GT) operating mode.** Real plant has it; model doesn't.
- **No dispatch feedback from yesterday's degradation to today's start-up decision beyond the EOH-proximity penalty** — i.e. the dispatch heuristic doesn't anticipate that today's cold start will move the next CI from October to April; the calendar is fixed at run-start. A proper rolling-window optimizer would re-plan each day.
- **No correlated tail-risk scenarios** (Uri-type gas spike + cold load + asset stress). The model's stochastic distribution misses 2021–22-class events.

## 16. Where this sits in the broader InfraSure framework

Per `InfraSure_ModelingFramework_V2.md` §2, the full pipeline is five stages:

```
Climate sim  +  Forward energy market sim
        |                |
        v                v
        Dispatch model (this repo's heuristic version)
                |
                v
        Engineering twin (this repo's state machine)
                |
                v
        Maintenance & failure (LTSA contract layer)
                |
                v
        Financial layer (EBITDA, DSCR, P10/P50/P90)
```

This repo implements **stages 3, 4, and part of 5**. Climate and energy-market simulations are pre-built modules (currently mocked by `generate_dummy_data.py`). The financial-metrics aggregation (EBITDA / DSCR / insurance adequacy) is downstream and not in this repo.

## 17. Open questions for the next iteration

A starter list, in rough priority:

1. **Get the real Athens CSA** and replace the `[ASSUME]` parameters. The sensitivity says the fixed monthly fee and inspection costs dominate LTSA totals.
2. **Connect to real forward curves** (NYISO Zone F LMP, TGP Zone 6 basis, NOAA Albany temperature) so the synthetic distribution can be calibrated and stress-shocked to historical extremes.
3. **Build the joint NPV optimizer.** A two-stage formulation: an outer policy (when to do maintenance, when to self-curtail) and an inner hourly dispatch (LP / MIP). Modes A/B/C become bounds on a continuous policy.
4. **Add capacity market** — for an asset of this size in Zone F, ICAP revenue is a meaningful EBITDA contributor and is sensitive to availability (which the twin already tracks).
5. **Address `P_BG_AGE_MAX`** with a Monte Carlo over [1.0×, 2.0×] and seek fleet aging data; this single Red-tagged parameter has outsized impact on year 8–10 outputs.
6. **Tail-event scenarios.** Build a 2022-type gas-shock scenario and a multi-month cold-snap scenario and run them as named cases alongside the stochastic distribution.
7. **1×1 dispatch mode** in `hourly_dispatch` — adds a real degree of operational flexibility at low prices.
8. **EOH reserve true-up.** Implement the cumulative reserve balance ↔ inspection-cost reconciliation per §4.4.3.

## 18. Glossary

| Term | Meaning |
| :--- | :--- |
| **CCGT** | Combined cycle gas turbine (2 GT + 1 ST + 2 HRSG here) |
| **CI** | Combustion inspection — combustion liners, transition pieces, nozzles. ~$3.75M, 12-day outage |
| **MI** | Major inspection — full CI scope + turbine blades/nozzles/shrouds + rotor. ~$30M, 52-day outage |
| **HGP** | Hot gas path (inspection / wear region) — turbine stage 1–2 blades, nozzles, shrouds |
| **EOH** | Equivalent operating hours — contractual life counter combining fired hours + start penalties + trips |
| **CSA / LTSA** | Contractual / Long-Term Service Agreement — the OEM service contract |
| **OEM** | Original equipment manufacturer (GE here) |
| **HRSG** | Heat recovery steam generator (the steam side; HP drum is the fatigue-critical part) |
| **TBC** | Thermal barrier coating on turbine blades / vanes |
| **BOP** | Balance of plant (cooling, controls, electrical, etc.) |
| **DLN** | Dry low-NOx combustion |
| **DSCR** | Debt service coverage ratio |
| **LMP** | Locational marginal price |
| **NYISO Zone F** | Capital region zone (Albany / Hudson Valley) |
| **TGP Zone 6** | Tennessee Gas Pipeline Zone 6 (Northeast delivery) |
| **GER-3620** | GE's published maintenance interval guide for heavy-duty gas turbines |
| **Spark spread** | Power price − (HR × gas price) − VOM, in $/MWh |
| **Clean spark** | Same as spark spread but using the ISO baseline HR and capacity (no degradation) |
| **Forced outage** | Unplanned outage; here, generated endogenously from stress state |
| **Forced outage rate (FOR)** | Conventional static metric for forced outages — replaced here by endogenous `P_forced` |

---

*This document is a reader's guide to the implementation in [docs/extra/gas-turbine-digital-twin/](docs/extra/gas-turbine-digital-twin/). It is not a substitute for [InfraSure_ModelingFramework_V2.md](docs/extra/gas-turbine-digital-twin/InfraSure_ModelingFramework_V2.md), which contains the full methodology, references, and Athens pilot results. Where the framework doc explains the *why*, this guide explains the *what's in the code*.*
