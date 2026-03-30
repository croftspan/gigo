---
name: retro
description: "Session retrospective — reads Claude Code telemetry and turns friction into project improvements. Analyzes one session or aggregates recent sessions. Produces proposals, not reports. Use gigo:retro."
---

# Retro

Data-driven session retrospective. Reads Claude Code's telemetry (`~/.claude/usage-data/`), identifies friction, checks pipeline compliance, and proposes concrete project improvements. Output is proposals the operator approves — not a report.

No character voice. Direct, evidence-based.

Read `.claude/references/language.md` if it exists. Present all analysis findings, proposals, and conversation in the interface language. If the file doesn't exist, default to English.

**Announce every phase.** As you work, tell the operator what's happening: "Phase 1: Discovering sessions...", "Phase 2: Analyzing friction...", etc. Don't work silently.

---

## Detect Mode

Resolve the current project's canonical path from the working directory.

1. If `$ARGUMENTS` is empty → **last session mode**.
2. If `$ARGUMENTS` is exactly "all", "recent", "aggregate", or matches "last N" (e.g., "last 3") → **aggregate mode**. Check this BEFORE descriptive text. Default window: last 7 days.
3. If `$ARGUMENTS` matches a session ID prefix (8+ hex chars) → **specific session mode**.
4. Otherwise → **specific session mode** via description matching. Search `first_prompt` and facets `underlying_goal` for substring matches. If ambiguous, list candidates and ask the operator to pick.

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
