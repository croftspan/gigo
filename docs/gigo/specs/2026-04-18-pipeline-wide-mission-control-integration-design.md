# Pipeline-Wide Mission-Control Integration — Design Spec

**Design brief:** `.claude/plans/crystalline-crunching-aurora.md`

## Original Request

> I want to add pipeline-wide mission-control integration to GIGO — the loosely-coupled "detect-and-adapt with install/init nudge" pattern that lets gigo compose with mission-control without becoming dependent on it. Triggered by an emergent observation: when mission-control is in-session, gigo:spec already produces beautiful slice-based specs (PRD foundation + numbered vertical slices ready for ticket breakdown). Without mission-control, no user discovers this is possible. Decided shape: detect-and-adapt with install/init nudge across spec, execute, verify, maintain, blueprint; three states (mc unavailable + project not initialized | mc available + project not initialized (retrofit) | mc available + project initialized (slice mode)); authority principle (mission-control OWNS ticket state; gigo skills EMIT signals — no imports, no SDK calls, artifact-based interface); single comprehensive brief (umbrella scope), NOT incremental; v0.12 archive at `archive/v0.12-development` is the cautionary example. Full context, decided constraints, all 5 touchpoints, open questions, success criteria, non-goals are in `briefs/12-mission-control-slice-integration.md`. Mission-control is markdown/skill ecosystem (no managed-runtime BCL surface). Platform & Runtime Targets: GIGO plugin source, mission-control plugin source, Claude Code Plugin API surface.

---

## Overview

Add pipeline-wide mission-control awareness to 4 gigo skills (spec, execute, verify, maintain) without creating any hard dependency on mission-control. Mission-control's existing public interface — Claude skill subcommands (`/mission-control init`, `/mission-control ticket`, `/mission-control review`), bin scripts (`mc-init`, `mc-ticket-status`, `mc-proof-of-work`, `mc-validate-dag`, `mc-ticket-new`), and convention paths under `vault/` — IS the integration interface. Gigo invokes by name, never by import.

The integration adds three behavioral states across all 4 touchpoints (UNAVAILABLE / NOT_INITIALIZED / ACTIVE), backed by a project-local preference file (`.claude/references/mission-control-preference.md`) that the operator can use to suppress nudges.

Authority principle (load-bearing): mission-control owns ticket state; gigo emits signals via file writes at convention paths and via subcommand invocation. Gigo never mutates ticket frontmatter.

Composition test (canonical): if mission-control is uninstalled entirely, all 4 affected gigo skills must fall back to v0.11/v0.13 behavior with zero errors.

---

## 1. Requirements

### R1: Detection Helper (shared by 4 skills)

**R1.1** Create `skills/spec/references/mc-detection.md` containing the canonical detection logic, preference schema, three-state table, and a "when to read this" pointer-style for each consuming skill. spec/execute/verify/maintain SKILL.md files all reference this single file (DRY).

**R1.2** Three-check detection:

| Check | Mechanism | Cost |
|---|---|---|
| Skill availability | `"mission-control"` present in session's available skills list | < 1ms (in-process lookup) |
| Bin script availability | `command -v mc-init` returns success (exit 0) | < 50ms (Bash call) |
| Project initialized | `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` exists | < 10ms (filesystem stat) |

**R1.3** Effective state derivation:
- `mc_available = skill_available AND mc_init_available`
- `mc_active = mc_available AND project_initialized`

**R1.4** Three states:
- **STATE_UNAVAILABLE** (`mc_available == false`) — mc not installed at session level
- **STATE_NOT_INITIALIZED** (`mc_available && !project_initialized`) — mc installed but project not yet scaffolded
- **STATE_ACTIVE** (`mc_active == true`) — mc installed AND project scaffolded

**R1.5** Detection runs per-invocation (no session caching). Total cost < 100ms.

### R2: Preference Storage

**R2.1** Preference file at `.claude/references/mission-control-preference.md` with YAML frontmatter:

```markdown
---
mc-integration: enabled | disabled | never-ask
last-asked: <ISO-8601 UTC timestamp>
last-state-when-asked: STATE_UNAVAILABLE | STATE_NOT_INITIALIZED
tiebreak: tickets | plan | sequential   # set by execute when both vault/tickets/ AND plan.md exist; absent before first prompt
---

# Mission-Control Integration Preference

This file stores the operator's decision about mission-control nudges in this project.

- `mc-integration: enabled` → gigo prompts to install/init when mc is missing or not initialized
- `mc-integration: disabled` → gigo never prompts AND does not use mc-aware mode even if active (escape hatch)
- `mc-integration: never-ask` → gigo silently uses v0.13 fallback when mc is missing or not initialized; uses mc-aware mode if state is ACTIVE
- `tiebreak` → tells execute which source of truth to follow when both tickets and plan.md exist
```

**R2.2** Behavior table:

| `mc-integration` | State | Action |
|---|---|---|
| (file missing) | UNAVAILABLE | Prompt to install+init (per R3.1) |
| (file missing) | NOT_INITIALIZED | Prompt to init (per R3.1) |
| (file missing) | ACTIVE | mc-aware mode silently |
| `enabled` | UNAVAILABLE | Prompt (operator wants mc) |
| `enabled` | NOT_INITIALIZED | Prompt (operator wants mc) |
| `enabled` | ACTIVE | mc-aware mode silently |
| `never-ask` | UNAVAILABLE | v0.13 fallback silently (no prompt) |
| `never-ask` | NOT_INITIALIZED | v0.13 fallback silently |
| `never-ask` | ACTIVE | mc-aware mode silently (override doesn't suppress active state) |
| `disabled` | UNAVAILABLE | v0.13 fallback silently |
| `disabled` | NOT_INITIALIZED | v0.13 fallback silently |
| `disabled` | ACTIVE | v0.13 fallback silently (escape hatch — operator opted out post-init) |

**R2.3** Preference file is project-local (`.claude/` directory). NEVER global. Each project decides independently.

### R3: Spec Touchpoint

**R3.1** New mc-mode branch in spec Phase 5, after Phase 0 (Gate 1) completes and before drafting the spec. Reads detection (R1), reads preference (R2), applies behavior table:

- **STATE_ACTIVE** → enter slice mode (R3.2)
- **STATE_NOT_INITIALIZED + (default | enabled)** → prompt: *"mission-control is installed but hasn't been set up in this project. Running its init will extract governance, create the vault, and enable slice-based specs ready for ticket breakdown. Run init now? [init / skip / never ask again for this project]"*. On `init` → run the **mc-init invocation procedure** (R3.1.a). On `skip` → monolithic mode for this run, write `last-asked` to preference file. On `never ask again` → write `mc-integration: never-ask` to preference file, monolithic mode.

**R3.1.a Mc-init invocation procedure** (shared by R3.1 STATE_NOT_INITIALIZED, R3.1 STATE_UNAVAILABLE post-install, and R6.2 NOT_INITIALIZED paths):

1. **Pre-flight: vault existence check.** Test whether `$CLAUDE_PROJECT_DIR/vault/` already exists. STATE_NOT_INITIALIZED is defined by absence of `vault/_schema/ticket.md`, but a partially-initialized `vault/` directory (from a half-completed prior init, a manual mkdir, or a stale v0.12 attempt) can exist without that file.
2. **Branch on vault state:**
   - **Vault absent:** invoke `mc-init $CLAUDE_PROJECT_DIR` via Bash. Success → proceed to step 3.
   - **Vault exists but no `TCK-*.md` tickets inside `vault/tickets/`:** invoke `mc-init $CLAUDE_PROJECT_DIR --force`. (Overwrites scaffolding but no ticket work is at risk.) Announce to operator: *"Existing vault/ directory found (no tickets inside). Running `mc-init --force` to complete scaffolding."*
   - **Vault exists WITH `TCK-*.md` tickets:** PROMPT operator: *"Existing vault/ directory contains N tickets. Running mc-init will overwrite scaffolding templates (`_schema/`, `runbooks/`, governance) but preserve your tickets. Proceed? [proceed / abort]"*. On `proceed` → invoke `mc-init $CLAUDE_PROJECT_DIR --force --yes`. On `abort` → fall back to monolithic mode, do NOT write preference file (re-ask next time).
3. **Invoke `/mission-control init` skill** via Skill tool. Mc's own init extracts governance from `.claude/rules/standards.md` (if present) → `vault/_governance/PROJECT_RULES.md`, and idempotently augments `CLAUDE.md` between `<!-- mission-control:begin -->` markers.
4. **Verification:** confirm `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` now exists (STATE transitions to ACTIVE). If still missing, report mc-init failure to operator, fall back to monolithic mode, do NOT write preference (`never-ask`).
5. **Preference update:** if init succeeded and preference file doesn't exist yet, write `mc-integration: enabled`.

If mc-init exits non-zero at any step, surface the stderr output to the operator verbatim and fall back to monolithic mode — do not hide mc failures.
- **STATE_UNAVAILABLE + (default | enabled)** → prompt: *"mission-control isn't installed. It pairs with gigo to produce slice-based specs ready for ticket breakdown — generally much higher quality output. Want to install and init it in this project? [install+init / skip / never ask again for this project]"*. On `install+init` → resolve mc source path per R-ADV (configurable `~/projects/mission-control/` default), check `{mc-source}/install.sh` exists; if yes, invoke via Bash (non-interactive: sets `set -euo pipefail`, symlinks bin/ and skill, exits cleanly), then run the **mc-init invocation procedure** (R3.1.a). If `{mc-source}/` doesn't exist, surface clone instructions to operator with the mc repo URL — operator action required. On `skip` / `never ask again` → same as above.
- All other state+preference combinations → silent fallback to v0.13 monolithic mode (no prompts).

**R3.2** Slice mode output contract (gigo-owned format):

When in slice mode, spec produces:
- `docs/gigo/specs/{date}-{topic}-prd-foundation-design.md` — PRD-level overview that names all slices, their order, and their interfaces. Includes Original Request, full Verb Trace, Conventions section, references to each slice file.
- `docs/gigo/specs/{date}-{topic}-slice-{N}-{name}-design.md` — one per vertical slice. Each is a complete spec for that slice (Original Request scoped to slice, Verb Trace per slice, Conventions, Acceptance Criteria) — bare-worker sufficient.

**R3.3** Each slice file gets its own `<!-- approved: spec [timestamp] by:[username] -->` marker via Phase 7. The PRD foundation also gets one. Operator may approve all slices in a single batch ("approve all PRD + slices") with explicit per-slice review available on request — Phase 7 prompt offers both.

**R3.4** Plan generation in slice mode (Phase 8 extension): spec writes ONE plan file per slice at `docs/gigo/plans/{date}-slice-{N}-{name}.md`. Each plan gets its own `<!-- approved: plan [timestamp] by:[username] -->` marker via Phase 10. Same batch-approval option.

**R3.5** Mission-control ticket trigger (after all slice plans approved): spec invokes the `mission-control` skill via Skill tool: `/mission-control ticket <plan-path>` for each approved slice plan, in order. Mission-control runs its own DAG validation, creates `vault/tickets/TCK-{phase}-{seq}.md` files, reports status. Spec presents the consolidated ticket-creation report to operator.

**R3.6** Phase 9.75 (Gate 2) interaction in slice mode: Gate 2 runs **per-slice plan** (not per-PRD). Each slice's plan gets its own `docs/gigo/research/{date}-slice-{N}-{name}-plan-verification.md`. Gate 1 still runs once at Phase 0 (PRD-level) — runtime targets don't vary per slice. (This requires v0.13's spec/SKILL.md as the base; v0.13 already has Phase 0 and Phase 9.75.)

**R3.7** Monolithic mode (STATE_UNAVAILABLE/NOT_INITIALIZED with `never-ask` / `disabled`, or operator declined nudge) is exactly v0.13 spec behavior — no changes.

### R4: Execute Touchpoint

**R4.1** New mc-mode detection at `gigo:execute` startup. Insert AFTER existing v0.13 step 2 (plan-verification check) and BEFORE existing step 3 (read full plan). Renumber existing steps 3→4, 4→5.

**R4.2** New step content:

```markdown
3. **Mission-control mode detection.** Run mc detection (per `skills/spec/references/mc-detection.md`).
   - If `mc_active` AND `$CLAUDE_PROJECT_DIR/vault/tickets/` contains ≥1 ticket file (`TCK-*.md`) → enter mc-mode (skip plan.md path; proceed to mc-mode work loop in Tier section).
   - If `mc_active` AND `vault/tickets/` is empty → fall back to plan.md path (operator hasn't generated tickets yet).
   - If NOT `mc_active` → existing plan.md path.
```

**R4.3** Mc-mode work loop (added as a new section after existing Tier 1/2/3 sections):

```
while True:
  # --- Step 1: Ask mc what's ready (lightweight, IDs + titles only) ---
  status_json = bash("mc-ticket-status --json")
  # Verified schema (from mission-control/bin/mc-ticket-status):
  #   {"total": N, "by_status": {...},
  #    "unblocked": [{"id": "TCK-X-NNN", "title": "..."}],
  #    "blocked": [{"id": ..., "title": ..., "unmet": [dep_ids]}]}
  # NOTE: objects in unblocked/blocked are intentionally minimal.
  # They do NOT contain body, acceptance tests, implementation notes, produced_files, etc.
  ready = status_json["unblocked"]
  if len(ready) == 0:
    break  # all tickets done OR all remaining are blocked

  ticket_id = ready[0]["id"]  # mc enforces DAG order; first-listed is correct

  # --- Step 2: Fetch full ticket body from disk ---
  ticket_path = Path(CLAUDE_PROJECT_DIR) / "vault" / "tickets" / f"{ticket_id}.md"
  if not ticket_path.exists():
    # mc-ticket-status listed a ticket that's missing from disk — defensive error
    raise RuntimeError(f"mc-ticket-status reported {ticket_id} ready but {ticket_path} missing")
  ticket_content = ticket_path.read_text()  # full frontmatter + body
  # Parse frontmatter for: title, exit_criteria, produced_files, acceptance_tests, depends_on
  # Body sections needed by worker: Summary, Context, Implementation Notes, Acceptance Tests
  ticket_fm, ticket_body = parse_frontmatter(ticket_content)

  # --- Step 3: Signal pickup ---
  emit_signal(f"vault/agents/logs/{ticket_id}-execute-pickup.md")
  # Signal contents: ISO-8601 timestamp, gigo:execute version, lead session id

  # --- Step 4: Dispatch worker with full ticket context ---
  worker_prompt = build_worker_prompt(
    ticket_id=ticket_id,
    ticket_title=ticket_fm["title"],
    ticket_body=ticket_body,
    exit_criteria=ticket_fm.get("exit_criteria", []),
    produced_files=ticket_fm.get("produced_files", []),
    acceptance_tests_section=extract_section(ticket_body, "Acceptance Tests"),
    implementation_notes_section=extract_section(ticket_body, "Implementation Notes"),
  )
  # Worker prompt is self-contained — worker reads the prompt, not the ticket file
  # (matches gigo:execute v0.13 pattern: "Never make workers read the plan file")
  worker_status = dispatch_worker(worker_prompt)
  # Worker reports DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT

  # --- Step 5: Handle worker result ---
  if worker_status == "DONE":
    bash(f"mc-proof-of-work {ticket_id}")  # captures test_output, lint_output to ticket frontmatter
    invoke_verify(ticket_id)               # gigo:verify in mc-mode (per R5)
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-complete.md")
    # Operator transitions ticket status to `done` after seeing verdicts (per mc's autonomy bound)
  elif worker_status in ["BLOCKED", "NEEDS_CONTEXT"]:
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-blocked.md")
    # Signal contents: worker's status report so operator/mc has context
    # Execute does NOT mutate ticket state (mc autonomy rule)
    # Surface to operator; operator decides ticket state transition
  elif worker_status == "DONE_WITH_CONCERNS":
    # Same as DONE but include concerns in execute-complete signal
    bash(f"mc-proof-of-work {ticket_id}")
    invoke_verify(ticket_id)
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-complete.md", concerns=worker_concerns)
```

**Ticket-body read is mandatory** — do not treat `{id, title}` from `mc-ticket-status` as sufficient context. Every worker dispatch reads `vault/tickets/{ticket-id}.md` from disk first.

**R4.4** Per-ticket scope: one ticket at a time in v1. Parallel execution deferred to v2 (requires worktree-per-ticket coordination + DAG-aware dispatch).

**R4.5** Mid-work failures: execute does NOT write to ticket frontmatter. All state changes propagate via signal files at `vault/agents/logs/`. Operator (or mc's own audit) decides ticket state transitions.

**R4.6** Crash recovery (two-pass audit on startup):

- **Pass A (signal-file based, 30-day window):** scan `vault/agents/logs/` for `{ticket-id}-execute-pickup.md` files WITHOUT a corresponding `{ticket-id}-execute-complete.md`. These are tickets execute was working on when it crashed.
- **Pass B (ticket-status based, always runs):** query `mc-ticket-status --json`, enumerate `by_status.in_progress` tickets. For each, check whether a corresponding pickup signal exists in the current `vault/agents/logs/` listing. If NOT (possible if mc-scrub removed signals, or a prior execute run in a different session started the ticket), include the ticket in the recovery report with a different annotation.

Combined recovery output uses the §Conventions error message format. Execute presents the list to the operator: re-pick or escalate. Execute does NOT mutate ticket state (R4.5).

**R4.7** Signal file lifetime + crash recovery (documented limitation):

`vault/agents/logs/` is also where mc's `mc-scrub` script (default `--days 30`) deletes files older than 30 days. This constrains how far back execute's signal-file-presence crash detection (R4.6) can look.

**Within 30 days:** execute's startup audit works as specified in R4.6 — scan `vault/agents/logs/` for `{ticket-id}-execute-pickup.md` files without matching `{ticket-id}-execute-complete.md` files.

**Beyond 30 days (or when signal files have been scrubbed):** execute's startup audit adds a second pass — query `mc-ticket-status --json`, examine every ticket in `by_status.in_progress`, cross-reference against the session's logs. Any `in_progress` ticket with no corresponding pickup signal in the current logs directory is reported to the operator as: *"Ticket {id} is `in_progress` but has no active gigo:execute pickup signal. It may have been interrupted before scrub or by another executor. Inspect manually: `mc-ticket-show {id}`."* Execute does NOT mutate the ticket's state (mc autonomy rule, R4.5); it only reports.

**Explicit non-claim:** mission-control as of current HEAD does not provide automatic stale-`in_progress` detection. Operators needing that behavior must run `mc-ticket-status --json` manually (or this startup audit on resume). Document this in `skills/execute/` reference. If mc later ships such detection, v2 of this integration can leverage it.

**R4.8** Plan.md coexistence: if `vault/tickets/` (≥1 ticket) AND `docs/gigo/plans/{plan}.md` (with approval marker) both exist, prompt operator on first invocation per project: *"This project has both a plan file and mission-control tickets. Which is the source of truth for this run? [tickets / plan / both (run plan tasks first, then tickets)]"*. Store decision in preference file as `tiebreak: tickets | plan | sequential`.

**R4.9** Auto-changelog in mc-mode: generate per-ticket changelog entries (one per ticket completed in this run) AND a final summary entry. Read `vault/tickets/` to find what was completed since execution started.

**R4.10** Fallback (no mc): existing v0.13 behavior — no changes.

### R5: Verify Touchpoint

**R5.1** New mc-mode detection at verify start. If `mc_active` AND a ticket ID is provided/detectable → mc-mode. Otherwise → v0.13 mode.

**R5.2** Ticket ID resolution priority:
1. Explicit flag: `gigo:verify --ticket TCK-X-NNN`
2. Most recent `vault/agents/logs/{ticket-id}-execute-pickup.md` (if execute just ran in this session)
3. Operator-provided in conversation (verify asks if not resolvable from 1 or 2)
4. Fall back to v0.13 mode if none resolvable

**R5.3** Verdict artifact paths (extends mc's existing single-verdict convention with stage suffix):
- Stage 1 (spec compliance): `vault/agents/reviewer/{ticket-id}-spec-compliance.md`
- Stage 2 (craft quality): `vault/agents/reviewer/{ticket-id}-craft-quality.md`
- Final combined: `vault/agents/reviewer/{ticket-id}.md` (mc's canonical path) — synthesized after both stages complete

**R5.4** Verdict schemas — **two distinct formats** depending on file:

**R5.4.a — Stage-suffixed files (gigo-owned, structured for programmatic consumption):**

Paths: `vault/agents/reviewer/{ticket-id}-spec-compliance.md` and `vault/agents/reviewer/{ticket-id}-craft-quality.md`. Only gigo:verify writes these. Format:

```markdown
---
type: reviewer-verdict
ticket: TCK-X-NNN
stage: spec-compliance | craft-quality
status: approved | approved_with_notes | escalate
reviewer: gigo:verify (subagent: general-purpose)
timestamp: <ISO-8601 UTC>
findings_count: <integer>
---

# Stage Verdict: {ticket-id} — {stage}

## Summary
[1-3 sentence summary of the verdict outcome]

## Findings
- [finding 1 with location reference]
- [finding 2]
(If no findings: "No findings.")

## Exit-Criteria Checklist
- [ ] {criterion verbatim from ticket frontmatter `exit_criteria`}: [met | not-met | n/a]
- ... (one entry per exit_criterion)

## Rule-Adherence Notes
[Notes against `vault/_governance/PROJECT_RULES.md` if mc has extracted rules; otherwise "No governance rules to check against."]
```

**R5.4.b — Canonical combined file (mc-compatible plain-header format, mc's own schema):**

Path: `vault/agents/reviewer/{ticket-id}.md`. Exact format mc's `mission-control:review` writes today (verified from `mission-control/skills/mission-control/references/reviewer-verdict.md`). Tools downstream of mc (mc-ticket-stats, mc-dashboard, mc-retro) parse this format by regex; gigo must not drift from it.

```markdown
# Reviewer Verdict — {ticket-id}

**Status:** approved | approved_with_notes | escalate
**Reviewer:** gigo:verify
**Timestamp:** {ISO-8601}
**Ticket:** {title — read from ticket frontmatter}

## Summary

One paragraph. What was built, how it was verified, the overall call. Synthesized from the two stage verdicts.

## Findings

- {bullet — specific observation, positive or negative, citing file:line when useful}
- {bullet}

## Exit criteria checklist

- [x] {criterion 1} — met: {one-line reason, cite a produced_file:line or a test case}
- [ ] {criterion 2} — unmet: {one-line reason, what's missing}

## Automated proof-of-work

- `test_output`: {log path or "n/a"} — {pass | fail | n/a}
- `lint_output`: {log path or "n/a"} — {pass | fail | n/a}

## Rule adherence

For every rule in `PROJECT_RULES.md` that applies to this ticket:

- Rule 3 ({short name}): respected — {evidence: file:line or test case}
- Rule 12 ({short name}): **violation** — {specific what and where}

## Stage verdicts (gigo extension)

- Spec compliance: {status} — see `{ticket-id}-spec-compliance.md`
- Craft quality: {status} — see `{ticket-id}-craft-quality.md`
```

The "Stage verdicts" section is a gigo addition — non-breaking for mc's parsers (they ignore unknown sections) and preserves the reference trail from combined to stage files. Everything above it is verbatim mc schema.

**R5.5** Stage ordering: existing rule applies. Stage 1 fail → SKIP Stage 2. Write spec-compliance verdict with `status: escalate`. Do NOT write craft-quality verdict file. Do write combined verdict with `status: escalate` and reason "spec compliance failed — craft review skipped per pipeline policy."

**R5.6** Re-verification (after operator-driven fixes): overwrite the verdict files. Each verdict file's body adds a `## History` section with a timestamped summary of the prior verdict. (Matches mc's existing reviewer-verdict pattern with history append.)

**R5.7** Partial pass / partial fail combined-status logic:
- Stage 1 pass + Stage 2 pass → combined `approved`
- Stage 1 pass + Stage 2 fail with NO Critical issue (no finding ≥90 confidence) → combined `approved_with_notes`. Listed Issues are surfaced to operator but not blocking.
- Stage 1 pass + Stage 2 fail with Critical issue (≥1 finding ≥90 confidence) → combined `escalate`. Operator must address.
- Stage 1 fail → combined `escalate` (Stage 2 skipped per R5.5)

**R5.8** Operator-facing handoff in mc-mode: existing v0.13 operator-readable summary, plus appended: *"Verdicts written to `vault/agents/reviewer/{ticket-id}.md` (combined), `{ticket-id}-spec-compliance.md`, `{ticket-id}-craft-quality.md`. Mission-control will pick up state transitions per its own rules. Suggested ticket status: [done | escalate]."*

**R5.9** Mission-control's `/mission-control review` invocation: v1 — gigo:verify writes verdicts directly per R5.4 schema. v2 could invoke `/mission-control review` as a delegate; out of scope for this brief.

**R5.10** Fallback (no mc): existing v0.13 behavior — human-readable output to operator, no verdict files.

### R6: Maintain Touchpoint

**R6.1** Add new auto-detected mode: **Add Mission-Control**. Triggered by:
- `$ARGUMENTS` contains `add-mission-control` (explicit), OR
- Operator runs `gigo:maintain` with no args AND mc detection returns STATE_NOT_INITIALIZED or STATE_UNAVAILABLE AND no preference file exists. In this case, maintain offers it as a top-level option alongside Targeted Addition / Health Check / Restructure / Upgrade.

**R6.2** Mode behavior:

| State | Action |
|---|---|
| ACTIVE | Print: *"Mission-control already active in this project. Audit vault for issues? (Vault audit deferred to v2; for now, status report only.)"* Print `mc-ticket-status --json` summary. |
| NOT_INITIALIZED | Run the **mc-init invocation procedure** (R3.1.a) — handles vault-exists case with operator confirmation. Report what was created. On success, update preference file: `mc-integration: enabled`. |
| UNAVAILABLE | Resolve mc source path per R-ADV, check `{mc-source}/install.sh` exists, invoke via Bash if yes, then run the **mc-init invocation procedure** (R3.1.a). If mc source repo missing, surface clone instructions. |

**R6.3** Reference file: new `skills/maintain/references/add-mission-control.md` containing:
- Detection logic (refers to `skills/spec/references/mc-detection.md`)
- Per-state procedure tables
- Install instructions template (with mc repo URL)
- Post-init verification steps (confirm `vault/_schema/ticket.md` exists, governance file written)

**R6.4** Coordination: Add Mission-Control mode is INFRASTRUCTURE; it does NOT trigger Targeted Addition (team composition), Health Check (rule audit), or Restructure (file reorg). It does NOT modify CLAUDE.md beyond what `/mission-control init` does (which is itself idempotent).

**R6.5** Audit capability (vault health check): deferred to v2.

### R7: Blueprint Touchpoint (No Changes in v1)

**R7.1** Blueprint receives no changes in v1. Slicing-hint emission is deferred to v2. Spec detects scope from brief content (count of components, count of features, presence of "vertical slice" language in brief) — no hint field needed.

### R-ADV: Configurable Mission-Control Source Path

**R-ADV.1** The path `~/projects/mission-control/` must NOT be hardcoded in any SKILL.md or reference file. Resolution order:

1. **Environment variable `GIGO_MC_SOURCE`** — if set and the path exists, use it.
2. **Preference file field `mc-source-path`** — if `.claude/references/mission-control-preference.md` contains a `mc-source-path:` YAML frontmatter field and the path exists, use it.
3. **Default `~/projects/mission-control/`** — fallback, documented as the default install location.

**R-ADV.2** Extend preference file schema (R2.1) with optional field:

```yaml
mc-source-path: /absolute/path/to/mission-control   # optional; overrides default ~/projects/mission-control/
```

**R-ADV.3** All three consumers (R3.1 STATE_UNAVAILABLE install flow, R6.2 UNAVAILABLE flow, error messages per §Conventions) call a single helper `resolve_mc_source_path()` documented in `skills/spec/references/mc-detection.md`. Hardcoding is an anti-pattern — the helper is the only place the default lives.

**R-ADV.4** If neither env var nor preference field is set AND `~/projects/mission-control/` doesn't exist, the error message per §Conventions instructs the operator to clone to the default path OR set `GIGO_MC_SOURCE` OR set `mc-source-path` in the preference file — give the operator all three options.

### R8: CHANGELOG Entry

**R8.1** Append to `CHANGELOG.md` an `[Unreleased]` (or version-bumped) section documenting:
- Pipeline-wide mission-control integration (4 modified skills + 1 no-change blueprint)
- Detection mechanism (3-check, 3-state) with canonical helper at `skills/spec/references/mc-detection.md`
- Preference storage at `.claude/references/mission-control-preference.md` (enabled/disabled/never-ask + mc-source-path + tiebreak fields)
- Slice mode in spec (PRD foundation + N slice designs + per-slice plans + per-slice Gate 2)
- Mc-mode in execute (ticket loop with explicit ticket-body read, two-pass crash recovery, signal emission, no state mutation)
- Mc-mode in verify (two verdict schemas — structured YAML for stage-suffixed files, mc-compatible plain-header for canonical combined file; combined synthesis logic)
- New maintain mode "Add Mission-Control" with retrofit support (handles existing-vault case via `mc-init --force --yes` with operator confirmation)
- Configurable mission-control source path (`GIGO_MC_SOURCE` env var → preference field → default `~/projects/mission-control/`)
- Authority principle (mc owns state, gigo emits signals)
- Composition test (uninstall mc → graceful degradation across all touchpoints, zero errors)
- Fact-check findings noted (mc-ticket-status emits `{id, title}` not rich objects, install.sh non-interactive, mc-scrub 30-day caveat, mc has no stale-in_progress detection)

---

## 2. Conventions

**Detection helper location:** `skills/spec/references/mc-detection.md`. spec/execute/verify/maintain SKILL.md files all reference this single file via "Read `skills/spec/references/mc-detection.md` when detecting mission-control state" — no logic duplication.

**Preference file format:** YAML frontmatter + brief documentation body. Frontmatter is the source of truth for consumers; body is for human readers.

**Skill-to-skill invocation:** when gigo skills invoke mission-control's subcommands, use the Skill tool with skill name `mission-control` and `args` containing the subcommand + arguments (e.g., `args: "init"`, `args: "ticket /abs/path/to/plan.md"`). When invoking mc bin scripts, use Bash directly (`bash("mc-init $CLAUDE_PROJECT_DIR")`).

**Signal file format (gigo writes to `vault/agents/logs/`):**

```markdown
---
type: gigo-signal
signal: execute-pickup | execute-complete | execute-blocked
ticket: TCK-X-NNN
gigo-skill: gigo:execute
gigo-version: <plugin version>
session-id: <Claude session id if available>
timestamp: <ISO-8601 UTC>
---

# Signal: {signal} for {ticket}

[Optional body — for blocked signals, include worker's status report verbatim]
```

**Verdict file format:**
- Stage-suffixed files (`{ticket-id}-spec-compliance.md`, `{ticket-id}-craft-quality.md`): gigo-owned YAML-frontmatter schema per R5.4.a.
- Canonical combined file (`{ticket-id}.md`): mc-compatible plain-header format per R5.4.b. **Must match mc's reviewer-verdict schema verbatim** (sourced from `mission-control/skills/mission-control/references/reviewer-verdict.md`) so downstream mc tools (mc-ticket-stats, mc-dashboard, mc-retro) parse it correctly.

**Path canonicalization:** all path comparisons (e.g., `mc_init` script path, vault directory path) MUST use absolute paths. Resolve via `realpath` / `Path.resolve()` / `os.path.abspath` BEFORE comparison. Filename-convention matching is forbidden (per existing v0.13 plan-verification matching pattern).

**Error message format for execute crash-recovery (two-pass per R4.6):**

```
Crash-recovery audit: found N ticket(s) in_progress without completion signals.

From signal files (this session's logs, within 30-day mc-scrub window):
  - {ticket-id}: picked up at {timestamp} ({hours} hours ago), no completion signal

From mc-ticket-status (in_progress with no current pickup signal — possibly interrupted before scrub, or by a different executor):
  - {ticket-id}: ticket status = in_progress, no matching pickup signal in current logs

Options per ticket:
  [r] Re-pick (dispatch fresh worker on this ticket)
  [e] Escalate (operator decides ticket state via mc tools — gigo does NOT mutate ticket state)
  [s] Skip (leave for next /execute run)

Choice for each ticket:
```

**Error message format for `install.sh` missing (mc source repo not cloned):**

```
mission-control source repo not found at {resolved-path}.
(Resolution order checked: GIGO_MC_SOURCE env var → mc-source-path in preference file → default ~/projects/mission-control/)

To enable mission-control integration, choose ONE of:

  1. Clone to the default location:
       git clone <mc-repo-url> ~/projects/mission-control

  2. Clone elsewhere and point GIGO at it:
       export GIGO_MC_SOURCE=/your/path/to/mission-control
       (add to your shell profile for persistence)

  3. Set mc-source-path in .claude/references/mission-control-preference.md:
       mc-source-path: /your/path/to/mission-control

Then re-run /gigo:spec (or /gigo:maintain add-mission-control) and choose install+init.
```

(Operator must provide the mc repo URL — gigo doesn't hardcode it.)

**Timestamps:** ISO-8601 UTC with `Z` suffix (e.g., `2026-04-18T00:15:22Z`). Matches existing v0.13 marker convention.

**Default verdict schema position fields:** `exit_criteria` checkboxes use `[ ]` (not yet evaluated), `[x]` (met), or `[!]` (not-met). The bracket character distinguishes the three states. Operators reading the verdict file see the unchecked boxes for any criteria the reviewer marked `not-met`.

**Subagent dispatch:** verify's per-stage subagents (already in v0.13) use `Agent` with `subagent_type: "general-purpose"`. No new subagent types introduced.

**Skill file size cap:** all 4 affected SKILL.md files MUST stay under 500 lines after this brief's modifications. Procedural depth lives in references.

---

## 3. Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| add (pipeline) | R1, R2, R3, R4, R5, R6, R-ADV, R8 — pipeline-wide addition across 4 skills + 4 new refs + CHANGELOG | ✅ |
| compose (with mc, not depend) | R1.2-R1.4 (detection by name only), R3.5 / R6.3 (subcommand invocation, not import), R5.4.b (plain-header format matches mc schema), §Conventions skill-to-skill rules | ✅ |
| detect (mc state) | R1.1-R1.5 (three-check detection, three-state output) | ✅ |
| adapt (output) | R3 (slice vs monolithic), R4 (mc-mode vs plan.md), R5 (verdicts vs human-readable), R6 (mode addition) | ✅ |
| nudge (operator) | R3.1 install/init prompts, R3.1.a vault-exists confirmation, R6.1-R6.2 maintain entry point | ✅ |
| emit (signals) | R4.3 (execute signals + explicit ticket body read), R5.4 (verify verdict files, two schemas), §Conventions signal file format | ✅ |
| retrofit (existing projects) | R6.2 STATE_NOT_INITIALIZED branch, R3.1 NOT_INITIALIZED prompt, R3.1.a vault-exists with tickets confirmation | ✅ |
| invoke (mc subcommands) | R3.5 ticket trigger, R3.1.a init invocation procedure, R4.3 mc-proof-of-work invocation, R6.2 maintain init flow | ✅ |
| respect (preferences) | R2 preference storage + behavior table, R-ADV.2 mc-source-path field | ✅ |
| fall-back (graceful degradation) | R3.7, R4.10, R5.10 explicit "no changes from v0.13" fallbacks; R4.6 two-pass crash recovery; R4.7 honest non-claim; composition test in §Acceptance Criteria | ✅ |

No unresolved verbs.

---

## 4. Known Risks (from design brief, addressed in implementation)

**Risk 1 — Mission-control churn.** mc is in active development; subcommand interface could change. Mitigation: gigo invokes mc subcommands by NAME only (no internal-structure dependency). If mc renames a subcommand, gigo emits a clear error and falls back. Documented in R3.5, R6.2, §Conventions.

**Risk 2 — mc install ergonomics.** Original brief assumed install.sh was interactive; fact-check confirmed it's non-interactive. Mitigation: R3.1 + R6.2 invoke install.sh directly via Bash. Operator action only required if mc source repo missing (clone instructions per §Conventions).

**Risk 3 — Two-step init feels heavy.** mc-init Python script + `/mission-control init` skill are two operations. Operator may forget step 2. Mitigation: R3.1 + R6.2 invoke BOTH steps when operator chooses install+init. R1.4 STATE_NOT_INITIALIZED detection (vault exists but governance not extracted) catches missed step 2 and offers to complete.

**Risk 4 — PRD foundation as new artifact pattern.** v0.13 specs don't have a PRD layer. Mitigation: R3.2 generates PRD foundation ONLY in slice mode. Monolithic mode unchanged (R3.7).

**Risk 5 — Per-slice approval ceremony.** 10 slices = 10 separate Phase 7 + Phase 10 reviews. Mitigation: R3.3 + R3.4 allow batch approval ("approve all PRD + slices" / "approve all plans") with per-slice review on request.

**Risk 6 — Signal file lifetime (mc-scrub).** 30-day deletion in `vault/agents/logs/`. Mitigation: R4.7 documents the limitation; mc's own stale-`in_progress` detection is the safety net.

**Risk 7 — Composition test.** If gigo:execute starts depending on `mc-ticket-status` JSON schema, mc version change could break execute even with loose coupling. Mitigation: R4.3 parses defensively (look for ticket IDs in `unblocked` array); fall back to direct `vault/tickets/*.md` reads if mc-ticket-status output is unparseable. Document this in execute's reference.

---

## 5. Non-Goals

- Not making mission-control a hard requirement. v0.12 was that and was reverted. Composition test is non-negotiable.
- Not merging mission-control's code into gigo. Two separate projects, loose coupling via subcommand + convention-path interfaces.
- Not designing mission-control's internal slicing algorithm, ticket schema internals, state machine, or governance extraction logic. mc owns those; gigo just detects + invokes + reads convention paths.
- Not replacing v0.13 behaviors. Monolithic spec, plan.md execute, human-readable verify all stay as fallbacks.
- Not building a shared in-process data format. Artifact signaling is the entire interface.
- Not solving mc bugs. If mc's init is flaky on some projects, that's an mc bug to file — not gigo's problem to work around.
- Not coordinating release cycles. Two projects ship independently.
- Not implementing parallel ticket execution in v1. Sequential only; v2 deferred.
- Not implementing slicing-hint in blueprint in v1. Spec detects scope from brief content; v2 deferred.
- Not implementing vault audit in maintain in v1. v2 deferred.
- Not invoking `/mission-control review` from verify in v1. gigo:verify writes verdicts directly per R5.4 schema; v2 could delegate.
- Not solving "signal files older than 30 days" — accept R4.7 limitation in v1; rely on mc's own stale-in_progress detection.

---

## 6. Acceptance Criteria

### Detection
- Three-check detection (R1.2) executes in < 100ms.
- All three states (UNAVAILABLE / NOT_INITIALIZED / ACTIVE) reachable from a real project setup.
- Single source of truth for detection logic — `skills/spec/references/mc-detection.md` is the only file containing the detection algorithm. Other skills reference it.

### Preference
- Preference file at `.claude/references/mission-control-preference.md` controls nudge behavior per R2.2 table.
- All 12 (state × preference) combinations behave per the table.
- File missing → default behavior (ask once per project per state).

### Spec
- A user running `gigo:spec` without mission-control gets a clear, non-annoying offer to install+init it, with a concrete preview of what they'd gain.
- A user running `gigo:spec` with mc available but project not initialized gets the retrofit offer (init only — not install).
- A user running `gigo:spec` with mc fully active gets slice-based output (PRD + N slice files + per-slice plans).
- A user who declined the nudge runs spec and gets v0.13 monolithic output cleanly.
- The detection + nudge adds < 500ms overhead to spec kickoff.
- Slice mode and monolithic mode share Phase 0 (Gate 1) — Gate 1 runs once at PRD level when slice mode is active.

### Execute
- With mc active, execute picks tickets from `mc-ticket-status --json`'s `unblocked` array in DAG order, reads each ticket's full body from `vault/tickets/{ticket-id}.md` (minimal JSON from mc-ticket-status is NOT treated as sufficient context), emits state signals (`execute-pickup`, `execute-complete`, `execute-blocked`) without mutating ticket internals.
- Without mc, execute runs against plan.md exactly as v0.13 — zero regression.
- Crash recovery: two-pass audit per R4.6 — Pass A scans signal files (30-day window), Pass B cross-references `mc-ticket-status` `in_progress` list against current signals. Both surface to operator via the §Conventions error message.
- Plan.md coexistence prompt fires correctly when both vault/tickets/ and plan.md exist.
- At least one end-to-end scenario validated: greenfield gigo+mc project produces slices → tickets → execute picks them up → signals fire correctly.

### Verify
- With mc active and ticket ID resolvable, verify writes 3 verdict files per ticket: stage-suffixed files (R5.4.a schema, YAML frontmatter) and canonical combined file (R5.4.b schema, mc plain-header format).
- Canonical combined file (`{ticket-id}.md`) is parseable by mc's downstream tools (`mc-ticket-stats` reads Status/Timestamp headers; mc-retro groups by Status). Validate by running `mc-ticket-stats {ticket-id}` after a verify-written combined file exists — the rendered output must show the Status correctly.
- Without mc, verify produces v0.13 human-readable output, no verdict files.
- Re-verification after fixes overwrites verdict files cleanly with history sections preserving prior summaries.
- Combined-status synthesis follows R5.7 logic: any Critical issue → escalate; otherwise pass-with-notes.

### Maintain
- A user running `gigo:maintain` on an existing gigo project can retrofit mc proactively via the new Add Mission-Control mode.
- Retrofit completes cleanly on a range of project ages (fresh v0.13 assembly, older v0.10 assembly, pre-assembly legacy project) — or fails gracefully with a clear error message, not a half-broken state.
- Existing-vault cases handled per R3.1.a: vault absent → plain mc-init; vault present without tickets → `--force`; vault present with tickets → operator confirmation then `--force --yes`.
- The new mode is auto-suggested when state is NOT_INITIALIZED or UNAVAILABLE AND no preference file exists.

### Global
- Composition test passes: uninstall mc entirely → all 4 affected gigo skills fall back to v0.13 behavior with zero errors. Verified by checking that detection (R1) returns STATE_UNAVAILABLE and all preference branches in R2.2 result in v0.13 fallback.
- v0.12 test passes: no gigo code imports from mc; all interaction is via Skill tool subcommand invocation, Bash bin script invocation, and convention-path file reads/writes.
- No hardcoded `~/projects/mission-control/` path in any SKILL.md or reference. All call sites go through `resolve_mc_source_path()` per R-ADV.
- Operator with mc cloned to a non-default path (via `GIGO_MC_SOURCE` or preference field) completes install+init successfully end-to-end.
- All 4 affected SKILL.md files stay under 500 lines after modifications.
- All cross-references between SKILL.md files and `skills/spec/references/mc-detection.md` resolve.
- CHANGELOG `[Unreleased]` (or version) entry covers all 5 touchpoints + authority principle + composition test + configurable path.
- One end-to-end scenario validated end-to-end: greenfield gigo+mc → slice spec → ticket creation → execute work loop → verify verdicts (with downstream `mc-ticket-stats` successfully parsing the combined verdict file) → operator transitions ticket state per mc rules.

<!-- approved: spec 2026-04-19T04:48:49Z by:Eaven -->
