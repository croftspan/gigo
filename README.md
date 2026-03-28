<div align="center">

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-skills-blueviolet.svg)](https://github.com/Eaven/gigo)

</div>

# 義剛 GIGO

**Research the experts. Build the team. Ship better work.**

You describe what you're building. GIGO researches the best practitioners in that field — real people with real philosophies — and builds you an expert team. Your AI plans smarter, writes better code, catches more bugs.

We tested it across 9 experiments. It works.

---

## Quick Start

```bash
claude install @eaven/gigo
```

Open any project in Claude Code. Type `gigo`.

---

## How It Works

1. **Plan with your expert team** — GIGO's personas ask the hard questions. They catch the architectural gaps, the missing edge cases, the things you'd only think of at 2am.

2. **Write a spec that carries the expertise** — The team's knowledge gets baked into the spec as concrete requirements. Not vague rules — specific decisions.

3. **Let the AI do its thing** — Workers get the spec, not the rules. No hand-holding. We tested this: bare workers with good specs were rated senior to staff level by principal engineers. Every run.

4. **Review with real standards** — Two focused reviewers catch different bugs than one reviewer trying to do everything. The team knows what to look for.

We proved this works with [9 phases of experiments](site/research/) across two completely different domains (a Rails API and a children's mystery novel), built on research from [Gloaguen et al.](https://arxiv.org/abs/2602.11988) and [Hu et al.](https://arxiv.org/abs/2603.18507)

The results: gets it right the first time, 97% of the time. Zero fixes needed.

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

Built at [Croftspan](https://croftspan.com). MIT License.

[Research](site/research/) · [Get Started](site/docs/getting-started.html) · [Skills](site/docs/skills.html) · [Architecture](site/docs/architecture.html)
