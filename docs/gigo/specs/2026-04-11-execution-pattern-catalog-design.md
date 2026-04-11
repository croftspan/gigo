# Execution Pattern Catalog — Design Spec

**Design brief:** `.claude/plans/curious-strolling-chipmunk.md`

**Cycle:** 1 of 2. This spec covers **Part A only** (Execution Pattern Catalog). Part B (Agent Teams rebuild) is a separate, future spec run and is **explicitly out of scope** for this document.

---

## Original Request

> Read briefs/03-execution-architecture-catalog.md — it has the full context from a competitive analysis of revfactory/harness.
>
> TL;DR: Two parts. Part A (shippable now): a reference catalog of execution patterns (Pipeline, Fan-out/Fan-in, Producer-Reviewer, Expert Pool, Supervisor) so gigo:spec can choose the right execution shape instead of always defaulting to "lead dispatches parallel workers." Part B (design only): how gigo:execute would use Claude Code's Agent Teams API when it stabilizes. Part A improves planning today. Part B is a design doc for the future.

---

## Problem

`gigo:spec` writes implementation plans using a task-level dependency graph (`blocks:`, `blocked-by:`, `parallelizable: true/false`). It has no vocabulary for naming the overall execution shape, so every plan is implicitly "Supervisor" — a lead that dispatches waves of workers. When the work's natural shape is Pipeline (strictly sequential stages), Fan-out/Fan-in (parallel work plus an explicit merge step), Producer-Reviewer (generate then validate at the task level), or Expert Pool (domain-routed review lens), planners lack the vocabulary to flag the intent and make the plan legible.

The outcome: plans drift toward a homogenized shape that hides intent, misses merge steps, and encodes false parallelism. A named catalog gives planners decision criteria and makes execution shape visible in reviews.

---

## Scope Boundary

**In scope (Cycle 1):**
- New reference file in `skills/spec/references/` documenting 5 execution patterns
- Integration hooks in `gigo:spec`'s planning procedure and example plan
- One-line pointer in `skills/spec/SKILL.md`

**Out of scope (Cycle 1):**
- Any change to `gigo:execute`, its references, or its dispatch logic
- Any change to `gigo:verify`, including enforcement of the `review-lens:` tag
- Any change to assembled projects' `.claude/references/`
- Plan validation that blocks plans missing the new header field
- Part B (Agent Teams rebuild) — a separate future spec

---

## Requirements

### R1: Execution Pattern Catalog Reference File

Create `skills/spec/references/execution-patterns.md` — a new plugin-local reference file that `gigo:spec` reads on demand during plan writing.

**Required top-level sections, in this order:**

1. **Purpose** (≤5 lines) — what the catalog is and who reads it.
2. **Lineage note** — a single sentence conveying: *"Adapted from harness's six-pattern catalog, omitting Hierarchical Delegation. Recursive delegation adds complexity without clear value for GIGO's current use cases — we may revisit if a concrete need appears."* The substance is required; exact wording may vary for flow. The note must (a) credit harness as the source, (b) state that GIGO adapts six patterns down to five, (c) name Hierarchical Delegation as the omission, and (d) leave the door open to revisiting.
3. **When to consult this file** — describes the trigger: during plan writing, before decomposing tasks. Must use the phrase "plan writing" or "when decomposing tasks" — **must NOT use the phrase "Phase 8"** (see R7.b).
4. **How to use** — exactly three numbered steps: (1) pick the pattern matching the work's shape, (2) declare it in the plan header as `**Execution Pattern:** <name>`, (3) decompose tasks per the pattern's conventions.
5. **Decision tree** — a compact scannable rule set (plain text, not a diagram) that leads a reader from task shape to pattern choice in ≤10 lines.
6. **The 5 patterns** — one subsection per pattern, in the order: Supervisor, Pipeline, Fan-out/Fan-in, Producer-Reviewer, Expert Pool. Each subsection follows the per-pattern layout defined in R2.
7. **Combining patterns** — explains that multi-phase plans may declare a different pattern per phase, and shows how the plan header expresses that.
8. **Anti-patterns** — the five mistakes listed in R3, each named and explained in 2-3 lines.

**Target length:** Approximately 200 lines. Not a hard ceiling — if a pattern genuinely requires more explanation, that's acceptable. Tokens spent here are on-demand, not auto-loaded.

**Token-tier:** Reference-tier. Loaded when `gigo:spec` reads it during plan writing, not auto-loaded into every conversation.

**Voice:** Domain-agnostic and direct. Examples must span multiple domains — at minimum software, but also research synthesis, writing, or similar non-code work — so the catalog works for assembled projects in any domain, not just code.

### R2: Per-Pattern Entry Layout (Uniform Across All 5)

Each pattern subsection in R1.6 contains exactly these five fields, in this order, using these field names:

1. **Definition** — 2-3 lines, domain-agnostic. States the pattern's core shape without tying it to software.
2. **When to use** — 3-4 bullets of decision criteria. Each bullet is a condition a planner can check against the work.
3. **GIGO mapping** — explains how the abstract pattern translates into GIGO's existing plan vocabulary (`blocks:`, `blocked-by:`, `parallelizable: true/false`). This is the bridge that keeps the catalog compatible with current `gigo:execute`.
4. **Plan shape** — a small markdown snippet showing what the relevant part of a plan looks like under this pattern. Snippets may be abbreviated; they illustrate the shape, not full worked examples.
5. **Gotchas** — 1-2 common mistakes a planner should avoid when using this pattern.

**Per-pattern content requirements:**

| Pattern | Definition must convey | GIGO mapping must state |
|---|---|---|
| **Supervisor** | Central coordinator dispatches independent workers and collects results. The default pattern. | Standard dependency graph with `parallelizable: true` where appropriate. No special markers — this is how GIGO already works. |
| **Pipeline** | Strictly sequential stages; each stage's output feeds the next. | Every task `parallelizable: false`; `blocked-by` forms a linear chain from task to task. |
| **Fan-out/Fan-in** | Independent parallel workers each produce an artifact, followed by a single merge/synthesis task that consolidates them. | A parallel wave (`parallelizable: true` tasks) followed by one merge task whose `blocked-by` lists all fan-out tasks. |
| **Producer-Reviewer** | A producer task generates an artifact; a separate reviewer task validates it; optional iteration on feedback. Generalizes `gigo:verify`'s two-stage review to the task level inside a plan. | Producer task, reviewer task with `blocked-by: [producer]`, optional revision task with `blocked-by: [reviewer]`. |
| **Expert Pool** | Tasks are routed to different **review lenses** by domain — workers stay bare; the lens applied during review changes based on the task's domain tag. | Introduces an optional per-task field `review-lens: <domain>`. **Today the field is metadata only — `gigo:verify` does not yet enforce it.** The catalog documents the pattern so planners can start tagging; enforcement is a future verify enhancement. |

**Expert Pool — required clarification in its entry:** The entry must explicitly state that workers remain bare (no persona context injection) and that the `review-lens:` field is metadata-only in Cycle 1. Any reader must come away understanding that Expert Pool does not change how workers execute; it only signals which review lens applies.

### R3: Anti-Patterns Section Content

The catalog's Anti-patterns section must name exactly these five mistakes, each with a 2-3 line explanation:

1. **False parallelism** — marking tasks `parallelizable: true` when they share hidden state (config file, upstream artifact, database migration). Usually a Pipeline masquerading as Fan-out.
2. **Missing fan-in** — dispatching parallel work with no consolidating merge task. Produces disjointed output.
3. **Self-review** — omitting the reviewer task in Producer-Reviewer because "the producer will check its own work." Violates the separation that makes review effective.
4. **Worker-level expert routing** — attempting to inject persona context into workers for "expert execution." Violates the Phase 7 research finding that bare workers produce better code (see R7.d for required phrasing).
5. **Pattern sprawl** — declaring a named pattern when Supervisor would do. Supervisor is the default; name another pattern only when its shape is genuinely different.

### R4: Planning-Procedure Integration

Edit `skills/spec/references/planning-procedure.md` to add a catalog-consultation step that runs during plan writing.

**Placement:** Add a new numbered section between existing section 1 ("Scope Check") and section 2 ("Map File Structure") — or, at the spec author's discretion, as a new subsection within section 2 — titled "Pick Execution Pattern" or equivalent. The exact section number must fit the existing numbering scheme; renumber downstream sections if necessary.

**Required content** (wording may vary for flow, but substance is fixed):

> Before mapping file structure, read `references/execution-patterns.md` and pick the pattern that matches the work's shape. Declare the chosen pattern in the plan header as `**Execution Pattern:** <name>`. For multi-phase plans, declare a pattern per phase under each phase heading. **Supervisor is the default** when nothing else fits — but don't name a pattern just to name something.

**Header format update:** The "Plan Document Header" section (currently section 3) must show the `**Execution Pattern:**` field in its template. Place it after `**Goal:**` and before `**Architecture:**`. The field is required on every plan written under the updated procedure.

**Per-phase declaration format:** For plans with explicit phases (see the Large Task example), each phase heading may include an inline pattern declaration. The catalog's "Combining patterns" section (R1.7) is the authoritative reference for the format.

**Use of "Phase 8":** Inside `planning-procedure.md`, it is acceptable to reference "Phase 8" when describing when the catalog is consulted, because `planning-procedure.md` is internal to `gigo:spec` where "Phase 8" unambiguously means plan writing. This exception applies only to `planning-procedure.md` — not to the catalog file itself (see R7.b).

### R5: Example-Plan Updates

Edit `skills/spec/references/example-plan.md` to reflect the new header field and add two new short examples.

**Required edits:**

1. **Add `**Execution Pattern:**` header field to all three existing examples** (Small, Medium, Large). Place it between `**Goal:**` and `**Architecture:**` in each example's header. Assign:
   - Small Task (mobile login fix): `**Execution Pattern:** Supervisor`
   - Medium Task (Stripe subscriptions): `**Execution Pattern:** Supervisor`
   - Large Task (frontend migration): `**Execution Pattern:** Supervisor` at the top, with per-phase declarations added under each Phase heading. The spec author reads the existing example's dependency graph and assigns the right pattern to each phase (Phase 1's Task 1 → Task 2 is a short sequential chain; Phase 2's three parallel tasks followed by Phase 3's `blocked-by: [3, 4, 5]` Task 6 is a fan-out with a fan-in-equivalent consolidation; Phase 4 is single-task). The goal is showing how per-phase declarations work in practice — not forcing any specific pattern onto any specific phase.

2. **Add one new short Fan-out/Fan-in example.** It may be software or non-software (e.g., a report-writing plan with three parallel section drafts plus a synthesis task). Show the `**Execution Pattern:** Fan-out/Fan-in` header, a parallel wave of 3 tasks marked `parallelizable: true`, and a single fan-in task with `blocked-by: [1, 2, 3]` (or equivalent). Keep the example short — ≤30 lines of task content.

3. **Add one new short Pipeline example.** It must be a clearly sequential workflow (e.g., a research pipeline: gather → extract → synthesize → write). Show the `**Execution Pattern:** Pipeline` header, tasks all marked `parallelizable: false`, and a linear `blocked-by` chain. Keep the example short — ≤25 lines of task content.

**Placement:** The two new examples may be inserted after the Small Task example or after the Medium Task example. The spec author picks the placement that reads best; both are acceptable.

### R6: SKILL.md Pointer

Edit `skills/spec/SKILL.md` to add a one-line pointer directing readers to the new catalog.

**Placement:** Near the Phase 8 section (currently around `skills/spec/SKILL.md:122`). Add the pointer inline in the Phase 8 text, or in the "Pointers" section at the bottom (currently around line 192) — the spec author picks whichever placement is cleaner.

**Required text** (wording may vary for flow):

> For task decomposition during the plan-writing phase (Phase 8), read `references/execution-patterns.md` to pick an execution pattern.

**Phase 7/8 disambiguation:** The first mention of the plan-writing phase in SKILL.md's edited text must use the form "plan-writing phase (Phase 8)" to anchor the phase number to its meaning inside spec's namespace. Subsequent references within the same section may use "Phase 8" on its own.

### R7: Content Constraints (Fact-Check Fixes)

These constraints come from the fact-check that ran on the design brief. A bare worker reading the spec must apply them to the catalog text.

**R7.a — No `_workspace/` convention.** The catalog must not reference `_workspace/` as a GIGO convention in any pattern's "GIGO mapping" or "Plan shape" field, and must not describe GIGO data passing as using a workspace directory. GIGO today flows data between tasks through plan "What Was Built" addendums and git branches from isolated worktrees. If data passing is discussed at all in any pattern entry, it must use this accurate description.

**R7.b — "Plan writing" language, not "Phase 8", inside the catalog.** The catalog file `execution-patterns.md` must use the phrase "during plan writing" or "when decomposing tasks" and must **not** contain the phrase "Phase 8" or "Phase 7" as standalone phase references. The reason: the catalog is read by humans and agents outside the `gigo:spec` phase namespace, where "Phase 7" would collide with the unrelated GIGO research phase 7 (the bare-worker finding). Cross-references into spec phases belong in `planning-procedure.md` and `SKILL.md`, not in the catalog.

**R7.c — Lineage note is required.** See R1.2 — the lineage note stating the catalog adapts harness's six patterns and omits Hierarchical Delegation must appear as a distinct item near the top of the catalog, before the pattern entries.

**R7.d — Bare-worker finding must be qualified.** Any mention of the research finding that bare workers produce better code (which appears in the Expert Pool entry and in the Worker-level expert routing anti-pattern) must use one of these forms:
- "Phase 7 research finding" (fully qualified)
- "bare-worker research finding" (semantic qualification)
- "research finding that bare workers produce better code" (descriptive)

The phrase "**Phase 7**" on its own is **forbidden** in the catalog text. It is unambiguous to readers inside `gigo:spec`'s phase namespace but ambiguous to readers outside it.

### R8: Non-Changes (Explicit Preservation)

The following must remain untouched in Cycle 1. A bare worker implementing this spec must not modify them.

- `skills/execute/SKILL.md` and all files under `skills/execute/references/`
- `skills/verify/SKILL.md` and all files under `skills/verify/references/`
- Any file under `skills/gigo/`, `skills/maintain/`, `skills/sweep/`, `skills/retro/`, `skills/snap/`, `skills/blueprint/`
- `CLAUDE.md`, `.claude/rules/`, `.claude/references/` in the GIGO repo
- Plans or specs in `docs/gigo/` other than the ones this spec produces
- Memory files under `~/.claude/projects/`

`gigo:execute` continues to read `blocks:`, `blocked-by:`, and `parallelizable:` as its sole dispatch signals. The new `**Execution Pattern:**` header and optional `review-lens:` task field are metadata that execute ignores today. Plans written before this cycle (without the field) remain valid and executable.

### R9: Backwards Compatibility

Plans that omit the `**Execution Pattern:**` header remain valid. The catalog and planning-procedure edits prescribe declaring the field in all **new** plans written after Cycle 1, but no validation, lint, or hook blocks existing plans from running. Cycle 1 adds vocabulary; it does not enforce it.

---

## Verb Trace

Action verbs extracted from the Original Request, traced to requirements:

| Verb | Requirement | Status |
|---|---|---|
| read (briefs/03-...) | Exploration verb, not a deliverable — handled during blueprint phase | N/A (not a deliverable) |
| build / catalog | R1 (catalog file), R2 (per-pattern content), R3 (anti-patterns) | ✅ |
| choose (the right execution shape) | R4 (planning-procedure integration enables pattern selection), R6 (SKILL.md pointer triggers catalog consultation) | ✅ |
| ship (Part A) | R8 (execute untouched), R9 (backwards compatibility), R5 (example plans updated) | ✅ |
| improve (planning) | R1-R6 collectively produce the planning-quality improvement | ✅ |
| design (Part B) | **Out of scope** — Cycle 2 is a separate future spec | ⏸ Deferred to Cycle 2 |
| use (Agent Teams API) | **Out of scope** — Cycle 2 | ⏸ Deferred to Cycle 2 |

The two deferred verbs belong to Part B (Agent Teams rebuild). The operator explicitly chose to phase the work into two cycles (see design brief Phase 3, Approach 1). Cycle 1 covers Part A's verbs in full. Cycle 2 will cover the deferred verbs with its own spec.

No verb from the Original Request is unaddressed without justification.

---

## Conventions

### Writing voice

- **Direct and prescriptive.** Match the tone of existing `skills/spec/references/planning-procedure.md` and `example-plan.md`. No softening hedges, no ceremony.
- **Domain-agnostic.** Examples span at least two domains (code and non-code). The catalog must remain useful when an assembled project writes fiction, runs research, or designs games.
- **Second-person address** where appropriate ("pick the pattern," "declare it in the header"). Matches existing reference voice.

### Catalog layout uniformity

- All 5 pattern entries use the same 5 fields in the same order (R2). A reader scanning the catalog should be able to skim any entry and know exactly which field they're reading.
- Field headings use bold markdown (`**Definition**`, `**When to use**`, etc.) — not H3 headers — to keep each entry visually compact.
- Pattern names use sentence case followed by a slash or `—` when abbreviated: "Fan-out/Fan-in" (not "fan out fan in").

### Markdown formatting

- Use plain markdown tables where dense comparison helps (e.g., the pattern comparison in R2). Avoid HTML.
- Code blocks for plan snippets use the `markdown` language tag so they render as illustrative (not as runnable code).
- No inline images, no diagrams. The decision tree in R1.5 is plain text (indented bullets or arrow strings like `task has strict sequencing → Pipeline`).

### Token economics

- The catalog is **reference-tier**: loaded on demand by `gigo:spec` during plan writing, not auto-loaded in every conversation.
- Target length ≈200 lines. Exceeding is acceptable for genuine content; padding is not.
- No restatement of content already in `planning-procedure.md` or `example-plan.md`. Cross-reference by filename when needed.

### Boundaries

This spec introduces or modifies the following integration boundaries between files — reviewers should check these seams:

1. **Catalog ↔ planning-procedure.md.** `planning-procedure.md` references `references/execution-patterns.md` by relative path. The filename and path must match exactly. If the catalog is renamed, all references must update together.
2. **Catalog ↔ example-plan.md.** The `**Execution Pattern:**` header field format in the catalog (R1.4, R2) must match the header field format shown in the example plans (R5). Drift between the two will confuse planners.
3. **Catalog ↔ SKILL.md pointer.** The pointer in `SKILL.md` (R6) references the catalog by the same relative path as `planning-procedure.md`. All three files name the catalog consistently.
4. **`review-lens:` tag ↔ future `gigo:verify` enhancement.** The tag is metadata-only in Cycle 1; the design anticipates future enforcement in `gigo:verify`. The catalog must state this explicitly (R2, Expert Pool clarification) so readers don't expect enforcement today. If a future Cycle adds enforcement, the catalog entry is the reference point.

### Domain-agnostic examples (suggested, not required verbatim)

Patterns may use examples from any of these domains to prove domain-agnosticism:

- **Supervisor:** a build pipeline, a marketing campaign launch, a research project manager delegating sub-studies
- **Pipeline:** research synthesis (gather → extract → synthesize → write), data transformation (raw → clean → analyze → report), content production (draft → edit → review → publish)
- **Fan-out/Fan-in:** multi-section report writing (each section parallel, then a merge pass), multi-platform release builds (parallel targets, then a unified release note), multi-contributor survey analysis (parallel analyses, then a cross-comparison)
- **Producer-Reviewer:** draft + fact-check, design + accessibility review, code + security audit at task level
- **Expert Pool:** a plan with mixed security-sensitive, UX-sensitive, and data-sensitive tasks that should each be reviewed with the matching lens

The spec author picks the examples that illustrate each pattern clearly without becoming the longest part of the entry.

---

## File Structure

Files touched in this cycle:

| File | Change | Approx. size |
|---|---|---|
| `skills/spec/references/execution-patterns.md` | **Create** | ~200 lines |
| `skills/spec/references/planning-procedure.md` | **Modify** — add catalog-consultation section and update header template (R4) | +~15 lines |
| `skills/spec/references/example-plan.md` | **Modify** — add header field to 3 existing examples, add 2 new short examples (R5) | +~60 lines |
| `skills/spec/SKILL.md` | **Modify** — add one-line pointer (R6) | +~1-2 lines |

No other files in the GIGO repo are modified.

---

## Acceptance Criteria

Cycle 1 is done when all of the following are true. Each item is independently checkable.

1. **Catalog file exists** at `skills/spec/references/execution-patterns.md` and contains all 8 top-level sections from R1 in the specified order.
2. **All 5 patterns are present** (Supervisor, Pipeline, Fan-out/Fan-in, Producer-Reviewer, Expert Pool) in the specified order, each with the 5 uniform fields from R2.
3. **Lineage note is present** near the top of the catalog, stating the adaptation from harness's six patterns and the omission of Hierarchical Delegation (R1.2, R7.c).
4. **Expert Pool entry explicitly states** that workers remain bare and that `review-lens:` is metadata-only in Cycle 1 (R2, Expert Pool clarification).
5. **Anti-patterns section names all 5 mistakes** from R3 in 2-3 lines each.
6. **Catalog contains no standalone "Phase 7" or "Phase 8" references** — verified by `grep -c "Phase 7\|Phase 8" skills/spec/references/execution-patterns.md` returning 0 for standalone phase references (qualified forms like "Phase 7 research finding" are allowed and expected) (R7.b, R7.d).
7. **Catalog contains no `_workspace/` references** — verified by `grep -c "_workspace" skills/spec/references/execution-patterns.md` returning 0 (R7.a).
8. **planning-procedure.md has a catalog-consultation step** per R4, placed between sections 1 and 2 (or inside section 2), with the required content.
9. **planning-procedure.md's Plan Document Header template includes** `**Execution Pattern:**` between `**Goal:**` and `**Architecture:**`.
10. **example-plan.md's three existing examples** all carry the `**Execution Pattern:**` header field.
11. **example-plan.md contains two new examples**: one Fan-out/Fan-in and one Pipeline, each ≤30 lines, demonstrating the pattern clearly.
12. **skills/spec/SKILL.md contains a one-line pointer** to `references/execution-patterns.md` near its Phase 8 section or Pointers section (R6).
13. **`gigo:execute`'s files are unchanged** — verified by `git diff --stat skills/execute/` returning no changes.
14. **Any existing plan written before Cycle 1 still runs** without error when passed to `gigo:execute` — pick any plan under `docs/gigo/plans/` that predates this spec and confirm it executes without error, confirming backwards compatibility (R9).
15. **A new plan written after Cycle 1** declares an `**Execution Pattern:**` header field, confirming the procedure update took effect.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Planners use the catalog as a cargo-cult naming exercise, declaring patterns without understanding them | Anti-patterns section names "Pattern sprawl" explicitly; Supervisor is stated as the default throughout |
| Catalog drifts from planning-procedure.md wording | Boundaries section (R2, R3 of Conventions) calls this out; all three files name the catalog consistently |
| Expert Pool confuses readers who expect worker context routing | Expert Pool entry explicitly states workers stay bare and `review-lens:` is metadata-only; anti-pattern "Worker-level expert routing" reinforces this |
| Future enforcement of `review-lens:` breaks backwards compatibility | Cycle 1 explicitly states the tag is metadata-only; enforcement is a future enhancement with its own spec cycle |
| Namespace collision ("Phase 7/8") causes confusion | R7.b and R7.d pin the exact required phrasing; acceptance criterion 6 verifies via grep |
| `_workspace/` stale convention leaks into catalog | R7.a pins the constraint; acceptance criterion 7 verifies via grep |

---

## Notes for the Bare Worker Implementing This Spec

- You are implementing **Cycle 1 only**. Do not touch `gigo:execute`, `gigo:verify`, or any file outside `skills/spec/`. If a task description tells you to do so, treat it as an error and stop.
- The fact-check constraints in R7 are non-negotiable. They come from a separate validation pass on the design brief and catch real ambiguities that would confuse readers outside spec's phase namespace.
- When in doubt about a pattern's example, pick a non-software example. The catalog must remain useful for assembled projects that don't write code.
- If a step says "use wording X" and you find wording Y reads better, prefer the substance of X over the exact letters — unless X is specifically called out as "required verbatim" (only the forbidden phrasings in R7 are verbatim).
- The catalog is reference-tier. Do not add it to any rules file. Do not auto-load it from any skill's entry point.
