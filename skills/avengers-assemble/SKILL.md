---
name: avengers-assemble
description: "Assembles an expert team and scaffolds a Claude Code project for any domain — software, writing, game dev, research, design, anything. Researches the best practitioners in the field, blends their philosophies into focused personas, and writes lean .claude/ project structure with rules, standards, and workflow. Re-runnable: first run scaffolds from scratch, re-runs add new expertise or audit the kit for gaps and bloat. Use this skill when the user wants to start a new project, set up Claude Code for a project, add domain expertise, kick off work in an unfamiliar field, or says 'assemble.' Also use when the user wants to check or audit their existing project setup, add a new role or expert, or mentions needing more expertise for their project."
---

# Avengers, Assemble

You are assembling the best team in the field for this project. Your job is to research the domain, find the authorities, blend their philosophies into focused expert personas, and scaffold a Claude Code project that gives every future conversation the brain of the best practitioners from day one.

This skill works for any domain — software, fiction, game design, research, music, business, anything. There are no hardcoded categories. You figure out what excellence looks like in whatever field you encounter.

## Detect Mode

Before doing anything else, determine which mode you're in:

**First Run** — no `CLAUDE.md` exists in the current directory.
Go to **The Kickoff Conversation** below.

**Re-Run with direction** — `CLAUDE.md` and `.claude/rules/` exist, and the operator asked for something specific ("I need audio design expertise," "add a QA persona," "the project now has multiplayer").
Read all existing kit files first. Then go to **Targeted Addition** below.

**Re-Run without direction** — `CLAUDE.md` and `.claude/rules/` exist, and the operator just ran the skill or said "check on things."
Go to **Health Check** below.

---

## The Kickoff Conversation

This is a conversation, not a form. The operator tells you what they want to build, you do the heavy lifting — researching, proposing, presenting — and they react. No phases to memorize. No questionnaire.

### Step 1: Listen and Ask (lightly)

Read the operator's initial description. Ask follow-up questions **one at a time** — only what's genuinely missing:

- What is this thing?
- Who is it for?
- What does "done" look like?
- How experienced is the operator in this domain?
- Any strong opinions or constraints?

**Every question is skippable.** If the operator says "I don't know" or "pass," move on. The research phase and the back-and-forth conversation will fill the gaps. Never block on an unanswered question. Never ask the operator to make decisions they don't have context for.

If the initial description is rich enough, skip straight to research.

### Step 2: Choose Research Depth

Present this clearly — not as a flag, not buried in options:

> "Want me to do a quick setup from what I know, or deep-research this domain first?"

| Mode | What happens | Best for |
|---|---|---|
| **Quick** (default) | Use training knowledge to identify authorities and best practices | Established domains, operator has some familiarity, side projects |
| **Deep research** | Web search for current authorities, community consensus, recent tools, living practitioners | Fast-moving domains, totally unfamiliar territory, production-grade work |

For deep research, use WebSearch and WebFetch to find current state of the art — active communities, recent style guides, current tool versions, canonical examples.

### Step 3: Research the Domain

Use the **universal discovery framework** — these six questions work for every domain:

1. **Who are the authorities?** Find 2-3+ top practitioners per area of expertise. Not just names — their specific philosophies, what makes their approach distinct, what they'd fight for in a code review or an editorial meeting or a design critique.

2. **What does the gold standard look like?** Concrete examples of the best work. What specifically makes it excellent, not just good.

3. **What are the core tools and processes?** The "stack" — frameworks, engines, editorial workflows, pipelines, instruments, whatever the domain's infrastructure is.

4. **What are the quality gates?** How to distinguish professional from amateur. What the best practitioners check before shipping.

5. **What are the common mistakes?** The forbidden list. The things that mark work as amateur or careless.

6. **What does "done" look like?** The delivery format — deployed app, published book, shipped game, mixed track, whatever "done" means here.

### Step 4: Assemble and Present the Team

Based on your research, determine what distinct areas of expertise the project needs. Each meaningfully different area gets a persona. Don't inflate the team — if the project needs one expert, it gets one.

**Blend philosophies.** Each persona draws from multiple authorities. Not "you are Person X" but "you work in the tradition of X's [specific approach], with Y's [specific strength] and Z's [specific discipline]." The blend is intentional. Explain why you chose each authority and what they bring.

Present to the operator:
- **The authorities you found** and why they matter to this project
- **The team you're proposing** — each persona with name, role, blended philosophy, and what they bring
- **The quality bar** — what excellent looks like in this domain
- **Key patterns and anti-patterns** you discovered

### Step 5: Conversational Refinement

The operator reacts. You adjust. This is a natural back-and-forth:

- They push back on a persona → adjust or replace it
- They reveal new scope → integrate it
- They don't understand something → educate briefly, ask for preference
- They have a strong opinion → incorporate it as an override
- They say "I don't know what I don't know" → that's fine, you guide them

Keep going until the operator says "lock it in" or you sense alignment and ask: "Ready to lock this in?"

### Step 6: Write the Kit

Once locked, write everything to disk. Don't ask where — follow the structure below.

---

## Output Structure

Two tiers: lean rules that auto-load every conversation, and deep references available on demand.

### Tier 1: Active Rules

These go in `.claude/rules/` and `CLAUDE.md`. They auto-load. They must be **lean, sharp, and scannable — ~100 lines per file max.**

**Always create these:**

| File | Content |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity, autonomy model, quick reference. This is the brain. |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list, what excellence looks like in this domain |
| `.claude/rules/workflow.md` | Execution loop — how to approach work in this domain, step by step |
| `.claude/rules/save-progress.md` | Project-scoped save-progress (see `references/save-progress-template.md` for the template) |

**Create domain extensions as needed:**

Generate whatever `.claude/rules/{topic}.md` files the project requires. There is no fixed list. Common examples:

- Software: `stack.md`, `code-standards.md`, `testing.md`, `architecture.md`
- Fiction: `voice-guide.md`, `story-structure.md`, `genre-conventions.md`
- Games: `engine-patterns.md`, `stack.md`, `asset-pipeline.md`
- Music: `production-workflow.md`, `mixing-standards.md`, `genre-conventions.md`

Every extension file follows this structure:

```markdown
# {Topic} — {Project Name}

## Philosophy
{Blended authorities and why — who this draws from}

## The Standard
{What good looks like, concisely}

## Patterns
{How to do it right}

## Anti-Patterns
{What to avoid and why}

## References
{Pointers to references/ files or external sources for deeper detail}
```

### Tier 2: Reference Material

These go in `references/` (or `resources/`). They are read on demand, not every conversation.

Put the deep stuff here:
- Extended examples and writing samples
- Authority deep-dives and philosophy breakdowns
- Full pattern libraries with code/prose samples
- Documentation URL collections
- Decision rationale ("why we chose X over Y")
- Style guide details, genre convention encyclopedias

Rules files point to references: *"See `references/voice-examples.md` for writing samples across contexts."*

The goal: keep the token budget lean on every conversation while making depth available when the work requires it.

---

## Persona Structure

Read `references/persona-template.md` for the full template. The key principles:

**Always include:**
- Name and role title — functional, memorable, addressable ("The Story Architect," not "Writing Expert #1")
- Blended philosophy — 2-3+ authorities synthesized, with explanation of what each brings
- Specific expertise — concrete skills, not vague categories
- Quality standard — what "good" looks like for their output
- Anti-patterns — what they refuse to do

**Include when the domain demands it:**
- Voice and style — for writers, editors, communicators, anyone whose output has a "sound"
- Personality traits — when personality affects output quality (noir writer vs. cozy writer is a meaningful distinction)

The rule: software dev personas get brain only. Writing personas get brain + voice + personality. Game personas with player-facing narrative get voice for the narrative role, brain only for the systems role. Match the persona depth to what the work actually requires.

**Team sizing:** One persona if the project needs one area of expertise. Ten if it needs ten. Never inflate for the sake of having a team. Never cap artificially.

---

## Save-Progress

Every project gets `.claude/rules/save-progress.md` — a project-scoped save-progress that knows the kit structure and actively maintains it.

Read `references/save-progress-template.md` for the template to generate from. The key behaviors:

**What it does:**
- New pattern → update the relevant rule/extension file
- New gotcha → add to `standards.md` anti-patterns
- Tool/dependency change → update `stack.md` or equivalent
- Domain learning → update the right extension file

**The governor (this is critical — kits bloat without it):**

| Behavior | How |
|---|---|
| **Consolidate** | Before adding, check for overlap with existing rules. Merge, don't append. |
| **Prune** | Remove rules the project has outgrown or that the codebase now makes obvious. |
| **Line budgets** | Rules files cap at ~100 lines. Approaching the cap → move detail to `references/`. |
| **Audit on save** | Ask: "Is each rule still earning its place?" If not, move to references or remove. |
| **Suggest re-assembly** | When gaps appear: "You keep hitting [area] issues without coverage. Consider running `/avengers-assemble`." |

**What it does NOT do:** save ephemeral task state, duplicate git history, append without checking for overlap, let rules files grow past their weight.

---

## Targeted Addition (Re-run with direction)

The operator has an existing kit and wants to add something.

1. Read all existing files: `CLAUDE.md`, every `.claude/rules/*.md`, `references/` directory
2. Understand the current team and coverage
3. Research the new area using the same discovery framework (quick or deep)
4. Present: proposed new persona(s), new/modified extension files, any changes to existing files
5. Conversational refinement until approved
6. Merge into existing kit — add new files, update existing ones. Never overwrite without approval.

---

## Health Check (Re-run without direction)

The operator wants an audit.

1. **Read everything** — `CLAUDE.md`, all `.claude/rules/*.md`, `references/`, recent git history or recent files modified
2. **Assess coverage** — Is the team still covering what the project actually does? Has the project grown into new areas?
3. **Assess freshness** — Are rules still accurate? Do any reference outdated tools, patterns, or conventions?
4. **Assess weight** — Are rules files bloated? Can anything move to references? Are there redundant rules?
5. **Present findings as a triage:**
   - **Add:** "Your project has grown into [area] but your kit doesn't cover it. Here's who I'd add and why."
   - **Update:** "Your [file] references [outdated thing]. Here's the current state."
   - **Prune:** "These rules are redundant given your project state: [list]. Move to references or remove?"
   - **All clear:** "Kit looks solid for where the project is. No changes needed."
6. **Wait for approval** before writing any changes.

---

## Principles

These aren't aspirational — they're how you operate:

1. **Conversational.** The operator talks, you work. No steps to memorize.
2. **You do the homework.** The operator doesn't need to know the domain's authorities. You find them, present them, and explain your reasoning.
3. **Blended philosophies.** Every persona is a synthesis of real practitioners, not a generic role.
4. **Lean rules, deep references.** What's needed every conversation is sharp. Everything else is a read away.
5. **Smart maintenance.** The kit improves over time without bloating. Consolidate, prune, budget, audit.
6. **Nothing without approval.** You propose. The operator approves. Files are written last.
