# gigo:retro — Session Retrospective Skill

## The Problem

The Snap captures learnings at session end but it's manual and relies on the agent's memory of what happened. Claude Code's `/insights` generates rich session telemetry (friction points, satisfaction, tool errors, goal achievement, summaries) but it just sits in a report. Nobody reads it systematically. The croftspan-site session was painful but we only know that because the operator felt it. The data that explains WHY is in the insights.

## What gigo:retro Does

Reads Claude Code's session telemetry and turns it into actionable project improvements. Not a summary. A retrospective that changes things.

## Data Sources

All at `~/.claude/usage-data/`:

### session-meta/{session-id}.json
Per-session data:
- `project_path` — which project
- `tool_counts` — what tools were used and how often
- `tool_errors` / `tool_error_categories` — where things broke
- `user_interruptions` — how often the operator had to intervene
- `user_response_times` — how long the operator waited before responding (frustration signal)
- `git_commits` / `git_pushes` — what shipped
- `input_tokens` / `output_tokens` — cost
- `lines_added` / `lines_removed` — productivity
- `files_modified` — scope
- `uses_task_agent` / `uses_mcp` — execution patterns

### facets/{session-id}.json
Session-level analysis:
- `underlying_goal` — what the session was trying to do
- `outcome` — `fully_achieved` / `mostly_achieved` / `partially_achieved` / `not_achieved`
- `friction_counts` — `wrong_approach`, `confusion`, `tool_limitation`, etc.
- `friction_detail` — specific description of what went wrong
- `user_satisfaction_counts` — `likely_satisfied` / `neutral` / `likely_frustrated`
- `claude_helpfulness` — self-assessed
- `session_type` — `multi_task`, `single_task`, `exploration`, etc.
- `primary_success` — what worked best
- `brief_summary` — one-line recap

### report.html
The full insights report. Aggregates across sessions. Good for trends but the per-session data is more actionable.

## What the Skill Produces

### 1. Friction Analysis
Read the facets for recent sessions on this project. For each friction point:
- What happened (from `friction_detail`)
- Why it happened (compare against project rules and pipeline expectations)
- What to change (new rule, updated skill prompt, memory entry)

### 2. Pipeline Compliance Check
Compare session-meta against what the pipeline expects:
- Did blueprint enter plan mode? (check for EnterPlanMode in tool_counts)
- Did execution use subagents or go inline? (check for Agent tool usage)
- Did review run between tasks? (check for verify invocations)
- Were approval markers written? (check git diff for `<!-- approved:`)
- Was The Snap run at session end?

### 3. Improvement Proposals
Concrete changes to the project:
- Rules that should be added (recurring friction → new guardrail)
- Rules that should be removed (never triggered, wasting tokens)
- Skill prompts that need strengthening (agent consistently does X wrong)
- Memory entries for learnings that apply to future sessions

### 4. Session Health Score
Simple metrics:
- Outcome: did the session achieve its goal?
- Friction: how many intervention points?
- Efficiency: tokens per useful output (commits, files changed)
- Pipeline adherence: did it follow the process?

## Integration Options

### Standalone: `/gigo:retro`
Operator invokes after a session (or reads another session's data). Produces the full retrospective.

### Part of The Snap
Add as an optional step in snap.md: "If insights data exists for this session, run the retro analysis." Makes it automatic.

### Triggered by insights
After `/insights` runs, suggest: "Want to run gigo:retro to turn these findings into project improvements?"

## Design Constraints

- Domain-agnostic. The friction analysis works for code, novels, games. The pipeline compliance check is GIGO-specific.
- Read-only on the telemetry. Never modifies `~/.claude/usage-data/`.
- Proposes changes, doesn't auto-apply. The operator approves improvements just like any other GIGO change.
- Single skill file + reference for the analysis procedure. Hub-and-spoke.
- The session-meta and facets files use session UUIDs. The skill needs to match sessions to the current project via `project_path`.

## Files to Create

| File | Purpose |
|------|---------|
| `skills/retro/SKILL.md` | Hub. Detects mode, reads data, routes to analysis |
| `skills/retro/references/analysis-procedure.md` | The full retrospective procedure |

## The Prompt

The skill reads telemetry and asks:
1. What was this session trying to do? (from facets `underlying_goal`)
2. Did it succeed? (from facets `outcome`)
3. Where did it get stuck? (from facets `friction_counts` + `friction_detail`)
4. Did it follow the pipeline? (from session-meta `tool_counts`)
5. What should change in the project to prevent this friction next time?

The output is not a report. It's a proposal: "Based on this session, here are 3 changes to make." Each change is a specific file edit, rule addition, or memory entry. The operator approves or rejects each one.
