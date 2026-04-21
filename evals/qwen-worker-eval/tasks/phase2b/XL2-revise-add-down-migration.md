---
id: XL2-revise-add-down-migration
task_type: code
size_bucket: XL
reference_task: phase2a/XL2-nullable-field-add
critique_type: synthetic-craft
revision_critique: |
  Your `migration.py` `down()` returns `DROP TABLE users;`, which drops
  everything — not a symmetric reversal of adding `deleted_at`. Replace
  `down()` with a column-specific reversal that contains an
  `ALTER TABLE users DROP COLUMN deleted_at` statement, so the migration is
  individually reversible. Keep `up()` and all other files unchanged.
verifier: XL2.py
---

Revision task. Turn 1 uses the Phase 2A XL2 spec; turn 2 applies the critique
above. Synthetic-craft: Phase 2A recorded no observed defect on XL2.
