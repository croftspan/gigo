# Boundary-Mismatch QA Patterns — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-10-boundary-mismatch-patterns-design.md`

**Goal:** Add cross-boundary coherence checking to GIGO's review pipeline

**Architecture:** Two-tier integration — universal boundary sections in reviewer prompts (always-on) + project-specific boundary criteria generated during assembly (injected via {DOMAIN_CRITERIA}). Backed by a taxonomy reference file that defines the 6 pattern categories.

---

### Task 1: Create Boundary Mismatch Taxonomy Reference

**blocks:** 4
**blocked-by:** []
**parallelizable:** false

**Files:**
- Create: `.claude/references/boundary-mismatch-patterns.md`

- [x] **Step 1: Write the taxonomy reference file**

```markdown
# Boundary Mismatch Patterns

A boundary mismatch is a bug where two representations of the same concept — maintained in different layers or files — disagree. Each side is correct in isolation. The bug only appears when they connect. These bugs pass build, lint, type-checking, and single-file code review. They break at runtime.

This reference defines the pattern categories and detection heuristics. Read by gigo:gigo Step 6.5 during assembly to generate project-specific review criteria.

---

## Pattern Categories

### BM-1: Shape Mismatch

**Definition:** Producer's output structure does not match consumer's expected structure.

**What to look for:** A function, API, or service returns data in one shape (e.g., wrapped in `{ data: [...] }`) while the consumer expects a different shape (e.g., unwrapped `T[]`). Type systems may mask this when generics or `any` types are involved.

**Examples:**
- Software: API returns `{ data: User[] }`, frontend destructures as `User[]` directly
- Software: CLI tool outputs JSON with a `results` wrapper, parser expects bare array
- Fiction: Character described as left-handed in chapter 3, uses right hand in chapter 12
- Research: Paper claims "significant at p<0.05" but cited study reports p=0.08

### BM-2: Convention Drift

**Definition:** Same concept named or formatted differently across layer boundaries.

**What to look for:** A field, variable, or concept uses one naming convention in its source layer and a different one where it's consumed, without a consistent transformation rule. Each layer follows its own convention correctly.

**Examples:**
- Software: Database column `user_name` (snake_case), API response field `userName` (camelCase), frontend prop `UserName` (PascalCase) — no serializer handling the transform
- Software: i18n key `error.not_found` in translation file, code references `error.notFound`
- Game design: Asset named `player_idle_01.png` in files, referenced as `playerIdle01` in code

### BM-3: Reference Mismatch

**Definition:** One layer references a path, ID, key, or name that does not exist in the target layer.

**What to look for:** A string literal or identifier in one file points to something in another file or system that has been renamed, moved, or never existed. Often caused by renaming in one place without updating references.

**Examples:**
- Software: Navigation links to `/dashboard/create`, actual page file is at `/dashboard/new`
- Software: Config key `redis.cache_ttl` referenced in code, config file has `redis.cacheTTL`
- Game design: Level data references `enemy_boss_phase2` sprite, asset folder has `boss_phase2_enemy`
- Fiction: Chapter 8 references "the letter from Madrid" — no letter scene exists

### BM-4: Contract Gap

**Definition:** A definition (state machine, interface, enum, schema) declares more states, variants, or methods than the implementation covers.

**What to look for:** A formal definition (type, enum, state diagram, interface) lists N possibilities, but the code handling those possibilities only covers N-M of them. The definition is correct; the implementation is incomplete.

**Examples:**
- Software: Enum defines `PENDING | APPROVED | REJECTED | EXPIRED`, switch statement handles 3 of 4
- Software: Interface declares 5 methods, implementing class has 4
- Game design: State machine defines transitions A→B→C→D, code implements A→B→C only
- Fiction: Outline lists 5 subplots, manuscript resolves 4

### BM-5: Temporal Shape Mismatch

**Definition:** Consumer accesses data fields from a response state that has not been reached yet.

**What to look for:** An async operation returns different shapes at different stages (e.g., `202 Accepted` with `{ status }` vs final `200 OK` with `{ status, results }`). The consumer accesses fields from the final shape on the intermediate response.

**Examples:**
- Software: Polling endpoint returns `{ status: "processing" }`, consumer accesses `response.data.failedIndices` (only present when status is "complete")
- Software: WebSocket sends partial updates during processing, handler assumes every message has the `summary` field from the final message
- Game design: Server sends `game_starting` event, client reads `scores` array (only present after `game_ended`)

### BM-6: False Positive Integration

**Definition:** A component exists and is reachable, but its actual interface does not match what callers expect.

**What to look for:** An integration test confirms "the endpoint responds" or "the component renders," but the response shape, props interface, or method signature has changed since the caller was written. Existence checks pass; behavior is wrong.

**Examples:**
- Software: API endpoint exists and returns 200, but response body changed from `{ users }` to `{ data: { users } }` — consumer gets `undefined`
- Software: React component accepts `onSubmit` prop, parent passes `onSave` — renders without error, callback never fires
- Research: Citation exists and is a real paper, but the cited claim is from a different paper

---

## Detection Heuristics

During assembly (gigo:gigo Step 6.5), use these heuristics to determine which patterns apply:

| Project has... | Check for... |
|---|---|
| API + consumer (frontend, mobile, CLI) | BM-1 (shape), BM-2 (naming), BM-6 (false positive) |
| Database + application layer | BM-2 (naming conventions across DB↔code) |
| Routing/navigation + page/view files | BM-3 (route references) |
| Config files + code that reads them | BM-3 (config key references) |
| State machines, enums, or formal interfaces | BM-4 (contract completeness) |
| Async operations (polling, webhooks, streaming) | BM-5 (temporal shapes) |
| Multi-service or microservice architecture | BM-1, BM-2, BM-6 (all cross-service boundaries) |
| i18n/localization | BM-2 (key naming), BM-3 (key existence) |
| Any multi-layer system | BM-6 (always relevant as a meta-check) |

**For non-software domains:** Identify the analogous boundaries (chapters↔character bible, rules↔implementation, claims↔citations) and map to the abstract pattern. BM-6 applies universally — "it exists" never guarantees "it connects correctly."

When generating criteria, produce 1-2 concrete, project-specific checks per relevant pattern. Use the project's actual layer names and technology (e.g., "Prisma model field names transform consistently to GraphQL response fields" not "naming is consistent").
```

- [x] **Step 2: Verify file is within GIGO plugin source**

Confirm the file was written to `~/projects/gigo/.claude/references/`, NOT `~/.claude/plugins/`.

- [x] **Step 3: Commit**

```bash
git add .claude/references/boundary-mismatch-patterns.md
git commit -m "feat: add boundary-mismatch pattern taxonomy reference"
```

#### What Was Built
- **Deviations:** None. File written verbatim from plan spec, confirmed inside gigo source worktree (not `~/.claude/plugins/`).
- **Review changes:** None. Stage 1 spec-compliant. Stage 2 flagged two confidence-80/82 phrasing concerns (BM-4 "N-M of them", BM-5 scope), both triaged as accept — they critique the approved plan text, not the implementation.
- **Notes for downstream:** Taxonomy file is consumed by Step 6.5 — the `## Detection Heuristics` section (9-row mapping) is the key input for boundary-type matching, and the closing instruction about project-specific layer names is what Step 6.5 should honor when generating criteria. **Amendment after Task 4:** file was relocated to `skills/gigo/references/boundary-mismatch-patterns.md` during Task 4's fix cycle — Step 6.5's relative path must resolve inside the skill, not the operator project. Task 5 docs must use the new path.

---

### Task 2: Add Boundary Coherence to Craft Reviewer

**blocks:** []
**blocked-by:** []
**parallelizable:** true (with Task 3)

**Files:**
- Modify: `skills/verify/references/craft-reviewer-prompt.md`

- [x] **Step 1: Insert Boundary Coherence section into review checklist**

In the template (inside the `~~~` block), insert the following after the **Structure:** section (after line 34 "Did this change create or significantly grow large units?" — the last Structure bullet) and before the **CLAUDE.md Compliance:** section (line 36):

```
**Boundary Coherence:**
Look for mismatches between different representations of the same concept
across layers or boundaries that this change touches:
- Do types/schemas match what the producing layer actually returns?
- Do names stay consistent (or consistently transform) across boundaries?
- Do references (paths, routes, keys, IDs) point to things that exist?
- If contracts are defined (state machines, interfaces, enums), are they fully implemented?
- At async boundaries, does the consumer handle all response states (not just the final one)?
- Does "it exists" also mean "it connects correctly"?

Focus on boundaries this change introduces or modifies. Don't audit the
entire codebase — check that this change's seams are coherent.
```

- [x] **Step 2: Commit**

```bash
git add skills/verify/references/craft-reviewer-prompt.md
git commit -m "feat: add boundary coherence section to craft reviewer prompt"
```

#### What Was Built
- **Deviations:** None. Block inserted verbatim between Structure and CLAUDE.md Compliance using text anchors.
- **Review changes:** None. Both review stages clean on first pass.
- **Notes for downstream:** Craft reviewer now has an always-on Boundary Coherence section with 6 question-style bullets mapping to BM-1 through BM-6. Projects without `review-criteria.md` still get this baseline; projects with it also get the injected `{DOMAIN_CRITERIA}` underneath. When Task 4 classifies generated criteria into the Craft Review section, the "Boundary Coherence" subsection header it uses should align with this prompt's wording.

---

### Task 3: Add Boundary Coherence to Quality Auditor

**blocks:** []
**blocked-by:** []
**parallelizable:** true (with Task 2)

**Files:**
- Modify: `skills/sweep/references/quality-auditor-prompt.md`

- [x] **Step 1: Insert Boundary Coherence section into audit checklist**

Inside the code block, insert the following after the **Consistency** section (after line 45 "for the same kind of operation)" — the end of the wrapped bullet) and before the **Output Format** section (line 47):

```
### Boundary Coherence
- Cross-layer type/schema mismatches (producer returns X, consumer expects Y)
- Naming convention drift at layer boundaries (different cases or conventions)
- Reference mismatches (paths, routes, keys, IDs pointing to non-existent targets)
- Partial contract implementation (defined transitions/variants/methods not all implemented)
- Async boundary confusion (accessing fields from response states not yet reached)
- Existence-without-connection (component exists but interface doesn't match callers)
```

- [x] **Step 2: Commit**

```bash
git add skills/sweep/references/quality-auditor-prompt.md
git commit -m "feat: add boundary coherence section to quality auditor prompt"
```

#### What Was Built
- **Deviations:** None to the specified insertion.
- **Review changes:** One auto-fix applied. Stage 2 craft review (conf 88) caught a partial-contract gap: the `**Type:**` enum in `## Output Format` listed `dead-code / error-handling / duplication / complexity / consistency` but not `boundary-coherence`. Fix commit appended `/ boundary-coherence` to that line — findings from the new section now have a valid type slug to report under.
- **Notes for downstream:** The sweep quality auditor prompt now has both (a) a Boundary Coherence checklist section and (b) `boundary-coherence` in the Type enum. Any future checklist additions to this prompt must also update the enum — Task 5's docs updates don't touch this file, but it's worth remembering for Snap audits. Meta note: the finding is itself a BM-4 (Contract Gap) — the review caught boundary-mismatch pattern #4 inside the very task implementing boundary-mismatch detection.

---

### Task 4: Extend Assembly Step 6.5

**blocks:** 5
**blocked-by:** 1
**parallelizable:** false

**Files:**
- Modify: `skills/gigo/SKILL.md`

- [x] **Step 1: Insert boundary detection step into Step 6.5**

In the Step 6.5 section (starting at line 230), insert a new step between existing step 3 ("Read bullets under `## The Standard` from any domain extension files") and step 4 ("Classify each criterion"). Renumber subsequent steps.

The current numbered steps are:
```
1. Read each persona's `Quality bar:` line...
2. Read bullets under `## Quality Gates`...
3. Read bullets under `## The Standard`...
4. Classify each criterion...
5. Deduplicate within each section
6. Write to `.claude/references/review-criteria.md`
```

Insert after step 3:

```
4. Read `.claude/references/boundary-mismatch-patterns.md` from the GIGO plugin. Match the project's tech stack and layers against the Detection Heuristics table. For each relevant boundary type, generate 1-2 concrete, project-specific criteria using the project's actual layer and technology names. These join the criteria pool.
```

Then renumber:
- Old step 4 (Classify) → step 5
- Old step 5 (Deduplicate) → step 6
- Old step 6 (Write) → step 7

Also update the classification list in the new step 5 to mention the Boundary Coherence subsection:

After the existing classification bullets, add:
```
   - **Boundary Coherence** (subsection of Craft Review) — about whether layers/boundaries agree
```

- [x] **Step 2: Commit**

```bash
git add skills/gigo/SKILL.md
git commit -m "feat: extend Step 6.5 to generate boundary coherence criteria"
```

#### What Was Built
- **Deviations:** None at implementation time. Step 6.5 got the new numbered step 4 and renumbered 5/6/7, plus the Boundary Coherence classification bullet.
- **Review changes:** Three fixes applied in a follow-up commit after Stage 2 craft review.
  1. **Critical (conf 95, ask-operator → Option A chosen):** The inserted path `.claude/references/boundary-mismatch-patterns.md` wouldn't resolve at runtime — `gigo:gigo` executes inside the operator project, so a relative `.claude/` path lands on the operator's tree (which has no taxonomy file). Fix: relocated the taxonomy from `.claude/references/` to `skills/gigo/references/boundary-mismatch-patterns.md` (colocated with its only consumer) and rewrote Step 6.5 to use the skill-relative path `references/boundary-mismatch-patterns.md`. This matches how every other reference in `skills/gigo/SKILL.md` is read (enforcement-mode.md, output-structure.md, snap-template.md, etc.).
  2. **Important (conf 80, auto-fix):** Changed "the Detection Heuristics table" to reference the `## Detection Heuristics` section by exact heading.
  3. **Important (conf 82, auto-fix):** Rewrote the classification bullet from `**Boundary Coherence** (subsection of Craft Review) — about whether layers/boundaries agree` to `**Boundary Coherence** — about whether layers/boundaries agree (file under Craft Review)` to restore parallel structure with the three sibling bullets.
- **Notes for downstream:** The taxonomy file is now at `skills/gigo/references/boundary-mismatch-patterns.md`, NOT `.claude/references/`. Task 5's output-structure.md update must reflect this — the plan's original Step 1 text (line 291) pointed to the old path and has been corrected below. The meta-lesson: this task was a BM-1 (Shape Mismatch) between "where SKILL.md's relative paths resolve in theory" and "where they resolve at runtime inside the plugin" — caught by craft review before it shipped.

---

### Task 5: Update Supporting Documentation

**blocks:** []
**blocked-by:** 4
**parallelizable:** false

**Files:**
- Modify: `skills/gigo/references/output-structure.md`
- Modify: `skills/maintain/references/targeted-addition.md`
- Modify: `skills/spec/SKILL.md`

- [x] **Step 1: Extend output-structure.md Review Criteria File section (R5)**

In the "Review Criteria File" section (starting at line 87), after the paragraph ending with "`gigo:maintain` and `gigo:snap` both check for staleness." (line 96 — end of that paragraph), insert:

```
During generation, also read `skills/gigo/references/boundary-mismatch-patterns.md`
(colocated with the gigo skill) to detect which boundary types apply to this project.
Add concrete boundary coherence criteria to the Craft Review section under a
"Boundary Coherence" subsection. See SKILL.md Step 6.5 for the detection procedure.
```

> **Note after Task 4:** The taxonomy file lives at `skills/gigo/references/boundary-mismatch-patterns.md`, not `.claude/references/`. This Step 1 text was corrected during Task 4's fix cycle to use the new location.

- [x] **Step 2: Extend maintain targeted-addition.md (R6)**

On line 57, the current text reads:
```
- **Regenerate review criteria.** After writing all changes, regenerate `.claude/references/review-criteria.md` using the same algorithm as gigo:gigo Step 6.5. If the file doesn't exist, create it. If it does, regenerate from scratch (don't append).
```

Append to the end of this line (same bullet):
```
 This includes boundary coherence criteria — re-detect boundary types against the current project state.
```

- [x] **Step 3: Add boundary map nudge to spec/SKILL.md (R7)**

In the Conventions Section (lines 66-68), after the paragraph ending with "the spec is all they get.", add:

```
If the spec introduces or modifies integration boundaries (API-to-consumer, DB-to-API, config-to-code), list them under a "Boundaries" heading in the Conventions section so reviewers know which seams to check.
```

- [x] **Step 4: Commit**

```bash
git add skills/gigo/references/output-structure.md skills/maintain/references/targeted-addition.md skills/spec/SKILL.md
git commit -m "docs: update supporting files for boundary coherence integration"
```

#### What Was Built
- **Deviations:** None. Three surgical insertions made verbatim against the plan's updated text (which was corrected during Task 4's fix cycle to use `skills/gigo/references/boundary-mismatch-patterns.md`).
- **Review changes:** None. Both review stages clean on first pass.
- **Notes for downstream:** `output-structure.md` now documents the boundary step inside the Review Criteria File section; `targeted-addition.md` single-line bullet preserved; `spec/SKILL.md` nudge lives inside the Conventions Section subsection. Two below-threshold observations from craft review (both ~55 confidence, accept): (1) `output-structure.md:91-92` still says "Classifies each into three sections: Spec Compliance Criteria, Craft Review Criteria, Challenger Criteria" — Boundary Coherence is a subsection of Craft Review, so this isn't wrong, but a future Snap could consider tightening that phrasing; (2) the new paragraph uses repo-relative `skills/gigo/references/...` while SKILL.md Step 6.5 uses skill-relative `references/...` — mitigated by the "colocated with the gigo skill" parenthetical.

---

**Done when:** All 6 BM categories are defined in the taxonomy, both reviewer prompts include boundary coherence sections, Step 6.5 generates project-specific boundary criteria, and supporting documentation reflects the new capability. `gigo:verify` and `gigo:sweep` catch boundary mismatches on any project.

<!-- approved: plan 2026-04-10T19:23:20 by:Eaven -->
