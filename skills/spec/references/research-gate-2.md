# Gate 2: Post-Plan Adversarial Verification

## Purpose

Adversarially verify that every specific API, method, library, or pattern the plan names actually exists in the target runtime / version. Catches the "plan drafted new specifics the Gate 1 discovery never covered" failure mode.

Output: `docs/gigo/research/YYYY-MM-DD-<topic>-plan-verification.md`. Any unresolved ❌ row in this file blocks `gigo:execute` from dispatching tasks.

The gate is independent from the plan author AND from Gate 1. Dispatched as its own subagent with fresh context and adversarial framing — hostile verification, not cooperative. This mirrors the Overwatch persona's via-negativa stance applied as dispatch-time constraint.

---

## When Gate 2 Fires

- Gate 1 ran for the same spec (i.e., `tech-constraints.md` exists for the topic)
- The plan is finalized (post-Phase 9 self-review, post-Phase 9.5 Challenger)
- Phase 10 (operator review) has not yet approved the plan

**Re-runs triggered by any of:**
- Plan file's `<!-- approved: plan ... -->` marker is absent (revision-in-progress)
- Plan file mtime is newer than latest `plan-verification.md` run's `run-at` timestamp (edited after Gate 2 passed)
- Operator explicitly says "re-run Gate 2"

Full re-run every time. Each run APPENDS a new `## Run N` section (append-only per-run structure); does NOT overwrite prior runs.

Skip if Gate 1 skipped (no `tech-constraints.md` exists).

---

## Dispatch Procedure

1. **Read `tech-constraints.md`** — Gate 1's output as read-only input.
2. **Read the plan** at `docs/gigo/plans/YYYY-MM-DD-<feature>.md` (full text).
3. **Determine run number.** If `plan-verification.md` does not exist → run-number=1. If exists → count existing `## Run N` sections, increment.
4. **Assemble adversarial prompt** using the template below. Fill all `{PLACEHOLDERS}`.
5. **Dispatch single subagent** via `Agent` tool with `subagent_type: "general-purpose"`. Do NOT use `feature-dev`, `code-reviewer`, or other generic reviewers — they default to cooperative stance. Gate 2's adversarial framing is load-bearing.
6. **Wait for completion.** Subagent writes the new `## Run N` section to `plan-verification.md`.
7. **Compute effective status** from the latest run section using the Derived Status Calculation below.
8. **Present to operator at Phase 10** with findings and effective status.

---

## Dispatch Prompt Template (Verbatim)

Fill all `{PLACEHOLDERS}`, then pass as `prompt` argument to `Agent`.

````
You are an independent verification subagent with fresh context and NO stake in the plan succeeding. You are not helping the plan ship. You are finding what's broken before it ships.

ADVERSARIAL STANCE (read carefully — non-negotiable):

- Assume the plan is wrong. Your default is skepticism.
- Your job is to prove every named API, method, library, or pattern exists in the target runtime by citing live context7 documentation — verbatim quote or direct doc link.
- A ✅ row requires a verbatim doc citation. "Looks right" is ❌. "Probably exists" is ❌. "I recall seeing this" is ❌.
- Default to ❌ when evidence is incomplete. Better to force the plan author to prove a specific than to rubber-stamp.
- This is via negativa — you add value by removing bullshit, not by validating work. If the plan passes cleanly, that means the plan was actually verifiable, not that you were generous.

INPUT FILES (READ-ONLY):

- PLAN: {PLAN_PATH}
- TECH CONSTRAINTS (Gate 1 output, read-only): {TECH_CONSTRAINTS_PATH}
- TARGET SUMMARY: {TARGET_SUMMARY}

ARTIFACT PATH: {ARTIFACT_PATH}
RUN NUMBER: {RUN_NUMBER}
ISO_TIMESTAMP: {ISO_TIMESTAMP}

WORKFLOW (mandatory):

1. Read the plan in full. Extract EVERY specific that could be verified:
   - Method calls: `Object.method(args)`, `module.function(params)`
   - Library/framework names with versions: `express@5.0`, `numpy`, `Unity.EditorCoroutines`
   - Language features: `readonly struct`, `async generators`, `record types`
   - Integration patterns: "subprocess with CancellationToken", "main-thread dispatcher via SynchronizationContext"
   - Configuration knobs / flags referenced as existing
   - Package/plugin names and exact versions
   - Any API the plan assumes exists without proof

2. For EACH extracted item, query context7:
   - Call `mcp__plugin_context7_context7__resolve-library-id` with the target runtime name (from TARGET SUMMARY)
   - Call `mcp__plugin_context7_context7__query-docs` with the resolved ID and the specific method/pattern
   - Record verbatim doc citation if the item exists
   - Record "not found in context7 docs" if the item does NOT exist, cannot be resolved, or evidence is ambiguous

3. For items context7 cannot cover (proprietary SDKs, internal libraries):
   - Fall back to WebSearch with official-docs-priority query
   - Record source URL and relevant quote
   - Mark ❌ if you cannot find authoritative documentation

4. If context7 MCP tools are not available at all, mark every item that would have required context7 as ❌ by default. Operator can override with WebSearch citations.

5. DO NOT trust Gate 1's tech-constraints.md as evidence for specific methods. Gate 1 covered surface. Gate 2 covers specifics. If Gate 1 said "async/await is supported" and the plan names `Task.WaitAsync(CancellationToken)`, you must verify THAT SPECIFIC OVERLOAD exists, not assume the umbrella claim covers it.

6. Write your findings to {ARTIFACT_PATH}:
   - **Check file state against RUN_NUMBER first.** Read the file if it exists.
     - If the file does NOT exist AND RUN_NUMBER == 1: OK, proceed to CREATE path below.
     - If the file does NOT exist AND RUN_NUMBER > 1: contradiction — return STATUS=ERROR with message "RUN_NUMBER={RUN_NUMBER} but artifact file does not exist; lead's run-number logic is inconsistent." Do NOT write anything.
     - If the file EXISTS AND contains the expected `(RUN_NUMBER - 1)` prior `## Run N` sections: OK, proceed to APPEND path below.
     - If the file EXISTS AND contains zero `## Run ` sections (stale/corrupted from aborted run) AND RUN_NUMBER == 1: return STATUS=STALE with message "Artifact file exists but has no run sections; likely aborted prior run. Lead must clear or move the file before re-dispatch." Do NOT write anything.
     - If the file EXISTS AND RUN_NUMBER disagrees with actual section count: return STATUS=CONTRADICTION with the observed vs expected counts. Do NOT write anything.
   - **CREATE path** (RUN_NUMBER == 1, file does not exist): write frontmatter + `# Plan Verification: <topic>` + `**Target:** <target-summary>` + your `## Run 1 — {ISO_TIMESTAMP}` section containing `### Findings` table and empty `### Overrides (Run 1)` section.
   - **APPEND path** (RUN_NUMBER > 1, file exists with matching prior-run count): READ existing content, UPDATE frontmatter with new `run-number`, `run-at`, `status`, `total-findings`, `pass-findings`, `fail-findings` values, APPEND new `## Run {RUN_NUMBER} — {ISO_TIMESTAMP}` section at the end with your findings table and empty overrides sub-section. Do NOT touch prior `## Run N` sections.

SCHEMA (the latest run section follows this structure VERBATIM):

```markdown
## Run {RUN_NUMBER} — {ISO_TIMESTAMP}

### Findings

| # | Plan Reference | Named Specific | Target | Status | Evidence / Suggested Fix |
|---|---|---|---|---|---|
| 1 | Task 4, Step 2 | `Process.WaitForExitAsync(ct)` | Unity 6 (.NET Standard 2.1) | ❌ | Not present in context7 Unity 6 docs. .NET Standard 2.1 does not include this overload (first added in .NET 5). Suggested: wrap `p.WaitForExit()` in `Task.Run` and observe cancellation via `ct.Register(() => p.Kill())`. |
| 2 | Task 4, Step 4 | `string.Contains(char)` | Unity 6 | ✅ | context7: "System.String.Contains(Char) available from .NET Standard 2.1 onwards." |

### Overrides (Run {RUN_NUMBER})

<!-- Gate 2 overrides live here. Operator-added markers only. Empty on fresh runs. Format:
<!-- override: finding-N reason:<reason> approved-by:<username> timestamp:<ISO-8601> -->

Each marker resolves exactly one ❌ finding in THIS run. Finding numbers are per-run; prior-run overrides do not apply to this run.
-->
```

FRONTMATTER (update on every run):

```yaml
---
plan: {PLAN_PATH}
spec: docs/gigo/specs/{DATE}-{TOPIC}-design.md
tech-constraints: {TECH_CONSTRAINTS_PATH}
run-at: {ISO_TIMESTAMP}
run-number: {RUN_NUMBER}
subagent: general-purpose
status: pass | fail   # advisory; pass if zero ❌ in THIS run, fail otherwise. Consumers derive effective status from body.
total-findings: <integer>
pass-findings: <integer>
fail-findings: <integer>
---
```

OUTPUT:

After writing, return a structured summary:
- Total findings extracted: N
- ✅ pass: N
- ❌ fail: N
- Per-❌: one-line "what's broken and what's the suggested fix"
- Plan tasks containing ❌ items, by task reference

END OF PROMPT.
````

---

## Derived Status Calculation (consumers run this)

Consumers (execute, spec Phase 10) operate on the LATEST `## Run N` section. Locate by scanning for `## Run ` headers; pick highest N, break ties by timestamp.

Within that run's section:

1. **Count ❌ rows** in `### Findings` → `N_fail`
2. **Count valid override markers** in `### Overrides (Run N)` where ALL of:
   - Marker regex: `^<!-- override: finding-(\d+) reason:(.+?) approved-by:(.+?) timestamp:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) -->$`
   - `finding-N` matches an existing ❌ row number IN THIS RUN's table
   - `reason`, `approved-by`, `timestamp` capture groups all non-empty after trim
   - Single ❌ covered by at most one valid override (duplicates: first counts, rest logged as DUPLICATE-OVERRIDE)
   - Malformed markers NOT counted toward `N_override_matched` but surfaced to operator as MALFORMED-OVERRIDE
   - Call this `N_override_matched`
3. **Derive effective status:**
   - `N_fail == 0` → `pass`
   - `N_fail > 0 AND N_override_matched == N_fail AND every ❌ has a matching valid override` → `needs-override`
   - `N_fail > 0 AND not all ❌ covered` → `fail`
   - Body structure missing, latest run section malformed, or findings unparseable → `fail` (safer default)

Frontmatter `status:` is NEVER trusted alone. Body wins on disagreement.

---

## Test Matrix (every consumer implementation MUST handle these)

| Input | Expected effective status | Expected operator message |
|---|---|---|
| Body has no `## Run` sections | `fail` | "plan-verification artifact has no run sections — unparseable" |
| Latest run: 0 findings rows | `fail` | "latest run's findings table is empty or missing" |
| Latest run: 5 ✅, 0 ❌ | `pass` | — |
| Latest run: 3 ✅, 2 ❌, 0 overrides | `fail` | List 2 unresolved ❌ with suggested fixes |
| Latest run: 3 ✅, 2 ❌, 2 valid matching overrides | `needs-override` | "Executing with 2 acknowledged API gaps" |
| Latest run: 3 ✅, 2 ❌, 1 valid + 1 malformed | `fail` | List 1 unresolved ❌ + note "1 override malformed: [details]" |
| Latest run: 3 ✅, 2 ❌, 2 valid overrides for finding-1 + 0 for finding-2 | `fail` | "finding-2 has no override; finding-1 has duplicate overrides (one ignored)" |
| Latest run: 3 ✅, 1 ❌, 1 override pointing at finding-99 | `fail` | "1 unresolved ❌ (finding-1); 1 malformed override (finding-99 does not exist)" |
| Body has Run 1 pass, Run 2 fail | `fail` | Evaluate Run 2; Run 1 historical |
| Body has Run 1 fail, Run 2 pass | `pass` | Evaluate Run 2; Run 1 historical |

---

## Override Mechanism

Authority model: artifact BODY is source of truth. Frontmatter `status:` is advisory only — written once by subagent on first pass, NEVER mutated after. Consumers derive effective status from body every read.

Marker format:

```
<!-- override: finding-<N> reason:<non-empty, no unescaped newlines> approved-by:<git username> timestamp:<ISO-8601 UTC with Z suffix> -->
```

Example:

```
<!-- override: finding-3 reason:Task 7 adds Newtonsoft.Json fallback layer for projects without com.unity.nuget approved-by:eaven timestamp:2026-04-17T22:48:46Z -->
```

Requirements: marker must be in the `### Overrides (Run N)` sub-section of the SAME run whose finding it overrides. Prior-run overrides do NOT carry forward.

Re-runs: each new run creates a fresh `### Overrides (Run N)` sub-section (empty). Operator reviewing a new run's findings must re-add overrides against the new finding numbers — prior-run overrides are preserved on disk (append-only) but do not apply to new runs.

---

## Block-on-❌ Behavior (consumed by execute)

`gigo:execute` reads `plan-verification.md` at startup:

1. Resolve artifact via frontmatter `plan:` field (canonical absolute-path comparison).
2. Find latest `## Run N` section.
3. Compute effective status per Derived Status Calculation.
4. Act:

| Effective status | Execute behavior |
|---|---|
| `pass` (N_fail = 0) | Proceed normally. |
| `needs-override` (N_fail > 0, all covered) | Announce override count: `"Executing with [N_override_matched] acknowledged API gaps per <artifact-path>"`. Proceed. |
| `fail` (N_fail > 0, not all covered) | REFUSE. Report: `"Plan verification has [N_fail - N_override_matched] unresolved ❌ findings at <artifact-path>. Resolve by revising the plan (Gate 2 re-runs on revision) or adding override markers in ### Overrides (Run N) sub-section. Format: <!-- override: finding-N reason:... approved-by:... timestamp:... -->. Re-run /execute after."` List unresolved ❌ + MALFORMED-OVERRIDE + DUPLICATE-OVERRIDE details. |
| (no matching artifact) | Treat as skipped gates. Proceed. |
| (artifact exists, body unparseable) | REFUSE. Report parse issue with path. |

---

## Independence Rules (Non-Negotiable)

Gate 2 must NOT share context with:

- **The spec author** (Claude session writing the plan). Otherwise Gate 2 rationalizes plan choices.
- **The Gate 1 subagent.** Gate 2 reads `tech-constraints.md` as read-only input but runs fresh. Gate 1's reasoning chain must not influence Gate 2's extraction or verification.
- **The Challenger subagent** (6.5/9.5). Challenger checks engineering quality. Gate 2 checks API existence. Mixing stances loses the Reflexion quality gain.

Mechanism: separate `Agent` call with fresh context. The prompt template is the ONLY input; no implicit context leaks. "Different subagent invocation, same input artifact (the plan)" satisfies the independence rule — the context (not the artifact) is what must be fresh.

---

## Error Handling

| Condition | Response |
|---|---|
| context7 MCP not available at all | Mark every context7-requiring item as ❌ by default; operator can override with WebSearch citations. Pipeline degrades visibly. |
| Subagent extracts zero specifics from the plan | Suspicious — few plans have zero verifiable items. Spec re-dispatches once with explicit instruction to re-read plan. Still zero → flag ambiguous, proceed with empty verification, surface to operator. |
| Plan path doesn't exist when Gate 2 fires | Phase 9.75 bug — plan must exist by then. Fail loudly. |
| Re-run requested mid-operator-review | Allowed. Appends new `## Run N` section; overwrites frontmatter with latest values. |
| Override marker references non-existent finding | Logged as MALFORMED-OVERRIDE. Surfaces in block-on-❌ refusal. |
| Operator adds override in wrong run section | Malformed (not in current run) — ignored for current run's status calc. Surfaced to operator. |

---

## What This Gate Does NOT Do

- Does not validate engineering quality (Challenger's job)
- Does not re-do discovery (Gate 1's job)
- Does not mutate the plan (only writes to plan-verification.md)
- Does not skip based on "short plan" or "low risk" heuristics — if Gate 1 ran, Gate 2 runs
