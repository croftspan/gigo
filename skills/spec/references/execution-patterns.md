# Execution Pattern Catalog

## Purpose

This catalog names the execution shapes a plan can take. Read it when decomposing tasks so the plan's shape is explicit instead of implicit. The catalog is domain-agnostic — it applies to code, writing, research, or any work GIGO plans.

## Lineage

Adapted from harness's six-pattern catalog, omitting Hierarchical Delegation. Recursive delegation adds complexity without clear value for GIGO's current use cases — we may revisit if a concrete need appears.

## When to consult this file

Read this catalog during plan writing, before decomposing tasks into a dependency graph. The pattern you pick shapes what you write and how a reviewer reads it later.

## How to use

1. Pick the pattern matching the work's shape — use the decision tree below if you're unsure.
2. Declare it in the plan header as `**Execution Pattern:** <name>`. For multi-phase plans, declare a pattern per phase under each phase heading.
3. Decompose tasks per the pattern's GIGO mapping (below).

## Decision tree

- Work is strictly sequential, each step feeds the next → **Pipeline**
- Parallel workers produce artifacts, need a single merge step → **Fan-out/Fan-in**
- Output needs independent validation at the task level → **Producer-Reviewer**
- Tasks span different domains needing different review lenses → **Expert Pool**
- None of the above, or default case → **Supervisor**

## The Patterns

### Supervisor

**Definition.** A central coordinator dispatches independent workers and collects their results. This is GIGO's default execution shape — like a research project lead delegating sub-studies and synthesizing findings when all reports are in.

**When to use.**
- Most common case — when no other pattern's shape clearly fits
- Work can be decomposed into independent tasks with no required sequencing beyond dependency order
- The lead needs to merge or interpret results after workers finish
- You're not sure which pattern fits (default to Supervisor, don't over-name)

**GIGO mapping.** Standard dependency graph with `parallelizable: true` where tasks don't share state. No special markers — this is how GIGO already works.

**Plan shape.**
```markdown
### Task 1: Setup

**blocks:** 2, 3
**blocked-by:** []
**parallelizable:** false

### Task 2: Worker A

**blocks:** 4
**blocked-by:** 1
**parallelizable:** true (with Task 3)

### Task 3: Worker B

**blocks:** 4
**blocked-by:** 1
**parallelizable:** true (with Task 2)

### Task 4: Collect and synthesize

**blocks:** []
**blocked-by:** 2, 3
**parallelizable:** false
```

**Gotchas.**
- Defaulting to Supervisor is correct. Naming a more specific pattern when Supervisor fits is pattern sprawl.

---

### Pipeline

**Definition.** Stages execute in strict linear order — each stage's output becomes the next stage's input. No stage can begin until its predecessor completes. Think of a research synthesis workflow: gather sources → extract key claims → synthesize findings → write the report.

**When to use.**
- Each step depends on the transformed output of the previous step, not just its completion
- Stages share state or a progressively refined artifact
- Parallelism would corrupt or bypass a required transformation step
- The work has a natural funnel shape where early stages reduce or transform the problem space

**GIGO mapping.** Every task has `parallelizable: false`. The `blocked-by` chain forms a strict linear sequence — each task lists only the immediately preceding task.

**Plan shape.**
```markdown
### Task 1: Gather sources

**blocks:** 2
**blocked-by:** []
**parallelizable:** false

### Task 2: Extract key claims

**blocks:** 3
**blocked-by:** 1
**parallelizable:** false

### Task 3: Synthesize findings

**blocks:** 4
**blocked-by:** 2
**parallelizable:** false

### Task 4: Write report

**blocks:** []
**blocked-by:** 3
**parallelizable:** false
```

**Gotchas.**
- False parallelism: tasks that look independent but share hidden state (a shared artifact, a config file, an upstream migration) are actually Pipeline. Mark them `parallelizable: false`.
- Skipping a stage because it "seems fast" creates invisible broken dependencies — a skipped extraction step means synthesis operates on raw, unprocessed material.

---

### Fan-out/Fan-in

**Definition.** A single coordinator fans work out to multiple parallel workers, each producing an independent artifact, then a dedicated merge task consolidates all artifacts into a coherent whole. Think of a multi-section report: each section drafted in parallel, then a synthesis pass integrates them.

**When to use.**
- Work naturally decomposes into independent parallel streams with no shared state
- Each stream produces a discrete artifact that can be combined later
- A consolidation step is required to produce coherent final output
- Speed matters and streams can genuinely run at the same time

**GIGO mapping.** Fan-out tasks have `parallelizable: true` and all share the same `blocked-by` prerequisite. The fan-in task has `blocked-by: [all fan-out task numbers]` and `parallelizable: false`.

**Plan shape.**
```markdown
### Task 1: Setup

**blocks:** 2, 3, 4
**blocked-by:** []
**parallelizable:** false

### Task 2: Draft Section A

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4)

### Task 3: Draft Section B

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 2, 4)

### Task 4: Draft Section C

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Tasks 2, 3)

### Task 5: Merge and synthesize

**blocks:** []
**blocked-by:** 2, 3, 4
**parallelizable:** false
```

**Gotchas.**
- Missing fan-in: fanning out without a named merge task produces disjointed output that never gets reconciled. If you fan out, name the fan-in task explicitly — it's structural, not optional.
- Treating the merge task as a "nice-to-have" optimization when it's doing real integration work. The merge task often carries significant cognitive load.

---

### Producer-Reviewer

**Definition.** A producer task generates an artifact; a separate reviewer task validates it independently; an optional revision task acts on the reviewer's feedback. This generalizes `gigo:verify`'s two-stage review to the task level inside a plan — useful when a specific task warrants its own review gate before the plan proceeds.

**When to use.**
- A task produces output with high stakes where errors are costly to fix later
- The task's output feeds many downstream tasks (failure amplifies)
- Independent validation is structurally required, not just "nice to check"
- The domain warrants a specialized review lens (fact-check, security audit, accessibility review)

**GIGO mapping.** Producer task runs first. Reviewer task has `blocked-by: [producer task number]`. Optional revision task has `blocked-by: [reviewer task number]`. All three are `parallelizable: false` with each other.

**Plan shape.**
```markdown
### Task 3: Draft content

**blocks:** 4
**blocked-by:** 2
**parallelizable:** false

### Task 4: Fact-check draft

**blocks:** 5
**blocked-by:** 3
**parallelizable:** false

### Task 5: Revise based on fact-check

**blocks:** 6
**blocked-by:** 4
**parallelizable:** false
```

**Gotchas.**
- Self-review: omitting the reviewer task because "the producer will check its own work" violates the separation that makes review effective. A producer reviewing its own output catches roughly the same errors it made writing it.

---

### Expert Pool

**Definition.** Tasks are tagged with domain-specific review lenses. Workers remain bare — the lens applied during review changes based on the task's domain tag. Like routing a mixed-domain plan through security review for auth tasks, UX review for interface tasks, and data review for analytics tasks — each review sees through the right lens without workers receiving persona context.

**When to use.**
- A plan contains tasks from meaningfully different domains (security-sensitive, UX-sensitive, data-sensitive)
- Each domain warrants a different review standard or checklist
- You want review quality to improve without compromising worker output quality
- The plan is large enough that a single review lens would miss domain-specific issues

**GIGO mapping.** Introduces an optional per-task field `review-lens: <domain>`. Workers remain bare — no persona context injection. This preserves the bare-worker research finding that workers without persona context produce better code. The `review-lens:` field is metadata-only in Cycle 1 — `gigo:verify` does not yet enforce it. The catalog documents the pattern so planners can start tagging; enforcement is a future verify enhancement.

**Plan shape.**
```markdown
### Task 1: Setup

**blocks:** 2, 3, 4
**blocked-by:** []
**parallelizable:** false
**review-lens:** (none — setup task)

### Task 2: Build authentication flow

**blocks:** 5
**blocked-by:** 1
**parallelizable:** false
**review-lens:** security

### Task 3: Design onboarding screens

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Task 4)
**review-lens:** ux

### Task 4: Implement analytics pipeline

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Task 3)
**review-lens:** data
```

**Gotchas.**
- Worker-level expert routing: injecting persona context into workers violates the bare-worker research finding. Expert Pool routes the review lens, not the worker context. Workers stay bare.

---

## Combining patterns

Multi-phase plans may declare a different pattern per phase. Use per-phase declarations under each phase heading:

```markdown
## Phase 1: Foundation

**Execution Pattern:** Pipeline

### Task 1: ...
### Task 2: ...

## Phase 2: Parallel Work

**Execution Pattern:** Fan-out/Fan-in

### Task 3: ...
```

The plan's top-level `**Execution Pattern:**` header names the dominant pattern or the first phase's pattern. When phases diverge significantly, per-phase declarations are the source of truth.

## Anti-patterns

### False parallelism

Marking tasks `parallelizable: true` when they share hidden state — a config file, an upstream artifact, a database migration. Usually a Pipeline masquerading as Fan-out. The plan looks faster on paper and breaks in practice.

### Missing fan-in

Dispatching parallel work with no consolidating merge task. Workers produce disjointed output that never gets reconciled. If you're fanning out, name the fan-in task explicitly.

### Self-review

Omitting the reviewer task in Producer-Reviewer because "the producer will check its own work." Violates the separation that makes review effective. A producer reviewing its own work catches roughly the same mistakes it made writing it.

### Worker-level expert routing

Injecting persona context into workers for "expert execution." Violates the bare-worker research finding that workers without persona context produce better code. Expert Pool routes the review lens, not the worker context.

### Pattern sprawl

Declaring a named pattern when Supervisor would do. Supervisor is the default — name another pattern only when its shape is genuinely different. Over-naming adds noise and confuses reviewers.
