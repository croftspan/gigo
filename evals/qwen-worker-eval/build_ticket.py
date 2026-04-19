#!/usr/bin/env python3
"""Deterministic ticket builder for the Qwen worker eval.

Usage:
    build_ticket.py <TF1|TF2|TF3> <task-id-or-path>

Emits the rendered ticket text to stdout. Pure function of (format, task file) —
same input always produces the same output, so comparisons stay valid across
re-runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

TASKS_DIR = Path(__file__).parent / "tasks"


def load_task(task_ref: str) -> dict:
    if "/" in task_ref or task_ref.endswith(".md"):
        path = Path(task_ref)
    else:
        matches = list(TASKS_DIR.glob(f"{task_ref}-*.md"))
        if not matches:
            sys.exit(f"ERROR: no task file matching {task_ref!r} in {TASKS_DIR}")
        if len(matches) > 1:
            sys.exit(f"ERROR: ambiguous task ref {task_ref!r}: {[m.name for m in matches]}")
        path = matches[0]

    raw = path.read_text()
    if not raw.startswith("---"):
        sys.exit(f"ERROR: {path} has no YAML front-matter")
    end = raw.find("\n---", 3)
    if end == -1:
        sys.exit(f"ERROR: unterminated YAML front-matter in {path}")
    fm = yaml.safe_load(raw[3:end])
    if not isinstance(fm, dict):
        sys.exit(f"ERROR: front-matter in {path} is not a mapping")
    return fm


def strip(s: str) -> str:
    return s.strip()


def build_tf1(t: dict) -> str:
    """Bare: the spec block alone (task description + any embedded data/code).

    No role, no acceptance list, no output format, no mode hint. The contrast
    between TF1 and TF3 isolates the scaffolding (not the task content), which
    is what the brief actually asks — nine of ten tasks reference data that
    only lives in the spec block, so sending the one-line spec_sentence alone
    leaves the worker asking for inputs rather than doing the task.
    """
    return strip(t["spec"])


def build_tf2(t: dict) -> str:
    """Gigo canonical worker dispatch — derived from the Tier-1 subagent template
    in skills/execute/references/teammate-prompts.md, adapted for single-shot LLM
    use (no worktree/git/commit steps).
    """
    parts: list[str] = []
    parts.append("You are implementing a task.")
    parts.append("")
    parts.append("## Task Description")
    parts.append(strip(t["spec"]))
    parts.append("")
    parts.append("## Acceptance Criteria")
    parts.append(strip(t["acceptance"]))
    parts.append("")
    parts.append("## Output Format")
    parts.append(strip(t["output_format"]))
    parts.append("")
    parts.append("## Before You Begin")
    parts.append("If anything is unclear about requirements, approach, or dependencies — flag it.")
    parts.append("")
    parts.append("## Your Job")
    parts.append("1. Implement exactly what the task specifies")
    parts.append("2. Verify your output satisfies every acceptance criterion")
    parts.append("3. Self-review: completeness, quality, no overbuilding")
    parts.append("4. Return the result")
    parts.append("")
    parts.append("Status: DONE | DONE_WITH_CONCERNS | BLOCKED")
    parts.append("")
    parts.append("If you're in over your head, say so. Bad work is worse than no work.")
    return "\n".join(parts)


def build_tf3(t: dict) -> str:
    """Qwen-optimized: Role / SPEC / ACCEPTANCE / OUTPUT FORMAT / Mode hint."""
    parts: list[str] = []
    parts.append(strip(t["role"]))
    parts.append("")
    parts.append("SPEC")
    parts.append(_indent(strip(t["spec"]), "  "))
    parts.append("")
    parts.append("ACCEPTANCE")
    parts.append(_indent(strip(t["acceptance"]), "  "))
    parts.append("")
    parts.append("OUTPUT FORMAT")
    parts.append(_indent(strip(t["output_format"]), "  "))
    if t.get("mode_hint"):
        parts.append("")
        parts.append("MODE HINT")
        parts.append(_indent(strip(t["mode_hint"]), "  "))
    return "\n".join(parts)


def _indent(block: str, prefix: str) -> str:
    return "\n".join(prefix + ln if ln else ln for ln in block.splitlines())


BUILDERS = {"TF1": build_tf1, "TF2": build_tf2, "TF3": build_tf3}


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: build_ticket.py <TF1|TF2|TF3> <task-id-or-path>")
    fmt, task_ref = sys.argv[1], sys.argv[2]
    if fmt not in BUILDERS:
        sys.exit(f"ERROR: unknown format {fmt!r}; must be one of {list(BUILDERS)}")
    task = load_task(task_ref)
    print(BUILDERS[fmt](task))


if __name__ == "__main__":
    main()
