# 03. The Four Concepts Vocabulary — A Cheatsheet

> **Status**: Cheatsheet / vocabulary anchor. Lower-stakes than 01 and 02 — its job is to give a single reference for *which concept is which* when conversations get confused. References the two open discussions but doesn't re-litigate them.
>
> **Folder context**: This is a discussion doc (per `docs/discussion/README.md`). It is *meta*-discussion in the sense that it organizes the vocabulary used in the other discussion docs and across the project.

---

## §1. Why this doc exists

The project has, at this point in its life, four distinct concepts that all sound similar in casual conversation:

- **Regime**
- **Policy mode** (sometimes shortened to "mode A/B/C")
- **Operating mode** (sometimes shortened to "3xCC / 2xCC / 1xCC mode")
- **Load level** (sometimes referenced implicitly as "running hard" or "throttled")

Without a clean vocabulary map, these collide in ways that have already caused real confusion (see [`01_regime_concept.md`](01_regime_concept.md) §3 for the cleanup history). This doc is the *single place to land* when a reader needs to know which is which.

This is a **cheatsheet, not an exploration**. The substantive discussion lives in [`01_regime_concept.md`](01_regime_concept.md) and [`02_load_as_a_dimension.md`](02_load_as_a_dimension.md); this doc consolidates the result.

---

## §2. The 2×2 framing

```
                   SLOW-CHANGING (posture / strategic / weeks-to-seasons)
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                                                      │
        REGIME                                                POLICY MODE
   "What is the plant                                  "How does the operator
    doing in the market?"                              manage wear vs revenue?"
   ──────────────────────                              ──────────────────────
   Business positioning                                Wear-management posture
                                                       (modeling abstraction)
   Examples:                                           Examples:
    ▸ baseload                                          ▸ A — run hard
    ▸ peaker / load-follower                            ▸ B — balanced
    ▸ frequency regulation                              ▸ C — preserve wear
    ▸ cogen (DHTS-driven)
    ▸ must-run contractual
            │                                                      │
            └─────────────────────────┬────────────────────────────┘
                                      │
                                      │ jointly condition the parameters of
                                      ▼
                FAST-CHANGING (tactical / hour-by-hour)
                                      │
            ┌─────────────────────────┼────────────────────────────┐
            │                                                      │
       OPERATING MODE                                       LOAD LEVEL
   "Which physical config                              "What intensity within
    is firing right now?"                              the chosen config?"
   ──────────────────────                              ──────────────────────
   Categorical                                         Continuous
                                                       (% of mode max)
   Examples:                                           Examples:
    ▸ 3×CC                                              ▸ 100% (full load)
    ▸ 2×CC                                              ▸ 70%  (mid-merit)
    ▸ 1×CC                                              ▸ 50%  (min stable)
    ▸ offline                                           ▸ peak fire (over)
            │                                                      │
            └─────────────────────────┬────────────────────────────┘
                                      │
                                      ▼
                              OPERATING POINT
                          = (mode, load) tuple per hour
                            — the realized hour-by-hour
                              dispatch decision
```

Two axes, two concepts per axis, four concepts total.

---

## §3. Compact reference table

| Concept | Question it answers | Type | Cadence | Status in gt_models |
| :--- | :--- | :--- | :--- | :--- |
| **Regime** | What is the plant *doing* in the market? | Categorical (or vector) | Slow (weeks–seasons) | Discussion (`01_regime_concept.md`) |
| **Policy mode** (A/B/C) | How aggressively is the operator managing wear vs revenue? | Categorical | Static per simulation | Committed (`architecture.md` §5.5) |
| **Operating mode** (3×CC / 2×CC / 1×CC) | Which physical configuration is firing? | Categorical | Hour-by-hour | Committed (`architecture.md` §5.3) |
| **Load level** | What fraction of mode max is being produced? | **Continuous** | Hour-by-hour | Discussion (`02_load_as_a_dimension.md`) |

Two committed, two in discussion. The two in discussion are *coupled* — any ADR for one should be aware of the other.

---

## §4. Common confusions and how to resolve them

| If the conversation says... | They probably mean... | The right disambiguation |
| :--- | :--- | :--- |
| "Mode A" or "Mode C" | **Policy mode** | Specify "policy mode A/B/C" |
| "3×CC mode" or "1×CC mode" | **Operating mode** | Specify "operating mode 3×CC" or just "3×CC configuration" |
| "Peaker mode" or "baseload mode" | **Regime** | Specify "peaker regime" (don't say "peaker mode") |
| "Running hard" or "throttled" | **Load level** | Specify "load at 100%" or "load at 60%" |
| "Operating point" | **(mode, load) tuple** | This is the only term that already names the right tuple — keep using it |

**Rule of thumb**: if you find yourself saying "mode" without a modifier, you're being ambiguous. Add the qualifier (policy / operating) or use the right concept name (regime / load level).

---

## §5. How the four concepts interact

A short, structural account — full discussion is in the two source docs.

### 5.1 Posture conditions tactics

Regime and policy mode (slow / posture) **jointly condition** the parameters of operating mode and load (fast / tactical). Specifically:

- **Regime → typical load patterns**: peaker regime → max-when-running; baseload → steady high; frequency-reg → swinging; cogen → demand-dictated. Regime sets the *distribution* of load levels you'd expect.
- **Regime → typical mode pick**: cogen regime usually 1×CC at low LMP; baseload regime usually 3×CC; peaker regime usually 3×CC when running, offline otherwise.
- **Policy mode → wear-penalty hurdle on starts**: in our model, Mode A imposes no hurdle; Mode C imposes a steep one near EOH thresholds. This conditions which starts get taken at the operating-mode-pick stage.
- **Policy mode → load-level preference (potential)**: a Policy C operator might prefer 80% load over 100% load even when 100% is economic — a wear preference manifesting at the load axis. The current model doesn't capture this, but a load-aware future model could.

### 5.2 The two posture concepts are independent

A plant can be in **any combination** of regime + policy mode:

- Peaker regime + Policy A — runs hard when prices spike, ignores accumulated wear
- Peaker regime + Policy C — runs only when spike *and* EOH headroom is comfortable
- Baseload regime + Policy A — high CF, take inspection hits when they fall
- Baseload regime + Policy C — high CF but skip marginal starts that would push EOH past favorable shoulder windows

All four combinations are real and produce different outcomes.

### 5.3 The two tactical concepts also interact

Operating mode and load level are not independent — they are *nested*:

- Operating mode is the *outer* choice (which CTs are firing)
- Load level is the *inner* choice (how hard, given the chosen configuration)

At any hour, the dispatch decision is the joint *(mode, load)* tuple. The model today does mode-pick at 100% load implicitly; a load-aware model would let load vary continuously within each mode's envelope.

### 5.4 What the operator actually decides

Of the four concepts, the operator *directly chooses* two:

- **Operating mode** — yes, hour-by-hour
- **Load level** — yes, hour-by-hour (within constraints)

The other two are *characterizations* of the operator's pattern of choices over time:

- **Regime** — inferred from observed operating-mode and load patterns (and contract structure)
- **Policy mode** — inferred from the wear–revenue trade-offs visible in the operator's choices

This is why **regime and policy mode are latent variables** (per `extra/performance_and_risk_framework.md` §3 and `01_regime_concept.md` §5.1), while operating mode and load are *direct decisions*.

---

## §6. Where each concept is documented

| Concept | Primary doc | Supporting docs |
| :--- | :--- | :--- |
| **Regime** | [`01_regime_concept.md`](01_regime_concept.md) | This doc; `modeling_flow.md` §3 |
| **Policy mode** | `architecture.md` §5.5; `dispatch_mechanics.md` | `extra/forward_looking_framing.md`; `extra/performance_and_risk_framework.md` §3 |
| **Operating mode** | `architecture.md` §5.3; `dispatch_mechanics.md` | `pnl_ledger.md` (where mode HRs are referenced) |
| **Load level** | [`02_load_as_a_dimension.md`](02_load_as_a_dimension.md) | This doc; `extra/performance_and_risk_framework.md` §4.6 (part-load HR polynomial) |

Two concepts are committed (policy mode, operating mode) and live in methodology. Two are in discussion (regime, load level) and live here in `docs/discussion/`.

---

## §7. When this cheatsheet will need to be updated

This is a vocabulary doc; it should be small and stable. Update it when:

- **A new concept enters the vocabulary** — e.g., if "operating point" becomes a first-class concept rather than just a tuple, that's a fifth concept and this doc needs to expand
- **A discussion graduates to methodology** — the "Status in gt_models" column in §3 needs updating; some "Discussion" entries will become "Committed"
- **An ADR is written** that affects vocabulary — e.g., the ADR for regime might rename it or refine its scope

Do *not* update this doc for:

- Routine refinements to the discussion docs
- Implementation changes that don't affect vocabulary
- New regimes / new policy modes within an existing concept (those go in the relevant primary doc)

---

## §8. Open question (small)

Should there eventually be a *fifth* concept — **operating point** — promoted from "tuple shorthand" to a first-class concept? Right now `(mode, load)` is just notation. If we end up doing dispatch optimization that produces operating-point trajectories as a primary output, the tuple may deserve its own name and treatment. For now: nope, it's just shorthand. Worth revisiting if the load discussion graduates.

---

## §9. Closing — what this doc is *not*

To be clear about scope:

- This doc is **not** the discussion of regime — that's `01_regime_concept.md`
- This doc is **not** the discussion of load — that's `02_load_as_a_dimension.md`
- This doc is **not** methodology — it's a cheatsheet
- This doc is **not** an ADR — it doesn't commit to anything

It is a *vocabulary anchor*. Its job is to make the four concepts visible in one place, with a 2×2 diagram that you can paste into a slide or print and pin above your desk when the conversations get confused. Nothing more.
