# Workflow — OrderFlow API

## The Loop

1. **Understand the ask.** Read the request. If the scope is unclear, ask one question.
2. **Write the spec first.** Request spec for the happy path and primary error case. Watch it fail.
3. **Implement.** Minimum code to pass the spec. Follow Rails conventions.
4. **Verify.** Run the full spec suite, not just the new spec.
5. **Review.** Check for N+1 queries, missing pagination, inconsistent error responses.

## Migration Workflow

1. Check if the table is large (>100k rows). If yes, plan for zero-downtime.
2. Write a reversible migration. Test both `up` and `down`.
3. If adding a column with a default: add column without default first, backfill in a separate migration, then set the default.
4. Run against a production-size dataset before merging.

## Endpoint Workflow

1. Define the route in `config/routes.rb`.
2. Write request spec: happy path, validation error, not found.
3. Implement controller action. Keep it thin — delegate to models.
4. Add `includes`/`preload` for any associations. Check with Bullet.
5. Verify error envelope format matches the standard.
