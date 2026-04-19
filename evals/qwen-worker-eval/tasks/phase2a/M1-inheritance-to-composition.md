---
id: M1-inheritance-to-composition
task_type: code
size_bucket: M
spec_sentence: |
  Refactor the 3-level inheritance hierarchy below into a composition-based design with the same public API. All public methods must behave identically for the given acceptance calls.
role: |
  You are refactoring a small Python module from inheritance to composition.
spec: |
  Below is a 3-level inheritance hierarchy of loggers. Refactor it so each
  responsibility (formatting, timestamping, level prefixing) becomes a
  separate small class, and `LeveledLogger` is built by *composing* those
  helpers rather than inheriting.

  The public API of `LeveledLogger` must be preserved:
  - constructor signature: `LeveledLogger(name: str, clock, level: str)`
  - instance method: `write(msg: str) -> None` (prints the formatted line)
  - the printed line must exactly equal: `f"{level} [{clock()}] [{name}] {msg}"`

  Original (inheritance-based):

  ```python
  class Logger:
      def __init__(self, name: str):
          self.name = name

      def format(self, msg: str) -> str:
          return f"[{self.name}] {msg}"

      def write(self, msg: str) -> None:
          print(self.format(msg))


  class TimestampedLogger(Logger):
      def __init__(self, name: str, clock):
          super().__init__(name)
          self.clock = clock

      def format(self, msg: str) -> str:
          ts = self.clock()
          return f"[{ts}] {super().format(msg)}"


  class LeveledLogger(TimestampedLogger):
      def __init__(self, name: str, clock, level: str):
          super().__init__(name, clock)
          self.level = level

      def format(self, msg: str) -> str:
          return f"{self.level} {super().format(msg)}"
  ```

  In the refactored version:
  - No class should inherit from another class you wrote.
  - `LeveledLogger.__init__` may accept the same args as before, and internally
    build whatever helper objects it needs.
acceptance: |
  - Zero inheritance among the classes you define (each helper + the facade is a standalone class)
  - `LeveledLogger("app", lambda: "T1", "INFO").write("hi")` prints exactly: `INFO [T1] [app] hi`
  - `LeveledLogger("svc", lambda: "T9", "WARN").write("disk full")` prints exactly: `WARN [T9] [svc] disk full`
  - No use of `super()` anywhere in your output
  - `LeveledLogger` constructor signature unchanged: `(name: str, clock, level: str)`
output_format: |
  - ONLY the refactored module inside a single ```python fence
  - No preamble, no trailing prose
  - All needed classes in one fenced block
mode_hint: |
  Python 3.12. Think: prefix formatter, timestamp decorator, name formatter — each a small class with one method — then `LeveledLogger` holds them and composes their output.
verifier: M1.py
---
