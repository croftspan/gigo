# Code Review: `tq add` Implementation

## Summary

Solid foundation — the happy path is clean, the dependency validation order is sensible, and WAL mode with a single writer is the right SQLite setup. The bugs below range from data loss (the `name` field) to silent data corruption (parseCommand escaping) to correctness issues in the cycle check. None are catastrophic but several will surface in real use.

---

## Bugs

### 1. `name` argument is silently discarded — data loss

**File:** `cmd/add.go`, line 124

```go
_ = name // name is stored inside the task via Command for display; kept as label
```

The comment is wrong. `name` is not stored inside `Command` — `Command` is populated from `--cmd`, not from the positional argument. The `Task` struct has no `Name` field, and the schema has no `name` column. The value is captured and thrown away.

**Impact:** Every task loses its human-readable label. `tq list` will have nothing to display for task names. If the feature is intentionally deferred, the comment should say so explicitly and the `Use: "add <name>"` doc string is misleading — users will expect this to work.

**Fix:** Add `Name string` to `Task`, `name TEXT NOT NULL DEFAULT ''` to the schema, store `t.Name = name`, and include it in the INSERT and SELECT column lists.

---

### 2. `parseCommand` drops escape sequences — silent data corruption

**File:** `cmd/add.go`, `parseCommand` function

The tokenizer handles quotes but not backslash escapes. This breaks real-world inputs:

- `--cmd "echo \"hello\""` — the backslash-quote is not consumed as an escape; the `\"` terminates the outer quote early, producing `["echo", "hello"]` instead of `["echo", "\"hello\""]`.
- `--cmd "path with\\ space"` — the double backslash is passed through literally.

Also, only space is treated as a delimiter — tabs and other Unicode whitespace are not. `--cmd "go\tbuild"` would produce a single token.

**Impact:** Commands with escaped quotes or backslashes silently produce wrong argv. The user gets no error; the wrong command runs.

**Fix:** Add a backslash-escape pass inside the tokenizer. When `inQuote` and the next character is `quoteChar` or `\\`, consume the escape and emit the literal character. For whitespace, check `unicode.IsSpace(r)` instead of `r == ' '`.

---

### 3. Cycle check does not add the new task's node — misses self-cycles

**File:** `dag/dag.go`, `CheckCycle`

```go
adj[t.ID] = t.DependsOn
```

The new task's edges are added to `adj`, but `t` is never added to `d.Nodes`. This doesn't affect the DFS (which only uses `adj`), but it means the new task is absent from the node set. More importantly, if a user passes `--depends-on <same-id-as-new-task>` and the ID happens to collide with an existing task, the cycle check runs against the wrong graph — it uses the existing task's edges, not the new one's.

**A harder bug:** The DFS iterates `for id := range adj` — this includes existing tasks and the new one. However, it does not check whether dependency IDs referenced in `adj[id]` actually exist in `adj`. If task A depends on task B, and B is in the store but not in `adj` (because `validateNoCycle` builds `adj` from `d.Edges` which comes from `store.List`), then `adj[B]` returns nil and the DFS silently stops. In practice `store.List` returns all tasks so B will be there — but the invariant is not enforced, making the code fragile.

**Fix:** After building `adj`, verify that every dependency ID referenced in it is also a key in `adj`. Return an informative error if not (this would also catch races between `validateDependencies` and `validateNoCycle`).

---

### 4. Race between dependency existence check and cycle check

**File:** `cmd/add.go`, `runAdd`

```
validateDependencies  →  validateNoCycle  →  store.Add
```

`validateDependencies` calls `store.Get` for each dep. `validateNoCycle` calls `store.List`. Neither is transactional with `store.Add`. A concurrent `tq add` that deletes or modifies a dependency between these steps will cause the new task to be written with a `DependsOn` pointing at a non-existent or changed task.

**Impact:** Low probability in a local CLI, but the store supports multiple workers (`ClaimTask`, `ReclaimOrphan`). A task queue with workers implies concurrent access.

**Fix:** Wrap the read-validate-write sequence in a SQLite transaction. SQLite in WAL mode allows this with `BEGIN IMMEDIATE`. The current `db.ExecContext` calls are not transactional; add a `BeginTx` / `Commit` / `Rollback` helper to `SQLiteStore`.

---

### 5. `RunE` error handling bypasses Cobra's error propagation

**File:** `cmd/add.go`, `runAdd`

The function signature is `func runAdd(cmd *cobra.Command, args []string) error` — meaning Cobra will print and propagate any returned error. Instead, every error path does:

```go
fmt.Fprintf(os.Stderr, "error: ...\n")
os.Exit(1)
```

**Impact:**
- `os.Exit(1)` prevents `defer store.Close()` from running. SQLite WAL mode requires a clean close to flush the WAL file; skipping it on error means the WAL may not checkpoint, and the DB is left in a state requiring recovery on next open. Under high write frequency this is a real problem.
- The pattern is untestable — you cannot write a unit test that calls `runAdd` and checks its behavior on error because the process exits.
- Cobra's `SilenceErrors` / `SilenceUsage` flags, error formatting, and exit code handling are all bypassed.

**Fix:** Return errors from `RunE`. Let Cobra handle printing and exit. For the `store.Close` issue specifically, use a named return or restructure so `defer store.Close()` always fires:

```go
store, err := openStore()
if err != nil {
    return fmt.Errorf("could not open store: %w", err)
}
defer store.Close()
```

---

### 6. ID collision is unhandled

**File:** `cmd/add.go`, `generateID`

4 bytes = 32 bits = ~4 billion IDs. Birthday paradox: 50% collision probability at ~65,000 tasks. For a local queue this is acceptable, but `store.Add` will return a SQLite UNIQUE constraint violation with no retry logic.

**Impact:** The user gets a raw SQLite error with no explanation. In queues that accumulate tens of thousands of tasks this becomes observable.

**Fix:** Either retry `generateID` up to N times on UNIQUE constraint violation, or increase to 8 bytes (16 hex chars) to push the collision point past any realistic local queue size.

---

## Design Issues

### 7. `Store` interface is too broad for `cmd/add.go`

**File:** `store/interfaces.go`

`cmd/add.go` uses three methods: `Get`, `List`, `Add`. The `Store` interface it receives has 13 methods including `ClaimTask`, `ReclaimOrphan`, `SetStarted`, `SetFinished`, `IncrementRetries`, `UpdateWorkerPID`. These are worker-process concerns, not CLI concerns.

**Impact:** Testing `runAdd` requires a mock or stub of 13 methods. Adding a new method to `Store` forces changes to every mock in the test suite. The worker package imports the same interface, so `cmd/add.go` is coupled to worker internals.

**Fix:** Define narrower interfaces at the call site:

```go
type taskAdder interface {
    Get(ctx context.Context, id string) (*Task, error)
    List(ctx context.Context, filter ListFilter) ([]*Task, error)
    Add(ctx context.Context, t *Task) error
    Close() error
}
```

`SQLiteStore` satisfies this automatically. The worker uses the full `Store`. No behavior changes, but mocking drops from 13 methods to 4.

---

### 8. `validateNoCycle` does a full table scan on every add

**File:** `cmd/add.go`, `validateNoCycle`

```go
all, err := store.List(ctx, ListFilter{})
```

This loads every task in the store to build the DAG. For a queue with thousands of completed tasks, this is wasteful — completed tasks cannot be part of a new cycle.

**Fix:** Filter to non-terminal statuses:

```go
all, err := store.List(ctx, ListFilter{
    Status: []TaskStatus{StatusPending, StatusReady, StatusRunning},
})
```

This reduces the scan proportionally to queue depth and doesn't affect correctness — done/failed/cancelled tasks cannot introduce cycles in new pending tasks.

---

### 9. `buildListQuery` has an OFFSET-without-LIMIT footgun

**File:** `store/sqlite.go`, `buildListQuery`

```go
if f.Limit > 0 {
    q += " LIMIT ?"
    args = append(args, f.Limit)
}
if f.Offset > 0 {
    q += " OFFSET ?"
    args = append(args, f.Offset)
}
```

If `f.Offset > 0` and `f.Limit == 0`, the query emits `OFFSET` without `LIMIT`. SQLite accepts this syntactically (it treats it as `LIMIT -1 OFFSET n`) but the behavior is surprising and not what any caller intends.

**Fix:** Either enforce `Limit > 0` when `Offset > 0` (return an error), or always emit `LIMIT -1` when Offset is set without a Limit.

---

### 10. `depends_on` stored as comma-separated string — no referential integrity

**File:** `store/sqlite.go`, schema

```sql
depends_on TEXT NOT NULL DEFAULT ''  -- comma-separated IDs
```

SQLite foreign keys are enabled (`_foreign_keys=on`), but the dependency relationship is stored as a denormalized comma-separated string — not as a foreign key. This means:

- Deleting a task does not cascade or error on its dependents.
- The DB cannot enforce referential integrity on dependencies.
- Querying "what tasks depend on task X" requires a full table scan with string matching.

**Fix for a future iteration:** Add a `task_deps` junction table: `(task_id TEXT REFERENCES tasks(id), dep_id TEXT REFERENCES tasks(id))`. This enables proper FK enforcement, cascade deletes, and indexed lookups. For v1 the current approach is pragmatic — just document the limitation and ensure the application layer enforces it consistently.

---

## Missing Pieces

### 11. No validation that a dependency has not already failed or been cancelled

`validateDependencies` checks existence. It does not check status. A user can add a task that depends on a `StatusFailed` task — the scheduler will promote it once... never, since failed tasks never become done. The task will sit in `StatusPending` forever.

**Fix:** In `validateDependencies`, check the dependency's status. Warn (or error) if any dependency is in a terminal non-done state.

---

### 12. `parseCommand` is not tested and has no documented contract for edge cases

No test coverage is visible for the tokenizer. The edge cases that matter:

- Empty string after trimming whitespace
- Unclosed quote: `--cmd "go build` — currently the final token is emitted without error
- Adjacent quotes: `--cmd "foo""bar"` — produces `foobar` (probably correct but undocumented)
- Escaped spaces inside unquoted args

An unclosed quote silently discards the partial token if the loop exits mid-quote — actually it does emit it because of the trailing `if current.Len() > 0` check, but with no error. A user typo in the command string produces a silently malformed argv.

**Fix:** After the loop, check `if inQuote { return nil, fmt.Errorf("unclosed quote in --cmd") }`. Surface this as a validation error before writing to the store.

---

## Minor / Nits

- `addCmd_` (trailing underscore) is an awkward name. `cmdFlag` or `addCmdStr` is cleaner.
- `Priority(addPriority)` casts an `int` to `Priority` without range validation. A user passing `--priority -999` gets a valid task with negative priority. Define a sensible floor/ceiling or document the behavior.
- `time.Now().UTC()` for `CreatedAt` is correct, but `SetStarted` and `SetFinished` also call `time.Now().UTC()` inside the store method — mixing clock ownership between caller and callee. Pick one convention: either the caller always provides times (more testable), or the store always calls `time.Now()`. Currently both happen.
- The `Execute()` function in `root.go` ignores the error returned by `rootCmd.Execute()`. The comment says "cobra already prints the error" which is true, but the process will not exit non-zero when cobra prints the error via its internal handler — you need `os.Exit(1)` or to use `cobra.CheckErr`.
