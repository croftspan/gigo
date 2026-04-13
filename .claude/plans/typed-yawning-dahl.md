# Design Brief: Phase Selection Matrix for gigo:maintain

## Context

**Why this change?** When an operator changes one thing in an assembled GIGO project — adds a persona, modifies a rule, adds a reference — there are downstream files that should be updated (review-criteria.md regeneration, snap checks, CLAUDE.md pointers). Right now the ripple logic is scattered: partially hardcoded in `skills/maintain/references/targeted-addition.md` Step 5 (persona addition only), partially in The Snap's 14-point reactive audit, partially implicit in health-check. Most change types have no dedicated downstream handling at all.

**What prompted it?** Competitive analysis of [revfactory/harness](https://github.com/revfactory/harness). Their Phase 0 contains a "Phase Selection Matrix" — a table mapping change types to which workflow phases need to re-run. Clean UX pattern. The operator wants a GIGO-native version.

**Intended outcome.** A decision aid (reference file, not a mandate) that maps change types → downstream effects, consulted by `gigo:maintain` at change time. Proactive where The Snap is reactive. Single source of truth for ripple logic, extensible for new change types.

## Phase 1: Project State (findings)

### Existing Surface Area

- `skills/maintain/SKILL.md` — 68 lines. Detects mode, points to 4 mode references. Operator constraint: must not grow.
- `skills/maintain/references/targeted-addition.md` — Step 5 already encodes persona-addition ripple logic (update CLAUDE.md, add extensions, check Overwatch threshold, check line budgets, regenerate review-criteria.md).
- `skills/maintain/references/health-check.md` — four-axis triage; doesn't know "what ripples from X change."
- `skills/maintain/references/restructure.md` — Phase 5 execution has 10 numbered steps including regenerate review-criteria (Step 10).
- `.claude/rules/snap.md` — 14-point audit runs end-of-session. Check 11 is "review criteria staleness"; check 6 is persona calibration; check 8 is coverage. All reactive.
- `skills/gigo/SKILL.md` Step 6.5 — mechanical algorithm that generates `review-criteria.md` from persona quality bars, standards gates, extension "The Standard" sections, and boundary-mismatch patterns. This is the reference implementation for "regenerate review-criteria."
- `skills/gigo/references/boundary-mismatch-patterns.md` — example of cross-skill reference sharing (read by gigo:gigo AND review skills).

### Current State of Ripple Handling

| Change type | Currently covered? | Where |
|---|---|---|
| Persona added | Yes (partially duplicated) | targeted-addition Step 5 hardcodes it; restructure.md Step 5/Phase 5 line 105 also regenerates review-criteria; upgrade-checklist.md line 78 also regenerates. Three places describe overlapping ripple logic. |
| Persona modified | Partial | no dedicated procedure; snap check 11 catches stale review-criteria reactively |
| Persona removed | No dedicated procedure | snap check 6 (calibration) may flag |
| Rule added/modified | Partial | snap checks 1/2/3/5/7 catch line-budget + derivability + overlap reactively |
| Rule removed | No dedicated procedure | orphaned references might be caught by health-check, not systematically |
| Reference added | No dedicated procedure | "When to Go Deeper" pointer convention exists but isn't enforced on add |
| Reference removed | No dedicated procedure | orphaned pointers in rules files go undetected |
| Extension file added/modified | Partial | standards check via snap audit |
| Pipeline change (workflow.md) | Partial | snap check 10 catches collapsed phases |

**Key insight:** Only one change type (persona added) has proactive ripple handling — and that handling is already *triply duplicated* across `targeted-addition.md`, `restructure.md`, and `upgrade-checklist.md` (all three regenerate review-criteria.md independently). Every other change type either waits for The Snap at session end, or falls through the cracks. The consolidation argument is stronger than I initially thought: the matrix doesn't just centralize new logic, it eliminates existing triplication.

### Brief Format Reference

Briefs in `briefs/` use loose structure: Origin, Problem, What to Build, proposed shape, Constraints, Open Questions. Example references: `01-qa-boundary-mismatch.md`, `03-execution-architecture-catalog.md`. Target audience is the operator + the `gigo:spec` skill downstream.

### Cross-skill Reference Pattern (key finding for path resolution)

Established convention: shared cross-skill references live in `skills/gigo/references/` and are referenced by other skills via the path `gigo/references/<file>.md`. Claude's skill framework resolves this automatically — no `$CLAUDE_PLUGIN_DIR`, no version-stamped paths, no explicit base directory substitution.

Evidence from grep:
- `skills/maintain/references/targeted-addition.md:49` — `gigo/references/persona-template.md`
- `skills/maintain/references/restructure.md:100` — `gigo/references/snap-template.md`
- `skills/maintain/references/upgrade-checklist.md:64,71,72,73` — same convention
- `skills/maintain/SKILL.md:67` — same convention
- `skills/gigo/references/boundary-mismatch-patterns.md` — existing example of shared cross-skill reference at this location

**Implication:** The matrix belongs at `skills/gigo/references/change-impact-matrix.md`. Both maintain and snap can read it via `gigo/references/change-impact-matrix.md`. No path-resolution complexity — the operator's explicit concern is addressed.

## Phase 2: Clarifying Question

Asked: "What should v1 ship — matrix only, matrix + consolidation, or full (matrix + consolidation + snap reverse-lookup)?"

**Operator answer:** Full scope. "isnt full the way to go? if we're doing this right? make sure we dont hit path-resolution complexity"

**Interpretation:** Ship the complete design. Resolve path-resolution complexity rather than dodging it. (Addressed above — `gigo/references/` convention handles it.)

## Phase 3: Verb-Listing Gate + Approach Selection

**Action verbs from the operator's request:**
- `add` / `modify` / `remove` (persona, rule, reference changes — source column of the matrix)
- `update` (downstream files that need touching)
- `surface` (show ripple effects to the operator)
- `consult` (maintain reads the matrix)
- `map` (matrix itself — change types → downstream effects)
- `catch` (ripples that currently go undetected)
- `refactor` (replace targeted-addition Step 5's hardcoded list with matrix consultation)
- `query` / `reverse-lookup` (snap asks "what changed since last commit → what ripples?")
- `report` (matrix outputs a findings list, operator decides what to act on)

**Approach chosen (operator-selected):** Full scope.

The matrix becomes the single source of truth for change → ripple mappings. Targeted-addition Step 5 is refactored to consult it. Snap gets a new pre-audit step that diffs recent changes against the matrix to flag stale downstream work. Drift detection (semantic comparison) is out of scope for v1 — syntactic matrix only.

Every verb is accounted for:
- `add/modify/remove` → matrix source column
- `update` → matrix downstream column  
- `surface` → maintain reports ripples at change time
- `consult` → maintain + snap both consult via `gigo/references/change-impact-matrix.md`
- `map` → matrix structure
- `catch` → matrix covers 8 currently-uncovered change types
- `refactor` → targeted-addition Step 5 rewrite
- `query/reverse-lookup` → snap's git-diff-driven pre-audit step
- `report` → matrix results flow into maintain's proposal and snap's audit report

No verb is dropped.

## Phase 4: Design

### Architecture Overview

```
                             ┌─────────────────────────────────────┐
                             │ skills/gigo/references/             │
                             │   change-impact-matrix.md           │
                             │                                     │
                             │  [matrix body]                      │
                             │  [ripple categorization]            │
                             │  [auto-run vs report policy]        │
                             │  [snap read-back protocol]          │
                             └──────────────┬──────────────────────┘
                                            │
                                            │ read via `gigo/references/...`
                                            │
                         ┌──────────────────┼─────────────────────┐
                         │                                        │
                         ▼                                        ▼
            ┌──────────────────────────┐          ┌──────────────────────────┐
            │ skills/maintain/         │          │ skills/snap/SKILL.md     │
            │   references/            │          │                          │
            │   targeted-addition.md   │          │  new pre-audit step:     │
            │                          │          │  git diff HEAD →         │
            │  Step 5 refactored to    │          │  matrix lookup →         │
            │  consult matrix at       │          │  flag stale downstream   │
            │  change time             │          │  files                   │
            └──────────────────────────┘          └──────────────────────────┘
```

Three files touched: one new (the matrix), two modified (`targeted-addition.md` for consolidation, `snap/SKILL.md` for reverse-lookup). Maintain's `SKILL.md` is untouched — stays at 68 lines.

### Component 1: The Matrix Reference File

**Path:** `skills/gigo/references/change-impact-matrix.md`

**Audience:** `gigo:maintain` at change time, `gigo:snap` at session end. Not operator-facing directly — but the operator sees the ripple list in maintain's proposals and snap's reports.

**Structure (proposed):**

```markdown
# Change Impact Matrix

Decision aid for `gigo:maintain` and `gigo:snap`. Maps change types to downstream
files that may need updating. Not a mandate — maintain reports, operator decides.

## How to Read This

Each row is a change type (what the operator did or is about to do). Columns are
downstream files. Cell values:
- **regenerate** — mechanical, deterministic. Maintain auto-runs without confirmation.
- **update (judgment)** — needs human decision. Maintain reports, operator approves.
- **verify** — may or may not need change depending on content. Maintain reports as a question.
- **check pointer** — rules files may have "When to Go Deeper" pointers to update.
- **—** — no expected effect.

## The Matrix

| Change Type | CLAUDE.md | rules/ | references/ | review-criteria.md | Snap audit checks |
|---|---|---|---|---|---|
| **Persona added** | update (team section) | check line budget | verify authorities.md if new research | regenerate | coverage + calibration |
| **Persona modified** (quality bar or approach) | update entry | — | verify if authority research changed | regenerate if quality bars changed | calibration |
| **Persona removed** | remove entry | check for orphaned rule sections | archive authority notes | regenerate | calibration + coverage |
| **Rule added** (new file in .claude/rules/) | — | direct edit; check overlap with existing | — | — | line + derivability + overlap |
| **Rule modified** | — | direct edit; re-check line budget | — | verify if it changed a quality gate | line + derivability |
| **Rule removed** | remove file reference if any | check for orphaned "When to Go Deeper" pointers in other rules files | — | — | overlap + coverage |
| **Reference added** | — | add "When to Go Deeper" pointer in the relevant rules file | direct write | — | — |
| **Reference removed** | — | remove orphaned "When to Go Deeper" pointers in rules files | — | — | — |
| **Extension file added/modified** (new domain extension in rules/) | — | follow extension-file-guide.md format | — | regenerate if "The Standard" section changed | line + derivability |
| **Pipeline change** (workflow.md structural edit) | — | update workflow.md | verify pipeline-architecture.md still describes the shape | — | pipeline |

## Auto-Run vs Report Policy

**Auto-run** (no operator confirmation needed — mechanical and deterministic):
- `regenerate` of review-criteria.md (algorithm is Step 6.5 from gigo:gigo, purely mechanical)
- Line count checks (numeric thresholds)
- "When to Go Deeper" pointer additions when a reference is added and the rules file exists

**Report** (needs operator decision):
- Any cell marked "update (judgment)" — includes CLAUDE.md entries, anything requiring research or phrasing decisions
- Any cell marked "verify" — maintain says "this may need updating, please look"
- Orphaned pointer cleanup (risk of unintended removal)

**Principle:** If the action is purely mechanical and the reference implementation exists (like review-criteria generation), auto-run. If it requires judgment, phrasing, or research, report and let the operator decide.

## Snap Read-Back Protocol

Snap consults this matrix at session end. Procedure:

1. Run `git diff HEAD --name-only` and `git status --short` to list files changed since the last commit.
2. For each changed file matching a maintainable path (`CLAUDE.md`, `.claude/rules/*.md`, `.claude/references/*.md`), determine the change type by matching the path pattern.
3. Look up the change type's row in the matrix. Any downstream cells with non-empty values become "potential ripples."
4. Compare to what's actually been touched. If a downstream file is listed as affected but hasn't been modified in the same commit range, flag it as a potential ripple the operator hasn't addressed.
5. Report at the end of snap's audit: "Since last commit, you changed [file]. Matrix says this may ripple to [list]. [File X] was updated in the same range — looks handled. [File Y] was not — worth verifying."

No new state tracking — git is the source of truth for "what changed." No timestamp files, no snap markers.

## Out of Scope for v1

- **Semantic drift detection.** "Persona quality bar mentions accessibility but review-criteria.md has no accessibility criteria" requires LLM-based comparison. v1 is syntactic only — it maps change types to file paths, not content to content. A v2 could add drift detection using the Challenger pattern.
- **Cross-project reference handling.** Matrix covers intra-project ripples. External dependencies, cross-repo coordination, etc. are out of scope.
- **Automated downstream execution for judgment tasks.** Matrix reports judgment-required ripples; maintain doesn't attempt to guess the right edit.
```

Estimated length: ~80-100 lines. Reference-tier, loaded on demand, zero always-on cost.

### Component 2: `targeted-addition.md` Refactor

**Path:** `skills/maintain/references/targeted-addition.md`

**Current Step 5** (lines 44-57): hardcoded list of persona-addition ripples — add to CLAUDE.md, add extensions, add references, check Overwatch threshold, check line budgets, regenerate review-criteria, handle persona style.

**Proposed Step 5 rewrite:**

```markdown
## Step 5: Merge

Consult `gigo/references/change-impact-matrix.md` to identify downstream ripples for the change type you're making. For "Persona added" (the common case this procedure handles), the matrix specifies:

- **CLAUDE.md:** update team section (operator judgment — use your proposed content)
- **rules/:** check line budget before adding; tighten existing entries if the addition pushes a file past ~60 lines
- **references/:** verify authorities.md only if new research was used (operator judgment — ask the operator)
- **review-criteria.md:** regenerate mechanically (auto-run, no confirmation needed)
- **Snap audit effects:** coverage + calibration checks now cover the new persona

Execute the auto-run items. Report the judgment items to the operator and wait for decisions.

**Overwatch threshold (scale-dependent).** After adding, count domain personas in CLAUDE.md (don't count The Overwatch). If now at 3+ and The Overwatch isn't present, add The Overwatch persona — read `gigo/references/persona-template.md` → "The Overwatch" for the template. Verify the Overwatch section in `workflow.md` and `overwatch.md` reference are present (should be from initial assembly).

**Persona style.** Read `.claude/references/persona-style.md` (default: Lenses). New personas must match the project's chosen style — Characters get evocative names and may include Personality in the lean tier; Lenses get functional names with Personality only in the rich tier reference file.

**Alignment vs knowledge placement.** Separate alignment signal (quality bars, approach, constraints → CLAUDE.md lean tier) from knowledge signal (factual details, patterns → references). See `gigo/references/persona-template.md` → "Alignment vs Knowledge Signal" section.

**Regenerate review criteria.** After writing all changes, regenerate `.claude/references/review-criteria.md` using the algorithm from gigo:gigo Step 6.5. If the file doesn't exist, create it. If it does, regenerate from scratch. This includes boundary coherence criteria — re-detect boundary types against the current project state.
```

**Net change:** Step 5 body stays roughly the same length (maybe +3/-3 lines). The hardcoded ripple list is now anchored in the matrix, preventing drift between Step 5's "what to do after adding a persona" and the matrix's canonical listing. Other change types can now be handled by the same mechanism — maintain consults the matrix for whichever change type the operator requested.

### Component 3: Snap Reverse-Lookup Integration

**Path:** `skills/snap/SKILL.md`

**Current state:** 24 lines. Reads per-project `.claude/rules/snap.md`, executes it, runs pipeline check, offers maintain invocation on coverage gaps.

**Proposed addition** (new step between current 2 and 3):

```markdown
3. **Change impact pre-audit.** Before running the per-project protocol's line/derivability/overlap checks, identify what's changed since the last commit and surface any unhandled ripples.
   - Run `git diff HEAD --name-only` and `git status --short` to find modified/added files.
   - For each changed file under `CLAUDE.md`, `.claude/rules/`, or `.claude/references/`, determine the change type (path-based matching).
   - Read `gigo/references/change-impact-matrix.md`. Look up each change type's row.
   - For each downstream effect listed in the matrix, check whether the downstream file was also modified in the same change range. If not, flag it as a potential unhandled ripple.
   - Include the findings as a "Change Impact" section at the top of your audit report, before the 14-point protocol results.
```

**Renumber existing steps 3 and 4 to 4 and 5.** Snap SKILL.md grows from 24 to ~34 lines. Well under any cap.

### Data Flow

**Flow A: Operator invokes `gigo:maintain` to add a persona**

1. Maintain detects `targeted-addition` mode.
2. Reads `targeted-addition.md`.
3. Step 5 says: consult `gigo/references/change-impact-matrix.md`.
4. Matrix lookup for "Persona added" returns: regenerate review-criteria (auto), update CLAUDE.md (judgment), verify authorities.md (judgment, if research new), check line budgets (auto-check).
5. Maintain runs auto items, presents judgment items to operator in the proposal.
6. Operator approves, maintain writes changes.
7. review-criteria.md is regenerated mechanically. Operator never sees friction for the purely mechanical step.

**Flow B: Operator runs `gigo:snap` at end of session (having made changes outside maintain)**

1. Snap reads per-project `.claude/rules/snap.md`.
2. New pre-audit step runs `git diff HEAD --name-only`.
3. Finds operator manually edited `CLAUDE.md` (persona quality bar text) and `.claude/rules/standards.md`.
4. Looks up "Persona modified" and "Rule modified" in the matrix.
5. Matrix says: persona mod → review-criteria.md regenerate if quality bar changed; rule mod → verify if it changed a quality gate.
6. Snap checks: was review-criteria.md modified in this range? No. Flags it as "potential unhandled ripple — review-criteria.md may be stale after your CLAUDE.md edit. Run gigo:maintain targeted to regenerate, or regenerate manually."
7. Snap continues with its 14-point audit and reports both.

**Why this flow works:** Snap catches ad-hoc changes (the operator manually edited a file outside maintain's structured flow). Maintain catches structured changes (the operator invoked maintain). Both consult the same matrix, so the definition of "ripple" is consistent across proactive and reactive paths.

### Error Handling

- **Matrix file missing.** Maintain: continue with hardcoded fallback (current Step 5 logic, preserved as a comment block for safety). Snap: skip the pre-audit step with a warning log.
- **Matrix row not found for a change type.** Maintain: report to operator "I don't recognize this change type — matrix has no row. Please handle manually." Snap: skip that file with a warning.
- **Git command fails in snap.** Fall back to running the 14-point audit without the pre-audit step.
- **Downstream file path resolution fails.** Log which path failed, continue with the rest of the matrix lookup.

Principle: the matrix is additive intelligence. If it fails, the existing behavior (maintain's current Step 5, snap's 14-point audit) continues unchanged. No new single point of failure.

### Interfaces (Isolation Boundaries)

- **Matrix file ↔ maintain:** Read-only. Matrix is a static reference. Maintain parses the table, looks up change types, acts on auto-run items, reports judgment items.
- **Matrix file ↔ snap:** Read-only. Snap uses the table for reverse-lookup, not forward execution.
- **Maintain ↔ snap:** No direct coupling. Both consume the same reference file. Changes to the matrix automatically propagate to both consumers.
- **Matrix ↔ operator:** Indirect. Operator never reads the matrix directly — they see matrix output as ripple lists in maintain's proposals and snap's reports.

### Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Matrix drifts from maintain's actual behavior | Medium | Make the matrix the source of truth; `targeted-addition.md` refactored to consult it, not duplicate it |
| Snap's git-diff-based lookup produces false positives | Medium | Phrase reports as "potential ripple — verify," not "you forgot to update X" |
| Matrix grows unwieldy as new change types accumulate | Low | Reference-tier, loaded on demand. Cost is zero until invoked. ~100 lines is comfortable; real change types are finite (~15 at most) |
| Operator ignores matrix output, feels noisy | Medium | Snap's report should only flag ripples NOT already in the same commit range. Maintain's proposal should group mechanical (auto-run, no ask) vs judgment (one operator prompt) |
| Path resolution breaks if plugin structure changes | Low | Uses established `gigo/references/` convention already proven across 5+ files |

### Build Sequence

1. Write `skills/gigo/references/change-impact-matrix.md` — the matrix itself. Format lockdown.
2. Update `skills/maintain/references/targeted-addition.md` Step 5 to consult the matrix. Validate existing persona-addition flow is unchanged.
3. Update `skills/snap/SKILL.md` with the pre-audit step. Renumber existing steps.
4. Manual smoke test: invoke maintain with a persona-addition scenario, verify it reads the matrix and behaves as before. Invoke snap on a repo with uncommitted rules changes, verify it flags ripples.
5. Update CHANGELOG.md with a v0.12.0-beta (or equivalent) entry.

No execute-phase parallelism needed — file changes are small and sequentially dependent (matrix must exist before consumers reference it).

### Verification Plan

- **Unit-level:** Read the matrix file after writing — markdown table parses, all 9 change types present, all 5 columns populated.
- **Integration-level:** Dogfood against GIGO itself. Add a fake persona to a test project, invoke `gigo:maintain`, verify the matrix path is consulted and downstream effects match the table.
- **Snap reverse-lookup:** Create a test scenario with uncommitted CLAUDE.md edit, run `gigo:snap`, verify the change impact pre-audit flags the expected downstream file.
- **Path resolution:** Grep for the matrix path from both maintain and snap skill directories — confirm no broken references.
- **Line budget:** Count lines of matrix, targeted-addition.md after edit, snap SKILL.md after edit. None should exceed their constraints (matrix is reference so no cap; targeted-addition should stay ~60; snap SKILL.md ≤ 40).

### Files to Touch

| File | Status | Why |
|---|---|---|
| `skills/gigo/references/change-impact-matrix.md` | **NEW** | The matrix itself — primary deliverable |
| `skills/maintain/references/targeted-addition.md` | **MODIFY** | Step 5 refactored to consult matrix |
| `skills/snap/SKILL.md` | **MODIFY** | Add change-impact pre-audit step, renumber |
| `CHANGELOG.md` | **MODIFY** | Document the new matrix + integration |
| `briefs/02-phase-selection-matrix.md` | **SUPERSEDE** (by this brief) | Old brief rolled into this approved design |

**Untouched:**
- `skills/maintain/SKILL.md` (68 lines, constraint preserved)
- `skills/maintain/references/health-check.md` (matrix is consulted only by targeted-addition in v1; health-check's four-axis triage is unchanged)
- `.claude/rules/snap.md` (per-project protocol unchanged — matrix consultation is plugin-level)

**Addendum from fact-check:** `restructure.md` line 105 and `upgrade-checklist.md` line 78 both contain their own calls to regenerate `review-criteria.md`. These are **partial duplications** of targeted-addition Step 5's ripple logic. In v1, we leave those calls in place (they're structurally correct and the matrix doesn't yet mandate consolidation across all modes). In v2, these should also refactor to consult the matrix, completing the consolidation. Noted as follow-up, not a v1 blocker.

### Scope Boundaries

**In scope for v1:**
- The matrix reference file
- Maintain's targeted-addition consumption of it
- Snap's reverse-lookup consumption of it
- Auto-run vs report policy encoded in the matrix
- 9 change types (persona add/modify/remove, rule add/modify/remove, reference add/remove, extension, pipeline)

**Out of scope for v1 (documented in matrix as "Future work"):**
- Semantic drift detection (persona quality bars vs review-criteria content alignment)
- Cross-project or cross-repo coordination
- Refactoring `restructure.md` Phase 5 and `upgrade-checklist.md` to consult the matrix (they currently have their own review-criteria regeneration calls — structurally fine, but duplicates the matrix's canonical listing; consolidate in v2)
- Health-check integration with the matrix (health-check does broad four-axis triage, not change-specific)
- Automated downstream execution for judgment-required ripples (matrix reports; operator decides)

## Phase 4.25: Fact-Check Results

Dispatched Plan subagent to verify factual claims. **All 10 key claims verified against the actual project:**

1. ✓ `skills/maintain/SKILL.md` = 68 lines
2. ✓ `skills/maintain/references/targeted-addition.md` Step 5 (lines 43-57) contains the persona-addition ripple logic as described
3. ✓ `.claude/rules/snap.md` has 14-point audit; checks 6 (persona calibration), 8 (coverage), 11 (review criteria) match claims
4. ✓ `skills/gigo/SKILL.md` Step 6.5 (lines 230-248) is the mechanical algorithm; line 247 explicitly says "This step is mechanical — no operator approval needed"
5. ✓ `gigo/references/<file>.md` path convention active at all cited lines
6. ✓ `skills/snap/SKILL.md` = 24 lines with 4 numbered steps
7. ✓ `skills/gigo/references/` contains all four shared reference files
8. ✓ No `review-criteria.md` in GIGO source itself (only in eval fixtures and worktrees)
9. ✓ No existing "change impact" or matrix-equivalent handling exists in the project
10. ✓ No internal contradictions in the brief

**Supplementary context from fact-check (not an issue, a refinement):** Review-criteria regeneration logic is more duplicated than the brief initially acknowledged — `restructure.md` line 105 and `upgrade-checklist.md` line 78 also regenerate review-criteria independently of `targeted-addition.md` Step 5. This triplication strengthens the matrix's consolidation value. Brief updated above to reflect this.

**Verdict:** Design brief is factually sound. Proceed to approval.

---

## Post-Approval: What Happens Next

This is a DESIGN BRIEF, not an implementation plan. After approval:

1. Run `/spec` to formalize this brief into a spec and implementation plan
2. `/spec` handles: spec writing, self-review, Challenger (for large tasks — this likely qualifies), operator approval, plan writing, plan review
3. Run `/execute` to build from the approved plan
4. Run `/verify` or `/sweep` after execution

**DO NOT start writing code after this brief is approved. The next step is `/spec`.**

**Expected artifact from `/spec`:**
- `spec.md` formalizing requirements (what the matrix must contain, what Step 5 must do, what snap's new step must do)
- `plan.md` with ordered tasks (write matrix → refactor Step 5 → add snap step → CHANGELOG)
- Challenger review (since this touches 3 skill files and changes an established procedure, it qualifies as "large task" under spec's criteria)

**Also: this brief supersedes `briefs/02-phase-selection-matrix.md`** — the original brief was a proposal, this is the approved design. After `/spec` runs, `briefs/02-phase-selection-matrix.md` can be archived or deleted (operator decides).

<!-- approved: design-brief 2026-04-10T16:33:16 by:Eaven -->
