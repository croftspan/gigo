# qwen-worker-eval

Harness for profiling Qwen3 models as gigo workers. Used for Briefs 16, 17, 18, and future Gemma comparisons.

## Prereqs

- Python 3.11+
- `pip install -r requirements.txt` (PyYAML only)
- An OpenAI-compatible chat completions endpoint serving the target model
  - Local MLX (default): `mlx_lm.server --model unsloth/Qwen3.6-35B-A3B-MLX-8bit --port 8080`
  - Remote: set `QWEN_ENDPOINT` or pass `--endpoint`
- Opus 4.7 via Claude Code CLI for the judge (`claude` on PATH). Only needed for `score_qwen_eval.py`, not the runner.

## Configure

Endpoint and model resolve in this order: CLI flag → env var → hardcoded default.

```bash
export QWEN_ENDPOINT="http://intranet-host:8080/v1/chat/completions"
export QWEN_MODEL="unsloth/Qwen3.6-35B-A3B-MLX-8bit"
```

Or per-invocation:

```bash
./run_qwen_eval.py --endpoint http://host:port/v1/chat/completions --model some/model ...
```

## Running

Full Phase 1 sweep (tasks × formats × thinking × reps):

```bash
./run_qwen_eval.py
```

Pinned single cell (the production recipe — TF3 + thinking-off):

```bash
./run_qwen_eval.py --pin-format TF3 --pin-thinking off --reps 5
```

Phase 2A scale trial:

```bash
./run_qwen_eval.py --tasks-dir tasks/phase2a --pin-format TF3 --pin-thinking off --reps 5
```

Phase 2B multi-turn (the 2-turn revision loop):

```bash
# T-off arm
./run_qwen_eval.py --mode multi-turn --tasks-dir tasks/phase2b \
    --pin-format TF3 --pin-thinking off --reps 5

# T-on preserve-on arm
./run_qwen_eval.py --mode multi-turn --tasks-dir tasks/phase2b \
    --pin-format TF3 --pin-thinking on --pin-preserve on --reps 5
```

## Scoring

```bash
./score_qwen_eval.py results/<stamp>
```

Uses `claude -p --json-schema` to invoke Opus 4.7 as judge against `judge-prompt.md` (single-turn) or `judge-prompt-revision.md` (multi-turn). Writes `scores.jsonl`, `summary.md`, and `manifest.jsonl` into the run dir.

**Known scorer quirk** (Open Question #20 in `evals/EVAL-NARRATIVE.md`): the multi-turn summary reports turn-2-only completion tokens while walltime is t1+t2 summed — treat summary token columns as turn-2 unless you cross-check against `manifest.jsonl`.

## Result layout

```
results/<YYYY-MM-DD-HHMMSS>/
  <task>--<format>-thinking-<on|off>[-preserve-<on|off>]--r<N>.json      # raw response(s)
  <task>--<format>-thinking-<on|off>[-preserve-<on|off>]--r<N>.content.txt
  <task>--<format>-thinking-<on|off>[-preserve-<on|off>]--r<N>.reasoning.txt
  manifest.jsonl                                                          # one row per run
  scores.jsonl, summary.md                                                # after scoring
```

`results/` is a tracked directory with a `.gitignore` stub; result contents are ignored so the harness can write into it on a fresh clone without `mkdir -p`.

## Writeups

- `docs/gigo/experiments/05-qwen36-worker-profile.md` (Brief 16, toy scale)
- `docs/gigo/experiments/06-qwen36-scale-trial.md` (Brief 17, realistic scale)
- `docs/gigo/experiments/07-qwen36-multi-turn.md` (Brief 18, 2-turn revision)
- `evals/EVAL-NARRATIVE.md` Phase 9-A..D for the cross-brief running log
