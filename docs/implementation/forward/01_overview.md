# forward — Overview

> **Source**: [`src/forward/`](../../../src/forward/) (`data.py`, `select.py`, `build.py`, `run.py`, `__init__.py`)
> **Concept docs**: [`plans/forward_engine_plan.md`](../../plans/forward_engine_plan.md) (design + decisions); the forward box in [`flowcharts.md`](../../methodology/flowcharts.md) chart 1.

## What it is

`forward` is the **forward scenario engine** (Stream A / Phase 6): it turns the historical-replay model into a **forward, SEAS5-conditioned, scenario-based valuation**. It generates conditioned forward price/gas/weather paths from the local data spine and runs [`gt_engine`](../gt_engine/) over each, producing a probability-weighted **P10/P50/P90** distribution of Net P&L.

It does *not* reimplement the dispatch/wear engine — it feeds [`gt_engine.run_path`](../gt_engine/03_function_reference.md). The method (temperature-analog window selection) is **ported from model-gpr's prototype** (`lockport_gas_continuous_window`), which was in-memory only; here it's a reusable, self-contained `src/` package reading gt_models' own local data.

## The pipeline

```
select  →  build  →  run
(which     (scenario   (gt_engine over each scenario
 windows,   specs)      → probability-weighted P10/P50/P90)
 weighted)
```

| Stage | Module | What it does |
|---|---|---|
| **data** | `data.py` | Loads price (basis-selectable) / weather / gas over the **full 1999–2026 range** in the schema `run_path` expects |
| **select** | `select.py` | Scores each continuous Apr→Mar historical window by how closely its temperature anomaly matches the SEAS5 ensemble → softmax probabilities |
| **build** | `build.py` | Turns the selected windows into engine-runnable scenario specs (native Apr→Mar date spans + probability) |
| **run** | `run.py` | Runs `gt_engine.run_path` over each scenario, collects per-scenario economics, computes probability-weighted quantiles, writes artifacts |

## What it produces

`run_forward(mode, seed, basis)` → a result dict + (saved) `data/outputs/lockport/forward_runs/forward_<ts>/`:
- `per_path.parquet` — one row per analog scenario (spark, LTSA, Net P&L, fired hours, probability)
- `quantiles.json` — P10/P50/P90 + prob-weighted mean for Net P&L, spark, LTSA, MWh
- `manifest.json` — provenance (basis, SEAS5 init, valid months, n_paths, seed)
- (via notebook 06) `forward_summary.png` (4-panel) + `forward_model_card.md`

## Key decisions baked in (v1)

- **Basis = RT** by default (`select`/`build`/`run` take a `basis` arg). RT → **25 analog windows (1999–2026)** spanning multiple gas regimes; DA → ~8 post-2017. RT captures the high-gas-year downside a DA-only pool excludes. ([plan §6](../../plans/forward_engine_plan.md).)
- **Raw historical price levels** — no forward-curve anchoring (deferred).
- **Native-date runs, no rebasing** — each window runs over its own Apr→Mar dates; because the engine computes aging relative to each run's start and a fresh 1-yr run never hits an EOH inspection threshold, the runs are directly comparable without hour-by-hour rebasing onto a common 2026 calendar (which is only needed for fan-chart presentation + anchoring).
- **Scenario-driven spread, fixed seed** — the spread reflects *which future* (analog), not outage-RNG noise.
- **Temperature-only conditioning, summer-only coverage** (per the prototype) — the SEAS5 file covers Apr–Oct, so Nov–Mar ride along on the chosen analog year (un-conditioned). Two known v2 gaps: **(1)** winter is un-conditioned yet Lockport is a winter must-run cogen → condition Nov–Mar on annual climate indices (ENSO/NAO/AO/PDO); **(2)** condition jointly on price/gas/market *regimes* (non-stationarity-aware, via anomalies not raw levels), not weather alone. Both interact with the Monte Carlo design. **Full notes: [`plans/forward_engine_plan.md`](../../plans/forward_engine_plan.md) §10.**

## Scope — what forward is and isn't

**Is**: the v1 scenario generator + runner for Lockport, reading the local data spine, producing a forward Net P&L distribution.

**Isn't**:
- **Not the dispatch engine** — that's [`gt_engine`](../gt_engine/).
- **Not anchored / market-consistent** — paths sit at raw historical levels (anchoring is a documented follow-up).
- **Not a full Monte Carlo** — fixed seed; outage-RNG MC (each window × many seeds) is a later layer.
- **Not yet coupled to model-gpr** — uses an in-repo analog selection; the model-gpr scenario package can later substitute at the `select`/`build` boundary.

> **Reminder**: absolute Net P&L is **not representative** (energy-only + placeholder LTSA, inherited from the historical model). The forward engine's value is the *distribution shape* and the *scenario spread*.

## Where to go next
- [`02_code_architecture.md`](02_code_architecture.md) — module layout, the analog method, data flow.
- [`03_function_reference.md`](03_function_reference.md) — per-function API.
- [`04_io_schemas.md`](04_io_schemas.md) — scenario spec + output schemas.
