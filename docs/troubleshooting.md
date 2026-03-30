# Troubleshooting — Known Issues

Tracked issues users have hit. When a new issue is reported, add it here and to the getting-started page.

## Stale version on install (2026-03-30)

**Symptom:** `claude plugin install gigo` gives an old version (e.g., v6.0.0 or v0.9.6-beta instead of latest).

**Root cause:** `.claude-plugin/marketplace.json` version was not synced with `.claude-plugin/plugin.json` during version bumps. The marketplace cache serves the old listing.

**Fix for users:**
```bash
# 1. Remove any leftover manual copies first
rm -rf ~/.claude/skills/gigo*

# 2. Uninstall the old plugin
claude plugin uninstall gigo

# 3. Clear the marketplace cache
rm -rf ~/.claude/plugins/marketplaces/gigo

# 4. Re-add and install fresh
claude plugin marketplace add croftspan/gigo
claude plugin install gigo
```

**Fix for maintainers:** Both `marketplace.json` and `plugin.json` must be updated on every version bump. Added to release checklist.

**Status:** Fixed in 87fc2b7.
