---
id: L1-god-class-split
task_type: code
size_bucket: L
spec_sentence: |
  Split the ReportGenerator god-class below into three responsibility-based classes (Reader, Computer, Formatter) plus a thin ReportGenerator facade that preserves the public API.
role: |
  You are refactoring a god-class into composition-based components.
spec: |
  Below is a single class, `ReportGenerator`, that mixes three responsibilities:
  reading data, computing statistics, and formatting output. Refactor it into
  **four** classes:

  1. `ReportReader` — turns a raw `dict` payload into a normalised list of rows.
  2. `ReportComputer` — given normalised rows, computes statistics.
  3. `ReportFormatter` — given statistics, produces a report string.
  4. `ReportGenerator` — a thin facade that composes Reader + Computer + Formatter
     and preserves the existing public API (`generate(payload, fmt)` returns the
     same strings as before).

  The original `ReportGenerator` public API that MUST be preserved:

  - `ReportGenerator()` constructor takes no arguments
  - `generate(payload: dict, fmt: str) -> str` — `fmt` is `"markdown"` or `"html"`

  Private/helper methods may move to the new classes; only the public surface
  above is contractual.

  ```python
  class ReportGenerator:
      """Monolithic reporter. Loads data, computes stats, formats output."""

      def __init__(self):
          self._rows: list[dict] = []
          self._stats: dict = {}

      # ---- I/O ----
      def _normalise_row(self, row: dict) -> dict:
          return {
              "category": str(row.get("category", "unknown")).strip().lower(),
              "amount": float(row.get("amount", 0)),
              "count": int(row.get("count", 0)),
          }

      def _load_from_payload(self, payload: dict) -> None:
          raw = payload.get("rows", []) or []
          self._rows = [self._normalise_row(r) for r in raw if isinstance(r, dict)]

      # ---- Computation ----
      def _group_by_category(self) -> dict:
          grouped: dict = {}
          for row in self._rows:
              cat = row["category"]
              bucket = grouped.setdefault(cat, {"amount": 0.0, "count": 0})
              bucket["amount"] += row["amount"]
              bucket["count"] += row["count"]
          return grouped

      def _compute_totals(self) -> dict:
          total_amount = sum(r["amount"] for r in self._rows)
          total_count = sum(r["count"] for r in self._rows)
          return {"amount": total_amount, "count": total_count}

      def _compute_means(self) -> dict:
          if not self._rows:
              return {"amount": 0.0, "count": 0.0}
          n = len(self._rows)
          return {
              "amount": sum(r["amount"] for r in self._rows) / n,
              "count": sum(r["count"] for r in self._rows) / n,
          }

      def _run_computations(self) -> None:
          self._stats = {
              "groups": self._group_by_category(),
              "totals": self._compute_totals(),
              "means": self._compute_means(),
              "row_count": len(self._rows),
          }

      # ---- Formatting ----
      def _format_markdown(self) -> str:
          lines = ["# Report", ""]
          lines.append(f"Rows: {self._stats['row_count']}")
          lines.append(f"Total amount: {self._stats['totals']['amount']:.2f}")
          lines.append(f"Total count: {self._stats['totals']['count']}")
          lines.append("")
          lines.append("## By category")
          for cat in sorted(self._stats["groups"]):
              g = self._stats["groups"][cat]
              lines.append(f"- {cat}: amount={g['amount']:.2f} count={g['count']}")
          return "\n".join(lines)

      def _format_html(self) -> str:
          rows = []
          rows.append("<h1>Report</h1>")
          rows.append(f"<p>Rows: {self._stats['row_count']}</p>")
          rows.append(
              f"<p>Total amount: {self._stats['totals']['amount']:.2f}</p>"
          )
          rows.append(f"<p>Total count: {self._stats['totals']['count']}</p>")
          rows.append("<h2>By category</h2>")
          rows.append("<ul>")
          for cat in sorted(self._stats["groups"]):
              g = self._stats["groups"][cat]
              rows.append(
                  f"<li>{cat}: amount={g['amount']:.2f} count={g['count']}</li>"
              )
          rows.append("</ul>")
          return "\n".join(rows)

      # ---- Public API ----
      def generate(self, payload: dict, fmt: str) -> str:
          self._load_from_payload(payload)
          self._run_computations()
          if fmt == "markdown":
              return self._format_markdown()
          if fmt == "html":
              return self._format_html()
          raise ValueError(f"unknown fmt: {fmt!r}")
  ```
acceptance: |
  - Four classes are defined: `ReportReader`, `ReportComputer`, `ReportFormatter`, `ReportGenerator`
  - None of the four classes inherits from another one of the four
  - `ReportGenerator()` takes no constructor args
  - `ReportGenerator().generate(payload, "markdown")` returns the SAME string as the original
  - `ReportGenerator().generate(payload, "html")` returns the SAME string as the original
  - `ReportGenerator().generate(payload, "xml")` raises `ValueError`
  - Each of Reader / Computer / Formatter is usable in isolation (for example: `ReportComputer().compute(rows)` returns a stats dict; `ReportFormatter().render(stats, "markdown")` returns a string). Exact method names are your call, but each class must expose at least one public method that does its job.
output_format: |
  - ONLY the refactored module inside a single ```python fence
  - No preamble, no trailing prose
  - All four classes in the same fence
mode_hint: |
  Keep the private helper functions' logic — the refactor is structural, not behavioural. Do NOT change the formatter output strings.
verifier: L1.py
---
