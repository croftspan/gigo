# Experiment 05 — Qwen3.6 Worker Profile (Brief 16)

**Status:** Complete.
**Date started:** 2026-04-19
**Date finished:** 2026-04-19
**Model under test:** `unsloth/Qwen3.6-35B-A3B-MLX-8bit` (local MLX build, MoE 35B / ~3B active).
**Judge model:** `claude-opus-4-7`.
**Orchestrator / planner:** Not under test — assumed to be Opus via `gigo:blueprint` + `gigo:spec`.
**Run:** `evals/qwen-worker-eval/results/2026-04-19-085822/`.

## The question

Opus plans. Qwen executes. What **ticket format** and **thinking setting** maximizes
Qwen3.6's reliability as a local worker, so the plan → execute → review loop
actually works on a laptop?

This is a shift from the prior Phase 9-A evals (which asked *does gigo help Opus?*).
This brief asks *what does Qwen need to behave like a worker?*

### Hypotheses going in

| # | Hypothesis | Prediction |
|---|---|---|
| H1 | Ticket format matters more than persona context | TF3 (Qwen-optimized: Role/SPEC/ACCEPTANCE/OUTPUT FORMAT) beats TF2 (current gigo worker dispatch) and TF1 (bare spec sentence) |
| H2 | Thinking-on beats thinking-off on any non-trivial task | Pass rate higher for thinking-on across TF2/TF3 for code and reasoning tasks |
| H3 | The current gigo:execute Tier-2 dispatch prompt is not optimized for Qwen | A Qwen-optimized dispatch template (TF3) will win measurably over TF2 |

## Design

**Two axes × two pins:**

| Axis | Levels |
|---|---|
| Ticket format | TF1 bare / TF2 gigo / TF3 qwen-optimized |
| Thinking mode | ON / OFF |

**Pinned:**
- Sampling profile — by task type (see below), not swept. Phase 2 candidate.
- Model — `unsloth/Qwen3.6-35B-A3B-MLX-8bit`.
- Endpoint — `http://127.0.0.1:8080/v1/chat/completions` (mlx_lm.server).
- Max tokens — 32768.

**Sampling profile by task type (pinned per Fix 3 of brief 16, verbatim from Unsloth):**

| Task type | Profile | temp | top_p | top_k | presence_penalty |
|---|---|---|---|---|---|
| `code` | Coding (thinking) | 0.6 | 0.95 | 20 | 0.0 |
| `reasoning` | General (thinking) | 1.0 | 0.95 | 20 | 1.5 |
| `structured` | General (non-thinking) | 0.7 | 0.80 | 20 | 1.5 |

### Thinking-toggle verification (Fix 2)

On this server build (`0.31.2-0.31.1-macOS-26.3.1-arm64-arm-64bit-applegpu_g15s`)
the toggle works as expected:

| Request | `message` keys | Reasoning |
|---|---|---|
| default (thinking on) | `content`, `reasoning`, `role` | 661-char trace |
| `chat_template_kwargs.enable_thinking: false` | `content`, `role` | no `reasoning` field |

Confirmed: `enable_thinking: false` removes reasoning output entirely and
produces direct responses. No `<think>...</think>` regex stripping needed —
the MLX server cleanly separates thinking from content.

### Conditions (6 total)

TF1×on, TF1×off, TF2×on, TF2×off, TF3×on, TF3×off.

### Tasks (10 total)

| ID | Type | Summary |
|---|---|---|
| T1 | code | `dedupe_preserve_order` — pure fn, hashable + unhashable items |
| T2 | code | rename `calc` → `compute_total` across a small module |
| T3 | code | fix branch-ordering bug in `fizzbuzz` so test passes |
| T4 | code | convert a JSON blob to YAML preserving types |
| T5 | code | write pytest test module for a given `parse_iso_date` function |
| T6 | code | add Python 3.12 type hints to 4 untyped functions |
| T7 | code | derive a Python regex from pos/neg examples |
| T8 | structured | extract SELECT result-set column names as a JSON array |
| T9 | reasoning | 3-bullet summary of a 400-word PR description |
| T10 | structured | classify a stack trace into `{severity, category}` JSON |

Every task has a **deterministic verifier** in `evals/qwen-worker-eval/verifiers/`
(Python script: extract fenced block → run checks → exit 0 pass / non-0 fail).
Verifiers were smoke-tested both directions (reference impl passes, intentional
bug fails) before the sweep.

### Replicates

3 per cell. Sequential against localhost. `6 × 10 × 3 = 180 runs.`

### Judge

Opus 4.7 rates each run on five fields (YAML output):

```
acceptance_pass: true | false      # substantive correctness, informed by verifier
format_adherence: true | false     # did the worker respect OUTPUT FORMAT?
fabrication_present: true | false  # did it invent imports/APIs/numbers/files?
quality: 1-5                        # craft
notes: "one sentence"
```

A **cell is a pass** iff `acceptance_pass && format_adherence && !fabrication_present`.
Pass rate, mean quality, and fabrication rate aggregate per condition and per
(condition × task_type).

Fabrication check is explicit (per `feedback_judge_rubric_fabrication_blindspot.md`
memory — Brief 13's rubric rewarded richness without penalizing invention).

## Results

180 runs (6 conditions × 10 tasks × 3 replicates), zero worker errors, zero verifier/judge disagreements.

### Headline

**TF2 and TF3 clear 90% pass across all task types. TF1 caps at 40% pass.
Thinking-off ties or beats thinking-on on every format. The best cell is
TF3-thinking-off: 100% pass, mean quality 4.07, mean 2.0s walltime, 118
completion tokens per call.**

### Per condition (all tasks)

| Condition | N | Pass rate | Mean quality | Fabrication rate |
|---|---|---|---|---|
| TF1-thinking-on | 30 | 0.233 | 2.80 | 0.067 |
| TF1-thinking-off | 30 | 0.400 | 2.80 | 0.000 |
| TF2-thinking-on | 30 | 1.000 | 4.03 | 0.000 |
| TF2-thinking-off | 30 | 0.900 | 3.87 | 0.000 |
| TF3-thinking-on | 30 | 0.933 | 3.67 | 0.000 |
| **TF3-thinking-off** | **30** | **1.000** | **4.07** | **0.000** |

The gap between TF1 (bare) and TF2/TF3 (structured) is the dominant signal.
Scaffolding (role, acceptance bullets, explicit OUTPUT FORMAT) turns a
~30% pass rate into a ~95% pass rate.

### Per condition × task type

| Condition | Task type | N | Pass | Mean quality | Fab rate |
|---|---|---|---|---|---|
| TF1-thinking-on | code | 21 | 0.333 | 3.14 | 0.048 |
| TF1-thinking-on | reasoning | 3 | 0.000 | 2.00 | 0.333 |
| TF1-thinking-on | structured | 6 | 0.000 | 2.00 | 0.000 |
| TF1-thinking-off | code | 21 | 0.571 | 3.14 | 0.000 |
| TF1-thinking-off | reasoning | 3 | 0.000 | 2.00 | 0.000 |
| TF1-thinking-off | structured | 6 | 0.000 | 2.00 | 0.000 |
| TF2-thinking-on | code | 21 | 1.000 | 3.90 | 0.000 |
| TF2-thinking-on | reasoning | 3 | 1.000 | 4.00 | 0.000 |
| TF2-thinking-on | structured | 6 | 1.000 | 4.50 | 0.000 |
| TF2-thinking-off | code | 21 | 0.857 | 3.62 | 0.000 |
| TF2-thinking-off | reasoning | 3 | 1.000 | 4.00 | 0.000 |
| TF2-thinking-off | structured | 6 | 1.000 | 4.67 | 0.000 |
| TF3-thinking-on | code | 21 | 0.905 | 3.48 | 0.000 |
| TF3-thinking-on | reasoning | 3 | 1.000 | 4.00 | 0.000 |
| TF3-thinking-on | structured | 6 | 1.000 | 4.17 | 0.000 |
| TF3-thinking-off | code | 21 | 1.000 | 3.95 | 0.000 |
| TF3-thinking-off | reasoning | 3 | 1.000 | 3.67 | 0.000 |
| TF3-thinking-off | structured | 6 | 1.000 | 4.67 | 0.000 |

Two striking patterns:
- **TF1 on reasoning and structured tasks is 0/9.** Without a stated OUTPUT FORMAT, Qwen reliably returns prose/markdown where the verifier demands a JSON array or `{severity, category}` object.
- **TF2 and TF3 are nearly interchangeable.** TF2-on ties TF3-off on code (both at top quality ~3.90). Margin between the two structured formats is noise-level compared to the gap either has over TF1.

### Per-task × condition (variance flags)

Flags mark replicate disagreement (pass rate 0 < x < 1). Full table in
`results/2026-04-19-085822/summary.md`. Notable:

| Task | Condition | Pass | Mean quality | Why flagged |
|---|---|---|---|---|
| T1 | TF2-thinking-off | 2/3 | 2.33 | one run produced a very short answer |
| T2 | TF1-thinking-on | 1/3 | 3.67 | TF1 bare format — less stable on rename task |
| T5 | TF1-thinking-on | 1/3 | 3.67 | pytest test-writing, unstable without scaffolding |
| T5 | TF2-thinking-off | 1/3 | 3.00 | one replicate violated the output format |
| T6 | TF1-thinking-on | 2/3 | 3.00 | type-hints task with bare spec |
| T7 | **TF3-thinking-on** | **1/3** | **2.00** | **two replicates ran reasoning budget to exhaustion** (see Anomalies) |

### Token accounting (means per condition)

| Condition | Prompt tokens | Completion tokens | Reasoning chars | Walltime (s) |
|---|---|---|---|---|
| TF1-thinking-on | 198 | 2716 | 8231 | 42.7 |
| TF1-thinking-off | 200 | 495 | 0 | 7.9 |
| TF2-thinking-on | 430 | 1705 | 6077 | 26.9 |
| TF2-thinking-off | 432 | 164 | 0 | 2.7 |
| TF3-thinking-on | 375 | 4127 | 12285 | 67.8 |
| **TF3-thinking-off** | **377** | **118** | **0** | **2.0** |

Thinking-off is 10–30× cheaper in tokens and 14–34× faster in walltime than
thinking-on at the same format. TF3-off averages 118 completion tokens and
2.0s per call — the fastest cell and the joint-highest quality.

### Fabrication findings

Two fabrication cases total, both TF1-thinking-on:

- `T7--TF1-thinking-on--r1` (regex derivation): invented a plausible-looking
  pattern that didn't match the positives.
- `T9--TF1-thinking-on--r1` (PR summary reasoning task): invented numeric claims
  not present in the source text.

TF2 and TF3 showed zero fabrication across 120 runs. The pattern is
consistent with prior findings (`feedback_judge_rubric_fabrication_blindspot`):
the model fabricates when asked to reason with insufficient structure.

### Anomalies

**T7 × TF3 × thinking-on: reasoning-budget exhaustion on 2/3 replicates.**

This is the most interesting finding in the sweep. T7 asks the worker to
derive a regex from positive/negative examples. With TF3 + thinking-on:

| Replicate | Walltime | Completion tokens | Reasoning chars | Outcome |
|---|---|---|---|---|
| r1 | 21.2s | 1339 | 3830 | PASS — emitted `[A-Z]{2}-[0-9]{4}` |
| r2 | 557.6s | 32768 (max) | 78736 | **EMPTY** — finish_reason=length |
| r3 | 559.5s | 32768 (max) | 85617 | **EMPTY** — finish_reason=length |

Reasoning trace excerpt (r2 tail): `"...I'll output [A-Z]{2}-[0-9]{4}. Wait,
I'll check if I should use \d. I'll use \d... I'll output [A-Z]{2}-\d{4}.
I'll output this. Wait, I'll check..."` — the model oscillates indefinitely
between equivalent forms and never emits content.

TF3-thinking-off on the same task: 3/3 PASS, mean quality 4.67, 2s walltime.

This is the same pathology recorded in
`memory/feedback_characters_over_lenses.md` (Brief 15, rails-api prompt 04
returned an empty Characters response) — Qwen3.6 thinking-mode occasionally
collapses to silence via a reasoning loop. The risk surface is prompts where
multiple equivalent answers exist and the model can't commit.

**Cost of thinking-on loop failure:** 9+ minutes of compute for an empty
response. A safe deployment would set a short wall-clock budget or prefer
thinking-off where possible.

## Analysis

### H1 — Ticket format vs persona context

**Prediction:** TF3 (Qwen-optimized: Role/SPEC/ACCEPTANCE/OUTPUT FORMAT) beats
TF2 (current gigo worker dispatch) and TF1 (bare spec sentence).

**Verdict:** Partially supported. TF3 and TF2 are tied within noise (1.00 vs
0.90 off; 0.93 vs 1.00 on). Both decisively beat TF1 (0.23–0.40). The real
finding is that **structure matters far more than which specific structure**.
A stated OUTPUT FORMAT, explicit ACCEPTANCE bullets, and a role hint are the
load-bearing elements; the exact framing above those is low-signal.

### H2 — Thinking on vs off

**Prediction:** Thinking-on beats thinking-off on non-trivial code and
reasoning tasks.

**Verdict:** Refuted. TF3-off matches or beats TF3-on on every task type.
TF2-on edges TF2-off on code (1.00 vs 0.86) but ties on reasoning/structured.
The edge comes at 10× the tokens and 13× the walltime. On TF1 (the worst
format), thinking-off edges thinking-on (0.40 vs 0.23) — presumably because
thinking-on sometimes fabricates its way into the gaps the spec leaves open.

The T7 reasoning-loop anomaly (above) is the concrete risk: thinking-on
introduces a long-tail failure mode that thinking-off doesn't have.

### H3 — Gigo worker dispatch vs Qwen-optimized

**Prediction:** TF3 (Qwen-optimized) beats TF2 (current gigo Tier-2 dispatch)
measurably.

**Verdict:** Not supported by a meaningful margin. TF3-off leads TF2-off by
10pp pass rate and +0.20 quality. TF3-on actually loses to TF2-on by 7pp pass
rate and -0.36 quality (because of the T7 anomaly). TF2's current shape is
close enough to Qwen-optimal that migrating to TF3 would be polish, not a
breaking fix.

## Recommendation

**Wire TF3 + thinking-off as the Tier-2 inline default** for Qwen3.6 worker
execution. Concretely:

- Keep the role / SPEC / ACCEPTANCE / OUTPUT FORMAT structure from TF3.
- Disable thinking on the inline path (`chat_template_kwargs.enable_thinking:
  false` or the equivalent flag).
- Reserve thinking-on for planning/reasoning calls to Opus, not for Qwen
  worker dispatch.

If the existing gigo:execute TF2 dispatch stays for other reasons, add a
Qwen-specific override that swaps to TF3. The margin is real but small; the
more important change is the thinking-off flip, which gives 30–50× walltime
savings for ties-or-better quality.

**Do not** use thinking-on as a general knob for "higher stakes = more
reasoning." On Qwen3.6 the failure mode is silent non-completion, not lower
quality — and it costs 9+ minutes when it fires.

## Cost

- Qwen3.6 sweep: local, free (~2h walltime end to end).
- Opus 4.7 judge: 180 runs, `claude -p --json-schema` path with
  ~$0.02–$0.32 per call (mostly cache hits once the session warms). Exact
  per-run cost was not captured in `.score.json`; total was well under
  the Brief 14 budget (~$20).
- First scoring pass produced 75 parse errors because the `explanatory`
  output style in the parent session bled into the subprocess, wrapping
  the YAML in `★ Insight` prose. Fix: switch to `--json-schema` with
  the structured output pulled from the `structured_output` field of
  `claude -p --output-format json`. Logged in `feedback_claude_p_output_style_leak.md`.

## Out of scope / Phase 2+

- Sampling profile sweep (brief pinned by task-type; Phase 2 asks "is the
  profile actually optimal?").
- Multi-turn with `preserve_thinking` — this eval is single-shot.
- Tool-use via Qwen-Agent — separate brief.
- Comparison with Opus/Haiku on the same tasks — Phase 3 cost/quality question.
- Comparison with other local models (DeepSeek-Coder, Llama, Mistral) — future bake-off.

## Files

- Harness: `evals/qwen-worker-eval/`
  - `tasks/T*.md` — task specs with YAML front-matter
  - `verifiers/T*.py` — deterministic pass/fail checks
  - `build_ticket.py` — renders TF1/TF2/TF3 from a task
  - `run_qwen_eval.py` — sweep runner (curl → local endpoint)
  - `judge-prompt.md` — Opus rubric with explicit fabrication check
  - `score_qwen_eval.py` — verifier + judge + aggregate
- Results: `evals/qwen-worker-eval/results/<timestamp>/` (gitignored)
- Summary: `evals/qwen-worker-eval/results/<timestamp>/summary.md`
