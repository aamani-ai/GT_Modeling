# `docs/discussion/`

> **What this folder is**: a working space for *open exploration* of concepts, frameworks, and modeling ideas before they crystallize into committed methodology.
>
> **What it is not**: ADRs (those live in `docs/decisions/`) or finalized methodology (that lives in `docs/methodology/`).

---

## Why this folder exists

There is a real distinction between three kinds of writing in this repo:

| Folder | Status of content | Purpose |
| :--- | :--- | :--- |
| `docs/discussion/` | *Pre-decision exploration* | "Here is a concept we're trying to think through — what could it mean, what are the nuances, what should we be careful about?" |
| `docs/decisions/` | *Substantive decisions made* | ADR format: "We chose X over Y because Z. Downstream consequences are A, B, C." |
| `docs/methodology/` | *Committed approach we are executing on* | The model architecture, the daily loop, the routing taxonomy. Things the build is rooted in. |

Without this separation, two failure modes are common:

1. **Premature crystallization** — concepts get baked into methodology before they're sufficiently understood. The methodology doc reads as if the team has committed; in reality the concept is still being explored. Misleading.
2. **Discussion lost in chat** — important exploratory thinking happens in conversations and is never written down, so the team has to re-derive it months later when someone asks "wait, what did we mean by *regime* again?" Wasteful.

The discussion folder addresses both by giving exploration its own home, separate from methodology.

---

## What goes in a discussion doc

Each discussion doc explores **one concept, framework, or proposed modeling pattern** that is being worked out. The format is open — exploration is messy — but a good discussion doc typically covers:

- **What we mean by the concept** — definition, scope, distinctions from related concepts already in our vocabulary
- **Why we think it matters** — the gap it fills, the question it answers
- **Nuances** — edge cases, terminology overlaps, things that are easy to misread
- **Drawbacks / costs** — what gets harder if we adopt this; what we might be giving up
- **Open questions** — things we don't yet know but will need to know before committing
- **What "committed" would look like** — if we eventually decide this is real, what gets added to methodology, what gets built in the code, what gets recorded as an ADR

Discussion docs are not required to resolve their own questions. They are required to make the questions explicit.

---

## How a discussion doc graduates (or doesn't)

A discussion doc can have three outcomes:

1. **Graduates to methodology** — the concept becomes a committed approach. The methodology doc absorbs the relevant content; an ADR is written if there was a substantive choice; the discussion doc stays as the *exploration record* (marked as graduated).
2. **Graduates to ADR but not methodology** — the discussion produced a specific decision (e.g., "we will not adopt this concept because…") that warrants an ADR but doesn't need a methodology change.
3. **Stays open** — the concept is interesting but we haven't matured it enough to decide. The doc keeps evolving in the discussion folder.

A discussion doc never disappears; it gets one of the three labels above so its status is visible.

---

## Naming convention

Numbered prefix + concept name:

```
docs/discussion/01_regime_concept.md
docs/discussion/02_regime_inference_methods.md   (future)
docs/discussion/03_<next_concept>.md             (future)
```

Numbering is sequential by creation order, not by priority. This keeps the folder browsable in chronological order, which is usually what you want for exploration material.

---

## Current discussion docs

| # | Concept | Status |
| --: | :--- | :--- |
| 01 | Regime as a higher-level concept (business positioning) — distinct from operating mode, policy mode, *and* load level | Open |
| 02 | Load level as a missing dimension (continuous intensity within operating mode) | Open |
| 03 | The four concepts vocabulary cheatsheet (regime + policy mode + operating mode + load level on a 2×2 axis layout) | Reference (low-stakes, supports 01 and 02) |
| 04 | Industry vocabulary mapping + concept-by-concept reality check + curated reference list + recommended reading sequence | Reference (validation; updated as references / refinements emerge) |

---

## Cross-reference

- `docs/decisions/` — ADRs once decisions are made
- `docs/methodology/` — committed methodology that's being executed against
- `docs/methodology/extra/` — analytical companions to methodology (positioning, decomposition lenses, etc.)
- `/Users/divy/Desktop/Learning/Modeling/framing_a_modeling_problem.md` — the upstream generic discipline for what to scope before modeling (not in this repo; lives in the personal Learning knowledge base)
