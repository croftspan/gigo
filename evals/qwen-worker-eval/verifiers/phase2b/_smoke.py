#!/usr/bin/env python3
"""Smoke-test every Phase 2B verifier in three directions per task.

For each of M1/M3/L1/L3/XL1/XL2 we supply:
  - REVISED: turn-2 content that resolves the critique AND preserves phase2a
    acceptance → verifier must exit 0.
  - ACCEPTANCE_REGRESSED: turn-2 content that broke the original acceptance
    check → verifier must exit 1 (phase2a stage fails).
  - CRITIQUE_NOT_ADDRESSED: turn-2 content that still passes phase2a acceptance
    but didn't address the critique → verifier must exit 1 (stage-2 fails).

A verifier that doesn't discriminate all three directions is a verifier bug.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).parent


def run_verifier(name: str, content: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HERE / f"{name}.py")],
        input=content,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


# --------------------------- M1 ---------------------------

M1_REVISED = '''```python
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

M1_ACCEPTANCE_REGRESSED = '''```python
# Still uses inheritance — phase2a M1 acceptance fails.
class Base:
    def __init__(self, name):
        self.name = name


class LeveledLogger(Base):
    def __init__(self, name, clock, level):
        super().__init__(name)
        self.clock = clock
        self.level = level
    def write(self, msg):
        print(f"{self.level} [{self.clock()}] [{self.name}] {msg}")
```'''

M1_CRITIQUE_NOT_ADDRESSED = '''```python
class NameFormatter:
    def __init__(self, name):
        self.name = name
    def format(self, msg):
        return f"[{self.name}] {msg}"


class TimestampDecorator:  # still named like a decorator — critique unaddressed
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
        self._ts_fmt = TimestampDecorator(clock)
        self._level_fmt = LevelFormatter(level)
    def write(self, msg):
        named = self._name_fmt.format(msg)
        timestamped = self._ts_fmt.format(named)
        print(self._level_fmt.format(timestamped))
```'''


# --------------------------- M3 ---------------------------

M3_REVISED = '''```python
from typing import Iterable, Optional


def parse_line(line: Optional[str]) -> list[str]:
    if line is None:
        return []
    return line.strip().split(",")


def normalize(rows: list[list[str]], defaults: list[list[str]] = []) -> list[list[str]]:
    """Prepend `defaults` to `rows` and return the combined list."""
    result = list(defaults)
    result.extend(rows)
    return result


def summarize(rows: list[list[str]]) -> int:
    total = 0
    for i in range(len(rows)):
        total += int(rows[i][1])
    return total


def pipeline(lines: Iterable[Optional[str]], initial_defaults: list[list[str]]) -> int:
    parsed = [parse_line(ln) for ln in lines]
    parsed = [row for row in parsed if row and row != [""]]
    normalized = normalize(parsed, initial_defaults)
    return summarize(normalized)
```'''

M3_ACCEPTANCE_REGRESSED = '''```python
from typing import Iterable, Optional


def parse_line(line: Optional[str]) -> list[str]:
    return line.strip().split(",")  # still crashes on None


def normalize(rows: list[list[str]], defaults: list[list[str]] = []) -> list[list[str]]:
    defaults.extend(rows)  # still leaks state
    return defaults


def summarize(rows: list[list[str]]) -> int:
    total = 0
    for i in range(len(rows) - 1):  # still off-by-one
        total += int(rows[i][1])
    return total


def pipeline(lines, initial_defaults):
    parsed = [parse_line(ln) for ln in lines]
    parsed = [row for row in parsed if row and row != [""]]
    normalized = normalize(parsed, initial_defaults)
    return summarize(normalized)
```'''

M3_CRITIQUE_NOT_ADDRESSED = '''```python
from typing import Iterable, Optional


def parse_line(line: Optional[str]) -> list[str]:
    if line is None:
        return []
    return line.strip().split(",")


def normalize(rows: list[list[str]], defaults: list[list[str]] | None = None) -> list[list[str]]:
    """Prepend `defaults` to `rows` and return the combined list."""
    if defaults is None:
        defaults = []
    result = list(defaults)
    result.extend(rows)
    return result


def summarize(rows: list[list[str]]) -> int:
    total = 0
    for i in range(len(rows)):
        total += int(rows[i][1])
    return total


def pipeline(lines: Iterable[Optional[str]], initial_defaults: list[list[str]]) -> int:
    parsed = [parse_line(ln) for ln in lines]
    parsed = [row for row in parsed if row and row != [""]]
    normalized = normalize(parsed, initial_defaults)
    return summarize(normalized)
```'''


# --------------------------- L1 ---------------------------

L1_REVISED = '''```python
def _normalise_row(row):
    return {
        "category": str(row.get("category", "unknown")).strip().lower(),
        "amount": float(row.get("amount", 0)),
        "count": int(row.get("count", 0)),
    }


def _group_by_category(rows):
    grouped = {}
    for row in rows:
        cat = row["category"]
        bucket = grouped.setdefault(cat, {"amount": 0.0, "count": 0})
        bucket["amount"] += row["amount"]
        bucket["count"] += row["count"]
    return grouped


def _compute_totals(rows):
    return {
        "amount": sum(r["amount"] for r in rows),
        "count": sum(r["count"] for r in rows),
    }


def _compute_means(rows):
    if not rows:
        return {"amount": 0.0, "count": 0.0}
    n = len(rows)
    return {
        "amount": sum(r["amount"] for r in rows) / n,
        "count": sum(r["count"] for r in rows) / n,
    }


def format_report_markdown(stats):
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


def format_report_html(stats):
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


class ReportReader:
    def read(self, payload):
        raw = payload.get("rows", []) or []
        return [_normalise_row(r) for r in raw if isinstance(r, dict)]


class ReportComputer:
    def compute(self, rows):
        return {
            "groups": _group_by_category(rows),
            "totals": _compute_totals(rows),
            "means": _compute_means(rows),
            "row_count": len(rows),
        }


class ReportFormatter:
    def render(self, stats, fmt):
        if fmt == "markdown":
            return format_report_markdown(stats)
        if fmt == "html":
            return format_report_html(stats)
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

L1_ACCEPTANCE_REGRESSED = '''```python
# Only one class — doesn't satisfy the 4-class phase2a requirement.
class ReportGenerator:
    def __init__(self):
        pass
    def generate(self, payload, fmt):
        return "broken"
```'''

L1_CRITIQUE_NOT_ADDRESSED = '''```python
class ReportReader:
    def read(self, payload):
        raw = payload.get("rows", []) or []
        return [
            {
                "category": str(r.get("category", "unknown")).strip().lower(),
                "amount": float(r.get("amount", 0)),
                "count": int(r.get("count", 0)),
            }
            for r in raw if isinstance(r, dict)
        ]


class ReportComputer:
    def compute(self, rows):
        groups = {}
        for row in rows:
            cat = row["category"]
            bucket = groups.setdefault(cat, {"amount": 0.0, "count": 0})
            bucket["amount"] += row["amount"]
            bucket["count"] += row["count"]
        totals = {"amount": sum(r["amount"] for r in rows), "count": sum(r["count"] for r in rows)}
        means = {"amount": 0.0, "count": 0.0}
        if rows:
            n = len(rows)
            means = {
                "amount": sum(r["amount"] for r in rows) / n,
                "count": sum(r["count"] for r in rows) / n,
            }
        return {"groups": groups, "totals": totals, "means": means, "row_count": len(rows)}


class ReportFormatter:
    # _format_* helpers still live on the class — critique unaddressed.
    def _format_markdown(self, stats):
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

    def _format_html(self, stats):
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

    def render(self, stats, fmt):
        if fmt == "markdown":
            return self._format_markdown(stats)
        if fmt == "html":
            return self._format_html(stats)
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


# --------------------------- L3 ---------------------------

# Minimal httpx-ported fixture that passes phase2a L3 acceptance.
L3_BASE = '''```python
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


def post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    resp = httpx.post(url, json=payload, headers=headers or {"Content-Type": "application/json"}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


class ApiClient:
    def __init__(self, base_url: str, token: str, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = httpx.Client(headers={"Authorization": f"Bearer {token}"})

    def get(self, path: str) -> dict[str, Any]:
        resp = self._session.get(f"{self.base_url}{path}", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._session.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._session.close()


def retry_get(url: str, attempts: int = 3, backoff: float = 0.5, timeout: float = DEFAULT_TIMEOUT) -> str:
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

L3_REVISED = L3_BASE  # no `import json`

L3_ACCEPTANCE_REGRESSED = '''```python
import requests  # phase2a L3 fails if requests is still imported

def fetch_json(url, timeout=10):
    return requests.get(url, timeout=timeout).json()
```'''

L3_CRITIQUE_NOT_ADDRESSED = L3_BASE.replace(
    "import time\n",
    "import json\nimport time\n",
)


# --------------------------- XL1 ---------------------------

_XL1_MODELS = '''### models.py
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
```'''

_XL1_SERVICE = '''### purchase_service.py
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
    return [p for p in _purchases.values() if p.is_open()]


def ship_purchase(purchase_id: str, tracking_id: str) -> Purchase:
    purchase = get_purchase(purchase_id)
    if not purchase.is_open():
        raise ValueError(f"purchase {purchase_id} is not open (status={purchase.status})")
    purchase.mark_shipped(tracking_id)
    return purchase


def reset_purchases() -> None:
    _purchases.clear()
```'''

_XL1_TEST_P = '''### test_purchase_service.py
```python
from __future__ import annotations
import pytest
from purchase_service import (
    create_purchase, get_purchase, list_open_purchases, reset_purchases, ship_purchase,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_purchases()
    yield
    reset_purchases()


def test_create_purchase_returns_pending():
    p = create_purchase("p1", "cust-1")
    assert p.id == "p1"
    assert p.status == "pending"


def test_duplicate_create_raises():
    create_purchase("p1", "cust-1")
    with pytest.raises(ValueError):
        create_purchase("p1", "cust-2")


def test_list_open_purchases():
    create_purchase("p1", "cust-1")
    create_purchase("p2", "cust-2")
    open_ps = list_open_purchases()
    assert {p.id for p in open_ps} == {"p1", "p2"}


def test_ship_purchase_marks_it_shipped():
    create_purchase("p1", "cust-1")
    shipped = ship_purchase("p1", tracking_id="T-123")
    assert shipped.status == "shipped"
    assert shipped.tracking_id == "T-123"
    with pytest.raises(ValueError):
        ship_purchase("p1", tracking_id="T-999")
```'''

_XL1_TEST_O = '''### test_purchase_service.py
```python
from __future__ import annotations
import pytest
from purchase_service import (
    create_purchase, get_purchase, list_open_purchases, reset_purchases, ship_purchase,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_purchases()
    yield
    reset_purchases()


def test_create_purchase_returns_pending():
    p = create_purchase("o1", "cust-1")  # fixture ID still o-prefixed
    assert p.id == "o1"
    assert p.status == "pending"


def test_duplicate_create_raises():
    create_purchase("o1", "cust-1")
    with pytest.raises(ValueError):
        create_purchase("o1", "cust-2")


def test_list_open_purchases():
    create_purchase("o1", "cust-1")
    create_purchase("o2", "cust-2")
    open_ps = list_open_purchases()
    assert {p.id for p in open_ps} == {"o1", "o2"}


def test_ship_purchase_marks_it_shipped():
    create_purchase("o1", "cust-1")
    shipped = ship_purchase("o1", tracking_id="T-123")
    assert shipped.status == "shipped"
    assert shipped.tracking_id == "T-123"
    with pytest.raises(ValueError):
        ship_purchase("o1", tracking_id="T-999")
```'''

XL1_REVISED = "\n\n".join([_XL1_MODELS, _XL1_SERVICE, _XL1_TEST_P])

XL1_ACCEPTANCE_REGRESSED = '''### models.py
```python
# Still uses Order — phase2a acceptance fails.
from dataclasses import dataclass


@dataclass
class Order:
    id: str
```

### purchase_service.py
```python
from models import Order
```

### test_purchase_service.py
```python
from purchase_service import Order
```'''

XL1_CRITIQUE_NOT_ADDRESSED = "\n\n".join([_XL1_MODELS, _XL1_SERVICE, _XL1_TEST_O])


# --------------------------- XL2 ---------------------------

_XL2_MODEL = '''### model.py
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
        deleted_at: datetime | None = None,
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
```'''

_XL2_SERIALIZER = '''### serializer.py
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
```'''

_XL2_TEST = '''### test_user.py
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
    assert make_user().is_active is True


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
    assert make_user().deleted_at is None
    assert serialize_user(make_user())["deleted_at"] is None
```'''

_XL2_MIGRATION_REVISED = '''### migration.py
```python
from __future__ import annotations


def up() -> str:
    return """
    ALTER TABLE users
    ADD COLUMN deleted_at TIMESTAMP NULL DEFAULT NULL;
    """.strip()


def down() -> str:
    return """
    ALTER TABLE users DROP COLUMN deleted_at;
    """.strip()
```'''

_XL2_MIGRATION_DROP_TABLE = '''### migration.py
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
        deleted_at TIMESTAMP NULL
    );
    """.strip()


def down() -> str:
    return "DROP TABLE users;"  # critique unaddressed — still drops the whole table
```'''

XL2_REVISED = "\n\n".join([_XL2_MODEL, _XL2_MIGRATION_REVISED, _XL2_SERIALIZER, _XL2_TEST])

XL2_ACCEPTANCE_REGRESSED = '''### model.py
```python
class User:
    FIELDS = ("id",)
    def __init__(self, id):
        self.id = id
```

### migration.py
```python
def up(): return "CREATE TABLE users (id INTEGER);"
def down(): return "DROP TABLE users;"
```

### serializer.py
```python
from model import User
def serialize_user(u): return {"id": u.id}
```

### test_user.py
```python
from model import User
def test_x(): assert User(1).id == 1
```'''

XL2_CRITIQUE_NOT_ADDRESSED = "\n\n".join([_XL2_MODEL, _XL2_MIGRATION_DROP_TABLE, _XL2_SERIALIZER, _XL2_TEST])


# --------------------------- dispatcher ---------------------------

TASKS: dict[str, dict[str, str]] = {
    "M1": {"revised": M1_REVISED, "acc_regressed": M1_ACCEPTANCE_REGRESSED, "crit_unaddr": M1_CRITIQUE_NOT_ADDRESSED},
    "M3": {"revised": M3_REVISED, "acc_regressed": M3_ACCEPTANCE_REGRESSED, "crit_unaddr": M3_CRITIQUE_NOT_ADDRESSED},
    "L1": {"revised": L1_REVISED, "acc_regressed": L1_ACCEPTANCE_REGRESSED, "crit_unaddr": L1_CRITIQUE_NOT_ADDRESSED},
    "L3": {"revised": L3_REVISED, "acc_regressed": L3_ACCEPTANCE_REGRESSED, "crit_unaddr": L3_CRITIQUE_NOT_ADDRESSED},
    "XL1": {"revised": XL1_REVISED, "acc_regressed": XL1_ACCEPTANCE_REGRESSED, "crit_unaddr": XL1_CRITIQUE_NOT_ADDRESSED},
    "XL2": {"revised": XL2_REVISED, "acc_regressed": XL2_ACCEPTANCE_REGRESSED, "crit_unaddr": XL2_CRITIQUE_NOT_ADDRESSED},
}


def main() -> None:
    failures: list[str] = []
    results: list[tuple[str, str, int, str]] = []

    for task_id, fixtures in TASKS.items():
        for label, content in fixtures.items():
            rc, out = run_verifier(task_id, content)
            expected_pass = (label == "revised")
            got_pass = (rc == 0)
            status = "OK" if got_pass == expected_pass else "MISMATCH"
            results.append((task_id, label, rc, status))
            if status == "MISMATCH":
                failures.append(
                    f"  {task_id} [{label}]: expected {'exit 0' if expected_pass else 'exit != 0'}, "
                    f"got rc={rc}; output:\n{textwrap.indent(out[:600], '    ')}"
                )

    print("=== Phase 2B smoke results ===")
    for task_id, label, rc, status in results:
        print(f"{status:9}  {task_id:4}  {label:14}  rc={rc}")

    if failures:
        print()
        print("=== FAILURES ===")
        for f in failures:
            print(f)
        sys.exit(1)
    else:
        print()
        print("All Phase 2B verifiers discriminate correctly in 3 directions.")


if __name__ == "__main__":
    main()
