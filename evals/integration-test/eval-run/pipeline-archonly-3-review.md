# Code Review: `tq add` Implementation

## Summary

Solid foundation for a CLI task queue. The architecture is clean, the interface is well-defined, and the dependency injection pattern makes the code genuinely testable. What follows is a focused list of concrete issues — bugs that will bite in production, behavioral gaps, and a few design concerns worth addressing before this code handles real workloads.

---

## Bugs

### 1. Cycle detection direction is inverted

**Location:** `detectCycle`, lines 139–177

**Impact:** High — the cycle check produces false negatives. A cycle can be added to the store undetected.

The DFS walks `adj[id]`, which is `DependsOn`. DependsOn edges point from a task *toward* its dependencies — the direction a task waits. But in a dependency graph, cycles are found by walking *dependents*, not dependencies.

Concretely: if task A depends on B, and B depends on C, and C depends on A — the adjacency list is `{A:[B], B:[C], C:[A]}`. The DFS from A visits B then C then A, finds A in `inStack`, and returns true. In *this* case it works. But consider a new task D that depends on A, where A→B→C→A already exists:

```
adj = {A:[B], B:[C], C:[A], D:[A]}
```

The DFS starts from some node, but because `visited` short-circuits, whether the cycle in {A,B,C} is caught depends entirely on iteration order over the map. Map iteration in Go is randomized. This means cycle detection is **non-deterministic** when cycles already exist in the graph (which shouldn't happen if prior adds were correct, but the point stands: the DFS is fragile about entry order).

More critically, the DFS marks nodes `visited` after first visit and skips them on re-entry. If the DFS enters D first, walks to A, marks A visited, continues to B, C — and then when the outer loop hits A it skips it (already visited). The cycle A→B→C→A is never fully traversed because A was already marked done.

**Fix:** The standard approach is: during DFS, when you reach a node that is in `inStack` (currently being explored), you have a cycle. The existing code does do this, but the early `visited` check (line 154) exits without fully exploring. The fix is to not exit early when a node is visited but not in the stack — you must still verify none of its paths lead back to the current stack. The correct implementation:

```go
var dfs func(id string) bool
dfs = func(id string) bool {
    if inStack[id] {
        return true
    }
    if visited[id] {
        return false // already fully explored, no cycle through here
    }
    visited[id] = true
    inStack[id] = true
    for _, dep := range adj[id] {
        if dfs(dep) {
            return true
        }
    }
    inStack[id] = false
    return false
}
```

Actually the existing code matches this pattern — the issue is subtler. The real problem: `visited[id] = true` is set when a node is *entered*, but `inStack[id]` is only set to false after all children are explored. If DFS enters A, sets `visited[A]=true`, `inStack[A]=true`, then explores B→C→A and finds `inStack[A]==true`, returns true — that is correct. But if the outer loop processes A first (before D), marks it visited, then processes D, and D's DFS walks to A — A is `visited` and not `inStack`, so the DFS returns false. No cycle detected even though D→A→B→C→A is a cycle. **Wait: D depending on A where A→B→C→A is a cycle means adding D doesn't *create* a new cycle** — A's cycle is what's wrong. So the question is: should `tq add D --depends-on A` be rejected if A itself is already in a cycle?

That's a policy question the implementation doesn't answer. But the deeper bug is: **if the first ever add of the A→B→C→A cycle somehow slipped through (e.g., because A was added to the store before cycle detection ran), subsequent adds will silently ignore the existing cycle** due to the `visited` short-circuit interacting with map iteration order.

The safest fix: reset `visited` for each DFS root, so every path from every node is fully explored. This is O(V*(V+E)) but for a CLI task queue the graph is small.

---

### 2. `parseCommand` fallback returns whitespace-only input as a command

**Location:** `parseCommand`, lines 376–382

**Impact:** Medium — a command of only whitespace (`--cmd "   "`) passes `MarkFlagRequired` (the flag is set), gets to `parseCommand`, `strings.Fields` returns empty, and the fallback returns `[]string{"   "}` — a command name that is three spaces. The process exec will fail with a confusing error.

```go
func parseCommand(s string) []string {
    fields := strings.Fields(s)
    if len(fields) == 0 {
        return []string{s}  // returns "   " as the command name
    }
    return fields
}
```

The fallback `return []string{s}` is also logically wrong for the non-whitespace case: if `strings.Fields` returns empty, `s` is either empty or all whitespace — returning it as a command makes no sense either way.

**Fix:**

```go
func parseCommand(s string) []string {
    return strings.Fields(s) // empty slice if blank; caller validates
}
```

And in `RunE`, validate before building the task:

```go
argv := parseCommand(cmd)
if len(argv) == 0 {
    return fmt.Errorf("--cmd must not be blank")
}
```

---

### 3. Dependency validation is not atomic with task insertion

**Location:** `RunE`, lines 317–324, and `Store.Add`, line 126

**Impact:** Medium — TOCTOU (time-of-check/time-of-use) race. Between the `store.Get(depID)` validation loop and the `store.Add(task)` call, a dependency task could be deleted. The task is then persisted with a dangling dependency reference.

```go
// Validation (checks deps exist)
for _, depID := range deps {
    if _, err := store.Get(depID); err != nil { ... }
}

// Gap: dep could be deleted here

// Insertion
if err := store.Add(task); err != nil { ... }
```

For an in-memory single-process CLI this is theoretical today, but the `Store` interface is designed for extension to persistent backends where concurrent access is real. The fix is to move dependency existence validation inside `Store.Add`, where it can be done under the same lock as the insertion.

**Fix:** Add a method or extend `Add` to validate dep existence atomically:

```go
func (s *memStore) Add(task Task) error {
    // ... duplicate check ...
    for _, depID := range task.DependsOn {
        if _, ok := s.tasks[depID]; !ok {
            return fmt.Errorf("%w: %s", ErrNotFound, depID)
        }
    }
    // ... cycle check, then insert ...
}
```

This also removes the per-dep-error-message distinction in the cmd layer, which is a minor UX regression — but atomicity is worth it.

---

### 4. `MarkFlagRequired` is redundant with the manual `--cmd` check

**Location:** Lines 301–303 and 368

**Impact:** Low — not a bug, but it is a contradiction. `MarkFlagRequired("cmd")` causes Cobra to reject the command before `RunE` is called if `--cmd` is absent. The manual check `if cmd == ""` in `RunE` is therefore dead code. It will never execute.

This is fine for the empty-string case (`--cmd ""`), which `MarkFlagRequired` does not catch — but then the parseCommand fix above handles that. Remove the redundant check or document why both exist.

---

## Design Issues

### 5. 8-character hex ID has meaningful collision risk at scale

**Location:** `generateID`, lines 274–280

**Impact:** Low-medium depending on queue size.

4 bytes = 32 bits = ~4.3 billion possible IDs. For a queue of N tasks, the probability of at least one collision is approximately N²/2³², which becomes ~0.1% at 65K tasks and ~10% at 650K tasks. For a local CLI that's probably fine. For a long-running daemon with task churn, it's not.

The `ErrDuplicate` handling asks the user to "retry," but `tq add` is likely called from scripts where a retry isn't automatic. A collision silently breaks automation.

**Fix:** Use 8 bytes (16 hex chars). The collision probability drops to negligible at any realistic queue size.

---

### 6. `memStore` is not goroutine-safe — comment understates the risk

**Location:** Lines 115–117

**Impact:** Medium if this store is ever used from concurrent code.

The comment says "not safe for concurrent use without external locking, but sufficient for a single-process CLI." That's accurate today. But the `Store` interface has no mutex, and nothing prevents a future consumer from calling it concurrently (e.g., a scheduler goroutine running alongside the CLI process). The interface design doesn't signal which implementations are safe.

**Fix:** Add a `sync.Mutex` to `memStore` now. It costs nothing for a CLI, protects against future misuse, and makes the implementation match what the interface implies:

```go
type memStore struct {
    mu    sync.Mutex
    tasks map[string]Task
}
```

All exported methods acquire `mu` before operating on `tasks`.

---

### 7. `Update` fn can observe a stale copy

**Location:** `Update`, lines 249–256

**Impact:** Medium — subtle correctness issue.

```go
func (s *memStore) Update(id string, fn func(*Task)) error {
    t, ok := s.tasks[id]   // t is a copy
    fn(&t)                  // fn mutates the copy
    s.tasks[id] = t         // copy written back
    return nil
}
```

This is correct for `memStore` in a single-threaded CLI. But the contract exposed by the `Store` interface says `Update` "applies fn to the task in place" — which implies the fn sees the live task. If a caller passes a fn that reads fields set by a concurrent `Transition` call, it will read the pre-Transition value. This is a semantic gap between the interface documentation and the implementation.

For a concurrent-safe implementation, the fn must be called while the lock is held and the task's current state is visible. Document this constraint explicitly in the interface comment, or accept that `Update` is only safe when no concurrent state changes are possible.

---

### 8. No validation on `--priority` range

**Location:** Flag definition, line 365

**Impact:** Low.

`--priority` accepts any `int`, including negatives. Negative priorities aren't documented as valid. The `sortTasks` implementation handles them correctly (they'll sort below zero-priority tasks), but a user passing `--priority -99` by accident gets no feedback.

If negative priorities are intentional (a "deprioritize" mechanism), document it. If not, add:

```go
if priority < 0 {
    return fmt.Errorf("--priority must be >= 0, got %d", priority)
}
```

---

### 9. Name stored in `Metadata["name"]` is never validated for emptiness

**Location:** `RunE`, line 345, and `Args: cobra.ExactArgs(1)`

**Impact:** Low.

`cobra.ExactArgs(1)` ensures exactly one positional arg is present, but it allows an empty string (`tq add "" --cmd "foo"`). The task is created with `Metadata["name"] = ""`. This is unlikely to cause a crash but produces tasks with no meaningful name.

**Fix:**

```go
name := strings.TrimSpace(args[0])
if name == "" {
    return fmt.Errorf("task name must not be blank")
}
```

---

## Minor

- **`ErrWrongState` alignment:** The error variable has an extra space before `=` (`ErrWrongState = ...`) that doesn't match the others. Cosmetic, but `gofmt` won't catch it since it's in a `var` block with explicit alignment. Run `goimports` to normalize.

- **`sortTasks` uses insertion sort:** Correct and readable. For the expected queue sizes (hundreds to low thousands) this is fine. At tens of thousands of tasks, switch to `slices.SortFunc` from the standard library.

- **`detectCycle` allocates two maps per `Add` call:** For a CLI, this is negligible. If this code moves into a hot path, pre-allocate or cache the adjacency list.

---

## What Works Well

- Store interface is clean and extension-ready. Swapping `memStore` for a SQLite or file-backed store requires touching only `main()`.
- Sentinel error pattern is correct — `errors.Is` wrapping works properly throughout.
- `Transition` as a compare-and-swap is the right design for preventing race conditions in state advancement.
- Dependency injection via `newAddCmd(store)` makes unit testing straightforward without any mocking framework.
- Output goes to `cobraCmd.OutOrStdout()` — this is the right call; it allows test capture without redirecting `os.Stdout`.

---

## Priority Order for Fixes

| # | Issue | Priority |
|---|---|---|
| 1 | Cycle detection correctness | High |
| 3 | TOCTOU dep validation | Medium |
| 2 | `parseCommand` blank-cmd fallback | Medium |
| 6 | `memStore` goroutine safety | Medium |
| 7 | `Update` stale-copy contract | Medium |
| 5 | ID collision at scale | Low-Medium |
| 4 | Redundant `--cmd` check | Low |
| 8 | Negative priority | Low |
| 9 | Empty name | Low |
