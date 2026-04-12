#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$EVALS_DIR")"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"

mkdir -p "$RESULTS_DIR"

echo "=== Agent Teams Cleanup Verification ==="
echo ""

CHECKS_PASSED=0
CHECKS_TOTAL=5
DETAILS=""

# Check 1: No Tier 3 in execute SKILL.md production sections
TIER3_HITS=$(grep -c "Tier 3" "$PROJECT_DIR/skills/execute/SKILL.md" 2>/dev/null) || TIER3_HITS=0
if [ "$TIER3_HITS" -eq 0 ]; then
  echo "  Check 1: No 'Tier 3' in SKILL.md              [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 1, \"name\": \"no_tier3\", \"clean\": true},"
else
  echo "  Check 1: 'Tier 3' found in SKILL.md ($TIER3_HITS hits) [DIRTY]"
  DETAILS="$DETAILS{\"check\": 1, \"name\": \"no_tier3\", \"clean\": false, \"hits\": $TIER3_HITS},"
fi

# Check 2: No TeamCreate or team-scoped SendMessage in SKILL.md
TEAM_API_HITS=$(grep -cE "TeamCreate|SendMessage.*team" "$PROJECT_DIR/skills/execute/SKILL.md" 2>/dev/null) || TEAM_API_HITS=0
if [ "$TEAM_API_HITS" -eq 0 ]; then
  echo "  Check 2: No TeamCreate/SendMessage in SKILL.md [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 2, \"name\": \"no_team_api\", \"clean\": true},"
else
  echo "  Check 2: Team API refs in SKILL.md ($TEAM_API_HITS hits) [DIRTY]"
  DETAILS="$DETAILS{\"check\": 2, \"name\": \"no_team_api\", \"clean\": false, \"hits\": $TEAM_API_HITS},"
fi

# Check 3: No Tier 3 templates in teammate-prompts.md
TEMPLATE_HITS=$(grep -cE "Tier 3|team\.prompt|team\.template" "$PROJECT_DIR/skills/execute/references/teammate-prompts.md" 2>/dev/null) || TEMPLATE_HITS=0
if [ "$TEMPLATE_HITS" -eq 0 ]; then
  echo "  Check 3: No Tier 3 templates in prompts         [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 3, \"name\": \"no_tier3_templates\", \"clean\": true},"
else
  echo "  Check 3: Tier 3 templates found ($TEMPLATE_HITS hits)  [DIRTY]"
  DETAILS="$DETAILS{\"check\": 3, \"name\": \"no_tier3_templates\", \"clean\": false, \"hits\": $TEMPLATE_HITS},"
fi

# Check 4: Design doc exists with status banner
DESIGN_DOC="$PROJECT_DIR/skills/execute/references/agent-teams-design.md"
if [ -f "$DESIGN_DOC" ]; then
  HAS_BANNER=$(head -10 "$DESIGN_DOC" | grep -ciE "not shipped|target.state" 2>/dev/null) || HAS_BANNER=0
  if [ "$HAS_BANNER" -gt 0 ]; then
    echo "  Check 4: Design doc exists with status banner    [CLEAN]"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    DETAILS="$DETAILS{\"check\": 4, \"name\": \"design_doc\", \"clean\": true},"
  else
    echo "  Check 4: Design doc exists but no status banner  [DIRTY]"
    DETAILS="$DETAILS{\"check\": 4, \"name\": \"design_doc\", \"clean\": false, \"reason\": \"no_banner\"},"
  fi
else
  echo "  Check 4: Design doc missing                     [DIRTY]"
  DETAILS="$DETAILS{\"check\": 4, \"name\": \"design_doc\", \"clean\": false, \"reason\": \"missing\"},"
fi

# Check 5: No AGENT_TEAMS env var in SKILL.md
ENV_HITS=$(grep -cE "AGENT_TEAMS|EXPERIMENTAL_AGENT" "$PROJECT_DIR/skills/execute/SKILL.md" 2>/dev/null) || ENV_HITS=0
if [ "$ENV_HITS" -eq 0 ]; then
  echo "  Check 5: No AGENT_TEAMS env var in SKILL.md     [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 5, \"name\": \"no_env_var\", \"clean\": true}"
else
  echo "  Check 5: AGENT_TEAMS env var found ($ENV_HITS hits) [DIRTY]"
  DETAILS="$DETAILS{\"check\": 5, \"name\": \"no_env_var\", \"clean\": false, \"hits\": $ENV_HITS}"
fi

echo ""
if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
  echo "Agent Teams Cleanup: $CHECKS_PASSED/$CHECKS_TOTAL checks   [PASS $CHECKS_TOTAL/$CHECKS_TOTAL]"
  RESULT="PASS"
else
  echo "Agent Teams Cleanup: $CHECKS_PASSED/$CHECKS_TOTAL checks   [FAIL $CHECKS_TOTAL/$CHECKS_TOTAL]"
  RESULT="FAIL"
fi

echo "{\"test\": \"cleanup-verify\", \"passed\": $CHECKS_PASSED, \"total\": $CHECKS_TOTAL, \"result\": \"$RESULT\", \"details\": [$DETAILS]}" > "$RESULTS_DIR/cleanup-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
