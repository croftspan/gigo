#!/usr/bin/env bash
# Deterministically build a Lenses-style variant from a Characters-style fixture.
#
# Usage: build-lenses-variant.sh <source-characters-fixture-dir> <dest-lenses-fixture-dir>
#
# Transforms CLAUDE.md only. Per Brief 15, .claude/rules/ and .claude/references/
# are copied unmodified — the eval isolates persona-style framing in CLAUDE.md.
#
# CLAUDE.md transformations (no others):
#   1. "## The Team" heading -> "## The Lenses"
#   2. "### {Name} — The {Role}" persona heading -> "### {Role}"
#      (drops the character name and the leading "The")
#   3. Any "- **Personality:** ..." bullet line is stripped
#      (Personality fields belong only to Characters style — none in current fixtures,
#       included defensively in case future fixtures add it)
#
# Must be a pure function of the source: identical inputs produce identical outputs.
# Exits non-zero if the source doesn't have the expected Characters structure.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <source-characters-fixture-dir> <dest-lenses-fixture-dir>" >&2
  exit 2
fi

SRC="$1"
DEST="$2"

[ -d "$SRC" ] || { echo "ERROR: source not found: $SRC" >&2; exit 1; }
[ -f "$SRC/CLAUDE.md" ] || { echo "ERROR: no CLAUDE.md in $SRC" >&2; exit 1; }

# Structural checks: must look like a Characters-style fixture.
grep -q "^## The Team" "$SRC/CLAUDE.md" \
  || { echo "ERROR: source CLAUDE.md missing '## The Team' section" >&2; exit 1; }
grep -qE "^### .+ — The " "$SRC/CLAUDE.md" \
  || { echo "ERROR: source CLAUDE.md missing any '### {Name} — The {Role}' persona heading" >&2; exit 1; }

# Reset destination so the build is pure.
rm -rf "$DEST"
mkdir -p "$DEST"

# Copy non-CLAUDE.md top-level entries, plus .claude/ tree.
for f in "$SRC"/*; do
  fname=$(basename "$f")
  case "$fname" in
    CLAUDE.md*) ;;  # we write CLAUDE.md ourselves; ignore variants like .original/.firstperson
    *) cp -r "$f" "$DEST/" ;;
  esac
done
if [ -d "$SRC/.claude" ]; then
  cp -r "$SRC/.claude" "$DEST/"
fi

# Transform CLAUDE.md. Pure-text awk; works under BSD awk (macOS default).
awk '
{
  if ($0 ~ /^## The Team[[:space:]]*$/) {
    print "## The Lenses"
    next
  }
  if ($0 ~ /^### .+ — The /) {
    sub(/^### .+ — The /, "### ")
    print
    next
  }
  if ($0 ~ /^- \*\*Personality:\*\* /) {
    next
  }
  print
}
' "$SRC/CLAUDE.md" > "$DEST/CLAUDE.md"

# Verify the transform actually did something — guard against silent identity copies.
if cmp -s "$SRC/CLAUDE.md" "$DEST/CLAUDE.md"; then
  echo "ERROR: transform produced an identical CLAUDE.md — source did not match Characters pattern" >&2
  exit 1
fi
if grep -q "^## The Team" "$DEST/CLAUDE.md"; then
  echo "ERROR: '## The Team' still present in destination CLAUDE.md" >&2
  exit 1
fi
if grep -qE "^### .+ — The " "$DEST/CLAUDE.md"; then
  echo "ERROR: '### {Name} — The {Role}' pattern still present in destination CLAUDE.md" >&2
  exit 1
fi

# Sanity report (stderr — keeps stdout clean for callers).
{
  src_bytes=$(wc -c < "$SRC/CLAUDE.md" | tr -d ' ')
  dest_bytes=$(wc -c < "$DEST/CLAUDE.md" | tr -d ' ')
  src_personas=$(grep -cE "^### " "$SRC/CLAUDE.md" || true)
  dest_personas=$(grep -cE "^### " "$DEST/CLAUDE.md" || true)
  src_authorities=$(grep -c "Modeled after" "$SRC/CLAUDE.md" || true)
  dest_authorities=$(grep -c "Modeled after" "$DEST/CLAUDE.md" || true)
  echo "[lenses-variant] $SRC -> $DEST"
  echo "  CLAUDE.md bytes: $src_bytes -> $dest_bytes"
  echo "  personas: $src_personas -> $dest_personas (must match)"
  echo "  authorities: $src_authorities -> $dest_authorities (must match)"
} >&2
