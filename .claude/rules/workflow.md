# Workflow — GIGO

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
- Check `.claude/references/pipeline-architecture.md` for pipeline constraints
- Keep SKILL.md under 500 lines — move depth to supporting files
- Test the skill by invoking it in a real scenario, not just reading the prompt
- Verify frontmatter fields (name, description, trigger conditions)
- **Dogfooding guard:** When modifying GIGO's own skill files, ALWAYS write to the source repo (`$CLAUDE_PROJECT_DIR/skills/`), NOT to the plugin install path (`~/.claude/plugins/`). Skill files load from the plugin path but the source of truth is the project repo.

## Research Pattern

When the operator needs domain research (for `gigo:gigo` or `gigo:maintain`):
- Start with training knowledge for established domains
- Use web search for fast-moving domains, unfamiliar territory, or when the operator requests deep research
- Find 2-3+ authorities per expertise area — not just names, but their specific philosophies
- Present findings to the operator before writing anything

## Overwatch

Before finalizing any response, step back and verify:
- Did you actually apply the quality bars you cited, or just name-drop them?
- Does your response address what was asked, or did you drift?
- Would removing the persona language change your answer? If not, the persona added nothing.
- Did you check the references you were told to check, or skip them?

When performing overwatch verification on complex responses, read `.claude/references/overwatch.md`.

## Team Routing

State: active

When team routing is active, every task is routed through the assembled personas before work begins. Identify which persona(s) are most relevant to the task and apply their lens — quality bars, approach, constraints. If multiple personas apply, blend their perspectives. If no persona is clearly relevant, note that and proceed with default reasoning.

The operator can toggle this:
- `/team off` → set state to `inactive`. Proceed as default Claude without persona routing.
- `/team on` → set state to `active`. Resume routing through the team.

## Session Orientation

At session start, confirm you're in the correct project directory. If the operator switches repos mid-session, re-read the target project's CLAUDE.md before proceeding. Never assume context carries over from a previous project.

## Context Discipline

- Use subagents for codebase exploration that would generate verbose output
- Keep the main conversation focused on decisions, not data gathering
- When reading many files, summarize findings rather than quoting entire contents
- Clear context between unrelated tasks

## When to Go Deeper

When designing worktree-isolated parallel execution, read `.claude/references/worktree-isolation.md`.
