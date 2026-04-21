#!/usr/bin/env python3
"""Phase 2B L3 verifier - 2-stage:
  1. Phase 2A L3 acceptance check (requests → httpx sync port).
  2. Critique: `import json` removed (unused after the port).
"""

import ast
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent.parent
PHASE2A = SCRIPT_DIR / "verifiers" / "phase2a" / "L3.py"

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

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "json":
                    fail(
                        "critique not addressed: `import json` is still present; "
                        "httpx responses have a built-in .json() method"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module == "json":
                fail(
                    "critique not addressed: `from json import ...` is still present; "
                    "httpx responses have a built-in .json() method"
                )

    ok("phase2a acceptance held; no `import json` (or `from json import ...`) remains")


if __name__ == "__main__":
    main()
