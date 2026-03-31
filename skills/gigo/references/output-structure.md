# Output Structure — Writing the Files

Two tiers. The division between them is the most important architectural decision in this skill.

**Everything lives inside `.claude/`.** Rules in `.claude/rules/`, references in `.claude/references/`. The only file outside `.claude/` is `CLAUDE.md` at the project root (required by Claude Code). This keeps the skill's footprint non-destructive — it never creates or modifies files in the project's source tree.

## The Non-Derivable Rule

Before writing any rule, ask: **"Can the agent figure this out by reading the project files?"**

- Philosophy, quality bar, blended authorities → **NOT derivable.** Write it.
- Anti-patterns, forbidden approaches → **NOT derivable.** Write it.
- Pinned versions and tooling constraints → **Partially derivable** but easy to get wrong. Write it.
- Directory structure, file listings, "how the project is organized" → **Fully derivable.** Never write it.
- Patterns obvious from reading existing code → **Derivable.** Don't state it.

Codebase overviews are useless. Agents navigate codebases on their own. Only describe things the agent cannot discover by reading the code.

## Tier 1: Active Rules (auto-loaded, token-taxed)

These go in `.claude/rules/` and `CLAUDE.md`. They load every conversation. Every line costs tokens and attention on every task — even irrelevant ones.

**Budgets:**
- Per-file cap: ~60 lines. Fewer is better.
- Total cap: ~300 lines across all `.claude/rules/` files.
- CLAUDE.md: under 200 lines.
- Persona target: 8-10 lines each.

**Always create these:**

| File | Content |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity, autonomy model, quick reference. At 3+ personas, include The Overwatch (see `persona-template.md` → The Overwatch). |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list. "When to Go Deeper" pointers must be task-specific: name the observable task, name the reference file, name what to look for. |
| `.claude/rules/workflow.md` | Encodes the pipeline (plan→execute→review) pointing to gigo:blueprint, gigo:execute, gigo:snap. Includes Persona Calibration section (see `persona-template.md`), Overwatch section (see `persona-template.md` → The Overwatch), and Team Routing section (see below). |
| `.claude/rules/snap.md` | The Snap — protects the project (see `snap-template.md`) |

**Create domain extensions as needed** — but only when the domain has rules that genuinely apply to every task. Common examples:

- Software: `stack.md` (pinned versions, forbidden deps), `testing.md` (philosophy only, not patterns)
- Fiction: `voice-guide.md` (prose rules that always apply), `story-structure.md` (only if structural rules are universal)
- Games: `engine-patterns.md` (architectural invariants only)

Every extension file follows the format in `extension-file-guide.md`. The key innovation is the **"When to Go Deeper"** section — task-aware pointers that tell the agent exactly when a reference file is relevant, making the system task-aware instead of always-on.

## Tier 2: Reference Material (on-demand, zero token tax)

These go in `.claude/references/`. They are read when needed, not every conversation. They cost nothing when unused.

**This is where most content belongs.** Push aggressively toward references:

- Extended examples, technique catalogs, code patterns
- Authority deep-dives and philosophy breakdowns
- Full pattern libraries
- Documentation URL collections
- Decision rationale ("why we chose X over Y")
- Narrow rules that only apply to specific task types

**Language configuration:** `.claude/references/language.md` stores the operator's interface language and output language(s). Two fields: `interface:` (single IETF tag) and `output:` (bracketed array of IETF tags). Written during gigo:gigo assembly. Read on demand by skills at startup — never auto-loaded.

**Language guard:** Any skill that produces operator-facing conversation must read `.claude/references/language.md` at startup and use the interface language for all conversation. Output deliverables follow the output language(s). If the file doesn't exist, default to English for both. This ensures new skills added via `gigo:maintain` inherit the language requirement.

**Persona style:** `.claude/references/persona-style.md` stores the operator's preference for persona presentation. One field: `style:` (`characters` or `lenses`). Written during gigo:gigo assembly. Characters get named personas with personality and voice. Lenses get functional descriptors that work silently. If the file doesn't exist, default to `lenses`.

Rules files tell the agent WHEN to read specific reference files. This creates task-aware context loading.

## Pre-Write Dedup Pass

Before writing any files, scan all proposed content for cross-file redundancy. The same rule must not appear in more than two auto-loaded locations (once in CLAUDE.md persona context, once in the relevant rules file). This is the most common failure mode — a core principle gets stated in CLAUDE.md, restated in standards.md, echoed in an extension file, and mentioned again in workflow.md. The agent reads it 4 times per conversation. That's bloat, not emphasis.

**How to check:** For each key rule or principle you're about to write, search your proposed content for the same idea across files. If it appears in more than 2 auto-loaded files, pick the best home and remove it from the others.

**The pattern:** CLAUDE.md states the principle as part of a persona's quality standard (brief). The relevant rules file states it as an actionable rule with consequences (full). That's two. Not three. Not six.

## Persona Structure — Two Tiers

Read `persona-template.md` for format, examples, and calibration guidance.

**Lean tier (CLAUDE.md):** Scannable, bullet-driven. Uses `Modeled after` (one authority per line with `+`), `Owns`, `Quality bar`, `Won't do`. Optional: `Personality`, `Decides by`, `Depth` pointer. Target: 8-10 lines, hard ceiling 12.

**Rich tier (`.claude/references/personas/{name}.md`):** Character sheets with Bio, Personality, Communication Style, Decision Framework, Pushes Back On, Champions. Depth calibrated to the operator — full treatment for casual/creative operators who need personas that lead, minimal treatment (just decision frameworks and edge cases) for direct/technical operators who need personas that execute.

**Alignment vs knowledge placement:** The lean tier should contain alignment signal only — how to approach work (quality bars, constraints, anti-patterns). Domain knowledge (factual specifics, technical patterns, implementation details) belongs in the rich tier, loaded on demand. System-prompt placement (rules) amplifies both persona benefits and persona damage; reference placement (mid-task loading) gives the model domain context without competing with its factual recall. This isn't just about token cost — it's about where in the context the persona lands.

Never inflate. Never cap.

## Review Criteria File

Generated as the FINAL output step (Step 6.5), after all personas and standards are
written. Extracts persona `Quality bar:` lines, standards `Quality Gates` bullets,
and extension `The Standard` sections. Classifies each into three sections: Spec
Compliance Criteria, Craft Review Criteria, Challenger Criteria.

This file is a REFERENCE (tier 2) — zero token cost. The review pipeline reads it
on demand when dispatching reviewers. If personas or standards change, the file must
be regenerated. `gigo:maintain` and `gigo:snap` both check for staleness.

## Team Routing

Every assembled project gets a **Team Routing** section in `.claude/rules/workflow.md`. This controls whether every task is automatically routed through the assembled personas or handled as default Claude.

**Default state: `inactive`.** Personas are in CLAUDE.md and naturally influence planning and review. Explicit routing adds deliberation overhead without proven quality gain. The operator can turn it on when they want it.

The generated workflow.md must include this section:

```markdown
## Team Routing

State: inactive

When team routing is active, every task is routed through the assembled personas before work begins. Identify which persona(s) are most relevant to the task and apply their lens — quality bars, approach, constraints. If multiple personas apply, blend their perspectives. If no persona is clearly relevant, note that and proceed with default reasoning.

The operator can toggle this:
- "team on" → set state to `active`. Route every task through personas.
- "team off" → set state to `inactive`. Personas still in context but no explicit routing.
```

**Why inactive by default:** Personas in CLAUDE.md already influence the agent's behavior — they're in context. Explicit routing forces a deliberation step on every response ("which persona applies?") that adds latency without proven quality improvement. Users who want it can toggle on.

## The Snap

Every project gets `.claude/rules/snap.md`. Read `snap-template.md` for the template.

The Snap is what keeps a great project great on day sixty. Named after Tony's snap — not Thanos's. It sacrifices what has to go so everything that matters survives. Two jobs, in order: (1) protect the project through audit, (2) route new learnings to the right file. Job 1 is more important — the audit runs every time, even when there's nothing new to save.
