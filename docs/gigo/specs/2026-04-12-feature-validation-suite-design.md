# Feature Validation Suite — Design Spec

**Design brief:** `.claude/plans/unified-seeking-thacker.md`

---

## Original Request

> ok ive ran all 4 sessions now. i want to create a blueprint kickoff prompt and md files to create a way for us to test everything we just built and make sure we're actually adding value to our system

---

## Problem

GIGO shipped 4 features from a competitive analysis of revfactory/harness: boundary-mismatch detection (review criteria + taxonomy), phase selection matrix (change-impact tracking for maintain), execution pattern catalog (planning reference for spec), and Agent Teams cleanup (Tier 3 removal). The existing eval framework tests core value (assembled vs bare, 94% baseline). It cannot answer whether these specific features work or whether adding them regressed anything.

---

## Requirements

### R1: Seeded-Defect Fixture

Create `evals/fixtures/integration-api/` — a simplified TypeScript task management project with 6 planted boundary bugs, one per BM category.

**Fidelity:** Realistic types, API routes, hooks, and components. Not runnable (no package.json, no build config). Matches existing fixture fidelity — the Rails fixture has real model/controller/migration files but isn't a runnable Rails app.

**File structure:**

```
integration-api/
├── CLAUDE.md
├── .claude/
│   ├── rules/
│   │   ├── standards.md
│   │   ├── workflow.md
│   │   └── snap.md
│   └── references/
│       ├── review-criteria.md
│       └── integration-patterns.md
├── src/
│   ├── types.ts
│   ├── api/
│   │   ├── tasks.ts
│   │   └── projects.ts
│   ├── hooks/
│   │   ├── useTasks.ts
│   │   └── useProjects.ts
│   ├── components/
│   │   └── Sidebar.tsx
│   ├── app/
│   │   └── dashboard/
│   │       └── tasks/
│   │           └── new/
│   │               └── page.tsx
│   └── models/
│       ├── task-status.ts
│       └── task-service.ts
└── DEFECT-MANIFEST.md
```

**CLAUDE.md:** 3 personas following existing fixture pattern:
- **Schema** — The Integration Architect (type-safe pragmatism, interface clarity)
- **Stack** — The Frontend Engineer (composition-first, route-centric, data-fetching)
- **Hawkeye** — The Overwatch (same as existing fixtures)

**review-criteria.md:** Spec compliance criteria (API shape matches consumer type, navigation resolves to actual routes, status model covers all values) and craft review criteria (naming consistency, async lifecycle handling, type generic validation). These are what gigo:gigo Step 6.5 would generate for a TypeScript full-stack project with BM patterns in scope — realistic criteria, not cheat-sheet entries pointing at bugs.

**The 6 seeded bugs:**

| # | BM Type | Bug | Files |
|---|---|---|---|
| 1 | BM-1: Shape Mismatch | API returns `{ data: Task[], total: number }` (envelope). Hook types response as `Task[]` — no envelope unwrapping. | `api/tasks.ts`, `hooks/useTasks.ts` |
| 2 | BM-2: Convention Drift | `types.ts` defines `created_at` (snake_case). API serializes as `createdAt` (camelCase). Hook accesses `task.created_at`. | `types.ts`, `api/tasks.ts`, `hooks/useTasks.ts` |
| 3 | BM-3: Reference Mismatch | Sidebar links to `/tasks/new`. Actual page is at `app/dashboard/tasks/new/page.tsx` → URL `/dashboard/tasks/new`. | `components/Sidebar.tsx`, `app/.../page.tsx` |
| 4 | BM-4: Contract Gap | Status model defines 5 statuses (`draft`, `active`, `paused`, `completed`, `archived`). Service implements 3 transitions (`draft→active`, `active→completed`, `active→paused`). Missing: `paused→active`, `completed→archived`. | `models/task-status.ts`, `models/task-service.ts` |
| 5 | BM-5: Temporal Shape Mismatch | POST `/projects` returns 202 with `{ id, status: 'creating' }`. Hook immediately accesses `response.memberCount` — a field that only exists when `status: 'ready'`. | `api/projects.ts`, `hooks/useProjects.ts` |
| 6 | BM-6: False Positive Integration | DELETE `/tasks/:id` returns `{ deleted: true }`. Hook accesses `response.task` for undo data. Endpoint exists, returns 200, but shape doesn't match consumer expectation. | `api/tasks.ts`, `hooks/useTasks.ts` |

**DEFECT-MANIFEST.md:** Test key listing all 6 bugs with exact locations and expected detection. Excluded from Claude's context during testing (not copied to temp dir).

### R2: Boundary-Mismatch Test Script

Create `evals/validation/run-boundary-test.sh`.

**Inputs:** The integration-api fixture directory.

**Flow:**
1. Copy `fixtures/integration-api/` to a temp directory, excluding `DEFECT-MANIFEST.md`
2. Run `claude -p "$AUDIT_PROMPT" --output-format json --permission-mode bypassPermissions` in the temp dir
3. Run `claude -p "$JUDGE_PROMPT"` with the audit output + defect manifest to score per-bug detection
4. Parse judge output: 6 YES/NO scores
5. Output: `X/6 detected`, per-bug breakdown, PASS/FAIL

**Audit prompt** (embedded in script):
```
Review this codebase for integration issues. Examine how data flows between
layers — API routes, frontend hooks, type definitions, navigation, state
management. For each issue, identify: the files involved, the specific
mismatch, and why it would fail at runtime despite passing TypeScript
compilation. Focus on cross-boundary coherence, not single-file code quality.
```

**Pass threshold:** ≥4/6 bugs detected.

### R3: Boundary-Mismatch Judge Prompt

Create `evals/validation/boundary-judge.md`.

**Template variables:** `{AUDIT_OUTPUT}`, `{DEFECT_MANIFEST}`

**Behavior:** For each of 6 defects from the manifest, score YES or NO:
- YES: the audit identified this specific bug (matching on concept, not exact wording)
- NO: the audit missed this bug or described something different

**Output format:** JSON array of 6 entries:
```json
[{ "defect": "BM-1", "detected": true, "evidence": "..." }, ...]
```

### R4: Boundary-Mismatch Rubric

Create `evals/validation/boundary-mismatch-rubric.md`.

The defect manifest reformatted for the judge — describes each bug, its files, and the specific mismatch. The judge compares audit output against this rubric.

### R5: Execution Pattern Test Script

Create `evals/validation/run-pattern-test.sh`.

**Inputs:** The rails-api fixture directory, the execution-patterns.md reference, 3 planning prompts from `evals/prompts/execution-patterns.txt`.

**Flow:**
1. Copy `fixtures/rails-api/` to a temp directory
2. Copy `skills/spec/references/execution-patterns.md` into the temp dir's `.claude/references/`
3. Add a "When to Go Deeper" pointer in the temp copy's `standards.md`: `When planning how to execute work, read .claude/references/execution-patterns.md — pick the pattern matching the task's dependency shape before writing tasks.`
4. For each prompt in `prompts/execution-patterns.txt`, run `claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions` in the temp dir
5. Run the pattern judge on each output
6. Output: `X/3 correct patterns`, per-prompt breakdown, PASS/FAIL

**Pass threshold:** 3/3 correct patterns.

**Limitation (acknowledged):** This tests whether Claude reads and applies the execution-patterns.md reference when present in `.claude/references/` — it does not test whether `gigo:spec` routes to the file during its planning procedure. Invoking skills programmatically in a test harness requires interactive Claude sessions, which the eval framework doesn't support. Content activation is an acceptable proxy: if the content activates when present, the skill pipeline's "When to Go Deeper" pointer will route to it during real use. If the content doesn't activate even when directly present, the catalog isn't earning its tokens regardless of routing.

### R6: Execution Pattern Prompts

Create `evals/prompts/execution-patterns.txt`.

**Format:** `P|<prompt>` — one prompt per line, matching existing `evals/prompts/*.txt` format.

**3 prompts:**

1. **Pipeline (sequential):** Planning prompt describing work where each step depends on the previous (migrate schema → update API → update spec).
2. **Fan-out/Fan-in (parallel):** Planning prompt describing independent parallel audits (security, stubs, code quality).
3. **Producer-Reviewer (generate-then-validate):** Planning prompt describing implementation followed by independent review against a design spec.

Each prompt is an obvious case for its pattern — testing whether the catalog activates at all, not edge cases.

### R7: Execution Pattern Judge Prompt

Create `evals/validation/pattern-judge.md`.

**Template variables:** `{PLAN_OUTPUT}`, `{EXPECTED_PATTERN}`

**Behavior:** Scores YES if the plan:
- Names the correct pattern (e.g., "Pipeline", "Fan-out/Fan-in", "Producer-Reviewer"), OR
- Describes its structure accurately (e.g., "these tasks must run sequentially" for Pipeline)

Scores NO if the plan uses the wrong execution shape or ignores execution structure entirely.

**Output format:** JSON: `{ "pattern": "Pipeline", "correct": true, "evidence": "..." }`

### R8: Phase Selection Matrix Test Script

Create `evals/validation/run-matrix-test.sh`.

**Inputs:** The rails-api fixture directory, the change-impact-matrix.md reference.

**Flow:**
1. Copy `fixtures/rails-api/` to a temp directory
2. Copy `skills/maintain/references/change-impact-matrix.md` into the temp dir's `.claude/references/`
3. Run `claude -p "$SCENARIO_PROMPT" --output-format json --permission-mode bypassPermissions` in the temp dir
4. Run the matrix judge on the output
5. Output: `X/5 effects identified`, per-effect breakdown, PASS/FAIL

**Scenario prompt** (embedded in script): Describes a new security auditor persona being added to CLAUDE.md and asks what other `.claude/` files need updating as a result.

**5 expected downstream effects:**
1. `review-criteria.md` needs regeneration (new quality bars → new review criteria)
2. `.claude/rules/` line budget check (added content may push files toward 60-line cap)
3. Snap audit (coverage check now includes security, calibration check covers one more persona)
4. Possible new reference file (`references/security-patterns.md` for deep security knowledge)
5. `workflow.md` "When to Go Deeper" (may need pointer for auth/input handling reviews)

**Pass threshold:** ≥3/5 effects identified.

**Limitation (acknowledged):** Same as R5 — this tests whether Claude applies the change-impact-matrix.md reference when present, not whether `gigo:maintain` or `gigo:snap` route to it during their workflows. The rationale is the same: content activation is the proxy. If Claude can't identify downstream effects even with the matrix directly in context, the matrix isn't adding value regardless of skill-pipeline routing.

### R9: Phase Selection Matrix Judge Prompt

Create `evals/validation/matrix-judge.md`.

**Template variables:** `{RESPONSE}`

**Behavior:** For each of 5 expected downstream effects, score YES or NO based on whether the response identifies the effect (matching on concept, not exact wording).

**Output format:** JSON array of 5 entries:
```json
[{ "effect": "review-criteria regeneration", "identified": true, "evidence": "..." }, ...]
```

### R10: Agent Teams Cleanup Verification Script

Create `evals/validation/run-cleanup-verify.sh`.

**Pure grep — no Claude invocations.** Fastest test in the suite.

**5 checks:**
1. No `Tier 3` references in `skills/execute/SKILL.md` production sections (allow in "Future: Agent Teams" pointer)
2. No `TeamCreate` or team-scoped `SendMessage` in `skills/execute/SKILL.md`
3. No `Tier 3`, `team.prompt`, or `team.template` in `skills/execute/references/teammate-prompts.md`
4. Design doc exists at `skills/execute/references/agent-teams-design.md` with status banner
5. No `AGENT_TEAMS` or `EXPERIMENTAL_AGENT` env var references in `skills/execute/SKILL.md` production paths

**Pass threshold:** 5/5 checks clean.

### R11: Master Runner

Create `evals/validation/run-all.sh`.

Runs all 5 tests in sequence and aggregates results:

```
=== Feature Validation Suite ===

1. Boundary-Mismatch Detection:    X/6 detected   [PASS/FAIL ≥4]
2. Phase Selection Matrix:         X/5 effects     [PASS/FAIL ≥3]
3. Execution Pattern Catalog:      X/3 patterns    [PASS/FAIL 3/3]
4. Agent Teams Cleanup:            X/5 checks      [PASS/FAIL 5/5]
5. Regression (assembled vs bare): XX% wins        [PASS/FAIL ≥90%]

Overall: X/5 PASS

Results saved to: evals/results/validation-YYYY-MM-DD-HHMMSS/
```

**Regression check:** Invokes existing `evals/run-eval.sh` and `evals/score-eval.sh`. No new code for this — the existing infrastructure handles it.

**Path resolution:** `run-all.sh` lives in `evals/validation/`. It resolves sibling paths using `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"` and `EVALS_DIR="$(dirname "$SCRIPT_DIR")"`. The regression check calls `"$EVALS_DIR/run-eval.sh"` and `"$EVALS_DIR/score-eval.sh"`.

**Results directory:** Each run creates `evals/results/validation-YYYY-MM-DD-HHMMSS/` with all raw outputs and scores.

---

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| test | R2 (boundary test), R5 (pattern test), R8 (matrix test), R10 (cleanup verify), R11 (master runner + regression) | ✅ |
| built | R1 (fixture replicates the integration context these features target), R10 (verifies cleanup is complete) | ✅ |
| make sure / adding value | R2-R11 (each test has a pass/fail threshold proving the feature activates), R11 (regression confirms no harm) | ✅ |

---

## Conventions

### Script Naming
- Test scripts: `run-<feature-name>.sh` (e.g., `run-boundary-test.sh`)
- Master runner: `run-all.sh`
- All scripts in `evals/validation/`

### Output Format
- Each test script outputs a summary line: `X/N <metric>   [PASS/FAIL ≥threshold]`
- Raw outputs saved to `evals/results/validation-YYYY-MM-DD-HHMMSS/`
- Judge outputs are JSON (parseable by scripts)

### Judge Prompt Template Format
- Template variables in `{CURLY_BRACES}` — matches existing `evals/judge-prompt.md` pattern
- Each judge prompt produces structured JSON output
- Scoring is concept-based (matching on meaning, not exact wording)

### Prompt File Format
- `<axis>|<prompt>` — one per line, matching existing `evals/prompts/*.txt` convention. Axis is a single-letter label (`P` for planning prompts). The script reads it as `IFS='|' read -r axis prompt`.

### Claude Invocation
- All Claude calls use: `claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions`
- Matches existing `evals/run-eval.sh` invocation pattern

### Pass/Fail Thresholds
- Boundary-mismatch: ≥4/6 (60% detection floor — proving feature activates)
- Phase selection matrix: ≥3/5 (core effects matter most)
- Execution patterns: 3/3 (obvious cases — if it misses these, the catalog isn't working)
- Agent Teams cleanup: 5/5 (binary — any Tier 3 in production paths is a failure)
- Regression: ≥90% assembled wins (4-point buffer from 94% baseline)

### Fixture Conventions
- CLAUDE.md follows existing fixture pattern (~60 lines, 3 personas, autonomy model, quick reference)
- Rules files follow GIGO standards (snap.md, standards.md, workflow.md)
- Source files use TypeScript syntax but aren't compilable — realistic enough to test pattern recognition
- DEFECT-MANIFEST.md is always excluded from Claude's context during testing

### Error Handling
- Scripts exit with code 0 on PASS, code 1 on FAIL
- If Claude invocation fails (timeout, API error), the test reports ERROR (not FAIL)
- Master runner continues through errors, reports them in the summary

---

## Scope

**In scope:** 1 fixture directory (~15 files), 4 test scripts, 3 judge prompts, 1 rubric, 1 prompt file, 1 master runner. All in `evals/`.

**Out of scope:**
- Layer 2 (version A/B comparison between two assembled versions) — dropped during design. Features affect review/planning paths, not response quality; the 5-criteria judge won't reliably distinguish.
- New eval framework — extending the existing one.
- Tests for unshipped features (Agent Teams execution mode).
- Modifications to existing eval scripts (`run-eval.sh`, `score-eval.sh`, `judge-prompt.md`).
- Changes to the 4 feature files themselves.

<!-- approved: spec PENDING -->
