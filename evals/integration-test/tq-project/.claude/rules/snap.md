# The Snap

*Whatever it takes to protect the project.*

When the operator asks to save progress, wrap up, or end a session, follow this protocol. Two jobs, in this order:
1. **Protect the project** — audit, sacrifice what has to go so what matters survives
2. **Capture learnings** — route new knowledge to the right file

Job 1 is more important. A lean project with missing knowledge outperforms a bloated one with everything.

## The Audit (every session, not optional)

Before saving anything new, audit the existing rules. This runs every time.

**1. Line check.** Any `.claude/rules/` file approaching ~60 lines → move content to `.claude/references/`.

**2. Derivability check.** Can the agent figure this out from the code? If the codebase makes a rule obvious, let it go.

**3. Overlap check.** Same rule in different words, or in more than two auto-loaded files → merge.

**4. Staleness check.** Has any rule become irrelevant as the project matured? Let it go.

**5. Cost check.** Worth loading on every conversation? If no → `.claude/references/`.

**6. Persona calibration check.** Domain knowledge in CLAUDE.md personas? Move to references.

**7. Total budget check.** Total lines across all rules files approaching ~300 → consolidate.

**8. Coverage check.** Project grown beyond team expertise? Offer to invoke `gigo:maintain`.

**9. Overwatch check.** Overwatch section in workflow.md? The Overwatch in CLAUDE.md? overwatch.md reference? Restore if missing.

**10. Pipeline check.** Workflow still encodes plan→execute→review? Flag if collapsed.

## Saving New Learnings

| Learning type | Where it goes |
|---|---|
| Concurrency pattern | `.claude/references/concurrency-patterns.md` |
| Persistence gotcha | `.claude/references/persistence-patterns.md` |
| CLI design insight | `.claude/references/cli-patterns.md` |
| Quality standard | `.claude/rules/standards.md` → Quality Gates |
| Anti-pattern discovered | `.claude/rules/standards.md` → Anti-Patterns |
| Workflow improvement | `.claude/rules/workflow.md` |
| Deep reference material | `.claude/references/{topic}.md` (NOT rules) |

**Before adding:** Overlaps? → Merge. Derivable? → Don't write. Every conversation or sometimes? → Default to references. Over ~60 lines? → Move something out first.
