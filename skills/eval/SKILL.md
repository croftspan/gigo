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

## Two Modes

### Pipeline Eval (default)

Run a multi-stage pipeline — architecture → implementation → review — as parallel chains with different context levels. This tests whether assembled context improves the *cumulative* output, not just isolated tasks.

1. **Define the pipeline.** Typically: design/architecture → implementation → code review. Each stage's output feeds the next.
2. **Run parallel chains.** At minimum two chains:
   - Bare: no CLAUDE.md, no `.claude/` rules at any stage
   - Assembled: full project context at every stage
   - Optional third chain: architecture-only (assembled architecture, bare implementation/review) — isolates whether the spec or the personas carry the signal
3. **Comparative judge.** Same judge sees all chains' complete output. Randomized labels (X/Y/Z not bare/assembled). Strict senior engineer persona. Judge scores pipeline consistency — do the stages form a coherent chain, or feel disconnected? See `references/comparative-judging.md`.
4. **Report the delta.** See `references/report-format.md`. Focus on where value enters the pipeline.

**Why pipeline, not isolated prompts:** Phase 9 proved isolated A/B testing misses the chain effect. Assembled context's primary value is pipeline coherence — the architecture informs the implementation which informs the review. Isolated prompts test each stage independently and miss this.

### Isolated Eval (quick check)

For fast checks — did adding a persona help a specific task type? — run single prompts bare vs assembled with comparative judging. Useful for debugging, not for comprehensive assessment.

## Methodology

Read `references/comparative-judging.md` for the full judging protocol. Key points:
- Same judge, all variants — eliminates judge-to-judge variance
- Randomized labels — prevents bias toward "assembled"
- Strict persona — lenient judges pass everything
- Blinding instruction: "You do NOT know which had project context. Judge the work, not the method."
- Multiple runs — single runs have meaningful variance (91%-99% in our tests)
- Pipeline consistency as a scoring criterion — does each stage build on the previous?

## Scope

Start with manual prompt authoring. Automatic prompt generation is a future enhancement.

## Principles

1. **Evidence, not vibes.** If you can't measure it, you can't improve it.
2. **Comparative, not absolute.** "Assembled scored 18/20" means nothing. "Assembled scored 18/20 vs bare's 12/20" means something.
3. **Actionable output.** "Your personas help planning but hurt creative execution" is useful. "Score: 87%" is not.
