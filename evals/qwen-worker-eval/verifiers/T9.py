#!/usr/bin/env python3
"""T9 verifier — 3 bullet PR summary (format only)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract import extract_fenced, fail, ok, read_stdin


def main() -> None:
    raw = read_stdin()
    content = extract_fenced(raw).strip()
    lines = [ln for ln in content.splitlines() if ln.strip()]
    bullet_lines = [ln for ln in lines if ln.lstrip().startswith(("- ", "* "))]

    if len(lines) != len(bullet_lines):
        fail(f"non-bullet lines present: {len(lines)} total, {len(bullet_lines)} bullets")
    if len(bullet_lines) != 3:
        fail(f"expected exactly 3 bullets, got {len(bullet_lines)}")

    lowered = "\n".join(ln.lower() for ln in bullet_lines)
    if "cache" not in lowered and "write-through" not in lowered:
        fail("no bullet mentions cache/write-through (bullet 1 missing)")

    ok("3 bullets, bullet 1 references the change")


if __name__ == "__main__":
    main()
