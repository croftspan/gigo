# Review Hook — TaskCompleted Gate

This hook runs when any teammate marks a task as complete. It invokes `gigo:review` and blocks completion if review finds issues.

## How It Works

1. Teammate marks task complete -> TaskCompleted hook fires
2. Hook invokes `gigo:review` (per-task mode) on the committed code
3. If review passes -> hook exits 0, task is marked complete
4. If review finds issues -> hook exits 2 with review feedback as stderr
5. Teammate receives the feedback and continues working on the task
6. Teammate tries to mark complete again -> hook runs again
7. Repeat until review passes

## Hook Configuration

Configure in `.claude/settings.json` or `.claude/settings.local.json`:

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/gigo-review-gate.sh",
            "timeout": 300,
            "statusMessage": "Running gigo:review on completed task..."
          }
        ]
      }
    ]
  }
}
```

## The Hook Script

The hook script (`.claude/hooks/gigo-review-gate.sh`) should:

1. Read task info from stdin (JSON with task_id, task_subject, task_description)
2. Determine the git SHA range for the task's changes
3. Run gigo:review Stage 1 (spec compliance) and Stage 2 (engineering review)
4. If all issues are below threshold -> exit 0 (pass)
5. If issues found -> write feedback to stderr, exit 2 (block)

**Exit code semantics:**
- `0` — review passed, task completion allowed
- `2` — review found issues, task completion blocked, stderr feedback sent to teammate

## Implementation Note

The exact hook script implementation depends on how `gigo:review` is invocable from a shell script. Options:

- Invoke `claude` CLI with a review prompt
- Call `gigo:review` as a skill from within the hook
- Run the review checks directly in the script

This is a design decision to finalize during implementation testing. The hook infrastructure is proven — the `TaskCompleted` and `TeammateIdle` hook events have been available since Claude Code 2.1.33. The integration point with `gigo:review` needs testing.

## For Tier 2 (Subagents)

When using subagents instead of agent teams, there is no TaskCompleted hook. The lead (`gigo:execute`) invokes `gigo:review` manually after each subagent completes:

1. Subagent finishes and reports status
2. Lead invokes `gigo:review` with the task spec and committed code
3. If review passes, lead moves to next task
4. If review finds issues, lead dispatches a fix subagent with the review feedback (see `teammate-prompts.md` fix prompt)
5. After fix, lead invokes `gigo:review` again
6. Repeat until review passes

Same review quality, different trigger mechanism.
