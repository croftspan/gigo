# Pipeline Enhancements — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-27-pipeline-enhancements-design.md`

**Goal:** Add "What Was Built" addendum, resume capability, and review triage to gigo:execute and gigo:review.

**Architecture:** All changes are prompt additions to existing SKILL.md files and reference files. No code, no scripts, no new skills. The plan document is the persistent storage layer for all three enhancements.

---

## Task Dependency Graph

```
Task 1 (review triage in gigo:review)
  ├── blocks: 2, 4, 5
  └── blocked-by: none

Task 2 (review triage in gigo:execute — hook + fix prompts)
  ├── blocks: 4
  └── blocked-by: 1

Task 3 (checkpoint reference file)
  ├── blocks: 5
  └── blocked-by: none

Task 4 (addendum + triage integration in gigo:execute SKILL.md)
  ├── blocks: 6
  └── blocked-by: 1, 2

Task 5 (resume detection in gigo:execute SKILL.md)
  ├── blocks: 6
  └── blocked-by: 3

Task 6 (self-review — verify all cross-references and integration points)
  ├── blocks: none
  └── blocked-by: 4, 5
```

Tasks 1 and 3 are independent and parallelizable. Task 2 depends on 1 (triage categories must exist before the hook references them). Tasks 4 and 5 are parallelizable once their dependencies resolve. Task 6 is the integration check.

---

### Task 1: Review Triage — gigo:review Changes

**blocks:** 2, 4, 5
**blocked-by:** —
**parallelizable:** true (with Task 3)

**Files:**
- Modify: `skills/review/SKILL.md`
- Modify: `skills/review/references/engineering-reviewer-prompt.md`
- Modify: `skills/review/references/spec-reviewer-prompt.md`

- [ ] **Step 1: Add "Suggested triage" field to engineering reviewer prompt**

In `skills/review/references/engineering-reviewer-prompt.md`, add a new field to the per-issue output format. After the existing `**Confidence**` line in the `For each issue:` section, add:

```
- **Suggested triage:** auto-fix | ask-operator | accept
```

Add a brief instruction above the output format section explaining the triage categories:

```
## Triage Suggestion

For each issue, suggest a triage category:
- **auto-fix** — minor issue with an obvious fix (formatting, naming, missing import). No architectural implications.
- **ask-operator** — fix would change the interface, involves a trade-off, or requires a scope/architecture decision.
- **accept** — observation worth noting but doesn't need a fix. Future consideration, strength, informational.

Your suggestion is a hint — the final triage decision is made by gigo:review, not you.
```

- [ ] **Step 2: Add "Suggested triage" field to spec reviewer prompt**

In `skills/review/references/spec-reviewer-prompt.md`, add triage suggestion to the output. After the existing report format (`✅ Spec compliant` or `❌ Issues found`), add:

```
For each issue, include:
- What's missing or wrong, with file:line references
- **Suggested triage:** auto-fix | ask-operator | accept

Triage guidance:
- Missing requirement where the spec is clear about what to build → auto-fix
- Missing requirement where the approach is ambiguous → ask-operator
- Extra/unneeded work that doesn't break anything → accept
- Misunderstanding of requirements → ask-operator
```

- [ ] **Step 3: Add "Triage" section to gigo:review SKILL.md**

In `skills/review/SKILL.md`, add a new section titled `## Triage` between the `---` separator that follows `## Stage 2: Engineering Review` and the `## Send-Back-and-Fix Loop` section:

```markdown
## Triage

After both stages complete, categorize each finding before returning feedback.

| Category | Criteria | Action |
|---|---|---|
| **auto-fix** | Minor, obvious fix, no architectural implications | Return to worker: "Fix these, no discussion needed." |
| **ask-operator** | Architectural, scope, ambiguous, or interface-changing | Surface to operator. Task stays blocked until operator decides. |
| **accept** | Informational, future consideration, strength | Record in addendum, don't send as fix items |

**Default rules:**
- Spec review findings → ask-operator (unless fix is unambiguous)
- Engineering review findings → auto-fix (unless interface-changing or architectural)
- Critical issues (confidence 90+) → never accept. Must be auto-fix or ask-operator.
- When in doubt → ask-operator. False escalation costs a question. False auto-fix can cost a wrong decision.

**Output the categorized summary:**

### Auto-Fix (worker handles)
[numbered list with file:line references]

### Ask Operator
[numbered list — these block the task]

### Accept (noted, no action)
[numbered list — goes into the addendum]

**In execution context** (called from gigo:execute): send auto-fix to worker, surface ask-operator to operator and wait, pass accept to lead for the addendum.

**In standalone mode:** present all three categories to the operator.
```

- [ ] **Step 4: Update "Send-Back-and-Fix Loop" section to respect triage**

In `skills/review/SKILL.md`, replace the existing "Send-Back-and-Fix Loop" section content (the section starting with `## Send-Back-and-Fix Loop`):

```markdown
## Send-Back-and-Fix Loop

When issues are found:

1. **Triage first.** Categorize all findings (see Triage section above).
2. **Auto-fix items** → return to the caller with "Fix these, no discussion needed."
3. **Ask-operator items** → surface to the operator. Task stays blocked until operator decides. Worker can move to independent tasks.
4. **Accept items** → pass to the lead for the "What Was Built" addendum. No fix needed.
5. After fixes are applied, re-review the fix commits.
6. Repeat until both stages pass with no auto-fix or ask-operator items remaining.

During execution, gigo:execute handles the routing. In standalone mode, present all categories to the operator and wait for direction.
```

- [ ] **Step 5: Commit**

```bash
git add skills/review/SKILL.md skills/review/references/engineering-reviewer-prompt.md skills/review/references/spec-reviewer-prompt.md
git commit -m "feat(review): add triage categorization — auto-fix, ask-operator, accept"
```

---

### Task 2: Review Triage — gigo:execute Integration (Hook + Fix Prompts)

**blocks:** 4
**blocked-by:** 1
**parallelizable:** false

**Files:**
- Modify: `skills/execute/references/review-hook.md`
- Modify: `skills/execute/references/teammate-prompts.md`

- [ ] **Step 1: Update hook exit code semantics in review-hook.md**

In `skills/execute/references/review-hook.md`, replace the current `**Exit code semantics:**` section with the triage-aware version:

```markdown
**Exit code semantics (triage-aware):**

| Findings present | Hook exit | Effect |
|---|---|---|
| Auto-fix only | 2 | Worker fixes, re-submits |
| Ask-operator only | 2 | Task blocked. `[ASK-OPERATOR]` prefixed feedback tells worker to move to another task. Lead handles operator communication. |
| Auto-fix + ask-operator | 2 | Worker fixes auto-fix items first. Task stays blocked on ask-operator items after auto-fix re-review passes. |
| Accept only | 0 | Task complete. `[ACCEPT]` prefixed items in stderr for lead to capture into addendum. |
| Auto-fix + accept | 2 | Worker fixes auto-fix items. Accept items captured into addendum after fix passes. |
| No issues | 0 | Task complete. |

**Stderr prefixes:**
- `[AUTO-FIX]` — worker handles directly
- `[ASK-OPERATOR]` — worker moves to independent task, lead surfaces to operator
- `[ACCEPT]` — lead captures into "What Was Built" addendum
```

- [ ] **Step 2: Add ask-operator handling to Tier 1 section**

In `skills/execute/references/review-hook.md`, add to the `## How It Works` section, after step 7 ("Repeat until review passes"):

```markdown
**When ask-operator items are present:**

The hook exits 2 and includes `[ASK-OPERATOR]` prefixed items in stderr. The teammate receives this feedback and should move to the next available independent task (one that doesn't depend on the blocked task). The lead reads the ask-operator items from the task output and surfaces them to the operator. Once the operator decides:

1. Lead sends the decision to the teammate via `SendMessage`
2. Teammate implements the operator's decision
3. Teammate re-marks the task complete
4. Hook runs review again
```

- [ ] **Step 3: Update fix prompt templates for triage**

In `skills/execute/references/teammate-prompts.md`, update the `## Fix Prompt` section. Keep the existing Tier 2 fix prompt as the auto-fix variant and add the operator-resolved variant below it.

After the existing `### Tier 2: Subagent Re-dispatch` fix prompt code block, add:

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add skills/execute/references/review-hook.md skills/execute/references/teammate-prompts.md
git commit -m "feat(execute): update hook exit codes and fix prompts for triage categories"
```

---

### Task 3: Checkpoint Reference File

**blocks:** 5
**blocked-by:** —
**parallelizable:** true (with Task 1)

**Files:**
- Create: `skills/execute/references/checkpoint-format.md`

- [ ] **Step 1: Create checkpoint-format.md**

Create `skills/execute/references/checkpoint-format.md` with the following content:

```markdown
# Checkpoint Format — Resume Capability

Checkpoints are HTML comments embedded in the plan document after each task completes. They enable gigo:execute to resume after context limits, crashes, or session breaks.

## Syntax

After each task's last step, append a checkpoint comment:

### Completed task:
```
- [x] **Step 3: Commit**
<!-- checkpoint: sha=abc1234 status=done reviewed=pass tier=1 -->
```

### Task with review issues (mid-fix):
```
- [x] **Step 2: Implement**
- [ ] **Step 3: Commit**
<!-- checkpoint: sha=def5678 status=in-review reviewed=issues-found tier=2 -->
```

### Task blocked on operator decision:
```
- [x] **Step 2: Implement**
- [ ] **Step 3: Commit**
<!-- checkpoint: sha=ghi9012 status=in-review reviewed=ask-operator-pending tier=1 -->
```

## Fields

| Field | Values | Purpose |
|---|---|---|
| `sha` | Short git commit hash | Verify the work still exists on disk |
| `status` | `done`, `in-review`, `in-progress`, `blocked` | Where the task was when interrupted |
| `reviewed` | `pass`, `issues-found`, `ask-operator-pending`, `pending` | Review state at interruption |
| `tier` | `1`, `2`, `3` | Which execution tier was running |

## Resume Detection Procedure

When gigo:execute starts, step 2 ("Read the full plan") includes checkpoint scanning:

### 1. Scan for checkpoints

Search the plan document for `<!-- checkpoint:` comments. If none found, this is a fresh execution — proceed normally.

### 2. Report progress

If checkpoints found, report status to the operator:

```
Resuming execution. Progress detected:
- Task 1: ✅ done (sha: abc1234)
- Task 2: ✅ done (sha: def5678)
- Task 3: ⚠️ in-review — ask-operator-pending
- Task 4: ⬜ not started
- Task 5: ⬜ not started
```

### 3. Verify checkpoint validity

For each `done` checkpoint, verify the commit SHA exists:

```bash
git cat-file -t <sha>
```

If a SHA is missing (force-push, rebase, reset):

```
⚠️ Task 2 checkpoint references sha def5678 which no longer exists.
This task may need re-implementation. Proceed or investigate?
```

Wait for operator decision before proceeding.

### 4. Resume from the right point

| Checkpoint state | Action |
|---|---|
| `status=done, reviewed=pass` | Skip. Task is complete. |
| `status=in-review, reviewed=issues-found` | Re-run review on current state. If issues persist, dispatch fix. |
| `status=in-review, reviewed=ask-operator-pending` | Re-surface ask-operator items to the operator. Wait for decision. |
| `status=in-progress` | Dispatch worker to continue. Provide addendum context from completed dependencies. |
| `status=blocked` | Re-evaluate the blocker. Surface to operator if still blocked. |

## Tier-Specific Reconciliation

### Tier 1 (Agent Teams)

On resume, the shared task list may have stale state from a previous session. Reconciliation rules:

1. Checkpoint state wins over task list state.
2. Update the task list to match checkpoints before spawning teammates.
3. Mark `done` tasks as complete in the task list.
4. Mark `in-review` and `in-progress` tasks as available for claiming.
5. Rebuild the dependency graph from the plan — don't trust the previous session's task list dependencies.

### Tier 2 (Subagents) and Tier 3 (Inline)

No shared state to reconcile. Checkpoints are the sole source of truth.

## Edge Cases

**Plan file modified between sessions:** If the plan document was edited (tasks added, reordered, or descriptions changed) since checkpoints were written, warn the operator. Checkpoint task numbers may not match current task numbers. The lead should verify by matching task *names*, not numbers.

**Branch was rebased:** SHA verification will catch this — the checkpoint SHAs won't exist. The operator decides whether to re-run affected tasks or accept the rebased state.

**A `done` task's tests now fail:** This can happen if a later task introduced a regression, or if external dependencies changed. The checkpoint says "done" but the code is broken. The lead should run the full test suite before resuming and flag any failures in completed tasks.

**Partial checkpoint (crash mid-write):** If the checkpoint comment is malformed or incomplete, treat the task as `in-progress`. Better to re-do work than to skip a broken task.

## When to Write Checkpoints

Checkpoints are written by the lead (not the worker) after:
1. Review passes (both stages)
2. "What Was Built" addendum is appended
3. Plan document is committed with the updated checkboxes, addendum, and checkpoint

All three happen atomically — if any step fails, the checkpoint is not written. This ensures checkpoints always represent a consistent, verified state.
```

- [ ] **Step 2: Commit**

```bash
git add skills/execute/references/checkpoint-format.md
git commit -m "feat(execute): add checkpoint format reference — resume capability"
```

---

### Task 4: Addendum + Triage Integration in gigo:execute SKILL.md

**blocks:** 6
**blocked-by:** 1, 2
**parallelizable:** true (with Task 5)

**Files:**
- Modify: `skills/execute/SKILL.md`
- Modify: `skills/execute/references/teammate-prompts.md`

- [ ] **Step 1: Add "After Review Passes" section to SKILL.md**

In `skills/execute/SKILL.md`, add a new section between the `## Status Handling` section and the `## When All Tasks Complete` section:

```markdown
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
4. **Check downstream impact.** If the implementation deviated in ways that affect dependent tasks, check whether those task descriptions need updating before a worker claims them.
5. **Write checkpoint** (see `references/checkpoint-format.md`).
6. **Commit the plan update.**

**Rules:**
- Always write an addendum, even when nothing deviated. "No deviations" confirms the plan was accurate.
- Keep it brief — 1-3 bullets per field. This is a breadcrumb trail, not a post-mortem.
- Focus on what downstream workers need. A renamed export belongs here. A refactored internal helper doesn't.
```

- [ ] **Step 2: Update triage handling in status/review flow**

In `skills/execute/SKILL.md`, update the `**DONE**` status description in the Status Handling section. Replace the current text:

```
**DONE** — Proceed to review (via TaskCompleted hook in Tier 1, manual invocation in Tier 2/3).
```

With:
```
**DONE** — Proceed to review (via TaskCompleted hook in Tier 1, manual invocation in Tier 2/3). After review, handle triage categories: auto-fix items go back to the worker, ask-operator items block the task until the operator decides, accept items go into the addendum. See `gigo:review` Triage section.
```

- [ ] **Step 3: Add addendum reading hint to Tier 2 subagent prompt**

In `skills/execute/references/teammate-prompts.md`, add to the Tier 2 subagent template's `## Context` section (inside the code block, after `[Where this fits, dependencies, what was built in prior tasks]`):

```
If prior tasks have "What Was Built" addendums in the plan, read them — they
may record interface changes or deviations that affect your task.
```

- [ ] **Step 4: Update "When All Tasks Complete" section**

In `skills/execute/SKILL.md`, update the `## When All Tasks Complete` section to reference addendums:

Replace:
```
1. Synthesize results — what was built, what was reviewed, any concerns raised
2. Report to operator with a summary of completed work
```

With:
```
1. Synthesize results — read the "What Was Built" addendums across all tasks for a complete picture of deviations, review changes, and observations
2. Report to operator with a summary: what was built, what deviated from plan, what the review cycle caught, and any "accept" observations worth noting
```

- [ ] **Step 5: Update References section**

In `skills/execute/SKILL.md`, add to the `## References` list at the end of the file:

```
- `references/checkpoint-format.md` — Checkpoint syntax, resume procedure, edge cases
```

- [ ] **Step 6: Commit**

```bash
git add skills/execute/SKILL.md skills/execute/references/teammate-prompts.md
git commit -m "feat(execute): add What Was Built addendum and triage integration"
```

---

### Task 5: Resume Detection in gigo:execute SKILL.md

**blocks:** 6
**blocked-by:** 3
**parallelizable:** true (with Task 4)

**Files:**
- Modify: `skills/execute/SKILL.md`

- [ ] **Step 1: Expand "Before Starting" step 2 with resume detection**

In `skills/execute/SKILL.md`, expand step 2 in the `## Before Starting` section. Replace:

```
2. **Read the full plan.** Extract all tasks, their descriptions (full text), dependencies, and parallelization markers.
```

With:

```
2. **Read the full plan.** Extract all tasks, their descriptions (full text), dependencies, and parallelization markers.
   - **Check for checkpoints.** Scan for `<!-- checkpoint: ... -->` comments in the plan.
   - **If checkpoints found:** Report progress to the operator, verify SHAs exist, and resume from the appropriate point. See `references/checkpoint-format.md` for the full resume procedure.
   - **If no checkpoints:** Fresh execution — proceed normally.
```

- [ ] **Step 2: Add "Checkpointing" note to the execution tier sections**

In `skills/execute/SKILL.md`, add a brief note to each tier's "How it runs" section.

After the Tier 1 "How it runs" bullet list (before "The CLAUDE.md question"):

```
- After a task completes and addendum is written, the lead writes a checkpoint comment to the plan and commits. See `references/checkpoint-format.md`.
```

After the Tier 2 "How it runs" bullet list (before the "Surface this warning" block):

```
- After each review pass, the lead writes a checkpoint and commits. On resume, checkpoints are the sole source of truth — no shared state to reconcile.
```

After the Tier 3 description (before the "Surface this warning" block):

```
- Lead writes checkpoints after each task. On context limit, the next session resumes from checkpoints.
```

- [ ] **Step 3: Commit**

```bash
git add skills/execute/SKILL.md
git commit -m "feat(execute): add resume detection via checkpoint scanning"
```

**Note:** Tasks 4 and 5 both modify `skills/execute/SKILL.md` but in different sections — Task 4 adds "After Review Passes" and updates status handling/completion, while Task 5 expands "Before Starting" and adds checkpoint notes to tier sections. If running in parallel, the workers touch non-overlapping sections. If running sequentially, the second worker should read the file fresh to see the first worker's changes.

---

### Task 6: Self-Review — Cross-Reference and Integration Verification

**blocks:** —
**blocked-by:** 4, 5
**parallelizable:** false

**Files:**
- Read (verify): `skills/execute/SKILL.md`
- Read (verify): `skills/review/SKILL.md`
- Read (verify): `skills/execute/references/checkpoint-format.md`
- Read (verify): `skills/execute/references/review-hook.md`
- Read (verify): `skills/execute/references/teammate-prompts.md`
- Read (verify): `skills/review/references/engineering-reviewer-prompt.md`
- Read (verify): `skills/review/references/spec-reviewer-prompt.md`

- [ ] **Step 1: Verify cross-references**

Read all modified files and check:

1. `gigo:execute` SKILL.md references `references/checkpoint-format.md` — does the reference exist?
2. `gigo:execute` SKILL.md references `gigo:review` Triage section — does that section exist in review SKILL.md?
3. `gigo:review` SKILL.md references the "What Was Built" addendum — does execute SKILL.md define the format?
4. `review-hook.md` references `[ASK-OPERATOR]` and `[ACCEPT]` prefixes — are these consistent with the triage output format in review SKILL.md?
5. `teammate-prompts.md` has the operator-resolved variant — does it match the triage flow described in execute SKILL.md?
6. Both reviewer prompts include "Suggested triage" — consistent category names (`auto-fix`, `ask-operator`, `accept`)?

- [ ] **Step 2: Verify the complete flow end-to-end**

Trace the full lifecycle of one task:

1. Worker implements task → marks complete
2. Hook fires → gigo:review runs Stage 1 + Stage 2
3. Reviewers suggest triage categories on each finding
4. gigo:review applies triage rules, produces categorized output
5. Auto-fix → hook exits 2, worker fixes
6. Ask-operator → hook exits 2, worker moves to independent task, lead surfaces to operator
7. Accept → noted for addendum
8. After all auto-fix resolved and operator decisions made → review re-runs → passes
9. Lead writes addendum under the task
10. Lead writes checkpoint comment
11. Lead commits plan update
12. Next worker reads addendum from dependencies before starting

Verify each handoff point has matching input/output format between the two skills.

- [ ] **Step 3: Check for internal consistency in gigo:execute SKILL.md**

After Tasks 4 and 5 both modified this file, verify:
- No duplicate sections
- Section ordering makes sense: Before Starting → Three Execution Tiers → Status Handling → After Review Passes → When All Tasks Complete → Red Flags → References
- The checkpoint notes in tier sections don't duplicate the "After Review Passes" section
- References list includes all reference files

- [ ] **Step 4: Fix any issues found and commit**

If cross-reference issues are found, fix them inline. If the flow trace reveals a gap, add the missing connector.

```bash
git add -A
git commit -m "chore: self-review — verify cross-references and integration points"
```

If nothing needs fixing:

```bash
echo "Self-review passed. No issues found."
```

---

## Done When

1. `gigo:review` has a Triage section that categorizes findings into auto-fix, ask-operator, and accept
2. Both reviewer prompts include a "Suggested triage" field
3. `gigo:execute` writes a "What Was Built" addendum after each task passes review
4. `gigo:execute` writes checkpoint comments and can resume from them on restart
5. The hook exit codes and fix prompts handle all three triage categories
6. Ask-operator items block the task — worker moves to independent tasks while waiting
7. All cross-references between the two skills are verified and consistent

## Risks

- **Tasks 4 and 5 both modify `skills/execute/SKILL.md`.** They touch different sections but if run in parallel, merge conflicts are possible. The plan marks them parallelizable but notes the overlap — gigo:execute should handle this with a fresh read before the second worker starts.
- **Review SKILL.md line count.** Adding the Triage section and updating Send-Back-and-Fix adds ~30 lines. Current file is 113 lines. The result (~143 lines) is reasonable for a SKILL.md — well under the 500-line hub limit.
- **Execute SKILL.md line count.** Adding "After Review Passes" and expanding "Before Starting" adds ~25 lines. Current file is 127 lines. Result (~152 lines) — also fine.
