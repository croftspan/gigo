package store

import "testing"

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
