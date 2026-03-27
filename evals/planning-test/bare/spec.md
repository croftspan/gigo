# Library Book Reservation System — Specification

## Data Model

### Books

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK, auto-increment | |
| `title` | `string` | NOT NULL | |
| `author` | `string` | NOT NULL | |
| `isbn` | `string` | NOT NULL, UNIQUE | 13-character ISBN |
| `copies_count` | `integer` | NOT NULL, DEFAULT 0 | Counter cache for total physical copies |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:**
- `index_books_on_isbn` (unique)

### Copies

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK, auto-increment | |
| `book_id` | `bigint` | NOT NULL, FK -> books | |
| `inventory_number` | `string` | NOT NULL, UNIQUE | Library's physical tracking ID |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:**
- `index_copies_on_book_id`
- `index_copies_on_inventory_number` (unique)

### Users

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK, auto-increment | |
| `name` | `string` | NOT NULL | |
| `email` | `string` | NOT NULL, UNIQUE | |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:**
- `index_users_on_email` (unique)

### Reservations

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK, auto-increment | |
| `user_id` | `bigint` | NOT NULL, FK -> users | |
| `book_id` | `bigint` | NOT NULL, FK -> books | Denormalized for query convenience |
| `copy_id` | `bigint` | NOT NULL, FK -> copies | The specific copy reserved |
| `status` | `string` | NOT NULL, DEFAULT 'active' | Enum: active, expired, cancelled |
| `expires_at` | `datetime` | NOT NULL | Set to `created_at + 48.hours` |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:**
- `index_reservations_on_user_id`
- `index_reservations_on_book_id`
- `index_reservations_on_copy_id`
- `index_reservations_on_status_and_expires_at` (composite, for active reservation queries)
- `index_reservations_on_copy_id_and_status` (composite, for availability checks)

**Design decision — `expires_at` column:** Rather than computing `created_at + 48.hours` in every query, we store `expires_at` explicitly. This makes queries simpler (`WHERE expires_at > NOW()`), allows future flexibility (different expiration windows per book type), and is indexable.

**Design decision — `book_id` on reservations:** Denormalized from `copies.book_id`. Avoids a JOIN when listing a user's reservations. The denormalization is safe because a copy never changes its book.

---

## Model Definitions

### Book
- `has_many :copies`
- `has_many :reservations`
- Method: `available_copies_count` — total copies minus active reservations

### Copy
- `belongs_to :book, counter_cache: :copies_count`
- `has_many :reservations`
- Scope: `available` — copies without an active reservation

### User
- `has_many :reservations`

### Reservation
- `belongs_to :user`
- `belongs_to :book`
- `belongs_to :copy`
- Scope: `active` — `where(status: :active).where('expires_at > ?', Time.current)`
- Scope: `expired_pending` — `where(status: :active).where('expires_at <= ?', Time.current)`
- Enum: `status` — `{ active: 'active', expired: 'expired', cancelled: 'cancelled' }`

---

## API Endpoints

All endpoints are JSON API. Base path: `/api/v1`.

### POST /api/v1/reservations — Create Reservation

**Request:**
```json
{
  "reservation": {
    "user_id": 1,
    "book_id": 42
  }
}
```

The user reserves a *book*, not a specific copy. The system assigns an available copy.

**Success Response (201 Created):**
```json
{
  "reservation": {
    "id": 100,
    "user_id": 1,
    "book_id": 42,
    "copy_id": 7,
    "status": "active",
    "expires_at": "2026-03-28T14:30:00Z",
    "created_at": "2026-03-26T14:30:00Z"
  }
}
```

**Error Responses:**

| Condition | HTTP Status | Response Body |
|---|---|---|
| Book not found | 404 | `{ "error": { "code": "book_not_found", "message": "Book not found" } }` |
| User not found | 404 | `{ "error": { "code": "user_not_found", "message": "User not found" } }` |
| No copies available | 422 | `{ "error": { "code": "no_copies_available", "message": "All copies of this book are currently reserved" } }` |
| User already has active reservation for this book | 422 | `{ "error": { "code": "duplicate_reservation", "message": "You already have an active reservation for this book" } }` |
| Missing/invalid params | 422 | `{ "error": { "code": "invalid_params", "message": "...", "details": { ... } } }` |

### GET /api/v1/users/:user_id/reservations — List User's Reservations

**Query Parameters:**
- `status` (optional): Filter by status. Values: `active`, `expired`, `cancelled`, `all`. Default: `all`.

**Success Response (200 OK):**
```json
{
  "reservations": [
    {
      "id": 100,
      "user_id": 1,
      "book_id": 42,
      "copy_id": 7,
      "status": "active",
      "expires_at": "2026-03-28T14:30:00Z",
      "created_at": "2026-03-26T14:30:00Z",
      "book": {
        "id": 42,
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441172719"
      }
    }
  ]
}
```

**Note on expired reservations:** Reservations where `status = 'active'` but `expires_at <= Time.current` are returned with an effective status of `"expired"`. The serializer computes the display status, not the raw database value.

**Error Responses:**

| Condition | HTTP Status | Response Body |
|---|---|---|
| User not found | 404 | `{ "error": { "code": "user_not_found", "message": "User not found" } }` |
| Invalid status filter | 422 | `{ "error": { "code": "invalid_status", "message": "Status must be one of: active, expired, cancelled, all" } }` |

### DELETE /api/v1/reservations/:id — Cancel Reservation

**Request:** No body required. User identification via `user_id` query param (since auth is out of scope).

`DELETE /api/v1/reservations/100?user_id=1`

**Success Response (200 OK):**
```json
{
  "reservation": {
    "id": 100,
    "user_id": 1,
    "book_id": 42,
    "copy_id": 7,
    "status": "cancelled",
    "expires_at": "2026-03-28T14:30:00Z",
    "created_at": "2026-03-26T14:30:00Z"
  }
}
```

**Error Responses:**

| Condition | HTTP Status | Response Body |
|---|---|---|
| Reservation not found | 404 | `{ "error": { "code": "reservation_not_found", "message": "Reservation not found" } }` |
| Not the user's reservation | 403 | `{ "error": { "code": "forbidden", "message": "You can only cancel your own reservations" } }` |
| Already cancelled | 422 | `{ "error": { "code": "already_cancelled", "message": "This reservation is already cancelled" } }` |
| Already expired | 422 | `{ "error": { "code": "already_expired", "message": "This reservation has already expired" } }` |

---

## Business Rules

### Reservation Creation
1. The book must exist.
2. The user must exist.
3. The user must not already have an active reservation for this book (active = status is `active` AND `expires_at > Time.current`).
4. At least one copy must be available (no active reservation against it).
5. An available copy is assigned automatically. Selection: the copy with the lowest `id` that is available (deterministic, testable).
6. `expires_at` is set to `Time.current + 48.hours`.
7. The entire operation runs in a transaction with `SELECT ... FOR UPDATE` on the candidate copies to prevent race conditions.

### Reservation Expiration
1. A reservation is considered expired when `expires_at <= Time.current`, regardless of the `status` column value.
2. The API serializer always returns the *effective* status (computed from `expires_at`), not the raw `status` column.
3. A background Sidekiq job runs hourly to bulk-update `status` from `active` to `expired` where `expires_at <= Time.current`. This is a cleanup operation — the system is correct without it.

### Reservation Cancellation
1. Only the reservation's owner can cancel it.
2. Only active, non-expired reservations can be cancelled.
3. Cancellation sets `status = 'cancelled'` and `updated_at` to current time.
4. The copy becomes immediately available for other reservations.

### Copy Availability
A copy is available if it has no reservation where `status = 'active'` AND `expires_at > Time.current`. This is the single source of truth for availability, used by both the reservation creation path and any future availability queries.

---

## Architecture

### Business Logic Location

All reservation business logic lives in a **service object**: `ReservationService`. This is not in the model (models handle scopes, validations, associations) and not in the controller (controllers handle HTTP concerns).

**`ReservationService`** has three public methods:
- `ReservationService.create(user_id:, book_id:)` — returns `Result` (success/failure with data or errors)
- `ReservationService.cancel(reservation_id:, user_id:)` — returns `Result`
- `ReservationService.list_for_user(user_id:, status:)` — returns `Result`

**Why a service object, not model callbacks:**
- The create operation spans multiple models (User, Book, Copy, Reservation) and involves locking. This is coordination logic, not model behavior.
- Testable in isolation from HTTP.
- Explicit flow — no hidden callbacks.

### Result Object

A simple value object for service responses:

```ruby
Result = Struct.new(:success?, :data, :error_code, :error_message, :http_status, keyword_init: true)
```

Controllers just translate Results to HTTP responses. No business logic in controllers.

### Serialization

One serializer per resource, using plain Ruby objects (no gem dependency for this scale):
- `ReservationSerializer` — handles effective status computation
- `BookSerializer` — nested in reservation responses

### Background Jobs

- `ExpireReservationsJob` — runs hourly via Sidekiq-Cron or `whenever`. Bulk-updates expired reservations. The system is correct without this job; it exists for data cleanliness and to keep the `status` column accurate for any direct database queries.

### Error Handling

A base `Api::V1::BaseController` rescues standard errors:
- `ActiveRecord::RecordNotFound` -> 404
- `ActionController::ParameterMissing` -> 422
- Unhandled errors -> 500 with generic message (no stack trace in response)

Service-specific errors are returned via the Result object, not exceptions.

### Request Flow

```
HTTP Request
  -> Router
    -> Api::V1::ReservationsController
      -> Strong params extraction
      -> ReservationService.create / cancel / list_for_user
        -> Model scopes, locking, validation
        -> Returns Result
      -> Controller translates Result to HTTP response
        -> Serializer formats data
  -> HTTP Response
```
