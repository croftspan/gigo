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
