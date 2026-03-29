# tq priority — Design Spec

## Goal

Add a `tq priority <task-id> <new-priority>` command that changes a task's priority after creation. Priority is queue-ordering metadata — it determines scheduling order but has no effect on currently running tasks. Changing priority on a running task succeeds and takes effect on retry if the task fails.

**Prerequisite:** Expand the `Store` interface with `Get` and `UpdatePriority` methods. `Get` is already specced by the watch design but not yet implemented; adding it here is forward-compatible. `UpdatePriority` is new — a focused atomic operation for priority mutation.

## Architecture

Minimal footprint — one new command file, two new Store methods, tests for both.

```
store/
├── store.go        # MODIFY — add ErrNotFound, Get, UpdatePriority to Store interface
├── memory.go       # MODIFY — implement Get, UpdatePriority on MemoryStore
└── memory_test.go  # MODIFY — add tests for Get, UpdatePriority
cmd/
├── priority.go     # NEW — tq priority command
└── priority_test.go # NEW — tests for priority command
```

No changes to existing commands (`add`, `list`, `status`). No new dependencies.

---

## Store Interface Expansion (`store/store.go`)

Add one sentinel error and two methods. This requires adding `"errors"` to the import list in `store/store.go`.

```go
var ErrNotFound = errors.New("not found")

type Store interface {
    Add(task Task) error
    Get(id string) (Task, error)                   // NEW
    List(filter Filter) ([]Task, error)
    UpdatePriority(id string, priority int) error   // NEW
    Close() error
}
```

### `ErrNotFound`

Returned by `Get` and `UpdatePriority` when the task ID doesn't exist. The watch spec defines the same sentinel with the message `"task not found"` — when watch lands, unify to one. For now, use `"not found"` (shorter, consistent with the error message format where context is added by the caller).

**Implementation note:** If `ErrNotFound` already exists in `store/store.go` (from the watch spec landing first), use it as-is. Do not redefine it.

### `Get(id string) (Task, error)`

Returns a copy of the task (value, not pointer) matching the given ID. Returns `ErrNotFound` if no task exists with that ID. This matches the pattern established by `List`, which returns `[]Task` value copies.

Forward-compatible with the watch spec, which defines the same method signature.

### `UpdatePriority(id string, priority int) error`

Atomically sets the priority field of the task with the given ID. Returns `ErrNotFound` if the task doesn't exist. Succeeds regardless of task state — priority is scheduling metadata, not execution state.

This is intentionally not a generic update method. Priority is the only mutable metadata field. State transitions use the separate `Transition` CAS method (specced by watch, not yet implemented). Focused methods are easier to reason about and test than generic mutation functions.

---

## MemoryStore Implementation (`store/memory.go`)

### `Get`

```go
func (m *MemoryStore) Get(id string) (Task, error) {
    m.mu.Lock()
    defer m.mu.Unlock()
    t, ok := m.tasks[id]
    if !ok {
        return Task{}, ErrNotFound
    }
    return t, nil
}
```

Returns a value copy (Go map access returns a copy of the value). Safe for concurrent use under the existing mutex.

### `UpdatePriority`

```go
func (m *MemoryStore) UpdatePriority(id string, priority int) error {
    m.mu.Lock()
    defer m.mu.Unlock()
    t, ok := m.tasks[id]
    if !ok {
        return ErrNotFound
    }
    t.Priority = priority
    m.tasks[id] = t
    return nil
}
```

Read-modify-write under a single mutex hold. Atomic — no window for concurrent modification between read and write.

---

## Command: `tq priority`

### Usage

```
tq priority <task-id> <new-priority>
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `<task-id>` | yes | 8-char hex task ID |
| `<new-priority>` | yes | Integer (any value, no bounds) |

No flags beyond the inherited `--json`. Two positional arguments via `cobra.ExactArgs(2)`.

### Behavior

1. Parse `args[1]` as integer via `strconv.Atoi`. Error if not a valid integer.
2. Call `store.Get(args[0])` to retrieve the task and capture the old priority.
3. Call `store.UpdatePriority(args[0], newPriority)` to apply the change.
4. Print result (old → new priority) to stdout.

Step 2 serves dual purpose: validates the task exists (returning a clear error if not) and captures the old priority for output. There is a theoretical race between `Get` and `UpdatePriority` where another process could change the priority between the two calls — this is acceptable for a local CLI where concurrent priority updates to the same task are not a realistic scenario.

### Output

**Default (text):**

```
a1b2c3d4  5 -> 10
```

Format: `fmt.Fprintf(w, "%s\t%d -> %d\n", id, oldPriority, newPriority)`

Same priority (idempotent): still prints the result, e.g. `a1b2c3d4  5 -> 5`. Not an error.

**JSON (`--json`):**

```json
{"id":"a1b2c3d4","old_priority":5,"new_priority":10}
```

JSON struct:

```go
type PriorityResult struct {
    ID          string `json:"id"`
    OldPriority int    `json:"old_priority"`
    NewPriority int    `json:"new_priority"`
}
```

### Errors

| Condition | Message | Exit |
|---|---|---|
| Task not found | `tq: cannot reprioritize task "<id>": not found` | 1 |
| Invalid priority | `tq: cannot reprioritize task "<id>": priority must be an integer` | 1 |
| Wrong arg count | Cobra usage error | 2 |

Priority validation happens before the store call — `strconv.Atoi` failure short-circuits before touching the store.

Errors return from `RunE`. No `os.Exit` in command logic.

### Testability

Injectable function:

```go
func runPriorityWithStore(s store.Store, id string, priorityStr string, jsonOut bool, w io.Writer) error
```

The `RunE` function creates the store and delegates:

```go
func runPriority(cmd *cobra.Command, args []string) error {
    s := store.NewMemoryStore()
    defer s.Close()
    return runPriorityWithStore(s, args[0], args[1], jsonOutput, os.Stdout)
}
```

---

## Testing

### Store Tests (`store/memory_test.go`)

| Test | What it verifies |
|---|---|
| `TestGet` | Add task, get by ID, all fields match |
| `TestGetNotFound` | Get nonexistent ID returns `ErrNotFound` |
| `TestUpdatePriority` | Add at priority 5, update to 10, get and verify priority changed |
| `TestUpdatePriorityNotFound` | Update nonexistent ID returns `ErrNotFound` |

### Command Tests (`cmd/priority_test.go`)

| Test | Setup | Action | Verify |
|---|---|---|---|
| `TestPriority` | Seed task at priority 5 | Reprioritize to 10 | Text output: `<id>\t5 -> 10` |
| `TestPriorityJSON` | Seed task at priority 5 | Reprioritize to 10, `--json` | JSON: `{"id":"...","old_priority":5,"new_priority":10}` |
| `TestPriorityNotFound` | Empty store | Reprioritize `"deadbeef"` | Error: `cannot reprioritize task "deadbeef": not found` |
| `TestPriorityInvalidInt` | Seed task | Reprioritize to `"high"` | Error: `priority must be an integer` |
| `TestPriorityRunningTask` | Seed task in `StateRunning` | Reprioritize to 10 | Success (no error), output shows change |
| `TestPriorityIdempotent` | Seed task at priority 5 | Reprioritize to 5 | Success, output: `<id>\t5 -> 5` |

All tests use `seedStore` + `runPriorityWithStore` injection pattern.

---

## Conventions

All conventions from previous specs remain. Additional conventions for this feature:

- **Error messages:** `tq: cannot reprioritize task "<id>": <reason>` — verb is `reprioritize`, noun is `task "<id>"`.
- **Output:** Text shows `<id>\t<old> -> <new>`. JSON shows `PriorityResult` struct with `old_priority`, `new_priority`.
- **Idempotent:** Reprioritizing to the same value is not an error — prints the (unchanged) result.
- **State-agnostic:** Priority changes succeed in any state. Priority is metadata, not execution state.
- **No bounds:** Priority accepts any integer, matching `tq add --priority` behavior.
- **No flags:** Command uses two positional args, no command-specific flags. Only inherited `--json`.
- **Exit codes:** 0 for success, 1 for errors, 2 for usage (Cobra).
- **Errors from RunE:** Return errors, never call `os.Exit` in command logic.
- **Package boundaries:** `cmd/` imports `store/`. `store/` imports only stdlib.

## Risks

1. **Interface expansion breaks compilation.** Adding `Get` and `UpdatePriority` to the `Store` interface means `MemoryStore` must be updated in the same step. Both must land together.

2. **ErrNotFound message divergence.** This spec uses `"not found"`. The watch spec uses `"task not found"`. When both are implemented, unify to one. Low risk — sentinel errors are compared with `errors.Is`, not string matching.

3. **Race between Get and UpdatePriority.** A concurrent process could change priority between the `Get` (to read old priority) and `UpdatePriority` (to write new priority). For a local CLI with no concurrent priority updates expected, this is acceptable. If atomicity is ever needed, a `CompareAndSwapPriority(id, oldPri, newPri)` method would solve it — not needed now.

4. **No BoltDB implementation.** This spec only implements `MemoryStore`. When BoltDB lands (watch prerequisite), `Get` and `UpdatePriority` need BoltDB implementations. The command code doesn't change — it talks to the `Store` interface.

5. **No scheduler exists yet.** The operator asked about updating the scheduler's priority queue atomically. There is no scheduler in the codebase — storage-layer atomicity is what this spec delivers. When the scheduler is built, it will need to either re-read priorities from the store on each scheduling decision (simplest — priority changes take effect on the next scheduling cycle) or expose a method to re-prioritize in-flight queue entries (only needed if sub-second priority propagation matters).
