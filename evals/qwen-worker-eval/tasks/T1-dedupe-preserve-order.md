---
id: T1-dedupe-preserve-order
task_type: code
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
verifier: T1.py
---

Reference implementation (not shown to worker):

```python
def dedupe_preserve_order(items: list) -> list:
    seen_hashable = set()
    seen_unhashable = []
    out = []
    for x in items:
        try:
            if x in seen_hashable:
                continue
            seen_hashable.add(x)
        except TypeError:
            if x in seen_unhashable:
                continue
            seen_unhashable.append(x)
        out.append(x)
    return out
```
