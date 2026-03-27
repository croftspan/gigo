# Library Book Reservation System — Brainstorm

## Discovery Questions & Answers

**Q1: What's the expected scale? How many concurrent users and reservations per day?**
A1: "Small library, maybe a few hundred reservations per day."

**Q2: Existing codebase or greenfield? What Rails/Ruby versions?**
A2: "Starting fresh. Rails 7.1, PostgreSQL."

**Q3: How does authentication work? Do we need to build user management?**
A3: "Not in scope. Assume user_id in params."

**Q4: How many copies per book typically? Is it always 1, or variable?**
A4: "Varies. Some books 1 copy, popular ones maybe 10."

**Q5: What happens when a reservation expires? Notifications? Waitlist?**
A5: "The copy becomes available again. No notifications."

**Q6: What's the testing expectation?**
A6: "Tests are important. RSpec. I want good coverage."

**Q7: Background job infrastructure? Cron? Sidekiq?**
A7: "We have Sidekiq if needed. Keep it simple though."

---

## Hard Problems Identified

1. **Race conditions on copy availability.** Two users reserving the last copy of a book simultaneously. Without proper locking, both could succeed, resulting in an over-reserved book. This is the hardest problem in the system.

2. **Expiration mechanics.** Reservations expire after 48 hours. Two sub-problems: (a) how to actually transition reservation state when the clock runs out, and (b) how to correctly count available copies when some reservations are expired but not yet cleaned up.

3. **Availability calculation.** "Available copies" is derived: total copies minus active (non-expired, non-cancelled) reservations. This calculation must be consistent with the reservation creation path to avoid double-booking.

4. **Definition of "active" reservation.** A reservation is active if it is not cancelled AND was created less than 48 hours ago. Every query that touches reservations must agree on this definition, or bugs emerge.

---

## Approaches

### Approach A: Eager Expiration via Sidekiq Scheduled Jobs

When a reservation is created, enqueue a Sidekiq job scheduled for exactly 48 hours later. That job transitions the reservation status from `active` to `expired`. Availability is calculated by counting reservations with `status = 'active'`.

**Trade-offs:**
- (+) Simple queries — just filter on status column
- (+) Explicit state transitions, easy to audit
- (-) If Sidekiq is down or delayed, reservations stay "active" past their expiration, blocking availability
- (-) Two sources of truth: the `created_at` timestamp says it's expired, but the status column says active
- (-) More moving parts (Redis, Sidekiq) for a simple domain

### Approach B: Lazy Expiration via Query Scopes

Never explicitly expire reservations. Instead, define "active" as `status = 'active' AND created_at > 48.hours.ago` everywhere. Availability is calculated using this compound condition. Optionally, run a periodic Sidekiq job to bulk-update expired reservations for cleanliness, but the system never depends on it.

**Trade-offs:**
- (+) Single source of truth — time-based, no race between clock and job
- (+) System is correct even if Sidekiq is down
- (+) Simpler architecture, fewer failure modes
- (-) Every query must include the time condition (mitigated by a model scope)
- (-) The `status` column can be stale (mitigated by the optional cleanup job)

### Approach C: Database-Level Expiration with CHECK Constraints and Views

Use a PostgreSQL view that computes the effective status. The `reservations` table stores raw data; a `active_reservations` view applies the 48-hour filter. Application code queries the view.

**Trade-offs:**
- (+) Correctness enforced at the database level
- (+) Any client of the database sees consistent state
- (-) Views add complexity for a Rails app (ActiveRecord doesn't love views without extra gems)
- (-) Harder to test, harder to reason about for a small team
- (-) Over-engineered for "a few hundred reservations per day"

---

## Recommendation: Approach B — Lazy Expiration via Query Scopes

**Why:**

For a small library system, correctness and simplicity beat architectural elegance. Approach B has the fewest moving parts and the strongest correctness guarantee: a reservation's expiration is derived from immutable data (`created_at`), not from a job that may or may not have run.

The implementation:
- A single `scope :active` on the Reservation model: `where(status: :active).where('created_at > ?', 48.hours.ago)`
- Availability check uses this scope with row-level locking (`FOR UPDATE`) to prevent race conditions
- An optional Sidekiq job runs periodically (e.g., hourly) to mark expired reservations for cleanliness, but the system never depends on it being timely
- Race conditions on the last copy are handled by `SELECT ... FOR UPDATE` on the book's copies count within a transaction

This gives us a system that is correct by default, simple to test, and degrades gracefully if background infrastructure hiccups.
