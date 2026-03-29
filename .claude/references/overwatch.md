# Overwatch — Deep Adversarial Checklist

## The Core Question

"Did you actually do what you claimed, or did you describe doing it?"

## Per-Domain Checks

### Skill Design Claims

- [ ] You said "the skill triggers correctly" — did you invoke it, or did you read the description and assume?
- [ ] You said "under 500 lines" — did you count, or estimate?
- [ ] You said "supporting file handles this" — does the SKILL.md actually point to it, or is it orphaned?
- [ ] You said "frontmatter is precise" — would Claude's task-matching fire on a real user request?

### Context Architecture Claims

- [ ] You said "non-derivable" — can the agent figure this out by reading the skill files and CLAUDE.md?
- [ ] You said "under 60 lines" — did you count the rules file?
- [ ] You said "moved to references" — is there a "When to Go Deeper" pointer from the rules file?
- [ ] You said "quality bar checklist" — are the items actually checklistable, or vague guidance?

### Pipeline Claims

- [ ] You said "workers run bare" — did you check the subagent prompt actually excludes personas/rules?
- [ ] You said "two-stage review" — are both stages present and sequential, or did someone merge them?
- [ ] You said "plan mode for design" — does the blueprint skill actually call EnterPlanMode?
- [ ] You said "parallel dispatch" — are the tasks actually marked parallelizable with no file conflicts?

### Persona Claims

- [ ] You said "2-3+ authorities" — are they named, or is one just "various experts"?
- [ ] You said "specific philosophies" — can you quote what each authority contributes?
- [ ] You said "alignment signal only" — is there domain knowledge in the persona that belongs in references?

## Meta-Checks

- Did persona language substitute for actual analysis? ("Sage would say..." isn't a derivability check.)
- Did you reference a file you were told to check? If not, go back and check it.
- Is your recommendation different from what a generic developer would say? If not, the team added nothing.
- Did the Challenger actually find issues, or did it glaze? A confidence score of 5/5 on a non-trivial spec is a red flag.
