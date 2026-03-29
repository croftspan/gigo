# gigo:retro — Session Retrospective Skill Design Spec

Reads Claude Code's session telemetry and turns friction into actionable project improvements. Not a report — a proposal engine. The operator approves or rejects each change individually.

## Guiding Constraints

- **New skill.** `skills/retro/SKILL.md` + `skills/retro/references/analysis-procedure.md`. Hub-and-spoke.
- **Domain-agnostic core.** Friction analysis, health scoring, and proposals work for any project. Pipeline compliance is GIGO-specific and conditional.
- **Read-only on telemetry.** Never modifies `~/.claude/usage-data/`. Reads only.
- **Proposes, never auto-applies.** Every improvement requires operator approval. No auto-fix category — project-level changes always need judgment.
- **Degrades gracefully.** Only ~12% of sessions have facets data. The skill works with meta-only data at lower confidence, clearly flagged.
- **Announce every phase.** Same convention as all GIGO skills.
- **Internal-only initially.** Do not add to README, site, getting-started, or any public-facing content. Add to CLAUDE.md skill list as internal. Validate on 5+ real sessions before promoting to public.

---

## Data Sources

All at `~/.claude/usage-data/`.

### session-meta/{session-id}.json

Per-session telemetry. Always present for every session.

Key fields for retro:
- `project_path` — match sessions to the current project (exact string match)
- `tool_counts` — object mapping tool names to invocation counts (e.g., `{"Read": 104, "Agent": 5, "EnterPlanMode": 1}`)
- `tool_errors` — total error count
- `tool_error_categories` — object mapping error types to counts (e.g., `{"Command Failed": 1}`)
- `user_interruptions` — count of operator interventions
- `user_response_times` — array of seconds between assistant message and next operator input
- `git_commits` / `git_pushes` — what shipped
- `input_tokens` / `output_tokens` — cost
- `lines_added` / `lines_removed` — productivity
- `files_modified` — scope
- `duration_minutes` — session length
- `start_time` — ISO 8601 timestamp
- `first_prompt` — first user message (useful for session identification)
- `uses_task_agent` / `uses_mcp` — execution pattern booleans

### facets/{session-id}.json

Session-level analysis. Present for ~12% of sessions (requires `/insights` to have been run).

Key fields:
- `underlying_goal` — what the session was trying to do (free text)
- `outcome` — enum: `fully_achieved`, `mostly_achieved`, `partially_achieved`, `not_achieved`, `unclear_from_transcript`
- `friction_counts` — object mapping friction types to counts (flexible keys, not a fixed enum)
- `friction_detail` — narrative description of what went wrong
- `user_satisfaction_counts` — object with flexible keys (`happy`, `satisfied`, `likely_satisfied`, `neutral`, `likely_frustrated`, `dissatisfied`)
- `claude_helpfulness` — self-assessed: `essential`, `very_helpful`, `helpful`
- `session_type` — `multi_task`, `single_task`, `exploration`, `iterative_refinement`, `quick_question`
- `goal_categories` — object mapping goal types to counts
- `primary_success` — what worked best
- `brief_summary` — one-line recap

### JSON Parsing Note

Some session-meta files contain control characters. Parse with `strict=False` (Python) or equivalent error-tolerant parsing. Catch and skip files that fail to parse.

---

## Three Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Last session** (default) | No arguments | Deep-dive on the most recent completed session for the current project |
| **Specific session** | Session ID prefix or descriptive text | Deep-dive on the matched session |
| **Aggregate** | "all", "recent", "last N", or explicit time window | Cross-session pattern analysis (default: last 7 days) |

### Mode Detection

1. Resolve the current project's canonical path (from working directory).
2. If `$ARGUMENTS` is empty → **last session mode**. Find the most recent session-meta where `project_path` matches the current project, excluding any session started within the last 5 minutes (likely the current session).
3. If `$ARGUMENTS` is exactly "all", "recent", "aggregate", or matches "last N" (e.g., "last 3") → **aggregate mode**. Check this BEFORE descriptive text matching to avoid misfires on session descriptions containing "all" or "recent". Default window: last 7 days. "last N" uses the N most recent sessions.
4. If `$ARGUMENTS` matches a session ID prefix (8+ hex chars) → **specific session mode**. Find the matching session.
5. If `$ARGUMENTS` contains descriptive text → **specific session mode**. Search `first_prompt` and facets `underlying_goal` for substring matches. If ambiguous (multiple matches), list candidates and ask the operator to pick.

---

## Phase Sequence

All modes follow the same six phases. Each phase is announced to the operator.

### Phase 1: Session Discovery

Read all `~/.claude/usage-data/session-meta/*.json` files. Filter by `project_path` exact match. Sort by `start_time` descending. For each matching session, check if `facets/{session_id}.json` exists.

**Announce:** In single-session mode: "Found session `{id_prefix}` from {date}: '{first_prompt truncated to 80 chars}' ({duration}min, {facets_status})". In aggregate mode: "Found {N} sessions for this project in the last {window}. {M} have facets data."

If no sessions found for this project, stop with: "No session telemetry found for this project. Run `/insights` after a session to generate facets data, or check that the project path matches."

### Phase 2: Friction Analysis

Read `references/analysis-procedure.md` Section 2 (facets path) or Section 2b (meta-only path).

**With facets:** Read `friction_counts`, categorize each friction type, cross-reference against project rules and skill prompts, produce structured findings.

**Without facets:** Apply meta-only heuristic signals, produce lower-confidence findings flagged as `[inferred from meta]`.

**In aggregate mode:** Aggregate friction across sessions. Flag recurring types (same type in 3+ sessions = systemic). Report both per-session breakdowns and cross-session patterns.

**Announce:** "Phase 2: Analyzing friction points... {N} friction points found across {M} sessions."

### Phase 3: Pipeline Compliance (Conditional)

**Gate check:** Read `CLAUDE.md` and `.claude/rules/workflow.md` for the current project. If neither references `gigo:` skills or describes a plan/execute/review pipeline, skip this phase entirely with: "Phase 3: Skipped — no GIGO pipeline detected for this project."

If pipeline detected, read `references/analysis-procedure.md` Section 3. Check `tool_counts` against pipeline expectations. Score each stage as pass / skip / not-applicable.

**Announce:** "Phase 3: Checking pipeline compliance..." then report pass/skip/n-a for each stage.

### Phase 4: Health Score

Read `references/analysis-procedure.md` Section 4. Calculate four-dimension composite score.

**Announce:** "Phase 4: Computing health score..." then display the score with per-dimension breakdown.

### Phase 5: Proposals

Synthesize findings from Phases 2-4 into concrete improvement proposals. Read `references/analysis-procedure.md` Section 5.

Each proposal is one of:
- **`new-rule`** — A `.claude/rules/` entry to prevent recurring friction
- **`remove-rule`** — A rule that appears ineffective based on the friction data
- **`skill-change`** — A specific edit to a SKILL.md or reference file
- **`memory-entry`** — A learning for `.claude/references/` or project memory

Each proposal is triaged as `propose` (clear, evidence-backed) or `discuss` (ambiguous, needs conversation).

**Announce:** "Phase 5: Generating improvement proposals... {N} proposals."

### Phase 6: Present

Display everything to the operator in this order:
1. Session summary (what was analyzed)
2. Health score with dimension breakdown
3. Friction findings (grouped by category)
4. Pipeline compliance results (if applicable)
5. Proposals (numbered, with triage category)

Ask: "Approve proposals by number (e.g., 'approve 1, 3'), discuss specific ones, or 'approve all'."

When the operator approves a proposal, apply the change to the target file. When they reject, skip it. When they want to discuss, enter conversation about that specific proposal.

---

## Friction Analysis Details

### Friction Categories (from facets `friction_counts` keys)

| Friction Type | Category | Addressable By |
|---------------|----------|----------------|
| `wrong_approach`, `misunderstood_request` | **Planning** | Better rules, clearer skill prompts |
| `buggy_code`, `tool_failure`, `tool_limitations` | **Execution** | Tooling improvements, skill fixes |
| `excessive_changes`, `rubber_stamping`, `skipped_gate` | **Pipeline** | Enforcement rules, workflow changes |
| `confusion` | **Planning** | Clearer documentation or rules |
| `deferred_work`, `session_interrupted` | **Completion** | Informational only |

Note: `friction_counts` keys are not a fixed enum. New types may appear. Categorize unknown types as **Uncategorized** and include them in the analysis without skipping.

### Cross-Reference Protocol

For each friction point:
1. Read the **target project's** `.claude/rules/` files (the project being analyzed, not the GIGO plugin) — does a rule exist that should have prevented this friction?
2. If a rule exists but friction still occurred → the rule may be too vague, buried, or unenforceable. Propose strengthening it.
3. If no rule exists → propose a new rule if the friction is recurring (appears in 2+ sessions or has count > 1 in a single session).
4. Check the **target project's** skill prompts (if any) — should a skill have caught this during its workflow?

### Meta-Only Heuristic Signals

When no facets exist, infer friction from session-meta:

| Signal | Threshold | Interpretation |
|--------|-----------|----------------|
| `tool_errors / sum(tool_counts.values())` > 0.10 | High error rate | Tooling friction |
| `user_interruptions` > 2 | Frequent intervention | Possible wrong approach |
| Median of `user_response_times` > 120s | Long operator waits | Session difficulty or disengagement |
| `output_tokens / max(lines_added, 1)` > 500 | High token-to-output ratio | Low efficiency / spinning |
| `duration_minutes > 30` AND `git_commits == 0` | Long session, no output | Stuck session |
| `tool_error_categories` contains "File Not Found" | Missing file references | Stale paths in rules or skills |

Meta-only findings are flagged `[inferred from meta — lower confidence]`. They inform proposals but with weaker evidence than facets-backed findings.

---

## Pipeline Compliance Details

### Detection Heuristics from tool_counts

| Pipeline Stage | tool_counts Key | Applicable When | Points |
|----------------|----------------|-----------------|--------|
| Plan mode entered | `EnterPlanMode` ≥ 1 | `git_commits ≥ 3` OR `duration_minutes ≥ 15` | 30 |
| Plan mode completed | `ExitPlanMode` ≥ 1 | `EnterPlanMode` present | 10 |
| Subagent execution | `Agent` ≥ 2 | `git_commits ≥ 3` | 20 |
| Review ran | `Skill` ≥ 1 | `git_commits ≥ 1` | 25 |
| Snap ran | `Skill` present (imperfect) | Always | 15 |

### Applicability Rules

A session that answered a quick question (1-2 messages, no commits, < 5 minutes) should not be penalized for missing plan mode. The applicability thresholds prevent false negatives on lightweight sessions.

### Known Limitations

Document these in the output so the operator knows confidence level:
- `Skill` counts ALL skill invocations, not just verify — cannot distinguish verify from snap from maintain
- Approval markers (`<!-- approved:`) are in git history, not telemetry — checking them requires git log queries (done in single-session deep-dive, skipped in aggregate for performance)
- Snap detection is unreliable — best proxy is `Skill` at session end, but per-message timing is unavailable
- `Agent` counts include both execution workers and review dispatches — cannot distinguish
- Historical sessions predating blueprint adoption will score 0 on plan mode even if they were substantive — pipeline scores are most meaningful for sessions after the pipeline was established

---

## Health Score

Four dimensions, each 0-100. Combined into a weighted composite.

### Dimension 1: Outcome (weight 0.35)

Requires facets. If unavailable, weight is redistributed.

| `outcome` value | Score |
|-----------------|-------|
| `fully_achieved` | 100 |
| `mostly_achieved` | 75 |
| `partially_achieved` | 40 |
| `not_achieved` | 10 |
| `unclear_from_transcript` | 50 |
| Any other value | 50 |

**Modifier:** If `user_satisfaction_counts` contains `frustrated`, `likely_frustrated`, or `dissatisfied` with combined count > 0, subtract up to 15 points (5 per frustrated/dissatisfied instance, capped at 15).

### Dimension 2: Friction (weight 0.25)

**With facets:** `max(0, 100 - total_friction_count * 12)`. Pipeline friction types (`rubber_stamping`, `skipped_gate`, `excessive_changes`) are double-weighted (count * 2 before applying formula).

**Without facets:** Start at 70. Subtract 10 per `tool_error_categories` entry. Subtract 15 if `user_interruptions > 3`. Subtract 10 if `output_tokens / max(lines_added, 1) > 500`. Floor at 0.

### Dimension 3: Efficiency (weight 0.20)

Always available from session-meta.

Ratio: `output_tokens / max(lines_added + git_commits * 50, 1)`

| Ratio | Score |
|-------|-------|
| < 50 | 100 |
| 50-150 | 85 |
| 150-400 | 70 |
| 400-1000 | 50 |
| 1000-2500 | 30 |
| > 2500 | 15 |

**Edge case:** Exploration sessions (0 lines added AND 0 commits) score 60 (neutral — not penalized for non-output work).

### Dimension 4: Pipeline Adherence (weight 0.20)

GIGO-specific. Only scored when the project has a GIGO pipeline. If not, weight is redistributed.

Score = (earned points / applicable points) * 100, using the points from the Pipeline Compliance table.

### Weight Redistribution

| Context | Outcome | Friction | Efficiency | Pipeline |
|---------|---------|----------|------------|----------|
| GIGO project + facets | 0.35 | 0.25 | 0.20 | 0.20 |
| GIGO project + no facets | — | 0.35 | 0.30 | 0.35 |
| Non-GIGO + facets | 0.45 | 0.30 | 0.25 | — |
| Non-GIGO + no facets | — | 0.50 | 0.50 | — |

### Display

| Score | Label |
|-------|-------|
| 80-100 | Healthy |
| 60-79 | Some friction |
| 40-59 | Significant issues |
| 0-39 | Problematic — deep-dive recommended |

In aggregate mode: weighted average across sessions, weighted by `max(duration_minutes, 1)` (longer sessions contribute more; floor of 1 prevents zero-duration sessions from being silently excluded). Display trend if 3+ sessions: improving / stable / declining.

---

## Proposal Format

### Two Triage Categories

| Category | Meaning | When to use |
|----------|---------|-------------|
| **propose** | Clear, evidence-backed change. Operator approves or rejects. | Friction is concrete, the fix is specific, evidence is strong |
| **discuss** | Ambiguous or cross-cutting. Needs conversation before action. | Pattern is real but the right response is unclear |

No "auto-fix" category. Project-level changes (rules, skill prompts, memory) always need operator judgment.

### Proposal Structure

```
#### {N}. [{propose|discuss}] {One-line description}
**Type:** {new-rule | remove-rule | skill-change | memory-entry}
**Target:** {exact file path}
**Change:** {specific text to add/remove/modify}
**Evidence:** {session ID prefix(es) and what was observed}
**Why:** {which friction this addresses and why the change helps}
```

For `discuss` proposals, replace **Change** with **Question** — what needs to be decided before acting.

### Approval Flow

Operator can:
- `approve 1, 3` — approve specific proposals
- `approve all` — approve everything
- `skip 2` — reject without discussion
- `discuss 2` — enter conversation about that proposal
- `skip all` — reject everything, end retro

When approved, retro applies the change to the target file. If the target file doesn't exist (e.g., a new memory entry or new reference file), create it.

---

## Snap Integration

Add to `.claude/rules/snap.md` after the 11-point audit section, before "Saving New Learnings":

```markdown
## Session Retro (optional)

After the audit, if session telemetry exists for this session (`~/.claude/usage-data/facets/`), offer to invoke `gigo:retro` in last-session mode. Retro proposals feed into the learning-routing table below.
```

This is 3 lines. It does not change the audit itself. The operator can always decline.

---

## Integration Points

| Integration | How |
|-------------|-----|
| **Standalone** | Operator invokes `/gigo:retro` directly |
| **Post-Snap** | Snap offers retro after its audit (see above) |
| **Post-Insights** | After `/insights` runs, retro's SKILL.md documents the pattern: "Run `/gigo:retro` to turn insights into improvements" |

---

## Files to Create

| File | Purpose | Est. Lines |
|------|---------|------------|
| `skills/retro/SKILL.md` | Hub: identity, mode detection, phase sequence, pointers | ~130 |
| `skills/retro/references/analysis-procedure.md` | Spoke: data loading, friction analysis, pipeline compliance, health scoring, proposal generation | ~220 |

## File to Modify

| File | Change | Lines Added |
|------|--------|-------------|
| `.claude/rules/snap.md` | Add "Session Retro (optional)" section after audit | ~3 |

---

## Conventions

- **Phase announcements:** "Phase 1: Discovering sessions...", "Phase 2: Analyzing friction...", etc.
- **Session ID display:** Always show 8-char prefix, not full UUID (e.g., `094277c7`)
- **Confidence labels:** Facets-backed findings have no label. Meta-only findings are tagged `[inferred from meta]`.
- **Friction categories:** Planning, Execution, Pipeline, Completion, Uncategorized. Always capitalized.
- **Proposal numbering:** Sequential integers starting at 1. Stable within a session (don't renumber on approval).
- **Health score display:** Show composite score + per-dimension breakdown. In aggregate, show trend arrow if 3+ sessions.
- **Empty results:** If no friction found, say "No friction detected." If no proposals generated, say "No improvements to propose — session looks healthy." Don't manufacture findings.
- **JSON parsing:** Always use error-tolerant parsing. Skip files that fail. Report count of skipped files if > 0.
- **Project matching:** Exact string match on `project_path`. Do not use substring or startswith — `/Users/x/projects/gigo` should not match `/Users/x/projects/gigo-orchestrator`.

<!-- approved: spec 2026-03-29T21:00:49 by:Eaven -->
