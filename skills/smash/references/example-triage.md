# Smash — Worked Example

A real agency project (Croftspan) had 16 rules files totaling 405 auto-loaded lines. Here's how Smash triaged it.

## Before

| File | Lines | Issue |
|---|---|---|
| `05-app-architecture.md` | 138 | 2.3x over cap |
| `11-schema-verification.md` | 48 | Narrow — only applies when touching data layer |
| `08-admin-panel.md` | 7 | One-liner, related to other executive files |
| `09-agency-dashboard.md` | 6 | One-liner, related to other executive files |
| `10-analytics.md` | 5 | One-liner, related to other executive files |
| `12-communications.md` | 8 | One-liner, related to other executive files |
| `06-executive-context.md` | 22 | Overlaps with client-specific executive files |
| `07-client-deliverables.md` | 18 | Overlaps with executive context |

## Triage

| File | Category | Action |
|---|---|---|
| `05-app-architecture.md` | Gold but heavy | Split: 55 lines stay in rules, 83 lines → `.claude/references/architecture-deep-dive.md` |
| `11-schema-verification.md` | Gold but narrow | Move to `.claude/references/schema-verification.md`, add "When to Go Deeper" pointer |
| `08, 09, 10, 12` | Consolidation | Merge 4 files (26 lines total) → 1 file `executive-context.md` (~20 lines) |
| `06, 07` | Consolidation | Merge with executive context → same consolidated file |
| All 26 gotchas | Gold | Preserve aggressively — highest-value content |
| All anti-patterns | Gold | Preserve — non-derivable |

## After

| Metric | Before | After | Change |
|---|---|---|---|
| Files | 16 | 8 | -50% |
| Auto-loaded lines | 405 | ~195 | -52% |
| Reference files | 2 | 4 | +2 |
| Gotchas preserved | 26 | 26 | 0 lost |
| Anti-patterns preserved | All | All | 0 lost |

Every piece of institutional knowledge survived. 210 lines of auto-loaded context stopped costing tokens on every conversation.
