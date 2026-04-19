#!/usr/bin/env bash
# Brief 15: Lenses vs Characters persona-style eval on Opus 4.7.
#
# Both conditions are FULLY ASSEMBLED — neither is bare. The only difference is
# CLAUDE.md persona-style framing (deterministically derived via build-lenses-variant.sh).
# Inherits Brief 13's harness fixes: --model claude-opus-4-7 pin, CLAUDE.md* glob hygiene.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$SCRIPT_DIR/results/lenses-vs-characters-$TIMESTAMP"

DOMAINS=("rails-api" "childrens-novel")

echo "=== Eval Suite: Lenses vs Characters (Brief 15) ==="
echo "Model: claude-opus-4-7"
echo "Results: $RESULTS_DIR"
echo ""

for domain in "${DOMAINS[@]}"; do
  CHAR_DIR="$FIXTURES_DIR/$domain"
  LENS_DIR="$FIXTURES_DIR/${domain}-lenses"
  DOMAIN_RESULTS="$RESULTS_DIR/$domain"
  PROMPT_FILE="$PROMPTS_DIR/$domain.txt"

  if [ ! -d "$CHAR_DIR" ]; then
    echo "ERROR: Characters fixture not found: $CHAR_DIR" >&2
    exit 1
  fi
  if [ ! -d "$LENS_DIR" ]; then
    echo "ERROR: Lenses fixture not found: $LENS_DIR (run build-lenses-variant.sh first)" >&2
    exit 1
  fi
  if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompts not found: $PROMPT_FILE" >&2
    exit 1
  fi
  if [ ! -f "$CHAR_DIR/CLAUDE.md" ] || [ ! -f "$LENS_DIR/CLAUDE.md" ]; then
    echo "ERROR: Both fixtures must contain CLAUDE.md" >&2
    exit 1
  fi

  mkdir -p "$DOMAIN_RESULTS"

  # Isolated temp dirs per condition — same hygiene as run-eval.sh.
  CHAR_TMPDIR=$(mktemp -d)
  LENS_TMPDIR=$(mktemp -d)

  # Copy each fixture in full. Both conditions are assembled.
  cp -r "$CHAR_DIR"/* "$CHAR_TMPDIR/" 2>/dev/null || true
  [ -d "$CHAR_DIR/.claude" ] && cp -r "$CHAR_DIR/.claude" "$CHAR_TMPDIR/"
  cp -r "$LENS_DIR"/* "$LENS_TMPDIR/" 2>/dev/null || true
  [ -d "$LENS_DIR/.claude" ] && cp -r "$LENS_DIR/.claude" "$LENS_TMPDIR/"

  echo "[$domain] Characters dir: $CHAR_TMPDIR"
  echo "[$domain] Lenses dir:     $LENS_TMPDIR"
  echo ""

  PROMPT_NUM=0
  while IFS='|' read -r axis prompt; do
    PROMPT_NUM=$((PROMPT_NUM + 1))
    PADDED=$(printf "%02d" "$PROMPT_NUM")

    echo "[$domain] Prompt $PADDED ($axis): $prompt"

    echo "  Running characters..."
    (cd "$CHAR_TMPDIR" && claude -p "$prompt" --model claude-opus-4-7 --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-characters.json" || true

    echo "  Running lenses..."
    (cd "$LENS_TMPDIR" && claude -p "$prompt" --model claude-opus-4-7 --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-lenses.json" || true

    # Persist axis label alongside results so the scorer can do per-axis aggregation.
    echo "{\"axis\": \"$axis\", \"prompt\": $(printf '%s' "$prompt" | jq -Rs .)}" \
      > "$DOMAIN_RESULTS/${PADDED}-prompt.json"

    echo "  Done."
    echo ""
  done < "$PROMPT_FILE"

  rm -rf "$CHAR_TMPDIR" "$LENS_TMPDIR"
done

echo "=== All prompts complete ==="
echo "Results: $RESULTS_DIR"
echo ""
echo "Next: ./score-lenses-vs-characters-eval.sh $RESULTS_DIR"
