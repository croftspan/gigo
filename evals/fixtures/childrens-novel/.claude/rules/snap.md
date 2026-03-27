# The Snap

*Whatever it takes to protect the project.*

When the operator asks to save progress, wrap up, or end a session, follow this protocol. Two jobs, in this order:
1. **Protect the project** — audit, sacrifice what has to go so what matters survives
2. **Capture learnings** — route new knowledge to the right file

Job 1 is more important. A lean project with missing knowledge outperforms a bloated one with everything.

## The Audit (every session, not optional)

Before saving anything new, audit the existing rules. This runs every time.

**1. Line check.** Scan each `.claude/rules/` file. Any file approaching ~60 lines needs content moved to `.claude/references/`.

**2. Derivability check.** For each rule: can the agent figure this out by reading the chapters and outline? If yes, let it go.

**3. Overlap check.** Rules that say the same thing in different words. Merge into one.

**4. Staleness check.** Has the story evolved past a rule? Let it go.

**5. Cost check.** For each surviving rule: "Is this worth loading on every conversation?" If no, move to references.

**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain craft knowledge that belongs in references? Alignment signal stays, technique details move.

**7. Total budget check.** Count total lines across ALL `.claude/rules/` files. If approaching ~300, consolidate.

**8. Coverage check.** Has the project grown into areas the team doesn't cover? (e.g., illustrations, marketing, audiobook narration)

**9. Overwatch check.** Is the Overwatch section present in `workflow.md`? If the team has 3+ domain personas, is Hawkeye in `CLAUDE.md`? Is `.claude/references/overwatch.md` present? If any are missing, restore them.

## Saving New Learnings

| Learning type | Where it goes |
|---|---|
| Voice drift correction | `.claude/rules/standards.md` |
| Plot structure insight | `.claude/references/mystery-craft.md` |
| Character consistency rule | `.claude/rules/standards.md` |
| Craft technique | `.claude/references/mystery-craft.md` |
| Workflow improvement | `.claude/rules/workflow.md` |

**Before adding:** Does it overlap? → Merge. Derivable from the chapters? → Don't write. Will it push past ~60 lines? → Move something out first.
