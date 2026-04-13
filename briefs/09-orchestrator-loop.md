# Brief 09: Autonomous Orchestrator Scaffold

## The Problem

GIGO assembles a Claude-optimized project context (personas, rules, references) and added local model support (Briefs 06-08: harness, routing, formatting). But the actual orchestration — picking work, dispatching to models, validating results, escalating failures — is left to the operator. Every task requires a human in the loop: `/blueprint` → `/spec` → `/execute` → `/verify`.

The CosmoGene architecture proves this can be fully automated. A local model runs the state machine, Claude Code drops to a headless tool invoked via `claude -p`, quality is structural (proof-of-work, not judgment), and cost is governed by a circuit breaker. The operator queues up work, walks away, comes back to reviewed code.

This is the make flow going forward. GIGO should scaffold it.

## What We Know

### The Validated Architecture (CosmoGene)

```
SPEC PHASE (interactive, human + Claude Code):
  gigo:blueprint → gigo:spec → vault populated with tickets

OPERATIONAL PHASE (autonomous, Hermes daemon):
  Hermes gateway (systemd service, survives reboots)
    │  Brain: local model via custom provider → llama-server
    │  Skills: vault-dispatcher, proof-of-work, claude-code (built-in)
    │
    ├─ Reads vault, picks next ready ticket
    ├─ Constructs prompt (harness + formatted task + source files)
    ├─ Dispatches to local model via OpenAI-compatible endpoint
    │   ├─ Proof-of-work check: tests? lint? reviewer?
    │   └─ Pass → mark done, next ticket
    │
    ├─ Fail → Escalate via Hermes's built-in claude-code skill
    │   ├─ claude -p --permission-mode acceptEdits --output-format json
    │   ├─ Reviews, fixes, or rewrites
    │   └─ Close ticket, log verdict, next ticket
    │
    └─ Circuit breaker: >N% escalation rate → pause + Telegram/Discord alert
```

### Hermes Agent Framework (Verified)

**Repo:** `github.com/NousResearch/hermes-agent` (v0.8.0, MIT, 69.3k stars, actively developed)
**Docs:** `hermes-agent.nousresearch.com/docs/`
**User's local clone:** `~/projects/hermes/`

Hermes provides exactly the infrastructure this architecture needs:

| Capability | Hermes Feature | How the Orchestrator Uses It |
|---|---|---|
| Persistent daemon | `hermes gateway install` → systemd service with lingering | Runs 24/7, survives reboots, auto-restarts on crash |
| Local model brain | Custom provider config: `provider: custom`, `base_url: http://localhost:8080/v1` | Gemma 4 (or any model) via llama-server as the dispatch brain |
| Claude Code escalation | Built-in skill at `skills/autonomous-ai-agents/claude-code/SKILL.md` | `claude -p` in print mode, captures JSON output including session_id |
| Operator commands | 15 messaging adapters (Telegram, Discord, Slack, etc.) | `/status`, `/pause`, `/resume` via native gateway |
| Parallel dispatch | Subagent delegation: max 3 parallel, isolated context, no nesting | Independent tickets execute concurrently |
| Automated scheduling | Built-in cron scheduler | Periodic dispatch cycles, health checks |
| State persistence | SQLite sessions with FTS5, lineage tracking, atomic writes | Ticket state survives crashes, per-ticket session history |
| Extensible skills | Skill system with `SKILL.md` frontmatter, auto-learning | Custom vault-dispatcher, proof-of-work validator, circuit-breaker |
| Tool use | 47 built-in tools: file I/O, terminal, web, browser | Applying code, running tests, reading vault files |

**Key constraint:** Hermes requires **64K minimum context** for the connected model. Gemma 4 26B-A4B supports 128K, so this is satisfied. Models with smaller windows (some 7B quants) would be rejected.

**Key constraint:** llama-server must start with `--jinja` flag for Hermes tool calling to work.

### What's Already Built (Briefs 06-08)

These are the execution primitives the orchestrator consumes:

| Brief | What it provides | Orchestrator uses it for |
|---|---|---|
| 06 — Harness Generator | System prompt for local models | The system message in every dispatch |
| 07 — Model Routing | Model detection, API calls, response parsing, 4-layer escalation | Sending work to localhost:8080 and handling failures |
| 08 — Prompt Formatting | Explicit task descriptions, mechanical formatting, file inlining | Converting tickets into single-turn prompts |

### Key Properties

- **Model-agnostic.** The daemon doesn't care what's behind `localhost:8080`. Gemma 4, MiniMax M2.7, Qwen, whatever. Hermes's custom provider config and Brief 07's model detection both handle this.
- **Zero API spend in the hot loop.** Local model attempts first. Claude Code is flat subscription, escalation-only, protected by circuit breaker.
- **Structural "done."** A ticket isn't done because a model said so. It's done when proof-of-work artifacts exist: test output, lint output, reviewer verdict. Each is a file reference, not inline content.
- **The vault is the source of truth.** Markdown files, filesystem-transparent, git-versioned. Hermes reads/writes via its file I/O tools. No database, no SaaS, no API.

## What GIGO Scaffolds

During first assembly, GIGO already creates the Claude-native context (`.claude/rules/`, `.claude/references/`, `CLAUDE.md`). This brief adds the orchestrator infrastructure alongside it.

### 1. Vault Structure

The vault is a superset of what GIGO already creates. `.claude/` IS the proto-vault. The orchestrator adds:

```
vault/
├── _schema/                    # Machine-readable schemas
│   ├── ticket.md               # Ticket frontmatter schema + field descriptions
│   └── proof-of-work.md        # Required artifacts per domain
├── _governance/                # Project rules for agent behavior
│   └── PROJECT_RULES.md        # Non-negotiable constraints (from GIGO's standards)
├── _orchestration/             # Hermes config and dispatch rules
│   ├── hermes-config.yaml      # Model provider, escalation threshold, gateway settings
│   ├── dispatch-rules.md       # How tickets are picked and ordered
│   ├── escalation-protocol.md  # Claude Code invocation pattern + retry budget
│   └── llama-server.md         # Server startup command + model path
├── tickets/                    # Work units (populated during spec phase)
│   └── TEMPLATE.md             # Empty ticket with full schema
├── skills/                     # Custom Hermes skills for this project
│   ├── vault-dispatcher/       # Reads tickets, builds dependency graph, dispatches
│   │   └── SKILL.md
│   ├── proof-of-work/          # Validates artifacts before marking done
│   │   └── SKILL.md
│   └── circuit-breaker/        # Monitors escalation rate, pauses + alerts
│       └── SKILL.md
├── agents/                     # Operational logs (populated during execution)
│   ├── model/                  # Local model attempt logs per ticket
│   ├── claude-code/            # Escalation session logs
│   └── circuit-breaker/        # State + alert history
└── runbooks/
    ├── daemon-setup.md         # How to install + start the Hermes gateway
    ├── model-setup.md          # llama-server setup for this project's model
    └── operations.md           # /status, /pause, /resume, /replan commands
```

### 2. Hermes Configuration

Generated `hermes-config.yaml` with project-specific settings:

```yaml
model:
  provider: custom
  model: "{detected model name}"
  base_url: http://localhost:8080/v1
  api_key: ""
  context_length: 32768

delegation:
  model: "{same or different model}"
  provider: custom
  base_url: http://localhost:8080/v1

gateway:
  platform: telegram              # or discord, slack — operator chooses during assembly
  
skills:
  config:
    vault:
      path: ./vault
    circuit_breaker:
      escalation_threshold: 0.30
      window_size: 10             # rolling window of last N tickets
      alert_channel: telegram     # matches gateway platform
```

GIGO detects the model from `localhost:8080/v1/models` during assembly (same as Brief 07). If no model is running, writes placeholder with setup instructions.

### 3. Ticket Schema

Machine-readable frontmatter + human/LLM context body. The unit of work for the daemon.

```yaml
type: ticket
id: TCK-XXXX
title: "..."
phase: "..."
depends_on: []
assignee: local_model          # local_model | claude_code | human
status: ready                  # ready | in_progress | done | failed | escalated

skill_hints: []                # domain-specific hints for prompt construction
permission_mode: acceptEdits

exit_criteria:
  - "Concrete, testable criterion 1"
  - "Concrete, testable criterion 2"

produced_files: []             # filled on completion
model_history: []              # which model attempted, when, result

proof_of_work:
  required:
    - test_output              # ref to test run artifact
    - lint_output              # ref to lint/format output
    - reviewer_verdict         # ref to reviewer note
  conditional: []              # domain-specific extras
  produced:
    test_output: null
    lint_output: null
    reviewer_verdict: null
```

GIGO generates the schema during assembly based on the project's domain:
- **Software projects:** test_output (framework auto-detected: RSpec, Jest, pytest, etc.), lint_output (linter auto-detected: RuboCop, ESLint, Selene, etc.), reviewer_verdict
- **Game projects:** test_output (TestEZ, Lune, etc.), lint_output (Selene, StyLua), reviewer_verdict, optional studio_playtest_note
- **Other domains:** adapted proof-of-work artifacts (e.g., word count for writing, render output for design)

### 4. Custom Hermes Skills

Three skills GIGO scaffolds for the project:

**vault-dispatcher** — Reads `vault/tickets/`, builds dependency graph from `depends_on` fields, yields next ready ticket, constructs the prompt using Brief 06 harness + Brief 08 formatting + Brief 07 file selection. Core dispatch loop.

**proof-of-work** — After a ticket attempt (local model or Claude Code), checks each `proof_of_work.required` field. Runs tests, runs linter, populates `proof_of_work.produced` with file references. Refuses to set `status: done` if any required artifact is missing or failed.

**circuit-breaker** — Tracks `escalation_count / total_attempted` over a rolling window. When threshold exceeded: sets dispatch to paused, sends alert via gateway, logs state. Responds to `/resume` command to restart.

### 5. Claude Code Escalation

Uses Hermes's built-in `claude-code` skill. GIGO generates the escalation protocol:

```markdown
## Escalation Protocol

When a ticket fails local model execution (after 1 retry):

1. Invoke claude-code skill in print mode:
   claude -p "{ticket context + prior attempt + error output}" \
     --permission-mode acceptEdits \
     --output-format json \
     --max-turns 25 \
     --allowedTools "Read,Edit,Write,Bash"

2. Parse JSON output for:
   - File changes (type: "tool_use", tool: "Edit"/"Write")
   - Session ID (for resumption if needed)
   - Terminal reason (end_turn, max_turns, error)

3. Apply changes to worktree
4. Run proof-of-work checks (same as local model path)
5. Log session to vault/agents/claude-code/{ticket-id}/
6. Update ticket: model_history += { model: "claude-code", session_id, result }
```

### 6. Dispatch Logic

The state machine for the vault-dispatcher skill:

```
1. Read vault/tickets/, build dependency graph from depends_on fields
2. Find next ticket where:
   - status = ready
   - all depends_on tickets have status = done
   - assignee = local_model (or unassigned)
3. Set status = in_progress
4. Construct prompt:
   - System: harness from .claude/references/gemma-harness.md (Brief 06)
   - User: formatted ticket (Brief 08 procedure) + inlined source files (Brief 07 selection)
5. Send to local model via Hermes's custom provider
6. Parse response → code blocks with file paths
7. Apply to worktree (Hermes file I/O tools)
8. Run proof-of-work:
   - Execute test command (auto-detected during assembly)
   - Execute lint command (auto-detected during assembly)
   → All pass: write artifact refs, set status = done, next ticket
   → Fail: retry once with error context appended
   → Still fail: set status = escalated, invoke claude-code skill
9. Circuit breaker check after each ticket
10. When no ready tickets remain: report summary, idle
```

**Parallelism:** Hermes's delegation system supports max 3 concurrent subagents. Independent tickets (no shared `depends_on`) can dispatch in parallel via `delegate_task()`. Each subagent gets isolated context — no cross-contamination. Tickets that write to overlapping files are serialized.

### 7. Runbooks

GIGO generates project-specific runbooks:

**daemon-setup.md** — How to install Hermes, configure the gateway, start the service:
```bash
# Install Hermes
pip install hermes-agent  # or from ~/projects/hermes/

# Configure
hermes setup              # Interactive wizard
hermes model              # Point to llama-server

# Install custom skills
cp -r vault/skills/* ~/.hermes/skills/

# Start daemon
hermes gateway install    # Creates systemd service
hermes gateway run        # Or foreground for testing
```

**model-setup.md** — llama-server startup for this project's model:
```bash
llama-server \
  -m ~/models/{model-file}.gguf \
  --host 0.0.0.0 --port 8080 \
  -c 65536 -np 1 -ngl 99 \
  --flash-attn on --jinja    # --jinja required for Hermes tool calling
```

**operations.md** — Operator commands via gateway:
- `/status` — current ticket, escalation rate, circuit breaker state
- `/pause` — stop dispatching new tickets
- `/resume` — restart after pause or circuit breaker
- `/tickets` — list ready/in_progress/done counts

## Integration with Existing GIGO Skills

### Spec Phase (Interactive)

| Skill | Role in orchestrator flow |
|---|---|
| `gigo:blueprint` | Design briefs → feeds ticket creation |
| `gigo:spec` | Specs + plans → decomposed into tickets via new ticket-generation step |
| `gigo:gigo` | First assembly → scaffolds vault + orchestrator alongside .claude/ context |
| `gigo:maintain` | Adds expertise, updates orchestrator config, regenerates proof-of-work schema |

### Operational Phase (Autonomous)

| Component | Role |
|---|---|
| Hermes gateway | Persistent daemon, runs dispatch loop, handles operator commands |
| Local model (via llama-server) | Attempts tickets — brain for Hermes |
| Claude Code (headless, via built-in skill) | Escalation worker — subscription-governed |
| Proof-of-work skill | Quality gate — structural, not judgment |
| Circuit breaker skill | Cost protection — escalation rate governor |
| `gigo:verify` | Human review gate (on-demand, not in hot loop) |

### The Boundary

GIGO skills live in the spec phase. Hermes lives in the operational phase. GIGO scaffolds Hermes's infrastructure (vault, skills, config, runbooks) but doesn't run it — Hermes is a separate daemon. This parallels how GIGO writes CLAUDE.md but doesn't run Claude Code.

The bridge: `gigo:spec` decomposes plans into tickets that Hermes can dispatch. `gigo:verify` reviews what Hermes built when the operator wants a human gate.

## Where This Lives

**Option A: Flag on `gigo:gigo`** — `--include-orchestrator`
- Scaffolds vault + Hermes config + custom skills during first assembly
- Parallel to `--include-gemma` (harness generation)
- Pro: one-shot setup. Con: makes gigo:gigo bigger.

**Option B: Separate skill** — `gigo:orchestrate`
- Invoked after assembly: "set up autonomous execution for this project"
- Reads the existing assembly, generates orchestrator infrastructure
- Pro: clean separation. Con: extra invocation step.

**Option C: Both**
- Flag for scaffold (structure only — vault, schemas, templates)
- Skill for ongoing operations (ticket creation from plans, dispatch monitoring, config updates)

## Testing

### Scaffold Validation
- Run assembly with orchestrator flag on the Rails API fixture
- Verify: vault structure created, ticket schema matches domain (RSpec for tests, RuboCop for lint)
- Verify: hermes-config.yaml has correct provider config for llama-server
- Verify: template ticket has domain-appropriate proof-of-work
- Verify: custom skills have valid SKILL.md files that Hermes accepts

### Single-Ticket Execution
- Create one ticket from an existing plan task
- Run the vault-dispatcher skill once (not full daemon — single dispatch)
- Verify: local model receives formatted prompt, response parsed, files written
- Verify: proof-of-work skill runs tests and populates artifact references
- Verify: ticket status transitions: ready → in_progress → done

### Escalation Path
- Create a ticket that will fail (references nonexistent table/module)
- Verify: local model fails → retry → still fails → escalated
- Verify: Claude Code invocation fires via built-in skill
- Verify: ticket marked done with claude-code in model_history
- Verify: escalation logged to vault/agents/claude-code/

### Circuit Breaker
- Create 5 tickets, 3 designed to fail local model execution
- Verify: circuit breaker triggers (3/5 = 60% > 30% threshold)
- Verify: dispatch pauses, alert fires via gateway
- Verify: `/resume` command restarts dispatch

### Cost Comparison
- Same plan: full Claude Code execution vs Hermes+local model
- Measure: Claude Code subscription usage (escalation only vs everything)
- Hypothesis: 60-80% subscription usage reduction with comparable output quality

## Dependencies

- **Brief 06 (Harness Generator):** Shipped. Provides system prompt.
- **Brief 07 (Model Routing):** Shipped. Provides execution primitives (model detection, API calls, response parsing).
- **Brief 08 (Prompt Formatting):** Shipped. Provides task formatting procedure.
- **Hermes Agent v0.8.0:** Installed. Repo at `~/projects/hermes/`. Docs at `hermes-agent.nousresearch.com/docs/`.
- **A running local model:** For testing. Any model behind llama-server with `--jinja` flag and ≥64K context.

## Scope / Decomposition

This is the biggest piece in the pipeline. Decomposition into independently shippable phases:

1. **Vault + Schema** — Scaffold the vault structure, ticket schema, proof-of-work schema, Hermes config template. No execution. Just the data model and config. GIGO skill changes only.

2. **Custom Hermes Skills** — Write the three custom skills (vault-dispatcher, proof-of-work, circuit-breaker). Test each in isolation against the Hermes skill system. No daemon — skills invoked manually.

3. **Single-Ticket Loop** — Wire skills together: dispatch one ticket → local model → parse → apply → proof-of-work. End-to-end on one ticket. Escalation path tested.

4. **Full Daemon** — Hermes gateway with all skills active. Multi-ticket dispatch with dependency resolution. Circuit breaker live. Operator commands via Telegram/Discord. Runbooks validated.

Each phase is independently shippable. Phase 1 has value immediately — it standardizes how work is represented and how the orchestrator is configured. Phase 2 proves the skills work within Hermes. Phase 3 proves the execution loop. Phase 4 makes it autonomous.

## What This Is NOT

- **Not a replacement for `gigo:execute`.** The execute skill handles Claude-native execution (subagents, worktrees, two-stage review). Hermes is a different execution path for when a local model runs the show.
- **Not CosmoGene-specific.** CosmoGene validated the pattern. GIGO generalizes it — software, games, research, whatever the domain.
- **Not locked to Hermes.** The vault + ticket + proof-of-work pattern is framework-agnostic. Hermes is the target because it provides daemon mode, Claude Code integration, messaging gateway, and skill system out of the box. But the vault schema and dispatch logic would work with any agent framework that can read markdown and call APIs.
- **Not locked to Gemma.** Any model behind llama-server with ≥64K context and `--jinja` support works. Gemma 4, MiniMax M2.7, Qwen, future models.
