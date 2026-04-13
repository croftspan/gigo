# Phase Selection Matrix — Design Spec

**Status:** Draft (pending operator approval)
**Design brief:** `.claude/plans/typed-yawning-dahl.md` (approved 2026-04-10)
**Supersedes:** `briefs/02-phase-selection-matrix.md` (exploratory brief)

## Original Request

> /blueprint Design a Phase Selection Matrix for gigo:maintain — a decision aid that maps change types (persona added/modified/removed, rule added, reference added, extension file added, pipeline change) to downstream effects across CLAUDE.md, rules/, references/, review-criteria.md, and the Snap audit.
>
> Full context is in briefs/02-phase-selection-matrix.md — read it first. Origin: competitive analysis of revfactory/harness, which has a clean "Phase Selection Matrix" UX pattern in their Phase 0. We want a GIGO-native version.
>
> Key tensions to resolve during design (operator flagged these as open questions):
>
> 1. **Auto-run vs report only.** Should maintain automatically offer to run downstream updates, or just report "here's what's affected" and let the operator decide?
> 2. **Redundancy with The Snap.** Snap's 14-point audit already catches some ripple effects reactively. This matrix would be the proactive version.
> 3. **Drift detection scope.** Is semantic drift detection in scope for v1, or a later extension?
>
> Constraints: maintain's SKILL.md is 68 lines — matrix belongs in a reference file. Must be a decision aid, not a mandate. Cover actual change types that happen in GIGO projects.
>
> Where it lands: Primary — gigo:maintain reads the matrix when processing a change request. Secondary — gigo:snap could use it in reverse.

Follow-up clarification from operator: "isnt full the way to go? if we're doing this right? make sure we dont hit path-resolution complexity"

## Problem

When an operator changes one thing in a GIGO project — adds a persona, modifies a rule, adds a reference — there are downstream files that should be updated in response. Today that ripple logic is scattered and inconsistent:

- **Persona addition** is handled proactively, but triply duplicated: `skills/maintain/references/targeted-addition.md` Step 5, `skills/maintain/references/restructure.md` Phase 5, and `skills/maintain/references/upgrade-checklist.md` all independently regenerate `review-criteria.md`.
- **Persona modification, persona removal, rule add/modify/remove, reference add/remove, extension changes, pipeline changes** — none have dedicated proactive handling. They either fall through to The Snap's reactive end-of-session audit, or fall through the cracks entirely.
- **The Snap** catches *some* ripple effects reactively (checks 6/8/11 cover persona calibration, coverage, review-criteria staleness), but only at session end and only for a subset.

The operator wants a proactive decision aid, not a rigid system — consulted by `gigo:maintain` at change time and by `gigo:snap` at session end, both reading from a single source of truth.

## Requirements

### R1: Change Impact Matrix reference file

**Path:** `skills/maintain/references/change-impact-matrix.md`

**Purpose:** Single source of truth mapping change types to downstream files and Snap audit checks. Consulted by `gigo:maintain` proactively and by `gigo:snap` reactively.

**Path placement rationale:** Lives under `skills/maintain/references/` — colocated with its primary consumer (`targeted-addition.md`, `restructure.md`, `upgrade-checklist.md` all live here). Maintain reads it as a sibling reference. Snap reads it via `maintain/references/change-impact-matrix.md`. The `skills/gigo/references/` location was rejected because that directory hosts assembly-skill templates and algorithms (`persona-template.md`, `snap-template.md`, `boundary-mismatch-patterns.md`, `authorities.md`), and this matrix is operational ripple logic, not assembly tooling. Path resolution is not framework-automatic — Claude-the-LLM reads the path and resolves it against the plugin's `skills/` tree. The relative form `maintain/references/change-impact-matrix.md` is unambiguous from any consumer inside the plugin.

**File structure (reference tier, loaded on demand):**

1. **Header & usage note.** One paragraph: "Decision aid for `gigo:maintain` and `gigo:snap`. Maps change types to downstream files that may need updating. Not a mandate — maintain reports, operator decides."
2. **How to read this.** Legend for cell values: `regenerate` / `update (judgment)` / `verify` / `check pointer` / `—`.
3. **The Matrix.** Markdown table with 10 rows (change types) × 5 columns (downstream effects).
4. **Auto-run vs Report policy.** Which cell values are auto-executed by maintain vs which require operator confirmation.
5. **Snap read-back protocol.** Step-by-step procedure for snap's git-diff-based reverse lookup.
6. **Out of scope for v1.** Explicit list of deferred capabilities.

**The 10 change types (rows):**

| ID | Change type | Trigger |
|---|---|---|
| CT-1 | Persona added | New persona in CLAUDE.md |
| CT-2 | Persona modified (quality bar / approach) | Edit to existing persona entry |
| CT-3 | Persona removed | Persona deleted from CLAUDE.md |
| CT-4 | Rule added (new file in `.claude/rules/`) | New `.md` in rules dir |
| CT-5 | Rule modified | Edit to existing rules file |
| CT-6 | Rule removed | Rules file deleted |
| CT-7 | Reference added | New `.md` in `.claude/references/` |
| CT-8 | Reference removed | References file deleted |
| CT-9 | Extension file added/modified (domain extension) | New or edited extension in `.claude/rules/` following extension-file-guide format |
| CT-10 | Pipeline change (`workflow.md` structural edit) | Edit changing phase structure |

**The 5 downstream columns:** `CLAUDE.md`, `.claude/rules/`, `.claude/references/`, `review-criteria.md`, Snap audit checks.

**The concrete matrix (what the worker writes into the file):**

| Change Type | CLAUDE.md | rules/ | references/ | review-criteria.md | Snap audit checks |
|---|---|---|---|---|---|
| **CT-1: Persona added** | update (team section) | check line budget | verify authorities.md if new research | regenerate | coverage + calibration |
| **CT-2: Persona modified** (quality bar or approach) | update entry | — | verify if authority research changed | regenerate if quality bars changed | calibration |
| **CT-3: Persona removed** | remove entry | check for orphaned rule sections | archive authority notes | regenerate | calibration + coverage |
| **CT-4: Rule added** | — | direct edit; check overlap | — | — | line + derivability + overlap |
| **CT-5: Rule modified** | — | direct edit; re-check line budget | — | verify if it changed a quality gate | line + derivability |
| **CT-6: Rule removed** | remove file reference if any | check pointer cleanup in other rules files | — | — | overlap + coverage |
| **CT-7: Reference added** | — | add "When to Go Deeper" pointer in relevant rules file | direct write | — | — |
| **CT-8: Reference removed** | — | remove orphaned "When to Go Deeper" pointers | — | — | — |
| **CT-9: Extension file added/modified** | — | follow extension-file-guide.md format | — | regenerate if "The Standard" section changed | line + derivability |
| **CT-10: Pipeline change** (workflow.md) | — | update workflow.md | verify pipeline-architecture.md still describes the shape | — | pipeline |

**Cell value semantics:**

- **`regenerate`** — mechanical, deterministic. Maintain auto-runs without operator confirmation (e.g., `review-criteria.md` regeneration via gigo:gigo Step 6.5 algorithm).
- **`update (judgment)`** — requires human decision. Maintain reports, operator approves.
- **`verify`** — may or may not need change depending on content. Maintain reports as a question to the operator.
- **`check pointer`** — rules files may have "When to Go Deeper" pointers that need cleanup.
- **`—`** — no expected effect.

**Auto-run policy:** Only `regenerate` of `review-criteria.md` and line-budget/threshold numeric checks are auto-run. Everything else is reported to the operator for decision.

**Line budget:** Reference tier has no strict cap, but should stay roughly ≤120 lines for readability. Zero always-on token cost.

### R2: targeted-addition.md Step 5 refactor

**Path:** `skills/maintain/references/targeted-addition.md`

**Current state:** Step 5 (lines 43–57) contains a hardcoded list of persona-addition ripple effects: update CLAUDE.md, add extensions, check Overwatch threshold, check line budgets, regenerate review-criteria.md, handle persona style.

**Target state:** Step 5 consults `change-impact-matrix.md` (sibling reference) as the source of truth for ripple effects. The specific persona-addition logic (Overwatch threshold check, persona style alignment, Alignment vs Knowledge guidance, review-criteria regeneration) is retained in prose — the matrix identifies *what* ripples, but persona-specific guidance still belongs in the targeted-addition procedure because those concerns are particular to persona additions, not all change types.

**No fallback.** If the matrix file is missing, Step 5 errors loudly. The matrix is a required dependency, not an optional enhancement. The old hardcoded ripple list is removed, not preserved as a comment block — keeping a commented copy would be a fourth duplication of the same logic and defeat the consolidation goal.

**Behavior preserved:**

- Review-criteria.md is still regenerated mechanically after persona changes
- Overwatch threshold (3+ domain personas triggers The Overwatch addition) still checked
- Persona style (Lenses vs Characters) still enforced
- Line budget checks still run before writing

**Net change:** Step 5 body grows or shrinks by at most ±3 lines.

### R3: snap/SKILL.md change-impact pre-audit step

**Path:** `skills/snap/SKILL.md`

**Current state:** 24 lines with 4 numbered steps. Reads per-project `.claude/rules/snap.md`, runs the 14-point protocol, offers maintain invocation on coverage gaps.

**Target state:** New step 3 inserted between current steps 2 and 3 (renumber existing 3 and 4 to 4 and 5). New step runs the matrix reverse-lookup against uncommitted changes:

1. **Baseline.** Run `git status --short` to list uncommitted changes (working tree + staged). This is the *only* scope: snap audits the uncommitted delta, not multi-commit history. Reason: stateless — no session tracking, no snap-local timestamp files, no "last snap" marker. If the operator committed mid-session, the pre-audit runs on the delta *since* that commit. Operators should run snap before committing for best coverage. The spec documents this tradeoff explicitly in the audit report's "Change Impact" section header ("uncommitted delta only").
2. **Filter to maintainable paths.** For each entry in `git status --short`, keep only files matching `CLAUDE.md`, `.claude/rules/*.md`, or `.claude/references/*.md`. Discard everything else.
3. **Classify each file by change type using git status flags:**
    - `A` (added) → CT-4 (rule), CT-7 (reference), or CT-9 (extension — distinguished by file format, see below)
    - `D` (deleted) → CT-6 (rule), CT-8 (reference)
    - `M` (modified) on a rules file → CT-5 (rule modified)
    - `M` (modified) on a references file → no matching CT (reference modifications are not a tracked change type in v1)
    - `M` on `CLAUDE.md` → inspect the diff to determine CT-1 (persona added, new persona entry), CT-2 (persona modified, edit to existing entry), or CT-3 (persona removed, entry deleted). Use `git diff CLAUDE.md` and look for added/removed persona header patterns.
    - `M` on `.claude/rules/workflow.md` specifically → CT-10 (pipeline change) if the diff touches phase structure; otherwise CT-5.
    - Extension file vs regular rule (CT-9 vs CT-4/CT-5): if the file contains a `## The Standard` section and follows `extension-file-guide.md` format, it's CT-9; otherwise CT-4/CT-5.
4. **Look up each change type in the matrix.** Read `maintain/references/change-impact-matrix.md`. For each row matched, enumerate the downstream effects.
5. **Flag unhandled ripples.** For each downstream file listed as affected, check whether that file also appears in `git status --short`. If not, it's a potential unhandled ripple.
6. **Report findings.** Include as a "Change Impact (uncommitted delta only)" section at the top of the audit report, before the 14-point protocol results. Phrase each flag as "potential ripple — verify," never as "you forgot to update X" (avoids false-positive fatigue).

**Line budget:** Snap SKILL.md grows from 24 to ~40–50 lines. Must stay ≤ 50 lines total. Detection rules and error handling can move to a supporting reference if they don't fit.

**Error handling:**

- Matrix file missing → skip the pre-audit step with a warning ("matrix not found, skipping change impact pre-audit"), continue with 14-point protocol
- Git command fails (not a git repo, detached HEAD with no parent, pre-initial-commit) → skip with a warning, continue with 14-point protocol
- Change type not recognized (file path matches but no classification rule applies) → skip that file with a warning, continue with remaining files

**Principle:** The matrix is additive intelligence. If the new step fails for any reason, snap's existing behavior continues unchanged. No new single point of failure.

### R4: CHANGELOG entry

**Path:** `CHANGELOG.md`

Add an entry to the current unreleased section (or create one) documenting:

- New reference: `skills/maintain/references/change-impact-matrix.md`
- `gigo:maintain` targeted-addition mode now consults the matrix for ripple effects
- `gigo:snap` now runs a change-impact pre-audit before the 14-point protocol
- Deferred for v2: matrix consultation from `restructure.md` and `upgrade-checklist.md` (they currently have their own independent review-criteria regeneration calls)
- Deferred for v2: semantic drift detection

### R5: Brief supersession

**Path:** `briefs/02-phase-selection-matrix.md`

Append a superseded note linking to this spec. Do not delete — the brief is the origin artifact and should remain as history. Format:

```markdown
---

**Superseded:** This exploratory brief was formalized into the approved design at `.claude/plans/typed-yawning-dahl.md` and spec at `docs/gigo/specs/2026-04-10-phase-selection-matrix-design.md` on 2026-04-10. See those files for the approved design.
```

## Verb Trace

Extracted from the original request. Every verb maps to a requirement.

| Verb | Requirement | Status |
|---|---|---|
| `add` / `modify` / `remove` (source column) | R1 — matrix CT-1 through CT-10 cover all add/modify/remove cases for personas, rules, references, extensions | Covered |
| `map` (change types → downstream effects) | R1 — matrix structure is 10 rows × 5 columns | Covered |
| `consult` (maintain reads the matrix) | R2 — targeted-addition Step 5 consults sibling `change-impact-matrix.md` | Covered |
| `update` (downstream files) | R1 — downstream columns enumerate updateable files; R2 — auto-run policy determines which happen without operator ask | Covered |
| `surface` (show ripple effects) | R2 — maintain reports judgment-required ripples to operator during proposal; R3 — snap reports in its audit | Covered |
| `catch` (ripples currently uncovered) | R1 — matrix covers 9 change types beyond persona-addition, which is the only one currently handled proactively | Covered |
| `refactor` (Step 5 replacement) | R2 — targeted-addition Step 5 rewritten to consult matrix | Covered |
| `query` / `reverse-lookup` (snap asks "what ripples?") | R3 — snap pre-audit step runs git diff → matrix lookup | Covered |
| `report` (matrix outputs findings) | R1 auto-run policy; R2 operator proposals; R3 snap audit reports | Covered |

No verbs dropped.

## Conventions

Decisions surfaced during design that a bare worker following this spec must preserve:

### File placement

- **Matrix file** lives at `skills/maintain/references/change-impact-matrix.md` — colocated with its primary consumer (other maintain references).
- **Consumer paths:** Maintain's `targeted-addition.md` reads it as sibling `change-impact-matrix.md`. Snap reads it as `maintain/references/change-impact-matrix.md`. Both are relative paths resolved by Claude-the-LLM against the plugin's `skills/` tree — not framework-automatic, but unambiguous from any consumer's vantage point.
- **Do not place** in `skills/gigo/references/` (that directory is for assembly-skill templates and algorithms) or `.claude/references/` (that directory is per-project, not plugin-level).

### Naming

- File is `change-impact-matrix.md`, not `phase-selection-matrix.md`. "Phase Selection Matrix" is the name of the harness pattern we took inspiration from; "Change Impact Matrix" is the GIGO-native name that describes what the file actually does. The brief and spec retain the "Phase Selection Matrix" name as the project-internal handle.
- Change type IDs use the `CT-N` prefix for stable references in future work.

### Prompt style for matrix consumers

- **Maintain** presents ripples as "here's what the matrix says may need updating" — never as "you must update." The operator is always the decision-maker on judgment cells.
- **Snap** phrases flags as "potential ripple — verify" — never as "you forgot to update X." False positives are expected; the tone must not create fatigue.
- Both tools group auto-run items (no ask) separately from judgment items (one operator prompt) in their reports.

### Report structure

- **Maintain's ripple report** appears inside its proposal, not as a separate step. The operator sees the ripple list as part of "here's what I'm planning to do."
- **Snap's change-impact report** appears at the top of the audit output, before the 14-point protocol results, labeled "Change Impact" or equivalent.

### Error handling

- **Matrix missing in maintain:** hard error. The matrix is a required dependency of `targeted-addition.md` Step 5. No fallback comment block — that would be a fourth copy of the ripple logic, defeating consolidation.
- **Matrix missing in snap:** soft degradation. Snap skips the pre-audit step with a warning and continues with the 14-point protocol. Rationale: snap's pre-audit is additive; maintain's Step 5 is load-bearing.
- Unknown change type → report "I don't recognize this change — handle manually" and proceed. Do not fail the whole operation.
- Git command failure in snap (not a git repo, pre-initial-commit, detached HEAD without a meaningful baseline) → skip pre-audit, continue with 14-point protocol.

### Boundaries (what this spec does NOT change)

- `skills/maintain/SKILL.md` — 68 lines, untouched. The matrix belongs in a reference file, not in the hub.
- `skills/maintain/references/health-check.md` — four-axis triage is unchanged. Matrix is consulted only from targeted-addition in v1.
- `skills/maintain/references/restructure.md` and `upgrade-checklist.md` — both still contain their own independent review-criteria regeneration calls. This triplication is noted as v2 consolidation work; removing it now is out of scope.
- `.claude/rules/snap.md` — the per-project snap protocol is untouched. Matrix consultation happens at the plugin level in `skills/snap/SKILL.md`, not in the per-project protocol.
- `.claude/rules/*` — no new rules files, no modifications to existing rules files.

### Dogfooding

- All writes go to `~/projects/gigo/` (source repo), never to `~/.claude/plugins/marketplaces/gigo/` (install path gets overwritten).
- The implementation is tested by dogfooding against GIGO itself — the matrix should correctly handle a persona-addition scenario before shipping.

## Scope

### In scope for v1

- The matrix reference file with all 10 change types and 5 downstream columns
- `gigo:maintain` targeted-addition consumption of the matrix (R2)
- `gigo:snap` reverse-lookup consumption of the matrix (R3)
- Auto-run vs report policy encoded in the matrix
- CHANGELOG entry
- Brief supersession note

### Out of scope for v1

- **Semantic drift detection.** "Persona quality bar mentions accessibility but review-criteria.md has no accessibility criteria" requires LLM-based content comparison. v1 is syntactic only — it maps change types to file paths, not content to content. Deferred to v2, possibly via the Challenger pattern.
- **Cross-project or cross-repo coordination.** Matrix covers intra-project ripples only.
- **Automated downstream execution for judgment-required ripples.** Matrix reports judgment items; maintain does not attempt to guess the right edit.
- **Health-check integration.** The four-axis triage in `health-check.md` does broad assessment, not change-specific. Matrix consultation is not added to health-check in v1.
- **Consolidation of `restructure.md` and `upgrade-checklist.md`.** Both currently have their own review-criteria regeneration. v1 leaves them as-is; v2 refactors both to consult the matrix, completing the consolidation.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Matrix drifts from maintain's actual behavior | Medium | Matrix is the source of truth; `targeted-addition.md` refactored to consult it, no fallback comment. The two remaining duplicates (`restructure.md`, `upgrade-checklist.md`) are flagged for v2 consolidation. |
| Snap's uncommitted-delta scope misses multi-commit sessions | Medium | Documented explicitly ("uncommitted delta only") in the report header. Operators should run snap before committing for best coverage. A stateful "since last snap" baseline is deferred to v2. |
| Snap's reverse-lookup produces false positives | Medium | Report as "potential ripple — verify," not "you forgot." Only flag when downstream file is NOT already in `git status --short`. |
| Change-type detection misclassifies CLAUDE.md edits | Medium | Use `git diff CLAUDE.md` content inspection for persona add/modify/remove — path alone is insufficient. Spec enumerates the detection rules in R3 step 3. |
| Matrix grows unwieldy as change types accumulate | Low | Reference-tier, loaded on demand. ~100–120 lines is comfortable; real change types are finite (~15 at most). |
| Path resolution breaks | Low | Matrix colocated with primary consumer. Sibling read from maintain, relative read from snap. No cross-skill framework magic. |

## Verification

- **Matrix file integrity:** After writing, the markdown table parses, all 10 change types present, all 5 columns populated, all cell values are from the defined legend.
- **Maintain integration:** Invoke `gigo:maintain` with a persona-addition scenario (dogfooded against GIGO itself). Verify Step 5 reads the matrix and the observable behavior is unchanged from before (review-criteria.md regenerated, Overwatch threshold checked, operator prompted for CLAUDE.md entry).
- **Snap reverse-lookup (uncommitted persona add):** Create a scenario with an uncommitted `CLAUDE.md` edit that adds a new persona. Invoke `gigo:snap`. Verify the change-impact pre-audit classifies it as CT-1 and flags `review-criteria.md` as a potential unhandled ripple.
- **Snap reverse-lookup (uncommitted persona remove):** Create a scenario with an uncommitted `CLAUDE.md` edit that removes an existing persona. Invoke `gigo:snap`. Verify the pre-audit classifies it as CT-3 via diff inspection (not CT-1) and flags `review-criteria.md`.
- **Path resolution:** Grep for the matrix path from both `skills/maintain/` and `skills/snap/` directories. Verify the sibling read (maintain) and relative read (snap) both resolve correctly. No absolute paths, no plugin-dir substitutions.
- **Line budgets:** Matrix ≤120 lines; `targeted-addition.md` stays within its current envelope; `snap/SKILL.md` ≤50 lines.
- **Degradation:** Rename the matrix file temporarily. Verify maintain errors loudly (hard failure — matrix is required). Verify snap degrades gracefully (warning, skips pre-audit, continues 14-point protocol).
- **Git edge cases:** Run snap in a pre-initial-commit repo, in a detached HEAD state, and with multiple uncommitted changes spanning all 10 change types. Verify each handles correctly or degrades as documented.

## Files touched

| File | Status | Why |
|---|---|---|
| `skills/maintain/references/change-impact-matrix.md` | **NEW** | The matrix itself |
| `skills/maintain/references/targeted-addition.md` | **MODIFY** | Step 5 refactored to consult matrix (no fallback comment) |
| `skills/snap/SKILL.md` | **MODIFY** | Add change-impact pre-audit step, renumber existing steps |
| `CHANGELOG.md` | **MODIFY** | Document the new capability |
| `briefs/02-phase-selection-matrix.md` | **MODIFY** | Append superseded note |

**Untouched:** `skills/maintain/SKILL.md`, `skills/maintain/references/health-check.md`, `skills/maintain/references/restructure.md`, `skills/maintain/references/upgrade-checklist.md`, `.claude/rules/snap.md`, all `.claude/rules/*.md`.

<!-- approved: spec 2026-04-10T23:08:41 by:Eaven -->
