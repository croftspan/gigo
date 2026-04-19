#!/usr/bin/env python3
"""T2 verifier - rename calc -> compute_total."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")
    if re.search(r"\bcalc\b", code):
        fail("the name `calc` is still present in the output")
    if "def compute_total(" not in code:
        fail("no `def compute_total(` found")
    if code.count("compute_total") < 4:
        fail(
            f"expected at least 4 occurrences of compute_total "
            f"(def + 3 call sites + recursive call), saw {code.count('compute_total')}"
        )
    try:
        compiled = compile(code, "<t2>", "exec")
    except SyntaxError as e:
        fail(f"syntax error: {e}")
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(compiled, ns)
    except SystemExit:
        pass
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")
    fn = ns.get("compute_total")
    if not callable(fn):
        fail("compute_total is not callable after exec")
    if fn([1, 2, 3]) != 6:
        fail(f"compute_total([1,2,3]) returned {fn([1,2,3])!r}, expected 6")
    if fn([]) != 0:
        fail("compute_total([]) did not return 0")
    ok("rename consistent, behaviour preserved")


if __name__ == "__main__":
    main()
