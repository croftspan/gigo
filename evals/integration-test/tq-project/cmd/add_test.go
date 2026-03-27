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
