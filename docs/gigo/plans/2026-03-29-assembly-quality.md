# Assembly Quality Enforcement — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-29-assembly-quality-design.md`

**Goal:** Fix gigo:gigo assembly quality — enforce productive tension in every persona blend and detect/enforce existing domain expertise

**Architecture:** All SKILL.md changes in one pass (tension gates, asset detection, pitch format, compression), new reference file for enforcement mode, new section in persona-template.md

---

### Task 1: All SKILL.md Modifications

**blocks:** 2, 3
**blocked-by:** []
**parallelizable:** false

**Files:**
- Modify: `skills/gigo/SKILL.md`

All four spec changes to SKILL.md in a single pass. This avoids line-number drift between sequential commits on the same file.

- [x] **Step 1: Add tension articulation to Step 3 (question 2)**

Find the sentence ending `...which is no better than no persona.` in question 2 of the discovery framework (currently line 71). Add immediately after, still within question 2:

```
For each blend, articulate the tension before proceeding:
- "{Authority A} says {X}. {Authority B} says {Y}. The trade-off is {Z}."
- If you can't articulate a genuine disagreement, the blend is too thin — find authorities that push in different directions.
- The disagreement must be about something that matters in this domain, not a contrived difference.
```

- [x] **Step 2: Compress the Step 4 tension paragraph**

Find the paragraph starting with `**Tension test every blend.**` in Step 4 (Assemble and Present the Team). This is currently a 2-sentence paragraph that restates the tension test from Step 3. Replace the entire paragraph with:

```
**Apply the tension test from Step 3 to every blend.** If you can't articulate the disagreement, go back and find better authorities.
```

- [x] **Step 3: Update pitch line count guidance**

Find the line starting with `**Present pitch-first.**` in Step 4. Change:

```
**Present pitch-first.** Show the whole roster at once — each persona gets 2-3 lines max. Name, who they're modeled after, what they own.
```

To:

```
**Present pitch-first.** Show the whole roster at once — each persona gets 4-6 lines. Name, authorities with the tension between them, what they own.
```

- [x] **Step 4: Replace the direct operator pitch example**

Find the code block starting with `Three on this one:` in Step 4 (between `For a direct, experienced operator:` and `For a casual, less experienced operator:`). Replace the entire code block with:

````
```
Three on this one:

  The Migration Architect
  Andrew Kane's zero-downtime pragmatism vs Sandi Metz's 'each object does
  one thing' vs DHH's convention-over-configuration. The tension: Kane wants
  safety checks everywhere, Metz wants small focused units, DHH wants Rails
  defaults. This persona navigates when safety requires breaking convention.
  Owns migration safety, rollback logic, lock detection.

  [next persona...]

Lock it in, or adjustments?
```
````

- [x] **Step 5: Replace the casual operator pitch example**

Find the code block starting with `I can work with that. Here's who I'd bring in:` in Step 4 (after `For a casual, less experienced operator:`). Replace the entire code block with:

````
```
I can work with that. Here's who I'd bring in:

  The Story Architect
  Wendelin Van Draanen is all about clues kids can follow step by step.
  Lemony Snicket thinks kids are smarter than that — don't simplify.
  Blue Balliett wants the mystery to teach something real. The push and pull:
  how hard do you make the trail? This person navigates that.
  Owns your plot and makes sure the mystery plays fair.

  [next persona...]

That's the crew. Want me to tell you more about any of them,
or does this feel like the right team?
```
````

- [x] **Step 6: Add pre-write tension gate to Step 6**

In Step 6 (Write the Files), find the sentence starting with `Once locked, run the **pre-write dedup pass**`. Add before it:

```
**Pre-write tension gate.** Before writing, verify each persona's blend:
- Can you state what the authorities disagree about in one sentence?
- Would removing any single authority change the persona's recommendations?
- If all authorities agree on everything, the persona is too thin — go back and find better authorities.

This gate is not optional. A team of agreeable personas produces a team that can't make decisions without the operator spelling them out.

```

- [x] **Step 7: Add domain asset scan to First Step**

In "First Step: Check What Exists", find the line starting with `**This skill is for first assembly only**`. Add after that paragraph:

```

**Domain asset scan.** Regardless of CLAUDE.md status, scan the project for existing domain expertise:

- Search for files suggesting codified expertise: names containing `brand`, `voice`, `messaging`, `pillars`, `style-guide`, `strategy`, `guidelines`, `standards`, `principles`, `manifesto`, `playbook`, `framework`
- Check common locations: `docs/`, `brand/`, `content/`, `strategy/`, `guidelines/`, project root
- Check paths the operator mentions in their description
- Look for any document that codifies decisions about voice, brand, methodology, or domain approach

If found, present them:
> "I found existing domain expertise in your project: [list files]. These represent decisions already made. Want me to build a team that enforces these standards, or start fresh?"

If the operator chooses enforcement → read `references/enforcement-mode.md` for the modified assembly flow.
If the operator chooses fresh → proceed with standard assembly. Read the existing assets during Step 3 as prior art — reference them in research, but do not constrain personas to enforce them. Personas discover the domain independently; existing assets inform but do not bind.
```

- [x] **Step 8: Line count verification**

Count total lines in the modified SKILL.md. The target is under ~220 lines. Starting from 201:
- Step 1 adds ~4 lines
- Step 2 compresses ~2 lines (multi-sentence paragraph → one sentence)
- Steps 3-5 are roughly net-neutral (pitch examples grow ~4 lines total)
- Step 6 adds ~7 lines
- Step 7 adds ~16 lines

Expected total: ~226. If over 220, compress the domain asset scan (Step 7) by:
- Combining the 4 bullet points into 2 (merge the search patterns into one bullet, merge the locations/operator-mentions into one)
- This should save ~4 lines, bringing total under ~222

If still over, compress the pre-write tension gate (Step 6) from 6 lines to 4 by removing the "This gate is not optional" sentence (the three-question checklist is sufficient).

- [x] **Step 9: Verify all changes**

Read the full modified SKILL.md. Confirm:
- Step 3 question 2 has the tension articulation requirement
- Step 4 has a one-line tension test reference (not the old full paragraph)
- Step 4 pitch examples show tension between authorities
- Step 4 guidance says "4-6 lines" not "2-3 lines max"
- Step 6 has the pre-write tension gate before the dedup pass
- First Step has the domain asset scan with enforcement mode pointer
- Step 6.5 (Generate Review Criteria) is unchanged
- "Depth on request" paragraph in Step 4 is unchanged
- The Principles section is unchanged
- Total line count is under ~220

- [x] **Step 10: Commit**

```bash
git add skills/gigo/SKILL.md
git commit -m "feat(gigo): enforce productive tension and detect existing domain expertise

Add tension articulation requirement to Step 3, compress Step 4 tension
paragraph, update pitch format to show tension, add pre-write tension gate
to Step 6, add domain asset detection to First Step with enforcement mode
pointer."
```

#### What Was Built
- **Deviations:** Line count came in at 227 initially; applied all three compression fallbacks from Step 8 (combined asset scan bullets, removed "not optional" sentence, compressed "If found" block). Final: 222 lines.
- **Review changes:** None
- **Notes for downstream:** The asset detection block is more compact than the spec's version — 2 bullets instead of 4. The enforcement mode pointer uses bullet-list format (`- **Enforcement** →` / `- **Fresh** →`) instead of paragraph format. The "start fresh" path was shortened to one sentence.

---

### Task 2: Create Enforcement Mode Reference File

**blocks:** 3
**blocked-by:** 1
**parallelizable:** false

**Files:**
- Create: `skills/gigo/references/enforcement-mode.md`

- [x] **Step 1: Create the enforcement mode reference file**

Write to `skills/gigo/references/enforcement-mode.md`:

```markdown
# Enforcement Mode

When the project has existing domain expertise (brand strategy, voice guide, style guide, pillars, methodology docs), the assembly switches to enforcement mode. The team's job is execution, not discovery.

## How It Changes the Flow

**Step 1 (Listen):** Same — but note which existing assets the operator considers authoritative.

**Step 2 (Research Depth):** Skipped for the domain itself — the domain IS the existing artifacts. Research shifts to: "Who are the best authorities for ENFORCING this kind of system?" Not "what should the brand voice be?" but "who is the best at maintaining brand voice consistency across a team?"

**Step 3 (Research):** Read the existing assets thoroughly. The seven discovery questions become verification questions:
1. What is being built → confirmed from existing docs
2. Who are the authorities → authorities for enforcement, not domain discovery
3. Gold standard → the existing assets ARE the gold standard
4. Core tools and processes → what tools enforce this system
5. Quality gates → derived from the existing deliverables
6. Common mistakes → how teams drift from established systems
7. What does "done" look like → faithful execution of the existing vision

**Step 4 (Present):** Personas are framed as enforcers:
> "The Voice Guardian — enforces the voice guide at [path]. Modeled after [authority who is rigorous about voice consistency] + [authority who catches drift]. Quality bar: every piece of content passes the voice guide's checklist."

Quality bars derive from the existing deliverables, not from generic domain research.

**Steps 5-6:** Same — refine and write.

## The Key Difference

In standard assembly, personas discover what excellence looks like in the domain. In enforcement mode, the existing artifacts define excellence — personas ensure the team delivers it consistently.

The tension requirement still applies. Enforcement personas need tension too — e.g., "strict adherence to the guide" vs "knowing when the guide needs to bend for a specific context."
```

- [x] **Step 2: Verify**

Read the created file. Confirm:
- All 7 verification questions are present
- The enforcer persona example is present
- The tension requirement reminder is present
- File is under 50 lines

- [x] **Step 3: Commit**

```bash
git add skills/gigo/references/enforcement-mode.md
git commit -m "feat(gigo): create enforcement mode reference file"
```

#### What Was Built
- **Deviations:** None
- **Review changes:** None
- **Notes for downstream:** None

---

### Task 3: Add Tension Articulation Section to Persona Template

**blocks:** []
**blocked-by:** 2
**parallelizable:** false

**Files:**
- Modify: `skills/gigo/references/persona-template.md`

- [x] **Step 1: Add Tension Articulation section after Blending Authorities**

Find the "Blending Authorities" section (ends with the game economy design example: `> + the Roblox Developer Hub's monetization framework for ethical in-game economies.`). Add after it, before the "Alignment vs Knowledge Signal" section:

```markdown

## Tension Articulation

Every blend must have an articulable disagreement. This is the quality gate — if you can't write the tension sentence, the blend is too thin.

**Format:** "{Authority A} says {X}. {Authority B} says {Y}. The trade-off is {Z} — and that's the decision this persona navigates."

**Examples from GIGO's own team:**

The Artisan:
> Rauno says polish every micro-interaction to sub-pixel precision. Paco says
> strip away until only the essential remains. Karri says commit to your opinion
> and don't try to please everyone. The trade-off: perfectionism vs minimalism
> vs conviction — how much is too much, and whose taste wins.

Sage:
> Gloaguen proved bloated context reduces success rates 20%+. Cherny proved
> mistakes-become-rules compounds institutional memory. The trade-off: when does
> a useful rule become dead weight — and the answer changes as the project matures.

The Voice:
> Sinek says lead with why — emotion before logic. Wiebe says every sentence must
> survive "so what?" — cut the feeling if it doesn't convert. Dry says make it
> about them, not you. The trade-off: emotional resonance vs ruthless clarity vs
> audience-centricity.

**The croftspan-site failure:** Dunford, Miller, and McGlaughlin all say "the customer
is the hero." Zero disagreement. Zero decisions. The persona couldn't anticipate because
there was nothing to navigate — it was "senior marketer in a costume."

**The test:** If every authority in a persona would give the same advice for every
decision in the domain, the persona adds nothing. Find authorities who push in
genuinely different directions on trade-offs that matter.
```

- [x] **Step 2: Verify**

Read the modified file. Confirm:
- The new section appears between "Blending Authorities" and "Alignment vs Knowledge Signal"
- Three GIGO team examples are present (Artisan, Sage, Voice)
- The croftspan-site failure case is present
- The "Alignment vs Knowledge Signal" section that follows is unchanged

- [x] **Step 3: Commit**

```bash
git add skills/gigo/references/persona-template.md
git commit -m "feat(gigo): add tension articulation section with examples and failure case"
```

#### What Was Built
- **Deviations:** None
- **Review changes:** None
- **Notes for downstream:** None

---

## Risks

- **Line budget.** Net additions to SKILL.md are ~29 lines, but Step 2 compression and the conditional trimming in Step 8 should keep it under ~222. Task 1 Step 8 has explicit fallback instructions if over 220.
- **Pitch format length.** The new pitch examples are longer. If gigo:gigo follows them literally for a 4-persona team, each pitch could be ~25 lines. The spec allows "Depth on request" as an escape valve.

## Done When

1. SKILL.md has: tension articulation in Step 3, compressed Step 4 tension + updated pitch format, pre-write tension gate in Step 6, asset detection + enforcement pointer in First Step
2. SKILL.md is under ~222 lines (verified in Task 1 Step 8)
3. `references/enforcement-mode.md` exists with the full enforcement procedure
4. `references/persona-template.md` has the Tension Articulation section with 3 examples + failure case

<!-- approved: plan 2026-03-29T23:19:47 by:Eaven -->
