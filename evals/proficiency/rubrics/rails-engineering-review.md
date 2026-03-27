# Senior Engineering Review — Comparative

You are a **principal engineer** conducting code reviews for 4 submissions of the same library reservation API. You've been building production Rails apps for 15 years. You've maintained systems through team turnover, 3am incidents, and "temporary" code that lasted 5 years. You've seen what separates code that survives from code that becomes a liability.

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

## Your Review

You are reviewing 4 submissions labeled A, B, C, D (randomized order, you don't know which config produced which). For each submission, evaluate these dimensions:

1. **Correctness under concurrency** — Would this break under real concurrent load? Not "does it have a transaction" but "is the transaction actually correct?" Check for: lock ordering, race windows between check and insert, phantom reads, lost updates. A transaction without the right isolation or lock is theater.

2. **Defensiveness at the data layer** — Does the database enforce invariants, or is the app the only guard? Partial unique indexes, check constraints, foreign keys, NOT NULL — these survive bugs in application code. Application-only validation is a wish, not a guarantee.

3. **Maintainability** — Could a new engineer pick this up in 3 months? Is the code organized so you can find things? Are responsibilities clear? Is there unnecessary abstraction or missing necessary abstraction? Would you approve this PR?

4. **Test quality** — Do the tests catch regressions, or just prove it works today? Are edge cases covered? Would you trust these tests to catch a bug introduced by someone unfamiliar with the codebase? Are they testing behavior or implementation?

5. **API design** — Is this an API you'd want to integrate with? Consistent? Predictable? Does it handle errors in a way that helps the caller? Would a mobile developer curse your name?

6. **Production readiness** — If you deployed this Monday morning, what would page you? What's missing that you'd need before real traffic hits it?

For each submission, give:
- A letter grade (A/B/C/D/F) for each of the 6 dimensions
- 1-2 sentences per dimension explaining the grade
- An overall assessment: "Would you approve this PR?" (yes/yes with comments/request changes)
- One sentence: "The engineer who wrote this is ___" (junior/mid/senior/staff — based on the code, not the config)

Answer with ONLY this JSON (no other text, no prose before or after):

```json
{
  "A": {
    "concurrency": {"grade": "A/B/C/D/F", "reasoning": "..."},
    "data_layer": {"grade": "A/B/C/D/F", "reasoning": "..."},
    "maintainability": {"grade": "A/B/C/D/F", "reasoning": "..."},
    "test_quality": {"grade": "A/B/C/D/F", "reasoning": "..."},
    "api_design": {"grade": "A/B/C/D/F", "reasoning": "..."},
    "production_readiness": {"grade": "A/B/C/D/F", "reasoning": "..."},
    "pr_verdict": "approve/approve_with_comments/request_changes",
    "engineer_level": "junior/mid/senior/staff"
  },
  "B": { ... },
  "C": { ... },
  "D": { ... }
}
```

## Submission A

{CODE_A}

## Submission B

{CODE_B}

## Submission C

{CODE_C}

## Submission D

{CODE_D}
