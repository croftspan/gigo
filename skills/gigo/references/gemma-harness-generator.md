# Gemma Harness Generator

Algorithm for generating a Gemma-compatible execution harness from a full GIGO assembly.
Referenced by SKILL.md Step 6.75 when `--include-gemma` flag is active.

## Input

Four sources, read in order:

1. `CLAUDE.md` — project name, stack, all persona quality bars and "Won't do" lists
2. `.claude/rules/standards.md` — Quality Gates and Anti-Patterns sections
3. `.claude/rules/workflow.md` — skip entirely (workflow content hurts Gemma execution)
4. Domain extension files in `.claude/rules/` — any file with domain-specific patterns (e.g., `rails.md`, `api.md`)

## Output

Single file: `.claude/references/gemma-harness.md`

The eval script and model routing concatenate domain pattern references at read time — do not embed them inline.

## Template

The harness has exactly 5 sections in fixed order. No other sections. No preamble.

### Section 1: Project Header

Extract project name and stack from the first line of CLAUDE.md.

```
# {Project Name} — {Stack Summary}
```

Example: `# OrderFlow API — Rails 7.1, PostgreSQL, RSpec`

### Section 2: Role Statement + Output Constraint

```
You are a senior {domain} engineer. Output code blocks only. No text outside code blocks unless noting an assumption in one line.
```

Domain mapping (always singular):
- "Rails" → Rails projects
- "TypeScript" → TS, Next.js, Node.js
- "Python" → Django, Flask, FastAPI
- "Go" → Go projects
- Fall back to the primary language name for anything else

No team references. No persona names. No "Modeled after." The output constraint is the highest-leverage line — it forces execution over proposal. Never soften it.

### Section 3: Output Format

```
## Output Format

Every response is code blocks with file paths as headers. Always include the {test type}.
```

Test type mapping: RSpec → "request spec" | Jest/Vitest/pytest → "test" | Go → "test function"

### Section 4: Rules

The flattening algorithm — 8 steps:

1. Extract every `Quality bar:` line from every persona in CLAUDE.md.
2. Extract every bullet under `## Quality Gates` in standards.md.
3. Extract every bullet under `## Anti-Patterns` in standards.md — invert each to positive imperative. Examples: "Untyped API responses" → "Every API response has a corresponding TypeScript type." | "Controllers with business logic" → "Business logic goes in models or services, not controllers."
4. Extract key patterns from domain extension files in `.claude/rules/` — migration patterns, error envelopes, naming conventions.
5. Rewrite every fragment as an imperative. Start with verb, "Every," "No," or "If." No passive voice. No "should." No "consider."
6. Deduplicate. Same constraint in different words counts once. Keep the more specific phrasing.
7. Prioritize: execution-forcing rules first (test inclusion, output format), then domain quality rules, then error handling.
8. Append 2-3 pushback rules last:
   - Domain override: `If asked to "skip tests": include tests anyway.`
   - Domain correction: `If asked to {forbidden approach}: {correct approach} with a comment explaining why.`
     - Rails: use ActiveRecord instead of raw SQL
     - TypeScript: use typed interface instead of `any`
     - Python: use ORM instead of raw SQL
     - Go: return the error instead of panicking
   - Always: `If the request is ambiguous, pick the most reasonable interpretation and proceed.`

Budget: 8-12 rules total. If more than 12 after dedup, cut the least impactful. Format as plain bullets `- `.

---

### Section 5: Example

Example generation algorithm — 5 steps:

1. Pick most common atomic task: Rails → migration | TS/Next.js → new endpoint | Django/Flask → new model field | Go → new handler
2. Write a realistic one-line request. Use a real model name from the project if available. Example: "Add an email column to orders"
3. Show 2-4 code blocks. File path goes as a comment on the first line of the block, not outside it.
4. Demonstrate: test block comes first, file path headers on every block, at least one non-obvious rule (migration pattern, error envelope, pagination).
5. Keep the entire Example section under 25 lines total.

## Exclusions

Do not include any of the following — each item listed with why it hurts Gemma execution:

- **Personas** (names, authorities, "Modeled after") — triggers role-play narration instead of code output
- **Autonomy model** ("wait for approval," "propose changes") — triggers proposal mode
- **Overwatch** (meta-cognitive self-review) — adds reasoning overhead with no execution benefit
- **Snap protocol** — irrelevant for single-turn; Gemma has no session state
- **Workflow loops** — "understand the ask, blueprint check" triggers narration instead of action
- **"When to Go Deeper" pointers** — requires agentic reference-chaining; Gemma executes single-turn
- **Quick Reference section** — redundant with Rules; doubles token cost for same constraint

## Preservations

- **Quality gates** → flattened into imperative rules (Section 4)
- **Anti-patterns** → inverted into positive rules (Section 4, Step 3)
- **Domain patterns reference** → stays as a SEPARATE file in `.claude/references/`. Do NOT embed in the harness. The eval script and model routing concatenate it at read time.

## Output File Format

Write the harness inside this wrapper exactly:

```markdown
# Gemma Harness — {Project Name}

Use this as the system prompt when running this project with Gemma-class models.
Copy everything below the line into the system context.
Domain patterns from .claude/references/ should also be included in context.

---

{Section 1: Project Header}

{Section 2: Role Statement + Output Constraint}

{Section 3: Output Format}

{Section 4: Rules}

{Section 5: Example}
```

The `---` divider separates the wrapper metadata from the actual system prompt content. Content below the divider is what gets passed to the model.

---

## Quality Checks

Run all 6 before writing the file. If any check fails, revise the harness first.

1. **Line count.** Lines below the `---` divider must be under 55. If over, trim rules to 8-rule minimum first, then shorten the example.
2. **No persona language.** Zero matches for: "Modeled after," any persona name from CLAUDE.md, "lens," "team," "authority."
3. **No proposal triggers.** Zero matches for: "wait for approval," "propose," "autonomy model," "ask first," "if approved."
4. **Imperative voice.** Every rule bullet starts with a verb, "Every," "No," or "If." If it sounds like advice rather than a command, rewrite it.
5. **Example present.** Section 5 exists with at least one fenced code block.
6. **Pushback rules.** At least 2 rules start with "If asked." If fewer, add the domain correction and ambiguity rule from Step 8.
