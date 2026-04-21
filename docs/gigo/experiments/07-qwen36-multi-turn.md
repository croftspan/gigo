# Experiment 07 — Qwen3.6 Phase 2B Multi-Turn (Brief 18)

**Status:** Complete.
**Date started:** 2026-04-19
**Date finished:** 2026-04-19
**Model under test:** `unsloth/Qwen3.6-35B-A3B-MLX-8bit` (local MLX build, MoE 35B / ~3B active).
**Judge model:** `claude-opus-4-7`.
**Orchestrator / planner:** Not under test.
**Runs:** `evals/qwen-worker-eval/results/phase2b-toff/` and `evals/qwen-worker-eval/results/phase2b-ton/`.
**Relationship to Brief 17:** reuses the Phase 2A M/L/XL task bed (6 of 9 tasks) as turn-1 ground truth and adds a turn-2 critique on top. Does **not** re-run Brief 17 baseline — the Phase 2A sweep is the reference.

## The question

Brief 16 shipped the recipe **TF3 + `enable_thinking: false`** (thinking-off). Brief 17 confirmed it held at realistic scale (45/45 pass on 20-500-line tasks, 4 files max).

But Brief 16 also identified a suspicious outlier: TF3 × thinking-on × task T7 produced one silent non-completion — a reasoning loop where the model thought forever and never emitted code. That single data point was dismissed as a scheduling edge in single-shot mode. In multi-turn, the same loop should matter more, because every turn builds on the last.

Qwen3's chat template exposes a second flag, `preserve_thinking`, that controls whether turn-1 `<think>` content is rendered back into turn-2's context. If it's on, the model reads its own prior reasoning on turn 2. If it's off, turn-2 starts from scratch even though turn 1 thought hard.

The question Phase 2B asks:

> In a 2-turn revision loop where a worker ships a solution and is then given a critique, does turning thinking on (with `preserve_thinking: true`) pay for itself in quality — or does it replay the T7 pathology as a walltime and fabrication tail?

If thinking-on + preserve-on wins on real-defect critiques without a loop tail, multi-turn becomes the case for reasoning mode. If it loses or loops, the single-shot recipe from Brief 16/17 carries over unchanged into the revision pipeline.

### Hypotheses going in

| # | Hypothesis | Prediction |
|---|---|---|
| H1 | Thinking-off holds through multi-turn on Brief 17 tasks | ≥ 90% pass on T-off (parity gate) |
| H2 | Thinking-on + preserve-on lifts quality on *real-defect* critiques (M1, M3) | Quality Δ ≥ +0.3 over T-off on the real-defect subset |
| H3 | Thinking-on + preserve-**off** reproduces the T7 loop — silent non-completion or length truncation | ≥ 1 `finish_reason: length` OR walltime > 3× preserve-on mean |
| H4 | `preserve_thinking` is a real, measurable mechanism (not a no-op flag) | Walltime, token, or quality difference between preserve-on and preserve-off beyond noise |

## Design

**Three pinned cells on TF3:**

| Cell | Ticket format | Thinking | preserve_thinking | Sampling profile |
|---|---|---|---|---|
| **T-off** | TF3 | `enable_thinking: false` | n/a (no thinking to preserve) | code: 0.6 / 0.95 / 20 / 0.0 |
| **T-on preserve-on** | TF3 | `enable_thinking: true` | `preserve_thinking: true` | code: 0.6 / 0.95 / 20 / 0.0 |
| **T-on preserve-off** | TF3 | `enable_thinking: true` | `preserve_thinking: false` | code: 0.6 / 0.95 / 20 / 0.0 |

The preserve flag is only meaningful with thinking on — when thinking is off there is no reasoning payload to carry, so preserve collapses to a single condition (`na`). The sweep is **6 tasks × 3 conditions × 5 reps = 90 runs**.

### Tasks (6 total — subset of Brief 17's 9)

All 6 are `task_type: code`. Each reuses its Phase 2A spec as the turn-1 ticket (via `reference_task: phase2a/<stem>` in the YAML front matter) and adds a `revision_critique` field for turn 2.

| ID | Size | Phase 2A task | Critique kind | What the critique asks for |
|---|---|---|---|---|
| M1 | M | Inheritance → composition | **real-defect** | Rename `TimestampDecorator` — it's not a decorator (anchored to M1 r3 judge note from Brief 17) |
| M3 | M | Pipeline bug-fix (off-by-one + mutable default + None guard) | **real-defect** | Fix the mutable-default bug **without** changing `normalize`'s signature (anchored to M3 r4) |
| L1 | L | ReportGenerator god-class split | synthetic-craft | Lift stateless `_format_*` helpers out of the class to module-level |
| L3 | L | requests → httpx port | synthetic-craft | Remove the now-unused `import json` |
| XL1 | XL | Domain rename (Order → Purchase, 3 files) | synthetic-craft | Rename test fixture ID literals `"o1"/"o2"` → `"p1"/"p2"` to match |
| XL2 | XL | Nullable `deleted_at` field add (4 files) | synthetic-craft | Replace `down()` body with column-specific `ALTER TABLE ... DROP COLUMN`, not `DROP TABLE users;` |

**Real-defect vs synthetic-craft** is a deliberate split:

- **Real-defect (M1, M3):** the critique points at a behaviour the Phase 2A judge actually caught on a replicate. If thinking-on helps anywhere, it should help here — the model needs to *think* about a subtle invariant (signature preservation, naming fit), not just execute.
- **Synthetic-craft (L1, L3, XL1, XL2):** the critique is a coherent craft ask we authored, never observed in Phase 2A. These test revision-following on well-specified, mostly-mechanical changes where thinking should be overkill.

Each task has a 2-stage deterministic verifier under `verifiers/phase2b/<ID>.py`:

1. **Stage 1** — re-run Phase 2A's acceptance check on the turn-2 output. The revision must not break the original spec.
2. **Stage 2** — check the critique was addressed. E.g. XL2's stage 2 walks `migration.py`'s `down()` AST, collects every string literal, and asserts all three of `ALTER TABLE`, `DROP COLUMN`, and `deleted_at` appear.

Verifiers were smoke-tested both directions (18 cases = 6 tasks × 3 smoke vectors) before the sweep via `verifiers/phase2b/_smoke.py`. Gate passed cleanly.

### Gate

**Parity gate before thinking-on.** Before spending the ~4-hour wall budget on the 60 thinking-on runs, the T-off 30-run cell had to hit ≥ 90% deterministic pass. It hit **100%** (30/30), so the thinking-on cells were cleared to execute.

### Judge

New prompt, new schema. `judge-prompt-revision.md` is turn-2-only — it receives the task spec, acceptance criteria, output format, critique, verifier result, and the turn-2 artefact, and returns:

```
acceptance_pass, critique_addressed, format_adherence,
fabrication_present, quality (1-5), notes
```

The `critique_addressed` field is the new signal — a yes/no on whether the revision did what the critique asked. The judge is told the verifier's stage-2 result is its strongest signal and to override it only when a worker addresses the critique in a way a regex/AST check happened to miss. (That never happened in this sweep.)

Turn-1 output is **not** judged. This experiment measures the turn-2 artefact only; the turn-1 pass rate is implicit in the stage-1 verifier gate.

## Results

**90 runs, zero worker errors, zero verifier/judge disagreements, zero `finish_reason: length` truncations across all three cells.**

### Headline

**Thinking-on passes — and quality is statistically tied with thinking-off. But it costs ~6.5× walltime and ~7.5× completion tokens (both turns summed) to deliver that tie.**

```
                 pass   Q    t1+t2 walltime   t1 comp    t2 comp   total comp
T-off            30/30  4.43         28.9s       638        635        1,273
T-on preserve-on 30/30  4.50        189.4s     6,934      2,638        9,572
T-on preserve-off 30/30 4.47        267.0s     7,565      2,966       10,530
```

Quality delta between the best (preserve-on, 4.50) and worst (T-off, 4.43) cell is 0.07 on a 1-5 scale. That's well inside judge noise. **`enable_thinking: false` remains the production recipe** for the worker role under gigo:execute.

### Per cell, all tasks

| Cell | N | Pass rate | Critique-addressed | Mean quality | Fab rate | Mean t1+t2 walltime | Mean total completion tokens (t1+t2) |
|---|---|---|---|---|---|---|---|
| T-off | 30 | **1.00** | 1.00 | 4.43 |  0.00 |  28.9s |  1,273 |
| T-on preserve-on | 30 | **1.00** | 1.00 | 4.50 |  0.00 | 189.4s |  9,572 |
| T-on preserve-off | 30 | **1.00** | 1.00 | 4.47 |  0.00 | 267.0s | 10,530 |

### Per cell × critique type

The real-defect vs synthetic-craft split is where H2 would have shown up if thinking-on helped:

| Cell | Real-defect (M1, M3) N=10 | Synthetic-craft (L1, L3, XL1, XL2) N=20 |
|---|---|---|
| T-off |  Q 4.10 |  Q 4.60 |
| T-on preserve-on |  Q 4.20 |  Q 4.65 |
| T-on preserve-off |  Q 4.30 |  Q 4.55 |

**Real-defect delta: +0.10 (preserve-on) and +0.20 (preserve-off) over T-off.** Predicted ≥ +0.30, observed ≤ +0.20. H2 is *refuted as a practical lift* — the movement is within-noise on a 5-point scale and does not justify the walltime cost.

Notably the real-defect quality floor is lower than synthetic-craft across all cells (4.10-4.30 vs 4.55-4.65). The M1 "naming drift" critique asks for taste-level judgment (pick a better name) and the M3 "preserve signature" critique asks for a specific diff shape — both produced the 3s and 4s in this sweep. No cell stands out as "good at real-defect work."

### Per size bucket × cell

| Bucket | T-off | T-on preserve-on | T-on preserve-off |
|---|---|---|---|
| M (M1, M3) | Q 4.1 | Q 4.2 | Q 4.3 |
| L (L1, L3) | Q 4.3 | Q 4.6 | Q 4.6 |
| XL (XL1, XL2) | Q 4.9 | Q 4.7 | Q 4.5 |

No monotonic degradation with size. XL T-off posting quality 4.9 is the single highest cell in the sweep — the worker is strictly emission-bound, not reasoning-bound, on XL tasks under thinking-off.

### Walltime and token accounting

| Cell | Mean prompt tokens (t2) | Mean t1 completion | Mean t2 completion | Mean reasoning chars (t2) | T1 walltime | T2 walltime | T2 walltime MAX |
|---|---|---|---|---|---|---|---|
| T-off            | 2,042 |   638 |   635 |     0 |  14s |  14.8s |     — |
| T-on preserve-on | 2,024 | 6,934 | 2,638 | 7,910 | 143s |  46.5s | 207s |
| T-on preserve-off| 2,024 | 7,565 | 2,966 | 9,121 | 154s | 113.0s | **831s** |

Reasoning character counts are the length of `<think>` payload returned by the server's `reasoning` field; the MLX server reports `reasoning_tokens=0` in usage metrics so we measure it by rendered characters. Turn-1 completion counts include the full `<think>` payload for thinking-on cells, which is why they are ~10× larger than turn-1 T-off.

### The oscillation tail (preserve-off only)

Three preserve-off runs had turn-2 walltime > 300s, vs zero in preserve-on:

| Run | T1 walltime | T2 walltime | T2 / T1 reasoning ratio | Observed pattern |
|---|---|---|---|---|
| M1 r2 | 131s | **831s** | 3.35× | 26 code-fence emits, 52 "I will output" phrases, 27 "Wait", 27 "Actually" in a single turn — full T7 loop |
| M3 r3 | 370s | **663s** | 0.20× | Turn-1 already oscillated (71 "Wait" / 23 code blocks); turn-2 recovered to a compact output but still ran the full budget |
| L1 r3 | 148s | **694s** | 0.98× | Milder: 12 code-fence emits, 1 "Wait" — steady but repetitive sampling of the formatter helpers |

The preserve-on worst case (M1 r2, 207s) is under half the preserve-off worst case. All 3 preserve-off outliers completed correctly — none hit `finish_reason: length`. H3's *truncation* prediction is refuted. H3's *walltime-tail* prediction is confirmed: preserve-off's max/mean ratio is **7.36×** versus preserve-on's **4.45×**.

**Interpretation.** When turn-2 receives the user critique without turn-1's thinking attached (preserve-off), the model re-derives its entire reasoning chain from scratch before editing — and occasionally sinks into a loop of "I will output the code / wait, let me check / *re-emits same code block*." When turn-1 thinking is preserved (preserve-on), the model reads its prior chain and jumps straight to the edit. Preserve-on is not just faster; it's what keeps the T7 pathology from resurfacing.

### Fabrication and regression

- **Fabrication:** 0/90. The regression we feared from Brief 16 (TF3-thinking-on on T9 wrote 2 fabrications) did not recur here — possibly because the turn-2 prompt is anchored on a pre-existing artefact rather than an open-ended ticket.
- **Spec regressions:** 0/90. Every turn-2 revision held the original Phase 2A acceptance check (stage 1 of the 2-stage verifier).
- **Critique-missed:** 0/90. Every revision addressed the specific critique (stage 2). No cell differs here.

### Determinism

Replicates are not byte-unique within cells. Per-task pass rate is 1.00 across all (task, cell) pairs — the variance is on quality, not correctness. The worker is strongly consistent on these 6 tasks at temp 0.6.

## Analysis

### H1 — Thinking-off parity gate

**Prediction:** ≥ 90% pass on T-off.

**Verdict:** **Confirmed.** 30/30 = 100%. T-off is stable in multi-turn — the recipe Brief 16 / Brief 17 found for single-shot carries over to revision flows without adjustment. This is the finding that matters most for production.

### H2 — Thinking-on lifts real-defect quality

**Prediction:** Quality Δ ≥ +0.3 on the real-defect subset (M1, M3) for T-on preserve-on vs T-off.

**Verdict:** **Refuted.** Observed Δ = +0.10. The real-defect tasks require taste (naming fit) and signature discipline — both of which thinking might plausibly help — but neither shows a meaningful lift. The model is either thinking in ways that do not route into craft improvement, or the judge cannot distinguish "thought harder" from "wrote good code" at this task difficulty.

### H3 — Thinking-on preserve-off replays T7

**Prediction:** At least one `finish_reason: length` truncation OR walltime > 3× preserve-on.

**Verdict:** **Partially confirmed.** Zero length truncations (refuted) — but three outliers with walltime > 300s, one at 831s (mean 267s), max/mean 7.36× vs preserve-on's 4.45×. Preserve-off reproduces the T7 oscillation in ~10% of runs (3/30), none of which hit the length cap because the 32,768-token budget is generous. In a lower-budget setting or under longer tasks, this is exactly the silent non-completion Brief 16 flagged.

### H4 — `preserve_thinking` is real

**Prediction:** Measurable difference between preserve-on and preserve-off beyond noise.

**Verdict:** **Confirmed.** Mean turn-2 walltime differs by 66.5s (113 vs 46.5, a **2.4× ratio**); mean reasoning-char length differs by 1,211. Preserve-off consistently reasons longer on turn 2, and 3× preserve-off runs drift into the T7 loop that preserve-on eliminates. The flag has observable, costly effects.

## What this means for the pipeline

**gigo:execute Tier-2 dispatch stays on `enable_thinking: false`.** The Phase 2B data provides zero evidence that thinking-on pays for itself in a revision loop:

- Quality ties within 0.07 on a 5-point scale.
- Walltime cost (both turns summed) is 6.5× for equal output.
- Completion-token cost (both turns summed) is **7.5×** — t1 alone is 11× (6,934 vs 638), because thinking-on's turn-1 reasoning payload is much larger than its turn-2 revision.
- preserve-off reintroduces a walltime tail that would degrade pipeline latency under budget pressure.

**If a future task class demands thinking** — e.g. a planner dispatch, or a task type we have not yet evaluated — the correct default is **preserve-on.** The preserve-off tail is the T7 pathology, measurable at 10% of runs under realistic critiques.

Concretely, for the worker role:

- No harness change required. `enable_thinking: false` continues to work.
- The revision loop can be wired directly to the existing single-shot dispatch — no conditional "thinking-on for turn 2 because the model should reason harder about feedback" logic needed. The data says that logic would be wrong.

## Harness changes shipped with Brief 18

Additive, non-breaking. Phase 2A and Brief 16 command lines still work unchanged.

- `build_critique.py` — single-template turn-2 user-message renderer. Pure function of the task file's `revision_critique` and `output_format` (the latter inherited from the referenced Phase 2A task via `reference_task:`).
- `run_qwen_eval.py` — new `--mode {single-turn|multi-turn}`, `--preserves`, and `--pin-preserve` flags. When `thinking=off`, the preserve axis collapses to `preserve=na`. Turn-1 and turn-2 request bodies are split via a new `call_qwen_turn2(...)` that threads `reasoning` into the assistant message only when thinking was on.
- `score_qwen_eval.py` — extended to detect `mode=multi-turn` in the manifest, route to `judge-prompt-revision.md`, pull nested `turn1/turn2` walltime and token fields into rollups, and emit a new "Revision outcomes (multi-turn only)" section in `summary.md` grouped by `(condition, critique_type)`. The combined pass gate becomes `acceptance ∧ critique_addressed ∧ format ∧ ¬fab`.
- `judge-prompt-revision.md` — new turn-2 rubric. Six required fields including `critique_addressed`; explicit regression penalty when a revision breaks previously-passing parts of the spec; explicit rule that verifier stage-2 is the strongest signal for `critique_addressed`.
- `verifiers/phase2b/{M1,M3,L1,L3,XL1,XL2}.py` + `_smoke.py` — 2-stage verifiers that subprocess the Phase 2A verifier for stage 1, then run AST or regex checks for stage 2. Discriminator smoke-test drives each case both directions (output satisfies critique ↔ output does not) before the sweep.
- `tasks/phase2b/*.md` — 6 task files with YAML front-matter fields `reference_task`, `critique_type`, `revision_critique`, `verifier`. No new task bodies — each inherits its spec from Phase 2A.

## Cost

- Qwen3.6 sweep:
  - T-off cell: 30 runs, **~15 min** walltime end-to-end on localhost.
  - T-on cells: 60 runs, **~3h 49m** walltime on localhost. Thinking dominates the budget.
- Opus 4.7 judge:
  - 30-run T-off judge pass: ~5 min.
  - 60-run T-on judge pass: ~10 min.
  - 0 judge errors, 0 re-runs, 0 verifier/judge disagreements.
- Total Anthropic API cost was dominated by turn-2 artefact review — comparable to the Brief 17 judge pass, since the turn-1 output is never judged in Phase 2B.

## Out of scope / follow-ups

- **Task types beyond `code`.** `reasoning` and `structured` turn-2 critiques are a separate brief. If Qwen becomes the default reasoning worker, Phase 2B's protocol is directly reusable — pair a Phase 2A reasoning/structured task with a critique and a stage-2 verifier.
- **Longer conversations (3+ turns).** Preserve-on's gap over preserve-off likely widens as turn count grows — each turn adds another reasoning payload to preserve or discard. Not tested here.
- **Budget-bounded thinking.** With `max_tokens` dropped from 32,768 to (say) 8,192, the preserve-off oscillations should start hitting the cap and registering as `finish_reason: length`. That is the regime where H3's truncation prediction would have confirmed. Not tested.
- **Larger or heterogenous tasks.** The 6 tasks here are all `code`. Mixing M-bucket reasoning in with M-bucket code in a single sweep would isolate task-type from task-size effects in multi-turn.
- **The `preserve_thinking` mechanism across vendors.** Qwen3 exposes it natively; DeepSeek-V3 and Kimi K1 expose similar flags but under different names. A cross-vendor replication would confirm the mechanism rather than the specific Qwen template.

## Open question closed

**Open Question #14 (Brief 16 → Brief 17 → Brief 18):** "Does thinking-on pay for itself in multi-turn with `preserve_thinking`?"

**Resolved, 2026-04-19:** **No.** Quality ties with thinking-off; walltime and token cost are 6.5× and 4.15×; the preserve-off variant reproduces the T7 oscillation in 10% of runs. `enable_thinking: false` remains the production recipe for the worker role. `preserve_thinking: true` is the correct *secondary* default only if thinking-on is later required for a non-worker dispatch.

## Files

- Harness: `evals/qwen-worker-eval/`
  - `tasks/phase2b/*.md` — 6 revision task specs with `reference_task:` inheritance
  - `verifiers/phase2b/*.py` + `_smoke.py` — 2-stage verifiers
  - `build_critique.py` — turn-2 message renderer
  - `run_qwen_eval.py` — sweep runner (extended with multi-turn mode and preserve axis)
  - `score_qwen_eval.py` — verifier + judge + aggregate (extended for multi-turn rollup)
  - `judge-prompt-revision.md` — turn-2 Opus rubric
- Results: `evals/qwen-worker-eval/results/phase2b-toff/` and `evals/qwen-worker-eval/results/phase2b-ton/` (gitignored)
- Summaries: `results/phase2b-toff/summary.md`, `results/phase2b-ton/summary.md`
- Reference: `docs/gigo/experiments/05-qwen36-worker-profile.md`, `docs/gigo/experiments/06-qwen36-scale-trial.md`
