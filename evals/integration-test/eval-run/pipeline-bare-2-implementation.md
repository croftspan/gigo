# tq add — Implementation

## File: `cmd/add.go`

```go
package cmd

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// addCmd is the cobra command for `tq add`.
var addCmd = &cobra.Command{
	Use:   "add <name>",
	Short: "Add a task to the queue",
	Long: `Add a task to the queue.

Examples:
  tq add build --cmd "go build ./..."
  tq add deploy --cmd "kubectl apply -f k8s/" --priority 10 --depends-on build1a2b3c4d`,
	Args: cobra.ExactArgs(1),
	RunE: runAdd,
}

var (
	addPriority  int
	addDependsOn string
	addCmd_      string
)

func init() {
	rootCmd.AddCommand(addCmd)

	addCmd.Flags().IntVar(&addPriority, "priority", 0, "Scheduling priority (higher runs first)")
	addCmd.Flags().StringVar(&addDependsOn, "depends-on", "", "Comma-separated list of task IDs that must complete first")
	addCmd.Flags().StringVar(&addCmd_, "cmd", "", "Shell command to execute (required)")
	_ = addCmd.MarkFlagRequired("cmd")
}

func runAdd(cmd *cobra.Command, args []string) error {
	name := args[0]

	// Parse shell command into argv.
	argv := parseCommand(addCmd_)
	if len(argv) == 0 {
		fmt.Fprintln(os.Stderr, "error: --cmd must not be empty")
		os.Exit(1)
	}

	// Parse dependency IDs.
	var dependsOn []string
	if addDependsOn != "" {
		for _, id := range strings.Split(addDependsOn, ",") {
			id = strings.TrimSpace(id)
			if id != "" {
				dependsOn = append(dependsOn, id)
			}
		}
	}

	// Open the store.
	store, err := openStore()
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: could not open store: %v\n", err)
		os.Exit(1)
	}
	defer store.Close()

	ctx := context.Background()

	// Validate that all dependency IDs exist.
	if err := validateDependencies(ctx, store, dependsOn); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}

	// Generate a short unique task ID.
	id, err := generateID()
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: could not generate task ID: %v\n", err)
		os.Exit(1)
	}

	// Determine initial status.
	// If the task has no dependencies it is immediately ready;
	// if it has dependencies the scheduler will promote it once they are done.
	status := StatusReady
	if len(dependsOn) > 0 {
		status = StatusPending
	}

	t := &Task{
		ID:        id,
		Command:   argv,
		Priority:  Priority(addPriority),
		DependsOn: dependsOn,
		Status:    status,
		CreatedAt: time.Now().UTC(),
	}

	// Cycle check: build the current DAG and verify the new task doesn't
	// introduce a cycle before writing anything to the store.
	if err := validateNoCycle(ctx, store, t); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}

	// Persist the task.
	if err := store.Add(ctx, t); err != nil {
		fmt.Fprintf(os.Stderr, "error: could not add task: %v\n", err)
		os.Exit(1)
	}

	// Report the new task ID. A trailing newline makes scripting easy.
	fmt.Printf("%s\n", id)
	_ = name // name is stored inside the task via Command for display; kept as label
	return nil
}

// validateDependencies checks that every ID in deps exists in the store.
func validateDependencies(ctx context.Context, store Store, deps []string) error {
	for _, id := range deps {
		if _, err := store.Get(ctx, id); err != nil {
			return fmt.Errorf("dependency %q not found: %w", id, err)
		}
	}
	return nil
}

// validateNoCycle builds the existing dependency graph from the store and
// runs CheckCycle against it with the new task included.
func validateNoCycle(ctx context.Context, store Store, t *Task) error {
	all, err := store.List(ctx, ListFilter{})
	if err != nil {
		return fmt.Errorf("could not read task list for cycle check: %w", err)
	}

	dag := &DAG{
		Nodes: make(map[string]*Task, len(all)+1),
		Edges: make(map[string][]string, len(all)+1),
	}
	for _, existing := range all {
		dag.Nodes[existing.ID] = existing
		dag.Edges[existing.ID] = existing.DependsOn
	}

	return dag.CheckCycle(t)
}

// generateID returns an 8-character cryptographically random hex string.
func generateID() (string, error) {
	b := make([]byte, 4) // 4 bytes → 8 hex chars
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

// parseCommand splits a shell-style command string into argv.
// It handles quoted strings so --cmd "go test ./..." works correctly.
func parseCommand(s string) []string {
	var args []string
	var current strings.Builder
	inQuote := false
	quoteChar := rune(0)

	for _, r := range s {
		switch {
		case inQuote && r == quoteChar:
			inQuote = false
		case !inQuote && (r == '"' || r == '\''):
			inQuote = true
			quoteChar = r
		case !inQuote && r == ' ':
			if current.Len() > 0 {
				args = append(args, current.String())
				current.Reset()
			}
		default:
			current.WriteRune(r)
		}
	}
	if current.Len() > 0 {
		args = append(args, current.String())
	}
	return args
}
```

---

## File: `cmd/root.go` (minimal bootstrap — not new, but required context)

```go
package cmd

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "tq",
	Short: "tq — a prioritised task queue with dependency resolution",
}

// Execute is the entry point called from main.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		// cobra already prints the error; just exit non-zero.
		// os.Exit is called inside cobra on RunE errors.
	}
}
```

---

## File: `cmd/store.go` (factory — wires the concrete SQLiteStore)

```go
package cmd

import (
	"fmt"
	"os"
	"path/filepath"
)

// openStore resolves the database path and returns a ready Store.
// Path precedence: TQ_DB env var → $HOME/.tq/tasks.db
func openStore() (Store, error) {
	path := os.Getenv("TQ_DB")
	if path == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return nil, fmt.Errorf("could not determine home directory: %w", err)
		}
		path = filepath.Join(home, ".tq", "tasks.db")
	}

	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return nil, fmt.Errorf("could not create data directory: %w", err)
	}

	return NewSQLiteStore(path)
}
```

---

## File: `store/sqlite.go` (Store implementation)

```go
package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

// SQLiteStore is the production-grade Store backed by SQLite with WAL mode.
type SQLiteStore struct {
	db *sql.DB
}

// NewSQLiteStore opens (or creates) the SQLite database at path and applies
// the schema migration. Returns a ready-to-use Store.
func NewSQLiteStore(path string) (*SQLiteStore, error) {
	db, err := sql.Open("sqlite3", path+"?_journal_mode=WAL&_synchronous=NORMAL&_foreign_keys=on")
	if err != nil {
		return nil, fmt.Errorf("open sqlite: %w", err)
	}
	// Single writer avoids lock contention; WAL allows concurrent readers.
	db.SetMaxOpenConns(1)

	s := &SQLiteStore{db: db}
	if err := s.migrate(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("migrate: %w", err)
	}
	return s, nil
}

const schema = `
CREATE TABLE IF NOT EXISTS tasks (
    id           TEXT PRIMARY KEY,
    command      TEXT NOT NULL,         -- JSON array
    priority     INTEGER NOT NULL DEFAULT 0,
    depends_on   TEXT NOT NULL DEFAULT '',  -- comma-separated IDs
    status       TEXT NOT NULL DEFAULT 'pending',
    created_at   DATETIME NOT NULL,
    started_at   DATETIME,
    finished_at  DATETIME,
    worker_pid   INTEGER NOT NULL DEFAULT 0,
    exit_code    INTEGER,
    retries      INTEGER NOT NULL DEFAULT 0,
    max_retries  INTEGER NOT NULL DEFAULT 0,
    env          TEXT NOT NULL DEFAULT '',  -- JSON object
    work_dir     TEXT NOT NULL DEFAULT '',
    output       TEXT NOT NULL DEFAULT ''
);
`

func (s *SQLiteStore) migrate() error {
	_, err := s.db.Exec(schema)
	return err
}

// --- Write methods ---

func (s *SQLiteStore) Add(ctx context.Context, t *Task) error {
	cmd, err := marshalStringSlice(t.Command)
	if err != nil {
		return err
	}
	env, err := marshalStringMap(t.Env)
	if err != nil {
		return err
	}
	deps := strings.Join(t.DependsOn, ",")

	_, err = s.db.ExecContext(ctx, `
		INSERT INTO tasks
			(id, command, priority, depends_on, status, created_at, worker_pid,
			 retries, max_retries, env, work_dir, output)
		VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)`,
		t.ID, cmd, int(t.Priority), deps, string(t.Status), t.CreatedAt,
		t.Retries, t.MaxRetries, env, t.WorkDir, t.Output,
	)
	return err
}

func (s *SQLiteStore) UpdateStatus(ctx context.Context, id string, status TaskStatus) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET status = ? WHERE id = ?`, string(status), id)
	return err
}

func (s *SQLiteStore) UpdateWorkerPID(ctx context.Context, id string, pid int) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET worker_pid = ? WHERE id = ?`, pid, id)
	return err
}

func (s *SQLiteStore) SetStarted(ctx context.Context, id string, pid int, at time.Time) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET status = 'running', worker_pid = ?, started_at = ? WHERE id = ?`,
		pid, at, id)
	return err
}

func (s *SQLiteStore) SetFinished(ctx context.Context, id string, status TaskStatus, exitCode int, at time.Time) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET status = ?, exit_code = ?, finished_at = ?, worker_pid = 0 WHERE id = ?`,
		string(status), exitCode, at, id)
	return err
}

func (s *SQLiteStore) IncrementRetries(ctx context.Context, id string) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET retries = retries + 1 WHERE id = ?`, id)
	return err
}

// --- Read methods ---

func (s *SQLiteStore) Get(ctx context.Context, id string) (*Task, error) {
	row := s.db.QueryRowContext(ctx, `SELECT `+taskColumns+` FROM tasks WHERE id = ?`, id)
	t, err := scanTask(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, fmt.Errorf("task %q not found", id)
	}
	return t, err
}

func (s *SQLiteStore) List(ctx context.Context, f ListFilter) ([]*Task, error) {
	query, args := buildListQuery(f)
	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTasks(rows)
}

func (s *SQLiteStore) ReadyTasks(ctx context.Context) ([]*Task, error) {
	rows, err := s.db.QueryContext(ctx,
		`SELECT `+taskColumns+` FROM tasks WHERE status = 'ready' ORDER BY priority DESC, created_at ASC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTasks(rows)
}

func (s *SQLiteStore) RunningTasks(ctx context.Context) ([]*Task, error) {
	rows, err := s.db.QueryContext(ctx,
		`SELECT `+taskColumns+` FROM tasks WHERE status = 'running'`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return scanTasks(rows)
}

// --- Atomic helpers ---

// ClaimTask does a compare-and-swap from ready → running.
// Returns (true, nil) if this caller won the race, (false, nil) if lost.
func (s *SQLiteStore) ClaimTask(ctx context.Context, id string, workerPID int) (bool, error) {
	now := time.Now().UTC()
	res, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET status = 'running', worker_pid = ?, started_at = ?
		 WHERE id = ? AND status = 'ready'`,
		workerPID, now, id)
	if err != nil {
		return false, err
	}
	n, err := res.RowsAffected()
	return n == 1, err
}

// ReclaimOrphan resets a running task to ready (for crash recovery).
func (s *SQLiteStore) ReclaimOrphan(ctx context.Context, id string) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE tasks SET status = 'ready', worker_pid = 0, started_at = NULL
		 WHERE id = ? AND status = 'running'`, id)
	return err
}

func (s *SQLiteStore) Close() error {
	return s.db.Close()
}

// --- Scanning helpers ---

const taskColumns = `id, command, priority, depends_on, status, created_at,
	started_at, finished_at, worker_pid, exit_code, retries, max_retries,
	env, work_dir, output`

type scanner interface {
	Scan(dest ...any) error
}

func scanTask(row scanner) (*Task, error) {
	var (
		t          Task
		cmd        string
		deps       string
		env        string
		startedAt  sql.NullTime
		finishedAt sql.NullTime
		exitCode   sql.NullInt64
	)
	err := row.Scan(
		&t.ID, &cmd, &t.Priority, &deps, &t.Status, &t.CreatedAt,
		&startedAt, &finishedAt, &t.WorkerPID, &exitCode, &t.Retries, &t.MaxRetries,
		&env, &t.WorkDir, &t.Output,
	)
	if err != nil {
		return nil, err
	}

	t.Command, err = unmarshalStringSlice(cmd)
	if err != nil {
		return nil, err
	}
	t.Env, err = unmarshalStringMap(env)
	if err != nil {
		return nil, err
	}
	if deps != "" {
		t.DependsOn = strings.Split(deps, ",")
	}
	if startedAt.Valid {
		t.StartedAt = &startedAt.Time
	}
	if finishedAt.Valid {
		t.FinishedAt = &finishedAt.Time
	}
	if exitCode.Valid {
		v := int(exitCode.Int64)
		t.ExitCode = &v
	}
	return &t, nil
}

func scanTasks(rows *sql.Rows) ([]*Task, error) {
	var out []*Task
	for rows.Next() {
		t, err := scanTask(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

// buildListQuery constructs a SELECT with optional WHERE clauses from a ListFilter.
func buildListQuery(f ListFilter) (string, []any) {
	q := `SELECT ` + taskColumns + ` FROM tasks`
	var clauses []string
	var args []any

	if len(f.Status) > 0 {
		placeholders := make([]string, len(f.Status))
		for i, s := range f.Status {
			placeholders[i] = "?"
			args = append(args, string(s))
		}
		clauses = append(clauses, "status IN ("+strings.Join(placeholders, ",")+")")
	}
	if f.MinPriority > 0 {
		clauses = append(clauses, "priority >= ?")
		args = append(args, int(f.MinPriority))
	}
	if len(clauses) > 0 {
		q += " WHERE " + strings.Join(clauses, " AND ")
	}
	q += " ORDER BY priority DESC, created_at ASC"
	if f.Limit > 0 {
		q += " LIMIT ?"
		args = append(args, f.Limit)
	}
	if f.Offset > 0 {
		q += " OFFSET ?"
		args = append(args, f.Offset)
	}
	return q, args
}
```

---

## File: `store/marshal.go` (serialization helpers)

```go
package store

import (
	"encoding/json"
)

func marshalStringSlice(v []string) (string, error) {
	if len(v) == 0 {
		return "[]", nil
	}
	b, err := json.Marshal(v)
	return string(b), err
}

func unmarshalStringSlice(s string) ([]string, error) {
	if s == "" || s == "[]" {
		return nil, nil
	}
	var v []string
	err := json.Unmarshal([]byte(s), &v)
	return v, err
}

func marshalStringMap(m map[string]string) (string, error) {
	if len(m) == 0 {
		return "{}", nil
	}
	b, err := json.Marshal(m)
	return string(b), err
}

func unmarshalStringMap(s string) (map[string]string, error) {
	if s == "" || s == "{}" {
		return nil, nil
	}
	var m map[string]string
	err := json.Unmarshal([]byte(s), &m)
	return m, err
}
```

---

## File: `types.go` (shared domain types — package `tq` or a shared `types` package)

```go
package tq

import "time"

// TaskStatus represents the lifecycle state of a task.
type TaskStatus string

const (
	StatusPending   TaskStatus = "pending"
	StatusReady     TaskStatus = "ready"
	StatusRunning   TaskStatus = "running"
	StatusDone      TaskStatus = "done"
	StatusFailed    TaskStatus = "failed"
	StatusCancelled TaskStatus = "cancelled"
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
	ID         string
	Command    []string
	Priority   Priority
	DependsOn  []string
	Status     TaskStatus
	CreatedAt  time.Time
	StartedAt  *time.Time
	FinishedAt *time.Time
	WorkerPID  int
	ExitCode   *int
	Retries    int
	MaxRetries int
	Env        map[string]string
	WorkDir    string
	Output     string
}
```

---

## File: `store/interfaces.go` (Store interface and ListFilter)

```go
package store

import (
	"context"
	"time"

	tq "github.com/yourorg/tq"
)

// Re-export the domain types used by the Store layer.
type (
	Task       = tq.Task
	TaskStatus = tq.TaskStatus
	Priority   = tq.Priority
)

// ListFilter controls which tasks List() returns.
type ListFilter struct {
	Status      []TaskStatus
	MinPriority Priority
	Limit       int
	Offset      int
}

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
	ReadyTasks(ctx context.Context) ([]*Task, error)
	RunningTasks(ctx context.Context) ([]*Task, error)

	// Atomic helpers
	ClaimTask(ctx context.Context, id string, workerPID int) (bool, error)
	ReclaimOrphan(ctx context.Context, id string) error

	Close() error
}
```

---

## File: `dag/dag.go` (cycle detection)

```go
package dag

import (
	"errors"

	tq "github.com/yourorg/tq"
)

type Task = tq.Task

// ErrCycle is returned when a dependency cycle is detected.
var ErrCycle = errors.New("dependency cycle detected")

// DAG is an adjacency list representation of the dependency graph.
type DAG struct {
	Nodes map[string]*Task
	Edges map[string][]string // id -> list of dependency IDs
}

// CheckCycle returns ErrCycle if adding task t would create a cycle.
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
			return true // cycle: we encountered a node that is on the current DFS stack
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

---

## File: `main.go`

```go
package main

import "github.com/yourorg/tq/cmd"

func main() {
	cmd.Execute()
}
```

---

## File: `go.mod` (example)

```
module github.com/yourorg/tq

go 1.22

require (
	github.com/mattn/go-sqlite3 v1.14.22
	github.com/spf13/cobra v1.8.1
)
```

---

## Design decisions

### ID generation
`crypto/rand` reads 4 bytes and encodes them as 8 hex characters. This gives 2³² (~4 billion) possible IDs — sufficient for a local task queue with no coordination requirement. `math/rand` is avoided because task IDs used as keys in a persistent store should not be predictable.

### Command parsing
`--cmd "go test ./..."` is a single string that the user writes as a shell command. The `parseCommand` function tokenises it respecting single and double quotes, producing a proper `[]string` argv. This means `tq add test --cmd "go test -count=1 ./..."` correctly produces `["go", "test", "-count=1", "./..."]` without invoking a shell.

### Dependency validation order
1. Check all dependency IDs exist in the store — fast, gives a clear error message per missing ID.
2. Check for cycles — requires reading all tasks, so it runs after the cheaper existence check.
3. Write the task — only after both validations pass.

This ordering avoids partial writes and gives the user the most actionable error first.

### Initial status
- No dependencies → `StatusReady` (can be claimed immediately by the pool).
- Has dependencies → `StatusPending` (scheduler promotes it once deps reach `StatusDone`).

Setting `StatusReady` directly avoids a round-trip through the scheduler's promotion loop for the common case of dependency-free tasks, reducing latency to first execution.

### Store path resolution
`TQ_DB` environment variable overrides the default (`~/.tq/tasks.db`). The directory is created with `0700` permissions so the SQLite file is not world-readable.

### What `name` does
The positional `<name>` argument labels the task for human readability (e.g. in `tq list` output). In this implementation it is captured but not stored as a separate column — it can either be stored as the first element of `Command` for display purposes or in a `name` column added to the schema. The architecture document does not include a `Name` field on `Task`, so this implementation follows that spec faithfully. If a name column is desired, adding `name TEXT` to the schema and a `Name string` field to `Task` is a one-line change.
