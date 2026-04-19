---
id: M3-pipeline-bugfixes
task_type: code
size_bucket: M
spec_sentence: |
  Fix all three bugs marked with `# BUG:` comments in the data pipeline below. Return the entire corrected module.
role: |
  You are fixing bugs in a small data pipeline. Three defects are marked with `# BUG:` comments — fix every one.
spec: |
  The module below has three bugs, each flagged with a `# BUG:` comment.
  Fix every bug while keeping the overall structure intact.

  ```python
  # data_pipeline.py
  from typing import Iterable, Optional


  def parse_line(line: Optional[str]) -> list[str]:
      # BUG: crashes when `line` is None — must return an empty list for None.
      return line.strip().split(",")


  def normalize(rows: list[list[str]], defaults: list[list[str]] = []) -> list[list[str]]:
      """Prepend `defaults` to `rows` and return the combined list."""
      # BUG: mutable default argument — calls accumulate state across invocations.
      defaults.extend(rows)
      return defaults


  def summarize(rows: list[list[str]]) -> int:
      """Sum the integer values in column 1 (zero-indexed) across every row."""
      total = 0
      # BUG: off-by-one — the last row is never summed.
      for i in range(len(rows) - 1):
          total += int(rows[i][1])
      return total


  def pipeline(lines: Iterable[Optional[str]], initial_defaults: list[list[str]]) -> int:
      parsed = [parse_line(ln) for ln in lines]
      parsed = [row for row in parsed if row and row != [""]]
      normalized = normalize(parsed, initial_defaults)
      return summarize(normalized)
  ```

  The function signatures and module-level imports must stay exactly the same.
  The pipeline's job, after all fixes:
  - `parse_line(None)` returns `[]`
  - `normalize` must not leak state between calls — each call returns a fresh list
  - `summarize` sums column-1 ints across **every** row, not `len(rows) - 1`
  - `pipeline(["a,1", None, "b,2", "c,3"], [])` returns `6`
  - Calling `pipeline(...)` a second time with a different initial_defaults must not be polluted by the first call
acceptance: |
  - All three `# BUG:` comments are resolved; their related defect is fixed (you may keep or drop the comments)
  - Function signatures unchanged
  - No new imports
  - `pipeline(["a,1", None, "b,2", "c,3"], [])` returns `6`
  - Calling `pipeline(["x,10", "y,20"], [])` twice in succession returns `30` both times (no state leakage via mutable default)
  - `parse_line(None)` returns `[]`
  - `parse_line(" a,b,c ")` returns `["a", "b", "c"]`
output_format: |
  - ONLY the corrected module inside a single ```python fence
  - No preamble, no trailing prose
  - The three BUG comments may be left in or removed — up to you
mode_hint: |
  Classic Python pitfalls: the mutable-default-argument fix, None guard, and fencepost on `range(len(x))`. Each is a 1- to 3-line edit.
verifier: M3.py
---
