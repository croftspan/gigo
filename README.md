# Avengers, Assemble

**Tell Claude what you're building. Get a team of domain experts who make every session smarter.**

Avengers Assemble is a set of Claude Code skills that researches the best practitioners in any field, blends their philosophies into focused AI personas, and writes lean project files that give Claude real expertise — not generic instructions.

> *"There was an idea... to bring together a group of remarkable people, so when we needed them, they could fight the battles we never could." — Nick Fury*

---

## See it in action

Fury reads the room — your experience, your style, how clear your vision is — and builds a team that meets you where you are.

**You know exactly what you're building:**

```
/avengers-assemble

You: "Building a CLI tool for database migrations. Go, targets
     Postgres and MySQL. Rollbacks, dry runs, schema diffing."

Fury: "Three on this one:

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
/avengers-assemble

You: "kids books. like mystery ones? idk"

Fury: "I can work with that. Here's who I'd bring in:

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

## The four skills

| Skill | What it does |
|---|---|
| `/avengers-assemble` | Builds your expert team from scratch. Researches authorities, blends philosophies, writes lean project files. |
| `/fury` | Ongoing maintenance. Adds expertise when gaps appear, audits for bloat, upgrades older setups. |
| `/smash` | Restructures bloated projects. Reads everything, measures against line caps, cuts what doesn't earn its keep. |
| `/cap` | Turns vague ideas into clear, prioritized action plans before anyone starts building. |

---

## Install

```bash
git clone https://github.com/Eaven/avengers-assemble.git
cp -r avengers-assemble/skills/avengers-assemble ~/.claude/skills/avengers-assemble
cp -r avengers-assemble/skills/fury ~/.claude/skills/fury
cp -r avengers-assemble/skills/smash ~/.claude/skills/smash
cp -r avengers-assemble/skills/cap ~/.claude/skills/cap
```

Then open any project and run `/avengers-assemble`.

---

## How it works

**Blended expert philosophies** — Not "you are a senior developer." Instead: *"you work in the tradition of DHH's convention-over-configuration, with Kent Beck's testing discipline and Sandi Metz's object design sensibility."* Each authority brings something specific. The blend has opinions.

**Two-tier architecture** — Rules (auto-loaded, lean) vs. references (on-demand, deep). Your rules files stay under ~60 lines. Deep-dives, pattern libraries, and technique catalogs live in references and load only when relevant. Every conversation pays only for what it uses.

**The non-derivable rule** — The skill only writes what Claude can't figure out by reading your project. Philosophy, quality bars, anti-patterns — yes. Directory structure, code patterns — never. [Research confirms](https://arxiv.org/abs/2602.11988) that bloated context reduces task success rates while increasing cost by 20%+.

**The Snap** — Named after Tony's snap, not Thanos's. A protocol that runs at session end: audits every rule, lets go of what's served its purpose, merges overlaps, enforces line caps. The project gets sharper over time, not bigger.

---

## Further reading

- [Design philosophy & origin story](docs/design-philosophy.md) — How this started at Croftspan, what failed, and what the research confirmed.
- [Future roadmap](docs/future-roadmap.md) — The Initiative: a shared community knowledge base for validated expert blends.
- [Gloaguen et al., 2026](https://arxiv.org/abs/2602.11988) — The research behind the lean-context approach.

---

Built at [Croftspan](https://croftspan.com). MIT License.
