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
