# Library Book Reservation System — Technical Spec

## Data Model

### Books

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK | |
| `title` | `string` | NOT NULL | |
| `author` | `string` | NOT NULL | |
| `isbn` | `string` | NOT NULL, UNIQUE | Index: unique on `isbn` |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:** `index_books_on_isbn` (unique)

**Kane's notes:** Straightforward table. No large-table concerns at this scale. Migration is a single `create_table` with `change` — fully reversible.

### BookCopies

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK | |
| `book_id` | `bigint` | NOT NULL, FK -> books | |
| `copy_number` | `integer` | NOT NULL | For display: "Copy 3 of 5" |
| `condition` | `string` | NOT NULL, default: `'good'` | Enum: good, fair, poor, withdrawn |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:**
- `index_book_copies_on_book_id` (for finding copies of a book)
- `index_book_copies_on_book_id_and_copy_number` (unique, prevents duplicate numbering)

**Kane's notes:** The `default: 'good'` on `condition` is safe here because this is a new table — no existing rows to lock against. The unique index on `(book_id, copy_number)` prevents data corruption.

### Users

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK | |
| `name` | `string` | NOT NULL | |
| `email` | `string` | NOT NULL, UNIQUE | |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:** `index_users_on_email` (unique)

**Kane's notes:** Minimal user model. Auth is out of scope, so no password digest or token columns.

### Reservations

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `bigint` | PK | |
| `user_id` | `bigint` | NOT NULL, FK -> users | |
| `book_id` | `bigint` | NOT NULL, FK -> books | Denormalized from book_copy for query convenience |
| `book_copy_id` | `bigint` | NOT NULL, FK -> book_copies | The assigned copy |
| `status` | `string` | NOT NULL, default: `'active'` | Enum: active, cancelled, expired |
| `expires_at` | `datetime` | NOT NULL | Set to `created_at + 48.hours` |
| `created_at` | `datetime` | NOT NULL | |
| `updated_at` | `datetime` | NOT NULL | |

**Indexes:**
- `index_reservations_on_user_id` (for listing user's reservations)
- `index_reservations_on_book_copy_id` (for checking copy availability)
- `index_reservations_on_user_id_and_book_id_active` — partial unique index: `UNIQUE (user_id, book_id) WHERE status = 'active'` (prevents duplicate active reservations)
- `index_reservations_on_status_and_expires_at` (for the expiration job: `WHERE status = 'active' AND expires_at < NOW()`)

**Kane's notes:** The `book_id` column is deliberately denormalized. Without it, listing a user's reservations with book info requires joining through `book_copies`. With it, we can query `reservations JOIN books` directly. The cost is one extra bigint column; the benefit is simpler, faster queries. The partial unique index is PostgreSQL-specific — the migration must use `execute` for this, with a matching `remove_index` in the `down` method. This is the one migration that needs explicit `up`/`down` instead of `change`.

---

## Model Layer

### Book
```ruby
class Book < ApplicationRecord
  has_many :book_copies, dependent: :destroy
  has_many :reservations

  validates :title, :author, :isbn, presence: true
  validates :isbn, uniqueness: true
end
```

### BookCopy
```ruby
class BookCopy < ApplicationRecord
  belongs_to :book
  has_many :reservations

  validates :copy_number, presence: true,
            uniqueness: { scope: :book_id }
  validates :condition, presence: true,
            inclusion: { in: %w[good fair poor withdrawn] }

  scope :available_for_reservation, -> {
    where(condition: %w[good fair])
      .where.not(
        id: Reservation.active_and_unexpired.select(:book_copy_id)
      )
  }
end
```

### Reservation
```ruby
class Reservation < ApplicationRecord
  belongs_to :user
  belongs_to :book
  belongs_to :book_copy

  validates :status, presence: true,
            inclusion: { in: %w[active cancelled expired] }
  validates :expires_at, presence: true

  scope :active_and_unexpired, -> {
    where(status: 'active').where('expires_at > ?', Time.current)
  }

  def expired?
    status == 'active' && expires_at <= Time.current
  end

  def cancel!
    update!(status: 'cancelled')
  end
end
```

### User
```ruby
class User < ApplicationRecord
  has_many :reservations

  validates :name, :email, presence: true
  validates :email, uniqueness: true
end
```

---

## Service Layer

### ReservationService

All business logic for creating reservations lives here. Controllers never touch copy assignment or availability checks directly.

```ruby
class ReservationService
  Result = Struct.new(:success?, :reservation, :error_code, :error_message, keyword_init: true)

  def self.create(user_id:, book_id:)
    new(user_id: user_id, book_id: book_id).create
  end

  def initialize(user_id:, book_id:)
    @user_id = user_id
    @book_id = book_id
  end

  def create
    user = User.find_by(id: @user_id)
    return not_found_result('user', @user_id) unless user

    book = Book.find_by(id: @book_id)
    return not_found_result('book', @book_id) unless book

    if Reservation.active_and_unexpired.exists?(user_id: @user_id, book_id: @book_id)
      return error_result('duplicate_reservation',
        'User already has an active reservation for this book')
    end

    copy = assign_copy(book)
    return error_result('no_copies_available',
      'All copies of this book are currently reserved') unless copy

    reservation = Reservation.create!(
      user: user,
      book: book,
      book_copy: copy,
      status: 'active',
      expires_at: 48.hours.from_now
    )

    Result.new(success?: true, reservation: reservation)

  rescue ActiveRecord::RecordNotUnique
    # Partial unique index caught a race condition on duplicate reservation
    error_result('duplicate_reservation',
      'User already has an active reservation for this book')
  end

  private

  def assign_copy(book)
    BookCopy
      .where(book: book, condition: %w[good fair])
      .where.not(
        id: Reservation.active_and_unexpired.select(:book_copy_id)
      )
      .lock('FOR UPDATE SKIP LOCKED')
      .first
  end

  def not_found_result(resource, id)
    error_result("#{resource}_not_found", "#{resource.capitalize} #{id} not found")
  end

  def error_result(code, message)
    Result.new(success?: false, error_code: code, error_message: message)
  end
end
```

**Key design decisions:**
- `FOR UPDATE SKIP LOCKED` prevents two concurrent requests from assigning the same copy. The first locks it; the second skips it and grabs the next available.
- The `RecordNotUnique` rescue handles the race condition where two requests pass the `exists?` check simultaneously — the partial unique index catches it at the database level.
- The service returns a Result struct, not exceptions. Controllers map result states to HTTP responses. This keeps controllers thin and makes testing straightforward.

---

## Endpoints

All endpoints are under `/api/v1`. All responses use JSON. All errors use the standard envelope.

### POST /api/v1/reservations

**Create a reservation for a book.**

**Request:**
```json
{
  "reservation": {
    "user_id": 1,
    "book_id": 42
  }
}
```

**Response — 201 Created:**
```json
{
  "reservation": {
    "id": 1,
    "user_id": 1,
    "book_id": 42,
    "book_copy_id": 7,
    "status": "active",
    "expires_at": "2026-03-28T14:30:00Z",
    "book": {
      "id": 42,
      "title": "Dune",
      "author": "Frank Herbert",
      "isbn": "978-0441013593"
    },
    "created_at": "2026-03-26T14:30:00Z"
  }
}
```

**Error responses:**

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Book not found | 404 | `book_not_found` | "Book 42 not found" |
| User not found | 404 | `user_not_found` | "User 1 not found" |
| No copies available | 422 | `no_copies_available` | "All copies of this book are currently reserved" |
| Duplicate active reservation | 422 | `duplicate_reservation` | "User already has an active reservation for this book" |
| Missing params | 422 | `validation_error` | "Book ID is required" / "User ID is required" |

**Error envelope:**
```json
{
  "error": {
    "code": "no_copies_available",
    "message": "All copies of this book are currently reserved"
  }
}
```

---

### GET /api/v1/users/:user_id/reservations

**List a user's reservations, paginated.**

**Query params:**

| Param | Type | Default | Notes |
|---|---|---|---|
| `status` | string | (all) | Filter: `active`, `cancelled`, `expired` |
| `page` | integer | 1 | Page number |
| `per_page` | integer | 25 | Items per page, max 100 |

**Response — 200 OK:**
```json
{
  "reservations": [
    {
      "id": 1,
      "user_id": 1,
      "book_id": 42,
      "book_copy_id": 7,
      "status": "active",
      "expires_at": "2026-03-28T14:30:00Z",
      "book": {
        "id": 42,
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "978-0441013593"
      },
      "created_at": "2026-03-26T14:30:00Z"
    }
  ],
  "meta": {
    "current_page": 1,
    "total_pages": 3,
    "total_count": 52,
    "per_page": 25
  }
}
```

**N+1 prevention:** `Reservation.includes(:book)` — every reservation in the collection loads its book in a single query. The `book` association is included directly on the reservation (via `book_id` denormalization), so no join through `book_copies` is needed.

**Error responses:**

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| User not found | 404 | `user_not_found` | "User 1 not found" |
| Invalid status filter | 422 | `invalid_status` | "Status must be one of: active, cancelled, expired" |
| per_page > 100 | 422 | `invalid_per_page` | "Per page must be between 1 and 100" |

---

### PATCH /api/v1/reservations/:id/cancel

**Cancel a reservation.**

**Request:** No body required. The action is in the URL.

**Response — 200 OK:**
```json
{
  "reservation": {
    "id": 1,
    "user_id": 1,
    "book_id": 42,
    "book_copy_id": 7,
    "status": "cancelled",
    "expires_at": "2026-03-28T14:30:00Z",
    "book": {
      "id": 42,
      "title": "Dune",
      "author": "Frank Herbert",
      "isbn": "978-0441013593"
    },
    "created_at": "2026-03-26T14:30:00Z"
  }
}
```

**Error responses:**

| Scenario | HTTP Status | Error Code | Message |
|---|---|---|---|
| Reservation not found | 404 | `reservation_not_found` | "Reservation 1 not found" |
| Already cancelled | 422 | `already_cancelled` | "Reservation is already cancelled" |

**Note on expired reservations:** Cancelling an expired reservation is allowed — it transitions to `cancelled`. This is a deliberate UX choice: the user sees the reservation in their list and should be able to dismiss it without getting an error.

---

## Business Rules

1. **One active reservation per user per book.** Enforced at the database level with a partial unique index. Checked in application code first for a friendly error message; the index is the safety net.

2. **Reservations expire after 48 hours.** `expires_at` is set to `created_at + 48.hours` at creation time. Not configurable per reservation (could be made configurable later via a `ReservationPolicy` if needed).

3. **System assigns the copy.** The user specifies `book_id`, not `book_copy_id`. The system picks an available copy. Copy selection uses `FOR UPDATE SKIP LOCKED` for concurrency safety.

4. **Expired reservations free the copy.** Availability queries always check `expires_at > NOW()`, not just `status = 'active'`. This means a copy becomes logically available the instant the reservation expires, even before the cleanup job runs.

5. **Withdrawn copies cannot be reserved.** Only copies with condition `good` or `fair` are eligible. This is enforced in the availability query, not as a validation on the Reservation model.

6. **Cancellation is idempotent for expired reservations.** Cancelling an expired reservation transitions it to `cancelled`. Cancelling an already-cancelled reservation returns an error.

7. **No cascading deletes on reservations.** Deleting a book or copy does not delete reservations — they serve as historical records. (Books and copies should be soft-deleted or withdrawn, not hard-deleted, but that's out of scope.)

---

## Background Jobs

### ExpireReservationsJob

Runs on a recurring schedule (every 5 minutes via Sidekiq-Cron or similar).

```ruby
class ExpireReservationsJob < ApplicationJob
  queue_as :default

  def perform
    Reservation
      .where(status: 'active')
      .where('expires_at <= ?', Time.current)
      .update_all(status: 'expired', updated_at: Time.current)
  end
end
```

**Why this design:**
- `update_all` for efficiency — no model callbacks or validations needed for this transition.
- The job is idempotent — running it twice is harmless.
- Availability doesn't depend on this job (queries check `expires_at` directly), so if the job is delayed, correctness is not affected. The job is for status consistency, not for freeing copies.

---

## Architecture: Where Logic Lives

| Concern | Location | Rationale |
|---|---|---|
| Copy assignment | `ReservationService` | Business logic with concurrency handling. Too complex for a model method, too important for a controller. |
| Availability check | `BookCopy.available_for_reservation` scope | Reusable query logic. Used by the service and potentially by future endpoints (e.g., "is this book available?"). |
| Expiration query | `Reservation.active_and_unexpired` scope | Reusable. Used by availability checks and the list endpoint. |
| Param validation | Controller (strong params + explicit checks) | Thin: validate input, call service, render response. |
| Error formatting | `ApplicationController` concern or base method | DRY: one method to render the error envelope, called from every action. |
| Pagination | Controller (using `kaminari` or `pagy`) | Standard pagination gem. Meta object built in the controller, following Leach's pagination standard. |
| Expiration cleanup | `ExpireReservationsJob` | Async, periodic, idempotent. Doesn't affect request-path correctness. |

**Leach's thin-controller rule in practice:** Each controller action is roughly: (1) extract params, (2) call service or scope, (3) render response or error. No action exceeds ~15 lines.

---

## Routes

```ruby
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :reservations, only: [:create] do
        member do
          patch :cancel
        end
      end

      resources :users, only: [] do
        resources :reservations, only: [:index], module: :users
      end
    end
  end
end
```

**Routes produced:**
- `POST   /api/v1/reservations`          -> `Api::V1::ReservationsController#create`
- `PATCH  /api/v1/reservations/:id/cancel` -> `Api::V1::ReservationsController#cancel`
- `GET    /api/v1/users/:user_id/reservations` -> `Api::V1::Users::ReservationsController#index`

The list endpoint is nested under users because it's semantically "this user's reservations." The create and cancel endpoints are top-level because they operate on the reservation itself.
