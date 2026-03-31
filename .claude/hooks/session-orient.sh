#!/usr/bin/env bash
# Session orientation — reminds Claude which project it's in at session start.
# Prevents wrong-context starts (reading wrong CLAUDE.md, stale directories).

PROJECT_NAME=$(basename "$CLAUDE_PROJECT_DIR")

# Check for key project markers to give Claude more specific context
MARKERS=""
if [[ -f "$CLAUDE_PROJECT_DIR/CLAUDE.md" ]]; then
  # Extract first non-empty, non-heading line as project description
  DESC=$(grep -m1 '^[^#]' "$CLAUDE_PROJECT_DIR/CLAUDE.md" | head -c 120 | sed 's/\\/\\\\/g; s/"/\\"/g')
  if [[ -n "$DESC" ]]; then
    MARKERS=" Project: $DESC"
  fi
fi

cat <<EOF
{"systemMessage": "Context check: You are in project '$PROJECT_NAME' at $CLAUDE_PROJECT_DIR.${MARKERS} Confirm this matches the user's intent before starting work."}
EOF
