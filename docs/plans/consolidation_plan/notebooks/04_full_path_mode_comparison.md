# Notebook 4 — Full Path + Mode A/B/C + LTSA Cost Streams

> **Status**: Plan drafted 2026-05-14. Awaiting user review before execution.
> **Notebook path (when built)**: `notebooks/04_full_path_mode_comparison.ipynb`
> **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) — execution Phase J
> **Sibling plans**: [`README.md`](./README.md); [`01_data_spine_load_validate.md`](./01_data_spine_load_validate.md); [`02_one_day_dispatch.md`](./02_one_day_dispatch.md); [`03_daily_loop_feedback.md`](./03_daily_loop_feedback.md)
> **Prerequisites**: Phase I complete (N3 ran end-to-end). Phases A–F (data spine). ADR-002 corrections applied to N3.

---

## §1. Purpose

**The v1 capstone.** Run the full historical horizon (2017-01-01 → 2025-12-31, 9 years) under three dispatch policies (Mode A / B / C), produce all seven LTSA cost streams, trigger inspection events, sample forced-outage events, and produce a `model_card.md` summarizing what the model says about Lockport.

The headline output is the **mode-comparison trade-off**: how much spark Mode A captures vs how much LTSA cost Mode C saves. Per the prototype's understanding doc §5: Athens shows Mode C sacrifices ~$1.3M/yr spark to save ~$80M LTSA over 10 yr → net +$67M. For Lockport (different scale, much lower CF, cogen), the numbers will differ but the direction should hold.

Goals, in priority order:

1. **Mode A/B/C policy actually fires.** The prototype's mode-difference machinery (wear penalty on start cost, scaled by EOH proximity to inspection threshold) is the dispatch logic that produces mode divergence. N4 implements this correctly per the prototype.
2. **Seven LTSA cost streams accrue.** Per the framework's cost taxonomy: fixed fee, EOH reserve, OEM-covered major, owner-uncovered major, start overage, availability penalty, HR penalty. All wired in even though parameters are placeholder per ADR-001 / N3.
3. **Inspection events trigger.** Calendar shoulder-snap + hard-stop overage logic. CI / MI events with outage duration + cost classification + state resets. Per prototype convention.
4. **Forced outage events sampled.** Daily P_forced from state → uniform random sample → event firing → cause classification (GT/HRSG/BG) → outage duration sampled lognormal → cost classification per LTSA coverage.
5. **First model_card.md produced.** Per `docs/assumptions/README.md` and consolidation plan §10. Required for shippable v1 outputs. Includes data vintages, assumption-status distribution, LOW-confidence flags, placeholder list, mode-comparison headlines.
6. **Validation against MOR observations.** Compare modeled 2024 generation to MOR-observed 192,494 MWh; modeled mode distribution to MOR's 65/26/9 split; modeled cold-start frequency to MOR's ~7/year.
7. **Plots: extend N3 templates per-mode + add LTSA cost stream breakdown + mode-comparison summary.**

**Optional writes to `data/outputs/lockport/runs/notebook4_<run_id>/`** for downstream review:
- `model_card.md` (required)
- `state_trajectory_mode_{a,b,c}.parquet`
- `daily_summary_mode_{a,b,c}.parquet`
- `ltsa_streams_mode_{a,b,c}.parquet`
- `inspection_events.parquet`
- `forced_outage_events.parquet`

---

## §2. Inputs

| File | Purpose | New in N4? |
|---|---|---|
| All from N3 | (inherits state-evolution machinery) | inherited |
| `data/assets/lockport/ltsa_terms.yaml` | **All 7 LTSA stream parameters** (placeholders per ADR-001) | **major new use** |
| `data/paths/lockport/lmp_da_hourly.parquet` | 9 years of hourly LMP (2017-2025) | extended use |

No new file additions. N4 fully exercises the existing data spine.

---

## §3. Cell-by-cell sketch

### §3.A — Setup

Same imports as N3 (numpy, pandas, yaml, matplotlib, dataclasses). Same `v()` / `m()` helpers. Same TZ-conversion for weather. Same constants block (extends N3 with Mode A/B/C + LTSA stream parameters).

### §3.B — Window definition

**9-year historical replay**: 2017-01-01 → 2025-12-31. Boundaries chosen because:
- LMP DA hourly starts 2017-01-01 (cleanest)
- LMP through 2026-04-29 → truncate to 2025-12-31 for clean calendar year boundaries
- Weather through 2025-12-31 (matches exactly)
- Gas Henry Hub covers all 9 years

3,287 days × 3 modes = 9,861 day-mode executions. Should run in <60 seconds.

**This is historical replay, NOT synthetic scenario**. Documented: v1 uses real history; Phase L Monte Carlo will use Step 1's scenario engine (currently in model-gpr).

### §3.C — Constants (extends N3)

#### Mode A/B/C policy parameters

Per prototype's understanding doc §5:

```python
# EOH rate multiplier — affects pre-built maintenance schedule
MODE_EOH_RATE_MULT = {"A": 1.00, "B": 0.875, "C": 0.65}

# Wear penalty on start cost — scales by EOH proximity to next inspection threshold
# Mode A: always 1.0× (no self-curtailment)
# Mode B: 1.0× when headroom > 4,000; scales linearly to 2.5× at headroom = 1,000
# Mode C: 1.0× when headroom > 4,000; scales linearly to 4.0× at headroom = 0
def wear_penalty_mult(mode: str, eoh_headroom: float) -> float:
    if mode == "A":
        return 1.0
    if eoh_headroom > 4_000:
        return 1.0
    # Linear scaling
    if mode == "B":
        # Headroom 4,000 → 1.0×; headroom 1,000 → 2.5×
        if eoh_headroom <= 1_000:
            return 2.5
        return 1.0 + (4_000 - eoh_headroom) / (4_000 - 1_000) * (2.5 - 1.0)
    if mode == "C":
        # Headroom 4,000 → 1.0×; headroom 0 → 4.0×
        if eoh_headroom <= 0:
            return 4.0
        return 1.0 + (4_000 - eoh_headroom) / 4_000 * (4.0 - 1.0)
    return 1.0

# Wear fraction of start cost (per prototype convention)
GT_WEAR_FRACTION_OF_START = 0.42  # 42% — the rest is HRSG/ST share, not subject to mode penalty
```

#### Start cost components (per Kumar 2012 + cold-start gas observation)

```python
# Start cost = C&M + fuel cost + wear penalty
# C&M from Kumar 2012 Table 1-1 "Gas-CC" $/MW of capacity:
START_CM_USD_PER_MW = {"cold": 79.0, "warm": 55.0, "hot": 35.0}  # 2011 USD
# Fuel cost from MOR-observed warming gas (real_observed Lockport, per ADR-002 Correction 1)
# 2,537 MMBtu/cold start × delivered_gas — applied DAILY when cold start fires (already in N3)
# For warm/hot starts, fuel is per Kumar 2012 Tbl 1-3 MMBtu/MW (smaller)
START_FUEL_MMBTU_PER_MW = {"cold": 0.24, "warm": 0.20, "hot": 0.19}
```

#### Outage event parameters

```python
# Forced outage duration sampled lognormal — medians per prototype convention
OUTAGE_DURATION_DAYS = {"gt": 8, "hrsg": 12, "bg": 5}
OUTAGE_DURATION_SIGMA = 0.5  # lognormal sigma

# Cost classification per ltsa_terms.yaml.forced_outage_coverage
OUTAGE_COST_USD = {"gt": 0, "hrsg": 500_000, "bg": 750_000}  # owner-uncovered amounts; gt = OEM covered
# (placeholder per ADR-001)
```

#### LTSA cost stream parameters

Read from `ltsa_terms.yaml`. All placeholder Athens defaults until data room extraction:

```python
# 1. Fixed monthly fee
LTSA_FIXED_MONTHLY_USD = float(v(ltsa_terms["fixed_fee"]["monthly_usd"]))  # $850K
LTSA_FIXED_DAILY = LTSA_FIXED_MONTHLY_USD * 12 / 365  # ~$27,945/day
LTSA_ESCALATION_PCT_PER_YEAR = float(v(ltsa_terms["fixed_fee"]["escalation_pct_per_year"]))  # 3.5%

# 2. EOH reserve
LTSA_EOH_RESERVE_USD_PER_EOH = float(v(ltsa_terms["eoh_reserve"]["rate_usd_per_eoh"]))  # $175

# 3 & 4. Inspection costs
CI_COST_TOTAL = float(v(ltsa_terms["inspection_ci"]["total_cost_usd"]))  # $3.75M
CI_OEM_COVERED_FRAC = float(v(ltsa_terms["inspection_ci"]["oem_covered_fraction"]))  # 0.75
CI_OUTAGE_DAYS = float(v(ltsa_terms["inspection_ci"]["outage_duration_days"]))  # 12
MI_COST_TOTAL = float(v(ltsa_terms["inspection_mi"]["total_cost_usd"]))  # $30M
MI_OEM_COVERED_FRAC = float(v(ltsa_terms["inspection_mi"]["oem_covered_fraction"]))  # 0.65
MI_OUTAGE_DAYS = float(v(ltsa_terms["inspection_mi"]["outage_duration_days"]))  # 52

# 5. Start overage
OVERAGE_BASELINE = {
    "hot":  float(v(ltsa_terms["start_overage"]["annual_baseline_starts"]["hot"])),   # 150
    "warm": float(v(ltsa_terms["start_overage"]["annual_baseline_starts"]["warm"])),  # 35
    "cold": float(v(ltsa_terms["start_overage"]["annual_baseline_starts"]["cold"])),  # 5
}
OVERAGE_CHARGE = {
    "hot":  float(v(ltsa_terms["start_overage"]["overage_charge_usd_per_excess_start"]["hot"])),
    "warm": float(v(ltsa_terms["start_overage"]["overage_charge_usd_per_excess_start"]["warm"])),
    "cold": float(v(ltsa_terms["start_overage"]["overage_charge_usd_per_excess_start"]["cold"])),
}

# 6. Availability penalty
AVAIL_GUARANTEE_PCT = float(v(ltsa_terms["availability_penalty"]["guarantee_pct"]))  # 95%

# 7. HR penalty
HR_PENALTY_TOLERANCE_PCT = float(v(ltsa_terms["hr_penalty"]["tolerance_pct_above_guarantee"]))  # 2%
```

### §3.D — Maintenance schedule pre-builder

Per prototype convention: at sim start, project the calendar based on the mode's EOH rate multiplier:

```python
def build_maint_schedule(mode: str, sim_start: pd.Timestamp, initial_eoh: float,
                        eoh_thresholds: dict, eoh_rate_estimate: float) -> list[dict]:
    """Pre-build inspection calendar.
    
    For each upcoming threshold (CI = next 24,000-mark from start_eoh, MI = next 48,000-mark):
    1. Project days-to-threshold from current EOH rate × mode multiplier
    2. Snap forward to next April 1 or October 1 ≥ projected date
    3. Return list of (event_type, scheduled_date, threshold)
    """
    schedule = []
    eoh_rate = eoh_rate_estimate * MODE_EOH_RATE_MULT[mode]  # EOH/day
    cur_eoh = initial_eoh
    cur_date = sim_start

    # Schedule the next 5 events (CI, MI alternating; 5 = enough for 10 yr)
    next_ci = ((int(cur_eoh) // int(eoh_thresholds["ci_interval"])) + 1) * eoh_thresholds["ci_interval"]
    next_mi = ((int(cur_eoh) // int(eoh_thresholds["mi_interval"])) + 1) * eoh_thresholds["mi_interval"]

    for _ in range(5):
        # Whichever comes first
        ci_eoh = next_ci
        mi_eoh = next_mi
        if ci_eoh < mi_eoh:
            event_type = "CI"
            target_eoh = ci_eoh
            next_ci += eoh_thresholds["ci_interval"]
        else:
            event_type = "MI"
            target_eoh = mi_eoh
            next_mi += eoh_thresholds["mi_interval"]

        days_to_threshold = (target_eoh - cur_eoh) / max(eoh_rate, 0.1)
        projected_date = cur_date + pd.Timedelta(days=days_to_threshold)
        # Snap to next April 1 or October 1
        snapped = snap_to_shoulder(projected_date)
        schedule.append({"type": event_type, "scheduled_date": snapped, "threshold_eoh": target_eoh})

        cur_eoh = target_eoh
        cur_date = snapped

    return schedule


def snap_to_shoulder(date: pd.Timestamp) -> pd.Timestamp:
    """Snap forward to next April 1 or October 1."""
    year = date.year
    apr = pd.Timestamp(year, 4, 1)
    oct = pd.Timestamp(year, 10, 1)
    next_apr = apr if date <= apr else pd.Timestamp(year + 1, 4, 1)
    next_oct = oct if date <= oct else pd.Timestamp(year + 1, 10, 1)
    return min(next_apr, next_oct)
```

**EOH rate estimate**: at sim start, estimate EOH burn rate from a rough heuristic — fraction of hours where spark > 0, times start mix. Per prototype's `estimate_eoh_rate`. Pre-built once.

### §3.E — Daily loop (extended from N3)

```python
def run_day_n4(state, day_inputs, mode, schedule, ltsa_state, year_frac, rng):
    """Extended N3 day-loop for a specific mode (A/B/C).
    
    New in N4:
    - Mode-aware wear penalty applied to start cost in dispatch decision
    - Inspection event triggering (calendar match or hard stop)
    - Forced outage event sampling
    - LTSA cost stream accrual (7 streams)
    - State resets on inspection
    
    Returns (new_state, day_record, new_ltsa_state).
    """
    # 1. Check continuing outage (from forced or planned)
    if state.outage_days_remaining > 0:
        # Skip dispatch; accrue fixed fee + apply daily decrement
        ...
        return ...

    # 2. Compute today's effective params (as N3)
    
    # 3. EOH headroom to next inspection
    next_event = next(s for s in schedule if not s["completed"])
    eoh_headroom = next_event["threshold_eoh"] - state.eoh
    
    # 4. Wear penalty for this mode
    wear_mult = wear_penalty_mult(mode, eoh_headroom)
    
    # 5. Twin dispatch (clean + degraded), with wear penalty applied
    # Wear penalty = GT_WEAR_FRACTION × Kumar start cost × wear_mult
    # Amortize over expected run-streak (proxy: 6 hours min)
    # Add to start-cost threshold for dispatch decision
    dr_clean = dispatch_day_with_mode_penalty(...)
    dr_degraded = dispatch_day_with_mode_penalty(...)
    
    # 6. Apply cold-start warming gas (inherited from N3)
    
    # 7. Check inspection trigger
    today = day_inputs["date"]
    if today >= next_event["scheduled_date"] or eoh_headroom <= -1_500:
        # Trigger inspection event
        trigger_inspection(state, next_event, ltsa_state)
        # Outage starts
        state.outage_type = next_event["type"]  # CI or MI
        state.outage_days_remaining = CI_OUTAGE_DAYS if next_event["type"] == "CI" else MI_OUTAGE_DAYS
        # Apply state resets per prototype convention
        apply_inspection_reset(state, next_event["type"], rng)
        next_event["completed"] = True
    
    # 8. Forced outage event sampling
    pf = p_forced_components(state, year_frac=year_frac)
    if rng.random() < pf["p_combined"]:
        # Sample cause
        cause = sample_outage_cause(rng, pf)
        # Sample duration
        duration = max(1, int(rng.lognormal(np.log(OUTAGE_DURATION_DAYS[cause]), OUTAGE_DURATION_SIGMA)))
        # Apply cost
        ltsa_state["major_uncov_outage_usd"] += OUTAGE_COST_USD[cause]
        state.outage_type = f"forced_{cause}"
        state.outage_days_remaining = duration
        # Don't execute dispatch today
        return ...
    
    # 9. Execute dispatch (commit operational flags)
    
    # 10. Update stress accumulators (N3 logic)
    
    # 11. Accrue LTSA streams
    today_year = today.year - sim_start.year
    escalation = (1 + LTSA_ESCALATION_PCT_PER_YEAR / 100) ** today_year
    
    ltsa_state["fixed_daily"] = LTSA_FIXED_DAILY * escalation
    ltsa_state["eoh_reserve_daily"] = (delta_eoh) * LTSA_EOH_RESERVE_USD_PER_EOH * escalation
    
    # Start overage — daily increment based on YTD vs pro-rated baseline
    update_overage_accrual(ltsa_state, today, starts_today)
    
    # 12. Year-end: availability + HR penalties
    if is_year_end(today):
        annual_avail = compute_annual_availability(state, ltsa_state, today.year)
        if annual_avail < AVAIL_GUARANTEE_PCT / 100:
            shortfall = (AVAIL_GUARANTEE_PCT / 100 - annual_avail)
            penalty = (LTSA_FIXED_MONTHLY_USD / 12) * shortfall * 10
            ltsa_state["avail_penalty_annual"] += penalty
    
    return ...
```

### §3.F — Run all 3 modes

```python
results = {}
for mode in ["A", "B", "C"]:
    state = init_state(seed=42)
    ltsa_state = init_ltsa_state()
    schedule = build_maint_schedule(mode, sim_start, state.eoh, ...)
    rng = np.random.default_rng(seed=42)
    
    daily_records = []
    for day_idx, day in enumerate(simulation_dates):
        day_inputs = prepare_day_inputs(day)
        new_state, day_record, ltsa_state = run_day_n4(state, day_inputs, mode, schedule, ltsa_state, day_idx/365, rng)
        daily_records.append(day_record)
        state = new_state
    
    results[mode] = {
        "daily": pd.DataFrame(daily_records),
        "ltsa_state_final": ltsa_state,
        "schedule": schedule,
    }
```

### §3.G — Plots

#### Plot 1: State trajectory by mode (3-panel × 3-mode overlay)

Each panel of N3's state plot, with 3 lines (A/B/C). Show how Mode C self-curtails to delay inspection, reducing EOH burn rate vs Mode A.

#### Plot 2: P_forced trajectory by mode

3 lines for combined P_forced over 9 years. Mode C should have lower probability (slower stress accumulation).

#### Plot 3: Daily MWh + cumulative spark margin by mode

3 cumulative lines. Mode A captures most spark; Mode C least. The "spark sacrifice" of Mode C vs Mode A is visible.

#### Plot 4: LTSA cost stream stacked area by mode

7 streams as stacked area, one chart per mode. Shows where the LTSA money goes:
- Fixed fee (constant daily)
- EOH reserve (grows with dispatch)
- Major uncov events (spikes at inspections + forced outages)
- Overage charges (grows late in year when YTD starts exceed baseline)
- Availability + HR penalties (annual)

#### Plot 5: Mode comparison summary chart

Bar chart, 5 categories × 3 modes:
- Total spark margin (degraded, $M over 9 yr)
- Total LTSA cost — owner uncovered ($M over 9 yr)
- Total fired hours (k)
- Total starts
- Total inspection events

#### Plot 6: Inspection event timeline

Gantt-style chart: when each mode triggered CI vs MI events. Mode A earliest (most aggressive EOH burn); Mode C latest.

### §3.H — Mode comparison summary table

For each mode, compute:
- Total spark (degraded) over 9 years
- Total LTSA cost owner-uncovered (all streams summed)
- **Net P&L** = spark - LTSA - VOM - non-fuel costs
- Total fired hours, starts
- Inspection events count + timing
- Forced outage events count + duration + cost

Headline: **Mode A − Mode C** net P&L delta. If Mode C has higher net P&L, that confirms the prototype's trade-off finding for Lockport.

### §3.I — Validation against MOR observations

Where our model output should align with MOR-derived facts:

| Metric | MOR-observed (real_observed) | Modeled (Mode A) | Pass / Note |
|---|---|---|---|
| 2024 annual generation | 192,494 MWh | computed | within ±20%? |
| Mode distribution (3×CC / 2×CC / 1×CC) | 64.9% / 26.1% / 8.9% (of active CC days) | computed share of fired hours | direction match? |
| Cold-start frequency | ~7/year (35 over 5 yr) | computed | order of magnitude? |
| Plant capacity factor | ~5% (eGRID 2023) | computed annual avg | within ±50% (low-CF asset; high variance) |

This is the v1 backtest. Document divergences but don't fail the notebook on them — these are honest validation findings to capture in `model_card.md`.

### §3.J — Generate model_card.md

Required per `docs/assumptions/README.md` for any shippable output. Structure:

```markdown
# Model Card — Lockport v1 Notebook 4 Run <timestamp>

## Run metadata
- Date: 2026-05-14
- Window: 2017-01-01 → 2025-12-31 (9 years historical replay)
- Random seed: 42
- Modes simulated: A, B, C

## Data vintages
[refresh dates of each input artifact from provenance.md]

## Assumption status distribution
- real_observed: X (X%)
- real_reported: X (X%)
- real_computed: X (X%)
- assumed_techclass: X (X%)
- assumed_industry: X (X%)
- placeholder: X (X%) — see placeholder_caveats.md

## LOW-confidence values flagged
[Bucket B from ADR-002 — table of values + impact]

## Placeholders pending
[Bucket C from ADR-002 — table with validation_path]

## Mode comparison headline
- Mode A: spark $X.XM, LTSA $X.XM, Net $X.XM, X inspections
- Mode B: ...
- Mode C: ...
- A → C delta: spark -$X.XM, LTSA -$X.XM, net +$X.XM

## Backtest validation
[§I outcomes]

## Caveats and known limitations
- ADR-001: gas hub = Henry Hub (no Algonquin basis modeled)
- ADR-002 Bucket B: state-evolution constants are Athens-calibrated
- Cogen synthetic must-run flag (temp-based proxy)
- Dual-fuel switching never fires in v1
- LTSA values all placeholder per ADR-001
```

### §3.K — Sanity checks

Beyond N3's checks:
- [ ] All 3 modes produce numerically valid outputs (no NaN/Inf)
- [ ] Mode comparison shows expected direction: Mode A spark ≥ Mode B ≥ Mode C
- [ ] Mode comparison shows expected direction: Mode C inspections later than Mode A
- [ ] LTSA fixed_fee accrual = $850K × 12 / 365 × 9 × escalation_avg ≈ $93M-100M over 9 yr
- [ ] No negative LTSA stream values
- [ ] Inspection events trigger when EOH headroom ≤ 0
- [ ] Forced outage events fire at rate consistent with P_forced (within 50% factor)
- [ ] State resets correctly at CI / MI (creep, fatigue, fouling, hr_recov)

### §3.L — Stage 1 findings

What we learned. Per N4 being v1 capstone, this section is especially important — feeds the model_card and any future ADR-003 (Phase L Monte Carlo prep).

Expected findings to surface:
- Mode comparison: A captures the most spark; C saves on cycling cost. Net P&L direction.
- LTSA stream sizes: what fraction is fixed vs event-based?
- How often inspections actually fire in 9 years (~3-5 CIs + 1-2 MIs for Athens; for Lockport's low CF, much less)
- Forced outage event frequency
- Validation vs MOR: where does model diverge from observed?
- The ADR-002 Bucket B sensitivity — which constants matter most for the 9-year horizon?

### §3.M — Decision log

Conventions chosen for N4. Inherited by Phase L (Monte Carlo) and Phase K (graduate to src/).

---

## §4. Conventions chosen for this notebook

| Decision | Choice | Rationale |
|---|---|---|
| Time horizon | 9-yr historical replay 2017-01-01 → 2025-12-31 | Real LMP coverage; clean year boundaries; longer than 10-yr synthetic gets us a real backtest |
| Number of modes | 3 (A, B, C) | Per prototype convention; baseline trade-off chart |
| Mode policy mechanics | Wear-penalty multiplier × GT_WEAR_FRACTION × Kumar start cost; amortized over min-run-time | Per prototype §5; the dispatch-time machinery that produces mode divergence |
| Maintenance schedule | Pre-built per mode at sim start; calendar shoulder-snap (April / October); hard-stop +1500 EOH | Per prototype convention |
| Inspection state reset | CI: dc/df halve, fouling 70% wash, hr_recov 30%; MI: dc/df zero, fouling 70% wash, hr_recov 75%, tbc_time zero, tbc_thresh resampled | Per prototype §6 |
| Forced outage event sampling | Daily sample against P_forced; cause weighted by component prob; lognormal duration | Per prototype §7 |
| Outage cost classification | GT mechanical: OEM-covered; HRSG/BG: owner-uncovered with placeholder costs | Per `ltsa_terms.yaml.forced_outage_coverage` (all placeholder per ADR-001) |
| LTSA stream parameters | Read from `ltsa_terms.yaml`; all placeholder Athens defaults | Per ADR-001 + `placeholder_caveats.md` §1 |
| RNG seed | 42 (fixed for reproducibility) | Single-path doesn't sample path uncertainty (that's Phase L Monte Carlo) |
| Cold-start warming gas | Inherited from N3 (ADR-002 Correction 1) | `real_observed` MOR-based Lockport correction |
| RGGI cost | Inherited from N3: $17/ton × 117 lb CO2/MMBtu | EPA AP-42 fuel-side |
| Cogen VOM markup | Inherited from N3: ×1.35 | `assumed_industry` mid-range |
| Cogen must-run | Inherited from N3: temp ≤ P20-of-window | `assumed_industry` proxy until MOR DHTS extraction |
| Plots | 6 in N4: state by mode, P_forced by mode, cumulative margin, LTSA streams, mode-comparison bars, inspection timeline | First with per-mode overlays |
| model_card | Generate `model_card.md` per `docs/assumptions/README.md` | Required for shippable output |
| Output bundle | Write to `data/outputs/lockport/runs/notebook4_<timestamp>/` | Gitignored per consolidation plan §4.2 |
| Backtest validation | Compare to MOR-observed metrics (2024 generation, mode distribution, cold-start frequency) | Honest report; not a fail-gate |

---

## §5. Validation checks (acceptance criteria)

Notebook is "done" when:

- [ ] §3.B 9-year window selected with full 78,888-hour LMP coverage
- [ ] §3.C all constants loaded; mode policy curves implementable
- [ ] §3.D maintenance schedule pre-built for each of 3 modes
- [ ] §3.E day-loop runs without errors for all modes
- [ ] §3.F all 3 modes complete 9-year simulation
- [ ] §3.G all 6 plots produced
- [ ] §3.H mode comparison summary table shows directional trade-off (Mode A ≥ Mode B ≥ Mode C spark; reverse for self-curtailment)
- [ ] §3.I MOR validation table populated (with divergences documented honestly)
- [ ] §3.J `model_card.md` written to outputs/
- [ ] All §3.K sanity checks pass
- [ ] §3.L findings cell filled in
- [ ] §3.M decision log captured
- [ ] Output bundle in `data/outputs/lockport/runs/notebook4_<ts>/` complete

**Specific numerical expectations**:

- Each mode's 9-year spark margin should be in (-$50M, +$200M) range — Lockport is low-CF
- Each mode's LTSA owner-uncovered should be in ($50M, $300M) — fixed fee dominates over 9 yr
- Mode A inspections count: ~3-5 CIs + 1-2 MIs (depends on EOH burn rate)
- Mode C inspections count: should be ≤ Mode A
- Forced outage events: 5-20 per mode over 9 years (depends on stress accumulation)

---

## §6. What this notebook surfaces

Inputs to Phase L Monte Carlo + future v2 work:

| Question | How N4 answers it |
|---|---|
| What's the Mode A vs C trade-off magnitude for Lockport? | §3.H summary table |
| Are Bucket B constants from ADR-002 sensitive at the 9-year horizon? | §3.L findings: which streams move most when the model runs |
| Does Mode C actually save LTSA cost as the prototype claims? | §3.G plot 4 + §3.H comparison |
| Does the model validate against MOR-observed reality? | §3.I backtest |
| Where do the cogen / cold-start corrections matter most? | §3.L findings: cold-start frequency in winter months |

---

## §7. What this notebook does NOT cover

- **Multi-path Monte Carlo.** Phase L. N4 is single-path × 3 modes.
- **Parameter sweeps on Bucket B constants.** Phase L should sweep `P_BG_AGE_MAX`, fouling rate, fatigue per start, etc. per ADR-002 §"Consequences".
- **Real LTSA values.** Still placeholder per ADR-001 + `placeholder_caveats.md`.
- **Capacity market revenue.** Out of v1 per consolidation plan §5 D4.
- **Dual-fuel switching.** Per ADR-001, never fires in v1.
- **Algonquin basis modeling.** Per ADR-001, deferred to v2.
- **NYISO RGGI auction-day variation.** RGGI price is fixed at $17/ton; v2 could vary by date.
- **Per-generator state granularity.** v2 architecture concern.
- **DHTS daily MOR extraction.** Still synthetic proxy.
- **Real optimization (vs heuristic).** Per understanding doc §5.1, "true optimization is the planned next phase."

---

## §8. How this informs Phase L (Monte Carlo)

Phase L extends N4 by:

1. **Replacing fixed-seed RNG with proper sampling**: N4 uses seed=42 for reproducibility. Phase L runs N=50+ paths, each with its own seed for forced-outage sampling and TBC threshold.
2. **Synthetic scenario paths instead of historical replay**: N4 plays history forward. Phase L draws from Step 1's scenario engine (analog-block sampling + forward anchoring).
3. **Sweeping Bucket B constants**: Per ADR-002, the LOW-confidence `assumed_industry` constants should be Phase L sweep parameters, not fixed.
4. **P10/P50/P90 outputs**: across paths × modes. The eventual investor deliverable.
5. **Tail-event scenarios**: 2022-Uri-class gas shock added as named cases (per understanding doc §17 open items).

---

## §9. Open questions to resolve during execution

| Question | How it gets answered |
|---|---|
| Does the mode-comparison direction hold for Lockport's low-CF profile? | §3.H — first answer; if Mode A ≈ Mode C, the prototype's trade-off doesn't survive Lockport's economics |
| What's the right `eoh_rate_estimate` for the schedule pre-builder? | §3.D — use first-pass heuristic or sample from historical operation |
| Will forced outage events fire often enough to be visible? | §3.E sampling — P_forced is small (~0.01-0.05/day) so over 9 yr we expect 5-20 events |
| Does the 9-year horizon hit the MI threshold (48,000 EOH) for any mode? | §3.D + §3.F — depends on EOH burn rate; Lockport's low CF means MI may not fire even in 9 yr |
| Should the cold-start frequency proxy be re-tuned for non-summer windows? | §3.I MOR validation — if modeled cold-start frequency too low |
| How does the wear-penalty mechanic feel in practice? | §3.G plot 3 — visible "self-curtailment" should appear in Mode C late in year |

---

## §10. Risks / things that could go wrong

| Risk | Mitigation |
|---|---|
| 9-year simulation runtime > expected | Profile; if > 5 min, reduce to 5-yr window for v1 |
| Bucket B constants produce implausible EOH burn rate → inspection never fires or fires too often | §3.K sanity check on inspection count; document if implausible |
| Mode C wear penalty too aggressive → plant offline most of time | §3.G plot — Mode C should still capture some spark; if zero, penalty curve too steep |
| Forced outage event sampling concentrates events unrealistically | Cross-check with prototype tornado: P_BG_AGE_MAX is dominant; outage frequency should be in plausible range |
| LTSA placeholder values produce unrealistic dollar magnitudes | Document in model_card — the dollar values aren't real; the proportions and direction are what matter |
| MOR validation shows large divergence (e.g., 50% off on 2024 generation) | Document; flag for future ADR refinement |

---

## §11. Output artifacts

- **`notebooks/04_full_path_mode_comparison.ipynb`** + paired `.py`
- 6 plots embedded
- `data/outputs/lockport/runs/notebook4_<ts>/`:
  - `model_card.md`
  - `state_trajectory_mode_{a,b,c}.parquet`
  - `daily_summary_mode_{a,b,c}.parquet`
  - `ltsa_streams_mode_{a,b,c}.parquet`
  - `inspection_events.parquet`
  - `forced_outage_events.parquet`
  - `run_config.yaml` — seed, mode params, escalation rate, etc., for reproducibility

---

## §12. Reference

- **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) §8 Phase J
- **Notebook 1, 2, 3 plans + notebooks**: see sibling plans
- **Understanding doc**: [`../../../extra/understanding_of_gas_turbine_digital_twin.md`](../../../extra/understanding_of_gas_turbine_digital_twin.md) §3.2 (twin attribution), §3.3 (LTSA streams), §4 (daily loop), §5 (Mode A/B/C), §6 (state vector), §7 (forced outage), §8 (calendar maintenance), §13 (sensitivity)
- **Prototype code reference**: [`../../../extra/gas-turbine-digital-twin/`](../../../extra/gas-turbine-digital-twin/) — `EnggDTwin_model.py`, `dispatch_model.py`, `LTSAContract.py`
- **ADRs**: [`../../../decisions/001-gas-hub-treatment-v1.md`](../../../decisions/001-gas-hub-treatment-v1.md), [`../../../decisions/002-lockport-specific-vs-generic-calibration.md`](../../../decisions/002-lockport-specific-vs-generic-calibration.md)
- **Status taxonomy + placeholder caveats**: [`../../../assumptions/`](../../../assumptions/)
- **Caveats**: [`../../../../data/assets/lockport/caveats.md`](../../../../data/assets/lockport/caveats.md)

---

## §13. Suggested execution sequence

1. **Write `notebooks/04_full_path_mode_comparison.py`** following §3 cell-by-cell sketch
2. **Run as Python script** to verify
3. **Convert to `.ipynb`** via jupytext
4. **Execute with nbclient** to embed plots
5. **Visual review** — most critical for N4: mode-comparison directional trade-off; LTSA stream stacked area; inspection event timeline
6. **Inspect model_card.md output** — does it summarize the run accurately?
7. **Update this plan** with findings if conventions changed
8. **Update consolidation plan §13 status log** with Phase J completion + observed mode trade-off magnitude
9. **Write Phase L Monte Carlo plan** informed by N4 results — what parameters to sweep, what number of paths, what tail-event scenarios to add
