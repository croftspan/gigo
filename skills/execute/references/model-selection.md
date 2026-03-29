# Model Selection for Workers

Use the least powerful model that can handle each task to conserve cost and increase speed.

## Task Complexity → Model

| Task complexity | Signals | Model |
|---|---|---|
| Mechanical | Touches 1-2 files, complete spec, isolated function | haiku |
| Integration | Multiple files, integration concerns, pattern matching | sonnet |
| Architecture/judgment | Design decisions, broad codebase understanding, debugging | opus |

Specify model via the Agent tool's `model` parameter when dispatching subagents.

## Complexity Assessment

When reading the plan, assess each task's complexity before dispatching:

**Mechanical (haiku):** "Add a config field," "Write a unit test for X," "Create a type definition," "Copy and adapt an existing pattern." The spec is complete and unambiguous. No judgment calls.

**Integration (sonnet):** "Wire up the API endpoint to the database layer," "Update the build pipeline to include the new module," "Refactor the auth flow to support the new provider." Multiple files, need to understand how pieces connect.

**Architecture/judgment (opus):** "Design the plugin interface," "Implement the caching strategy with invalidation," "Build the error recovery system." Requires design decisions, trade-off evaluation, or deep codebase understanding.

When in doubt, go one tier up. A slightly over-powered model wastes tokens; an under-powered model wastes a review cycle.

## For Review Subagents

Use sonnet — review needs judgment but has focused scope.

## For Agent Teams (Tier 3, Opt-In)

Same model guidance applies. Specify model when spawning teammates. Team sizing: ~5-6 tasks per teammate.

| Plan size | Teammates |
|---|---|
| 3-6 tasks | 1-2 |
| 7-12 tasks | 2-3 |
| 13-18 tasks | 3-4 |
| 19+ tasks | 4-5 |

Start small. 3 focused teammates outperform 5 scattered ones.
