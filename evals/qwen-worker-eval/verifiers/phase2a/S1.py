#!/usr/bin/env python3
"""S1 verifier - parity with Phase 1 T1: dedupe_preserve_order."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")
    fn = ns.get("dedupe_preserve_order")
    if not callable(fn):
        fail("no callable dedupe_preserve_order in output")
    cases = [
        ([1, 2, 1, 3, 2, 4], [1, 2, 3, 4]),
        ([[1], [2], [1], [3]], [[1], [2], [3]]),
        ([], []),
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),
    ]
    for inp, expected in cases:
        try:
            got = fn(list(inp))
        except Exception as e:
            fail(f"{inp!r} raised {type(e).__name__}: {e}")
        if got != expected:
            fail(f"{inp!r} -> {got!r}, expected {expected!r}")
    ok(f"{len(cases)} cases passed")


if __name__ == "__main__":
    main()
