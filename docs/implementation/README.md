# Implementation Docs — how the `src/` code actually works

> **Why this folder exists.** When the model lived in notebooks, every step was narrated inline (the `# %%` cells + comments). Now that the engine and forward pipeline live in `src/`, that step-by-step narration moved here. These docs explain the **actual code** — module layout, the functions, the data flow, the I/O schemas — so the `src/` packages are readable without scrolling the source.
>
> **Relationship to the rest of the docs.** This folder is the *code* layer. It sits below the *concept* layers:
> - **Fundamentals** (organized our way, not model-gpr's): [`docs/learning_logs/`](../learning_logs/) — the gas-turbine / market fundamentals.
> - **Methodology**: [`docs/methodology/`](../methodology/) — how the model works conceptually ([`architecture.md`](../methodology/architecture.md), [`flowcharts.md`](../methodology/flowcharts.md), [`pnl_ledger.md`](../methodology/pnl_ledger.md), [`glossary.md`](../methodology/glossary.md)).
> - **Implementation** (this folder): how the *code* that realizes the methodology is built.
> - **Plans / decisions**: [`docs/plans/`](../plans/), [`docs/decisions/`](../decisions/) — what we're building and why.

## The pattern (per `src/` package)

Each package gets the same four-file set (borrowed from model-gpr's `docs/layer_1/*/implementation/`):

| File | Answers |
|---|---|
| `01_overview.md` | What is this package, what does it produce, what's in/out of scope? |
| `02_code_architecture.md` | Module layout, the core objects, the data flow, the daily/per-run loop, key patterns |
| `03_function_reference.md` | Per-function API: purpose, params, returns, side effects, gotchas |
| `04_io_schemas.md` | The exact input and output schemas (columns, types, units, provenance) |

## The packages

| Package | Source | Docs | What it is |
|---|---|---|---|
| **gt_engine** | [`src/gt_engine/`](../../src/gt_engine/) | [`gt_engine/`](gt_engine/) | The dispatch + wear + LTSA engine, extracted from notebook 4. Exposes `run_path()` (run over an injected market path) and `run_mode()` (historical-replay wrapper). |
| **forward** | [`src/forward/`](../../src/forward/) | [`forward/`](forward/) | The forward scenario engine: `select` (temperature-analog windows) → `build` (scenario specs) → `run` (engine over each scenario → P10/P50/P90), with `data` (basis loader). |

## Reading order (to grasp the whole project)

1. [`README.md`](../../README.md) — repo entry point.
2. [`methodology/flowcharts.md`](../methodology/flowcharts.md) — the loop, visually (start here if you think in pictures).
3. [`methodology/architecture.md`](../methodology/architecture.md) — the engine in words (state vector, the 12-step daily loop, forced outage, inspections).
4. [`methodology/pnl_ledger.md`](../methodology/pnl_ledger.md) — the economic ledger (every revenue + cost component).
5. **[`implementation/gt_engine/`](gt_engine/)** — how the engine code works (this folder).
6. **[`implementation/forward/`](forward/)** — how the forward scenario engine works.
7. [`plans/forward_engine_plan.md`](../plans/forward_engine_plan.md) — the forward design + the decisions (DA→RT, raw levels, etc.).
8. [`learning_logs/`](../learning_logs/) — fundamentals (duty types, degradation factors, revenue stack, merchant economics), as needed.
9. [`decisions/`](../decisions/) — the ADRs (the *why* behind the substantive choices, incl. ambient wear 006 / creep+trip 007).
10. [`methodology/glossary.md`](../methodology/glossary.md) — term reference.

## Status

| Package | 01 overview | 02 architecture | 03 function ref | 04 io schemas | extra |
|---|:--:|:--:|:--:|:--:|:--|
| gt_engine | ✅ | ✅ | ✅ | ✅ | ✅ `05_worked_example.md` (one day traced through the engine) |
| forward | ✅ | ✅ | ✅ | ✅ | — |

(✅ written. Keep this table current as `src/` evolves — e.g. when the N4 dedup-rewire lands, or when the model-gpr scenario package substitutes at the forward `select`/`build` seam.)
