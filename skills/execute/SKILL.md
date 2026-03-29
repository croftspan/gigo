---
name: execute
description: "Execute implementation plans. Lead dispatches bare worker subagents per task, invokes gigo:verify after each, tracks progress via checkpoints. Falls back to inline if subagents unavailable. Agent teams available as experimental opt-in. Use when you have an approved plan from gigo:blueprint."
---

# Execute

Good spec + bare workers + per-task review = quality output. The lead coordinates, subagents implement, review gates enforce quality on every task.

You run approved plans. You don't plan, you don't design, you don't question the spec. You execute it — dispatching workers, tracking progress, enforcing review on every task, and reporting results.

**Announce every phase.** As you work, tell the operator what's happening: "Reading plan...", "Dispatching Task 1 and Task 2 in parallel...", "Task 1 complete, running review...", "All tasks complete, synthesizing results." Don't work silently.

---

## Before Starting

1. **Verify the plan exists and is approved.** If there's no approved plan, stop and tell the operator to run `gigo:blueprint` first.
2. **Read the full plan.** Extract all tasks, their descriptions (full text), dependencies, and parallelization markers.
   - **Check for checkpoints.** Scan for `<!-- checkpoint: ... -->` comments in the plan.
   - **If checkpoints found:** Report progress to the operator, verify SHAs exist, and resume from the appropriate point. See `references/checkpoint-format.md` for the full resume procedure.
   - **If no checkpoints:** Fresh execution — proceed normally.
3. **Present execution options.** Let the operator choose their tier:

   > "Ready to execute. Available options:
   > 1. **Subagents** (recommended) — fresh worker per task, parallel dispatch for independent tasks, lead-managed review.
   > 2. **Inline** — sequential in this session, no isolation. Good for small plans or debugging.
   > 3. **Agent teams** (experimental opt-in) — full parallelization via shared task list, hook-enforced review. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.
   >
   > Which route?"

   Default recommendation: subagents. But always ask — the operator may prefer inline for debugging or agent teams for experimentation.

---

## Tier 1: Subagents (Primary)

Fresh subagent per task via Agent tool. Lead controls dispatch, review, and triage.

### Execution Flow

For each **wave** of unblocked tasks:

1. **Identify the wave.** Read the dependency graph. All tasks whose `blocked-by` dependencies are satisfied form the current wave.
2. **Dispatch in parallel.** For tasks marked `parallelizable: true` with no shared file conflicts, dispatch multiple subagents in a single message (multiple Agent tool calls). Each subagent gets:
   - Full task text from the plan (don't make subagents read the plan file)
   - Context from completed dependencies ("What Was Built" addendums)
   - Model selected per task complexity — see `references/model-selection.md`
   - The implementation prompt from `references/teammate-prompts.md` (Tier 1 variant)
3. **Wait for completion.** Process results as subagents finish.
4. **Review each completed task.** Invoke `gigo:verify` (Stage 1: spec compliance, Stage 2: engineering quality).
5. **Triage findings.** For each reviewed task:
   - **Auto-fix:** Dispatch a fix subagent with the review feedback (see fix prompt in `references/teammate-prompts.md`). Re-review after fix.
   - **Ask-operator:** Surface to operator. Task stays blocked. Move to next independent task.
   - **Accept/pass:** Write addendum, checkpoint, commit.
6. **Update the wave.** Completed tasks unblock dependent tasks. Repeat from step 1 with the new wave.

### Parallel Dispatch Rules

- Only dispatch tasks in parallel if they're marked `parallelizable: true` in the plan
- Never dispatch tasks that modify the same files in parallel
- If unsure about file conflicts, dispatch sequentially — wasted time beats merge conflicts
- The lead can dispatch up to 3-4 subagents per wave (more creates diminishing returns from context switching)

### Status Handling

Workers report one of four statuses:

**DONE** — Proceed to review via `gigo:verify`. Handle triage categories: auto-fix items go back to a fix subagent, ask-operator items block the task, accept items go into the addendum.

**DONE_WITH_CONCERNS** — Worker completed the task but flagged doubts. Read the concerns before proceeding to review. If concerns are about correctness or scope, address them first.

**NEEDS_CONTEXT** — Worker needs information that wasn't provided. Provide context and re-dispatch a new subagent.

**BLOCKED** — Worker cannot complete the task. Assess the blocker:
1. Context problem — provide more context, re-dispatch
2. Task too hard — re-dispatch with a more capable model
3. Task too large — break it into smaller pieces
4. Plan is wrong — escalate to the operator

Never silently skip a blocker. The operator decides.

---

## Tier 2: Inline (Fallback)

If subagents are unavailable or the operator prefers it (debugging, simple plans).

- Execute tasks sequentially in the current session
- No context isolation between tasks
- Lead invokes `gigo:verify` after each task
- Lead writes checkpoints after each task. On context limit, the next session resumes from checkpoints.

> "Running inline — no parallelization, no context isolation. Good for small plans or debugging."

---

## Tier 3: Agent Teams (Experimental Opt-In)

Available when the operator specifically wants it and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is enabled. Not recommended as default due to: auto-claim race conditions, forced CLAUDE.md loading on teammates, significantly higher token cost, no session resume, and unproven hook integration.

**If the operator chooses agent teams:**

1. **Set up review hook.** The hook must exist BEFORE tasks are dispatched — see `references/review-hook.md`.
2. **Create tasks in shared task list.** Use `TaskCreate` with full task text in description.
3. **Pre-assign tasks** to specific workers using `TaskUpdate` with `owner`. Do NOT rely on auto-claim — it defeats parallelism (one fast worker grabs everything).
4. **Set dependencies.** Use `addBlocks`/`addBlockedBy` to match the plan's dependency graph.
5. **Spawn teammates** with the agent team prompt from `references/teammate-prompts.md` (Tier 3 variant). Select model per task complexity. Team sizing: ~5-6 tasks per teammate.
6. **TaskCompleted hook** invokes `gigo:verify` before any task can be marked done.

See `references/review-hook.md` for hook configuration and the full agent teams flow.

**Known issues:**
- Auto-claim lets one fast worker grab all tasks (mitigated by pre-assignment)
- CLAUDE.md auto-loads on all teammates (can't make them truly bare)
- No session resume — teammates die on crash, task list has stale state
- Significantly more tokens than subagents
- Hook integration with gigo:verify is unproven

---

## After Review Passes

After a task passes both review stages, update the plan document before moving to the next task:

1. **Mark steps complete.** Update checkboxes: `- [ ]` → `- [x]`.
2. **Write the "What Was Built" addendum** under the task:

```markdown
#### What Was Built
- **Deviations:** None | [brief description of what changed from plan and why]
- **Review changes:** None | [what the review cycle changed]
- **Notes for downstream:** None | [interface changes, renamed exports, constraint additions — anything the next worker needs to know]
```

3. **Include "accept" observations** from review triage in the "Notes for downstream" field.
4. **Check downstream impact.** If the implementation deviated in ways that affect dependent tasks, check whether those task descriptions need updating before dispatching them.
5. **Write checkpoint** (see `references/checkpoint-format.md`).
6. **Commit the plan update.**

**Rules:**
- Always write an addendum, even when nothing deviated. "No deviations" confirms the plan was accurate.
- Keep it brief — 1-3 bullets per field. This is a breadcrumb trail, not a post-mortem.
- Focus on what downstream workers need. A renamed export belongs here. A refactored internal helper doesn't.

---

## When All Tasks Complete

1. Synthesize results — read the "What Was Built" addendums across all tasks for a complete picture of deviations, review changes, and observations
2. Report to operator with a summary: what was built, what deviated from plan, what the review cycle caught, and any "accept" observations worth noting
3. Suggest: "Ready for a PR? I can invoke `gigo:verify` in PR mode for the final gate."

---

## Red Flags

**Never:**
- Start implementation without an approved plan
- Skip review on any task
- Proceed with unfixed review issues
- Ignore worker escalations (BLOCKED, NEEDS_CONTEXT)
- Silently skip a task
- Make workers read the plan file — provide full task text in the dispatch prompt

**If a worker reports concerns:** Read them before proceeding. Don't rush into review.

**If review finds issues:** The worker fixes them, review runs again. Repeat until approved. Don't skip the re-review.

---

## References

- `references/teammate-prompts.md` — Implementation and fix prompt templates (all tiers)
- `references/model-selection.md` — When to use which model tier
- `references/review-hook.md` — TaskCompleted hook configuration (agent teams only)
- `references/checkpoint-format.md` — Checkpoint syntax, resume procedure, edge cases
