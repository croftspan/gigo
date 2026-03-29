# Next Session Kickoff Packet

## Session 1: Voice Session — Deferred Page Rewrites + Pillar Docs

The homepage and README are transformation-first. The subpages aren't. Three pages were cleaned for jargon but still have the old content structure. Plus the architecture/design-philosophy pages need the pillar treatment.

### Prompt for the voice session:

```
Three pages need the same transformation-first treatment the homepage got. They were cleaned for jargon last session but the content structure is still feature-first.

1. site/docs/getting-started.html — Rewrite to lead with what the user achieves, not what the tool does. The install steps are fine but the framing needs work. Make it feel like "you're 5 minutes from a better project" not "here are the technical steps."

2. site/docs/skills.html — Each skill card should lead with the transformation, not the feature. "Your expert team plans the work" not "Brainstorm, write specs, and produce ordered implementation plans." Match the voice of the homepage's "How it works" section.

3. site/research/index.html — Keep the technical depth but frame it as "here's how we validated it" not "here's our research." The reader should feel like they're seeing evidence of something that works, not a paper defense.

Also: site/docs/architecture.html and site/docs/design-philosophy.html need the pillar treatment. Two-tier architecture, The Snap, and the adversarial review system are core pillars of GIGO. These pages should communicate the VALUE of each pillar clearly. "Your project doesn't rot" not "we use a two-tier architecture." "Independent reviewer catches what you miss" not "adversarial output verification."

Same voice rules as the homepage: no "proven", no em dashes in copy, no jargon, every sentence survives "so what?", results as achievements not grades. Read docs/gigo/briefs/2026-03-29-presence-overhaul.md for the full language rules table.

Update footer version to match current plugin version in all modified files.
```

---

## Session 2: Test Subagent Execution

Use `gigo:blueprint` on the tq project to plan a 3+ task feature, then execute it. Watch for:
- Does execute announce "Executing with Subagents"?
- Does it dispatch Agent tool calls with `isolation: "worktree"`?
- Does it run gigo:verify between tasks?
- Does it merge branches back to main?

### Prompt:

```bash
cd ~/projects/gigo/evals/integration-test/tq-project
```

```
/gigo:blueprint Add a 'tq retry' command that re-queues failed tasks. Support 'tq retry <task-id>' for one task and 'tq retry --all' for all failed tasks. Must reset state from "failed" to "pending", preserve the original command and priority, increment a retry_count field, and refuse to retry tasks that have already been retried 3 times (configurable via --max-retries flag). Needs 4+ tasks: store interface changes, retry logic, command implementation, tests.
```

When it hits Phase 11, tell it: "Use subagents. Do not run inline."

---

## Session 3: gigo:eval Overhaul

gigo:eval was built before the domain-neutral redesign, before the Challenger, before {DOMAIN_CRITERIA}, before the fact-checker. It likely still references "assembled context", assumes code, and doesn't account for the current pipeline architecture.

### Prompt:

```
/gigo:blueprint Audit and overhaul the gigo:eval skill. It was built before the domain-neutral review redesign, before the Challenger adversarial reviewer, before {DOMAIN_CRITERIA}, before the fact-checker (Phase 4.25), before plan mode integration. Read skills/eval/SKILL.md and all its references. Check for: stale references to old terminology ("assembled context", "engineering review", "QUALITY_BAR_CHECKLIST"), code-specific assumptions that don't work for novels/games/research, missing awareness of the current pipeline (plan mode → fact-checker → spec → Challenger → plan → Challenger → execute → per-task review). The eval skill should be able to test whether ANY assembled project produces better output than bare, across any domain. Use the fact-checker prompt as the reference for domain-neutral language.
```

---

## Session 4 (when ready): Eval Repo Split

Create croftspan/gigo-evals. Move:
- `evals/` directory (scripts, fixtures, results)
- EVAL-NARRATIVE.md
- Keep stub references in main repo

Not urgent. Do this when testing stabilizes.
