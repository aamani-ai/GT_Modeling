# Forward Engine Plan — Stream A / Phase 6

> **Status**: Proposed (2026-05-27). The execution plan for the forward-looking engine — the build that turns the v1 historical-replay model into a forward, scenario-based valuation. Sits under [`00_strategic_spine.md`](00_strategic_spine.md) §4 Phase 6 (Stream A) and supersedes the sketch in [`step_2_execution_blueprint_plan.md`](step_2_execution_blueprint_plan.md) for the consumer side.
>
> **One-line goal**: run gt_models' own dispatch/wear/LTSA engine over a set of **conditioned forward scenario paths** (price + gas + weather, generated *inside* gt_models) instead of the single 2017–2025 historical replay — producing P10/P50/P90 economics for a forward horizon.

---

## §1. Where we are (the facts this plan is built on)

- **The conditioning method already exists as a prototype** in model-gpr: `data_analytics_notebooks/lockport_gas_continuous_window/01_initial_prototype.ipynb` (+ memo `.md`). It is **in-memory only, not productionized** ("does not create production code", "does not write reusable artifacts"). So there is nothing to runtime-depend on — porting the *method* is the only option.
- **All data is already local to gt_models** (`data/paths/lockport/`): RT nodal LMP (`lmp_rt_intervals`, 1999→2026), DA hourly (`lmp_da_hourly`, 2017→2026), West-zone DA, Henry Hub gas (`gas_price_history`, in `trade_date`/`price_usd_per_mmbtu`), hourly weather (`weather_hourly`, 1980→2026), and the SEAS5 forecast (`weather_forecast_seas5.json`, 12 vars × 51 members). **Nothing is missing.**
- **`src/` is empty** (README only); the **engine lives in `notebooks/04_*.py` and runs on import** (top-level `run_mode` loop). So the engine is not yet callable on an injected path.
- **The 98 tests cover data/config only** (`test_lockport_static_profile`, `test_tech_class_defaults`) — *not* the engine. So extracting the engine to `src/` does not threaten the existing test suite (we add engine tests as we go).

**Implication**: this build is also the natural trigger for the Phase K "graduate notebooks to `src/`" refactor — because the forward engine *requires* an importable engine. We do that extraction as the foundation, killing two birds.

## §2. The conditioning method we are porting (from the prototype)

Label: `temperature_conditioned_continuous_window_physical_analog`.

1. **Candidate = a full continuous Apr–Mar historical window** (8760 h) — not month blocks, because gas value is path-dependent (streaks, scarcity hours, joint LMP+gas states). ~24 eligible windows (1999→2026) at ≥99% coverage on price/weather/gas.
2. **Conditioning signal = standardized monthly temperature anomaly** (z-score vs historical climatology), conditioned on the **SEAS5 ensemble-mean** anomaly, only for months with ≥80% S2S coverage (Apr–Oct for the current file; other months neutral — *no fake climatology*).
3. **Window distance** `D(w) = sqrt(Σ αₘ (z_hist − z_s2s)²)` → **softmax → probability** (τ=0.5, floor 0.02).
4. **Sample N paths** (with replacement) from window probabilities, or use the probability-weighted windows directly.
5. **Rebase** each source window onto the target horizon by ordered-hour rank (drop Feb 29, enforce 8760 h).
6. Each path **carries RT/DA LMP + Henry Hub gas + weather together** — the joint state dispatch needs.

This method aligns with gt_models' existing decisions: Henry Hub for gas (ADR-001), delivered basis deferred (caveats §11/§13), **raw tails preserved** (scarcity hours are the value), temperature-only conditioning for v1.

## §3. Proposed architecture

**Own it in gt_models; port the method; reuse the engine via extraction.**

```
data/paths/lockport/                      ← inputs (already local)
   lmp_rt_intervals / lmp_da_hourly / gas_price_history / weather_hourly / weather_forecast_seas5.json
        │
        ▼
src/gt_engine/                            ← FOUNDATION (Phase K extraction)
   state.py        PlantState + constants
   dispatch.py     dispatch_day_mode_aware, mode caps, HR
   wear.py         update_stress, p_forced (incl. ADR-006/007)
   ltsa.py         accruals, inspections
   run.py          run_path(): the daily loop over an arbitrary (lmp,gas,weather) path
        │                         ▲
        │                         │ imported by both
        ▼                         │
notebooks/04_*.py (thin driver)   │   src/forward/
   historical replay  ────────────┘      select.py    analog selection (the ported method)
                                          build.py     rebase + assemble scenario_paths ensemble
                                          run.py       run_path over each scenario; aggregate P10/P50/P90
        │
        ▼
data/paths/lockport/scenarios/<run_id>/scenario_paths.parquet   ← the input contract (saved)
data/outputs/lockport/forward_runs/<ts>/                         ← P10/P50/P90 + per-path P&L
```

**Why extraction (not a quick parameterization of N4)**: N4 runs on import and mixes engine + reporting; the forward engine needs the *daily loop* callable on injected inputs. Extracting `src/gt_engine/` gives one engine that both the historical notebook and the forward runner call — and it's the Phase K graduation we owed anyway. The "properly, with right workflows" choice.

## §4. The scenario-path schema (the input contract)

`data/paths/lockport/scenarios/<run_id>/scenario_paths.parquet` — one row per (path, target hour):

| Column | Meaning |
|---|---|
| `path_id` | scenario id (1..N) |
| `source_window_id` | historical Apr–Mar window the path was drawn from |
| `target_datetime_local` / `_utc` | rebased target timestamp |
| `temperature_2m` | weather carried from source (feeds ambient derate/wear) |
| `lmp` | the dispatch price (RT or DA per §6 decision) |
| `henry_gas_usd_per_mmbtu` | daily gas carried from source, expanded to hourly |
| `source_datetime_local` | provenance (which historical hour this came from) |

Plus a `selections.json` (which windows, probabilities, sample counts) and a `manifest.json` (run config, SEAS5 init date, conditioning vars/weights) for provenance — mirroring the prototype's outputs but **saved** (the prototype kept them in-memory).

## §5. Build sequence

| Step | Deliverable | Notes / unblocked? |
|---|---|---|
| **0. Engine extraction** | `src/gt_engine/` importable; N4 becomes a thin driver; **prove identical output** to current N4 (same seed → same model_card numbers) + add engine smoke tests | Foundation. Unblocked now. The risk-controlled part: refactor with a byte-identical-output gate. |
| **1. Scenario selection** | `src/forward/select.py` — port the analog method; reads local data; emits window probabilities + `selections.json` | Unblocked now (data local). Validate: warm SEAS5 → warm windows favored. |
| **2. Scenario build** | `src/forward/build.py` — rebase + assemble `scenario_paths.parquet` (carry lmp+gas+weather); schema validation (8760 h/path, no nulls) | After step 1. |
| **3. Forward run** | `src/forward/run.py` — `run_path` over each scenario; aggregate to P10/P50/P90; write `forward_runs/<ts>/` | After steps 0+2. |
| **4. Driver notebook** | `notebooks/06_forward_scenarios.py` — orchestrates 1→3, plots fan charts / P10-P50-P90, model_card-style summary | After step 3. |
| **5. (Later) behavioral output (#3)** | layer the price-responsive dispatch rule so forward output is a *realized-output predictor*, not just the economic upper bound over scenarios | Refinement; see §7. |
| **6. (Later) forward-price anchoring** | scale raw historical price levels to the current forward curve (the prototype's deferred "Step 3") | Refinement; see §6. |

## §6. Decisions needed before coding (the forks)

These shape the build; recommendations given, but they're judgment calls for alignment:

1. **Dispatch price basis — RT-primary vs DA. → DONE: built on DA, then switched to RT (2026-05-27).**
   v1 was proven on **DA** (~8 windows, comparable to N4's baseline), then switched to **RT** as the default (`src/forward/data.py` `load_price_hourly`; `select`/`build`/`run`/notebook 06 take a `basis` arg, default `"RT"`).
   > ✅ **RT switch complete.** RT runs from **1999 → 25 eligible windows** spanning multiple gas regimes vs DA's ~8 post-2017 shale-era windows.
   > **Validated payoff (the reason it mattered):** the RT pool surfaces the **high-gas-year downside** (2005–2009 gas at $8–13/MMBtu → negative spark while the cogen still must-runs → Net as low as −$21M) that the DA-only 2017+ pool *structurally excluded*. The distribution moved from DA's P10/P50/P90 = −13.6/−10.6/−2.6 to RT's **−18.9/−16.2/−8.2 ($M)** — more negative but far more representative of the range of futures.
   > **How it was done:** RT aggregated to hourly (floor in UTC to dodge a DST fall-back ambiguity, then →Eastern); `data.py` loads the full 1999–2026 range (the engine's pre-sliced 2017–2025 windows can't serve older RT windows); `run.py` slices per scenario.
   > **Still open (smaller follow-ups):** an RT *historical* baseline for apples-to-apples comparison with N4; re-checking the commitment hurdle under RT spikiness (tuned on DA); forward-price anchoring; outage-RNG Monte Carlo; behavioral output (#3).
   > **Deeper limit:** any analog method is capped by history; a generative weather→price model (model-gpr) is what truly lifts it — beyond v1.
2. **Forward-price anchoring — raw historical levels vs anchor to forward curve.** The prototype paths sit at *historical* price levels (not scaled to today's forward curve). *Recommendation*: v1 = **raw, no anchoring**, clearly labeled "analog-implied, not market-consistent"; anchoring is step 6. (Matches the prototype's own staging.)
3. **Path count / sampling — sampled ensemble vs weighted windows directly.** Prototype samples 100; you noted 7–8 (or even the ~24 weighted windows) is fine. *Recommendation*: make it **configurable** (default ~50), and also support "use the eligible windows directly with their probabilities" (deterministic, no sampling noise) — cheap either way.
4. **Engine reuse — extract to `src/gt_engine/` (recommended) vs quick-parameterize N4.** *Recommendation*: **extract** (proper foundation + Phase K). This is the main effort but the right one.

## §7. The behavioral-output (#3) relationship

v1 forward can run the **same upper-bound dispatch** over scenarios → a *distribution of economic-ceiling* P&L (honest: removes hindsight, brackets uncertainty). The behavioral/price-responsive output rule (#3, which turns the ceiling into a realized-output prediction and is where 2×CC can emerge) is a **layer on top**, not a blocker for the first forward run. Sequencing it after the first forward run keeps the build tractable and lets us see the upper-bound distribution first.

## §8. Non-goals for v1 forward

- Forward-price anchoring, delivered gas basis (TETCO-M3), residual perturbation — all deferred (prototype Step 3).
- Market-state conditioning beyond temperature (spark-spread regime, scarcity-hour count) — deferred.
- Multi-asset — Lockport only.
- Full Monte Carlo precision (thousands of paths) — a modest ensemble is the point at this stage.

## §9. Validation discipline (per the workflow)

- **Step 0**: byte-identical N4 output post-extraction (the gate) + engine smoke tests.
- **Step 1**: conditioning sanity — a warm SEAS5 signal up-weights historically-warm windows (reproduce the prototype's `window_weight_table` behavior); coverage gate excludes low-S2S months.
- **Step 2**: every path = exactly 8760 h, no nulls, joint lmp+gas+weather present, provenance traceable.
- **Step 3**: P10/P50/P90 are ordered and plausible; a degenerate single-path run reproduces a single historical-window replay.

## §10. Conditioning — open issues & v2 design notes

The v1 conditioning is **temperature-anomaly analog matching over the forecast-covered months only** (the SEAS5 file covers Apr–Oct; see §2). Two substantive limitations + a coupling, to resolve in a later version. **Captured here so they're not lost.**

### §10.1 The un-forecast winter months (the coverage gap) — *unfair to leave un-conditioned for a winter-heavy asset*

The SEAS5 file (init 2026-04-02, 215-day horizon) only conditions **Apr–Oct**; Nov–Mar contribute nothing to the window score. Once a year is selected on its summer match, its **whole 12 months — including Nov–Mar — ride along as that year's actual history**, i.e. winter is conditioned only *implicitly* via the summer analog.

**Why this is a real problem for Lockport specifically**: it's a **winter must-run cogen** — its highest-stakes months (steam-driven winter) are exactly the **un-conditioned** ones. Forecasting the summer and letting winter free-ride is the wrong emphasis for this asset.

**Candidate solutions (v2)**:
- **Annual / seasonal climate indices with winter teleconnection skill** — e.g. **ENSO/ONI**, **NAO**, **AO**, **PDO**. These carry genuine winter-weather signal and are available where a 7-month SEAS5 daily forecast isn't; add them to the distance for Nov–Mar.
- **Rolling forecast vintages** — a forecast initialized later in the year covers a different 7-month window; stitching vintages could span the full Apr→Mar.
- **Longer-horizon seasonal products** if available.

### §10.2 Beyond temperature — joint multi-regime conditioning (*price / gas / market regime*)

Today we condition on **weather (temperature) only**, then let price/gas ride along with the chosen analog year. But the better question: condition **jointly** — favor analog years that match the forecast on **multiple dimensions** (temperature *and* a price regime *and* a gas regime *and* maybe a market/scarcity regime). That picks more economically-relevant analogs, not just thermally-similar ones.

**The catch — non-stationarity** (the reason it's not trivial): price and especially **gas** are strongly non-stationary (structural shale shift in gas; renewables penetration + fuel-mix changes in LMP). Conditioning on **raw levels** would just match the *trend*, not the *regime*. The fix is the **same trick temperature already uses**: condition on **standardized anomalies / regime-relative deviations** (de-trend / difference / normalize to a rolling baseline), or **classify into regimes first** and match on regime — not on raw $/MWh or $/MMBtu. This is a real analysis opportunity: move from "pick weather analogs" to "pick *market-state* analogs" done in a non-stationarity-aware way.

### §10.3 The Monte Carlo coupling (*these complicate the MC design*)

Adding conditioning dimensions is **not free for the Monte Carlo** (Phase L / the eventual MC layer):
- **Pool shrinks / weights concentrate**: requiring a match on temp *and* price *and* gas means fewer historical years qualify, weights pile onto a handful → the ensemble narrows and the tails get thin (the opposite of what an MC wants).
- **"What are we sampling?" gets subtler**: marginal-vs-joint conditioning, and whether the MC samples *over scenarios*, *over the engine RNG*, or *over conditioning uncertainty* — these stack. More conditioning specificity trades **representativeness for relevance**, and the MC has to be designed *with* the conditioning, not after it.

**Action**: design the conditioning richness and the Monte Carlo together; treat §10.1/§10.2 as v2 work with §10.3 as the constraint. None of this is v1 — v1 stays temperature-only, summer-conditioned, documented.

## §11. Dispatch basis (DA vs RT), perfect foresight, and the backfilled-DA-nodal option

> Formal decision record: [ADR-008](../decisions/008-forward-dispatch-basis-and-foresight.md). This section is the analysis it points to.

### §11.1 Two roles of the price series — keep them separate
The price feed does **two** jobs: (a) the **dispatch signal** the engine optimizes against, and (b) the **analog-pool length** (history start sets how many windows are eligible). The basis choice trades these off.

### §11.2 The perfect-foresight idealization (why v1 is an upper bound)
The engine dispatches against **realized** hourly prices — i.e. with **hindsight**. A real gas plant **submits an offer/bid curve in advance** and is committed under price *uncertainty*; it cannot cherry-pick the profitable hours after the fact. So the model **over-states** achievable margin — this is the core reason v1 is an *economic upper bound*, not a realized-output forecast, and a driver of the ~2× over-commit vs MOR.

> **Sharp consequence for basis choice**: **perfect foresight on *RT* is the *loosest* upper bound**, because RT scarcity spikes are the *least* foreseeable thing in the market — a real plant can't pre-position to capture them. **DA is closer to the plant's actual committable position** (cleared a day ahead, against forecasts). So RT-with-hindsight over-states *more* than DA-with-hindsight.

### §11.3 DA vs RT — pros / cons

| | **RT (real-time nodal)** — *current v1 default* | **DA (day-ahead nodal)** |
|---|---|---|
| History / pool | **1999+ → ~25 windows**, multiple gas regimes (rich, tail-representative) | **2017+ → ~8 windows**, all shale-era (biased, thin tails) |
| Realism as a dispatch signal | **Loosest** upper bound — perfect foresight on the least-foreseeable series | **Tighter / more realistic** — DA is the advance-committable price the plant actually bids into |
| Scarcity / option value | captures RT scarcity (but un-foreseeably) | smoother; misses RT scarcity |
| Volatility / noise | high | lower |

**The tension**: DA is the *more realistic* dispatch signal but has a *short, biased* pool; RT has the *rich* pool but is the *loosest* foresight assumption. v1 picked RT (pool richness) and labels itself the loosest upper bound.

### §11.4 The ideal — and the backfilled-DA-nodal option (v2 candidate)
The **ideal dispatch signal is the DA *nodal* price over a *long* pool** — realistic commitment basis *and* regime diversity. We don't have long DA-nodal history (2017+), so the candidates:

- **(A) Backfill DA-nodal for pre-2017 windows.** Fit the DA↔RT relationship on the 2017+ overlap (where we have both DA and RT nodal) — and/or DA-zonal→nodal congestion — then synthesize pre-2017 DA from RT. *Pro*: realistic DA dispatch + long pool. *Con*: the DA/RT spread is itself **non-stationary** (congestion patterns, the DA-RT premium drifted), so the backfill carries model error — flag it honestly; don't fabricate confidence.
- **(B) Use RT but apply a "foreseeability haircut" (tail compression).** This is the prototype's deferred compression layer (`01_initial_prototype` §13): compress the un-foreseeable RT spikes toward a DA-like envelope (P15/P85 slot compression). Cheaper than (A); approximates "you couldn't have captured that spike."
- **(C) Accept RT, label it the loosest upper bound** (current v1). Honest, simplest.

### §11.5 Related analyses & realisations to run (later)
- **Quantify the foresight premium**: run the engine perfect-foresight-DA vs perfect-foresight-RT vs a *forecast-based / lagged* (imperfect-foresight) dispatch, and report the spread — this *measures* how much the basis + foresight choice actually moves the valuation (turns the hand-waving into a number).
- **It's the #3 behavioral-output work in disguise**: the cleanest route to a realistic, foresight-free dispatch is the **behavioral / realized-output rule (Stream A, #3)** — calibrate dispatch to realized MOR behavior (hour-selection / CF) rather than simulating offers + clearing + forecast error.
- **The fully-realistic mechanism = two-settlement** (DA commit on forecast + RT settle on deviations). Highest fidelity, **heaviest** — v2+ and likely overkill for a low-CF must-run cogen that mostly steam-follows + price-takes.

### §11.6 v1 stance
RT, perfect foresight, **explicitly labeled the loosest upper bound**. DA-backfill / compression / #3 / two-settlement are all v2+; the foresight premium is the thing to *measure* first (cheap analysis) before deciding how much realism to buy.

## §12. Cross-references

- [`00_strategic_spine.md`](00_strategic_spine.md) §3.1 (Stream A), §4 (Phase 6)
- [`step_1_climate_price_scenario_plan.md`](step_1_climate_price_scenario_plan.md) — the upstream scenario package (model-gpr side)
- model-gpr `data_analytics_notebooks/lockport_gas_continuous_window/01_initial_prototype.{ipynb,md}` — the ported method
- [`../methodology/architecture.md`](../methodology/architecture.md) §5 + [`../methodology/flowcharts.md`](../methodology/flowcharts.md) — the engine being extracted + run over paths
- ADRs [001](../decisions/001-gas-hub-treatment-v1.md) (Henry Hub), [006](../decisions/006-ambient-weighted-wear.md)/[007](../decisions/007-creep-wiring-and-trip-wear.md) (wear) — preserved in the extracted engine
