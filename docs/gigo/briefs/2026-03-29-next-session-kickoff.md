# Next Session Kickoff Packet

## Session 1: gigo:eval Overhaul + Subagent Execution Test

Two birds: overhaul the eval skill AND test subagent execution on a real 3+ task plan. Use `gigo:blueprint` for the eval overhaul. When it hits Phase 11, force subagents. Watch for:
- Does execute announce "Executing with Subagents"?
- Does it dispatch Agent tool calls with `isolation: "worktree"`?
- Does it run gigo:verify between tasks?
- Does it merge branches back to main?

### Prompt:

```
/gigo:blueprint Audit and overhaul the gigo:eval skill. It was built before the domain-neutral review redesign, before the Challenger adversarial reviewer, before {DOMAIN_CRITERIA}, before the fact-checker (Phase 4.25), before plan mode integration. Read skills/eval/SKILL.md and all its references. Check for: stale references to old terminology ("assembled context", "engineering review", "QUALITY_BAR_CHECKLIST"), code-specific assumptions that don't work for novels/games/research, missing awareness of the current pipeline (plan mode → fact-checker → spec → Challenger → plan → Challenger → execute → per-task review). The eval skill should be able to test whether ANY assembled project produces better output than bare, across any domain. Use the fact-checker prompt as the reference for domain-neutral language.
```

When it hits Phase 11, tell it: "Use subagents. Do not run inline. This plan has 3+ tasks."

---

## Session 2: gigo:gigo "Enforce Existing Expertise" Mode (when Croftspan discovery product is ready)

gigo:gigo currently only has one mode: research a domain from scratch. But the Croftspan enterprise play is: do discovery with a client, produce brand system/voice guide/messaging framework, THEN assemble a GIGO project that enforces those deliverables. If gigo:gigo treats existing expertise the same as a blank slate, the entire service model breaks.

### The feature:

When existing expertise artifacts exist (brand strategy, voice guide, messaging framework, pillars, style guide), `gigo:gigo` should detect them and switch to "enforce" mode:
- Build personas that ENFORCE the existing system, not research the domain
- Quality bars derived from the existing deliverables
- The team's job is enforcement and execution, not discovery
- Existing voice guide becomes law, not suggestion

This is the core flow for every Croftspan client engagement: discovery → deliverables → assembly that enforces those deliverables.

### Prompt:

```
/gigo:blueprint Add an "enforce existing expertise" mode to gigo:gigo. When assembling a project that has existing brand/voice/messaging/strategy deliverables from a discovery phase, the assembly should BUILD AROUND those deliverables instead of researching the domain from scratch. Detect existing artifacts (brand-strategy.md, voice-guide.md, messaging-framework.md, pillars.md, style-guide.md, etc.) and switch to enforcement mode: personas enforce the existing system, quality bars derive from the deliverables, the team's job is execution not discovery. This is critical for the Croftspan enterprise play where every client engagement produces deliverables that gigo:gigo then needs to operationalize.
```

---

## Backlog: Eval Repo Split

Create croftspan/gigo-evals. Move:
- `evals/` directory (scripts, fixtures, results)
- EVAL-NARRATIVE.md
- Keep stub references in main repo

Not urgent. Do this when testing stabilizes.
