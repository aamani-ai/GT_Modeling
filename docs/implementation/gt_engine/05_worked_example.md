# gt_engine — Worked Example: one day through the engine

> A concrete trace of a single simulated day, to make the [`02_code_architecture.md`](02_code_architecture.md) loop tangible. Numbers are **illustrative** (rounded, plausible) — the point is the *flow*, not exact values.

We trace **Mode A**, a cold winter day where the plant was running yesterday. Entering the day:

```
PlantState (from yesterday's close):
  eoh=31,240  hr_recov=0.9%  fouling=2.1%  dc=0.006  df=0.18  tbc_time=7,050
  op=True  hrs_off=0  last_stype="warm"
ltsa_state: fixed_fee_cum=$58.2M  eoh_reserve_cum=$1.1M  ... (cumulative so far)
```

---

### [1] Year boundary?
Not Jan 1 → skip. `ytd_calendar_days += 1`.

### [2] Continuing outage?
`state.outage_days_remaining == 0` → no. Proceed. `ytd_avail_days += 1`.

### [3] Forced-outage draw
`p_forced_components(state)` →
```
p_combustion(df=0.18)  = 0      (df < 0.60 inflection)
p_creep(dc=0.006)      = 0      (dc < 0.50 inflection)
p_tbc(tbc_time=7050)   ≈ 0.0004 (Weibull, far below η=28,000)
p_rotor                ≈ 0.0001
p_hrsg (aged)          ≈ 0.0078
p_bg   (aged)          ≈ 0.0042
→ p_combined           ≈ 0.0125   (~1.25%/day)
```
`rng.random() = 0.83 > 0.0125` → **no outage**. (Had it fired while `op=True`, ADR-007 trip wear would add `df += 0.008`, `eoh += 160`, and the day would end here.)

### [4]–[5] Inspection headroom + policy hurdle
Next inspection = MI @ EOH 48,000. Headroom = 48,000 − 31,240 = 16,760. Mode A → `wear_penalty_mult = 1.0` (no curtailment). (Mode C here would also be ~1.0 — headroom > 4,000.)

### [6] Gas price
`henry` most-recent trade ≤ today → `gas_hh = $3.10/MMBtu`. Delivered = 3.10 + RGGI 0.995 = **$4.10/MMBtu**.

### [7] Build the day's 24-hour frame
From `lmp_window` (24 hourly DA prices, ~$22–48/MWh, winter) + `weather_window` (`temp_f` ≈ 18–28°F). This day is in the coldest-20% set → **`must_run = True`** (cogen proxy).

### [8] Twin dispatch — `dispatch_day_mode_aware` (×2)
For each hour, each mode: `spark = LMP − (HR/1000)(gas+RGGI) − VOM`. Example hour (LMP $38, 3xCC HR 8,901, degraded):
```
fuel_cost = 8.901 × 4.10 = $36.5/MWh ;  spark = 38 − 36.5 − 1.38 = $0.12/MWh  (barely economic)
```
The unit was already on (`op=True`) → no commitment hurdle this hour. Best mode = 3xCC when spark>0; on the few hours spark<0, the **must-run** branch keeps 1xCC (or steam-only if even peak-hour 3xCC spark ≤ 0). Ambient ≈ 22°F → `ambient_wear_factor ≈ 0.95` accumulated per fired hour into `fired_hours_hotweighted`.
```
Degraded run → fired_hours=24, mwh_degraded≈4,100, margin_degraded≈ +$3,800, fired_hours_hot≈22.9, starts=[]
Clean run    → margin_clean ≈ +$5,200
loss_degradation = 5,200 − 3,800 = $1,400   (the $ cost of degradation today)
```

### [9] Warming gas
No cold starts today → no warming-gas correction.

### [10] Commit + `update_stress(fired_hours=24, starts=[], fired_hours_hot=22.9)`
```
eoh        += 24 (+0 start EOH)            → 31,264
tbc_time   += 22.9  (ambient-weighted)     → 7,073     ← cold day < ref → <24
dc         += CREEP_RATE × 22.9            → 0.0061    ← hot-section, ambient-weighted
fouling    += small approach to 2.5%       → 2.11%
hr_recov   += 24×1e-5×100                  → 0.92%
rotor_life += rate × 24 (raw)              → +tiny
df unchanged (no starts)
```

### [11] LTSA accrual — `accrue_daily_ltsa(delta_eoh=24, starts=[])`
```
fixed_fee_cum   += daily fee × escalation   (≈ +$33k)
eoh_reserve_cum += 24 × $175/EOH × esc      (≈ +$4.6k)
overage_cum     += 0  (no starts today)
```
Cycle-end HR trackers accumulate today's fuel + MWh (used at the next inspection's HR-penalty check).

### [12] Inspection trigger?
`calendar_hit`: today < scheduled MI date → no. `hard_stop_hit`: eoh 31,264 < 48,000+1,500 → no. → **no inspection**.

**Record the day** → append the `daily` row (mwh, margin, fired_hours, eoh, dc, df, the cumulative LTSA streams…). Advance to tomorrow, which inherits `PlantState(eoh=31,264, tbc_time=7,073, dc=0.0061, …)`.

---

## Two contrasting days (why the state matters)

| | This cold winter must-run day | A hot summer mid-merit day |
|---|---|---|
| LMP / spark | low, thin/negative → must-run holds it on | high → genuinely economic, runs for profit |
| `ambient_wear_factor` | ~0.95 (cold → **slower** hot-section wear) | ~1.18 (hot → **faster** creep/TBC) |
| Dispatch | 1xCC/steam-only on uneconomic hours (cogen) | 3xCC full-out |
| Net that day | small loss/breakeven (running for steam) | positive spark margin |

This is the whole engine in miniature: **yesterday's state → today's (degraded) dispatch decision → today's running consumes life (ambient-weighted) → tomorrow's state**, with LTSA metering the cost and inspections/outages punctuating it. Multiply by 3,287 days × 3 modes for the historical run, or by each analog window for the forward run.
