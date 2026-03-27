# Code Review: tq add Implementation

Reviewer: spec-only, no project context loaded.

---

## Summary

The implementation is largely correct and well-structured. It handles the happy path, pipe-friendliness, atomic writes, and sentinel error wrapping correctly. There are a handful of real bugs and spec gaps that need fixing before this is production-ready.

---

## Bugs

### 1. Cycle detection is direction-inverted (store/store.go:294–326)

**Impact: Critical — ErrCycle fires on legitimate tasks, not actual cycles.**

`detectCycle` builds a graph where edges run `task → dependency` (i.e., if task A depends on B, edge is A→B). The DFS then starts from `newTask.ID` and walks *forward* through that dependency direction. This detects only cycles that are reachable from the new task via its own dependency chain — it does not detect the case where an *existing* task depends on the new task, forming a back-edge through the new task.

Concrete failing case:
```
add A (no deps)          → graph: A→[]
add B --depends-on A     → graph: A→[], B→[A]
add A2 --depends-on B    → detectCycle starts DFS at A2, walks A2→B→A, no cycle found. Correct.
```

But now:
```
add C --depends-on A     → fine
add A2 --depends-on C    → DFS from A2: A2→C→A, no cycle. Correct.
```

The real failure mode: if the graph already contains a cycle in `existing` tasks (which should be impossible if Add always validates, but see bug 2), `detectCycle` only starts the DFS from `newTask.ID`, so it will miss cycles entirely disconnected from the new task.

More importantly, the DFS direction is wrong for detecting whether the *new* task creates a cycle. A cycle occurs when any dependency of `newTask` (transitively) depends back on `newTask.ID`. The current code would catch `newTask → dep → newTask` but only if `newTask.ID` already exists in the graph's adjacency list with edges pointing back — which it won't, because this is a *new* task being added. The DFS on `newTask.ID` with `newTask.DependsOn` as its edges will never find a cycle through `newTask` itself since no existing task has `newTask.ID` as a dependency yet.

**Fix:** Run DFS over all nodes (not just `newTask.ID`), or reverse the graph and check reachability from the new task's dependencies back to the new task.

```go
func detectCycle(existing []Task, newTask Task) error {
    graph := make(map[string][]string, len(existing)+1)
    for _, t := range existing {
        graph[t.ID] = t.DependsOn
    }
    graph[newTask.ID] = newTask.DependsOn

    visited := make(map[string]bool)
    inStack := make(map[string]bool)

    var dfs func(id string) bool
    dfs = func(id string) bool {
        if inStack[id] {
            return true
        }
        if visited[id] {
            return false
        }
        visited[id] = true
        inStack[id] = true
        for _, dep := range graph[id] {
            if dfs(dep) {
                return true
            }
        }
        inStack[id] = false
        return false
    }

    // Must check ALL nodes, not just the new task.
    for id := range graph {
        if !visited[id] {
            if dfs(id) {
                return ErrCycle
            }
        }
    }
    return nil
}
```

### 2. Get errors other than ErrNotFound are silently swallowed (cmd/add.go:509)

**Impact: Medium — storage errors during dependency validation are ignored.**

```go
if _, err := s.Get(id); errors.Is(err, store.ErrNotFound) {
    missing = append(missing, id)
}
```

If `s.Get` returns an I/O error (corrupt store, permission denied), the condition is false, the ID is not added to `missing`, and the function returns `nil` — treating the dependency as present when it may not be. The task is then added with an unverified dependency.

**Fix:**
```go
for _, id := range deps {
    _, err := s.Get(id)
    if err == nil {
        continue
    }
    if errors.Is(err, store.ErrNotFound) {
        missing = append(missing, id)
        continue
    }
    return fmt.Errorf("tq: cannot add task %q: checking dependency %q: %w", taskName, id, err)
}
```

### 3. Store is never closed on success (cmd/root.go)

**Impact: Low for FileStore (Close is a no-op), but a real correctness issue against the Store interface.**

`PersistentPreRunE` opens the store and assigns it to `taskStore`. There is no `PersistentPostRun` or `defer taskStore.Close()`. If a future Store implementation (SQLite, network-backed) has a non-trivial `Close`, this leaks resources and may lose buffered writes.

**Fix:** Add a `PersistentPostRunE` that calls `taskStore.Close()`, or defer it inside `PersistentPreRunE` (but defers there run when `PersistentPreRunE` returns, not when the command finishes — so use `PersistentPostRunE`):

```go
rootCmd.PersistentPostRunE = func(cmd *cobra.Command, args []string) error {
    if taskStore != nil {
        return taskStore.Close()
    }
    return nil
}
```

---

## Spec Compliance Issues

### 4. Task name is stored nowhere (cmd/add.go:473–479)

**Impact: Medium — the Task struct has no Name field; the positional argument is parsed and then discarded.**

The spec says "Task name is positional argument." The `Task` struct (store/task.go:41–55) has no `Name` field. The name is used only for error messages inside `runAdd` and `validateDependenciesExist`. Once the task is stored, there is no way to recover the name from the store — `tq list` (if it exists) will show IDs and commands but not the human-readable name the operator assigned.

This may be intentional (name is purely cosmetic at the CLI boundary), but if `tq list` or `tq get` is expected to show the name, it needs to be added to `Task`:

```go
Name string `json:"name"`
```

and populated:
```go
task := store.Task{
    ID:      id,
    Name:    name,
    ...
}
```

### 5. List does not sort by priority desc, created_at asc (store/store.go:208–230)

**Impact: Medium — the Store interface contract is documented but unimplemented.**

The interface comment says "ordered by priority desc, created_at asc." The `List` implementation returns tasks in insertion order. The worker scheduler relying on `List` to get the next eligible task will not get priority ordering.

**Fix:** Sort before returning:
```go
sort.Slice(out, func(i, j int) bool {
    if out[i].Priority != out[j].Priority {
        return out[i].Priority > out[j].Priority // desc
    }
    return out[i].CreatedAt.Before(out[j].CreatedAt) // asc
})
```

(`sort` import needed.)

### 6. List does not apply Filter.Priority or Filter.Limit (store/store.go:208–230)

**Impact: Low for `tq add`, but the interface is only half-implemented.**

`Filter.Priority` and `Filter.Limit` are declared in the Filter struct but the List implementation ignores them. Only `Filter.State` is applied. This is a stub that will silently return too many tasks if callers rely on these fields.

---

## Design Issues

### 7. Global mutable state for taskStore (cmd/root.go:346–349)

**Impact: Low for production CLI use, High for testing.**

`taskStore` is a package-level variable mutated by `PersistentPreRunE`. Tests that call `runAdd` directly or run multiple commands in the same process will share this global. This makes the command functions untestable in parallel and creates a hidden dependency.

The design notes claim "tests can call `runAdd` directly" — but `runAdd` uses `taskStore` via the package global, not a parameter. A test calling `runAdd` without first triggering `PersistentPreRunE` will panic on a nil dereference.

**Better pattern:** Pass the store as a parameter or embed it in a command struct. At minimum, document that `taskStore` must be initialized before calling `runAdd` in tests.

### 8. validateDependenciesExist calls Get N times under no lock (cmd/add.go:506–520)

**Impact: Low — TOCTOU window between validation and Add.**

The command layer calls `Get` for each dependency (N round-trips to disk), then calls `Add`. Another process could delete a dependency between these two operations. The store will add the task with a dangling dependency reference. For a local file-backed store this window is small, but the implementation claims to be "safe for concurrent use."

This is acceptable for v1 but should be noted as a known limitation.

### 9. The --cmd flag stores shell string as `["sh", "-c", cmd]` without documentation of the security implication

**Impact: Low for local CLI, worth noting.**

`cmd/add.go:475`: `Command: []string{"sh", "-c", addShellCmd}` means arbitrary shell injection is available by design. For a local task queue run by the same user who writes the commands, this is fine — but if a future API layer allows remote task submission, this becomes a shell injection vector. The current implementation has no validation or escaping of `addShellCmd`. This should at minimum be noted in a comment or doc, not left as an implicit design choice.

---

## Minor Issues

### 10. ErrDuplicate error message in runAdd includes the generated ID (cmd/add.go:489–490)

```go
return fmt.Errorf("tq: cannot add task %q: ID %s already exists", name, id)
```

A collision on a freshly generated 8-char ID (4 bytes, ~4 billion values) is vanishingly rare on a local queue. When it does happen, this message will confuse operators — they didn't choose the ID, so "ID already exists" with no context on what to do is unhelpful. A better message: `"tq: cannot add task %q: ID collision; please retry"`.

### 11. write() uses a fixed `.tmp` suffix (store/store.go:157)

```go
tmp := fs.path + ".tmp"
```

If two `FileStore` instances point to the same path (unlikely but possible in tests), concurrent writes will clobber each other's temp file and potentially lose data even though each instance holds its own mutex. A PID-qualified or random temp name is safer: `fmt.Sprintf("%s.%d.tmp", fs.path, os.Getpid())`.

### 12. `os.Rename` across filesystems is not atomic (store/store.go:165)

**Impact: Informational — the claim in the design notes is slightly overstated.**

The design notes claim `rename(2)` is atomic. This is true only when source and destination are on the same filesystem. If the store path is on a different mount than the default temp directory (not the case here since `.tmp` is co-located), this guarantee breaks. The implementation correctly co-locates `.tmp` next to the target file, so this is fine in practice — but the comment should say "same filesystem" not just "POSIX."

---

## What Is Done Well

- Sentinel errors wrapped correctly with `%w` so callers can use `errors.Is`.
- Atomic write via temp-file + rename is the right pattern for a file-backed store.
- Only task ID printed to stdout; errors go to stderr via Cobra — pipe-friendly by design.
- `crypto/rand` for ID generation rather than `math/rand` — correct for a uniqueness guarantee.
- Dependency validation accumulates all missing IDs before returning — good UX.
- `MarkFlagRequired("cmd")` is the right Cobra mechanism; no manual nil check needed.
- Initial state logic (ready vs pending based on deps) is correctly placed and documented.

---

## Priority Order for Fixes

| # | Issue | Severity |
|---|-------|----------|
| 1 | Cycle detection only traverses from new task, misses existing-graph cycles | Critical |
| 2 | Get errors swallowed during dependency validation | Medium |
| 4 | Task name discarded — not stored in Task struct | Medium |
| 5 | List unsorted despite interface contract | Medium |
| 3 | Store never closed | Low |
| 6 | Filter.Priority and Filter.Limit unimplemented | Low |
| 7 | Global taskStore blocks test isolation | Low |
| 8 | TOCTOU between validateDependenciesExist and Add | Low |
| 9 | Shell injection by design, undocumented | Low |
| 10 | ErrDuplicate message blames operator for system collision | Minor |
| 11 | Fixed .tmp suffix | Minor |
| 12 | rename atomicity claim overstated | Informational |
