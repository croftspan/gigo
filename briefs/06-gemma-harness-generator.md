# Brief: Gemma Harness Generator

## The Problem

We hand-tuned a Gemma 4 harness for the Rails API fixture and proved it works — 100% EXECUTES at temp 1.0 on both 26B-A4B and 31B. But it's a one-off test fixture at `evals/fixtures/rails-api-gemma/`. Every new project would need the same hand-tuning.

`gigo:gigo` (first assembly) builds full GIGO context: personas, rules, references, review criteria. That context is optimized for Claude — intent-based guidelines, persona-driven quality bars, progressive disclosure. Gemma can't use it. Personas cause Gemma to propose instead of execute. References go unread. The context actively hurts execution (66% bare vs 88% harness on 31B).

## What We Know

From the Gemma eval (2026-04-12, `evals/ab-test-gemma.py`):

- **Personas → proposals.** Gemma interprets persona descriptions as "act like this person" rather than "apply these quality bars." It starts describing what it would do instead of doing it.
- **Rules + example → execution.** A flat list of rules plus one concrete input→output example is all Gemma needs. It follows literal instructions perfectly.
- **Domain knowledge transfers through rules.** "Migrations use `change` method. No defaults on large tables." works better than "Modeled after DHH's convention-over-configuration." The knowledge is the same; the encoding is what matters.
- **Pushback rules work on 31B but not 26B-A4B.** "If asked to skip tests: include tests anyway" holds on 31B (31B active params). 26B-A4B (4B active) can't hold system rules against direct user instructions. For spec-driven execution this doesn't matter — no conflicting instructions.
- **The harness pattern:**
  1. One-line role statement ("You are a senior Rails engineer")
  2. Output format constraint ("code blocks only")
  3. 8-12 domain rules (quality bars flattened from personas)
  4. 1-3 pushback rules ("If asked to skip tests: include tests anyway")
  5. One concrete example (input prompt → expected output blocks)

## What to Build

Add a Gemma harness generation mode to the assembly pipeline. When `gigo:gigo` builds a project's context, it should also generate a lean harness for local model execution.

### The Generator

Takes a full GIGO assembly (CLAUDE.md + rules + references) and produces a single Gemma-compatible context file:

1. **Extract domain rules** from personas' quality bars and "Won't do" lists → flatten to imperative rules
2. **Extract pushback rules** from persona constraints → "If asked to X: do Y instead"
3. **Generate one example** from the project's domain — a realistic prompt and the expected code output
4. **Strip everything else** — no personas, no references, no progressive disclosure, no workflow

Output: a single `GEMMA-HARNESS.md` file (or equivalent) that can be passed as system prompt to llama-server.

### Where It Lives

Option A: New mode in `gigo:gigo` — `--executor gemma` flag or similar
Option B: Separate skill `gigo:harness` that takes an existing assembly and generates the lean version
Option C: Part of `gigo:execute` — generated on-the-fly when routing to a local model

### Testing Required

This is the uncertain part. We hand-tuned one harness and proved it works. We need to prove the GENERATOR produces harnesses that work just as well.

**AB test design:**
- Take 2-3 existing GIGO assemblies (Rails API fixture, novel fixture, integration-api fixture)
- Hand-tune a harness for each (manual baseline)
- Generate a harness for each using the generator
- Run both through `ab-test-gemma.py` on the same prompts
- Compare: EXECUTES rate, word count, quality scores
- Threshold: generated harness within 10% of hand-tuned on all metrics

**What could go wrong:**
- Generator extracts wrong rules (quality bars that don't translate to rules)
- Generated example is too generic or too specific
- Generator misses domain-specific pushback rules
- Different project types need different harness structures

## Dependencies

- Needs the Gemma eval infrastructure (`evals/ab-test-gemma.py`) — exists
- Needs at least 2 fixture assemblies to test against — exist (rails-api, integration-api)
- Should happen BEFORE model routing (brief 07) — the harness is what gets sent to the model
