# data/ — The self-contained data spine

> The single home for everything the model consumes. Per [consolidation plan](../docs/plans/consolidation_plan.md) §4.2 and §5 (D3, D4).

## Principle

gt_models is **self-contained**. Inputs land here as copies from upstream sources — never symlinks. The model reads from `data/` and nowhere else.

The four upstream feeders:

| Source repo | What lands in `data/` |
|---|---|
| renewablesinfo (lab) | `tech_class_defaults/` — dispatch_params lookup |
| renewablesinfo_org | `assets/<asset>/` — public-data parts of identity, engineering, market_context |
| diligence-extractor | `assets/<asset>/` — proprietary parts of operating_profile, ltsa_terms |
| model-gpr | `paths/<asset>/` — hourly LMP, daily gas, hourly weather |

Refresh is a deliberate human act: re-copy → update `provenance.md` → commit. There is no automatic sync. This is by design.

## Structure

```
data/
├── README.md                       (this file)
│
├── tech_class_defaults/            ← copied from renewablesinfo lab pass
│   ├── README.md
│   ├── dispatch_params_lookup.parquet
│   ├── dispatch_params_values.csv
│   └── refs/                       (source PDFs)
│
├── assets/                         ← per-asset profiles
│   ├── README.md
│   └── lockport/                   (v1 scope; only asset)
│       ├── README.md
│       ├── identity.yaml
│       ├── engineering.yaml
│       ├── operating_profile.yaml
│       ├── market_context.yaml
│       ├── ltsa_terms.yaml
│       ├── caveats.md
│       └── provenance.md
│
├── paths/                          ← copied from model-gpr (or Step 1 outputs)
│   ├── README.md
│   └── lockport/
│       ├── README.md
│       ├── lmp_da_hourly.parquet
│       ├── lmp_rt_intervals.parquet
│       ├── lmp_west_zone_da.parquet
│       ├── gas_price_history.parquet
│       ├── weather_hourly.parquet
│       └── weather_forecast_seas5.json
│
└── outputs/                        ← simulation outputs (GITIGNORED — regenerable)
    └── lockport/
        ├── runs/                   (per-run output bundles)
        └── reports/                (aggregated reports)
```

## Rules

1. **Self-contained.** No symlinks to model-gpr, renewablesinfo, or diligence-extractor. Copies only.
2. **Provenance everywhere.** Every artifact in `data/` has a `provenance.md` or README entry tracing it to: source path + copy date + SHA256 (for parquet) + source version.
3. **YAML for static specs, parquet for time series.** Per consolidation plan §5 D2.
4. **Assumption metadata on every value.** Every leaf value in YAML files carries `status` + `source` (+ `confidence` for assumed values). Per consolidation plan §6.
5. **Outputs are regenerable.** `data/outputs/` is gitignored. Re-running a simulation reproduces them.

## Current state

| Subfolder | Phase | Status |
|---|---|---|
| `tech_class_defaults/` | B | Empty — populated by Phase B |
| `assets/lockport/` | C, D, F | Empty — populated by Phases C/D/F |
| `paths/lockport/` | E | Empty — populated by Phase E |
| `outputs/` | L+ | Empty — populated by simulation runs |

## See also

- [consolidation plan §4.2](../docs/plans/consolidation_plan.md#42-data--the-spine-new) — folder architecture rationale
- [consolidation plan §6](../docs/plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle) — assumption tracking discipline
- [consolidation plan §7](../docs/plans/consolidation_plan.md#7-migration-mapping) — migration mapping (what comes from where)
- [docs/assumptions/status_taxonomy.md](../docs/assumptions/status_taxonomy.md) — status code reference
