# tq export — Design Spec

## Goal

Add a `tq export <output-file>` command that dumps the entire queue state to a JSON file for backup and migration. The exported format includes metadata (tq version, export timestamp, task count) and is designed to be importable by a future `tq import` command.

**Prerequisite:** Add a `Version` variable to `cmd/root.go` for metadata. No store interface changes — `List(Filter{})` with nil `State` already returns all tasks.

## Architecture

Minimal footprint — one new command file, one version variable, tests.

```
cmd/
├── root.go         # MODIFY — add Version variable
├── export.go       # NEW — tq export command
└── export_test.go  # NEW — tests for export command
```

No changes to the store interface. No changes to existing commands. No new dependencies.

---

## Version Variable (`cmd/root.go`)

Add a package-level variable settable via ldflags:

```go
var Version = "0.1.0"
```

This follows the standard Go pattern for build-time version injection:

```
go build -ldflags "-X tq/cmd.Version=1.2.3"
```

The variable is used by the export command for metadata. Future commands (`tq version`, `tq import` compatibility checks) can also reference it.

---

## Export Format

The export file is always JSON, regardless of the `--json` flag (which controls stdout feedback only).

```json
{
  "metadata": {
    "version": "0.1.0",
    "exported_at": "2026-03-28T12:00:00Z",
    "task_count": 3
  },
  "tasks": [
    {
      "id": "a1b2c3d4",
      "name": "build",
      "cmd": "make build",
      "state": "ready",
      "priority": 5,
      "depends_on": [],
      "created_at": "2026-03-28T10:00:00Z"
    }
  ]
}
```

### Metadata Fields

| Field | Type | Description |
|---|---|---|
| `version` | string | Value of `cmd.Version` at export time |
| `exported_at` | string | RFC 3339 UTC timestamp of when the export was generated |
| `task_count` | int | Number of tasks in the `tasks` array (redundant, but useful for quick validation) |

### Task Fields

Identical to the `ListTask` JSON structure used by `tq list --json`:

| Field | Type | Description |
|---|---|---|
| `id` | string | 8-char hex task ID |
| `name` | string | Task name |
| `cmd` | string | Shell command |
| `state` | string | One of: pending, ready, running, done, failed, dead |
| `priority` | int | Task priority |
| `depends_on` | array | List of dependency task IDs (empty array if none, never null) |
| `created_at` | string | RFC 3339 timestamp |

`depends_on` is always an array, never null — matching the `tq add` convention where nil slices are converted to empty slices before storage.

### Import Compatibility

The format is designed for a future `tq import` command:
- `metadata.version` enables the importer to detect format differences and migrate if needed.
- `metadata.task_count` enables quick validation that the file isn't truncated.
- `tasks` contains the full task state — an importer can recreate the queue by calling `Store.Add` for each task.
- Tasks in `running` state will be imported as-is; the importer may choose to reset them to `ready`.

---

## Command: `tq export`

### Usage

```
tq export <output-file> [--force]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `<output-file>` | yes | Path to the output JSON file |

### Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--force` | bool | false | Overwrite output file if it already exists |

Inherits `--json` from root — controls stdout feedback format, not the export file.

### Behavior

1. Call `s.List(store.Filter{})` to retrieve all tasks (all states).
2. Check if `output-file` exists. If yes and `--force` is false, return error.
3. Build the export structure: metadata (version, timestamp, task count) + tasks array.
4. Marshal to JSON with indentation (`json.MarshalIndent` with 2-space indent) for human readability.
5. Write to a temporary file in the same directory as `output-file` using `os.CreateTemp(dir, ".tq-export-*.tmp")`.
6. Fsync the temporary file via `f.Sync()`.
7. Close the file, then `os.Rename` the temporary file to `output-file` (atomic on POSIX).
8. Print feedback to stdout.

The atomic write pattern (temp file + fsync + rename) ensures a power failure mid-export never leaves a corrupt partial file at the target path.

### Output

**Default (text):**

```
exported 42 tasks to backup.json
```

Format: `fmt.Fprintf(w, "exported %d tasks to %s\n", count, path)`

**JSON (`--json`):**

```json
{"path":"backup.json","task_count":42}
```

JSON struct:

```go
type ExportResult struct {
    Path      string `json:"path"`
    TaskCount int    `json:"task_count"`
}
```

### Errors

| Condition | Message | Exit |
|---|---|---|
| File exists (no --force) | `tq: cannot export: file exists (use --force to overwrite)` | 1 |
| Write failure | `tq: cannot export: write <path>: <os error>` | 1 |
| Store list failure | `tq: cannot export: <store error>` | 1 |
| Wrong arg count | Cobra usage error | 2 |

Errors return from `RunE`. No `os.Exit` in command logic.

### Testability

Injectable function:

```go
func runExportWithStore(s store.Store, outputPath string, force bool, jsonOut bool, w io.Writer) error
```

The `RunE` function creates the store and delegates:

```go
func runExport(cmd *cobra.Command, args []string) error {
    s := store.NewMemoryStore()
    defer s.Close()
    return runExportWithStore(s, args[0], exportForce, jsonOutput, os.Stdout)
}
```

---

## Testing

### Command Tests (`cmd/export_test.go`)

All tests use `t.TempDir()` for file paths and `seedStore` for task injection.

| Test | Setup | Action | Verify |
|---|---|---|---|
| `TestExport` | Seed 2 tasks | Export to new file | File exists, valid JSON, metadata correct (version, task_count=2, exported_at is RFC3339), tasks array has 2 entries with correct fields |
| `TestExportJSON` | Seed 2 tasks | Export with `--json` | Stdout has `ExportResult` JSON with path and task_count=2 |
| `TestExportFileExists` | Create file at target path | Export without --force | Error contains "file exists (use --force to overwrite)" |
| `TestExportFileExistsForce` | Create file at target path, seed 1 task | Export with --force | Success, file overwritten with valid export JSON |
| `TestExportEmptyQueue` | Empty store | Export to new file | File exists, valid JSON, task_count=0, tasks is empty array |
| `TestExportDependsOnNeverNull` | Seed 1 task with no deps, 1 task with deps | Export | Both tasks have `depends_on` as arrays (empty `[]`, not null) |

---

## Conventions

All conventions from previous specs remain. Additional conventions for this feature:

- **Error messages:** `tq: cannot export: <reason>` — verb is `export`, no task ID in error (command operates on the whole queue).
- **Output:** Text shows `exported N tasks to <path>`. JSON shows `ExportResult` struct with `path`, `task_count`.
- **Export file format:** Always JSON with 2-space indent, regardless of `--json` flag. `--json` controls stdout only.
- **Atomic writes:** Temp file + fsync + rename. Never leave a partial file at the target path.
- **Null safety:** `depends_on` is always `[]`, never `null` in the export JSON.
- **Timestamps:** RFC 3339 UTC for `exported_at` and `created_at`.
- **Version:** `cmd.Version` variable, defaulting to `"0.1.0"`, settable via ldflags.
- **Exit codes:** 0 for success, 1 for errors, 2 for usage (Cobra).
- **Errors from RunE:** Return errors, never call `os.Exit` in command logic.
- **Package boundaries:** `cmd/` imports `store/`. `store/` imports only stdlib.

## Risks

1. **Atomic rename is POSIX only.** `os.Rename` is atomic on POSIX filesystems but not guaranteed on all Windows filesystems. For a local-first CLI targeting dev machines, this is acceptable. If Windows support becomes critical, a platform-specific write path may be needed — not now.

2. **No store interface changes.** This spec relies on `List(Filter{})` returning all tasks. If a future store implementation (e.g., BoltDB) paginates `List`, the export command would need updating. Current MemoryStore returns all tasks in one call — no issue today.

3. **Large exports fit in memory.** The entire task list is marshaled to JSON in memory before writing. For the in-memory store, this is fine — the tasks are already in memory. If the store grows to millions of tasks, streaming JSON would be needed — not a realistic scenario for a local task queue CLI.

4. **Temp file cleanup on failure.** If the process is killed between creating the temp file and renaming it, a `.tmp` file may remain. This is a minor inconvenience, not data corruption. The target file is never in a partial state.
