#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./run-review-pipeline-test.sh <results-dir-with-code>}"
RUBRIC_FILE="$SCRIPT_DIR/rubrics/review-pipeline-test.md"
PROMPTS_DIR="$SCRIPT_DIR/prompts"

TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
OUTPUT_DIR="$SCRIPT_DIR/results/$TIMESTAMP"
mkdir -p "$OUTPUT_DIR"

SPEC=$(cat "$PROMPTS_DIR/rails.md")

# Use all 4 code variants from the given results dir
VARIANTS=(bare warstories compressed fixonly)

TEMPLATE=$(cat "$RUBRIC_FILE")

echo "=== Review Pipeline Test ==="
echo "Code from: $RESULTS_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

for variant in "${VARIANTS[@]}"; do
  CODE_FILE="$RESULTS_DIR/rails-api/$variant.json"
  if [ ! -f "$CODE_FILE" ]; then
    echo "SKIP: No $variant result"
    continue
  fi

  CODE=$(jq -r '.result // "ERROR"' "$CODE_FILE")
  mkdir -p "$OUTPUT_DIR/$variant"

  echo "=== $variant ==="

  # --- Review A: Plan-aware (has spec, reviews against requirements) ---
  CONTEXT_A="## Review Context

You have the original task spec. Your job is to check whether the implementation meets ALL requirements. Check for missing features, incorrect behavior, spec deviations, and business rule violations.

## Original Task Spec

$SPEC"

  PROMPT_A="${TEMPLATE//\{CODE\}/$CODE}"
  PROMPT_A="${PROMPT_A//\{REVIEW_CONTEXT\}/$CONTEXT_A}"

  echo "  [plan-aware] Running..."
  (claude -p "$PROMPT_A" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}') \
    > "$OUTPUT_DIR/$variant/plan-aware.json"
  echo "  [plan-aware] Done."

  # --- Review B: Code-quality (no spec, reviews code on its own merits) ---
  CONTEXT_B="## Review Context

You are reviewing this Rails API code with NO knowledge of the original requirements. Review it purely on engineering merit: bugs, race conditions, security, performance, maintainability, test quality, API design."

  PROMPT_B="${TEMPLATE//\{CODE\}/$CODE}"
  PROMPT_B="${PROMPT_B//\{REVIEW_CONTEXT\}/$CONTEXT_B}"

  echo "  [code-quality] Running..."
  (claude -p "$PROMPT_B" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}') \
    > "$OUTPUT_DIR/$variant/code-quality.json"
  echo "  [code-quality] Done."

  # --- Review C: Combined (has spec + code quality review) ---
  CONTEXT_C="## Review Context

You have the original task spec AND you should review for engineering quality. Check BOTH:
1. Does the implementation meet all spec requirements? Missing features, incorrect behavior, business rule violations?
2. Is the code well-engineered? Bugs, race conditions, performance, maintainability, test quality?

## Original Task Spec

$SPEC"

  PROMPT_C="${TEMPLATE//\{CODE\}/$CODE}"
  PROMPT_C="${PROMPT_C//\{REVIEW_CONTEXT\}/$CONTEXT_C}"

  echo "  [combined] Running..."
  (claude -p "$PROMPT_C" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}') \
    > "$OUTPUT_DIR/$variant/combined.json"
  echo "  [combined] Done."
  echo ""
done

# --- Build summary ---
SUMMARY_FILE="$OUTPUT_DIR/summary.md"

{
  echo "# Review Pipeline Test Results"
  echo ""
  echo "Run: $TIMESTAMP"
  echo "Code from: $(basename "$RESULTS_DIR")"
  echo ""
  echo "Three review approaches per code variant:"
  echo "- **plan-aware** — has the task spec, checks requirements compliance"
  echo "- **code-quality** — no spec, checks engineering merit only"
  echo "- **combined** — has spec + checks engineering merit"
  echo ""
} > "$SUMMARY_FILE"

for variant in "${VARIANTS[@]}"; do
  {
    echo "## $variant"
    echo ""
  } >> "$SUMMARY_FILE"

  for review in plan-aware code-quality combined; do
    REVIEW_FILE="$OUTPUT_DIR/$variant/$review.json"
    if [ ! -f "$REVIEW_FILE" ]; then
      echo "### $review: MISSING" >> "$SUMMARY_FILE"
      continue
    fi

    RAW=$(jq -r '.result // "ERROR"' "$REVIEW_FILE")

    # Try to extract JSON
    REVIEW_JSON=""
    FENCED=$(echo "$RAW" | sed -n '/^```json$/,/^```$/p' | sed '1d;$d')
    if [ -n "$FENCED" ] && echo "$FENCED" | jq -e '.issues' >/dev/null 2>&1; then
      REVIEW_JSON="$FENCED"
    fi
    if [ -z "$REVIEW_JSON" ] && echo "$RAW" | jq -e '.issues' >/dev/null 2>&1; then
      REVIEW_JSON="$RAW"
    fi
    if [ -z "$REVIEW_JSON" ]; then
      # Try to find JSON starting with {"issues"
      FROM_JSON=$(echo "$RAW" | sed -n '/^{"issues"/,$p' | head -1)
      if [ -n "$FROM_JSON" ] && echo "$FROM_JSON" | jq -e '.issues' >/dev/null 2>&1; then
        REVIEW_JSON="$FROM_JSON"
      fi
    fi

    if [ -z "$REVIEW_JSON" ]; then
      {
        echo "### $review: PARSE ERROR"
        echo ""
        echo "Raw output (first 500 chars):"
        echo '```'
        echo "$RAW" | head -c 500
        echo '```'
        echo ""
      } >> "$SUMMARY_FILE"
      continue
    fi

    CRIT=$(echo "$REVIEW_JSON" | jq -r '.total_critical // 0')
    IMP=$(echo "$REVIEW_JSON" | jq -r '.total_important // 0')
    MIN=$(echo "$REVIEW_JSON" | jq -r '.total_minor // 0')
    TOTAL=$(echo "$REVIEW_JSON" | jq '.issues | length')

    {
      echo "### $review: $TOTAL issues ($CRIT critical, $IMP important, $MIN minor)"
      echo ""
      echo "| Severity | What | Where | Why |"
      echo "|---|---|---|---|"

      echo "$REVIEW_JSON" | jq -r '.issues[] | "| \(.severity) | \(.what) | \(.where) | \(.why) |"'

      echo ""
    } >> "$SUMMARY_FILE"
  done
done

echo "=== Done ==="
echo "Summary: $SUMMARY_FILE"
cat "$SUMMARY_FILE"
