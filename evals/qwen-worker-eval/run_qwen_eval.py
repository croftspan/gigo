#!/usr/bin/env python3
"""Qwen worker eval runner.

Iterates tasks x ticket-formats x thinking-modes x replicates. Posts each
assembled ticket to the local OpenAI-compatible endpoint. Saves the raw
JSON response, extracted content, and extracted reasoning per run.

Sampling profile is pinned per task type (Fix 3 in brief 16). Does not sweep it.

Two modes:
- single-turn (default): post the ticket, save response. Matches Phase 1/2A.
- multi-turn: post the ticket (turn 1), then post the turn-1 response back
  as an `assistant` message followed by the critique as a second `user` turn.
  `chat_template_kwargs.preserve_thinking` controls whether the prior
  `<think>` block is rendered into the turn-2 prompt (requires the
  assistant message to carry a `reasoning` field, populated from turn 1).

Usage:
    run_qwen_eval.py                                    # full sweep (Phase 1 tasks)
    run_qwen_eval.py --tasks T1                         # subset
    run_qwen_eval.py --tasks T1 --formats TF3 --thinks on --reps 1   # dry run
    run_qwen_eval.py --out results/custom-dir
    run_qwen_eval.py --tasks-dir tasks/phase2a --pin-format TF3 \
                     --pin-thinking off --reps 5       # Phase 2A single-cell
    run_qwen_eval.py --mode multi-turn --tasks-dir tasks/phase2b \
                     --pin-format TF3 --pin-thinking off --reps 5  # Phase 2B T-off cell
    run_qwen_eval.py --mode multi-turn --tasks-dir tasks/phase2b \
                     --pin-format TF3 --pin-thinking on \
                     --pin-preserve on --reps 5          # Phase 2B T-on-preserve cell
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_critique import build_critique  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS_DIR = SCRIPT_DIR / "tasks"
DEFAULT_ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"
DEFAULT_MODEL = "unsloth/Qwen3.6-35B-A3B-MLX-8bit"
ENDPOINT = os.environ.get("QWEN_ENDPOINT", DEFAULT_ENDPOINT)
MODEL = os.environ.get("QWEN_MODEL", DEFAULT_MODEL)
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
ALL_PRESERVES = ["on", "off"]
ALL_MODES = ["single-turn", "multi-turn"]


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


def _post_with_retry(payload: dict) -> tuple[dict, str]:
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


def _base_payload(task_type: str, messages: list[dict], template_kwargs: dict) -> dict:
    sampling = SAMPLING[task_type]
    return {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": sampling["temperature"],
        "top_p": sampling["top_p"],
        "top_k": sampling["top_k"],
        "presence_penalty": sampling["presence_penalty"],
        "chat_template_kwargs": template_kwargs,
    }


def call_qwen(ticket: str, task_type: str, thinking_on: bool) -> tuple[dict, str]:
    """Single-turn call. Return (raw_response, error_or_empty)."""
    payload = _base_payload(
        task_type,
        messages=[{"role": "user", "content": ticket}],
        template_kwargs={"enable_thinking": thinking_on},
    )
    return _post_with_retry(payload)


def call_qwen_turn2(
    ticket: str,
    turn1_content: str,
    turn1_reasoning: str,
    critique: str,
    task_type: str,
    thinking_on: bool,
    preserve_thinking: bool,
) -> tuple[dict, str]:
    """Turn-2 call with prior-assistant message and critique. Return (raw, err).

    If `thinking_on` is True, the assistant message carries the `reasoning`
    field so the server's chat template can consult it. `preserve_thinking`
    controls whether the template renders the prior `<think>` block into the
    turn-2 prompt (True) or strips it (False).

    If `thinking_on` is False, no reasoning is present and preserve_thinking
    is omitted from the template kwargs.
    """
    assistant_msg: dict = {"role": "assistant", "content": turn1_content}
    if thinking_on and turn1_reasoning:
        assistant_msg["reasoning"] = turn1_reasoning
    messages = [
        {"role": "user", "content": ticket},
        assistant_msg,
        {"role": "user", "content": critique},
    ]
    template_kwargs: dict = {"enable_thinking": thinking_on}
    if thinking_on:
        template_kwargs["preserve_thinking"] = preserve_thinking
    payload = _base_payload(task_type, messages, template_kwargs)
    return _post_with_retry(payload)


def _extract(resp: dict) -> tuple[str, str, dict, str | None]:
    """Return (content, reasoning, usage, finish_reason)."""
    if not resp:
        return "", "", {}, None
    choices = resp.get("choices") or [{}]
    msg = choices[0].get("message", {}) or {}
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning") or ""
    usage = resp.get("usage", {}) or {}
    finish_reason = choices[0].get("finish_reason")
    return content, reasoning, usage, finish_reason


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
    ap.add_argument(
        "--mode",
        default="single-turn",
        choices=ALL_MODES,
        help="single-turn: one call per run. multi-turn: two calls with critique between.",
    )
    ap.add_argument(
        "--preserves",
        nargs="+",
        default=ALL_PRESERVES,
        choices=ALL_PRESERVES,
        help="(multi-turn only) preserve_thinking values to iterate over when thinking=on",
    )
    ap.add_argument(
        "--pin-preserve",
        default=None,
        choices=ALL_PRESERVES,
        help="shorthand for `--preserves on|off` — pin a single preserve_thinking setting",
    )
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", default=None, help="override results dir")
    ap.add_argument(
        "--endpoint",
        default=None,
        help="OpenAI-compatible chat completions URL; env QWEN_ENDPOINT also honored",
    )
    ap.add_argument(
        "--model",
        default=None,
        help="model identifier sent to the endpoint; env QWEN_MODEL also honored",
    )
    args = ap.parse_args()

    global ENDPOINT, MODEL
    if args.endpoint:
        ENDPOINT = args.endpoint
    if args.model:
        MODEL = args.model

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
    if args.pin_preserve:
        args.preserves = [args.pin_preserve]

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

    # Enumerate (thinking, preserve) cells up front. In single-turn mode,
    # preserve is not a dimension. In multi-turn mode, preserve is only
    # meaningful when thinking=on; when thinking=off, we fold to a single
    # preserve="na" cell so we don't double-run T-off.
    cells: list[tuple[str, str]] = []
    for think in args.thinks:
        if args.mode == "single-turn":
            cells.append((think, "na"))
        elif think == "off":
            cells.append((think, "na"))
        else:
            for pre in args.preserves:
                cells.append((think, pre))

    total = len(args.tasks) * len(args.formats) * len(cells) * args.reps
    idx = 0
    started = time.time()

    # Preload critiques for multi-turn mode.
    critiques: dict[str, str] = {}
    if args.mode == "multi-turn":
        for task_id in args.tasks:
            critiques[task_id] = build_critique(str(task_paths[task_id]))

    manifest_path = out_dir / "manifest.jsonl"
    manifest = manifest_path.open("w")
    print(f"=== Qwen worker eval ===")
    print(f"mode: {args.mode}")
    print(f"tasks_dir: {tasks_dir}")
    print(f"out: {out_dir}")
    print(f"runs: {total}")
    print()

    for task_id in args.tasks:
        task_type = meta[task_id]["task_type"]
        for fmt in args.formats:
            ticket = build_ticket(fmt, task_paths[task_id])
            for think, pre in cells:
                thinking_on = think == "on"
                if args.mode == "single-turn":
                    cond = f"{fmt}-thinking-{think}"
                else:
                    cond = f"{fmt}-thinking-{think}-preserve-{pre}"
                for rep in range(1, args.reps + 1):
                    idx += 1
                    stem = f"{task_id}--{cond}--r{rep}"
                    elapsed = time.time() - started
                    print(
                        f"[{idx}/{total}] {stem} "
                        f"(task_type={task_type}, elapsed={elapsed:.0f}s)"
                    )

                    # --- Turn 1 ---
                    t0 = time.time()
                    resp1, err1 = call_qwen(ticket, task_type, thinking_on)
                    dt1 = time.time() - t0
                    c1, r1, u1, fin1 = _extract(resp1)

                    if args.mode == "single-turn":
                        # Preserve original artifact naming for back-compat.
                        (out_dir / f"{stem}.raw.json").write_text(
                            json.dumps(resp1, indent=2) if resp1 else json.dumps({"error": err1})
                        )
                        (out_dir / f"{stem}.content.txt").write_text(c1)
                        (out_dir / f"{stem}.reasoning.txt").write_text(r1)
                        record = {
                            "stem": stem,
                            "task": task_id,
                            "task_type": task_type,
                            "size_bucket": meta[task_id].get("size_bucket"),
                            "format": fmt,
                            "thinking": think,
                            "rep": rep,
                            "condition": cond,
                            "mode": args.mode,
                            "error": err1,
                            "finish_reason": fin1,
                            "elapsed_s": round(dt1, 2),
                            "ticket_chars": len(ticket),
                            "content_chars": len(c1),
                            "reasoning_chars": len(r1),
                            "prompt_tokens": u1.get("prompt_tokens"),
                            "completion_tokens": u1.get("completion_tokens"),
                            "total_tokens": u1.get("total_tokens"),
                        }
                    else:
                        # multi-turn: save turn-1 under .turn1.* names.
                        (out_dir / f"{stem}.turn1.raw.json").write_text(
                            json.dumps(resp1, indent=2) if resp1 else json.dumps({"error": err1})
                        )
                        (out_dir / f"{stem}.turn1.content.txt").write_text(c1)
                        (out_dir / f"{stem}.turn1.reasoning.txt").write_text(r1)

                        # --- Turn 2 ---
                        preserve_thinking = pre == "on"
                        critique = critiques[task_id]
                        t0 = time.time()
                        resp2, err2 = call_qwen_turn2(
                            ticket=ticket,
                            turn1_content=c1,
                            turn1_reasoning=r1,
                            critique=critique,
                            task_type=task_type,
                            thinking_on=thinking_on,
                            preserve_thinking=preserve_thinking,
                        )
                        dt2 = time.time() - t0
                        c2, r2, u2, fin2 = _extract(resp2)

                        (out_dir / f"{stem}.turn2.raw.json").write_text(
                            json.dumps(resp2, indent=2) if resp2 else json.dumps({"error": err2})
                        )
                        (out_dir / f"{stem}.turn2.content.txt").write_text(c2)
                        (out_dir / f"{stem}.turn2.reasoning.txt").write_text(r2)
                        (out_dir / f"{stem}.critique.txt").write_text(critique)

                        record = {
                            "stem": stem,
                            "task": task_id,
                            "task_type": task_type,
                            "size_bucket": meta[task_id].get("size_bucket"),
                            "format": fmt,
                            "thinking": think,
                            "preserve_thinking": pre,
                            "rep": rep,
                            "condition": cond,
                            "mode": args.mode,
                            "critique_type": meta[task_id].get("critique_type"),
                            "turn1": {
                                "error": err1,
                                "finish_reason": fin1,
                                "elapsed_s": round(dt1, 2),
                                "content_chars": len(c1),
                                "reasoning_chars": len(r1),
                                "prompt_tokens": u1.get("prompt_tokens"),
                                "completion_tokens": u1.get("completion_tokens"),
                                "total_tokens": u1.get("total_tokens"),
                            },
                            "turn2": {
                                "error": err2,
                                "finish_reason": fin2,
                                "elapsed_s": round(dt2, 2),
                                "content_chars": len(c2),
                                "reasoning_chars": len(r2),
                                "prompt_tokens": u2.get("prompt_tokens"),
                                "completion_tokens": u2.get("completion_tokens"),
                                "total_tokens": u2.get("total_tokens"),
                            },
                            "ticket_chars": len(ticket),
                            "critique_chars": len(critique),
                        }

                    manifest.write(json.dumps(record) + "\n")
                    manifest.flush()

                    time.sleep(BETWEEN_CALL_SLEEP)

    manifest.close()
    print()
    print(f"=== DONE ===")
    print(f"elapsed: {time.time() - started:.0f}s")
    print(f"results: {out_dir}")


if __name__ == "__main__":
    main()
