# tq — Worker Pool and Task Scheduler Design

## Overview

This document covers the core architecture for `tq`, a Go CLI task queue with priorities, DAG-based dependency resolution, concurrent workers, graceful shutdown, and crash recovery.

---

## 1. Key Types and Interfaces

### Task

```go
// TaskStatus represents the lifecycle state of a task.
type TaskStatus string

const (
    StatusPending   TaskStatus = "pending"    // waiting to be scheduled
    StatusReady     TaskStatus = "ready"      // dependencies satisfied, eligible to run
    StatusRunning   TaskStatus = "running"    // currently executing on a worker
    StatusDone      TaskStatus = "done"       // completed successfully
    StatusFailed    TaskStatus = "failed"     // completed with error
    StatusCancelled TaskStatus = "cancelled"  // cancelled before execution
)

// Priority controls scheduling order among ready tasks.
type Priority int

const (
    PriorityLow    Priority = 0
    PriorityNormal Priority = 5
    PriorityHigh   Priority = 10
    PriorityCrit   Priority = 20
)

// Task is the unit of work in the queue.
type Task struct {
    ID           string            // unique identifier (UUID or user-supplied slug)
    Command      []string          // argv to exec, e.g. ["go", "test", "./..."]
    Priority     Priority          // scheduling weight
    DependsOn    []string          // IDs of tasks that must be Done before this runs
    Status       TaskStatus        // current lifecycle state
    CreatedAt    time.Time
    StartedAt    *time.Time        // nil until worker picks it up
    FinishedAt   *time.Time        // nil until terminal state
    WorkerPID    int               // PID of worker process; 0 if not running
    ExitCode     *int              // nil until finished
    Retries      int               // number of retry attempts made
    MaxRetries   int               // maximum retries allowed (0 = no retries)
    Env          map[string]string // environment overrides
    WorkDir      string            // working directory for the command
    Output       string            // path to captured stdout/stderr file
}
```

### Store

The store is the single source of truth. All state mutations go through it. It is persistence-backed (SQLite by default) so recovery after a crash is possible.

```go
// Store persists task state. Implementations: SQLiteStore, MemStore (tests).
type Store interface {
    // Write
    Add(ctx context.Context, t *Task) error
    UpdateStatus(ctx context.Context, id string, status TaskStatus) error
    UpdateWorkerPID(ctx context.Context, id string, pid int) error
    SetStarted(ctx context.Context, id string, pid int, at time.Time) error
    SetFinished(ctx context.Context, id string, status TaskStatus, exitCode int, at time.Time) error
    IncrementRetries(ctx context.Context, id string) error

    // Read
    Get(ctx context.Context, id string) (*Task, error)
    List(ctx context.Context, filter ListFilter) ([]*Task, error)
    ReadyTasks(ctx context.Context) ([]*Task, error)   // status=ready, ordered by priority desc
    RunningTasks(ctx context.Context) ([]*Task, error) // status=running

    // Atomic transition helpers (used for crash recovery)
    ClaimTask(ctx context.Context, id string, workerPID int) (bool, error) // CAS: pending->running
    ReclaimOrphan(ctx context.Context, id string) error // running->ready for recovery

    Close() error
}

// ListFilter controls which tasks List() returns.
type ListFilter struct {
    Status   []TaskStatus
    MinPriority Priority
    Limit    int
    Offset   int
}
```

### Scheduler

The scheduler owns the DAG. It watches the store for state changes and promotes tasks from `pending` to `ready` when their dependencies are satisfied.

```go
// Scheduler resolves dependencies and marks tasks ready for execution.
type Scheduler interface {
    // Start begins the scheduling loop. Blocks until ctx is cancelled.
    Start(ctx context.Context) error

    // Notify tells the scheduler a task's status changed.
    // Called by the store layer or worker pool after each terminal event.
    Notify(taskID string)

    // DAGFor returns the dependency graph for a set of task IDs.
    // Used for cycle detection at enqueue time.
    DAGFor(ctx context.Context, ids []string) (*DAG, error)
}

// DAG is an adjacency list representation of the dependency graph.
type DAG struct {
    Nodes map[string]*Task
    Edges map[string][]string // id -> list of dependency IDs
}
```

### WorkerPool

```go
// WorkerPool bounds concurrency and dispatches ready tasks to workers.
type WorkerPool interface {
    // Start launches the pool. Blocks until ctx is cancelled.
    Start(ctx context.Context) error

    // Size returns the number of active workers.
    Size() int

    // Resize adjusts the number of concurrent workers at runtime.
    Resize(n int) error
}
```

### Internal worker

```go
// worker is an internal unit managed by the pool.
type worker struct {
    id     int
    pool   *poolImpl
    stopCh chan struct{}
}

// poolImpl is the concrete WorkerPool.
type poolImpl struct {
    store     Store
    scheduler Scheduler
    maxWorkers int
    taskCh    chan *Task       // unbuffered: pool feeds tasks one at a time
    wg        sync.WaitGroup  // tracks in-flight workers
    mu        sync.Mutex
    running   map[string]*exec.Cmd // taskID -> live process
    logger    *slog.Logger
}
```

---

## 2. DAG Resolution and Scheduling

### Cycle Detection at Enqueue Time

Before a task is written to the store, the scheduler checks for cycles using depth-first search.

```go
// ErrCycle is returned when a dependency cycle is detected.
var ErrCycle = errors.New("dependency cycle detected")

// CheckCycle returns ErrCycle if adding task t would create a cycle
// in the existing dependency graph.
func (d *DAG) CheckCycle(t *Task) error {
    // Build a temporary adjacency list including the new task.
    adj := make(map[string][]string, len(d.Edges)+1)
    for k, v := range d.Edges {
        adj[k] = v
    }
    adj[t.ID] = t.DependsOn

    // DFS from every node; detect back edges.
    visited := make(map[string]int) // 0=unvisited, 1=in-stack, 2=done
    var dfs func(id string) bool
    dfs = func(id string) bool {
        if visited[id] == 1 {
            return true // cycle
        }
        if visited[id] == 2 {
            return false
        }
        visited[id] = 1
        for _, dep := range adj[id] {
            if dfs(dep) {
                return true
            }
        }
        visited[id] = 2
        return false
    }

    for id := range adj {
        if visited[id] == 0 && dfs(id) {
            return ErrCycle
        }
    }
    return nil
}
```

### Promoting Pending Tasks to Ready

The scheduler runs a promotion loop. Each cycle it scans pending tasks and checks whether all dependencies are in `StatusDone`.

```go
// scheduleLoop is the main goroutine of the scheduler.
func (s *schedulerImpl) scheduleLoop(ctx context.Context) {
    ticker := time.NewTicker(500 * time.Millisecond)
    defer ticker.Stop()

    notifyCh := s.notifyCh // buffered channel, capacity 64

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            s.promoteReady(ctx)
        case <-notifyCh:
            // Drain burst of notifications, then promote once.
            for len(notifyCh) > 0 {
                <-notifyCh
            }
            s.promoteReady(ctx)
        }
    }
}

func (s *schedulerImpl) promoteReady(ctx context.Context) {
    pending, err := s.store.List(ctx, ListFilter{Status: []TaskStatus{StatusPending}})
    if err != nil {
        s.logger.Error("list pending failed", "err", err)
        return
    }

    for _, t := range pending {
        if s.depsAllDone(ctx, t.DependsOn) {
            if err := s.store.UpdateStatus(ctx, t.ID, StatusReady); err != nil {
                s.logger.Error("promote failed", "id", t.ID, "err", err)
                continue
            }
            s.logger.Info("task promoted to ready", "id", t.ID)
        }
    }
}

func (s *schedulerImpl) depsAllDone(ctx context.Context, depIDs []string) bool {
    for _, id := range depIDs {
        dep, err := s.store.Get(ctx, id)
        if err != nil || dep.Status != StatusDone {
            return false
        }
    }
    return true
}
```

### Priority Queue within the Pool

The pool pulls from `store.ReadyTasks()`, which returns tasks ordered by `priority DESC, created_at ASC`. This gives a strict priority queue with FIFO tie-breaking at the same priority level. No in-memory heap is needed; the store handles ordering via SQL `ORDER BY`.

```sql
-- SQLiteStore.ReadyTasks implementation
SELECT * FROM tasks
WHERE status = 'ready'
ORDER BY priority DESC, created_at ASC;
```

---

## 3. Bounding Concurrency — Worker Pool

The pool maintains exactly `maxWorkers` goroutines, each pulling tasks through a shared channel.

```go
func (p *poolImpl) Start(ctx context.Context) error {
    p.logger.Info("worker pool starting", "workers", p.maxWorkers)

    for i := 0; i < p.maxWorkers; i++ {
        p.wg.Add(1)
        go p.runWorker(ctx, i)
    }

    p.wg.Wait()
    p.logger.Info("worker pool stopped")
    return nil
}

// runWorker is the per-goroutine loop. Each worker blocks on the poll loop,
// picks one task, runs it to completion, then loops.
func (p *poolImpl) runWorker(ctx context.Context, id int) {
    defer p.wg.Done()
    p.logger.Debug("worker started", "worker", id)

    for {
        select {
        case <-ctx.Done():
            p.logger.Debug("worker stopping", "worker", id)
            return
        default:
        }

        task, err := p.claimNextTask(ctx)
        if err != nil {
            // No task available; back off briefly.
            select {
            case <-time.After(200 * time.Millisecond):
            case <-ctx.Done():
                return
            }
            continue
        }

        p.executeTask(ctx, task)
    }
}

// claimNextTask atomically picks the highest-priority ready task.
// Uses optimistic concurrency: ReadyTasks() returns candidates,
// ClaimTask() does a compare-and-swap in the store.
func (p *poolImpl) claimNextTask(ctx context.Context) (*Task, error) {
    candidates, err := p.store.ReadyTasks(ctx)
    if err != nil {
        return nil, err
    }
    for _, t := range candidates {
        ok, err := p.store.ClaimTask(ctx, t.ID, os.Getpid())
        if err != nil {
            continue
        }
        if ok {
            return t, nil
        }
        // Another worker claimed it; try next candidate.
    }
    return nil, errors.New("no task available")
}
```

`ClaimTask` in SQLite uses a single atomic UPDATE with a WHERE guard:

```sql
UPDATE tasks
SET status = 'running', worker_pid = ?, started_at = ?
WHERE id = ? AND status = 'ready';
-- Returns rows-affected; 1 = claimed, 0 = lost the race.
```

### Executing a Task

```go
func (p *poolImpl) executeTask(ctx context.Context, t *Task) {
    outFile, _ := os.CreateTemp("", "tq-output-"+t.ID+"-*")
    defer outFile.Close()

    cmd := exec.CommandContext(ctx, t.Command[0], t.Command[1:]...)
    cmd.Dir = t.WorkDir
    cmd.Stdout = outFile
    cmd.Stderr = outFile
    for k, v := range t.Env {
        cmd.Env = append(cmd.Env, k+"="+v)
    }

    // Register the live process so shutdown can signal it.
    p.mu.Lock()
    p.running[t.ID] = cmd
    p.mu.Unlock()

    err := cmd.Start()
    if err != nil {
        p.finishTask(ctx, t, -1, err)
        return
    }

    // Record the worker PID in the store for crash recovery.
    _ = p.store.UpdateWorkerPID(ctx, t.ID, cmd.Process.Pid)

    err = cmd.Wait()

    p.mu.Lock()
    delete(p.running, t.ID)
    p.mu.Unlock()

    exitCode := 0
    if err != nil {
        var exitErr *exec.ExitError
        if errors.As(err, &exitErr) {
            exitCode = exitErr.ExitCode()
        } else {
            exitCode = -1
        }
    }

    p.finishTask(ctx, t, exitCode, err)
}

func (p *poolImpl) finishTask(ctx context.Context, t *Task, exitCode int, err error) {
    status := StatusDone
    if err != nil {
        if t.Retries < t.MaxRetries {
            _ = p.store.IncrementRetries(context.Background(), t.ID)
            _ = p.store.UpdateStatus(context.Background(), t.ID, StatusReady)
            p.scheduler.Notify(t.ID)
            return
        }
        status = StatusFailed
    }
    _ = p.store.SetFinished(context.Background(), t.ID, status, exitCode, time.Now())
    p.scheduler.Notify(t.ID) // wake scheduler so dependents can be promoted
}
```

---

## 4. Graceful Shutdown

The shutdown sequence has three goals:
1. Stop accepting new tasks.
2. Allow in-progress tasks to finish (up to a configurable drain timeout).
3. If the drain timeout expires, send SIGTERM then SIGKILL to remaining processes.

### Signal Handling

```go
func Run(pool WorkerPool, scheduler Scheduler, drainTimeout time.Duration) error {
    rootCtx, cancel := context.WithCancel(context.Background())
    defer cancel()

    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

    // Start scheduler and pool in background goroutines.
    errCh := make(chan error, 2)
    go func() { errCh <- scheduler.Start(rootCtx) }()
    go func() { errCh <- pool.Start(rootCtx) }()

    // Wait for a signal or a fatal error.
    select {
    case sig := <-sigCh:
        log.Printf("received %s, initiating shutdown", sig)
    case err := <-errCh:
        log.Printf("fatal error: %v", err)
        cancel()
        return err
    }

    // Phase 1: Stop accepting new tasks (cancel the root context).
    // Workers finish their current task or respect ctx.Done() during Wait().
    cancel()

    // Phase 2: Drain in-progress tasks.
    drainDone := make(chan struct{})
    go func() {
        pool.(*poolImpl).wg.Wait()
        close(drainDone)
    }()

    select {
    case <-drainDone:
        log.Println("clean shutdown: all tasks finished")
    case <-time.After(drainTimeout):
        log.Println("drain timeout: terminating running processes")
        pool.(*poolImpl).killAll(syscall.SIGTERM)
        select {
        case <-drainDone:
            log.Println("processes terminated gracefully")
        case <-time.After(5 * time.Second):
            log.Println("force-killing remaining processes")
            pool.(*poolImpl).killAll(syscall.SIGKILL)
            pool.(*poolImpl).wg.Wait()
        }
    }

    return nil
}
```

### Killing In-Progress Processes

```go
// killAll sends sig to every process currently tracked by the pool.
func (p *poolImpl) killAll(sig syscall.Signal) {
    p.mu.Lock()
    defer p.mu.Unlock()

    for taskID, cmd := range p.running {
        if cmd.Process != nil {
            p.logger.Info("sending signal to process", "task", taskID, "pid", cmd.Process.Pid, "sig", sig)
            _ = cmd.Process.Signal(sig)
        }
    }
}
```

### What Happens to In-Progress Tasks

When a worker's `cmd.Wait()` returns due to a signal:

- If the process exits with a non-zero code, `finishTask` is called with the exit code.
- If `MaxRetries > 0` and retries remain, the task is reset to `StatusReady` for the next run.
- If retries are exhausted or `MaxRetries == 0`, the task is marked `StatusFailed`.
- If `ctx.Done()` fires during `claimNextTask` (no task was claimed yet), the worker simply exits — no task state is touched.

The key invariant: **a task is only in `StatusFailed` or `StatusDone` when `finishTask` commits to the store. A task killed mid-execution ends up `StatusFailed` (or re-queued as `StatusReady` if retries remain).**

---

## 5. Crash Recovery

A crash (OOM kill, power loss, `kill -9`) leaves some tasks in `StatusRunning` with a `worker_pid` that no longer exists. On next startup, the recovery routine detects and repairs these orphans.

### Detecting Orphans

```go
// RecoverOrphans is called once at startup, before the scheduler and pool begin.
func RecoverOrphans(ctx context.Context, store Store, logger *slog.Logger) error {
    running, err := store.RunningTasks(ctx)
    if err != nil {
        return fmt.Errorf("list running tasks: %w", err)
    }

    for _, t := range running {
        alive := processIsAlive(t.WorkerPID)
        if alive {
            // Process survived (e.g. we are the same process after a hot reload).
            // Leave it running.
            continue
        }
        // The worker process is gone. Decide what to do with the task.
        if t.Retries < t.MaxRetries {
            logger.Info("orphaned task re-queued", "id", t.ID, "pid", t.WorkerPID)
            if err := store.IncrementRetries(ctx, t.ID); err != nil {
                return err
            }
            if err := store.ReclaimOrphan(ctx, t.ID); err != nil { // running -> ready
                return err
            }
        } else {
            logger.Warn("orphaned task marked failed", "id", t.ID, "pid", t.WorkerPID)
            now := time.Now()
            if err := store.SetFinished(ctx, t.ID, StatusFailed, -1, now); err != nil {
                return err
            }
        }
    }
    return nil
}

// processIsAlive checks whether a PID is still running on this machine.
// On Linux/macOS: send signal 0 to test existence without side effects.
func processIsAlive(pid int) bool {
    if pid <= 0 {
        return false
    }
    process, err := os.FindProcess(pid)
    if err != nil {
        return false
    }
    err = process.Signal(syscall.Signal(0))
    return err == nil
}
```

`ReclaimOrphan` in SQLite:

```sql
UPDATE tasks
SET status = 'ready', worker_pid = 0, started_at = NULL
WHERE id = ? AND status = 'running';
```

### Task State After Unclean Shutdown

| Scenario | Task state at crash | State after recovery |
|---|---|---|
| Task pending, never claimed | `pending` | `pending` (unchanged, scheduler re-evaluates deps) |
| Task ready, not yet claimed | `ready` | `ready` (unchanged) |
| Task running, process alive | `running` | `running` (left alone) |
| Task running, process dead, retries remain | `running` | `ready` (re-queued, retry count incremented) |
| Task running, process dead, no retries | `running` | `failed` (exit code -1) |
| Task done or failed | terminal state | unchanged |

### Store Durability Guarantees

For SQLite, `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` give crash-safe writes with acceptable performance:

```go
func openDB(path string) (*sql.DB, error) {
    db, err := sql.Open("sqlite3", path+"?_journal_mode=WAL&_synchronous=NORMAL")
    if err != nil {
        return nil, err
    }
    // Single writer avoids lock contention; WAL allows concurrent readers.
    db.SetMaxOpenConns(1)
    return db, nil
}
```

All status transitions use SQLite transactions so partial writes cannot corrupt state. The `ClaimTask` CAS operation is a single-statement atomic UPDATE (no explicit transaction needed; SQLite auto-commits each statement by default).

---

## Summary: Invariants the Design Upholds

1. **At most one worker claims a task** — `ClaimTask` uses a compare-and-swap UPDATE; concurrent workers naturally lose the race and move to the next candidate.
2. **No task is lost on crash** — running tasks are either re-queued or failed on startup before any new work begins.
3. **Dependencies are respected** — tasks never enter `ready` until all `DependsOn` tasks are `done`; cycle detection at enqueue time prevents deadlock.
4. **Concurrency is bounded** — exactly `maxWorkers` goroutines, each holding at most one task at a time.
5. **Shutdown is orderly** — SIGINT drains in-flight tasks before terminating processes, with a hard timeout as a safety net.
