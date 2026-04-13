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

### Task completed via local model:

```
- [x] **Step 5: Write endpoint**
<!-- checkpoint: sha=jkl3456 status=done reviewed=pass tier=1 model=gemma-4-26b-a4b -->
```

## Fields

| Field | Values | Purpose |
|---|---|---|
| `sha` | Short git commit hash | Verify the work still exists on disk |
| `status` | `done`, `in-review`, `in-progress`, `blocked` | Where the task was when interrupted |
| `reviewed` | `pass`, `issues-found`, `ask-operator-pending`, `ask-operator-resolved`, `pending` | Review state at interruption |
| `tier` | `1`, `2` | Which execution tier was running |
| `model` | Model ID as reported by `/v1/models` (e.g., `gemma-4-26b-a4b`) or `claude-haiku`, `claude-sonnet`, `claude-opus` | Which model generated the code (optional, omit when local routing disabled) |

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

**Model field on resume:** The `model` field is informational only. Resume logic ignores it — it doesn't affect which model handles a retry. Its purpose is production tracing: when a task's output quality is questioned, the model field answers "who wrote this?"

## Reconciliation on Resume

For the primary execution path (subagents and inline), there's no shared state to reconcile. Checkpoints in the plan file are the sole source of truth. The lead reads them and picks up where it left off.

## Edge Cases

**Plan file modified between sessions:** If the plan document was edited (tasks added, reordered, or descriptions changed) since checkpoints were written, warn the operator. Checkpoint task numbers may not match current task numbers. The lead should verify by matching task *names*, not numbers.

**Branch was rebased:** SHA verification will catch this — the checkpoint SHAs won't exist. The operator decides whether to re-run affected tasks or accept the rebased state.

**A `done` task's tests now fail:** This can happen if a later task introduced a regression, or if external dependencies changed. The checkpoint says "done" but the code is broken. The lead should run the full test suite before resuming and flag any failures in completed tasks.

**Partial checkpoint (crash mid-write):** If the checkpoint comment is malformed or incomplete, treat the task as `in-progress`. Better to re-do work than to skip a broken task.

**Operator decided, worker implementing:** When the operator resolves an ask-operator item and the worker starts implementing the decision, write a checkpoint with `reviewed=ask-operator-resolved`. This distinguishes "operator hasn't responded yet" (`ask-operator-pending`) from "operator decided, implementation in progress" (`ask-operator-resolved`). On resume, `ask-operator-resolved` means dispatch the worker with the operator's decision — don't re-ask the operator.

## When to Write Checkpoints

Checkpoints are written by the lead (not the worker) after:
1. Review passes (both stages)
2. "What Was Built" addendum is appended
3. Plan document is committed with the updated checkboxes, addendum, and checkpoint

All three happen atomically — if any step fails, the checkpoint is not written. This ensures checkpoints always represent a consistent, verified state.
