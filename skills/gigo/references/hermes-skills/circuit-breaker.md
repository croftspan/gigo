---
name: circuit-breaker
description: "Monitors escalation rate and pauses dispatch when threshold is exceeded."
version: 1.0.0
metadata:
  hermes:
    tags: [monitoring, cost-protection, vault]
---

# Circuit Breaker

## Accept Input

Accept a ticket result: `{ticket_id, result: "passed"|"escalated"|"failed"}`.
Append the entry to the `window` array in `vault/agents/circuit-breaker/state.md`.
Include `timestamp` (ISO 8601) with each entry.

## State Initialization

If `vault/agents/circuit-breaker/state.md` does not exist, create it:
```yaml
paused: false
window: []
window_size: 10
threshold: 0.30
```

## Rate Trigger (Chronic)

1. Read `window` array from state file.
2. Count entries with `result: "escalated"` in the last N entries (N = `window_size`, default 10).
3. Calculate rate: `escalation_count / min(total_entries, N)`.
4. If rate >= `threshold` (default 0.30): trigger.

## Burst Trigger (Acute)

1. Check the last 3 entries in `window`.
2. If all 3 have `result: "escalated"` AND the time span between the first and last is under 5 minutes: trigger.
3. Burst catches model health issues (crashed server, context overflow) before the rate window fills.

## On Trigger

1. Write to `vault/agents/circuit-breaker/state.md`:
   ```yaml
   paused: true
   trigger_type: rate | burst
   trigger_time: "{ISO 8601}"
   escalation_count: N
   window_size: N
   rate: 0.XX
   ```
   Preserve existing `window` and `threshold` fields.
2. Append to `vault/agents/circuit-breaker/history.md`:
   ```
   ## {ISO 8601} — {trigger_type} trigger
   Escalation rate: {rate} ({escalation_count}/{window_size})
   Last 3 tickets: {ticket-ids and results}
   ```
3. Return to caller: `{triggered: true, trigger_type: "rate"|"burst", rate: 0.XX, escalation_count: N}`.

Do NOT call `send_message`. It is blocked for delegated children. The vault-dispatcher handles alerting.

## On Resume

When `/resume` command is received:
1. Set `paused: false` in state file.
2. Reset burst counter (clear last-3 escalation tracking).
3. Do NOT reset the rate window — chronic history is retained.
4. Append to history: `## {ISO 8601} — Resumed by operator`.

## No Trigger

If neither trigger fires, return: `{triggered: false}`.
