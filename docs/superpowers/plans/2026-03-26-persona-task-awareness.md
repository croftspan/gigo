# Persona Task-Type Awareness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Hu et al.'s persona-accuracy tradeoff findings into the skill ecosystem so assembled personas help alignment tasks without degrading knowledge-retrieval tasks.

**Architecture:** Four-part change — (1) add Hu et al. to the research foundation in authorities.md, (2) add an alignment-vs-knowledge split to persona design guidance, (3) add a dynamic task-type assessment heuristic to the persona template, (4) add context-placement awareness to output-structure.md so knowledge-heavy persona content lands in references (user-context) rather than rules (system-context).

**Research basis:** Hu, Rostami & Thomason, "Expert Personas Improve LLM Alignment but Damage Accuracy" (arXiv:2603.18507, March 2026). Tested 6 LLMs across MT-Bench, MMLU, and safety benchmarks with 12 expert personas at 3 granularity levels.

---

### Task 1: Add Hu et al. to authorities.md

**Files:**
- Modify: `.claude/references/authorities.md:54-68` (Agent Research section)
- Modify: `.claude/references/authorities.md:70-77` (What This Means for Persona Blending section)

This task adds the paper as a cited authority alongside the existing positive-side persona citations (Kong, Xu, Pei). It also updates the "What This Means" section to acknowledge the tradeoff.

- [ ] **Step 1: Add Hu et al. entry to Agent Research section**

Add after the existing Xu et al. entry (line 66), before the Hong et al. entry (line 68):

```markdown
**Hu et al. — "Expert Personas Improve LLM Alignment but Damage Accuracy" (2026):** Persona effectiveness is task-type dependent. Expert personas consistently improve alignment-dependent tasks (writing style, tone, safety refusal, format adherence: +0.40 to +0.65 on MT-Bench) but consistently damage pretraining-dependent tasks (factual recall, coding knowledge, math: -0.10 to -0.65). Longer personas amplify both effects. Models more optimized for system-prompt steering are more sensitive to both gains and losses. For reasoning-distilled models, gains come from added context length triggering reasoning chains, not from persona identity itself.
```

- [ ] **Step 2: Update "What This Means for Persona Blending" section**

Replace the current section (lines 70-77) with:

```markdown
## What This Means for Persona Blending

The research presents a nuanced picture: personas work when they're **specific syntheses of real authorities** (Kong, Xu, Pei) — but they also carry a cost. Hu et al. (2026) showed that persona context competes with factual recall at the attention level, consistently degrading knowledge-retrieval tasks even when the persona is well-matched.

This means every persona in the skill ecosystem must:
1. Name 2-3+ specific authorities with their distinct contributions
2. Explain what each authority brings to the blend
3. Apply specifically to the project's domain, not generically
4. Be concrete enough that the persona would produce measurably different output than a generic prompt
5. **Separate alignment signal from knowledge signal** — alignment-shaping content (quality bars, approach, anti-patterns) belongs in always-on rules; domain-knowledge content (factual specifics, technical details) belongs in on-demand references
6. **Include task-type awareness** — personas should know when to step back and let the model's training lead (see persona template)
```

- [ ] **Step 3: Verify the file stays well-structured**

Run: Read `.claude/references/authorities.md` in full and confirm:
- Hu et al. entry sits naturally among the other Agent Research entries
- No duplicate information with existing Kong/Xu/Pei entries
- "What This Means" section flows logically from positive findings through the tradeoff to the design requirements

- [ ] **Step 4: Commit**

```bash
git add .claude/references/authorities.md
git commit -m "Add Hu et al. (2026) persona-accuracy tradeoff to authorities

Research shows expert personas help alignment tasks but hurt knowledge
retrieval. Updates persona blending guidance with alignment-vs-knowledge
split and task-type awareness requirements."
```

---

### Task 2: Add alignment-vs-knowledge split to persona template

**Files:**
- Modify: `skills/avengers-assemble/references/persona-template.md:137-169` (Blending Authorities section onward)

This task adds a new section to the persona template that teaches the assembler how to separate alignment signal from knowledge signal during persona design. This is the structural (Option B) component.

- [ ] **Step 1: Add "Alignment vs Knowledge Signal" section**

Add after the "Blending Authorities" section (after line 153) and before "Team Sizing" (line 155):

```markdown
## Alignment vs Knowledge Signal

When blending authorities, distinguish two types of persona content:

**Alignment signal** — how to approach work. Style, quality bars, anti-patterns, decision heuristics, what to push back on. This shapes *how the answer is presented* and benefits from always-on persona context.

**Knowledge signal** — what to know about the domain. Factual specifics, technical details, implementation patterns, domain terminology. This is *what the answer contains* and can be degraded by persona context competing with the model's factual recall (Hu et al., 2026).

**The split:**
- Alignment signal stays in the lean tier (CLAUDE.md) and rules — it's the persona's core value
- Knowledge signal goes in the rich tier (references) — loaded when the task needs domain depth, not on every conversation
- When assembling, ask of each persona element: "Does this shape *how* the agent works, or *what* it knows?" How → rules. What → references.

**Example — a database migration persona:**
- Alignment (rules): "Every migration is reversible and tested against production-size data" — this is a quality bar
- Alignment (rules): "Won't do migrations that lock tables over 10 seconds" — this is a constraint
- Knowledge (references): PostgreSQL lock types, migration rollback patterns, specific pg_stat_activity queries — these are domain facts the model already knows and loads better on demand
```

- [ ] **Step 2: Verify template stays under reasonable length and reads well**

Run: Read `skills/avengers-assemble/references/persona-template.md` in full and confirm:
- New section sits naturally between Blending Authorities and Team Sizing
- No overlap with existing content in the template
- The example is concrete and follows the template's existing example style (database migration persona already exists as an example above)

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/persona-template.md
git commit -m "Add alignment-vs-knowledge signal split to persona template

Teaches assemblers to separate how-to-approach-work content (alignment,
stays in rules) from what-to-know content (knowledge, goes to references).
Based on Hu et al. finding that persona context competes with factual recall."
```

---

### Task 3: Add task-type assessment heuristic to persona template

**Files:**
- Modify: `skills/avengers-assemble/references/persona-template.md` (after the new section from Task 2)

This task adds the dynamic determination framework — the runtime (Option C) component. Instead of hardcoding task lists, it gives the persona a self-assessment heuristic that Claude applies in the moment.

- [ ] **Step 1: Add "Task-Type Awareness" section**

Add immediately after the "Alignment vs Knowledge Signal" section added in Task 2:

```markdown
## Task-Type Awareness

Personas should know when to lead and when to step back. Not every task benefits from persona framing — factual lookup, debugging, and knowledge retrieval are degraded by persona context competing with the model's training (Hu et al., 2026).

When assembling a project, include this heuristic in the workflow or standards file (adapt the language to the domain):

```
## Persona Calibration

Before applying persona guidance, assess the task:
- **Presentation tasks** — how the answer is shaped matters (style, format, tone, structure, quality judgment). Lean into persona fully.
- **Content tasks** — what the answer contains matters (factual recall, computation, code lookup, debugging). Step back — let your training lead, use persona only for framing the response.

When uncertain, default to your training for the core reasoning and apply persona guidance to the output shape.
```

This is not a rigid gate — it's a lightweight metacognitive check. The model self-assesses task type before deciding how heavily to apply the persona lens. For tasks the heuristic doesn't cleanly cover, the instruction to "default to training for core reasoning" provides a safe fallback.
```

- [ ] **Step 2: Verify the section reads as actionable guidance**

Run: Read `skills/avengers-assemble/references/persona-template.md` in full and confirm:
- The heuristic is concrete enough to include in a generated workflow/standards file
- The code block within the section is clearly marked as "include this in the generated project"
- No overlap with the alignment-vs-knowledge section from Task 2 (that one is about design time; this one is about runtime)

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/persona-template.md
git commit -m "Add task-type awareness heuristic to persona template

Gives assembled personas a self-assessment: presentation tasks get full
persona, content tasks default to model training. Lightweight metacognitive
check instead of hardcoded task lists."
```

---

### Task 4: Add context-placement awareness to output-structure.md

**Files:**
- Modify: `skills/avengers-assemble/references/output-structure.md:69-77` (Persona Structure section)

This task captures the paper's finding that system-prompt placement amplifies both persona gains and losses. Knowledge-heavy persona content should load mid-task from references (user-context) rather than at session start from rules (system-context). Our two-tier architecture already supports this — we just need to make the *intent* explicit.

- [ ] **Step 1: Expand the Persona Structure section**

Replace the current Persona Structure section (lines 69-77) with:

```markdown
## Persona Structure — Two Tiers

Read `persona-template.md` for format, examples, and calibration guidance.

**Lean tier (CLAUDE.md):** Scannable, bullet-driven. Uses `Modeled after` (one authority per line with `+`), `Owns`, `Quality bar`, `Won't do`. Optional: `Personality`, `Decides by`, `Depth` pointer. Target: 8-10 lines, hard ceiling 12.

**Rich tier (`.claude/references/personas/{name}.md`):** Character sheets with Bio, Personality, Communication Style, Decision Framework, Pushes Back On, Champions. Depth calibrated to the operator — full treatment for casual/creative operators who need personas that lead, minimal treatment (just decision frameworks and edge cases) for direct/technical operators who need personas that execute.

**Alignment vs knowledge placement:** The lean tier should contain alignment signal only — how to approach work (quality bars, constraints, anti-patterns). Domain knowledge (factual specifics, technical patterns, implementation details) belongs in the rich tier, loaded on demand. System-prompt placement (rules) amplifies both persona benefits and persona damage; reference placement (mid-task loading) gives the model domain context without competing with its factual recall. This isn't just about token cost — it's about where in the context the persona lands.

Never inflate. Never cap.
```

- [ ] **Step 2: Verify the change is consistent with persona-template.md**

Run: Read both `skills/avengers-assemble/references/output-structure.md` and `skills/avengers-assemble/references/persona-template.md` and confirm:
- The output-structure section points to persona-template for details (it already does)
- The new "Alignment vs knowledge placement" paragraph doesn't duplicate the fuller treatment in persona-template — it summarizes the architectural implication
- Language is consistent between the two files

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/references/output-structure.md
git commit -m "Add context-placement awareness to persona output structure

System-prompt placement amplifies both persona gains and damage. Alignment
signal stays in rules (lean tier). Domain knowledge goes to references
(rich tier) where it loads mid-task without competing with factual recall."
```

---

### Task 5: Update the avengers-assemble SKILL.md principles

**Files:**
- Modify: `skills/avengers-assemble/SKILL.md:163-172` (Principles section)

The SKILL.md principles section is the top-level guidance for the assembler. It should reflect the new understanding without duplicating the detail in the reference files.

- [ ] **Step 1: Add persona-awareness principle**

Add as principle 9 (before the closing of the Principles section), after principle 8 ("Nothing without approval"):

```markdown
9. **Personas shape approach, not recall.** Persona context helps alignment tasks (style, quality, format) but can degrade knowledge tasks (factual recall, debugging, code lookup). Design personas around *how to approach work*, not *what to know*. Load domain knowledge on demand from references.
```

- [ ] **Step 2: Verify SKILL.md stays under 500 lines**

Run: Count lines in `skills/avengers-assemble/SKILL.md`
Expected: Under 500 lines (currently ~173, well within budget)

- [ ] **Step 3: Commit**

```bash
git add skills/avengers-assemble/SKILL.md
git commit -m "Add persona-awareness principle to assembly skill

Principle 9: personas shape approach, not recall. Alignment content in
rules, knowledge content in references."
```

---

### Task 6: Update the snap template with persona-calibration audit step

**Files:**
- Modify: `skills/avengers-assemble/references/snap-template.md:28-39` (The Audit section)

The Snap audits rules every session. It should also check whether persona content in rules contains knowledge signal that should be in references.

- [ ] **Step 1: Add persona-calibration check to the audit template**

Add as step 6 in the audit (between current step 5 "Cost check" and current step 6 "Total budget check", renumbering accordingly):

```markdown
**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain domain-knowledge content (factual specifics, implementation patterns) that belongs in references? Persona entries in rules should be alignment signal only — quality bars, approach, constraints. Domain knowledge loads better on demand where it doesn't compete with the model's factual recall.
```

- [ ] **Step 2: Renumber subsequent audit steps**

Current step 6 "Total budget check" becomes step 7. Current step 7 "Coverage check" becomes step 8.

- [ ] **Step 3: Verify the template reads coherently**

Run: Read `skills/avengers-assemble/references/snap-template.md` in full and confirm:
- The new step fits the audit's progression (line check → derivability → overlap → staleness → cost → persona calibration → total budget → coverage)
- The language matches the existing audit tone
- The template stays under reasonable length

- [ ] **Step 4: Commit**

```bash
git add skills/avengers-assemble/references/snap-template.md
git commit -m "Add persona-calibration audit step to Snap template

Snap now checks whether persona entries contain knowledge signal that
should be in references. Alignment signal stays, domain knowledge moves."
```

---

### Task 7: Update this project's own snap.md with the persona-calibration check

**Files:**
- Modify: `.claude/rules/snap.md:28-40` (The Audit section)

Our own project's snap should also include the new audit step, since our CLAUDE.md has personas.

- [ ] **Step 1: Add persona-calibration check to our snap**

Add as step 6 in the audit (between current step 5 "Cost check" and current step 6 "Total budget check", renumbering accordingly):

```markdown
**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain domain-knowledge content (factual specifics, implementation patterns) that belongs in references? Persona entries should contain alignment signal only — quality bars, approach, constraints. Move domain knowledge to `.claude/references/` where it loads on demand.
```

- [ ] **Step 2: Renumber subsequent audit steps**

Current step 6 "Total budget check" becomes step 7. Current step 7 "Coverage check" becomes step 8.

- [ ] **Step 3: Verify snap.md stays under ~60 lines**

Run: Count lines in `.claude/rules/snap.md`
Expected: Under 60 lines (currently ~56 lines, the new step adds ~2 lines net after renumbering)

- [ ] **Step 4: Commit**

```bash
git add .claude/rules/snap.md
git commit -m "Add persona-calibration audit step to project snap

Mirrors the snap template change. Our snap now checks whether our own
personas contain knowledge signal that should be in references."
```

---

### Task 8: Add forward-proofing note to context-engineering.md

**Files:**
- Modify: `.claude/references/context-engineering.md` (add section at end)

The paper found that reasoning-distilled models don't benefit from persona identity — gains come from context length triggering reasoning chains. If Claude shifts toward more reasoning-distilled architecture, our persona approach would need to change. This is worth tracking as a reference note.

- [ ] **Step 1: Add reasoning-distillation note**

Add at the end of `.claude/references/context-engineering.md`:

```markdown
## Persona and Model Architecture

Hu et al. (2026) found that persona effectiveness depends on model training:

- **Instruction-tuned models** (Claude's architecture): Personas amplify alignment behaviors learned during instruction-tuning. Expert personas consistently outperform random personas. System-prompt placement amplifies both gains and losses.
- **Reasoning-distilled models** (e.g., DeepSeek-R1 variants): Any structured context triggers reasoning chains regardless of persona identity. Expert personas provide only marginal benefit over random personas. The gain is from context length, not persona specificity.

**Current implication:** Claude is instruction-tuned, so our specific-persona approach is on the right side of this split. Our personas provide genuine alignment value beyond what random context would.

**Future consideration:** If Claude's architecture shifts toward reasoning-distilled patterns, persona value would shift from identity to context structure. The specific authorities and philosophies we blend would matter less; the structured format and length would matter more. Monitor for this in model updates.
```

- [ ] **Step 2: Verify the file stays well-structured**

Run: Read `.claude/references/context-engineering.md` in full and confirm:
- New section adds relevant architectural context
- Doesn't duplicate authorities.md (that file has the paper's findings; this file has the architectural implication)
- Tone matches the rest of the document

- [ ] **Step 3: Commit**

```bash
git add .claude/references/context-engineering.md
git commit -m "Add persona-model-architecture note to context engineering ref

Tracks that persona effectiveness depends on model training architecture.
Claude is instruction-tuned (personas help). If architecture shifts toward
reasoning-distilled, persona value shifts from identity to structure."
```

---

### Task 9: Final integration verification

**Files:**
- Read: All modified files

This task verifies that all changes are consistent with each other and with the existing ecosystem.

- [ ] **Step 1: Cross-reference check**

Read all modified files and verify:
- authorities.md references Hu et al. and points to the alignment-vs-knowledge split
- persona-template.md has both the design-time split (alignment vs knowledge) and the runtime heuristic (task-type awareness)
- output-structure.md summarizes the architectural placement implication
- SKILL.md principle 9 is consistent with the detail in the reference files
- snap-template.md and snap.md both have the persona-calibration audit step
- context-engineering.md has the forward-proofing note
- No circular references or contradictions between files

- [ ] **Step 2: Dedup check**

Verify that the Hu et al. finding is not stated in full in more than 2 auto-loaded files. The finding should appear:
- In detail in authorities.md (reference, on-demand)
- In detail in persona-template.md (reference, on-demand)
- In detail in context-engineering.md (reference, on-demand)
- As a brief principle in SKILL.md (on-demand, loaded when skill invoked)
- As a brief audit step in snap.md (auto-loaded — just the check, not the research)
- NOT restated in CLAUDE.md, standards.md, or workflow.md

- [ ] **Step 3: Line budget check**

Verify all auto-loaded files stay within budget:
- `.claude/rules/snap.md`: under 60 lines
- `.claude/rules/standards.md`: unchanged
- `.claude/rules/workflow.md`: unchanged
- `CLAUDE.md`: unchanged

Expected: Only snap.md is modified among auto-loaded files, and it gains ~2 net lines.

- [ ] **Step 4: Final commit (if any fixups needed)**

Only if cross-reference or dedup check revealed issues:
```bash
git add -A
git commit -m "Fix integration issues from persona task-awareness changes"
```
