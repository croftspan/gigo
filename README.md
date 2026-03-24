# Avengers, Assemble

A Claude Code skill that builds you the best team in any field — before you write a single line of code, a single chapter, or a single design.

You tell it what you're building. It researches the domain, finds the authorities, blends their philosophies into focused expert personas, and scaffolds your entire Claude Code project with lean rules, quality standards, and a workflow tailored to the work. Run it again a month later and it audits your setup, finds the gaps, and levels you up.

## The Problem

Every Claude Code project starts the same way: a blank `CLAUDE.md` and a vague sense of what you want. You write some rules, add some context, and hope it's enough. A week in, you realize the AI doesn't know the best practices for your domain. A month in, your rules files are bloated with stuff that doesn't matter and missing stuff that does.

**Avengers Assemble fixes this.** It gives every project the brain of the best practitioners in the field from day one — and keeps it sharp over time.

## How It Works

```
You: "I want to build a children's mystery novel series for ages 10-14"

Skill: researches the domain, finds authorities like Wendelin Van Draanen's
       plot structure, Blue Balliett's puzzle-weaving, Scholastic's editorial
       philosophy...

Skill: "Here's the team I'd assemble:
        - The Story Architect — blends Van Draanen's clue pacing with
          Balliett's intellectual puzzle design
        - The Prose Stylist — works in the tradition of Kate DiCamillo's
          clarity with Rebecca Stead's emotional precision
        - The Age Lens — calibrated to the reading level and emotional
          maturity research from Fountas & Pinnell

        Here's the quality bar, here are the patterns, here's what
        to avoid. What do you think?"

You: "I want it darker than that, more like Lemony Snicket"

Skill: adjusts the team, re-presents...

You: "Lock it in"

Skill: writes CLAUDE.md, .claude/rules/, references/ — done.
```

No forms. No questionnaires. Just a conversation that ends with a fully scaffolded project.

## What You Get

### Lean rules that auto-load every conversation

| File | Purpose |
|---|---|
| `CLAUDE.md` | Team roster, project identity, philosophy, quick reference |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, what excellence looks like |
| `.claude/rules/workflow.md` | How to approach work in this domain |
| `.claude/rules/save-progress.md` | Smart session-saving that keeps the kit sharp |
| `.claude/rules/{extensions}.md` | Domain-specific rules — as many as the project needs |

### Deep references available on demand

Extended examples, authority deep-dives, pattern libraries, and documentation links live in `references/` — loaded when needed, not every conversation.

The rules stay sharp. The depth is always there.

## Features

### Blended Expert Philosophies

Every persona draws from multiple real authorities. Not "you are a senior developer" — that's generic. Instead: "you work in the tradition of DHH's convention-over-configuration, with Kent Beck's testing discipline and Sandi Metz's object design sensibility." The opinions come from practitioners with track records, blended intentionally.

### Works for Any Domain

Software, fiction, game design, research, music production, board games, business strategy — anything. The skill uses a universal discovery framework to find what excellence looks like in any field:

- Who are the authorities?
- What does the gold standard look like?
- What are the core tools and processes?
- What separates professional from amateur?

No hardcoded categories. No routing logic. Just a framework that works everywhere.

### Smart Save-Progress

The kit doesn't fossilize after day one. The included save-progress knows your project structure and actively maintains it:

- **Consolidates** — merges new learnings with existing rules instead of appending endlessly
- **Prunes** — removes rules that the project has outgrown or that the codebase now makes obvious
- **Enforces line budgets** — moves detail to references when rules files get heavy
- **Audits on every save** — asks "is each rule still earning its place?"
- **Suggests re-assembly** — when it spots gaps the team doesn't cover

### Re-Runnable

First run scaffolds the project. Every run after that makes it better.

| You say | Skill does |
|---|---|
| "I need audio design expertise" | Researches the domain, proposes new persona and rules, merges in |
| "Check on things" | Reads project state, audits the kit, suggests additions or pruning |
| "Run it again" | Full health check — finds what's stale, what's missing, what's grown |

### Quick or Deep Research

Presented as a clear choice at the start:

- **Quick** (default) — uses Claude's knowledge to identify authorities and best practices. Fast, usually sufficient.
- **Deep research** — web search for current state of the art, active communities, recent style guides, living practitioners. Better for fast-moving domains or unfamiliar territory.

## Installation

Clone the repo and copy the skill to your global Claude Code skills directory:

```bash
git clone https://github.com/Eaven/avengers-assemble.git
cp -r avengers-assemble/skills/avengers-assemble ~/.claude/skills/avengers-assemble
```

## Usage

### First time — new project

```
cd ~/projects/my-new-thing
/avengers-assemble
```

The skill detects no existing `CLAUDE.md` and runs the full assembly flow.

### Adding expertise

```
/avengers-assemble I need someone who knows multiplayer networking
```

The skill reads your existing kit and adds to it.

### Health check

```
/avengers-assemble
```

Run in an existing project without specific direction and the skill audits your setup.

## Examples

A Roblox game might produce:

```
CLAUDE.md                              # Team + identity
.claude/rules/standards.md             # Quality gates
.claude/rules/workflow.md              # Dev loop
.claude/rules/save-progress.md         # Kit maintenance
.claude/rules/stack.md                 # Luau, Rojo, Wally, versions
.claude/rules/code-standards.md        # ModuleScript patterns, style
.claude/rules/engine-patterns.md       # Physics, replication, datastores
.claude/rules/economy-design.md        # Monetization, virtual currency
references/luau-style-guide.md         # Full style reference
references/datastore-patterns.md       # Extended examples
```

A children's novel series might produce:

```
CLAUDE.md                              # Team + identity
.claude/rules/standards.md             # Quality gates
.claude/rules/workflow.md              # Editorial process
.claude/rules/save-progress.md         # Kit maintenance
.claude/rules/voice-guide.md           # Prose style, dialogue, POV
.claude/rules/story-structure.md       # Mystery plotting, clue pacing
.claude/rules/genre-conventions.md     # Age targeting, content boundaries
references/voice-examples.md           # Writing samples across contexts
references/mystery-plotting.md         # Extended structural patterns
```

A SaaS application might produce:

```
CLAUDE.md                              # Team + identity
.claude/rules/standards.md             # Quality gates
.claude/rules/workflow.md              # Dev loop
.claude/rules/save-progress.md         # Kit maintenance
.claude/rules/stack.md                 # Framework, DB, versions
.claude/rules/code-standards.md        # Architecture patterns
.claude/rules/testing.md               # Test philosophy + pyramid
.claude/rules/api-design.md            # Endpoint conventions
references/architecture-decisions.md   # Extended rationale
references/deployment-guide.md         # Infrastructure detail
```

Every project gets exactly what it needs. No more, no less.

## Design Principles

1. **Conversational, not procedural.** No steps to memorize. You talk, it works.
2. **The skill does the homework.** You don't need to know who the best practitioners are. It finds them.
3. **Blended philosophies.** Synthesis of real authorities, not generic role-play.
4. **Lean rules, deep references.** What you need every conversation is sharp and scannable. Everything else is a read away.
5. **Smart maintenance.** The kit gets better over time, not bloated.
6. **No artificial limits.** One persona or ten. Two rule files or twelve. Depth matches the project.
7. **Nothing without approval.** It proposes. You approve. Files are written last.

## Origin

Born from the dev kit system at [Croftspan](https://croftspan.com), where every project starts by building the expert brain before writing a single line of code. The Ruby on Rails kit — modeled after DHH's philosophy, 37signals' practices, and Rails 8's patterns — proved that domain-specific expert scaffolding makes every session better. Avengers Assemble takes that approach and makes it work for anything.

## License

MIT
