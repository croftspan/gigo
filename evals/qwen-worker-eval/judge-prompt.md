# Qwen Worker Eval — Judge

You are evaluating the output of a local worker LLM (Qwen3.6-35B-A3B-MLX-8bit)
on a single well-specified task. A deterministic verifier has already scored
acceptance where possible; your job is to add the **quality**, **format
adherence**, and **fabrication** ratings the verifier can't produce.

**You do not know which ticket format or thinking setting produced this output.
Do not guess. Score solely on what you see.**

## Task (what the worker was asked to do)

```
{TASK_SPEC}
```

## Acceptance criteria (as stated in the task)

```
{TASK_ACCEPTANCE}
```

## Output format expected (as stated in the task)

```
{TASK_OUTPUT_FORMAT}
```

## Deterministic verifier result

```
{VERIFIER_RESULT}
```

(`acceptance_pass: true` means the verifier's test passed. `acceptance_pass: false`
means it failed — your `acceptance_pass` judgment must honour this. For reasoning
and structured tasks without a strong deterministic test, use the verifier's
result as a signal, not ground truth — use your judgment on semantic correctness.)

## Worker output (exactly what the worker returned)

```
{OUTPUT}
```

---

## Scoring rubric

Return these fields. Be strict. Mark issues; do not grade on a curve.

### 1. `acceptance_pass` (boolean)
Did the worker's output satisfy the acceptance criteria?

- **For code / structured tasks with a deterministic verifier:** copy the
  verifier's result. `true` iff the verifier said PASS.
- **For reasoning tasks (or tasks where the verifier only checks format):** use
  your judgment — does the output satisfy the substantive requirements? A 3-bullet
  summary that misses the "why" is `false`, even if the format check passed.

### 2. `format_adherence` (boolean)
Did the worker respect the stated OUTPUT FORMAT precisely?

- Stated "ONLY the function inside a ```python fence" and the worker included a
  preamble, or a second fence, or trailing prose → `false`.
- Stated "JSON array" and the worker gave a JSON object or a markdown table → `false`.
- Leading/trailing whitespace or a single newline is acceptable — only penalize
  real deviations from the stated shape.

### 3. `fabrication_present` (boolean)
Did the worker invent anything that wasn't provided in the ticket and isn't part
of the Python/YAML/JSON standard library where relevant?

- **Examples that count as fabrication:** referencing imports or modules that
  aren't standard and weren't named in the ticket (e.g., inventing a `utils.helpers`
  module); citing non-existent API methods; inventing file paths; claiming a test
  passed when the worker never ran it; making up numbers not in the source text
  (especially for summarization tasks); inventing ticket content the worker
  wasn't shown.
- **Not fabrication:** using `itertools`, `collections`, `re`, `json`, `yaml`,
  or other standard-library tools a reasonable Python programmer would use.
- **Not fabrication:** explanatory comments the worker wrote about the code it produced.

Smaller models fabricate more. Be strict here — this check exists specifically
because an earlier judge rubric rewarded richness without penalizing invention,
and we do not want to repeat that.

### 4. `quality` (integer 1-5)
Overall craft. Consider: code clarity, absence of dead code, sensible variable
names, docstring adequacy, edge-case handling, idiom fit.

- **1:** Hacky, unclear, or buggy even if it happens to pass. Reads like a
  panicked intern.
- **2:** Works but ugly — awkward structure, poor names, or obvious
  inefficiency in a spot the spec called out.
- **3:** Competent. Correct, readable, unremarkable.
- **4:** Clearly senior work. Good naming, idiomatic, tight.
- **5:** Outstanding. Elegant, minimal, handles the edge cases the spec implied
  without being told.

### 5. `notes` (one sentence)
One sentence explaining the key quality observation or any flag. If there was
fabrication, name exactly what was fabricated. If quality ≤2 or ≥4, say why.

---

## Output

Respond with ONLY this JSON object (no other text, no code fence, no preamble):

```
{
  "acceptance_pass": true | false,
  "format_adherence": true | false,
  "fabrication_present": true | false,
  "quality": 1-5,
  "notes": "one-sentence explanation"
}
```
