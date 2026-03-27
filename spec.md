# GIGO — Skill Specification

## Overview

A Claude Code skill ecosystem that researches domain experts, blends their philosophies into focused personas, scaffolds lean AI-native project setups, and orchestrates execution through a proven plan→execute→review pipeline. Seven skills, seven distinct jobs.

**Location:** Installed as a Claude Code plugin or in `~/.claude/skills/`

**Scope:** Global (not project-scoped). Works in any directory, any domain.

---

## The Seven Skills

| Skill | Job | Trigger |
|---|---|---|
| `gigo:gigo` | First assembly — research domain, build team, scaffold project | New project, no CLAUDE.md, "assemble" |
| `gigo:plan` | Planning — turn vague intent into clear, executable plans | Vague ideas, "plan this out," need structure before execution |
| `gigo:execute` | Execution — dispatch bare workers from a plan | Have a plan, ready to build, "execute" |
| `gigo:review` | Two-stage review — spec compliance then engineering quality | Work completed, need review, "review" |
| `gigo:snap` | Audit rules and capture learnings — project protection protocol | Session end, "snap," saving progress |
| `gigo:maintain` | Ongoing maintenance — add expertise, audit, health check, restructure | Existing project, need new expertise, bloated setup, "maintain" |
| `gigo:eval` | Context effectiveness testing — measure how context changes affect output | Need to test prompt changes, "eval," measure quality |

**Routing logic:**
- No CLAUDE.md → `gigo:gigo`
- CLAUDE.md exists, lean and well-structured → `gigo:maintain`
- CLAUDE.md exists, bloated or disorganized → `gigo:maintain` (auto-detects severity)
- Operator has vague intent, needs clarity before execution → `gigo:plan`
- Have a plan, ready to implement → `gigo:execute`
- Work completed, need quality check → `gigo:review`
- Wrapping up, saving progress, or want an audit → `gigo:snap`
- Need to measure context effectiveness → `gigo:eval`

---

## Pipeline Architecture

GIGO generates projects that follow a proven three-stage pipeline:

**1. Assembled Planning** — Full team context loaded. Personas shape WHAT gets asked, not just formatting. The plan captures domain-specific concerns that bare workers wouldn't think to address.

**2. Bare Execution** — Workers run without persona context. They receive only the task description from the plan. Research shows format and framing don't matter at this stage — workers perform at senior/staff level with just clear instructions.

**3. Two-Stage Review** — First stage checks spec compliance (did we build the right thing?). Second stage checks engineering quality (did we build it well?). Different reviewers find different problems.

This architecture emerged from 8 phases of empirical testing. The key insight: context helps planning and hurts execution. Complexity belongs in the plan, not the worker instructions.

---

## Skill: `gigo:gigo` (First Assembly)

### Trigger Conditions

**Invoke when:** User says "assemble," wants to start a new project, set up Claude Code for a project, or kick off work in an unfamiliar field. No CLAUDE.md exists yet.

**Do not invoke when:** Project already has CLAUDE.md (use `gigo:maintain` instead), user is implementing a feature, user is debugging.

### The Kickoff Conversation

**Phase 1: Understand the Mission** — Ask lightweight follow-ups one at a time. All questions are skippable. If the description is rich enough, skip to research.

**Phase 2: Research & Assemble** — Choose research depth (quick vs deep). Use the universal discovery framework (7 questions). Find 2-3+ authorities per expertise area. Blend philosophies intentionally.

**Phase 3: Conversational Refinement** — Operator reacts, skill adjusts. Loop until "lock it in."

**Phase 4: Write the Files** — Write everything to disk following the output structure. Remind operator about `gigo:maintain` for future maintenance.

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

## Skill: `gigo:plan` (Planning)

### Trigger Conditions

**Invoke when:** Operator has vague intent, a big idea that needs breaking down, is thinking out loud, says "plan this out." Also invoked as the first stage of the pipeline — assembled planning with full team context.

**Do not invoke when:** Operator knows exactly what they want and just needs execution.

### Four Steps

1. **Listen** — Find the core intent. Check project state if it exists (CLAUDE.md, rules, git history). If no project exists, work from description alone.
2. **Ask** — 2-3 questions max, one at a time. Only questions that change the plan.
3. **Plan** — Scale to task: 3-5 bullets (small), numbered steps (medium), phases with milestones (large).
4. **Recommend** — 2-3 next steps. Suggest `gigo:execute` for implementation if the plan is ready.

### What Plan Is Not

- Not a brainstormer (doesn't explore possibilities)
- Not a project manager (doesn't track progress)
- Not an executor (doesn't write code or create files)
- Not a router (doesn't auto-invoke other skills)

---

## Skill: `gigo:execute` (Execution)

### Trigger Conditions

**Invoke when:** A plan exists and the operator is ready to implement. User says "execute," "build it," or "implement the plan."

**Do not invoke when:** No plan exists (use `gigo:plan` first). Operator is still exploring ideas.

### How It Works

1. **Read the plan** — Parse tasks, dependencies, and parallelization opportunities.
2. **Dispatch bare workers** — Each worker gets only its task description. No persona context, no war stories, no framing. Workers perform at senior/staff level with clear instructions alone.
3. **Parallelize where possible** — Independent tasks run concurrently via agent teams.
4. **Report results** — Surface completions, failures, and anything that needs operator attention.

### The Bare Worker Principle

Workers run without assembled context. Research (Phase 7) proved that format, framing, and persona context don't improve execution quality. Clear task descriptions are sufficient. Complexity belongs in the plan.

---

## Skill: `gigo:review` (Two-Stage Review)

### Trigger Conditions

**Invoke when:** Work has been completed and needs quality verification. User says "review," or execution has just finished.

**Do not invoke when:** Work hasn't started yet (use `gigo:plan`). Mid-implementation (let workers finish first).

### Two Stages

**Stage 1: Spec Compliance** — Did we build the right thing? Checks output against the plan's requirements and acceptance criteria. Plan-aware review catches different problems than engineering review.

**Stage 2: Engineering Quality** — Did we build it well? Checks code quality, patterns, edge cases, and maintainability. Standard engineering review independent of the specific plan.

Different reviewers find different problems. Combining stages into one reduces coverage.

---

## Skill: `gigo:maintain` (Ongoing Maintenance)

### Trigger Conditions

**Invoke when:** Operator needs new expertise added, wants a health check, wants to upgrade an older setup, says "maintain" or "check on things." Also handles bloated or disorganized setups — severity is auto-detected. Project already has CLAUDE.md and `.claude/rules/`.

**Do not invoke when:** No CLAUDE.md exists (use `gigo:gigo`).

### Modes (auto-detected)

**Targeted Addition** — Operator identifies a specific gap. Skill researches, proposes new persona(s), merges without bloating.

**Upgrade Check** — Project was built with older version. Skill compares against current spec (two-tier split, "When to Go Deeper" pointers, cumulative budgets, snap protocol, persona targets, pipeline architecture), creates timestamped backup, proposes upgrades without touching domain expertise.

**Health Check** — No specific direction. Skill assesses coverage, freshness, and weight. Presents triage: add, update, prune, or all clear.

**Restructure** — Setup is bloated or disorganized. Auto-detected when rules exceed budgets or structure is messy. Tears down and rebuilds lean, following the six-phase process: read everything, measure, triage, present plan, execute, assess.

### Backup Policy

Every upgrade creates a timestamped backup at `.claude/pre-upgrade-backup-{date}/`. Existing backups are never overwritten or deleted. Each backup is a snapshot in time — gitignored, costs nothing.

### Health Check Axes

- **Coverage:** Has the project grown beyond the team's expertise?
- **Freshness:** Are rules still accurate and current?
- **Weight:** Is every rule earning its token cost? Can the agent figure any of them out from the code?
- **Pipeline:** Does the workflow reflect the plan→execute→review architecture?

---

## Skill: `gigo:eval` (Context Effectiveness Testing)

### Trigger Conditions

**Invoke when:** Operator wants to measure how context changes affect AI output quality. User says "eval," "test this change," or "measure effectiveness."

**Do not invoke when:** Operator wants to execute a plan (use `gigo:execute`). Operator wants a code review (use `gigo:review`).

### What It Does

Provides infrastructure for A/B testing context changes — different prompts, persona configurations, rule sets — against real tasks. Measures whether a change actually improves output or just feels like it should.

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

## The Team

This project's own team — the personas that build GIGO itself.

### Sage — The Context Architect
Owns token economics, two-tier architecture, derivability testing, line budgets, context rot prevention.

### Forge — The Skill Engineer
Owns SKILL.md architecture, frontmatter, supporting file organization, subagent design, hook lifecycle, progressive disclosure.

### Mirror — The Quality Auditor
Owns eval design, before/after benchmarking, The Snap audit cycle, derivability checks, skill triggering accuracy.

### Scribe — The Prompt Architect
Owns prompt engineering, persona blending, instruction specificity, anti-slop discipline, voice consistency.

### The Voice — README & Developer Relations Architect
Owns README architecture, progressive disclosure, the 5-second test, scan-path design, emotional resonance before technical depth.

### Conductor — The Execution Architect

**Modeled after:** The Phase 7 "two kinds of leadership" finding — plan well, let workers work, review honestly
+ Kent Beck's "make the change easy, then make the easy change" — pipeline design makes good output the path of least resistance
+ John Ousterhout's "A Philosophy of Software Design" — complexity belongs in the module (planning), not the interface (worker instructions).

- **Owns:** Execution pipeline design (plan→bare execute→two-stage review), tool detection, subagent context rules, the assembled/bare boundary
- **Quality bar:** The generated workflow produces the proven architecture without requiring the operator to understand why it works.
- **Won't do:** Load workers with context, combine review stages into one, skip tool detection

### The Overwatch — Adversarial Output Verification
Owns eval integrity, hallucination detection, pre-mortem analysis, independent verification of all output claims.

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
10. **Plan well, execute bare, review honestly.** The pipeline architecture that emerged from empirical testing.

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

The pipeline architecture is validated by 8 phases of internal experimentation:
- Assembled context improves planning quality (personas change WHAT gets asked)
- Bare workers match senior/staff performance with clear instructions alone
- Two-stage review catches more issues than single-pass review
- Format and framing don't matter for execution — only clarity of the task
