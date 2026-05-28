# Lockport v1 — Gaps and Improvement Priorities

> The honest self-assessment of what the v1 model gets right, where it's wrong, what fixing each issue would shift the headline numbers by, and what order to do the fixes in. Everything below is reasoned **per year** because annual is the natural unit for thinking about a power plant; the 9-year totals are derivations, not primary.
>
> Where this fits:
> - [`pnl_ledger.md`](./pnl_ledger.md) — the entry-point ledger of every revenue + cost component (read first)
> - [`architecture.md`](./architecture.md) describes what v1 *is*
> - **This doc** describes what v1 *isn't*, what's missing, and what to do next
> - [`glossary.md`](./glossary.md) defines the terms used here
> - The historical record of the v1 build is in [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md)

> **Post-2026-05-25 note**: The 9 bottom-up priorities in §6 are still the right *list*. Their *ordering* now flows from the strategic-phase structure in [`../plans/00_strategic_spine.md`](../plans/00_strategic_spine.md) §5.1, which maps each priority onto Phase 2 (data-fill), Phase 5 (fidelity), or Phase 6 (forward-looking). Read the strategic spine first to understand the phase context; this doc remains the authoritative source for *what each gap is, its dollar magnitude, and what closing it requires*.

---

## §1. The three-leg framing

The v1 Net P&L of **−$22.6M/year** (Mode A 9-year average) **is not a real claim about Lockport's economics.** It's the output of a model with three independent gaps that all push the number the same direction:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          v1 Net P&L = −$22.6M/yr                         │
└──────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
   ┌────────┴────────┐  ┌─────────┴────────┐  ┌─────────┴────────┐
   │ Leg 1: LTSA     │  │ Leg 2: Revenue   │  │ Leg 3: Dispatch  │
   │ cost values are │  │ streams are      │  │ realism is       │
   │ all PLACEHOLDER │  │ MISSING (only    │  │ MISSING (over-   │
   │ (Athens copy)   │  │ electricity in)  │  │ commits 2.4×)    │
   │                 │  │                  │  │                  │
   │ Likely shift:   │  │ Likely shift:    │  │ Likely shift:    │
   │ +$8–15M/yr      │  │ +$8–22M/yr       │  │ +$3–5M/yr        │
   │ (LTSA cost ↓)   │  │ (revenue ↑)      │  │ (LTSA cost ↓)    │
   └─────────────────┘  └──────────────────┘  └──────────────────┘
            │                     │                     │
            └─────────────────────┴─────────────────────┘
                                  │
                                  ▼
                  Mid-range combined shift: +$20–40M/yr
                  → "Improved" Net P&L → +$0 to +$20M/yr (central ~+$10M/yr)
                  
                  Then subtract Fixed OPEX (F1–F7) + sustaining capex (~$6–12M/yr):
                  → Real economic Net P&L → +$0 to +$8M/yr (central ~+$2–4M/yr)
                  → Consistent with a 32-year-operating cogen (survivorship check)
```

The rest of this doc walks each leg in detail, then proposes a Phase-K addition (MOR-replay mode) that helps validate the fixes, then ranks the work.

**Survivorship calibration**: Lockport has been operating continuously since 1992. Any reconciliation that produces a sustained-negative real Net P&L is failing the basic plausibility test that operating assets must, on average, cover their cash costs (or owners shut them down). All magnitudes below are calibrated to that constraint. See [`pnl_ledger.md §4.1`](./pnl_ledger.md) for the full discussion.

---

## §2. Leg 1 — LTSA cost values are placeholder

### §2.1 Current state

Every cost in the v1 LTSA stack comes from [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml), where **all 47 leaf values are `status: placeholder`** — copied from the Athens-prototype defaults (a 2-on-1 modern merchant CCGT, NYISO Zone F). Athens ≠ Lockport. The placeholder values are numerically valid (model runs) but not deal-realistic.

### §2.2 Annual breakdown — Mode A in v1

| Stream | v1 annual avg | v1 9-yr cumulative | What it represents |
|---|---:|---:|---|
| Fixed monthly fee | **$11.96M/yr** | $107.66M | $850K/month base × ~1.17 avg escalation |
| Start overage | $4.37M/yr | $39.36M | Cycling > baselines (placeholder rates) |
| HR penalty | $3.55M/yr | $31.94M | Cycle-end penalty at MI (one-time, amortized) |
| Forced outage owner-cost | $2.19M/yr | $19.75M | HRSG / BG repair events |
| MI events (owner share) | $1.55M/yr | $13.95M | The $10.5M MI bill (placeholder) |
| EOH reserve | $0.63M/yr | $5.71M | $175/EOH × delta EOH |
| Availability penalty | $0.06M/yr | $0.52M | Year-end true-up |
| CI events (owner share) | $0.00M/yr | $0.00M | No CI fired in 9 yr Mode A |
| **TOTAL** | **$24.32M/yr** | **$218.89M** | |

**Fixed monthly fee is half of total LTSA in Mode A.** It pays the same whether the plant runs or sits idle. **This is the single most important number to fix** — every other LTSA stream is conditional on dispatch/wear/events.

### §2.3 What we expect after data-room extraction

The Lockport data-room file `3.2.6.4 Lockport Trial Balances 2024-Feb 2026.xlsx` will surface real LTSA invoice line items. **Magnitudes for a 1992 cogen are likely materially below Athens's modern-merchant defaults.**

| Stream | v1 Athens placeholder (annual) | Plausible Lockport range (annual) | Annual delta |
|---|---:|---:|---:|
| Fixed monthly fee | $11.96M/yr | $3.0 – $5.0M/yr | **−$7 to −$9M/yr** |
| EOH reserve rate ($175/EOH) | $0.63M/yr | ~$0.4 – $0.6M/yr | −$0.0 to −$0.2M/yr |
| CI total cost | (no fires this run) | range TBD | event-conditional |
| MI total cost | $1.55M/yr amortized | $0.4 – $1.7M/yr amortized | −$0 to −$1.2M/yr |
| Start overage rates | $4.37M/yr | $0.5 – $3M/yr | −$1 to −$4M/yr |
| HRSG repair / BG repair | $2.19M/yr | $0.8 – $2.0M/yr | −$0.2 to −$1.4M/yr |
| **Combined annual shift** | | | **−$8 to −$15M/yr LTSA cost** |

**Net effect on annual Net P&L: +$8 to +$15M/yr improvement** from this leg alone (cost drops). The median plausible shift is around **+$11M/yr**.

**Why the fixed-fee range is lower than my earlier estimate**: a 1992 plant past its original CSA period has very likely renegotiated to a "supplemental services agreement" or reduced-scope CSA at materially lower fixed fee. Athens's $850K/month is a modern-merchant CSA rate; Lockport's effective fee is plausibly $250–400K/month. Survivorship calibration: the plant must be cash-positive on average over decades, which constrains how high real LTSA fixed fee can be.

### §2.4 What it takes to close the gap

1. Extract the trial-balance file → identify the 7 LTSA stream invoice categories
2. Cross-reference with the original PURPA contract filings (NYS PSC 1990–1992) for headline terms
3. Update `ltsa_terms.yaml` cells: change `status: placeholder` → `status: real_reported`; update `value`; cite the source
4. Rerun N4; the model_card's assumption-distribution improves from 80% real / 17.5% placeholder → ~95% real / ~0% placeholder

**Effort**: small once we have the data room file. The bottleneck is access + extraction time, not modeling work.

---

## §3. Leg 2 — Missing revenue streams

### §3.1 What v1 sees on the revenue side

**Only spark margin.** The model treats Lockport like a merchant power plant whose sole revenue is selling MWh into NYISO Zone A LMP. For Mode A in v1:

- Total spark over 9 yr = $15.81M
- **Annual avg spark = $1.76M/yr**
- Implied annual revenue: ~$10–13M/yr gross (before fuel + RGGI + VOM)

That implied revenue (~$11M/yr) is plausibly **a third or less of Lockport's total annual revenue**.

### §3.2 What real Lockport almost certainly also earns

| Revenue stream | What it is | v1 models | Plausible annual range |
|---|---|---|---:|
| **Cogen steam revenue** | The cogen host pays for process steam under DHTS | **No — $0 in v1** | $3 – $7M/yr |
| **NYISO ICAP capacity** | Reliability payment for being available; 200 MW UCAP × Zone A capacity price | **No — out of v1 per D4** | $5 – $9M/yr |
| **Ancillary services** | Regulation, spinning reserve, voltage support | **No** | $0.5 – $1.5M/yr |
| **PURPA avoided-cost** | Above-market PPA if original PURPA contract is still active | **No** | $0 – $5M/yr (contract status TBD) |
| **Combined missing revenue** | | | **$8 – $22M/yr** |

### §3.3 Annual shift from adding revenue streams

| Fix | Annual ↑ revenue | Difficulty |
|---|---:|---|
| Add NYISO ICAP capacity revenue | +$5 – $9M/yr | Small — UCAP capability is known; capacity prices are NYISO public data |
| Add cogen steam revenue (DHTS × steam tariff) | +$3 – $7M/yr | Medium — needs DHTS daily extraction + steam-tariff contract terms |
| Add ancillary services | +$0.5 – $1.5M/yr | Medium — needs NYISO settlement data |
| Add PURPA avoided-cost (if active) | +$0 – $5M/yr | Small if active; contract validation needed first |
| **Mid-range combined** | **+$10 – $18M/yr** | |

**Net effect on annual Net P&L: +$8 to +$22M/yr** from this leg alone (revenue grows). Median plausible shift around **+$13M/yr**.

### §3.4 Why this leg may be the biggest dollar-uplift

The fixed-fee LTSA correction (Leg 1) saves $8–15M/yr. Adding revenue streams (Leg 2) adds $8–22M/yr. **Leg 2 is comparable to or larger than Leg 1** at the annual level — and ICAP alone is plausibly the largest single line item we're missing.

The reason the v1 doc has emphasized Leg 1 first is that **the LTSA fix is mechanically easier** (just update YAML cells) than building a revenue-side model layer (requires DHTS extraction, capacity revenue logic, contract validation). But on dollar impact, they're comparable, and ICAP is plausibly the single largest line item we're missing.

### §3.5 What it takes to close the gap

| Stream | Path |
|---|---|
| Steam revenue | (a) extract DHTS from MOR per the documented v1 caveat; (b) get steam tariff from data room or PURPA contract; (c) add `steam_revenue.yaml` to asset config; (d) add to dispatch_day's revenue calc |
| ICAP | (a) determine Lockport's UCAP rating; (b) build NYISO Zone A capacity price time series; (c) add monthly capacity-revenue accrual to the daily loop |
| Ancillary services | Lower priority; could be a Phase L+ scope item |
| PURPA | Confirm contract status; if active, model as fixed $/MWh adder on dispatched MWh |

---

## §4. Leg 3 — Dispatch realism is missing

### §4.1 The MOR-observed reality check

v1 Mode A in 2024:

| Metric | MOR observed | v1 Mode A | Direction |
|---|---:|---:|---|
| Annual generation | 192,494 MWh | 468,331 MWh | **Model 2.4× too high** |
| Capacity factor (annual avg) | ~9.9% | ~14.6% | Model too high |
| 3xCC share of fired hours | 64.9% | 74.1% | Model favors 3xCC more |
| 2xCC share | 26.1% | **0.0%** | **Model never picks 2xCC** |
| 1xCC share | 8.9% | 25.9% | Model favors 1xCC more |
| Cold starts | ~7/yr | 14/yr | Model cycles too aggressively |

The model thinks the plant should run *more than twice as much as it actually does*.

### §4.2 Why — these are mechanics, not calibration knobs

The user is right to frame this as *missing model features*, not *calibration to MOR*. Seven real-world mechanics the model currently doesn't represent:

| Missing mechanic | What it would do | How to add |
|---|---|---|
| **Steam-only mode** (NEW — biggest miss) | ~25% of real Lockport days have steam delivery via duct burner / aux mechanism with 0 MWh and 0 EOH wear. v1 forces 1×CC dispatch on those days instead. | Add a third must-run branch: `if must_run AND uneconomic: pick between 1×CC and steam-only based on net cost`. Requires the steam-only mode's gas-to-steam efficiency (~45% from MOR) as a parameter. **Detail in [`dispatch_mechanics.md §6`](./dispatch_mechanics.md) and [`backtest_findings.md §3.4`](./extra/backtest_findings.md).** |
| **Planned outages** | Plant goes offline for maintenance windows (not just LTSA-driven CI/MI) | Add a planned-outage schedule extracted from MOR; daily loop respects it before dispatch |
| **Ramp constraints** | Real CCGT can't go from 0 → 221 MW in 1 hour; ramp limits constrain dispatch shape | Add per-operating-mode ramp rate (MW/min); dispatch optimization across an hour-block |
| **Dispatch derates** | Real plants run at < nameplate for many reasons (steam-host obligation reduces electric output; component degradation; emissions limits) | Add per-day derate factor (could be MOR-driven for backtest, distribution-driven for forward) |
| **Grid curtailment** | NYISO sometimes asks plants to back down (security-constrained dispatch) | Add curtailment probability + magnitude; small annual incidence |
| **Min-load enforcement** | 1×CC mode has a min-MW floor (can't dispatch at 30 MW if the floor is 60 MW) | Add `min_load_mw` per operating mode to engineering.yaml |
| **2×CC emergence from single-CT-down** | When one CT is out (maintenance or forced), the block runs as 2×CC, not as 1×CC | Requires per-generator state (v2) |

### §4.3 Annual shift from adding dispatch realism (updated with MOR backtest)

The May 2026 backtest in [`backtest_findings.md §4`](./extra/backtest_findings.md) revised these numbers using 5 years of MOR ground-truth data. The headline: **v1 Mode A over-commits 2.22×** (417 GWh/yr modeled vs 188 GWh/yr MOR).

Cutting modeled fired hours by ~55% to match MOR (driven mostly by steam-only-mode adoption + planned outages), the dispatch-driven LTSA streams drop proportionally:

| Stream | v1 annual (Mode A) | After dispatch realism | Annual shift |
|---|---:|---:|---:|
| Start overage | $4.37M/yr | $2.0M/yr (fewer starts) | −$2.4M/yr |
| EOH reserve | $0.63M/yr | $0.30M/yr | −$0.3M/yr |
| HR penalty | $3.55M/yr | $1.5M/yr (slower HR drift) | −$2.0M/yr |
| Forced outage owner-cost | $2.19M/yr | $1.0M/yr (less stress → fewer events) | −$1.2M/yr |
| **Subtotal LTSA reduction** | | | **−$6 to $7M/yr LTSA cost** |
| Spark margin lost | $1.76M/yr | $0.80M/yr (fewer dispatch hours) | **−$1.0M/yr revenue** |
| **Net annual shift** | | | **+$5M/yr** |

The dispatch realism fix is now **slightly bigger** than the earlier estimate (+$3-5M/yr) because the over-commit was bigger than originally thought. But still smaller dollar impact than Legs 1 or 2. Importantly, it's the fix that **builds model trust** — without it, all downstream analyses inherit the 2.22× over-commit.

### §4.4 What it takes to close the gap

Phase K work, after the notebooks graduate to `src/`:

1. **Planned outages**: parse MOR planned-outage entries; build a per-asset planned-outage parquet; daily loop checks before dispatch
2. **Min-load floors**: add `min_load_mw_by_mode` to `engineering.yaml`; dispatch enforces `mw_dispatched >= min_load OR mw_dispatched = 0`
3. **Ramp constraints**: add `ramp_up_mw_per_min`, `ramp_down_mw_per_min` per mode; dispatch optimization respects adjacency
4. **Dispatch derates**: distribution sampled per-day (e.g., DHTS-load-correlated derate)
5. **Grid curtailment**: low-probability per-day event with small magnitude; tracked separately

---

## §5. The MOR-replay mode (Phase K proposal)

A fourth mode alongside A/B/C: **"Mode M" — replay MOR-observed dispatch exactly and accrue LTSA against it.**

```python
mode = "M"  # MOR replay
# Skip the spark optimization; use the observed dispatch directly
mode_per_hour = mor_observed_dispatch.loc[day]   # ["3xCC", "1xCC", "offline", ...]
# Run the LTSA / state / forced-outage machinery as normal
```

### §5.1 Why this is valuable

Three big payoffs:

1. **Diligence-relevant question**: "Given the real 2024 dispatch and given the (eventually real) LTSA contract, what should the 2024 LTSA bill have been?" — that's directly answerable with Mode M. Diligence buyers can compare to the actual LTSA invoices in the data room and validate the model.

2. **Decouples dispatch error from LTSA error**: today, the −$203M Net P&L is the product of bad LTSA values *and* over-committed dispatch *and* missing revenue. Mode M fixes the dispatch leg by construction → isolates the LTSA + revenue gaps cleanly.

3. **Backtest sanity check**: if Mode M with real LTSA values reproduces the 2024 LTSA invoice within reasonable error, the model is validated. If it doesn't, we know where to look (which stream is off?).

### §5.2 What it requires

| Need | Source |
|---|---|
| MOR-observed dispatch by day or by hour | EIA MOR (monthly); or NYISO real-time settlement (hourly) |
| 4 modes × 9 years extends the run-time | Should still run in <2 min |
| Plumbing: a `mode == "M"` branch in `run_mode()` | Small code change in N4 + Phase K refactor |

### §5.3 Where it fits in the priority order

After Leg 1 (data-room LTSA), Mode M becomes the **single most useful diagnostic** because it shows what the model thinks LTSA *should* have been on real dispatch. Before Leg 1, Mode M shows what *Athens-LTSA* says LTSA should have been — less useful, but still a structure validation.

Recommendation: build Mode M as part of Phase K refactor, ready to consume real LTSA values as soon as they land.

---

## §6. Priority order — what to fix first

The matrix below ranks by **annual Net P&L impact × effort × signal quality**:

| Priority | Fix | Annual Net P&L shift | Effort | Why this order |
|---|---|---:|---|---|
| **1** | **Data-room LTSA extraction** (Leg 1) | +$8 to +$15M/yr | Low (just update YAML) | Single largest-impact mechanical change. Removes the dominant placeholder. Unblocks Mode M validation. |
| **2** | **Add NYISO ICAP revenue** (Leg 2, part) | +$5 to +$9M/yr | Low–Medium (capacity price spine + UCAP rating) | Largest individual revenue gap. Public data. Easy to add. |
| **3** | **MOR-replay mode (Mode M)** + Phase K refactor | $0 direct, but validates everything | Medium (refactor notebooks → `src/`; add Mode M flag) | Diagnostic for validating Legs 1 and 2 against real plant invoices. |
| **4** | **Add cogen steam revenue** (Leg 2, part) | +$3 to +$7M/yr | Medium (DHTS extraction + steam tariff) | Cogen's reason for existing; major v1 gap; harder data lift. |
| **5** | **Dispatch realism** (Leg 3) — planned outages, ramp, derates | +$3 to +$5M/yr | Medium (new mechanics in dispatch logic) | Smaller dollar impact than Legs 1/2 but important for model trust. |
| **6** | **Add Fixed OPEX layer** (F1–F7 from [`pnl_ledger.md`](./pnl_ledger.md)) | −$6 to −$12M/yr | Medium (new YAML + cost layer) | Brings the "improved" Net P&L down to real cash economics. Must be modeled before any investor-grade output. |
| **7** | **Phase L Monte Carlo** | Uncertainty bands, not point shift | Medium–High (orchestration layer) | Quantifies single-path noise; sweeps Bucket B Athens constants. |
| **8** | **Per-asset Bucket B calibration** | Tightens uncertainty | High (long tail of engineering parameter learning) | Replaces Athens defaults with Lockport-calibrated state-evolution constants. **Process planned in [`docs/plans/parameter_calibration_plan.md`](../plans/parameter_calibration_plan.md)** (sensitivity-rank → tiered defensibility → provenance register; pre-v2, partly data-gated). |
| **9** | **Per-generator state** (v2 architecture) | Unlocks 2xCC emergence + single-CT-down | High (state-vector rework) | The piece that fixes the 0% 2xCC backtest divergence. |
| **10** | **Heat-rate vs ambient temperature** | Small (a few % HR drift in hot months → modest spark margin shift) | Low–Medium (add `temp_f` arg to `hr_clean_for_mode` + a curve from EIA-860 / vendor specs) | Capacity already derates with ambient (`ambient_derate_factor`), and ambient already drives hot-section wear (ADR-006). But heat rate itself is currently **mode-only** — it does NOT vary with ambient. Real GTs degrade HR ~0.5%/°C in hot weather. Surfaced 2026-05-28 while reviewing the load-temp paper (Saturday & Isaiah 2018), which handles this implicitly via PYTHIA gas-path recomputation. Small structural gap, not a Stream A item. |

### §6.1 What "done" looks like at priority 1+2 only

Just doing **#1 (real LTSA)** + **#2 (NYISO ICAP)** in isolation should produce a model_card where:

- LTSA owner-uncovered drops by **~$8–15M/yr** (Mode A: $24.32M/yr → ~$10–16M/yr)
- Revenue grows by **~$5–9M/yr** (Mode A spark stays at ~$1.76M/yr but adds $7M/yr ICAP → ~$9M/yr total revenue)
- **Net P&L moves from −$22.6M/yr → roughly +$0 to +$15M/yr** depending on real values

That's a plausibly positive operating-Net-P&L within reach of two well-scoped fixes. After step #6 (Fixed OPEX layer) the number lands at the real-cash-economics level — **central tendency +$2 to +$4M/yr**, consistent with the survivorship-bias reality that the plant has been operating profitably since 1992.

Worth doing before Phase L Monte Carlo (which is more about quantifying uncertainty around a sensible point estimate than about getting to a sensible point estimate in the first place).

---

## §7. Why annual, not 9-year

Throughout this doc the primary unit is **dollars per year, not dollars per 9-year window**. Three reasons:

1. **Annual is the unit of plant operation.** Budgets, capacity contracts, MOR filings, LTSA escalation, RGGI auctions, ICAP commitments — all annual. The plant operator thinks in years, the contract pays in months, no one thinks in 9-year totals.

2. **9-year totals can hide year-to-year variance.** A −$203M 9-yr total could be uniformly bad (−$23M every year) or could mask one catastrophic year and 8 break-even years. Annual reveals the shape:

   ```
   Mode A annual net P&L (rough; from the daily summaries):
   2017  −$22M    | typical year
   2018  −$21M    | typical
   2019  −$20M    | typical
   2020  −$24M    | gas dipped → spark dropped
   2021  −$22M    | typical
   2022  −$18M    | high LMP year (gas spike but spark margins higher)
   2023  −$24M    | typical
   2024  −$22M    | typical
   2025  −$26M    | MI fired → +$14M MI cost + $32M HR penalty all in 2025
   ```
   The 2025 spike is invisible at 9-year scale but tells you something important: inspection events are lumpy and lumpy years dominate the average. (Numbers above are approximate from the parquets; check the run bundle for exact values.)

3. **The plausible-magnitude logic naturally works in annual terms.** ICAP is paid monthly. Fixed fee is monthly. Steam revenue is daily/monthly. Forced outage events are daily-probability. When you scale these to "9-year totals," you're hiding the underlying time scale that makes the assumption sane.

The recommendation going forward: **model_card and dashboards should lead with annual averages + standard deviations across years, with 9-year totals as derivations for cumulative-context only.**

This is a small change to N4's output that's worth doing in Phase K: add `mean_annual` and `std_annual` for every cumulative-stream column. Cross-ref: cookbook task for when Phase K starts.

---

## §8. Current v1 numbers reframed annually

For ease of cross-reference, here's the Mode A 9-year run reframed at annual grain:

### Annual averages (Mode A, seed=42)

| Metric | 9-yr total | Annual avg | Notes |
|---|---:|---:|---|
| Generation | 2,555,147 MWh | 283,905 MWh/yr | (MOR 2024 = 192K; model over-commits) |
| Fired hours | 18,552 | 2,061/yr | |
| Capacity factor | — | ~14.6%/yr | (MOR 2024 = 9.9%) |
| Total starts | 827 | 92/yr | |
| Cold starts | 129 | 14.3/yr | (MOR ~7/yr) |
| **Spark margin** | $15.81M | **$1.76M/yr** | Electricity revenue only |
| **LTSA owner-uncovered** | $218.89M | **$24.32M/yr** | Of which fixed fee = $11.96M/yr |
| **Net P&L** | −$203.1M | **−$22.6M/yr** | The headline number |
| Inspections | 1 (MI) | 0.11/yr | (Lumpy: 8 yrs at 0, 1 yr at 1) |
| Forced outages | 35 | 3.9/yr | |

### Annual avg, all modes

| Mode | Spark $/yr | LTSA $/yr | Net P&L $/yr |
|---|---:|---:|---:|
| A | $1.76M | $24.32M | **−$22.57M** |
| B | $0.88M | $24.55M | **−$23.68M** |
| C | $1.12M | $24.49M | **−$23.37M** |

Mode A wins Net P&L by ~$0.8M–1.1M/yr. The mode-comparison delta is small relative to the leg-fix shifts above (each leg moves Net P&L by $4–14M/yr). **The interesting decisions are about the gaps, not the mode policy at v1's CF level.**

---

## §9. Cross-reference

| Concept | Where |
|---|---|
| Three legs framing (LTSA / revenue / dispatch) | This doc §1 |
| LTSA placeholder details | This doc §2, [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml), [ADR-001](../decisions/001-gas-hub-treatment-v1.md) |
| Missing revenue streams | This doc §3, [architecture.md §6.4.1](./architecture.md), [`caveats.md`](../../data/assets/lockport/caveats.md) §3 (DHTS) |
| Dispatch realism gaps | This doc §4, [architecture.md §7.3, §7.4](./architecture.md) |
| MOR-replay mode proposal | This doc §5 (new in this doc) |
| Phase K (graduate to `src/`) | [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) §8 Phase K |
| Phase L (Monte Carlo) | [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) §8 Phase L |
| Annual vs 9-year framing | This doc §7 |
| MOR (Monthly Operating Report) | [`glossary.md`](./glossary.md) §7 |
| ADRs | [`../decisions/README.md`](../decisions/README.md) |
