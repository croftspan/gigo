---
id: M3-revise-preserve-signature
task_type: code
size_bucket: M
reference_task: phase2a/M3-pipeline-bugfixes
critique_type: real-defect
revision_critique: |
  Your fix to `normalize` changed the function's signature. The acceptance
  criteria require function signatures to stay unchanged
  (`normalize(rows: list[list[str]], defaults: list[list[str]] = []) -> list[list[str]]`).
  Fix the mutable-default-argument bug without changing the public signature —
  use the sentinel-default pattern inside the body:

      def normalize(rows, defaults=[]):
          if defaults:
              ...  # still need to avoid the shared-state leak

  The classic fix is either `defaults = list(defaults)` at the top of the body
  or a None sentinel with the same external default — whichever keeps the
  signature identical to the original while avoiding the shared-list trap.
verifier: M3.py
---

Revision task. Turn 1 uses the Phase 2A M3 spec; turn 2 applies the critique
above. The critique anchors on Phase 2A judge note M3 r3/r4:
"changed normalize's signature (correct bug-fix, unnecessary API break)."
