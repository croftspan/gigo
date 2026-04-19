---
id: XL1-domain-rename
task_type: code
size_bucket: XL
spec_sentence: |
  Rename the domain concept "Order" to "Purchase" across three files. Update every class, variable, attribute, import, and module reference. Do not change behaviour.
role: |
  You are performing a cross-file rename: `Order` → `Purchase` everywhere (class/type names, variable/attr names, imports). Preserve behaviour.
spec: |
  Three files use the `Order` / `order` concept. Rename every occurrence:

  - `Order` (any class or capitalised reference) → `Purchase`
  - `order` (any variable, attr, or lowercase reference) → `purchase`
  - `orders` (plural) → `purchases`
  - Module name `order_service` → `purchase_service`
  - Import lines must be updated to match the new module name (`from order_service import Order` → `from purchase_service import Purchase`)

  Constraints:
  - Behaviour must be preserved — the refactor is purely a rename.
  - Comments may contain the word "order" in natural English (e.g., "order of operations"); but ANY `order`/`Order` that is a symbolic reference in code must be renamed.
  - Imports must resolve internally: if `service.py` imports from `order_service`, after rename it imports from `purchase_service`.
  - All three files must be emitted in the output.

  The three files are given below. Each is clearly marked with a `### filename` heading.

  ### models.py

  ```python
  from __future__ import annotations

  from dataclasses import dataclass, field
  from typing import Optional


  @dataclass
  class Order:
      id: str
      customer_id: str
      items: list[str] = field(default_factory=list)
      total_cents: int = 0
      status: str = "pending"
      tracking_id: Optional[str] = None

      def is_open(self) -> bool:
          return self.status in ("pending", "processing")

      def add_item(self, sku: str, price_cents: int) -> None:
          self.items.append(sku)
          self.total_cents += price_cents

      def mark_shipped(self, tracking_id: str) -> None:
          self.status = "shipped"
          self.tracking_id = tracking_id
  ```

  ### order_service.py

  ```python
  from __future__ import annotations

  from models import Order


  _orders: dict[str, Order] = {}


  def create_order(order_id: str, customer_id: str) -> Order:
      if order_id in _orders:
          raise ValueError(f"order already exists: {order_id}")
      order = Order(id=order_id, customer_id=customer_id)
      _orders[order_id] = order
      return order


  def get_order(order_id: str) -> Order:
      if order_id not in _orders:
          raise KeyError(f"no order with id {order_id}")
      return _orders[order_id]


  def list_open_orders() -> list[Order]:
      return [order for order in _orders.values() if order.is_open()]


  def ship_order(order_id: str, tracking_id: str) -> Order:
      order = get_order(order_id)
      if not order.is_open():
          raise ValueError(f"order {order_id} is not open (status={order.status})")
      order.mark_shipped(tracking_id)
      return order


  def reset_orders() -> None:
      _orders.clear()
  ```

  ### test_order_service.py

  ```python
  from __future__ import annotations

  import pytest

  from order_service import (
      create_order,
      get_order,
      list_open_orders,
      reset_orders,
      ship_order,
  )


  @pytest.fixture(autouse=True)
  def _clean():
      reset_orders()
      yield
      reset_orders()


  def test_create_order_returns_pending_order():
      order = create_order("o1", "cust-1")
      assert order.id == "o1"
      assert order.status == "pending"


  def test_duplicate_create_raises():
      create_order("o1", "cust-1")
      with pytest.raises(ValueError):
          create_order("o1", "cust-2")


  def test_list_open_orders():
      create_order("o1", "cust-1")
      create_order("o2", "cust-2")
      open_orders = list_open_orders()
      assert {o.id for o in open_orders} == {"o1", "o2"}


  def test_ship_order_marks_it_shipped():
      create_order("o1", "cust-1")
      shipped = ship_order("o1", tracking_id="T-123")
      assert shipped.status == "shipped"
      assert shipped.tracking_id == "T-123"

      # Shipping again should fail because it's no longer open.
      with pytest.raises(ValueError):
          ship_order("o1", tracking_id="T-999")
  ```
acceptance: |
  - Output contains THREE `### filename` sections, one for each renamed file: `models.py`, `purchase_service.py`, `test_purchase_service.py`
  - Each section is followed by a single ```python fence with the full file contents
  - Zero occurrences of the symbol `Order` in any of the three files (bare word as a class / type reference)
  - Zero occurrences of `orders`, `order`, or `Order` as code identifiers in any file (inside fences) — they may appear inside string literals or comments only if semantically about "order of operations" etc.; any code-level variable/attribute/function name must be renamed
  - `models.py` defines `@dataclass class Purchase` with the same fields and methods as before
  - `purchase_service.py` exports `create_purchase`, `get_purchase`, `list_open_purchases`, `ship_purchase`, `reset_purchases`
  - `test_purchase_service.py` imports from `purchase_service` and references `Purchase` / `purchase` / `purchases` — NOT `order_service` / `Order`
  - Behaviour of the refactored code is unchanged (an instance of `Purchase` has the same fields, methods, and semantics as the old `Order`)
output_format: |
  Emit every file in a `### {filename}` heading followed by a single ```python fence, separated by a blank line.

  Example shape (for illustration — filenames must match the renamed ones):

  ```
  ### models.py
  ```python
  # ...file content...
  ```

  ### purchase_service.py
  ```python
  # ...file content...
  ```

  ### test_purchase_service.py
  ```python
  # ...file content...
  ```
  ```

  No preamble before the first `### models.py` heading. No trailing prose after the last closing fence.
mode_hint: |
  This is a pure rename. Do NOT reformat, add comments, or "improve" any code. Do not change imports' paths except to swap `order_service` → `purchase_service`.
verifier: XL1.py
---
