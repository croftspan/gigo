# Phase 4.25: Brief Fact-Checker — Design Brief

## Context

The blueprint pipeline has a gap between design presentation (Phase 4) and design approval (Phase 4.5). The planner writes a design brief based on codebase exploration and operator input — but if the planner missed something obvious (existing code that does what's proposed, wrong assumptions about project patterns, nonexistent dependencies), the operator won't catch it either, especially if they're unfamiliar with the repo.

The Challenger (Phase 6.5/9.5) catches engineering and intent problems in formal specs/plans — but by then the design is already locked in. A lightweight fact-check before approval prevents wasted spec-writing effort.

**Prior art:** Memory `project_brief_reviewer.md` established this concept. Priority 1 for this session per `project_next_session_priorities.md`.

## Phase 1 Findings

### Current SKILL.md State
- **267 lines** — well under 500-line cap. ~30-line addition is safe.
- Phase 4 ends at line 88 (plan file write directive)
- Phase 4.5 starts at line 90
- Insertion point: line 89

### Existing Dispatch Patterns
- Challenger (Phase 6.5): Agent tool → `subagent_type: "general-purpose"` → reads prompt template from `skills/verify/references/spec-plan-reviewer-prompt.md` → fills template variables → passes as agent prompt
- Challenger is adversarial, two-pass (blind technical → intent alignment)
- Fact-checker is different: not adversarial, just codebase-aware sanity check

### Domain-Agnostic Requirement
- Per memory `feedback_domain_agnostic_reviews.md`: ALL review templates must work across domains (code, novels, games, research)
- No "file:line references" → "specific location references"
- No "does this compile?" → "is this internally consistent?"
- The fact-checker checks whether brief assumptions match actual project state, regardless of domain

### What Exists
- Blueprint references dir: `planning-procedure.md`, `example-plan.md`
- No fact-checker prompt template exists yet
- Verify skill has `spec-plan-reviewer-prompt.md` (Challenger) — different purpose, don't reuse

---

## Phase 3: Approaches

### Approach A: Inline section in SKILL.md + prompt template in references/ (Recommended)

Add ~20-25 lines to SKILL.md between Phase 4 and Phase 4.5. Create a new prompt template at `skills/blueprint/references/fact-checker-prompt.md` that the blueprint reads, fills, and dispatches via Agent tool.

**Pros:** Follows the hub-and-spoke pattern. Prompt template is reusable and testable. Keeps SKILL.md lean.
**Cons:** One more reference file.

### Approach B: Inline everything in SKILL.md

Put the fact-checker dispatch instructions and prompt directly in SKILL.md. No reference file.

**Pros:** One file to maintain.
**Cons:** Adds ~50-60 lines to SKILL.md. The prompt template is harder to test independently. Violates the hub-and-spoke pattern.

### Approach C: Add to verify skill as a shared resource

Put the fact-checker prompt in verify's references alongside the Challenger.

**Pros:** Centralizes review prompts.
**Cons:** Blueprint would depend on verify's file structure. The fact-checker is conceptually different from the Challenger. Couples two skills unnecessarily.

**Recommendation: Approach A.** Hub-and-spoke is the established pattern. The prompt template belongs in blueprint's references because it's blueprint's phase, not verify's.

---

## Phase 4: Design

### What Phase 4.25 Does

After the design brief is written to the plan file (Phase 4) and before the operator approves it (Phase 4.5), dispatch a subagent that:

1. Reads the design brief from the plan file
2. Explores the actual project (codebase, docs, config, whatever exists)
3. Checks for factual mismatches:
   - **Redundancy:** Does something proposed already exist in the project?
   - **Wrong assumptions:** Does the brief assume patterns, tools, or structures that don't match the project?
   - **Missing dependencies:** Does the brief reference things (libraries, modules, files, systems) that don't exist?
   - **Internal consistency:** Does the brief contradict itself?
4. Returns a short list of findings or "No issues found."

### What It Does NOT Do

- Challenge whether the approach is right (that's judgment — the Challenger's job later)
- Suggest alternative designs
- Review code quality or engineering decisions
- Act as a second planner

### Domain-Agnostic Language

The prompt template uses neutral terms:
- "project" not "codebase" (works for novels, games, etc.)
- "existing work" not "existing code"
- "project state" not "file structure"
- "proposed elements" not "proposed functions/classes"
- The agent explores whatever the project contains — code, docs, manuscripts, game rules, data files

### Dispatch Pattern

```
Agent tool:
  subagent_type: "general-purpose"
  prompt: [filled fact-checker-prompt.md template]
```

Template variables:
- `{DESIGN_BRIEF}` — the full text of the design brief from the plan file
- `{PROJECT_ROOT}` — the project directory to explore

The subagent gets read-only exploration tools (Glob, Grep, Read, LS). It returns findings as a structured list.

### Output Format

```markdown
## Fact-Check Results

### Findings
- **[Redundancy/Wrong Assumption/Missing Dependency/Inconsistency]:** [1-2 sentence description with specific evidence]

### No Issues
- "No issues found." (if clean)
```

Findings are written to the plan file under a `## Fact-Check Results` section, visible to the operator when they review the brief in Phase 4.5.

### Integration Into SKILL.md

Add a new `### Phase 4.25: Fact-Check Design Brief` section (~20 lines) that:
1. Explains the purpose (one sentence)
2. Says to read the prompt template from `references/fact-checker-prompt.md`
3. Says to fill `{DESIGN_BRIEF}` from the plan file and `{PROJECT_ROOT}` from the working directory
4. Says to dispatch via Agent tool with `subagent_type: "general-purpose"`
5. Says to write findings to the plan file
6. Says: if findings exist, present them to the operator before Phase 4.5; operator decides whether to revise or proceed

### The Prompt Template (`references/fact-checker-prompt.md`)

The template instructs the subagent to:
1. Read the design brief provided
2. Explore the project at `{PROJECT_ROOT}` — scan structure, read key files, understand what exists
3. Check four categories: redundancy, wrong assumptions, missing dependencies, internal consistency
4. For each finding: state the category, describe the mismatch, cite specific evidence from the project
5. If no issues: say "No issues found."
6. Do NOT suggest alternatives, challenge design decisions, or act as an adversarial reviewer
7. Keep findings to genuine factual mismatches, not stylistic preferences

### Scale Behavior

Always runs regardless of task size. No skip logic, no opt-out. Operator confirmed.

- **Small tasks:** Returns "No issues found" quickly. One subagent, fast scan.
- **Large tasks:** Higher value — more assumptions to check, more existing work that might overlap.
- **Non-code projects:** Works the same — checks whether a novel's brief assumes a character that doesn't exist yet, whether a game brief references mechanics that aren't implemented, etc.

### Files to Create/Modify

1. **Modify:** `skills/blueprint/SKILL.md` — insert Phase 4.25 section (~20 lines at line 89)
2. **Create:** `skills/blueprint/references/fact-checker-prompt.md` — the prompt template (~40-50 lines)

---

## Post-Approval: What Happens Next

This is a DESIGN BRIEF, not an implementation plan. After approval:
1. Write formal spec to docs/gigo/specs/ (Phase 5)
2. Self-review spec (Phase 6)
3. Challenger adversarial review of spec (Phase 6.5)
4. Operator reviews spec (Phase 7)
5. Write implementation plan to docs/gigo/plans/ (Phase 8)
6. Self-review plan (Phase 9)
7. Challenger adversarial review of plan (Phase 9.5)
8. Operator reviews plan (Phase 10)
9. Offer execution via gigo:execute (Phase 11)

DO NOT start writing code after this plan is approved.
The next step is formalizing this brief into a spec document.

<!-- approved: design-brief 2026-03-28T22:00:00 by:Eaven -->
