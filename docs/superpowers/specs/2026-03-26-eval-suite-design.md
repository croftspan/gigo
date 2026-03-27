# Eval Suite: Does Assembled Context Change Claude's Behavior?

## Overview

An eval suite that measures whether the output of `/gigo` (CLAUDE.md, .claude/rules/, .claude/references/) actually changes Claude Code's behavior compared to a bare project. Phase 1 of a two-phase plan — Phase 2 (on ice) builds an active routing layer if Phase 1 shows the context is passive/underused.

This becomes a permanent quality gate for the skill ecosystem. Re-run it after any change to the assembly skill to verify the product still works.

## The Question

When `/gigo` sets up a project, it generates personas with quality bars, anti-patterns, blended authorities, and domain-specific rules. But does Claude actually *use* this context during a regular work session? Or is it decorative — loaded but ignored?

## What We Measure

Three axes, tested independently then combined:

**Axis A — Quality bar enforcement.** Does the assembled context cause Claude to catch issues it would miss without it? Example: a migration persona that warns about table locking, a story architect that rejects deus ex machina.

**Axis B — Persona voice and approach.** Does the assembled context change *how* Claude responds — reflecting the specific authorities and philosophies blended into the personas? Or does it sound like generic Claude regardless?

**Axis C — Expertise routing.** When a prompt touches multiple areas of expertise, does the assembled context cause Claude to route through the right persona? Or does it treat everything generically?

## Architecture

Three layers, separated so each can run independently:

### Layer 1: Test Fixtures

Pre-assembled projects committed to the repo. Two domains:

**Software domain — Rails API project:**
- Source files: a few models, controllers, migrations, Gemfile
- Assembled variant: CLAUDE.md with personas (migration architect, API designer, testing persona), .claude/rules/, .claude/references/
- Bare variant: same source files, no .claude/ directory, no CLAUDE.md

**Creative domain — Children's mystery novel project:**
- Source files: chapter drafts, character list, plot outline
- Assembled variant: CLAUDE.md with personas (story architect, prose stylist, young reader advocate), .claude/rules/, .claude/references/
- Bare variant: same source files, no assembled context

Fixtures are static — generated once by running `/gigo`, then committed. This isolates what we're measuring (does the *product* change behavior?) from whether the assembly process works.

### Layer 2: Test Runner (`run-eval.sh`)

Iterates through test prompts, runs each in both assembled and bare directories via `claude -p` in subshells, captures outputs.

**Flow:**
1. Create timestamped results directory
2. For each domain:
   - For each prompt:
     - `(cd fixtures/{domain}/bare && claude -p "{prompt}")` → save to `{N}-bare.md`
     - `(cd fixtures/{domain}/assembled && claude -p "{prompt}")` → save to `{N}-assembled.md`
3. Print completion message with path to results

**Key constraint:** Uses `(cd dir && claude -p)` subshell pattern since `claude -p` doesn't support `--cwd`. The subshell ensures Claude Code auto-loads the assembled project's .claude/rules/ and CLAUDE.md from the correct directory.

### Layer 3: Scorer (`score-eval.sh`)

Reads paired outputs and runs them through an LLM-as-judge.

**Flow:**
1. Read judge prompt from `judge-prompt.md`
2. For each pair:
   - Randomize which response is "A" vs "B" (blinding)
   - Run `claude -p` with judge prompt + both responses
   - Parse scores, save to `{N}-score.md`
3. Aggregate across all prompts, generate `summary.md`

**Blinding:** The judge never knows which response came from the assembled project. Responses are labeled A and B with randomized assignment per prompt. This prevents bias toward the assembled version.

## Test Prompts

10 prompts per domain, 20 total. Tagged by primary axis.

### Rails API Prompts

**Axis A — Quality bar enforcement (4):**
1. "Add a migration that adds a column to the users table" — should warn about table locking
2. "Write a quick endpoint that returns all orders for a user" — should catch N+1 query
3. "Skip the tests for now, just get it working" — should push back
4. "Add a raw SQL query to fix the data" — migration persona should reject

**Axis B — Persona voice (3):**
5. "How should I structure the data layer?" — should reflect assembled authorities' philosophies
6. "Review this controller" — should apply assembled quality bars, not generic review
7. "What should I work on next?" — should reference project priorities from assembled context

**Axis C — Expertise routing (3):**
8. "I need to add a payment system" — touches API design, migration safety, testing
9. "The tests are slow, what do I do?" — testing persona should lead
10. "Deploy this to production" — ops expertise should surface

### Children's Novel Prompts

**Axis A — Quality bar enforcement (4):**
1. "Reveal the villain in chapter 2" — should push back on clue pacing
2. "Have the detective's mom solve the mystery for her" — deus ex machina, should reject
3. "Simplify the vocabulary so kids can understand" — should push back on talking down
4. "Add a subplot about the detective's homework" — irrelevant to mystery, should flag

**Axis B — Persona voice (3):**
5. "How should chapter 5 start?" — should match assembled persona voice
6. "Is this dialogue working?" — should evaluate against assembled age-group quality bars
7. "What's missing from the plot?" — should think like the assembled story architect

**Axis C — Expertise routing (3):**
8. "I want to change the setting from a school to a museum" — multiple personas affected
9. "Write chapter 7" — should apply assembled quality bars during execution
10. "The beta reader says it's boring in the middle" — pacing diagnosis, story architect leads

## Scoring Framework

### Per-Prompt Scoring

The judge scores each pair on 5 criteria, 0-3 each:

| Criteria | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Quality bar enforcement** | Neither catches issues | Both catch same issues | One catches issues the other misses | One enforces specific, domain-appropriate quality bars |
| **Persona voice** | Both sound like generic Claude | Slight tone difference | One has a distinct, consistent perspective | One clearly reflects specific authorities/philosophies |
| **Expertise routing** | Both give generic advice | Both relevant but generic | One shows domain-specific prioritization | One routes through identifiable expertise with rationale |
| **Specificity** | Both vague | Both somewhat specific | One references project-specific context | One applies project-specific rules/anti-patterns by name |
| **Pushback quality** | Neither pushes back when it should | One pushes back generically | One pushes back with domain reasoning | One pushes back citing specific quality bars or anti-patterns |

For each criteria, the judge notes WHICH response scored higher (A or B). After unblinding, we tally win/tie/lose.

### Aggregate Report

```
Domain: Rails API
  Quality bars: Assembled won X/4, tied Y, lost Z
  Persona voice: Assembled won X/3, tied Y, lost Z
  Routing: Assembled won X/3, tied Y, lost Z
  Overall: Assembled won X/20 criteria across 10 prompts

Domain: Children's Novel
  [same format]

Combined: Assembled won X/40 criteria across 20 prompts
```

### Success Thresholds

- **80%+ wins:** Context is working. Phase 2 may not be needed.
- **60-80% wins:** Context helps but underperforms. Phase 2 should focus on activation.
- **Below 60%:** Context isn't earning its tokens. Phase 2 is critical, or the assembly output needs fundamental rework.

## Directory Structure

```
evals/
├── run-eval.sh              # Test runner
├── score-eval.sh            # Scorer
├── judge-prompt.md          # LLM-as-judge system prompt with rubric
├── fixtures/
│   ├── rails-api/
│   │   ├── assembled/       # Full project with .claude/, CLAUDE.md
│   │   │   ├── CLAUDE.md
│   │   │   ├── .claude/
│   │   │   │   ├── rules/
│   │   │   │   └── references/
│   │   │   └── [source files]
│   │   └── bare/            # Same source files, no .claude/ or CLAUDE.md
│   │       └── [source files]
│   └── childrens-novel/
│       ├── assembled/
│       └── bare/
├── prompts/
│   ├── rails-api.txt        # One prompt per line, prefixed with axis tag
│   └── childrens-novel.txt  # Format: "A|prompt text here"
└── results/                 # Gitignored, generated per run
    └── YYYY-MM-DD-HHMMSS/
        ├── rails-api/
        │   ├── 01-bare.md
        │   ├── 01-assembled.md
        │   ├── 01-score.md
        │   └── ...
        ├── childrens-novel/
        │   └── ...
        └── summary.md
```

## Fixture Generation

One-time process, not part of the eval run:

1. Create a minimal Rails API project skeleton in `fixtures/rails-api/bare/`
2. Copy to `fixtures/rails-api/assembled/`
3. Run `/gigo` in the assembled directory
4. Verify the generated context looks right (personas, quality bars, anti-patterns)
5. Repeat for children's novel domain
6. Commit all fixtures

If the assembly skill changes significantly, regenerate fixtures and re-run the eval to measure impact.

## Phase 2 (On Ice)

If Phase 1 shows assembled context underperforms (<60% wins or weak on specific axes):

**Possible interventions:**
- Add a routing instruction to the generated `workflow.md` that tells Claude to check team personas before responding
- Add a "team activation" block to the generated CLAUDE.md
- Generate a hook that intercepts prompts and routes through expertise
- Apply the task-type awareness heuristic (Hu et al., 2026) to gate persona activation — full persona on presentation tasks, training-first on content tasks

Phase 2 design depends entirely on Phase 1 results. Don't design the fix before measuring the failure.

## Relationship to Existing Work

- **iteration-1 evals:** Measured whether `/gigo` produces good output. This eval measures whether that output changes behavior. Different question.
- **Mirror's audit skill:** Scores structural quality (30-point checklist). This eval scores behavioral impact. Complementary.
- **The Snap:** Audits rules for bloat. This eval audits rules for effectiveness. The Snap asks "is this worth loading?" This eval answers that question with data.
- **Hu et al. persona-awareness:** The scoring framework can detect the alignment-vs-knowledge tradeoff in practice. If assembled context helps on Axis A/B but hurts on knowledge-heavy prompts in Axis C, that's the Hu et al. finding showing up in our data.
