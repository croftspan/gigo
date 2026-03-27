# Standards — GIGO

## Philosophy

Draws from Gloaguen et al.'s finding that unnecessary requirements make tasks harder, not easier. Every standard here passed a simple test: "Would removing this cause the skill ecosystem to produce worse output?"

## Quality Gates

- Every rules file stays under ~60 lines. Approaching the cap triggers a move to `.claude/references/`.
- Every rule passes the derivability test: can the agent figure this out from the project files? If yes, don't write it.
- Every persona blends 2-3+ real authorities with specific contributions named. No generic roles.
- Every skill has a clear trigger condition in its description. If Claude can't tell when to invoke it, the description needs work.
- Skill output is tested against operator expectations — not assumed to work because the prompt looks right.

## Anti-Patterns

- **Codebase overviews in rules.** Agents navigate codebases on their own. Directory listings, file descriptions, and structural summaries are fully derivable. Never write them.
- **Restating Claude's training.** Don't tell Claude how markdown works, how to write clean code, or standard language conventions. Only write what's specific to this project.
- **Monotonic growth.** Every session adds, nothing removes. Within weeks the context hurts more than it helps. The Snap exists to prevent this.
- **Generic persona descriptions.** Research shows generic personas ("helpful assistant," "expert developer") perform no better than no persona. Specific, blended philosophies with named authorities are what work (Kong et al., Xu et al.).
- **Reference content in rules.** Extended examples, authority deep-dives, technique catalogs — these belong in `.claude/references/`, loaded on demand. Rules pay tokens on every conversation.
- **Bloated SKILL.md files.** SKILL.md is the hub — it detects mode and points to the right reference. Procedural steps, checklists, and detailed guidance go in `references/` supporting files, loaded on demand. If a SKILL.md mode section is longer than ~5 lines, the procedure belongs in a reference file.
- **Duplicating existing documentation.** If it's in the README, spec.md, or the skill files themselves, don't repeat it in rules. The agent can read those files.

## Forbidden

- Never modify files in the operator's source tree. The skill's footprint lives entirely in `.claude/` and `CLAUDE.md`.
- Never write a rule without explaining *why*. "Don't do X" without consequence is noise.
- Never ship a skill change without testing it against at least one real scenario.
- Never inflate the team roster. One persona if one area of expertise is needed. Ten if ten are needed.

## When to Go Deeper

When evaluating whether a rule earns its token cost, read `.claude/references/context-engineering.md`.
When blending authorities for a new persona, read `.claude/references/authorities.md`.
