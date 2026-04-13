# Spec-to-Prompt Formatting — Design Spec

**Design brief:** `.claude/plans/sleepy-forging-planet.md`

## Original Request

> Read briefs/08-spec-to-prompt-formatting.md — it has the full context.
> TL;DR: gigo:spec writes tasks for Claude (assumes file reading, multi-turn, judgment). Gemma gets one prompt, produces one response. Tasks need a Gemma-compatible format: explicit instructions, relevant source files inlined, expected output files listed. The hard part is source file selection — too few and Gemma produces incompatible code, too many and you blow the context window. Needs AB testing: same tasks, Claude-format vs Gemma-format, measure spec compliance. Depends on briefs 06-07.

## Problem Statement

Plan tasks written by `gigo:spec` contain structural noise (plan metadata, checkbox syntax, verification commands) and can contain Claude-style ambiguity that Gemma cannot resolve. When `gigo:execute` routes tasks to a local Gemma model, the current "pasted verbatim" approach wastes context tokens on non-execution content and produces lower spec compliance when task descriptions are vague.

Two complementary fixes: raise spec quality so tasks are explicit enough for any executor, then format them mechanically for single-turn execution.

## Requirements

### R1: Explicitness Quality Gate

Add an explicitness check to the plan self-review in `skills/spec/references/planning-procedure.md`. This applies to ALL plans, not just Gemma-targeted ones.

**R1.1:** New section 8b ("Explicitness Check") after the existing section 8. Each task step must:
- Name every field, column, or property being added/changed with its type and default
- Specify validation rules with exact constraints — not "add validations" but "validate: inclusion of `payment_status` in `['unpaid', 'paid', 'failed', 'refunded']`"
- Name every scope or method with its implementation logic — not "add a scope for paid orders" but "add scope `paid` → `where(payment_status: 'paid')`"
- Specify test cases with concrete scenarios — not "write specs covering transitions" but "spec: happy path (create with status 'paid') + error case (status 'invalid' rejected)"

**R1.2:** New section 9d in the plan self-review. The test: read each task in isolation (ignore the plan header and other tasks). Could a model execute it without reading any project files or asking questions? If a step says "update with validations" without naming the validations, it fails. Apply section 8b.

**R1.3:** Section 8b is a quality bar, not a format change. The existing task format (metadata, checkboxes, code blocks) is unchanged. Tasks simply must be more explicit within that format.

### R2: Mechanical Task Formatting

Replace the "pasted verbatim" instruction in `skills/execute/references/local-model-routing.md` (Prompt Formatting > User Message section) with a formatting procedure.

**R2.1: Strip plan metadata.** Remove the `blocks:`, `blocked-by:`, `parallelizable:` lines and the `**Files:**` section (including all Create/Modify/Test lines). These are consumed by the execute lead for dispatch decisions — Gemma doesn't need them.

**R2.2: Flatten checkbox steps.** Convert `- [ ] **Step N: Action**` to plain imperative sentences. Drop step numbering, bold formatting, and checkbox syntax. Keep the content of each step.

**R2.3: Drop non-execution content.** Remove:
- Commit steps (any step whose only content is "Commit" or "git add ... && git commit ...")
- Verification commands (`Run: ...` lines)
- Expected result lines (`Expected: PASS` or `Expected: ...`)

Retain surrounding prose about what the code should do or how it should behave.

**R2.4: Preserve code blocks.** Code blocks inside steps are kept verbatim — they are the specification, not decoration.

**R2.5: Prepend addendum context.** If prior tasks have "What Was Built" addendums with relevant context (interface changes, renamed exports, deviations), prepend as:
```
Background: [relevant addendum content]
```
This replaces the separate "Context" section used in Claude subagent prompts (from `teammate-prompts.md`). Gemma processes a flat prompt better than structured sections.

**R2.6: Assemble.** The final user message is, in order:
1. Formatted task description (steps R2.1–R2.5 above)
2. `## Current Files` section with subsections for each file (`### {file_path}` followed by file contents)
3. `## Output Files` section listing paths to produce

### R3: Enhanced File Selection

Extend the file selection heuristic in `skills/execute/references/local-model-routing.md`.

**R3.1: Conditional test helper inclusion.** Include test helper and factory files when the task includes writing tests. Examples: `spec/rails_helper.rb`, `spec/factories/*.rb`, `test/test_helper.*`, `conftest.py`, `jest.config.*`. Only include if the files exist. The current line "Do not include test helpers, config files, or files the task doesn't reference" becomes "Do not include config files or files the task doesn't reference. Include test helper and factory files when the task includes writing tests." Config file and unreferenced file exclusions are preserved.

**R3.2: Schema truncation.** When a schema/type definition file exceeds ~2000 tokens (~8000 characters), truncate to the table(s) or model(s) relevant to the current task. This is guidance for the execute lead (Claude), not a rigid algorithm — different schema formats (ActiveRecord, Prisma, TypeORM) have different structures.

**R3.3: File ordering.** Within the `## Current Files` section, order files by relevance:
1. Files the task creates or modifies (most relevant — Gemma needs to see what it's changing)
2. Schema/type definitions (structural context)
3. Files from prior task addendums (changed dependencies)
4. Test helpers (only if task has test steps)

### R4: Gemma Fix Prompt Update

Update the Gemma Fix Prompt template in `skills/execute/references/teammate-prompts.md`.

**R4.1:** The `## Original Task` section in the fix prompt must use the formatted task description (per R2), not the raw plan text. Consistency: Gemma sees the same format on retry as on first attempt.

**R4.2:** If the original task had addendum context (R2.5), include the same `Background:` prefix in the fix prompt's `## Original Task` section.

### R5: AB Test Eval

Create an eval comparing verbatim vs formatted task descriptions.

**R5.1:** Create `evals/test-task-formatting.py`. The script:
- Loads task fixtures from `evals/prompts/task-formatting.json`
- Loads the Gemma harness from the rails-api-gemma fixture as system prompt
- Loads source files from `evals/fixtures/rails-api-gemma/` as inline context
- For each fixture, sends both variants (verbatim and formatted) to the local model API
- Scores responses using structural checks (no LLM-as-judge)
- Prints per-task and aggregate comparison tables

**R5.2:** Create `evals/prompts/task-formatting.json` with 3 task fixtures. Each fixture:
```json
{
  "name": "descriptive name",
  "task_verbatim": "raw plan task text with all metadata and checkboxes",
  "task_formatted": "mechanically formatted version per R2",
  "output_files": ["path/to/expected/output1.rb", "path/to/output2.rb"],
  "spec_checks": ["string_to_grep_1", "string_to_grep_2"]
}
```

Source files for `## Current Files` are loaded at runtime from the rails-api-gemma fixture directory, not embedded in the JSON. This avoids duplicating large file contents.

**R5.3:** Scoring metrics (structural, deterministic):
- **Parse success** (bool): at least one code block with a recognizable file path header extracted
- **Path accuracy** (float 0-1): fraction of `output_files` that appear as file path headers in code blocks
- **Spec compliance** (float 0-1): fraction of `spec_checks` strings found in the output
- **Code ratio** (float 0-1): (lines inside code blocks) / (total output lines)

**R5.4:** CLI follows the pattern of `evals/ab-test-gemma.py`: argparse with `--server` (default `http://localhost:8080`), `--max-tokens` (default 4096), `--temp` (default 0.0), `--runs` (default 1). Adds `--fixture N` to run a single fixture by index. Model name for R5.5's results directory is auto-detected by querying `GET {server}/v1/models` at startup (same `detect_model()` pattern as `ab-test-gemma.py`), not a CLI argument.

**R5.5:** Results saved to `evals/results/task-formatting-{model}-temp{temp}/` directory with per-fixture JSON files containing both responses and scores.

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| writes (tasks for Claude) | R1: Explicitness Quality Gate | ✅ |
| gets (one prompt, one response) | R2: Mechanical Task Formatting | ✅ |
| need (Gemma-compatible format) | R1 + R2 combined | ✅ |
| inlined (source files) | R3: Enhanced File Selection | ✅ |
| listed (output files) | R2.6: Assemble | ✅ |
| testing (AB) | R5: AB Test Eval | ✅ |
| measure (spec compliance) | R5.3: Scoring metrics | ✅ |

## Conventions

### Section Numbering
New sections in `planning-procedure.md` use gap numbering: 8b follows 8, 9d follows 9c. No renumbering of existing sections.

### Prose Style
All new content in reference files uses the existing style: imperative sentences, markdown headers, numbered or bulleted lists. No passive voice. No "should" — use direct imperatives.

### Eval Script Conventions
Follow `evals/ab-test-gemma.py` patterns: argparse CLI, `requests` library for API calls, JSON fixtures, tabulated console output. No external dependencies beyond Python standard library + requests. Results directory under `evals/results/`.

### Task Formatting Boundary
The formatting procedure (R2) is a structural transformation the execute lead (Claude) performs in-context when building the Gemma API request. It is not a separate script, tool, or LLM call. The lead reads the plan task, applies the steps, and writes the formatted text into the request JSON.

## Boundaries

- **Spec ↔ Execute:** R1 lives in `gigo:spec` (planning-procedure.md). R2-R4 live in `gigo:execute` (local-model-routing.md, teammate-prompts.md). The spec produces explicit tasks; execute formats them mechanically.
- **Formatting ↔ Harness:** R2 produces the user message. The harness (brief 06) produces the system message. Independent, composed at API call time.
- **Eval ↔ Production:** R5 validates the hypothesis but does not gate R1-R4. The formatting procedure ships regardless of eval results. The eval informs future refinement.

## Out of Scope

- `--executor local` flag on `gigo:spec` — rejected: dual-format plans create maintenance burden
- Claude-rewrites-for-Gemma translation step — rejected: defeats cost savings of local routing
- Import chain following — deferred: cross-language code analysis is separate scope
- Eval CI integration — deferred: requires GPU hardware not available in CI

<!-- approved: spec 2026-04-13T03:20:22 by:Eaven -->
