# Executor Model Routing — Spec

**Design brief:** `.claude/plans/functional-hopping-hollerith.md`

## Original Request

> gigo:execute currently dispatches all work through Claude Agent subagents. We proved Gemma 4 handles execution tasks at 100% quality in 16s (vs Opus tokens). Add model detection (localhost:8080/health) and route execution tasks to the local model when available, fall back to Claude when not. The hard part is applying Gemma's text output (code blocks) as actual file writes — Gemma has no tool use. Depends on brief 06 (harness).

## Problem

Every execution task in `gigo:execute` costs Claude tokens — haiku at minimum, often sonnet or opus. The Gemma eval proved that a local model (26B-A4B at 16s/prompt, 31B at 107s/prompt) achieves 100% EXECUTES on spec-following tasks when given a harness. Brief 06 shipped harness generation. The missing piece: a routing layer that detects a local model, sends tasks to it, and bridges Gemma's text output (code blocks) to files on disk. Claude tokens should be reserved for planning, review, and escalation — not routine execution.

The core constraint: Gemma generates text, not tool calls. It can't read files, write files, or run tests. The hybrid applier approach solves this — Gemma generates code, a minimal haiku subagent applies it in a worktree. This preserves worktree isolation, the review pipeline, and the checkpoint protocol while routing the creative work (code generation) to the free local model.

## Requirements

### R1: Model Detection

At execute startup (after reading the plan, before presenting options), the lead checks for a local model:

1. `GET http://localhost:8080/health` — 200 means a local model is running
2. `GET http://localhost:8080/v1/models` — extract model ID string (e.g., `gemma-4-26b-a4b`)
3. Check `.claude/references/gemma-harness.md` exists in the target project

All three must pass. If health check fails (connection refused, timeout, non-200): local routing disabled, no error. If health passes but harness is missing: warn operator ("No Gemma harness found. Run gigo:gigo --include-gemma to generate one."), disable local routing. Detection runs once at startup, not per-task.

Implement the detection logic in `skills/execute/references/local-model-routing.md` as the authoritative reference. SKILL.md adds ~5 lines: a detection step in "Before Starting" and a pointer to the reference.

### R2: Execution Options Update

Modify the "Present execution options" step in SKILL.md to include the local model option when detection passes:

```
> "Local model detected: {model_id} at localhost:8080.
> 1. **Subagents + local model** (recommended) — Gemma generates, haiku applies in worktrees
> 2. **Subagents only** — Claude subagents (current behavior)
> 3. **Inline** — sequential in this session"
```

When detection did not pass, present current options unchanged (no mention of local model).

Default behavior: use subagents + local model for plans with 3+ tasks when local is available. Present the choice to the operator only if they haven't specified a preference.

### R3: Prompt Formatting

For each task routed to Gemma, the lead constructs a two-part prompt:

**System message:** Full contents of `.claude/references/gemma-harness.md` (everything after the `---` separator — the harness content, not the header/instructions).

**User message:** Task description + inline source files + expected output files:

```
{task description from plan, verbatim}

## Current Files

### {file_path_1}
{file contents}

### {file_path_2}
{file contents}

## Output Files
{list of files to produce — parsed from the task description's "Files:" section}
```

#### R3.1: File Selection Heuristic

Which files to inline for each task:

1. Files listed in the task's **Files:** section (Create targets show expected output; Modify targets show current content)
2. Schema/type definition files when the task involves data model changes (e.g., `schema.rb`, `schema.prisma`, type definition files)
3. Files referenced in "What Was Built" addendums from dependency tasks — only the files that changed, not the full addendum text
4. If the task mentions importing from or depending on specific modules, include those module files

**Do not include** test helpers, config files, or files not directly relevant to the task unless the task description explicitly references them.

#### R3.2: Context Budget

Total llama-server context: 32,768 tokens.

| Budget slice | Tokens | Purpose |
|---|---|---|
| System (harness) | ~2,000 | Gemma harness from `.claude/references/gemma-harness.md` |
| Generation output | ~8,000 | Reserved for Gemma's response (`max_tokens: 8192`) |
| User message | ~22,000 | Task description + inline source files |

If inlined files exceed the ~22K user budget, apply this priority:
1. Keep task description (always)
2. Keep files the task directly creates or modifies
3. Keep schema/type files
4. Drop dependency context files (largest first)
5. If still over budget, skip local routing for this task — dispatch to Claude subagent instead

Estimate token count at 4 characters per token for budget checks.

### R4: API Call

The lead calls llama-server via curl, with the JSON request body written to a temp file to avoid shell escaping issues with inline source code.

#### R4.1: JSON Serialization

The JSON payload must be constructed using the Write tool (not echo, heredoc, or inline shell construction). Source files contain newlines, quotes, backticks, backslashes, and other characters that break shell escaping. Writing a file with the Write tool handles this correctly.

**Procedure:**
1. Construct the messages array: `[{"role": "system", "content": "<harness>"}, {"role": "user", "content": "<formatted prompt>"}]`
2. Write the complete JSON request body to `/tmp/gigo-gemma-task-{N}.json` using the Write tool
3. Call curl with the `@` file reference

```bash
curl -s --max-time 300 http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @/tmp/gigo-gemma-task-{N}.json
```

#### R4.2: Timeout

- curl `--max-time 300` (5 minutes): covers 31B's ~107s generation with margin
- Bash tool `timeout: 360000` (6 minutes): outer safety net above curl's own timeout

If curl times out: treat as API failure (Layer 1 escalation, R8).

#### R4.3: Cleanup

After the API response is received (success or failure), delete the temp file:
```bash
rm -f /tmp/gigo-gemma-task-{N}.json
```

### R5: Response Parsing

Parse Gemma's response to extract code blocks with their target file paths.

#### R5.1: Extraction

1. Parse the curl JSON response to extract `choices[0].message.content`
2. Split the content on triple-backtick markers (` ``` `)
3. For each code block:
   - The first token after the opening backticks is the language identifier (e.g., `ruby`, `python`, `typescript`)
   - The first line of code content is the file path, formatted as a comment (e.g., `# db/migrate/20260413_add_column.rb`)
   - Strip the comment character (`#`, `//`, `--`) and whitespace to get the bare path
   - Remaining lines are the file content
4. Produce an ordered list of `{path, content, language}` tuples

#### R5.2: Validation

A valid parse requires:
- At least one code block extracted
- At least one code block with a parseable file path
- No file paths that are clearly not paths (single words, sentences, empty strings)

If validation fails: escalate to Claude subagent (Layer 2, R8).

#### R5.3: Edge Cases

| Case | Handling |
|---|---|
| Code block has no file path header | Map to expected output files from the task's "Output Files" list by position (first block → first expected file, second → second, etc.). If no expected files listed or position exceeds the list, skip the block. |
| Nested code blocks (markdown in markdown) | Match outermost block delimiters only. Rare for code tasks. |
| Empty code block | Skip — do not create an empty file. |
| File path contains spaces | Preserve as-is — the applier must quote the path. |
| Multiple blocks targeting the same file | Use the last occurrence (later blocks likely include fixes). |

### R6: Applier Subagent

After Gemma generates and the lead parses, dispatch a haiku subagent to write files and run tests in an isolated worktree.

#### R6.1: Dispatch

```
Agent(
  description: "Task {N}: apply generated code",
  model: "haiku",
  isolation: "worktree",
  prompt: <applier prompt>
)
```

Model is always haiku — this is purely mechanical work (write files, run commands, report).

#### R6.2: Applier Prompt Template

New template added to `skills/execute/references/teammate-prompts.md`:

```
You are applying pre-generated code to files. Write each file exactly as provided.
Do not modify, improve, or add to the code. Apply it verbatim.

## Files to Write

### {path/to/file1}
{code content — pasted verbatim from parsed response}

### {path/to/file2}
{code content}

[repeat for all parsed code blocks]

## After Writing
1. Create any directories that don't exist.
2. Write each file to its exact target path.
3. If a file already exists, replace its contents entirely.
{IF test_command exists:}
4. Run: {test_command}
5. If tests fail, report the test output — do NOT attempt to fix the code.
{END IF}
6. Commit all changes to this branch.
7. Report back with the list of files written.

Status: DONE | BLOCKED (with reason — include full test output if tests failed)
```

**Key constraint:** The applier must NOT modify the code. It writes files verbatim and reports results. If tests fail, it reports the failure — it doesn't debug or fix. The lead handles escalation.

#### R6.3: Gemma Fix Prompt Template

New template for re-prompting Gemma on test failure or review feedback:

```
{system: harness — same as original}

{user message:}
The previous code had issues.

## Original Task
{original task description}

## Issue
{test failure output OR review feedback — verbatim}

## Previous Code
{the code blocks from the failed attempt}

## Current Files
{same inline source files as original, updated if applier modified any}

Fix the issues. Output corrected code blocks only.
```

### R7: Wave Execution with Local Routing

Modify the Tier 1 execution flow to support sequential Gemma generation followed by parallel haiku dispatch.

#### R7.1: Modified Wave Flow

For each wave of unblocked tasks (when local routing is enabled):

1. **Identify wave** — same as current
2. **Pre-flight** — same as current (file conflicts, CWD check)
3. **Sequential Gemma generation** — for each task in the wave:
   a. Format the Gemma prompt (R3)
   b. Write JSON to temp file (R4.1)
   c. Call Gemma API (R4)
   d. Parse response (R5)
   e. If parse fails → mark task for Claude fallback
   f. Clean up temp file (R4.3)
4. **Parallel dispatch** — dispatch all applier subagents in one message:
   - Tasks with successful Gemma responses → haiku applier (R6)
   - Tasks marked for Claude fallback → standard Claude subagent (existing prompt from teammate-prompts.md, model per model-selection.md)
   - Both use `isolation: "worktree"`
5. **Review, triage, merge** — same as current (gigo:verify, then triage, then merge)

#### R7.2: Status Mapping

Applier subagents report simplified status:

| Applier status | Maps to existing status | Next action |
|---|---|---|
| DONE | DONE | Proceed to review |
| BLOCKED (test failure) | BLOCKED | Gemma retry (R8 Layer 3) |
| BLOCKED (write failure) | BLOCKED | Escalate to Claude (filesystem issue, not a code problem) |

### R8: Error Handling & Escalation

Four layers, each with a clear fallback.

#### R8.1: Layer 1 — API Failure

**Trigger:** Connection refused, HTTP error, curl timeout.
**Action:** Route this task to a Claude subagent using existing Tier 1 dispatch (model per model-selection.md).
**Announce:** "Gemma API unavailable for Task {N}, routing to Claude ({model})."

If the API fails on the first task of a session, disable local routing for all remaining tasks (server is probably down). Don't retry the API on every task.

#### R8.2: Layer 2 — Parse Failure

**Trigger:** Gemma response doesn't contain valid code blocks (R5.2 fails).
**Action:** Route to Claude subagent.
**Announce:** "Gemma response couldn't be parsed for Task {N}, routing to Claude ({model})."

#### R8.3: Layer 3 — Test Failure

**Trigger:** Applier reports BLOCKED with test output.
**Action:**
1. Re-prompt Gemma with the fix prompt (R6.3), including test output. One retry.
2. If retry also fails tests → escalate to Claude subagent at one model tier above model-selection.md default (e.g., if model-selection.md says sonnet, escalate to opus).
**Announce:** "Gemma retry failed for Task {N}, escalating to Claude ({higher_model})."

#### R8.4: Layer 4 — Review Failure

**Trigger:** gigo:verify finds issues after applier reports DONE.
**Action:** Follow existing triage rules:
- Auto-fix items → re-prompt Gemma with review feedback (R6.3). One shot.
- If Gemma can't fix (second review still fails) → dispatch Claude fix subagent.
- Ask-operator items → surface to operator as usual.
**Announce auto-fix escalation:** "Gemma couldn't resolve review feedback for Task {N}, dispatching Claude fix."

#### R8.5: Escalation Principle

Gemma gets first attempt + one retry. Claude is the safety net. Every routing change is announced to the operator. Failures are never silent.

### R9: Checkpoint Extension

Add an optional `model` field to the checkpoint format.

**New syntax:**
```
<!-- checkpoint: sha=abc1234 status=done reviewed=pass tier=1 model=gemma-26b -->
<!-- checkpoint: sha=def5678 status=done reviewed=pass tier=1 model=claude-sonnet -->
```

**Values:** `gemma-26b`, `gemma-31b` (extracted from model detection), or `claude-haiku`, `claude-sonnet`, `claude-opus`. When local routing is disabled, omit the field (backward compatible with existing checkpoints).

**Purpose:** Production tracing — when a task's output quality is questioned, the model field immediately answers "who wrote this?"

**Resume behavior:** The `model` field is informational only. Resume logic ignores it — it doesn't affect which model handles a retry.

Update `skills/execute/references/checkpoint-format.md`:
- Add `model` to the Fields table
- Add one example showing the field
- Note: optional, backward compatible

### R10: Completion Summary

Modify the "When All Tasks Complete" section in SKILL.md to include routing statistics when local routing was used:

```
"N tasks completed. M via Gemma {model_id} (avg Xs generation),
K via Claude (reasons: parse failure on Task A, escalation on Task B)."
```

Report routing stats only when local routing was active. When all tasks ran via Claude (no local model), omit — no change from current behavior.

### R11: Model Selection Update

Update `skills/execute/references/model-selection.md` to document the local model override:

When local routing is enabled (R1 detection passes, operator chose option 1):
- All tasks route to Gemma first, regardless of complexity tier
- Complexity tier from model-selection.md is used ONLY for Claude fallback/escalation
- Escalation uses one tier above model-selection.md default (R8.3)

Add this as a new section at the top of model-selection.md, before the existing table.

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| Add (model detection) | R1: Model Detection | Done |
| Route (to local model) | R3, R4, R7: Prompt Formatting, API Call, Wave Execution | Done |
| Fall back (to Claude) | R8: Error Handling & Escalation | Done |
| Apply (text output as file writes) | R5, R6: Response Parsing, Applier Subagent | Done |

## Conventions

### JSON Serialization

Always use the Write tool to construct API request JSON. Never use echo, heredoc, printf, or inline shell construction. Source files contain every character that breaks shell escaping — newlines, single quotes, double quotes, backticks, backslashes, dollar signs. The Write tool handles all of these correctly. The lead writes `/tmp/gigo-gemma-task-{N}.json` and passes it to curl via `@` file reference.

### File Path Parsing

Gemma outputs file paths as the first line of each code block, formatted as a comment in the block's language:
- Ruby/Python/Shell: `# path/to/file.rb`
- JavaScript/TypeScript: `// path/to/file.ts`
- SQL: `-- db/migrate/001_init.sql`
- CSS: `/* path/to/file.css */`

The parser strips the comment syntax and leading/trailing whitespace to extract the bare path.

### Escalation Logging

Every routing decision that differs from the default (Gemma first) is announced to the operator. Format: `"[reason] for Task {N}, routing to [target] ({model})."` This creates an audit trail in the conversation.

### Context Budget Estimation

Estimate token count at 4 characters per token. This is conservative (typical English is ~3.5 chars/token, code is ~4-5). Being conservative is correct — exceeding the context window truncates input silently, which produces broken output.

### Temp File Naming

Pattern: `/tmp/gigo-gemma-task-{N}.json` where N is the task number from the plan. Cleaned up immediately after use. No PII or sensitive data persists in /tmp beyond the API call.

## Out of Scope

- **Prompt formatting refinement (brief 08)** — this spec includes a minimal file selection heuristic. Brief 08 will refine it with smarter selection, context window testing, and Gemma-specific task formatting.
- **Agent loop / Hermes (brief 09)** — the hybrid applier is a bridge. Brief 09 replaces it with a proper agent framework where Gemma has tool use.
- **Multi-slot parallelism** — llama-server supports multiple slots, but the default is 1. Parallel Gemma generation is deferred until slot management is tested.
- **Model auto-selection (26B vs 31B per task)** — the spec routes all tasks to whichever model is running. Per-task 26B/31B routing based on complexity is deferred.
- **Inline tier (Tier 2)** — local model routing applies to subagent execution (Tier 1) only. Inline mode uses current behavior.

## Risks

1. **Gemma produces incompatible code on complex multi-file tasks.** The eval tested single-prompt tasks. Real plan tasks with dependency context and multiple output files are harder. Mitigation: escalation path catches failures in ~16s (26B) and falls back to Claude. The worst case is burning one Gemma attempt before Claude handles it — 16s overhead.

2. **JSON serialization breaks on exotic source file contents.** Source files can contain any character. Mitigation: R4.1 mandates Write tool for JSON construction, which handles encoding correctly. The spec explicitly bans shell-based JSON construction.

3. **Response parsing fails on non-standard code block formats.** Gemma occasionally varies its output format despite harness instructions. Mitigation: validation in R5.2 catches malformed responses, and Layer 2 escalation handles the fallback.

4. **Haiku applier modifies code instead of applying verbatim.** Haiku might "improve" the code or add error handling. Mitigation: the applier prompt explicitly says "Do not modify, improve, or add to the code. Apply it verbatim." Review (gigo:verify) would catch any deviation from the spec.

5. **Context budget estimation is wrong, causing truncation.** If the 4 chars/token estimate is too generous, large files might get truncated in the llama-server context. Mitigation: the budget check in R3.2 is conservative (22K tokens out of 32K available), and the fallback skips local routing for over-budget tasks.

<!-- approved: spec 2026-04-13T02:10:42 by:Eaven -->
