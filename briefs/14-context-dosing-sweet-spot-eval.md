# Kickoff: Context-dosing sweet spot on Opus 4.7

**Date:** 2026-04-19
**Depends on:** Brief 13 (`briefs/13-v0.14-opus-4-7-eval.md`) must complete first. This brief assumes Brief 13 has produced assembled-vs-bare numbers for v0.14 + Opus 4.7.
**This session's job:** Find where on the context-mass axis Opus 4.7 actually performs best. Is full gigo helping, or have we over-contexted? Five conditions, rank-based scoring, per-prompt token accounting, clear recommendation.

---

## The question

Opus 4.7 is anecdotally sensitive to context mass — more tokens can hurt reasoning quality, not help it. Brief 13 only answers "full gigo vs nothing." That's binary; the sweet spot could be anywhere in between.

This eval sweeps the mass axis with 5 conditions and scores them against each other. The outcome is one of:

- **Monotonic up** — more context always helps, keep shipping full gigo.
- **Peak below full** — there's an intermediate condition that beats full. Trim.
- **Peak at bare** — gigo hurts Opus 4.7 on average. Different approach needed.
- **Per-domain / per-axis split** — e.g., full wins on review prompts but over-contexts on advisory. Domain-aware dosing.

## Context you need (read in this order)

1. `briefs/13-v0.14-opus-4-7-eval.md` — the Phase 1 packet. Same harness base, same fixtures. This brief extends that one.
2. `docs/gigo/experiments/02-opus-4-7-v0.14-assembled-vs-bare.md` — Phase 1 writeup (produced by Brief 13). Read the headline numbers and per-prompt verdicts before designing Phase 2. If Phase 1 shows assembled already losing on many prompts, the hypothesis shifts from "trim to a sweet spot" to "gigo approach needs rethinking."
3. `evals/run-eval.sh` — the harness you'll fork/extend. Brief 13 already pinned `--model claude-opus-4-7` and restored the `CLAUDE.md*` glob; this brief inherits both fixes.
4. `evals/judge-prompt.md` — pairwise judge. You'll adapt to rank-of-5 for this phase (see "Judge adaptation" below).
5. `evals/fixtures/rails-api/CLAUDE.md` and `evals/fixtures/childrens-novel/CLAUDE.md` — the source-of-truth full-assembled content from which the trimmed variants get derived.
6. Memory `feedback_persona_activation_cost.md` — prior theory-side observation that persona defs in rules are dead weight until activated. Directly relevant to whether C1/C2 beat C3.
7. Memory `reference_hu_et_al_persona_tradeoff.md` — the authority reference for why personas can HURT knowledge retrieval even as they help alignment.
8. Memory `project_experiment_results.md` — Phase 9 finding: "architecture carries coherence, personas add polish." If true on Opus 4.7, trimmed variants should hold most of the assembled win.

## What's new since Brief 13

Brief 13 produced:
- Harness with `--model claude-opus-4-7` pinned
- Bare-contamination glob restored
- Writeup at `docs/gigo/experiments/02-opus-4-7-v0.14-assembled-vs-bare.md`
- Two-condition baseline (bare / full assembled) on rails-api + childrens-novel

This brief builds 3 more conditions and scores all 5 together.

---

## Experimental design

### Five conditions on the context-mass axis

For each domain, build these variants from the existing `CLAUDE.md` + `.claude/` source. Name the directories `fixture-c0` through `fixture-c4`.

| Condition | What's in it | Est. tokens (CLAUDE.md + rules) |
|---|---|---|
| **C0 — Bare** | Source files only. No `CLAUDE.md`, no `.claude/`. | 0 |
| **C1 — Roster only** | Stripped `CLAUDE.md`: persona names + "Modeled after" one-liners only. NO quality bars, NO won't-do, NO autonomy model, NO quick reference. Tests whether "knowing the cast" without the directives adds signal. | ~20% of C3 |
| **C2 — Team, no rules** | Full `CLAUDE.md` (personas + quality bars + won't-do + autonomy + quick reference) but NO `.claude/rules/` and NO `.claude/references/`. Tests whether the team framing alone carries the gain. | ~40% of C3 |
| **C3 — Full assembled (baseline)** | Current full gigo: `CLAUDE.md` + `.claude/rules/` + `.claude/references/`. Same as Brief 13's assembled condition. | 100% (baseline) |
| **C4 — Rules only** | NO `CLAUDE.md` (rename to `CLAUDE.md.hidden` during copy). Keep `.claude/rules/` and `.claude/references/`. Tests whether structural guidance alone beats bare — decouples team from rules. | ~60% of C3 |

Token numbers are approximate — the writeup MUST report exact token counts per condition per domain (`wc -m` on all loaded files).

### Why these 5 and not more

Resisting the urge to test 10+ variants. Each condition needs a hypothesis it's designed to answer:

- **C0 vs C3** (from Brief 13) — does gigo help at all?
- **C1 vs C3** — are quality bars + autonomy + references load-bearing, or does the cast alone do the work?
- **C2 vs C3** — are the rules files earning their token cost?
- **C4 vs C3** — does the team framing matter, or is it really the rules doing the work?
- **C1/C2/C4 vs C0** — do any partial configurations beat bare by themselves?

If results are ambiguous after this sweep, add conditions in a Phase 3. Don't front-load.

### Prompts + fixtures

Same 7 prompts per domain (`evals/prompts/*.txt`), same two fixtures. Brief 13 default of "preserve, don't refresh" applies here too — the trimmed variants are derived from the same source `CLAUDE.md` each fixture has today.

### Run matrix

5 conditions × 2 domains × 7 prompts = **70 generation runs**. At Opus 4.7 latency, budget ~60-90 min for generation. Judge scoring adds another 30-45 min. Total: allow ~2 hours for the full cycle.

---

## REQUIRED pre-flight fixes

### Fix 1 — Fork the harness as `run-dosing-eval.sh`

Do NOT modify `run-eval.sh` in-place. Copy it to `evals/run-dosing-eval.sh` and extend. Reasoning: Brief 13's harness needs to stay runnable for future regression checks against the 2-condition baseline. Dosing eval is additive, not a replacement.

Key changes in the fork:

```bash
CONDITIONS=("c0-bare" "c1-roster" "c2-team-no-rules" "c3-full" "c4-rules-only")

for domain in "${DOMAINS[@]}"; do
  for condition in "${CONDITIONS[@]}"; do
    # Build the temp dir for this (domain, condition) pair
    # Exclusion logic differs per condition — see Fix 2
    # Run `claude -p "$prompt" --model claude-opus-4-7 ...`
    # Output to $DOMAIN_RESULTS/${PADDED}-${condition}.json
  done
done
```

### Fix 2 — Variant builders (the load-bearing part)

Each condition needs a deterministic build script. Create `evals/build-variant.sh`:

```bash
#!/usr/bin/env bash
# Usage: build-variant.sh <source-fixture-dir> <condition> <dest-tmpdir>
# Deterministically constructs a condition variant from the full-assembled source.
```

- `c0-bare` — copy source files, exclude `CLAUDE.md*` (glob), exclude `.claude/`.
- `c1-roster` — copy all, then REPLACE `CLAUDE.md` with a roster-only extraction. Strip everything below each persona's "Modeled after:" line up to the next persona. Also strip Autonomy Model and Quick Reference sections. Verify result is ~20% of original `wc -c`.
- `c2-team-no-rules` — copy all, delete `.claude/rules/` and `.claude/references/`. Keep `CLAUDE.md` intact.
- `c3-full` — copy all (no modifications). Equivalent to Brief 13 assembled.
- `c4-rules-only` — copy all, delete `CLAUDE.md` (and any variants — use `CLAUDE.md*` glob).

**Determinism matters.** The variant builds must be a pure function of the source fixture — no timestamps, no randomness, no manual edits. If the source fixture changes, re-deriving the variants must produce exactly what got tested. This is so a future session can reproduce a 2026-04-19 run from a SHA.

**Sanity check for each condition** (print before run):
```
echo "Condition: $condition"
echo "  Files present: $(find "$TMPDIR" -type f | wc -l)"
echo "  CLAUDE.md bytes: $(wc -c < "$TMPDIR/CLAUDE.md" 2>/dev/null || echo 0)"
echo "  rules/ files: $(find "$TMPDIR/.claude/rules" -type f 2>/dev/null | wc -l)"
echo "  references/ files: $(find "$TMPDIR/.claude/references" -type f 2>/dev/null | wc -l)"
```

### Fix 3 — Judge adaptation (rank-of-5, not pairwise)

`evals/judge-prompt.md` is pairwise ("A or B"). For 5 conditions, use rank-ordered judging. Create `evals/judge-prompt-rank5.md` with the same 5 criteria but this output contract:

```json
{
  "quality_bar": { "rank": ["c3-full", "c2-team-no-rules", "c1-roster", "c4-rules-only", "c0-bare"], "scores": {"c0-bare": 0, "c1-roster": 1, "c2-team-no-rules": 2, "c3-full": 3, "c4-rules-only": 1} },
  "persona_voice": { "rank": [...], "scores": {...} },
  "expertise_routing": { "rank": [...], "scores": {...} },
  "specificity": { "rank": [...], "scores": {...} },
  "pushback_quality": { "rank": [...], "scores": {...} },
  "notes": "One sentence on the key difference pattern"
}
```

The judge sees all 5 responses to the same prompt, labeled only as Response 1-5 (random mapping to conditions per prompt — log the mapping). Score each 0-3, then rank. Ties in scores → tied ranks allowed.

**Critical: the judge must not see the condition label during scoring.** Store the condition→response-number mapping OUTSIDE the judge's context. The scorer script applies the mapping after the judge returns.

### Fix 4 — Token accounting per condition

Every result file needs a `tokens_loaded` field — approximate context mass loaded into the assembled context BEFORE the prompt. Measure with:

```bash
# Per condition variant, before running the prompt
TOKENS_LOADED=$(find "$TMPDIR" \( -name "CLAUDE.md" -o -path "*/.claude/rules/*" -o -path "*/.claude/references/*" \) -type f -exec wc -w {} + | tail -1 | awk '{print $1}')
```

Word count is a rough proxy for tokens (multiply by 1.3 for tokens-ish). Good enough for per-condition comparison; we just need the ratios. Record as `tokens_word_count` in each result JSON.

---

## Run protocol

1. Verify Brief 13 is complete (`docs/gigo/experiments/02-opus-4-7-v0.14-assembled-vs-bare.md` exists with headline numbers).
2. Apply Fix 1 (`run-dosing-eval.sh` fork), Fix 2 (`build-variant.sh`), Fix 3 (`judge-prompt-rank5.md`), Fix 4 (token accounting). Commit each as its own commit.
3. Sanity-check each variant build: run `build-variant.sh` against both fixtures for all 5 conditions, inspect the `wc -c` + file counts. If any variant has unexpected token counts, fix the builder before running the full matrix.
4. Execute `./evals/run-dosing-eval.sh`. Results land in `evals/results/dosing-<timestamp>/`.
5. Build a rank-based scorer at `evals/score-dosing-eval.sh`. For each prompt:
   - Load all 5 condition results
   - Shuffle into Response 1-5 with a recorded mapping
   - Run the rank-5 judge
   - Apply the mapping to get per-condition ranks
   - Aggregate per prompt: Borda count (rank 1 = 5 pts, rank 5 = 1 pt) per condition per criterion
6. Aggregate across prompts per condition per domain. Report:
   - Per-condition average rank across all criteria
   - Per-condition total Borda points
   - Per-domain × condition matrix (14 cells = 2 domains × 7 criteria-avg)
   - Per-prompt-axis (A/B/C) × condition breakdown — does the sweet spot shift by prompt type?

## What the writeup needs to cover

At `docs/gigo/experiments/03-opus-4-7-context-dosing.md`:

- **Model & version:** Opus 4.7 + plugin v0.14.0-beta.
- **Condition definitions:** one sentence each + token counts (per domain).
- **The headline:** which condition ranks highest per domain, and by how much.
- **Is there a peak?** Plot (ASCII or markdown table) showing condition-rank vs condition-mass. Shape matters: monotonic / peaked / flat / U.
- **Per-axis breakdown:** does "bare wins on axis A but full wins on axis C" show up? If so, that's a dosing-by-prompt-type finding.
- **Token efficiency:** quality-per-token for each condition. Rank 1 at 100% tokens is different from rank 1 at 40% tokens.
- **Regression delta vs Brief 13:** does C3 here match Brief 13's assembled numbers? If not, investigate before publishing — the harness shouldn't have drifted between briefs.
- **Recommendation:** concrete. "Ship C2 as the default" / "Keep C3, no evidence of over-context" / "C1 wins — the team framing alone does the work, trim the rules" / "No clear winner, domain-dependent."
- **Open questions:** what Phase 3 should test. Likely candidates: different persona structures, condensed `CLAUDE.md`, subagent-only architecture where main context is bare.

## Hypotheses to state upfront in the writeup

Operator hypothesis going in: **"We might be over-contexted on Opus 4.7."** If results support it, C1 or C2 wins. If results refute it, C3 wins monotonically.

Counter-hypothesis from `project_experiment_results.md`: **"Architecture carries coherence, personas add polish."** If this holds on Opus 4.7, C4 (rules only) should beat C1 (roster only) on structural prompts — but C3 still wins overall because personas contribute polish on top.

Third-way hypothesis: **"Opus 4.7 ignores extra context it doesn't need."** If true, all conditions with ANY gigo content tie C3, and C0 (bare) is the only loser. This would mean the full context is harmless but unnecessary.

The writeup should say which hypothesis the data supports. If none cleanly, say "no clean support for any hypothesis, here's what we saw instead" — don't force a narrative.

## Out of scope

- Testing other models (Sonnet 4.6, Haiku 4.5, GPT-5, etc.) — Opus 4.7 only. Separate brief.
- Testing other persona styles (Lenses vs Characters from Brief 10) — separate axis, separate brief.
- Refreshing fixtures to v0.14-era assembly — preserve, same as Brief 13.
- Expanding prompts — same 14 prompts. If results are ambiguous, suggest a Phase 3 with more prompts rather than expanding mid-run.
- Testing just-in-time context fetching (hypothetical variant where a discovery skill pulls context on demand) — new architecture, separate brief.
- Splitting evals into their own repo — deferred per `project_eval_repo_split.md`.

## Relevant memories

- `feedback_persona_activation_cost.md` — persona defs in rules are dead weight until activated. Predicts C2 beats C3.
- `reference_hu_et_al_persona_tradeoff.md` — personas help alignment, hurt knowledge retrieval. Predicts C0/C4 might beat C1/C2/C3 on knowledge-retrieval prompts.
- `project_experiment_results.md` — architecture carries coherence, personas add polish. Predicts C4 > C1 on structural prompts.
- `feedback_eval_harness_hygiene.md` — model pin + bare glob rules. Apply to the new harness too.
- `feedback_kickoff_packet_structure.md` — the pattern this packet follows.
- `feedback_right_context_for_the_job.md` — core principle. Directly relevant: "give each agent exactly what it needs for its job, nothing more." This eval tests whether we're honoring that principle or violating it.

## Deliverables

1. `evals/run-dosing-eval.sh` + `evals/build-variant.sh` + `evals/judge-prompt-rank5.md` + `evals/score-dosing-eval.sh`, committed.
2. `evals/results/dosing-<timestamp>/` — gitignored per existing `.gitignore`. Keep it local unless operator asks otherwise.
3. Writeup at `docs/gigo/experiments/03-opus-4-7-context-dosing.md`.
4. A one-line update to memory `feedback_right_context_for_the_job.md` if the data meaningfully refines it (e.g., specific token-count guidance). Don't create a new memory unless the finding is cleanly actionable.

## Starting prompt for the new session

Paste this into a fresh Claude Code session in `/Users/eaven/projects/gigo`:

> Kickoff packet at `briefs/14-context-dosing-sweet-spot-eval.md`. Read the whole file before doing anything. Prerequisite: Brief 13 (the v0.14 + Opus 4.7 assembled-vs-bare eval) must be complete — check for `docs/gigo/experiments/02-opus-4-7-v0.14-assembled-vs-bare.md`. Your job is to sweep the context-mass axis with 5 conditions (bare / roster-only / team-no-rules / full / rules-only), score with a rank-of-5 judge, and answer: is Opus 4.7 benefiting from full gigo context, or have we over-contexted? Fork the harness — don't modify Brief 13's. Writeup lands at `docs/gigo/experiments/03-opus-4-7-context-dosing.md`. Start with `cat briefs/14-context-dosing-sweet-spot-eval.md`.
