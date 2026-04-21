#!/usr/bin/env python3
"""Phase 2B XL2 verifier - 2-stage:
  1. Phase 2A XL2 acceptance check (nullable deleted_at across 4 files).
  2. Critique: migration.py's `down()` body contains a column-specific drop
     (ALTER TABLE ... DROP COLUMN deleted_at), not just `DROP TABLE users;`.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent.parent
PHASE2A = SCRIPT_DIR / "verifiers" / "phase2a" / "XL2.py"

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

    files = extract_named_fences(content, ["migration.py"])
    mig_code = files.get("migration.py")
    if mig_code is None:
        fail("critique check: migration.py fence not found")

    try:
        mig_tree = ast.parse(mig_code)
    except SyntaxError as e:
        fail(f"stage-2: migration.py syntax error: {e}")

    down_fn = next(
        (n for n in ast.walk(mig_tree)
         if isinstance(n, ast.FunctionDef) and n.name == "down"),
        None,
    )
    if down_fn is None:
        fail("critique check: `down()` function missing from migration.py")

    # Extract down() body as source (from the function node).
    # Collect every string literal inside down()'s body.
    down_source_parts: list[str] = []
    for node in ast.walk(down_fn):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            down_source_parts.append(node.value)
    down_body = " ".join(down_source_parts)

    if not re.search(r"\bALTER\s+TABLE\b", down_body, re.IGNORECASE):
        fail(
            "critique not addressed: down() does not contain an ALTER TABLE "
            "statement (expected column-specific reversal, not DROP TABLE)"
        )
    if not re.search(r"\bDROP\s+COLUMN\b", down_body, re.IGNORECASE):
        fail(
            "critique not addressed: down() does not contain a DROP COLUMN "
            "statement"
        )
    if "deleted_at" not in down_body.lower():
        fail(
            "critique not addressed: down() does not mention `deleted_at` "
            "(the column being reversed)"
        )

    ok("phase2a acceptance held; down() performs ALTER TABLE DROP COLUMN deleted_at")


if __name__ == "__main__":
    main()
