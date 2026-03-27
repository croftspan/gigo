# Library Book Reservation System — Brainstorm

## Discovery Questions & Answers

**Q1 (Kane — capacity sizing for migration strategy):** What's the expected scale? A few reservations per day or thousands? This determines whether we need zero-downtime migrations and partitioning from day one, or whether straightforward schema design suffices.

> **A1:** Small library, maybe a few hundred reservations per day.

**Q2 (Kane — environment constraints):** Are we building on an existing Rails app with an established schema, or starting fresh? This determines whether migrations need to account for existing tables and data.

> **A2:** Starting fresh. Rails 7.1, PostgreSQL.

**Q3 (Leach — authentication boundary):** How does authentication work? Do we need token-based auth, or is user identity passed some other way? This determines whether we need an auth layer or can focus purely on the reservation API.

> **A3:** Not in scope. Assume user_id in params.

**Q4 (Leach — business domain clarity):** How many copies does a typical book have? Always 1, or can popular books have multiple copies? This fundamentally shapes the reservation model — are we reserving a specific copy, or reserving the next available copy of a title?

> **A4:** Varies. Some books 1 copy, popular ones maybe 10.

**Q5 (Beck — edge case discovery):** What happens when a reservation expires? Does the copy just become available again, or is there a waitlist/notification system?

> **A5:** The copy becomes available again. No notifications.

**Q6 (Beck — test infrastructure):** What's the testing expectation? Full TDD with RSpec, or lighter coverage? This determines whether we set up FactoryBot, request specs, and the full test harness from the start.

> **A6:** Tests are important. RSpec. I want good coverage.

**Q7 (Kane — background processing):** How should expiration work mechanically? A cron job, a background worker, or checked at query time? This affects whether we need Sidekiq, a scheduled task, or can handle it purely in application logic.

> **A7:** We have Sidekiq if needed. Keep it simple though.

---

## Approaches

### Approach A: Reserve a Specific Copy

Users reserve a specific `BookCopy` by ID. The `Reservation` belongs to a `User` and a `BookCopy`. Availability is checked by looking at whether a copy has an active (non-expired, non-cancelled) reservation.

**Trade-offs:**
- **Pro:** Simple, explicit. The data model is clean — each reservation points to exactly one copy. Leach likes this because the API is straightforward: POST with `book_copy_id`.
- **Pro:** Kane likes this because queries are simple — checking availability is a single indexed lookup per copy.
- **Con:** Puts copy selection on the client. The client needs to know which copies exist and which are available. This leaks internal data (copy IDs) into the API surface.
- **Con:** Race condition: two users could try to reserve the same copy simultaneously.

### Approach B: Reserve a Book, System Assigns a Copy

Users reserve a `Book` by ID. The system finds an available copy and assigns it. The `Reservation` belongs to a `User` and a `BookCopy`, but the user never sees or picks the copy — they just say "I want this book."

**Trade-offs:**
- **Pro:** Leach strongly prefers this. The API is cleaner — the user says `book_id`, the system handles copy assignment. No internal IDs leak.
- **Pro:** Race condition is contained in one place — the copy-assignment logic — and can be solved with a database lock or optimistic locking.
- **Pro:** Beck likes this because the business logic (find available copy, assign it) is testable as a discrete unit, separate from the controller.
- **Con:** Slightly more complex implementation — need a service object or model method to handle copy selection.
- **Con:** Kane notes: if copy selection logic evolves (e.g., prefer least-used copy), it's more code to maintain. But for "grab any available," it's fine.

### Approach C: Queue-Based Reservation

Users request a reservation for a `Book`. The reservation starts in a `pending` state. A background job assigns a copy and moves it to `active`. If no copies are available, it stays `pending` or is rejected.

**Trade-offs:**
- **Pro:** Eliminates race conditions entirely — the job processes sequentially.
- **Con:** Massively overengineered for a few hundred reservations per day. Adds Sidekiq as a hard dependency for the core flow.
- **Con:** Leach objects: the API becomes eventually consistent. The create endpoint can't return the assigned copy in the response. This complicates the client.
- **Con:** Beck notes: testing async flows is harder and more brittle.

---

## Recommendation: Approach B — Reserve a Book, System Assigns a Copy

**Why:**

1. **Leach's API standards:** The API surface is clean. Users POST with `book_id`, get back a reservation with the assigned copy. No internal copy IDs in the request. Consistent with "smallest useful surface area."

2. **Kane's migration concerns:** The schema is the same as Approach A (books, book_copies, reservations), but the query patterns are slightly different. Copy availability uses a LEFT JOIN or NOT EXISTS subquery — straightforward and indexable. No exotic migration patterns needed.

3. **Beck's testability:** The copy-assignment logic lives in a service object or model method, fully testable in isolation. Request specs test the full flow. Clear separation of concerns.

4. **Race condition handling:** We solve it with a database advisory lock or `SELECT ... FOR UPDATE SKIP LOCKED` on the copy assignment. Kane approves — PostgreSQL handles this natively, no application-level locking needed.

5. **Expiration:** A Sidekiq scheduled job runs periodically (every 5 minutes) to mark expired reservations. This is the simplest mechanical approach that uses the available infrastructure without making Sidekiq a dependency of the core request path. Alternatively, we check expiration at query time (expired_at < now) and clean up async — belt and suspenders.

---

## Hard Problems

### 1. Race Condition on Copy Assignment
Two users reserve the same book simultaneously. Both find the same copy "available." Both create reservations. Now a copy has two active reservations.

**Solution:** Wrap copy selection in a database transaction with `SELECT ... FOR UPDATE SKIP LOCKED`. The first transaction locks the copy row; the second skips it and finds the next available copy (or fails if none left). This is PostgreSQL-native, no application-level locking, and Kane approves of the approach.

### 2. Expiration Timing
A reservation expires at T+48h. But the expiration job runs every 5 minutes. There's a window where a reservation is logically expired but not yet marked as such. During that window, a copy appears unavailable when it should be available.

**Solution:** Dual-layer expiration. When checking copy availability, the query includes `WHERE reservations.expires_at > NOW()` — so logically expired reservations don't block new ones, even before the cleanup job runs. The Sidekiq job just updates the `status` column for display consistency. This means the source of truth for "is this copy available" is always the query, not the status enum alone.

### 3. Idempotency / Duplicate Reservations
Should a user be allowed to reserve the same book twice? If they already have an active reservation for Book X, what happens when they try again?

**Solution:** Business rule: one active reservation per user per book. Enforced with a unique partial index on `(user_id, book_id) WHERE status = 'active'`. The database prevents duplicates even under concurrency. The API returns a clear error: `duplicate_reservation`.

### 4. Cancellation of Expired Reservations
Can a user cancel a reservation that has already expired? It's a no-op functionally, but the API needs to decide what to return.

**Solution:** Allow it. Cancelling an expired reservation transitions it to `cancelled`. The copy was already freed by the expiration logic, so there's no side effect. The alternative — returning an error — creates confusion ("but I see it in my list"). Leach prefers: let the user clean up their own list.

### 5. Copy Count Accuracy Under Load
When checking "are copies available for this book," the count needs to reflect in-flight transactions. A naive `COUNT(*)` of active reservations vs total copies can be stale.

**Solution:** The `FOR UPDATE SKIP LOCKED` pattern handles this. We don't count — we try to lock an available copy. If we get one, we proceed. If not, all copies are reserved. This is more robust than counting.
