#!/usr/bin/env bash
# Gate enforcement — prevents writing specs without approved design briefs,
# and writing plans without approved specs. Uses approval markers (HTML comments)
# that the blueprint skill writes at each approval point.
#
# Markers checked:
#   <!-- approved: design-brief YYYY-MM-DDTHH:MM:SS -->  (in plan file)
#   <!-- approved: spec YYYY-MM-DDTHH:MM:SS -->           (in spec file)
#   <!-- approved: plan YYYY-MM-DDTHH:MM:SS -->            (in plan doc)

INPUT=$(cat)

# Parse tool input with python3 (ships with macOS, no jq needed)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Only gate Write and Edit operations
case "$TOOL_NAME" in
  Write|Edit)
    ;;
  *)
    exit 0
    ;;
esac

# Gate 1: Writing to specs/ requires an approved design brief in the plan file
if [[ "$FILE_PATH" == *"/specs/"* && "$FILE_PATH" == *.md ]]; then
  PLAN_FILE=$(ls -t "$CLAUDE_PROJECT_DIR"/.claude/plans/*.md 2>/dev/null | head -1)
  if [[ -z "$PLAN_FILE" ]]; then
    echo '{"decision": "deny", "reason": "Gate 1: No plan file found. Run gigo:blueprint and get the design brief approved (Phase 4.5) before writing a spec."}' >&2
    exit 2
  fi
  if ! grep -q '<!-- approved: design-brief' "$PLAN_FILE" 2>/dev/null; then
    echo '{"decision": "deny", "reason": "Gate 1: Design brief not approved. The operator must approve the design brief (Phase 4.5) before a spec can be written."}' >&2
    exit 2
  fi
  if ! grep -q '<!-- approved: design-brief.*by:' "$PLAN_FILE" 2>/dev/null; then
    echo '{"decision": "deny", "reason": "Gate 1: Design brief approval missing approver identity (by: field). Re-approve with operator name."}' >&2
    exit 2
  fi
fi

# Gate 2: Writing to plans/ (implementation plans, not .claude/plans/) requires an approved spec
if [[ "$FILE_PATH" == */docs/gigo/plans/* && "$FILE_PATH" == *.md ]]; then
  SPEC_FILE=$(ls -t "$CLAUDE_PROJECT_DIR"/docs/gigo/specs/*.md 2>/dev/null | head -1)
  if [[ -z "$SPEC_FILE" ]]; then
    echo '{"decision": "deny", "reason": "Gate 2: No spec file found. The spec must be written and approved (Phase 7) before writing an implementation plan."}' >&2
    exit 2
  fi
  if ! grep -q '<!-- approved: spec' "$SPEC_FILE" 2>/dev/null; then
    echo '{"decision": "deny", "reason": "Gate 2: Spec not approved. The operator must approve the spec (Phase 7) before an implementation plan can be written."}' >&2
    exit 2
  fi
  if ! grep -q '<!-- approved: spec.*by:' "$SPEC_FILE" 2>/dev/null; then
    echo '{"decision": "deny", "reason": "Gate 2: Spec approval missing approver identity (by: field). Re-approve with operator name."}' >&2
    exit 2
  fi
fi

# Default: allow
exit 0
