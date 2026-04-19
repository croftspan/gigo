---
id: T4-json-to-yaml
task_type: code
spec_sentence: |
  Convert the JSON blob below into equivalent YAML, preserving all types (strings, ints, booleans, nulls, nested structure). Return only the YAML.
role: |
  You are converting a JSON document to YAML for a config migration.
spec: |
  Convert this JSON to YAML. Preserve types exactly: ints stay as ints, booleans as
  booleans (`true`/`false`), nulls as `null`, strings quoted only if YAML requires it.

  ```json
  {
    "service": {
      "name": "auth-api",
      "port": 8080,
      "enabled": true,
      "replicas": 3,
      "tags": ["prod", "eu-west-1", "v2"],
      "env": {
        "LOG_LEVEL": "info",
        "FEATURE_X": false,
        "RETRY_BACKOFF_MS": 250
      },
      "healthcheck": null
    }
  }
  ```
acceptance: |
  - Output is valid YAML that `yaml.safe_load` can parse
  - Round-trips back to a dict that is deeply equal to the input JSON (same types, same keys, same values)
  - No comments added
  - No extra top-level keys
output_format: |
  - ONLY the YAML inside a single ```yaml fence
  - No preamble, no explanation
mode_hint: |
  Two-space indentation. Do not wrap unambiguous scalar values in quotes.
verifier: T4.py
---
