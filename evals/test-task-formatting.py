#!/usr/bin/env python3
"""A/B test: verbatim vs formatted task descriptions for local model execution.

Tests whether mechanically formatting plan tasks (stripping metadata,
flattening checkboxes, making instructions explicit) improves Gemma's
spec compliance compared to pasting tasks verbatim.

Usage:
    python3 test-task-formatting.py [OPTIONS]

Options:
    --server URL        llama-server URL (default: http://localhost:8080)
    --max-tokens N      Max tokens (default: 4096)
    --temp FLOAT        Temperature (default: 0.0)
    --runs N            Number of runs per variant (default: 1)
    --fixture N         Run single fixture by 1-based index
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent


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


def generate(url, prompt, system=None, max_tokens=4096, temp=0.0):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        f"{url}/v1/chat/completions",
        json={
            "messages": messages,
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
    reasoning = msg.get("reasoning_content", "")
    usage = data.get("usage", {})

    if not content.strip() and reasoning:
        print("  WARNING: model used all tokens for thinking")
        return "", {
            "reasoning_chars": len(reasoning),
            "reasoning_words": len(reasoning.split()),
            "output_chars": 0,
            "tokens_total": usage.get("completion_tokens", 0),
        }

    if "<channel|>" in content:
        content = content.split("<channel|>", 1)[1].strip()

    stats = {
        "reasoning_chars": len(reasoning),
        "reasoning_words": len(reasoning.split()) if reasoning else 0,
        "output_chars": len(content),
        "output_words": len(content.split()) if content else 0,
        "tokens_total": usage.get("completion_tokens", 0),
        "think_ratio": f"{len(reasoning)/(len(content) or 1):.1f}:1",
    }
    return content, stats


def load_fixtures(path):
    """Load JSON fixture file, return list of fixture dicts."""
    return json.loads(Path(path).read_text())


def build_system_prompt(fixture_dir):
    """Read CLAUDE.md from fixture_dir; return content after '---' separator (the harness).

    If no '---' found, return entire content.
    """
    claude_md = Path(fixture_dir) / "CLAUDE.md"
    if not claude_md.exists():
        return None
    text = claude_md.read_text()
    if "---" in text:
        return text.split("---", 1)[1].strip()
    return text.strip()


def build_source_context(fixture_dir):
    """Recursively gather source files, format as annotated code blocks."""
    fixture_dir = Path(fixture_dir)
    parts = []
    for ext in ("*.rb", "*.ts", "*.py", "*.json"):
        for f in sorted(fixture_dir.rglob(ext)):
            rel = f.relative_to(fixture_dir)
            rel_str = str(rel)
            if rel_str.startswith(".claude") or rel_str.startswith("CLAUDE"):
                continue
            if f.stat().st_size > 10000:
                continue
            parts.append(f"### {rel}\n\n```\n{f.read_text()}\n```")
    return "\n\n".join(parts) if parts else ""


def build_user_message(task_text, source_context, output_files):
    """Assemble user message from task, source context, and output file list."""
    file_list = "\n".join(f"- {f}" for f in output_files)
    return (
        f"{task_text}\n\n"
        f"## Current Files\n\n{source_context}\n\n"
        f"## Output Files\n\n{file_list}"
    )


def score_response(text, fixture):
    """Structural scoring: parse success, path accuracy, spec compliance, code ratio."""
    lines = text.splitlines()

    # Parse success: at least one code block, with a file-path comment line
    triple_backtick_count = text.count("```")
    has_code_blocks = triple_backtick_count >= 2

    # Check if at least one code block has a line starting with '#' containing '/'
    in_block = False
    found_path_comment = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_block = not in_block
            continue
        if in_block and stripped.startswith("#") and "/" in stripped:
            found_path_comment = True
            break

    parse_success = has_code_blocks and found_path_comment

    # Path accuracy: fraction of output_files found in code block headers or first lines
    found_paths = 0
    for path in fixture["output_files"]:
        # Check code block fences (```ruby\n# path) and inline references
        if path in text:
            found_paths += 1
            continue
        # Substring match against any line containing a path segment
        basename = path.split("/")[-1]
        if basename in text:
            found_paths += 1
    path_accuracy = found_paths / len(fixture["output_files"]) if fixture["output_files"] else 0.0

    # Spec compliance: fraction of spec_checks found (case-insensitive)
    lower_text = text.lower()
    found_checks = sum(
        1 for check in fixture["spec_checks"]
        if check.lower() in lower_text
    )
    spec_compliance = found_checks / len(fixture["spec_checks"]) if fixture["spec_checks"] else 0.0

    # Code ratio: lines inside code blocks / total lines
    total_lines = len(lines) if lines else 1
    code_lines = 0
    in_block = False
    for line in lines:
        if line.strip().startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            code_lines += 1
    code_ratio = code_lines / total_lines if total_lines else 0.0

    return {
        "parse_success": parse_success,
        "path_accuracy": round(path_accuracy, 2),
        "spec_compliance": round(spec_compliance, 2),
        "code_ratio": round(code_ratio, 2),
    }


def print_comparison(fixture_name, results):
    """Print formatted table comparing verbatim vs formatted scores."""
    print(f"\n  Fixture: {fixture_name}")
    header = f"    {'Variant':<12} {'Parse':>6} {'Paths':>6} {'Spec':>6} {'Code%':>6} {'Time':>6} {'Words':>6}"
    print(header)
    print(f"    {'-'*54}")
    for label, runs in results.items():
        if not runs:
            continue
        avg_parse = sum(1 for r in runs if r["scores"]["parse_success"]) / len(runs)
        avg_paths = sum(r["scores"]["path_accuracy"] for r in runs) / len(runs)
        avg_spec = sum(r["scores"]["spec_compliance"] for r in runs) / len(runs)
        avg_code = sum(r["scores"]["code_ratio"] for r in runs) / len(runs)
        avg_time = sum(r["time_s"] for r in runs) / len(runs)
        avg_words = sum(r["stats"]["output_words"] for r in runs) / len(runs)
        tag = "Verbatim" if label == "verbatim" else "Formatted"
        print(
            f"    {tag:<12} {avg_parse:>6.0%} {avg_paths:>6.0%} "
            f"{avg_spec:>6.0%} {avg_code:>6.0%} {avg_time:>5.0f}s {avg_words:>5.0f}w"
        )


def main():
    parser = argparse.ArgumentParser(
        description="A/B test: verbatim vs formatted task descriptions"
    )
    parser.add_argument("--server", default="http://localhost:8080")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temp", type=float, default=0.0)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument(
        "--fixture", type=int, default=None, help="Run single fixture by 1-based index"
    )
    args = parser.parse_args()

    if not check_server(args.server):
        print(f"ERROR: llama-server not reachable at {args.server}")
        sys.exit(1)

    model = detect_model(args.server)

    fixtures_path = SCRIPT_DIR / "prompts" / "task-formatting.json"
    all_fixtures = load_fixtures(fixtures_path)

    if args.fixture is not None:
        idx = args.fixture - 1
        if idx < 0 or idx >= len(all_fixtures):
            print(f"ERROR: --fixture {args.fixture} out of range (1–{len(all_fixtures)})")
            sys.exit(1)
        test_fixtures = [all_fixtures[idx]]
    else:
        test_fixtures = all_fixtures

    fixture_dir = SCRIPT_DIR / "fixtures" / "rails-api-gemma"
    system_prompt = build_system_prompt(fixture_dir)
    source_context = build_source_context(fixture_dir)

    model_short = model.replace(".gguf", "").split("/")[-1]
    temp_label = f"temp{args.temp}".replace(".", "")
    results_dir = SCRIPT_DIR / "results" / f"task-formatting-{model_short}-{temp_label}"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=== Task Formatting A/B Eval ===")
    print(f"Model:      {model}")
    print(f"Server:     {args.server}")
    print(f"Temp:       {args.temp}, Max tokens: {args.max_tokens}")
    print(f"Runs:       {args.runs}")
    print(f"Fixtures:   {len(test_fixtures)}")
    print()

    all_results = []
    per_fixture_results = {}

    variants = [
        ("verbatim", "task_verbatim"),
        ("formatted", "task_formatted"),
    ]

    for fixture in test_fixtures:
        fixture_name = fixture["name"]
        per_fixture_results[fixture_name] = {"verbatim": [], "formatted": []}

        print(f"{'=' * 60}")
        print(f"FIXTURE: {fixture_name}")
        print(f"{'=' * 60}")

        for label, key in variants:
            task_text = fixture[key]
            user_message = build_user_message(task_text, source_context, fixture["output_files"])

            for run in range(1, args.runs + 1):
                run_label = f" (run {run}/{args.runs})" if args.runs > 1 else ""
                tag = "Verbatim" if label == "verbatim" else "Formatted"
                print(f"  {tag}{run_label}...", end=" ", flush=True)

                start = time.time()
                content, stats = generate(
                    args.server,
                    user_message,
                    system=system_prompt,
                    max_tokens=args.max_tokens,
                    temp=args.temp,
                )
                elapsed = time.time() - start
                scores = score_response(content, fixture)

                print(
                    f"{elapsed:.0f}s, {stats['output_words']}w, "
                    f"spec={scores['spec_compliance']:.0%}, "
                    f"paths={scores['path_accuracy']:.0%}, "
                    f"parse={'OK' if scores['parse_success'] else 'FAIL'}"
                )

                result = {
                    "fixture": fixture_name,
                    "variant": label,
                    "run": run,
                    "time_s": round(elapsed, 1),
                    "response": content,
                    "stats": stats,
                    "scores": scores,
                }
                all_results.append(result)
                per_fixture_results[fixture_name][label].append(result)

                out_name = fixture_name.lower().replace(" ", "-")
                out_path = results_dir / f"{out_name}-{label}-run{run}.json"
                out_path.write_text(json.dumps(result, indent=2))

        print_comparison(fixture_name, per_fixture_results[fixture_name])
        print()

    # Aggregate summary
    print(f"{'=' * 60}")
    print("AGGREGATE SUMMARY")
    print(f"{'=' * 60}")
    print(f"\n  {'Variant':<12} {'Parse':>6} {'Paths':>6} {'Spec':>6} {'Code%':>6} {'Time':>6} {'Words':>6}")
    print(f"  {'-'*54}")

    for label, _ in variants:
        runs = [r for r in all_results if r["variant"] == label]
        if not runs:
            continue
        avg_parse = sum(1 for r in runs if r["scores"]["parse_success"]) / len(runs)
        avg_paths = sum(r["scores"]["path_accuracy"] for r in runs) / len(runs)
        avg_spec = sum(r["scores"]["spec_compliance"] for r in runs) / len(runs)
        avg_code = sum(r["scores"]["code_ratio"] for r in runs) / len(runs)
        avg_time = sum(r["time_s"] for r in runs) / len(runs)
        avg_words = sum(r["stats"]["output_words"] for r in runs) / len(runs)
        tag = "Verbatim" if label == "verbatim" else "Formatted"
        print(
            f"  {tag:<12} {avg_parse:>6.0%} {avg_paths:>6.0%} "
            f"{avg_spec:>6.0%} {avg_code:>6.0%} {avg_time:>5.0f}s {avg_words:>5.0f}w"
        )

    summary = {
        "model": model,
        "temp": args.temp,
        "runs": args.runs,
        "fixtures": len(test_fixtures),
        "results": [
            {k: v for k, v in r.items() if k != "response"}
            for r in all_results
        ],
    }
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nResults saved to: {results_dir}")


if __name__ == "__main__":
    main()
