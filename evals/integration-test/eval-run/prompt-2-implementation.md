# Prompt 2: Implementation

Implement the `tq add` command for a Go CLI task queue tool called tq.

Requirements:
- Uses Cobra for CLI
- Flags: `--priority N` (int, default 0), `--depends-on ID,ID,...` (comma-separated task IDs), `--cmd "shell command"` (required)
- Task name is a positional argument (required)
- Generates a short unique ID for each task (8 chars)
- Validates that dependency IDs exist in the store before adding
- Validates that adding this task doesn't create a dependency cycle
- Stores the task via a Store interface with an `Add(Task) error` method
- Prints the created task ID to stdout on success
- Returns appropriate exit codes (0 success, 1 error)

Produce complete, compilable Go code for the command file and any supporting types.
