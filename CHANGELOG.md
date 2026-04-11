# Changelog

## [Unreleased]

### Review Pipeline

- **Boundary coherence checking.** Both `/verify` (craft reviewer) and `/sweep` (quality auditor) now check for cross-boundary mismatches — bugs where two representations of the same concept disagree across layers. Catches shape mismatches, convention drift, reference mismatches, contract gaps, temporal shape mismatches, and false positive integrations. Generalized from a competitive analysis of revfactory/harness's battle-tested taxonomy.
- **Project-specific boundary criteria.** `gigo:gigo` Step 6.5 now reads the boundary taxonomy during assembly, matches the project's tech stack against detection heuristics, and generates 1-2 concrete criteria per relevant boundary type (e.g., "API response wrapper shapes match frontend type definitions"). Criteria land under a "Boundary Coherence" subsection of Craft Review in `review-criteria.md`.
- **Regeneration support.** `gigo:maintain` regenerates boundary coherence criteria alongside other review criteria when the team or standards change.

### Change Impact Matrix

- **Proactive ripple detection.** New reference `skills/maintain/references/change-impact-matrix.md` maps 10 change types (persona add/modify/remove, rule add/modify/remove, reference add/remove, extension, pipeline) to downstream files and Snap audit checks. Acts as the single source of truth for ripple logic.
- **Maintain consults the matrix.** `gigo:maintain` targeted-addition mode now reads the matrix at Step 5 to identify which downstream files a change affects. Auto-run items (mechanical `review-criteria.md` regeneration, line budget checks) execute without confirmation. Judgment items are reported to the operator for approval.
- **Snap pre-audit.** `gigo:snap` runs a `git status --short` reverse-lookup against the matrix before the 14-point protocol. Classifies uncommitted changes by change type (CT-1..CT-10) and flags downstream files that haven't been touched as potential ripples. Baseline is uncommitted delta only — snap before committing for best coverage.
- **Deferred for v2:** matrix consultation from `restructure.md` and `upgrade-checklist.md` (they currently regenerate `review-criteria.md` independently); semantic drift detection; multi-commit session baseline.

### Spec Writing

- **Boundaries nudge.** `/spec` Conventions Section now prompts spec writers to list integration boundaries (API-to-consumer, DB-to-API, config-to-code) under a "Boundaries" heading so reviewers know which seams to check.

### Execution Pattern Catalog

- **Five named execution patterns.** New reference `skills/spec/references/execution-patterns.md` documents Supervisor, Pipeline, Fan-out/Fan-in, Producer-Reviewer, and Expert Pool with uniform entries (Definition, When to use, GIGO mapping, Plan shape, Gotchas). Plans now have vocabulary for their execution shape instead of implicitly defaulting to Supervisor. Adapted from harness's six-pattern catalog, omitting Hierarchical Delegation.
- **Plans declare their shape.** `gigo:spec`'s planning procedure gained a "Pick Execution Pattern" step, and the plan document template now includes a `**Execution Pattern:**` header field between `**Goal:**` and `**Architecture:**`. Multi-phase plans can declare per-phase patterns. `gigo:execute` is untouched — the field is metadata that existing execution ignores, preserving backwards compatibility for plans written before the catalog landed.
- **Two new worked examples.** `example-plan.md` gained a Fan-out/Fan-in example (market report writing) and a Pipeline example (literature review synthesis), both in non-software domains to reinforce that patterns are domain-agnostic. The three existing examples got their new header field, and the Large Task example demonstrates per-phase declarations (Phase 1 Pipeline → Phase 2 Fan-out/Fan-in → Phase 3-4 Supervisor).
- **Expert Pool routes review, not workers.** The Expert Pool entry explicitly states workers stay bare (Phase 7 research finding holds) — the pattern introduces a `review-lens:` task tag that `gigo:verify` will later consume to apply the matching persona's quality bars. For Cycle 1 the tag is metadata-only; enforcement is a future enhancement.
- **Cycle 1 of 2.** This catalog is Part A of a two-cycle proposal. Part B (Agent Teams rebuild in `gigo:execute`) is a separate future spec run.

### New References

- `skills/gigo/references/boundary-mismatch-patterns.md` — Canonical taxonomy of 6 boundary-mismatch pattern categories (BM-1 Shape Mismatch, BM-2 Convention Drift, BM-3 Reference Mismatch, BM-4 Contract Gap, BM-5 Temporal Shape Mismatch, BM-6 False Positive Integration) with a 9-row detection heuristics table. Colocated with the gigo skill so Step 6.5's skill-relative path resolves at runtime.
- `skills/spec/references/execution-patterns.md` — 5-pattern execution catalog (Supervisor, Pipeline, Fan-out/Fan-in, Producer-Reviewer, Expert Pool) loaded on demand during plan writing. Domain-agnostic — applies to code, writing, and research alike.

## v0.11.0-beta (2026-03-31)

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
