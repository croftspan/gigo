# Avengers, Assemble

**Build the best team in any field — before you write a single line.**

A Claude Code skill that researches your domain, finds the best practitioners, blends their philosophies into focused expert personas, and scaffolds a lean project that makes every future session smarter. Run it again later and it audits your setup, finds the gaps, and protects what you built.

> *"There was an idea... to bring together a group of remarkable people, so when we needed them, they could fight the battles we never could." — Nick Fury*

---

### The problem with every Claude Code project

You start with a blank `CLAUDE.md`. You write some rules, add some context, hope it's enough. A week in, the AI doesn't know the best practices for your domain. A month in, your rules files have grown with stuff that doesn't matter and are missing stuff that does.

[Research confirms this](https://arxiv.org/abs/2602.11988): bloated context files *reduce* task success rates while *increasing* cost by 20%+. More rules doesn't mean better results — it means more noise, diluted attention, and higher bills.

**Avengers Assemble fixes both problems.** Expert knowledge from day one. Active bloat prevention from day two.

---

## Getting Started

### Install

```bash
git clone https://github.com/Eaven/avengers-assemble.git
cp -r avengers-assemble/skills/avengers-assemble ~/.claude/skills/avengers-assemble
```

### Your first assembly

Open a new project and run the skill:

```bash
cd ~/projects/my-board-game
/avengers-assemble
```

Fury sees no `CLAUDE.md` and kicks off the assembly. It's a conversation — you describe what you're building, he does the rest.

```
You: "I'm designing a cooperative deck-building board game. 2-4 players,
     60 minute target play time. Fantasy theme but not generic tolkien
     stuff — more like Hades meets Slay the Spire on a tabletop."

Fury: "Want me to do a quick setup from what I know, or deep-research
        the current board game design landscape first?"

You: "Quick is fine"

Fury: researches the domain... identifies authorities in deck-builder
       design, cooperative game theory, tabletop development...

Fury: "Here's the team I'd assemble:

        The Systems Architect
        Blends Donald X. Vaccarino's deck-building engine design
        (Dominion) with Eric Lang's tension mechanics and Matt
        Leacock's cooperative balance philosophy (Pandemic). Owns
        card economy, action systems, and win/loss conditions.

        The Experience Designer
        Draws from Jamey Stegmaier's player engagement principles
        (Wingspan, Scythe) with Rob Daviau's legacy/narrative
        progression and Bruno Cathala's elegant interaction design.
        Owns table feel, player agency, and session pacing.

        The Production Lead
        Informed by Stonemaier Games' manufacturing pipeline,
        The Game Crafter's prototyping methodology, and
        Tabletop Simulator's digital playtesting workflow.
        Owns component specs, print-readiness, and prototype cycles.

        Quality bar: every card earns its place in the deck. If removing
        a card doesn't make the game worse, the card shouldn't exist.
        A full game fits in 60 minutes including teach time.

        Key anti-patterns I found: runaway leader in co-op (kills table
        feel), analysis paralysis from too many card options per turn,
        and component bloat that inflates manufacturing cost without
        improving gameplay.

        What do you think?"

You: "I like it but I don't need a production lead yet — we're
     months from manufacturing. And the fantasy theme is important,
     I want someone who gets worldbuilding."

Fury: drops Production Lead, researches narrative/worldbuilding
       authorities, re-presents with a new persona...

Fury: "Updated team:

        The Systems Architect — [same as above]

        The Experience Designer — [same as above]

        The World Builder
        Blends Patrick Rothfuss's lived-in world design with the
        Supergiant Games approach to mythological remixing (Hades,
        Pyre). Cultures feel discovered, not invented. Every
        mechanical faction has a narrative reason to exist.

        Ready to lock this in?"

You: "Lock it in"
```

Fury writes everything to disk:

```
CLAUDE.md                              # Team roster + project identity
.claude/rules/standards.md             # Quality gates + anti-patterns
.claude/rules/workflow.md              # Design-playtest-iterate loop
.claude/rules/snap.md                  # The Snap
.claude/rules/game-systems.md          # Deck-builder architecture rules
.claude/rules/worldbuilding.md         # Narrative design constraints
references/deckbuilder-patterns.md     # Deep card economy patterns
references/cooperative-balance.md      # Co-op tuning techniques
references/worldbuilding-guide.md      # Extended lore methodology
```

You now have a project where every session thinks like Vaccarino, Leacock, and Stegmaier — before you've designed a single card.

### Two months later

The game is taking shape. Playtesting reveals that 2-player mode feels flat — the co-op mechanics were tuned for 3-4 and don't scale down. You need expertise you don't have.

```
/avengers-assemble the 2-player mode is broken — co-op doesn't
scale down and we might need a competitive variant or a solo
mode with an AI opponent. I need someone who gets small player
count design.
```

Fury reads your existing team, researches small-count and solo board game design, and comes back:

```
Fury: "Your current team covers systems, experience, and world — but
        nobody specializes in player count scaling. Here's who I'd add:

        The Solo Architect
        Blends Morten Monrad Pedersen's solo AI design (the Automa
        system used in Scythe, Viticulture) with Shadi Torbey's
        elegant solo-only design (Onirim, Sylvion) and David
        Turczi's approach to scaling co-op games down to one.

        I'd also update game-systems.md with player count scaling
        patterns and add references/solo-ai-design.md for the
        Automa framework details.

        Want me to merge this in?"

You: "Do it"
```

New persona added to `CLAUDE.md`. Rules updated. References expanded. The project didn't start over — it grew.

---

## What It Produces

### Two-tier architecture

Every line in `.claude/rules/` loads on every conversation — even when irrelevant. So the skill is ruthlessly selective about what goes where.

**Tier 1: Lean rules** — auto-loaded, ~60 lines max per file

| File | What it does |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list |
| `.claude/rules/workflow.md` | How to approach work in this domain |
| `.claude/rules/snap.md` | **The Snap** — protects the project, whatever it takes |
| `.claude/rules/{extensions}.md` | Domain-specific rules as needed |

**Tier 2: Deep references** — on-demand, zero cost when unused

Extended examples, authority deep-dives, pattern libraries, and technique catalogs live in `references/`. Rules files include **"When to Go Deeper"** sections that tell the agent *when* to read them — not just that they exist. The agent loads `references/cooperative-balance.md` when tuning difficulty, not when writing flavor text.

### The non-derivable rule

The skill only writes what the agent can't figure out by reading the project:

| | Write it | Never write it |
|---|---|---|
| **Examples** | Philosophy, quality bars, blended authorities, anti-patterns | Directory structure, file listings, code patterns, codebase overviews |
| **Why** | Not discoverable from project files | Agent navigates codebases on its own — writing this wastes attention |

---

## Key Features

### Blended expert philosophies

Not "you are a senior developer" — that's generic. Instead: *"you work in the tradition of DHH's convention-over-configuration, with Kent Beck's testing discipline and Sandi Metz's object design sensibility."* Each authority brings something specific. The blend has a reason. The persona has opinions.

### Works for any domain

Software, fiction, game design, research, music, business — anything. Seven questions that work everywhere:

1. What are you building, and who is it for?
2. Who are the authorities?
3. What does the gold standard look like?
4. What are the core tools and processes?
5. What are the quality gates?
6. What are the common mistakes?
7. What does "done" look like?

No hardcoded categories. No routing logic.

### The Snap

Tony sacrificed himself so everyone else could keep going. The Snap here works the same way — rules that have served their purpose get cleared out so the ones that matter stay sharp.

Every project gets `snap.md`, which runs at the end of every session:

- **Audits first, saves second** — the primary job is protecting the project, not logging
- **Lets go of derivable rules** — if the codebase now makes it obvious, it's served its purpose
- **Merges overlaps** — three versions of the same rule become one
- **Enforces ~60 line caps** — pushes detail to references when files get heavy
- **Questions every rule** — "is this worth loading on every conversation?"
- **Flags gaps** — suggests `/avengers-assemble` when the project outgrows the team

Without The Snap, rules bloat within weeks. With it, they get sharper.

### Quick or deep research

- **Quick** (default) — Claude's training knowledge. Fast, usually sufficient.
- **Deep** — live web search for current authorities, communities, tools. For unfamiliar territory or production-grade work.

---

## Design Principles

1. **Conversational.** You talk, it works. No steps to memorize.
2. **It does the homework.** You don't need to know the domain's authorities.
3. **Blended philosophies.** Synthesis of real practitioners, not generic role-play.
4. **Every rule pays rent.** Auto-loaded rules cost tokens on every task. Only write rules worth that cost.
5. **Non-derivable only.** If the agent can figure it out from the project, don't write a rule.
6. **Task-aware depth.** Rules tell the agent *when* to read references, not just that they exist.
7. **The Snap.** The project gets sharper over time, not bigger. Whatever it takes.
8. **Nothing without approval.** It proposes. You approve. Files are written last.

---

## Behind the Design

This skill didn't start as a skill. It started as a problem we kept hitting at [Croftspan](https://croftspan.com) — an AI-native agency where every project runs on Claude Code. What follows is the thinking behind the decisions, what we tried, what failed, and what the research confirmed.

### The origin: dev kits that worked too well

Every Croftspan project begins with a "dev kit" — a set of files that give Claude the brain of a domain expert before any work starts. The first kit was for Ruby on Rails: DHH's philosophy, 37signals' practices, Rails 8's patterns, all distilled into lean rules files.

It worked immediately. Sessions with the rules produced better code, caught more edge cases, and needed fewer corrections than sessions without them. It wasn't just context — it was opinionated expertise that shaped every decision.

The question became: can this work for anything? Not just Rails, but children's novels, Roblox games, research papers, brand strategy? The answer turned out to be yes — the pattern is universal. Every domain has authorities, best practices, quality gates, and common mistakes. The skill just needed a framework for finding them in any field.

### Why blended philosophies, not single authorities

Early setups said things like "you are a senior Rails developer." Generic. No personality, no opinions, no specific approach to fight for. The breakthrough was modeling personas after Croftspan's C-suite — each executive is a blend of real practitioners. The CTO isn't "a CTO" — she works in the tradition of DHH's monolith philosophy with Sandi Metz's object design and Kent Beck's testing discipline. She has opinions. She pushes back. She catches things a generic role wouldn't.

Blending multiple authorities creates something better than any single authority alone. Each practitioner brings a specific strength, and the combination covers blind spots that any one person would have. It also prevents the persona from being a shallow impersonation — it's a synthesis with its own coherent worldview.

### The bloat problem (and what the research confirmed)

The first projects grew out of control. Every session discovered something worth remembering, so rules files grew monotonically — adding, never removing. Within weeks, context files were hundreds of lines long, full of overlapping rules, outdated guidance, and reference-depth detail that didn't need to load on every conversation.

We noticed performance degrading. Sessions took longer, made more mistakes, and sometimes ignored rules entirely — there was too much to attend to. We started pruning manually and saw immediate improvement.

Then [Gloaguen et al. (2026)](https://arxiv.org/abs/2602.11988) published "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" — the first rigorous study of how context files affect agent performance. Their findings confirmed exactly what we'd experienced:

- **Context files help, but only when lean and relevant.** Well-crafted files improve task success rates. Bloated ones reduce them.
- **The cost isn't just tokens — it's attention.** Irrelevant rules dilute the model's focus on rules that actually matter for the current task.
- **More requirements can hurt.** Adding unnecessary constraints makes tasks harder, not easier. The model spends reasoning effort on compliance with rules that don't apply.
- **20%+ cost increase** from bloated context, with *lower* success rates. You pay more and get worse results.

This research shaped three core decisions in the skill:

**The ~60 line cap.** Rules files must be ruthlessly lean. If it's approaching 60 lines, move detail to references. A 30-line file that nails the essentials outperforms a 100-line file that's thorough but dilutes attention.

**The non-derivable rule.** Only write rules for things the agent can't figure out by reading the project files. Philosophy, quality bars, blended authorities — write those, they're not discoverable. Directory structure, code patterns, file organization — never write those, the agent navigates codebases on its own. Codebase overviews are actively harmful because they waste attention on information the agent would have found anyway.

**The Snap.** Every project gets `snap.md` — named after Tony's snap, not Thanos's. It's not about indiscriminate wiping — it's about sacrificing what has to go so everything that matters survives. Before adding a rule: "Does this overlap with something that already exists? Can the agent figure this out from the code? Is this needed on every conversation or just sometimes?" After adding: "Is each rule still earning its token cost?" The project gets sharper over time, not bigger. Whatever it takes.

### Why two tiers instead of one

The obvious approach is one tier: put everything in `.claude/rules/` and let it load. Simpler. No decisions about what goes where.

The problem: every line in `rules/` loads on every conversation. A deep-dive on solo AI opponent design is invaluable when you're building the Automa system — and pure noise when you're writing card flavor text. Loading it every time wastes tokens and dilutes attention on whatever the agent is actually doing.

The two-tier architecture solves this. Tier 1 (rules) contains only what applies to *all* work — philosophy, quality gates, universal patterns. Tier 2 (references) contains everything else — extended examples, deep-dives, technique catalogs. The key innovation is **"When to Go Deeper"** — rules files don't just point to references, they tell the agent *when* to read them. "When tuning cooperative balance, read `references/cooperative-balance.md`." This makes the system task-aware: the agent loads deep context only when it's relevant.

### Why conversational, not procedural

Early versions used a phased approach: fill out this form, answer these questions, review this output. It felt like a wizard. Users didn't know the answers to half the questions (especially in unfamiliar domains), and the rigid structure prevented the natural back-and-forth that surfaces the best ideas.

The current design is a conversation. You say what you want to build. The skill does the research, proposes a team, and presents it. You react — "drop the production lead, add a worldbuilder," "I don't need a separate testing persona," "what about solo mode?" The skill adjusts. When it feels right, you lock it in.

This works better because the skill does the homework. You don't need to know who the best deck-builder designers are — the skill finds Vaccarino, Leacock, and Stegmaier and explains why each matters. Your job is taste and direction, not domain expertise.

### What we'd still like to figure out

**Persona interaction.** The assembled team currently lives as static rules. We think there's value in being able to consult individual personas in a conversational way — "What would The Systems Architect think about adding a fifth resource type?" — without bloating the always-on context. The architecture supports this (deep persona profiles in references, loaded on demand), but we haven't nailed the UX yet.

**Cross-project learning.** Right now each project's rules are independent. A pattern discovered in one Rails project could benefit another, but there's no mechanism for that. The Snap prevents bloat, but it doesn't help projects learn from siblings.

**Automated health checks.** The skill can audit a project when you run it, but it'd be better if The Snap could flag "your rules are getting stale, consider running `/avengers-assemble`" based on actual usage patterns rather than a generic periodic reminder.

---

### Further reading

- [Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" The research that validated (and quantified) the lean-context approach.
- [Croftspan](https://croftspan.com) — The agency where this methodology was developed and battle-tested.

---

## License

MIT
