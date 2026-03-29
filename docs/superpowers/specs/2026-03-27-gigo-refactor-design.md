# GIGO Refactor Design

> Rename Avengers Assemble to GIGO. Restructure skills around the proven pipeline. Take superpowers and code-review processes (MIT), make them better, ship them as native GIGO skills.

**Goal:** Transform a team-assembly tool into a team-assembly + execution pipeline tool, informed by 8 phases of eval data proving that assembled context helps planning and review but not execution.

**Core thesis:** Quality of AI input determines quality of output. GIGO ensures good input — expert planning, bare execution, honest review.

---

## 1. The Rename

All Marvel references go. The project becomes GIGO.

| Old | New | Notes |
|---|---|---|
| `gigo` | `gigo` | Repo, skill directories, all references |
| `/gigo` → `gigo:gigo` | First assembly | |
| `/fury` + `/smash` → `gigo:maintain` | Merged — severity auto-detected | |
| `/cap` → `gigo:blueprint` | Absorbs superpowers planning process | |
| `/snap` → `gigo:snap` | Name survives — it's not Marvel-specific | |
| NEW: `gigo:execute` | Bare worker dispatch | |
| NEW: `gigo:verify` | Two-stage review pipeline | |
| NEW: `gigo:eval` | Context effectiveness testing | |

**Nick Fury voice drops.** The assembly skill speaks as itself — direct, opinionated, but not a character.

**This project's team names** (Sage, Forge, Mirror, Scribe, The Voice) — not Marvel, they stay. Conductor is added (see Section 2).

---

## 2. New Persona: Conductor — The Execution Architect

Added to THIS project's team (CLAUDE.md). Owns the execution pipeline.

### Conductor — The Execution Architect

**Modeled after:** The Phase 7 "two kinds of leadership" finding — plan well, let workers work, review honestly
+ Kent Beck's "make the change easy, then make the easy change" — pipeline design makes good output the path of least resistance
+ John Ousterhout's "A Philosophy of Software Design" — complexity belongs in the module (planning), not the interface (worker instructions).

- **Owns:** Execution pipeline design (plan→bare execute→two-stage review), tool detection, subagent context rules, the assembled/bare boundary
- **Quality bar:** The generated workflow produces the proven architecture without requiring the operator to understand why it works.
- **Won't do:** Load workers with context, combine review stages into one, skip tool detection

**What Conductor influences:**
- How `gigo:gigo` generates `workflow.md` — the pipeline structure
- How `gigo:execute` dispatches workers — bare, plan-ordered, parallelizable
- How `gigo:verify` structures two-stage review — spec compliance then engineering quality
- How `gigo:maintain` checks pipeline health
- How `gigo:snap` audits pipeline integrity

**Conductor does NOT replace Forge.** Conductor owns *what the skills produce*. Forge owns *how the skills are built*.

### Reference File: `.claude/references/pipeline-architecture.md`

Conductor's reference material. Contains:
- The proven architecture table (planning=assembled, execution=bare, review=assembled)
- Key findings from each eval phase — compressed, not the full narrative
- Why two review stages, not one or three (Phase 8 data)
- Why workers run bare (Phase 7 data)
- Why personas influence planning (Phase 6 data)
- Pointers to full eval narrative for depth

This file lives in THIS project only. Never generated into operator projects.

---

## 3. Skill Roster (7 Skills)

### Pipeline Flow

The skills chain together with operator gates:

```
Operator triggers gigo:blueprint
  → brainstorm → spec → ordered plan
  → "Plan ready. Review it and tell me when you're ready to execute."
  → Operator approves plan
  → gigo:blueprint invokes gigo:execute with the plan file

gigo:execute runs the plan:
  For each task (respecting dependency order):
    → dispatch bare worker subagent
    → worker completes (DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT)
    → gigo:execute invokes gigo:verify (per-task mode)
      → Stage 1: spec review (gigo's own)
      → Stage 2: engineering review (gigo's own, SHA-range based)
    → if issues found: re-dispatch worker with review feedback, re-review
    → next task
  → all tasks complete
  → gigo:execute reports results to operator
  → operator creates PR
  → gigo:verify (PR mode) invokes code-review:code-review for final gate

Operator triggers gigo:snap at session end
```

**Gates:** Plan approval (operator reviews spec and plan before execution starts). Task-level review (every task reviewed before next starts). Final completion (operator reviews results).

**Context management:** With agent teams (preferred), each teammate has its own context window and auto-loads project CLAUDE.md. The lead coordinates via shared task list and messaging. TaskCompleted hook enforces review at the infrastructure level. With subagent fallback, each worker is a fresh subagent — no context accumulation. With inline fallback, sequential execution in the current session.

### 3.1 `gigo:gigo` — First Assembly

**Takes from:** Current `gigo` skill (our own code).

**What stays the same:**
- Universal discovery framework (7 questions)
- Research depth choice (quick vs deep)
- Persona blending with real authorities
- Two-tier architecture (rules + references)
- Token tax principle, non-derivable rule, line budgets
- Conversational refinement flow
- Pre-write dedup pass

**What changes:**
- Nick Fury voice drops — skill speaks as itself
- Generated `workflow.md` encodes the pipeline (see Section 4)
- Generated `snap.md` adds pipeline health check
- Tool detection: checks for `gigo:blueprint`, `gigo:execute`, `gigo:verify`, `gigo:snap` — if not installed, tells operator to install GIGO plugin
- Persona Calibration and Overwatch sections remain (proven by eval)
- Hawkeye persona renamed (Marvel) — becomes "The Overwatch" or similar functional name

### 3.2 `gigo:blueprint` — Planning

**Takes from:** superpowers:brainstorming + superpowers:writing-plans + our old `/cap` skill. All MIT.

**What we keep from superpowers:brainstorming:**
- One question at a time
- Propose 2-3 approaches with trade-offs
- Write spec to file
- Self-review loop (placeholder scan, internal consistency, scope check, ambiguity check)
- User review gate before proceeding

**What we keep from superpowers:writing-plans:**
- Bite-sized task granularity (2-5 minutes per step)
- File structure mapping before task decomposition
- No placeholders — every step has actual content
- Self-review (spec coverage, placeholder scan, type consistency)
- Plan document structure with header, tasks, steps

**What we keep from cap:**
- Ask 2-3 questions max discipline — superpowers can over-question
- Scaled output (3-5 bullets small, numbered steps medium, phases large)

**What we improve:**
- **Single skill, not two invocations.** Brainstorm → spec → plan is one continuous arc. No handoff friction between brainstorming and writing-plans.
- **Plans include explicit dependency graph.** Each task lists what it blocks and what blocks it. superpowers:writing-plans produces ordered steps but doesn't formalize dependencies.
- **Plans mark parallelizable tasks.** `gigo:execute` needs to know what can run concurrently. The plan is the authority on this.
- **Auto-gap-detection during brainstorming.** If the team hits a domain it lacks expertise in during planning, `gigo:blueprint` flags it and offers to invoke `gigo:maintain` to add a teammate right there. The operator doesn't leave the conversation.
- **Plan header references `gigo:execute`** instead of superpowers execution skills.
- **Spec and plan save locations** follow GIGO conventions, not superpowers paths.
- **Visual companion** — evaluate whether to keep, simplify, or drop. It's token-intensive and may not earn its cost.

**Triggering:** Operator invokes `gigo:blueprint`. After the plan is written and approved, `gigo:blueprint` asks: "Plan ready. Want me to start execution?" If yes, `gigo:blueprint` invokes `gigo:execute` with the plan file. The operator stays in the conversation.

### 3.3 `gigo:execute` — Worker Dispatch

**Takes from:** superpowers:subagent-driven-development process (MIT) + our Phase 7 findings + Claude Code agent teams (experimental).

**Primary mechanism: Claude Code Agent Teams.**

The lead (gigo:execute) has assembled context. It creates tasks in the shared task list with dependency relationships, spawns bare worker teammates, and coordinates. Agent teams give us:
- **Shared task list with auto-unblocking** — tasks auto-unblock when dependencies complete. No custom dependency tracking.
- **Auto-claiming** — teammates claim unblocked tasks automatically. Parallelization is handled by infrastructure.
- **TaskCompleted hook** — invokes `gigo:verify` before any task can be marked done. Per-task review enforced at the infrastructure level.
- **Inter-agent messaging** — workers communicate directly if they discover something another worker needs.
- **Model per teammate** — haiku for mechanical tasks, sonnet for integration, opus for architecture.

**The CLAUDE.md question:** Teammates auto-load project CLAUDE.md. Our Phase 7 data says bare workers perform best. For v1, we accept this — assembled workers still got 3/3 approvals in engineering review, and agent teams' coordination benefits outweigh the theoretical context concern. Test and optimize later with `gigo:eval`.

**Three execution tiers (try in order):**
1. **Agent teams (optimal)** — requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`. Full parallelization, hook-enforced review, inter-worker messaging.
2. **Subagents (good)** — fresh subagent per task via Agent tool. Sequential with manual parallelization. Lead invokes review after each task. Surface warning suggesting agent teams.
3. **Inline (functional)** — sequential in current session. No isolation. Surface warning suggesting subagent support.

**Review is enforced per task.** Via TaskCompleted hook (Tier 1) or manual invocation by the lead (Tier 2/3). Issues are fixed before the next task starts.

**The implementer prompt template (improved):**

```
You are implementing Task N: [task name]

## Task Description
[FULL TEXT of task from plan — don't make subagent read file]

## Context
[Where this fits, dependencies, what was built in prior tasks]

## Before You Begin
If anything is unclear about requirements, approach, or dependencies — ask now.

## Your Job
1. Implement exactly what the task specifies
2. Write tests as the task describes
3. Verify implementation works
4. Commit your work
5. Self-review: completeness, quality, no overbuilding
6. Report back

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT

If you're in over your head, say so. Bad work is worse than no work.
```

**The fix prompt (re-dispatch after review finds issues):**

```
You are fixing issues found in Task N: [task name]

## Review Feedback
[SPECIFIC issues from gigo:verify — what's wrong, where, why it matters]

## Original Task Description
[FULL TEXT of task from plan]

## Your Job
Fix the issues listed above. Don't change anything else.
Run tests. Commit. Report back.

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

Still bare — no personas, no rules. But the worker gets the specific review feedback as context. This is not "assembled context" — it's task-specific feedback the same way the original task spec is task-specific input.

**Triggering:** Invoked by `gigo:blueprint` after plan approval. `gigo:execute` runs the full plan, invoking `gigo:verify` after each task, and reports results when all tasks complete.

### 3.4 `gigo:verify` — Two-Stage Review Pipeline

**Takes from:** superpowers:requesting-code-review + superpowers spec-reviewer-prompt (MIT). Stage 2 invokes code-review:code-review directly — we don't rebuild it.

**The pipeline (validated by Phase 8):**

**Stage 1: Spec Review (GIGO's own)** — "Did the worker build what the plan said?"
- GIGO's own reviewer, built from superpowers' spec-reviewer-prompt.md
- Reviewer gets the plan/spec AND the code
- Reviewer gets the spec as its primary context — the spec already embeds team expertise as concrete requirements. No need for personas in the reviewer. (Open question: test whether adding team context to spec reviewer improves catch rate. Our Phase 8 tested plan-aware vs code-quality, not assembled-reviewer vs bare-reviewer.)
- Checks: missing requirements, extra/unneeded work, misunderstandings, spec deviations
- Keeps the "do not trust the report" adversarial framing from superpowers

**Stage 2: Engineering Review** — "Is the code production-ready?"
- **Per-task (during execution):** GIGO's own engineering review — dispatches focused bare subagents on the git SHA range (base SHA before task, head SHA after task). Modeled on code-review's pattern but operates on committed code, not PRs. Checks: bugs, test quality, architecture, CLAUDE.md compliance. Confidence scored, filtered at ≥80.
- **At PR time (before merge):** Invokes `code-review:code-review` on the actual PR. This is where code-review's full power applies — git history context, prior PR patterns, gh-based commenting. This is a final gate, not a replacement for per-task review.

**Why two modes:** `code-review:code-review` is built around PRs — it uses `gh pr diff`, `gh pr view`, reads prior PR comments. During execution, there's no PR yet, just committed code on a branch. We can't invoke code-review mid-execution. So per-task engineering review is GIGO's own (lightweight, SHA-range based), and the full code-review runs once at PR time.

**Tool-not-installed handling:** If `code-review:code-review` isn't installed when it's time for PR review, `gigo:verify` tells the operator: "Final engineering review works best with the code-review plugin. Install it with `claude install @anthropic/code-review`. I can do an inline review, but it won't be as thorough as 5 focused parallel agents with confidence scoring." Always suggest installing the real thing, fall back with a warning.

**What we improve over superpowers:**
- **Two stages are enforced, never combined.** Phase 8 proved combining averages instead of adding up (11 issues combined vs 10-15 per focused reviewer).
- **Feedback is specific, not categorical.** "This race window between the duplicate check and the insert would manifest under concurrent load" — not "you violated rule 7."
- **Send-back-and-fix loop.** If review finds issues, the implementer fixes them, review runs again. Repeat until approved. superpowers has this; we keep it.
- **Review works standalone.** Can be invoked on any code, not just code produced by `gigo:execute`. Useful for reviewing existing PRs or manual work.
- **Verification before completion.** Absorb the core principle from superpowers:verification-before-completion — evidence before claims. No claiming "tests pass" without running them. No "looks good" without checking. This discipline is baked into the review process, not a separate skill.

**Standalone mode:** When invoked without a plan (operator wants to review a PR or manual work), `gigo:verify` adapts:
- If a plan/spec exists in the project, ask: "Want me to review against the spec, or just engineering quality?"
- If no plan exists, skip Stage 1 (spec review) and run Stage 2 only (engineering review)
- If reviewing a PR, invoke `code-review:code-review` directly (PR mode)
- If reviewing committed code without a PR, run GIGO's own SHA-range engineering review

**Triggering:** Invoked by `gigo:execute` after each task completes (per-task mode). Can also be invoked standalone by the operator on any code (PR review, manual work, etc.). At PR time, invokes `code-review:code-review` for the final gate.

### 3.5 `gigo:snap` — Session-End Audit

**Takes from:** Our own snap skill (not superpowers).

**What stays the same:**
- Two jobs in order: protect (audit), then capture (learnings)
- 9-step audit (line check, derivability, overlap, staleness, cost, persona calibration, total budget, coverage, overwatch)
- Learning routing table
- "If nothing was learned, still run the audit"

**What changes:**
- **Pipeline health check** (new audit step 10): Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed planning and execution? Merged the review stages? If so, flag it and offer to fix.
- **Skill invocation.** If the coverage check finds gaps, snap offers to invoke `gigo:maintain` right there — not "consider running /gigo:maintain."
- **Hawkeye rename** — whatever the overwatch persona becomes, snap checks for it.

### 3.6 `gigo:maintain` — Ongoing Maintenance

**Takes from:** Our own `/fury` + `/smash` skills, merged. Not superpowers.

**Three modes, severity auto-detected:**

1. **Add expertise** (targeted addition) — operator identified a gap, or `gigo:blueprint`/`gigo:snap` detected one. Research, propose persona, merge into team. Same process as current fury targeted-addition.

2. **Health check** (light audit) — coverage, freshness, weight. Three-axis check from current fury health-check. If things look lean, report and done.

3. **Restructure** (heavy audit) — setup is bloated or disorganized. Full smash process: read everything, measure, triage, present plan, execute. Auto-detected when multiple files exceed line caps or structure has drifted significantly.

**Severity detection:**
- Operator says "add X expertise" → mode 1
- Operator says "check on things" / invoked by snap or plan → mode 2, escalate to mode 3 if needed
- Operator says "this is a mess" / line caps blown → mode 3

**What changes from current fury + smash:**
- **Single skill, not two.** The operator doesn't need to know whether their setup needs a light audit or a full restructure. The skill figures it out.
- **Pipeline health** is part of the health check — does the workflow encode the three phases? Are review stages intact?
- **Can be invoked by other skills.** `gigo:blueprint` detects expertise gap → invokes `gigo:maintain` mode 1. `gigo:snap` detects structural drift → invokes `gigo:maintain` mode 2/3. The operator stays in the conversation.

### 3.7 `gigo:eval` — Context Effectiveness Testing

**Takes from:** Our own eval infrastructure built across Phases 1-8.

**Purpose:** Let operators test whether their assembled context actually improves output. Not required for the core pipeline, but valuable for teams that want to prove their setup works — or debug why it doesn't.

**Minimal scope:**
1. Operator provides a task prompt (or eval generates representative prompts from the project)
2. Run the task bare (no CLAUDE.md, no `.claude/`) vs assembled (full context)
3. Comparative judge — same judge sees both outputs, randomized labels, strict criteria
4. Report the delta: where assembled won, where it tied, where it lost, and why

**What we already have:**
- Comparative judging (Phase 7) — eliminates judge-to-judge variance
- Engineering review rubric (Phase 7) — 6-dimension review with letter grades
- Format experiment runner (Phase 7) — swap one variable, hold everything else constant
- Pipeline review test (Phase 8) — test what different review approaches catch
- A/B eval runner (Phases 1-3) — blinded randomized scoring across 5 criteria

**What we build:**
- A skill that wraps this infrastructure for any project, not just our test fixtures
- Prompt generation from project context (suggest representative tasks)
- Summary output that non-eval-experts can act on: "Your personas help planning (+6 rubric points) but hurt creative execution (-2). Consider adjusting Persona Calibration for creative tasks."

**Triggering:** Operator invokes `gigo:eval` directly. Not part of the automatic pipeline — this is an opt-in diagnostic tool.

---

## 4. Generated Output Spec

What `gigo:gigo` produces when it assembles a project.

### 4.1 `CLAUDE.md` — Team Roster

**Same structure as today.** Team name, personas with blended philosophies, autonomy model, quick reference.

No pipeline content here. The team roster is about WHO, not HOW.

**Hawkeye rename:** The overwatch persona at 3+ team members becomes a functional name — "The Overwatch" or "The Auditor" or similar. No Marvel reference.

### 4.2 `.claude/rules/workflow.md` — The Pipeline

**This is the major redesign.** Today it generates a generic loop. The new version encodes the proven pipeline:

```markdown
# Workflow

## How Work Gets Done

### Planning
The team plans together. Brainstorm with full team context — personas
shape the questions, catch architectural gaps, identify edge cases.

Run /gigo:blueprint to brainstorm, write a spec, and produce an ordered plan
with dependencies.

### Execution and Review
Workers execute the plan. Each task gets a bare subagent — no personas,
no rules, just the task description from the plan.

After each task completes, two review passes run automatically:
1. Spec review — compare output against the plan
2. Engineering review — evaluate code quality, bugs, test quality

Issues are fixed before the next task starts.

Run /gigo:execute with the plan file. Review is automatic per task.

### Session End
Run /gigo:snap to audit rules and capture learnings.

## Persona Calibration
[Domain-adapted — same as today, proven by eval]

## Overwatch
[Domain-adapted — structured vs creative, same as today, proven by eval]
```

**What this achieves:**
- Pipeline complexity lives in the skills, not the generated file
- Workflow stays lean (well under 60 lines) and never goes stale
- Skills can improve without touching generated workflows
- Operator can read the workflow and understand the process in 30 seconds

### 4.3 `.claude/rules/standards.md` — Quality Gates

**Same structure as today.** Philosophy (blended authorities), the standard, patterns, anti-patterns, when to go deeper.

No pipeline philosophy. No "two kinds of leadership." Standards are about domain quality, not execution process.

### 4.4 `.claude/rules/snap.md` — The Snap

**Same as today + pipeline health check.** The 9-step audit becomes 10 steps. Step 10:

> **10. Pipeline check.** Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed planning and execution, or merged the review stages? If so, flag it and offer to fix.

### 4.5 `.claude/rules/{extensions}` — Domain Extensions

**Same as today.** Domain-specific rules that apply to every task. Extension file guide unchanged.

### 4.6 `.claude/references/*` — On-Demand Depth

**Same as today.** Reference material loaded when needed. Overwatch checklist, persona character sheets, domain deep-dives.

---

## 5. Skill Consolidation: `/fury` + `/smash` → `gigo:maintain`

### Why Merge

Both skills audit existing setups. `/smash` is just `/fury` at higher severity. The operator shouldn't need to diagnose whether their setup needs a "light audit" or a "full restructure" — the skill figures it out.

### How It Works

The skill reads the current state and auto-detects severity:

| Signal | Mode |
|---|---|
| Operator asks to add expertise | Targeted addition (mode 1) |
| Invoked by gigo:blueprint (expertise gap) or gigo:snap (coverage check) | Health check (mode 2), escalate if needed |
| Operator says "check on things" | Health check (mode 2) |
| Multiple files over line cap, structural drift | Restructure (mode 3) — auto-detected |
| Operator says "this is a mess" | Restructure (mode 3) |

### What Carries Forward

**From fury:**
- Targeted addition procedure (research, propose, merge)
- Health check (coverage, freshness, weight)
- Upgrade checklist (for older setups)
- Hawkeye threshold check on persona addition

**From smash:**
- 6-phase restructure process (read, measure, triage, present, execute, assess)
- 7 triage categories (gold, gold-heavy, gold-narrow, consolidation, derivable, stale, missing)
- Example triage reference

### Cross-Skill Invocation

`gigo:maintain` can be invoked by:
- **`gigo:blueprint`** — "The team doesn't have WebSocket expertise. This gap could produce a weak spec. Want me to add a teammate?" → invokes maintain mode 1
- **`gigo:snap`** — coverage check finds gaps → invokes maintain mode 2
- **Operator directly** — `/gigo:maintain` or natural language

---

## 6. Taking and Improving External Skills

### Source Material (all MIT licensed)

| Source | What We Take | License |
|---|---|---|
| superpowers:brainstorming | Planning process, self-review, visual companion | MIT |
| superpowers:writing-plans | Plan document structure, task granularity, no-placeholder discipline | MIT |
| superpowers:subagent-driven-development | Worker dispatch process, status protocol, prompt templates | MIT |
| superpowers:requesting-code-review | Review dispatch, git SHA capture, feedback handling | MIT |
| superpowers:verification-before-completion | Evidence-before-claims discipline | MIT |
| superpowers:executing-plans | Inline execution fallback pattern | MIT |
| code-review:code-review | Invoked directly for Stage 2 engineering review — not rebuilt | MIT |
| Our own eval infrastructure (Phases 1-8) | Comparative judging, engineering review rubrics, experiment runners | Ours |

### Key Improvements Over Source

1. **Single planning arc.** Brainstorm → spec → plan is one skill (`gigo:blueprint`), not two invocations with a handoff.

2. **Explicit dependency graphs in plans.** Tasks declare what they block and what blocks them. Enables intelligent parallelization in `gigo:execute`.

3. **Workers run bare.** Phase 7 proved this. superpowers injects project CLAUDE.md into workers; we don't.

4. **Review is compositional.** `gigo:verify` works standalone on any code, not just code from `gigo:execute`. Useful for PR review, manual work, etc.

5. **Two review stages enforced.** Phase 8 proved combining averages instead of adding up. Stage 1 is GIGO's own spec reviewer. Stage 2 has two modes: per-task (GIGO's own SHA-range review during execution) and at-PR-time (code-review:code-review for the final gate).

6. **Auto-gap-detection.** `gigo:blueprint` detects missing expertise during brainstorming and offers to add it immediately via `gigo:maintain`. superpowers has no equivalent.

7. **Verification baked in, not bolted on.** Evidence-before-claims is built into the review process, not a separate skill that needs to be remembered and invoked.

8. **Skills invoke each other.** The operator stays in the conversation. No "run this command yourself."

9. **Cap's question discipline.** superpowers:brainstorming can over-question. Cap's "2-3 questions max, one at a time" discipline is proven to be enough.

---

## 7. File Structure After Refactor

```
skills/
├── gigo/
│   ├── SKILL.md                          # First assembly
│   └── references/
│       ├── output-structure.md           # Two-tier architecture spec
│       ├── persona-template.md           # Persona format and examples
│       ├── snap-template.md              # Snap audit template
│       └── extension-file-guide.md       # Domain extension format
├── plan/
│   ├── SKILL.md                          # Brainstorm → spec → plan
│   └── references/
│       ├── planning-procedure.md         # Full planning arc procedure
│       └── example-plan.md               # Worked examples at different scales
├── execute/
│   ├── SKILL.md                          # Worker dispatch
│   └── references/
│       ├── implementer-prompt.md         # Worker prompt template
│       └── model-selection.md            # When to use which model
├── review/
│   ├── SKILL.md                          # Two-stage review pipeline
│   └── references/
│       └── spec-reviewer-prompt.md       # Stage 1 prompt template (Stage 2 = code-review:code-review)
├── eval/
│   ├── SKILL.md                          # Context effectiveness testing
│   └── references/
│       ├── comparative-judging.md        # Judge methodology
│       └── report-format.md             # How to present results
├── snap/
│   └── SKILL.md                          # Session-end audit
└── maintain/
    ├── SKILL.md                          # Add/audit/restructure
    └── references/
        ├── targeted-addition.md          # Mode 1: add expertise
        ├── health-check.md               # Mode 2: light audit
        ├── restructure.md                # Mode 3: heavy restructure
        └── upgrade-checklist.md          # Upgrade older setups
```

---

## 8. This Project's Changes

### CLAUDE.md Updates
- Add Conductor persona
- Rename project identity from "Avengers Assemble" to "GIGO"
- Rename Hawkeye to functional name
- Update skill references throughout

### `.claude/rules/` Updates
- Update all rules files to reference GIGO, not Avengers Assemble
- Update skill references (`/fury` → `gigo:maintain`, etc.)
- Workflow.md updated to reflect new skill roster

### `.claude/references/` Additions
- `pipeline-architecture.md` — Conductor's reference, the "why" behind the pipeline

### spec.md Update
- Rename throughout
- Update skill roster from 5 to 7
- Add pipeline architecture section
- Update trigger conditions for new skill names

---

## 9. Migration Path

### What Existing Users See

If someone ran `/gigo` on their project before the rename, their generated files still work — they reference `.claude/rules/` and `.claude/references/` which don't change structure. The workflow.md they have won't reference GIGO skills (it references the old generic loop), but it still functions.

When they next interact with the tool (now GIGO), `gigo:maintain` can detect the old-format workflow and offer to upgrade it to the pipeline-aware version.

### Upgrade Detection

`gigo:maintain` upgrade checklist adds:
- [ ] Workflow encodes pipeline (plan → execute → review)?
- [ ] Workflow references `gigo:` skills?
- [ ] Snap includes pipeline health check?
- [ ] Overwatch persona has functional name (not Hawkeye)?

---

## 10. Open Questions

1. **Overwatch persona name.** "Hawkeye" is Marvel. Options: "The Overwatch," "The Auditor," "The Critic," "QA." Need to pick one.

2. **Visual companion in `gigo:blueprint`.** superpowers:brainstorming has a browser-based visual companion for mockups. It's token-intensive. Keep, simplify, or drop?

3. **GIGO plugin package structure.** How does this get packaged and distributed as a Claude Code plugin? Need to understand plugin packaging requirements.

4. **Spec reviewer context.** Does the spec reviewer need assembled team context, or is the spec itself sufficient? Phase 8 tested plan-aware vs code-quality review approaches, not whether the reviewer itself needs personas. The memory file `project_review_subagent_context.md` flags this as an open test. Default: spec-only (consistent with "workers run bare" principle).

5. **Eval prompt generation.** How does `gigo:eval` generate representative task prompts from a project it hasn't seen before? Manual prompt authoring works but limits adoption. Automatic generation from project structure + CLAUDE.md would make eval accessible to more teams.
