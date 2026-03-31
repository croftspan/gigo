# Pipeline v2 — Master Brief

Everything that needs to happen for the next major version. Consolidates intent-fidelity, proportionality, audit, and undocumented items.

## Already Shipped (v0.10.0-beta)

- Blueprint 303 → 182 lines (phases 5-10 to reference file)
- Team routing OFF by default
- Challenger scaling (large tasks only)
- Fact-checker scaling (existing codebases only)
- Assembly quick mode (training knowledge default, no web search)
- Resume detection reverted (trigger-based, not eager)
- Execute worktree fallback (subagents without worktrees before inline)
- Troubleshooting docs + marketplace.json version sync

---

## The Build

### 1. Pipeline Split (4 skills)

Currently blueprint owns 11 phases. Split into skills with one job each:

| Skill | Input | Output | Handoff |
|---|---|---|---|
| `/blueprint` | User's idea | Approved design brief | "Want me to run /spec now?" |
| `/spec` | Approved brief | Approved spec + implementation plan | "Want me to run /execute now?" |
| `/execute` | Approved plan | Built code | "Want me to run /verify now?" or "/audit for a deep sweep?" |
| `/verify` | Any work | Review findings | (terminal) |

Each skill reads its input artifact from disk, not from conversation memory. Any step can be a session boundary. Users can enter at any point with their own artifact.

**Handoff behavior:** Each skill saves its artifact, then asks "Want me to run /[next] now?" Yes = invoke directly. No = file persists for later.

**Files:**
- `skills/blueprint/SKILL.md` — strip to Phases 0-4.5 only (design brief)
- `skills/blueprint/references/formal-phases.md` — delete (absorbed into spec)
- New: `skills/spec/SKILL.md` — spec + plan writing, self-review, challenger
- `skills/execute/SKILL.md` — remove plan writing, just reads plan and builds
- `skills/verify/` — unchanged

### 2. Intent Fidelity (3 fixes, applied during pipeline split)

**Fix 1: Intent anchor.** User's original prompt quoted verbatim at top of every spec under `## Original Request`. After writing requirements, trace each action verb to a requirement. Missing verb = gap flagged before proceeding.

**Fix 2: Challenger escalation.** When Challenger Pass 2 (intent alignment) finds drift, it's a hard stop — operator must see the mismatch and decide. Agent cannot proceed with unresolved intent mismatch.

**Fix 3: Verb-listing before design.** Before proposing approaches in blueprint, list the user's action verbs explicitly. Each approach must account for every verb. Dropped verbs must be justified.

### 3. Assembly Flow

`/gigo` scans the project first, assembles a team from what it finds, THEN asks what the user wants to build. The task prompt comes after assembly, not during. This prevents the assembly from biasing the team toward a pre-conditioned interpretation.

Step 7 handoff already offers `/blueprint`. No change needed — just ensure assembly doesn't require a task description upfront.

### 4. Audit Command (new skill)

`/audit` dispatches 3 parallel subagents:
- **Security** — injection, auth, secrets, OWASP
- **Stubs** — TODO/FIXME, placeholder returns, mock data, empty catches
- **Code quality** — dead code, inconsistent patterns, missing error handling, duplication

All parallel, findings consolidated by severity. Works standalone or offered after execute completes.

**Files:** New: `skills/audit/SKILL.md` + `skills/audit/references/` for each auditor prompt template.

### 5. Auto-Changelog After Execute

After execute completes all tasks and verify passes, auto-generate a changelog entry. Reads approved spec + actual git diff to ground the entry in what was built, not what was planned. Appends to project root `CHANGELOG.md`. Keep a Changelog format.

**Where it lives:** End of execute flow, after all tasks pass verify.

### 6. Skill Count Update

| Current (7) | v2 (8) |
|---|---|
| gigo | gigo (unchanged) |
| maintain | maintain (unchanged) |
| blueprint | blueprint (stripped to brief only) |
| execute | execute (minus plan writing) |
| verify | verify (unchanged) |
| snap | snap (unchanged) |
| retro | retro (unchanged) |
| — | **spec** (new: spec + plan writing) |
| — | **audit** (new: 3 parallel auditors) |

Total: 9 skills. But blueprint and execute both get simpler, so net complexity is lower.

README, site, and skill descriptions all need updating to reflect the new count and flow.

---

### 7. Verbosity Control

Skills narrate too much — phase announcements with explanations, "let me read...", post-phase summaries, insight blocks. Burns tokens in context for no user value.

**Config:** `.claude/references/verbosity.md`
```markdown
# Verbosity
level: minimal
```

**Levels:**
- `minimal` (default) — phase number only ("Phase 3"), no narration between tool calls, no summaries of completed work, no insight blocks
- `verbose` — current behavior with full announcements, explanations, educational insights

**Set during assembly** as a question alongside persona style and language. Skippable — defaults to minimal.

**All skills check this file** before generating output. If missing, default to minimal.

## Build Order

1. **Pipeline split** (blueprint strip + new spec skill + execute adjustment) — this is the core architecture change. Everything else layers on top.
2. **Intent fidelity fixes** — applied during the pipeline split, not separately.
3. **Verbosity control** — applied during the pipeline split, small addition to each skill.
4. **Audit command** — independent, can be built in parallel.
5. **Auto-changelog** — small addition to execute, can be last.
6. **README/site/docs update** — after everything works.

## Validation

Run Carlos's exact prompt against a fresh project:
> "I want to build a solution to explore and evaluate the substances data available at the substances folder. The idea is to iterate over the substances, merge, group, classify, anything that may help make the substances database into a better source of information."

**Pass criteria:**
- Assembly: under 5 min, no unnecessary web search
- Blueprint: under 10 min, brief captures merge/group/classify as user-facing actions
- Spec: spec has requirements for write operations, not just read-only viewer
- Plan: implementation plan includes POST/PUT endpoints and action UI
- Execute: built code has merge, group, classify features the user can interact with
- Total: under 30 min end-to-end
