# GIGO Refactor Implementation Plan

> **For agentic workers:** Use `gigo:execute` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename Avengers Assemble to GIGO, restructure from 5 skills to 7, add the Conductor persona, and redesign generated output around the proven plan→execute→review pipeline.

**Architecture:** Rename all files and references first (foundation), then build new skills (execute, review, eval), then update existing skills to reference new names and encode the pipeline, then update this project's own CLAUDE.md and rules.

**Spec:** `docs/superpowers/specs/2026-03-27-gigo-refactor-design.md`

---

## Dependency Graph

```
Task 1: Rename skill directories
  ↓
Task 2: Update this project's CLAUDE.md (add Conductor, rename)
Task 3: Update this project's rules files (rename references)
Task 4: Update spec.md (rename, add pipeline section)
  ↓ (Tasks 2-4 can run in parallel, all depend on Task 1)
Task 5: Create .claude/references/pipeline-architecture.md
  ↓ (depends on Task 2 — needs Conductor defined)
Task 6: Write gigo:gigo SKILL.md (rename + pipeline workflow template)
Task 7: Write gigo:plan SKILL.md + references (new skill, absorbs cap + superpowers)
Task 8: Write gigo:execute SKILL.md + references (new skill)
Task 9: Write gigo:review SKILL.md + references (new skill)
Task 10: Write gigo:snap SKILL.md (update from old snap)
Task 11: Write gigo:maintain SKILL.md + references (merge fury + smash)
Task 12: Write gigo:eval SKILL.md + references (new skill)
  ↓ (Tasks 6-12 can run in parallel, all depend on Tasks 1-4)
Task 13: Update gigo:gigo references (output-structure, persona-template, snap-template, extension-file-guide)
  ↓ (depends on Tasks 6, 10 — needs skill names settled)
Task 14: Clean up old skill directories
  ↓ (depends on all above)
Task 15: Final verification and commit
  ↓ (depends on Task 14)
```

**Parallelizable groups:**
- Tasks 2, 3, 4 (all depend on 1, independent of each other)
- Tasks 6, 7, 8, 9, 10, 11, 12 (all depend on 1-4, independent of each other)

---

### Task 1: Rename Skill Directories

**Files:**
- Move: `skills/avengers-assemble/` → `skills/gigo/`
- Move: `skills/cap/` → `skills/plan/`
- Move: `skills/fury/` → merge into `skills/maintain/` (new)
- Move: `skills/smash/` → merge into `skills/maintain/` (new)
- Move: `skills/snap/` → `skills/snap/` (stays, but content updates)
- Create: `skills/execute/` (new)
- Create: `skills/review/` (new)
- Create: `skills/eval/` (new)

- [ ] **Step 1: Create the new directory structure**

```bash
mkdir -p skills/gigo/references
mkdir -p skills/plan/references
mkdir -p skills/execute/references
mkdir -p skills/review/references
mkdir -p skills/eval/references
mkdir -p skills/maintain/references
```

- [ ] **Step 2: Move avengers-assemble to gigo**

```bash
cp skills/avengers-assemble/SKILL.md skills/gigo/SKILL.md
cp skills/avengers-assemble/references/output-structure.md skills/gigo/references/output-structure.md
cp skills/avengers-assemble/references/persona-template.md skills/gigo/references/persona-template.md
cp skills/avengers-assemble/references/snap-template.md skills/gigo/references/snap-template.md
cp skills/avengers-assemble/references/extension-file-guide.md skills/gigo/references/extension-file-guide.md
```

- [ ] **Step 3: Copy cap files to plan (will be rewritten in Task 7)**

```bash
cp skills/cap/references/planning-procedure.md skills/plan/references/planning-procedure.md
cp skills/cap/references/example-plan.md skills/plan/references/example-plan.md
```

- [ ] **Step 4: Copy fury + smash references to maintain (will be rewritten in Task 11)**

```bash
cp skills/fury/references/targeted-addition.md skills/maintain/references/targeted-addition.md
cp skills/fury/references/health-check.md skills/maintain/references/health-check.md
cp skills/fury/references/upgrade-checklist.md skills/maintain/references/upgrade-checklist.md
cp skills/smash/references/example-triage.md skills/maintain/references/example-triage.md
```

- [ ] **Step 5: Commit the directory setup**

```bash
git add skills/gigo/ skills/plan/ skills/execute/ skills/review/ skills/eval/ skills/maintain/
git commit -m "feat: create GIGO directory structure — rename from Avengers Assemble"
```

---

### Task 2: Update This Project's CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Depends on:** Task 1

- [ ] **Step 1: Read current CLAUDE.md**

Read `CLAUDE.md` to see current content before modifying.

- [ ] **Step 2: Update project identity and add Conductor**

Replace the entire `CLAUDE.md` with updated content. Changes:
1. Rename project from "Avengers Assemble" to "GIGO (Garbage In, Garbage Out)"
2. Update description to reflect team-assembly + execution pipeline
3. Add Conductor persona to The Team section
4. Rename Hawkeye to "The Overwatch" (functional name, no Marvel)
5. Update all skill references: `/avengers-assemble` → `gigo:gigo`, `/fury` → `gigo:maintain`, `/smash` → `gigo:maintain`, `/cap` → `gigo:plan`, `/snap` → `gigo:snap`
6. Add `gigo:execute`, `gigo:review`, `gigo:eval` to Quick Reference
7. Update skill count from 5 to 7
8. Drop "Avengers" from the name throughout — the project is now GIGO

The Conductor persona to add to The Team section:

```markdown
### Conductor — The Execution Architect

**Modeled after:** The Phase 7 "two kinds of leadership" finding — plan well, let workers work, review honestly
+ Kent Beck's "make the change easy, then make the easy change" — pipeline design makes good output the path of least resistance
+ John Ousterhout's "A Philosophy of Software Design" — complexity belongs in the module (planning), not the interface (worker instructions).

- **Owns:** Execution pipeline design (plan→bare execute→two-stage review), tool detection, subagent context rules, the assembled/bare boundary
- **Quality bar:** The generated workflow produces the proven architecture without requiring the operator to understand why it works.
- **Won't do:** Load workers with context, combine review stages into one, skip tool detection
```

The Overwatch persona (replacing Hawkeye):

```markdown
### The Overwatch — Adversarial Output Verification

**Modeled after:** Nassim Taleb's via negativa — value comes from removing bullshit, not adding polish
+ Daniel Kahneman's pre-mortem technique — assume the output failed, then find why
+ The Phase 2b hallucination incident — evals that don't catch bullshit are useless.

- **Owns:** Output verification, drift detection, quality-bar enforcement audit
- **Quality bar:** Every response survives the question "did you actually do what you claimed?"
- **Won't do:** Let persona language substitute for substance, let generic answers wear domain costumes, let references go unread
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: rename to GIGO, add Conductor persona, rename Hawkeye to The Overwatch"
```

---

### Task 3: Update This Project's Rules Files

**Files:**
- Modify: `.claude/rules/workflow.md`
- Modify: `.claude/rules/standards.md`
- Modify: `.claude/rules/skill-engineering.md`
- Modify: `.claude/rules/snap.md`

**Depends on:** Task 1

- [ ] **Step 1: Read all four rules files**

Read each file to see current content.

- [ ] **Step 2: Update workflow.md**

Replace all references:
- "Avengers Assemble" → "GIGO"
- `/avengers-assemble` → `gigo:gigo`
- `/fury` → `gigo:maintain`
- `/smash` → `gigo:maintain`
- `/cap` → `gigo:plan`
- `/snap` → `gigo:snap`
- Add references to `gigo:execute`, `gigo:review`, `gigo:eval` where appropriate
- Update the "Skill Development Pattern" to reference new skill paths (`skills/gigo/`, `skills/plan/`, etc.)

- [ ] **Step 3: Update standards.md**

Replace all references:
- "Avengers Assemble" → "GIGO"
- All skill name references
- "Hawkeye" → "The Overwatch"

- [ ] **Step 4: Update skill-engineering.md**

Replace all references:
- "Avengers Assemble" → "GIGO"
- All skill name references
- Update "When to Go Deeper" pointers to reference new paths

- [ ] **Step 5: Update snap.md**

Replace all references:
- "Avengers Assemble" → "GIGO"
- `/fury` → `gigo:maintain`
- `/smash` → `gigo:maintain`
- `/avengers-assemble` → `gigo:gigo`
- "Hawkeye" → "The Overwatch"
- Add pipeline health check as audit step 10:
  ```
  **10. Pipeline check.** Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed planning and execution? Merged the review stages? If so, flag it and offer to fix.
  ```

- [ ] **Step 6: Commit**

```bash
git add .claude/rules/
git commit -m "feat: update all rules files — GIGO naming, pipeline health check in snap"
```

---

### Task 4: Update spec.md

**Files:**
- Modify: `spec.md`

**Depends on:** Task 1

- [ ] **Step 1: Read spec.md**

Read `spec.md` to see current content.

- [ ] **Step 2: Update spec.md**

Changes:
1. Rename "Avengers Assemble" → "GIGO" throughout
2. Update skill roster from 5 to 7 (add execute, review, eval)
3. Update skill names: `/avengers-assemble` → `gigo:gigo`, `/fury` → `gigo:maintain`, `/smash` → `gigo:maintain`, `/cap` → `gigo:plan`, `/snap` → `gigo:snap`
4. Add pipeline architecture section describing the plan→execute→review flow
5. Update trigger conditions for new skill names
6. Add Conductor to the team roster section
7. Replace "Nick Fury" references with neutral skill voice
8. Replace "Hawkeye" with "The Overwatch"
9. Update routing logic to include new skills (execute, review, eval)
10. Note that `gigo:maintain` replaces both fury and smash with auto-detected severity

- [ ] **Step 3: Commit**

```bash
git add spec.md
git commit -m "feat: update spec.md — GIGO naming, 7 skills, pipeline architecture"
```

---

### Task 5: Create Pipeline Architecture Reference

**Files:**
- Create: `.claude/references/pipeline-architecture.md`

**Depends on:** Task 2

- [ ] **Step 1: Write pipeline-architecture.md**

This is Conductor's reference material. Create `.claude/references/pipeline-architecture.md` with:

```markdown
# Pipeline Architecture — Why It Works This Way

Reference material for the Conductor persona. This explains the "why" behind the plan→bare execute→two-stage review pipeline. The eval narrative at `evals/EVAL-NARRATIVE.md` has the full data trail.

## The Proven Architecture

| Phase | Context | Why (eval phase) |
|---|---|---|
| Planning (brainstorm, spec, plan) | Assembled ON | Personas shape questions, catch architectural gaps (Phase 6) |
| Execution (all work) | Bare | Workers produce best output with training alone + good spec (Phase 7) |
| Review Stage 1 (spec compliance) | Spec as context | Catches "you built the wrong thing" (Phase 8) |
| Review Stage 2 (engineering quality) | Bare workers | Catches "you built it wrong" — race conditions, lock ordering, test quality (Phase 8) |

## Why Workers Run Bare (Phase 7)

Tested 4 context formats: war stories (468 words), compressed (287), fix-only (229), bare (0). Three runs, comparative judging.

- Bare was rated senior or staff by principal engineer review every time
- Compressed (terse rules) produced the worst code every run — real bugs found
- The delta between formats was noise. The delta between good spec and bad spec was signal.
- Workers don't need to know WHY partial unique indexes matter — they need a spec that SAYS to use one

## Why Two Review Stages, Not One (Phase 8)

Tested plan-aware, code-quality, and combined review on 4 code variants.

- Plan-aware found: expired reservation cancellation inflating inventory, missing expiry enforcement, duplicate check outside transaction
- Code-quality found: transaction-return footgun, broken concurrency tests, deadlock from inconsistent lock ordering, non-atomic operations
- Combined found FEWER issues than either focused reviewer alone (11 vs 10-15)
- One reviewer holding both lenses averages instead of adding up

## Why Personas Influence Planning (Phase 6)

Controlled test: same task, same scripted answers, only variable was team personas.

- Assembled asked FEWER questions (7 vs 10) — standards pre-answered some
- Assembled asked WHY-driven questions — "Kane needs to know scale for migration lock duration"
- Assembled caught: partial unique index, SKIP LOCKED, copy condition field, pagination, runnable test code
- Bare missed ALL of these

## Key Insight

Knowledge is in the right place at the right time:
- **Planning:** Knowledge lives in the team's questions
- **Execution:** Knowledge lives in the spec's requirements
- **Review:** Knowledge lives in the team's judgment

Trying to put knowledge into the worker's context solves the wrong problem.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/references/pipeline-architecture.md
git commit -m "feat: add pipeline architecture reference — Conductor's why-it-works doc"
```

---

### Task 6: Write gigo:gigo SKILL.md

**Files:**
- Modify: `skills/gigo/SKILL.md`

**Depends on:** Tasks 1-4

- [ ] **Step 1: Read current skills/gigo/SKILL.md**

This was copied from avengers-assemble in Task 1. Read it.

- [ ] **Step 2: Rewrite SKILL.md**

Take the current avengers-assemble SKILL.md and apply these changes:

1. **Frontmatter:** Update name to `gigo`, update description to reference GIGO not Avengers Assemble. Update trigger conditions: "Use this skill when the user wants to start a new project, set up Claude Code for a project, kick off work in an unfamiliar field, or says 'gigo.'"

2. **Drop Nick Fury voice.** Replace "You are Nick Fury" with neutral skill voice: "You're assembling the best team in the field for this project. Your job is to research the domain, find the authorities, blend their philosophies into focused expert personas, and scaffold a Claude Code project." Direct, opinionated, but not a character.

3. **Update all skill references:**
   - `/avengers-assemble` → `gigo:gigo`
   - `/fury` → `gigo:maintain`
   - `/smash` → `gigo:maintain`
   - `/cap` → `gigo:plan`
   - `/snap` → `gigo:snap`
   - Add mentions of `gigo:execute`, `gigo:review` where relevant

4. **Update "This skill is for first assembly only" block:** Reference `gigo:maintain` and `gigo:maintain` (not fury and smash).

5. **Update Output Structure section:** Reference `gigo:snap` and add note that generated `workflow.md` now encodes the pipeline (pointing to new workflow template in references/output-structure.md).

6. **Replace Hawkeye references** with "The Overwatch" in Principles section (Principle 10).

7. **Update references pointers** to use `references/` (relative, within skills/gigo/).

8. **Add Principle 11:** "Skills invoke each other. When the operator needs more expertise, offer to run `gigo:maintain` — don't tell them to run a command."

- [ ] **Step 3: Verify the file is under 500 lines**

The current file is 174 lines. Changes should keep it in the same range.

- [ ] **Step 4: Commit**

```bash
git add skills/gigo/SKILL.md
git commit -m "feat: rewrite gigo:gigo — drop Fury voice, update all references to GIGO naming"
```

---

### Task 7: Write gigo:plan SKILL.md + References

**Files:**
- Create: `skills/plan/SKILL.md`
- Modify: `skills/plan/references/planning-procedure.md`
- Modify: `skills/plan/references/example-plan.md`

**Depends on:** Tasks 1-4

This skill absorbs superpowers:brainstorming + superpowers:writing-plans + old cap. Build it from the superpowers source (MIT) with GIGO improvements.

- [ ] **Step 1: Read the source skills**

Read these files (already read earlier in the session, but the worker should read them):
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.6/skills/brainstorming/SKILL.md`
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.6/skills/writing-plans/SKILL.md`
- `skills/plan/references/planning-procedure.md` (copied from cap)
- `skills/plan/references/example-plan.md` (copied from cap)

- [ ] **Step 2: Write skills/plan/SKILL.md**

Create the unified planning skill. Key structure:

```markdown
---
name: plan
description: "Brainstorm, write specs, and produce ordered implementation plans. Use when the user has an idea, feature, or task that needs planning — from vague intent to detailed execution-ready plan. Handles the full arc: explore → design → spec → plan. Use gigo:plan or /plan."
---

# Plan

[Skill content — see detailed guidance below]
```

**Content structure for SKILL.md (hub, under 500 lines):**

1. **Identity:** No character voice. Direct, opinionated. "You turn ideas into execution-ready plans."

2. **The Full Arc:** Brainstorm → spec → plan is one continuous flow. No handoff.
   - Phase 1: Understand (ask 2-3 questions max, one at a time — cap's discipline)
   - Phase 2: Explore approaches (propose 2-3 with trade-offs and recommendation)
   - Phase 3: Present design (in sections, get approval per section)
   - Phase 4: Write spec (to `docs/specs/YYYY-MM-DD-<topic>-design.md`)
   - Phase 5: Spec self-review (placeholder scan, consistency, scope, ambiguity)
   - Phase 6: User reviews spec
   - Phase 7: Write plan (ordered tasks with dependency graph)
   - Phase 8: Plan self-review (spec coverage, placeholder scan, type consistency)
   - Phase 9: User reviews plan
   - Phase 10: Offer execution ("Plan ready. Want me to start execution?" → invoke gigo:execute)

3. **Auto-gap-detection:** During brainstorming, if the team lacks expertise: "The team doesn't have [X] expertise. This gap could produce a weak spec. Want me to add a teammate?" → invoke gigo:maintain.

4. **Plan format improvements over superpowers:writing-plans:**
   - Each task lists `blocks:` and `blocked-by:` fields
   - Tasks marked as `parallelizable: true/false`
   - Plan header references `gigo:execute`
   - No TDD mandate — plan specifies testing approach per task

5. **Pointers to references:** "Read `references/planning-procedure.md` for the detailed step-by-step. Read `references/example-plan.md` for worked examples."

- [ ] **Step 3: Update skills/plan/references/planning-procedure.md**

Rewrite to combine:
- Cap's 4-step procedure (listen, ask, plan, recommend)
- Superpowers:brainstorming's process (context exploration, approaches, design sections, spec writing, self-review)
- Superpowers:writing-plans' plan writing process (file structure mapping, bite-sized tasks, no placeholders)

Add:
- Dependency graph format for tasks
- Parallelization marking
- Auto-gap-detection procedure
- Execution handoff (invoke gigo:execute, not superpowers)

- [ ] **Step 4: Update skills/plan/references/example-plan.md**

Keep cap's 3 worked examples (small/medium/large). Update to include:
- Dependency graph syntax (`blocks:`, `blocked-by:`, `parallelizable:`)
- GIGO plan header (referencing gigo:execute)
- Remove any Marvel references

- [ ] **Step 5: Commit**

```bash
git add skills/plan/
git commit -m "feat: write gigo:plan — unified brainstorm→spec→plan, absorbs cap + superpowers planning"
```

---

### Task 8: Write gigo:execute SKILL.md + References

**Files:**
- Create: `skills/execute/SKILL.md`
- Create: `skills/execute/references/implementer-prompt.md`
- Create: `skills/execute/references/model-selection.md`

**Depends on:** Tasks 1-4

Build from superpowers:subagent-driven-development (MIT) + Phase 7 findings.

- [ ] **Step 1: Read the source skill**

Read: `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.6/skills/subagent-driven-development/SKILL.md`

- [ ] **Step 2: Write skills/execute/SKILL.md**

```markdown
---
name: execute
description: "Execute implementation plans by dispatching bare worker subagents per task, with per-task review via gigo:review. Respects dependency ordering and parallelizes independent tasks. Use when you have an approved plan from gigo:plan."
---

# Execute

[Skill content — see detailed guidance below]
```

**Content structure for SKILL.md:**

1. **Core principle:** Bare workers + good spec = senior/staff code. No assembled context injection.

2. **The process:**
   - Read plan, extract all tasks with dependency graph
   - Create task tracking (TodoWrite)
   - For each task (respecting dependency order):
     - Dispatch bare worker subagent with implementer prompt
     - Handle status (DONE → review, DONE_WITH_CONCERNS → review + address, NEEDS_CONTEXT → ask operator, BLOCKED → skip to independent tasks or escalate)
     - Invoke gigo:review (per-task mode)
     - If issues: re-dispatch worker with fix prompt + review feedback
     - Mark task complete
   - Report results to operator

3. **Parallelization:** Read dependency graph. Tasks with no unresolved blockers can run in parallel. Never dispatch tasks whose blockers haven't completed.

4. **Inline fallback:** If subagents aren't available, fall back to sequential inline execution with warning.

5. **Status handling:** Full spec of DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED behavior (from spec Section 3.3).

6. **Model selection:** Pointer to `references/model-selection.md`.

7. **Prompt templates:** Pointer to `references/implementer-prompt.md`.

8. **Context management:** Each worker and reviewer is a fresh subagent. No accumulation across tasks.

- [ ] **Step 3: Write skills/execute/references/implementer-prompt.md**

Two prompt templates:

**Implementation prompt:**
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

**Fix prompt (re-dispatch after review finds issues):**
```
You are fixing issues found in Task N: [task name]

## Review Feedback
[SPECIFIC issues from gigo:review — what's wrong, where, why it matters]

## Original Task Description
[FULL TEXT of task from plan]

## Your Job
Fix the issues listed above. Don't change anything else.
Run tests. Commit. Report back.

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

- [ ] **Step 4: Write skills/execute/references/model-selection.md**

From superpowers:subagent-driven-development's model selection section:

```markdown
# Model Selection for Worker Dispatch

Use the least powerful model that can handle each role.

| Task complexity | Signals | Model |
|---|---|---|
| Mechanical | Touches 1-2 files, complete spec, isolated function | Fast/cheap (haiku) |
| Integration | Multiple files, integration concerns, pattern matching | Standard (sonnet) |
| Architecture/judgment | Design decisions, broad codebase understanding, debugging | Most capable (opus) |

Review subagents: use standard model (sonnet) — they need judgment but have focused scope.
```

- [ ] **Step 5: Commit**

```bash
git add skills/execute/
git commit -m "feat: write gigo:execute — bare worker dispatch with dependency graph and per-task review"
```

---

### Task 9: Write gigo:review SKILL.md + References

**Files:**
- Create: `skills/review/SKILL.md`
- Create: `skills/review/references/spec-reviewer-prompt.md`

**Depends on:** Tasks 1-4

Build from superpowers:requesting-code-review + spec-reviewer-prompt (MIT) + Phase 8 findings.

- [ ] **Step 1: Read source files**

Read:
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.6/skills/requesting-code-review/SKILL.md`
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.6/skills/subagent-driven-development/spec-reviewer-prompt.md`
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.6/skills/subagent-driven-development/code-quality-reviewer-prompt.md`
- `~/.claude/plugins/cache/claude-plugins-official/code-review/61c0597779bd/commands/code-review.md`

- [ ] **Step 2: Write skills/review/SKILL.md**

```markdown
---
name: review
description: "Two-stage code review: spec compliance (did you build the right thing?) then engineering quality (is the code good?). Invoked automatically by gigo:execute after each task, or standalone on any code. Use gigo:review or /review."
---

# Review

[Skill content — see detailed guidance below]
```

**Content structure for SKILL.md:**

1. **Two stages, never combined.** Phase 8 proved combining averages instead of adding up.

2. **Stage 1: Spec Review (GIGO's own)**
   - Dispatch spec reviewer subagent with spec-reviewer-prompt
   - Reviewer gets the plan/spec AND the code
   - Checks: missing requirements, extra work, misunderstandings, spec deviations
   - "Do not trust the report" adversarial framing
   - Output: ✅ compliant or ❌ issues with file:line references

3. **Stage 2: Engineering Review**
   - **Per-task mode (during execution):** GIGO's own engineering review — dispatch focused bare subagent on git SHA range. Checks: bugs, test quality, architecture, CLAUDE.md compliance. Confidence scored, filtered at ≥80.
   - **PR mode (at merge time):** Invoke `code-review:code-review` on the actual PR. If not installed, warn and offer inline fallback.

4. **Standalone mode:** When invoked without a plan:
   - If plan/spec exists, ask: "Review against spec, or just engineering quality?"
   - If no plan, skip Stage 1, run Stage 2 only
   - If reviewing a PR, invoke code-review:code-review (PR mode)
   - If reviewing commits without PR, run SHA-range engineering review

5. **Send-back-and-fix loop:** If issues found, return feedback to caller (gigo:execute re-dispatches worker). Repeat until approved.

6. **Verification before completion:** Evidence before claims. No "tests pass" without running them. Baked in, not a separate skill.

7. **Tool-not-installed handling:** If code-review:code-review isn't installed at PR time, surface it with install instructions and fall back with warning.

- [ ] **Step 3: Write skills/review/references/spec-reviewer-prompt.md**

Based on superpowers' spec-reviewer-prompt.md:

```markdown
# Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify the implementation matches its specification — nothing more, nothing less.

## Template

You are reviewing whether an implementation matches its specification.

### What Was Requested
[FULL TEXT of task requirements from the plan]

### What the Implementer Claims They Built
[From implementer's status report]

### CRITICAL: Do Not Trust the Report

The implementer may be optimistic. Verify everything independently.

**DO NOT:**
- Take their word for what they implemented
- Trust their claims about completeness
- Accept their interpretation of requirements

**DO:**
- Read the actual code they wrote
- Compare actual implementation to requirements line by line
- Check for missing pieces they claimed to implement
- Look for extra features they didn't mention

### Your Job

Read the implementation code and verify:

**Missing requirements:**
- Did they implement everything requested?
- Are there requirements they skipped?
- Did they claim something works but didn't actually implement it?

**Extra/unneeded work:**
- Did they build things not requested?
- Did they over-engineer or add unnecessary features?

**Misunderstandings:**
- Did they interpret requirements differently than intended?
- Did they solve the wrong problem?

**Verify by reading code, not by trusting report.**

Report:
- ✅ Spec compliant (if everything matches after code inspection)
- ❌ Issues found: [list specifically what's missing or extra, with file:line references]
```

- [ ] **Step 4: Commit**

```bash
git add skills/review/
git commit -m "feat: write gigo:review — two-stage pipeline, spec compliance + engineering quality"
```

---

### Task 10: Write gigo:snap SKILL.md

**Files:**
- Modify: `skills/snap/SKILL.md`

**Depends on:** Tasks 1-4

- [ ] **Step 1: Read current skills/snap/SKILL.md**

Read the current file (18 lines).

- [ ] **Step 2: Rewrite SKILL.md**

Update the snap skill:

```markdown
---
name: snap
description: "Run The Snap — audit rules for bloat, staleness, and derivability, then capture session learnings. Use when wrapping up a session, saving progress, or when the user says 'snap.' Requires an existing .claude/rules/snap.md in the project."
---

# The Snap

*Whatever it takes to protect the project.*

You are The Snap — the project's immune system. You don't add. You audit first, save second.

## Run It

1. **Check for snap.md.** Read `.claude/rules/snap.md`. If it doesn't exist, stop: "No snap protocol found. Run `gigo:gigo` to set up the project, or `gigo:maintain` to restructure an existing one."

2. **Follow the protocol.** The project's `snap.md` contains the full audit procedure and learning-routing table, customized for this project's domain. Read it and execute it exactly.

3. **Pipeline check.** After the standard audit, verify: Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed them? If so, flag it and offer to fix.

4. **Coverage gaps.** If the audit finds coverage gaps, offer to invoke `gigo:maintain` to add expertise — don't tell the operator to run a command.

That's it. The snap protocol lives in the project, not here. This skill just makes it invocable and adds pipeline-aware checks.
```

- [ ] **Step 3: Commit**

```bash
git add skills/snap/SKILL.md
git commit -m "feat: update gigo:snap — GIGO naming, pipeline check, auto-invoke maintain"
```

---

### Task 11: Write gigo:maintain SKILL.md + References

**Files:**
- Create: `skills/maintain/SKILL.md`
- Modify: `skills/maintain/references/targeted-addition.md`
- Modify: `skills/maintain/references/health-check.md`
- Create: `skills/maintain/references/restructure.md`
- Modify: `skills/maintain/references/upgrade-checklist.md`

**Depends on:** Tasks 1-4

Merges fury + smash into one skill with auto-detected severity.

- [ ] **Step 1: Read source skills**

Read:
- `skills/maintain/references/targeted-addition.md` (copied from fury)
- `skills/maintain/references/health-check.md` (copied from fury)
- `skills/maintain/references/upgrade-checklist.md` (copied from fury)
- `skills/maintain/references/example-triage.md` (copied from smash)
- The original fury SKILL.md and smash SKILL.md (already read)

- [ ] **Step 2: Write skills/maintain/SKILL.md**

```markdown
---
name: maintain
description: "Ongoing maintenance for your assembled expert team. Add expertise, audit for bloat, restructure messy setups, or upgrade older projects. Auto-detects severity — targeted addition, health check, or full restructure. Use gigo:maintain, /maintain, or when gigo:plan or gigo:snap detect gaps."
---

# Maintain

[Skill content — see detailed guidance below]
```

**Content structure for SKILL.md:**

1. **Identity:** No Fury voice. Direct, confident. "You know this project's team because you assessed it. When something's missing, you say so."

2. **Detect mode:**
   - Read all existing files first (CLAUDE.md, .claude/rules/*, .claude/references/)
   - **Mode 1 (Targeted Addition):** Operator or another skill identified a specific gap. Go to `references/targeted-addition.md`.
   - **Mode 2 (Health Check):** General checkup, invoked by snap or plan, or operator says "check on things." Go to `references/health-check.md`. Escalate to Mode 3 if multiple files over cap or structural drift detected.
   - **Mode 3 (Restructure):** Bloated or disorganized setup. Full smash process. Go to `references/restructure.md`.
   - **Upgrade:** Operator says "upgrade" or old AA format detected. Go to `references/upgrade-checklist.md`.

3. **Pipeline health** is part of every mode — does the workflow encode plan→execute→review? Are review stages intact?

4. **Can be invoked by other skills.** gigo:plan and gigo:snap can invoke maintain directly.

5. **Principles:** Same as current fury/smash but consolidated, Fury voice removed, all references updated to GIGO naming, "The Overwatch" not "Hawkeye."

- [ ] **Step 3: Update references/targeted-addition.md**

Update all references from fury/avengers-assemble to GIGO naming. Replace Hawkeye with The Overwatch. Replace "Fury" voice. Update persona-template reference to `gigo/references/persona-template.md`.

- [ ] **Step 4: Update references/health-check.md**

Update all references. Add pipeline health to the three-axis check (coverage, freshness, weight → add pipeline integrity as fourth axis).

- [ ] **Step 5: Create references/restructure.md**

Extract smash's Phase 1-6 process into this reference file. Update all references from smash/avengers-assemble to GIGO naming. Replace Fury/Hulk voice. Update persona-template and output-structure references. Add pipeline check to Phase 2 (measure) and Phase 5 (execute — ensure pipeline workflow is generated).

- [ ] **Step 6: Update references/upgrade-checklist.md**

Update all references. Add new upgrade checks:
- [ ] Workflow encodes pipeline (plan → execute → review)?
- [ ] Workflow references `gigo:` skills?
- [ ] Snap includes pipeline health check?
- [ ] Overwatch persona has functional name (not Hawkeye)?

- [ ] **Step 7: Commit**

```bash
git add skills/maintain/
git commit -m "feat: write gigo:maintain — merge fury + smash, auto-detect severity, pipeline health"
```

---

### Task 12: Write gigo:eval SKILL.md + References

**Files:**
- Create: `skills/eval/SKILL.md`
- Create: `skills/eval/references/comparative-judging.md`
- Create: `skills/eval/references/report-format.md`

**Depends on:** Tasks 1-4

Build from our own eval infrastructure (Phases 1-8).

- [ ] **Step 1: Read existing eval infrastructure**

Read:
- `evals/EVAL-NARRATIVE.md` (already read — reference for methodology)
- Scan `evals/` directory for existing scripts and rubrics

- [ ] **Step 2: Write skills/eval/SKILL.md**

```markdown
---
name: eval
description: "Test whether your assembled context actually improves AI output. Runs tasks bare vs assembled, uses comparative judging, reports the delta. Use gigo:eval when you want to prove your setup works or debug why it doesn't."
---

# Eval

[Skill content — see detailed guidance below]
```

**Content structure for SKILL.md:**

1. **Purpose:** Opt-in diagnostic. Not part of the automatic pipeline.

2. **The process:**
   - Operator provides task prompt(s) or eval suggests representative prompts
   - Run each task twice: bare (no CLAUDE.md, no .claude/) vs assembled (full context)
   - Comparative judge: same judge sees both outputs, randomized labels, strict criteria
   - Report the delta with actionable recommendations

3. **Methodology pointers:** "Read `references/comparative-judging.md` for judge setup. Read `references/report-format.md` for output structure."

4. **Minimal scope:** Start with manual prompt authoring. Automatic generation is a future enhancement.

- [ ] **Step 3: Write skills/eval/references/comparative-judging.md**

Document the methodology proven across Phases 1-8:

- Same judge sees all variants (eliminates judge-to-judge variance)
- Randomized labels (A/B, not bare/assembled)
- Strict senior engineer persona for the judge
- Full spec/context given to judge for informed evaluation
- 5 criteria: quality bar enforcement, persona voice, expertise routing, specificity, pushback quality
- Engineering review option: 6 dimensions with letter grades for deeper analysis
- Multiple runs to average out noise

- [ ] **Step 4: Write skills/eval/references/report-format.md**

Document the output format:

```markdown
# Eval Report Format

## Summary
- Win rate: X% assembled, Y% bare, Z% ties
- Strongest assembled advantage: [area]
- Strongest bare advantage: [area]

## Per-Prompt Results
| Prompt | Winner | Why |
|---|---|---|

## Recommendations
- [Actionable suggestions based on findings]
- E.g., "Personas help planning (+6 points) but hurt creative execution (-2). Consider adjusting Persona Calibration."

## Methodology
- [Number] prompts, [number] runs each, comparative judging
- Judge: [model], strict senior engineer persona
```

- [ ] **Step 5: Commit**

```bash
git add skills/eval/
git commit -m "feat: write gigo:eval — context effectiveness testing with comparative judging"
```

---

### Task 13: Update gigo:gigo References

**Files:**
- Modify: `skills/gigo/references/output-structure.md`
- Modify: `skills/gigo/references/persona-template.md`
- Modify: `skills/gigo/references/snap-template.md`
- Modify: `skills/gigo/references/extension-file-guide.md`

**Depends on:** Tasks 6, 10

- [ ] **Step 1: Read all four reference files**

Read each to see current content.

- [ ] **Step 2: Update output-structure.md**

Changes:
1. Replace all "Avengers Assemble" / "avengers-assemble" references with "GIGO" / "gigo"
2. Update generated workflow.md template to encode the pipeline (from spec Section 4.2):
   - Planning section pointing to `gigo:plan`
   - Execution and Review section pointing to `gigo:execute` (review is automatic per task)
   - Session End section pointing to `gigo:snap`
3. Replace "Hawkeye" with "The Overwatch"
4. Update skill references throughout (`/fury` → `gigo:maintain`, etc.)
5. Update the "Always create these" table to note that workflow.md now encodes the pipeline

- [ ] **Step 3: Update persona-template.md**

Changes:
1. Replace all "Avengers Assemble" references
2. Replace "Hawkeye" with "The Overwatch" throughout
3. Update The Overwatch persona template — remove "Clint Barton" reference, use the functional version from Task 2
4. Update all skill references
5. Update the threshold description to reference "The Overwatch" not "Hawkeye"

- [ ] **Step 4: Update snap-template.md**

Changes:
1. Replace all "Avengers Assemble" references
2. Replace all skill references (`/fury` → `gigo:maintain`, etc.)
3. Replace "Hawkeye" with "The Overwatch"
4. Add pipeline health check as audit step 10 in the template
5. Update the coverage check to say "offer to invoke `gigo:maintain`" not "suggest running `/fury`"

- [ ] **Step 5: Update extension-file-guide.md**

Changes:
1. Replace all "Avengers Assemble" references (likely minimal — this file is domain-generic)
2. Update any skill references

- [ ] **Step 6: Commit**

```bash
git add skills/gigo/references/
git commit -m "feat: update gigo:gigo references — pipeline workflow template, The Overwatch, GIGO naming"
```

---

### Task 14: Clean Up Old Skill Directories

**Files:**
- Delete: `skills/avengers-assemble/` (copied to skills/gigo/ in Task 1)
- Delete: `skills/cap/` (absorbed into skills/plan/ in Task 7)
- Delete: `skills/fury/` (merged into skills/maintain/ in Task 11)
- Delete: `skills/smash/` (merged into skills/maintain/ in Task 11)

**Depends on:** All previous tasks

- [ ] **Step 1: Verify new skills are complete**

Check that all new skill directories have SKILL.md files:

```bash
ls -la skills/gigo/SKILL.md skills/plan/SKILL.md skills/execute/SKILL.md skills/review/SKILL.md skills/eval/SKILL.md skills/snap/SKILL.md skills/maintain/SKILL.md
```

All 7 should exist.

- [ ] **Step 2: Remove old directories**

```bash
rm -rf skills/avengers-assemble/
rm -rf skills/cap/
rm -rf skills/fury/
rm -rf skills/smash/
```

- [ ] **Step 3: Verify no dangling references**

Search for any remaining references to old skill names in the codebase:

```bash
grep -r "avengers-assemble\|/fury\|/smash\|/cap\b\|Hawkeye" skills/ CLAUDE.md .claude/rules/ spec.md --include="*.md" -l
```

If any files still reference old names, fix them.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: remove old skill directories — avengers-assemble, cap, fury, smash"
```

---

### Task 15: Final Verification and Commit

**Files:** All

**Depends on:** Task 14

- [ ] **Step 1: Verify file structure matches spec**

```bash
find skills/ -type f | sort
```

Expected output should match the file structure in spec Section 7.

- [ ] **Step 2: Verify no remaining Marvel references**

```bash
grep -ri "nick fury\|avengers\|hulk\|hawkeye\|steve rogers\|captain america\|tony stark\|thanos" skills/ CLAUDE.md .claude/rules/ spec.md --include="*.md" -l
```

Exception: The Snap can reference "Tony's snap" as it's the naming etymology, not a character voice. All other Marvel references should be gone.

- [ ] **Step 3: Verify skill frontmatter**

For each of the 7 SKILL.md files, verify:
- `name:` field matches the skill name (gigo, plan, execute, review, snap, maintain, eval)
- `description:` field is specific enough to trigger correctly
- No references to old skill names in descriptions

- [ ] **Step 4: Count total lines**

```bash
wc -l skills/*/SKILL.md skills/*/references/*.md CLAUDE.md .claude/rules/*.md spec.md
```

Verify no skill SKILL.md exceeds 500 lines. Verify no rules file exceeds ~60 lines.

- [ ] **Step 5: Create summary commit**

```bash
git add -A
git commit -m "GIGO refactor complete — 7 skills, proven pipeline, Conductor persona

Renamed Avengers Assemble to GIGO. Skills: gigo (assembly), plan (brainstorm→spec→plan),
execute (bare worker dispatch), review (two-stage pipeline), snap (audit), maintain
(fury+smash merged), eval (context effectiveness testing).

Architecture: assembled planning → bare execution → two-stage review (Phase 7-8 proven).
New Conductor persona owns pipeline design. Hawkeye → The Overwatch."
```

---

## Self-Review

**Spec coverage check:**

| Spec Section | Task(s) |
|---|---|
| 1. The Rename | Tasks 1, 2, 3, 4, 14 |
| 2. Conductor persona | Task 2 (CLAUDE.md), Task 5 (reference) |
| 3.1 gigo:gigo | Task 6 |
| 3.2 gigo:plan | Task 7 |
| 3.3 gigo:execute | Task 8 |
| 3.4 gigo:review | Task 9 |
| 3.5 gigo:snap | Task 10 |
| 3.6 gigo:maintain | Task 11 |
| 3.7 gigo:eval | Task 12 |
| 4. Generated output | Tasks 6, 13 (output-structure, templates) |
| 5. Skill consolidation | Task 11 |
| 7. File structure | Tasks 1, 14 (create + cleanup) |
| 8. This project's changes | Tasks 2, 3, 4, 5 |
| 9. Migration path | Task 11 (upgrade-checklist) |

**Placeholder scan:** No TBDs, TODOs, or "implement later" found.

**Type/name consistency:** All tasks use consistent naming — `gigo:gigo`, `gigo:plan`, `gigo:execute`, `gigo:review`, `gigo:snap`, `gigo:maintain`, `gigo:eval`. "The Overwatch" used consistently (not "Hawkeye" except in removal context).
