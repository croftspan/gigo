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
| `reviewed` | `pass`, `issues-found`, `ask-operator-pending`, `ask-operator-resolved`, `pending` | Review state at interruption |
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
| `status=in-review, reviewed=ask-operator-resolved` | Operator already decided. Dispatch worker with the decision — don't re-ask. |
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

**Tier 1 race window between hook pass and checkpoint write:** In Tier 1, the review hook passes (task marked complete in task list) before the lead writes the addendum and checkpoint. If the session crashes in this window, the task list says "complete" but no checkpoint exists. On resume, "checkpoint state wins" means this task would be treated as not started and re-dispatched. This is wasteful but not destructive — the work exists in git, and re-doing a completed task produces the same result. The window is narrow (seconds between hook pass and lead writing the checkpoint). Accepted as a known limitation; two-phase checkpoints would add complexity for a rare scenario.

**Operator decided, worker implementing:** When the operator resolves an ask-operator item and the worker starts implementing the decision, write a checkpoint with `reviewed=ask-operator-resolved`. This distinguishes "operator hasn't responded yet" (`ask-operator-pending`) from "operator decided, implementation in progress" (`ask-operator-resolved`). On resume, `ask-operator-resolved` means dispatch the worker with the operator's decision — don't re-ask the operator.

## When to Write Checkpoints

Checkpoints are written by the lead (not the worker) after:
1. Review passes (both stages)
2. "What Was Built" addendum is appended
3. Plan document is committed with the updated checkboxes, addendum, and checkpoint

All three happen atomically — if any step fails, the checkpoint is not written. This ensures checkpoints always represent a consistent, verified state.
