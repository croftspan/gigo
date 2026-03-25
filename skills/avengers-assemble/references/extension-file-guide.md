# Extension File Guide

Domain extension files live in `.claude/rules/` and auto-load every conversation. They contain domain-specific rules that don't fit in the universal core (standards, workflow, snap).

**Every line in these files costs tokens and attention on every task — even irrelevant ones.** Only write rules that genuinely apply to all work in this project.

## Structure

Every extension file follows this format:

```markdown
# {Topic} — {Project Name}

## Philosophy
{Blended authorities — who this draws from and why. Same depth as persona
philosophies but applied to a domain area rather than a role.}

## The Standard
{What good looks like in this area, stated concisely. Scannable.
This is the quality bar, not the tutorial.}

## Patterns
{How to do it right. Short, actionable entries.
Each pattern earns its place — if it's obvious from reading the code, don't state it.}

## Anti-Patterns
{What to avoid and why. Each entry explains the consequence,
not just the rule. "Don't do X because Y happens."}

## When to Go Deeper
{Task-aware pointers to .claude/references/ files. Tell the agent WHEN to read them:
"When writing dialogue scenes, read .claude/references/dialogue-techniques.md"
"When designing economy loops, read .claude/references/monetization-framework.md"}
```

Note the last section: **"When to Go Deeper"** replaces a generic "References" link. It tells the agent *when* a reference file is relevant, making the system task-aware. The agent reads `.claude/references/dialogue-techniques.md` when writing dialogue, not when editing plot structure.

## Line Budget

**Per-file cap: ~60 lines. Fewer is better.** If a file is growing past this, move detail to `.claude/references/` and leave a "When to Go Deeper" pointer.

**Total cap: ~300 lines across all `.claude/rules/` files.** A project with 8 extensions at 60 lines each is 480 lines of auto-loaded context — that's systemic bloat even though each file is individually "fine." Track the total.

**Reference files:** No hard cap, but keep individual reference files under ~200 lines. If a reference is growing larger, split it by subtopic.

Ask: "Does the agent need this on every conversation, or only when working in this specific area?" If the latter, it belongs in `.claude/references/`.

Ask: "Can the agent figure this out by reading the project files?" If yes, don't write it. No codebase overviews. No structural descriptions. No obvious patterns.

## Examples

### Software: stack.md

```markdown
# Stack — MyApp

## Philosophy
Follows Rails 8's omakase philosophy — trust the framework's choices.
No unnecessary dependencies, no build step, no microservices.

## The Standard
Every dependency is pinned. Every forbidden tool has a reason.

## Pinned Versions

| Dependency | Version | Lock |
|---|---|---|
| Ruby | 3.3.1 | Exact |
| Rails | 8.0.1 | Exact |
| PostgreSQL | 16+ | Minimum |

## Forbidden

| Forbidden | Use Instead | Why |
|---|---|---|
| Webpack/esbuild | importmap-rails | No build step |
| Redis | Solid Queue/Cache/Cable | No external deps |
| RSpec | Minitest | Rails default |

## When to Go Deeper
When setting up deployment or infrastructure, read `.claude/references/deployment-guide.md`.
When adding a new gem, read `.claude/references/gem-evaluation-criteria.md`.
```

### Fiction: voice-guide.md

```markdown
# Voice Guide — The Blackwood Files

## Philosophy
Draws from Kate DiCamillo's spare, precise prose with Lemony Snicket's
willingness to trust young readers with complexity. Dialogue drives scenes.

## The Standard
Read it aloud. If you stumble, rewrite. Anglo-Saxon over Latinate.

## Patterns
- Short paragraphs — two to three sentences max
- Dialogue tags: "said" and "asked" only
- One sensory detail per scene transition
- Internal monologue in italics, sparingly

## Anti-Patterns
- Adverb-heavy dialogue tags — rewrite the dialogue to show it
- Explaining the joke or the clue — trust the reader
- Purple prose in action scenes — short sentences, active verbs

## When to Go Deeper
When writing dialogue-heavy scenes, read `.claude/references/dialogue-techniques.md`.
When writing action/chase sequences, read `.claude/references/pacing-guide.md`.
When starting a new chapter, read `.claude/references/voice-examples.md` for calibration.
```

### Game: engine-patterns.md

```markdown
# Engine Patterns — Shadow Protocol

## Philosophy
Follows the Roblox Developer Hub's recommended architecture with
Quenty's NevermoreEngine patterns and Sleitnick's Knit framework philosophy.

## The Standard
ModuleScripts for all shared logic. Server authority for all
game state. Client predicts, server validates.

## Patterns
- One ModuleScript per system (CombatService, InventoryService)
- ReplicatedStorage for shared, ServerScriptService for server-only
- RemoteEvents namespaced by system: "Combat:Attack", "Inventory:Equip"
- DataStore wrapped in single DataManager with retry + session locking

## Anti-Patterns
- Game logic in LocalScripts — exploitable, always
- Polling loops for state sync — use RemoteEvents
- Raw DataStore calls scattered across scripts — single access point

## When to Go Deeper
When designing a new game system, read `.claude/references/roblox-architecture.md`.
When implementing DataStore persistence, read `.claude/references/datastore-patterns.md`.
When optimizing network traffic, read `.claude/references/replication-guide.md`.
```

## When to Create a New Extension vs. Add to an Existing One

Create a new extension when:
- The topic has its own set of authorities and philosophy
- It could grow independently of other extensions
- It serves a distinct phase or aspect of the work

Add to an existing extension when:
- The content is a subset of an existing topic
- Splitting would create two thin files that belong together

When in doubt, start with fewer files. You can always split later during a health check.
