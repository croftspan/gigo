# tq add — Implementation

## Overview

This implements the `tq add` command as a Cobra subcommand. The implementation defines all required types, the Store interface, sentinel errors, and a concrete in-memory/file-backed store stub, then wires up the CLI.

In a real project these would be split across packages (e.g. `internal/task`, `internal/store`, `cmd/add`). Here everything is self-contained and compilable in a single `main.go`.

---

## File: main.go

```go
package main

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

// State represents the lifecycle state of a task.
type State string

const (
	StatePending State = "pending"
	StateReady   State = "ready"
	StateRunning State = "running"
	StateDone    State = "done"
	StateFailed  State = "failed"
	StateDead    State = "dead"
)

// Task is the core unit of work managed by tq.
type Task struct {
	ID         string
	Command    []string
	Priority   int
	DependsOn  []string
	State      State
	Retries    int
	MaxRetries int
	CreatedAt  time.Time
	StartedAt  *time.Time
	FinishedAt *time.Time
	WorkerPID  int
	Artifact   string
	Metadata   map[string]string
}

// Filter controls which tasks List returns.
type Filter struct {
	State    []State
	Priority *int
	Limit    int
}

// ---------------------------------------------------------------------------
// Sentinel errors
// ---------------------------------------------------------------------------

var (
	ErrNotFound  = errors.New("task not found")
	ErrWrongState = errors.New("task is not in the expected state")
	ErrCycle     = errors.New("dependency cycle detected")
	ErrDuplicate = errors.New("task with this ID already exists")
)

// ---------------------------------------------------------------------------
// Store interface
// ---------------------------------------------------------------------------

// Store is the persistence layer for tasks.
type Store interface {
	// Add persists a new task. Returns ErrCycle if the task's DependsOn
	// fields introduce a dependency cycle, ErrDuplicate if the ID already
	// exists.
	Add(task Task) error

	// Get retrieves a single task by ID. Returns ErrNotFound if absent.
	Get(id string) (Task, error)

	// List returns tasks matching the filter, ordered by priority desc then
	// created_at asc.
	List(filter Filter) ([]Task, error)

	// Transition performs a compare-and-swap state change. Returns
	// ErrWrongState if the current state != from.
	Transition(id string, from, to State) error

	// Update applies fn to the task in place.
	Update(id string, fn func(*Task)) error

	// Delete removes a task.
	Delete(id string) error

	// Close releases any resources held by the store.
	Close() error
}

// ---------------------------------------------------------------------------
// In-memory store (reference implementation / stub)
// ---------------------------------------------------------------------------

// memStore is a simple in-memory Store used when no persistent backend is
// configured. It is not safe for concurrent use without external locking, but
// is sufficient for a single-process CLI.
type memStore struct {
	tasks map[string]Task
}

func newMemStore() *memStore {
	return &memStore{tasks: make(map[string]Task)}
}

func (s *memStore) Add(task Task) error {
	if _, exists := s.tasks[task.ID]; exists {
		return ErrDuplicate
	}
	if err := s.detectCycle(task); err != nil {
		return err
	}
	s.tasks[task.ID] = task
	return nil
}

// detectCycle performs a DFS over the dependency graph to check whether
// adding task would introduce a cycle.
func (s *memStore) detectCycle(task Task) error {
	// Build an adjacency list including the candidate task.
	adj := make(map[string][]string, len(s.tasks)+1)
	for id, t := range s.tasks {
		adj[id] = t.DependsOn
	}
	adj[task.ID] = task.DependsOn

	visited := make(map[string]bool)
	inStack := make(map[string]bool)

	var dfs func(id string) bool
	dfs = func(id string) bool {
		if inStack[id] {
			return true // back-edge → cycle
		}
		if visited[id] {
			return false
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

	for id := range adj {
		if !visited[id] {
			if dfs(id) {
				return ErrCycle
			}
		}
	}
	return nil
}

func (s *memStore) Get(id string) (Task, error) {
	t, ok := s.tasks[id]
	if !ok {
		return Task{}, ErrNotFound
	}
	return t, nil
}

func (s *memStore) List(filter Filter) ([]Task, error) {
	var out []Task
	for _, t := range s.tasks {
		if !matchesFilter(t, filter) {
			continue
		}
		out = append(out, t)
	}
	// Sort: priority desc, then created_at asc.
	sortTasks(out)
	if filter.Limit > 0 && len(out) > filter.Limit {
		out = out[:filter.Limit]
	}
	return out, nil
}

func matchesFilter(t Task, f Filter) bool {
	if len(f.State) > 0 {
		found := false
		for _, s := range f.State {
			if t.State == s {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	if f.Priority != nil && t.Priority != *f.Priority {
		return false
	}
	return true
}

// sortTasks sorts in-place: priority desc, created_at asc.
func sortTasks(tasks []Task) {
	n := len(tasks)
	for i := 1; i < n; i++ {
		for j := i; j > 0; j-- {
			a, b := tasks[j-1], tasks[j]
			if a.Priority < b.Priority ||
				(a.Priority == b.Priority && a.CreatedAt.After(b.CreatedAt)) {
				tasks[j-1], tasks[j] = tasks[j], tasks[j-1]
			}
		}
	}
}

func (s *memStore) Transition(id string, from, to State) error {
	t, ok := s.tasks[id]
	if !ok {
		return ErrNotFound
	}
	if t.State != from {
		return ErrWrongState
	}
	t.State = to
	s.tasks[id] = t
	return nil
}

func (s *memStore) Update(id string, fn func(*Task)) error {
	t, ok := s.tasks[id]
	if !ok {
		return ErrNotFound
	}
	fn(&t)
	s.tasks[id] = t
	return nil
}

func (s *memStore) Delete(id string) error {
	if _, ok := s.tasks[id]; !ok {
		return ErrNotFound
	}
	delete(s.tasks, id)
	return nil
}

func (s *memStore) Close() error { return nil }

// ---------------------------------------------------------------------------
// ID generation
// ---------------------------------------------------------------------------

// generateID returns an 8-character random hex string.
func generateID() (string, error) {
	b := make([]byte, 4) // 4 bytes → 8 hex chars
	if _, err := rand.Read(b); err != nil {
		return "", fmt.Errorf("generating task ID: %w", err)
	}
	return hex.EncodeToString(b), nil
}

// ---------------------------------------------------------------------------
// tq add command
// ---------------------------------------------------------------------------

func newAddCmd(store Store) *cobra.Command {
	var (
		priority  int
		dependsOn string
		cmd       string
	)

	addCmd := &cobra.Command{
		Use:   "add <name>",
		Short: "Add a new task to the queue",
		Args:  cobra.ExactArgs(1),
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			name := args[0]

			// --cmd is required.
			if cmd == "" {
				return fmt.Errorf("--cmd is required")
			}

			// Parse --depends-on into a slice of IDs.
			var deps []string
			if dependsOn != "" {
				for _, raw := range strings.Split(dependsOn, ",") {
					id := strings.TrimSpace(raw)
					if id != "" {
						deps = append(deps, id)
					}
				}
			}

			// Validate that every declared dependency exists in the store.
			for _, depID := range deps {
				if _, err := store.Get(depID); err != nil {
					if errors.Is(err, ErrNotFound) {
						return fmt.Errorf("dependency %q not found", depID)
					}
					return fmt.Errorf("looking up dependency %q: %w", depID, err)
				}
			}

			// Generate a short unique ID.
			id, err := generateID()
			if err != nil {
				return err
			}

			// Parse the shell command string into argv.
			argv := parseCommand(cmd)

			// Build the task. New tasks start in the pending state; the
			// scheduler advances them to ready once all deps are satisfied.
			now := time.Now().UTC()
			task := Task{
				ID:        id,
				Command:   argv,
				Priority:  priority,
				DependsOn: deps,
				State:     StatePending,
				CreatedAt: now,
				Metadata:  map[string]string{"name": name},
			}

			// Store.Add handles cycle detection (ErrCycle) and duplicate
			// detection (ErrDuplicate) atomically before persisting.
			if err := store.Add(task); err != nil {
				if errors.Is(err, ErrCycle) {
					return fmt.Errorf("adding task would create a dependency cycle")
				}
				if errors.Is(err, ErrDuplicate) {
					return fmt.Errorf("task with ID %q already exists (ID collision — retry)", id)
				}
				return fmt.Errorf("adding task: %w", err)
			}

			fmt.Fprintln(cobraCmd.OutOrStdout(), id)
			return nil
		},
	}

	addCmd.Flags().IntVar(&priority, "priority", 0, "Task priority (higher = runs first)")
	addCmd.Flags().StringVar(&dependsOn, "depends-on", "", "Comma-separated IDs of tasks this task depends on")
	addCmd.Flags().StringVar(&cmd, "cmd", "", "Shell command to run (required)")
	_ = addCmd.MarkFlagRequired("cmd")

	return addCmd
}

// parseCommand splits a shell command string into an argv slice. For simple
// cases (no quoting, no escaping) splitting on whitespace is sufficient. A
// production implementation would use a proper shell-word parser.
func parseCommand(s string) []string {
	fields := strings.Fields(s)
	if len(fields) == 0 {
		return []string{s}
	}
	return fields
}

// ---------------------------------------------------------------------------
// Root command & main
// ---------------------------------------------------------------------------

func newRootCmd(store Store) *cobra.Command {
	root := &cobra.Command{
		Use:   "tq",
		Short: "tq — a local task queue",
	}
	root.AddCommand(newAddCmd(store))
	return root
}

func main() {
	store := newMemStore()
	defer store.Close()

	root := newRootCmd(store)
	if err := root.Execute(); err != nil {
		// Cobra already prints the error; exit 1 signals failure.
		os.Exit(1)
	}
}
```

---

## Design notes

### Flag choices

| Flag | Type | Default | Notes |
|---|---|---|---|
| `--cmd` | string | — | Required. Marked with `MarkFlagRequired`. |
| `--priority` | int | 0 | Higher integers run first. |
| `--depends-on` | string | — | Comma-separated IDs, trimmed of whitespace. |
| positional `<name>` | string | — | Stored in `Metadata["name"]`. |

`--cmd` accepts the command as a single quoted string (e.g. `--cmd "go test ./..."`) and is split into argv with `strings.Fields`. A production implementation would use a proper shell-word parser (e.g. `github.com/mattn/go-shellwords`) to handle quoted arguments correctly.

### ID generation

`generateID` reads 4 bytes from `crypto/rand` and hex-encodes them to produce an 8-character ID. This gives 4 billion possible IDs; collision probability for reasonable queue sizes is negligible. The `ErrDuplicate` path from `Store.Add` handles the astronomically unlikely collision gracefully with a user-visible error asking them to retry.

### Validation order

1. `--cmd` present (Cobra `MarkFlagRequired` handles this before `RunE`).
2. Each dep ID exists in the store (returns a clear "not found" error per ID).
3. `Store.Add` runs cycle detection via DFS before persisting (returns `ErrCycle` if a cycle would be introduced).

This order gives the most actionable error messages: the user knows which dep is missing before being told about a cycle, and the cycle check is authoritative because it happens inside the store where the full graph is visible.

### State on creation

Tasks enter as `StatePending`. A scheduler (not implemented here) watches for tasks whose dependencies have all reached `StateDone` and advances them to `StateReady` via `Transition(pending → ready)`. From `StateReady` the scheduler can claim a task for execution via `Transition(ready → running)` as a CAS — only one caller wins.

### Exit codes

- 0: task created, ID printed to stdout.
- 1: any error (missing flag, dep not found, cycle, store error). Cobra calls `os.Exit(1)` after printing the error.

### Extending to a persistent store

Replace `newMemStore()` in `main()` with a constructor for a file-backed or database-backed store that satisfies the same `Store` interface. The `tq add` command and all validation logic are unchanged.
