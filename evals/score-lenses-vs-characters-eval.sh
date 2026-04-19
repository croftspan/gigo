#!/usr/bin/env bash
# Brief 15 scorer: pairwise judge of characters vs lenses on Opus 4.7.
#
# - Per-prompt A/B label is randomized; mapping logged to ${PADDED}-mapping.json.
# - Aggregations: per-criterion, per-domain, per-axis (A/B/C from prompts file).
# - Reuses evals/judge-prompt.md verbatim.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-lenses-vs-characters-eval.sh <results-dir>}"
JUDGE_PROMPT_TEMPLATE="$SCRIPT_DIR/judge-prompt.md"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR" >&2
  exit 1
fi

DOMAINS=("rails-api" "childrens-novel")
CRITERIA=(quality_bar persona_voice expertise_routing specificity pushback_quality)

# Per-domain aggregate counters: characters_wins, lenses_wins, ties.
declare -A CHAR_WINS LENS_WINS TIES
# Per-domain × per-criterion counters.
declare -A CRIT_CHAR_WINS CRIT_LENS_WINS CRIT_TIES
# Per-domain × per-axis counters.
declare -A AXIS_CHAR_WINS AXIS_LENS_WINS AXIS_TIES

for domain in "${DOMAINS[@]}"; do
  CHAR_WINS[$domain]=0
  LENS_WINS[$domain]=0
  TIES[$domain]=0
  for crit in "${CRITERIA[@]}"; do
    CRIT_CHAR_WINS[${domain}_${crit}]=0
    CRIT_LENS_WINS[${domain}_${crit}]=0
    CRIT_TIES[${domain}_${crit}]=0
  done
  for axis in A B C; do
    AXIS_CHAR_WINS[${domain}_${axis}]=0
    AXIS_LENS_WINS[${domain}_${axis}]=0
    AXIS_TIES[${domain}_${axis}]=0
  done
done

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$RESULTS_DIR/$domain"
  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "SKIP: No results for $domain" >&2
    continue
  fi

  echo "=== Scoring: $domain ===" >&2

  for char_file in "$DOMAIN_DIR"/*-characters.json; do
    [ -e "$char_file" ] || continue
    PADDED=$(basename "$char_file" | cut -d'-' -f1)
    lens_file="$DOMAIN_DIR/${PADDED}-lenses.json"
    prompt_file="$DOMAIN_DIR/${PADDED}-prompt.json"
    score_file="$DOMAIN_DIR/${PADDED}-score.json"
    mapping_file="$DOMAIN_DIR/${PADDED}-mapping.json"

    if [ ! -f "$lens_file" ]; then
      echo "  SKIP $PADDED: no lenses result" >&2
      continue
    fi

    CHAR_RESPONSE=$(jq -r '.result // "ERROR: no result"' "$char_file")
    LENS_RESPONSE=$(jq -r '.result // "ERROR: no result"' "$lens_file")

    if [ -f "$prompt_file" ]; then
      PROMPT_TEXT=$(jq -r '.prompt' "$prompt_file")
      AXIS=$(jq -r '.axis' "$prompt_file")
    else
      # Fallback: read prompts file directly.
      PROMPT_LINE=$(sed -n "${PADDED##0}p" "$SCRIPT_DIR/prompts/$domain.txt" 2>/dev/null || echo "")
      AXIS="${PROMPT_LINE%%|*}"
      PROMPT_TEXT="${PROMPT_LINE#*|}"
    fi

    # Randomize A/B mapping; log it.
    COIN=$((RANDOM % 2))
    if [ "$COIN" -eq 0 ]; then
      RESPONSE_A="$CHAR_RESPONSE"
      RESPONSE_B="$LENS_RESPONSE"
      A_IS="characters"
      B_IS="lenses"
    else
      RESPONSE_A="$LENS_RESPONSE"
      RESPONSE_B="$CHAR_RESPONSE"
      A_IS="lenses"
      B_IS="characters"
    fi
    printf '{"a_is":"%s","b_is":"%s","axis":"%s"}\n' "$A_IS" "$B_IS" "$AXIS" > "$mapping_file"

    JUDGE_PROMPT=$(cat "$JUDGE_PROMPT_TEMPLATE")
    JUDGE_PROMPT="${JUDGE_PROMPT//\{PROMPT\}/$PROMPT_TEXT}"
    JUDGE_PROMPT="${JUDGE_PROMPT//\{RESPONSE_A\}/$RESPONSE_A}"
    JUDGE_PROMPT="${JUDGE_PROMPT//\{RESPONSE_B\}/$RESPONSE_B}"

    echo "  Scoring prompt $PADDED (axis=$AXIS, A=$A_IS)..." >&2
    JUDGE_OUTPUT=$(claude -p "$JUDGE_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
    JUDGE_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')

    # Persist score with full unblinding metadata.
    if echo "$JUDGE_RESULT" | jq empty 2>/dev/null; then
      jq -n --arg a_is "$A_IS" --arg b_is "$B_IS" --arg axis "$AXIS" \
            --argjson judge "$JUDGE_RESULT" \
            '{a_is:$a_is, b_is:$b_is, axis:$axis, judge_output:$judge}' \
            > "$score_file"
    else
      jq -n --arg a_is "$A_IS" --arg b_is "$B_IS" --arg axis "$AXIS" \
            --arg raw "$JUDGE_RESULT" \
            '{a_is:$a_is, b_is:$b_is, axis:$axis, judge_output_raw:$raw}' \
            > "$score_file"
    fi

    # Tally per-criterion, per-domain, per-axis.
    for crit in "${CRITERIA[@]}"; do
      WINNER=$(echo "$JUDGE_RESULT" | jq -r ".$crit.winner // \"TIE\"" 2>/dev/null || echo "TIE")
      case "$WINNER" in
        TIE|tie)
          TIES[$domain]=$((${TIES[$domain]} + 1))
          CRIT_TIES[${domain}_${crit}]=$((${CRIT_TIES[${domain}_${crit}]} + 1))
          AXIS_TIES[${domain}_${AXIS}]=$((${AXIS_TIES[${domain}_${AXIS}]} + 1))
          ;;
        A|a)
          if [ "$A_IS" = "characters" ]; then
            CHAR_WINS[$domain]=$((${CHAR_WINS[$domain]} + 1))
            CRIT_CHAR_WINS[${domain}_${crit}]=$((${CRIT_CHAR_WINS[${domain}_${crit}]} + 1))
            AXIS_CHAR_WINS[${domain}_${AXIS}]=$((${AXIS_CHAR_WINS[${domain}_${AXIS}]} + 1))
          else
            LENS_WINS[$domain]=$((${LENS_WINS[$domain]} + 1))
            CRIT_LENS_WINS[${domain}_${crit}]=$((${CRIT_LENS_WINS[${domain}_${crit}]} + 1))
            AXIS_LENS_WINS[${domain}_${AXIS}]=$((${AXIS_LENS_WINS[${domain}_${AXIS}]} + 1))
          fi
          ;;
        B|b)
          if [ "$B_IS" = "characters" ]; then
            CHAR_WINS[$domain]=$((${CHAR_WINS[$domain]} + 1))
            CRIT_CHAR_WINS[${domain}_${crit}]=$((${CRIT_CHAR_WINS[${domain}_${crit}]} + 1))
            AXIS_CHAR_WINS[${domain}_${AXIS}]=$((${AXIS_CHAR_WINS[${domain}_${AXIS}]} + 1))
          else
            LENS_WINS[$domain]=$((${LENS_WINS[$domain]} + 1))
            CRIT_LENS_WINS[${domain}_${crit}]=$((${CRIT_LENS_WINS[${domain}_${crit}]} + 1))
            AXIS_LENS_WINS[${domain}_${AXIS}]=$((${AXIS_LENS_WINS[${domain}_${AXIS}]} + 1))
          fi
          ;;
        *)
          # Treat unparsable as TIE so the run doesn't abort.
          TIES[$domain]=$((${TIES[$domain]} + 1))
          CRIT_TIES[${domain}_${crit}]=$((${CRIT_TIES[${domain}_${crit}]} + 1))
          AXIS_TIES[${domain}_${AXIS}]=$((${AXIS_TIES[${domain}_${AXIS}]} + 1))
          ;;
      esac
    done
  done
  echo "" >&2
done

# Write the summary.
SUMMARY_FILE="$RESULTS_DIR/summary.md"
{
  echo "# Eval Results: Lenses vs Characters (Brief 15)"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo "Model: claude-opus-4-7"
  echo ""

  total_char=0; total_lens=0; total_tie=0
  for domain in "${DOMAINS[@]}"; do
    C=${CHAR_WINS[$domain]}; L=${LENS_WINS[$domain]}; T=${TIES[$domain]}
    DT=$((C + L + T))
    total_char=$((total_char + C))
    total_lens=$((total_lens + L))
    total_tie=$((total_tie + T))

    echo "## $domain"
    echo ""
    if [ "$DT" -gt 0 ]; then
      C_PCT=$((C * 100 / DT)); L_PCT=$((L * 100 / DT)); T_PCT=$((T * 100 / DT))
      echo "- Characters won: $C / $DT (${C_PCT}%)"
      echo "- Lenses won:     $L / $DT (${L_PCT}%)"
      echo "- Tied:           $T / $DT (${T_PCT}%)"
    else
      echo "- (no results)"
    fi
    echo ""

    echo "### Per-criterion"
    echo ""
    echo "| Criterion | Characters | Lenses | Tie |"
    echo "|---|---|---|---|"
    for crit in "${CRITERIA[@]}"; do
      cc=${CRIT_CHAR_WINS[${domain}_${crit}]}
      cl=${CRIT_LENS_WINS[${domain}_${crit}]}
      ct=${CRIT_TIES[${domain}_${crit}]}
      echo "| $crit | $cc | $cl | $ct |"
    done
    echo ""

    echo "### Per-axis (A=invited mistakes / B=advisory / C=multi-step)"
    echo ""
    echo "| Axis | Characters | Lenses | Tie |"
    echo "|---|---|---|---|"
    for axis in A B C; do
      ac=${AXIS_CHAR_WINS[${domain}_${axis}]}
      al=${AXIS_LENS_WINS[${domain}_${axis}]}
      at=${AXIS_TIES[${domain}_${axis}]}
      echo "| $axis | $ac | $al | $at |"
    done
    echo ""
  done

  GT=$((total_char + total_lens + total_tie))
  echo "## Combined"
  echo ""
  if [ "$GT" -gt 0 ]; then
    cpc=$((total_char * 100 / GT))
    lpc=$((total_lens * 100 / GT))
    tpc=$((total_tie * 100 / GT))
    echo "- Characters won: $total_char / $GT (${cpc}%)"
    echo "- Lenses won:     $total_lens / $GT (${lpc}%)"
    echo "- Tied:           $total_tie / $GT (${tpc}%)"
  fi
  echo ""

  echo "## Headline"
  echo ""
  if [ "$GT" -gt 0 ]; then
    if [ "$total_char" -gt "$total_lens" ]; then
      DELTA=$((total_char - total_lens))
      echo "**Characters wins** by $DELTA criteria-judgments ($((DELTA * 100 / GT))% margin over Lenses, ties excluded from margin)."
    elif [ "$total_lens" -gt "$total_char" ]; then
      DELTA=$((total_lens - total_char))
      echo "**Lenses wins** by $DELTA criteria-judgments ($((DELTA * 100 / GT))% margin over Characters, ties excluded from margin)."
    else
      echo "**Tie** at $total_char each across all criteria-judgments."
    fi
  fi
} > "$SUMMARY_FILE"

cat "$SUMMARY_FILE"
echo ""
echo "Full results: $RESULTS_DIR"
