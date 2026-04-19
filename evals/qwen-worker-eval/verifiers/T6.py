#!/usr/bin/env python3
"""T6 verifier - type hints added, behaviour unchanged."""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    expected = {"greet", "summarize", "pick_even", "maybe_parse"}
    if set(funcs) != expected:
        fail(f"expected functions {expected}, got {set(funcs)}")

    for name, node in funcs.items():
        if node.returns is None:
            fail(f"{name} missing return annotation")
        for arg in node.args.args:
            if arg.annotation is None:
                fail(f"{name} parameter {arg.arg} missing annotation")

    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")

    if ns["greet"]("World") != "Hello, World!":
        fail(f'greet("World") wrong: {ns["greet"]("World")!r}')
    if ns["greet"]("Ada", ".") != "Hello, Ada.":
        fail("greet with explicit punctuation wrong")
    if ns["summarize"]([1, 2, 3]) != {"count": 3, "first": 1}:
        fail("summarize([1,2,3]) wrong")
    if ns["summarize"]([]) != {"count": 0, "first": None}:
        fail("summarize([]) wrong")
    if ns["pick_even"]([1, 2, 3, 4, 5]) != [2, 4]:
        fail("pick_even wrong")
    if ns["maybe_parse"]("42") != 42:
        fail('maybe_parse("42") wrong')
    if ns["maybe_parse"]("abc") is not None:
        fail('maybe_parse("abc") should return None')

    ok("annotations present on all params+returns, behaviour preserved")


if __name__ == "__main__":
    main()
