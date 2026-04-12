#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$EVALS_DIR/fixtures/rails-api"
JUDGE_PROMPT="$SCRIPT_DIR/matrix-judge.md"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"

MATRIX_REF="$(dirname "$EVALS_DIR")/skills/maintain/references/change-impact-matrix.md"

mkdir -p "$RESULTS_DIR"

echo "=== Phase Selection Matrix Test ==="
echo ""

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cp -r "$FIXTURE_DIR"/* "$TMPDIR/" 2>/dev/null || true
cp -r "$FIXTURE_DIR"/.claude "$TMPDIR/" 2>/dev/null || true
mkdir -p "$TMPDIR/.claude/references"
cp "$MATRIX_REF" "$TMPDIR/.claude/references/change-impact-matrix.md"

SCENARIO_PROMPT='A new persona has been added to this project'"'"'s CLAUDE.md:

### Vault — The Security Auditor

**Modeled after:** Troy Hunt'"'"'s breach-first pragmatism + OWASP'"'"'s systematic methodology + Tanya Janca'"'"'s DevSecOps integration.

- **Owns:** Input validation, authentication flows, SQL injection prevention, dependency auditing
- **Quality bar:** Every endpoint validates authentication and authorization. No raw SQL. Input sanitization on all user-facing fields.
- **Won'"'"'t do:** Security theater — adding CSRF tokens to an API-only app, over-restricting dev environments

This persona was just added to CLAUDE.md. Without making any changes, analyze: what other files in the .claude/ directory need updating as a result? For each file, explain what change is needed and why.'

echo "Running scenario analysis..."
SCENARIO_OUTPUT=$(cd "$TMPDIR" && claude -p "$SCENARIO_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Claude invocation failed"
  echo '{ "status": "ERROR", "reason": "Claude invocation failed" }' > "$RESULTS_DIR/matrix-test.json"
  exit 1
}

SCENARIO_TEXT=$(echo "$SCENARIO_OUTPUT" | jq -r '.result // "ERROR: no result"')
echo "$SCENARIO_OUTPUT" > "$RESULTS_DIR/matrix-scenario-raw.json"

echo "Running judge..."
JUDGE_TEMPLATE=$(cat "$JUDGE_PROMPT")
JUDGE_INPUT="${JUDGE_TEMPLATE//\{RESPONSE\}/$SCENARIO_TEXT}"

JUDGE_OUTPUT=$(claude -p "$JUDGE_INPUT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Judge invocation failed"
  echo '{ "status": "ERROR", "reason": "Judge invocation failed" }' > "$RESULTS_DIR/matrix-test.json"
  exit 1
}

JUDGE_TEXT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')
echo "$JUDGE_TEXT" > "$RESULTS_DIR/matrix-judge-raw.json"

IDENTIFIED=$(echo "$JUDGE_TEXT" | jq '[.[] | select(.identified == true)] | length' 2>/dev/null || echo 0)
TOTAL=5
THRESHOLD=3

echo ""
echo "Per-effect results:"
EFFECTS=("review-criteria regeneration" "rules line budget" "snap audit updates" "new reference file" "workflow pointer")
for i in $(seq 0 4); do
  STATUS=$(echo "$JUDGE_TEXT" | jq -r ".[$i].identified // false" 2>/dev/null)
  if [ "$STATUS" = "true" ]; then
    echo "  ${EFFECTS[$i]}: IDENTIFIED"
  else
    echo "  ${EFFECTS[$i]}: MISSED"
  fi
done

echo ""
if [ "$IDENTIFIED" -ge "$THRESHOLD" ]; then
  echo "Phase Selection Matrix: $IDENTIFIED/$TOTAL effects   [PASS ≥$THRESHOLD]"
  RESULT="PASS"
else
  echo "Phase Selection Matrix: $IDENTIFIED/$TOTAL effects   [FAIL ≥$THRESHOLD]"
  RESULT="FAIL"
fi

echo "{\"test\": \"phase-matrix\", \"identified\": $IDENTIFIED, \"total\": $TOTAL, \"threshold\": $THRESHOLD, \"result\": \"$RESULT\"}" > "$RESULTS_DIR/matrix-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
