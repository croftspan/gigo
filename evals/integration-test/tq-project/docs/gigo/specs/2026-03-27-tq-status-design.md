# tq status — Design Spec

## Goal

Add a `tq status` command that reports queue status: task counts by state, queue health assessment. Works in pipelines (grep-friendly default, `--json` for machines).

## Architecture

Three packages, each with one responsibility:

```
tq-project/
├── main.go              # entry point — calls cmd.Execute()
├── go.mod               # module: tq
├── cmd/
│   ├── root.go          # root Cobra command, --json persistent flag
│   └── status.go        # status subcommand
└── store/
    ├── store.go          # Store interface, Task, State, Filter types
    └── memory.go         # MemoryStore — in-memory implementation
```

### Store Package (`store/`)

**Types:**

```go
type State string

const (
    StatePending State = "pending"
    StateReady   State = "ready"
    StateRunning State = "running"
    StateDone    State = "done"
    StateFailed  State = "failed"
    StateDead    State = "dead"
)

type Task struct {
    ID        string
    Name      string
    State     State
    Priority  int
    DependsOn []string
    CreatedAt time.Time
}

type Filter struct {
    State *State // nil means all states
}

type Store interface {
    Add(task Task) error
    List(filter Filter) ([]Task, error)
    Close() error
}
```

**MemoryStore:** Map-based (`map[string]Task`), `sync.Mutex`-protected. Implements `Store`. Supports `Add` and `List`. `Close` is a no-op.

- `Add` generates a short hex ID (8 chars from `crypto/rand`) if `task.ID` is empty
- `List` iterates all tasks, applies `Filter.State` if non-nil, returns a copy (not a reference to internal state)

### Command Package (`cmd/`)

**Root command (`root.go`):**

```go
var rootCmd = &cobra.Command{
    Use:   "tq",
    Short: "Local task queue CLI",
}

var jsonOutput bool

func init() {
    rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output as JSON")
}

func Execute() error {
    return rootCmd.Execute()
}
```

**Status command (`status.go`):**

`RunE` function:
1. Open the store (for now, create a new MemoryStore — no persistence yet)
2. Call `store.List(Filter{})` to get all tasks
3. Count tasks by state
4. Determine health
5. Format and print output

**Health logic:**

```go
func health(counts map[State]int) string {
    total := 0
    for _, c := range counts {
        total += c
    }
    switch {
    case total == 0:
        return "empty"
    case counts[StateDead] > 0:
        return "unhealthy"
    case counts[StateFailed] > 0:
        return "degraded"
    case counts[StateRunning] == 0 && counts[StateReady] == 0 && counts[StateDone] > 0:
        return "idle"
    default:
        return "healthy"
    }
}
```

### Entry Point (`main.go`)

```go
func main() {
    if err := cmd.Execute(); err != nil {
        os.Exit(1)
    }
}
```

Cobra prints the error to stderr. `main` only sets the exit code.

## Output Format

### Default (grep-friendly)

Tab-separated, one line per state, fixed order, then total and health:

```
pending     3
ready       5
running     2
done       12
failed      1
dead        0
total      23
health      healthy
```

Always print all states, even when count is 0. This makes output predictable for `grep` and `awk`.

Format: `fmt.Fprintf(os.Stdout, "%-10s%d\n", label, count)`. No tabwriter — fixed format string is simpler and grep-friendlier.

### JSON (`--json`)

```json
{"pending":3,"ready":5,"running":2,"done":12,"failed":1,"dead":0,"total":23,"health":"healthy"}
```

Single line. Use `encoding/json` with a struct, not `map[string]interface{}`. The struct ensures field order is stable:

```go
type StatusOutput struct {
    Pending  int    `json:"pending"`
    Ready    int    `json:"ready"`
    Running  int    `json:"running"`
    Done     int    `json:"done"`
    Failed   int    `json:"failed"`
    Dead     int    `json:"dead"`
    Total    int    `json:"total"`
    Health   string `json:"health"`
}
```

### Empty queue

Default:
```
pending     0
ready       0
running     0
done        0
failed      0
dead        0
total       0
health      empty
```

JSON:
```json
{"pending":0,"ready":0,"running":0,"done":0,"failed":0,"dead":0,"total":0,"health":"empty"}
```

Not an error. Exit code 0.

## Conventions

- **Error messages:** `tq: cannot read queue status: <reason>` — always `tq:` prefix, operation attempted, then reason
- **Output:** Default is tab-aligned text to stdout. Errors to stderr. Never mix data and diagnostics on the same stream.
- **Naming:** `State` not `Status` for the enum. Constants prefixed: `StatePending`, `StateReady`, etc.
- **Exit codes:** 0 for success (including empty queue), 1 for errors. Cobra handles usage errors (exit 2).
- **Flag naming:** `--json` not `--format json`. Boolean flag, persistent on root command so all future commands inherit it.
- **No ANSI:** No colors, no spinners, no formatting that assumes a terminal.
- **JSON struct:** Use a named struct with `json` tags, not `map[string]interface{}`. Stable field order.
- **Store access:** Commands get a `Store` — they never construct storage directly. For now, the status command creates a `MemoryStore` in `RunE`. This will be replaced by a factory when persistence lands.
- **Errors from RunE:** Return errors, never call `os.Exit` in command logic. Cobra handles error display.
- **Package boundaries:** `cmd/` imports `store/`. `store/` imports nothing from `cmd/`. `main.go` imports only `cmd/`.

## Testing

**Store tests (`store/memory_test.go`):**
- List with empty store returns empty slice, no error
- Add tasks, list all, verify counts
- List with state filter returns only matching tasks
- Add with empty ID generates an ID

**Status command test (`cmd/status_test.go`):**
- Use a MemoryStore pre-loaded with known tasks
- Verify default output matches expected format exactly (line by line)
- Verify `--json` output parses to correct StatusOutput struct
- Test each health state: empty, healthy, degraded, unhealthy, idle

Tests use `store.MemoryStore` directly — no mocks. The MemoryStore IS the test store.

## Risks

- **No persistence yet.** `tq status` on a fresh MemoryStore always shows zeros. This is correct behavior for now — the store is empty. When BoltDB lands, the status command works unchanged because it talks to the `Store` interface.
- **State list could change.** If states are added later, the `StatusOutput` struct and format need updating. Low risk — state machine is well-defined in persistence-patterns.md.
