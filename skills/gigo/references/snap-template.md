# The Snap — Template

When the skill scaffolds a project, it writes `.claude/rules/snap.md` using this template. Adapt the specifics to the domain.

**This is the most important file the skill produces.** Named after Tony's snap — not Thanos's. It's not about indiscriminate wiping. It's about sacrificing what has to go so everything that matters survives. Without The Snap, every session adds rules, nothing removes them, and within weeks the context is bloated enough to actively hurt performance. The generated snap must carry this weight — it's not a logging utility, it's what protects the project.

---

## Template

Generate a `.claude/rules/snap.md` that follows this structure, adapted to the project:

```markdown
# The Snap

*Whatever it takes to protect the project.*

When the operator asks to save progress, wrap up, or end a session, follow this protocol. Two jobs, in this order:
1. **Protect the project** — audit, sacrifice what has to go so what matters survives
2. **Capture learnings** — route new knowledge to the right file

Job 1 is more important. A lean project with missing knowledge outperforms a bloated one with everything. Research shows bloated context files reduce task success rates while increasing cost by 20%+ (Gloaguen et al., arXiv:2602.11988). Every rule you add loads on every conversation and costs tokens, reasoning, and attention — even when irrelevant to the current task.

## The Audit (every session, not optional)

Before saving anything new, audit the existing rules. This runs every time.

**1. Line check.** Scan each `.claude/rules/` file. Any file approaching ~60 lines needs content moved to `.claude/references/` with a "When to Go Deeper" pointer.

**2. Derivability check.** For each rule, ask: "Can the agent figure this out by reading the project files?" If the codebase now makes a rule obvious — through code patterns, test structure, config files — it's served its purpose. Let it go. It's costing tokens for information the agent would find anyway.

**3. Overlap check.** Rules that say the same thing in different words, or rules that partially overlap. Merge into one clear statement. Also check for cross-file redundancy — the same rule appearing in multiple auto-loaded files (CLAUDE.md, standards.md, extension files, workflow.md). A rule should live in at most two auto-loaded locations: once briefly in a CLAUDE.md persona, once fully in the relevant rules file. More than that is bloat, not emphasis.

**4. Staleness check.** Has any rule become irrelevant? Early-project rules often don't apply once the project matures. They served their purpose — let them go.

**5. Cost check.** For each rule that survived steps 1-4, ask: "Is this worth loading on every single conversation, including ones where it doesn't apply?" If no, move to `.claude/references/`.

**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain domain-knowledge content (factual specifics, implementation patterns) that belongs in references? Persona entries in rules should be alignment signal only — quality bars, approach, constraints. Domain knowledge loads better on demand where it doesn't compete with the model's factual recall.

**7. Total budget check.** Count total lines across ALL `.claude/rules/` files. If approaching ~300 lines total, consolidate or move content to references. Per-file cap (~60) prevents individual bloat; total cap (~300) prevents systemic bloat.

**8. Coverage check.** Has the project grown into areas the team doesn't cover? If yes, suggest: "Consider running `/fury` to add expertise." If multiple files are over the line cap or the structure has drifted significantly, suggest: "Consider running `/smash` to restructure."

**9. Overwatch check.** Is the Overwatch section present in `workflow.md`? If the team has 3+ domain personas, is Hawkeye in `CLAUDE.md`? Is `.claude/references/overwatch.md` present? If any are missing, restore them — the overwatch system is not optional.

## Saving New Learnings

After the audit, capture what you learned this session. Route to the right file:

| Learning type | Where it goes |
|---|---|
| {domain pattern discovered} | `.claude/rules/{relevant-extension}.md` → Patterns section |
| {domain gotcha found} | `.claude/rules/standards.md` → Anti-Patterns section |
| {tool or dependency change} | `.claude/rules/{stack-or-equivalent}.md` |
| {quality insight} | `.claude/rules/standards.md` → Quality Gates section |
| {workflow improvement} | `.claude/rules/workflow.md` |
| {deep reference material} | `.claude/references/{topic}.md` (NOT rules) |

**Before adding anything new:**
- Does it overlap with an existing rule? → **Merge**, don't append.
- Can the agent figure this out from the project files? → **Don't write it.**
- Is it needed every conversation, or only sometimes? → Default to `.claude/references/`.
- Will adding this push the file past ~60 lines? → Move something else out first.

## What Never Goes in Rules

- Ephemeral task state (what you're working on right now)
- Things git history captures (who changed what, when)
- Reference-depth content (extended examples, deep-dives, pattern libraries)
- Things derivable from reading the project files
- Duplicates of existing rules in different words

## If Nothing Was Learned

Still run the audit. The audit is the primary job — saving is secondary. Say "No new learnings. Rules audited — [clean / let go of X / moved Y to references]."
```

---

## Domain-Specific Routing Examples

When generating the snap file, customize the "Saving New Learnings" routing table for the domain.

### Software Project

| Learning type | Where it goes |
|---|---|
| New architecture pattern | `.claude/rules/architecture.md` → Patterns |
| Dependency gotcha or version issue | `.claude/rules/stack.md` |
| Code standard discovered | `.claude/rules/code-standards.md` → Patterns |
| Testing insight | `.claude/rules/testing.md` |
| Security concern | `.claude/rules/standards.md` → Anti-Patterns |
| Framework-specific deep dive | `.claude/references/{framework}-patterns.md` |

### Fiction / Writing Project

| Learning type | Where it goes |
|---|---|
| Voice drift correction | `.claude/rules/voice-guide.md` |
| Plot structure insight | `.claude/rules/story-structure.md` |
| Character consistency rule | `.claude/rules/standards.md` |
| Genre convention discovered | `.claude/rules/genre-conventions.md` |
| Extended writing samples | `.claude/references/voice-examples.md` |

### Game Development Project

| Learning type | Where it goes |
|---|---|
| Engine pattern discovered | `.claude/rules/engine-patterns.md` |
| Performance gotcha | `.claude/rules/standards.md` → Anti-Patterns |
| Asset pipeline change | `.claude/rules/asset-pipeline.md` |
| Economy balance insight | `.claude/rules/economy-design.md` |
| Extended technical reference | `.claude/references/{topic}-deep-dive.md` |

### Research / Business / Music Projects

Adapt the routing table to the domain's structure. The pattern is always the same:
- Universal quality rules → `standards.md`
- Domain-specific patterns → the relevant extension file
- Deep reference material → `.claude/references/`

---

## Why The Snap Is the Most Important File

The skill assembles a great project on day one. But day one is the *easiest* day. The hard part is month two, when dozens of sessions have each added "just one more rule" and the rules have silently grown from lean and focused to bloated and counterproductive.

This happens to every project without active maintenance:
- Rules overlap (three slightly different ways of saying the same thing)
- Rules become derivable (the codebase grew to make them obvious)
- Reference-depth content sits in rules (loading every conversation when it's needed once a week)
- Early rules go stale (the project matured past them)

The Snap is the only thing that prevents this. It runs every session. It audits before it adds. It sacrifices what has to go so everything that matters survives. Without it, what the skill built will degrade until it's actively hurting the work it was designed to help. Whatever it takes.
