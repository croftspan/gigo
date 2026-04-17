# Two-Gate context7 Research Pipeline — Design Spec

**Design brief:** `.claude/plans/crystalline-crunching-aurora.md`

## Original Request

> I want to add a two-gate context7 research pipeline to GIGO, triggered by a real incident where spec shipped weeks of Unity C# against .NET APIs that don't exist in Unity 6's BCL. Core shape is decided: Gate 1 pre-spec discovery, Gate 2 post-plan adversarial confirmation, both using independent subagents with context7 MCP as primary doc source, via-negativa framing on Gate 2, block-on-❌ before execute dispatches. Full context, decided constraints, and open questions are in briefs/11-context7-research-gates.md. Read that first, then start discovery on the open questions — don't re-litigate the decided constraints. Related memory: feedback_blueprint_spec_platform_verification.md, project_research_gate_blueprint_to_spec.md.

---

## Overview

Add two research gates to GIGO's spec → execute pipeline. Both use the `context7` MCP as primary documentation source with independent subagents (fresh context, no shared reasoning chain).

- **Gate 1 — Pre-Spec Discovery** runs at a new spec Phase 0, before Phase 5 writes the spec. Grounds the target runtime's API surface so the spec and plan don't assume nonexistent APIs. Output: `docs/gigo/research/YYYY-MM-DD-<topic>-tech-constraints.md`.
- **Gate 2 — Post-Plan Adversarial Verification** runs at a new spec Phase 9.75, after Phase 9.5 Challenger and before Phase 10 operator review. Extracts every specific API the plan names and adversarially verifies each against context7. Output: `docs/gigo/research/YYYY-MM-DD-<topic>-plan-verification.md`.
- **Block-on-❌ enforcement** at `gigo:execute` startup: execute resolves the plan-verification artifact by parsing the frontmatter `plan:` field, computes effective status from the body (not the frontmatter `status:`), and refuses to dispatch tasks when unresolved ❌ findings exist.
- **Blueprint Phase 4** captures a `## Platform & Runtime Targets` section in the design brief when applicable, feeding Gate 1's trigger detection.

---

## 1. Requirements

### R1: Gate 1 — Pre-Spec Research (spec Phase 0)

**R1.1** A new Phase 0 in `skills/spec/SKILL.md` runs BEFORE Phase 5 (Write Spec).

**R1.2** Phase 0 trigger detection:
- Read the approved design brief.
- Scan for a `## Platform & Runtime Targets` section. If present, extract the target list (each target: name + version + notes) and run Gate 1 with those targets.
- Scan for an explicit `**Targets:** none` declaration. If present, Phase 0 MUST prompt the operator to confirm: *"The brief declares `Targets: none` — this will skip API verification gates. Confirm: is this a pure content/config project with NO shipped code that targets a runtime? [yes, skip gates / no, this ships code — let me name targets]."* Only proceed with skip if operator confirms explicitly. (This closes the blueprint-misclassification bypass — the same failure mode that caused the Unity incident.)
- If neither section nor `Targets: none` is present, prompt the operator with a **default-skeptical** framing:
  > "This is a code project. What runtime / platform / SDK does it target? Answer `none` only if this is pure content/config with no code output. Otherwise name the target(s) — e.g., `Unity 6 .NET Standard 2.1`, `Node 20 LTS`, `iOS 17 SDK`, `VSCode Extension API 1.85`."
  
  The framing assumes code projects target *something*; the burden of proof is on skipping the gate, not running it. Operator must explicitly answer `none` to skip.

**R1.2a** Small-task handling (revised — closes the bypass identified by Challenger):

Small-task skip does NOT skip Gate 1 entirely for code projects. Instead:
- A brief with `**Scale:** small` AND non-code output (docs tweak, config typo, README fix) → skip both gates fully.
- A brief with `**Scale:** small` AND code output (bug fix in Unity, single-method change in an iOS app, etc.) → **Gate 1 runs host-shell detection (R1.6) only**, skipping deep API discovery. The rationale: small code changes still ship against the target runtime. The 30-second host-shell check is cheap and would have caught the Unity incident's "no `Assets/` + `ProjectSettings/`" smell. Gate 2 also runs on the resulting (small) plan with minimal overhead.
- A brief with `**Scale:** small` but no scale-vs-code-output distinction → Phase 0 asks the operator: *"Small task — does it produce any code that ships against a runtime (even one line)? [yes, run host-shell check / no, skip all gates]."*

The point: the cheap piece of Gate 1 (host-shell detection) is mandatory for any code-producing work. Only pure non-code tasks bypass fully.

**R1.3** When Phase 0 runs, dispatch research subagents **sequentially** (one target at a time) via `Agent` tool with `subagent_type: "general-purpose"` and the prompt template from `references/research-gate-1.md`. Sequential dispatch avoids the append/overwrite race condition from parallel writes to the same artifact file.

**R1.4** Each subagent receives:
- `{TARGET_NAME}`, `{TARGET_VERSION}` from the brief or operator prompt
- `{DEPTH}` (`light` or `deep`) — computed by Phase 0 per the depth calibration table (§R1.5)
- `{SCOPE_NOTES}` — the relevant brief excerpt for this target
- `{DATE}`, `{TOPIC}`, `{BRIEF_NAME}` — for artifact frontmatter and filenames

**R1.5** Depth calibration (Phase 0 computes before dispatch):

| Depth | Targets |
|---|---|
| `deep` (default for high-risk) | Unity, Unreal, Godot, Bevy, GameMaker; iOS/macOS/Android SDKs; WinUI/WPF; RTOS and microcontroller SDKs; Figma/Chrome/Firefox/VSCode/Obsidian/Blender plugin APIs; managed-runtime hosts (custom/restricted BCL); any target released < 2 years before today |
| `light` | Node 20+ LTS, Python 3.11+, Go 1.22+, Rust stable; React, Vue, Svelte, Next.js (current majors); Django, Rails, FastAPI, Express (current majors); stable cloud SDKs (AWS v3, GCP, Azure) |
| `deep` (unknown target) | If the target doesn't match either list, default to `deep`. False-positive cost is ~30s per target; false-negative cost is weeks (the Unity incident). |

Operator may override depth explicitly at Phase 0 (e.g., "run light for all targets").

**R1.6** Host-shell detection (Gate 1 first-class subtask — required, not optional):

Per-target-family heuristics the subagent evaluates:

| Target family | Required host-shell artifact |
|---|---|
| Unity (any language) | `Assets/` AND `ProjectSettings/` at repo root or a declared sub-path |
| .NET general (non-Unity) | `.csproj` or `.sln` |
| Unreal | `.uproject` |
| iOS / macOS | `.xcodeproj`, `.xcworkspace`, or `Package.swift` |
| Android | `build.gradle(.kts)` AND `AndroidManifest.xml` |
| VSCode extension | `package.json` with `engines.vscode` declared |
| Browser extension | `manifest.json` matching MV3 schema |
| Plugin/library with no host | Spec must contain an explicit `**External-consumer-only:** true` declaration — else Gate 1 flags |

If the required artifact is missing AND the spec does not explicitly declare `external-consumer-only`, Gate 1 writes `Host-Shell Requirement: MISSING — [recommendation]` in the artifact and Phase 0 surfaces this to the operator before spec writing begins.

**R1.7** `tech-constraints.md` artifact schema (required fields and body sections):

```markdown
---
spec: docs/gigo/specs/YYYY-MM-DD-<topic>-design.md
brief: .claude/plans/<brief-name>.md
run-at: <ISO-8601 UTC timestamp>
subagent: general-purpose
depth: light | deep | WebSearch-only    # last value indicates context7 MCP unavailable; Gate 1 degraded to WebSearch
targets: [<name>@<version>, ...]         # list of targets covered in this file
future-coupling: {brief-12: <note>, ...}  # reserved for future integration notes (e.g., Brief 12 mission-control slice-awareness)
---

# Tech Constraints: <topic>

## Target: <name> <version>

**context7 library ID:** <resolved_id> | "unresolved — fallback sources: [urls]"

### Verified APIs / Patterns

- `Exact.Api.Name(params)` — <verbatim doc citation or quote>
- `Pattern.Name` — <verbatim doc citation>

### Known Gaps vs Brief

- Brief assumes X → target does NOT support X. Evidence: <citation>. Suggested replacement: Y.
- If no gaps at this depth: "No gaps identified at <depth> depth. Plan-level verification (Gate 2) will surface specific-API gaps."

### Integration Notes

- <lifecycle constraints, threading model, reload behavior, permission/sandbox notes>

### Host-Shell Requirement

- `met` | `MISSING — <recommendation>`

---

## Target: <next target> ...
```

**R1.8** Phase 0 exit behavior:
- After all subagents complete, Phase 0 reads the artifact.
- If any target has `Host-Shell Requirement: MISSING` or `context7 library ID: unresolved`, surface to operator with a clear summary: *"Gate 1 found [N] issue(s) the spec should address: [summary]. Proceed to spec writing, or adjust scope first?"*
- Operator can proceed, adjust brief, or abort.
- Phase 5 must not start until Phase 0 is complete (or explicitly skipped).

---

### R2: Gate 2 — Post-Plan Adversarial Verification (spec Phase 9.75)

**R2.1** A new Phase 9.75 in `skills/spec/SKILL.md` runs AFTER Phase 9.5 (Challenger) and BEFORE Phase 10 (Operator Reviews Plan).

**R2.2** Gate 2 triggers only if Gate 1 ran (i.e., a `tech-constraints.md` exists for the current spec). If Gate 1 skipped, Gate 2 skips.

**R2.3** Gate 2 dispatches a **single** verification subagent via `Agent` tool with `subagent_type: "general-purpose"` and the prompt template from `references/research-gate-2.md`. The subagent must run in fresh context — NOT the spec author's session, NOT sharing context with Gate 1's subagent, NOT the Challenger's subagent.

**R2.4** The Gate 2 prompt template embeds via-negativa framing verbatim. The subagent is instructed to:
- Assume the plan is wrong; default to skepticism
- Extract every specific that could be verified: method calls with signatures, library/framework names with versions, language features, integration patterns, configuration knobs, package names
- Query context7 for each extracted item (resolve-library-id + query-docs)
- Record `✅` ONLY with a verbatim doc citation; "looks right" or "probably exists" is `❌`
- Fall back to WebSearch for items context7 cannot cover, with source URL and quote
- Do NOT trust Gate 1's `tech-constraints.md` as evidence for specific methods — Gate 1 covered surface, Gate 2 covers specifics

**R2.5** `plan-verification.md` artifact schema (required fields and body):

```markdown
---
plan: docs/gigo/plans/YYYY-MM-DD-<feature>.md      # MUST match the plan being verified (execute uses this for resolution)
spec: docs/gigo/specs/YYYY-MM-DD-<topic>-design.md
tech-constraints: docs/gigo/research/YYYY-MM-DD-<topic>-tech-constraints.md
run-at: <ISO-8601 UTC timestamp>
run-number: <integer, starts at 1, increments on re-runs>
subagent: general-purpose
status: pass | fail         # ADVISORY ONLY. Written by subagent on first pass. Consumers derive effective status from body.
total-findings: <integer>
pass-findings: <integer, ✅ count>
fail-findings: <integer, ❌ count>
---

# Plan Verification: <topic>

**Target:** <target-summary>

## Findings

| # | Plan Reference | Named Specific | Target | Status | Evidence / Suggested Fix |
|---|---|---|---|---|---|
| 1 | Task 4, Step 2 | `Process.WaitForExitAsync(ct)` | Unity 6 (.NET Standard 2.1) | ❌ | Not present in context7 Unity 6 docs. .NET Standard 2.1 does not include this overload (first added in .NET 5). Suggested: wrap `p.WaitForExit()` in `Task.Run` and observe cancellation via `ct.Register(() => p.Kill())`. |
| 2 | Task 4, Step 4 | `string.Contains(char)` | Unity 6 | ✅ | context7: "System.String.Contains(Char) available from .NET Standard 2.1 onwards." |

## Overrides

<!-- Gate 2 overrides live here. Operator-added markers only. Empty on fresh runs. Format:
<!-- override: finding-N reason:<reason> approved-by:<username> timestamp:<ISO-8601> -->

Each marker resolves exactly one ❌ finding. Finding numbers are per-run; re-runs invalidate prior overrides.
-->

## Exit Status

First-pass status (written by the Gate 2 subagent): `pass` if zero ❌, `fail` otherwise. Consumers re-derive effective status from body.
```

**R2.6** Body-as-truth authority model (closes design risk #1 — override mutation cycle):
- The artifact **body** is the source of truth for pass/fail/needs-override.
- Frontmatter `status:` is **advisory only** — written once by the Gate 2 subagent on the first pass, NEVER mutated after.
- Consumers (execute, spec Phase 10) compute **effective status** from the body.

**R2.7** Derived Status Calculation (the canonical algorithm consumers use):

Given a `plan-verification.md` body, consumers operate on the LATEST `## Run N — <timestamp>` section (locate by scanning for `## Run ` headers, pick the one with the highest N or the latest timestamp; use timestamp on ties).

Within that run's section:
1. Count ❌ rows in the `### Findings` sub-section → `N_fail`
2. Count **valid** override markers in `### Overrides (Run N)` — valid means ALL of:
   - Marker comment matches the strict regex `^<!-- override: finding-(\d+) reason:(.+?) approved-by:(.+?) timestamp:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) -->$`
   - `finding-N` matches an existing ❌ row number in the current run's findings table
   - `reason`, `approved-by`, and `timestamp` capture groups are all non-empty after trimming whitespace
   - A single ❌ row is covered by at most one valid override (duplicate overrides for the same finding: first valid one counts, rest are logged as `DUPLICATE-OVERRIDE` in the surface-to-operator list)
   - Malformed markers (wrong format, missing fields, bad timestamp, non-existent finding-N) are NOT counted toward `N_override_matched` but ARE surfaced to the operator as `MALFORMED-OVERRIDE` on block-on-❌ refusal — so operator sees "you wrote 3 overrides but 1 didn't parse"
   - Call the valid count `N_override_matched`
3. Derive effective status:
   - `N_fail == 0` → `pass`
   - `N_fail > 0 AND N_override_matched == N_fail AND every ❌ row has a matching valid override` → `needs-override`
   - `N_fail > 0 AND not all ❌ rows covered` → `fail`
   - Body structure missing, latest-run section malformed, or findings table unparseable → `fail` (safer default; do not silently pass)

The frontmatter `status:` is never trusted alone. When frontmatter and body disagree, the body wins.

**Test matrix** (every consumer implementation MUST handle these cases deterministically; included in `references/research-gate-2.md` as worked examples):

| Input | Expected effective status | Expected message |
|---|---|---|
| Body has no `## Run` sections | `fail` | "plan-verification artifact has no run sections — unparseable" |
| Latest run: 0 findings rows | `fail` | "latest run's findings table is empty or missing" |
| Latest run: 5 ✅, 0 ❌ | `pass` | — |
| Latest run: 3 ✅, 2 ❌, 0 overrides | `fail` | List 2 unresolved ❌ with suggested fixes |
| Latest run: 3 ✅, 2 ❌, 2 valid matching overrides | `needs-override` | "Executing with 2 acknowledged API gaps" |
| Latest run: 3 ✅, 2 ❌, 1 valid override + 1 malformed | `fail` | List 1 unresolved ❌ + note "1 override was malformed: [details]" |
| Latest run: 3 ✅, 2 ❌, 2 valid overrides for finding-1 + 0 for finding-2 | `fail` | "finding-2 has no override; finding-1 has duplicate overrides (one ignored)" |
| Latest run: 3 ✅, 1 ❌, 1 override pointing at non-existent finding-99 | `fail` | "1 unresolved ❌ (finding-1); 1 malformed override (finding-99 does not exist)" |
| Body has 2 `## Run` sections, Run 1 passes, Run 2 fails | `fail` | Evaluate Run 2 only; Run 1 historical |
| Body has 2 `## Run` sections, Run 1 fails, Run 2 passes | `pass` | Evaluate Run 2 only; Run 1's ❌ is historical |

**v2 followup (out of scope for this spec):** a helper script at `.claude/hooks/check-plan-verification.sh` can codify this derivation for shell-level enforcement, mirroring `gate-check.sh`'s pattern. Not required for v1 but noted so the architectural symmetry is preserved when the script is written.

**R2.8** Re-run semantics — append-only per-run sections (revised per Challenger — makes audit trail mechanical, not aspirational):

The artifact is **append-only across runs**. Each Gate 2 run appends a new `## Run N` section with its own findings table and overrides sub-section. Derivation always uses the LATEST run.

Structure after multiple runs:

```markdown
---
<frontmatter: only the LATEST run's metadata (run-number, run-at, status)>
---

# Plan Verification: <topic>

**Target:** <target-summary>

## Run 1 — <ISO-8601 timestamp>

### Findings

| # | Plan Reference | Named Specific | Target | Status | Evidence / Suggested Fix |
|---|---|---|---|---|---|
| 1 | ... | ... | ... | ❌ | ... |
| 2 | ... | ... | ... | ✅ | ... |

### Overrides (Run 1)

<!-- override: finding-1 reason:... approved-by:... timestamp:... -->

## Run 2 — <ISO-8601 timestamp>

### Findings

| # | Plan Reference | Named Specific | Target | Status | Evidence / Suggested Fix |
|---|---|---|---|---|---|
| 1 | ... (different from run 1's finding-1) | ... | ... | ❌ | ... |

### Overrides (Run 2)

<!-- operator adds overrides here for run 2's findings -->

## Run 3 — ...
```

**Per-run rules:**
- Each run appends a new `## Run N — <timestamp>` section. Does NOT modify prior run sections.
- Finding numbers are scoped to the run (Run 1 finding-1 and Run 2 finding-1 are independent).
- Override markers inside `### Overrides (Run N)` apply ONLY to findings in that same Run N section.
- Frontmatter `run-number` is the latest run; `run-at` is the latest run's timestamp.
- Derivation algorithm (§R2.7) operates on the LATEST run's section only.

**Why append-only:** the operator's audit trail ("every override has a named approver, reason, timestamp") now survives intrinsically in the artifact itself, not via a "remember to commit before re-running" discipline. A second re-run before committing preserves the first run's overrides on disk.

**Old-run invalidation still applies to overrides:** an operator reviewing a fresh run must add overrides to THAT run's Overrides section — they cannot reuse prior-run marker numbers. This is explicit in the section structure.

**Git history remains the long-term audit;** append-only is the short-term in-file audit, preventing the "lost between runs" failure mode.

**R2.9** Phase 9.75 exit behavior:
- After Gate 2 subagent completes, spec computes effective status per §R2.7.
- `pass` → proceed to Phase 10 normally.
- `fail` → do NOT write the plan approval marker. Present findings to operator at Phase 10 with all ❌ rows listed. Operator must either request plan revision (spec returns to Phase 8 → 9 → 9.5 → 9.75 re-run) or add override markers to the `## Overrides` section.
- `needs-override` → proceed to Phase 10 with override count summarized. Operator approval at Phase 10 acknowledges the overrides by signing the plan.

---

### R3: Block-on-❌ Enforcement at Execute Startup

**R3.1** `skills/execute/SKILL.md` "Before Starting" section gains a new step (inserted between current steps 1 and 2): check plan verification.

**R3.2** Plan-verification artifact resolution (closes design risk #3 — plan-verification matching):
- Scan `docs/gigo/research/*-plan-verification.md`.
- For each candidate, read frontmatter `plan:` field. Canonicalize BOTH the frontmatter `plan:` value AND the plan being executed to absolute paths (resolve `~`, convert relative paths using `$CLAUDE_PROJECT_DIR` or the current working directory, resolve symlinks via `realpath`/`readlink -f`). Compare canonicalized paths.
- If multiple candidates match after canonicalization, select the one with the most recent `run-at` frontmatter timestamp.
- If zero candidates match → treat as skipped gates; proceed.
- Do NOT rely on filename-convention matching. The frontmatter `plan:` field is authoritative.
- If the frontmatter `plan:` field is missing or empty in a candidate artifact, log the candidate as `MALFORMED-ARTIFACT` and continue (do not use it for matching, but surface in refusal message if no valid candidate is found).

**R3.3** Effective-status computation at startup uses the algorithm from §R2.7 — body-as-truth, not frontmatter. Consumer code must not trust `status:` frontmatter alone.

**R3.4** Execute startup behavior:

| Effective status | Execute behavior |
|---|---|
| `pass` | Proceed normally. |
| `needs-override` | Announce before first dispatch: `"Executing with [N_override_matched] acknowledged API gaps per <artifact-path>"`. Proceed. |
| `fail` | REFUSE to start. Report: `"Plan verification has [N_fail - N_override_matched] unresolved ❌ findings at <artifact-path>. Resolve by revising the plan (Gate 2 re-runs on revision) or adding override markers in ## Overrides section. Format: <!-- override: finding-N reason:... approved-by:... timestamp:... -->. Re-run /execute after."` Then list each unresolved ❌ inline with finding number, named specific, target, and suggested fix. |
| (no matching artifact) | Treat as skipped gates. Proceed. |
| (artifact exists but body table missing/malformed) | REFUSE. Report the specific parse issue with the artifact path. |

**R3.5** Add to execute's Red Flags section (the "Never" list):
- `Dispatch tasks when plan-verification.md shows effective status: fail with unresolved ❌ findings — the operator must revise the plan OR add override markers first`

---

### R4: Blueprint Platform & Runtime Targets Capture

**R4.1** `skills/blueprint/SKILL.md` Phase 4 (Present Design) gains a new guidance subsection on capturing `## Platform & Runtime Targets` in the design brief.

**R4.2** The guidance instructs blueprint to:
- Include a `## Platform & Runtime Targets` section in the brief when the project targets a specific runtime, platform, SDK, or external library.
- For each target, capture: name + version, BCL/language surface notes (when applicable), consuming host project shell requirement (e.g., `Assets/` + `ProjectSettings/` for Unity, `.xcodeproj` for iOS), known runtime constraints.
- Skip the section for pure design/content projects OR code projects using only ubiquitous stable runtimes with no unusual constraints (Node 20 LTS, Python 3.11, etc.).

**R4.3** Blueprint Phase 4 self-check (closes design risk #5 — blueprint capture fragility):

After drafting the design and before writing `Post-Approval`, blueprint runs an explicit self-check:

> "Is this a code project? If yes, does the brief include a `## Platform & Runtime Targets` section? If no, either:
> - Add the section with the target list, OR
> - Add an explicit `**Targets:** none` declaration to the brief header justifying why (pure content, pure config, etc.)
>
> Without one of these, spec Phase 0 will prompt for targets anyway. Capturing here saves a prompt and catches scope drift."

This is a blueprint-side enforcement point — the spec Phase 0 default-skeptical fallback is the safety net, but blueprint is the first line of defense.

---

### R5: New Reference Files

**R5.1** Create `skills/spec/references/research-gate-1.md`. File MUST contain:
- Purpose statement (Gate 1's role)
- Trigger detection logic (references the brief's Platform & Runtime Targets section + default-skeptical fallback + `Targets: none` confirmation flow)
- Depth calibration table (R1.5) — copied verbatim
- Sequential dispatch procedure: lead constructs TWO prompt variants — variant-first for the FIRST subagent (creates the artifact file with frontmatter header, writes the first `## Target:` section), variant-subsequent for LATER subagents (file already exists; APPEND a new `## Target:` section at the end, do not touch frontmatter or prior target sections). Both variants share the same body structure; only the "create-vs-append" instruction differs.
- Host-shell checklist (R1.6) — verbatim with per-target heuristics
- **Verbatim subagent prompt templates** (two fillable templates, variant-first and variant-subsequent). Not a description of what the prompt should cover — the actual prompt text with `{PLACEHOLDERS}` where the lead substitutes values. A bare worker implementing execute-side dispatch must be able to copy-paste the template and fill placeholders without inventing structure.
- `tech-constraints.md` artifact schema (R1.7) — verbatim with example
- Error handling table: context7 MCP not available (Gate 1 degrades to WebSearch-only mode, flags `depth: WebSearch-only` in frontmatter); context7 resolve-library-id returns no match; subagent crash mid-research (retry once, then surface partial artifact); ambiguous target resolution; file-already-exists from earlier spec run (overwrite with operator confirmation — never silently); concurrent spec runs on same topic (append a run suffix `-r2`, `-r3` OR prompt operator to disambiguate)
- "What this gate does NOT do" clarifications

**R5.2** Create `skills/spec/references/research-gate-2.md`. File MUST contain:
- Purpose statement (Gate 2's role)
- Fire conditions (Gate 1 ran + plan finalized + plan edits after initial Gate 2 pass trigger re-run)
- Dispatch procedure (single independent subagent, fresh context, dispatched via `Agent` tool)
- **Verbatim adversarial prompt template** — the actual prompt text with `{PLACEHOLDERS}` that the lead fills. Must embed the via-negativa framing verbatim: "Assume this plan is wrong. Default to skepticism. ✅ requires a verbatim context7 doc citation; 'looks right' is ❌. You are not helping the plan succeed; you are finding what's broken before it ships." Not a description — the actual paragraph the subagent reads.
- `plan-verification.md` artifact schema (R2.5) — verbatim with example of append-only multi-run structure
- Body-as-truth authority model (R2.6)
- Derived Status Calculation (R2.7) **with the test matrix from R2.7 copied verbatim** as worked examples
- Override mechanism with marker format and validation regex
- Re-run semantics with append-only per-run structure (R2.8)
- Block-on-❌ behavior table (R3.4)
- Independence rules (non-negotiable — separate subagent, fresh context, no context sharing with Gate 1 / Challenger / spec author; note that "different subagent invocation, same input artifact" satisfies the independence rule per the Challenger's feedback)
- Error handling table: context7 MCP not available (verifier marks every context7-requiring item as ❌ by default; operator can override with WebSearch citations); subagent extracts zero specifics; subagent crash; operator adds override to wrong run section (malformed — caught by R2.7 derivation)
- "What this gate does NOT do" clarifications

---

### R6: Spec SKILL.md Integration Points

**R6.1** Announce line update: add `"Phase 0: Researching platform targets..."` at start and `"Phase 9.75: Verifying plan against live docs..."` before Phase 10.

**R6.2** New "## Phase 0: Pre-Spec Research Gate (Gate 1)" section, inserted after the "## Locate the Design Brief" section and before "## Phase 5: Write Spec". Content summarizes R1; procedural depth in `references/research-gate-1.md`.

**R6.3** Phase 5 gains a paragraph: "If Gate 1 ran, also read `docs/gigo/research/<date>-<topic>-tech-constraints.md` — the spec's Conventions section and Tech Stack references must reflect verified constraints, not assumed ones. If Gate 1 flagged `Host-Shell Requirement: MISSING`, include the host-shell addition (or an explicit `external-consumer-only` declaration) as a spec requirement."

**R6.4** Phase 8 gains a paragraph: "If Gate 1 ran, also read `docs/gigo/research/<date>-<topic>-tech-constraints.md` — every API, method, or pattern named in task code blocks must come from the verified surface, not from training-data recall."

**R6.5** New "## Phase 9.75: Post-Plan Verification Gate (Gate 2)" section, inserted between "## Phase 9.5: The Challenger (Plan)" and "## Phase 10: Operator Reviews Plan". Content summarizes R2; procedural depth in `references/research-gate-2.md`. Must explicitly state the independence rule (fresh subagent, not spec author, not Challenger).

**R6.6** Sequencing clarification for Phase 9.5 → 9.75:

- If Challenger (9.5) recommends plan revisions and the operator accepts them, the revisions are applied BEFORE Gate 2 dispatches.
- If the plan is edited AFTER Gate 2 has already run (e.g., operator accepts a Challenger revision post-hoc, or edits in response to operator review), Gate 2 MUST re-run on the revised plan. The revised plan may contain new specifics not covered by the prior Gate 2 pass; skipping re-verification creates a silent bypass of block-on-❌. Spec detects "plan edited after Gate 2" by checking: (a) plan file mtime is newer than the artifact's latest `run-at`, OR (b) plan has no `<!-- approved: plan ... -->` marker, indicating revision-in-progress.
- If Gate 2 subsequently triggers another plan revision (❌ findings require polyfill tasks, etc.), Challenger does NOT re-run automatically (engineering quality is orthogonal to API-existence fixes); operator may explicitly request a re-Challenger if the revision is structurally significant.

**R6.7** Phase 10 update: after the standard plan-review prompt, if Gate 2 ran, also present the verification artifact: *"Plan verification saved to `<path>`. Effective status: [pass / needs-override / fail]. [Summary of ❌ findings if any.]"* Do NOT write the plan approval marker while effective status is `fail`.

**R6.8** Handoff update: mention that execute reads `plan-verification.md` at startup and refuses to dispatch on unresolved ❌.

**R6.9** Pointers section gains entries for `references/research-gate-1.md` and `references/research-gate-2.md`.

**R6.10** `skills/spec/SKILL.md` stays under 500 lines. Procedural detail lives in references per GIGO convention.

---

### R7: CHANGELOG Entry

**R7.1** Append a `[Unreleased]` section to `CHANGELOG.md` documenting:
- Gate 1 (Phase 0, purpose, output artifact, depth heuristic, host-shell check, incident that motivated it)
- Gate 2 (Phase 9.75, purpose, via-negativa framing, adversarial verification, output artifact)
- Block-on-❌ enforcement in execute
- Override mechanism with marker format
- Body-as-truth authority model (explain why frontmatter `status:` is advisory)
- Re-run invalidates prior overrides
- Trigger scope (code projects with named targets; skip for design/content/small tasks)
- Blueprint Phase 4 Platform & Runtime Targets capture + self-check

---

## 2. Conventions

**Artifact paths:**
- Tech constraints: `docs/gigo/research/YYYY-MM-DD-<topic>-tech-constraints.md`
- Plan verification: `docs/gigo/research/YYYY-MM-DD-<topic>-plan-verification.md`
- Both use the SAME `<topic>` slug as the corresponding spec (e.g., spec `2026-04-17-foo-design.md` → `2026-04-17-foo-tech-constraints.md`)

**Override marker format (exact):**
```
<!-- override: finding-<N> reason:<non-empty string, no unescaped newlines> approved-by:<git username> timestamp:<ISO-8601 UTC> -->
```
Example:
```
<!-- override: finding-3 reason:Task 7 adds Newtonsoft.Json fallback layer for projects without com.unity.nuget approved-by:eaven timestamp:2026-04-17T22:48:46Z -->
```

**Error message format for execute refusal (verbatim, operator sees this):**
```
Plan verification has [N_fail - N_override_matched] unresolved ❌ findings at <artifact-path>.

Resolve by revising the plan (Gate 2 re-runs on revision) or adding override markers in ## Overrides section.

Format: <!-- override: finding-N reason:... approved-by:... timestamp:... -->

Re-run /execute after.

Unresolved findings:
  finding-N: <named-specific> (<target>) — <suggested-fix>
  ...
```

**Error message format for Gate 1 missing host-shell:**
```
Gate 1 flagged missing host-shell artifact for target <target>.
  Required: <artifact-description>
  Recommendation: <one of: add smoke host | declare external-consumer-only | re-scope>

Spec Phase 5 must address this before writing the spec.
```

**Subagent dispatch:** All three subagents (Gate 1 targets, Gate 2 verifier) use `Agent` tool with `subagent_type: "general-purpose"`. The dispatch prompt is the ONLY input — do not expect subagents to read session context.

**Timestamps:** All timestamps in artifacts and markers are ISO-8601 UTC with `Z` suffix (e.g., `2026-04-17T22:48:46Z`). Match existing approval-marker convention.

**Status frontmatter vocabulary:**
- `status: pass | fail` — written by subagents on first pass (no `needs-override` on first write; that's a derived state only).
- Derived effective status: `pass | fail | needs-override`. Consumers use this.

**Re-run trigger:** Gate 2 re-runs when ANY of: (a) the plan file's `<!-- approved: plan ... -->` marker is absent, indicating revision-in-progress; (b) the plan file's mtime is newer than the latest `plan-verification.md` run's `run-at` timestamp (catches "edited after Gate 2 passed"); (c) the operator explicitly says "re-run Gate 2". These are the canonical triggers. When in doubt, ask the operator before re-dispatching.

**context7 MCP availability:** If the context7 MCP tools (`mcp__plugin_context7_context7__resolve-library-id`, `mcp__plugin_context7_context7__query-docs`) are not available in the operator's environment, gates degrade deterministically: Gate 1 runs in WebSearch-only mode and marks `depth: WebSearch-only` in frontmatter; Gate 2 marks every item that would have required context7 as ❌ by default (operator can accept with override markers + WebSearch citations). The pipeline does not silently skip verification just because context7 isn't installed — it degrades visibly.

**Gate-check hook interaction:** `.claude/hooks/gate-check.sh` enforces approval markers on `docs/gigo/specs/*` and `docs/gigo/plans/*`. Artifacts under `docs/gigo/research/*` are NOT subject to hook enforcement — they are research artifacts, not approval-gated artifacts. Writes during Phase 0 (before spec approval marker exists) are allowed because the research directory is outside the hook's scope.

**Concurrent spec runs on same topic+date:** If an artifact for the same `YYYY-MM-DD-<topic>` already exists when Phase 0 starts (e.g., operator re-running spec after aborting), the spec MUST prompt: *"A research artifact for <topic> already exists (run-at: <timestamp>). Append a run suffix (-r2, -r3, ...) to the new artifact OR overwrite the existing one?"* Do NOT silently overwrite.

---

## 3. Verb Trace

Extracted action verbs from the original request with requirement mapping:

| Verb | Requirement | Status |
|---|---|---|
| add (pipeline) | R1, R2, R3, R4, R5, R6 — pipeline-wide addition across 3 skills + 2 new refs + CHANGELOG | ✅ |
| ground (Gate 1) | R1.3–R1.8 — Gate 1 grounds target's API surface via context7 discovery | ✅ |
| discover (Gate 1 pre-spec) | R1.3, R1.5 — depth-calibrated discovery via context7 resolve + query | ✅ |
| confirm / verify (Gate 2) | R2.3–R2.9 — adversarial verification via context7 | ✅ |
| extract (specifics from plan) | R2.4 — Gate 2 subagent extracts method calls, library names, patterns, config knobs | ✅ |
| prove (APIs exist) | R2.4 — ✅ requires verbatim context7 doc citation | ✅ |
| fall back (to WebSearch) | R2.4, Conventions — WebSearch fallback for items context7 cannot cover | ✅ |
| block (execute on ❌) | R3.1–R3.5 — execute startup check + Red Flag | ✅ |
| default to skepticism (adversarial framing) | R2.4, R5.2 verbatim prompt — via-negativa posture | ✅ |

No unresolved verbs. All action verbs from the original request map to explicit requirements.

---

## 4. Known Design Risks (Addressed)

The design brief surfaced 5 risks; Challenger review added 3 more. This spec closes each:

### Original risks (from design brief)

**Risk 1 — Override mutation cycle** (who updates `status:` after operator adds override markers?)
→ Closed by R2.6 (body-as-truth authority model) and R2.7 (Derived Status Calculation). Nobody updates frontmatter; consumers derive effective status from body every read. Frontmatter `status:` is advisory only.

**Risk 2 — Gate 1 append/overwrite race** (parallel subagents colliding on one artifact)
→ Closed by R1.3 (sequential dispatch) and R5.1 (reference-file error handling: first subagent creates file with header + first target section, subsequent subagents APPEND new `## Target:` sections; no parallel writes, no race).

**Risk 3 — Plan-verification matching** (execute picking the wrong artifact)
→ Closed by R3.2 (frontmatter `plan:` field is authoritative with ABSOLUTE-PATH canonicalization before comparison; most-recent `run-at` breaks ties; missing `plan:` field logged as MALFORMED-ARTIFACT).

**Risk 4 — Re-run override preservation** (finding numbers change per run)
→ Closed by R2.8 (append-only per-run sections — every Gate 2 run appends a new `## Run N` section; prior runs' findings + overrides preserved on disk; derivation uses latest run only). This is now mechanical, not dependent on git-commit discipline.

**Risk 5 — Blueprint capture fragility** (Phase 4 guidance ignored, operator answers "no" to fallback prompt → gates skip when they shouldn't)
→ Closed by R4.3 (blueprint Phase 4 self-check: must either include Platform & Runtime Targets OR explicit `**Targets:** none` declaration) AND R1.2 (spec Phase 0 requires operator confirmation on `Targets: none`; default-skeptical fallback when neither section is present).

### Risks added by Challenger review

**Risk 6 — Small-task bypass defeats Unity incident coverage** (Challenger Failure Mode 1 / Criterion 6)
→ Closed by R1.2a (revised small-task handling): code-producing small tasks always run Gate 1 host-shell detection; only pure non-code tasks bypass fully. The 30-second host-shell check is mandatory for any work shipping code against a runtime.

**Risk 7 — Challenger-triggered plan revisions bypass Gate 2** (Challenger Failure Mode 2)
→ Closed by R6.6 (revised): plan edits after Gate 2 passed trigger Gate 2 re-run automatically (by mtime check + approval-marker absence); Gate 2 is not a one-shot gate.

**Risk 8 — Malformed override markers silently lost** (Challenger Failure Mode 5)
→ Closed by R2.7 (test matrix): malformed overrides are surfaced in the block-on-❌ refusal message ("you wrote N overrides but M didn't parse"), not silently ignored. DUPLICATE-OVERRIDE, MALFORMED-OVERRIDE, and missing-finding-N cases all produce explicit operator-visible messages.

### Additional safeguards from Challenger feedback

- **context7 MCP availability** (Challenger Feasibility 2): Conventions specify deterministic degradation to WebSearch-only with `depth: WebSearch-only` frontmatter flag; Gate 2 defaults context7-requiring items to ❌ when MCP unavailable.
- **Concurrent spec runs**: Conventions require operator prompt on same-topic+date conflict (append `-r2` suffix OR explicit overwrite confirmation).
- **Verbatim subagent prompts** (Challenger Criterion 2): R5.1 and R5.2 require actual prompt text, not descriptions; bare workers can copy-paste and fill placeholders.
- **Gate-check hook coupling** (Challenger Feasibility 1): Conventions state that `docs/gigo/research/` is outside hook scope; research artifacts write freely without approval markers.

---

## 5. Non-Goals

- **Not replacing Challenger.** Challenger (6.5, 9.5) checks engineering quality. Gate 2 checks API/pattern existence. Different foci, both required for large tasks.
- **Not a runtime test.** Gates verify compile-surface via docs. Actual compilation/execution is a separate concern (spec acceptance criteria, execute post-task verify).
- **Not a general documentation lookup.** Only verifies API/library/pattern existence for implementation plans. Not a replacement for developer research.
- **Not mission-control-aware (Brief 12).** For v1, gates run once per spec+plan pair. Brief 12's slice-based output will revisit per-slice vs per-PRD dispatch. Tech-constraints.md frontmatter includes a note for Brief 12 to find.
- **Not hook-enforced.** Block-on-❌ is artifact-based per GIGO convention (Pipeline v2 principle: every boundary is a potential session boundary, disk artifacts are the interface).

---

## 6. Acceptance Criteria

- A spec produced through the new pipeline for a Unity-class target catches at least one API/pattern the spec author would have assumed without gates (simulated or via eval — actual Unity case is the canonical test).
- `plan-verification.md` lists every plan-named specific with a context7 citation for ✅ rows.
- Block-on-❌ prevents execute from running on an unverified plan in at least one real scenario.
- Override mechanism is auditable — every override has a named approver, a reason, and a timestamp.
- Gates skip cleanly for design/content/small-task projects (no false positives forcing unnecessary research).
- All 5 design risks from §4 have observable closure in the implementation (not just claimed in the spec).
- SKILL.md files stay under 500 lines; procedural depth in references.
- All cross-references between SKILL.md and reference files resolve to actual paths.
- Implementation passes `gigo:verify` both stages (spec compliance + engineering quality).

<!-- approved: spec 2026-04-17T23:05:30Z by:Eaven -->
