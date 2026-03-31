# Proportionality Refactor — Attack Plan

**Problem:** Blueprint takes 2.5hr planning + 1.5hr implementation for a medium task that should take 30min total. External tester called it "the pinnacle of over-engineering." We became the bloated context we warned about.

**Goal:** Medium task end-to-end under 30 min. Small tasks under 10 min. Quality gates scale with the task.

**Evidence:** Carlos's test — same prompt, three runs:
- v6.0.0: 2hr, 570k tokens, good result with minor errors
- Vanilla Claude + /plan: similar quality, slightly less polish
- v0.9.9: 4hr, incomplete output, missing features, worse UI

---

## The Cuts (in order)

### 1. Blueprint SKILL.md refactor
**Current:** 303 lines. Detailed phase-by-phase procedure all in the hub.
**Target:** Under 200 lines. Move Phases 5-10 procedural details to `references/formal-phases.md`. Hub keeps phase summaries + hard gates + scale guidance.
**Why first:** Reduces context load for everything else.

### 2. /team routing default OFF
**Current:** Default active. Agent routes through all personas before every response.
**Target:** Default inactive. Personas still in CLAUDE.md, still read during Phase 1. But no per-response routing deliberation. Users opt in with `/team on`.
**Why:** Persona routing adds deliberation overhead without proven quality gain over just having personas in context. Hu et al. finding: personas help alignment but hurt knowledge retrieval.

### 3. Challenger scaling
**Current:** Mandatory for ALL tasks. Three-layer enforcement. 2 subagent dispatches per blueprint (~30min each).
**Target:** Default for large tasks. Self-review sufficient for small/medium. Operator can always request it. Scale detection already exists in "Scale to the Task" section.
**Why:** Two Challenger reviews on a substance explorer dashboard is ceremony, not quality assurance.

### 4. Fact-checker scaling
**Current:** Always runs at Phase 4.25. Dispatches Plan subagent.
**Target:** Only for existing codebases with meaningful code. Greenfield projects (< ~10 source files) skip it.
**Why:** Fact-checking an empty project is wasted tokens.

### 5. Assembly web search speed
**Current:** ~10 min web search for every assembly, even established domains.
**Target:** Training knowledge first. Web search only for unfamiliar/fast-moving domains or operator request.
**Why:** React/Tailwind/Bun doesn't need web research to assemble a team.

### 6. Remove eager resume detection (DONE)
**Already reverted.** Resume is trigger-based — user says "resume" and the agent reads existing approval markers. No scanning on every blueprint invocation.

---

## Anti-Pattern We Hit

Each quality gate was individually justified:
- Fact-checker catches wrong assumptions ✓
- Challenger catches sycophancy gaps ✓
- /team routing applies expert lenses ✓
- Resume detection handles context limits ✓

But cumulative effect: 4 subagent dispatches, 10+ persona deliberations, and file scanning before a single line of code. The Gloaguen finding applied to our own pipeline.

**The principle:** Every feature must justify its cost against the COMMON case, not the edge case it was designed for.

---

## Validation

After each cut, run Carlos's exact prompt:
> "I want to build a solution to explore and evaluate the substances data available at the substances folder. The idea is to iterate over the substances, merge, group, classify, anything that may help make the substances database into a better source of information."

Project: Bun + React + Tailwind (greenfield)

Measure: time-to-first-implementation, total time, output completeness.
Target: under 30 min total, all features present.

---

## What We Keep

- The Hard Gate (no code before approved plan) — proven value
- Plan mode for design briefs — proven value
- Specs with Conventions sections — proven value
- Two-stage code review during execution — proven value
- Approval markers — proven value, zero overhead
- Checkpoint/resume in execute — proven value, already lazy
