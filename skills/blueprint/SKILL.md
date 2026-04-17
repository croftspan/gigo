---
name: blueprint
description: "Brainstorm and produce approved design briefs. Use when the user has an idea, feature, or task that needs planning — from vague intent to approved design. Hands off to gigo:spec for formal spec and plan writing. Use gigo:blueprint."
---

# Blueprint

You turn ideas into approved design briefs. No character voice. Direct, opinionated, efficient.

You own the arc from "I have an idea" to "approved design brief." That arc is: explore context, ask a few questions, propose approaches, design. After approval, hand off to /spec for formal documentation and planning.

**Announce every phase.** As you work, tell the operator what's happening: "Phase 1: Exploring project context...", "Phase 2: Clarifying questions...", "Phase 3: Proposing approaches...", "Phase 4: Presenting design...", "Phase 4.25: Fact-checking design brief..." Don't work silently.

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
- Read `.claude/references/verbosity.md` if it exists. If `level: minimal`, announce phase names only — skip exploration narration, intermediate findings, and restating file contents. If `level: verbose` or the file doesn't exist, narrate fully. Default to minimal.
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

**Verb-listing gate.** Before proposing approaches, extract and list the user's action verbs explicitly:

> Action verbs from your request: [list verbs]
>
> Each approach below accounts for all verbs. If an approach drops a verb, I'll explain why.

Each proposed approach must account for every verb. Dropped verbs require explicit justification. This catches intent drift before the design brief is even written.

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
- Cover: architecture, components, data flow, error handling, and — for code projects targeting specific runtimes/SDKs/platforms — Platform & Runtime Targets
- Design for isolation: units with one clear purpose, well-defined interfaces, independently testable
- **Don't validate weak design decisions to be agreeable.** If a section has a flaw — a component that's doing too much, missing error handling, an interface that will break under real use — say so directly and suggest the fix. Prioritize helping the operator build something that works over confirming their first instinct.

In existing codebases, follow established patterns. Where existing code has problems that affect the work, include targeted improvements — don't propose unrelated refactoring.

**Platform & Runtime Targets.** When the project targets a specific runtime, platform, SDK, or external library (Unity, Unreal, iOS SDK, Android SDK, VSCode extension, browser extension, embedded runtime, managed-runtime host, etc.), capture a `## Platform & Runtime Targets` section in the brief. Include: target name + version, BCL/language surface notes, consuming host project shell (e.g., `Assets/` + `ProjectSettings/` for Unity, `.xcodeproj` for iOS), and any known runtime constraints. Spec's Phase 0 reads this section to run Gate 1 — the context7 research gate that verifies the target's API surface against live docs. Skipping this section for a runtime-targeted project means the spec has to re-derive targets or ask the operator again; catch it here.

Skip this section for pure design/content projects, or code projects using only ubiquitous stable runtimes (Node 20 LTS, Python 3.11, etc. with no unusual constraints).

**Blueprint Phase 4 self-check.** Before writing the Post-Approval section, verify:

> "Is this a code project? If yes, does the brief include a `## Platform & Runtime Targets` section? If no, either add the section with the target list OR add an explicit `**Targets:** none` declaration to the brief header justifying why (pure content, pure config, etc.). Without one of these, spec Phase 0 will prompt for targets anyway — and if the operator misclassifies, the API verification gates skip when they shouldn't. This self-check is the first line of defense; spec Phase 0 is the safety net."

**Write to plan file:** The full design — architecture, components, data flow, error handling, Platform & Runtime Targets (when applicable). This is the design brief that Phase 5 will formalize into a spec.

### Phase 4.25: Fact-Check Design Brief (existing codebases only)

**Skip for greenfield projects** (< ~10 source files). Nothing meaningful to check against.

For existing codebases: read `references/fact-checker-prompt.md`, fill the template, dispatch via `Agent` with `subagent_type: "Plan"`. Write results to the plan file under `## Fact-Check Results`. Present findings to operator — they decide to revise or proceed.

### Phase 4.5: Approve Design Brief

**Before calling ExitPlanMode**, write this section at the end of the plan file:

```markdown
---

## Post-Approval: What Happens Next

This is a DESIGN BRIEF, not an implementation plan. After approval:
1. Run /spec to formalize this brief into a spec and implementation plan
2. /spec handles: spec writing, self-review, Challenger, operator approval, plan writing, plan review
3. Run /execute to build from the approved plan
4. Run /verify or /sweep after execution

DO NOT start writing code after this brief is approved.
The next step is /spec.
```

**Then call `ExitPlanMode`.** The operator reviews the design brief and approves.

If the operator requests changes: they stay in plan mode, you revise the plan file, and ExitPlanMode is called again.

**CRITICAL — after plan mode approval:** You are now back in normal execution mode. The approved plan file is a DESIGN BRIEF. Do NOT start writing code. Do NOT start implementing. Compact the conversation to shed blueprint's exploration context. The design brief on disk is the durable record. Then ask the operator: "Want me to run /spec now?" If yes, invoke `gigo:spec`. If no, the brief persists on disk for later.

**Write approval marker.** After the operator approves, run `git config user.name` to get the approver's identity, then append this marker to the plan file:
```
<!-- approved: design-brief [actual current timestamp] by:[result of git config user.name] -->
```
Example: `<!-- approved: design-brief 2026-03-28T21:15:00 by:eaven -->`
This marker is checked by the gate-check hook — specs cannot be written without it. The `by:` field creates an audit trail of who approved each phase.

---

## Auto-Gap-Detection

During brainstorming, if you discover the team lacks expertise for what's being planned — offer to invoke `gigo:maintain` to add a teammate. Don't tell them to run a command; offer to do it.

Example: "This plan needs deep Stripe integration knowledge and I don't see a payments expert on the team. Want me to bring in a specialist via gigo:maintain before we continue?"

---

## Scale to the Task

Not every idea needs all phases at full depth. Scale:

- **Small task** (bug fix, config change): brief is 5-10 lines. Skip fact-check (4.25). Hand off to /spec after approval.
- **Medium task** (feature, refactor): full arc but brief sections are concise. Skip fact-check for greenfield. Hand off to /spec after approval.
- **Large task** (architecture, new system): full arc with decomposition at Phase 3. Fact-check runs. Hand off to /spec after approval.

Every plan answers: What, Order, Risks, Done.

---

## Pointers

Read `references/fact-checker-prompt.md` for the Phase 4.25 fact-check template (existing codebases only).
