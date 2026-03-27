# Three-Way Pipeline Evaluation

**Judge:** Principal Go Engineer
**Date:** 2026-03-27
**Task:** tq -- Go CLI task queue with priorities, dependencies, concurrent workers

---

## 1. ARCHITECTURAL COHERENCE

Does the implementation follow its architecture? Same types, interfaces, error patterns, placement of concerns?

### Pipeline X: 4/5

X shares Z's architecture and follows it closely. All six State constants present. The 7-method Store interface is reproduced exactly. Sentinel errors match. Cycle detection lives inside `Store.Add` as the architecture specifies. The `Task` struct mirrors the architecture's shape including `Metadata`, `Artifact`, `WorkerPID`, `MaxRetries`.

Two deviations prevent a perfect score. First, the name is stored in `Metadata["name"]` rather than as a first-class field -- the architecture's Task struct has no Name field, so this is technically faithful to the spec, but the CLI's `Use: "add <name>"` implies a real Name field. This is an interpretation gap, not a contradiction. Second, all tasks start as `StatePending` regardless of whether they have dependencies. The architecture's scheduler promotes pending to ready when deps are satisfied, so this is consistent with the architecture but less user-friendly than starting no-dep tasks as `StateReady` (which would avoid a scheduler round-trip).

The `memStore` is not goroutine-safe, which conflicts with the interface doc: "Implementations must be safe for concurrent use." The implementation's own comment acknowledges this ("not safe for concurrent use without external locking") but that creates an explicit contradiction with the interface contract it claims to satisfy.

### Pipeline Y: 2/5

Y uses a completely different architecture than the one it was given. This is the most telling signal of all three pipelines.

The architecture Y received specifies `TaskStatus`, `Priority` as a wrapped int, a 13-method `Store` with `ClaimTask` CAS, SQLite with WAL, and `Scheduler.DAGFor` for cycle detection. Let me enumerate the divergences:

1. **Name field: the architecture has no Name field on Task. The implementation accepts `<name>`, then discards it with `_ = name` and an incorrect comment.** The comment says "name is stored inside the task via Command" -- it is not. This is a factual error in the code.

2. **Cycle detection placement: the architecture puts it in `Scheduler.DAGFor`. The implementation puts it in a separate `dag` package called from the `cmd` layer.** The scheduler is never involved.

3. **Error handling pattern: the architecture doesn't specify error handling style, but Y uses `fmt.Fprintf(os.Stderr) + os.Exit(1)` throughout RunE instead of returning errors.** This is a fundamental design choice that prevents `defer store.Close()` from running -- a durability problem with a WAL-mode SQLite store.

4. **`parseCommand` is an unarchitected invention.** The architecture specifies `Command []string` and uses `exec.CommandContext(ctx, t.Command[0], t.Command[1:]...)`. The implementation adds a custom shell tokenizer that the review later identifies as buggy.

The SQLite store itself is faithful to the architecture -- WAL mode, `SetMaxOpenConns(1)`, `ClaimTask` CAS via UPDATE WHERE. But the CLI layer deviates substantially.

### Pipeline Z: 5/5

Z follows its own architecture with precise fidelity. Evidence:

- Architecture: `State` type with six constants. Implementation: all six defined with matching strings and comments matching the architecture's inline documentation.
- Architecture: `Store` interface with 7 methods, `Transition(id, from, to State)` as CAS. Implementation: identical signatures, `ErrWrongState` returned on mismatch, all under mutex.
- Architecture: cycle detection inside `Store.Add` via DFS before persisting. Implementation: `detectCycle` called inside `FileStore.Add` under the same lock.
- Architecture: `Filter` struct with `State []State`, `Priority *int`, `Limit int`. Implementation: same struct (though `Priority` and `Limit` are not implemented in `List` -- a bug, but the types match perfectly).
- Architecture: sentinel errors `ErrNotFound`, `ErrWrongState`, `ErrCycle`, `ErrDuplicate`. Implementation: all four defined with `errors.New`, used via `errors.Is` throughout.
- Architecture: initial state (ready if no deps, pending if deps). Implementation: explicit `initialState` logic in `runAdd`.
- Architecture: `Command []string`. Implementation: wraps shell command as `["sh", "-c", cmd]`, the standard pattern for `exec.CommandContext`.

The design notes explicitly document why each decision maps to the architecture. This is not after-the-fact justification -- the code structure itself mirrors the architecture doc's sections.

### Criterion winner: Pipeline Z

---

## 2. INTERFACE QUALITY

Store interface design -- clean or over/under-engineered? CAS transitions or blind overwrites?

### Pipeline X: 4/5

7 methods. Clean separation: `Add`, `Get`, `List`, `Transition`, `Update`, `Delete`, `Close`. CAS via `Transition(id, from, to)` -- exactly right. Sentinel errors for all failure modes. The `memStore` implements all seven correctly.

Deductions: `memStore` lacks a mutex, contradicting the interface doc. The `Update` function takes `fn func(*Task)` but passes a copy, creating a semantic gap between the interface contract ("applies fn to the task in place") and the implementation behavior. Both issues were caught by the review.

### Pipeline Y: 2/5

13 methods. This is over-engineered for `tq add` and indicative of a leaky abstraction. The `add` command uses 3 methods (`Get`, `List`, `Add`). The remaining 10 (`UpdateStatus`, `SetStarted`, `SetFinished`, `IncrementRetries`, `UpdateWorkerPID`, `ReadyTasks`, `RunningTasks`, `ClaimTask`, `ReclaimOrphan`, `Close`) are worker-process concerns that the CLI layer should not know about.

The `ClaimTask` CAS method is well-designed -- single-statement UPDATE with WHERE guard, returning rows-affected. This is correct for concurrent claim scenarios. But `UpdateStatus` is a blind overwrite with no state guard -- two callers can transition a task through incompatible states without error. The interface has both a CAS method and blind-overwrite methods for the same concern (state transitions), which is an invitation to bypass the CAS.

`depends_on` is stored as a comma-separated string with no referential integrity despite `_foreign_keys=on` being set. The FK pragma is a false comfort.

### Pipeline Z: 5/5

7 methods, identical to X, but with better implementation. CAS `Transition` is the only path for state changes. `Update` with `fn func(*Task)` operates on the actual slice element (`fn(&tasks[i])`), not a copy -- the in-place contract is honored. Mutex on every operation. Sentinel errors wrapped with `%w` for context propagation.

The `List` function uses a set-based state filter (`map[State]struct{}`) for O(1) lookups instead of linear scans per task -- a minor detail that shows engineering discipline at the implementation level.

The Store interface comment says "Implementations must be safe for concurrent use" and the `FileStore` delivers on this with `sync.Mutex` on every method.

### Criterion winner: Pipeline Z

---

## 3. CLI DISCIPLINE

Error messages specific or vague? Output pipe-friendly? Exit codes correct? Composable?

### Pipeline X: 3/5

Error messages use a format like `"dependency %q not found"` -- specific enough but inconsistent. There is no project-level error prefix convention. Output goes to `cobraCmd.OutOrStdout()` -- excellent for testing. Exit codes follow Cobra's convention correctly. `MarkFlagRequired` handles the `--cmd` requirement, but there is also a manual `if cmd == ""` check that is dead code (the review caught this).

Name stored in `Metadata["name"]` means the implementation handles the positional arg without losing data, but the approach is unidiomatic -- consumers must know to look in `Metadata` for a core concept.

All tasks start as `StatePending` even with no deps. This forces a scheduler round-trip before a simple `tq add "build" --cmd "make"` can be picked up by workers. For a CLI tool, this is friction.

### Pipeline Y: 1/5

The single worst CLI decision across all three pipelines: every error path uses `fmt.Fprintf(os.Stderr, "error: ...") + os.Exit(1)` instead of returning from `RunE`.

Consequences:
1. **`defer store.Close()` never runs on error.** WAL-mode SQLite requires clean close to checkpoint. Skipping it means the WAL file accumulates without checkpointing, requiring recovery on next open. Under repeated error conditions (e.g., a script with bad dep IDs), this is real data corruption risk.
2. **Untestable.** Any test calling `runAdd` exits the test process on error.
3. **Cobra's error handling is completely bypassed** -- no SilenceErrors, no formatted usage hints, no error unwrapping.

Error messages are generic: `"error: could not add task: %v"`. The user gets the raw store error with no context about which task or which step failed.

The `name` argument is silently discarded. A user running `tq add "my important task" --cmd "make"` sees the ID printed and assumes the name was stored. It was not.

Output: the ID goes to stdout via `fmt.Printf`, which is correct. But the `_ = name` line means the only user-visible output is a hex ID with no label.

### Pipeline Z: 5/5

Every error follows a consistent convention: `tq: cannot add task "<name>": <reason>`. Examples from the code:

```
tq: cannot add task "deploy": unknown dependency ID(s): a1b2c3d4
tq: cannot add task "deploy": dependency chain creates a cycle
tq: cannot add task "deploy": ID a1b2c3d4 already exists
```

This is specific enough to act on without `--verbose`. The prefix `tq:` identifies the tool in piped output. The task name is quoted. The reason is targeted.

Output goes to stdout (ID only). Errors go to stderr via Cobra. Exit codes follow Cobra's convention. No manual `os.Exit` calls in command logic.

Initial state is `StateReady` for no-dep tasks and `StatePending` for tasks with deps. This means `tq add "build" --cmd "make"` creates a task that can be claimed immediately -- no scheduler round-trip needed. This is the right UX for a CLI tool.

`validateDependenciesExist` accumulates ALL missing IDs and reports them in one error. The user fixes everything in one pass:
```
tq: cannot add task "deploy": unknown dependency ID(s): a1b2, c3d4
```

### Criterion winner: Pipeline Z

---

## 4. DURABILITY

Atomic writes? Crash safety? State transitions safe under concurrent access?

### Pipeline X: 2/5

`memStore` is the concrete implementation. No persistence. No atomic writes. No crash safety. No mutex. If the process exits, all data is lost.

The Store interface is designed for durability (CAS transitions, Close), but the implementation is ephemeral. The review catches the missing mutex and notes it is "sufficient for a single-process CLI" -- but the interface contract says "Implementations must be safe for concurrent use."

For a CLI tool that is supposed to survive restarts and support concurrent workers, an in-memory store is fundamentally inadequate.

### Pipeline Y: 3/5

SQLite with WAL mode and `SetMaxOpenConns(1)` is the correct production setup. `ClaimTask` uses a single-statement CAS UPDATE -- atomic by SQLite's guarantee. The schema is reasonable.

Two critical problems undermine the durability story:

1. **`os.Exit(1)` prevents `defer store.Close()`.** WAL-mode SQLite accumulates writes in the WAL file. `db.Close()` triggers a checkpoint that flushes WAL to the main database. Skipping this means the WAL can grow without bound under error conditions. This was caught by both the original review and by inspection.

2. **No transactions around the validate-check-write sequence.** `validateDependencies`, `validateNoCycle`, and `store.Add` are three separate SQLite operations. A concurrent process modifying the task graph between these calls can introduce dangling references or cycles.

### Pipeline Z: 4/5

`FileStore` uses atomic writes via temp-file + `os.Rename`. On POSIX systems, `rename(2)` is atomic -- a crash mid-write leaves either the old file intact or the new file complete. This is the correct pattern for a JSON file store.

`sync.Mutex` protects every method. Concurrent CLI invocations on the same store file are serialized.

The TOCTOU gap between `validateDependenciesExist` (in cmd layer) and `Store.Add` (in store layer) is a durability concern -- but the review catches this and proposes moving dep validation inside `Store.Add` under the same lock. The cycle detection is already inside `Store.Add`, so half the problem is already solved.

The `write(nil)` producing JSON `null` is a fragility the review identifies but it does not cause data loss -- `load` handles it correctly.

Deduction: a JSON file store will not scale to thousands of concurrent operations the way SQLite would. For a local CLI this is fine, but the architecture specified BoltDB as the backend, and the implementation chose JSON files. The atomic-write pattern is correct but the storage medium is a simplification.

### Criterion winner: Pipeline Z

---

## 5. REVIEW QUALITY

Did the review catch real bugs? Miss anything? False positives? Actionable?

### Pipeline X: 4/5

9 issues found. Quality breakdown:

**Real bugs caught:**
- Cycle detection DFS `visited` short-circuit with map iteration (HIGH). The review's analysis is lengthy and self-correcting but ultimately arrives at a nuanced concern about non-deterministic behavior under pre-existing cycles. The concern is theoretically valid but practically moot -- the store prevents cycles at add time, so a pre-existing cycle should never exist. The review loses marks for not reaching this conclusion cleanly.
- `parseCommand` blank fallback (MEDIUM). Correctly identified.
- TOCTOU between dep validation and insertion (MEDIUM). Correctly identified.
- `memStore` has no mutex (MEDIUM). Correctly identified and correctly scoped.
- `Update` fn sees stale copy (MEDIUM). Correctly identified as a semantic gap.

**False positives:** The redundant `--cmd` check (LOW) is real dead code but not a bug. Fair flag.

**Misses:** The review does not flag that all tasks start as `StatePending` even with no deps -- a usability issue that Pipeline Z handles correctly.

The review lists 5 specific positives with evidence. This is a sign of calibrated judgment -- a reviewer who only finds negatives cannot be trusted.

### Pipeline Y: 4/5

12 issues found. Quality breakdown:

**Real bugs caught:**
- Name silently discarded (BUG). Correctly identified with specific evidence (the wrong comment on `_ = name`).
- `os.Exit(1)` in RunE prevents defer (BUG). Correctly identified with specific WAL consequences.
- `parseCommand` drops backslash escapes (BUG). Correctly identified.
- TOCTOU race (BUG). Correctly identified.
- ID collision unhandled (BUG). Correctly identified with birthday paradox math.
- `depends_on` as comma-separated string (DESIGN). Correctly identified as missing referential integrity.

**Design issues correctly identified:**
- Store interface too broad (13 methods, add uses 3). Correct.
- Full table scan including terminal tasks in cycle check. Correct.
- OFFSET without LIMIT footgun. Correct and subtle -- shows deep SQL knowledge.

**Misses:** The review does not flag the `Execute()` function in root.go ignoring errors (it catches it in "Minor" but underweights it). It also does not flag that `parseCommand` silently accepts unclosed quotes -- wait, it does flag this under item 12. Good.

**False positive concern:** Item 3 (cycle check doesn't validate dep IDs are keys in adj) -- the review's analysis of this bug is muddled. It flags that dep IDs might not be keys in `adj`, but then acknowledges that `store.List` returns all tasks so they will be. This is a fragility flag, not a bug. Fair enough.

### Pipeline Z: 5/5

8 issues found, but they are the *right* 8 issues. Quality breakdown:

**Real bugs caught:**
- TOCTOU race in validate-then-add (HIGH). Correctly identified with specific fix: move dep validation inside `Store.Add`.

**Spec violations caught (unique to this review):**
- List not sorted by priority desc (MEDIUM). The interface comment says "ordered by priority desc, created_at asc" -- the implementation ignores this. No other review caught this.
- Filter.Priority ignored (MEDIUM). The field exists in the struct but `List` never reads it.
- Filter.Limit ignored (MEDIUM). Same pattern. The review even notes that Limit must be applied after sorting.

These three spec violations demonstrate that the reviewer actually read the interface contract and compared it to the implementation. This is the difference between reviewing code and reviewing against a specification.

**Self-correction:** The review initially flagged cycle detection as a bug, then walked through a concrete scenario, realized the logic is correct, and explicitly withdrew the concern: "no bug here." This is intellectual honesty that adds credibility to every other finding.

**Positives section:** 9 specific positives with evidence. Not generic praise -- each positive cites a specific implementation detail (atomic write pattern, `errors.Is` usage, `PersistentPreRunE` separation, `crypto/rand` not `math/rand`).

**Misses:** The `write(nil)` producing JSON `null` is flagged as LOW -- correct prioritization. The `MaxRetries=0` making `StateFailed` unreachable is a subtle design observation no other review made.

### Criterion winner: Pipeline Z

---

## 6. PIPELINE CONSISTENCY

Do architecture, implementation, and review form a coherent chain, or feel disconnected?

### Pipeline X: 3/5

The architecture is Z's architecture. The implementation follows it closely. The review evaluates the implementation competently. The chain is coherent but with an asterisk: the implementation and review feel like they come from a different team than the architecture. The architecture specifies `FileStore` or `boltStore` for durability; the implementation delivers `memStore`. The architecture emphasizes crash recovery and CAS transitions under concurrent workers; the implementation has no persistence and no concurrency safety.

This is the expected outcome of receiving a detailed architecture document and implementing against it without the context that motivated the architectural decisions. The "what" is followed. The "why" is occasionally lost.

### Pipeline Y: 2/5

The architecture is detailed and well-structured. The implementation diverges from it on several fronts. The review catches many of the divergences, but also catches issues that exist *because* the implementation diverged (name discarded, os.Exit preventing defer, cycle detection in wrong layer).

The most telling disconnect: the architecture specifies `ClaimTask` as the CAS mechanism. The implementation builds `ClaimTask` in the store layer. But `runAdd` uses `os.Exit(1)` throughout, which is architecturally incompatible with the WAL-mode SQLite store that `ClaimTask` protects. The architecture team designed for durability; the implementation team undermined it.

The review catches this, which partially redeems the chain. But the pipeline as a whole produces code that needs the most rework before shipping.

### Pipeline Z: 5/5

Architecture, implementation, and review are a single coherent narrative.

The architecture says "cycle detection at enqueue time, inside Store.Add." The implementation puts it there. The review validates it is there and confirms correctness by walking through the DFS algorithm.

The architecture says "CAS transitions." The implementation has `Transition(id, from, to)`. The review confirms the CAS contract is honored and identifies the TOCTOU gap where dep validation is not yet under the same lock.

The architecture says "pipe-friendly output." The implementation prints only the ID to stdout. The review confirms this and notes the missing `--json` flag as a spec gap.

The review even references the architecture's sorting requirement ("ordered by priority desc, created_at asc") and catches that the implementation doesn't implement it. This proves the reviewer had the architecture in mind while reviewing.

The chain reads like one engineer wrote the architecture, implemented it, then had a competent colleague review it -- which is the ideal pipeline.

### Criterion winner: Pipeline Z

---

## Scorecard

| Criterion | X | Y | Z | Winner |
|---|---|---|---|---|
| Architectural Coherence | 4 | 2 | 5 | Z |
| Interface Quality | 4 | 2 | 5 | Z |
| CLI Discipline | 3 | 1 | 5 | Z |
| Durability | 2 | 3 | 4 | Z |
| Review Quality | 4 | 4 | 5 | Z |
| Pipeline Consistency | 3 | 2 | 5 | Z |
| **Total** | **20** | **14** | **29** | **Z** |

---

## Verdict

### Overall Ranking

1. **Pipeline Z** (29/30) -- Clean sweep across all six criteria. The implementation follows the architecture precisely, the CLI output is disciplined and consistent, the store has real durability, and the review catches the right bugs while honestly withdrawing a false positive. This is the most shippable code with the fewest real issues.

2. **Pipeline X** (20/30) -- Competent implementation of a good architecture, held back by the `memStore` (no persistence, no mutex) and the all-tasks-start-pending UX issue. The review is thorough and calibrated. The gap to Z is primarily in durability and CLI polish -- the architecture-to-implementation translation is faithful but the implementation does not carry the architectural *intent* around crash safety and concurrency.

3. **Pipeline Y** (14/30) -- The most technically ambitious (SQLite, WAL, CAS, shell tokenizer, separate dag package) but the most problematic. The `os.Exit(1)` pattern is a fundamental mistake for a Cobra command -- it undermines durability (WAL), testability, and composability. The discarded `name` argument is user-visible data loss. The 13-method Store interface is over-engineered. The architecture-implementation gap is the widest of all three.

### Clustering: Does X cluster with Y (bare) or Z (full context)?

**X clusters with Z, not Y.** The evidence:

- X follows Z's architecture faithfully. Y diverges from its own architecture on multiple fronts.
- X uses sentinel errors with `errors.Is` throughout. Z does too. Y uses string-formatted errors with `os.Exit`.
- X's Store interface is 7 methods with CAS Transition. Z's is identical. Y's is 13 methods with both CAS and blind-overwrite methods.
- X's review finds 9 issues at correct severity levels. Z's review finds 8 with self-correction. Y's review finds 12 but against code with more bugs.
- X returns errors from RunE. Z returns errors from RunE. Y calls `os.Exit(1)`.

The primary delta between X and Z is implementation quality at the edges -- Z's error messages have a consistent `tq:` prefix, Z starts no-dep tasks as `StateReady`, Z uses atomic writes, Z's `Update` operates on the actual element rather than a copy. These are polish and discipline differences, not structural ones.

**The architecture document carried most of the signal.** X received Z's architecture and produced output that clusters with Z across interface design, error handling, code organization, and even DFS implementation style. The gap between X and Z (9 points) is smaller than the gap between Y and X (6 points) in relative terms -- but more importantly, X's failures are all in *execution* (no persistence, no mutex, no initial-state optimization) while Y's failures are in *design decisions* (wrong error pattern, wrong interface breadth, discarded user data).

### The single most important finding

**Architecture is the highest-leverage intervention point in the pipeline.** Pipeline X received only the architecture document -- no personas, no quality standards, no design patterns -- and produced output that is closer to the full-context Pipeline Z than to the bare Pipeline Y. The architecture document established the types, interfaces, error patterns, and placement of concerns that the implementation then followed. Quality standards and personas added measurable polish to Z (error message conventions, initial state optimization, the `tq:` prefix, the `["sh", "-c", cmd]` pattern) but the architecture document provided the structural foundation that separated both X and Z from Y.

Y's architecture was equally detailed but the implementation diverged from it -- suggesting that without the project context (quality standards, conventions) to reinforce the architecture's intent, the implementer felt free to make independent design choices. Some of those choices (SQLite, shell tokenizer) were technically reasonable. Others (os.Exit, discarding name, 13-method interface) were harmful. The context that X lacked and Z had was not "what to build" (both had the architecture for that) but "how to hold yourself accountable to the architecture" -- conventions like error message formats, exit code discipline, and the principle that `RunE` should return errors, not exit.

The practical implication: if you can only invest in one part of the pipeline, invest in the architecture. If you can invest in two, add conventions that reinforce the architecture's intent at the implementation level. The architecture gets you from 14 to 20. The conventions get you from 20 to 29.
