# Production Readiness Review: Worker Pool Implementation

**File reviewed:** `scheduler/pool.go` (inferred)
**Date:** 2026-03-27
**Verdict:** Not production-ready. Multiple correctness bugs, missing error handling, and structural gaps that would cause silent data loss and incorrect behavior under real workloads.

---

## Critical Bugs

### 1. Error from `store.List()` is silently swallowed

**Location:** `Run()`, line ~33

```go
tasks, _ := p.store.List()
```

The blank identifier discards the error. If the store is unavailable, returns a partial result, or fails for any reason, `tasks` will be `nil` and the pool will silently process nothing — no log, no returned error, no signal to the caller that anything went wrong.

**Impact:** Silent no-op on store failure. The caller sees a successful return from `Run()` while zero tasks were executed. This is the worst failure mode: invisible.

**Fix:**
```go
tasks, err := p.store.List()
if err != nil {
    return fmt.Errorf("listing tasks: %w", err)
}
```

---

### 2. `context.Context` is accepted but never respected

**Location:** `Run()` signature and body

```go
func (p *Pool) Run(ctx context.Context) error {
```

The context is accepted but never passed to goroutines, never checked for cancellation or deadline, and never threaded into `execute()`. This means:

- Cancellation signals (from HTTP request timeouts, `os.Signal` handlers, `context.WithTimeout`) are completely ignored.
- A shutdown signal during a long task run cannot stop the pool.
- The goroutines will run to completion regardless of the caller's intent.

**Impact:** The pool cannot be gracefully shut down. Any caller expecting context propagation — including virtually all production orchestrators — will be broken.

**Fix:** Thread `ctx` through `execute()`, select on `ctx.Done()` in the semaphore acquire, and propagate the context to any real command execution:

```go
// Semaphore acquire with cancellation support
select {
case sem <- struct{}{}:
case <-ctx.Done():
    return ctx.Err()
}

// Pass context into execute
err := p.execute(ctx, t)
```

---

### 3. Race condition on task state mutation

**Location:** goroutine closure in `Run()`, lines ~44-58

```go
t.State = "running"
p.store.Update(t)
```

Multiple goroutines mutate `t.State` concurrently on the same `*Task` pointer without any synchronization. Go's race detector will flag this. The `Task` struct is passed by pointer; concurrent writes to `t.State` from different goroutines are a data race.

**Impact:** Undefined behavior. Under the race detector this panics. In production this produces corrupted state values silently.

**Fix options:**
- Make a per-goroutine copy of the task before mutating it: `task := *t; task.State = "running"` (value copy, not pointer).
- Or protect all mutations with a mutex (but a copy is simpler and avoids contention).

```go
go func(t Task) {  // pass by value, not pointer
    defer wg.Done()
    defer func() { <-sem }()

    t.State = "running"
    p.store.Update(&t)
    // ...
}(*task)  // dereference here
```

---

### 4. `store.Update()` errors are silently discarded

**Location:** goroutine body, lines ~45 and ~52-55

```go
p.store.Update(t)
// ...
p.store.Update(t)
```

Both `Update` calls ignore return values. If the store fails to persist the state transition, the task will appear stuck in its prior state with no indication of failure. This is especially bad for the `"done"` transition — completed work becomes invisible.

**Impact:** Silent persistence failures. Operators cannot distinguish "task ran and state was saved" from "task ran but we lost the record."

**Fix:**
```go
if err := p.store.Update(t); err != nil {
    log.Printf("failed to update task %s to running: %v", t.ID, err)
}
```

---

## Design Issues

### 5. Dependency field exists but dependency resolution is absent

**Location:** `Task.Deps []string` field; `Run()` ignores it entirely

The `Task` struct declares a `Deps` field, which implies the system is designed to handle tasks with prerequisites. The `Run()` method completely ignores it — tasks with unresolved dependencies will be dispatched if their state happens to be `"ready"`, and tasks that should be ready won't be until their dependencies complete.

**Impact:** Incorrect execution order. Dependent tasks may run before their prerequisites, producing wrong results or panics depending on what the commands actually do.

**Fix:** Before dispatching a task, verify all dependency IDs are in `"done"` state:

```go
func (p *Pool) depsComplete(deps []string) (bool, error) {
    for _, id := range deps {
        dep, err := p.store.Get(id)
        if err != nil {
            return false, fmt.Errorf("getting dep %s: %w", id, err)
        }
        if dep.State != "done" {
            return false, nil
        }
    }
    return true, nil
}
```

Then filter in the dispatch loop. Note that a single-pass loop cannot handle multi-level dependency graphs — a proper solution requires topological ordering (Kahn's algorithm) or iterative re-queuing until the graph drains.

---

### 6. `Priority` field is declared but has no effect

**Location:** `Task.Priority int`; `Run()` iterates tasks in whatever order `store.List()` returns them

The field exists but is never used. If priorities are meaningful to the operator (higher-priority tasks should run first), this is a silent correctness gap.

**Fix:** Sort tasks by priority before dispatch, or use a priority queue:

```go
sort.Slice(tasks, func(i, j int) bool {
    return tasks[i].Priority > tasks[j].Priority
})
```

If priority is vestigial and the field was included by mistake, remove it — dead fields in a struct add confusion.

---

### 7. Task state is a stringly-typed enum with no validation

**Location:** `Task.State string`; used throughout as `"pending"`, `"ready"`, `"running"`, `"done"`, `"failed"`

String constants for state values invite typos, make exhaustive case checking impossible, and produce no compiler errors on invalid transitions. A state of `"runnng"` would silently behave as an unknown state.

**Fix:** Define a typed constant set:

```go
type TaskState string

const (
    StatePending TaskState = "pending"
    StateReady   TaskState = "ready"
    StateRunning TaskState = "running"
    StateDone    TaskState = "done"
    StateFailed  TaskState = "failed"
)
```

Change `Task.State` to `TaskState`. This doesn't add runtime validation automatically, but it makes invalid values visible at compile time and enables exhaustive switch coverage.

---

### 8. `Pool.mu` is declared but never used

**Location:** `Pool` struct, `mu sync.Mutex`

The mutex is defined on the struct but never locked or unlocked anywhere in the code. This is either a forgotten synchronization point (a bug) or dead code (confusion risk). Either way it should be resolved — dead fields in concurrent code are a red flag during review.

---

### 9. `execute()` is a stub that prints to stdout

**Location:** `execute()`, line ~61

```go
func (p *Pool) execute(t *Task) error {
    fmt.Printf("running: %s\n", t.Name)
    return nil
}
```

This is a placeholder. In production, this function would need to:
- Execute `t.Cmd` as a real shell command or structured invocation.
- Capture stdout/stderr for logging or storage.
- Propagate the context for cancellation.
- Handle exit codes and timeouts.
- Sanitize `t.Cmd` — unsanitized shell execution is an injection vector.

**Impact:** The pool cannot actually run anything. This is not a bug per se, but shipping a stub as production infrastructure means the only production behavior is printing to stdout and returning nil, which causes every task to be marked `"done"` regardless of actual execution.

---

## Missing Pieces

### 10. No retry logic

Tasks that fail go directly to `"failed"` with no retry. For transient errors (network timeouts, resource contention), this produces permanent failures. A production pool should support at least configurable retry with backoff.

### 11. No observability hooks

There is no metrics emission, no structured logging, and no tracing integration. In production you need to know: how many tasks are queued, running, failed; what the p99 execution time is; which tasks are stuck. The `log.Printf` on failure is the only signal.

### 12. No backpressure on `store.List()` at startup

If `store.List()` returns 10,000 tasks, all 10,000 are held in memory simultaneously before dispatch begins. A streaming or paginated approach would be more appropriate for large task sets.

### 13. No test coverage

There are no tests. For concurrent infrastructure, tests should cover: the semaphore limiting concurrency, context cancellation stopping the run, error propagation from the store, and the race detector (`go test -race`) finding no issues.

### 14. No graceful shutdown or draining

`wg.Wait()` blocks until all in-flight goroutines complete, but there is no mechanism to stop accepting new work or to signal that the pool is shutting down. If the pool is embedded in a larger service, a clean shutdown sequence matters.

---

## Summary

| Category | Issue | Severity |
|---|---|---|
| Bug | `store.List()` error discarded | Critical |
| Bug | Context ignored — no cancellation | Critical |
| Bug | Data race on `*Task` mutation | Critical |
| Bug | `store.Update()` errors discarded | High |
| Design | Dependencies declared but not enforced | High |
| Design | Priority declared but not used | Medium |
| Design | Stringly-typed state with no validation | Medium |
| Design | `mu` declared but never used | Medium |
| Incomplete | `execute()` is a stub | High |
| Missing | No retry logic | Medium |
| Missing | No observability | Medium |
| Missing | No test coverage | High |
| Missing | No graceful shutdown | Medium |

**Before shipping:** fix the three data-race and error-handling bugs, thread the context, implement real dependency resolution, and write tests with `-race`. Everything else is important but not a blocker for correctness.
