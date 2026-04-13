# Brief: Orchestrator Loop

## The Problem

The full pipeline — Opus plans, Gemma executes, Opus/Codex reviews — currently requires the operator to invoke each skill manually: `/blueprint` → `/spec` → `/execute` → `/verify`. Each handoff is a conversation turn. The operator is the orchestrator. That's fine for supervised work but the goal is autonomous execution: queue up work, walk away, come back to reviewed code.

## What We Know

### Architecture (validated through Gemma eval)

```
Opus (Claude Code)          Gemma 4 (local)           Opus/Codex (reviewer)
─────────────────          ──────────────            ─────────────────────
/blueprint                  ↓                         /verify (spec review)
/spec ──────────────→ execute tasks ──────────→ /verify (craft review)
                            ↑         ↓
                        harness    code output
                      (system     (code blocks
                       prompt)     parsed → files)
```

### What's Proven

- **Gemma executes, doesn't propose** — 100% EXECUTES with tuned harness at temp 1.0
- **26B-A4B: 16s/task, 31B: 107s/task** — speed vs judgment tradeoff
- **Workers run bare** — GIGO's existing model. Workers get task spec, not full assembly. Maps directly to Gemma's single-prompt execution.
- **Two-stage review catches real issues** — spec compliance + craft quality, different reviewers for different things. Combining them loses signal.
- **Features 1-4 enhance Opus** — boundary-mismatch detection, execution patterns, phase matrix all make planning and review sharper. Gemma doesn't need them.

### The Orchestrator Project

Exists at `~/projects/gigo-orchestrator`. Team: Archi (system architect), Ctx (context engineer), Bolt (implementation). Assembled via GIGO. Ready for planning.

### Hermes Agent Framework

Target framework for the orchestration loop. Provides:
- Agent definitions with tool schemas
- Message routing between agents
- State management across turns
- Tool use (file I/O, shell commands, API calls)

This is what lets Gemma's text output become actual file writes and test runs.

## What to Build

### The Loop

```
1. PLAN    → Opus reads the spec, breaks into tasks, assigns execution order
2. EXECUTE → For each task:
               a. Format task as Gemma prompt (brief 08)
               b. Send to local model with harness (brief 06)
               c. Parse response → extract code blocks with file paths
               d. Write files to disk (or worktree for isolation)
               e. Run tests/linting if applicable
               f. If tests fail → re-prompt Gemma with error output (max 2 retries)
               g. If still failing → escalate to Opus
3. REVIEW  → Opus/Codex reviews the completed work:
               a. Spec compliance (did the worker build what the plan said?)
               b. Craft quality (is the work well-built?)
               c. If issues found → route back to step 2 with fix instructions
4. REPORT  → Summary of what was built, what was reviewed, what needs attention
```

### Key Design Decisions

**Worktree isolation:** Each task (or task group) executes in a git worktree. If the task fails review, the worktree is discarded. If it passes, changes merge to the working branch. GIGO already has worktree isolation docs at `.claude/references/worktree-isolation.md`.

**Retry budget:** Gemma gets 2 retries per task (re-prompt with error). After that, the task escalates to Opus. This bounds the cost of Gemma failures without falling back to Opus for every hiccup.

**Review model selection:** Codex 5.4 Pro if budget allows (different model = different perspective). Opus as fallback. Never Gemma reviewing Gemma — the reviewer must be stronger than the executor.

**Parallelism:** Tasks without dependencies execute in parallel (multiple Gemma prompts). Tasks with dependencies execute sequentially. The execution pattern catalog (Feature 3) already defines these patterns: Pipeline, Fan-out/Fan-in, Producer-Reviewer.

**State persistence:** The orchestrator maintains a run log — which tasks completed, which are pending, which failed. If the process crashes, it resumes from the last completed task, not from scratch.

### Components

1. **Task queue** — reads the plan, builds a dependency graph, yields tasks in executable order
2. **Prompt formatter** — takes a task + relevant source files → Gemma-compatible prompt (brief 08)
3. **Local executor** — sends prompt to llama-server, receives response, parses code blocks (brief 07)
4. **File applier** — takes parsed code blocks → writes files to worktree
5. **Test runner** — runs project tests after each task, captures output for retry/review
6. **Review dispatcher** — sends completed work to Opus/Codex for two-stage review
7. **State manager** — tracks progress, handles resume, produces final report

### Testing Required

**End-to-end pipeline test:**
- Take a completed `gigo:spec` plan (Rails API fixture, 5 tasks)
- Run the full loop: plan → execute (Gemma) → review (Opus)
- Compare output to the same plan executed via Claude subagents
- Measure: total time, total cost (Opus tokens), spec compliance, code quality

**Failure handling test:**
- Seed a task that will fail (e.g., references a nonexistent table)
- Verify: Gemma retries with error context, escalates after 2 failures
- Verify: worktree isolation prevents failed tasks from polluting the working branch

**Parallelism test:**
- Plan with 3 independent tasks
- Verify they execute concurrently (3 Gemma prompts in flight)
- Verify they don't interfere (separate worktrees or file locks)

**Resume test:**
- Start a 5-task plan, kill the orchestrator after task 3
- Restart — verify it resumes from task 4, doesn't re-execute 1-3

**Cost comparison:**
- Same plan, full Opus execution vs Opus+Gemma hybrid
- Measure Opus token usage: planning + review only vs planning + execution + review
- Hypothesis: 60-80% token reduction with comparable output quality

**What could go wrong:**
- Gemma generates code that compiles but is logically wrong — review catches it but the retry loop costs time
- Worktree merges conflict when parallel tasks touch adjacent files
- llama-server OOMs on large context (many inline source files)
- The orchestrator itself is more complex than the work it's orchestrating (for small tasks)
- Hermes framework has limitations we haven't discovered yet

## Dependencies

- Needs Gemma harness generator (brief 06) — what Gemma receives as system prompt
- Needs model routing (brief 07) — the local execution path
- Needs spec-to-prompt formatting (brief 08) — how tasks become prompts
- Orchestrator project already assembled at `~/projects/gigo-orchestrator`
- Hermes agent framework (research and integration needed)

## Scope Check

This is the biggest brief in the series. It might need decomposition:
- Phase 1: Single-task execution loop (plan → execute one task → review)
- Phase 2: Multi-task sequential execution
- Phase 3: Parallel execution with worktree isolation
- Phase 4: Resume, state persistence, cost tracking
