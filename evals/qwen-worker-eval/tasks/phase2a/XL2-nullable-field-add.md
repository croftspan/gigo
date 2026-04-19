---
id: XL2-nullable-field-add
task_type: code
size_bucket: XL
spec_sentence: |
  Add a new nullable `deleted_at` timestamp field to the User domain across four files: model, migration, serializer, and test. Field defaults to None and must appear in all four files.
role: |
  You are adding a nullable `deleted_at` field to the User domain across four related files. The field must appear in the model, migration, serializer, and test — all four.
spec: |
  Add a nullable `deleted_at` field (type: `datetime | None`, default `None`) to
  the User domain. The field must be added to all four files below.

  Constraints:
  - Default value is `None` — the field is optional at construction time.
  - `deleted_at` must appear in: the model's field list, the migration's up/down SQL, the serializer's output dict, and an assertion in the test.
  - No behavioural change to any existing User — fresh Users default to `deleted_at=None`.
  - Keep every existing field, method, and test.
  - Do not rename anything.
  - Do not add new files. Output must be exactly four files — one per input file.

  The four files:

  ### model.py

  ```python
  from __future__ import annotations

  from datetime import datetime
  from typing import Optional


  class User:
      """A simple User value object.

      Stores its fields in `__dict__` so the Serializer can introspect them.
      """

      FIELDS = ("id", "email", "display_name", "created_at", "is_active")

      def __init__(
          self,
          id: int,
          email: str,
          display_name: str,
          created_at: datetime,
          is_active: bool = True,
      ) -> None:
          self.id = id
          self.email = email
          self.display_name = display_name
          self.created_at = created_at
          self.is_active = is_active

      def deactivate(self) -> None:
          self.is_active = False

      def reactivate(self) -> None:
          self.is_active = True
  ```

  ### migration.py

  ```python
  from __future__ import annotations

  # Migration: 0001_create_users_table
  #
  # Creates the `users` table with the fields currently known to model.User.


  def up() -> str:
      return """
      CREATE TABLE users (
          id INTEGER PRIMARY KEY,
          email TEXT NOT NULL UNIQUE,
          display_name TEXT NOT NULL,
          created_at TIMESTAMP NOT NULL,
          is_active BOOLEAN NOT NULL DEFAULT TRUE
      );
      """.strip()


  def down() -> str:
      return "DROP TABLE users;"
  ```

  ### serializer.py

  ```python
  from __future__ import annotations

  from typing import Any

  from model import User


  def serialize_user(user: User) -> dict[str, Any]:
      """Return a JSON-safe dict for the User."""
      return {
          "id": user.id,
          "email": user.email,
          "display_name": user.display_name,
          "created_at": user.created_at.isoformat(),
          "is_active": user.is_active,
      }


  def serialize_users(users: list[User]) -> list[dict[str, Any]]:
      return [serialize_user(u) for u in users]
  ```

  ### test_user.py

  ```python
  from __future__ import annotations

  from datetime import datetime

  from model import User
  from serializer import serialize_user


  def make_user() -> User:
      return User(
          id=1,
          email="a@example.com",
          display_name="Ada",
          created_at=datetime(2026, 1, 1, 12, 0, 0),
      )


  def test_user_defaults_are_active() -> None:
      user = make_user()
      assert user.is_active is True


  def test_serialize_user_includes_core_fields() -> None:
      user = make_user()
      out = serialize_user(user)
      assert out["id"] == 1
      assert out["email"] == "a@example.com"
      assert out["display_name"] == "Ada"
      assert out["is_active"] is True
      assert out["created_at"] == "2026-01-01T12:00:00"


  def test_deactivate_flips_is_active() -> None:
      user = make_user()
      user.deactivate()
      assert user.is_active is False
  ```

  The change:

  1. In `model.py`: add `deleted_at: datetime | None = None` to the constructor; store it on `self.deleted_at`; append `"deleted_at"` to the `FIELDS` tuple.
  2. In `migration.py`: add `deleted_at TIMESTAMP NULL DEFAULT NULL` (or `TIMESTAMP` without `NOT NULL`) to the CREATE TABLE body. The `down()` need not change (drop drops everything).
  3. In `serializer.py`: include `"deleted_at": user.deleted_at.isoformat() if user.deleted_at else None` in the output dict.
  4. In `test_user.py`: add a new test `test_user_default_deleted_at_is_none` that asserts `make_user().deleted_at is None` and that `serialize_user(make_user())["deleted_at"] is None`.
acceptance: |
  - Output contains FOUR `### filename` sections, one per file: `model.py`, `migration.py`, `serializer.py`, `test_user.py`
  - Each section is followed by a single ```python fence
  - `model.py` has `deleted_at` in the `__init__` signature with a default of `None` (via `= None` or `: datetime | None = None`); assigns it to `self.deleted_at`; includes `"deleted_at"` in the `FIELDS` tuple
  - `migration.py`'s `up()` SQL contains `deleted_at` (any TIMESTAMP-ish column type; NOT `NOT NULL`)
  - `serializer.py` returns a dict that contains the key `"deleted_at"`
  - `test_user.py` contains a test that asserts `make_user().deleted_at is None` (function name / style is your call)
  - All four existing tests in `test_user.py` are still present and still pass under the updated model
  - No file is missing
output_format: |
  Emit every file in a `### {filename}` heading followed by a single ```python fence, separated by a blank line.

  ```
  ### model.py
  ```python
  # ...file content...
  ```

  ### migration.py
  ```python
  # ...file content...
  ```

  ### serializer.py
  ```python
  # ...file content...
  ```

  ### test_user.py
  ```python
  # ...file content...
  ```
  ```

  No preamble before the first `### model.py` heading. No trailing prose after the last closing fence.
mode_hint: |
  Nullable everywhere. In Python that means `datetime | None = None`. In SQL that means the column has NO `NOT NULL` constraint. In the serializer, gracefully handle the None case.
verifier: XL2.py
---
