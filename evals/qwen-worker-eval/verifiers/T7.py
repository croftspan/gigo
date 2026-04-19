#!/usr/bin/env python3
"""T7 verifier - regex from examples."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin

POSITIVE = ["AB-1234", "XY-0001", "QQ-9999"]
NEGATIVE = ["ab-1234", "ABC-1234", "AB-123", "AB-12345", "AB1234", "AB-12A4", ""]


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")
    pat = ns.get("PATTERN")
    if not isinstance(pat, str):
        fail(f"PATTERN not a string, got {type(pat).__name__}")

    try:
        compiled = re.compile(pat)
    except re.error as e:
        fail(f"pattern does not compile: {e}")

    for s in POSITIVE:
        if not compiled.fullmatch(s):
            fail(f"pattern rejected positive example {s!r}")
    for s in NEGATIVE:
        if compiled.fullmatch(s):
            fail(f"pattern accepted negative example {s!r}")

    ok(f"pattern {pat!r} matches all positives, rejects all negatives")


if __name__ == "__main__":
    main()
