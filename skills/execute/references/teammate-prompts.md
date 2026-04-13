# Worker Prompt Templates

## Implementation Prompt

### Tier 1: Subagent Worker (Primary)

Include the full task text in the Agent tool prompt. Dispatch with `isolation: "worktree"` so each worker gets its own repo copy:

```
You are implementing a task on an isolated git worktree branch.

## Task Description
[FULL TEXT of task from plan — paste it here, don't make subagent read file]

## Context
[Where this fits, dependencies, what was built in prior tasks]

If prior tasks have "What Was Built" addendums in the plan, the lead has
included relevant context above. Use it — it may record interface changes
or deviations that affect your task.

## Output Language
[Output language(s) from .claude/references/language.md. If the project
has non-English output languages, state them here: "Output language(s):
es, sl. Produce all user-facing deliverables in the specified language(s).
Code, commit messages, and internal comments remain in English."
If language.md doesn't exist or output is English-only, omit this section.]

## Worktree Isolation
You are on your own branch in a git worktree. Commit freely — the lead
handles merging your branch back to main after review passes. You don't
need to worry about conflicts with other workers.

## Before You Begin
If anything is unclear about requirements, approach, or dependencies — ask now.

## Your Job
1. Implement exactly what the task specifies
2. Write tests as the task describes
3. Verify implementation works
4. Commit your work to this branch
5. Self-review: completeness, quality, no overbuilding
6. Report back

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT

If you're in over your head, say so. Bad work is worse than no work.
```

### Tier 2: Inline

No prompt template needed — the lead executes tasks directly in the current session.

---

## Fix Prompt

### Tier 1: Subagent Re-dispatch

Dispatch a new subagent with the fix prompt and review feedback:

```
You are fixing issues found in a task.

## Review Feedback
[SPECIFIC issues from gigo:verify — what's wrong, where, why it matters]

## Original Task
[FULL TEXT of task from plan]

## Your Job
Fix the issues listed above. Don't change anything else.
Run tests. Commit. Report back.

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

### Tier 1: Operator-Resolved Re-dispatch

When ask-operator items have been decided by the operator:

```
You are implementing a decision made by the project operator.

## Operator Decision
[What the operator decided on the architectural/scope question]

## Additional Fixes
[AUTO-FIX items, if any remain]

## Original Task
[FULL TEXT of task from plan]

## Your Job
Implement the operator's decision. Fix any additional items listed above.
Don't change anything else. Run tests. Commit. Report back.

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

---

## Applier Prompt

### Local Model Routing: Haiku Applier

When a task is routed through a local model (see `references/local-model-routing.md`), the local model generates code and a haiku subagent applies it. Dispatch with `isolation: "worktree"`:

```
You are applying pre-generated code to files. Write each file exactly as provided.
Do not modify, improve, or add to the code. Apply it verbatim.

## Files to Write

### {path/to/file1}
{code content — pasted verbatim from parsed response}

### {path/to/file2}
{code content}

[repeat for all parsed code blocks]

## After Writing
1. Create any directories that don't exist.
2. Write each file to its exact target path.
3. If a file already exists, replace its contents entirely.
[IF test_command exists:]
4. Run: {test_command}
5. If tests fail, report the test output — do NOT attempt to fix the code.
[END IF]
6. Commit all changes to this branch.
7. Report back with the list of files written.

Status: DONE | BLOCKED (with reason — include full test output if tests failed)
```

### Local Model Routing: Gemma Fix Prompt

When a Gemma-generated task fails (test failure or review issues), re-prompt Gemma with this template. Uses the same system prompt (harness) as the original attempt:

```
The previous code had issues.

## Original Task
{original task description from plan}

## Issue
{test failure output OR review feedback — pasted verbatim}

## Previous Code
{the code blocks from the failed attempt}

## Current Files
{same inline source files as original prompt}

Fix the issues. Output corrected code blocks only.
```

---

## Prompt Design Rationale

**Why lean prompts:** Phase 7 eval data proved that bare workers (no personas, no rules, just the task spec) perform at senior/staff level. The spec quality — not the worker context — determines output quality. Loading workers with assembled context doesn't improve their work and can degrade it.

**Why full task text:** Workers should never need to read the plan file themselves. The lead extracts and provides the full task description. This eliminates file-reading overhead and ensures the worker gets exactly the context they need.

**Why self-review before reporting:** Workers catch their own mistakes before the formal review runs. This reduces review-fix cycles and saves time.
