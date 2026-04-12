# Boundary-Mismatch Detection Judge

You are scoring whether an integration audit identified specific known bugs in a codebase.

## The Audit Output

{AUDIT_OUTPUT}

## The Defect Manifest

{DEFECT_MANIFEST}

## Your Job

For each of the 6 defects listed in the Defect Manifest, determine whether the audit output identified that specific bug.

**Score YES if:**
- The audit describes the same mismatch (matching on concept, not exact wording)
- The audit identifies the correct files involved
- The audit explains why it would fail at runtime

**Score NO if:**
- The audit does not mention this bug at all
- The audit describes something different in the same files
- The audit mentions the files but misidentifies the actual mismatch

## Output

Respond with ONLY a JSON array. No other text, no markdown fences.

[
  { "defect": "BM-1", "detected": true, "evidence": "The audit noted that the API returns a wrapper object with data and total fields while the hook expects a direct array" },
  { "defect": "BM-2", "detected": false, "evidence": "" },
  { "defect": "BM-3", "detected": true, "evidence": "..." },
  { "defect": "BM-4", "detected": true, "evidence": "..." },
  { "defect": "BM-5", "detected": false, "evidence": "" },
  { "defect": "BM-6", "detected": true, "evidence": "..." }
]
