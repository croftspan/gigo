#!/usr/bin/env bash
# Deterministically build one context-dosing variant from a source fixture.
#
# Usage: build-variant.sh <source-fixture-dir> <condition> <dest-tmpdir>
#
# Conditions:
#   c0-bare           Source files only. No CLAUDE.md*, no .claude/.
#   c1-roster         Copy all; replace CLAUDE.md with a roster extraction
#                     (persona names + "Modeled after:" paragraphs only).
#   c2-team-no-rules  Copy all; delete .claude/rules/ and .claude/references/.
#                     Keep CLAUDE.md intact.
#   c3-full           Copy all, unchanged. Equivalent to Brief 13 assembled.
#   c4-rules-only     Copy all; delete CLAUDE.md* (keep .claude/).
#
# Must be a pure function of the source fixture — no timestamps, no randomness.
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <source-fixture-dir> <condition> <dest-tmpdir>" >&2
  exit 2
fi

SRC="$1"
COND="$2"
DEST="$3"

if [ ! -d "$SRC" ]; then
  echo "ERROR: Source not found: $SRC" >&2
  exit 1
fi
if [ ! -f "$SRC/CLAUDE.md" ]; then
  echo "ERROR: No CLAUDE.md in source: $SRC" >&2
  exit 1
fi

mkdir -p "$DEST"

# Base copy: non-CLAUDE.md* source files plus .claude/ if present.
copy_all_source() {
  # Non-dotfile top-level entries
  for f in "$SRC"/*; do
    fname=$(basename "$f")
    case "$fname" in
      CLAUDE.md*) ;;  # handled per-condition below
      *) cp -r "$f" "$DEST/" 2>/dev/null || true ;;
    esac
  done
  # .claude/ tree if present
  if [ -d "$SRC/.claude" ]; then
    cp -r "$SRC/.claude" "$DEST/" 2>/dev/null || true
  fi
}

# Extract roster-only content from a full CLAUDE.md.
# Keeps: everything before "## The Team", "## The Team" heading, and
# per-persona (### Name) + **Modeled after:** paragraphs.
# Strips: Owns/Quality bar/Won't do bullets, Autonomy Model, Quick Reference,
# and any other ## sections after The Team.
extract_roster() {
  local input="$1"
  local output="$2"
  # Paragraph-mode awk. Keeps header content, "## The Team" heading, and for
  # each persona: the "### Name" header + the first (stem) line of the
  # "**Modeled after:**" paragraph. Strips Owns/Quality-bar/Wont-do,
  # Autonomy Model, Quick Reference, and "+ continuation" lines on the
  # Modeled-after block (one-liner only, per brief 14 spec).
  awk '
    BEGIN { RS = ""; ORS = "\n\n"; team_started = 0; team_ended = 0 }
    {
      if (team_ended) next
      if (!team_started) {
        print
        if ($0 ~ /^## The Team/) team_started = 1
        next
      }
      if ($0 ~ /^## / && $0 !~ /^## The Team/) { team_ended = 1; next }
      if ($0 ~ /^### /) { print; next }
      if ($0 ~ /^\*\*Modeled after:\*\*/) {
        n = split($0, lines, "\n")
        print lines[1]
        next
      }
    }
  ' "$input" > "$output"
}

case "$COND" in
  c0-bare)
    # Copy only non-CLAUDE.md* top-level entries. Skip .claude/ entirely.
    for f in "$SRC"/*; do
      fname=$(basename "$f")
      case "$fname" in
        CLAUDE.md*) ;;
        *) cp -r "$f" "$DEST/" 2>/dev/null || true ;;
      esac
    done
    # Explicit: no .claude/ (should already be absent since * is non-dotfile)
    rm -rf "$DEST/.claude"
    ;;

  c1-roster)
    copy_all_source
    extract_roster "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"
    ;;

  c2-team-no-rules)
    copy_all_source
    cp "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"
    rm -rf "$DEST/.claude/rules"
    rm -rf "$DEST/.claude/references"
    ;;

  c3-full)
    copy_all_source
    cp "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"
    ;;

  c4-rules-only)
    copy_all_source
    # No CLAUDE.md* (copy_all_source already skipped it)
    # Ensure none snuck in
    for f in "$DEST"/CLAUDE.md*; do
      [ -e "$f" ] && rm -f "$f"
    done
    ;;

  *)
    echo "ERROR: Unknown condition: $COND" >&2
    echo "Expected one of: c0-bare c1-roster c2-team-no-rules c3-full c4-rules-only" >&2
    exit 2
    ;;
esac

# Sanity report to stderr (doesn't pollute stdout for callers)
{
  file_count=$(find "$DEST" -type f | wc -l | tr -d ' ')
  if [ -f "$DEST/CLAUDE.md" ]; then
    claude_md_bytes=$(wc -c < "$DEST/CLAUDE.md" | tr -d ' ')
  else
    claude_md_bytes=0
  fi
  if [ -d "$DEST/.claude/rules" ]; then
    rules_files=$(find "$DEST/.claude/rules" -type f -name "*.md" | wc -l | tr -d ' ')
  else
    rules_files=0
  fi
  if [ -d "$DEST/.claude/references" ]; then
    ref_files=$(find "$DEST/.claude/references" -type f -name "*.md" | wc -l | tr -d ' ')
  else
    ref_files=0
  fi
  echo "[variant] cond=$COND files=$file_count CLAUDE.md=${claude_md_bytes}b rules=${rules_files} refs=${ref_files}"
} >&2
