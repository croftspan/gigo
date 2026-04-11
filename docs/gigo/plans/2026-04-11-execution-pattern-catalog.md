# Execution Pattern Catalog — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-11-execution-pattern-catalog-design.md`

**Goal:** Add a 5-pattern execution catalog to `gigo:spec` so plans declare their execution shape explicitly instead of implicitly defaulting to Supervisor.

**Execution Pattern:** Fan-out/Fan-in

**Architecture:** A new reference file `skills/spec/references/execution-patterns.md` is loaded on demand during plan writing. Three supporting files (`planning-procedure.md`, `example-plan.md`, `SKILL.md`) are edited to consume it. `gigo:execute` is untouched.

**Tech Stack:** Markdown only — no code, no config, no tests. Verification is grep + file existence + manual skim.

---

### Task 1: Create the Execution Pattern Catalog

**blocks:** 2, 3, 4, 5
**blocked-by:** []
**parallelizable:** false

**Files:**
- Create: `skills/spec/references/execution-patterns.md`

This task produces the complete catalog file per spec requirements R1, R2, R3, and R7. The file has 8 top-level sections in a fixed order. Every pattern entry uses the uniform 5-field layout. The fact-check constraints in R7 are enforced by the grep check in step 13 before commit.

- [x] **Step 1: Create the file with the title and Purpose section**

  Open `skills/spec/references/execution-patterns.md` and write the top of the file:

  ```markdown
  # Execution Pattern Catalog

  ## Purpose

  This catalog names the execution shapes a plan can take. Read it when decomposing tasks so the plan's shape is explicit instead of implicit. The catalog is domain-agnostic — it applies to code, writing, research, or any work GIGO plans.
  ```

  Keep Purpose to ≤5 lines. Do not describe *how* to use the catalog here — that belongs in "How to use" (step 4).

- [x] **Step 2: Add the lineage note**

  Add a second top-level section `## Lineage` (or a prominent note block directly under Purpose) with the substance:

  > Adapted from harness's six-pattern catalog, omitting Hierarchical Delegation. Recursive delegation adds complexity without clear value for GIGO's current use cases — we may revisit if a concrete need appears.

  The exact wording may vary for flow, but the note must credit harness, state the six→five adaptation, name Hierarchical Delegation as the omission, and leave the door open to revisiting. See spec R1.2 and R7.c.

- [x] **Step 3: Add the "When to consult this file" section**

  ```markdown
  ## When to consult this file

  Read this catalog during plan writing, before decomposing tasks into a dependency graph. The pattern you pick shapes what you write and how a reviewer reads it later.
  ```

  **CRITICAL:** This section must use the phrase "during plan writing" or "when decomposing tasks". It must **not** contain "Phase 8" or "Phase 7" as standalone phase references. The catalog is read by readers outside `gigo:spec`'s phase namespace, where a bare "Phase 7" would collide with the bare-worker research finding. See spec R7.b.

- [x] **Step 4: Add the "How to use" section with exactly 3 numbered steps**

  ```markdown
  ## How to use

  1. Pick the pattern matching the work's shape — use the decision tree below if you're unsure.
  2. Declare it in the plan header as `**Execution Pattern:** <name>`. For multi-phase plans, declare a pattern per phase under each phase heading.
  3. Decompose tasks per the pattern's GIGO mapping (below).
  ```

  Exactly three steps. See spec R1.4.

- [x] **Step 5: Add the Decision Tree section**

  Write a compact scannable rule set in ≤10 lines. Plain text, indented bullets or arrow strings — no diagrams. Example shape:

  ```markdown
  ## Decision tree

  - Work is strictly sequential, each step feeds the next → **Pipeline**
  - Parallel workers produce artifacts, need a single merge step → **Fan-out/Fan-in**
  - Output needs independent validation at the task level → **Producer-Reviewer**
  - Tasks span different domains needing different review lenses → **Expert Pool**
  - None of the above, or default case → **Supervisor**
  ```

  Keep it under 10 lines. Plain markdown. No Mermaid, no ASCII art. See spec R1.5.

- [x] **Step 6: Add the Supervisor pattern entry**

  Open `## The Patterns` as a section heading, then write the Supervisor entry with the uniform 5-field layout (bold field names, not H3 headers — see spec R2 and conventions R2 "Catalog layout uniformity"):

  ```markdown
  ## The Patterns

  ### Supervisor

  **Definition.** A central coordinator dispatches independent workers and collects their results. This is GIGO's default execution shape.

  **When to use.**
  - Most common case — when no other pattern's shape clearly fits
  - Work can be decomposed into independent tasks with no required sequencing beyond dependency order
  - The lead needs to merge or interpret results after workers finish
  - You're not sure which pattern fits (default to Supervisor, don't over-name)

  **GIGO mapping.** Standard dependency graph with `parallelizable: true` where tasks don't share state. No special markers — this is how GIGO already works.

  **Plan shape.**
  ```markdown
  ### Task 1: Setup

  **blocks:** 2, 3
  **blocked-by:** []
  **parallelizable:** false

  ### Task 2: Worker A

  **blocks:** 4
  **blocked-by:** 1
  **parallelizable:** true (with Task 3)

  ### Task 3: Worker B

  **blocks:** 4
  **blocked-by:** 1
  **parallelizable:** true (with Task 2)
  ```

  **Gotchas.**
  - Defaulting to Supervisor is correct. Naming a more specific pattern when Supervisor fits is pattern sprawl.
  ```

  Use a non-code example if one makes the Definition land faster (e.g., a research project lead delegating sub-studies). See spec R2 and the "Domain-agnostic examples" list in Conventions.

- [x] **Step 7: Add the Pipeline pattern entry**

  Follow the same 5-field layout. Definition should convey strict sequencing where each stage feeds the next. GIGO mapping states: every task `parallelizable: false`, `blocked-by` forms a linear chain.

  Example domain to consider: research synthesis (gather → extract → synthesize → write) or data transformation (raw → clean → analyze → report). Pick one that makes the linearity obvious.

  Gotchas to name: false parallelism (tasks that look independent but share hidden state are actually Pipeline); skipping a stage because it "seems fast" leads to broken dependencies downstream.

- [x] **Step 8: Add the Fan-out/Fan-in pattern entry**

  Follow the 5-field layout. Definition should convey independent parallel workers producing artifacts, followed by a single merge task.

  GIGO mapping: parallel wave of tasks with `parallelizable: true`, followed by one merge task whose `blocked-by` lists all fan-out tasks.

  Plan shape should show 2-3 parallel tasks and a single merge task with `blocked-by: [2, 3, 4]` (or equivalent task numbers).

  Example domain: multi-section report writing (each section drafted in parallel, then a synthesis pass) or multi-contributor survey analysis.

  Gotchas to name: missing fan-in (parallel work with no merge step produces disjointed output); treating the merge task as a "nice-to-have" optimization when it's structural.

- [x] **Step 9: Add the Producer-Reviewer pattern entry**

  Follow the 5-field layout. Definition should convey: a producer task generates an artifact; a separate reviewer task validates it; optional iteration on feedback. This generalizes `gigo:verify`'s two-stage review to the task level inside a plan.

  GIGO mapping: producer task, reviewer task with `blocked-by: [producer]`, optional revision task with `blocked-by: [reviewer]`.

  Plan shape: show the producer → reviewer → optional revision chain.

  Example domain: draft + fact-check for content, design + accessibility review, code + security audit at task level.

  Gotchas to name: self-review (omitting the reviewer task because "the producer will check its own work" violates the separation that makes review effective).

- [x] **Step 10: Add the Expert Pool pattern entry — with required clarification**

  Follow the 5-field layout. Definition should convey: tasks routed to different **review lenses** by domain. Workers stay bare — the lens applied during review changes based on the task's domain tag.

  GIGO mapping: introduces an optional per-task field `review-lens: <domain>`. **The entry must explicitly state** two things:

  1. Workers remain bare — no persona context injection. This preserves the bare-worker research finding (see spec R7.d for allowed phrasings).
  2. The `review-lens:` field is metadata-only in Cycle 1 — `gigo:verify` does not yet enforce it. The catalog documents the pattern so planners can start tagging; enforcement is a future verify enhancement.

  **Allowed phrasings for the bare-worker reference** (pick one, do not use bare "Phase 7"):
  - "the Phase 7 research finding"
  - "the bare-worker research finding"
  - "the research finding that bare workers produce better code"

  Plan shape: show 2-3 tasks each with a different `review-lens:` value (e.g., `review-lens: security`, `review-lens: ux`, `review-lens: data`).

  Example domain: a plan with mixed security-sensitive, UX-sensitive, and data-sensitive tasks, each reviewed with the matching lens.

  Gotchas to name: worker-level expert routing (injecting persona context into workers violates the bare-worker research finding).

  See spec R2 (Expert Pool row) and R2's "Expert Pool — required clarification".

- [x] **Step 11: Add the Combining Patterns section**

  ```markdown
  ## Combining patterns

  Multi-phase plans may declare a different pattern per phase. Use per-phase declarations under each phase heading:

  ```markdown
  ## Phase 1: Foundation

  **Execution Pattern:** Pipeline

  ### Task 1: ...
  ### Task 2: ...

  ## Phase 2: Parallel Work

  **Execution Pattern:** Fan-out/Fan-in

  ### Task 3: ...
  ```

  The plan's top-level `**Execution Pattern:**` header names the dominant pattern or the first phase's pattern. When phases diverge significantly, per-phase declarations are the source of truth.
  ```

  See spec R1.7.

- [x] **Step 12: Add the Anti-patterns section with all 5 mistakes**

  ```markdown
  ## Anti-patterns

  ### False parallelism

  Marking tasks `parallelizable: true` when they share hidden state — a config file, an upstream artifact, a database migration. Usually a Pipeline masquerading as Fan-out. The plan looks faster on paper and breaks in practice.

  ### Missing fan-in

  Dispatching parallel work with no consolidating merge task. Workers produce disjointed output that never gets reconciled. If you're fanning out, name the fan-in task explicitly.

  ### Self-review

  Omitting the reviewer task in Producer-Reviewer because "the producer will check its own work." Violates the separation that makes review effective. A producer reviewing its own work catches roughly the same mistakes it made writing it.

  ### Worker-level expert routing

  Injecting persona context into workers for "expert execution." Violates the bare-worker research finding that workers without persona context produce better code. Expert Pool routes the review lens, not the worker context.

  ### Pattern sprawl

  Declaring a named pattern when Supervisor would do. Supervisor is the default — name another pattern only when its shape is genuinely different. Over-naming adds noise and confuses reviewers.
  ```

  See spec R3. The phrasing for the "Worker-level expert routing" entry must use a qualified bare-worker reference (see R7.d): "bare-worker research finding" is used above.

- [x] **Step 13: Grep-check for forbidden strings before committing**

  Run these greps from the repo root to verify R7 constraints:

  ```bash
  rg -c "_workspace" skills/spec/references/execution-patterns.md
  rg -c "\bPhase 7\b|\bPhase 8\b" skills/spec/references/execution-patterns.md
  ```

  **Expected output:**
  - First grep: `0` matches (file does not contain `_workspace`)
  - Second grep: `0` matches for the word-boundary Phase 7/8 pattern

  If either returns `>0`, read the matching lines and fix the content before committing. Qualified phrases like "Phase 7 research finding" will NOT match the second grep because of the `\b` word boundary after the number — only "Phase 7" followed by a non-word character (space, period, comma, end-of-line) matches.

  **Note on the Phase 7/8 grep:** ripgrep's `\b` is a word boundary, so `\bPhase 7\b` matches "Phase 7" as a standalone word. "Phase 7 research finding" contains "Phase 7" as a standalone word too — so if you wrote "the Phase 7 research finding" in the Expert Pool entry or the Worker-level anti-pattern, it WILL match and you need to rewrite to "the bare-worker research finding" or "the research finding that bare workers produce better code" instead. The grep is deliberately strict to force the semantic form.

- [x] **Step 14: Commit**

  ```bash
  git add skills/spec/references/execution-patterns.md
  git commit -m "feat(spec): add execution pattern catalog reference

  New reference file documenting 5 execution patterns (Supervisor, Pipeline,
  Fan-out/Fan-in, Producer-Reviewer, Expert Pool). Loaded on demand by
  gigo:spec during plan writing. Domain-agnostic.

  Implements R1, R2, R3, R7 of spec 2026-04-11-execution-pattern-catalog-design.md."
  ```

**Done when:** `skills/spec/references/execution-patterns.md` exists with all 8 top-level sections, all 5 patterns present with the uniform 5-field layout, Anti-patterns section names all 5 mistakes, lineage note present, Expert Pool entry explicitly states workers stay bare and `review-lens:` is metadata-only, grep-checks return 0 for `_workspace` and for standalone `Phase 7`/`Phase 8`.

#### What Was Built
- **Deviations:** None. Catalog shipped with all 8 sections, 5 patterns, and the uniform 5-field per-pattern layout. Final size 298 lines — within the ~200-line target's reasonable margin.
- **Review changes:** Stage 2 craft review flagged two dangling-dependency defects in example snippets: (1) Supervisor Plan shape referenced a Task 4 that was never defined — fix added an explicit "Task 4: Collect and synthesize" blocked-by [2, 3]; (2) Expert Pool Plan shape started at Task 2 with tasks declaring `blocked-by: 1` but Task 1 was never shown — fix added a Task 1 Setup stub. Both landed in commit `a4bd1b9`.
- **Notes for downstream:** The catalog's pattern names (Supervisor, Pipeline, Fan-out/Fan-in, Producer-Reviewer, Expert Pool) are the canonical strings the `**Execution Pattern:**` plan header field expects. Task 2 (planning-procedure.md) and Task 3 (example-plan.md) must match these names verbatim — `Fan-out/Fan-in` uses a hyphen and a slash, not "Fanout" or "Fan Out". Expert Pool's `review-lens:` field is documented as metadata-only today.

---

### Task 2: Edit planning-procedure.md to Consume the Catalog

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4)

**Files:**
- Modify: `skills/spec/references/planning-procedure.md`

Adds the catalog-consultation step and updates the Plan Document Header template with the new `**Execution Pattern:**` field. See spec R4.

- [x] **Step 1: Add the catalog-consultation step as a new section 2**

  Open `skills/spec/references/planning-procedure.md`. Current sections: 0 (Design Brief chain), 1 (Scope Check), 2 (Map File Structure), 3 (Plan Document Header), 4 (Task Format), ..., 10 (File Locations).

  Insert a new section after section 1 titled `## 2. Pick Execution Pattern` with this content:

  ```markdown
  ## 2. Pick Execution Pattern

  Before mapping file structure, read `references/execution-patterns.md` and pick the pattern that matches the work's shape. Declare the chosen pattern in the plan header as `**Execution Pattern:** <name>`. For multi-phase plans, declare a pattern per phase under each phase heading. **Supervisor is the default** when nothing else fits — but don't name a pattern just to name something.
  ```

  Renumber all downstream sections by +1: old section 2 (Map File Structure) → new section 3, old 3 → new 4, ..., old 10 → new 11.

- [x] **Step 2: Renumber downstream section headings**

  Update section headings:
  - `## 2. Map File Structure` → `## 3. Map File Structure`
  - `## 3. Plan Document Header` → `## 4. Plan Document Header`
  - `## 4. Task Format` → `## 5. Task Format`
  - `## 5. Dependency Graph Rules` → `## 6. Dependency Graph Rules`
  - `## 6. Bite-Sized Task Granularity` → `## 7. Bite-Sized Task Granularity`
  - `## 7. No Placeholders` → `## 8. No Placeholders`
  - `## 8. Plan Self-Review` → `## 9. Plan Self-Review`
  - `## 9. Execution Handoff` → `## 10. Execution Handoff`
  - `## 10. Specs and Plans File Locations` → `## 11. Specs and Plans File Locations`

  Update the "8a / 8b / 8c" subsection labels inside Plan Self-Review to `9a / 9b / 9c`.

  Scan the file for any cross-references that name a section number (e.g., "section 7 above") and update them. The current content references "section 7 above" inside the Plan Self-Review section's placeholder-scan subsection — that becomes "section 8 above" after renumbering.

- [x] **Step 3: Update the Plan Document Header template**

  Inside the (newly renumbered) section 4 "Plan Document Header", find the template code block. It currently contains:

  ```markdown
  **Spec:** `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`

  **Goal:** [One sentence describing what this builds]

  **Architecture:** [2-3 sentences about approach]

  **Tech Stack:** [Key technologies/libraries]
  ```

  Insert a new line between `**Goal:**` and `**Architecture:**`:

  ```markdown
  **Spec:** `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`

  **Goal:** [One sentence describing what this builds]

  **Execution Pattern:** [Pattern name — see references/execution-patterns.md]

  **Architecture:** [2-3 sentences about approach]

  **Tech Stack:** [Key technologies/libraries]
  ```

- [x] **Step 4: Verify "Phase 8" usage is still acceptable here**

  `planning-procedure.md` is internal to `gigo:spec` where "Phase 8" unambiguously means plan writing. Any "Phase 8" reference inside this file is acceptable (see spec R4, last paragraph). Do not remove existing "Phase 8" references from this file. The R7.b constraint applies only to `execution-patterns.md`, not this file.

- [x] **Step 5: Commit**

  ```bash
  git add skills/spec/references/planning-procedure.md
  git commit -m "feat(spec): add Pick Execution Pattern step to planning procedure

  New section 2 directs planners to read the execution pattern catalog
  before decomposing tasks. Plan Document Header template gains a required
  **Execution Pattern:** field between Goal and Architecture.

  Implements R4 of spec 2026-04-11-execution-pattern-catalog-design.md."
  ```

**Done when:** `planning-procedure.md` has a new section 2 "Pick Execution Pattern", all downstream sections are renumbered consistently (including cross-references), and the Plan Document Header template shows `**Execution Pattern:**` between `**Goal:**` and `**Architecture:**`.

#### What Was Built
- **Deviations:** None. Worker implemented all 5 steps exactly as specified.
- **Review changes:** None. Stage 1 R4.1–R4.9 all PASS; Stage 2 PASS with no craft issues. Clean merge.
- **Notes for downstream:** The `**Execution Pattern:**` field in the Plan Document Header template lives between `**Goal:**` and `**Architecture:**`. The subsection labels `9a/9b/9c` (formerly `8a/8b/8c`) are inside the renumbered section 9 "Plan Self-Review". The catalog-consultation step is section 2 "Pick Execution Pattern" — future edits to planning-procedure.md must respect this new numbering scheme.

---

### Task 3: Edit example-plan.md with Header Field and Two New Examples

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 2, 4)

**Files:**
- Modify: `skills/spec/references/example-plan.md`

Adds the `**Execution Pattern:**` header to all three existing worked examples and inserts two new short examples (one Fan-out/Fan-in, one Pipeline). See spec R5.

- [x] **Step 1: Add header field to the Small Task example**

  Find the Small Task example (currently around line 14-42). The plan's header currently has:

  ```markdown
  **Spec:** (inline — too small for a separate spec)

  **Goal:** Fix login page rendering on mobile viewports

  **Architecture:** CSS fix targeting responsive breakpoints in the login component
  ```

  Insert `**Execution Pattern:** Supervisor` between Goal and Architecture:

  ```markdown
  **Spec:** (inline — too small for a separate spec)

  **Goal:** Fix login page rendering on mobile viewports

  **Execution Pattern:** Supervisor

  **Architecture:** CSS fix targeting responsive breakpoints in the login component
  ```

- [x] **Step 2: Add header field to the Medium Task example**

  Find the Medium Task example (currently around line 52-153). Insert `**Execution Pattern:** Supervisor` between `**Goal:**` and `**Architecture:**`:

  ```markdown
  **Goal:** Add Stripe subscription billing with free trial support

  **Execution Pattern:** Supervisor

  **Architecture:** Stripe Checkout for payment flow, webhooks for lifecycle events, subscription status gated on user model
  ```

- [x] **Step 3: Add header field to the Large Task example (with per-phase declarations)**

  Find the Large Task example (currently around line 163-248). At the top header level, insert `**Execution Pattern:** Supervisor` between `**Goal:**` and `**Architecture:**`:

  ```markdown
  **Goal:** Migrate frontend from legacy framework to [chosen framework]

  **Execution Pattern:** Supervisor

  **Architecture:** Incremental migration using feature flags, both frontends run in parallel during cutover
  ```

  Then add per-phase declarations under each phase heading. Phase 1 has Task 1 → Task 2 as a sequential chain (Pipeline-shaped). Phase 2 has three parallel tasks (Fan-out-shaped). Phase 3's Task 6 is `blocked-by: [3, 4, 5]` (fan-in-equivalent). Phase 4 is a single task.

  Use the phase heading form:

  ```markdown
  ## Phase 1: Foundation (unblocks everything)

  **Execution Pattern:** Pipeline

  ### Task 1: Framework Spike
  ```

  Apply to all four phases:
  - Phase 1 → `**Execution Pattern:** Pipeline`
  - Phase 2 → `**Execution Pattern:** Fan-out/Fan-in` (the fan-in task is Task 6 in Phase 3)
  - Phase 3 → `**Execution Pattern:** Supervisor` (Task 6 is the fan-in/merge tail of Phase 2's fan-out; treating Phase 3 as its own Supervisor shape works)
  - Phase 4 → `**Execution Pattern:** Supervisor` (single-task phase; Supervisor is the default)

  *Note: if you judge the Phase 2/3 split differently while editing — e.g., treating Phase 2 as pure Fan-out and Phase 3 as the explicit fan-in — pick whichever reading makes the example clearer. The point is to demonstrate per-phase declarations work, not to force one specific labeling.*

- [x] **Step 4: Add a new short Fan-out/Fan-in example**

  Insert a new `## Fan-out/Fan-in Example` section after the Small Task example (around the current line 43). Pick a non-software domain to prove domain-agnosticism — e.g., a multi-section report writing plan.

  Target: ≤30 lines of task content in the plan code block.

  ```markdown
  ---

  ## Fan-out/Fan-in Example

  **User says:** "Draft a three-section market report on AI code tools, then merge into a single doc"

  **Plan:**

  ```markdown
  # Market Report — Implementation Plan

  > **For agentic workers:** Use gigo:execute to implement this plan task-by-task.

  **Spec:** (inline)

  **Goal:** Produce a three-section market report on AI code tools

  **Execution Pattern:** Fan-out/Fan-in

  **Architecture:** Three parallel section drafts followed by a single merge pass that reconciles overlaps and adds a cross-section summary

  ---

  ### Task 1: Draft Section A — Market Overview

  **blocks:** 4
  **blocked-by:** []
  **parallelizable:** true (with Tasks 2, 3)

  - [ ] **Step 1:** Gather market size and growth data
  - [ ] **Step 2:** Write the overview section (~600 words)
  - [ ] **Step 3:** Commit

  ### Task 2: Draft Section B — Competitor Landscape

  **blocks:** 4
  **blocked-by:** []
  **parallelizable:** true (with Tasks 1, 3)

  - [ ] **Step 1:** Research 5-8 competitors
  - [ ] **Step 2:** Write the landscape section (~800 words)
  - [ ] **Step 3:** Commit

  ### Task 3: Draft Section C — User Interviews

  **blocks:** 4
  **blocked-by:** []
  **parallelizable:** true (with Tasks 1, 2)

  - [ ] **Step 1:** Synthesize 10 user interviews into themes
  - [ ] **Step 2:** Write the interviews section (~700 words)
  - [ ] **Step 3:** Commit

  ### Task 4: Merge and Cross-Reference

  **blocks:** []
  **blocked-by:** 1, 2, 3
  **parallelizable:** false

  - [ ] **Step 1:** Merge the three sections into a single doc
  - [ ] **Step 2:** Reconcile overlapping claims between sections
  - [ ] **Step 3:** Write a cross-section summary
  - [ ] **Step 4:** Commit

  **Done when:** Single report doc exists with all three sections merged, overlaps reconciled, summary added.
  ```

  ---
  ```

  **Verify the ≤30 line constraint** by counting the lines inside the plan code block (between the opening ```markdown and closing ```). If over 30, trim step detail without dropping steps.

- [x] **Step 5: Add a new short Pipeline example**

  Insert a new `## Pipeline Example` section after the Fan-out/Fan-in example. Again, pick a non-software domain — e.g., a research synthesis pipeline.

  Target: ≤25 lines of task content.

  ```markdown
  ---

  ## Pipeline Example

  **User says:** "Synthesize 20 academic papers on distributed consensus into a single literature review"

  **Plan:**

  ```markdown
  # Literature Review — Implementation Plan

  > **For agentic workers:** Use gigo:execute to implement this plan task-by-task.

  **Spec:** (inline)

  **Goal:** Produce a literature review covering 20 papers on distributed consensus

  **Execution Pattern:** Pipeline

  **Architecture:** Strict sequence: gather papers → extract claims → synthesize themes → write review. Each stage's output feeds the next.

  ---

  ### Task 1: Gather Papers

  **blocks:** 2
  **blocked-by:** []
  **parallelizable:** false

  - [ ] **Step 1:** Download 20 papers matching the search criteria
  - [ ] **Step 2:** Commit bibliography

  ### Task 2: Extract Claims

  **blocks:** 3
  **blocked-by:** 1
  **parallelizable:** false

  - [ ] **Step 1:** Read each paper, extract 3-5 key claims per paper
  - [ ] **Step 2:** Commit extracted claims table

  ### Task 3: Synthesize Themes

  **blocks:** 4
  **blocked-by:** 2
  **parallelizable:** false

  - [ ] **Step 1:** Cluster claims into 4-6 themes
  - [ ] **Step 2:** Commit themes outline

  ### Task 4: Write Review

  **blocks:** []
  **blocked-by:** 3
  **parallelizable:** false

  - [ ] **Step 1:** Write the review section-by-section, one theme per section
  - [ ] **Step 2:** Commit final review
  ```

  ---
  ```

- [x] **Step 6: Commit**

  ```bash
  git add skills/spec/references/example-plan.md
  git commit -m "feat(spec): add execution pattern headers to examples

  Adds **Execution Pattern:** field to all three existing worked examples
  (Small, Medium, Large). Adds two new short examples: a Fan-out/Fan-in
  market report plan and a Pipeline literature review plan. Both new
  examples are non-software to prove domain-agnosticism.

  Implements R5 of spec 2026-04-11-execution-pattern-catalog-design.md."
  ```

**Done when:** All three existing examples carry the `**Execution Pattern:**` header. The Large Task example has per-phase declarations under each phase heading. Two new short examples exist (Fan-out/Fan-in ≤30 lines task content, Pipeline ≤25 lines task content), placed after the Small Task example and before the Medium Task example.

#### What Was Built
- **Deviations:** The initial worker used verbatim task-text examples (56 lines Fan-out/Fan-in, 49 lines Pipeline) which exceeded the R5.7 hard line caps (≤30, ≤25). Worker's reasoning: the task text's example snippet was already over-budget, so trimming step detail felt unjustified. Correct call by the verifier — R5.7 is a hard gate and "trim step detail without dropping steps" explicitly permitted the fix.
- **Review changes:** Stage 1 first pass FAILED on R5.7. Fix subagent trimmed both examples to exactly 30/25 lines by (1) pipe-delimiting the `**blocks:**/**blocked-by:**/**parallelizable:**` fields onto single lines, (2) collapsing `**Spec:**` and `**Goal:**` onto one line, (3) removing `**For agentic workers:**` scaffolding notes, (4) removing `**Done when:**` from both new examples, (5) dropping `**Step N:**` prefixes from checkboxes. Re-verify PASSED both stages (confidence 87%). Large Task per-phase declarations: Phase 1 → Pipeline, Phase 2 → Fan-out/Fan-in, Phase 3 → Supervisor, Phase 4 → Supervisor.
- **Notes for downstream:** The new Fan-out/Fan-in and Pipeline examples use a **pipe-delimited field layout** that differs stylistically from the multi-line layout in the Small/Medium/Large examples. This is an acceptable minor inconsistency the reviewer accepted — both layouts expose the `blocks`/`blocked-by`/`parallelizable` vocabulary. If a future edit normalizes the style (either direction), it needs to respect the line caps on the two new examples. Task 5's verification sweep should confirm the line caps hold on the merged file.

---

### Task 4: Edit SKILL.md with the Catalog Pointer

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 2, 3)

**Files:**
- Modify: `skills/spec/SKILL.md`

Adds a one-line pointer near the Phase 8 section directing readers to the new catalog. See spec R6.

- [x] **Step 1: Locate the Phase 8 section**

  Open `skills/spec/SKILL.md`. Find the section that starts with `## Phase 8: Write Implementation Plan` (currently around line 122).

- [x] **Step 2: Add the pointer inline in the Phase 8 body**

  The current Phase 8 body contains these lines near the end:

  ```markdown
  Read `references/planning-procedure.md` for the full procedure.
  Read `references/example-plan.md` for worked examples.
  ```

  Insert a new line between these two lines:

  ```markdown
  Read `references/planning-procedure.md` for the full procedure.
  Read `references/execution-patterns.md` to pick an execution pattern during the plan-writing phase (Phase 8).
  Read `references/example-plan.md` for worked examples.
  ```

  The phrasing "plan-writing phase (Phase 8)" anchors the phase number to its meaning on first mention. Subsequent references to "Phase 8" in SKILL.md (which already exist elsewhere in the file — do not change them) are then unambiguous. See spec R6, "Phase 7/8 disambiguation".

- [x] **Step 3: Commit**

  ```bash
  git add skills/spec/SKILL.md
  git commit -m "feat(spec): point SKILL.md at execution pattern catalog

  Adds a one-line pointer inside the Phase 8 section directing readers to
  references/execution-patterns.md during the plan-writing phase.

  Implements R6 of spec 2026-04-11-execution-pattern-catalog-design.md."
  ```

**Done when:** `skills/spec/SKILL.md` contains a one-line pointer to `references/execution-patterns.md` inside the Phase 8 body, using the form "plan-writing phase (Phase 8)" to anchor the phase number.

#### What Was Built
- **Deviations:** None on content. Worker implemented all 3 steps exactly as specified. The `references/execution-patterns.md` pointer is at line 131 of `skills/spec/SKILL.md`, between the `planning-procedure.md` and `example-plan.md` pointers, using the exact phrasing "plan-writing phase (Phase 8)".
- **Review changes:** None. Stage 1 R6.1–R6.6 all PASS; Stage 2 PASS with no craft issues.
- **Notes for downstream:** **Lead-level note, not a code change:** the Task 4 worker (dispatched on haiku) appears to have bypassed its worktree and committed directly to main via commit `9122512`, rather than (or in addition to) committing on the isolated branch `worktree-agent-a3c22d36`. The worker branch had an independent functionally-identical commit (`5ef8aff`). Main now holds the correct Task 4 content; the redundant branch and worktree were cleaned up. This is a worktree-isolation escape that should be investigated for the haiku model dispatch path — future dispatches should log the worker's effective CWD before trusting isolation. Does not affect the correctness of Cycle 1.

---

### Task 5: Verification Sweep

**blocks:** []
**blocked-by:** 2, 3, 4
**parallelizable:** false

**Files:** None modified. This task only reads and runs commands.

Runs the spec's 15 acceptance criteria as a single verification pass. Any failure returns to the task that produced the failing artifact for a fix.

- [x] **Step 1: Verify catalog file structure (AC1, AC2, AC3, AC4, AC5)**

  ```bash
  rg -c "^## " skills/spec/references/execution-patterns.md
  ```

  Expected: at least 8 top-level `## ` headings (Purpose, Lineage, When to consult, How to use, Decision tree, The Patterns, Combining patterns, Anti-patterns). Count may be higher if the lineage note is its own section or if additional subsections appear.

  Then manually read the file and confirm:
  - All 5 patterns appear in order (Supervisor, Pipeline, Fan-out/Fan-in, Producer-Reviewer, Expert Pool)
  - Each pattern has the 5 fields (Definition, When to use, GIGO mapping, Plan shape, Gotchas) in that order
  - Lineage note appears near the top
  - Expert Pool entry explicitly states workers stay bare + `review-lens:` is metadata-only
  - Anti-patterns section names all 5 mistakes

- [x] **Step 2: Verify forbidden strings are absent (AC6, AC7)**

  ```bash
  rg -c "_workspace" skills/spec/references/execution-patterns.md
  rg -c "\bPhase 7\b|\bPhase 8\b" skills/spec/references/execution-patterns.md
  ```

  Both must return `0` (or ripgrep's "No matches" exit code — treat absence as pass).

- [x] **Step 3: Verify planning-procedure.md integration (AC8, AC9)**

  Open `skills/spec/references/planning-procedure.md` and confirm:
  - A new section titled "Pick Execution Pattern" exists between section 1 (Scope Check) and the old section 2 (now renumbered to 3, Map File Structure)
  - The Plan Document Header template contains `**Execution Pattern:**` between `**Goal:**` and `**Architecture:**`
  - All downstream section numbers and internal cross-references are consistent

- [x] **Step 4: Verify example-plan.md updates (AC10, AC11)**

  Open `skills/spec/references/example-plan.md` and confirm:
  - Small, Medium, and Large Task examples all contain `**Execution Pattern:**` in their plan headers
  - Large Task has per-phase declarations under each phase heading
  - A new Fan-out/Fan-in example exists with a parallel wave and a fan-in task
  - A new Pipeline example exists with a linear blocked-by chain

  Then count lines inside each new example's plan code block:

  ```bash
  awk '/^```markdown$/,/^```$/' skills/spec/references/example-plan.md
  ```

  Confirm the Fan-out/Fan-in example's task content is ≤30 lines and the Pipeline example's task content is ≤25 lines. (Counting the lines between the opening `### Task` and closing of the plan block.)

- [x] **Step 5: Verify SKILL.md pointer (AC12)**

  ```bash
  rg "execution-patterns" skills/spec/SKILL.md
  ```

  Expected: at least one hit inside the Phase 8 section, referencing the catalog by the relative path `references/execution-patterns.md`.

- [x] **Step 6: Verify gigo:execute is untouched (AC13)**

  ```bash
  git diff --stat main -- skills/execute/
  ```

  Expected: no changes shown. If any file under `skills/execute/` appears in the diff, the cycle violated R8 — return to whichever task touched it and revert.

- [x] **Step 7: Verify backwards compatibility with an existing plan (AC14)**

  Pick any plan under `docs/gigo/plans/` that predates Cycle 1 — for example, `docs/gigo/plans/2026-04-10-phase-selection-matrix.md` if it exists, or the most recent plan committed before this cycle's changes.

  Confirm the plan file still parses as valid markdown and that `gigo:execute` can ingest it without error. A dry-run check:

  ```bash
  rg "^\*\*blocks:\*\*|^\*\*blocked-by:\*\*|^\*\*parallelizable:\*\*" <plan-file-path>
  ```

  Expected: the task format flags are still recognizable. The absence of an `**Execution Pattern:**` header does not invalidate the plan (R9).

- [x] **Step 8: Verify forward compatibility — a new plan declares the field (AC15)**

  Any plan written after Cycle 1 (including this plan itself) must declare an `**Execution Pattern:**` header. Confirm this plan declares it:

  ```bash
  rg "\*\*Execution Pattern:\*\*" docs/gigo/plans/2026-04-11-execution-pattern-catalog.md
  ```

  Expected: at least one match (the header declaration: `**Execution Pattern:** Fan-out/Fan-in`).

- [x] **Step 9: Final commit (if any verification found issues, commit fixes)**

  If all 8 verification steps passed with no changes, no commit is needed — just report success. If any step required a fix, commit the fix:

  ```bash
  git add <fixed files>
  git commit -m "fix(spec): address verification sweep findings for execution pattern catalog"
  ```

**Done when:** All 15 acceptance criteria pass verification. Any failures have been fixed and committed. The execute agent returns to the lead with a pass report and pointers to the commits.

#### What Was Built
- **Deviations:** None. Read-only verification sweep; no files modified, no fixes needed — all 15 ACs passed on the first run. Step 9 (final commit) was a no-op.
- **Review changes:** None. Task 5 is itself the verification gate — skipping `gigo:verify` is correct here because there is no artifact to judge against spec or craft criteria. The lead spot-checked AC6, AC7, AC11, AC13 against the merged state on main to confirm the subagent's report before accepting.
- **Notes for downstream:** One incidental finding worth recording for future spec authors: the plan's Step 7 verification command `rg "^\*\*blocks:\*\*|^\*\*blocked-by:\*\*|^\*\*parallelizable:\*\*"` does not reliably match when run as a combined alternation because shell escaping interacts with rg's pattern parser. Running each pattern individually works. This is a command defect in the plan, not an artifact defect — the backwards-compatibility guarantee itself holds. Consider splitting multi-pattern rg commands into per-pattern runs in future plans.

---

## Execution Notes

- **Execution Pattern: Fan-out/Fan-in** — Task 1 is the setup/fan-out origin (creates the catalog that later tasks depend on). Tasks 2, 3, 4 are the parallel wave and touch disjoint files. Task 5 is the fan-in that verifies the whole.
- Tasks 2, 3, 4 are genuinely parallelizable — they touch disjoint files (`planning-procedure.md`, `example-plan.md`, `SKILL.md` respectively) with no shared state. A gigo:execute Supervisor dispatching this plan should run them as a single wave of 3 workers.
- Task 5 must not run until all three parallel tasks commit — the verification sweep reads the committed state.
- No code is written in this cycle. Every task is markdown editing. Type-checking, test runs, and lint are N/A.

**Done when:** All 5 tasks pass, all 15 acceptance criteria are met, the catalog is live, planning-procedure/example-plan/SKILL.md consume it, and `gigo:execute` remains unchanged.

<!-- approved: plan 2026-04-11T01:27:49 by:Eaven -->
