---
id: L1-revise-extract-module-level
task_type: code
size_bucket: L
reference_task: phase2a/L1-god-class-split
critique_type: synthetic-craft
revision_critique: |
  The private formatting helpers on `ReportFormatter` (`_format_markdown`,
  `_format_html`, and any other `_format_*` methods) never touch `self`. Lift
  them to module-level functions so the class only holds the public entry point
  (e.g. `render(stats, fmt)`), and have that entry point call the module-level
  functions directly. Keep the public API of `ReportGenerator.generate()`
  identical.
verifier: L1.py
---

Revision task. Turn 1 uses the Phase 2A L1 spec; turn 2 applies the critique
above. Synthetic-craft: Phase 2A recorded no observed defect on L1.
