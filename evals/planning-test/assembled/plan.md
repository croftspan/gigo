# Library Book Reservation System — Implementation Plan

## Dependency Graph

```
Task 1: Project setup
  └─> Task 2: Book + BookCopy migrations, models, factories
      └─> Task 3: User migration, model, factory
          └─> Task 4: Reservation migration, model, factory
              ├─> Task 5: ReservationService (create logic)
              │   └─> Task 7: POST /api/v1/reservations
              ├─> Task 6: List reservations scope + pagination
              │   └─> Task 8: GET /api/v1/users/:user_id/reservations
              └─> Task 9: PATCH /api/v1/reservations/:id/cancel
                  └─> Task 10: ExpireReservationsJob
                      └─> Task 11: Integration & edge case specs
```

---

## Task 1: Project Setup

**Goal:** Rails 7.1 API-only app with PostgreSQL, RSpec, FactoryBot, and essential gems.

**Files to create/modify:**
- Generate new app: `rails new library_reservations --api --database=postgresql -T`
- `Gemfile` — add: `rspec-rails`, `factory_bot_rails`, `faker`, `pagy`, `sidekiq`
- `spec/rails_helper.rb` — configure FactoryBot, database cleaner strategy
- `spec/support/factory_bot.rb` — `config.include FactoryBot::Syntax::Methods`
- `spec/support/pagy.rb` — include Pagy helpers in request specs if needed
- `config/application.rb` — confirm API-only mode, set default time zone to UTC

**Commands:**
```bash
rails new library_reservations --api --database=postgresql -T
cd library_reservations
# Add gems to Gemfile
bundle install
rails generate rspec:install
rails db:create
```

**Test first (Beck):** Verify the setup works.
```bash
bundle exec rspec  # Should run 0 examples, 0 failures
rails db:migrate:status  # Should show no migrations
```

**No dependencies. This is the starting point.**

---

## Task 2: Book and BookCopy — Migration, Model, Factory, Specs

**Goal:** Create the Book and BookCopy tables with proper indexes, models with validations, and factories.

### Test first

**File: `spec/models/book_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe Book, type: :model do
  describe 'validations' do
    subject { build(:book) }

    it { is_expected.to validate_presence_of(:title) }
    it { is_expected.to validate_presence_of(:author) }
    it { is_expected.to validate_presence_of(:isbn) }
    it { is_expected.to validate_uniqueness_of(:isbn) }
  end

  describe 'associations' do
    it { is_expected.to have_many(:book_copies).dependent(:destroy) }
    it { is_expected.to have_many(:reservations) }
  end
end
```

**File: `spec/models/book_copy_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe BookCopy, type: :model do
  describe 'validations' do
    subject { build(:book_copy) }

    it { is_expected.to validate_presence_of(:copy_number) }
    it { is_expected.to validate_uniqueness_of(:copy_number).scoped_to(:book_id) }
    it { is_expected.to validate_presence_of(:condition) }
    it { is_expected.to validate_inclusion_of(:condition).in_array(%w[good fair poor withdrawn]) }
  end

  describe 'associations' do
    it { is_expected.to belong_to(:book) }
    it { is_expected.to have_many(:reservations) }
  end

  describe '.available_for_reservation' do
    let(:book) { create(:book) }
    let!(:good_copy) { create(:book_copy, book: book, condition: 'good') }
    let!(:fair_copy) { create(:book_copy, book: book, condition: 'fair') }
    let!(:withdrawn_copy) { create(:book_copy, book: book, condition: 'withdrawn') }

    it 'includes copies in good and fair condition' do
      expect(BookCopy.available_for_reservation).to include(good_copy, fair_copy)
    end

    it 'excludes withdrawn copies' do
      expect(BookCopy.available_for_reservation).not_to include(withdrawn_copy)
    end

    # Reservation-aware tests added in Task 4 after Reservation model exists
  end
end
```

### Implement

**File: `db/migrate/001_create_books.rb`**
```ruby
class CreateBooks < ActiveRecord::Migration[7.1]
  def change
    create_table :books do |t|
      t.string :title, null: false
      t.string :author, null: false
      t.string :isbn, null: false

      t.timestamps
    end

    add_index :books, :isbn, unique: true
  end
end
```

**File: `db/migrate/002_create_book_copies.rb`**
```ruby
class CreateBookCopies < ActiveRecord::Migration[7.1]
  def change
    create_table :book_copies do |t|
      t.references :book, null: false, foreign_key: true
      t.integer :copy_number, null: false
      t.string :condition, null: false, default: 'good'

      t.timestamps
    end

    add_index :book_copies, [:book_id, :copy_number], unique: true
  end
end
```

**File: `app/models/book.rb`** — As specified in spec.

**File: `app/models/book_copy.rb`** — As specified in spec.

**File: `spec/factories/books.rb`**
```ruby
FactoryBot.define do
  factory :book do
    title { Faker::Book.title }
    author { Faker::Book.author }
    sequence(:isbn) { |n| "978-#{n.to_s.rjust(10, '0')}" }
  end
end
```

**File: `spec/factories/book_copies.rb`**
```ruby
FactoryBot.define do
  factory :book_copy do
    book
    sequence(:copy_number) { |n| n }
    condition { 'good' }
  end
end
```

**Verify:**
```bash
rails db:migrate
bundle exec rspec spec/models/book_spec.rb spec/models/book_copy_spec.rb
```

**Kane's checklist:** Migration uses `change` (reversible). No default on large table (table is new). Unique index on isbn. Composite unique index on (book_id, copy_number).

**Depends on:** Task 1.

---

## Task 3: User — Migration, Model, Factory, Specs

**Goal:** Minimal user model for reservation ownership.

### Test first

**File: `spec/models/user_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe User, type: :model do
  describe 'validations' do
    subject { build(:user) }

    it { is_expected.to validate_presence_of(:name) }
    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email) }
  end

  describe 'associations' do
    it { is_expected.to have_many(:reservations) }
  end
end
```

### Implement

**File: `db/migrate/003_create_users.rb`**
```ruby
class CreateUsers < ActiveRecord::Migration[7.1]
  def change
    create_table :users do |t|
      t.string :name, null: false
      t.string :email, null: false

      t.timestamps
    end

    add_index :users, :email, unique: true
  end
end
```

**File: `app/models/user.rb`** — As specified in spec.

**File: `spec/factories/users.rb`**
```ruby
FactoryBot.define do
  factory :user do
    name { Faker::Name.name }
    sequence(:email) { |n| "user#{n}@example.com" }
  end
end
```

**Verify:**
```bash
rails db:migrate
bundle exec rspec spec/models/user_spec.rb
```

**Depends on:** Task 1.

---

## Task 4: Reservation — Migration, Model, Factory, Specs

**Goal:** Reservation table with partial unique index, model with scopes, factory.

### Test first

**File: `spec/models/reservation_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe Reservation, type: :model do
  describe 'validations' do
    it { is_expected.to validate_presence_of(:status) }
    it { is_expected.to validate_inclusion_of(:status).in_array(%w[active cancelled expired]) }
    it { is_expected.to validate_presence_of(:expires_at) }
  end

  describe 'associations' do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to belong_to(:book) }
    it { is_expected.to belong_to(:book_copy) }
  end

  describe '.active_and_unexpired' do
    let(:user) { create(:user) }
    let(:book) { create(:book) }
    let(:copy1) { create(:book_copy, book: book, copy_number: 1) }
    let(:copy2) { create(:book_copy, book: book, copy_number: 2) }
    let(:copy3) { create(:book_copy, book: book, copy_number: 3) }

    let!(:active_reservation) do
      create(:reservation, user: user, book: book, book_copy: copy1,
             status: 'active', expires_at: 24.hours.from_now)
    end
    let!(:expired_reservation) do
      create(:reservation, user: user, book: book, book_copy: copy2,
             status: 'active', expires_at: 1.hour.ago)
    end
    let!(:cancelled_reservation) do
      create(:reservation, user: user, book: book, book_copy: copy3,
             status: 'cancelled', expires_at: 24.hours.from_now)
    end

    it 'includes active reservations that have not expired' do
      expect(described_class.active_and_unexpired).to contain_exactly(active_reservation)
    end

    it 'excludes reservations with expires_at in the past' do
      expect(described_class.active_and_unexpired).not_to include(expired_reservation)
    end

    it 'excludes cancelled reservations' do
      expect(described_class.active_and_unexpired).not_to include(cancelled_reservation)
    end
  end

  describe '#expired?' do
    it 'returns true for active reservation past expires_at' do
      reservation = build(:reservation, status: 'active', expires_at: 1.hour.ago)
      expect(reservation.expired?).to be true
    end

    it 'returns false for active reservation before expires_at' do
      reservation = build(:reservation, status: 'active', expires_at: 1.hour.from_now)
      expect(reservation.expired?).to be false
    end

    it 'returns false for cancelled reservation past expires_at' do
      reservation = build(:reservation, status: 'cancelled', expires_at: 1.hour.ago)
      expect(reservation.expired?).to be false
    end
  end

  describe '#cancel!' do
    it 'updates status to cancelled' do
      reservation = create(:reservation)
      reservation.cancel!
      expect(reservation.reload.status).to eq('cancelled')
    end
  end

  describe 'partial unique index enforcement' do
    it 'prevents two active reservations for the same user and book' do
      user = create(:user)
      book = create(:book)
      copy1 = create(:book_copy, book: book, copy_number: 1)
      copy2 = create(:book_copy, book: book, copy_number: 2)

      create(:reservation, user: user, book: book, book_copy: copy1, status: 'active')

      expect {
        create(:reservation, user: user, book: book, book_copy: copy2, status: 'active')
      }.to raise_error(ActiveRecord::RecordNotUnique)
    end

    it 'allows a new active reservation after the previous is cancelled' do
      user = create(:user)
      book = create(:book)
      copy1 = create(:book_copy, book: book, copy_number: 1)
      copy2 = create(:book_copy, book: book, copy_number: 2)

      old = create(:reservation, user: user, book: book, book_copy: copy1, status: 'active')
      old.cancel!

      expect {
        create(:reservation, user: user, book: book, book_copy: copy2, status: 'active')
      }.not_to raise_error
    end
  end
end
```

### Implement

**File: `db/migrate/004_create_reservations.rb`**
```ruby
class CreateReservations < ActiveRecord::Migration[7.1]
  def up
    create_table :reservations do |t|
      t.references :user, null: false, foreign_key: true
      t.references :book, null: false, foreign_key: true
      t.references :book_copy, null: false, foreign_key: true
      t.string :status, null: false, default: 'active'
      t.datetime :expires_at, null: false

      t.timestamps
    end

    add_index :reservations, [:status, :expires_at],
              name: 'index_reservations_on_status_and_expires_at'

    execute <<-SQL
      CREATE UNIQUE INDEX index_reservations_on_user_book_active
      ON reservations (user_id, book_id)
      WHERE status = 'active'
    SQL
  end

  def down
    remove_index :reservations, name: 'index_reservations_on_user_book_active'
    remove_index :reservations, name: 'index_reservations_on_status_and_expires_at'
    drop_table :reservations
  end
end
```

**File: `app/models/reservation.rb`** — As specified in spec.

**File: `spec/factories/reservations.rb`**
```ruby
FactoryBot.define do
  factory :reservation do
    user
    book { association :book }
    book_copy { association :book_copy, book: book }
    status { 'active' }
    expires_at { 48.hours.from_now }
  end
end
```

**Verify:**
```bash
rails db:migrate
bundle exec rspec spec/models/reservation_spec.rb
```

**Kane's checklist:** This migration uses `up`/`down` because the partial unique index requires raw SQL. The `down` method properly removes the indexes before dropping the table. Reversibility verified.

**Depends on:** Tasks 2 and 3.

---

## Task 5: ReservationService — Create Logic with Concurrency Handling

**Goal:** Service object that assigns a copy and creates a reservation, handling all edge cases.

### Test first

**File: `spec/services/reservation_service_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe ReservationService do
  describe '.create' do
    let(:user) { create(:user) }
    let(:book) { create(:book) }
    let!(:copy) { create(:book_copy, book: book, condition: 'good') }

    context 'happy path' do
      it 'creates a reservation' do
        result = described_class.create(user_id: user.id, book_id: book.id)

        expect(result.success?).to be true
        expect(result.reservation).to be_persisted
        expect(result.reservation.user).to eq(user)
        expect(result.reservation.book).to eq(book)
        expect(result.reservation.book_copy).to eq(copy)
        expect(result.reservation.status).to eq('active')
      end

      it 'sets expires_at to 48 hours from now' do
        freeze_time do
          result = described_class.create(user_id: user.id, book_id: book.id)
          expect(result.reservation.expires_at).to be_within(1.second).of(48.hours.from_now)
        end
      end
    end

    context 'when book not found' do
      it 'returns error' do
        result = described_class.create(user_id: user.id, book_id: 0)

        expect(result.success?).to be false
        expect(result.error_code).to eq('book_not_found')
      end
    end

    context 'when user not found' do
      it 'returns error' do
        result = described_class.create(user_id: 0, book_id: book.id)

        expect(result.success?).to be false
        expect(result.error_code).to eq('user_not_found')
      end
    end

    context 'when user already has an active reservation for this book' do
      before do
        create(:reservation, user: user, book: book, book_copy: copy, status: 'active')
      end

      it 'returns duplicate_reservation error' do
        other_copy = create(:book_copy, book: book, copy_number: 2)
        result = described_class.create(user_id: user.id, book_id: book.id)

        expect(result.success?).to be false
        expect(result.error_code).to eq('duplicate_reservation')
      end
    end

    context 'when all copies are reserved' do
      before do
        other_user = create(:user)
        create(:reservation, user: other_user, book: book, book_copy: copy, status: 'active')
      end

      it 'returns no_copies_available error' do
        result = described_class.create(user_id: user.id, book_id: book.id)

        expect(result.success?).to be false
        expect(result.error_code).to eq('no_copies_available')
      end
    end

    context 'when only withdrawn copies remain' do
      before { copy.update!(condition: 'withdrawn') }

      it 'returns no_copies_available error' do
        result = described_class.create(user_id: user.id, book_id: book.id)

        expect(result.success?).to be false
        expect(result.error_code).to eq('no_copies_available')
      end
    end

    context 'when a reservation has expired (not yet cleaned up)' do
      before do
        other_user = create(:user)
        create(:reservation, user: other_user, book: book, book_copy: copy,
               status: 'active', expires_at: 1.hour.ago)
      end

      it 'treats the copy as available' do
        result = described_class.create(user_id: user.id, book_id: book.id)

        expect(result.success?).to be true
        expect(result.reservation.book_copy).to eq(copy)
      end
    end

    context 'with multiple copies' do
      let!(:copy2) { create(:book_copy, book: book, copy_number: 2) }

      it 'assigns an available copy when first is taken' do
        other_user = create(:user)
        create(:reservation, user: other_user, book: book, book_copy: copy, status: 'active')

        result = described_class.create(user_id: user.id, book_id: book.id)

        expect(result.success?).to be true
        expect(result.reservation.book_copy).to eq(copy2)
      end
    end
  end
end
```

### Implement

**File: `app/services/reservation_service.rb`** — As specified in spec.

**Verify:**
```bash
bundle exec rspec spec/services/reservation_service_spec.rb
```

**Depends on:** Task 4.

---

## Task 6: Error Rendering Concern and Base Controller Setup

**Goal:** Consistent error envelope rendering, pagination setup, and shared serialization.

### Test first

No dedicated spec — this is infrastructure tested through the request specs in Tasks 7-9. But we verify the error helper renders the correct shape.

### Implement

**File: `app/controllers/concerns/error_renderable.rb`**
```ruby
module ErrorRenderable
  extend ActiveSupport::Concern

  private

  def render_error(code:, message:, status:, details: nil)
    body = { error: { code: code, message: message } }
    body[:error][:details] = details if details.present?
    render json: body, status: status
  end

  def render_not_found(resource, id)
    render_error(
      code: "#{resource}_not_found",
      message: "#{resource.capitalize} #{id} not found",
      status: :not_found
    )
  end
end
```

**File: `app/controllers/application_controller.rb`**
```ruby
class ApplicationController < ActionController::API
  include ErrorRenderable
  include Pagy::Backend
end
```

**File: `app/controllers/concerns/paginatable.rb`**
```ruby
module Paginatable
  extend ActiveSupport::Concern

  private

  def pagination_params
    page = (params[:page] || 1).to_i
    per_page = (params[:per_page] || 25).to_i
    per_page = [[per_page, 1].max, 100].min  # Clamp between 1 and 100
    [page, per_page]
  end

  def pagination_meta(pagy)
    {
      current_page: pagy.page,
      total_pages: pagy.pages,
      total_count: pagy.count,
      per_page: pagy.limit
    }
  end
end
```

**Depends on:** Task 1.

---

## Task 7: POST /api/v1/reservations — Request Spec and Controller

**Goal:** Create reservation endpoint with full error handling.

### Test first

**File: `spec/requests/api/v1/reservations_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe 'POST /api/v1/reservations', type: :request do
  let(:user) { create(:user) }
  let(:book) { create(:book) }
  let!(:copy) { create(:book_copy, book: book) }

  describe 'happy path' do
    it 'creates a reservation and returns 201' do
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }

      expect(response).to have_http_status(:created)

      json = response.parsed_body
      expect(json['reservation']['id']).to be_present
      expect(json['reservation']['user_id']).to eq(user.id)
      expect(json['reservation']['book_id']).to eq(book.id)
      expect(json['reservation']['book_copy_id']).to eq(copy.id)
      expect(json['reservation']['status']).to eq('active')
      expect(json['reservation']['expires_at']).to be_present
      expect(json['reservation']['book']['title']).to eq(book.title)
    end
  end

  describe 'error cases' do
    it 'returns 404 when book not found' do
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: 0 }
      }

      expect(response).to have_http_status(:not_found)
      json = response.parsed_body
      expect(json['error']['code']).to eq('book_not_found')
    end

    it 'returns 404 when user not found' do
      post '/api/v1/reservations', params: {
        reservation: { user_id: 0, book_id: book.id }
      }

      expect(response).to have_http_status(:not_found)
      json = response.parsed_body
      expect(json['error']['code']).to eq('user_not_found')
    end

    it 'returns 422 when no copies available' do
      other_user = create(:user)
      create(:reservation, user: other_user, book: book, book_copy: copy)

      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }

      expect(response).to have_http_status(:unprocessable_entity)
      json = response.parsed_body
      expect(json['error']['code']).to eq('no_copies_available')
    end

    it 'returns 422 when user already has active reservation for this book' do
      create(:reservation, user: user, book: book, book_copy: copy)
      copy2 = create(:book_copy, book: book, copy_number: 2)

      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }

      expect(response).to have_http_status(:unprocessable_entity)
      json = response.parsed_body
      expect(json['error']['code']).to eq('duplicate_reservation')
    end

    it 'returns 422 when book_id is missing' do
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id }
      }

      expect(response).to have_http_status(:unprocessable_entity)
      json = response.parsed_body
      expect(json['error']['code']).to eq('validation_error')
    end

    it 'returns 422 when user_id is missing' do
      post '/api/v1/reservations', params: {
        reservation: { book_id: book.id }
      }

      expect(response).to have_http_status(:unprocessable_entity)
      json = response.parsed_body
      expect(json['error']['code']).to eq('validation_error')
    end
  end
end
```

### Implement

**File: `config/routes.rb`** — Add routes as specified in spec.

**File: `app/controllers/api/v1/reservations_controller.rb`**
```ruby
module Api
  module V1
    class ReservationsController < ApplicationController
      def create
        user_id = reservation_params[:user_id]
        book_id = reservation_params[:book_id]

        if user_id.blank?
          return render_error(code: 'validation_error', message: 'User ID is required', status: :unprocessable_entity)
        end

        if book_id.blank?
          return render_error(code: 'validation_error', message: 'Book ID is required', status: :unprocessable_entity)
        end

        result = ReservationService.create(user_id: user_id, book_id: book_id)

        if result.success?
          render json: { reservation: serialize_reservation(result.reservation) }, status: :created
        else
          status = result.error_code.end_with?('_not_found') ? :not_found : :unprocessable_entity
          render_error(code: result.error_code, message: result.error_message, status: status)
        end
      end

      def cancel
        reservation = Reservation.find_by(id: params[:id])
        return render_not_found('reservation', params[:id]) unless reservation

        if reservation.status == 'cancelled'
          return render_error(
            code: 'already_cancelled',
            message: 'Reservation is already cancelled',
            status: :unprocessable_entity
          )
        end

        reservation.cancel!
        render json: { reservation: serialize_reservation(reservation) }
      end

      private

      def reservation_params
        params.require(:reservation).permit(:user_id, :book_id)
      end

      def serialize_reservation(reservation)
        book = reservation.book
        {
          id: reservation.id,
          user_id: reservation.user_id,
          book_id: reservation.book_id,
          book_copy_id: reservation.book_copy_id,
          status: reservation.status,
          expires_at: reservation.expires_at.iso8601,
          book: {
            id: book.id,
            title: book.title,
            author: book.author,
            isbn: book.isbn
          },
          created_at: reservation.created_at.iso8601
        }
      end
    end
  end
end
```

**Verify:**
```bash
bundle exec rspec spec/requests/api/v1/reservations_spec.rb
```

**Depends on:** Tasks 5 and 6.

---

## Task 8: GET /api/v1/users/:user_id/reservations — Request Spec and Controller

**Goal:** Paginated list of a user's reservations with status filtering and N+1 prevention.

### Test first

**File: `spec/requests/api/v1/users/reservations_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe 'GET /api/v1/users/:user_id/reservations', type: :request do
  let(:user) { create(:user) }
  let(:book) { create(:book) }
  let(:copy) { create(:book_copy, book: book) }

  describe 'happy path' do
    before do
      create(:reservation, user: user, book: book, book_copy: copy)
    end

    it 'returns paginated reservations with book data' do
      get "/api/v1/users/#{user.id}/reservations"

      expect(response).to have_http_status(:ok)

      json = response.parsed_body
      expect(json['reservations'].length).to eq(1)
      expect(json['reservations'][0]['book']['title']).to eq(book.title)
      expect(json['meta']['current_page']).to eq(1)
      expect(json['meta']['total_count']).to eq(1)
      expect(json['meta']['per_page']).to eq(25)
    end
  end

  describe 'status filtering' do
    let(:book2) { create(:book) }
    let(:copy2) { create(:book_copy, book: book2) }

    before do
      create(:reservation, user: user, book: book, book_copy: copy, status: 'active')
      create(:reservation, user: user, book: book2, book_copy: copy2, status: 'cancelled')
    end

    it 'filters by active status' do
      get "/api/v1/users/#{user.id}/reservations", params: { status: 'active' }

      json = response.parsed_body
      expect(json['reservations'].length).to eq(1)
      expect(json['reservations'][0]['status']).to eq('active')
    end

    it 'returns error for invalid status' do
      get "/api/v1/users/#{user.id}/reservations", params: { status: 'bogus' }

      expect(response).to have_http_status(:unprocessable_entity)
      json = response.parsed_body
      expect(json['error']['code']).to eq('invalid_status')
    end
  end

  describe 'pagination' do
    before do
      30.times do |i|
        b = create(:book, isbn: "978-#{i.to_s.rjust(10, '0')}")
        c = create(:book_copy, book: b)
        create(:reservation, user: user, book: b, book_copy: c)
      end
    end

    it 'defaults to 25 per page' do
      get "/api/v1/users/#{user.id}/reservations"

      json = response.parsed_body
      expect(json['reservations'].length).to eq(25)
      expect(json['meta']['total_pages']).to eq(2)
    end

    it 'respects per_page param' do
      get "/api/v1/users/#{user.id}/reservations", params: { per_page: 10 }

      json = response.parsed_body
      expect(json['reservations'].length).to eq(10)
    end

    it 'caps per_page at 100' do
      get "/api/v1/users/#{user.id}/reservations", params: { per_page: 200 }

      json = response.parsed_body
      expect(json['meta']['per_page']).to eq(100)
    end
  end

  describe 'error cases' do
    it 'returns 404 for non-existent user' do
      get '/api/v1/users/0/reservations'

      expect(response).to have_http_status(:not_found)
      json = response.parsed_body
      expect(json['error']['code']).to eq('user_not_found')
    end
  end

  describe 'N+1 prevention' do
    before do
      3.times do |i|
        b = create(:book, isbn: "978-#{i.to_s.rjust(10, '0')}")
        c = create(:book_copy, book: b)
        create(:reservation, user: user, book: b, book_copy: c)
      end
    end

    it 'loads books without N+1 queries' do
      # Warm up
      get "/api/v1/users/#{user.id}/reservations"

      query_count = 0
      counter = lambda { |_name, _start, _finish, _id, payload|
        query_count += 1 unless payload[:name] == 'SCHEMA' || payload[:cached]
      }

      ActiveSupport::Notifications.subscribed(counter, 'sql.active_record') do
        get "/api/v1/users/#{user.id}/reservations"
      end

      # Expected: 1 user lookup + 1 reservations query + 1 books eager load + 1 count = 4
      # N+1 would be: 1 + 1 + 3 (one per reservation) + 1 = 6+
      expect(query_count).to be <= 5
    end
  end
end
```

### Implement

**File: `app/controllers/api/v1/users/reservations_controller.rb`**
```ruby
module Api
  module V1
    module Users
      class ReservationsController < ApplicationController
        include Paginatable

        VALID_STATUSES = %w[active cancelled expired].freeze

        def index
          user = User.find_by(id: params[:user_id])
          return render_not_found('user', params[:user_id]) unless user

          if params[:status].present? && !VALID_STATUSES.include?(params[:status])
            return render_error(
              code: 'invalid_status',
              message: "Status must be one of: #{VALID_STATUSES.join(', ')}",
              status: :unprocessable_entity
            )
          end

          page, per_page = pagination_params
          scope = user.reservations.includes(:book).order(created_at: :desc)
          scope = scope.where(status: params[:status]) if params[:status].present?

          pagy, reservations = pagy(scope, limit: per_page, page: page)

          render json: {
            reservations: reservations.map { |r| serialize_reservation(r) },
            meta: pagination_meta(pagy)
          }
        end

        private

        def serialize_reservation(reservation)
          book = reservation.book
          {
            id: reservation.id,
            user_id: reservation.user_id,
            book_id: reservation.book_id,
            book_copy_id: reservation.book_copy_id,
            status: reservation.status,
            expires_at: reservation.expires_at.iso8601,
            book: {
              id: book.id,
              title: book.title,
              author: book.author,
              isbn: book.isbn
            },
            created_at: reservation.created_at.iso8601
          }
        end
      end
    end
  end
end
```

**Verify:**
```bash
bundle exec rspec spec/requests/api/v1/users/reservations_spec.rb
```

**Leach's checklist:** Paginated (default 25, max 100). Includes book data with `includes(:book)`. Consistent error envelope. No business logic in controller.

**Depends on:** Tasks 4 and 6.

---

## Task 9: PATCH /api/v1/reservations/:id/cancel — Request Spec

**Goal:** Cancel endpoint with error handling (already implemented in Task 7's controller, now spec it).

### Test first

**File: `spec/requests/api/v1/cancel_reservation_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe 'PATCH /api/v1/reservations/:id/cancel', type: :request do
  let(:user) { create(:user) }
  let(:book) { create(:book) }
  let(:copy) { create(:book_copy, book: book) }

  describe 'happy path' do
    it 'cancels an active reservation' do
      reservation = create(:reservation, user: user, book: book, book_copy: copy, status: 'active')

      patch "/api/v1/reservations/#{reservation.id}/cancel"

      expect(response).to have_http_status(:ok)
      json = response.parsed_body
      expect(json['reservation']['status']).to eq('cancelled')
      expect(reservation.reload.status).to eq('cancelled')
    end

    it 'allows cancelling an expired reservation' do
      reservation = create(:reservation, user: user, book: book, book_copy: copy,
                           status: 'active', expires_at: 1.hour.ago)

      patch "/api/v1/reservations/#{reservation.id}/cancel"

      expect(response).to have_http_status(:ok)
      json = response.parsed_body
      expect(json['reservation']['status']).to eq('cancelled')
    end
  end

  describe 'error cases' do
    it 'returns 404 for non-existent reservation' do
      patch '/api/v1/reservations/0/cancel'

      expect(response).to have_http_status(:not_found)
      json = response.parsed_body
      expect(json['error']['code']).to eq('reservation_not_found')
    end

    it 'returns 422 for already cancelled reservation' do
      reservation = create(:reservation, user: user, book: book, book_copy: copy, status: 'cancelled')

      patch "/api/v1/reservations/#{reservation.id}/cancel"

      expect(response).to have_http_status(:unprocessable_entity)
      json = response.parsed_body
      expect(json['error']['code']).to eq('already_cancelled')
    end
  end

  describe 'side effects' do
    it 'frees the copy for new reservations' do
      reservation = create(:reservation, user: user, book: book, book_copy: copy, status: 'active')

      patch "/api/v1/reservations/#{reservation.id}/cancel"

      other_user = create(:user)
      post '/api/v1/reservations', params: {
        reservation: { user_id: other_user.id, book_id: book.id }
      }

      expect(response).to have_http_status(:created)
    end
  end
end
```

### Implement

The `cancel` action is already in `Api::V1::ReservationsController` from Task 7. No additional implementation needed — just ensure the route is wired.

**Verify:**
```bash
bundle exec rspec spec/requests/api/v1/cancel_reservation_spec.rb
```

**Depends on:** Task 7.

---

## Task 10: ExpireReservationsJob

**Goal:** Background job to mark expired reservations, with specs.

### Test first

**File: `spec/jobs/expire_reservations_job_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe ExpireReservationsJob, type: :job do
  let(:user) { create(:user) }
  let(:book) { create(:book) }
  let(:copy1) { create(:book_copy, book: book, copy_number: 1) }
  let(:copy2) { create(:book_copy, book: book, copy_number: 2) }
  let(:copy3) { create(:book_copy, book: book, copy_number: 3) }

  it 'marks expired active reservations as expired' do
    reservation = create(:reservation, user: user, book: book, book_copy: copy1,
                         status: 'active', expires_at: 1.hour.ago)

    described_class.perform_now

    expect(reservation.reload.status).to eq('expired')
  end

  it 'does not touch active reservations that have not expired' do
    reservation = create(:reservation, user: user, book: book, book_copy: copy1,
                         status: 'active', expires_at: 24.hours.from_now)

    described_class.perform_now

    expect(reservation.reload.status).to eq('active')
  end

  it 'does not touch cancelled reservations' do
    reservation = create(:reservation, user: user, book: book, book_copy: copy1,
                         status: 'cancelled', expires_at: 1.hour.ago)

    described_class.perform_now

    expect(reservation.reload.status).to eq('cancelled')
  end

  it 'is idempotent — running twice has same effect' do
    reservation = create(:reservation, user: user, book: book, book_copy: copy1,
                         status: 'active', expires_at: 1.hour.ago)

    described_class.perform_now
    described_class.perform_now

    expect(reservation.reload.status).to eq('expired')
  end

  it 'handles multiple expired reservations in one pass' do
    r1 = create(:reservation, user: user, book: book, book_copy: copy1,
                status: 'active', expires_at: 2.hours.ago)

    user2 = create(:user)
    book2 = create(:book)
    r2 = create(:reservation, user: user2, book: book2, book_copy: copy2,
                status: 'active', expires_at: 1.hour.ago)

    r3 = create(:reservation, user: create(:user), book: create(:book), book_copy: copy3,
                status: 'active', expires_at: 24.hours.from_now)

    described_class.perform_now

    expect(r1.reload.status).to eq('expired')
    expect(r2.reload.status).to eq('expired')
    expect(r3.reload.status).to eq('active')
  end
end
```

### Implement

**File: `app/jobs/expire_reservations_job.rb`**
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

**Sidekiq scheduling (config/sidekiq.yml or initializer):**
```yaml
:schedule:
  expire_reservations:
    every: '5m'
    class: ExpireReservationsJob
```

Note: This requires `sidekiq-cron` or `sidekiq-scheduler` gem. Alternatively, use `whenever` gem for cron-based scheduling. The simplest approach for "keep it simple" is to add `sidekiq-scheduler` to the Gemfile.

**Verify:**
```bash
bundle exec rspec spec/jobs/expire_reservations_job_spec.rb
```

**Depends on:** Task 4.

---

## Task 11: Integration and Edge Case Specs

**Goal:** End-to-end scenarios that cross service boundaries and test the full request lifecycle.

### Test first (and only — these are pure verification)

**File: `spec/requests/api/v1/reservation_integration_spec.rb`**
```ruby
require 'rails_helper'

RSpec.describe 'Reservation lifecycle integration', type: :request do
  let(:user) { create(:user) }
  let(:book) { create(:book) }
  let!(:copy1) { create(:book_copy, book: book, copy_number: 1) }
  let!(:copy2) { create(:book_copy, book: book, copy_number: 2) }

  describe 'full lifecycle: create -> list -> cancel -> re-reserve' do
    it 'works end to end' do
      # 1. Create reservation
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)
      reservation_id = response.parsed_body['reservation']['id']

      # 2. List shows the reservation
      get "/api/v1/users/#{user.id}/reservations"
      expect(response).to have_http_status(:ok)
      expect(response.parsed_body['reservations'].length).to eq(1)

      # 3. Cancel the reservation
      patch "/api/v1/reservations/#{reservation_id}/cancel"
      expect(response).to have_http_status(:ok)
      expect(response.parsed_body['reservation']['status']).to eq('cancelled')

      # 4. Can re-reserve the same book
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)

      # 5. List shows both reservations
      get "/api/v1/users/#{user.id}/reservations"
      expect(response.parsed_body['reservations'].length).to eq(2)
    end
  end

  describe 'copy exhaustion and recovery' do
    it 'fails when all copies taken, succeeds after cancellation' do
      user2 = create(:user)

      # User 1 takes copy 1
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)
      user1_reservation_id = response.parsed_body['reservation']['id']

      # User 2 takes copy 2
      post '/api/v1/reservations', params: {
        reservation: { user_id: user2.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)

      # User 3 can't get a copy
      user3 = create(:user)
      post '/api/v1/reservations', params: {
        reservation: { user_id: user3.id, book_id: book.id }
      }
      expect(response).to have_http_status(:unprocessable_entity)
      expect(response.parsed_body['error']['code']).to eq('no_copies_available')

      # User 1 cancels
      patch "/api/v1/reservations/#{user1_reservation_id}/cancel"
      expect(response).to have_http_status(:ok)

      # Now User 3 can reserve
      post '/api/v1/reservations', params: {
        reservation: { user_id: user3.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)
    end
  end

  describe 'expiration recovery' do
    it 'allows reservation after previous expires' do
      # User 1 reserves
      post '/api/v1/reservations', params: {
        reservation: { user_id: user.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)

      # Simulate expiration by manipulating the DB directly
      Reservation.last.update_columns(expires_at: 1.hour.ago)

      # User 2 can reserve the same book (expired reservation doesn't block)
      user2 = create(:user)
      post '/api/v1/reservations', params: {
        reservation: { user_id: user2.id, book_id: book.id }
      }
      expect(response).to have_http_status(:created)
    end
  end
end
```

**Verify:**
```bash
bundle exec rspec spec/requests/api/v1/reservation_integration_spec.rb
# Then run full suite:
bundle exec rspec
```

**Depends on:** Tasks 7, 8, 9, 10.

---

## Summary: Implementation Order

| Order | Task | What | Test files | Depends on |
|---|---|---|---|---|
| 1 | Task 1 | Project setup | (setup verification) | None |
| 2 | Task 2 | Book + BookCopy | `spec/models/book_spec.rb`, `spec/models/book_copy_spec.rb` | Task 1 |
| 3 | Task 3 | User | `spec/models/user_spec.rb` | Task 1 |
| 4 | Task 6 | Error rendering + pagination concerns | (tested via request specs) | Task 1 |
| 5 | Task 4 | Reservation model | `spec/models/reservation_spec.rb` | Tasks 2, 3 |
| 6 | Task 5 | ReservationService | `spec/services/reservation_service_spec.rb` | Task 4 |
| 7 | Task 7 | POST endpoint | `spec/requests/api/v1/reservations_spec.rb` | Tasks 5, 6 |
| 8 | Task 8 | GET list endpoint | `spec/requests/api/v1/users/reservations_spec.rb` | Tasks 4, 6 |
| 9 | Task 9 | PATCH cancel endpoint | `spec/requests/api/v1/cancel_reservation_spec.rb` | Task 7 |
| 10 | Task 10 | Expiration job | `spec/jobs/expire_reservations_job_spec.rb` | Task 4 |
| 11 | Task 11 | Integration specs | `spec/requests/api/v1/reservation_integration_spec.rb` | Tasks 7, 8, 9, 10 |

**Parallelizable:** Tasks 2, 3, and 6 can be done in parallel after Task 1. Tasks 8 and 10 can be done in parallel after Task 4 is complete.

**Total spec files:** 9. Total spec count estimate: ~45-50 examples covering happy paths, error cases, edge cases, concurrency safety, N+1 prevention, pagination, and full lifecycle integration.
