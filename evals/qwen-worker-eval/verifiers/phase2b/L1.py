#!/usr/bin/env python3
"""Phase 2B L1 verifier - 2-stage:
  1. Phase 2A L1 acceptance check (4-class composition, byte-exact output).
  2. Critique: private formatters moved out of `ReportFormatter` to
     module-level. The class body must contain no `_format_*` methods.
"""

import ast
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent.parent
PHASE2A = SCRIPT_DIR / "verifiers" / "phase2a" / "L1.py"

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

    formatter_cls = next(
        (n for n in ast.walk(tree)
         if isinstance(n, ast.ClassDef) and n.name == "ReportFormatter"),
        None,
    )
    if formatter_cls is None:
        fail("critique check: ReportFormatter class missing")

    # Critique-addressed: no `_format_*` methods inside ReportFormatter.
    private_format_methods = [
        m.name for m in formatter_cls.body
        if isinstance(m, ast.FunctionDef) and m.name.startswith("_format")
    ]
    if private_format_methods:
        fail(
            f"critique not addressed: ReportFormatter still has private "
            f"_format_* methods: {private_format_methods} — lift them to "
            f"module-level functions"
        )

    # Sanity: at least one module-level function exists (the lifted formatter).
    module_level_fns = [
        n.name for n in tree.body if isinstance(n, ast.FunctionDef)
    ]
    if not module_level_fns:
        fail(
            "critique not addressed: no module-level functions found — "
            "the lifted formatters should live at module scope"
        )

    ok(
        "phase2a acceptance held; ReportFormatter has no _format_* methods; "
        f"module-level fns: {module_level_fns}"
    )


if __name__ == "__main__":
    main()
