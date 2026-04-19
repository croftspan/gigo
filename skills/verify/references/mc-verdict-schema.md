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
