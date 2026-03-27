# Code Review: Worker Pool Implementation

**File under review:** `scheduler` package (worker pool)
**Verdict:** Not production-ready. Six bugs that will cause incorrect behavior or data corruption; four missing pieces that are required before shipping.

---

## Bugs

### 1. Error from `store.List()` is silently discarded

```go
tasks, _ := p.store.List()
```

The blank identifier swallows the error entirely. If the store fails to read — database unavailable, file corruption, permissions error — `tasks` will be `nil` and `Run` returns `nil`, signaling success. The caller has no way to distinguish "nothing to run" from "failed to load tasks."

**Fix:**
```go
tasks, err := p.store.List()
if err != nil {
    return fmt.Errorf("loading tasks: %w", err)
}
```

---

### 2. Mutation of shared task state without synchronization

```go
t.State = "running"
p.store.Update(t)
```

Each goroutine receives a `*Task` pointer. If the store's `List()` returns pointers into an internal map or slice (a common implementation), multiple goroutines writing to `t.State` concurrently is a data race. `go test -race` will catch this. Even if the store copies on `List()`, the goroutine is mutating the struct before the store sees it — bypassing any CAS protection the store might have.

**Fix:** Never mutate a task pointer in place. Build a transition request and let the store own the state change:
```go
if err := p.store.Transition(t.ID, "ready", "running"); err != nil {
    // another worker claimed it — skip
    return
}
```

The `Store` interface as written lacks `Transition()` with compare-and-swap semantics. That is both a bug here and a missing piece addressed below.

---

### 3. Context cancellation is completely ignored

```go
func (p *Pool) Run(ctx context.Context) error {
```

`ctx` is accepted but never checked. If the caller cancels — `SIGINT`, timeout, parent context expiry — the pool continues launching and executing tasks as if nothing happened. Workers will block on `sem <- struct{}{}` indefinitely if all slots are full and no task completes.

**Fix:** Select on ctx.Done() when acquiring the semaphore, and pass ctx into execute:
```go
select {
case sem <- struct{}{}:
case <-ctx.Done():
    break // stop launching new tasks
}
```

And propagate to execute:
```go
func (p *Pool) execute(ctx context.Context, t *Task) error
```

---

### 4. Tasks launched after context cancel, then `wg.Wait()` hangs

Even after adding the select above, tasks that were already launched continue running after context cancellation. `wg.Wait()` will block until every in-flight task finishes regardless of how long they take. For a task running `t.Cmd` (a shell command), that could be minutes.

**Fix:** execute must respect context cancellation — pass ctx to exec.CommandContext, not exec.Command.

---

### 5. `store.Update()` errors are silently ignored — twice

```go
p.store.Update(t)  // transition to "running" — error ignored
// ...
p.store.Update(t)  // transition to "done"/"failed" — error ignored
```

If the first `Update` fails, the task's state was never persisted as `running`. The store still thinks it's `ready`. The task executes anyway, and if it succeeds, the store transitions directly from `ready` to `done` — which may violate the store's CAS invariants. If the second `Update` fails, the task ran to completion but remains `ready` in the store. On the next `Run()`, it executes again.

**Fix:** Check every `Update` / `Transition` return value. On failure to mark `running`, abort the goroutine. On failure to mark `done`/`failed`, retry with backoff or log at ERROR — not silently continue.

---

### 6. No crash recovery for tasks left in `running` state

`Run()` marks tasks as `running` then executes them. If the process crashes mid-execution, those tasks are permanently stuck in `running` on the next startup. `Run()` filters for `State == "ready"` only, so they will never execute again.

**Fix:** On startup (in `NewPool` or a separate `Recover()` call), scan for tasks in `running` state and transition them back to `ready`. Per the project spec:
```
On startup, scan for tasks in `running` state. Transition back to `ready` for re-execution.
```
This is specified but not implemented.

---

## Missing Pieces

### M1. No dependency resolution (DAG)

`Task.Deps []string` is declared but `Run()` never reads it. Tasks with unresolved dependencies execute immediately. If task B depends on task A, and both are `ready`, they may run concurrently or B may run before A finishes.

This is not a minor omission. It is the core scheduling requirement stated in the project spec. Before scheduling a task, every dep in `t.Deps` must be in `done` state.

---

### M2. Store interface lacks `Transition()` with CAS semantics

The current interface:
```go
Update(task *Task) error
```

This is a blind overwrite. Two goroutines can both read a task as `ready`, both call `Update` with `State = "running"`, and the store will accept both — the task runs twice. Without atomic compare-and-swap, the entire concurrency model is broken.

Required:
```go
Transition(id string, from, to State) error  // returns error if current != from
```

Without this, every concurrent state mutation is a potential double-execution or state corruption.

---

### M3. No retry logic — supervisor never decides

Per the project's supervision strategy: "The supervisor decides — the worker never decides its own fate." Currently the pool logs the error and marks the task `failed`. There is no retry counter, no retry policy, no distinction between transient failures (retry) and permanent failures (abort). A network blip kills a task permanently.

Minimum required: `Task.Retries int` and `Task.MaxRetries int`. The supervisor checks retries remaining before marking `failed`.

---

### M4. `execute()` doesn't run `t.Cmd`

```go
func (p *Pool) execute(t *Task) error {
    fmt.Printf("running: %s\n", t.Name)
    return nil
}
```

The method prints the task name and returns nil. `Task.Cmd` — the actual command to execute — is never used. This is a stub, not an implementation. In a code review context this would be marked as a known gap; in a production context it means the tool does nothing.

---

## Summary

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `store.List()` error swallowed | Critical | Silent failure — returns success on storage error |
| 2 | Shared pointer mutation, no CAS | Critical | Data race, double-execution of tasks |
| 3 | Context cancellation ignored | High | Process won't stop cleanly; goroutine leak risk |
| 4 | `wg.Wait()` ignores cancellation deadline | High | Shutdown hangs indefinitely |
| 5 | `store.Update()` errors ignored (x2) | High | Tasks re-run on next startup; state corruption |
| 6 | No crash recovery for `running` tasks | High | Tasks permanently stuck after crash |
| M1 | Dependency resolution not implemented | Critical | Core requirement missing |
| M2 | No CAS in Store interface | Critical | Concurrent double-execution guaranteed |
| M3 | No retry logic | Medium | All transient failures are permanent |
| M4 | `execute()` is a stub | Critical | Tool does nothing |

**Minimum before shipping:** Fix bugs 1, 2, 3, 5 and implement M1, M2. The remaining items (4, 6, M3, M4) are required for a complete implementation but the above six would make the tool actively harmful to ship as-is — it will silently misreport success, double-execute tasks under concurrency, and corrupt state on any store error.
