#!/usr/bin/env python3
"""T5 verifier — pytest tests for parse_iso_date."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")

    try:
        compile(code, "<t5>", "exec")
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    test_fn_count = len(re.findall(r"^def test_\w+\s*\(", code, re.MULTILINE))
    if test_fn_count < 2:
        fail(f"expected at least 2 test_* functions, saw {test_fn_count}")
    if "pytest.raises" not in code:
        fail("no pytest.raises used (error-case assertions are required)")
    if "import pytest" not in code and "from pytest" not in code:
        fail("no pytest import")
    if "parse_iso_date" not in code:
        fail("target function parse_iso_date not referenced")
    if "iso_date" not in code:
        fail("module name iso_date not referenced")
    if "ValueError" not in code:
        fail("ValueError not referenced in tests")

    ok(f"{test_fn_count} test_* fns, pytest.raises present, target referenced")


if __name__ == "__main__":
    main()
