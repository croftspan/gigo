#!/usr/bin/env python3
"""L2 verifier - every function has full type annotations + behaviour preserved."""

import ast
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_fenced, fail, ok, read_stdin


EXPECTED_FUNCS = {
    "read_ints",
    "parse_config",
    "histogram",
    "describe",
    "pick",
    "batched",
    "first_or_default",
    "merge_dicts",
}


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")

    if "from typing import Optional" in code:
        fail("`from typing import Optional` is present — brief requires PEP 604 `| None` instead")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    missing = EXPECTED_FUNCS - set(funcs)
    if missing:
        fail(f"missing functions: {sorted(missing)}")

    for name in EXPECTED_FUNCS:
        node = funcs[name]
        if node.returns is None:
            fail(f"{name} missing return annotation")
        # Every positional/keyword-only arg must be annotated.
        arglist: list[ast.arg] = list(node.args.args) + list(node.args.kwonlyargs)
        for arg in arglist:
            if arg.annotation is None:
                fail(f"{name} parameter `{arg.arg}` missing annotation")
        if node.args.vararg is not None and node.args.vararg.annotation is None:
            fail(f"{name} parameter `*{node.args.vararg.arg}` missing annotation")
        if node.args.kwarg is not None and node.args.kwarg.annotation is None:
            fail(f"{name} parameter `**{node.args.kwarg.arg}` missing annotation")

    # Behaviour check: exec the module, run a few functions.
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")

    # read_ints — write a temp file and read it.
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("1\n2\n3\n\n")
        tmp_path = f.name
    try:
        got = ns["read_ints"](tmp_path)
        if got != [1, 2, 3]:
            fail(f"read_ints returned {got!r}, expected [1,2,3]")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if ns["parse_config"]('{"k": 1}') != {"k": 1}:
        fail("parse_config misbehaved")
    if ns["parse_config"]("null") is not None:
        fail("parse_config('null') should return None")

    if ns["histogram"]([1, 2, 3, 11, 12], 10) != {0: 3, 10: 2}:
        fail("histogram misbehaved")

    d = ns["describe"]([1, 2, 3, 4])
    if d["count"] != 4 or d["min"] != 1 or d["max"] != 4:
        fail(f"describe misbehaved: {d!r}")

    if ns["pick"]([1, 2, 3, 4], lambda x: x % 2 == 0) != [2, 4]:
        fail("pick misbehaved")

    if list(ns["batched"]([1, 2, 3, 4, 5], 2)) != [[1, 2], [3, 4], [5]]:
        fail("batched misbehaved")

    if ns["first_or_default"]([], 99) != 99:
        fail("first_or_default on empty should return default")
    if ns["first_or_default"]([7, 8]) != 7:
        fail("first_or_default on non-empty should return first")

    if ns["merge_dicts"]({"a": 1}, {"a": 2}, overwrite=True) != {"a": 2}:
        fail("merge_dicts overwrite=True misbehaved")
    if ns["merge_dicts"]({"a": 1}, {"a": 2}, overwrite=False) != {"a": 1}:
        fail("merge_dicts overwrite=False misbehaved")

    ok(f"all {len(EXPECTED_FUNCS)} functions typed; behaviour preserved")


if __name__ == "__main__":
    main()
