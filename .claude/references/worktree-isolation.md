# Worktree Isolation — Deep Reference

Read this when designing or debugging worktree-isolated parallel execution. Covers the lifecycle, merge strategies, known issues, and cleanup procedures.

## How It Works

The Agent tool's `isolation: "worktree"` parameter creates a temporary git worktree for the subagent. Each worker gets a full copy of the repo on its own branch. The worktree is automatically cleaned up when the subagent finishes without changes; if changes were made, the worktree path and branch name are returned in the agent result.

## Dispatch Pattern

```
Agent(
  prompt: "...",
  isolation: "worktree",
  mode: "bypassPermissions",  // or appropriate mode
  model: "sonnet",            // per model-selection.md
  description: "Task N: short description"
)
```

Multiple Agent calls in a single message dispatch workers in parallel, each to their own worktree.

## Merge Protocol

After a worker's task passes review:

1. Ensure CWD is `$CLAUDE_PROJECT_DIR` (not inside a worktree)
2. `git merge --no-ff <branch>` — preserves branch history in the merge commit
3. If merge conflicts:
   - Trivial (non-overlapping hunks in same file): attempt auto-resolution
   - Non-trivial (overlapping edits, semantic conflicts): escalate to operator
4. Run tests after merge to verify integration
5. Worktree and branch are cleaned up automatically

**Merge commit message format:**
```
merge: Task N — <short task description>

Merged from worktree branch <branch-name>.
Review: passed (Stage 1 + Stage 2)
```

## Known Issues

### CWD Drift After Context Compaction

**Bug:** When the orchestrator (lead) dispatches subagents with `isolation: "worktree"`, context compaction can leave the lead's CWD pointing inside a previous worktree path. Subsequent worktree dispatches then nest inside the previous worktree instead of being created at the repo root.

**Mitigation:** Before each dispatch wave, the lead should verify CWD:
```bash
cd "$CLAUDE_PROJECT_DIR"
pwd  # confirm we're at repo root
```

If CWD has drifted, `cd` back to the project root before dispatching.

**Tracking:** [anthropics/claude-code#27881](https://github.com/anthropics/claude-code/issues/27881)

### Worktree Cleanup on Failure

If a subagent crashes or is killed, the worktree may not be cleaned up automatically. Before starting a new execution session, check for stale worktrees:
```bash
git worktree list  # shows all worktrees
git worktree prune  # removes stale entries
```

### Branch Naming

Worktree branches are auto-named by Claude Code. The lead doesn't control branch names. Identify branches by the worktree path returned in the agent result, not by guessing branch names.

## Sequential Fallback

If worktree isolation causes issues (rare), fall back to Tier 2 (inline sequential execution). Don't fight infrastructure problems — dispatch sequentially and move on. Report the issue to the operator.

## Retry With Worktrees

Each retry attempt gets a fresh worktree. The failed worktree's branch may still exist — that's fine. The new worktree creates a new branch. After the task eventually passes, only the successful branch gets merged; failed branches are cleaned up.

## When Workers Share Dependencies

If Task B depends on Task A's output, Task A must be merged to main before Task B's worktree is created. The worktree snapshots the repo at creation time — it won't see uncommitted changes from other worktrees.

This is why the dependency graph matters: dependent tasks cannot be in the same wave. The pre-flight check catches this.
