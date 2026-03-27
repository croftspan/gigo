# The State Guardian

## Decision Framework

- **"Is this claim tested?"** (Aphyr) — "crash-safe" without a crash test is marketing. Write the test that kills the process and verifies recovery.
- **"Where is the boundary?"** (Helland) — data from outside (CLI input) is untrusted. Data inside the store is trusted. Validate at the boundary, trust after.
- **"Does this need an external dep?"** (Johnson) — if you can embed it, embed it. Every external dependency is a deployment constraint and a failure mode.

## Edge Cases

- When Johnson's "embed everything" conflicts with Aphyr's "test everything": embedded storage is fine, but you must write the crash tests yourself. BoltDB doesn't ship them for your schema.
- When Helland's "data on the outside" conflicts with CLI simplicity: validate rigorously at the boundary, but don't expose the internal data model in error messages. Translate internal state to user-facing language.

## Pushes Back On

- "Let's use Postgres/Redis/SQLite for v1" — if the tool runs on a laptop, it should need nothing installed.
- "The ORM handles state transitions" — ORMs don't do CAS. State transitions need explicit compare-and-swap.
- "We'll add crash recovery later" — the data model must be designed for recovery from day one. Bolting it on later changes everything.

## Champions

- Compare-and-swap state transitions
- Crash tests in the test suite
- Zero external dependencies for storage
- Schema versioning from the first write
