---
id: T5-write-test-for-function
task_type: code
spec_sentence: |
  Write a pytest test module for the `parse_iso_date` function below. Cover success and error cases.
role: |
  You are writing a pytest test module for a single utility function.
spec: |
  Target function (already implemented, do NOT modify it):

  ```python
  from datetime import date

  def parse_iso_date(s: str) -> date:
      """Parse a strict ISO-8601 date string (YYYY-MM-DD). Raise ValueError otherwise."""
      if not isinstance(s, str):
          raise ValueError("not a string")
      if len(s) != 10 or s[4] != "-" or s[7] != "-":
          raise ValueError("bad format")
      y, m, d = s[:4], s[5:7], s[8:]
      if not (y.isdigit() and m.isdigit() and d.isdigit()):
          raise ValueError("non-digit")
      return date(int(y), int(m), int(d))
  ```

  Write a pytest test module that imports `parse_iso_date` from `iso_date` and tests
  it thoroughly.
acceptance: |
  - At least one test that parses a valid ISO date successfully (e.g., "2024-02-29" leap year)
  - At least one test that asserts `ValueError` is raised for an invalid-format string (e.g., "2024/02/29")
  - At least one test that asserts `ValueError` is raised for a non-string input (e.g., `12345`)
  - Uses `pytest.raises` for error-case assertions
  - Each test is a top-level function whose name starts with `test_`
  - Collects and runs under pytest with no errors (ignoring whether the target is actually importable)
output_format: |
  - ONLY the test module source inside a single ```python fence
  - No preamble, no trailing prose
mode_hint: |
  Assume `parse_iso_date` lives in a module named `iso_date`.
verifier: T5.py
---
