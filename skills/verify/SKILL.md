---
name: verify
description: "Two-stage review: spec compliance (did you build the right thing?) then craft quality (is the work well-built?). Invoked automatically by gigo:execute after each task, or standalone on any work. Use gigo:verify."
---

# Verify

Two-stage review pipeline. Each stage finds different things — combining them into one reviewer averages instead of adding up (Phase 8 eval: 11 issues combined vs 10-15 per focused reviewer). Two focused passes always beat one pass trying to hold both lenses.

No character voice. Direct, adversarial, evidence-based.

Read `.claude/references/language.md` if it exists. Present all findings and stage announcements to the operator in the interface language. Reviewer subagents operate in English — their templates and criteria are system-internal. If the file doesn't exist, default to English.

**Announce every phase.** As you work, tell the operator what's happening: "Running Stage 1: Spec compliance review...", "Stage 1 passed. Running Stage 2: Craft quality review...", "Both stages complete. Triaging findings..." Don't work silently.

**Stages are sequential, not parallel.** Run Stage 1 first. If Stage 1 fails (spec not met), skip Stage 2 — no point reviewing craft quality on work that doesn't meet the spec. Only run Stage 2 after Stage 1 passes.

---

## Mission-Control Mode Detection

Run at verify start, before Stage 1.

1. Run mc detection per `skills/spec/references/mc-detection.md`.
2. Attempt ticket ID resolution per `skills/verify/references/mc-verdict-schema.md` § "Ticket ID Resolution":
   - Explicit flag: `--ticket TCK-X-NNN`
   - Most recent `vault/agents/logs/{ticket-id}-execute-pickup.md`
   - Operator-provided
3. If `mc_active` AND ticket ID resolved → enter mc-mode (write verdict files per R5.4).
4. Otherwise → v0.13 mode (human-readable operator summary, no verdict files).

If `mc_active` but ticket ID NOT resolvable, ask the operator before falling back — silent fallback hides mc-mode regressions.

---

## Stage 1: Spec Review — "Did the worker build what the plan said?"

Dispatch a subagent using the prompt template in `references/spec-reviewer-prompt.md`.

**{DOMAIN_CRITERIA} injection:** Before dispatching, check for `.claude/references/review-criteria.md` in the project. If it exists, read the `## Spec Compliance Criteria` section and inject as `{DOMAIN_CRITERIA}`. If it does not exist, leave `{DOMAIN_CRITERIA}` empty.

The reviewer gets:
- The full task requirements from the plan/spec
- The implementer's status report (what they claim they built)
- Access to the actual code

The reviewer does NOT trust the report. They read code and compare to requirements line by line. They check for:
- **Missing requirements** — skipped, missed, or claimed-but-not-implemented
- **Extra/unneeded work** — over-engineering, unrequested features
- **Misunderstandings** — wrong interpretation, wrong problem, right feature wrong way

Output: `✅ Spec compliant` or `❌ Issues found` with specific location references.

**In mc-mode:** after Stage 1 completes, write `vault/agents/reviewer/{ticket-id}-spec-compliance.md` per R5.4.a schema (YAML frontmatter). See `skills/verify/references/mc-verdict-schema.md` for the exact schema.

---

## Stage 2: Craft Review — "Is the work well-built?"

Two modes depending on context:

### Per-task mode (during execution, or standalone commit review)

Dispatch a subagent using the prompt template in `references/craft-reviewer-prompt.md`.

**{DOMAIN_CRITERIA} injection:** Before dispatching, check for `.claude/references/review-criteria.md` in the project. If it exists, read the `## Craft Review Criteria` section and inject as `{DOMAIN_CRITERIA}`. If it does not exist, leave `{DOMAIN_CRITERIA}` empty.

The reviewer checks for defects, structural issues, and project standards.
Domain-specific criteria are injected from `.claude/references/review-criteria.md` when available.

Each issue is confidence-scored 0-100. Only issues scoring 80+ are reported. This filters noise and false positives.

Output: Strengths (with specific location), Issues (Critical/Important/Minor with specific location), Assessment (Ready to proceed / Needs fixes).

### PR mode (at merge time, or standalone PR review)

Invoke `code-review:code-review` on the actual PR. This dispatches 5 focused Sonnet workers covering bugs, CLAUDE.md compliance, git history, prior PR patterns, and code comments.

If `code-review` is not installed, warn and offer inline fallback:

> "Stage 2 craft review works best with the code-review plugin. Install with `claude install @anthropic/code-review`. Running inline craft review instead."

Then fall back to per-task mode using the SHA range of the PR.

**In mc-mode:** after Stage 2 completes (only if Stage 1 passed — stage ordering rule unchanged), write `vault/agents/reviewer/{ticket-id}-craft-quality.md` per R5.4.a schema.

---

## Combined Verdict Synthesis (Mc-Mode Only)

After both stages complete (or Stage 1 failed → Stage 2 skipped), write the canonical combined verdict at `vault/agents/reviewer/{ticket-id}.md` using mc's **plain-header format** per R5.4.b schema. This file is parsed by mc's downstream tools — do NOT drift.

Combined status derivation per R5.7:

| Stage 1 | Stage 2 | Critical in S2 (≥90 confidence)? | Combined |
|---|---|---|---|
| pass | pass | — | `approved` |
| pass | fail | no | `approved_with_notes` |
| pass | fail | yes | `escalate` |
| fail | skipped | — | `escalate` (reason: "spec compliance failed — craft review skipped per pipeline policy") |

See `skills/verify/references/mc-verdict-schema.md` for:
- The exact plain-header format
- The Stage-verdicts extension section (non-breaking gigo addition)
- Re-verification history-append pattern
- Validation step (run `mc-ticket-stats {ticket-id}` to confirm parsability)

**Operator-facing summary in mc-mode** (appended to existing v0.13 operator-readable summary):

> "Verdicts written to `vault/agents/reviewer/{ticket-id}.md` (combined), `{ticket-id}-spec-compliance.md`, `{ticket-id}-craft-quality.md`. Mission-control will pick up state transitions per its own rules. Suggested ticket status: [done | escalate]."

**Non-Mutation Rule:** verify NEVER writes to `vault/tickets/*.md` frontmatter. mc transitions ticket state; gigo provides verdicts.

---

## Spec/Plan Review Mode — The Challenger

A fundamentally different review mode. Not compliance checking — adversarial validation. Triggered when reviewing a spec or plan document rather than code.

**When this mode activates:**
- Called by `gigo:spec` at Phase 6.5 (spec review) or Phase 9.5 (plan review)
- Called standalone on any spec/plan document in `docs/gigo/specs/` or `docs/gigo/plans/`

**How it works:** Dispatch a subagent using the prompt template in `references/spec-plan-reviewer-prompt.md`.

**{DOMAIN_CRITERIA} injection:** Before dispatching, check for `.claude/references/review-criteria.md` in the project. If it exists, read the `## Challenger Criteria` section and inject as `{DOMAIN_CRITERIA}`. If it does not exist, leave `{DOMAIN_CRITERIA}` empty.

The reviewer runs two passes:

1. **Pass 1 (blind):** Reviewer sees the document + repo only. No knowledge of operator intent. Judges feasibility, alternatives, failure modes against the actual codebase. This prevents rationalizing the planner's choices.
2. **Pass 2 (intent):** Reviewer then gets the operator's original request (1-2 sentences). Checks if the document solves the stated problem or drifted.

**The reviewer checks:**
- **Feasibility** — will this work in this codebase, given its actual patterns and constraints?
- **Alternatives** — is there a fundamentally better approach? (not style preferences)
- **Failure modes** — what will break during execution or in production?
- **Honest assessment** — confidence 1-5, where most specs score 3-4 and 5 is rare
- **Intent alignment** — does this solve the right problem? (pass 2 only)

**Verdicts:** Proceed (minor issues) / Revise (specific fixes needed) / Rethink (fundamental problems, reconsider approach).

**After the review:** Present findings to the operator alongside the spec/plan. Operator decides whether to revise, override, or proceed. If Rethink, blueprint can loop back to Phase 3 (approaches).

This mode does NOT use the triage framework (auto-fix/ask-operator/accept) — all findings go directly to the operator. There's no worker to auto-fix a spec.

---

## Standalone Mode

When invoked without a plan context (not called from gigo:execute):

1. **If reviewing a spec or plan** (file in `docs/gigo/specs/` or `docs/gigo/plans/`):
   - Run Spec/Plan Review Mode (The Challenger)
   - Ask for the operator's original intent to enable Pass 2

2. **If reviewing code with a plan/spec available:**
   - Ask: "Review against spec, or just craft quality?"
   - If against spec: run both review stages
   - If craft only: skip to Stage 2

3. **If reviewing code with no plan:**
   - Skip Stage 1 entirely
   - Run Stage 2 only

4. **If reviewing a PR:**
   - Invoke `code-review:code-review` (PR mode)

5. **If reviewing commits without a PR:**
   - Run SHA-range craft review (per-task mode)

---

## Triage

After both stages complete, categorize each finding before returning feedback.

| Category | Criteria | Action |
|---|---|---|
| **auto-fix** | Minor, obvious fix, no architectural implications | Return to worker: "Fix these, no discussion needed." |
| **ask-operator** | Architectural, scope, ambiguous, or interface-changing | Surface to operator. Task stays blocked until operator decides. |
| **accept** | Informational, future consideration, strength | Record in addendum, don't send as fix items |

**Default rules:**
- Spec review findings → ask-operator (unless fix is unambiguous)
- Craft review findings → auto-fix (unless interface-changing or architectural)
- Confidence informs but doesn't determine category — a high-confidence architectural issue is ask-operator, not auto-fix. A high-confidence missing import is auto-fix regardless of score.
- Critical issues (confidence 90+) → never accept. Must be auto-fix or ask-operator.
- When in doubt → ask-operator. False escalation costs a question. False auto-fix can cost a wrong decision.

**Output the categorized summary:**

### Auto-Fix (worker handles)
[numbered list with specific location references]

### Ask Operator
[numbered list — these block the task]

### Accept (noted, no action)
[numbered list — goes into the addendum]

**In execution context** (called from gigo:execute): send auto-fix to worker, surface ask-operator to operator and wait, pass accept to lead for the addendum.

**In standalone mode:** present all three categories to the operator.

---

## Send-Back-and-Fix Loop

When issues are found:

1. **Triage first.** Categorize all findings (see Triage section above).
2. **Auto-fix items** → return to the caller with "Fix these, no discussion needed."
3. **Ask-operator items** → surface to the operator. Task stays blocked until operator decides. Worker can move to independent tasks.
4. **Accept items** → pass to the lead for the "What Was Built" addendum. No fix needed.
5. After fixes are applied, re-review the fix commits.
6. Repeat until both stages pass with no auto-fix or ask-operator items remaining.

During execution, gigo:execute handles the routing. In standalone mode, present all categories to the operator and wait for direction.

---

## Verification Before Completion

Evidence before claims. Baked into both stages, not a separate step.

- No "tests pass" without running them
- No "spec compliant" without reading the code
- No "ready to merge" without checking the diff
- Every claim backed by specific location reference

If a reviewer can't verify something (e.g., no test suite exists), they say so explicitly rather than assuming it works.

---

## Pointers

Read `references/spec-reviewer-prompt.md` for the Stage 1 subagent prompt template.

Read `references/craft-reviewer-prompt.md` for the Stage 2 per-task subagent prompt template.

Read `references/spec-plan-reviewer-prompt.md` for the Challenger (spec/plan adversarial review) prompt template.
