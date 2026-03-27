# GIGO (Garbage In, Garbage Out)

**Tell Claude what you're building. Get a team of domain experts who make every session smarter -- and an execution pipeline that puts context where it helps and strips it where it hurts.**

GIGO is a set of Claude Code skills that researches the best practitioners in any field, blends their philosophies into focused AI personas, writes lean project files that give Claude real expertise, and orchestrates the proven plan→execute→review pipeline.

---

## See it in action

GIGO reads the room — your experience, your style, how clear your vision is — and builds a team that meets you where you are.

**You know exactly what you're building:**

```
gigo:gigo

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
gigo:gigo

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
| `gigo:gigo` | Builds your expert team from scratch. Researches authorities, blends philosophies, writes lean project files. |
| `gigo:maintain` | Ongoing maintenance. Adds expertise when gaps appear, audits for bloat, upgrades older setups. |
| `gigo:plan` | Turns vague ideas into clear, prioritized action plans before anyone starts building. |
| `gigo:execute` | Runs the plan with bare workers — no personas, no rules, just a good spec and their training. |
| `gigo:review` | Two-stage review: plan-aware check (did you build the right thing?) then code-quality check (did you build it well?). |
| `gigo:snap` | Session-end audit. Enforces line caps, removes derivable rules, captures learnings, protects the project. |
| `gigo:eval` | Tests how context affects AI output quality. Before/after benchmarking for rules, personas, and prompts. |

---

## Install

```bash
git clone https://github.com/Eaven/gigo.git
cp -r gigo/skills/gigo ~/.claude/skills/gigo
```

Then open any project and run `gigo:gigo`.

---

## How it works

**Blended expert philosophies** — Not "you are a senior developer." Instead: *"you work in the tradition of DHH's convention-over-configuration, with Kent Beck's testing discipline and Sandi Metz's object design sensibility."* Each authority brings something specific. The blend has opinions.

**Two-tier architecture** — Rules (auto-loaded, lean) vs. references (on-demand, deep). Your rules files stay under ~60 lines. Deep-dives, pattern libraries, and technique catalogs live in references and load only when relevant. Every conversation pays only for what it uses.

**The non-derivable rule** — The skill only writes what Claude can't figure out by reading your project. Philosophy, quality bars, anti-patterns — yes. Directory structure, code patterns — never. [Research confirms](https://arxiv.org/abs/2602.11988) that bloated context reduces task success rates while increasing cost by 20%+.

**The Snap** — A protocol that runs at session end: audits every rule, lets go of what's served its purpose, merges overlaps, enforces line caps. The project gets sharper over time, not bigger.

---

## Why the team doesn't write the code

There are two kinds of bosses. One says *do your job or I'll fire you* — piles on rules, guardrails, compliance checks. The other says *what can I do to help you do your job better?* The answer is almost always the same: a clear plan and honest feedback. Not someone standing over my shoulder.

We tested both approaches across 7 phases and 50+ experimental runs. ([Full data trail](evals/EVAL-NARRATIVE.md#two-kinds-of-leadership))

The "rules everywhere" approach — loading workers with quality gates, war stories, anti-patterns — produces mid-level output. A blind judge called it "mid-level reaching for senior" because the worker spends energy checking boxes instead of thinking. We tested four different formats for delivering rules. None of them helped. One of them (compressed rules) consistently produced the worst code, with real bugs a principal engineer found.

A bare worker — no personas, no rules, no context at all — was rated senior to staff level. Every time.

But that same worker, left to plan on its own, misses things. A bare brainstormer asks "What's the expected scale?" An assembled brainstormer asks "What's the expected scale? *This determines whether we need to worry about table lock duration on migrations.*" Same question, different depth. The bare planner's spec ships with a concurrency bug, unbounded queries, and no way to withdraw damaged inventory. The assembled planner's spec catches all of these. ([Planning evidence](evals/planning-test/judge-report.md))

**The architecture that won:**

| Phase | Context | Why |
|---|---|---|
| **Planning** | Team ON | Personas shape questions, catch gaps, expertise becomes spec requirements |
| **Execution** | Team OFF | Workers produce best output with their training alone + a good spec |
| **Review** | Team ON | Team catches what workers miss, sends back for fixes |

This is what `gigo:gigo` generates: a team that asks better questions, writes better specs, and catches more problems in review. Not a team that hovers over the worker's shoulder telling them how to do their job.

---

## Further reading

- [The eval narrative](evals/EVAL-NARRATIVE.md) — 7 phases of testing: how we proved where context helps and where it hurts.
- [Design philosophy & origin story](docs/design-philosophy.md) — How this started at Croftspan, what failed, and what the research confirmed.
- [Future roadmap](docs/future-roadmap.md) — The Initiative: a shared community knowledge base for validated expert blends.
- [Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — The research behind the lean-context approach.

---

Built at [Croftspan](https://croftspan.com). MIT License.
