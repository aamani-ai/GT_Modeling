# Decisions — gt_models Prototype Explainer + Arch Review

## 1. Used `sdeshp0/gas-turbine-digital-twin.git` fork over `aamani-ai/gas-turbine-digital-twin.git`

### Decision

When cloning the prototype reference, use the `sdeshp0` fork rather than the `aamani-ai` fork.

### Rationale

- The user's correction in this session pointed out the `sdeshp0` fork is "more updated."
- Latest commit on `sdeshp0` fork is `c31c5e8` (2026-05-08): *"small fix to charts_inputs.py to make it runnable"* — i.e. has bug fixes the `aamani-ai` fork lacks.
- Trade-off considered: cloning the aamani-ai canonical version would be more "official," but the sdeshp0 fork has runnable code. Since the purpose is reference and explanation (not running), runnability isn't strictly required — but freshness of the latest engineering corrections is.

## 2. Wrote a single 18-section explainer rather than splitting into multiple files

### Decision

`docs/extra/understanding_of_gas_turbine_digital_twin.md` is one ~400-line file with 18 sections, rather than a folder of split topic files.

### Rationale

- The user's framing was "understand what this repo contains, what it might suggest the goal is, and a bunch of other things related to gas-fired generation dispatch models" — a single coherent narrative, not a reference library.
- Single file is easier to land on cold, easier to grep, easier to link to from other docs (the arch doc now references it via §3.4 and §5.5).
- The 18 sections give the same internal navigation a folder would, without the cross-link maintenance burden.
- Trade-off: file is ~400 lines which is on the long side; mitigated by the table-of-contents-style structure and per-section anchor links.

## 3. Chose "reader's guide" depth (not executive brief, not deep technical)

### Decision

The explainer is written at "anyone on the InfraSure team can read this and navigate the repo in one sitting" depth — conceptual + structural with file:line pointers, but no code snippets or equations.

### Rationale

- Explicitly confirmed with the user via `AskUserQuestion` — they picked "Reader's guide (recommended)" over "Deep technical walkthrough" and "Executive brief."
- Matches the existing methodology-doc style in `docs/methodology/`: terse, pointer-rich, no code blocks.
- Trade-off: someone extending the prototype model would still need to read the code; this doc gets them oriented quickly but isn't a substitute for the Python source.

## 4. Audience framed as internal team, not external DD

### Decision

The explainer assumes the reader has read `InfraSure_ModelingFramework_V2.md` already and wants to understand what's actually in the implementation.

### Rationale

- Explicitly confirmed with the user — "internal team" picked over "external investor / DD audience" and "code-first contributor."
- Lets the doc skip the methodology motivation (already in framework MD) and focus on what's *in the code* vs *what the framework promised*.
- This is also why the explainer leans heavily on file:line references — internal team members can dive into the source.

## 5. Included a critical assessment section (not soft acknowledgements)

### Decision

Explainer §15 is a dedicated "What is prototype, what is production-ready" section split into three sub-sections: solid / prototype / genuinely missing.

### Rationale

- Explicitly confirmed with the user — they picked "Yes, frank gaps + limitations" over "Soft acknowledgements only" and "No critique — descriptive only."
- Calls out concretely: heuristic dispatch (not MIP), all LTSA `[ASSUME]` values, no capacity market / RGGI / 1×1 mode / joint NPV optimizer, no correlated tail scenarios.
- Trade-off: the section is the longest in the doc and could read as harsh; mitigated by placing the "solid" subsection first and giving each "missing" item a clear fix path.

## 6. Added the modes-as-optimization clarification as §5.1 within the existing doc

### Decision

When the user followed up with "does this allow optimization for max profit vs min LTSA?", added the answer as a new subsection §5.1 within the existing §5, rather than creating a separate doc.

### Rationale

- The question was a natural extension of §5 ("The three dispatch modes"), not a different topic.
- A separate doc would have orphaned the answer from its context.
- The new §5.1 covers: (a) modes are heuristic policies not optimization, (b) three levels of capability the architecture supports (mode comparison today, parametric sweep cheap-next-step, true MIP/LP genuinely-missing), (c) architectural verdict — scaffold is right, optimizer just isn't built yet.

## 7. Added §5.8 to architecture.md instead of renumbering existing sections

### Decision

The new "Execution nesting" section was added as §5.8 at the *end* of the §5 core-engine sequence (after §5.7 LTSA streams, before §6 Outputs), rather than inserting it before §5.1 and renumbering everything 5.1→5.2 etc.

### Rationale

- Renumbering would have required updates throughout the doc and potentially in any external references (notebooks, plans, ADRs that mention "§5.x"). The cost wasn't justified by the placement gain.
- The "putting it all together" framing actually flows better as a closer to §5 — the reader has just learned what one day does (12-step loop), what state evolves, how forced outages work, how policies bind, how inspections fire, how LTSA accrues — and *then* zooms out to see the outer orchestration.
- Trade-off: ordering is slightly less "top-down" than ideal (would have been cleaner to introduce nesting before diving into the daily loop), but the renumbering cost was higher than the ordering benefit.

## 8. Disambiguated "mode" word in §5.8

### Decision

The new §5.8 includes a dedicated callout box distinguishing *policy mode* (A/B/C) from *operating mode* (3×CC/2×CC/1×CC).

### Rationale

- The dual meaning of "mode" came up explicitly in the Q&A walkthrough this session (the user asked "how do the formulas change per mode" referring to §5.3, and the answer required pulling apart the two meanings).
- The same confusion will hit any future reader. Documenting it inside the doc reduces re-discovery cost.
- Placed in §5.8 (the new section) rather than retrofitting §5.3 because §5.8's nested-loop diagram is the natural place where both meanings appear together: outer loop iterates policy modes, inner per-hour pick chooses operating modes.

## 9. Documented the CI scheduler bug as a finding rather than fixing it in code

### Decision

The CI-never-fires bug discovered during the MI explanation Q&A was documented in this task folder + flagged for next-session fix, NOT patched in this session.

### Rationale

- The fix has two distinct sub-decisions that need user input:
  1. **YAML field semantics**: should `eoh_threshold` mean *interval between events* (current code usage) or *cumulative threshold value* (what the Athens framework intended — CI at 32K, 40K; MI at 48K)? These imply different YAML edits.
  2. **Scheduler algorithm**: should the scheduler track `last_event_eoh` and compute `next = last + interval`, or keep periodic multiples?
- Either fix is small in lines-of-code but materially changes model output (introduces 2× more CI events in 9 years at $937K owner-uncovered each → ~$2M additional LTSA owner cost; changes inspection cadence which affects state resets, which cascades into HR penalty timing, forced-outage probabilities, etc.).
- A change of that scope warrants user direction before code changes — consistent with the "don't try to fix findings before team weighs in" instruction in `CLAUDE.md` "Don'ts."

## 10. Deliverables committed mid-session; task-docs deferred to end-of-session

### Decision

The session's deliverables (prototype clone, explainer doc, §5.8 arch-doc edit) were committed mid-session and are at git HEAD. The task-docs folder (this folder) was deliberately left uncommitted at session end so it can ship in a single commit with the next-session fixes (CI scheduler, etc.).

### Rationale

- Verified at end of session: `git ls-files docs/extra/` confirms the prototype clone and explainer doc are tracked; `git status` shows only the task-docs folder + a pre-existing notebook modification as uncommitted.
- This means the deliverables won't be lost if the next session takes a while to start. Good outcome.
- Trade-off considered: I initially drafted handoff/task_context/decisions claiming "nothing committed this session" — that was incorrect. Caught it via `git status` after writing the task docs. Corrected all three files. **Lesson**: when writing handoff documents, always cross-check claims about git state by actually running `git status` and `git ls-files`, don't infer from the conversation transcript.
- Per `CLAUDE.md`: *"Don't push without explicit cd + pwd verification"* — commits and push are explicit user decisions, not autonomous. Whoever committed the deliverables mid-session followed that protocol.

## 11. Memory file structure: separated user-feedback from project-context

### Decision

Created two separate memory files: `feedback_no_shallow_answers.md` (the "search recursively before assuming" lesson) and `project_gt_digital_twin.md` (the Athens-pilot-context-and-bridge-framing).

### Rationale

- Feedback memories drive *behavior change* (always search before assuming); project memories provide *factual context* (Athens pilot specs, the bridge framing).
- Mixing them into one file would make the index entry harder to write (one description can't cover both behavioral guidance and project facts).
- Matches the convention established in the prior `v1-lockport-shipped` session memory (`feedback_explicit_cd_for_git.md` is a behavioral memory; project state is mostly tracked in the repo itself rather than in memory).
