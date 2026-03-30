# Domain-Neutral Review Templates — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-29-domain-neutral-reviews-design.md`

**Goal:** Make the review pipeline domain-neutral with `{DOMAIN_CRITERIA}` injection, and generate domain-specific criteria from assembled teams.

**Architecture:** Three templates get neutralized language + a `{DOMAIN_CRITERIA}` variable. Dispatchers read `.claude/references/review-criteria.md` to fill it. `gigo:gigo` and `gigo:maintain` generate/regenerate the criteria file.

**CRITICAL:** All file paths target `~/projects/gigo/skills/` (source repo). Never write to `~/.claude/plugins/marketplaces/gigo/skills/` (plugin install path).

---

### Task 1: Neutralize engineering-reviewer-prompt.md → craft-reviewer-prompt.md

**blocks:** 4
**blocked-by:** none
**parallelizable:** true

**Files:**
- Rename: `skills/verify/references/engineering-reviewer-prompt.md` → `skills/verify/references/craft-reviewer-prompt.md`

- [ ] **Step 1: Rename the file**

```bash
cd ~/projects/gigo
git mv skills/verify/references/engineering-reviewer-prompt.md skills/verify/references/craft-reviewer-prompt.md
```

- [ ] **Step 2: Rewrite the template**

Replace the full content of `skills/verify/references/craft-reviewer-prompt.md` with:

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add skills/verify/references/craft-reviewer-prompt.md
git commit -m "feat: rename engineering-reviewer to craft-reviewer, neutralize template language

Replace software-specific checklist (race conditions, deadlocks, etc.) with
domain-neutral Defects/Structure/Domain-Specific Criteria sections. Add
{DOMAIN_CRITERIA} injection point."
```

---

### Task 2: Neutralize spec-reviewer-prompt.md

**blocks:** 4
**blocked-by:** none
**parallelizable:** true

**Files:**
- Modify: `skills/verify/references/spec-reviewer-prompt.md`

- [ ] **Step 1: Rewrite the template**

Replace the full content of `skills/verify/references/spec-reviewer-prompt.md` with:

```markdown
# Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify the work matches its specification — nothing more, nothing less.

## Template

~~~
You are reviewing whether the work matches its specification.

## What Was Requested

[FULL TEXT of task requirements from the plan]

## What the Implementer Claims They Built

[From implementer's status report]

## CRITICAL: Do Not Trust the Report

The implementer may be optimistic, incomplete, or wrong. You MUST verify
everything independently by reading the actual work.

**DO NOT:**
- Take their word for what they built
- Trust their claims about completeness
- Accept their interpretation of requirements

**DO:**
- Read the actual work they produced
- Compare actual deliverables to requirements line by line
- Check for missing pieces they claimed to complete
- Look for extra work they didn't mention

## Your Job

Read the deliverables and verify:

**Missing requirements:**
- Did they complete everything that was requested?
- Are there requirements they skipped or missed?
- Did they claim something works but didn't actually deliver it?

**Extra/unneeded work:**
- Did they build things that weren't requested?
- Did they over-engineer or add unnecessary features?
- Did they add "nice to haves" that weren't in spec?

**Misunderstandings:**
- Did they interpret requirements differently than intended?
- Did they solve the wrong problem?
- Did they deliver the right thing but the wrong way?

**Domain-specific criteria:**

{DOMAIN_CRITERIA}

If criteria are listed above, also check the work against them. If empty,
the checks above are sufficient.

**Verify by inspecting the work, not by trusting the report.**

Report:
- ✅ Spec compliant (if everything matches after inspection)
- ❌ Issues found: [list specifically what's missing or extra, with specific location references]

For each issue, include:
- What's missing or wrong, with specific location references
- **Suggested triage:** auto-fix | ask-operator | accept

Triage guidance:
- Missing requirement where the spec is clear about what to build → auto-fix
- Missing requirement where the approach is ambiguous → ask-operator
- Extra/unneeded work that doesn't break anything → accept
- Misunderstanding of requirements → ask-operator
~~~
```

- [ ] **Step 2: Commit**

```bash
git add skills/verify/references/spec-reviewer-prompt.md
git commit -m "feat: neutralize spec-reviewer template, add {DOMAIN_CRITERIA}

Replace code-specific language with domain-neutral equivalents.
Add {DOMAIN_CRITERIA} injection point for project-specific checks."
```

---

### Task 3: Neutralize spec-plan-reviewer-prompt.md

**blocks:** 4
**blocked-by:** none
**parallelizable:** true

**Files:**
- Modify: `skills/verify/references/spec-plan-reviewer-prompt.md`

- [ ] **Step 1: Apply variable and language replacements**

In `skills/verify/references/spec-plan-reviewer-prompt.md`, apply these replacements:

1. Replace `{QUALITY_BAR_CHECKLIST}` with `{DOMAIN_CRITERIA}` (all occurrences)
2. Replace `## Quality Bar Checklist` with `## Domain-Specific Criteria`
3. Replace `Quality Bar Results` with `Domain-Specific Criteria Results` (in output section heading and references)
4. Replace `quality bar` with `domain criteria` (in output instructions, section 5 reference)
5. Replace `Judge it purely as engineering` with `Judge it purely on technical merit`
6. Replace `## The Codebase` with `## The Project`
7. Replace `Read the codebase. Understand the existing patterns, constraints, dependencies,\nand architecture.` with `Read the project. Understand the existing patterns, constraints, dependencies,\nand structure.`
8. Replace `codebase evidence` with `project evidence` (all occurrences — lines 44, 103, 113)
9. Replace `codebase files` with `project files` (line 103)
10. Replace `actual state of the code` with `actual state of the project`
11. Replace `Existing patterns in the codebase` with `Existing patterns in the project`
12. Replace `file:line or pattern references` with `specific location or pattern references` (line 153)
13. Replace `Read actual codebase files` with `Read actual project files` (line 103)
14. In Mode-Specific Notes: replace `Whether the architecture fits the codebase` with `Whether the design fits the project`
15. In Mode-Specific Notes: replace `Whether the code in task steps will actually work against the real codebase` with `Whether the steps will actually work against the real project`

- [ ] **Step 2: Replace the Quality Bar Checklist Construction section**

Replace lines 210-224 (the "Quality Bar Checklist Construction" section and everything after it) with:

```markdown
## Domain-Specific Criteria Construction

The dispatching skill provides criteria extracted from the project's expertise.
These are domain-specific checks, not generic quality assessments.

Example criteria (software):
- "Does this survive a power failure mid-write?"
- "Does every goroutine have a shutdown path?"

Example criteria (fiction):
- "Is every clue planted 2+ chapters before payoff?"
- "Does the chapter end mid-tension, not at a resolution?"

Example criteria (game design):
- "Does the server validate all game state mutations?"
- "Does the reward loop respect the session-length target?"

If no domain-specific criteria are provided, omit the section.
The reviewer's own judgment covers generic quality.
```

- [ ] **Step 3: Commit**

```bash
git add skills/verify/references/spec-plan-reviewer-prompt.md
git commit -m "feat: neutralize Challenger template, rename QUALITY_BAR_CHECKLIST to DOMAIN_CRITERIA

Replace codebase/engineering language with project/technical merit.
Add multi-domain example criteria. Rename variable for consistency."
```

---

### Task 4: Update verify SKILL.md

**blocks:** none
**blocked-by:** 1, 2, 3
**parallelizable:** false

**Files:**
- Modify: `skills/verify/SKILL.md`

- [ ] **Step 1: Update frontmatter description**

Replace the frontmatter description with:
```
"Two-stage review: spec compliance (did you build the right thing?) then craft quality (is the work well-built?). Invoked automatically by gigo:execute after each task, or standalone on any work. Use gigo:verify."
```

- [ ] **Step 2: Neutralize Stage 2 section**

In verify SKILL.md, apply these changes:

1. Line 8: Replace `Two-stage code review pipeline.` with `Two-stage review pipeline.`
2. Line 14: Replace `no point reviewing engineering quality on code that doesn't meet the spec` with `no point reviewing craft quality on work that doesn't meet the spec`
3. Line 36: Replace `## Stage 2: Engineering Review — "Is the code production-ready?"` with `## Stage 2: Craft Review — "Is the work well-built?"`
4. Line 42: Replace `references/engineering-reviewer-prompt.md` with `references/craft-reviewer-prompt.md`
5. Lines 44-50: Replace the software-specific bug/test/architecture summary with:
```
The reviewer checks for defects, structural issues, and project standards.
Domain-specific criteria are injected from `.claude/references/review-criteria.md` when available.
```
6. Replace `file:line references` with `specific location references` (all occurrences)
7. Replace `file:line` with `specific location` in output format sections
8. Replace `code quality independent of spec compliance` with `craft quality independent of spec compliance` (line 5 in template purpose)

- [ ] **Step 3: Add {DOMAIN_CRITERIA} injection instructions**

After the Stage 1 template reference ("Dispatch a subagent using the prompt template in `references/spec-reviewer-prompt.md`."), add:

```markdown
**{DOMAIN_CRITERIA} injection:** Before dispatching, check for `.claude/references/review-criteria.md` in the project. If it exists, read the `## Spec Compliance Criteria` section and inject as `{DOMAIN_CRITERIA}`. If it does not exist, leave `{DOMAIN_CRITERIA}` empty.
```

After the Stage 2 per-task template reference ("Dispatch a subagent using the prompt template in `references/craft-reviewer-prompt.md`."), add:

```markdown
**{DOMAIN_CRITERIA} injection:** Before dispatching, check for `.claude/references/review-criteria.md` in the project. If it exists, read the `## Craft Review Criteria` section and inject as `{DOMAIN_CRITERIA}`. If it does not exist, leave `{DOMAIN_CRITERIA}` empty.
```

After the Challenger template reference ("Dispatch a subagent using the prompt template in `references/spec-plan-reviewer-prompt.md`."), add:

```markdown
**{DOMAIN_CRITERIA} injection:** Before dispatching, check for `.claude/references/review-criteria.md` in the project. If it exists, read the `## Challenger Criteria` section and inject as `{DOMAIN_CRITERIA}`. If it does not exist, leave `{DOMAIN_CRITERIA}` empty.
```

- [ ] **Step 4: Update Pointers section**

In the `## Pointers` section at the bottom of verify SKILL.md, replace:
```
Read `references/engineering-reviewer-prompt.md` for the Stage 2 per-task subagent prompt template.
```
with:
```
Read `references/craft-reviewer-prompt.md` for the Stage 2 per-task subagent prompt template.
```

- [ ] **Step 5: Commit**

```bash
git add skills/verify/SKILL.md
git commit -m "feat: neutralize verify SKILL.md, add DOMAIN_CRITERIA injection instructions

Rename Stage 2 to Craft Review, remove software-specific summaries,
add injection instructions for all three review stages, update Pointers."
```

---

### Task 5: Update blueprint SKILL.md

**blocks:** none
**blocked-by:** 3
**parallelizable:** true (with Task 4)

**Files:**
- Modify: `skills/blueprint/SKILL.md`

- [ ] **Step 1: Update Phase 6.5 dispatch instructions**

Find the Phase 6.5 section that references `{QUALITY_BAR_CHECKLIST}` and replace:

1. All occurrences of `{QUALITY_BAR_CHECKLIST}` → `{DOMAIN_CRITERIA}`
2. Replace the extraction instruction "checklistable criteria from CLAUDE.md personas" (or similar) with:
```
Read `.claude/references/review-criteria.md` and extract the Challenger Criteria
section. If the file does not exist, extract quality bars from CLAUDE.md personas
as a fallback.
```

- [ ] **Step 2: Update Phase 9.5 dispatch instructions**

In the Phase 9.5 section, apply these specific replacements:

1. Replace `{QUALITY_BAR_CHECKLIST}` with `{DOMAIN_CRITERIA}` (if any remaining occurrences)
2. Replace `quality bar checklist` (line 238) with `domain criteria checklist`
3. Replace `Will the code in task steps actually work against the real codebase?` (line 241) with `Will the steps actually work against the real project?`
4. Update the extraction instruction to match Step 1 (read review-criteria.md with fallback)

- [ ] **Step 3: Commit**

```bash
git add skills/blueprint/SKILL.md
git commit -m "feat: rename QUALITY_BAR_CHECKLIST to DOMAIN_CRITERIA in blueprint

Update Phases 6.5 and 9.5 to read review-criteria.md with
fallback to CLAUDE.md persona extraction."
```

---

### Task 6: Add Step 6.5 to gigo SKILL.md

**blocks:** none
**blocked-by:** none
**parallelizable:** true

**Files:**
- Modify: `skills/gigo/SKILL.md`

- [ ] **Step 1: Add Step 6.5 after Step 6**

In `skills/gigo/SKILL.md`, find the line `After writing, remind the operator: "When you need new expertise or want a checkup, I can invoke \`gigo:maintain\` for you."` (inside Step 6). Insert the following BEFORE that reminder line:

```markdown
### Step 6.5: Generate Review Criteria

After writing all files, extract domain-specific review criteria for the review pipeline.

1. Read each persona's `Quality bar:` line from the just-written CLAUDE.md
2. Read bullets under `## Quality Gates` from the just-written `.claude/rules/standards.md`
3. Read bullets under `## The Standard` from any domain extension files
4. Classify each criterion:
   - **Spec Compliance** — about whether the right thing was built (completeness, correctness)
   - **Craft Review** — about whether the work is well-built (craft, robustness, structure)
   - **Challenger** — about whether an approach will succeed (feasibility, design soundness)
   - Some criteria belong in multiple sections
5. Deduplicate within each section
6. Write to `.claude/references/review-criteria.md`

This step is mechanical — no operator approval needed. The criteria are derived
directly from the approved team, not invented.
```

- [ ] **Step 2: Commit**

```bash
git add skills/gigo/SKILL.md
git commit -m "feat: add Step 6.5 — generate review criteria from personas

Extracts quality bars from personas and standards, classifies into
three review-stage sections, writes to .claude/references/review-criteria.md"
```

---

### Task 7: Update output-structure.md

**blocks:** none
**blocked-by:** none
**parallelizable:** true

**Files:**
- Modify: `skills/gigo/references/output-structure.md`

- [ ] **Step 1: Add Review Criteria File section**

At the end of `skills/gigo/references/output-structure.md`, before the final "The Snap" section, add:

```markdown
## Review Criteria File

Generated as the FINAL output step (Step 6.5), after all personas and standards are
written. Extracts persona `Quality bar:` lines, standards `Quality Gates` bullets,
and extension `The Standard` sections. Classifies each into three sections: Spec
Compliance Criteria, Craft Review Criteria, Challenger Criteria.

This file is a REFERENCE (tier 2) — zero token cost. The review pipeline reads it
on demand when dispatching reviewers. If personas or standards change, the file must
be regenerated. `gigo:maintain` and `gigo:snap` both check for staleness.
```

- [ ] **Step 2: Commit**

```bash
git add skills/gigo/references/output-structure.md
git commit -m "docs: add review-criteria.md to output structure reference"
```

---

### Task 8: Add regeneration trigger to maintain

**blocks:** none
**blocked-by:** none
**parallelizable:** true

**Files:**
- Modify: `skills/maintain/references/targeted-addition.md`
- Modify: `skills/maintain/references/restructure.md`
- Modify: `skills/maintain/references/upgrade-checklist.md`

- [ ] **Step 1: Add regeneration step to targeted-addition.md**

In `skills/maintain/references/targeted-addition.md`, find Step 5 (Merge) and add after the last bullet in the list (the line about reading templates from gigo skill's bundled references):

```markdown
- **Regenerate review criteria.** After writing all changes, regenerate `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo Step 6.5. If the file doesn't exist, create it. If it does, regenerate from scratch (don't append).
```

- [ ] **Step 2: Add to upgrade-checklist.md Step 1 table**

In `skills/maintain/references/upgrade-checklist.md`, add this row to the Step 1 feature table (after the "Snap pipeline check" row):

```
| Review criteria file | `.claude/references/review-criteria.md` exists with domain-specific review criteria | No review-criteria.md, or criteria don't match current personas |
| Snap review criteria check | Snap audit includes check 11 (review criteria currency) | Snap has 10 or fewer audit checks, or no criteria currency verification |
```

- [ ] **Step 2.5: Add regeneration step to restructure.md**

In `skills/maintain/references/restructure.md`, find Phase 5 step 9 ("Update CLAUDE.md"). After it, add step 10:

```
10. **Regenerate review criteria** — if personas or standards changed, regenerate `.claude/references/review-criteria.md` using the algorithm from gigo:gigo Step 6.5. If the file doesn't exist and personas have quality bars, create it.
```

- [ ] **Step 3: Add to upgrade-checklist.md Step 4**

In the Step 4 section ("Apply Upgrades"), add this bullet:

```markdown
- Generate `.claude/references/review-criteria.md` using the extraction algorithm from gigo:gigo Step 6.5
```

- [ ] **Step 4: Commit**

```bash
git add skills/maintain/references/targeted-addition.md skills/maintain/references/restructure.md skills/maintain/references/upgrade-checklist.md
git commit -m "feat: add review criteria regeneration to maintain skill

targeted-addition regenerates after merge. restructure regenerates after
cleanup. upgrade-checklist detects missing/stale criteria."
```

---

### Task 9: Add Snap audit step 11

**blocks:** none
**blocked-by:** none
**parallelizable:** true

**Files:**
- Modify: `skills/gigo/references/snap-template.md`
- Modify: `.claude/rules/snap.md` (GIGO's own snap)

- [ ] **Step 1: Add step 11 to snap-template.md**

In `skills/gigo/references/snap-template.md`, find `**10. Pipeline check.**` in the audit template (inside the code fence). After the pipeline check line, add:

```
**11. Review criteria check.** If `.claude/references/review-criteria.md` exists, compare its criteria against current personas' quality bars and standards quality gates. If personas changed but criteria weren't updated, flag: "Review criteria are stale — offer to regenerate via `gigo:maintain`." If the file doesn't exist and personas have quality bars, flag: "No review criteria file — review pipeline uses neutral defaults. Offer to generate via `gigo:maintain`."
```

- [ ] **Step 2: Add step 11 to GIGO's own snap.md**

In `.claude/rules/snap.md`, after the existing step 10 ("Pipeline check"), add:

```
**11. Review criteria check.** If `.claude/references/review-criteria.md` exists, compare its criteria against current personas' quality bars and standards quality gates. If personas changed but criteria weren't updated, flag: "Review criteria are stale — offer to regenerate via `gigo:maintain`." If the file doesn't exist and personas have quality bars, flag: "No review criteria file — review pipeline uses neutral defaults. Offer to generate via `gigo:maintain`."
```

- [ ] **Step 3: Commit**

```bash
git add skills/gigo/references/snap-template.md .claude/rules/snap.md
git commit -m "feat: add Snap audit step 11 — review criteria currency check"
```

---

### Task 10: Generate Rails API fixture review-criteria.md

**blocks:** none
**blocked-by:** 6
**parallelizable:** true (with Task 11)

**Files:**
- Create: `evals/fixtures/rails-api/.claude/references/review-criteria.md`

- [ ] **Step 1: Read Rails API fixture personas and standards**

Read `evals/fixtures/rails-api/CLAUDE.md` and `evals/fixtures/rails-api/.claude/rules/standards.md`. Extract each persona's `Quality bar:` line and each bullet under `## Quality Gates`.

- [ ] **Step 2: Generate review-criteria.md**

Apply the Step 6.5 algorithm: classify each criterion into Spec Compliance, Craft Review, and Challenger sections. Write to `evals/fixtures/rails-api/.claude/references/review-criteria.md`.

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/rails-api/.claude/references/review-criteria.md
git commit -m "feat: generate review-criteria.md for Rails API eval fixture"
```

---

### Task 11: Generate children's novel fixture review-criteria.md

**blocks:** none
**blocked-by:** 6
**parallelizable:** true (with Task 10)

**Files:**
- Create: `evals/fixtures/childrens-novel/.claude/references/review-criteria.md`

- [ ] **Step 1: Read children's novel fixture personas and standards**

Read `evals/fixtures/childrens-novel/CLAUDE.md` and `evals/fixtures/childrens-novel/.claude/rules/standards.md`. Extract each persona's `Quality bar:` line and each bullet under `## Quality Gates`.

- [ ] **Step 2: Generate review-criteria.md**

Apply the Step 6.5 algorithm: classify each criterion into Spec Compliance, Craft Review, and Challenger sections. Write to `evals/fixtures/childrens-novel/.claude/references/review-criteria.md`.

- [ ] **Step 3: Commit**

```bash
git add evals/fixtures/childrens-novel/.claude/references/review-criteria.md
git commit -m "feat: generate review-criteria.md for children's novel eval fixture"
```

---

## Dependency Graph

```
Tasks 1, 2, 3 — template neutralization (parallel, no deps)
    ↓
Task 4 — verify SKILL.md (depends on 1, 2, 3)
Task 5 — blueprint SKILL.md (depends on 3, parallel with 4)

Tasks 6, 7, 8, 9 — generation machinery (parallel, no deps on 1-5)
    ↓
Tasks 10, 11 — eval fixtures (depend on 6, parallel with each other)
```

**Maximum parallelism:** Tasks 1, 2, 3, 6, 7, 8, 9 can all run simultaneously. Then 4+5 and 10+11 in the next waves.

---

## Risks

1. **File rename breaks references.** Task 1 renames `engineering-reviewer-prompt.md` to `craft-reviewer-prompt.md`. Task 4 updates the reference in verify SKILL.md. If Task 4 runs before Task 1 completes, it will reference a file that doesn't exist yet. The dependency graph prevents this.

2. **Incomplete neutralization.** The templates are rewritten in full (Tasks 1, 2) or have exhaustive replacement lists (Task 3). Post-implementation, run the verification grep from the spec to catch any missed instances.

3. **Snap line budget.** Adding step 11 to GIGO's snap.md pushes it near ~57 lines. Acceptable but monitor in next Snap audit.

---

## Done

All 11 tasks complete when:
- All three templates use `{DOMAIN_CRITERIA}` and domain-neutral language
- `QUALITY_BAR_CHECKLIST` returns zero grep matches across the codebase
- verify and blueprint SKILL.md dispatch instructions reference the criteria file
- gigo:gigo has Step 6.5 for criteria generation
- maintain regenerates criteria on persona changes
- Snap checks criteria currency at step 11
- Both eval fixtures have review-criteria.md generated from their personas

<!-- approved: plan 2026-03-29T14:09:44 by:Eaven -->
