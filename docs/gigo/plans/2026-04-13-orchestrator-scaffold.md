# Orchestrator Scaffold Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-13-orchestrator-scaffold-design.md`

**Goal:** Add `--include-orchestrator` flag to gigo:gigo and Phase 10.5 to gigo:spec, enabling GIGO to scaffold autonomous execution infrastructure (vault, tickets, Hermes config, skills, runbooks) during first assembly and convert approved plans to vault tickets.

**Execution Pattern:** Supervisor

**Architecture:** Six new reference files (templates and procedures) plus two SKILL.md modifications. The orchestrator scaffold reference (R3) is the master procedure that reads all other templates at runtime. Two independent integration paths: gigo:gigo Step 6.8 (vault scaffolding) and gigo:spec Phase 10.5 (ticket generation).

---

### Task 1: Ticket Schema Reference (R4)

**blocks:** 2, 3, 4, 5, 7
**blocked-by:** []
**parallelizable:** false

Foundation file — defines the ticket frontmatter schema and domain-aware proof-of-work configuration that all other files reference.

**Files:**
- Create: `skills/gigo/references/ticket-schema.md`

- [ ] **Step 1: Create ticket-schema.md**

Write `skills/gigo/references/ticket-schema.md` (~80 lines). Four sections:

**Section 1 — Header and purpose** (~5 lines):

```markdown
# Ticket Schema

Ticket frontmatter schema and domain-aware proof-of-work configuration.
Referenced by `orchestrator-scaffold.md` (R3) to generate `vault/_schema/ticket.md`,
`vault/_schema/proof-of-work.md`, and `vault/tickets/TEMPLATE.md`.
```

**Section 2 — Frontmatter Schema** (~30 lines):

The complete YAML frontmatter block from spec R4.1. Include every field with its inline comment:

```yaml
type: ticket
id: TCK-0-000                        # format: TCK-{phase_number}-{zero_padded_sequence}
title: "..."
phase: "..."                         # name of the phase this ticket belongs to
depends_on: []                       # array of ticket IDs this ticket is blocked by
assignee: local_model                # enum: local_model | claude_code | human
status: ready                        # enum: ready | in_progress | done | failed | escalated

skill_hints: []                      # domain-specific keywords for prompt construction
permission_mode: acceptEdits         # Claude Code permission mode for escalation

exit_criteria:                       # concrete, testable criteria (from plan task)
  - "Criterion 1"

produced_files: []                   # file paths (pre-populated from plan, updated on completion)
model_history: []                    # array of {model, timestamp, result, session_id?}

proof_of_work:
  required: []                       # from domain schema
  conditional: []                    # from domain schema
  produced:                          # artifact paths (filled by proof-of-work skill)
    test_output: null
    lint_output: null
    reviewer_verdict: null
```

Include the status transition diagram from spec R4.1:
```
ready → in_progress → done
                    → failed
                    → escalated → in_progress → done | failed
```

Note: Only `done` requires all `proof_of_work.required` to be non-null.

**Section 3 — Domain-Aware Proof-of-Work Table** (~25 lines):

The full domain mapping table from spec R4.2:

| Domain | `required` | `conditional` | test_command | lint_command |
|---|---|---|---|---|
| `software` | `[test_output, lint_output, reviewer_verdict]` | `[]` | detected framework | detected linter |
| `game-roblox` | `[test_output, lint_output, reviewer_verdict]` | `[studio_playtest_note]` | `lune run tests/` | `selene src/` |
| `game-other` | `[test_output, lint_output, reviewer_verdict]` | `[]` | detected or null | detected or null |
| `writing` | `[reviewer_verdict]` | `[word_count, style_check]` | n/a | n/a |
| `research` | `[reviewer_verdict]` | `[citation_check, methodology_review]` | n/a | n/a |
| `other` | `[reviewer_verdict]` | `[]` | null | null |

Include the placeholder rule: when detection returns null, set command to `"PLACEHOLDER — configure your test/lint command"`.

**Section 4 — Ticket Body Structure** (~15 lines):

The 8-section body order from spec R4.3: Summary, Context, Implementation Notes, Acceptance Tests, Closure Proof-of-Work, Out of Scope, Judgment Calls, Notes from Prior Attempts.

- [ ] **Step 2: Verify**

Confirm file exists, has ~80 lines, contains all three sections. Confirm the YAML schema block parses correctly. Confirm the domain table has all 6 domain rows.

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/ticket-schema.md
git commit -m "feat: add ticket schema reference for orchestrator scaffold (R4)"
```

---

### Task 2: Vault-Dispatcher Skill Template (R5)

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4)

**Files:**
- Create: `skills/gigo/references/hermes-skills/vault-dispatcher.md`

- [ ] **Step 1: Create directory and file**

Create `skills/gigo/references/hermes-skills/` directory. Write `vault-dispatcher.md` (~80 lines). This file IS the Hermes SKILL.md that gets copied to `vault/skills/vault-dispatcher/SKILL.md` in target projects. Must stay under 100 lines (R5.4 budget discipline).

**Frontmatter** (spec R5.1):

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

**Body — 10-step state machine** (spec R5.2):

Write each step as a numbered imperative instruction. Use mechanical, imperative voice — "Read all .md files in vault/tickets/. Parse YAML frontmatter." not "you should consider reading."

Steps 1-3: Read tickets, build DAG, select next (lowest sequence number breaks ties).

Step 4: Update ticket status to `in_progress`. Append to `model_history`. Validate YAML after write (see YAML Frontmatter Validation convention in spec).

Step 5: Construct prompt. System = `.claude/references/gemma-harness.md` (fallback: `vault/_governance/PROJECT_RULES.md` if harness doesn't exist). User = ticket body + inlined source files from `skill_hints` and `produced_files`.

Steps 6-8: Send to model, parse response (file path headers: `// filepath:` or `# filepath:`), apply via `write_file`.

Step 9: Run proof-of-work — read test/lint commands from `vault/_schema/proof-of-work.md`, execute, capture output to `vault/agents/model/{ticket-id}-test.log` and `{ticket-id}-lint.log`. Update `proof_of_work.produced`.

Step 10: Route on results:
- All pass → `status: done`, `result: "passed"`, generate reviewer verdict at `vault/agents/reviewer/{ticket-id}.md` (spec R6.4), next ticket.
- Fail → retry once with error context appended.
- Still fail → `status: escalated`, read `vault/_orchestration/escalation-protocol.md`, invoke claude-code skill.
- Claude Code pass → `status: done` with `model: "claude-code"`.
- Claude Code fail → `status: failed`, log, next ticket.

**After each ticket** — invoke circuit-breaker skill. If return value has `triggered: true`, send alert via `send_message` (dispatcher is top-level, has access):

```
⚠️ Circuit breaker triggered ({trigger_type}).
Escalation rate: {rate}. Dispatch paused.
Send /resume to restart.
```

Check `vault/agents/circuit-breaker/state.md` for `paused: true`. If paused, wait for `/resume`.

**Parallelism section** (~5 lines, spec R5.3): After step 3, if multiple tickets qualify (independent), dispatch up to 3 via `delegate_task()`. Check `produced_files` overlap — overlapping tickets serialize.

- [ ] **Step 2: Verify line count and voice**

Count lines. Must be under 100 (frontmatter + body). Verify imperative voice — no "you should", no "consider", no rationale text. Every sentence is an instruction.

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/hermes-skills/vault-dispatcher.md
git commit -m "feat: add vault-dispatcher Hermes skill template (R5)"
```

---

### Task 3: Proof-of-Work Skill Template (R6)

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 2, 4)

**Files:**
- Create: `skills/gigo/references/hermes-skills/proof-of-work.md`

- [ ] **Step 1: Create proof-of-work.md**

Write `skills/gigo/references/hermes-skills/proof-of-work.md` (~50 lines). This is the Hermes SKILL.md for `vault/skills/proof-of-work/SKILL.md`.

**Frontmatter** (spec R6.1):

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

**Body — Validation Logic** (spec R6.2):

6-step procedure:
1. Accept ticket ID as input.
2. Read `vault/tickets/{ticket-id}.md`, parse `proof_of_work` from frontmatter.
3. For each `required` entry:
   - `test_output`: read command from `vault/_schema/proof-of-work.md`. Run via `execute_command`. Capture to `vault/agents/model/{ticket-id}-test.log`. Exit 0 → set produced path. Non-zero → report failure with last 20 lines.
   - `lint_output`: same pattern, log to `{ticket-id}-lint.log`.
   - `reviewer_verdict`: check `vault/agents/reviewer/{ticket-id}.md` exists.
4. For each `conditional` entry: evaluate `required_when`, validate if true.
5. Write updated `proof_of_work.produced` to ticket frontmatter.
6. Return: `{pass: true/false, missing: [...], failures: [{field, exit_code, last_20_lines}]}`.

**Key constraint** (spec R6.3): This skill NEVER changes ticket `status`. Only updates `proof_of_work.produced` and returns a result. The caller (vault-dispatcher) decides pass/retry/escalate.

- [ ] **Step 2: Verify**

Under 100 lines. No status mutations in the body. Return value format matches what vault-dispatcher expects.

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/hermes-skills/proof-of-work.md
git commit -m "feat: add proof-of-work Hermes skill template (R6)"
```

---

### Task 4: Circuit-Breaker Skill Template (R7)

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 2, 3)

**Files:**
- Create: `skills/gigo/references/hermes-skills/circuit-breaker.md`

- [ ] **Step 1: Create circuit-breaker.md**

Write `skills/gigo/references/hermes-skills/circuit-breaker.md` (~60 lines). This is the Hermes SKILL.md for `vault/skills/circuit-breaker/SKILL.md`.

**Frontmatter** (spec R7.1):

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

**Body — Dual-Trigger Logic** (spec R7.2):

Two independent triggers:

**Rate trigger (chronic):**
1. Read `vault/agents/circuit-breaker/state.md`, parse `window` array.
2. Count escalations in last N entries (default N=10).
3. Rate = `escalation_count / min(total_attempted, N)`.
4. Rate >= 0.30 → trigger.

**Burst trigger (acute):**
1. Check last 3 entries in `window`.
2. All 3 are escalations AND time span < 5 minutes → trigger.

**On trigger** (spec R7.3):
1. Write state: `paused: true`, `trigger_type`, `trigger_time`, `escalation_count`, `window_size`, `rate`.
2. Append to `vault/agents/circuit-breaker/history.md`.
3. Return `{triggered: true, trigger_type: "rate"|"burst", rate: 0.XX, escalation_count: N}` to caller.

**Critical:** Do NOT call `send_message` — it's blocked for delegated children (`DELEGATE_BLOCKED_TOOLS`). The vault-dispatcher handles alerting.

**On resume** (spec R7.4):
1. Set `paused: false`.
2. Reset burst counter.
3. Do NOT reset rate window.
4. Append to history.

**State initialization** (spec R7.5):
On first run, create state file:
```yaml
paused: false
window: []
window_size: 10
threshold: 0.30
```

- [ ] **Step 2: Verify**

Under 100 lines. No `send_message` calls in the body. Returns result to caller. State file format matches what vault-dispatcher reads.

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/hermes-skills/circuit-breaker.md
git commit -m "feat: add circuit-breaker Hermes skill template (R7)"
```

---

### Task 5: Orchestrator Scaffold Reference (R3)

**blocks:** 6
**blocked-by:** 1, 2, 3, 4
**parallelizable:** false

The master procedure. Step 6.8 reads this at runtime to generate the entire vault directory structure. This is the largest file (~200 lines) and references all templates from Tasks 1-4.

**Files:**
- Create: `skills/gigo/references/orchestrator-scaffold.md`

- [ ] **Step 1: Create orchestrator-scaffold.md**

Write `skills/gigo/references/orchestrator-scaffold.md` (~200 lines). Follow the same structure as `references/gemma-harness-generator.md`: Input → Output → Algorithm.

**Header** (~5 lines):

```markdown
# Orchestrator Scaffold Generator

Algorithm for scaffolding autonomous execution infrastructure from a GIGO assembly.
Referenced by SKILL.md Step 6.8 when `--include-orchestrator` flag is active.
```

**Input section** (~5 lines):

Four sources read in order:
1. Just-completed team assembly (domain inference)
2. `.claude/rules/standards.md` (governance extraction)
3. Project files (test framework + linter detection)
4. `http://localhost:8080/v1/models` (local model detection)

**Output section** (~5 lines):

The vault/ directory structure from spec R3.2 — list the full tree.

**Algorithm — Detection Procedure** (spec R3.1, ~40 lines):

Four detection steps. Use the exact scan patterns from the spec:

1. **Domain detection:** Map from team assembly. Categories: `software`, `game-roblox`, `game-other`, `writing`, `research`, `other`.

2. **Test framework detection:** Scan project files:
   - `pytest.ini`, `conftest.py`, `tests/*.py` → `pytest`
   - `jest.config.*`, `__tests__/`, `*.test.ts` → `jest`
   - `spec/`, `.rspec`, Gemfile with `rspec` → `rspec`
   - `*.spec.luau`, TestEZ references → `testez`
   - None → `null`

3. **Linter detection:** Same pattern:
   - `.eslintrc*`, `eslint.config.*` → `eslint`
   - `.rubocop.yml` → `rubocop`
   - `selene.toml` → `selene`
   - `.flake8`, `pyproject.toml` with `[tool.ruff]` → `ruff`
   - None → `null`

4. **Model detection:** `GET http://localhost:8080/v1/models`. Extract `data[0].id`. On failure → placeholder.

**Algorithm — File Generation** (~120 lines):

Step-by-step generation of each file in the vault. For each generated file, specify:
- Exact path
- Source (which reference file provides the template, or inline generation)
- Any variable substitutions from detection results

The generation steps:

1. **Create vault directory structure** — all directories from R3.2, including empty `agents/` subdirs.

2. **Generate `vault/_schema/ticket.md`** — read `references/ticket-schema.md` (Task 1), copy the frontmatter schema section. Substitute domain-detected values into the proof-of-work fields.

3. **Generate `vault/_schema/proof-of-work.md`** — read `references/ticket-schema.md`, extract the domain row matching R3.1 detection. Write as:
   ```markdown
   # Proof-of-Work Schema
   
   ## Required Artifacts
   {list from domain row}
   
   ## Commands
   test_command: {detected or PLACEHOLDER}
   lint_command: {detected or PLACEHOLDER}
   
   ## Conditional Artifacts
   {list from domain row, if any}
   ```

4. **Generate `vault/_governance/PROJECT_RULES.md`** — governance extraction per spec R3.3:
   - Read `.claude/rules/standards.md`
   - Extract `## Quality Gates` bullets as imperative rules
   - Extract `## Anti-Patterns` bullets, invert to positive imperatives
   - Extract `## Forbidden` bullets verbatim
   - Write as flat rule list with project name header

5. **Generate `vault/_orchestration/hermes-config.yaml`** — per spec R3.4 template:
   ```yaml
   model: "{detected_model_id or placeholder}"
   
   providers:
     local:
       base_url: "http://localhost:8080/v1"
       api_key: ""
       context_length: 65536
   
   agent:
     max_turns: 90
     gateway_timeout: 1800
     tool_use_enforcement: "auto"
   
   terminal:
     backend: local
   
   _config_version: 16
   ```

6. **Generate `vault/_orchestration/dispatch-rules.md`** — ticket selection criteria, parallelism limits (max 3), file overlap serialization, retry budget (1), escalation trigger (2 consecutive failures).

7. **Generate `vault/_orchestration/escalation-protocol.md`** — per spec R3.4: `claude -p` invocation pattern with `--permission-mode acceptEdits --output-format json --max-turns 25`, JSON output parsing, change application, proof-of-work re-check, logging to `vault/agents/claude-code/{ticket-id}/`.

8. **Generate `vault/_orchestration/llama-server.md`** — per spec R3.4: startup command with detected model path, notes about `--jinja` (required) and `-c 65536` (minimum).

9. **Generate vault/skills/** — copy three Hermes skill templates:
   - Read `references/hermes-skills/vault-dispatcher.md` → write to `vault/skills/vault-dispatcher/SKILL.md`
   - Read `references/hermes-skills/proof-of-work.md` → write to `vault/skills/proof-of-work/SKILL.md`
   - Read `references/hermes-skills/circuit-breaker.md` → write to `vault/skills/circuit-breaker/SKILL.md`

10. **Generate `vault/tickets/TEMPLATE.md`** — empty ticket with full schema from R4, all fields with placeholder values and comments.

11. **Generate vault/runbooks/** — three runbooks per spec R3.5:
    - `daemon-setup.md`: pip install, config copy, hermes setup, skill copy, gateway start
    - `model-setup.md`: llama-server command with detected model, download instructions
    - `operations.md`: /status, /pause, /resume, /tickets commands

12. **Create empty `vault/agents/` subdirs** — `model/`, `claude-code/`, `circuit-breaker/`.

- [ ] **Step 2: Verify cross-references**

Verify every reference path in the file points to a file that exists (from Tasks 1-4):
- `references/ticket-schema.md` — exists (Task 1)
- `references/hermes-skills/vault-dispatcher.md` — exists (Task 2)
- `references/hermes-skills/proof-of-work.md` — exists (Task 3)
- `references/hermes-skills/circuit-breaker.md` — exists (Task 4)

Verify file is ~200 lines. Verify detection patterns match spec R3.1 exactly.

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/orchestrator-scaffold.md
git commit -m "feat: add orchestrator scaffold reference — master vault generation algorithm (R3)"
```

---

### Task 6: gigo:gigo SKILL.md Changes (R1 + R2)

**blocks:** 8
**blocked-by:** 5
**parallelizable:** true (with Task 7)

**Files:**
- Modify: `skills/gigo/SKILL.md:4` (frontmatter)
- Modify: `skills/gigo/SKILL.md:27` (after Gemma Harness Flag paragraph)
- Modify: `skills/gigo/SKILL.md:262` (after Step 6.75, before Step 7)
- Modify: `skills/gigo/SKILL.md:264` (Step 7 handoff)

- [ ] **Step 1: Update argument-hint frontmatter (R1)**

Change line 4 from:
```yaml
argument-hint: "[--include-gemma]"
```
to:
```yaml
argument-hint: "[--include-gemma] [--include-orchestrator]"
```

- [ ] **Step 2: Add Orchestrator Flag paragraph (R2)**

Insert after the Gemma Harness Flag paragraph (after line 27, before the "Domain asset scan" paragraph). ~5 lines:

```markdown
### Orchestrator Flag

If `$ARGUMENTS` contains `--include-orchestrator`, activate orchestrator scaffold generation. After Step 6.75 (or after Step 6.5 if Gemma flag is not set), Step 6.8 scaffolds the autonomous execution vault. Read `references/orchestrator-scaffold.md` for the full algorithm. This flag only applies during first assembly.
```

- [ ] **Step 3: Add Step 6.8 (R2)**

Insert after Step 6.75 (after line 262), before Step 7 (The Handoff). ~10 lines:

```markdown
### Step 6.8: Scaffold Orchestrator Vault (if flagged)

If the `--include-orchestrator` flag was set, scaffold the autonomous execution vault from the just-completed assembly. Read `references/orchestrator-scaffold.md` and follow the algorithm.

Input: project domain (from team assembly), `.claude/rules/standards.md`, project files (test/lint detection), local model (localhost:8080).
Output: `vault/` directory with schemas, governance, orchestration config, Hermes skills, ticket template, and runbooks.

This is infrastructure generation from already-approved assembly content. No additional operator approval needed. Include the vault location in the Step 7 summary.
```

- [ ] **Step 4: Update Step 7 handoff (R2)**

In the Step 7 format block (the command table), add a line after the existing content (inside the closing triple-backtick block, after the "Run `/blueprint`" line). The line only appears when `--include-orchestrator` was used:

Add this note after the format block:

```markdown
If `--include-orchestrator` was used, add to the "What just happened" section:
> Orchestrator vault scaffolded at `vault/`. See `vault/runbooks/daemon-setup.md` to install and start the Hermes daemon.
```

- [ ] **Step 5: Verify line count**

SKILL.md was ~325 lines. Adding ~18 lines puts it at ~343. Verify still under 500-line cap.

- [ ] **Step 6: Commit**

```bash
git add skills/gigo/SKILL.md
git commit -m "feat: add --include-orchestrator flag and Step 6.8 to gigo:gigo (R1, R2)"
```

---

### Task 7: Ticket Generation Reference + Phase 10.5 (R8 + R9)

**blocks:** 8
**blocked-by:** 1
**parallelizable:** true (with Task 6)

**Files:**
- Create: `skills/spec/references/ticket-generation.md`
- Modify: `skills/spec/SKILL.md:165-168` (between Phase 10 approval marker and Handoff section)

- [ ] **Step 1: Create ticket-generation.md (R8)**

Write `skills/spec/references/ticket-generation.md` (~60 lines). Three sections:

**Section 1 — Conversion Procedure** (spec R8.1, ~30 lines):

For each task in the approved plan:

1. **ID generation:** `TCK-{plan_phase_number}-{task_sequence_number}`. No phases → `TCK-0-{N}`. Pad sequence to 3 digits.

2. **Dependency mapping:**
   - `blocked-by: [task numbers]` → `depends_on: [TCK-{phase}-{sequence}]`
   - `blocks:` is discarded (inverse of depends_on)
   - `parallelizable: true` needs no special mapping

3. **Field population** — table mapping plan fields to ticket fields:

   | Plan field | Ticket field |
   |---|---|
   | Task title | `title` |
   | Phase heading | `phase` |
   | "Done when:" / exit criteria | `exit_criteria` |
   | "Files: Create:" + "Files: Modify:" | `produced_files` |
   | Domain schema | `proof_of_work` |
   | (default) | `assignee: local_model` |
   | (always) | `status: ready` |
   | Domain terms from content | `skill_hints` |
   | (default) | `permission_mode: acceptEdits` |

4. **Body generation:** Map task steps to ticket body sections per R4.3.

5. **Write** to `vault/tickets/TCK-{phase}-{sequence}.md`.

**Section 2 — DAG Validation** (spec R8.2, ~15 lines):

After generating all tickets:
1. Build adjacency list from `depends_on`.
2. Orphan check: every ID in any `depends_on` must exist. Flag missing: `"ERROR: TCK-{id} references non-existent dependency TCK-{missing-id}"`.
3. Cycle check: topological sort. Flag cycles: `"ERROR: Dependency cycle detected: TCK-A → TCK-B → ... → TCK-A"`.
4. If validation fails, do NOT write tickets. Report errors.

**Section 3 — Summary Output** (spec R8.3, ~10 lines):

```
Tickets generated: N
  Ready: M (no unmet dependencies)
  Blocked: K (waiting on dependencies)
Vault location: vault/tickets/
DAG: valid (no cycles, no orphaned refs)
```

- [ ] **Step 2: Add Phase 10.5 to spec SKILL.md (R9)**

Insert between the Phase 10 approval marker code block (line 165: ` ``` `) and the `---` separator before the Handoff section (line 167). ~12 lines:

```markdown
---

## Phase 10.5: Generate Vault Tickets (Conditional)

If `vault/_schema/ticket.md` exists in the project (indicating orchestrator scaffold is present), convert the approved plan's tasks into vault tickets.

Read `references/ticket-generation.md` for the full conversion procedure. This is a mechanical translation — no new decisions, no operator approval needed.

If the vault schema doesn't exist, skip this phase entirely. The standard /execute path proceeds as normal.

After generation, include the ticket summary in the handoff message.
```

- [ ] **Step 3: Verify**

Confirm `ticket-generation.md` exists with ~60 lines. Confirm spec SKILL.md has Phase 10.5 between Phase 10 and Handoff. Confirm SKILL.md is still under 500 lines (~196 + 12 = ~208).

- [ ] **Step 4: Commit**

```bash
git add skills/spec/references/ticket-generation.md skills/spec/SKILL.md
git commit -m "feat: add ticket generation reference and Phase 10.5 to gigo:spec (R8, R9)"
```

---

### Task 8: Integration Verification

**blocks:** []
**blocked-by:** 6, 7
**parallelizable:** false

**Files:**
- (no files created — verification only)

- [ ] **Step 1: Cross-reference audit**

Verify all internal references resolve:
- `skills/gigo/SKILL.md` references `references/orchestrator-scaffold.md` → exists
- `orchestrator-scaffold.md` references `references/ticket-schema.md` → exists
- `orchestrator-scaffold.md` references `references/hermes-skills/vault-dispatcher.md` → exists
- `orchestrator-scaffold.md` references `references/hermes-skills/proof-of-work.md` → exists
- `orchestrator-scaffold.md` references `references/hermes-skills/circuit-breaker.md` → exists
- `skills/spec/SKILL.md` references `references/ticket-generation.md` → exists

- [ ] **Step 2: Line count audit**

| File | Expected | Cap |
|---|---|---|
| `skills/gigo/SKILL.md` | ~343 | 500 |
| `skills/spec/SKILL.md` | ~208 | 500 |
| `skills/gigo/references/orchestrator-scaffold.md` | ~200 | — |
| `skills/gigo/references/ticket-schema.md` | ~80 | — |
| `skills/gigo/references/hermes-skills/vault-dispatcher.md` | ~80 | 100 |
| `skills/gigo/references/hermes-skills/proof-of-work.md` | ~50 | 100 |
| `skills/gigo/references/hermes-skills/circuit-breaker.md` | ~60 | 100 |
| `skills/spec/references/ticket-generation.md` | ~60 | — |

- [ ] **Step 3: Convention compliance**

Verify across all new files:
- Hermes skill templates use imperative voice exclusively (no "you should", no rationale)
- YAML frontmatter uses explicit quoting for strings, `null` for empty values
- Ticket IDs follow `TCK-{phase}-{sequence}` format consistently
- No references to Hermes `send_message` inside delegated skills (vault-dispatcher handles alerting)
- All YAML examples parse without errors

- [ ] **Step 4: Spec coverage check**

| Requirement | Task | File |
|---|---|---|
| R1: Flag Detection | 6 | `skills/gigo/SKILL.md` |
| R2: Hub Insertion | 6 | `skills/gigo/SKILL.md` |
| R3: Scaffold Reference | 5 | `skills/gigo/references/orchestrator-scaffold.md` |
| R4: Ticket Schema | 1 | `skills/gigo/references/ticket-schema.md` |
| R5: Vault-Dispatcher | 2 | `skills/gigo/references/hermes-skills/vault-dispatcher.md` |
| R6: Proof-of-Work | 3 | `skills/gigo/references/hermes-skills/proof-of-work.md` |
| R7: Circuit-Breaker | 4 | `skills/gigo/references/hermes-skills/circuit-breaker.md` |
| R8: Ticket Generation | 7 | `skills/spec/references/ticket-generation.md` |
| R9: Phase 10.5 | 7 | `skills/spec/SKILL.md` |

All 9 requirements covered.

**Done when:** All 6 reference files exist, both SKILL.md files are modified, cross-references resolve, line counts are within caps, and all spec requirements map to a file.
