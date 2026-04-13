#!/usr/bin/env python3
"""Test a local model's ability to execute a task from a spec/plan.

Gives the model a real task from an implementation plan and compares
the output against what was actually built. Tests whether the model
can serve as an executor in the Opus-orchestrated GIGO pipeline.

Requires a running llama-server instance. Start one with:
    ./start-local-server.sh [MODEL_PATH]

Usage:
    python3 test-executor.py [OPTIONS]

Options:
    --server URL        llama-server URL (default: http://localhost:8080)
    --task N            Which task to run: 1=bash-script, 2=typescript (default: 1)
    --max-tokens N      Max tokens (default: 4096)
    --temp FLOAT        Temperature (default: 0.3)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent

# Task 1: Write the cleanup verification script (bash, well-scoped)
TASK_1_PROMPT = """You are a software engineer executing a task from an implementation plan. Follow the instructions precisely. Output ONLY the file contents requested — no explanation, no commentary.

## Task: Write Agent Teams Cleanup Verification Script

Write a bash script at `evals/validation/run-cleanup-verify.sh` that verifies the Agent Teams feature cleanup was done correctly. This is a pure grep-based test — no Claude invocations.

### Requirements

The script must:
1. Accept an optional results directory argument (default: `evals/results/validation-YYYY-MM-DD-HHMMSS`)
2. Run 5 checks against the project's skill files:

**Check 1:** No "Tier 3" references in `skills/execute/SKILL.md`
**Check 2:** No `TeamCreate` or team-scoped `SendMessage` references in `skills/execute/SKILL.md`
**Check 3:** No Tier 3 templates (`Tier 3`, `team.prompt`, `team.template`) in `skills/execute/references/teammate-prompts.md`
**Check 4:** Design doc exists at `skills/execute/references/agent-teams-design.md` AND has a status banner containing "not shipped" or "target.state" in the first 10 lines
**Check 5:** No `AGENT_TEAMS` or `EXPERIMENTAL_AGENT` environment variable references in `skills/execute/SKILL.md`

3. For each check, output a line showing the check name and [CLEAN] or [DIRTY]
4. Track pass count and output final PASS/FAIL (all 5 must pass)
5. Write a JSON results file to `$RESULTS_DIR/cleanup-test.json` with structure: `{"test": "cleanup-verify", "passed": N, "total": 5, "result": "PASS|FAIL", "details": [...]}`
6. Exit 0 on PASS, exit 1 on FAIL

### Conventions
- Use `set -euo pipefail`
- Derive project directory from script location: script is at `evals/validation/`, project root is two levels up
- When `grep -c` finds 0 matches it returns exit code 1 — handle this correctly so the script doesn't abort
- The details array should contain one object per check with at minimum: check number, name, and clean (boolean)

### Output format
Write ONLY the bash script contents. Start with `#!/usr/bin/env bash`. No markdown fences, no explanation.
"""

# Task 2: Write a TypeScript type definition (cross-file coherence)
TASK_2_PROMPT = """You are a software engineer executing a task from an implementation plan. Follow the instructions precisely. Output ONLY the file contents requested — no explanation, no commentary.

## Task: Write Shared Type Definitions

Write `src/types.ts` for a task management API. This file defines the shared types used across API routes, hooks, and components.

### Requirements

Define the following types:

1. **Status** — Union type: `'draft' | 'active' | 'paused' | 'completed' | 'archived'`

2. **Task** — Object type with fields:
   - `id: string`
   - `title: string`
   - `description: string | null`
   - `status: Status`
   - `projectId: string`
   - `assigneeId: string | null`
   - `created_at: string` (ISO 8601, snake_case to match DB column naming)
   - `updated_at: string`

3. **Project** — Object type with fields:
   - `id: string`
   - `name: string`
   - `status: 'creating' | 'ready' | 'archived'`
   - `memberCount: number` (only present when status is 'ready')
   - `created_at: string`

4. **ApiResponse<T>** — Generic wrapper: `{ data: T, total?: number }`

5. **ApiError** — Error envelope: `{ error: { code: string, message: string, details?: Record<string, string> } }`

### Conventions
- Use TypeScript `type` declarations, not `interface`
- Export all types
- No runtime code — types only
- Use JSDoc comments on each type explaining its purpose

### Output format
Write ONLY the TypeScript file contents. No markdown fences, no explanation.
"""


def check_server(url):
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def detect_model(url):
    try:
        resp = requests.get(f"{url}/v1/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                return data["data"][0].get("id", "local")
    except Exception:
        pass
    return "local"


def generate(url, prompt, max_tokens=4096, temp=0.3):
    """Generate with low temp — execution tasks need precision, not creativity."""
    resp = requests.post(
        f"{url}/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temp,
            "top_p": 0.9,
            "stream": False,
        },
        timeout=1800,
    )
    resp.raise_for_status()
    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "")

    # llama-server splits Gemma 4 output into content + reasoning_content
    if not content.strip() and msg.get("reasoning_content"):
        print(f"\n  WARNING: model used all tokens for thinking, no visible output")
        print(f"  Reasoning preview: {msg['reasoning_content'][:200]}...")
        return ""

    # Strip older Gemma 4 channel markers
    if "<channel|>" in content:
        content = content.split("<channel|>", 1)[1].strip()

    # Strip markdown fences if the model wrapped output
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first line (```bash or ```typescript)
        lines = lines[1:]
        # Remove last ``` if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    return content


TASKS = {
    1: {"name": "cleanup-verify-script", "ext": ".sh", "prompt": TASK_1_PROMPT,
        "compare": "evals/validation/run-cleanup-verify.sh"},
    2: {"name": "types-definition", "ext": ".ts", "prompt": TASK_2_PROMPT,
        "compare": None},
}


def main():
    parser = argparse.ArgumentParser(description="Test local model as executor")
    parser.add_argument("--server", default="http://localhost:8080")
    parser.add_argument("--task", type=int, default=1, choices=TASKS.keys())
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temp", type=float, default=0.3)
    args = parser.parse_args()

    if not check_server(args.server):
        print(f"ERROR: llama-server not reachable at {args.server}")
        print(f"Start it with: ./start-local-server.sh [MODEL_PATH]")
        sys.exit(1)

    model_name = detect_model(args.server)
    task = TASKS[args.task]

    print(f"=== Executor Test: {task['name']} ===")
    print(f"Server: {args.server}")
    print(f"Model: {model_name}")
    print(f"Temp: {args.temp}")
    print()

    print("Generating...", flush=True)
    start = time.time()
    response = generate(args.server, task["prompt"],
                        max_tokens=args.max_tokens, temp=args.temp)
    elapsed = time.time() - start
    words = len(response.split())
    print(f"Done: {elapsed:.1f}s, {words} words")

    # Save output
    results_dir = SCRIPT_DIR / "results" / "executor-test"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / f"task-{args.task}-output{task['ext']}"
    output_path.write_text(response)

    metadata = {
        "model": model_name,
        "task": task["name"],
        "time_s": round(elapsed, 1),
        "words": words,
        "temp": args.temp,
        "max_tokens": args.max_tokens,
    }
    (results_dir / f"task-{args.task}-metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )

    print(f"\nOutput saved to: {output_path}")
    if task["compare"]:
        print(f"Compare against: {task['compare']}")

    # Quick structural checks
    print(f"\n--- Quick Checks ---")
    if task["ext"] == ".sh":
        has_shebang = response.startswith("#!/")
        has_set = "set -euo pipefail" in response
        has_json = "cleanup-test.json" in response
        print(f"  Shebang:        {'PASS' if has_shebang else 'FAIL'}")
        print(f"  set -euo:       {'PASS' if has_set else 'FAIL'}")
        print(f"  JSON output:    {'PASS' if has_json else 'FAIL'}")
    elif task["ext"] == ".ts":
        has_status = "Status" in response
        has_task = "Task" in response
        has_export = "export" in response
        has_api_response = "ApiResponse" in response
        print(f"  Status type:    {'PASS' if has_status else 'FAIL'}")
        print(f"  Task type:      {'PASS' if has_task else 'FAIL'}")
        print(f"  Exports:        {'PASS' if has_export else 'FAIL'}")
        print(f"  ApiResponse:    {'PASS' if has_api_response else 'FAIL'}")


if __name__ == "__main__":
    main()
