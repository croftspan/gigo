# Phase Selection Matrix Judge

You are scoring whether a response correctly identifies downstream effects of adding a new persona to a GIGO-assembled project.

## The Response

{RESPONSE}

## Expected Downstream Effects

5 effects that should be identified:

1. **review-criteria.md regeneration** — New quality bars about auth/SQL/input validation should become review criteria
2. **Rules line budget check** — Adding persona content may push rules files toward the ~60-line cap
3. **Snap audit updates** — Coverage check now includes security domain, calibration check covers one more persona
4. **New reference file** — Deep security knowledge (patterns, checklists) should go in a reference file, not rules
5. **Workflow "When to Go Deeper" pointer** — May need a pointer for security-related reviews

## Your Job

For each of the 5 expected effects, determine whether the response identifies it.

**Score YES if:**
- The response describes the same downstream effect (matching on concept, not exact wording)
- The response identifies the correct file or area that needs updating

**Score NO if:**
- The response does not mention this effect
- The response mentions the file but for a different reason

## Output

Respond with ONLY a JSON array. No other text, no markdown fences.

[
  { "effect": "review-criteria regeneration", "identified": true, "evidence": "Response mentions that review-criteria.md needs updating with the new security quality bars" },
  { "effect": "rules line budget", "identified": false, "evidence": "" },
  { "effect": "snap audit updates", "identified": true, "evidence": "..." },
  { "effect": "new reference file", "identified": true, "evidence": "..." },
  { "effect": "workflow pointer", "identified": false, "evidence": "" }
]
