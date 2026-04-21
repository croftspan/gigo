#!/usr/bin/env python3
"""Phase 2B XL1 verifier - 2-stage:
  1. Phase 2A XL1 acceptance check (symbol-level Order -> Purchase rename).
  2. Critique: test fixture string literals `"o1"`, `"o2"` renamed to
     `"p1"`, `"p2"` (or any `"o<N>"` → `"p<N>"`) in test_purchase_service.py.
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent.parent
PHASE2A = SCRIPT_DIR / "verifiers" / "phase2a" / "XL1.py"

sys.path.insert(0, str(HERE.parent))
from extract import extract_named_fences, fail, ok, read_stdin


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

    files = extract_named_fences(content, ["test_purchase_service.py"])
    test_code = files.get("test_purchase_service.py")
    if test_code is None:
        fail("critique check: test_purchase_service.py fence not found")

    stale = re.findall(r"""(['"])o\d+\1""", test_code)
    if stale:
        raw_hits = re.findall(r"""['"]o\d+['"]""", test_code)
        fail(
            f"critique not addressed: test file still contains o-prefixed "
            f"fixture ID string literals: {sorted(set(raw_hits))[:10]} "
            f"— rename to 'p1'/'p2'/etc."
        )

    if not re.search(r"""(['"])p\d+\1""", test_code):
        fail(
            "critique not addressed: no p-prefixed fixture ID literals found "
            "in test_purchase_service.py (expected 'p1', 'p2', etc.)"
        )

    ok("phase2a acceptance held; test fixture IDs renamed o* → p*")


if __name__ == "__main__":
    main()
