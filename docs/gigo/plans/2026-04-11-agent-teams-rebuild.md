# Agent Teams Rebuild — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-11-agent-teams-rebuild-design.md`

**Design brief:** `~/.claude/plans/curious-strolling-chipmunk.md` (approved 2026-04-11T06:00:54Z by:Eaven)

**Cycle:** 2 of 2 — Execution Architecture Catalog, Part B (Agent Teams Rebuild)

**Goal:** Rip Tier 3 (Agent Teams experimental opt-in) out of `skills/execute/` and replace it with a reference-tier target-state design doc, plus one `README.md` fix. Non-destructive to Tier 1 (Subagents) and Tier 2 (Inline) behavior.

**Execution Pattern:** Fan-out/Fan-in

**Architecture:** Six rip-out tasks fan out in parallel (one batched SKILL.md task + five independent file operations). A sequential design-doc creation task (Task 7) runs after the rip-out wave completes — its §9 Audit Trail references the removed files. A verification sweep (Task 8) fans in at the end, running all 24 acceptance criteria from the spec.

**Tech Stack:** Markdown edits; `git rm` for one file deletion; Grep for verification.

---

## Notes for implementers

**Critical preserve-block (Task 3):** `skills/execute/references/teammate-prompts.md` lines containing the `**Why lean prompts:**`, `**Why full task text:**`, and `**Why self-review before reporting:**` bullets MUST NOT be touched. They are the Phase 7 (research) bare-worker rationale — load-bearing for Tier 1 design. Task 3 has explicit preserve-block instructions; read them twice before editing.

**Parallel file coverage:** Tasks 1–6 all fan out in one wave. Task 1 batches SKILL.md edits (R2.1, R2.2, R2.3, R2.4, R7) because they all touch one file and cannot parallelize within it. Tasks 2–6 each touch a different file and genuinely parallelize.

**Model selection guidance:** Tasks 2, 4, 5, 6 are mechanical strips suitable for haiku. Tasks 1, 3, 7, 8 are integration-grade and should use sonnet. None require opus.

---

### Task 1: SKILL.md — strip Tier 3 and add Future pointer (R2.1, R2.2, R2.3, R2.4, R7)

**blocks:** 7
**blocked-by:** []
**parallelizable:** true (with Tasks 2, 3, 4, 5, 6)

**Files:**
- Modify: `skills/execute/SKILL.md`

**Model:** sonnet (structural edits to a 225-line SKILL.md; ordering matters)

**Context for the worker:** This task implements five sub-requirements (R2.1, R2.2, R2.3, R2.4, R7) from the spec. Apply them in the order below. Edits are structural — preserve all surrounding content verbatim except where explicitly changed.

- [ ] **Step 1: Read SKILL.md to establish baseline.**

Run: `wc -l skills/execute/SKILL.md`
Expected: ~225 lines.

Read the full file once before editing. Confirm the following landmarks exist:
- Line ~3: frontmatter `description:` field containing `Agent teams available as experimental opt-in.`
- Line ~32: tier presentation blockquote with third numbered bullet `3. **Agent teams** (experimental opt-in) — ...`
- Line ~131: `---` separator preceding `## Tier 3: Agent Teams (Experimental Opt-In)`
- Line ~133: `## Tier 3: Agent Teams (Experimental Opt-In)` heading
- Line ~155: `---` separator preceding `## After Review Passes`
- Line ~222: `## References` section bullet `- \`references/teammate-prompts.md\` — Implementation and fix prompt templates (all tiers)`
- Line ~224: `## References` section bullet `- \`references/review-hook.md\` — TaskCompleted hook configuration (agent teams only)`

- [ ] **Step 2: Apply R2.1 — frontmatter description.**

In the frontmatter `description:` field (line ~3), remove exactly the sentence `Agent teams available as experimental opt-in.` Preserve all other description content verbatim. The sentence may be preceded or followed by a space — collapse any resulting double-space to a single space so the description reads cleanly.

Final description value (verbatim):
> Execute implementation plans. Lead dispatches bare worker subagents per task, invokes gigo:verify after each, tracks progress via checkpoints. Falls back to inline if subagents unavailable. Use when you have an approved plan from gigo:blueprint.

- [ ] **Step 3: Apply R2.2 — tier presentation in "Before Starting".**

In the "Before Starting" section, the tier presentation is a multi-line blockquote containing three numbered bullets. Remove the third bullet (`3. **Agent teams** (experimental opt-in) — full parallelization via shared task list, hook-enforced review. Requires \`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS\`.`).

**Preserve the empty blockquote separator line** (a line whose content is only `   >` with surrounding whitespace) that sits between the tier list and `> Which route?"`. Do NOT convert it to a true blank markdown line — doing so would break the blockquote.

Target final block:
```
   > "Ready to execute. Available options:
   > 1. **Subagents** (recommended) — fresh worker per task, parallel dispatch for independent tasks, lead-managed review.
   > 2. **Inline** — sequential in this session, no isolation. Good for small plans or debugging.
   >
   > Which route?"
```

- [ ] **Step 4: Apply R2.3 — delete the `## Tier 3: Agent Teams (Experimental Opt-In)` section.**

Delete everything from the `## Tier 3: Agent Teams (Experimental Opt-In)` heading (line ~133) through (and including) the closing `---` separator that precedes `## After Review Passes` (line ~155).

**PRESERVE** the `---` separator that PRECEDED the Tier 3 section (line ~131). This separator stays and becomes the separator before the new `## Future: Agent Teams` section added in Step 6.

Intermediate state after Step 4 (before Step 6): `... end of Tier 2: Inline content → blank line → ---  → blank line → ## After Review Passes`. Exactly one `---` separator between Tier 2 and After Review Passes at this point.

- [ ] **Step 5: Apply R2.4 — References list cleanup.**

In the `## References` section at the bottom of SKILL.md:

1. **Delete** the bullet pointing to `references/review-hook.md` entirely: `- \`references/review-hook.md\` — TaskCompleted hook configuration (agent teams only)`.

2. **Update** the bullet pointing to `references/teammate-prompts.md`. Replace the current bullet:

```
- `references/teammate-prompts.md` — Implementation and fix prompt templates (all tiers)
```

with:

```
- `references/teammate-prompts.md` — Implementation and fix prompt templates for Subagents (Inline has no template — the lead executes directly)
```

The bullets for `model-selection.md` and `checkpoint-format.md` must be preserved verbatim.

- [ ] **Step 6: Apply R7 — add `## Future: Agent Teams` section and a new `---` separator.**

Insert a new section between the preserved `---` (from Step 4) and `## After Review Passes`. Final layout (exact structure):

```
... end of Tier 2: Inline content
(blank line)
---                                                     ← preserved from Step 4
(blank line)
## Future: Agent Teams

Agent Teams are not a tier. See `references/agent-teams-design.md` for the target-state design — how teams would fit when the Claude Code Agent Teams API stabilizes and the bare-worker research tension resolves. Not shipped. Not wired up.
(blank line)
---                                                     ← NEW, added by this step
(blank line)
## After Review Passes
```

Then, in the `## References` section (where Step 5 removed the `review-hook.md` bullet), add a new bullet at the end of the list (after the `checkpoint-format.md` bullet):

```
- `references/agent-teams-design.md` — Target-state design doc. Not shipped, not wired up. Loaded on demand when a reader follows the Future pointer.
```

- [ ] **Step 7: Verify — SKILL.md string coverage.**

Run the following greps and confirm each returns zero matches in `skills/execute/SKILL.md`:

```bash
grep -n "Tier 3" skills/execute/SKILL.md
grep -n "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" skills/execute/SKILL.md
grep -n "review-hook" skills/execute/SKILL.md
grep -n "TaskCreate" skills/execute/SKILL.md
grep -n "TaskCompleted" skills/execute/SKILL.md
grep -n "auto-claim" skills/execute/SKILL.md
grep -ni "experimental opt-in" skills/execute/SKILL.md
```

Expected: zero matches for every grep.

Run:
```bash
grep -n "Future: Agent Teams" skills/execute/SKILL.md
grep -n "references/agent-teams-design.md" skills/execute/SKILL.md
```

Expected: at least one match each (the new pointer and the References bullet).

- [ ] **Step 8: Commit.**

```bash
git add skills/execute/SKILL.md
git commit -m "refactor(execute): strip Tier 3 from SKILL.md, add Future pointer (R2+R7)"
```

---

### Task 2: Delete `review-hook.md` (R1)

**blocks:** 7
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 3, 4, 5, 6)

**Files:**
- Delete: `skills/execute/references/review-hook.md`

**Model:** haiku (mechanical file deletion)

- [ ] **Step 1: Confirm file exists and is 98 lines.**

Run: `wc -l skills/execute/references/review-hook.md`
Expected: `98 skills/execute/references/review-hook.md`.

- [ ] **Step 2: Delete the file using `git rm`.**

```bash
git rm skills/execute/references/review-hook.md
```

Do NOT use `rm` alone or leave an empty file. The deletion must produce a clean `git log --diff-filter=D` entry (per the spec's Conventions section "File deletion via git").

- [ ] **Step 3: Verify deletion.**

```bash
test ! -e skills/execute/references/review-hook.md && echo OK
```

Expected: `OK`.

- [ ] **Step 4: Commit.**

```bash
git commit -m "refactor(execute): delete review-hook.md (R1, Tier 3 cleanup)"
```

---

### Task 3: Strip Tier 3 from `teammate-prompts.md` (R3)

**blocks:** 7
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 4, 5, 6)

**Files:**
- Modify: `skills/execute/references/teammate-prompts.md`

**Model:** sonnet (three sub-edits + critical preserve block, over-strip risk)

**CRITICAL — preserve block.** Before touching this file, locate these three bullets in the `## Prompt Design Rationale` section and memorize them. They MUST NOT be deleted or modified:

> **Why lean prompts:** Phase 7 eval data proved that bare workers (no personas, no rules, just the task spec) perform at senior/staff level. The spec quality — not the worker context — determines output quality. Loading workers with assembled context doesn't improve their work and can degrade it.
>
> **Why full task text:** Workers should never need to read the plan file themselves. The lead extracts and provides the full task description. This eliminates file-reading overhead and ensures the worker gets exactly the context they need.
>
> **Why self-review before reporting:** Workers catch their own mistakes before the formal review runs. This reduces review-fix cycles and saves time.

These bullets are foundational to the Subagents (Tier 1) design — they are NOT Tier 3 content and must survive this task untouched. AC7 verifies they are still present after Task 3.

- [ ] **Step 1: Read teammate-prompts.md to establish baseline.**

Run: `wc -l skills/execute/references/teammate-prompts.md`
Expected: ~150 lines.

Confirm these landmarks exist:
- `### Tier 3: Agent Team Teammate (Experimental Opt-In)` heading (around line 54)
- `### Tier 3: Agent Team (hook feedback)` heading (around line 136)
- The three KEEP bullets from the CRITICAL block above (around lines 144–148)
- `**Why explicit task assignment (Tier 3):**` bullet (around line 150)

- [ ] **Step 2: Apply R3.1 — delete the `### Tier 3: Agent Team Teammate` subsection.**

Delete everything from the `### Tier 3: Agent Team Teammate (Experimental Opt-In)` heading through (and including) its code block, its trailing `**Note:**` paragraph, and the blank line before the next `---` separator. The `---` separator itself must be preserved (it separates `## Implementation Prompt` from `## Fix Prompt`).

- [ ] **Step 3: Apply R3.2 — delete the `### Tier 3: Agent Team (hook feedback)` subsection.**

Delete the entire `### Tier 3: Agent Team (hook feedback)` subsection: the `###` heading, the blank line, and the single paragraph that follows. The `---` separator after this subsection must be preserved.

- [ ] **Step 4: Apply R3.3 — delete ONLY the "Why explicit task assignment (Tier 3)" bullet.**

In the `## Prompt Design Rationale` section, delete ONLY this bullet:

> **Why explicit task assignment (Tier 3):** Auto-claim in agent teams lets one fast worker grab all tasks, defeating parallelism. Pre-assigning tasks to specific workers ensures parallel execution when the dependency graph allows it.

**DO NOT** delete any of the three KEEP bullets listed in the CRITICAL block at the top of this task. They are NOT Tier 3 content.

- [ ] **Step 5: Verify preserve block survived.**

```bash
grep -n "Why lean prompts" skills/execute/references/teammate-prompts.md
grep -n "Phase 7 eval data" skills/execute/references/teammate-prompts.md
grep -n "bare workers" skills/execute/references/teammate-prompts.md
grep -n "Why full task text" skills/execute/references/teammate-prompts.md
grep -n "Why self-review before reporting" skills/execute/references/teammate-prompts.md
```

Expected: at least one match for EACH grep. If any grep returns zero matches, the preserve block was damaged — restore from git (`git checkout skills/execute/references/teammate-prompts.md`) and retry the task more carefully.

- [ ] **Step 6: Verify forbidden strings removed.**

```bash
grep -n "Tier 3" skills/execute/references/teammate-prompts.md
grep -n "Agent Team" skills/execute/references/teammate-prompts.md
grep -n "SendMessage" skills/execute/references/teammate-prompts.md
grep -n "TaskCompleted" skills/execute/references/teammate-prompts.md
grep -n "auto-claim" skills/execute/references/teammate-prompts.md
```

Expected: zero matches for each grep.

- [ ] **Step 7: Commit.**

```bash
git add skills/execute/references/teammate-prompts.md
git commit -m "refactor(execute): strip Tier 3 from teammate-prompts.md (R3), preserve Phase 7 research rationale"
```

---

### Task 4: Strip Tier 3 from `model-selection.md` (R4)

**blocks:** 7
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 3, 5, 6)

**Files:**
- Modify: `skills/execute/references/model-selection.md`

**Model:** haiku (mechanical section deletion at end of file)

- [ ] **Step 1: Read model-selection.md to confirm the target.**

Run: `wc -l skills/execute/references/model-selection.md`
Expected: 42 lines.

Confirm line 31 is `## For Agent Teams (Tier 3, Opt-In)` and line 27 contains `## For Review Subagents`.

- [ ] **Step 2: Delete the `## For Agent Teams (Tier 3, Opt-In)` section.**

Delete lines 31 through 42 inclusive (the `## For Agent Teams (Tier 3, Opt-In)` heading and its entire body — table and trailing "Start small" paragraph). The file should end cleanly at the end of the `## For Review Subagents` section.

- [ ] **Step 3: Verify final state.**

```bash
wc -l skills/execute/references/model-selection.md
```
Expected: 30 lines (was 42, minus 12).

```bash
tail -n 5 skills/execute/references/model-selection.md
```
Expected: the closing lines of the `## For Review Subagents` section.

```bash
grep -n "Tier 3" skills/execute/references/model-selection.md
grep -n "Agent Teams" skills/execute/references/model-selection.md
grep -n "teammate" skills/execute/references/model-selection.md
```
Expected: zero matches for each.

- [ ] **Step 4: Commit.**

```bash
git add skills/execute/references/model-selection.md
git commit -m "refactor(execute): strip Tier 3 section from model-selection.md (R4)"
```

---

### Task 5: Fix `README.md` line 72 stale Tier 3 reference (R5)

**blocks:** 7
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 3, 4, 6)

**Files:**
- Modify: `README.md`

**Model:** haiku (one-line table-row edit)

- [ ] **Step 1: Confirm line 72 content.**

```bash
sed -n '72p' README.md
```
Expected: `| \`gigo:execute\` | Runs plans with agent teams. Workers get the spec, not the rules |`

- [ ] **Step 2: Replace "agent teams" language.**

Replace line 72 with:

```
| `gigo:execute` | Runs plans by dispatching parallel subagents. Workers get the spec, not the rules |
```

Only the first sentence changes. The second sentence ("Workers get the spec, not the rules") must remain verbatim. Preserve the table column structure (pipe characters and spacing).

- [ ] **Step 3: Verify.**

```bash
grep -in "agent teams" README.md
```
Expected: zero matches (case-insensitive).

```bash
sed -n '72p' README.md
```
Expected: the replacement line shown in Step 2.

- [ ] **Step 4: Commit.**

```bash
git add README.md
git commit -m "docs(readme): fix stale Tier 3 reference on skill table line 72 (R5)"
```

---

### Task 6: Strip Tier 3 from `checkpoint-format.md` (R8)

**blocks:** 7
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 3, 4, 5)

**Files:**
- Modify: `skills/execute/references/checkpoint-format.md`

**Model:** haiku (three small, localized edits)

**Context:** This task is the Challenger-discovered R8 — the source brief did not include `checkpoint-format.md`, but it contains three Tier 3 artifacts that would fail AC17's grep if left in place. Three sub-edits.

- [ ] **Step 1: Confirm landmarks.**

Run: `wc -l skills/execute/references/checkpoint-format.md`
Expected: ~125 lines.

Confirm:
- Line ~39: table row `| \`tier\` | \`1\`, \`2\`, \`3\` | Which execution tier was running |`
- Line ~94: `### Agent Teams (Tier 3, if used)` heading
- Line ~114: edge case starting with `**Agent teams race window (Tier 3 only):**`

- [ ] **Step 2: Apply R8.1 — update `tier` field values.**

In the Fields table, change the `tier` row's values column from `` `1`, `2`, `3` `` to `` `1`, `2` ``. Final row:

```
| `tier` | `1`, `2` | Which execution tier was running |
```

The other columns (`Field` name, `Purpose` description) and other table rows are preserved verbatim. The checkpoint example code blocks earlier in the file (which use `tier=1` and `tier=2`) are not touched.

- [ ] **Step 3: Apply R8.2 — delete `### Agent Teams (Tier 3, if used)` subsection.**

In the `## Reconciliation on Resume` section, remove the entire `### Agent Teams (Tier 3, if used)` subsection: the `###` heading, the blank line, the introductory sentence ("On resume, the shared task list may have stale state..."), the 5-item numbered list, and any trailing blank line up to the next top-level section heading.

After the deletion, `## Reconciliation on Resume` contains only its opening paragraph about the primary execution path ("For the primary execution path (subagents and inline), there's no shared state to reconcile. Checkpoints in the plan file are the sole source of truth. The lead reads them and picks up where it left off.") and flows directly into `## Edge Cases`.

- [ ] **Step 4: Apply R8.3 — delete `**Agent teams race window (Tier 3 only):**` edge case.**

In the `## Edge Cases` section, remove the entire paragraph starting with `**Agent teams race window (Tier 3 only):**`. The deletion covers the bold-prefixed line and all continuation lines through (but not including) the next `**` bullet.

**Preserve verbatim** the surrounding edge cases:
- `**Partial checkpoint (crash mid-write):**` — appears before the deleted paragraph
- `**Operator decided, worker implementing:**` — appears after the deleted paragraph

- [ ] **Step 5: Verify forbidden strings removed.**

```bash
grep -n "Tier 3" skills/execute/references/checkpoint-format.md
grep -ni "agent teams" skills/execute/references/checkpoint-format.md
grep -n "shared task list" skills/execute/references/checkpoint-format.md
```
Expected: zero matches for each.

- [ ] **Step 6: Verify load-bearing structure preserved.**

```bash
grep -n "Reconciliation on Resume" skills/execute/references/checkpoint-format.md
grep -n "Edge Cases" skills/execute/references/checkpoint-format.md
grep -n "Partial checkpoint" skills/execute/references/checkpoint-format.md
grep -n "Operator decided" skills/execute/references/checkpoint-format.md
```
Expected: at least one match for each grep.

- [ ] **Step 7: Commit.**

```bash
git add skills/execute/references/checkpoint-format.md
git commit -m "refactor(execute): strip Tier 3 content from checkpoint-format.md (R8)"
```

---

### Task 7: Create `agent-teams-design.md` target-state design doc (R6)

**blocks:** 8
**blocked-by:** 1, 2, 3, 4, 5, 6
**parallelizable:** false

**Files:**
- Create: `skills/execute/references/agent-teams-design.md`

**Model:** sonnet (creative writing under strict constraints: 9 sections, 220–280 lines, multiple verbatim-required phrases, qualified-naming discipline)

**Context for the worker:** This task creates the target-state design doc that `gigo:execute`'s new `## Future: Agent Teams` pointer (added in Task 1) references. The doc is NOT shipped, NOT wired up — it is a reference-tier blueprint for when the Claude Code Agent Teams API stabilizes. Read the spec's R6 section end-to-end before writing. Particularly R6.1 (structure), R6.2 (per-section requirements), and the Conventions section's "Qualified Phase 7 references" rule.

**Hard constraints:**
1. **Total length 220–280 lines.** AC10 enforces this strictly. If per-section drafting pushes you outside the range, trim the least load-bearing content.
2. **Every `Phase 7` mention must be qualified** — either followed by `(research)` or appearing in the same sentence as `bare-worker research finding` / `research finding`. Unqualified bare `Phase 7` is forbidden. (Rationale: the unqualified term collides with `gigo:spec`'s internal Phase 7 — "Operator Reviews Spec".)
3. **`_workspace/` may appear only in the context of clarifying it is NOT a GIGO convention.** Nowhere else. §5 contains the required clarification sentence.
4. **Nine sections in exact order with exact headings** — see Step 2 below.

- [ ] **Step 1: Create the file with top-level heading.**

```bash
cat > skills/execute/references/agent-teams-design.md <<'EOF'
# Agent Teams: Target-State Design

EOF
```

- [ ] **Step 2: Write §1 Status (5–10 lines) and §2 Why Teams (25–35 lines).**

**§1 Status** must contain verbatim ALL THREE phrases: `TARGET-STATE DESIGN`, `NOT SHIPPED`, `NOT WIRED UP`. Must name two preconditions for future implementation: (a) Claude Code Agent Teams API stability, (b) resolution of the bare-worker research tension.

**§2 Why Teams** must name THREE mechanisms where teams could add value over subagents:
1. Inter-agent communication via `SendMessage` (synchronous, small updates between members)
2. Shared task state visibility (all members see a common task list)
3. Cross-review at the team level (reviewer-in-the-loop reviewing another member's output)

§2 must also contain an explicit caveat that these benefits do NOT apply to single-pass code generation, and that where they DO apply is non-code workflows with iterative refinement or cross-agent negotiation.

Section headings:
- `## Status`
- `## Why Teams`

- [ ] **Step 3: Write §3 Decision Tree (35–45 lines) and §4 Team Composition (25–40 lines).**

**§3 Decision Tree** must be scannable and branching. The top-level question must be `Is the task producing code?`. The code-producing (YES) branch routes to Subagents unconditionally — this is the enforcement point for the bare-worker research finding. The non-code (NO) branch gates on a second question: `Is the Claude Code Agent Teams API stable?` If YES, route to a team; if NO, fall back to Subagents.

Do NOT add `plan size` or `single-session requirement` gates — those were deliberately dropped as under-specified.

**§4 Team Composition** must state all of:
- One team per execution (no mid-execution recomposition).
- Leader = the lead persona driving `gigo:execute`.
- Members mapped from `CLAUDE.md` personas.
- **Known cost**: Claude Code auto-loads `CLAUDE.md` onto all team members at spawn — team members are NOT bare.
- Sizing: ~5–6 tasks per member; 2–5 members per team.
- Rationale for "one team per execution": Pipeline phases that need different members fall back to Subagents, not team recomposition.

Section headings:
- `## Decision Tree`
- `## Team Composition`

- [ ] **Step 4: Write §5 Data-Passing Protocols (25–35 lines) and §6 Team Lifecycle (20–30 lines).**

**§5 Data-Passing Protocols** must document four modes:
- **Message** (`SendMessage`): synchronous, small inter-member updates.
- **Task** (`TaskCreate` / `TaskUpdate`): persistent work-item state.
- **File** (agreed paths): large artifacts.
- **Return-value**: not applicable inside teams.

The File mode description must include this exact sentence (or a semantically equivalent phrasing that preserves all substantive claims):

> File-based passing means agreed file paths for large artifacts — GIGO today flows data through plan "What Was Built" addendums and git branch merges, not a dedicated workspace directory. A workspace convention could be introduced later if teams need it.

The literal string `_workspace/` may appear in this file ONLY in this non-convention clarification context.

**§6 Team Lifecycle** must cover in order:
- Spawn (`TeamCreate`)
- Run-phase (member-to-member communication via the four protocols in §5)
- Hook enforcement via `TaskCompleted` invoking `gigo:verify`
- Crash handling (team dies, fresh team spawned from plan checkpoints)
- Teardown (`TeamDelete`)
- Explicit statement: "no mid-execution recomposition"

Section headings:
- `## Data-Passing Protocols`
- `## Team Lifecycle`

- [ ] **Step 5: Write §7 Phase 7 (research) Reconciliation (35–50 lines) and §8 Open Questions (20–30 lines).**

**§7 Phase 7 (research) Reconciliation** is the load-bearing reconciliation section. Must state:
- The bare-worker research finding: bare workers produce better CODE than context-loaded workers.
- The platform constraint: Claude Code auto-loads `CLAUDE.md` onto all team members; teams cannot be bare.
- The resolution: **teams are for NON-CODE workflows only**. Non-code work benefits from persona context; the bare-worker research finding applies specifically to code generation.
- The future relaxation condition: if Claude Code adds selectively-bare team members, the code-producing branch in the decision tree can relax. Until then, the branch stays.

**Qualified-naming constraint** applies to this section especially. Every literal `Phase 7` must be qualified — either followed by `(research)` or appearing in the same sentence as `bare-worker research finding` or `research finding`. The section heading `## Phase 7 (research) Reconciliation` is itself qualified and satisfies the rule for readers entering the section.

**§8 Open Questions** must list at least FOUR unresolved concerns:
1. Selectively-bare team members (can the platform support bare members?)
2. Pre-assignment reliability (auto-claim race conditions in current experimental API)
3. Crash recovery of in-flight team state
4. Hook integration reliability (`TaskCompleted` with `gigo:verify`)

A fifth entry (non-code team sizing) is permitted but not required.

Section headings:
- `## Phase 7 (research) Reconciliation`
- `## Open Questions`

- [ ] **Step 6: Write §9 Audit Trail (15–25 lines).**

**§9 Audit Trail** must include ALL of:
- List of the six files touched by Cycle 2: `review-hook.md` (deleted), `SKILL.md`, `teammate-prompts.md`, `model-selection.md`, `README.md`, `checkpoint-format.md` (all stripped).
- Pointer to Cycle 2 ship date (`shipped 2026-04-11` or the actual ship date from execution — today's date is acceptable).
- A `git log` hint showing how to surface the deletion, e.g.:

  ```
  git log --all --diff-filter=D -- skills/execute/references/review-hook.md
  ```

- Reasons for removal: the four documented Tier 3 issues (auto-claim race conditions, forced `CLAUDE.md` load on team members, no session resume on crash, higher token cost) PLUS the Phase 7 (research) bare-worker tension.
- Pointer to source briefs: `briefs/03-execution-architecture-catalog.md`, `briefs/04-agent-teams-rebuild.md`, and the path of the Cycle 2 spec (`docs/gigo/specs/2026-04-11-agent-teams-rebuild-design.md`).

Section heading: `## Audit Trail`

- [ ] **Step 7: Self-verify design doc.**

```bash
wc -l skills/execute/references/agent-teams-design.md
```
Expected: between 220 and 280 (inclusive).

```bash
grep -c "^## " skills/execute/references/agent-teams-design.md
```
Expected: exactly 9 (the nine required section headings).

```bash
grep -n "TARGET-STATE DESIGN" skills/execute/references/agent-teams-design.md
grep -n "NOT SHIPPED" skills/execute/references/agent-teams-design.md
grep -n "NOT WIRED UP" skills/execute/references/agent-teams-design.md
```
Expected: at least one match for each (Status section verbatim phrases).

```bash
grep -n "Phase 7" skills/execute/references/agent-teams-design.md
```
Expected: every match must be followed by `(research)` OR appear in a sentence also containing `bare-worker research finding` / `research finding`. Manually inspect each line.

```bash
grep -n "_workspace/" skills/execute/references/agent-teams-design.md
```
Expected: matches only in §5 Data-Passing Protocols, in the non-convention clarification context.

```bash
grep -n "Is the task producing code" skills/execute/references/agent-teams-design.md
```
Expected: at least one match (the §3 top-level decision).

If any verification fails, fix the section and re-verify before committing.

- [ ] **Step 8: Commit.**

```bash
git add skills/execute/references/agent-teams-design.md
git commit -m "docs(execute): add agent-teams-design.md target-state design doc (R6)"
```

---

### Task 8: Verification sweep — run all 24 acceptance criteria (AC1–AC24)

**blocks:** []
**blocked-by:** 1, 2, 3, 4, 5, 6, 7
**parallelizable:** false

**Files:** Read-only — no file modifications. This task runs the verification greps defined in the spec's Acceptance Criteria section and reports aggregate status.

**Model:** sonnet (AC traceability requires reading ACs and mapping findings back to requirements)

**Context:** This task runs after Task 7 commits. Its job is to confirm every AC in the spec passes. If any AC fails, report which AC, what the expected vs actual state was, and which requirement (R-number) is implicated. Do NOT attempt to fix failures from this task — escalate to the lead for retry.

- [ ] **Step 1: AC1 — `review-hook.md` deleted.**

```bash
test ! -e skills/execute/references/review-hook.md && echo "AC1: PASS (file absent)" || echo "AC1: FAIL"
git log --all --diff-filter=D -- skills/execute/references/review-hook.md --oneline | head -5
```
Expected: `AC1: PASS` and a deletion commit in the git log.

- [ ] **Step 2: AC2 — SKILL.md frontmatter cleaned.**

```bash
sed -n '1,10p' skills/execute/SKILL.md | grep -c "Agent teams"
```
Expected: 0 (zero matches in the frontmatter region).

- [ ] **Step 3: AC3 — Two-tier presentation.**

```bash
grep -c "Agent teams" skills/execute/SKILL.md
grep -n "Subagents\*\* (recommended)" skills/execute/SKILL.md
grep -n "Inline\*\* — sequential" skills/execute/SKILL.md
grep -n "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" skills/execute/SKILL.md
```
Expected:
- First grep: 0 (no "Agent teams" in frontmatter/bullet context — only the R7 "Future: Agent Teams" heading/body will match "Agent Teams" with capital T)
- Second and third greps: at least one match (Subagents and Inline bullets preserved)
- Fourth grep: 0 (no env var reference)

Note: "Agent Teams" (capital T) WILL match in the R7 Future section — this is expected and allowed. AC3 checks the blockquote bullet context specifically; manual inspection confirms only options 1 and 2 are present.

- [ ] **Step 4: AC4 — Tier 3 section removed and Future section structure correct.**

```bash
grep -n "^## Tier 3" skills/execute/SKILL.md
grep -n "^## Future: Agent Teams" skills/execute/SKILL.md
grep -n "^## After Review Passes" skills/execute/SKILL.md
```
Expected:
- First grep: zero matches.
- Second grep: one match (R7 addition).
- Third grep: one match (section exists).

Manual structural inspection: between `## Future: Agent Teams` and `## After Review Passes`, there should be two `---` separators (one preceding Future, one preceding After Review Passes).

- [ ] **Step 5: AC5 — References list updated.**

```bash
grep -n "review-hook.md" skills/execute/SKILL.md
grep -n "agent-teams-design.md" skills/execute/SKILL.md
grep -n "teammate-prompts.md" skills/execute/SKILL.md
grep -n "(all tiers)" skills/execute/SKILL.md
grep -n "model-selection.md" skills/execute/SKILL.md
grep -n "checkpoint-format.md" skills/execute/SKILL.md
```
Expected:
- `review-hook.md`: zero matches
- `agent-teams-design.md`: matches (R7 added the Future pointer + References bullet)
- `teammate-prompts.md`: one match (the updated bullet — still present, just reworded)
- `(all tiers)`: zero matches (the old bullet used this; the new bullet does not)
- `model-selection.md`: one match (preserved bullet)
- `checkpoint-format.md`: one match (preserved bullet)

- [ ] **Step 6: AC6 and AC7 — teammate-prompts.md Tier 3 removed, KEEP block preserved.**

```bash
grep -n "^### Tier 3" skills/execute/references/teammate-prompts.md
grep -n "SendMessage" skills/execute/references/teammate-prompts.md
grep -n "TaskCompleted" skills/execute/references/teammate-prompts.md
grep -n "auto-claim" skills/execute/references/teammate-prompts.md
grep -n "Agent Team" skills/execute/references/teammate-prompts.md
```
Expected (AC6): zero matches for each.

```bash
grep -n "Phase 7 eval data proved that bare workers" skills/execute/references/teammate-prompts.md
grep -n "Why full task text" skills/execute/references/teammate-prompts.md
grep -n "Why self-review before reporting" skills/execute/references/teammate-prompts.md
grep -c "Why explicit task assignment" skills/execute/references/teammate-prompts.md
```
Expected (AC7): at least one match for each of the first three; zero for the fourth.

- [ ] **Step 7: AC8 — model-selection.md Tier 3 removed.**

```bash
grep -n "^## For Agent Teams" skills/execute/references/model-selection.md
grep -n "teammate" skills/execute/references/model-selection.md
grep -n "^## For Review Subagents" skills/execute/references/model-selection.md
wc -l skills/execute/references/model-selection.md
```
Expected: first and second greps return zero; third returns one match; line count ~30.

- [ ] **Step 8: AC9 — README.md line 72 fixed.**

```bash
grep -ni "agent teams" README.md
grep -n "subagents" README.md
sed -n '72p' README.md
```
Expected: first grep zero matches (case-insensitive); second grep returns at least one match; line 72 uses the word "subagents".

- [ ] **Step 9: AC10 and AC11 — design doc exists with correct length and structure.**

```bash
wc -l skills/execute/references/agent-teams-design.md
grep -c "^## " skills/execute/references/agent-teams-design.md
grep -n "^## Status" skills/execute/references/agent-teams-design.md
grep -n "^## Why Teams" skills/execute/references/agent-teams-design.md
grep -n "^## Decision Tree" skills/execute/references/agent-teams-design.md
grep -n "^## Team Composition" skills/execute/references/agent-teams-design.md
grep -n "^## Data-Passing Protocols" skills/execute/references/agent-teams-design.md
grep -n "^## Team Lifecycle" skills/execute/references/agent-teams-design.md
grep -n "^## Phase 7 (research) Reconciliation" skills/execute/references/agent-teams-design.md
grep -n "^## Open Questions" skills/execute/references/agent-teams-design.md
grep -n "^## Audit Trail" skills/execute/references/agent-teams-design.md
```
Expected (AC10): line count in [220, 280].
Expected (AC11): second grep returns 9; each subsequent heading grep returns at least one match (confirms order and presence). Manually confirm the headings appear in the required order.

- [ ] **Step 10: AC12 — Status banner unambiguous.**

```bash
grep -n "TARGET-STATE DESIGN" skills/execute/references/agent-teams-design.md
grep -n "NOT SHIPPED" skills/execute/references/agent-teams-design.md
grep -n "NOT WIRED UP" skills/execute/references/agent-teams-design.md
grep -n "API" skills/execute/references/agent-teams-design.md | head -5
grep -n "bare-worker" skills/execute/references/agent-teams-design.md | head -5
```
Expected: at least one match for each of the first three; the last two confirm the two preconditions are named in §1 (manually verify they're near the Status heading).

- [ ] **Step 11: AC13 — Decision tree code-producing branch.**

```bash
grep -n "Is the task producing code" skills/execute/references/agent-teams-design.md
grep -n "Subagents" skills/execute/references/agent-teams-design.md | head -10
```
Expected: first grep returns at least one match (the top-level question); second grep returns multiple matches including within §3.

- [ ] **Step 12: AC14 — `_workspace/` clarification.**

```bash
grep -n "_workspace/" skills/execute/references/agent-teams-design.md
grep -n "not a dedicated workspace" skills/execute/references/agent-teams-design.md
grep -n "What Was Built" skills/execute/references/agent-teams-design.md
```
Expected: first grep's matches all appear in §5 Data-Passing Protocols in a non-convention context; second and third greps each return at least one match.

- [ ] **Step 13: AC15 — Qualified Phase 7 references.**

```bash
grep -n "Phase 7" skills/execute/references/agent-teams-design.md
```
For each line in the output, confirm ONE of:
- The line contains `Phase 7 (research)` immediately (the qualifier follows).
- The line is the heading `## Phase 7 (research) Reconciliation`.
- The surrounding sentence (line above or below) contains `bare-worker research finding` or `research finding`.

If any line has an unqualified bare `Phase 7`, AC15 fails. Report the line number.

- [ ] **Step 14: AC16 — Future pointer in SKILL.md.**

```bash
grep -n "^## Future: Agent Teams" skills/execute/SKILL.md
grep -n "references/agent-teams-design.md" skills/execute/SKILL.md
```
Expected: first grep returns one match (the R7 heading); second grep returns at least two matches (the pointer body + the References bullet).

Manually inspect: the Future section body is 2–4 rendered lines, a single paragraph, does NOT describe the team mechanism. A new `---` separator sits between the Future body and `## After Review Passes`.

- [ ] **Step 15: AC17 — Global Tier 3 coverage grep is clean.**

```bash
grep -rn "Tier 3\|CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS\|review-hook\|auto-claim\|TeamCreate\|TaskCompleted" \
  skills/ README.md CLAUDE.md
```

Expected: matches return ONLY from `skills/execute/references/agent-teams-design.md`. Zero matches in any other file under `skills/`, `README.md`, or `CLAUDE.md`.

If any match appears outside `agent-teams-design.md`, report:
- The file path
- The matching line
- Which string matched
- Which requirement should have removed it

- [ ] **Step 16: AC18 — checkpoint-format.md cleaned.**

```bash
grep -n "^### Agent Teams" skills/execute/references/checkpoint-format.md
grep -n "Agent teams race window" skills/execute/references/checkpoint-format.md
grep -n "Tier 3" skills/execute/references/checkpoint-format.md
grep -n "shared task list" skills/execute/references/checkpoint-format.md
grep -ni "agent teams" skills/execute/references/checkpoint-format.md
grep -n "tier\` | \`1\`, \`2\`" skills/execute/references/checkpoint-format.md
grep -n "Reconciliation on Resume" skills/execute/references/checkpoint-format.md
grep -n "Edge Cases" skills/execute/references/checkpoint-format.md
grep -n "Partial checkpoint" skills/execute/references/checkpoint-format.md
grep -n "Operator decided" skills/execute/references/checkpoint-format.md
```
Expected:
- First 5 greps: zero matches (forbidden strings removed).
- Sixth grep: one match (updated tier row).
- Last four greps: at least one match each (load-bearing structure preserved).

- [ ] **Step 17: AC19 — Why Teams section names three mechanisms.**

```bash
grep -n "SendMessage" skills/execute/references/agent-teams-design.md
grep -n "shared task" skills/execute/references/agent-teams-design.md
grep -n "cross-review" skills/execute/references/agent-teams-design.md
grep -ni "does not apply\|do not apply\|not for code" skills/execute/references/agent-teams-design.md
```
Expected: first three greps return at least one match each (the three mechanisms); fourth grep returns at least one match (the code-generation caveat).

- [ ] **Step 18: AC20 — Team Composition load-bearing claims.**

```bash
grep -n "one team per execution" skills/execute/references/agent-teams-design.md
grep -n "auto-loads" skills/execute/references/agent-teams-design.md
grep -n "CLAUDE.md" skills/execute/references/agent-teams-design.md
grep -ni "not bare\|cannot be bare" skills/execute/references/agent-teams-design.md
```
Expected: at least one match for each.

- [ ] **Step 19: AC21 — Team Lifecycle primitives.**

```bash
grep -n "TeamCreate" skills/execute/references/agent-teams-design.md
grep -n "TaskCompleted" skills/execute/references/agent-teams-design.md
grep -n "TeamDelete" skills/execute/references/agent-teams-design.md
grep -n "crash" skills/execute/references/agent-teams-design.md
grep -ni "no recomposition\|no mid-execution recomposition\|cannot be recomposed" skills/execute/references/agent-teams-design.md
```
Expected: at least one match for each.

- [ ] **Step 20: AC22 — Open Questions has at least four items.**

Manually read §8 Open Questions. Count bullet/numbered items. Expected: at least 4 items. Confirm at minimum these topics are named:
- `selectively-bare` (or `selectively bare`)
- `auto-claim` (or `pre-assignment`)
- `crash recovery` (or `crash` with `recovery`)
- `hook integration`

```bash
grep -ni "selectively-bare\|selectively bare" skills/execute/references/agent-teams-design.md
grep -n "auto-claim\|pre-assignment" skills/execute/references/agent-teams-design.md
grep -n "crash recovery\|crash" skills/execute/references/agent-teams-design.md
grep -n "hook integration" skills/execute/references/agent-teams-design.md
```
Expected: at least one match for each.

- [ ] **Step 21: AC23 — Audit Trail completeness.**

```bash
grep -n "review-hook.md" skills/execute/references/agent-teams-design.md
grep -n "SKILL.md" skills/execute/references/agent-teams-design.md
grep -n "teammate-prompts.md" skills/execute/references/agent-teams-design.md
grep -n "model-selection.md" skills/execute/references/agent-teams-design.md
grep -n "README.md" skills/execute/references/agent-teams-design.md
grep -n "checkpoint-format.md" skills/execute/references/agent-teams-design.md
grep -n "git log" skills/execute/references/agent-teams-design.md
grep -n "briefs/03-execution-architecture-catalog.md" skills/execute/references/agent-teams-design.md
grep -n "briefs/04-agent-teams-rebuild.md" skills/execute/references/agent-teams-design.md
grep -n "2026-04-11-agent-teams-rebuild-design.md" skills/execute/references/agent-teams-design.md
```
Expected: at least one match for each (all six files named, git log example present, three pointer paths present).

- [ ] **Step 22: AC24 — Reference-tier discipline.**

```bash
grep -c "TARGET-STATE DESIGN" skills/execute/SKILL.md
grep -c "references/agent-teams-design.md" skills/execute/SKILL.md
```
Expected:
- First grep: 0 (SKILL.md does NOT inline the design doc content — the sentinel phrase appears only in the design doc).
- Second grep: at least 1 (SKILL.md references the design doc by path).

- [ ] **Step 23: Report aggregate status.**

Produce a summary of AC1 through AC24 status. For each AC, report PASS or FAIL with a one-line justification. If any AC fails, include the file path, matching/missing content, and the requirement (R-number) implicated.

Format the report as:

```
## Verification Sweep Results

AC1: PASS — review-hook.md absent, deletion commit present
AC2: PASS — frontmatter clean of "Agent teams"
...
AC24: PASS — no TARGET-STATE DESIGN sentinel in SKILL.md; pointer present

OVERALL: 24/24 PASS  (or N/24, with failing ACs listed)
```

Return the report. Do NOT commit anything from this task — it is read-only.

---

## Done when

- All 8 tasks complete (commits on `main` or their respective worktree branches merged cleanly)
- Task 8 reports 24/24 AC PASS
- `gigo:execute`'s two-tier presentation is the default operator experience (Subagents + Inline only)
- `skills/execute/references/agent-teams-design.md` exists in the 220–280 line range with all nine required sections
- No Tier 3 implementation strings remain in `skills/`, `README.md`, or `CLAUDE.md` outside the new design doc
- The Phase 7 (research) bare-worker rationale in `teammate-prompts.md` is preserved verbatim

<!-- approved: plan 2026-04-12T04:32:15Z by:Eaven -->
