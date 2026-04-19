#!/usr/bin/env python3
"""M3 verifier - fix three marked bugs in a data pipeline."""

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

    for fn_name in ("parse_line", "normalize", "summarize", "pipeline"):
        if not callable(ns.get(fn_name)):
            fail(f"missing callable {fn_name}")

    parse_line = ns["parse_line"]
    normalize = ns["normalize"]
    pipeline = ns["pipeline"]

    # Fix 1: parse_line(None) returns []
    if parse_line(None) != []:
        fail(f"parse_line(None) = {parse_line(None)!r}, expected []")

    # parse_line normal case
    if parse_line(" a,b,c ") != ["a", "b", "c"]:
        fail(f"parse_line(' a,b,c ') = {parse_line(' a,b,c ')!r}, expected ['a','b','c']")

    # Fix 3: summarize off-by-one — pipeline must sum ALL rows
    result = pipeline(["a,1", None, "b,2", "c,3"], [])
    if result != 6:
        fail(f"pipeline(['a,1', None, 'b,2', 'c,3'], []) = {result}, expected 6")

    # Fix 2: mutable default — two independent calls must return 30 each
    r1 = pipeline(["x,10", "y,20"], [])
    r2 = pipeline(["x,10", "y,20"], [])
    if r1 != 30 or r2 != 30:
        fail(
            f"pipeline called twice with same args returned {r1} then {r2} — "
            "mutable-default state leaked between calls"
        )

    # Also confirm `normalize` isn't mutating a shared default. Call it twice
    # with no explicit defaults kwarg and check the results are independent.
    a = normalize([["k", "1"]])
    b = normalize([["k", "2"]])
    if a == [["k", "1"], ["k", "2"]] or b == [["k", "1"], ["k", "2"]]:
        fail("normalize() still shares state between calls via mutable default")

    ok("all three bugs fixed: None guard, mutable default, off-by-one")


if __name__ == "__main__":
    main()
