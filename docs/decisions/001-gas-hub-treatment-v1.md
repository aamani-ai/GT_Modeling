# ADR 001: Gas hub treatment for v1 dispatch model

**Status**: Accepted
**Date**: 2026-05-14
**Decision-maker(s)**: divy + Claude (in conversation during Phase G execution)
**Affects**: Phase H (Notebook 2 — one day of dispatch) and forward; `market_context.yaml.gas_market`; the model_card content for any v1 Lockport run

---

## Context

Notebook 1 surfaced an unexpected gap in the gas price data: the `gas_price_history.parquet` copied from model-gpr has 8 hubs, but only **Henry Hub** has deep coverage (1997-04-07 → 2026-04-20, 8,303 rows). Every other hub — including **Algonquin Citygate**, which is the NYISO-relevant delivery hub for Lockport — has only **2014-03-17 → 2017-12-28** (~698-950 rows, ~4 years).

Per-hub coverage (from Notebook 1 §F output):

| Hub | Rows | Date range |
|---|---|---|
| Henry Hub | 8,303 | 1997-01-07 → 2026-04-20 |
| Algonquin Citygate (Lockport-relevant) | 698 | 2014-03-17 → 2017-12-28 |
| Chicago Citygate | 950 | 2014-03-17 → 2017-12-28 |
| Malin / PG&E / SoCal × 2 / TETCO-M3 | ~950 each | 2014-03-17 → 2017-12-28 |

The Step 1 plan's delivered-gas formula assumes a basis layer on top of Henry Hub:

```
delivered_gas = Henry_Hub_forward + delivery_basis_month + historical_daily_shape
```

But the basis layer for Northeast US delivery (which Lockport needs) is post-2017 empty in our data.

This forces a decision before Notebook 2's gross-margin proxy can compute fuel cost.

### Why this matters specifically for Lockport

Lockport is a 1992 PURPA-era CCGT cogen with **dual-fuel switching capability** (gas ↔ DFO, 1-hour switch time, storage- and air-permit-limited). The dual-fuel exists because Northeast US gas prices spike during winter pipeline-constraint events (most famously the January 2014 polar vortex, which saw Algonquin Citygate spot >$100/MMBtu while Henry Hub stayed under $7).

The economic mechanism:

```
switch from gas to oil when:
  delivered_gas_$/MMBtu  >  delivered_oil_$/MMBtu  ×  heat_rate_penalty_on_oil
```

Roughly, DFO delivered at ~$15-25/MMBtu × 1.05-1.08 heat-rate penalty = oil-switching threshold around $14-22/MMBtu delivered gas.

- **Henry Hub**: never crosses that threshold (winter peak ~$7-10/MMBtu).
- **Algonquin Citygate**: routinely crosses it during winter polar-vortex events; peak >$100/MMBtu in 2014.

So the basis isn't just a price-level correction — it's the difference between a dispatch model that fires the dual-fuel switching logic correctly (Algonquin) vs one in which dual-fuel becomes an unused paper feature (Henry Hub only).

### The framing question

The decision depends on what v1's Phase 1 model is trying to demonstrate:

- **Frame A** — "validate the model plumbing works end-to-end with real data; produce a sensible-shaped output that doesn't crash"
- **Frame B** — "produce a first defensible Lockport-specific P10/P50/P90 distribution that captures the asset's economic story including winter tail-event value"

These are different goals with different basis requirements.

---

## Decision

**For v1, use Henry Hub directly as the delivered gas price. Document the basis gap as a known limitation. Defer basis modeling to v2.**

This commits to Frame A for the v1 build.

Concretely:
- Notebook 2 reads `data/paths/lockport/gas_price_history.parquet`, filters to `hub_name == 'Henry Hub'`, uses the `price_usd_per_mmbtu` column directly as delivered gas
- `market_context.yaml.gas_market.delivery_hub.value` remains "Algonquin Citygate" (the *intended* hub, per the asset's location) but a new field documents that v1 uses Henry Hub as a stand-in
- The model_card for any v1 Lockport run must include a banner: "Algonquin basis not modeled — dual-fuel switching never fires; winter dispatch risk under-represented"

---

## Reasoning

### Why Frame A is right for v1 here

1. **The model doesn't exist end-to-end yet.** v1's first job is to validate that the pipeline (data spine → loaders → dispatch logic → state update → LTSA → output) works structurally with real data. Adding basis modeling before the plumbing is proven is premature optimization.

2. **Dual-fuel is a tail-event capability, not a typical-day driver.** Lockport's annual capacity factor is ~5%. On 95%+ of operating days, basis is small (<$2/MMBtu) and doesn't change dispatch decisions. The 5-15 winter days/year where basis matters drive meaningful winter risk but a small fraction of annual margin. For a "first defensible model output," that fraction is acceptable to defer.

3. **Honest about the gap is better than imputed-and-likely-wrong.** Applying 2014-2017 monthly basis to 2018-2025 would *overstate* basis (Atlantic Sunrise pipeline + other Northeast capacity expansions tightened the basis post-2017). Henry Hub-only is a known limitation; 2014-2017 basis on 2018-2025 is a likely-wrong imputation.

4. **Faster path to feedback.** Frame A gets us to a running Notebook 2 → Notebook 3 → Notebook 4 → first Phase L Monte Carlo run sooner. When we see what the model actually does, the basis question gets re-evaluated with concrete dispatch evidence rather than hypothetical reasoning.

5. **The basis question doesn't go away — it just moves.** v2 is the right place to model basis properly (probably with daily distribution conditioned on temperature, using both the 2014-2017 Algonquin window for shape and external sources like EIA Daily Natural Gas Prices for the missing 2018+ period). Doing it as part of Phase G is doing it poorly in haste.

### Honest reconsideration of the original argument

The argument I (Claude) made for Option B/C in the prior turn overstated the case. I claimed dual-fuel was "the central modeling capability" that Henry Hub "neuters." That was too strong:

- Dual-fuel is *important* for capturing Lockport's distinctive economic story, but NOT *central* in the sense of driving annual margin
- "Neuters" implies the model becomes useless; in fact, the model runs fine for typical-day modeling, with dual-fuel as a documented unused capability
- The 95%-of-days argument cuts the other direction: most dispatch logic works correctly with Henry Hub

A more honest framing (which the user pushed for): basis matters for **tail-event risk modeling** and for **capturing the plant's reliability/winter-capture story**. For Phase 1 plumbing validation, Henry Hub is acceptable with documentation.

---

## Consequences

### Positive

- Notebook 2 can be written without an upstream basis-derivation notebook → faster to a working end-to-end model
- Decision is reversible — adding basis later doesn't require ripping out existing code, just adding a basis-overlay step before the dispatch fuel-cost calculation
- The Henry Hub time series has 29 years of coverage, well-aligned with LMP and weather (post-conversion); no time-alignment hacks needed
- model_card surfaces the limitation visibly — stakeholders can see what's omitted

### Negative / accepted tradeoffs

- **Dual-fuel switching never fires in v1**. The dispatch model has fuel-switching logic present but never economically triggered. The model can't show "what would happen in a polar vortex." This is the most consequential cost.
- **Winter dispatch risk under-represented.** P10 (rare-bad-days) values for spark spread will be too optimistic — actual polar-vortex days had Lockport running on oil to capture winter scarcity, our model has it running on (cheap) gas straight through. The downside protection that dual-fuel provides isn't captured.
- **Lockport-specific economic story partially obscured.** A merchant CCGT in the South would model fine on Henry Hub; Lockport is in NYISO specifically for winter reliability value, which we under-capture.
- **The 2014 polar vortex specifically isn't honored in backtests.** Anyone backtesting against January 2014 will see our model say "gas is fine" when reality was Lockport switching to oil. Backtest acceptance criteria need to allow for this.

### Mitigations / follow-up actions

- **model_card banner** (mandatory): see Decision section for exact wording. Every v1 Lockport run must surface this.
- **`market_context.yaml` documentation**: add an explicit `v1_basis_treatment` field with `status: assumed_industry`, `confidence: LOW`, citing this ADR.
- **Stub the dual-fuel logic** in `src/dispatch/` (Phase K) so it's present but documented as currently unused. When v2 adds basis, the switching logic is already in place.
- **v2 follow-on ADR** will document the basis modeling approach (likely daily distribution + temperature conditioning, drawing on the 2014-2017 Algonquin daily data for shape and external sources for 2018+). That ADR supersedes this one.

---

## Alternatives considered

### Option B — 2014-2017 monthly average Algonquin basis applied additively to Henry Hub

- **What it does**: compute 12 monthly average basis values from the 2014-2017 Algonquin daily data, add to Henry Hub daily price.
- **Pros**: captures the seasonal pattern (winter premium > summer premium); fires dual-fuel switching in winter months; only 30 minutes more work than Frame A.
- **Cons**: 2014-2017 basis is *higher* than 2018-2025 basis due to Atlantic Sunrise pipeline (~2018) and other Northeast capacity expansions; applying 2014-2017 averages to 2018-2025 overstates the basis; still flat within a month so misses daily extremes (polar-vortex events show up as ~$50-100 spikes for 1-3 days, not as monthly averages).
- **Why rejected for v1**: introduces a known imputation bias (overstating post-2017 basis) without proving the rest of the model plumbing first. Better to ship Frame A end-to-end, then decide whether the basis modeling is worth doing well in v2.

### Option C — Real daily Algonquin where we have it (2014-2017), Henry Hub elsewhere

- **What it does**: use actual daily Algonquin basis for the 2014-2017 period (~698 days) where we have real data; use Henry Hub for everything else.
- **Pros**: honest about the data we have; backtesting against the 2014 polar vortex actually uses real Algonquin spot prices including the >$100 peak days; no imputation
- **Cons**: introduces a discontinuity at end of 2017; the dispatch model behaves differently on either side of the data boundary; model_card discussion becomes complicated (basis-modeled period vs not)
- **Why rejected for v1**: introduces inconsistency that complicates downstream analysis. Either basis is modeled everywhere or nowhere — the period-aware hybrid creates more confusion than it resolves for a v1 plumbing validation.

### Option D — Full basis model (daily distribution + temperature conditioning)

- **What it does**: build a statistical model of Algonquin basis as a function of temperature, day-of-year, and Henry Hub level, fit on 2014-2017, apply to all periods.
- **Pros**: best of all options — captures seasonality, daily variation, polar-vortex tails; can be calibrated to known events
- **Cons**: substantial modeling work; not appropriate for v1 plumbing validation; needs Notebook 2's structure to exist first to know what the model needs to feed
- **Why rejected for v1**: scope-mismatch with Phase 1 goals. Defer to v2 (or beyond) when we know what the dispatch model actually demands from the gas input.

---

## References

- **Data**: `data/paths/lockport/gas_price_history.parquet` — per-hub coverage table in `data/paths/lockport/README.md`
- **Step 1 plan**: [`docs/plans/step_1_climate_price_scenario_plan.md`](../plans/step_1_climate_price_scenario_plan.md) §"Gas Price Path Construction" — the canonical decomposition formula
- **Notebook 1 output**: §F cross-validation surfaced the gas hub coverage gap as a soft warning + the per-hub coverage table; §I findings cell discusses Algonquin specifically
- **Market context YAML**: `data/assets/lockport/market_context.yaml` `gas_market` block — to be updated with `v1_basis_treatment` field referencing this ADR
- **Caveats**: `data/assets/lockport/caveats.md` §4 (dual-fuel switching) — modeling implication noted
- **Conversation context**: This ADR captures the discussion between divy and Claude on 2026-05-14 about gas hub treatment, including the original (overconfident) Option B/C recommendation, the user's "help me understand the logic" pushback, the honest reconsideration of dual-fuel's "centrality", and the eventual Frame A choice.

---

## Notes for future-self / reader

1. **Don't read this as "Henry Hub is the right answer for Lockport." It isn't.** It's the right v1 answer for a plumbing-validation goal. v2 should revisit.
2. **The basis story has direction**: 2014-2017 basis was *higher* than current basis. Don't imputate from 2014-2017 averages to 2018-2025 without acknowledging this.
3. **Dual-fuel is real**. Don't let "currently unused in v1" become "permanently unused." The dispatch model architecture should keep the fuel-switching code path present and ready to fire when basis modeling is added.
4. **Backtest accommodation**: if/when we backtest against 2014 specifically, expect divergence from reality on polar-vortex days. The model says "run on gas at $7"; reality was "switch to oil because Algonquin is $100."
