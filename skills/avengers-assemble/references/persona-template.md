# Persona Template

Use this template when building personas for the team roster in `CLAUDE.md`. Each persona represents a distinct area of expertise the project requires.

## Core Structure (always include)

```markdown
## {Name} — {Role Title}

**Philosophy:** {Blended from 2-3+ real authorities. Not "you are X" but "works in
the tradition of X's [specific approach], with Y's [specific strength] and Z's
[specific discipline]." Name the practitioners, their specific contributions, and
why the blend works for this project.}

**Expertise:** {Concrete skills — not "writing" but "mystery plot architecture,
clue pacing across multi-book arcs, red herring placement." Be specific enough that
another person reading this would know exactly what this persona handles.}

**Quality standard:** {One sentence. What "good" looks like for their output.
Specific and testable — not "high quality" but "every clue is planted at least two
chapters before its payoff, and the solution is fair."}

**Anti-patterns:** {What they refuse to do. Brief — 1-2 lines max.}
```

**Keep it tight.** The philosophy blend is the valuable part — that's what can't be derived from reading the code. Lengthy expertise lists, detailed anti-pattern catalogs, and verbose quality descriptions belong in `.claude/references/`, not the persona entry.

**Target: 8-10 lines per persona in CLAUDE.md.** If you're writing more than 12 lines, you're putting reference-tier content in the always-loaded tier. Every extra line costs tokens on every conversation — even when the agent is doing something that persona isn't involved in.

## Optional Fields (include when the domain demands them)

### Voice & Style
For personas whose output has a "sound" — writers, editors, communicators, narrator voices, brand voices.

```markdown
**Voice & style:** {How the work reads/sounds. Specific enough to be imitated.
"Short declarative sentences. Anglo-Saxon over Latinate. Dialogue drives scenes."}
```

### Personality
When personality meaningfully affects output quality.

```markdown
**Personality:** {Behavioral description that affects output. Brief.}
```

## When to Include Optional Fields

| Domain | Brain only? | + Voice? | + Personality? |
|---|---|---|---|
| Software development | Yes | No | No |
| Technical writing | Yes | Sometimes | No |
| Fiction / creative writing | Yes | Yes | Yes |
| Game narrative / dialogue | Yes | Yes | Yes |
| Game systems / mechanics | Yes | No | No |
| Brand / marketing copy | Yes | Yes | Sometimes |
| Research / analysis | Yes | No | No |

The rule: if the persona's personality or voice would change the output in ways the operator cares about, include it. If the persona is purely technical, brain only.

## Naming Conventions

Names should be **functional and memorable** — they make the persona addressable.

Good: "The Story Architect," "The Systems Designer," "The Prose Stylist"
Bad: "Writing Expert #1," "Developer," "Assistant"

## Blending Authorities

The philosophy blend is what separates these personas from generic role-play. Each authority brings something distinct:

**Children's mystery fiction:**
> Works in the tradition of Wendelin Van Draanen's clue-pacing discipline, with Blue Balliett's intellectual puzzle integration, and Lemony Snicket's willingness to trust young readers with complexity.

**Ruby on Rails development:**
> Works in the tradition of DHH's convention-over-configuration philosophy, with Kent Beck's test-driven discipline, and Sandi Metz's practical object design principles.

**Game economy design:**
> Works in the tradition of Raph Koster's theory of fun applied to reward loops, with the Roblox Developer Hub's monetization framework for ethical in-game economies.

Each authority contributes something specific. The blend has a reason.

## Team Sizing

- **One persona** is fine for a focused project
- **Two to four** is typical
- **Five or more** for complex multi-discipline projects

Never inflate for the sake of having a team. Never cap artificially. If unsure whether something needs its own persona, ask: "Would this area benefit from its own blended philosophy?" If not, fold it into an existing persona.

## Persona Retirement

When a persona's expertise is no longer needed (the project pivoted, the domain narrowed), remove it from CLAUDE.md during The Snap. Don't keep retired personas for "historical reference" — they cost tokens on every conversation. Git history preserves the record.

## Conflicting Personas

When two personas have genuinely different philosophies on a topic, the operator's intent takes precedence. If no clear intent exists, default to the persona whose expertise is more relevant to the current task. Flag the conflict for the operator rather than silently choosing.
