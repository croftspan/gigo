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
    - `M` on a rules file containing `## The Standard` → CT-9 (extension modification); on `workflow.md` with phase-structure edits → CT-10; on any other rules file → CT-5
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
