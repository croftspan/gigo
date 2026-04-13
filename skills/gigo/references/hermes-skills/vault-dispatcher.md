---
name: vault-dispatcher
description: "Reads vault tickets, builds dependency graph, dispatches ready tickets to the model for execution."
version: 1.0.0
metadata:
  hermes:
    tags: [orchestration, dispatch, vault]
---

# Vault Dispatcher

## Dispatch Loop

1. Read all `.md` files in `vault/tickets/`. Parse YAML frontmatter from each. Skip `TEMPLATE.md`.
2. Build dependency DAG. For each ticket, map `depends_on` entries to ticket IDs.
3. Select next ticket: `status == "ready"` AND every ID in `depends_on` has `status == "done"`. If multiple qualify, pick the lowest sequence number. If none qualify and no tickets are `in_progress`, dispatch is complete.
4. Set `status: in_progress` on selected ticket. Append to `model_history`: `{model: "{model_id}", timestamp: "{ISO 8601}", result: "started"}`. Re-parse the written YAML to validate it.
5. Construct prompt:
   - System message: read `.claude/references/gemma-harness.md`, extract content after the `---` divider. If file does not exist, use `vault/_governance/PROJECT_RULES.md` as the system message.
   - User message: ticket body (Summary through Notes from Prior Attempts) + inlined source files selected by `skill_hints` and `produced_files`.
6. Send prompt to the model via the configured provider.
7. Parse response. Extract code blocks with file path headers (`// filepath: path/to/file` or `# filepath: path/to/file`). Each maps to a file write.
8. Write each extracted code block to its file path using `write_file`.
9. Run proof-of-work. Read `vault/_schema/proof-of-work.md` for test and lint commands. Execute test command via `terminal`, capture output to `vault/agents/model/{ticket-id}-test.log`. Execute lint command, capture to `vault/agents/model/{ticket-id}-lint.log`. Update `proof_of_work.produced.test_output` and `proof_of_work.produced.lint_output` with log paths.
10. Route on results:
    - Test and lint both exit 0: generate reviewer verdict at `vault/agents/reviewer/{ticket-id}.md` (see Reviewer Verdict below). Set `proof_of_work.produced.reviewer_verdict` to the file path. Set `status: done`. Append `{result: "passed"}` to `model_history`. Go to step 1.
    - Any failure: append error output (last 20 lines) to the user message. Re-send to model (steps 6-9). One retry only.
    - Retry also fails: set `status: escalated`. Append `{result: "escalated"}` to `model_history`. Read `vault/_orchestration/escalation-protocol.md`. Invoke `claude-code` skill with the escalation prompt.
    - Claude Code succeeds (proof-of-work passes): set `status: done` with `model: "claude-code"` in history.
    - Claude Code fails: set `status: failed`. Log to `vault/agents/claude-code/{ticket-id}/`. Go to step 1.

## After Each Ticket

1. Invoke `circuit-breaker` skill with the ticket result. Read the return value.
2. If `triggered: true`: send alert via `send_message`:
   `⚠️ Circuit breaker triggered ({trigger_type}). Escalation rate: {rate}. Dispatch paused. Send /resume to restart.`
   Stop dispatching. Wait for `/resume`.
3. If not triggered: read `vault/agents/circuit-breaker/state.md`. If `paused: true`, wait. Otherwise go to step 1.

## Parallelism

After step 3, if multiple tickets qualify (independent — no shared `depends_on` paths), dispatch up to 3 in parallel via `delegate_task()`. Check `produced_files` arrays for overlap before parallel dispatch. Overlapping tickets serialize — dispatch one, keep the other `ready`.

## Reviewer Verdict

Generate at `vault/agents/reviewer/{ticket-id}.md` after test and lint pass:

```markdown
# Reviewer Verdict — {ticket-id}
**Status:** auto-approved
**Timestamp:** {ISO 8601}
**Model:** {model that produced the code}
**Test result:** pass
**Lint result:** pass
All required proof-of-work artifacts passed automated checks.
```
