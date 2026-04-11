# Walkthrough — Execution Pattern Catalog (Cycle 1)

**Shipped:** 2026-04-11
**Spec:** `docs/gigo/specs/2026-04-11-execution-pattern-catalog-design.md`
**Plan:** `docs/gigo/plans/2026-04-11-execution-pattern-catalog.md`
**Source brief:** `.claude/plans/curious-strolling-chipmunk.md` (Part A of a two-cycle proposal)
**Commits:** `92a0040` → `a156178` on `main`

---

## What it is

A named catalog of 5 execution patterns that `gigo:spec` consults during plan writing. Previously every plan was implicitly "Supervisor" (lead dispatches parallel workers). Plans now declare their execution shape explicitly via a `**Execution Pattern:**` header field.

**The 5 patterns:**

| Pattern | Shape | When to use |
|---|---|---|
| **Supervisor** (default) | Central lead dispatches independent workers | Most plans — fall back here when nothing else fits |
| **Pipeline** | Strictly sequential stages, each feeding the next | Research, ETL, any workflow where Stage N depends on Stage N-1 output |
| **Fan-out/Fan-in** | Parallel workers produce artifacts + explicit merge task | Multi-section deliverables where pieces converge |
| **Producer-Reviewer** | Generator task → separate reviewer task → optional revision | High-stakes output where independent validation matters |
| **Expert Pool** | Tasks routed to different *review lenses* by domain | Mixed-domain plans where one reviewer can't cover all areas |

---

## Where it lives

```
skills/spec/
├── SKILL.md                              ← +1 line pointer (line 131)
└── references/
    ├── execution-patterns.md             ← NEW (298 lines) — the catalog
    ├── planning-procedure.md             ← +18 / -12 (new section 2)
    └── example-plan.md                   ← +91 (2 new examples + headers)
```

**Read path during `/spec`:**

1. Operator invokes `/spec` on an approved brief.
2. Spec reaches Phase 8 (plan writing).
3. `skills/spec/SKILL.md:131` points to `references/execution-patterns.md`.
4. Spec reads the catalog, picks a pattern, declares it in the plan header.
5. Spec reads `references/planning-procedure.md` section 2 for the procedure.
6. Spec reads `references/example-plan.md` to see worked examples with the new field.

---

## How to use it

### As an operator

Nothing changes in your workflow. Run `/blueprint` → `/spec` → `/execute` as before. The only visible difference is that plans now include a line like:

```markdown
**Execution Pattern:** Fan-out/Fan-in
```

between `**Goal:**` and `**Architecture:**` in the header. If you see a plan that looks parallelizable but only names "Supervisor," you now have vocabulary to ask "why not Fan-out/Fan-in?"

### For multi-phase plans

Each phase can declare its own pattern:

```markdown
## Phase 1: Foundation

**Execution Pattern:** Pipeline

### Task 1: ...
### Task 2: ...
```

The Large Task example in `example-plan.md` demonstrates this — four phases with different patterns (Pipeline → Fan-out/Fan-in → Supervisor → Supervisor).

### For existing plans (backwards compatibility)

Plans written before Cycle 1 don't have the new header. They still execute without changes — the field is metadata, not validation. `gigo:execute` ignores it.

### Expert Pool's `review-lens:` tag

Expert Pool introduces an optional per-task field:

```markdown
### Task 2: Build authentication flow

**blocks:** 5
**blocked-by:** 1
**parallelizable:** false
**review-lens:** security
```

**In Cycle 1 this is metadata-only.** `gigo:verify` does not yet enforce it. Planners can start tagging; enforcement is a future enhancement with its own spec cycle.

---

## What stayed untouched

- `gigo:execute` and all its references — the new field is metadata; execution logic is unchanged
- `gigo:verify` — no enforcement of `review-lens:` in Cycle 1
- Assembled projects' `.claude/references/` — the catalog lives in the plugin, not in assembled projects
- No new plan validation — plans missing the header field are not blocked

---

## The 5 anti-patterns the catalog names

If you're writing or reviewing a plan, watch for these:

1. **False parallelism** — marking tasks `parallelizable: true` when they share hidden state (same file, same database, same global config). Pre-flight conflict check catches file overlap; hidden state is on the planner.
2. **Missing fan-in** — parallel work with no merge step. The parallel workers succeed but nothing integrates their output.
3. **Self-review** — skipping the separate reviewer task in Producer-Reviewer because "the producer will check its own work." A producer catches roughly the same errors it made writing the content.
4. **Worker-level expert routing** — injecting persona context into workers to "make them better." Violates the bare-worker research finding (Phase 7) — workers produce better output when bare.
5. **Pattern sprawl** — naming a pattern for every plan when Supervisor would do. Supervisor is the default; don't invent reasons to escape it.

---

## Review gates that caught things

Three defects were caught before the catalog shipped. Worth noting because they show the review pipeline working:

1. **Task 1 — Plan shape Setup stubs were placeholders.** Initial worker used `### Setup` without concrete task numbers, leaving dangling references. Fix subagent added Task 1/2/3/4 numbering. Caught by Stage 1 (spec compliance).

2. **Task 3 — New examples were 56 and 49 lines, exceeding R5.7 caps of 30 and 25.** Initial worker preserved verbatim task text instead of trimming. Fix subagent collapsed fields to pipe-delimited lines and removed scaffolding, landing at exactly 30/25. Caught by Stage 1 (R5.7 is a machine-countable gate).

3. **End-of-cycle — Expert Pool and Producer-Reviewer plan shapes had dangling `blocks:` references.** Tasks 2/3/4 declared `blocks: 5` but no Task 5 existed in the Expert Pool snippet. Producer-Reviewer similarly referenced non-existent Tasks 2 and 6. Caught by end-of-cycle Stage 2 craft review (adjacent defect in Producer-Reviewer found by the lead during triage, not by the reviewer subagent). Fix landed in commit `a156178` — all 5 pattern dep graphs now self-contained.

---

## What's next — Cycle 2 (Part B)

Cycle 2 is a **destructive + additive refactor of `gigo:execute`**. The approved brief at `.claude/plans/curious-strolling-chipmunk.md` covers both cycles; Cycle 2's section is a sketch that needs its own `/blueprint` → `/spec` → `/execute` loop.

**Scope preview:**

- Remove Tier 3 (Agent Teams experimental opt-in) from `skills/execute/SKILL.md`
- Simplify execute to two tiers: Subagents (primary) + Inline (fallback)
- Strip or delete `skills/execute/references/review-hook.md` and the Tier 3 prompt templates in `teammate-prompts.md`
- Add new reference `skills/execute/references/agent-teams-design.md` — target-state design doc for when Agent Teams stabilizes

**Status:** target-state design only. No team implementation. The design doc resolves the Phase 7 research tension (bare workers produce better code; teams can't be bare) by restricting future teams to non-code workflows — code work stays on subagents.

The kickoff prompt for Cycle 2 is in the session where this walkthrough was handed off — paste it into a fresh Claude Code session to start.
