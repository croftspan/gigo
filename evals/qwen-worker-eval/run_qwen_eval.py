#!/usr/bin/env python3
"""Qwen worker eval runner.

Iterates tasks x ticket-formats x thinking-modes x replicates. Posts each
assembled ticket to the local OpenAI-compatible endpoint. Saves the raw
JSON response, extracted content, and extracted reasoning per run.

Sampling profile is pinned per task type (Fix 3 in brief 16). Does not sweep it.

Usage:
    run_qwen_eval.py                         # full sweep
    run_qwen_eval.py --tasks T1              # subset
    run_qwen_eval.py --tasks T1 --formats TF3 --thinks on --reps 1  # dry run
    run_qwen_eval.py --out results/custom-dir
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
TASKS_DIR = SCRIPT_DIR / "tasks"
ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "unsloth/Qwen3.6-35B-A3B-MLX-8bit"
MAX_TOKENS = 32768
REQUEST_TIMEOUT = 600  # seconds per request; MoE first-token can spike
BETWEEN_CALL_SLEEP = 1.0
RETRY_ON_TIMEOUT = 1

SAMPLING = {
    "code":       {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "presence_penalty": 0.0},
    "reasoning":  {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "presence_penalty": 1.5},
    "structured": {"temperature": 0.7, "top_p": 0.80, "top_k": 20, "presence_penalty": 1.5},
}

ALL_TASKS = [f"T{i}" for i in range(1, 11)]
ALL_FORMATS = ["TF1", "TF2", "TF3"]
ALL_THINKS = ["on", "off"]


def load_task_meta(task_id: str) -> dict:
    matches = list(TASKS_DIR.glob(f"{task_id}-*.md"))
    if not matches:
        sys.exit(f"ERROR: no task file matching {task_id}")
    raw = matches[0].read_text()
    end = raw.find("\n---", 3)
    fm = yaml.safe_load(raw[3:end])
    return fm


def build_ticket(fmt: str, task_id: str) -> str:
    proc = subprocess.run(
        [str(SCRIPT_DIR / "build-ticket.sh"), fmt, task_id],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.rstrip("\n")


def post(payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def call_qwen(ticket: str, task_type: str, thinking_on: bool) -> tuple[dict, str]:
    """Return (raw_response, error_or_empty)."""
    sampling = SAMPLING[task_type]
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": ticket}],
        "max_tokens": MAX_TOKENS,
        "temperature": sampling["temperature"],
        "top_p": sampling["top_p"],
        "top_k": sampling["top_k"],
        "presence_penalty": sampling["presence_penalty"],
        "chat_template_kwargs": {"enable_thinking": thinking_on},
    }
    last_err = ""
    for attempt in range(1 + RETRY_ON_TIMEOUT):
        try:
            return post(payload, REQUEST_TIMEOUT), ""
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < RETRY_ON_TIMEOUT:
                time.sleep(5)
                continue
        except Exception as e:
            return {}, f"{type(e).__name__}: {e}"
    return {}, last_err


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", default=ALL_TASKS)
    ap.add_argument("--formats", nargs="+", default=ALL_FORMATS)
    ap.add_argument("--thinks", nargs="+", default=ALL_THINKS, choices=ALL_THINKS)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default=None, help="override results dir")
    args = ap.parse_args()

    if args.out:
        out_dir = Path(args.out)
    else:
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        out_dir = SCRIPT_DIR / "results" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    # Preload task metadata
    meta = {t: load_task_meta(t) for t in args.tasks}

    total = len(args.tasks) * len(args.formats) * len(args.thinks) * args.reps
    idx = 0
    started = time.time()

    manifest_path = out_dir / "manifest.jsonl"
    manifest = manifest_path.open("w")
    print(f"=== Qwen worker eval ===")
    print(f"out: {out_dir}")
    print(f"runs: {total}")
    print()

    for task_id in args.tasks:
        task_type = meta[task_id]["task_type"]
        for fmt in args.formats:
            ticket = build_ticket(fmt, task_id)
            for think in args.thinks:
                cond = f"{fmt}-thinking-{think}"
                thinking_on = think == "on"
                for rep in range(1, args.reps + 1):
                    idx += 1
                    stem = f"{task_id}--{cond}--r{rep}"
                    elapsed = time.time() - started
                    print(
                        f"[{idx}/{total}] {stem} "
                        f"(task_type={task_type}, elapsed={elapsed:.0f}s)"
                    )
                    t0 = time.time()
                    resp, err = call_qwen(ticket, task_type, thinking_on)
                    dt = time.time() - t0

                    (out_dir / f"{stem}.raw.json").write_text(
                        json.dumps(resp, indent=2) if resp else json.dumps({"error": err})
                    )

                    if resp:
                        msg = resp.get("choices", [{}])[0].get("message", {}) or {}
                        content = msg.get("content") or ""
                        reasoning = msg.get("reasoning") or ""
                        usage = resp.get("usage", {}) or {}
                    else:
                        content = ""
                        reasoning = ""
                        usage = {}

                    (out_dir / f"{stem}.content.txt").write_text(content)
                    (out_dir / f"{stem}.reasoning.txt").write_text(reasoning)

                    manifest.write(
                        json.dumps(
                            {
                                "stem": stem,
                                "task": task_id,
                                "task_type": task_type,
                                "format": fmt,
                                "thinking": think,
                                "rep": rep,
                                "condition": cond,
                                "error": err,
                                "elapsed_s": round(dt, 2),
                                "ticket_chars": len(ticket),
                                "content_chars": len(content),
                                "reasoning_chars": len(reasoning),
                                "prompt_tokens": usage.get("prompt_tokens"),
                                "completion_tokens": usage.get("completion_tokens"),
                                "total_tokens": usage.get("total_tokens"),
                            }
                        )
                        + "\n"
                    )
                    manifest.flush()

                    time.sleep(BETWEEN_CALL_SLEEP)

    manifest.close()
    print()
    print(f"=== DONE ===")
    print(f"elapsed: {time.time() - started:.0f}s")
    print(f"results: {out_dir}")


if __name__ == "__main__":
    main()
