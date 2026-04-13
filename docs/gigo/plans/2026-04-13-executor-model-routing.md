# Executor Model Routing — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-13-executor-model-routing-design.md`

**Goal:** Route execution tasks to a local Gemma model when available, with Claude as fallback. Gemma generates code, a haiku applier writes files in worktrees.

**Architecture:** Detection at startup, sequential Gemma generation via curl, parallel haiku applier dispatch in worktrees, 4-layer escalation to Claude on failure. New reference file holds the procedure; SKILL.md integrates with pointers.

**Tech Stack:** llama-server (OpenAI-compatible API), curl, existing Claude Agent subagent dispatch

---

### Task 1: Create Local Model Routing Reference

**blocks:** 5
**blocked-by:** []
**parallelizable:** true (with Tasks 2, 3, 4)

**Files:**
- Create: `skills/execute/references/local-model-routing.md`

This is the authoritative reference for the entire local routing system. SKILL.md will point here; this file contains all procedural detail.

- [ ] **Step 1: Write the detection section**

```markdown
# Local Model Routing

When a local model is available, execution tasks route through it instead of Claude subagents. Gemma generates code; a haiku applier writes the files in a worktree. Claude handles planning, review, and escalation.

---

## Detection (Run Once at Startup)

After reading the plan, before presenting execution options:

1. **Health check:**
   ```bash
   curl -s --max-time 5 http://localhost:8080/health
   ```
   If status 200: proceed. Otherwise: local routing disabled. No error — this is expected when no local model is running.

2. **Model identification:**
   ```bash
   curl -s --max-time 5 http://localhost:8080/v1/models
   ```
   Extract the model ID from `data[0].id`. Store it for reporting (e.g., `gemma-4-26b-a4b`).

3. **Harness check:** Verify `.claude/references/gemma-harness.md` exists via Glob or Read.
   - Exists: local routing enabled.
   - Missing: warn operator ("No Gemma harness found. Run gigo:gigo --include-gemma to generate one."). Local routing disabled.

All three must pass. Detection runs once — not per-task.
```

- [ ] **Step 2: Write the prompt formatting section**

```markdown
## Prompt Formatting

For each task routed to Gemma, construct a two-part prompt.

### System Message

Read `.claude/references/gemma-harness.md`. Extract everything after the first `---` separator (the harness content, not the header/usage instructions).

### User Message

```
{task description from plan — paste verbatim, including all steps}

## Current Files

### {file_path}
{file contents}

[repeat for each selected file]

## Output Files
- {path/to/output1}
- {path/to/output2}
```

### File Selection

Which files to inline:

1. Files in the task's **Files:** section — for Modify targets, read and include current contents. For Create targets, list in Output Files.
2. Schema/type definitions — when the task involves data model changes, include schema files (`schema.rb`, `schema.prisma`, etc.).
3. Dependency context — files listed in "What Was Built" addendums from prior tasks (only changed files, not full addendums).
4. Imported modules — if the task mentions importing from or depending on specific modules, include those files.

Do not include test helpers, config files, or files the task doesn't reference.

### Context Budget

Total context: 32,768 tokens. Budget:

| Slice | Tokens | Purpose |
|---|---|---|
| System (harness) | ~2,000 | Gemma harness |
| Generation output | ~8,000 | `max_tokens: 8192` |
| User message | ~22,000 | Task + inline files |

Estimate tokens at 4 characters per token. If files exceed ~22K:
1. Keep task description (always)
2. Keep files the task creates or modifies
3. Keep schema/type files
4. Drop dependency files (largest first)
5. If still over → skip local routing for this task, dispatch to Claude
```

- [ ] **Step 3: Write the API call section**

```markdown
## API Call

### JSON Serialization

**Use the Write tool** to create the request JSON at `/tmp/gigo-gemma-task-{N}.json`. Never use echo, heredoc, or inline shell construction — source files contain newlines, quotes, backticks, and backslashes that break shell escaping.

Request body format:
```json
{
  "messages": [
    {"role": "system", "content": "<harness content>"},
    {"role": "user", "content": "<formatted task prompt>"}
  ],
  "temperature": 1.0,
  "max_tokens": 8192
}
```

### Calling the API

```bash
curl -s --max-time 300 http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @/tmp/gigo-gemma-task-{N}.json
```

Use Bash tool timeout of 360000ms (6 minutes) as the outer safety net.

### Cleanup

After receiving the response (success or failure):
```bash
rm -f /tmp/gigo-gemma-task-{N}.json
```
```

- [ ] **Step 4: Write the response parsing section**

```markdown
## Response Parsing

### Extraction

1. Parse curl JSON output to extract `choices[0].message.content`
2. Split content on triple-backtick markers
3. For each code block:
   - First token after opening backticks = language identifier
   - First code line = file path as comment (`# path/to/file.rb`, `// path/to/file.ts`, `-- file.sql`)
   - Strip comment character and whitespace → bare path
   - Remaining lines = file content
4. Produce ordered list of `{path, content, language}` tuples

### Validation

Valid parse requires:
- At least one code block extracted
- At least one block with a parseable file path (not single words, sentences, or empty strings)

If validation fails → escalate to Claude (Layer 2).

### Edge Cases

| Case | Handling |
|---|---|
| No file path header | Map by position to task's Output Files list. Skip if no match. |
| Nested code blocks | Match outermost delimiters only. |
| Empty code block | Skip. |
| Spaces in path | Preserve as-is. |
| Multiple blocks for same file | Use last occurrence. |
```

- [ ] **Step 5: Write the error handling section**

```markdown
## Error Handling & Escalation

Gemma gets first attempt + one retry. Claude is the safety net. Every routing change is announced.

### Layer 1: API Failure

**Trigger:** Connection refused, HTTP error, curl timeout.
**Action:** Route task to Claude subagent (model per model-selection.md).
**Announce:** "Gemma API unavailable for Task {N}, routing to Claude ({model})."

If the API fails on the first task, disable local routing for all remaining tasks.

### Layer 2: Parse Failure

**Trigger:** Response doesn't contain valid code blocks.
**Action:** Route to Claude subagent.
**Announce:** "Gemma response couldn't be parsed for Task {N}, routing to Claude ({model})."

### Layer 3: Test Failure

**Trigger:** Applier reports BLOCKED with test output.
**Action:**
1. Re-prompt Gemma with fix prompt (include test output). One retry.
2. If retry fails → escalate to Claude at one model tier above model-selection.md default.
**Announce:** "Gemma retry failed for Task {N}, escalating to Claude ({higher_model})."

### Layer 4: Review Failure

**Trigger:** gigo:verify finds issues after applier reports DONE.
**Action:** Standard triage:
- Auto-fix → re-prompt Gemma (one shot). If still fails → Claude fix subagent.
- Ask-operator → surface as usual.
**Announce escalation:** "Gemma couldn't resolve review feedback for Task {N}, dispatching Claude fix."
```

- [ ] **Step 6: Verify and commit**

Verify the file:
- Is under 200 lines
- Contains all five sections: Detection, Prompt Formatting, API Call, Response Parsing, Error Handling
- No placeholder text (TBD, TODO, etc.)
- All code blocks have correct syntax

```bash
git add skills/execute/references/local-model-routing.md
git commit -m "feat: add local model routing reference for gigo:execute"
```

---

### Task 2: Add Prompt Templates

**blocks:** 5
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 3, 4)

**Files:**
- Modify: `skills/execute/references/teammate-prompts.md`

Add two new templates: the applier prompt (haiku writes Gemma's output) and the Gemma fix prompt (re-prompt on failure).

- [ ] **Step 1: Add applier prompt template**

After the existing "Tier 1: Operator-Resolved Re-dispatch" section (after line 99), add a new top-level section:

```markdown
---

## Applier Prompt

### Local Model Routing: Haiku Applier

When a task is routed through a local model (see `references/local-model-routing.md`), the local model generates code and a haiku subagent applies it. Dispatch with `isolation: "worktree"`:

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
[IF test_command exists:]
4. Run: {test_command}
5. If tests fail, report the test output — do NOT attempt to fix the code.
[END IF]
6. Commit all changes to this branch.
7. Report back with the list of files written.

Status: DONE | BLOCKED (with reason — include full test output if tests failed)
```
```

- [ ] **Step 2: Add Gemma fix prompt template**

After the applier prompt section, add:

```markdown
### Local Model Routing: Gemma Fix Prompt

When a Gemma-generated task fails (test failure or review issues), re-prompt Gemma with this template. Uses the same system prompt (harness) as the original attempt:

```
The previous code had issues.

## Original Task
{original task description from plan}

## Issue
{test failure output OR review feedback — pasted verbatim}

## Previous Code
{the code blocks from the failed attempt}

## Current Files
{same inline source files as original prompt}

Fix the issues. Output corrected code blocks only.
```
```

- [ ] **Step 3: Verify and commit**

Verify:
- Both templates are after the existing sections
- The "Prompt Design Rationale" section at the end of the file is preserved
- No existing content was modified

```bash
git add skills/execute/references/teammate-prompts.md
git commit -m "feat: add applier and Gemma fix prompt templates"
```

---

### Task 3: Update Checkpoint Format

**blocks:** 5
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 4)

**Files:**
- Modify: `skills/execute/references/checkpoint-format.md`

Add the optional `model` field for production tracing.

- [ ] **Step 1: Add model to the Fields table**

In the `## Fields` table (after the `tier` row at line 39), add:

```markdown
| `model` | `gemma-26b`, `gemma-31b`, `claude-haiku`, `claude-sonnet`, `claude-opus` | Which model generated the code (optional, omit when local routing disabled) |
```

- [ ] **Step 2: Add an example showing the model field**

After the "Task blocked on operator decision" example (line 30), add:

```markdown
### Task completed via local model:

```
- [x] **Step 5: Write endpoint**
<!-- checkpoint: sha=jkl3456 status=done reviewed=pass tier=1 model=gemma-26b -->
```
```

- [ ] **Step 3: Add resume note**

At the end of the `## Resume Detection Procedure` section (after line 87), add a paragraph:

```markdown
**Model field on resume:** The `model` field is informational only. Resume logic ignores it — it doesn't affect which model handles a retry. Its purpose is production tracing: when a task's output quality is questioned, the model field answers "who wrote this?"
```

- [ ] **Step 4: Verify and commit**

Verify:
- Fields table has 5 rows (sha, status, reviewed, tier, model)
- The new example is consistent with existing example format
- No existing content was modified

```bash
git add skills/execute/references/checkpoint-format.md
git commit -m "feat: add model field to checkpoint format for routing traceability"
```

---

### Task 4: Update Model Selection

**blocks:** 5
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 3)

**Files:**
- Modify: `skills/execute/references/model-selection.md`

Add a section documenting the local model override.

- [ ] **Step 1: Add local model override section**

Before the existing `## Task Complexity → Model` heading (line 3), insert:

```markdown
## Local Model Override

When local routing is enabled (local model detected at startup, operator chose "Subagents + local model"):

- **All tasks route to the local Gemma model first**, regardless of complexity tier
- The complexity table below is used ONLY for Claude fallback and escalation
- On escalation (Gemma fails after retry), use one tier above the table's recommendation:
  - Table says haiku → escalate to sonnet
  - Table says sonnet → escalate to opus
  - Table says opus → escalate to opus (ceiling)

When local routing is disabled (no local model, or operator chose "Subagents only"), use the table below as current behavior — no change.

See `references/local-model-routing.md` for the full routing procedure.

---

```

- [ ] **Step 2: Verify and commit**

Verify:
- New section appears before the existing table
- Existing content is unchanged
- The `## For Review Subagents` section at the bottom is preserved (review always uses sonnet, never local model)

```bash
git add skills/execute/references/model-selection.md
git commit -m "feat: add local model override to model selection reference"
```

---

### Task 5: Integrate into SKILL.md

**blocks:** []
**blocked-by:** 1, 2, 3, 4
**parallelizable:** false

**Files:**
- Modify: `skills/execute/SKILL.md`

Wire the routing into the execute skill. Four integration points: detection at startup, execution options, dispatch flow, and completion summary.

- [ ] **Step 1: Add detection step to "Before Starting"**

After step 2 ("Read the full plan", which ends with the checkpoint scanning bullet), add a new step 2.5. Insert after line 26 (the "If no checkpoints" bullet):

```markdown
2.5. **Detect local model.** Check for a running local model and Gemma harness. If both present, local routing is available as an execution option. See `references/local-model-routing.md` for the detection procedure. Detection runs once — not per-task.
```

- [ ] **Step 2: Update execution options**

Replace the current execution options block (lines 28-35, from "Present execution options" to the end of the quoted block) with:

```markdown
3. **Present execution options.** Let the operator choose their tier:

   **When local model detected (step 2.5 passed):**
   > "Local model detected: {model_id} at localhost:8080. Choose:
   > 1. **Subagents + local model** (recommended) — Gemma generates, haiku applies in worktrees
   > 2. **Subagents only** — Claude subagents (current behavior)
   > 3. **Inline** — sequential in this session"

   **When no local model detected:**
   > "Ready to execute. Available options:
   > 1. **Subagents** (recommended) — fresh worker per task, parallel dispatch for independent tasks, lead-managed review.
   > 2. **Inline** — sequential in this session, no isolation. Good for small plans or debugging.
   >
   > Which route?"

   **Default behavior:** Use subagents + local model for plans with 3+ tasks when local is available. Use subagents for 3+ tasks when local is not available. Use inline for plans with 1-2 tasks. Present the choice to the operator only if they haven't already specified a preference. Do NOT silently choose inline for larger plans just because it's easier.
```

- [ ] **Step 3: Add local routing to Tier 1 dispatch flow**

After the existing "Execution Flow" heading and before step 1 ("Identify the wave"), insert a conditional block. Add after line 49 (the "For each **wave** of unblocked tasks:" line):

```markdown
   **If local routing is enabled** (operator chose option 1), the wave flow changes at step 3. See `references/local-model-routing.md` for the full procedure. Summary:
   - Steps 1-2 (identify wave, pre-flight): unchanged
   - Step 3 becomes: sequentially call the local model API for each task, parse responses
   - Step 4 becomes: dispatch haiku applier subagents in parallel (for tasks with successful Gemma responses) alongside Claude subagents (for tasks that failed parsing). All use `isolation: "worktree"`.
   - Steps 5-8 (review, triage, merge, update wave): unchanged

   **If local routing is not enabled**, the existing dispatch flow below applies unchanged.
```

- [ ] **Step 4: Add routing stats to completion summary**

In the "When All Tasks Complete" section (line 166), after bullet 1 ("Synthesize results"), add:

```markdown
   1.5. **Routing stats** (when local routing was active). Include in the summary:
      > "N tasks completed. M via Gemma {model_id} (avg Xs generation), K via Claude (reasons: {per-task reasons})."
      Only report this when local routing was used. When all tasks ran via Claude, omit.
```

- [ ] **Step 5: Add reference pointer**

In the `## References` section at the end of the file, add:

```markdown
- `references/local-model-routing.md` — Local model detection, prompt formatting, API call, response parsing, and escalation protocol. Loaded when local routing is enabled.
```

- [ ] **Step 6: Verify and commit**

Verify:
- SKILL.md is under 500 lines (was 206, adding ~40 lines → ~246)
- All existing behavior is preserved when local routing is disabled
- The "Tier 2: Inline" section is unchanged
- The "Future: Agent Teams" section is unchanged
- All new content is conditional on local routing being enabled
- Reference pointer is in the References section

```bash
git add skills/execute/SKILL.md
git commit -m "feat: integrate local model routing into gigo:execute"
```

---

## Verification

After all tasks are complete:

1. **Read all modified files** — verify consistency between SKILL.md pointers and reference file content
2. **Line count check** — SKILL.md under 500 lines, local-model-routing.md under 200 lines, no reference file over 200 lines
3. **Cross-reference check** — all R1-R11 requirements from the spec map to content in the plan's output files
4. **Backward compatibility** — when no local model is running, execute behaves identically to before this change. No detection errors, no missing options, no changed output.

**Done when:** All five files are committed, the execute skill supports three tiers (subagents + local, subagents only, inline), and the routing reference covers detection through escalation.

<!-- approved: plan 2026-04-13T02:15:11 by:Eaven -->
