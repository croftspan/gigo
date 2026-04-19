---
name: execute
description: "Execute implementation plans. Lead dispatches bare worker subagents per task, invokes gigo:verify after each, tracks progress via checkpoints. Falls back to inline if subagents unavailable. Agent teams available as experimental opt-in. Use when you have an approved plan from gigo:blueprint."
---

# Execute

Good spec + bare workers + per-task review = quality output. The lead coordinates, subagents implement, review gates enforce quality on every task.

You run approved plans. You don't plan, you don't design, you don't question the spec. You execute it — dispatching workers, tracking progress, enforcing review on every task, and reporting results.

**Announce every phase.** As you work, tell the operator what's happening: "Reading plan...", "Dispatching Task 1 and Task 2 in parallel...", "Task 1 complete, running review...", "All tasks complete, synthesizing results." Don't work silently.

Read `.claude/references/language.md` if it exists. Conduct all operator-facing conversation — phase announcements, status reports, escalations — in the interface language. Worker prompts remain in English (see `references/teammate-prompts.md`). If the file doesn't exist, default to English.

Read `.claude/references/verbosity.md` if it exists. If `level: minimal`, announce wave dispatch and task completion only — skip per-step narration within tasks, skip file-conflict analysis details, skip retry reasoning. If `level: verbose` or the file doesn't exist, narrate fully. Default to minimal.

---

## Before Starting

1. **Verify the plan exists and is approved.** If there's no approved plan, stop and tell the operator to run `gigo:blueprint` first.
2. **Check plan verification (if Gate 2 ran).** Resolve the matching artifact, then compute effective status from its body.
   - **Resolve artifact:** scan `docs/gigo/research/*-plan-verification.md`. For each candidate, read frontmatter `plan:` field. Canonicalize BOTH the frontmatter value AND the plan being executed to absolute paths (resolve `~`, expand relative paths using `$CLAUDE_PROJECT_DIR` or current working directory, resolve symlinks via `realpath`). Compare canonicalized paths. If multiple candidates match after canonicalization, select the one with the most recent `run-at`. Do NOT match by filename convention — frontmatter `plan:` is authoritative.
   - **Malformed candidates:** if a candidate artifact is missing the frontmatter `plan:` field or the field is empty, tag it as `MALFORMED-ARTIFACT` and skip it for matching. If NO valid candidate remains after scanning all files, include MALFORMED-ARTIFACT entries in the refusal message (step 3 below "(artifact exists but body table missing/malformed)" path) — don't silently treat as "no matching artifact." The operator needs to see which candidate files are unusable and why.
   - **No matching artifact (all candidates either absent or MALFORMED-ARTIFACT with no valid match)** → treat as skipped gates ONLY if zero candidates existed at all (small task, pure design, gates explicitly off). If candidates existed but were all MALFORMED-ARTIFACT, REFUSE and list them. Proceed to step 3 only in the clean "no candidates" case.
   - **Artifact found → compute effective status from body** (per `skills/spec/references/research-gate-2.md` → Derived Status Calculation):
     - Find the LATEST `## Run N` section (scan for `## Run ` headers, pick highest N or latest timestamp).
     - Count ❌ rows in `### Findings` → `N_fail`.
     - Count valid override markers in `### Overrides (Run N)` matching regex `^<!-- override: finding-(\d+) reason:(.+?) approved-by:(.+?) timestamp:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) -->$` where finding-N matches an existing ❌ row AND capture groups are non-empty → `N_override_matched`. Track MALFORMED-OVERRIDE and DUPLICATE-OVERRIDE cases separately.
     - **Findings table contains ZERO data rows** (0 ✅ AND 0 ❌) → REFUSE. Gate 2 extracted nothing from the plan — suspicious (few plans have zero verifiable items). Report: "Gate 2's findings table is empty at `<artifact-path>`. Either re-run Gate 2 with explicit re-read instruction or verify the plan file is intact." Do NOT silently proceed as `pass`.
     - **N_fail == 0 AND findings table has at least one row** → `pass`. Proceed to step 3.
     - **N_fail > 0 AND every ❌ covered by valid override** → `needs-override`. Announce: `"Executing with [N_override_matched] acknowledged API gaps per <artifact-path>"`. Proceed to step 3.
     - **N_fail > 0 AND not all covered** → REFUSE. Report:
       > "Plan verification has [N_fail - N_override_matched] unresolved ❌ findings at `<artifact-path>`. Resolve by revising the plan (Gate 2 re-runs on revision) or adding override markers in the `### Overrides (Run N)` sub-section. Format: `<!-- override: finding-N reason:... approved-by:... timestamp:... -->`. Re-run `/execute` after."
       List each unresolved ❌ inline (finding number, named specific, target, suggested fix). Also list any MALFORMED-OVERRIDE or DUPLICATE-OVERRIDE details so operator sees near-miss overrides.
   - **Body structure missing, latest run section malformed, findings unparseable, OR findings table has zero rows** → REFUSE. Report the specific parse issue with the artifact path.

   **Why body-as-truth?** Frontmatter `status:` is written once by Gate 2 before any overrides exist. Overrides are added by the operator after; nobody updates frontmatter. Consumers derive effective status from body every time. See `skills/spec/references/research-gate-2.md` → Derived Status Calculation for the canonical algorithm and test matrix.
3. **Mission-control mode detection.** Run mc detection per `skills/spec/references/mc-detection.md`.
   - If `mc_active` AND `$CLAUDE_PROJECT_DIR/vault/tickets/` contains ≥1 ticket file (`TCK-*.md`) → enter mc-mode (skip plan.md path; proceed to the Mc-Mode Work Loop section below).
   - If `mc_active` AND `vault/tickets/` is empty → fall back to plan.md path (operator hasn't generated tickets yet).
   - If NOT `mc_active` → existing plan.md path.

   **Plan.md coexistence (R4.8):** if BOTH `vault/tickets/` (≥1 ticket) AND an approved plan file in `docs/gigo/plans/` exist, prompt operator once per project: *"This project has both a plan file and mission-control tickets. Which is the source of truth for this run? [tickets / plan / both (run plan tasks first, then tickets)]"*. Store decision in preference file as `tiebreak: tickets | plan | sequential`.
4. **Read the full plan.** Extract all tasks, their descriptions (full text), dependencies, and parallelization markers.
   - **Check for checkpoints.** Scan for `<!-- checkpoint: ... -->` comments in the plan.
   - **If checkpoints found:** Report progress to the operator, verify SHAs exist, and resume from the appropriate point. See `references/checkpoint-format.md` for the full resume procedure.
   - **If no checkpoints:** Fresh execution — proceed normally.
5. **Present execution options.** Let the operator choose their tier:

   > "Ready to execute. Available options:
   > 1. **Subagents** (recommended) — fresh worker per task, parallel dispatch for independent tasks, lead-managed review.
   > 2. **Inline** — sequential in this session, no isolation. Good for small plans or debugging.
   > 3. **Agent teams** (experimental opt-in) — full parallelization via shared task list, hook-enforced review. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.
   >
   > Which route?"

   **Default behavior:** Use subagents for plans with 3+ tasks. Use inline for plans with 1-2 tasks. Present the choice to the operator only if they haven't already specified a preference. Do NOT silently choose inline for larger plans just because it's easier.

   **Announce your choice.** Before executing, announce which tier you're using and why:
   > "Executing with [Tier]: [reason]. [N] tasks, [M] parallelizable."

---

## Tier 1: Subagents (Primary)

Fresh subagent per task. Lead controls dispatch, review, and triage.

**Worktree isolation:** Use `isolation: "worktree"` for parallel tasks when available — each worker gets its own repo copy. If worktree creation fails (not a git repo, permissions, hooks), drop `isolation: "worktree"` and dispatch subagents without it. Subagents without worktrees still give fresh context per task — you just lose file isolation, so dispatch parallel tasks sequentially instead. **Do NOT fall back to inline just because worktrees failed.**

### Execution Flow

For each **wave** of unblocked tasks:

1. **Identify the wave.** All tasks whose `blocked-by` dependencies are satisfied.
2. **Pre-flight.** Verify readiness:
   - List files each task will create or modify
   - Check for file conflicts between parallel tasks — same file means sequential
   - **CWD check:** Confirm you're in `$CLAUDE_PROJECT_DIR`
3. **Dispatch.** For parallelizable tasks with no file conflicts, dispatch multiple subagents in one message. Each gets:
   - `isolation: "worktree"` if available (omit if worktrees failed — dispatch sequentially instead)
   - Full task text from the plan
   - Context from completed dependencies ("What Was Built" addendums)
   - Model selected per task complexity — see `references/model-selection.md`
   - The implementation prompt from `references/teammate-prompts.md` (Tier 1 variant, includes worktree awareness)
4. **Wait for completion.** Process results as subagents finish. The Agent tool returns the worktree path and branch name for each worker that made changes.
5. **Review each completed task.** Invoke `gigo:verify` (Stage 1: spec compliance, Stage 2: engineering quality) on the worker's branch.
6. **Triage findings.** For each reviewed task:
   - **Auto-fix:** Dispatch a fix subagent to the same worktree branch with review feedback. Re-review after fix.
   - **Ask-operator:** Surface to operator. Task stays blocked. Move to next independent task.
   - **Accept/pass:** Merge the branch, write addendum, checkpoint.
7. **Merge.** After review passes, merge the worker's branch back to main:
   - `git merge --no-ff <branch>` with a descriptive commit message referencing the task
   - If merge conflicts: attempt auto-resolution for trivial conflicts. If non-trivial, escalate to operator.
   - Run tests after merge to verify integration
   - Worktree and branch are cleaned up automatically after merge
8. **Update the wave.** Completed and merged tasks unblock dependent tasks. Repeat from step 1 with the new wave.

For deep reference on worktree lifecycle, merge strategies, and known issues, read `.claude/references/worktree-isolation.md`.

### Parallel Dispatch Rules

- Only dispatch tasks in parallel if they're marked `parallelizable: true` in the plan
- Never dispatch tasks that modify the same files in parallel — pre-flight catches this
- If unsure about file conflicts, dispatch sequentially — wasted time beats merge conflicts
- The lead can dispatch up to 3-4 subagents per wave (more creates diminishing returns from context switching)

### Retry Protocol

When a subagent returns BLOCKED or fails (max 2 retry attempts per task):

1. **Attempt 1:** Same model, include error context in prompt. Dispatch to a fresh worktree.
2. **Attempt 2:** One model tier up (e.g., Sonnet → Opus), include both error contexts.
3. **Escalate:** "Task N failed twice. Here's what happened: [errors]. Options: break it down, change approach, or skip."

Never silently retry more than twice. Never silently skip a failure. The operator decides after escalation.

### Status Handling

Workers report one of four statuses:

**DONE** — Proceed to review via `gigo:verify`. Handle triage categories: auto-fix items go back to a fix subagent on the same branch, ask-operator items block the task, accept items go into the addendum.

**DONE_WITH_CONCERNS** — Worker completed the task but flagged doubts. Read the concerns before proceeding to review. If concerns are about correctness or scope, address them first.

**NEEDS_CONTEXT** — Worker needs information that wasn't provided. Provide context and re-dispatch a new subagent (fresh worktree).

**BLOCKED** — Enters the retry protocol above.

---

## Tier 2: Inline (Fallback)

If subagents are unavailable or the operator prefers it (debugging, simple plans).

- Execute tasks sequentially in the current session
- No context isolation between tasks
- Lead writes checkpoints after each task. On context limit, the next session resumes from checkpoints.

> "Running inline — no parallelization, no context isolation. Good for small plans or debugging."

**CRITICAL — per-task review is NOT optional in inline mode.** After completing each task (tests pass, code committed), you MUST dispatch `gigo:verify` as a subagent before moving to the next task. You are both the lead and the worker in inline mode — that makes independent review MORE important, not less. Self-review is not a substitute for `gigo:verify`.

After each task:
1. Commit the work
2. Dispatch `gigo:verify` as a subagent (Stage 1: spec compliance, Stage 2: engineering quality)
3. Triage findings — auto-fix, ask-operator, accept
4. Fix any auto-fix items, re-run verify
5. Only then proceed to the next task

Do NOT skip this step. Do NOT move to the next task without review passing.

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

After a task passes both review stages, update the plan document before moving to the next task. **Batch all updates into a single edit** — mark all checkboxes and write the addendum in one pass. Do not make separate edits for each checkbox.

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
3. **Auto-changelog.** Generate a changelog entry:
   - Read the approved spec (linked in the plan header under `**Spec:**`)
   - Get the git diff since execution started: `git diff <first-task-parent-sha>..HEAD`
   - Generate a changelog entry in Keep a Changelog format grounded in both sources
   - The entry describes what was BUILT (from the diff), not what was PLANNED (from the spec). The spec provides "why" context, the diff provides "what" facts.
   - Use `[Unreleased]` for version unless the operator specifies one. Use today's date.
   - Append to project root `CHANGELOG.md`. If no `CHANGELOG.md` exists, create it with the standard Keep a Changelog header.
   - Commit the changelog update.
4. **Compact.** Compact the conversation to shed execution context before offering the next skill.
5. **Handoff.** Ask the operator:
   > "Want me to run /verify in PR mode for the final gate? Or /sweep for a deep code sweep?"
   - `/verify` → invoke `gigo:verify` in PR mode
   - `/sweep` → invoke `gigo:sweep`
   - Neither → done

---

## Mc-Mode Work Loop

When Before-Starting step 3 resolves to mc-mode (mc active + tickets present), read `skills/execute/references/mc-mode-work-loop.md` for the full procedure: two-pass crash recovery, main ticket loop with mandatory ticket-body read from `vault/tickets/{id}.md`, worker prompt contents, auto-changelog, and the non-mutation rule.

Key constraints enforced by the reference:
- One ticket at a time in v1 (parallel deferred to v2)
- mc enforces DAG order via `mc-ticket-status --json`'s `unblocked` array; execute picks first-listed
- Worker prompt is self-contained (ticket body from `vault/tickets/*.md`, not a plan file)
- Execute NEVER writes to ticket frontmatter — state changes flow through signal files and verify verdicts

---

## Red Flags

**Never:**
- Start implementation without an approved plan
- Dispatch tasks when `plan-verification.md` shows effective status `fail` with unresolved ❌ findings — the operator must revise the plan OR add override markers first
- Skip review on any task
- Proceed with unfixed review issues
- Ignore worker escalations (BLOCKED, NEEDS_CONTEXT)
- Silently skip a task
- Make workers read the plan file — provide full task text in the dispatch prompt
- Mutate ticket frontmatter in mc-mode (authority principle: mc owns ticket state, gigo emits signals)
- Treat `mc-ticket-status --json` output as sufficient ticket context (ticket-body read from `vault/tickets/{id}.md` is MANDATORY before worker dispatch)
- Use `mc-ticket-status`'s `by_status.in_progress` count as a ticket list (it's a count int, not an iterable — use `mc-ticket-ls --status in_progress --json` for enumeration)

**If a worker reports concerns:** Read them before proceeding. Don't rush into review.

**If review finds issues:** The worker fixes them, review runs again. Repeat until approved. Don't skip the re-review.

---

## References

- `references/teammate-prompts.md` — Implementation and fix prompt templates (all tiers)
- `references/model-selection.md` — When to use which model tier
- `references/review-hook.md` — TaskCompleted hook configuration (agent teams only)
- `references/checkpoint-format.md` — Checkpoint syntax, resume procedure, edge cases
