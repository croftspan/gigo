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

import "time"

// State represents the lifecycle state of a task.
type State string

const (
	StatePending State = "pending"
	StateRunning State = "running"
	StateDone    State = "done"
	StateFailed  State = "failed"
)

// Task is a single unit of work in the queue.
type Task struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Cmd       string    `json:"cmd"`
	Priority  int       `json:"priority"`
	DependsOn []string  `json:"depends_on"`
	State     State     `json:"state"`
	CreatedAt time.Time `json:"created_at"`
}

// Filter constrains the result set returned by Store.List.
type Filter struct {
	State *State // nil means all states
}
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

// Store is the interface all commands depend on.
// The add command requires Add, Get, and List.
type Store interface {
	// Add persists a task. Returns an error if a constraint is violated.
	Add(task Task) error

	// Get retrieves a single task by ID.
	// Returns (Task, true) when found, (Task{}, false) when absent.
	Get(id string) (Task, bool)

	// List returns tasks matching the filter.
	List(filter Filter) ([]Task, error)

	// Transition atomically moves a task from one state to another.
	Transition(id string, from, to State) error

	// Delete removes a task by ID.
	Delete(id string) error

	// Close flushes and closes the store.
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
	// Initialise the file with an empty array if it doesn't yet exist.
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

// write serialises and atomically replaces the store file.
// Caller must hold fs.mu.
func (fs *FileStore) write(tasks []Task) error {
	// Marshal to a temp file, then rename for atomicity.
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
			return fmt.Errorf("task with ID %q already exists", task.ID)
		}
	}
	tasks = append(tasks, task)
	return fs.write(tasks)
}

func (fs *FileStore) Get(id string) (Task, bool) {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return Task{}, false
	}
	for _, t := range tasks {
		if t.ID == id {
			return t, true
		}
	}
	return Task{}, false
}

func (fs *FileStore) List(filter Filter) ([]Task, error) {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, err := fs.load()
	if err != nil {
		return nil, err
	}
	if filter.State == nil {
		return tasks, nil
	}
	var out []Task
	for _, t := range tasks {
		if t.State == *filter.State {
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
				return fmt.Errorf("task %q is in state %q, expected %q", id, t.State, from)
			}
			tasks[i].State = to
			return fs.write(tasks)
		}
	}
	return fmt.Errorf("task %q not found", id)
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
	return fmt.Errorf("task %q not found", id)
}

func (fs *FileStore) Close() error {
	// FileStore has no persistent handles to close.
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
	Short: "tq — a lightweight local task queue CLI",
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
		// Cobra has already printed the error message.
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

Examples:
  tq add "build binary"  --cmd "go build ./..."
  tq add "run tests"     --cmd "go test ./..."    --priority 10
  tq add "deploy"        --cmd "./deploy.sh"      --depends-on a1b2c3d4,e5f6a7b8
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
	if err := validateDependenciesExist(taskStore, name, depIDs); err != nil {
		return err
	}

	id, err := generateID()
	if err != nil {
		return fmt.Errorf("tq: generate task ID: %w", err)
	}

	task := store.Task{
		ID:        id,
		Name:      name,
		Cmd:       addShellCmd,
		Priority:  addPriority,
		DependsOn: depIDs,
		State:     store.StatePending,
		CreatedAt: time.Now().UTC(),
	}

	// Cycle detection runs before Add so the store is never left inconsistent.
	if err := validateNoCycle(taskStore, task); err != nil {
		return err
	}

	if err := taskStore.Add(task); err != nil {
		return fmt.Errorf("tq: cannot add task %q: %w", name, err)
	}

	// Only the ID goes to stdout — machine-readable, pipe-friendly.
	fmt.Println(task.ID)
	return nil
}

// validateDependenciesExist checks that every id in deps refers to a known task.
// It accumulates all missing IDs so the user can fix them in one pass.
func validateDependenciesExist(s store.Store, taskName string, deps []string) error {
	var missing []string
	for _, id := range deps {
		if _, ok := s.Get(id); !ok {
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

// validateNoCycle detects whether adding candidate to the store would introduce
// a dependency cycle. It builds a provisional adjacency list (existing tasks +
// candidate) and runs DFS with a recursion-stack marker.
//
// The graph edge direction is: task → its dependencies.
// A cycle exists if DFS from the candidate can reach the candidate again.
func validateNoCycle(s store.Store, candidate store.Task) error {
	all, err := s.List(store.Filter{})
	if err != nil {
		return fmt.Errorf("tq: load tasks for cycle check: %w", err)
	}

	// Build adjacency list.
	adj := make(map[string][]string, len(all)+1)
	for _, t := range all {
		adj[t.ID] = t.DependsOn
	}
	adj[candidate.ID] = candidate.DependsOn

	visited := make(map[string]bool)
	inStack := make(map[string]bool)

	var dfs func(node string) bool
	dfs = func(node string) bool {
		if inStack[node] {
			return true // back-edge: cycle
		}
		if visited[node] {
			return false // already fully explored: no cycle via this node
		}
		visited[node] = true
		inStack[node] = true
		for _, dep := range adj[node] {
			if dfs(dep) {
				return true
			}
		}
		inStack[node] = false
		return false
	}

	if dfs(candidate.ID) {
		return errors.New(
			"tq: cannot add task: dependency chain creates a cycle",
		)
	}
	return nil
}

// generateID returns a cryptographically random 8-character lowercase hex string.
// 4 bytes → 2^32 ≈ 4 billion values, sufficient for a local task queue.
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

### ID generation

`generateID` reads 4 bytes from `crypto/rand` and hex-encodes them, producing an 8-character lowercase string with 2^32 (~4 billion) possible values. For a local task queue this collision probability is negligible. The approach uses only the standard library; no UUID or ULID dependency is required.

### Dependency existence validation

`validateDependenciesExist` calls `Store.Get` for every declared dependency ID before the task is written. All missing IDs are accumulated and reported together so the operator can resolve them in a single edit rather than iterating one error at a time. The error message follows the project's error-message convention: `tq: cannot add task "<name>": <reason>`.

### Cycle detection

`validateNoCycle` runs before `Store.Add` so the store is never left in an inconsistent state. It builds an in-memory adjacency list from `Store.List` plus the candidate task, then runs DFS with a `visited` set and an `inStack` set. The `inStack` marker detects back-edges (the classical cycle indicator in a directed graph). Starting DFS from the candidate node means it only walks paths reachable from the new task, keeping the check O(V+E) in the relevant subgraph.

### Store interface alignment

The `Store` interface is the full interface specified in the project's CLAUDE.md (`Add`, `Get`, `List`, `Transition`, `Delete`, `Close`). The add command uses only `Add`, `Get`, and `List`. Using the full interface rather than a narrower one keeps `FileStore` as the single implementation for all future commands. Tests can supply an in-memory stub that satisfies the same interface.

### Atomic writes

`FileStore.write` marshals to a `.tmp` file and renames it over the target. On POSIX systems `rename(2)` is atomic, so a power failure mid-write leaves either the old file intact or the new file complete — never a partial write. This is the durability guarantee required by the State Guardian's quality bar.

### Exit codes

Cobra exits with code 1 whenever `RunE` returns a non-nil error; `rootCmd.Execute()` in `main` propagates this via `os.Exit(1)`. Success exits with code 0 automatically. No manual `os.Exit` calls appear in command logic, keeping the code testable.

### Output discipline

Only the task ID is written to stdout on success, making the output pipe-friendly:

```sh
DEP=$(tq add "build" --cmd "go build ./...")
tq add "test" --cmd "go test ./..." --depends-on "$DEP"
```

All errors go to stderr via Cobra's default error handling.
