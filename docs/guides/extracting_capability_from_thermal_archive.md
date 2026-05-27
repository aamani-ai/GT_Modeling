# Extracting a Capability Envelope from the Thermal Source Archive

> **For**: anyone building or refreshing a `data/assets/<asset>/capability_envelope.yaml` — the capability-side concept from the regime decomposition ([ADR-003](../decisions/003-regime-decomposition.md)).
>
> **Premise**: most of the *physical / engineering* capability signal you need is already extracted and normalized in the `renewablesinfo_org` thermal source archive (`thermal_enriched.parquet`, 65 columns). You don't have to read raw EIA XLSXs for it. What the archive *can't* give you is the *regulatory / market-qualification* signal (AGC qualification, PURPA QF status, ICAP participation, RMR) — that's a separate sourcing problem.
>
> **Relationship to the engineering-pull guide**: [`pulling_specs_from_powerplantsinfo.md`](pulling_specs_from_powerplantsinfo.md) covers *column mechanics* — how to query the parquet, status-tag values, and land them in `engineering.yaml`. **This guide builds on that** and covers the *capability interpretation* layer: how to reason from raw columns to a duty's qualified/unqualified verdict, and how to assemble the envelope. Read the engineering-pull guide first for the mechanics; this one for the capability reasoning.

---

## §1. The two-tier structure of capability data

The single most important thing to internalize: **capability data comes from two different worlds, and only one of them is in the archive.**

| Tier | What it answers | Source | In the thermal archive? |
| :--- | :--- | :--- | :---: |
| **Tier 1 — Physical / engineering capability** | Can the plant *physically* do this duty? (start time, ramp, fuel, configuration, steam) | EIA-860 (3_1, 3_5, 6_1, 6_2) → `thermal_enriched.parquet` | ✅ **Already extracted** |
| **Tier 2 — Regulatory / market qualification** | Is the plant *certified / contracted / registered* to do this duty? | NYISO MIS, FERC PURPA DB, ISO capacity-market filings | ❌ **Not in EIA** |

Why this matters: a duty is in the capability envelope only if *both* tiers clear. A plant can be physically capable of frequency regulation (Tier 1: fast ramp, fine control) but not AGC-qualified (Tier 2: no NYISO registration) — in which case frequency regulation is **not** in the envelope. The Tier-2 gate is often binary and decisive.

**Practical consequence for sequencing**: do Tier 1 first. It's cheap (the data's already in the archive), high-confidence (`real_reported` from EIA), and closes most of the *physical* capability questions. Then chase Tier 2 separately (NYISO/FERC web records + data-room documents) for the *qualification* questions Tier 1 can't answer.

The `thermal_enriched.parquet` schema doc itself says this explicitly — accredited capacity (UCAP/ICAP/EAS) "lives in ISO capacity-market filings, not EIA." Don't expect the archive to know about market qualification.

---

## §2. The source archive map

The `renewablesinfo_org` repo documents its upstream sources in a structured archive. For capability extraction, the relevant docs:

| Doc | What it tells you | Path (macOS) |
| :--- | :--- | :--- |
| **Thermal enriched schema** | The 65-column output schema + build flow + nuances | `~/code/personal/renewablesinfo_org/docs/data/parquet_outputs/engineering__thermal_enriched.md` |
| **EIA-860 3_1 Generator** | Generator master — capacity, prime mover, vintage, cold-start time, advanced-tech flags | `.../docs/data/raw_sources/eia/860/3_1_generator.md` |
| **EIA-860 3_5 Multifuel** | Dual-fuel switching block (the fuel-switching capability) | `.../docs/data/raw_sources/eia/860/3_5_multifuel.md` |
| **EIA-860 6_1 EnviroAssoc** | Boiler↔generator relational links + emissions-control equipment | `.../docs/data/raw_sources/eia/860/6_1_envir_assoc.md` |
| **EIA-860 6_2 EnviroEquip** | Boiler design, efficiency, firing rates, cooling | `.../docs/data/raw_sources/eia/860/6_2_envir_equip.md` |
| **CCGT topology insight** | How combined-cycle blocks are identified (4 signals) | `.../docs/data/raw_sources/insights/thermal/ccgt_topology_identification.md` |
| **The data itself** | `thermal_enriched.parquet` (13,227 thermal generators) | `~/code/personal/renewablesinfo_org/data/dimensions/engineering/thermal_enriched.parquet` |

(The archive uses "Zones": Zone 1 = raw-source schema docs, Zone 2/3 = parquet-output schema docs. For capability extraction you mostly read the Zone 2/3 thermal schema + the Zone 1 docs for the columns you want to interpret.)

---

## §3. Query mechanics

### The interpreter gotcha

`gt_models`'s own venv does **not** have pandas/pyarrow. The `renewablesinfo_org` venv does. Use it:

```bash
RIO=/Users/divy/code/personal/renewablesinfo_org
$RIO/.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_parquet(f"{__import__('os').path.expanduser('~')}/code/personal/renewablesinfo_org/data/dimensions/engineering/thermal_enriched.parquet")
lp = df[df['plant_id'] == 54041]   # join key is plant_id (int)
print(lp.T.to_string())             # transpose: one column per generator, easy to read
PY
```

Join key: **`plant_id`** (int, EIA Plant ID). Grain: one row per `(plant_id, generator_id)`. For Lockport that's 4 rows (GEN1/2/3 = CT, GEN4 = CA).

### The capability-relevant column subset

Of the 65 columns, these are the ones that inform capability (the rest are mostly cooling / boiler-design detail that's often null for gas turbines):

```
# Configuration / operating-mode envelope
prime_mover_code, configuration_label, is_combined_cycle,
combined_cycle_unit_id, combined_cycle_role, has_hrsg,
has_duct_burners, can_bypass_hrsg, topping_or_bottoming, is_chp

# Peaker test (start speed)
time_to_full_load_min, min_load_mw, min_load_pct

# Fuel-switching capability (winter reliability)
is_dual_fuel, can_switch_when_operating, secondary_energy_source,
capacity_mw_with_gas, capacity_mw_with_oil,
switch_time_gas_to_oil_hr, switch_time_oil_to_gas_hr,
fuel_switch_storage_limited, fuel_switch_air_permit_limited

# Capacity / ambient (mid-merit + baseload feasibility)
nameplate_capacity_mw, net_summer_capacity_mw, net_winter_capacity_mw,
is_ambient_sensitive, summer_derate_pct, winter_boost_pct

# Steam (cogen quantification — often null)
max_steam_flow_klb_per_hr, waste_heat_input_mmbtu_per_hr, boiler_count
```

---

## §4. Column → duty mapping (the recipe)

The core of this guide. For each duty, which columns inform the qualified/unqualified verdict, and how to read them.

| Duty | Tier-1 columns (from archive) | How to read them | Tier-2 gate (NOT in archive) |
| :--- | :--- | :--- | :--- |
| **peaker** | `time_to_full_load_min`, `prime_mover_code`, `min_load_pct` | Fast peaker needs cold-start ≪ 30 min. `time_to_full_load_min` ≥ ~120 (especially the 720 = "12H" default) → physically disqualified. Frame GT (not aero/IC) reinforces. | NYISO fast-start certification (physical proxy usually decisive; cert is confirmation) |
| **mid_merit** | `configuration_label`, `prime_mover_code`, `is_ambient_sensitive`, capacity columns | CCGT/CT/CA with reasonable efficiency → qualified. Cycling tolerance is implied by CCGT design. | None hard — mostly physical |
| **baseload** | `configuration_label`, efficiency (if present), capacity | Continuous-duty hardware → qualified (capability ≠ current realization). | None hard |
| **frequency_regulation** | `prime_mover_code`, ramp-adjacent fields | Hardware *may* suffice (aero best; CCGT possible). But this duty's verdict is dominated by Tier 2. | **NYISO AGC qualification (binary, decisive).** Without it, NOT in envelope regardless of hardware. |
| **cogen** | `is_chp`, `has_duct_burners`, `max_steam_flow`, `can_bypass_hrsg` | `is_chp=True` → cogen-capable. Duct burners + bypass = steam-delivery flexibility. | Active steam-offtake contract (data-room / D2) — capability needs a host |
| **must_run_eligible** | `is_dual_fuel` (reliability), `is_chp` (steam obligation) | Physical contributors: dual-fuel keeps it running in gas curtailment; CHP implies steam must-run. | **Mechanism-specific**: PURPA QF (FERC), RMR (NYISO), capacity-firm (NYISO ICAP) — all Tier 2 |

**Capability modifiers** (not duties, but attributes that condition multiple duties):

| Modifier | Columns | Conditions which duties |
| :--- | :--- | :--- |
| **fuel_switching** | `is_dual_fuel`, `switch_time_*`, `can_switch_when_operating`, `fuel_switch_*_limited`, `capacity_mw_with_oil` | Strengthens must-run / winter reliability — can keep delivering during gas curtailment by burning oil |
| **simple_cycle_capable** | `can_bypass_hrsg` | Expands the operating-mode envelope — can run GT-only, not just combined-cycle |
| **supplemental_firing** | `has_duct_burners` | Cogen steam flexibility — can boost steam output / sometimes enables steam-only mode |
| **load_turndown** | `min_load_pct` | Conditions load-level flexibility (Stream B) and mid-merit cycling depth |

---

## §5. Status-tagging capability values

Per [`docs/assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md). Capability-specific guidance:

| Situation | Status | Notes |
| :--- | :--- | :--- |
| Duty verdict from a directly-reported EIA column (e.g., `is_chp=True` → cogen) | `real_reported` | Source: cite EIA schedule via thermal_enriched |
| Duty verdict computed from EIA columns + a rule (e.g., 720-min start → peaker=false) | `real_reported` if the input is reported and the rule is deterministic; else `real_computed` | The 720-min value *is* reported; the "→ not a peaker" inference is a deterministic read. Tag `real_reported` with a caveat. |
| EIA clustering-default value (720 min, see §6) | `real_reported` + **caveat** | It's reported, but it's a coarse bucket (86% of CCGTs report exactly 720). Still decisive for the peaker verdict; caveat the precision. |
| Tier-2 verdict not yet sourced (AGC, PURPA QF, ICAP, RMR) | `placeholder` + `validation_path` | The archive cannot close these. Name the NYISO/FERC/data-room source in `validation_path`. |
| Physical capability present but Tier-2 unknown (e.g., freq-reg hardware OK, AGC unverified) | `placeholder` for the duty verdict; note the physical side in `evidence` | Don't claim the duty is qualified on hardware alone when a binary Tier-2 gate is unverified. |

---

## §6. Gotchas

These bite if you don't know them. The first is documented in the engineering-pull guide §5.4; repeated here because it's load-bearing for the peaker verdict.

| Gotcha | Detail | Capability consequence |
| :--- | :--- | :--- |
| **720-min cold-start is a clustering default** | EIA reports `time_to_full_load_min` in coarse buckets; 86% of CCGTs report exactly 720 (= "12H"). | Don't read 720 as a precise Lockport measurement. But it's still *decisive* for peaker: a fast peaker would report minutes, not 12 hours. Tag `real_reported` + caveat. |
| **`has_hrsg` is inconsistently populated** | For Lockport, CTs show `has_hrsg=None` and the CA shows `False` — even though it's a combined-cycle plant with HRSGs. EIA reporting quirk. | Don't rely on `has_hrsg` alone for CCGT detection. Use `is_combined_cycle` + `combined_cycle_unit_id` (the Unit Code grouping) + `boiler_count`. |
| **Efficiency stored as min/max pair** | `boiler_efficiency_100pct_min/max` not a weighted average. | When present, read the range. Often null for gas turbines anyway. |
| **Steam-side fields often null** | `max_steam_flow_klb_per_hr`, `turndown_ratio` are nan for Lockport. | Can't quantify steam capacity from EIA. The cogen *qualified* verdict still stands (from `is_chp`); only the quantification is missing. |
| **Dual-fuel capacities differ from nameplate** | `capacity_mw_with_gas` ≠ `capacity_mw_with_oil` ≠ `nameplate_capacity_mw`. | Use the fuel-specific capacities when reasoning about oil-mode operation. |
| **`min_load_pct` can be high** | Lockport CTs report 0.62 (62% floor) — limited turndown. | Affects mid-merit cycling depth + load-level flexibility (Stream B). High floor ≠ no mid-merit capability, but it's a real constraint. |

---

## §7. Worked example — Lockport capability extraction

The actual query (2026-05-26) returned these capability-relevant values:

| Column | GEN1/2/3 (CT) | GEN4 (CA) | Capability read |
| :--- | :--- | :--- | :--- |
| `configuration_label` | Combined Cycle | Combined Cycle | CCGT → mid-merit + baseload capable |
| `is_combined_cycle` / `combined_cycle_unit_id` | True / LEA1 | True / LEA1 | One block, 3 CT + 1 CA |
| `is_chp` | True | True | **cogen-capable** (real_reported) |
| `time_to_full_load_min` | **720** | **720** | **peaker = false** (12-hr start; clustering default but decisive) |
| `can_bypass_hrsg` | **True** | None | **simple-cycle capable** (operating-mode flexibility) |
| `has_duct_burners` | None | **True** | **supplemental firing** (cogen steam flexibility) |
| `is_dual_fuel` / `secondary_energy_source` | True / DFO | True / DFO | **fuel-switching capability** |
| `can_switch_when_operating` | True | True | Can switch gas↔oil *while running* |
| `switch_time_*_hr` | 1.0 / 1.0 | 1.0 / 1.0 | 1-hour switch each direction |
| `fuel_switch_storage_limited` / `_air_permit_limited` | True / True | True / True | Oil runtime bounded by storage + Title V permit |
| `capacity_mw_with_gas` / `_with_oil` | ~42 / ~43 | 78 / 78 | Roughly fuel-symmetric |
| `min_load_pct` | 0.62 | 0.19 | CTs limited turndown; CA flexible |

**What this closed (Tier 1)**: peaker verdict (was asserted from vintage → now EIA-confirmed); the entire fuel-switching capability (previously missing from the envelope); simple-cycle + supplemental-firing operating-mode flexibility; load-turndown floors.

**What it could NOT close (Tier 2 — still open)**: AGC qualification (frequency reg), PURPA QF status, NYISO fast-start certification (formal — though the physical proxy already decides peaker), RMR designation, NYISO ICAP participation. These need NYISO/FERC web records + data-room documents.

---

## §8. What the archive cannot tell you — and where to get it (Tier 2)

When you've maxed out Tier 1, these remain. Document them as `placeholder` with the right `validation_path`:

| Tier-2 item | Source | Notes |
| :--- | :--- | :--- |
| **AGC qualification** (frequency reg) | NYISO MIS resource registration | Binary gate. Web-checkable. |
| **PURPA QF status** | FERC PURPA QF database (`ferconline.ferc.gov`) | Indirect indicators (1992 vintage, Entity Type Q, IPP CHP sector) suggest QF; verify directly. Can lapse on efficiency threshold (18 CFR Part 292). |
| **Fast-start certification** | NYISO MIS | Physical proxy (720-min start) already decides peaker; cert is formal confirmation, low priority. |
| **RMR designation** | NYISO operations / RMR list | Negative-evidence check (absence from public list). Re-verify annually. |
| **ICAP / capacity-firm participation** | NYISO public ICAP auction records + data-room commitment letters | Also closes gap #2 in `gaps_and_priorities.md` (NYISO ICAP revenue). |
| **Active steam-offtake contract** (cogen realization) | Data room — commercial agreements (D2) | Capability (is_chp) is confirmed; the *active host contract* is the realization-side question. |

### §8.1 What the web audit actually yields (learned from the Lockport 2026-05-26 pass)

A real D1 web audit was run for Lockport. The honest result reshapes the Tier-2 expectation:

| Item | Web-retrievable? | Verdict |
| :--- | :---: | :--- |
| **Steam-host identity** | ✅ Yes | Found via DOE/public plant histories (Lockport's host = GM Harrison Radiator; electricity to NYSEG). Strong yield. |
| **PURPA QF *structure*** | ✅ Yes (circumstantial) | NYSEG offtake + named steam host + 1992 cogen = textbook QF. Upgrades a `placeholder` to `assumed_industry`/HIGH. |
| **PURPA QF *formal docket*** | ❌ No | FERC's QF search is a JS form; the Form-556 docket didn't surface in general web search. Needs FERC eLibrary direct query or data room. |
| **RMR designation** | ✅ Yes (negative) | No public Lockport RMR record → confirms not-active. Negative evidence is a real result. |
| **Ownership** | ✅ Yes | GEM gives the chain (Fortistar 76% / Osaka Gas 24%) — a bonus for identity.yaml. |
| **AGC qualification** (freq-reg) | ❌ No | NYISO doesn't publish an AGC-qualified-resource list at plant grain. |
| **ICAP participation** (capacity-firm) | ❌ No | NYISO ICAP clears at zone/aggregate; per-plant participation isn't public. |

**The meta-finding**: the "D1 web" lane has *limited* yield for capability. It's good for **identity-adjacent facts** (host, offtaker, ownership) and **negative checks** (no RMR). It is **poor** for **market-qualification status** (AGC, ICAP, formal QF) — that data is not published at plant grain and realistically comes from **D2 (the data room)** or direct NYISO market-participant / operator data.

Practical takeaway for a new asset: run the web audit, but **expect it to confirm identity/host/ownership + rule out RMR, and expect it to *not* close AGC/ICAP/formal-QF.** Budget those for D2, not D1. Don't burn time hunting public records that don't exist at plant grain.

---

## §9. The repeatable process (recap)

For any new asset's capability envelope:

1. **Confirm in archive** — query `thermal_enriched.parquet` by `plant_id`; expect N generator rows.
2. **Pull the capability column subset** (§3) — transpose for readability.
3. **Apply the column → duty mapping** (§4) — get a Tier-1 verdict per duty + the capability modifiers.
4. **Status-tag** (§5) — `real_reported` for EIA-sourced verdicts (caveat clustering defaults).
5. **List the Tier-2 gaps** (§8) — `placeholder` + `validation_path` for AGC / PURPA QF / ICAP / RMR / steam-contract.
6. **Assemble** `capability_envelope.yaml` — duty blocks + capability_modifiers + the gap inventory.
7. **Graduation** happens later (a per-concept ADR) once both tiers are filled enough to be honest.

The Tier-1 pass is the same recipe for every thermal asset. The Tier-2 pass varies by ISO/RTO and by what's in the asset's data room.

---

## §10. Cross-references

- [`pulling_specs_from_powerplantsinfo.md`](pulling_specs_from_powerplantsinfo.md) — the column-mechanics layer this guide builds on (query, status-tag, land in engineering.yaml)
- [`asset_profile_dimensions.md`](asset_profile_dimensions.md) §2 — where `capability_envelope.yaml` sits among the six dimensions
- [`../decisions/003-regime-decomposition.md`](../decisions/003-regime-decomposition.md) — the ADR that introduced the capability envelope
- [`../../data/assets/lockport/capability_envelope.yaml`](../../data/assets/lockport/capability_envelope.yaml) — the worked output
- [`../learning_logs/basics/10_plant_duty_classifications.md`](../learning_logs/basics/10_plant_duty_classifications.md) — what each duty means
- [`../learning_logs/basics/11_capability_vs_realization.md`](../learning_logs/basics/11_capability_vs_realization.md) — the capability/realization framework
- [`../assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md) — the 9-code status grammar
- [`../plans/00_strategic_spine.md`](../plans/00_strategic_spine.md) §5.2 — the open-data audit this extraction feeds
- **renewablesinfo_org thermal schema**: `~/code/personal/renewablesinfo_org/docs/data/parquet_outputs/engineering__thermal_enriched.md`
