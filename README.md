<div align="center">

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skills-blueviolet.svg)](https://github.com/Eaven/gigo)

</div>

# 義剛 GIGO

**Only give them what they need for the job.**

A Claude Code skill that researches domain experts, blends their philosophies into focused personas, and runs a plan→execute→review pipeline backed by [published research](https://arxiv.org/abs/2602.11988) and [9 phases of original experiments](site/research/).

---

## See It In Action

**You know what you're building:**

```
gigo

You: "Building a CLI tool for database migrations. Go, targets
     Postgres and MySQL. Rollbacks, dry runs, schema diffing."

GIGO: "Three on this one:

        The Migration Architect
        Andrew Kane's database ops pragmatism + Sandi Metz's
        'small objects that talk to each other.' Owns migration
        safety, rollback logic, and the 'will this lock the
        table?' question.

        The CLI Designer
        Steve Francia's cobra/viper patterns + Rob Pike's Go
        proverbs. Owns the interface — flags, output formatting,
        error messages that actually help.

        The Test Strategist
        Mitchell Hashimoto's infrastructure testing philosophy —
        if you can't test it against a real database, the test
        is lying. Owns integration tests and CI reliability.

       Lock it in, or adjustments?"
```

**You're still figuring it out:**

```
gigo

You: "I'm thinking about writing kids' mystery books.
      Not sure where to start."

GIGO: "I can work with that. Here's who I'd bring in:

        The Story Architect
        Wendelin Van Draanen — she's the master of clues kids
        can actually follow. Mixed with Lemony Snicket's
        philosophy that kids are smarter than adults give them
        credit for. Owns your plot and makes sure the mystery
        plays fair.

        The Voice Coach
        Kate DiCamillo writes sentences that sound simple but
        hit you right in the chest. Mixed with Mo Willems —
        nobody alive is better at making kids laugh with fewer
        words. Owns how your book sounds and feels.

       That's two to start. Want me to dig into either of them,
       or does this feel right?"
```

Same skill, different calibration. Works for anything — software, fiction, game design, research, music, business.

---

## Quick Start

```bash
claude install @eaven/gigo
```

Open any project in Claude Code. Type `gigo`.

---

## The Results

97% convention compliance on first pass. Zero review fixes needed. Principal engineers rated the output senior to staff level — every run.

Built on two published papers — [Gloaguen et al. (2026)](https://arxiv.org/abs/2602.11988) on context bloat and [Hu et al. (2026)](https://arxiv.org/abs/2603.18507) on the persona tradeoff — then validated with 9 phases of original experiments across two domains.

The core finding: **personas help planning. Bare workers + good specs produce the best code.** The architecture that won:

| Phase | Context | Result |
|---|---|---|
| Planning | Assembled (personas ON) | Catches architectural gaps bare misses |
| Execution | Bare (personas OFF) | Senior/staff-level code every run |
| Review | Assembled (quality bars) | Two focused reviewers > one combined |

[Read the full research →](site/research/)

---

## The Seven Skills

| Skill | What it does |
|---|---|
| `gigo` | Builds your expert team from scratch |
| `gigo:maintain` | Adds expertise, audits for bloat, upgrades setups |
| `gigo:plan` | Turns ideas into specs and implementation plans |
| `gigo:execute` | Runs plans with agent teams — workers get the spec, not the personas |
| `gigo:review` | Two-stage review: spec compliance + engineering quality |
| `gigo:snap` | Session-end audit — projects get sharper, not bigger |
| `gigo:eval` | Proves the assembled context actually improves output |

---

## The Name

義剛 (Gigo) — "righteousness" and "strong." In computer science, GIGO means "Garbage In, Garbage Out." Both meanings apply.

---

Built at [Croftspan](https://croftspan.com). MIT License.

[Research](site/research/) · [Get Started](site/docs/getting-started.html) · [Skills](site/docs/skills.html) · [Architecture](site/docs/architecture.html)
