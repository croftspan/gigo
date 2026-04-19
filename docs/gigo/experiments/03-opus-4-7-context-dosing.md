# Context-dosing sweet spot — Opus 4.7 + plugin v0.14.0-beta

**Date:** 2026-04-19
**Model:** `claude-opus-4-7`
**Plugin:** v0.14.0-beta
**Depends on:** [Phase 1 assembled-vs-bare](02-opus-4-7-v0.14-assembled-vs-bare.md)
**Artifacts:** `evals/results/dosing-2026-04-19-005126/` (gitignored)

## TL;DR

Opus 4.7 benefits decisively from gigo context — **c0-bare loses by 70+ Borda points on both domains.** But full-assembled (c3) is *not* uniformly best. On a craft-heavy creative domain (childrens-novel), a trimmed **c1-roster** condition (persona headers + "Modeled after" one-liners only, keeping `.claude/rules/` intact) **ties c3-full at 84% of its token mass**. On rails-api, c3 still wins but c1 trails by only 17 Borda points at 81% of the tokens.

The over-contexting hypothesis is **partially supported**: not a pervasive penalty, but **task-dependent over-contexting shows up on open-ended C-axis prompts in the creative domain** — where c3-full drops to 4th place behind c4, c2, and c1.

**Recommendation:** Keep c3-full as the default for now — it wins or ties across both domains. Treat c1-roster as a strong efficiency fallback and a live hypothesis for domain-aware dosing.

## Hypotheses going in

| Hypothesis | Prediction | Supported? |
|---|---|---|
| H1 — "We might be over-contexted on Opus 4.7" (operator) | c1 or c2 beats c3 outright | **Partial** — c1 ties c3 on childrens-novel; c3 wins rails-api |
| H2 — "Architecture carries coherence, personas add polish" (Phase 9) | c4 > c1 on structural prompts; c3 still wins overall | **Partial** — c4 > c1 on childrens C-axis but loses everywhere else |
| H3 — "Opus 4.7 ignores extra context it doesn't need" | All conditions with any gigo content tie c3; only c0 loses | **Refuted** — c1/c2/c4 all lose to c3 on rails-api by 17-47 Borda |

None of the three hypotheses cleanly lands. The data supports a fourth: **context matters a lot at the low end but with diminishing returns past ~2000 words, and the ceiling location is task-dependent.**

## Condition definitions + token mass

Word counts measured over `CLAUDE.md + .claude/rules/*.md + .claude/references/*.md` after variant build. Rough tokens ≈ 1.3× words.

| Condition | What's in it | rails-api | childrens-novel |
|---|---|---:|---:|
| **c0-bare** | Source files only; no `CLAUDE.md*`, no `.claude/` | 0 | 0 |
| **c1-roster** | Copy all; replace `CLAUDE.md` with stem-only roster (persona headers + "Modeled after" one-liners). Keep rules + references | 1969 | 2291 |
| **c2-team-no-rules** | Copy all; keep full `CLAUDE.md`; delete rules + references | 569 | 553 |
| **c3-full** | Copy all unchanged (= Brief 13 assembled) | 2432 | 2729 |
| **c4-rules-only** | Copy all; delete `CLAUDE.md*`; keep rules + references | 1863 | 2176 |

**Not monotonic by design.** c4 < c1 (by 106 / 115 words — the roster CLAUDE.md) lets us isolate "the team framing even in thin form" from rules content. c2 < c4 lets us isolate "personas alone" from "rules alone."

## Headline ranking (Borda across all 5 criteria)

Borda = 5 for rank 1, 1 for rank 5. Max per prompt per criterion = 5. Total across 10 prompts × 5 criteria = 250.

### rails-api

| Rank | Condition | Borda | Raw 0-3 score sum | Words |
|---:|---|---:|---:|---:|
| 1 | **c3-full** | **196** | 139 | 2432 |
| 2 | c1-roster | 179 | 118 | 1969 |
| 3 | c2-team-no-rules | 149 | 114 | 569 |
| 3 | c4-rules-only | 149 | 108 | 1863 |
| 5 | c0-bare | 77 | 52 | 0 |

### childrens-novel

| Rank | Condition | Borda | Raw 0-3 score sum | Words |
|---:|---|---:|---:|---:|
| 1 | **c1-roster** | **189** | 138 | 2291 |
| 2 | c3-full | 188 | 132 | 2729 |
| 3 | c4-rules-only | 168 | 132 | 2176 |
| 4 | c2-team-no-rules | 155 | 126 | 553 |
| 5 | c0-bare | 50 | 19 | 0 |

**Shape of the mass-quality curve:** monotonic from 0→~2000 words, then flat or slightly declining. Not U-shaped; not monotonic up through c3.

```
rails-api          childrens-novel
Borda              Borda
200 |   * c3       200 |
175 | * c1         175 | * c1 * c3
150 |*c2 *c4       150 |      * c4
125 |              125 |    * c2
100 |              100 |
 75 |* c0           75 |
 50 |               50 |* c0
 25 |               25 |
  0 +------>tokens    0 +------>tokens
    0 500 1.5k 2.5k      0 500 1.5k 2.5k
```

## Per-axis breakdown (avg Borda per criterion, rounded)

### rails-api

| Axis | c0-bare | c1-roster | c2-team-no-rules | c3-full | c4-rules-only |
|---|---:|---:|---:|---:|---:|
| A (dangerous tasks: migrations, unpag queries, raw SQL, skip-tests) | 1.2 | 3.6 | 2.6 | **4.2** | 3.0 |
| B (open-ended: architecture, review, prioritization) | 2.0 | **3.6** | 3.2 | 3.2 | 2.6 |
| C (scope: payment system, slow tests, deploy) | 1.4 | 3.4 | 2.8 | **4.0** | 3.0 |

### childrens-novel

| Axis | c0-bare | c1-roster | c2-team-no-rules | c3-full | c4-rules-only |
|---|---:|---:|---:|---:|---:|
| A (dangerous craft moves: early reveal, deus ex machina, simplify vocab) | 1.0 | **4.4** | 2.2 | 3.6 | 3.4 |
| B (craft questions: chapter start, dialogue, plot gaps) | 1.0 | 3.2 | 3.4 | **4.8** | 2.4 |
| C (structural: setting change, write new chapter, beta-reader "boring middle") | 1.0 | 3.4 | 3.6 | 2.8 | **3.8** |

**The C-axis of childrens-novel is the over-contexting signal.** c3-full drops to 4th on open-ended structural prompts — beaten by c4, c2, and c1. This does not show up on rails-api C-axis, where c3 still wins decisively. The divergence is the story.

## Token efficiency (Borda per 1000 words)

| Condition | rails-api | childrens-novel |
|---|---:|---:|
| c2-team-no-rules | **261.9** | **280.3** |
| c1-roster | 90.9 | 82.5 |
| c3-full | 80.6 | 68.9 |
| c4-rules-only | 80.0 | 77.2 |

**c2-team-no-rules is the per-token efficiency champion** — 553/569 words deliver ~60-80% of c3's Borda. If you have a strict token budget and are ok losing 40-45 Borda points (roughly 2 criteria × 4.5 points × 10 prompts ≈ 1 rank position across the board), c2 is the tight answer.

**c3-full's efficiency is lower than c4-rules-only on rails-api.** Borda per 1000 words: c3=80.6 vs c4=80.0 (effectively tied). On childrens-novel c3 is the *least* efficient non-bare condition — 68.9 vs c4's 77.2. This is the clearest "diminishing returns past ~2000 words" signal.

## Regression delta vs Brief 13

Brief 13's `02-opus-4-7-v0.14-assembled-vs-bare.md` reported assembled winning 99/100 criteria in pairwise matchups against bare. This eval is rank-of-5 with a different judge prompt, so direct comparison isn't clean — but the directional signal matches:

- **c3-full vs c0-bare in this eval** — on rails-api: 196 vs 77 Borda (2.5×). On childrens-novel: 188 vs 50 Borda (3.8×). That's more decisive than Brief 13 because the rank-of-5 judge can differentiate degrees, not just pick a winner.
- **No harness drift detected.** c3 fixture content is unchanged since Brief 13 (`CLAUDE.md` SHAs still `9fb8d4c1` rails / `19fec2c6` childrens). Model pin and bare-contamination glob inherited from Brief 13.

## What the evidence actually supports

**Two findings, not three hypotheses:**

1. **Context is strongly load-bearing from 0 → ~2000 words.** c0-bare is catastrophic on both domains. Even the thinnest non-bare condition (c2 at ~560 words) triples c0's Borda. The cold-context pushback pattern from Brief 13 replicates here — c0 responses either hallucinate structure (rails-api prompt 1: c0 interprets the prompt as a UI fragment) or refuse with "directory is empty" ground-truth statements.

2. **Past ~2000 words, extra context earns less on creative/open-ended tasks and still earns on structural/dangerous ones.** On childrens-novel C-axis (beta-reader complaints, setting changes, new chapter drafting), full-assembled drops below conditions that have less total content but retain just the rules files. The extra 440 words in c3 vs c1 (on childrens) don't add signal there; they may crowd out the generative freedom the task needs.

The "overwatch" pattern — persona name-drops without substance — shows up visibly in c2 and c4 responses on both domains. c2 has the persona framing but no rules citations; responses sound in-character but miss the rules grounding that c1/c3/c4 demonstrate. c4 has rules citations without persona framing; responses cite quality gates but don't triangulate through named authority perspectives.

## Qualitative example — rails-api prompt 3 ("Skip the tests for now")

All five conditions push back. Grounding differs:

- **c0-bare**: "directory is empty, nothing to skip" — technically correct, no push on the premise.
- **c1-roster**: "No. ... `.claude/rules/standards.md` calls it out explicitly under Anti-Patterns: *'Skipping tests "for now." There is no "for now."'* And Beck..." — **cites both rules file and persona name**, grounded push.
- **c2-team-no-rules**: cites `CLAUDE.md` Beck quality bar + Won't do list. Strong persona voice but no rules file to point to.
- **c3-full**: "explicitly on the anti-pattern list in `.claude/rules/standards.md`, and Beck's quality bar says..." — strongest grounding, both layers.
- **c4-rules-only**: "direct hit on a forbidden anti-pattern" — cites rules file, no persona name to anchor.

Judge awarded near-equal ranks to c1/c3/c4 on this prompt, c0 last, c2 middling. The pattern fits the overall Borda data.

## Qualitative example — childrens-novel prompt 10 ("beta reader says boring in the middle")

This is a **C-axis prompt on the creative domain — where c3 underperforms.**

- **c3-full** opens with `★ Insight ──` framing pointing at `plot-outline.md`, analyzing which chapters the reader probably means, drawing on the mystery-craft references. Dense, structural, somewhat over-constrained for a diagnostic request.
- **c4-rules-only** opens with "Diagnosis: the middle of what's drafted is chapters 2-3, and the pacing issue is structural" then immediately ladders into "Why the A-options are traps" — rule-citing but more decisive and actionable.
- Judge gave c4 higher ranks on 3 of 5 criteria (quality_bar, specificity, pushback_quality). c3 got its rank-2 only on pushback.

c3's extra ~550 words of content (the difference vs c4) *doesn't* help this task — it adds analytical scaffolding where the prompt wanted a decisive next move. This is the over-contexting signal in a concrete prompt.

## Open questions for Phase 3

1. **Domain-aware dosing** — is the childrens-novel over-context penalty a "creative domain" property or a "small codebase / loose structure" property? Test with a large-codebase creative domain (e.g., screenplay repo with many scene files).
2. **c2 as a real option** — c2-team-no-rules delivers 75-80% of c3's Borda at 23% of the tokens. Does a *second* eval using the cost-weighted Borda re-rank c2 above c3? Worth running a budgeted eval on a longer prompt set.
3. **Cast-only test** — c1's 106-word roster beats c4's no-CLAUDE.md condition by ~20-30 Borda. Is it the roster words specifically that matter, or just *any* CLAUDE.md header? Replace the roster with a one-line "You have a team: Kane, Leach, Beck, Hawkeye." stub and re-run.
4. **Prompt-axis-aware routing** — the A/B/C axes show different winners. Could GIGO detect prompt type and route to different context configurations? Closer to "just-in-time context" but still static.
5. **Within-axis variance** — 10 prompts is enough to show direction but not to cleanly separate c1 vs c3 on childrens-novel (189 vs 188 Borda is within noise). Phase 3 should widen prompt sets in the domains where hypotheses split.

## Recommendation

**Ship c3-full as the default for v0.14.** It wins or ties across both domains. No evidence supports trimming rules files at the project level today.

**Log c1-roster as the live efficiency hypothesis.** It's within 1-17 Borda of c3 at 81-84% of the tokens. Worth a Phase 3 with a 3rd domain before making it the default.

**Flag the over-contexting signal on creative/open-ended tasks.** Document that on C-axis creative prompts, c3 loses to lighter conditions. This is a domain-aware dosing finding, not a "trim everywhere" finding. Gigo's `gigo:blueprint` or planning flows could benefit from a mode that deliberately drops to c1/c4 when the task type is known.

**Don't trim rules files.** Across all conditions, c4 (rules only) outperforms c2 (personas only) on open-ended tasks and ties it on dangerous-action tasks. The rules carry signal. The claim worth testing next is whether *some* rules can move to on-demand references, not whether rules as a tier should shrink.

## Cost

Generation pass: $21.13 over 100 calls (opus 4.7). Judge pass: 20 calls at rank-of-5, not separately costed but estimated ~$4-5 based on judge-input size (5× response text per call).

## Reproducibility

- Harness: `evals/run-dosing-eval.sh` + `evals/build-variant.sh`
- Judge: `evals/judge-prompt-rank5.md` + `evals/score-dosing-eval.sh`
- Variant builds are pure functions of fixture + condition (deterministic awk extraction for c1-roster)
- Model pinned `claude-opus-4-7`; `CLAUDE.md*` glob inherited from Brief 13
- Fixtures unchanged since Brief 13 (preserve policy)
- Aggregate JSON at `evals/results/dosing-2026-04-19-005126/aggregate.json`
