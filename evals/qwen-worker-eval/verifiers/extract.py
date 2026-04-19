"""Shared helpers for extracting fenced blocks from worker outputs."""

from __future__ import annotations

import re
import sys


def read_stdin() -> str:
    return sys.stdin.read()


def extract_fenced(content: str, lang: str | None = None) -> str:
    """Return the body of the first fenced block; if no fence, return content stripped.

    If `lang` is given, prefer a fence with that language tag but fall back to
    the first fence of any type.
    """
    if lang:
        m = re.search(rf"```{re.escape(lang)}\s*\n(.*?)\n```", content, re.DOTALL)
        if m:
            return m.group(1).rstrip()
    m = re.search(r"```[a-zA-Z0-9_-]*\s*\n(.*?)\n```", content, re.DOTALL)
    if m:
        return m.group(1).rstrip()
    return content.strip()


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str = "") -> None:
    if msg:
        print(f"PASS: {msg}")
    sys.exit(0)
