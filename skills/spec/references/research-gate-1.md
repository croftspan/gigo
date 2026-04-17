# Gate 1: Pre-Spec Discovery Research

## Purpose

Ground the target runtime / library / SDK surface with live documentation before the spec is written. Catches the "we assumed modern .NET is available" class of failure by forcing a docs lookup at the moment assumptions would otherwise ossify into spec commitments.

Output: `docs/gigo/research/YYYY-MM-DD-<topic>-tech-constraints.md`. Spec Phase 5 and Phase 8 both read this as a hard input.

The gate is independent from the spec author — dispatched as its own subagent with fresh context. Subagents run SEQUENTIALLY (one target at a time). This avoids the append/overwrite race from parallel writes to the same artifact file.

---

## When Gate 1 Fires

Phase 0 trigger detection (see spec R1.2):

1. Read the approved design brief.
2. **If the brief has a `## Platform & Runtime Targets` section:** extract target list (name + version + notes), run Gate 1.
3. **If the brief has `**Targets:** none`:** prompt operator to confirm before skipping:
   > "The brief declares `Targets: none` — this will skip API verification gates. Confirm: is this a pure content/config project with NO shipped code that targets a runtime? [yes, skip gates / no, this ships code — let me name targets]"
4. **If neither:** prompt operator with default-skeptical framing:
   > "This is a code project. What runtime / platform / SDK does it target? Answer `none` only if this is pure content/config with no code output. Otherwise name the target(s) — e.g., `Unity 6 .NET Standard 2.1`, `Node 20 LTS`, `iOS 17 SDK`, `VSCode Extension API 1.85`."

**Small-task handling (spec R1.2a):**
- `**Scale:** small` AND non-code output → skip both gates fully
- `**Scale:** small` AND code output → Gate 1 runs **host-shell detection only**, skipping deep API discovery; Gate 2 still runs on the (small) plan
- `**Scale:** small` ambiguous → ask operator: *"Small task — does it produce any code that ships against a runtime (even one line)? [yes, run host-shell check / no, skip all gates]."*

---

## Depth Calibration

| Depth | Targets |
|---|---|
| `deep` (default for high-risk) | Unity, Unreal, Godot, Bevy, GameMaker; iOS/macOS/Android SDKs; WinUI/WPF; RTOS and microcontroller SDKs; Figma/Chrome/Firefox/VSCode/Obsidian/Blender plugin APIs; managed-runtime hosts (custom/restricted BCL); any target released < 2 years before today |
| `light` | Node 20+ LTS, Python 3.11+, Go 1.22+, Rust stable; React, Vue, Svelte, Next.js (current majors); Django, Rails, FastAPI, Express (current majors); stable cloud SDKs (AWS v3, GCP, Azure) |
| `deep` (unknown) | Default when target doesn't match either list. False-positive cost ~30s; false-negative cost weeks (Unity incident). |

Operator may override depth explicitly at Phase 0.

---

## Host-Shell Checklist (first-class Gate 1 subtask)

| Target family | Required host-shell artifact |
|---|---|
| Unity (any language) | `Assets/` AND `ProjectSettings/` at repo root or declared sub-path |
| .NET general (non-Unity) | `.csproj` or `.sln` |
| Unreal | `.uproject` |
| iOS / macOS | `.xcodeproj`, `.xcworkspace`, or `Package.swift` |
| Android | `build.gradle(.kts)` AND `AndroidManifest.xml` |
| VSCode extension | `package.json` with `engines.vscode` declared |
| Browser extension | `manifest.json` matching MV3 schema |
| Plugin/library with no host | Spec must declare `**External-consumer-only:** true` — else Gate 1 flags |

Missing artifact AND no `external-consumer-only` declaration → write `Host-Shell Requirement: MISSING — [recommendation]` in the artifact.

---

## Dispatch Procedure

1. **Read the brief.** Extract target list and scope notes.
2. **Calibrate depth** per target using the table above. Operator may override.
3. **Assemble per-target prompts.** Use the template variants below. Fill all `{PLACEHOLDERS}`.
4. **Dispatch subagents SEQUENTIALLY** (one at a time, NOT parallel) via `Agent` tool with `subagent_type: "general-purpose"`. First subagent uses `variant-first`; all others use `variant-subsequent`.
5. **Wait for each subagent to complete** before dispatching the next.
6. **Self-review the artifact.** Read the finished file. If any target has `Host-Shell Requirement: MISSING` or `context7 library ID: unresolved`, surface to operator before proceeding to Phase 5.
7. **Spec Phase 5 and Phase 8 read `tech-constraints.md`** as hard input.

---

## Dispatch Prompt Template — Variant-First (creates the artifact)

Fill all `{PLACEHOLDERS}`, then pass as `prompt` argument to `Agent`.

````
You are a research subagent dispatched by gigo:spec Phase 0 (Gate 1). You have fresh context and no stake in the plan being written. Your only job is to ground a specific tech target by fetching live documentation and reporting what the target actually supports.

TARGET: {TARGET_NAME}
VERSION: {TARGET_VERSION}
DEPTH: {DEPTH}  (light = quick surface scan; deep = thorough API/BCL/pattern check)
SCOPE NOTES FROM BRIEF: {SCOPE_NOTES}

ARTIFACT PATH: {ARTIFACT_PATH}
YOUR ROLE: FIRST subagent — CREATE this file (it does not exist yet). Write frontmatter + # heading + your target's section.

SPEC: {SPEC_PATH}
BRIEF: {BRIEF_PATH}
DATE: {DATE}
TOPIC: {TOPIC}
ISO_TIMESTAMP: {ISO_TIMESTAMP}

WORKFLOW (mandatory):

1. Call `mcp__plugin_context7_context7__resolve-library-id` with the target name. Record the resolved ID. If no ID resolves, try up to 2 alternate names (e.g., "Unity 6" → "unity-engine", "unity3d"). Record every attempt.

2. Call `mcp__plugin_context7_context7__query-docs` against the resolved ID. For DEPTH=deep, query multiple facets: runtime/BCL overview; async/concurrency surface; IO and networking APIs; threading/lifecycle; the specific area(s) named in SCOPE NOTES. For DEPTH=light, one overview query is sufficient.

3. If context7 returns nothing useful, fall back to `WebSearch` with official-docs-priority query. Record the source URL and relevant quote.

4. If context7 MCP tools are not available in your environment at all, run in WebSearch-only mode and flag `depth: WebSearch-only` in frontmatter.

5. Extract:
   - Verified APIs / patterns / libraries with exact doc citation
   - Known gaps vs what the brief assumes
   - Integration notes (lifecycle, threading, reload, sandbox, permissions)
   - Host-shell requirement (see HOST-SHELL CHECKLIST below)

6. Write the artifact. CREATE the file (no prior contents). Use the SCHEMA below.

HOST-SHELL CHECKLIST (flag missing):

- Unity → `Assets/` + `ProjectSettings/`
- .NET general → `.csproj` or `.sln`
- Unreal → `.uproject`
- iOS/macOS → `.xcodeproj`, `.xcworkspace`, or `Package.swift`
- Android → `build.gradle(.kts)` + `AndroidManifest.xml`
- Browser extension → `manifest.json` (MV3 schema)
- VSCode extension → `package.json` with `engines.vscode` declared
- Plugin/library with no host → spec must declare `**External-consumer-only:** true`

Missing AND no external-consumer declaration → flag in Host-Shell Requirement with concrete recommendation (add smoke host | declare external-consumer-only | re-scope).

SCHEMA (write this structure VERBATIM — do not improvise):

```markdown
---
spec: {SPEC_PATH}
brief: {BRIEF_PATH}
run-at: {ISO_TIMESTAMP}
subagent: general-purpose
depth: {DEPTH}
targets: [{TARGET_NAME}@{TARGET_VERSION}]
future-coupling: {}
---

# Tech Constraints: {TOPIC}

## Target: {TARGET_NAME} {TARGET_VERSION}

**context7 library ID:** {resolved_id | "unresolved — fallback sources: [urls]"}

### Verified APIs / Patterns

- `Exact.Api.Name(params)` — [verbatim doc citation or quote]
- `Pattern.Name` — [verbatim doc citation]

### Known Gaps vs Brief

- Brief assumes X → target does NOT support X. Evidence: [citation]. Suggested replacement: Y.
- (If no gaps: "No gaps identified at {DEPTH} depth. Plan-level verification (Gate 2) will surface specific-API gaps.")

### Integration Notes

- [lifecycle constraints, threading model, reload behavior, sandbox/permission notes]

### Host-Shell Requirement

- met | MISSING — [recommendation]

---
```

OUTPUT:

After writing the artifact, return a 3-line summary:
1. Did you resolve via context7?
2. What's the headline constraint the spec must respect?
3. Is host-shell OK or flagged?
````

---

## Dispatch Prompt Template — Variant-Subsequent (appends to existing artifact)

Same as variant-first, but replace the "YOUR ROLE" line and "6. Write the artifact" step:

**YOUR ROLE line:**

```
YOUR ROLE: LATER subagent — the artifact file already exists. APPEND a new ## Target: section at the end of the body, AND update the frontmatter `targets:` list to include your target. Do NOT touch frontmatter `run-at`, prior `## Target:` sections, or the `# Tech Constraints:` heading.
```

**Step 6 replacement:**

```
6. Read the existing artifact. Find the frontmatter `targets:` line and append `{TARGET_NAME}@{TARGET_VERSION}` to the list. Append a new `## Target: {TARGET_NAME} {TARGET_VERSION}` section at the end of the body, following the same schema as existing sections. Do NOT modify prior content.
```

---

## Error Handling

| Condition | Response |
|---|---|
| context7 MCP not available at all | Run in WebSearch-only mode; flag `depth: WebSearch-only` in frontmatter. Pipeline degrades visibly. |
| context7 resolve-library-id returns no match | Subagent tries up to 2 alternate names. If still nothing, falls back to WebSearch with official-docs query. Records "context7 unresolved — fell back to WebSearch" in the artifact. |
| Subagent crashes mid-research | Spec Phase 0 retries once with fresh dispatch. Second failure → surface to operator with partial artifact. Don't silently proceed. |
| Ambiguous target ("Unity" without version) | Subagent resolves to latest stable, flags ambiguity in Integration Notes. Operator sees in artifact. |
| Proprietary/internal SDK (context7 can't index) | Subagent records "context7 cannot cover — WebSearch sources: [urls] — CONFIDENCE: LOW". Phase 0 surfaces to operator. |
| Artifact file from earlier spec run exists | Spec Phase 0 MUST prompt operator: *"A research artifact for <topic> already exists (run-at: <timestamp>). Append a run suffix (-r2, -r3...) OR overwrite?"* Never silently overwrite. |
| Concurrent spec runs on same topic+date | Same as above — prompt operator to disambiguate. |

---

## What This Gate Does NOT Do

- **Does not write code.** Only writes to `docs/gigo/research/`.
- **Does not read the plan.** The plan doesn't exist at Phase 0. Gate 2 is the plan-aware gate.
- **Does not verify specific method signatures in plan task code blocks.** That's Gate 2 (post-plan).
- **Does not replace Challenger.** Challenger (6.5/9.5) checks engineering quality; Gate 1 checks platform reality.
