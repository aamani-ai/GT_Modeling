# Dispatch Mechanics — How Lockport Decides What to Run Each Hour

> Deep dive on the dispatch decision. Read after [`architecture.md`](./architecture.md) §5 (the engine overview). This doc unpacks two things the architecture doc glosses over:
>
> 1. The two completely different things we've been calling "mode" — **operating mode** vs **policy mode** — and how they interact in the per-hour decision.
> 2. Concrete numerical walkthroughs of the dispatch math, including why **2×CC never fires in v1** and how the **cogen must-run override** works.
>
> If you're reading this and `operating mode` vs `policy mode` doesn't ring an immediate bell, start with §1.

---

## §1. The two meanings of "mode" — clearing up the confusion

In the codebase and earlier docs, "mode" gets used for two completely different concepts. They live on different axes and answer different questions:

| Term we'll use | Maps to | What it means | Where it lives in the code |
|---|---|---|---|
| **Operating mode** | `3×CC` / `2×CC` / `1×CC` | Physical configuration — how many CTs are spinning, with associated heat rate and capacity | `MODES` dict in [`04_full_path_mode_comparison.py`](../../notebooks/04_full_path_mode_comparison.py) §C; iterated inside the hourly loop |
| **Policy mode** (or "dispatch policy mode") | `A` / `B` / `C` | Investor / operator policy — how aggressively to self-curtail starts near an inspection threshold | `wear_mult` parameter passed into `dispatch_day_mode_aware`; set once per day from `wear_penalty_mult(policy, eoh_headroom)` |

**The mental model**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       The dispatch decision                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   OUTER axis (set once per day, per simulation):                        │
│     Policy mode = A / B / C                                              │
│     → determines wear_mult (1.0 to 4.0)                                  │
│     → affects how expensive it is to START                               │
│                                                                          │
│         │                                                                │
│         ▼                                                                │
│                                                                          │
│   INNER loop (per hour, per day):                                       │
│     For each operating mode in [3×CC, 2×CC, 1×CC]:                      │
│       compute spark = LMP − fuel(operating_HR) − VOM                     │
│       compute hurdle = wear_penalty(start_type, policy) / 6              │
│       effective_spark = spark − (hurdle if currently_off else 0)         │
│       margin = max(effective_spark, 0) × operating_capacity              │
│     Pick the operating mode with the highest margin.                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Architecture §5.3's `HR_btu_per_kwh` and `mode_capacity_mw` change with operating mode.** That's the inner loop choice — three numbers per hour: 3×CC spark, 2×CC spark, 1×CC spark.

**The `wear_penalty` term changes with policy mode** — A/B/C set the wear_mult that scales the start hurdle. Same plant, same hour, same LMP can produce a different operating-mode pick depending on which policy is in force.

When earlier docs talked about "mode A spark vs mode C spark over 9 years," they meant **policy mode**. When the model_card backtest table compared "3×CC share vs MOR's 26% 2×CC," it meant **operating mode**. The naming overlap is a real source of confusion.

**From here on**: "operating mode" = the inner-loop physical config; "policy mode" = the outer wear-penalty knob. Both old usages get translated as we go.

---

## §2. Operating mode — the physical configuration

The plant can physically run in three configurations. Each has its own heat rate, capacity, and ambient-derate behavior.

### §2.1 Per-operating-mode constants (MOR-derived `real_observed`)

| Operating mode | What it is | `HR_btu_per_kwh` | `mode_capacity_mw` (nameplate, no derate) |
|---|---|---:|---:|
| **3×CC_full** | All 3 CTs + 1 ST | **8,901** | **221.3** |
| **2×CC** | 2 of 3 CTs + 1 ST | 9,598 | 172.6 |
| **1×CC** | 1 of 3 CTs + 1 ST | 10,424 | 123.9 |

Values come from [`operating_profile.yaml`](../../data/assets/lockport/operating_profile.yaml) (HR) and [`engineering.yaml`](../../data/assets/lockport/engineering.yaml) (capacity).

**Why 3×CC has the lowest HR**: more CT exhaust mass flow per unit of ST steam capacity → ST runs closer to design point → block-level efficiency peaks. Real-world combined-cycle physics.

### §2.2 What the hourly margin looks like at a typical operating point

Take LMP = $50/MWh, delivered gas (Henry Hub + RGGI) = $4.495/MMBtu, VOM = $1.38/MWh, no degradation, ignore wear hurdle:

| Step | 3×CC | 2×CC | 1×CC |
|---|---:|---:|---:|
| `fuel_cost = HR/1000 × $4.495` | $40.01/MWh | $43.14/MWh | $46.86/MWh |
| `spark = $50 − fuel − $1.38` | **$8.61/MWh** | $5.48/MWh | $1.76/MWh |
| `margin = spark × capacity` | **$1,905/hr** | $946/hr | $218/hr |

**3×CC wins by 2× over 2×CC and 9× over 1×CC.** And this isn't accidental — it's structural:

- 3×CC has the **lowest HR** → highest spark *per MWh*
- 3×CC has the **highest capacity** → most MWh to multiply spark by
- `spark_3×CC × cap_3×CC > spark_2×CC × cap_2×CC > spark_1×CC × cap_1×CC`, **always**, when spark is positive

So in v1, when ANY operating mode is economic, **3×CC wins**. See §5 below for what happens when none is, and why 2×CC therefore literally never appears.

### §2.3 Ambient derate per operating mode

Capacity is adjusted hourly by ambient temperature via `cap_eff_for_mode(mode_name, temp_f)` in [`dispatch_mechanics`](../../notebooks/04_full_path_mode_comparison.py) §E.1. Combustion turbines lose power in hot air (less mass flow at fixed volume) and gain in cold:

- At 90°F: 1 − `summer_derate_pct/100` (about −3%)
- At 32°F: 1 + `winter_boost_pct/100` (about +3%)
- Linear interp in between

The block-level derate is the capacity-weighted average of the operating CTs' derate plus the ST's. Doesn't change the operating mode ordering — all three modes shift together — just shifts the absolute MW dispatched.

---

## §3. Policy mode — the wear-penalty curve

The policy mode answers a different question: **how much should the model penalize a marginal start as the plant gets close to its next inspection?**

### §3.1 The intuition

Every start adds EOH to the plant. EOH accumulation eventually triggers a Combustion Inspection (CI) or Major Inspection (MI), which costs money (owner-uncovered share + heat-rate penalty + outage). So a start has two costs:

1. **The cash spent on fuel + cycling wear**, already in spark margin via VOM and the Kumar cycling cost (in real terms — v1 only includes VOM in the spark formula; Kumar feeds the wear hurdle separately)
2. **The "EOH pull-forward" of the next inspection** — a start today brings the next $10.5M MI a few EOH closer

The policy mode is how much weight #2 gets. Mode A ignores it; Mode C cares a lot.

### §3.2 The wear-penalty multiplier curve

```
wear_mult
   ▲
4.0│                                  ┐ Policy C (caps at 4.0×, headroom ≤ 0)
   │                              ╱
   │                           ╱
3.0│                        ╱
   │                     ╱
2.5│                  ╱─────────────  Policy B (caps at 2.5×, headroom ≤ 1,000)
   │                ╱╱
2.0│              ╱  ╱
   │            ╱   ╱
1.5│          ╱   ╱
   │        ╱   ╱
1.0│──────╱───╱─────────────────────  Policy A (always 1.0×)
   │
   └──────────────────────────────────→ EOH headroom (= threshold − current_eoh)
   0    1K   2K   3K   4K
```

Defined in [`wear_penalty_mult`](../../notebooks/04_full_path_mode_comparison.py) §C. Headroom is computed once per day from the pre-built maintenance schedule and current state EOH.

### §3.3 How the wear hurdle is applied

The wear_mult feeds into a per-MWh hurdle that's subtracted from spark **only when the plant is currently off** (i.e., a start is being considered):

```
wear_penalty_per_MW   = wear_mult × GT_WEAR_FRACTION (0.42) × Kumar_$/MW_by_start_type
wear_hurdle_per_MWh   = wear_penalty_per_MW / MIN_RUN_HOURS (6)
```

**The Kumar $/MW** depends on the start type (hot/warm/cold), which is determined by `hrs_off`:

| Start type | Condition | Kumar C&M ($/MW, 2011 USD) | Why expensive |
|---|---|---:|---|
| **hot** | `hrs_off < 8` | $35/MW | HRSG still pressured; lowest thermal shock |
| **warm** | `8 ≤ hrs_off < 72` | $55/MW | Partial cool-down |
| **cold** | `hrs_off ≥ 72` | $79/MW | Full overnight cool; biggest thermal shock |

So **the wear hurdle scales with both policy mode AND start type**. A cold start in Policy C is the most expensive case; a hot start in Policy A is the cheapest.

### §3.4 Per-policy wear hurdle on a cold start

Worked numbers for a cold start (Kumar $79/MW base):

| Policy | wear_mult when far from inspection (headroom > 4K) | wear_mult when AT threshold (headroom = 0) | Hurdle range ($/MWh) |
|---|---:|---:|---|
| **A** | 1.0 | 1.0 | $5.53 always |
| **B** | 1.0 | 2.5 (clamped at headroom ≤ 1K) | $5.53 → $13.83 |
| **C** | 1.0 | 4.0 (only when headroom ≤ 0) | $5.53 → $22.13 |

The hurdle starts the same across policies when the plant is far from an inspection. As headroom shrinks, Policy B and C ramp the hurdle up — making marginal starts increasingly uneconomic — while Policy A stays flat.

For a **hot start** (Kumar $35), the hurdle is correspondingly smaller: A = $2.45/MWh, C-at-threshold = $9.80/MWh.

---

## §4. The two-axis dispatch decision — a worked example

Putting both axes together. **Plant currently off** (so a start is being considered). Cold start (hrs_off ≥ 72). LMP = $50/MWh, delivered gas = $4/MMBtu, VOM = $1.38/MWh. **EOH headroom = 500 (close to threshold).**

### §4.1 Per policy mode, what wear_mult fires?

| Policy | Formula | wear_mult | Cold-start hurdle ($/MWh) |
|---|---|---:|---:|
| A | flat 1.0 | 1.0 | $5.53 |
| B | clamped at 2.5 (headroom < 1,000) | 2.5 | $13.83 |
| C | `1 + (4000−500)/4000 × (4.0−1.0)` | ≈ 3.6 | ≈ $19.91 |

### §4.2 Per (operating mode × policy mode), what's the effective spark?

Bare spark (LMP − fuel − VOM) is the same regardless of policy. Subtracting the hurdle gives:

| Step | 3×CC | 2×CC | 1×CC |
|---|---:|---:|---:|
| `fuel_cost = HR/1000 × $4` | $35.60 | $38.39 | $41.70 |
| `bare_spark = $50 − fuel − $1.38` | **$13.02** | $10.23 | $6.92 |
| `effective_spark` (Policy A: hurdle $5.53) | $7.49 | $4.70 | $1.39 |
| `effective_spark` (Policy B: hurdle $13.83) | **−$0.81** | −$3.60 | −$6.91 |
| `effective_spark` (Policy C: hurdle $19.91) | **−$6.89** | −$9.68 | −$12.99 |

### §4.3 What operating mode does each policy pick?

The dispatch rule: pick the operating mode with the **highest positive margin**; if none is positive, go offline (or 1×CC if must-run).

| Policy | Best operating mode | Hourly margin |
|---|---|---:|
| **A** | 3×CC starts | +$1,658/hr (= $7.49 × 221.3) |
| **B** | All effective sparks negative → **offline** | $0 |
| **C** | All effective sparks negative → **offline** | $0 |

**That's the mechanic in one table.** Same LMP, same gas, same plant state. Policy A takes a profitable start; Policy C declines it because it doesn't want to bring the inspection date forward.

The $1,658/hr that Policy C "leaves on the table" is the **cost of pushing the inspection out** — paid in foregone spark today, in hopes of larger inspection-cost-deferral savings down the line. Whether the trade pays off depends on what inspection costs eventually look like (real LTSA values from the data room) and how many hours of self-curtailment compound.

**In Lockport's v1 run** (placeholder LTSA values), Policy A nets the highest 9-year P&L. Policy C's curtailment didn't pay off because:
1. Lockport's CF is so low that EOH headroom rarely falls below 4,000 (the curve activates late)
2. Placeholder LTSA values don't make inspection avoidance valuable enough

---

## §5. Why operating mode 2×CC never wins in v1

You might have noticed in any model_card backtest:

```
                MOR 2024 observed    v1 Mode A modeled
                ─────────────────   ─────────────────
   3×CC share:        64.9%                74.1%
   2×CC share:        26.1%   ←──   v1: ────────── 0.0%   ← THE GAP
   1×CC share:         8.9%                25.9%
```

The 0% 2×CC modeled share is **structural to v1's dispatch math**, not an artifact:

- `spark_3×CC > spark_2×CC` always (3×CC has lower HR → higher spark per MWh)
- `cap_3×CC > cap_2×CC` always (3 CTs > 2 CTs)
- So `margin_3×CC > margin_2×CC` whenever margin is positive

For 2×CC to ever win, you'd need either `spark_2×CC > spark_3×CC` (impossible — higher HR) or `cap_2×CC > cap_3×CC` (impossible — fewer CTs). Neither can happen.

The wear-penalty doesn't help either, because the hurdle is applied **per MWh equally across operating modes** at any given hour (same start type, same policy). The 3×CC ranking advantage is preserved.

### §5.1 Why real Lockport DOES run 2×CC ~26% of the time

Four real-world mechanics that v1 doesn't represent:

| Mechanic | What happens at real Lockport | v1's blind spot |
|---|---|---|
| **Single-CT planned outage** | One of three CTs goes offline for maintenance; the block continues as 2×CC | v1 has **block-level state**, not per-generator state. Can't represent "1 of 3 CTs down." |
| **Single-CT forced outage** | A CT trips on a fault; the other two keep running as 2×CC for hours/days | Same — no per-generator state |
| **Variable steam-host demand** | Cogen host needs an intermediate steam flow; 2×CC matches better than 1×CC or 3×CC | v1 has a **binary** must-run flag; no continuous steam demand profile |
| **Min-load constraints** | 3×CC may have a minimum dispatch floor (~140 MW); operator drops to 2×CC when grid demand is below that | v1 has **no min-load floor**; 3×CC can dispatch at any MW |

The dominant cause is the first two. EIA-860 and GADS data both show Lockport spends material time with one CT offline. That's just "2×CC operating mode" emerging from per-generator availability.

### §5.2 The v2 fix — per-generator state

The remedy is in [`gaps_and_priorities.md §6`](./gaps_and_priorities.md) priority #9: rewrite `PlantState` to hold four sub-states (GEN1, GEN2, GEN3, GEN4) instead of one block-level state. Then teach dispatch, maintenance, and forced-outage to operate at generator grain.

Once that's done, the operating mode **emerges from CT availability**:

```python
For each hour:
    available_cts = [g for g in GEN1..GEN3 if not g.in_outage]
    if len(available_cts) == 3 and 3xCC is economic: operating_mode = "3×CC"
    elif len(available_cts) == 2: operating_mode = "2×CC"
    elif len(available_cts) == 1: operating_mode = "1×CC"
    elif must_run: operating_mode = whatever min config is available
    else: offline
```

The 26% 2×CC share would emerge naturally because that's roughly the fraction of time one CT is in planned/forced outage. **Order of operations reverses**: v1 picks operating mode by economics; v2 picks it by availability, then by economics within the available set.

---

## §6. The cogen must-run override

### §6.1 The physics — TWO modes of steam delivery at Lockport (corrected)

> **Correction**: an earlier version of this section claimed "at Lockport, you can't produce steam without also producing electricity — there's no path to steam that doesn't go through the CT." The MOR backtest in [`backtest_findings.md §3.4`](./extra/backtest_findings.md) shows this is wrong. **460 days out of 1,826 (25%) over 2021-2025 had non-zero gas burn and non-zero DHTS delivery with ZERO MWh generation.** Lockport has a steam-only operating mode.

The full picture:

```
                                ┌─── shaft power → grid (only in mode A below)
                                │
   gas ──→ CT (any of GEN1-3) ──┤
                                │
                                └─── hot exhaust ──→ HRSG ──→ steam ──┬─→ ST → electricity → grid
                                                                      │           (only in mode A)
                                                                      └─→ steam extraction → cogen host
                                                                          (BOTH modes A & B)

                                ┌─── duct burner / fresh-fire / aux mechanism
   gas ──→ HRSG directly ──────┤                                       (the mechanism is TBD;
   (or via unsynced CT path)    └─── steam ──→ cogen host                MOR data confirms it exists
                                              (mode B: STEAM-ONLY)       but mechanics need investigation)
```

**Two real operating modes for steam delivery**:

| Steam-delivery mode | What it means | Frequency in MOR | v1 modeled? |
|---|---|---:|---|
| **A — Coupled** | CT runs → exhaust feeds HRSG → both steam and electricity | ~75% of operating days | ✓ (modeled as 3×CC/2×CC/1×CC) |
| **B — Steam-only** | Gas burns through some mechanism (duct burner / aux boiler / CT bypass) → steam only, no electricity | **~25% of all days (460/1,826)** | ✗ Not modeled |

The exact mechanism for Mode B is unclear from the documents in the data room — could be:
- An auxiliary boiler (we previously thought Lockport didn't have one; needs re-investigation)
- HRSG duct burners with bypassed/unsynced CTs
- Fresh-fire mode on the HRSG itself

Whatever the mechanism, it's a real, frequent operating regime that consumes ~580 MMBtu of gas per day to deliver ~270 MMBtu of steam (45.8% gas-to-steam efficiency). When in this mode, the plant **does not** produce electricity, **does not** accumulate engineering wear (CTs are off), and **does** continue to fulfill the cogen steam obligation.

### §6.2 What the must-run code path does (and what it misses)

```python
if best_margin <= 0:                # no operating mode is economic
    if must_run:                    # cogen DHTS day — host needs steam
        operating_mode = "1×CC"     # forced to run; produces ~124 MW + steam
        dispatch at whatever spark; accept the loss
    else:
        operating_mode = "offline"  # all CTs off, no steam, no electricity
```

The current code **only models the coupled path (Mode A)**. When must-run fires and dispatch is uneconomic, it forces 1×CC — i.e., one CT spinning + ST + steam to host + ~124 MW to grid.

**What the code is missing**: real Lockport often picks **Mode B (steam-only)** on those same days. So when must-run is binary-true in v1, the real plant has a *three-way* choice:

1. **Run 1×CC** (or more) → MWh + steam + EOH wear + fuel cost + some electric revenue (or loss)
2. **Run steam-only** → 0 MWh + steam + 0 EOH wear + smaller fuel cost + 0 electric revenue
3. **Stay offline** → 0 of everything, including breaking the steam contract

The model treats option 2 as if it doesn't exist. So on days when the real plant ran steam-only, v1 instead forces 1×CC dispatch — **over-counting MWh, over-counting EOH wear, over-counting fuel cost, and over-counting the (typically negative) electric margin**. This is a major contributor to the 2.22× over-commit found in [`backtest_findings.md §3.1`](./extra/backtest_findings.md).

**Why steam-only might be the better real choice** when LMP < fuel cost: gas burned through a duct burner uses ~30-50% as much gas per MMBtu of steam as gas burned through a CT (you don't pay for the lost shaft-power-as-heat). So if there's no useful market for the electricity, burning gas in the most direct path to steam is cheaper. The plant pays only the steam fuel cost, no electric loss.

### §6.3 Why must-run isn't "just an arbitrary loss" in real economics

In v1, must-run hours look like pure pain. But that's because v1 only sees the electricity side. The reality:

```
Electric side:    revenue = LMP × 123.9 MW
                  cost    = fuel + RGGI + VOM (1×CC HR)
                  margin  = often negative                       ← v1 sees this

Steam side:       revenue = steam delivered × steam tariff       ← v1 says $0
                  cost    = ~$0 (exhaust heat is "free" — coupled byproduct)
                  margin  = positive

Net cogen-hour margin:   electric + steam (often net positive)   ← reality
```

Example at LMP=$30/hr, 200 MMBtu/hr steam at $8/MMBtu:
- Electric margin: 1×CC bleeds ~$2,260/hr at that LMP
- Steam revenue: 200 × $8 = $1,600/hr (no incremental cost)
- **Net cogen-hour margin: −$660/hr** (much less bad than v1's −$2,260)

In some hours, steam revenue **exceeds** the electric loss → the must-run hour is genuinely profitable. **That's why cogens exist as a business model**: the steam contract pays for the privilege of being able to deliver steam, and the electric side is partly a byproduct economics.

The missing-revenue gap (R3 in [`pnl_ledger.md §3.A`](./pnl_ledger.md)) is the structural reason v1's Net P&L is over-pessimistic on must-run days. See [`gaps_and_priorities.md §3`](./gaps_and_priorities.md) Leg 2.

### §6.4 The v1 must-run flag is a synthetic proxy

v1 doesn't have a real DHTS extracted from MOR. The `must_run` flag in N4 is a **synthetic proxy**: coldest 20% of days in the window are flagged must-run. Reasoning: industrial steam hosts often need more steam in winter, so cold days are a rough proxy for must-run-required days.

Documented as a caveat in [`caveats.md §3`](../../data/assets/lockport/caveats.md), flagged for fix in v2 (extract real DHTS from MOR data).

The v1 chain of approximations on cogen:
1. **Real DHTS** → synthetic temp-based binary flag
2. **Steam revenue** → $0 (not modeled)
3. **Variable steam demand** → binary on/off
4. **Aux boiler / bypass options** → not modeled (Lockport doesn't have them anyway)

Structure correct; values missing.

---

## §7. Two subtleties worth catching

### §7.1 The wear hurdle only applies when STARTING

From [`dispatch_day_mode_aware`](../../notebooks/04_full_path_mode_comparison.py) §E.2:

```python
effective_spark = spark − (wear_hurdle_per_mwh if not op else 0.0)
```

If the plant is already running (`op == True`), no wear hurdle is applied — the spark spread is used as-is for the mode pick. **The hurdle only affects start decisions, not continue-running decisions.**

Practical consequence: once the plant has started, it tends to stay on as long as bare spark > 0. Policy mode B and C don't penalize keeping the plant on; they only penalize **bringing it on** when it's currently off. This is why mode divergence shows up in **start counts** (Policy A starts more often than C) rather than in fired hours per-run-streak.

### §7.2 Start type compounds with policy mode

The hurdle = `wear_mult × 0.42 × Kumar_$/MW(start_type)`. Both factors matter:

| Start type | Kumar $/MW | Hurdle (Policy A) | Hurdle (Policy C @ threshold) |
|---|---:|---:|---:|
| hot | $35 | $2.45/MWh | $9.80/MWh |
| warm | $55 | $3.85/MWh | $15.40/MWh |
| cold | $79 | $5.53/MWh | $22.13/MWh |

So a **cold start in Policy C near an inspection threshold** carries a $22.13/MWh effective hurdle — at $50/MWh LMP and $4/MMBtu gas, that completely wipes out 3×CC's $13/MWh bare spark and the start gets declined. A hot start under the same Policy C is much less suppressed ($9.80/MWh hurdle).

This is why Policy C is described in [`architecture.md §5.5`](./architecture.md) as "strongly penalizing cold starts" — same multiplier, but applied to a 2.3× bigger Kumar base, plus the multiplier itself is larger near a threshold. Compound effect.

---

## §8. The dispatch FAQ — quick answers

### §8.1 Is dispatch hourly or daily?

**Hourly mode choice, daily state update.** Every hour the model picks the best operating mode (or offline) from 24 decisions per day. State accumulators (EOH, fouling, dc, df, etc.) update once at the end of the day, summing the day's fired hours and starts.

### §8.2 Why is the policy mode set once per day, not per hour?

The wear_mult depends on EOH headroom = `threshold − state.eoh`. Within a single day, EOH grows by at most ~25 (a heavily-fired summer day), so the headroom shifts trivially. Setting wear_mult once per day at sim start of day is a fair approximation. Phase L Monte Carlo could revisit this, but the runtime gain isn't worth re-running it 24 times.

### §8.3 Can a hot/warm start ever be in a "must-run" cogen day?

Yes. The must-run flag is independent of the start-type determination. On a cold day flagged must-run, if the plant happened to have been running 8 hours earlier (e.g., the prior must-run day extended into early morning), the start would be classified hot or warm rather than cold. The must-run override only kicks in if no operating mode is economic; if 3×CC is economic on a must-run day, the plant fires 3×CC normally.

### §8.4 Can the model dispatch at less-than-full mode capacity?

No, not in v1. **Each operating mode dispatches at its full block capacity** (after ambient derate). There's no min-load floor, no part-loading within a mode. This is a v1 simplification; real plants have ramp constraints, part-load curves (HR worsens at low MW), and grid security constraints. v2 would add these.

### §8.5 What does "Mode A" mean in the model_card?

**Policy mode A**, not operating mode. The model_card reports results for three full simulations, each one using a different policy (A / B / C) across all 9 years. Within each simulation, the operating mode (3×CC / 2×CC / 1×CC / offline) is picked hour-by-hour. The 9-year totals for "Mode A" are the 24 × 3,287 hourly decisions made under Policy A.

### §8.6 Does Policy A always fire more than Policy B?

In Lockport's low-CF case in v1, yes — Policy A's total starts (~92/yr) exceed Policy B's (~84/yr) which exceed C's (~82/yr). But the differences are small because the wear hurdle rarely activates (Lockport's EOH headroom is large for most of the 9 years). In higher-CF or more start-intensive assets the divergence would be bigger.

---

## §9. Cross-references

| Concept | Where it's documented |
|---|---|
| Two-meaning-of-mode taxonomy | This doc §1 |
| Operating mode `MODES` dict + values | [`architecture.md §5.3`](./architecture.md), this doc §2 |
| Policy mode `wear_penalty_mult` curve | [`architecture.md §5.5`](./architecture.md), this doc §3 |
| Why 2×CC never fires | This doc §5 |
| Cogen must-run physics | This doc §6 |
| Per-generator state (v2 fix for 2×CC) | [`gaps_and_priorities.md §6`](./gaps_and_priorities.md) priority #9 |
| Missing steam revenue (R3) | [`pnl_ledger.md §3.A`](./pnl_ledger.md), [`gaps_and_priorities.md §3`](./gaps_and_priorities.md) |
| Synthetic must-run proxy caveat | [`caveats.md §3`](../../data/assets/lockport/caveats.md) |
| The actual code | [`notebooks/04_full_path_mode_comparison.py`](../../notebooks/04_full_path_mode_comparison.py) — `dispatch_day_mode_aware()` in §E.2, `wear_penalty_mult()` in §C |
| Mode comparison results | [`architecture.md §6.2`](./architecture.md) |
| Glossary entries for both kinds of mode | [`glossary.md`](./glossary.md) §1 (operating modes) and §4 (policy modes) |
