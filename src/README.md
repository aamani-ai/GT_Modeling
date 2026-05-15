# src/ — The model code

> Where the gas turbine model lives. Per [consolidation plan](../docs/plans/consolidation_plan.md) §4.3, §5 D1.

## Status

🅿️ **Empty in v1 until Phase K.** The model code is built by *refactoring validated notebooks* into modules, not by designing modules upfront. Per the parent plan's notebook-first sequencing — notebooks (Phases G–J) prove the modeling logic on real Lockport data; then Phase K refactors them into `src/`.

This is deliberate. Designing modules before doing the computation linearly is exactly the "designed in isolation" failure mode the original prototype suffered from. The notebooks force the right module boundaries to emerge from the work.

## Reference: the prototype this replaces

The Athens prototype lives in [`docs/extra/gas-turbine-digital-twin/`](../docs/extra/gas-turbine-digital-twin/). That's the **architectural reference**, not the source. We replicate the same conceptual model (three layers, daily feedback loop, Mode A/B/C trade-off, P10/P50/P90 outputs, endogenous forced outage from state, recursive state update) — but with a clean implementation that knows about the real data shapes.

See [docs/extra/understanding_of_gas_turbine_digital_twin.md](../docs/extra/understanding_of_gas_turbine_digital_twin.md) for the reader's guide to what we're replicating.

## Proposed module map (target shape after Phase K refactor)

This will evolve during Phase K based on what the notebooks actually surface. Tentative:

```
src/
├── README.md                       (this file)
├── __init__.py
│
├── io/                             ← built from Notebook 1
│   ├── __init__.py
│   ├── asset_loader.py             (reads data/assets/<asset>/*.yaml with assumption metadata)
│   ├── path_loader.py              (reads data/paths/<asset>/*.parquet)
│   ├── tech_defaults_loader.py     (reads data/tech_class_defaults/)
│   └── schemas.py                  (pydantic/dataclass schemas for YAML)
│
├── engineering/                    ← built from Notebook 3
│   ├── state.py                    (state vector + init_state)
│   ├── stress.py                   (EOH, creep, fatigue, fouling, TBC, HRSG, rotor accumulators)
│   ├── capacity.py                 (cap_eff: ambient derate)
│   ├── heat_rate.py                (hr_clean + hr_degraded, mode-aware)
│   ├── forced_outage.py            (endogenous P_forced from state)
│   └── inspection.py               (CI/MI reset semantics)
│
├── dispatch/                       ← built from Notebook 2
│   ├── modes.py                    (Mode A/B/C policy curves)
│   ├── hourly.py                   (hourly commit/dispatch)
│   ├── daily.py                    (daily loop orchestration)
│   ├── maintenance_schedule.py     (calendar shoulder-snapping)
│   └── multi_mode.py               (1×CC / 2×CC / 3×CC mode choice — Lockport-specific)
│
├── ltsa/                           ← built from Notebook 4
│   ├── contract.py                 (daily fee accruals, EOH reserve)
│   ├── inspections.py              (CI/MI event cost classification)
│   ├── overage.py                  (start overage charges)
│   ├── penalties.py                (availability + HR penalties)
│   └── forced_outage_classify.py   (in-scope vs owner-uncovered)
│
├── cogen/                          ← built from Notebook 2 (NEW vs prototype)
│   ├── host_steam_constraint.py    (must-run logic when DHTS > threshold)
│   └── vom_adjustment.py           (cogen +30-50% VOM markup)
│
├── markets/                        ← built from Notebook 2 (NEW vs prototype)
│   ├── rggi.py                     (CO2 cost from emissions rate × allowance price)
│   └── capacity_market.py          (NYISO ICAP — future, v2)
│
└── runners/                        ← built from Notebook 4
    ├── single_path.py              (one path × N years)
    └── monte_carlo.py              (N paths × M modes)
```

## What changes from the prototype

Per consolidation plan §5 D1:

**Carries over unchanged (conceptual):**
- Three-layer architecture (engineering / dispatch / LTSA)
- Daily feedback loop and order of operations
- Clean-vs-degraded twin dispatch attribution
- State vector concept + inspection-reset semantics
- Mode A/B/C policy framework
- Calendar-snapped maintenance scheduling with hard-stop overage
- Endogenous forced outage from state
- LTSA cost taxonomy (7 streams)

**Redesigned for our use:**
- Data ingest: reads from `data/` spine, not `gt_market_inputs.npz` synthetic blob
- Multi-mode dispatch: 1×CC / 2×CC / 3×CC mode choice for Lockport (not just on/off block)
- Cogen host-steam constraint (Lockport-specific)
- RGGI carbon cost layered into delivered fuel cost
- Assumption metadata: every parameter carries provenance

**Eventually better (out of v1 scope but the trajectory):**
- Real rolling-window optimizer instead of heuristic spark-vs-hurdle
- NYISO ICAP capacity revenue
- Ancillary services
- Tail-event scenarios (Uri-class gas shocks)

## See also

- [consolidation plan §4.3](../docs/plans/consolidation_plan.md#43-src--the-model-new)
- [consolidation plan §5 D1](../docs/plans/consolidation_plan.md#d1-the-prototype-is-architectural-reference-not-a-source-for-copy-paste)
- [docs/extra/understanding_of_gas_turbine_digital_twin.md](../docs/extra/understanding_of_gas_turbine_digital_twin.md) — the prototype reader's guide
- [docs/plans/consolidation_plan/notebooks/](../docs/plans/consolidation_plan/notebooks/) — the notebook plans that will inform the eventual src/ structure
