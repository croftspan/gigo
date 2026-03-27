# Pipeline Architecture — Why It Works This Way

Reference material for the Conductor persona. This explains the "why" behind the plan→bare execute→two-stage review pipeline. The eval narrative at `evals/EVAL-NARRATIVE.md` has the full data trail.

## The Proven Architecture

| Phase | Context | Why (eval phase) |
|---|---|---|
| Planning (brainstorm, spec, plan) | Assembled ON | Personas shape questions, catch architectural gaps (Phase 6) |
| Execution (all work) | Bare | Workers produce best output with training alone + good spec (Phase 7) |
| Review Stage 1 (spec compliance) | Spec as context | Catches "you built the wrong thing" (Phase 8) |
| Review Stage 2 (engineering quality) | Bare workers | Catches "you built it wrong" — race conditions, lock ordering, test quality (Phase 8) |

## Why Workers Run Bare (Phase 7)

Tested 4 context formats: war stories (468 words), compressed (287), fix-only (229), bare (0). Three runs, comparative judging.

- Bare was rated senior or staff by principal engineer review every time
- Compressed (terse rules) produced the worst code every run — real bugs found
- The delta between formats was noise. The delta between good spec and bad spec was signal.
- Workers don't need to know WHY partial unique indexes matter — they need a spec that SAYS to use one

## Why Two Review Stages, Not One (Phase 8)

Tested plan-aware, code-quality, and combined review on 4 code variants.

- Plan-aware found: expired reservation cancellation inflating inventory, missing expiry enforcement, duplicate check outside transaction
- Code-quality found: transaction-return footgun, broken concurrency tests, deadlock from inconsistent lock ordering, non-atomic operations
- Combined found FEWER issues than either focused reviewer alone (11 vs 10-15)
- One reviewer holding both lenses averages instead of adding up

## Why Personas Influence Planning (Phase 6)

Controlled test: same task, same scripted answers, only variable was team personas.

- Assembled asked FEWER questions (7 vs 10) — standards pre-answered some
- Assembled asked WHY-driven questions — "Kane needs to know scale for migration lock duration"
- Assembled caught: partial unique index, SKIP LOCKED, copy condition field, pagination, runnable test code
- Bare missed ALL of these

## Key Insight

Knowledge is in the right place at the right time:
- **Planning:** Knowledge lives in the team's questions
- **Execution:** Knowledge lives in the spec's requirements
- **Review:** Knowledge lives in the team's judgment

Trying to put knowledge into the worker's context solves the wrong problem.
