# Troubleshooting — Known Issues

Tracked issues users have hit. When a new issue is reported, add it here and to the getting-started page.

## Stale version on install (2026-03-30)

**Symptom:** `claude plugin install gigo` gives an old version (e.g., v6.0.0 or v0.9.6-beta instead of latest).

**Root cause:** `.claude-plugin/marketplace.json` version was not synced with `.claude-plugin/plugin.json` during version bumps. The marketplace cache serves the old listing.

**Fix for users:**
```bash
claude plugin uninstall gigo
rm -rf ~/.claude/plugins/marketplaces/gigo
claude plugin marketplace add croftspan/gigo
claude plugin install gigo
```

**Fix for maintainers:** Both `marketplace.json` and `plugin.json` must be updated on every version bump. Added to release checklist.

**Status:** Fixed in 87fc2b7.

## Manual install conflicts with marketplace install

**Symptom:** Skills behave unexpectedly or load old versions even after marketplace install.

**Root cause:** Previous manual install (`cp -r gigo/skills/ ~/.claude/skills/`) left files that take precedence over or conflict with the marketplace plugin path.

**Fix for users:**
```bash
rm -rf ~/.claude/skills/gigo*
```

**Status:** Documented in getting-started troubleshooting section.
