#!/usr/bin/env python3
"""T10 verifier — classify error log."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    body = extract_fenced(read_stdin(), lang="json")
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as e:
        fail(f"JSON parse error: {e}")
    if not isinstance(obj, dict):
        fail(f"expected JSON object, got {type(obj).__name__}")
    if set(obj.keys()) != {"severity", "category"}:
        fail(f"keys should be exactly severity,category — got {sorted(obj.keys())}")

    if obj["severity"] != "error":
        fail(f"severity should be 'error' (worker survives, job failed), got {obj['severity']!r}")

    cat = obj["category"]
    if not isinstance(cat, str):
        fail("category is not a string")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", cat):
        fail(f"category {cat!r} is not kebab-case")

    lowered = cat.lower()
    acceptable = ("timeout" in lowered and ("db" in lowered or "database" in lowered or "connection" in lowered)) \
        or lowered in {"connection-timeout", "network-timeout"}
    if not acceptable:
        fail(f"category {cat!r} does not describe a db/connection timeout")

    ok(f"severity=error, category={cat!r}")


if __name__ == "__main__":
    main()
