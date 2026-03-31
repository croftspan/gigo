# Formal Phases (5-10) — Procedural Details

Loaded by blueprint SKILL.md when the design brief is approved and formal documentation begins.

## Phase 5: Write Spec

Read the approved design brief (the plan file from Phase 4.5). Formalize it into a spec — don't recreate the design from conversation memory.

Save to `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md` and commit.

If `.claude/references/language.md` exists with non-English output languages, write the spec in the primary output language (first in the output array). If multi-language output is configured (2+ languages in the output array), include a **Language Requirements** section in the spec specifying which deliverables need which languages and which stay in English (code comments, commit messages, internal docs).

The spec is the source of truth. A bare worker who reads only this spec should be able to build the right thing.

**Include a Conventions section.** During design, the team's personas surface convention decisions — error message formats, output patterns, naming schemes, exit code discipline, durability patterns. These must be explicit in the spec. A bare worker won't have the personas; the spec is all they get.

Example:
```
## Conventions
- Error messages: `tq: cannot add task "<name>": <reason>`
- Output: only the task ID to stdout on success. Errors to stderr.
- Exit codes: return errors from RunE, never call os.Exit in command logic
- Writes: atomic via temp file + fsync + rename
```

## Phase 6: Spec Self-Review

Assume a bare worker follows the spec literally. What goes wrong?

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections? Fix them.
2. **Internal consistency:** Do sections contradict each other?
3. **Scope check:** One spec or multiple sub-projects?
4. **Ambiguity check:** Could any requirement be read two ways? Pick one.
5. **Bare worker test:** Worker gets ONLY this spec — what would they build wrong?
6. **Convention check:** Does the Conventions section capture every decision the personas surfaced?

Fix issues inline.

## Phase 6.5: Independent Spec Challenge

**For large tasks only.** Small/medium tasks use self-review (Phase 6) alone. Operator can always request a Challenger.

Dispatch a subagent using `gigo:verify`'s `references/spec-plan-reviewer-prompt.md`. Do NOT use generic reviewers.

**How to dispatch:** Use `Agent` with `subagent_type: "general-purpose"`. Read the prompt template, fill `{DOCUMENT_TYPE}` = "spec", `{DOCUMENT_CONTENT}` = full spec, `{OPERATOR_INTENT}` = 1-2 sentence summary of what the operator asked for, `{DOMAIN_CRITERIA}` = from `.claude/references/review-criteria.md` Challenger Criteria section (fallback: quality bars from CLAUDE.md).

Present findings to the operator. Verdicts: Proceed / Revise / Rethink.

## Phase 7: User Reviews Spec

> "Spec written and committed to `<path>`. Please review — I'll revise anything before we move to the implementation plan."

Wait for approval. If changes requested, revise and re-run self-review.

**Write approval marker.** Run `git config user.name`, then append:
```
<!-- approved: spec [timestamp] by:[username] -->
```

## Phase 8: Write Implementation Plan

Read the approved design brief and spec. Break the spec into executable tasks.

Save to `docs/gigo/plans/YYYY-MM-DD-<feature-name>.md`.

Plans are always in English. For tasks producing user-facing deliverables, include `**Output languages:** {codes from language.md}`.

Read `references/planning-procedure.md` for the full procedure.
Read `references/example-plan.md` for worked examples.

## Phase 9: Plan Self-Review

1. **Spec coverage:** Can you point to a task for each spec requirement?
2. **Placeholder scan:** No "TBD", "TODO", "implement later", "similar to Task N".
3. **Type consistency:** Do types and names in later tasks match earlier tasks?

Fix issues inline.

## Phase 9.5: Independent Plan Challenge

**For large tasks only.** Same rule as Phase 6.5.

Same dispatch method — use `{DOCUMENT_TYPE}` = "plan", include the approved spec as `{SPEC_CONTENT_IF_PLAN_REVIEW}`.

Present findings to the operator. Same verdicts.

## Phase 10: User Reviews Plan

> "Plan saved to `<path>`. Review the tasks and dependency order — I'll adjust before we start."

Wait for approval.

**Write approval marker:**
```
<!-- approved: plan [timestamp] by:[username] -->
```
