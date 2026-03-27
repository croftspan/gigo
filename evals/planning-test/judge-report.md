# Planning Pipeline Evaluation: Bare vs Assembled

**Evaluator role:** VP of Engineering, choosing which pipeline's output to hand to a development team.

**Setup:** Both teams received the identical task (library book reservation system) and identical user answers. Team A (bare) had no context engineering. Team B (assembled) had defined personas (Kane for migrations, Leach for API design, Beck for TDD) and quality standards.

---

## Phase 1: Brainstorm

### Questions Asked

Both teams asked the same seven questions and got the same answers. The questions themselves are nearly identical in substance: scale, greenfield vs existing, auth, copy counts, expiration behavior, testing expectations, background jobs.

**Difference in framing:** Team B attributes each question to a specific persona and explains *why* that persona cares about the answer. "Kane -- capacity sizing for migration strategy" vs bare's "What's the expected scale?" This is not cosmetic. Team B's framing connects each question to a downstream architectural decision, which means the answers are already being interpreted through a lens. Team A's questions float free of context.

**Verdict:** Slight edge to Team B. The questions are functionally equivalent, but the persona attribution creates a decision-trail that pays off later.

### Hard Problems Identified

**Team A** identified 4 hard problems:
1. Race conditions on copy availability
2. Expiration mechanics
3. Availability calculation
4. Definition of "active" reservation

**Team B** identified 5 hard problems:
1. Race condition on copy assignment
2. Expiration timing
3. Idempotency / duplicate reservations
4. Cancellation of expired reservations
5. Copy count accuracy under load

**Critical gap in Team A:** Problems 3 and 4 from Team B -- duplicate reservation handling and the UX question of cancelling expired reservations -- are completely absent from Team A's brainstorm. Team A identifies "definition of active reservation" as a hard problem but treats it as a consistency concern, not an enforcement concern. Team B explicitly calls out the need for a partial unique index and the UX decision around expired cancellation.

**Critical gap in Team B:** None. Team B's list is a strict superset of Team A's, with two additional problems that both prove material in later phases.

### Architectural Approach

**Team A** presents three approaches for *expiration strategy*:
- Eager expiration via Sidekiq
- Lazy expiration via query scopes
- Database-level expiration with views

**Team B** presents three approaches for *reservation model*:
- Reserve a specific copy
- Reserve a book, system assigns a copy
- Queue-based reservation

These are fundamentally different framings. Team A narrows to one sub-problem (how to expire) and presents three solutions. Team B frames the entire domain model as the decision point and presents three architectures. Team B's framing is stronger because the reservation model shapes everything downstream -- the API surface, the concurrency model, the copy assignment logic. Team A's framing assumes "reserve a book, assign a copy" is obvious and jumps to the expiration problem.

**Specific architectural wins for Team B:**
- Explicitly considers `FOR UPDATE SKIP LOCKED` vs `FOR UPDATE` in the brainstorm, not just the spec. This is a PostgreSQL-specific concurrency technique that Team A only mentions as `FOR UPDATE` later, without the `SKIP LOCKED` variant.
- Team B's Approach C (queue-based) is correctly rejected for good reasons, which shows the team considered and dismissed an async architecture. Team A's Approach C (database views) is also correctly rejected but is a less interesting design space to explore.
- Team B's recommendation explicitly references which persona favors which approach and why, creating an auditable decision record.

**Verdict:** Team B wins Phase 1. The hard problems list is more complete, the architectural framing is broader, and the decision rationale is traceable.

---

## Phase 2: Spec

### Completeness

**Team A spec: 296 lines.** Covers data model, model definitions, API endpoints, business rules, architecture, and request flow.

**Team B spec: 462 lines.** Covers data model, model layer with code, service layer with full implementation, endpoints with pagination, business rules, background jobs, architecture decisions table, and routes.

### Specific Differences That Matter

**1. Data model: BookCopy condition field.**

Team B includes a `condition` column on BookCopies with an enum (`good`, `fair`, `poor`, `withdrawn`) and a business rule that withdrawn copies cannot be reserved. Team A has a `Copy` model with only `inventory_number` and no concept of copy condition. This means Team A's system has no way to take a damaged book out of circulation without deleting the copy record (which would orphan reservation history).

This is a real-world requirement that Team B anticipated and Team A missed entirely.

**2. Data model: Copy naming.**

Team A uses `Copy` with `inventory_number`. Team B uses `BookCopy` with `copy_number`. Team B's naming is more specific (avoids collision with Ruby's `Object#copy`) and the `copy_number` enables "Copy 3 of 5" display. Minor but thoughtful.

**3. Concurrency: `FOR UPDATE` vs `FOR UPDATE SKIP LOCKED`.**

Team A's spec says: "SELECT ... FOR UPDATE on the candidate copies count within a transaction." Team B's spec says: "SELECT ... FOR UPDATE SKIP LOCKED." These are meaningfully different. `FOR UPDATE` blocks the second transaction until the first completes. `FOR UPDATE SKIP LOCKED` lets the second transaction skip the locked row and grab the next available copy. Under concurrent load, Team B's approach has lower latency and higher throughput. Team A's approach will work but creates unnecessary serialization.

**4. Duplicate reservation enforcement.**

Team A enforces duplicate prevention in application code only (checking the `active` scope before creating). Team B enforces it with both application code AND a partial unique index: `UNIQUE (user_id, book_id) WHERE status = 'active'`. This is defense in depth. Team A's approach has a race window between the check and the insert. Team B's spec even includes a `rescue ActiveRecord::RecordNotUnique` handler for when two concurrent requests both pass the application check.

This is the single biggest quality difference between the two specs. Team A's system can produce duplicate active reservations under concurrent load. Team B's cannot.

**5. Cancellation of expired reservations.**

Team A's spec says cancelling an already-expired reservation returns 422 with `already_expired`. Team B's spec says it is allowed -- the reservation transitions to `cancelled`. Team B includes an explicit rationale: "the user sees the reservation in their list and should be able to dismiss it without getting an error."

This is a UX decision that Team B identified as a hard problem in Phase 1 and carried through to a deliberate design choice. Team A made the opposite choice without discussing the tradeoff.

**6. Pagination.**

Team B's list endpoint includes pagination with `page`, `per_page` (max 100), and a `meta` object with `current_page`, `total_pages`, `total_count`, `per_page`. Team A's list endpoint has no pagination. For "a few hundred reservations per day," pagination may not be urgent, but a user who has been using the library for a year could have thousands of reservations. Team A's endpoint will return an unbounded result set.

**7. Cancel endpoint design.**

Team A uses `DELETE /api/v1/reservations/:id` with `user_id` as a query parameter. Team B uses `PATCH /api/v1/reservations/:id/cancel`. Team B's design is more RESTful -- DELETE implies resource destruction, but cancellation is a state transition. PATCH with an action route makes the intent clear. Team A also requires `user_id` as a query param on DELETE, which is an unusual pattern (DELETE with a query param for authorization).

**8. N+1 prevention.**

Team B's spec explicitly calls out `Reservation.includes(:book)` for the list endpoint and notes: "No join through book_copies is needed" because of the `book_id` denormalization. Team A mentions `includes(:book)` in the service layer but does not highlight N+1 prevention as a design concern.

**9. Service layer.**

Both specs use a ReservationService. Team A's service has three methods (create, cancel, list_for_user). Team B's service has one method (create) -- cancellation is handled directly in the controller since it is a simple state transition, and listing is a query concern handled by scopes. Team B's separation is cleaner: the service handles the complex coordinated operation (create), while simple operations stay in the controller.

### Gaps That Would Cause Implementation Problems

**Team A:**
- No partial unique index for duplicate prevention -- a developer following this spec will build a system with a concurrency bug.
- No pagination on list endpoint -- will need to be added later.
- No copy condition concept -- no way to withdraw damaged books.
- `DELETE` for cancellation will confuse developers who expect DELETE to destroy the resource.

**Team B:**
- The `condition` enum is specced but the migration doesn't explicitly include a CHECK constraint at the database level (only model validation). Minor gap.
- The cancel endpoint lacks authorization -- any user can cancel any reservation. Team A at least attempted this with the `user_id` query param. Team B's spec says "No body required. The action is in the URL" but does not address who is allowed to cancel. (Note: auth was declared out of scope, so this is defensible.)

**Verdict:** Team B wins Phase 2 decisively. The partial unique index, `SKIP LOCKED`, copy condition, pagination, and RESTful cancel design are all specific, defensible improvements that a bare architect missed.

---

## Phase 3: Implementation Plan

### Task Breakdown

**Team A: 10 tasks, 533 lines.** Linear dependency chain with some parallelism noted.

**Team B: 11 tasks, 1367 lines.** More granular dependency graph with explicit parallelism.

### TDD Approach

**Team A** describes tests in English for each task. Example from Task 6 (Service): "Happy path: creates reservation, assigns a copy, sets expires_at to 48 hours from now." This is a test description, not a test. A developer reads this and writes the test.

**Team B** includes actual RSpec code for every task. Full test files with `describe`, `context`, `let`, `it` blocks, assertions, and setup. A developer reads this and runs the test immediately.

The difference is substantial. Team A's plan requires the developer to make decisions about test structure, assertion style, factory design, and edge case coverage. Team B's plan has already made those decisions.

**Specific TDD wins for Team B:**

1. **Partial unique index test.** Team B's Task 4 includes a spec that directly tests the database constraint:
   ```ruby
   expect {
     create(:reservation, user: user, book: book, book_copy: copy2, status: 'active')
   }.to raise_error(ActiveRecord::RecordNotUnique)
   ```
   Team A has no equivalent test. This means a developer following Team A's plan could implement the migration without the partial index and never discover the gap.

2. **N+1 query count test.** Team B's Task 8 includes a spec that counts SQL queries using `ActiveSupport::Notifications` and asserts `expect(query_count).to be <= 5`. Team A mentions N+1 prevention nowhere in the plan.

3. **Side effects test for cancellation.** Team B's Task 9 includes a spec that cancels a reservation and then immediately tries to create a new reservation for the same book, verifying the copy was freed. This crosses service boundaries in a way Team A's plan does not.

4. **Expired-but-not-cleaned-up test.** Team B's Task 5 (ReservationService) includes a test where a reservation has expired (by time) but the status column still says `active`, and verifies the system treats the copy as available. This validates the dual-layer expiration design. Team A's plan mentions this scenario in English but does not spec it.

### Dependency Management

**Team A** has a dependency graph at the end, showing parallel tracks. Tasks 3 and 4 can run in parallel; Tasks 6, 7, and 9 can run in parallel. This is correct.

**Team B** also has a dependency graph, placed at the top of the plan for immediate visibility. Tasks 2, 3, and 6 can run in parallel; Tasks 8 and 10 can run in parallel after Task 4. Team B also includes a summary table at the bottom mapping each task to its order, test files, and dependencies.

Team B's approach to parallelism is slightly more conservative (fewer parallel tracks) but more practical -- the tasks that can genuinely be assigned to different developers are clearly marked.

### Ambiguity

**Team A's plan** leaves several implementation decisions to the developer:
- How exactly to implement the `Copy.available` scope (mentioned but not specified)
- How the Result object's `http_status` maps to controller responses
- Whether `effective_status` should be computed in the serializer or the model
- How `travel_to` should be used in time-sensitive tests (mentioned but not demonstrated)

**Team B's plan** resolves all of these with actual code:
- `BookCopy.available_for_reservation` scope is fully defined
- Error status mapping is explicit in the controller code
- `expired?` is a model method, serialization uses `reservation.status` directly
- Factory definitions handle the `book_copy` association correctly (this is subtle -- the factory must create a book_copy associated with the same book)

### Missing From Both

Neither plan includes:
- Database seeding for development
- CI configuration
- API documentation generation
- Performance benchmarks for concurrent reservation creation

---

## The Core Question: Did Personas Produce Measurably Better Planning?

Yes. Here are the specific, traceable impacts:

### 1. The partial unique index (Kane's contribution)

Team B's "Kane" persona -- modeled after a migration/database specialist -- drove the decision to use a partial unique index for duplicate reservation prevention. This is a PostgreSQL-specific technique that prevents a real concurrency bug. Team A's plan has no equivalent. A system built from Team A's plan will allow duplicate active reservations under concurrent load. This alone is a shipping-quality bug.

**Measurable impact:** Team A's system has a data integrity bug. Team B's does not.

### 2. `FOR UPDATE SKIP LOCKED` (Kane's contribution)

Team B uses `SKIP LOCKED`, which means concurrent reservations for the same book proceed without blocking each other. Team A uses plain `FOR UPDATE`, which serializes concurrent requests. Under load, Team B's system will have lower p99 latency for reservation creation.

**Measurable impact:** Different concurrency behavior under load.

### 3. Copy condition (domain modeling)

Team B includes a `condition` field that allows withdrawing damaged copies. Team A has no mechanism for this. A library cannot operate without the ability to remove damaged books from circulation.

**Measurable impact:** Team A requires a schema migration and feature addition before the system is operationally viable.

### 4. Pagination (Leach's contribution)

Team B's API persona drove the inclusion of pagination on the list endpoint. Team A's list endpoint returns unbounded results.

**Measurable impact:** Team A's system will time out or OOM on users with many reservations.

### 5. RESTful cancel design (Leach's contribution)

Team B uses `PATCH` for state transitions. Team A uses `DELETE` with a query parameter for authorization. Team B's design is more standard and less surprising to API consumers.

**Measurable impact:** Developer experience and API consistency.

### 6. Written test code vs test descriptions (Beck's contribution)

Team B's plan includes runnable RSpec code. Team A's plan includes English descriptions of tests. The gap between "write tests like this" and "here are the tests" is the gap between a specification and an implementation guide.

**Measurable impact:** Team B's plan can be executed faster with fewer interpretation errors.

### Were there cosmetic persona applications?

Yes. Some persona attributions in Team B add no value. "Kane's checklist: Migration uses `change` (reversible)" is stating something any Rails developer knows. "Beck likes this because the business logic is testable as a discrete unit" is a generic observation dressed in a persona label. Perhaps 20-30% of the persona attributions are decorative rather than functional.

### Did bare do anything better?

Two things:

1. **Team A's expiration framing.** The brainstorm's three approaches to expiration (eager, lazy, database views) are a cleaner comparison than Team B's three approaches to the reservation model. Both are useful framings, but Team A's is more focused on the genuinely hard sub-problem.

2. **Team A's explicit `expires_at` design decision.** Team A's spec includes a paragraph explaining why `expires_at` is stored explicitly rather than computed from `created_at + 48.hours`. Team B's spec also stores `expires_at` but does not call out the design decision as prominently. This is a minor writing quality win for Team A.

3. **Team A's authorization on cancel.** Team A requires `user_id` on the cancel request and returns 403 if the user does not own the reservation. Team B's cancel endpoint has no authorization check at all. While auth was declared out of scope, Team A's approach is safer.

---

## Verdict

**I would hand Team B's pipeline output to my engineering team.**

The reasons are structural, not stylistic:

1. **Data integrity.** Team B's system cannot produce duplicate active reservations. Team A's can. This is not a theoretical concern -- it is a concurrency bug that will manifest in production under modest load.

2. **Operational viability.** Team B's copy condition field means the library can withdraw damaged books. Team A's system has no mechanism for this.

3. **Implementation speed.** Team B's plan includes runnable test code. A developer picks up Task 2, runs the failing specs, writes the migration and model until they pass, moves to the next task. Team A's plan requires the developer to design the test harness themselves.

4. **Fewer follow-up tickets.** Team A's plan will generate follow-up work for: pagination, duplicate prevention fix, copy withdrawal mechanism, and cancel endpoint redesign. Team B's plan addresses all of these upfront.

**Confidence level:** High. The differences are not "Team B wrote more words." The differences are specific architectural decisions (partial unique index, SKIP LOCKED, copy condition, pagination) that produce a more correct, more complete, and more maintainable system. The personas were the mechanism that surfaced these decisions -- particularly the database specialist catching the partial unique index and the API designer catching the pagination gap.

**Caveat:** Team B's output is roughly 2.5x longer. If token cost or generation time matters, there is a real cost to the assembled approach. But the cost of fixing the bugs and gaps in Team A's output after implementation would exceed the upfront token investment.
