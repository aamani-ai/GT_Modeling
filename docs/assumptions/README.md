# docs/assumptions/ — Assumption-tracking discipline

> The home of the assumption-tracking schema. Per [consolidation plan §6](../plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle) — non-negotiable.

## Why assumption tracking is a first-class concern

The model produces P10/P50/P90 outputs that someone will use to commit capital. The defensibility of those outputs depends entirely on whether every input can be traced back to a source — and whether stakeholders can distinguish *observed* values from *assumed* values from *placeholders waiting on extraction*.

Mixing real and assumed numbers without tracking is the single biggest way the model becomes uncredible. So we don't mix them silently — every value in `data/assets/<asset>/*.yaml` carries metadata: `status`, `source`, and (for assumed values) `confidence`.

The discipline was proven at scale by the renewablesinfo dispatch_params lab pass (2026-05-08): 144 cells, each with status + source + confidence + cross-check, distribution explicitly reported (11 HIGH / 40 MEDIUM / 74 LOW / 19 NoSource). The same discipline applies here.

## Files

| File | What it is |
|---|---|
| `README.md` | This file |
| `status_taxonomy.md` | The 9 status codes with definitions, examples, and disclosure rules |

## Where assumption metadata lives

| Location | Use |
|---|---|
| `data/assets/<asset>/*.yaml` leaf values | Per-value metadata: `{value, status, source, confidence?, caveat?}` |
| `data/outputs/<asset>/runs/<run_id>/model_card.md` | Per-run summary: distribution of statuses, list of LOW-confidence values, list of pending placeholders |
| `docs/assumptions/status_taxonomy.md` | The taxonomy reference (this folder) |

## Status quick reference

| Status | One-line meaning |
|---|---|
| `real_observed` | Measured from this plant's own operating data |
| `real_reported` | Reported by this plant in regulatory or contractual filings |
| `real_computed` | Derived deterministically from `real_*` values |
| `assumed_techclass` | Tech-class default from public methodology references |
| `assumed_vendor` | Vendor literature for the specific model |
| `assumed_industry` | Industry-typical with no canonical public source |
| `assumed_derived` | Derived from other assumed values (compounds uncertainty) |
| `placeholder` | Waiting on a known-pending source extraction |
| `not_applicable` | Field in schema doesn't apply to this asset |

Full definitions + examples + disclosure rules: [status_taxonomy.md](./status_taxonomy.md).

## Confidence (for assumed values)

| Confidence | Meaning |
|---|---|
| `HIGH` | Cross-validated by ≥2 primary sources within ±20% |
| `MEDIUM` | Single primary source, no cross-validation; or extrapolated within tech class |
| `LOW` | Single low-quality source (vendor marketing, single academic study, undocumented industry default) |

## The model_card discipline

Every simulation run produces a `model_card.md` in `data/outputs/<asset>/runs/<run_id>/`. It summarizes:

1. **Data vintages** — refresh dates of every input artifact
2. **Assumption-status distribution** — count by code, percent real vs assumed vs placeholder
3. **LOW-confidence values flagged** — field paths + values + what they affect
4. **Placeholders pending** — what's not yet real, where the real value comes from

Per consolidation plan §10 anti-patterns: **"Don't run a model and call it valid because it doesn't crash."** Phase L acceptance requires the model_card to explain which results depend most on assumed vs real values.

## See also

- [consolidation plan §6](../plans/consolidation_plan.md#6-assumption-tracking-schema-first-class-principle) — the full discipline rationale + YAML format examples
- [status_taxonomy.md](./status_taxonomy.md) — the reference taxonomy
- [data/assets/README.md](../../data/assets/README.md) — where assumption metadata gets applied
- renewablesinfo dispatch_params AUDIT.md (precedent): `~/code/personal/renewablesinfo/integration/dispatch_params/AUDIT.md`
