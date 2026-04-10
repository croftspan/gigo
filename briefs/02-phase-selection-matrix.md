# Brief: Phase Selection Matrix for gigo:maintain

## Origin

Competitive analysis of [revfactory/harness](https://github.com/revfactory/harness). Their Phase 0 includes a "Phase Selection Matrix" — a table showing which phases to run based on what changed (agent added, skill modified, architecture change). Clean UX pattern that prevents re-running the entire workflow when only part of the setup changed.

## The Problem

`gigo:maintain` currently handles five modes: health check, targeted addition, restructure, upgrade, and triage. But when an operator says "add a persona" or "restructure the rules," maintain runs its full mode procedure without a clear signal of what downstream work is affected.

Example: operator adds a new persona. Currently maintain handles the persona addition, but doesn't explicitly signal that:
- `review-criteria.md` needs regeneration (new quality bars)
- `snap.md` persona calibration check now covers one more entry
- The Snap's coverage check might already have flagged this gap

There's no decision aid showing "you changed X, so Y and Z need updating too."

## What to Build

A decision matrix (probably in a reference file for `gigo:maintain`) that maps change types to downstream effects. Not a rigid "always re-run these phases" system — a reference that maintain consults to offer the operator a clear "here's what else is affected" summary.

## Harness's Matrix (for reference)

| Change Type | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|---|---|---|---|---|---|---|
| Agent added | Skip | Placement only | Required | If dedicated skill needed | Modify orchestrator | Required |
| Skill added/modified | Skip | Skip | Skip | Required | If connections change | Required |
| Architecture change | Skip | Required | Affected agents only | Affected skills only | Required | Required |

## GIGO-Native Version (proposed shape)

| Change Type | CLAUDE.md | rules/ | references/ | review-criteria.md | Snap audit |
|---|---|---|---|---|---|
| Persona added | Update team section | Check line caps | Update authorities.md if new research | Regenerate (new quality bars) | Run coverage + calibration checks |
| Persona modified | Update entry | No change | Update if authority research changed | Regenerate if quality bars changed | Run calibration check |
| Persona removed | Remove entry | Check for orphaned rules | Archive authority notes | Regenerate | Run calibration check |
| Rule added/modified | No change | Direct edit | Move to ref if approaching cap | No change | Run line + derivability checks |
| Reference added | No change | Add "When to Go Deeper" pointer | Direct write | No change | No change |
| Extension file added | No change | No change | No change | Check if new criteria apply | Run coverage check |
| Pipeline change | No change | Update workflow.md | Update pipeline-architecture.md | No change | Run pipeline check |

## Where It Lands

- **Primary:** `gigo:maintain` — the matrix becomes a reference file that maintain reads when determining what downstream effects a change has.
- **Secondary:** `gigo:snap` — the audit could use the matrix in reverse: "these files changed since last snap, here's what might be stale."

## Constraints

- Must not add procedural weight to maintain's SKILL.md (currently a lean 68 lines). The matrix belongs in a reference file.
- Must be a decision aid, not a mandate. The operator sees "here's what's affected" and decides what to update.
- Should cover the actual change types that happen in GIGO projects, not hypothetical ones.

## Open Questions

- Should maintain automatically offer to run the downstream updates, or just report them?
- Does the Snap already catch most of these via its 14-point audit? If so, the matrix might be redundant with the Snap — or it might be the "proactive" version of what Snap catches "reactively."
- Should this extend to detecting drift? e.g., "persona X's quality bars mention 'accessibility' but review-criteria.md has no accessibility criteria"

---

**Superseded:** This exploratory brief was formalized into the approved design brief at `.claude/plans/typed-yawning-dahl.md` and spec at `docs/gigo/specs/2026-04-10-phase-selection-matrix-design.md` on 2026-04-10. See those files for the approved design and implementation plan.
