# GIGO (Garbage In, Garbage Out)

**Only give them the information they need for the job.**

Personas for planning. Specs with conventions for workers. Quality bar checklists for reviewers. Every layer gets exactly what it needs — nothing more.

GIGO is a set of Claude Code skills that researches domain experts, blends their philosophies into focused personas, and orchestrates a plan→execute→review pipeline where the right context reaches the right agent at the right time. 9 phases of eval data prove it works.

---

## See it in action

GIGO reads the room — your experience, your style, how clear your vision is — and builds a team that meets you where you are.

**You know exactly what you're building:**

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

You: "kids books. like mystery ones? idk"

GIGO: "I can work with that. Here's who I'd bring in:

        The Story Architect
        I'm pulling from Wendelin Van Draanen — she's the master
        of clues kids can actually follow. Mixing in Lemony
        Snicket's philosophy that kids are way smarter than adults
        give them credit for. This person owns your plot and makes
        sure the mystery plays fair.

        The Voice Coach
        Kate DiCamillo writes sentences that sound simple but hit
        you right in the chest. Mixing that with Mo Willems —
        nobody alive is better at making kids laugh with fewer
        words. This person owns how your book sounds and feels.

       That's two to start. Want me to dig into either of them,
       or does this feel right?"
```

Same skill, different calibration. Detailed brief gets peers who challenge. "idk" gets guides who lead.

Works for anything: software, fiction, game design, research, music, business.

---

## The seven skills

| Skill | What it does |
|---|---|
| `gigo` | Builds your expert team from scratch. Researches authorities, blends philosophies, writes lean project files. |
| `gigo:maintain` | Ongoing maintenance. Adds expertise when gaps appear, audits for bloat, upgrades older setups. |
| `gigo:plan` | Turns vague ideas into clear specs and prioritized plans. Brainstorms with you first, then structures. |
| `gigo:execute` | Runs the plan with agent teams or subagents — bare workers get the spec, not the personas. |
| `gigo:review` | Two-stage review: spec compliance (did you build the right thing?) then engineering quality (did you build it well?). |
| `gigo:snap` | Session-end audit. Enforces line caps, removes stale rules, captures learnings, protects the project. |
| `gigo:eval` | Tests whether your assembled context actually improves output. Pipeline eval with comparative judging. |

---

## Install

```bash
claude install @eaven/gigo
```

Or manually:

```bash
git clone https://github.com/Eaven/gigo.git
cp -r gigo/skills/ ~/.claude/skills/
```

Then open any project and say `gigo`.

---

## Why this works

### The core principle

We tested where context helps and where it hurts across 9 experimental phases and 50+ runs. The finding:

**Context helps when it shapes the questions. Context hurts when it shapes the answers.**

A planner with personas asks "What's the expected scale? *This determines whether we need to worry about table lock duration on migrations.*" A planner without personas asks "What's the expected scale?" Same question, different depth. The persona catches the architectural gap.

But a worker with personas writes self-conscious code — checking boxes, explaining craft decisions, over-commenting. A bare worker following a good spec produces senior-to-staff-level code. Every time.

### The architecture that won

| Phase | Context | Why |
|---|---|---|
| **Planning** | Personas ON | Personas shape questions, catch conventions, surface quality bars |
| **Spec** | Conventions embedded | Personas noticed them; the spec delivers them to the worker |
| **Execution** | Personas OFF | Bare workers + good spec = senior/staff code. Every time. |
| **Review** | Quality bar checklists | Extracted from personas, not the personas themselves |

### The data

**Pipeline coherence test** — three chains built the same feature:

| Chain | What the worker got | Score |
|---|---|---|
| Full context | Architecture + personas + rules | 29/30 |
| Architecture only | Same architecture, no personas | 20/30 |
| Bare | Nothing | 14/30 |

Architecture alone gets you from 14 to 20 — types match, interfaces match, error patterns match. Conventions embedded in the spec get you from 20 to 29 — error message formats, output discipline, durability patterns. The personas' job is to *notice* these conventions during planning. The spec's job is to *deliver* them to the worker.

**Convention compliance** — bare workers following specs with explicit conventions sections:

- Tier 1 (agent teams): 20/20 conventions matched, first pass
- Tier 2 (subagents): 10/10 conventions matched, first pass
- Zero review fixes needed in either tier

The execution mechanism doesn't matter. The spec is what matters.

### What the project files look like

**Two-tier architecture** — Rules (auto-loaded, lean) vs. references (on-demand, deep). Rules files stay under ~60 lines. Deep-dives, pattern libraries, and technique catalogs load only when relevant. Every conversation pays only for what it uses.

**The non-derivable rule** — Only write what Claude can't figure out by reading your project. Philosophy, quality bars, anti-patterns — yes. Directory structure, code patterns — never. [Research confirms](https://arxiv.org/abs/2602.11988) that bloated context reduces task success rates while increasing cost by 20%+.

**The Snap** — Runs at session end: audits every rule, lets go of what's served its purpose, merges overlaps, enforces line caps. The project gets sharper over time, not bigger.

---

## Further reading

- [The eval narrative](evals/EVAL-NARRATIVE.md) — 9 phases of testing: how we proved where context helps and where it hurts.
- [Phase 9 integration test](evals/integration-test/) — End-to-end pipeline test with convention compliance data.
- [Design philosophy & origin story](docs/design-philosophy.md) — How this started, what failed, and what the research confirmed.
- [Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — The research behind the lean-context approach.

---

Built at [Croftspan](https://croftspan.com). MIT License.
