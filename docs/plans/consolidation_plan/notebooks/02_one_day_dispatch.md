# Notebook 2 — One Day of Dispatch: The Inner Loop

> **Status**: Plan drafted 2026-05-14. Awaiting user review before execution.
> **Notebook path (when built)**: `notebooks/02_one_day_dispatch.ipynb`
> **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) — execution Phase H
> **Sibling plans**: [`README.md`](./README.md) — notebook-track overview; [`01_data_spine_load_validate.md`](./01_data_spine_load_validate.md) — Notebook 1 plan
> **Prerequisites**: Phase G complete (Notebook 1 ran end-to-end with no hard fails). Phases A–F (data spine) populated.

---

## §1. Purpose

Pick **one representative Lockport day** and walk through the hourly dispatch logic end-to-end in linear, inspectable form. Surfaces the dispatch model's inner loop — the per-hour commit decision, mode choice (1×/2×/3×CC), spark spread under clean vs degraded heat rate, cogen constraint, RGGI cost layering — before any of it gets refactored into `src/dispatch/`, `src/cogen/`, `src/markets/`.

Goals, in priority order:

1. **Prove the dispatch logic works** with real Lockport data — heat rate by mode (from `operating_profile.yaml`), real LMP at PTID 23791 (from `data/paths/lockport/lmp_da_hourly.parquet`), real Henry Hub gas (per ADR-001), real weather (for ambient derate), real RGGI cost layered.
2. **Surface mode-choice ergonomics** — the model needs to decide hour-by-hour which of `1×CC` / `2×CC` / `3×CC_full` to commit. The heat rates differ by 17% across modes; the decision matters. This notebook makes that logic visible.
3. **Encode the cogen must-run constraint** — when host steam is needed (DHTS > threshold), the plant runs regardless of LMP. This is the single biggest Phase 1 trap for a cogen plant (per `caveats.md` §6).
4. **Demonstrate the clean-vs-degraded twin attribution** — the prototype's signature trick. For a single-day notebook, "degraded" is the same as "clean" (no state evolution yet — that's Notebook 3). But we set up the structure so Notebook 3 can drop it in.
5. **Produce a defensible daily P&L** for one day — gross margin = (LMP - delivered_fuel_cost - VOM - RGGI_cost) × MWh, with the mode choice and cogen constraint applied.

**Read-only on the data spine.** No writes to YAMLs or path parquets. Optional writes to `data/outputs/lockport/runs/notebook2_<day>/` if useful for Notebook 3 to inherit.

**Decisions inherited from Notebook 1 + ADR-001**:
- `v()` / `m()` helper functions (re-defined in this notebook's §A setup)
- Weather TZ conversion at load: `pd.to_datetime(..., utc=True).tz_convert('US/Eastern')`
- Display in NYISO local (US/Eastern) consistently
- Tech-class join key derivation: `(prime_mover, vintage_class, aero_derivative)`
- **Henry Hub used directly as delivered gas** per ADR-001 — Algonquin basis NOT modeled in v1
- **Dual-fuel switching never fires in v1** as a direct consequence (per `market_context.yaml.gas_market.v1_modeling_choice.dual_fuel_switching_fires_in_v1`)

---

## §2. Inputs (files this notebook reads)

All inherited from Phase E (paths) + Phase C/D/F (YAMLs) + Phase B (tech defaults). No new files needed.

| File | Purpose |
|---|---|
| `data/assets/lockport/identity.yaml` | Plant ID, status, operating dates |
| `data/assets/lockport/engineering.yaml` | 4 generators, capacity, dual-fuel, ambient sensitivity |
| `data/assets/lockport/market_context.yaml` | NYISO node, RGGI exposure, gas market `v1_modeling_choice` |
| `data/assets/lockport/operating_profile.yaml` | Heat rate by mode (3×CC 8,901 / 2×CC 9,598 / 1×CC 10,424 Btu/kWh), DHTS host-steam, mode classifier thresholds |
| `data/paths/lockport/lmp_da_hourly.parquet` | NYISO DA LMP at PTID 23791, hourly |
| `data/paths/lockport/gas_price_history.parquet` | Henry Hub daily, filtered per ADR-001 |
| `data/paths/lockport/weather_hourly.parquet` | Hourly ambient temperature (after TZ conversion) |
| `data/tech_class_defaults/dispatch_params_lookup.parquet` | VOM ($1.02/MWh), startup costs (deferred to Notebook 3 for actual use) |

---

## §3. Cell-by-cell sketch

### §3.A — Setup

Imports, helpers, repo root.

```python
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path("..").resolve()
DATA_DIR = REPO_ROOT / "data"
ASSET = "lockport"

def v(field): ...   # same as Notebook 1
def m(field): ...   # same as Notebook 1
```

Also: load all the YAMLs + path files. Apply the weather TZ conversion (per Notebook 1 finding).

### §3.B — Day picker

Pick **one representative day** for the walkthrough. Strategy:

1. From `data/paths/lockport/lmp_da_hourly.parquet`, restrict to 2023 (a typical year, post-2017 LMP regime, pre-MOR-2024-question)
2. Compute daily peak LMP and daily mean LMP
3. Find a day in the **P75-P90 of daily peak LMP** — high-LMP enough that dispatch decisions matter, but not the absolute peak (which might be a once-in-a-decade event)
4. Verify the day is mid-week (not weekend), summer month (June-September), and the LMP profile looks "normal" (no obvious data gaps)
5. Document the chosen date + the criteria

**Decision**: pick a single date programmatically based on criteria, not hard-coded. The criteria are visible in the cell so future readers see WHY this day.

This is also where we'd verify (qualitatively) that the day picker is reasonable — the chosen day's max LMP, ambient temp, gas price should look like a "summer dispatch-relevant day."

### §3.C — Slice the data for the chosen day

For the chosen date `D`:
- Slice 24 hours of LMP from `lmp_da_hourly` — should be `datetime_local` between `D 00:00 US/Eastern` and `D 23:00 US/Eastern`
- Pull Henry Hub gas price for `D` from `gas_price_history.parquet` (single number, daily granularity)
- Slice 24 hours of weather from `weather_hourly` (after TZ conversion, US/Eastern)
- Build a single DataFrame `hourly = pd.DataFrame(index=24h, columns=['lmp', 'gas_henry_hub', 'temp_f', ...])`

Display the resulting DataFrame so the reader sees the actual inputs for the day.

### §3.D — Compute hourly delivered fuel cost

This is where ADR-001 binds. Per Frame A:

```python
delivered_gas_usd_per_mmbtu = gas_henry_hub_daily  # same value all 24 hours
```

No basis. No daily shape (we don't have hourly gas; daily is fine for a thermal asset).

Add RGGI cost (CO2 allowance × emissions rate):

```python
# RGGI allowance price — model parameter, see §4 decision log
RGGI_USD_PER_SHORT_TON_CO2 = 17.0  # mid-range recent NYISO/RGGI clearing

# emissions rate from engineering / emissions data: 1,096.78 lb CO2/MWh (eGRID 2023)
# but applied per MMBtu of fuel: ~117 lb CO2 / MMBtu for natural gas (EPA standard)
RGGI_CO2_LB_PER_MMBTU_NG = 117.0

rggi_cost_per_mmbtu = (RGGI_CO2_LB_PER_MMBTU_NG / 2000) * RGGI_USD_PER_SHORT_TON_CO2

delivered_fuel_cost_per_mmbtu = delivered_gas_usd_per_mmbtu + rggi_cost_per_mmbtu
```

Show: at $17/short ton RGGI + 117 lb CO2/MMBtu, the RGGI adder is ~$1.00/MMBtu added to gas cost. At Henry Hub $3-5/MMBtu typical, RGGI is 20-33% of the delivered fuel cost — material.

### §3.E — Mode-specific spark spread per hour

Compute three parallel spark spreads — one per CCGT mode — using mode-specific heat rate from `operating_profile.yaml`:

```python
modes = {
    "3xCC_full": {"hr_btu_per_kwh": 8901, "capacity_mw": 221.3},
    "2xCC":      {"hr_btu_per_kwh": 9598, "capacity_mw": 170.0},   # approx 2 CT + ST
    "1xCC":      {"hr_btu_per_kwh": 10424, "capacity_mw": 120.0},  # approx 1 CT + ST
}

# VOM from tech-class defaults (per ADR Decision 2: same for CT/CA in CCGT block)
VOM_USD_PER_MWH = 1.02

# Spark per hour per mode
for mode, params in modes.items():
    hourly[f"fuel_cost_{mode}_usd_per_mwh"] = (
        params["hr_btu_per_kwh"] / 1000 * delivered_fuel_cost_per_mmbtu
    )
    hourly[f"spark_{mode}_usd_per_mwh"] = (
        hourly["lmp"] - hourly[f"fuel_cost_{mode}_usd_per_mwh"] - VOM_USD_PER_MWH
    )
```

Display: for each hour, show LMP and the three spark spreads. The reader sees how mode choice affects per-MWh margin.

### §3.F — Cogen host-steam constraint check

From `operating_profile.yaml.dhts`:
- Typical annual DHTS: ~80,000 MMBtu/yr
- 2024 dip: ~64,000 MMBtu/yr
- MOR-derived classification threshold: `dhts_threshold_mmbtu_per_day` = 50 MMBtu (`assumed_industry`, MEDIUM)

For our chosen day, we **don't have the actual DHTS reading** (it lives in the MOR data, not in our YAML — we only have aggregated stats). So Notebook 2's options:

| Option | Approach |
|---|---|
| **(i) Assume DHTS active** | Treat the chosen day as a host-demand day → must-run constraint fires |
| **(ii) Assume DHTS inactive** | Treat as a no-host-demand day → no must-run constraint |
| **(iii) Model both modes** | Compute dispatch under both assumptions, show the difference |

**Recommendation**: Option (iii). For one representative day, computing both modes and showing the contrast is exactly the kind of insight a single-day notebook should produce. The cogen constraint is non-trivial — making it visible matters.

**Encoding**: minimum-mode dispatch in the constrained case = whatever mode has duct-burner steam capacity (ST-only on duct-burner steam, ~78 MW). When constraint fires, plant must produce at least ST-only output regardless of spark.

### §3.G — Mode choice per hour

For each hour, pick the mode that maximizes spark margin × MW dispatched:

```python
def choose_mode(lmp_hour, modes, must_run=False):
    """
    Heuristic mode choice:
    - For each mode, compute hourly gross margin = max(0, spark) × capacity_mw
    - Pick the mode with highest gross margin
    - If must_run=True AND best-mode spark is negative, force minimum mode
    - If must_run=False AND all modes have negative spark, plant is OFF (mode = 'offline')
    """
    ...
```

Implementation notes:
- This is the **simplest heuristic** — no min-load enforcement, no startup cost amortization (those come in Notebook 3 + Notebook 4)
- Mode capacities are approximate — see §4 decision on capacity_mw per mode
- A more sophisticated version would compare gross margin not on capacity but on actual realized MW (considering min-load floors per generator)

Apply to all 24 hours, with must-run = False (or run the both-modes from §3.F).

Display: per-hour table showing `(hour, lmp, mode_chosen, gross_margin)`. Color-code or annotate where mode switches happen.

### §3.H — Clean vs degraded twin attribution

In Notebook 2, the plant has no degradation state (state evolution is Notebook 3). So `clean = degraded` for this notebook. But we set up the structure:

```python
spark_clean = compute_spark(hr=mode["hr_btu_per_kwh"], ...)
spark_degraded = spark_clean  # in N2; differs in N3 once state evolves

loss_degradation = spark_clean - spark_degraded  # = 0 in N2
```

This is the prototype's clean-vs-degraded twin attribution scaffolding (per `understanding_of_gas_turbine_digital_twin.md` §3.2). Notebook 3 adds real degradation.

### §3.I — Daily summary

Aggregate the 24-hour profile into a daily P&L:

| Field | Value |
|---|---|
| Day | YYYY-MM-DD |
| LMP mean / max | from §3.C |
| Henry Hub gas | $X/MMBtu |
| RGGI adder | $1.00/MMBtu |
| Mode hours: 3×CC / 2×CC / 1×CC / offline | counts |
| Total MWh dispatched | sum |
| Total fuel burn (MMBtu) | sum |
| Gross fuel cost | $X |
| RGGI cost | $X |
| VOM cost | $X |
| Total revenue | $X |
| **Gross margin** | $X (or P&L per MWh) |

This is the artifact other notebooks reference — a daily P&L that demonstrates the dispatch logic works.

### §3.J — (Optional) Compare to MOR observed for similar days

If our chosen day is in the 2021-2025 MOR window and we can extract the actual operating mode + generation from MOR (currently in diligence-extractor, not in our data spine), do a quick reality-check:

- Did Lockport actually run on the chosen day?
- What mode did it actually run in?
- How does our heuristic mode choice compare?

This is **optional** for v1 — the MOR daily data isn't in our spine. Note as a Notebook 3 / Phase L follow-up. If it turns out to be one cell of work, do it; otherwise defer.

### §3.K — Stage 1 findings

Markdown cell. Captures what we learned:

1. Mode-choice behavior — does the heuristic produce sensible mode switches?
2. RGGI cost magnitude — what fraction of fuel cost is it?
3. Cogen constraint difference — how much does must-run change daily output?
4. Anything surprising about the heat rate / VOM / RGGI / mode-choice interactions

These findings feed Notebook 3's plan.

### §3.L — Decision log

Conventions chosen during this notebook. Mirror Notebook 1's §J pattern.

---

## §4. Conventions chosen for this notebook (decision log)

Captured at the top so the reader sees them immediately. Major decisions for this notebook:

| Decision | Choice | Where applied | Rationale |
|---|---|---|---|
| Day picker | Programmatic — 2023 mid-week summer day in P75-P90 of daily peak LMP | §3.B | Reproducible; documented criteria; not hand-cherrypicked |
| Delivered gas formula | `delivered_gas = Henry_Hub_daily` (no basis, no RGGI inside gas) | §3.D | Per ADR-001 (Frame A) |
| RGGI allowance price | $17.0 per short ton CO2 (model parameter, configurable) | §3.D | Mid-range recent RGGI clearing 2024-2025; documented as `assumed_industry` MEDIUM confidence |
| CO2 emissions rate for natural gas | 117 lb CO2 per MMBtu (EPA standard for pipeline gas) | §3.D | EPA AP-42 / IPCC standard |
| Mode capacity_mw | 3×CC=221.3, 2×CC=170, 1×CC=120, offline=0 | §3.E, §3.G | 3×CC matches engineering.yaml plant total. 2×CC ≈ 2×47 + 78 = 172; rounded to 170. 1×CC ≈ 1×47 + 78 = 125; rounded to 120. **Approximate** — refine in Notebook 3. |
| Mode choice heuristic | Max(max(spark, 0) × capacity_mw) per hour | §3.G | Simplest defensible — no min-load enforcement, no startup cost amortization (Notebook 3) |
| VOM | $1.02/MWh constant from tech_class_defaults | §3.E | Per dispatch_params lookup Kumar 2012 row for (CT, <2000, F). Note: cogen markup NOT applied in N2 — deferred to Notebook 3 along with state evolution. |
| Clean vs degraded | Identical in N2 (no state evolution) | §3.H | Structural scaffolding; full attribution in Notebook 3 |
| Cogen constraint | Compute both must-run-yes and must-run-no for the day, show contrast | §3.F | Don't know the day's DHTS; surfacing the constraint impact is the goal |
| Dual-fuel switching | Not modeled in N2 | implicit | Per ADR-001: Henry Hub never crosses oil threshold; no switching event possible in v1 |
| Min-load enforcement | Not enforced in N2 (each mode is "run at capacity_mw if economic") | §3.G | Defer to Notebook 3 where state evolution makes min-load matter |
| Startup cost | Not modeled in N2 (single-day, plant assumed already on at start of day) | implicit | Daily commitment / startup attribution is multi-day concept; Notebook 3 |
| Ambient derate | Not modeled in N2 (use nameplate capacity) | implicit | Ambient sensitivity is real per engineering.yaml but adds complexity; document as Notebook 3 follow-up |
| Output bundle | Optional write to `data/outputs/lockport/runs/notebook2_<day>/` if useful | §3.I | Gitignored per consolidation plan §4.2 |

---

## §5. Validation checks (acceptance criteria)

Notebook is "done" when:

- [ ] §3.A setup runs without errors
- [ ] §3.B picks a single date with documented criteria; date is reproducible from the seed/criteria
- [ ] §3.C produces a 24-row DataFrame with non-null LMP, gas, weather
- [ ] §3.D computes per-mode fuel cost and per-mode spark spread
- [ ] §3.E displays the 24-hour mode-comparison table
- [ ] §3.F handles the cogen constraint correctly (or shows both modes)
- [ ] §3.G mode choice produces sensible mode switches (no whipsawing 1×↔3× back and forth every hour)
- [ ] §3.H clean-vs-degraded scaffolding present (even if both equal)
- [ ] §3.I daily summary shows: total MWh, gross margin, mode-hour counts, all reasonable
- [ ] §3.K Stage 1 findings cell is filled in
- [ ] §3.L Decision log records the conventions used
- [ ] No cells crash on re-run from a fresh kernel

**Sanity checks** (sub-acceptance):

- Daily MWh dispatched ≤ 221.3 × 24 = 5,311 MWh (plant max output × 24 hours)
- Gross margin sign matches the daily LMP/gas relationship (if LMP > $40/MWh average and gas at $4/MMBtu, gross margin should be positive)
- Mode choice is "stickier" than alternative — if all 24 hours have positive 3×CC spark, the model picks 3×CC for all 24 (no senseless switching)

---

## §6. What this notebook surfaces

Inputs to Notebook 3's plan. After Notebook 2 runs, we should know:

| Question | How N2 answers it |
|---|---|
| Does mode choice work cleanly across an hourly profile? | §3.G output — visual inspection of mode switches |
| How big is RGGI as a fraction of fuel cost? | §3.D output — $/MMBtu and % |
| Does cogen constraint materially change daily output? | §3.F output — compare both modes |
| Are the mode capacity_mw approximations reasonable? | §3.I total MWh sanity check |
| Where does the clean-vs-degraded twin attribution scaffolding live in code? | §3.H — Notebook 3 inherits |
| What's the daily P&L look like? | §3.I — defines the structure for Notebook 4 |
| Is the assumption-tracking discipline ergonomic in dispatch code? | All cells — verbose `v(...)` access pattern, do we want a wrapper class for Notebook 3? |

---

## §7. What this notebook does NOT cover

- **Multi-day state evolution.** Notebook 3 adds EOH, stress accumulators, capacity degradation, heat rate drift, forced outage probability.
- **Startup costs.** No transition events in a single-day notebook.
- **Min-load enforcement.** Notebook 3 with multi-day daily loop.
- **Maintenance scheduling / inspection events.** Notebook 4.
- **Mode A/B/C policy curves.** Notebook 4 — these are multi-day strategic choices.
- **LTSA cost streams.** Notebook 4.
- **Forced outage simulation.** Notebook 3 (probability calc) + Notebook 4 (event sampling).
- **Capacity market revenue (NYISO ICAP).** Out of v1 per consolidation plan §5 D4.
- **Dual-fuel switching.** Per ADR-001, never fires in v1 with Henry Hub.
- **Ambient derate.** Real but deferred to Notebook 3 to keep N2 focused.
- **Cogen VOM markup.** Real but deferred to Notebook 3 with full cogen handling.
- **Multi-path Monte Carlo.** Phase L.

---

## §8. How this informs Notebook 3

Notebook 3 ("Daily loop — state and feedback") expects:

1. **A working hourly dispatch function** — Notebook 3 wraps the §3.E-G logic in a function and calls it day-by-day for ~30 days
2. **Clean-vs-degraded structure in place** — Notebook 3 evolves the degraded path while the clean path stays as the prototype's reference (per the understanding doc §3.2 twin attribution)
3. **Day-end state inputs** — Notebook 3 needs to know what hourly variables matter for state evolution (fired hours, starts, EOH burn). Notebook 2's §3.G output should hint at these.
4. **Mode-switching pattern** — does Notebook 2 produce realistic mode switches? If yes, Notebook 3 inherits. If no (whipsawing), Notebook 3 adds mode-stickiness logic.
5. **Cogen handling pattern** — Notebook 3 should encode the must-run constraint properly with day-level DHTS data (when we get it from MOR; currently the constraint is "both modes shown")

After Notebook 2 runs, the open questions narrow. Notebook 3's plan gets written informed by what we actually saw in Notebook 2's outputs.

---

## §9. Open questions to resolve during execution

These get answered as Notebook 2 runs; their resolution shapes Notebook 3's plan.

| Question | How it gets answered |
|---|---|
| **Day picker outcome**: which specific 2023 date does the heuristic land on? Does its profile look "normal"? | §3.B output |
| **Mode capacities**: are 170 MW for 2×CC and 120 MW for 1×CC defensible, or do we need to derive them from `engineering.yaml` per-generator data? | §3.I total MWh sanity check + Notebook 3 refinement |
| **RGGI sensitivity**: at $17/ton, is RGGI material? At $30/ton would it change mode choice? | §3.D + a brief sensitivity sub-cell in §3.I |
| **Cogen constraint magnitude**: in §3.F's "both modes" comparison, what's the daily margin difference between must-run-yes and must-run-no? | §3.F output |
| **Mode-switch frequency**: does the heuristic produce excessive switching (1× → 3× → 1× every few hours)? If yes, we need stickiness in Notebook 3. | §3.G output |
| **VOM cogen markup**: do we need to apply +30-50% in Notebook 2, or defer to Notebook 3 with full state-aware logic? | §3.K findings — depends on whether N2's gross margin looks right vs MOR-derived expectations |

---

## §10. Risks / things that could go wrong

| Risk | Mitigation |
|---|---|
| Day picker lands on an outage day (zero LMP, dispatch impossible) | Add a sanity check: chosen day must have non-null LMP every hour |
| Henry Hub daily price missing for chosen day | Re-pick from a nearby day; document the substitution |
| RGGI cost factor wrong (lb CO2/MMBtu) | Cross-check against EPA AP-42 and engineering.yaml.plant emissions data |
| Gross margin negative for the entire day → mode = offline 24 hours | Notebook still runs; shows what the dispatch decision was; not a bug |
| Mode capacities don't match engineering.yaml summed | Acceptable approximation for N2; refine in N3 |
| Cogen "both modes" comparison produces unstable results | Plot both, document the comparison; the contrast itself is the insight |

---

## §11. Output artifacts

- The notebook itself (`notebooks/02_one_day_dispatch.ipynb` paired with `02_one_day_dispatch.py` via jupytext)
- Optional: `data/outputs/lockport/runs/notebook2_<day>/hourly.parquet` — the 24-row daily output bundle (gitignored)
- Stage 1 findings + decision log updates to this plan doc — if any conventions change

---

## §12. Reference

- **Parent plan**: [`../../consolidation_plan.md`](../../consolidation_plan.md) §8 Phase H
- **Notebook 1 plan**: [`01_data_spine_load_validate.md`](./01_data_spine_load_validate.md)
- **Notebook 1 itself**: [`../../../../notebooks/01_data_spine_load_validate.ipynb`](../../../../notebooks/01_data_spine_load_validate.ipynb)
- **ADR-001 (gas hub treatment)**: [`../../../decisions/001-gas-hub-treatment-v1.md`](../../../decisions/001-gas-hub-treatment-v1.md)
- **Assumption status taxonomy**: [`../../../assumptions/status_taxonomy.md`](../../../assumptions/status_taxonomy.md)
- **Placeholder caveats** (LTSA): [`../../../assumptions/placeholder_caveats.md`](../../../assumptions/placeholder_caveats.md)
- **Caveats** (Lockport modeling): [`../../../../data/assets/lockport/caveats.md`](../../../../data/assets/lockport/caveats.md)
- **Step 2 plan** (broader execution blueprint for dispatch): [`../../step_2_execution_blueprint_plan.md`](../../step_2_execution_blueprint_plan.md) — Notebook 2 prototypes the dispatch logic that becomes §3.E and §3.G of the eventual `src/dispatch/` module
- **Understanding doc** (prototype reader's guide): [`../../../extra/understanding_of_gas_turbine_digital_twin.md`](../../../extra/understanding_of_gas_turbine_digital_twin.md) §3.2 (twin attribution), §3.3 (LTSA cost streams not in N2)

---

## §13. Suggested execution sequence

When ready to build the notebook:

1. **Write `notebooks/02_one_day_dispatch.py`** following §3 cell-by-cell sketch
2. **Run it as a Python script** to verify execution end-to-end (catches Python 3.9 typing issues etc. — Notebook 1 caught one)
3. **Convert to `.ipynb`** via `jupytext --to ipynb 02_one_day_dispatch.py` (same workflow as Notebook 1)
4. **Execute with nbclient** to embed outputs (matches Notebook 1 workflow)
5. **Review outputs** — especially §3.G mode choice, §3.F cogen comparison, §3.I daily summary
6. **Update this plan** with Stage 1 findings if any conventions changed during execution
7. **Update consolidation plan §13 status log** with Phase H completion summary
8. **Write Notebook 3 plan** informed by Notebook 2's findings
