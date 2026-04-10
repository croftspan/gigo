# Boundary-Mismatch QA Patterns — Design Spec

**Design brief:** `.claude/plans/enumerated-tickling-ladybug.md`

---

## Original Request

> Read briefs/01-qa-boundary-mismatch.md — it has the full context from a competitive analysis of revfactory/harness.
>
> TL;DR: Harness has a battle-tested taxonomy of integration bugs that pass build/lint but break at runtime (API shape vs consumer type, naming convention drift across boundaries, state machine completeness gaps). We want to generalize these patterns into GIGO's review pipeline — primarily gigo:verify and gigo:sweep. The patterns need to be domain-agnostic, reference-tier, and integrate with our existing review-criteria generation.

---

## Problem

GIGO's review pipeline checks whether individual files are well-built (craft review) and whether a codebase has structural issues (sweep). Neither checks whether the seams between layers agree. Integration bugs — where each side is correct in isolation but they mismatch at the boundary — pass both gigo:verify and gigo:sweep undetected.

These bugs pass build, pass lint, pass type-checking, and pass code review. They only break at runtime.

---

## Requirements

### R1: Boundary Mismatch Taxonomy Reference

Create `.claude/references/boundary-mismatch-patterns.md` in the GIGO plugin repo.

This file defines 6 abstract boundary-mismatch pattern categories, each with:
- A name and one-sentence definition
- What to look for (the mismatch signature)
- Multi-domain examples (software, fiction, game design, research — at minimum software)
- Detection heuristic: how to determine if this pattern applies to a given project

The 6 categories:

| ID | Name | Definition |
|---|---|---|
| BM-1 | Shape mismatch | Producer's output structure does not match consumer's expected structure |
| BM-2 | Convention drift | Same concept named or formatted differently across layer boundaries |
| BM-3 | Reference mismatch | One layer references a path/ID/key that does not exist in the target layer |
| BM-4 | Contract gap | A definition (state machine, interface, enum) declares more than the implementation covers |
| BM-5 | Temporal shape mismatch | Consumer accesses fields from a response state that has not been reached yet |
| BM-6 | False positive integration | A component exists and is reachable, but its actual interface does not match what callers expect |

The file also includes a "Detection Heuristics" section: given a project's tech stack and layer structure, which patterns are relevant. This section is read by gigo:gigo Step 6.5 during assembly.

This file is GIGO-internal — it stays in the plugin repo's `.claude/references/`, not in target projects.

### R2: Craft Reviewer — Boundary Coherence Section

Add a "Boundary Coherence" section to `skills/verify/references/craft-reviewer-prompt.md`.

**Placement:** After the "Structure" section (currently line 33), before the "CLAUDE.md Compliance" section (currently line 36).

**Content** — 6 checklist items corresponding to BM-1 through BM-6, phrased as review questions. Scoped to the change under review (not the entire codebase). Approximately 10 lines.

**Behavior:** Always-on. Every craft review checks boundary coherence. The section complements (does not replace) project-specific boundary criteria injected via `{DOMAIN_CRITERIA}`.

### R3: Quality Auditor — Boundary Coherence Section

Add a "Boundary Coherence" section to `skills/sweep/references/quality-auditor-prompt.md`.

**Placement:** After the "Consistency" section (currently line 44), before the "Output Format" section (currently line 47).

**Content** — 6 checklist items corresponding to BM-1 through BM-6, phrased as audit checks. Approximately 7 lines.

**Behavior:** Always-on. Every sweep quality audit checks boundary coherence. Since sweep auditors do not have `{DOMAIN_CRITERIA}` injection (they only receive `{SCOPE}`), this is the only boundary-checking mechanism in sweep — it must be self-contained in the prompt.

### R4: Assembly Step 6.5 — Boundary Criteria Generation

Extend Step 6.5 in `skills/gigo/SKILL.md` (currently lines 230-246) to detect project-specific boundary types and generate concrete boundary criteria.

**New step** inserted between existing step 3 ("Read bullets under `## The Standard` from any domain extension files") and step 4 ("Classify each criterion"):

> 3.5. Read `.claude/references/boundary-mismatch-patterns.md` from the GIGO plugin. Based on the project's tech stack and layer structure (already known from the assembly conversation — e.g., "this is a Next.js app with a REST API and PostgreSQL DB"):
>    - Match the project's layers against the Detection Heuristics in the taxonomy
>    - For each relevant boundary type (BM-1 through BM-6), generate 1-2 concrete, project-specific criteria
>    - These criteria join the pool for classification in step 4

The generated criteria are classified into the Craft Review section (they're about whether work is well-built, not whether the right thing was built). They appear under a "Boundary Coherence" subsection within Craft Review Criteria.

Example output for a Next.js + REST API project:
```
## Craft Review Criteria
...existing criteria...

### Boundary Coherence
- API response wrapper shapes match frontend type definitions (BM-1)
- Route paths in navigation components match actual page file paths (BM-3)
- Database column names transform consistently to API response field names (BM-2)
```

### R5: Output Structure Documentation

Extend the "Review Criteria File" section in `skills/gigo/references/output-structure.md` (currently lines 87-94) to document the boundary coherence subsection.

Add after the existing paragraph about staleness checking:

> During generation, also read `.claude/references/boundary-mismatch-patterns.md` to detect which boundary types apply to this project. Add concrete boundary coherence criteria to the Craft Review section. See SKILL.md Step 6.5 for the detection procedure.

### R6: Maintain — Boundary Criteria Regeneration

Extend the "Regenerate review criteria" instruction in `skills/maintain/references/targeted-addition.md` (currently line 57) to mention that boundary criteria are included in the regeneration.

Current text:
> Regenerate review criteria. After writing all changes, regenerate `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo Step 6.5.

Append to this instruction:
> This includes boundary coherence criteria — re-detect boundary types against the current project state.

### R7: Spec — Boundary Map Nudge

Add boundary mapping guidance to the Conventions Section in `skills/spec/SKILL.md` (currently lines 66-68).

Add after the existing Conventions Section paragraph:

> If the spec introduces or modifies integration boundaries (API-to-consumer, DB-to-API, config-to-code), list them under a "Boundaries" heading in the Conventions section so reviewers know which seams to check.

This is a planning-time nudge that feeds forward into review-time checking.

---

## Verb Trace

| Verb | Requirement | Status |
|---|---|---|
| generalize | R1: Taxonomy reference with 6 abstract domain-agnostic categories | ✅ |
| integrate | R2: Craft reviewer section, R3: Quality auditor section, R4: Step 6.5 extension | ✅ |
| identify | R4: Boundary detection during assembly, R7: Boundary mapping during spec writing | ✅ |

---

## Conventions

### File Placement
- New GIGO-internal reference: `.claude/references/boundary-mismatch-patterns.md` (plugin repo)
- All modifications target `skills/` files in the plugin repo source (`~/projects/gigo/skills/`), never the install path

### Naming
- Pattern IDs: BM-1 through BM-6
- Prompt section heading: "Boundary Coherence" (consistent across craft reviewer and quality auditor)
- Review criteria subsection heading: "### Boundary Coherence" (within Craft Review Criteria)

### Prompt Style
- Craft reviewer: questions ("Do types/schemas match...?") — matches existing Defects style
- Quality auditor: declarative checks ("Cross-layer type/schema mismatches") — matches existing checklist style
- Both scoped to changes under review, not full codebase audit

### Taxonomy Style
- Each pattern: name, one-sentence definition, "what to look for" signature, multi-domain examples
- Detection heuristics: conditional ("If the project has X, check for BM-N")
- No code examples in the taxonomy — keep domain-agnostic. Code examples belong in generated review-criteria.md (project-specific)

### Boundaries (this spec's own integration boundaries)
- Taxonomy reference (R1) is read by Step 6.5 (R4) — the detection heuristics section must produce actionable output for the assembly algorithm
- Craft reviewer section (R2) and quality auditor section (R3) use the same 6-category structure as the taxonomy — items must correspond 1:1 to BM-1 through BM-6
- Generated review-criteria.md entries (R4) reference pattern IDs (BM-N) for traceability back to the taxonomy

---

## Scope

**In scope:** 1 new reference file, 6 file modifications (all in GIGO plugin repo).

**Out of scope:**
- Changes to the spec reviewer prompt (spec review checks "right thing built," not boundary coherence)
- Changes to the challenger prompt (boundary coherence is a craft concern, not a feasibility concern)
- A dedicated boundary auditor for sweep (decided against in design brief — fold into quality)
- Runtime detection of boundary types (detection happens at assembly time, not review time)
- Changes to target projects' files (all changes are GIGO-internal)
