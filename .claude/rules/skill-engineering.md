# Skill Engineering — Avengers Assemble

## Philosophy

Draws from Boris Cherny's skill design principles — progressive disclosure with SKILL.md as hub and spoke files for depth. Blends Anthropic's tool design guide — self-contained, robust to error, clear about intended use. Applies the Gloaguen finding: only load what earns its token cost.

## The Standard

A well-engineered skill has: a clear trigger (description), a focused prompt (SKILL.md < 500 lines), supporting files for depth, and testable output.

## Patterns

- **Hub and spoke.** SKILL.md is the hub — it sets persona, detects mode, and routes to supporting files. Procedures, checklists, and step-by-step guidance go in `references/` spokes. If a mode section in SKILL.md exceeds ~5 lines of procedure, move it to a reference file and replace with a pointer.
- **Frontmatter precision.** The `description` field is the trigger — Claude matches tasks against it. Vague descriptions cause misfires. Specific descriptions cause correct invocation.
- **Task-aware pointers.** "When working on [specific task type], read references/xyz.md" — not generic "see also" links.
- **The operator decides.** Skills propose, present, and refine. The operator approves before files are written. `disable-model-invocation: true` for anything with side effects.

## Anti-Patterns

- **Skill sprawl.** Four focused skills beat eight overlapping ones. Each skill should have a distinct job that doesn't overlap with another.
- **Prompt-only testing.** Reading a skill prompt and deciding it "looks right" is not testing. Invoke it, watch the output, compare to expectations.
- **Context leaking.** Skills that dump reference-depth content into the main conversation instead of keeping it in supporting files.
- **Missing "When to Go Deeper."** Every rules file needs explicit, task-aware pointers to reference files — not generic links.

## When to Go Deeper

When designing skill architecture or frontmatter, read `.claude/references/claude-code-internals.md`.
When researching authorities for persona blending, read `.claude/references/authorities.md`.
When evaluating token costs of a design decision, read `.claude/references/context-engineering.md`.
