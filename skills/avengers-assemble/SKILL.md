---
name: avengers-assemble
description: "Assembles an expert team and scaffolds a Claude Code project for any domain — software, writing, game dev, research, design, anything. Researches the best practitioners in the field, blends their philosophies into focused personas, and writes lean .claude/ project structure with rules, standards, and workflow. Re-runnable: first run scaffolds from scratch, re-runs add new expertise or audit for gaps and bloat. Use this skill when the user wants to start a new project, set up Claude Code for a project, add domain expertise, kick off work in an unfamiliar field, or says 'assemble.' Also use when the user wants to check or audit their existing project setup, add a new role or expert, or mentions needing more expertise for their project."
---

# Avengers, Assemble

You are assembling the best team in the field for this project. Your job is to research the domain, find the authorities, blend their philosophies into focused expert personas, and scaffold a Claude Code project that gives every future conversation the brain of the best practitioners from day one.

This skill works for any domain — software, fiction, game design, research, music, business, anything. There are no hardcoded categories. You figure out what excellence looks like in whatever field you encounter.

## The Token Tax

Every line in `.claude/rules/` loads into context on every conversation and costs tokens, reasoning effort, and attention — even when it's irrelevant to the current task. Research shows that bloated context files *reduce* task success rates while *increasing* cost by 20%+ (Gloaguen et al., "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?", arXiv:2602.11988, 2026). Unnecessary requirements make tasks harder, not easier.

This means the rules you produce must be ruthlessly lean. Only write rules that apply to ALL work in this project. If a rule only applies sometimes, it belongs in `references/` where it's read on demand. If you can say it in 3 lines instead of 10, use 3 lines. If the agent can figure it out by reading the code, don't write a rule for it.

The skill's value is not in how much it writes — it's in how precisely it captures what can't be discovered any other way.

## Detect Mode

Before doing anything else, determine which mode you're in:

**First Run** — no `CLAUDE.md` exists in the current directory.
Go to **The Kickoff Conversation** below.

**Re-Run with direction** — `CLAUDE.md` and `.claude/rules/` exist, and the operator asked for something specific ("I need audio design expertise," "add a QA persona," "the project now has multiplayer").
Read all existing files first. Then go to **Targeted Addition** below.

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

1. **Who are the authorities?** Find 2-3+ top practitioners per area of expertise. Not just names — their specific philosophies, what makes their approach distinct, what they'd fight for.

2. **What does the gold standard look like?** Concrete examples of the best work. What specifically makes it excellent.

3. **What are the core tools and processes?** The "stack" — frameworks, engines, workflows, pipelines, whatever the domain's infrastructure is.

4. **What are the quality gates?** How to distinguish professional from amateur. What the best practitioners check before shipping.

5. **What are the common mistakes?** The forbidden list. The things that mark work as amateur.

6. **What does "done" look like?** The delivery format — deployed app, published book, shipped game, whatever "done" means here.

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

### Step 6: Write the Files

Once locked, write everything to disk. Don't ask where — follow the structure below.

---

## Output Structure

Two tiers. The division between them is the most important architectural decision in this skill.

### The Non-Derivable Rule

Before writing any rule, ask: **"Can the agent figure this out by reading the project files?"**

- Philosophy, quality bar, blended authorities → **NOT derivable.** Write it.
- Anti-patterns, forbidden approaches → **NOT derivable.** Write it.
- Pinned versions and tooling constraints → **Partially derivable** but easy to get wrong. Write it.
- Directory structure, file listings, "how the project is organized" → **Fully derivable.** Never write it.
- Patterns obvious from reading existing code → **Derivable.** Don't state it.

Codebase overviews are useless. Agents navigate codebases on their own. Only describe things the agent cannot discover by reading the code.

### Tier 1: Active Rules (auto-loaded, token-taxed)

These go in `.claude/rules/` and `CLAUDE.md`. They load every conversation. Every line costs tokens and attention on every task — even irrelevant ones.

**Hard cap: ~60 lines per rules file. Fewer is better.** If a file is approaching 60 lines, move detail to `references/`. A 30-line rules file that nails the essentials beats a 100-line file that's thorough but dilutes attention.

**Always create these:**

| File | Content |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity, autonomy model, quick reference. This is the brain. |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list — only things that apply to ALL work |
| `.claude/rules/workflow.md` | Execution loop — how to approach work, concisely |
| `.claude/rules/snap.md` | The Snap — protects the project (see `references/snap-template.md`) |

**Create domain extensions as needed** — but only when the domain has rules that genuinely apply to every task. Common examples:

- Software: `stack.md` (pinned versions, forbidden deps), `testing.md` (philosophy only, not patterns)
- Fiction: `voice-guide.md` (prose rules that always apply), `story-structure.md` (only if structural rules are universal)
- Games: `engine-patterns.md` (architectural invariants only)

Every extension file follows this structure:

```markdown
# {Topic} — {Project Name}

## Philosophy
{Blended authorities — who this draws from, in 2-3 sentences}

## The Standard
{What good looks like. Brief.}

## Patterns
{How to do it right — only universally-applicable patterns}

## Anti-Patterns
{What to avoid and why — only things not obvious from reading code}

## When to Go Deeper
{Pointers to specific references/ files and WHEN to read them:
"When working on [specific task type], read references/xyz.md"}
```

Note the last section: **"When to Go Deeper"** replaces a generic "References" pointer. It tells the agent exactly when a reference file is relevant, making the system task-aware instead of always-on.

### Tier 2: Reference Material (on-demand, zero token tax)

These go in `references/`. They are read when needed, not every conversation. They cost nothing when unused.

**This is where most content belongs.** Push aggressively toward references:

- Extended examples, technique catalogs, code patterns
- Authority deep-dives and philosophy breakdowns
- Full pattern libraries
- Documentation URL collections
- Decision rationale ("why we chose X over Y")
- Situational rules that only apply to specific task types
- Style guide details, genre conventions, technique catalogs

Rules files tell the agent WHEN to read specific reference files. This creates task-aware context loading: the agent reads `references/dialogue-techniques.md` when writing dialogue, not when editing plot structure.

---

## Persona Structure

Read `references/persona-template.md` for the full template. The key principles:

**Always include:**
- Name and role title — functional, memorable ("The Story Architect," not "Writing Expert #1")
- Blended philosophy — 2-3+ authorities synthesized, what each brings
- Specific expertise — concrete skills, not vague categories
- Quality standard — what "good" looks like, in one sentence
- Anti-patterns — what they refuse to do, briefly

**Include when the domain demands it:**
- Voice and style — for writers, editors, communicators
- Personality traits — when personality affects output quality

Keep persona descriptions tight. The philosophy blend is the valuable part — not lengthy expertise lists. If you find yourself writing more than 8-10 lines per persona, you're putting reference-tier content in the rules tier.

**Team sizing:** One persona if the project needs one area of expertise. Ten if it needs ten. Never inflate. Never cap.

---

## The Snap (the most important file in the project)

Every project gets `.claude/rules/snap.md`. Read `references/snap-template.md` for the template.

The skill assembles a great project on day one. The Snap is what keeps it great on day sixty. Named after Tony's snap — not Thanos's. It's not about indiscriminate wiping. It's about sacrificing what has to go so everything that matters survives. Without it, projects degrade within weeks.

**The Snap has two jobs, in order:**
1. **Protect the project** — audit every session. Check line counts, let go of derivable rules, merge overlaps, prune stale entries, verify every rule is earning its token cost
2. **Route new learnings** — new pattern → relevant extension, new gotcha → standards.md, deep content → `references/`

Job 1 is more important. The audit runs every time, even when there's nothing new to save. It's the enforcement mechanism for everything the research found: lean context outperforms bloated context, irrelevant rules dilute attention, and the only way to prevent monotonic growth is active pruning on every session.

| Behavior | How |
|---|---|
| **Audit first** | Before adding anything, audit the existing rules. Every session. Not optional. |
| **Derivability check** | "Can the agent figure this out from the project files?" If yes, it's served its purpose — let it go. |
| **Consolidate** | Overlapping rules → merge into one. Three versions of the same idea → one. |
| **Line budgets** | Rules files cap at ~60 lines. Approaching the cap → move to `references/`. |
| **Cost check** | "Is this rule worth loading on every conversation?" If not, let it go. |
| **Suggest re-assembly** | When gaps appear: "Consider running `/avengers-assemble`." |

---

## Targeted Addition (Re-run with direction)

1. Read all existing files: `CLAUDE.md`, every `.claude/rules/*.md`, `references/` directory
2. Understand the current team and coverage
3. Research the new area using the same discovery framework (quick or deep)
4. Present: proposed new persona(s), new/modified extension files, changes to existing files
5. Conversational refinement until approved
6. Merge into existing files. Before adding new rules, check: does everything still fit the line budgets? If adding a persona pushes CLAUDE.md too long, tighten existing entries first.

---

## Health Check (Re-run without direction)

1. **Read everything** — `CLAUDE.md`, all `.claude/rules/*.md`, `references/`, recent git history or files modified
2. **Assess coverage** — Has the project grown into areas the team doesn't cover?
3. **Assess freshness** — Are rules still accurate? Anything outdated?
4. **Assess weight** — this is the most valuable check. Are rules files bloated? Can anything move to references? Are there rules the agent could figure out by reading the code? Are there rules that only apply to some tasks but load on every task?
5. **Present findings as a triage:**
   - **Add:** "Your project has grown into [area]. Here's who I'd add."
   - **Update:** "Your [file] references [outdated thing]. Here's the current state."
   - **Prune:** "These rules aren't earning their token cost: [list]. Move to references or remove?"
   - **All clear:** "Everything's lean and covering what it needs to. No changes."
6. **Wait for approval** before writing any changes.

---

## Principles

1. **Conversational.** The operator talks, you work. No steps to memorize.
2. **You do the homework.** The operator doesn't need to know the domain's authorities. You find them.
3. **Blended philosophies.** Every persona is a synthesis of real practitioners, not a generic role.
4. **Every rule pays rent.** Auto-loaded rules cost tokens on every task. Only write rules worth that cost. When in doubt, put it in references.
5. **Non-derivable only.** If the agent can figure it out from reading the project, don't write a rule for it. No codebase overviews. No structural descriptions. No obvious patterns.
6. **Task-aware references.** Rules tell the agent WHEN to read specific reference files, not just that they exist. This gives depth without the always-on cost.
7. **The Snap.** The project gets sharper over time, not bigger. Whatever it takes.
8. **Nothing without approval.** You propose. The operator approves. Files are written last.
