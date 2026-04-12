#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$EVALS_DIR/fixtures/rails-api"
PROMPTS_FILE="$EVALS_DIR/prompts/execution-patterns.txt"
JUDGE_PROMPT="$SCRIPT_DIR/pattern-judge.md"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"

# The catalog lives in the GIGO plugin source
PATTERNS_REF="$(dirname "$EVALS_DIR")/skills/spec/references/execution-patterns.md"

mkdir -p "$RESULTS_DIR"

echo "=== Execution Pattern Catalog Test ==="
echo ""

EXPECTED_PATTERNS=("Pipeline" "Fan-out/Fan-in" "Producer-Reviewer")
CORRECT=0
TOTAL=3
PROMPT_NUM=0

# Create temp copy of fixture with execution-patterns.md injected
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cp -r "$FIXTURE_DIR"/* "$TMPDIR/" 2>/dev/null || true
cp -r "$FIXTURE_DIR"/.claude "$TMPDIR/" 2>/dev/null || true
mkdir -p "$TMPDIR/.claude/references"
cp "$PATTERNS_REF" "$TMPDIR/.claude/references/execution-patterns.md"

# Append execution-patterns pointer to existing "When to Go Deeper" section
echo 'When planning how to execute work, read `.claude/references/execution-patterns.md` — pick the pattern matching the task'"'"'s dependency shape before writing tasks.' >> "$TMPDIR/.claude/rules/standards.md"

JUDGE_TEMPLATE=$(cat "$JUDGE_PROMPT")

while IFS='|' read -r axis prompt; do
  PROMPT_NUM=$((PROMPT_NUM + 1))
  EXPECTED="${EXPECTED_PATTERNS[$((PROMPT_NUM - 1))]}"

  echo "Prompt $PROMPT_NUM (expected: $EXPECTED): $prompt"

  echo "  Running plan generation..."
  PLAN_OUTPUT=$(cd "$TMPDIR" && claude -p "$prompt" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
    echo "  ERROR: Claude invocation failed"
    echo "{\"prompt\": $PROMPT_NUM, \"expected\": \"$EXPECTED\", \"correct\": false, \"error\": \"invocation_failed\"}" > "$RESULTS_DIR/pattern-prompt-${PROMPT_NUM}.json"
    continue
  }

  PLAN_TEXT=$(echo "$PLAN_OUTPUT" | jq -r '.result // "ERROR: no result"')
  echo "$PLAN_OUTPUT" > "$RESULTS_DIR/pattern-plan-${PROMPT_NUM}-raw.json"

  echo "  Running judge..."
  JUDGE_INPUT="${JUDGE_TEMPLATE//\{PLAN_OUTPUT\}/$PLAN_TEXT}"
  JUDGE_INPUT="${JUDGE_INPUT//\{EXPECTED_PATTERN\}/$EXPECTED}"

  JUDGE_OUTPUT=$(claude -p "$JUDGE_INPUT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
    echo "  ERROR: Judge invocation failed"
    echo "{\"prompt\": $PROMPT_NUM, \"expected\": \"$EXPECTED\", \"correct\": false, \"error\": \"judge_failed\"}" > "$RESULTS_DIR/pattern-prompt-${PROMPT_NUM}.json"
    continue
  }

  JUDGE_TEXT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')
  IS_CORRECT=$(echo "$JUDGE_TEXT" | jq -r '.correct // false' 2>/dev/null || echo "false")

  if [ "$IS_CORRECT" = "true" ]; then
    echo "  Result: CORRECT"
    CORRECT=$((CORRECT + 1))
  else
    echo "  Result: INCORRECT"
  fi

  echo "$JUDGE_TEXT" > "$RESULTS_DIR/pattern-prompt-${PROMPT_NUM}.json"
  echo ""

done < "$PROMPTS_FILE"

THRESHOLD=3

if [ "$CORRECT" -ge "$THRESHOLD" ]; then
  echo "Execution Pattern Catalog: $CORRECT/$TOTAL patterns   [PASS $THRESHOLD/$TOTAL]"
  RESULT="PASS"
else
  echo "Execution Pattern Catalog: $CORRECT/$TOTAL patterns   [FAIL $THRESHOLD/$TOTAL]"
  RESULT="FAIL"
fi

echo "{\"test\": \"execution-patterns\", \"correct\": $CORRECT, \"total\": $TOTAL, \"threshold\": $THRESHOLD, \"result\": \"$RESULT\"}" > "$RESULTS_DIR/pattern-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
