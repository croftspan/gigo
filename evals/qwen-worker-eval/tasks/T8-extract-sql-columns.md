---
id: T8-extract-sql-columns
task_type: structured
spec_sentence: |
  Given the SQL SELECT statement below, output a JSON array of the selected column names (final output names — i.e., the alias if one is present).
role: |
  You are extracting selected column names from a SQL SELECT statement.
spec: |
  Given this SQL statement:

  ```sql
  SELECT
    u.id,
    u.email AS user_email,
    COUNT(o.id) AS order_count,
    SUM(o.total) total_spent,
    u.created_at
  FROM users u
  LEFT JOIN orders o ON o.user_id = u.id
  WHERE u.active = true
  GROUP BY u.id, u.email, u.created_at
  ORDER BY order_count DESC
  LIMIT 100;
  ```

  Output the list of columns that will appear in the result set, in order, using
  the final output name (the alias when one is present, otherwise the bare column
  name without table qualifier).
acceptance: |
  - Output is a valid JSON array of strings
  - Exactly 5 entries, in this order: ["id", "user_email", "order_count", "total_spent", "created_at"]
  - No table prefixes (e.g., "u.id" is wrong — use "id")
  - When an alias exists (AS alias OR bare alias), use the alias
output_format: |
  - ONLY a JSON array inside a single ```json fence
  - No preamble, no trailing prose
mode_hint: |
  Watch for the bare alias `total_spent` (no AS keyword) on the SUM expression.
verifier: T8.py
---
