#!/usr/bin/env python3
"""M1 verifier - inheritance-to-composition refactor of LeveledLogger."""

import ast
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    code = extract_fenced(read_stdin(), lang="python")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"syntax error: {e}")

    # No class in the output may inherit from another class defined in the output.
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    class_names = {c.name for c in classes}
    if "LeveledLogger" not in class_names:
        fail(f"LeveledLogger class is missing; got classes: {sorted(class_names)}")
    for c in classes:
        for base in c.bases:
            base_id = _name_of(base)
            if base_id and base_id in class_names:
                fail(
                    f"class {c.name} inherits from {base_id} — "
                    "refactor must remove inheritance among the classes you define"
                )

    # No `super()` anywhere.
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "super"
        ):
            fail("`super()` is present — refactor must not use super()")

    # Behavioural check: write(msg) prints the expected formatted line.
    ns: dict = {}
    runner = getattr(__builtins__, "exec", None) or __builtins__["exec"]
    try:
        runner(code, ns)
    except Exception as e:
        fail(f"exec raised: {type(e).__name__}: {e}")

    LL = ns.get("LeveledLogger")
    if not isinstance(LL, type):
        fail("LeveledLogger is not a class after exec")

    cases = [
        (("app", lambda: "T1", "INFO"), "hi", "INFO [T1] [app] hi"),
        (("svc", lambda: "T9", "WARN"), "disk full", "WARN [T9] [svc] disk full"),
    ]
    for args, msg, expected in cases:
        buf = io.StringIO()
        try:
            inst = LL(*args)
            with redirect_stdout(buf):
                inst.write(msg)
        except Exception as e:
            fail(f"LeveledLogger{args!r}.write({msg!r}) raised {type(e).__name__}: {e}")
        out = buf.getvalue().rstrip("\n")
        if out != expected:
            fail(f"LeveledLogger{args!r}.write({msg!r}) printed {out!r}, expected {expected!r}")

    ok(f"{len(cases)} behavioural cases passed; no inheritance; no super()")


def _name_of(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


if __name__ == "__main__":
    main()
