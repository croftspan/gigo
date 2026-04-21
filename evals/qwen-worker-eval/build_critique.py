#!/usr/bin/env python3
"""Turn-2 critique renderer for the Qwen multi-turn eval.

Usage:
    build_critique.py <phase2b-task-id-or-path>

Emits the turn-2 user message to stdout. Pure function of the task file's
`revision_critique` field (Phase 2B) and `output_format` field (inherited
from the referenced Phase 2A task). Single template — no format variants at
turn 2, since the turn-1 format (TF1/TF2/TF3) already set the dispatch shape.
"""

from __future__ import annotations

import sys

from build_ticket import load_task, strip


TEMPLATE = """Review of your previous response:

{critique}

Please revise your solution to address the critique above. Keep everything else
unchanged — only fix what the critique calls out.

Output format is the same as before:
{output_format_reminder}"""


def build_critique(task_ref: str) -> str:
    task = load_task(task_ref)
    critique = task.get("revision_critique")
    if not critique:
        sys.exit(f"ERROR: task {task_ref!r} has no `revision_critique` field")
    output_format = task.get("output_format")
    if not output_format:
        sys.exit(f"ERROR: task {task_ref!r} has no `output_format` field (check reference_task)")
    return TEMPLATE.format(
        critique=strip(critique),
        output_format_reminder=strip(output_format),
    )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: build_critique.py <phase2b-task-id-or-path>")
    print(build_critique(sys.argv[1]))


if __name__ == "__main__":
    main()
