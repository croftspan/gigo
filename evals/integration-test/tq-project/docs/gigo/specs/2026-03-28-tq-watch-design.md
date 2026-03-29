# tq watch — Design Spec

## Goal

Add a `tq watch` command that monitors task state changes in real-time by streaming events to stdout as tasks transition between states. Support `--json` for machine-readable NDJSON output, `--filter` for targeting specific task IDs or state transitions, and `--interval` for poll frequency.

**Prerequisite:** BoltDB persistence. The current MemoryStore is process-local — a watch process can't see tasks added by separate `tq add` invocations. This spec includes BoltDB as Sub-project 1 because watch cannot function without cross-process shared state.

## Architecture

Two sub-projects, sequential dependency:

### Sub-project 1: BoltDB Persistence

```
store/
├── store.go        # MODIFY — expand Store interface (Get, Transition, Delete)
├── memory.go       # MODIFY — implement new interface methods
├── memory_test.go  # MODIFY — tests for new methods
├── bolt.go         # NEW — BoltStore implementation
└── bolt_test.go    # NEW — BoltStore tests
cmd/
├── root.go         # MODIFY — store factory, --dir flag
├── add.go          # MODIFY — use openStore() in RunE
├── list.go         # MODIFY — use openStore() in RunE
└── status.go       # MODIFY — use openStore() in RunE
go.mod              # MODIFY — add go.etcd.io/bbolt
```

### Sub-project 2: Watch Command

```
cmd/
├── watch.go        # NEW — watch command
└── watch_test.go   # NEW — watch tests
```

---

## Sub-project 1: BoltDB Persistence

### Store Interface Expansion (`store/store.go`)

Expand the `Store` interface with three methods from `persistence-patterns.md`:

```go
type Store interface {
    Add(task Task) error
    Get(id string) (Task, error)
    List(filter Filter) ([]Task, error)
    Transition(id string, from, to State) error
    Delete(id string) error
    Close() error
}

var ErrNotFound = errors.New("task not found")
var ErrConflict = errors.New("state conflict")
```

- `Get` returns a single task by ID, or `ErrNotFound`
- `Transition` is compare-and-swap: checks current state matches `from` before setting `to`. Returns `ErrConflict` if current state doesn't match `from`. Returns `ErrNotFound` if task doesn't exist.
- `Delete` removes a task by ID. Returns `ErrNotFound` if missing.

### MemoryStore Updates (`store/memory.go`)

Implement the three new methods on `MemoryStore`:

- `Get(id string) (Task, error)` — lock, look up in map, return copy or `ErrNotFound`
- `Transition(id string, from, to State) error` — lock, look up task, compare `task.State` to `from`, if mismatch return `ErrConflict`, otherwise set state to `to`, write back
- `Delete(id string) error` — lock, check key exists, delete, return `ErrNotFound` if missing

### BoltStore Implementation (`store/bolt.go`)

```go
type BoltStore struct {
    db *bbolt.DB
}
```

**Storage model:**
- Single bucket: `"tasks"`
- Key: task ID as bytes
- Value: JSON-encoded `Task` struct
- JSON chosen for debuggability — inspectable with standard bolt tools

**Constructor:**
```go
func NewBoltStore(path string) (*BoltStore, error)
```
Opens BoltDB at `path` with `bbolt.Options{Timeout: 1 * time.Second}`. Creates the `"tasks"` bucket in an `Update` transaction if it doesn't exist. Returns the store.

The 1-second timeout prevents indefinite blocking when another process holds the write lock. After timeout, returns an error instead of hanging.

**Methods — all wrap BoltDB transactions:**
- `Add` — read-write tx. If ID empty, generate 8-char hex ID. Marshal task to JSON, put in bucket.
- `Get` — read-only tx. Get key from bucket, unmarshal, return. `ErrNotFound` if key missing.
- `List` — read-only tx. Cursor iteration over bucket, unmarshal each, apply filter, return slice.
- `Transition` — read-write tx. Get current task, compare state to `from`, update if match, put back. `ErrConflict` on mismatch, `ErrNotFound` if missing. The transaction provides atomicity.
- `Delete` — read-write tx. Check key exists, delete. `ErrNotFound` if missing.
- `Close` — close `bbolt.DB`.

**Dependency:** `go.etcd.io/bbolt` — pure Go, no CGO, single-file embedded database.

**Concurrency model:** BoltDB allows one writer and multiple readers within a single process via one `*bbolt.DB` handle. A second process opening the same file blocks on the file lock. For the CLI pattern (short-lived invocations), each command opens the DB, runs its transaction, and closes. The lock is held for single-digit milliseconds.

**Read-only open:** `NewBoltStoreReadOnly(path string) (*BoltStore, error)` opens the DB with `bbolt.Options{ReadOnly: true}`. Read-only handles do not acquire the write lock and can coexist with a writer. The watch command uses read-only opens so it works even while a future long-running `tq run` holds the write lock.

### Store Factory (`cmd/root.go`)

Add a `--dir` persistent flag and `openStore()` factory function:

```go
var tqDir string

// Add to EXISTING init() — do NOT re-register --json (already registered).
func init() {
    // rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", ...) ← already exists, do not duplicate
    rootCmd.PersistentFlags().StringVar(&tqDir, "dir", "", "Queue directory (default ~/.tq, env: TQ_DIR)")
}

func openStore() (store.Store, error) {
    dir := tqDir
    if dir == "" {
        dir = os.Getenv("TQ_DIR")
    }
    if dir == "" {
        home, err := os.UserHomeDir()
        if err != nil {
            return nil, fmt.Errorf("tq: cannot determine home directory: %w", err)
        }
        dir = filepath.Join(home, ".tq")
    }
    if err := os.MkdirAll(dir, 0o755); err != nil {
        return nil, fmt.Errorf("tq: cannot create queue directory %q: %w", dir, err)
    }
    return store.NewBoltStore(filepath.Join(dir, "queue.db"))
}
```

**Resolution order:** `--dir` flag > `$TQ_DIR` env var > `~/.tq`

All existing commands (`add`, `list`, `status`) change their `RunE` functions to use `openStore()` instead of `store.NewMemoryStore()`. The injectable `runXWithStore` functions remain unchanged — tests still inject MemoryStore.

Example change in `runAdd`:
```go
func runAdd(cmd *cobra.Command, args []string) error {
    s, err := openStore()
    if err != nil {
        return err
    }
    defer s.Close()
    return runAddWithStore(s, args[0], addCmd, addPri, addDepStr, jsonOutput, os.Stdout)
}
```

Same pattern for `runList` and `runStatus`.

---

## Sub-project 2: Watch Command

### Usage

```
tq watch [--filter EXPR] [--interval DURATION] [--json]
```

### Flags

| Flag | Required | Default | Description |
|---|---|---|---|
| `--filter` | no | `""` (all events) | Comma-separated key=value filter expression |
| `--interval` | no | `500ms` | Poll interval as Go duration string |
| `--json` | no | `false` | Inherited from root. NDJSON output. |

### Filter Syntax

`--filter` accepts comma-separated `key=value` pairs with AND logic:

- `id=a1b2c3d4` — only events for this task ID
- `id=a1b2c3d4,id=e5f6a7b8` — events for either task ID (OR within same key)
- `to=running` — only transitions TO running state
- `from=ready` — only transitions FROM ready state
- `from=ready,to=running` — only the specific ready→running transition (AND across keys)

Valid keys: `id`, `from`, `to`. Unknown keys are an error. State values in `from` and `to` filters are validated against `AllStates` — invalid states produce an error before the poll loop starts. Multiple `id` values use OR logic (match any). `from` and `to` use AND logic with each other and with `id`.

**Filter spec struct and parser:**

```go
type watchFilterSpec struct {
    IDs   map[string]bool // empty = match all IDs; OR logic (match any listed ID)
    Froms map[string]bool // empty = match all from-states; OR within, AND with other keys
    Tos   map[string]bool // empty = match all to-states; OR within, AND with other keys
}

func parseWatchFilter(raw string) (watchFilterSpec, error)
```

Matching logic: an event passes the filter if ALL of these are true:
- `IDs` is empty OR `event.TaskID` is in `IDs`
- `Froms` is empty OR `event.From` is in `Froms`
- `Tos` is empty OR `event.To` is in `Tos`

### Change Detection Algorithm

```
1. Open store (read-only), List all tasks, build snapshot: map[taskID]snapshotEntry
   where snapshotEntry = {State, Name}
2. Close store
3. Signal that initial snapshot is ready (for testability — see Testing section)
4. Start ticker at --interval
5. On each tick:
   a. Open store (read-only via NewBoltStoreReadOnly)
   b. List all tasks (full Task structs)
   c. Close store
   d. Build set of current task IDs
   e. For each task in current list:
      - ID not in snapshot → emit event (from="", to=task.State, name=task.Name)
      - State differs from snapshot → emit event (from=snapshot[id].State, to=task.State, name=task.Name)
   f. For each ID in snapshot NOT in current list:
      - Emit event (from=snapshot[id].State, to="deleted", name=snapshot[id].Name)
      - Remove from snapshot
   g. Update snapshot with current task states and names
6. On SIGINT/SIGTERM → cancel context → stop ticker → exit 0
```

Events are constructed from the **current poll's `List` result** for `to`, `name`, and `task_id` fields. The `from` field comes from the snapshot. The snapshot stores both state and name for each task — the name is needed for deletion events when the task is no longer in the current list.

The store is opened in **read-only mode** on each poll cycle. This avoids acquiring BoltDB's write lock, allowing concurrent writes from other `tq` commands (including a future long-running `tq run`).

### Event Types

| Type | `from` | `to` | When |
|---|---|---|---|
| New task | `""` (empty) | current state | Task ID appears that wasn't in snapshot |
| State transition | previous state | new state | Task ID exists but state changed |
| Deletion | previous state | `"deleted"` | Task ID was in snapshot but not in current list |

Deletion events use `from=<last known state>` and `to="deleted"`. The task name comes from the snapshot (since the task is no longer in the current list). In text output, this renders as:
```
2026-03-28T10:00:05Z  a1b2c3d4  done->deleted  build-frontend
```

### Output Format

**Text (default):**

```
2026-03-28T10:00:01Z  a1b2c3d4  NEW->ready      build-frontend
2026-03-28T10:00:03Z  a1b2c3d4  ready->running   build-frontend
2026-03-28T10:00:05Z  e5f6a7b8  running->done    lint
```

Format: `%s  %s  %s->%s  %s\n` — timestamp (RFC 3339), task ID, from→to, task name. Two-space separation between fields.

For new tasks, `from` displays as `NEW`:
```
2026-03-28T10:00:01Z  a1b2c3d4  NEW->pending  deploy
```

**JSON (`--json`):**

```json
{"timestamp":"2026-03-28T10:00:01Z","task_id":"a1b2c3d4","name":"build-frontend","from":"","to":"ready"}
{"timestamp":"2026-03-28T10:00:03Z","task_id":"a1b2c3d4","name":"build-frontend","from":"ready","to":"running"}
```

NDJSON — one JSON object per line. No array wrapper. Pipe directly to `jq`:
```
tq watch --json | jq 'select(.to == "done")'
```

For new tasks, `from` is an empty string `""` in JSON (not `"NEW"`).

**Event struct:**

```go
type WatchEvent struct {
    Timestamp string `json:"timestamp"`
    TaskID    string `json:"task_id"`
    Name      string `json:"name"`
    From      string `json:"from"`
    To        string `json:"to"`
}
```

`Timestamp` is RFC 3339 string. `From` is empty string for new tasks.

### Signal Handling

```go
ctx, cancel := signal.NotifyContext(cmd.Context(), os.Interrupt, syscall.SIGTERM)
defer cancel()
```

Context cancellation stops the ticker select loop. `runWatchLoop` returns `nil` on clean shutdown (not an error). Exit code 0.

### Testability

Injectable `storeOpener` function replaces the direct `openStore()` dependency:

```go
type storeOpener func() (store.Store, error)

func runWatchLoop(ctx context.Context, open storeOpener, spec watchFilterSpec, interval time.Duration, jsonOut bool, w io.Writer) error
```

In production, `open` is `openStore`. In tests, `open` returns a shared `MemoryStore` (whose `Close` is a no-op, so it survives repeated open/close cycles). Tests add and modify tasks on the shared store between poll cycles to trigger events.

To simulate state transitions in tests: call `s.Transition(id, from, to)` — the same method production code uses. Do NOT call `s.Add()` with the same ID to overwrite state, as this tests the wrong contract and is fragile if `Add` ever rejects duplicate IDs.

**Snapshot-ready signaling for tests:** `runWatchLoop` accepts an optional `chan struct{}` parameter (`snapshotReady`) that is closed after the initial snapshot is taken. If nil, no signal is sent. Tests pass a channel and wait on it before mutating the store, eliminating the race condition of a `time.Sleep`-based approach.

```go
func runWatchLoop(ctx context.Context, open storeOpener, spec watchFilterSpec, interval time.Duration, jsonOut bool, w io.Writer, snapshotReady chan struct{}) error
```

In production, `snapshotReady` is `nil`. In tests:

```go
ready := make(chan struct{})
go func() {
    done <- runWatchLoop(ctx, open, spec, 10*time.Millisecond, false, &buf, ready)
}()
<-ready // blocks until initial snapshot is taken
s.Add(store.Task{...}) // now safe — snapshot exists, next poll will detect this
```

### Error Handling

| Error | Message | Exit |
|---|---|---|
| Can't open store | `tq: cannot open queue: <reason>` | 1 |
| Can't read queue | `tq: cannot read queue: <reason>` | 1 |
| Invalid filter | `tq: invalid filter expression "<expr>" (expected key=value)` | 1 |
| Unknown filter key | `tq: unknown filter key "<key>" (valid: id, from, to)` | 1 |
| Invalid filter state | `tq: invalid state "<state>" in filter (valid: pending, ready, running, done, failed, dead)` | 1 |
| Clean shutdown | *(no output)* | 0 |

Errors return from `RunE`. No `os.Exit` in command logic.

---

## Testing

### Store Tests

**MemoryStore new methods (`store/memory_test.go`):**
- `TestGet` — add task, get by ID, verify fields match
- `TestGetNotFound` — get nonexistent ID, verify `ErrNotFound`
- `TestTransition` — add task in StateReady, transition to StateRunning, verify
- `TestTransitionConflict` — add task in StateReady, attempt transition from StatePending, verify `ErrConflict`
- `TestTransitionNotFound` — transition nonexistent ID, verify `ErrNotFound`
- `TestDelete` — add task, delete, verify List returns empty
- `TestDeleteNotFound` — delete nonexistent ID, verify `ErrNotFound`

**BoltStore (`store/bolt_test.go`):**
- All MemoryStore tests replicated against BoltStore (same behavior contract)
- Each test uses `t.TempDir()` for DB path — clean isolation
- `TestBoltCrashRecovery` — write tasks, close DB (simulating crash), reopen, verify all committed data present
- `TestBoltConcurrentReads` — multiple goroutines reading simultaneously from single BoltStore instance

### Command Tests

**Watch (`cmd/watch_test.go`):**
- `TestWatchDetectsNewTask` — start with empty store, add task after snapshot ready, verify NEW event
- `TestWatchDetectsTransition` — start with task in StateReady, call `Transition(id, ready, running)` after snapshot ready, verify transition event
- `TestWatchDetectsDeletion` — start with task, call `Delete(id)` after snapshot ready, verify deletion event with `to="deleted"`
- `TestWatchFilterByID` — add two tasks, change both, filter by one ID, verify only matching events
- `TestWatchFilterByToState` — multiple transitions, filter `to=running`, verify only matching
- `TestWatchFilterByFromState` — filter `from=ready`, verify only matching
- `TestWatchFilterCombined` — filter `from=ready,to=running`, verify AND logic
- `TestWatchJSON` — verify NDJSON output parses to correct WatchEvent struct
- `TestWatchJSONNewTask` — verify `from` is empty string in JSON for new tasks
- `TestWatchGracefulShutdown` — cancel context, verify nil return (not error)
- `TestParseWatchFilter` — valid expressions parse correctly
- `TestParseWatchFilterInvalid` — bad syntax, unknown keys, invalid states error correctly
- `TestParseWatchFilterEmpty` — empty string returns zero-value spec (all events pass)

**Test coordination pattern:** Tests use the `snapshotReady` channel to synchronize. No `time.Sleep` for setup coordination. Short poll interval (10ms), 200ms context timeout.

```go
func TestWatchDetectsNewTask(t *testing.T) {
    s := store.NewMemoryStore()
    open := func() (store.Store, error) { return s, nil }
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    var buf bytes.Buffer
    ready := make(chan struct{})
    done := make(chan error, 1)
    go func() {
        done <- runWatchLoop(ctx, open, watchFilterSpec{}, 10*time.Millisecond, false, &buf, ready)
    }()

    <-ready // wait for initial snapshot — no race
    s.Add(store.Task{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady})

    err := <-done
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !strings.Contains(buf.String(), "aaaa1111") {
        t.Errorf("expected event for aaaa1111, got: %q", buf.String())
    }
    if !strings.Contains(buf.String(), "NEW->ready") {
        t.Errorf("expected NEW->ready, got: %q", buf.String())
    }
}

func TestWatchDetectsTransition(t *testing.T) {
    s := store.NewMemoryStore()
    s.Add(store.Task{ID: "bbbb2222", Name: "deploy", Cmd: "./deploy.sh", State: store.StateReady})
    open := func() (store.Store, error) { return s, nil }
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    var buf bytes.Buffer
    ready := make(chan struct{})
    done := make(chan error, 1)
    go func() {
        done <- runWatchLoop(ctx, open, watchFilterSpec{}, 10*time.Millisecond, false, &buf, ready)
    }()

    <-ready
    s.Transition("bbbb2222", store.StateReady, store.StateRunning) // use Transition, not Add

    err := <-done
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if !strings.Contains(buf.String(), "ready->running") {
        t.Errorf("expected ready->running, got: %q", buf.String())
    }
}
```

Tests use `MemoryStore` — not BoltDB — for the watch command tests. This validates the poll-diff-emit logic without filesystem concerns. State mutations use `s.Transition()`, not `s.Add()` overwrite. BoltStore is tested separately in `store/bolt_test.go`.

---

## Conventions

All conventions from previous specs remain. Additional conventions for this feature:

- **Error messages:** `tq: cannot watch queue: <reason>`, `tq: cannot open queue: <reason>`, `tq: invalid filter expression "<expr>"...`
- **Output:** Default is grep-friendly text, one event per line. `--json` produces NDJSON (one JSON object per line, no array wrapper).
- **No ANSI, no unicode:** Transition arrow is `->` not `→`. No colors. No terminal assumptions.
- **Flag naming:** `--filter`, `--interval`, `--dir` — kebab-case, no short flags.
- **JSON struct:** Named `WatchEvent` struct with `json` tags. `From` is empty string for new tasks (not `"NEW"`).
- **Exit codes:** 0 for clean shutdown (SIGINT/SIGTERM), 1 for errors.
- **Store lifecycle in watch:** Open read-only and close on each poll cycle. Never hold the DB open across ticks. Use `NewBoltStoreReadOnly` for watch, `NewBoltStore` for write commands.
- **Store factory resolution:** `--dir` flag > `$TQ_DIR` env var > `~/.tq`
- **BoltDB encoding:** JSON for task values. Debuggable with standard tools.
- **Errors from RunE:** Return errors, never call `os.Exit` in command logic.
- **Package boundaries:** `cmd/` imports `store/`. `store/` imports nothing from `cmd/`.
- **Goroutine shutdown:** Every goroutine controlled by context cancellation. No leaked goroutines.
- **Single binary:** `go.etcd.io/bbolt` is pure Go, no CGO. `go install` still works.

## Risks

1. **BoltDB file lock contention.** Short-lived write commands (`add`, `list`, `status`) open/write/close in milliseconds — low contention. The watch command opens in **read-only mode**, which does not acquire the write lock and coexists with writers. A future long-running `tq run` can hold the write lock while watch reads concurrently.

2. **Polling latency.** Up to `--interval` delay (default 500ms) in seeing changes. Acceptable for a local CLI. Users needing lower latency can use `--interval 100ms`.

3. **Interface expansion breaks compilation.** Adding `Get`, `Transition`, `Delete` to the `Store` interface means MemoryStore must be updated in the same commit. Tasks 1.0 + 1.1 must land together.

4. **Test timing.** Watch tests use the `snapshotReady` channel for setup coordination — no race condition. The 200ms context timeout with 10ms poll interval gives 20 detection opportunities, providing ample margin.

5. **Memory on large queues.** Watch snapshot holds `map[string]snapshotEntry` — ~64 bytes per task (state + name). At 10,000 tasks this is ~640KB. Not a concern for a local tool.

6. **BoltDB is a new dependency.** First external dependency beyond Cobra. Justified because: it's the planned persistence layer per `persistence-patterns.md`, it's pure Go with no CGO, and persistence is required for watch (and every future cross-process feature).

<!-- approved: spec 2026-03-28T12:30:00 -->
