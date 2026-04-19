# Kickoff: Qwen3.6 Phase 2A — Scale Trial (Brief 17)

**Date:** 2026-04-19
**Previous work:** Brief 16 (Phase 1) found `TF3 + thinking-off` = 100% pass, 2.0s walltime, 118 tokens on 10 toy tasks (max ~40 lines each). `docs/gigo/experiments/05-qwen36-worker-profile.md`.
**This brief:** Does that recipe **still hit 100% on realistic task sizes**? Phase 1 ran on 20–40 line tasks; production workers see 200–500+ line refactors, multi-file renames, god-class splits. If TF3-off degrades past some size threshold, the laptop-worker plan is broken and Phase 2B/2C are premature.

---

## Why this brief

Brief 16's data is tight but thin on realism. Every task fit in a ~40-line fence, used stdlib only, and asked for a single-function output. Production worker dispatch from `gigo:execute` will hand Qwen multi-function modules, multi-file changes, and outputs in the 200–500-line range. The recipe survives at small scale — but we don't know where (or whether) it breaks.

Working hypotheses:

- **H1 — TF3 + thinking-off holds at medium scale** (100–200 line tasks) at ≥90% pass.
- **H2 — Quality degrades before pass rate does.** Larger outputs are more likely to pass the deterministic check but lose rigor (missed edge cases, inconsistent naming across a file, dropped type hints on one function).
- **H3 — Multi-file tasks break the recipe.** Qwen has no file access; the ticket has to embed every file inline and the model has to emit them back. At 400+ lines of input, we expect either truncation, file drops, or format violations.

We want a specific answer: **at what task size (lines of input, complexity, number of files) does the recipe stop working?** Knowing the cliff lets us route work correctly — small inline to Qwen, large to Opus or to a multi-step Qwen chain.

---

## Context you need (read in this order)

1. `docs/gigo/experiments/05-qwen36-worker-profile.md` — Phase 1 findings, the baseline we're stressing.
2. `/Users/eaven/.claude/projects/-Users-eaven-projects-gigo/memory/feedback_qwen36_worker_profile.md` — the recipe summary.
3. `evals/qwen-worker-eval/` — reusable harness from Phase 1. You are NOT rebuilding it.
4. `evals/qwen-worker-eval/score_qwen_eval.py::dispatch_judge` + `feedback_claude_p_output_style_leak.md` — the `--json-schema` / `structured_output` fix that made scoring reliable. Keep it.
5. `/Users/eaven/plzhalp/README.md` — Qwen3.6 ground-truth reference, for TF3 shape.

## Endpoint smoke test

Before anything else, confirm the server is live:

```bash
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "unsloth/Qwen3.6-35B-A3B-MLX-8bit",
    "messages": [{"role":"user","content":"respond with just: OK"}]
  }' | jq '.choices[0].message.content'
```

If not running, start via `~/plzhalp` (`./wakeup`).

---

## Design

**Single pinned condition — no sweep.** We already have the winner. This trial measures how it scales.

- **Format:** TF3 (role / SPEC / ACCEPTANCE / OUTPUT FORMAT / MODE HINT)
- **Thinking:** OFF (`chat_template_kwargs.enable_thinking: false`)
- **Sampling:** code → temp 0.6 / top_p 0.95 / top_k 20 / pp 0.0 (Unsloth code profile)
- **Model:** `unsloth/Qwen3.6-35B-A3B-MLX-8bit` (pinned verbatim)
- **max_tokens:** 32768 (same as Phase 1 — watch finish_reason=length for truncation)

**Axis — task size bucket (4 levels):**

| Bucket | Input size | Task scope | N tasks |
|---|---|---|---|
| S | ~20–40 lines | pure function or small bug fix (Phase 1 baseline) | 1 |
| M | ~80–150 lines | multi-function module change, single file | 3 |
| L | ~250–400 lines | class refactor, comprehensive typing, module port | 3 |
| XL | ~400–600 lines across 2–4 files | cross-file rename, feature addition | 2 |

**Replicates:** **5** per task (up from 3 in Phase 1 — 3 replicates is too thin to catch the 10–20% silent-failure tail we saw in T7). Total: **9 tasks × 5 reps = 45 runs.** Thinking-off runs are ~2–30s each at this size, so walltime is ~10–25 minutes.

---

## Tasks (9 total)

Propose these; adjust during design if a task is not amenable to a deterministic verifier.

**S1 (baseline, ~30 lines)**
- Re-use one of the Phase 1 tasks verbatim (suggest T1 dedupe_preserve_order or T3 fizzbuzz). Confirms parity — if S1 doesn't hit 5/5 we have a harness regression, not a scale finding.

**M1 (~100 lines)** — convert inheritance to composition
- Input: 3-class hierarchy with virtual dispatch
- Output: refactored to use composition, same public API, same tests pass

**M2 (~120 lines)** — add `__repr__` and `__eq__` to 6 dataclasses
- Input: 6 dataclass definitions, none with `__repr__`/`__eq__`
- Output: every dataclass has both dunder methods; deterministic check: string format of repr + equality of two equivalent instances

**M3 (~100 lines)** — fix 3 marked bugs in a data pipeline
- Input: pipeline with 3 `# BUG:` comments indicating off-by-one, wrong default, and missing None check
- Output: all 3 fixed; verifier runs the pipeline on fixture data and asserts correct output

**L1 (~300 lines)** — split a god class into 3 responsibility-based classes
- Input: one class with 3 clear responsibility clusters (I/O, computation, formatting)
- Output: 3 classes + facade that preserves public API; verifier instantiates the facade and runs its methods

**L2 (~280 lines)** — add type hints + make mypy-strict clean
- Input: 8-function module with zero type hints
- Output: fully typed, passes a verifier that runs `mypy --strict` (or ast-based check if mypy too slow)

**L3 (~320 lines)** — port a module from `requests` to `httpx` (sync API, not async)
- Input: module using `requests.get/post/session` in 5 places
- Output: ported to `httpx`, same signatures; verifier: AST check that no `import requests` remains and `import httpx` appears; optional smoke by mocking and running one call

**XL1 (~450 lines across 3 files)** — rename a domain concept across files
- Input: 3 fenced files: `models.py`, `service.py`, `test_service.py`. Every `Order`/`order` needs to become `Purchase`/`purchase`, class/attr/variable/filename(within imports).
- Output: 3 modified files, each in its own fenced block tagged with filename. Verifier: parse each fence, assert zero `Order`/`order` in non-comment lines, all imports consistent, tests still reference the renamed module correctly.

**XL2 (~500 lines across 4 files)** — add a nullable field + migration + serializer + test
- Input: 4 fenced files (model, migration-stub, serializer, test)
- Output: field added to model, migration adds column, serializer includes field, test asserts the default null
- Verifier: each file emitted, field appears in all 4, test passes when the fixture is run

**Verifier contract:** every task has a deterministic `verifiers/PhaseN-{id}.py` that extracts emitted fences, runs checks, exit 0 = pass. For multi-file tasks the verifier must handle multiple named fences.

---

## Replicates

5 per task. Key reason: Phase 1 T7 showed a 2/3 silent-failure rate under a different condition. With 3 reps we'd have called that "variance"; with 5 we see the tail clearly. On a 9-task slate this costs 15 extra runs (30s–5min in walltime). Worth it.

---

## Judge

Reuse the Phase 1 judge (`evals/qwen-worker-eval/judge-prompt.md`) with two adjustments:

1. **Add a `completeness` note to `quality`**: large outputs can pass the deterministic check while silently dropping a test case, a type hint, or one call site. Score `quality` down for partial work even when acceptance passes.
2. **Add an explicit multi-file check to `format_adherence`**: for XL tasks, the judge must verify every expected file fence is present. A missing file = `format_adherence: false` even if the emitted files are correct.

Otherwise the 5-field rubric (`acceptance_pass`, `format_adherence`, `fabrication_present`, `quality`, `notes`) carries forward verbatim.

**Judge dispatch:** reuse `score_qwen_eval.py::dispatch_judge` — keep `--json-schema` + `structured_output`. Do NOT regress to the YAML-parse path (Brief 16 cost us 75/180 judge failures before the fix).

---

## Harness

Reuse `evals/qwen-worker-eval/` almost as-is. Minor additions:

```
evals/qwen-worker-eval/
├── tasks/                # existing T1-T10 stay put
│   └── phase2a/
│       ├── S1-dedupe-preserve-order.md
│       ├── M1-inheritance-to-composition.md
│       ├── M2-dataclass-dunders.md
│       ├── M3-pipeline-bugfixes.md
│       ├── L1-god-class-split.md
│       ├── L2-type-hints-strict.md
│       ├── L3-requests-to-httpx.md
│       ├── XL1-domain-rename.md
│       └── XL2-nullable-field-add.md
├── verifiers/
│   └── phase2a/
│       ├── S1.py ... XL2.py
├── build_ticket.py       # no change — TF3 builder already correct
├── run_qwen_eval.py      # minor: accept --tasks-dir tasks/phase2a, --reps 5, --format TF3, --thinking off
├── judge-prompt.md       # minor edit to add completeness + multi-file notes
├── score_qwen_eval.py    # reuse dispatch_judge; aggregate should add size-bucket rollup
└── results/
    └── phase2a-{timestamp}/
```

Runner changes (small):
- Accept a `--tasks-dir` arg so we can run Phase 1 or Phase 2A without filename collisions.
- Add `--pin-format` and `--pin-thinking` to skip the matrix and run one condition.
- Add `--reps N` so we can pin to 5 without editing the script.

Scorer change (small): aggregate **by size bucket** (S, M, L, XL) in addition to per-task. That's the table that tells us where the cliff is.

---

## Run protocol

1. Server smoke test (curl above).
2. Write 9 task files under `tasks/phase2a/` with YAML front-matter (match Phase 1 shape). **Budget most of your time here.** Crafting realistic, verifiable fixtures is the whole game.
3. Write 9 verifiers. Smoke-test each on a reference-correct input AND an intentionally-broken input. Both directions must discriminate.
4. Patch `run_qwen_eval.py` for the three new flags. Dry-run on S1 × 1 rep to confirm the harness.
5. Run the full 45-run sweep. ETA ~15 minutes. Monitor manifest for `finish_reason=length` (truncation) and any empty content.
6. Score with Opus judge — reuse the fixed `dispatch_judge`. ETA ~10–15 minutes.
7. Read summary. Cross-check any failed replicate against its raw content. Look for: truncation (output cut off), format deviation (prose before/after fences), missing files (XL tasks), partial completeness (missed one of N required changes).
8. Writeup at `docs/gigo/experiments/06-qwen36-scale-trial.md`.

---

## What the writeup needs to cover

- Per-size-bucket table: N, pass rate, mean quality, fabrication rate, mean walltime, mean completion tokens.
- Per-task table with 5-replicate variance breakdown. Flag any task with <5/5 pass.
- Truncation audit: how many runs hit `finish_reason=length`? At what bucket?
- Multi-file handling on XL1/XL2: did Qwen emit all files? In the right format? Were any silently dropped?
- Quality delta vs Phase 1 — did mean quality degrade at L or XL vs Phase 1's 4.07?
- Cliff identification: at which bucket (if any) does the recipe stop hitting ≥90% pass?
- Recommendation: is TF3-off safe to dispatch for tasks up to bucket X? What's the routing rule?
- Phase 2B/C readiness: if the recipe holds through L, proceed to 2B (loop). If it breaks at M or L, the loop work needs rethinking first.

---

## Out of scope for this brief

- **Phase 2B — Loop (end-to-end pipeline test).** Separate brief (18). Runs AFTER 2A so we know the worker is safe to wire in.
- **Phase 2C — Thinking-on loop-failure characterization.** Separate brief (19). Also runs AFTER 2A.
- **Local-worker bake-off** vs Gemma4, DeepSeek-Coder, Qwen3-Coder, Codestral, Llama. Tracked as Open Question #15 in `evals/EVAL-NARRATIVE.md`. Gemma4 is the operator's priority — scheduled after Phase 2A/B/C.
- **Sampling profile sweep.** Open Question #13. Keep pinned; revisit if 2A reveals a scale cliff that might be sampling-fixable.
- **Multi-turn with `preserve_thinking`.** Open Question #14. Single-shot in this brief.
- **Any `skills/execute/` changes.** Brief 16 was data-only; Brief 17 stays data-only. Wiring is separate.

---

## Relevant memories

- `feedback_qwen36_worker_profile.md` — the recipe we're stressing.
- `feedback_claude_p_output_style_leak.md` — the judge dispatch gotcha. `--json-schema` + `structured_output`, NOT `--bare` (kills OAuth).
- `feedback_eval_harness_hygiene.md` — pin the model string verbatim; preserve fixtures once written.
- `feedback_judge_rubric_fabrication_blindspot.md` — keep the explicit fabrication check.

---

## Deliverables

1. 9 task files under `evals/qwen-worker-eval/tasks/phase2a/` with deterministic verifiers.
2. Minor patches to `run_qwen_eval.py` (flags: `--tasks-dir`, `--pin-format`, `--pin-thinking`, `--reps`) and `score_qwen_eval.py` (size-bucket rollup).
3. Edited `judge-prompt.md` with completeness + multi-file notes (keep it small — don't rewrite).
4. Full 45-run sweep under `evals/qwen-worker-eval/results/phase2a-{timestamp}/` (gitignored — already covered by `evals/qwen-worker-eval/results/`).
5. Writeup at `docs/gigo/experiments/06-qwen36-scale-trial.md`.
6. Memory update: extend `feedback_qwen36_worker_profile.md` with the scale finding (don't create a new memory unless the recipe changes).
7. Append Phase 9-C subsection to `evals/EVAL-NARRATIVE.md` under Phase 9-B.
8. If the recipe survives: mark Open Question #12 (thinking-loop characterization) as ready for Phase 2C, and Open Question "Phase 2B readiness" as green. If it breaks: raise the cliff location as a new blocker.

---

## Starting prompt for the new session

Paste this into a fresh Claude Code session in `/Users/eaven/projects/gigo`:

> Kickoff packet at `briefs/17-qwen-phase-2a-scale-eval.md`. Read the whole file before doing anything. Phase 1 (Brief 16) is done — writeup at `docs/gigo/experiments/05-qwen36-worker-profile.md`, recipe in `feedback_qwen36_worker_profile.md`. This brief stress-tests the recipe at realistic task sizes. Reuse the Phase 1 harness at `evals/qwen-worker-eval/` — do not rebuild it. Target deliverable: 45-run sweep + writeup + narrative update. Out of scope: loop test (Phase 2B), loop-failure characterization (2C), bake-off, wiring changes. Check server is live, then start designing the 9 task fixtures.
