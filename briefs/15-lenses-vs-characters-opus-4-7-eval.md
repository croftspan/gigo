# Kickoff: Lenses vs Characters on Opus 4.7 (supersedes Brief 10)

**Date:** 2026-04-19
**Supersedes:** `briefs/10-lenses-vs-characters-eval.md` (original scope, never executed — this packet folds it forward to v0.14 + Opus 4.7 and makes it runnable).
**Relationship to Briefs 13 & 14:** Sibling, not dependent. Can run before, after, or in parallel with Brief 14. See "Ordering" below — there's a case for running this FIRST.
**This session's job:** Settle whether GIGO's "Recommended" label on Lenses holds up on Opus 4.7, or whether Characters — the operator's actual production default — wins. Two conditions, pairwise judging, headline recommendation that can change the `/gigo:gigo` default.

---

## The question

`skills/gigo/SKILL.md:155-158` presents two persona styles at assembly time:

- **Characters** — named personas (Sage, Forge, Mirror) with personality, voice, opinions, push-back
- **Lenses** — functional descriptors (Database Architecture Lens, Schema Architecture Lens) with the same expertise but no character voice

Current skill behavior: *"if the operator passes, default to **Lenses**."* That "Recommended" posture is untested theory. The operator has shipped production work on Characters consistently — memory `feedback_characters_over_lenses.md` — and has never chosen Lenses in practice.

The outcome of this eval is one of:

- **Characters wins** — flip the skill's "Recommended" label to Characters. The operator's lived experience was right.
- **Lenses wins** — the theory was right. Keep the label, but investigate why the operator's experience diverges (domain? complexity? prompt type?).
- **Tie / domain-split** — neither dominates. Update the skill to offer both without a "Recommended" label, or surface the domain-specific guidance ("Characters for X, Lenses for Y").

## Ordering — run this BEFORE Brief 14 if you can

Persona style is a confounder for Brief 14's context-dosing sweep. Brief 14's five conditions (C0-C4) are all built from the current Characters fixtures. If Lenses substantially outperforms Characters on Opus 4.7, Brief 14's mass-axis findings are specifically for Characters and might not generalize.

Recommended ordering:

1. **Brief 13** (assembled vs bare) — sets the 2-condition baseline.
2. **Brief 15 (this brief)** — picks the winning persona style at full mass (C3 equivalent).
3. **Brief 14** (context dosing) — runs the mass sweep using the winning style from Brief 15.

If time-boxed: run Brief 14 and Brief 15 in parallel sessions. Brief 14 gets a caveat in its writeup; Brief 15 stands alone.

If Brief 14 is already complete when this runs: note in the writeup whether Brief 14's C3 (full assembled, Characters) was competitive; if Lenses wins here, flag Brief 14 for a re-run with Lenses fixtures in a Phase 3.

## Context you need (read in this order)

1. `briefs/10-lenses-vs-characters-eval.md` — original scope from 2026-04-14. This packet is the executable version.
2. `briefs/13-v0.14-opus-4-7-eval.md` — same harness base, same fixtures, same model pin, same bare-contamination glob. Re-use Brief 13's pre-flight fixes wholesale.
3. `skills/gigo/SKILL.md` — lines 155-200 present the two styles to the operator at assembly time. Read how each style is described so your Lenses variant matches what `/gigo:gigo` would actually produce.
4. `skills/gigo/references/persona-template.md` — the template that controls persona structure per style. Your Lenses variant must match this template, not be hand-rolled.
5. `evals/fixtures/rails-api/CLAUDE.md` + `evals/fixtures/childrens-novel/CLAUDE.md` — the source-of-truth Characters `CLAUDE.md` for each domain. Build the Lenses variants as transformations of these, not from scratch.
6. `evals/judge-prompt.md` — pairwise judge with 5 criteria. Works as-is for a 2-condition eval; no adaptation needed.
7. Memory `feedback_characters_over_lenses.md` — operator's stated preference + "Recommended" label tension.
8. Memory `reference_hu_et_al_persona_tradeoff.md` — authority reference: personas help alignment but hurt knowledge retrieval. Predicts Lenses might win on knowledge-heavy prompts and Characters on push-back prompts.

## What's new since Brief 10

Brief 10 was written 2026-04-14, 5 days ago. Between then and now:
- **v0.13.0-beta** shipped two-gate context7 research pipeline.
- **v0.14.0-beta** shipped pipeline-wide mission-control integration.
- The `/gigo:gigo` skill itself wasn't substantially changed in either release — persona-style offering at `SKILL.md:155-158` is the same. So Brief 10's core scope (build two variants, same fixtures, same prompts, score) is unchanged. This packet updates the model target (Opus 4.7) and the eval infrastructure (Brief 13's pre-flight fixes).

---

## REQUIRED pre-flight fixes

### Fix 1 — Inherit Brief 13's harness fixes

Brief 13 produced a `run-eval.sh` with `--model claude-opus-4-7` pinned and the `CLAUDE.md*` glob for bare-contamination. Both are load-bearing here too.

**Verify before starting:**
- `grep -n "claude-opus-4-7" evals/run-eval.sh` — should return at least 2 matches (bare + assembled run lines).
- `grep -n "CLAUDE.md\*\|CLAUDE\.md\*" evals/run-eval.sh` OR verify the exclusion is a `case "$fname" in CLAUDE.md*)` pattern.

If either is missing, Brief 13 didn't complete cleanly — go back and finish Brief 13 first.

### Fix 2 — Build the Lenses variant fixtures

For each existing fixture, produce a Lenses-style `CLAUDE.md` that preserves everything except the persona-style-specific content. Keep these things:
- Same number of personas
- Same expertise domains per persona
- Same "Modeled after:" authority citations (the authorities matter for grounding; they're not a style choice)
- Same quality bars
- Same "Won't do" lists
- Same Autonomy Model section
- Same Quick Reference section
- Same `.claude/rules/` and `.claude/references/` directories (unmodified)

Change ONLY these:
- **Names** — replace character names (Sage, Forge, Mirror, Scribe, The Voice, Conductor, The Artisan, The Narrator, The Signal, The Overwatch) with functional descriptors matching `persona-template.md` Lenses conventions. E.g., "Sage — The Context Architect" → "Context Architecture Lens". "Forge — The Skill Engineer" → "Skill Engineering Lens".
- **Voice** — strip any personality language. No "push back," no "opinions," no "speaks up" wording. The Lenses template treats personas as silent filters, not characters.
- **Personality field** — if any persona has a Personality field (only in lean tier per `persona-template.md`), remove it.
- **Section header** — rename `## The Team` to `## The Lenses` to match the Lenses-style output the skill would actually produce.

**Deterministic builder:** create `evals/build-lenses-variant.sh` as a pure function of the source Characters fixture. Pattern:

```bash
#!/usr/bin/env bash
# Usage: build-lenses-variant.sh <source-characters-fixture-dir> <dest-lenses-fixture-dir>
# Produces a Lenses-style variant from a Characters-style source.
# Exits non-zero if the source doesn't have the expected Characters structure.
```

Verify the transformation is reproducible: run it twice, diff the outputs, should be zero bytes.

Place the output fixtures at `evals/fixtures/rails-api-lenses/` and `evals/fixtures/childrens-novel-lenses/`. Do NOT modify the original Characters fixtures.

**Sanity check before running:**
- `wc -c evals/fixtures/rails-api/CLAUDE.md evals/fixtures/rails-api-lenses/CLAUDE.md` — Lenses should be slightly smaller (no character names are usually shorter, no personality field) but within ~85-95% of Characters' bytes. If it's under 50%, the builder stripped too much.
- `grep -c "Modeled after" evals/fixtures/rails-api-lenses/CLAUDE.md` — should match the Characters count (authorities preserved).
- `grep -iE "push back|opinion|speaks up|voice" evals/fixtures/rails-api-lenses/CLAUDE.md` — should return zero matches (personality language stripped).

### Fix 3 — Fork the harness as `run-lenses-vs-characters-eval.sh`

Do NOT modify `run-eval.sh` in place. Copy to `evals/run-lenses-vs-characters-eval.sh` with two changes:

- Condition names: `characters` and `lenses` instead of `bare` and `assembled`.
- Assembled dir sources from the Characters fixture; Lenses dir sources from the Lenses fixture. Neither condition is "bare" — both have full assembly.
- Output file names: `${PADDED}-characters.json` and `${PADDED}-lenses.json`.

### Fix 4 — Judge A/B label randomization

The existing judge prompt (`evals/judge-prompt.md`) labels responses as A and B. To prevent position bias from the judge:

- For each prompt, randomize which condition gets labeled A vs B. Log the mapping to `$DOMAIN_RESULTS/${PADDED}-mapping.json`.
- Scorer applies the mapping after the judge returns. Aggregate by CONDITION, not by A/B position.

This is standard AB-eval hygiene and should not be skipped. The judge must not see the condition label.

---

## Run protocol

1. Verify Brief 13 completed and its fixes are in the harness (see Fix 1).
2. Apply Fix 2 (variant builders + sanity checks), Fix 3 (harness fork), Fix 4 (label randomization + scorer). Commit each as its own commit.
3. Run `./evals/build-lenses-variant.sh` for both domains. Verify sanity checks pass.
4. Run `./evals/run-lenses-vs-characters-eval.sh`. Results land in `evals/results/lenses-vs-characters-<timestamp>/`.
5. Run `./evals/score-eval.sh evals/results/lenses-vs-characters-<timestamp>/` (reuse Brief 13's scorer; it's pairwise and works with arbitrary condition names as long as you pass the right label mapping).
6. Aggregate:
   - Per-prompt winner per criterion
   - Per-domain aggregate (rails-api, childrens-novel) per criterion
   - Per-axis breakdown (A/B/C axes from the prompts file — advisory vs decision vs review)
   - Overall: which style wins more prompts, by how much

## What the writeup needs to cover

At `docs/gigo/experiments/04-opus-4-7-lenses-vs-characters.md`:

- **Model & version:** Opus 4.7 + plugin v0.14.0-beta.
- **Variant construction:** exactly how the Lenses variant was derived from the Characters source, with byte-count and line-count deltas.
- **The headline:** which style wins per domain, per criterion, and overall.
- **Per-axis breakdown:** does Characters win on advisory prompts (push-back invited) and Lenses win on decision prompts (knowledge retrieval)? This would match the Hu et al. prediction. Call it out if it holds.
- **Per-criterion breakdown:** the 5 judge criteria (quality_bar, persona_voice, expertise_routing, specificity, pushback_quality). Persona_voice is hypothesized to favor Characters by construction; the interesting question is what the other 4 criteria show.
- **Delta to "Recommended" label:** concrete. "Flip the default to Characters" / "Keep Lenses as default" / "Remove the Recommended label — domain-split". Include the skill-file changes this would require if the recommendation is to flip.
- **Reconciliation with operator experience:** memory says operator always picks Characters and it works. If the data says Lenses wins, why does the operator experience Characters as better? Hypotheses: subjective engagement vs. objective quality, domain mismatch, the voice IS the value on certain tasks even if the judge doesn't score it that way.
- **Implications for Brief 14:** if Lenses wins here, flag Brief 14 for a re-run on Lenses fixtures.

## Hypotheses to state upfront in the writeup

- **H1 (skill's current assumption):** Lenses wins on cleanliness criteria (specificity, expertise_routing); Characters wins only on persona_voice. Net: Lenses takes 4/5 criteria.
- **H2 (operator's lived experience):** Characters wins overall — the voice and push-back activate better reasoning. Characters takes 3-5/5 criteria.
- **H3 (Hu et al. prediction):** Domain-split. Characters wins on push-back prompts (axis A — invited mistakes); Lenses wins on knowledge-retrieval prompts (axis B — decision/advisory). Per-axis result is the story.

Let the data pick. If the result is clean, say so; if ambiguous, say so and propose Phase 2 conditions to disambiguate.

## Out of scope

- Testing other persona styles beyond Lenses and Characters. Only two styles exist in the skill today.
- Testing other models. Opus 4.7 only. Separate brief if we want Sonnet 4.6 / Haiku 4.5.
- Re-assembling fixtures from scratch with `/gigo:gigo`. Deriving Lenses from Characters is deterministic; re-assembly adds LLM variance and mixes the test with assembly-time quality.
- Changing the `persona-template.md` contents. This eval tests existing template outputs, not template improvements.
- Refactoring `/gigo:gigo` to change the default BEFORE the eval runs. Wait for data.

## Relevant memories

- `feedback_characters_over_lenses.md` — operator's stated preference, the "Recommended" tension this eval resolves.
- `reference_hu_et_al_persona_tradeoff.md` — the authority prediction for a domain-split result.
- `feedback_personas_enhance_not_narrow.md` — "deep personas with disagreeing authorities force better thinking." Predicts Characters wins on pushback_quality.
- `project_experiment_results.md` — Phase 9 finding: "architecture carries coherence, personas add polish." If polish matters on Opus 4.7, Characters should edge Lenses even when the criteria aren't obviously persona-voice.
- `feedback_eval_harness_hygiene.md` — model pin, bare-glob, preserve fixtures. Apply all three.
- `feedback_kickoff_packet_structure.md` — the pattern this packet follows.
- `feedback_right_context_for_the_job.md` — core principle. Relevant because the question is effectively "which style IS the right context for Opus 4.7's job?"

## Deliverables

1. `evals/build-lenses-variant.sh` — deterministic Characters → Lenses variant builder, committed.
2. `evals/run-lenses-vs-characters-eval.sh` — forked harness, committed.
3. `evals/fixtures/rails-api-lenses/` + `evals/fixtures/childrens-novel-lenses/` — committed (they're source-of-truth fixtures, not gitignored results).
4. `evals/results/lenses-vs-characters-<timestamp>/` — gitignored per existing `.gitignore`.
5. Writeup at `docs/gigo/experiments/04-opus-4-7-lenses-vs-characters.md`.
6. **Product decision:** a one-line edit to `skills/gigo/SKILL.md:158` if the data supports flipping the default (or a confirmation line if the data supports keeping Lenses). Do NOT make this edit without operator approval — surface the recommendation in the writeup and let the operator decide.
7. Memory update to `feedback_characters_over_lenses.md`: replace the "untested" framing with actual findings. If Characters wins, the memory becomes "Characters confirmed by eval, [date], [result summary]." If Lenses wins, the memory becomes "Operator preference for Characters is subjective — data supports Lenses. Use Characters only when operator explicitly requests it."

## Starting prompt for the new session

Paste this into a fresh Claude Code session in `/Users/eaven/projects/gigo`:

> Kickoff packet at `briefs/15-lenses-vs-characters-opus-4-7-eval.md`. Read the whole file before doing anything. Prerequisite: Brief 13 (v0.14 + Opus 4.7 baseline) must be complete — check for `docs/gigo/experiments/02-opus-4-7-v0.14-assembled-vs-bare.md` and confirm `evals/run-eval.sh` has `--model claude-opus-4-7` pinned and the `CLAUDE.md*` glob exclusion. Your job: build deterministic Lenses variants of the two fixtures (preserve everything except character names, voice, and Personality fields), fork the harness, run the 28-prompt eval (2 domains × 7 prompts × 2 styles), score with the existing pairwise judge (randomize A/B mapping), and produce a recommendation on whether to flip `skills/gigo/SKILL.md:158`'s default from Lenses to Characters. Writeup lands at `docs/gigo/experiments/04-opus-4-7-lenses-vs-characters.md`. Start with `cat briefs/15-lenses-vs-characters-opus-4-7-eval.md`.
