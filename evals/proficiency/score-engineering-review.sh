#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-engineering-review.sh <results-dir>}"
RUBRIC_FILE="$SCRIPT_DIR/rubrics/rails-engineering-review.md"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR"
  exit 1
fi

VARIANTS=(bare warstories compressed fixonly)

# Randomize order
SHUFFLED=($(echo "${VARIANTS[@]}" | tr ' ' '\n' | sort -R))

echo "=== Engineering Review ==="
echo "Run: $(basename "$RESULTS_DIR")"
echo ""
echo "Label mapping (hidden from judge):"
echo "  A = ${SHUFFLED[0]}"
echo "  B = ${SHUFFLED[1]}"
echo "  C = ${SHUFFLED[2]}"
echo "  D = ${SHUFFLED[3]}"
echo ""

# Build prompt
TEMPLATE=$(cat "$RUBRIC_FILE")

for i in 0 1 2 3; do
  LABEL=$(echo "ABCD" | cut -c$((i + 1)))
  VARIANT="${SHUFFLED[$i]}"
  FILE="$RESULTS_DIR/rails-api/$VARIANT.json"
  if [ ! -f "$FILE" ]; then
    echo "ERROR: Missing $VARIANT result"
    exit 1
  fi
  CODE=$(jq -r '.result // "ERROR"' "$FILE")
  TEMPLATE="${TEMPLATE//\{CODE_${LABEL}\}/$CODE}"
done

echo "Sending to judge..."
JUDGE_OUTPUT=$(claude -p "$TEMPLATE" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
RAW_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"')

# Save raw result
echo "$RAW_RESULT" > "$RESULTS_DIR/engineering-review-raw.md"

# Try to extract JSON
JUDGE_JSON=""

# Try code fence
FENCED=$(echo "$RAW_RESULT" | sed -n '/^```json$/,/^```$/p' | sed '1d;$d')
if [ -n "$FENCED" ] && echo "$FENCED" | jq -e '.A' >/dev/null 2>&1; then
  JUDGE_JSON="$FENCED"
fi

# Try finding JSON start
if [ -z "$JUDGE_JSON" ]; then
  FROM_JSON=$(echo "$RAW_RESULT" | sed -n '/^{$/,$p')
  if [ -n "$FROM_JSON" ] && echo "$FROM_JSON" | jq -e '.A' >/dev/null 2>&1; then
    JUDGE_JSON="$FROM_JSON"
  fi
fi

# Try whole thing
if [ -z "$JUDGE_JSON" ] && echo "$RAW_RESULT" | jq -e '.A' >/dev/null 2>&1; then
  JUDGE_JSON="$RAW_RESULT"
fi

if [ -z "$JUDGE_JSON" ]; then
  echo "WARNING: Could not parse JSON from judge output."
  echo "Raw output saved to: $RESULTS_DIR/engineering-review-raw.md"
  echo ""
  echo "=== Raw Judge Output ==="
  echo "$RAW_RESULT"
  exit 0
fi

# Build summary
SUMMARY_FILE="$RESULTS_DIR/engineering-review.md"
DIMENSIONS=(concurrency data_layer maintainability test_quality api_design production_readiness)

{
  echo "# Engineering Review — War Story Format Experiment"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo ""
  echo "## Results by Variant"
  echo ""

  for i in 0 1 2 3; do
    LABEL=$(echo "ABCD" | cut -c$((i + 1)))
    VARIANT="${SHUFFLED[$i]}"

    PR_VERDICT=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.pr_verdict // \"unknown\"")
    ENGINEER_LEVEL=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.engineer_level // \"unknown\"")

    echo "### $VARIANT (was label $LABEL)"
    echo ""
    echo "**PR verdict:** $PR_VERDICT | **Engineer level:** $ENGINEER_LEVEL"
    echo ""
    echo "| Dimension | Grade | Reasoning |"
    echo "|---|---|---|"

    for dim in "${DIMENSIONS[@]}"; do
      GRADE=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.${dim}.grade // \"?\"")
      REASONING=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.${dim}.reasoning // \"N/A\"")
      echo "| $dim | $GRADE | $REASONING |"
    done
    echo ""
  done

  # Comparison table
  echo "## Comparison"
  echo ""
  echo "| Variant | Concurrency | Data Layer | Maintainability | Tests | API | Prod Ready | PR Verdict | Level |"
  echo "|---|---|---|---|---|---|---|---|---|"

  for i in 0 1 2 3; do
    LABEL=$(echo "ABCD" | cut -c$((i + 1)))
    VARIANT="${SHUFFLED[$i]}"

    GRADES=""
    for dim in "${DIMENSIONS[@]}"; do
      G=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.${dim}.grade // \"?\"")
      GRADES+="$G | "
    done

    PR=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.pr_verdict // \"?\"")
    LVL=$(echo "$JUDGE_JSON" | jq -r ".${LABEL}.engineer_level // \"?\"")

    echo "| $VARIANT | ${GRADES}$PR | $LVL |"
  done

  echo ""
} > "$SUMMARY_FILE"

echo ""
cat "$SUMMARY_FILE"
echo ""
echo "Full results: $SUMMARY_FILE"
echo "Raw judge output: $RESULTS_DIR/engineering-review-raw.md"
