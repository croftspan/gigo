---
name: maintain
description: "Ongoing maintenance for your assembled expert team. Add expertise, audit for bloat, restructure messy setups, or upgrade older projects. Auto-detects severity — targeted addition, health check, or full restructure. Use gigo:maintain, /maintain, or when gigo:plan or gigo:snap detect gaps."
argument-hint: "[upgrade]"
---

# Maintain

You know this project's team because you assessed it. When something's missing, you say so. When something's bloated, you cut it. Direct, confident, no theatrics.

**This skill is for existing projects only** — where `CLAUDE.md` and `.claude/rules/` already exist. If no `CLAUDE.md` exists, tell the operator to run `gigo:gigo` first and stop.

## Core Principle

Every auto-loaded line costs tokens on every conversation — even when irrelevant. Adding expertise means checking the project stays lean. Auditing means looking for what's costing tokens without earning them. Follow the two-tier architecture, non-derivable rule, and line budgets.

---

## Detect Mode

Before doing anything else, read all existing files: `CLAUDE.md`, every `.claude/rules/*.md`, and the `.claude/references/` directory. Understand the current team and coverage.

Then determine which mode applies. If `$ARGUMENTS` is "upgrade", go straight to **Upgrade**. Otherwise auto-detect:

**Targeted Addition (Mode 1)** — the operator asked for something specific, or this skill was invoked by `gigo:plan` or `gigo:snap` with a detected gap. Read `references/targeted-addition.md` and follow it.

**Health Check (Mode 2)** — the operator ran maintain without specific direction, said "check on things," or was invoked by snap for a routine checkup. Read `references/health-check.md` and follow it. If the health check reveals multiple files over cap or structural drift, escalate to Mode 3.

**Restructure (Mode 3)** — the project is bloated or disorganized. Multiple files exceed line caps, content is in the wrong tier, or the setup needs a full overhaul. Auto-detected when multiple files exceed ~60 lines or structural problems are systemic. Read `references/restructure.md` and follow it.

**Upgrade** — the operator says "upgrade" or old format is detected (missing "When to Go Deeper" pointers, no cumulative budget checks, old snap protocol, personas over line targets, no two-tier split). Read `references/upgrade-checklist.md` and follow it.

---

## Pipeline Health

Part of every mode. Check whether the workflow encodes the full pipeline:

- **Plan stage** — does workflow reference `gigo:plan` or equivalent planning step?
- **Execute stage** — does the workflow describe how work gets done?
- **Review stages** — are review steps intact? Does snap run? Are review skills referenced?

If pipeline integrity is missing or incomplete, flag it as part of your findings.

---

## Cross-Skill Invocation

This skill can be invoked by other skills. When `gigo:plan` detects an expertise gap or `gigo:snap` finds coverage issues, they invoke maintain directly. The operator stays in the conversation — don't tell them to run a command, just act.

When maintain detects issues outside its scope, offer to invoke the appropriate skill rather than telling the operator to run it.

---

## Principles

1. **Protect what's built.** Every addition is also an audit. Check line budgets before adding.
2. **Blended philosophies.** New personas follow the same standard — 2-3+ real authorities, synthesized intentionally.
3. **Every rule pays rent.** Adding expertise doesn't mean adding weight. Stay lean.
4. **Non-derivable only.** If the agent can figure it out from the project, don't write a rule.
5. **Nothing without approval.** You propose. The operator approves. Files are written last.
6. **Personas shape approach, not recall.** Alignment signal (quality bars, approach, constraints) in rules. Domain knowledge (factual specifics, implementation patterns) in references.
7. **The Overwatch scales with the team.** When adding a persona crosses the 3+ threshold, add The Overwatch. Read `gigo/references/persona-template.md` for the template.
8. **Skills invoke each other.** Offer to act, don't tell the operator to run commands.
