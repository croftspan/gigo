# Avengers, Assemble

A Claude Code skill that assembles expert teams for any project — software, fiction, games, research, anything — before you write a single line.

You describe what you're building. It researches the domain, finds the best practitioners, blends their philosophies into focused personas, and scaffolds a lean Claude Code project. Run it again later and it audits your setup for gaps and bloat.

## Why This Exists

Every Claude Code project starts with a blank `CLAUDE.md`. You write some rules, add some context, hope it's enough. A week in, the AI doesn't know the best practices for your domain. A month in, your rules files have grown with things that don't matter and are missing things that do.

Research on LLM context management shows that bloated instruction files *reduce* task success rates while *increasing* cost by 20%+. More rules doesn't mean better results — it means more noise, diluted attention, and higher bills.

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

## Origin

Born from the dev kit system at [Croftspan](https://croftspan.com), where every project starts by building the expert brain before writing a single line of code. The approach proved that domain-specific expert scaffolding makes every session better. Avengers Assemble takes that methodology and makes it work for anything.

## License

MIT
