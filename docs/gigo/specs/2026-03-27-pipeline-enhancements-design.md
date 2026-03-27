# Pipeline Enhancements — Design Spec

Three targeted additions to existing skills (`gigo:execute` and `gigo:review`) that improve observability, resilience, and review efficiency. Absorbs process patterns from the deep trilogy (piercelamb/deep-project, deep-plan, deep-implement) — adapted to GIGO's proven architecture of assembled planning, bare execution, and two-stage review.

## Guiding Constraints

- **No new skills.** All changes modify `gigo:execute` and `gigo:review`.
- **No worker context changes.** Phase 7 proved bare workers produce the best code. These enhancements change what the *lead* and *reviewers* do, not what workers receive.
- **Plan document as source of truth.** All three enhancements use the plan document as persistent storage. This works across all three execution tiers (agent teams, subagents, inline) and survives session breaks.
- **Additive to existing flow.** Each enhancement slots into the existing SKILL.md structure at a specific point. No existing steps are removed or reordered.

---

## Enhancement 1: "What Was Built" Addendum

### What

After each task passes review, the lead appends a brief structured addendum to the plan document recording what actually happened vs what was planned. The plan becomes living documentation that stays in sync with reality.

### Why

- The next worker in the dependency chain reads what *actually got built*, not just what was planned. Critical when the implementation deviated — a renamed function, a different data structure, an added constraint.
- In Tier 2/3, subagents have no shared state. The addendum is the only way for Worker B to know that Worker A changed the interface.
- In Tier 1, agent teams can message each other, but the addendum is more durable — it survives session breaks and provides a written record for the operator.
- At plan completion, the lead already synthesizes results. Incremental addendums make this synthesis trivial — just read the addendums.

### Format

Appended directly under each completed task in the plan document:

```markdown
#### What Was Built
- **Deviations:** None | [brief description of what changed and why]
- **Review changes:** None | [what the review cycle changed]
- **Notes for downstream:** None | [interface changes, renamed exports, constraint additions — anything the next worker needs to know]
```

### Rules

1. **Always write an addendum.** Even if everything matched the plan exactly. "No deviations" is useful signal — it confirms the plan was accurate.
2. **Keep it brief.** 1-3 bullet points per field. This isn't a post-mortem — it's a breadcrumb trail for the next worker.
3. **Focus on what downstream workers need.** Internal implementation details that don't affect the interface don't belong here. A renamed export does. A refactored internal helper doesn't.
4. **Include review-driven changes.** If the review cycle changed the implementation (e.g., "review caught a race condition, added a lock"), record it. This distinguishes planned work from review-improved work.
5. **The "accept" category from review triage (Enhancement 3) feeds into addendum notes.** Observations worth recording but not worth fixing go here.

### Where It Inserts in gigo:execute

**In SKILL.md:** New section titled **"After Review Passes"** between the current "Status Handling" section and "When All Tasks Complete":

```
## After Review Passes

After a task passes both review stages, update the plan document:

1. Mark the task's steps as complete (checkboxes: `- [ ]` → `- [x]`)
2. Append the "What Was Built" addendum under the task
3. Include any "accept" observations from review triage
4. If the implementation deviated from the plan in ways that affect downstream tasks, check whether dependent task descriptions need updating

The addendum is brief — 1-3 bullets per field. Focus on what downstream workers need to know.

Format: [the format block above]
```

**In `references/teammate-prompts.md`:** Add to the Tier 2 subagent `## Context` section:

```
If prior tasks have "What Was Built" addendums in the plan, read them — they may record
interface changes or deviations that affect your task.
```

No changes to Tier 1 prompts — agent team teammates can already read the plan file and message the lead.

### Tier Behavior

| Tier | Who writes the addendum | When |
|---|---|---|
| 1 (Agent Teams) | Lead, after TaskCompleted hook passes | After hook exits 0 |
| 2 (Subagents) | Lead, after manual review passes | After review invocation returns pass |
| 3 (Inline) | Lead (same session), after review passes | After review invocation returns pass |

---

## Enhancement 2: Resume Capability

### What

Save progress per task (commit hash, task status, review result) as checkpoint comments in the plan document so execution can resume after context limits, crashes, or session breaks.

### Why

- Context limits are the most common execution interruption. A 10-task plan that hits the limit at task 6 currently requires the operator to manually communicate "tasks 1-5 are done, start at 6."
- Agent teams' shared task list provides some persistence, but it doesn't survive across sessions and isn't available in Tier 2/3.
- The plan document is the most durable artifact — it's a committed file that persists across sessions, tiers, and operators.
- Resume detection is cheap: scan for checkpoint comments before starting work.

### Checkpoint Format

After each task completes (review passes + addendum written), the lead adds a checkpoint comment to the last step of the task:

```markdown
- [x] **Step 3: Commit**
<!-- checkpoint: sha=abc1234 status=done reviewed=pass tier=1 -->
```

If a task was partially completed (review found issues, worker is mid-fix):

```markdown
- [x] **Step 2: Implement**
- [ ] **Step 3: Commit**
<!-- checkpoint: sha=def5678 status=in-review reviewed=issues-found tier=2 -->
```

### Checkpoint Fields

| Field | Values | Purpose |
|---|---|---|
| `sha` | Git commit hash (short) | Verify the work still exists on disk |
| `status` | `done`, `in-review`, `in-progress`, `blocked` | Where the task was when interrupted |
| `reviewed` | `pass`, `issues-found`, `pending` | Review state at interruption |
| `tier` | `1`, `2`, `3` | Which tier was running (for reconciliation) |

### Resume Detection

When `gigo:execute` starts (step 2: "Read the full plan"), it now includes:

1. **Scan for checkpoint comments.** If none found, proceed normally (fresh execution).
2. **If checkpoints found, report status:**

```
Resuming execution. Progress detected:
- Task 1: ✅ done (sha: abc1234)
- Task 2: ✅ done (sha: def5678)
- Task 3: ⚠️ in-review — issues found, needs re-review
- Task 4: ⬜ not started
- Task 5: ⬜ not started
```

3. **Verify checkpoints are valid.** For each `done` checkpoint, verify the commit SHA exists (`git cat-file -t <sha>`). If a SHA is missing (force-push, reset), warn the operator:

```
⚠️ Task 2 checkpoint references sha def5678 which no longer exists.
This task may need re-implementation. Proceed or investigate?
```

4. **Resume from the right point:**
   - `done` → skip
   - `in-review` with `issues-found` → re-run review on current state, then fix if needed
   - `in-progress` → dispatch worker to continue (provide addendum context from completed deps)
   - `blocked` → re-evaluate the blocker

### Tier-Specific Reconciliation

**Tier 1 (Agent Teams):** On resume, the shared task list may have stale state from the previous session. The lead reconciles: checkpoint state wins over task list state. Update the task list to match checkpoints before spawning teammates.

**Tier 2 (Subagents):** No shared state to reconcile. Checkpoints are the sole source of truth.

**Tier 3 (Inline):** Same as Tier 2.

### Where It Inserts in gigo:execute

**In SKILL.md:** Modify "Before Starting" section. Current step 2 is "Read the full plan." Expand it:

```
2. **Read the full plan.** Extract all tasks, their descriptions, dependencies, and parallelization markers.
   - Scan for checkpoint comments (`<!-- checkpoint: ... -->`).
   - If found: report progress, verify SHAs, resume from the appropriate point.
   - If not found: fresh execution — proceed normally.
```

**New reference file: `references/checkpoint-format.md`.** Contains:
- Full checkpoint comment syntax
- Resume detection procedure (the detailed steps above)
- SHA verification commands
- Tier reconciliation rules
- Edge cases: what to do when the plan file was modified between sessions, when checkpoints exist but the branch was rebased, when a `done` task's tests now fail

### What's NOT in This Enhancement

- **Automatic crash recovery.** If Claude crashes mid-task, the checkpoint records the last *completed* state, not the mid-task state. The worker may need to redo partial work. This is acceptable — partial work is unreliable anyway.
- **Task list migration.** We don't try to reconstruct the Tier 1 task list from checkpoints. The lead reconciles manually (update task list to match checkpoints). Full automation is a future enhancement.
- **Cross-plan checkpoints.** Each plan's checkpoints are self-contained. No global execution state.

---

## Enhancement 3: Review Triage

### What

After both review stages produce their findings, categorize each finding into one of three buckets before returning feedback. This focuses worker attention on real fixes, keeps the operator in the loop on decisions that matter, and captures observations without creating unnecessary fix cycles.

### Why

- Currently `gigo:review` returns everything equally. A missing import and an architectural concern get the same treatment. Workers waste cycles on trivial fixes while ignoring the real issues.
- Architectural questions and scope decisions should go to the operator, not the worker. The worker can't decide whether to change the API surface — that's a planning decision.
- Some review observations are worth recording but don't need fixes. "This works, but note that the caching layer will need revisiting when we add real-time updates" is useful context, not a bug.

### Categories

| Category | What goes here | Who handles it | Example |
|---|---|---|---|
| **auto-fix** | Minor issues with obvious fixes. Formatting, naming inconsistencies, missing imports, trivial test gaps. Engineering review findings with confidence 80-85. | Worker. Instructions: "Fix these, no discussion needed." | "Missing import for `ValidationError` at `src/handlers.py:12`" |
| **ask-operator** | Architectural questions, scope decisions, trade-offs, ambiguous requirements. Spec review findings where the right fix isn't clear. Engineering review findings where the fix changes the interface. | Operator decides, then worker implements. | "Spec says 'handle concurrent access' but doesn't specify optimistic vs pessimistic locking. Which approach?" |
| **accept** | Observations that don't need changes. Strengths. Future considerations. Anything informational. | Nobody fixes. Goes into the "What Was Built" addendum (Enhancement 1). | "The caching strategy works for current load but won't scale past ~10k concurrent users. Worth noting for future." |

### Triage Rules

1. **Spec review findings default to ask-operator** unless the fix is unambiguous (e.g., "forgot to implement the delete endpoint" → auto-fix if spec is clear about the endpoint design).
2. **Engineering review findings default to auto-fix** unless the fix changes the public interface or has architectural implications.
3. **Confidence score informs but doesn't determine category.** A confidence-80 finding about a race condition is ask-operator (architectural), not auto-fix. A confidence-95 finding about a missing import is auto-fix.
4. **When in doubt, ask-operator.** False escalation costs a question. False auto-fix can cost a wrong architectural decision.
5. **Critical issues (confidence 90+) are always auto-fix or ask-operator, never accept.** Critical issues must be resolved.

### Output Format

Review currently outputs findings in two stages. After both stages complete, the triage adds a categorized summary:

```markdown
## Triage

### Auto-Fix (worker handles)
1. Missing import `ValidationError` — `src/handlers.py:12`
2. Test name doesn't match function — `tests/test_handlers.py:45`

### Ask Operator
1. Spec says "handle concurrent access" — optimistic vs pessimistic locking? (spec review)
2. The error response format differs from the existing API convention — align with existing or use the new format from spec? (engineering review)

### Accept (noted, no action)
1. Caching strategy works for current load, won't scale past ~10k concurrent — future consideration
2. Clean separation of concerns in the handler layer (strength)
```

### Where It Inserts in gigo:review

**In SKILL.md:** New section titled **"Triage"** between Stage 2 and "Send-Back-and-Fix Loop":

```
## Triage

After both stages complete, categorize each finding:

| Category | Criteria | Action |
|---|---|---|
| **auto-fix** | Minor, obvious fix, no architectural implications | Return to worker: "Fix these, no discussion needed." |
| **ask-operator** | Architectural, scope, ambiguous, or interface-changing | Surface to operator before sending to worker |
| **accept** | Informational, future consideration, strength | Record in addendum, don't send as fix items |

Default rules:
- Spec review findings → ask-operator (unless fix is unambiguous)
- Engineering findings → auto-fix (unless interface-changing or architectural)
- Critical issues (90+) → never accept
- When in doubt → ask-operator

Output the categorized summary. In execution context (called from gigo:execute):
- Send auto-fix items to the worker immediately
- Surface ask-operator items to the operator and wait
- Pass accept items to the lead for the addendum

In standalone mode: present all three categories to the operator.
```

**Modification to `references/engineering-reviewer-prompt.md`:** Add a triage hint to the output format:

After each issue, the reviewer adds a suggested category:

```
- **File:line** — exact location
- **What's wrong** — concrete description
- **Why it matters** — impact
- **Confidence** — score 0-100
- **Suggested triage:** auto-fix | ask-operator | accept
```

The reviewer's suggestion is a hint, not a decision. The triage section in gigo:review makes the final call using the rules above.

**Modification to `references/spec-reviewer-prompt.md`:** Same addition — each finding gets a suggested triage category.

### Integration with gigo:execute

**Modification to "Send-Back-and-Fix Loop" behavior:** Currently gigo:execute receives all findings and sends them to the worker. With triage:

1. Receive categorized findings from gigo:review
2. **auto-fix:** Send to worker immediately with "Fix these, no discussion needed"
3. **ask-operator:** Surface to operator. Wait for decision. Then send decision to worker if action needed.
4. **accept:** Hold for the addendum (Enhancement 1). Don't send to worker.

This means the fix prompt in `references/teammate-prompts.md` needs a small update. The Tier 2 fix prompt becomes two variants:

**Auto-fix variant** (no change from current — issues are straightforward):
```
## Review Feedback
[AUTO-FIX items only — what's wrong, where, why it matters]

## Your Job
Fix the issues listed above. Don't change anything else.
Run tests. Commit. Report back.
```

**Operator-resolved variant** (when ask-operator items were decided):
```
## Operator Decision
[What the operator decided on the architectural/scope question]

## Review Feedback
[AUTO-FIX items, if any remain]

## Your Job
Implement the operator's decision. Fix any remaining auto-fix items.
Run tests. Commit. Report back.
```

### Tier Behavior

| Tier | How auto-fix reaches worker | How ask-operator reaches operator |
|---|---|---|
| 1 (Agent Teams) | Hook stderr contains only auto-fix items. Ask-operator items are held — hook exits with a special code or the lead intercepts. | Lead surfaces to operator via conversation. |
| 2 (Subagents) | Lead dispatches fix subagent with auto-fix items only. | Lead surfaces to operator, waits, then dispatches with resolution. |
| 3 (Inline) | Lead presents auto-fix items, implements fixes. | Lead presents ask-operator items, waits for operator. |

**Tier 1 hook implication:** The review hook currently has two exit codes (0 = pass, 2 = issues). With triage, we need to handle the case where review finds only ask-operator items (no auto-fix). Options:
- Hook exits 0 (pass) but writes ask-operator items to a sideband file the lead reads. Task completion is not blocked by ask-operator items — the work is done, the question is for the operator.
- Hook exits 2 only when auto-fix items exist. Ask-operator items don't block the worker.

**Recommended:** Hook exits 2 only for auto-fix items. Ask-operator items are written to stderr as informational (prefixed with `[ASK-OPERATOR]`) but don't block completion. The lead reads them from the task output and surfaces to the operator. Accept items are written with `[ACCEPT]` prefix for the lead to capture into the addendum.

This keeps the hook simple: the worker only gets blocked when there's something for *them* to fix.

---

## Cross-Enhancement Integration

The three enhancements form a reinforcing loop:

1. **Review triage** categorizes findings → auto-fix goes to worker, accept goes to addendum
2. **Addendum** captures what was built + accept observations → downstream workers read it
3. **Checkpoints** record completion state → resume picks up where the loop left off

The integration points:
- Review triage's "accept" category feeds directly into the addendum's "Notes for downstream" field
- Checkpoints record whether a task is in the triage-pending state (status: `in-review`, reviewed: `issues-found`)
- On resume, if a task has `ask-operator` items pending, the lead re-surfaces them — they weren't answered yet

---

## Files Changed (Summary)

### gigo:execute (`skills/execute/`)

| File | Change |
|---|---|
| `SKILL.md` | Add "After Review Passes" section (addendum). Expand "Before Starting" step 2 (resume detection). Add note about triage integration in status handling. |
| `references/teammate-prompts.md` | Add addendum reading hint to Tier 2 context. Update fix prompt to distinguish auto-fix from operator-resolved items. |
| `references/checkpoint-format.md` | **New file.** Full checkpoint syntax, resume procedure, SHA verification, tier reconciliation, edge cases. |
| `references/review-hook.md` | Update exit code semantics for triage categories. Document `[ASK-OPERATOR]` and `[ACCEPT]` stderr prefixes. |

### gigo:review (`skills/review/`)

| File | Change |
|---|---|
| `SKILL.md` | Add "Triage" section between Stage 2 and Send-Back-and-Fix Loop. Update Send-Back-and-Fix Loop to respect triage categories. |
| `references/engineering-reviewer-prompt.md` | Add "Suggested triage" field to issue output format. |
| `references/spec-reviewer-prompt.md` | Add "Suggested triage" field to issue output format. |

### Total new files: 1

`skills/execute/references/checkpoint-format.md`

### Total modified files: 6

All within existing skill directories. No new skills. No changes to worker prompts beyond the minor context and fix-prompt updates.
