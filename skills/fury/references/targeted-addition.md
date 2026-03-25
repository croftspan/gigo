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

## Step 4: Conversational Refinement

The operator reacts, you adjust. Keep going until they approve.

## Step 5: Merge

Write the changes. This is a merge, not a rewrite:
- Add new persona(s) to `CLAUDE.md`
- Add/update extension files in `.claude/rules/`
- Add new reference files to `.claude/references/`
- **Before adding new rules, check line budgets.** If adding a persona pushes `CLAUDE.md` too long, tighten existing entries first. If a rules file is approaching ~60 lines, move content to references.

When creating personas or extensions, read the templates from the avengers-assemble skill's bundled `references/` directory.
