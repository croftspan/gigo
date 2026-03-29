# tq priority — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-28-tq-priority-design.md`

**Goal:** Add `tq priority <task-id> <new-priority>` command for changing task priority after creation.

**Architecture:** Two new methods on the Store interface (`Get`, `UpdatePriority`), implemented on MemoryStore, plus one new Cobra command. Store changes land first (Task 1), command depends on them (Task 2).

**Tech Stack:** Go 1.22, Cobra, existing store package

---

### Task 1: Expand Store interface with `Get` and `UpdatePriority`

**blocks:** 2
**blocked-by:** []
**parallelizable:** false

**Files:**
- Modify: `store/store.go:1-44`
- Modify: `store/memory.go`
- Modify: `store/memory_test.go`

- [ ] **Step 1: Add `ErrNotFound` sentinel and new methods to Store interface**

In `store/store.go`, add `"errors"` to the import list. Add the `ErrNotFound` sentinel before the `Store` interface. Add `Get` and `UpdatePriority` to the interface.

If `ErrNotFound` already exists (from the watch spec landing first), skip the sentinel definition and use the existing one.

```go
package store

import (
	"errors"
	"time"
)

// State represents a task's position in the lifecycle.
type State string

const (
	StatePending State = "pending"
	StateReady   State = "ready"
	StateRunning State = "running"
	StateDone    State = "done"
	StateFailed  State = "failed"
	StateDead    State = "dead"
)

// AllStates lists every state in display order.
var AllStates = []State{
	StatePending, StateReady, StateRunning,
	StateDone, StateFailed, StateDead,
}

// ErrNotFound is returned when a task ID does not exist in the store.
var ErrNotFound = errors.New("not found")

// Task is the unit of work in the queue.
type Task struct {
	ID        string
	Name      string
	Cmd       string
	State     State
	Priority  int
	DependsOn []string
	CreatedAt time.Time
}

// Filter controls which tasks List returns.
type Filter struct {
	State *State // nil means all states
}

// Store is the persistence interface. All access to task data goes through this.
type Store interface {
	Add(task Task) error
	Get(id string) (Task, error)
	List(filter Filter) ([]Task, error)
	UpdatePriority(id string, priority int) error
	Close() error
}
```

- [ ] **Step 2: Implement `Get` on MemoryStore**

In `store/memory.go`, add:

```go
// Get returns a single task by ID. Returns ErrNotFound if the ID does not exist.
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

- [ ] **Step 3: Implement `UpdatePriority` on MemoryStore**

In `store/memory.go`, add:

```go
// UpdatePriority atomically sets the priority of a task. Returns ErrNotFound if the ID does not exist.
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

- [ ] **Step 4: Add store tests**

In `store/memory_test.go`, add four tests:

```go
func TestGet(t *testing.T) {
	s := NewMemoryStore()
	task := Task{
		ID:       "aaaa1111",
		Name:     "build",
		Cmd:      "make",
		State:    StateReady,
		Priority: 5,
	}
	s.Add(task)

	got, err := s.Get("aaaa1111")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got.ID != "aaaa1111" {
		t.Errorf("expected ID aaaa1111, got %q", got.ID)
	}
	if got.Name != "build" {
		t.Errorf("expected name build, got %q", got.Name)
	}
	if got.Priority != 5 {
		t.Errorf("expected priority 5, got %d", got.Priority)
	}
	if got.State != StateReady {
		t.Errorf("expected state ready, got %s", got.State)
	}
}

func TestGetNotFound(t *testing.T) {
	s := NewMemoryStore()
	_, err := s.Get("nonexistent")
	if !errors.Is(err, ErrNotFound) {
		t.Errorf("expected ErrNotFound, got %v", err)
	}
}

func TestUpdatePriority(t *testing.T) {
	s := NewMemoryStore()
	s.Add(Task{ID: "aaaa1111", Name: "build", Cmd: "make", State: StateReady, Priority: 5})

	err := s.UpdatePriority("aaaa1111", 10)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	got, _ := s.Get("aaaa1111")
	if got.Priority != 10 {
		t.Errorf("expected priority 10 after update, got %d", got.Priority)
	}
}

func TestUpdatePriorityNotFound(t *testing.T) {
	s := NewMemoryStore()
	err := s.UpdatePriority("nonexistent", 10)
	if !errors.Is(err, ErrNotFound) {
		t.Errorf("expected ErrNotFound, got %v", err)
	}
}
```

Note: Add `"errors"` to the import list in `memory_test.go` for `errors.Is`.

- [ ] **Step 5: Run tests**

Run: `go test ./store/ -v`
Expected: All existing tests pass + 4 new tests (TestGet, TestGetNotFound, TestUpdatePriority, TestUpdatePriorityNotFound).

- [ ] **Step 6: Run full suite**

Run: `go test ./...`
Expected: All tests pass. Existing command tests still compile because `MemoryStore` satisfies the expanded `Store` interface.

- [ ] **Step 7: Commit**

```bash
git add store/store.go store/memory.go store/memory_test.go
git commit -m "feat(store): add Get and UpdatePriority to Store interface"
```

---

### Task 2: `tq priority` command

**blocks:** []
**blocked-by:** 1
**parallelizable:** false

**Files:**
- Create: `cmd/priority.go`
- Create: `cmd/priority_test.go`

- [ ] **Step 1: Write `cmd/priority.go`**

```go
package cmd

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"strconv"

	"tq/store"

	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(priorityCommand)
}

var priorityCommand = &cobra.Command{
	Use:   "priority <task-id> <new-priority>",
	Short: "Change a task's priority",
	Args:  cobra.ExactArgs(2),
	RunE:  runPriority,
}

func runPriority(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runPriorityWithStore(s, args[0], args[1], jsonOutput, os.Stdout)
}

// PriorityResult is the JSON output for the priority command.
type PriorityResult struct {
	ID          string `json:"id"`
	OldPriority int    `json:"old_priority"`
	NewPriority int    `json:"new_priority"`
}

func runPriorityWithStore(s store.Store, id string, priorityStr string, jsonOut bool, w io.Writer) error {
	newPri, err := strconv.Atoi(priorityStr)
	if err != nil {
		return fmt.Errorf("tq: cannot reprioritize task %q: priority must be an integer", id)
	}

	task, err := s.Get(id)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			return fmt.Errorf("tq: cannot reprioritize task %q: not found", id)
		}
		return fmt.Errorf("tq: cannot reprioritize task %q: %w", id, err)
	}
	oldPri := task.Priority

	if err := s.UpdatePriority(id, newPri); err != nil {
		return fmt.Errorf("tq: cannot reprioritize task %q: %w", id, err)
	}

	if jsonOut {
		return json.NewEncoder(w).Encode(PriorityResult{
			ID:          id,
			OldPriority: oldPri,
			NewPriority: newPri,
		})
	}
	fmt.Fprintf(w, "%s\t%d -> %d\n", id, oldPri, newPri)
	return nil
}
```

- [ ] **Step 2: Write `cmd/priority_test.go`**

```go
package cmd

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"tq/store"
)

func TestPriority(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 5},
	})
	var buf bytes.Buffer
	err := runPriorityWithStore(s, "aaaa1111", "10", false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "aaaa1111") {
		t.Errorf("expected task ID in output, got: %q", out)
	}
	if !strings.Contains(out, "5 -> 10") {
		t.Errorf("expected '5 -> 10' in output, got: %q", out)
	}

	// Verify store was updated
	task, _ := s.Get("aaaa1111")
	if task.Priority != 10 {
		t.Errorf("expected priority 10 in store, got %d", task.Priority)
	}
}

func TestPriorityJSON(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 5},
	})
	var buf bytes.Buffer
	err := runPriorityWithStore(s, "aaaa1111", "10", true, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	var out PriorityResult
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("invalid JSON: %v\nraw: %s", err, buf.String())
	}
	if out.ID != "aaaa1111" {
		t.Errorf("expected ID aaaa1111, got %q", out.ID)
	}
	if out.OldPriority != 5 {
		t.Errorf("expected old_priority 5, got %d", out.OldPriority)
	}
	if out.NewPriority != 10 {
		t.Errorf("expected new_priority 10, got %d", out.NewPriority)
	}
}

func TestPriorityNotFound(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runPriorityWithStore(s, "deadbeef", "10", false, &buf)
	if err == nil {
		t.Fatal("expected error for nonexistent task")
	}
	if !strings.Contains(err.Error(), `cannot reprioritize task "deadbeef"`) {
		t.Errorf("expected reprioritize error, got: %v", err)
	}
	if !strings.Contains(err.Error(), "not found") {
		t.Errorf("expected 'not found' in error, got: %v", err)
	}
}

func TestPriorityInvalidInt(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 5},
	})
	var buf bytes.Buffer
	err := runPriorityWithStore(s, "aaaa1111", "high", false, &buf)
	if err == nil {
		t.Fatal("expected error for non-integer priority")
	}
	if !strings.Contains(err.Error(), "priority must be an integer") {
		t.Errorf("expected integer error, got: %v", err)
	}
}

func TestPriorityRunningTask(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateRunning, Priority: 5},
	})
	var buf bytes.Buffer
	err := runPriorityWithStore(s, "aaaa1111", "10", false, &buf)
	if err != nil {
		t.Fatalf("expected success for running task, got error: %v", err)
	}
	if !strings.Contains(buf.String(), "5 -> 10") {
		t.Errorf("expected '5 -> 10' in output, got: %q", buf.String())
	}
}

func TestPriorityIdempotent(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 5},
	})
	var buf bytes.Buffer
	err := runPriorityWithStore(s, "aaaa1111", "5", false, &buf)
	if err != nil {
		t.Fatalf("expected success for same priority, got error: %v", err)
	}
	if !strings.Contains(buf.String(), "5 -> 5") {
		t.Errorf("expected '5 -> 5' in output, got: %q", buf.String())
	}
}
```

Note: `seedStore` is defined in `cmd/status_test.go` and is available to all tests in the `cmd` package.

- [ ] **Step 3: Run tests**

Run: `go test ./cmd/ -run TestPriority -v`
Expected: All 6 TestPriority* tests pass.

- [ ] **Step 4: Run full suite**

Run: `go test ./...`
Expected: All tests pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add cmd/priority.go cmd/priority_test.go
git commit -m "feat(cmd): add tq priority command for changing task priority"
```

---

## Dependency Graph

```
Task 1 (Store: Get + UpdatePriority) ──→ Task 2 (tq priority command)
```

Sequential — Task 2 depends on the Store interface expansion in Task 1.

## Risks

- **Interface expansion must be atomic.** Adding methods to the `Store` interface and implementing them on `MemoryStore` must happen in the same commit, or existing code won't compile. Task 1 handles this.
- **`seedStore` dependency.** Task 2 tests use `seedStore` from `cmd/status_test.go`. This helper already exists and works — verify it's still present before writing tests. If it's been moved or renamed, define it locally.

## Done When

- `go test ./...` passes with all existing tests + 4 new store tests + 6 new command tests
- `runPriorityWithStore(s, "id", "10", false, &buf)` updates priority and prints `<id>\t<old> -> <new>`
- `runPriorityWithStore(s, "id", "10", true, &buf)` produces `{"id":"...","old_priority":N,"new_priority":N}`
- `runPriorityWithStore(s, "missing", "10", false, &buf)` returns error with "not found"
- `runPriorityWithStore(s, "id", "high", false, &buf)` returns error with "priority must be an integer"
- Running tasks accept priority changes without error

<!-- approved: plan 2026-03-28T14:30:00 -->
