# Dispatch Economics — spark → effective spark → margin, with worked examples

> **What this doc is.** A zoom-in on **how one hour's dispatch margin is built** — the four-line stack `fuel_cost → spark → effective_spark → margin` — and exactly **where temperature enters** (capacity, not the per-MWh spark). It's the *dispatch-decision* companion to [`outage_mechanics.md`](outage_mechanics.md) (the outage gates) and expands [`architecture.md`](architecture.md) §5.3 and [`flowcharts.md`](flowcharts.md) chart 5 with numbers.
>
> **Code**: `src/gt_engine/engine.py` — `dispatch_day_mode_aware` (the hourly loop), `cap_eff_for_mode`, `ambient_derate_factor`. Mechanics of the mode axes (A/B/C vs 3xCC/2xCC/1xCC) are in [`dispatch_mechanics.md`](dispatch_mechanics.md); this doc is the **$ decomposition**.

---

## §1. The four-line stack (per hour, per mode)

```
fuel_cost       = (HR / 1000) × (gas + RGGI)                       # $/MWh
spark           = LMP − fuel_cost − VOM                            # $/MWh  ← the raw spark spread
effective_spark = spark − (commitment_hurdle + wear_hurdle)        # $/MWh  ← ONLY when the plant is OFF (a start)
margin          = max(effective_spark, 0) × capacity(mode, temp)   # $/hour ← capacity is where temperature enters
```

The engine computes this for **every hour × every mode (3xCC / 2xCC / 1xCC)** and picks the mode with the highest `margin`. Reference constants (Lockport, v1): VOM = **$1.38/MWh**, RGGI ≈ **$1.00/MMBtu**, 3xCC HR = **8.901 MMBtu/MWh**, 3xCC nameplate ≈ **221 MW**.

The four lines, in words:
1. **`fuel_cost`** — what a MWh costs in fuel (heat rate × delivered gas, where delivered gas = Henry Hub + RGGI carbon).
2. **`spark`** — the gross per-MWh margin after fuel and variable O&M. **No explicit temperature here** (the mode HR is fixed in v1).
3. **`effective_spark`** — `spark` minus the **start hurdles**, applied **only when the plant is off** (deciding whether to *start*). When already running, `effective_spark = spark`.
4. **`margin`** — the per-MWh result × the **MW you can actually deliver**, and **that MW is the temperature-adjusted part**.

---

## §2. `effective_spark` — the start hurdles (a commitment adjustment, *not* temperature)

When the plant is **off**, starting it commits it for a minimum run window and consumes a start's worth of cost + wear. So a start must clear two extra per-MWh hurdles (amortized over the min-run window, `MIN_RUN_HOURS = 6`):

- **commitment hurdle** = `START_CM / 6` — the full non-fuel start cost (the "don't fire up the plant for one marginal hour" economics, the #2 fix).
- **wear hurdle** = `wear_mult × 0.42 × START_CM / 6` — the Mode A/B/C preservation penalty (the GT-wear fraction of a start).

With `START_CM` ≈ $55/MW for a **warm** start and Mode A (`wear_mult = 1.0`):
```
commitment_hurdle = 55 / 6              = $9.17/MWh
wear_hurdle       = 1.0 × 0.42 × 55 / 6 = $3.85/MWh
total start hurdle (warm, Mode A)       ≈ $13.0/MWh
```
(Cold start ≈ $79/MW → ~$18.7/MWh total; hot ≈ $35/MW → ~$8.3/MWh. Higher for colder starts.)

### Worked example A — same hour, "run if on" vs "won't start"

Hour: LMP = **$42/MWh**, gas $3.10, RGGI $1.00 (delivered $4.10), 3xCC.
```
fuel_cost = 8.901 × 4.10 = $36.49/MWh
spark     = 42 − 36.49 − 1.38 = $4.13/MWh      ← marginally positive
```

| Plant state | effective_spark | run? | margin |
|---|---|---|---|
| **Already running** (`op=True`) | `4.13` (no hurdle) | yes — stay on | 4.13 × 221 ≈ **$913/hr** |
| **Off**, warm start (Mode A) | `4.13 − 13.0 = −8.87` → `max(·,0)=0` | **no — won't start** | **$0** |

**Lesson**: the *same* $4.13/MWh hour keeps the plant running if it's already on, but is **not worth starting up for**. That asymmetry is `effective_spark` — and it's why the model doesn't fire up the whole plant to chase a single marginal hour. (None of this is temperature.)

---

## §3. `margin` — where temperature actually enters (capacity)

Temperature does **not** change `spark` or `effective_spark`. It enters via **capacity**:
```
capacity(mode, temp_f) = Σ nameplate_g × ambient_derate_factor(temp_f, g)
ambient_derate_factor:  ~+3% below 32°F (winter boost),  ~−3% above 90°F (summer derate),  linear between
```
So temperature scales the **MW**, which multiplies the (temperature-independent) per-MWh spark.

### Worked example B — same spark, MW swings with temperature

One economic hour: LMP **$45**, gas $3.10, RGGI $1.00, 3xCC, plant **already on**.
```
fuel_cost = 8.901 × 4.10 = $36.49/MWh
spark     = 45 − 36.49 − 1.38 = $7.13/MWh      ← the SAME at −5°F or 95°F
```

| Day | Temp | derate | Capacity (MW) | spark ($/MWh) | **Margin ($/hr)** |
|---|---|---|---|---|---|
| Cold | ≤ 32°F | ×1.03 | 221 × 1.03 = **227.6** | $7.13 *(same)* | 7.13 × 227.6 = **$1,623** |
| Mild | ~61°F | ×1.00 | **221.0** | $7.13 *(same)* | 7.13 × 221.0 = **$1,576** |
| Hot | ≥ 90°F | ×0.97 | 221 × 0.97 = **214.4** | $7.13 *(same)* | 7.13 × 214.4 = **$1,529** |

**Lesson**: identical $7.13/MWh spark; only the **MW** moves (227.6 → 214.4), so the hourly **margin** swings ~6% (cold→hot) — purely the **"fewer MW × the same spark"** effect. That is the *only* way temperature touches dispatch in v1.

### The channel v1 leaves out — the "double hit"

In reality, hot ambient **also** worsens the heat rate (less efficient → more fuel/MWh) → **lower per-MWh spark**. v1's mode HRs are fixed, so it misses this. If the hot day's HR worsened ~2%:
```
hot fuel_cost = (8.901 × 1.02) × 4.10 = $37.22/MWh
hot spark     = 45 − 37.22 − 1.38     = $6.40/MWh   (vs $7.13)
hot margin    = 6.40 × 214.4          = $1,372/hr   (vs v1's $1,529)
```
So reality hits the hot day **twice** — fewer MW (capacity) **and** thinner spark (heat rate). **v1 captures only the MW hit.** (Documented gap: [`temperature_load_fidelity.md`](extra/temperature_load_fidelity.md) §2.)

---

## §4. The rest of the per-hour decision (for completeness)

- **Mode pick**: the engine evaluates 3xCC / 2xCC / 1xCC and takes the highest `margin`. Because 3xCC has both the best HR and the most MW, it dominates whenever spark > 0 (why 2xCC never wins economically in v1 — see [`temperature_load_fidelity.md`](extra/temperature_load_fidelity.md) §3.4).
- **Must-run / steam-only fallback**: if the best `margin ≤ 0` on a **must-run** (cold, steam-obligation) day, the plant doesn't go offline — it runs 1xCC at a loss, or **steam-only** (0 MWh, gas-for-steam only) if even peak-hour 3xCC spark ≤ 0. (Cogen runs for *heat*, not power, on those days.)
- **Twin dispatch**: every hour is evaluated **twice** — once with the *clean* HR and once with the *degraded* HR — purely to attribute the $ cost of degradation (`loss_degradation = clean margin − degraded margin`). Only the **degraded** run drives state and the recorded result.
- **Full-capacity assumption**: when a mode runs, it runs at **full** `capacity(mode, temp)` — v1 has no part-load output (that's the behavioral-output #3 / Stream A work). So `margin` is always `spark × full_capacity`, never a part-load quantity.

---

## §5. Summary table — what adjusts each quantity

| Quantity | Adjusted by | NOT adjusted by |
|---|---|---|
| `fuel_cost` | heat rate, gas, RGGI | (HR is fixed per mode in v1 — not temperature) |
| `spark` | LMP, fuel_cost, VOM | **temperature** (no explicit channel in v1) |
| `effective_spark` | `spark` − **start hurdles** (commitment + wear), **only when off** | temperature |
| `margin` | `effective_spark` × **capacity**, and **capacity = the temperature-adjusted part** (ambient derate) | — |

**One line**: temperature scales **how many MW** you can sell; it does **not** (in v1) change the **dollars per MWh** — even though in the real world it does both (capacity *and* heat rate).

---

## §6. Cross-references
- [`architecture.md`](architecture.md) §5.3 (dispatch decision), §5.5 (Mode A/B/C wear curve)
- [`flowcharts.md`](flowcharts.md) chart 5 (the dispatch decision, visual)
- [`dispatch_mechanics.md`](dispatch_mechanics.md) — operating mode × policy mode (the mode *axes*)
- [`outage_mechanics.md`](outage_mechanics.md) — the outage-gate companion deep-dive
- [`extra/temperature_load_fidelity.md`](extra/temperature_load_fidelity.md) §2 (the missing heat-rate channel), §9 (the commitment hurdle)
- [`implementation/gt_engine/05_worked_example.md`](../implementation/gt_engine/05_worked_example.md) — a full day traced end-to-end
