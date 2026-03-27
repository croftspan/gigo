# Workflow — tq

## The Pipeline

1. **Plan.** Use `gigo:plan` for anything beyond a trivial fix. Spec first, code second.
2. **Execute.** Use `gigo:execute` to run approved plans. Workers run bare — no personas, no rules, just the spec.
3. **Review.** Use `gigo:review` for two-stage review: spec compliance first, engineering quality second. Sequential, not parallel.
4. **Snap.** At session end, use `gigo:snap`. Audit first, save learnings second.

## Persona Calibration

Before applying persona guidance, assess the task:
- **Presentation tasks** — how the answer is shaped matters (architecture, design, code review, quality judgment). Lean into persona fully.
- **Content tasks** — what the answer contains matters (debugging, code lookup, factual recall). Step back — let your training lead, use persona only for framing the response.

When uncertain, default to your training for the core reasoning and apply persona guidance to the output shape.

## Overwatch

Before finalizing any response, step back and verify:
- Did you actually apply the quality bars you cited, or just name-drop them?
- Does your response address what was asked, or did you drift?
- Would removing the persona language change your answer? If not, the persona added nothing.
- Did you check the references you were told to check, or skip them?

When performing overwatch verification on complex responses, read `.claude/references/overwatch.md`.
