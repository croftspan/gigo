# Agent Teams: Target-State Design

## Status

**TARGET-STATE DESIGN. NOT SHIPPED. NOT WIRED UP.**

This document describes how `gigo:execute` would integrate with the Claude Code Agent
Teams API once two preconditions are met:

1. **API stability** — the Claude Code Agent Teams API reaches a stable, non-experimental
   interface with reliable session resume and hook enforcement.
2. **Bare-worker tension resolved** — the bare-worker research finding applies to code
   generation. A clear boundary is established between code and non-code workflows so
   teams can operate where they help without contaminating the code path.

Until both preconditions are met, the primary execution path is subagents.

---

## Why Teams

Agent teams expose three platform capabilities that subagents don't provide:

**1. Inter-agent communication via `SendMessage`**
Synchronous messaging allows a worker to surface a blocking question to the lead mid-task,
without waiting for a full review cycle. In subagents, the only channel is the return
value — the worker finishes, reports, waits. With `SendMessage`, a teammate asks, receives
an answer, and continues. This matters in iterative, non-code workflows.

**2. Shared task state visibility**
All team members read from a common task list — each sees what others are working on,
what's blocked, what's complete. In subagents, the lead holds all state and must
synthesize addendums to pass context forward. Shared visibility eliminates that overhead.

**3. Cross-review at the team level**
A reviewer member can read another member's output and respond inline, without routing
through the lead. A dedicated reviewer watches the task list and picks up completed items
directly — reviewer-in-the-loop without lead dispatch overhead.

**Where these benefits apply**

These three capabilities add value in non-code workflows with iterative refinement or
cross-agent negotiation: long-form writing, research synthesis, multi-perspective review.
They do NOT add value in single-pass code generation. Code benefits from bare workers —
teams cannot be bare (see §7). Routing code tasks through a team adds persona loading
cost with no quality gain.

---

## Decision Tree

```
Is the task producing code?
│
├─ YES → Subagents (unconditional)
│         Enforcement point for the bare-worker research finding.
│         Do not route code-producing tasks through teams, even if the API
│         is stable. Team members cannot be bare — CLAUDE.md is auto-loaded.
│
└─ NO  → Is the Claude Code Agent Teams API stable?
          │
          ├─ YES → Teams
          │         Use the team composition rules in §4.
          │         Apply the data-passing protocols in §5.
          │         Follow the lifecycle in §6.
          │
          └─ NO  → Subagents (fallback)
                    Default primary path. Full feature parity except shared
                    state and `SendMessage`. No capability is lost — only
                    the three team-specific capabilities are unavailable.
```

**Dropped gates:** Plan size and single-session requirement were dropped. Plan size is not a
reliable predictor of whether teams help. Single-session requirement created false urgency.
The only gates are task type (code vs non-code) and API stability.

---

## Team Composition

**One team per execution.** A team is spawned at the start of execution and runs to
completion. No mid-execution recomposition — if a pipeline phase requires a different
set of members, fall back to sequential subagent dispatch rather than dissolving and
rebuilding the team.

**Leader.** The lead persona driving `gigo:execute` acts as team leader. The lead owns
spawn, lifecycle management, operator communication, and final review.

**Members.** Members are drawn from the `CLAUDE.md` personas. Map domain-relevant
personas to the tasks they're best suited for, then assign tasks explicitly in the
teammate spawn prompt. Do not allow auto-claim.

**Known cost: `CLAUDE.md` is auto-loaded onto all team members at spawn.** Claude Code
loads project context onto every team member when the team is created. Team members are
NOT bare — they carry persona definitions, rules, and all assembled context. This is a
platform constraint, not a configuration choice. It is the primary reason code tasks
stay on the subagent path.

**Sizing.**
- Aim for ~5–6 tasks per member.
- Keep teams at 2–5 members.
- Start small. A 2-member team running 10 tasks each outperforms a 5-member team
  with tasks spread thin and coordination overhead compounding.

**Rationale for no mid-execution recomposition.** Spawning a new team for each pipeline
phase introduces more overhead than sequential subagent dispatch. The team model works
when a stable member set runs all tasks through to completion.

---

## Data-Passing Protocols

Four modes are available inside an agent team. Choose based on artifact size and
persistence needs.

**Message (`SendMessage`)**
Synchronous inter-member updates. Use for: blocking questions from a worker to the lead,
clarifications needed before proceeding, mid-task pivots, status pings. Keep messages
short — they are transient and not stored beyond the receiving member's context window.

**Task (`TaskCreate` / `TaskUpdate`)**
Persistent work-item state. Use for: tracking completion, recording blocking conditions,
storing structured outputs that other members need to read. The task list is the shared
state layer — it persists across member context windows and survives individual member
turns.

**File (agreed paths)**
Large artifacts. Use for: implementation output, generated documents, analysis results,
anything that exceeds what a task description should hold.

File-based passing means agreed file paths for large artifacts — GIGO today flows data
through plan "What Was Built" addendums and git branch merges, not a dedicated workspace
directory. A workspace convention could be introduced later if teams need it. The string
`_workspace/` is not a GIGO convention and should not be assumed to exist.

**Return-value**
Not applicable inside teams. Return values are the subagent model's output channel. Team
members communicate through the three channels above, not return values.

---

## Team Lifecycle

**1. Spawn (`TeamCreate`)**
The lead calls `TeamCreate` with the team configuration: member personas, model
assignments, and the task list. Each member receives its spawn prompt with explicitly
assigned task numbers. Do not use generic "claim available tasks" prompts — pre-assignment
is required to prevent auto-claim race conditions.

**2. Run phase**
Members execute assigned tasks. Inter-member communication uses the four §5 protocols.
The lead monitors progress via the shared task list and responds to `SendMessage`
escalations. Workers do not communicate directly with each other except through the task
list and file artifacts — direct member-to-member messaging routes through the lead.

**3. Hook enforcement**
When a member calls `TaskCompleted`, the hook invokes `gigo:verify` before the completion
is recorded. If review fails, the member receives feedback and continues working on the
task. If review raises `[ASK-OPERATOR]` items, the hook blocks completion and surfaces
the items to the lead, who routes them to the operator.

**4. Crash handling**
If the team dies mid-execution (API failure, context limit, session crash), do not attempt
partial resume. Spawn a fresh team. Reconcile against plan checkpoints: mark completed
tasks as done, mark in-progress tasks as available. Rebuild the dependency graph from the
plan — do not trust the previous session's task list. A post-crash fresh team replaces the
full team; no mid-execution recomposition.

**5. Teardown (`TeamDelete`)**
After all tasks complete and final review passes, the lead calls `TeamDelete`. Write the
plan's "What Was Built" addendum and final checkpoint after teardown, not before — the
checkpoint records the post-teardown state.

---

## Phase 7 (research) Reconciliation

The Phase 7 (research) bare-worker finding is the central constraint on this design —
why teams are restricted to non-code workflows.

**The bare-worker research finding**
Bare workers — workers dispatched with no persona definitions, no assembled rules, just
the task spec — produce better code than context-loaded workers. The research finding from
Phase 7 (research) is specific to code generation: when the task is producing code,
additional context (personas, rules, style guides) does not improve output and can degrade
it. Worker quality is determined by spec quality, not worker context.

**The platform constraint**
Claude Code auto-loads `CLAUDE.md` onto all team members at spawn. There is no supported
way to spawn a bare team member — the platform enforces context loading. This is not a
configuration gap that a future API version might expose (though it might). It is the
current state of the platform.

**The resolution**
Teams are for non-code workflows only. This is not a compromise — it is the correct
boundary. Non-code work (research synthesis, long-form writing, multi-perspective review)
benefits from persona context. The bare-worker research finding applies specifically to
code generation. By restricting teams to non-code work, the design avoids the tension
entirely: team members carry persona context, which helps them in non-code work, and the
code path stays on the subagent tier where workers can be bare.

**The future relaxation**
If the Claude Code platform adds support for selectively-bare team members — allowing the
lead to specify that a particular member spawns without `CLAUDE.md` context — the
code-producing branch in the decision tree can relax. A bare team member doing code work
would be equivalent to a subagent: same context profile, same research finding applies.
Until that capability exists, the YES branch of the decision tree points unconditionally
to subagents.

The research finding cited here as Phase 7 (research) is documented in
`skills/execute/references/teammate-prompts.md` under "Prompt Design Rationale."

---

## Open Questions

These questions gate parts of the design. They are unresolved at the time of writing.

**1. Selectively-bare team members**
Can the Claude Code Agent Teams API be configured to spawn a member without auto-loading
`CLAUDE.md`? If yes, the code-producing branch in the decision tree can relax. The bare-
worker research finding would apply to bare team members the same way it applies to
subagents. Until the platform documents this capability, assume it is not available.

**2. Pre-assignment reliability**
The experimental API has documented auto-claim race conditions. Pre-assigning tasks in
the spawn prompt is the mitigation, but it is unclear whether pre-assignment is reliably
enforced or whether a fast member can still grab unassigned tasks. Needs empirical testing.

**3. Crash recovery of in-flight team state**
When a team crashes, what state survives? Is the task list recoverable? Are partial
`TaskUpdate` records persisted? §6 assumes plan checkpoints are authoritative and team
state is discarded. If team state is persistable, a more efficient recovery path exists.

**4. Hook integration reliability (`TaskCompleted` with `gigo:verify`)**
The `TaskCompleted` hook invoking `gigo:verify` is untested. Does the hook receive
sufficient context for a meaningful review? Can it block completion reliably? Does
failure mode fail closed (block) or open (allow)?

**5. Non-code team sizing**
The ~5–6 tasks per member guideline is not empirically validated for teams. Non-code work
may have different optimal sizing. Treat as a starting point, not a constraint.

---

## Audit Trail

This document was created as part of Cycle 2, which stripped Tier 3 (Agent Teams)
experimental content from the active execution skill files on **2026-04-12**.

**Files touched by Cycle 2:**

| File | Action |
|---|---|
| `references/review-hook.md` | Deleted — Tier 3 content, no stable platform hook |
| `SKILL.md` | Stripped — Tier 3 section removed, Future pointer added |
| `references/teammate-prompts.md` | Stripped — Tier 3 prompt template removed, rationale preserved |
| `references/model-selection.md` | Stripped — Tier 3 model/sizing table removed |
| `README.md` | Fixed — "agent teams" corrected to "parallel subagents" |
| `references/checkpoint-format.md` | Stripped — Tier 3 reconciliation section removed |

**To recover the deleted `review-hook.md`:**
```bash
git log --all --diff-filter=D -- skills/execute/references/review-hook.md
```

**Reasons for removal — four documented Tier 3 issues:**
1. Auto-claim race conditions in the experimental API defeated pre-assigned parallelism
2. Forced `CLAUDE.md` load on all team members — teams cannot be bare, conflicting with
   the Phase 7 (research) bare-worker finding for code generation
3. No session resume on crash — in-flight team state was not recoverable
4. Higher token cost per task due to full context loading on every member

Plus the Phase 7 (research) bare-worker tension documented in §7 of this file.

**Source briefs and design documents:**
- `briefs/03-execution-architecture-catalog.md` — architecture survey
- `briefs/04-agent-teams-rebuild.md` — the rebuild brief
- `docs/gigo/specs/2026-04-11-agent-teams-rebuild-design.md` — approved design spec
