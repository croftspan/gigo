# 義剛 GIGO

**Research the experts. Build the team. Ship better work.**

[croftspan.github.io/gigo](https://croftspan.github.io/gigo/)

Describe what you're building. GIGO researches the best practitioners in that field, real people with real philosophies, and builds you an expert team.

Better plans. Better output. Fewer problems that make it to production.

---

## Quick Start

```bash
claude install @croftspan/gigo
```

Open any project in Claude Code. Type `gigo`.

---

## How It Works

1. **Plan with your expert team.** GIGO's personas ask the hard questions. They catch the architectural gaps, the missing edge cases, the things you'd only think of at 2am.

2. **Write a spec that carries the expertise.** The team's knowledge gets baked into the spec as concrete requirements. Not vague rules. Specific decisions.

3. **Let the AI do its thing.** Workers get the spec, not the rules. No hand-holding. We tested this: bare workers with good specs were rated senior to staff level by principal engineers. Every run.

4. **Review with real standards.** Two focused reviewers catch different bugs than one reviewer trying to do everything. The team knows what to look for.

Most AI tools are vibe coded. Ship it, hope it works, iterate on feelings. We took a different approach: published research, controlled experiments, real methodology.

9 phases. Hundreds of eval runs. Blinded judging. Principal engineer reviews. Two completely different domains. Built on [Gloaguen et al.](https://arxiv.org/abs/2602.11988) and [Hu et al.](https://arxiv.org/abs/2603.18507)

70M+ Claude tokens burned proving it.

The results: **97% of requirements met on the first pass. Zero fixes needed.**

---

## Your Project Stays Lean

Most AI setups grow out of control. Every session adds rules, nothing gets removed. Within weeks your context files are hundreds of lines of overlapping, outdated guidance that makes output worse, not better.

GIGO uses a two-tier system. Rules that apply to every conversation stay lean (under 60 lines each). Deep knowledge loads only when relevant. Zero cost when unused.

At the end of every session, The Snap audits your project: removes what's stale, merges what overlaps, enforces line budgets. Your project gets sharper over time, not bigger.

---

## The Seven Skills

| Skill | What it does |
|---|---|
| `gigo` | Builds your expert team from scratch |
| `gigo:maintain` | Adds expertise, audits for bloat, upgrades setups |
| `gigo:plan` | Turns ideas into specs and implementation plans |
| `gigo:execute` | Runs plans with agent teams. Workers get the spec, not the personas |
| `gigo:review` | Two-stage review: spec compliance + engineering quality |
| `gigo:snap` | Session-end audit. Projects get sharper, not bigger |
| `gigo:eval` | Proves the assembled context actually improves output |

---

## The Name

義剛 (Gigo), pronounced *ghee-goh* (義 *gi*, righteousness + 剛 *gō*, strong).

In computer science, GIGO means "Garbage In, Garbage Out."


---

## See It In Action

**Clear technical brief:**

```
You: "Building a real-time multiplayer game server. Rust.
      WebSocket connections, matchmaking, state sync."

GIGO: "Three on this one:

        The Network Architect
        Carl Lerche's Tokio-driven async pragmatism. The runtime
        is the foundation, get it right or nothing else matters.
        + Glenn Fiedler's game networking gospel. Client-side
        prediction, server authority, snapshot interpolation.
        + Sanjay Ghemawat's systems-level efficiency thinking.
        When you're processing thousands of connections per tick,
        allocation patterns are gameplay decisions.

        The Game State Engineer
        Gabriel Gambetta's client-server game architecture.
        The canonical breakdown of interpolation, prediction,
        and reconciliation. + Jon Blow's data-oriented design
        philosophy. ECS isn't a religion, but your state layout
        determines your tick budget. + Martin Kleppmann's
        distributed systems rigor. State sync is a distributed
        systems problem wearing a game costume.

        The Matchmaker
        Josh Menke's matchmaking philosophy (Halo, Call of Duty).
        Skill rating is easy, match quality is hard. + Raph
        Koster's theory of fun as a design constraint.
        Matchmaking that doesn't produce fun games is technically
        correct and functionally useless.

       Three distinct lenses. Each one disagrees with the others
       on where to spend complexity budget, which is exactly the
       tension you want. Lock it in, or adjustments?"
```

**Vibes-only creative brief:**

```
You: "I want to make a tabletop RPG. Something dark and weird,
      like if Miyazaki directed D&D."

GIGO: "Custom system, no safety net of an existing engine. That's
       more work but more control. Here's who I'd bring in:

        The Mythwright
        Fumito Ueda's design-through-absence. What you don't
        explain is more haunting than what you do. + Miyazaki's
        moral complexity. No pure villains, just beings with
        alien logic. + Kentaro Miura's capacity to make beauty
        feel precarious. Owns your setting, your tone, and the
        question 'does this feel wrong in the right way?'

        The Mechanist
        Vincent Baker's 'fiction first' engine philosophy.
        Apocalypse World proved mechanics should emerge from
        the narrative. + Luke Crane's conviction that the system
        should hurt. Advancement costs something. + Ben Milton's
        Knave-style minimalism. If a rule doesn't create a
        meaningful decision, cut it.

        The Dread Cartographer
        Grant Howitt's one-page game clarity. Honey Heist proved
        you can teach a game in minutes without losing depth.
        + Emmy Allen's Stygian Library approach to procedural
        wonder. Tables that generate mood, not just content.

       Want me to tell you more about any of them, swap someone
       out, or does this feel like the right team?"
```

Same skill, different calibration. Software, fiction, game design, research, music, business.

---

Built at [Croftspan](https://croftspan.com). apache 2.0.

[Research](site/research/) · [Get Started](site/docs/getting-started.html) · [Skills](site/docs/skills.html) · [Architecture](site/docs/architecture.html)
