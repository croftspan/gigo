#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-warstory-format-test.sh <results-dir>}"
RUBRICS_DIR="$SCRIPT_DIR/rubrics"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR"
  exit 1
fi

# ============================================================
# RAILS AUTOMATED CHECKS (same as score-proficiency.sh)
# ============================================================
rails_auto_checks() {
  local RESPONSE="$1"
  local PASS=0
  local RESULTS=""

  if echo "$RESPONSE" | grep -qE '(def |class |module |end$)'; then
    RESULTS+="| 1 | Parseable Ruby | PASS | Contains Ruby syntax |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 1 | Parseable Ruby | FAIL | No Ruby syntax detected |\n"
  fi

  if echo "$RESPONSE" | grep -qiE '(create_table|class Create|class Add.*Migration)'; then
    RESULTS+="| 2 | Migration exists | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 2 | Migration exists | FAIL | No migration found |\n"
  fi

  if echo "$RESPONSE" | grep -qE 'def change' || \
     { echo "$RESPONSE" | grep -qE 'def up' && echo "$RESPONSE" | grep -qE 'def down'; }; then
    RESULTS+="| 3 | Migration reversible | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 3 | Migration reversible | FAIL | No reversible migration pattern |\n"
  fi

  local MODEL_COUNT=0
  echo "$RESPONSE" | grep -qiE 'class Book' && MODEL_COUNT=$((MODEL_COUNT + 1))
  echo "$RESPONSE" | grep -qiE 'class User' && MODEL_COUNT=$((MODEL_COUNT + 1))
  echo "$RESPONSE" | grep -qiE 'class Reservation' && MODEL_COUNT=$((MODEL_COUNT + 1))
  if [ "$MODEL_COUNT" -eq 3 ]; then
    RESULTS+="| 4 | Models exist | PASS | All 3 models found |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 4 | Models exist | FAIL | Found $MODEL_COUNT/3 models |\n"
  fi

  if echo "$RESPONSE" | grep -qE 'belongs_to' && echo "$RESPONSE" | grep -qE 'has_many'; then
    RESULTS+="| 5 | Associations defined | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 5 | Associations defined | FAIL | Missing belongs_to or has_many |\n"
  fi

  if echo "$RESPONSE" | grep -qiE 'class.*ReservationsController' && \
     echo "$RESPONSE" | grep -qE 'def (create|index|destroy)'; then
    RESULTS+="| 6 | Controller exists | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 6 | Controller exists | FAIL | Missing controller or actions |\n"
  fi

  if echo "$RESPONSE" | grep -qiE 'resources? :reservations'; then
    RESULTS+="| 7 | Routes defined | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 7 | Routes defined | FAIL | No reservation routes found |\n"
  fi

  if echo "$RESPONSE" | grep -qiE '(RSpec\.describe|describe.*type: :request|spec/requests)'; then
    RESULTS+="| 8 | Request specs exist | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 8 | Request specs exist | FAIL | No request specs found |\n"
  fi

  if echo "$RESPONSE" | grep -qiE '(error.*code.*message|render json:.*error|{ error:)'; then
    RESULTS+="| 9 | Error envelope pattern | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 9 | Error envelope pattern | FAIL | No error envelope pattern found |\n"
  fi

  if echo "$RESPONSE" | grep -qiE '(page|per_page|pagy|kaminari|paginate)'; then
    RESULTS+="| 10 | Pagination present | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 10 | Pagination present | FAIL | No pagination found |\n"
  fi

  echo "$PASS"
  echo -e "$RESULTS"
}

# ============================================================
# LLM RUBRIC CHECK
# ============================================================
llm_rubric_check() {
  local TEMPLATE_FILE="$1"
  local CONTENT="$2"
  local QUESTION="$3"
  local CHECK_NUM="$4"
  local CHECK_NAME="$5"

  local TEMPLATE
  TEMPLATE=$(cat "$TEMPLATE_FILE")

  local PROMPT="${TEMPLATE//\{CODE\}/$CONTENT}"
  PROMPT="${PROMPT//\{QUESTION\}/$QUESTION}"

  local JUDGE_OUTPUT
  JUDGE_OUTPUT=$(claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
  local JUDGE_RESULT
  JUDGE_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')

  local PASSED
  PASSED=$(echo "$JUDGE_RESULT" | jq -r '.pass // false' 2>/dev/null || echo "false")
  local REASONING
  REASONING=$(echo "$JUDGE_RESULT" | jq -r '.reasoning // "Parse error"' 2>/dev/null || echo "Parse error")

  if [ "$PASSED" = "true" ]; then
    echo "PASS"
    echo "| $CHECK_NUM | $CHECK_NAME | PASS | $REASONING |"
  else
    echo "FAIL"
    echo "| $CHECK_NUM | $CHECK_NAME | FAIL | $REASONING |"
  fi
}

# ============================================================
# MAIN SCORING LOOP
# ============================================================

SUMMARY_FILE="$RESULTS_DIR/summary.md"

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

{
  echo "# War Story Format Experiment Results"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo ""
  echo "## Variants"
  echo ""
  echo "- **bare** — no context at all"
  echo "- **warstories** — full narrative (proven 20/20 baseline)"
  echo "- **compressed** — trigger → consequence → fix (one line each)"
  echo "- **fixonly** — just the rules, no story or consequence"
  echo ""
} > "$SUMMARY_FILE"

VARIANTS=(bare warstories compressed fixonly)

for variant in "${VARIANTS[@]}"; do
  VARIANT_FILE="$RESULTS_DIR/rails-api/$variant.json"
  if [ ! -f "$VARIANT_FILE" ]; then
    echo "SKIP: No $variant result"
    continue
  fi

  RESPONSE=$(jq -r '.result // "ERROR: no result"' "$VARIANT_FILE")

  echo "=== Scoring: $variant ==="
  AUTO_PASS=0
  RUBRIC_PASS=0
  ALL_ROWS=""

  AUTO_OUTPUT=$(rails_auto_checks "$RESPONSE")
  AUTO_PASS=$(echo "$AUTO_OUTPUT" | head -1)
  AUTO_ROWS=$(echo "$AUTO_OUTPUT" | tail -n +2)
  ALL_ROWS+="$AUTO_ROWS"

  RUBRIC_TEMPLATE="$RUBRICS_DIR/rails-rubric.md"
  for i in "${!RAILS_QUESTIONS[@]}"; do
    CHECK_NUM=$((i + 11))
    echo "  Rubric check $CHECK_NUM: ${RAILS_CHECK_NAMES[$i]}..."
    RESULT=$(llm_rubric_check "$RUBRIC_TEMPLATE" "$RESPONSE" "${RAILS_QUESTIONS[$i]}" "$CHECK_NUM" "${RAILS_CHECK_NAMES[$i]}")
    PASS_FAIL=$(echo "$RESULT" | head -1)
    ROW=$(echo "$RESULT" | tail -1)
    ALL_ROWS+="\n$ROW"
    if [ "$PASS_FAIL" = "PASS" ]; then
      RUBRIC_PASS=$((RUBRIC_PASS + 1))
    fi
  done

  TOTAL_PASS=$((AUTO_PASS + RUBRIC_PASS))

  echo "{\"variant\": \"$variant\", \"auto\": $AUTO_PASS, \"rubric\": $RUBRIC_PASS, \"total\": $TOTAL_PASS}" \
    > "$RESULTS_DIR/rails-api/$variant-score.json"

  {
    echo "## $variant: $TOTAL_PASS/20"
    echo ""
    echo "| # | Check | Result | Notes |"
    echo "|---|---|---|---|"
    echo -e "$ALL_ROWS"
    echo ""
  } >> "$SUMMARY_FILE"

  echo "  $variant: $TOTAL_PASS/20 (auto: $AUTO_PASS, rubric: $RUBRIC_PASS)"
  echo ""
done

# Comparison table
{
  echo "## Summary"
  echo ""
  echo "| Variant | Score | Auto | Rubric |"
  echo "|---|---|---|---|"

  for variant in "${VARIANTS[@]}"; do
    SCORE_FILE="$RESULTS_DIR/rails-api/$variant-score.json"
    if [ -f "$SCORE_FILE" ]; then
      TOTAL=$(jq -r '.total' "$SCORE_FILE")
      AUTO=$(jq -r '.auto' "$SCORE_FILE")
      RUBRIC=$(jq -r '.rubric' "$SCORE_FILE")
      echo "| $variant | $TOTAL/20 | $AUTO/10 | $RUBRIC/10 |"
    fi
  done

  echo ""
} >> "$SUMMARY_FILE"

echo "=== Summary ==="
cat "$SUMMARY_FILE"
echo ""
echo "Full results: $RESULTS_DIR"
