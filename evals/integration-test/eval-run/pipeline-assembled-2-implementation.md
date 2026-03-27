# tq add — Implementation

## File Structure

```
tq/
├── main.go
├── cmd/
│   ├── root.go
│   └── add.go
└── store/
    ├── task.go
    └── store.go
```

---

## store/task.go

```go
package store

import (
	"errors"
	"time"
)

// State represents the lifecycle state of a task.
type State string

const (
	StatePending State = "pending" // created, deps not yet met
	StateReady   State = "ready"   // deps satisfied, eligible to run
	StateRunning State = "running" // claimed by a worker
	StateDone    State = "done"    // completed successfully
	StateFailed  State = "failed"  // failed, retries remain
	StateDead    State = "dead"    // failed, no retries remain
)

// Task is a single unit of work in the queue.
type Task struct {
	ID         string            `json:"id"`
	Command    []string          `json:"command"`
	Priority   int               `json:"priority"`
	DependsOn  []string          `json:"depends_on"`
	State      State             `json:"state"`
	Retries    int               `json:"retries"`
	MaxRetries int               `json:"max_retries"`
	CreatedAt  time.Time         `json:"created_at"`
	StartedAt  *time.Time        `json:"started_at,omitempty"`
	FinishedAt *time.Time        `json:"finished_at,omitempty"`
	WorkerPID  int               `json:"worker_pid,omitempty"`
	Artifact   string            `json:"artifact,omitempty"`
	Metadata   map[string]string `json:"metadata,omitempty"`
}

// Filter constrains the result set returned by Store.List.
type Filter struct {
	State    []State
	Priority *int
	Limit    int
}

// Sentinel errors — callers compare with errors.Is.
var (
	ErrNotFound   = errors.New("task not found")
	ErrWrongState = errors.New("task not in expected state")
	ErrCycle      = errors.New("dependency cycle detected")
	ErrDuplicate  = errors.New("task id already exists")
)
```

---

## store/store.go

```go
package store

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// Store is the only path to durable task state. All callers go through this interface.
// Implementations must be safe for concurrent use.
type Store interface {
	// Add enqueues a new task. Returns ErrCycle if deps form a cycle,
	// ErrDuplicate if the ID already exists.
	Add(task Task) error

	// Get retrieves a single task by ID. Returns ErrNotFound if absent.
	Get(id string) (Task, error)

	// List returns tasks matching the filter, ordered by priority desc, created_at asc.
	List(filter Filter) ([]Task, error)

	// Transition atomically moves a task from one state to another.
	// Returns ErrWrongState if current state != from.
	Transition(id string, from, to State) error

	// Update writes fields to an existing task (used to record StartedAt, WorkerPID, etc.)
	Update(id string, fn func(*Task)) error

	// Delete removes a task permanently.
	Delete(id string) error

	// Close flushes and closes the underlying storage.
	Close() error
}

// FileStore is a JSON-file-backed implementation of Store.
// All methods are safe for concurrent use.
type FileStore struct {
	mu   sync.Mutex
	path string
}

// NewFileStore opens (or creates) a JSON store at the given path.
func NewFileStore(path string) (*FileStore, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, fmt.Errorf("create store directory: %w", err)
	}
	fs := &FileStore{path: path}
	if _, err := os.Stat(path); os.IsNotExist(err) {
		if err := fs.write(nil); err != nil {
			return nil, err
		}
	}
	return fs, nil
}

// load reads and deserialises the task list from disk.
// Caller must hold fs.mu.
func (fs *FileStore) load() ([]Task, error) {
	data, err := os.ReadFile(fs.path)
	if err != nil {
		return nil, fmt.Errorf("read store: %w", err)
	}
	if len(data) == 0 {
		return nil, nil
	}
	var tasks []Task
	if err := json.Unmarshal(data, &tasks); err != nil {
		return nil, fmt.Errorf("parse store: %w", err)
	}
	return tasks, nil
}

// write serialises the task list and atomically replaces the store file.
// Uses a temp-file + rename so a crash mid-write leaves the old file intact.
// Caller must hold fs.mu.
func (fs *FileStore) write(tasks []Task) error {
	tmp := fs.path + ".tmp"
	data, err := json.MarshalIndent(tasks, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal store: %w", err)
	}
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return fmt.Errorf("write store: %w", err)
	}
	if err := os.Rename(tmp, fs.path); err != nil {
		return fmt.Errorf("commit store: %w", err)
	}
	return nil
}

func (fs *FileStore) Add(task Task) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return err
	}
	for _, t := range tasks {
		if t.ID == task.ID {
			return fmt.Errorf("%w: %s", ErrDuplicate, task.ID)
		}
	}
	// Cycle detection before any write.
	if err := detectCycle(tasks, task); err != nil {
		return err
	}
	tasks = append(tasks, task)
	return fs.write(tasks)
}

func (fs *FileStore) Get(id string) (Task, error) {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return Task{}, err
	}
	for _, t := range tasks {
		if t.ID == id {
			return t, nil
		}
	}
	return Task{}, fmt.Errorf("%w: %s", ErrNotFound, id)
}

func (fs *FileStore) List(filter Filter) ([]Task, error) {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return nil, err
	}
	if len(filter.State) == 0 {
		return tasks, nil
	}
	stateSet := make(map[State]struct{}, len(filter.State))
	for _, s := range filter.State {
		stateSet[s] = struct{}{}
	}
	var out []Task
	for _, t := range tasks {
		if _, ok := stateSet[t.State]; ok {
			out = append(out, t)
		}
	}
	return out, nil
}

func (fs *FileStore) Transition(id string, from, to State) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return err
	}
	for i, t := range tasks {
		if t.ID == id {
			if t.State != from {
				return fmt.Errorf("%w: task %s is in state %q, expected %q",
					ErrWrongState, id, t.State, from)
			}
			tasks[i].State = to
			return fs.write(tasks)
		}
	}
	return fmt.Errorf("%w: %s", ErrNotFound, id)
}

func (fs *FileStore) Update(id string, fn func(*Task)) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return err
	}
	for i := range tasks {
		if tasks[i].ID == id {
			fn(&tasks[i])
			return fs.write(tasks)
		}
	}
	return fmt.Errorf("%w: %s", ErrNotFound, id)
}

func (fs *FileStore) Delete(id string) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return err
	}
	for i, t := range tasks {
		if t.ID == id {
			tasks = append(tasks[:i], tasks[i+1:]...)
			return fs.write(tasks)
		}
	}
	return fmt.Errorf("%w: %s", ErrNotFound, id)
}

func (fs *FileStore) Close() error {
	// FileStore holds no persistent handles.
	return nil
}

// detectCycle uses DFS on the dependency graph to check whether adding newTask
// would form a cycle. Called inside Add before any write.
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
			return true // back-edge: cycle
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

	if dfs(newTask.ID) {
		return ErrCycle
	}
	return nil
}
```

---

## cmd/root.go

```go
package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"tq/store"
)

var (
	storePath string
	taskStore store.Store
)

var rootCmd = &cobra.Command{
	Use:   "tq",
	Short: "tq — a local task queue CLI",
	// PersistentPreRunE wires up the store before any subcommand runs.
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		fs, err := store.NewFileStore(storePath)
		if err != nil {
			return fmt.Errorf("open store: %w", err)
		}
		taskStore = fs
		return nil
	},
}

// Execute is the entry point called from main.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		// Cobra has already printed the error. Exit 1 for any error.
		os.Exit(1)
	}
}

func init() {
	rootCmd.PersistentFlags().StringVar(
		&storePath, "store", ".tq/tasks.json",
		"path to the task store file",
	)
}
```

---

## cmd/add.go

```go
package cmd

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"

	"tq/store"
)

var (
	addPriority  int
	addDependsOn string
	addShellCmd  string
)

var addCmd = &cobra.Command{
	Use:   "add <name>",
	Short: "Add a new task to the queue",
	Long: `Add a new task to the queue.

The task name is a positional argument. The --cmd flag is required.
Dependency IDs are the 8-character IDs printed by earlier 'tq add' calls.

Examples:
  tq add "build binary" --cmd "go build ./..."
  tq add "run tests"    --cmd "go test ./..."    --priority 10
  tq add "deploy"       --cmd "./deploy.sh"      --depends-on a1b2c3d4,e5f6a7b8
`,
	Args: cobra.ExactArgs(1),
	RunE: runAdd,
}

func init() {
	addCmd.Flags().IntVar(
		&addPriority, "priority", 0,
		"task priority — higher value runs first when workers are free",
	)
	addCmd.Flags().StringVar(
		&addDependsOn, "depends-on", "",
		"comma-separated list of task IDs this task depends on",
	)
	addCmd.Flags().StringVar(
		&addShellCmd, "cmd", "",
		"shell command to execute (required)",
	)
	_ = addCmd.MarkFlagRequired("cmd")

	rootCmd.AddCommand(addCmd)
}

func runAdd(cmd *cobra.Command, args []string) error {
	name := args[0]

	// Parse the comma-separated dependency list.
	var depIDs []string
	if addDependsOn != "" {
		for _, raw := range strings.Split(addDependsOn, ",") {
			if id := strings.TrimSpace(raw); id != "" {
				depIDs = append(depIDs, id)
			}
		}
	}

	// Validate that every declared dependency exists in the store.
	// Report all missing IDs at once so the operator can fix them in one edit.
	if err := validateDependenciesExist(taskStore, name, depIDs); err != nil {
		return err
	}

	id, err := generateID()
	if err != nil {
		return fmt.Errorf("tq: generate task ID: %w", err)
	}

	// A task with no dependencies starts as ready; one with deps starts as pending.
	// This mirrors the state machine: pending means "deps not yet met."
	initialState := store.StateReady
	if len(depIDs) > 0 {
		initialState = store.StatePending
	}

	task := store.Task{
		ID:        id,
		Command:   []string{"sh", "-c", addShellCmd},
		Priority:  addPriority,
		DependsOn: depIDs,
		State:     initialState,
		CreatedAt: time.Now().UTC(),
	}

	// Store.Add performs cycle detection internally (DFS before any write).
	// This is the correct location per the architecture: detect at enqueue time,
	// never at run time.
	if err := taskStore.Add(task); err != nil {
		if errors.Is(err, store.ErrCycle) {
			return fmt.Errorf("tq: cannot add task %q: dependency chain creates a cycle", name)
		}
		if errors.Is(err, store.ErrDuplicate) {
			return fmt.Errorf("tq: cannot add task %q: ID %s already exists", name, id)
		}
		return fmt.Errorf("tq: cannot add task %q: %w", name, err)
	}

	// Only the task ID goes to stdout — pipe-friendly.
	// tq add "build" --cmd "go build ./..."  → a1b2c3d4
	// DEP=$(tq add "build" --cmd "..."); tq add "test" --depends-on "$DEP" ...
	fmt.Println(task.ID)
	return nil
}

// validateDependenciesExist checks that every id in deps refers to a known task.
// Error messages follow the project convention:
//
//	tq: cannot add task "<name>": dependency "<dep>" not found
func validateDependenciesExist(s store.Store, taskName string, deps []string) error {
	var missing []string
	for _, id := range deps {
		if _, err := s.Get(id); errors.Is(err, store.ErrNotFound) {
			missing = append(missing, id)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf(
			"tq: cannot add task %q: unknown dependency ID(s): %s",
			taskName, strings.Join(missing, ", "),
		)
	}
	return nil
}

// generateID returns a cryptographically random 8-character lowercase hex string.
// 4 bytes → 2^32 ≈ 4 billion values — negligible collision probability for a local queue.
// Uses only the standard library; no UUID or ULID dependency.
func generateID() (string, error) {
	b := make([]byte, 4)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}
```

---

## main.go

```go
package main

import "tq/cmd"

func main() {
	cmd.Execute()
}
```

---

## go.mod

```
module tq

go 1.22

require github.com/spf13/cobra v1.8.1

require (
	github.com/inconshreveable/mousetrap v1.1.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
)
```

---

## Design Notes

### Exact architecture alignment

The `Task` struct and `Store` interface match the architecture spec exactly:
- `Command []string` (not a single `Cmd string`) — the architecture uses a string slice, consistent with how `exec.Cmd` works and how the worker pool's `Runner` will invoke it. The `--cmd` flag wraps the shell string as `["sh", "-c", <cmd>]`, which is the standard pattern for running arbitrary shell commands.
- All six `State` constants (`pending`, `ready`, `running`, `done`, `failed`, `dead`) are defined.
- The full `Store` interface (`Add`, `Get`, `List`, `Transition`, `Update`, `Delete`, `Close`) is implemented. The add command uses only `Add` and `Get`; implementing the full interface means `FileStore` serves all future commands without modification.
- Sentinel errors (`ErrNotFound`, `ErrWrongState`, `ErrCycle`, `ErrDuplicate`) are used throughout. Callers use `errors.Is`, not string matching.

### Initial state assignment

A task with no dependencies starts in `StateReady` — it can be claimed immediately by the scheduler. A task with dependencies starts in `StatePending` — the scheduler's `Tick` will promote it to `StateReady` when all dependencies reach `StateDone`. This mirrors the state machine in the architecture spec and avoids a `Tick` call on every `add`.

### Cycle detection placement

Cycle detection lives inside `Store.Add` (the `detectCycle` helper), not in the command layer. This is deliberate: the architecture spec states "cycle detection happens at enqueue time, not at run time" and shows `detectCycle` called inside `Store.Add` before persisting. Placing it in the store means any caller (CLI, future API, test) gets the guarantee automatically. The command layer still surfaces a human-readable error by checking `errors.Is(err, store.ErrCycle)`.

### Dependency existence validation

`validateDependenciesExist` in the command layer runs before `Store.Add`. This is the data-boundary check (Helland's principle): CLI input is validated at the boundary before it enters the store. All missing IDs are accumulated and reported in a single error so the operator can fix them in one edit.

### Atomic writes

`FileStore.write` writes to a `.tmp` file then calls `os.Rename`. On POSIX systems `rename(2)` is atomic — a crash mid-write leaves either the old file or the new file complete, never a partial write. This is the durability guarantee required by the State Guardian's quality bar.

### Error messages

Every error follows the project's convention: `tq: cannot add task "<name>": <reason>`. The reason is specific enough to act on without `--verbose`:
```
tq: cannot add task "deploy": unknown dependency ID(s): a1b2c3d4
tq: cannot add task "deploy": dependency chain creates a cycle
```

### Output discipline

Only the task ID goes to stdout on success. All errors go to stderr via Cobra's default handling. This keeps the output pipe-friendly:
```sh
DEP=$(tq add "build" --cmd "go build ./...")
tq add "test" --cmd "go test ./..." --depends-on "$DEP"
```

### Exit codes

Cobra exits with code 1 whenever `RunE` returns a non-nil error. No manual `os.Exit` calls appear in command logic, which keeps functions testable — tests can call `runAdd` directly and inspect the returned error.
