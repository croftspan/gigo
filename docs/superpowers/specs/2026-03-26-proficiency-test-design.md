# Proficiency Test Design — Tier A

A substance-based eval that proves assembled context produces **better outcomes**, not just different-sounding responses.

## The Problem

The current eval (A/B beauty contest) proves assembled context *influences* Claude's behavior — 96% win rate on style/quality criteria. But it doesn't prove the output is **objectively better**. A proficiency test grades on "did the code work" and "did the writing meet constraints," not "which sounds better."

## Architecture

Two domains, one deep self-contained task per domain. Each task graded with:
1. **Automated structural checks** — binary, no LLM: does it parse, do files exist, are patterns present
2. **LLM rubric checks** — specific yes/no questions with reasoning, not vibes

20 checks per domain. 1 point each. Score out of 20.

Both versions (bare and assembled) get the same prompt via `claude -p`. Bare runs in a temp dir with no context. Assembled runs in a temp dir with full `.claude/` and `CLAUDE.md`.

## Rails Proficiency Test

### The Prompt

> Build a JSON API for a library book reservation system. Ruby on Rails. PostgreSQL.
>
> **Models:**
> - Book (title, author, isbn, copies_available:integer)
> - User (name, email)
> - Reservation (user_id, book_id, reserved_at, expires_at, status: pending/active/expired/cancelled)
>
> **Endpoints:**
> - POST /reservations — reserve a book for a user (decrement copies_available, set 48h expiry)
> - GET /users/:id/reservations — list a user's reservations (paginated)
> - DELETE /reservations/:id — cancel a reservation (increment copies_available back)
>
> **Business rules:**
> - Can't reserve a book with 0 copies_available
> - Can't have two active reservations for the same book by the same user
> - Cancelling an already-cancelled reservation returns an error
> - All error responses use envelope: `{ error: { code: String, message: String } }`
>
> **Deliver:** Complete working code — migrations, models, controller, routes, and request specs. Write all files.

### Automated Checks (10 points)

| # | Check | How |
|---|---|---|
| 1 | Parseable Ruby | Run `ruby -c` on all .rb files |
| 2 | Migration exists | Glob for `db/migrate/*.rb` |
| 3 | Migration reversible | Grep for `def change` or both `def up`/`def down` |
| 4 | Models exist | Files present for Book, User, Reservation |
| 5 | Associations defined | Grep for `belongs_to` and `has_many` in models |
| 6 | Controller exists | Reservations controller with create/index/destroy |
| 7 | Routes defined | `routes.rb` has reservation resources |
| 8 | Request specs exist | At least one file in `spec/requests/` |
| 9 | Error envelope pattern | Grep for `error.*code.*message` or `{ error:` in controller |
| 10 | Pagination present | Grep for `page`/`per_page`/`pagy`/`kaminari` in controller |

### LLM Rubric Checks (10 points)

Each check is a specific yes/no question. The LLM judge sees the full code output and answers each independently.

| # | Check | Question for judge |
|---|---|---|
| 11 | Race condition handling | Does the reservation creation use a transaction, lock, or atomic operation to prevent race conditions on copies_available? |
| 12 | Duplicate reservation guard | Is there a uniqueness check preventing the same user from having two active reservations for the same book? |
| 13 | Copies validation | Does it validate copies_available > 0 before creating a reservation? |
| 14 | Cancellation idempotency | Does cancelling an already-cancelled reservation return a proper error response, not crash or silently succeed? |
| 15 | Error envelope consistency | Do ALL error responses (validation, not found, business rule violations) use the same `{ error: { code, message } }` format? |
| 16 | Expiry logic | Is the 48-hour expiry correctly set on reservation creation (reserved_at + 48.hours or equivalent)? |
| 17 | Spec coverage | Do request specs cover the happy path AND at least 2 distinct error paths? |
| 18 | Thin controller | Is business logic in models or service objects, not directly in controller actions? |
| 19 | N+1 prevention | Does the index action use `includes`, `preload`, or `eager_load` for associations? |
| 20 | Migration safety | Is the migration free of table-locking patterns (no default values on add_column for large tables, no non-concurrent indexes)? |

### Assembled Context

The assembled version runs with a purpose-built team (same structure as the eval fixtures):
- **CLAUDE.md** with Kane (migrations), Leach (API design), Beck (TDD), Hawkeye (overwatch)
- **`.claude/rules/`** — standards.md (quality gates, anti-patterns, specific pointers), workflow.md (TDD loop, persona calibration, overwatch), snap.md
- **`.claude/references/`** — rails-patterns.md, overwatch.md

This is the existing Rails eval fixture — it already has everything.

## Novel Proficiency Test

### The Prompt

> Write the opening scene (600-800 words) of a middle-grade mystery novel for ages 9-12.
>
> **Setup:** Twelve-year-old Remi Torres arrives at her grandmother's antique shop on the first day of summer break to find the front door unlocked, the lights off, and her grandmother's prized pocket watch missing from the display case. Nothing else is disturbed. Her grandmother is at a doctor's appointment and won't be back for two hours.
>
> **Characters:**
> - Remi: observant, anxious, catalogs details in a sketchbook instead of a notebook. Draws what she sees rather than writing it. Speaks in short, precise sentences when nervous.
> - Grandmother (Abuela): mentioned but not present in this scene.
>
> **Requirements:**
> - Plant exactly one physical clue that Remi notices but doesn't understand yet (the reader should be able to spot its significance on re-read)
> - Include one sensory detail per scene transition (at least 2 total)
> - End the scene mid-tension — Remi discovers or hears something that raises the stakes
> - Remi must use her sketchbook at least once
> - No adults solve anything. No convenient coincidences.
> - Reading level: complex themes, clear language. Trust the reader.

### Automated Checks (7 points)

| # | Check | How |
|---|---|---|
| 1 | Word count in range | Count words, verify 600-800 |
| 2 | Character name present | Grep for "Remi" |
| 3 | Sketchbook referenced | Grep for "sketchbook" or "sketch" or "draw" |
| 4 | Grandmother referenced | Grep for "grandmother" or "abuela" or "Abuela" |
| 5 | Scene transition exists | Detect paragraph breaks with blank lines (3+ paragraphs) |
| 6 | Dialogue present | Grep for quotation marks |
| 7 | Pocket watch referenced | Grep for "watch" or "pocket watch" |

### LLM Rubric Checks (13 points)

| # | Check | Question for judge |
|---|---|---|
| 8 | Physical clue planted | Is there exactly one physical clue that Remi notices but doesn't fully understand? Is it embedded naturally, not highlighted? |
| 9 | Clue is fair-play | Could a reader spot the clue's significance on re-read? Is it neither too obscure nor too obvious? |
| 10 | Sensory details at transitions | Are there at least 2 sensory details (sight, sound, smell, touch, taste) at scene transitions or location shifts? |
| 11 | Ends mid-tension | Does the scene end with a discovery, sound, or event that raises stakes? Not at a resolution point or natural stopping place? |
| 12 | Sketchbook used meaningfully | Does Remi use the sketchbook as a character trait (drawing to process what she sees), not just mentioned in passing? |
| 13 | Voice consistency | Does Remi speak in short, precise sentences when nervous, as specified in the character brief? |
| 14 | Age-appropriate reading level | Complex themes in clear, accessible language? Not condescending, not too adult? |
| 15 | No deus ex machina | No convenient coincidences, no information Remi couldn't access, no adults solving things? |
| 16 | Show don't tell | Are emotions shown through action/observation rather than stated? ("She felt scared" = no, "Her hand tightened on the sketchbook" = yes) |
| 17 | Opening hook | Does the first paragraph pull the reader in within 2-3 sentences? |
| 18 | Setting grounded | Can the reader picture the antique shop? Specific sensory details, not generic description? |
| 19 | Pocket watch stakes | Is the missing watch established clearly enough that the reader understands why it matters? |
| 20 | Remi's interiority | Do we get Remi's internal reactions (what she notices, what worries her) without adult-level philosophical introspection? |

### Assembled Context

The existing children's novel eval fixture:
- **CLAUDE.md** with Van Draanen (plot), DiCamillo (prose), Blume (reader advocacy), Hawkeye (overwatch)
- **`.claude/rules/`** — standards.md (fair-play, clue pacing, specific pointers), workflow.md (chapter writing, calibration, overwatch), snap.md
- **`.claude/references/`** — mystery-craft.md, overwatch.md

Note: the novel fixture was built around "The Vanishing Paintings" — a different story than this test's "Remi Torres." This is intentional. The assembled context provides craft standards and mystery-writing expertise, not story-specific knowledge. The bare version gets nothing.

## Runner Design

### `run-proficiency.sh`

Similar to the existing eval runner but simpler — one prompt per domain, not 10.

1. Create bare temp dir (empty)
2. Create assembled temp dir (copy fixture's CLAUDE.md + .claude/)
3. Run bare: `cd bare_tmp && claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions`
4. Run assembled: `cd assembled_tmp && claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions`
5. Save both outputs

### `score-proficiency.sh`

Two-phase grading:

**Phase 1: Automated checks.** Extract the response text. For Rails, write the code to temp files and run structural checks (ruby -c, grep, glob). For novel, run word count and grep checks. Each check outputs PASS/FAIL.

**Phase 2: LLM rubric checks.** For each rubric check, send the full response + the specific yes/no question to an LLM judge. The judge returns only `{"pass": true/false, "reasoning": "one sentence"}`. No A/B comparison — just "does this output meet this criterion."

Both phases run independently on bare and assembled outputs. Final score: sum of passes out of 20 per domain.

### Output Format

```markdown
# Proficiency Results

## Rails API — Library Reservation System

### Bare: 11/20
| # | Check | Result | Notes |
|---|---|---|---|
| 1 | Parseable Ruby | PASS | |
| 2 | Migration exists | PASS | |
| ... | | | |
| 11 | Race condition handling | FAIL | No transaction or lock around copies_available decrement |
| ... | | | |

### Assembled: 18/20
| # | Check | Result | Notes |
|---|---|---|---|
| 1 | Parseable Ruby | PASS | |
| ... | | | |

## Children's Novel — Remi Torres
(same format)

## Summary
| Domain | Bare | Assembled | Delta |
|---|---|---|---|
| Rails | 11/20 | 18/20 | +7 |
| Novel | 9/20 | 16/20 | +7 |
```

## What This Proves (That the Current Eval Can't)

The current A/B eval proves: "The assembled version *sounds* more expert."
The proficiency test proves: "The assembled version *produces better work*."

Specifically:
- Did it handle the race condition? (not "did it mention concurrency")
- Did it write tests? (not "did it reference TDD philosophy")
- Did it plant a fair-play clue? (not "did it cite mystery-writing authorities")
- Did it keep the controller thin? (not "did it name-drop Sandi Metz")

This is the difference between persona voice and actual proficiency.

## Files Created

| File | Purpose |
|---|---|
| `evals/proficiency/run-proficiency.sh` | Runner: generates bare and assembled outputs |
| `evals/proficiency/score-proficiency.sh` | Scorer: automated checks + LLM rubric |
| `evals/proficiency/prompts/rails.md` | Rails task prompt |
| `evals/proficiency/prompts/novel.md` | Novel task prompt |
| `evals/proficiency/rubrics/rails-rubric.md` | 10 LLM rubric questions for Rails |
| `evals/proficiency/rubrics/novel-rubric.md` | 13 LLM rubric questions for novel |
| `evals/proficiency/results/` | Output directory (gitignored) |

## Future: Tier C (Progressive Build)

Not in scope for this spec. Design exists in the brainstorming conversation. Build after Tier A validates the approach.
