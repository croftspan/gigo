---
name: execute
description: "Execute implementation plans using Claude Code agent teams. Lead creates tasks with dependencies, spawns bare worker teammates, reviews each task via gigo:review before completion. Falls back to subagents if agent teams unavailable, inline if neither available. Use when you have an approved plan from gigo:plan."
---

# Execute

Good spec + bare workers + per-task review = quality output. The lead coordinates, teammates implement, infrastructure handles parallelization and review gates.

You run approved plans. You don't plan, you don't design, you don't question the spec. You execute it — dispatching workers, tracking progress, enforcing review on every task, and reporting results.

---

## Before Starting

1. **Verify the plan exists and is approved.** If there's no approved plan, stop and tell the operator to run `gigo:plan` first.
2. **Read the full plan.** Extract all tasks, their descriptions (full text), dependencies, and parallelization markers.
3. **Detect execution tier.** Try in order — use the best available.

---

## Three Execution Tiers

### Tier 1: Agent Teams (optimal)

Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` enabled. Full parallelization, hook-enforced review, inter-worker messaging.

**Setup:**

1. **Create tasks in shared task list.** For each task in the plan, use `TaskCreate` with:
   - `subject`: task name from plan
   - `description`: FULL TEXT of task from plan — don't make teammates read the plan file
2. **Set dependencies.** Use `TaskUpdate` with `addBlocks`/`addBlockedBy` to match the plan's dependency graph. Tasks with unresolved `blockedBy` dependencies can't be claimed — the infrastructure handles ordering.
3. **Spawn teammates.** Create bare worker teammates with the implementation prompt from `references/teammate-prompts.md`. Select model per task complexity — see `references/model-selection.md`. Team sizing: ~5-6 tasks per teammate.
4. **Configure review hook.** TaskCompleted hook invokes `gigo:review` before any task can be marked done — see `references/review-hook.md`.

**How it runs:**

- Teammates auto-claim unblocked tasks and implement them
- When a teammate marks a task complete, the TaskCompleted hook fires and runs `gigo:review`
- If review passes (hook exits 0), the task is marked complete
- If review finds issues (hook exits 2 with stderr feedback), the teammate receives the feedback and continues working on the task
- Teammates communicate directly via `SendMessage` if they discover something another worker needs
- When all tasks complete, the lead synthesizes results and reports to the operator

**The CLAUDE.md question:** Teammates auto-load project CLAUDE.md. Phase 7 data says bare workers perform best, but assembled workers still passed engineering review (3/3 approvals). Agent teams' coordination benefits — auto-parallelization, shared task list, inter-worker messaging, hook-enforced review — outweigh the theoretical context concern. Accept for v1. Test and optimize later with `gigo:eval`.

### Tier 2: Subagents (good)

If agent teams are not available. Fresh subagent per task via Agent tool.

**How it runs:**

- Lead dispatches one subagent per task using the implementation prompt from `references/teammate-prompts.md` (Tier 2 variant)
- Sequential execution, with manual parallelization of independent tasks where possible
- After each subagent completes, lead invokes `gigo:review` manually
- If review finds issues, dispatch a new subagent with the fix prompt + review feedback
- Repeat until review passes, then move to next task

**Surface this warning:**
> Agent teams not available. Running with subagents — no auto-parallelization, no inter-worker communication. Enable agent teams with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for better results.

### Tier 3: Inline (functional)

If neither agent teams nor subagents are available.

- Execute tasks sequentially in the current session
- No context isolation between tasks
- Lead invokes `gigo:review` after each task

**Surface this warning:**
> Neither agent teams nor subagents available. Running inline — no parallelization, no context isolation. Consider enabling subagent support.

---

## Status Handling

Workers report one of four statuses. Handle each appropriately:

**DONE** — Proceed to review (via TaskCompleted hook in Tier 1, manual invocation in Tier 2/3).

**DONE_WITH_CONCERNS** — Worker completed the task but flagged doubts. Read the concerns before proceeding. If concerns are about correctness or scope, address them before review. If they're observations (e.g., "this file is getting large"), note them and proceed to review.

**NEEDS_CONTEXT** — Worker needs information that wasn't provided.
- Tier 1: Teammate sends message to lead via `SendMessage`. Lead provides context, teammate continues.
- Tier 2: Lead provides context and re-dispatches subagent.

**BLOCKED** — Worker cannot complete the task. Assess the blocker:
1. If it's a context problem — provide more context and let the worker retry
2. If the task requires more reasoning — in Tier 1, the teammate can escalate; in Tier 2, re-dispatch with a more capable model
3. If the task is too large — break it into smaller pieces
4. If the plan itself is wrong — escalate to the operator

Never silently skip a blocker. Never force the same model to retry without changes. The operator decides.

---

## When All Tasks Complete

1. Synthesize results — what was built, what was reviewed, any concerns raised
2. Report to operator with a summary of completed work
3. Suggest: "Ready for a PR? I can invoke `gigo:review` in PR mode for the final gate."

---

## Red Flags

**Never:**
- Start implementation without an approved plan
- Skip review on any task (TaskCompleted hook enforces this in Tier 1)
- Proceed with unfixed review issues
- Ignore worker escalations (BLOCKED, NEEDS_CONTEXT)
- Silently skip a task
- Make workers read the plan file — provide full task text in the task description

**If a worker asks questions:** Answer clearly and completely. Provide additional context if needed. Don't rush them into implementation.

**If review finds issues:** The worker fixes them, review runs again. Repeat until approved. Don't skip the re-review.

---

## References

- `references/teammate-prompts.md` — Implementation and fix prompt templates
- `references/model-selection.md` — When to use which model tier
- `references/review-hook.md` — TaskCompleted hook configuration and flow
