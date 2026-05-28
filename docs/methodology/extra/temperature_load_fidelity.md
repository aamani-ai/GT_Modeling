# Temperature + Load Fidelity — Gap Analysis and Engine Changes (Stream B)

> **Status**: **Resolved for v1 (2026-05-27).** This was the framing (B1) for Stream B; §1–§7 are the original analysis. **The outcome of B2/B3/#1/#2/#3 is in §9 (read that for the conclusion).** Headline: only **#2 (commitment hurdle)** was committed; the part-load HR change is a no-op for a price-taker, the gas-basis overlay was tested and reverted, and the realistic-output model (#3) was deferred to Stream A because it *is* Stream A's forward dispatch rule. v1 is honestly labeled an **economic upper bound**. **Update 2026-05-27**: the **ambient half of B3** was subsequently *built* (hot-section creep + TBC ambient-weighted, re-anchored; [ADR-006](../../decisions/006-ambient-weighted-wear.md)); the **load half** stays deferred to Stream A (no load variation to weight in a full-dispatch v1). **See §10.**
>
> **Companion**: [`backtest_findings.md`](backtest_findings.md) (sibling analytical doc). Concept-level discussion of load is in [`../../discussion/02_load_as_a_dimension.md`](../../discussion/02_load_as_a_dimension.md) (local-only).
>
> **Sizing script**: [`notebooks/scratch/load_temp_gap_analysis.py`](../../../notebooks/scratch/load_temp_gap_analysis.py) — reproduces every number below from `mor_daily.parquet`.

---

## §1. Why this doc

The 2026-05-22 advisory meeting flagged that gas-turbine wear depends significantly on **load percentage** and **ambient temperature**, while the v1 model is **fired-hours-driven**. Before changing the engine (which alters headline numbers), Stream B starts by *sizing* the gap on real Lockport data, so we invest in the engine changes that actually matter for this asset.

---

## §2. The three engine gaps (confirmed in code)

The engine lives in `notebooks/04_full_path_mode_comparison.py` (N4); state evolution in `update_stress()`.

| Channel | → Capacity | → Heat rate | → Degradation |
| :--- | :---: | :---: | :---: |
| **Ambient temperature** | ✅ modeled (`ambient_derate_factor`, N3) | partial (baked into MOR-derived mode HRs) | ❌ **gap** — `tbc_time`/`eoh`/`fouling`/`rotor_life` accumulate as raw `fired_hours`; `FOULING_AQI_PROXY=1.0` is an unused hook |
| **Load level** | n/a | ❌ **gap** — no part-load HR; N4 line ~1231 `pass # dispatch at full capacity` | ❌ **gap** — wear identical at 60% or 100% load |

So: ambient is **half-modeled** (capacity yes, wear no); load affects **nothing** (100%-when-on assumed).

---

## §3. Gap quantification (real MOR data, 2021–2025; 348 operating days)

### §3.1 Part-load heat rate (the B2 prize) — mode-normalized

The model already captures **mode-pick** (3×CC / 2×CC / 1×CC) via mode-specific heat rates. The *missing* gap is **within-mode part-load** (running 3×CC at 70% vs 100%). So load must be normalized to the *chosen mode's* capacity, not total nameplate:

| Measure | Naive (vs nameplate) | **Mode-normalized (the true gap)** |
| :--- | --: | --: |
| Median load fraction | 0.585 | **0.669** |
| Mean HR penalty | 10.2% | **9.0%** |
| **Generation-weighted HR penalty** | — | **6.2%** |

Within-mode median load by mode: **1×CC 0.36, 2×CC 0.62, 3×CC 0.72**. The plant runs well below 100% even within its chosen mode — so the "100% load" assumption understates heat rate (overstates margin) by a **generation-weighted ~6%** on operating days.

**⚠ Cogen entanglement caveat**: this HR penalty is computed from *electrical* load fraction. On steam-driven days (especially 1×CC at 0.36 load) the GT runs to make **steam**, with electricity as a low byproduct — so gas-per-electrical-MWh looks inefficient, but much of that gas is making steam, not wasted. The ~6% therefore **partly reflects cogen steam co-production, not pure part-load inefficiency**. A clean B2 must allocate gas between steam and electricity (or condition on steam-day vs not) rather than naively applying a part-load HR curve to electrical load. The MOR-derived mode HRs may already embed some of this.

### §3.2 The framework polynomial is wrong (a finding for B2)

`InfraSure_ModelingFramework_V2.md` §4.6 / Appendix B.6 (and the copy in `02_load_as_a_dimension.md` §4.1) transcribe the part-load HR curve as:

```
HR_multiplier(L) = 2.648 - 4.296·L + 2.648·L²      ← AS TRANSCRIBED — INCORRECT
```

This polynomial is **internally inconsistent**: it has a minimum at L≈0.81 where it dips to **0.906** (a part-load HR multiplier *below 1.0* is unphysical — part-load is *less* efficient, so the multiplier must be ≥ 1.0), and it does **not** reproduce its own stated values (it gives 0.927 at L=0.9, not the documented 1.015). The *stated anchor values* (1.000 @ 100% … 1.162 @ 50%) are sensible; the *polynomial coefficients* are mistranscribed. B2 should refit to the anchors:

```
HR_multiplier(L) ≈ 0.471·L² - 1.026·L + 1.556     ← refit to published anchors; monotonic, ≥1.0
```

(The sizing script uses this refit. Action for B2: correct the polynomial in the framework + load discussion docs.)

### §3.3 Load × temperature degradation (the B3 question) — modest & redistributive for Lockport

Illustrative wear-weighting sensitivity (pending the Saturday & Isaiah (2018) load-temp paper):

| Wear model | Total weighted / flat |
| :--- | --: |
| `fired_hours` (current) | 1.00 |
| `fired_hours · load¹` | **0.68** |
| `fired_hours · load²` | **0.49** |

Counter-intuitive but important: because Lockport runs **part-load, not peak-fire**, load-weighting *redistributes* wear toward the (few) high-load hours and, absent recalibration, would *reduce* modeled total wear by 30–50% vs flat fired-hours. The current fired-hours-only model may therefore **overstate** Lockport's wear (it treats every part-load hour as full-stress). Only **14%** of operating fired-hours occur at ambient >80°F, and total fired hours are low (~1,340/yr). So **B3's absolute effect on Lockport is modest** — it matters far more for high-CF, peak-firing assets. For Lockport, B3 mainly changes the *distribution* (and hence inspection *timing*), not the total.

### §3.4 The 2×CC lockout is (mostly) a B2 byproduct, not a separate fix

The model never picks 2×CC (0% vs ~26% of operating days in MOR; `gaps_and_priorities.md` #9). Root cause confirmed in N4 `dispatch_day_mode_aware()` (~line 632): mode-pick is `margin = max(spark, 0) × full_mode_capacity`. Because **3×CC has both the best heat rate (8,901 vs 9,598 Btu/kWh) AND the most capacity (221 vs 173 MW)**, it strictly dominates 2×CC whenever spark is positive. So 2×CC can never win economically; 1×CC appears only via the must-run branch. **The lockout is a direct consequence of the 100%-load (full-capacity) assumption** — the same assumption B2 fixes.

Once B2 makes dispatch a **joint (mode, load) decision** with a part-load HR penalty, 2×CC stops being dominated: 3×CC at part-load (e.g., 68%, HR penalty ~7%) becomes *less* efficient than 2×CC at higher load (e.g., 87%) for intermediate output. So **the economic portion of the 2×CC gap resolves as a byproduct of doing B2 correctly** — not extra work, but a *correctness criterion* for B2.

How much of Lockport's 26% is economic vs unit-availability (data, 97 MOR 2×CC days):

| Signal | Finding | Driver |
| :--- | :--- | :--- |
| Output level | 2×CC median 106 MW vs 3×CC 159 MW; within-mode load 0.61 vs 0.72 | **Economic** — lower-output days, part-load → B2 captures |
| Which CT off | CT3 68% / CT1 20% / CT2 11% (preferential, not random) | **Unit-availability** — some specific-CT-down pattern |
| Clustering | median 3-day gap, 41% consecutive, 8-day max streak | **Mixed** — scattered (economic) + clustered (possible unit-down) |

**Conclusion**: the **economic** part (the majority signal — lower-output part-load days) is recoverable by B2's joint (mode, load) dispatch. The **unit-availability** residual (CT3-preferential, multi-day streaks = a specific CT down for maintenance/derate) genuinely needs **per-generator state** (v2, `gaps_and_priorities.md` #9 — a state-vector rework tracking each CT's EOH/availability/forced-outage). Do **not** bundle per-generator state into B2; it balloons scope. B2 should target the economic 2×CC; the unit-down 2×CC stays v2.

**B2 acceptance criterion (added)**: after B2, 2×CC should emerge on a non-trivial share of operating days (economic, intermediate-output) — closing much of the 0%→~26% gap, with the residual attributable to single-CT-down events that await per-generator state.

---

## §4. The data constraint

Confirmed (02 §7 Q5): we have **hourly ambient** (`weather_hourly.parquet`) but **daily-only load** (`mor_daily.parquet` gives daily MWh + run-hours, not an hourly load shape). Consequences:
- Ambient-conditional effects can be modeled at hourly resolution.
- Load-conditional effects can be *modeled* but only *calibrated* against daily-average load — within-day load shape (e.g., frequency-reg swings) is invisible.
- This caps B3's calibratable fidelity; a higher-resolution SCADA feed would lift it.

---

## §5. Proposed engine changes (await direction)

| Sub-step | Change | Touches | Decision needed |
| :--- | :--- | :--- | :--- |
| **B2 — part-load HR + joint (mode, load) dispatch** | Make dispatch a joint (mode, load) decision with a (cogen-aware) part-load HR multiplier. **Byproduct: resolves the economic 2×CC lockout** (§3.4) — 2×CC stops being dominated once 3×CC-at-part-load is penalized | N4 `dispatch_day_mode_aware()` (the mode-pick + the `margin = spark × full_capacity` line) + HR (`hr_degraded_for_mode`); `operating_profile.yaml` (corrected polynomial); fixes framework doc | (a) continuous load vs 3 bands? (b) separate part-load HR from cogen steam allocation? (c) dispatch optimizer picks load vs heuristic? **Acceptance: economic 2×CC emerges; unit-down 2×CC stays v2** |
| **B3 — load × temp degradation** | Weight `update_stress()` wear terms by load and ambient | N4 `update_stress` (eoh/fouling/tbc_time/rotor_life); recalibrate base coefficients so totals stay anchored | (a) coefficients from the **Saturday & Isaiah (2018) paper** (pending); (b) recalibrate base wear so we redistribute, not double-count; (c) which terms get load-weighting vs ambient-weighting |
| **B4 — ADR-006** | Commit the load representation + degradation approach | `docs/decisions/006-*.md` + methodology | After B2/B3 direction |

---

## §6. Conditioning + dependencies

- **Realized-profile conditioning** (now available, Phase 4): B2/B3 parameters could be conditioned on the realized profile — e.g., winter cogen days (steam-driven, low electrical load) want the cogen-aware HR allocation; summer mid-merit days want the pure part-load curve. The realized profile tells the engine *which regime's load/wear physics apply*.
- **Saturday & Isaiah (2018) paper dependency**: B3's load-and-temperature fatigue/creep coefficients should come from the paper Siddharth shared (citation pending, per `04_industry_vocabulary_and_references.md` §5.3). Until then B3 is illustrative.

---

## §7. Recommendation + open questions

**Recommendation**: B2 (part-load HR) is the higher-value Lockport change (~6% gen-weighted margin effect, real), but it must be **cogen-aware** (don't naively apply a part-load curve to electrical load on steam-driven days). B3 (load×temp degradation) is mostly a **generalization investment** for future high-CF assets and **wants the Saturday & Isaiah (2018) paper** — lower priority for Lockport, where its effect is modest and redistributive. Sequence: fix the framework polynomial → B2 cogen-aware part-load HR → (paper) B3.

**Open questions**:
1. Cogen gas allocation: how to split gas between steam and electricity so part-load HR isn't conflated with steam co-production?
2. Load representation: continuous vs 3 bands (per 02 §10 stepping-stone)?
3. Recalibration: if B3 redistributes wear, how do we re-anchor base coefficients to avoid double-counting?
4. Does B2 change dispatch (load becomes a decision) or just accounting (HR penalty on the realized load)?

---

## §9. Resolution (2026-05-27) — what was actually built, and the v1 stance

The §1–§7 proposals were executed and the surprising bits resolved. Final v1 outcome:

| Item | Outcome | Why |
| :--- | :--- | :--- |
| **Part-load HR (the "B2 prize")** | **No-op — not implemented.** | For a price-taker merchant CCGT, per-MWh margin is *best* at full load, so the model always dispatches full when spark > 0 → the part-load multiplier never fires. Adding it alone changes nothing. |
| **Framework polynomial** | **Corrected** (commit a0b2e18). | `2.648 − 4.296L + 2.648L²` was internally inconsistent; refit to `0.471L² − 1.026L + 1.556`. Kept regardless, since it's just wrong. |
| **#1 gas-basis overlay** | **Tested and reverted** (commit 4e2ff49). | Overstates post-2018 winter gas (caveats §11: Atlantic Sunrise tightened the basis) AND didn't fix the over-commit. Flat Henry Hub stands for v1. |
| **#2 commitment hurdle** | ✅ **COMMITTED** (commit d429d18). | Always-on full-start-C&M-recovery hurdle. The one principled dispatch-realism win. Over-commit 2.07× → **1.94×**, fired hours −15%, spark $36M → $33.6M, 98 tests pass. |
| **#3 realistic (price-responsive) output** | **Deferred to Stream A (Phase 6).** | There is no *principled* price-taker version of part-load output — it's inherently a **behavioral / dispatched** model, which is exactly the forward dispatch rule Stream A needs. Doing it now would be a fudge or a premature behavioral commitment. #3 *is* Stream A. |
| **2×CC emergence** | **Not achievable in v1.** | It needs either #3 (behavioral output, → Stream A) or per-generator availability (v2 state-vector rework, gaps #9). |
| **B3 — ambient half** | ✅ **COMMITTED** (2026-05-27, [ADR-006](../../decisions/006-ambient-weighted-wear.md)). | Hot-section creep (`dc`) + TBC life (`tbc_time`) now ambient-weighted at hourly resolution over fired hours, re-anchored to the fired-hour-weighted mean ambient (34.3°F) so total wear is preserved (anchor 0.9999) and only the *distribution* shifts toward hot hours. Headline byte-identical (latent on Lockport-seed-42). Coefficient is a literature placeholder pending the Saturday & Isaiah (2018) paper. **See §10.** |
| **B3 — load half** | **Deferred to Stream A (Phase 6).** | A full-dispatch price-taker has no load variation to weight → load-weighted wear is a structural no-op until Stream A introduces behavioural/price-responsive output (the same dependency as #3). Plan documented in §10 + ADR-006. |

**The v1 stance (the key decision)**: the model is an **honest economic upper bound** — "the most this asset could economically generate/earn." The ~1.94× over-commit is the *economic ceiling*, NOT a realized-output forecast, because the model self-commits as a price-taker; real output is lower due to ISO dispatch-to-quantity, steam-following, conservatism, and unit availability — none of which are economic. The **behavioral output model that would turn the ceiling into a realized-output predictor is Stream A's job** (a forward valuation has no future dispatched-MW, so it needs a behavioral/price-responsive dispatch rule — the same thing #3 needs). This avoids a premature behavioral fudge and does the dispatch rule once, properly, in Stream A.

**The root insight for the whole stream**: the over-commit is the **price-taker self-commitment paradigm**, not gas price or part-load HR. #2 dents the *hours* component principledly; the *MW-per-hour* component is the upper-bound-vs-predictor fork, resolved by labeling v1 as an upper bound and carrying the behavioral output into Stream A.

---

## §10. Ambient-weighted hot-section wear — built (2026-05-27)

This section is the implementation record for the **ambient half of B3** and the **deferred plan for the load half**. Full reasoning trail: [ADR-006](../../decisions/006-ambient-weighted-wear.md).

### §10.1 What was built (the ambient half) — DONE

The wear physics meeting-point — "ambient temperature drives degradation, not just hours" — is now in the N4 engine for the **hot-section thermal accumulators**:

- **New**: `ambient_wear_factor(temp_f)` — a bounded maintenance factor (∈ [0.70, 1.40]) = `1 + 0.004·(temp_f − 34.3)`, ~1.0 at the reference ambient, >1 hotter, <1 colder.
- **Applied**: at **hourly resolution over fired hours**, accumulated in `dispatch_day_mode_aware` as `fired_hours_hotweighted`, consumed in `update_stress(..., fired_hours_hot=...)`.
- **Weights ONLY**: creep (`state.dc`) and TBC life (`state.tbc_time`) — the metal-temperature-driven hot-section terms. `eoh`, `fouling`, `rotor_life`, `df` stay on raw `fired_hours` by design (see ADR-006 table for why each).
- **Physics direction**: hotter ambient → hotter compressor-discharge cooling air → hotter blade metal → faster creep / TBC oxidation; colder ambient → the reverse.

**Re-anchored, not re-levelled** (the key correctness property): the reference (`AMBIENT_WEAR_REF_F = 34.3 °F`) is the **fired-hour-weighted mean ambient** of Lockport's post-#2 path, so the applied factor's weighted mean ≈ 1.0. This **redistributes** wear toward hot hours (changing inspection *timing*) without changing the calibrated *total*.

**Validation** (2026-05-27 run, mode A):

| Check | Result |
|---|---|
| Anchor: Σ`fired_hours_hot` / Σ`fired_hours` | **0.9999** (total preserved) |
| Redistribution: effective factor by ambient band | <32°F **0.94** → 32–50°F 1.00 → 65–80°F **1.15** → >80°F **1.19** |
| Headline (spark / net / inspections / forced) vs baseline | **byte-identical** ($33.59M / −$145.96M / 1 / 35) |
| Unit tests | 98/98 pass |

**Why the headline is unchanged (and why that's correct)**: for Lockport-seed-42 the hot-section accumulators are **sub-threshold** (`tbc_time` ≪ Weibull η; `p_tbc` negligible) and `dc` (creep) **is not wired into any outcome** (not in `p_forced`; the `dc+df > D_LIM` halving never fires). So redistribution is **real and directionally correct but latent** — it will bite for higher-CF / hotter assets, for paths where `tbc_time` nears threshold, and once creep is wired to a failure mode. This matches the §3.3 prediction ("modest & redistributive; changes distribution/timing, not total").

### §10.2 What is deferred (the load half) — Stream A / Phase 6, with a plan

The load half is **not** built in v1, on purpose and with a documented reason and plan:

- **Why deferred (the blocker)**: v1 dispatches at **full mode capacity** (price-taker, §9). With load pinned at 100%, a load-weighted wear term has *no signal to act on*. The load half **requires** a per-hour **dispatched MW < capacity**, which is produced by **Stream A's behavioural/price-responsive dispatch rule** (Phase 6, the realistic-output work ex-#3). So it's blocked on a dependency, not merely postponed.
- **How to build it (when unblocked)**: form `load_fraction = dispatched_MW / mode_capacity_MW` per hour; multiply the hot-section weight → `ambient_wear_factor(temp_f) × load_wear_factor(load_fraction)`, accumulated into the **same** `fired_hours_hotweighted` seam this ADR built. The plumbing already exists — the load half is *an additional multiplier on the same accumulator*, not new structure.
- **Direction + a trap**: higher load → higher firing temp / peak-fire → faster hot-section wear (GER-3620 peak-load factor). But §3.3 showed load-weighting *reduces* Lockport's modeled **total** (it runs part-load, not peak-fire) — so the load half must be **re-anchored too** (redistribute, not re-level) or it silently drops total wear.
- **Rides along**: the **`eoh` peak-fire maintenance factor** belongs with the load half (industry EOH counts peak-fire hours at a multiple) — same dependency, same paper.
- **Coefficients**: from the Saturday & Isaiah (2018) load-temp paper (same source as the ambient coefficient).

### §10.3 Side-fix surfaced by this work — Sanity-6 (calendar inspections)

Validating the run exposed a **pre-existing** over-strict sanity check (N4 §O "inspections triggered near threshold"): it flagged *any* inspection firing >5K EOH below threshold, but **calendar-triggered** inspections legitimately fire below the EOH threshold (they're time-driven). Once the #2 commitment hurdle cut fired hours, EOH lags the calendar, so a valid calendar MI tripped the assert and **aborted the whole run before any output bundle was written** (the model_card had silently gone stale). Fixed: Sanity-6 now exempts `trigger == "calendar"` inspections and only enforces the EOH-proximity rule on EOH/hard-stop triggers. Run now completes; fresh model_card regenerated. Noted in `caveats.md` §12.

---

## §8. Cross-references

- [`../../plans/00_strategic_spine.md`](../../plans/00_strategic_spine.md) §3.2, §4 (Phase 5) — Stream B in the overall plan
- [`../../discussion/02_load_as_a_dimension.md`](../../discussion/02_load_as_a_dimension.md) — load concept (local-only); §4.1 polynomial corrected 2026-05-26
- [`../../InfraSure_ModelingFramework_V2.md`](../../InfraSure_ModelingFramework_V2.md) §4.6 + App B.6 — the actual source of the part-load polynomial (corrected 2026-05-26)
- [`../architecture.md`](../architecture.md) §5 — the engine + state vector B2/B3 would change
- [`backtest_findings.md`](backtest_findings.md) — sibling findings (incl. steam-only mode, mode divergence)
- [`../../data/assets/lockport/realized_operating_profile.yaml`](../../../data/assets/lockport/realized_operating_profile.yaml) — the conditioning signal for B2/B3
- [`../../data/assets/lockport/operating_profile.yaml`](../../../data/assets/lockport/operating_profile.yaml) — where the corrected part-load polynomial + steam-only params live
- `notebooks/scratch/load_temp_gap_analysis.py` — the reproducible sizing
