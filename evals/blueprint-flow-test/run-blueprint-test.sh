#!/usr/bin/env bash
# Blueprint Flow Test — Does gigo:blueprint follow the full pipeline?
#
# Tests the critical flow after plan mode exit:
#   After ExitPlanMode approval, does the agent write a spec (not code)?
#
# Uses --resume to simulate multi-turn interaction:
#   Turn 1: gigo:blueprint enters plan mode, does design, calls ExitPlanMode
#   Turn 2: User "approves" and tells agent to continue to Phase 5
#   Grading: Check artifacts (spec file, no Go code, phase ordering)
#
# Usage: ./run-blueprint-test.sh [test-project-dir]
# Default test project: ../integration-test/tq-project

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEST_PROJECT="${1:-$SCRIPT_DIR/../integration-test/tq-project}"
RESULTS_DIR="$SCRIPT_DIR/results/$(date +%Y-%m-%d-%H%M%S)"
WORK_DIR=$(mktemp -d)

echo "=== Blueprint Flow Test ==="
echo "Test project: $TEST_PROJECT"
echo "Results dir: $RESULTS_DIR"
echo "Work dir: $WORK_DIR"
echo ""

mkdir -p "$RESULTS_DIR"

# Copy test project to a temp working directory so we don't pollute it
cp -r "$TEST_PROJECT" "$WORK_DIR/tq-project"
cd "$WORK_DIR/tq-project"

# Initialize git if not already
if [ ! -d .git ]; then
  git init -b main
  git add -A
  git commit -m "initial"
fi

# Create docs directories
mkdir -p docs/gigo/specs docs/gigo/plans .claude/plans

# Snapshot pre-existing files to distinguish from new ones
find docs/gigo/specs -name "*.md" > "$RESULTS_DIR/pre-existing-specs.txt" 2>/dev/null || true
find docs/gigo/plans -name "*.md" > "$RESULTS_DIR/pre-existing-plans.txt" 2>/dev/null || true

# The feature request
FEATURE_REQUEST="Add a 'tq watch' command that monitors task state changes in real-time. It should stream updates to stdout as tasks transition between states (pending, running, done, failed). Support --json flag for machine-readable output. Support --filter to watch only specific task IDs or state transitions. Must handle the case where the queue file is being written to by workers concurrently."

echo "Feature request: $FEATURE_REQUEST"
echo ""

# === TURN 1: Enter plan mode, do design, call ExitPlanMode ===
echo "--- Turn 1: Design phase in plan mode ---"
echo ""

SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

claude --print \
  --verbose \
  --output-format stream-json \
  --permission-mode auto \
  --session-id "$SESSION_ID" \
  --max-turns 30 \
  -p "Use gigo:blueprint to plan this feature: $FEATURE_REQUEST

When asked clarifying questions, say 'your call, whatever you think is best'. When asked to choose between approaches, pick the recommended one.

Your job in this turn is to complete the design phase (Phases 0-4) and call ExitPlanMode with the design brief." \
  > "$RESULTS_DIR/turn1-stream.jsonl" \
  2>"$RESULTS_DIR/turn1-stderr.log"

echo ""
echo "--- Turn 1 complete ---"
echo ""

# Check if plan file was created
PLAN_FILE=$(find "$WORK_DIR/tq-project/.claude/plans" -name "*.md" 2>/dev/null | head -1)
if [ -z "$PLAN_FILE" ]; then
  # Also check ~/.claude/plans/ in case it wrote there
  PLAN_FILE=$(find "$HOME/.claude/plans" -name "*.md" -newer "$RESULTS_DIR/turn1-stream.jsonl" 2>/dev/null | head -1)
fi

echo "Plan file: ${PLAN_FILE:-not found}"
echo ""

# === TURN 2: Resume and continue to spec writing ===
echo "--- Turn 2: Continue to spec and implementation plan ---"
echo ""

claude --print \
  --verbose \
  --output-format stream-json \
  --permission-mode auto \
  --resume "$SESSION_ID" \
  --max-turns 30 \
  -p "Design brief approved. Now continue with the gigo:blueprint pipeline:

Phase 5: Write the formal spec document to docs/gigo/specs/
Phase 6: Self-review the spec
Phase 6.5: Run the Challenger adversarial review
Phase 7: I approve the spec (pre-approved, continue)
Phase 8: Write the implementation plan to docs/gigo/plans/
Phase 9: Self-review the plan

Do NOT write Go code. Write the spec and implementation plan documents only.
Read the design brief from the plan file and formalize it." \
  > "$RESULTS_DIR/turn2-stream.jsonl" \
  2>"$RESULTS_DIR/turn2-stderr.log"

echo ""
echo "--- Turn 2 complete ---"
echo ""

# === GRADE THE OUTPUT ===

PASS=0
FAIL=0
WARN=0

grade() {
  local label="$1"
  local result="$2"
  local detail="$3"

  case "$result" in
    pass) PASS=$((PASS + 1)); echo "  ✅ $label: $detail" ;;
    fail) FAIL=$((FAIL + 1)); echo "  ❌ $label: $detail" ;;
    warn) WARN=$((WARN + 1)); echo "  ⚠️  $label: $detail" ;;
  esac
}

echo "=== Grading ==="
echo ""

# 1. Did it enter plan mode in turn 1?
if grep -q "EnterPlanMode" "$RESULTS_DIR/turn1-stream.jsonl" 2>/dev/null; then
  grade "Plan mode entry" "pass" "EnterPlanMode called in turn 1"
else
  grade "Plan mode entry" "warn" "No EnterPlanMode found in stream"
fi

# 2. Did it create a plan file?
if [ -n "$PLAN_FILE" ] && [ -f "$PLAN_FILE" ]; then
  grade "Plan file created" "pass" "$(basename "$PLAN_FILE")"
  cp "$PLAN_FILE" "$RESULTS_DIR/plan-file.md" 2>/dev/null || true
else
  grade "Plan file created" "warn" "No plan file found"
fi

# 3. Post-Approval section in plan file?
if [ -n "$PLAN_FILE" ] && [ -f "$PLAN_FILE" ] && grep -q "Post-Approval" "$PLAN_FILE" 2>/dev/null; then
  grade "Post-Approval section" "pass" "Found in plan file"
elif [ -n "$PLAN_FILE" ] && [ -f "$PLAN_FILE" ]; then
  grade "Post-Approval section" "fail" "Plan file exists but missing Post-Approval section"
else
  grade "Post-Approval section" "warn" "No plan file to check"
fi

# 4. Did it call ExitPlanMode?
if grep -q "ExitPlanMode" "$RESULTS_DIR/turn1-stream.jsonl" 2>/dev/null; then
  grade "ExitPlanMode called" "pass" "Found in turn 1"
else
  grade "ExitPlanMode called" "fail" "Never exited plan mode"
fi

# 5. THE CRITICAL TEST: Did turn 2 write a NEW spec file?
NEW_SPEC=""
for f in $(find "$WORK_DIR/tq-project/docs/gigo/specs" -name "*.md" 2>/dev/null); do
  if ! grep -qF "$(basename "$f")" "$RESULTS_DIR/pre-existing-specs.txt" 2>/dev/null; then
    NEW_SPEC="$f"
    break
  fi
done

if [ -n "$NEW_SPEC" ]; then
  grade "NEW spec file written (CRITICAL)" "pass" "$(basename "$NEW_SPEC")"
  cp "$NEW_SPEC" "$RESULTS_DIR/spec-file.md" 2>/dev/null || true
else
  grade "NEW spec file written (CRITICAL)" "fail" "No new spec file — agent did not continue to Phase 5 after plan approval"
fi

# 6. Spec has Conventions section?
if [ -n "$NEW_SPEC" ] && grep -qi "Conventions" "$NEW_SPEC" 2>/dev/null; then
  grade "Spec conventions" "pass" "Conventions section present"
elif [ -n "$NEW_SPEC" ]; then
  grade "Spec conventions" "warn" "Spec exists but no Conventions section"
else
  grade "Spec conventions" "fail" "No new spec to check"
fi

# 7. Did it write a NEW implementation plan?
NEW_PLAN=""
for f in $(find "$WORK_DIR/tq-project/docs/gigo/plans" -name "*.md" 2>/dev/null); do
  if ! grep -qF "$(basename "$f")" "$RESULTS_DIR/pre-existing-plans.txt" 2>/dev/null; then
    NEW_PLAN="$f"
    break
  fi
done

if [ -n "$NEW_PLAN" ]; then
  grade "NEW implementation plan written" "pass" "$(basename "$NEW_PLAN")"
  cp "$NEW_PLAN" "$RESULTS_DIR/impl-plan.md" 2>/dev/null || true
else
  grade "Implementation plan written" "warn" "No new implementation plan — may have run out of turns"
fi

# 8. Did it write Go code? (it shouldn't have)
GO_CHANGES=$(git diff --name-only 2>/dev/null | grep "\.go$" || true)
NEW_GO=$(git status --porcelain 2>/dev/null | grep "\.go$" || true)
if [ -z "$GO_CHANGES" ] && [ -z "$NEW_GO" ]; then
  grade "No code written" "pass" "No .go files modified — correctly stayed in planning"
else
  grade "No code written" "fail" "Go files were modified: ${GO_CHANGES}${NEW_GO} — agent jumped to implementation!"
fi

# 9. Challenger referenced?
if grep -qi "Challenger\|adversarial.*review\|Phase 6.5\|Phase 9.5" "$RESULTS_DIR/turn2-stream.jsonl" 2>/dev/null; then
  grade "Challenger referenced" "pass" "Found Challenger references in turn 2"
else
  grade "Challenger referenced" "warn" "No Challenger references — may have been skipped"
fi

# 10. Phase ordering
if [ -n "$NEW_SPEC" ] && [ -n "$NEW_PLAN" ]; then
  SPEC_TIME=$(stat -f %m "$NEW_SPEC" 2>/dev/null || stat -c %Y "$NEW_SPEC" 2>/dev/null)
  PLAN_TIME=$(stat -f %m "$NEW_PLAN" 2>/dev/null || stat -c %Y "$NEW_PLAN" 2>/dev/null)
  if [ "$SPEC_TIME" -le "$PLAN_TIME" ]; then
    grade "Phase ordering" "pass" "Spec written before implementation plan"
  else
    grade "Phase ordering" "fail" "Implementation plan written before spec!"
  fi
elif [ -n "$NEW_SPEC" ]; then
  grade "Phase ordering" "pass" "Spec written (impl plan not reached — acceptable)"
else
  grade "Phase ordering" "warn" "Can't check — missing spec"
fi

echo ""
echo "=== Results ==="
echo "  Pass: $PASS"
echo "  Fail: $FAIL"
echo "  Warn: $WARN"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo "✅ BLUEPRINT FLOW TEST PASSED"
  VERDICT="PASS"
else
  echo "❌ BLUEPRINT FLOW TEST FAILED — $FAIL critical failures"
  VERDICT="FAIL"
fi

# Save summary
cat > "$RESULTS_DIR/summary.md" << SUMMARY
# Blueprint Flow Test Results

**Date:** $(date)
**Session ID:** $SESSION_ID
**Verdict:** $VERDICT
**Pass:** $PASS | **Fail:** $FAIL | **Warn:** $WARN

## Feature Request
$FEATURE_REQUEST

## Artifacts
- Plan file: $([ -n "${PLAN_FILE:-}" ] && [ -f "${PLAN_FILE:-}" ] && echo "✅ $(basename "$PLAN_FILE")" || echo "⚠️ missing")
- New spec: $([ -n "${NEW_SPEC:-}" ] && echo "✅ $(basename "$NEW_SPEC")" || echo "❌ missing")
- New impl plan: $([ -n "${NEW_PLAN:-}" ] && echo "✅ $(basename "$NEW_PLAN")" || echo "⚠️ missing")
- Go code modified: $([ -z "${GO_CHANGES:-}${NEW_GO:-}" ] && echo "✅ none" || echo "❌ yes")

## Critical Test: Post-Plan-Mode Transition
$([ -n "${NEW_SPEC:-}" ] && echo "✅ Agent wrote a NEW spec after plan mode approval" || echo "❌ Agent did NOT write a new spec after plan mode approval")

## Work Directory
$WORK_DIR/tq-project
SUMMARY

echo ""
echo "Turn 1 stream: $RESULTS_DIR/turn1-stream.jsonl"
echo "Turn 2 stream: $RESULTS_DIR/turn2-stream.jsonl"
echo "Summary: $RESULTS_DIR/summary.md"
echo "Work dir: $WORK_DIR/tq-project"
