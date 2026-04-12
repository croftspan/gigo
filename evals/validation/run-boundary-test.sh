#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$EVALS_DIR/fixtures/integration-api"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"
JUDGE_PROMPT="$SCRIPT_DIR/boundary-judge.md"
RUBRIC="$SCRIPT_DIR/boundary-mismatch-rubric.md"

mkdir -p "$RESULTS_DIR"

echo "=== Boundary-Mismatch Detection Test ==="
echo ""

# Copy fixture to temp dir, excluding DEFECT-MANIFEST.md
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

rsync -a --exclude='DEFECT-MANIFEST.md' "$FIXTURE_DIR/" "$TMPDIR/"

AUDIT_PROMPT='Review this codebase for integration issues. Examine how data flows between layers — API routes, frontend hooks, type definitions, navigation, state management. For each issue, identify: the files involved, the specific mismatch, and why it would fail at runtime despite passing TypeScript compilation. Focus on cross-boundary coherence, not single-file code quality.'

echo "Running audit..."
AUDIT_OUTPUT=$(cd "$TMPDIR" && claude -p "$AUDIT_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Claude invocation failed"
  echo '{ "status": "ERROR", "reason": "Claude invocation failed" }' > "$RESULTS_DIR/boundary-test.json"
  exit 1
}

AUDIT_TEXT=$(echo "$AUDIT_OUTPUT" | jq -r '.result // "ERROR: no result"')
echo "$AUDIT_OUTPUT" > "$RESULTS_DIR/boundary-audit-raw.json"

echo "Running judge..."
DEFECT_MANIFEST=$(cat "$FIXTURE_DIR/DEFECT-MANIFEST.md")
RUBRIC_TEXT=$(cat "$RUBRIC")
JUDGE_TEMPLATE=$(cat "$JUDGE_PROMPT")
JUDGE_INPUT="${JUDGE_TEMPLATE//\{AUDIT_OUTPUT\}/$AUDIT_TEXT}"
JUDGE_INPUT="${JUDGE_INPUT//\{DEFECT_MANIFEST\}/$RUBRIC_TEXT}"

JUDGE_OUTPUT=$(claude -p "$JUDGE_INPUT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Judge invocation failed"
  echo '{ "status": "ERROR", "reason": "Judge invocation failed" }' > "$RESULTS_DIR/boundary-test.json"
  exit 1
}

JUDGE_TEXT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')
echo "$JUDGE_TEXT" > "$RESULTS_DIR/boundary-judge-raw.json"

DETECTED=$(echo "$JUDGE_TEXT" | jq '[.[] | select(.detected == true)] | length' 2>/dev/null || echo 0)
TOTAL=6
THRESHOLD=4

echo ""
echo "Per-bug results:"
for i in $(seq 0 5); do
  DEFECT=$(echo "$JUDGE_TEXT" | jq -r ".[$i].defect // \"BM-$((i+1))\"" 2>/dev/null)
  STATUS=$(echo "$JUDGE_TEXT" | jq -r ".[$i].detected // false" 2>/dev/null)
  if [ "$STATUS" = "true" ]; then
    echo "  $DEFECT: DETECTED"
  else
    echo "  $DEFECT: MISSED"
  fi
done

echo ""
if [ "$DETECTED" -ge "$THRESHOLD" ]; then
  echo "Boundary-Mismatch Detection: $DETECTED/$TOTAL detected   [PASS ≥$THRESHOLD]"
  RESULT="PASS"
else
  echo "Boundary-Mismatch Detection: $DETECTED/$TOTAL detected   [FAIL ≥$THRESHOLD]"
  RESULT="FAIL"
fi

echo "{\"test\": \"boundary-mismatch\", \"detected\": $DETECTED, \"total\": $TOTAL, \"threshold\": $THRESHOLD, \"result\": \"$RESULT\"}" > "$RESULTS_DIR/boundary-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
