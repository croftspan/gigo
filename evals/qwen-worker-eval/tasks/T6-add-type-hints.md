---
id: T6-add-type-hints
task_type: code
spec_sentence: |
  Add correct type hints to every function parameter and return type in the Python module below. Do not change behaviour.
role: |
  You are adding type hints to an untyped Python module.
spec: |
  Here is the module as it stands. Add type hints to every parameter and every
  return type. Do not change behaviour. Do not add new imports unless required for
  the hints themselves (e.g., `from typing import ...` if needed).

  ```python
  def greet(name, punctuation="!"):
      return f"Hello, {name}{punctuation}"

  def summarize(items):
      return {"count": len(items), "first": items[0] if items else None}

  def pick_even(numbers):
      return [n for n in numbers if n % 2 == 0]

  def maybe_parse(s):
      try:
          return int(s)
      except ValueError:
          return None
  ```
acceptance: |
  - Every function parameter has a type annotation
  - Every function has a return type annotation
  - `greet` parameters are `str` (both) and return is `str`
  - `summarize` takes a sequence/list and returns a dict (use `dict` or `dict[str, ...]`)
  - `pick_even` takes a list/sequence of ints and returns a list of ints
  - `maybe_parse` takes `str` and returns `int | None` (or `Optional[int]`)
  - Behaviour is unchanged — same input, same output
  - No function bodies are rewritten
output_format: |
  - ONLY the full module with hints added inside a single ```python fence
  - No preamble, no trailing prose
mode_hint: |
  Python 3.12 — use modern PEP 604 union syntax (`int | None`) rather than `Optional`.
verifier: T6.py
---
