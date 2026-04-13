# Brief: Feature Validation Suite

## The Question

We shipped 4 features from a competitive analysis of revfactory/harness:

1. **Boundary-mismatch detection** — review criteria for gigo:verify and gigo:sweep that catch integration bugs (API shape vs consumer type, naming drift, state machine gaps)
2. **Phase selection matrix** — decision aid for gigo:maintain showing downstream effects of changes
3. **Execution pattern catalog** — named patterns (Pipeline, Fan-out/Fan-in, etc.) for gigo:spec planning
4. **Agent Teams cleanup** — Tier 3 ripped out, simplified to Subagents + Inline, design doc added

Do these additions actually improve GIGO's output? Or are they token decoration on an already-working system?

## What Exists Today

GIGO has a mature eval framework at `evals/`:

- `run-eval.sh` — runs bare vs assembled comparisons using `claude -p` with `--output-format json`
- `score-eval.sh` — blinded randomized A/B LLM-as-judge scoring
- `judge-prompt.md` — 5-criteria judge (quality bar, persona voice, expertise routing, specificity, pushback quality)
- Two fixture domains: Rails API (OrderFlow) + Children's Novel (The Vanishing Paintings), 10 prompts each
- Historical results: 87% baseline → 96%+ after persona calibration and task-specific pointers
- Full narrative at `evals/EVAL-NARRATIVE.md`

**The gap:** This eval tests ASSEMBLED vs BARE — GIGO's core value proposition. It doesn't test whether GIGO v0.12 (with these 4 features) outperforms GIGO v0.11 (without them). That's an **incremental value** test, not a **core value** test.

## Three Layers of Testing

### Layer 1: Feature-Specific Functional Tests — "Does it work?"

Does each feature do what it claims? These are pass/fail checks, not comparative evals.

**Feature 1 — Boundary-mismatch detection:**
- Create a seeded-defect fixture: a small full-stack project (could be Next.js, could be any API+consumer pattern) with 5-8 known boundary bugs planted:
  - API returns `{ data: [...] }`, consumer expects `T[]` directly
  - `snake_case` DB field, `camelCase` API response, wrong case in frontend type
  - Link href points to `/create`, page lives at `/dashboard/create`
  - State transition map defines `A → B → C`, code only implements `A → B`
  - API returns 202 with `{ status }`, consumer accesses `data.result` (async shape mismatch)
- Run gigo:sweep and gigo:verify on the seeded fixture
- **Pass criterion:** detects ≥60% of seeded bugs. This isn't a high bar — it's proving the feature activates at all.
- **Stretch:** Run the same fixture WITHOUT the boundary-mismatch criteria (remove from review-criteria.md). If detection rate drops meaningfully, the criteria are earning their tokens.

**Feature 2 — Phase selection matrix:**
- Set up a test project with a full GIGO assembly (CLAUDE.md, rules, references, review-criteria.md)
- Run gigo:maintain in "add a persona" mode
- **Pass criterion:** maintain reports at least 2 downstream effects (e.g., "review-criteria.md needs regeneration," "Snap calibration check covers one more entry")
- **Stretch:** Same operation without the matrix reference. If maintain doesn't surface downstream effects without it, the matrix is adding value.

**Feature 3 — Execution pattern catalog:**
- Write 3 task descriptions with obvious execution shapes:
  - **Sequential:** "Migrate the database schema, then update the API to use new column names, then update the frontend types" (Pipeline)
  - **Parallel:** "Audit security, check for stubs, and review code quality" (Fan-out/Fan-in — this is literally what gigo:sweep does)
  - **Generate-then-validate:** "Write the implementation, then review it against the spec" (Producer-Reviewer)
- Run gigo:spec on each task
- **Pass criterion:** the plan names or structurally reflects the correct pattern. A pipeline task doesn't get parallelized. A parallel task doesn't get serialized.
- **Stretch:** Same tasks without the pattern catalog reference. If spec produces the same plan structure anyway, the catalog isn't adding value (which would be fine for these obvious cases — the real value is for ambiguous tasks).

**Feature 4 — Agent Teams cleanup:**
- Grep the plugin for `TeamCreate`, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, "Tier 3"
- Run gigo:execute on a small plan. Confirm only Subagents + Inline are offered.
- **Pass criterion:** no Tier 3 references in production paths. Design doc exists at `skills/execute/references/agent-teams-design.md` with status banner.
- No comparison needed — this is a removal.

### Layer 2: Incremental Value Test — "Is v0.12 better than v0.11?"

This is the harder test. Extend the existing eval framework to answer: does GIGO with these features produce better output than GIGO without them?

**Approach: "Version A/B" eval**

Similar to the existing bare-vs-assembled eval, but both sides have full GIGO context. The variable is the 4 new features.

- **Version A (control):** GIGO assembly WITHOUT boundary-mismatch criteria, WITHOUT pattern catalog, WITHOUT phase selection matrix
- **Version B (treatment):** GIGO assembly WITH all 4 features

**New fixture needed:** The existing Rails API and Children's Novel fixtures are good for baseline regression but don't stress-test integration boundaries or execution pattern selection. Add a third fixture:

- **Full-stack integration fixture** — a small project with API routes, frontend hooks, state management, and deliberate integration seams. This stresses feature 1 (boundary detection) and feature 3 (execution patterns for multi-layer tasks).

**New prompts needed:** 8-10 prompts per fixture that exercise the new features:
- "Review this API integration" (boundary detection)
- "Plan a migration that touches the API, frontend hooks, and database schema" (execution patterns)
- "I just added a new data model — what else needs to change?" (phase selection matrix thinking)
- "Audit this codebase for issues" (sweep with boundary awareness)

**Judge prompt extension:** The current 5 criteria may not capture boundary awareness. Consider adding:
- **Integration awareness (0-3):** Does the response identify cross-boundary concerns — mismatches between layers, assumptions that don't hold across API boundaries?

Or extend the existing "expertise routing" criterion to include integration boundary recognition.

**Scoring:**
- Run both versions against the same prompts
- Blinded A/B with the existing judge pipeline
- Compare win rates: does treatment outperform control?

### Layer 3: Regression Check — "Did we break anything?"

Rerun the existing 20-prompt eval (Rails API + Children's Novel) with the current GIGO version.

- Compare to the Phase 4 result (96%+ assembled wins)
- If win rate drops below 90%, something regressed
- Specific risk: the boundary-mismatch criteria in review-criteria.md might add noise to reviews of projects that don't have integration boundaries (like the Children's Novel fixture). If novel reviews get worse, the criteria need scoping.

## Practical Considerations

**Token cost:** Each eval prompt = 2 Claude invocations (A + B) + 1 judge invocation. 20 existing prompts + 10 new prompts = 90 invocations per run. At ~1000 tokens average response, this is ~90K tokens per run. Cheap enough to run multiple times.

**Time:** The existing eval runs sequentially (not parallel). With 30 prompts, expect ~15-20 minutes per run. Could be parallelized with background processes.

**Results location:** Per existing plan (`project_eval_repo_split.md`), eval results should eventually go to a separate repo. For now, keep in `evals/results/` with timestamps. This validation suite might be the forcing function that makes the split worth doing.

**Fixture creation cost:** The seeded-defect fixture (Layer 1, feature 1) is the most work — it needs to be a realistic-enough project that the seeded bugs aren't obvious from context. But it doesn't need to be large. 5-10 files with deliberate integration boundaries is enough.

## What This Blueprint Should Produce

1. **Seeded-defect fixture** in `evals/fixtures/` for boundary-mismatch testing
2. **New prompts** in `evals/prompts/` that exercise the 4 new features
3. **Extended judge prompt** (or a second judge prompt) that captures integration awareness
4. **Version A/B test script** — like run-eval.sh but comparing two assembled versions instead of assembled vs bare
5. **Test execution plan** — which tests to run first, what constitutes pass/fail, when to stop

## What This Blueprint Should NOT Produce

- A new eval framework. The existing one works. Extend it.
- Theoretical test designs with no fixtures. The blueprint should produce runnable tests.
- Tests for features that don't exist yet (Agent Teams execution). Feature 4 is verification-only.

## Open Questions

- Should the seeded-defect fixture be a real technology (Next.js + TypeScript) or a simplified mock? Real tech is more realistic but harder to set up and maintain. A mock project with fake API routes and types might test the pattern recognition just as well.
- Should Layer 2 (version A/B) use the same judge prompt as the existing eval, or does boundary awareness need its own scoring criteria?
- How do we handle the phase selection matrix test (feature 2)? It's about gigo:maintain's behavior, not about assembled context quality. The existing eval framework doesn't test skill behavior — it tests output quality. This might need a different kind of test (scenario-based, not comparative).
- Is Carlos's prompt (from `feedback_carlos_first_test.md`) worth including as a regression benchmark? It tests end-to-end pipeline quality, not specific features, but it's the only real-world baseline we have.

## Sources

- `evals/EVAL-NARRATIVE.md` — full eval history and methodology
- `evals/run-eval.sh` — existing bare vs assembled runner
- `evals/score-eval.sh` — existing blinded A/B scorer
- `evals/judge-prompt.md` — existing 5-criteria judge
- `evals/fixtures/` — existing Rails API + Children's Novel fixtures
- `evals/prompts/` — existing 10-prompt-per-domain prompt files
- Memory: `feedback_carlos_first_test.md` — first real-world test results
- Memory: `project_eval_repo_split.md` — eval results need separate repo
