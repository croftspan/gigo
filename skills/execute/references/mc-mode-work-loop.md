# Mc-Mode Work Loop — Ticket-Based Execution

Used when `gigo:execute` Before-Starting detection resolves to mc-mode (per `skills/spec/references/mc-detection.md` and `execute/SKILL.md` Before-Starting step 3). One ticket at a time in v1; parallel ticket execution deferred to v2.

## Crash Recovery (runs before main loop)

Two-pass audit per R4.6. Both passes run; results are combined before prompting the operator.

### Pass A — signal-file based (30-day window, mc-scrub limit)

Scan `$CLAUDE_PROJECT_DIR/vault/agents/logs/` for `{ticket-id}-execute-pickup.md` files WITHOUT a corresponding `{ticket-id}-execute-complete.md`. Collect these ticket IDs as "interrupted within last 30 days."

Pass A only finds recent interruptions because `mc-scrub` (default `--days 30`) deletes files in `vault/agents/logs/` older than 30 days.

### Pass B — ticket-list based (complete coverage)

Run `bash("cd $CLAUDE_PROJECT_DIR && mc-ticket-ls --status in_progress --json")`. This returns a JSON array of ticket objects with at least `{id, title, status, phase, depends_on}`.

(NOTE: do NOT use `mc-ticket-status --json`'s `by_status` field — that is a count dict per `mission-control/bin/mc-ticket-status` line 66, not a list. mc-ticket-ls with `--status` and `--json` is the correct enumeration command per `mission-control/bin/mc-ticket-ls` lines 35, 43.)

For each ticket `t` in the returned array: check whether `$CLAUDE_PROJECT_DIR/vault/agents/logs/{t.id}-execute-pickup.md` exists. If NOT, collect with annotation "in_progress without recent pickup signal — possibly interrupted before scrub or by another executor."

### Combined handling

If Pass A or Pass B returned any tickets, present the combined list to the operator using the crash-recovery message format in §Conventions of the spec. For each ticket, operator chooses `[r] Re-pick / [e] Escalate / [s] Skip`. Execute does NOT mutate ticket state — all state changes stay in the operator's hands per the authority principle.

Honest non-claim: mission-control as of current HEAD does not provide automatic stale-`in_progress` detection. Operators needing detection beyond the mc-scrub window rely on this startup audit or manual `mc-ticket-ls --status in_progress --json` invocations.

## Main Loop

```
while True:
  # Step 1: Ask mc what's ready
  status_json = bash("cd $CLAUDE_PROJECT_DIR && mc-ticket-status --json")
  ready = status_json["unblocked"]  # list of {id, title} objects per mc-ticket-status lines 67
  if len(ready) == 0:
    break

  ticket_id = ready[0]["id"]  # mc enforces DAG order; first-listed is correct

  # Step 2: Fetch full ticket body from disk (MANDATORY)
  # mc-ticket-status --json returns ONLY id + title (minimal JSON).
  # Worker needs Summary, Context, Implementation Notes, Acceptance Tests sections,
  # plus exit_criteria and produced_files from frontmatter. These come from disk.
  ticket_path = Path(CLAUDE_PROJECT_DIR) / "vault" / "tickets" / f"{ticket_id}.md"
  if not ticket_path.exists():
    raise RuntimeError(f"mc-ticket-status reported {ticket_id} ready but {ticket_path} missing")
  ticket_content = ticket_path.read_text()
  ticket_fm, ticket_body = parse_frontmatter(ticket_content)

  # Step 3: Signal pickup
  emit_signal(f"vault/agents/logs/{ticket_id}-execute-pickup.md")

  # Step 4: Dispatch worker with full ticket context from disk
  worker_status = dispatch_worker(build_worker_prompt(ticket_id, ticket_fm, ticket_body))

  # Step 5: Handle worker result
  if worker_status == "DONE":
    bash(f"cd $CLAUDE_PROJECT_DIR && mc-proof-of-work {ticket_id}")
    invoke_verify(ticket_id)  # gigo:verify in mc-mode
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-complete.md")
  elif worker_status in ["BLOCKED", "NEEDS_CONTEXT"]:
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-blocked.md", body=worker_report)
    # Surface to operator; operator decides ticket state
  elif worker_status == "DONE_WITH_CONCERNS":
    bash(f"cd $CLAUDE_PROJECT_DIR && mc-proof-of-work {ticket_id}")
    invoke_verify(ticket_id)
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-complete.md", concerns=worker_concerns)
```

All `bash()` invocations specify `cd $CLAUDE_PROJECT_DIR` because `mc-ticket-status` / `mc-ticket-ls` / `mc-proof-of-work` all use mc's `find_vault()` helper which walks upward from cwd.

## Worker Prompt Contents

Worker prompt MUST include (self-contained — worker does not read files the prompt doesn't hand them):
- `Ticket:` (id + title from `ticket_fm`)
- `Summary`, `Context`, `Implementation Notes`, `Acceptance Tests` sections from `ticket_body`
- `Exit criteria:` from `ticket_fm["exit_criteria"]`
- `Produced files:` from `ticket_fm["produced_files"]`
- Instruction: *"Your unit of work is ticket {id}. The ticket body is above. Output goes to the files in `produced_files`. Report DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT."*

## Auto-Changelog in Mc-Mode

Per R4.9: generate per-ticket changelog entries AND a final summary entry. Read `vault/tickets/` to find what was completed since execution started (filter tickets where `status: done` AND completion signal timestamp falls within this run).

## Non-Mutation Rule (Authority Principle)

Execute NEVER writes to `vault/tickets/*.md` frontmatter. All state changes propagate via:
- Signal files at `vault/agents/logs/{ticket-id}-execute-{pickup|complete|blocked}.md`
- Verify verdicts at `vault/agents/reviewer/{ticket-id}*.md` (written by `gigo:verify` in mc-mode)

Operator (or future mc automation) transitions ticket state by running `mc-ticket-transition` directly. This is load-bearing for the authority principle — violating it repeats v0.12's tight-coupling failure.
