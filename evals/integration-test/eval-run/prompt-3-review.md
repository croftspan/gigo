# Prompt 3: Code Review

Review this worker pool implementation for production readiness. Identify bugs, design issues, and missing pieces. Be specific — file:line references, concrete impact, suggested fixes.

```go
package scheduler

import (
	"context"
	"fmt"
	"log"
	"sync"
)

type Task struct {
	ID       string
	Name     string
	Cmd      string
	Priority int
	Deps     []string
	State    string // "pending", "ready", "running", "done", "failed"
}

type Store interface {
	Get(id string) (*Task, error)
	List() ([]*Task, error)
	Update(task *Task) error
}

type Pool struct {
	store   Store
	workers int
	mu      sync.Mutex
}

func NewPool(store Store, workers int) *Pool {
	return &Pool{store: store, workers: workers}
}

func (p *Pool) Run(ctx context.Context) error {
	tasks, _ := p.store.List()

	var wg sync.WaitGroup
	sem := make(chan struct{}, p.workers)

	for _, task := range tasks {
		if task.State != "ready" {
			continue
		}

		sem <- struct{}{}
		wg.Add(1)
		go func(t *Task) {
			defer wg.Done()
			defer func() { <-sem }()

			t.State = "running"
			p.store.Update(t)

			err := p.execute(t)
			if err != nil {
				log.Printf("task %s failed: %v", t.ID, err)
				t.State = "failed"
			} else {
				t.State = "done"
			}
			p.store.Update(t)
		}(task)
	}

	wg.Wait()
	return nil
}

func (p *Pool) execute(t *Task) error {
	// run the command
	fmt.Printf("running: %s\n", t.Name)
	return nil
}
```

What bugs would you catch? What's missing? What would you change before shipping this?
