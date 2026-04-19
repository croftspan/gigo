---
id: T7-regex-from-examples
task_type: code
spec_sentence: |
  Produce a Python regex that matches the positive examples and rejects the negative examples below. Use re.fullmatch semantics. Return only the pattern.
role: |
  You are writing a single Python regex from positive and negative examples.
spec: |
  The regex must be used with `re.fullmatch(pattern, s)`. It should return a match
  for every POSITIVE example and None for every NEGATIVE example.

  POSITIVE (must match):
    - "AB-1234"
    - "XY-0001"
    - "QQ-9999"

  NEGATIVE (must not match):
    - "ab-1234"
    - "ABC-1234"
    - "AB-123"
    - "AB-12345"
    - "AB1234"
    - "AB-12A4"
    - ""
acceptance: |
  - Exactly one Python regex pattern string
  - With `re.fullmatch(pattern, s)`: matches every POSITIVE example, returns None for every NEGATIVE example
  - Pattern is a raw string literal (e.g., r"...")
output_format: |
  - ONLY the raw string literal for the pattern inside a single ```python fence
  - Exactly one line of code assigning the pattern to a variable named `PATTERN`
  - E.g., `PATTERN = r"..."`
  - No preamble, no trailing prose, no imports, no test code
mode_hint: |
  Think: two uppercase letters, a hyphen, exactly four digits.
verifier: T7.py
---
