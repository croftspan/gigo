# Avengers, Assemble

A Claude Code skill that assembles expert teams for any project — software, fiction, games, research, anything — before you write a single line.

You describe what you're building. It researches the domain, finds the best practitioners, blends their philosophies into focused personas, and scaffolds a lean Claude Code project. Run it again later and it audits your setup for gaps and bloat.

## Why This Exists

Every Claude Code project starts with a blank `CLAUDE.md`. You write some rules, add some context, hope it's enough. A week in, the AI doesn't know the best practices for your domain. A month in, your rules files have grown with things that don't matter and are missing things that do.

Research on LLM context management shows that bloated instruction files *reduce* task success rates while *increasing* cost by 20%+ ([Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"). More rules doesn't mean better results — it means more noise, diluted attention, and higher bills.

**Avengers Assemble solves both problems.** It gives every project the brain of the best practitioners from day one — and actively prevents the bloat that degrades performance over time.

## How It Works

```
You: "I'm building a children's mystery novel series for ages 10-14"

Skill: researches the domain... finds Wendelin Van Draanen's plot
       structure, Blue Balliett's puzzle design, Kate DiCamillo's
       prose discipline...

Skill: "Here's the team I'd assemble:
        - The Story Architect — blends Van Draanen's clue pacing
          with Balliett's intellectual puzzle design
        - The Prose Stylist — DiCamillo's clarity with Rebecca
          Stead's emotional precision
        - The Age Lens — calibrated to Fountas & Pinnell's
          reading level research

        Ready to lock this in?"

You: "Make it darker — more Lemony Snicket"

Skill: adjusts, re-presents...

You: "Lock it in"

Skill: writes CLAUDE.md, .claude/rules/, references/ — done.
```

No forms. No questionnaires. A conversation that ends with a fully scaffolded project.

## What It Produces

### Two-tier architecture

**Tier 1: Lean rules** (auto-loaded, ~60 lines max per file)

| File | Purpose |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list |
| `.claude/rules/workflow.md` | How to approach work in this domain |
| `.claude/rules/save-progress.md` | Smart maintenance that keeps the kit sharp |
| `.claude/rules/{extensions}.md` | Domain-specific rules as needed |

**Tier 2: Deep references** (on-demand, zero token cost when unused)

Extended examples, authority deep-dives, pattern libraries, writing samples, and documentation links live in `references/` — loaded only when relevant, not every conversation.

Rules files include **"When to Go Deeper"** sections that tell the agent *when* to read specific references. The agent reads `references/dialogue-techniques.md` when writing dialogue, not when editing plot structure. This gives depth without always-on cost.

### The non-derivable rule

The skill only writes rules for things the agent can't figure out by reading the project files:

- Philosophy, quality bar, blended authorities — **write it** (not derivable)
- Anti-patterns, forbidden approaches — **write it** (not derivable)
- Directory structure, file listings, code patterns — **never write it** (fully derivable)

Codebase overviews are useless. Agents navigate codebases on their own. The skill captures only what can't be discovered any other way.

## Key Features

### Blended expert philosophies

Every persona draws from multiple real authorities. Not "you are a senior developer" — that's generic. Instead: "you work in the tradition of DHH's convention-over-configuration, with Kent Beck's testing discipline and Sandi Metz's object design sensibility." Opinions from practitioners with track records, blended intentionally.

### Works for any domain

Software, fiction, game design, research, music, business — anything. A universal discovery framework finds what excellence looks like in any field:

1. Who are the authorities?
2. What does the gold standard look like?
3. What are the core tools and processes?
4. What are the quality gates?
5. What are the common mistakes?
6. What does "done" look like?

No hardcoded categories. No routing logic. Just a framework that works everywhere.

### Smart save-progress with governor

The kit doesn't fossilize after day one. The included save-progress actively maintains it:

- **Consolidates** — merges learnings with existing rules instead of appending
- **Prunes** — removes rules the project has outgrown or the code now makes obvious
- **Enforces line budgets** — moves detail to references when rules files approach ~60 lines
- **Audits on every save** — "is each rule still earning its token cost?"
- **Suggests re-assembly** — when it spots gaps the team doesn't cover

Without the governor, kits bloat within weeks. Every session adds, nothing removes, and soon the context file is actively hurting performance. The governor prevents this.

### Re-runnable

First run scaffolds. Every run after that makes it better.

| You say | Skill does |
|---|---|
| "I need audio design expertise" | Researches the domain, proposes new persona, merges into kit |
| "Check on things" | Audits the kit — finds bloat, gaps, stale rules |
| "Run it again" | Full health check with triage: add, update, prune, or all clear |

### Quick or deep research

- **Quick** (default) — uses Claude's knowledge to identify authorities and best practices
- **Deep research** — web search for current state of the art, active communities, living practitioners

## Installation

Clone the repo and copy the skill to your Claude Code skills directory:

```bash
git clone https://github.com/Eaven/avengers-assemble.git
cp -r avengers-assemble/skills/avengers-assemble ~/.claude/skills/avengers-assemble
```

## Usage

**New project:**
```
cd ~/projects/my-new-thing
/avengers-assemble
```

**Add expertise:**
```
/avengers-assemble I need someone who knows multiplayer networking
```

**Health check:**
```
/avengers-assemble
```
Run in an existing project without direction to audit your setup.

## Example Output

A Roblox game:
```
CLAUDE.md                              # Team + identity
.claude/rules/standards.md             # Quality gates
.claude/rules/workflow.md              # Dev loop
.claude/rules/save-progress.md         # Kit maintenance
.claude/rules/stack.md                 # Luau, Rojo, Wally, versions
.claude/rules/engine-patterns.md       # Architecture invariants
references/luau-style-guide.md         # Full style reference
references/datastore-patterns.md       # Extended examples
```

A children's novel:
```
CLAUDE.md                              # Team + identity
.claude/rules/standards.md             # Quality gates
.claude/rules/workflow.md              # Editorial process
.claude/rules/save-progress.md         # Kit maintenance
.claude/rules/voice-guide.md           # Prose rules
.claude/rules/story-structure.md       # Mystery plotting
references/voice-examples.md           # Writing samples
references/mystery-plotting.md         # Extended patterns
```

A SaaS app:
```
CLAUDE.md                              # Team + identity
.claude/rules/standards.md             # Quality gates
.claude/rules/workflow.md              # Dev loop
.claude/rules/save-progress.md         # Kit maintenance
.claude/rules/stack.md                 # Framework, DB, versions
.claude/rules/testing.md               # Test philosophy
references/architecture-decisions.md   # Extended rationale
references/deployment-guide.md         # Infrastructure detail
```

Every project gets exactly what it needs. No more, no less.

## Design Principles

1. **Conversational.** You talk, it works. No steps to memorize.
2. **It does the homework.** You don't need to know the domain's authorities.
3. **Blended philosophies.** Synthesis of real practitioners, not generic role-play.
4. **Every rule pays rent.** Auto-loaded rules cost tokens on every task. Only write rules worth that cost.
5. **Non-derivable only.** If the agent can figure it out from reading the project, don't write a rule.
6. **Task-aware depth.** Rules tell the agent *when* to read references, not just that they exist.
7. **Smart maintenance.** The kit gets sharper over time, not bigger.
8. **Nothing without approval.** It proposes. You approve. Files are written last.

## Behind the Design

This skill didn't start as a skill. It started as a problem we kept hitting at [Croftspan](https://croftspan.com) — an AI-native agency where every project runs on Claude Code. What follows is the thinking behind the decisions, what we tried, what failed, and what the research confirmed.

### The origin: dev kits that worked too well

Every Croftspan project begins with a "dev kit" — a set of files that give Claude the brain of a domain expert before any work starts. The first kit was for Ruby on Rails: DHH's philosophy, 37signals' practices, Rails 8's patterns, all distilled into lean rules files.

It worked immediately. Sessions that used the kit produced better code, caught more edge cases, and needed fewer corrections than sessions without it. The kit wasn't just context — it was opinionated expertise that shaped every decision.

The question became: can this work for anything? Not just Rails, but children's novels, Roblox games, research papers, brand strategy? The answer turned out to be yes — the pattern is universal. Every domain has authorities, best practices, quality gates, and common mistakes. The skill just needed a framework for finding them in any field.

### Why blended philosophies, not single authorities

Early kits said things like "you are a senior Rails developer." Generic. No personality, no opinions, no specific approach to fight for. The breakthrough was modeling personas after Croftspan's C-suite — each executive is a blend of real practitioners. The CTO isn't "a CTO" — she works in the tradition of DHH's monolith philosophy with Sandi Metz's object design and Kent Beck's testing discipline. She has opinions. She pushes back. She catches things a generic role wouldn't.

Blending multiple authorities creates something better than any single authority alone. Each practitioner brings a specific strength, and the combination covers blind spots that any one person would have. It also prevents the persona from being a shallow impersonation — it's a synthesis with its own coherent worldview.

### The bloat problem (and what the research confirmed)

The first kits grew out of control. Every session discovered something worth remembering, so rules files grew monotonically — adding, never removing. Within weeks, context files were hundreds of lines long, full of overlapping rules, outdated guidance, and reference-depth detail that didn't need to load on every conversation.

We noticed performance degrading. Sessions took longer, made more mistakes, and sometimes ignored rules entirely — there was too much to attend to. We started pruning manually and saw immediate improvement.

Then [Gloaguen et al. (2026)](https://arxiv.org/abs/2602.11988) published "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" — the first rigorous study of how context files affect agent performance. Their findings confirmed exactly what we'd experienced:

- **Context files help, but only when lean and relevant.** Well-crafted files improve task success rates. Bloated ones reduce them.
- **The cost isn't just tokens — it's attention.** Irrelevant rules dilute the model's focus on rules that actually matter for the current task.
- **More requirements can hurt.** Adding unnecessary constraints makes tasks harder, not easier. The model spends reasoning effort on compliance with rules that don't apply.
- **20%+ cost increase** from bloated context, with *lower* success rates. You pay more and get worse results.

This research shaped three core decisions in the skill:

**The ~60 line cap.** Rules files must be ruthlessly lean. If it's approaching 60 lines, move detail to references. A 30-line file that nails the essentials outperforms a 100-line file that's thorough but dilutes attention.

**The non-derivable rule.** Only write rules for things the agent can't figure out by reading the project files. Philosophy, quality bars, blended authorities — write those, they're not discoverable. Directory structure, code patterns, file organization — never write those, the agent navigates codebases on its own. Codebase overviews are actively harmful because they waste attention on information the agent would have found anyway.

**The governor.** Every project's save-progress includes active pruning and consolidation. Before adding a rule: "Does this overlap with something that already exists? Can the agent figure this out from the code? Is this needed on every conversation or just sometimes?" After adding: "Is each rule still earning its token cost?" The kit gets sharper over time, not bigger.

### Why two tiers instead of one

The obvious approach is one tier: put everything in `.claude/rules/` and let it load. Simpler. No decisions about what goes where.

The problem: every line in `rules/` loads on every conversation. A deep-dive on Roblox DataStore patterns is invaluable when you're implementing persistence — and pure noise when you're tweaking UI colors. Loading it every time wastes tokens and dilutes attention on whatever the agent is actually doing.

The two-tier architecture solves this. Tier 1 (rules) contains only what applies to *all* work — philosophy, quality gates, universal patterns. Tier 2 (references) contains everything else — extended examples, deep-dives, technique catalogs. The key innovation is **"When to Go Deeper"** — rules files don't just point to references, they tell the agent *when* to read them. "When writing dialogue scenes, read `references/dialogue-techniques.md`." This makes the system task-aware: the agent loads deep context only when it's relevant.

### Why conversational, not procedural

Early versions used a phased approach: fill out this form, answer these questions, review this output. It felt like a wizard. Users didn't know the answers to half the questions (especially in unfamiliar domains), and the rigid structure prevented the natural back-and-forth that surfaces the best ideas.

The current design is a conversation. You say what you want to build. The skill does the research, proposes a team, and presents it. You react — "make it darker," "I don't need a separate testing persona," "what about multiplayer?" The skill adjusts. When it feels right, you lock it in.

This works better because the skill does the homework. You don't need to know who the authorities are in children's mystery fiction — the skill finds Wendelin Van Draanen, Blue Balliett, and Lemony Snicket and explains why each matters. The operator's job is taste and direction, not domain expertise.

### What we'd still like to figure out

**Persona interaction.** The assembled team currently lives as static rules. We think there's value in being able to consult individual personas in a conversational way — "What would The Story Architect think about this plot twist?" — without bloating the always-on context. The architecture supports this (deep persona profiles in references, loaded on demand), but we haven't nailed the UX yet.

**Cross-project learning.** Right now each project's kit is independent. A pattern discovered in one Rails project could benefit another, but there's no mechanism for that. The governor prevents kits from growing, but it doesn't help them learn from siblings.

**Automated health checks.** The skill can audit a kit when you run it, but it'd be better if the save-progress could flag "your kit is getting stale, consider running `/avengers-assemble`" based on actual usage patterns rather than a generic periodic reminder.

### Further reading

- [Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" The research that validated (and quantified) the lean-context approach.
- [Croftspan](https://croftspan.com) — The agency where this methodology was developed and battle-tested across software, branding, and strategy projects.

## License

MIT
