# Concurrency Patterns — tq

## Worker Pool with Supervision

The worker pool is bounded by a semaphore channel. Each worker goroutine is owned by the pool supervisor, which tracks lifecycle and handles failure.

**Supervision strategy (Armstrong):** When a worker panics or returns an error:
1. Record the failure against the task
2. Transition task state to `failed` (atomically, in the store)
3. Decide: retry (if retries remain), skip (mark failed), or abort (if task is critical)
4. The supervisor decides — the worker never decides its own fate

**Shutdown sequence (Pike + Kleppmann):**
1. Stop accepting new tasks
2. Signal all workers via context cancellation
3. Wait for in-progress tasks to reach a safe point (not just cancel them)
4. Persist final state of all in-progress tasks
5. Close the store
6. Exit

The "safe point" is the key tension: Pike would cancel and exit. Armstrong would let it crash and restart. Kleppmann insists on persisting state before shutdown. tq does all three in sequence — cancel the context (Pike), let workers reach a checkpoint (Armstrong's supervision boundary), persist state (Kleppmann), then exit.

## DAG Resolution

Topological sort at enqueue time. Cycle detection before any task is accepted.

- Use Kahn's algorithm (BFS-based) — iteratively remove nodes with no incoming edges
- If any nodes remain after exhaustion, there's a cycle — reject with the cycle path
- Store the resolved order alongside the task set for fast scheduling

## Channel Patterns

- Semaphore channel for worker pool bounding: `make(chan struct{}, maxWorkers)`
- Done channel for shutdown signaling (or `context.WithCancel`)
- Result channel per task for status reporting back to supervisor
- Never select on an unbuffered channel without a timeout or done case

## Error Propagation

Errors flow up, never sideways. A worker reports errors to the supervisor. The supervisor reports to the caller. The caller reports to the CLI. At each level, context is added — not stripped.
