# Decision Log (ADRs)

> Architectural Decision Records — one Markdown file per substantive decision, with the **full reasoning trail** preserved. The point isn't just the answer; it's the discussion that got us there and the alternatives considered.

## Why this folder exists

We've already made several substantive decisions during the gt_models build (the consolidation plan §5 captures five of them). As the model build progresses, more analytical decisions will come up — gas basis treatment, RGGI allowance modeling, ICAP capacity revenue inclusion, dispatch optimization vs heuristic, etc.

Without a place to capture *why we picked X over Y*, future-self (or another team member) loses the reasoning and re-litigates settled questions. ADRs prevent that.

## What goes here vs elsewhere

| Where | What |
|---|---|
| `docs/plans/consolidation_plan.md` §5 "Decisions Locked" | Architectural foundation decisions made up-front (folder shape, repo boundaries, prototype-as-reference, etc.) |
| `docs/plans/consolidation_plan.md` §13 status log | Phase completion / status updates |
| `data/.../README.md` provenance sections | Data refresh discipline (which version copied when) |
| `data/.../caveats.md` | Modeling caveats baked into the data (cogen markup, EIA clustering, etc.) |
| **`docs/decisions/NNN-topic.md`** (this folder) | **Substantive decisions made during execution** where there was a real choice between alternatives with trade-offs |

ADRs are for "we had a real choice and here's how we picked." Not for routine implementation choices.

## When to write an ADR

A new ADR is justified when:

1. **There's a real choice** with non-trivial alternatives (≥2 viable options)
2. **The choice has downstream consequences** (affects more than one file or one phase)
3. **The reasoning involves tradeoffs** that future readers need to understand
4. **It's the kind of decision someone might later question** and ask "why did we do it this way?"

A new ADR is NOT needed for:
- One-line typos and obvious bug fixes
- Pure-implementation choices with no real alternative
- Decisions already captured in consolidation plan §5

## Naming convention

`NNN-short-topic-name.md` — three-digit zero-padded sequential number, hyphen-separated topic.

Examples:
- `001-gas-hub-treatment-v1.md`
- `002-rggi-allowance-modeling.md`
- `003-capacity-market-inclusion.md`

Numbers are assigned in order of creation, never renumbered.

## ADR template

Each ADR follows this structure:

```markdown
# ADR NNN: <Title>

**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date**: YYYY-MM-DD
**Decision-maker(s)**: <who>
**Affects**: <phase, code, data area>

## Context

<What's the situation? What forced this decision? What did we discover?>

## Decision

<The 1-2 sentence answer. What we chose to do.>

## Reasoning

<The full argument. Show your work. Why this answer and not the alternatives?>

## Consequences

### Positive

<What this enables / fixes>

### Negative / accepted tradeoffs

<What this gives up. What limitations the decision introduces.>

### Mitigations / follow-up actions

<How we handle the negative consequences. Often a future ADR or v2 task.>

## Alternatives considered

<Each option that was on the table, with why it was rejected.>

## References

<Links to related docs, prior decisions, data files, conversations.>
```

## Status semantics

| Status | Meaning |
|---|---|
| `Proposed` | Under discussion; not yet committed to the codebase |
| `Accepted` | Decided + reflected in code/data. The default once we move forward. |
| `Deprecated` | No longer applies. Kept for reasoning trail; no longer followed. |
| `Superseded by ADR-XXX` | Replaced by a later decision. Original ADR stays as record. |

When an ADR is superseded, **do not delete it.** Mark its status as superseded and link to the replacement. The reasoning trail is the value.

## Prior decisions (not in this folder)

These were made before this folder existed. They're captured elsewhere but worth knowing about:

| Decision | Where it lives |
|---|---|
| Five locked decisions for gt_models architecture (D1–D5) | [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) §5 |
| Notebook-first sequencing (Phases G–J as notebooks, K as graduation) | [`../plans/consolidation_plan.md`](../plans/consolidation_plan.md) §8 + §13 status log |
| PJM Manual 15 publishes no defaults → Kumar 2012 primary | [`../../data/tech_class_defaults/refs/AUDIT.md`](../../data/tech_class_defaults/refs/AUDIT.md) "Headline finding" section |
| LTSA values are placeholders pending data room extraction | [`../assumptions/placeholder_caveats.md`](../assumptions/placeholder_caveats.md) §1 |

If any of these get revisited or refined, the new decision earns an ADR here.

## Index of current ADRs

| # | Title | Status | Date | Affects |
|---|---|---|---|---|
| [001](./001-gas-hub-treatment-v1.md) | Gas hub treatment for v1 dispatch model | Accepted | 2026-05-14 | Phase H (Notebook 2) onwards |
| [002](./002-lockport-specific-vs-generic-calibration.md) | Lockport-specific vs Generic F-class — calibration inventory | Accepted | 2026-05-14 | N1–N3 retroactively + N4+ forward |
