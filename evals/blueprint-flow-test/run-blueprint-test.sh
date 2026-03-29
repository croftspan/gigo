#!/usr/bin/env bash
# Blueprint Flow Test — Does gigo:blueprint follow the full pipeline?
#
# Tests the critical flow:
#   Phase 0: EnterPlanMode
#   Phases 1-4: Design work in plan mode
#   Phase 4.5: ExitPlanMode (with Post-Approval section)
#   Phase 5: Write spec (NOT start coding)
#   Phase 6-7: Self-review + Challenger + user review
#   Phase 8-10: Write implementation plan + reviews
#
# The critical assertion: after plan mode approval, the agent writes a spec
# document — it does NOT jump to writing code.
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

# Initialize git if not already (needed for blueprint to work)
if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "initial"
fi

# Create docs directories that blueprint expects
mkdir -p docs/gigo/specs docs/gigo/plans

# The feature request — non-trivial enough to need a real spec
FEATURE_REQUEST="Add a 'tq watch' command that monitors task state changes in real-time. It should stream updates to stdout as tasks transition between states (pending, running, done, failed). Support --json flag for machine-readable output. Support --filter to watch only specific task IDs or state transitions. Must handle the case where the queue file is being written to by workers concurrently."

echo "Feature request: $FEATURE_REQUEST"
echo ""
echo "--- Running gigo:blueprint (this will take a while) ---"
echo ""

# Run blueprint with the feature request
# Use --print to capture the full conversation
# Auto-approve plan mode and approvals to let the flow run
claude --print \
  --dangerously-skip-permissions \
  --max-turns 40 \
  -p "Use gigo:blueprint to plan this feature: $FEATURE_REQUEST

When asked for approval or review, approve and continue. When asked to choose between options, pick the recommended one. When asked clarifying questions, say 'your call, whatever you think is best'. The goal is to get through the full pipeline: design brief → spec → implementation plan.

IMPORTANT: After the design brief is approved via ExitPlanMode, you MUST continue to write the formal spec document. Do NOT start writing Go code. The next step after design brief approval is Phase 5: Write Spec." \
  2>"$RESULTS_DIR/stderr.log" \
  | tee "$RESULTS_DIR/full-output.md"

echo ""
echo "--- Blueprint run complete ---"
echo ""

# === GRADE THE OUTPUT ===

PASS=0
FAIL=0
WARN=0

grade() {
  local label="$1"
  local result="$2"  # pass, fail, warn
  local detail="$3"

  case "$result" in
    pass) PASS=$((PASS + 1)); echo "  ✅ $label: $detail" ;;
    fail) FAIL=$((FAIL + 1)); echo "  ❌ $label: $detail" ;;
    warn) WARN=$((WARN + 1)); echo "  ⚠️  $label: $detail" ;;
  esac
}

echo "=== Grading ==="
echo ""

# 1. Did it enter plan mode?
if grep -qi "EnterPlanMode\|entering plan mode\|plan mode" "$RESULTS_DIR/full-output.md"; then
  grade "Plan mode entry" "pass" "Found plan mode references in output"
else
  grade "Plan mode entry" "fail" "No plan mode references found"
fi

# 2. Did it create a plan file?
PLAN_FILE=$(find "$WORK_DIR/tq-project/.claude/plans" -name "*.md" 2>/dev/null | head -1)
if [ -n "$PLAN_FILE" ]; then
  grade "Plan file created" "pass" "$(basename "$PLAN_FILE")"
  cp "$PLAN_FILE" "$RESULTS_DIR/plan-file.md" 2>/dev/null || true
else
  grade "Plan file created" "fail" "No plan file found in .claude/plans/"
fi

# 3. Did the plan file contain Post-Approval section?
if [ -n "$PLAN_FILE" ] && grep -q "Post-Approval" "$PLAN_FILE" 2>/dev/null; then
  grade "Post-Approval section" "pass" "Found in plan file"
else
  grade "Post-Approval section" "fail" "Missing from plan file — transition reinforcement not written"
fi

# 4. Did it call ExitPlanMode?
if grep -qi "ExitPlanMode\|exited plan mode\|plan.*approved" "$RESULTS_DIR/full-output.md"; then
  grade "ExitPlanMode called" "pass" "Found exit/approval references"
else
  grade "ExitPlanMode called" "fail" "Never exited plan mode"
fi

# 5. THE CRITICAL TEST: Did it write a spec file?
SPEC_FILE=$(find "$WORK_DIR/tq-project/docs/gigo/specs" -name "*.md" 2>/dev/null | head -1)
if [ -n "$SPEC_FILE" ]; then
  grade "Spec file written" "pass" "$(basename "$SPEC_FILE")"
  cp "$SPEC_FILE" "$RESULTS_DIR/spec-file.md" 2>/dev/null || true
else
  grade "Spec file written" "fail" "NO SPEC FILE — agent likely jumped to coding after plan approval"
fi

# 6. Did the spec have a Conventions section?
if [ -n "$SPEC_FILE" ] && grep -qi "Conventions" "$SPEC_FILE" 2>/dev/null; then
  grade "Spec conventions" "pass" "Conventions section present"
else
  if [ -n "$SPEC_FILE" ]; then
    grade "Spec conventions" "warn" "Spec exists but no Conventions section"
  else
    grade "Spec conventions" "fail" "No spec file to check"
  fi
fi

# 7. Did it write an implementation plan?
IMPL_PLAN=$(find "$WORK_DIR/tq-project/docs/gigo/plans" -name "*.md" 2>/dev/null | head -1)
if [ -n "$IMPL_PLAN" ]; then
  grade "Implementation plan written" "pass" "$(basename "$IMPL_PLAN")"
  cp "$IMPL_PLAN" "$RESULTS_DIR/impl-plan.md" 2>/dev/null || true
else
  grade "Implementation plan written" "warn" "No implementation plan — may have run out of turns"
fi

# 8. Did it write Go code? (it shouldn't have)
GO_FILES_CHANGED=$(git diff --name-only 2>/dev/null | grep "\.go$" || true)
if [ -z "$GO_FILES_CHANGED" ]; then
  grade "No code written" "pass" "No .go files modified — correctly stayed in planning"
else
  grade "No code written" "fail" "Go files were modified: $GO_FILES_CHANGED — agent jumped to implementation!"
fi

# 9. Did it mention the Challenger?
if grep -qi "Challenger\|adversarial.*review\|spec.*challenge\|plan.*challenge" "$RESULTS_DIR/full-output.md"; then
  grade "Challenger invoked" "pass" "Found Challenger references"
else
  grade "Challenger invoked" "warn" "No Challenger references — may have been skipped for task scale"
fi

# 10. Phase ordering — did spec come before implementation plan?
if [ -n "$SPEC_FILE" ] && [ -n "$IMPL_PLAN" ]; then
  SPEC_TIME=$(stat -f %m "$SPEC_FILE" 2>/dev/null || stat -c %Y "$SPEC_FILE" 2>/dev/null)
  PLAN_TIME=$(stat -f %m "$IMPL_PLAN" 2>/dev/null || stat -c %Y "$IMPL_PLAN" 2>/dev/null)
  if [ "$SPEC_TIME" -le "$PLAN_TIME" ]; then
    grade "Phase ordering" "pass" "Spec written before implementation plan"
  else
    grade "Phase ordering" "fail" "Implementation plan written before spec!"
  fi
else
  grade "Phase ordering" "warn" "Can't check — missing one or both files"
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
**Verdict:** $VERDICT
**Pass:** $PASS | **Fail:** $FAIL | **Warn:** $WARN

## Feature Request
$FEATURE_REQUEST

## Artifacts
- Plan file: $([ -n "$PLAN_FILE" ] && echo "✅ $(basename "$PLAN_FILE")" || echo "❌ missing")
- Spec file: $([ -n "$SPEC_FILE" ] && echo "✅ $(basename "$SPEC_FILE")" || echo "❌ missing")
- Impl plan: $([ -n "$IMPL_PLAN" ] && echo "✅ $(basename "$IMPL_PLAN")" || echo "⚠️ missing")
- Go code modified: $([ -z "$GO_FILES_CHANGED" ] && echo "✅ none" || echo "❌ $GO_FILES_CHANGED")

## Critical Test: Post-Plan-Mode Transition
$([ -n "$SPEC_FILE" ] && echo "✅ Agent continued to spec writing after plan mode approval" || echo "❌ Agent did NOT write a spec — likely jumped to implementation")

## Work Directory
$WORK_DIR/tq-project
(kept for inspection — delete manually when done)
SUMMARY

echo ""
echo "Full output: $RESULTS_DIR/full-output.md"
echo "Summary: $RESULTS_DIR/summary.md"
echo "Work dir preserved: $WORK_DIR/tq-project"
