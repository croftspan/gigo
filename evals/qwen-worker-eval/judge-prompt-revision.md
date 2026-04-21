# Qwen Worker Eval — Judge (Revision / Turn 2)

You are evaluating the **turn-2 revision** of a local worker LLM
(Qwen3.6-35B-A3B-MLX-8bit) in a 2-turn flow:

1. **Turn 1** — worker was given a task and produced an initial solution.
2. **Turn 2** — worker was given a critique of that solution and asked to
   revise it. You are scoring the **turn-2 output only**.

A deterministic verifier has already checked whether the revised output
(a) still satisfies the original acceptance criteria and (b) addresses the
specific critique. Your job is to add the **quality**, **format adherence**,
**fabrication**, and **critique_addressed** judgments.

**You do not know which ticket format, thinking setting, or preserve-thinking
setting produced this output. Do not guess. Score solely on what you see.**

## Task (what the worker was asked to do in turn 1)

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

## Critique delivered at turn 2

```
{REVISION_CRITIQUE}
```

## Deterministic verifier result (2-stage)

```
{VERIFIER_RESULT}
```

(`acceptance_pass: true` means **both** the original acceptance check AND the
critique-specific check passed. `acceptance_pass: false` means one of them
failed — read the verifier message for which.)

## Worker output — turn 2 revision (exactly what the worker returned)

```
{OUTPUT}
```

---

## Scoring rubric

Return these fields. Be strict. Mark issues; do not grade on a curve.

### 1. `acceptance_pass` (boolean)
Did the revised output satisfy the original acceptance criteria?

- **For code tasks with a deterministic verifier:** copy the verifier's
  stage-1 result (original-acceptance check). The verifier output tells you
  whether that stage passed before stage 2 was even attempted.
- Use your judgment on semantic correctness — a revision that passes regex
  checks but breaks the public API the task required is `false`.

### 2. `critique_addressed` (boolean)
Did the revision actually address the critique?

- `true` iff the specific defect the critique named is fixed in the turn-2
  output. Read the critique carefully — it points at a concrete thing
  (a rename, a signature preservation, an extraction, an import removal,
  a fixture rename, a down-migration detail).
- `false` if the worker ignored the critique, fixed something else, claimed
  to fix it but didn't, or made the same mistake with different words.
- Do not reward effort — a long explanation of *why* the critique was
  addressed without the corresponding code change is still `false`.
- The verifier's stage-2 result is your strongest signal. Override it only
  when the worker clearly addressed the critique in a way the regex/AST
  check happened to miss (rare — note it if you do).

### 3. `format_adherence` (boolean)
Did the revised output respect the stated OUTPUT FORMAT precisely?

Same rubric as turn 1 — a single `python` fence when asked for one, named
headings + fences for multi-file outputs, no trailing prose.

### 4. `fabrication_present` (boolean)
Did the worker invent anything in the revision that wasn't in the ticket or
the standard library?

Same rubric as turn 1. Pay extra attention: during revision, workers sometimes
invent justification ("I also added…", "the tests now cover…") that claims
changes they didn't make. If the worker says it did X and X isn't in the
output → `fabrication_present: true`.

### 5. `quality` (integer 1-5)
Overall craft of the revised output. Consider: code clarity, absence of dead
code, sensible variable names, docstring adequacy, edge-case handling, idiom
fit — applied to the **turn-2 artifact**, not turn 1.

- **1:** Hacky, unclear, or buggy even if it happens to pass. Reads like a
  panicked intern.
- **2:** Works but ugly — awkward structure, poor names, or obvious
  inefficiency.
- **3:** Competent. Correct, readable, unremarkable.
- **4:** Clearly senior work. Good naming, idiomatic, tight. The revision
  fixes the critique cleanly without collateral churn.
- **5:** Outstanding. Elegant, minimal. The revision is surgical: only the
  critique-affected surface changes.

**Regression penalty:** if the revision introduces a new defect (breaks a
previously-passing part of the spec, widens the diff beyond what the critique
asked for, or changes unrelated names), drop `quality` by 1-2 and flag it in
`notes`.

### 6. `notes` (one sentence)
One sentence explaining the key observation. If `critique_addressed` is
`false`, say exactly why. If the revision broke something that was working in
turn 1, name it. If `fabrication_present` is `true`, name what was fabricated.

---

## Output

Respond with ONLY this JSON object (no other text, no code fence, no preamble):

```
{
  "acceptance_pass": true | false,
  "critique_addressed": true | false,
  "format_adherence": true | false,
  "fabrication_present": true | false,
  "quality": 1-5,
  "notes": "one-sentence explanation"
}
```
