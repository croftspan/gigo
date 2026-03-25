# Avengers, Assemble

**Tell Claude what you're building. Get a team of domain experts who make every session smarter.**

Avengers Assemble is a set of Claude Code skills that researches the best practitioners in any field, blends their philosophies into focused AI personas, and writes lean project files that give Claude real expertise — not generic instructions.

> *"There was an idea... to bring together a group of remarkable people, so when we needed them, they could fight the battles we never could." — Nick Fury*

---

## See it in action

```
/avengers-assemble

You: "I'm designing a cooperative deck-building board game. 2-4 players,
     60 minute target play time. Fantasy theme — more like Hades meets
     Slay the Spire on a tabletop."

Fury: "Here's the team I'd assemble:

        The Systems Architect
        Blends Donald X. Vaccarino's deck-building engine design
        (Dominion) with Eric Lang's tension mechanics and Matt
        Leacock's cooperative balance philosophy (Pandemic). Owns
        card economy, action systems, and win/loss conditions.

        The Experience Designer
        Draws from Jamey Stegmaier's player engagement principles
        (Wingspan, Scythe) with Rob Daviau's legacy/narrative
        progression and Bruno Cathala's elegant interaction design.
        Owns table feel, player agency, and session pacing.

        The World Builder
        Blends Patrick Rothfuss's lived-in world design with the
        Supergiant Games approach to mythological remixing (Hades,
        Pyre). Cultures feel discovered, not invented. Every
        mechanical faction has a narrative reason to exist.

        What do you think?"

You: "Lock it in"
```

That's it. You describe the project, Fury finds the authorities, you shape the team, and it writes everything to disk. Every session after this thinks like Vaccarino, Leacock, and Stegmaier — before you've designed a single card.

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
