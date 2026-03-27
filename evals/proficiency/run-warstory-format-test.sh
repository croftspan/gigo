#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/../fixtures"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$SCRIPT_DIR/results/$TIMESTAMP"

mkdir -p "$RESULTS_DIR/rails-api"

RAILS_FIXTURE="$FIXTURES_DIR/rails-api"
RAILS_PROMPT=$(cat "$PROMPTS_DIR/rails.md")

echo "=== War Story Format Experiment ==="
echo "Results: $RESULTS_DIR"
echo ""
echo "Variants:"
echo "  1. bare — no context"
echo "  2. warstories — full narrative (proven 20/20 baseline)"
echo "  3. compressed — trigger → consequence → fix"
echo "  4. fixonly — just the rules, no story"
echo ""

# --- Variant: bare ---
BARE_TMPDIR=$(mktemp -d)
echo "[bare] Dir: $BARE_TMPDIR"
echo "[bare] Running..."
(cd "$BARE_TMPDIR" && claude -p "$RAILS_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
  > "$RESULTS_DIR/rails-api/bare.json" || true
rm -rf "$BARE_TMPDIR"
echo "[bare] Done."
echo ""

# --- Helper: set up assembled dir with a specific standards.md variant ---
run_variant() {
  local VARIANT_NAME="$1"
  local STANDARDS_FILE="$2"

  local TMPDIR
  TMPDIR=$(mktemp -d)

  # Copy full fixture
  cp "$RAILS_FIXTURE/CLAUDE.md" "$TMPDIR/"
  cp -r "$RAILS_FIXTURE/.claude" "$TMPDIR/"

  # Swap in the variant standards.md
  cp "$STANDARDS_FILE" "$TMPDIR/.claude/rules/standards.md"

  echo "[$VARIANT_NAME] Dir: $TMPDIR"
  echo "[$VARIANT_NAME] Running..."
  (cd "$TMPDIR" && claude -p "$RAILS_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
    > "$RESULTS_DIR/rails-api/$VARIANT_NAME.json" || true
  rm -rf "$TMPDIR"
  echo "[$VARIANT_NAME] Done."
  echo ""
}

# --- Variant: warstories (full narrative) ---
run_variant "warstories" "$RAILS_FIXTURE/.claude/rules/standards.md.warstories"

# --- Variant: compressed ---
run_variant "compressed" "$RAILS_FIXTURE/.claude/rules/standards.md.compressed"

# --- Variant: fixonly ---
run_variant "fixonly" "$RAILS_FIXTURE/.claude/rules/standards.md.fixonly"

echo "=== All variants complete ==="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Next: ./score-warstory-format-test.sh $RESULTS_DIR"
