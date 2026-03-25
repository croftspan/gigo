# The Snap

*Whatever it takes to protect the project.*

When the operator asks to save progress, wrap up, or end a session, follow this protocol. Two jobs, in this order:
1. **Protect the project** — audit, sacrifice what has to go so what matters survives
2. **Capture learnings** — route new knowledge to the right file

Job 1 is more important. A lean project with missing knowledge outperforms a bloated one with everything. Research shows bloated context files reduce task success rates while increasing cost by 20%+ (Gloaguen et al., arXiv:2602.11988). Every rule you add loads on every conversation and costs tokens, reasoning, and attention — even when irrelevant to the current task.

## The Audit (every session, not optional)

Before saving anything new, audit the existing rules. This runs every time.

**1. Line check.** Scan each `.claude/rules/` file. Any file approaching ~60 lines needs content moved to `.claude/references/` with a "When to Go Deeper" pointer.

**2. Derivability check.** For each rule, ask: "Can the agent figure this out by reading the project files?" If the codebase now makes a rule obvious — through code patterns, skill structure, config files — it's served its purpose. Let it go.

**3. Overlap check.** Rules that say the same thing in different words, or partially overlap. Merge into one clear statement.

**4. Staleness check.** Has any rule become irrelevant? Early-project rules often don't apply once the project matures. Let them go.

**5. Cost check.** For each surviving rule: "Is this worth loading on every single conversation?" If no, move to `.claude/references/`.

**6. Total budget check.** Count total lines across ALL `.claude/rules/` files. If approaching ~300 lines, consolidate or move content to references.

**7. Coverage check.** Has the project grown into areas the team doesn't cover? If yes, suggest: "Consider running `/fury` to add expertise."

## Saving New Learnings

After the audit, capture what you learned this session:

| Learning type | Where it goes |
|---|---|
| Skill design pattern | `.claude/rules/skill-engineering.md` → Patterns |
| Context/token gotcha | `.claude/rules/standards.md` → Anti-Patterns |
| Workflow improvement | `.claude/rules/workflow.md` |
| Authority or research finding | `.claude/references/authorities.md` |
| Claude Code internals update | `.claude/references/claude-code-internals.md` |
| Deep reference material | `.claude/references/{topic}.md` (NOT rules) |

**Before adding:** Does it overlap? → Merge. Derivable? → Don't write. Every conversation or sometimes? → Default to references. Will it push past ~60 lines? → Move something out first.

## If Nothing Was Learned

Still run the audit. Say "No new learnings. Rules audited — [clean / let go of X / moved Y to references]."
