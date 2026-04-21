#!/usr/bin/env python3
"""Phase 2B M1 verifier - 2-stage:
  1. Phase 2A M1 acceptance check (inheritance-to-composition semantics still hold).
  2. Critique: no class in the output has "Decorator" in its name.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent.parent  # evals/qwen-worker-eval/
PHASE2A = SCRIPT_DIR / "verifiers" / "phase2a" / "M1.py"

sys.path.insert(0, str(HERE.parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    content = read_stdin()

    # Stage 1: Phase 2A acceptance check.
    proc = subprocess.run(
        ["python3", str(PHASE2A)],
        input=content,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = (proc.stdout + proc.stderr).strip() or "(no output)"
        fail(f"phase2a acceptance regressed: {msg[:400]}")

    # Stage 2: critique — no class named *Decorator*.
    code = extract_fenced(content, lang="python")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        fail(f"stage-2: syntax error: {e}")

    decorator_named = [
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and re.search(r"Decorator\b", n.name)
    ]
    if decorator_named:
        fail(
            f"critique not addressed: class name(s) still contain 'Decorator': "
            f"{decorator_named}"
        )

    ok("phase2a acceptance held; no *Decorator class names remain")


if __name__ == "__main__":
    main()
