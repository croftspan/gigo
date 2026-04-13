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
    echo "ERROR: No CLAUDE.md in fixture — run /gigo first: $DOMAIN_DIR"
    exit 1
  fi

  mkdir -p "$DOMAIN_RESULTS"

  # Create isolated temp directories to prevent parent project context leaking in
  BARE_TMPDIR=$(mktemp -d)
  ASSEMBLED_TMPDIR=$(mktemp -d)

  # Copy source files to both (excluding .claude/ and CLAUDE.md for bare)
  cp -r "$DOMAIN_DIR"/* "$ASSEMBLED_TMPDIR/" 2>/dev/null || true
  cp -r "$DOMAIN_DIR"/.claude "$ASSEMBLED_TMPDIR/" 2>/dev/null || true

  # Bare gets source files only — no .claude/ or CLAUDE.md*
  for f in "$DOMAIN_DIR"/*; do
    fname=$(basename "$f")
    case "$fname" in
      CLAUDE.md*) continue ;;
    esac
    cp -r "$f" "$BARE_TMPDIR/" 2>/dev/null || true
  done

  echo "[$domain] Bare dir: $BARE_TMPDIR"
  echo "[$domain] Assembled dir: $ASSEMBLED_TMPDIR"
  echo ""

  PROMPT_NUM=0
  while IFS='|' read -r axis prompt; do
    PROMPT_NUM=$((PROMPT_NUM + 1))
    PADDED=$(printf "%02d" "$PROMPT_NUM")

    echo "[$domain] Prompt $PADDED ($axis): $prompt"

    # Bare run — temp dir with no CLAUDE.md or .claude/
    echo "  Running bare..."
    (cd "$BARE_TMPDIR" && claude -p "$prompt" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-bare.json" || true

    # Assembled run — temp dir with CLAUDE.md and .claude/rules/
    echo "  Running assembled..."
    (cd "$ASSEMBLED_TMPDIR" && claude -p "$prompt" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-assembled.json" || true

    echo "  Done."
    echo ""

  done < "$PROMPT_FILE"

  # Cleanup temp dirs
  rm -rf "$BARE_TMPDIR" "$ASSEMBLED_TMPDIR"
done

echo "=== All prompts complete ==="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Next: ./score-eval.sh $RESULTS_DIR"
