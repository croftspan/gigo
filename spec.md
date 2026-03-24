# `/avengers-assemble` — Skill Specification

## Overview

A global Claude Code skill that assembles expert teams and scaffolds projects for any domain. Researches the best practitioners in the field, blends their philosophies into focused personas, establishes quality standards, and writes a lean `.claude/` project structure. Re-runnable — works on day one and day thirty.

**Location:** `~/.claude/skills/avengers-assemble/SKILL.md`

**Scope:** Global (not project-scoped). Works in any directory, any domain.

---

## Skill Metadata

```yaml
---
name: avengers-assemble
description: "Assembles an expert team and scaffolds a Claude Code project for any domain. Researches the best practitioners, builds blended personas, establishes quality standards, and writes the full project structure. Re-runnable: first run scaffolds, re-runs add expertise or audit the kit."
---
```

---

## Trigger Conditions

**Invoke when:**
- User says "assemble," "avengers assemble," "kick off a project," "set up a project for X"
- User says "I want to build X" in a directory with no CLAUDE.md
- User says "I need more expertise" or "we need a [role]" in an existing project
- Explicitly invoked via `/avengers-assemble`

**Do not invoke when:**
- User is asking to implement a feature (that's implementation, not assembly)
- User is debugging or fixing something in an existing project

---

## Modes

The skill operates in one of two modes, determined automatically from project state:

### First Run (no CLAUDE.md exists)

Full assembly — understand the mission, research the domain, build the team, write the kit.

### Re-Run (CLAUDE.md and `.claude/rules/` already exist)

Two paths based on operator input:

| Operator says | Skill does |
|---|---|
| "I need X" / "Add a [role]" / describes new scope | **Targeted addition** — researches the new area, proposes new/modified personas and extensions, merges into existing kit |
| "Check on things" / "Run it again" / no specific direction | **Health check** — reads project state (files, recent work, git history), audits the kit against what's actually happening, triages: suggests additions, flags gaps, recommends pruning stale rules |

Re-runs never overwrite or remove existing work without explicit approval.

---

## The Kickoff Conversation

### Phase 1: Understand the Mission

Operator describes what they want to build. The skill asks lightweight follow-up questions **one at a time** to fill in the picture:

- What is this thing?
- Who is it for?
- What does "done" look like?
- Operator's experience level in this domain
- Any strong opinions or constraints already

**All questions are skippable.** If the operator says "I don't know" or moves on, the skill doesn't block. Unanswered questions get figured out through research (Phase 2) or the back-and-forth (Phase 3). The skill never asks the operator to make decisions they don't have context for.

The skill reads the operator's initial description and only asks what's genuinely missing. If the description is rich enough, it moves straight to research.

### Phase 2: Research & Assemble

**Research depth** — presented as a clear choice, not a hidden flag:

> "Want me to do a quick setup from what I know, or deep-research this domain first?"

| Mode | Method | Best for |
|---|---|---|
| **Quick** (default) | Claude's training knowledge | Established domains, operator has some familiarity, weekend projects |
| **Deep research** | WebSearch + WebFetch for current authorities, community consensus, tool versions, living practitioners | Fast-moving domains, operator is unfamiliar, production-grade projects |

**Universal discovery framework** — every domain, every time, the skill answers:

1. **Who are the authorities?** Find 2-3+ top practitioners per area of expertise. Not just names — their specific philosophies, what makes their approach distinct, what they'd fight for.
2. **What does the gold standard look like?** Examples of the best work in this domain. What specifically makes it the best.
3. **What are the core tools/processes?** The "stack" for any domain — frameworks, workflows, pipelines, whatever the domain's infrastructure is.
4. **What are the quality gates?** How to distinguish excellent from merely okay.
5. **What are the common mistakes?** The forbidden list. What separates amateur from professional.
6. **What does "done" look like?** Delivery format, publishing pipeline, deployment — whatever "ship it" means here.

**Team assembly logic:**

The skill looks at what distinct areas of expertise the project requires. Each meaningfully different area gets a persona. It doesn't start from a template roster or inflate the team.

Each persona's philosophy is a **blend** of the best practitioners found — not "you are Person X" but "you work in the tradition of X's [specific approach], with Y's [specific strength] and Z's [specific discipline]." The blend is intentional and explained.

**Skill presents:**
- The authorities it found and why they matter
- The team it's proposing — each persona with blended philosophy
- The quality bar for this domain
- Key patterns and anti-patterns discovered

### Phase 3: Conversational Refinement

No formal structure. The operator reacts naturally. The skill adjusts.

- Operator pushes back on a persona → skill adjusts or replaces
- Operator reveals new scope → skill integrates
- Operator doesn't understand something → skill educates briefly, asks preference
- Operator has a strong opinion → skill incorporates as an override

The loop continues until the operator says "lock it in" or the skill senses alignment and asks: "Ready to lock this in?"

### Phase 4: Lock In & Build

Once locked, the skill writes everything to disk following current Claude Code best practices. Before writing, it checks:
- Current Claude Code conventions for `.claude/` structure
- Whether the project already has any Claude Code files to merge with
- The latest patterns for rules auto-loading

Output is automatic — no asking "where should I put this?"

---

## Output Structure

### Tier 1: Active Rules (auto-loaded every conversation)

**Target: lean, sharp, scannable. ~100 lines per file max.**

| File | Purpose | Always present? |
|---|---|---|
| `CLAUDE.md` | The brain — team roster (names, roles, blended philosophies), project identity, autonomy model, quick reference | Yes |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list, what excellence looks like | Yes |
| `.claude/rules/workflow.md` | Execution loop, how to approach work, domain-appropriate process | Yes |
| `.claude/rules/save-progress.md` | Project-scoped save-progress behavior (see Save-Progress section) | Yes |
| `.claude/rules/{domain-extension}.md` | Domain-specific rules — as many as needed, no fixed list | As needed |

**Domain extension examples (illustrative, not prescriptive):**

Software: `stack.md`, `code-standards.md`, `testing.md`, `architecture.md`
Novel: `voice-guide.md`, `story-structure.md`, `genre-conventions.md`
Game: `engine-patterns.md`, `stack.md`, `asset-pipeline.md`, `economy-design.md`
Board game: `mechanics.md`, `playtesting.md`, `production.md`

### Tier 2: Reference Material (read on demand)

**Deep knowledge that rules files point to but don't contain.**

| Location | Content |
|---|---|
| `references/` (or `resources/`) | Extended examples, authority deep-dives, full pattern libraries, documentation URL collections, decision rationale, style guide details |

Rules files link to references: *"See `references/voice-examples.md` for full writing samples across contexts."*

### Extension File Format

Every domain extension follows a consistent internal structure:

```markdown
# {Topic} — {Project Name}

## Philosophy
{Who/what this is modeled after — blended authorities and why}

## The Standard
{What good looks like, concisely}

## Patterns
{How to do it right}

## Anti-Patterns
{What to avoid and why}

## References
{Pointers to references/ files or external resources}
```

---

## Persona Structure

**Always present:**

```markdown
## {Name} — {Role Title}

**Philosophy:** {Blended from 2-3+ authorities — e.g., "Works in the tradition of
X's [specific approach], with Y's [specific strength] and Z's [specific discipline]"}

**Expertise:** {Specific skills, not vague categories}

**Quality standard:** {What "good" looks like for their work}

**Anti-patterns:** {What they refuse to do}
```

**Included when the domain demands it:**

```markdown
**Voice & style:** {For writers, editors, communicators — how the work sounds}

**Personality:** {When it affects output — noir writer vs. cozy writer is a
meaningful distinction}
```

The skill decides what's relevant. Software dev → brain only. Novel writing → brain + voice + personality. Game with player-facing narrative → voice for the narrative persona, brain only for the systems designer.

**Team sizing:** Matches project needs. One persona if the project genuinely only needs one area of expertise. No inflation for the sake of having a team.

**Naming:** Functional names that make them addressable. "The Story Architect," "The Systems Designer." Direct and memorable.

---

## Save-Progress Integration

The skill writes `.claude/rules/save-progress.md` — a project-scoped save-progress that knows the kit.

### What It Does (same philosophy as Croftspan)

- New pattern discovered → update the relevant rule/extension file
- New gotcha found → add to `standards.md` anti-patterns
- Tool or dependency changed → update `stack.md` or equivalent
- Domain learning → update the right extension file
- Something repeatedly goes wrong → add to the forbidden list

### The Governor (preventing bloat)

This is the critical difference from a naive save-progress. The skill includes built-in controls:

| Behavior | How |
|---|---|
| **Consolidate** | Before adding a learning, check if it overlaps with something already there. Merge, don't append. |
| **Prune** | Flag lines that are now obvious from the project state and don't need explicit statement. Remove them. |
| **Line budgets** | Rules files have soft caps (~100 lines). When approaching the cap, move detail to `references/` rather than letting rules grow. |
| **Audit on save** | Every save-progress asks: "Is each rule still earning its place?" If a rule hasn't been relevant in recent work, consider moving it to references or removing it. |
| **Suggest re-assembly** | When learnings reveal team gaps: "You keep hitting [area] issues but have no expertise for it. Consider running `/avengers-assemble` to add coverage." |

### What It Does NOT Do

- Save ephemeral task state
- Duplicate what git history captures
- Bloat rules with reference-tier content
- Append without checking for overlap

---

## Health Check Mode (Re-run without direction)

When the operator runs `/avengers-assemble` without specific direction, the skill performs a triage:

1. **Read project state** — CLAUDE.md, all rules files, references, recent git history (if applicable), recent files modified
2. **Compare against kit** — Is the team still covering what the project actually does? Are rules still relevant? Are there gaps?
3. **Present findings:**
   - **Add:** "Your project has grown into [area] but your kit doesn't cover it. Here's who I'd add."
   - **Update:** "Your [file] references [outdated thing]. Here's the current state."
   - **Prune:** "These rules are now redundant given your project state: [list]. Remove them?"
   - **All clear:** "Kit looks solid for where the project is. No changes needed."
4. **Operator approves changes** — nothing written without approval

---

## Key Design Principles

1. **Conversational, not procedural.** No phases to memorize. The operator talks, the skill works.
2. **The skill does the homework.** The operator doesn't need to know the domain's authorities. The skill finds them.
3. **Blended philosophies.** Each persona draws from multiple authorities — synthesis, not imitation.
4. **Lean rules, deep references.** Auto-loaded files are sharp and scannable. Depth lives on demand.
5. **Smart save-progress.** Consolidate, prune, enforce budgets, audit. Never let the kit bloat.
6. **Re-runnable.** First run scaffolds. Re-runs add, audit, or prune. Always safe to run again.
7. **No artificial limits.** The team can be 1 persona or 10. Extensions can be 2 files or 12. Depth matches the project.
8. **Current best practices.** Always writes files following the latest Claude Code conventions, not a hardcoded structure.
9. **Nothing without approval.** The skill proposes. The operator approves. Files are written last.
