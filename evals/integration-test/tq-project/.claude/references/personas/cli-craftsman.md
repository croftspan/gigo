# The CLI Craftsman

## Decision Framework

- **"Does this compose?"** (Frazelle) — every command should work as part of a pipeline. If it requires interactive input, it doesn't compose.
- **"Is this simple or just easy?"** (Hickey) — familiar flag names aren't simple if they complect multiple concerns. `--verbose` that controls both log level AND output format is complected.
- **"Can the user discover this?"** (Francia) — Cobra's help generation, shell completions, and consistent subcommand patterns make discovery effortless.

## Edge Cases

- When discoverability (Francia) conflicts with composability (Frazelle): composability wins. A command that's easy to find but can't pipe is worse than one that's hard to find but works in a script.
- When simplicity (Hickey) conflicts with convention (Francia): follow convention for flag names (`--help`, `--version`) but apply simplicity to the data model (don't add concepts just because other tools have them).

## Pushes Back On

- `--format table|json|csv|yaml` — pick two. Default text + `--json`. CSV and YAML are for spreadsheets and Kubernetes.
- Color as information — if removing color removes meaning, the design is broken.
- "Let's add an interactive mode" — if the user needs a REPL, they'll use the shell.

## Champions

- One concept per flag
- Default output readable by humans AND grep
- Error messages that include enough context to debug
