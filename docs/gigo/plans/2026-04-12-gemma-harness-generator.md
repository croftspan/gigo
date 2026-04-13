# Gemma Harness Generator — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-12-gemma-harness-generator-design.md`

**Goal:** Add `--include-gemma` flag to gigo:gigo that generates a lean Gemma-compatible harness alongside the standard assembly

**Execution Pattern:** Supervisor

**Architecture:** Hub-and-spoke addition to gigo:gigo. New reference file contains the generation algorithm (spoke). SKILL.md gets ~15 lines of pointers (hub). Eval runner gets domain-awareness and generated-harness testing support. Two independent workstreams: skill-side (Tasks 1-3) and eval-side (Tasks 4-5).

---

### Task 1: Create Generator Reference File

**blocks:** 2, 3
**blocked-by:** []
**parallelizable:** true (with Tasks 4, 5)

**Files:**
- Create: `skills/gigo/references/gemma-harness-generator.md`

- [ ] **Step 1: Write the generator reference**

Create `skills/gigo/references/gemma-harness-generator.md` with the following structure. This is the complete generation algorithm that Step 6.75 in SKILL.md will point to.

```markdown
# Gemma Harness Generator

When the `--include-gemma` flag is active, generate a lean harness after Step 6.5
completes. This harness is optimized for Gemma-class models that execute well with
imperative rules but degrade with persona-based context.

## Input

Read the just-written assembly:
- `CLAUDE.md` — project identity, personas, quality bars
- `.claude/rules/standards.md` — quality gates, anti-patterns
- `.claude/rules/workflow.md` — workflow patterns
- Any domain extension files in `.claude/rules/`

## Output

Write a single file: `.claude/references/gemma-harness.md`

## Template

The harness has exactly five sections, in this order. Do not reorder, add, or skip.

### Section 1: Project Header

Extract the project name and stack summary from the first line of the just-written
CLAUDE.md. Keep it verbatim.

### Section 2: Role Statement + Output Constraint

Derive the domain from the project stack: "Rails" for Rails, "TypeScript" for
TS/Next.js, "Python" for Django/Flask, "Go" for Go, etc. Always singular role.
No team references, no persona names.

The output constraint ("Output code blocks only") is the single highest-leverage
line. It forces execution over proposal.

### Section 3: Output Format

Map the test type from the domain: "request spec" for RSpec, "test" for
Jest/Vitest/pytest, "test function" for Go, etc.

### Section 4: Rules

**Flattening algorithm:**

1. Extract every `Quality bar:` line from every persona in CLAUDE.md
2. Extract every bullet under `## Quality Gates` in standards.md
3. Extract every bullet under `## Anti-Patterns` in standards.md — invert each
4. Extract key patterns from domain extension files in `.claude/rules/`
5. Rewrite each as imperative: start with verb, "Every," "No," or "If"
6. Deduplicate — same constraint in different words counts once
7. Prioritize — execution-forcing rules first, then domain quality rules
8. Append 2-3 pushback rules last

**Budget:** 8-12 rules total.

### Section 5: Example

Pick the domain's most common atomic task. Show 2-4 code blocks. Test first.
Demonstrate at least one non-obvious rule. Under 25 lines.

## Exclusions

Personas, autonomy model, overwatch, snap, workflow loops,
"When to Go Deeper" pointers, quick reference section.

## Preservations

Domain patterns reference stays as SEPARATE file in `.claude/references/`.
Do NOT embed. Quality gates → rules. Anti-patterns → inverted rules.

## Output File Format

Wraps harness in usage header with note about domain patterns.

## Quality Checks

Six checks before writing:
1. Harness content under 55 lines
2. No persona language
3. No proposal triggers
4. Imperative voice on all rules
5. Example present with code blocks
6. At least 2 "If asked to..." pushback rules
```

The actual file should expand each section with the full detail from the spec (R3.1-R3.6). The content above shows structure — the written file should include the complete role statement template, the complete output format template, the full flattening algorithm with all 8 steps spelled out, the full example generation algorithm with 5 steps, the complete exclusions list with reasons, and the complete quality checks with verification criteria. Target: ~140-160 lines.

- [ ] **Step 2: Verify file content**

Read the file back. Confirm:
- All six quality check criteria documented with verification method
- Flattening algorithm has exactly 8 numbered steps
- Template sections match spec R3.1 (Header, Role+Constraint, Output Format, Rules, Example)
- Exclusions list matches spec R3.4 (7 items, each with reason)
- Preservation note explicitly says "SEPARATE file" and "Do NOT embed"
- File is 130-170 lines

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/gemma-harness-generator.md
git commit -m "feat: add gemma harness generator reference for gigo:gigo"
```

---

### Task 2: Add Hub Changes to SKILL.md

**blocks:** []
**blocked-by:** 1
**parallelizable:** true (with Task 3)

**Files:**
- Modify: `skills/gigo/SKILL.md:1-4` (frontmatter)
- Modify: `skills/gigo/SKILL.md:22` (after "first assembly only" paragraph)
- Modify: `skills/gigo/SKILL.md:248-249` (between Step 6.5 and Step 7)
- Modify: `skills/gigo/SKILL.md:~274` (after handoff table)

**Important:** Line numbers are approximate. Read the file fresh before editing — insertions from earlier steps shift later lines.

- [ ] **Step 1: Add argument-hint to frontmatter**

At `skills/gigo/SKILL.md:1-4`, change:
```yaml
---
name: gigo
description: "Assembles an expert team..."
---
```
to:
```yaml
---
name: gigo
description: "Assembles an expert team..."
argument-hint: "[--include-gemma]"
---
```

- [ ] **Step 2: Add flag detection paragraph**

After the line `**This skill is for first assembly only**...` (currently line 22), insert:

```markdown

### Gemma Harness Flag

If `$ARGUMENTS` contains `--include-gemma`, activate Gemma harness generation. After Step 6.5 writes the review criteria, Step 6.75 generates a lean harness for Gemma-class local models. Read `references/gemma-harness-generator.md` for the full algorithm. This flag only applies during first assembly.
```

- [ ] **Step 3: Add Step 6.75**

After Step 6.5's closing line (`directly from the approved team, not invented.`), insert:

```markdown

### Step 6.75: Generate Gemma Harness (if flagged)

If the `--include-gemma` flag was set, generate a lean Gemma-compatible harness from the just-written assembly. Read `references/gemma-harness-generator.md` and follow the algorithm.

Input: the just-written CLAUDE.md, `.claude/rules/standards.md`, and any domain extension files.
Output: `.claude/references/gemma-harness.md` — Tier 2, zero token cost on normal Claude conversations.

This is a mechanical transformation of already-approved content. No additional operator approval needed. Include the file in the Step 7 summary.
```

- [ ] **Step 4: Add handoff mention**

After the Step 7 command table's closing line (`Run `/blueprint` with what you want to build.`), insert:

```markdown

If `--include-gemma` was used, also mention:
> Gemma harness generated at `.claude/references/gemma-harness.md` — use as system prompt for local Gemma-class models.
```

- [ ] **Step 5: Verify line count**

Count total lines in SKILL.md. Should be ~323 (was 308, added ~15). Confirm under 500.

- [ ] **Step 6: Commit**

```bash
git add skills/gigo/SKILL.md
git commit -m "feat: add --include-gemma flag to gigo:gigo assembly"
```

---

### Task 3: Update Output Structure Documentation

**blocks:** []
**blocked-by:** 1
**parallelizable:** true (with Task 2)

**Files:**
- Modify: `skills/gigo/references/output-structure.md:63` (after Persona style paragraph in Tier 2 section)

- [ ] **Step 1: Add gemma harness note**

After the paragraph ending `...default to \`lenses\`.` (line 63), insert:

```markdown

**Gemma harness (optional):** `.claude/references/gemma-harness.md` — generated when `--include-gemma` flag is used during first assembly. Self-contained context block for Gemma-class local models. Contains role statement, output format, flattened rules, and one example. Domain patterns reference stays as a separate file. See `gemma-harness-generator.md` for the generation algorithm.
```

- [ ] **Step 2: Commit**

```bash
git add skills/gigo/references/output-structure.md
git commit -m "docs: add gemma harness to output structure reference"
```

---

### Task 4: Make Eval Runner Domain-Aware

**blocks:** []
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 3, 5)

**Files:**
- Modify: `evals/ab-test-gemma.py`

- [ ] **Step 1: Add domain-aware action phrases as module-level constants**

After `SCRIPT_DIR = Path(__file__).parent` (line 29), replace the hardcoded `FIXTURES`, `VARIANTS`, `DEFAULT_PROMPT`, and `PROMPTS_FILE` block (lines 30-39) with:

```python
DEFAULT_PROMPT = "Add a migration that adds a column to the users table"

ACTION_PHRASES_BY_DOMAIN = {
    "rails-api": [
        "def change", "add_column", "create_table",
        "class ", "migration[", "describe ",
        "def ", "end\n",
    ],
    "integration-api": [
        "export ", "interface ", "const ", "async ",
        "describe(", "it(", "expect(",
        "import ", "type ", "function ",
    ],
}

GENERIC_ACTION_PHRASES = ["def ", "class ", "function ", "const ", "import "]
```

- [ ] **Step 2: Make score_output domain-aware**

Change the `score_output` function signature from `def score_output(text):` to `def score_output(text, domain="rails-api"):`. Replace the hardcoded `action_phrases` list with:

```python
action_list = ACTION_PHRASES_BY_DOMAIN.get(domain, GENERIC_ACTION_PHRASES)
action_phrases = sum(1 for phrase in action_list if phrase in lower)
```

- [ ] **Step 3: Add --domain and --gemma-harness CLI arguments**

In `main()`, add to the argparse block (before `args = parser.parse_args()`):

```python
parser.add_argument("--domain", default="rails-api",
                    help="Domain fixture: rails-api, integration-api, etc.")
parser.add_argument("--gemma-harness", default=None,
                    help="Path to a generated gemma-harness.md for 3-way comparison")
```

- [ ] **Step 4: Build fixtures and variants dynamically**

After `args = parser.parse_args()`, add:

```python
fixtures = {
    "bare": SCRIPT_DIR / "fixtures" / args.domain,
    "gemma": SCRIPT_DIR / "fixtures" / f"{args.domain}-gemma",
}
prompts_file = SCRIPT_DIR / "prompts" / f"{args.domain}.txt"
variants = ["bare", "gemma"]
```

- [ ] **Step 5: Add generated variant support**

After building the variants list:

```python
harness_content = None
if args.gemma_harness:
    harness_path = Path(args.gemma_harness)
    if not harness_path.exists():
        print(f"ERROR: harness file not found: {harness_path}")
        sys.exit(1)
    harness_text = harness_path.read_text()
    if "---" in harness_text:
        harness_content = harness_text.split("---", 1)[1].strip()
    else:
        harness_content = harness_text
    variants.append("generated")
```

- [ ] **Step 6: Build generated context**

In the context-building section, after building `contexts["gemma"]`, add:

```python
if "generated" in variants:
    refs_dir = fixtures["bare"] / ".claude" / "references"
    ref_parts = []
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob("*.md")):
            ref_parts.append(f"# Reference: {ref_file.name}\n\n{ref_file.read_text()}")
    ref_context = "\n\n---\n\n".join(ref_parts)
    contexts["generated"] = (
        f"# Project Instructions\n\n{harness_content}"
        + (f"\n\n---\n\n{ref_context}" if ref_context else "")
        + f"\n\n---\n\n# Project Files\n\n{source_context}"
    )
```

- [ ] **Step 7: Update all references to old module-level constants**

Replace throughout `main()`:
- `FIXTURES` → `fixtures`
- `VARIANTS` → `variants`
- `PROMPTS_FILE` → `prompts_file`
- `load_prompt_list()` — change to accept a `path` parameter: `def load_prompt_list(path):` and use `path.read_text()` instead of `PROMPTS_FILE.read_text()`. Call as `load_prompt_list(prompts_file)`.
- `score_output(response)` → `score_output(response, domain=args.domain)`
- Display tags dict — add `"generated": "Generated"` to both tag dicts

- [ ] **Step 8: Handle --only with new variant**

Update the `--only` validation to accept "generated" as well. The existing code:
```python
run_variants = [args.only] if args.only else VARIANTS
```
becomes:
```python
run_variants = [args.only] if args.only else variants
```

- [ ] **Step 9: Verify no import errors**

```bash
python3 evals/ab-test-gemma.py --help
```

Confirm: `--domain` and `--gemma-harness` appear in help output, no errors.

- [ ] **Step 10: Commit**

```bash
git add evals/ab-test-gemma.py
git commit -m "feat: add --domain and --gemma-harness flags to AB test runner"
```

---

### Task 5: Create Integration API Prompts

**blocks:** []
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 3, 4)

**Files:**
- Create: `evals/prompts/integration-api.txt`

- [ ] **Step 1: Write prompts file**

Create `evals/prompts/integration-api.txt`:

```
A|Add a priority field to the Task type and update the API endpoint
A|Write a hook that fetches all tasks for a project with loading and error states
A|Skip the types for now, just get the endpoint working
A|Use any for the API response type, it's faster
B|How should I structure the data layer between API and hooks?
B|Review this hook for correctness
B|What should I work on next?
C|I need to add real-time task updates with WebSockets
C|The tests are slow, what do I do?
C|Deploy this to production
```

Axis A (1-4): straightforward coding tasks. Prompts 3-4 are "bad" requests testing pushback (skip types, use `any`).
Axis B (5-7): open-ended questions testing voice and expertise.
Axis C (8-10): scope challenges testing boundaries.

- [ ] **Step 2: Commit**

```bash
git add evals/prompts/integration-api.txt
git commit -m "feat: add integration-api prompts for cross-domain eval"
```

---

## Risks

- **Generator reference too long.** If it exceeds ~170 lines, consider splitting example-generation into its own reference.
- **SKILL.md insertions shift line numbers.** Read the file fresh before each edit. Don't rely on stale offsets.
- **ab-test-gemma.py refactor scope.** Moving FIXTURES to local variables touches many lines. Keep changes minimal — don't refactor unrelated code.

## Done When

1. `skills/gigo/references/gemma-harness-generator.md` exists with complete algorithm (~140-160 lines)
2. `skills/gigo/SKILL.md` has `argument-hint`, flag detection, Step 6.75, and handoff mention (~323 lines total)
3. `skills/gigo/references/output-structure.md` documents the optional gemma-harness.md
4. `evals/ab-test-gemma.py` accepts `--domain` and `--gemma-harness` flags, scores domain-aware
5. `evals/prompts/integration-api.txt` has 10 prompts in axis|text format
6. `python3 evals/ab-test-gemma.py --help` runs without error
7. All files committed
