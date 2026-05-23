# 04. Industry Vocabulary, Reality Check, and References

> **Status**: Reference / validation. Documents how the project's four-concept framing maps to industry-standard vocabulary, what caveats apply, and where to find authoritative external references. Updated whenever the framing changes or new references are added.
>
> **Folder context**: This is a discussion doc (per `docs/discussion/README.md`). It is meta-discussion — it doesn't litigate the concepts (those live in 01 and 02) or organize the cheatsheet (that's 03). It validates the framing against external practice and points to authoritative sources.

---

## §1. Why this doc exists

The project is building for industry users (operators, insurers, asset managers, lenders, advisors). If our internal vocabulary diverges from how these users actually talk and write about gas plant operations, three things go wrong:

1. **External communication friction**: a colleague, partner, or client reading our docs has to translate our terms into theirs.
2. **Credibility risk**: introducing novel terminology where standard terminology exists looks like the team didn't know the standard. Lowers trust.
3. **Lost integration**: standard terminology has standard references (papers, codes, contracts). Our terms don't inherit that scaffolding unless we map them.

This doc does the mapping. For each of the four concepts (regime, policy mode, operating mode, load level), it:

- Validates whether the *concept itself* matches industry usage
- Documents the *standard industry terminology* (with synonyms / alternatives where multiple exist)
- Flags the caveats / limitations of our internal framing relative to industry practice
- Cites *authoritative references* where readers can verify the standard usage

This is "show your homework" — making the reality check explicit so the framing is defensible.

---

## §2. Concept-by-concept reality check

Quick verdict for each concept on how well our framing matches real-world / industry usage:

| Concept | Match with real-world? | Confidence | Main caveat |
| :--- | :--- | :--- | :--- |
| **Operating mode** (3×CC / 2×CC / 1×CC) | ✓ exact match | High | None significant |
| **Load level** (continuous % of mode max) | ✓ exact match | High | Industry adds ambient conditions as a co-dimension; we embed ambient in mode parameters |
| **The slow/fast (posture/tactical) split** | ✓ matches industry mental model | High | Industry doesn't formalize the split into a 2×2 — they treat each concept independently. Our explicit 2×2 is a useful internal abstraction but not a "thing" externally |
| **Regime as "business positioning"** | ✓ concept real; ⚠ *terminology* diverges | Medium | Industry calls this "duty cycle" / "operating profile" / "plant archetype." "Regime" is our internal term. See §3.1 |
| **Policy mode as "wear management posture"** | ✓ concept real; ⚠ *terminology* and *static-per-simulation* both diverge | Medium | Industry calls this "dispatch philosophy" / "asset preservation strategy." Industry treats it as continuous and dynamically shifting; we discretize and freeze. See §3.2 |
| **(Operating mode + load) tuple as the hour-by-hour decision** | ✓ matches, slightly incomplete | Medium-high | Industry "operating point" often includes ambient conditions and ramp state. Our tuple captures the most important dimensions. See §3.5 |
| **Operating point as a derived concept** | ⚠ industry treats this as a *primary* descriptor; we treat it as tuple notation | Low-medium | If we end up exposing operating-point trajectories as outputs, it deserves its own first-class treatment. See §3.5 |

**Overall verdict**: The framing is substantially correct. The main risks are *terminology* (our two-axis labels for the posture concepts don't match industry) and a few small *completeness* gaps. None of these is a methodological error; all are documentation / external-communication concerns.

---

## §3. Concept-by-concept industry vocabulary

For each concept, this section gives:

- The *concept-level* mapping (our term → industry equivalent[s])
- Synonyms / alternative terms used in different sub-domains
- Where the term appears authoritatively
- Caveats specific to that concept

### §3.1 Regime ↔ duty cycle / operating profile / plant archetype

Our **regime** maps to one of several industry terms, each used in a slightly different sub-domain:

| Industry term | Primary sub-domain | What it specifically denotes |
| :--- | :--- | :--- |
| **Duty cycle** | OEM service contracts; NERC GADS; insurance underwriting | The plant's *intended operating intensity* — used to set warranties, LTSA terms, and reliability expectations |
| **Operating profile** | Asset management; fleet studies; EPRI documentation | The plant's *observed operating behavior* over a period — used for trending and benchmarking |
| **Plant archetype** | NREL ATB; capacity expansion modeling; policy analysis | A *category* the plant belongs to for aggregation purposes (peaker / intermediate / baseload) |
| **Service classification** | GE / Siemens documentation | OEM's classification of the unit's intended duty |
| **Capacity factor regime** | Power systems trading | The plant's typical capacity factor band (used in trading strategy discussion) |

**Specific values** that an industry source would use, with rough equivalents to our regime list:

| Our regime | Industry equivalents |
| :--- | :--- |
| Baseload | "Baseload duty"; "high-CF unit"; "Type 1 (continuous duty)" in some classifications |
| Peaker | "Peaking duty"; "extreme peaker"; "Type 2 (peaking)"; "OCGT-style operation" (even for CCGTs) |
| Mid-merit | "Intermediate duty"; "cycling duty"; "load-following" |
| Cogen / industrial host | "Cogeneration"; "CHP" (combined heat and power); "industrial host" |
| Frequency regulation | "AGC unit" (automatic generation control); "regulation up/down provider"; "ancillary services unit" |
| Must-run contractual | "Capacity-firm unit"; "RMR" (reliability must-run); "must-take" |

**Authoritative sources for industry use of "duty cycle":**

- **GE GER-3620 series** — "Heavy-Duty Gas Turbine Operating and Maintenance Considerations." Uses duty cycle as the primary categorization for setting maintenance intervals. The 2018 edition (GER-3620N) is current; older versions (K, L, M) remain widely cited.
- **NERC GADS Data Reporting Instructions** — categorizes units by duty cycle for availability statistics. Available via NERC's public data products.
- **NREL ATB (Annual Technology Baseline)** — uses "plant archetype" (peaker / intermediate / baseload) for capacity cost categorization. Current edition published annually at `atb.nrel.gov`.
- **EPRI Technical Reports** — EPRI's CCGT fleet studies use "duty cycle" as the primary stratification dimension. Specific reports referenced in `extra/performance_and_risk_framework.md` (e.g., 1026609 on TBC life, 1025357 on combustion). Catalog at `epri.com`.
- **NERC Reliability Standards** — operating-state and reliability-class definitions; some overlap with duty-cycle concepts.

**Caveat 1 — terminology mismatch**: Our "regime" term is internal. External communication should *additionally* use "duty cycle" or "operating profile" when context is industry-facing. Suggested practice: when writing a client-facing deliverable, replace "regime" with the appropriate industry term; when writing internal docs, "regime" is fine but should be defined.

**Caveat 2 — vector vs categorical**: Some industry usage treats duty cycle as a *category* (baseload / intermediate / peaker). Some treats it as a *spectrum* (capacity factor as a continuous proxy). Our discussion (`01_regime_concept.md` §5.2) leans toward a *vector* representation. The vector approach is more sophisticated than typical industry usage but is supported by recent fleet-analytics work that recognizes regimes can be hybrid (a plant in cogen + mid-merit simultaneously).

### §3.2 Policy mode ↔ dispatch philosophy / asset preservation strategy / wear-aware dispatch

Our **policy mode (A / B / C)** is an internal modeling abstraction for the operator's wear-vs-revenue trade-off preference. Industry doesn't have a single canonical term, but the concept appears under multiple names:

| Industry term | Sub-domain | What it denotes |
| :--- | :--- | :--- |
| **Dispatch philosophy** | Trading desk; merchant operations | The operator's overall approach to when and how aggressively to dispatch |
| **Asset preservation strategy** | O&M planning; LTSA negotiation | Explicit strategy for managing wear and maintenance costs |
| **Operating discretion** | LTSA / FSA contract language | The space within the contract that the operator can use to shift wear vs revenue |
| **Wear-aware dispatch** | Academic literature | Formal name in the dispatch optimization research community |
| **Cycling-aware dispatch** | NREL / EPRI literature | Specific variant focused on start/stop cycling costs |
| **EOH-aware dispatch** | OEM service literature | Practical variant focused on equivalent-operating-hour management |

**The continuous-to-discrete simplification**:

In industry usage, the operator's preference is treated as a **continuous parameter** — a weight in an objective function balancing near-term revenue against long-term wear cost. Our model discretizes this into three bookends (A, B, C) as a *bracketing abstraction*.

This is explicitly a **modeling choice**, not a description of how operators actually think. Real operators have a continuous preference that shifts dynamically over the asset's life:

- After a major inspection: typically run harder (fresh stress budget)
- As an inspection approaches: typically preserve wear more aggressively
- When LTSA terms re-negotiate: incentive structure shifts
- When capacity payments rise relative to energy: trade-off shifts toward availability

Our policy mode is **static per simulation**. The framework reference (`extra/performance_and_risk_framework.md` §3) discusses this as a latent conditioning variable that *can change*; the engine treats it as fixed within a run.

**Authoritative sources for industry use:**

- **Kumar, Besuner, Lefton, Agan, Hilleman (2012). "Power Plant Cycling Costs." NREL/TP-5500-55433.** — The canonical reference on cycling cost quantification. Establishes the wear-cost framework that "wear-aware dispatch" optimizes against. Available at `nrel.gov`.
- **Timera Energy "Power plant optionality & dispatch cost hurdles"** — practitioner-facing treatment of how dispatch philosophy interacts with optionality and wear. Available at `timera-energy.com`.
- **Tofighi-Niaki (2024). "Economic Dispatch of Combined Cycle Power Plant: A Mixed-Integer Programming Approach." MDPI Processes 12(6), 1199.** — Academic treatment of dispatch optimization with explicit wear-cost handling.
- **GE GER-3620 series** — Defines EOH counting and the wear implications of different dispatch patterns; the source for "EOH-aware" thinking.

**Caveat 1 — terminology**: When writing client-facing material, "policy mode" reads as our jargon. "Dispatch philosophy" or "asset preservation strategy" are better externally. Internally, "policy mode" is established in the engine and docs; keep using it but be aware it doesn't translate.

**Caveat 2 — discretization**: The A/B/C bookends are a *bracketing tool*, per the framework's bracketing posture (`extra/forward_looking_framing.md`). Be explicit when explaining this externally — it is not a claim about how operators actually behave.

**Caveat 3 — static vs dynamic**: The static-per-simulation treatment is a real simplification. For long-horizon projections, real policy may shift over the projection window. Future model versions should consider dynamic policy.

### §3.3 Operating mode ↔ block configuration / unit commitment state

Our **operating mode (3×CC / 2×CC / 1×CC)** matches industry usage exactly. This is the cleanest concept-to-vocabulary mapping in the four-concept set.

| Industry term | Sub-domain | What it denotes |
| :--- | :--- | :--- |
| **Block configuration** | Plant operations; CCGT engineering | Which GTs are firing into the HRSG (most common term) |
| **N×1 configuration** | OEM documentation; merchant operations | Format: "3×1" or "2×1" indicates N gas turbines on 1 steam turbine |
| **Unit commitment state** | Power systems optimization | Binary state of each unit (on/off) — academic / RTO terminology |
| **Dispatch group** | ISO/RTO market software | Set of physical units that can be dispatched as a group |
| **Combined cycle mode** | OEM service contracts | "3×CC" or similar — denotes the integrated CC operating state |

**Specific notations:**

- *"3×1 CCGT"* — three gas turbines on one steam turbine, all integrated (the most common notation for our 3×CC)
- *"2-on-1"* or *"3-on-1"* — verbal shorthand
- *"SC mode"* — simple cycle (GT only, no ST); usually denoted distinctly from CC operation
- *"Block 1 / Block 2"* — when a plant has multiple independent CCGT trains

**Authoritative sources:**

- **ANSI / ASME PTC 22 — Gas Turbine Performance Test Code** — defines testing conditions for combined cycle and simple cycle configurations.
- **ANSI / ASME B133 — Procurement Standard for Gas Turbine Power Plants** — standard procurement framework that uses configuration terminology.
- **Boyce, "Gas Turbine Engineering Handbook" (4th ed., 2012, Butterworth-Heinemann)** — comprehensive treatment of CCGT configurations and operating modes.
- **Kehlhofer, Bachmann, Nielsen, Warner, "Combined Cycle Gas Steam Turbine Power Plants" (3rd ed., 2009, PennWell)** — industry reference for CC plant operations.
- **IEEE 762 — IEEE Standard Definitions for Use in Reporting Electric Generating Unit Reliability, Availability, and Productivity** — defines operating states formally.

**Caveat — minor**: When writing for an ISO/RTO market context, "dispatch group" or "unit commitment state" may be the more natural framing. For OEM / O&M contexts, "block configuration" is standard. Both map to the same concept.

### §3.4 Load level ↔ set point / load point / part-load operation / peak fire

Our **load level (continuous % of mode max)** is also a clean concept-to-industry-vocabulary mapping. Multiple industry terms cover slightly different aspects:

| Industry term | What it denotes | When it's used |
| :--- | :--- | :--- |
| **Load point** | Operating intensity expressed as MW | Generic dispatch / operations discussion |
| **Set point** | The target MW value the operator is dispatching to | Real-time operations; control room terminology |
| **% load** or **% MCR** (maximum continuous rating) | Operating intensity as fraction of nameplate or current max | Engineering documentation; performance studies |
| **Part-load operation** | Operating below 100% load | Performance / efficiency analysis (where part-load HR matters) |
| **Peak fire** or **over-firing** | Operating above design firing temperature (typically 3–5% above nameplate output) | OEM service terms; extreme-condition operations |
| **Minimum stable load** (or **min-load**) | Lowest operating intensity at which combustion is stable | Engineering specifications; dispatch constraints |
| **Turn-down ratio** | Ratio of full load to min-load | OEM specifications; flexibility assessments |

**Specific numerical values** commonly cited in industry:

- **Minimum stable load** for CCGT: typically ~50% of nameplate (some advanced models reach 30–40%)
- **Part-load HR multiplier** at 50%: ~1.16× full-load HR (CCGT class average)
- **Part-load HR at 80%**: ~1.04× full-load HR
- **Peak fire output uplift**: ~3–5% above nameplate, typically limited to <10% of operating hours per OEM agreement
- **Ramp rate**: 10–30 MW/min (full plant); OEM-specific

**Authoritative sources:**

- **GE GER-3620 series** — Cycling and part-load operating considerations.
- **GE GER-3567H — "Performance and Reliability Improvements for the 7FA Gas Turbine"** — Performance characteristics including part-load.
- **Kumar et al. (2012). NREL/TP-5500-55433. "Power Plant Cycling Costs."** — Quantifies wear and efficiency penalties from part-load and cycling operation.
- **Kehlhofer et al. (2009). "Combined Cycle Gas Steam Turbine Power Plants."** — Engineering treatment of part-load CCGT operation.
- **ANSI / ASME PTC 22** — Performance test conditions including part-load specifications.
- **EPRI Technical Reports on CCGT operation** — fleet experience with part-load and cycling.
- **`extra/performance_and_risk_framework.md` §4.6** — the part-load HR polynomial in this codebase, derived from GE 7FA part-load curves.

**Caveat — minor**: The numerical values above are *industry-average / class-typical*. Specific assets (e.g., Lockport's CTs which are 1992 vintage) may have characteristics slightly different from current fleet averages. When applied to a specific asset, the OEM datasheets for that asset's exact model should be consulted.

### §3.5 Operating point and ambient conditions — two related "watch this" items

Industry usage of **operating point** is *richer* than our (mode, load) tuple. A full operating point typically includes:

- **Operating mode** (which CTs firing) — we capture
- **Load level** (intensity) — we capture
- **Ambient temperature** — we embed in mode-capacity calculations (`cap_eff_for_mode`)
- **Ambient humidity** — we ignore
- **Ambient pressure** — we ignore (small effect)
- **Ramp state** — whether load is steady or changing — we ignore
- **Reserves provided** — whether the unit is in spinning reserve, regulation, etc. — we capture only via the regime concept
- **Fuel mix** (if dual-fuel) — N/A for Lockport in v1; relevant for some assets

Industry sources (e.g., **OEM performance curves**, **ASME PTC 22**) treat ambient conditions as a primary axis alongside load. We treat ambient as a parameter on operating mode, which is a reasonable simplification for most use cases but might be worth elevating if we move to more sophisticated dispatch optimization.

**The current treatment is**:
- Adequate for v1 forward projection (where ambient is forecasted as input)
- Inadequate for any analysis that needs to optimize over ambient conditions
- Documented as an *embedded conditioner* rather than a missing concept — but flagged as a "watch this" if the discussion of load matures further

**Authoritative sources for the broader operating-point view:**

- **ANSI / ASME PTC 22 — Gas Turbine Performance Test Code** — defines reference and corrected operating points; treats ambient conditions explicitly.
- **ISO 2314 — Gas Turbines — Acceptance Tests** — international standard for performance testing; includes ambient corrections.
- **GE GER-3567** — Performance curves for the 7FA showing dependency on ambient temperature and humidity.

---

## §4. Caveats summary

The complete list of caveats raised by this reality check, consolidated for reference:

1. **"Regime" is our internal term; industry uses "duty cycle" / "operating profile" / "plant archetype."** Concept is real; terminology should be mapped for external communication. (§3.1)

2. **"Policy mode" isn't a single industry term.** Closest equivalents: "dispatch philosophy," "asset preservation strategy," "wear-aware dispatch." Our A/B/C discretization is a *bracketing abstraction*, not a claim about operator behavior. (§3.2)

3. **Policy mode treated as static per simulation is a real simplification.** Real operators shift wear strategy dynamically over the asset's life. Future model versions should consider dynamic policy. (§3.2)

4. **Operating mode and load level match industry vocabulary cleanly.** Minimal terminology friction; just be mindful of context (block config vs unit commitment state). (§3.3, §3.4)

5. **Ambient conditions are embedded in operating-mode calculations, not first-class.** Adequate for v1 forward projection; might deserve elevation in future versions. (§3.5)

6. **The (mode, load) tuple is slightly less complete than industry's "operating point."** Industry often includes ambient + ramp + reserves. Our tuple captures the most impactful dimensions for revenue modeling. (§3.5)

7. **The 2×2 orthogonal layout (slow/fast × posture/tactical) is our internal organization.** Industry doesn't formalize this 2×2; they treat each concept independently. Our explicit organization is useful internally but is *not* a real-world structure. (§2)

---

## §5. Curated reference list — by topic

Authoritative sources organized by the topic they best address. Cite freely; pull when needed.

### §5.1 OEM service and maintenance documentation

- **GE GER-3620 series** ("Heavy-Duty Gas Turbine Operating and Maintenance Considerations"). Multiple editions; the canonical reference for OEM service-interval logic, duty cycle effects, EOH counting. The 2018 edition (GER-3620N) is current; older (K through M) still widely cited.
- **GE GER-3567 series** ("Performance and Reliability Improvements for the 7FA Gas Turbine"). 7FA-specific performance characteristics including part-load and ambient corrections.
- **Siemens Energy / Mitsubishi MHI** — OEM service documentation analogous to GER-3620 for non-GE units. Less publicly accessible but referenced via service agreements.

### §5.2 Industry standards and codes

- **NERC GADS** (Generating Availability Data System) — duty-cycle classifications, availability metrics, outage definitions. Reporting Instructions and Data Reporting Guidance available via NERC.
- **NERC Reliability Standards** — operating-state definitions, must-run requirements, ancillary services.
- **IEEE 762 — IEEE Standard Definitions for Use in Reporting Electric Generating Unit Reliability, Availability, and Productivity** — formal definitions of operating states, availability classes.
- **ANSI / ASME PTC 22 — Gas Turbine Performance Test Code** — testing standard; defines operating points, corrections, performance metrics.
- **ANSI / ASME B133 — Procurement Standard for Gas Turbine Power Plants** — procurement framework using duty-cycle and configuration terminology.
- **ISO 2314 — Gas Turbines — Acceptance Tests** — international standard for performance testing.
- **ENTSO-E grid codes** — European equivalents for grid-connected resource categorization. Specific documents vary by service.

### §5.3 Research and academic literature

- **Kumar, N., Besuner, P., Lefton, S., Agan, D., Hilleman, D. (2012). "Power Plant Cycling Costs." NREL/TP-5500-55433.** — canonical reference on cycling cost quantification. Foundational for our LTSA / wear modeling. `nrel.gov`.
- **EPRI Technical Reports on Gas Turbine Experience and Intelligence**:
  - EPRI 1026609 — TBC coating failure distributions (cited in framework doc)
  - EPRI 1025357 — Combustion hardware fleet experience (cited in framework doc)
  - EPRI 1012586 — Combustion turbine starts modeling (cited in framework doc)
  - Catalog at `epri.com`; access typically requires membership.
- **Abdul Ghafir, M.F. et al. (2025). "Gas turbine equivalent operating hour estimation considering creep-LCF interactions." *The Aeronautical Journal*, Cambridge University Press.** — Recent work on creep-fatigue interaction; supports the framework's coupled damage model.
- **Tofighi-Niaki, A. (2024). "Economic Dispatch of Combined Cycle Power Plant: A Mixed-Integer Programming Approach." MDPI Processes 12(6), 1199.** — Wear-aware dispatch optimization.
- **Lew, D. et al. (2012). "Impacts of Renewable Generation on Fossil Fuel Unit Cycling: Costs and Emissions." NREL.** — Companion to the Kumar 2012 paper.
- **Friday 2026-05-22 advisory meeting paper** — Research paper on load-and-temperature dependency for turbine fatigue and creep, shared by Siddharth. *Specific citation pending* — see task history doc for the paper Siddharth forwarded.

### §5.4 Industry and policy organizations

- **NREL ATB (Annual Technology Baseline)** — plant archetype classifications, performance and cost reference for capacity expansion modeling. Published annually at `atb.nrel.gov`.
- **EIA Annual Energy Outlook** — long-term technology cost and capacity factor projections.
- **LBNL studies on gas plant operations** — varied; Berkeley Lab has produced multiple gas-plant cycling and flexibility studies.
- **CAISO / ERCOT / PJM market rules** — ISO-specific definitions of ancillary services products (regulation, spinning reserve, etc.). Available via each ISO's market rules / Open Access Same-time Information System (OASIS).
- **NREL Renewable and Conventional Plant Lifecycle Studies** — various NREL TPs on plant operations.

### §5.5 Practitioner / consultancy publications

- **Timera Energy blogs** — "Getting comfortable with CCGT extrinsic value"; "Power plant optionality & dispatch cost hurdles"; "Monetising the value of flexible gas & power assets." Practitioner-facing treatments of CCGT optionality, dispatch philosophy, and asset valuation. `timera-energy.com`.
- **Intertek APTECH** — "Power Plant Cycling Cost and Flexible Generation." Consultancy work on cycling cost quantification.
- **Combined Cycle Journal** — industry magazine; 7F Users Group articles and combustion-dynamics monitoring features. `ccj-online.com`.

### §5.6 Textbooks and foundational references

- **Boyce, M.P. (2012). "Gas Turbine Engineering Handbook" (4th ed.). Butterworth-Heinemann.** — Foundational engineering reference.
- **Kehlhofer, R., Bachmann, R., Nielsen, H., Warner, J. (2009). "Combined Cycle Gas Steam Turbine Power Plants" (3rd ed.). PennWell.** — Industry reference for CCGT operations.
- **Wood, A.J., Wollenberg, B.F., Sheblé, G.B. (2014). "Power Generation, Operation, and Control" (3rd ed.). Wiley.** — Standard textbook for dispatch and unit commitment.
- **Sutton, R.S., Barto, A.G. (2018). "Reinforcement Learning: An Introduction" (2nd ed.). MIT Press.** — Referenced in `framing_a_modeling_problem.md` for state-conditional decision-making; relevant background for operating-point dispatch.

### §5.7 InfraSure-internal foundational documents

- `extra/performance_and_risk_framework.md` — the InfraSure-generic framework. Many of the references in §5.1 through §5.6 originate from this document's bibliography.
- `extra/gas_plant_workflow.md` — gas-specific application of the framework.
- `extra/forward_looking_framing.md` — bracketing posture, including the discrete-bookends rationale.
- `/Users/divy/Desktop/Learning/Risk/infraSure_specific/the_risk_spine.md` — the philosophy-level treatment of why the framework has the shape it does.

---

## §6. How to use this doc

Three modes of use:

### 6.1 External communication

When writing a client / partner / investor-facing deliverable, *use industry terminology* even if the internal docs use our terms:

- Replace "regime" with "duty cycle" or "operating profile"
- Replace "policy mode" with "dispatch philosophy" or "asset preservation strategy"
- Keep "operating mode" and "load level" — these are industry-standard already

### 6.2 Internal communication

Internal docs and code can keep our terminology, but **every formal artifact should link back to this doc** so the mapping is one click away. The cheatsheet (`03_four_concepts_vocabulary.md`) is the front door; this doc (`04`) is the depth.

### 6.3 Onboarding new collaborators

New team members or external advisors should be pointed at the reading list in §7 below. Reading the four discussion docs in sequence, with the methodology cross-references, gives a complete picture of how the project's vocabulary relates to industry practice.

---

## §7. Reading list — recommended sequence

For anyone wanting to internalize the project's framing and how it maps to industry practice, the following sequence is suggested. Estimated reading time given for each item.

### Phase A — Get oriented (30 min)

1. **`docs/discussion/README.md`** *(5 min)* — what the folder is for; the three-folder distinction (discussion / decisions / methodology).
2. **`docs/discussion/03_four_concepts_vocabulary.md`** *(10 min)* — the cheatsheet. Start here for the four-concept framing.
3. **This doc — §1, §2, §6** *(15 min)* — what this validation doc is, the concept-by-concept reality check table, how to use the vocabulary externally.

### Phase B — Deep dive on the two open concepts (60–90 min)

4. **`docs/discussion/01_regime_concept.md`** *(30–45 min)* — full exploration of regime, including the "what regime is NOT" section in §3 and the open questions in §7.
5. **`docs/discussion/02_load_as_a_dimension.md`** *(30–45 min)* — full exploration of load level, including part-load HR, load-dependent degradation, frequency-reg invisibility, and the static-100%-load assumption.

### Phase C — Industry vocabulary and references in depth (45–60 min)

6. **This doc — §3** *(30–45 min)* — concept-by-concept industry vocabulary mapping for regime, policy mode, operating mode, load level, and operating point.
7. **This doc — §4, §5** *(15 min)* — consolidated caveats summary and the curated reference list.

### Phase D — How these connect to the methodology (60 min)

8. **`docs/methodology/modeling_flow.md`** — especially **§3** *(20 min)* — the end-to-end project flow Step 2, now reflecting the four-concept framing.
9. **`docs/methodology/architecture.md`** **§5.3** *(10 min)* — where operating mode is committed in the engine.
10. **`docs/methodology/architecture.md`** **§5.5** *(10 min)* — where policy mode is committed (wear-penalty curve).
11. **`docs/methodology/dispatch_mechanics.md`** *(20 min)* — operating mode × policy mode interaction in detail.

### Phase E — Broader framing context (45 min)

12. **`docs/methodology/extra/forward_looking_framing.md`** **§3** *(15 min)* — policy mode as bracketing posture (the why for our discretization).
13. **`docs/methodology/extra/performance_and_risk_framework.md`** **§3** *(20 min)* — the latent conditioning variable discussion at the generic framework level.
14. **`docs/methodology/extra/gas_plant_workflow.md`** **§1, §5** *(10 min)* — institutional scope (gt_models = revenue arm) and policy mode in the gas-specific context.

### Phase F — External references (as needed; 1–4 hr)

For credibility with external reviewers, the most important external references to pull are:

15. **Kumar et al. (2012). NREL/TP-5500-55433. "Power Plant Cycling Costs"** *(1 hr to skim, longer for deep read)* — the foundational reference. Citable across virtually every wear / cycling discussion.
16. **GE GER-3620 series** *(30 min to skim relevant sections)* — for OEM-perspective on duty cycle and EOH counting.
17. **One Timera Energy blog post** of choice *(15 min)* — for practitioner-facing CCGT optionality language.
18. **NREL ATB current edition** *(skim for plant archetype categorizations)* — for the duty-cycle classification we map regime against.

### Phase G — Source material (optional; 60–120 min)

For the curious, the raw materials that motivated the discussion:

19. **`docs/extra/tasks_history/2026-05-15__gt-models__prototype-explainer-and-arch-review/handoff.md`** *(30 min)* — the session that surfaced the regime concept.
20. **`/Users/divy/Desktop/infrasure/meets/friday-gt-modeling-meeting.md`** *(30 min)* — the 2026-05-22 advisory meeting where Siddharth flagged the load and ambient-temperature dependency.

---

## §8. Maintenance

This doc should be updated when:

- A new industry-standard term is identified that maps to one of our concepts
- A reference becomes available (e.g., the specific load-temperature paper from the Friday meeting)
- A concept changes representation (e.g., regime moves from categorical to vector)
- An ADR commits one of the open concepts to methodology (the corresponding "Caveat" in §4 should be updated or removed)

Keep references current. Add new references via the appropriate sub-section in §5.

---

## §9. Cross-references

- [`README.md`](README.md) — folder purpose and index
- [`01_regime_concept.md`](01_regime_concept.md) — regime exploration
- [`02_load_as_a_dimension.md`](02_load_as_a_dimension.md) — load exploration
- [`03_four_concepts_vocabulary.md`](03_four_concepts_vocabulary.md) — the cheatsheet
- `../methodology/modeling_flow.md` — where these concepts plug into the project workflow
- `../methodology/extra/performance_and_risk_framework.md` — the framework's bibliography (overlapping references)
