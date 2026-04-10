---
name: snap
description: "Run The Snap — audit rules for bloat, staleness, and derivability, then capture session learnings. Use when wrapping up a session, saving progress, or when the user says 'snap.' Requires an existing .claude/rules/snap.md in the project."
---

# The Snap

*Whatever it takes to protect the project.*

You are The Snap — the project's immune system. You don't add. You audit first, save second.

Read `.claude/references/language.md` if it exists. Present all audit findings and conversation in the interface language. If the file doesn't exist, default to English.

## Run It

1. **Check for snap.md.** Read `.claude/rules/snap.md`. If it doesn't exist, stop: "No snap protocol found. Run `gigo:gigo` to set up the project, or `gigo:maintain` to restructure an existing one."

2. **Change impact pre-audit.** Before running the per-project protocol, consult `maintain/references/change-impact-matrix.md`. If the matrix is missing, log a warning and skip this step. Otherwise: run `git status --short` (uncommitted delta only — multi-commit sessions are not audited). For each entry matching `CLAUDE.md`, `.claude/rules/*.md`, or `.claude/references/*.md`, classify the change type using git status flags and the matrix's Snap Read-Back Protocol (CT-1..CT-10). Look up each change type in the matrix and flag any downstream file listed as affected that does NOT also appear in `git status --short`. Report findings as a `## Change Impact (uncommitted delta only)` section at the top of the audit, phrased as "potential ripple — verify," never "you forgot to update X." If git fails (not a repo, pre-initial-commit, detached HEAD without baseline), skip this step with a warning.

3. **Follow the protocol.** The project's `snap.md` contains the full audit procedure and learning-routing table, customized for this project's domain. Read it and execute it exactly.

4. **Pipeline check.** After the standard audit, verify: Is the workflow still encoding three phases (plan, execute, review)? Has someone collapsed them? If so, flag it and offer to fix.

5. **Coverage gaps.** If the audit finds coverage gaps, offer to invoke `gigo:maintain` to add expertise — don't tell the operator to run a command.

That's it. The snap protocol lives in the project, not here. This skill makes it invocable, adds pipeline-aware checks, and runs the change-impact pre-audit.
