---
name: proof-of-work
description: "Validates proof-of-work artifacts exist before a ticket can be marked done."
version: 1.0.0
metadata:
  hermes:
    tags: [validation, quality-gate, vault]
---

# Proof-of-Work Validator

## Validation Procedure

1. Accept ticket ID as input.
2. Read `vault/tickets/{ticket-id}.md`. Parse `proof_of_work` from YAML frontmatter.
3. For each entry in `proof_of_work.required` (skip `reviewer_verdict` — the vault-dispatcher handles it after this skill returns):
   - `test_output`: read test command from `vault/_schema/proof-of-work.md`. Execute via `terminal`. Capture output to `vault/agents/model/{ticket-id}-test.log`. Exit code 0: set `proof_of_work.produced.test_output` to the log path. Non-zero: record failure with last 20 lines of output.
   - `lint_output`: read lint command from `vault/_schema/proof-of-work.md`. Execute via `terminal`. Capture output to `vault/agents/model/{ticket-id}-lint.log`. Exit code 0: set `proof_of_work.produced.lint_output` to the log path. Non-zero: record failure with last 20 lines.
4. For each entry in `proof_of_work.conditional`: evaluate the `required_when` condition against ticket frontmatter fields. If condition is true, validate the artifact the same way as required entries.
5. Write updated `proof_of_work.produced` to the ticket's YAML frontmatter.
6. Return result to caller:
   ```json
   {
     "pass": true,
     "missing": [],
     "failures": []
   }
   ```
   On failure:
   ```json
   {
     "pass": false,
     "missing": ["field_name"],
     "failures": [{"field": "test_output", "exit_code": 1, "last_20_lines": "..."}]
   }
   ```

## Constraints

- NEVER change ticket `status`. Only update `proof_of_work.produced` and return. The caller decides pass/retry/escalate.
- `reviewer_verdict` is excluded from checks. The dispatcher generates it after this skill returns `pass: true`. Checking it here would deadlock.
- Use Hermes `terminal` tool for command execution. `execute_command` does not exist. `execute_code` is blocked for delegated children.
