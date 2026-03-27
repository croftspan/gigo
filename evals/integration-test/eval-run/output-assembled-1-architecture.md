# tq Worker Pool & Task Scheduler Architecture

## 1. Core Types and Interfaces

### Task

```go
type State string

const (
    StatePending State = "pending" // created, deps not yet met
    StateReady   State = "ready"   // deps satisfied, eligible to run
    StateRunning State = "running" // claimed by a worker
    StateDone    State = "done"    // completed successfully
    StateFailed  State = "failed"  // failed, retries remain
    StateDead    State = "dead"    // failed, no retries remain
)

type Task struct {
    ID           string            `json:"id"`
    Command      []string          `json:"command"`
    Priority     int               `json:"priority"`    // higher = more urgent
    DependsOn    []string          `json:"depends_on"`  // task IDs that must be done first
    State        State             `json:"state"`
    Retries      int               `json:"retries"`
    MaxRetries   int               `json:"max_retries"`
    CreatedAt    time.Time         `json:"created_at"`
    StartedAt    *time.Time        `json:"started_at,omitempty"`
    FinishedAt   *time.Time        `json:"finished_at,omitempty"`
    WorkerPID    int               `json:"worker_pid,omitempty"`  // for crash detection
    Artifact     string            `json:"artifact,omitempty"`    // output path, for crash recovery
    Metadata     map[string]string `json:"metadata,omitempty"`
}
```

### Store Interface

```go
// Store is the only path to durable task state. All callers go through this interface.
// Implementations must be safe for concurrent use.
type Store interface {
    // Add enqueues a new task. Validates DAG — returns ErrCycle if deps form a cycle.
    Add(task Task) error

    // Get retrieves a single task by ID.
    Get(id string) (Task, error)

    // List returns tasks matching the filter, ordered by priority desc, created_at asc.
    List(filter Filter) ([]Task, error)

    // Transition atomically moves a task from one state to another.
    // Returns ErrWrongState if current state != from. This is the compare-and-swap
    // that makes concurrent workers safe — only one worker can win the transition
    // from ready → running.
    Transition(id string, from, to State) error

    // Update writes fields to an existing task (used to record StartedAt, WorkerPID, etc.)
    Update(id string, fn func(*Task)) error

    // Delete removes a task permanently.
    Delete(id string) error

    // Close flushes and closes the underlying storage. Must be called on shutdown.
    Close() error
}

type Filter struct {
    State    []State
    Priority *int
    Limit    int
}

var (
    ErrNotFound   = errors.New("task not found")
    ErrWrongState = errors.New("task not in expected state")
    ErrCycle      = errors.New("dependency cycle detected")
    ErrDuplicate  = errors.New("task id already exists")
)
```

### Scheduler Interface

```go
// Scheduler decides which tasks are eligible to run and promotes them from
// pending → ready when their dependencies are satisfied.
type Scheduler interface {
    // Tick scans pending tasks and transitions eligible ones to ready.
    // Called after any task reaches StateDone.
    Tick(ctx context.Context) error

    // Next claims the highest-priority ready task for a worker.
    // Transitions it from ready → running atomically.
    // Returns nil, nil if no tasks are ready.
    Next(ctx context.Context) (*Task, error)
}

// Notify is sent on the ready channel whenever Tick promotes tasks.
// Workers use this to avoid polling.
type Notify struct{}
```

### WorkerPool

```go
// WorkerPool bounds concurrency and owns all worker goroutines.
// It is the supervisor — workers report results back; the pool decides fate.
type WorkerPool interface {
    // Start launches workers and begins processing.
    Start(ctx context.Context) error

    // Wait blocks until all workers have stopped.
    Wait()
}

// Runner executes a single task. The pool calls this in each worker goroutine.
type Runner interface {
    Run(ctx context.Context, task Task) error
}

// Result is what a worker sends back to the supervisor after attempting a task.
type Result struct {
    Task  Task
    Err   error
}
```

---

## 2. DAG Resolution

Cycle detection happens at enqueue time — not at run time. Discovering a cycle when a task is already queued is too late.

```go
// detectCycle uses DFS on the dependency graph stored in the database.
// Called inside Store.Add before persisting the new task.
func (s *boltStore) detectCycle(newTask Task) error {
    // Build adjacency from existing tasks
    all, _ := s.List(Filter{})
    graph := make(map[string][]string, len(all)+1)
    for _, t := range all {
        graph[t.ID] = t.DependsOn
    }
    graph[newTask.ID] = newTask.DependsOn

    visited := make(map[string]bool)
    inStack := make(map[string]bool)

    var dfs func(id string) bool
    dfs = func(id string) bool {
        if inStack[id] {
            return true // back edge — cycle
        }
        if visited[id] {
            return false
        }
        visited[id] = true
        inStack[id] = true
        for _, dep := range graph[id] {
            if dfs(dep) {
                return true
            }
        }
        inStack[id] = false
        return false
    }

    if dfs(newTask.ID) {
        return ErrCycle
    }
    return nil
}
```

Promoting pending → ready:

```go
// Tick is called after any task transitions to done.
// It finds pending tasks whose every dependency is now done and promotes them.
func (s *defaultScheduler) Tick(ctx context.Context) error {
    pending, err := s.store.List(Filter{State: []State{StatePending}})
    if err != nil {
        return err
    }

    for _, task := range pending {
        if s.depsAllDone(ctx, task) {
            // Transition may fail (ErrWrongState) if another scheduler raced us.
            // That's fine — idempotent. Log and skip.
            if err := s.store.Transition(task.ID, StatePending, StateReady); err != nil {
                if !errors.Is(err, ErrWrongState) {
                    return err
                }
            }
        }
    }
    return nil
}

func (s *defaultScheduler) depsAllDone(ctx context.Context, task Task) bool {
    for _, depID := range task.DependsOn {
        dep, err := s.store.Get(depID)
        if err != nil || dep.State != StateDone {
            return false
        }
    }
    return true
}
```

Claiming the next task:

```go
// Next picks the highest-priority ready task and atomically claims it.
// Uses Transition(ready → running) as the CAS — only one caller wins.
func (s *defaultScheduler) Next(ctx context.Context) (*Task, error) {
    candidates, err := s.store.List(Filter{State: []State{StateReady}, Limit: 20})
    if err != nil {
        return nil, err
    }
    // List returns priority desc. Try each until one claim succeeds.
    for _, task := range candidates {
        err := s.store.Transition(task.ID, StateReady, StateRunning)
        if err == nil {
            // Record start time and worker PID for crash recovery
            now := time.Now()
            _ = s.store.Update(task.ID, func(t *Task) {
                t.StartedAt = &now
                t.WorkerPID = os.Getpid()
            })
            claimed := task
            claimed.State = StateRunning
            return &claimed, nil
        }
        if !errors.Is(err, ErrWrongState) {
            return nil, err
        }
        // ErrWrongState: another worker claimed it. Try the next candidate.
    }
    return nil, nil
}
```

---

## 3. Worker Pool — Bounded Concurrency

The pool uses a semaphore channel to bound concurrency. Each worker goroutine is owned by the pool and reports results via a channel. The pool is the supervisor — it decides what happens after a failure.

```go
type pool struct {
    scheduler Scheduler
    runner    Runner
    store     Store
    sem       chan struct{}    // semaphore, len = max concurrency
    results   chan Result
    ready     chan Notify     // scheduler signals when tasks become ready
    wg        sync.WaitGroup
}

func NewWorkerPool(concurrency int, sched Scheduler, runner Runner, store Store) WorkerPool {
    return &pool{
        scheduler: sched,
        runner:    runner,
        store:     store,
        sem:       make(chan struct{}, concurrency),
        results:   make(chan Result, concurrency),
        ready:     make(chan Notify, 1), // buffered: one pending notification is enough
    }
}

func (p *pool) Start(ctx context.Context) error {
    p.wg.Add(1)
    go p.supervise(ctx)
    return nil
}

func (p *pool) Wait() {
    p.wg.Wait()
}

// supervise is the single goroutine that owns the scheduling loop and all workers.
// It never touches state directly — it calls the scheduler and processes results.
func (p *pool) supervise(ctx context.Context) {
    defer p.wg.Done()

    for {
        select {
        case <-ctx.Done():
            // Drain in-progress results before exiting
            p.drainResults()
            return

        case result := <-p.results:
            p.handleResult(ctx, result)

        case <-p.ready:
            p.dispatchAvailable(ctx)

        case <-time.After(500 * time.Millisecond):
            // Periodic poll — catches any notify races
            p.dispatchAvailable(ctx)
        }
    }
}

// dispatchAvailable claims and dispatches as many ready tasks as semaphore allows.
func (p *pool) dispatchAvailable(ctx context.Context) {
    for {
        select {
        case p.sem <- struct{}{}: // acquire slot
            task, err := p.scheduler.Next(ctx)
            if err != nil || task == nil {
                <-p.sem // release slot — nothing to run
                return
            }
            p.wg.Add(1)
            go p.runWorker(ctx, *task)
        default:
            return // all slots busy
        }
    }
}

func (p *pool) runWorker(ctx context.Context, task Task) {
    defer p.wg.Done()
    defer func() { <-p.sem }() // release slot when done

    // Workers run with the pool context — they respect cancellation.
    err := p.runner.Run(ctx, task)
    p.results <- Result{Task: task, Err: err}
}

// handleResult is the supervisor's decision point. The worker never decides its own fate.
func (p *pool) handleResult(ctx context.Context, result Result) {
    if result.Err == nil {
        // Success
        _ = p.store.Transition(result.Task.ID, StateRunning, StateDone)
        // Promote any tasks that were waiting on this one
        _ = p.scheduler.Tick(ctx)
        p.ready <- Notify{} // signal supervise loop to dispatch more
        return
    }

    // Failure — supervisor decides
    task := result.Task
    if task.Retries < task.MaxRetries {
        // Retry: back to ready
        _ = p.store.Update(task.ID, func(t *Task) { t.Retries++ })
        _ = p.store.Transition(task.ID, StateRunning, StateReady)
        p.ready <- Notify{}
    } else {
        // Dead: no retries left
        _ = p.store.Transition(task.ID, StateRunning, StateDead)
        // Dependent tasks stay pending forever — surface this to the operator
        log.Printf("task %s is dead after %d retries: %v", task.ID, task.Retries, result.Err)
    }
}
```

---

## 4. Graceful Shutdown

When the user hits Ctrl-C, the process receives SIGINT. The shutdown sequence follows Pike (context propagation) and Kleppmann (no committed work lost):

```go
func main() {
    ctx, cancel := context.WithCancel(context.Background())

    // Catch Ctrl-C
    sigs := make(chan os.Signal, 1)
    signal.Notify(sigs, os.Interrupt, syscall.SIGTERM)
    go func() {
        <-sigs
        log.Println("shutdown: stopping new task dispatch")
        cancel() // signals pool supervisor and all workers
    }()

    store := mustOpenStore()
    sched := newScheduler(store)
    runner := newRunner()
    pool := NewWorkerPool(4, sched, runner, store)

    if err := pool.Start(ctx); err != nil {
        log.Fatal(err)
    }

    pool.Wait() // blocks until supervisor and all workers exit

    // All workers have stopped. Now persist final state and close storage.
    // Any task still in StateRunning at this point did not finish cleanly —
    // transition it back to StateReady so crash recovery picks it up on next start.
    if err := recoverInFlight(store); err != nil {
        log.Printf("shutdown: recovery error: %v", err)
    }

    if err := store.Close(); err != nil {
        log.Printf("shutdown: store close error: %v", err)
    }

    log.Println("shutdown: clean exit")
}
```

What happens to in-progress tasks:

1. `cancel()` fires — the context is cancelled. All worker goroutines receive this via `ctx.Done()`.
2. Workers respect context cancellation in `runner.Run`. The runner passes `ctx` to `exec.CommandContext`, so the subprocess receives SIGKILL after a grace period.
3. Workers finish their current unit of work (or reach cancellation) and send a Result.
4. The supervisor's `drainResults` loop collects all outstanding results before the supervisor goroutine exits.
5. `pool.Wait()` returns only after the supervisor and all worker goroutines exit.
6. `recoverInFlight` scans for any remaining `running` tasks and transitions them back to `ready`. On a clean shutdown these should be zero; this is the safety net.
7. `store.Close()` flushes all pending writes and closes the file handle.

```go
// drainResults collects all pending results after ctx is cancelled.
// Workers have already received the cancellation; this just empties the channel.
func (p *pool) drainResults() {
    // Give workers a moment to land their results
    deadline := time.After(5 * time.Second)
    for {
        select {
        case result := <-p.results:
            // Record what we know — worker stopped, state is uncertain
            _ = p.store.Transition(result.Task.ID, StateRunning, StateReady)
        case <-deadline:
            return
        }
    }
}
```

---

## 5. Crash Recovery

An unclean shutdown (OOM kill, power loss, `kill -9`) leaves tasks in `StateRunning` with no worker alive to finish them. On next startup, before accepting any new work:

```go
// RecoverOnStartup is called once, before the pool starts.
// It inspects all running tasks and decides their fate based on observable evidence.
func RecoverOnStartup(store Store) error {
    running, err := store.List(Filter{State: []State{StateRunning}})
    if err != nil {
        return fmt.Errorf("crash recovery: list running: %w", err)
    }

    for _, task := range running {
        fate := assessTaskFate(task)
        switch fate {
        case fateComplete:
            // Output artifact exists and is valid — treat as done
            log.Printf("recovery: task %s artifact present, marking done", task.ID)
            if err := store.Transition(task.ID, StateRunning, StateDone); err != nil {
                return fmt.Errorf("recovery: %w", err)
            }

        case fateIncomplete:
            // No artifact — the task did not finish. Retry if retries remain.
            if task.Retries < task.MaxRetries {
                log.Printf("recovery: task %s incomplete, requeueing (retry %d/%d)",
                    task.ID, task.Retries+1, task.MaxRetries)
                if err := store.Update(task.ID, func(t *Task) { t.Retries++ }); err != nil {
                    return err
                }
                if err := store.Transition(task.ID, StateRunning, StateReady); err != nil {
                    return fmt.Errorf("recovery: %w", err)
                }
            } else {
                log.Printf("recovery: task %s out of retries, marking dead", task.ID)
                if err := store.Transition(task.ID, StateRunning, StateDead); err != nil {
                    return fmt.Errorf("recovery: %w", err)
                }
            }
        }
    }

    return nil
}

type taskFate int

const (
    fateComplete   taskFate = iota
    fateIncomplete taskFate = iota
)

func assessTaskFate(task Task) taskFate {
    if task.Artifact == "" {
        // No artifact configured — assume incomplete
        return fateIncomplete
    }
    info, err := os.Stat(task.Artifact)
    if err != nil {
        return fateIncomplete
    }
    // Artifact exists and was modified after the task started — complete
    if task.StartedAt != nil && info.ModTime().After(*task.StartedAt) {
        return fateComplete
    }
    return fateIncomplete
}
```

After recovery runs, the scheduler's first `Tick` will promote any newly-ready tasks whose dependencies were completed before the crash.

---

## Architecture Summary

```
main()
  │
  ├─ Store (BoltDB, single file, CAS transitions)
  │
  ├─ Scheduler (reads store, promotes pending→ready, claims ready→running)
  │
  └─ WorkerPool (supervisor goroutine owns N worker goroutines)
       │
       ├─ sem channel (cap=N) — semaphore bounding concurrency
       ├─ results channel — workers report outcomes, supervisor decides fate
       └─ ready channel — scheduler notifies supervisor when work is available

On startup:   RecoverOnStartup → pool.Start
On SIGINT:    cancel() → workers stop → drainResults → recoverInFlight → store.Close
On task done: worker → results channel → supervisor → Tick → promote deps → dispatch more
```

Key invariants:
- **Only `Transition` (CAS) writes state changes.** No goroutine reads state and then writes without going through the store's atomic transition.
- **The supervisor decides, never the worker.** Workers return results; the pool's `handleResult` function decides retry vs dead vs done.
- **Cycle detection at enqueue time.** `Store.Add` calls `detectCycle` before writing. A cycle never enters the database.
- **`go test -race` is the gate.** Every channel hand-off is the only synchronization point — no mutexes on shared task state.
