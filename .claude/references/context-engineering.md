# Context Engineering — Deep Reference

Read this when evaluating whether a rule earns its token cost, when designing the two-tier architecture for a new project, or when optimizing an existing setup.

## The Token Tax — By the Numbers

From Gloaguen et al. (2026), across 4 agents and 2 benchmarks:

| Metric | Without context file | With LLM-generated | With human-written |
|---|---|---|---|
| Resolution rate change | baseline | -0.5% to -2% | +4% average |
| Inference cost change | baseline | +20-23% | +19% |
| Additional steps | baseline | +2.45 to +3.92 | +1.5 to +2.8 |
| Reasoning token increase | baseline | +14-22% | +10-15% |

Key insight: agents with context files explore *more broadly* (more files read, more tests run, more searches) but not *more effectively*. The broader exploration consumes tokens without improving outcomes.

## Two-Tier Architecture — How It Works

### Tier 1: Always-On (`.claude/rules/`, `CLAUDE.md`)

**Loaded:** Every session start, every request.
**Token cost:** Applied to every single conversation.
**What belongs here:** Only content that applies to ALL work in the project:
- Blended philosophies and quality bars (non-derivable)
- Anti-patterns and forbidden lists (prevent mistakes)
- Core workflow (how to approach any task)
- The Snap (enforcement mechanism)

**Hard cap:** ~60 lines per file. CLAUDE.md under 200 lines (per Anthropic docs: "target under 200 lines per CLAUDE.md file").

### Tier 2: On-Demand (`.claude/references/`, skills with supporting files)

**Loaded:** Only when referenced or when agent determines relevance.
**Token cost:** Zero until used. Then only the relevant file loads.
**What belongs here:** Everything else:
- Extended examples, technique catalogs
- Authority deep-dives and philosophy breakdowns
- Full pattern libraries
- Decision rationale ("why we chose X over Y")
- Situational rules (apply only to specific task types)

### The Bridge: "When to Go Deeper"

Every Tier 1 file includes a "When to Go Deeper" section with task-aware pointers:
```
When [specific task], read .claude/references/[specific file].md
```

This replaces generic "see also" links. The agent reads the right reference at the right time.

## Context Rot — What It Is

From Anthropic's documentation: as token count grows in the context window, accuracy and recall degrade. This is separate from the "Lost in the Middle" positional effect — it's a general degradation from volume.

**Practical impact on this skill:**
- A 500-line CLAUDE.md causes Claude to ignore half its own instructions
- Rules that worked at 30 lines may stop working at 90 lines (not because they're bad, but because attention is diluted)
- The Snap's audit prevents this by pruning before it happens

## Positional Effects — Where to Put Critical Content

From Liu et al. ("Lost in the Middle," 2023):
- LLMs perform best when critical information is at the **beginning or end** of context
- Performance degrades for information in the **middle**
- From Anthropic: "Queries at the end can improve response quality by up to 30%"

**Implication for rules files:** Put the most important rules first. Put "When to Go Deeper" pointers last (they're the last thing read before the agent takes action).

## Path-Scoped Rules — When They Apply

Claude Code supports rules with `paths` frontmatter that only load when matching files are accessed:

```yaml
---
paths:
  - "skills/avengers-assemble/**"
---
```

**When to use path-scoping in this project:**
- Rules that only apply to specific skills (e.g., assembly-specific vs fury-specific patterns)
- Rules that only apply to specific file types (e.g., template files vs SKILL.md files)
- Rules that would waste tokens loading for unrelated work

**When NOT to path-scope:** Rules that genuinely apply to all work. The standards, workflow, snap, and skill-engineering files are deliberately unconditional.

## Measuring Token Cost

To evaluate whether a rule change is worth it:
1. Count the lines added to Tier 1
2. Estimate ~1-2 tokens per word in rules (rough heuristic)
3. Multiply by number of conversations per day
4. Ask: "Does this rule prevent enough mistakes to justify that cost?"

Boris's test: "Would removing this cause Claude to make mistakes?" If not, it's not earning its keep.

## The Derivability Spectrum

Not everything is clearly derivable or non-derivable. Use this spectrum:

| Content type | Derivable? | Action |
|---|---|---|
| Philosophy, quality bars, blended authorities | NOT derivable | Write in rules |
| Anti-patterns, forbidden approaches | NOT derivable | Write in rules |
| Pinned versions, specific tooling | Partially derivable | Write in rules (easy to get wrong) |
| Directory structure, file organization | Fully derivable | Never write |
| Patterns obvious from reading code | Derivable | Don't state |
| Framework defaults and standard conventions | Known to Claude | Don't state |
