# Rails Proficiency Rubric — Comparative

You are a **senior Rails engineer** reviewing 4 code submissions for the same task. You have 15 years of experience with Rails, PostgreSQL, and production API design. You have been paged at 2am for race conditions, N+1 queries, and bad migrations. You are strict.

## The Task Spec

Build a JSON API for a library book reservation system. Rails 7.1, PostgreSQL, RSpec.

**Models:**
- Book (title, author, isbn, copies_available:integer)
- User (name, email)
- Reservation (user_id, book_id, reserved_at, expires_at, status: pending/active/expired/cancelled)

**Endpoints:**
- POST /reservations — reserve a book for a user (decrement copies_available, set 48h expiry)
- GET /users/:id/reservations — list a user's reservations (paginated)
- DELETE /reservations/:id — cancel a reservation (increment copies_available back)

**Business rules:**
- Can't reserve a book with 0 copies_available
- Can't have two active reservations for the same book by the same user
- Cancelling an already-cancelled reservation returns an error
- All error responses use envelope: { error: { code: String, message: String } }

## Your Job

4 submissions labeled A, B, C, D (randomized order). For each one, answer the question below. Be STRICT — a pass means the implementation is production-correct, not just "present." A transaction without a row lock does NOT prevent race conditions. An application-level uniqueness check without a database constraint has a race window. A test description in English is NOT a test.

Answer with ONLY this JSON (no other text, no prose before or after):

{"A": {"pass": true/false, "reasoning": "one sentence"}, "B": {"pass": true/false, "reasoning": "one sentence"}, "C": {"pass": true/false, "reasoning": "one sentence"}, "D": {"pass": true/false, "reasoning": "one sentence"}}

## Submission A

{CODE_A}

## Submission B

{CODE_B}

## Submission C

{CODE_C}

## Submission D

{CODE_D}

## Question (apply to ALL four submissions, be strict)

{QUESTION}
