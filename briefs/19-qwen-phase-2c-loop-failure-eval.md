# Kickoff: Qwen3.6 Phase 2C — Loop-Failure Characterisation (Brief 19)

**Date:** 2026-04-19
**Previous work:**
- Brief 16 (Phase 1) — T7 × TF3 × thinking-on = 2/30 silent non-completions. Reasoning oscillated between equivalent regex forms until max_tokens, then emitted empty content. `docs/gigo/experiments/05-qwen36-worker-profile.md`.
- Brief 17 (Phase 2A) — TF3 + thinking-off recipe stable to 500-line / 4-file tasks. `docs/gigo/experiments/06-qwen36-scale-trial.md`.
- Brief 18 (Phase 2B) — 2-turn revision: thinking-on ties thinking-off on quality at 6.5× walltime / 7.5× tokens. preserve-off reproduced T7-*like* oscillation in 3/30 runs (max 831s), but none of Brief 18's code tasks actually matched T7's spec so the T7 pathology itself was never directly re-run. `docs/gigo/experiments/07-qwen36-multi-turn.md`.

**This brief:** reproduce the original T7 pathology under controlled conditions, measure its base rate, test whether it's **task-specific** (regex-from-examples only) or **axis-specific** (TF3 + thinking-on generally), and confirm the loop is what we think it is by varying `max_tokens` to turn silent non-completion into visible `finish_reason: length`.

---

## Why this brief

Brief 16's T7 anomaly is the single largest unknown in the Qwen worker profile. We have a production recipe (TF3 + thinking-off) that sidesteps the failure mode entirely, so nothing is blocked — but three decisions downstream depend on knowing what actually triggers the loop:

1. **When is thinking-on ever safe?** Brief 18 said "not in the worker role, period." But a future planner or reviewer dispatch might want it. The answer depends on whether T7 is a task-type trap or a broader regime.
2. **Does the loop ever happen silently in production?** `finish_reason: length` is logged. Silent-non-completion-under-budget (32k reasoning, 0 content, returned as stop) is not. If the pathology is task-general and only hidden by the generous MLX default max_tokens, we need an observable circuit-breaker.
3. **Is Brief 18's preserve-off oscillation the same loop or a different one?** Phenomenologically similar (repetitive code-fence re-emits, long walltime). If they share a mechanism, the fix is the same. If they're distinct, we have two failure modes to guard against.

Working hypotheses:

- **H1 — T7 base rate reproduces.** T7 × TF3 × thinking-on × max_tokens=32,768 at N=30 produces silent non-completion in 5-15% of runs. Brief 16's 2/30 (6.7%) was real, not noise.
- **H2 — Trigger is task-specific to regex-from-examples.** A shape-similar regex task (T7-variant) reproduces at a comparable rate; a non-regex control (T1) does not. If all three cells show similar rates, reject H2 → trigger is TF3+thinking-on general.
- **H3 — Tight budgets surface the loop.** At max_tokens=8,192, oscillation hits the cap on turn 1 and registers as `finish_reason: length` with 0-token content. Pass rate collapses, non-completion count jumps by ≥ 3×.
- **H4 — Brief 18's preserve-off oscillation is mechanistically the same loop.** Collect `<think>` payload from both failure modes; compare repetition signatures (code-fence re-emit count, phrase-level cycles). If they match, we have one pathology, not two.

We want a specific answer: **is the T7 loop a regex-from-examples-specific trap (bounded blast radius, can be blacklisted), or is it the visible tip of a thinking-on-general iceberg (requires a timeout / token-budget guard on any thinking-on dispatch)?**

---

## Context you need (read in this order)

1. `docs/gigo/experiments/05-qwen36-worker-profile.md` — §T7 anomaly detail. The original spec, sample reasoning trace, 9-min walltime observation.
2. `docs/gigo/experiments/07-qwen36-multi-turn.md` — §The oscillation tail (preserve-off only). Character-count and phrase-frequency signatures of the Brief 18 loop.
3. `/Users/eaven/.claude/projects/-Users-eaven-projects-gigo/memory/feedback_qwen36_worker_profile.md` — recipe summary.
4. `evals/qwen-worker-eval/` — harness from Briefs 16/17/18. **You are extending it with a `--max-tokens` axis and a classifier verifier, not rebuilding.**
5. `evals/qwen-worker-eval/tasks/T7-regex-from-examples.md` + `verifiers/T7.py` — the original fixture. Do NOT modify.

---

## Endpoint + pre-flight

**Liveness check** (standard):

```bash
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"unsloth/Qwen3.6-35B-A3B-MLX-8bit","messages":[{"role":"user","content":"respond with just: OK"}]}' \
  | jq '.choices[0].message.content'
```

**One new probe:** confirm `max_tokens` parameter is honoured at low values. Send a request with `max_tokens: 64` and a prompt that would want ~500 tokens to answer properly. Confirm response has `finish_reason: "length"` and ~64 completion tokens. If the MLX server silently ignores low `max_tokens` values, the budget-sensitivity axis (H3) is unreachable — flag and stop.

---

## Design

**No Opus judge in this brief.** Phase 2C is a pure mechanism sweep — outcomes are discrete (complete-pass, complete-fail, silent-non-completion, visible-truncation) and the verifier is deterministic. Saves judge cost and removes judge noise from the signal.

**Axes:**

| Axis | Levels | Rationale |
|---|---|---|
| Task | T7 (original), T7v (regex variant, new), T1 (non-regex control, existing) | H2 — trigger specificity |
| max_tokens | 32,768 (Brief 16 baseline), 8,192 (loop-surfacing) | H3 — budget sensitivity |
| Thinking | `enable_thinking: true` — pinned | The anomaly only appears with thinking-on |
| Ticket format | TF3 — pinned | Brief 16's trigger condition |
| Sampling | code: temp 0.6 / top_p 0.95 / top_k 20 / pp 0.0 — pinned | Brief 16 profile |
| Mode | single-shot — pinned | T7 is a single-shot pathology |
| Replicates | 30 per cell | Brief 16 saw 2/30; 30 is the minimum to confirm the 6.7% rate |

**Total: 3 tasks × 2 max_tokens × 30 reps = 180 runs.**

**Walltime budget.** Thinking-on at max_tokens=32,768 averages 140-150s in Brief 18 (and worst case 900s when oscillating). Thinking-on at max_tokens=8,192 should cap oscillations faster. Estimate 5-8h end-to-end; reserve an overnight slot.

### Tasks

**T7 (original, existing).** Ships unchanged from `tasks/T7-regex-from-examples.md`. Verifier `verifiers/T7.py` unchanged.

**T7v (regex variant, new).** Shape-similar: regex-from-examples, same `re.fullmatch` semantics, different content. E.g. 4 lowercase letters + 3 digits, comparable positive/negative set. Craft the spec so a competent human writes the regex in <60s. Add as `tasks/T7v-regex-variant.md` + `verifiers/T7v.py`. Smoke-test both directions.

**T1 (non-regex control, existing).** Ships unchanged from `tasks/T1-dedupe-preserve-order.md`. Verifier `verifiers/T1.py` unchanged. This is the parity anchor — if T1 at thinking-on + max_tokens=32,768 hits 0/30 silent-non-completions, then the loop is not thinking-on-general.

### Classifier verifier

**New concept:** outcome is not binary pass/fail. It's one of four discrete categories:

| Category | Signature |
|---|---|
| `complete-pass` | Content non-empty, verifier check passes |
| `complete-fail` | Content non-empty, verifier check fails (bug or wrong answer) |
| `silent-non-completion` | Content empty or whitespace-only, `finish_reason: stop` |
| `visible-truncation` | `finish_reason: length`, whether or not content is empty |

Scorer computes the 4-category distribution per cell. Run-level verifier remains the existing per-task `verifiers/*.py` for the `complete-*` split; category assignment happens in `score_qwen_eval.py` based on the raw response envelope + verifier outcome.

No Opus judge. All outcomes are mechanically classifiable.

### Harness changes (additive)

```
evals/qwen-worker-eval/
├── tasks/
│   └── T7v-regex-variant.md       # NEW
├── verifiers/
│   └── T7v.py                     # NEW (+ _smoke.py case)
├── run_qwen_eval.py               # extend: --max-tokens flag (overrides task-level)
├── score_qwen_eval.py             # extend: outcome classifier, 4-category rollup
└── results/
    └── phase2c-{timestamp}/       # gitignored
```

**Runner diff.** `--max-tokens <N>` CLI flag, overrides the default 32,768. Manifest records `max_tokens` and `finish_reason` per run (both already captured in Brief 18's manifest — no schema change, just a CLI knob).

**Scorer diff.** New classifier function in `score_qwen_eval.py`:
```python
def classify_outcome(verifier_result, raw_response) -> str:
    content = raw_response["choices"][0]["message"]["content"] or ""
    finish = raw_response["choices"][0]["finish_reason"]
    if finish == "length":
        return "visible-truncation"
    if not content.strip():
        return "silent-non-completion"
    return "complete-pass" if verifier_result["ok"] else "complete-fail"
```

New rollup section in `summary.md`:
```
## Outcome distribution (Phase 2C)

| Task | max_tokens | complete-pass | complete-fail | silent-non-completion | visible-truncation |
|------|------------|---------------|---------------|------------------------|---------------------|
| T7   | 32768      | 26/30         | 2/30          | 2/30                   | 0/30                |
...
```

**No judge path triggered.** Scorer still generates the manifest and summary; judge dispatch is skipped when `--no-judge` is set, OR when the manifest has `phase: phase2c` in the header (pick one — the CLI flag is simpler).

---

## Run protocol

1. Server smoke test + max_tokens=64 probe. Confirm low-budget `finish_reason: length` works. If not, stop and flag.
2. Write `tasks/T7v-regex-variant.md` + `verifiers/T7v.py`. Smoke-test: reference impl passes, intentional bug fails.
3. Patch `run_qwen_eval.py` — add `--max-tokens` flag, default 32768.
4. Patch `score_qwen_eval.py` — add outcome classifier, 4-category rollup, `--no-judge` flag.
5. Dry-run: T7 × max_tokens=8192 × 1 rep. Confirm manifest captures `finish_reason` and `max_tokens`; confirm classifier emits the right category for whatever outcome it lands on.
6. Run the full 180-run sweep. **Gate:** after the first 30 T1 × 32768 runs complete, confirm 30/30 complete-pass (the parity anchor). If T1 shows any non-complete-pass outcomes at thinking-on, the harness has a bug — stop and diagnose before burning the rest of the budget.
7. Score without judge.
8. **Manual spot-check on every silent-non-completion and visible-truncation run:** read the `reasoning.txt` file, record repetition signature (code-fence re-emit count, "I will output" count, "Wait" count — same metrics as Brief 18 spot-check). This is the H4 evidence.
9. Writeup at `docs/gigo/experiments/08-qwen36-loop-failure.md`.

---

## What the writeup needs to cover

- **Per-task × budget outcome table:** 4-category distribution for all 6 cells.
- **Base rate (H1):** T7 × 32768 silent-non-completion rate with 95% CI. Brief 16 saw 2/30 (6.7%); confirm or correct.
- **Trigger specificity verdict (H2):** does T7v replicate T7's rate? Does T1 stay clean? If T7v≈T7 and T1≈0, the trigger is task-shape-specific. If all three cells fail at comparable rates, the trigger is thinking-on-general.
- **Budget-sensitivity verdict (H3):** pass rate and visible-truncation rate at 8,192 vs 32,768. Expected: 32k hides most loops (silent), 8k surfaces them (visible).
- **Mechanism match (H4):** side-by-side repetition signature for:
  - 2-3 silent-non-completion runs from Phase 2C
  - The 3 preserve-off oscillation runs from Brief 18 (M1 r2, M3 r3, L1 r3)
  - Decision: same loop or distinct?
- **Production implication:**
  - If H2 holds: thinking-on is usable outside regex-from-examples task shapes; ship a task-type blacklist in any thinking-on dispatch harness.
  - If H2 fails: thinking-on requires a wall-clock timeout and visible-truncation observable on every dispatch.
- **Circuit-breaker recommendation:** what max_tokens should `gigo:execute` use on any future thinking-on dispatch to make loops observable? (The answer is informed by H3 — somewhere between 4k and 16k.)
- **Phase 3 readiness call:** does Phase 2C's finding change the Gemma4 bake-off protocol? If thinking-on has a known task-specific trap, the bake-off needs to cover that task shape explicitly to verify cross-vendor generality.

---

## Out of scope for this brief

- **Multi-turn variants.** Brief 18 covered revision. Phase 2C is single-shot only — T7's pathology was observed single-shot.
- **Other task types.** `reasoning` and `structured` tasks. Brief 16 mapped those; the anomaly was specifically T7 (a `code` task).
- **Other sampling profiles.** Pinned to Brief 16's code profile. Open Question #13 (sampling sweep) is a separate brief.
- **Gemma4 or any other model.** This is a Qwen-internals characterisation, not a bake-off. Phase 3 is the bake-off.
- **Fixing the loop.** This brief *characterises*. If the fix is "add a wall-clock timeout to the runner," that's a 1-line harness patch we can ship after the brief. If the fix is "add `preserve_thinking` to single-shot requests when it makes semantic sense," that's a deeper investigation.

---

## Relevant memories

- `feedback_qwen36_worker_profile.md` — recipe + T7 anomaly history.
- `feedback_eval_harness_hygiene.md` — pin the model string verbatim; preserve fixtures.
- `feedback_claude_p_output_style_leak.md` — if the writeup ever triggers a judge re-run for any reason, use `--json-schema`.
- `feedback_kickoff_packet_structure.md` — this brief follows the template.

---

## Deliverables

1. `tasks/T7v-regex-variant.md` + `verifiers/T7v.py` + smoke test addition.
2. Patches to `run_qwen_eval.py` (`--max-tokens`) and `score_qwen_eval.py` (outcome classifier, `--no-judge`, 4-category rollup).
3. Full 180-run sweep under `evals/qwen-worker-eval/results/phase2c-{timestamp}/` (gitignored).
4. Writeup at `docs/gigo/experiments/08-qwen36-loop-failure.md`.
5. Memory update: extend `feedback_qwen36_worker_profile.md` with the T7 characterisation finding and any circuit-breaker recommendation.
6. Phase 9-E subsection appended to `evals/EVAL-NARRATIVE.md` under Phase 9-D.
7. Resolve Open Question #12 (Qwen thinking-loop failure mode) and #18 (Phase 2C). Update #20 (scorer summary inconsistency) if the new `--no-judge` scorer path also needs the token-column fix.

---

## Starting prompt (copy-paste)

```
Run Brief 19 — Qwen3.6 Phase 2C loop-failure characterisation.

Read /Users/eaven/projects/gigo/briefs/19-qwen-phase-2c-loop-failure-eval.md
first — follow it end to end. Extend the existing qwen-worker-eval harness;
do not rebuild.

Guardrails: pin the model string verbatim, preserve existing fixtures, do
not re-run Brief 16 or 17 baselines. No Opus judge in this brief — use the
deterministic outcome classifier. H2 is the highest-value hypothesis; make
sure T1 is run at the same thinking-on setting as T7 so the control lands.

Deliverable order: probe max_tokens=64 first. Write T7v. Patch harness.
Dry-run. Full sweep with the 30-run T1 parity gate. Score. Spot-check
every non-complete-pass run for repetition signature. Writeup. Memory
update. Narrative append. Close Open Questions #12 and #18.
```
