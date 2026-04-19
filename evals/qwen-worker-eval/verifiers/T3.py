#!/usr/bin/env python3
"""T3 verifier - fizzbuzz branch ordering fix."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")
    fn = ns.get("fizzbuzz")
    if not callable(fn):
        fail("no callable fizzbuzz in output")
    cases = [
        (1, "1"),
        (2, "2"),
        (3, "Fizz"),
        (5, "Buzz"),
        (9, "Fizz"),
        (10, "Buzz"),
        (15, "FizzBuzz"),
        (30, "FizzBuzz"),
        (45, "FizzBuzz"),
    ]
    for n, expected in cases:
        got = fn(n)
        if got != expected:
            fail(f"fizzbuzz({n}) -> {got!r}, expected {expected!r}")
    ok(f"{len(cases)} cases passed")


if __name__ == "__main__":
    main()
