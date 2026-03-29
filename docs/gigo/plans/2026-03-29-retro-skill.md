# gigo:retro Skill — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-29-retro-skill-design.md`

**Goal:** Create the retro skill — reads session telemetry, analyzes friction, proposes project improvements.

**Architecture:** Hub-and-spoke. SKILL.md handles mode detection and phase sequencing, references/analysis-procedure.md contains the detailed analysis logic. One 3-line addition to snap.md for integration.

---

### Task 1: Create analysis-procedure.md (the spoke)

**blocks:** 2
**blocked-by:** []
**parallelizable:** false

**Files:**
- Create: `skills/retro/references/analysis-procedure.md`

Write the reference file first — it contains the substantive analysis logic that SKILL.md will point to.

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p skills/retro/references
```

- [ ] **Step 2: Write the complete file in one pass**

Create `skills/retro/references/analysis-procedure.md` with the full content below. Write as a single file — do NOT append section by section (partial files on error are unrecoverable).

```markdown
# Analysis Procedure

Reference file for `gigo:retro`. Contains the step-by-step analysis logic.
SKILL.md points here for each phase's details.

---

## Section 1: Data Loading

### Reading Session Files

1. Read all files in `~/.claude/usage-data/session-meta/`. For each file:
   - Parse JSON with error-tolerant mode (Python: `json.loads(content, strict=False)`, or equivalent). Catch and skip files that fail.
   - Check `project_path` — exact string match against the current project's canonical path. No substring matching. `/Users/x/projects/gigo` must NOT match `/Users/x/projects/gigo-orchestrator`.
   - Track count of skipped files for reporting.

2. For each matching session, check if `~/.claude/usage-data/facets/{session_id}.json` exists. If yes, load it (same error-tolerant parsing).

3. Sort matched sessions by `start_time` descending (most recent first).

4. Exclude the current session: skip any session with `start_time` within the last 5 minutes of the current time.

### Mode-Specific Filtering

- **Last session mode:** Take the first (most recent) session only.
- **Specific session mode:** Find the session matching the operator's ID prefix or description. For ID prefix: match against `session_id` starting characters. For description: substring search in `first_prompt` and facets `underlying_goal`. If multiple matches, list candidates with their `first_prompt` (truncated to 80 chars) and `start_time`, ask the operator to pick.
- **Aggregate mode:** Take all sessions within the time window (default 7 days from now). If "last N" was specified, take the N most recent regardless of time window.
```

The file continues with all remaining sections inline (Sections 2 through 5). The full content for each section follows:

**Section 2: Friction Analysis (Facets Path)**

```markdown
---

## Section 2: Friction Analysis (Facets Path)

For each session with facets data:

### Step 1: Categorize Friction Types

Read `friction_counts` object. Map each key to a category:

| Friction Type | Category |
|---------------|----------|
| `wrong_approach`, `misunderstood_request`, `confusion` | **Planning** |
| `buggy_code`, `tool_failure`, `tool_limitations` | **Execution** |
| `excessive_changes`, `rubber_stamping`, `skipped_gate` | **Pipeline** |
| `deferred_work`, `session_interrupted` | **Completion** |
| Any unknown key | **Uncategorized** |

### Step 2: Read Friction Narrative

Read `friction_detail` — this is the narrative explaining what went wrong.
Extract specific incidents from the text.

### Step 3: Cross-Reference Against Project

For each friction point:

1. Read the **target project's** `.claude/rules/` files. Does a rule exist that should have prevented this friction?
   - If a rule exists but friction still occurred: the rule may be too vague, buried, or unenforceable → propose strengthening it.
   - If no rule exists and the friction is recurring (appears in 2+ sessions OR has count > 1 in this session) → propose a new rule.

2. Check the **target project's** skill prompts (in `.claude/skills/` or the project's plugin skills). Should a skill have caught this during its workflow?

### Step 4: Produce Structured Findings

For each friction point, output:

```
- **Category:** [Planning|Execution|Pipeline|Completion|Uncategorized]
- **What happened:** [from friction_detail narrative]
- **Root cause:** [why existing rules/skills didn't prevent it]
- **Proposed change:** [specific action — new rule, rule edit, skill change, or memory entry]
- **Sessions:** [session ID prefix(es)]
```
```

**Section 2b: Friction Analysis (Meta-Only Path)**

```markdown
---

## Section 2b: Friction Analysis (Meta-Only Path)

When no facets exist for a session, infer friction from session-meta signals. All findings from this path are flagged `[inferred from meta — lower confidence]`.

### Heuristic Signals

Check each signal. If the threshold is exceeded, produce a finding:

| Signal | Formula | Threshold | Interpretation |
|--------|---------|-----------|----------------|
| Error rate | `tool_errors / sum(tool_counts values)` | > 0.10 | Tooling friction — tools failed too often |
| Interruptions | `user_interruptions` | > 2 | Operator had to intervene frequently — possible wrong approach |
| Response delay | Median of `user_response_times` | > 120 seconds | Operator disengaged or struggling with complexity |
| Token waste | `output_tokens / max(lines_added, 1)` | > 500 | High token spend relative to productive output |
| Stuck session | `duration_minutes > 30` AND `git_commits == 0` | Both true | Long session that produced nothing |
| Stale paths | `tool_error_categories` contains "File Not Found" | Present | Rules or skills reference files that don't exist |

### Finding Format (Meta-Only)

```
- **Category:** [inferred category based on signal type]
- **Signal:** [which heuristic triggered]
- **Value:** [actual value vs threshold]
- **Interpretation:** [what this likely means]
- **[inferred from meta — lower confidence]**
```

These findings can still produce proposals, but the proposals should note the lower evidence quality.
```

**Section 3: Pipeline Compliance**

```markdown
---

## Section 3: Pipeline Compliance (GIGO-Specific)

**Gate:** This section only runs for projects with a GIGO pipeline. To detect: read the target project's `CLAUDE.md` and `.claude/rules/workflow.md`. If neither references `gigo:` skills or describes a plan/execute/review pipeline, skip this section entirely.

### Pipeline Stage Checks

For each session, check `tool_counts` against expectations:

| Stage | Key | Pass Condition | Applicable When | Points |
|-------|-----|----------------|-----------------|--------|
| Plan mode entered | `EnterPlanMode` in tool_counts | Count ≥ 1 | `git_commits ≥ 3` OR `duration_minutes ≥ 15` | 30 |
| Plan mode completed | `ExitPlanMode` in tool_counts | Count ≥ 1 | `EnterPlanMode` is present | 10 |
| Subagent execution | `Agent` in tool_counts | Count ≥ 2 | `git_commits ≥ 3` | 20 |
| Review ran | `Skill` in tool_counts | Count ≥ 1 | `git_commits ≥ 1` | 25 |
| Snap ran | `Skill` in tool_counts | Present (imperfect) | Always | 15 |

### Applicability Logic

- If `git_commits < 3` AND `duration_minutes < 15`: plan mode and subagents are N/A
- If `git_commits == 0`: review is N/A
- Snap is always applicable

Score each stage as: **pass** / **skip** (applicable but not done) / **n/a** (not applicable)

### Known Limitations (include in output)

- `Skill` counts ALL skill invocations — cannot distinguish verify from snap
- `Agent` counts include review dispatches and execution workers
- Approval markers are in git, not telemetry — checked in single-session mode via git log if commits exist, skipped in aggregate
- Historical sessions predating blueprint adoption will score 0 on plan mode even if substantive
- Snap detection is unreliable — best proxy only

### Compliance Score

Score = (earned points / applicable points) × 100

If no stages are applicable (e.g., quick Q&A session), score is N/A — don't penalize.
```

**Section 4: Health Score**

```markdown
---

## Section 4: Health Score

Four dimensions, each scored 0-100. Combined with weighted average.

### Dimension 1: Outcome (requires facets)

| `outcome` value | Score |
|-----------------|-------|
| `fully_achieved` | 100 |
| `mostly_achieved` | 75 |
| `partially_achieved` | 40 |
| `not_achieved` | 10 |
| `unclear_from_transcript` | 50 |
| Any other/unknown value | 50 |

**Frustration modifier:** Count instances of `frustrated`, `likely_frustrated`, `dissatisfied` in `user_satisfaction_counts`. Subtract 5 per instance, capped at 15 total. Floor at 0.

### Dimension 2: Friction

**With facets:**
1. Sum all values in `friction_counts`
2. Double-weight pipeline types: multiply counts of `rubber_stamping`, `skipped_gate`, `excessive_changes` by 2 before summing
3. Score = `max(0, 100 - weighted_total × 12)`

**Without facets:**
1. Start at 70
2. Subtract 10 per entry in `tool_error_categories`
3. Subtract 15 if `user_interruptions > 3`
4. Subtract 10 if `output_tokens / max(lines_added, 1) > 500`
5. Floor at 0

### Dimension 3: Efficiency (always available)

Ratio = `output_tokens / max(lines_added + git_commits × 50, 1)`

| Ratio | Score |
|-------|-------|
| < 50 | 100 |
| 50–150 | 85 |
| 150–400 | 70 |
| 400–1000 | 50 |
| 1000–2500 | 30 |
| > 2500 | 15 |

**Edge case:** If `lines_added == 0` AND `git_commits == 0` (exploration/Q&A session): score 60 (neutral).

### Dimension 4: Pipeline Adherence (GIGO-specific)

Use the compliance score from Section 3. If Section 3 was skipped (no GIGO pipeline), this dimension is N/A.

### Composite Score

Select weights based on context:

| Context | Outcome | Friction | Efficiency | Pipeline |
|---------|---------|----------|------------|----------|
| GIGO + facets | 0.35 | 0.25 | 0.20 | 0.20 |
| GIGO + no facets | — | 0.35 | 0.30 | 0.35 |
| Non-GIGO + facets | 0.45 | 0.30 | 0.25 | — |
| Non-GIGO + no facets | — | 0.50 | 0.50 | — |

Composite = sum of (dimension score × weight) for available dimensions.

### Aggregate Mode

Weighted average across sessions: `sum(session_score × max(duration_minutes, 1)) / sum(max(duration_minutes, 1))`

If 3+ sessions: compute trend by comparing first-half average to second-half average.
- Improving: second half > first half + 5
- Declining: second half < first half - 5
- Stable: within ±5

### Display

| Score | Label |
|-------|-------|
| 80–100 | Healthy |
| 60–79 | Some friction |
| 40–59 | Significant issues |
| 0–39 | Problematic — deep-dive recommended |

Show composite score + per-dimension breakdown. In aggregate, include trend indicator.
```

**Section 5: Proposal Generation**

```markdown
---

## Section 5: Proposal Generation

Synthesize findings from Sections 2-4 into concrete proposals.

### Proposal Types

| Type | Target | When |
|------|--------|------|
| `new-rule` | `.claude/rules/{file}.md` | Recurring friction with no existing rule |
| `remove-rule` | `.claude/rules/{file}.md` | Rule that appears ineffective (friction persists despite rule) |
| `skill-change` | Specific SKILL.md or reference file | Skill should have caught friction but didn't |
| `memory-entry` | `.claude/references/` or project memory | Learning that applies to future sessions |

### Triage

| Category | Meaning | Use when |
|----------|---------|----------|
| **propose** | Clear, evidence-backed, specific change | Friction is concrete, fix is specific, evidence from 2+ sessions or high-count single session |
| **discuss** | Pattern is real but right response is unclear | Cross-cutting concern, ambiguous root cause, or affects multiple skills |

### Proposal Format

```
#### {N}. [{propose|discuss}] {One-line description}
**Type:** {new-rule | remove-rule | skill-change | memory-entry}
**Target:** {exact file path relative to project root}
**Change:** {specific text to add/remove/modify}
**Evidence:** {session ID prefix(es) and what was observed}
**Why:** {which friction this addresses and why the change helps}
```

For `discuss` proposals: replace **Change** with **Question** (what needs to be decided).

### Generation Rules

1. Every proposal must cite at least one session ID as evidence
2. `new-rule` proposals must include the exact text of the proposed rule
3. `remove-rule` proposals must quote the existing rule text
4. `skill-change` proposals must specify the file, section, and what changes
5. Don't propose changes to files outside `.claude/` — retro's footprint is context configuration
6. Don't manufacture proposals — "No improvements to propose — session looks healthy" is valid
7. If a finding from Section 2b (meta-only) generates a proposal, note the lower confidence in the Evidence field
```

- [ ] **Step 3: Commit**

```bash
git add skills/retro/references/analysis-procedure.md
git commit -m "feat(retro): add analysis procedure reference"
```

---

### Task 2: Create SKILL.md (the hub)

**blocks:** 3
**blocked-by:** 1
**parallelizable:** false

**Files:**
- Create: `skills/retro/SKILL.md`

- [ ] **Step 1: Write frontmatter and identity**

Create `skills/retro/SKILL.md`:

```markdown
---
name: retro
description: "Session retrospective — reads Claude Code telemetry and turns friction into project improvements. Analyzes one session or aggregates recent sessions. Produces proposals, not reports. Use gigo:retro."
---

# Retro

Data-driven session retrospective. Reads Claude Code's telemetry (`~/.claude/usage-data/`), identifies friction, checks pipeline compliance, and proposes concrete project improvements. Output is proposals the operator approves — not a report.

No character voice. Direct, evidence-based.

**Announce every phase.** As you work, tell the operator what's happening: "Phase 1: Discovering sessions...", "Phase 2: Analyzing friction...", etc. Don't work silently.
```

- [ ] **Step 2: Write mode detection**

Append:

```markdown
---

## Detect Mode

Resolve the current project's canonical path from the working directory.

1. If `$ARGUMENTS` is empty → **last session mode**.
2. If `$ARGUMENTS` is exactly "all", "recent", "aggregate", or matches "last N" (e.g., "last 3") → **aggregate mode**. Check this BEFORE descriptive text. Default window: last 7 days.
3. If `$ARGUMENTS` matches a session ID prefix (8+ hex chars) → **specific session mode**.
4. Otherwise → **specific session mode** via description matching. Search `first_prompt` and facets `underlying_goal` for substring matches. If ambiguous, list candidates and ask the operator to pick.
```

- [ ] **Step 3: Write phase sequence**

Append:

```markdown
---

## Phases

### Phase 1: Session Discovery

Read `references/analysis-procedure.md` Section 1 for data loading details.

Load session-meta files from `~/.claude/usage-data/session-meta/`. Filter by `project_path` exact match. Check for corresponding facets files.

**Announce (single session):** "Found session `{8-char-id}` from {date}: '{first_prompt truncated to 80 chars}' ({duration}min, {has facets / meta only})"

**Announce (aggregate):** "Found {N} sessions in the last {window}. {M} have facets data."

If no sessions found: "No session telemetry found for this project. Run `/insights` after a session to generate facets data, or check that the project path matches."

### Phase 2: Friction Analysis

Read `references/analysis-procedure.md` Section 2 (if facets available) or Section 2b (meta-only).

- With facets: categorize friction types, cross-reference against project rules, produce structured findings
- Without facets: apply heuristic signals from session-meta, flag as `[inferred from meta]`
- Aggregate mode: flag recurring types (same type in 3+ sessions = systemic)

**Announce:** "Phase 2: Analyzing friction... {N} friction points found across {M} sessions."

### Phase 3: Pipeline Compliance (Conditional)

**Gate:** Read the target project's `CLAUDE.md` and `.claude/rules/workflow.md`. If neither references `gigo:` skills or a plan/execute/review pipeline → skip: "Phase 3: Skipped — no GIGO pipeline detected."

If pipeline detected: read `references/analysis-procedure.md` Section 3. Check `tool_counts` against pipeline expectations.

**Announce:** "Phase 3: Checking pipeline compliance..." then report pass/skip/n-a for each stage.

### Phase 4: Health Score

Read `references/analysis-procedure.md` Section 4. Calculate composite score with per-dimension breakdown.

**Announce:** "Phase 4: Health score: {score}/100 ({label})" with dimension details.

### Phase 5: Proposals

Read `references/analysis-procedure.md` Section 5. Synthesize findings into proposals.

Each proposal has: type (`new-rule`/`remove-rule`/`skill-change`/`memory-entry`), target file, specific change, evidence, and triage (`propose`/`discuss`).

**Announce:** "Phase 5: {N} improvement proposals generated."

### Phase 6: Present

Display to the operator in order:
1. Session summary
2. Health score with dimension breakdown
3. Friction findings grouped by category
4. Pipeline compliance (if applicable)
5. Numbered proposals with triage categories

Ask: "Approve proposals by number (e.g., 'approve 1, 3'), discuss specific ones, or 'approve all'."

When approved → apply the change to the target file (create file if it doesn't exist).
When rejected → skip.
When discuss → conversation about that proposal.
```

- [ ] **Step 4: Write facets handling and integration sections**

Append:

```markdown
---

## Facets vs Meta-Only

Sessions with facets get full friction analysis from `friction_counts`, `friction_detail`, `outcome`, and `user_satisfaction_counts`. Sessions without facets get heuristic inference from session-meta signals at lower confidence. Announce which path each session takes.

In aggregate mode, all sessions contribute to efficiency and pipeline scoring. Only sessions with facets contribute to outcome and friction categorization. Meta-only sessions contribute heuristic friction signals.

---

## Integration

- **Standalone:** `/gigo:retro` — operator invokes directly
- **Post-Snap:** The Snap offers retro after its audit when facets exist (see snap.md)
- **Post-Insights:** After running `/insights`, follow with `/gigo:retro` to turn the analysis into project improvements

---

## Pointers

Read `references/analysis-procedure.md` for the full analysis logic — data loading, friction categorization, pipeline compliance heuristics, health scoring formulas, and proposal generation rules.
```

- [ ] **Step 5: Commit**

```bash
git add skills/retro/SKILL.md
git commit -m "feat(retro): add SKILL.md hub — mode detection, phases, pointers"
```

---

### Task 3: Modify snap.md

**blocks:** []
**blocked-by:** 2
**parallelizable:** false

**Files:**
- Modify: `.claude/rules/snap.md`

- [ ] **Step 1: Add Session Retro section**

In `.claude/rules/snap.md`, insert after the "## The Audit" section (after check #11, before "## Saving New Learnings"):

```markdown

## Session Retro (optional)

After the audit, if session telemetry exists for this session (`~/.claude/usage-data/facets/`), offer to invoke `gigo:retro` in last-session mode. Retro proposals feed into the learning-routing table below.
```

- [ ] **Step 2: Verify line count**

After adding, count lines in snap.md. Should be ~58 lines (under the 60-line cap). If over, move content to a reference file.

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/snap.md
git commit -m "feat(snap): add optional retro step after audit"
```

---

### Task 4: Validate end-to-end (inline-only)

**blocks:** []
**blocked-by:** 3
**parallelizable:** false
**inline-only:** true — skill invocations (`/gigo:retro`) require the lead or operator, not a subagent. Do not dispatch this task to a worker via Agent.

- [ ] **Step 1: Invoke `/gigo:retro` in last-session mode**

Run the skill with no arguments in the GIGO project directory. Verify:
- Phase 1 discovers sessions and announces correctly
- Phase 2 produces friction findings (or "no friction detected")
- Phase 3 detects the GIGO pipeline and checks compliance
- Phase 4 computes a health score with per-dimension breakdown
- Phase 5 generates proposals (or "no improvements to propose")
- Phase 6 presents everything in the expected format

- [ ] **Step 2: Invoke `/gigo:retro` with a specific session ID**

Pick a session ID prefix from the discovery output. Verify it finds and analyzes the correct session.

- [ ] **Step 3: Invoke `/gigo:retro recent`**

Verify aggregate mode activates, shows cross-session patterns, and computes aggregate health score.

**Done when:** All three modes work, output follows the spec's conventions, and proposals are actionable.

---

**Internal-only note:** Do not add retro to README, site, getting-started, or any public-facing content. Add to CLAUDE.md skill list as internal only. Validate on 5+ real sessions before promoting to public.
