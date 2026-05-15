# Lockport Energy Associates LP — Asset Profile

> EIA Plant ID 54041. 3-on-1 CCGT cogeneration, dual-fuel. NYISO Zone A. Commissioned 1992. Entity Type Q (cogeneration). 100% Lockport Energy Associates LP.

## Quick facts

| Field | Value |
|---|---|
| EIA Plant ID | 54041 |
| Operator | Lockport Energy Associates LP (Entity ID 11127) |
| Sector | IPP CHP |
| Configuration | 3-on-1 CCGT cogeneration, dual-fuel (NG + DFO) |
| Total nameplate | 221.3 MW (3 × 48.7 MW CT + 1 × 75.2 MW CA) |
| Operating since | 1992-07 (CTs) / 1992-09 (ST) |
| Balancing Authority | NYISO Zone A (NYIS) |
| LMP node (CTs) | NYISO PTID 23791 |
| LMP node (ST) | NYISO PTID 323769 |
| eGRID subregion | NYUP (NPCC Upstate NY) |
| EPA ORISPL | 54041 (same as EIA Plant ID) |

## Files in this folder (planned)

| File | Phase | Source | Status |
|---|---|---|---|
| `identity.yaml` | C | renewablesinfo brief §"At a glance" + §1 | Empty |
| `engineering.yaml` | C | renewablesinfo brief §3, §4, §5, §6 + thermal_enriched | Empty |
| `market_context.yaml` | C | renewablesinfo brief §7 + node_crosswalk | Empty |
| `operating_profile.yaml` | D | diligence-extractor MOR notebook final-summary table | Empty |
| `ltsa_terms.yaml` | F | Data room (pending extraction) | Empty — placeholder values until then |
| `caveats.md` | C/D | Composition of public + private caveats | Empty |
| `provenance.md` | C/D/F | Where each artifact came from + dates | Empty |

## What makes Lockport modeling-interesting (and tricky)

| Feature | Implication for the model |
|---|---|
| **3-on-1 CCGT** | Multi-mode dispatch: 3×CC_full (221 MW) / 2×CC (~170 MW) / 1×CC (~120 MW) / ST-only (~78 MW). Mode-specific heat rates (8,901 / 9,598 / 10,424 Btu/kWh from MOR). |
| **CHP-flagged (cogen)** | Host steam delivery (DHTS) is a real must-run constraint when host needs steam. VOM systematically higher than merchant-CCGT defaults (+30–50%). |
| **Dual-fuel** | Gas↔oil switching in 1 hr, storage-limited (~3–7 days oil), Title V permit-limited. Relevant in NYISO winter polar-vortex scenarios. |
| **1992 F-class vintage** | Tech-class falls in `<2000` vintage class for the dispatch_params lookup. Older steam-bottoming → slower ramp than newer fleet. |
| **Ambient sensitivity** | All four generators flagged `is_ambient_sensitive`. CT-side modest summer derate; ST-side actually gains capacity in summer. |
| **Operational status caveat** | Originally inferred as "likely mothballed" from public 2024 generation data — but **the diligence-extractor MOR notebook corrects this**: Lockport generated 192,494 MWh in 2024, similar to 2022. The plant was active throughout 2024. |
| **RGGI exposure** | NYUP subregion, NY state — Lockport is RGGI-exposed. CO2 cost layered into delivered fuel cost matters. |
| **Merchant cogen** | Not a regulated utility. No FERC Form 1. LTSA contract structure pending data room extraction. |

## Status

🟡 **Empty — to be populated by Phases C, D, F.**

Refresh source documents:

- renewablesinfo brief: `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_data_brief.md`
- diligence-extractor MOR notebook: `~/code/personal/diligence-extractor/notebooks/daily_heat_rate_analysis.ipynb`
- renewablesinfo equipment profile (internal working version): `~/code/personal/renewablesinfo_org/docs/extra/data_samples/plant_54041_lockport_equipment_profile.md`

## See also

- [data/assets/README.md](../README.md) — asset folder conventions
- [data/paths/lockport/README.md](../../paths/lockport/) — Lockport's exogenous time-series paths
- [docs/assumptions/status_taxonomy.md](../../../docs/assumptions/status_taxonomy.md) — status code reference
- [consolidation plan §7](../../../docs/plans/consolidation_plan.md#7-migration-mapping) — migration mapping
- [consolidation plan §8 Phases C, D, F](../../../docs/plans/consolidation_plan.md#8-execution-plan)
