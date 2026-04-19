---
id: T3-bugfix-from-failing-test
task_type: code
spec_sentence: |
  Fix the function `fizzbuzz` below so it passes the given pytest test. Return only the corrected function.
role: |
  You are fixing a broken function so a failing test passes.
spec: |
  Here is the current (buggy) implementation:

  ```python
  def fizzbuzz(n: int) -> str:
      if n % 3 == 0:
          return "Fizz"
      if n % 5 == 0:
          return "Buzz"
      if n % 15 == 0:
          return "FizzBuzz"
      return str(n)
  ```

  Here is the test that is currently failing:

  ```python
  def test_fizzbuzz():
      assert fizzbuzz(1) == "1"
      assert fizzbuzz(3) == "Fizz"
      assert fizzbuzz(5) == "Buzz"
      assert fizzbuzz(15) == "FizzBuzz"
      assert fizzbuzz(30) == "FizzBuzz"
      assert fizzbuzz(9) == "Fizz"
      assert fizzbuzz(10) == "Buzz"
  ```
acceptance: |
  - Fix the function so every assertion in `test_fizzbuzz` passes
  - Preserve the signature `def fizzbuzz(n: int) -> str`
  - Do not modify the test
  - Do not add new imports or helper functions
output_format: |
  - ONLY the corrected function inside a single ```python fence
  - No preamble, no trailing prose
mode_hint: |
  The ordering of the branches matters. Think about which condition must be checked first.
verifier: T3.py
---
