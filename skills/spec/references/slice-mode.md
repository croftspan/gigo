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
