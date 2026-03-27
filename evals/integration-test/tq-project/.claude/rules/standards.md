# Standards — tq

## Quality Gates

- Every goroutine has an owner and a shutdown path. `go test -race` passes on all packages.
- Every command produces grep-friendly text by default and structured JSON with `--json`.
- Every state transition is atomic and crash-safe. No "it uses BoltDB so it's fine" — test it.
- DAG cycle detection happens at enqueue time, not at run time.
- Single binary, `go install`-able, no CGO, no external runtime dependencies.

## Anti-Patterns

- **Goroutine leaks.** Spawning goroutines without cancellation context or shutdown coordination. Every goroutine must be traceable to an owner that stops it.
- **Silent failure swallowing.** `log.Println(err)` and continuing. If a task fails, the supervisor decides what happens — retry, skip, or abort. Never silently continue.
- **Untested durability claims.** Saying "crash-safe" without a test that kills the process mid-write and verifies recovery. Aphyr would test it. So do we.
- **Mixing persistence with logic.** Storage operations in command handlers or scheduler code. The store is an interface; everything else talks to the interface.
- **CLI output that assumes a terminal.** No ANSI codes without TTY detection. No fixed-width formatting. Default output works with `grep`, `awk`, `jq`.

## When to Go Deeper

When designing the worker pool or task scheduler, read `.claude/references/concurrency-patterns.md` — especially supervision trees and graceful shutdown sequences.
When implementing the data model or storage layer, read `.claude/references/persistence-patterns.md` — especially crash recovery testing and state machine transitions.
When designing CLI commands or output formats, read `.claude/references/cli-patterns.md` — especially pipe compatibility and error formatting.
