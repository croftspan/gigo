# Changelog

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
