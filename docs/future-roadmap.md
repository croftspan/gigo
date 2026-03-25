# Future Roadmap

## The Initiative — Shared Community Knowledge Base

**Status:** Proposal
**Date:** 2026-03-24

### The Problem

Every `/avengers-assemble` run starts from zero. The skill researches authorities, blends philosophies, builds personas — and throws all of that work away when it's done. The next person building a Rails app does the same research, discovers the same authorities, makes similar blends. Thousands of hours of redundant research across the community.

Meanwhile, the most valuable thing the skill produces — validated blends refined by real users over real projects — has no way to persist or spread.

### The Proposal

A shared, community-driven registry that every avengers-assemble skill can pull from and contribute back to. Not a database of generic templates — a living knowledge base of battle-tested expertise refined by real usage.

### What Lives in the Registry

**Authority Profiles**
- Who they are, their specific philosophies, what they contribute
- Which domains they're relevant to
- Community-sourced — anyone can propose an authority, usage validates them

**Validated Blends**
- Tested combinations of authorities into personas
- User ratings, usage counts, project types where they've been applied
- Variants — "the standard Rails blend" vs "Rails + API-heavy variant"

**Domain Templates**
- Starter kits for common project types: "Rails app," "Roblox game," "children's novel," "SaaS product"
- Community-refined, not generated fresh — the template for a Rails app reflects what dozens of users kept after `/fury` health checks

**Extension Packs**
- Shared rules files, snap templates, reference collections
- Domain-specific anti-pattern libraries
- "Here's the testing rules file that survived 6 months of production Rails work"

**Anti-Pattern Libraries**
- Community-sourced "don't do this" lists per domain
- The kind of institutional knowledge that's expensive to learn and easy to share

### How It Works

**Discovery (built into `/avengers-assemble` Step 3: Research)**

Before researching from scratch, the skill checks the Initiative:

```
Fury: "Found 3 community blends for cooperative board game design.
       The highest-rated one uses Vaccarino, Leacock, and Stegmaier
       — 23 projects, 4.7/5. Want to start from this, customize it,
       or build fresh?"
```

Options:
- **Use as-is** — pull the validated blend, write the files, done in seconds
- **Start from, customize** — use as a foundation, swap/add/remove personas
- **Build fresh** — ignore the Initiative, research from scratch (current behavior)

**Contribution (built into `/avengers-assemble` Step 6: Write Files)**

After writing files, opt-in contribution:

```
Fury: "This blend turned out well. Want to share it with the
       community? Your project details stay private — only the
       authority blends, rules patterns, and domain tags get shared."
```

What gets shared:
- Authority names and philosophy blends (the non-derivable knowledge)
- Domain tags and project type
- Rules file structures (not content that's project-specific)
- Extension file patterns

What never gets shared:
- Project names, code, business logic
- Client information, vault contents
- Anything project-specific

**Refinement (built into `/fury` and `/smash`)**

When `/fury` cuts a persona or `/smash` removes a rule, that's signal:

```
Fury: "I just removed The Production Lead from your team.
       Want to flag this in the Initiative? Helps others know
       this persona works better for later-stage projects."
```

Usage data flows back: which blends survive health checks, which get cut, which rules last and which get pruned. Quality surfaces naturally.

### The Flywheel

1. Early adopters contribute blends from `/avengers-assemble` runs
2. New users discover validated blends instead of starting from zero
3. `/fury` health checks and `/smash` restructures generate refinement signal
4. Popular blends rise, stale ones fade, domain coverage grows organically
5. Each new user makes the Initiative more valuable for the next one

### The Social Angle

- "I just ran `/avengers-assemble` for a Roblox game and it already knew about Quenty's NevermoreEngine patterns because someone contributed that blend last month"
- Leaderboard of top contributors by domain
- "Used in X projects" badges on blends
- Domain experts become recognized authorities in the Initiative itself

### Implementation Phases

**Phase 1: Structured Logging (no infrastructure)**
- Every `/avengers-assemble` run appends to a local structured log (JSON)
- Authority names, blends, domain tags, what the user kept/cut
- No sharing yet — just building the data model from real usage
- Ship this first. Learn what patterns emerge from 20-30 runs.

**Phase 2: GitHub-Based Registry (minimal infrastructure)**
- Public GitHub repo with structured YAML/JSON files
- Community contributions via PR
- Skills read from the repo during research step
- Ratings via GitHub reactions or a simple metadata file
- Low maintenance, high visibility, natural social sharing

**Phase 3: API + Search (when scale demands it)**
- Simple REST API for registry queries
- Semantic search: "cooperative card game with horror themes" finds relevant blends
- Usage tracking, automated quality scoring
- Still backed by flat files or simple database — no over-engineering

**Phase 4: Graph Layer (when traversals matter)**
- When "find the intersection of board game economy authorities and horror narrative authorities that have been validated together" becomes a real query people run
- Neo4j or similar for authority-domain-blend relationship traversals
- Only build this when Phase 3 data proves the connections matter

### What This Is Not

- **Not a marketplace.** No paid content, no premium tiers. Community knowledge is free.
- **Not a template store.** Templates are static. The Initiative is alive — blends get refined by usage.
- **Not a social network.** The social features serve discovery, not engagement metrics.

### Open Questions

- ~~**Naming.** Settled: **The Initiative.**~~
- **Moderation.** How to prevent low-quality contributions from diluting the Initiative. Usage-based scoring helps, but is it enough?
- **Privacy boundaries.** The line between "shareable blend" and "project-specific knowledge" needs to be crisp and enforced by the skill, not left to user judgment.
- **Versioning.** Authorities evolve, best practices change. How do blends stay current? Does a blend from 2026 still apply in 2028?
- **Offline-first.** The skills must work without the Initiative. It's an accelerant, not a dependency.
