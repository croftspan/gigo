# Croftspan Cleanup Plan

Date: 2026-03-24
Status: Planned — not yet executed

Based on the audit in `docs/croftspan-audit.md`. Preserves everything that works, trims what doesn't earn its token cost.

---

## Split: `05-app-architecture.md` (138 lines -> ~55 + reference)

### Keep in rules (non-derivable core, ~55 lines):

- Data Model (core chain, polymorphic, immutable, status machines) — 7 lines
- Authentication (roles, token scopes) — 3 lines
- API Layer (conventions not obvious from code: Jbuilder partials, cursor pagination, event tracking) — 5 lines
- ActionCable (two-stream pattern, model callbacks vs controller calls — intentional difference is non-derivable) — 4 lines
- Agent Dispatch (orchestration logic, rate limits, WorkDispatcher rule, session resume patterns) — 8 lines
- Maintenance Mode (intentionally different behaviors — don't "fix" this) — 2 lines
- Gotchas (ALL 26 of them — pure gold, prevents real bugs) — 26 lines

### Move to `.claude/references/app-architecture-deep.md`:

With "When to Go Deeper" pointers added to the trimmed rules file:
- Client Dashboard (BaseController, MessageThread concern, RetainerTracking concern)
- Operator Dashboard (BaseController, revenue scopes, materialization pattern)
- Client Intake & Discovery (wizard flow, adaptive discovery, polling, per-answer dispatch)
- Time Estimation & Billing (pipeline details, estimate model, billing rates, status insertion)

---

## Move: `11-schema-verification.md` (48 lines -> reference)

Full protocol moves to `.claude/references/schema-verification.md`.

Add one-line "When to Go Deeper" pointer to `02-code-standards.md`:
> When writing code that touches models, schema, or data layer, read `.claude/references/schema-verification.md`.

---

## Consolidate: Executive context (rules 10, 12, 13, 14 -> one file)

New `10-executive-context.md` (~10 lines):

```
# Executive Context

The agency's value proposition is operator-reviewed quality backed by 20+ years of experience. The operator reviews EVERYTHING before clients see it. Non-negotiable. If a process change bypasses operator review, reject it.

Every significant recommendation includes: the decision, alternatives, reasoning, second-order effects, revenue impact. Log to executive/decisions/ with date and context. Check decisions log before re-debating settled questions.

Eaven splits time between El Salvador and Georgia. M3 Max MacBook, 7x A6000 server for inference. Works across Croftspan, Neon Syndicates, BuzzScout/SaleScout simultaneously. Prefers direct communication, moves fast, strong opinions on quality. Will forget things — the vault exists for this. System should work autonomously and only surface what needs his attention.

This agent was built from a multi-day intensive. Check executive/decisions/founding-decisions.md first for past decisions. If not there, check executive/decisions/ broadly. Update the vault actively — if it's not in the vault, it didn't happen.
```

### Files removed:
- `10-quality-promise.md` (merged)
- `12-decisions.md` (merged)
- `13-operator-context.md` (merged)
- `14-institutional-memory.md` (merged)

---

## Consolidate: Agency operations (rules 20-25 -> one file)

New `20-agency-operations.md` (~15 lines):

```
# Agency Operations

All data operations use the Croftspan REST API via curl. $CROFTSPAN_API_URL and $CROFTSPAN_TOKEN always available. Never use sqlite3. Database is PostgreSQL via Rails — API endpoints only.

Only Lena Morrow and Marco Reyes post client-visible comments (visibility: "client"). All others use visibility: "internal". Say "within 48 hours" — never promise faster. Clients never see Vince reviews, internal comments, draft work, or anything in internal_review/operator_review status.

Read STANDARDS.md before producing any deliverable. Zero tolerance for AI slop. Every deliverable is portfolio-grade. Self-check against STANDARDS.md before setting status to internal_review.

For branding deliverables, read DELIVERABLE_STANDARD.md before production. Minimum quality floor: self-contained HTML, client-specific design tokens, cover page + TOC, dark/light/responsive/print. Meridian Health is the reference exemplar.

You are dispatched headlessly with 500+ max-turns. Complete the full task. Before exiting: update status via API, post production summary as internal comment, save learnings.

Save learnings scoped correctly: agency-wide -> governance docs, client-specific -> agency/vault/clients/{client-slug}/. Never put client-specific information in STANDARDS.md or CLAUDE.md.
```

### Files removed:
- `20-api-only.md` (merged)
- `21-client-communication.md` (merged)
- `22-agency-quality.md` (merged)
- `23-session-discipline.md` (merged)
- `24-auto-save-scope.md` (merged)
- `25-deliverable-standard.md` (merged)

---

## New: Add The Snap

Add `.claude/rules/snap.md` using the snap template from avengers-assemble, customized for Croftspan's routing table:

| Learning type | Where it goes |
|---|---|
| Architecture pattern | `.claude/rules/05-app-architecture.md` -> Gotchas |
| Code standard | `.claude/rules/02-code-standards.md` |
| Rails-specific pattern | `.claude/rules/03-rails8.md` |
| Testing insight | `.claude/rules/04-testing.md` |
| Agency quality rule | `agency/governance/STANDARDS.md` |
| Client-specific learning | `agency/vault/clients/{slug}/` |
| Deep reference material | `.claude/references/{topic}.md` |

---

## Result Summary

### Before: 16 files, 405 lines auto-loaded

```
01-stack.md                47 lines
02-code-standards.md       40 lines
03-rails8.md               29 lines
04-testing.md              30 lines
05-app-architecture.md    138 lines  <-- 2.3x over cap
10-quality-promise.md       1 line
11-schema-verification.md  48 lines
12-decisions.md             1 line
13-operator-context.md      1 line
14-institutional-memory.md  5 lines
20-api-only.md              1 line
21-client-communication.md  1 line
22-agency-quality.md        1 line
23-session-discipline.md    1 line
24-auto-save-scope.md       5 lines
25-deliverable-standard.md  1 line
```

### After: 8 files, ~195 lines auto-loaded (52% reduction)

```
01-stack.md                47 lines  (unchanged)
02-code-standards.md       42 lines  (+2 lines: schema verification pointer)
03-rails8.md               29 lines  (unchanged)
04-testing.md              30 lines  (unchanged)
05-app-architecture.md    ~55 lines  (trimmed from 138, derivable moved to ref)
10-executive-context.md   ~10 lines  (consolidated from 4 files)
20-agency-operations.md   ~15 lines  (consolidated from 6 files)
snap.md                   ~30 lines  (new — The Snap)
```

### New reference files:

```
references/app-architecture-deep.md    (dashboard, intake, estimation details)
references/schema-verification.md      (full verification protocol)
```

### What's preserved:
- ALL 26 gotchas (non-derivable, prevents real bugs)
- Data model, auth, API conventions (non-derivable)
- Agent dispatch logic (non-derivable)
- Maintenance mode intentional behavior (non-derivable)
- Quality promise, decision protocol (non-derivable)
- Operator context (non-derivable)
- All agency operation rules (consolidated, not removed)
- Schema verification protocol (moved to reference, pointer in rules)
- Stack versions and forbidden list (unchanged)
- Code standards (unchanged)
- Rails patterns (unchanged)
- Testing pyramid (unchanged)

### What's removed:
- Client Dashboard section (derivable from reading controllers)
- Operator Dashboard section (derivable from reading controllers)
- Intake wizard implementation details (derivable from code)
- Estimation pipeline details (derivable from code)
- File overhead from 8 one-liner files (consolidated into 2)
- 210 lines of auto-loaded context that wasn't earning its token cost
