# Pipeline v2 — Design Spec

**Design brief:** `docs/gigo/briefs/2026-03-31-pipeline-v2-master.md`

## Original Request

> Implement the pipeline v2 changes documented in docs/gigo/briefs/2026-03-31-pipeline-v2-master.md. The design is approved — I need a spec and implementation plan.

---

## Overview

Split the monolithic blueprint skill (11 phases) into 4 focused skills with artifact-based handoff. Add an `/audit` skill for post-build code sweeps. Add auto-changelog generation after successful execution. Apply three intent-fidelity fixes across the pipeline. Update all references to reflect 9 skills instead of 7.

---

## 1. Pipeline Split

### 1.1 Blueprint (stripped to design brief only)

**Current state:** `skills/blueprint/SKILL.md` (182 lines) owns Phases 0-11 — design brief through execution handoff. References `formal-phases.md` for Phases 5-10 procedural details.

**Target state:** Blueprint owns Phases 0-4.5 only — from "I have an idea" to "approved design brief." After approval, it asks "Want me to run /spec now?" and invokes `gigo:spec` if yes.

**Changes to `skills/blueprint/SKILL.md`:**
- Remove the "Phases 5-10: Formalize and Review" section (lines 135-148)
- Remove Phase 11 (lines 150-154)
- Update the "Post-Approval: What Happens Next" template in Phase 4.5 to reflect the new flow: next step is `/spec`, not "Phase 5"
- Update the "Announce every phase" line to list only Phases 0-4
- Update the "Scale to the Task" section: small tasks still skip to plan writing, but that now happens inside `/spec`, not blueprint
- Update the frontmatter description: remove "write specs, and produce ordered implementation plans" — blueprint only produces design briefs
- Add handoff behavior: after operator approves the brief, ask "Want me to run /spec now?" Yes → invoke `gigo:spec`. No → file persists for later.

**Reference files:**
- Delete `skills/blueprint/references/formal-phases.md` — its content moves into the new spec skill
- Keep `skills/blueprint/references/fact-checker-prompt.md` — still used by Phase 4.25
- Move `skills/blueprint/references/planning-procedure.md` to `skills/spec/references/planning-procedure.md`
- Move `skills/blueprint/references/example-plan.md` to `skills/spec/references/example-plan.md`

### 1.2 Spec (new skill)

**Purpose:** Formalize an approved design brief into a spec and implementation plan, with self-review and optional Challenger review at each stage.

**Create `skills/spec/SKILL.md`** with this structure:

**Frontmatter:**
```yaml
name: spec
description: "Formalize an approved design brief into a spec and implementation plan. Self-reviews both, runs Challenger for large tasks. Use after gigo:blueprint produces an approved brief, or when you have your own design brief to formalize. Use gigo:spec."
```

**Input:** An approved design brief. The skill locates it by:
1. Checking conversation context for a path (passed by blueprint's handoff)
2. Scanning `.claude/plans/` for the most recent file with `<!-- approved: design-brief` marker
3. If neither found: ask the operator to point to the brief

**Phases absorbed from blueprint:**
- Phase 5: Write spec — formalize brief into `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`
- Phase 6: Self-review spec — placeholder scan, consistency, ambiguity, bare-worker test
- Phase 6.5: Challenger spec review — large tasks only, dispatched via `gigo:verify`'s `references/spec-plan-reviewer-prompt.md`
- Phase 7: Operator reviews spec — wait for approval, write `<!-- approved: spec [timestamp] by:[name] -->` marker
- Phase 8: Write implementation plan — break spec into tasks, save to `docs/gigo/plans/YYYY-MM-DD-<feature>.md`
- Phase 9: Self-review plan — spec coverage, placeholder scan, type consistency
- Phase 9.5: Challenger plan review — large tasks only
- Phase 10: Operator reviews plan — write `<!-- approved: plan [timestamp] by:[name] -->` marker

**Handoff:** After the plan is approved, ask "Want me to run /execute now?" Yes → invoke `gigo:execute`. No → file persists.

**Phase announcements:** "Phase 5: Writing spec...", "Phase 6: Self-reviewing spec...", etc.

**Language handling:** Read `.claude/references/language.md`. Conduct conversation in interface language. Spec language rules from `formal-phases.md` Phase 5 apply.

**Scale to task:** Small tasks skip Challenger (6.5/9.5). Medium tasks use self-review only, Challenger on request. Large tasks run both.

**Auto-Gap-Detection:** Inherited from blueprint — if the team lacks expertise for the spec domain, offer `gigo:maintain`.

**Reference files:**
- `skills/spec/references/planning-procedure.md` — moved from blueprint
- `skills/spec/references/example-plan.md` — moved from blueprint

### 1.3 Execute (adjusted)

**Current state:** `skills/execute/SKILL.md` (210 lines) reads an approved plan and dispatches workers.

**Target state:** No plan-writing responsibility (it never had any — this is already correct). Add two new behaviors:

**Change 1: Handoff after completion.** After all tasks complete and the final synthesis is reported, ask: "Want me to run /verify in PR mode for the final gate? Or /audit for a deep code sweep?"

**Change 2: Auto-changelog.** After all tasks complete AND verify passes (both stages), auto-generate a changelog entry. Details in Section 5.

**No other changes to execute's core flow.** The brief says "remove plan writing" but execute already doesn't write plans — it reads them. Confirmed by reading the current SKILL.md.

### 1.4 Verify (unchanged)

No changes to `skills/verify/SKILL.md` or its references. The Challenger review mode is already dispatched by the calling skill — currently blueprint's formal-phases, moving to the new spec skill. Verify doesn't need to know which skill invoked it.

---

## 2. Intent Fidelity (3 fixes)

### 2.1 Fix 1: Intent Anchor

**Where:** New spec skill, Phase 5 (write spec).

Every spec starts with an `## Original Request` section containing the user's original prompt quoted verbatim. After writing the `## Requirements` section, the spec skill traces each action verb from the original request to a requirement. Missing verbs are flagged before proceeding.

**Format in spec document:**
```markdown
## Original Request

> [user's exact words]

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| explore | R1: Data exploration view | ✅ |
| evaluate | R2: Quality scoring | ✅ |
| merge | R3: Merge operation | ✅ |
| group | R4: Grouping interface | ✅ |
| classify | R5: Classification pipeline | ✅ |
```

If any verb has no corresponding requirement, the spec skill flags it:
> "⚠️ The original request mentions '[verb]' but no requirement covers it. Add a requirement, or justify why it's intentionally excluded."

The spec skill does NOT proceed to Phase 6 (self-review) with unresolved verb gaps.

### 2.2 Fix 2: Challenger Escalation

**Where:** Verify skill's Challenger mode (already exists in `references/spec-plan-reviewer-prompt.md`).

When the Challenger's Pass 2 (intent alignment) reports "No" or "Partially" for "Does this solve the stated problem?", this becomes a hard stop. The spec skill must:
1. Present the mismatch to the operator
2. Wait for the operator's decision: revise the spec, override the finding, or rethink
3. NOT proceed with an unresolved intent mismatch

**Implementation:** Add this rule to the new spec skill's Phase 6.5 handling. The Challenger prompt template itself already checks intent alignment in Pass 2 — the change is in how the invoking skill (spec) handles the verdict.

### 2.3 Fix 3: Verb-Listing Before Design

**Where:** Blueprint SKILL.md, Phase 3 (Propose Approaches).

Before proposing approaches, blueprint lists the user's action verbs explicitly:

```
Action verbs from your request: explore, evaluate, merge, group, classify

Each approach below accounts for all verbs. If an approach drops a verb, I'll explain why.
```

Each proposed approach includes a verb coverage check. Dropped verbs require justification. This catches intent drift before the design brief is even written.

---

## 3. Assembly Flow

**Where:** `skills/gigo/SKILL.md`, Step 1 and Step 7.

**Change:** Assembly scans the project and builds the team FIRST, then asks what the user wants to build. Currently, the operator's task description comes during assembly (Step 1: "Listen and Ask"). The change separates team assembly from task definition.

**How:** Step 1 still listens to the initial description — but if the operator provides a task alongside "set up my project," the task is captured but not used to bias team composition. Assembly completes based on the project's domain, not a specific task.

Step 7 handoff already offers `/blueprint` with a synthesized prompt. No change needed to Step 7 mechanics — just ensure Step 1 doesn't require a task description upfront. If the operator says "gigo" without describing a task, assembly proceeds with project-scanning alone.

**Concrete change:** In Step 1's intro paragraph, add: "If the operator provides a task description alongside setup, capture it for the Step 7 handoff prompt but don't let it bias team composition. If they don't provide a task, proceed with project-scanning alone." This is a 2-line addition, not a restructure.

---

## 4. Audit Command (new skill)

### 4.1 Skill Structure

**Create `skills/audit/SKILL.md`** with this structure:

**Frontmatter:**
```yaml
name: audit
description: "Deep code audit — dispatches 3 parallel focused auditors for security, stubs, and code quality. Works standalone or offered after gigo:execute completes. Use gigo:audit."
```

**Behavior:** Dispatches 3 subagents in parallel:
1. **Security auditor** — injection vulnerabilities, authentication/authorization gaps, secrets in code, OWASP Top 10
2. **Stubs auditor** — TODO/FIXME comments, placeholder return values, mock data in production code, empty catch blocks, stub implementations
3. **Code quality auditor** — dead code, inconsistent patterns, missing error handling at system boundaries, duplication, unused imports

**Input:** Works on the current project state. No plan or spec required. Can target specific directories or file patterns if the operator specifies.

**Output:** Consolidated findings by severity:
- **Critical** — security vulnerabilities, exposed secrets
- **High** — stub implementations that could reach production, auth gaps
- **Medium** — code quality issues, minor inconsistencies
- **Low** — style issues, minor cleanup opportunities

Each finding includes: file path, line number, description, suggested fix.

**Phase announcements:** "Dispatching 3 parallel auditors: security, stubs, code quality...", "Security audit complete. Stubs audit complete. Code quality complete.", "Consolidating findings..."

### 4.2 Reference Files

Create 3 prompt templates in `skills/audit/references/`:

**`security-auditor-prompt.md`** — Template for the security subagent. Checks:
- SQL/NoSQL injection
- XSS (reflected, stored, DOM-based)
- Command injection
- Path traversal
- Authentication bypass
- Authorization gaps (IDOR, privilege escalation)
- Secrets in code (API keys, passwords, tokens)
- Insecure dependencies (if lockfile available)
- CSRF protection
- Insecure deserialization

**`stubs-auditor-prompt.md`** — Template for the stubs subagent. Checks:
- TODO/FIXME/HACK/XXX comments
- Functions returning hardcoded values or empty results
- Mock/fake data outside test directories
- Empty catch/except blocks
- `pass` statements in non-abstract methods
- `NotImplementedError` raises outside abstract base classes
- Commented-out code blocks (> 3 lines)

**`quality-auditor-prompt.md`** — Template for the code quality subagent. Checks:
- Dead code (unreachable branches, unused functions/variables)
- Inconsistent error handling patterns
- Missing error handling at system boundaries (user input, external APIs, file I/O)
- Code duplication (> 10 lines of near-identical code)
- Unused imports
- Overly complex functions (> 50 lines or > 5 levels of nesting)
- Inconsistent naming conventions

### 4.3 Integration with Execute

After the "When All Tasks Complete" section in `skills/execute/SKILL.md`, the handoff offers audit as an option alongside verify PR mode.

---

## 5. Auto-Changelog After Execute

**Where:** `skills/execute/SKILL.md`, at the end of the "When All Tasks Complete" section.

**Trigger:** After all tasks complete AND the operator doesn't request further review (or review passes).

**Procedure:**
1. Read the approved spec from `docs/gigo/specs/` (linked in the plan header)
2. Read the git diff since execution started (first task's parent commit to HEAD)
3. Generate a changelog entry grounded in both — what was specified (spec) and what was actually built (diff)
4. Append to project root `CHANGELOG.md` in Keep a Changelog format
5. If no `CHANGELOG.md` exists, create it with the standard header

**Format:**
```markdown
## [version] (YYYY-MM-DD)

### Added
- [feature descriptions from spec + diff]

### Changed
- [modification descriptions]

### Fixed
- [bug fix descriptions]
```

The version field is left as `[Unreleased]` unless the operator specifies a version. The date is the current date.

**Grounding rule:** The changelog entry describes what was BUILT (from the diff), not what was PLANNED (from the spec). The spec provides the "why" context, the diff provides the "what" facts.

---

## 6. Skill Count and Documentation Updates

### 6.1 Skill Count

| Current (7) | v2 (9) | Change |
|---|---|---|
| gigo | gigo | unchanged |
| maintain | maintain | unchanged |
| blueprint | blueprint | stripped to brief only |
| execute | execute | + handoff, + auto-changelog |
| verify | verify | unchanged |
| snap | snap | unchanged |
| retro | retro | unchanged |
| — | **spec** | new: spec + plan writing + review |
| — | **audit** | new: 3 parallel auditors |

### 6.2 Files That Need Updating

- `CLAUDE.md` — Update "Seven skills" to "Nine skills" in Quick Reference, add `gigo:spec` and `gigo:audit` descriptions
- `skills/gigo/SKILL.md` — Update Step 7 handoff table to include `/spec` and `/audit`
- `.claude/references/pipeline-architecture.md` — Update the pipeline phases table to reflect the split
- `CHANGELOG.md` — Entry for v2 changes (auto-generated if auto-changelog lands, otherwise manual)
- Plugin metadata files (if they exist) — update skill count

### 6.3 Handoff Table (new, replaces blueprint's Phase 11)

The pipeline's handoff chain:

```
/blueprint → approved brief → "Want me to run /spec now?"
/spec → approved plan → "Want me to run /execute now?"
/execute → built code → "Want me to run /verify in PR mode? Or /audit for a deep sweep?"
/verify → review findings → (terminal)
/audit → audit findings → (terminal)
```

Each skill saves its artifact to disk before offering the handoff. Any step can be a session boundary. Users can enter at any point with their own artifact.

---

## Conventions

- **Skill file location:** All writes go to `~/projects/gigo/skills/` (source repo), never to `~/.claude/plugins/` (install path). Per dogfooding guard in `.claude/rules/dogfooding.md`.
- **SKILL.md line budget:** Under 500 lines per hub file. Procedural depth in `references/` spoke files.
- **Phase announcements:** Every skill announces phases as it works. Format: "Phase N: [description]..."
- **Artifact paths:** Specs to `docs/gigo/specs/YYYY-MM-DD-<topic>-design.md`. Plans to `docs/gigo/plans/YYYY-MM-DD-<feature>.md`. Design briefs to `.claude/plans/`.
- **Approval markers:** HTML comment format `<!-- approved: [type] [ISO timestamp] by:[git username] -->`. Gate-checked before dependent phases proceed.
- **Handoff pattern:** Save artifact → ask "Want me to run /[next] now?" → Yes = invoke directly, No = file persists.
- **Prompt templates:** Subagent prompts live in `references/` directories, not inline in SKILL.md. Dispatching code reads the template and fills placeholders.
- **Language handling:** Skills read `.claude/references/language.md` for interface and output languages. Worker prompts stay in English.
