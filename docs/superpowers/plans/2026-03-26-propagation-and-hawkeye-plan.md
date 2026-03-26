# Propagation & Hawkeye Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Propagate the eval-proven persona calibration heuristic and task-specific pointers into the output templates, and add Hawkeye (adversarial output gate) as a standard team member.

**Architecture:** Template-driven propagation — strengthen existing template files so the assembler generates these sections automatically. Hawkeye has two tiers: Overwatch workflow step (all teams) and Hawkeye persona (3+ team members), both pointing to an on-demand reference file.

**Tech Stack:** Markdown template files in the avengers-assemble and fury skill directories.

---

### Task 1: Strengthen persona calibration directive in persona-template.md

**Files:**
- Modify: `skills/avengers-assemble/references/persona-template.md:173-187`

- [ ] **Step 1: Change the Task-Type Awareness directive from suggestive to mandatory**

In `skills/avengers-assemble/references/persona-template.md`, replace lines 175-177:

```
Personas should know when to lead and when to step back. Not every task benefits from persona framing — factual lookup, debugging, and knowledge retrieval are degraded by persona context competing with the model's training (Hu et al., 2026).

When assembling a project, include this heuristic in the workflow or standards file (adapt the language to the domain):
```

With:

```
Personas should know when to lead and when to step back. Not every task benefits from persona framing — factual lookup, debugging, and knowledge retrieval are degraded by persona context competing with the model's training (Hu et al., 2026).

**When assembling a project, you MUST include this heuristic in the generated workflow.md** (adapt the language to the domain). This is not optional — the eval suite proved it converts ties to wins by letting the model lead with training on content tasks while adding persona value through framing. Omitting it costs ~10% win rate.
```

- [ ] **Step 2: Verify the file is still well-formed**

Read the modified file. Confirm the heuristic blockquote (lines 179-185) is unchanged and the new directive flows into it naturally.

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/persona-template.md
git commit -m "Make persona calibration heuristic mandatory in generated workflow.md"
```

---

### Task 2: Add generic-pointer anti-pattern to extension-file-guide.md

**Files:**
- Modify: `skills/avengers-assemble/references/extension-file-guide.md:30-36`

- [ ] **Step 1: Add the anti-pattern after the "When to Go Deeper" explanation**

In `skills/avengers-assemble/references/extension-file-guide.md`, after line 36 (the paragraph ending "not when editing plot structure."), add:

```markdown

**Anti-pattern: generic pointers.** "When working on migrations, read rails-patterns.md" is insufficient. Each pointer must name the observable task and what to check in the reference file: "When writing or reviewing a migration, read `.claude/references/rails-patterns.md` — especially safe migration patterns and lock-duration checks." Generic pointers don't trigger on real tasks. Task-specific pointers do — this was the single highest-leverage change in the eval suite (children's novel: 86% to 100%).
```

- [ ] **Step 2: Verify examples are consistent**

Read the three examples (Rails stack.md lines 80-83, Fiction voice-guide.md lines 108-111, Game engine-patterns.md lines 138-141). These examples already use reasonably specific pointers. No changes needed — the anti-pattern text reinforces the standard.

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/extension-file-guide.md
git commit -m "Add generic-pointer anti-pattern to extension file guide"
```

---

### Task 3: Update "Always create these" table in output-structure.md

**Files:**
- Modify: `skills/avengers-assemble/references/output-structure.md:29-36`

- [ ] **Step 1: Update the table descriptions for workflow.md and standards.md**

In `skills/avengers-assemble/references/output-structure.md`, replace lines 29-36:

```markdown
**Always create these:**

| File | Content |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity, autonomy model, quick reference. This is the brain. |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list — only things that apply to ALL work |
| `.claude/rules/workflow.md` | Execution loop — how to approach work, concisely |
| `.claude/rules/snap.md` | The Snap — protects the project (see `snap-template.md`) |
```

With:

```markdown
**Always create these:**

| File | Content |
|---|---|
| `CLAUDE.md` | Team roster with blended philosophies, project identity, autonomy model, quick reference. At 3+ personas, include Hawkeye (see `persona-template.md` → The Overwatch). |
| `.claude/rules/standards.md` | Quality gates, anti-patterns, forbidden list. "When to Go Deeper" pointers must be task-specific: name the observable task, name the reference file, name what to look for. |
| `.claude/rules/workflow.md` | Execution loop, Persona Calibration section (see `persona-template.md`), and Overwatch section (see `persona-template.md` → The Overwatch). |
| `.claude/rules/snap.md` | The Snap — protects the project (see `snap-template.md`) |
```

- [ ] **Step 2: Verify line count**

Read the file. Confirm it's still under 86 lines (current length). The table changes don't add lines, just update descriptions.

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/output-structure.md
git commit -m "Update output-structure table to require calibration, overwatch, and specific pointers"
```

---

### Task 4: Add The Overwatch section to persona-template.md

**Files:**
- Modify: `skills/avengers-assemble/references/persona-template.md:189-204`

- [ ] **Step 1: Add The Overwatch section after Team Sizing**

In `skills/avengers-assemble/references/persona-template.md`, after line 195 ("Never inflate for the sake of having a team. Never cap artificially."), add:

```markdown

## The Overwatch

Every assembled team gets adversarial output verification. This is not optional.

**Tier 1 (all teams):** An "Overwatch" section in the generated `workflow.md`. ~6 lines. Runs on every response. Template:

> ## Overwatch
>
> Before finalizing any response, step back and verify:
> - Did you actually apply the quality bars you cited, or just name-drop them?
> - Does your response address what was asked, or did you drift?
> - Would removing the persona language change your answer? If not, the persona added nothing.
> - Did you check the references you were told to check, or skip them?

**Tier 2 (3+ team members):** A Hawkeye persona in `CLAUDE.md`. Uses the lean persona template:

```
### Hawkeye — The Overwatch

**Modeled after:** Clint Barton's "I see better from a distance" detachment — step back from the work to see what's actually there
+ Nassim Taleb's via negativa — value comes from removing bullshit, not adding polish
+ Daniel Kahneman's pre-mortem technique — assume the output failed, then find why.

- **Owns:** Output verification, drift detection, quality-bar enforcement audit
- **Quality bar:** Every response survives the question "did you actually do what you claimed?"
- **Won't do:** Let persona language substitute for substance, let generic answers wear domain costumes, let references go unread
```

**Both tiers point to:** `.claude/references/overwatch.md` for the deep adversarial checklist. Generate this reference file for every project.

**The threshold:** Count the domain personas in the team roster (don't count Hawkeye himself). At 1-2, generate Overwatch workflow section and overwatch.md reference only. At 3+, also add Hawkeye persona to CLAUDE.md.

**Why the threshold:** Larger teams produce more complex output with more opportunities for persona decoration to substitute for substance. The workflow step catches honest mistakes at any team size. The full persona adds a voice for adversarial challenge when complexity warrants it.
```

- [ ] **Step 2: Verify the file is well-formed and under reasonable length**

Read the full file. Confirm it flows: ... → Team Sizing → The Overwatch → Persona Retirement → Conflicting Personas. The file will grow from ~204 lines to ~240 lines. This is a reference file (no line cap), but verify it's still well-organized.

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/persona-template.md
git commit -m "Add The Overwatch section: Hawkeye adversarial output gate"
```

---

### Task 5: Add Overwatch audit check to snap-template.md

**Files:**
- Modify: `skills/avengers-assemble/references/snap-template.md:42-43`

- [ ] **Step 1: Add check 9 after check 8 in the template's audit section**

In `skills/avengers-assemble/references/snap-template.md`, after line 42 (the line ending with `"Consider running `/smash` to restructure."`), add:

```markdown

**9. Overwatch check.** Is the Overwatch section present in `workflow.md`? If the team has 3+ domain personas, is Hawkeye in `CLAUDE.md`? Is `.claude/references/overwatch.md` present? If any are missing, restore them — the overwatch system is not optional.
```

- [ ] **Step 2: Verify template is still well-formed**

Read the file. Confirm the 9 audit checks flow logically (1-5 are content checks, 6 is persona calibration, 7 is total budget, 8 is coverage, 9 is overwatch).

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/snap-template.md
git commit -m "Add Overwatch audit check to Snap template"
```

---

### Task 6: Add Principle 10 to SKILL.md

**Files:**
- Modify: `skills/avengers-assemble/SKILL.md:173-174`

- [ ] **Step 1: Add Principle 10 after Principle 9**

In `skills/avengers-assemble/SKILL.md`, after line 173 (Principle 9, ending with "Load domain knowledge on demand from references."), add:

```markdown
10. **Every team has overwatch.** Assembled teams include adversarial self-verification — the Overwatch section in `workflow.md` (all teams) and the Hawkeye persona in `CLAUDE.md` (3+ team members). Both point to `.claude/references/overwatch.md` for depth.
```

- [ ] **Step 2: Verify SKILL.md is still under 500 lines**

Read the file. Current length is 174 lines. Adding 1 line keeps it well within budget.

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/SKILL.md
git commit -m "Add Principle 10: every team has overwatch"
```

---

### Task 7: Add Hawkeye threshold check to Fury's targeted-addition

**Files:**
- Modify: `skills/fury/references/targeted-addition.md:45-53`
- Modify: `skills/fury/SKILL.md:65`

- [ ] **Step 1: Add Hawkeye threshold check to Step 5 (Merge) in targeted-addition.md**

In `skills/fury/references/targeted-addition.md`, after line 49 ("Add new reference files to `.claude/references/`"), add:

```markdown
- **Check Hawkeye threshold.** After adding, count domain personas in CLAUDE.md (don't count Hawkeye). If now at 3+ and Hawkeye isn't present, add the Hawkeye persona to CLAUDE.md. Read `avengers-assemble/references/persona-template.md` → "The Overwatch" for the template. The Overwatch section in workflow.md and overwatch.md reference should already exist from initial assembly — verify they're present.
```

- [ ] **Step 2: Add Principle 9 to Fury's SKILL.md**

In `skills/fury/SKILL.md`, after line 65 (Principle 8, ending with "Read `avengers-assemble/references/persona-template.md` for the full standard."), add:

```markdown
9. **Overwatch scales with the team.** When adding a persona crosses the 3+ threshold, add Hawkeye. Read `avengers-assemble/references/persona-template.md` → The Overwatch.
```

- [ ] **Step 3: Commit**

```bash
git add skills/fury/references/targeted-addition.md skills/fury/SKILL.md
git commit -m "Add Hawkeye threshold check to Fury targeted-addition"
```

---

### Task 8: Update eval fixtures with Overwatch section

**Files:**
- Modify: `evals/fixtures/rails-api/.claude/rules/workflow.md`
- Modify: `evals/fixtures/childrens-novel/.claude/rules/workflow.md`

- [ ] **Step 1: Add Overwatch section to Rails fixture workflow.md**

In `evals/fixtures/rails-api/.claude/rules/workflow.md`, after the Persona Calibration section (after line 32), add:

```markdown

## Overwatch

Before finalizing any response, step back and verify:
- Did you actually apply the quality bars you cited, or just name-drop them?
- Does your response address what was asked, or did you drift?
- Would removing the persona language change your answer? If not, the persona added nothing.
- Did you check the references you were told to check, or skip them?
```

- [ ] **Step 2: Add Overwatch section to children's novel fixture workflow.md**

In `evals/fixtures/childrens-novel/.claude/rules/workflow.md`, after the Persona Calibration section (after line 31), add:

```markdown

## Overwatch

Before finalizing any response, step back and verify:
- Did you actually apply the quality bars you cited, or just name-drop them?
- Does your response address what was asked, or did you drift?
- Would removing the persona language change your answer? If not, the persona added nothing.
- Did you check the references you were told to check, or skip them?
```

- [ ] **Step 3: Add Hawkeye persona to Rails fixture CLAUDE.md (3 personas = threshold)**

In `evals/fixtures/rails-api/CLAUDE.md`, after Beck's persona entry (after the line "- **Won't do:** Skipping tests "for now"...") and before "## Autonomy Model", add:

```markdown

### Hawkeye — The Overwatch

**Modeled after:** Clint Barton's "I see better from a distance" detachment — step back from the work to see what's actually there
+ Nassim Taleb's via negativa — value comes from removing bullshit, not adding polish
+ Daniel Kahneman's pre-mortem technique — assume the output failed, then find why.

- **Owns:** Output verification, drift detection, quality-bar enforcement audit
- **Quality bar:** Every response survives the question "did you actually do what you claimed?"
- **Won't do:** Let persona language substitute for substance, let generic answers wear domain costumes, let references go unread
```

- [ ] **Step 4: Add Hawkeye persona to children's novel fixture CLAUDE.md (3 personas = threshold)**

In `evals/fixtures/childrens-novel/CLAUDE.md`, after Blume's persona entry and before "## Autonomy Model", add the same Hawkeye persona block as Step 3.

- [ ] **Step 5: Create overwatch.md reference for Rails fixture**

Create `evals/fixtures/rails-api/.claude/references/overwatch.md`:

```markdown
# Overwatch — Deep Reference

Read this when verifying output quality or when the Overwatch check flags a concern.

## Substance Check
Strip the persona language from your response. Read what remains. Does it still answer the question with domain-specific insight? If the answer is generic advice dressed in persona vocabulary, rewrite with actual substance.

## Drift Check
Re-read the operator's prompt. Does your response address what was actually asked? Common drift patterns:
- Answering the question you wish they'd asked instead of the one they did
- Expanding scope beyond what was requested
- Classifying or analyzing the prompt instead of responding to it

## Quality Gate Audit
For every quality bar or anti-pattern you referenced by name:
- Point to where in your response you enforced it
- If you can't point to enforcement, you name-dropped — either enforce it or remove the reference

## Reference Check
For every "When to Go Deeper" pointer that matched this task:
- Did you actually read the reference file?
- Did you use specific content from it in your response?
- If you cited a reference without using its content, that's decoration

## Specificity Check
Replace your project-specific references with generic equivalents. Does the response change meaningfully? If not, the specificity is cosmetic — find the project details that actually matter for this task and use them.
```

- [ ] **Step 6: Create overwatch.md reference for children's novel fixture**

Create `evals/fixtures/childrens-novel/.claude/references/overwatch.md` with the same content as Step 5.

- [ ] **Step 7: Verify line counts**

Run: `wc -l evals/fixtures/rails-api/.claude/rules/workflow.md evals/fixtures/childrens-novel/.claude/rules/workflow.md`

Expected: Both under 45 lines (currently 32-33, adding ~7 lines).

Run: `wc -l evals/fixtures/rails-api/.claude/rules/*.md evals/fixtures/childrens-novel/.claude/rules/*.md`

Expected: Both fixture totals under 300 lines.

- [ ] **Step 8: Commit**

```bash
git add evals/fixtures/
git commit -m "Add Overwatch and Hawkeye to eval fixtures"
```

---

### Task 9: Run eval suite and verify no regression

**Files:**
- Run: `evals/run-eval.sh`
- Run: `evals/score-eval.sh <results-dir>`

- [ ] **Step 1: Run the eval suite**

```bash
bash evals/run-eval.sh
```

Wait for all 20 prompts to complete (~15-20 minutes).

- [ ] **Step 2: Score the results**

```bash
bash evals/score-eval.sh evals/results/<timestamp>
```

- [ ] **Step 3: Verify results**

Expected: Combined win rate >= 95%. Zero losses. The Overwatch section should not degrade performance — it's a self-check that runs after the response is formed, not a constraint on response generation.

If regression detected: check whether the Overwatch section is causing the model to second-guess correct answers. If so, soften the language from "verify" to "confirm" and re-run.

- [ ] **Step 4: Update latest-summary.md**

```bash
cp evals/results/<timestamp>/summary.md evals/results/latest-summary.md
```

- [ ] **Step 5: Commit**

```bash
git add evals/results/latest-summary.md
git commit -m "Eval: verify no regression after Overwatch addition"
```
