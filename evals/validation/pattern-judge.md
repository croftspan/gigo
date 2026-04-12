# Execution Pattern Judge

You are scoring whether a plan correctly identifies and applies an execution pattern.

## The Plan Output

{PLAN_OUTPUT}

## Expected Pattern

{EXPECTED_PATTERN}

## Your Job

Determine whether the plan uses the correct execution pattern for the task.

**Score YES if the plan:**
- Explicitly names the correct pattern (e.g., "Pipeline", "Fan-out/Fan-in", "Producer-Reviewer"), OR
- Describes the correct structure without naming it:
  - Pipeline: tasks run sequentially, each consuming the previous step's output
  - Fan-out/Fan-in: independent tasks run in parallel, results merged afterward
  - Producer-Reviewer: one phase generates output, a separate independent phase reviews/validates it

**Score NO if:**
- The plan uses a different execution shape (e.g., parallelizes a Pipeline task, serializes a Fan-out task)
- The plan ignores execution structure entirely (just lists steps without addressing dependencies)
- The plan defaults to generic sequential ordering without acknowledging the task's dependency shape

## Output

Respond with ONLY a JSON object. No other text, no markdown fences.

{ "pattern": "Pipeline", "correct": true, "evidence": "The plan describes sequential execution where each step depends on the previous step's output" }
