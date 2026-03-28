# Contributing to GIGO

GIGO is a skill ecosystem for Claude Code — contributions are skill improvements, not application code.

## Reporting Issues

Use the [issue templates](https://github.com/Eaven/gigo/issues/new/choose):
- **Bug Report** — something isn't working as expected
- **Feature Request** — suggest an improvement

## How Skills Are Structured

Each skill follows a hub-and-spoke pattern:
- **SKILL.md** is the hub — it sets persona, detects mode, and routes to supporting files. Keep it under 500 lines.
- **references/** files are spokes — procedures, checklists, deep guidance. Loaded on demand.

If a mode section in SKILL.md exceeds ~5 lines of procedure, move it to a reference file.

## The Non-Derivable Rule

Only contribute rules for things Claude can't figure out by reading the project files.

**Yes:** Philosophy, quality bars, anti-patterns, blended authority rationale.

**No:** Directory structure, code patterns, file organization. The agent navigates codebases on its own. Codebase overviews are actively harmful — they waste attention on information the agent would find anyway.

## Architecture

See the [architecture doc](site/docs/architecture.html) for the two-tier system, line caps, The Snap, and the plan-execute-review pipeline.

## License

MIT. By contributing you agree your contributions are released under the same license.
