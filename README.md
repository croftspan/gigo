<div align="center">
  <img src="site/assets/social-preview.png" alt="義剛 GIGO" width="600">

  [![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Claude Code Skills](https://img.shields.io/badge/Claude_Code-skills-blueviolet.svg)](https://github.com/Eaven/gigo)
</div>

# 義剛 GIGO

**Only give them what they need for the job.**

## The Problem

Claude Code is powerful out of the box. But most projects get context engineering wrong — they either give Claude nothing (and get generic output) or give it everything (and get worse output that costs more). We spent 9 experimental phases proving exactly where context helps and where it hurts. Then we built a system that applies the findings automatically.

## See It In Action

**Clear technical brief:**

```
gigo

You: "Building a CLI tool for database migrations. Go, targets
     Postgres and MySQL. Rollbacks, dry runs, schema diffing."

GIGO: "Three on this one:

        The Migration Architect
        Andrew Kane's database ops pragmatism + Sandi Metz's
        'small objects that talk to each other.' Owns migration
        safety, rollback logic, table lock detection.

        The CLI Designer
        Steve Francia's cobra/viper patterns + Rob Pike's Go
        proverbs. Owns the interface — flags, output formatting,
        error messages that help.

        The Test Strategist
        Mitchell Hashimoto's infrastructure testing philosophy —
        if you can't test it against a real database, the test
        is lying. Owns integration tests and CI reliability.

       Lock it in, or adjustments?"
```

**Vague creative idea:**

```
gigo

You: "kids books. like mystery ones? idk"

GIGO: "I can work with that. Here's who I'd bring in:

        The Story Architect
        Wendelin Van Draanen — the master of clues kids can
        actually follow. Mixed with Lemony Snicket's philosophy
        that kids are smarter than adults give them credit for.
        Owns plot and makes sure the mystery plays fair.

        The Voice Coach
        Kate DiCamillo writes sentences that sound simple but
        hit you right in the chest. Mixed with Mo Willems —
        nobody alive is better at making kids laugh with fewer
        words. Owns how your book sounds and feels.

       That's two to start. Want me to dig into either of them,
       or does this feel right?"
```

Same skill, different calibration. Works for anything — software, fiction, game design, research, music, business.

## Quick Start

```bash
claude install @eaven/gigo
```

Open any project. Say `gigo`.

## The Seven Skills

| Skill | What it does |
|---|---|
| `gigo` | Builds your expert team from scratch. Researches authorities, blends philosophies. |
| `gigo:maintain` | Ongoing maintenance. Adds expertise, audits for bloat, upgrades older setups. |
| `gigo:plan` | Turns ideas into specs and prioritized plans. Brainstorms first, then structures. |
| `gigo:execute` | Runs plans with agent teams or subagents. Workers get the spec, not the personas. |
| `gigo:review` | Two-stage review: spec compliance, then engineering quality. |
| `gigo:snap` | Session-end audit. Enforces caps, removes stale rules, captures learnings. |
| `gigo:eval` | Tests whether assembled context actually improves output. |

## Why This Works

### The core finding

Context helps when it shapes the questions. Context hurts when it shapes the answers.

1. **Architecture carries coherence** — 14 to 20 out of 30
2. **Personas add conventions on top** — 20 to 29
3. **Workers run bare + good spec = senior/staff code.** Every time.

### The research

Built on published research — not intuition:

- **Gloaguen et al. (2026):** bloated context reduces success, increases cost 20%+ ([arXiv](https://arxiv.org/abs/2602.11988))
- **Hu et al.:** personas help alignment but hurt knowledge retrieval
- **Kong et al. + Xu et al.:** specific blended personas outperform generic roles
- **Shinn et al.:** reflection agents make better decisions
- **Yang et al.:** interface design matters more than the prompt

Then validated with 9 phases of original experiments across two domains, 50+ eval runs, comparative judging, and principal engineer reviews.

### Convention compliance

30/30 conventions matched on first pass across two execution tiers. Zero review fixes needed. The spec is what matters.

## Two Kinds of Leadership

The intuitive approach — load workers with rules, quality gates, and compliance checks — produces mid-level output that checks boxes instead of thinking.

The counterintuitive finding: plan with the full team, then send bare workers a clear spec. They produce senior/staff-level code because the team's expertise is baked into the spec as requirements, not loaded as rules the worker has to perform against.

[Read the full research narrative →](site/research/)

## The Name

義剛 (Gigo) — "righteousness" and "strong." In computer science, GIGO means "Garbage In, Garbage Out." Both meanings apply. The project exists because garbage context produces garbage output, and it solves that problem with discipline.

---

Built at [Croftspan](https://croftspan.com). MIT License.

[Research](site/research/) · [Getting Started](site/docs/getting-started.html) · [Skills](site/docs/skills.html) · [Architecture](site/docs/architecture.html)
