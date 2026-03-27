# tq add — Code Review

## Summary

The implementation is solid for a first pass. The architecture decisions are mostly correct: cycle detection at enqueue, atomic writes via temp+rename, sentinel errors with `errors.Is`, pipe-friendly output. However there are several real bugs and a handful of spec-compliance gaps that need addressing before this is production-ready.

---

## Bugs

### 1. `write(nil)` marshals `null`, not `[]` — breaks `load()` on the next open

**store/store.go:129, 143–145**

`NewFileStore` calls `fs.write(nil)` to initialise an empty store. `json.MarshalIndent(nil, ...)` produces the literal bytes `null`, not `[]`. On the next open, `load()` checks `len(data) == 0` — that check is false for `null` (4 bytes), so it falls through to `json.Unmarshal`. `json.Unmarshal([]byte("null"), &tasks)` succeeds and leaves `tasks` as `nil`, which is harmless — but only by accident. The intent is an empty array, and any code that later does `json.Unmarshal` on a file expecting an array and gets `null` is a silent mismatch.

Fix: initialise with an explicit empty slice.

```go
if err := fs.write([]Task{}); err != nil { ... }
```

And in `write`, guard against the nil case:

```go
func (fs *FileStore) write(tasks []Task) error {
    if tasks == nil {
        tasks = []Task{}
    }
    ...
}
```

---

### 2. `write` does not `fsync` — atomic rename is not crash-safe on Linux/ext4

**store/store.go:162–168**

The design notes claim this satisfies the State Guardian's quality bar ("a crash mid-write leaves either the old file or the new file complete"). This is true for `rename(2)` itself, but `os.WriteFile` does not call `fsync` before rename. On Linux with ext4 (and many other filesystems), the kernel may reorder writes: the rename can land in the journal before the data pages are flushed. A power failure at that moment produces the new filename pointing at a file with zero or partial content.

The correct sequence is: write → `f.Sync()` → close → rename.

```go
f, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o644)
if err != nil { ... }
if _, err := f.Write(data); err != nil { f.Close(); ... }
if err := f.Sync(); err != nil { f.Close(); ... }
if err := f.Close(); err != nil { ... }
if err := os.Rename(tmp, fs.path); err != nil { ... }
```

Without `Sync`, the durability claim in the design notes is false. This matters most on servers and CI runners; macOS HFS+/APFS is more forgiving, but the code should be correct on all POSIX targets.

---

### 3. `detectCycle` explores the full graph from `newTask.ID`, not from existing roots — misses some cycles

**store/store.go:294–327**

The DFS is seeded only from `newTask.ID`. Consider:

```
existing: A → B → C
new task: D → C
```

No cycle here — correct. But consider:

```
existing: A → (nothing), B → A
new task: C — depends on B
```

Still fine. Now the tricky case:

```
new task: X — depends on X (self-loop)
```

DFS starts at X, sees dep X, recurses — X is in `inStack`, returns true. Correctly caught.

Now:

```
existing: A → B
new task: B — depends on A   (B already exists)
```

Wait — `Add` would catch the `ErrDuplicate` check before reaching `detectCycle`, so B can't be re-added. Self-loops and transitive cycles through the new node are correctly caught by this DFS.

However there is a subtler gap: the DFS only runs `dfs(newTask.ID)`. If an existing task is already part of a cycle that was smuggled in (e.g., through a bug or direct store manipulation), this won't be caught. That's a secondary concern — the primary path is correct.

**Actual bug:** The DFS traverses `graph[id]` which maps to `DependsOn`. `DependsOn` entries are IDs of tasks this task *depends on*. A dependency edge A→B means "A needs B to finish first." The cycle the code finds is when following dependency pointers leads back to `newTask.ID`. This is correct — if you can reach X from X by following dependency edges, there is a cycle. No bug here on direction.

**Real issue found:** `dfs` only starts from `newTask.ID`. If the new task has no dependency on itself but creates a cycle in the existing graph through an indirect path, that cycle already existed (a pre-existing bug) and would not be newly introduced by this add. So the guard is correct: we only need to check whether `newTask` introduces a cycle. This is fine.

Marking this section: **no cycle-detection bug confirmed**. The earlier concern was unfounded after tracing through the logic.

---

### 4. `validateDependenciesExist` is not atomic with `Add` — TOCTOU window

**cmd/add.go:457–459**

`validateDependenciesExist` calls `s.Get` for each dep, then `taskStore.Add` is called. Between those two calls, a concurrent `tq cancel` or `tq delete` could remove a dependency. The task would then be added with a `DependsOn` entry pointing at a deleted task ID.

This matters for correctness: the scheduler's `Tick` that promotes tasks from `pending` to `ready` will check whether all deps are `done`. If a dep no longer exists, the check fails silently and the task stays pending forever.

Mitigation options (from simplest to most correct):
- Accept the race (document the assumption of single-writer use).
- Re-validate inside `Store.Add` before persisting (already holds the lock).
- The current code validates then trusts — at minimum, `Add` should re-check dep existence under the lock.

For a local single-user CLI this is low risk, but it should be called out.

---

### 5. `generateID` collision produces `ErrDuplicate` with a confusing error message

**cmd/add.go:489–492**

```go
if errors.Is(err, store.ErrDuplicate) {
    return fmt.Errorf("tq: cannot add task %q: ID %s already exists", name, id)
}
```

In the collision case (two tasks happen to get the same 8-char hex ID — rare but possible), this message tells the operator "ID a1b2c3d4 already exists" — which looks like a user error, not a system collision. A retry would silently fix it. The operator should just retry.

Fix: detect the collision and retry `generateID` up to N times before failing with a clearer message.

```go
for attempt := 0; attempt < 5; attempt++ {
    id, err = generateID()
    if err != nil { ... }
    if err = taskStore.Add(task); !errors.Is(err, store.ErrDuplicate) {
        break
    }
}
```

---

## Spec Compliance Gaps

### 6. `List` ignores `Filter.Priority` and `Filter.Limit`

**store/store.go:208–230**

The `Store` interface doc says `List` returns tasks "ordered by priority desc, created_at asc." The `Filter` struct has `Priority *int` and `Limit int` fields. `List` only handles `Filter.State` — it ignores `Priority` filtering and `Limit`, and applies no sort order.

The scheduler's `Tick` will call `List` to find eligible tasks. If it gets results in insertion order rather than priority order, higher-priority tasks don't run first. This is a functional bug against the spec.

Fix:

```go
import "sort"

// after filtering by state:
sort.Slice(out, func(i, j int) bool {
    if out[i].Priority != out[j].Priority {
        return out[i].Priority > out[j].Priority // desc
    }
    return out[i].CreatedAt.Before(out[j].CreatedAt) // asc
})
if filter.Limit > 0 && len(out) > filter.Limit {
    out = out[:filter.Limit]
}
```

---

### 7. `MaxRetries` is never set on task creation

**cmd/add.go:473–480**

The `Task` struct has `MaxRetries int`, but `runAdd` never sets it. It will default to `0`, meaning every task will transition to `dead` on the first failure (zero retries remain). This contradicts the `StateFailed` doc comment: "failed, retries remain."

The `--max-retries` flag is missing from `addCmd`. Either add it or default to a sensible value (e.g., 3) and document it.

---

### 8. `--cmd` is shell-expanded without a `--shell` escape hatch

**cmd/add.go:475**

```go
Command: []string{"sh", "-c", addShellCmd},
```

This is a reasonable default and the design notes justify it. However it means all commands run through a shell, which is a security consideration when commands include user-supplied strings. For the spec's use case (local task queue) this is acceptable — but the hard-coded `sh` will fail on systems where the queue worker runs in a minimal container with no `sh`. Consider making the shell configurable, or at least using `os.Getenv("SHELL")` as a fallback.

This is minor; document the assumption.

---

### 9. `PersistentPreRunE` leaks the store — `Close()` is never called

**cmd/root.go:355–362**

`taskStore` is opened in `PersistentPreRunE` but there is no `PersistentPostRunE` that calls `taskStore.Close()`. For `FileStore` this is currently harmless (Close is a no-op), but it violates the interface contract and will become a real leak if the store is later backed by bbolt or SQLite.

Fix: add a `PersistentPostRunE` or use `cobra.OnFinalize`/deferred close in `Execute`.

```go
PersistentPostRunE: func(cmd *cobra.Command, args []string) error {
    if taskStore != nil {
        return taskStore.Close()
    }
    return nil
},
```

---

### 10. Global `taskStore` variable is not safe for concurrent command invocation

**cmd/root.go:347–349**

`taskStore` is a package-level variable assigned in `PersistentPreRunE`. Cobra commands in a test suite can run concurrently if the test binary uses `t.Parallel()` and calls `rootCmd.Execute()` on different goroutines. The store assignment has no synchronisation.

For a single-process CLI this is harmless, but the design notes claim "tests can call `runAdd` directly" — doing so while sharing the global `taskStore` across parallel tests will race.

Fix: thread the store through command context or use `cobra.Command.SetContext`.

---

## Design Issues

### 11. Dependency existence check (`validateDependenciesExist`) re-opens the store separately from `Add`

The validation reads from the store, then `Add` reads and writes. That is two full load-from-disk cycles. For a large queue this is two full JSON deserializations. A more efficient design validates inside `Add` (which already has the loaded slice under the lock).

This also eliminates the TOCTOU race noted in issue 4.

---

### 12. Error wrapping in `ErrDuplicate` breaks `errors.Is` in some callers

**store/store.go:181**

```go
return fmt.Errorf("%w: %s", ErrDuplicate, task.ID)
```

This wraps `ErrDuplicate` correctly for `errors.Is`. No bug. Confirming this is fine.

---

### 13. `tmp` file is not cleaned up on write failure

**store/store.go:162–168**

If `os.WriteFile(tmp, ...)` succeeds but `os.Rename(tmp, fs.path)` fails, the `.tmp` file is left on disk. On the next write it will be silently overwritten, so this is not a correctness issue — but it is untidy and could confuse operators who inspect the store directory.

Fix: `defer os.Remove(tmp)` before the rename, or clean up explicitly on error.

---

## Missing Pieces (for future tasks but worth noting)

- No crash recovery: the spec says "scan running tasks on startup." `NewFileStore` should transition any `running` tasks back to `ready` (or `failed`) on open. Not required for `tq add` alone, but the architecture spec requires it.
- No `tq list` command. The `List` store method is implemented but no CLI surfaces it.
- No worker or scheduler. The `State` machine is defined but nothing drives it.

These are out of scope for the `tq add` task but should be tracked.

---

## What Is Done Well

- Cycle detection at enqueue time, not run time — correct placement per spec.
- Atomic write via temp+rename — right pattern (needs fsync, see bug 2).
- Sentinel errors with `%w` wrapping throughout — `errors.Is` works correctly.
- Only ID to stdout — pipe-friendly, matches spec.
- Error messages follow `tq: cannot add task "<name>": <reason>` convention.
- `detectCycle` in the store layer, not the command layer — guarantees hold for any caller.
- `Command []string` (not a flat string) — correct alignment with `exec.Cmd`.
- No CGO, no external runtime deps beyond Cobra.

---

## Priority Order for Fixes

1. **Bug 2 (fsync)** — the durability claim is false without it.
2. **Bug 6 (List sort + Limit)** — scheduler correctness depends on priority ordering.
3. **Bug 7 (MaxRetries unset)** — every task dies on first failure.
4. **Bug 1 (null vs [])** — silent mismatch, will confuse debugging.
5. **Bug 4 (TOCTOU)** — low risk for single-user CLI but architecturally wrong.
6. **Bug 9 (Close not called)** — will become a real leak if the store backend changes.
7. **Bug 5 (ID collision message)** — UX issue, rare but misleading.
8. **Bug 10 (global store, test races)** — matters if parallel tests are added.
9. **Bug 13 (tmp not cleaned)** — untidy, not a correctness issue.
