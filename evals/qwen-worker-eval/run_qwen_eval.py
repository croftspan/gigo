#!/usr/bin/env python3
"""Qwen worker eval runner.

Iterates tasks x ticket-formats x thinking-modes x replicates. Posts each
assembled ticket to the local OpenAI-compatible endpoint. Saves the raw
JSON response, extracted content, and extracted reasoning per run.

Sampling profile is pinned per task type (Fix 3 in brief 16). Does not sweep it.

Usage:
    run_qwen_eval.py                                    # full sweep (Phase 1 tasks)
    run_qwen_eval.py --tasks T1                         # subset
    run_qwen_eval.py --tasks T1 --formats TF3 --thinks on --reps 1   # dry run
    run_qwen_eval.py --out results/custom-dir
    run_qwen_eval.py --tasks-dir tasks/phase2a --pin-format TF3 \
                     --pin-thinking off --reps 5       # Phase 2A single-cell
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS_DIR = SCRIPT_DIR / "tasks"
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

ALL_FORMATS = ["TF1", "TF2", "TF3"]
ALL_THINKS = ["on", "off"]


def discover_tasks(tasks_dir: Path) -> list[str]:
    """Return task IDs (stems before the first `-`) found in tasks_dir, in a
    stable order. Phase 1 uses T1..T10; Phase 2A uses S1/M*/L*/XL*.
    """
    ids = sorted(
        {path.name.split("-")[0] for path in tasks_dir.glob("*.md")},
        key=_task_sort_key,
    )
    return ids


def _task_sort_key(task_id: str) -> tuple:
    """Sort T1,T2,...T10 numerically; S/M/L/XL grouped then numerically."""
    order = {"S": 0, "M": 1, "L": 2, "XL": 3, "T": 4}
    m = re.match(r"([A-Z]+)(\d+)", task_id)
    if not m:
        return (9, task_id)
    prefix, num = m.group(1), int(m.group(2))
    return (order.get(prefix, 9), num)


def load_task_meta(tasks_dir: Path, task_id: str) -> dict:
    matches = list(tasks_dir.glob(f"{task_id}-*.md"))
    if not matches:
        sys.exit(f"ERROR: no task file matching {task_id} in {tasks_dir}")
    raw = matches[0].read_text()
    end = raw.find("\n---", 3)
    fm = yaml.safe_load(raw[3:end])
    return fm


def resolve_task_path(tasks_dir: Path, task_id: str) -> Path:
    matches = list(tasks_dir.glob(f"{task_id}-*.md"))
    if not matches:
        sys.exit(f"ERROR: no task file matching {task_id} in {tasks_dir}")
    return matches[0]


def build_ticket(fmt: str, task_path: Path) -> str:
    proc = subprocess.run(
        [str(SCRIPT_DIR / "build-ticket.sh"), fmt, str(task_path)],
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
    ap.add_argument(
        "--tasks-dir",
        default=None,
        help="task directory (relative to script or absolute); default = tasks/",
    )
    ap.add_argument(
        "--tasks",
        nargs="+",
        default=None,
        help="task IDs to run; defaults to every task file in --tasks-dir",
    )
    ap.add_argument("--formats", nargs="+", default=ALL_FORMATS)
    ap.add_argument(
        "--pin-format",
        default=None,
        choices=ALL_FORMATS,
        help="shorthand for `--formats TFx` — pin a single format",
    )
    ap.add_argument("--thinks", nargs="+", default=ALL_THINKS, choices=ALL_THINKS)
    ap.add_argument(
        "--pin-thinking",
        default=None,
        choices=ALL_THINKS,
        help="shorthand for `--thinks on|off` — pin a single thinking setting",
    )
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default=None, help="override results dir")
    args = ap.parse_args()

    if args.tasks_dir:
        tasks_dir = Path(args.tasks_dir)
        if not tasks_dir.is_absolute():
            tasks_dir = SCRIPT_DIR / tasks_dir
    else:
        tasks_dir = DEFAULT_TASKS_DIR

    if not tasks_dir.is_dir():
        sys.exit(f"ERROR: tasks dir not found: {tasks_dir}")

    if args.pin_format:
        args.formats = [args.pin_format]
    if args.pin_thinking:
        args.thinks = [args.pin_thinking]

    if args.tasks is None:
        args.tasks = discover_tasks(tasks_dir)
        if not args.tasks:
            sys.exit(f"ERROR: no task files found in {tasks_dir}")

    if args.out:
        out_dir = Path(args.out)
    else:
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        out_dir = SCRIPT_DIR / "results" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    # Preload task metadata + resolved paths
    meta = {t: load_task_meta(tasks_dir, t) for t in args.tasks}
    task_paths = {t: resolve_task_path(tasks_dir, t) for t in args.tasks}

    total = len(args.tasks) * len(args.formats) * len(args.thinks) * args.reps
    idx = 0
    started = time.time()

    manifest_path = out_dir / "manifest.jsonl"
    manifest = manifest_path.open("w")
    print(f"=== Qwen worker eval ===")
    print(f"tasks_dir: {tasks_dir}")
    print(f"out: {out_dir}")
    print(f"runs: {total}")
    print()

    for task_id in args.tasks:
        task_type = meta[task_id]["task_type"]
        for fmt in args.formats:
            ticket = build_ticket(fmt, task_paths[task_id])
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

                    finish_reason = None
                    if resp:
                        choices = resp.get("choices") or [{}]
                        finish_reason = choices[0].get("finish_reason")

                    manifest.write(
                        json.dumps(
                            {
                                "stem": stem,
                                "task": task_id,
                                "task_type": task_type,
                                "size_bucket": meta[task_id].get("size_bucket"),
                                "format": fmt,
                                "thinking": think,
                                "rep": rep,
                                "condition": cond,
                                "error": err,
                                "finish_reason": finish_reason,
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
