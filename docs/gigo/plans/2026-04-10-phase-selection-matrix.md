# Phase Selection Matrix Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-10-phase-selection-matrix-design.md`

**Goal:** Add a change-impact matrix reference file consulted by `gigo:maintain` proactively and by `gigo:snap` reactively, so ripple effects from persona/rule/reference changes are surfaced instead of falling through the cracks.

**Architecture:** Matrix file lives at `skills/maintain/references/change-impact-matrix.md` — colocated with its primary consumer. Maintain's `targeted-addition.md` Step 5 consults it as a sibling reference with no fallback. Snap's `SKILL.md` gains a new pre-audit step that runs `git status --short`, classifies each changed file as one of 10 change types (CT-1..CT-10), looks them up in the matrix, and flags potential unhandled ripples.

**Tech Stack:** Markdown reference files, git CLI for snap's reverse-lookup, Claude-LLM path resolution inside the plugin's `skills/` tree.

---

## File Structure Map

| File | Status | Responsibility |
|---|---|---|
| `skills/maintain/references/change-impact-matrix.md` | NEW | The matrix itself: 10 change types × 5 downstream columns, cell-value legend, auto-run policy, snap read-back protocol, v1 scope notes |
| `skills/maintain/references/targeted-addition.md` | MODIFY (Step 5, lines 43–57) | Refactor Step 5 to consult the matrix; remove hardcoded ripple list; preserve persona-specific guidance (Overwatch threshold, persona style, alignment/knowledge split) |
| `skills/snap/SKILL.md` | MODIFY (24 → ~45 lines) | Insert new step 3 "Change impact pre-audit" between current steps 2 and 3; renumber existing 3 and 4 to 4 and 5 |
| `CHANGELOG.md` | MODIFY ([Unreleased] section) | Document the new matrix, maintain integration, snap pre-audit, and deferred v2 work |
| `briefs/02-phase-selection-matrix.md` | MODIFY (append) | Append superseded note pointing to the approved design brief and spec |

---

## Dependency Graph

```
Task 1 (write matrix)
  ├── Task 2 (refactor targeted-addition Step 5)   [parallelizable with Task 3]
  └── Task 3 (add snap pre-audit step)              [parallelizable with Task 2]
        └── Task 4 (static verification of matrix consumption)
              └── Task 5 (matrix-missing degradation test, non-destructive)
                    ├── Task 6 (CHANGELOG entry)    [parallelizable with Task 7]
                    ├── Task 7 (brief supersession) [parallelizable with Task 6]
                    └── Task 8 (final verification pass)

After Task 8: operator runs the post-execution checklist (Operator Checks A–F)
to validate runtime behavior that requires skill invocation.
```

---

## Task 1: Write the Change Impact Matrix

**blocks:** 2, 3
**blocked-by:** —
**parallelizable:** false

**Files:**
- Create: `skills/maintain/references/change-impact-matrix.md`

- [x] **Step 1.1: Create the matrix file**

Write this exact content to `skills/maintain/references/change-impact-matrix.md`:

````markdown
# Change Impact Matrix

Decision aid for `gigo:maintain` and `gigo:snap`. Maps change types to downstream files that may need updating. **Not a mandate** — maintain reports ripples, operator decides what to act on.

## How to Read This

Each row is a change type (what the operator did or is about to do). Columns are downstream files. Cell values:

- **regenerate** — mechanical, deterministic. Maintain auto-runs without operator confirmation.
- **update (judgment)** — needs human decision. Maintain reports, operator approves.
- **verify** — may or may not need change depending on content. Maintain reports as a question.
- **check pointer** — rules files may have "When to Go Deeper" pointers to update.
- **—** — no expected effect.

## The Matrix

| Change Type | CLAUDE.md | rules/ | references/ | review-criteria.md | Snap audit checks |
|---|---|---|---|---|---|
| **CT-1: Persona added** | update (team section) | check line budget | verify authorities.md if new research | regenerate | coverage + calibration |
| **CT-2: Persona modified** (quality bar or approach) | update entry | — | verify if authority research changed | regenerate if quality bars changed | calibration |
| **CT-3: Persona removed** | remove entry | check for orphaned rule sections | archive authority notes | regenerate | calibration + coverage |
| **CT-4: Rule added** (new file in `.claude/rules/`) | — | direct edit; check overlap with existing | — | — | line + derivability + overlap |
| **CT-5: Rule modified** | — | direct edit; re-check line budget | — | verify if it changed a quality gate | line + derivability |
| **CT-6: Rule removed** | remove file reference if any | check for orphaned "When to Go Deeper" pointers | — | — | overlap + coverage |
| **CT-7: Reference added** | — | add "When to Go Deeper" pointer in relevant rules file | direct write | — | — |
| **CT-8: Reference removed** | — | remove orphaned "When to Go Deeper" pointers | — | — | — |
| **CT-9: Extension file added/modified** (domain extension in `.claude/rules/`) | — | follow `extension-file-guide.md` format | — | regenerate if "The Standard" section changed | line + derivability |
| **CT-10: Pipeline change** (`workflow.md` structural edit) | — | update workflow.md | verify `pipeline-architecture.md` still describes the shape | — | pipeline |

## Auto-Run vs Report Policy

**Auto-run** (no operator confirmation — mechanical and deterministic):

- `regenerate` of `review-criteria.md` using the algorithm from `gigo:gigo` Step 6.5 (purely mechanical)
- Line count checks (numeric thresholds)
- "When to Go Deeper" pointer additions when a reference is added and the target rules file exists

**Report** (needs operator decision):

- Any cell marked **update (judgment)** — includes CLAUDE.md entries, anything requiring research or phrasing decisions
- Any cell marked **verify** — maintain says "this may need updating, please look"
- Orphaned pointer cleanup (risk of unintended removal)

**Principle:** If the action is purely mechanical and the reference implementation exists, auto-run. If it requires judgment, phrasing, or research, report and let the operator decide.

## Snap Read-Back Protocol

Snap consults this matrix at session end for uncommitted changes only. Procedure:

1. Run `git status --short` to list uncommitted (working tree + staged) changes. **Baseline is uncommitted delta only** — multi-commit sessions are not audited. Operators should snap before committing for best coverage.
2. For each entry matching `CLAUDE.md`, `.claude/rules/*.md`, or `.claude/references/*.md`, classify by change type:
    - `A` (added) → CT-4 (rule), CT-7 (reference), or CT-9 (extension if the file contains a `## The Standard` section)
    - `D` (deleted) → CT-6 (rule) or CT-8 (reference)
    - `M` on a rules file → CT-5; on `workflow.md` with phase-structure edits → CT-10
    - `M` on `CLAUDE.md` → run `git diff CLAUDE.md`; new persona header → CT-1; removed persona header → CT-3; edit to existing entry → CT-2
3. Look up each change type's row in the matrix. Any downstream cells with non-empty values become "potential ripples."
4. For each potential ripple, check whether the downstream file also appears in `git status --short`. If yes, the operator has already touched it — no flag. If no, flag as "potential ripple — verify."
5. Report findings at the top of snap's audit as a `## Change Impact (uncommitted delta only)` section, before the 14-point protocol results.

No new state tracking — git is the source of truth for "what changed." No timestamp files, no snap markers.

## Error Handling

- **Matrix file missing (maintain):** hard error. This file is a required dependency of `targeted-addition.md` Step 5. No silent fallback.
- **Matrix file missing (snap):** soft degradation. Snap logs a warning ("matrix not found, skipping change impact pre-audit") and continues with the 14-point protocol.
- **Git command fails** (not a git repo, pre-initial-commit, detached HEAD without baseline): snap skips pre-audit with a warning, continues 14-point protocol.
- **Unknown change type** (path matches but no classification rule applies): skip that file with a warning, continue with remaining files.

## Out of Scope for v1

- **Semantic drift detection.** "Persona quality bar mentions accessibility but review-criteria.md has no accessibility criteria" requires LLM-based content comparison. v1 is syntactic only — it maps change types to file paths, not content to content. Deferred to v2, possibly via the Challenger pattern.
- **Multi-commit session baseline.** The uncommitted-delta scope is a deliberate tradeoff for statelessness. A "since last snap" baseline would require timestamp tracking.
- **Cross-project coordination.** Matrix covers intra-project ripples only.
- **Automated execution of judgment-required ripples.** Matrix reports them; maintain doesn't guess the right edit.
- **Consolidation with `restructure.md` and `upgrade-checklist.md`.** Both currently contain their own independent `review-criteria.md` regeneration calls. v1 leaves them as-is; v2 should refactor both to consult this matrix.
````

- [x] **Step 1.2: Verify line count**

Run: `wc -l /Users/eaven/projects/gigo/skills/maintain/references/change-impact-matrix.md`
Expected: under 120 lines.

- [x] **Step 1.3: Verify matrix table parses**

Run: `grep -c "^| \*\*CT-" /Users/eaven/projects/gigo/skills/maintain/references/change-impact-matrix.md`
Expected: 10 (one row per change type).

- [x] **Step 1.4: Commit**

```bash
git add skills/maintain/references/change-impact-matrix.md
git commit -m "feat: add change impact matrix reference for maintain and snap"
```

#### What Was Built
- **Deviations:** None. Matrix file written verbatim from plan, 75 lines (well under 120-line cap), exactly 10 CT rows.
- **Review changes:** None. Review pass was clean — all 8 spec requirements satisfied on first write.
- **Notes for downstream:** Matrix sits at `skills/maintain/references/change-impact-matrix.md`. Tasks 2 and 3 reference it via the sibling path `change-impact-matrix.md` (from targeted-addition) and the cross-skill path `maintain/references/change-impact-matrix.md` (from snap). Commit: `4737a64`.

---

## Task 2: Refactor targeted-addition.md Step 5

**blocks:** 4
**blocked-by:** 1
**parallelizable:** true (with Task 3)

**Files:**
- Modify: `skills/maintain/references/targeted-addition.md` (Step 5, lines 43–57)

- [x] **Step 2.1: Replace Step 5 with matrix-consulting version**

Use Edit to replace the current Step 5 block. The `old_string` is:

```markdown
## Step 5: Merge

Write the changes. This is a merge, not a rewrite:
- Add new persona(s) to `CLAUDE.md`
- Add/update extension files in `.claude/rules/`
- Add new reference files to `.claude/references/`
- **Check Overwatch threshold.** After adding, count domain personas in CLAUDE.md (don't count The Overwatch). If now at 3+ and The Overwatch isn't present, add The Overwatch persona to CLAUDE.md. Read `gigo/references/persona-template.md` → "The Overwatch" for the template. The Overwatch section in workflow.md and overwatch.md reference should already exist from initial assembly — verify they're present.
- **Before adding new rules, check line budgets.** If adding a persona pushes `CLAUDE.md` too long, tighten existing entries first. If a rules file is approaching ~60 lines, move content to references.

When creating personas or extensions, read the templates from the gigo skill's bundled `references/` directory.

**Match persona style.** Read `.claude/references/persona-style.md` (or default to Lenses). New personas must match the project's chosen style — Characters get evocative names and may include Personality in the lean tier; Lenses get functional names and Personality goes only in the rich tier reference file.

When designing the new persona, separate alignment signal from knowledge signal. The lean tier entry in CLAUDE.md should contain only alignment content — quality bars, approach, constraints, what to push back on. Domain-specific knowledge (factual details, implementation patterns, technical specifics) belongs in `.claude/references/personas/` or a reference file, loaded on demand. See `gigo/references/persona-template.md` for the "Alignment vs Knowledge Signal" section.
- **Regenerate review criteria.** After writing all changes, regenerate `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo Step 6.5. If the file doesn't exist, create it. If it does, regenerate from scratch (don't append). This includes boundary coherence criteria — re-detect boundary types against the current project state.
```

The `new_string` is:

```markdown
## Step 5: Merge

Write the changes. This is a merge, not a rewrite. Start by consulting `change-impact-matrix.md` (sibling reference) to identify which downstream files the change affects. **The matrix is required** — if it's missing, error loudly and stop. Do not fall back to a hardcoded ripple list.

For a persona addition (the common case this procedure handles), the matrix row **CT-1: Persona added** specifies:

- **CLAUDE.md:** update (judgment) — add the new persona entry
- **rules/:** check line budget before writing
- **references/:** verify `authorities.md` only if new research was used
- **review-criteria.md:** regenerate mechanically (auto-run, no operator confirmation)
- **Snap audit checks affected:** coverage + calibration

Execute the auto-run items. Report the judgment items to the operator in your proposal before writing.

Then perform the persona-specific work that the matrix doesn't cover:

- Add new persona(s) to `CLAUDE.md`
- Add/update extension files in `.claude/rules/`
- Add new reference files to `.claude/references/`
- **Check Overwatch threshold.** After adding, count domain personas in CLAUDE.md (don't count The Overwatch). If now at 3+ and The Overwatch isn't present, add The Overwatch persona to CLAUDE.md. Read `gigo/references/persona-template.md` → "The Overwatch" for the template. The Overwatch section in workflow.md and overwatch.md reference should already exist from initial assembly — verify they're present.
- **Before adding new rules, check line budgets.** If adding a persona pushes `CLAUDE.md` too long, tighten existing entries first. If a rules file is approaching ~60 lines, move content to references.

When creating personas or extensions, read the templates from the gigo skill's bundled `references/` directory.

**Match persona style.** Read `.claude/references/persona-style.md` (or default to Lenses). New personas must match the project's chosen style — Characters get evocative names and may include Personality in the lean tier; Lenses get functional names and Personality goes only in the rich tier reference file.

When designing the new persona, separate alignment signal from knowledge signal. The lean tier entry in CLAUDE.md should contain only alignment content — quality bars, approach, constraints, what to push back on. Domain-specific knowledge (factual details, implementation patterns, technical specifics) belongs in `.claude/references/personas/` or a reference file, loaded on demand. See `gigo/references/persona-template.md` for the "Alignment vs Knowledge Signal" section.

**Regenerate review criteria.** After writing all changes, regenerate `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo Step 6.5. If the file doesn't exist, create it. If it does, regenerate from scratch (don't append). This includes boundary coherence criteria — re-detect boundary types against the current project state.
```

- [x] **Step 2.2: Verify line count stayed in envelope**

Run: `wc -l /Users/eaven/projects/gigo/skills/maintain/references/targeted-addition.md`
Expected: under 80 lines (was 57, adding matrix consultation adds roughly 15–20 lines).

- [x] **Step 2.3: Verify the matrix reference is present**

Run: `grep -c "change-impact-matrix.md" /Users/eaven/projects/gigo/skills/maintain/references/targeted-addition.md`
Expected: at least 1.

- [x] **Step 2.4: Commit**

```bash
git add skills/maintain/references/targeted-addition.md
git commit -m "refactor: consult change impact matrix from targeted-addition Step 5"
```

#### What Was Built
- **Deviations:** None. Single Edit applied the verbatim old_string/new_string swap.
- **Review changes:** None. Per-task review is deferred to Task 4's static verification (cross-cutting grep checks).
- **Notes for downstream:** File grew 57 → 71 lines (+14, well under 80-line cap). Step 5 now consults `change-impact-matrix.md` as a sibling reference. Commit: `3abf96e`.

---

## Task 3: Add change-impact pre-audit to snap/SKILL.md

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Task 2)

**Files:**
- Modify: `skills/snap/SKILL.md` (lines 14–24)

- [x] **Step 3.1: Replace the "Run It" section with the updated five-step version**

Use Edit to replace the current "## Run It" block through the closing line. The `old_string` is:

```markdown
## Run It

1. **Check for snap.md.** Read `.claude/rules/snap.md`. If it doesn't exist, stop: "No snap protocol found. Run `gigo:gigo` to set up the project, or `gigo:maintain` to restructure an existing one."

2. **Follow the protocol.** The project's `snap.md` contains the full audit procedure and learning-routing table, customized for this project's domain. Read it and execute it exactly.

3. **Pipeline check.** After the standard audit, verify: Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed them? If so, flag it and offer to fix.

4. **Coverage gaps.** If the audit finds coverage gaps, offer to invoke `gigo:maintain` to add expertise — don't tell the operator to run a command.

That's it. The snap protocol lives in the project, not here. This skill just makes it invocable and adds pipeline-aware checks.
```

The `new_string` is:

```markdown
## Run It

1. **Check for snap.md.** Read `.claude/rules/snap.md`. If it doesn't exist, stop: "No snap protocol found. Run `gigo:gigo` to set up the project, or `gigo:maintain` to restructure an existing one."

2. **Change impact pre-audit.** Before running the per-project protocol, consult `maintain/references/change-impact-matrix.md`. If the matrix is missing, log a warning and skip this step. Otherwise: run `git status --short` (uncommitted delta only — multi-commit sessions are not audited). For each entry matching `CLAUDE.md`, `.claude/rules/*.md`, or `.claude/references/*.md`, classify the change type using git status flags and the matrix's Snap Read-Back Protocol (CT-1..CT-10). Look up each change type in the matrix and flag any downstream file listed as affected that does NOT also appear in `git status --short`. Report findings as a `## Change Impact (uncommitted delta only)` section at the top of the audit, phrased as "potential ripple — verify," never "you forgot to update X." If git fails (not a repo, pre-initial-commit, detached HEAD without baseline), skip this step with a warning.

3. **Follow the protocol.** The project's `snap.md` contains the full audit procedure and learning-routing table, customized for this project's domain. Read it and execute it exactly.

4. **Pipeline check.** After the standard audit, verify: Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed them? If so, flag it and offer to fix.

5. **Coverage gaps.** If the audit finds coverage gaps, offer to invoke `gigo:maintain` to add expertise — don't tell the operator to run a command.

That's it. The snap protocol lives in the project, not here. This skill makes it invocable, adds pipeline-aware checks, and runs the change-impact pre-audit.
```

- [x] **Step 3.2: Verify snap/SKILL.md line count ≤ 50**

Run: `wc -l /Users/eaven/projects/gigo/skills/snap/SKILL.md`
Expected: ≤ 50 lines.

- [x] **Step 3.3: Verify the matrix reference is present**

Run: `grep -c "maintain/references/change-impact-matrix.md" /Users/eaven/projects/gigo/skills/snap/SKILL.md`
Expected: at least 1.

- [x] **Step 3.4: Verify step renumbering**

Run: `grep -c "^[0-9]\. \*\*" /Users/eaven/projects/gigo/skills/snap/SKILL.md`
Expected: 5 numbered steps.

- [x] **Step 3.5: Commit**

```bash
git add skills/snap/SKILL.md
git commit -m "feat: add change impact pre-audit to snap"
```

#### What Was Built
- **Deviations:** None. Single Edit applied the verbatim old_string/new_string swap.
- **Review changes:** None. Static verification deferred to Task 4.
- **Notes for downstream:** File grew 24 → 26 lines (+2, well under 50-line cap). The new step 2 is one long markdown paragraph so wc-l count stays low. Five numbered steps confirmed. Commit: `f69d064`.

---

## Task 4: Static verification of matrix consumption

**blocks:** 5, 6, 7
**blocked-by:** 2, 3
**parallelizable:** false

**Files:**
- Read-only static checks

Tasks 4 runs static (non-invocation) checks that a bare worker *can* execute. Skill-invocation dogfood tests that require multi-turn agent behavior are deferred to the post-execution operator checklist at the end of this plan.

- [x] **Step 4.1: Verify targeted-addition consults the matrix by name**

Run: `grep -c "change-impact-matrix.md" skills/maintain/references/targeted-addition.md`
Expected: at least 2 (one in the "consult" instruction, one in the "matrix is required" instruction).

- [x] **Step 4.2: Verify targeted-addition no longer hardcodes the old ripple list**

Run: `grep -c "Regenerate review criteria" skills/maintain/references/targeted-addition.md`
Expected: at most 1 (the preserved persona-specific instruction — the consolidated hardcoded list was removed).

- [x] **Step 4.3: Verify snap SKILL.md names the matrix with the correct relative path**

Run: `grep -c "maintain/references/change-impact-matrix.md" skills/snap/SKILL.md`
Expected: at least 1.

- [x] **Step 4.4: Verify snap SKILL.md uses git status --short for the baseline**

Run: `grep -c "git status --short" skills/snap/SKILL.md`
Expected: at least 1.

- [x] **Step 4.5: Verify snap SKILL.md mentions the stateless baseline tradeoff**

Run: `grep -c "uncommitted delta only" skills/snap/SKILL.md`
Expected: at least 1.

- [x] **Step 4.6: Verify the matrix file has all 10 change types and all 5 columns**

Run: `grep -c "^| \*\*CT-" skills/maintain/references/change-impact-matrix.md`
Expected: 10.

Run: `grep -c "^| Change Type | CLAUDE.md | rules/ | references/ | review-criteria.md | Snap audit checks |" skills/maintain/references/change-impact-matrix.md`
Expected: 1.

#### What Was Built
- **Deviations:** Task 4.1 initially failed because both matrix mentions landed on the same line in the Task 2 output (grep -c counts lines, not occurrences).
- **Review changes:** Split the "matrix is required" sentence onto its own line in `targeted-addition.md`, promoting the requirement to a standalone bold statement. Better content, satisfies the ≥ 2 rule. Fix committed separately.
- **Notes for downstream:** targeted-addition.md is now 73 lines (still under 80-line cap). All 7 checks pass: 4.1=2, 4.2=1, 4.3=1, 4.4=1, 4.5=1, 4.6a=10, 4.6b=1.

---

## Task 5: Matrix-missing degradation test (non-destructive)

**blocks:** 6, 7
**blocked-by:** 4
**parallelizable:** false

**Files:**
- Non-destructive move-and-restore of `skills/maintain/references/change-impact-matrix.md`

- [x] **Step 5.1: Copy the matrix to a backup, then remove the original**

```bash
cp skills/maintain/references/change-impact-matrix.md /tmp/change-impact-matrix.md.bak
rm skills/maintain/references/change-impact-matrix.md
```

Using `cp` + `rm` instead of `mv` ensures the backup exists in `/tmp/` before the original is removed. If anything fails between this step and Step 5.3, the `/tmp/` copy is still available for restore.

- [x] **Step 5.2: Confirm the file is gone but reference-correctness still holds**

Run: `test ! -f skills/maintain/references/change-impact-matrix.md && echo "matrix removed" || echo "still present"`
Expected: `matrix removed`.

Run: `grep -c "change-impact-matrix.md" skills/maintain/references/targeted-addition.md skills/snap/SKILL.md`
Expected: both files still reference the path (the references don't vanish just because the target is missing).

- [x] **Step 5.3: Restore the matrix from the backup**

```bash
cp /tmp/change-impact-matrix.md.bak skills/maintain/references/change-impact-matrix.md
```

- [x] **Step 5.4: Verify restore succeeded**

Run: `test -f skills/maintain/references/change-impact-matrix.md && wc -l skills/maintain/references/change-impact-matrix.md`
Expected: file exists, line count matches what Task 1 wrote.

- [x] **Step 5.5: Clean up the backup**

```bash
rm /tmp/change-impact-matrix.md.bak
```

#### What Was Built
- **Deviations:** None. All 5 steps ran in order, non-destructive cp+rm+cp pattern worked as designed.
- **Review changes:** None.
- **Notes for downstream:** Verified that references to `change-impact-matrix.md` in both consumers (targeted-addition=2, snap=1) persist when the target file is missing — the references don't evaporate, which is what lets maintain error loudly and snap degrade softly at runtime. Matrix restored to 75 lines, git status clean.

---

## Task 6: CHANGELOG entry

**blocks:** 8
**blocked-by:** 5
**parallelizable:** true (with Task 7)

**Files:**
- Modify: `CHANGELOG.md` (append to [Unreleased] section)

- [x] **Step 6.1: Add entry under [Unreleased]**

Use Edit with the following exact anchors. The `old_string` is:

```markdown
- **Regeneration support.** `gigo:maintain` regenerates boundary coherence criteria alongside other review criteria when the team or standards change.

### Spec Writing
```

The `new_string` is:

```markdown
- **Regeneration support.** `gigo:maintain` regenerates boundary coherence criteria alongside other review criteria when the team or standards change.

### Change Impact Matrix

- **Proactive ripple detection.** New reference `skills/maintain/references/change-impact-matrix.md` maps 10 change types (persona add/modify/remove, rule add/modify/remove, reference add/remove, extension, pipeline) to downstream files and Snap audit checks. Acts as the single source of truth for ripple logic.
- **Maintain consults the matrix.** `gigo:maintain` targeted-addition mode now reads the matrix at Step 5 to identify which downstream files a change affects. Auto-run items (mechanical `review-criteria.md` regeneration, line budget checks) execute without confirmation. Judgment items are reported to the operator for approval.
- **Snap pre-audit.** `gigo:snap` runs a `git status --short` reverse-lookup against the matrix before the 14-point protocol. Classifies uncommitted changes by change type (CT-1..CT-10) and flags downstream files that haven't been touched as potential ripples. Baseline is uncommitted delta only — snap before committing for best coverage.
- **Deferred for v2:** matrix consultation from `restructure.md` and `upgrade-checklist.md` (they currently regenerate `review-criteria.md` independently); semantic drift detection; multi-commit session baseline.

### Spec Writing
```

- [x] **Step 6.2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add changelog entry for change impact matrix"
```

#### What Was Built
- **Deviations:** None. Changelog entry anchored on the `### Spec Writing` heading, inserted a new `### Change Impact Matrix` subsection with 4 bullets.
- **Review changes:** None. The subagent misreported its commit SHA as `efdf9f2` (actually Task 7's SHA) — the real commit is `37317d9`. Cosmetic reporting issue, the commit is correct.
- **Notes for downstream:** CHANGELOG.md grew by 7 lines under `## [Unreleased]` > `### Change Impact Matrix`. Commit: `37317d9`.

---

## Task 7: Brief supersession note

**blocks:** 8
**blocked-by:** 5
**parallelizable:** true (with Task 6)

**Files:**
- Modify: `briefs/02-phase-selection-matrix.md` (append)

- [x] **Step 7.1: Append the supersession note**

Use Edit to append at the end of the file. The `old_string` is:

```markdown
- Should this extend to detecting drift? e.g., "persona X's quality bars mention 'accessibility' but review-criteria.md has no accessibility criteria"
```

The `new_string` is:

```markdown
- Should this extend to detecting drift? e.g., "persona X's quality bars mention 'accessibility' but review-criteria.md has no accessibility criteria"

---

**Superseded:** This exploratory brief was formalized into the approved design brief at `.claude/plans/typed-yawning-dahl.md` and spec at `docs/gigo/specs/2026-04-10-phase-selection-matrix-design.md` on 2026-04-10. See those files for the approved design and implementation plan.
```

- [x] **Step 7.2: Commit**

```bash
git add briefs/02-phase-selection-matrix.md
git commit -m "docs: supersede exploratory brief with approved design"
```

#### What Was Built
- **Deviations:** The brief file was untracked before this task — first `git add` brought the whole file (61 lines) into git, not just the 5-line append. File now lives in history with its final supersede-note state.
- **Review changes:** None.
- **Notes for downstream:** `briefs/02-phase-selection-matrix.md` is now git-tracked (others in `briefs/` remain untracked, consistent with prior operator practice). Commit: `efdf9f2`.

---

## Task 8: Final verification pass

**blocks:** —
**blocked-by:** 6, 7
**parallelizable:** false

**Files:**
- Read-only verification

- [x] **Step 8.1: Verify all files exist and have expected content**

Run these checks:

```bash
test -f skills/maintain/references/change-impact-matrix.md && echo "matrix: OK" || echo "matrix: MISSING"
grep -q "change-impact-matrix" skills/maintain/references/targeted-addition.md && echo "targeted-addition: OK" || echo "targeted-addition: MISSING REF"
grep -q "maintain/references/change-impact-matrix" skills/snap/SKILL.md && echo "snap: OK" || echo "snap: MISSING REF"
grep -q "Change Impact Matrix" CHANGELOG.md && echo "changelog: OK" || echo "changelog: MISSING"
grep -q "Superseded" briefs/02-phase-selection-matrix.md && echo "brief: OK" || echo "brief: MISSING"
```

Expected: all five print `OK`.

- [x] **Step 8.2: Verify line budgets**

Run:

```bash
wc -l skills/maintain/references/change-impact-matrix.md skills/maintain/references/targeted-addition.md skills/snap/SKILL.md
```

Expected:
- `change-impact-matrix.md` ≤ 120 lines
- `targeted-addition.md` ≤ 80 lines
- `snap/SKILL.md` ≤ 50 lines

- [x] **Step 8.3: Verify no broken path references**

Run:

```bash
grep -rn "gigo/references/change-impact-matrix" skills/ docs/gigo/ 2>/dev/null
```

Expected: no matches (we moved the matrix out of `gigo/references/`, so any lingering reference is stale).

- [x] **Step 8.4: Verify no hardcoded ripple logic remains in targeted-addition**

The old Step 5 had the ripple list inline as bullets. After the refactor, the ripple list should come from the matrix, not from a duplicated hardcoded block. Spot-check by reading Step 5 and confirming it explicitly names the matrix as the source.

Run: `grep -A 3 "matrix is required" skills/maintain/references/targeted-addition.md`
Expected: matches the "do not fall back to a hardcoded ripple list" language.

- [x] **Step 8.5: Final git status check**

Run: `git status --short`
Expected: clean (all changes committed across Tasks 1, 2, 3, 6, 7).

- [x] **Step 8.6: Summary report**

Write a one-paragraph summary of what was built and what deferred work remains (restructure.md and upgrade-checklist.md consolidation, semantic drift detection, multi-commit baseline). Hand off to operator for the post-execution operator checklist below.

#### What Was Built
- **Deviations:** Task 8.3 grep for `gigo/references/change-impact-matrix` matched the plan file itself (which embeds the check command as text) — scoped the check to `skills/` only, confirmed no real broken refs. Task 8.4's original anchor "matrix is required" no longer matched because the Task 4 fix promoted the phrase to "`change-impact-matrix.md` is required"; re-verified with "Do not fall back to a hardcoded" and found the language on line 47.
- **Review changes:** None.
- **Notes for downstream:** Final state — matrix file (75 lines), targeted-addition.md (73 lines, 2 matrix mentions, old ripple list gone), snap/SKILL.md (26 lines, 5 numbered steps with change-impact pre-audit as step 2), CHANGELOG.md has Change Impact Matrix subsection, briefs/02-phase-selection-matrix.md has Superseded note and is now git-tracked. All 5 task-touched files clean in git status.

### Execution Summary

Built a change-impact matrix decision aid that unifies ripple-effect detection across `gigo:maintain` (proactive, at change time) and `gigo:snap` (reactive, at session end). The matrix lives at `skills/maintain/references/change-impact-matrix.md` — 10 change types (CT-1..CT-10) × 5 downstream columns, colocated with its primary consumer. Maintain's `targeted-addition.md` Step 5 was refactored to consult the matrix as a sibling reference, with a hard-fail on missing matrix (no hidden fallback). Snap's `SKILL.md` gained a new step 2 "Change impact pre-audit" that runs `git status --short` on the uncommitted delta, classifies each changed file into a CT row using git-status flags + `git diff` content inspection, and flags downstream files as "potential ripple — verify" when they aren't already touched. Snap degrades softly when the matrix is missing. 8 tasks, 6 commits, zero review escalations. One self-inflicted hiccup on Task 4 (both matrix mentions on the same line ≠ grep -c returning 2) was fixed by splitting the requirement onto its own line, which also improved readability. Deferred to v2: matrix consultation from `restructure.md` + `upgrade-checklist.md` (both still regenerate review-criteria independently), semantic drift detection, multi-commit session baseline.

---

## Post-Execution Operator Checklist

These runtime validation steps require skill invocation and cannot be performed by a bare worker inside `gigo:execute`. After Task 8 completes, the operator runs these manually to verify the matrix works end-to-end.

### Operator Check A: Maintain consumes the matrix (CT-1 persona add)

1. In a fresh conversation turn, ask: `@maintain I want to add a hypothetical persona "The Benchmark — Performance Engineering Lens" to GIGO's CLAUDE.md. Handle as targeted addition.`
2. Watch maintain's output for an explicit reference to `change-impact-matrix.md` and enumeration of the CT-1 row contents (update CLAUDE.md, regenerate review-criteria, etc.).
3. Cancel before any file writes (say "stop, this was a dry run").
4. **Pass criteria:** maintain names the matrix, enumerates ripples, and does not say "matrix not found, using fallback."

### Operator Check B: Snap catches an unhandled CT-1 ripple

1. Append a fake persona block to `CLAUDE.md` (do NOT commit):
    ```markdown

    ### The Bench — Performance Lens (TEST — DO NOT COMMIT)

    - **Owns:** Benchmark discipline
    - **Quality bar:** Every change has a measured delta
    - **Won't do:** Ship without numbers
    ```
2. Verify `git status --short` shows `M  CLAUDE.md`.
3. Run `/snap` or ask Claude to invoke `gigo:snap`.
4. **Pass criteria:** snap's output includes a `## Change Impact (uncommitted delta only)` section at the top, classifies the edit as CT-1 (not CT-2 or CT-3), and flags `review-criteria.md` as a "potential ripple — verify."
5. Revert: `git checkout CLAUDE.md`.

### Operator Check C: Snap catches an unhandled CT-3 ripple (persona removal)

1. In `CLAUDE.md`, delete an entire existing persona block (e.g., cut out "### The Signal — Open-Source Presence Strategist" section down to the next `###` header). Do NOT commit.
2. Verify `git status --short` shows `M  CLAUDE.md`.
3. Run `/snap`.
4. **Pass criteria:** snap classifies the edit as CT-3 (persona removed) via `git diff CLAUDE.md` content inspection, and flags `review-criteria.md` as a "potential ripple."
5. Revert: `git checkout CLAUDE.md`.

### Operator Check D: Snap degrades gracefully when matrix is missing

1. Move the matrix aside:
    ```bash
    mv skills/maintain/references/change-impact-matrix.md /tmp/
    ```
2. Run `/snap`.
3. **Pass criteria:** snap logs "matrix not found, skipping change impact pre-audit" (or equivalent) and continues with the 14-point protocol — no crash, no abort.
4. Restore:
    ```bash
    mv /tmp/change-impact-matrix.md skills/maintain/references/
    ```

### Operator Check E: Maintain fails hard when matrix is missing

1. Move the matrix aside: `mv skills/maintain/references/change-impact-matrix.md /tmp/`
2. In a fresh conversation: `@maintain add a persona "Test" — targeted addition.`
3. **Pass criteria:** maintain errors loudly ("matrix not found" or similar), does NOT fall back to a hardcoded ripple list, does NOT proceed silently.
4. Restore: `mv /tmp/change-impact-matrix.md skills/maintain/references/`

### Operator Check F: Git edge cases (optional, if paranoid)

1. In a throwaway temp directory, run `git init` to create a pre-initial-commit repo.
2. Copy in a fake `.claude/rules/` + `CLAUDE.md` structure, seed matrix + snap SKILL.md.
3. Run snap. **Pass criteria:** snap logs a warning about git state and continues with the 14-point protocol.

---

## Deferred to v2

- **Matrix consultation from `restructure.md` and `upgrade-checklist.md`.** Both currently regenerate `review-criteria.md` independently. v2 should refactor both to consult the matrix, completing the consolidation.
- **Semantic drift detection.** Checking that persona quality bar wording aligns with review-criteria.md content requires LLM-based comparison. Possible via the Challenger pattern.
- **Multi-commit session baseline.** Current snap pre-audit only catches uncommitted changes. A "since last snap" baseline would need timestamp tracking.

<!-- approved: plan 2026-04-10T23:25:01 by:Eaven -->
