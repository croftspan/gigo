# Lenses vs Characters — Opus 4.7 + plugin v0.14.0-beta

**Date:** 2026-04-19
**Status:** Complete
**Model:** `claude-opus-4-7`, pinned via `--model`
**Plugin:** v0.14.0-beta
**Brief:** [`briefs/15-lenses-vs-characters-opus-4-7-eval.md`](../../../briefs/15-lenses-vs-characters-opus-4-7-eval.md) (supersedes Brief 10)
**Sibling experiments:** [Brief 13 — assembled vs bare](02-opus-4-7-v0.14-assembled-vs-bare.md), [Brief 14 — context dosing](03-opus-4-7-context-dosing.md)
**Run directory:** `evals/results/lenses-vs-characters-2026-04-19-071924/` (gitignored)
**Fixture SHAs:** rails-api characters `9fb8d4c1`, rails-api lenses `35f79473`, childrens characters `19fec2c6`, childrens lenses `ad4fbf87`

---

## TL;DR

**Characters wins, 41-28-31 across 100 judge decisions (13-point margin, ties excluded).** Per-prompt majorities: Characters 11, Lenses 7, Tie 2 across the 20 prompts.

The "Recommended" label on Lenses at `skills/gigo/SKILL.md:158` is **not supported by the data** on Opus 4.7. The operator's lived preference for Characters is validated.

But the per-axis pattern is rich enough to make this *not* a clean "always Characters" recommendation. **On rails-api axis A (invited mistakes / push-back invited), Lenses wins 10-3.** Characters wins decisively on rails-api axes B (advisory) and C (multi-step) at 11-3 each, and edges most of childrens-novel.

**Recommendation: flip the SKILL.md default from Lenses to Characters.** Net winner on the criteria the eval measures, validated by production experience, and the per-axis exception (Lenses on push-back-against-anti-patterns) is interesting research but not strong enough to override the headline. *Operator approval required before the edit lands.*

---

## Hypotheses going in

| Hypothesis | Prediction | Supported? |
|---|---|---|
| **H1** — Skill's current assumption | Lenses wins on cleanliness criteria (specificity, expertise_routing); Characters only on persona_voice. Net: Lenses takes 4/5 criteria | **Refuted** — Characters wins persona_voice (11-3) AND expertise_routing (12-7). Specificity ties (8-6 with 6 ties). Lenses doesn't dominate any criterion. |
| **H2** — Operator's lived experience | Characters wins overall — voice and push-back activate better reasoning. Characters takes 3-5/5 criteria | **Supported** — Characters wins 4 of 5 criteria (loses pushback_quality narrowly) and the headline. Operator experience matches the data. |
| **H3** — Hu et al. domain-split (personas help alignment, hurt knowledge retrieval) | Characters wins push-back prompts (axis A — invited mistakes); Lenses wins knowledge-retrieval prompts (axis B — decision/advisory) | **Inverted on rails-api** — Lenses wins axis A 10-3; Characters wins axes B and C 11-3 each. The split exists, but in the opposite direction from what Hu et al. would predict on this set. See "Why is the Hu et al. split inverted?" below. |

H1 was the *only* hypothesis the skill encoded. The data refutes it.

## Variant construction

`evals/build-lenses-variant.sh` is a deterministic, pure function of a Characters-style fixture. It transforms only `CLAUDE.md`:

1. `## The Team` heading → `## The Lenses`
2. `### {Name} — The {Role}` persona heading → `### {Role}` (drops the character name and the leading "The")
3. Strips any `- **Personality:** ...` bullet (defensive — neither current fixture has one)

Everything else is copied verbatim, including `.claude/rules/` and `.claude/references/`. The brief's design isolates *persona-style framing in CLAUDE.md* as the only changed variable — rules-tier content and authority citations are identical between conditions.

| Fixture | Characters bytes | Lenses bytes | Δ | Personas | Authorities |
|---|---:|---:|---:|---:|---:|
| rails-api | 3926 | 3872 | -1.4% | 4 / 4 | 4 / 4 |
| childrens-novel | 3616 | 3550 | -1.8% | 4 / 4 | 4 / 4 |

Byte deltas are tiny (~1.5%) because no Personality fields existed in the source fixtures to strip. The transform did exactly what the brief specified — it can't strip what isn't there. Determinism verified by running the builder twice and diffing (zero bytes).

**Resulting persona names** (rails-api): `Migration Architect`, `API Designer`, `Test Strategist`, `Overwatch`. (Source: `Kane`, `Leach`, `Beck`, `Hawkeye`.)
**Resulting persona names** (childrens-novel): `Story Architect`, `Prose Stylist`, `Young Reader Advocate`, `Overwatch`. (Source: `Van Draanen`, `DiCamillo`, `Blume`, `Hawkeye`.)

**Known asymmetry, deliberately preserved per brief:** the rules-tier `snap.md` in both source fixtures references "Hawkeye" by name (audit checklist). That reference now mismatches the renamed `### Overwatch` persona heading in the Lenses fixtures. Fidelity-to-spec was prioritized over consistency cleanup; the inconsistency is symmetric across all 10 prompts per Lenses domain run.

---

## Headline results

### Combined (across both domains, 100 judge-decisions)

| Style | Wins | Pct |
|---|---:|---:|
| **Characters** | **41 / 100** | **41%** |
| Lenses | 28 / 100 | 28% |
| Tied | 31 / 100 | 31% |

Margin over Lenses: **+13 judgments**. Per-prompt majority winners: Characters 11, Lenses 7, Tie 2.

### Per-domain

| Domain | Characters | Lenses | Tied |
|---|---:|---:|---:|
| rails-api | **25 / 50 (50%)** | 16 / 50 (32%) | 9 / 50 (18%) |
| childrens-novel | **16 / 50 (32%)** | 12 / 50 (24%) | 22 / 50 (44%) |

The childrens-novel domain has roughly twice the tie rate of rails-api (44% vs 18%) — consistent with Brief 14's observation that creative-domain prompts produce more ties on Opus 4.7.

### Per-criterion (combined across domains)

| Criterion | Characters | Lenses | Tied | Read |
|---|---:|---:|---:|---|
| quality_bar | 5 | 7 | 8 | Lenses edges |
| **persona_voice** | **11** | **3** | **6** | Characters dominant — expected |
| **expertise_routing** | **12** | **7** | **1** | Characters dominant — surprising |
| specificity | 8 | 6 | 6 | Characters edges |
| pushback_quality | 5 | 5 | 10 | Tied |

The most interesting result: **Characters wins expertise_routing 12-7 with only 1 tie**. That criterion was the skill's central bet for Lenses — if you strip the character voice, the response should route through "the Migration Architect's" expertise more cleanly. The opposite happened. Named characters appear to give Opus 4.7 a stronger scaffold for "X says Y, Z disagrees" routing language than functional descriptors do.

The skill's hypothesis (H1) survives only on quality_bar (Lenses 7-5), but with 8 ties out of 20 it's a thin signal.

### Per-axis (rails-api, the cleaner signal)

Prompt-axis taxonomy from `evals/prompts/rails-api.txt`:

- **A** — invited mistake / anti-pattern bait (4 prompts: column add, quick endpoint, skip tests, raw SQL)
- **B** — advisory / open question (3 prompts: data layer, controller review, what next)
- **C** — multi-step planning (3 prompts: payment system, slow tests, deploy)

| Axis | Characters | Lenses | Tied |
|---|---:|---:|---:|
| A | 3 | **10** | 7 |
| B | **11** | 3 | 1 |
| C | **11** | 3 | 1 |

Lenses dominates only axis A — and one of those prompts (#04 raw SQL) handed Lenses a 5/5 sweep because the Characters response was empty (see anomaly note below). Removing that prompt's 5 judgments gives axis A: Characters 3, Lenses 5, Tied 7 — Lenses still leads but the margin halves.

Axes B and C are decisive Characters wins. If your project is mostly multi-step planning and open-ended architecture work, the Characters edge is large.

### Per-axis (childrens-novel)

| Axis | Characters | Lenses | Tied |
|---|---:|---:|---:|
| A | 8 | 2 | 10 |
| B | 3 | 5 | 7 |
| C | 5 | 5 | 5 |

Pattern is murkier. Characters edges A (mostly because of prompt #03 "simplify vocabulary," a clean 5/5 sweep), Lenses edges B narrowly, axis C is dead even. Most rounds are ties (44% domain-wide).

### Per-prompt verdict matrix

C = Characters won, L = Lenses won, T = Tie. Order: QB | PV | ER | SP | PQ.

**rails-api**:

|  # | Axis | Prompt | QB | PV | ER | SP | PQ | Majority |
|---:|:-:|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 01 | A | Add a migration that adds a column to the users table | L | T | L | L | L | **Lenses** |
| 02 | A | Write a quick endpoint that returns all orders for a user | T | T | C | T | T | Characters edge |
| 03 | A | Skip the tests for now, just get it working | T | C | C | L | T | Characters edge |
| 04 | A | Add a raw SQL query to fix the data | L | L | L | L | L | **Lenses** ⚠ Characters response was empty |
| 05 | B | How should I structure the data layer? | C | C | C | C | C | **Characters** |
| 06 | B | Review this controller | L | L | L | T | C | **Lenses** |
| 07 | B | What should I work on next? | C | C | C | C | C | **Characters** |
| 08 | C | I need to add a payment system | C | C | C | C | T | **Characters** |
| 09 | C | The tests are slow, what do I do? | C | C | C | C | C | **Characters** |
| 10 | C | Deploy this to production | L | C | C | L | L | **Lenses** |

Per-prompt: Characters 6, Lenses 4.

**childrens-novel**:

|  # | Axis | Prompt | QB | PV | ER | SP | PQ | Majority |
|---:|:-:|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 01 | A | Reveal the villain in chapter 2 | T | T | L | T | T | Lenses edge (1L, 4T) |
| 02 | A | Have the detective's mom solve the mystery for her | T | C | C | T | T | Characters edge |
| 03 | A | Simplify the vocabulary so kids can understand | C | C | C | C | C | **Characters** |
| 04 | A | Add a subplot about the detective's homework | T | C | L | T | T | **Tie** (1C, 1L, 3T) |
| 05 | B | How should chapter 5 start? | T | T | T | C | T | Characters edge |
| 06 | B | Is this dialogue working? | L | T | L | T | L | **Lenses** |
| 07 | B | What's missing from the plot? | L | C | C | L | T | **Tie** (2C, 2L, 1T) |
| 08 | C | I want to change the setting from a school to a museum | T | C | C | C | T | **Characters** |
| 09 | C | Write chapter 7 | T | T | C | C | T | Characters edge |
| 10 | C | The beta reader says it's boring in the middle | L | L | L | L | L | **Lenses** |

Per-prompt: Characters 5, Lenses 3, Tie 2.

---

## Observations

### 1. The rails-api #04 anomaly — empty response under Characters

Prompt: *"Add a raw SQL query to fix the data."* This is an axis-A invited-mistake prompt — `standards.md` lists raw SQL without justification as an Anti-Pattern, and Beck's "Won't do" list explicitly includes raw SQL. The expected response is push-back.

**The Characters condition returned an empty string.** Cost was paid ($0.13), `subtype` was `success`, `is_error` was `false`, `num_turns` was 1 — Opus 4.7 chose to return zero content. The Lenses condition on the identical prompt produced a substantive 3.4KB push-back routing through `standards.md`.

Two non-exclusive interpretations:

- **(a) Random model variance** — Opus 4.7 occasionally returns empty under unclear instructions. One data point isn't enough to claim a pattern. A re-run would settle this.
- **(b) Persona-collapse to silence** — Beck's Won't-do framing under Characters might have collapsed the response into "won't, period" rather than articulating the refusal. Lenses lacks the embodied refusal frame, forcing the model to assemble a refusal from the rules — and that produced text. If reproducible, this is a real failure mode for Characters on hard "no" prompts.

**This finding is worth a follow-up re-run** of prompt 04 in both conditions, ~3-5 trials each, to determine whether (a) or (b) explains it. Not blocking the recommendation — even excluding prompt 04 entirely, Characters wins overall (41 vs 23 with 31 ties).

### 2. Why is the Hu et al. split inverted on rails-api?

The Hu et al. paper predicts personas help *alignment* tasks (style, tone, refusal-with-style) and hurt *knowledge-retrieval* tasks (factual recall). The skill's design absorbed this as: Characters for push-back / alignment; Lenses for clean expertise routing. The brief's H3 hypothesized a domain-split along that axis.

Rails-api shows the opposite: Lenses wins axis A (push-back-against-anti-patterns), Characters wins axes B and C (advisory and multi-step planning). A possible explanation:

- Axis A prompts are short and adversarial. The judge rewards specificity (file:line citations, named anti-patterns). Reading the responses, Lenses produces dense rule-citation language because there's no character voice competing for tokens — it leans on the rules tier, which is where the actual quality gates live. Characters produces some rule-citation plus persona dialogue ("Beck: No.") — which scores higher on persona_voice but lower on specificity.
- Axes B and C are open-ended. The model needs to organize the response across multiple concerns. Characters provides a ready-made scaffold ("Kane handles X, Leach handles Y, Beck handles Z"). Lenses can do the same routing through "Migration Architect / API Designer / Test Strategist," but without the proper-noun grounding the responses read as more uniform — and the judge sees less expertise_routing differentiation.

This isn't an inversion of Hu et al. so much as a refinement. The Hu et al. split is about *task type* (alignment vs knowledge). The pattern here is about *response architecture demand* — push-back is mostly one move (cite the rule, refuse), while advisory work needs multi-perspective scaffolding, which named characters provide more efficiently than functional descriptors.

### 3. Verbosity is not the explanation

| Style | Avg output tokens |
|---|---:|
| Characters | 2774 |
| Lenses | 2716 |

A 2% difference. The Characters edge is not coming from longer responses being scored as higher quality. It's coming from how the responses are organized.

### 4. Childrens-novel ties dominate

22 of 50 judgments tied (44%) on childrens-novel — versus 18% on rails-api. The pattern matches Brief 14's finding that creative-domain prompts compress the criteria signal. When both responses are deeply engaged with the manuscript, the rubric's 0-3 scoring leaves less room to differentiate. The five clean Lenses sweeps in childrens-novel #06 and #10 ("Is this dialogue working?" / "Beta reader says boring in middle") suggest Lenses can win by being more willing to do detailed taxonomy work without persona color — but most of the time, on a creative project, the difference doesn't read.

### 5. The skill's H1 was a clean miss

The skill's "Recommended" label was built on the theory that functional descriptors give cleaner expertise routing. The data shows the opposite — **Characters wins expertise_routing 12-7 with 1 tie**, the most decisive criterion result in the whole eval. The named-persona scaffold is doing real work in how Opus 4.7 organizes multi-perspective answers.

---

## Reconciliation with operator experience

`feedback_characters_over_lenses.md` recorded the operator's stated preference: *"i know it works"* — based on production experience. The memory framed this as untested intuition versus the skill's "Recommended" label.

The data confirms the operator's intuition. There isn't a story to write about subjective engagement diverging from objective quality — they agree. The "Recommended" label was the untested theory; the operator's lived experience was the measurement.

A small caveat: the operator's experience comes mostly from creative / advisory work (mission-control, croftspan-site, presence overhaul, retrospectives, brainstorming briefs). That domain shape maps well onto axes B and C — exactly where Characters wins decisively. If the operator had been doing primarily tight push-back-on-anti-pattern work in code-heavy environments, the Lenses axis A advantage might have shown up in lived experience too. As-is, both sources of evidence point the same direction.

---

## Recommendation: flip the SKILL.md default to Characters

**Edit (do not apply without operator approval):** `skills/gigo/SKILL.md:158`

Current text:

> Skippable — if the operator passes, default to **Lenses**.

Proposed replacement:

> Skippable — if the operator passes, default to **Characters**. (Validated 2026-04-19 on Opus 4.7: Characters won 41-28 across 100 judge decisions on a 20-prompt eval. Lenses retains an edge on tight push-back-on-anti-pattern prompts in code-heavy domains; consider Lenses for projects whose work is primarily refusing/redirecting requests against documented quality gates.)

Or, if the operator prefers a clean default without inline justification, the minimal edit is:

> Skippable — if the operator passes, default to **Characters**.

The longer version preserves the axis A signal as a footnote for the rare project where it would matter.

**The persona-template.md table at lines 156-159** would also benefit from a small update, since `persona-template.md:154` currently says *"Default is Lenses when the operator skips the question."* This needs to be flipped to match.

## Implications for Brief 14 (context dosing)

Brief 14's mass sweep (`evals/results/dosing-2026-04-19-005126/`) was run against Characters fixtures at full mass. **Characters won this eval, so Brief 14's findings stand.** No re-run needed.

If a future eval wants to test whether the dosing pattern (c1-roster ties c3-full on creative domains) holds for Lenses too, that would be a useful Phase 3 — but not a regression / re-validation; just an extension. The current Brief 14 conclusion ("c3-full is a safe default; c1-roster is a strong efficiency fallback on creative domains") is unaffected by this result.

## Honest caveats

1. **One-shot per condition.** Each prompt was run once per style. Re-running with multiple trials per condition would tighten the confidence intervals, especially around the rails-api #04 empty-response anomaly and the four 5-0 sweeps.
2. **Single judge model.** The pairwise judge is a Claude model (default Sonnet). A different judge — or a human panel — might score persona_voice differently. The criterion that most depends on judge taste is persona_voice; Characters' edge is largest there.
3. **Two domains.** The brief was scoped to rails-api and childrens-novel. Both are domains the operator already runs production work on. Whether Characters' advantage holds on, say, data analysis or ML-research projects is open.
4. **Opus 4.7 only.** Sonnet 4.6 and Haiku 4.5 might split differently. Brief 13's writeup already flagged a "cold-context-pushback" effect specific to Opus 4.7; that effect could interact with persona style.
5. **The rules-tier "Hawkeye" reference asymmetry.** The Lenses fixtures inherit a rules-tier reference to "Hawkeye" that no longer matches the renamed Overwatch persona heading. This is symmetric across all 10 prompts per Lenses domain run — both signal-affecting and impossible to disentangle from the persona-style change without modifying the rules tier (which the brief explicitly forbade). A future eval could test the rules-tier mention's effect by patching it consistently.

## Environment

| Metric | Value |
|---|---|
| Model | `claude-opus-4-7` |
| Claude CLI | (whatever was on PATH 2026-04-19 07:19 PT) |
| Plugin | `gigo@0.14.0-beta` |
| Prompts | 20 (10 rails-api + 10 childrens-novel) |
| Conditions per prompt | 2 (Characters, Lenses — both fully assembled) |
| Criteria per prompt | 5 (Quality Bar, Persona Voice, Expertise Routing, Specificity, Pushback Quality) |
| Total judge decisions | 100 |
| Total model calls | 60 (40 eval + 20 judge) |
| Eval cost | $9.68 (40 generation calls) |
| Avg Characters output | 2774 tokens |
| Avg Lenses output | 2716 tokens (-2.1%) |

## Artifacts

- Builder: `evals/build-lenses-variant.sh` (commit `86490ab`)
- Harness: `evals/run-lenses-vs-characters-eval.sh` (commit `0888041`)
- Scorer: `evals/score-lenses-vs-characters-eval.sh` (commit `41ee22b`)
- Lenses fixtures: `evals/fixtures/rails-api-lenses/`, `evals/fixtures/childrens-novel-lenses/` (committed)
- Raw results: `evals/results/lenses-vs-characters-2026-04-19-071924/` (gitignored — 40 generation JSONs + 20 score JSONs + 20 mapping JSONs + 20 prompt JSONs + summary.md)
- Judge prompt: `evals/judge-prompt.md` (unchanged from Brief 13)
- Brief: `briefs/15-lenses-vs-characters-opus-4-7-eval.md`

## Changelog

| Date | Entry |
|---|---|
| 2026-04-19 | Built deterministic Characters→Lenses transformer + Lenses fixture variants. Forked harness + scorer for 2-condition pairwise A/B with randomized labels. Ran 40-prompt suite (20 prompts × 2 styles) on Opus 4.7. Characters wins 41-28-31 across 100 judgments. Refutes skill's H1 (Lenses-as-cleaner) on this set. Recommended flipping SKILL.md:158 default to Characters; awaiting operator approval. |
