#!/usr/bin/env python3
"""Score a Qwen worker eval run.

For each run in results/<stamp>/:
  1. Execute the deterministic verifier on the content.txt. Capture PASS/FAIL + msg.
  2. Assemble the judge prompt with task fields + verifier result + output.
  3. Dispatch `claude -p --model claude-opus-4-7 --output-format json` with the prompt.
  4. Parse the YAML score block. Save as <stem>.score.json.

Aggregate per condition and per task_type. If the manifest records size_bucket
(Phase 2A), also aggregate per bucket. Emit summary.md.

Usage:
    score_qwen_eval.py <results-dir>
    score_qwen_eval.py <results-dir> --only T1 T2              # limit to some tasks
    score_qwen_eval.py <results-dir> --skip-judge              # re-aggregate only
    score_qwen_eval.py <results-dir> --tasks-dir tasks/phase2a \
                                     --verifiers-dir verifiers/phase2a   # Phase 2A
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS_DIR = SCRIPT_DIR / "tasks"
DEFAULT_VERIFIERS_DIR = SCRIPT_DIR / "verifiers"
JUDGE_PROMPT = (SCRIPT_DIR / "judge-prompt.md").read_text()
REVISION_PROMPT_PATH = SCRIPT_DIR / "judge-prompt-revision.md"
REVISION_JUDGE_PROMPT = (
    REVISION_PROMPT_PATH.read_text() if REVISION_PROMPT_PATH.exists() else ""
)

_BUCKET_RANK = {"S": 0, "M": 1, "L": 2, "XL": 3}


def _bucket_order(bucket: str) -> int:
    return _BUCKET_RANK.get(bucket, 9)


def load_task(tasks_dir: Path, task_id: str) -> dict:
    matches = list(tasks_dir.glob(f"{task_id}-*.md"))
    if not matches:
        sys.exit(f"ERROR: no task {task_id} in {tasks_dir}")
    raw = matches[0].read_text()
    end = raw.find("\n---", 3)
    return yaml.safe_load(raw[3:end])


def run_verifier(verifiers_dir: Path, task_id: str, content: str) -> dict:
    verifier = verifiers_dir / f"{task_id}.py"
    if not verifier.exists():
        return {"ran": False, "pass": None, "msg": "no verifier"}
    proc = subprocess.run(
        ["python3", str(verifier)],
        input=content,
        capture_output=True,
        text=True,
    )
    passed = proc.returncode == 0
    msg = (proc.stdout + proc.stderr).strip() or "(no output)"
    return {"ran": True, "pass": passed, "msg": msg[:800]}


def build_judge_prompt(task: dict, verifier_result: dict, output: str) -> str:
    v_text = f"acceptance_pass: {verifier_result['pass']}\nmessage: {verifier_result['msg']}"
    if not verifier_result["ran"]:
        v_text = "(no deterministic verifier for this task — rate on substance)"
    prompt = JUDGE_PROMPT
    prompt = prompt.replace("{TASK_SPEC}", (task.get("spec") or "").strip())
    prompt = prompt.replace("{TASK_ACCEPTANCE}", (task.get("acceptance") or "").strip())
    prompt = prompt.replace("{TASK_OUTPUT_FORMAT}", (task.get("output_format") or "").strip())
    prompt = prompt.replace("{VERIFIER_RESULT}", v_text)
    prompt = prompt.replace("{OUTPUT}", output)
    return prompt


def build_revision_judge_prompt(
    task: dict,
    verifier_result: dict,
    critique: str,
    output: str,
) -> str:
    if not REVISION_JUDGE_PROMPT:
        raise RuntimeError(
            f"revision judge prompt missing: {REVISION_PROMPT_PATH} not found"
        )
    v_text = f"acceptance_pass: {verifier_result['pass']}\nmessage: {verifier_result['msg']}"
    if not verifier_result["ran"]:
        v_text = "(no deterministic verifier for this task — rate on substance)"
    prompt = REVISION_JUDGE_PROMPT
    prompt = prompt.replace("{TASK_SPEC}", (task.get("spec") or "").strip())
    prompt = prompt.replace("{TASK_ACCEPTANCE}", (task.get("acceptance") or "").strip())
    prompt = prompt.replace("{TASK_OUTPUT_FORMAT}", (task.get("output_format") or "").strip())
    prompt = prompt.replace("{REVISION_CRITIQUE}", (critique or "").strip())
    prompt = prompt.replace("{VERIFIER_RESULT}", v_text)
    prompt = prompt.replace("{OUTPUT}", output)
    return prompt


JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "acceptance_pass": {"type": "boolean"},
        "format_adherence": {"type": "boolean"},
        "fabrication_present": {"type": "boolean"},
        "quality": {"type": "integer", "minimum": 1, "maximum": 5},
        "notes": {"type": "string"},
    },
    "required": ["acceptance_pass", "format_adherence", "fabrication_present", "quality", "notes"],
    "additionalProperties": False,
}

REVISION_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "acceptance_pass": {"type": "boolean"},
        "critique_addressed": {"type": "boolean"},
        "format_adherence": {"type": "boolean"},
        "fabrication_present": {"type": "boolean"},
        "quality": {"type": "integer", "minimum": 1, "maximum": 5},
        "notes": {"type": "string"},
    },
    "required": [
        "acceptance_pass",
        "critique_addressed",
        "format_adherence",
        "fabrication_present",
        "quality",
        "notes",
    ],
    "additionalProperties": False,
}


def dispatch_judge(prompt: str, schema: dict | None = None) -> dict:
    """Return parsed score dict, or {'error': msg} on failure.

    Uses --json-schema to force structured JSON output — makes the judge
    robust against session-level settings like the 'explanatory' output
    style that would otherwise prepend insight blocks into the response.
    (Not using --bare because it strips OAuth auth.)

    Pass `schema` to use a custom JSON schema (e.g., REVISION_JUDGE_SCHEMA
    for multi-turn scoring). Defaults to the single-turn JUDGE_SCHEMA.
    """
    if schema is None:
        schema = JUDGE_SCHEMA
    required = set(schema.get("required") or [])
    proc = subprocess.run(
        [
            "claude",
            "-p",
            prompt,
            "--model",
            "claude-opus-4-7",
            "--output-format",
            "json",
            "--permission-mode",
            "bypassPermissions",
            "--json-schema",
            json.dumps(schema),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        return {"error": f"claude exit {proc.returncode}: {proc.stderr[:400]}"}
    try:
        wrapped = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": "wrapper not JSON", "raw": proc.stdout[:500]}

    # With --json-schema, the structured object is in `structured_output`.
    # Fall back to `result` (prose) for legacy compatibility.
    parsed = wrapped.get("structured_output")
    if parsed is None:
        inner = wrapped.get("result", "")
        m = re.search(r"```(?:json|yaml|yml)?\s*\n(.*?)\n```", inner, re.DOTALL)
        body = m.group(1) if m else inner
        body = body.strip()
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            try:
                parsed = yaml.safe_load(body)
            except yaml.YAMLError as e:
                return {"error": f"parse error: {e}", "raw": inner[:500]}

    if not isinstance(parsed, dict):
        return {"error": "judge did not return a mapping", "raw": str(parsed)[:500]}

    missing = required - set(parsed.keys())
    if missing:
        inner_raw = wrapped.get("result", "") if isinstance(wrapped, dict) else ""
        return {"error": f"missing keys {sorted(missing)}", "raw": inner_raw[:500], "parsed": parsed}

    return parsed


def _resolve_reference_task(tasks_dir: Path, fm: dict) -> dict:
    """Merge `reference_task` front-matter underneath current fm (as in
    build_ticket.load_task). Lets Phase 2B tasks inherit Phase 2A spec."""
    ref = fm.get("reference_task")
    if not ref:
        return fm
    # Resolve the ref relative to tasks_dir's parent (so `phase2a/<stem>`
    # works from a phase2b task file).
    ref_path = None
    candidate = (tasks_dir.parent / ref).with_suffix(".md")
    if candidate.exists():
        ref_path = candidate
    else:
        matches = list(tasks_dir.parent.glob(f"**/{Path(ref).name}*.md"))
        if matches:
            ref_path = sorted(matches)[0]
    if not ref_path:
        return fm
    raw = ref_path.read_text()
    end = raw.find("\n---", 3)
    ref_fm = yaml.safe_load(raw[3:end])
    return {**ref_fm, **fm}


def score_run(
    results_dir: Path,
    manifest_record: dict,
    only: set[str] | None,
    skip_judge: bool,
    tasks_dir: Path,
    verifiers_dir: Path,
) -> dict | None:
    stem = manifest_record["stem"]
    task_id = manifest_record["task"]
    if only and task_id not in only:
        return None
    mode = manifest_record.get("mode", "single-turn")
    is_multi = mode == "multi-turn"

    if is_multi:
        content_path = results_dir / f"{stem}.turn2.content.txt"
    else:
        content_path = results_dir / f"{stem}.content.txt"
    content = content_path.read_text()
    score_path = results_dir / f"{stem}.score.json"

    if skip_judge and score_path.exists():
        return json.loads(score_path.read_text())

    # Reuse existing score if the judge call succeeded. Only re-dispatch if
    # the prior score has an error (e.g., parse failures from a prior run).
    if score_path.exists():
        existing = json.loads(score_path.read_text())
        if not existing.get("judge", {}).get("error"):
            return existing

    task = load_task(tasks_dir, task_id)
    if is_multi:
        task = _resolve_reference_task(tasks_dir, task)
    verifier_result = run_verifier(verifiers_dir, task_id, content)

    if skip_judge:
        score = {
            "stem": stem,
            "task": task_id,
            "mode": mode,
            "verifier": verifier_result,
            "judge": {"error": "judge skipped (--skip-judge)"},
        }
        score_path.write_text(json.dumps(score, indent=2))
        return score

    if is_multi:
        critique_path = results_dir / f"{stem}.critique.txt"
        critique = critique_path.read_text() if critique_path.exists() else (
            task.get("revision_critique") or ""
        )
        prompt = build_revision_judge_prompt(task, verifier_result, critique, content)
        judge = dispatch_judge(prompt, schema=REVISION_JUDGE_SCHEMA)
    else:
        prompt = build_judge_prompt(task, verifier_result, content)
        judge = dispatch_judge(prompt, schema=JUDGE_SCHEMA)

    score = {
        "stem": stem,
        "task": task_id,
        "mode": mode,
        "verifier": verifier_result,
        "judge": judge,
    }
    score_path.write_text(json.dumps(score, indent=2))
    return score


def load_manifest(results_dir: Path) -> list[dict]:
    return [json.loads(ln) for ln in (results_dir / "manifest.jsonl").read_text().splitlines() if ln.strip()]


def aggregate(results_dir: Path, scores: dict[str, dict], manifest: list[dict]) -> str:
    """Build summary.md."""
    manifest_by_stem = {m["stem"]: m for m in manifest}
    per_cond = defaultdict(list)
    per_cond_type = defaultdict(list)
    per_task = defaultdict(list)
    per_bucket = defaultdict(list)

    # Detect mode mix — if any run is multi-turn, the summary reports the
    # critique_addressed axis and the combined-pass gate includes it.
    any_multi = any(m.get("mode") == "multi-turn" for m in manifest)

    def cell_pass(score: dict, is_multi: bool) -> bool | None:
        j = score.get("judge") or {}
        if j.get("error"):
            return None
        base = (
            bool(j.get("acceptance_pass"))
            and bool(j.get("format_adherence"))
            and not bool(j.get("fabrication_present"))
        )
        if is_multi:
            return base and bool(j.get("critique_addressed"))
        return base

    rows = []
    for stem, score in scores.items():
        m = manifest_by_stem.get(stem, {})
        j = score.get("judge") or {}
        cond = m.get("condition", "?")
        ttype = m.get("task_type", "?")
        bucket = m.get("size_bucket")
        run_is_multi = m.get("mode") == "multi-turn"
        if run_is_multi:
            t1 = m.get("turn1") or {}
            t2 = m.get("turn2") or {}
            completion_tokens = t2.get("completion_tokens")
            prompt_tokens = t2.get("prompt_tokens")
            reasoning_chars = t2.get("reasoning_chars")
            elapsed_s = (t1.get("elapsed_s") or 0) + (t2.get("elapsed_s") or 0)
            finish_reason = t2.get("finish_reason")
        else:
            completion_tokens = m.get("completion_tokens")
            prompt_tokens = m.get("prompt_tokens")
            reasoning_chars = m.get("reasoning_chars")
            elapsed_s = m.get("elapsed_s")
            finish_reason = m.get("finish_reason")
        rows.append({
            "stem": stem,
            "task": score["task"],
            "cond": cond,
            "task_type": ttype,
            "size_bucket": bucket,
            "rep": m.get("rep"),
            "mode": m.get("mode", "single-turn"),
            "critique_type": m.get("critique_type"),
            "judge_error": j.get("error"),
            "acceptance_pass": j.get("acceptance_pass"),
            "critique_addressed": j.get("critique_addressed"),
            "format_adherence": j.get("format_adherence"),
            "fabrication_present": j.get("fabrication_present"),
            "quality": j.get("quality"),
            "verifier_pass": (score.get("verifier") or {}).get("pass"),
            "verifier_ran": (score.get("verifier") or {}).get("ran"),
            "completion_tokens": completion_tokens,
            "prompt_tokens": prompt_tokens,
            "reasoning_chars": reasoning_chars,
            "elapsed_s": elapsed_s,
            "finish_reason": finish_reason,
        })
        cp = cell_pass(score, run_is_multi)
        if cp is not None:
            per_cond[cond].append((cp, j))
            per_cond_type[(cond, ttype)].append((cp, j))
            per_task[(score["task"], cond)].append((cp, j))
            if bucket:
                per_bucket[(bucket, cond)].append((cp, j))

    def summarize_cells(cells: list[tuple[bool, dict]]) -> dict:
        n = len(cells)
        if n == 0:
            return {
                "n": 0, "pass_rate": None, "mean_quality": None,
                "fab_rate": None, "crit_rate": None,
            }
        passes = sum(1 for cp, _ in cells if cp)
        qs = [j.get("quality") for _, j in cells if isinstance(j.get("quality"), (int, float))]
        fabs = sum(1 for _, j in cells if j.get("fabrication_present"))
        crit_cells = [j for _, j in cells if j.get("critique_addressed") is not None]
        crit_passes = sum(1 for j in crit_cells if j.get("critique_addressed"))
        return {
            "n": n,
            "pass_rate": round(passes / n, 3),
            "mean_quality": round(mean(qs), 2) if qs else None,
            "fab_rate": round(fabs / n, 3),
            "crit_rate": round(crit_passes / len(crit_cells), 3) if crit_cells else None,
        }

    # Derive condition list from the manifest so multi-turn cells
    # (e.g. TF3-thinking-on-preserve-on) show up correctly.
    conds = sorted({m.get("condition", "?") for m in manifest if m.get("condition")})

    # Condition table
    md = ["# Qwen Worker Eval Summary\n"]
    md.append(f"Run: `{results_dir.name}`  ")
    md.append(f"Total runs: {len(rows)}  ")
    judge_errors = sum(1 for r in rows if r["judge_error"])
    md.append(f"Judge errors: {judge_errors}  ")
    if any_multi:
        md.append("Mode: multi-turn (combined pass = acceptance ∧ critique_addressed ∧ format ∧ ¬fab)\n")
    else:
        md.append("Mode: single-turn\n")

    md.append("## Per condition (all tasks)\n")
    if any_multi:
        md.append("| Condition | N | Pass rate | Critique-addressed | Mean quality | Fabrication rate |")
        md.append("|---|---|---|---|---|---|")
        for cond in conds:
            s = summarize_cells(per_cond.get(cond, []))
            md.append(
                f"| {cond} | {s['n']} | {s['pass_rate']} | {s['crit_rate']} "
                f"| {s['mean_quality']} | {s['fab_rate']} |"
            )
    else:
        md.append("| Condition | N | Pass rate | Mean quality | Fabrication rate |")
        md.append("|---|---|---|---|---|")
        for cond in conds:
            s = summarize_cells(per_cond.get(cond, []))
            md.append(f"| {cond} | {s['n']} | {s['pass_rate']} | {s['mean_quality']} | {s['fab_rate']} |")
    md.append("")

    # Condition × task_type table
    md.append("## Per condition × task type\n")
    md.append("| Condition | Task type | N | Pass rate | Mean quality | Fab rate |")
    md.append("|---|---|---|---|---|---|")
    for cond in conds:
        for ttype in ["code", "reasoning", "structured"]:
            s = summarize_cells(per_cond_type.get((cond, ttype), []))
            md.append(f"| {cond} | {ttype} | {s['n']} | {s['pass_rate']} | {s['mean_quality']} | {s['fab_rate']} |")
    md.append("")

    # Revision-specific rollup (multi-turn only)
    if any_multi:
        md.append("## Revision outcomes (multi-turn only)\n")
        md.append("| Condition | Critique type | N | Critique-addressed | Acceptance held | Mean quality |")
        md.append("|---|---|---|---|---|---|")
        by_cond_crit: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in rows:
            if r["mode"] != "multi-turn":
                continue
            key = (r["cond"], r.get("critique_type") or "?")
            by_cond_crit[key].append(r)
        for (cond, ct), bucket_rows in sorted(by_cond_crit.items()):
            n = len(bucket_rows)
            crit_cells = [b for b in bucket_rows if b["critique_addressed"] is not None]
            crit_rate = (
                round(
                    sum(1 for b in crit_cells if b["critique_addressed"]) / len(crit_cells),
                    3,
                )
                if crit_cells else None
            )
            acc_cells = [b for b in bucket_rows if b["acceptance_pass"] is not None]
            acc_rate = (
                round(sum(1 for b in acc_cells if b["acceptance_pass"]) / len(acc_cells), 3)
                if acc_cells else None
            )
            qs = [b["quality"] for b in bucket_rows if isinstance(b["quality"], (int, float))]
            mq = round(mean(qs), 2) if qs else None
            md.append(f"| {cond} | {ct} | {n} | {crit_rate} | {acc_rate} | {mq} |")
        md.append("")

    # Size-bucket roll-up (Phase 2A — only populated when manifest has size_bucket)
    buckets_present = sorted({b for (b, _cond) in per_bucket.keys()}, key=_bucket_order)
    if buckets_present:
        md.append("## Per size bucket × condition (Phase 2A scale trial)\n")
        md.append("| Bucket | Condition | N | Pass rate | Mean quality | Fab rate |")
        md.append("|---|---|---|---|---|---|")
        for bucket in buckets_present:
            for cond in conds:
                cells = per_bucket.get((bucket, cond), [])
                if not cells:
                    continue
                s = summarize_cells(cells)
                md.append(
                    f"| {bucket} | {cond} | {s['n']} | {s['pass_rate']} "
                    f"| {s['mean_quality']} | {s['fab_rate']} |"
                )
        md.append("")

    # Per-task variance
    md.append("## Per-task × condition (variance check)\n")
    md.append("Replicates disagree if pass rate is 0 < x < 1.\n")
    md.append("| Task | Condition | Pass rate | Mean quality | Notes |")
    md.append("|---|---|---|---|---|")
    for (task, cond), cells in sorted(per_task.items()):
        s = summarize_cells(cells)
        flag = ""
        if s["pass_rate"] is not None and 0 < s["pass_rate"] < 1:
            flag = f"**FLAG: {int(s['pass_rate']*s['n'])}/{s['n']} passed**"
        md.append(f"| {task} | {cond} | {s['pass_rate']} | {s['mean_quality']} | {flag} |")
    md.append("")

    # Token accounting
    md.append("## Token accounting (means per condition)\n")
    md.append("| Condition | Mean prompt tokens | Mean completion tokens | Mean reasoning chars | Mean walltime (s) |")
    md.append("|---|---|---|---|---|")
    for cond in conds:
        cond_rows = [r for r in rows if r["cond"] == cond]
        if not cond_rows:
            md.append(f"| {cond} | 0 | 0 | 0 | 0 |")
            continue
        pt = [r["prompt_tokens"] for r in cond_rows if isinstance(r["prompt_tokens"], int)]
        ct = [r["completion_tokens"] for r in cond_rows if isinstance(r["completion_tokens"], int)]
        rc = [r["reasoning_chars"] for r in cond_rows if isinstance(r["reasoning_chars"], int)]
        el = [r["elapsed_s"] for r in cond_rows if isinstance(r["elapsed_s"], (int, float))]
        md.append(
            f"| {cond} | {round(mean(pt),0) if pt else 0:.0f} "
            f"| {round(mean(ct),0) if ct else 0:.0f} "
            f"| {round(mean(rc),0) if rc else 0:.0f} "
            f"| {round(mean(el),1) if el else 0} |"
        )
    md.append("")

    # Fabrication roll-up
    fab_cases = [r for r in rows if r["fabrication_present"]]
    md.append(f"## Fabrication roll-up\n")
    md.append(f"Cases with fabrication_present=true: {len(fab_cases)}\n")
    if fab_cases:
        md.append("| Stem | Task | Condition |")
        md.append("|---|---|---|")
        for r in fab_cases[:30]:
            md.append(f"| {r['stem']} | {r['task']} | {r['cond']} |")
        md.append("")

    # Verifier vs judge acceptance_pass disagreements
    disagreements = [
        r for r in rows
        if r["verifier_ran"] and r["verifier_pass"] is not None
        and r["acceptance_pass"] is not None
        and r["verifier_pass"] != r["acceptance_pass"]
    ]
    md.append(f"## Verifier/judge acceptance_pass disagreements\n")
    md.append(f"{len(disagreements)} runs where the verifier and judge disagreed.\n")
    if disagreements:
        md.append("| Stem | Verifier | Judge |")
        md.append("|---|---|---|")
        for r in disagreements[:30]:
            md.append(f"| {r['stem']} | {r['verifier_pass']} | {r['acceptance_pass']} |")

    return "\n".join(md) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("--only", nargs="+", default=None)
    ap.add_argument("--skip-judge", action="store_true")
    ap.add_argument(
        "--tasks-dir",
        default=None,
        help="task directory (relative to script or absolute); default = tasks/",
    )
    ap.add_argument(
        "--verifiers-dir",
        default=None,
        help="verifier directory (relative to script or absolute); default = verifiers/",
    )
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.is_dir():
        sys.exit(f"ERROR: no such dir: {results_dir}")

    def _resolve(p: str | None, default: Path) -> Path:
        if not p:
            return default
        path = Path(p)
        if not path.is_absolute():
            path = SCRIPT_DIR / path
        if not path.is_dir():
            sys.exit(f"ERROR: dir not found: {path}")
        return path

    tasks_dir = _resolve(args.tasks_dir, DEFAULT_TASKS_DIR)
    verifiers_dir = _resolve(args.verifiers_dir, DEFAULT_VERIFIERS_DIR)

    manifest = load_manifest(results_dir)
    only = set(args.only) if args.only else None

    scores: dict[str, dict] = {}
    total = len(manifest)
    for i, m in enumerate(manifest, 1):
        stem = m["stem"]
        if only and m["task"] not in only:
            continue
        print(f"[{i}/{total}] scoring {stem}")
        s = score_run(
            results_dir,
            m,
            only,
            args.skip_judge,
            tasks_dir,
            verifiers_dir,
        )
        if s is not None:
            scores[stem] = s

    md = aggregate(results_dir, scores, manifest)
    (results_dir / "summary.md").write_text(md)
    print()
    print(f"=== summary ===")
    print(md)
    print(f"Summary written to {results_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
