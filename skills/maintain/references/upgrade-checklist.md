# Upgrade Check — Procedure

The project was built with an older version and needs to be brought up to current standards. This isn't about bloat (that's Restructure / Mode 3) or missing expertise (that's Targeted Addition) — it's about architectural evolution.

## Step 1: Compare Against Current Spec

Read the project's setup and check for these features. Missing ones are upgrade candidates:

| Feature | Current Standard | How to detect it's missing |
|---|---|---|
| "When to Go Deeper" pointers | Every rules file has task-aware links to references | Rules files have generic "References" sections or no pointers at all |
| Cumulative line budget | ~300 lines total across all `.claude/rules/` | No total budget awareness, only per-file caps (or no caps) |
| The Snap protocol | `snap.md` triggers on save/wrap-up, 7-step audit including total budget | Missing snap.md, or snap that says "run at end of every session" (old protocol) |
| Snap overlap check includes cross-file redundancy | Overlap check (#3) explicitly catches the same rule in 3+ auto-loaded files, not just "same thing in different words" | Snap's overlap check only mentions rewording, not cross-file duplication |
| Persona format | `Modeled after` + `Owns` + `Quality bar` + `Won't do`, with optional `Personality`/`Decides by`/`Depth` pointer. Rich tier in `.claude/references/personas/` | Old format uses `Philosophy`/`Expertise`/`Quality standard`/`Anti-patterns` labels, or personas are dense paragraphs instead of scannable bullets |
| Persona line targets | 8-10 lines per persona, max 12 | Personas are 15+ lines in CLAUDE.md |
| Persona content split | Persona entries contain alignment signal only (quality bars, approach, constraints). Domain knowledge lives in `.claude/references/personas/` or reference files | Persona entries in CLAUDE.md contain factual specifics, implementation patterns, or technical details that could be moved to references |
| Two-tier split | `.claude/rules/` (lean) + `.claude/references/` (deep) | Reference-depth content living in rules files, or no `.claude/references/` directory |
| Cross-file dedup | A rule appears in at most 2 auto-loaded locations (brief in CLAUDE.md persona, full in relevant rules file) | Same rule repeated in 3+ auto-loaded files (CLAUDE.md, standards.md, extension, workflow.md) |
| Persona retirement | Snap audits include checking if personas are still needed | No guidance on removing outdated personas |
| Scope rule | Skills only write to `.claude/` and `CLAUDE.md`, never source tree | No scope constraint stated |
| Persona Calibration | `workflow.md` has a Persona Calibration section (presentation vs content task self-assessment) | No calibration section in workflow.md |
| Overwatch section | `workflow.md` has a domain-adapted Overwatch self-check section | No Overwatch section in workflow.md |
| The Overwatch persona | At 3+ domain personas, `CLAUDE.md` includes The Overwatch | 3+ personas but no The Overwatch |
| Overwatch reference | `.claude/references/overwatch.md` exists with the deep adversarial checklist | No overwatch.md reference file |
| Task-specific pointers | "When to Go Deeper" pointers name the observable task AND what to check in the reference | Pointers are generic ("when working on X, read Y") without naming what to look for |
| Snap Overwatch check | Snap audit includes check 9 (Overwatch presence verification) | Snap has 8 or fewer audit checks |
| Pipeline in workflow | Workflow encodes plan → execute → review pipeline | Workflow has no planning or review stages |
| Skill references | Workflow references `gigo:` skills (plan, maintain, snap) | Workflow references old `/` commands or no skill references |
| Snap pipeline check | Snap includes pipeline health check (step 10) | Snap has no pipeline integrity audit |
| Overwatch functional name | Overwatch persona uses functional name (The Overwatch), not character name | Persona still named Hawkeye |
| Review criteria file | `.claude/references/review-criteria.md` exists with domain-specific review criteria | No review-criteria.md, or criteria don't match current personas |
| Snap review criteria check | Snap audit includes check 11 (review criteria currency) | Snap has 10 or fewer audit checks, or no criteria currency verification |
| Language configuration | `.claude/references/language.md` exists with interface and output preferences | No language.md (pre-i18n project). Ask operator if they want language configuration. |
| Snap language check | `.claude/rules/snap.md` includes check 12 (language configuration freshness) | Snap has 11 or fewer checks. Add check 12 from current template. |

## Step 2: Back Up Before Upgrading

Create a timestamped backup before making any changes:

1. Create `.claude/pre-upgrade-backup-{YYYY-MM-DD}/` directory
2. Copy the entire current `.claude/` directory and `CLAUDE.md` into it
3. Write a `backup-log.md` with date, git SHA, file list with line counts, and what's being upgraded
4. Add to `.gitignore` if not already there

**Never overwrite or delete existing backups.** If `.claude/pre-smash-backup-*/` or previous upgrade backups exist, leave them. Each backup is a snapshot in time. They're gitignored and cost nothing.

## Step 3: Present Upgrade Plan

For each missing feature, explain:
- What it is and why it matters
- What specifically will change in the project's files
- Impact on line counts (before/after)

**Wait for approval before making any changes.**

## Step 4: Apply Upgrades

Once approved:
- Add "When to Go Deeper" pointers to existing rules files
- Move reference-depth content from rules to `.claude/references/`
- Update or create `snap.md` using current template (read `gigo/references/snap-template.md` for the latest)
- Strengthen snap's overlap check to include cross-file redundancy if missing
- Deduplicate rules that appear in 3+ auto-loaded files — pick the best two homes, remove the rest
- Reformat personas from old labels (`Philosophy`/`Expertise`/`Quality standard`/`Anti-patterns`) to new labels (`Modeled after`/`Owns`/`Quality bar`/`Won't do`) with one authority per line using `+` format
- Tighten personas to 8-10 lines, move detail to `.claude/references/personas/`
- Audit persona entries for knowledge signal — factual specifics, implementation patterns, and technical details that compete with the model's factual recall when loaded as system context. Move to `.claude/references/personas/` or relevant reference files, keeping only alignment signal (quality bars, approach, constraints) in the lean tier
- Add total budget check to snap
- Add Persona Calibration section to `workflow.md` — read `gigo/references/persona-template.md` → "Task-Type Awareness" for the template, adapt language to the domain
- Add Overwatch section to `workflow.md` — read `gigo/references/persona-template.md` → "The Overwatch" for domain-adapted templates (structured vs creative)
- If 3+ domain personas and no The Overwatch, add The Overwatch persona to `CLAUDE.md` using the template from `gigo/references/persona-template.md` → "The Overwatch"
- Create `.claude/references/overwatch.md` with the deep adversarial checklist
- Upgrade generic "When to Go Deeper" pointers to task-specific: name the observable task, name the reference file, name what to check
- Add Overwatch audit check (check 9) to `snap.md` if missing
- Preserve all existing domain knowledge — upgrading the architecture, not the expertise
- Generate `.claude/references/review-criteria.md` using the extraction algorithm from gigo:gigo Step 6.5

After upgrading: "Setup is current. Run `gigo:maintain` for your next checkup."
