# data/assets/ — Per-asset profiles

> One subfolder per asset. Each contains the asset's static specs as assumption-tracked YAML files. v1 has `lockport/` only.
>
> **For understanding what each YAML captures and why**: read [`docs/guides/asset_profile_dimensions.md`](../../docs/guides/asset_profile_dimensions.md) — the principle (plant profile is upstream of everything), the 5 dimensions, decision tree for where ambiguous fields go.
>
> **For setting up a new asset from the renewablesinfo_org pipeline**: read [`docs/guides/pulling_specs_from_powerplantsinfo.md`](../../docs/guides/pulling_specs_from_powerplantsinfo.md) — the step-by-step lift-from-platform workflow.

## Why this folder

The model is asset-specific. Lockport's 1992 F-class 3-on-1 CCGT cogen has a completely different operating profile from, say, a 2020 H-class single-shaft merchant CCGT. The static facts about each plant — capacity, generators, dual-fuel matrix, cold-start time, LTSA contract terms — live here, separated from the time-series scenario inputs in `paths/` and the tech-class defaults in `tech_class_defaults/`.

## Asset folder structure

Each `<asset>/` folder follows this convention:

```
<asset>/
├── README.md                  (entry point — what's known, what's pending)
├── identity.yaml              (plant ID, name, operator, sector, status, cross-system IDs)
├── engineering.yaml           (capacity, generators, derates, dual-fuel, prime movers)
├── operating_profile.yaml     (heat rate by mode, cold-start gas, run-streak patterns)
├── market_context.yaml        (NYISO node, hub, BA, eGRID subregion, RGGI exposure)
├── ltsa_terms.yaml            (contract structure — placeholders until data room extraction)
├── capability_envelope.yaml   (what duties the plant is *capable* of — peaker/mid-merit/baseload/cogen/freq-reg/must-run; per ADR-003)
├── caveats.md                 (cogen, mothball question, fuel switching, multi-mode dispatch)
└── provenance.md              (where each artifact came from + last refresh date)
```

**Note on `capability_envelope.yaml`** (added 2026-05-25): the capability-side concept from the regime decomposition ([ADR-003](../../docs/decisions/003-regime-decomposition.md), local-only). Describes what duties the plant *is capable of providing* — structural, very-slow cadence (years). The realization-side concept (what the plant *is currently doing*) is inferred from operating history and will live separately when committed (per ADR-003 §4.2).

## v1 scope: Lockport only

Per consolidation plan §5 D4, v1 has exactly one asset: Lockport Energy Associates LP (EIA Plant ID 54041). The directory structure is *designed to be multi-asset* (so adding `deal_2/` later is trivial), but populating only Lockport is intentional. Multi-asset abstraction comes from doing 2–3 deals end-to-end, not from designing for it upfront.

## YAML conventions

### Format

YAML for static specs (per consolidation plan §5 D2). Parquet for time series within an asset folder if needed (e.g., a months-by-mode heat-rate table).

### Assumption metadata on every value

Every leaf value carries provenance. Per consolidation plan §6 — non-negotiable.

```yaml
generators:
  GEN1:
    nameplate_capacity_mw:
      value: 48.7
      status: real_reported
      source: "EIA-860 schedule 3_1 Y2024"
    vom_per_mwh:
      value: 1.02
      usd_year: 2011
      status: assumed_techclass
      source: "Kumar 2012 NREL/SR-5500-55433 Table 1-1 'Gas-CC' baseload"
      confidence: MEDIUM
      caveat: "Baseload-only lower-bound; cogen markup of +30-50% likely applies"
```

Status taxonomy (9 codes): see [docs/assumptions/status_taxonomy.md](../../docs/assumptions/status_taxonomy.md).

### Loader convention

`src/io/asset_loader.py` (Phase K) will expose:
- Direct access for modeling code: `asset.engineering.generators['GEN1'].nameplate_capacity_mw → 48.7`
- Metadata access for introspection: `asset.engineering.generators['GEN1'].nameplate_capacity_mw_meta → {status, source, confidence, caveat}`

Notebooks before Phase K work with the raw nested dict (per Notebook 1 plan §3.D).

## Status

| Asset | Phase | Status |
|---|---|---|
| `lockport/` | C, D, F | Empty — populated by Phases C (public data), D (MOR-derived), F (LTSA placeholder) |

## See also

- **[docs/guides/asset_profile_dimensions.md](../../docs/guides/asset_profile_dimensions.md)** — comprehensive dimension framework + principle (read first)
- **[docs/guides/pulling_specs_from_powerplantsinfo.md](../../docs/guides/pulling_specs_from_powerplantsinfo.md)** — new-asset setup workflow
- [consolidation plan §4.2](../../docs/plans/consolidation_plan.md#42-data--the-spine-new) — folder architecture
- [consolidation plan §6](../../docs/plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle) — assumption-tracking discipline
- [docs/assumptions/status_taxonomy.md](../../docs/assumptions/status_taxonomy.md) — status code reference
- [docs/methodology/extra/backtest_findings.md](../../docs/methodology/extra/backtest_findings.md) — evidence that profile fidelity drives downstream accuracy (steam-only mode discovery)
