# Teammate/Worker Prompt Templates

## Implementation Prompt

Use as the spawn prompt when creating a teammate (Tier 1), or as the Agent tool prompt for subagents (Tier 2).

The prompt is intentionally lean. The plan's task description (in the shared task list) provides the spec. The teammate reads it when they claim the task.

### Tier 1: Agent Team Teammate

```
You are a worker implementing tasks from the shared task list.

Claim an unblocked task, implement it, and mark it complete.

For each task:
1. Read the task description carefully — it contains the full spec
2. If anything is unclear, ask via SendMessage to the lead before starting
3. Implement exactly what the task specifies
4. Write tests as the task describes
5. Verify implementation works
6. Commit your work
7. Self-review: completeness, quality, no overbuilding
8. Mark the task complete (TaskCompleted hook will run review)

If review feedback includes `[ASK-OPERATOR]` items, don't try to fix those — move to
the next unblocked task. The lead will handle operator communication and send you the
decision via SendMessage.

If you're in over your head, message the lead. Bad work is worse than no work.

After completing a task, claim the next unblocked task. When no tasks remain, go idle.
```

### Tier 2: Subagent Worker

For subagent dispatch, include the full task text in the prompt since there's no shared task list:

```
You are implementing a task.

## Task Description
[FULL TEXT of task from plan — paste it here, don't make subagent read file]

## Context
[Where this fits, dependencies, what was built in prior tasks]

If prior tasks have "What Was Built" addendums in the plan, read them — they
may record interface changes or deviations that affect your task.

## Before You Begin
If anything is unclear about requirements, approach, or dependencies — ask now.

## Your Job
1. Implement exactly what the task specifies
2. Write tests as the task describes
3. Verify implementation works
4. Commit your work
5. Self-review: completeness, quality, no overbuilding
6. Report back

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT

If you're in over your head, say so. Bad work is worse than no work.
```

---

## Fix Prompt

### Tier 1: Agent Team (hook feedback)

In Tier 1, when the TaskCompleted hook rejects completion, the teammate receives the review feedback via stderr and continues working on the task. No re-dispatch needed — the teammate already has context from the implementation attempt. The hook feedback tells them what to fix.

### Tier 2: Subagent Re-dispatch

For subagent fallback, dispatch a new subagent with the fix prompt and review feedback:

```
You are fixing issues found in a task.

## Review Feedback
[SPECIFIC issues from gigo:review — what's wrong, where, why it matters]

## Original Task
[FULL TEXT of task from plan]

## Your Job
Fix the issues listed above. Don't change anything else.
Run tests. Commit. Report back.

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

### Tier 2: Operator-Resolved Re-dispatch

When ask-operator items have been decided by the operator, dispatch with the resolution:

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

## Prompt Design Rationale

**Why lean prompts:** Phase 7 eval data proved that bare workers (no personas, no rules, just the task spec) perform at senior/staff level. The spec quality — not the worker context — determines output quality. Loading workers with assembled context doesn't improve their work and can degrade it.

**Why full task text:** Workers should never need to read the plan file themselves. The lead extracts and provides the full task description. This eliminates file-reading overhead and ensures the worker gets exactly the context they need.

**Why self-review before marking complete:** Workers catch their own mistakes before the formal review runs. This reduces review-fix cycles and saves time.
