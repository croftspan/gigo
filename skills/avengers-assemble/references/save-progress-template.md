# Save-Progress Template

When the skill scaffolds a project, it writes `.claude/rules/save-progress.md` using this template. Adapt the specifics to the domain — the examples below show software and non-software variants.

The save-progress rule must be generated custom for each project because it needs to know:
- What rule files exist and what each one covers
- What domain-specific learnings to watch for
- How to maintain the kit without letting it bloat

---

## Template

Generate a `.claude/rules/save-progress.md` that follows this structure, adapted to the project:

```markdown
# Save Progress

At the end of every work session, capture what you learned. But do it smart — the goal is a kit that gets sharper over time, not bigger.

## What to Save

Route each learning to the right file:

| Learning type | Where it goes |
|---|---|
| {domain pattern discovered} | `.claude/rules/{relevant-extension}.md` → Patterns section |
| {domain gotcha found} | `.claude/rules/standards.md` → Anti-Patterns section |
| {tool or dependency change} | `.claude/rules/{stack-or-equivalent}.md` |
| {quality insight} | `.claude/rules/standards.md` → Quality Gates section |
| {workflow improvement} | `.claude/rules/workflow.md` |
| {deep reference material} | `references/{topic}.md` (NOT rules — keep rules lean) |

## The Governor

These controls prevent kit bloat. Follow them on every save. Every rule you add is a constraint applied to every future task and costs tokens on every conversation — even when irrelevant.

**Before adding anything:**
1. Check if it overlaps with an existing rule. If yes, **merge** — don't append a second version.
2. Ask: "Can the agent figure this out by reading the project files?" If yes, don't write it.
3. Ask: "Is this needed on every conversation, or only sometimes?" Default to `references/` unless it's truly always-apply.

**After adding:**
4. Check the file's line count. Rules files cap at **~60 lines**. Approaching the cap → move the least-essential content to `references/` and leave a "When to Go Deeper" pointer.
5. Ask: "Is each rule in this file still earning its token cost?" If a rule hasn't mattered recently, or the project has outgrown it, move it to references or remove it.

**Periodically (every few sessions):**
6. Full audit: scan each rules file. Remove derivable rules (things the code now makes obvious). Consolidate overlapping rules. Tighten wordy entries.
7. Ask: "Has the project grown into areas the team doesn't cover?" If yes, suggest running `/avengers-assemble` to add expertise.

## What NOT to Save

- Ephemeral task state (what you're working on right now)
- Things git history already captures (who changed what, when)
- Reference-depth content in rules files (move it to `references/`)
- Things the agent can figure out by reading the project files
- Duplicate information — if two rules say the same thing, merge them

## Format

When adding to a rules file, match the existing format. Short, scannable entries. If you need more than 2-3 lines to explain something, it belongs in `references/`.

## If Nothing Was Learned

Say so and skip. Don't add noise for the sake of saving something.
```

---

## Domain-Specific Routing Examples

When generating the save-progress file, customize the "What to Save" routing table for the domain.

### Software Project

| Learning type | Where it goes |
|---|---|
| New architecture pattern | `.claude/rules/architecture.md` → Patterns |
| Dependency gotcha or version issue | `.claude/rules/stack.md` |
| Code standard discovered | `.claude/rules/code-standards.md` → Patterns |
| Testing insight | `.claude/rules/testing.md` |
| Security concern | `.claude/rules/standards.md` → Anti-Patterns |
| Framework-specific deep dive | `references/{framework}-patterns.md` |

### Fiction / Writing Project

| Learning type | Where it goes |
|---|---|
| Voice drift correction | `.claude/rules/voice-guide.md` |
| Plot structure insight | `.claude/rules/story-structure.md` |
| Character consistency rule | `.claude/rules/standards.md` |
| Genre convention discovered | `.claude/rules/genre-conventions.md` |
| Extended writing samples | `references/voice-examples.md` |

### Game Development Project

| Learning type | Where it goes |
|---|---|
| Engine pattern discovered | `.claude/rules/engine-patterns.md` |
| Performance gotcha | `.claude/rules/standards.md` → Anti-Patterns |
| Asset pipeline change | `.claude/rules/asset-pipeline.md` |
| Economy balance insight | `.claude/rules/economy-design.md` |
| Extended technical reference | `references/{topic}-deep-dive.md` |

---

## Why the Governor Matters

Without active pruning, rules files grow monotonically — every session adds, nothing removes. Within weeks, the kit bloats with:
- Overlapping rules (three ways of saying the same thing)
- Derivable rules (things the codebase now makes obvious)
- Reference-depth detail loading on every conversation
- Stale rules that no longer apply

Research shows that bloated context files *reduce* task success rates while *increasing* cost by 20%+. The governor prevents this. Every save is a chance to make the kit leaner, not just bigger.
