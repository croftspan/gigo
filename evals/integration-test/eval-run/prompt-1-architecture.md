# Prompt 1: Architecture/Planning

Design the worker pool and task scheduler for tq — a Go CLI task queue with priorities, dependencies, and concurrent workers.

Show:
1. The key types and interfaces (Store, Scheduler, WorkerPool, Task)
2. How tasks with dependencies are scheduled (DAG resolution)
3. How the worker pool bounds concurrency
4. How graceful shutdown works — what happens to in-progress tasks when the user hits Ctrl-C
5. How a crashed process recovers — what state are tasks in after an unclean shutdown

Produce Go type definitions and interface signatures. Include pseudocode or real code for the shutdown sequence and crash recovery logic.
