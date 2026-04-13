#!/usr/bin/env python3
"""A/B test: original GIGO context vs Gemma-tuned context on local model.

Runs the same prompt through both assembled contexts and prints a side-by-side
comparison. Used to test whether the Gemma-tuned variant produces execution
(code) instead of proposals (commentary).

Usage:
    python3 ab-test-gemma.py [OPTIONS]

Options:
    --server URL        llama-server URL (default: http://localhost:8080)
    --prompt TEXT        Custom prompt (overrides --num)
    --num N             Prompt number from <domain>.txt: 1-10 (default: 1)
    --all               Run all 10 prompts sequentially
    --max-tokens N      Max tokens (default: 4096)
    --temp FLOAT        Temperature (default: 0.0)
    --runs N            Number of runs per variant (default: 1)
    --domain DOMAIN     Domain fixture: rails-api, integration-api, etc. (default: rails-api)
    --gemma-harness     Path to a generated gemma-harness.md for 3-way comparison
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent

DEFAULT_PROMPT = "Add a migration that adds a column to the users table"

ACTION_PHRASES_BY_DOMAIN = {
    "rails-api": [
        "def change", "add_column", "create_table",
        "class ", "migration[", "describe ",
        "def ", "end\n",
    ],
    "integration-api": [
        "export ", "interface ", "const ", "async ",
        "describe(", "it(", "expect(",
        "import ", "type ", "function ",
    ],
}

GENERIC_ACTION_PHRASES = ["def ", "class ", "function ", "const ", "import "]


def load_prompt_list(path):
    """Load numbered prompts from a domain prompt file."""
    prompts = []
    for line in path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        axis, text = line.split("|", 1)
        prompts.append({"axis": axis.strip(), "text": text.strip()})
    return prompts


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


def generate(url, prompt, system=None, max_tokens=4096, temp=0.7):
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
        return "", {"reasoning_chars": len(reasoning), "reasoning_words": len(reasoning.split()),
                    "output_chars": 0, "tokens_total": usage.get("completion_tokens", 0)}

    if "<channel|>" in content:
        content = content.split("<channel|>", 1)[1].strip()

    thinking_stats = {
        "reasoning_chars": len(reasoning),
        "reasoning_words": len(reasoning.split()) if reasoning else 0,
        "output_chars": len(content),
        "output_words": len(content.split()) if content else 0,
        "tokens_total": usage.get("completion_tokens", 0),
        "think_ratio": f"{len(reasoning)/(len(content) or 1):.1f}:1",
    }
    return content, thinking_stats


def build_assembled_context(fixture_dir):
    parts = []
    claude_md = fixture_dir / "CLAUDE.md"
    if claude_md.exists():
        parts.append(f"# Project Instructions (CLAUDE.md)\n\n{claude_md.read_text()}")

    rules_dir = fixture_dir / ".claude" / "rules"
    if rules_dir.exists():
        for rule_file in sorted(rules_dir.glob("*.md")):
            parts.append(f"# Rules: {rule_file.name}\n\n{rule_file.read_text()}")

    refs_dir = fixture_dir / ".claude" / "references"
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob("*.md")):
            parts.append(f"# Reference: {ref_file.name}\n\n{ref_file.read_text()}")

    return "\n\n---\n\n".join(parts) if parts else None


def build_source_context(fixture_dir):
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


def score_output(text, domain="rails-api"):
    """Quick heuristic: does the output execute or propose?"""
    lower = text.lower()
    code_markers = text.count("```")
    proposal_phrases = sum(1 for phrase in [
        "i will", "i would", "i'll propose", "wait for approval",
        "does this meet", "would you like", "shall i",
        "implementation plan", "safety analysis",
        "if approved", "for your approval",
        "autonomy model", "kane's lens", "leach's",
    ] if phrase in lower)
    action_list = ACTION_PHRASES_BY_DOMAIN.get(domain, GENERIC_ACTION_PHRASES)
    action_phrases = sum(1 for phrase in action_list if phrase in lower)

    words = len(text.split())
    return {
        "words": words,
        "code_blocks": code_markers // 2,
        "proposal_phrases": proposal_phrases,
        "action_phrases": action_phrases,
        "verdict": "EXECUTES" if proposal_phrases <= 1 and action_phrases >= 2
                   else "PROPOSES" if proposal_phrases >= 2
                   else "MIXED",
    }


def main():
    parser = argparse.ArgumentParser(description="A/B test: original vs Gemma-tuned context")
    parser.add_argument("--server", default="http://localhost:8080")
    parser.add_argument("--prompt", default=None, help="Custom prompt text (overrides --num)")
    parser.add_argument("--num", type=int, default=None, help="Prompt number 1-10 from <domain>.txt")
    parser.add_argument("--all", action="store_true", help="Run all 10 prompts")
    parser.add_argument("--skip", default=None, help="Comma-separated prompt numbers to skip (e.g. 1,2)")
    parser.add_argument("--only", default=None, help="Run only this variant: bare or gemma")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temp", type=float, default=0.0)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--domain", default="rails-api",
                        help="Domain fixture: rails-api, integration-api, etc.")
    parser.add_argument("--gemma-harness", default=None,
                        help="Path to a generated gemma-harness.md for 3-way comparison")
    args = parser.parse_args()

    fixtures = {
        "bare": SCRIPT_DIR / "fixtures" / args.domain,
        "gemma": SCRIPT_DIR / "fixtures" / f"{args.domain}-gemma",
    }
    prompts_file = SCRIPT_DIR / "prompts" / f"{args.domain}.txt"
    variants = ["bare", "gemma"]

    harness_content = None
    if args.gemma_harness:
        harness_path = Path(args.gemma_harness)
        if not harness_path.exists():
            print(f"ERROR: harness file not found: {harness_path}")
            sys.exit(1)
        harness_text = harness_path.read_text()
        if "---" in harness_text:
            harness_content = harness_text.split("---", 1)[1].strip()
        else:
            harness_content = harness_text
        variants.append("generated")

    if not check_server(args.server):
        print(f"ERROR: llama-server not reachable at {args.server}")
        sys.exit(1)

    model = detect_model(args.server)

    # Build prompt list
    all_prompts = load_prompt_list(prompts_file)
    skip_set = set(int(x) for x in args.skip.split(",")) if args.skip else set()
    if args.all:
        test_prompts = [(i + 1, p["axis"], p["text"]) for i, p in enumerate(all_prompts)
                        if (i + 1) not in skip_set]
    elif args.prompt:
        test_prompts = [(0, "?", args.prompt)]
    elif args.num:
        idx = args.num - 1
        test_prompts = [(args.num, all_prompts[idx]["axis"], all_prompts[idx]["text"])]
    else:
        test_prompts = [(1, all_prompts[0]["axis"], all_prompts[0]["text"])]

    # Filter variants
    run_variants = [args.only] if args.only else variants

    print(f"=== Gemma Eval ===")
    print(f"Model: {model}")
    print(f"Domain: {args.domain}")
    print(f"Variants: {', '.join(run_variants)}")
    print(f"Prompts: {len(test_prompts)} ({'all' if args.all else test_prompts[0][2][:60]})")
    print(f"Temp: {args.temp}, Max tokens: {args.max_tokens}")
    print(f"Runs: {args.runs}")
    print()

    # Build results dir with model + temp to prevent overwriting across runs
    model_short = model.replace(".gguf", "").split("/")[-1]
    temp_label = f"temp{args.temp}".replace(".", "")
    results_dir = SCRIPT_DIR / "results" / f"ab-test-{model_short}-{temp_label}"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Build contexts once — source files are the same across all fixtures
    source_context = build_source_context(fixtures["bare"])

    contexts = {}
    # Bare: source files only, no assembled context
    contexts["bare"] = f"You are reviewing a codebase. Here are the project files:\n\n{source_context}" if source_context else None
    # Gemma: lean harness + source files
    gemma_assembled = build_assembled_context(fixtures["gemma"])
    contexts["gemma"] = f"{gemma_assembled}\n\n---\n\n# Project Files\n\n{source_context}" if gemma_assembled else None

    if "generated" in variants:
        refs_dir = fixtures["bare"] / ".claude" / "references"
        ref_parts = []
        if refs_dir.exists():
            for ref_file in sorted(refs_dir.glob("*.md")):
                ref_parts.append(f"# Reference: {ref_file.name}\n\n{ref_file.read_text()}")
        ref_context = "\n\n---\n\n".join(ref_parts)
        contexts["generated"] = (
            f"# Project Instructions\n\n{harness_content}"
            + (f"\n\n---\n\n{ref_context}" if ref_context else "")
            + f"\n\n---\n\n# Project Files\n\n{source_context}"
        )

    all_results = []

    for prompt_num, axis, prompt_text in test_prompts:
        padded = f"{prompt_num:02d}"
        if len(test_prompts) > 1:
            print(f"{'=' * 60}")
            print(f"PROMPT {padded} (axis {axis}): {prompt_text}")
            print(f"{'=' * 60}\n")

        for run in range(1, args.runs + 1):
            run_label = f" (run {run}/{args.runs})" if args.runs > 1 else ""
            print(f"--- Prompt {padded}{run_label} ---\n")

            for label in run_variants:
                tag = {"bare": "Bare", "gemma": "Gemma-tuned", "generated": "Generated"}[label]
                print(f"  {tag}...", end=" ", flush=True)

                start = time.time()
                response, thinking = generate(
                    args.server, prompt_text,
                    system=contexts[label],
                    max_tokens=args.max_tokens,
                    temp=args.temp,
                )
                elapsed = time.time() - start
                scores = score_output(response, domain=args.domain)

                print(f"{elapsed:.0f}s, {scores['words']}w, "
                      f"think={thinking['reasoning_words']}w ({thinking['think_ratio']}), "
                      f"proposals={scores['proposal_phrases']}, "
                      f"actions={scores['action_phrases']} → {scores['verdict']}")

                result = {
                    "variant": label,
                    "prompt_num": prompt_num,
                    "prompt_axis": axis,
                    "prompt_text": prompt_text,
                    "run": run,
                    "time_s": round(elapsed, 1),
                    "response": response,
                    "thinking": thinking,
                    "scores": scores,
                }
                all_results.append(result)

                # Save individual result
                out_path = results_dir / f"{padded}-{label}-run{run}.json"
                out_path.write_text(json.dumps(result, indent=2))

            print()

    # Print per-prompt comparison
    prompt_nums = sorted(set(r["prompt_num"] for r in all_results))

    print("=" * 60)
    print("COMPARISON")
    print("=" * 60)

    # Per-prompt breakdown
    for pn in prompt_nums:
        prompt_results = [r for r in all_results if r["prompt_num"] == pn]
        axis = prompt_results[0]["prompt_axis"]
        text = prompt_results[0]["prompt_text"]
        print(f"\n  Prompt {pn:02d} (axis {axis}): {text[:50]}")

        for label in run_variants:
            tag = {"bare": "Bare ", "gemma": "Gemma", "generated": "Genrt"}[label]
            runs = [r for r in prompt_results if r["variant"] == label]
            if not runs:
                continue
            verdicts = [r["scores"]["verdict"] for r in runs]
            avg_w = sum(r["scores"]["words"] for r in runs) / len(runs)
            avg_p = sum(r["scores"]["proposal_phrases"] for r in runs) / len(runs)
            avg_a = sum(r["scores"]["action_phrases"] for r in runs) / len(runs)
            print(f"    {tag:5s}: {avg_w:3.0f}w, proposals={avg_p:.0f}, "
                  f"actions={avg_a:.0f} → {', '.join(verdicts)}")

    # Overall summary
    print(f"\n{'=' * 60}")
    print("OVERALL")
    print("=" * 60)

    for label in run_variants:
        tag = {"bare": "Bare", "gemma": "Gemma-tuned", "generated": "Generated"}[label]
        runs = [r for r in all_results if r["variant"] == label]
        verdicts = [r["scores"]["verdict"] for r in runs]
        exec_pct = verdicts.count("EXECUTES") * 100 // len(verdicts) if verdicts else 0
        avg_words = sum(r["scores"]["words"] for r in runs) / len(runs)
        avg_time = sum(r["time_s"] for r in runs) / len(runs)

        print(f"\n  {tag}:")
        print(f"    EXECUTES: {verdicts.count('EXECUTES')}/{len(verdicts)} ({exec_pct}%)")
        print(f"    PROPOSES: {verdicts.count('PROPOSES')}/{len(verdicts)}")
        print(f"    MIXED:    {verdicts.count('MIXED')}/{len(verdicts)}")
        print(f"    Avg words: {avg_words:.0f}, Avg time: {avg_time:.0f}s")

    # Show responses for each prompt (last run only)
    print(f"\n{'=' * 60}")
    print("RESPONSES (last run, truncated to 300 chars)")
    print("=" * 60)

    for pn in prompt_nums:
        text = [r for r in all_results if r["prompt_num"] == pn][0]["prompt_text"]
        print(f"\n  Prompt {pn:02d}: {text[:50]}")
        for label in run_variants:
            tag = {"bare": "Bare ", "gemma": "Gemma", "generated": "Genrt"}[label]
            last = [r for r in all_results
                    if r["prompt_num"] == pn and r["variant"] == label]
            if not last:
                continue
            preview = last[-1]["response"][:300].replace("\n", "\n         ")
            print(f"    {tag}: {preview}")
            if len(last[-1]["response"]) > 300:
                print(f"         ... ({len(last[-1]['response'])} chars)")

    # Save summary
    summary = {
        "model": model,
        "domain": args.domain,
        "prompts": len(test_prompts),
        "temp": args.temp,
        "runs": args.runs,
        "results": [
            {k: v for k, v in r.items() if k != "response"}
            for r in all_results
        ],
    }
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nResults saved to: {results_dir}")


if __name__ == "__main__":
    main()
