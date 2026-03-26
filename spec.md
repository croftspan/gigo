# Avengers Assemble — Skill Specification

## Overview

A Claude Code skill ecosystem that researches domain experts, blends their philosophies into focused personas, and scaffolds lean AI-native project setups. Five skills, five distinct jobs.

**Location:** Installed as a Claude Code plugin or in `~/.claude/skills/`

**Scope:** Global (not project-scoped). Works in any directory, any domain.

---

## The Five Skills

| Skill | Persona | Job | Trigger |
|---|---|---|---|
| `/avengers-assemble` | Nick Fury | First assembly — research domain, build team, scaffold project | New project, no CLAUDE.md, "assemble" |
| `/fury` | Nick Fury | Ongoing maintenance — add expertise, audit, health check | Existing project, "check on things," need new expertise |
| `/smash` | Nick Fury + Hulk | Restructure — tear down bloated setups, rebuild lean | Bloated rules, "smash," messy .claude/ |
| `/cap` | Steve Rogers | Planning — turn vague intent into clear action plans | Vague ideas, "cap," "plan this out" |
| `/snap` | The Snap | Audit rules and capture learnings — project protection protocol | Session end, "snap," saving progress |

**Routing logic:**
- No CLAUDE.md → `/avengers-assemble`
- CLAUDE.md exists, lean and well-structured → `/fury`
- CLAUDE.md exists, bloated or disorganized → `/smash`
- Operator has vague intent, needs clarity before execution → `/cap`
- Wrapping up, saving progress, or want an audit → `/snap`

---

## Skill: `/avengers-assemble` (First Assembly)

### Trigger Conditions

**Invoke when:** User says "assemble," wants to start a new project, set up Claude Code for a project, or kick off work in an unfamiliar field. No CLAUDE.md exists yet.

**Do not invoke when:** Project already has CLAUDE.md (use `/fury` or `/smash` instead), user is implementing a feature, user is debugging.

### The Kickoff Conversation

**Phase 1: Understand the Mission** — Ask lightweight follow-ups one at a time. All questions are skippable. If the description is rich enough, skip to research.

**Phase 2: Research & Assemble** — Choose research depth (quick vs deep). Use the universal discovery framework (7 questions). Find 2-3+ authorities per expertise area. Blend philosophies intentionally.

**Phase 3: Conversational Refinement** — Operator reacts, skill adjusts. Loop until "lock it in."

**Phase 4: Write the Files** — Write everything to disk following the output structure. Remind operator about `/fury` for future maintenance.

### Research Depth

| Mode | Method | Best for |
|---|---|---|
| **Quick** (default) | Training knowledge | Domain has stable standards, operator has some familiarity |
| **Deep research** | WebSearch + WebFetch | Domain changed in last 12 months, operator unfamiliar, production-grade |

### Universal Discovery Framework

Seven questions, every domain, every time:

1. What is being built, and who is it for?
2. Who are the authorities? (2-3+ per area, specific philosophies)
3. What does the gold standard look like?
4. What are the core tools and processes?
5. What are the quality gates?
6. What are the common mistakes?
7. What does "done" look like?

---

## Skill: `/fury` (Ongoing Maintenance)

### Trigger Conditions

**Invoke when:** Operator needs new expertise added, wants a health check, wants to upgrade an older setup, says "fury" or "check on things." Project already has CLAUDE.md and `.claude/rules/`.

**Do not invoke when:** No CLAUDE.md exists (use `/avengers-assemble`). Setup is bloated or disorganized (use `/smash` first).

### Three Modes

**Targeted Addition** — Operator identifies a specific gap. Skill researches, proposes new persona(s), merges without bloating.

**Upgrade Check** — Project was built with older AA version. Skill compares against current spec (two-tier split, "When to Go Deeper" pointers, cumulative budgets, snap protocol, persona targets), creates timestamped backup, proposes upgrades without touching domain expertise.

**Health Check** — No specific direction. Skill assesses coverage, freshness, and weight. Presents triage: add, update, prune, or all clear.

### Backup Policy

Every upgrade creates a timestamped backup at `.claude/pre-upgrade-backup-{date}/`. Existing backups (from `/smash` or previous upgrades) are never overwritten or deleted. Each backup is a snapshot in time — gitignored, costs nothing.

### Health Check Axes

- **Coverage:** Has the project grown beyond the team's expertise?
- **Freshness:** Are rules still accurate and current?
- **Weight:** Is every rule earning its token cost? Can the agent figure any of them out from the code?

---

## Skill: `/smash` (Restructure)

### Trigger Conditions

**Invoke when:** Rules files are bloated, disorganized, or messy. User says "smash." Setup wasn't built by `/avengers-assemble`.

**Do not invoke when:** No CLAUDE.md exists (use `/avengers-assemble`). Setup is already lean (use `/fury`).

### Six Phases

1. **Read Everything** — CLAUDE.md, all rules, references, project structure, git history
2. **Measure** — Five checks per file: line count, derivability, relevance, overlap, staleness
3. **Triage** — Categorize: Gold, Gold but heavy, Gold but narrow, Consolidation candidate, Derivable, Stale, Missing
4. **Present the Plan** — Before/after numbers, backup offer, wait for approval
5. **Execute** — Back up, create references, write consolidated files, add The Snap, remove old files
6. **Assessment** — Check expertise layer depth, suggest `/fury` or `/avengers-assemble` if gaps remain

### Triage Categories

| Category | Action |
|---|---|
| **Gold** | Keep — non-derivable, universal, under cap |
| **Gold but heavy** | Split — core stays in rules, detail to references |
| **Gold but narrow** | Move to references with "When to Go Deeper" pointer |
| **Consolidation** | Merge related small files into one |
| **Derivable** | Let go — the codebase makes it obvious now |
| **Stale** | Let go — was true once, isn't anymore |
| **Missing** | Flag for addition |

---

## Skill: `/cap` (Planning)

### Trigger Conditions

**Invoke when:** Operator has vague intent, a big idea that needs breaking down, is thinking out loud, says "cap" or "plan this out."

**Do not invoke when:** Operator knows exactly what they want and just needs execution.

### Four Steps

1. **Listen** — Find the core intent. Check project state if it exists (CLAUDE.md, rules, git history). If no project exists, work from description alone.
2. **Ask** — 2-3 questions max, one at a time. Only questions that change the plan.
3. **Plan** — Scale to task: 3-5 bullets (small), numbered steps (medium), phases with milestones (large).
4. **Recommend** — 2-3 next steps. Cap doesn't execute or auto-route. The operator decides.

### What Cap Is Not

- Not a brainstormer (doesn't explore possibilities)
- Not a project manager (doesn't track progress)
- Not an executor (doesn't write code or create files)
- Not a router (doesn't auto-invoke other skills)

---

## Output Structure

Two tiers. The division between them is the most important architectural decision.

### Tier 1: Active Rules (auto-loaded, token-taxed)

| File | Content | Always? |
|---|---|---|
| `CLAUDE.md` | Team roster, project identity, autonomy model, quick reference | Yes |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list | Yes |
| `.claude/rules/workflow.md` | Execution loop, how to approach work | Yes |
| `.claude/rules/snap.md` | The Snap — project protection protocol | Yes |
| `.claude/rules/{extension}.md` | Domain-specific rules | As needed |

**Budgets:**
- Per-file cap: ~60 lines. Fewer is better.
- Total cap: ~300 lines across all `.claude/rules/` files.
- CLAUDE.md: under 200 lines.
- Persona target: 8-10 lines each.

### Tier 2: Reference Material (on-demand, zero token tax)

Deep knowledge that rules files point to but don't contain. Extended examples, authority deep-dives, pattern libraries, decision rationale, narrow rules.

Rules files include "When to Go Deeper" pointers: task-aware links that tell the agent WHEN to read specific reference files, not just that they exist.

### The Non-Derivable Rule

Before writing any rule: "Can the agent figure this out by reading the project files?"

- Philosophy, quality bar, blended authorities → NOT derivable. Write it.
- Anti-patterns, forbidden approaches → NOT derivable. Write it.
- Pinned versions, tooling constraints → Partially derivable. Write it (easy to get wrong).
- Directory structure, file listings → Fully derivable. Never write it.
- Patterns obvious from code → Derivable. Don't state it.

### Scope Rule

Skills only write to `.claude/` (rules, references, backup) and `CLAUDE.md` at the project root. They never create, modify, or delete files in the project's source tree.

---

## Persona Structure

Each persona blends 2-3+ real authorities with specific contributions named. Not "you are Person X" but "works in the tradition of X's [approach], with Y's [strength] and Z's [discipline]."

See `references/persona-template.md` for the full template, including optional fields (Voice & Style, Personality), naming conventions, team sizing, persona retirement, and conflict resolution.

---

## The Snap (Project Protection)

Every project gets `.claude/rules/snap.md`. See `references/snap-template.md` for the full template.

**When it runs:** When the operator asks to save progress, wrap up, or end a session.

**Two jobs, in order:**
1. **Protect the project** — audit line counts, derivability, overlap, staleness, cost, total budget, coverage
2. **Capture learnings** — route new knowledge to the correct file

**The audit is the primary job.** It runs every time, even when there's nothing new to save. It's the enforcement mechanism that keeps projects lean over time.

---

## Key Design Principles

1. **Conversational, not procedural.** The operator talks, the skill works.
2. **The skill does the homework.** Finds authorities, the operator has taste and direction.
3. **Blended philosophies.** Every persona is a synthesis of real practitioners, not a generic role.
4. **Every rule pays rent.** Auto-loaded rules cost tokens on every task. Only write rules worth that cost.
5. **Non-derivable only.** If the agent can figure it out, don't write it.
6. **Task-aware references.** "When to Go Deeper" pointers, not generic links.
7. **The Snap.** The project gets sharper over time, not bigger. Whatever it takes.
8. **Nothing without approval.** Skills propose. The operator approves. Files are written last.
9. **Simple over clever.** The right system, not the most sophisticated system.

---

## Research Foundation

The skill's lean-context philosophy is validated by Gloaguen et al., "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" (arXiv:2602.11988, 2026). Key findings:

- LLM-generated context files reduce task success rates by ~3% while increasing cost by 20%+
- Developer-written files help only ~4%, and only when containing non-inferable information
- Repository overviews do NOT help agents find relevant files faster
- Recommendation: "Include only minimal requirements"

This leads to three core decisions in the skill:
- **~60 line cap** — nails essentials without diluting attention
- **Non-derivable rule** — don't write what the agent would discover
- **The Snap** — active pruning every session prevents bloat
