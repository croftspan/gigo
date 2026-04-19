---
id: T10-classify-error-log
task_type: structured
spec_sentence: |
  Classify the Python stack trace below. Output a JSON object with severity (fatal|error|warn) and category (a short kebab-case label).
role: |
  You are classifying an error log for an alerting pipeline.
spec: |
  Given this error log:

  ```
  2026-04-18 03:14:22,107 ERROR [worker-7] Unhandled exception in job runner
  Traceback (most recent call last):
    File "/app/jobs/runner.py", line 118, in _execute
      result = job.run(ctx)
    File "/app/jobs/email_blast.py", line 42, in run
      conn = psycopg.connect(self.dsn, connect_timeout=2)
    File "/usr/local/lib/python3.12/site-packages/psycopg/__init__.py", line 148, in connect
      raise OperationalError(...)
  psycopg.OperationalError: connection to server at "db.internal" (10.0.0.14), port 5432 failed: Connection timed out
  ```

  Classify it. The severity is one of: `fatal` (process cannot continue),
  `error` (operation failed but process continues), `warn` (degraded but
  recoverable). The category is a short kebab-case label describing the error
  type — not the product area.
acceptance: |
  - Output is a single JSON object
  - Has exactly two keys: "severity" and "category"
  - "severity" is one of: "fatal", "error", "warn" — for this log, "error" is correct (operation failed, worker continues)
  - "category" is kebab-case and describes the failure type — acceptable values include "db-connection-timeout", "database-connection-timeout", "connection-timeout", or equivalent
  - No other keys
output_format: |
  - ONLY a JSON object inside a single ```json fence
  - No preamble, no trailing prose
mode_hint: |
  The error is an unhandled exception in one worker job — the process survives.
verifier: T10.py
---
