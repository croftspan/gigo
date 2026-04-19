# Changelog

## v0.14.0-beta (2026-04-19)

### Pipeline-Wide Mission-Control Integration

Loose-coupling integration across 4 gigo skills (spec, execute, verify, maintain) when mission-control is available in the session. Detect-and-adapt with install/init nudge — never a hard requirement. Authority principle: mission-control owns ticket state, gigo emits signals via file writes. Repeats none of v0.12's tight-coupling failure; composition test passes (uninstall mc → all 4 skills fall back to v0.13 behavior cleanly).

- **Detection + preference.** New canonical detection helper at `skills/spec/references/mc-detection.md` — three-check (skill list, `command -v mc-init`, `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md`), three-state (UNAVAILABLE / NOT_INITIALIZED / ACTIVE), < 100ms per invocation. Preference file at `.claude/references/mission-control-preference.md` controls nudge behavior (`enabled` / `disabled` / `never-ask`) plus `tiebreak` and `mc-source-path` fields. All 12 state×preference combinations behave per the behavior table.

- **Slice mode in spec.** When mc is STATE_ACTIVE (or operator accepts nudge), Phase 5 produces a PRD foundation + N per-slice design files instead of a monolithic spec. Phase 8 writes one plan per slice. Phase 9.75 runs Gate 2 per-slice plan (Gate 1 still runs once at PRD level). Phase 10 offers batch-or-per-slice approval. After all slice plans approved, spec invokes `/mission-control ticket <plan-path>` per plan to generate tickets in mc's vault. Procedure in new `skills/spec/references/slice-mode.md`.

- **Mc-mode work loop in execute.** Before-Starting gains a new mc-mode detection step. When `mc_active` AND `vault/tickets/` has tickets, execute enters the ticket loop: query `mc-ticket-status --json` for `unblocked` array (minimal `{id, title}` objects), read full ticket body from `vault/tickets/{ticket-id}.md` (mandatory — minimal JSON is NOT treated as sufficient context), emit pickup signal to `vault/agents/logs/{ticket-id}-execute-pickup.md`, dispatch worker with full ticket context, run `mc-proof-of-work` and gigo:verify on DONE, emit completion/blocked signals per worker result. Execute NEVER mutates ticket frontmatter.

- **Two-pass crash recovery in execute.** Pass A scans signal files (within 30-day mc-scrub window) for pickup signals without matching completion signals. Pass B queries `mc-ticket-status --json` for `in_progress` tickets without matching current pickup signals (catches interruptions before scrub or by other executors). Honest non-claim: mission-control currently has no automatic stale-`in_progress` detection — operators needing it must run `mc-ticket-status --json` manually or rely on execute's startup audit on resume.

- **Per-stage + canonical combined verdicts in verify.** When mc is active AND ticket ID is resolvable (priority: `--ticket` flag → recent execute-pickup signal → operator input → fallback to v0.13), verify writes 3 verdict files per ticket: `{ticket-id}-spec-compliance.md` and `{ticket-id}-craft-quality.md` in gigo's structured YAML frontmatter schema (R5.4.a), plus the canonical combined `{ticket-id}.md` in mc's **plain-header format** (R5.4.b) — structurally matching `mission-control/skills/mission-control/references/reviewer-verdict.md` so downstream mc tools (`mc-ticket-stats`, `mc-dashboard`, `mc-retro`, all present in `mission-control/bin/`) parse gigo-written verdicts correctly. The `Reviewer:` field carries `gigo:verify` (not mc's `mission-control:review`) — consumers display who actually wrote the verdict; mc's parsers are value-agnostic on that field. Combined-status synthesis: any Critical issue (≥90 confidence) in Stage 2 → `escalate`; otherwise `approved_with_notes`.

- **Add Mission-Control mode in maintain.** New auto-detected mode retrofits mc onto existing projects. Triggered by explicit `add-mission-control` argument OR auto-suggested when no preference file exists and mc state is NOT_INITIALIZED / UNAVAILABLE. Per-state behavior: ACTIVE reports status only (vault audit deferred to v2); NOT_INITIALIZED runs the shared Mc-Init Invocation Procedure; UNAVAILABLE resolves the mc source path then runs install.sh + the procedure. Procedure in new `skills/maintain/references/add-mission-control.md`.

- **Mc-Init Invocation Procedure (R3.1.a).** Shared subroutine in `skills/spec/references/mc-detection.md`. Handles three vault states: vault absent → plain `mc-init`; vault exists without tickets → `mc-init --force` with announcement; vault exists WITH ≥1 ticket → ABORT with a three-option message (vault-is-usable / manual-rebuild preserving tickets / back-up-and-fresh-start). The ABORT path is load-bearing safety: mc's `mc-init --force` calls `shutil.rmtree(vault)` (verified at `mission-control/bin/mc-init` line 288), which would delete all tickets, logs, and verdicts. On abort, falls back to monolithic mode without writing a preference file — operator re-runs after choosing an option. Closes the retrofit-safety gap on projects with legacy vaults.

- **Configurable mc source path.** No `~/projects/mission-control/` path is hardcoded. `resolve_mc_source_path()` helper (documented in `mc-detection.md`) checks `GIGO_MC_SOURCE` env var → preference field `mc-source-path` → default `~/projects/mission-control/`. Clone-instructions error when resolution fails shows all three options to the operator.

- **Blueprint unchanged.** v1 defers slicing-hint in blueprint — spec detects scope from brief content (≥3 distinct components, "vertical slice" language). Keeps v1 surface smaller; blueprint remains monolithic.

### Fact-check findings noted (from spec Phase 4.25)

- `mc-ticket-status --json` emits `{id, title}` per ticket (NOT rich objects with body) — execute MUST read `vault/tickets/{ticket-id}.md` for full context before worker dispatch.
- `install.sh` is non-interactive (sets `set -euo pipefail`, symlinks bin/ + skill, exits cleanly) — gigo invokes directly via Bash, no operator intervention needed when source repo is cloned.
- `mc-scrub` (default 30 days) deletes files in `vault/agents/logs/` — constrains signal-file crash recovery to 30-day window; Pass B covers beyond that.
- Pass B crash recovery uses `mc-ticket-ls --status in_progress --json` (verified in `mission-control/bin/mc-ticket-ls` lines 35/43) — `mc-ticket-status --json` returns `by_status` as a count dict, not an enumerable ticket list.

### Design references

- Spec: `docs/gigo/specs/2026-04-18-pipeline-wide-mission-control-integration-design.md`
- Plan: `docs/gigo/plans/2026-04-18-pipeline-wide-mission-control-integration.md`
- Motivating brief: `briefs/12-mission-control-slice-integration.md`
- Loose-coupling principle memory: `feedback_skill_integration_loose_coupling.md`

## v0.13.0-beta (2026-04-17)

### Two-Gate context7 Research Pipeline

Pipeline-wide safeguard against specs and plans that assume APIs the target runtime doesn't actually have. Triggered by a 2026-04-17 incident where a Unity package shipped weeks of Editor C# against .NET 5+ APIs (`Process.WaitForExitAsync`, `Task.WaitAsync(CancellationToken)`, `SHA256.ComputeHashAsync`, ~20 others) missing from Unity 6's .NET Standard 2.1 BCL. The package was uninstallable; 1820 vitest tests covered only the TypeScript sidecar, so the compile-surface mismatch went unnoticed for weeks.

- **Gate 1 — Pre-Spec Research** (new spec Phase 0). Before the spec is written, an independent subagent grounds the target runtime's API surface via `context7` MCP (`resolve-library-id` → `query-docs`). Output: `docs/gigo/research/YYYY-MM-DD-<topic>-tech-constraints.md`. Spec Phase 5 (Write Spec) and Phase 8 (Write Plan) both read this as a hard input. Procedure in new `skills/spec/references/research-gate-1.md` (211 lines) — includes depth calibration heuristic (deep default for Unity/Unreal/iOS/Android/embedded/plugin APIs; light for Node/Python/stable web stacks), first-class host-shell checklist (flags missing `Assets/`+`ProjectSettings/` for Unity, `.xcodeproj` for iOS, etc.), sequential dispatch (avoids parallel-write race), and verbatim variant-first / variant-subsequent subagent prompt templates.

- **Gate 2 — Post-Plan Adversarial Verification** (new spec Phase 9.75). After the plan is finalized (post-9.5 Challenger), an independent verification subagent runs with fresh context and via-negativa framing: *"Assume this plan is wrong. Find every API, method, library, or pattern it names and prove each one exists in [target] by citing context7 docs. ✅ requires a verbatim citation; 'looks right' is ❌. You are not helping the plan succeed; you are finding what's broken before it ships."* Output: `docs/gigo/research/YYYY-MM-DD-<topic>-plan-verification.md` — append-only `## Run N` sections preserve audit trail across re-runs. Procedure in new `skills/spec/references/research-gate-2.md` (268 lines). Reflexion pattern (Shinn et al.) applied as dispatch-time constraint; independence from the spec author, Gate 1 subagent, and Challenger subagent is non-negotiable.

- **Block-on-❌ enforcement** at `gigo:execute` startup. Execute's Before-Starting gains a new step that resolves the plan-verification artifact via frontmatter `plan:` field (canonical absolute-path comparison — filename matching is not trusted), finds the latest `## Run N` section, computes effective status from the body (not the frontmatter `status:` — advisory only). `pass` → proceed. `needs-override` → announce gap count, proceed. `fail` → refuse to dispatch and list unresolved ❌ rows inline. MALFORMED-ARTIFACT, MALFORMED-OVERRIDE, and DUPLICATE-OVERRIDE cases all surfaced in refusal messages so operators see near-miss overrides, not silent bypass.

- **Body-as-truth authority model.** Gate 2's `plan-verification.md` artifact uses the body as the source of truth for effective status. Frontmatter `status:` is advisory — written once by the subagent on first pass, never mutated after. Consumers (execute, spec Phase 10) derive effective status from body on every read using the canonical Derived Status Calculation algorithm: count ❌ rows in the latest run's `### Findings`, count valid override markers in `### Overrides (Run N)` matching the regex `^<!-- override: finding-(\d+) reason:(.+?) approved-by:(.+?) timestamp:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) -->$`. This closes the "who updates frontmatter after overrides are added" mutation-cycle problem.

- **Append-only per-run structure** for `plan-verification.md`. Re-runs (plan revisions, explicit operator re-run) APPEND a new `## Run N` section — do NOT overwrite prior runs. Finding numbers are per-run; prior overrides preserved on disk but do not apply to new runs (operator re-adds against new finding numbers). Audit trail survives re-runs mechanically, not via git-commit discipline. 10-row Test Matrix in `research-gate-2.md` documents consumer-side derivation behavior for every edge case.

- **Override mechanism.** Inline marker in the run's `### Overrides (Run N)` sub-section: `<!-- override: finding-N reason:<reason> approved-by:<username> timestamp:<ISO-8601> -->`. Auditable (named approver, reason, timestamp per override), consistent with existing approval-marker pattern. Malformed markers are flagged to operators, not silently ignored.

- **Trigger scope.** Runs only for code projects with named runtime/platform/SDK/library targets. Detection: spec Phase 0 reads the design brief's `## Platform & Runtime Targets` section. If absent, checks for explicit `**Targets:** none` declaration (prompts for confirmation before skipping). If neither, default-skeptical fallback: *"This is a code project. What runtime / platform / SDK does it target? Answer `none` only if this is pure content/config with no code output."* Small-task handling: pure non-code tasks skip fully; code-producing small tasks STILL run host-shell detection (the 30-second cheap piece of Gate 1) — closes the Unity-incident bypass path.

- **Blueprint Phase 4 — Platform & Runtime Targets capture.** Blueprint now captures a `## Platform & Runtime Targets` section in the design brief when applicable (Unity, Unreal, iOS/Android SDKs, VSCode/browser extensions, embedded runtimes, managed-runtime hosts). Includes target name+version, BCL/language surface notes, consuming host project shell requirements, runtime constraints. New Phase 4 self-check forces blueprint to either include the section OR add explicit `**Targets:** none` declaration before Post-Approval — first line of defense against blueprint misclassification.

- **Graceful degradation when context7 MCP is unavailable.** Gate 1 runs in WebSearch-only mode with `depth: WebSearch-only` flagged in frontmatter. Gate 2 defaults context7-requiring items to ❌, operator can override with WebSearch citations. Pipeline degrades visibly, not silently.

### Design references

- Spec: `docs/gigo/specs/2026-04-17-two-gate-context7-research-pipeline-design.md`
- Plan: `docs/gigo/plans/2026-04-17-two-gate-context7-research-pipeline.md`
- Motivating memory: `feedback_blueprint_spec_platform_verification.md`, `project_research_gate_blueprint_to_spec.md`

## v0.11.0-beta (2026-03-31)

### New Skills

- **`/spec`** — Formalizes approved design briefs into specs and implementation plans. Absorbs Phases 5-10 from blueprint. Self-review, Challenger for large tasks, operator approval at each gate.
- **`/sweep`** — Deep code audit dispatching 3 parallel focused auditors (security, stubs, code quality). Works standalone or offered after execute completes.

### Pipeline Changes

- **Blueprint stripped to design brief only.** Phases 5-11 removed. Blueprint now ends at the approved design brief and hands off to `/spec`.
- **Intent fidelity.** Three fixes: verb-listing before design (blueprint Phase 3), intent anchor with verb trace in every spec (spec Phase 5), Challenger hard stop on intent mismatch (spec Phase 6.5).
- **Auto-changelog.** Execute auto-generates a changelog entry after all tasks complete, grounded in the approved spec and actual git diff.
- **Handoff chain.** Each skill saves its artifact then offers to invoke the next: `/blueprint` → `/spec` → `/execute` → `/verify` or `/sweep`.
- **Assembly flow.** Task description now optional during assembly — team composed for the project domain, not a specific task.
- **Verbosity control.** `.claude/references/verbosity.md` with minimal/verbose levels. Default minimal. Asked during assembly. All pipeline skills check it.
- **Compact at handoff.** Conversation compacted between skill invocations to shed prior context. Artifact on disk is the durable record.

### Documentation

- Skill count updated from 7 to 9 across CLAUDE.md and pipeline architecture reference.
- Gigo handoff table updated with all 9 skills.

## v0.10.0-beta (2026-03-31)

### Breaking Changes

- **Team routing OFF by default.** Personas still in CLAUDE.md and influence behavior, but explicit per-response routing is now opt-in (`team on`). Existing projects keep their current state — only new assemblies default to inactive.

### Improvements

- **Blueprint proportionality.** SKILL.md cut from 303 to 182 lines. Phases 5-10 procedural details moved to on-demand reference file. Less context loaded per blueprint run.
- **Challenger scaling.** Adversarial reviews now run for large tasks only. Small and medium tasks use self-review. Operator can always request a Challenger.
- **Fact-checker scaling.** Phase 4.25 only runs for existing codebases. Greenfield projects skip it — nothing meaningful to check against.
- **Assembly speed.** Training knowledge is the default. Web search only for genuinely unfamiliar domains or when the operator requests deep research. Saves ~10 minutes on assembly.
- **Troubleshooting docs.** Added troubleshooting section to getting-started page and `docs/troubleshooting.md` for tracking known issues.

### Bug Fixes

- **Marketplace version sync.** `marketplace.json` was stuck at 6.0.0 while `plugin.json` had 0.9.9-beta, causing users to get stale versions on install.
- **Site footer versions.** All 9 site pages updated from stale v7.6.0.

## v0.9.9-beta (2026-03-30)

### Bug Fixes

- **Marketplace version sync.** Fixed version mismatch between marketplace.json and plugin.json.

## v0.9.8-beta (2026-03-30)

### New Features

- **Post-assembly handoff (Step 7).** After `gigo:gigo` finishes, users see a command table, a clear next step (`/blueprint`), and a synthesized starter prompt built from the assembly conversation. No more staring at a finished setup with no idea what to do next.
- **Persona style preference.** During assembly, operators choose Characters (named personas with personality and voice) or Lenses (functional descriptors, silent operation). Saved to `.claude/references/persona-style.md`. Default: Lenses.

### Bug Fixes

- **Install command.** Fixed `claude marketplace add` to `claude plugin marketplace add` across README and all site pages.
- **Persona style pipeline coherence.** 6 issues found by `gigo:verify` and fixed via `gigo:blueprint`: downstream skills now read persona-style.md, default contradiction resolved, accidental Overwatch rename reverted, Personality table respects style, `/team off/on` separated from slash commands, files written summary updated.

### Improvements

- **Naming conventions.** Better persona name examples. "The Voice" and "The Oracle" explicitly called out as bad names. The Overwatch stays — it's a system component, not a domain persona.
- **Snap template check 14.** Persona style consistency audit for new projects.
- **Blueprint check in workflow.** Step 2 of The Loop now nudges toward blueprint before writing when design decisions are involved.

## v0.9.7-beta (2026-03-30)

### Improvements

- **Team routing.** Every assembled project gets automatic persona routing. Toggle with "team on"/"team off" in conversation. Woven into workflow, snap template, persona template, and output structure.

## v0.9.6-beta (2026-03-30)

### Bug Fixes

- Removed duplicate rot story from Stays Lean sections.
- Fixed Senior+ stat label, direct claim instead of anonymous authority framing.
