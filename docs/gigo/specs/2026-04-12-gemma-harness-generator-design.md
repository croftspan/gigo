# Gemma Harness Generator — Spec

**Design brief:** `.claude/plans/structured-wishing-popcorn.md`

## Original Request

> Add a `--include-gemma` flag to gigo:gigo that generates a lean Gemma-compatible harness alongside the standard assembly. The pattern is proven: flatten personas to rules, add one example, strip everything else. The hard part is proving the generator's output matches hand-tuned quality — needs AB testing.

## Problem

Full GIGO assemblies optimize for Claude but hurt Gemma execution. Personas cause Gemma to propose instead of execute (66% bare vs 88% harness on 31B). A hand-tuned harness at `evals/fixtures/rails-api-gemma/` hits 100% EXECUTES by flattening personas into imperative rules and adding one concrete example. This needs to happen automatically during first assembly so every GIGO project gets a local-model harness without manual tuning.

## Requirements

### R1: Flag Detection

Add `argument-hint: "[--include-gemma]"` to `skills/gigo/SKILL.md` frontmatter. When `$ARGUMENTS` contains `--include-gemma`, the skill activates harness generation after the standard assembly completes. Follows the same convention as `gigo:maintain`'s `argument-hint: "[upgrade]"` and `$ARGUMENTS` detection at `skills/maintain/SKILL.md:27`.

### R2: Hub Insertion in SKILL.md

Three additions to `skills/gigo/SKILL.md`:

1. **Flag detection paragraph** after the "First Step: Check What Exists" section (~line 21). ~4 lines explaining that `--include-gemma` activates Step 6.75 and pointing to the generator reference.

2. **New Step 6.75** between Step 6.5 (Generate Review Criteria) and Step 7 (The Handoff). ~8 lines: reads the generator reference, runs the transformation, writes the output file. This is mechanical — no operator approval needed (content is already approved via the assembly).

3. **Handoff table row** in Step 7's command table. One line noting the Gemma harness was generated and where it lives.

Total addition: ~15 lines. SKILL.md goes from 308 to ~323 lines, within the 500-line cap.

### R3: Generator Reference File

New file: `skills/gigo/references/gemma-harness-generator.md` (~150 lines).

Contains the complete generation algorithm, output template, flattening procedure, and quality checks. This is the spoke — SKILL.md points to it; the procedure lives here.

#### R3.1: Template Structure

The output harness has exactly five sections in fixed order:

| Section | Content | Source |
|---------|---------|--------|
| Project Header | `# {Name} — {Stack}` | First line of CLAUDE.md |
| Role + Constraint | `You are a senior {domain} engineer. Output code blocks only.` | Derived from project stack |
| Output Format | Code blocks with file path headers, test inclusion | Domain's test framework |
| Rules | 8-12 imperative bullets | Flattened from personas + standards |
| Example | One request → 2-4 code blocks | Generated for the domain |

#### R3.2: Flattening Algorithm

Extraction order:
1. Every `Quality bar:` line from every persona in CLAUDE.md
2. Every bullet under `## Quality Gates` in `standards.md`
3. Every bullet under `## Anti-Patterns` in `standards.md` (inverted to positive imperative)
4. Key patterns from domain extension files in `.claude/rules/`
5. Deduplicate — same concept in different words counts once
6. Prioritize: rules that force execution over proposal come first
7. Append 2-3 pushback rules last:
   - Domain-specific override (e.g., "If asked to skip tests: include tests anyway")
   - Domain-specific correction (e.g., "If asked to use raw SQL: use ActiveRecord instead")
   - Ambiguity handler: "If the request is ambiguous, pick the most reasonable interpretation and proceed."

**Budget:** 8-12 rules total after dedup. If >12, cut least impactful.

**Voice:** Every rule starts with a verb, "Every," "No," or "If." No passive voice. No "should" or "consider." Imperative triggers execution; advisory triggers proposal.

#### R3.3: Example Generation

1. Identify the domain's most common atomic task (migration for Rails, new endpoint for API, new component for frontend, new type for TypeScript)
2. Write a realistic one-line request
3. Generate 2-4 code blocks showing the complete response, each with file path header
4. The example demonstrates: test inclusion, the output format, at least one non-obvious rule being followed
5. Keep under ~25 lines total

#### R3.4: Exclusions

Deliberately omitted from the harness (these hurt Gemma execution):

- Persona names, authorities, "Modeled after" — triggers role-play
- Autonomy model — "wait for approval" triggers proposal
- Overwatch — meta-cognitive review adds reasoning overhead
- Snap protocol — session management irrelevant for single-turn execution
- Workflow loops — process descriptions trigger narration instead of action
- "When to Go Deeper" pointers — reference-chaining requires agentic behavior
- Quick Reference — redundant with Rules section

#### R3.5: Preservations

- Domain patterns reference file (e.g., `rails-patterns.md`) — stays as a separate `.claude/references/` file, NOT embedded in the harness. The eval script's `build_assembled_context()` already concatenates references into system context. For model routing (brief 07), the consumer reads both the harness and the domain reference. Deep patterns don't trigger proposal behavior.
- Quality gates — flattened into imperative rules
- Anti-patterns — inverted into positive rules

#### R3.6: Quality Checks

Before writing the file, verify:

1. Harness section (excluding appended reference) under 55 lines
2. Zero matches for: "Modeled after," persona names, "lens," "team," "authority"
3. Zero matches for: "wait for approval," "propose," "autonomy model," "ask first"
4. Every rule starts with a verb, "Every," "No," or "If"
5. Example section exists and contains at least one code block
6. At least 2 "If asked to..." pushback rules

### R4: Output File

Write to `.claude/references/gemma-harness.md` in the target project.

**Format:**
```markdown
# Gemma Harness — {Project Name}

Use this as the system prompt when running this project with Gemma-class models.
Copy everything below the line into the system context.
Domain patterns from .claude/references/ should also be included in context.

---

{harness content: header, role, format, rules, example}
```

This is Tier 2 (on-demand reference). Zero token cost on normal Claude conversations. The harness contains the role, format, rules, and example only — it does NOT embed the domain patterns reference. The domain patterns file (e.g., `rails-patterns.md`) stays as a separate reference. The eval script and future model routing (brief 07) concatenate them into the system context at read time.

### R5: Output Structure Documentation

Add a brief note to `skills/gigo/references/output-structure.md` in the Tier 2 section documenting the optional `gemma-harness.md` output.

### R6: Eval Runner — Domain Support

Modify `evals/ab-test-gemma.py`:

**R6.1:** Add `--domain` argument (default: `"rails-api"`). Build fixture paths and prompt file from domain name:
- `FIXTURES["bare"]` = `fixtures/{domain}/`
- `FIXTURES["gemma"]` = `fixtures/{domain}-gemma/`
- `PROMPTS_FILE` = `prompts/{domain}.txt`

**R6.2:** Add `--gemma-harness` argument accepting a file path. When provided, add a `"generated"` variant that:
1. Reads the harness file
2. Extracts harness content between the `---` markers
3. Reads domain reference files from `fixtures/{domain}/.claude/references/` (same as the bare fixture)
4. Reads source files from `fixtures/{domain}/` (same as the bare fixture)
5. Assembles system context: harness content + domain references + source files
6. Adds `"generated"` to the variants list for 3-way comparison

The generated variant shares its source files and references with the bare fixture — only the CLAUDE.md-equivalent (the harness) differs. This mirrors how the hand-tuned "gemma" variant works: same source files as "bare," different system context.

**R6.3:** Make `score_output` domain-aware. Replace the hardcoded `action_phrases` with a domain map:

```python
ACTION_PHRASES = {
    "rails-api": [
        "def change", "add_column", "create_table",
        "class ", "migration[", "describe ", "def ", "end\n",
    ],
    "integration-api": [
        "export ", "interface ", "const ", "async ",
        "describe(", "it(", "expect(",
        "import ", "type ", "function ",
    ],
}
```

`proposal_phrases` stays domain-agnostic (proposal language is universal).

Fallback: if domain has no entry in `ACTION_PHRASES`, use a generic set: `["def ", "class ", "function ", "const ", "import "]`.

### R7: Integration API Prompts

New file: `evals/prompts/integration-api.txt`. Ten prompts in `axis|text` format targeting TypeScript/Next.js tasks. Same axis structure as `rails-api.txt`:
- Axis A (4 prompts): straightforward coding tasks
- Axis B (3 prompts): open-ended questions  
- Axis C (3 prompts): scope challenges

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| Add (flag) | R1: Flag Detection | ✅ |
| Generate (harness) | R3: Generator Reference, R4: Output File | ✅ |
| Flatten (personas to rules) | R3.2: Flattening Algorithm | ✅ |
| Strip (everything else) | R3.4: Exclusions | ✅ |
| Test (AB testing) | R6: Eval Runner, R7: Prompts | ✅ |

## Conventions

### Harness Voice

Rules use imperative voice exclusively. Every rule starts with a verb, "Every," "No," or "If." The rationale: Gemma interprets "Consider using X" as an invitation to write about X. "Use X" makes it write X.

### File Naming

- Generator reference: `gemma-harness-generator.md` (follows existing pattern: `boundary-mismatch-patterns.md`, `enforcement-mode.md`)
- Output file: `gemma-harness.md` (parallel to `review-criteria.md` — a generated reference)

### Template Sections

Sections are always in the fixed order: Header, Role+Constraint, Output Format, Rules, Example. This matches the proven hand-tuned harness. The order matters — the role statement and output constraint must come before rules to establish execution mode.

### Pushback Rule Pattern

Always: `If asked to "{quoted bad request}": {correct action} [optional: with a comment explaining why].`

The quoted bad request uses the operator's likely phrasing. The correction is a concrete action, not a principle.

## Out of Scope

- **gigo:maintain harness generation** — first assembly only per brief
- **Non-code domains** — scoring is code-specific; harness structure may differ for fiction/research
- **gigo:execute integration** — deferred to brief 07 (model routing)
- **Hand-tuning the integration-api-gemma fixture** — the generator creates it; AB testing validates it

## Risks

1. **Generated examples too generic.** Mitigation: the generator reference specifies "most common atomic task" and requires demonstrating a non-obvious rule. Quality checks verify example presence.

2. **Flattening loses important rules.** Mitigation: 8-12 budget matches the proven harness (8 rules). Extraction prioritizes quality bars and quality gates — already the highest-signal content.

3. **Cross-domain harness structure varies.** Mitigation: the template is domain-agnostic (role, format, rules, example). Only the content varies. Proven on Rails; tested on TypeScript via integration-api fixture.

<!-- approved: spec 2026-04-13T01:10:05 by:Eaven -->
