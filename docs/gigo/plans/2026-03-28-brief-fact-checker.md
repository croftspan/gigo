# Brief Fact-Checker — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-28-brief-fact-checker-design.md`

**Goal:** Add Phase 4.25 to the blueprint pipeline — a fact-checker subagent that validates design brief assumptions against the actual project before operator approval.

**Architecture:** Hub-and-spoke. ~20-line section in SKILL.md dispatches a `Plan`-type subagent using a prompt template from `references/fact-checker-prompt.md`. The subagent explores the project read-only and returns findings.

---

### Task 1: Create the Fact-Checker Prompt Template

**blocks:** 2
**blocked-by:** []
**parallelizable:** true

**Files:**
- Create: `skills/blueprint/references/fact-checker-prompt.md`

- [ ] **Step 1: Write the prompt template**

Create `skills/blueprint/references/fact-checker-prompt.md` with this content:

```markdown
# Brief Fact-Checker Prompt Template

Dispatched by `gigo:blueprint` at Phase 4.25 — after the design brief is written, before the operator approves it.

## Template

You are a fact-checker. Your job is to verify whether a design brief's assumptions
match the actual project. You are NOT an adversarial reviewer — you don't challenge
design decisions, suggest alternatives, or judge quality. You check facts.

## The Design Brief

{DESIGN_BRIEF}

## Your Job

Explore the project at `{PROJECT_ROOT}`. Scan its structure, read key files,
understand what exists. Then check the design brief against reality in four
categories:

### 1. Redundancy
Does the project already contain something that does what the brief proposes?
Look for existing work that overlaps with what's being designed.

### 2. Wrong Assumptions
Does the brief assume patterns, tools, structures, or conventions that don't
match the project? Check what the project actually uses versus what the brief
says it uses.

### 3. Missing Dependencies
Does the brief reference things that don't exist in the project? Check that
named files, modules, systems, components, or concepts the brief depends on
are actually present.

### 4. Internal Consistency
Does the brief contradict itself? Check whether claims in one section conflict
with claims in another.

## Output

Return your findings in this exact format:

### If issues found:

## Fact-Check Results

- **[Category]:** [1-2 sentence description citing specific evidence from the
  project. Explain why this matters — what would go wrong if the brief proceeds
  with this assumption.]

### If no issues:

## Fact-Check Results

No issues found.

Categories are exactly one of: Redundancy, Wrong Assumption, Missing Dependency,
Inconsistency.

## Rules

DO:
- Explore the project thoroughly before reporting
- Cite specific locations (file paths, section names, directory structures) as evidence
- Include enough context that someone unfamiliar with the project understands the finding
- Report only genuine factual mismatches backed by evidence

DO NOT:
- Suggest alternative designs or approaches
- Challenge whether the design decision is right — that's judgment, not fact-checking
- Review quality, engineering decisions, or style
- Act as a second planner or adversarial reviewer
- Report stylistic preferences as findings
- Manufacture findings — "No issues found." is a valid and valuable result
```

- [ ] **Step 2: Verify the template**

Read the created file. Confirm:
- `{DESIGN_BRIEF}` and `{PROJECT_ROOT}` template variables are present
- Output format uses `## Fact-Check Results` header
- Category labels match spec: `Redundancy`, `Wrong Assumption`, `Missing Dependency`, `Inconsistency`
- Language is domain-agnostic (no "codebase", "code", "functions", "classes" — uses "project", "existing work", "project contents")
- DO NOT list includes all constraints from spec

- [ ] **Step 3: Commit**

```bash
git add skills/blueprint/references/fact-checker-prompt.md
git commit -m "feat(blueprint): add fact-checker prompt template for Phase 4.25"
```

---

### Task 2: Add Phase 4.25 to SKILL.md

**blocks:** []
**blocked-by:** 1
**parallelizable:** false

**Files:**
- Modify: `skills/blueprint/SKILL.md:88-90` (insert between Phase 4 and Phase 4.5)
- Modify: `skills/blueprint/SKILL.md:12` (phase announcement line)
- Modify: `skills/blueprint/SKILL.md:251-254` (small-task scaling section)

- [ ] **Step 1: Insert Phase 4.25 section**

After line 88 (the `**Write to plan file:**` line ending Phase 4) and before line 90 (`### Phase 4.5: Approve Design Brief`), insert:

```markdown

### Phase 4.25: Fact-Check Design Brief

Before the operator sees the brief, verify its assumptions against the actual project. This catches redundancy, wrong assumptions, missing dependencies, and internal inconsistencies — high value when the operator doesn't know the project well.

**How to run:** Read `references/fact-checker-prompt.md`. Fill `{DESIGN_BRIEF}` with the plan file contents and `{PROJECT_ROOT}` with the project's working directory. Dispatch using the Agent tool:

```
Agent tool:
  subagent_type: "Plan"
  prompt: [filled template with {DESIGN_BRIEF} and {PROJECT_ROOT} replaced]
```

Required: `subagent_type: "Plan"` — this runs in plan mode where only Explore/Plan types are available. Plan inherits the parent model for reasoning capacity.

**Write to plan file:** Add the subagent's results under a `## Fact-Check Results` section at the end of the current brief content.

**If findings exist:** Present them to the operator alongside the brief. The operator decides: revise the design (loop back to Phase 4) or proceed to approval (Phase 4.5).

**If no issues:** Note "Fact-check passed — no issues found" and proceed to Phase 4.5.

**Announce:** "Phase 4.25: Fact-checking design brief..."
```

- [ ] **Step 2: Update the phase announcement line**

In the header paragraph (line 12), update the announcement examples to include Phase 4.25:

Change:
```
"Phase 1: Exploring project context...", "Phase 2: Clarifying questions...", "Phase 3: Proposing approaches...", "Phase 5: Writing spec...", "Phase 8: Writing plan..."
```

To:
```
"Phase 1: Exploring project context...", "Phase 2: Clarifying questions...", "Phase 3: Proposing approaches...", "Phase 4.25: Fact-checking design brief...", "Phase 5: Writing spec...", "Phase 8: Writing plan..."
```

- [ ] **Step 3: Update the small-task scaling section**

In the "Scale to the Task" section, update the small task bullet to note that Phase 4.25 always runs:

Change:
```
- **Small task** (bug fix, config change): plan mode still activates but the design brief is short (5-10 lines: bug, cause, fix approach). Skip to Phase 8 after approval. Challenger may be skipped if operator requests it.
```

To:
```
- **Small task** (bug fix, config change): plan mode still activates but the design brief is short (5-10 lines: bug, cause, fix approach). Phase 4.25 (fact-check) always runs — fast on short briefs, catches the assumptions small tasks leave unexamined. Skip to Phase 8 after approval. Challenger may be skipped if operator requests it.
```

- [ ] **Step 4: Verify the changes**

Read the modified SKILL.md. Confirm:
- Phase 4.25 section exists between Phase 4 and Phase 4.5
- `subagent_type: "Plan"` is specified (not `general-purpose`)
- Phase announcement examples include 4.25
- Small-task scaling notes the exception
- Total line count is still under 500

- [ ] **Step 5: Commit**

```bash
git add skills/blueprint/SKILL.md
git commit -m "feat(blueprint): add Phase 4.25 fact-checker to pipeline"
```

---

## Risks

- **Plan-mode subagent behavior:** The `Plan` subagent type is documented as available in plan mode, but if the runtime rejects it, fall back to `Explore` type (which uses Haiku — less reasoning capacity but still functional for fact-checking).
- **Prompt template effectiveness:** The template hasn't been tested against a real project yet. First real use will validate whether the four categories and the "don't be adversarial" constraint produce useful output.

## Done When

1. `skills/blueprint/references/fact-checker-prompt.md` exists with the prompt template
2. `skills/blueprint/SKILL.md` has Phase 4.25 between Phase 4 and Phase 4.5
3. SKILL.md phase announcement includes 4.25
4. SKILL.md small-task scaling notes the Phase 4.25 exception
5. SKILL.md is under 500 lines
6. Both files are committed

<!-- approved: plan 2026-03-29T04:55:00 by:Eaven -->
