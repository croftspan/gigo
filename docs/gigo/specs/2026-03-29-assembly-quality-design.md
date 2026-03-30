# Assembly Quality Enforcement — Design Spec

The assembly is the product. Two real failures proved this: croftspan-site got 4 surface-level personas that all agreed with each other (operator: "pulling teeth," "I'd never use gigo again"), and the assembly ignored extensive existing brand assets, researching the domain from scratch instead of enforcing existing expertise.

Two fixes: (1) enforce productive tension — every persona blend must have authorities that genuinely disagree, with the disagreement articulated and visible to the operator, (2) detect and enforce existing expertise — when the project has brand/voice/strategy artifacts, switch to enforcement mode where personas enforce the existing system instead of discovering a new one.

## Guiding Constraints

- **Tension is a gate, not guidance.** The tension test already exists in SKILL.md as descriptive text. It failed because nothing enforces it. The fix adds a validation gate that blocks assembly if tension can't be articulated.
- **The operator sees the tension.** Disagreements between authorities are surfaced in the pitch, not hidden in internal reasoning. This is how the operator knows the team will make real decisions.
- **Existing expertise overrides discovery.** When brand/voice/strategy artifacts exist, the assembly's job is enforcement, not research. Personas enforce the existing system; quality bars derive from the deliverables.
- **Detection is broad, not brittle.** Asset detection scans for patterns (filenames, common directories, operator mentions), not a hardcoded list. New project types shouldn't require skill updates.
- **The 6-step flow stays.** No new numbered steps. Tension validation and asset detection are gates within existing steps.
- **Line budgets are sacred.** SKILL.md is currently 202 lines. Enforcement mode procedure goes in `references/enforcement-mode.md` — SKILL.md gets a pointer, not the procedure. Follows the maintain skill's pattern (SKILL.md detects mode, reference has procedure).

---

## Part 1: Productive Tension Enforcement

### 1A. Tension Articulation Requirement (SKILL.md Step 3)

**File:** `skills/gigo/SKILL.md`, Step 3 (Research the Domain)

In question 2 of the discovery framework, after the existing sentence ending "...which is no better than no persona." (currently line 71), add the tension articulation requirement:

**Add immediately after that sentence, still within question 2:**

```
For each blend, articulate the tension before proceeding:
- "{Authority A} says {X}. {Authority B} says {Y}. The trade-off is {Z}."
- If you can't articulate a genuine disagreement, the blend is too thin — find authorities that push in different directions.
- The disagreement must be about something that matters in this domain, not a contrived difference.
```

**Example tensions (for the pitch, not for the skill text):**
- Artisan: "Rauno says polish every pixel. Paco says strip to the essential. Karri says commit to your opinion. The tension: how much is too much — and who decides."
- Sage: "Gloaguen says fewer rules succeed more. Cherny says mistakes should become rules. The tension: when does a useful rule become dead weight."
- Voice: "Sinek says lead with why. Wiebe says every word must survive 'so what?' Dry says make it about them, not you. The tension: emotional resonance vs ruthless clarity."

### 1B. Tension Visibility in Pitch (SKILL.md Step 4)

**File:** `skills/gigo/SKILL.md`, Step 4 (Assemble and Present the Team)

**First: compress the existing tension paragraph.** The current "Tension test every blend" paragraph (line 87) overlaps with the new Step 3 articulation requirement. Replace it with a one-line reference: "**Apply the tension test from Step 3 to every blend.** If you can't articulate the disagreement, go back." This avoids having the tension test stated in three places (Step 3 expanded, Step 4 full paragraph, Step 6 gate).

**Second: modify the pitch format** to include the tension. The current format shows "who they're modeled after" and "what they own." Add the disagreement. Update the guidance at line 97 — currently says "each persona gets 2-3 lines max," change to "each persona gets 4-6 lines" to accommodate the tension line.

**New pitch format for direct operator:**
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

**New pitch format for casual operator:**
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

The key change: each persona pitch now includes the tension between authorities, not just their names and what they own.

### 1C. Pre-Write Tension Gate (SKILL.md Step 6)

**File:** `skills/gigo/SKILL.md`, Step 6 (Write the Files)

Add a tension validation gate before the pre-write dedup pass. This is the enforcement mechanism.

**Add before "run the pre-write dedup pass":**

```
**Pre-write tension gate.** Before writing, verify each persona's blend:
- Can you state what the authorities disagree about in one sentence?
- Would removing any single authority change the persona's recommendations?
- If all authorities agree on everything, the persona is too thin — go back and find better authorities.

This gate is not optional. A team of agreeable personas produces a team that can't make decisions without the operator spelling them out.
```

### 1D. Tension Articulation in Persona Template

**File:** `skills/gigo/references/persona-template.md`

Add a "Tension Articulation" section after "Blending Authorities" (currently line 137). This teaches the format and provides examples.

**New section:**

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

---

## Part 2: Enforce-Existing-Expertise Mode

### 2A. Asset Detection (SKILL.md First Step)

**File:** `skills/gigo/SKILL.md`, "First Step: Check What Exists"

After checking for CLAUDE.md/.claude/, add a domain asset scan. This detects existing expertise the assembly should enforce rather than replace.

**Add after the existing three-way check:**

```
**Domain asset scan.** Regardless of CLAUDE.md status, scan the project for existing
domain expertise:

- Search for files suggesting codified expertise: names containing `brand`, `voice`,
  `messaging`, `pillars`, `style-guide`, `strategy`, `guidelines`, `standards`,
  `principles`, `manifesto`, `playbook`, `framework`
- Check common locations: `docs/`, `brand/`, `content/`, `strategy/`, `guidelines/`,
  project root
- Check paths the operator mentions in their description
- Look for any document that codifies decisions about voice, brand, methodology,
  or domain approach

If found, present them:
> "I found existing domain expertise in your project: [list files]. These represent
> decisions already made. Want me to build a team that enforces these standards,
> or start fresh?"

If the operator chooses enforcement → proceed to Enforcement Mode (see
`references/enforcement-mode.md`).
If the operator chooses fresh → proceed with standard assembly. Read the
existing assets during Step 3 as prior art — reference them in research,
but do not constrain personas to enforce them. Personas discover the domain
independently; existing assets inform but do not bind.
```

### 2B. Enforcement Mode (new reference file)

**File:** `skills/gigo/references/enforcement-mode.md`

Create a new reference file with the enforcement mode procedure. This follows the maintain skill's pattern — SKILL.md detects the mode and points here; the reference has the full procedure.

**SKILL.md gets a pointer, not the procedure.** Add after the domain asset scan in "First Step: Check What Exists":

```
When the operator chooses enforcement mode, read `references/enforcement-mode.md`
for the modified assembly flow.
```

**Reference file content:**

```markdown
# Enforcement Mode

When the project has existing domain expertise (brand strategy, voice guide, style
guide, pillars, methodology docs), the assembly switches to enforcement mode. The
team's job is execution, not discovery.

## How It Changes the Flow

**Step 1 (Listen):** Same — but note which existing assets the operator considers
authoritative.

**Step 2 (Research Depth):** Skipped for the domain itself — the domain IS the
existing artifacts. Research shifts to: "Who are the best authorities for ENFORCING
this kind of system?" Not "what should the brand voice be?" but "who is the best
at maintaining brand voice consistency across a team?"

**Step 3 (Research):** Read the existing assets thoroughly. The seven discovery
questions become verification questions:
1. What is being built → confirmed from existing docs
2. Who are the authorities → authorities for enforcement, not domain discovery
3. Gold standard → the existing assets ARE the gold standard
4. Core tools and processes → what tools enforce this system
5. Quality gates → derived from the existing deliverables
6. Common mistakes → how teams drift from established systems
7. What does "done" look like → faithful execution of the existing vision

**Step 4 (Present):** Personas are framed as enforcers:
> "The Voice Guardian — enforces the voice guide at [path]. Modeled after [authority
> who is rigorous about voice consistency] + [authority who catches drift]. Quality
> bar: every piece of content passes the voice guide's checklist."

Quality bars derive from the existing deliverables, not from generic domain research.

**Steps 5-6:** Same — refine and write.

## The Key Difference

In standard assembly, personas discover what excellence looks like in the domain.
In enforcement mode, the existing artifacts define excellence — personas ensure
the team delivers it consistently.

The tension requirement still applies. Enforcement personas need tension too —
e.g., "strict adherence to the guide" vs "knowing when the guide needs to bend
for a specific context."
```

---

## Conventions

- **Tension format:** Always use the pattern "{A} says {X}. {B} says {Y}. The trade-off is {Z}." This is consistent, scannable, and forces specificity.
- **Asset detection output:** List detected files with paths. Let the operator confirm which are authoritative.
- **Enforcement persona framing:** Use "enforces [artifact] at [path]" in the Owns field. Quality bars reference specific deliverables by name.
- **Pitch format:** Each persona gets name, authorities with tension, what they own. The tension line is not optional.
- **No new step numbers.** Validation gates live within existing steps, not as Step 3.5 or Step 6.1.
- **Line budget discipline:** Enforcement mode procedure lives in `references/enforcement-mode.md`. SKILL.md gets a 2-line pointer. Target: SKILL.md stays under ~220 lines after all changes.

---

## Files Modified

| File | Change |
|---|---|
| `skills/gigo/SKILL.md` | Add asset detection + enforcement mode pointer to First Step, tension articulation to Step 3, compress Step 4 tension paragraph + update pitch format, pre-write tension gate to Step 6 |
| `skills/gigo/references/persona-template.md` | Add Tension Articulation section with format, examples, and the croftspan-site failure case |
| `skills/gigo/references/enforcement-mode.md` | New file — enforcement mode procedure (how Steps 1-6 change when existing domain assets are detected) |

## Files NOT Modified

| File | Why |
|---|---|
| `skills/gigo/references/output-structure.md` | Enforcement mode doesn't change the two-tier architecture or file output structure |
| `skills/gigo/references/snap-template.md` | The Snap already audits persona quality — tension enforcement happens at assembly time |
| `skills/gigo/references/extension-file-guide.md` | Extension files are domain-specific; enforcement mode doesn't change their structure |

<!-- approved: spec 2026-03-29T23:19:47 by:Eaven -->
