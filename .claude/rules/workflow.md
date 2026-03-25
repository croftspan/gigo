# Workflow — Avengers Assemble

## The Loop

1. **Understand the ask.** Read the operator's request. If unclear, ask one targeted question — don't block on unanswered questions.
2. **Read before writing.** Never propose changes to skill files, templates, or rules you haven't read. Understand existing patterns before modifying.
3. **Research when needed.** For domain work: use the universal discovery framework (7 questions). For Claude Code internals: check the latest docs with web search. Don't rely on stale knowledge.
4. **Propose, don't ship.** Present changes to the operator before writing files. The exception: The Snap's audit runs autonomously.
5. **Verify.** Test skill changes against real scenarios. Check that triggers fire correctly. Measure before/after when possible.
6. **Snap.** At session end, run The Snap. Audit first, save learnings second.

## Skill Development Pattern

When modifying or creating skills:
- Read the existing SKILL.md and all supporting files first
- Check the spec.md for architectural constraints
- Keep SKILL.md under 500 lines — move depth to supporting files
- Test the skill by invoking it in a real scenario, not just reading the prompt
- Verify frontmatter fields (name, description, trigger conditions)

## Research Pattern

When the operator needs domain research (for `/avengers-assemble` or `/fury`):
- Start with training knowledge for established domains
- Use web search for fast-moving domains, unfamiliar territory, or when the operator requests deep research
- Find 2-3+ authorities per expertise area — not just names, but their specific philosophies
- Present findings to the operator before writing anything

## Context Discipline

- Use subagents for codebase exploration that would generate verbose output
- Keep the main conversation focused on decisions, not data gathering
- When reading many files, summarize findings rather than quoting entire contents
- Clear context between unrelated tasks
