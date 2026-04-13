# Brief: Agent Teams Rebuild (Cycle 2 of Execution Architecture Catalog)

## Origin

Cycle 1 of the Execution Architecture Catalog work (Part A — Execution Pattern Catalog) shipped on 2026-04-11. The approved two-cycle design brief lives at `.claude/plans/curious-strolling-chipmunk.md`. Its Phase 4 "Part B — Agent Teams Rebuild (Cycle 2 sketch)" section covers what this cycle should do.

This brief is the formal Cycle 2 kickoff. Read the source brief for full context, but the summary below is sufficient to start.

## The Cycle is Destructive + Additive

**DESTRUCTIVE:** Rip out Tier 3 (Agent Teams experimental opt-in) from `skills/execute/`.
- Strip `skills/execute/references/review-hook.md`
- Strip Tier 3 templates from `skills/execute/references/teammate-prompts.md`
- Simplify `skills/execute/SKILL.md` to two tiers: **Subagents (primary)** + **Inline (fallback)**

**ADDITIVE:** Add a new `skills/execute/references/agent-teams-design.md`.
- Target-state design doc (~250 lines, reference tier, loaded on demand)
- Blueprints how `gigo:execute` would use Claude Code's Agent Teams API when it stabilizes
- NOT shipped, NOT wired up — pure design

## Critical Constraints (carried from Cycle 1's brief fact-check)

1. **No `_workspace/` convention.** The original brief mentions it, but it doesn't exist in GIGO. Data passing flows through plan "What Was Built" addendums and git branches from isolated worktrees. The design doc must be explicit:
   > "File-based passing means agreed file paths for large artifacts — GIGO today flows data through plan addendums and git branch merges, not a dedicated workspace directory. A workspace convention could be introduced later if teams need it."

2. **Phase 7 disambiguation.** "Phase 7" has two meanings in this project — the bare-worker research finding, and an internal phase of the `gigo:spec` skill. Any reference to the bare-worker finding must be qualified as "the bare-worker research finding" or "Phase 7 (research)" — never bare "Phase 7".

3. **Bare workers vs teams tension.** Phase 7 (research) shows bare workers produce better code. Claude Code auto-loads CLAUDE.md onto all team members — they can't be bare. The resolution from Cycle 1's brief: **teams are for NON-CODE workflows only. Code work stays on subagents.** The design doc must encode this explicitly — the decision tree needs a "code-producing?" branch that keeps code work on subagents.

## Design Doc Outline

The ~250 line `agent-teams-design.md` should have these sections:

1. **Status banner** — "Target-state design. NOT shipped. Implementation waits for API stability and bare-worker tension resolution."
2. **Why teams** — case for teams over subagents (inter-agent communication, cross-review, shared state)
3. **Decision tree** — when to use teams vs subagents vs inline, with the "code-producing?" branch that keeps code work on subagents
4. **Team composition** — one team per execution, leader = lead persona, members mapped from personas with acknowledged CLAUDE.md cost
5. **Data-passing protocols** — Message (`SendMessage`), Task (`TaskCreate`/`TaskUpdate`), File (agreed paths — NOT `_workspace/`), Return-value (N/A inside teams)
6. **Team lifecycle** — single team per execution, no mid-execution recomposition, crash = fresh team from plan checkpoints, Pipeline phases needing different members fall back to subagents
7. **Phase 7 (research) reconciliation** — bare workers produce better CODE; teams can't be bare; therefore teams are for NON-CODE workflows only; code stays on subagents
8. **Open questions** — list the things we can't decide until the API stabilizes (selectively-bare members, pre-assignment reliability, crash recovery, hook integration)
9. **Audit trail** — what was removed from Tier 3, git history pointer

## What Cycle 2 is NOT

- NOT implementing teams. No `TeamCreate`/`SendMessage`/`TaskCreate` calls anywhere in production paths.
- NOT changing the Subagents or Inline tiers.
- NOT modifying `gigo:verify`.

## Verification Plan

After execute completes for Cycle 2:

1. Grep the plugin for `TeamCreate`, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, "Tier 3", "Agent teams" — confirm only the new design doc and its audit trail remain.
2. Run `gigo:execute` on a small test plan. Confirm it offers Subagents (primary) + Inline (fallback) only — no Tier 3 in the options presented.
3. Read `skills/execute/references/agent-teams-design.md` end-to-end. Confirm the status banner is unambiguous and the decision tree is scannable.
4. Verify the design doc's reference tier cost: confirm it's NOT auto-loaded and only reads when the execute SKILL.md pointer fires.

## Sources to Read

- `.claude/plans/curious-strolling-chipmunk.md` — full approved Cycle 1 brief including the Cycle 2 sketch (Part B section)
- `briefs/03-execution-architecture-catalog.md` — original competitive analysis (note: the `_workspace/` claim in this file is stale — see constraint 1 above)
- Current Tier 3 code to rip out:
  - `skills/execute/SKILL.md` (Tier 3 section)
  - `skills/execute/references/review-hook.md`
  - `skills/execute/references/teammate-prompts.md` (Tier 3 templates)
- Cycle 1's catalog for cross-reference: `skills/spec/references/execution-patterns.md`

## Where Cycle 1 Artifacts Live

| Artifact | Path |
|---|---|
| Cycle 1 walkthrough | `docs/gigo/walkthroughs/2026-04-11-execution-pattern-catalog.md` |
| Cycle 1 spec | `docs/gigo/specs/2026-04-11-execution-pattern-catalog-design.md` |
| Cycle 1 plan | `docs/gigo/plans/2026-04-11-execution-pattern-catalog.md` |
| Source design brief (both cycles) | `.claude/plans/curious-strolling-chipmunk.md` |
| The catalog itself | `skills/spec/references/execution-patterns.md` |
| Integration points | `skills/spec/references/planning-procedure.md` §2, `skills/spec/references/example-plan.md`, `skills/spec/SKILL.md:131` |
| Changelog entry | `CHANGELOG.md` (Unreleased → Execution Pattern Catalog section) |

## Starting Point for the New Session

Start with Phase 1 exploration — check current state of Tier 3 in the plugin, map exactly which files and lines reference it, then move to Phase 2 clarifying questions.
