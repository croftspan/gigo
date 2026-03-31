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

### Fix 4: Split the pipeline into clean context boundaries

Blueprint currently owns 11 phases. By Phase 8 context is compressed and the user's original words are buried. Each step should be its own skill with one job and one deliverable.

**The pipeline (4 skills):**

1. **blueprint** — idea → approved design brief
   - Plan mode: explore, question, propose approaches, design, fact-check
   - Operator approves the brief
   - Done. Hands off to `/spec`.

2. **spec** — approved brief → approved spec + implementation plan
   - Fresh context. Reads the brief (intent anchor right there).
   - Writes the formal spec with conventions section
   - Self-review, challenger (large tasks), operator approves spec
   - Writes the implementation plan from the approved spec
   - Self-review, challenger (large tasks), operator approves plan
   - Done. Hands off to `/execute`.
   - Spec and plan stay together because they're two views of the same thing — "what" and "how." Breaking context between them adds overhead without value.

3. **execute** — approved plan → built code
   - Fresh context. Reads the plan + spec.
   - Dispatch workers, per-task verify, checkpoints
   - Unchanged from current execute behavior (minus plan writing)

4. **verify** — review any work (unchanged)

**Operator flow:** `/blueprint` → approve brief → `/spec` → approve spec → approve plan → `/execute`

**Why this works:**
- Each skill starts with a clean context window
- The spec skill reads the brief fresh — user's intent (with anchor from Fix 1) isn't compressed
- The plan is written right after the spec in the same context — they naturally inform each other
- Execute reads the plan fresh — no design deliberation noise
- Any step can be a session boundary if context gets tight
- Users can enter at any point (hand-written spec → `/execute` still works)

**What changes:**
- `skills/blueprint/SKILL.md` — strip to Phases 0-4.5 only (design brief). Add verb-listing (Fix 3).
- `skills/blueprint/references/formal-phases.md` — delete (absorbed into spec skill)
- New: `skills/spec/SKILL.md` — spec writing + plan writing + challenger reviews
- `skills/execute/SKILL.md` — remove plan writing, just reads approved plan and builds
- `skills/verify/` — unchanged

## Validation

Run Carlos's exact prompt against a fresh project with all fixes applied. The spec must contain requirements for merge, group, and classify as user-facing actions, not just pipeline operations. If it builds a read-only viewer again, we haven't fixed it.
