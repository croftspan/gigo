# Eval Report Format

## Summary

Win rate: X% assembled, Y% bare, Z% ties
Strongest assembled advantage: [specific area]
Strongest bare advantage: [specific area]

## Per-Prompt Results

| Prompt | Winner | Delta | Why |
|---|---|---|---|
| [prompt description] | Assembled/Bare/Tie | +/- points | [specific reason] |

## Recommendations

Actionable suggestions based on findings:
- "Personas help planning (+6 rubric points on spec quality)"
- "Creative execution degrades with context (-2 on prose quality). Consider adjusting Persona Calibration for creative tasks."
- "Quality bar enforcement is the strongest win (+4). The personas are earning their tokens on structural tasks."

## Methodology

- [N] prompts, [N] runs each, comparative judging
- Judge: [model], strict senior engineer persona
- Labels randomized, full spec context provided
