---
id: XL1-revise-rename-fixture-ids
task_type: code
size_bucket: XL
reference_task: phase2a/XL1-domain-rename
critique_type: synthetic-craft
revision_critique: |
  Your rename stopped at the symbol level. The test fixture ID string literals
  in `test_purchase_service.py` are still `"o1"` and `"o2"` (and any other
  `o`-prefixed fixture strings you carried across). Rename those string
  literals to `"p1"` and `"p2"` (use the same 1-for-1 letter mapping for any
  other `o*` fixture IDs) so the Purchase vocabulary is consistent down to
  the test data. Keep all symbol-level renames intact.
verifier: XL1.py
---

Revision task. Turn 1 uses the Phase 2A XL1 spec; turn 2 applies the critique
above. Synthetic-craft: Phase 2A recorded no observed defect on XL1.
