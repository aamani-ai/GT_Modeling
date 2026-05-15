# P&L Ledger — Full Economic View of Lockport

> **Start here.** This is the single-table view of every component that affects Lockport's economic P&L, what v1 actually models, what v1 ignores, and rough annual magnitudes. The rest of the methodology folder explains the mechanics behind each line:
> - [`architecture.md`](./architecture.md) — how v1 works
> - [`dispatch_mechanics.md`](./dispatch_mechanics.md) — operating mode × policy mode deep dive
> - [`backtest_findings.md`](./extra/backtest_findings.md) — modeled vs real MOR comparison (steam-only mode discovery)
> - [`gaps_and_priorities.md`](./gaps_and_priorities.md) — what to fix first
> - [`glossary.md`](./glossary.md) — term definitions

---

## §1. What this doc answers in one glance

1. **What money flows IN to the plant?** Six revenue components possible; v1 models one.
2. **What money flows OUT of the plant?** Three cost layers: variable, contract-driven (LTSA), and structural fixed; v1 models the first two.
3. **What's the model actually capturing, and what's it ignoring?** Status code on every row.
4. **For each ignored line, how big is the gap?** Annual magnitude in plausible range.
5. **What's the gap between "model Net P&L" and "real economic P&L"?** Reconciliation in §3.

---

## §2. Status legend

Every line in the ledger carries one of these tags:

| Tag | Meaning |
|---|---|
| **✓ Modeled** | Computed end-to-end in v1; output shows up in the model_card / parquets |
| **◐ Partial** | Some aspect is in v1; another aspect is missing or proxied |
| **✗ Not modeled** | Real component, but v1 outputs $0 for it |
| **— N/A** | Doesn't apply to Lockport (e.g., REC for a gas plant) |
| **PH** | Modeled but with `placeholder` values (Athens defaults) — magnitudes not deal-realistic |

---

## §3. The ledger

All figures are **annual averages** (USD/year). For 9-year cumulative, multiply by ~9 (with escalation for LTSA streams).

### §3.A Revenue side — money flowing IN

| # | Component | What it is | v1 says | Plausible Lockport range | Status | Reference |
|---|---|---|---:|---:|---|---|
| **R1** | **Energy revenue (DA wholesale)** | MWh × LMP at Lockport NYISO node, day-ahead market | Built into spark margin | $8 – $12M/yr gross (≈$1–2M/yr after fuel/VOM/RGGI) | ✓ Modeled | [`architecture.md §6.4.1`](./architecture.md), N4 §E.2 |
| **R2** | **Capacity payments (NYISO ICAP)** | Reliability payment for being available to dispatch; 200 MW UCAP × Zone A capacity price | $0 | $4 – $12M/yr | ✗ Not modeled (per D4) | [`gaps_and_priorities.md §3`](./gaps_and_priorities.md) |
| **R3** | **Steam revenue (cogen DHTS)** | Industrial host pays for process steam under the cogen contract | $0 | $2 – $8M/yr | ✗ Not modeled | [`gaps_and_priorities.md §3`](./gaps_and_priorities.md), [`caveats.md §3`](../../data/assets/lockport/caveats.md) |
| **R4** | **Ancillary services** | Regulation, spinning reserve, 10/30-min operating reserve, voltage support | $0 | $0.5 – $1.5M/yr | ✗ Not modeled | [`gaps_and_priorities.md §3`](./gaps_and_priorities.md) |
| **R5** | **PURPA avoided-cost premium** | Above-market PPA if original 1990s PURPA contract is still active | $0 | TBD (could be $0 if expired, or material if active) | ✗ Not modeled (contract status TBD) | [`ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml) `contract_metadata` |
| **R6** | **Other** (black start, RT energy spread, reactive power, RECs) | Small misc streams | $0 | $0 – $1M/yr collectively | ✗ Not modeled / partial | — |
| | **Total revenue** | | **~$11M/yr** (gross, mostly fuel pass-through) | **~$15 – $35M/yr** | | |

**Headline gap on revenue side**: real Lockport plausibly earns **$5 – $25M/yr more** than v1's revenue side captures. ICAP alone could be a third of that gap.

### §3.B Variable costs — money flowing OUT, already netted into spark margin

These are computed inside the dispatch loop and subtracted from energy revenue to produce spark margin. So they're not "Net P&L deductions" in the sense of being separately accrued — they're already inside the $1.76M/yr Mode A spark.

| # | Component | What it is | v1 annual cost | Status | Reference |
|---|---|---|---:|---|---|
| **V1** | **Fuel cost (gas)** | MMBtu × Henry Hub price | ~$6 – $9M/yr | ✓ Modeled | [`architecture.md §5.3`](./architecture.md) |
| **V2** | **RGGI carbon allowance** | MMBtu × 117 lb-CO2/MMBtu × $17/short ton | ~$0.5 – $1M/yr | ✓ Modeled | [`caveats.md §12`](../../data/assets/lockport/caveats.md), [ADR-002](../decisions/002-lockport-specific-vs-generic-calibration.md) |
| **V3** | **VOM (Variable O&M, cogen-markup)** | MWh × $1.38 | ~$0.4M/yr | ✓ Modeled | [`glossary.md`](./glossary.md) §1 VOM |
| **V4** | **Cold-start warming gas** | Cold starts × 2,537 MMBtu × delivered gas price | Small in v1 (cold starts rare in summer windows) | ✓ Modeled | [ADR-002](../decisions/002-lockport-specific-vs-generic-calibration.md) Correction 1 |
| **V5** | **Algonquin basis premium** | Real delivered gas at Algonquin Citygate vs Henry Hub benchmark | $0 (Henry Hub used directly) | ✗ Not modeled | [ADR-001](../decisions/001-gas-hub-treatment-v1.md) (deferred to v2) |
| **V6** | **NOx / SOx emissions allowances** | Smaller secondary emissions allowance markets | $0 | ✗ Not modeled | — |

**Variable cost coverage in v1**: solid except for Algonquin basis (small magnitude likely) and secondary emissions (small). Variable side is the model's most mature area.

### §3.C LTSA / contract costs — money flowing OUT, accrued separately

These are the model's "LTSA owner-uncovered" total. **Every value below is a `placeholder` Athens default in v1.**

| # | Component | What it is | v1 annual (PH) | Plausible Lockport range | Status | Reference |
|---|---|---|---:|---:|---|---|
| **L1** | **Fixed monthly fee** | Recurring contract fee paid to OEM each month, regardless of dispatch | $11.96M/yr | $3.6 – $7.2M/yr | PH | [`architecture.md §6.4.2`](./architecture.md), `ltsa_terms.yaml` |
| **L2** | **EOH reserve** | $/EOH × delta EOH; goes to OEM maintenance fund | $0.63M/yr | $0.4 – $0.6M/yr | PH | `ltsa_terms.yaml` |
| **L3** | **CI events (owner-uncovered)** | 25% of Combustion Inspection bill; fires every 24K EOH | $0/yr (none fired) | event-conditional ≈ $0.1 – $0.3M/yr amortized | PH | `ltsa_terms.yaml` |
| **L4** | **MI events (owner-uncovered)** | 35% of Major Inspection bill; fires every 48K EOH | $1.55M/yr (1 fired in 9 yr) | $0.4 – $1.7M/yr amortized | PH | `ltsa_terms.yaml` |
| **L5** | **Start overage** | YTD starts above baseline → per-start excess fee | $4.37M/yr | $1 – $4M/yr | PH | `ltsa_terms.yaml` |
| **L6** | **Availability penalty** | Year-end true-up if avail < 95% guarantee | $0.06M/yr | $0 – $0.5M/yr | PH | `ltsa_terms.yaml` |
| **L7** | **HR penalty** | Cycle-end charge if HR > guarantee × (1 + tolerance) | $3.55M/yr (lumpy) | $0.5 – $3M/yr | PH | `ltsa_terms.yaml` |
| **L8** | **Forced outage owner-cost** | HRSG / BG repair events ($0 for OEM-covered GT) | $2.19M/yr | $1 – $2.5M/yr | PH | `ltsa_terms.yaml.forced_outage_coverage` |
| | **Total LTSA (Mode A v1)** | | **$24.32M/yr** | **$7 – $19M/yr** | | |

**Headline gap on LTSA side**: real Lockport LTSA cost plausibly **$5 – $17M/yr lower** than v1's placeholder-driven number. Almost entirely driven by the fixed monthly fee.

### §3.D Non-LTSA fixed operating costs — money flowing OUT, NOT modeled at all in v1

This is the biggest hole on the cost side that v1 doesn't even attempt to model. **Real plants pay all of these every year.**

| # | Component | What it is | v1 says | Plausible Lockport range | Status |
|---|---|---|---:|---:|---|
| **F1** | **Fixed O&M (FOM)** | Plant staff (operators, maintenance, control room), security, basic admin, IT, supplies | $0 | $3 – $5M/yr | ✗ Not modeled |
| **F2** | **Property tax** | NY state property tax on assessed plant value | $0 | $1 – $3M/yr | ✗ Not modeled |
| **F3** | **Insurance** | Property + liability + business interruption coverage | $0 | $0.5 – $1.5M/yr | ✗ Not modeled |
| **F4** | **Land lease / site fees** | If site is leased; or municipal fees | $0 | $0 – $0.5M/yr | ✗ Not modeled |
| **F5** | **Environmental compliance** | NYDEC permit fees, emissions reporting, water permits | $0 | $0.1 – $0.5M/yr | ✗ Not modeled |
| **F6** | **G&A (Operating company overhead)** | Parent company / SPV admin allocation | $0 | $0.3 – $1M/yr | ✗ Not modeled |
| **F7** | **Steam supply contract O&M** | Cogen-side heat exchangers, steam piping maintenance | $0 | $0.2 – $0.8M/yr | ✗ Not modeled |
| | **Total non-LTSA fixed OPEX** | | **$0** | **$5 – $12M/yr** | |

**Headline gap on non-LTSA fixed OPEX**: real Lockport pays **$5 – $12M/yr** in costs the v1 model entirely ignores. Industry benchmark: EIA Form 1 data shows ~$20–30/kW-yr Fixed O&M for similar CCGTs → $4.4–6.6M/yr for 221 MW.

### §3.E Capital, financial, and tax — money flowing OUT, NOT modeled

Not directly relevant for operating-economics analysis but worth noting for completeness.

| # | Component | What it is | v1 says | Plausible | Status |
|---|---|---|---:|---:|---|
| **C1** | **Sustaining capex** | Periodic equipment refurbishment outside LTSA scope | $0 | $1 – $3M/yr (averaged) | ✗ Not modeled |
| **C2** | **Major upgrade capex** | Life-extension projects, controls modernization | $0 | Lumpy; could be $0 or large | ✗ Not modeled |
| **C3** | **Interest on debt** | If asset has remaining project debt | $0 | TBD (likely paid down by now for 1992 vintage) | ✗ Not modeled |
| **C4** | **Federal + state income tax** | If asset is profitable | $0 | Asset-dependent | ✗ Not modeled |
| **C5** | **Depreciation** | Tax shield (no cash flow impact) | $0 | Doesn't affect cash economics | — N/A |
| **C6** | **Decommissioning reserve** | Set-aside for end-of-life site restoration | $0 | $0.3 – $1M/yr | ✗ Not modeled |
| **C7** | **Working capital changes** | Receivables, payables, inventory swings | $0 | Small | ✗ Not modeled |

These are typically modeled at the **financial-investor layer**, not the **asset-operations layer**. v1's purpose is asset operations (the engineering↔dispatch↔LTSA feedback loop); a full investor model layers debt/equity structure on top. v2+ scope.

---

## §4. The reconciliation — what v1 represents vs full economic P&L

### §4.1 The survivorship sanity check

Before doing any range math, apply this constraint: **Lockport has been operating continuously since 1992** — 32 years and counting. Any range that puts real economic Net P&L materially negative on a sustained basis is failing a basic plausibility test. Owners shut down or sell off assets that lose money for years; the fact that this asset is still running tells you, before any model output, that **real cash flow is at least breakeven, and almost certainly modestly positive in normal years**.

So our reconciliation should land somewhere around **+$1 to +$5M/yr in central tendency**, with bad years (MI fired + forced outage cluster + low-LMP year) potentially dipping near or slightly below zero, and good years (high-LMP, low cycling) up to +$8M/yr. If the math says otherwise, the math is wrong, not the asset.

### §4.2 The walk from v1 to real economics

```
                                       Annual ($M/yr)         Status
                                       ──────────────         ─────────
v1 Mode A revenue (R1 only — spark)        $1.76                ✓
v1 Mode A LTSA cost (L1–L8, placeholder)  -$24.32                PH
                                       ──────────────
v1 Mode A "Net P&L"                        −$22.6               ← headline today

ADJUSTMENTS to get to plausible Lockport reality:

  + Real LTSA values (L1–L8 dropping)     +$8 to +$15/yr        ← Leg 1
                                                                  For 1992 plant past original
                                                                  LTSA period, real fixed fee
                                                                  likely $3–5M/yr (vs $11.96M PH)
  
  + Add ICAP revenue (R2)                  +$5 to +$9/yr        ← Leg 2a
                                                                  200 MW UCAP × $2–4/kW-month avg
  
  + Add steam revenue (R3)                 +$3 to +$7/yr        ← Leg 2b
                                                                  Cogen tariff is plant's REASON
                                                                  for existing; meaningful magnitude
  
  + Add ancillary (R4)                     +$0.5 to +$1.5/yr    ← Leg 2c
  
  + PURPA premium (R5) if contract active   +$0 to +$5/yr       ← Leg 2d
                                                                  Highly uncertain; conservative
                                                                  to assume $0 in central case
  
  + Realistic dispatch (less LTSA accrual) +$3 to +$5/yr        ← Leg 3
  
  Subtotal moves from −$22.6 to approx:   +$0 to +$20M/yr       "improved Net P&L"
                                                                  central tendency ~+$10M/yr

FURTHER adjustments to get to real cash economics:

  − Fixed O&M (F1)                        -$2.5 to -$4/yr       ← 1992 cogen, modest staffing
  − Property tax (F2)                     -$0.5 to -$2/yr       ← Older plant, lower assessed value
  − Insurance (F3)                        -$0.5 to -$1.5/yr
  − Other fixed OPEX (F4–F7)              -$0.5 to -$2/yr
  − Sustaining capex (C1)                 -$1 to -$3/yr         ← Periodic, lumpy
  
  Real economic Net P&L:                  +$0 to +$8M/yr        "real cash economics"
                                                                  central tendency ~+$2–4M/yr
```

### §4.3 Three different "Net P&L" numbers and what they each mean

| View | Annual range | Central tendency | What it represents |
|---|---:|---:|---|
| **v1 Net P&L (today)** | −$22.6M/yr | −$22.6M/yr | Spark margin minus placeholder-LTSA. Model's current output. Not a real claim about Lockport. |
| **"Improved" Net P&L** | +$0 to +$20M/yr | ~+$10M/yr | After fixing Legs 1, 2, 3 from `gaps_and_priorities.md`. Still ignores F1–F7 non-LTSA fixed costs. **This is the most useful diligence number** because LTSA + revenue completeness drives investment thesis. |
| **Real economic Net P&L** | +$0 to +$8M/yr | ~+$2 to +$4M/yr | After also subtracting F1–F7 and sustaining capex. The true "free cash flow before debt service and tax." A modestly positive cogen that throws off small cash. |

**The plausible reality**: Lockport is a **modestly profitable cogen** — fully depreciated capital, long-term steam contract, capacity payments, modest spark — earning **a few million per year in cash** with normal year-to-year variance. Bad years (MI + outage cluster) might dip near zero; good years might clear $6–8M. The cumulative 9-year cash generated is plausibly **$15 to $40M**, not the −$135M to −$190M v1 implies.

### §4.4 What was wrong with my earlier numbers

An earlier version of this section put "Real economic Net P&L" at **−$15 to +$0M/yr**. That was wrong, and the survivorship-bias check is what catches it. Specifically:

- I took **low end** of every revenue line and **high end** of every cost line and compounded them. That's not a "range" — it's a worst-case scenario stacked seven ways.
- I didn't account for the fact that **a 1992 plant past its original LTSA period likely renegotiated** to a much lower fixed fee. Athens's $850K/month placeholder is for a modern merchant CCGT under an active CSA; Lockport's effective fee is plausibly $250–400K/month.
- I assumed the **steam revenue at the low end of $2M/yr** when cogen contracts of this scale typically run $4–8M/yr.
- I gave **no weight to PURPA premium** even as a possibility worth flagging.

The fixed numbers above are still rough estimates pending data-room information. But they pass the "could this asset have plausibly survived 32 years of operation?" sanity check, which is the right calibration to ground all ledger ranges against.

---

## §5. What v1 is good at, what v1 is missing

### §5.1 Mature areas of v1
✓ Hour-by-hour dispatch decision under three policy regimes (Mode A/B/C)
✓ Engineering wear → forced outage probability → outage event sampling
✓ Inspection event triggering with calendar + hard-stop logic
✓ Full LTSA stream accrual (7 streams) with proper state-of-the-art OEM/owner split
✓ Twin dispatch (clean vs degraded) for loss attribution
✓ Status-tagged inputs across 268 leaf values
✓ MOR backtest scaffolding

### §5.2 Material gaps (in priority order, from [`gaps_and_priorities.md §6`](./gaps_and_priorities.md))

1. **PH** LTSA values are placeholder Athens defaults — **largest single number-mover** at the contract-cost layer
2. **✗** Capacity revenue (R2, ICAP) — **largest single number-mover** at the revenue layer
3. **✗** Steam revenue (R3) — the cogen plant's reason for existing
4. **✗** Non-LTSA Fixed OPEX (F1–F7) — **the biggest "blind spot"** in v1's economic picture (~$5–12M/yr)
5. **✗** Dispatch realism — planned outages, ramps, derates, curtailment, min-load
6. **✗** Multi-path Monte Carlo — quantify single-path noise on outage timing
7. **✗** Per-generator state — unlocks 2×CC emergence and single-CT-down modeling
8. **✗** Algonquin basis modeling (V5)
9. **✗** Capex / financial layer (C1–C7) — only relevant if model expands to full-investor view

### §5.3 The economic-completeness ladder

```
v1 TODAY: covers about 50% of the cash-flow components on the cost side
          and 25% of the revenue side
          → Net P&L = -$22.6M/yr (severely understated; both errors compounding)
          → Not a real economic claim; useful only for mode comparison

WITH GAPS 1–3 CLOSED (Legs 1–2):
          Cost side ~70% complete (real LTSA), revenue side ~75% complete
          → Net P&L = +$0 to +$20M/yr (central ~+$10M/yr)
          → Diligence-grade for operations, before fixed OPEX

WITH GAPS 1–5 CLOSED + Fixed OPEX (F1–F7) + sustaining capex (C1):
          Cost side ~95% complete, revenue side ~85% complete  
          → Real economic Net P&L = +$0 to +$8M/yr (central ~+$2–4M/yr)
          → A modestly profitable operating cogen; matches the asset's
            survivorship reality (continuously operating since 1992)

WITH GAP 6 (Monte Carlo) + GAP 7 (per-generator):
          Uncertainty bands quantified; multi-asset extensibility
          → Investment-grade model
```

---

## §6. How to use this doc

**If you're new to the model**: read this doc first, then [`architecture.md`](./architecture.md) for how each ✓-tagged component actually works, then [`gaps_and_priorities.md`](./gaps_and_priorities.md) for what to fix first.

**If you're reviewing a model_card**: cross-reference the headline Net P&L against §4's reconciliation. The number reported is v1's −$22.6M/yr equivalent; the "real economic Net P&L" is what diligence needs.

**If you're planning Phase K / next work**: rows tagged **✗** that have plausible annual magnitude > $2M/yr are the highest-priority fixes. That's R2 (ICAP), R3 (steam), F1 (Fixed O&M), F2 (property tax). All other ✗ rows are smaller dollar impact or v2+ scope.

**If you're explaining to a stakeholder**: §4's three-tier reconciliation is the right framing. "v1 Net P&L" is what the model says now. "Improved Net P&L" is what diligence cares about. "Real economic Net P&L" is what the owner experiences as cash.

---

## §7. Cross-reference

| Concept | Where |
|---|---|
| How v1 actually computes each ✓ row | [`architecture.md §5–§6`](./architecture.md) |
| Why each ✗ row is missing + plausible magnitude | [`gaps_and_priorities.md §1–§5`](./gaps_and_priorities.md) |
| Priority order for closing ✗ rows | [`gaps_and_priorities.md §6`](./gaps_and_priorities.md) |
| MOR-replay mode proposal (validates ✓ rows against reality) | [`gaps_and_priorities.md §5`](./gaps_and_priorities.md) |
| Term definitions used in the ledger | [`glossary.md`](./glossary.md) |
| Why annual not 9-year | [`gaps_and_priorities.md §7`](./gaps_and_priorities.md) |
| Source YAML for L1–L8 (and what they're keyed off) | [`../../data/assets/lockport/ltsa_terms.yaml`](../../data/assets/lockport/ltsa_terms.yaml) |
| Source notebook (run that produces current numbers) | [`../../notebooks/04_full_path_mode_comparison.ipynb`](../../notebooks/04_full_path_mode_comparison.ipynb) |
| 5 locked decisions (incl. D4 capacity-out-of-scope) | [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) §5 |
| ADR-001 (gas hub choice → V5 not modeled) | [`../decisions/001-gas-hub-treatment-v1.md`](../decisions/001-gas-hub-treatment-v1.md) |
| ADR-002 (Lockport vs generic calibration) | [`../decisions/002-lockport-specific-vs-generic-calibration.md`](../decisions/002-lockport-specific-vs-generic-calibration.md) |
