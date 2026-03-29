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
   - If a rule exists but friction still occurred: the rule may be too vague, buried, or unenforceable. Propose strengthening it.
   - If no rule exists and the friction is recurring (appears in 2+ sessions OR has count > 1 in this session): propose a new rule.

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

---

## Section 3: Pipeline Compliance (GIGO-Specific)

**Gate:** This section only runs for projects with a GIGO pipeline. To detect: read the target project's `CLAUDE.md` and `.claude/rules/workflow.md`. If neither references `gigo:` skills or describes a plan/execute/review pipeline, skip this section entirely.

### Pipeline Stage Checks

For each session, check `tool_counts` against expectations:

| Stage | Key | Pass Condition | Applicable When | Points |
|-------|-----|----------------|-----------------|--------|
| Plan mode entered | `EnterPlanMode` in tool_counts | Count >= 1 | `git_commits >= 3` OR `duration_minutes >= 15` | 30 |
| Plan mode completed | `ExitPlanMode` in tool_counts | Count >= 1 | `EnterPlanMode` is present | 10 |
| Subagent execution | `Agent` in tool_counts | Count >= 2 | `git_commits >= 3` | 20 |
| Review ran | `Skill` in tool_counts | Count >= 1 | `git_commits >= 1` | 25 |
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

Score = (earned points / applicable points) * 100

If no stages are applicable (e.g., quick Q&A session), score is N/A — don't penalize.

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
3. Score = `max(0, 100 - weighted_total * 12)`

**Without facets:**
1. Start at 70
2. Subtract 10 per entry in `tool_error_categories`
3. Subtract 15 if `user_interruptions > 3`
4. Subtract 10 if `output_tokens / max(lines_added, 1) > 500`
5. Floor at 0

### Dimension 3: Efficiency (always available)

Ratio = `output_tokens / max(lines_added + git_commits * 50, 1)`

| Ratio | Score |
|-------|-------|
| < 50 | 100 |
| 50-150 | 85 |
| 150-400 | 70 |
| 400-1000 | 50 |
| 1000-2500 | 30 |
| > 2500 | 15 |

**Edge case:** If `lines_added == 0` AND `git_commits == 0` (exploration/Q&A session): score 60 (neutral).

### Dimension 4: Pipeline Adherence (GIGO-specific)

Use the compliance score from Section 3. If Section 3 was skipped (no GIGO pipeline), this dimension is N/A.

### Composite Score

Select weights based on context:

| Context | Outcome | Friction | Efficiency | Pipeline |
|---------|---------|----------|------------|----------|
| GIGO + facets | 0.35 | 0.25 | 0.20 | 0.20 |
| GIGO + no facets | -- | 0.35 | 0.30 | 0.35 |
| Non-GIGO + facets | 0.45 | 0.30 | 0.25 | -- |
| Non-GIGO + no facets | -- | 0.50 | 0.50 | -- |

Composite = sum of (dimension score * weight) for available dimensions.

### Aggregate Mode

Weighted average across sessions: `sum(session_score * max(duration_minutes, 1)) / sum(max(duration_minutes, 1))`

If 3+ sessions: compute trend by comparing first-half average to second-half average.
- Improving: second half > first half + 5
- Declining: second half < first half - 5
- Stable: within +/-5

### Display

| Score | Label |
|-------|-------|
| 80-100 | Healthy |
| 60-79 | Some friction |
| 40-59 | Significant issues |
| 0-39 | Problematic — deep-dive recommended |

Show composite score + per-dimension breakdown. In aggregate, include trend indicator.

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
