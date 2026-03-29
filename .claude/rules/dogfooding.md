# Dogfooding Guard — GIGO Source Repo

This project IS the GIGO plugin source. Skills load from `~/.claude/plugins/marketplaces/gigo/` but the source of truth is `~/projects/gigo/`.

When reading or modifying GIGO's own skill files:
- **Read from:** `~/projects/gigo/skills/` (source repo)
- **Write to:** `~/projects/gigo/skills/` (source repo)
- **Never write to:** `~/.claude/plugins/marketplaces/gigo/skills/` (install path, gets overwritten)
- **Commit in:** `~/projects/gigo/` (the git repo you push from)

If you see yourself `cd`-ing to `~/.claude/plugins/` or writing files there, stop and redirect.
