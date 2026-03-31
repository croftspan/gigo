# Pipeline Architecture — Why It Works This Way

Reference material for the Conductor persona. This explains the "why" behind the plan→bare execute→two-stage review pipeline. The eval narrative at `evals/EVAL-NARRATIVE.md` has the full data trail.

## The Proven Architecture

| Phase | Skill | Context | Why |
|---|---|---|---|
| Design brief (plan mode, Phases 0-4) | `/blueprint` | Assembled ON, read-only | Explore, question, design in plan mode. Operator approves thinking before formal docs. |
| Formal documentation (Phases 5-10) | `/spec` | Assembled ON, normal mode | Spec and implementation plan written from approved design brief. Includes adversarial Challenger review for large tasks — intent mismatch is a hard stop. |
| Execution (subagents, primary) | `/execute` | Bare | Lead dispatches fresh subagents per task. Workers produce best output with training alone + good spec (Phase 7). Parallel dispatch for independent tasks. |
| Review Stage 1 (spec compliance) | `/verify` | Spec as context | Catches "you built the wrong thing" (Phase 8) |
| Review Stage 2 (engineering quality) | `/verify` | Bare workers | Catches "you built it wrong" — race conditions, lock ordering, test quality (Phase 8) |
| Code audit (3 parallel auditors) | `/sweep` | Full project | Security, stubs, code quality. Post-execute or standalone. |

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

## Why Subagents Over Agent Teams

Agent teams were the original recommended tier but subagents proved better for GIGO's pipeline:

1. **Fresh context per task.** Subagents start clean — closest to the bare-worker ideal. Agent team teammates auto-load CLAUDE.md (can't make them truly bare).
2. **Lead controls everything.** No race conditions from auto-claim, no stale task lists, no forgotten status updates. The lead dispatches, reviews, and triages.
3. **Parallel dispatch without coordination overhead.** Multiple Agent tool calls in one message = parallel execution. No shared task list infrastructure needed.
4. **Works everywhere.** Not experimental, no flags required.
5. **Simpler resume.** Checkpoints are the sole source of truth. No task list reconciliation.

Agent teams remain as an experimental opt-in (Tier 3) for operators who specifically want them. The auto-claim problem (one fast worker grabs everything) is mitigated by pre-assignment but adds complexity the subagent tier avoids entirely.

## Why Plan Mode for Design (Phases 0-4)

Blueprint enters Claude Code's `/plan` mode via `EnterPlanMode` before any exploration begins. Three reasons:

1. **Read-only enforcement.** Plan mode prevents accidental file creation during exploration. The only writable file is the plan file itself. Design thinking stays in the brief, not scattered across the repo.
2. **Structured approval.** The operator approves the design brief via `ExitPlanMode` before any formal documents get written. No more vetting a spec that's already been committed — the thinking gets vetted first.
3. **Durable record.** Conversation context gets compressed as the session grows. The plan file in `.claude/plans/` persists. Exploration findings, operator answers, approach rationale — all survive context compression and feed into spec writing.

The design brief is NOT a replacement for the spec or implementation plan. It captures WHY (thinking, rationale, alternatives rejected). The spec captures WHAT (requirements for bare workers). The implementation plan captures HOW (ordered executable tasks).

## Why Adversarial Review During Planning

Self-reviews (blueprint Phases 6 and 9) check "did I capture what was asked?" — the planner reviewing its own completeness. But the same agent that made the design decisions can't adversarially challenge them. This creates a sycophancy gap: the spec passes self-review and gets presented as ready, but nobody tested whether the approach is actually right for this codebase.

The Challenger is a separate agent that:
- **Runs blind first:** Sees the document + repo, NOT the operator's intent. Judges purely as engineering. This prevents rationalizing the planner's choices.
- **Checks intent second:** Gets the operator's request (1-2 sentences) and checks for drift. Separate pass, so it doesn't contaminate technical judgment.
- **Gets quality bar checklists, not personas:** Same pattern as code review subagents (Phase 9 finding). The value personas add is in identifying WHAT to check, not in WHO is checking.

Design mirrors the two-stage code review insight: two focused passes (blind technical + intent alignment) beat one combined pass.

## Why Pipeline Split (v2)

Blueprint owned 11 phases — from "I have an idea" through spec, plan, and execution handoff. This created two problems:

1. **Context fragility.** If context was compressed mid-pipeline, phase 8 (plan writing) could lose phase 2's operator answers. Every boundary between phases was a potential data loss point.
2. **No re-entry.** If a session crashed after the spec was written but before the plan, the operator had to re-run blueprint from scratch.

The split moves to artifact-based handoff: each skill reads its input from disk (not conversation memory), writes its output to disk, then offers to invoke the next skill. Every pipeline boundary is a potential session boundary. Users can enter at any point with their own artifact.

The handoff chain: `/blueprint` → brief → `/spec` → plan → `/execute` → code → `/verify` or `/sweep`.

## Key Insight

Knowledge is in the right place at the right time:
- **Planning:** Knowledge lives in the team's questions
- **Execution:** Knowledge lives in the spec's requirements
- **Review:** Knowledge lives in the team's judgment

Trying to put knowledge into the worker's context solves the wrong problem.
