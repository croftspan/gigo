# Standards — OrderFlow API

## Quality Gates

- Every migration is reversible. `change` method preferred; `up`/`down` only when `change` can't express the rollback.
- No N+1 queries. Every association in a collection endpoint uses `includes` or `preload`. Bullet gem catches what code review misses.
- Request spec before implementation. No feature ships without a green request spec covering the happy path and at least one error path.
- Consistent error envelope: `{ error: { code: String, message: String, details: Hash? } }` on every non-2xx response.
- Every collection endpoint is paginated. Default 25, max 100.

## Anti-Patterns

- **Raw SQL without justification.** ActiveRecord handles 95% of queries. Raw SQL needs a comment explaining why AR can't do it.
- **Skipping tests "for now."** There is no "for now." Write the spec first.
- **Unpaginated collections.** `Order.all` in a response is a production incident waiting to happen.
- **Table-locking migrations.** Adding a column with a default on a large table locks it. Add the column first, backfill separately.
- **Business logic in controllers.** Controllers are thin — they validate input, call a service or model, and render the response.
- **Mocking the database.** Use real database queries in request specs. Mocks hide bugs that matter in production.

## Forbidden

- Never deploy without green CI.
- Never change schema without a migration.
- Never put SQL queries in controllers or views.
- Never skip the migration reversibility check.

## When to Go Deeper

When writing or reviewing a migration, read `.claude/references/rails-patterns.md` — especially safe migration patterns and lock-duration checks.
When designing or reviewing an endpoint, read `.claude/references/rails-patterns.md` — especially N+1 prevention and pagination requirements.
When reviewing existing controller code, read `.claude/references/rails-patterns.md` — check for N+1 queries, missing pagination, and thin-controller violations.
When deploying or preparing for production, read `.claude/references/rails-patterns.md` — verify migration safety, index strategy, and CI status before shipping.
When diagnosing slow tests, read `.claude/references/rails-patterns.md` — check factory design, unnecessary database hits, and spec isolation patterns.
When scoping a new feature or system, read `.claude/references/rails-patterns.md` — audit existing code for violations first, then plan migrations, endpoints, and specs using established patterns.
