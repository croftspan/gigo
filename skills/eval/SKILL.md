---
name: eval
description: "Test whether your assembled context actually improves AI output. Runs tasks bare vs assembled, uses comparative judging, reports the delta. Use gigo:eval when you want to prove your setup works or debug why it doesn't."
---

# Eval

Test whether assembled context actually improves output. Not part of the automatic pipeline — this is an opt-in diagnostic tool for teams that want evidence, not vibes.

## When to Use

- After running `gigo:gigo` — does the assembled context actually help?
- When output quality seems inconsistent — is context helping or hurting?
- When adding new personas — did they improve planning?
- When debugging — is the Persona Calibration heuristic working?

## The Process

1. **Get task prompts.** Operator provides representative task prompts, or eval suggests them based on the project's CLAUDE.md and domain.

2. **Run bare vs assembled.** Execute each prompt twice:
   - Bare: no CLAUDE.md, no `.claude/` rules loaded
   - Assembled: full project context loaded

3. **Comparative judge.** Same judge sees both outputs side by side, randomized labels (A/B not bare/assembled), strict senior engineer persona. See `references/comparative-judging.md`.

4. **Report the delta.** See `references/report-format.md` for output structure. Actionable, not academic.

## Methodology

Read `references/comparative-judging.md` for the full judging protocol. Key points:
- Same judge, all variants — eliminates judge-to-judge variance
- Randomized labels — prevents bias toward "assembled"
- Strict persona — lenient judges pass everything
- Multiple runs — single runs have meaningful variance (91%-99% in our tests)

## Scope

Start with manual prompt authoring. Automatic prompt generation is a future enhancement.

## Principles

1. **Evidence, not vibes.** If you can't measure it, you can't improve it.
2. **Comparative, not absolute.** "Assembled scored 18/20" means nothing. "Assembled scored 18/20 vs bare's 12/20" means something.
3. **Actionable output.** "Your personas help planning but hurt creative execution" is useful. "Score: 87%" is not.
