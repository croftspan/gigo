#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-eval.sh <results-dir>}"
JUDGE_PROMPT_TEMPLATE="$SCRIPT_DIR/judge-prompt.md"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR"
  exit 1
fi

DOMAINS=("rails-api" "childrens-novel")

# Track aggregate scores
declare -A ASSEMBLED_WINS
declare -A TIES
declare -A ASSEMBLED_LOSSES
TOTAL_CRITERIA=0

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$RESULTS_DIR/$domain"
  ASSEMBLED_WINS[$domain]=0
  TIES[$domain]=0
  ASSEMBLED_LOSSES[$domain]=0

  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "SKIP: No results for $domain"
    continue
  fi

  echo "=== Scoring: $domain ==="

  for bare_file in "$DOMAIN_DIR"/*-bare.json; do
    PADDED=$(basename "$bare_file" | cut -d'-' -f1)
    assembled_file="$DOMAIN_DIR/${PADDED}-assembled.json"
    score_file="$DOMAIN_DIR/${PADDED}-score.json"

    if [ ! -f "$assembled_file" ]; then
      echo "  SKIP: No assembled result for $PADDED"
      continue
    fi

    # Extract response text from JSON
    BARE_RESPONSE=$(jq -r '.result // "ERROR: no result"' "$bare_file")
    ASSEMBLED_RESPONSE=$(jq -r '.result // "ERROR: no result"' "$assembled_file")

    # Read the prompt from the prompts file
    PROMPT_LINE=$(sed -n "${PADDED##0}p" "$SCRIPT_DIR/prompts/$domain.txt" 2>/dev/null || echo "")
    PROMPT_TEXT="${PROMPT_LINE#*|}"

    # Randomize A/B assignment
    COIN=$((RANDOM % 2))
    if [ "$COIN" -eq 0 ]; then
      RESPONSE_A="$BARE_RESPONSE"
      RESPONSE_B="$ASSEMBLED_RESPONSE"
      A_IS="bare"
    else
      RESPONSE_A="$ASSEMBLED_RESPONSE"
      RESPONSE_B="$BARE_RESPONSE"
      A_IS="assembled"
    fi

    # Build judge prompt
    JUDGE_PROMPT=$(cat "$JUDGE_PROMPT_TEMPLATE")
    JUDGE_PROMPT="${JUDGE_PROMPT//\{PROMPT\}/$PROMPT_TEXT}"
    JUDGE_PROMPT="${JUDGE_PROMPT//\{RESPONSE_A\}/$RESPONSE_A}"
    JUDGE_PROMPT="${JUDGE_PROMPT//\{RESPONSE_B\}/$RESPONSE_B}"

    echo "  Scoring prompt $PADDED..."
    JUDGE_OUTPUT=$(claude -p "$JUDGE_PROMPT" --bare --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
    JUDGE_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"')

    # Save raw score with unblinding metadata
    echo "{\"a_is\": \"$A_IS\", \"judge_output\": $JUDGE_RESULT}" > "$score_file" 2>/dev/null || \
    echo "{\"a_is\": \"$A_IS\", \"judge_output_raw\": $(echo "$JUDGE_RESULT" | jq -Rs .)}" > "$score_file"

    # Count wins per criteria
    for criteria in quality_bar persona_voice expertise_routing specificity pushback_quality; do
      WINNER=$(echo "$JUDGE_RESULT" | jq -r ".$criteria.winner // \"TIE\"" 2>/dev/null || echo "TIE")
      TOTAL_CRITERIA=$((TOTAL_CRITERIA + 1))

      # Unblind: map A/B winner back to bare/assembled
      if [ "$WINNER" = "TIE" ]; then
        TIES[$domain]=$((${TIES[$domain]} + 1))
      elif { [ "$WINNER" = "A" ] && [ "$A_IS" = "assembled" ]; } || \
           { [ "$WINNER" = "B" ] && [ "$A_IS" = "bare" ]; }; then
        ASSEMBLED_WINS[$domain]=$((${ASSEMBLED_WINS[$domain]} + 1))
      else
        ASSEMBLED_LOSSES[$domain]=$((${ASSEMBLED_LOSSES[$domain]} + 1))
      fi
    done

  done

  echo ""
done

# Generate summary
SUMMARY_FILE="$RESULTS_DIR/summary.md"
TOTAL_WINS=0
TOTAL_TIES=0
TOTAL_LOSSES=0

{
  echo "# Eval Results: Assembled vs Bare"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo ""

  for domain in "${DOMAINS[@]}"; do
    W=${ASSEMBLED_WINS[$domain]}
    T=${TIES[$domain]}
    L=${ASSEMBLED_LOSSES[$domain]}
    DOMAIN_TOTAL=$((W + T + L))
    TOTAL_WINS=$((TOTAL_WINS + W))
    TOTAL_TIES=$((TOTAL_TIES + T))
    TOTAL_LOSSES=$((TOTAL_LOSSES + L))

    echo "## $domain"
    echo ""
    if [ "$DOMAIN_TOTAL" -gt 0 ]; then
      PCT=$((W * 100 / DOMAIN_TOTAL))
      echo "- Assembled won: $W / $DOMAIN_TOTAL ($PCT%)"
    else
      echo "- Assembled won: $W / $DOMAIN_TOTAL"
    fi
    echo "- Tied: $T"
    echo "- Assembled lost: $L"
    echo ""
  done

  GRAND_TOTAL=$((TOTAL_WINS + TOTAL_TIES + TOTAL_LOSSES))
  echo "## Combined"
  echo ""
  if [ "$GRAND_TOTAL" -gt 0 ]; then
    GRAND_PCT=$((TOTAL_WINS * 100 / GRAND_TOTAL))
    echo "- Assembled won: $TOTAL_WINS / $GRAND_TOTAL ($GRAND_PCT%)"
  else
    echo "- Assembled won: $TOTAL_WINS / $GRAND_TOTAL"
  fi
  echo "- Tied: $TOTAL_TIES"
  echo "- Assembled lost: $TOTAL_LOSSES"
  echo ""
  echo "## Interpretation"
  echo ""
  if [ "$GRAND_TOTAL" -gt 0 ]; then
    if [ "$GRAND_PCT" -ge 80 ]; then
      echo "Context is working. Assembled context wins $GRAND_PCT% of criteria. Phase 2 may not be needed."
    elif [ "$GRAND_PCT" -ge 60 ]; then
      echo "Context helps but underperforms. Assembled context wins $GRAND_PCT% of criteria. Phase 2 should focus on activation."
    else
      echo "Context isn't earning its tokens. Assembled context wins only $GRAND_PCT% of criteria. Phase 2 is critical."
    fi
  fi

} > "$SUMMARY_FILE"

echo "=== Summary ==="
cat "$SUMMARY_FILE"
echo ""
echo "Full results: $RESULTS_DIR"
