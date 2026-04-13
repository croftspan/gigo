# Orchestrator Scaffold — Spec

**Design brief:** `.claude/plans/enumerated-dreaming-pebble.md`

## Original Request

> Read briefs/09-orchestrator-loop.md — it has the full context including verified Hermes Agent docs. TL;DR: GIGO should scaffold the autonomous orchestrator infrastructure alongside the Claude context it already builds. The pattern is validated in ~/projects/cosmogene-roblox/discovery/ — read claude-code-unified-directive.md, TCK-0042-example-ticket.md, and patches/ for the proven architecture. Hermes Agent (v0.8.0, ~/projects/hermes/, github.com/NousResearch/hermes-agent) is the daemon runtime — it already has a built-in Claude Code skill, systemd gateway, Telegram/Discord adapters, and a skill system with SKILL.md frontmatter. The local model (Gemma, MiniMax, whatever) is the brain for Hermes, driving Claude Code as a headless escalation tool via claude -p. GIGO scaffolds: vault structure, ticket schema with proof-of-work gates, Hermes config (custom provider → llama-server), three custom Hermes skills (vault-dispatcher, proof-of-work validator, circuit-breaker), and runbooks. Briefs 06-08 are shipped and provide the execution primitives (harness, routing, formatting). The brief proposes 4-phase decomposition — vault+schema, custom skills, single-ticket loop, full daemon. Key constraint: Hermes requires 64K minimum context and --jinja flag on llama-server.

## Problem

GIGO builds the Claude-optimized context (personas, rules, references) and Briefs 06-08 added local model primitives (harness generation, model routing, prompt formatting). But the actual execution loop — reading a work queue, dispatching to a local model, validating results, escalating failures — remains manual. The operator must drive every cycle: `/blueprint` → `/spec` → `/execute` → `/verify`.

The CosmoGene architecture validated that a Hermes Agent daemon can run this autonomously: local model as the dispatcher brain, Claude Code as subscription-governed escalation via `claude -p`, quality enforced structurally through proof-of-work artifacts, cost protected by a circuit breaker. GIGO should scaffold this infrastructure during first assembly so any project can opt into autonomous execution.

## Requirements

### R1: Flag Detection

Add `--include-orchestrator` to `skills/gigo/SKILL.md` frontmatter `argument-hint`. Current value is `"[--include-gemma]"`, new value is `"[--include-gemma] [--include-orchestrator]"`. When `$ARGUMENTS` contains `--include-orchestrator`, the skill activates vault scaffolding after the standard assembly completes. Follows the same pattern as `--include-gemma` at Step 6.75.

### R2: Hub Insertion in gigo:gigo SKILL.md

Three additions to `skills/gigo/SKILL.md`:

1. **Orchestrator Flag paragraph** after the Gemma Harness Flag section (~line 27). ~5 lines explaining that `--include-orchestrator` activates Step 6.8 and pointing to `references/orchestrator-scaffold.md`.

2. **New Step 6.8** between Step 6.75 (Generate Gemma Harness) and Step 7 (The Handoff). ~10 lines: reads the scaffold reference, runs detection (domain, test framework, linter, model), writes vault directory structure and all generated files. Mechanical — no additional operator approval needed (assembly is already approved).

3. **Handoff mention** in Step 7's output. One line noting: `Orchestrator vault scaffolded at vault/. See vault/runbooks/daemon-setup.md to install and start the Hermes daemon.`

Total addition: ~18 lines. SKILL.md currently at ~325 lines, stays within 500-line cap.

### R3: Orchestrator Scaffold Reference

New file: `skills/gigo/references/orchestrator-scaffold.md` (~200 lines).

Contains the complete vault scaffolding algorithm that Step 6.8 reads at runtime. This is the master procedure — all other reference files are templates it reads and instantiates.

#### R3.1: Detection Procedure

Before generating files, detect four things:

1. **Project domain:** Infer from the just-completed team assembly. Map to domain category: `software`, `game-roblox`, `game-other`, `writing`, `research`, `other`. This determines proof-of-work field types.

2. **Test framework:** Scan project files for framework markers:
   - `pytest.ini`, `conftest.py`, `tests/` with `.py` → `pytest`
   - `jest.config.*`, `__tests__/`, `*.test.ts` → `jest`
   - `spec/`, `.rspec`, `Gemfile` with `rspec` → `rspec`
   - `*.spec.luau`, `TestEZ` references → `testez`
   - None found → `null` (placeholder with instructions in proof-of-work schema)

3. **Linter:** Scan for linter config:
   - `.eslintrc*`, `eslint.config.*` → `eslint`
   - `.rubocop.yml` → `rubocop`
   - `selene.toml` → `selene`
   - `.flake8`, `pyproject.toml` with `[tool.ruff]` → `ruff`
   - None found → `null`

4. **Local model:** `GET http://localhost:8080/v1/models`. On success, extract `data[0].id` as the model name. On failure (connection refused, timeout), write placeholder config with setup instructions. Same detection as Brief 07 (`skills/execute/references/local-model-routing.md` line 8).

#### R3.2: Vault Directory Structure

Generate this structure in the target project root:

```
vault/
├── _schema/
│   ├── ticket.md
│   └── proof-of-work.md
├── _governance/
│   └── PROJECT_RULES.md
├── _orchestration/
│   ├── hermes-config.yaml
│   ├── dispatch-rules.md
│   ├── escalation-protocol.md
│   └── llama-server.md
├── tickets/
│   └── TEMPLATE.md
├── skills/
│   ├── vault-dispatcher/
│   │   └── SKILL.md
│   ├── proof-of-work/
│   │   └── SKILL.md
│   └── circuit-breaker/
│       └── SKILL.md
├── agents/
│   ├── model/
│   ├── claude-code/
│   └── circuit-breaker/
└── runbooks/
    ├── daemon-setup.md
    ├── model-setup.md
    └── operations.md
```

All `agents/` subdirectories are created empty (populated during execution).

#### R3.3: Governance Extraction

`vault/_governance/PROJECT_RULES.md` is derived from `.claude/rules/standards.md`:

1. Read `standards.md`
2. Extract all bullets from `## Quality Gates` as imperative rules
3. Extract all bullets from `## Anti-Patterns`, invert to positive imperatives (same transformation as R3.2 in the Gemma harness generator spec)
4. Extract all bullets from `## Forbidden` verbatim
5. Write as a flat rule list with project name header

The governance file uses imperative voice exclusively (same convention as the Gemma harness — R3.4 from that spec).

#### R3.4: Orchestration Files

Four files in `vault/_orchestration/`:

**hermes-config.yaml:** Generated from R3.1 detection results using Hermes's actual config schema (from `~/projects/hermes/hermes_cli/config.py` DEFAULT_CONFIG). Template:

```yaml
# Generated by GIGO --include-orchestrator
# Copy to ~/.hermes/config.yaml or merge with existing
# hermes_version: 0.8.0

model: "{detected_model_id or 'PLACEHOLDER — run llama-server then re-run assembly'}"

providers:
  local:
    base_url: "http://localhost:8080/v1"
    api_key: ""

agent:
  max_turns: 90
  gateway_timeout: 1800
  tool_use_enforcement: true

terminal:
  backend: local
```

If model detection failed, `model:` is set to the placeholder string. The runbook explains how to update it.

**dispatch-rules.md:** Specifies the vault-dispatcher's operating rules — ticket selection criteria, parallelism limits (max 3 concurrent via Hermes `delegate_task()`), file overlap serialization rule, retry budget (1 retry per ticket), escalation trigger (2 consecutive failures).

**escalation-protocol.md:** Specifies the Claude Code invocation pattern:

```
claude -p "{ticket context + prior attempt + error output}" \
  --permission-mode acceptEdits \
  --output-format json \
  --max-turns 25 \
  --allowedTools "Read,Edit,Write,Bash"
```

Includes: JSON output parsing for file changes and session ID, change application procedure, proof-of-work re-check after escalation, logging to `vault/agents/claude-code/{ticket-id}/`.

**llama-server.md:** Server startup command using detected model path:

```bash
llama-server \
  -m ~/models/{model-file}.gguf \
  --host 0.0.0.0 --port 8080 \
  -c 65536 -np 1 -ngl 99 \
  --flash-attn on --jinja
```

Notes: `--jinja` is required for Hermes tool calling. Minimum 64K context (`-c 65536`) is required by Hermes. If model detection succeeded, uses actual model path; otherwise placeholder.

#### R3.5: Runbook Generation

Three runbooks in `vault/runbooks/`:

**daemon-setup.md:**
1. Install Hermes: `pip install hermes-agent`
2. Copy config: `cp vault/_orchestration/hermes-config.yaml ~/.hermes/config.yaml`
3. Run Hermes setup wizard: `hermes setup` (interactive — configures gateway platform)
4. Install custom skills: `cp -r vault/skills/* ~/.hermes/skills/`
5. Start daemon: `hermes gateway install` (creates systemd/launchd service) or `hermes gateway run` (foreground)

**model-setup.md:** Contents of `llama-server.md` plus model download instructions (placeholder URL).

**operations.md:** Documents operator commands via the Hermes gateway:
- `/status` — current ticket, escalation rate, circuit breaker state
- `/pause` — stop dispatching new tickets
- `/resume` — restart after pause or circuit breaker trigger
- `/tickets` — list ready/in_progress/done/failed counts

#### R3.6: Template Ticket

`vault/tickets/TEMPLATE.md` — an empty ticket with the full schema from R4, all fields populated with placeholder values and field-level comments explaining each field. Not a real ticket — a template the operator or `gigo:spec` Phase 10.5 copies when creating tickets.

### R4: Ticket Schema Reference

New file: `skills/gigo/references/ticket-schema.md` (~80 lines).

Contains the ticket frontmatter schema and domain-aware proof-of-work configuration. The scaffold reference (R3) reads this to generate `vault/_schema/ticket.md`, `vault/_schema/proof-of-work.md`, and `vault/tickets/TEMPLATE.md`.

#### R4.1: Frontmatter Schema

```yaml
type: ticket
id: TCK-XXXX                        # format: TCK-{phase_number}-{sequence}
title: "..."
phase: "..."                         # name of the phase this ticket belongs to
depends_on: []                       # array of ticket IDs this ticket is blocked by
assignee: local_model                # enum: local_model | claude_code | human
status: ready                        # enum: ready | in_progress | done | failed | escalated

skill_hints: []                      # domain-specific keywords for prompt construction
permission_mode: acceptEdits         # Claude Code permission mode for escalation

exit_criteria:                       # concrete, testable criteria (from plan task)
  - "Criterion 1"

produced_files: []                   # file paths created/modified (filled on completion)
model_history: []                    # array of {model, timestamp, result, session_id?}

proof_of_work:
  required: []                       # from domain schema (R4.2)
  conditional: []                    # from domain schema (R4.2)
  produced:                          # artifact paths (filled by proof-of-work skill)
    test_output: null
    lint_output: null
    reviewer_verdict: null
```

**Status transitions:** `ready` → `in_progress` → `done` | `failed` | `escalated`. Only `done` requires all `proof_of_work.required` fields to be non-null. `escalated` transitions to `in_progress` when Claude Code takes over.

#### R4.2: Domain-Aware Proof-of-Work

The scaffold reference reads R3.1 domain detection and maps to proof-of-work configuration:

| Domain | `required` array | `conditional` array | test_command | lint_command |
|---|---|---|---|---|
| `software` | `[test_output, lint_output, reviewer_verdict]` | `[]` | `{R3.1 detected test framework} {standard run command}` | `{R3.1 detected linter} {standard run command}` |
| `game-roblox` | `[test_output, lint_output, reviewer_verdict]` | `[{name: studio_playtest_note, required_when: "studio_verification_required == true"}]` | `lune run tests/` or `rojo test` | `selene src/` |
| `game-other` | `[test_output, lint_output, reviewer_verdict]` | `[]` | detected or `null` | detected or `null` |
| `writing` | `[reviewer_verdict]` | `[{name: word_count, required_when: "true"}, {name: style_check, required_when: "true"}]` | n/a | n/a |
| `research` | `[reviewer_verdict]` | `[{name: citation_check, required_when: "true"}, {name: methodology_review, required_when: "true"}]` | n/a | n/a |
| `other` | `[reviewer_verdict]` | `[]` | `null` | `null` |

When test framework or linter detection returns `null`, the corresponding `required` entry is still present but the test/lint command in `vault/_schema/proof-of-work.md` is set to `"PLACEHOLDER — configure your test/lint command"`.

#### R4.3: Ticket Body Structure

Below the frontmatter, every ticket body follows this section order:

1. **Summary** — one sentence
2. **Context** — links to design docs, system notes, inherited constraints
3. **Implementation Notes** — specific guidance, patterns to follow, function signatures
4. **Acceptance Tests** — concrete test cases with expected input/output
5. **Closure Proof-of-Work** — restatement of required artifacts
6. **Out of Scope** — what this ticket intentionally does not cover (forward links to future tickets)
7. **Judgment Calls** — explicit decision points where the worker has discretion
8. **Notes from Prior Attempts** — empty on first attempt; populated by retry/escalation

### R5: Vault-Dispatcher Skill Template

New file: `skills/gigo/references/hermes-skills/vault-dispatcher.md` (~80 lines).

Contains the complete SKILL.md that gets written to `vault/skills/vault-dispatcher/SKILL.md` in the target project. This is a Hermes-compatible skill prompt, not a GIGO skill.

#### R5.1: Frontmatter

```yaml
---
name: vault-dispatcher
description: "Reads vault tickets, builds dependency graph, dispatches ready tickets to the model for execution."
version: 1.0.0
metadata:
  hermes:
    tags: [orchestration, dispatch, vault]
---
```

#### R5.2: State Machine

The skill body is a 10-step state machine written in mechanical, imperative language. Each step must be unambiguous — the local model (Gemma, MiniMax, etc.) executes these steps via Hermes tool use.

1. Read all `.md` files in `vault/tickets/`. Parse YAML frontmatter from each.
2. Build dependency DAG: for each ticket, map `depends_on` to ticket IDs.
3. Select next ticket: `status == "ready"` AND every ticket in `depends_on` has `status == "done"`. If multiple qualify, pick the one with the lowest sequence number in its ID.
4. Update selected ticket: set `status: in_progress`. Append to `model_history`: `{model: "{model_id}", timestamp: "{ISO 8601}", result: "started"}`.
5. Construct prompt:
   - System message: read `.claude/references/gemma-harness.md`, extract content after `---` divider
   - User message: ticket body (Summary through Notes from Prior Attempts) + inlined source files from the project (selected by `skill_hints` and `produced_files` fields)
6. Send prompt to the model (Hermes handles the API call via the configured provider).
7. Parse response: extract code blocks. Each code block with a file path header (`// filepath: path/to/file.ext` or `# filepath: path/to/file.ext`) maps to a file write.
8. Apply changes: write each extracted code block to the corresponding file path using Hermes `write_file` tool.
9. Run proof-of-work: read `vault/_schema/proof-of-work.md` for test and lint commands. Execute test command, capture output to `vault/agents/model/{ticket-id}-test.log`. Execute lint command, capture output to `vault/agents/model/{ticket-id}-lint.log`. Update ticket `proof_of_work.produced` fields with log paths.
10. Route on results:
    - All required proof-of-work artifacts exist and commands returned exit code 0: set `status: done`, update `model_history` with `result: "passed"`, proceed to step 1.
    - Any proof-of-work failed: retry ONCE — append error output to the user message, re-send to model (steps 6-9). If retry also fails: set `status: escalated`, update `model_history` with `result: "escalated"`, read `vault/_orchestration/escalation-protocol.md`, invoke Hermes's built-in `claude-code` skill with the escalation prompt.
    - After Claude Code escalation: re-run proof-of-work (step 9). If pass: set `status: done` with `model: "claude-code"` in history. If fail: set `status: failed`, log to `vault/agents/claude-code/{ticket-id}/`, proceed to step 1.

**After each ticket (pass or fail):** check circuit breaker state by reading `vault/agents/circuit-breaker/state.md`. If `paused: true`, stop dispatching and wait for `/resume` command. Otherwise, invoke the circuit-breaker skill to update statistics.

#### R5.3: Parallelism

After step 3, if multiple tickets qualify (independent — no shared `depends_on` paths), dispatch up to 3 in parallel using Hermes `delegate_task()`. Each parallel dispatch gets its own isolated context (Hermes enforces this — `MAX_CONCURRENT_CHILDREN = 3`, `MAX_DEPTH = 2`).

**File overlap guard:** Before dispatching parallel tickets, check if their `produced_files` arrays overlap. Overlapping tickets are serialized — only one dispatches; the other stays `ready` for the next cycle.

#### R5.4: Budget Discipline

The complete skill prompt (frontmatter + body) must stay under 100 lines. The local model processes this entire prompt plus the ticket content plus source files within its context window. Every line in the skill prompt is a line not available for the ticket. Use imperative, mechanical language — no explanations, no rationale, no "you should consider."

### R6: Proof-of-Work Skill Template

New file: `skills/gigo/references/hermes-skills/proof-of-work.md` (~50 lines).

Contains the complete SKILL.md for `vault/skills/proof-of-work/SKILL.md`.

#### R6.1: Frontmatter

```yaml
---
name: proof-of-work
description: "Validates proof-of-work artifacts exist before a ticket can be marked done."
version: 1.0.0
metadata:
  hermes:
    tags: [validation, quality-gate, vault]
---
```

#### R6.2: Validation Logic

1. Accept ticket ID as input.
2. Read `vault/tickets/{ticket-id}.md`, parse `proof_of_work` from frontmatter.
3. For each entry in `proof_of_work.required`:
   - `test_output`: read test command from `vault/_schema/proof-of-work.md`. Run command via Hermes `execute_command` tool. Capture output to `vault/agents/model/{ticket-id}-test.log`. If exit code 0, set `proof_of_work.produced.test_output` to the log path. If non-zero, report failure with the last 20 lines of output.
   - `lint_output`: same pattern with lint command. Log to `{ticket-id}-lint.log`.
   - `reviewer_verdict`: check if file exists at `vault/agents/reviewer/{ticket-id}.md`. If exists, set `proof_of_work.produced.reviewer_verdict` to the file path. If not, report missing. (For autonomous execution, the vault-dispatcher generates this after a successful review subagent run.)
4. For each entry in `proof_of_work.conditional`: evaluate the `required_when` condition against ticket frontmatter fields. If true, validate the same way as required entries.
5. Write updated `proof_of_work.produced` to the ticket's frontmatter.
6. Return: `{pass: true/false, missing: [list of field names], failures: [list of {field, exit_code, last_20_lines}]}`.

#### R6.3: No Side Effects Beyond Logging

The proof-of-work skill NEVER changes ticket `status`. It only updates `proof_of_work.produced` and returns a result. The caller (vault-dispatcher) decides what to do with the result (mark done, retry, or escalate).

### R7: Circuit-Breaker Skill Template

New file: `skills/gigo/references/hermes-skills/circuit-breaker.md` (~60 lines).

Contains the complete SKILL.md for `vault/skills/circuit-breaker/SKILL.md`.

#### R7.1: Frontmatter

```yaml
---
name: circuit-breaker
description: "Monitors escalation rate and pauses dispatch when threshold is exceeded."
version: 1.0.0
metadata:
  hermes:
    tags: [monitoring, cost-protection, vault]
---
```

#### R7.2: Dual-Trigger Logic

Two independent triggers, either can pause dispatch:

**Rate trigger (chronic):**
1. Read `vault/agents/circuit-breaker/state.md`. Parse `window` array (list of recent ticket results).
2. Count escalations in the last N entries (default N=10, configurable in state file).
3. Calculate rate: `escalation_count / min(total_attempted, N)`.
4. If rate >= threshold (default 0.30): trigger.

**Burst trigger (acute):**
1. Read `window` array. Check the last 3 entries.
2. If all 3 are escalations AND the time span between first and last is under 5 minutes: trigger.
3. This catches model health issues (crashed server, corrupted weights, context overflow) that the rate trigger would miss because the window hasn't filled yet.

#### R7.3: On Trigger

1. Write to `vault/agents/circuit-breaker/state.md`:
   ```yaml
   paused: true
   trigger_type: rate | burst
   trigger_time: "{ISO 8601}"
   escalation_count: N
   window_size: N
   rate: 0.XX
   ```
2. Append to `vault/agents/circuit-breaker/history.md`:
   ```
   ## {ISO 8601} — {trigger_type} trigger
   Escalation rate: {rate} ({escalation_count}/{window_size})
   Last 3 tickets: {ticket-ids and results}
   ```
3. Send alert via Hermes `send_message` tool to the configured gateway platform:
   ```
   ⚠️ Circuit breaker triggered ({trigger_type}).
   Escalation rate: {rate}. Dispatch paused.
   Send /resume to restart.
   ```

#### R7.4: On Resume

When `/resume` command received via gateway:
1. Set `paused: false` in state file.
2. Reset burst counter (clear last-3 escalation tracking).
3. Do NOT reset the rate window — the chronic trigger retains history.
4. Append to history: `## {ISO 8601} — Resumed by operator`.

#### R7.5: State Initialization

On first run (state file doesn't exist), create `vault/agents/circuit-breaker/state.md`:
```yaml
paused: false
window: []
window_size: 10
threshold: 0.30
```

### R8: Ticket Generation Reference

New file: `skills/spec/references/ticket-generation.md` (~60 lines).

Contains the procedure for converting approved plan tasks into vault tickets. Read by `gigo:spec` Phase 10.5.

#### R8.1: Conversion Procedure

For each task in the approved plan:

1. **ID generation:** `TCK-{plan_phase_number}-{task_sequence_number}`. If no phases, use `TCK-0-{N}`. Pad sequence to 3 digits: `TCK-1-001`, `TCK-1-002`, `TCK-2-001`.

2. **Dependency mapping:**
   - Plan field `blocked-by: [task numbers]` → ticket field `depends_on: [TCK-{phase}-{sequence} for each blocking task]`
   - Plan field `blocks:` is not transferred — `depends_on` is the canonical direction.
   - Plan field `parallelizable: true` means the ticket has no dependency on other parallel tickets — no special mapping needed.

3. **Field population:**
   - `title`: from task title
   - `phase`: from plan phase heading (or "default" if no phases)
   - `exit_criteria`: from task "Done when:" line or step verification criteria
   - `produced_files`: from task "Files: Create:" and "Files: Modify:" entries
   - `proof_of_work`: copy from `vault/_schema/proof-of-work.md` (domain-detected during assembly)
   - `assignee`: `local_model` (default)
   - `status`: `ready` if all `depends_on` tickets exist with `status: done`; otherwise `ready` (the dispatcher handles dependency checking at runtime)
   - `skill_hints`: extracted from task content — key domain terms, framework names, pattern names
   - `permission_mode`: `acceptEdits` (default)

4. **Body generation:** Map task steps to the ticket body structure (R4.3):
   - Steps → Implementation Notes
   - "Run: ... Expected: ..." steps → Acceptance Tests
   - Task exit criteria → Exit Criteria (frontmatter) + Closure Proof-of-Work (body)
   - No Out of Scope or Judgment Calls unless task specifies them
   - Notes from Prior Attempts starts empty

5. **Write ticket:** Save to `vault/tickets/TCK-{phase}-{sequence}.md`.

#### R8.2: DAG Validation

After generating all tickets:

1. Build adjacency list from all `depends_on` fields.
2. Check for orphaned references: every ticket ID in any `depends_on` must exist as a generated ticket. Flag any missing with: `"ERROR: TCK-{id} references non-existent dependency TCK-{missing-id}"`.
3. Check for cycles: run topological sort on the DAG. If a cycle is detected, flag: `"ERROR: Dependency cycle detected: TCK-A → TCK-B → ... → TCK-A"`.
4. Report: `Generated N tickets. DAG valid: {yes/no}. {error details if any}`.

If DAG validation fails, do NOT write tickets. Report errors and ask the operator to fix the plan's dependency graph.

#### R8.3: Summary Output

After successful generation, print:

```
Tickets generated: N
  Ready: M (no unmet dependencies)
  Blocked: K (waiting on dependencies)
Vault location: vault/tickets/
DAG: valid (no cycles, no orphaned refs)
```

### R9: gigo:spec Phase 10.5 Insertion

Add Phase 10.5 to `skills/spec/SKILL.md` between Phase 10 (Operator Reviews Plan) and the Handoff section.

~12 lines:

```markdown
## Phase 10.5: Generate Vault Tickets (Conditional)

If `vault/_schema/ticket.md` exists in the project (indicating orchestrator scaffold is present), convert the approved plan's tasks into vault tickets.

Read `references/ticket-generation.md` for the full conversion procedure. This is a mechanical translation — no new decisions, no operator approval needed.

If the vault schema doesn't exist, skip this phase entirely. The standard /execute path proceeds as normal.

After generation, include the ticket summary in the handoff message.
```

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| scaffold | R3: Orchestrator Scaffold Reference | ✅ |
| detect (model) | R3.1: Detection Procedure | ✅ |
| generate (schema) | R4: Ticket Schema Reference | ✅ |
| generate (config) | R3.4: Orchestration Files | ✅ |
| generate (rules) | R3.3: Governance Extraction | ✅ |
| generate (runbooks) | R3.5: Runbook Generation | ✅ |
| decompose (plans → tickets) | R8: Ticket Generation Reference | ✅ |
| dispatch | R5: Vault-Dispatcher Skill Template | ✅ |
| validate (proof-of-work) | R6: Proof-of-Work Skill Template | ✅ |
| escalate | R5.2 step 10: Escalation path | ✅ |
| track (escalation rate) | R7: Circuit-Breaker Skill Template | ✅ |
| alert | R7.3: On Trigger | ✅ |

## Conventions

### YAML Frontmatter in Tickets

All YAML values use explicit quoting for strings. Arrays use bracket notation for inline (`depends_on: [TCK-1-001, TCK-1-002]`) or indented list notation for multi-line. Status and assignee values are unquoted enums. Null values are written as `null`, not empty strings.

### Hermes SKILL.md Format

Hermes skill files use YAML frontmatter with these fields: `name` (kebab-case), `description` (one-liner), `version` (semver), `metadata.hermes.tags` (array). The body is a prompt — imperative, mechanical language. No rationale, no "consider." Total prompt under 100 lines for local model skills.

### Ticket ID Format

`TCK-{phase}-{sequence}` where phase is a 1-2 digit number and sequence is zero-padded to 3 digits. Examples: `TCK-1-001`, `TCK-2-015`, `TCK-0-003` (no-phase plans). The ID is unique within a vault.

### Status Transitions

```
ready → in_progress → done
                    → failed
                    → escalated → in_progress → done | failed
```

Only `done` requires all `proof_of_work.required` to be non-null. `failed` is terminal for the current dispatch cycle. `escalated` re-enters `in_progress` when Claude Code takes over.

### Imperative Voice in Generated Skills

All three Hermes skill prompts use imperative voice exclusively. Same convention as the Gemma harness (spec 2026-04-12, R3.4). "Read the file" not "you should read the file." "Set status to done" not "consider setting the status."

### Vault vs .claude/ Boundary

`.claude/` is Claude Code's contract (rules auto-load, references on-demand, governed by The Snap). `vault/` is the orchestrator's contract (tickets, dispatch config, agent logs, governed by Hermes). They are parallel directories at the project root. GIGO writes both during assembly but they serve different runtimes.

`vault/_governance/PROJECT_RULES.md` is extracted FROM `.claude/rules/standards.md`, not linked to it. It drifts over time — this is accepted and handled by gigo:snap's vault governance staleness check.

## Boundaries

| Boundary | From | To | Integration Point |
|---|---|---|---|
| Assembly → Vault | gigo:gigo Step 6.8 | vault/ directory | R3: scaffold reference generates all vault files |
| Claude Rules → Vault Governance | `.claude/rules/standards.md` | `vault/_governance/PROJECT_RULES.md` | R3.3: one-time extraction during assembly |
| Plan Tasks → Vault Tickets | gigo:spec Phase 10.5 | `vault/tickets/*.md` | R8: mechanical translation with DAG validation |
| Vault Skills → Hermes | `vault/skills/` | `~/.hermes/skills/` | Manual copy by operator (documented in runbook) |
| Hermes → llama-server | Hermes custom provider | `http://localhost:8080/v1` | R3.4: hermes-config.yaml |
| Hermes → Claude Code | Built-in claude-code skill | `claude -p` headless | R5.2 step 10 / R3.4: escalation-protocol.md |

## Out of Scope

- **Running the Hermes daemon.** GIGO scaffolds infrastructure; Hermes is a separate runtime. The operator starts it via runbooks.
- **gigo:execute integration.** Execute handles Claude-native execution (subagents, worktrees). Hermes is a different execution path. No changes to execute.
- **Snap integration for vault governance staleness.** Deferred — only matters once vaults exist in the wild. Documented in design brief as future work.
- **CosmoGene-specific features.** Obsidian Bases/Dataview, wikilinks, Roblox-specific fields — the orchestrator scaffold generalizes the pattern.
- **Non-Hermes runtimes.** The vault/ticket/proof-of-work pattern is framework-agnostic, but this spec generates Hermes-specific config and skills.

## Risks

### Risk 1: Competing Dependency Graphs

Plan uses `blocks`/`blocked-by`/`parallelizable`. Tickets use `depends_on`/`status`. The translation in R8.1 maps `blocked-by` → `depends_on` and discards `blocks` (which is the inverse). R8.2 validates the resulting DAG with orphan detection and cycle checking.

### Risk 2: Prompt-as-Code Fragility

The three Hermes skills are prompts that a local model must follow correctly. State mutations (writing YAML frontmatter to ticket files) via natural language instructions are fragile. Mitigations: R5.4 enforces 100-line budget discipline; R5.2 uses explicit, step-numbered instructions with concrete YAML examples; R6.3 separates proof-of-work validation from status transitions so incorrect validation doesn't corrupt ticket state.

### Risk 3: Circuit Breaker Measures Rate Not Volume

30% threshold with 10-ticket window allows indefinite low-rate escalation. R7.2 addresses this with dual triggers: rate (chronic, 30% over window) and burst (acute, 3 consecutive in 5 minutes). A future volume cap (max N escalations per session) is documented in the design brief but out of scope for this spec.

### Risk 4: PROJECT_RULES Drift

`vault/_governance/PROJECT_RULES.md` is a one-time snapshot. As `.claude/rules/standards.md` evolves via gigo:snap and gigo:maintain, the vault copy drifts. Accepted trade-off — the alternative (symlink or runtime inclusion) would couple the two runtimes. Snap integration for staleness detection is deferred (Out of Scope).

### Risk 5: Hermes Version Drift

Generated skills target Hermes v0.8.0 skill format. R3.4 includes `hermes_version: 0.8.0` as a comment in hermes-config.yaml. gigo:maintain can detect version drift during health checks. If Hermes changes its skill format, the skill templates (R5, R6, R7) need updating — this is a manual maintenance task.
