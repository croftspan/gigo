package store

import "time"

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
	List(filter Filter) ([]Task, error)
	Close() error
}
