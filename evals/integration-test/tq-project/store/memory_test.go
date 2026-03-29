package store

import (
	"errors"
	"testing"
)

func TestListEmpty(t *testing.T) {
	s := NewMemoryStore()
	tasks, err := s.List(Filter{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(tasks) != 0 {
		t.Fatalf("expected 0 tasks, got %d", len(tasks))
	}
}

func TestAddAndList(t *testing.T) {
	s := NewMemoryStore()
	s.Add(Task{Name: "build", State: StateReady})
	s.Add(Task{Name: "test", State: StatePending})
	s.Add(Task{Name: "deploy", State: StateReady})

	tasks, err := s.List(Filter{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(tasks) != 3 {
		t.Fatalf("expected 3 tasks, got %d", len(tasks))
	}
}

func TestListWithFilter(t *testing.T) {
	s := NewMemoryStore()
	s.Add(Task{Name: "a", State: StateReady})
	s.Add(Task{Name: "b", State: StatePending})
	s.Add(Task{Name: "c", State: StateReady})

	ready := StateReady
	tasks, err := s.List(Filter{State: &ready})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(tasks) != 2 {
		t.Fatalf("expected 2 ready tasks, got %d", len(tasks))
	}
}

func TestAddGeneratesID(t *testing.T) {
	s := NewMemoryStore()
	s.Add(Task{Name: "no-id", State: StatePending})

	tasks, _ := s.List(Filter{})
	if len(tasks) != 1 {
		t.Fatalf("expected 1 task, got %d", len(tasks))
	}
	if tasks[0].ID == "" {
		t.Fatal("expected generated ID, got empty string")
	}
}

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
