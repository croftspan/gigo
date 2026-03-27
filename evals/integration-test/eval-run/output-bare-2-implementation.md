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

// Status represents the lifecycle state of a task.
type Status string

const (
	StatusPending  Status = "pending"
	StatusRunning  Status = "running"
	StatusDone     Status = "done"
	StatusFailed   Status = "failed"
)

// Task is a single unit of work in the queue.
type Task struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Cmd       string    `json:"cmd"`
	Priority  int       `json:"priority"`
	DependsOn []string  `json:"depends_on"`
	Status    Status    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
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

// Store is the interface the add command depends on.
type Store interface {
	// Add persists a task. Returns an error if the task already exists
	// or a constraint is violated.
	Add(task Task) error

	// Get retrieves a task by ID. Returns (task, true) when found.
	Get(id string) (Task, bool)

	// All returns every task in the store.
	All() []Task
}

// FileStore is a JSON-file-backed implementation of Store.
type FileStore struct {
	mu   sync.Mutex
	path string
}

// NewFileStore creates (or opens) a JSON store at the given path.
func NewFileStore(path string) (*FileStore, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, fmt.Errorf("create store dir: %w", err)
	}
	fs := &FileStore{path: path}
	// Touch the file if it doesn't exist yet.
	if _, err := os.Stat(path); os.IsNotExist(err) {
		if err := fs.write(nil); err != nil {
			return nil, err
		}
	}
	return fs, nil
}

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

func (fs *FileStore) write(tasks []Task) error {
	data, err := json.MarshalIndent(tasks, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal store: %w", err)
	}
	return os.WriteFile(fs.path, data, 0o644)
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

func (fs *FileStore) All() []Task {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	tasks, _ := fs.load()
	return tasks
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
	Short: "tq — a lightweight task queue CLI",
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
		// Cobra already prints the error; just exit 1.
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

var addCmd = &cobra.Command{
	Use:   "add <name>",
	Short: "Add a new task to the queue",
	Long: `Add a new task to the queue.

Examples:
  tq add "build binary" --cmd "go build ./..."
  tq add "run tests"    --cmd "go test ./..." --priority 10
  tq add "deploy"       --cmd "./deploy.sh"   --depends-on abc12345,def67890
`,
	Args: cobra.ExactArgs(1),
	RunE: runAdd,
}

var (
	addPriority  int
	addDependsOn string
	addCmd_      string
)

func init() {
	addCmd.Flags().IntVar(&addPriority, "priority", 0, "task priority (higher = more urgent)")
	addCmd.Flags().StringVar(&addDependsOn, "depends-on", "", "comma-separated list of task IDs this task depends on")
	addCmd.Flags().StringVar(&addCmd_, "cmd", "", "shell command to execute (required)")
	_ = addCmd.MarkFlagRequired("cmd")

	rootCmd.AddCommand(addCmd)
}

func runAdd(cmd *cobra.Command, args []string) error {
	name := args[0]

	// Parse dependency list.
	var depIDs []string
	if addDependsOn != "" {
		for _, raw := range strings.Split(addDependsOn, ",") {
			id := strings.TrimSpace(raw)
			if id != "" {
				depIDs = append(depIDs, id)
			}
		}
	}

	// Validate that every dependency ID exists in the store.
	if err := validateDependenciesExist(taskStore, depIDs); err != nil {
		return err
	}

	// Generate a unique 8-character hex ID.
	id, err := generateID()
	if err != nil {
		return fmt.Errorf("generate task ID: %w", err)
	}

	task := store.Task{
		ID:        id,
		Name:      name,
		Cmd:       addCmd_,
		Priority:  addPriority,
		DependsOn: depIDs,
		Status:    store.StatusPending,
		CreatedAt: time.Now().UTC(),
	}

	// Cycle detection: treat the store as a graph, add the new task
	// provisionally and check for reachability from itself.
	if err := validateNoCycle(taskStore, task); err != nil {
		return err
	}

	if err := taskStore.Add(task); err != nil {
		return fmt.Errorf("store task: %w", err)
	}

	fmt.Println(task.ID)
	return nil
}

// validateDependenciesExist ensures every id in deps references a known task.
func validateDependenciesExist(s store.Store, deps []string) error {
	var missing []string
	for _, id := range deps {
		if _, ok := s.Get(id); !ok {
			missing = append(missing, id)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("unknown dependency ID(s): %s", strings.Join(missing, ", "))
	}
	return nil
}

// validateNoCycle checks that adding task t to the store would not create
// a dependency cycle. It builds an adjacency list from the existing tasks
// plus the candidate task, then walks the graph with DFS.
func validateNoCycle(s store.Store, candidate store.Task) error {
	// Build adjacency list: node → its direct dependencies.
	existing := s.All()
	adj := make(map[string][]string, len(existing)+1)
	for _, t := range existing {
		adj[t.ID] = t.DependsOn
	}
	adj[candidate.ID] = candidate.DependsOn

	// DFS from the candidate's own ID: if we can reach candidate.ID
	// through its dependencies, there is a cycle.
	visited := make(map[string]bool)
	inStack := make(map[string]bool)

	var hasCycle func(node string) bool
	hasCycle = func(node string) bool {
		if inStack[node] {
			return true
		}
		if visited[node] {
			return false
		}
		visited[node] = true
		inStack[node] = true
		for _, dep := range adj[node] {
			if hasCycle(dep) {
				return true
			}
		}
		inStack[node] = false
		return false
	}

	if hasCycle(candidate.ID) {
		return errors.New("adding this task would create a dependency cycle")
	}
	return nil
}

// generateID returns a cryptographically random 8-character hex string.
func generateID() (string, error) {
	b := make([]byte, 4) // 4 bytes → 8 hex chars
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

## go.mod (example)

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
`generateID` reads 4 bytes from `crypto/rand` and hex-encodes them, giving an 8-character string with 2^32 (~4 billion) possible values. For a task queue this is more than sufficient. A ULID or UUID would also work but adds a dependency; this approach stays stdlib-only.

### Dependency validation (existence)
Before persisting the new task, `validateDependenciesExist` calls `Store.Get` for every supplied ID. If any ID is not found it returns a combined error listing all missing IDs so the user can fix them in one edit.

### Cycle detection
`validateNoCycle` builds an in-memory adjacency list from all existing tasks plus the candidate, then runs iterative DFS with a "currently in stack" set. The DFS starts from the candidate node; if DFS can reach the candidate through its own dependency chain, a cycle exists and the add is rejected. This runs before `Store.Add` so the store is never left in an inconsistent state.

### Exit codes
Cobra returns exit code 1 whenever `RunE` returns a non-nil error. `rootCmd.Execute()` in main propagates this via `os.Exit(1)`. Success produces exit code 0 automatically. No manual `os.Exit` calls are needed in the command logic.

### Store interface
The `Store` interface (`Add`, `Get`, `All`) is intentionally minimal — just what the add command needs. `FileStore` is the concrete implementation. Tests can supply an in-memory stub that satisfies the same interface without touching the filesystem.

### Thread safety
`FileStore` holds a `sync.Mutex` and locks around every load/write pair. This protects against concurrent CLI invocations on the same store file.
