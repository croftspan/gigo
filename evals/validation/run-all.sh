#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$EVALS_DIR/results/validation-$TIMESTAMP"

mkdir -p "$RESULTS_DIR"

echo "=== Feature Validation Suite ==="
echo "Results: $RESULTS_DIR"
echo ""

TESTS_PASSED=0
TESTS_TOTAL=5
RESULTS=()

# Test 1: Boundary-Mismatch Detection
echo "--- Test 1/5: Boundary-Mismatch Detection ---"
echo ""
if "$SCRIPT_DIR/run-boundary-test.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
BM_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/boundary-test.json" 2>/dev/null || echo "ERROR")
BM_SCORE=$(jq -r '"\(.detected)/\(.total)"' "$RESULTS_DIR/boundary-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("1. Boundary-Mismatch Detection:    $BM_SCORE detected   [$BM_RESULT ≥4]")
echo ""

# Test 2: Phase Selection Matrix
echo "--- Test 2/5: Phase Selection Matrix ---"
echo ""
if "$SCRIPT_DIR/run-matrix-test.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
MX_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/matrix-test.json" 2>/dev/null || echo "ERROR")
MX_SCORE=$(jq -r '"\(.identified)/\(.total)"' "$RESULTS_DIR/matrix-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("2. Phase Selection Matrix:         $MX_SCORE effects     [$MX_RESULT ≥3]")
echo ""

# Test 3: Execution Pattern Catalog
echo "--- Test 3/5: Execution Pattern Catalog ---"
echo ""
if "$SCRIPT_DIR/run-pattern-test.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
PT_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/pattern-test.json" 2>/dev/null || echo "ERROR")
PT_SCORE=$(jq -r '"\(.correct)/\(.total)"' "$RESULTS_DIR/pattern-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("3. Execution Pattern Catalog:      $PT_SCORE patterns    [$PT_RESULT 3/3]")
echo ""

# Test 4: Agent Teams Cleanup
echo "--- Test 4/5: Agent Teams Cleanup ---"
echo ""
if "$SCRIPT_DIR/run-cleanup-verify.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
CL_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/cleanup-test.json" 2>/dev/null || echo "ERROR")
CL_SCORE=$(jq -r '"\(.passed)/\(.total)"' "$RESULTS_DIR/cleanup-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("4. Agent Teams Cleanup:            $CL_SCORE checks      [$CL_RESULT 5/5]")
echo ""

# Test 5: Regression (assembled vs bare)
echo "--- Test 5/5: Regression Check ---"
echo ""
REGRESSION_DIR="$RESULTS_DIR/regression"
mkdir -p "$REGRESSION_DIR"

if "$EVALS_DIR/run-eval.sh" 2>&1; then
  LATEST_EVAL=$(ls -td "$EVALS_DIR/results/"* 2>/dev/null | grep -v validation | head -1)
  if [ -n "$LATEST_EVAL" ] && [ -d "$LATEST_EVAL" ]; then
    "$EVALS_DIR/score-eval.sh" "$LATEST_EVAL" 2>&1
    cp "$LATEST_EVAL/summary.md" "$REGRESSION_DIR/" 2>/dev/null || true

    WIN_PCT=$(grep -oE '[0-9]+%' "$LATEST_EVAL/summary.md" 2>/dev/null | tail -1 | tr -d '%' || echo 0)
    if [ "$WIN_PCT" -ge 90 ]; then
      TESTS_PASSED=$((TESTS_PASSED + 1))
      RG_RESULT="PASS"
    else
      RG_RESULT="FAIL"
    fi
    RESULTS+=("5. Regression (assembled vs bare): ${WIN_PCT}% wins        [$RG_RESULT ≥90%]")
  else
    RESULTS+=("5. Regression (assembled vs bare): ?% wins         [ERROR]")
  fi
else
  RESULTS+=("5. Regression (assembled vs bare): ?% wins         [ERROR]")
fi
echo ""

# Summary
echo "==========================================="
echo "=== Feature Validation Suite — Summary ==="
echo "==========================================="
echo ""

for line in "${RESULTS[@]}"; do
  echo "$line"
done

echo ""
echo "Overall: $TESTS_PASSED/$TESTS_TOTAL PASS"
echo ""
echo "Results saved to: $RESULTS_DIR"

# Save summary
{
  echo "# Feature Validation Suite Results"
  echo ""
  echo "Run: $TIMESTAMP"
  echo ""
  for line in "${RESULTS[@]}"; do
    echo "$line"
  done
  echo ""
  echo "Overall: $TESTS_PASSED/$TESTS_TOTAL PASS"
} > "$RESULTS_DIR/summary.md"

[ "$TESTS_PASSED" -eq "$TESTS_TOTAL" ] && exit 0 || exit 1
