# Upgrade Check — Procedure

The project was built with an older version of AA and needs to be brought up to current standards. This isn't about bloat (that's `/smash`) or missing expertise (that's Targeted Addition) — it's about architectural evolution.

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
- Update or create `snap.md` using current template (read `avengers-assemble/references/snap-template.md` for the latest)
- Strengthen snap's overlap check to include cross-file redundancy if missing
- Deduplicate rules that appear in 3+ auto-loaded files — pick the best two homes, remove the rest
- Reformat personas from old labels (`Philosophy`/`Expertise`/`Quality standard`/`Anti-patterns`) to new labels (`Modeled after`/`Owns`/`Quality bar`/`Won't do`) with one authority per line using `+` format
- Tighten personas to 8-10 lines, move detail to `.claude/references/personas/`
- Audit persona entries for knowledge signal — factual specifics, implementation patterns, and technical details that compete with the model's factual recall when loaded as system context. Move to `.claude/references/personas/` or relevant reference files, keeping only alignment signal (quality bars, approach, constraints) in the lean tier
- Add total budget check to snap
- Preserve all existing domain knowledge — upgrading the architecture, not the expertise

After upgrading: "Setup is current. Run `/fury` for your next checkup."
