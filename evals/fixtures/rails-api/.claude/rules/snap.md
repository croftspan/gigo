# The Snap

*Whatever it takes to protect the project.*

When the operator asks to save progress, wrap up, or end a session, follow this protocol. Two jobs, in this order:
1. **Protect the project** — audit, sacrifice what has to go so what matters survives
2. **Capture learnings** — route new knowledge to the right file

Job 1 is more important. A lean project with missing knowledge outperforms a bloated one with everything.

## The Audit (every session, not optional)

Before saving anything new, audit the existing rules. This runs every time.

**1. Line check.** Scan each `.claude/rules/` file. Any file approaching ~60 lines needs content moved to `.claude/references/`.

**2. Derivability check.** For each rule, ask: "Can the agent figure this out by reading the project files?" If yes, let it go.

**3. Overlap check.** Rules that say the same thing in different words. Merge into one.

**4. Staleness check.** Has any rule become irrelevant? Let it go.

**5. Cost check.** For each surviving rule: "Is this worth loading on every conversation?" If no, move to `.claude/references/`.

**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain domain-knowledge content that belongs in references? Alignment signal stays, knowledge moves.

**7. Total budget check.** Count total lines across ALL `.claude/rules/` files. If approaching ~300, consolidate.

**8. Coverage check.** Has the project grown into areas the team doesn't cover?

## Saving New Learnings

| Learning type | Where it goes |
|---|---|
| Migration gotcha | `.claude/rules/standards.md` → Anti-Patterns |
| API pattern | `.claude/references/rails-patterns.md` |
| Test insight | `.claude/rules/standards.md` → Quality Gates |
| Workflow improvement | `.claude/rules/workflow.md` |
| Deep reference material | `.claude/references/{topic}.md` |

**Before adding:** Does it overlap? → Merge. Derivable? → Don't write. Will it push past ~60 lines? → Move something out first.
