# Ticket Generation

Procedure for converting approved plan tasks into vault tickets.
Referenced by `SKILL.md` Phase 10.5 when `vault/_schema/ticket.md` exists.

## Conversion Procedure

For each task in the approved plan:

### 1. ID Generation

Format: `TCK-{phase_number}-{sequence}`. Pad sequence to 3 digits.
- Plan has phases: use phase number. `Phase 1, Task 3` → `TCK-1-003`.
- Plan has no phases: use `TCK-0-{N}`. `Task 5` → `TCK-0-005`.

### 2. Dependency Mapping

- `blocked-by: [task numbers]` → `depends_on: [TCK-{phase}-{sequence} for each]`
- `blocks:` is discarded. `depends_on` is the canonical direction.
- `parallelizable: true` needs no special mapping.

### 3. Field Population

| Plan field | Ticket field |
|---|---|
| Task title | `title` |
| Phase heading (or "default") | `phase` |
| "Done when:" / exit criteria | `exit_criteria` |
| "Files: Create:" + "Files: Modify:" | `produced_files` |
| Domain schema from `vault/_schema/proof-of-work.md` | `proof_of_work` |
| (default) | `assignee: local_model` |
| (always) | `status: ready` |
| Domain terms from task content | `skill_hints` |
| (default) | `permission_mode: acceptEdits` |

### 4. Body Generation

Map task content to ticket body sections:

| Task content | Ticket section |
|---|---|
| Task steps | Implementation Notes |
| "Run: ... Expected: ..." steps | Acceptance Tests |
| Exit criteria | Closure Proof-of-Work |
| (empty unless task specifies) | Out of Scope, Judgment Calls |
| (always empty) | Notes from Prior Attempts |

### 5. Write Ticket

Save to `vault/tickets/{id}.md`. Filename matches the ticket ID: `vault/tickets/TCK-1-003.md`.

## DAG Validation

After generating all tickets:

1. Build adjacency list from all `depends_on` fields.
2. **Orphan check:** every ticket ID referenced in any `depends_on` must exist as a generated ticket. Flag missing: `ERROR: TCK-{id} references non-existent dependency TCK-{missing}`.
3. **Cycle check:** run topological sort on the DAG. If a cycle is detected: `ERROR: Dependency cycle detected: TCK-A → TCK-B → ... → TCK-A`.
4. If validation fails, do NOT write tickets to disk. Report errors and ask the operator to fix the plan's dependency graph.

## Summary Output

After successful generation, print:

```
Tickets generated: N
  Ready: M (no unmet dependencies)
  Blocked: K (waiting on dependencies)
Vault location: vault/tickets/
DAG: valid (no cycles, no orphaned refs)
```
