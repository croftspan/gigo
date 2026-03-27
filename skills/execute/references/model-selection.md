# Model Selection for Workers

Use the least powerful model that can handle each role to conserve cost and increase speed.

## For Agent Team Teammates

Specify model when spawning teammates. Agent teams let you set model per teammate.

| Task complexity | Signals | Model |
|---|---|---|
| Mechanical | Touches 1-2 files, complete spec, isolated function | haiku |
| Integration | Multiple files, integration concerns, pattern matching | sonnet |
| Architecture/judgment | Design decisions, broad codebase understanding, debugging | opus |

## For Subagent Dispatch (Tier 2 fallback)

Same guidance, specified via Agent tool's `model` parameter.

## For Review Subagents

Use sonnet — review needs judgment but has focused scope.

## Sizing the Team

Agent teams docs recommend 5-6 tasks per teammate. Scale accordingly:

| Plan size | Teammates |
|---|---|
| 3-6 tasks | 1-2 |
| 7-12 tasks | 2-3 |
| 13-18 tasks | 3-4 |
| 19+ tasks | 4-5 |

Start small. 3 focused teammates outperform 5 scattered ones.

## Complexity Assessment

When reading the plan, assess each task's complexity before spawning:

**Mechanical (haiku):** "Add a config field," "Write a unit test for X," "Create a type definition," "Copy and adapt an existing pattern." The spec is complete and unambiguous. No judgment calls.

**Integration (sonnet):** "Wire up the API endpoint to the database layer," "Update the build pipeline to include the new module," "Refactor the auth flow to support the new provider." Multiple files, need to understand how pieces connect.

**Architecture/judgment (opus):** "Design the plugin interface," "Implement the caching strategy with invalidation," "Build the error recovery system." Requires design decisions, trade-off evaluation, or deep codebase understanding.

When in doubt, go one tier up. A slightly over-powered model wastes tokens; an under-powered model wastes a review cycle.
