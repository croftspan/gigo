# Brief: Spec-to-Prompt Formatting

## The Problem

`gigo:spec` writes implementation plans for Claude. The task descriptions assume an agent that can read files, ask clarifying questions, make judgment calls, and iterate. Gemma can't do any of that — it gets one prompt and produces one response. The spec format needs a Gemma-compatible output mode.

## What We Know

From the Gemma eval:

- **Gemma follows literal instructions perfectly.** "Add a column to the users table" → migration + model + controller + spec. No clarification needed if the instruction is specific enough.
- **Ambiguity = Gemma's weakness.** "How should I structure the data layer?" works because the harness rules say "pick the most reasonable interpretation and proceed." But the output quality depends entirely on how much context the prompt provides.
- **File context matters.** The eval sends all source files as context alongside the prompt. Without seeing the existing code, Gemma can't produce compatible output (wrong class names, wrong table structures, missing associations).
- **One prompt, one response.** No multi-turn. No "read this file then decide." Everything Gemma needs must be in the single prompt.

## What to Build

### Gemma Task Format

When `gigo:spec` writes tasks and the plan targets local model execution, each task should include:

1. **Explicit instruction** — what to build, not what to think about. "Create a migration adding `payment_status` column to orders" not "Consider how to add payment tracking."
2. **Relevant source files inline** — the files Gemma needs to read to produce compatible code. Not all files — just the ones this task touches or depends on.
3. **Expected output files** — which files Gemma should produce code blocks for. "Output: `db/migrate/..._add_payment_status.rb`, `app/models/order.rb`, `spec/requests/orders_spec.rb`"
4. **Constraints from the harness** — any task-specific rules beyond the harness defaults.

### Example

Current spec task (Claude-targeted):
```
Task 3: Add payment status tracking
- Add a `payment_status` column to orders (enum: unpaid, paid, failed, refunded)
- Update the Order model with validations
- Add a scope for paid orders
- Write request specs covering status transitions
Dependencies: Task 1 (migration setup), Task 2 (order model exists)
```

Gemma-formatted task:
```
Add a `payment_status` column to orders.

Statuses: unpaid, paid, failed, refunded.
Default: unpaid. Validate inclusion.
Add scope `paid` → where(payment_status: 'paid').
Spec: happy path (create order with payment_status) + error case (invalid status).

## Current files

### db/schema.rb
[inline content]

### app/models/order.rb
[inline content]

## Output files
- db/migrate/YYYYMMDD_add_payment_status_to_orders.rb
- app/models/order.rb (update)
- spec/requests/orders_spec.rb (addition)
```

### Where the Formatting Happens

Option A: **In `gigo:spec`** — a `--executor local` flag that changes how tasks are written. Generates two versions: Claude-targeted (current) and Gemma-targeted.
Option B: **In `gigo:execute`** — takes the Claude-targeted plan and reformats each task before sending to Gemma. More flexible (same plan, multiple executors) but adds a translation step.
Option C: **In the harness generator** (brief 06) — the harness includes formatting rules that shape how tasks are presented.

### Source File Selection

The key challenge: which files to inline for each task? Too few and Gemma produces incompatible code. Too many and you blow the context window (8K-16K typical for local models).

Heuristic:
- Files listed in the task's "Dependencies" or "Modifies" fields → always include
- Files imported/required by those files → include if under 200 lines
- Schema/type definition files → always include (they're small and critical)
- Test helper/factory files → include if task involves specs

### Testing Required

**AB test design:**
- Take 3 plans from previous `gigo:spec` runs
- Format each task both ways (Claude-targeted, Gemma-formatted)
- Execute Gemma-formatted tasks via llama-server
- Score output: does the code compile/parse? Does it match the spec? Does it integrate with existing files?

**Format comparison:**
- Gemma with Claude-targeted task description vs Gemma with Gemma-formatted task description
- Hypothesis: Gemma-formatted tasks produce higher spec compliance because they eliminate ambiguity and provide inline context
- Measure: spec compliance rate, file integration correctness

**Context window testing:**
- How many source files can fit alongside a task in 8K context? 16K? 32K?
- At what point does adding more context hurt output quality?
- Does file ordering matter (most relevant first)?

**What could go wrong:**
- Source file selection heuristic misses a critical dependency → Gemma produces incompatible code
- Inline files blow the context window → truncated input, broken output
- Over-specifying the output format constrains Gemma too much → misses edge cases the original spec would have caught
- Two-format maintenance burden — Claude-targeted and Gemma-targeted specs drift apart

## Dependencies

- Needs the Gemma harness (brief 06) — format must be compatible with harness rules
- Needs the model routing (brief 07) — routing determines which format to use
- Informs the orchestrator (brief 09) — the orchestrator automates this formatting
