# Parameter Calibration & Defensibility Plan (pre-v2)

> **Status**: Planned (2026-05-27) — captured now, executed later (partly data-gated). The deliberate process for moving the model's constants from *unsourced placeholders* to *defensible numbers*.
>
> **Why this exists**: the engine's *mechanisms* are well-documented (see `methodology/wear_mechanics.md`, `dispatch_economics.md`, `outage_mechanics.md`), but its *numbers* are mostly `assumed_industry` LOW (Athens / generic-F-class placeholders, ADR-002). Every headline conclusion (Net P&L, the over-commit, the forward distribution) is only as defensible as those constants. This is the credibility backbone — and should be done **before v2 goes to anyone**.
>
> **This is not new scope** — it operationalizes ADR-002's Bucket-B/C inventory + `gaps_and_priorities.md` #1 (data-room LTSA) and #8 (per-asset Bucket-B calibration). What was missing is making it a *tracked, prioritized process*.

---

## §1. The principle — prioritize by impact, don't blanket-sweep

There are ~30+ constants; most barely move *Lockport's* outputs (its GT-side hazards are sub-threshold; HRSG/BG baselines + aging dominate its outages). Effort follows impact:

> **Step 0 = sensitivity-rank.** A quick local sweep (or the prototype tornado — which flagged the **aging / `P_BG` multiplier** as the dominant driver, plus **TBC η**, **fatigue-per-start**, **fouling tau/asymptote**, **inspection thresholds/costs**) decides *which* numbers to invest in. Leave the inert ones flagged.

> **High-impact target — initial condition & aging anchoring** (flagged 2026-05-27): the historical run starts from a *modeling-convention* state (`EOH=24,000`, `rotor=0.35`, hot-section damage = 0 — "fresh off an HGP, mid-clock") and clocks the **aging multiplier from sim-start (2017), not the 1992 vintage**. Neither is calibrated to Lockport's *actual* 2017 condition, and both are **first-order**: the initial EOH directly sets *when inspections fire* (the dominant LTSA cost — the MI fires ~2025 only because EOH starts at 24k and accrues to the 48k threshold), and the aging multiplier is the #1 sensitivity driver. **Fix**: set the 2017 initial state from the asset's real last-overhaul / accumulated-EOH history (MOR/data-room), and anchor aging to 1992. *Until then, these are explicit assumptions — and good candidates to expose as dashboard knobs (see `dashboard_plan.md`).*

## §2. The goal — "sourced/justified," not "the true value"

For a specific 1992 plant the *true* physical value is often unknowable. The achievable goal is to move each high-impact constant from **"unsourced placeholder"** to **"here's its source / what it's calibrated to / how sensitive the answer is."** Tiered:

| Tier | Source | Status earned |
|---|---|---|
| **1 — measured** | the asset's own **MOR / data room / GADS / SCADA** (real EFOR, real LTSA intervals + costs, observed HR-degradation) | `real_observed` / `real_reported` |
| **2 — vendor / literature** | OEM specs (GER-3620, TBC curves), published F-class data, the **Friday load-temp paper**, Kumar 2012 — *cited* | `assumed_vendor` / `assumed_industry` (with a reference) |
| **3 — calibrated** | when neither exists: **tune to a known target** — wear rates so modeled EOH→MI timing matches the contract MI interval; `P_forced` so modeled **EFOR matches MOR/GADS** | `assumed_derived` (calibration target recorded) |

## §3. The artifact — a parameter-provenance / calibration register

A single table (lives in `docs/assumptions/`, the per-leaf value-provenance home; seeds from `wear_mechanics.md` §7 constants + ADR-002 buckets):

```
constant · current value · status · source · sensitivity rank · defensibility target · blocked-on · owner
```

It makes visible, at a glance: what's **doable now** (literature + calibrate-to-MOR) vs **blocked** (data room / Friday paper).

## §4. Sequence (when executed)

1. **Sensitivity-rank** the constants (cheap; reuse the Phase-L sweep machinery or a local sweep).
2. **Build the register** (status + source + rank + target for each).
3. **Upgrade the high-impact, data-available ones now** — literature/vendor (cited) + calibrate-to-MOR (EFOR, inspection timing).
4. **Close the rest as data lands** — D2 data-room (LTSA terms/costs, gap #1), the Friday paper (ambient/load wear coefficients, ADR-006/007), MOR depth.
5. **Re-run** + update the model-card's assumption-status distribution (it already reports the real_* vs placeholder split).

## §5. Gating & timing

- **Doable now**: sensitivity rank, the register, literature/vendor citations, calibrate-to-MOR (EFOR + inspection timing).
- **Blocked on data**: LTSA monetary terms (data room, #1), ambient/load coefficients (Friday paper), some EFOR detail (GADS).
- **Target**: the **high-impact** constants defensible **before v2 / before sharing**; the inert ones can stay flagged with status + sensitivity. The register tracks the boundary.

## §6. Cross-references
- [ADR-002](../decisions/002-lockport-specific-vs-generic-calibration.md) — the 3-bucket calibration inventory (A real / B generic placeholder / C data-room)
- [`gaps_and_priorities.md`](../methodology/gaps_and_priorities.md) #1 (data-room LTSA), #8 (per-asset Bucket-B calibration)
- [`assumptions/status_taxonomy.md`](../assumptions/status_taxonomy.md), [`assumptions/placeholder_caveats.md`](../assumptions/placeholder_caveats.md) — the status grammar this upgrades
- [`methodology/wear_mechanics.md`](../methodology/wear_mechanics.md) §7–§8 — the constants + their current (placeholder) status
- [`00_strategic_spine.md`](00_strategic_spine.md) — where this sits relative to the phases
