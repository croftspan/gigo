# tq add + tq list — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-27-tq-add-list-design.md`

**Goal:** Add `tq add` and `tq list` commands, plus a review hook for automated two-stage review.

**Architecture:** Two new Cobra commands in `cmd/`, one struct field addition in `store/`, one shell script in `.claude/hooks/`. The add and list commands are fully independent — they share only the existing Store interface and the new `Cmd` field on Task.

**Tech Stack:** Go 1.22, Cobra, existing store package

---

### Task 1: Add `Cmd` field to `store.Task`

**blocks:** 2, 3
**blocked-by:** []
**parallelizable:** false

**Files:**
- Modify: `store/store.go:24-31`

- [ ] **Step 1: Add the Cmd field to the Task struct**

In `store/store.go`, add `Cmd` between `Name` and `State` in the Task struct:

```go
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
```

- [ ] **Step 2: Verify existing tests still pass**

Run: `go test ./...`
Expected: All 10 tests pass. The new field has a zero value (`""`) so existing code is unaffected.

- [ ] **Step 3: Commit**

```bash
git add store/store.go
git commit -m "feat(store): add Cmd field to Task struct"
```

---

### Task 2: `tq add` command

**blocks:** []
**blocked-by:** 1
**parallelizable:** true (with Task 3)

**Files:**
- Create: `cmd/add.go`
- Create: `cmd/add_test.go`

- [ ] **Step 1: Write `cmd/add.go`**

```go
package cmd

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"tq/store"

	"github.com/spf13/cobra"
)

var (
	addCmd    string
	addPri    int
	addDepStr string
)

func init() {
	addCommand.Flags().StringVar(&addCmd, "cmd", "", "Shell command to execute (required)")
	addCommand.Flags().IntVar(&addPri, "priority", 0, "Task priority (higher = more important)")
	addCommand.Flags().StringVar(&addDepStr, "depends-on", "", "Comma-separated task IDs")
	rootCmd.AddCommand(addCommand)
}

var addCommand = &cobra.Command{
	Use:   "add <name>",
	Short: "Add a task to the queue",
	Args:  cobra.ExactArgs(1),
	RunE:  runAdd,
}

func runAdd(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runAddWithStore(s, args[0], addCmd, addPri, addDepStr, jsonOutput, os.Stdout)
}

func runAddWithStore(s store.Store, name, cmdStr string, priority int, depStr string, jsonOut bool, w io.Writer) error {
	if cmdStr == "" {
		return fmt.Errorf("tq: cannot add task %q: --cmd is required", name)
	}

	var deps []string
	if depStr != "" {
		deps = strings.Split(depStr, ",")
		// Validate dependencies exist
		tasks, err := s.List(store.Filter{})
		if err != nil {
			return fmt.Errorf("tq: cannot add task %q: %w", name, err)
		}
		existing := make(map[string]bool, len(tasks))
		for _, t := range tasks {
			existing[t.ID] = true
		}
		for _, d := range deps {
			if !existing[d] {
				return fmt.Errorf("tq: cannot add task %q: dependency %q not found", name, d)
			}
		}
	}

	state := store.StateReady
	if len(deps) > 0 {
		state = store.StatePending
	}
	if deps == nil {
		deps = []string{}
	}

	// Pre-generate ID
	b := make([]byte, 4)
	if _, err := rand.Read(b); err != nil {
		return fmt.Errorf("tq: cannot add task %q: %w", name, err)
	}
	id := hex.EncodeToString(b)

	task := store.Task{
		ID:        id,
		Name:      name,
		Cmd:       cmdStr,
		State:     state,
		Priority:  priority,
		DependsOn: deps,
		CreatedAt: time.Now(),
	}

	if err := s.Add(task); err != nil {
		return fmt.Errorf("tq: cannot add task %q: %w", name, err)
	}

	if jsonOut {
		return json.NewEncoder(w).Encode(struct {
			ID string `json:"id"`
		}{ID: id})
	}
	fmt.Fprintln(w, id)
	return nil
}
```

- [ ] **Step 2: Write `cmd/add_test.go`**

```go
package cmd

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"tq/store"
)

func TestAddBasic(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runAddWithStore(s, "build", "make build", 5, "", false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	id := strings.TrimSpace(buf.String())
	if len(id) != 8 {
		t.Errorf("expected 8-char hex ID, got %q", id)
	}

	// Verify task in store
	tasks, _ := s.List(store.Filter{})
	if len(tasks) != 1 {
		t.Fatalf("expected 1 task, got %d", len(tasks))
	}
	task := tasks[0]
	if task.Name != "build" {
		t.Errorf("expected name 'build', got %q", task.Name)
	}
	if task.Cmd != "make build" {
		t.Errorf("expected cmd 'make build', got %q", task.Cmd)
	}
	if task.Priority != 5 {
		t.Errorf("expected priority 5, got %d", task.Priority)
	}
	if task.State != store.StateReady {
		t.Errorf("expected state ready, got %s", task.State)
	}
}

func TestAddMissingCmd(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runAddWithStore(s, "build", "", 0, "", false, &buf)
	if err == nil {
		t.Fatal("expected error for missing --cmd")
	}
	if !strings.Contains(err.Error(), "--cmd is required") {
		t.Errorf("expected --cmd error, got: %v", err)
	}
}

func TestAddWithDeps(t *testing.T) {
	s := store.NewMemoryStore()
	// Add a task to depend on
	s.Add(store.Task{ID: "abc12345", Name: "compile", Cmd: "make", State: store.StateReady})

	var buf bytes.Buffer
	err := runAddWithStore(s, "test", "make test", 0, "abc12345", false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	tasks, _ := s.List(store.Filter{})
	// Find the newly added task (not "compile")
	for _, task := range tasks {
		if task.Name == "test" {
			if task.State != store.StatePending {
				t.Errorf("expected state pending (has deps), got %s", task.State)
			}
			if len(task.DependsOn) != 1 || task.DependsOn[0] != "abc12345" {
				t.Errorf("expected depends-on [abc12345], got %v", task.DependsOn)
			}
			return
		}
	}
	t.Fatal("newly added task not found in store")
}

func TestAddMissingDep(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runAddWithStore(s, "deploy", "deploy.sh", 0, "nonexistent", false, &buf)
	if err == nil {
		t.Fatal("expected error for missing dependency")
	}
	if !strings.Contains(err.Error(), `dependency "nonexistent" not found`) {
		t.Errorf("expected dependency-not-found error, got: %v", err)
	}
}

func TestAddJSON(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runAddWithStore(s, "build", "make", 0, "", true, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	var out struct {
		ID string `json:"id"`
	}
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("invalid JSON: %v\nraw: %s", err, buf.String())
	}
	if len(out.ID) != 8 {
		t.Errorf("expected 8-char hex ID, got %q", out.ID)
	}
}

func TestAddNoDepsEmptySlice(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	runAddWithStore(s, "build", "make", 0, "", false, &buf)

	tasks, _ := s.List(store.Filter{})
	if tasks[0].DependsOn == nil {
		t.Error("DependsOn should be empty slice, not nil")
	}
	if len(tasks[0].DependsOn) != 0 {
		t.Errorf("expected 0 deps, got %d", len(tasks[0].DependsOn))
	}
}
```

- [ ] **Step 3: Run tests**

Run: `go test ./cmd/ -run TestAdd -v`
Expected: All 6 TestAdd* tests pass.

- [ ] **Step 4: Run full suite**

Run: `go test ./...`
Expected: All tests pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add cmd/add.go cmd/add_test.go
git commit -m "feat(cmd): add tq add command with dependency validation"
```

---

### Task 3: `tq list` command

**blocks:** []
**blocked-by:** 1
**parallelizable:** true (with Task 2)

**Files:**
- Create: `cmd/list.go`
- Create: `cmd/list_test.go`

- [ ] **Step 1: Write `cmd/list.go`**

```go
package cmd

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"time"

	"tq/store"

	"github.com/spf13/cobra"
)

var listState string

func init() {
	listCommand.Flags().StringVar(&listState, "state", "", "Filter by state (pending, ready, running, done, failed, dead)")
	rootCmd.AddCommand(listCommand)
}

var listCommand = &cobra.Command{
	Use:   "list",
	Short: "List tasks in the queue",
	RunE:  runList,
}

func runList(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runListWithStore(s, listState, jsonOutput, os.Stdout)
}

// ListTask is the JSON representation of a task in list output.
type ListTask struct {
	ID        string   `json:"id"`
	Name      string   `json:"name"`
	Cmd       string   `json:"cmd"`
	State     string   `json:"state"`
	Priority  int      `json:"priority"`
	DependsOn []string `json:"depends_on"`
	CreatedAt string   `json:"created_at"`
}

func runListWithStore(s store.Store, stateStr string, jsonOut bool, w io.Writer) error {
	var filter store.Filter
	if stateStr != "" {
		st := store.State(stateStr)
		valid := false
		for _, s := range store.AllStates {
			if s == st {
				valid = true
				break
			}
		}
		if !valid {
			names := make([]string, len(store.AllStates))
			for i, s := range store.AllStates {
				names[i] = string(s)
			}
			return fmt.Errorf("tq: invalid state %q (valid: %s)", stateStr, strings.Join(names, ", "))
		}
		filter.State = &st
	}

	tasks, err := s.List(filter)
	if err != nil {
		return fmt.Errorf("tq: cannot list tasks: %w", err)
	}

	// Sort: priority descending, then CreatedAt ascending
	sort.Slice(tasks, func(i, j int) bool {
		if tasks[i].Priority != tasks[j].Priority {
			return tasks[i].Priority > tasks[j].Priority
		}
		return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
	})

	if jsonOut {
		out := make([]ListTask, len(tasks))
		for i, t := range tasks {
			deps := t.DependsOn
			if deps == nil {
				deps = []string{}
			}
			out[i] = ListTask{
				ID:        t.ID,
				Name:      t.Name,
				Cmd:       t.Cmd,
				State:     string(t.State),
				Priority:  t.Priority,
				DependsOn: deps,
				CreatedAt: t.CreatedAt.Format(time.RFC3339),
			}
		}
		return json.NewEncoder(w).Encode(out)
	}

	if len(tasks) == 0 {
		return nil
	}

	fmt.Fprintf(w, "%-10s%-10s%4s  %-16s%s\n", "ID", "STATE", "PRI", "NAME", "DEPENDS")
	for _, t := range tasks {
		deps := strings.Join(t.DependsOn, ",")
		fmt.Fprintf(w, "%-10s%-10s%4d  %-16s%s\n", t.ID, t.State, t.Priority, t.Name, deps)
	}
	return nil
}
```

- [ ] **Step 2: Write `cmd/list_test.go`**

```go
package cmd

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
	"time"

	"tq/store"
)

func TestListEmpty(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runListWithStore(s, "", false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if buf.String() != "" {
		t.Errorf("expected no output for empty list, got: %q", buf.String())
	}
}

func TestListWithTasks(t *testing.T) {
	s := store.NewMemoryStore()
	s.Add(store.Task{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 10, CreatedAt: time.Now()})
	s.Add(store.Task{ID: "bbbb2222", Name: "test", Cmd: "make test", State: store.StatePending, Priority: 5, DependsOn: []string{"aaaa1111"}, CreatedAt: time.Now()})

	var buf bytes.Buffer
	err := runListWithStore(s, "", false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	out := buf.String()
	lines := strings.Split(strings.TrimSpace(out), "\n")
	if len(lines) != 3 {
		t.Fatalf("expected 3 lines (header + 2 tasks), got %d:\n%s", len(lines), out)
	}
	// Header
	if !strings.HasPrefix(lines[0], "ID") {
		t.Errorf("expected header starting with ID, got: %q", lines[0])
	}
	// First row should be higher priority (build, pri 10)
	if !strings.Contains(lines[1], "build") {
		t.Errorf("expected first task to be 'build' (higher pri), got: %q", lines[1])
	}
	// Second row should be lower priority (test, pri 5)
	if !strings.Contains(lines[2], "test") {
		t.Errorf("expected second task to be 'test' (lower pri), got: %q", lines[2])
	}
	// Deps column
	if !strings.Contains(lines[2], "aaaa1111") {
		t.Errorf("expected depends column to show aaaa1111, got: %q", lines[2])
	}
}

func TestListFilterState(t *testing.T) {
	s := store.NewMemoryStore()
	s.Add(store.Task{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, CreatedAt: time.Now()})
	s.Add(store.Task{ID: "bbbb2222", Name: "test", Cmd: "make test", State: store.StatePending, CreatedAt: time.Now()})
	s.Add(store.Task{ID: "cccc3333", Name: "lint", Cmd: "golint", State: store.StateReady, CreatedAt: time.Now()})

	var buf bytes.Buffer
	err := runListWithStore(s, "ready", false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	lines := strings.Split(strings.TrimSpace(buf.String()), "\n")
	// Header + 2 ready tasks
	if len(lines) != 3 {
		t.Fatalf("expected 3 lines (header + 2 ready), got %d:\n%s", len(lines), buf.String())
	}
}

func TestListInvalidState(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runListWithStore(s, "borked", false, &buf)
	if err == nil {
		t.Fatal("expected error for invalid state")
	}
	if !strings.Contains(err.Error(), `invalid state "borked"`) {
		t.Errorf("expected invalid-state error, got: %v", err)
	}
	if !strings.Contains(err.Error(), "pending, ready, running, done, failed, dead") {
		t.Errorf("expected valid states listed in error, got: %v", err)
	}
}

func TestListJSON(t *testing.T) {
	s := store.NewMemoryStore()
	now := time.Date(2026, 3, 27, 10, 0, 0, 0, time.UTC)
	s.Add(store.Task{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 10, DependsOn: []string{}, CreatedAt: now})

	var buf bytes.Buffer
	err := runListWithStore(s, "", true, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	var out []ListTask
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("invalid JSON: %v\nraw: %s", err, buf.String())
	}
	if len(out) != 1 {
		t.Fatalf("expected 1 task, got %d", len(out))
	}
	if out[0].ID != "aaaa1111" {
		t.Errorf("expected ID aaaa1111, got %q", out[0].ID)
	}
	if out[0].Cmd != "make" {
		t.Errorf("expected cmd 'make', got %q", out[0].Cmd)
	}
	if out[0].State != "ready" {
		t.Errorf("expected state ready, got %q", out[0].State)
	}
	if len(out[0].DependsOn) != 0 {
		t.Errorf("expected empty depends_on, got %v", out[0].DependsOn)
	}
}

func TestListJSONEmpty(t *testing.T) {
	s := store.NewMemoryStore()
	var buf bytes.Buffer
	err := runListWithStore(s, "", true, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	var out []ListTask
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("invalid JSON: %v\nraw: %s", err, buf.String())
	}
	if len(out) != 0 {
		t.Fatalf("expected 0 tasks, got %d", len(out))
	}
}

func TestListSortOrder(t *testing.T) {
	s := store.NewMemoryStore()
	now := time.Date(2026, 3, 27, 10, 0, 0, 0, time.UTC)
	// Same priority, different times — older first
	s.Add(store.Task{ID: "cccc3333", Name: "newer", Cmd: "c", State: store.StateReady, Priority: 5, CreatedAt: now.Add(time.Minute)})
	s.Add(store.Task{ID: "aaaa1111", Name: "older", Cmd: "a", State: store.StateReady, Priority: 5, CreatedAt: now})
	// Higher priority — should be first regardless of time
	s.Add(store.Task{ID: "bbbb2222", Name: "urgent", Cmd: "b", State: store.StateReady, Priority: 10, CreatedAt: now.Add(2 * time.Minute)})

	var buf bytes.Buffer
	runListWithStore(s, "", false, &buf)
	lines := strings.Split(strings.TrimSpace(buf.String()), "\n")
	// Header + 3 tasks
	if len(lines) != 4 {
		t.Fatalf("expected 4 lines, got %d:\n%s", len(lines), buf.String())
	}
	// First data row: urgent (pri 10)
	if !strings.Contains(lines[1], "urgent") {
		t.Errorf("expected first task 'urgent' (highest pri), got: %q", lines[1])
	}
	// Second: older (pri 5, earlier time)
	if !strings.Contains(lines[2], "older") {
		t.Errorf("expected second task 'older' (same pri, earlier), got: %q", lines[2])
	}
	// Third: newer (pri 5, later time)
	if !strings.Contains(lines[3], "newer") {
		t.Errorf("expected third task 'newer' (same pri, later), got: %q", lines[3])
	}
}
```

- [ ] **Step 3: Run tests**

Run: `go test ./cmd/ -run TestList -v`
Expected: All 7 TestList* tests pass.

- [ ] **Step 4: Run full suite**

Run: `go test ./...`
Expected: All tests pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add cmd/list.go cmd/list_test.go
git commit -m "feat(cmd): add tq list command with state filter and sorting"
```

---

### Task 4: Review hook

**blocks:** []
**blocked-by:** []
**parallelizable:** true (with Tasks 2, 3)

**Files:**
- Create: `.claude/hooks/gigo-review-gate.sh`

- [ ] **Step 1: Create the hook directory and script**

```bash
#!/usr/bin/env bash
set -euo pipefail

SPEC="docs/gigo/specs/2026-03-27-tq-add-list-design.md"

echo "=== Stage 1: Go quality gate ==="
go vet ./...
go test ./...

echo "=== Stage 2: Two-stage review (spec compliance + engineering quality) ==="
claude -p "Run gigo:verify on the most recent changes. Two stages: spec compliance first, then engineering quality. Spec: $SPEC"
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x .claude/hooks/gigo-review-gate.sh`

- [ ] **Step 3: Commit**

```bash
git add .claude/hooks/gigo-review-gate.sh
git commit -m "feat: add gigo-review-gate hook for automated two-stage review"
```

---

## Dependency Graph

```
Task 1 (Cmd field) ──┬──→ Task 2 (tq add)    ← Worker 1
                      └──→ Task 3 (tq list)   ← Worker 2
Task 4 (review hook) ────→ (independent)       ← either worker
```

Task 1 is the only blocker. After it completes, Tasks 2 and 3 run in parallel on separate workers. Task 4 is independent — assign to whichever worker finishes first, or run it alongside Tasks 2 and 3.

## Risks

- **MemoryStore means no cross-invocation state.** `tq add` then `tq list` in separate runs won't share data. Expected — persistence comes with BoltDB later.
- **Cmd field is a shared change.** Both workers need it, but it's Task 1 (sequential) so no merge conflict risk.
- **ID pre-generation in add.** The MemoryStore also generates IDs for tasks with empty IDs — the add command sets the ID explicitly to avoid this ambiguity.

## Done When

- `go test ./...` passes with all existing tests + new tests for add (6) and list (7)
- `tq add "build" --cmd "make" --priority 5` prints a hex ID
- `tq add "deploy" --cmd "deploy.sh" --depends-on <id>` prints a hex ID and sets state to pending
- `tq list` shows header + rows sorted by priority
- `tq list --state ready` filters correctly
- `tq list --json` produces a parseable JSON array
- `.claude/hooks/gigo-review-gate.sh` exists and is executable
