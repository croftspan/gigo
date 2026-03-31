# Intent Fidelity — Preliminary Plan

**Problem:** Blueprint over-processes user intent through persona lenses, research frameworks, and architecture decisions until the original ask is buried. v6.0.0 and vanilla Claude both built what the user asked for. v0.9.9+ built a read-only viewer when the user asked for merge/group/classify actions.

**Evidence:**
- User prompt: "iterate over the substances, merge, group, classify" — action verbs
- Blueprint interpreted as pipeline operations (automatic batch) instead of user-facing actions
- Spec locked in a read-only viewer with 7 GET-only endpoints, zero write operations
- Challenger caught the intent mismatch TWICE but the agent noted it and moved on
- v6.0.0 (hundreds of commits ago) and vanilla Claude + superpowers both got it right
- External tester: "It just made an explorer tool, but with no actual actions"

**Root cause:** More ceremony = more opportunities to drift from intent. The blueprint arc filters the user's words through so many layers that the original signal gets lost.

---

## Proposed Fixes

### Fix 1: Intent Anchor in Spec

The user's original prompt must be quoted verbatim at the top of every spec. Every requirement traces back to a word or phrase from that prompt.

**Mechanism:** Add to Phase 5 (write spec) instructions:
- Quote the operator's original request at the top of the spec under `## Original Request`
- After writing requirements, run a traceability check: for each action verb in the original request, point to the requirement that implements it
- If an action verb has no corresponding requirement, flag it as a gap before proceeding

**Example failure this catches:**
- Original: "merge, group, classify"
- Spec requirements: search, browse, compare, detail view
- Gap: "merge" → no requirement. "group" → no requirement. "classify" → no requirement.
- The spec self-review would catch this before the Challenger even runs.

### Fix 2: Challenger Escalation is Mandatory

When the Challenger finds an intent mismatch (Pass 2), it's not a note — it's a hard stop. The operator must see it and decide.

**Mechanism:** Add to the formal-phases reference and Challenger dispatch instructions:
- If the Challenger's Pass 2 (intent alignment) finds drift, the blueprint MUST present it to the operator with the specific mismatch quoted
- The operator decides: revise spec, or confirm the drift is intentional
- The agent cannot proceed past Phase 7 (spec approval) with an unresolved intent mismatch
- This is the same pattern as the Hard Gate — put the prohibition where the temptation happens

### Fix 3: Simplify the Design Phase

Blueprint Phase 3 (propose approaches) and Phase 4 (present design) are where drift starts. The agent gets excited about architecture and loses sight of the user's verbs.

**Mechanism:** Before proposing approaches, list the user's action verbs:
- "The user asked for: [merge], [group], [classify], [iterate], [explore], [evaluate]"
- Each approach must account for every verb
- If an approach drops a verb, it must explicitly say so and justify why

---

## What We Keep

- The pipeline itself (plan → spec → execute) — proven value
- Plan mode for design briefs — keeps thinking durable
- Two-stage code review during execution — proven value
- The proportionality refactor we just shipped — essential

## What We're Fixing

- Intent gets lost in ceremony → anchor it at the source
- Challenger findings get noted but not escalated → make escalation mandatory
- Design phase drifts from verbs to architecture → verb-tracing before design

### Fix 4: Split blueprint and execute responsibilities

Blueprint currently owns 11 phases — by Phase 8 (implementation plan), context is compressed and the user's original words are buried under design deliberation.

**Proposed split:**

**blueprint** owns: idea → approved spec (Phases 0-7)
- Explore, question, design, fact-check, write spec, self-review, challenger, operator approves
- Deliverable: approved spec. Done.

**execute** owns: approved spec → shipped code (Phases 8-11 + build)
- Reads the spec with fresh context (user's words right there, not compressed)
- Writes implementation plan (current Phases 8-9)
- Challenger on plan (current Phase 9.5)
- Operator approves plan (current Phase 10)
- Builds (existing execution flow)

**Why this helps intent fidelity:**
- Execute starts with the spec as primary input, not a compressed hour-long conversation
- The spec has the intent anchor (Fix 1) — user's exact words quoted at top
- Implementation plan is written against the spec, not against fading conversation memory
- Each skill has one clear deliverable, not an 11-phase marathon

**Option A (two-way split):**
- blueprint: idea → approved spec
- execute: spec → implementation plan → build

**Option B (full pipeline split — preferred):**
Each step is its own skill with its own clean context window:

1. **blueprint** — idea → approved design brief (plan mode explore/question/design)
2. **spec** — brief → approved spec (read brief, write spec, self-review, challenger)
3. **plan** — spec → approved implementation plan (read spec, write plan, self-review, challenger)
4. **execute** — plan → built code (dispatch workers, per-task verify)
5. **verify** — review any work (unchanged)

Operator flow: `/blueprint` → approve → `/spec` → approve → `/plan` → approve → `/execute`

Each skill starts fresh, reads the artifact from the previous step, does one thing. No context compression killing intent. Each approval gate is a natural session boundary — if context gets tight, break between any two steps.

Skills can auto-chain (blueprint offers `/spec` after approval) but don't have to. The user can also start at any step if they already have the input artifact (e.g., hand-written spec → `/plan` → `/execute`).

## Files to Modify

- `skills/blueprint/SKILL.md` — intent verb-listing (Fix 3), end at spec approval (Fix 4)
- `skills/blueprint/references/formal-phases.md` — intent anchor in Phase 5 (Fix 1), remove Phases 8-10 (Fix 4), challenger escalation (Fix 2)
- `skills/execute/SKILL.md` — absorb implementation plan writing (Fix 4)
- `skills/verify/references/spec-plan-reviewer-prompt.md` — strengthen Pass 2 intent alignment

## Validation

Run Carlos's exact prompt against a fresh project with the fixes applied. The spec must contain requirements for merge, group, and classify as user-facing actions, not just pipeline operations. If it builds a read-only viewer again, we haven't fixed it.
