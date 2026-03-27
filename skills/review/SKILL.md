---
name: review
description: "Two-stage code review: spec compliance (did you build the right thing?) then engineering quality (is the code good?). Invoked automatically by gigo:execute after each task, or standalone on any code. Use gigo:review or /review."
---

# Review

Two-stage code review pipeline. Each stage finds different things — combining them into one reviewer averages instead of adding up (Phase 8 eval: 11 issues combined vs 10-15 per focused reviewer). Two focused passes always beat one pass trying to hold both lenses.

No character voice. Direct, adversarial, evidence-based.

---

## Stage 1: Spec Review — "Did the worker build what the plan said?"

Dispatch a subagent using the prompt template in `references/spec-reviewer-prompt.md`.

The reviewer gets:
- The full task requirements from the plan/spec
- The implementer's status report (what they claim they built)
- Access to the actual code

The reviewer does NOT trust the report. They read code and compare to requirements line by line. They check for:
- **Missing requirements** — skipped, missed, or claimed-but-not-implemented
- **Extra/unneeded work** — over-engineering, unrequested features
- **Misunderstandings** — wrong interpretation, wrong problem, right feature wrong way

Output: `✅ Spec compliant` or `❌ Issues found` with file:line references.

---

## Stage 2: Engineering Review — "Is the code production-ready?"

Two modes depending on context:

### Per-task mode (during execution, or standalone commit review)

Dispatch a subagent using the prompt template in `references/engineering-reviewer-prompt.md`.

The reviewer operates on a git SHA range and checks:
- **Bugs:** Race conditions, deadlocks, lock ordering, off-by-one, null handling, resource leaks. Production bugs, not style.
- **Test quality:** Tests verify behavior not mocks? Edge cases? Independent tests?
- **Architecture:** Clean separation? Single responsibility? Easy to modify in 6 months?
- **CLAUDE.md compliance:** Project-specific standards followed?

Each issue is confidence-scored 0-100. Only issues scoring 80+ are reported. This filters noise and false positives.

Output: Strengths (with file:line), Issues (Critical/Important/Minor with file:line), Assessment (Ready to proceed / Needs fixes).

### PR mode (at merge time, or standalone PR review)

Invoke `code-review:code-review` on the actual PR. This dispatches 5 focused Sonnet workers covering bugs, CLAUDE.md compliance, git history, prior PR patterns, and code comments.

If `code-review` is not installed, warn and offer inline fallback:

> "Stage 2 engineering review works best with the code-review plugin. Install with `claude install @anthropic/code-review`. Running inline engineering review instead."

Then fall back to per-task mode using the SHA range of the PR.

---

## Standalone Mode

When invoked without a plan context (not called from gigo:execute):

1. **If plan/spec exists** in `docs/gigo/specs/` or `docs/gigo/plans/`:
   - Ask: "Review against spec, or just engineering quality?"
   - If against spec: run both stages
   - If engineering only: skip to Stage 2

2. **If no plan exists:**
   - Skip Stage 1 entirely
   - Run Stage 2 only

3. **If reviewing a PR:**
   - Invoke `code-review:code-review` (PR mode)

4. **If reviewing commits without a PR:**
   - Run SHA-range engineering review (per-task mode)

---

## Send-Back-and-Fix Loop

When issues are found:
1. Return feedback to the caller (gigo:execute or the operator)
2. Issues get fixed
3. Re-review the fix commits
4. Repeat until both stages pass

During execution, this loop is automatic — gigo:execute handles it. In standalone mode, present findings to the operator and wait for them to fix or push back.

---

## Verification Before Completion

Evidence before claims. Baked into both stages, not a separate step.

- No "tests pass" without running them
- No "spec compliant" without reading the code
- No "ready to merge" without checking the diff
- Every claim backed by file:line reference

If a reviewer can't verify something (e.g., no test suite exists), they say so explicitly rather than assuming it works.

---

## Pointers

Read `references/spec-reviewer-prompt.md` for the Stage 1 subagent prompt template.

Read `references/engineering-reviewer-prompt.md` for the Stage 2 per-task subagent prompt template.
