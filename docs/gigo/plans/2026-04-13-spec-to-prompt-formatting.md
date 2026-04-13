# Spec-to-Prompt Formatting — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-13-spec-to-prompt-formatting-design.md`

**Goal:** Make plan tasks explicit enough for any executor and format them mechanically for single-turn Gemma execution.

**Execution Pattern:** Supervisor

**Architecture:** Two complementary reference file updates (spec-side quality gate + execute-side formatting procedure), one prompt template update, and an AB test eval script with fixtures.

---

### Task 1: Add Explicitness Quality Gate to Planning Procedure

**blocks:** 4
**blocked-by:** []
**parallelizable:** true (with Task 2)

**Files:**
- Modify: `skills/spec/references/planning-procedure.md`

- [x] **Step 1: Add section 8b after section 8**

Insert the following after the existing section 8 ("No Placeholders") block, before section 9:

```markdown
## 8b. Explicitness Check

Every task must be executable by a model that cannot read files or ask questions. After writing each task, verify:

- Every field, column, or property names its type and default — not "add a status column" but "add `payment_status` column (string, default: 'unpaid')"
- Every validation names its constraint — not "add validations" but "validate: inclusion of `payment_status` in `['unpaid', 'paid', 'failed', 'refunded']`"
- Every scope or method names its logic — not "add a scope for paid orders" but "add scope `paid` → `where(payment_status: 'paid')`"
- Every test case names its scenario — not "write specs covering transitions" but "spec: happy path (create with status 'paid') + error case (status 'invalid' rejected)"

Section 8 catches placeholders ("TBD", "add appropriate error handling"). This section catches subtler ambiguity that passes section 8 but fails when no agent can ask "which validations?"
```

- [x] **Step 2: Add section 9d to the self-review**

Insert after the existing `**9c. Type consistency:**` paragraph, before the "Fix issues inline" line:

```markdown
**9d. Explicitness check:** For each task, read only the task text (ignore the plan header and other tasks). Could a model execute it without reading any project files or asking questions? If a step says "update with validations" without naming the validations, fix it. Apply section 8b.
```

- [x] **Step 3: Commit**

```bash
git add skills/spec/references/planning-procedure.md
git commit -m "feat: add explicitness quality gate to planning procedure (R1)"
```

#### What Was Built
- **Deviations:** None
- **Review changes:** None
- **Notes for downstream:** Section 8b and 9d are now live in planning-procedure.md. Section 8b defines the explicitness bar; 9d adds it to the self-review checklist.

<!-- checkpoint: sha=083fed4 status=done reviewed=pass tier=1 -->

---

### Task 2: Add Task Formatting Procedure and Enhanced File Selection

**blocks:** 3, 4
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 3)

**Files:**
- Modify: `skills/execute/references/local-model-routing.md`

- [x] **Step 1: Replace the User Message section**

Replace the current "User Message" section (lines 39-44 of local-model-routing.md):

```
### User Message

Format:
- Task description from plan (pasted verbatim, including all steps)
- Then a "## Current Files" section with subsections for each file (`### {file_path}` followed by file contents)
- Then a "## Output Files" section listing paths to produce
```

With:

```markdown
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
```

- [x] **Step 2: Update the File Selection section**

Replace the current line (line 55):
```
Do not include test helpers, config files, or files the task doesn't reference.
```

With:
```markdown
Do not include config files or files the task doesn't reference. Include test helper and factory files (e.g., `spec/rails_helper.rb`, `spec/factories/*.rb`, `test/test_helper.*`, `conftest.py`) when the task includes writing tests — Gemma needs the project's test setup to produce compatible specs. Only include if the files exist.
```

- [x] **Step 3: Add file ordering guidance**

After the updated file selection exclusion line (from Step 2), add:

```markdown
**File ordering** within `## Current Files`:
1. Files the task creates or modifies (most relevant — Gemma needs to see what it's changing)
2. Schema/type definitions (structural context)
3. Files from prior task addendums (changed dependencies)
4. Test helpers (only if task has test steps)
```

- [x] **Step 4: Add schema truncation to the Context Budget section**

After the existing priority list (lines 67-72, ending with "If still over → skip local routing for this task, dispatch to Claude"), add:

```markdown
**Schema truncation:** When a schema/type definition file exceeds ~2000 tokens (~8000 characters), truncate to the table(s) or model(s) relevant to the current task. For example, if the task adds a column to `orders`, include only the `create_table "orders"` block from `schema.rb`, not the entire file. The execute lead (Claude) judges which sections are relevant — this varies by schema format (ActiveRecord, Prisma, TypeORM, etc.).
```

- [x] **Step 5: Commit**

```bash
git add skills/execute/references/local-model-routing.md
git commit -m "feat: add task formatting procedure and enhanced file selection (R2, R3)"
```

#### What Was Built
- **Deviations:** None
- **Review changes:** None
- **Notes for downstream:** The "User Message" section in local-model-routing.md now has a 6-step formatting procedure (strip metadata, flatten checkboxes, drop non-execution content, preserve code blocks, prepend addendum context, assemble). File selection now conditionally includes test helpers. File ordering and schema truncation guidance added to Context Budget section. Task 3 should reference "per local-model-routing.md formatting procedure" in the fix prompt.

<!-- checkpoint: sha=01e9e21 status=done reviewed=pass tier=1 -->

---

### Task 3: Update Gemma Fix Prompt

**blocks:** 4
**blocked-by:** 2
**parallelizable:** false

**Files:**
- Modify: `skills/execute/references/teammate-prompts.md`

- [x] **Step 1: Update the Gemma Fix Prompt template**

Replace the current Gemma Fix Prompt template (lines 141-157 of teammate-prompts.md):

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

With:

```
The previous code had issues.

## Original Task
{formatted task description — same formatting as the original Gemma prompt (plan metadata stripped, checkboxes flattened, non-execution content dropped per local-model-routing.md formatting procedure). If the original task had addendum context, include the same Background: prefix.}

## Issue
{test failure output OR review feedback — pasted verbatim}

## Previous Code
{the code blocks from the failed attempt}

## Current Files
{same inline source files as original prompt}

Fix the issues. Output corrected code blocks only.
```

- [x] **Step 2: Commit**

```bash
git add skills/execute/references/teammate-prompts.md
git commit -m "feat: update Gemma fix prompt to use formatted task text (R4)"
```

#### What Was Built
- **Deviations:** None
- **Review changes:** None
- **Notes for downstream:** The Gemma Fix Prompt now references the formatting procedure in local-model-routing.md and includes the Background: prefix for addendum context. Task 4's eval fixtures should produce formatted task text consistent with this procedure.

<!-- checkpoint: sha=52042c7 status=done reviewed=pass tier=1 -->

---

### Task 4: Create AB Test Eval

**blocks:** []
**blocked-by:** 1, 2, 3
**parallelizable:** false

**Files:**
- Create: `evals/test-task-formatting.py`
- Create: `evals/prompts/task-formatting.json`

- [x] **Step 1: Create the task fixtures file**

Create `evals/prompts/task-formatting.json` with 3 fixtures based on Rails API tasks that exercise different formatting gaps. Each fixture has:
- `name`: descriptive identifier
- `task_verbatim`: raw plan task text with `blocks:`, `blocked-by:`, `parallelizable:`, `**Files:**`, checkbox steps (`- [ ] **Step N:**`), commit step, `Run:` / `Expected:` lines
- `task_formatted`: same task with plan metadata stripped, checkboxes flattened to imperative sentences, commit/verify steps removed, code blocks preserved
- `output_files`: list of file paths Gemma should produce
- `spec_checks`: list of strings to grep for in Gemma's output (column names, method names, validation calls, scope definitions)

Fixture 1 — "Add payment status column":
- Verbatim includes vague "Update the Order model with validations" and "Add a scope for paid orders"
- Formatted replaces with "Validate: inclusion of `payment_status` in `['unpaid', 'paid', 'failed', 'refunded']`" and "Add scope `paid` → `where(payment_status: 'paid')`"
- spec_checks: `["payment_status", "validates", "scope :paid", "def change", "add_column"]`
- output_files: `["db/migrate/add_payment_status_to_orders.rb", "app/models/order.rb", "spec/requests/orders_spec.rb"]`

Fixture 2 — "Add email validation to users":
- Verbatim has "Add validations to the User model" and "Write request specs"
- Formatted has "Validate: presence of `email`, format with `URI::MailTo::EMAIL_REGEXP`, uniqueness (case-insensitive)"
- spec_checks: `["validates", "email", "uniqueness", "format", "describe"]`
- output_files: `["app/models/user.rb", "spec/requests/users_spec.rb"]`

Fixture 3 — "Add pagination to orders index":
- Verbatim has "Add pagination to the index action" and "Update specs"
- Formatted has "Add `page` param (default: 1) and `per_page` param (default: 25, max: 100). Use `.limit(per_page).offset((page - 1) * per_page)`. Return `X-Total-Count` header."
- spec_checks: `["page", "per_page", "limit", "offset", "X-Total-Count", "describe"]`
- output_files: `["app/controllers/orders_controller.rb", "spec/requests/orders_spec.rb"]`

- [x] **Step 2: Create the eval script**

Create `evals/test-task-formatting.py` following the `ab-test-gemma.py` pattern:

**Imports:** `argparse`, `json`, `sys`, `time`, `pathlib.Path`, `requests`

**Functions to reuse from ab-test-gemma.py pattern:**
- `check_server(url)` — GET `/health`, return bool
- `detect_model(url)` — GET `/v1/models`, extract `data[0].id`, fallback "local"
- `generate(url, prompt, system, max_tokens, temp)` — POST `/v1/chat/completions`, return (content, stats)

**New functions:**
- `load_fixtures(path)` — load and return parsed JSON from task-formatting.json
- `build_system_prompt(fixture_dir)` — read `CLAUDE.md` from the rails-api-gemma fixture, extract content after `---` separator (the harness)
- `build_source_context(fixture_dir)` — reuse the pattern from ab-test-gemma.py: recursively gather source files, wrap as markdown code blocks with path headers
- `build_user_message(task_text, source_context, output_files)` — assemble: task text + `## Current Files\n\n{source_context}` + `## Output Files\n\n{bullet list of output_files}`
- `score_response(text, fixture)` — structural scoring:
  - `parse_success`: count code blocks (triple-backtick pairs), check at least one has a recognizable file path (line starting with `#` comment containing `/`)
  - `path_accuracy`: for each path in `fixture["output_files"]`, check if any code block header contains a substring match. Return fraction found.
  - `spec_compliance`: for each string in `fixture["spec_checks"]`, check if it appears in `text` (case-insensitive). Return fraction found.
  - `code_ratio`: count lines inside code blocks / total lines. Return float.
- `print_results(results)` — tabulated comparison: fixture name, variant, parse_success, path_accuracy, spec_compliance, code_ratio

**Main flow:**
1. Parse args: `--server`, `--max-tokens`, `--temp`, `--runs`, `--fixture`
2. `check_server()` — exit if unavailable
3. `detect_model()` — store for results dir naming
4. Load fixtures from `evals/prompts/task-formatting.json`
5. Build system prompt from `evals/fixtures/rails-api-gemma/CLAUDE.md`
6. Build source context from `evals/fixtures/rails-api-gemma/` source files
7. For each fixture (or single if `--fixture N`):
   a. For each variant (`verbatim`, `formatted`):
      - Build user message: `build_user_message(fixture[variant_key], source_context, fixture["output_files"])`
      - For each run (1 to `--runs`):
        - Call `generate(url, user_message, system_prompt, max_tokens, temp)`
        - Score with `score_response(content, fixture)`
        - Store result
   b. Print comparison table for this fixture
8. Print aggregate summary: average scores per variant across all fixtures
9. Save results to `evals/results/task-formatting-{model}-temp{temp}/` as JSON

**CLI:**
```python
parser = argparse.ArgumentParser(description="A/B test: verbatim vs formatted task descriptions")
parser.add_argument("--server", default="http://localhost:8080")
parser.add_argument("--max-tokens", type=int, default=4096)
parser.add_argument("--temp", type=float, default=0.0)
parser.add_argument("--runs", type=int, default=1)
parser.add_argument("--fixture", type=int, default=None, help="Run single fixture by index (1-based)")
```

- [x] **Step 3: Verify the script runs**

Run: `python3 evals/test-task-formatting.py --server http://localhost:8080 --fixture 1`

If llama-server is not running, verify the script exits cleanly with "ERROR: llama-server not reachable at http://localhost:8080" (matching ab-test-gemma.py's error handling).

- [x] **Step 4: Commit**

```bash
git add evals/test-task-formatting.py evals/prompts/task-formatting.json
git commit -m "feat: add task formatting AB test eval (R5)"
```

#### What Was Built
- **Deviations:** None
- **Review changes:** Removed duplicate `## Output Files` sections from all 3 `task_formatted` fields in task-formatting.json — `build_user_message()` already appends output files, so having them in the fixture text produced a confound (formatted variant had output files listed twice). Fixed in commit 0c1fac2.
- **Notes for downstream:** Eval script (`evals/test-task-formatting.py`) follows the `ab-test-gemma.py` pattern — same `check_server`, `detect_model`, `generate` functions. Auto-detects model via `/v1/models` endpoint. Exits cleanly if llama-server is not running. Fixtures are in `evals/prompts/task-formatting.json`.

<!-- checkpoint: sha=0c1fac2 status=done reviewed=pass tier=1 -->

---

**Done when:**
- `planning-procedure.md` has sections 8b and 9d
- `local-model-routing.md` has the formatting procedure instead of "pasted verbatim," enhanced file selection with conditional test helpers, file ordering guidance, and schema truncation
- `teammate-prompts.md` Gemma Fix Prompt uses formatted task text
- `test-task-formatting.py` runs and produces comparison output (or exits cleanly if no local model)
- All 5 requirements (R1-R5) from the spec are implemented

<!-- approved: plan 2026-04-13T03:25:00 by:Eaven -->
