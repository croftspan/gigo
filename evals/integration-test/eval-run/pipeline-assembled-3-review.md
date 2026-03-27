# Code Review — tq add Implementation

**Reviewer:** Mirror (Quality Auditor)
**Scope:** store/task.go, store/store.go, cmd/root.go, cmd/add.go, main.go
**Standard applied:** tq project quality standards (spec compliance, correctness, output discipline, atomicity, cycle detection placement)

---

## Summary

The implementation is structurally sound and hits most of the spec requirements cleanly. The atomic write pattern is correct, cycle detection is placed correctly, and the output discipline (ID to stdout, errors to stderr) is followed. There are, however, six concrete issues ranging from a real bug to missing spec features.

---

## Issues

### 1. RACE CONDITION — validate-then-add is not atomic (HIGH)

**Location:** `cmd/add.go`, `runAdd` → `validateDependenciesExist` then `taskStore.Add`

**Problem:** `validateDependenciesExist` reads the store to check that dependency IDs exist. Then `taskStore.Add` writes to the store. Between those two calls, another process could delete one of the dependency tasks. The task would be added with a dangling dependency reference — the dependency ID is stored in `DependsOn` but the referenced task no longer exists. When the scheduler later tries to walk the dependency graph to promote the task to `ready`, it will find a ghost ID.

This is not hypothetical in a multi-user or scripted scenario: `tq delete <dep-id>` in a concurrent shell is enough to trigger it.

**Fix:** Move the dependency-existence check inside `Store.Add`, under the same mutex lock as the cycle detection. Both checks read the task list; they should share one read-and-lock, not two.

```go
func (fs *FileStore) Add(task Task) error {
    fs.mu.Lock()
    defer fs.mu.Unlock()

    tasks, err := fs.load()
    if err != nil {
        return err
    }
    // Duplicate check
    for _, t := range tasks {
        if t.ID == task.ID {
            return fmt.Errorf("%w: %s", ErrDuplicate, task.ID)
        }
    }
    // Dependency existence check — same lock, no TOCTOU window
    if err := validateDepsExist(tasks, task.DependsOn); err != nil {
        return err
    }
    // Cycle check
    if err := detectCycle(tasks, task); err != nil {
        return err
    }
    tasks = append(tasks, task)
    return fs.write(tasks)
}
```

The CLI layer can then remove `validateDependenciesExist` entirely, or keep it as a fast pre-flight that surfaces friendly error messages before the lock is acquired — but must not rely on it for correctness.

---

### 2. BUG — Cycle detection only walks from newTask.ID (MEDIUM)

**Location:** `store/store.go`, `detectCycle`

**Problem:** The DFS starts only from `newTask.ID`. It does not run DFS from every node in the graph. This means an indirect cycle introduced by the new task may be missed if the cycle path does not pass through `newTask.ID` as its starting point — but more importantly, it misses an edge case: if adding the new task creates a cycle that is only reachable from an *existing* node that was not previously part of a cycle.

Consider: tasks A → B and adding C → A, where B → C already exists in the graph (added via an earlier valid Add that didn't form a cycle at the time). The cycle is A → B → C → A. Starting DFS only from C would walk C → A → B → C and find it. This specific case is actually caught. However, the implementation only calls `dfs(newTask.ID)` — if the new task's own DFS does not reach back to itself, no cycle is reported.

Actually, on careful reading: the correct DFS for "does adding this edge create a cycle" is to check whether any dependency of `newTask` can reach `newTask.ID` through the existing graph. The implementation adds `newTask.ID` to the graph first, then runs DFS from `newTask.ID`. This will catch self-referential cycles and direct mutual cycles. But it will NOT catch a cycle introduced when:

- existing task A depends on B
- new task B depends on A  (this is the new task being added)

Walkthrough: graph becomes `{A: [B], B: [A]}`. DFS from B visits A, then tries to visit B — finds `inStack[B]=true` → cycle detected. OK, this is caught.

The real gap: the `visited` map is shared across all calls but `inStack` resets per DFS traversal path (via the `inStack[id] = false` backtrack). If DFS is only called from one starting point, and there are disconnected subgraphs, cycles in those subgraphs that existed before this add go undetected — but that is not this function's job (they should have been caught at their own add time). The single-entry DFS from `newTask.ID` is actually correct for the stated invariant: "would adding this task create a new cycle?" provided the existing graph was cycle-free before this call (which the store enforces). The design note stands: this is acceptable.

**Corrected assessment:** The cycle detection logic is correct given the invariant. Withdraw the concern. No bug here.

---

### 3. SPEC VIOLATION — List does not sort by priority desc, created_at asc (MEDIUM)

**Location:** `store/store.go`, `FileStore.List`

**Problem:** The `Store` interface comment specifies: "ordered by priority desc, created_at asc." The `List` implementation returns tasks in file-storage order (insertion order). No sorting is performed.

This matters now for any caller relying on `List` for scheduling decisions (e.g., picking the next `ready` task to claim). A scheduler calling `List(Filter{State: []State{StateReady}})` and taking `result[0]` will get the oldest-inserted ready task, not the highest-priority one.

**Fix:** Sort the result slice before returning it.

```go
import "sort"

// After filtering:
sort.Slice(out, func(i, j int) bool {
    if out[i].Priority != out[j].Priority {
        return out[i].Priority > out[j].Priority // desc
    }
    return out[i].CreatedAt.Before(out[j].CreatedAt) // asc
})
```

This applies whether the filter is active or not (the no-filter path returns early without sorting at all — same bug).

---

### 4. SPEC VIOLATION — Filter.Priority field is ignored (MEDIUM)

**Location:** `store/store.go`, `FileStore.List`

**Problem:** `Filter` has a `Priority *int` field. The implementation never reads it. Any caller setting `filter.Priority` gets back tasks of all priorities, silently.

**Fix:** Add the filter:

```go
if filter.Priority != nil && t.Priority != *filter.Priority {
    continue
}
```

---

### 5. SPEC VIOLATION — Filter.Limit field is ignored (MEDIUM)

**Location:** `store/store.go`, `FileStore.List`

**Problem:** `Filter` has a `Limit int` field. The implementation never reads it. A caller expecting at most N results gets all matching tasks. For large stores this wastes memory and produces incorrect scheduler behavior.

**Fix:** After sorting, apply the limit:

```go
if filter.Limit > 0 && len(out) > filter.Limit {
    out = out[:filter.Limit]
}
```

Note: Limit must be applied *after* sorting so the caller gets the top-N by priority, not an arbitrary N.

---

### 6. MISSING — No --json flag on `tq add` (LOW)

**Location:** `cmd/add.go`

**Problem:** The project standard states "every command produces grep-friendly text by default and structured JSON with `--json`." The `add` command has no `--json` flag. On success, the plain-text output is just the bare ID (which is pipe-friendly), but there is no way to get a JSON envelope like `{"id": "a1b2c3d4", "state": "ready"}` for callers that need it.

This is a missing feature, not a bug, but it is a stated spec requirement.

**Fix:** Add a `--json` flag that wraps the output:

```go
var addJSON bool
addCmd.Flags().BoolVar(&addJSON, "json", false, "output result as JSON")

// In runAdd, on success:
if addJSON {
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    return enc.Encode(task)
}
fmt.Println(task.ID)
```

---

### 7. CORRECTNESS — `write(nil)` initializes the file with JSON `null` (LOW)

**Location:** `store/store.go`, `NewFileStore`

**Problem:** When creating a new store file, `fs.write(nil)` is called. `json.MarshalIndent(nil, ...)` produces `null`. The `load` function handles an empty file (returns nil), but if the file contains `null`, `json.Unmarshal` into `*[]Task` sets the pointer to nil — which is fine — but the `len(data) == 0` guard will not trigger (data is `"null"`, 4 bytes). `json.Unmarshal([]byte("null"), &tasks)` sets `tasks` to nil, which is correct behavior. So this works but it is fragile: the explicit empty-check is misleading because `null` is not an empty file.

**Fix:** Initialize with an empty array instead of null:

```go
// Change write(nil) to write([]Task{})
if err := fs.write([]Task{}); err != nil {
```

`json.MarshalIndent([]Task{}, ...)` produces `[]`, not `null`. More importantly, `load` will then return an empty slice, and the `len(data) == 0` guard can be removed entirely because `[]` is valid JSON that will unmarshal cleanly.

---

### 8. CORRECTNESS — `MaxRetries` is never set by `tq add` (LOW)

**Location:** `cmd/add.go`, `runAdd`

**Problem:** The `Task` struct has `MaxRetries int`. The `add` command does not expose a `--max-retries` flag and constructs the task with `MaxRetries: 0` (the zero value). A task with `MaxRetries: 0` that fails will have `Retries < MaxRetries` evaluate as `0 < 0` → false, meaning it immediately transitions to `dead` with zero retry attempts.

This may be intentional if the spec says retries default to zero (fail-fast). But the field exists, and the state machine has `StateFailed` ("failed, retries remain") which implies at least one retry is possible. Without a `--max-retries` flag, `StateFailed` is unreachable in practice — every failed task goes straight to `dead`.

**Fix:** Either add `--max-retries` flag to `tq add`, or document that zero retries is intentional and remove `StateFailed` from the spec. If the worker pool will set `MaxRetries` at claim time rather than at enqueue time, document that and remove the field from the `Task` struct (or at least from the `add` command's responsibility).

---

## What Works Well

- Atomic write (temp + rename) is correctly implemented. The crash-safety guarantee holds.
- Cycle detection is in `Store.Add`, not in the command layer. Any caller gets the guarantee. The DFS is correct.
- Sentinel errors use `errors.New` and callers use `errors.Is`. No string comparison anywhere.
- Output discipline is correct: ID to stdout, errors to stderr via Cobra.
- Error message format matches the convention (`tq: cannot add task "<name>": <reason>`).
- `validateDependenciesExist` accumulates all missing IDs before returning — one error, not N errors.
- `generateID` uses `crypto/rand`, not `math/rand`. Correct for a tool where IDs appear in scripts.
- No CGO, no external runtime, single binary. `go.mod` has only Cobra as a direct dep.
- `PersistentPreRunE` cleanly separates store setup from command logic. Subcommands are testable in isolation.

---

## Priority Order for Fixes

1. **RACE CONDITION** — Move dep-existence check inside `Store.Add` (correctness, data integrity)
2. **List not sorted** — Scheduler picks wrong task (spec violation, functional impact)
3. **Filter.Priority ignored** — Silently wrong behavior (spec violation)
4. **Filter.Limit ignored** — Silently wrong behavior (spec violation)
5. **MaxRetries=0 makes StateFailed unreachable** — Design clarification needed
6. **write(nil) → null** — Fragile but currently works; low urgency
7. **--json missing** — Feature gap, not a bug
