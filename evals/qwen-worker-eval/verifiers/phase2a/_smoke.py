#!/usr/bin/env python3
"""Smoke-test every Phase 2A verifier in both directions.

For each task, we supply a reference-correct output (expect exit 0) AND an
intentionally-broken output (expect exit 1). Any verifier that doesn't
discriminate both directions is a verifier bug — flag it here before the
45-run sweep.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

HERE = Path(__file__).parent


def run_verifier(name: str, content: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HERE / f"{name}.py")],
        input=content,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


# --------------------------- S1 ---------------------------

S1_OK = '''```python
def dedupe_preserve_order(items: list) -> list:
    """Dedupe preserving first-occurrence order; handle unhashables."""
    seen_h: set = set()
    seen_u: list = []
    out: list = []
    for x in items:
        try:
            if x in seen_h:
                continue
            seen_h.add(x)
        except TypeError:
            if x in seen_u:
                continue
            seen_u.append(x)
        out.append(x)
    return out
```'''

S1_BROKEN = '''```python
def dedupe_preserve_order(items: list) -> list:
    return list(set(items))  # loses order, breaks on unhashable
```'''

# --------------------------- M1 ---------------------------

M1_OK = '''```python
class NameFormatter:
    def __init__(self, name):
        self.name = name
    def format(self, msg):
        return f"[{self.name}] {msg}"


class TimestampFormatter:
    def __init__(self, clock):
        self.clock = clock
    def format(self, inner):
        return f"[{self.clock()}] {inner}"


class LevelFormatter:
    def __init__(self, level):
        self.level = level
    def format(self, inner):
        return f"{self.level} {inner}"


class LeveledLogger:
    def __init__(self, name, clock, level):
        self._name_fmt = NameFormatter(name)
        self._ts_fmt = TimestampFormatter(clock)
        self._level_fmt = LevelFormatter(level)
    def write(self, msg):
        named = self._name_fmt.format(msg)
        timestamped = self._ts_fmt.format(named)
        print(self._level_fmt.format(timestamped))
```'''

M1_BROKEN = '''```python
# Still uses inheritance — should fail.
class Base:
    def __init__(self, name):
        self.name = name
    def write(self, msg):
        print(f"[{self.name}] {msg}")


class LeveledLogger(Base):
    def __init__(self, name, clock, level):
        super().__init__(name)
        self.clock = clock
        self.level = level
    def write(self, msg):
        print(f"{self.level} [{self.clock()}] [{self.name}] {msg}")
```'''

# --------------------------- M2 ---------------------------

M2_OK = '''```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point(x={self.x!r}, y={self.y!r})"
    def __eq__(self, other):
        return type(other) is type(self) and self.x == other.x and self.y == other.y


class Rectangle:
    def __init__(self, width, height, label):
        self.width = width
        self.height = height
        self.label = label
    def __repr__(self):
        return f"Rectangle(width={self.width!r}, height={self.height!r}, label={self.label!r})"
    def __eq__(self, other):
        return (
            type(other) is type(self)
            and self.width == other.width
            and self.height == other.height
            and self.label == other.label
        )


class Circle:
    def __init__(self, radius):
        self.radius = radius
    def __repr__(self):
        return f"Circle(radius={self.radius!r})"
    def __eq__(self, other):
        return type(other) is type(self) and self.radius == other.radius


class Color:
    def __init__(self, r, g, b, alpha):
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha
    def __repr__(self):
        return f"Color(r={self.r!r}, g={self.g!r}, b={self.b!r}, alpha={self.alpha!r})"
    def __eq__(self, other):
        return (
            type(other) is type(self)
            and self.r == other.r and self.g == other.g
            and self.b == other.b and self.alpha == other.alpha
        )


class User:
    def __init__(self, username, email, active):
        self.username = username
        self.email = email
        self.active = active
    def __repr__(self):
        return f"User(username={self.username!r}, email={self.email!r}, active={self.active!r})"
    def __eq__(self, other):
        return (
            type(other) is type(self)
            and self.username == other.username
            and self.email == other.email
            and self.active == other.active
        )


class Employee:
    def __init__(self, name, department, salary, manager):
        self.name = name
        self.department = department
        self.salary = salary
        self.manager = manager
    def __repr__(self):
        return (
            f"Employee(name={self.name!r}, department={self.department!r}, "
            f"salary={self.salary!r}, manager={self.manager!r})"
        )
    def __eq__(self, other):
        return (
            type(other) is type(self)
            and self.name == other.name
            and self.department == other.department
            and self.salary == other.salary
            and self.manager == other.manager
        )
```'''

M2_BROKEN = '''```python
# __eq__ is missing on Point — verifier should fail.
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point(x={self.x!r}, y={self.y!r})"


class Rectangle:
    def __init__(self, width, height, label):
        self.width = width; self.height = height; self.label = label
    def __repr__(self): return f"Rectangle(width={self.width!r}, height={self.height!r}, label={self.label!r})"
    def __eq__(self, other): return type(other) is type(self) and self.__dict__ == other.__dict__


class Circle:
    def __init__(self, radius): self.radius = radius
    def __repr__(self): return f"Circle(radius={self.radius!r})"
    def __eq__(self, other): return type(other) is type(self) and self.__dict__ == other.__dict__


class Color:
    def __init__(self, r, g, b, alpha): self.r, self.g, self.b, self.alpha = r, g, b, alpha
    def __repr__(self): return f"Color(r={self.r!r}, g={self.g!r}, b={self.b!r}, alpha={self.alpha!r})"
    def __eq__(self, other): return type(other) is type(self) and self.__dict__ == other.__dict__


class User:
    def __init__(self, username, email, active): self.username, self.email, self.active = username, email, active
    def __repr__(self): return f"User(username={self.username!r}, email={self.email!r}, active={self.active!r})"
    def __eq__(self, other): return type(other) is type(self) and self.__dict__ == other.__dict__


class Employee:
    def __init__(self, name, department, salary, manager):
        self.name, self.department, self.salary, self.manager = name, department, salary, manager
    def __repr__(self):
        return f"Employee(name={self.name!r}, department={self.department!r}, salary={self.salary!r}, manager={self.manager!r})"
    def __eq__(self, other): return type(other) is type(self) and self.__dict__ == other.__dict__
```'''

# --------------------------- M3 ---------------------------

M3_OK = '''```python
from typing import Iterable, Optional


def parse_line(line):
    if line is None:
        return []
    return line.strip().split(",")


def normalize(rows, defaults=None):
    if defaults is None:
        defaults = []
    out = list(defaults)
    out.extend(rows)
    return out


def summarize(rows):
    total = 0
    for row in rows:
        total += int(row[1])
    return total


def pipeline(lines, initial_defaults):
    parsed = [parse_line(ln) for ln in lines]
    parsed = [row for row in parsed if row and row != [""]]
    normalized = normalize(parsed, initial_defaults)
    return summarize(normalized)
```'''

M3_BROKEN = '''```python
# Kept the mutable default and off-by-one.
from typing import Iterable, Optional

def parse_line(line):
    if line is None:
        return []
    return line.strip().split(",")

def normalize(rows, defaults=[]):
    defaults.extend(rows)
    return defaults

def summarize(rows):
    total = 0
    for i in range(len(rows) - 1):
        total += int(rows[i][1])
    return total

def pipeline(lines, initial_defaults):
    parsed = [parse_line(ln) for ln in lines]
    parsed = [row for row in parsed if row and row != [""]]
    normalized = normalize(parsed, initial_defaults)
    return summarize(normalized)
```'''

# --------------------------- L1 ---------------------------

L1_OK = '''```python
class ReportReader:
    def _normalise_row(self, row):
        return {
            "category": str(row.get("category", "unknown")).strip().lower(),
            "amount": float(row.get("amount", 0)),
            "count": int(row.get("count", 0)),
        }
    def read(self, payload):
        raw = payload.get("rows", []) or []
        return [self._normalise_row(r) for r in raw if isinstance(r, dict)]


class ReportComputer:
    def compute(self, rows):
        grouped = {}
        for r in rows:
            bucket = grouped.setdefault(r["category"], {"amount": 0.0, "count": 0})
            bucket["amount"] += r["amount"]
            bucket["count"] += r["count"]
        totals = {
            "amount": sum(r["amount"] for r in rows),
            "count": sum(r["count"] for r in rows),
        }
        if rows:
            means = {
                "amount": sum(r["amount"] for r in rows) / len(rows),
                "count": sum(r["count"] for r in rows) / len(rows),
            }
        else:
            means = {"amount": 0.0, "count": 0.0}
        return {"groups": grouped, "totals": totals, "means": means, "row_count": len(rows)}


class ReportFormatter:
    def render(self, stats, fmt):
        if fmt == "markdown":
            lines = ["# Report", ""]
            lines.append(f"Rows: {stats['row_count']}")
            lines.append(f"Total amount: {stats['totals']['amount']:.2f}")
            lines.append(f"Total count: {stats['totals']['count']}")
            lines.append("")
            lines.append("## By category")
            for cat in sorted(stats["groups"]):
                g = stats["groups"][cat]
                lines.append(f"- {cat}: amount={g['amount']:.2f} count={g['count']}")
            return "\\n".join(lines)
        if fmt == "html":
            rows = []
            rows.append("<h1>Report</h1>")
            rows.append(f"<p>Rows: {stats['row_count']}</p>")
            rows.append(f"<p>Total amount: {stats['totals']['amount']:.2f}</p>")
            rows.append(f"<p>Total count: {stats['totals']['count']}</p>")
            rows.append("<h2>By category</h2>")
            rows.append("<ul>")
            for cat in sorted(stats["groups"]):
                g = stats["groups"][cat]
                rows.append(f"<li>{cat}: amount={g['amount']:.2f} count={g['count']}</li>")
            rows.append("</ul>")
            return "\\n".join(rows)
        raise ValueError(f"unknown fmt: {fmt!r}")


class ReportGenerator:
    def __init__(self):
        self._reader = ReportReader()
        self._computer = ReportComputer()
        self._formatter = ReportFormatter()
    def generate(self, payload, fmt):
        rows = self._reader.read(payload)
        stats = self._computer.compute(rows)
        return self._formatter.render(stats, fmt)
```'''

L1_BROKEN = '''```python
# Facade exists but returns wrong markdown (missing totals).
class ReportReader:
    def read(self, payload):
        return payload.get("rows", [])


class ReportComputer:
    def compute(self, rows):
        return {"row_count": len(rows)}


class ReportFormatter:
    def render(self, stats, fmt):
        if fmt == "markdown":
            return f"Report: {stats['row_count']}"
        if fmt == "html":
            return f"<p>{stats['row_count']}</p>"
        raise ValueError(fmt)


class ReportGenerator:
    def __init__(self):
        self.r = ReportReader()
        self.c = ReportComputer()
        self.f = ReportFormatter()
    def generate(self, payload, fmt):
        return self.f.render(self.c.compute(self.r.read(payload)), fmt)
```'''

# --------------------------- L2 ---------------------------

L2_OK = '''```python
import json
import statistics
from collections import Counter
from collections.abc import Callable, Iterator


def read_ints(path: str) -> list[int]:
    with open(path) as f:
        return [int(line.strip()) for line in f if line.strip()]


def parse_config(raw: str) -> dict[str, int | float | str] | None:
    data = json.loads(raw)
    if not isinstance(data, dict):
        return None
    result: dict[str, int | float | str] = {}
    for k, v in data.items():
        if isinstance(v, (int, float, str)):
            result[str(k)] = v
    return result


def histogram(values: list[int], bucket_size: int = 1) -> dict[int, int]:
    buckets: Counter = Counter()
    for v in values:
        key = (v // bucket_size) * bucket_size
        buckets[key] += 1
    return dict(buckets)


def describe(values: list[int | float]) -> dict[str, int | float | None]:
    if not values:
        return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def pick(values: list[int], predicate: Callable[[int], bool]) -> list[int]:
    return [v for v in values if predicate(v)]


def batched(items: list[int], size: int) -> Iterator[list[int]]:
    buf: list[int] = []
    for item in items:
        buf.append(item)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf


def first_or_default(items: list[int], default: int | None = None) -> int | None:
    for item in items:
        return item
    return default


def merge_dicts(*dicts: dict, overwrite: bool = True) -> dict:
    out: dict = {}
    for d in dicts:
        for k, v in d.items():
            if overwrite or k not in out:
                out[k] = v
    return out
```'''

L2_BROKEN = '''```python
# read_ints missing annotations — verifier should fail.
import json
import statistics
from collections import Counter
from collections.abc import Callable, Iterator


def read_ints(path):
    with open(path) as f:
        return [int(line.strip()) for line in f if line.strip()]


def parse_config(raw: str) -> dict | None:
    data = json.loads(raw)
    if not isinstance(data, dict):
        return None
    return {str(k): v for k, v in data.items() if isinstance(v, (int, float, str))}


def histogram(values: list[int], bucket_size: int = 1) -> dict[int, int]:
    buckets: Counter = Counter()
    for v in values:
        key = (v // bucket_size) * bucket_size
        buckets[key] += 1
    return dict(buckets)


def describe(values: list[int | float]) -> dict[str, int | float | None]:
    if not values:
        return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
    return {
        "count": len(values), "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values), "max": max(values),
    }


def pick(values: list[int], predicate: Callable[[int], bool]) -> list[int]:
    return [v for v in values if predicate(v)]


def batched(items: list[int], size: int) -> Iterator[list[int]]:
    buf: list[int] = []
    for item in items:
        buf.append(item)
        if len(buf) == size:
            yield buf
            buf = []
    if buf:
        yield buf


def first_or_default(items: list[int], default: int | None = None) -> int | None:
    for item in items:
        return item
    return default


def merge_dicts(*dicts: dict, overwrite: bool = True) -> dict:
    out: dict = {}
    for d in dicts:
        for k, v in d.items():
            if overwrite or k not in out:
                out[k] = v
    return out
```'''

# --------------------------- L3 ---------------------------

L3_OK = '''```python
import json
import time
from typing import Any

import httpx

DEFAULT_TIMEOUT = 10.0


def fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    resp = httpx.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_text(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    resp = httpx.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def post_json(url, payload, headers=None, timeout=DEFAULT_TIMEOUT):
    resp = httpx.post(
        url,
        json=payload,
        headers=headers or {"Content-Type": "application/json"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


class ApiClient:
    def __init__(self, base_url, token, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = httpx.Client(headers={"Authorization": f"Bearer {token}"})

    def get(self, path):
        resp = self._session.get(f"{self.base_url}{path}", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def post(self, path, payload):
        resp = self._session.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self._session.close()


def retry_get(url, attempts=3, backoff=0.5, timeout=DEFAULT_TIMEOUT):
    last_err = None
    for i in range(attempts):
        try:
            resp = httpx.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_err = e
            time.sleep(backoff * (2 ** i))
    raise RuntimeError(f"all {attempts} attempts failed: {last_err}")
```'''

L3_BROKEN = '''```python
# Still imports requests — verifier should fail.
import requests

def fetch_json(url, timeout=10):
    return requests.get(url, timeout=timeout).json()

def fetch_text(url, timeout=10):
    return requests.get(url, timeout=timeout).text

def post_json(url, payload, headers=None, timeout=10):
    return requests.post(url, json=payload, headers=headers, timeout=timeout).json()


class ApiClient:
    def __init__(self, base_url, token, timeout=10):
        self.base_url = base_url
        self.timeout = timeout
        self._session = requests.Session()
    def get(self, path): return self._session.get(f"{self.base_url}{path}").json()
    def post(self, path, payload): return self._session.post(f"{self.base_url}{path}", json=payload).json()
    def close(self): self._session.close()


def retry_get(url, attempts=3, backoff=0.5, timeout=10):
    return requests.get(url, timeout=timeout).text
```'''

# --------------------------- XL1 ---------------------------

XL1_OK = '''### models.py

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Purchase:
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

### purchase_service.py

```python
from __future__ import annotations

from models import Purchase


_purchases: dict[str, Purchase] = {}


def create_purchase(purchase_id: str, customer_id: str) -> Purchase:
    if purchase_id in _purchases:
        raise ValueError(f"purchase already exists: {purchase_id}")
    purchase = Purchase(id=purchase_id, customer_id=customer_id)
    _purchases[purchase_id] = purchase
    return purchase


def get_purchase(purchase_id: str) -> Purchase:
    if purchase_id not in _purchases:
        raise KeyError(f"no purchase with id {purchase_id}")
    return _purchases[purchase_id]


def list_open_purchases() -> list[Purchase]:
    return [purchase for purchase in _purchases.values() if purchase.is_open()]


def ship_purchase(purchase_id: str, tracking_id: str) -> Purchase:
    purchase = get_purchase(purchase_id)
    if not purchase.is_open():
        raise ValueError(f"purchase {purchase_id} is not open (status={purchase.status})")
    purchase.mark_shipped(tracking_id)
    return purchase


def reset_purchases() -> None:
    _purchases.clear()
```

### test_purchase_service.py

```python
from __future__ import annotations

import pytest

from purchase_service import (
    create_purchase,
    get_purchase,
    list_open_purchases,
    reset_purchases,
    ship_purchase,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_purchases()
    yield
    reset_purchases()


def test_create_purchase_returns_pending_purchase():
    purchase = create_purchase("o1", "cust-1")
    assert purchase.id == "o1"
    assert purchase.status == "pending"


def test_duplicate_create_raises():
    create_purchase("o1", "cust-1")
    with pytest.raises(ValueError):
        create_purchase("o1", "cust-2")


def test_list_open_purchases():
    create_purchase("o1", "cust-1")
    create_purchase("o2", "cust-2")
    open_items = list_open_purchases()
    assert {o.id for o in open_items} == {"o1", "o2"}


def test_ship_purchase_marks_it_shipped():
    create_purchase("o1", "cust-1")
    shipped = ship_purchase("o1", tracking_id="T-123")
    assert shipped.status == "shipped"
    assert shipped.tracking_id == "T-123"
    with pytest.raises(ValueError):
        ship_purchase("o1", tracking_id="T-999")
```'''

XL1_BROKEN = '''### models.py

```python
from dataclasses import dataclass

@dataclass
class Order:
    id: str
```

### purchase_service.py

```python
from models import Order

def create_order(order_id):
    return Order(id=order_id)
```

### test_purchase_service.py

```python
from order_service import create_order

def test_it():
    assert create_order("o1").id == "o1"
```'''

# --------------------------- XL2 ---------------------------

XL2_OK = '''### model.py

```python
from __future__ import annotations

from datetime import datetime
from typing import Optional


class User:
    FIELDS = ("id", "email", "display_name", "created_at", "is_active", "deleted_at")

    def __init__(
        self,
        id: int,
        email: str,
        display_name: str,
        created_at: datetime,
        is_active: bool = True,
        deleted_at: Optional[datetime] = None,
    ) -> None:
        self.id = id
        self.email = email
        self.display_name = display_name
        self.created_at = created_at
        self.is_active = is_active
        self.deleted_at = deleted_at

    def deactivate(self) -> None:
        self.is_active = False

    def reactivate(self) -> None:
        self.is_active = True
```

### migration.py

```python
from __future__ import annotations


def up() -> str:
    return """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        deleted_at TIMESTAMP NULL DEFAULT NULL
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
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "created_at": user.created_at.isoformat(),
        "is_active": user.is_active,
        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
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


def test_user_default_deleted_at_is_none() -> None:
    user = make_user()
    assert user.deleted_at is None
    assert serialize_user(user)["deleted_at"] is None
```'''

XL2_BROKEN = '''### model.py

```python
class User:
    FIELDS = ("id", "email", "display_name", "created_at", "is_active")
    def __init__(self, id, email, display_name, created_at, is_active=True):
        self.id = id; self.email = email; self.display_name = display_name
        self.created_at = created_at; self.is_active = is_active
    def deactivate(self): self.is_active = False
    def reactivate(self): self.is_active = True
```

### migration.py

```python
def up(): return "CREATE TABLE users (id INTEGER);"
def down(): return "DROP TABLE users;"
```

### serializer.py

```python
from model import User
def serialize_user(u):
    return {"id": u.id, "email": u.email}
```

### test_user.py

```python
from model import User
from serializer import serialize_user
def test_it(): pass
```'''


CASES: list[tuple[str, str, str, str]] = [
    ("S1", S1_OK, S1_BROKEN, "dedupe_preserve_order"),
    ("M1", M1_OK, M1_BROKEN, "inheritance-to-composition"),
    ("M2", M2_OK, M2_BROKEN, "dataclass-dunders"),
    ("M3", M3_OK, M3_BROKEN, "pipeline-bugfixes"),
    ("L1", L1_OK, L1_BROKEN, "god-class-split"),
    ("L2", L2_OK, L2_BROKEN, "type-hints-strict"),
    ("L3", L3_OK, L3_BROKEN, "requests-to-httpx"),
    ("XL1", XL1_OK, XL1_BROKEN, "domain-rename"),
    ("XL2", XL2_OK, XL2_BROKEN, "nullable-field-add"),
]


def main() -> int:
    failures = 0
    for name, ok, broken, desc in CASES:
        rc_ok, out_ok = run_verifier(name, ok)
        rc_broken, out_broken = run_verifier(name, broken)
        ok_label = "PASS" if rc_ok == 0 else f"WRONG (rc={rc_ok})"
        broken_label = "REJECT" if rc_broken != 0 else f"WRONG (rc={rc_broken})"
        print(f"{name:<4} ({desc:<25}) ok->{ok_label:<20}  broken->{broken_label}")
        if rc_ok != 0:
            print(f"    ok output tail: {out_ok[-300:]}")
            failures += 1
        if rc_broken == 0:
            print(f"    broken output: {out_broken[-300:]}")
            failures += 1
    if failures:
        print(f"\n{failures} smoke failure(s)")
    else:
        print("\nAll 9 verifiers discriminate correct vs broken.")
    return failures


if __name__ == "__main__":
    sys.exit(main())
