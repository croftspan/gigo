#!/usr/bin/env python3
"""Local eval runner using llama-server (OpenAI-compatible API).

Requires a running llama-server instance. Start one with:
    ./start-local-server.sh [MODEL_PATH]

Usage:
    python3 run-local-eval.py [OPTIONS]

Options:
    --server URL        llama-server URL (default: http://localhost:8080)
    --model NAME        Model name for results metadata (default: auto-detect)
    --runs N            Number of runs per prompt (default: 1)
    --domains D1,D2     Comma-separated domains (default: rails-api,childrens-novel)
    --prompts 05,06,07  Comma-separated prompt numbers to run (default: all)
    --max-tokens N      Max tokens per generation (default: 2048)
    --results-dir DIR   Output directory (default: evals/results/local-TIMESTAMP)
    --skip-judge        Generate responses only, skip judging
    --judge-only DIR    Score existing results directory, skip generation
    --temp FLOAT        Sampling temperature (default: 0.7)
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

import requests

SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
JUDGE_TEMPLATE_PATH = SCRIPT_DIR / "judge-prompt.md"


def check_server(url):
    """Verify llama-server is running and return model info."""
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        if resp.status_code == 200:
            return True
    except requests.ConnectionError:
        pass
    return False


def detect_model(url):
    """Try to get model name from server."""
    try:
        resp = requests.get(f"{url}/v1/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                return data["data"][0].get("id", "local")
    except Exception:
        pass
    return "local"


def generate(url, prompt, system=None, max_tokens=2048, temp=0.7):
    """Generate a response via llama-server's OpenAI-compatible API.

    Handles Gemma 4's thinking mode: llama-server splits output into
    'content' (visible) and 'reasoning_content' (thinking). We return
    visible content only. If content is empty but reasoning exists,
    the model spent all tokens thinking — caller should increase max_tokens.
    """
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

    # If content is empty but reasoning exists, warn
    if not content.strip() and msg.get("reasoning_content"):
        content = "[THINKING_ONLY: model used all tokens for reasoning]"

    # Strip Gemma 4 channel markers (older format)
    if "<channel|>" in content:
        content = content.split("<channel|>", 1)[1].strip()

    return content


def build_assembled_context(fixture_dir):
    """Read CLAUDE.md + .claude/rules/*.md to build system context.
    Replicates what `claude -p` does automatically in a directory."""
    parts = []

    claude_md = fixture_dir / "CLAUDE.md"
    if claude_md.exists():
        parts.append(f"# Project Instructions (CLAUDE.md)\n\n{claude_md.read_text()}")

    rules_dir = fixture_dir / ".claude" / "rules"
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.md")):
            content = rule_file.read_text()
            parts.append(f"# Rules: {rule_file.name}\n\n{content}")

    refs_dir = fixture_dir / ".claude" / "references"
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob("*.md")):
            content = ref_file.read_text()
            parts.append(f"# Reference: {ref_file.name}\n\n{content}")

    return "\n\n---\n\n".join(parts) if parts else None


def build_source_context(fixture_dir):
    """Read source files to provide as context."""
    parts = []
    for ext in ("*.rb", "*.ts", "*.tsx", "*.py", "*.json", "*.txt"):
        for f in sorted(fixture_dir.rglob(ext)):
            rel = f.relative_to(fixture_dir)
            if str(rel).startswith(".claude") or str(rel).startswith("CLAUDE"):
                continue
            if f.stat().st_size > 10000:
                continue
            parts.append(f"## {rel}\n\n```\n{f.read_text()}\n```")
    return "\n\n".join(parts) if parts else ""


def load_prompts(domain):
    """Load prompts from the prompts file."""
    prompt_file = PROMPTS_DIR / f"{domain}.txt"
    prompts = []
    for line in prompt_file.read_text().strip().split("\n"):
        if not line.strip():
            continue
        axis, prompt = line.split("|", 1)
        prompts.append({"axis": axis.strip(), "prompt": prompt.strip()})
    return prompts


def run_generation(url, fixture_dir, domain, prompts,
                   prompt_filter, num_runs, max_tokens, temp, results_dir):
    """Run bare + assembled generation for selected prompts."""
    assembled_context = build_assembled_context(fixture_dir)
    source_context = build_source_context(fixture_dir)

    bare_system = (
        f"You are reviewing a codebase. Here are the project files:\n\n{source_context}"
        if source_context else None
    )
    assembled_system = (
        f"{assembled_context}\n\n---\n\n# Project Files\n\n{source_context}"
        if assembled_context else bare_system
    )

    domain_dir = results_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    for i, p in enumerate(prompts):
        num = i + 1
        padded = f"{num:02d}"

        if prompt_filter and padded not in prompt_filter:
            continue

        for run in range(1, num_runs + 1):
            run_suffix = f"-run{run}" if num_runs > 1 else ""
            print(f"  [{domain}] Prompt {padded} ({p['axis']})"
                  f"{f' run {run}/{num_runs}' if num_runs > 1 else ''}: {p['prompt']}")

            # Bare
            print(f"    Bare...", end=" ", flush=True)
            start = time.time()
            bare_response = generate(url, p["prompt"],
                                     system=bare_system, max_tokens=max_tokens, temp=temp)
            bare_time = time.time() - start
            bare_out = {"result": bare_response, "model": "local", "time_s": bare_time}
            bare_path = domain_dir / f"{padded}-bare{run_suffix}.json"
            bare_path.write_text(json.dumps(bare_out, indent=2))
            print(f"({bare_time:.1f}s, {len(bare_response.split())}w)")

            # Assembled
            print(f"    Assembled...", end=" ", flush=True)
            start = time.time()
            asm_response = generate(url, p["prompt"],
                                    system=assembled_system, max_tokens=max_tokens, temp=temp)
            asm_time = time.time() - start
            asm_out = {"result": asm_response, "model": "local", "time_s": asm_time}
            asm_path = domain_dir / f"{padded}-assembled{run_suffix}.json"
            asm_path.write_text(json.dumps(asm_out, indent=2))
            print(f"({asm_time:.1f}s, {len(asm_response.split())}w)")


def run_judging(url, results_dir, domain, prompts,
                prompt_filter, num_runs, max_tokens, temp):
    """Score response pairs using the local model as judge."""
    judge_template = JUDGE_TEMPLATE_PATH.read_text()
    domain_dir = results_dir / domain

    for i, p in enumerate(prompts):
        num = i + 1
        padded = f"{num:02d}"

        if prompt_filter and padded not in prompt_filter:
            continue

        for run in range(1, num_runs + 1):
            run_suffix = f"-run{run}" if num_runs > 1 else ""

            bare_path = domain_dir / f"{padded}-bare{run_suffix}.json"
            asm_path = domain_dir / f"{padded}-assembled{run_suffix}.json"
            score_path = domain_dir / f"{padded}-score{run_suffix}.json"

            if not bare_path.exists() or not asm_path.exists():
                continue

            bare_response = json.loads(bare_path.read_text())["result"]
            asm_response = json.loads(asm_path.read_text())["result"]

            # Randomize A/B assignment
            coin = random.randint(0, 1)
            if coin == 0:
                response_a, response_b, a_is = bare_response, asm_response, "bare"
            else:
                response_a, response_b, a_is = asm_response, bare_response, "assembled"

            judge_prompt = judge_template
            judge_prompt = judge_prompt.replace("{PROMPT}", p["prompt"])
            judge_prompt = judge_prompt.replace("{RESPONSE_A}", response_a)
            judge_prompt = judge_prompt.replace("{RESPONSE_B}", response_b)

            run_label = f" run {run}/{num_runs}" if num_runs > 1 else ""
            print(f"  [{domain}] Judging {padded}{run_label}...", end=" ", flush=True)
            start = time.time()
            # Lower temp for judging — we want consistent scoring
            judge_response = generate(
                url, judge_prompt,
                system="You are an impartial judge. Respond with ONLY valid JSON, no other text.",
                max_tokens=1024, temp=0.3,
            )
            judge_time = time.time() - start

            # Parse JSON — strip any remaining artifacts
            judge_text = judge_response.strip()
            if "```json" in judge_text:
                judge_text = judge_text.split("```json", 1)[1]
            if "```" in judge_text:
                judge_text = judge_text.split("```", 1)[0]
            judge_text = judge_text.strip()

            try:
                judge_parsed = json.loads(judge_text)
                score_data = {"a_is": a_is, "judge_output": judge_parsed}
                print(f"OK ({judge_time:.1f}s)")
            except json.JSONDecodeError:
                score_data = {"a_is": a_is, "judge_output_raw": judge_text, "parse_error": True}
                print(f"PARSE ERROR ({judge_time:.1f}s)")

            score_path.write_text(json.dumps(score_data, indent=2))


def compute_summary(results_dir, domains, prompts_by_domain, prompt_filter, num_runs):
    """Compute and print summary statistics."""
    criteria = ["quality_bar", "persona_voice", "expertise_routing", "specificity", "pushback_quality"]

    for domain in domains:
        domain_dir = results_dir / domain
        if not domain_dir.exists():
            continue

        prompts = prompts_by_domain[domain]
        print(f"\n=== {domain} ===\n")

        for i, p in enumerate(prompts):
            num = i + 1
            padded = f"{num:02d}"

            if prompt_filter and padded not in prompt_filter:
                continue

            run_wins = []
            for run in range(1, num_runs + 1):
                run_suffix = f"-run{run}" if num_runs > 1 else ""
                score_path = domain_dir / f"{padded}-score{run_suffix}.json"
                if not score_path.exists():
                    continue

                data = json.loads(score_path.read_text())
                if "parse_error" in data:
                    run_wins.append(None)
                    continue

                a_is = data["a_is"]
                judge = data["judge_output"]
                asm_wins = 0
                for c in criteria:
                    winner = judge.get(c, {}).get("winner", "TIE")
                    if winner == "TIE":
                        pass
                    elif (winner == "A" and a_is == "assembled") or \
                         (winner == "B" and a_is == "bare"):
                        asm_wins += 1
                run_wins.append(asm_wins)

            valid = [w for w in run_wins if w is not None]
            if not valid:
                continue

            if len(valid) == 1:
                print(f"  Prompt {padded} ({p['axis']}): assembled {valid[0]}/5")
            else:
                avg = mean(valid)
                sd = stdev(valid) if len(valid) > 1 else 0
                vals = ", ".join(str(v) for v in valid)
                print(f"  Prompt {padded} ({p['axis']}): mean {avg:.1f}/5 (s={sd:.1f}) [{vals}]")

        total_asm = 0
        total_bare = 0
        total_tie = 0
        parse_errors = 0

        for score_file in sorted(domain_dir.glob("*-score*.json")):
            data = json.loads(score_file.read_text())
            if "parse_error" in data:
                parse_errors += 1
                continue
            a_is = data["a_is"]
            judge = data["judge_output"]
            for c in criteria:
                winner = judge.get(c, {}).get("winner", "TIE")
                if winner == "TIE":
                    total_tie += 1
                elif (winner == "A" and a_is == "assembled") or \
                     (winner == "B" and a_is == "bare"):
                    total_asm += 1
                else:
                    total_bare += 1

        total = total_asm + total_bare + total_tie
        if total > 0:
            pct = total_asm * 100 // total
            print(f"\n  Total: assembled {total_asm}/{total} ({pct}%), "
                  f"ties {total_tie}, bare {total_bare}")
            if parse_errors:
                print(f"  ! {parse_errors} judge parse errors (excluded)")

    summary_path = results_dir / "summary.md"
    summary_path.write_text(
        f"# Local Eval Results\n\nRun: {results_dir.name}\n"
        f"Runs per prompt: {num_runs}\n\n"
        f"See console output for detailed stats.\n"
    )


def main():
    parser = argparse.ArgumentParser(description="Local eval runner using llama-server")
    parser.add_argument("--server", default="http://localhost:8080",
                        help="llama-server URL")
    parser.add_argument("--model", default=None,
                        help="Model name for metadata (auto-detected if omitted)")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--domains", default="rails-api,childrens-novel")
    parser.add_argument("--prompts", default=None, help="e.g. 05,06,07")
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--judge-only", default=None, help="Score existing results dir")
    parser.add_argument("--temp", type=float, default=0.7)
    args = parser.parse_args()

    # Check server
    if not check_server(args.server):
        print(f"ERROR: llama-server not reachable at {args.server}")
        print(f"Start it with: ./start-local-server.sh [MODEL_PATH]")
        sys.exit(1)

    model_name = args.model or detect_model(args.server)
    domains = [d.strip() for d in args.domains.split(",")]
    prompt_filter = set(args.prompts.split(",")) if args.prompts else None
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")

    if args.judge_only:
        results_dir = Path(args.judge_only)
    elif args.results_dir:
        results_dir = Path(args.results_dir)
    else:
        results_dir = SCRIPT_DIR / "results" / f"local-{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Local Eval Suite ===")
    print(f"Server: {args.server}")
    print(f"Model: {model_name}")
    print(f"Runs per prompt: {args.runs}")
    print(f"Domains: {', '.join(domains)}")
    print(f"Results: {results_dir}")
    if prompt_filter:
        print(f"Prompts: {', '.join(sorted(prompt_filter))}")
    print()

    prompts_by_domain = {}
    for domain in domains:
        prompts_by_domain[domain] = load_prompts(domain)

    if not args.judge_only:
        print("=== Generation Phase ===\n")
        for domain in domains:
            fixture_dir = FIXTURES_DIR / domain
            run_generation(args.server, fixture_dir, domain,
                           prompts_by_domain[domain], prompt_filter,
                           args.runs, args.max_tokens, args.temp, results_dir)

    if not args.skip_judge:
        print("\n=== Judging Phase ===\n")
        for domain in domains:
            run_judging(args.server, results_dir, domain,
                        prompts_by_domain[domain], prompt_filter,
                        args.runs, args.max_tokens, args.temp)

    print("\n=== Summary ===")
    compute_summary(results_dir, domains, prompts_by_domain, prompt_filter, args.runs)
    print(f"\nResults saved to: {results_dir}")


if __name__ == "__main__":
    main()
