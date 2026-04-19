#!/usr/bin/env bash
# Rank-5 judge scorer for the context-dosing sweep.
#
# Per prompt:
#   1. Load all 5 condition results
#   2. Shuffle into Response 1-5 with a recorded mapping
#   3. Call the rank-5 judge (./judge-prompt-rank5.md)
#   4. Unblind using the mapping and store per-prompt score JSON
# Then aggregate Borda points per condition per criterion per domain.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-dosing-eval.sh <results-dir>}"
JUDGE_PROMPT_TEMPLATE="$SCRIPT_DIR/judge-prompt-rank5.md"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR" >&2
  exit 1
fi
if [ ! -f "$JUDGE_PROMPT_TEMPLATE" ]; then
  echo "ERROR: Judge template not found: $JUDGE_PROMPT_TEMPLATE" >&2
  exit 1
fi

DOMAINS=("rails-api" "childrens-novel")
CONDITIONS=("c0-bare" "c1-roster" "c2-team-no-rules" "c3-full" "c4-rules-only")
CRITERIA=(quality_bar persona_voice expertise_routing specificity pushback_quality)

# Shuffle a bash array in place (Fisher-Yates using $RANDOM).
shuffle() {
  local i tmp size max rand
  size=${#arr[@]}
  max=$(( 32768 / size * size ))
  for ((i=size-1; i>0; i--)); do
    while (( (rand=$RANDOM) >= max )); do :; done
    rand=$(( rand % (i+1) ))
    tmp=${arr[i]}
    arr[i]=${arr[rand]}
    arr[rand]=$tmp
  done
}

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$RESULTS_DIR/$domain"
  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "SKIP: No results for $domain" >&2
    continue
  fi

  echo "=== Scoring: $domain ==="

  # Find all prompt indices by looking at c0-bare files
  for c0_file in "$DOMAIN_DIR"/*-c0-bare.json; do
    [ -e "$c0_file" ] || continue
    BASE=$(basename "$c0_file")
    PADDED="${BASE%%-*}"
    SCORE_FILE="$DOMAIN_DIR/${PADDED}-score.json"

    # Skip if already scored
    if [ -f "$SCORE_FILE" ]; then
      echo "  [${PADDED}] already scored, skipping"
      continue
    fi

    # Verify all 5 condition files exist
    MISSING=0
    for condition in "${CONDITIONS[@]}"; do
      f="$DOMAIN_DIR/${PADDED}-${condition}.json"
      if [ ! -s "$f" ]; then
        echo "  [${PADDED}] MISSING $condition, skipping prompt" >&2
        MISSING=1
        break
      fi
    done
    [ "$MISSING" -eq 1 ] && continue

    # Load prompt text + axis from c0-bare (all conditions share this)
    PROMPT_TEXT=$(jq -r '.prompt' "$c0_file")
    AXIS=$(jq -r '.axis' "$c0_file")

    # Shuffle conditions into positions 1-5
    arr=("${CONDITIONS[@]}")
    shuffle
    # arr[0]..arr[4] now the condition for Response 1..5

    # Build the judge prompt in one python call — substitutes PROMPT and all
    # 5 RESPONSE_N placeholders from the shuffled condition order.
    # Args: template_path, prompt_text, then 5 file paths (response 1..5).
    JUDGE_PROMPT=$(python3 - \
      "$JUDGE_PROMPT_TEMPLATE" \
      "$PROMPT_TEXT" \
      "$DOMAIN_DIR/${PADDED}-${arr[0]}.json" \
      "$DOMAIN_DIR/${PADDED}-${arr[1]}.json" \
      "$DOMAIN_DIR/${PADDED}-${arr[2]}.json" \
      "$DOMAIN_DIR/${PADDED}-${arr[3]}.json" \
      "$DOMAIN_DIR/${PADDED}-${arr[4]}.json" <<'PYEOF'
import json, sys
template_path, prompt_text, *resp_paths = sys.argv[1:]
with open(template_path) as f:
    template = f.read()
out = template.replace("{PROMPT}", prompt_text)
for i, p in enumerate(resp_paths, start=1):
    with open(p) as f:
        data = json.load(f)
    resp_text = data.get("response", {}).get("result", "ERROR: missing response")
    out = out.replace(f"{{RESPONSE_{i}}}", resp_text)
sys.stdout.write(out)
PYEOF
    )

    echo "  [${PADDED}] axis=$AXIS — calling judge..."

    JUDGE_OUTPUT=$(claude -p "$JUDGE_PROMPT" --model claude-opus-4-7 --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
    JUDGE_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^```$/d')

    # Record: mapping + raw judge output
    MAPPING_JSON=$(python3 -c 'import json,sys; arr = sys.argv[1:]; print(json.dumps({str(i+1): arr[i] for i in range(len(arr))}))' "${arr[@]}")

    {
      echo "{"
      echo "  \"padded\": \"$PADDED\","
      echo "  \"axis\": \"$AXIS\","
      echo "  \"mapping\": $MAPPING_JSON,"
      echo -n "  \"judge\": "
      # Judge result may or may not be valid JSON — store as raw string if not
      if echo "$JUDGE_RESULT" | jq -e . >/dev/null 2>&1; then
        echo "$JUDGE_RESULT"
      else
        python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<< "$JUDGE_RESULT"
        echo "  ,\"judge_parse_error\": true"
      fi
      echo "}"
    } > "$SCORE_FILE"

    echo "  [${PADDED}] scored."
  done

  echo ""
done

# === Aggregate Borda + score summaries across domains + criteria + axes ===
SUMMARY_FILE="$RESULTS_DIR/summary.md"
AGG_JSON="$RESULTS_DIR/aggregate.json"

python3 - "$RESULTS_DIR" "$SUMMARY_FILE" "$AGG_JSON" <<'PYEOF'
import json, os, sys, glob
from collections import defaultdict

results_dir, summary_path, agg_path = sys.argv[1:4]
DOMAINS = ["rails-api", "childrens-novel"]
CONDITIONS = ["c0-bare", "c1-roster", "c2-team-no-rules", "c3-full", "c4-rules-only"]
CRITERIA = ["quality_bar", "persona_voice", "expertise_routing", "specificity", "pushback_quality"]
BORDA = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# agg[domain][condition][criterion] = {"borda": int, "score_sum": int, "n": int}
# ax_agg[domain][axis][condition] = {"borda_sum": int, "n_criteria": int}
agg = {d: {c: {k: {"borda": 0, "score_sum": 0, "n": 0} for k in CRITERIA} for c in CONDITIONS} for d in DOMAINS}
ax_agg = {d: defaultdict(lambda: {c: {"borda_sum": 0, "n": 0} for c in CONDITIONS}) for d in DOMAINS}
tokens = {}
prompt_count = {d: 0 for d in DOMAINS}
parse_errors = []

for d in DOMAINS:
    ddir = os.path.join(results_dir, d)
    if not os.path.isdir(ddir):
        continue
    tok_path = os.path.join(ddir, "tokens.json")
    if os.path.isfile(tok_path):
        with open(tok_path) as f:
            tokens[d] = json.load(f).get("conditions", {})
    for sf in sorted(glob.glob(os.path.join(ddir, "*-score.json"))):
        with open(sf) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                parse_errors.append(sf)
                continue
        if data.get("judge_parse_error"):
            parse_errors.append(sf)
            continue
        mapping = data["mapping"]  # {"1": "c3-full", ...}
        judge = data["judge"]
        if not isinstance(judge, dict):
            parse_errors.append(sf)
            continue
        prompt_count[d] += 1
        axis = data.get("axis", "?")
        for crit in CRITERIA:
            if crit not in judge:
                continue
            block = judge[crit]
            scores = block.get("scores", {})
            rank = block.get("rank", [])
            # Borda from position in rank array
            for pos, resp_num in enumerate(rank, start=1):
                resp_key = str(resp_num)
                cond = mapping.get(resp_key)
                if not cond or cond not in CONDITIONS:
                    continue
                agg[d][cond][crit]["borda"] += BORDA.get(pos, 0)
                agg[d][cond][crit]["n"] += 1
                ax_agg[d][axis][cond]["borda_sum"] += BORDA.get(pos, 0)
                ax_agg[d][axis][cond]["n"] += 1
            # Raw scores
            for resp_key, s in scores.items():
                cond = mapping.get(str(resp_key))
                if not cond or cond not in CONDITIONS:
                    continue
                try:
                    agg[d][cond][crit]["score_sum"] += int(s)
                except (TypeError, ValueError):
                    pass

# Emit aggregate JSON
out = {
    "tokens": tokens,
    "prompt_count": prompt_count,
    "parse_errors": parse_errors,
    "per_domain": {
        d: {
            "per_condition": {
                c: {
                    "total_borda": sum(agg[d][c][k]["borda"] for k in CRITERIA),
                    "total_score": sum(agg[d][c][k]["score_sum"] for k in CRITERIA),
                    "per_criterion": {k: agg[d][c][k] for k in CRITERIA},
                } for c in CONDITIONS
            },
            "per_axis": {ax: dict(ax_agg[d][ax]) for ax in ax_agg[d]},
        } for d in DOMAINS
    },
}
with open(agg_path, "w") as f:
    json.dump(out, f, indent=2)

# Emit markdown summary
def rank_line(d):
    lines = []
    per_cond = out["per_domain"][d]["per_condition"]
    ordered = sorted(CONDITIONS, key=lambda c: per_cond[c]["total_borda"], reverse=True)
    max_borda = per_cond[ordered[0]]["total_borda"] if per_cond[ordered[0]]["total_borda"] else 1
    for c in ordered:
        pc = per_cond[c]
        tok = tokens.get(d, {}).get(c, "?")
        bar = "█" * int(25 * pc["total_borda"] / max_borda) if max_borda else ""
        lines.append(f"  - **{c}** — Borda {pc['total_borda']}, raw score {pc['total_score']}, ~{tok} words  {bar}")
    return "\n".join(lines)

with open(summary_path, "w") as f:
    f.write(f"# Context-Dosing Sweep — {os.path.basename(results_dir)}\n\n")
    f.write("Rank-of-5 judge, 5 conditions on the context-mass axis. Borda points = 5 for rank 1, 1 for rank 5. Per prompt = 5 criteria × (5+4+3+2+1) = 75 pts distributed.\n\n")
    if parse_errors:
        f.write(f"**Judge parse errors:** {len(parse_errors)} (see aggregate.json for paths)\n\n")
    for d in DOMAINS:
        f.write(f"## {d}\n\n")
        f.write(f"Prompts scored: {prompt_count[d]}\n\n")
        f.write("### Ranking (by total Borda across all 5 criteria)\n\n")
        f.write(rank_line(d) + "\n\n")
        # Per-criterion table
        f.write("### Per-criterion Borda points\n\n")
        f.write("| Condition | " + " | ".join(CRITERIA) + " | total |\n")
        f.write("|" + "---|" * (len(CRITERIA) + 2) + "\n")
        for c in CONDITIONS:
            row = [c]
            for crit in CRITERIA:
                row.append(str(agg[d][c][crit]["borda"]))
            row.append(str(sum(agg[d][c][k]["borda"] for k in CRITERIA)))
            f.write("| " + " | ".join(row) + " |\n")
        f.write("\n")
        # Per-axis table
        axes = sorted(ax_agg[d].keys())
        if axes:
            f.write("### Per-axis Borda (avg per criterion)\n\n")
            f.write("| Axis | " + " | ".join(CONDITIONS) + " |\n")
            f.write("|" + "---|" * (len(CONDITIONS) + 1) + "\n")
            for ax in axes:
                row = [ax]
                for c in CONDITIONS:
                    cell = ax_agg[d][ax][c]
                    avg = cell["borda_sum"] / cell["n"] if cell["n"] else 0
                    row.append(f"{avg:.2f}")
                f.write("| " + " | ".join(row) + " |\n")
            f.write("\n")

print(f"Summary written to {summary_path}")
print(f"Aggregate JSON at {agg_path}")
PYEOF

echo ""
echo "=== Summary ==="
cat "$SUMMARY_FILE"
echo ""
echo "Full results: $RESULTS_DIR"
