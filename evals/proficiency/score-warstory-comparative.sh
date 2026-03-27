#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-warstory-comparative.sh <results-dir>}"
RUBRICS_DIR="$SCRIPT_DIR/rubrics"
TEMPLATE_FILE="$RUBRICS_DIR/rails-rubric-comparative.md"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR"
  exit 1
fi

VARIANTS=(bare warstories compressed fixonly)

# Load all 4 responses
declare -A RESPONSES
for v in "${VARIANTS[@]}"; do
  FILE="$RESULTS_DIR/rails-api/$v.json"
  if [ ! -f "$FILE" ]; then
    echo "ERROR: Missing $v result"
    exit 1
  fi
  RESPONSES[$v]=$(jq -r '.result // "ERROR"' "$FILE")
done

# ============================================================
# RAILS AUTOMATED CHECKS (same as before, per-variant)
# ============================================================
rails_auto_checks() {
  local RESPONSE="$1"
  local PASS=0

  echo "$RESPONSE" | grep -qE '(def |class |module |end$)' && PASS=$((PASS + 1))
  echo "$RESPONSE" | grep -qiE '(create_table|class Create|class Add.*Migration)' && PASS=$((PASS + 1))
  { echo "$RESPONSE" | grep -qE 'def change' || \
    { echo "$RESPONSE" | grep -qE 'def up' && echo "$RESPONSE" | grep -qE 'def down'; }; } && PASS=$((PASS + 1))

  local MC=0
  echo "$RESPONSE" | grep -qiE 'class Book' && MC=$((MC + 1))
  echo "$RESPONSE" | grep -qiE 'class User' && MC=$((MC + 1))
  echo "$RESPONSE" | grep -qiE 'class Reservation' && MC=$((MC + 1))
  [ "$MC" -eq 3 ] && PASS=$((PASS + 1))

  { echo "$RESPONSE" | grep -qE 'belongs_to' && echo "$RESPONSE" | grep -qE 'has_many'; } && PASS=$((PASS + 1))
  { echo "$RESPONSE" | grep -qiE 'class.*ReservationsController' && \
    echo "$RESPONSE" | grep -qE 'def (create|index|destroy)'; } && PASS=$((PASS + 1))
  echo "$RESPONSE" | grep -qiE 'resources? :reservations' && PASS=$((PASS + 1))
  echo "$RESPONSE" | grep -qiE '(RSpec\.describe|describe.*type: :request|spec/requests)' && PASS=$((PASS + 1))
  echo "$RESPONSE" | grep -qiE '(error.*code.*message|render json:.*error|{ error:)' && PASS=$((PASS + 1))
  echo "$RESPONSE" | grep -qiE '(page|per_page|pagy|kaminari|paginate)' && PASS=$((PASS + 1))

  echo "$PASS"
}

# ============================================================
# RUBRIC QUESTIONS
# ============================================================
RAILS_QUESTIONS=(
  "Does the reservation creation use a transaction, lock, or atomic operation to prevent race conditions on copies_available?"
  "Is there a uniqueness check preventing the same user from having two active reservations for the same book?"
  "Does it validate copies_available > 0 before creating a reservation?"
  "Does cancelling an already-cancelled reservation return a proper error response, not crash or silently succeed?"
  "Do ALL error responses (validation, not found, business rule violations) use the same { error: { code, message } } format?"
  "Is the 48-hour expiry correctly set on reservation creation (reserved_at + 48.hours or equivalent)?"
  "Do request specs cover the happy path AND at least 2 distinct error paths?"
  "Is business logic in models or service objects, not directly in controller actions?"
  "Does the index action use includes, preload, or eager_load for associations?"
  "Is the migration free of table-locking patterns (no default values on add_column, no non-concurrent indexes on large tables)?"
)
RAILS_CHECK_NAMES=(
  "Race condition handling"
  "Duplicate reservation guard"
  "Copies validation"
  "Cancellation idempotency"
  "Error envelope consistency"
  "Expiry logic"
  "Spec coverage"
  "Thin controller"
  "N+1 prevention"
  "Migration safety"
)

# ============================================================
# MAIN: comparative rubric scoring
# ============================================================

SUMMARY_FILE="$RESULTS_DIR/comparative-summary.md"

{
  echo "# War Story Format — Comparative Scoring"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo ""
  echo "Same judge scores all 4 variants per rubric check. Order randomized per check."
  echo ""
} > "$SUMMARY_FILE"

# Auto checks first (these don't need comparative judging)
echo "=== Auto checks ==="
declare -A AUTO_SCORES
for v in "${VARIANTS[@]}"; do
  AUTO_SCORES[$v]=$(rails_auto_checks "${RESPONSES[$v]}")
  echo "  $v auto: ${AUTO_SCORES[$v]}/10"
done
echo ""

# Comparative rubric checks
declare -A RUBRIC_SCORES
for v in "${VARIANTS[@]}"; do
  RUBRIC_SCORES[$v]=0
done

# Per-check detail rows
declare -A CHECK_RESULTS

echo "=== Comparative rubric checks ==="
for i in "${!RAILS_QUESTIONS[@]}"; do
  CHECK_NUM=$((i + 11))
  echo "  Check $CHECK_NUM: ${RAILS_CHECK_NAMES[$i]}..."

  # Randomize order: shuffle variant indices
  SHUFFLED=($(echo "${VARIANTS[@]}" | tr ' ' '\n' | sort -R))
  # Map: A=SHUFFLED[0], B=SHUFFLED[1], C=SHUFFLED[2], D=SHUFFLED[3]

  TEMPLATE=$(cat "$TEMPLATE_FILE")

  # Substitute all 4 code blocks and the question
  PROMPT="${TEMPLATE//\{CODE_A\}/${RESPONSES[${SHUFFLED[0]}]}}"
  PROMPT="${PROMPT//\{CODE_B\}/${RESPONSES[${SHUFFLED[1]}]}}"
  PROMPT="${PROMPT//\{CODE_C\}/${RESPONSES[${SHUFFLED[2]}]}}"
  PROMPT="${PROMPT//\{CODE_D\}/${RESPONSES[${SHUFFLED[3]}]}}"
  PROMPT="${PROMPT//\{QUESTION\}/${RAILS_QUESTIONS[$i]}}"

  # Call judge
  JUDGE_OUTPUT=$(claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
  RAW_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"')
  # Extract JSON — judge often returns prose before/after the JSON block
  # Strategy: try to extract from code fence first, then try parsing the whole thing
  JUDGE_RESULT=""
  # Try code fence extraction
  FENCED=$(echo "$RAW_RESULT" | sed -n '/^```json$/,/^```$/p' | sed '1d;$d')
  if [ -n "$FENCED" ] && echo "$FENCED" | jq -e '.A' >/dev/null 2>&1; then
    JUDGE_RESULT="$FENCED"
  fi
  # Try: find the line starting with {"A" and take everything from there
  if [ -z "$JUDGE_RESULT" ]; then
    FROM_JSON=$(echo "$RAW_RESULT" | sed -n '/^{"A"/,$p')
    if [ -n "$FROM_JSON" ] && echo "$FROM_JSON" | jq -e '.A' >/dev/null 2>&1; then
      JUDGE_RESULT="$FROM_JSON"
    fi
  fi
  # Try: the whole raw result might be valid JSON
  if [ -z "$JUDGE_RESULT" ] && echo "$RAW_RESULT" | jq -e '.A' >/dev/null 2>&1; then
    JUDGE_RESULT="$RAW_RESULT"
  fi
  # Give up
  if [ -z "$JUDGE_RESULT" ]; then
    echo "    WARN: Could not parse judge output for check $CHECK_NUM"
    JUDGE_RESULT='{"A":{"pass":false,"reasoning":"Parse error"},"B":{"pass":false,"reasoning":"Parse error"},"C":{"pass":false,"reasoning":"Parse error"},"D":{"pass":false,"reasoning":"Parse error"}}'
  fi

  # Parse results for each label and map back to variant
  for label_idx in 0 1 2 3; do
    LABEL=$(echo "ABCD" | cut -c$((label_idx + 1)))
    VARIANT="${SHUFFLED[$label_idx]}"

    PASSED=$(echo "$JUDGE_RESULT" | jq -r ".${LABEL}.pass // false" 2>/dev/null || echo "false")
    REASONING=$(echo "$JUDGE_RESULT" | jq -r ".${LABEL}.reasoning // \"Parse error\"" 2>/dev/null || echo "Parse error")

    if [ "$PASSED" = "true" ]; then
      RUBRIC_SCORES[$VARIANT]=$(( ${RUBRIC_SCORES[$VARIANT]} + 1 ))
      CHECK_RESULTS["${VARIANT}_${CHECK_NUM}"]="PASS|$REASONING"
    else
      CHECK_RESULTS["${VARIANT}_${CHECK_NUM}"]="FAIL|$REASONING"
    fi
  done

  # Show per-check results
  for v in "${VARIANTS[@]}"; do
    RESULT="${CHECK_RESULTS[${v}_${CHECK_NUM}]}"
    PF=$(echo "$RESULT" | cut -d'|' -f1)
    echo "    $v: $PF"
  done
done
echo ""

# ============================================================
# OUTPUT SUMMARY
# ============================================================

{
  echo "## Per-Check Results"
  echo ""

  for v in "${VARIANTS[@]}"; do
    TOTAL=$(( ${AUTO_SCORES[$v]} + ${RUBRIC_SCORES[$v]} ))
    echo "### $v: $TOTAL/20 (auto: ${AUTO_SCORES[$v]}, rubric: ${RUBRIC_SCORES[$v]})"
    echo ""
    echo "| # | Check | Result | Notes |"
    echo "|---|---|---|---|"

    # Auto checks (just pass/fail count, no detail for brevity)
    echo "| 1-10 | Auto checks | ${AUTO_SCORES[$v]}/10 | Structural checks passed |"

    for i in "${!RAILS_QUESTIONS[@]}"; do
      CHECK_NUM=$((i + 11))
      RESULT="${CHECK_RESULTS[${v}_${CHECK_NUM}]:-SKIP|No result}"
      PF=$(echo "$RESULT" | cut -d'|' -f1)
      REASON=$(echo "$RESULT" | cut -d'|' -f2-)
      echo "| $CHECK_NUM | ${RAILS_CHECK_NAMES[$i]} | $PF | $REASON |"
    done
    echo ""
  done

  echo "## Summary"
  echo ""
  echo "| Variant | Total | Auto | Rubric | Words |"
  echo "|---|---|---|---|---|"

  for v in "${VARIANTS[@]}"; do
    TOTAL=$(( ${AUTO_SCORES[$v]} + ${RUBRIC_SCORES[$v]} ))
    case $v in
      bare) WORDS=0 ;;
      warstories) WORDS=468 ;;
      compressed) WORDS=287 ;;
      fixonly) WORDS=229 ;;
    esac
    echo "| $v | $TOTAL/20 | ${AUTO_SCORES[$v]}/10 | ${RUBRIC_SCORES[$v]}/10 | $WORDS |"
  done

  echo ""
} >> "$SUMMARY_FILE"

echo "=== Final Summary ==="
echo ""
for v in "${VARIANTS[@]}"; do
  TOTAL=$(( ${AUTO_SCORES[$v]} + ${RUBRIC_SCORES[$v]} ))
  echo "  $v: $TOTAL/20 (auto: ${AUTO_SCORES[$v]}, rubric: ${RUBRIC_SCORES[$v]})"
done
echo ""
echo "Full results: $SUMMARY_FILE"
