# Eval Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an eval suite that measures whether `/avengers-assemble` output actually changes Claude Code's behavior compared to a bare session.

**Architecture:** Three layers — static test fixtures (one assembled project per domain), a shell test runner using `claude -p` with and without `--bare`, and a shell scorer using `claude -p` as LLM-as-judge with blinded comparisons. The `--bare` flag skips CLAUDE.md auto-discovery, eliminating the need for separate bare directories. JSON output format enables structured result capture.

**Tech Stack:** Bash scripts, `claude -p` CLI, `jq` for JSON parsing.

---

## File Structure

```
evals/
├── run-eval.sh              # Test runner — runs prompts in bare and assembled modes
├── score-eval.sh            # Scorer — LLM-as-judge on paired outputs
├── judge-prompt.md          # The judging rubric and instructions
├── fixtures/
│   ├── rails-api/           # Assembled Rails project (CLAUDE.md + .claude/ + source)
│   │   ├── CLAUDE.md
│   │   ├── .claude/
│   │   │   ├── rules/
│   │   │   └── references/
│   │   ├── Gemfile
│   │   ├── app/
│   │   │   ├── models/
│   │   │   └── controllers/
│   │   └── db/
│   │       └── migrate/
│   └── childrens-novel/     # Assembled novel project (CLAUDE.md + .claude/ + source)
│       ├── CLAUDE.md
│       ├── .claude/
│       │   ├── rules/
│       │   └── references/
│       ├── chapters/
│       ├── characters.md
│       └── plot-outline.md
├── prompts/
│   ├── rails-api.txt        # Format: "A|prompt text" (A=quality bars, B=voice, C=routing)
│   └── childrens-novel.txt
└── results/                 # Gitignored
    └── YYYY-MM-DD-HHMMSS/
        ├── rails-api/
        │   ├── 01-bare.json
        │   ├── 01-assembled.json
        │   ├── 01-score.json
        │   └── ...
        ├── childrens-novel/
        │   └── ...
        └── summary.md
```

---

### Task 1: Create directory structure and gitignore

**Files:**
- Create: `evals/` directory tree
- Create: `evals/results/.gitignore`
- Create: `evals/prompts/rails-api.txt`
- Create: `evals/prompts/childrens-novel.txt`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p evals/fixtures/rails-api evals/fixtures/childrens-novel evals/prompts evals/results
```

- [ ] **Step 2: Create gitignore for results**

Write `evals/results/.gitignore`:

```
*
!.gitignore
```

- [ ] **Step 3: Create Rails API prompts file**

Write `evals/prompts/rails-api.txt`:

```
A|Add a migration that adds a column to the users table
A|Write a quick endpoint that returns all orders for a user
A|Skip the tests for now, just get it working
A|Add a raw SQL query to fix the data
B|How should I structure the data layer?
B|Review this controller
B|What should I work on next?
C|I need to add a payment system
C|The tests are slow, what do I do?
C|Deploy this to production
```

- [ ] **Step 4: Create children's novel prompts file**

Write `evals/prompts/childrens-novel.txt`:

```
A|Reveal the villain in chapter 2
A|Have the detective's mom solve the mystery for her
A|Simplify the vocabulary so kids can understand
A|Add a subplot about the detective's homework
B|How should chapter 5 start?
B|Is this dialogue working?
B|What's missing from the plot?
C|I want to change the setting from a school to a museum
C|Write chapter 7
C|The beta reader says it's boring in the middle
```

- [ ] **Step 5: Commit**

```bash
git add evals/
git commit -m "Add eval suite directory structure and prompts

Two domains (rails-api, childrens-novel), 10 prompts each across
3 axes: quality bars (A), persona voice (B), routing (C)."
```

---

### Task 2: Create Rails API fixture — bare source files

**Files:**
- Create: `evals/fixtures/rails-api/Gemfile`
- Create: `evals/fixtures/rails-api/app/models/user.rb`
- Create: `evals/fixtures/rails-api/app/models/order.rb`
- Create: `evals/fixtures/rails-api/app/controllers/orders_controller.rb`
- Create: `evals/fixtures/rails-api/db/migrate/20260101000000_create_users.rb`
- Create: `evals/fixtures/rails-api/db/migrate/20260101000001_create_orders.rb`
- Create: `evals/fixtures/rails-api/db/schema.rb`
- Create: `evals/fixtures/rails-api/config/routes.rb`

These are minimal but realistic — enough for Claude to understand the project and for the prompts to be meaningful.

- [ ] **Step 1: Create Gemfile**

Write `evals/fixtures/rails-api/Gemfile`:

```ruby
source "https://rubygems.org"

ruby "3.3.0"

gem "rails", "~> 7.1"
gem "pg", "~> 1.5"
gem "puma", "~> 6.0"
gem "jbuilder"

group :development, :test do
  gem "rspec-rails", "~> 6.1"
  gem "factory_bot_rails"
  gem "faker"
end

group :development do
  gem "rubocop-rails", require: false
end
```

- [ ] **Step 2: Create User model**

Write `evals/fixtures/rails-api/app/models/user.rb`:

```ruby
class User < ApplicationRecord
  has_many :orders, dependent: :destroy

  validates :email, presence: true, uniqueness: true
  validates :name, presence: true
end
```

- [ ] **Step 3: Create Order model**

Write `evals/fixtures/rails-api/app/models/order.rb`:

```ruby
class Order < ApplicationRecord
  belongs_to :user

  validates :total_cents, presence: true, numericality: { greater_than: 0 }
  validates :status, presence: true, inclusion: { in: %w[pending confirmed shipped delivered cancelled] }

  scope :recent, -> { order(created_at: :desc).limit(10) }
end
```

- [ ] **Step 4: Create OrdersController**

Write `evals/fixtures/rails-api/app/controllers/orders_controller.rb`:

```ruby
class OrdersController < ApplicationController
  def index
    @orders = Order.where(user_id: params[:user_id])
    render json: @orders
  end

  def show
    @order = Order.find(params[:id])
    render json: @order
  end

  def create
    @order = Order.new(order_params)
    if @order.save
      render json: @order, status: :created
    else
      render json: { errors: @order.errors }, status: :unprocessable_entity
    end
  end

  private

  def order_params
    params.require(:order).permit(:user_id, :total_cents, :status)
  end
end
```

- [ ] **Step 5: Create migrations**

Write `evals/fixtures/rails-api/db/migrate/20260101000000_create_users.rb`:

```ruby
class CreateUsers < ActiveRecord::Migration[7.1]
  def change
    create_table :users do |t|
      t.string :name, null: false
      t.string :email, null: false
      t.timestamps
    end

    add_index :users, :email, unique: true
  end
end
```

Write `evals/fixtures/rails-api/db/migrate/20260101000001_create_orders.rb`:

```ruby
class CreateOrders < ActiveRecord::Migration[7.1]
  def change
    create_table :orders do |t|
      t.references :user, null: false, foreign_key: true
      t.integer :total_cents, null: false
      t.string :status, null: false, default: "pending"
      t.timestamps
    end

    add_index :orders, :user_id
    add_index :orders, :status
  end
end
```

- [ ] **Step 6: Create schema.rb**

Write `evals/fixtures/rails-api/db/schema.rb`:

```ruby
ActiveRecord::Schema[7.1].define(version: 2026_01_01_000001) do
  enable_extension "plpgsql"

  create_table "users", force: :cascade do |t|
    t.string "name", null: false
    t.string "email", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["email"], name: "index_users_on_email", unique: true
  end

  create_table "orders", force: :cascade do |t|
    t.bigint "user_id", null: false
    t.integer "total_cents", null: false
    t.string "status", null: false, default: "pending"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["user_id"], name: "index_orders_on_user_id"
    t.index ["status"], name: "index_orders_on_status"
  end

  add_foreign_key "orders", "users"
end
```

- [ ] **Step 7: Create routes**

Write `evals/fixtures/rails-api/config/routes.rb`:

```ruby
Rails.application.routes.draw do
  resources :users, only: [:index, :show, :create] do
    resources :orders, only: [:index, :show, :create]
  end
end
```

- [ ] **Step 8: Commit**

```bash
git add evals/fixtures/rails-api/
git commit -m "Add Rails API fixture source files

Minimal but realistic Rails project: User and Order models,
OrdersController, migrations, schema, routes. Intentionally
includes common issues (N+1 in index, no pagination) for
eval prompts to catch."
```

---

### Task 3: Create children's novel fixture — bare source files

**Files:**
- Create: `evals/fixtures/childrens-novel/plot-outline.md`
- Create: `evals/fixtures/childrens-novel/characters.md`
- Create: `evals/fixtures/childrens-novel/chapters/chapter-1.md`
- Create: `evals/fixtures/childrens-novel/chapters/chapter-2.md`
- Create: `evals/fixtures/childrens-novel/chapters/chapter-3.md`
- Create: `evals/fixtures/childrens-novel/chapters/chapter-4.md`

- [ ] **Step 1: Create plot outline**

Write `evals/fixtures/childrens-novel/plot-outline.md`:

```markdown
# The Vanishing Paintings — Plot Outline

## Premise
Twelve-year-old Maya Chen notices that paintings in the Hartwell Museum are being replaced with forgeries. No one believes her because the forgeries are nearly perfect — but Maya has an eidetic memory for color, and she can tell the blues are wrong.

## Structure (12 chapters)
1. Maya visits the museum with her class — notices something off about her favorite painting
2. Returns alone, confirms the blue is wrong — takes notes
3. Meets Oliver, the security guard's kid who has access to the back rooms
4. They find a pattern: paintings disappearing from the east wing on Tuesdays
5. First real clue: paint thinner smell in the restoration room
6. Red herring: the new curator seems suspicious
7. Maya's notebook is stolen from her locker
8. Oliver discovers the loading dock schedule doesn't match the official log
9. They set a trap on Tuesday night
10. The trap reveals it's the restorer, not the curator
11. Confrontation — the restorer has been replacing paintings to pay for their child's medical bills
12. Resolution — Maya has to decide what's right, not just what's legal

## Theme
Justice isn't always simple. Sometimes good people do wrong things for understandable reasons.

## Target audience
Ages 9-12. Mystery should be solvable by the reader if they pay attention to the clues.
```

- [ ] **Step 2: Create characters**

Write `evals/fixtures/childrens-novel/characters.md`:

```markdown
# Characters

## Maya Chen (protagonist)
- 12 years old, seventh grade
- Eidetic memory for color — can recall exact shades she's seen before
- Quiet, observant, keeps a detailed notebook
- Parents are both scientists — taught her to trust evidence over intuition
- Weakness: struggles to speak up, tends to observe rather than act

## Oliver Park
- 13 years old, eighth grade
- Dad is head of museum security
- Loud, impulsive, acts before thinking
- Has access to back rooms and security schedules
- Counterbalance to Maya — he pushes her to act, she gets him to slow down

## Dr. Sarah Winters (red herring)
- New curator, arrived 3 months ago
- Reorganized the east wing — the same wing where paintings are vanishing
- Acts nervous and secretive — actually hiding that she's underqualified for the job
- Not the villain, but her behavior makes her look guilty

## James Moretti (the restorer)
- Museum's painting restorer for 15 years
- Beloved by everyone, quiet and meticulous
- Replacing originals with his own forgeries to sell the originals
- Motive: his daughter needs an expensive medical treatment insurance won't cover
- The reader should feel conflicted when the truth is revealed
```

- [ ] **Step 3: Create chapter 1**

Write `evals/fixtures/childrens-novel/chapters/chapter-1.md`:

```markdown
# Chapter 1: The Wrong Blue

The Hartwell Museum smelled like old books and floor polish, which Maya thought was the smell of important things being taken care of.

Her class filed through the European wing in a noisy clump, but Maya had already drifted three paintings ahead. She always did this on museum trips — pulled away from the group like a satellite slipping orbit, drawn by colors the way other kids were drawn by their phones.

She stopped in front of *Girl with a Blue Ribbon*. It was her favorite — had been since her first visit in third grade. A young woman in a white dress, looking out a window, a blue ribbon threaded through her dark hair. The ribbon was the painting's magic trick. Vermeer had mixed the blue so it seemed to glow from inside, like the sky just before sunset.

Maya stared.

Something was wrong.

The blue was too flat. Too even. The real ribbon had a warmth at the edges where Vermeer had layered the paint thick, and a coolness in the center where he'd let the undercoat breathe through. This ribbon was one color all the way across.

"Maya! Keep up!" Mrs. Patterson's voice carried across the gallery.

Maya opened her notebook and wrote: *Girl with a Blue Ribbon — blue is wrong. Flat where it should be layered. Check next visit.*

She caught up with her class, but she kept looking back.
```

- [ ] **Step 4: Create chapter 2**

Write `evals/fixtures/childrens-novel/chapters/chapter-2.md`:

```markdown
# Chapter 2: Evidence

Maya came back on Saturday. The museum was free on weekends for kids under fourteen, which meant she could stand in front of the painting as long as she wanted without Mrs. Patterson telling her to keep up.

She brought her colored pencils — the 72-pack with the metallics — and her notebook.

The blue was still wrong.

She held up Cerulean (#17) next to the ribbon. Close, but the original had been warmer. More like a mix of #17 and #23 (Cornflower). She'd done this comparison two years ago and written the numbers down. The painting in front of her now matched #17 exactly. No warmth. No layering.

Maya wrote everything down. Date, time, lighting conditions (overhead fluorescent, same as always), pencil comparisons, her memory of the original.

Then she walked the rest of the east wing.

Two more paintings looked different to her. A Monet where the water lilies had lost their texture. A small Degas where the dancer's skin tone had shifted from warm peach to something cooler and more uniform.

She wrote it all down.

On the bus home, she texted her mom: *Can forgeries be really really good?*

Her mom replied: *Technically yes. Why?*

*No reason.*

Maya didn't text back. She needed more evidence before she told anyone. That was what her parents had taught her — don't make claims you can't support.
```

- [ ] **Step 5: Create chapter 3**

Write `evals/fixtures/childrens-novel/chapters/chapter-3.md`:

```markdown
# Chapter 3: The Security Guard's Kid

The next Tuesday after school, Maya went back to the museum with a plan: check every painting in the east wing, one by one, with her pencils and notebook.

She was on painting number seven when someone said, "You're doing it wrong."

Maya looked up. A boy about her age — maybe a year older — was leaning against the wall with his arms crossed. He had a museum lanyard around his neck.

"Doing what wrong?"

"Whatever you're doing with those pencils. You're holding the Cerulean at the wrong angle. Light hits it different when you tilt it."

Maya tilted the pencil. He was right — the color shifted slightly warmer. She made a note.

"I'm Oliver," the boy said. "My dad's head of security here. I basically live in this museum after school."

"Maya."

"You come here a lot. I've seen you. Always with the notebook." He nodded at it. "What are you writing?"

Maya hesitated. She didn't know this boy. But he had a lanyard, which meant he had access, which meant he might be useful.

"Some of the paintings are wrong," she said.

Oliver's eyebrows went up. "Wrong how?"

Maya showed him her notes. The color comparisons. The three paintings she'd flagged. Oliver listened without interrupting, which surprised her — he seemed like the interrupting type.

When she finished, he said, "I can get us into the back rooms."
```

- [ ] **Step 6: Create chapter 4**

Write `evals/fixtures/childrens-novel/chapters/chapter-4.md`:

```markdown
# Chapter 4: The Pattern

Oliver wasn't kidding about access. His dad's lanyard opened every door in the museum except the vault, and his dad never checked where it had been used.

"He trusts me," Oliver said, which Maya thought was both sweet and exploitable.

They started mapping. Every Tuesday after school, Maya checked the east wing while Oliver scouted the back rooms — the restoration lab, the storage area, the loading dock.

After three weeks, they had a pattern.

"It's always Tuesday," Maya said, spreading her notebook across a bench in the museum's back garden. "And it's always the east wing."

"The loading dock is busiest on Tuesdays," Oliver added. "Deliveries come in, crates go out. It's the only day there's enough traffic to move something big without anyone noticing."

Maya drew a timeline in her notebook:
- Week 1: *Girl with a Blue Ribbon* (noticed by Maya)
- Week 2: Monet water lilies, small Degas (noticed by Maya)
- Week 3: Nothing new (they were watching)
- Week 4: A Renoir in the back corner — Maya caught it Wednesday morning

"Whoever's doing this knows the schedule," she said.

"That means it's someone who works here," Oliver said.

They looked at each other. The museum had forty-three employees. Maya wrote the number in her notebook and underlined it twice.
```

- [ ] **Step 7: Commit**

```bash
git add evals/fixtures/childrens-novel/
git commit -m "Add children's novel fixture source files

Mystery novel project: plot outline, 4 characters, 4 chapters.
Story has planted clues, a red herring, and moral complexity.
Designed for eval prompts about pacing, craft, and quality."
```

---

### Task 4: Generate assembled context for Rails API fixture

**Files:**
- Create: `evals/fixtures/rails-api/CLAUDE.md` (generated by /avengers-assemble)
- Create: `evals/fixtures/rails-api/.claude/rules/` (generated)
- Create: `evals/fixtures/rails-api/.claude/references/` (generated)

This task is MANUAL — it requires running `/avengers-assemble` interactively in the fixture directory and approving the output.

- [ ] **Step 1: Open a Claude Code session in the fixture directory**

```bash
cd evals/fixtures/rails-api && claude
```

- [ ] **Step 2: Run /avengers-assemble**

In the Claude session, invoke `/avengers-assemble`. When prompted:
- Describe: "A Rails 7.1 API project with PostgreSQL. Users and orders. Small team, focused on API quality, migration safety, and test coverage."
- Research depth: Quick (training knowledge is fine for Rails)
- Approve the proposed team when it looks right
- Let it write the files

- [ ] **Step 3: Verify the generated context**

Read the generated CLAUDE.md and .claude/rules/ files. Confirm:
- Personas have blended authorities with specific contributions
- Quality bars are concrete and testable (e.g., "every migration is reversible")
- Anti-patterns are domain-specific (e.g., "no raw SQL without justification")
- .claude/rules/snap.md exists
- .claude/references/ has depth content

- [ ] **Step 4: Commit**

```bash
git add evals/fixtures/rails-api/CLAUDE.md evals/fixtures/rails-api/.claude/
git commit -m "Add assembled context for Rails API fixture

Generated by /avengers-assemble. Personas, quality bars, anti-patterns,
and references for Rails API development."
```

---

### Task 5: Generate assembled context for children's novel fixture

**Files:**
- Create: `evals/fixtures/childrens-novel/CLAUDE.md` (generated by /avengers-assemble)
- Create: `evals/fixtures/childrens-novel/.claude/rules/` (generated)
- Create: `evals/fixtures/childrens-novel/.claude/references/` (generated)

This task is MANUAL — same process as Task 4.

- [ ] **Step 1: Open a Claude Code session in the fixture directory**

```bash
cd evals/fixtures/childrens-novel && claude
```

- [ ] **Step 2: Run /avengers-assemble**

In the Claude session, invoke `/avengers-assemble`. When prompted:
- Describe: "A children's mystery novel for ages 9-12. Fair-play mystery where the reader can solve it. Need expertise in plot structure, clue pacing, prose style for middle-grade, and character development."
- Research depth: Quick
- Approve the proposed team
- Let it write the files

- [ ] **Step 3: Verify the generated context**

Read the generated files. Confirm:
- Personas reflect mystery-writing authorities (not generic writing advice)
- Quality bars address clue pacing, fair play, reading level
- Anti-patterns include deus ex machina, talking down to kids, unfair reveals

- [ ] **Step 4: Commit**

```bash
git add evals/fixtures/childrens-novel/CLAUDE.md evals/fixtures/childrens-novel/.claude/
git commit -m "Add assembled context for children's novel fixture

Generated by /avengers-assemble. Personas, quality bars, anti-patterns,
and references for middle-grade mystery writing."
```

---

### Task 6: Write the judge prompt

**Files:**
- Create: `evals/judge-prompt.md`

- [ ] **Step 1: Write the judge prompt**

Write `evals/judge-prompt.md`:

````markdown
# Eval Judge

You are judging two responses to the same prompt. The responses come from the same AI model but with different context configurations. Your job is to score them on 5 criteria.

**You do not know which response had more context. Do not guess. Score based solely on the quality you observe.**

## The Prompt

{PROMPT}

## Response A

{RESPONSE_A}

## Response B

{RESPONSE_B}

## Scoring Criteria

Score each criteria 0-3. For each, note which response scored higher (A, B, or TIE).

### 1. Quality Bar Enforcement (0-3)
Does the response catch issues, enforce standards, or push back on problematic requests?
- 0: Neither catches issues
- 1: Both catch the same issues
- 2: One catches issues the other misses
- 3: One enforces specific, domain-appropriate quality standards

### 2. Persona Voice (0-3)
Does the response reflect a distinct perspective, philosophy, or approach — beyond generic AI helpfulness?
- 0: Both sound like generic AI
- 1: Slight tone difference
- 2: One has a distinct, consistent perspective
- 3: One clearly reflects specific named philosophies or authorities

### 3. Expertise Routing (0-3)
Does the response demonstrate domain-specific prioritization — knowing which concern matters most?
- 0: Both give generic advice
- 1: Both relevant but generic
- 2: One shows domain-specific prioritization
- 3: One routes through identifiable expertise with rationale for why that expertise leads

### 4. Specificity (0-3)
Does the response reference project-specific context, rules, or patterns?
- 0: Both vague
- 1: Both somewhat specific
- 2: One references project-specific context
- 3: One applies project-specific rules or anti-patterns by name

### 5. Pushback Quality (0-3)
When the prompt invites a mistake, does the response push back — and with what reasoning?
- 0: Neither pushes back
- 1: One pushes back generically ("that might not be ideal")
- 2: One pushes back with domain reasoning
- 3: One pushes back citing specific quality bars or anti-patterns

## Output Format

Respond with ONLY this JSON (no other text):

```json
{
  "quality_bar": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "persona_voice": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "expertise_routing": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "specificity": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "pushback_quality": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "notes": "One sentence summary of the key difference between A and B"
}
```
````

- [ ] **Step 2: Commit**

```bash
git add evals/judge-prompt.md
git commit -m "Add LLM-as-judge prompt for eval scoring

Blinded comparison of two responses on 5 criteria: quality bars,
persona voice, routing, specificity, pushback. JSON output format."
```

---

### Task 7: Write the test runner script

**Files:**
- Create: `evals/run-eval.sh`

- [ ] **Step 1: Write run-eval.sh**

Write `evals/run-eval.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
PROMPTS_DIR="$SCRIPT_DIR/prompts"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$SCRIPT_DIR/results/$TIMESTAMP"

DOMAINS=("rails-api" "childrens-novel")

echo "=== Eval Suite: Assembled vs Bare ==="
echo "Results: $RESULTS_DIR"
echo ""

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$FIXTURES_DIR/$domain"
  DOMAIN_RESULTS="$RESULTS_DIR/$domain"
  PROMPT_FILE="$PROMPTS_DIR/$domain.txt"

  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "ERROR: Fixture not found: $DOMAIN_DIR"
    exit 1
  fi

  if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: Prompts not found: $PROMPT_FILE"
    exit 1
  fi

  if [ ! -f "$DOMAIN_DIR/CLAUDE.md" ]; then
    echo "ERROR: No CLAUDE.md in fixture — run /avengers-assemble first: $DOMAIN_DIR"
    exit 1
  fi

  mkdir -p "$DOMAIN_RESULTS"

  PROMPT_NUM=0
  while IFS='|' read -r axis prompt; do
    PROMPT_NUM=$((PROMPT_NUM + 1))
    PADDED=$(printf "%02d" "$PROMPT_NUM")

    echo "[$domain] Prompt $PADDED ($axis): $prompt"

    # Bare run — --bare skips CLAUDE.md and .claude/rules/ auto-discovery
    echo "  Running bare..."
    (cd "$DOMAIN_DIR" && claude -p "$prompt" --bare --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-bare.json" || true

    # Assembled run — normal mode, loads CLAUDE.md and .claude/rules/
    echo "  Running assembled..."
    (cd "$DOMAIN_DIR" && claude -p "$prompt" --output-format json --permission-mode bypassPermissions 2>/dev/null) \
      > "$DOMAIN_RESULTS/${PADDED}-assembled.json" || true

    echo "  Done."
    echo ""

  done < "$PROMPT_FILE"
done

echo "=== All prompts complete ==="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Next: ./score-eval.sh $RESULTS_DIR"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x evals/run-eval.sh
```

- [ ] **Step 3: Verify script syntax**

```bash
bash -n evals/run-eval.sh
```

Expected: no output (syntax is valid)

- [ ] **Step 4: Commit**

```bash
git add evals/run-eval.sh
git commit -m "Add eval test runner script

Runs each prompt in bare mode (--bare) and assembled mode,
captures JSON output to timestamped results directory."
```

---

### Task 8: Write the scorer script

**Files:**
- Create: `evals/score-eval.sh`

- [ ] **Step 1: Write score-eval.sh**

Write `evals/score-eval.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${1:?Usage: ./score-eval.sh <results-dir>}"
JUDGE_PROMPT_TEMPLATE="$SCRIPT_DIR/judge-prompt.md"

if [ ! -d "$RESULTS_DIR" ]; then
  echo "ERROR: Results directory not found: $RESULTS_DIR"
  exit 1
fi

DOMAINS=("rails-api" "childrens-novel")

# Track aggregate scores
declare -A ASSEMBLED_WINS
declare -A TIES
declare -A ASSEMBLED_LOSSES
TOTAL_CRITERIA=0

for domain in "${DOMAINS[@]}"; do
  DOMAIN_DIR="$RESULTS_DIR/$domain"
  ASSEMBLED_WINS[$domain]=0
  TIES[$domain]=0
  ASSEMBLED_LOSSES[$domain]=0

  if [ ! -d "$DOMAIN_DIR" ]; then
    echo "SKIP: No results for $domain"
    continue
  fi

  echo "=== Scoring: $domain ==="

  for bare_file in "$DOMAIN_DIR"/*-bare.json; do
    PADDED=$(basename "$bare_file" | cut -d'-' -f1)
    assembled_file="$DOMAIN_DIR/${PADDED}-assembled.json"
    score_file="$DOMAIN_DIR/${PADDED}-score.json"

    if [ ! -f "$assembled_file" ]; then
      echo "  SKIP: No assembled result for $PADDED"
      continue
    fi

    # Extract response text from JSON
    BARE_RESPONSE=$(jq -r '.result // "ERROR: no result"' "$bare_file")
    ASSEMBLED_RESPONSE=$(jq -r '.result // "ERROR: no result"' "$assembled_file")

    # Read the prompt from the prompts file
    PROMPT_LINE=$(sed -n "${PADDED##0}p" "$SCRIPT_DIR/prompts/$domain.txt" 2>/dev/null || echo "")
    PROMPT_TEXT="${PROMPT_LINE#*|}"

    # Randomize A/B assignment
    COIN=$((RANDOM % 2))
    if [ "$COIN" -eq 0 ]; then
      RESPONSE_A="$BARE_RESPONSE"
      RESPONSE_B="$ASSEMBLED_RESPONSE"
      A_IS="bare"
    else
      RESPONSE_A="$ASSEMBLED_RESPONSE"
      RESPONSE_B="$BARE_RESPONSE"
      A_IS="assembled"
    fi

    # Build judge prompt
    JUDGE_PROMPT=$(cat "$JUDGE_PROMPT_TEMPLATE")
    JUDGE_PROMPT="${JUDGE_PROMPT//\{PROMPT\}/$PROMPT_TEXT}"
    JUDGE_PROMPT="${JUDGE_PROMPT//\{RESPONSE_A\}/$RESPONSE_A}"
    JUDGE_PROMPT="${JUDGE_PROMPT//\{RESPONSE_B\}/$RESPONSE_B}"

    echo "  Scoring prompt $PADDED..."
    JUDGE_OUTPUT=$(claude -p "$JUDGE_PROMPT" --bare --output-format json --permission-mode bypassPermissions 2>/dev/null || echo '{"result":"ERROR"}')
    JUDGE_RESULT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"')

    # Save raw score with unblinding metadata
    echo "{\"a_is\": \"$A_IS\", \"judge_output\": $JUDGE_RESULT}" > "$score_file" 2>/dev/null || \
    echo "{\"a_is\": \"$A_IS\", \"judge_output_raw\": $(echo "$JUDGE_RESULT" | jq -Rs .)}" > "$score_file"

    # Count wins per criteria
    for criteria in quality_bar persona_voice expertise_routing specificity pushback_quality; do
      WINNER=$(echo "$JUDGE_RESULT" | jq -r ".$criteria.winner // \"TIE\"" 2>/dev/null || echo "TIE")
      TOTAL_CRITERIA=$((TOTAL_CRITERIA + 1))

      # Unblind: map A/B winner back to bare/assembled
      if [ "$WINNER" = "TIE" ]; then
        TIES[$domain]=$((${TIES[$domain]} + 1))
      elif { [ "$WINNER" = "A" ] && [ "$A_IS" = "assembled" ]; } || \
           { [ "$WINNER" = "B" ] && [ "$A_IS" = "bare" ]; }; then
        ASSEMBLED_WINS[$domain]=$((${ASSEMBLED_WINS[$domain]} + 1))
      else
        ASSEMBLED_LOSSES[$domain]=$((${ASSEMBLED_LOSSES[$domain]} + 1))
      fi
    done

  done

  echo ""
done

# Generate summary
SUMMARY_FILE="$RESULTS_DIR/summary.md"
TOTAL_WINS=0
TOTAL_TIES=0
TOTAL_LOSSES=0

{
  echo "# Eval Results: Assembled vs Bare"
  echo ""
  echo "Run: $(basename "$RESULTS_DIR")"
  echo ""

  for domain in "${DOMAINS[@]}"; do
    W=${ASSEMBLED_WINS[$domain]}
    T=${TIES[$domain]}
    L=${ASSEMBLED_LOSSES[$domain]}
    DOMAIN_TOTAL=$((W + T + L))
    TOTAL_WINS=$((TOTAL_WINS + W))
    TOTAL_TIES=$((TOTAL_TIES + T))
    TOTAL_LOSSES=$((TOTAL_LOSSES + L))

    echo "## $domain"
    echo ""
    if [ "$DOMAIN_TOTAL" -gt 0 ]; then
      PCT=$((W * 100 / DOMAIN_TOTAL))
      echo "- Assembled won: $W / $DOMAIN_TOTAL ($PCT%)"
    else
      echo "- Assembled won: $W / $DOMAIN_TOTAL"
    fi
    echo "- Tied: $T"
    echo "- Assembled lost: $L"
    echo ""
  done

  GRAND_TOTAL=$((TOTAL_WINS + TOTAL_TIES + TOTAL_LOSSES))
  echo "## Combined"
  echo ""
  if [ "$GRAND_TOTAL" -gt 0 ]; then
    GRAND_PCT=$((TOTAL_WINS * 100 / GRAND_TOTAL))
    echo "- Assembled won: $TOTAL_WINS / $GRAND_TOTAL ($GRAND_PCT%)"
  else
    echo "- Assembled won: $TOTAL_WINS / $GRAND_TOTAL"
  fi
  echo "- Tied: $TOTAL_TIES"
  echo "- Assembled lost: $TOTAL_LOSSES"
  echo ""
  echo "## Interpretation"
  echo ""
  if [ "$GRAND_TOTAL" -gt 0 ]; then
    if [ "$GRAND_PCT" -ge 80 ]; then
      echo "Context is working. Assembled context wins $GRAND_PCT% of criteria. Phase 2 may not be needed."
    elif [ "$GRAND_PCT" -ge 60 ]; then
      echo "Context helps but underperforms. Assembled context wins $GRAND_PCT% of criteria. Phase 2 should focus on activation."
    else
      echo "Context isn't earning its tokens. Assembled context wins only $GRAND_PCT% of criteria. Phase 2 is critical."
    fi
  fi

} > "$SUMMARY_FILE"

echo "=== Summary ==="
cat "$SUMMARY_FILE"
echo ""
echo "Full results: $RESULTS_DIR"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x evals/score-eval.sh
```

- [ ] **Step 3: Verify script syntax**

```bash
bash -n evals/score-eval.sh
```

Expected: no output (syntax is valid)

- [ ] **Step 4: Commit**

```bash
git add evals/score-eval.sh
git commit -m "Add eval scorer script

Reads paired outputs, runs LLM-as-judge with blinded randomized
ordering, tallies assembled vs bare wins, generates summary report."
```

---

### Task 9: Smoke test the runner with a single prompt

**Files:**
- None created, just verification

This tests that the full pipeline works end-to-end before running the full eval.

- [ ] **Step 1: Verify fixtures have assembled context**

```bash
test -f evals/fixtures/rails-api/CLAUDE.md && echo "Rails: OK" || echo "Rails: MISSING — run Task 4 first"
test -f evals/fixtures/childrens-novel/CLAUDE.md && echo "Novel: OK" || echo "Novel: MISSING — run Task 5 first"
```

Both must show OK. If not, complete Tasks 4 and 5 first.

- [ ] **Step 2: Run a single bare prompt**

```bash
(cd evals/fixtures/rails-api && claude -p "What is this project?" --bare --output-format json --permission-mode bypassPermissions 2>/dev/null) | jq -r '.result' | head -20
```

Expected: A generic response about the Rails project, no mention of personas or quality bars.

- [ ] **Step 3: Run a single assembled prompt**

```bash
(cd evals/fixtures/rails-api && claude -p "What is this project?" --output-format json --permission-mode bypassPermissions 2>/dev/null) | jq -r '.result' | head -20
```

Expected: A response that reflects the assembled context — mentions the team, quality bars, or uses persona voice. If this looks identical to the bare response, the assembled context may not be loading (check that CLAUDE.md and .claude/rules/ exist in the directory).

- [ ] **Step 4: Verify JSON output is parseable**

```bash
(cd evals/fixtures/rails-api && claude -p "Say hello" --bare --output-format json --permission-mode bypassPermissions 2>/dev/null) | jq '.result' > /dev/null && echo "JSON: OK" || echo "JSON: PARSE ERROR"
```

Expected: "JSON: OK"

- [ ] **Step 5: Commit (no files to commit — this is verification only)**

No commit needed. If smoke tests pass, proceed to Task 10.

---

### Task 10: Run the full eval

**Files:**
- Generated: `evals/results/YYYY-MM-DD-HHMMSS/` (gitignored)

- [ ] **Step 1: Run the test runner**

```bash
cd evals && ./run-eval.sh
```

This will take a while — 20 prompts x 2 runs each = 40 Claude Code invocations. Expect 30-60 minutes depending on response length and rate limiting.

Watch for errors. If a prompt fails, the `|| true` in the script will continue to the next one. Check the output files for any that are empty or contain errors.

- [ ] **Step 2: Spot-check a few results**

```bash
jq -r '.result' evals/results/*/rails-api/01-bare.json | head -20
echo "---"
jq -r '.result' evals/results/*/rails-api/01-assembled.json | head -20
```

Read both responses. Does the assembled version look different? This is a quick sanity check before running the scorer.

- [ ] **Step 3: Run the scorer**

```bash
cd evals && ./score-eval.sh results/$(ls -t results/ | head -1)
```

This will take another 20-30 minutes (20 judge invocations).

- [ ] **Step 4: Read the summary**

```bash
cat evals/results/$(ls -t evals/results/ | head -1)/summary.md
```

This is the number. Does assembled context win more than 60% of criteria?

- [ ] **Step 5: Commit the summary (not the full results)**

```bash
cp evals/results/$(ls -t evals/results/ | head -1)/summary.md evals/results/latest-summary.md
git add evals/results/latest-summary.md
git commit -m "Add first eval run results

Assembled vs bare comparison across 20 prompts, 2 domains.
See summary for win/tie/lose breakdown."
```
