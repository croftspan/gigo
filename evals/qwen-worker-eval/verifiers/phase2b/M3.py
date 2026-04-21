#!/usr/bin/env python3
"""Phase 2B M3 verifier - 2-stage:
  1. Phase 2A M3 acceptance check (all three bugs fixed, no state leak).
  2. Critique: `normalize`'s signature preserves the `defaults: list[...] = []`
     shape. The second parameter is named `defaults` and has a list-literal
     default (NOT `None`).
"""

import ast
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent.parent
PHASE2A = SCRIPT_DIR / "verifiers" / "phase2a" / "M3.py"

sys.path.insert(0, str(HERE.parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    content = read_stdin()

    proc = subprocess.run(
        ["python3", str(PHASE2A)],
        input=content,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = (proc.stdout + proc.stderr).strip() or "(no output)"
        fail(f"phase2a acceptance regressed: {msg[:400]}")

    code = extract_fenced(content, lang="python")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"stage-2: syntax error: {e}")

    normalize_fn = next(
        (n for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name == "normalize"),
        None,
    )
    if normalize_fn is None:
        fail("critique check: `normalize` function missing")

    arg_names = [a.arg for a in normalize_fn.args.args]
    if len(arg_names) < 2 or arg_names[1] != "defaults":
        fail(
            f"critique not addressed: normalize's second parameter must be "
            f"named `defaults` (got args: {arg_names})"
        )

    # The critique requires the signature to stay identical, which means the
    # default must be a list literal `[]`, not None or anything else.
    defaults = normalize_fn.args.defaults
    total_args = len(normalize_fn.args.args)
    if len(defaults) == 0 or (total_args - len(defaults)) > 1:
        fail(
            "critique not addressed: `defaults` parameter has no default value "
            "(original signature had `defaults: list[list[str]] = []`)"
        )
    # Find the default node for the `defaults` arg (index 1 counts from the end).
    default_for_defaults = defaults[-(total_args - 1)] if total_args >= 2 else None
    # Simpler: since defaults line up right-to-left with args, and `defaults`
    # is the 2nd arg out of 2, the default is defaults[0] when len(defaults)==1
    # or defaults[1] when both rows and defaults have defaults. Compute by
    # offset instead to be safe.
    offset = total_args - len(defaults)
    try:
        node = defaults[1 - offset]  # index of `defaults` arg is 1
    except IndexError:
        fail(
            "critique not addressed: couldn't locate the default value for "
            "the `defaults` parameter (indexing mismatch)"
        )

    # Accept either `[]` (List literal) or a call like `list()` that produces a
    # shared-empty-list default. Reject `None` or a name/constant of None.
    if isinstance(node, ast.Constant) and node.value is None:
        fail(
            "critique not addressed: `defaults` default was changed to `None` — "
            "signature is no longer `defaults: list[list[str]] = []`"
        )
    if isinstance(node, ast.Name) and node.id == "None":
        fail(
            "critique not addressed: `defaults` default was changed to `None` — "
            "signature is no longer `defaults: list[list[str]] = []`"
        )
    is_list_literal = isinstance(node, ast.List)
    is_list_call = (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "list"
    )
    if not (is_list_literal or is_list_call):
        fail(
            f"critique not addressed: `defaults` default is not a list literal "
            f"or `list()` call (got {ast.dump(node)})"
        )

    ok("phase2a acceptance held; normalize signature preserved (defaults=[] style)")


if __name__ == "__main__":
    main()
