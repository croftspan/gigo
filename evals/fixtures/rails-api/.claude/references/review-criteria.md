# Review Criteria

Domain-specific quality checks for this project's review pipeline.
Generated from team expertise. Regenerate with `gigo:maintain` when expertise changes.

## Spec Compliance Criteria
<!-- Used by spec-reviewer: "did you build the right thing?" -->
- Does every feature have a request spec covering the happy path and at least one error path before implementation?
- Does every non-2xx response use the consistent error envelope (`{ error: { code: String, message: String, details: Hash? } }`)?
- Is every collection endpoint paginated with default 25, max 100?
- Does every migration use the `change` method where possible, with `up`/`down` only when `change` can't express the rollback?
- Are factories minimal and valid by default?
- Does the implementation match what was claimed in the plan — did you actually build what you said you would?

## Craft Review Criteria
<!-- Used by craft-reviewer: "is the work well-built?" -->
- Is every migration reversible and tested against production-size data?
- Does no migration lock a table for more than 10 seconds?
- Are schema changes separated from data backfills in migrations?
- Does every association in a collection endpoint use `includes` or `preload` to prevent N+1 queries?
- Does no controller action trigger N+1 queries?
- Are controllers thin — validating input, delegating to models/services, rendering responses — with no business logic?
- Is raw SQL justified with a comment when used, rather than defaulting to it over ActiveRecord?
- Do request specs test with real database queries rather than mocking the database?

## Challenger Criteria
<!-- Used by spec-plan-reviewer: "will this approach succeed?" -->
- Does the migration plan account for table size and lock duration on production-size data?
- For columns with defaults on large tables, does the approach add the column without default first, backfill separately, then set the default?
- Does the approach account for migration reversibility — can every migration be safely rolled back?
- Does the endpoint design include pagination, error envelope consistency, and N+1 prevention from the start?
- Is the API surface area minimal — the smallest useful set of endpoints for the requirement?
- Does the test strategy follow the test pyramid — broad unit tests, narrow integration tests — rather than inverting it?
- Will the approach survive the question "did you actually do what you claimed?" — are there concrete verification steps?
