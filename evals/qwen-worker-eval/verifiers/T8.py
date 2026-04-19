#!/usr/bin/env python3
"""T8 verifier — SELECT column extraction."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin

EXPECTED = ["id", "user_email", "order_count", "total_spent", "created_at"]


def main() -> None:
    body = extract_fenced(read_stdin(), lang="json")
    try:
        got = json.loads(body)
    except json.JSONDecodeError as e:
        fail(f"JSON parse error: {e}")
    if not isinstance(got, list):
        fail(f"expected JSON array, got {type(got).__name__}")
    if got != EXPECTED:
        fail(f"got {got!r}, expected {EXPECTED!r}")
    ok(f"exact match on {len(EXPECTED)} columns")


if __name__ == "__main__":
    main()
