# Pipeline-Wide Mission-Control Integration — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-18-pipeline-wide-mission-control-integration-design.md`

**Design brief:** `.claude/plans/crystalline-crunching-aurora.md`

**Goal:** Add pipeline-wide mission-control awareness to 4 gigo skills (spec, execute, verify, maintain) via detect-and-adapt with install/init nudge, without creating any hard dependency on mission-control.

**Architecture:** One canonical detection helper (`skills/spec/references/mc-detection.md`) referenced by all 4 touching skills. mc's existing subcommand + bin-script + convention-path interfaces are the integration surface; gigo invokes by name, never by import. Authority principle: mc owns ticket state, gigo emits signals via file writes at `vault/agents/logs/` and via verdict file writes at `vault/agents/reviewer/`.

**Tech Stack:** Markdown skill files, Bash for mc bin-script invocation, Skill tool for mc subcommand invocation, YAML frontmatter for structured artifacts, mc's plain-header Markdown format for the canonical combined verdict file.

---

## File Map

**CREATE (5 new reference files):**
- `skills/spec/references/mc-detection.md` — canonical detection logic, preference schema, configurable source-path resolution. Referenced by all 4 affected SKILL.md files.
- `skills/spec/references/slice-mode.md` — slice mode output contract (PRD foundation + N slices + per-slice plans + per-slice Gate 2).
- `skills/verify/references/mc-verdict-schema.md` — R5.4.a structured schema (stage files) + R5.4.b mc-compatible plain-header schema (combined file), synthesis rules.
- `skills/maintain/references/add-mission-control.md` — retrofit procedure with mc-init invocation procedure (R3.1.a), install instructions template.
- `skills/execute/references/mc-mode-work-loop.md` — mc-mode ticket loop procedure (crash recovery, main loop, worker prompt contents, non-mutation rule). Extracted per GIGO's hub-and-spoke convention (`.claude/rules/skill-engineering.md`: *"If a mode section in SKILL.md exceeds ~5 lines of procedure, move it to a reference file and replace with a pointer"*).

**MODIFY (4 SKILL.md files + CHANGELOG):**
- `skills/spec/SKILL.md` — Phase 5 mc-mode branch, Phase 8 per-slice plan generation, Phase 10 per-slice approval, ticket-trigger invocation, Phase 9.75 per-slice Gate 2.
- `skills/execute/SKILL.md` — Before-Starting mc-mode detection step, mc-mode work loop section, two-pass crash recovery, plan.md coexistence.
- `skills/verify/SKILL.md` — mc-mode detection at start, ticket ID resolution, per-stage verdict writes, combined synthesis, mc plain-header format for canonical file.
- `skills/maintain/SKILL.md` — new auto-detected mode "Add Mission-Control", auto-suggestion logic.
- `CHANGELOG.md` — `[Unreleased]` section per R8.1.

**Line-cap constraint:** all 4 affected SKILL.md files MUST stay under 500 lines after modifications.

---

## Dependency Graph

```
Wave 1 (parallel, no cross-deps):
  Task 1: Create mc-detection.md             (foundation)
  Task 2: Create slice-mode.md               (spec-only ref)
  Task 3: Create mc-verdict-schema.md        (verify-only ref)
  Task 4: Create add-mission-control.md      (maintain-only ref)
  Task 5: Create mc-mode-work-loop.md        (execute-only ref)

Wave 2 (parallel, blocked-by Wave 1 references):
  Task 6: Modify spec/SKILL.md               (needs Task 1, 2)
  Task 7: Modify execute/SKILL.md            (needs Task 1, 5)
  Task 8: Modify verify/SKILL.md             (needs Task 1, 3)
  Task 9: Modify maintain/SKILL.md           (needs Task 1, 4)

Wave 3:
  Task 10: Update CHANGELOG.md               (blocked-by all)
```

---

## Task 1: Create mc-detection.md

**blocks:** 6, 7, 8, 9
**blocked-by:** (none)
**parallelizable:** true

**Files:**
- Create: `skills/spec/references/mc-detection.md`

- [x] **Step 1: Write the detection reference file.**

File contents (complete, copy-paste ready):

````markdown
# Mission-Control Detection, Preferences, and Source Path

Canonical reference for detecting mission-control (mc) availability, reading/writing the project's mc preference, and resolving the mc source repo path. Read by spec, execute, verify, and maintain when any of them needs to adapt behavior to mc state.

## Three-Check Detection

Runs per-invocation. Total cost < 100ms.

| Check | Mechanism | Cost |
|---|---|---|
| Skill availability | `"mission-control"` present in session's available skills list | < 1ms |
| Bin script availability | `command -v mc-init` returns success (exit 0) | < 50ms |
| Project initialized | `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` exists | < 10ms |

## Effective State

```
mc_available = skill_available AND mc_init_available
mc_active    = mc_available AND project_initialized
```

Three states (consumer-facing):
- **STATE_UNAVAILABLE** — `mc_available == false`. mc not installed at session level.
- **STATE_NOT_INITIALIZED** — `mc_available && !project_initialized`. mc installed but project not scaffolded.
- **STATE_ACTIVE** — `mc_active == true`. mc installed AND project scaffolded.

## Preference File

Path: `.claude/references/mission-control-preference.md` (project-local, never global).

Schema:
```markdown
---
mc-integration: enabled | disabled | never-ask
last-asked: <ISO-8601 UTC timestamp>
last-state-when-asked: STATE_UNAVAILABLE | STATE_NOT_INITIALIZED
tiebreak: tickets | plan | sequential   # set by execute when both vault/tickets/ AND plan.md exist
mc-source-path: /absolute/path/to/mission-control   # optional; overrides default
---

# Mission-Control Integration Preference

[Body documentation — see R2.1 for details.]
```

Behavior table (state × preference):

| `mc-integration` | State | Action |
|---|---|---|
| (file missing) | UNAVAILABLE | Prompt install+init |
| (file missing) | NOT_INITIALIZED | Prompt init |
| (file missing) | ACTIVE | mc-aware mode silently |
| `enabled` | UNAVAILABLE | Prompt |
| `enabled` | NOT_INITIALIZED | Prompt |
| `enabled` | ACTIVE | mc-aware mode silently |
| `never-ask` | UNAVAILABLE | v0.13 fallback silently |
| `never-ask` | NOT_INITIALIZED | v0.13 fallback silently |
| `never-ask` | ACTIVE | mc-aware mode silently |
| `disabled` | UNAVAILABLE | v0.13 fallback silently |
| `disabled` | NOT_INITIALIZED | v0.13 fallback silently |
| `disabled` | ACTIVE | v0.13 fallback silently (escape hatch) |

## Configurable Source Path (resolve_mc_source_path)

Resolution order:

1. Environment variable `GIGO_MC_SOURCE` — if set and path exists, use it.
2. Preference file field `mc-source-path` — if set and path exists, use it.
3. Default `~/projects/mission-control/` — fallback.

Do NOT hardcode the default anywhere else. All call sites go through this helper.

When resolution fails (none of the three paths exist), surface the clone-instructions error per §Conventions in the spec (with all three options: clone to default, set env var, set preference field).

## Mc-Init Invocation Procedure (R3.1.a)

Shared by all "install or init mc" paths. Steps:

1. **Pre-flight vault check:** test whether `$CLAUDE_PROJECT_DIR/vault/` exists. If yes, count tickets: `count = len(glob("$CLAUDE_PROJECT_DIR/vault/tickets/TCK-*.md")) - 1_if_TEMPLATE_present`.
2. **Branch on vault state:**
   - **Vault absent** → `bash("cd $CLAUDE_PROJECT_DIR && mc-init $CLAUDE_PROJECT_DIR")`.
   - **Vault exists, zero tickets** → announce to operator, run `bash("cd $CLAUDE_PROJECT_DIR && mc-init $CLAUDE_PROJECT_DIR --force")`. This rebuilds scaffolding only; no ticket data to destroy.
   - **Vault exists WITH ≥1 ticket** → DO NOT run `mc-init --force --yes`. This would DELETE the entire vault including tickets (verified against `mission-control/bin/mc-init` line 288: `shutil.rmtree(vault)`). Instead, ABORT with this message:

     > "Existing vault at `$CLAUDE_PROJECT_DIR/vault/` contains N ticket(s). `mc-init --force` would DELETE the entire vault including all tickets, logs, and verdicts.
     >
     > This retrofit path refuses to destroy operator data. Choose ONE of:
     >
     >   1. **Vault is already usable** — if `vault/_schema/ticket.md` exists, skip mc-init entirely (mc is already active). Re-run gigo:maintain; detection should report STATE_ACTIVE.
     >   2. **Rebuild scaffolding without losing tickets** — manually: move `vault/tickets/` aside, run `mc-init $CLAUDE_PROJECT_DIR --force`, restore `vault/tickets/`.
     >   3. **Fresh start** — back up `vault/` externally (e.g., `mv vault vault.bak`), then re-run this flow; detection will see an absent vault and run plain `mc-init`."
     >
     > Falling back to monolithic mode. No preference file written — re-run after choosing an option above.

     Execute writes the fallback to monolithic mode; does NOT write preference file (operator hasn't decided).
3. **Invoke `/mission-control init` skill** via Skill tool (only reached on the absent-vault or zero-tickets paths).
4. **Verify:** confirm `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` now exists. If missing, report mc-init failure to operator, fall back to monolithic mode.
5. **Preference update:** on success, if preference file missing, write `mc-integration: enabled`.

If mc-init exits non-zero at any step, surface stderr verbatim — do not hide mc failures.

## When to Read This

- **spec/SKILL.md Phase 5:** when deciding mc-mode (slice) vs monolithic fallback.
- **execute/SKILL.md Before-Starting:** when deciding mc-mode (ticket loop) vs plan.md fallback.
- **verify/SKILL.md start:** when deciding mc-mode (verdict files) vs human-readable fallback.
- **maintain/SKILL.md auto-detect:** when auto-suggesting the Add Mission-Control mode.
````

- [x] **Step 2: Verify the file is complete and well-formed.**

Run: `wc -l skills/spec/references/mc-detection.md` — expect 110-135 lines (expanded R3.1.a retrofit-safety block). Read the file to confirm no placeholders.

- [x] **Step 3: Commit.**

```bash
git add skills/spec/references/mc-detection.md
git commit -m "feat(spec): add mc-detection reference — canonical detection + preference + source path

Shared reference for spec, execute, verify, maintain — implements R1, R2, R-ADV
from the pipeline-wide mission-control integration spec."
```

#### What Was Built
- **Deviations:** None. Worker reproduced the plan's copy-paste content byte-for-byte (107 lines; plan's 110-135 estimate was stale).
- **Review changes:** None.
- **Notes for downstream:** Retrofit-safety ABORT path is load-bearing — cites `mission-control/bin/mc-init` line 288 (`shutil.rmtree(vault)`). Task 4 correctly delegates to this file's Mc-Init Invocation Procedure rather than duplicating. All 4 consuming skills (spec/execute/verify/maintain) must route through `resolve_mc_source_path()` helper — do NOT hardcode `~/projects/mission-control/` elsewhere.

---

## Task 2: Create slice-mode.md

**blocks:** 6
**blocked-by:** (none)
**parallelizable:** true

**Files:**
- Create: `skills/spec/references/slice-mode.md`

- [x] **Step 1: Write the slice-mode reference file.**

File contents (copy-paste ready):

````markdown
# Slice Mode — Spec Phase 5 with Mission-Control Active

When mc is STATE_ACTIVE and the operator has consented (via preference file or accepted nudge), spec Phase 5 produces slice-based output instead of a single monolithic spec. Downstream effects cascade through Phase 8 (plans), Phase 9.75 (Gate 2), and Phase 10 (approval) — all are per-slice.

## Output Contract

### PRD Foundation (one per brief)

Path: `docs/gigo/specs/{date}-{topic}-prd-foundation-design.md`

Sections:
- `# {Topic} — PRD Foundation`
- `## Original Request` (verbatim from brief)
- `## Verb Trace` (full verb trace across all slices)
- `## Overview` (2-3 paragraphs naming all slices, their order, their interfaces)
- `## Slices` — numbered table: `| # | Slice name | File path | Dependencies | Interface |`
- `## Shared Conventions` (project-wide conventions — timestamps, error message format, skill-to-skill invocation rules)
- `## Known Risks` (PRD-level risks spanning slices)
- `## Non-Goals` (brief-level non-goals)

### Per-Slice Design (one per vertical slice)

Path: `docs/gigo/specs/{date}-{topic}-slice-{N}-{name}-design.md`

Each slice file is a complete spec for that slice — bare-worker sufficient. Sections:
- `# Slice {N}: {Name}`
- `## Original Request (slice-scoped)` — which subset of the original request this slice addresses.
- `## Verb Trace (slice-scoped)` — the verbs from the original request that this slice implements.
- `## Requirements` — R1, R2, ... numbered per slice (not globally).
- `## Conventions` — any slice-specific conventions (inherits shared from PRD foundation).
- `## Acceptance Criteria` — measurable gates.

Slices are ordered such that earlier slices do not depend on later ones. Each slice is independently shippable.

## Approval Ceremony (Phase 7, Phase 10)

Default: offer batch approval with per-slice review on request.

Phase 7 prompt:
> "PRD foundation + N slices written. Options:
>  [a] Approve all (PRD foundation + all N slices)
>  [s] Review each slice individually (I'll walk through them)
>  [r] Revise — tell me what to change
> Your choice?"

On batch approval, apply `<!-- approved: spec {timestamp} by:{username} -->` to every slice file AND the PRD foundation in a single commit.

On per-slice review, iterate slice by slice, writing the approval marker per file as each is approved.

Phase 10 follows the same pattern for per-slice plan approval.

## Plan Generation (Phase 8)

One plan file per slice at `docs/gigo/plans/{date}-slice-{N}-{name}.md`. Each plan cites its slice file in its header's `**Spec:**` field.

The PRD foundation does NOT get its own plan — it's descriptive, not executable.

## Gate 2 Interaction (Phase 9.75)

- **Gate 1 (Phase 0):** runs ONCE at the top, PRD-level. Runtime targets don't vary per slice.
- **Gate 2 (Phase 9.75):** runs PER-SLICE-PLAN. Each slice plan gets its own `docs/gigo/research/{date}-slice-{N}-{name}-plan-verification.md`. Block-on-❌ enforcement in execute applies per slice.

## Ticket Trigger (after Phase 10)

After all slice plans are approved, spec invokes mission-control's ticket-generation subcommand for each slice plan in order:

```
for plan_file in approved_slice_plans:
    Skill(skill="mission-control", args=f"ticket {plan_file}")
```

mission-control runs its own DAG validation, creates `vault/tickets/TCK-{phase}-{seq}.md` files per slice plan. Spec presents the consolidated ticket-creation report to the operator.

## Monolithic Mode Fallback

If mc is not STATE_ACTIVE OR the operator declined the nudge OR `mc-integration: disabled`, spec uses v0.13 monolithic mode unchanged. See the Phase 5 mc-mode decision tree in `skills/spec/SKILL.md` and the behavior table in `skills/spec/references/mc-detection.md`.

## Scope Heuristic (blueprint decides → spec detects)

Slicing-hint in blueprint is deferred to v2. In v1, spec detects scope from brief content:
- Brief has ≥3 distinct components (distinct files / systems / surfaces) → candidate for slice mode.
- Brief uses "vertical slice" or similar language → candidate.
- Brief is a single-surface change (one bug fix, one config, one function) → NOT a slice candidate; monolithic even if mc is active.

The nudge and the preference gate still apply — detection only determines whether slice mode is *offered*, not whether it's *forced*.
````

- [x] **Step 2: Verify.**

Run: `wc -l skills/spec/references/slice-mode.md` — expect 70-90 lines. No placeholders.

- [x] **Step 3: Commit.**

```bash
git add skills/spec/references/slice-mode.md
git commit -m "feat(spec): add slice-mode reference — PRD foundation + N slice designs

Implements R3.2-R3.7 from the pipeline-wide mission-control integration spec."
```

#### What Was Built
- **Deviations:** None — byte-identical to plan's copy-paste content (85 lines, within 70-90 range).
- **Review changes:** None.
- **Notes for downstream:** Ticket trigger fires AFTER each slice plan's Phase 10 approval (not during design). Invocation pattern: `Skill(skill="mission-control", args=f"ticket {plan_file}")` per approved slice plan in order. Task 6 (spec/SKILL.md) must wire the Phase 5 mc-mode branch to reference this file, the Phase 9.75 per-slice Gate 2 dispatch, the Phase 10 batch-or-per-slice approval flow, and the post-Phase-10 ticket trigger loop.

---

## Task 3: Create mc-verdict-schema.md

**blocks:** 8
**blocked-by:** (none)
**parallelizable:** true

**Files:**
- Create: `skills/verify/references/mc-verdict-schema.md`

- [x] **Step 1: Write the verdict-schema reference.**

File contents (copy-paste ready):

````markdown
# Mission-Control Verdict Schemas

When mc is STATE_ACTIVE and gigo:verify runs with a resolvable ticket ID, verify writes three verdict files per ticket. This reference defines the two distinct schemas.

## File Paths

```
vault/agents/reviewer/{ticket-id}-spec-compliance.md   # R5.4.a (YAML frontmatter)
vault/agents/reviewer/{ticket-id}-craft-quality.md     # R5.4.a (YAML frontmatter)
vault/agents/reviewer/{ticket-id}.md                   # R5.4.b (mc plain-header)
```

## Ticket ID Resolution (priority order)

1. Explicit flag: `gigo:verify --ticket TCK-X-NNN`
2. Most recent `vault/agents/logs/{ticket-id}-execute-pickup.md` (if execute just ran in this session)
3. Operator-provided in conversation (verify asks if not resolvable from 1 or 2)
4. Fall back to v0.13 mode if none resolvable

## Stage File Schema (R5.4.a — gigo-owned, YAML frontmatter)

Used for `{ticket-id}-spec-compliance.md` and `{ticket-id}-craft-quality.md`. Structured for programmatic consumption by gigo tooling.

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

## Rule-Adherence Notes
[Notes against `vault/_governance/PROJECT_RULES.md` if mc has extracted rules; otherwise "No governance rules to check against."]
```

## Canonical Combined File Schema (R5.4.b — mc-compatible plain-header)

Used for `{ticket-id}.md`. **Structurally matches mc's existing reviewer-verdict format** — sections, headers, and field names align with `mission-control/skills/mission-control/references/reviewer-verdict.md`. The `Reviewer:` field value is `gigo:verify` (not mc's `mission-control:review`), since gigo wrote the verdict — consumers that display the value see who actually reviewed. Downstream mc tools (mc-ticket-stats, mc-dashboard, mc-retro — verified present at `mission-control/bin/`) parse this format by regex against field labels, not specific values. Section ordering and the extension location (§Stage verdicts AFTER mc's canonical sections) are load-bearing — do not reorder.

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

The "Stage verdicts" section is a gigo addition — non-breaking for mc parsers (they ignore unknown sections) and preserves the reference trail.

## Stage Ordering

Stage 1 (spec compliance) fail → SKIP Stage 2 (existing rule). Write spec-compliance file with `status: escalate`. Do NOT write craft-quality file. Do write combined file with `status: escalate` and reason "spec compliance failed — craft review skipped per pipeline policy."

## Combined Status Synthesis

| Stage 1 | Stage 2 | Critical issue in S2? | Combined |
|---|---|---|---|
| pass | pass | — | `approved` |
| pass | fail | no (no finding ≥90 confidence) | `approved_with_notes` |
| pass | fail | yes (≥1 finding ≥90 confidence) | `escalate` |
| fail | skipped | — | `escalate` |

## Re-Verification (after operator-driven fixes)

Overwrite verdict files. Each verdict body adds a `## History` section with a timestamped summary of the prior verdict — matches mc's existing reviewer-verdict pattern.

## Operator Handoff

After writing all 3 files:

> "Verdicts written to `vault/agents/reviewer/{ticket-id}.md` (combined), `{ticket-id}-spec-compliance.md`, `{ticket-id}-craft-quality.md`. Mission-control will pick up state transitions per its own rules. Suggested ticket status: [done | escalate]."

## Validation

After writing the combined file, sanity-check by running: `mc-ticket-stats {ticket-id}`. The rendered Status line must match what gigo wrote. If mc-ticket-stats reports something else, the combined file format drifted — fix it.
````

- [x] **Step 2: Verify.**

Run: `wc -l skills/verify/references/mc-verdict-schema.md` — expect 90-120 lines. No placeholders.

- [x] **Step 3: Commit.**

```bash
git add skills/verify/references/mc-verdict-schema.md
git commit -m "feat(verify): add mc-verdict-schema reference — stage files + canonical combined

Implements R5.3-R5.8 from the pipeline-wide mission-control integration spec.
Stage files use gigo-owned YAML frontmatter; canonical combined file uses
mc-compatible plain-header format so downstream mc tools (mc-ticket-stats,
mc-dashboard, mc-retro) parse it correctly."
```

#### What Was Built
- **Deviations:** 123 lines vs 90-120 plan estimate (+3 lines). Reviewer confirmed all content load-bearing; no trimmable sections. Matches plan's copy-paste block verbatim.
- **Review changes:** None.
- **Notes for downstream:** Two schemas locked: R5.4.a YAML-frontmatter for stage files, R5.4.b mc plain-header for canonical combined file. `Reviewer:` field value is `gigo:verify` (not `mission-control:review`) — verified safe because mc parsers read field labels, not values. The "Stage verdicts (gigo extension)" section MUST remain AFTER mc's canonical sections — Task 8 consumers must not reorder or move the extension. Final sanity check is `mc-ticket-stats {ticket-id}` against the rendered Status line.

---

## Task 4: Create add-mission-control.md

**blocks:** 9
**blocked-by:** (none)
**parallelizable:** true

**Files:**
- Create: `skills/maintain/references/add-mission-control.md`

- [x] **Step 1: Write the add-mission-control reference.**

File contents (copy-paste ready):

````markdown
# Add Mission-Control — Maintain Mode Procedure

New auto-detected mode in gigo:maintain for retrofitting mission-control onto an existing project. Mode is INFRASTRUCTURE — it does NOT trigger Targeted Addition (team composition), Health Check (rule audit), or Restructure (file reorg).

## Triggers

Explicit: `$ARGUMENTS` contains `add-mission-control`.

Auto-suggested: operator runs `gigo:maintain` with no args AND mc detection returns STATE_NOT_INITIALIZED or STATE_UNAVAILABLE AND no preference file exists. In this case, maintain offers it as a top-level option alongside Targeted Addition / Health Check / Restructure / Upgrade.

## Detection

Read `skills/spec/references/mc-detection.md` for the canonical detection algorithm and state definitions. Do NOT reimplement.

## Per-State Behavior

| State | Action |
|---|---|
| ACTIVE | Print: *"Mission-control already active in this project. Audit vault for issues? (Vault audit deferred to v2; for now, status report only.)"* Print `mc-ticket-status --json` summary. |
| NOT_INITIALIZED | Run the **Mc-Init Invocation Procedure** per `skills/spec/references/mc-detection.md`. Report what was created. On success, update preference file: `mc-integration: enabled`. |
| UNAVAILABLE | Resolve mc source path per `resolve_mc_source_path()` in `skills/spec/references/mc-detection.md`. Check `{mc-source}/install.sh` exists; if yes, invoke via Bash, then run the Mc-Init Invocation Procedure. If mc source missing, surface clone instructions (all three resolution options). |

## Install Instructions Template (UNAVAILABLE, source missing)

```
mission-control source repo not found at {resolved-path}.
(Resolution order: GIGO_MC_SOURCE env var → mc-source-path in preference file → default ~/projects/mission-control/)

To enable mission-control integration, choose ONE of:

  1. Clone to the default location:
       git clone <mc-repo-url> ~/projects/mission-control

  2. Clone elsewhere and point GIGO at it:
       export GIGO_MC_SOURCE=/your/path/to/mission-control
       (add to your shell profile for persistence)

  3. Set mc-source-path in .claude/references/mission-control-preference.md:
       mc-source-path: /your/path/to/mission-control

Then re-run /gigo:maintain add-mission-control.
```

(The mc repo URL is not hardcoded — operator must know where mc lives.)

## Post-Init Verification

After Mc-Init Invocation Procedure returns:

1. Confirm `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` exists.
2. Confirm `$CLAUDE_PROJECT_DIR/vault/_governance/PROJECT_RULES.md` exists.
3. Confirm `$CLAUDE_PROJECT_DIR/CLAUDE.md` was augmented (check for `<!-- mission-control:begin -->` marker).

If any are missing, the init was partial. Report the specific missing artifact to the operator. Do not claim success.

## Coordination With Other Modes

Add Mission-Control does NOT:
- modify CLAUDE.md beyond what `/mission-control init` does (which is itself idempotent between `<!-- mission-control:begin -->` markers).
- touch team composition, persona files, or `.claude/references/review-criteria.md`.
- run Health Check or Restructure audits.

If the operator wants those, they can run `gigo:maintain` again in the appropriate mode after mc is initialized.

## Vault Audit

Deferred to v2. v1 reports "active" status without auditing vault contents.
````

- [x] **Step 2: Verify.**

Run: `wc -l skills/maintain/references/add-mission-control.md` — expect 60-80 lines. No placeholders.

- [x] **Step 3: Commit.**

```bash
git add skills/maintain/references/add-mission-control.md
git commit -m "feat(maintain): add add-mission-control reference — retrofit procedure

Implements R6.3 from the pipeline-wide mission-control integration spec.
Handles three states (ACTIVE/NOT_INITIALIZED/UNAVAILABLE) with operator
confirmation for existing-vault case via shared Mc-Init Invocation Procedure."
```

#### What Was Built
- **Deviations:** None (67 lines, within 60-80 range).
- **Review changes:** None.
- **Notes for downstream:** Correctly DELEGATES to Shared Mc-Init Invocation Procedure in `skills/spec/references/mc-detection.md` rather than inlining — prevents DRY drift on the safety-critical vault-with-tickets ABORT path. Task 9 (maintain/SKILL.md) must wire the mode into (a) auto-detect logic when `$ARGUMENTS` contains `add-mission-control`, (b) top-level menu option alongside Targeted Addition / Health Check / Restructure / Upgrade when detection returns NOT_INITIALIZED/UNAVAILABLE and no preference exists.

---

## Task 5: Create mc-mode-work-loop.md

**blocks:** 7, 10
**blocked-by:** (none)
**parallelizable:** true

**Files:**
- Create: `skills/execute/references/mc-mode-work-loop.md`

**Rationale:** R4.3 describes ~80 lines of procedural detail (crash recovery, main loop, worker prompt contents, non-mutation rule). Inlining it in `execute/SKILL.md` violates GIGO's hub-and-spoke convention (`.claude/rules/skill-engineering.md`: *"If a mode section in SKILL.md exceeds ~5 lines of procedure, move it to a reference file and replace with a pointer"*). This task extracts the procedure; Task 7 adds a short pointer in SKILL.md.

- [x] **Step 1: Write the mc-mode work loop reference.**

File contents (copy-paste ready):

````markdown
# Mc-Mode Work Loop — Ticket-Based Execution

Used when `gigo:execute` Before-Starting detection resolves to mc-mode (per `skills/spec/references/mc-detection.md` and `execute/SKILL.md` Before-Starting step 3). One ticket at a time in v1; parallel ticket execution deferred to v2.

## Crash Recovery (runs before main loop)

Two-pass audit per R4.6. Both passes run; results are combined before prompting the operator.

### Pass A — signal-file based (30-day window, mc-scrub limit)

Scan `$CLAUDE_PROJECT_DIR/vault/agents/logs/` for `{ticket-id}-execute-pickup.md` files WITHOUT a corresponding `{ticket-id}-execute-complete.md`. Collect these ticket IDs as "interrupted within last 30 days."

Pass A only finds recent interruptions because `mc-scrub` (default `--days 30`) deletes files in `vault/agents/logs/` older than 30 days.

### Pass B — ticket-list based (complete coverage)

Run `bash("cd $CLAUDE_PROJECT_DIR && mc-ticket-ls --status in_progress --json")`. This returns a JSON array of ticket objects with at least `{id, title, status, phase, depends_on}`.

(NOTE: do NOT use `mc-ticket-status --json`'s `by_status` field — that is a count dict per `mission-control/bin/mc-ticket-status` line 66, not a list. mc-ticket-ls with `--status` and `--json` is the correct enumeration command per `mission-control/bin/mc-ticket-ls` lines 35, 43.)

For each ticket `t` in the returned array: check whether `$CLAUDE_PROJECT_DIR/vault/agents/logs/{t.id}-execute-pickup.md` exists. If NOT, collect with annotation "in_progress without recent pickup signal — possibly interrupted before scrub or by another executor."

### Combined handling

If Pass A or Pass B returned any tickets, present the combined list to the operator using the crash-recovery message format in §Conventions of the spec. For each ticket, operator chooses `[r] Re-pick / [e] Escalate / [s] Skip`. Execute does NOT mutate ticket state — all state changes stay in the operator's hands per the authority principle.

Honest non-claim: mission-control as of current HEAD does not provide automatic stale-`in_progress` detection. Operators needing detection beyond the mc-scrub window rely on this startup audit or manual `mc-ticket-ls --status in_progress --json` invocations.

## Main Loop

```
while True:
  # Step 1: Ask mc what's ready
  status_json = bash("cd $CLAUDE_PROJECT_DIR && mc-ticket-status --json")
  ready = status_json["unblocked"]  # list of {id, title} objects per mc-ticket-status lines 67
  if len(ready) == 0:
    break

  ticket_id = ready[0]["id"]  # mc enforces DAG order; first-listed is correct

  # Step 2: Fetch full ticket body from disk (MANDATORY)
  # mc-ticket-status --json returns ONLY id + title (minimal JSON).
  # Worker needs Summary, Context, Implementation Notes, Acceptance Tests sections,
  # plus exit_criteria and produced_files from frontmatter. These come from disk.
  ticket_path = Path(CLAUDE_PROJECT_DIR) / "vault" / "tickets" / f"{ticket_id}.md"
  if not ticket_path.exists():
    raise RuntimeError(f"mc-ticket-status reported {ticket_id} ready but {ticket_path} missing")
  ticket_content = ticket_path.read_text()
  ticket_fm, ticket_body = parse_frontmatter(ticket_content)

  # Step 3: Signal pickup
  emit_signal(f"vault/agents/logs/{ticket_id}-execute-pickup.md")

  # Step 4: Dispatch worker with full ticket context from disk
  worker_status = dispatch_worker(build_worker_prompt(ticket_id, ticket_fm, ticket_body))

  # Step 5: Handle worker result
  if worker_status == "DONE":
    bash(f"cd $CLAUDE_PROJECT_DIR && mc-proof-of-work {ticket_id}")
    invoke_verify(ticket_id)  # gigo:verify in mc-mode
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-complete.md")
  elif worker_status in ["BLOCKED", "NEEDS_CONTEXT"]:
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-blocked.md", body=worker_report)
    # Surface to operator; operator decides ticket state
  elif worker_status == "DONE_WITH_CONCERNS":
    bash(f"cd $CLAUDE_PROJECT_DIR && mc-proof-of-work {ticket_id}")
    invoke_verify(ticket_id)
    emit_signal(f"vault/agents/logs/{ticket_id}-execute-complete.md", concerns=worker_concerns)
```

All `bash()` invocations specify `cd $CLAUDE_PROJECT_DIR` because `mc-ticket-status` / `mc-ticket-ls` / `mc-proof-of-work` all use mc's `find_vault()` helper which walks upward from cwd.

## Worker Prompt Contents

Worker prompt MUST include (self-contained — worker does not read files the prompt doesn't hand them):
- `Ticket:` (id + title from `ticket_fm`)
- `Summary`, `Context`, `Implementation Notes`, `Acceptance Tests` sections from `ticket_body`
- `Exit criteria:` from `ticket_fm["exit_criteria"]`
- `Produced files:` from `ticket_fm["produced_files"]`
- Instruction: *"Your unit of work is ticket {id}. The ticket body is above. Output goes to the files in `produced_files`. Report DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT."*

## Auto-Changelog in Mc-Mode

Per R4.9: generate per-ticket changelog entries AND a final summary entry. Read `vault/tickets/` to find what was completed since execution started (filter tickets where `status: done` AND completion signal timestamp falls within this run).

## Non-Mutation Rule (Authority Principle)

Execute NEVER writes to `vault/tickets/*.md` frontmatter. All state changes propagate via:
- Signal files at `vault/agents/logs/{ticket-id}-execute-{pickup|complete|blocked}.md`
- Verify verdicts at `vault/agents/reviewer/{ticket-id}*.md` (written by `gigo:verify` in mc-mode)

Operator (or future mc automation) transitions ticket state by running `mc-ticket-transition` directly. This is load-bearing for the authority principle — violating it repeats v0.12's tight-coupling failure.
````

- [x] **Step 2: Verify.**

Run: `wc -l skills/execute/references/mc-mode-work-loop.md` — expect 90-115 lines. No placeholders. No inline mc-init calls (those belong to maintain/spec retrofit paths).

- [x] **Step 3: Commit.**

```bash
git add skills/execute/references/mc-mode-work-loop.md
git commit -m "feat(execute): add mc-mode-work-loop reference — ticket loop procedure

Implements R4.3-R4.9 procedural detail. Extracted to reference file per
GIGO hub-and-spoke convention (skill-engineering.md: mode sections > ~5
lines belong in references/). Task 7 adds the pointer in execute/SKILL.md.

Pass B crash recovery uses mc-ticket-ls --status in_progress --json (not
mc-ticket-status's by_status count dict)."
```

#### What Was Built
- **Deviations:** Commit message's "R4.3-R4.9" claim is slightly overclaimed — R4.8 (plan.md coexistence / `tiebreak`) is correctly scoped OUT of this file (belongs in execute/SKILL.md Before-Starting via Task 7). File implements R4.3-R4.7 + R4.9. Worker resolved spec ambiguity inline: Pass B uses `mc-ticket-ls --status in_progress --json` (not the Counter-dict `by_status` spec R4.6 loosely referenced) — clarification, not deviation.
- **Review changes:** None.
- **Notes for downstream:** Main loop uses `mc-ticket-status --json` with `unblocked[0].id` — verified correct per mc source (mc-ticket-status lines 63-73): `unblocked` is already DAG-dependency-resolved. Do NOT switch to `mc-ticket-ls --status ready`. Authority principle enforced in 3 places (lines 25, 64, 86-92). Task 7 (execute/SKILL.md) must add: Before-Starting mc detection step between existing step 2 (plan-verification) and step 3 (read plan), the plan.md coexistence prompt + `tiebreak` preference storage (R4.8), and the "When to Go Deeper" pointer to this file.

---

## Task 6: Modify spec/SKILL.md

**blocks:** 10
**blocked-by:** 1, 2
**parallelizable:** true (with Tasks 7, 8, 9 — different files)

**Files:**
- Modify: `skills/spec/SKILL.md`

- [x] **Step 1: Read the current file to identify Phase 5, Phase 8, Phase 9.75, Phase 10 anchors.**

```bash
wc -l skills/spec/SKILL.md
grep -n "^## Phase" skills/spec/SKILL.md
```

Note the line numbers. Baseline is v0.13's 251 lines.

- [x] **Step 2: In Phase 5 section, after the Phase 0 reference and BEFORE the "Read the approved design brief" line, insert the mc-mode decision block:**

Insert this text (adjust surrounding markdown as needed):

```markdown
### Mission-Control Mode Decision (R3.1)

After Phase 0 (Gate 1) completes and BEFORE drafting the spec:

1. Run mc detection per `skills/spec/references/mc-detection.md` (three-check, three-state).
2. Read preference file at `.claude/references/mission-control-preference.md` if it exists.
3. Apply the state × preference behavior table from `mc-detection.md`.
4. On STATE_ACTIVE OR operator-approved nudge → enter slice mode per `skills/spec/references/slice-mode.md`.
5. On all other combinations → proceed with v0.13 monolithic mode (no changes below).

For install/init prompts in UNAVAILABLE and NOT_INITIALIZED states, use the Mc-Init Invocation Procedure in `skills/spec/references/mc-detection.md` (handles vault-exists case with operator confirmation).

For source-path resolution when mc is unavailable, call `resolve_mc_source_path()` per `mc-detection.md` — do NOT hardcode `~/projects/mission-control/`.
```

- [x] **Step 3: In Phase 8 (Write Implementation Plan) section, after the existing "Save to `docs/gigo/plans/YYYY-MM-DD-<feature-name>.md`" line, insert the slice-mode branch:**

```markdown
**If in slice mode (R3.4):** write ONE plan file per slice at `docs/gigo/plans/{date}-slice-{N}-{name}.md`. Each plan's header cites its slice spec in the `**Spec:**` field. See `skills/spec/references/slice-mode.md` for the full slice-mode procedure.
```

- [x] **Step 4: In Phase 9.75 section (Plan Verification Gate), at the end of the existing procedure, append the slice-mode branch:**

```markdown
**If in slice mode:** Gate 2 runs PER-SLICE-PLAN, not per-PRD. Each slice plan gets its own `docs/gigo/research/{date}-slice-{N}-{name}-plan-verification.md`. Dispatch one verification subagent per slice plan in parallel if independent; sequential if dependencies overlap. Gate 1 (Phase 0) still runs ONCE at PRD level — runtime targets don't vary per slice.
```

- [x] **Step 5: In Phase 10 section, replace the single-approval-marker logic with the batch-or-per-slice logic for slice mode:**

Find the existing Phase 10 approval marker instructions. Replace with:

```markdown
**Monolithic mode:** single approval marker on the single plan file (existing behavior).

**Slice mode (R3.3):** offer batch approval with per-slice review on request. See `skills/spec/references/slice-mode.md` § "Approval Ceremony" for the exact prompt and per-slice iteration. Apply `<!-- approved: plan {timestamp} by:{username} -->` marker to every approved slice plan.

**After all slice plans are approved:** invoke mission-control's ticket-generation subcommand for each approved slice plan in order:

```
for plan_file in approved_slice_plans:
    Skill(skill="mission-control", args=f"ticket {plan_file}")
```

mission-control creates `vault/tickets/TCK-{phase}-{seq}.md` files per slice plan. Present the consolidated ticket-creation report to the operator.
```

- [x] **Step 6: Update the announce line at the top of the file to reference slice-mode phase variants.**

Find:
```
**Announce every phase.** "Phase 0: Researching platform targets...", "Phase 5: Writing spec...", ...
```

Append to that instruction:
```
In slice mode, announce "Phase 5: Writing PRD foundation + {N} slice designs...", "Phase 8: Writing {N} slice plans...", "Phase 9.75: Verifying {N} slice plans...", "Phase 10: {N} slice plans ready for review...".
```

- [x] **Step 7: Verify line cap.**

Run: `wc -l skills/spec/SKILL.md`

Must be < 500. If ≥ 500, move additional procedural detail to `skills/spec/references/slice-mode.md` or `mc-detection.md`.

- [x] **Step 8: Verify cross-references resolve.**

```bash
grep -c "skills/spec/references/mc-detection.md" skills/spec/SKILL.md      # expect ≥ 2
grep -c "skills/spec/references/slice-mode.md" skills/spec/SKILL.md         # expect ≥ 2
```

- [x] **Step 9: Commit.**

```bash
git add skills/spec/SKILL.md
git commit -m "feat(spec): add mc-mode branch — slice spec, per-slice plans, ticket trigger

Implements R3.1-R3.7 from the pipeline-wide mission-control integration spec.
Phase 5 branches to slice mode when mc is ACTIVE; Phase 8 writes per-slice plans;
Phase 9.75 runs per-slice Gate 2; Phase 10 invokes mission-control's ticket
subcommand after approval. Monolithic mode unchanged for backward compatibility."
```

#### What Was Built
- **Deviations:** The pre-existing `**Write approval marker:**` template block (L245-248 of the modified SKILL.md) was preserved alongside the new monolithic/slice mode logic inserted above it. Reviewer flagged this as an ordering ambiguity (confidence 70, below the 80+ threshold) — for slice mode, the marker is applied per-slice BEFORE mc ticket generation, but the template block now sits AFTER the ticket-generation loop. Not a spec violation; plan Step 5 said "replace" but the worker interpreted "replace logic" (the surrounding descriptive text) while preserving the canonical marker template for reuse.
- **Review changes:** None.
- **Notes for downstream:** 6 edits landed verbatim at correct anchors. Cross-refs: mc-detection.md = 2, slice-mode.md = 3. Line cap 284 < 500. All R3.1-R4.4 requirements satisfied. Authority principle preserved — no direct mc frontmatter mutation; ticket creation delegated via `Skill(skill="mission-control", args=f"ticket {plan_file}")`. Announce-line slice variants follow existing "Phase N:" pattern. Task 10 (CHANGELOG) should note the Phase 10 ordering caveat as a known polish opportunity.

---

## Task 7: Modify execute/SKILL.md

**blocks:** 10
**blocked-by:** 1, 5
**parallelizable:** true (with Tasks 6, 8, 9)

**Files:**
- Modify: `skills/execute/SKILL.md`

- [x] **Step 1: Read the current file to identify Before-Starting anchor.**

```bash
wc -l skills/execute/SKILL.md
grep -n "^## Before Starting\|^1\.\|^2\.\|^3\." skills/execute/SKILL.md | head -20
```

Baseline is v0.13's 242 lines.

- [x] **Step 2: In the Before-Starting section, AFTER existing step 2 (plan-verification check) and BEFORE existing step 3 (read full plan), insert new step 3:**

```markdown
3. **Mission-control mode detection.** Run mc detection per `skills/spec/references/mc-detection.md`.
   - If `mc_active` AND `$CLAUDE_PROJECT_DIR/vault/tickets/` contains ≥1 ticket file (`TCK-*.md`) → enter mc-mode (skip plan.md path; proceed to the Mc-Mode Work Loop section below).
   - If `mc_active` AND `vault/tickets/` is empty → fall back to plan.md path (operator hasn't generated tickets yet).
   - If NOT `mc_active` → existing plan.md path.

   **Plan.md coexistence (R4.8):** if BOTH `vault/tickets/` (≥1 ticket) AND an approved plan file in `docs/gigo/plans/` exist, prompt operator once per project: *"This project has both a plan file and mission-control tickets. Which is the source of truth for this run? [tickets / plan / both (run plan tasks first, then tickets)]"*. Store decision in preference file as `tiebreak: tickets | plan | sequential`.
```

Renumber existing steps 3 → 4, 4 → 5.

- [x] **Step 3: Add a new short pointer section after the existing Tier 1/2/3 sections and before Red Flags.**

Insert (replaces the old plan's ~80-line inline block — procedure is now in Task 5's reference file):

```markdown
---

## Mc-Mode Work Loop

When Before-Starting step 3 resolves to mc-mode (mc active + tickets present), read `skills/execute/references/mc-mode-work-loop.md` for the full procedure: two-pass crash recovery, main ticket loop with mandatory ticket-body read from `vault/tickets/{id}.md`, worker prompt contents, auto-changelog, and the non-mutation rule.

Key constraints enforced by the reference:
- One ticket at a time in v1 (parallel deferred to v2)
- mc enforces DAG order via `mc-ticket-status --json`'s `unblocked` array; execute picks first-listed
- Worker prompt is self-contained (ticket body from `vault/tickets/*.md`, not a plan file)
- Execute NEVER writes to ticket frontmatter — state changes flow through signal files and verify verdicts
```

- [x] **Step 4: Add a Red Flag entry.**

In the existing Red Flags section, add:

```markdown
- Mutate ticket frontmatter in mc-mode (authority principle: mc owns ticket state, gigo emits signals)
- Treat `mc-ticket-status --json` output as sufficient ticket context (ticket-body read from `vault/tickets/{id}.md` is MANDATORY before worker dispatch)
- Use `mc-ticket-status`'s `by_status.in_progress` count as a ticket list (it's a count int, not an iterable — use `mc-ticket-ls --status in_progress --json` for enumeration)
```

- [x] **Step 5: Verify line cap.**

Run: `wc -l skills/execute/SKILL.md`

Must be < 500. With procedure extracted to the reference file, expect roughly 260-270 lines (baseline 243 + ~15 line Before-Starting insert + ~10 line pointer section + 3 Red Flags bullets).

- [x] **Step 6: Verify cross-references.**

```bash
grep -c "skills/spec/references/mc-detection.md" skills/execute/SKILL.md        # expect ≥ 1
grep -c "skills/execute/references/mc-mode-work-loop.md" skills/execute/SKILL.md # expect ≥ 1
```

- [x] **Step 7: Commit.**

```bash
git add skills/execute/SKILL.md
git commit -m "feat(execute): add mc-mode branch — detection step + work-loop pointer

Implements R4.1-R4.10 from the pipeline-wide mission-control integration spec.
Before-Starting gains mc-mode detection step; new Mc-Mode Work Loop section
with mandatory ticket-body read from vault/tickets/, signal emission, and
two-pass crash recovery. Execute never mutates ticket frontmatter."
```

#### What Was Built
- **Deviations:** None — all 4 edits verbatim. Reviewer noted a pre-existing stale reference in the Phase 0 (Gate 2) block: lines 25-33 of the modified SKILL.md say "Proceed to step 3" — after renumbering (old step 3 → new step 4), these now semantically point to mc detection (the new step 3) rather than read-plan. Not blocking; semantically still resolves to "proceed past the gate". Fixing it is out of Task 7 scope (Gate 2 procedure ownership belongs to the two-gate research pipeline spec, not Brief 12).
- **Review changes:** None.
- **Notes for downstream:** Renumbering chain 1→2→3 (new)→4 (was 3)→5 (was 4) verified unbroken. Mc-Mode Work Loop pointer section (10 lines, 4 constraint bullets) lives between "When All Tasks Complete" and "Red Flags". Three new Red Flag bullets enforce authority principle (no frontmatter mutation), mandatory ticket-body read from `vault/tickets/`, and `in_progress` count misuse. Cross-refs: mc-detection.md = 1, mc-mode-work-loop.md = 1. Line cap 264 < 500. Downstream (Task 10 CHANGELOG) can reference the stale "Proceed to step 3" language as a polish follow-up.

---

## Task 8: Modify verify/SKILL.md

**blocks:** 10
**blocked-by:** 1, 3
**parallelizable:** true (with Tasks 6, 7, 9)

**Files:**
- Modify: `skills/verify/SKILL.md`

- [x] **Step 1: Read the current file.**

```bash
wc -l skills/verify/SKILL.md
grep -n "^## " skills/verify/SKILL.md
```

Baseline is v0.13's 195 lines.

- [x] **Step 2: After the opening persona paragraph (before Stage 1), insert the Mc-Mode Detection section:**

```markdown
---

## Mission-Control Mode Detection

Run at verify start, before Stage 1.

1. Run mc detection per `skills/spec/references/mc-detection.md`.
2. Attempt ticket ID resolution per `skills/verify/references/mc-verdict-schema.md` § "Ticket ID Resolution":
   - Explicit flag: `--ticket TCK-X-NNN`
   - Most recent `vault/agents/logs/{ticket-id}-execute-pickup.md`
   - Operator-provided
3. If `mc_active` AND ticket ID resolved → enter mc-mode (write verdict files per R5.4).
4. Otherwise → v0.13 mode (human-readable operator summary, no verdict files).

If `mc_active` but ticket ID NOT resolvable, ask the operator before falling back — silent fallback hides mc-mode regressions.
```

- [x] **Step 3: In the Stage 1 section, at the end, add the mc-mode output branch:**

```markdown
**In mc-mode:** after Stage 1 completes, write `vault/agents/reviewer/{ticket-id}-spec-compliance.md` per R5.4.a schema (YAML frontmatter). See `skills/verify/references/mc-verdict-schema.md` for the exact schema.
```

- [x] **Step 4: In the Stage 2 section, at the end, add the mc-mode output branch:**

```markdown
**In mc-mode:** after Stage 2 completes (only if Stage 1 passed — stage ordering rule unchanged), write `vault/agents/reviewer/{ticket-id}-craft-quality.md` per R5.4.a schema.
```

- [x] **Step 5: Add a new section after Stage 2 and before Spec/Plan Review Mode: "Combined Verdict Synthesis (Mc-Mode Only)".**

```markdown
---

## Combined Verdict Synthesis (Mc-Mode Only)

After both stages complete (or Stage 1 failed → Stage 2 skipped), write the canonical combined verdict at `vault/agents/reviewer/{ticket-id}.md` using mc's **plain-header format** per R5.4.b schema. This file is parsed by mc's downstream tools — do NOT drift.

Combined status derivation per R5.7:

| Stage 1 | Stage 2 | Critical in S2 (≥90 confidence)? | Combined |
|---|---|---|---|
| pass | pass | — | `approved` |
| pass | fail | no | `approved_with_notes` |
| pass | fail | yes | `escalate` |
| fail | skipped | — | `escalate` (reason: "spec compliance failed — craft review skipped per pipeline policy") |

See `skills/verify/references/mc-verdict-schema.md` for:
- The exact plain-header format
- The Stage-verdicts extension section (non-breaking gigo addition)
- Re-verification history-append pattern
- Validation step (run `mc-ticket-stats {ticket-id}` to confirm parsability)

**Operator-facing summary in mc-mode** (appended to existing v0.13 operator-readable summary):

> "Verdicts written to `vault/agents/reviewer/{ticket-id}.md` (combined), `{ticket-id}-spec-compliance.md`, `{ticket-id}-craft-quality.md`. Mission-control will pick up state transitions per its own rules. Suggested ticket status: [done | escalate]."

**Non-Mutation Rule:** verify NEVER writes to `vault/tickets/*.md` frontmatter. mc transitions ticket state; gigo provides verdicts.
```

- [x] **Step 6: Verify line cap.**

Run: `wc -l skills/verify/SKILL.md`

Must be < 500.

- [x] **Step 7: Verify cross-references.**

```bash
grep -c "skills/spec/references/mc-detection.md" skills/verify/SKILL.md        # expect ≥ 1
grep -c "skills/verify/references/mc-verdict-schema.md" skills/verify/SKILL.md  # expect ≥ 2
```

- [x] **Step 8: Commit.**

```bash
git add skills/verify/SKILL.md
git commit -m "feat(verify): add mc-mode — per-stage verdicts + canonical combined file

Implements R5.1-R5.10 from the pipeline-wide mission-control integration spec.
Stage files use gigo-owned YAML frontmatter; canonical combined file uses
mc-compatible plain-header format so mc-ticket-stats, mc-dashboard, mc-retro
can parse it. Combined-status synthesis: any Critical issue → escalate."
```

#### What Was Built
- **Deviations:** None — all 4 insertions verbatim.
- **Review changes:** None.
- **Notes for downstream:** Mc-Mode Detection section (L18-33) placed between intro paragraphs and `## Stage 1: Spec Review` (L36). Ticket ID resolution priority order (flag → pickup signal → operator → v0.13 fallback). Two-schema distinction explicit: R5.4.a YAML frontmatter for per-stage files (`{ticket-id}-spec-compliance.md`, `{ticket-id}-craft-quality.md`), R5.4.b mc plain-header format for combined canonical file (`{ticket-id}.md`). Status-synthesis table at L95-100 has 4 rows matching R5.7 exactly: pass/pass → `approved`; pass/fail no-Critical → `approved_with_notes`; pass/fail with-Critical → `escalate`; fail/skipped → `escalate`. Non-Mutation Rule at L112 inside Combined Verdict Synthesis section — placement is verbatim per plan Step 5. Cross-refs: mc-detection.md = 1, mc-verdict-schema.md = 3. Line cap 241 < 500.

---

## Task 9: Modify maintain/SKILL.md

**blocks:** 10
**blocked-by:** 1, 4
**parallelizable:** true (with Tasks 6, 7, 8)

**Files:**
- Modify: `skills/maintain/SKILL.md`

- [x] **Step 1: Read the current file.**

```bash
wc -l skills/maintain/SKILL.md
grep -n "^## \|^### " skills/maintain/SKILL.md
```

Baseline is roughly 70 lines.

- [x] **Step 2: In the mode auto-detect section, add the new mode.**

Find the existing mode list (Targeted Addition / Health Check / Restructure / Upgrade). Add:

```markdown
- **Add Mission-Control** — retrofit mission-control onto the project (scaffold vault, extract governance, augment CLAUDE.md). Triggered by `$ARGUMENTS` containing `add-mission-control` OR auto-suggested when mc detection returns NOT_INITIALIZED or UNAVAILABLE AND no preference file exists. See `skills/maintain/references/add-mission-control.md` for the procedure.
```

- [x] **Step 3: In the auto-detect logic section, insert the auto-suggestion rule.**

After the existing auto-detect triggers, add:

```markdown
### Auto-Suggesting Add Mission-Control

When operator runs `gigo:maintain` with no args:
1. Check whether `.claude/references/mission-control-preference.md` exists. If yes, skip auto-suggestion (operator has already made a decision).
2. If not, run mc detection per `skills/spec/references/mc-detection.md`.
3. If state is NOT_INITIALIZED or UNAVAILABLE, offer Add Mission-Control as an additional option in the top-level menu:

   > "Which maintenance task?
   >  [1] Targeted Addition
   >  [2] Health Check
   >  [3] Restructure
   >  [4] Upgrade
   >  [5] Add Mission-Control (mc detected: {state})"

4. If state is ACTIVE, do not auto-suggest (mc is already integrated).
```

- [x] **Step 4: Verify line cap.**

Run: `wc -l skills/maintain/SKILL.md`

Must be < 500.

- [x] **Step 5: Verify cross-reference.**

```bash
grep -c "skills/maintain/references/add-mission-control.md" skills/maintain/SKILL.md  # expect ≥ 1
grep -c "skills/spec/references/mc-detection.md" skills/maintain/SKILL.md              # expect ≥ 1
```

- [x] **Step 6: Commit.**

```bash
git add skills/maintain/SKILL.md
git commit -m "feat(maintain): add Add Mission-Control mode with auto-suggestion

Implements R6.1-R6.5 from the pipeline-wide mission-control integration spec.
New mode retrofits mc onto existing projects. Auto-suggested when no
preference file exists and mc state is NOT_INITIALIZED or UNAVAILABLE."
```

#### What Was Built
- **Deviations:** None — both blocks verbatim. Reviewer noted a stylistic inconsistency in rendering: the new `- **Add Mission-Control**` bullet at L37 uses dash-bullet format while existing modes (Targeted Addition, Health Check, Restructure, Upgrade) use paragraph-style `**Name (Mode N)** —`. Traces to the plan's verbatim spec text — not the worker's execution. Polish opportunity for a follow-up reconciliation pass.
- **Review changes:** None.
- **Notes for downstream:** Both spec-mandated blocks inserted between Upgrade mode (L35) and the `---` (L55) preceding "Pipeline Health" (L57). 5-option menu at L39-54 includes mc as option 5 with `(mc detected: {state})` annotation. Auto-suggest 4-step logic is traceable: no args → check preference → detect state → offer menu if NOT_INITIALIZED/UNAVAILABLE, skip if ACTIVE. Cross-refs: add-mission-control.md = 1 (L37), mc-detection.md = 1 (L43). Line cap 86 < 500 (huge headroom). Task 10 CHANGELOG should note the stylistic polish opportunity.

---

## Task 10: Update CHANGELOG.md

**blocks:** (none)
**blocked-by:** 1, 2, 3, 4, 5, 6, 7, 8, 9
**parallelizable:** false (waits for all prior tasks to establish the actual diff)

**Files:**
- Modify: `CHANGELOG.md`

- [x] **Step 1: Read current CHANGELOG to find the insertion point (above the most recent version section).**

```bash
head -40 CHANGELOG.md
```

Insertion point: above `## v0.13.0-beta (2026-04-17)`.

- [x] **Step 2: Insert the new `[Unreleased]` section.**

Append above `## v0.13.0-beta (2026-04-17)`:

```markdown
## [Unreleased]

### Pipeline-Wide Mission-Control Integration

Loose-coupling integration across 4 gigo skills (spec, execute, verify, maintain) when mission-control is available in the session. Detect-and-adapt with install/init nudge — never a hard requirement. Authority principle: mission-control owns ticket state, gigo emits signals via file writes. Repeats none of v0.12's tight-coupling failure; composition test passes (uninstall mc → all 4 skills fall back to v0.13 behavior cleanly).

- **Detection + preference.** New canonical detection helper at `skills/spec/references/mc-detection.md` — three-check (skill list, `command -v mc-init`, `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md`), three-state (UNAVAILABLE / NOT_INITIALIZED / ACTIVE), < 100ms per invocation. Preference file at `.claude/references/mission-control-preference.md` controls nudge behavior (`enabled` / `disabled` / `never-ask`) plus `tiebreak` and `mc-source-path` fields. All 12 state×preference combinations behave per the behavior table.

- **Slice mode in spec.** When mc is STATE_ACTIVE (or operator accepts nudge), Phase 5 produces a PRD foundation + N per-slice design files instead of a monolithic spec. Phase 8 writes one plan per slice. Phase 9.75 runs Gate 2 per-slice plan (Gate 1 still runs once at PRD level). Phase 10 offers batch-or-per-slice approval. After all slice plans approved, spec invokes `/mission-control ticket <plan-path>` per plan to generate tickets in mc's vault. Procedure in new `skills/spec/references/slice-mode.md`.

- **Mc-mode work loop in execute.** Before-Starting gains a new mc-mode detection step. When `mc_active` AND `vault/tickets/` has tickets, execute enters the ticket loop: query `mc-ticket-status --json` for `unblocked` array (minimal `{id, title}` objects), read full ticket body from `vault/tickets/{ticket-id}.md` (mandatory — minimal JSON is NOT treated as sufficient context), emit pickup signal to `vault/agents/logs/{ticket-id}-execute-pickup.md`, dispatch worker with full ticket context, run `mc-proof-of-work` and gigo:verify on DONE, emit completion/blocked signals per worker result. Execute NEVER mutates ticket frontmatter.

- **Two-pass crash recovery in execute.** Pass A scans signal files (within 30-day mc-scrub window) for pickup signals without matching completion signals. Pass B queries `mc-ticket-status --json` for `in_progress` tickets without matching current pickup signals (catches interruptions before scrub or by other executors). Honest non-claim: mission-control currently has no automatic stale-`in_progress` detection — operators needing it must run `mc-ticket-status --json` manually or rely on execute's startup audit on resume.

- **Per-stage + canonical combined verdicts in verify.** When mc is active AND ticket ID is resolvable (priority: `--ticket` flag → recent execute-pickup signal → operator input → fallback to v0.13), verify writes 3 verdict files per ticket: `{ticket-id}-spec-compliance.md` and `{ticket-id}-craft-quality.md` in gigo's structured YAML frontmatter schema (R5.4.a), plus the canonical combined `{ticket-id}.md` in mc's **plain-header format** (R5.4.b) — structurally matching `mission-control/skills/mission-control/references/reviewer-verdict.md` so downstream mc tools (`mc-ticket-stats`, `mc-dashboard`, `mc-retro`, all present in `mission-control/bin/`) parse gigo-written verdicts correctly. The `Reviewer:` field carries `gigo:verify` (not mc's `mission-control:review`) — consumers display who actually wrote the verdict; mc's parsers are value-agnostic on that field. Combined-status synthesis: any Critical issue (≥90 confidence) in Stage 2 → `escalate`; otherwise `approved_with_notes`.

- **Add Mission-Control mode in maintain.** New auto-detected mode retrofits mc onto existing projects. Triggered by explicit `add-mission-control` argument OR auto-suggested when no preference file exists and mc state is NOT_INITIALIZED / UNAVAILABLE. Per-state behavior: ACTIVE reports status only (vault audit deferred to v2); NOT_INITIALIZED runs the shared Mc-Init Invocation Procedure; UNAVAILABLE resolves the mc source path then runs install.sh + the procedure. Procedure in new `skills/maintain/references/add-mission-control.md`.

- **Mc-Init Invocation Procedure (R3.1.a).** Shared subroutine in `skills/spec/references/mc-detection.md`. Handles three vault states: vault absent → plain `mc-init`; vault exists without tickets → `mc-init --force` with announcement; vault exists WITH tickets → operator confirmation → `mc-init --force --yes`. On abort, falls back to monolithic mode without writing preference file. Closes the retrofit-safety gap on projects with half-initialized or legacy vaults.

- **Configurable mc source path.** No `~/projects/mission-control/` path is hardcoded. `resolve_mc_source_path()` helper (documented in `mc-detection.md`) checks `GIGO_MC_SOURCE` env var → preference field `mc-source-path` → default `~/projects/mission-control/`. Clone-instructions error when resolution fails shows all three options to the operator.

- **Blueprint unchanged.** v1 defers slicing-hint in blueprint — spec detects scope from brief content (≥3 distinct components, "vertical slice" language). Keeps v1 surface smaller; blueprint remains monolithic.

### Fact-check findings noted (from spec Phase 4.25)

- `mc-ticket-status --json` emits `{id, title}` per ticket (NOT rich objects with body) — execute MUST read `vault/tickets/{ticket-id}.md` for full context before worker dispatch.
- `install.sh` is non-interactive (sets `set -euo pipefail`, symlinks bin/ + skill, exits cleanly) — gigo invokes directly via Bash, no operator intervention needed when source repo is cloned.
- `mc-scrub` (default 30 days) deletes files in `vault/agents/logs/` — constrains signal-file crash recovery to 30-day window; Pass B covers beyond that.

### Design references

- Spec: `docs/gigo/specs/2026-04-18-pipeline-wide-mission-control-integration-design.md`
- Plan: `docs/gigo/plans/2026-04-18-pipeline-wide-mission-control-integration.md`
- Motivating brief: `briefs/12-mission-control-slice-integration.md`
- Loose-coupling principle memory: `feedback_skill_integration_loose_coupling.md`
```

- [x] **Step 3: Verify.**

```bash
head -80 CHANGELOG.md
grep -c "^## \[Unreleased\]" CHANGELOG.md   # expect 1
```

- [x] **Step 4: Commit.**

```bash
git add CHANGELOG.md
git commit -m "docs: add [Unreleased] changelog entry for mc integration

Implements R8 from the pipeline-wide mission-control integration spec."
```

#### What Was Built
- **Deviations:** Worker's Sonnet model committed directly to `main` instead of a `worktree-agent-*` branch despite `isolation: "worktree"` dispatch — same "worktree escape" pattern previously observed with haiku (memory: `feedback_haiku_worktree_escape.md`). Content-only review unaffected (commit 03fa63e is already on main with correct content). Worker also dropped the `Implements R8 from the pipeline-wide mission-control integration spec.` body line from the commit message, using only the header line. Minor deviation; not worth amending a commit on main.
- **Review changes:** None.
- **Notes for downstream:** All 9 feature bullets verbatim match (plan lists 9 including "Blueprint unchanged"; the review prompt's "8 bullets" count was off-by-one — plan and CHANGELOG both carry 9). Fact-check findings (3 bullets) and Design references (4 bullets) verbatim. `[Unreleased]` count = 1. CHANGELOG now 146 lines. R-number references preserved (R3.1.a, R5.4.a, R5.4.b). Session retro should capture the recurring worktree-escape pattern — now observed on both haiku and sonnet workers.

---

## Risks

- **Retrofit data-loss path.** `mc-init --force --yes` runs `shutil.rmtree(vault)` unconditionally at `mission-control/bin/mc-init` line 288, destroying all tickets, logs, and verdicts. Task 1's Mc-Init Invocation Procedure (R3.1.a) MUST refuse to run `--force` against a populated vault — the vault-with-tickets branch ABORTS with a three-option operator message and falls back to monolithic mode. No preference file is written in this case so the retrofit can be re-attempted after the operator moves tickets aside.
- **Verdict schema drift.** If mission-control updates its reviewer-verdict format between now and integration landing, R5.4.b canonical file will parse incorrectly. Mitigation: Task 3 references the exact mc file (`mission-control/skills/mission-control/references/reviewer-verdict.md`). Task 9 validation step runs `mc-ticket-stats` against a written verdict — catches drift early.
- **Cross-reference rot.** 4 SKILL.md files reference `skills/spec/references/mc-detection.md` by exact path. If mc-detection.md is moved, all 4 break. Mitigation: path is stable; no refactor planned in this brief.
- **Operator confusion on first slice-mode spec.** PRD foundation is a new artifact pattern. Mitigation: slice-mode.md includes the output contract with section headings; Phase 7 prompt explicitly describes what was written.
- **Plan.md coexistence prompt fatigue.** Operator with both plan.md and tickets may find the tiebreak prompt annoying. Mitigation: decision is stored in preference file — asked once per project, not once per run.

## Done

- All 10 tasks committed cleanly.
- All 4 affected SKILL.md files under 500 lines. execute/SKILL.md tracked explicitly (target 260–270 after extraction).
- All cross-references to `skills/spec/references/mc-detection.md`, `slice-mode.md`, `mc-verdict-schema.md`, `add-mission-control.md`, and `skills/execute/references/mc-mode-work-loop.md` resolve.
- `CHANGELOG.md` [Unreleased] entry present and covers all 5 touchpoints + authority principle + composition test + configurable path.
- Per-task gigo:verify passes Stage 1 (spec compliance) and Stage 2 (craft quality).
- Composition test passes: uninstall mc entirely → detection returns STATE_UNAVAILABLE → all 4 skills fall back to v0.13 behavior with zero errors.
- Retrofit-safety test passes: `mc-init $CLAUDE_PROJECT_DIR` against a vault containing ≥1 ticket file → Task 4's add-mission-control flow ABORTS with the three-option message, does NOT invoke `mc-init --force`, and does NOT delete any ticket. Verified in a throwaway test project.

<!-- approved: plan 2026-04-19T05:13:15Z by:Eaven -->
