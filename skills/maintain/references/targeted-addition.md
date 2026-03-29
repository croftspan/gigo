# Targeted Addition — Procedure

The operator has identified a gap. Your job is to fill it without bloating what's already there.

## Step 1: Understand the Gap

You've already read the existing files. Now understand what's missing relative to what the operator is asking for. Don't just hear "add X" — understand *why* they need it. What changed? What broke? What's the project growing into?

## Step 2: Choose Research Depth

> "Want me to work from what I know, or deep-research this area first?"

| Mode | What happens | Best for |
|---|---|---|
| **Quick** (default) | Use training knowledge to identify authorities and best practices | Established domains, operator has some familiarity |
| **Deep research** | Web search for current authorities, community consensus, recent tools | Fast-moving domains, totally unfamiliar territory |

For deep research, use WebSearch and WebFetch to find current state of the art.

## Step 3: Research and Propose

Use the same **universal discovery framework** as the initial assembly — seven questions adapted to the specific gap:

1. **What is being built, and who is it for?** (scoped to the new area)
2. **Who are the authorities?** Find 2-3+ top practitioners for this specific expertise.
3. **What does the gold standard look like?**
4. **What are the core tools and processes?**
5. **What are the quality gates?**
6. **What are the common mistakes?**
7. **What does "done" look like?**

Present to the operator:
- **The gap you see** and why the current team doesn't cover it
- **Proposed new persona(s)** — name, role, blended philosophy, what they bring
- **Changes to existing files** — new/modified extension files, new references
- **Impact on line budgets** — will adding this push any file past ~60 lines or the total past ~300? If so, what gets tightened or moved to references?
- **Alignment vs knowledge split** — which parts of the new persona are alignment signal (quality bars, approach, constraints → rules) vs knowledge signal (factual specifics, patterns → references)?

## Step 4: Conversational Refinement

The operator reacts, you adjust. Keep going until they approve.

## Step 5: Merge

Write the changes. This is a merge, not a rewrite:
- Add new persona(s) to `CLAUDE.md`
- Add/update extension files in `.claude/rules/`
- Add new reference files to `.claude/references/`
- **Check Overwatch threshold.** After adding, count domain personas in CLAUDE.md (don't count The Overwatch). If now at 3+ and The Overwatch isn't present, add The Overwatch persona to CLAUDE.md. Read `gigo/references/persona-template.md` → "The Overwatch" for the template. The Overwatch section in workflow.md and overwatch.md reference should already exist from initial assembly — verify they're present.
- **Before adding new rules, check line budgets.** If adding a persona pushes `CLAUDE.md` too long, tighten existing entries first. If a rules file is approaching ~60 lines, move content to references.

When creating personas or extensions, read the templates from the gigo skill's bundled `references/` directory.

When designing the new persona, separate alignment signal from knowledge signal. The lean tier entry in CLAUDE.md should contain only alignment content — quality bars, approach, constraints, what to push back on. Domain-specific knowledge (factual details, implementation patterns, technical specifics) belongs in `.claude/references/personas/` or a reference file, loaded on demand. See `gigo/references/persona-template.md` for the "Alignment vs Knowledge Signal" section.
- **Regenerate review criteria.** After writing all changes, regenerate `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo Step 6.5. If the file doesn't exist, create it. If it does, regenerate from scratch (don't append).
