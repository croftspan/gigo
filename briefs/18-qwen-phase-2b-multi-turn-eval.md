# Kickoff: Qwen3.6 Phase 2B — Multi-turn with preserve_thinking (Brief 18)

**Date:** 2026-04-19
**Previous work:**
- Brief 16 (Phase 1) — `TF3 + thinking-off` wins single-shot on toy tasks. Thinking-on adds a silent-failure tail (T7 oscillated in reasoning 9+ min → empty output). `docs/gigo/experiments/05-qwen36-worker-profile.md`.
- Brief 17 (Phase 2A) — same recipe holds at realistic scale: 45/45 pass S (20 lines) through XL (500 lines across 4 files), mean quality 3.96, 0 fabrication. `docs/gigo/experiments/06-qwen36-scale-trial.md`.
**This brief:** Production gigo is a **loop**, not a shot. Opus plans → Qwen executes → reviewer critiques → Qwen revises. Does `preserve_thinking` flip Qwen's thinking-mode from net-negative (Brief 16) to net-positive when there's actual prior context to anchor the reasoning?

---

## Why this brief

Briefs 16–17 settled single-shot execution. Single-shot is only half the real workflow. The other half is **revision** — the Two-Kinds-of-Leadership pipeline has `gigo:verify` producing pointed critiques that a worker must act on without discarding what was right the first time.

Brief 16's most interesting anomaly was T7 × TF3 × thinking-on: reasoning trace oscillated between equivalent regex forms forever and never emitted content. That was **single-shot thinking-on with no context to anchor the reasoning**. Multi-turn is specifically where `preserve_thinking` is designed to pay off — the prior `<think>` block carries into the next turn, so turn-2 reasoning builds on turn-1's commitments instead of re-deriving from scratch.

Working hypotheses:

- **H1 — Revision with thinking-off works cleanly.** Brief 17's TF3-off baseline extended to a 2-turn cycle still clears ≥90% on combined pass (acceptance + critique addressed), matching single-shot within noise.
- **H2 — Thinking-on + `preserve_thinking: true` fixes the two Phase 2A craft-3s.** Specifically: M1 r3 (TimestampDecorator naming drift) and M3 r4 (signature-breaking bugfix) were quality-3 runs where the worker shipped correct code but violated a craft constraint. If thinking-mode with preserved reasoning helps, these task-critique pairs should come back as quality-4+ revisions on ≥4/5 replicates.
- **H3 — Thinking-on + `preserve_thinking: false` is the worst cell.** Worker sees prior output but lost its prior reasoning, re-derives from scratch, reproduces the T7 oscillation tail. Prediction: ≥1/5 replicate hits `finish_reason=length` with empty content on at least one task.
- **H4 — The `preserve_thinking` mechanism is a finding in its own right.** Either `mlx_lm.server` passes the chat-template kwarg through natively, or it doesn't and we need client-side fallback. The answer shapes how we wire multi-turn into `gigo:execute` — log it.

We want a specific answer: **is thinking-on safe to re-enable for revision flows, and under which `preserve_thinking` setting?** The recipe wired into `gigo:execute`'s revision path depends on it.

---

## Context you need (read in this order)

1. `docs/gigo/experiments/05-qwen36-worker-profile.md` — Phase 1, the T7 anomaly, why thinking-on is blacklisted.
2. `docs/gigo/experiments/06-qwen36-scale-trial.md` — Phase 2A, the TF3-off baseline we're extending. **Read §Results judge notes carefully** — M1 r3 and M3 r4 are the real-defect anchors for this brief.
3. `/Users/eaven/.claude/projects/-Users-eaven-projects-gigo/memory/feedback_qwen36_worker_profile.md` — recipe summary.
4. `evals/qwen-worker-eval/` — Phase 1/2A harness. **You are extending it with a multi-turn mode, not rebuilding.** Most changes are localised: a new runner mode, a new critique builder, a revision-specific judge prompt, a 2-stage verifier pattern.
5. `evals/qwen-worker-eval/score_qwen_eval.py::dispatch_judge` + `feedback_claude_p_output_style_leak.md` — the `--json-schema` / `structured_output` fix. Keep it. Do NOT regress.
6. Qwen3/Unsloth docs on `chat_template_kwargs.preserve_thinking` — confirm semantics before assuming. Use Context7 if needed; the MLX build may pass it through or silently ignore.

---

## Endpoint + `preserve_thinking` smoke test

**Do this before writing any tasks.** The probe outcome determines the harness architecture.

```bash
# 1. Liveness check (same as Phase 1/2A)
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "unsloth/Qwen3.6-35B-A3B-MLX-8bit",
    "messages": [{"role":"user","content":"respond with just: OK"}]
  }' | jq '.choices[0].message.content'

# 2. preserve_thinking probe — 3 requests
#    (a) thinking-on turn 1 → capture message.reasoning + message.content
#    (b) turn 2 with [prior_user, prior_assistant(reasoning+content), new_user]
#        and chat_template_kwargs.preserve_thinking: true
#    (c) same messages, preserve_thinking: false
# Compare turn-2 reasoning trace between (b) and (c).
# If identical → flag ignored → client-side fallback required.
# If divergent → server-native → wire it straight through.
```

**Client-side fallback (if needed):** manually include the prior assistant turn's `reasoning` in the next turn's `messages` — either inside an `assistant` role message with a structured body, or embedded as a `<think>...</think>` block in a synthesised assistant turn. Pick one pattern, document it in the writeup, keep it consistent across the sweep.

If server not running: `cd ~/plzhalp && ./wakeup`.

---

## Design

**Axis 1 — Turn pattern (pinned):** 2-turn revise-on-feedback.
- Turn 1: standard TF3 ticket (same shape as Phase 2A).
- Turn 2: canned reviewer critique + revision instruction appended to the conversation.

The 1-turn control is **Brief 17's existing data.** Do not re-run it — reference `evals/qwen-worker-eval/results/phase2a-sweep/` as the baseline.

**Axis 2 — Thinking configuration (3 levels):**

| Level | `enable_thinking` | `preserve_thinking` | What it tests |
|---|---|---|---|
| **T-off** | `false` | N/A | Brief 17 recipe in multi-turn — the parity anchor. If this doesn't clear ≥90% combined pass, we have a harness regression, not a thinking finding. |
| **T-on-no-preserve** | `true` | `false` (or default) | Thinking-on with turn-1 `<think>` stripped from turn-2 — expected to reproduce the T7 pathology. |
| **T-on-preserve** | `true` | `true` | Thinking-on with turn-1 `<think>` carried forward — the condition this brief is really about. |

**Pinned (same as Brief 17):**

| Axis | Pinned value |
|---|---|
| Ticket format | TF3 (role / SPEC / ACCEPTANCE / OUTPUT FORMAT / MODE HINT) |
| Sampling profile | code → temp 0.6 / top_p 0.95 / top_k 20 / pp 0.0 |
| Model | `unsloth/Qwen3.6-35B-A3B-MLX-8bit` |
| max_tokens | 32768 per turn |
| Task pool | 6 tasks drawn from Phase 2A (2 × M, 2 × L, 2 × XL). S excluded — critiques on 20-line functions are too shallow. |

**Replicates:** 5 per cell. **6 tasks × 3 conditions × 5 reps = 90 runs.** T-on conditions may run long (Brief 16 showed 9+ min walltime on T7-like pathology); budget 45 min – 2 h for the sweep depending on whether T-on-no-preserve oscillates.

---

## Tasks and critiques (6 total)

Reuse Phase 2A fixtures directly. Add a `revision_critique` block to each task's YAML front-matter. **Two categories, flagged honestly:**

### Real-defect critiques (2 tasks — the primary signal)

These correct documented Phase 2A judge observations. They are the actual "does revision work?" test, because the critique targets a real craft weakness the model exhibited.

**M1 — inheritance to composition** *(anchors H2)*
- Critique: "Your `TimestampDecorator` class is named like a decorator but doesn't decorate anything — it's a wrapper that adds a timestamp field. Rename it to something that reflects what it actually does (`TimestampedWriter`, `TimestampedCache`, or similar) and update all references."
- Source: Phase 2A judge note on M1 r3 — "TimestampDecorator isn't actually a decorator."

**M3 — pipeline bugfixes** *(anchors H2)*
- Critique: "Your fix to `normalize` changed the function's signature from `defaults: list = []` to `defaults: list | None = None`. The acceptance criteria require function signatures to stay unchanged. Fix the mutable-default bug without changing the public signature (use the sentinel-default pattern inside the function body)."
- Source: Phase 2A judge note on M3 r4 — "changed normalize's signature (correct bug-fix, unnecessary API break)."

### Synthetic-craft critiques (4 tasks — secondary signal, call this out in the writeup)

Phase 2A flagged no judge-level defects on L1, L3, XL1, XL2. Critiques below are plausible reviewer output but are **not** documented worker weaknesses. They test the mechanical question "does the worker follow a reviewer instruction without regressing?" rather than the craft question "does revision fix real defects?"

**L1 — god-class split**
- Critique: "The four private formatters in `ReportFormatter` never touch `self`. Lift them to module-level functions so the class only holds methods that need instance state."

**L3 — requests to httpx**
- Critique: "You left `import json` at the top of the module. `httpx` responses have a built-in `.json()` method; the standalone `json` import is now unused. Remove it and verify no other call site depends on it."

**XL1 — domain rename**
- Critique: "Your rename stopped at symbol level. The test fixture IDs are still the string literals `'o1'` and `'o2'`. Rename them to `'p1'` and `'p2'` so the Purchase vocabulary is consistent down to test data."

**XL2 — nullable field**
- Critique: "Your migration has an `up()` but no `down()`. Add a symmetric `down()` that drops the `deleted_at` column — gigo migrations are expected to be reversible."

### Verifier contract (extends Phase 2A)

Each task's `verifiers/phase2b/<ID>.py`:
- Accepts both turn-1 and turn-2 content (verifier chooses what it needs).
- **First:** runs the Phase 2A verifier checks on turn-2 content — exit 1 if original acceptance regressed.
- **Second:** runs critique-specific checks — exit 1 if the revision didn't land.
- Exit 0 iff both pass.
- Smoke-test each verifier on three fixtures: (a) correct revision PASS, (b) original-acceptance drop FAIL, (c) critique-not-addressed FAIL. All three must discriminate.

---

## Judge

Reuse the Phase 1/2A judge prompt with **one new field**:

- **`critique_addressed` (boolean):** Did turn-2 specifically address the reviewer critique without breaking what was already correct? This is the distinguishing signal between "reasoned and improved" and "re-generated from scratch and happened to pass."

Judge sees: turn-1 content, the critique text, turn-2 content. Asks: is turn-2 a meaningful revision or a cosmetic rewrite?

Updated rubric: `acceptance_pass`, `format_adherence`, `fabrication_present`, `critique_addressed` (new), `quality`, `notes`. **Revision pass** = `acceptance_pass && format_adherence && !fabrication_present && critique_addressed`.

Extend `JUDGE_SCHEMA` in `score_qwen_eval.py` with the new field. Put revision rubric in a new `judge-prompt-revision.md` — do NOT stuff both rubrics into one prompt.

**Judge dispatch:** reuse `score_qwen_eval.py::dispatch_judge` — keep `--json-schema` + `structured_output`. Regressing to YAML parsing cost us 75/180 judge calls in Brief 16.

---

## Harness

Extend `evals/qwen-worker-eval/` with a multi-turn mode:

```
evals/qwen-worker-eval/
├── tasks/
│   └── phase2b/
│       ├── M1-revise-naming-drift.md
│       ├── M3-revise-preserve-signature.md
│       ├── L1-revise-extract-module-level.md
│       ├── L3-revise-remove-unused-import.md
│       ├── XL1-revise-rename-fixture-ids.md
│       └── XL2-revise-add-down-migration.md
├── verifiers/
│   └── phase2b/
│       ├── M1.py ... XL2.py        # 2-stage: original + critique-specific
│       └── _smoke.py
├── build_ticket.py                  # no change (turn 1)
├── build_critique.py                # NEW: renders turn-2 user message
├── run_qwen_eval.py                 # extend: --mode multi-turn, --preserve-thinking on|off
├── judge-prompt.md                  # unchanged
├── judge-prompt-revision.md         # NEW: revision-specific rubric
├── score_qwen_eval.py               # extend: turn-2 scoring, critique_addressed rollup
└── results/
    └── phase2b-{timestamp}/
        ├── <stem>.turn1.content.txt
        ├── <stem>.turn1.reasoning.txt
        ├── <stem>.turn2.content.txt
        ├── <stem>.turn2.reasoning.txt
        ├── <stem>.raw.json          # full conversation + both responses
        └── manifest.jsonl
```

**Runner changes (additive — single-shot still works):**
- `--mode {single-shot,multi-turn}`, default `single-shot`.
- `--preserve-thinking {on,off}` — only meaningful with `--pin-thinking on --mode multi-turn`.
- Task files in `phase2b/` carry `revision_critique` in front-matter; runner fetches it for turn 2.
- Manifest records: `turn1_elapsed_s`, `turn2_elapsed_s`, `turn1_tokens`, `turn2_tokens`, `preserve_thinking`, `mode`.

**Critique construction (`build_critique.py`):** single-template constant. Shape:

> Review of your previous response:
>
> {critique text}
>
> Please revise your previous output to address this feedback while keeping everything else correct. Output format is the same as before: {OUTPUT FORMAT reminder}.

No branching. A second template is a new file, not a flag.

**Scorer changes:**
- Score turn-2 content as the primary artifact.
- Run `verifiers/phase2b/<task>.py` with both turns available.
- `summary.md` adds "Per thinking config × task" and "Per thinking config (aggregate)" sections.
- Roll up `critique_addressed` rate per condition.

---

## Run protocol

1. Server smoke test. **`preserve_thinking` probe first** — decide and log the preservation mechanism (server-native vs client-side fallback) before writing tasks.
2. Write 6 task files under `tasks/phase2b/` with `revision_critique` front-matter. Adapt from Phase 2A sources — do NOT duplicate the original SPEC; reference it and add the critique block. Flag the 2 real-defect vs 4 synthetic-craft split explicitly in each file's front-matter (`critique_type: real-defect | synthetic-craft`).
3. Write 6 verifiers under `verifiers/phase2b/`. Smoke-test each on (a) correct revision PASS, (b) acceptance-regressed FAIL, (c) critique-not-addressed FAIL. All three directions must discriminate.
4. Build `build_critique.py` as a single-template module. Unit-test it renders a plausible turn-2 message on M1 and XL2 (the shortest and longest).
5. Patch `run_qwen_eval.py` for multi-turn. **Dry-run on M1 × T-off × 1 rep.** Verify: two content files + two reasoning files saved, manifest records both elapsed times and both token counts, raw JSON has well-formed conversation history.
6. Extend `judge-prompt-revision.md` + `JUDGE_SCHEMA`. End-to-end test the judge on the dry-run output.
7. Run the full 90-run sweep. **Parity gate:** after the first 30 T-off runs complete, confirm T-off clears ≥90% combined pass before starting T-on cells. If it doesn't, the harness is broken, not the thinking finding.
8. Score with Opus judge. Budget ~20 min, ~$10.
9. Read summary. Spot-check any cell with <3/5 on either acceptance or critique-addressed — especially T-on-preserve failures (H2 rests on them) and T-on-no-preserve empty-content runs (H3 rests on them).
10. Writeup at `docs/gigo/experiments/07-qwen36-multi-turn.md`.

---

## What the writeup needs to cover

- **`preserve_thinking` mechanism:** server-native or client-side fallback. Exact message-construction pattern used. Log it — future multi-turn work depends on it.
- **Per-thinking-config table:** N, acceptance pass, critique-addressed, combined pass, mean quality, fabrication, mean turn-1 + turn-2 walltime, mean turn-2 completion tokens.
- **Per-task × condition table:** 5-replicate variance. Flag any cell < 5/5 on either axis.
- **Reasoning-loop tail check:** did T-on-no-preserve reproduce the T7 pathology? How many turn-2 runs hit `finish_reason=length` with empty content? Did T-on-preserve prevent it?
- **H2 verdict on the real-defect pair (M1 + M3):** did thinking-on-preserve specifically fix the Phase 2A quality-3s? This is the strongest signal in the dataset — call out separately from the synthetic-craft tasks.
- **Craft-quality delta across thinking configs** on the runs that passed acceptance in all 3 cells — is thinking-on + preserve producing higher-quality work, or just slower work?
- **Critique-address failure modes:** when the worker failed `critique_addressed`, what did it do? Regenerated from scratch? Ignored the critique? Partial-addressed + broke acceptance?
- **Recommendation:** what thinking config does `gigo:execute`'s revision path use? Same as single-shot (thinking-off) or different?
- **Phase 2C readiness call:** if T-on-no-preserve reproduced the loop pathology, 2C (targeted regex-from-examples × 20 reps) has what it needs. If preservation already fixed the problem, 2C may be moot — reframe or cancel.

---

## Out of scope for this brief

- **Phase 2C — Thinking-loop targeted characterisation.** Separate brief (19). Runs AFTER 2B so we know whether `preserve_thinking` already resolved it.
- **3+ turn loops.** Agentic refinement, multi-step conversations. Separate design question.
- **Critique generation by a live reviewer model.** Critiques here are pre-authored to isolate the revision-mechanism question. Live `gigo:verify` → Qwen revision is a Phase 3 experiment.
- **Local-worker bake-off** vs Gemma4, DeepSeek-Coder, Qwen3-Coder, Codestral, Llama. Tracked as Open Question #15. Gemma4 is the operator priority; scheduled after 2B/2C.
- **Sampling profile sweep** (Open Question #13). Pinned here.
- **Any `skills/execute/` changes.** 2B is data-only. Wiring the revision path is a separate PR after the recipe is confirmed.

---

## Relevant memories

- `feedback_qwen36_worker_profile.md` — the recipe we're extending to multi-turn.
- `feedback_claude_p_output_style_leak.md` — judge dispatch gotcha. `--json-schema` + `structured_output`, NOT `--bare` (kills OAuth).
- `feedback_eval_harness_hygiene.md` — pin the model string verbatim; preserve fixtures.
- `feedback_judge_rubric_fabrication_blindspot.md` — keep the explicit fabrication check.
- `feedback_kickoff_packet_structure.md` — this brief follows the template.

---

## Deliverables

1. 6 task files under `evals/qwen-worker-eval/tasks/phase2b/` with `revision_critique` + `critique_type` front-matter.
2. 6 paired verifiers under `verifiers/phase2b/` with `_smoke.py` discriminator (3-direction test per verifier).
3. `build_critique.py` (new, single-template constant).
4. `judge-prompt-revision.md` (new) with extended rubric including `critique_addressed`.
5. Patches to `run_qwen_eval.py` (`--mode`, `--preserve-thinking`) and `score_qwen_eval.py` (turn-2 handling, revision scoring, `critique_addressed` rollup, extended `JUDGE_SCHEMA`).
6. Full 90-run sweep under `evals/qwen-worker-eval/results/phase2b-{timestamp}/` (gitignored).
7. Writeup at `docs/gigo/experiments/07-qwen36-multi-turn.md`.
8. Memory update: extend `feedback_qwen36_worker_profile.md` with the multi-turn finding and the revision-path thinking decision. Create a new memory **only** if the multi-turn recipe contradicts the single-shot recipe materially.
9. Phase 9-D subsection appended to `evals/EVAL-NARRATIVE.md` under Phase 9-C.
10. Update Open Question #14 in the narrative — mark resolved or refine based on the `preserve_thinking` mechanism finding.
11. Readiness call on Phase 2C: green / reframe / cancel.

---

## Starting prompt for the new session

Paste this into a fresh Claude Code session in `/Users/eaven/projects/gigo`:

> Kickoff packet at `briefs/18-qwen-phase-2b-multi-turn-eval.md`. Read the whole file before doing anything. Phases 1 and 2A are shipped — writeups at `docs/gigo/experiments/05-qwen36-worker-profile.md` and `06-qwen36-scale-trial.md`, recipe in `feedback_qwen36_worker_profile.md`. This brief tests whether `preserve_thinking` flips Qwen's thinking-mode from net-negative (Brief 16) to net-positive in 2-turn revision flows. Reuse the Phase 1/2A harness at `evals/qwen-worker-eval/` — you are **extending** it with a multi-turn mode, not rebuilding. Target deliverable: 90-run sweep (6 tasks × 3 thinking configs × 5 reps) + writeup + narrative update. Out of scope: Phase 2C (loop-failure sweep), 3+ turn loops, live-reviewer critique generation, local-worker bake-off, `skills/execute/` wiring. **Before writing any tasks**, run the 3-request `preserve_thinking` probe on the live MLX server and decide whether we get server-native preservation or need client-side fallback — log the decision in the writeup. Then design the 6 critique fixtures, leaning on the real-defect anchors (M1 naming drift, M3 signature break) from Phase 2A's judge notes.
