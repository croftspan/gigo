# Library Book Reservation System — Implementation Plan

## Task Overview

10 tasks, ordered by dependency. Each task specifies files to create/modify, what to build, and what to test first (TDD).

---

## Task 1: Project Setup and Configuration

**Depends on:** Nothing

**Files to create:**
- New Rails 7.1 API-mode app: `rails new library_reservations --api --database=postgresql --skip-javascript --skip-asset-pipeline`
- `Gemfile` — add `rspec-rails`, `factory_bot_rails`, `shoulda-matchers`, `database_cleaner-active_record`, `sidekiq`
- `spec/rails_helper.rb` — configure FactoryBot, Shoulda Matchers, DatabaseCleaner
- `spec/support/shared_contexts.rb` — empty for now
- `config/database.yml` — verify PostgreSQL configuration

**What to build:**
- Generate the Rails app in API mode
- Install and configure RSpec (`rails generate rspec:install`)
- Configure `spec/rails_helper.rb` with FactoryBot syntax methods, Shoulda Matchers for Rails, and DatabaseCleaner strategy (transaction)
- Verify `rails db:create` and `rails db:migrate` succeed on a fresh database
- Remove `test/` directory (using RSpec instead of Minitest)

**Test first:**
- `rails db:create` succeeds
- `rspec` runs with 0 examples, 0 failures
- FactoryBot is accessible in specs

---

## Task 2: Database Migrations — Books, Copies, Users

**Depends on:** Task 1

**Files to create:**
- `db/migrate/TIMESTAMP_create_books.rb`
- `db/migrate/TIMESTAMP_create_copies.rb`
- `db/migrate/TIMESTAMP_create_users.rb`

**What to build:**

`create_books` migration:
- `title` string, null: false
- `author` string, null: false
- `isbn` string, null: false
- `copies_count` integer, null: false, default: 0
- timestamps
- `add_index :books, :isbn, unique: true`

`create_copies` migration:
- `book_id` bigint, null: false, foreign_key: true
- `inventory_number` string, null: false
- timestamps
- `add_index :copies, :book_id`
- `add_index :copies, :inventory_number, unique: true`

`create_users` migration:
- `name` string, null: false
- `email` string, null: false
- timestamps
- `add_index :users, :email, unique: true`

**Test first:**
- `rails db:migrate` succeeds
- `rails db:rollback STEP=3` succeeds
- Schema matches expected columns and indexes

---

## Task 3: Database Migration — Reservations

**Depends on:** Task 2

**Files to create:**
- `db/migrate/TIMESTAMP_create_reservations.rb`

**What to build:**

`create_reservations` migration:
- `user_id` bigint, null: false, foreign_key: true
- `book_id` bigint, null: false, foreign_key: true
- `copy_id` bigint, null: false, foreign_key: true
- `status` string, null: false, default: 'active'
- `expires_at` datetime, null: false
- timestamps
- `add_index :reservations, :user_id`
- `add_index :reservations, :book_id`
- `add_index :reservations, :copy_id`
- `add_index :reservations, [:status, :expires_at]`
- `add_index :reservations, [:copy_id, :status]`

**Test first:**
- `rails db:migrate` succeeds
- Foreign keys are enforced (inserting reservation with nonexistent user_id fails at DB level)
- All indexes exist

---

## Task 4: Models — Book, Copy, User

**Depends on:** Task 2

**Files to create/modify:**
- `app/models/book.rb`
- `app/models/copy.rb`
- `app/models/user.rb`
- `spec/models/book_spec.rb`
- `spec/models/copy_spec.rb`
- `spec/models/user_spec.rb`
- `spec/factories/books.rb`
- `spec/factories/copies.rb`
- `spec/factories/users.rb`

**What to build:**

`Book`:
- `has_many :copies, dependent: :destroy`
- `has_many :reservations, dependent: :destroy`
- Validations: `title`, `author`, `isbn` presence; `isbn` uniqueness
- Method: `available_copies_count` — `copies.count - reservations.active.count`

`Copy`:
- `belongs_to :book, counter_cache: :copies_count`
- `has_many :reservations, dependent: :destroy`
- Validations: `inventory_number` presence and uniqueness
- Scope: `available` — left outer join to reservations, exclude copies with active reservations

`User`:
- `has_many :reservations, dependent: :destroy`
- Validations: `name`, `email` presence; `email` uniqueness

**Test first (TDD order):**
1. Factory validity: `build(:book).valid?` is true, etc.
2. Validation specs: missing title, duplicate isbn, etc.
3. Association specs: `book.copies` returns copies
4. `Copy.available` scope: with no reservations, all copies available; with active reservation, that copy excluded; with expired reservation, copy available again
5. `book.available_copies_count` returns correct number

---

## Task 5: Reservation Model

**Depends on:** Task 3, Task 4

**Files to create/modify:**
- `app/models/reservation.rb`
- `spec/models/reservation_spec.rb`
- `spec/factories/reservations.rb`

**What to build:**

`Reservation`:
- `belongs_to :user`
- `belongs_to :book`
- `belongs_to :copy`
- Enum-like status handling (Rails 7.1 style): validate inclusion in `%w[active expired cancelled]`
- Validations: `status` presence and inclusion; `expires_at` presence
- Scope: `active` — `where(status: 'active').where('expires_at > ?', Time.current)`
- Scope: `expired_pending` — `where(status: 'active').where('expires_at <= ?', Time.current)`
- Scope: `cancelled` — `where(status: 'cancelled')`
- Scope: `for_book` — `where(book_id: book_id)`
- Method: `effective_status` — returns `'expired'` if status is active but `expires_at <= Time.current`, otherwise returns raw `status`
- Method: `effectively_active?` — `status == 'active' && expires_at > Time.current`
- Method: `effectively_expired?` — `expires_at <= Time.current || status == 'expired'`

**Test first (TDD order):**
1. Factory validity
2. Validation specs: missing status, invalid status value
3. `active` scope: includes reservation created 1 hour ago, excludes reservation created 49 hours ago, excludes cancelled reservation
4. `expired_pending` scope: includes reservation with `expires_at` in the past and status `active`, excludes cancelled
5. `effective_status`: active reservation returns `'active'`, expired-but-not-cleaned-up returns `'expired'`, cancelled returns `'cancelled'`
6. `effectively_active?` and `effectively_expired?` correctness with time travel (`travel_to`)

---

## Task 6: Result Object and ReservationService

**Depends on:** Task 5

**Files to create:**
- `app/services/result.rb`
- `app/services/reservation_service.rb`
- `spec/services/reservation_service_spec.rb`

**What to build:**

`Result`:
```ruby
class Result
  attr_reader :data, :error_code, :error_message, :http_status

  def initialize(success:, data: nil, error_code: nil, error_message: nil, http_status: nil)
    @success = success
    @data = data
    @error_code = error_code
    @error_message = error_message
    @http_status = http_status
  end

  def success?
    @success
  end

  def self.success(data)
    new(success: true, data: data)
  end

  def self.failure(error_code:, message:, http_status:)
    new(success: false, error_code: error_code, error_message: message, http_status: http_status)
  end
end
```

`ReservationService.create(user_id:, book_id:)`:
1. Find user or return `user_not_found` failure (404)
2. Find book or return `book_not_found` failure (404)
3. Check for duplicate active reservation (user + book) or return `duplicate_reservation` failure (422)
4. Open transaction:
   a. Lock available copies for this book: `book.copies.available.lock('FOR UPDATE').order(:id).first`
   b. If no available copy, return `no_copies_available` failure (422)
   c. Create reservation: `user_id`, `book_id`, `copy_id`, `status: 'active'`, `expires_at: Time.current + 48.hours`
5. Return success with reservation

`ReservationService.cancel(reservation_id:, user_id:)`:
1. Find reservation or return `reservation_not_found` failure (404)
2. Verify `reservation.user_id == user_id` or return `forbidden` failure (403)
3. Check `reservation.effective_status`:
   - If `'cancelled'`, return `already_cancelled` failure (422)
   - If `'expired'`, return `already_expired` failure (422)
4. Update `reservation.status = 'cancelled'`
5. Return success with reservation

`ReservationService.list_for_user(user_id:, status: 'all')`:
1. Find user or return `user_not_found` failure (404)
2. Validate status param (must be one of: `active`, `expired`, `cancelled`, `all`) or return `invalid_status` failure (422)
3. Base query: `user.reservations.includes(:book).order(created_at: :desc)`
4. Apply filter:
   - `'active'`: chain `.active`
   - `'expired'`: chain `.where(status: 'expired').or(.expired_pending)` — includes both DB-expired and time-expired
   - `'cancelled'`: chain `.cancelled`
   - `'all'`: no filter
5. Return success with reservations

**Test first (TDD order):**

Create:
1. Happy path: creates reservation, assigns a copy, sets expires_at to 48 hours from now
2. Book not found: returns failure with `book_not_found`
3. User not found: returns failure with `user_not_found`
4. No available copies: all copies reserved, returns `no_copies_available`
5. Duplicate reservation: user already has active reservation for book, returns `duplicate_reservation`
6. Expired reservation does not block: user had reservation that expired, can reserve again
7. Cancelled reservation does not block: user cancelled reservation, can reserve again
8. Copy assignment is deterministic: assigns lowest-id available copy
9. Race condition: two threads reserve last copy simultaneously, only one succeeds (test with `ActiveRecord::Base.connection.execute('BEGIN; SELECT ... FOR UPDATE')` in a separate thread)

Cancel:
1. Happy path: reservation status changes to cancelled
2. Reservation not found: returns `reservation_not_found`
3. Not owner: returns `forbidden`
4. Already cancelled: returns `already_cancelled`
5. Already expired (by time): returns `already_expired`

List:
1. Returns all reservations for user, ordered by created_at desc
2. Filters by active status correctly
3. Filters by expired status (includes both DB-expired and time-expired)
4. Filters by cancelled status
5. User not found: returns `user_not_found`
6. Invalid status param: returns `invalid_status`
7. Includes book data in results

---

## Task 7: Serializers

**Depends on:** Task 5

**Files to create:**
- `app/serializers/reservation_serializer.rb`
- `app/serializers/book_serializer.rb`
- `spec/serializers/reservation_serializer_spec.rb`

**What to build:**

`BookSerializer`:
```ruby
class BookSerializer
  def initialize(book)
    @book = book
  end

  def as_json
    {
      id: @book.id,
      title: @book.title,
      author: @book.author,
      isbn: @book.isbn
    }
  end
end
```

`ReservationSerializer`:
```ruby
class ReservationSerializer
  def initialize(reservation, include_book: false)
    @reservation = reservation
    @include_book = include_book
  end

  def as_json
    result = {
      id: @reservation.id,
      user_id: @reservation.user_id,
      book_id: @reservation.book_id,
      copy_id: @reservation.copy_id,
      status: @reservation.effective_status,
      expires_at: @reservation.expires_at.iso8601,
      created_at: @reservation.created_at.iso8601
    }
    result[:book] = BookSerializer.new(@reservation.book).as_json if @include_book
    result
  end
end
```

**Test first:**
1. Serializes all fields correctly
2. `status` field uses `effective_status`, not raw status — an expired-by-time reservation shows `"expired"`
3. Timestamps are ISO 8601 format
4. `include_book: true` nests book data
5. `include_book: false` omits book data

---

## Task 8: Controllers and Routing

**Depends on:** Task 6, Task 7

**Files to create/modify:**
- `config/routes.rb`
- `app/controllers/api/v1/base_controller.rb`
- `app/controllers/api/v1/reservations_controller.rb`
- `spec/requests/api/v1/reservations_spec.rb`

**What to build:**

Routes:
```ruby
namespace :api do
  namespace :v1 do
    resources :reservations, only: [:create, :destroy]
    get 'users/:user_id/reservations', to: 'reservations#index'
  end
end
```

`Api::V1::BaseController`:
- Inherits from `ActionController::API`
- `rescue_from ActiveRecord::RecordNotFound` -> 404 JSON
- `rescue_from ActionController::ParameterMissing` -> 422 JSON
- `rescue_from StandardError` -> 500 JSON (generic message, log the actual error)
- Private method: `render_result(result, include_book: false)` — translates Result to HTTP response

`Api::V1::ReservationsController`:

`create`:
- Strong params: `params.require(:reservation).permit(:user_id, :book_id)`
- Call `ReservationService.create(user_id:, book_id:)`
- Success: render reservation JSON, status 201
- Failure: render error JSON with appropriate status

`index`:
- Params: `params[:user_id]`, `params[:status]` (default 'all')
- Call `ReservationService.list_for_user(user_id:, status:)`
- Success: render array of reservation JSON (with `include_book: true`), status 200
- Failure: render error JSON

`destroy`:
- Params: `params[:id]`, `params[:user_id]`
- Call `ReservationService.cancel(reservation_id:, user_id:)`
- Success: render reservation JSON, status 200
- Failure: render error JSON

**Test first (request specs, TDD order):**

POST /api/v1/reservations:
1. Happy path: 201, correct JSON shape
2. Missing `reservation` key: 422
3. Missing `book_id`: 422
4. Book not found: 404, `book_not_found` error code
5. No copies available: 422, `no_copies_available` error code
6. Duplicate reservation: 422, `duplicate_reservation` error code

GET /api/v1/users/:user_id/reservations:
1. Happy path: 200, array of reservations with nested book
2. Empty list: 200, empty array
3. Status filter works: returns only matching reservations
4. User not found: 404
5. Invalid status: 422

DELETE /api/v1/reservations/:id:
1. Happy path: 200, reservation with status cancelled
2. Reservation not found: 404
3. Not owner: 403
4. Already cancelled: 422
5. Already expired: 422
6. Missing user_id param: 422

---

## Task 9: Background Expiration Job

**Depends on:** Task 5

**Files to create/modify:**
- `app/jobs/expire_reservations_job.rb`
- `spec/jobs/expire_reservations_job_spec.rb`
- `config/initializers/sidekiq.rb` (basic Sidekiq config)

**What to build:**

`ExpireReservationsJob`:
- Inherits from `ApplicationJob`, uses Sidekiq queue
- Finds all reservations where `status = 'active'` AND `expires_at <= Time.current`
- Bulk-updates them to `status = 'expired'`
- Uses `update_all` for efficiency (no callbacks needed on status change)
- Logs the count of expired reservations

**Test first:**
1. Job expires reservations past their `expires_at`: create 3 reservations (1 expired, 1 active, 1 cancelled), run job, only the expired one changes status
2. Job is idempotent: running twice doesn't cause errors
3. Job handles zero expired reservations gracefully
4. Already-expired reservations (status = 'expired') are not touched again

---

## Task 10: Integration and Edge Case Tests

**Depends on:** Tasks 1-9

**Files to create:**
- `spec/integration/reservation_lifecycle_spec.rb`

**What to build:**

End-to-end tests covering complete workflows:

1. **Full lifecycle:** Create reservation -> verify copy unavailable -> list reservations shows it -> cancel -> verify copy available again -> create new reservation for same book
2. **Expiration lifecycle:** Create reservation -> travel 49 hours forward -> list shows expired status -> create new reservation succeeds (same user, same book)
3. **Multiple copies:** Book with 3 copies -> 3 users reserve -> 4th user gets no_copies_available -> 1 cancels -> 4th user succeeds
4. **Concurrent reservations:** User reserves book A and book B simultaneously (different books) -> both succeed
5. **Duplicate prevention:** User creates reservation -> tries again -> gets duplicate_reservation -> cancels -> creates again -> succeeds
6. **Expired reservation doesn't block new one:** Create reservation -> travel 49 hours -> create again for same user/book -> succeeds, gets a (possibly different) copy
7. **Data integrity:** Cancel reservation -> verify `updated_at` changed, `created_at` unchanged, `expires_at` unchanged

---

## Dependency Graph

```
Task 1 (Setup)
  |
  v
Task 2 (Migrations: Books, Copies, Users)
  |         \
  v          v
Task 3       Task 4 (Models: Book, Copy, User)
(Migration:    |
Reservations)  |
  |           /
  v          v
Task 5 (Model: Reservation)
  |         \
  v          v
Task 6       Task 7 (Serializers)    Task 9 (Background Job)
(Service)      |
  |           /
  v          v
Task 8 (Controllers & Routes)
  |
  v
Task 10 (Integration Tests)
```

Tasks that can run in parallel:
- Task 3 and Task 4 (after Task 2)
- Task 6, Task 7, and Task 9 (after Task 5)

---

## File Inventory (all files created or modified)

| File | Task | Purpose |
|---|---|---|
| `Gemfile` | 1 | Add rspec-rails, factory_bot_rails, shoulda-matchers, database_cleaner, sidekiq |
| `spec/rails_helper.rb` | 1 | RSpec configuration |
| `spec/support/shared_contexts.rb` | 1 | Shared test contexts (placeholder) |
| `db/migrate/*_create_books.rb` | 2 | Books table |
| `db/migrate/*_create_copies.rb` | 2 | Copies table |
| `db/migrate/*_create_users.rb` | 2 | Users table |
| `db/migrate/*_create_reservations.rb` | 3 | Reservations table |
| `app/models/book.rb` | 4 | Book model |
| `app/models/copy.rb` | 4 | Copy model |
| `app/models/user.rb` | 4 | User model |
| `spec/models/book_spec.rb` | 4 | Book model tests |
| `spec/models/copy_spec.rb` | 4 | Copy model tests |
| `spec/models/user_spec.rb` | 4 | User model tests |
| `spec/factories/books.rb` | 4 | Book factory |
| `spec/factories/copies.rb` | 4 | Copy factory |
| `spec/factories/users.rb` | 4 | User factory |
| `app/models/reservation.rb` | 5 | Reservation model |
| `spec/models/reservation_spec.rb` | 5 | Reservation model tests |
| `spec/factories/reservations.rb` | 5 | Reservation factory |
| `app/services/result.rb` | 6 | Result value object |
| `app/services/reservation_service.rb` | 6 | Core business logic |
| `spec/services/reservation_service_spec.rb` | 6 | Service tests (most critical) |
| `app/serializers/reservation_serializer.rb` | 7 | Reservation JSON serializer |
| `app/serializers/book_serializer.rb` | 7 | Book JSON serializer |
| `spec/serializers/reservation_serializer_spec.rb` | 7 | Serializer tests |
| `config/routes.rb` | 8 | API routes |
| `app/controllers/api/v1/base_controller.rb` | 8 | Base controller with error handling |
| `app/controllers/api/v1/reservations_controller.rb` | 8 | Reservations endpoints |
| `spec/requests/api/v1/reservations_spec.rb` | 8 | Request specs |
| `app/jobs/expire_reservations_job.rb` | 9 | Background expiration job |
| `spec/jobs/expire_reservations_job_spec.rb` | 9 | Job tests |
| `config/initializers/sidekiq.rb` | 9 | Sidekiq configuration |
| `spec/integration/reservation_lifecycle_spec.rb` | 10 | End-to-end integration tests |
