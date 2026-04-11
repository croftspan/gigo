# Planning Procedure

The detailed step-by-step for writing implementation plans. The hub (`SKILL.md`) covers the full arc from idea to plan. This reference covers the mechanics of plan construction — file structure, task format, dependency graphs, and quality checks.

---

## 0. Design Brief → Spec → Implementation Plan

Three documents form the planning chain:

1. **Design brief** (`.claude/plans/<name>.md`) — the approved thinking from plan mode. Contains exploration findings, operator answers, approach rationale, and design decisions. Created in Phases 0-4, approved at Phase 4.5.
2. **Spec** (`docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`) — the formal source of truth for bare workers. Formalizes the design brief into requirements. Created in Phase 5.
3. **Implementation plan** (`docs/gigo/plans/YYYY-MM-DD-<feature>.md`) — ordered, executable tasks that implement the spec. Created in Phase 8.

Each document feeds the next. The spec references the design brief for rationale. The implementation plan references both the design brief (why) and the spec (what).

**Include in the spec header:**
```markdown
**Design brief:** `.claude/plans/<name>.md`
```

This links the formal document back to the approved thinking.

---

## 1. Scope Check

Before writing tasks, confirm the spec is appropriately scoped:
- If it covers multiple independent subsystems, it should have been decomposed during design
- If it wasn't, suggest breaking into separate plans — one per subsystem
- Each plan should produce working, testable software on its own

## 2. Pick Execution Pattern

Before mapping file structure, read `references/execution-patterns.md` and pick the pattern that matches the work's shape. Declare the chosen pattern in the plan header as `**Execution Pattern:** <name>`. For multi-phase plans, declare a pattern per phase under each phase heading. **Supervisor is the default** when nothing else fits — but don't name a pattern just to name something.

## 3. Map File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- Prefer smaller, focused files over large ones that do too much. Claude reasons better about code it can hold in context, and edits are more reliable when files are focused.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure — but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs task decomposition. Each task should produce self-contained changes that make sense independently.

## 4. Plan Document Header

Every plan starts with this header:

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`

**Goal:** [One sentence describing what this builds]

**Execution Pattern:** [Pattern name — see references/execution-patterns.md]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## 5. Task Format

Each task follows this structure:

````markdown
### Task N: [Component Name]

**blocks:** [task numbers this unblocks, e.g., 4, 5]
**blocked-by:** [task numbers that must complete first, e.g., 1, 2]
**parallelizable:** true/false

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: [Concrete action]**

```python
# Actual code — not pseudocode, not "implement X"
def function(input):
    return expected
```

- [ ] **Step 2: [Verify]**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## 6. Dependency Graph Rules

Every task declares its dependencies:

- **blocks:** Which tasks this one unblocks. Empty if nothing depends on it.
- **blocked-by:** Which tasks must complete before this one starts. Empty if none.
- **parallelizable:** Can this run alongside other unblocked tasks? `true` if it touches different files and has no shared state.

The dependency graph determines execution order. `gigo:execute` uses it to dispatch tasks — potentially in parallel when tasks are independent.

## 7. Bite-Sized Task Granularity

Each step is one action (2-5 minutes of work):

- "Write the test" — step
- "Run it to verify it fails" — step
- "Implement the minimal code" — step
- "Run tests and verify they pass" — step
- "Commit" — step

If a step takes longer than 5 minutes, it's too big. Break it down.

## 8. No Placeholders

Every step must contain the actual content a worker needs. These are plan failures — never write them:

- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the content — the worker may read tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## 9. Plan Self-Review

After writing the complete plan, review it against the spec:

**9a. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? If a requirement has no task, add the task.

**9b. Placeholder scan:** Search the plan for any of the patterns from section 8 above. Fix them.

**9c. Type consistency:** Do the types, method signatures, and property names used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

Fix issues inline. No need to re-review — just fix and move on.

## 10. Execution Handoff

After saving the plan and getting user approval:

> "Plan ready. Want me to start execution?"

If yes, invoke `gigo:execute`.

## 11. Specs and Plans File Locations

- Specs save to: `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`
- Plans save to: `docs/gigo/plans/YYYY-MM-DD-<feature-name>.md`

User preferences for location override these defaults.

## Scale Reference

From the hub — every plan answers these regardless of size:

| Scale | Format | Phases used |
|---|---|---|
| Small (bug fix, config) | 3-5 ordered bullets | 1, 2 lightly, then 8 |
| Medium (feature, refactor) | Numbered tasks with dependencies | Full arc, brief design |
| Large (architecture, new system) | Phased tasks with milestones and decision points | Full arc with decomposition |

Every plan answers: **What** (specific things that need to happen), **Order** (dependencies and sequencing), **Risks** (what could go wrong), **Done** (how to know it's finished).
