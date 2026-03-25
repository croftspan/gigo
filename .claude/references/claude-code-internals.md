# Claude Code Internals — Deep Reference

Read this when designing skill architecture, configuring frontmatter, building hooks, or making decisions about how the skill ecosystem interacts with Claude Code's systems. Based on official Anthropic documentation as of March 2026 and Claude 4.6 models.

## CLAUDE.md Loading Behavior

- Loaded as a **user message** after the system prompt, not part of the system prompt itself
- Walking: scans up from working directory to root, loading CLAUDE.md at each level
- Subdirectory files are **lazy-loaded** — only when Claude accesses files in those directories
- `@path/to/import` syntax expands imports at load time (max 5 hops deep)
- Files survive compaction: after `/compact`, CLAUDE.md is re-read from disk and re-injected fresh
- Priority: managed policy > project > user (more specific overrides broader)
- Target: under 200 lines. Over 500 significantly degrades adherence.

## .claude/rules/ Loading Behavior

- Discovered recursively in `.claude/rules/`
- Files without `paths` frontmatter: loaded at session start (always in context)
- Files with `paths` frontmatter: loaded only when Claude accesses matching files
- User-level rules (`~/.claude/rules/`): loaded before project rules, project rules override
- Symlinks supported (cross-project shared rules)

## Skills Architecture (as of Claude Code latest)

### File Structure
```
.claude/skills/<name>/
├── SKILL.md           # Required: frontmatter + instructions
├── references/        # Optional: detailed docs loaded on demand
├── templates/         # Optional: templates Claude fills in
├── examples/          # Optional: example outputs
└── scripts/           # Optional: executable scripts
```

### Frontmatter Fields
| Field | Purpose |
|---|---|
| `name` | Becomes `/name` command. Lowercase, hyphens, max 64 chars |
| `description` | Claude matches tasks against this. THE trigger mechanism |
| `disable-model-invocation` | `true` = only user can invoke. For side-effect workflows |
| `user-invocable` | `false` = hidden from menu. Claude-only background knowledge |
| `allowed-tools` | Tools permitted without asking when skill is active |
| `model` | Model override when skill is active |
| `effort` | Effort level override (low/medium/high/max) |
| `context` | `fork` = run in isolated subagent context |
| `agent` | Which subagent type for `context: fork` (Explore, Plan, general-purpose, or custom) |
| `argument-hint` | Autocomplete hint: `[issue-number]` |
| `hooks` | Hooks scoped to this skill's lifecycle |

### Loading Cost
1. Session start: skill **descriptions** load (~50-200 chars each, ~1-2K total for 10 skills)
2. On invocation: **full content** loads (500-5K tokens depending on size)
3. With `disable-model-invocation: true`: zero cost until manual invocation

### String Substitutions
- `$ARGUMENTS` — all arguments passed to skill
- `$ARGUMENTS[N]` or `$N` — specific argument by index
- `${CLAUDE_SESSION_ID}` — current session ID
- `${CLAUDE_SKILL_DIR}` — directory containing the SKILL.md
- `` !`command` `` — shell preprocessing (runs before Claude sees content)

### Skill Priority (highest wins)
1. Enterprise/managed
2. Personal (`~/.claude/skills/`)
3. Project (`.claude/skills/`)
4. Plugin (namespaced: `plugin:skill-name`)

## Subagent Architecture

### Built-in Types
| Agent | Model | Tools | Use for |
|---|---|---|---|
| Explore | Haiku (fast) | Read-only | Codebase search, analysis |
| Plan | Inherits | Read-only | Research before planning |
| General-purpose | Inherits | All | Complex multi-step tasks |

### Custom Subagents (`.claude/agents/`)
Key frontmatter: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills` (preloaded), `memory` (persistent), `background`, `isolation` (worktree).

### Context Isolation
Subagent work happens in a separate context window. Only the summary returns to main conversation. This prevents verbose exploration from bloating the primary session.

## Hooks System

### Event Lifecycle (ordered)
SessionStart → InstructionsLoaded → UserPromptSubmit → PreToolUse → (tool executes) → PostToolUse/PostToolUseFailure → Stop → SessionEnd

Special events: Notification, SubagentStart/Stop, TaskCompleted, ConfigChange, WorktreeCreate/Remove, PreCompact/PostCompact

### Hook Types
1. **Command** — synchronous shell execution. Exit 0 = allow, exit 2 = block
2. **HTTP** — POST event data to URL
3. **Prompt** — single LLM call (Haiku default), yes/no judgment
4. **Agent** — subagent with tools, complex verification

### Configuration Location
Managed policy > project `.claude/settings.json` > local `.claude/settings.local.json` > user `~/.claude/settings.json` > plugin > skill frontmatter

## Plugin Architecture

```
plugin/
├── plugin.json          # Manifest (name, version, skills[], agents[], hooks, mcp, lsp)
├── skills/              # Skill directories
├── agents/              # Subagent definitions
├── hooks/hooks.json     # Hook configurations
├── mcp/.mcp.json        # MCP server configs (scoped to plugin)
└── lsp/lsp.json         # Language server configs
```

Plugin skills are namespaced (`plugin-name:skill-name`) to prevent conflicts.

## Auto Memory System

- Location: `~/.claude/projects/<project>/memory/`
- `MEMORY.md` first 200 lines loaded every session
- Topic files (e.g., `debugging.md`) loaded on demand
- Shared across all worktrees within same git repo
- Machine-local, not synced across devices

## Key Model Capabilities (Claude 4.6)

- **Extended thinking:** Interleaved thinking between tool calls. Previous thinking blocks auto-stripped to save tokens.
- **Effort levels:** low, medium, high, max (Opus 4.6 only for max)
- **Context window:** 1M tokens for Opus 4.6
- **Adaptive thinking:** Model dynamically allocates reasoning tokens based on perceived difficulty
