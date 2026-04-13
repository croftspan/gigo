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

---

## Prompt Formatting

For each task routed to Gemma, construct a two-part prompt.

### System Message

Read `.claude/references/gemma-harness.md`. Extract everything after the first `---` separator (the harness content, not the header/usage instructions).

### User Message

Format the task description for single-turn execution:

1. **Strip plan metadata.** Remove the `blocks:`, `blocked-by:`, `parallelizable:` lines and the `**Files:**` section (including all Create/Modify/Test lines). These are consumed by the execute lead for dispatch — Gemma doesn't need them.

2. **Flatten checkbox steps.** Convert `- [ ] **Step N: Action**` to plain imperative sentences. Drop step numbering, bold formatting, and checkbox syntax. Keep the content.

3. **Drop non-execution content.** Remove:
   - Commit steps (any step whose content is only "Commit" or a git command)
   - Verification commands (`Run: ...` lines)
   - Expected result lines (`Expected: PASS` or similar)
   Retain surrounding prose about what the code should do or how it should behave.

4. **Preserve code blocks.** Code blocks inside steps are kept verbatim — they are the specification.

5. **Prepend addendum context.** If prior tasks have "What Was Built" addendums with relevant context (interface changes, renamed exports, deviations), prepend as:
   ```
   Background: [relevant addendum content]
   ```
   This replaces the separate "Context" section used in Claude subagent prompts. Gemma processes a flat prompt better than structured sections.

6. **Assemble.** The user message is:
   - Formatted task description (steps 1-5 above)
   - `## Current Files` section with subsections for each file (`### {file_path}` followed by file contents)
   - `## Output Files` section listing paths to produce

### File Selection

Which files to inline:

1. Files in the task's **Files:** section — for Modify targets, read and include current contents. For Create targets, list in Output Files.
2. Schema/type definitions — when the task involves data model changes, include schema files (schema.rb, schema.prisma, etc.).
3. Dependency context — files listed in "What Was Built" addendums from prior tasks (only changed files, not full addendums).
4. Imported modules — if the task mentions importing from or depending on specific modules, include those files.

Do not include config files or files the task doesn't reference. Include test helper and factory files (e.g., `spec/rails_helper.rb`, `spec/factories/*.rb`, `test/test_helper.*`, `conftest.py`) when the task includes writing tests — Gemma needs the project's test setup to produce compatible specs. Only include if the files exist.

**File ordering** within `## Current Files`:
1. Files the task creates or modifies (most relevant — Gemma needs to see what it's changing)
2. Schema/type definitions (structural context)
3. Files from prior task addendums (changed dependencies)
4. Test helpers (only if task has test steps)

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

**Schema truncation:** When a schema/type definition file exceeds ~2000 tokens (~8000 characters), truncate to the table(s) or model(s) relevant to the current task. For example, if the task adds a column to `orders`, include only the `create_table "orders"` block from `schema.rb`, not the entire file. The execute lead (Claude) judges which sections are relevant — this varies by schema format (ActiveRecord, Prisma, TypeORM, etc.).

---

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

---

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

---

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

Track consecutive parse failures. If 2 consecutive tasks fail parsing, disable local routing for all remaining tasks — parse failures are usually systematic (wrong harness, model mismatch), not per-task. Reset the counter on any successful parse.
**Announce disable:** "Local model disabled — 2 consecutive parse failures. Remaining tasks use Claude."

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
