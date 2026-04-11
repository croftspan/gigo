# Spec: Agent Teams Rebuild (Cycle 2)

**Source brief:** `.claude/plans/curious-strolling-chipmunk.md` (approved 2026-04-11T06:00:54Z by:Eaven)
**Kickoff brief:** `briefs/04-agent-teams-rebuild.md`
**Cycle:** 2 of 2 (Execution Architecture Catalog). Cycle 1 (Execution Pattern Catalog) shipped 2026-04-11.

---

## Original Request

> Cycle 2 of the Execution Architecture Catalog proposal — Part B: Agent Teams rebuild.
>
> This cycle is destructive + additive:
>
> - DESTRUCTIVE: rip out Tier 3 (Agent Teams experimental opt-in) from `skills/execute/`. Strip `skills/execute/references/review-hook.md` and the Tier 3 templates in `skills/execute/references/teammate-prompts.md`. Simplify `skills/execute/SKILL.md` to two tiers: Subagents (primary) + Inline (fallback).
> - ADDITIVE: add a new `skills/execute/references/agent-teams-design.md` — a target-state design doc (~250 lines, reference tier, loaded on demand) that blueprints how `gigo:execute` would use Claude Code's Agent Teams API when it stabilizes.
>
> Critical constraints carried from Cycle 1's fact-check: no `_workspace/` convention, qualified Phase 7 (research) references only, bare workers vs teams tension resolved by restricting teams to non-code workflows, code work stays on subagents.

---

## Problem

Tier 3 (Agent Teams experimental opt-in) shipped as a rough prototype with four documented issues: auto-claim race conditions, forced CLAUDE.md loading on team members (violating the bare-worker research finding from Phase 7 research), no session resume on crash, and higher token cost than subagents. It consumes ~40 lines of `skills/execute/SKILL.md` as "not recommended", plus a dedicated `review-hook.md` reference file, plus Tier 3 variants in `teammate-prompts.md` and `model-selection.md`. The Agent Teams API itself is still experimental in Claude Code — the current Tier 3 is premature integration.

## Goal

1. Remove Tier 3 entirely from `skills/execute/` production paths.
2. Add a reference-tier target-state design doc (`skills/execute/references/agent-teams-design.md`) that blueprints how teams would work when the API stabilizes, including the "teams for non-code only" resolution to the bare-worker research tension.
3. Fix one operator-facing stale Tier 3 reference in `README.md`.
4. Preserve historical audit trail (specs, plans, briefs referencing Tier 3 remain unchanged).

## Non-Goals

- Not implementing teams. No `TeamCreate`/`SendMessage`/`TaskCreate` calls in production paths.
- Not modifying `gigo:verify`.
- Not modifying Subagents (Tier 1) or Inline (Tier 2) behavior.
- Not editing audit trail files (`briefs/`, `docs/gigo/specs/`, `docs/gigo/plans/`, `docs/gigo/walkthroughs/`, `docs/superpowers/`).
- Not addressing README.md's unrelated skill-count drift (table lists 7 skills; project has 9).
- Not touching assembled projects' `.claude/` — plugin source only.

---

## Requirements

### R1. Delete `skills/execute/references/review-hook.md`

The entire file (98 lines, all Tier 3 hook configuration) must be deleted. No partial salvage — no content applies to Subagents or Inline tiers.

### R2. Strip Tier 3 from `skills/execute/SKILL.md`

Four distinct edits:

**R2.1. Frontmatter description.** Edit the description field in the frontmatter (line 3). Current value contains the sentence `Agent teams available as experimental opt-in.` Remove that sentence only; preserve the rest of the description unchanged. Result description:

> Execute implementation plans. Lead dispatches bare worker subagents per task, invokes gigo:verify after each, tracks progress via checkpoints. Falls back to inline if subagents unavailable. Use when you have an approved plan from gigo:blueprint.

**R2.2. Tier presentation in "Before Starting".** The section currently presents three options inside a multi-line blockquote. Remove the Tier 3 option (the third numbered bullet starting with `3. **Agent teams** (experimental opt-in)...`). After the edit, the blockquote must contain exactly two numbered options:

> 1. **Subagents** (recommended) — fresh worker per task, parallel dispatch for independent tasks, lead-managed review.
> 2. **Inline** — sequential in this session, no isolation. Good for small plans or debugging.

The **empty blockquote separator line** (a line whose content is only the `>` marker with surrounding whitespace, used inside the blockquote to create visual spacing before `> Which route?"`) must be preserved. Do NOT convert it to a true blank markdown line — doing so would break the blockquote and split the tier list from `Which route?"`. After R2.2, lines 29–34 of SKILL.md (approximately; exact line numbers may shift) should read:

```
   > "Ready to execute. Available options:
   > 1. **Subagents** (recommended) — fresh worker per task, parallel dispatch for independent tasks, lead-managed review.
   > 2. **Inline** — sequential in this session, no isolation. Good for small plans or debugging.
   >
   > Which route?"
```

**R2.3. Delete the entire Tier 3 section.** Remove everything from the `## Tier 3: Agent Teams (Experimental Opt-In)` heading through (and including) the closing `---` separator that precedes `## After Review Passes`. The `---` separator that *preceded* the Tier 3 section (between Tier 2 Inline content and the Tier 3 heading) must be preserved — it will later serve as the separator before the `## Future: Agent Teams` section added by R7.

Intermediate state after R2.3 alone (before R7): `... end of Tier 2 content` → blank → `---` → blank → `## After Review Passes`. Exactly one `---` separator sits between Tier 2 and After Review Passes at this point. R7 will then insert a new `## Future: Agent Teams` section into that gap, restoring a two-separator pattern around the new section (see R7 for exact separator placement).

**R2.4. References list cleanup (remove `review-hook.md` bullet + update `teammate-prompts.md` bullet).** In the `## References` section at the bottom of SKILL.md:

1. **Delete** the bullet that points to `references/review-hook.md` entirely.
2. **Update** the `references/teammate-prompts.md` bullet. Current content of that bullet:

```
- `references/teammate-prompts.md` — Implementation and fix prompt templates (all tiers)
```

Replace with:

```
- `references/teammate-prompts.md` — Implementation and fix prompt templates for Subagents (Inline has no template — the lead executes directly)
```

The bullets for `model-selection.md` and `checkpoint-format.md` must be preserved verbatim. R7 adds a new bullet for `agent-teams-design.md` at the end of the References list after R2.4 completes.

After R2.1–R2.4 (and after R7 adds the Future pointer section and the new References bullet), `skills/execute/SKILL.md` must contain NONE of the following strings:

- `Tier 3`
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
- `review-hook`
- `TaskCreate`
- `TaskCompleted`
- `auto-claim`
- `experimental opt-in` (case-insensitive)

The literal phrase "Agent Teams" IS allowed to appear in SKILL.md post-Cycle-2 (in the R7 Future pointer heading, body, and References bullet) — but only in those R7-added contexts. No other mention of "Agent Teams" should remain.

### R3. Strip Tier 3 from `skills/execute/references/teammate-prompts.md`

Three distinct edits. **Critical**: one block in this file must be preserved verbatim (see R3.3 preserve-block below).

**R3.1. Delete Tier 3 Teammate template.** Remove the entire `### Tier 3: Agent Team Teammate (Experimental Opt-In)` subsection including its code block, its trailing `**Note:**` paragraph, and the blank line before the next `---` separator. The `---` separator itself must be preserved (it separates `## Implementation Prompt` from `## Fix Prompt`).

**R3.2. Delete Tier 3 fix variant.** Remove the entire `### Tier 3: Agent Team (hook feedback)` subsection (header + blank + single paragraph). The `---` separator that follows must be preserved.

**R3.3. Delete only the Tier 3 rationale bullet in "Prompt Design Rationale".** In the `## Prompt Design Rationale` section, delete ONLY the final bullet:

> **Why explicit task assignment (Tier 3):** Auto-claim in agent teams lets one fast worker grab all tasks, defeating parallelism. Pre-assigning tasks to specific workers ensures parallel execution when the dependency graph allows it.

**Preserve verbatim** (this is the KEEP block):

> **Why lean prompts:** Phase 7 eval data proved that bare workers (no personas, no rules, just the task spec) perform at senior/staff level. The spec quality — not the worker context — determines output quality. Loading workers with assembled context doesn't improve their work and can degrade it.
>
> **Why full task text:** Workers should never need to read the plan file themselves. The lead extracts and provides the full task description. This eliminates file-reading overhead and ensures the worker gets exactly the context they need.
>
> **Why self-review before reporting:** Workers catch their own mistakes before the formal review runs. This reduces review-fix cycles and saves time.

**Why the KEEP block matters**: the "Why lean prompts" bullet is the Phase 7 (research) bare-worker rationale. It is foundational to the Subagents tier design — the reason Tier 1 dispatches workers without persona context. Over-stripping this block would damage Tier 1. Any worker implementing R3 must quote this KEEP block in its mental model before touching the file.

After R3.1–R3.3, `skills/execute/references/teammate-prompts.md` must contain none of the following strings: `Tier 3`, `Agent Team`, `SendMessage`, `TaskCompleted`, `auto-claim`. It must still contain the strings `Why lean prompts`, `Phase 7 eval data`, `bare workers`, `Why full task text`, and `Why self-review before reporting`.

### R4. Strip Tier 3 from `skills/execute/references/model-selection.md`

Delete the entire `## For Agent Teams (Tier 3, Opt-In)` subsection, including its team-sizing table and trailing "Start small" paragraph. The subsection begins at the `## For Agent Teams (Tier 3, Opt-In)` heading and ends at the end of the file.

After the deletion, the file must end cleanly with the "## For Review Subagents" section and its single paragraph about using sonnet for review.

After R4, `model-selection.md` must contain none of the following strings: `Tier 3`, `Agent Teams`, `teammate`, `teammates`. The `## For Review Subagents` section and its content must be preserved verbatim.

### R5. Fix `README.md` line 72 stale Tier 3 reference

Current content of line 72 (a Markdown table row in the "The Seven Skills" table):

```
| `gigo:execute` | Runs plans with agent teams. Workers get the spec, not the rules |
```

Replace with accurate wording that describes the post-Cycle-2 Subagents tier:

```
| `gigo:execute` | Runs plans by dispatching parallel subagents. Workers get the spec, not the rules |
```

The second sentence ("Workers get the spec, not the rules") must remain verbatim — it is still accurate post-rip-out. Only the first sentence is being updated. No structural changes to the README.md table itself (column count, header row, other rows all preserved). The skill-count discrepancy in the table header ("Seven Skills" vs nine actual skills) is out of scope — see Out of Scope section.

After R5, `README.md` must not contain the lowercase string `agent teams` anywhere in the file.

### R6. Create `skills/execute/references/agent-teams-design.md`

Add a new reference-tier file at `skills/execute/references/agent-teams-design.md`. Target length: **220–280 lines** (inclusive of the top-level `# Agent Teams: Target-State Design` heading and section separators).

**Range priority.** The per-section ranges in R6.2 are writing guides — if your drafts sum above 280 or below 220, the 220–280 overall target wins. Trim the least load-bearing content (or expand the most essential) to land inside the global range. Do not let per-section minimums push the file past 280, and do not let per-section maximums leave the file under 220. AC10 enforces the overall range, not per-section ranges.

**R6.1. Structure.** Nine sections, in this exact order and with these exact section headings:

1. `## Status`
2. `## Why Teams`
3. `## Decision Tree`
4. `## Team Composition`
5. `## Data-Passing Protocols`
6. `## Team Lifecycle`
7. `## Phase 7 (research) Reconciliation`
8. `## Open Questions`
9. `## Audit Trail`

(A top-level `# Agent Teams: Target-State Design` heading precedes all sections.)

**R6.2. Section content requirements.**

**§1 Status (5–10 lines).** Must contain, verbatim, all three phrases: `TARGET-STATE DESIGN`, `NOT SHIPPED`, `NOT WIRED UP`. Must list two preconditions for future implementation: (a) Claude Code Agent Teams API stability, (b) resolution of the bare-worker research tension.

**§2 Why Teams (25–35 lines).** Case for teams' potential value over subagents. Must name three mechanisms:
- Inter-agent communication (`SendMessage`)
- Shared task state visibility
- Cross-review at the team level

Must include an explicit caveat that these benefits do not apply to single-pass code generation, and that where they DO apply is non-code workflows with iterative refinement or cross-agent negotiation.

**§3 Decision Tree (35–45 lines).** A scannable decision tree. The top-level question must be `Is the task producing code?`. The code-producing (YES) branch must route to Subagents unconditionally — this is the enforcement point for the bare-worker research finding. The non-code (NO) branch then gates on a second question: `Is the Claude Code Agent Teams API stable?` If YES, route to a team; if NO, route to Subagents as a fallback. Only these two questions are required by this target-state doc. Additional operational gates (plan size, single-session requirement, etc.) are deliberately left undefined — they become concrete design decisions only when implementation begins, and adding them here without thresholds would be under-specification.

**§4 Team Composition (25–40 lines).** Must state:
- One team per execution (no mid-execution recomposition).
- Leader = the lead persona driving `gigo:execute`.
- Members mapped from `CLAUDE.md` personas.
- Known cost: Claude Code auto-loads `CLAUDE.md` onto all team members at spawn — team members are NOT bare.
- Sizing: ~5–6 tasks per member; 2–5 members per team.
- Rationale for "one team per execution": Pipeline phases that need different members fall back to Subagents, not team recomposition.

**§5 Data-Passing Protocols (25–35 lines).** Document four modes:
- **Message** (`SendMessage`): synchronous, small inter-member updates.
- **Task** (`TaskCreate` / `TaskUpdate`): persistent work-item state.
- **File** (agreed paths): large artifacts.
- **Return-value**: not applicable inside teams.

The **File mode description must include this exact sentence** (or a semantically equivalent phrasing that preserves all substantive claims):

> File-based passing means agreed file paths for large artifacts — GIGO today flows data through plan "What Was Built" addendums and git branch merges, not a dedicated workspace directory. A workspace convention could be introduced later if teams need it.

The literal string `_workspace/` may appear in this file ONLY in the context of clarifying that it is NOT a current GIGO convention.

**§6 Team Lifecycle (20–30 lines).** Must cover, in order:
- Spawn (`TeamCreate`)
- Run-phase (member-to-member communication via the four protocols in §5)
- Hook enforcement via `TaskCompleted` invoking `gigo:verify`
- Crash handling (team dies, fresh team from plan checkpoints)
- Teardown (`TeamDelete`)
- Explicit "no mid-execution recomposition" statement.

**§7 Phase 7 (research) Reconciliation (35–50 lines).** The load-bearing reconciliation section. Must state:
- The bare-worker research finding: bare workers produce better CODE than context-loaded workers.
- The platform constraint: Claude Code auto-loads `CLAUDE.md` onto all team members; teams cannot be bare.
- The resolution: **teams are for NON-CODE workflows only**. Non-code work benefits from persona context; the bare-worker research finding applies specifically to code generation.
- The future relaxation condition: if Claude Code adds selectively-bare team members, the code-producing branch in the decision tree can relax. Until then, the branch stays.

**Qualified-naming constraint (enforced here and across the whole file)**: any reference to the bare-worker research must be written as `Phase 7 (research)` or `the bare-worker research finding`. Bare `Phase 7` (without the `(research)` qualifier or a phrase like "research finding" within the same sentence) is forbidden because it would collide with the unrelated `gigo:spec` skill Phase 7 ("Operator Reviews Spec"). The section heading `## Phase 7 (research) Reconciliation` satisfies the constraint.

**§8 Open Questions (20–30 lines).** List at least four unresolved concerns that cannot be decided until the API stabilizes or more research is done:
- Selectively-bare team members
- Pre-assignment reliability (auto-claim race conditions in current experimental API)
- Crash recovery of in-flight team state
- Hook integration reliability (`TaskCompleted` with `gigo:verify`)

An optional fifth entry about non-code team sizing is permitted but not required.

**§9 Audit Trail (15–25 lines).** Must include:
- List of files that were removed or stripped in Cycle 2 (from R1–R5 and R8 of this spec — six files total: `review-hook.md` deleted, `SKILL.md`, `teammate-prompts.md`, `model-selection.md`, `README.md`, `checkpoint-format.md` stripped).
- A pointer to Cycle 2 ship date ("shipped 2026-04-11" or the actual ship date from execution).
- A `git log` hint (example: `` `git log --all --diff-filter=D -- skills/execute/references/review-hook.md` ``) that surfaces the deletion.
- Reasons for removal (the four documented issues + the Phase 7 (research) bare-worker tension).
- Pointer to source briefs: `briefs/03-execution-architecture-catalog.md`, `briefs/04-agent-teams-rebuild.md`, and this spec's path.

**R6.3. Tone.** Direct, precise. No character persona voice. Match the tone of existing `skills/execute/references/*.md` files (`checkpoint-format.md`, `model-selection.md`).

**R6.4. Reference-tier discipline.** The file is loaded on demand only, via the pointer added by R7 below. It must not be auto-loaded by SKILL.md (i.e., SKILL.md must reference it by path, not inline its contents).

### R7. Add a `Future: Agent Teams` pointer in `skills/execute/SKILL.md`

Insert a new section AFTER the `---` separator that previously preceded Tier 3 (now the separator that precedes `## After Review Passes` post-R2.3) and BEFORE the `## After Review Passes` heading. Heading: `## Future: Agent Teams`. The section must be 2–4 short lines of body text plus the heading. Exact body content (the worker may vary punctuation minimally but must preserve meaning):

> Agent Teams are not a tier. See `references/agent-teams-design.md` for the target-state design — how teams would fit when the Claude Code Agent Teams API stabilizes and the bare-worker research tension resolves. Not shipped. Not wired up.

**Separator placement.** R7 must ALSO add a new `---` separator (with surrounding blank lines) between the body of the `## Future: Agent Teams` section and the `## After Review Passes` heading, so the final state matches the rest of SKILL.md's section-separator convention. Final layout:

```
... end of Tier 2: Inline content
(blank line)
---                                                     ← preserved from pre-R2.3 state
(blank line)
## Future: Agent Teams

Agent Teams are not a tier. See `references/agent-teams-design.md` ...
(blank line)
---                                                     ← NEW, added by R7
(blank line)
## After Review Passes
```

The pointer section must not describe what teams do — its job is to redirect curious readers to the design doc.

**References list bullet.** In the `## References` section at the bottom of SKILL.md (where R2.4 removed the `review-hook.md` bullet), add a new bullet at the end of the References list, after the `checkpoint-format.md` bullet. Content:

```
- `references/agent-teams-design.md` — Target-state design doc. Not shipped, not wired up. Loaded on demand when a reader follows the Future pointer.
```

### R8. Strip Tier 3 from `skills/execute/references/checkpoint-format.md`

This file was missed in the original brief's file-scope and surfaced by the spec-review Challenger. It contains three distinct Tier 3 artifacts that must be removed so AC17's Tier 3 coverage grep stays clean. R8 has three sub-edits.

**R8.1. Update the `tier` field row in the Fields table.** The table currently contains the row:

```
| `tier` | `1`, `2`, `3` | Which execution tier was running |
```

Replace the values column to drop `3`:

```
| `tier` | `1`, `2` | Which execution tier was running |
```

The `Field`, `Values`, and `Purpose` column headers are preserved verbatim; only the values cell of the `tier` row changes. The checkpoint example blocks earlier in the file (which use `tier=1` and `tier=2` only) are preserved verbatim — no `tier=3` appears in any example block.

**R8.2. Delete the `### Agent Teams (Tier 3, if used)` subsection under `## Reconciliation on Resume`.** The section `## Reconciliation on Resume` currently contains a single paragraph about the primary execution path followed by a subsection `### Agent Teams (Tier 3, if used)` with a 5-item numbered list about shared-task-list reconciliation. Remove the entire `### Agent Teams (Tier 3, if used)` subsection: the `###` heading, the blank line, the introductory sentence, the numbered list, and any trailing blank line up to the next top-level section heading.

After deletion, `## Reconciliation on Resume` contains only its opening paragraph ("For the primary execution path (subagents and inline), there's no shared state to reconcile. Checkpoints in the plan file are the sole source of truth. The lead reads them and picks up where it left off.") and then flows directly into `## Edge Cases`.

**R8.3. Delete the `**Agent teams race window (Tier 3 only):**` edge case from `## Edge Cases`.** The `## Edge Cases` section is a sequence of bold-prefixed paragraphs. Remove the entire paragraph whose first line begins with `**Agent teams race window (Tier 3 only):**`. The deletion covers the bold-prefixed line and all continuation lines through (but not including) the next `**` bullet. The surrounding edge cases must be preserved verbatim:

- `**Partial checkpoint (crash mid-write):**` — appears before the deleted paragraph; preserved.
- `**Operator decided, worker implementing:**` — appears after the deleted paragraph; preserved.

After R8.1–R8.3, `skills/execute/references/checkpoint-format.md` must contain none of the following strings:

- `Tier 3`
- `Agent Teams` (case-insensitive)
- `agent teams` (the lowercase phrase also occurs in the race-window edge case)
- `shared task list` (only appeared inside the deleted subsection)

The file must still contain the strings `Reconciliation on Resume`, `Edge Cases`, `Partial checkpoint`, and `Operator decided` (these mark the load-bearing structure that survives R8).

---

## Architecture

### File layout after Cycle 2

```
skills/execute/
├── SKILL.md                              ← modified (R2, R7)
└── references/
    ├── agent-teams-design.md             ← NEW (R6, 220–280 lines)
    ├── checkpoint-format.md              ← modified (R8)
    ├── model-selection.md                ← modified (R4)
    ├── review-hook.md                    ← DELETED (R1)
    └── teammate-prompts.md               ← modified (R3)
```

### Read path during `/execute` post-Cycle-2

1. Operator invokes `/execute` on an approved plan.
2. SKILL.md's "Before Starting" section presents two tier options (was three).
3. Operator picks Subagents (default for 3+ tasks) or Inline (default for 1–2 tasks).
4. SKILL.md routes through the chosen tier.
5. If the operator asks about Agent Teams: the `## Future: Agent Teams` pointer directs them to `references/agent-teams-design.md`.
6. The design doc is reference-tier — loaded on demand when the pointer fires, not auto-loaded on every `/execute` invocation.

### Execution pattern for Cycle 2 itself (for the plan phase)

**Fan-out/Fan-in** (from Cycle 1's execution-patterns catalog). The rip-out wave fans out six tasks in parallel:

- **One SKILL.md task** batching R2.1, R2.2, R2.3, R2.4, and R7 together (all five edits touch the same file and cannot parallelize within that file; they must run in a single task).
- **R1**: delete `skills/execute/references/review-hook.md`.
- **R3**: strip `skills/execute/references/teammate-prompts.md`.
- **R4**: strip `skills/execute/references/model-selection.md`.
- **R5**: fix `README.md` line 72.
- **R8**: strip `skills/execute/references/checkpoint-format.md`.

R6 (design doc creation) runs sequentially AFTER the rip-out wave completes — the design doc's §9 Audit Trail references the files removed or stripped in the rip-out wave, so it needs the wave's commits to exist. A verification sweep fans in at the end.

---

## Conventions

### Tier 3 string coverage

After Cycle 2 ships, this grep:

```bash
grep -rn "Tier 3\|CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS\|review-hook\|auto-claim\|TeamCreate\|TaskCompleted" \
  ~/projects/gigo/skills/ \
  ~/projects/gigo/README.md \
  ~/projects/gigo/CLAUDE.md
```

must return matches **only** in `skills/execute/references/agent-teams-design.md`. No other file under `skills/`, `README.md`, or `CLAUDE.md` may match any of those strings.

**Why these strings and not `Agent Teams` generally:** The literal phrase "Agent Teams" legitimately appears post-Cycle-2 in SKILL.md's `## Future: Agent Teams` pointer section and References bullet (per R7) — those are intentional pointers to the new design doc, not stale Tier 3 content. Searching for the generic phrase would produce false positives. The six strings above are specific to Tier 3 *implementation*:

- `Tier 3` — the literal tier label; appears in the design doc's §9 Audit Trail (allowed).
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` — the experimental env var; should not appear outside the design doc.
- `review-hook` — the deleted file name; may appear in the design doc's §9 Audit Trail (allowed).
- `auto-claim` — Tier 3 race-condition term; appears in the design doc's §8 Open Questions (allowed).
- `TeamCreate`, `TaskCompleted` — API names; appear in the design doc's §5/§6 lifecycle coverage (allowed).

Audit trail files (`briefs/`, `docs/`, `.claude/plans/`) are excluded — they preserve historical state and are intentionally left unchanged.

### Preservation of bare-worker rationale

After Cycle 2, `grep -n "bare workers" skills/execute/references/teammate-prompts.md` must still return the `Phase 7 eval data proved that bare workers` rationale bullet. The phrase `bare workers` in the `Why lean prompts:` bullet is load-bearing for the Subagents tier's design justification.

### Qualified Phase 7 references

In `skills/execute/references/agent-teams-design.md`, every literal string `Phase 7` must be qualified. The qualifier options are:
- `Phase 7 (research)` — direct qualifier
- `bare-worker research finding` — semantic substitute

Unqualified `Phase 7` (for example, a sentence like "see Phase 7 for background") is forbidden in this file. The section heading `## Phase 7 (research) Reconciliation` is itself qualified and satisfies the rule for readers entering that section.

### No new `_workspace/` convention

The design doc's §5 Data-Passing Protocols must explicitly state that GIGO does NOT use a `_workspace/` convention. Data flows through plan "What Was Built" addendums and git branch merges. The literal string `_workspace/` may appear in this file only in the context of clarifying its non-existence.

### Reference-tier line discipline

`skills/execute/references/agent-teams-design.md` target: **220–280 lines**. Under-length (<220) means the design is under-specified; over-length (>280) means the file is bloated. The file is reference-tier — it does not pay auto-load token cost, but discipline still applies.

### Voice

New content written in direct, precise voice matching existing `skills/execute/references/*.md` files. No character persona. Use "we" sparingly, referring to the GIGO project collectively.

### File deletion via git

The file deletion in R1 (`skills/execute/references/review-hook.md`) must use a method that produces a clean `git log --diff-filter=D` entry — i.e., `git rm` or equivalent. Do not leave the file as an empty file or a stub.

---

## Boundaries

- **`skills/execute/SKILL.md` ↔ reference files**: SKILL.md points to reference files via relative paths (`references/<filename>.md`). Reference files do not reference SKILL.md back.
- **`skills/spec/references/execution-patterns.md` (Cycle 1) ↔ `skills/execute/references/agent-teams-design.md` (Cycle 2)**: both live in reference tier but in different skills (`spec/references/` vs `execute/references/`). They describe different concerns — execution patterns are plan-level vocabulary for the planner; agent teams are execute-tier dispatch mechanisms. No cross-linking required.
- **`teammate-prompts.md` Prompt Design Rationale ↔ Subagents (Tier 1) design**: the rationale bullets (especially `Why lean prompts`) are the load-bearing justification for Tier 1's bare-worker design. Over-stripping this section would damage the Subagents tier.
- **`README.md` ↔ operator-facing descriptions**: the README describes user-visible skill behavior. R5 brings one table row into alignment with post-Cycle-2 behavior. Other README drift (skill count, etc.) is not in scope.

---

## Acceptance Criteria

### AC1. `review-hook.md` deleted
- The file `skills/execute/references/review-hook.md` does not exist.
- `git log --all --diff-filter=D -- skills/execute/references/review-hook.md` returns a deletion commit.

### AC2. SKILL.md frontmatter cleaned (R2.1)
- The frontmatter description field in `skills/execute/SKILL.md` does not contain the substring `Agent teams`.
- The rest of the description (sentences about dispatching bare worker subagents, invoking gigo:verify, checkpoints, the inline fallback, and the gigo:blueprint handoff) is preserved verbatim except for removal of the Tier 3 sentence.

### AC3. Two-tier presentation (R2.2)
- The "Before Starting" section in `skills/execute/SKILL.md` offers exactly two numbered tier options: Subagents (1) and Inline (2). There is no option 3.
- The substring `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` does not appear anywhere in `skills/execute/SKILL.md`.

### AC4. Tier 3 section removed (R2.3)
- `skills/execute/SKILL.md` contains no heading matching the regex `^## Tier 3`.
- No `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, no `TaskCompleted`, no `auto-claim`, no `review-hook` substring remains in SKILL.md after R2.3 (these are all checked by AC17's grep too — this AC double-checks within SKILL.md specifically).
- In the final post-R7 state, the structure between the end of Tier 2 Inline content and `## After Review Passes` is: `---` separator, blank line, `## Future: Agent Teams` heading and body, blank line, `---` separator, blank line, `## After Review Passes`. (Two separators wrapping the Future section — this is the final state, not the intermediate R2.3-only state.)

### AC5. References list updated (R2.4 + R7)
- `skills/execute/SKILL.md`'s `## References` section does NOT include any bullet pointing to `review-hook.md`.
- `skills/execute/SKILL.md`'s `## References` section DOES include a bullet for `agent-teams-design.md` (added by R7).
- The `teammate-prompts.md` bullet was updated per R2.4 — it no longer contains the parenthetical `(all tiers)`. It now describes Subagents-only template coverage with the Inline clarification.
- The bullets for `model-selection.md` and `checkpoint-format.md` are preserved verbatim (no changes to those bullets).

### AC6. Tier 3 template removed from teammate-prompts.md (R3.1 + R3.2)
- `skills/execute/references/teammate-prompts.md` contains no heading matching the regex `^### Tier 3`.
- `teammate-prompts.md` does not contain the strings `SendMessage`, `TaskCompleted`, `auto-claim`, or `Agent Team`.

### AC7. Preserve block preserved verbatim (R3.3 KEEP block)
- `teammate-prompts.md` contains the verbatim phrase `Phase 7 eval data proved that bare workers`.
- `teammate-prompts.md` contains the verbatim phrase `Why full task text`.
- `teammate-prompts.md` contains the verbatim phrase `Why self-review before reporting`.
- `teammate-prompts.md` does NOT contain the phrase `Why explicit task assignment (Tier 3)`.

### AC8. Tier 3 section removed from model-selection.md (R4)
- `skills/execute/references/model-selection.md` contains no heading matching the regex `^## For Agent Teams`.
- `model-selection.md` does not contain the strings `teammate` or `teammates`.
- `model-selection.md` ends with the `## For Review Subagents` section content (the sonnet paragraph).

### AC9. README.md line 72 fixed (R5)
- `README.md` does not contain the string `agent teams` (case-insensitive match) anywhere in the file.
- The `gigo:execute` row in `README.md`'s skill table uses the word `subagents` to describe what the skill does.

### AC10. New design doc exists with required length (R6)
- The file `skills/execute/references/agent-teams-design.md` exists.
- Line count is in the range 220–280 (inclusive).

### AC11. Design doc section structure (R6.1)
- `agent-teams-design.md` contains all nine required section headings, in order:
  1. `## Status`
  2. `## Why Teams`
  3. `## Decision Tree`
  4. `## Team Composition`
  5. `## Data-Passing Protocols`
  6. `## Team Lifecycle`
  7. `## Phase 7 (research) Reconciliation`
  8. `## Open Questions`
  9. `## Audit Trail`

### AC12. Status banner is unambiguous (R6.2 §1)
- `agent-teams-design.md` §1 (Status) contains verbatim all three phrases: `TARGET-STATE DESIGN`, `NOT SHIPPED`, `NOT WIRED UP`.
- §1 names two preconditions for future implementation (API stability and bare-worker research tension resolution).

### AC13. Decision tree code-producing branch (R6.2 §3)
- §3 (Decision Tree) contains the exact question `Is the task producing code?` (or a close paraphrase that preserves the question form and "producing code" language).
- The code-producing (YES) branch routes unambiguously to Subagents.

### AC14. Data-passing `_workspace/` clarification (R6.2 §5)
- §5 (Data-Passing Protocols) contains the required clarification sentence (or semantic equivalent): "GIGO today flows data through plan 'What Was Built' addendums and git branch merges, not a dedicated workspace directory."
- The literal string `_workspace/` appears in `agent-teams-design.md` ONLY in the context of this non-convention clarification (not as a claimed GIGO pattern).

### AC15. Qualified Phase 7 references (R6.2 §7, convention)
- Every occurrence of the substring `Phase 7` in `agent-teams-design.md` is either:
  - Immediately followed by `(research)`, OR
  - Appears within a sentence that also uses the phrase `bare-worker research finding` or `research finding`.
- Unqualified bare `Phase 7` (as in "see Phase 7 for context") does not appear anywhere in the file.

### AC16. Future pointer in SKILL.md (R7)
- `skills/execute/SKILL.md` contains a `## Future: Agent Teams` section between the Inline tier section and the `## After Review Passes` section.
- The Future section body is a single short paragraph (2–4 rendered lines) and points to `references/agent-teams-design.md`.
- The Future section does not describe the team mechanism — it only redirects.
- A new `---` separator exists between the end of the Future section body and the `## After Review Passes` heading (per R7's separator placement diagram).
- `skills/execute/SKILL.md`'s `## References` list contains a bullet for `agent-teams-design.md` (added by R7) at the end of the list.

### AC17. Verification grep is clean (global convention)
- Running the Tier 3 coverage grep from the Conventions section returns matches ONLY in `skills/execute/references/agent-teams-design.md`. Zero matches in any other file under `skills/`, `README.md`, or `CLAUDE.md`.

### AC18. `checkpoint-format.md` cleaned (R8)
- `skills/execute/references/checkpoint-format.md` contains no heading matching the regex `^### Agent Teams`.
- The file contains no `**Agent teams race window` substring.
- The file does not contain the strings `Tier 3`, `shared task list`, or the phrase `agent teams` (case-insensitive).
- The `tier` field row of the Fields table has values column `` `1`, `2` `` — no `3`.
- The file still contains the strings `Reconciliation on Resume`, `Edge Cases`, `Partial checkpoint`, and `Operator decided` (load-bearing structure preserved).

### AC19. Why Teams section names three mechanisms (R6.2 §2)
- `agent-teams-design.md` §2 body contains all three: `SendMessage` (or `Message` protocol language), `shared task` (or `task state visibility`), and `cross-review` (or equivalent phrase naming review at the team level).
- §2 contains an explicit caveat that these benefits do NOT apply to single-pass code generation (grep for a phrase like `does not apply` or `do not apply` or `not for code`).

### AC20. Team Composition load-bearing claims (R6.2 §4)
- §4 contains the phrase `one team per execution` (or close paraphrase like `one team per execute run`).
- §4 contains the phrase `auto-loads` and `CLAUDE.md` in the same paragraph, naming the cost.
- §4 contains the explicit statement that team members are NOT bare (look for `not bare`, `NOT bare`, or `cannot be bare`).
- §4 names the leader as the lead persona from `gigo:execute` (or equivalent).

### AC21. Team Lifecycle names load-bearing primitives (R6.2 §6)
- §6 contains all five of: `TeamCreate`, `TaskCompleted`, `TeamDelete`, `crash`, and a phrase meaning `no mid-execution recomposition` (e.g., `no recomposition` or `cannot be recomposed`).

### AC22. Open Questions has at least four items (R6.2 §8)
- §8 contains at least 4 bulleted or numbered items.
- §8 names at minimum: `selectively-bare` (or `selectively bare`), `auto-claim` (or `pre-assignment`), `crash recovery` (or `crash` with `recovery`), and `hook integration`.

### AC23. Audit Trail completeness (R6.2 §9)
- §9 lists all six files touched by Cycle 2: `review-hook.md`, `SKILL.md`, `teammate-prompts.md`, `model-selection.md`, `README.md`, and `checkpoint-format.md`.
- §9 contains a `git log` command example (search for `git log`).
- §9 points to `briefs/03-execution-architecture-catalog.md`, `briefs/04-agent-teams-rebuild.md`, and the path of this spec file.

### AC24. Reference-tier discipline (R6.4)
- `skills/execute/SKILL.md` does NOT contain the substring `TARGET-STATE DESIGN` (the sentinel phrase that appears only in `agent-teams-design.md` §1 Status). If SKILL.md contains that phrase, the design doc content was inlined rather than referenced by pointer, violating the reference-tier contract.
- `skills/execute/SKILL.md` DOES contain the path `references/agent-teams-design.md` (the pointer from R7).

---

## Out of Scope

- `CHANGELOG.md` — auto-generated by `gigo:execute` after task completion.
- Walkthrough file for Cycle 2 (`docs/gigo/walkthroughs/2026-04-11-agent-teams-rebuild.md` or similar) — will be created separately after execute completes, per operator preference.
- `README.md` skill-count drift (table lists 7 skills; project has 9 skills `gigo`, `gigo:blueprint`, `gigo:spec`, `gigo:execute`, `gigo:verify`, `gigo:sweep`, `gigo:snap`, `gigo:retro`, `gigo:maintain`) — separate maintenance concern, not Tier 3 related.
- Any implementation of Agent Teams — this spec is destructive rip-out + reference-tier design doc only.
- `gigo:verify` changes.
- `gigo:spec` changes.
- `gigo:sweep` changes.
- `gigo:snap` changes.
- Subagents (Tier 1) or Inline (Tier 2) behavioral changes — both stay as-is post-Cycle-2.
- Assembled projects' `.claude/` — plugin source only.
- Audit trail files (`briefs/`, `docs/gigo/specs/`, `docs/gigo/plans/`, `docs/gigo/walkthroughs/`, `docs/superpowers/`, `.claude/plans/`) — historical record, intentionally preserved.

---

## Verb Trace

Action verbs extracted from the Original Request, traced to requirements:

| Verb | Requirement | Status |
|---|---|---|
| rip out (Tier 3 from `skills/execute/`) | R1, R2, R3, R4, R8 | ✅ |
| strip (`review-hook.md`) | R1 (full file delete) | ✅ |
| strip (Tier 3 templates in `teammate-prompts.md`) | R3 | ✅ |
| strip (Tier 3 content in `checkpoint-format.md`) | R8 (three sub-edits — Challenger-discovered) | ✅ |
| simplify (`SKILL.md` to two tiers) | R2 (four sub-edits) + R7 (Future pointer completes the simplification story by redirecting curious readers to the design doc) | ✅ |
| add (new `agent-teams-design.md`) | R6 | ✅ |
| blueprint (how `gigo:execute` would use Agent Teams API) | R6 (nine-section target-state doc) | ✅ |
| fix (stale Tier 3 reference in README, per brief's Phase 2 clarifying question) | R5 | ✅ |
| preserve (Phase 7 research rationale) | R3.3 KEEP block + convention + AC7 | ✅ |
| preserve (audit trail) | Non-Goals + Out of Scope + Conventions | ✅ |

**Derived-from-design requirements** (not strict verbs, but called out in the brief's Phase 4 design):
| Design element | Requirement | Rationale |
|---|---|---|
| `## Future: Agent Teams` pointer in SKILL.md | R7 | The brief's Phase 4 specifies this pointer so operators who remember Tier 3 can find the design doc; it's the "additive" half of the simplification story. |
| References list bullet for `agent-teams-design.md` | R7 | Consistency with SKILL.md's existing References section format. |

No unresolved verb gaps.
