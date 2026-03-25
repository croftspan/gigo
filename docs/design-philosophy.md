# Behind the Design

This skill didn't start as a skill. It started as a problem we kept hitting at [Croftspan](https://croftspan.com) — an AI-native agency where every project runs on Claude Code. What follows is the thinking behind the decisions, what we tried, what failed, and what the research confirmed.

## The origin: dev kits that worked too well

Every Croftspan project begins with a "dev kit" — a set of files that give Claude the brain of a domain expert before any work starts. The first kit was for Ruby on Rails: DHH's philosophy, 37signals' practices, Rails 8's patterns, all distilled into lean rules files.

It worked immediately. Sessions with the rules produced better code, caught more edge cases, and needed fewer corrections than sessions without them. It wasn't just context — it was opinionated expertise that shaped every decision.

The question became: can this work for anything? Not just Rails, but children's novels, Roblox games, research papers, brand strategy? The answer turned out to be yes — the pattern is universal. Every domain has authorities, best practices, quality gates, and common mistakes. The skill just needed a framework for finding them in any field.

## Why blended philosophies, not single authorities

Early setups said things like "you are a senior Rails developer." Generic. No personality, no opinions, no specific approach to fight for. The breakthrough was modeling personas after Croftspan's C-suite — each executive is a blend of real practitioners. The CTO isn't "a CTO" — she works in the tradition of DHH's monolith philosophy with Sandi Metz's object design and Kent Beck's testing discipline. She has opinions. She pushes back. She catches things a generic role wouldn't.

Blending multiple authorities creates something better than any single authority alone. Each practitioner brings a specific strength, and the combination covers blind spots that any one person would have. It also prevents the persona from being a shallow impersonation — it's a synthesis with its own coherent worldview.

## The bloat problem (and what the research confirmed)

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

## Why two tiers instead of one

The obvious approach is one tier: put everything in `.claude/rules/` and let it load. Simpler. No decisions about what goes where.

The problem: every line in `rules/` loads on every conversation. A deep-dive on solo AI opponent design is invaluable when you're building the Automa system — and pure noise when you're writing card flavor text. Loading it every time wastes tokens and dilutes attention on whatever the agent is actually doing.

The two-tier architecture solves this. Tier 1 (rules) contains only what applies to *all* work — philosophy, quality gates, universal patterns. Tier 2 (references) contains everything else — extended examples, deep-dives, technique catalogs. The key innovation is **"When to Go Deeper"** — rules files don't just point to references, they tell the agent *when* to read them. "When tuning cooperative balance, read `.claude/references/cooperative-balance.md`." This makes the system task-aware: the agent loads deep context only when it's relevant. And everything stays inside `.claude/` — non-destructive by design.

## Why conversational, not procedural

Early versions used a phased approach: fill out this form, answer these questions, review this output. It felt like a wizard. Users didn't know the answers to half the questions (especially in unfamiliar domains), and the rigid structure prevented the natural back-and-forth that surfaces the best ideas.

The current design is a conversation. You say what you want to build. The skill does the research, proposes a team, and presents it. You react — "drop the production lead, add a worldbuilder," "I don't need a separate testing persona," "what about solo mode?" The skill adjusts. When it feels right, you lock it in.

This works better because the skill does the homework. You don't need to know who the best deck-builder designers are — the skill finds Vaccarino, Leacock, and Stegmaier and explains why each matters. Your job is taste and direction, not domain expertise.

## What we'd still like to figure out

**Persona interaction.** The assembled team currently lives as static rules. We think there's value in being able to consult individual personas in a conversational way — "What would The Systems Architect think about adding a fifth resource type?" — without bloating the always-on context. The architecture supports this (deep persona profiles in references, loaded on demand), but we haven't nailed the UX yet.

**Cross-project learning.** Right now each project's rules are independent. A pattern discovered in one Rails project could benefit another, but there's no mechanism for that. The Snap prevents bloat, but it doesn't help projects learn from siblings.

**Automated health checks.** `/fury` can audit a project when you run it, but it'd be better if The Snap could flag "your rules are getting stale, consider running `/fury`" based on actual usage patterns rather than a generic periodic reminder.

---

## Further reading

- [Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" The research that validated (and quantified) the lean-context approach.
- [Croftspan](https://croftspan.com) — The agency where this methodology was developed and battle-tested.
