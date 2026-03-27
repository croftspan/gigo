# Persistence Patterns — tq

## Storage Interface

The store is an interface. Everything talks to the interface. Command handlers, scheduler, workers — none of them know whether tasks live in BoltDB, SQLite, or memory.

```go
type Store interface {
    Add(task Task) error
    Get(id string) (Task, error)
    List(filter Filter) ([]Task, error)
    Transition(id string, from, to State) error  // CAS — fails if current != from
    Delete(id string) error
    Close() error
}
```

The `Transition` method is a compare-and-swap. It atomically checks the current state matches `from` before setting `to`. This prevents double-transitions (e.g., two workers both trying to claim the same task).

## Task State Machine

```
pending → ready → running → done
                         ↘ failed → ready (retry)
                                  ↘ dead (max retries)
```

- `pending`: has unresolved dependencies
- `ready`: all dependencies satisfied, available for scheduling
- `running`: claimed by a worker
- `done`: completed successfully
- `failed`: worker reported failure, may retry
- `dead`: exhausted retries

Every transition goes through `Store.Transition()` with CAS semantics.

## Crash Recovery (Aphyr's test)

On startup, scan for tasks in `running` state. These were in-progress when the process died.

Recovery strategy:
1. Check if the task's output artifact exists (if applicable)
2. If complete: transition to `done`
3. If incomplete/missing: transition back to `ready` for re-execution
4. Log the recovery action

**The crash test:** Write a test that:
1. Starts a queue with tasks
2. Begins execution
3. Kills the process (or simulates via store close without clean shutdown)
4. Restarts and verifies all tasks reach terminal state (done or dead)
5. Verifies no task is silently lost

## Data Boundaries (Helland)

Task definitions that come from outside (CLI input, file import) are validated at the boundary. Once inside the store, data is trusted. The boundary is the CLI command layer — it validates, normalizes, and rejects before anything reaches the store.

Schema evolution: use a version field in the stored data. Migration runs on startup if version < current. Never silently ignore unknown fields.
