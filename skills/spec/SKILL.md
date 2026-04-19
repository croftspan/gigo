---
name: spec
description: "Formalize an approved design brief into a spec and implementation plan. Self-reviews both, runs Challenger for large tasks. Use after gigo:blueprint produces an approved brief, or when you have your own design brief to formalize. Use gigo:spec."
---

# Spec

You turn approved design briefs into formal specs and implementation plans. No character voice. Direct, precise, methodical.

Your input is an approved design brief. Your output is an approved spec and an approved implementation plan — ready for execution.

**Announce every phase.** "Phase 0: Researching platform targets...", "Phase 5: Writing spec...", "Phase 6: Self-reviewing spec...", "Phase 6.5: Running Challenger review...", "Phase 7: Spec ready for review...", "Phase 8: Writing implementation plan...", "Phase 9: Self-reviewing plan...", "Phase 9.75: Verifying plan against live docs...", "Phase 10: Plan ready for review..."

In slice mode, announce "Phase 5: Writing PRD foundation + {N} slice designs...", "Phase 8: Writing {N} slice plans...", "Phase 9.75: Verifying {N} slice plans...", "Phase 10: {N} slice plans ready for review...".

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

## Phase 0: Pre-Spec Research Gate (Gate 1)

Before writing the spec, verify the target runtime's API surface against live documentation via context7. Prevents the spec and plan from assuming APIs that don't exist — the class of failure that shipped weeks of Unity C# against .NET 5+ methods missing from Unity 6's .NET Standard 2.1 BCL.

**When Gate 1 fires:**

1. Read the approved design brief.
2. **If the brief has a `## Platform & Runtime Targets` section:** extract target list, run Gate 1 with those targets.
3. **If the brief declares `**Targets:** none`:** prompt the operator to confirm: *"The brief declares `Targets: none` — this will skip API verification gates. Confirm: is this a pure content/config project with NO shipped code that targets a runtime? [yes, skip gates / no, this ships code — let me name targets]."* Only skip on explicit confirmation.
4. **If neither:** prompt default-skeptical: *"This is a code project. What runtime / platform / SDK does it target? Answer `none` only if this is pure content/config with no code output. Otherwise name the target(s)."*

**Small-task handling:**

- `**Scale:** small` + non-code output → skip both gates fully
- `**Scale:** small` + code output → Gate 1 runs **host-shell detection only** (skip deep API discovery); Gate 2 still runs
- Ambiguous → ask operator explicitly

**When Gate 1 runs:** Read `references/research-gate-1.md` for the dispatch procedure, depth calibration, host-shell checklist, subagent prompt templates (variant-first and variant-subsequent), and artifact schema. Dispatch subagents SEQUENTIALLY (one target at a time) via `Agent` tool with `subagent_type: "general-purpose"`. Output: `docs/gigo/research/YYYY-MM-DD-<topic>-tech-constraints.md`.

**Before proceeding to Phase 5:** verify the tech-constraints artifact was written. If any target shows `Host-Shell Requirement: MISSING` or `context7 library ID: unresolved`, surface to operator — they decide to proceed, adjust scope, or add missing project shell before spec writing.

---

## Phase 5: Write Spec

### Mission-Control Mode Decision (R3.1)

After Phase 0 (Gate 1) completes and BEFORE drafting the spec:

1. Run mc detection per `skills/spec/references/mc-detection.md` (three-check, three-state).
2. Read preference file at `.claude/references/mission-control-preference.md` if it exists.
3. Apply the state × preference behavior table from `mc-detection.md`.
4. On STATE_ACTIVE OR operator-approved nudge → enter slice mode per `skills/spec/references/slice-mode.md`.
5. On all other combinations → proceed with v0.13 monolithic mode (no changes below).

For install/init prompts:
- **NOT_INITIALIZED** (mc-init is on PATH, vault just missing) → use the Mc-Init Invocation Procedure in `skills/spec/references/mc-detection.md` (handles vault-exists case with operator confirmation).
- **UNAVAILABLE** (mc-init not on PATH) → delegate to `gigo:maintain add-mission-control` via the Skill tool. That mode already handles source-path resolution, `install.sh` invocation, and the Mc-Init Procedure in sequence. Do NOT call the Mc-Init Procedure directly from spec in this state — `bash("mc-init ...")` would fail with "command not found" before installation.

`gigo:maintain` uses `resolve_mc_source_path()` per `mc-detection.md` — do NOT hardcode `~/projects/mission-control/` anywhere.

Read the approved design brief. If Gate 1 ran, also read `docs/gigo/research/<date>-<topic>-tech-constraints.md` — the spec's Conventions section and Tech Stack references must reflect verified constraints, not assumed ones. If Gate 1 flagged `Host-Shell Requirement: MISSING`, include the host-shell addition (or an explicit `**External-consumer-only:** true` declaration) as a spec requirement.

Formalize the brief into a spec — don't recreate the design from conversation memory.

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

Read the approved design brief and spec. If Gate 1 ran, also read `docs/gigo/research/<date>-<topic>-tech-constraints.md` — every API, method, or pattern named in task code blocks must come from the verified surface, not from training-data recall. Break the spec into executable tasks.

Save to `docs/gigo/plans/YYYY-MM-DD-<feature-name>.md`.

**If in slice mode (R3.4):** write ONE plan file per slice at `docs/gigo/plans/{date}-slice-{N}-{name}.md`. Each plan's header cites its slice spec in the `**Spec:**` field. See `skills/spec/references/slice-mode.md` for the full slice-mode procedure.

Plans are always in English. For tasks producing user-facing deliverables, include `**Output languages:** {codes from language.md}`.

Read `references/planning-procedure.md` for the full procedure.
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

## Phase 9.75: Post-Plan Verification Gate (Gate 2)

**Skip if Gate 1 was skipped.** If no `docs/gigo/research/<date>-<topic>-tech-constraints.md` exists, Gate 2 also skips.

Adversarially verify that every specific API, method, library, or pattern the plan names actually exists in the target runtime. This is a separate subagent with fresh context and via-negativa framing — *"find what's broken, default to skepticism, ✅ requires verbatim doc citation."* Cooperative verification would rubber-stamp the plan; hostile verification catches the specifics that Gate 1's discovery pass couldn't cover.

**Execution:** Read `references/research-gate-2.md` for the dispatch procedure, verbatim adversarial prompt template, `plan-verification.md` append-only schema, Derived Status Calculation with test matrix, override mechanism, and independence rules. Output: `docs/gigo/research/YYYY-MM-DD-<topic>-plan-verification.md`.

**Sequencing with Phase 9.5 Challenger:**

- If Challenger (9.5) recommends plan revisions and operator accepts, revisions apply BEFORE Gate 2 dispatches.
- If the plan is edited AFTER Gate 2 already ran (post-hoc acceptance, Phase 10 review edits), Gate 2 MUST re-run on the revised plan. Detect by: (a) plan mtime newer than latest artifact `run-at`, OR (b) plan lacks `<!-- approved: plan ... -->` marker.
- If Gate 2 triggers its own plan revision (for ❌ fixes), Challenger does NOT re-run automatically; operator may explicitly request re-Challenger if the revision is structurally significant.

**Exit handling (compute effective status per Derived Status Calculation in research-gate-2.md):**

- `pass` → proceed to Phase 10 normally.
- `fail` → present findings to operator at Phase 10 alongside the plan. Do NOT write the plan approval marker while any ❌ remains unaddressed. Operator must revise the plan (triggering Gate 2 re-run) or add override markers per `research-gate-2.md` Override Mechanism.
- `needs-override` → proceed to Phase 10 with override count summarized.

**Independence rule (non-negotiable):** Gate 2 runs as its own subagent with fresh context — NOT the spec author's session, NOT sharing context with Gate 1's subagent, NOT the Challenger's subagent. The via-negativa framing is load-bearing; shared context collapses the pattern back to single-pass verification (Shinn et al. Reflexion). Dispatch via `Agent` with `subagent_type: "general-purpose"` and the prompt template from `references/research-gate-2.md`.

**If in slice mode:** Gate 2 runs PER-SLICE-PLAN, not per-PRD. Each slice plan gets its own `docs/gigo/research/{date}-slice-{N}-{name}-plan-verification.md`. Dispatch one verification subagent per slice plan in parallel if independent; sequential if dependencies overlap. Gate 1 (Phase 0) still runs ONCE at PRD level — runtime targets don't vary per slice.

---

## Phase 10: Operator Reviews Plan

> "Plan saved to `<path>`. Review the tasks and dependency order — I'll adjust before we start."

If Gate 2 ran, also present the verification artifact:

> "Plan verification saved to `docs/gigo/research/<date>-<topic>-plan-verification.md`. Effective status: [pass / needs-override / fail]. [Summary of ❌ findings if any.]"

Wait for approval. On `fail` effective status, operator must either request plan revision (Gate 2 re-runs on revision) or add override markers per `references/research-gate-2.md`. Do NOT write the approval marker while any ❌ remains unaddressed.

**Monolithic mode:** single approval marker on the single plan file (existing behavior).

**Slice mode (R3.3):** offer batch approval with per-slice review on request. See `skills/spec/references/slice-mode.md` § "Approval Ceremony" for the exact prompt and per-slice iteration. Apply `<!-- approved: plan {timestamp} by:{username} -->` marker to every approved slice plan.

**After all slice plans are approved:** invoke mission-control's ticket-generation subcommand for each approved slice plan in order:

```
for plan_file in approved_slice_plans:
    Skill(skill="mission-control", args=f"ticket {plan_file}")
```

mission-control creates `vault/tickets/TCK-{phase}-{seq}.md` files per slice plan. Present the consolidated ticket-creation report to the operator.

**Write approval marker:**
```
<!-- approved: plan [timestamp] by:[username] -->
```

---

## Handoff

After the plan is approved, compact the conversation to shed spec-writing context. The plan and spec on disk are the durable records. If Gate 2 ran, `plan-verification.md` is also a durable record — execute reads it at startup and refuses to dispatch tasks while unresolved ❌ findings remain. Then ask:

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

Read `references/research-gate-1.md` when dispatching Phase 0 — the Pre-Spec Research Gate. Covers trigger detection, depth calibration, host-shell checklist, `tech-constraints.md` schema, variant-first and variant-subsequent subagent prompt templates.

Read `references/research-gate-2.md` when dispatching Phase 9.75 — the Post-Plan Verification Gate. Covers the verbatim adversarial prompt template, append-only `plan-verification.md` schema, Derived Status Calculation with test matrix, override mechanism, block-on-❌ behavior, and independence rules.
