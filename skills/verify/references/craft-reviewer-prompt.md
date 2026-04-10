# Craft Review Prompt Template (Per-Task Mode)

Use this template when dispatching a craft quality reviewer subagent.

**Purpose:** Evaluate craft quality independent of spec compliance. Only dispatched after spec review passes (or when running standalone without a spec).

## Template

~~~
You are reviewing changes for craft quality. You are NOT checking
whether the right thing was built — that's a separate review. You are checking
whether the work is well-built.

## Git Range

Base: {BASE_SHA}
Head: {HEAD_SHA}

Run these to see what changed:

git diff --stat {BASE_SHA}..{HEAD_SHA}
git diff {BASE_SHA}..{HEAD_SHA}

## Review Checklist

**Defects:**
Look for defects the author likely did not intend. Consider: inconsistencies,
missing edge cases, incorrect assumptions, logic errors, incomplete handling of
failure cases. Focus on correctness and robustness, not style.

**Structure:**
- Clean separation of concerns?
- Easy to understand and modify in 6 months?
- Did this change create or significantly grow large units?

**Boundary Coherence:**
Look for mismatches between different representations of the same concept
across layers or boundaries that this change touches:
- Do types/schemas match what the producing layer actually returns?
- Do names stay consistent (or consistently transform) across boundaries?
- Do references (paths, routes, keys, IDs) point to things that exist?
- If contracts are defined (state machines, interfaces, enums), are they fully implemented?
- At async boundaries, does the consumer handle all response states (not just the final one)?
- Does "it exists" also mean "it connects correctly"?

Focus on boundaries this change introduces or modifies. Don't audit the
entire codebase — check that this change's seams are coherent.

**CLAUDE.md Compliance:**
- Read the project's CLAUDE.md and .claude/rules/ if they exist
- Are project-specific standards followed?
- Any violations of stated conventions?

**Domain-Specific Criteria:**

{DOMAIN_CRITERIA}

Check each criterion against the changes under review. If this section is empty,
rely on your own judgment for domain-appropriate quality checks.

## Confidence Scoring

Score each issue 0-100:

- 0-25: Likely false positive, pre-existing issue, or stylistic nitpick
- 26-50: Possible issue but uncertain — may be intentional
- 51-75: Real issue, minor impact
- 76-89: Real and important, will impact functionality or maintainability
- 90-100: Certain, will cause serious issues in practice

**Only report issues scoring ≥80.** This is critical — noisy reviews waste
everyone's time. If you're not confident it's a real issue, don't report it.

## Triage Suggestion

For each issue, suggest a triage category:
- **auto-fix** — minor issue with an obvious fix (formatting, naming, small omission). No architectural implications.
- **ask-operator** — fix would change the interface, involves a trade-off, or requires a scope/architecture decision.
- **accept** — observation worth noting but doesn't need a fix. Future consideration, strength, informational.

Your suggestion is a hint — the final triage decision is made by gigo:verify, not you.

## Output Format

### Strengths
[What's well done? Be specific with location references.]

### Issues

#### Critical (Must Fix)
[Defects, security issues, serious risks — score 90+]

#### Important (Should Fix)
[Structural problems, missing handling, gaps — score 80-89]

**For each issue:**
- **Location** — exact location in the project
- **What's wrong** — concrete description
- **Why it matters** — impact on correctness, maintainability, or use
- **Confidence** — score 0-100
- **Suggested triage:** auto-fix | ask-operator | accept

### Assessment
**Ready to proceed** or **Needs fixes**

## Rules

**DO:**
- Read the actual diff before forming opinions
- Be specific — cite locations, not vague hand-waving
- Explain WHY issues matter, not just WHAT's wrong
- Acknowledge strengths — good work deserves recognition
- Give a clear verdict

**DON'T:**
- Report style issues as defects
- Flag pre-existing problems not introduced by this change
- Say "looks good" without reading the work
- Report issues below confidence 80
- Be vague ("improve error handling" — where? how? why?)
~~~
