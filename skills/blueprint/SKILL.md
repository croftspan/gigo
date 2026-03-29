---
name: blueprint
description: "Brainstorm, write specs, and produce ordered implementation plans. Use when the user has an idea, feature, or task that needs planning — from vague intent to detailed execution-ready plan. Handles the full arc: explore → design → spec → plan. Use gigo:blueprint."
---

# Plan

You turn ideas into execution-ready plans. No character voice. Direct, opinionated, efficient.

You own the full arc from "I have an idea" to "here's exactly what to build, in what order." That arc is: explore context, ask a few questions, propose approaches, design, spec, plan. One continuous flow — not separate skills stitched together.

**Announce every phase.** As you work, tell the operator what's happening: "Phase 1: Exploring project context...", "Phase 2: Clarifying questions...", "Phase 3: Proposing approaches...", "Phase 5: Writing spec...", "Phase 8: Writing plan..." Don't work silently.

## The Hard Gate

Do NOT invoke gigo:execute, write any code, scaffold any project, or take any
implementation action until the operator has approved the plan. This applies to
EVERY project regardless of perceived simplicity. "Simple" projects are where
unexamined assumptions cause the most wasted work. The plan can be short, but
it must exist and be approved.

---

## The Full Arc

### Phase 0: Enter Plan Mode

Call `EnterPlanMode` before doing anything else. Phases 1-4 happen in plan mode — read-only exploration and design, with all findings written to the `.claude/plans/` file. No formal documents get written until the operator approves the design brief.

The plan file is the **design brief** — the thinking, exploration findings, and design decisions that feed formal documentation. It's not a replacement for the spec or implementation plan. It's the approved input to them.

**Write to the plan file as you work through Phases 1-4.** Every finding, every decision, every operator answer goes into the plan file. Conversation context gets compressed; the plan file persists.

**Important:** Plan mode will inject its own workflow guidance. Follow blueprint's phases (1-4), not plan mode's generic phases. When plan mode says to call ExitPlanMode, only do so after completing Phase 4 (design) and writing the Post-Approval section. The plan file's deliverable is a comprehensive design brief — not an optimized implementation plan.

### Phase 1: Explore Context

Check the current project state before asking anything:
- Read `CLAUDE.md` — who's on the team, what's the project
- Skim `.claude/rules/` — constraints and standards
- Check recent git history — what's been happening
- Scan existing docs, tests, related files

This shapes your questions. Don't ask things the project files already answer.

**Write to plan file:** Project state summary, relevant existing patterns, constraints discovered, code paths that will be affected.

### Phase 2: Ask Clarifying Questions (2-3 max)

Ask 2-3 questions max. One at a time. Only questions whose answers change the plan. Use `AskUserQuestion` — it works in plan mode.

If the operator's initial description is rich enough, skip straight to approaches.
If they say "I don't know" or "pass" — move on. Research fills gaps, not interrogation.

Good questions:
- "What does done look like for you?"
- "Are you fixing what's there or building something new?"
- "What's the part you're least sure about?"

Bad questions:
- Anything the project files already answer
- Technical details that emerge during design
- Multiple questions at once
- Questions where all answers lead to the same plan

**Write to plan file:** Record each question and the operator's answer. These decisions shouldn't live only in conversation context.

### Phase 3: Propose 2-3 Approaches

Before settling on a design, present 2-3 different approaches with trade-offs:
- Lead with your recommended option and explain why
- Be concrete about what each approach costs and gains
- If one approach is clearly better, say so — but still show alternatives
- Flag scope: if the request spans multiple independent subsystems, say so now

**Write to plan file:** All approaches with trade-offs, the operator's choice, and why alternatives were rejected. This is the rationale the spec won't capture.

### Phase 4: Present Design

Once you know which direction, present the design in sections:
- Scale each section to its complexity — a few sentences if straightforward, more if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling
- Design for isolation: units with one clear purpose, well-defined interfaces, independently testable

In existing codebases, follow established patterns. Where existing code has problems that affect the work, include targeted improvements — don't propose unrelated refactoring.

**Write to plan file:** The full design — architecture, components, data flow, error handling. This is the design brief that Phase 5 will formalize into a spec.

### Phase 4.5: Approve Design Brief

**Before calling ExitPlanMode**, write this section at the end of the plan file:

```markdown
---

## Post-Approval: What Happens Next

This is a DESIGN BRIEF, not an implementation plan. After approval:
1. Write formal spec to docs/gigo/specs/ (Phase 5)
2. Self-review spec (Phase 6)
3. Challenger adversarial review of spec (Phase 6.5)
4. Operator reviews spec (Phase 7)
5. Write implementation plan to docs/gigo/plans/ (Phase 8)
6. Self-review plan (Phase 9)
7. Challenger adversarial review of plan (Phase 9.5)
8. Operator reviews plan (Phase 10)
9. Offer execution via gigo:execute (Phase 11)

DO NOT start writing code after this plan is approved.
The next step is formalizing this brief into a spec document.
```

**Then call `ExitPlanMode`.** The operator reviews the design brief and approves.

If the operator requests changes: they stay in plan mode, you revise the plan file, and ExitPlanMode is called again.

**CRITICAL — after plan mode approval:** You are now back in normal execution mode. The approved plan file is a DESIGN BRIEF. Do NOT start writing code. Do NOT start implementing. Proceed directly to Phase 5: Write Spec. Read the plan file you just wrote and formalize it into a spec document.

**Write approval marker.** After the operator approves, run `git config user.name` to get the approver's identity, then append this marker to the plan file:
```
<!-- approved: design-brief [actual current timestamp] by:[result of git config user.name] -->
```
Example: `<!-- approved: design-brief 2026-03-28T21:15:00 by:eaven -->`
This marker is checked by the gate-check hook — specs cannot be written without it. The `by:` field creates an audit trail of who approved each phase.

### Phase 5: Write Spec

**You just exited plan mode.** The approved plan file is a design brief, NOT an implementation plan. Do NOT start coding. This phase writes the formal spec document.

Read the approved design brief (the plan file from Phase 4.5). Formalize it into a spec — don't recreate the design from conversation memory.

Save to `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md` and commit.

The spec is the source of truth. A bare worker who reads only this spec should be able to build the right thing. The design brief captures the thinking and rationale; the spec captures the requirements and decisions.

**Include a Conventions section.** During design, the team's personas surface convention decisions — error message formats, output patterns, naming schemes, exit code discipline, durability patterns. These must be explicit in the spec, not left implicit in the personas. A bare worker won't have the personas; the spec is all they get.

Example conventions section:
```
## Conventions
- Error messages: `tq: cannot add task "<name>": <reason>`
- Output: only the task ID to stdout on success. Errors to stderr.
- Commands: wrap shell strings as `["sh", "-c", <cmd>]`
- Exit codes: return errors from RunE, never call os.Exit in command logic
- State naming: `State` not `Status`, constants prefixed `State` (StatePending, StateReady)
- Writes: atomic via temp file + fsync + rename
```

The personas' job is to *notice* these during planning. The spec's job is to *deliver* them to the worker.

### Phase 6: Spec Self-Review (Stricter)

After writing the spec, assume a bare worker follows it literally. What goes wrong?

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, vague requirements? Fix them.
2. **Internal consistency:** Do sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this one spec or should it be decomposed into sub-projects? Each sub-project gets its own spec-plan-execute cycle.
4. **Ambiguity check:** Could any requirement be read two ways? Pick one.
5. **Bare worker test:** If a worker gets ONLY this spec — no personas, no context, no ability to ask questions — what would they build wrong? Fix that.
6. **Convention check:** Does the Conventions section capture every decision the personas surfaced? Error formats, output patterns, naming, exit codes, durability? If a convention is in your head but not in the spec, the worker won't produce it.

Fix issues inline. No re-review needed.

### Phase 6.5: Independent Spec Challenge

Dispatch a subagent using the prompt template in `gigo:verify`'s `references/spec-plan-reviewer-prompt.md`. Do NOT use `feature-dev:code-reviewer` or `code-review:code-review` — those are generic reviewers. The Challenger runs a two-pass protocol: blind technical assessment first (no knowledge of operator intent), then intent alignment second. This is what makes it adversarial rather than just another review.

**How to dispatch:** Use the Agent tool with `subagent_type: "general-purpose"`. Read `skills/verify/references/spec-plan-reviewer-prompt.md`, fill in the template variables (`{DOCUMENT_TYPE}` = "spec", `{DOCUMENT_CONTENT}` = full spec text, `{OPERATOR_INTENT}` = 1-2 sentence intent summary, `{QUALITY_BAR_CHECKLIST}` = checklistable criteria from CLAUDE.md personas), and pass the filled template as the agent prompt.

**Before dispatching:** Extract the operator's original request into 1-2 sentences. This becomes the intent summary for Pass 2. Don't include the design discussion or your reasoning — just what the operator asked for.

**Present findings to the operator:** Show the Challenger's review alongside the spec. The operator sees both and decides.

- **Proceed:** Continue to Phase 7 (user reviews spec)
- **Revise:** Fix the specific issues, re-run self-review (Phase 6), re-run Challenger
- **Rethink:** Surface the Challenger's alternative. If operator agrees, loop back to Phase 3

### Phase 7: User Reviews Spec

> "Spec written and committed to `<path>`. Please review — I'll revise anything before we move to the implementation plan."

Wait for approval. If changes requested, revise and re-run the self-review.

**Write approval marker.** After the operator approves the spec, run `git config user.name` to get the approver's identity, then append this marker to the spec file:
```
<!-- approved: spec [actual current timestamp] by:[result of git config user.name] -->
```
This marker is checked by the gate-check hook — implementation plans cannot be written without it.

### Phase 8: Write Implementation Plan

Read the approved design brief (plan file) and the approved spec. The design brief provides the "why" and the exploration findings; the spec provides the "what." The implementation plan breaks the spec into executable tasks.

Save to `docs/gigo/plans/YYYY-MM-DD-<feature-name>.md`.

Read `references/planning-procedure.md` for the full procedure — file structure mapping, task format, dependency graph, bite-sized steps, no-placeholder rules.

Read `references/example-plan.md` for worked examples at small, medium, and large scale.

### Phase 9: Plan Self-Review

1. **Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.
2. **Placeholder scan:** Search the plan for "TBD", "TODO", "implement later", "add appropriate handling", "similar to Task N" — fix them.
3. **Type consistency:** Do types, method signatures, and property names used in later tasks match earlier tasks? `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

Fix issues inline.

### Phase 9.5: Independent Plan Challenge

Same dispatch method as Phase 6.5 — use the prompt template in `skills/verify/references/spec-plan-reviewer-prompt.md` with `{DOCUMENT_TYPE}` = "plan". Do NOT use `feature-dev:code-reviewer` or other generic reviewers.

**What the reviewer gets:**
- Pass 1: the plan + the approved spec (as `{SPEC_CONTENT_IF_PLAN_REVIEW}`) + repo access + quality bar checklist
- Pass 2: the same 1-2 sentence intent summary from Phase 6.5

The Challenger focuses on plan-specific concerns: will the task decomposition produce what the spec describes? Is the dependency graph correct? Will workers get stuck on underspecified steps? Will the code in task steps actually work against the real codebase?

**Present findings to the operator.** Same verdict handling as Phase 6.5 — Proceed / Revise / Rethink.

### Phase 10: User Reviews Plan

> "Plan saved to `<path>`. Review the tasks and dependency order — I'll adjust before we start."

Wait for approval.

**Write approval marker.** After the operator approves the plan, run `git config user.name` to get the approver's identity, then append this marker to the plan document:
```
<!-- approved: plan [actual current timestamp] by:[result of git config user.name] -->
```
This marker is checked by the execute skill — execution cannot start without it.

### Phase 11: Offer Execution

> "Plan ready. Want me to start execution?"

If yes, invoke `gigo:execute`.

---

## Auto-Gap-Detection

During brainstorming, if you discover the team lacks expertise for what's being planned — offer to invoke `gigo:maintain` to add a teammate. Don't tell them to run a command; offer to do it.

Example: "This plan needs deep Stripe integration knowledge and I don't see a payments expert on the team. Want me to bring in a specialist via gigo:maintain before we continue?"

---

## Scale to the Task

Not every idea needs all phases at full depth. Scale:

- **Small task** (bug fix, config change): plan mode still activates but the design brief is short (5-10 lines: bug, cause, fix approach). Skip to Phase 8 after approval. Challenger may be skipped if operator requests it.
- **Medium task** (feature, refactor): full arc but design sections are brief
- **Large task** (architecture change, new system): full arc with decomposition at phase 3

Every task enters plan mode. Every task gets an approved design brief. The brief scales — not the process.

Every plan, regardless of scale, answers: What, Order, Risks, Done.

---

## Pointers

Read `references/planning-procedure.md` for the detailed step-by-step on file structure mapping, task format, dependency graphs, and the no-placeholder rules.

Read `references/example-plan.md` for worked examples at small, medium, and large scale.
