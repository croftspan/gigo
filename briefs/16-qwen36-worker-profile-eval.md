# Kickoff: Qwen3.6 Worker Profile Eval (Brief 16)

**Date:** 2026-04-19
**Previous work:** Briefs 13–15 established the v0.14 + Opus 4.7 picture. Characters > Lenses, ~2000-word context ceiling is domain-dependent, full gigo wins 99/100 criteria.
**This brief:** Switch from Opus-vs-bare to **"how do we make Qwen3.6 a reliable local worker?"** Opus still plans via `gigo:blueprint` and `gigo:spec`. Qwen3.6 executes. We want to find the ticket format + runtime config that maximizes Qwen's worker reliability.

---

## Why this brief

The Unsloth model page and `/Users/eaven/plzhalp/README.md` are explicit: **Qwen3.6 is a worker, not an orchestrator.** No file access, no browser, no shell on the local MLX build. Its superpower is cheap high-quality thinking on whatever gets pasted into context.

The product hypothesis: Opus plans (expensive, ~$5 per plan), Qwen3.6 executes (free, local), Opus or Claude Code reviews. This brief tests **what input structure maximizes Qwen3.6's output quality** so the plan → execute → review loop actually works on a laptop.

Three working hypotheses going in:

- **H1 — Ticket format matters more than persona context.** Qwen3.6 doesn't need the team roster (no expertise routing — it's a single model); it needs the task described the way the README prescribes: Role / Spec / Acceptance / Output Format / Mode Hint.
- **H2 — Thinking-on beats thinking-off for any non-trivial task**, because the README explicitly warns thinking quality degrades below 128K context and says the training target is thinking-mode reasoning.
- **H3 — The current `gigo:execute` Tier 2 inline dispatch prompt format won't be optimal for Qwen** — it was written for Opus. A Qwen-optimized dispatch template will win measurably.

---

## Context you need (read in this order)

1. `/Users/eaven/plzhalp/README.md` — the ground-truth reference for how Qwen3.6 behaves. Thinking mode, sampling profiles, ticket format, context budget. Everything in this brief leans on it.
2. `evals/run-eval.sh` — the current harness pattern (OpenAI-style single-shot). Your new harness forks this, but replaces `claude -p` with `curl` to `http://127.0.0.1:8080/v1/chat/completions`.
3. `evals/score-eval.sh` + `evals/judge-prompt.md` — the judge pattern. You'll write a new judge prompt for worker-task evaluation (acceptance-criteria pass/fail + quality + fabrication check).
4. `skills/execute/references/teammate-prompts.md` — the current gigo:execute dispatch prompt template. This is "TF2 — gigo format" in the sweep.
5. `docs/gigo/experiments/04-opus-4-7-lenses-vs-characters.md` — shape of what a completed writeup looks like.
6. Most recent Opus eval: `evals/results/` — fixture SHAs, harness hygiene patterns.

## Endpoint smoke test

Run this **before anything else** to confirm the server is live:

```bash
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "unsloth/Qwen3.6-35B-A3B-MLX-8bit",
    "messages": [{"role":"user","content":"respond with just: OK"}]
  }' | jq '.choices[0].message.content'
```

Expect `"OK"` or `"OK\n"`. If the server isn't running, start it (see `~/plzhalp` — `./wakeup` helper).

Key response-shape fact (confirmed): thinking blocks come back in `choices[0].message.reasoning` (array), **separate from** `choices[0].message.content`. You don't need to regex-strip `<think>…</think>` from content — the server already separates them. Save `reasoning` to results for audit; score on `content`.

---

## REQUIRED pre-flight fixes

### Fix 1 — Pin the exact model string

Every request uses `"model": "unsloth/Qwen3.6-35B-A3B-MLX-8bit"` verbatim. Not `"qwen3.6"`, not `"qwen"`. The server may route based on the full string.

### Fix 2 — Verify the thinking toggle

Before running the full sweep, confirm `chat_template_kwargs.enable_thinking` actually toggles thinking on this build:

```bash
# Thinking ON (default)
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"unsloth/Qwen3.6-35B-A3B-MLX-8bit","messages":[{"role":"user","content":"What is 23*47?"}]}' \
  | jq '.choices[0].message | keys'
# Expect: ["content","reasoning","role"] with non-empty reasoning

# Thinking OFF
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"unsloth/Qwen3.6-35B-A3B-MLX-8bit","messages":[{"role":"user","content":"What is 23*47?"}],"chat_template_kwargs":{"enable_thinking":false}}' \
  | jq '.choices[0].message | keys'
# Expect: ["content","role"] — no reasoning field, or empty
```

If the toggle doesn't work on this server build, flag it immediately — the thinking-mode axis of the sweep depends on it. Fallback: use `QWEN_THINK=0` via `./wakeup ask` subprocess instead of raw curl.

### Fix 3 — Set sampling profile per task type (don't use defaults)

The README is explicit: sampling profile is tuned per task type. For this eval:

| Task type | Profile | temp | top_p | top_k | presence_penalty |
|---|---|---|---|---|---|
| Code tasks (pure fn, refactor, test-gen) | Coding (thinking) | 0.6 | 0.95 | 20 | 0.0 |
| Reasoning tasks (bug-fix-from-test, summarization) | General (thinking) | 1.0 | 0.95 | 20 | 1.5 |
| Simple structured (classification, extraction) | General (non-thinking) | 0.7 | 0.8 | 20 | 1.5 |

Sampling profile is **pinned by task type** in this brief, not swept. Profile sweep is Phase 2.

### Fix 4 — Context budget floor

Per the README: "maintain a context length of at least 128K tokens to preserve thinking capabilities." Set `max_tokens` generously in requests (e.g., `32768`). Don't cap tiny.

### Fix 5 — Local-endpoint stability

180 sequential requests against a local MoE model will stress the server. Between requests, add a small delay (`sleep 1`) to let the KV cache settle. If a request times out (MoE first-token latency can spike), retry once with the same seed before failing.

---

## The sweep

**Two axes × two pins:**

| Axis | Levels |
|---|---|
| Ticket format | TF1 bare / TF2 gigo / TF3 qwen-optimized |
| Thinking mode | ON / OFF |

**Pinned per task type:** sampling profile (per Fix 3), model, endpoint.

### Ticket formats

**TF1 — Bare.** Just the spec sentence. E.g., `"Implement a function dedupe_preserve_order that removes duplicates while preserving first-occurrence order. Handle unhashable items."` No role, no acceptance list, no output format.

**TF2 — Gigo (current).** The current `gigo:execute` Tier 2 inline dispatch prompt template, filled with the task's spec + acceptance + the "What Was Built" addendum pattern. This is what `skills/execute/references/teammate-prompts.md` produces today.

**TF3 — Qwen-optimized.** Per the README's "How to task it" section:
- **Role/context** — one sentence
- **SPEC** — inputs, outputs, constraints
- **ACCEPTANCE** — bullet list, testable
- **OUTPUT FORMAT** — exactly the shape expected back (fenced block, no preamble)
- **Mode hint** — optional, e.g., "Use a single pass, no class."

See the README's coding-ticket example (lines 69–93) for the canonical shape.

### Conditions (6 total)

TF1×thinking-on, TF1×thinking-off, TF2×thinking-on, TF2×thinking-off, TF3×thinking-on, TF3×thinking-off.

### Tasks

**10 worker tasks across 3 types. Each task is a self-contained file in `evals/qwen-worker-eval/tasks/T{N}-{name}.md` with:**
- `spec:` — the requirement
- `acceptance:` — bulleted testable criteria (at least one must be deterministically verifiable — e.g., a unit test the output must pass)
- `output_format:` — shape expected
- `task_type:` — `code | reasoning | structured`
- `ground_truth:` (optional) — reference implementation or expected output for spot-checking

**Suggested task slate (pick 10 total, cover all 3 types):**

Code (6–8):
1. `T1-dedupe-preserve-order` — pure function (README example canonical form)
2. `T2-rename-refactor` — given a Python file, rename a symbol consistently
3. `T3-bugfix-from-failing-test` — given a broken function + a failing test, fix the function
4. `T4-json-to-yaml` — convert a JSON blob to YAML preserving types
5. `T5-write-test-for-function` — given a function, produce a pytest test file
6. `T6-add-type-hints` — given a Python file without hints, add correct type hints
7. `T7-regex-from-examples` — given positive + negative examples, produce a regex
8. `T8-extract-sql-columns` — given a SELECT statement, output the column names as a JSON array

Reasoning (1–2):
9. `T9-summarize-pr-description` — given a 400-word PR description, produce a 3-bullet summary

Structured (1–2):
10. `T10-classify-error-log` — given a stack trace, output `{"severity": "fatal|error|warn", "category": "..."}`

### Replicates

3 runs per cell for variance. 6 conditions × 10 tasks × 3 replicates = **180 runs.**

Sequential against localhost. At ~30s/task conservative, that's ~90 minutes walltime. Local + free, so no cost constraint.

### Judge

Opus scores each output. New prompt at `evals/qwen-worker-eval/judge-prompt.md`. Per-run scoring:

```yaml
task: T1-dedupe-preserve-order
condition: TF3-thinking-on
replicate: 2
scores:
  acceptance_pass: true | false   # deterministic where possible (run the test)
  format_adherence: true | false  # did it respect OUTPUT FORMAT?
  fabrication_present: true | false  # did it invent files, imports, APIs that don't exist?
  quality: 1-5                    # overall craft
notes: "one sentence explaining any flag"
```

Aggregate per condition:
- Pass rate (% of replicate-task cells where `acceptance_pass && format_adherence && !fabrication_present`)
- Mean quality (1–5)
- Fabrication rate (% with `fabrication_present == true`)

### Variance check

For each task, compute across the 3 replicates: are all 3 outputs the same pass/fail verdict? If 2/3 pass and 1/3 fails, flag that task's sensitivity in the writeup — it's a candidate for more replicates.

---

## Deterministic ticket builders

One script per format at `evals/qwen-worker-eval/build-ticket.sh`:

```bash
./build-ticket.sh TF1 T1-dedupe-preserve-order   # emits bare ticket to stdout
./build-ticket.sh TF2 T1-dedupe-preserve-order   # emits gigo-format ticket
./build-ticket.sh TF3 T1-dedupe-preserve-order   # emits qwen-optimized ticket
```

Pure function of the task file. Same task + same TF always produces the same ticket. Comparisons stay valid across re-runs.

---

## Harness

New directory: `evals/qwen-worker-eval/`

```
evals/qwen-worker-eval/
├── tasks/
│   ├── T1-dedupe-preserve-order.md
│   ├── T2-rename-refactor.md
│   └── ...
├── build-ticket.sh           # deterministic ticket builder (TF1 | TF2 | TF3)
├── run-qwen-eval.sh          # the main runner — replaces claude -p with curl
├── judge-prompt.md           # Opus judge rubric for worker tasks
├── score-qwen-eval.sh        # runs Opus over results/*.json → summary.md
└── results/
    └── {timestamp}/
        ├── {task}-{condition}-{replicate}.json   # raw server response
        ├── {task}-{condition}-{replicate}.content.txt  # extracted message.content
        ├── {task}-{condition}-{replicate}.reasoning.txt  # extracted reasoning (for audit)
        └── summary.md
```

The runner loops tasks × conditions × replicates, posts to the local endpoint, saves raw JSON + extracted content + extracted reasoning. Scorer loops results, dispatches Opus judge, aggregates.

Gitignore `evals/qwen-worker-eval/results/` — same pattern as existing eval results.

---

## Run protocol

1. Start the local server (verify `curl` smoke test returns OK).
2. Run Fix 2 — confirm thinking toggle works on this server build.
3. Write the 10 task files. Each must have a deterministically-verifiable acceptance criterion (unit test for code tasks; exact-match or format-valid for structured tasks).
4. Write `build-ticket.sh` — test all 3 formats produce valid output for task T1.
5. Write `run-qwen-eval.sh` — dry-run with 1 task × 1 condition × 1 replicate first, confirm the pipeline works end-to-end.
6. Run the full sweep (180 runs). Monitor for server crashes or timeouts. Expect ~60–120 minutes walltime.
7. Write `judge-prompt.md` + `score-qwen-eval.sh`. Run scoring. Expect 5–10 minutes + ~$3–5 Opus spend.
8. Read the summary. Cross-check anomalies against raw content files.
9. Writeup at `docs/gigo/experiments/05-qwen36-worker-profile.md`.

---

## What the writeup needs to cover

- Model: `unsloth/Qwen3.6-35B-A3B-MLX-8bit`, endpoint `127.0.0.1:8080`, server build + date pinned.
- Sampling profiles used per task type (verbatim table from Fix 3).
- Thinking toggle verification result (did `chat_template_kwargs.enable_thinking:false` actually disable it on this build?).
- Per-condition table: pass rate, mean quality, fabrication rate (6 rows).
- Per-task-type breakdown: does the winning format differ for code vs reasoning vs structured?
- Per-task anomaly callouts: any task with 2-of-3 replicate disagreement.
- Fabrication findings: Qwen3.6 is a smaller model than Opus — does it invent imports, functions, or APIs? Rate + examples.
- Thinking mode ablation: does thinking-on beat thinking-off by enough to justify the token cost? (Thinking traces can run 1–10k tokens; non-thinking is direct.)
- Token accounting per condition: mean input tokens, mean output tokens, mean reasoning tokens.
- Hypothesis verdicts: H1/H2/H3 supported, refuted, mixed.
- Recommendation: which TF + thinking setting to wire into `gigo:execute` Tier 2 inline as the "local worker" option. Or: Qwen3.6 not reliable enough for default worker dispatch — gate behind opt-in flag.
- Phase 2/3 candidates.

---

## Out of scope for this session

- **Tool use / MCP / Qwen-Agent loops.** Separate brief. Per the README, tool-calling on this MLX build needs Qwen-Agent because `mlx_lm.server` doesn't parse native Qwen tool calls. That's a wiring project, not an eval.
- **Multi-turn with `preserve_thinking`.** Separate brief. This eval is single-shot per task. `preserve_thinking` is 3.6's signature feature, but testing it needs multi-turn tasks and a different harness.
- **Sampling profile sweep.** Phase 2. This brief pins profile by task type per README. Phase 2 asks "is the README profile actually optimal, or can we do better?"
- **Orchestration by Qwen.** Confirmed wrong-stack by README. Opus plans, Qwen executes.
- **Comparison with Opus or Haiku on same tasks.** Phase 3 cost/quality tradeoff question. Out of scope here.
- **Comparison with other local models** (Llama, Mistral, DeepSeek-Coder). Future bake-off.
- **YaRN-extended context.** README warns against enabling YaRN unless the task actually needs >256K. None of these worker tasks do.
- **Modifying any `skills/execute/` file.** Even if the eval finds TF3 wins decisively, wiring Qwen into `gigo:execute` is a separate design → spec → execute cycle. This brief produces the data + recommendation only.
- **Touching existing fixtures** (`evals/fixtures/rails-api/`, `evals/fixtures/childrens-novel/`). Those are for Claude evals. Qwen worker tasks are net-new, in `evals/qwen-worker-eval/tasks/`.

---

## Relevant memories

- `feedback_eval_harness_hygiene.md` — three eval-methodology rules (pin the model, bare-contamination glob, regression-vs-refresh). Rules 1 and 3 apply directly — pin the Qwen model string, preserve tasks once written.
- `feedback_judge_rubric_fabrication_blindspot.md` — Brief 13 found the judge rubric rewarded richness without penalizing fabrication. **Carry this forward:** the Qwen judge prompt MUST include an explicit fabrication check ("did the response reference files, imports, functions, or APIs that don't exist or weren't provided in the ticket?"). Smaller models fabricate more; the rubric must catch it.
- `feedback_haiku_extraction_embellishment.md` and `feedback_subagent_fabrication_risk.md` — related findings that smaller/non-Opus models embellish or invent. Warn the judge to look for this.
- `feedback_right_context_for_the_job.md` — the core GIGO principle. Workers need specs with conventions, not personas. This brief tests exactly that claim for Qwen specifically.
- `project_gemma_executor_architecture.md` and `project_cosmogene_architecture.md` — prior attempts at local-executor architectures. Context for why this matters.
- `feedback_characters_over_lenses.md` — persona style findings from Brief 15. **Applies if** you use any fixture-derived context for Qwen, but this brief uses self-contained tasks, so the roster isn't a variable. Worth noting: Qwen has no team; expertise-routing isn't a feature it can use.

---

## Deliverables

1. `evals/qwen-worker-eval/` directory with harness, tasks, builder, judge, scorer, gitignored results.
2. Full sweep results at `evals/qwen-worker-eval/results/{timestamp}/` (gitignored).
3. Writeup at `docs/gigo/experiments/05-qwen36-worker-profile.md`.
4. Memory update: `feedback_qwen36_worker_profile.md` with the winning TF + thinking config and the fabrication rate observed.
5. Append Phase 9-B section to `evals/EVAL-NARRATIVE.md` — this is a distinct thread from the Opus evals (Phase 9-A = Briefs 13–15).
6. Update `MEMORY.md` with a pointer to the new `feedback_qwen36_worker_profile.md`.
7. One-paragraph recommendation on whether to wire Qwen3.6 into `gigo:execute` Tier 2 inline as the "local worker" option. Do NOT make the wiring change — surface the recommendation for operator approval.
8. Update `evals/EVAL-NARRATIVE.md` Open Questions to reflect which Phase 3 items this brief closed and which remain open.

---

## Starting prompt for the new session

Paste this into a fresh Claude Code session in `/Users/eaven/projects/gigo`:

> Kickoff packet at `briefs/16-qwen36-worker-profile-eval.md`. Read the whole file before doing anything. Prerequisite: local Qwen3.6 server running at `http://127.0.0.1:8080/v1/chat/completions` (smoke test: `curl -sS http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"unsloth/Qwen3.6-35B-A3B-MLX-8bit","messages":[{"role":"user","content":"OK"}]}' | jq '.choices[0].message.content'`). Also read `/Users/eaven/plzhalp/README.md` — the ground-truth reference for how Qwen3.6 behaves. Your job: build `evals/qwen-worker-eval/` from scratch (10 worker tasks, 3 ticket formats TF1/TF2/TF3, 2 thinking modes = 6 conditions × 10 tasks × 3 replicates = 180 runs), run the sweep against the local server, judge with Opus (per-task acceptance pass/fail + quality + fabrication check), produce a recommendation on which ticket format + thinking setting to wire into `gigo:execute` Tier 2 inline as the "local worker" option. Sampling profile pinned per task type per the Fix 3 table (don't sweep it). Writeup lands at `docs/gigo/experiments/05-qwen36-worker-profile.md`. Start with `cat briefs/16-qwen36-worker-profile-eval.md`.
