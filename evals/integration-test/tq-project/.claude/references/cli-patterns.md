# CLI Patterns — tq

## Command Structure (Francia's Cobra)

```
tq add <name> [--priority N] [--depends-on ID,...] [--cmd "shell command"]
tq run [--workers N] [--timeout DURATION]
tq status [ID]
tq list [--state STATE] [--json]
tq cancel ID
tq reset ID
```

Each command is a Cobra command with standard help, shell completions, and consistent flag naming.

## Output Philosophy (Frazelle + Hickey)

**Default output:** Human-readable, one record per line, tab-separated fields. Grep-friendly.

```
$ tq list
ID      STATE   PRI  NAME           DEPENDS
a1b2    ready   10   build-frontend
c3d4    pending  5   deploy         a1b2
e5f6    done     1   lint
```

**JSON output:** `--json` flag on every command. Full structured output for machines.

```
$ tq list --json | jq '.[] | select(.state == "ready") | .name'
"build-frontend"
```

**Rules:**
- No ANSI colors unless stdout is a TTY (check `os.IsTerminal`)
- No progress bars or spinners in non-TTY mode
- Exit code 0 for success, 1 for errors, 2 for usage errors
- Stderr for errors and diagnostics, stdout for data

## Error Messages

Every error includes:
1. What operation was attempted
2. What went wrong
3. Enough context to debug without `--verbose`

```
tq: cannot add task "deploy": dependency "build-frontend" (a1b2) is in state "failed"
```

Not:
```
error: invalid dependency
```

## Pipe Compatibility

Commands that produce lists work with Unix tools:
- `tq list | grep ready` — filter by state
- `tq list --json | jq '.[] | .id'` — extract IDs
- `tq list | wc -l` — count tasks
- `tq status a1b2 | head -1` — quick state check

Commands that take input accept IDs from stdin when no argument given:
- `tq list --state failed | tq reset -` — reset all failed tasks
