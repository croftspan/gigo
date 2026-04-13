# Ticket Schema

Ticket frontmatter schema and domain-aware proof-of-work configuration.
Referenced by `orchestrator-scaffold.md` (R3) to generate `vault/_schema/ticket.md`,
`vault/_schema/proof-of-work.md`, and `vault/tickets/TEMPLATE.md`.

## Frontmatter Schema

```yaml
---
type: ticket
id: TCK-0-000                        # format: TCK-{phase_number}-{zero_padded_sequence}
title: "..."
phase: "..."                         # name of the phase this ticket belongs to
depends_on: []                       # array of ticket IDs this ticket is blocked by
assignee: local_model                # enum: local_model | claude_code | human
status: ready                        # enum: ready | in_progress | done | failed | escalated

skill_hints: []                      # domain-specific keywords for prompt construction
                                     # examples: [activerecord, migration, postgresql]
                                     #           [react, component, state-management]
                                     #           [luau, module-script, server-authoritative]
permission_mode: acceptEdits         # Claude Code permission mode for escalation

exit_criteria:                       # concrete, testable criteria (from plan task)
  - "Criterion 1"

produced_files: []                   # file paths (pre-populated from plan, updated on completion)
model_history: []                    # array of {model, timestamp, result, session_id?}

proof_of_work:
  required: []                       # from domain schema (see Domain-Aware Proof-of-Work)
  conditional: []                    # from domain schema
  produced:                          # artifact paths (filled by proof-of-work skill)
    test_output: null
    lint_output: null
    reviewer_verdict: null
---
```

### Status Transitions

```
ready → in_progress → done
                    → failed
                    → escalated → in_progress → done | failed
```

Only `done` requires all `proof_of_work.required` fields to be non-null.
`failed` is terminal for the current dispatch cycle.
`escalated` re-enters `in_progress` when Claude Code takes over.

## Domain-Aware Proof-of-Work

The scaffold reference reads the detected domain (R3.1) and maps to proof-of-work configuration:

| Domain | `required` | `conditional` | test_command | lint_command |
|---|---|---|---|---|
| `software` | `[test_output, lint_output, reviewer_verdict]` | `[]` | detected framework | detected linter |
| `game-roblox` | `[test_output, lint_output, reviewer_verdict]` | `[{name: studio_playtest_note, required_when: "studio_verification_required == true"}]` | `lune run tests/` or `rojo test` | `selene src/` |
| `game-other` | `[test_output, lint_output, reviewer_verdict]` | `[]` | detected or `null` | detected or `null` |
| `writing` | `[reviewer_verdict]` | `[{name: word_count, required_when: "true"}, {name: style_check, required_when: "true"}]` | n/a | n/a |
| `research` | `[reviewer_verdict]` | `[{name: citation_check, required_when: "true"}, {name: methodology_review, required_when: "true"}]` | n/a | n/a |
| `other` | `[reviewer_verdict]` | `[]` | `null` | `null` |

When test framework or linter detection returns `null`, the corresponding `required` entry
is still present but the command in `vault/_schema/proof-of-work.md` is set to
`"PLACEHOLDER — configure your test/lint command"`.

## Ticket Body Structure

Below the YAML frontmatter, every ticket body follows this section order:

1. **Summary** — one sentence describing the ticket's purpose
2. **Context** — links to design docs, system notes, inherited constraints
3. **Implementation Notes** — specific guidance, patterns to follow, function signatures
4. **Acceptance Tests** — concrete test cases with expected input/output
5. **Closure Proof-of-Work** — restatement of required artifacts from frontmatter
6. **Out of Scope** — what this ticket intentionally does not cover
7. **Judgment Calls** — explicit decision points where the worker has discretion
8. **Notes from Prior Attempts** — empty on first attempt; populated by retry/escalation
