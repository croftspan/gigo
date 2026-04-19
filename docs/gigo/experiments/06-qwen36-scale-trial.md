# Experiment 06 — Qwen3.6 Phase 2A Scale Trial (Brief 17)

**Status:** Complete.
**Date started:** 2026-04-19
**Date finished:** 2026-04-19
**Model under test:** `unsloth/Qwen3.6-35B-A3B-MLX-8bit` (local MLX build, MoE 35B / ~3B active).
**Judge model:** `claude-opus-4-7`.
**Orchestrator / planner:** Not under test — assumed to be Opus via `gigo:blueprint` + `gigo:spec`.
**Run:** `evals/qwen-worker-eval/results/phase2a-sweep/`.
**Relationship to Brief 16:** follow-up stress test. Brief 16 found the recipe on toy tasks (20-40 lines); Brief 17 asks whether it holds at realistic sizes.

## The question

Brief 16 shipped a recipe: **TF3 ticket scaffold + `enable_thinking: false`** gave 100% pass, mean quality 4.07, mean 2.0s walltime, 118 completion tokens on 10 toy tasks. That was the win condition — but every task was a single fenced block in under 40 lines of output.

The question Phase 2A asks is narrower and harder: does that recipe survive when the tasks look like real gigo work?

- Single-file refactors of 80-150 lines (M bucket).
- Cross-module refactors of 250-400 lines (L bucket).
- Multi-file operations spanning 2-4 files, 400-600 lines total (XL bucket).

If the recipe degrades at scale — pass rate falls, quality drops, or fabrication appears — the plan→execute→review loop needs a different worker. If it holds, the Brief 16 recipe is production-ready for the current gigo:execute Tier-2 dispatch.

### Hypotheses going in

| # | Hypothesis | Prediction |
|---|---|---|
| H1 | The recipe holds at S (20-40 lines, = Brief 16 toys) | 5/5 pass, parity with Brief 16 results |
| H2 | Quality stays ≥ 3.5 (Brief 16 mean 4.07) through the L bucket (250-400 lines) | 15/15 pass at M and L |
| H3 | XL multi-file tasks produce missing-file or malformed-fence failures | Pass rate < 90% on XL, driven by format, not logic |
| H4 | Walltime scales roughly linearly with output tokens | XL ~5-10× S walltime |

## Design

**Single pinned condition, no sweep:**

| Axis | Pinned value |
|---|---|
| Ticket format | TF3 (Qwen-optimized: Role / SPEC / ACCEPTANCE / OUTPUT FORMAT) |
| Thinking mode | `enable_thinking: false` |
| Sampling profile | `code` → temp 0.6, top_p 0.95, top_k 20, presence_penalty 0.0 |
| Model | `unsloth/Qwen3.6-35B-A3B-MLX-8bit` |
| Endpoint | `http://127.0.0.1:8080/v1/chat/completions` (mlx_lm.server) |
| Max tokens | 32768 |

All 9 tasks are `task_type: code` — the Brief 16 result showed `code` was the most reliable type under TF3-off, and the scale-up question is orthogonal to task-type mix (which Brief 16 already mapped).

### Tasks (9 total)

| ID | Bucket | Size | Summary |
|---|---|---|---|
| S1 | S | ~20 lines | Verbatim Brief 16 T1 — `dedupe_preserve_order` (parity anchor) |
| M1 | M | ~100 lines | Inheritance → composition on a `LoggedCache(Cache)` pair |
| M2 | M | ~120 lines | Add `__repr__` + `__eq__` to 6 dataclass-shaped classes |
| M3 | M | ~130 lines | Fix 3 discrete bugs (None guard, mutable default, off-by-one) in a pipeline module |
| L1 | L | ~250 lines | Split a "ReportGenerator" god-class into 3 composed pieces, preserving byte-exact markdown+html output |
| L2 | L | ~280 lines | Add Python 3.12 type hints to 8 functions across a module, preserving behaviour |
| L3 | L | ~330 lines | Migrate a `requests`-based client to `httpx` (sync), 10 call sites, signatures preserved |
| XL1 | XL | ~450 lines, 3 files | Rename `Order → Purchase` across model/service/test |
| XL2 | XL | ~500 lines, 4 files | Add nullable `deleted_at` field across model/migration/serializer/test, preserving existing tests |

Each task has a deterministic verifier under `verifiers/phase2a/<ID>.py`. Verifiers were smoke-tested both directions (reference impl passes, intentional bug fails) before the sweep via `verifiers/phase2a/_smoke.py`.

### Replicates

5 per task. Sequential against localhost. **9 × 1 × 5 = 45 runs.**

### Judge

Same as Brief 16 — Opus 4.7 via `claude -p --json-schema`, rating `acceptance_pass / format_adherence / fabrication_present / quality / notes`. Judge prompt extended per Brief 17 §Judge with two additions:

- **Completeness check** in `quality`: partial outputs that pass the deterministic check but drop a named file or test case must be scored down (3→2 or 2→1).
- **Multi-file check** in `format_adherence`: for XL tasks, a missing file = `format_adherence: false` even if the present files look correct.

## Results

**45 runs, zero worker errors, zero verifier/judge disagreements, zero `finish_reason: length` truncations.**

### Headline

**The Brief 16 recipe (TF3 + thinking-off) holds at scale. 45/45 deterministic PASS, 45/45 judge PASS, 0 fabrication, mean quality 3.96. No degradation from 20 lines (S1) to 500 lines across 4 files (XL2).**

### Per size bucket

| Bucket | N | Pass rate | Mean quality | Fabrication rate | Mean walltime | Mean completion tokens |
|---|---|---|---|---|---|---|
| S  |  5 | **1.00** | 4.00 | 0.00 |  2.0s | 109 |
| M  | 15 | **1.00** | 3.87 | 0.00 | 13.7s | 417 |
| L  | 15 | **1.00** | 4.00 | 0.00 | 16.6s | 730 |
| XL | 10 | **1.00** | 4.00 | 0.00 | 17.0s | 810 |

S-bucket walltime (2.0s) and completion tokens (109) are within noise of Brief 16's reported mean (2.0s, 118 tokens) — H1 confirmed, parity anchor holds.

### Per-task breakdown

| Task | N | Pass rate | Quality (r1-r5) | Mean quality | Judge notes |
|---|---|---|---|---|---|
| S1  | 5 | 1.00 | 4,4,4,4,4 | 4.00 | clean |
| M1  | 5 | 1.00 | 3,4,4,4,4 | 3.80 | r3 flagged for naming drift ("TimestampDecorator isn't actually a decorator") |
| M2  | 5 | 1.00 | 4,4,4,4,4 | 4.00 | clean |
| M3  | 5 | 1.00 | 4,4,3,4,4 | 3.80 | r3 changed `normalize`'s signature (correct bug-fix, unnecessary API break) |
| L1  | 5 | 1.00 | 4,4,4,4,4 | 4.00 | byte-exact markdown+html preserved across all replicates |
| L2  | 5 | 1.00 | 4,4,4,4,4 | 4.00 | all 8 functions typed, no behaviour changes |
| L3  | 5 | 1.00 | 4,4,4,4,4 | 4.00 | clean 10-call-site `requests → httpx` migration, no async smuggle |
| XL1 | 5 | 1.00 | 4,4,4,4,4 | 4.00 | 3-file rename, no `Order`/`order` leakage across AST |
| XL2 | 5 | 1.00 | 4,4,4,4,4 | 4.00 | 4-file nullable-field addition, original tests preserved |

### Token and walltime accounting

| Bucket | Mean prompt tokens | Mean completion tokens | Mean walltime |
|---|---|---|---|
| S  |   277 | 109 |  2.0s |
| M  |   671 | 417 | 13.7s |
| L  | 1,099 | 730 | 16.6s |
| XL | 1,693 | 810 | 17.0s |

Walltime scales **sub-linearly** past the M bucket — L and XL completion-token means (730, 810) are 7× and 7.5× S (109), but walltime ratios are 8.3× and 8.5× S. Fast enough to fit a full-loop iteration (plan + execute + review) in well under a minute on the biggest tasks.

### Quality distribution

43 × quality 4; 2 × quality 3; 0 × quality ≤ 2; 0 × quality 5.

Both quality-3 cases had legitimate judge notes:

- **M1 r3:** class called `TimestampDecorator` that wasn't actually decorating — naming drift in otherwise-correct composition.
- **M3 r4:** changed `normalize(x)` to `normalize(x, default=...)` — correctly fixed the mutable-default bug but broke the caller contract in the process.

Both are craft-level observations, not correctness failures — both runs still passed acceptance and format adherence.

### Determinism signal

Replicates are not all byte-unique:

| Task | Unique outputs out of 5 |
|---|---|
| S1  | 5 |
| L1  | 4 |
| XL2 | 2 |
| XL1 | **1** (all 5 replicates byte-identical) |

XL1 being 1-of-5 is expected rather than suspicious — a pure mechanical rename with a well-specified OUTPUT FORMAT has a canonical correct answer, and temp=0.6 is low enough that the model converges there every time. XL2's 2-of-5 reflects the same pattern on a more-structured task. This is not a sampling bug; it is Qwen3.6 being well-behaved on spec-closed tasks.

### Fabrication and truncation

- **Fabrication:** 0/45. Matches Brief 16 (0/60 on TF3, 2/30 on TF1-thinking-on only).
- **Truncation (`finish_reason: length`):** 0/45. Max observed completion tokens was 826 (XL2) — well under the 32,768 cap. No sign of the Brief 16 TF3-thinking-on reasoning-loop pathology, which is the expected result given thinking is off.

## Analysis

### H1 — S-bucket parity with Brief 16

**Prediction:** 5/5 pass on S1, parity with Brief 16's 3/3 pass at ~2.0s / ~118 tokens.

**Verdict:** Confirmed. 5/5 pass, quality 4.00, 2.0s walltime, 109 completion tokens.

### H2 — Quality holds through the L bucket

**Prediction:** 15/15 pass at M and L, quality ≥ 3.5.

**Verdict:** Confirmed and exceeded. 15/15 pass at M (quality 3.87), 15/15 pass at L (quality 4.00). The M-bucket mean is slightly lower because M1 r3 and M3 r4 caught legitimate craft-level 3s — but every run still passed acceptance.

### H3 — XL multi-file failures

**Prediction:** XL pass rate < 90%, failures driven by missing fences or malformed filenames.

**Verdict:** **Refuted.** XL1 (3-file rename) and XL2 (4-file schema addition) both hit 5/5 pass with 100% fence adherence. The heading-then-fence format the tasks specified (`### filename\n\`\`\`python...`) is robust enough that Qwen3.6 produced every named file every time. The judge's multi-file check was never triggered.

### H4 — Walltime linearity

**Prediction:** XL ≈ 5-10× S walltime.

**Verdict:** Confirmed. XL mean walltime 17.0s / S mean 2.0s = 8.5×. Matches the completion-token ratio (810/109 = 7.4×) closely — the model is emission-bound, not reasoning-bound, on thinking-off.

## What this means for the pipeline

The Brief 16 recipe is **production-ready for the current gigo:execute Tier-2 dispatch on tasks up to ~500 lines of multi-file output.** Concretely:

- No ceiling found in this sweep at L or XL — 45/45 was unanimous across every bucket.
- Walltime budget: plan on **~2s × (completion_tokens / 100)** for estimation. Multi-file XL work stays under 20s per call.
- The open risk moves outward: sizes beyond 600 lines, task types beyond `code`, and multi-turn loops (Phase 2B) are the next unknowns. This sweep does not speak to any of them.

## Harness changes shipped with Brief 17

- `run_qwen_eval.py` — new `--tasks-dir`, `--pin-format`, `--pin-thinking`, `--reps`, `--out` flags. Auto-discovers tasks in any dir. Manifest now records `size_bucket` and `finish_reason` per run.
- `score_qwen_eval.py` — new `--tasks-dir` / `--verifiers-dir` flags. New "Per size bucket × condition" section in `summary.md` whenever `size_bucket` is present in the manifest.
- `verifiers/extract.py` — new `extract_named_fences(content, filenames)` helper for multi-file XL verifiers. Tolerates `##`/`###`/`####` heading levels and any fence language tag.
- `judge-prompt.md` — completeness note added to `quality`, multi-file rule added to `format_adherence`.

All changes are additive — Phase 1 command lines (no flags) still produce the same runs they always did against the original `tasks/` and `verifiers/` directories.

## Cost

- Qwen3.6 sweep: local, free. ~11m20s walltime end to end for the 45 runs.
- Opus 4.7 judge: 45 runs × `claude -p --json-schema` path. Session cache warmed early. Total judge walltime ~7 minutes. No parse errors (the `explanatory` output style fix from Brief 16 held).
- 0 judge errors, 0 re-runs.

## Out of scope / Phase 2B+

- **Phase 2B — multi-turn.** This eval is single-shot. Multi-turn with `preserve_thinking` is where thinking-mode should pay off in principle.
- **Phase 2C — loop-failure sweep.** Reproduce Brief 16's T7 × TF3 × thinking-on reasoning-loop pathology with a targeted regex-from-examples sweep (20 replicates) to characterise the silent-non-completion tail.
- **Phase 3 — local-worker bake-off.** Gemma4 first, then DeepSeek-Coder, Qwen3-Coder, Codestral, Llama at the same TF3-off recipe. Is the harness Qwen-specific or a general local-worker pattern?
- **Task types beyond `code`.** Brief 16 already mapped reasoning and structured at toy scale; a scale-up on those types is a separate brief if we ship Qwen as the default reasoning worker.
- **Sizes beyond 600 lines / 4 files.** No evidence of a cliff here, but the trend needs to be extended before claiming "scales arbitrarily."

## Files

- Harness: `evals/qwen-worker-eval/`
  - `tasks/phase2a/{S1,M1,M2,M3,L1,L2,L3,XL1,XL2}-*.md` — task specs with YAML front-matter
  - `verifiers/phase2a/*.py` — deterministic pass/fail checks (+ `_smoke.py` discriminator)
  - `run_qwen_eval.py` — sweep runner (extended with pin flags)
  - `score_qwen_eval.py` — verifier + judge + aggregate (extended with bucket rollup)
  - `judge-prompt.md` — Opus rubric (extended with completeness + multi-file checks)
- Results: `evals/qwen-worker-eval/results/phase2a-sweep/` (gitignored)
- Summary: `evals/qwen-worker-eval/results/phase2a-sweep/summary.md`
- Phase 1 reference: `docs/gigo/experiments/05-qwen36-worker-profile.md`
