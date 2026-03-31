# Changelog

## [Unreleased]

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
