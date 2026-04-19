#!/usr/bin/env bash
# Context-dosing sweep — 5 conditions on the context-mass axis.
#
# Forks run-eval.sh (Brief 13) without modifying it. Builds 5 variants per
# fixture via build-variant.sh, then runs the same prompts under each.
#
# Run matrix: 5 conditions × 2 domains × N prompts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
BUILD_VARIANT="$SCRIPT_DIR/build-variant.sh"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$SCRIPT_DIR/results/dosing-$TIMESTAMP"

DOMAINS=("rails-api" "childrens-novel")
CONDITIONS=("c0-bare" "c1-roster" "c2-team-no-rules" "c3-full" "c4-rules-only")

if [ ! -x "$BUILD_VARIANT" ]; then
  echo "ERROR: build-variant.sh not executable at $BUILD_VARIANT" >&2
  exit 1
fi

echo "=== Context-Dosing Sweep: 5 conditions ==="
echo "Results: $RESULTS_DIR"
echo "Conditions: ${CONDITIONS[*]}"
echo ""

# Count word tokens loaded as context (CLAUDE.md + rules/ + references/).
# Word count is a rough proxy — used for per-condition ratios only.
count_context_tokens() {
  local tmpdir="$1"
  local total=0
  if [ -f "$tmpdir/CLAUDE.md" ]; then
    total=$(( total + $(wc -w < "$tmpdir/CLAUDE.md") ))
  fi
  if [ -d "$tmpdir/.claude/rules" ]; then
    local rules_count
    rules_count=$(find "$tmpdir/.claude/rules" -type f -name "*.md" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1+0}')
    total=$(( total + ${rules_count:-0} ))
  fi
  if [ -d "$tmpdir/.claude/references" ]; then
    local ref_count
    ref_count=$(find "$tmpdir/.claude/references" -type f -name "*.md" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1+0}')
    total=$(( total + ${ref_count:-0} ))
  fi
  echo "$total"
}

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$FIXTURES_DIR/$domain"
  DOMAIN_RESULTS="$RESULTS_DIR/$domain"
  PROMPT_FILE="$PROMPTS_DIR/$domain.txt"

  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "ERROR: Fixture not found: $DOMAIN_DIR" >&2
    exit 1
  fi
  if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompts not found: $PROMPT_FILE" >&2
    exit 1
  fi
  if [ ! -f "$DOMAIN_DIR/CLAUDE.md" ]; then
    echo "ERROR: No CLAUDE.md in fixture — run /gigo first: $DOMAIN_DIR" >&2
    exit 1
  fi

  mkdir -p "$DOMAIN_RESULTS"

  # Build all 5 variant dirs once per domain (variants are pure functions of source).
  declare -A VARIANT_DIRS=()
  declare -A VARIANT_TOKENS=()

  echo "[$domain] Building variants..."
  for condition in "${CONDITIONS[@]}"; do
    VARIANT_TMPDIR=$(mktemp -d)
    "$BUILD_VARIANT" "$DOMAIN_DIR" "$condition" "$VARIANT_TMPDIR"
    VARIANT_DIRS["$condition"]="$VARIANT_TMPDIR"
    VARIANT_TOKENS["$condition"]=$(count_context_tokens "$VARIANT_TMPDIR")
    echo "  $condition: $VARIANT_TMPDIR (${VARIANT_TOKENS[$condition]} words)"
  done

  # Persist the token counts per condition for the writeup.
  {
    echo "{"
    echo "  \"domain\": \"$domain\","
    echo "  \"conditions\": {"
    local_first=1
    for condition in "${CONDITIONS[@]}"; do
      if [ $local_first -eq 1 ]; then
        local_first=0
      else
        echo ","
      fi
      printf "    \"%s\": %s" "$condition" "${VARIANT_TOKENS[$condition]}"
    done
    echo ""
    echo "  }"
    echo "}"
  } > "$DOMAIN_RESULTS/tokens.json"

  echo ""

  PROMPT_NUM=0
  while IFS='|' read -r axis prompt; do
    [ -z "$axis" ] && continue
    PROMPT_NUM=$((PROMPT_NUM + 1))
    PADDED=$(printf "%02d" "$PROMPT_NUM")

    echo "[$domain] Prompt $PADDED ($axis): $prompt"

    for condition in "${CONDITIONS[@]}"; do
      VARIANT_TMPDIR="${VARIANT_DIRS[$condition]}"
      OUT_FILE="$DOMAIN_RESULTS/${PADDED}-${condition}.json"

      echo "  [$condition] running..."
      (cd "$VARIANT_TMPDIR" && claude -p "$prompt" --model claude-opus-4-7 --output-format json --permission-mode bypassPermissions 2>/dev/null) \
        > "$OUT_FILE" || true

      # Wrap: inject axis + condition + tokens_word_count alongside claude's JSON.
      # Claude's JSON output is a single object; we keep it under "response" and add sidecar fields.
      if [ -s "$OUT_FILE" ]; then
        TMP_WRAP=$(mktemp)
        {
          echo "{"
          echo "  \"axis\": \"$axis\","
          echo "  \"prompt\": $(printf '%s' "$prompt" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),"
          echo "  \"condition\": \"$condition\","
          echo "  \"tokens_word_count\": ${VARIANT_TOKENS[$condition]},"
          echo "  \"response\": $(cat "$OUT_FILE")"
          echo "}"
        } > "$TMP_WRAP"
        mv "$TMP_WRAP" "$OUT_FILE"
      fi
    done

    echo "  Done prompt $PADDED."
    echo ""
  done < "$PROMPT_FILE"

  # Cleanup variant temp dirs for this domain.
  for condition in "${CONDITIONS[@]}"; do
    rm -rf "${VARIANT_DIRS[$condition]}"
  done
  unset VARIANT_DIRS VARIANT_TOKENS
done

echo "=== Dosing sweep complete ==="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Next: ./score-dosing-eval.sh $RESULTS_DIR"
