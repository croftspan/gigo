# Pipeline Evaluation: A vs B

**Judge:** Principal Go Engineer
**Date:** 2026-03-27
**Task:** tq -- Go CLI task queue with priorities, dependencies, concurrent workers

---

## 1. ARCHITECTURAL COHERENCE

### Pipeline A: 5/5

The implementation follows its architecture with remarkable fidelity. The architecture specifies a `State` type with six constants (`pending`, `ready`, `running`, `done`, `failed`, `dead`) -- the implementation defines all six. The architecture specifies `Store.Transition(id, from, to State)` as a CAS method -- the implementation provides exactly that signature with `ErrWrongState` returned on mismatch. The architecture places cycle detection inside `Store.Add` -- the implementation does this via a `detectCycle` helper called before persisting, under the same mutex.

Specific evidence of architecture-to-implementation traceability:
- Architecture: `Command []string` with `json:"command"` tag. Implementation: identical.
- Architecture: sentinel errors `ErrNotFound`, `ErrWrongState`, `ErrCycle`, `ErrDuplicate`. Implementation: all four defined with `errors.New`, used via `errors.Is` throughout.
- Architecture: initial state assignment (ready if no deps, pending if deps). Implementation: explicit `initialState` logic in `runAdd` with a comment referencing the state machine.
- Architecture: `Filter` struct with `State`, `Priority`, `Limit`. Implementation: identical struct (though `Priority` and `Limit` are not applied in `List` -- a bug, but the types match).

The design notes in the implementation explicitly call out alignment decisions: "The Task struct and Store interface match the architecture spec exactly." This is not just boilerplate -- the implementation backs it up.

### Pipeline B: 3/5

The architecture specifies a `TaskStatus` type, `Priority` as a wrapped int type, and a `Store` interface with 13 methods. The implementation faithfully reproduces all of these. SQLite with WAL mode, `ClaimTask` as CAS, the `poolImpl` with a `running` map -- all present.

However, there are significant divergences:

1. **The architecture has no `Name` field on Task. The implementation accepts `<name>` as a positional argument, then discards it with `_ = name` and a wrong comment.** This is the implementation trying to satisfy the CLI spec ("task name is a positional argument") while following an architecture that forgot to include it. The architecture and implementation are misaligned on a user-visible feature.

2. **The architecture places cycle detection in the Scheduler's `DAGFor` method.** The implementation puts it in a separate `dag` package called from the `cmd` layer. This is functionally similar but architecturally different -- the scheduler is not involved.

3. **The architecture specifies `Scheduler.Notify(taskID)` as the notification mechanism.** The implementation's `validateNoCycle` builds a fresh `DAG` from `store.List` on every call. This doesn't use the architectural `Scheduler` or `DAG` types at all -- it reconstructs the graph ad hoc.

4. **The `parseCommand` function is an invention of the implementation with no architectural basis.** The architecture specifies `Command []string` and lets the caller decide how to populate it. The implementation introduces a custom shell tokenizer that the review later identifies as buggy.

### Criterion winner: Pipeline A

---

## 2. INTERFACE QUALITY

### Pipeline A: 5/5

The `Store` interface is 7 methods, each with a clear responsibility:

```go
Add(task Task) error
Get(id string) (Task, error)
List(filter Filter) ([]Task, error)
Transition(id string, from, to State) error
Update(id string, fn func(*Task)) error
Delete(id string) error
Close() error
```

Key design decisions:
- `Transition` is the CAS primitive. It takes `from` and `to` states and returns `ErrWrongState` if the precondition fails. This is the correct abstraction for concurrent task claiming -- the scheduler calls `Transition(id, StateReady, StateRunning)`, and only one caller can win.
- `Update` takes a mutation function `func(*Task)` rather than accepting a full `Task` struct. This prevents callers from accidentally overwriting state fields -- they can only modify the fields they touch.
- `Get` returns `(Task, error)` with `ErrNotFound` as a sentinel. Clean `errors.Is` checking throughout.
- Value semantics for `Task` (not pointers). Tasks are passed by value, eliminating shared-pointer mutation issues.

The `Filter` struct is reasonably designed (`State []State`, `Priority *int`, `Limit int`) even though the implementation doesn't apply all fields. The interface is right even if the implementation has gaps.

### Pipeline B: 2/5

The `Store` interface has 13 methods:

```go
Add, UpdateStatus, UpdateWorkerPID, SetStarted, SetFinished, IncrementRetries,
Get, List, ReadyTasks, RunningTasks, ClaimTask, ReclaimOrphan, Close
```

This is over-engineered. The `add` command uses 3 methods; mocking requires stubbing 13. `UpdateStatus` is a blind overwrite (`UPDATE tasks SET status = ? WHERE id = ?`) -- it has no CAS semantics. Only `ClaimTask` has CAS (via the `AND status = 'ready'` WHERE clause). This means the interface has two ways to change status: one safe (`ClaimTask`) and one unsafe (`UpdateStatus`). Which one should a caller use? The interface doesn't make the safe path obvious.

`ReadyTasks` and `RunningTasks` are convenience methods that could be expressed as `List` with a filter. They add surface area without adding capability.

The `Priority` type wrapping `int` with named constants (`PriorityLow = 0`, `PriorityNormal = 5`, `PriorityHigh = 10`, `PriorityCrit = 20`) is reasonable but the gaps between values (0, 5, 10, 20) are arbitrary and undocumented.

The `Task` struct uses pointer semantics (`*Task`) throughout, which introduces shared-mutation risks that Pipeline B's own review later identifies.

### Criterion winner: Pipeline A

---

## 3. CLI DISCIPLINE

### Pipeline A: 4/5

Strong points:
- Only the task ID goes to stdout: `fmt.Println(task.ID)`. The design notes explicitly show the pipe composition pattern: `DEP=$(tq add "build" --cmd "..."); tq add "test" --depends-on "$DEP"`.
- Error messages follow a consistent convention: `tq: cannot add task "<name>": <reason>`. Specific, actionable.
- Errors go to stderr via Cobra's default handling. No manual `os.Exit` in command logic.
- Exit codes are correct: Cobra returns 1 on `RunE` error, 0 on success.
- `--cmd` is marked required via `MarkFlagRequired`.

Deductions:
- No `--json` flag (the review catches this as a spec gap).
- The `Name` field is stored but never used in output -- however, the architecture includes it in the `Task` struct, so this is consistent.

### Pipeline B: 2/5

Serious problems:
- **`os.Exit(1)` on every error path bypasses Cobra entirely.** The function signature is `RunE` (returns error), but every error branch does `fmt.Fprintf(os.Stderr, ...) + os.Exit(1)`. This prevents `defer store.Close()` from running -- the review correctly identifies that SQLite WAL may not checkpoint. It also makes the function untestable.
- **The `name` argument is accepted and discarded.** `_ = name` with the comment "name is stored inside the task via Command for display" -- but this is false. The name is not stored. Users running `tq add "build-binary" --cmd "go build"` will lose the label entirely.
- **Error messages are generic:** `"error: could not add task: %v"` instead of including the task name or a `tq:` prefix.
- **`parseCommand` silently produces wrong argv** for commands with backslash escapes. `--cmd 'echo "hello world"'` works, but `--cmd "echo \"hello\""` does not. No error is reported.

The pipe-friendly output (`fmt.Printf("%s\n", id)`) is correct. The `--cmd` flag is correctly marked required. But the `os.Exit` pattern and the discarded name are both issues that affect real users.

### Criterion winner: Pipeline A

---

## 4. DURABILITY

### Pipeline A: 4/5

- **Atomic writes:** `FileStore.write` uses temp-file + `os.Rename`. On POSIX, `rename(2)` is atomic. A crash mid-write leaves the old file intact. This is correctly implemented.
- **CAS transitions:** `Transition` loads all tasks, checks `t.State != from`, and returns `ErrWrongState` if the precondition fails. Under the mutex this is correct for a single-process model.
- **Cycle detection under lock:** `detectCycle` runs inside `Store.Add` under `fs.mu.Lock()`. No TOCTOU window between cycle check and write -- but the review correctly identifies that `validateDependenciesExist` runs *outside* the lock in the command layer, creating a TOCTOU window for dependency existence.
- **Crash recovery:** The architecture specifies `RecoverOnStartup` with artifact-based fate assessment. The implementation details are in the architecture doc, not in the `tq add` implementation (which is appropriate -- crash recovery is a startup concern).

Deduction: The TOCTOU race between `validateDependenciesExist` (outside lock) and `Store.Add` (inside lock) is a real bug for concurrent CLI invocations. The review catches it.

### Pipeline B: 3/5

- **SQLite WAL mode:** Correctly configured with `_journal_mode=WAL&_synchronous=NORMAL`. Single writer via `db.SetMaxOpenConns(1)`.
- **CAS via SQL:** `ClaimTask` uses `UPDATE ... WHERE id = ? AND status = 'ready'` with rows-affected check. Correct.
- **No transaction around validate-add:** `validateDependencies`, `validateNoCycle`, and `store.Add` are three separate operations with no wrapping transaction. The review catches this.
- **`os.Exit(1)` prevents `defer store.Close()`:** This is a durability issue. SQLite WAL mode relies on clean close to checkpoint the WAL. The review identifies this -- on error paths, the WAL file is left dirty.
- **`depends_on` as comma-separated string:** No referential integrity despite `_foreign_keys=on`. Deleting a task does not cascade or error on dependents.

The SQLite foundation is solid, but the application layer undermines it. The `os.Exit` bypassing `defer Close()` is particularly bad -- it means every error path is a potential WAL corruption vector.

### Criterion winner: Pipeline A

---

## 5. REVIEW QUALITY

### Pipeline A Review: 5/5

The review examines the implementation produced by its own pipeline and finds:

1. **TOCTOU race (HIGH):** `validateDependenciesExist` reads outside the mutex, `Store.Add` writes inside it. A concurrent `tq delete` between the two creates a dangling dependency. This is a real bug with a concrete fix (move dep-existence check inside `Store.Add`). Actionable, correct.

2. **Cycle detection correctness (self-correcting):** The review initially questions whether DFS from only `newTask.ID` catches all cases. It then walks through the specific scenario `{A: [B], B: [A]}`, confirms the cycle is detected, and explicitly withdraws the concern: "The cycle detection logic is correct given the invariant. Withdraw the concern. No bug here." This self-correction is impressive -- many reviews would either skip the analysis or leave a false positive.

3. **Three spec violations (MEDIUM):** List not sorted by priority desc, `Filter.Priority` ignored, `Filter.Limit` ignored. All three are real gaps in the implementation with concrete fixes including code.

4. **Design clarifications (LOW):** `MaxRetries=0` makes `StateFailed` unreachable, `write(nil)` produces JSON `null`. Both are real observations with proportionate severity ratings.

5. **What Works Well section:** Lists 9 specific things with evidence (atomic writes, sentinel errors, output discipline, `crypto/rand` for IDs, no CGO, etc.). This is not generic praise -- each item cites a concrete implementation detail.

No false positives survived (the cycle detection concern was raised and correctly withdrawn). The priority ordering of fixes is sensible.

### Pipeline B Review: 4/5

The review finds 6 bugs, 4 design issues, and 2 missing pieces:

1. **Name silently discarded (data loss):** Correctly identified. The comment `// name is stored inside the task via Command for display` is wrong, and the reviewer calls it out specifically.

2. **`parseCommand` drops backslash escapes:** Real bug with concrete examples (`echo \"hello\"` produces wrong output). Correct severity.

3. **Cycle check doesn't validate dependency IDs in `adj`:** This is a valid fragility concern but rated slightly high -- in practice `store.List` returns all tasks. The reviewer acknowledges this.

4. **TOCTOU race:** Same class of bug as Pipeline A's review found. Correctly identified with a fix (SQLite transaction).

5. **`os.Exit(1)` in `RunE` prevents `defer store.Close()`:** Excellent catch. The reviewer connects it to WAL checkpoint behavior and testability. Actionable.

6. **32-bit ID collision (birthday problem at ~65k tasks):** Valid concern, proportionately rated. Not critical for a local queue but worth noting.

7. **Store interface too broad (13 methods):** Correct design observation with a concrete fix (narrower `taskAdder` interface).

Deductions: The review is thorough but does not include a "What Works Well" section. It identifies bugs but doesn't calibrate which are likely to hit users first. The OFFSET-without-LIMIT observation (issue 9) is technically correct but unlikely to cause problems in practice -- slight over-counting of issues.

### Criterion winner: Pipeline A (marginally)

---

## 6. PIPELINE CONSISTENCY

### Pipeline A: 5/5

The three stages form a coherent narrative:

1. **Architecture** defines `State` with 6 constants, `Store.Transition` as CAS, `detectCycle` inside `Store.Add`, sentinel errors, semaphore-based worker pool with supervisor pattern.

2. **Implementation** reproduces every architectural decision. The `Store` interface is identical. The `Task` struct matches. Cycle detection is inside `Store.Add`. Sentinel errors are used with `errors.Is`. The implementation explicitly references the architecture in its design notes: "Command `[]string` (not a single `Cmd string`) -- the architecture uses a string slice." The initial state assignment (ready vs pending based on deps) mirrors the architecture's state machine.

3. **Review** evaluates the implementation against both the architecture and the spec. It finds that `List` doesn't sort (violating the interface comment from the architecture), that `Filter.Priority` and `Filter.Limit` are ignored (features defined in the architecture but not implemented), and that the TOCTOU race is a gap between the architecture's "all checks under one lock" principle and the implementation's split validation.

The pipeline reads as one continuous thought process where each stage builds on the previous one. The architecture makes decisions, the implementation honors them, and the review verifies the honor.

### Pipeline B: 3/5

The stages are competent individually but loosely coupled:

1. **Architecture** defines a rich system with 13-method Store, SQLite, Priority type, Scheduler with DAGFor, WorkerPool with Resize.

2. **Implementation** uses SQLite and WAL mode (matching architecture), defines the 13-method Store (matching), but introduces `parseCommand` (not in architecture), discards the `name` argument (architecture has no Name field but the CLI spec requires it), and puts cycle detection in a `dag` package (architecture puts it in the Scheduler). The architecture's `Scheduler.DAGFor` is not used -- `validateNoCycle` builds a DAG ad hoc from `store.List`.

3. **Review** finds bugs in the implementation but doesn't evaluate whether the implementation follows the architecture. It never references the architecture doc. The `name` bug, the `parseCommand` bug, and the TOCTOU race are all caught, but they're analyzed as standalone code quality issues rather than as deviations from the architectural plan.

The pipeline feels like three independent responses to three independent prompts. The architecture is rich, the implementation partially follows it while inventing new concepts, and the review evaluates the implementation as standalone code. There is no through-line.

### Criterion winner: Pipeline A

---

## Scoring Summary

| Criterion | Pipeline A | Pipeline B | Winner |
|---|---|---|---|
| Architectural Coherence | 5 | 3 | A |
| Interface Quality | 5 | 2 | A |
| CLI Discipline | 4 | 2 | A |
| Durability | 4 | 3 | A |
| Review Quality | 5 | 4 | A |
| Pipeline Consistency | 5 | 3 | A |
| **Total** | **28** | **17** | **A** |

---

## Overall Winner: Pipeline A

Pipeline A wins every criterion. The margin ranges from narrow (review quality, 5 vs 4) to decisive (interface quality, 5 vs 2).

Pipeline A produces code I would approve for merge after fixing the TOCTOU race and the three `List` spec violations -- both identified by its own review. The implementation is lean, the types are right, the abstractions are clean, and the review is honest about what's missing. This is a pipeline that produces shippable code with known, bounded issues.

Pipeline B produces code I would send back for a second round. The `os.Exit(1)` pattern bypasses Cobra and breaks `defer`. The `name` argument is silently discarded. The `parseCommand` tokenizer is silently wrong on escape sequences. The Store interface is 13 methods wide for a command that uses 3. The review catches most of these, which means the pipeline is self-aware of its problems -- but the problems exist because the implementation stage introduced unnecessary complexity (custom tokenizer, broad interface, ad hoc DAG construction) that the architecture didn't call for.

---

## The Single Most Important Difference

**Pipeline A's implementation serves its architecture. Pipeline B's implementation invents beyond its architecture.**

Pipeline A's implementation reads its architecture and reproduces it faithfully -- same types, same interfaces, same error handling patterns, same placement of cycle detection. When the review finds gaps, they are gaps between "what the architecture specified" and "what the implementation delivered" (e.g., `List` not sorting). The gaps are bounded and fixable.

Pipeline B's implementation reads its architecture and then makes additional decisions: a custom shell tokenizer, a separate `dag` package not called for by the architecture, `os.Exit` instead of error returns, discarding the name argument. Each of these inventions introduced a bug. The architecture gave the implementation a plan, and the implementation diverged from it. The divergences are where the bugs live.

This is the fundamental value of pipeline consistency: when the implementation follows the architecture, bugs cluster in "didn't implement feature X" (omission). When the implementation invents beyond the architecture, bugs cluster in "invented feature Y incorrectly" (commission). Omission bugs are cheaper to fix than commission bugs because they have smaller blast radii and more obvious fixes.
