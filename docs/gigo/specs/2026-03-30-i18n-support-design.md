# i18n Support — Design Spec

GIGO assumes English everywhere. This limits adoption for non-English-speaking operators. The feature adds two-part language configuration during first assembly: **interface language** (conversation) and **output language(s)** (deliverables), with a clean boundary between system files (always English) and operator-facing surfaces (configurable).

## Guiding Constraints

- **System files are English.** CLAUDE.md, `.claude/rules/*`, `.claude/references/*` (except language.md), approval markers, checkpoint markers, plan files — all English. These are instructions for Claude, not operator-facing content.
- **Three language domains.** System (English), Interface (operator's conversation language), Output (deliverable languages). Every surface belongs to exactly one domain.
- **Zero token tax.** Language configuration lives in `.claude/references/language.md` — read on demand, never auto-loaded.
- **Language enforcement flows through the spec.** Reviewers don't need language-specific logic. If the spec says "produce in Spanish," the spec reviewer catches a missing Spanish version the same way it catches any missing requirement.
- **Backward compatible.** Missing language.md defaults to English for both interface and output. Every pre-i18n project works unchanged.
- **Minimal template changes.** Reviewer prompt templates stay untouched. Worker templates get one line. The architecture carries the feature, not template complexity.

---

## Part 1: Storage — `.claude/references/language.md`

### Format

```markdown
# Language Configuration

interface: es
output: [en, es, sl]
```

Two fields. `interface` is a single language code. `output` is an array (one or many). Both use IETF language tags (en, es, fr, pt, zh, ja, ko, de, sl, etc.).

### Reading Pattern

Every skill that produces operator-facing conversation reads this file once at startup. Fallback: if the file doesn't exist, both default to `en`. No error, no warning.

Skills that read language.md:
- `gigo:gigo` — writes it during assembly, reads it if re-invoked
- `gigo:blueprint` — Phase 1 (explore context)
- `gigo:execute` — before dispatching workers and making announcements
- `gigo:verify` — before presenting findings to operator
- `gigo:snap` — when conversing about audit findings
- `gigo:maintain` — at startup
- `gigo:retro` — before presenting analysis and proposals

### Centralized Guard

Add to `skills/gigo/references/output-structure.md` in the Tier 2 section: "Any skill that produces operator-facing conversation must read `.claude/references/language.md` at startup and use the interface language. If the file doesn't exist, default to English." This ensures new skills added via `gigo:maintain` inherit the language requirement without patching individual skill files.

### Token Cost

Zero always-on cost. ~10 tokens per skill invocation to read the file.

---

## Part 2: Assembly Flow — Language Configuration Step

### Position

Between "First Step: Check What Exists" and "Step 1: Listen and Ask" in `skills/gigo/SKILL.md`.

### Procedure

**File:** `skills/gigo/SKILL.md`

After the "Check What Exists" section and before Step 1, add a "Language Configuration" section:

1. **Detect language.** Read the operator's initial description. If non-English, note the detected language.

2. **Ask interface language.** Use `AskUserQuestion` with options:
   - If non-English detected: lead with that language. "Veo que escribes en español. Quieres que sigamos en espanol?"
   - If English or uncertain: "What language should we work in?" with options: English (recommended), Spanish, French, Portuguese, Chinese, Japanese, Korean, German, Other (type your own).
   - The question itself is asked in the detected language if non-English, or English if uncertain.

3. **Ask output language.** Use `AskUserQuestion`: "What language(s) should your project's output be in?" with options: Same as conversation language (default), specify languages (comma-separated). The question is in the interface language chosen in step 2.

4. **Write `.claude/references/language.md`** with the chosen preferences.

5. **Switch.** All subsequent conversation happens in the interface language.

### Skippable

Both questions are skippable. If the operator skips or says "pass," default to English for both. This follows the existing pattern where every question in Step 1 is skippable.

### When language.md is written

language.md is written once during the Language Configuration step (before Step 1), so the conversation switches to the interface language immediately. It is NOT re-written in Step 6. Step 6's "files written" summary should list it alongside the other files for the operator's awareness, but the file already exists on disk.

---

## Part 3: Skill-by-Skill Language Handling

### gigo:blueprint

**File:** `skills/blueprint/SKILL.md`

**Phase 1 addition.** After the existing "Read CLAUDE.md" bullet, add: "Read `.claude/references/language.md` if it exists. Conduct all conversation in the interface language. If the file doesn't exist, default to English."

**Phase 5 (Write Spec) addition.** After the existing "Save to `docs/gigo/specs/...`" instruction, add: "Write the spec in the primary output language (first in the output array from language.md). If multi-language output is configured (output array has 2+ languages), include a Language Requirements section in the spec specifying which deliverables need which languages."

Example Language Requirements section for a spec:
```markdown
## Language Requirements

This project produces deliverables in: English (primary), Spanish, Slovenian.

- User-facing documentation: all three languages
- Code comments and commit messages: English
- UI strings: all three languages
- API responses: all three languages

Each implementation plan task specifies which languages apply.
```

**Phase 8 (Write Plan) addition.** After the existing "Save to `docs/gigo/plans/...`" instruction, add: "Plans are written in English (operational instructions). For tasks that produce user-facing deliverables, include `Output languages:` from language.md. Example: `**Output languages:** en, es, sl`."

**Challenger/fact-checker findings.** No template changes. Subagents run their English templates. The blueprint lead presents findings to the operator in the interface language. This is natural — the lead already interprets and presents, not passes through verbatim.

### gigo:execute

**File:** `skills/execute/references/teammate-prompts.md`

**Tier 1 worker template.** After the `## Context` section, add:

```
## Output Language
[Output language(s) from .claude/references/language.md. If the project
has non-English output languages, state them here: "Output language(s):
es, sl. Produce all user-facing deliverables in the specified language(s).
Code, commit messages, and internal comments remain in English."
If language.md doesn't exist or output is English-only, omit this section.]
```

This follows the existing bracketed-instruction pattern used elsewhere in teammate-prompts.md (e.g., `[FULL TEXT of task from plan]`, `[Where this fits, dependencies]`). The lead reads language.md and fills or omits the section accordingly.

**Tier 3 agent team template.** Same addition.

**Phase announcements and operator communication.** The execute lead reads language.md at startup and conducts all operator-facing conversation in the interface language. No template change needed — this is instruction to the lead, not to workers.

### gigo:verify

**File:** `skills/verify/SKILL.md`

**Opening section addition.** After the existing "No character voice. Direct, adversarial, evidence-based." line, add: "Read `.claude/references/language.md` if it exists. Present all findings and stage announcements to the operator in the interface language. Reviewer subagents operate in English — their templates and criteria are system-internal. If the file doesn't exist, default to English."

**Reviewer templates.** No changes to `spec-reviewer-prompt.md`, `craft-reviewer-prompt.md`, or `spec-plan-reviewer-prompt.md`. Language enforcement flows through the spec: if the spec says "produce in Spanish" and the work is in English, the spec reviewer catches it as a missing requirement.

**Review-criteria.md.** Stays in English. It's a system reference consumed by English reviewer templates via `{DOMAIN_CRITERIA}` injection.

### gigo:snap

**File:** `skills/gigo/references/snap-template.md`

Add check 12 to the audit template after check 11:

```markdown
**12. Language check.** If `.claude/references/language.md` exists, verify it's
still accurate. If the project's language needs have changed (new audiences,
expanded markets, shifted team composition), offer to update. If the file is
missing and the project has non-English operators or output requirements, offer
to create it.
```

### gigo:retro

**File:** `skills/retro/SKILL.md`

**Opening addition.** Add: "Read `.claude/references/language.md` if it exists. Present all analysis findings, proposals, and conversation in the interface language. If the file doesn't exist, default to English."

### gigo:maintain

**File:** `skills/maintain/references/upgrade-checklist.md`

Add two rows to the feature comparison table:

```
| Language configuration | `.claude/references/language.md` exists with interface and output preferences | No language.md (pre-i18n project). Ask operator if they want language configuration. |
| Snap language check | `.claude/rules/snap.md` includes check 12 (language configuration freshness) | Snap has 11 or fewer checks. Add check 12 from current template. |
```

---

## Part 4: Multi-Language Output

When `output` has multiple languages:

**Specs** are written in the primary output language (first in the array). They include a Language Requirements section specifying per-deliverable language rules.

**Plans** are written in English. Each task that produces user-facing deliverables includes `Output languages:` from language.md. The plan doesn't duplicate tasks per language — it specifies the language requirement and the worker handles production.

**Workers** receive the output languages via the one-line addition to their prompt. How they produce multi-language output is task-dependent: a documentation task might write English first then translate, while a UI strings task might populate a locale file per language.

**Reviewers** check that all specified languages were produced, treating missing languages as spec deviations.

---

## Part 5: Boundaries and Edge Cases

### What stays English always
- CLAUDE.md (team roster, personas, autonomy model)
- `.claude/rules/*` (standards, workflow, snap, extensions)
- `.claude/references/*` (except language.md is language-neutral by nature)
- Approval markers: `<!-- approved: spec ... -->`
- Checkpoint markers: `<!-- checkpoint: task-1 ... -->`
- Plan files (`.claude/plans/*` and `docs/gigo/plans/*`)
- Worker addendums ("What Was Built" sections in plans)
- Triage category labels (auto-fix, ask-operator, accept)
- Git commit messages (conventional commits in English)

### What switches to interface language
- All conversation output (phase announcements, questions, proposals)
- Review findings as presented to operator (not the raw subagent output)
- Snap audit conversation
- AskUserQuestion prompts
- Error messages and status updates

### What follows output language(s)
- Specs (primary output language)
- Creative deliverables (fiction, documentation, copy)
- User-facing code output (UI strings, API error messages, user documentation)

### Edge case: operator changes language preference mid-project
Use `gigo:maintain` to update language.md. Existing specs and plans don't retroactively change. New deliverables follow the updated preference.

### Edge case: reviewer can't evaluate non-English content quality
Claude is multilingual. Craft review of Spanish prose, Japanese documentation, or Slovenian UI strings works without template modification. If a specific language is genuinely outside Claude's capability (rare), the reviewer should flag this rather than produce low-quality review.

---

## Conventions

- Language codes: IETF tags (en, es, fr, pt, zh, ja, ko, de, sl, etc.)
- language.md format: YAML-like key-value. `interface:` single code. `output:` bracketed array.
- Default: English for both when language.md is absent.
- Spec Language Requirements section: appears after the main spec content, before Conventions.
- Plan output language note: appears per-task as `**Output languages:** en, es, sl` — bold label, comma-separated codes.
- Worker prompt language section: appears after `## Context`, before `## Before You Begin`.

<!-- approved: spec 2026-03-30T00:54:17 by:Eaven -->
