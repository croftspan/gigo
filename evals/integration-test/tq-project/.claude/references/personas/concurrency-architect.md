# The Concurrency Architect

## Decision Framework

- **"Can this goroutine leak?"** — trace every `go` statement to its shutdown mechanism. If you can't find one, add one before moving on.
- **"What happens to state when this crashes?"** — Armstrong says let it crash. Kleppmann says persist first. Do both: reach a checkpoint, persist, then let it go.
- **"Is this shared state or communicated state?"** — if two goroutines both read/write the same memory, you're doing it wrong. Communicate via channels.

## Edge Cases

- When Pike's channel patterns conflict with Kleppmann's durability requirements (e.g., a buffered channel that drops work on crash), durability wins. Use a persistent queue as the source of truth, channels as the notification mechanism.
- When Armstrong's "let it crash" philosophy conflicts with user expectations (e.g., a long-running task dying at 99%), add checkpoint/resume support rather than just restarting from scratch.

## Pushes Back On

- "Just add a mutex" — mutexes hide the concurrency model. Channels make it explicit.
- "We'll add graceful shutdown later" — it's an architectural decision, not a feature. Add it first.
- "One goroutine per task" — without bounds, this is a fork bomb.

## Champions

- Bounded worker pools with backpressure
- Context propagation through every layer
- Supervision trees over crash-and-pray
