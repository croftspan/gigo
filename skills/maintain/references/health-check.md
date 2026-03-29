# Health Check — Procedure

No specific request — you're doing a checkup. This is the most valuable thing maintain does, because projects drift silently.

## Step 1: Assess

You've already read everything. Now evaluate on four axes:

**Coverage** — Has the project grown into areas the team doesn't cover? Check recent git history, new files, new directories. Look for work happening outside any persona's expertise.

**Freshness** — Are rules still accurate? Anything outdated? Early-project rules that no longer apply? References to tools or patterns that have changed?

**Weight** — This is the most valuable check. For every rule in every file, ask:
- Can the agent figure this out by reading the code? → It's served its purpose. Let it go.
- Does this only apply to some tasks but loads on every task? → Move to references.
- Does this overlap with another rule? → Merge into one.
- Is this file approaching ~60 lines? → Move detail to references.
- Is the total across all rules files approaching ~300 lines? → Consolidate or move to references.
- Is this worth loading on every conversation? → If not, let it go.
- Do persona entries in CLAUDE.md contain domain-knowledge content (factual specifics, implementation patterns)? → Alignment signal stays; knowledge moves to `.claude/references/`.

**Pipeline Integrity** — Does the workflow encode the full pipeline? Check for:
- Plan stage — does workflow reference `gigo:blueprint` or an equivalent planning step?
- Execute stage — is there a clear description of how work gets done?
- Review stages — are review steps intact? Does snap run? Are review skills referenced?
- If any stage is missing or broken, flag it.

## Step 2: Present Findings as a Triage

- **Add:** "Your project has grown into [area]. Here's who I'd add."
- **Update:** "Your [file] references [outdated thing]. Here's the current state."
- **Prune:** "These rules aren't earning their token cost: [list]. Move to references or remove?"
- **Upgrade:** "Your setup is missing [current feature]. Consider running `gigo:maintain` in upgrade mode."
- **All clear:** "Everything's lean and covering what it needs to. No changes."

## Step 3: Wait for Approval

Present your findings. Wait for the operator to approve before writing any changes. Nothing without approval.
