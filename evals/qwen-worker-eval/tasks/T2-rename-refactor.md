---
id: T2-rename-refactor
task_type: code
spec_sentence: |
  Rename the function `calc` to `compute_total` in the Python source below, updating every call site. Return the full modified file.
role: |
  You are performing a rename-refactor on a small Python module.
spec: |
  Rename the function `calc` to `compute_total` in the source below. Update every
  call site, including nested and recursive calls. Do not change behaviour.

  ```python
  def calc(items):
      if not items:
          return 0
      return items[0] + calc(items[1:])

  def report(items):
      total = calc(items)
      print(f"total={total}")

  def demo():
      data = [1, 2, 3]
      print(calc(data))
      report(data)

  if __name__ == "__main__":
      demo()
  ```
acceptance: |
  - Every occurrence of the symbol `calc` (definition + 3 call sites) is renamed to `compute_total`
  - No other code is changed (no reformatting, no added comments, no extra functions)
  - The recursive call inside the function body is renamed consistently
  - Output is syntactically valid Python that runs without errors
output_format: |
  - ONLY the full modified file inside a single ```python fence
  - No preamble, no diff notation, no explanation
mode_hint: |
  This is a pure rename — do not "improve" anything else.
verifier: T2.py
---
