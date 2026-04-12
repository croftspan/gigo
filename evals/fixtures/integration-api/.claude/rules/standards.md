# Standards — TaskFlow

## Quality Gates

- Every API endpoint's response type matches the type its consumer uses. No implicit shape assumptions.
- Naming conventions are consistent within a layer. Cross-layer transformations are explicit.
- Every navigation link resolves to an actual page route in the app directory.
- Every status defined in the model has transition logic in the service layer.
- Every hook handles loading, error, and success states for its API calls.

## Anti-Patterns

- **Untyped API responses.** `fetch(...).then(r => r.json())` without type validation is a runtime bug waiting to happen.
- **Silent naming drift.** `created_at` in the DB, `createdAt` in the API, `created_at` in the hook — pick one or transform explicitly.
- **Dead navigation links.** Links that point to routes that don't exist in the app directory.
- **Partial state machines.** Defining statuses without implementing all their transitions.

## When to Go Deeper

When reviewing cross-boundary data flow, read `.claude/references/review-criteria.md`.
When reviewing integration patterns, read `.claude/references/integration-patterns.md`.
