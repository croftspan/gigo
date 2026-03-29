# Domain-Neutral Review Templates — Design Spec

The review pipeline assumes software engineering. Templates reference "race conditions," "file:line," and "code" throughout. GIGO works for any domain — novels, research, game design, Go microservices. The review system must too.

Three changes: (1) neutralize template language, (2) add a `{DOMAIN_CRITERIA}` injection point to all three templates, (3) generate domain-specific criteria from the assembled team.

## Guiding Constraints

- **Neutral defaults are sufficient alone.** Templates must produce useful reviews with `{DOMAIN_CRITERIA}` empty. No "software mode" fallback.
- **One variable, one concept.** `{DOMAIN_CRITERIA}` replaces `{QUALITY_BAR_CHECKLIST}`. Same name in all three templates.
- **Criteria are tier 2.** `.claude/references/review-criteria.md` — zero token cost, read on demand by dispatchers.
- **Generation is mechanical.** Criteria are extracted from approved personas and standards, not invented. No operator approval needed.
- **Backward compatible.** Projects assembled before this feature exist get fallback behavior — blueprint extracts quality bars from CLAUDE.md personas directly.

---

## Part 1: Template Neutralization

### 1A. engineering-reviewer-prompt.md → craft-reviewer-prompt.md

**File:** `skills/verify/references/engineering-reviewer-prompt.md`

Rename file to `craft-reviewer-prompt.md`. This is the heaviest change — the entire review checklist is software-specific.

**Structural change:**

| Current | New |
|---|---|
| Bugs (software-specific list) | Defects (domain-neutral with concrete guidance) |
| Test Quality (4 software bullets) | Removed — testing criteria come from `{DOMAIN_CRITERIA}` |
| Architecture (4 software bullets) | Structure (3 neutral bullets) |
| CLAUDE.md Compliance (3 bullets) | Unchanged |
| *(none)* | Domain-Specific Criteria (`{DOMAIN_CRITERIA}` section) |

**Defects section replacement:**

Current:
```
**Bugs:**
Race conditions, deadlocks, lock ordering, off-by-one, null/undefined handling,
resource leaks, transaction footguns. Focus on production bugs, not style.
```

New:
```
**Defects:**
Look for defects the author likely did not intend. Consider: inconsistencies,
missing edge cases, incorrect assumptions, logic errors, incomplete handling of
failure cases. Focus on correctness and robustness, not style.
```

**Structure section replacement:**

Current:
```
**Architecture:**
- Clean separation of concerns?
- Single responsibility per file/module?
- Easy to understand and modify in 6 months?
- Did this change create or significantly grow large files?
```

New:
```
**Structure:**
- Clean separation of concerns?
- Easy to understand and modify in 6 months?
- Did this change create or significantly grow large units?
```

**New section (after CLAUDE.md Compliance, before Confidence Scoring):**
```
**Domain-Specific Criteria:**

{DOMAIN_CRITERIA}

Check each criterion against the changes under review. If this section is empty,
rely on your own judgment for domain-appropriate quality checks.
```

**Language replacements throughout:**

| Current | New |
|---|---|
| "Engineering Review Prompt Template" | "Craft Review Prompt Template" |
| "code changes for engineering quality" | "changes for craft quality" |
| "whether the code is well-built" | "whether the work is well-built" |
| "production issues or data loss" | "serious issues in practice" |
| "formatting, naming, missing import" | "minor issue with an obvious fix (formatting, naming, small omission)" |
| "file:line" (all occurrences) | "specific location" |
| "File:line" in output format | "Location" |
| "code" in "Read the actual diff before forming opinions" | Unchanged (git diff is always code) |
| "code" in "reading the code" | "reading the work" |
| "Evaluate code quality" | "Evaluate craft quality" |

### 1B. spec-reviewer-prompt.md

**File:** `skills/verify/references/spec-reviewer-prompt.md`

No file rename. Light language changes plus `{DOMAIN_CRITERIA}` injection.

**Language replacements:**

| Current | New |
|---|---|
| "Verify implementation matches specification" | "Verify the work matches its specification" |
| "reviewing whether an implementation matches its specification" | "reviewing whether the work matches its specification" |
| "reading actual code" (all) | "reading the actual work" |
| "the actual code they wrote" | "the actual work they produced" |
| "Read the implementation code and verify" | "Read the actual deliverables and verify" |
| "Verify by reading code, not by trusting report" | "Verify by inspecting the work, not by trusting the report" |
| "after code inspection" | "after inspection" |
| "file:line references" (all) | "specific location references" |

**New section (after "Misunderstandings" check, before "Report"):**
```
**Domain-specific criteria:**

{DOMAIN_CRITERIA}

If criteria are listed above, also check the work against them. If empty,
the checks above are sufficient.
```

### 1C. spec-plan-reviewer-prompt.md

**File:** `skills/verify/references/spec-plan-reviewer-prompt.md`

No file rename. Variable rename, language neutralization, multi-domain examples.

**Variable and heading renames:**

| Current | New |
|---|---|
| `{QUALITY_BAR_CHECKLIST}` | `{DOMAIN_CRITERIA}` |
| "## Quality Bar Checklist" | "## Domain-Specific Criteria" |
| "Quality Bar Results" (output section) | "Domain-Specific Criteria Results" |
| "quality bar" in output instructions | "domain criteria" |

**Language replacements:**

| Current | New |
|---|---|
| "Judge it purely as engineering" | "Judge it purely on technical merit" |
| "The Codebase" (heading) | "The Project" |
| "Read the codebase" | "Read the project" |
| "codebase evidence" (all) | "project evidence" |
| "actual state of the code" | "actual state of the project" |
| "codebase files" | "project files" |
| "Existing patterns in the codebase" | "Existing patterns in the project" |
| "file:line or pattern references" | "specific location or pattern references" |

**Mode-Specific Notes section (lines 183-208) — additional neutralization:**

| Current | New |
|---|---|
| "Whether the architecture fits the codebase" | "Whether the design fits the project" |
| "Whether the code in task steps will actually work against the real codebase" | "Whether the steps will actually work against the real project" |

**Replace "Quality Bar Checklist Construction" section (lines 210-224):**

```
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

---

## Part 2: Dispatcher Updates

### 2A. verify SKILL.md

**File:** `skills/verify/SKILL.md`

**Frontmatter description change:**
```
"Two-stage review: spec compliance (did you build the right thing?) then craft quality (is the work well-built?). Invoked automatically by gigo:execute after each task, or standalone on any work. Use gigo:verify."
```

**Stage 2 rename:** "Engineering Review" → "Craft Review" in all headings and prose.

**Stage 2 description neutralization (lines 44-50):** Replace the software-specific bug/test/architecture lists with:
```
The reviewer checks for defects, structural issues, and project standards.
Domain-specific criteria are injected from `.claude/references/review-criteria.md` when available.
```

**Template reference update (line 42-43):** Change `engineering-reviewer-prompt.md` to `craft-reviewer-prompt.md`.

**Language replacements throughout:**

| Current | New |
|---|---|
| "Two-stage code review pipeline" | "Two-stage review pipeline" |
| "code review" (general) | "review" |
| "engineering quality on code" | "craft quality on work" |
| "file:line references" (all) | "specific location references" |
| "file:line" in output format sections | "specific location" |
| "Is the code production-ready?" | "Is the work well-built?" |
| "code quality independent of spec compliance" | "craft quality independent of spec compliance" |

**New dispatch instruction (add after each stage's template reference):**

```
**{DOMAIN_CRITERIA} injection:** Before dispatching, check for
`.claude/references/review-criteria.md` in the project.
If it exists, read the `## [Section Name] Criteria` section and inject as `{DOMAIN_CRITERIA}`.
If it does not exist, leave `{DOMAIN_CRITERIA}` empty.
```

Section mapping:
- Stage 1 (spec reviewer): extract `## Spec Compliance Criteria`
- Stage 2 (craft reviewer): extract `## Craft Review Criteria`
- Challenger: extract `## Challenger Criteria`

### 2B. blueprint SKILL.md

**File:** `skills/blueprint/SKILL.md`

**Phase 6.5 and 9.5 changes:**
- Replace `{QUALITY_BAR_CHECKLIST}` with `{DOMAIN_CRITERIA}` in all instructions
- Replace "checklistable criteria from CLAUDE.md personas" with:

```
Read `.claude/references/review-criteria.md` and extract the Challenger Criteria
section. If the file does not exist, extract quality bars from CLAUDE.md personas
as a fallback.
```

### 2C. execute SKILL.md

No changes. Execute invokes `gigo:verify` which handles dispatch.

---

## Part 3: Criteria Generation Machinery

### 3A. review-criteria.md File Format

Written to `.claude/references/review-criteria.md` in the target project.

```markdown
# Review Criteria

Domain-specific quality checks for this project's review pipeline.
Generated from team expertise. Regenerate with `gigo:maintain` when expertise changes.

## Spec Compliance Criteria
<!-- Used by spec-reviewer: "did you build the right thing?" -->
- [criteria about completeness, correctness, scope]

## Craft Review Criteria
<!-- Used by craft-reviewer: "is the work well-built?" -->
- [criteria about craft, robustness, structure]

## Challenger Criteria
<!-- Used by spec-plan-reviewer: "will this approach succeed?" -->
- [criteria about feasibility, design soundness]
```

Three sections because the three review stages ask different questions. Some criteria appear in multiple sections — that's correct and expected.

### 3B. gigo:gigo — Step 6.5 (Generate Review Criteria)

**File:** `skills/gigo/SKILL.md`

Add between Step 6's write logic and the closing operator reminder. This is an append after the current final step, not an insert between steps.

```
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

### 3C. output-structure.md Update

**File:** `skills/gigo/references/output-structure.md`

Add to the reference material section:

```
## Review Criteria File

Generated as the FINAL output step (Step 6.5), after all personas and standards are
written. Extracts persona `Quality bar:` lines, standards `Quality Gates` bullets,
and extension `The Standard` sections. Classifies each into three sections: Spec
Compliance Criteria, Craft Review Criteria, Challenger Criteria.

This file is a REFERENCE (tier 2) — zero token cost. The review pipeline reads it
on demand when dispatching reviewers. If personas or standards change, the file must
be regenerated. `gigo:maintain` and `gigo:snap` both check for staleness.
```

### 3D. maintain — Regeneration Trigger

**File:** `skills/maintain/references/targeted-addition.md`

Add after Step 5 (Merge) bullet list:

```
- **Regenerate review criteria.** After writing all changes, regenerate
  `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo
  Step 6.5. If the file doesn't exist, create it. If it does, regenerate from
  scratch (don't append).
```

**File:** `skills/maintain/references/upgrade-checklist.md`

Add to Step 1 feature table:
```
| Review criteria file | `.claude/references/review-criteria.md` exists with domain-specific review criteria | No review-criteria.md, or criteria don't match current personas |
```

Add to Step 4:
```
- Generate `.claude/references/review-criteria.md` using the extraction algorithm from gigo:gigo Step 6.5
```

### 3E. snap-template.md — Audit Step 11

**File:** `skills/gigo/references/snap-template.md`

Add after step 10 in the audit template:

```
**11. Review criteria check.** If `.claude/references/review-criteria.md` exists,
compare its criteria against current personas' quality bars and standards quality
gates. If personas changed but criteria weren't updated, flag: "Review criteria are
stale — offer to regenerate via `gigo:maintain`." If the file doesn't exist and
personas have quality bars, flag: "No review criteria file — review pipeline uses
neutral defaults. Offer to generate via `gigo:maintain`."
```

Also add to GIGO's own `.claude/rules/snap.md`.

Add to upgrade-checklist.md Step 1 table:
```
| Snap review criteria check | Snap audit includes check 11 (review criteria currency) | Snap has 10 or fewer audit checks, or no criteria currency verification |
```

---

## Part 4: Eval Fixtures

### 4A. Rails API fixture

**File:** `evals/fixtures/rails-api/.claude/references/review-criteria.md`

Generate from the existing Rails API fixture personas and standards.

### 4B. Children's novel fixture

**File:** `evals/fixtures/childrens-novel/.claude/references/review-criteria.md`

Generate from the existing children's novel fixture personas and standards.

---

## Conventions

These conventions apply to all template modifications and must be consistent across all three templates:

- **Variable name:** `{DOMAIN_CRITERIA}` — never `{QUALITY_BAR_CHECKLIST}`, `{DOMAIN_CHECKS}`, or any variant
- **Section heading in templates:** `Domain-Specific Criteria` — same heading in all three templates
- **Empty behavior:** When `{DOMAIN_CRITERIA}` is empty, templates say "rely on your own judgment" (craft reviewer) or "checks above are sufficient" (spec reviewer) or "omit the section" (Challenger). No error, no warning.
- **Location references:** "specific location references" — never "file:line" in template prose. Output format uses "Location" as the field name.
- **Stage names:** Stage 1 is "Spec Compliance." Stage 2 is "Craft Review." Not "Quality Review," not "Engineering Review."
- **Criteria file sections:** `## Spec Compliance Criteria`, `## Craft Review Criteria`, `## Challenger Criteria` — exact headings, parsed by dispatchers
- **"work" not "code":** All templates use "work," "deliverables," "changes" instead of "code," "implementation," "codebase" except when referring to git operations (diff, SHA) which are inherently software
- **"project" not "codebase":** The Challenger uses "project" for the thing being reviewed

---

## Known Limitations

- **PR mode does not receive `{DOMAIN_CRITERIA}`.** verify SKILL.md's PR mode invokes `code-review:code-review`, a third-party plugin that has its own review logic. The `{DOMAIN_CRITERIA}` injection only applies to per-task mode (craft-reviewer template) and spec/plan mode (Challenger template). PR mode is a software-specific optimization path — domain-neutral projects won't use it. If `code-review:code-review` adds a criteria injection point in the future, verify can be updated to pass it through.

---

## Verification

After implementation:

1. **Template consistency check:** Grep all three templates for "file:line", "codebase", "code quality", "engineering", "race condition", "deadlock" — none should appear in template prose
2. **Variable consistency check:** Grep all skill files for `QUALITY_BAR_CHECKLIST` — should return zero matches
3. **Dispatcher alignment:** verify SKILL.md Stage 2 description mentions the same section names as the craft-reviewer template
4. **Criteria generation test:** Read the Rails API fixture's CLAUDE.md and standards.md. Verify the generated review-criteria.md contains criteria from each persona's quality bar
5. **Empty criteria test:** Mentally trace a dispatch path with no review-criteria.md present — verify the template produces a coherent review prompt with `{DOMAIN_CRITERIA}` empty
6. **Cross-domain test:** Read the children's novel fixture's generated review-criteria.md — verify no software-specific language leaked in

<!-- approved: spec 2026-03-29T14:00:13 by:Eaven -->
