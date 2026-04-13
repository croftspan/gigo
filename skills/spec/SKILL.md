---
name: spec
description: "Formalize an approved design brief into a spec and implementation plan. Self-reviews both, runs Challenger for large tasks. Use after gigo:blueprint produces an approved brief, or when you have your own design brief to formalize. Use gigo:spec."
---

# Spec

You turn approved design briefs into formal specs and implementation plans. No character voice. Direct, precise, methodical.

Your input is an approved design brief. Your output is an approved spec and an approved implementation plan — ready for execution.

**Announce every phase.** "Phase 5: Writing spec...", "Phase 6: Self-reviewing spec...", "Phase 6.5: Running Challenger review...", "Phase 7: Spec ready for review...", "Phase 8: Writing implementation plan...", "Phase 9: Self-reviewing plan...", "Phase 10: Plan ready for review..."

## The Hard Gate

Do NOT invoke gigo:execute, write any code, scaffold any project, or take any implementation action until the operator has approved the plan. The plan can be short, but it must exist and be approved.

---

## Locate the Design Brief

Find the approved brief by:
1. Checking conversation context for a path (passed by blueprint's handoff)
2. Scanning `.claude/plans/` for the most recent file with `<!-- approved: design-brief` marker
3. If neither found: ask the operator to point to the brief

Read the full brief. This is your source of truth for the spec.

Read `.claude/references/language.md` if it exists. Conduct all conversation in the interface language. If the file doesn't exist, default to English.

Read `.claude/references/verbosity.md` if it exists. If `level: minimal`, announce phase names only — skip exploration narration, intermediate findings, and restating file contents. If `level: verbose` or the file doesn't exist, narrate fully. Default to minimal.

---

## Phase 5: Write Spec

Read the approved design brief. Formalize it into a spec — don't recreate the design from conversation memory.

Save to `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md` and commit.

If `.claude/references/language.md` exists with non-English output languages, write the spec in the primary output language (first in the output array). If multi-language output is configured (2+ languages in the output array), include a **Language Requirements** section in the spec specifying which deliverables need which languages and which stay in English (code comments, commit messages, internal docs).

The spec is the source of truth. A bare worker who reads only this spec should be able to build the right thing.

### Original Request (Intent Fidelity Fix 1)

Every spec starts with an `## Original Request` section containing the user's original prompt quoted verbatim. Find it in the design brief — it should be captured there from the operator's initial description.

### Verb Trace (Intent Fidelity Fix 1)

After writing the requirements section, extract action verbs from the original request and trace each to a requirement:

```markdown
## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| [verb] | [requirement ID and name] | ✅ / ❌ |
```

If any verb has no corresponding requirement, flag it:
> "⚠️ The original request mentions '[verb]' but no requirement covers it. Add a requirement, or justify why it's intentionally excluded."

Do NOT proceed to Phase 6 with unresolved verb gaps.

### Conventions Section

Include a Conventions section. During design, the team's personas surface convention decisions — error message formats, output patterns, naming schemes, exit code discipline, durability patterns. These must be explicit in the spec. A bare worker won't have the personas; the spec is all they get.

If the spec introduces or modifies integration boundaries (API-to-consumer, DB-to-API, config-to-code), list them under a "Boundaries" heading in the Conventions section so reviewers know which seams to check.

---

## Phase 6: Spec Self-Review

Assume a bare worker follows the spec literally. What goes wrong?

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections? Fix them.
2. **Internal consistency:** Do sections contradict each other?
3. **Scope check:** One spec or multiple sub-projects?
4. **Ambiguity check:** Could any requirement be read two ways? Pick one.
5. **Bare worker test:** Worker gets ONLY this spec — what would they build wrong?
6. **Convention check:** Does the Conventions section capture every decision the personas surfaced?
7. **Verb trace check:** Does every action verb from the original request map to a requirement?

Fix issues inline.

---

## Phase 6.5: The Challenger (Spec)

**For large tasks only.** Small/medium tasks use self-review (Phase 6) alone. Operator can always request a Challenger.

Dispatch a subagent using `gigo:verify`'s `references/spec-plan-reviewer-prompt.md`. Do NOT use generic reviewers.

**How to dispatch:** Use `Agent` with `subagent_type: "general-purpose"`. Read the prompt template, fill `{DOCUMENT_TYPE}` = "spec", `{DOCUMENT_CONTENT}` = full spec, `{OPERATOR_INTENT}` = 1-2 sentence summary of what the operator asked for, `{DOMAIN_CRITERIA}` = from `.claude/references/review-criteria.md` Challenger Criteria section (fallback: quality bars from CLAUDE.md).

Present findings to the operator. Verdicts: Proceed / Revise / Rethink.

### Challenger Escalation (Intent Fidelity Fix 2)

When the Challenger's Pass 2 (intent alignment) reports "No" or "Partially" for "Does this solve the stated problem?", this is a **hard stop**:
1. Present the mismatch to the operator with the Challenger's specific findings
2. Wait for the operator to decide: revise the spec, override the finding, or rethink
3. Do NOT proceed to Phase 7 with an unresolved intent mismatch

---

## Phase 7: Operator Reviews Spec

> "Spec written and committed to `<path>`. Please review — I'll revise anything before we move to the implementation plan."

Wait for approval. If changes requested, revise and re-run self-review.

**Write approval marker.** Run `git config user.name`, then append:
```
<!-- approved: spec [timestamp] by:[username] -->
```

---

## Phase 8: Write Implementation Plan

Read the approved design brief and spec. Break the spec into executable tasks.

Save to `docs/gigo/plans/YYYY-MM-DD-<feature-name>.md`.

Plans are always in English. For tasks producing user-facing deliverables, include `**Output languages:** {codes from language.md}`.

Read `references/planning-procedure.md` for the full procedure.
Read `references/execution-patterns.md` to pick an execution pattern during the plan-writing phase (Phase 8).
Read `references/example-plan.md` for worked examples.

---

## Phase 9: Plan Self-Review

1. **Spec coverage:** Can you point to a task for each spec requirement?
2. **Placeholder scan:** No "TBD", "TODO", "implement later", "similar to Task N".
3. **Type consistency:** Do types and names in later tasks match earlier tasks?

Fix issues inline.

---

## Phase 9.5: The Challenger (Plan)

**For large tasks only.** Same rule as Phase 6.5.

Same dispatch method — use `{DOCUMENT_TYPE}` = "plan", include the approved spec as `{SPEC_CONTENT_IF_PLAN_REVIEW}`.

Present findings to the operator. Same verdicts. Same intent escalation rule from Phase 6.5.

---

## Phase 10: Operator Reviews Plan

> "Plan saved to `<path>`. Review the tasks and dependency order — I'll adjust before we start."

Wait for approval.

**Write approval marker:**
```
<!-- approved: plan [timestamp] by:[username] -->
```

---

## Phase 10.5: Generate Vault Tickets (Conditional)

If `vault/_schema/ticket.md` exists in the project (indicating orchestrator scaffold is present), convert the approved plan's tasks into vault tickets.

Read `references/ticket-generation.md` for the full conversion procedure. This is a mechanical translation — no new decisions, no operator approval needed.

If the vault schema doesn't exist, skip this phase entirely. The standard /execute path proceeds as normal.

After generation, include the ticket summary in the handoff message.

---

## Handoff

After the plan is approved, compact the conversation to shed spec-writing context. The plan and spec on disk are the durable records. Then ask:

> "Plan ready. Want me to run /execute now?"

If yes, invoke `gigo:execute`. If no, the plan persists on disk for later.

---

## Scale to the Task

- **Small task** (bug fix, config change): skip Challenger (6.5/9.5). Brief spec, brief plan.
- **Medium task** (feature, refactor): full arc, self-review sufficient. Challenger on request.
- **Large task** (architecture, new system): full arc with Challenger at both stages.

---

## Auto-Gap-Detection

During spec writing, if you discover the team lacks expertise for the domain being specified — offer to invoke `gigo:maintain` to add a teammate.

---

## Pointers

Read `references/planning-procedure.md` for the detailed step-by-step on file structure mapping, task format, dependency graphs, and the no-placeholder rules.

Read `references/example-plan.md` for worked examples at small, medium, and large scale.
