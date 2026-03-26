#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$SCRIPT_DIR/results/$TIMESTAMP"

DOMAINS=("rails-api" "childrens-novel")

echo "=== Eval Suite: Assembled vs Bare ==="
echo "Results: $RESULTS_DIR"
echo ""

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$FIXTURES_DIR/$domain"
  DOMAIN_RESULTS="$RESULTS_DIR/$domain"
  PROMPT_FILE="$PROMPTS_DIR/$domain.txt"

  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "ERROR: Fixture not found: $DOMAIN_DIR"
    exit 1
  fi

  if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompts not found: $PROMPT_FILE"
    exit 1
  fi

  if [ ! -f "$DOMAIN_DIR/CLAUDE.md" ]; then
    echo "ERROR: No CLAUDE.md in fixture — run /avengers-assemble first: $DOMAIN_DIR"
    exit 1
  fi

  mkdir -p "$DOMAIN_RESULTS"

  PROMPT_NUM=0
  while IFS='|' read -r axis prompt; do
    PROMPT_NUM=$((PROMPT_NUM + 1))
    PADDED=$(printf "%02d" "$PROMPT_NUM")

    echo "[$domain] Prompt $PADDED ($axis): $prompt"

    # Bare run — --bare skips CLAUDE.md and .claude/rules/ auto-discovery
    echo "  Running bare..."
    (cd "$DOMAIN_DIR" && claude -p "$prompt" --bare --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-bare.json" || true

    # Assembled run — normal mode, loads CLAUDE.md and .claude/rules/
    echo "  Running assembled..."
    (cd "$DOMAIN_DIR" && claude -p "$prompt" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-assembled.json" || true

    echo "  Done."
    echo ""

  done < "$PROMPT_FILE"
done

echo "=== All prompts complete ==="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Next: ./score-eval.sh $RESULTS_DIR"
