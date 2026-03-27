Build a JSON API for a library book reservation system. Ruby on Rails. PostgreSQL.

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

**Deliver:** Complete working code — migrations, models, controller, routes, and request specs. Write all files now. Do not ask clarifying questions — the spec is complete. Make your own design decisions and build it.
