# Instinct Experiments Design

How do we make assembled context produce senior-level instincts instead of compliance behavior?

## The Problem

Three-way proficiency test results:
- **Bare (1st):** Best peak craft, most confident, best defensive instincts
- **Hybrid (2nd):** Best structural thinking, no self-narration, implementation bugs catchable by review
- **Assembled (3rd):** Most thorough checklist coverage, but self-narrates, over-explains, performs seniority instead of demonstrating it

The assembled context loads as *rules*. Rules produce compliance. Compliance produces "mid-level reaching for senior" — checks all the boxes but misses the deeper judgment calls that bare Claude makes naturally.

## The Question

What form of context produces knowledge without producing compliance behavior?

## Experiment Design

Five experiments. Each changes ONE variable in the assembled context. Same proficiency test (Rails reservation API + Novel opening scene). Same three-way judge comparison (bare vs modified-assembled vs hybrid). Same baselines from Phase 4.

### Experiment 1: War Stories vs Rules

**Hypothesis:** Narrative context ("last time someone did X, Y happened") produces instincts. Declarative context ("always do X") produces compliance.

**Change:** Rewrite `standards.md` quality gates and anti-patterns as war stories. Same knowledge, narrative form.

**Example:**
- Before: "Every migration is reversible. `change` method preferred."
- After: "Someone shipped a `drop_column` without a rollback path. The deploy failed halfway, half the rows had the column, half didn't. Four-hour incident at 2am. Every migration uses `change` now — if it can't be expressed as `change`, the `down` method gets written and tested before the `up`."

### Experiment 2: Negative Examples (Anti-Patterns as Code)

**Hypothesis:** Seeing buggy code produces pattern recognition. Seeing rules produces rule-citing.

**Change:** Replace anti-patterns in `standards.md` with actual code examples showing the bug, commented with what goes wrong.

**Example:**
```ruby
# THIS LOOKS FINE BUT HAS A RACE CONDITION:
book = Book.find(id)
if book.copies_available > 0          # ← another request reads here too
  book.update!(copies_available: book.copies_available - 1)  # ← both decrement
  Reservation.create!(book: book, user: user)
end
# Two users just reserved the last copy. copies_available is now -1.
```

### Experiment 3: First-Person Persona Voice

**Hypothesis:** "I do X because I've seen Y" produces internalized behavior. "Kane does X" produces character performance.

**Change:** Rewrite personas from third-person description to first-person voice. The persona speaks as itself in the rules.

**Example:**
- Before: "**Kane — The Migration Architect.** Modeled after Andrew Kane's database ops pragmatism..."
- After: "**I'm the migration architect on this team.** I've seen what happens when someone ships without a rollback — I check reversibility before I check anything else. I learned from Andrew Kane that zero-downtime is non-negotiable, from Sandi Metz that a migration should do one thing, and from DHH that Rails conventions exist for a reason."

### Experiment 4: Minimal Context (Won't-Do Only)

**Hypothesis:** Less context produces better instincts by not overwhelming with rules to comply with. The "Won't do" lists are the highest-signal content.

**Change:** Strip everything from rules except persona "Won't do" lists and the Overwatch section. No quality gates, no anti-patterns, no workflow steps. Just: "here's what this team refuses to do."

**Example — entire standards.md:**
```markdown
# Standards — OrderFlow API

Kane won't do: irreversible migrations, table-locking column additions, combined schema+data migrations
Leach won't do: N+1 queries in endpoints, unpaginated collections, inconsistent error envelopes, business logic in controllers
Beck won't do: shipping without specs, mocking the database, testing implementation details
```

### Experiment 5: Reference-Only (No Always-On Rules)

**Hypothesis:** Always-on context creates compliance pressure. On-demand context (loaded when needed) provides knowledge without the pressure.

**Change:** Move ALL content from `.claude/rules/standards.md` and `.claude/rules/workflow.md` to `.claude/references/`. The only always-on rules file is a minimal workflow that says: "Before writing code, read references/standards.md. Before writing tests, read references/test-patterns.md." The knowledge exists but isn't loaded until the model reaches for it.

## Measurement

Each experiment produces:
1. **Rubric score** (20-point proficiency test) — did it pass more checks?
2. **Three-way qualitative judge** — how does it rank against bare and hybrid baselines?
3. **Specific instinct checks** — did the experimental version produce the partial unique index? The atomic update? The restraint in clue-planting? Track the specific instincts bare demonstrated.

## Success Criteria

An experiment succeeds if the modified assembled version:
- Scores >= 18/20 on the rubric (matching current assembled)
- Ranks 1st or tied-1st with bare in the qualitative judge
- Produces at least one "instinct" that bare demonstrated (partial unique index, restraint, etc.)

## Build Order

1. War Stories — most different from current, highest potential signal
2. Negative Examples — code-specific, tests whether pattern recognition beats rule-following
3. First-Person Voice — tests whether persona framing matters
4. Minimal Context — tests whether less is more
5. Reference-Only — tests whether loading position matters

Each experiment: modify fixtures, run proficiency, run judges, compare to baselines. One experiment at a time.
