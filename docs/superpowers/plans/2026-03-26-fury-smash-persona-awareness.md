# Fury & Smash Persona-Awareness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `/fury` and `/smash` skills to incorporate the persona-accuracy tradeoff (Hu et al., 2026) so they design, audit, and restructure personas with alignment-vs-knowledge awareness.

**Architecture:** Targeted edits to both SKILL.md files (principles) and their reference files (operational procedures). Fury gets updates to targeted-addition, health-check, and upgrade-checklist. Smash gets updates to Phase 2 (Measure) and Phase 6 (Assessment). No new files created.

**Tech Stack:** Markdown skill files only — no code.

---

### Task 1: Add persona-awareness principle to Fury SKILL.md

**Files:**
- Modify: `skills/fury/SKILL.md:56-65` (Principles section)

- [ ] **Step 1: Add principle 8**

Add after principle 7 ("Whatever it takes." on line 65):

```markdown
8. **Personas shape approach, not recall.** When adding or auditing personas, keep alignment signal (quality bars, approach, constraints) in rules. Move domain knowledge (factual specifics, implementation patterns) to references. Read `avengers-assemble/references/persona-template.md` for the full standard.
```

- [ ] **Step 2: Verify file reads well**

Read `skills/fury/SKILL.md` in full. Confirm:
- Principle 8 fits the existing tone (short, direct, Fury voice)
- The cross-reference to persona-template.md gives implementers the full guidance without duplicating it here
- File stays well under any size concern (was 65 lines, now 66)

- [ ] **Step 3: Commit**

```bash
git add skills/fury/SKILL.md
git commit -m "Add persona-awareness principle to Fury skill

Principle 8: personas shape approach, not recall. Points to persona
template for alignment-vs-knowledge split guidance."
```

---

### Task 2: Update Fury's targeted-addition procedure with alignment-vs-knowledge split

**Files:**
- Modify: `skills/fury/references/targeted-addition.md:32-36` (Step 3 presentation) and `skills/fury/references/targeted-addition.md:44-50` (Step 5 merge)

When Fury adds a new persona, the procedure should guide the assembler to separate alignment signal from knowledge signal.

- [ ] **Step 1: Add persona-calibration bullet to Step 3 presentation**

In Step 3 "Research and Propose", add a bullet to the presentation checklist (after line 36 "Impact on line budgets"):

```markdown
- **Alignment vs knowledge split** — which parts of the new persona are alignment signal (quality bars, approach, constraints → rules) vs knowledge signal (factual specifics, patterns → references)?
```

- [ ] **Step 2: Add alignment guidance to Step 5 merge**

In Step 5 "Merge", add after the line about reading templates (line 50):

```markdown

When designing the new persona, separate alignment signal from knowledge signal. The lean tier entry in CLAUDE.md should contain only alignment content — quality bars, approach, constraints, what to push back on. Domain-specific knowledge (factual details, implementation patterns, technical specifics) belongs in `.claude/references/personas/` or a reference file, loaded on demand. See `avengers-assemble/references/persona-template.md` for the "Alignment vs Knowledge Signal" section.
```

- [ ] **Step 3: Verify the file reads coherently**

Read `skills/fury/references/targeted-addition.md` in full. Confirm:
- The new bullet in Step 3 fits naturally with the existing presentation checklist
- The new paragraph in Step 5 adds actionable guidance without being redundant with the bullet
- The cross-reference to persona-template.md avoids duplicating the full framework

- [ ] **Step 4: Commit**

```bash
git add skills/fury/references/targeted-addition.md
git commit -m "Add alignment-vs-knowledge guidance to Fury targeted addition

New personas should separate alignment signal (rules) from knowledge
signal (references). Points to persona template for full framework."
```

---

### Task 3: Update Fury's health-check procedure with persona-calibration check

**Files:**
- Modify: `skills/fury/references/health-check.md:13-18` (Weight section in Step 1)

The health check's "Weight" axis evaluates whether rules earn their token cost. It should also check whether persona entries contain knowledge signal that belongs in references.

- [ ] **Step 1: Add persona-calibration check to Weight axis**

Add after the last bullet in the Weight section (after line 19 "If not, let it go."):

```markdown
- Do persona entries in CLAUDE.md contain domain-knowledge content (factual specifics, implementation patterns)? → Alignment signal stays; knowledge moves to `.claude/references/`.
```

- [ ] **Step 2: Verify the file reads coherently**

Read `skills/fury/references/health-check.md` in full. Confirm:
- The new bullet fits naturally among the existing weight-check questions
- It doesn't duplicate the other bullets (derivability, relevance, overlap, line count, total budget, cost)
- It adds persona-specific checking without being redundant

- [ ] **Step 3: Commit**

```bash
git add skills/fury/references/health-check.md
git commit -m "Add persona-calibration check to Fury health check

Weight axis now checks whether persona entries contain knowledge signal
that should be in references."
```

---

### Task 4: Update Fury's upgrade-checklist with persona-calibration feature

**Files:**
- Modify: `skills/fury/references/upgrade-checklist.md:9-20` (Feature comparison table in Step 1)

The upgrade checklist compares a project against current AA standards. It should include the alignment-vs-knowledge persona split as a checkable feature.

- [ ] **Step 1: Add persona-calibration row to feature table**

Add a new row to the table in Step 1 (after the "Persona line targets" row on line 16):

```markdown
| Persona content split | Persona entries contain alignment signal only (quality bars, approach, constraints). Domain knowledge lives in `.claude/references/personas/` or reference files | Persona entries in CLAUDE.md contain factual specifics, implementation patterns, or technical details that could be moved to references |
```

- [ ] **Step 2: Add upgrade action to Step 4**

In Step 4 "Apply Upgrades" (after line 51 about tightening personas), add:

```markdown
- Audit persona entries for knowledge signal — factual specifics, implementation patterns, and technical details that compete with the model's factual recall when loaded as system context. Move to `.claude/references/personas/` or relevant reference files, keeping only alignment signal (quality bars, approach, constraints) in the lean tier
```

- [ ] **Step 3: Verify the file reads coherently**

Read `skills/fury/references/upgrade-checklist.md` in full. Confirm:
- The new table row follows the same format as existing rows (Feature | Current Standard | How to detect)
- The new upgrade action sits naturally after the persona formatting actions
- No duplication with existing table rows

- [ ] **Step 4: Commit**

```bash
git add skills/fury/references/upgrade-checklist.md
git commit -m "Add persona content split to Fury upgrade checklist

Projects can now be checked for alignment-vs-knowledge persona split.
Upgrade action moves knowledge signal from lean tier to references."
```

---

### Task 5: Add persona-calibration check to Smash Phase 2 (Measure)

**Files:**
- Modify: `skills/smash/SKILL.md:37-47` (Phase 2: Measure)

Smash measures every rules file against five checks. Add a sixth check for persona-calibration.

- [ ] **Step 1: Add check 6 to Phase 2**

Add after check 5 "Staleness check" (after line 47):

```markdown

**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain domain-knowledge content (factual specifics, implementation patterns) that belongs in references? Persona entries should be alignment signal only — quality bars, approach, constraints. Domain knowledge competes with the model's factual recall when loaded as system context (Hu et al., 2026).
```

- [ ] **Step 2: Verify the file reads coherently**

Read `skills/smash/SKILL.md` in full. Confirm:
- Check 6 fits the existing measurement pattern (each check is a bold numbered item with a question)
- The Hu et al. citation matches the style used elsewhere (brief, parenthetical)
- Phase 2 still reads as a coherent measurement sequence

- [ ] **Step 3: Commit**

```bash
git add skills/smash/SKILL.md
git commit -m "Add persona-calibration check to Smash Phase 2

Smash now measures whether persona entries contain knowledge signal
that should be in references during its assessment phase."
```

---

### Task 6: Update Smash Phase 6 (Assessment) with persona-calibration check

**Files:**
- Modify: `skills/smash/SKILL.md:113-129` (Phase 6: Assessment)

Smash's post-restructure assessment checks persona quality. It should also check the alignment-vs-knowledge split.

- [ ] **Step 1: Add persona-calibration question to assessment**

Add a new bullet to the assessment questions (after line 120 "or is everything surface-level?"):

```markdown
- Do persona entries contain only alignment signal (quality bars, approach, constraints), or are they carrying domain knowledge that belongs in references?
```

- [ ] **Step 2: Verify the file reads coherently**

Read `skills/smash/SKILL.md` in full. Confirm:
- The new question fits the existing assessment style (questions about persona quality)
- It doesn't duplicate the Phase 2 check (Phase 2 measures during assessment; Phase 6 checks the result after restructuring)
- SKILL.md stays well under 500 lines

- [ ] **Step 3: Commit**

```bash
git add skills/smash/SKILL.md
git commit -m "Add persona-calibration check to Smash Phase 6 assessment

Post-restructure assessment now verifies persona entries contain only
alignment signal, not knowledge that belongs in references."
```

---

### Task 7: Add persona-awareness principle to Smash principles

**Files:**
- Modify: `skills/smash/SKILL.md:132-141` (Principles section)

- [ ] **Step 1: Add principle 8**

Add after principle 7 ("Nothing without approval." on line 141):

```markdown
8. **Personas shape approach, not recall.** When restructuring personas, keep alignment signal (quality bars, constraints, anti-patterns) in rules. Move domain knowledge (factual specifics, implementation patterns) to references where it loads on demand without competing with the model's factual recall.
```

- [ ] **Step 2: Verify the file reads coherently**

Read `skills/smash/SKILL.md` in full. Confirm:
- Principle 8 fits the existing tone
- SKILL.md stays well under 500 lines (was 141, now ~142)
- No duplication with the Phase 2 or Phase 6 additions from Tasks 5 and 6

- [ ] **Step 3: Commit**

```bash
git add skills/smash/SKILL.md
git commit -m "Add persona-awareness principle to Smash skill

Principle 8: personas shape approach, not recall. Alignment signal in
rules, knowledge in references."
```

---

### Task 8: Final verification

**Files:**
- Read: All modified files

- [ ] **Step 1: Cross-reference check**

Read all modified files and verify:
- Fury SKILL.md has principle 8 and points to persona-template.md
- Fury targeted-addition.md has alignment-vs-knowledge bullet in presentation and guidance in merge
- Fury health-check.md has persona-calibration bullet in weight axis
- Fury upgrade-checklist.md has persona content split in feature table and upgrade actions
- Smash SKILL.md has check 6 in Phase 2, persona question in Phase 6, and principle 8
- No contradictions between files
- Consistent terminology ("alignment signal," "knowledge signal," "persona calibration")

- [ ] **Step 2: Dedup check**

Verify the Hu et al. finding is not stated in full in any of these files. Each file should have:
- A brief operational instruction (what to check or do)
- NOT the full research finding (that lives in authorities.md)
- At most one parenthetical citation "(Hu et al., 2026)"

- [ ] **Step 3: Line count check**

Verify:
- `skills/fury/SKILL.md`: under reasonable size (was 65 lines)
- `skills/smash/SKILL.md`: under 500 lines (was 141 lines)
- All reference files: under reasonable size

- [ ] **Step 4: Final commit (if any fixups needed)**

Only if checks revealed issues:
```bash
git add -A
git commit -m "Fix integration issues in fury/smash persona-awareness updates"
```
