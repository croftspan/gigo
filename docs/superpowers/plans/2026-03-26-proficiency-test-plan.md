# Proficiency Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a substance-based proficiency test that grades bare vs assembled outputs on objective criteria — automated structural checks + LLM rubric with specific yes/no questions.

**Architecture:** Two prompt files (Rails, Novel), a runner script that generates outputs, and a scorer script that runs automated checks then LLM rubric checks independently on each output. Scores out of 20 per domain.

**Tech Stack:** Bash scripts, jq, Claude CLI (`claude -p`), existing eval fixtures for assembled context.

---

### Task 1: Create prompt files

**Files:**
- Create: `evals/proficiency/prompts/rails.md`
- Create: `evals/proficiency/prompts/novel.md`

- [ ] **Step 1: Create the Rails prompt file**

Create `evals/proficiency/prompts/rails.md`:

```markdown
Build a JSON API for a library book reservation system. Ruby on Rails. PostgreSQL.

**Models:**
- Book (title, author, isbn, copies_available:integer)
- User (name, email)
- Reservation (user_id, book_id, reserved_at, expires_at, status: pending/active/expired/cancelled)

**Endpoints:**
- POST /reservations — reserve a book for a user (decrement copies_available, set 48h expiry)
- GET /users/:id/reservations — list a user's reservations (paginated)
- DELETE /reservations/:id — cancel a reservation (increment copies_available back)

**Business rules:**
- Can't reserve a book with 0 copies_available
- Can't have two active reservations for the same book by the same user
- Cancelling an already-cancelled reservation returns an error
- All error responses use envelope: { error: { code: String, message: String } }

**Deliver:** Complete working code — migrations, models, controller, routes, and request specs. Write all files.
```

- [ ] **Step 2: Create the Novel prompt file**

Create `evals/proficiency/prompts/novel.md`:

```markdown
Write the opening scene (600-800 words) of a middle-grade mystery novel for ages 9-12.

**Setup:** Twelve-year-old Remi Torres arrives at her grandmother's antique shop on the first day of summer break to find the front door unlocked, the lights off, and her grandmother's prized pocket watch missing from the display case. Nothing else is disturbed. Her grandmother is at a doctor's appointment and won't be back for two hours.

**Characters:**
- Remi: observant, anxious, catalogs details in a sketchbook instead of a notebook. Draws what she sees rather than writing it. Speaks in short, precise sentences when nervous.
- Grandmother (Abuela): mentioned but not present in this scene.

**Requirements:**
- Plant exactly one physical clue that Remi notices but doesn't understand yet (the reader should be able to spot its significance on re-read)
- Include one sensory detail per scene transition (at least 2 total)
- End the scene mid-tension — Remi discovers or hears something that raises the stakes
- Remi must use her sketchbook at least once
- No adults solve anything. No convenient coincidences.
- Reading level: complex themes, clear language. Trust the reader.
```

- [ ] **Step 3: Commit**

```bash
git add evals/proficiency/prompts/
git commit -m "Add proficiency test prompts for Rails and Novel domains"
```

---

### Task 2: Create rubric files

**Files:**
- Create: `evals/proficiency/rubrics/rails-rubric.md`
- Create: `evals/proficiency/rubrics/novel-rubric.md`

- [ ] **Step 1: Create the Rails rubric**

Create `evals/proficiency/rubrics/rails-rubric.md`:

```markdown
# Rails Proficiency Rubric

You are grading a code submission for a library book reservation API. Answer each question with ONLY this JSON (no other text):

{"pass": true/false, "reasoning": "one sentence"}

## The Code

{CODE}

## Question

{QUESTION}
```

- [ ] **Step 2: Create the Novel rubric**

Create `evals/proficiency/rubrics/novel-rubric.md`:

```markdown
# Novel Proficiency Rubric

You are grading a creative writing submission for a middle-grade mystery opening scene. The scene should feature twelve-year-old Remi Torres discovering her grandmother's antique shop has been broken into, with a prized pocket watch missing. Answer each question with ONLY this JSON (no other text):

{"pass": true/false, "reasoning": "one sentence"}

## The Scene

{SCENE}

## Question

{QUESTION}
```

- [ ] **Step 3: Commit**

```bash
git add evals/proficiency/rubrics/
git commit -m "Add proficiency test rubric templates for Rails and Novel"
```

---

### Task 3: Create the runner script

**Files:**
- Create: `evals/proficiency/run-proficiency.sh`

- [ ] **Step 1: Create the runner**

Create `evals/proficiency/run-proficiency.sh`:

```bash
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
```

- [ ] **Step 2: Make executable**

```bash
chmod +x evals/proficiency/run-proficiency.sh
```

- [ ] **Step 3: Commit**

```bash
git add evals/proficiency/run-proficiency.sh
git commit -m "Add proficiency test runner"
```

---

### Task 4: Create the scorer script

**Files:**
- Create: `evals/proficiency/score-proficiency.sh`

This is the most complex file. It runs automated checks, then LLM rubric checks, then generates the summary.

- [ ] **Step 1: Create the scorer**

Create `evals/proficiency/score-proficiency.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-proficiency.sh <results-dir>}"
RUBRICS_DIR="$SCRIPT_DIR/rubrics"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR"
  exit 1
fi

# ============================================================
# RAILS AUTOMATED CHECKS
# ============================================================
rails_auto_checks() {
  local RESPONSE="$1"
  local PASS=0
  local TOTAL=10
  local RESULTS=""

  # 1. Parseable Ruby — check for ruby-like syntax (def, end, class keywords)
  if echo "$RESPONSE" | grep -qE '(def |class |module |end$)'; then
    RESULTS+="| 1 | Parseable Ruby | PASS | Contains Ruby syntax |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 1 | Parseable Ruby | FAIL | No Ruby syntax detected |\n"
  fi

  # 2. Migration exists — mentions create_table or add_column in a migration context
  if echo "$RESPONSE" | grep -qiE '(create_table|class Create|class Add.*Migration)'; then
    RESULTS+="| 2 | Migration exists | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 2 | Migration exists | FAIL | No migration found |\n"
  fi

  # 3. Migration reversible — uses def change or both def up/def down
  if echo "$RESPONSE" | grep -qE 'def change' || \
     { echo "$RESPONSE" | grep -qE 'def up' && echo "$RESPONSE" | grep -qE 'def down'; }; then
    RESULTS+="| 3 | Migration reversible | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 3 | Migration reversible | FAIL | No reversible migration pattern |\n"
  fi

  # 4. Models exist — Book, User, Reservation classes
  local MODEL_COUNT=0
  echo "$RESPONSE" | grep -qiE 'class Book' && MODEL_COUNT=$((MODEL_COUNT + 1))
  echo "$RESPONSE" | grep -qiE 'class User' && MODEL_COUNT=$((MODEL_COUNT + 1))
  echo "$RESPONSE" | grep -qiE 'class Reservation' && MODEL_COUNT=$((MODEL_COUNT + 1))
  if [ "$MODEL_COUNT" -eq 3 ]; then
    RESULTS+="| 4 | Models exist | PASS | All 3 models found |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 4 | Models exist | FAIL | Found $MODEL_COUNT/3 models |\n"
  fi

  # 5. Associations defined
  if echo "$RESPONSE" | grep -qE 'belongs_to' && echo "$RESPONSE" | grep -qE 'has_many'; then
    RESULTS+="| 5 | Associations defined | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 5 | Associations defined | FAIL | Missing belongs_to or has_many |\n"
  fi

  # 6. Controller exists with actions
  if echo "$RESPONSE" | grep -qiE 'class.*ReservationsController' && \
     echo "$RESPONSE" | grep -qE 'def (create|index|destroy)'; then
    RESULTS+="| 6 | Controller exists | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 6 | Controller exists | FAIL | Missing controller or actions |\n"
  fi

  # 7. Routes defined
  if echo "$RESPONSE" | grep -qiE 'resources? :reservations'; then
    RESULTS+="| 7 | Routes defined | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 7 | Routes defined | FAIL | No reservation routes found |\n"
  fi

  # 8. Request specs exist
  if echo "$RESPONSE" | grep -qiE '(RSpec\.describe|describe.*type: :request|spec/requests)'; then
    RESULTS+="| 8 | Request specs exist | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 8 | Request specs exist | FAIL | No request specs found |\n"
  fi

  # 9. Error envelope pattern
  if echo "$RESPONSE" | grep -qiE '(error.*code.*message|render json:.*error|{ error:)'; then
    RESULTS+="| 9 | Error envelope pattern | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 9 | Error envelope pattern | FAIL | No error envelope pattern found |\n"
  fi

  # 10. Pagination present
  if echo "$RESPONSE" | grep -qiE '(page|per_page|pagy|kaminari|paginate)'; then
    RESULTS+="| 10 | Pagination present | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 10 | Pagination present | FAIL | No pagination found |\n"
  fi

  echo "$PASS"
  echo -e "$RESULTS"
}

# ============================================================
# NOVEL AUTOMATED CHECKS
# ============================================================
novel_auto_checks() {
  local RESPONSE="$1"
  local PASS=0
  local TOTAL=7
  local RESULTS=""

  # 1. Word count in range (600-800)
  local WC
  WC=$(echo "$RESPONSE" | wc -w | tr -d ' ')
  if [ "$WC" -ge 600 ] && [ "$WC" -le 800 ]; then
    RESULTS+="| 1 | Word count in range | PASS | $WC words |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 1 | Word count in range | FAIL | $WC words (need 600-800) |\n"
  fi

  # 2. Character name present
  if echo "$RESPONSE" | grep -q 'Remi'; then
    RESULTS+="| 2 | Character name present | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 2 | Character name present | FAIL | 'Remi' not found |\n"
  fi

  # 3. Sketchbook referenced
  if echo "$RESPONSE" | grep -qiE '(sketchbook|sketch|drew|drawing|draw)'; then
    RESULTS+="| 3 | Sketchbook referenced | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 3 | Sketchbook referenced | FAIL | No sketchbook reference |\n"
  fi

  # 4. Grandmother referenced
  if echo "$RESPONSE" | grep -qiE '(grandmother|abuela|grandma)'; then
    RESULTS+="| 4 | Grandmother referenced | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 4 | Grandmother referenced | FAIL | No grandmother reference |\n"
  fi

  # 5. Scene transition exists (3+ paragraphs with blank lines)
  local PARA_COUNT
  PARA_COUNT=$(echo "$RESPONSE" | grep -c '^$' || true)
  if [ "$PARA_COUNT" -ge 2 ]; then
    RESULTS+="| 5 | Scene transition exists | PASS | $((PARA_COUNT + 1)) paragraphs |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 5 | Scene transition exists | FAIL | Too few paragraph breaks |\n"
  fi

  # 6. Dialogue present
  if echo "$RESPONSE" | grep -qE '"[^"]{2,}"'; then
    RESULTS+="| 6 | Dialogue present | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 6 | Dialogue present | FAIL | No dialogue found |\n"
  fi

  # 7. Pocket watch referenced
  if echo "$RESPONSE" | grep -qiE '(pocket watch|watch)'; then
    RESULTS+="| 7 | Pocket watch referenced | PASS | |\n"
    PASS=$((PASS + 1))
  else
    RESULTS+="| 7 | Pocket watch referenced | FAIL | No watch reference |\n"
  fi

  echo "$PASS"
  echo -e "$RESULTS"
}

# ============================================================
# LLM RUBRIC CHECK (single question)
# ============================================================
llm_rubric_check() {
  local TEMPLATE_FILE="$1"
  local CONTENT="$2"
  local QUESTION="$3"
  local CHECK_NUM="$4"
  local CHECK_NAME="$5"

  local TEMPLATE
  TEMPLATE=$(cat "$TEMPLATE_FILE")

  # Substitute content and question
  local PROMPT="${TEMPLATE//\{CODE\}/$CONTENT}"
  PROMPT="${PROMPT//\{SCENE\}/$CONTENT}"
  PROMPT="${PROMPT//\{QUESTION\}/$QUESTION}"

  local JUDGE_OUTPUT
  JUDGE_OUTPUT=$(claude -p "$PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
  local JUDGE_RESULT
  JUDGE_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')

  local PASSED
  PASSED=$(echo "$JUDGE_RESULT" | jq -r '.pass // false' 2>/dev/null || echo "false")
  local REASONING
  REASONING=$(echo "$JUDGE_RESULT" | jq -r '.reasoning // "Parse error"' 2>/dev/null || echo "Parse error")

  if [ "$PASSED" = "true" ]; then
    echo "PASS"
    echo "| $CHECK_NUM | $CHECK_NAME | PASS | $REASONING |"
  else
    echo "FAIL"
    echo "| $CHECK_NUM | $CHECK_NAME | FAIL | $REASONING |"
  fi
}

# ============================================================
# MAIN SCORING LOOP
# ============================================================

SUMMARY_FILE="$RESULTS_DIR/summary.md"

# Rails rubric questions (checks 11-20)
RAILS_QUESTIONS=(
  "Does the reservation creation use a transaction, lock, or atomic operation to prevent race conditions on copies_available?"
  "Is there a uniqueness check preventing the same user from having two active reservations for the same book?"
  "Does it validate copies_available > 0 before creating a reservation?"
  "Does cancelling an already-cancelled reservation return a proper error response, not crash or silently succeed?"
  "Do ALL error responses (validation, not found, business rule violations) use the same { error: { code, message } } format?"
  "Is the 48-hour expiry correctly set on reservation creation (reserved_at + 48.hours or equivalent)?"
  "Do request specs cover the happy path AND at least 2 distinct error paths?"
  "Is business logic in models or service objects, not directly in controller actions?"
  "Does the index action use includes, preload, or eager_load for associations?"
  "Is the migration free of table-locking patterns (no default values on add_column, no non-concurrent indexes on large tables)?"
)
RAILS_CHECK_NAMES=(
  "Race condition handling"
  "Duplicate reservation guard"
  "Copies validation"
  "Cancellation idempotency"
  "Error envelope consistency"
  "Expiry logic"
  "Spec coverage"
  "Thin controller"
  "N+1 prevention"
  "Migration safety"
)

# Novel rubric questions (checks 8-20)
NOVEL_QUESTIONS=(
  "Is there exactly one physical clue that Remi notices but doesn't fully understand? Is it embedded naturally, not highlighted?"
  "Could a reader spot the clue's significance on re-read? Is it neither too obscure nor too obvious?"
  "Are there at least 2 sensory details (sight, sound, smell, touch, taste) at scene transitions or location shifts?"
  "Does the scene end with a discovery, sound, or event that raises stakes? Not at a resolution point or natural stopping place?"
  "Does Remi use the sketchbook as a character trait (drawing to process what she sees), not just mentioned in passing?"
  "Does Remi speak in short, precise sentences when nervous, as specified in the character brief?"
  "Is the writing at an appropriate reading level for ages 9-12? Complex themes in clear, accessible language? Not condescending?"
  "Are there no convenient coincidences, no information Remi couldn't access, and no adults solving things for her?"
  "Are emotions shown through action and observation rather than stated directly? (e.g. 'Her hand tightened on the sketchbook' not 'She felt scared')"
  "Does the first paragraph pull the reader in within 2-3 sentences?"
  "Can the reader picture the antique shop from specific sensory details, not generic description?"
  "Is the missing pocket watch established clearly enough that the reader understands why it matters?"
  "Do we get Remi's internal reactions (what she notices, what worries her) without adult-level philosophical introspection?"
)
NOVEL_CHECK_NAMES=(
  "Physical clue planted"
  "Clue is fair-play"
  "Sensory details at transitions"
  "Ends mid-tension"
  "Sketchbook used meaningfully"
  "Voice consistency"
  "Age-appropriate reading level"
  "No deus ex machina"
  "Show don't tell"
  "Opening hook"
  "Setting grounded"
  "Pocket watch stakes"
  "Remi interiority"
)

{
  echo "# Proficiency Test Results"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo ""
} > "$SUMMARY_FILE"

for domain in rails-api childrens-novel; do
  DOMAIN_DIR="$RESULTS_DIR/$domain"

  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "SKIP: No results for $domain"
    continue
  fi

  echo "## $domain" >> "$SUMMARY_FILE"
  echo "" >> "$SUMMARY_FILE"

  for variant in bare assembled; do
    VARIANT_FILE="$DOMAIN_DIR/$variant.json"
    if [ ! -f "$VARIANT_FILE" ]; then
      echo "SKIP: No $variant result for $domain"
      continue
    fi

    RESPONSE=$(jq -r '.result // "ERROR: no result"' "$VARIANT_FILE")

    echo "=== Scoring: $domain / $variant ==="
    AUTO_PASS=0
    RUBRIC_PASS=0
    ALL_ROWS=""

    # --- Automated checks ---
    if [ "$domain" = "rails-api" ]; then
      AUTO_OUTPUT=$(rails_auto_checks "$RESPONSE")
      AUTO_PASS=$(echo "$AUTO_OUTPUT" | head -1)
      AUTO_ROWS=$(echo "$AUTO_OUTPUT" | tail -n +2)
      ALL_ROWS+="$AUTO_ROWS"

      # --- LLM rubric checks ---
      RUBRIC_TEMPLATE="$RUBRICS_DIR/rails-rubric.md"
      for i in "${!RAILS_QUESTIONS[@]}"; do
        CHECK_NUM=$((i + 11))
        echo "  Rubric check $CHECK_NUM: ${RAILS_CHECK_NAMES[$i]}..."
        RESULT=$(llm_rubric_check "$RUBRIC_TEMPLATE" "$RESPONSE" "${RAILS_QUESTIONS[$i]}" "$CHECK_NUM" "${RAILS_CHECK_NAMES[$i]}")
        PASS_FAIL=$(echo "$RESULT" | head -1)
        ROW=$(echo "$RESULT" | tail -1)
        ALL_ROWS+="\n$ROW"
        if [ "$PASS_FAIL" = "PASS" ]; then
          RUBRIC_PASS=$((RUBRIC_PASS + 1))
        fi
      done
    else
      AUTO_OUTPUT=$(novel_auto_checks "$RESPONSE")
      AUTO_PASS=$(echo "$AUTO_OUTPUT" | head -1)
      AUTO_ROWS=$(echo "$AUTO_OUTPUT" | tail -n +2)
      ALL_ROWS+="$AUTO_ROWS"

      # --- LLM rubric checks ---
      RUBRIC_TEMPLATE="$RUBRICS_DIR/novel-rubric.md"
      for i in "${!NOVEL_QUESTIONS[@]}"; do
        CHECK_NUM=$((i + 8))
        echo "  Rubric check $CHECK_NUM: ${NOVEL_CHECK_NAMES[$i]}..."
        RESULT=$(llm_rubric_check "$RUBRIC_TEMPLATE" "$RESPONSE" "${NOVEL_QUESTIONS[$i]}" "$CHECK_NUM" "${NOVEL_CHECK_NAMES[$i]}")
        PASS_FAIL=$(echo "$RESULT" | head -1)
        ROW=$(echo "$RESULT" | tail -1)
        ALL_ROWS+="\n$ROW"
        if [ "$PASS_FAIL" = "PASS" ]; then
          RUBRIC_PASS=$((RUBRIC_PASS + 1))
        fi
      done
    fi

    TOTAL_PASS=$((AUTO_PASS + RUBRIC_PASS))

    # Save individual score
    echo "{\"domain\": \"$domain\", \"variant\": \"$variant\", \"auto\": $AUTO_PASS, \"rubric\": $RUBRIC_PASS, \"total\": $TOTAL_PASS}" \
      > "$DOMAIN_DIR/$variant-score.json"

    # Append to summary
    {
      echo "### ${variant^}: $TOTAL_PASS/20"
      echo ""
      echo "| # | Check | Result | Notes |"
      echo "|---|---|---|---|"
      echo -e "$ALL_ROWS"
      echo ""
    } >> "$SUMMARY_FILE"

    echo "  $variant: $TOTAL_PASS/20 (auto: $AUTO_PASS, rubric: $RUBRIC_PASS)"
    echo ""
  done

done

# Add comparison table at end
{
  echo "## Summary"
  echo ""
  echo "| Domain | Bare | Assembled | Delta |"
  echo "|---|---|---|---|"

  for domain in rails-api childrens-novel; do
    BARE_SCORE=0
    ASM_SCORE=0
    [ -f "$RESULTS_DIR/$domain/bare-score.json" ] && BARE_SCORE=$(jq -r '.total' "$RESULTS_DIR/$domain/bare-score.json")
    [ -f "$RESULTS_DIR/$domain/assembled-score.json" ] && ASM_SCORE=$(jq -r '.total' "$RESULTS_DIR/$domain/assembled-score.json")
    DELTA=$((ASM_SCORE - BARE_SCORE))
    SIGN=""
    [ "$DELTA" -gt 0 ] && SIGN="+"
    echo "| $domain | $BARE_SCORE/20 | $ASM_SCORE/20 | ${SIGN}${DELTA} |"
  done

  echo ""
} >> "$SUMMARY_FILE"

echo "=== Summary ==="
cat "$SUMMARY_FILE"
echo ""
echo "Full results: $RESULTS_DIR"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x evals/proficiency/score-proficiency.sh
```

- [ ] **Step 3: Commit**

```bash
git add evals/proficiency/score-proficiency.sh
git commit -m "Add proficiency test scorer with automated checks and LLM rubric"
```

---

### Task 5: Add results gitignore

**Files:**
- Create: `evals/proficiency/results/.gitignore`

- [ ] **Step 1: Create gitignore for results**

Create `evals/proficiency/results/.gitignore`:

```
*
!.gitignore
```

- [ ] **Step 2: Commit**

```bash
git add evals/proficiency/results/.gitignore
git commit -m "Add gitignore for proficiency test results"
```

---

### Task 6: Run the proficiency test and verify

- [ ] **Step 1: Run the proficiency test**

```bash
bash evals/proficiency/run-proficiency.sh
```

Wait for both domains to complete (~5-10 minutes — only 4 total Claude invocations).

- [ ] **Step 2: Score the results**

```bash
bash evals/proficiency/score-proficiency.sh evals/proficiency/results/<timestamp>
```

Wait for scoring (~20 LLM rubric checks per variant × 2 variants × 2 domains = ~46 judge calls).

Note: the scorer is going to call the LLM rubric function many times. If the scoring takes too long or errors, check that the rubric template substitution is working (the `{CODE}` / `{SCENE}` / `{QUESTION}` placeholders are being replaced correctly).

- [ ] **Step 3: Review the output**

Check the summary. Expected: assembled scores higher than bare on both domains, with the delta coming primarily from the rubric checks (automated checks should be similar since both versions will produce syntactically valid code/prose).

If the scores are identical or bare wins, check:
1. Did the assembled version actually get the context? (check the temp dir setup)
2. Did the automated checks work correctly? (check grep patterns)
3. Did the LLM rubric parse correctly? (check for JSON parse errors in scores)

- [ ] **Step 4: Commit the summary**

```bash
cp evals/proficiency/results/<timestamp>/summary.md evals/proficiency/results/latest-summary.md
git add evals/proficiency/results/latest-summary.md
git commit -m "First proficiency test run: substance-based grading"
```
