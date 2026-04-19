---
id: S1-dedupe-preserve-order
task_type: code
size_bucket: S
spec_sentence: |
  Implement a Python function dedupe_preserve_order(items: list) -> list that removes duplicates while preserving first-occurrence order. Must handle unhashable items (lists, dicts) via O(n²) fallback. No external dependencies.
role: |
  You are implementing a single function in Python 3.12.
spec: |
  def dedupe_preserve_order(items: list) -> list
  - Remove duplicates from `items`
  - Preserve first-occurrence order
  - Handle unhashable items (e.g., lists, dicts) by falling back to O(n²) comparison
  - No external dependencies
acceptance: |
  - Single function, no class
  - Type hints on params and return
  - Docstring under 3 lines
  - Must pass: dedupe_preserve_order([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]
  - Must pass: dedupe_preserve_order([[1], [2], [1], [3]]) == [[1], [2], [3]]
  - Must pass: dedupe_preserve_order([]) == []
output_format: |
  - ONLY the function (with any helpers it needs) inside a single ```python fence
  - No preamble, no trailing prose, no module-level comments outside the function
mode_hint: |
  Use a single pass with a set for hashable items; fall back to linear scan for unhashables.
verifier: S1.py
---

Parity task — re-used verbatim from Phase 1 T1. If S1 does not hit 5/5 in the
Phase 2A sweep, we have a harness regression, not a scale finding.
