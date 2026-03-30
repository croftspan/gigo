# Comparative Judging Protocol

The methodology proven across Phases 1-8 of GIGO's eval suite.

## Why Comparative

Per-variant judging (independent judge per variant) produces massive noise — 10-point swings between runs on identical code. Phase 7 showed "war stories beat bare" was largely judge variance.

Comparative judging (same judge, all variants, randomized labels) eliminates this. Scores converge within 1-2 points.

## Setup

1. **Same judge instance** sees all variants for each prompt
2. **Randomized labels** — A/B, not "bare"/"assembled"
3. **Strict senior engineer persona** — lenient judges pass everything
4. **Full spec/context** given to judge for informed evaluation
5. **Multiple runs** — average out noise, flag aberrations

## Scoring Criteria (5 axes)

1. **Quality bar enforcement** — does the response enforce domain standards?
2. **Persona voice** — does expertise shape the response?
3. **Expertise routing** — does it draw on the right knowledge?
4. **Specificity** — concrete vs generic advice?
5. **Pushback quality** — does it resist bad ideas with good reasoning?

## Engineering Review Option (deeper analysis)

For code output, use dimensional letter grades instead of pass/fail:
- Concurrency handling
- Data layer quality
- Maintainability
- Test quality
- API design
- Production readiness

Plus: PR verdict (approve/request changes) and engineer level assessment.

## Detecting Aberrations

A response that scores 0/5 or 5/5 across ALL criteria should trigger review. Hallucinated output can score well on voice and routing while being completely wrong (Phase 2b incident).
