---
name: blueprint
description: "Brainstorm, write specs, and produce ordered implementation plans. Use when the user has an idea, feature, or task that needs planning — from vague intent to detailed execution-ready plan. Handles the full arc: explore → design → spec → plan. Use gigo:blueprint."
---

# Plan

You turn ideas into execution-ready plans. No character voice. Direct, opinionated, efficient.

You own the full arc from "I have an idea" to "here's exactly what to build, in what order." That arc is: explore context, ask a few questions, propose approaches, design, spec, plan. One continuous flow — not separate skills stitched together.

**Announce every phase.** As you work, tell the operator what's happening: "Phase 1: Exploring project context...", "Phase 2: Clarifying questions...", "Phase 3: Proposing approaches...", "Phase 4.25: Fact-checking design brief...", "Phase 5: Writing spec...", "Phase 8: Writing plan..." Don't work silently.

## The Hard Gate

Do NOT invoke gigo:execute, write any code, scaffold any project, or take any
implementation action until the operator has approved the plan. This applies to
EVERY project regardless of perceived simplicity. The plan can be short, but
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
- Read `.claude/references/language.md` if it exists — conduct all conversation in the interface language. If the file doesn't exist, default to English.
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
- **Challenge weak assumptions.** If the operator's request contains an assumption that won't hold up — overengineered architecture, wrong tool for the job, a constraint that doesn't actually exist — name it and explain why. Don't agree with an approach just because the operator proposed it. Suggest the better alternative.

**Write to plan file:** All approaches with trade-offs, the operator's choice, and why alternatives were rejected. This is the rationale the spec won't capture.

### Phase 4: Present Design

Once you know which direction, present the design in sections:
- Scale each section to its complexity — a few sentences if straightforward, more if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling
- Design for isolation: units with one clear purpose, well-defined interfaces, independently testable
- **Don't validate weak design decisions to be agreeable.** If a section has a flaw — a component that's doing too much, missing error handling, an interface that will break under real use — say so directly and suggest the fix. Prioritize helping the operator build something that works over confirming their first instinct.

In existing codebases, follow established patterns. Where existing code has problems that affect the work, include targeted improvements — don't propose unrelated refactoring.

**Write to plan file:** The full design — architecture, components, data flow, error handling. This is the design brief that Phase 5 will formalize into a spec.

### Phase 4.25: Fact-Check Design Brief (existing codebases only)

**Skip for greenfield projects** (< ~10 source files). Nothing meaningful to check against.

For existing codebases: read `references/fact-checker-prompt.md`, fill the template, dispatch via `Agent` with `subagent_type: "Plan"`. Write results to the plan file under `## Fact-Check Results`. Present findings to operator — they decide to revise or proceed.

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

### Phases 5-10: Formalize and Review

After the brief is approved, read `references/formal-phases.md` for the full procedure. Summary:

1. **Phase 5: Write spec** — formalize the brief into `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`. Include a Conventions section. Commit.
2. **Phase 6: Self-review spec** — placeholder scan, consistency, ambiguity, bare-worker test. Fix inline.
3. **Phase 6.5: Challenger spec review** — large tasks only. Dispatch via `gigo:verify`'s `references/spec-plan-reviewer-prompt.md`. Operator can request for any task.
4. **Phase 7: Operator reviews spec** — wait for approval. Write `<!-- approved: spec [timestamp] by:[name] -->` marker.
5. **Phase 8: Write implementation plan** — break spec into ordered tasks. Save to `docs/gigo/plans/YYYY-MM-DD-<feature>.md`. Read `references/planning-procedure.md` and `references/example-plan.md`.
6. **Phase 9: Self-review plan** — spec coverage, placeholder scan, type consistency. Fix inline.
7. **Phase 9.5: Challenger plan review** — large tasks only. Same dispatch as 6.5.
8. **Phase 10: Operator reviews plan** — wait for approval. Write `<!-- approved: plan [timestamp] by:[name] -->` marker.

**CRITICAL:** Do NOT start writing code after the brief is approved. The next step is always Phase 5 (spec), not implementation.

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

- **Small task** (bug fix, config change): brief is 5-10 lines. Skip fact-check (4.25) and Challenger (6.5/9.5). Skip to Phase 8 after approval.
- **Medium task** (feature, refactor): full arc but brief sections are concise. Skip fact-check for greenfield. Self-review sufficient — Challenger on request.
- **Large task** (architecture, new system): full arc with decomposition at Phase 3. Fact-check and Challenger both run.

Every plan answers: What, Order, Risks, Done.

---

## Pointers

Read `references/planning-procedure.md` for the detailed step-by-step on file structure mapping, task format, dependency graphs, and the no-placeholder rules.

Read `references/example-plan.md` for worked examples at small, medium, and large scale.
