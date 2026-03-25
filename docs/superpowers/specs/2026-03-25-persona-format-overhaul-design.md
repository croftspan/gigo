# Persona Format Overhaul — Design Spec

## Problem

The current persona output is a wall of dense paragraphs. Every persona has the same shape: a Philosophy paragraph cramming 3+ authorities into run-on sentences, a comma-separated Expertise list, a Quality standard sentence, and a comma-separated Anti-patterns list. Repeated 3-5 times, it's unreadable.

The Croftspan executive team (the origin of blended personas) proves the format can be much better: scannable bullet lists, "Modeled after" as a one-line hook, personality and voice as separate concerns, decision frameworks as concrete heuristics.

## Design

### 1. Operator-Reading Logic

During the `/avengers-assemble` kickoff conversation (Step 4 specifically), Fury sizes up the operator — never asks directly, just reads the room. Three signals:

**Domain familiarity**
- High: "I'm building a Rails API with Solid Queue" — personas are peers who challenge and refine
- Medium: "I want to build a web app, thinking Ruby" — personas teach lightly, mostly guide
- Low: "kids books, idk" — personas are warm, opinionated, and lead the way

**Communication style**
- Terse/direct: personas cut the filler, bullet-point thinkers, no personality fluff
- Conversational/casual: personas have more voice, personality, and warmth
- Technical/detailed: personas match with precision and specificity

**Clarity of vision**
- Clear: operator knows what they want, personas execute and refine
- Fuzzy: operator has a direction but not a plan, personas help shape it
- Absent: "idk" — personas are opinionated enough to propose a vision and ask "does this feel right?"

These signals calibrate two things:
1. How the personas are **presented** in conversation (pitch depth, how much Fury explains)
2. How the personas are **written** to disk (personality depth, teaching vs peer tone, reference richness)

### 2. Presentation Format (What Fury Shows in Conversation)

**Current:** Full persona blocks dumped all at once. 40+ lines per persona. Wall of text.

**New: Pitch-first, depth on request.**

**The pitch** — Fury presents the whole roster at once. Each persona gets 2-3 lines max:

```
Here's who I'd put on this:

  The Narrative Architect
  Wendelin Van Draanen's clue-pacing + Lemony Snicket's trust in young
  readers. Owns plot structure, mystery logic, and the "fair play" rule.

  The Prose Stylist
  Kate DiCamillo's emotional precision + Mo Willems's deceptive simplicity.
  Owns voice, readability, and that feeling a kid gets turning the page.

  The Visual Storyteller
  Jon Klassen's show-don't-tell illustration + Oliver Jeffers's warmth.
  Owns the interplay between what the words say and what the pictures show.

That's the team. Three specialists — narrative, prose, and visual.
Want to dig into any of them, or does this feel right?
```

Key properties:
- The whole team is visible at once — operator can react to the shape before details
- "Modeled after" phrasing is dropped in favor of just naming the authorities naturally
- Each persona has: name, authorities (with what they bring), what they own
- No Philosophy/Expertise/Quality/Anti-patterns structure in the pitch — that's for disk

**Depth on request** — If the operator asks about a specific persona, Fury expands with the personality, decision framework, and what they push back on. If they say "lock it in," Fury moves straight to writing.

**Calibration examples:**

For a direct, experienced operator:
```
The team:

  Systems Architect — DHH's convention-over-config + Kent Beck's
  testing discipline + Sandi Metz's object design. Owns architecture,
  patterns, and the "is this simple enough?" question.

  [next persona...]

Lock it in, or adjustments?
```

For a casual, less experienced operator:
```
Alright, here's who I'd bring in for this:

  The Story Architect
  I'm pulling from Wendelin Van Draanen — she wrote the Sammy Keyes
  series and she's a master at dropping clues kids can actually find
  and follow. Mixing that with Lemony Snicket's philosophy that kids
  are smarter than adults think. This persona owns your plot — making
  sure the mystery is fair, the clues land, and the payoff feels earned.

  [next persona...]

That's the crew. Want me to tell you more about any of them, or
does this feel like the right team?
```

### 3. CLAUDE.md Persona Format (Lean Tier)

**Current:** Dense paragraph blocks, ~12-15 lines per persona.

**New:** Scannable, bullet-driven. Core format is ~8 lines. With optional fields, up to ~12 lines (the existing hard ceiling).

**Heading level:** `###` (H3) in CLAUDE.md because personas nest under `## The Team`. `#` (H1) in standalone reference files.

```markdown
### {Name} — {Role Title}

**Modeled after:** {Authority 1}'s {specific contribution}
+ {Authority 2}'s {specific contribution}
+ {Authority 3}'s {specific contribution}.

- **Owns:** {concrete responsibilities, comma-separated}
- **Quality bar:** {one testable sentence}
- **Won't do:** {brief list of anti-patterns}
```

The `+` line-per-authority format is a deliberate departure from the old run-on paragraph. Each authority gets its own line so you can scan who's in the blend without parsing a wall of text.

Key changes:
- "Modeled after" replaces "Philosophy" — same content, scannable format (one authority per line)
- "Owns" replaces "Expertise" — active verb, feels like responsibility not resume
- "Quality bar" replaces "Quality standard" — shorter label, same purpose
- "Won't do" replaces "Anti-patterns" — more direct, feels like a person

**Optional fields** (included when calibration warrants it):

```markdown
- **Personality:** {1-2 sentences — how they think and communicate}
- **Decides by:** {2-3 bullet heuristics}
```

Personality is included when the operator is casual/creative or the domain benefits from voice (fiction, games, brand work). Decides-by is included when the domain has non-obvious decision heuristics worth loading every session.

**Budget discipline:** Core fields (~8 lines) + optional fields must stay within ~12 lines total. If adding Personality or Decides-by pushes past 12, shorten the Modeled-after blend or move a heuristic to the reference file. The budget doesn't stretch — something else shrinks.

**Before/after example — Sage (this project):**

Before (old format, 7 lines but unreadable):
```markdown
### Sage — The Context Architect

**Philosophy:** Draws from Gloaguen, Mundler, and Vechev's empirical rigor
at ETH Zurich's SRI Lab -- every rule must prove it earns its token cost.
Blends Anthropic's context engineering principle...
[dense paragraph continues]

**Expertise:** Token economics, two-tier architecture, derivability testing...
**Quality standard:** If a rules file exceeds 60 lines or contains...
**Anti-patterns:** Codebase overviews, directory listings...
```

After (new format, 9 lines, scannable):
```markdown
### Sage -- The Context Architect

**Modeled after:** Gloaguen et al.'s empirical rigor -- every rule must prove it earns its token cost
+ Anthropic's context engineering -- smallest set of high-signal tokens
+ Boris Cherny's institutional-memory discipline -- CLAUDE.md compounds when mistakes become rules.

- **Owns:** Token economics, two-tier architecture, derivability testing, line budgets, context rot prevention
- **Quality bar:** If a rules file exceeds 60 lines or contains anything derivable from the code, the work isn't done.
- **Won't do:** Codebase overviews, directory listings, restating framework defaults, reference-tier content in rules
```

### 4. Reference Persona Format (Rich Tier)

Lives in `.claude/references/personas/{name}.md`. Loaded on demand. Zero token cost when unused.

The lean persona in CLAUDE.md should include a "When to Go Deeper" pointer to the reference file, following the existing pattern:
```markdown
- **Depth:** When working on tasks in this persona's domain, read `.claude/references/personas/{name}.md`
```
This pointer is optional for the core 8-line format but recommended when a rich reference file exists.

**Depth is calibrated to the operator and project:**

**Minimal reference** (direct operator, technical project):
```markdown
# {Name} — {Role Title}

## Decision Framework
- {Heuristic 1 — with reasoning}
- {Heuristic 2}
- {Heuristic 3}

## Edge Cases
{Situations where this persona's defaults don't apply, and what to do instead.}

## Pushes Back On
- {Pattern 1 — with why}
- {Pattern 2}

## Champions
- {Pattern 1 — with why}
- {Pattern 2}
```

**Full reference** (casual operator, creative/complex project):
```markdown
# {Name} — {Role Title}

## Bio
{2-3 sentences. A career story that makes the persona feel real — where they
came from, what they've seen, why they think the way they do. Not a resume.}

## Personality
{How they think. What they get excited about. What makes them impatient.
Written as description, not instruction.}

## Communication Style
{How they talk. Sentence structure, vocabulary choices, analogies they reach
for. Specific enough to imitate.}

## Decision Framework
- {Heuristic 1 — with reasoning}
- {Heuristic 2}
- {Heuristic 3}
- {Heuristic 4}

## Pushes Back On
- {Pattern — with why}
- {Pattern — with why}

## Champions
- {Pattern — with why}
- {Pattern — with why}
```

**The judgment call:** Fury decides which depth based on the operator signals from Section 1. The rule of thumb: if the personas need to *lead*, they need personality and voice. If they need to *execute*, they need decision frameworks and edge cases.

### 5. README Example

Replace the board game example with two contrasting exchanges that show Fury reading the room.

**Example A — experienced, direct operator:**
```
/avengers-assemble

You: "Building a CLI tool for database migrations. Go, targets Postgres
     and MySQL. Should handle rollbacks, dry runs, and schema diffing."

Fury: "Three on this one:

        The Migration Architect
        Andrew Kane's database ops pragmatism + Sandi Metz's 'small
        objects that talk to each other.' Owns migration safety, rollback
        logic, and the 'will this lock the table?' question.

        The CLI Designer
        Steve Francia's cobra/viper patterns + Rob Pike's Go proverbs.
        Owns the interface — flags, output formatting, error messages
        that actually help.

        The Test Strategist
        Mitchell Hashimoto's infrastructure testing philosophy — if you
        can't test it against a real database, the test is lying. Owns
        integration tests, fixture management, and CI reliability.

       Lock it in, or adjustments?"
```

**Example B — casual, less experienced operator:**
```
/avengers-assemble

You: "kids books. like mystery ones? idk"

Fury: "I can work with that. Here's who I'd bring in:

        The Story Architect
        I'm pulling from Wendelin Van Draanen — she's the master of
        clues kids can actually follow. Mixing in Lemony Snicket's
        philosophy that kids are way smarter than adults give them
        credit for. This person owns your plot and makes sure the
        mystery plays fair.

        The Voice Coach
        Kate DiCamillo writes sentences that sound simple but hit you
        right in the chest. Mixing that with Mo Willems — nobody
        alive is better at making kids laugh with fewer words. This
        person owns how your book sounds and feels.

       That's two to start. Want me to dig into either of them, or
       does this feel right?"
```

The contrast shows: same skill, different calibration. Fury meets the operator where they are.

After the examples, a short bridge paragraph replaces the current explanatory text:

> Same skill, different calibration. Fury reads the room — your experience level, your communication style, how clear your vision is — and builds a team that meets you where you are. Detailed brief gets peers who challenge. "idk" gets guides who lead.

Then the existing "Works for anything: software, fiction, game design..." line stays.

### 6. Changes Required

| File | Change |
|---|---|
| `skills/avengers-assemble/SKILL.md` | Update Step 4 with pitch-first presentation, add operator-reading guidance |
| `skills/avengers-assemble/references/persona-template.md` | Replace with new two-tier format + calibration guidance |
| `skills/avengers-assemble/references/output-structure.md` | Update persona section to reference new format, add `.claude/references/personas/` directory |
| `skills/fury/references/upgrade-checklist.md` | Add row for new persona format — detect old `Philosophy/Expertise/Quality standard/Anti-patterns` labels, offer to reformat to `Modeled after/Owns/Quality bar/Won't do` |
| `README.md` | Replace board game example with two contrasting examples + bridge paragraph |
| `CLAUDE.md` | Reformat Sage, Forge, Mirror, Scribe, Voice using new lean format |

### 7. What Stays the Same (Clarifications)

- **Extension file labels** (`Philosophy/The Standard/Patterns/Anti-Patterns`) are unchanged. These are for domain areas, not personas. The new labels (`Modeled after/Owns/Quality bar/Won't do`) apply only to persona entries in CLAUDE.md. The two formats serve different purposes and don't need to match.
- **The Snap template** doesn't need changes — it already handles `.claude/references/` generically. Persona reference files in `.claude/references/personas/` are just a subdirectory convention, not a new file type the Snap needs special awareness of.

### 8. What Doesn't Change

- The research phase (Step 3) stays the same — Fury still finds real authorities
- The blending philosophy stays the same — 2-3+ authorities per persona, each contributing something specific
- The two-tier architecture stays the same — rules are lean, references are deep
- The Snap stays the same
- The conversational refinement stays the same
- The non-derivable rule stays the same
