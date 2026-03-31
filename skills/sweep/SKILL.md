---
name: sweep
description: "Deep code sweep — dispatches 3 parallel focused auditors for security, stubs, and code quality. Works standalone or offered after gigo:execute completes. Use gigo:sweep."
---

# Audit

Three parallel auditors, each focused on one lens. Consolidated findings by severity. No character voice.

**Announce every phase.** "Dispatching 3 parallel auditors: security, stubs, code quality...", "All audits complete. Consolidating findings..."

Read `.claude/references/language.md` if it exists. Conduct all operator-facing conversation in the interface language. Auditor subagents operate in English. If the file doesn't exist, default to English.

Read `.claude/references/verbosity.md` if it exists. If `level: minimal`, announce dispatch and consolidated results only — skip per-auditor progress updates. If `level: verbose` or the file doesn't exist, narrate each auditor's progress. Default to minimal.

---

## Before Starting

1. **Determine scope.** If the operator specified directories or file patterns, scope the audit to those. Otherwise, audit the entire project.
2. **Skip non-code.** Exclude `node_modules/`, `vendor/`, `.git/`, build artifacts, and binary files.

---

## Dispatch

Dispatch all 3 auditors in a single message (parallel):

1. **Security auditor** — read `references/security-auditor-prompt.md`, fill `{SCOPE}` with the target files/directories, dispatch via `Agent` with `subagent_type: "general-purpose"`.
2. **Stubs auditor** — read `references/stubs-auditor-prompt.md`, same dispatch pattern.
3. **Code quality auditor** — read `references/quality-auditor-prompt.md`, same dispatch pattern.

Each auditor returns a structured list of findings with file paths, line numbers, descriptions, and suggested fixes.

---

## Consolidate

After all 3 auditors complete:

1. **Deduplicate.** Same file + same line + overlapping description = one finding. Keep the most specific version.
2. **Classify by severity:**
   - **Critical** — security vulnerabilities, exposed secrets, authentication bypass
   - **High** — stub implementations reachable in production, authorization gaps, empty error handlers in critical paths
   - **Medium** — code quality issues, minor inconsistencies, non-critical dead code
   - **Low** — style issues, minor cleanup, informational

3. **Present to operator** in severity order. Each finding includes:
   - Severity tag
   - Source auditor (security / stubs / quality)
   - File path and line number
   - Description
   - Suggested fix

---

## Output Format

```
## Audit Results

### Critical (N)
1. **[security]** `src/auth/login.ts:45` — SQL injection in user lookup. Use parameterized query.

### High (N)
1. **[stubs]** `src/api/payments.ts:123` — Returns hardcoded `{status: "ok"}`. Stub reachable in production.

### Medium (N)
...

### Low (N)
...

**Summary:** N critical, N high, N medium, N low across N files.
```

If no findings in a severity category, omit that section.

---

## Standalone vs Post-Execute

**Standalone:** Operator invokes `/sweep` directly. Run on current project state.

**Post-execute:** Offered by gigo:execute after all tasks complete. Can scope to only files changed during execution (via git diff from first task commit to HEAD).
