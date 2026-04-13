# Brief: Execution Architecture Catalog + Agent Teams Preparation

## Origin

Competitive analysis of [revfactory/harness](https://github.com/revfactory/harness). Two things worth taking:

1. **Architecture pattern catalog** — six named execution patterns (Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical Delegation) with decision criteria. GIGO's execution is implicitly "Supervisor" (lead dispatches workers). Having named alternatives helps `gigo:spec` produce better plans.

2. **Agent Teams readiness** — Harness is built around Claude Code's experimental Agent Teams API (`TeamCreate`, `SendMessage`, `TaskCreate`). The API requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. When it stabilizes, GIGO should be ready to use it. Their team-vs-subagent decision tree is sound.

## What to Build

### Part A: Architecture Pattern Catalog (shippable now)

A reference file for `gigo:spec` that helps the planning phase choose the right execution pattern for a given task. Currently, specs always assume "lead dispatches parallel workers" — but some tasks are better served by pipeline (sequential dependencies), fan-out/fan-in (parallel then merge), or producer-reviewer (generate then validate).

This directly improves plan quality without touching the execution engine.

**Patterns to catalog:**

| Pattern | When to use | GIGO mapping |
|---|---|---|
| **Supervisor** (current default) | Central coordinator dispatches workers, collects results | Current `gigo:execute` behavior |
| **Pipeline** | Sequential dependencies — each step needs the previous step's output | Spec should flag sequential tasks and avoid false parallelism |
| **Fan-out/Fan-in** | Independent parallel work followed by a merge step | Current parallel dispatch, but with an explicit merge task |
| **Producer-Reviewer** | Generate then validate | Already exists in verify (spec review → craft review) — generalize it |
| **Expert Pool** | Route to the right specialist based on task type | Useful when assembled team has domain-specific personas |

Skip "Hierarchical Delegation" — it's recursive delegation which adds complexity without clear value for GIGO's use cases.

### Part B: Agent Teams Integration (design now, ship when stable)

Design how `gigo:execute` would use Agent Teams as an alternative execution mode. Key decisions:

- **When teams vs subagents:** Teams when workers need to communicate (cross-review, shared state). Subagents (current) when workers are independent and results flow back to lead.
- **Team composition:** Map assembled personas to team members. The lead becomes the team leader.
- **Data passing:** File-based (current `_workspace/` approach) vs message-based (`SendMessage`) vs task-based (`TaskCreate`).
- **Team lifecycle:** One team per execution, or re-compose between phases?

This part produces a design document and reference files, but doesn't change `gigo:execute` until the API is stable.

## Where It Lands

- **Part A → `gigo:spec`** — planning procedure reads the pattern catalog to choose execution architecture. New reference file: `.claude/references/execution-patterns.md` or similar (in the GIGO plugin's own references, not in assembled projects).
- **Part A → assembled projects** — when `gigo:spec` writes plans, it names the chosen pattern so `gigo:execute` knows the execution shape.
- **Part B → `gigo:execute`** — future alternative to bare subagent dispatch. Design doc lives in GIGO's own references until ready to ship.
- **Part B → `gigo:gigo`/`gigo:maintain`** — assembled projects may eventually get agent team configurations alongside persona definitions.

## Constraints

- Part A must improve planning without breaking existing execution. Specs that name patterns must still work with current `gigo:execute` (which only does Supervisor).
- Part B is design-only until Agent Teams API drops the experimental flag. No shipping half-baked team support.
- The pattern catalog must be domain-agnostic. "Pipeline" applies to software builds, content creation workflows, research synthesis — not just code.
- Token economics: the catalog is reference-tier content in the GIGO plugin itself (loaded when `gigo:spec` runs), not in assembled projects' rules.

## Harness's Decision Tree (for reference)

```
2+ agents needed?
├── Yes → Inter-agent communication needed?
│         ├── Yes → Agent Teams
│         └── No  → Subagents (or teams if cheap)
└── No  → Single subagent
```

Their data-passing protocols:
- **Message-based** (`SendMessage`) — real-time coordination, lightweight
- **Task-based** (`TaskCreate/Update`) — progress tracking, dependencies
- **File-based** (agreed paths) — large artifacts, audit trail
- **Return-value** (Agent tool result) — subagent results to main

## Open Questions

- Does Part A change how `gigo:execute` dispatches workers, or only how `gigo:spec` writes plans? (I'd say plans-only for now.)
- Should the pattern choice be explicit in the spec ("Execution pattern: Fan-out/Fan-in") or implicit (spec structure implies the pattern)?
- For Part B: should team members get full persona context (assembled mode) or stay bare? Our Phase 7 (research) finding says bare workers produce better code — does that hold for team members who need to communicate?
- How do we handle the "one team per session" constraint? Pipeline patterns need team recomposition between phases.

---

**Cycle 1 shipped 2026-04-11.** Part A (Execution Pattern Catalog) is live at `skills/spec/references/execution-patterns.md`. The approved two-cycle design brief is at `.claude/plans/curious-strolling-chipmunk.md`. Cycle 2 (Part B — Agent Teams Rebuild) is formalized at `briefs/04-agent-teams-rebuild.md`.

**Note:** The `_workspace/` reference in the "Harness's Decision Tree" section above is stale — that convention does not exist in GIGO. Data flows through plan "What Was Built" addendums and git branch merges from isolated worktrees. Brief 04 carries this correction forward.
