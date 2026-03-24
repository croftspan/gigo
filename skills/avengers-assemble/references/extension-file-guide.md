# Extension File Guide

Domain extension files live in `.claude/rules/` and auto-load every conversation. They contain domain-specific rules that don't fit in the universal core (standards, workflow, save-progress).

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
Each pattern earns its place — if it's obvious, don't state it.}

## Anti-Patterns
{What to avoid and why. Each entry explains the consequence,
not just the rule. "Don't do X because Y happens."}

## References
{Pointers to references/ files or external resources.
"See references/xyz.md for extended examples."}
```

## Line Budget

Target ~100 lines per file. This is a soft cap, not a hard limit — but if a file is growing past it, that's a signal to move detail to `references/`.

Ask yourself: "Does someone need this on every conversation, or only when they're working in this specific area?" If the latter, it belongs in `references/`.

## Examples

### Software: stack.md

```markdown
# Stack — MyApp

## Philosophy
Follows Rails 8's omakase philosophy — trust the framework's choices.
No unnecessary dependencies, no build step, no microservices.

## The Standard
Every dependency is pinned. Every forbidden tool has a reason.
Version verification runs clean.

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
| Redis | Solid Queue/Cache/Cable | No external dependencies |
| RSpec | Minitest | Rails default |

## References
See `references/deployment-guide.md` for infrastructure setup.
```

### Fiction: voice-guide.md

```markdown
# Voice Guide — The Blackwood Files

## Philosophy
Draws from Kate DiCamillo's spare, precise prose with Lemony Snicket's
willingness to trust young readers with complexity. Every sentence earns
its place. Dialogue drives scenes.

## The Standard
Read it aloud. If you stumble, rewrite. If a word has a simpler
synonym that works, use the simpler word. Anglo-Saxon over Latinate.

## Patterns
- Short paragraphs — two to three sentences max
- Dialogue tags: "said" and "asked" only. No "exclaimed," "muttered," "quipped"
- One sensory detail per scene transition — ground the reader, then move
- Internal monologue in italics, sparingly — Ellie thinks in fragments, not essays

## Anti-Patterns
- Adverb-heavy dialogue tags ("she said quietly") — rewrite the dialogue to show it
- Explaining the joke or the clue — trust the reader
- Purple prose in action scenes — short sentences, active verbs, white space

## References
See `references/voice-examples.md` for writing samples across scene types.
```

### Game: engine-patterns.md

```markdown
# Engine Patterns — Shadow Protocol

## Philosophy
Follows the Roblox Developer Hub's recommended architecture with
Quenty's NevermoreEngine patterns for module organization and
Sleitnick's Knit framework philosophy for service structure.

## The Standard
ModuleScripts for all shared logic. No code in StarterPlayerScripts
that isn't a LocalScript bootstrapper. Server authority for all
game state. Client predicts, server validates.

## Patterns
- One ModuleScript per system (CombatService, InventoryService, etc.)
- ReplicatedStorage for shared modules, ServerScriptService for server-only
- RemoteEvents namespaced by system: "Combat:Attack", "Inventory:Equip"
- DataStore wrapped in a single DataManager module with retry + session locking

## Anti-Patterns
- Game logic in LocalScripts — exploitable, always
- Polling loops for state sync — use RemoteEvents and value objects
- Raw DataStore calls scattered across scripts — single access point only

## References
See `references/roblox-architecture.md` for full module structure.
```

## When to Create a New Extension vs. Add to an Existing One

Create a new extension when:
- The topic has its own set of authorities and philosophy
- It could grow independently of other extensions
- It serves a distinct phase or aspect of the work

Add to an existing extension when:
- The content is a subset of an existing topic
- Splitting would create two thin files that belong together

When in doubt, start with fewer files. You can always split later. The operator can also split during a health check.
