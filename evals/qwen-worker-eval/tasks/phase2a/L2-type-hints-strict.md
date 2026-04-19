---
id: L2-type-hints-strict
task_type: code
size_bucket: L
spec_sentence: |
  Add complete type annotations to every function in the module below. Do not change behaviour. Use modern PEP 604 syntax.
role: |
  You are adding full type annotations to an untyped Python 3.12 module. Do not change runtime behaviour.
spec: |
  Below is a 8-function untyped module. Add annotations to every parameter
  (including `*args`, `**kwargs` where they appear) and every return type.

  Constraints:
  - Use PEP 604 union syntax (`int | None`), not `Optional[int]`.
  - Prefer built-in generics: `list[int]`, `dict[str, int]`, `tuple[int, ...]`.
  - For callables, use `collections.abc.Callable`. You may add `from collections.abc import Callable` if needed.
  - For iterators, use `collections.abc.Iterator`. You may add the import.
  - Do not change any function body, variable name, or default value.
  - Do not add comments.

  ```python
  import json
  import statistics
  from collections import Counter


  def read_ints(path):
      with open(path) as f:
          return [int(line.strip()) for line in f if line.strip()]


  def parse_config(raw):
      data = json.loads(raw)
      if not isinstance(data, dict):
          return None
      result = {}
      for k, v in data.items():
          if isinstance(v, (int, float, str)):
              result[str(k)] = v
      return result


  def histogram(values, bucket_size=1):
      buckets = Counter()
      for v in values:
          key = (v // bucket_size) * bucket_size
          buckets[key] += 1
      return dict(buckets)


  def describe(values):
      if not values:
          return {"count": 0, "mean": None, "stdev": None, "min": None, "max": None}
      return {
          "count": len(values),
          "mean": statistics.mean(values),
          "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
          "min": min(values),
          "max": max(values),
      }


  def pick(values, predicate):
      return [v for v in values if predicate(v)]


  def batched(items, size):
      buf = []
      for item in items:
          buf.append(item)
          if len(buf) == size:
              yield buf
              buf = []
      if buf:
          yield buf


  def first_or_default(items, default=None):
      for item in items:
          return item
      return default


  def merge_dicts(*dicts, overwrite=True):
      out = {}
      for d in dicts:
          for k, v in d.items():
              if overwrite or k not in out:
                  out[k] = v
      return out
  ```
acceptance: |
  - Every function in the module has a return annotation
  - Every function parameter has a type annotation (including `*args`, `**kwargs` forms if present)
  - `read_ints(path)` annotates path as `str` (or `str | Path` — but don't add Path unless you also import it)
  - `parse_config(raw)` annotates raw as `str` and return as `dict[str, int | float | str] | None`
  - `histogram(values, bucket_size=1)` annotates values as iterable of int and bucket_size as `int`, returns `dict[int, int]`
  - `describe(values)` return type is `dict[str, int | float | None]`
  - `pick(values, predicate)` uses `Callable[[T], bool]` or `Callable[..., bool]` for predicate; any consistent generic annotation is fine
  - `batched(items, size)` return type is `Iterator[list[T]]` or `Iterator[list]`
  - `first_or_default(items, default=None)` uses union with `None`
  - `merge_dicts(*dicts, overwrite=True)` annotates `*dicts` as `dict` and `overwrite` as `bool`, returns `dict`
  - The annotated module still runs and every function produces the same output as the unannotated module on the same inputs
  - No `from typing import Optional` — use `| None` instead
output_format: |
  - ONLY the annotated module (including imports) inside a single ```python fence
  - No preamble, no trailing prose
mode_hint: |
  Python 3.12. `collections.abc.Callable` and `collections.abc.Iterator` are fine to import. Do not touch function bodies.
verifier: L2.py
---
