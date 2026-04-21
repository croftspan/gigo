---
id: M1-revise-naming-drift
task_type: code
size_bucket: M
reference_task: phase2a/M1-inheritance-to-composition
critique_type: real-defect
revision_critique: |
  Your `TimestampDecorator` class is named like a decorator but doesn't decorate
  anything — it's just a helper that adds a timestamp field. Rename it to
  something that reflects what it actually does (`TimestampFormatter`,
  `TimestampPrefixer`, or similar — your call), and update every reference to
  the old name. Keep all other code unchanged.
verifier: M1.py
---

Revision task. Turn 1 uses the Phase 2A M1 spec; turn 2 applies the critique
above. The critique anchors on Phase 2A judge note M1 r3:
"TimestampDecorator isn't actually a decorator."
