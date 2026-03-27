# Restructure — Procedure

The project's setup has grown unwieldy — bloated rules, derivable content loading on every conversation, files that overlap, institutional knowledge buried where it can't be found. Your job is to assess, plan, get approval, then execute.

**Why projects need restructuring:** Rules accumulate, overlap, and outlive their usefulness. What started lean becomes heavy. That's normal — it happens to every project.

For a worked example of the full triage process, read `example-triage.md`.

## Phase 1: Read Everything

Before forming any opinions, read the full landscape:

- `CLAUDE.md` — the main project file
- Every file in `.claude/rules/` — the auto-loaded rules
- Any `.claude/references/`, `docs/`, or equivalent knowledge directories
- Project structure — what directories exist, what the project actually does
- Recent git history — how long has this been going, how active, what kind of work
- Any governance docs, vault structures, or knowledge stores that exist

Understand: what is this project, what are its concerns, who works on it, and how is the setup currently organized.

## Phase 2: Measure

For every rules file, evaluate against these checks:

**1. Line count.** Flag anything over ~60 lines. Note the exact count.

**2. Derivability check.** For each rule or section within a file, ask: "Can the agent figure this out by reading the project files?" Don't guess — actually read the source files to verify. A rule about API conventions is derivable if the conventions are obvious from reading the controllers. A rule about intentional design differences (like "these two behaviors are different on purpose, don't fix this") is NOT derivable.

**3. Relevance check.** Does this rule apply to ALL work in the project, or only to specific types of work? A coding standard applies to all code. A schema verification protocol only applies when touching the data layer. A branding deliverable standard only applies when producing brand work.

**4. Overlap check.** Do multiple rules say the same thing in different words? Do multiple files cover the same ground? Check for cross-file redundancy — the same rule appearing in more than two auto-loaded files. A rule should live in at most two auto-loaded locations: once briefly in CLAUDE.md, once fully in the relevant rules file.

**5. Staleness check.** Is this still accurate? Has the project evolved past it? Were there early-project rules that made sense at the time but the codebase now makes obvious?

**6. Persona calibration check.** For each persona in CLAUDE.md: does it contain domain-knowledge content (factual specifics, implementation patterns) that belongs in references? Persona entries should be alignment signal only — quality bars, approach, constraints. Domain knowledge competes with the model's factual recall when loaded as system context (Hu et al., 2026).

**7. Overwatch check.** Does `workflow.md` have a Persona Calibration section and an Overwatch section? If 3+ domain personas, does CLAUDE.md include The Overwatch? Does `.claude/references/overwatch.md` exist? Are "When to Go Deeper" pointers task-specific (naming the observable task and what to check) rather than generic? Read `gigo/references/persona-template.md` → "The Overwatch" for templates.

**8. Pipeline check.** Does the workflow encode plan → execute → review? Are review stages intact? Does the workflow reference `gigo:plan` or equivalent planning? Does snap run as part of the pipeline? Flag missing or broken stages.

## Phase 3: Triage

Categorize every piece of content:

| Category | What it means | Action |
|---|---|---|
| **Gold** | Non-derivable, applies to all work, file is under ~60 lines | Keep exactly where it is |
| **Gold but heavy** | Non-derivable, but the file is over the cap | Split: core stays in rules, detail moves to references with "When to Go Deeper" pointer |
| **Gold but narrow** | Non-derivable, but only applies to some types of work | Move to references with "When to Go Deeper" pointer in the relevant rules file |
| **Consolidation candidate** | Multiple small files covering related ground | Merge into one lean file |
| **Derivable** | The codebase now makes this obvious | Let it go — it served its purpose |
| **Stale** | Was true once, isn't anymore | Let it go |
| **Missing** | Gap the project needs but doesn't have | Flag for addition |

Special attention to these high-value patterns — preserve them aggressively:

- **Gotchas / foot-guns** — non-derivable, prevent real bugs. These are the most valuable lines in any rules file.
- **Intentional design differences** — "don't fix this, it's different on purpose." These save hours of misguided refactoring.
- **Banned lists / anti-patterns** — what to never do. Not discoverable from reading code.
- **Quality bars** — what "good" looks like in this domain. Opinionated, non-derivable.
- **Blended philosophies** — who this project draws from and why. The most valuable content the skill produces.

## Phase 4: Present the Plan

Present findings to the operator as a clear before/after:

**The Assessment:**
- Total auto-loaded lines (current)
- Number of files
- Specific issues found (over-cap files, derivable content, overlaps, stale rules, gaps)

**The Plan:**
- What stays (and why it's earning its place)
- What splits (over-cap files -> rules core + reference detail)
- What moves to references (narrow rules with "When to Go Deeper" pointers)
- What consolidates (small files merging into lean grouped files)
- What gets let go (derivable or stale, with acknowledgment of why it existed)
- What's missing (gaps to flag for `gigo:maintain` targeted addition or `gigo:gigo`)

**The Numbers:**
- Before: X files, Y lines auto-loaded
- After: X files, Y lines auto-loaded (Z% reduction)
- New reference files created

**Scope rule:** The skill only reads project files for assessment. It only writes to `.claude/` (rules, references, backup) and `CLAUDE.md` at the project root. It never creates, modifies, or deletes anything else in the project's source tree.

**Wait for approval.** Nothing gets touched until the operator says go.

## Phase 5: Execute

Once approved, do the restructuring:

1. **Back up first** — create `.claude/pre-restructure-backup-{YYYY-MM-DD}/`, copy `.claude/` and `CLAUDE.md` into it, write `backup-log.md` with date, git SHA, file list with line counts, and the assessment summary. Add to `.gitignore`. Never overwrite or delete existing backups. This is not optional.
2. **Create reference files** — write new `.claude/references/` files with content being moved out of rules
3. **Write consolidated files** — create the new merged rules files
4. **Update existing files** — add "When to Go Deeper" pointers, trim over-cap files
5. **Add snap** — if no `snap.md` exists, create one using the template from `gigo/references/snap-template.md`, customized for this project's domain
6. **Restore pipeline** — if plan → execute → review pipeline is missing or broken, add it to workflow. Ensure snap runs as part of the pipeline. Add review stage references where appropriate.
7. **Add Overwatch** — if missing, add Persona Calibration and domain-adapted Overwatch sections to `workflow.md`, create `.claude/references/overwatch.md`, and add The Overwatch persona to CLAUDE.md if 3+ domain personas. Read `gigo/references/persona-template.md` → "The Overwatch" for templates.
8. **Remove old files** — delete the files that were consolidated or emptied
9. **Update CLAUDE.md** — if CLAUDE.md references files that moved or merged, update the references

## Phase 6: Assessment

After the structural cleanup, briefly assess the expertise layer:

- Does CLAUDE.md have specific, opinionated personas with blended philosophies, or generic role descriptions like "you are a senior developer"?
- Are the quality bars concrete and domain-specific, or vague?
- Are there anti-patterns and banned lists, or only positive rules?
- Are there reference files with deep authority knowledge, or is everything surface-level?
- Do persona entries contain only alignment signal (quality bars, approach, constraints), or are they carrying domain knowledge that belongs in references?
- Does the project have the Overwatch system (Persona Calibration + Overwatch section + overwatch.md reference + The Overwatch at 3+)?
- Is the plan → execute → review pipeline intact in the workflow?

If the expertise layer is weak or generic, suggest next steps:

> "The structure is clean now. But the team is thin — [specific gap]. Run `gigo:gigo` to build the expertise layer on top of this foundation, or use `gigo:maintain` to add specific expertise where you need it."

If the expertise is already strong:

> "Structure is clean, team is solid. Run `gigo:maintain` whenever you need a checkup."
