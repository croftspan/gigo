#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/../fixtures"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$SCRIPT_DIR/results/$TIMESTAMP"

mkdir -p "$RESULTS_DIR"

echo "=== Proficiency Test: Assembled vs Bare ==="
echo "Results: $RESULTS_DIR"
echo ""

# --- Rails Domain ---
RAILS_FIXTURE="$FIXTURES_DIR/rails-api"
RAILS_PROMPT=$(cat "$PROMPTS_DIR/rails.md")
RAILS_RESULTS="$RESULTS_DIR/rails-api"
mkdir -p "$RAILS_RESULTS"

BARE_TMPDIR=$(mktemp -d)
ASSEMBLED_TMPDIR=$(mktemp -d)

# Assembled gets CLAUDE.md + .claude/ from fixture
cp "$RAILS_FIXTURE/CLAUDE.md" "$ASSEMBLED_TMPDIR/"
cp -r "$RAILS_FIXTURE/.claude" "$ASSEMBLED_TMPDIR/"

echo "[rails-api] Bare dir: $BARE_TMPDIR"
echo "[rails-api] Assembled dir: $ASSEMBLED_TMPDIR"
echo ""

echo "[rails-api] Running bare..."
(cd "$BARE_TMPDIR" && claude -p "$RAILS_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
  > "$RAILS_RESULTS/bare.json" || true
echo "[rails-api] Running assembled..."
(cd "$ASSEMBLED_TMPDIR" && claude -p "$RAILS_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
  > "$RAILS_RESULTS/assembled.json" || true
echo "[rails-api] Done."
echo ""

rm -rf "$BARE_TMPDIR" "$ASSEMBLED_TMPDIR"

# --- Novel Domain ---
NOVEL_FIXTURE="$FIXTURES_DIR/childrens-novel"
NOVEL_PROMPT=$(cat "$PROMPTS_DIR/novel.md")
NOVEL_RESULTS="$RESULTS_DIR/childrens-novel"
mkdir -p "$NOVEL_RESULTS"

BARE_TMPDIR=$(mktemp -d)
ASSEMBLED_TMPDIR=$(mktemp -d)

# Assembled gets CLAUDE.md + .claude/ from fixture
cp "$NOVEL_FIXTURE/CLAUDE.md" "$ASSEMBLED_TMPDIR/"
cp -r "$NOVEL_FIXTURE/.claude" "$ASSEMBLED_TMPDIR/"

echo "[childrens-novel] Bare dir: $BARE_TMPDIR"
echo "[childrens-novel] Assembled dir: $ASSEMBLED_TMPDIR"
echo ""

echo "[childrens-novel] Running bare..."
(cd "$BARE_TMPDIR" && claude -p "$NOVEL_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
  > "$NOVEL_RESULTS/bare.json" || true
echo "[childrens-novel] Running assembled..."
(cd "$ASSEMBLED_TMPDIR" && claude -p "$NOVEL_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
  > "$NOVEL_RESULTS/assembled.json" || true
echo "[childrens-novel] Done."
echo ""

rm -rf "$BARE_TMPDIR" "$ASSEMBLED_TMPDIR"

echo "=== All prompts complete ==="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Next: ./score-proficiency.sh $RESULTS_DIR"
