package store

import (
	"crypto/rand"
	"encoding/hex"
	"sync"
)

// MemoryStore is an in-memory Store implementation.
type MemoryStore struct {
	mu    sync.Mutex
	tasks map[string]Task
}

// NewMemoryStore returns an empty MemoryStore.
func NewMemoryStore() *MemoryStore {
	return &MemoryStore{tasks: make(map[string]Task)}
}

// Add inserts a task. If task.ID is empty, a random ID is generated.
func (m *MemoryStore) Add(task Task) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if task.ID == "" {
		b := make([]byte, 4)
		if _, err := rand.Read(b); err != nil {
			return err
		}
		task.ID = hex.EncodeToString(b)
	}
	m.tasks[task.ID] = task
	return nil
}

// List returns tasks matching the filter. Returns a copy, not internal references.
func (m *MemoryStore) List(filter Filter) ([]Task, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var result []Task
	for _, t := range m.tasks {
		if filter.State != nil && t.State != *filter.State {
			continue
		}
		result = append(result, t)
	}
	return result, nil
}

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

// Close is a no-op for MemoryStore.
func (m *MemoryStore) Close() error {
	return nil
}
