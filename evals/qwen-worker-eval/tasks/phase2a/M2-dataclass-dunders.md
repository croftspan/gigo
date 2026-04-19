---
id: M2-dataclass-dunders
task_type: code
size_bucket: M
spec_sentence: |
  Add `__repr__` and `__eq__` methods to every one of the six plain classes below so they behave as value-objects. Preserve every other aspect of each class.
role: |
  You are adding dunder methods to a small Python module of plain value-style classes.
spec: |
  Below are six plain classes (none are @dataclass). Each has an `__init__`
  that assigns its constructor args to instance attributes of the same name.
  Add two methods to every class:

  1. `__repr__(self) -> str` — returns `ClassName(field=value, field=value, ...)` with fields in constructor order; use `repr()` on each value.
  2. `__eq__(self, other) -> bool` — returns True iff `type(other) is type(self)` and every named field compares equal. (Do not use `isinstance` — require exact type match.)

  Rules:
  - Do NOT convert any class to `@dataclass`. The verifier checks class bodies.
  - Do NOT add `__hash__`, `__lt__`, or any other dunder.
  - Do NOT add imports.
  - Preserve constructor order of fields.

  ```python
  class Point:
      def __init__(self, x, y):
          self.x = x
          self.y = y


  class Rectangle:
      def __init__(self, width, height, label):
          self.width = width
          self.height = height
          self.label = label


  class Circle:
      def __init__(self, radius):
          self.radius = radius


  class Color:
      def __init__(self, r, g, b, alpha):
          self.r = r
          self.g = g
          self.b = b
          self.alpha = alpha


  class User:
      def __init__(self, username, email, active):
          self.username = username
          self.email = email
          self.active = active


  class Employee:
      def __init__(self, name, department, salary, manager):
          self.name = name
          self.department = department
          self.salary = salary
          self.manager = manager
  ```
acceptance: |
  - All six classes still present with the same names and `__init__` signatures
  - Every class has a `__repr__` that returns `ClassName(field=value, ...)` with fields in constructor order
  - Every class has an `__eq__` that returns True iff type matches exactly and all fields compare equal; False otherwise (including vs a different class with identical fields)
  - `repr(Point(1, 2)) == "Point(x=1, y=2)"`
  - `Rectangle(3, 4, "room") == Rectangle(3, 4, "room")` is True
  - `Rectangle(3, 4, "room") == Point(3, 4)` is False
  - No use of `@dataclass`
  - No added imports
output_format: |
  - ONLY the modified module inside a single ```python fence
  - No preamble, no trailing prose
mode_hint: |
  Six near-identical edits. Keep the pattern uniform: each `__repr__` returns `f"{type(self).__name__}({', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())})"` — or the hand-written equivalent.
verifier: M2.py
---
