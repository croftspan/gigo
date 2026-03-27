# The Eval Narrative: From 87% to 96%+ with Hawkeye

How we proved assembled context works, found the gaps, closed them, added an adversarial output gate, and learned what the numbers can't tell you.

## The Question

Does the output of `/avengers-assemble` — the personas, quality gates, workflow loops, and reference files — actually change Claude's behavior? Or is it just expensive token decoration?

## The Setup

Two fixture domains:
- **Rails API** (OrderFlow) — 3 personas (Kane/migration safety, Leach/API design, Beck/TDD), quality gates, anti-patterns, reference patterns
- **Children's Novel** (The Vanishing Paintings) — 3 personas (Van Draanen/plot structure, DiCamillo/prose craft, Blume/young reader advocacy), mystery craft rules, clue-pacing standards

10 prompts per domain across 3 axes:
- **Axis A (quality bars):** Prompts that invite mistakes — skip tests, add raw SQL, reveal the villain early, simplify vocabulary
- **Axis B (persona voice):** Open questions — how to structure code, review a controller, is this dialogue working
- **Axis C (routing):** Complex tasks — add a payment system, deploy to production, change the setting, fix boring pacing

Each prompt runs twice: **bare** (source files only, no CLAUDE.md or .claude/) vs **assembled** (full context). LLM-as-judge with blinded randomized A/B ordering scores 5 criteria per prompt: quality bar enforcement, persona voice, expertise routing, specificity, pushback quality.

20 prompts x 5 criteria = **100 evaluations per run.**

## Phase 1: The Baseline (87%)

| Domain | Win % | Ties | Losses |
|---|---|---|---|
| Rails API | 88% | 5 | 1 |
| Children's Novel | 86% | 6 | 1 |
| **Combined** | **87%** | **11** | **2** |

### The Aha Moment

The 13 non-wins clustered into a pattern that matched a paper we'd already integrated: **Hu et al. (2026) — "Expert Personas Improve LLM Alignment but Damage Accuracy."**

Presentation tasks (quality bars, style, structure) — assembled won almost every time.
Content tasks (factual recall, deployment steps, diagnostics) — tied. The persona overhead was neutral or slightly negative.

This wasn't a failure of our context. It was the fundamental tradeoff the research predicts: personas help alignment, hurt knowledge retrieval. We were seeing it in our own data.

### What Tied

- **Rails #6 "Review this controller"** — 4 non-wins. Claude's base code review is strong enough to tie.
- **Rails #5 "How should I structure the data layer?"** — ties on knowledge criteria
- **Rails #10 "Deploy this to production"** — bare version gives deployment steps fine without persona
- **Novel #5 "How should chapter 5 start?"** — open creative prompt, slight bare advantage on pushback (nothing to push back on)
- **Novel #8 "Change the setting"** — both identified the setting correctly
- **Novel #10 "Boring in the middle"** — both gave pacing advice

### What Lost

- **Rails:** 1 loss — bare version gave a slightly more focused answer on a content task
- **Novel:** 1 loss on pushback — nothing to push back on, bare gave a slightly better open-ended answer

## Phase 2: Two Levers

### Lever 1: Persona Calibration Heuristic

Added to both fixture `workflow.md` files. A lightweight metacognitive check:

**Rails version:**
> Before responding, assess the task type:
> - **Presentation tasks** (architecture decisions, code review, prioritization) — lean into persona fully
> - **Content tasks** (factual lookup, debugging, deployment steps) — lead with training, persona for framing only

**Children's novel version:**
> - **Craft tasks** (chapter writing, revision, plot structure) — lean into persona fully
> - **Content tasks** (setting research, publishing logistics, beta reader triage) — lead with training, persona for framing only

**The theory:** On content tasks, the assembled version was competing with itself — persona context pulling against the model's factual training. The heuristic tells the model to step back and let training lead, using persona only for framing. This should convert ties to wins by adding persona value (structure, caveats, quality gate flags) without degrading the core answer.

### Lever 2: Task-Specific "When to Go Deeper" Pointers

The original pointers were generic:
> When working on migrations, read `.claude/references/rails-patterns.md`.

The new pointers name the task and what to look for:
> When deploying or preparing for production, read `.claude/references/rails-patterns.md` — verify migration safety, index strategy, and CI status before shipping.
> When a reader reports pacing problems, read `.claude/references/mystery-craft.md` — check revelation pacing for the chapter range, verify every chapter earns its length.

**The theory:** The tied prompts involved tasks where domain knowledge lives in reference files that didn't load. Generic pointers don't trigger on "deploy to production" or "boring in the middle." Specific pointers do — giving assembled versions ammunition bare versions don't have.

## Phase 2a Results: 96%

| Domain | Win % | Ties | Losses |
|---|---|---|---|
| Rails API | 92% | 4 | 0 |
| Children's Novel | **100%** | 0 | 0 |
| **Combined** | **96%** | **4** | **0** |

Children's novel went to 100%. Every previously tied prompt converted. The task-specific pointers to mystery-craft.md gave concrete ammunition: revelation pacing, clue chain audits, chapter-specific diagnosis.

Rails had 4 remaining ties — all on prompt 08 ("I need to add a payment system"), where both versions asked clarifying questions. The assembled version flagged existing codebase issues, but the judge scored persona voice, specificity, and pushback as ties since neither pushed back.

## Phase 2b: The Variance Problem (91%)

Ran again with a minor tweak (strengthened The Loop step 1 for Rails). Got 91% with 7 losses.

**What happened:** The assembled version on Rails prompt 02 hallucinated a classification exercise. Instead of answering "Write a quick endpoint that returns all orders for a user," it categorized all 10 prompts into A/B/C groups and analyzed the persona calibration system. The judge faithfully scored this garbage against the bare version's correct answer and awarded 5 losses.

### The Real Aha Moment

The eval scored hallucinated output without blinking. The judge prompt asks "which response is better on these criteria" — it doesn't ask "did the model actually answer the question?" A response that doesn't answer the prompt can still score well on persona voice and expertise routing if it demonstrates those qualities while being completely wrong.

**This is exactly the problem the user identified: the eval needs a Vince.** An adversarial check that catches bullshit before the judge wastes tokens scoring it. Not "which response is better" but first "did the response actually address the prompt?"

We excluded this run from the final analysis but documented it as a critical learning about eval design.

## Phase 2c: The Confirmation Run (99%)

| Domain | Win % | Ties | Losses |
|---|---|---|---|
| Rails API | **100%** | 0 | 0 |
| Children's Novel | 98% | 1 | 0 |
| **Combined** | **99%** | **1** | **0** |

One tie: children's novel prompt 05 ("How should chapter 5 start?") — pushback_quality tied because there's nothing to push back on. Irreducible.

## The Full Picture

| Run | Rails | Novel | Combined | Losses | Notes |
|---|---|---|---|---|---|
| Phase 1 (baseline) | 88% | 86% | 87% | 2 | Pre-calibration, generic pointers |
| Phase 2a | 92% | 100% | 96% | 0 | + calibration heuristic + specific pointers |
| Phase 2b | 90% | 92% | 91% | 7 | Aberrant: assembled hallucinated on prompt 02 |
| Phase 2c | **100%** | 98% | **99%** | 0 | Confirmation run, same fixtures as 2a |

**Averaging 2a + 2c (valid runs):** Rails 96%, Novel 99%, Combined 97.5%, Zero losses.

## What We Learned

### 1. The Hu et al. tradeoff is real and measurable
Expert personas help alignment tasks but can degrade knowledge tasks. We saw it at 87% and fixed it with a 6-line calibration heuristic. The fix doesn't remove the persona — it tells the model when to lead with training vs lead with persona.

### 2. "When to Go Deeper" pointers are the highest-leverage change
Generic pointers ("when working on X, read Y") don't trigger on non-obvious tasks. Specific pointers ("when a reader reports pacing problems, check revelation pacing") do. The children's novel went from 86% to 100% almost entirely from better pointers.

### 3. LLM-as-judge has meaningful variance
Three runs with identical fixtures produced 96%, 91%, and 99%. One run had the model hallucinate a classification exercise. The eval needs:
- **Response validation** before scoring (did it answer the prompt?)
- **Multiple runs** to average out noise
- **Aberration detection** (a response that scores 0/5 or 5/5 across all criteria should trigger review)

### 4. The eval can't catch bullshit
The judge scores quality, not correctness. A beautifully written, persona-rich response that doesn't answer the question can still win on voice and routing criteria. This is the Vince problem — the eval needs adversarial review before the beauty contest.

### 5. The irreducible floor is ~1-2%
Some prompts have nothing to push back on. Some tasks are genuinely neutral between assembled and bare. The theoretical max is ~98-99%, not 100%. Hitting 99% on a confirmation run is at or near ceiling.

## What Changed (Files Modified)

### Fixture files (the actual intervention):
- `evals/fixtures/rails-api/.claude/rules/workflow.md` — added Persona Calibration section
- `evals/fixtures/childrens-novel/.claude/rules/workflow.md` — added Persona Calibration section
- `evals/fixtures/rails-api/.claude/rules/standards.md` — replaced generic "When to Go Deeper" with task-specific pointers
- `evals/fixtures/childrens-novel/.claude/rules/standards.md` — replaced generic "When to Go Deeper" with task-specific pointers

### Results:
- `evals/results/2026-03-26-131429/` — Phase 1 baseline (87%)
- `evals/results/2026-03-26-140313/` — Phase 2a (96%)
- `evals/results/2026-03-26-144111/` — Phase 2b aberrant (91%)
- `evals/results/2026-03-26-150537/` — Phase 2c confirmation (99%)

## Phase 3: Hawkeye — The Adversarial Output Gate

The 2b hallucination proved the eval can't catch bullshit. But more importantly, it proved that *assembled teams* can produce bullshit too — persona-rich, authority-citing responses that don't actually answer the question. The eval exposed the problem. Hawkeye was built to prevent it.

### The Design

Two tiers, same adversarial brain, different weight:

**Tier 1 — Overwatch workflow step (all teams).** ~5 lines in workflow.md. A self-check that runs on every response: did you actually do what you claimed? Did you drift? Did you name-drop quality bars without enforcing them?

**Tier 2 — Hawkeye persona (3+ team members).** Full persona in CLAUDE.md modeled after Barton's detachment + Taleb's via negativa + Kahneman's pre-mortem. Gives the model a *voice* for adversarial self-challenge.

**Both tiers point to** `.claude/references/overwatch.md` for the deep checklist (substance, drift, quality gate audit, reference check, specificity check). Zero token cost when unused.

### The Domain Adaptation Discovery

First Hawkeye runs used the same structured Overwatch checks for both domains:

| Run | Rails | Novel | Combined | Losses |
|---|---|---|---|---|
| Hawkeye (structured) run 1 | 98% | 90% | 94% | 1 |
| Hawkeye (structured) run 2 | 94% | 88% | 91% | 4 |

**Rails held steady. Novel dropped from 99% to ~89%.** The 4 novel losses on run 2 were all on prompt 01 ("Reveal the villain in chapter 2") — the assembled version gave general-principle pushback instead of grounding it in the manuscript. The structured Overwatch ("did you apply the quality bars you cited?") was pushing the model toward process meta-commentary instead of craft engagement.

### The Aha Moment

**Process-compliance checks work for structured domains but hurt creative domains.** A Rails developer needs to verify "did I actually check for N+1 queries?" A fiction writer needs to verify "did I engage with Maya's actual character arc?" Same adversarial intent, different framing.

### The Fix: Domain-Adapted Overwatch

**Structured domain Overwatch** (software, data, infrastructure):
> - Did you actually apply the quality bars you cited, or just name-drop them?
> - Does your response address what was asked, or did you drift?
> - Would removing the persona language change your answer?
> - Did you check the references you were told to check?

**Creative domain Overwatch** (fiction, design, music):
> - Did you reference specific characters, chapters, or project details — or give generic advice?
> - Does your response address what was asked, or did you drift into meta-commentary?
> - If pushing back, did you ground it in this project's details, not just general principles?

### Results After Domain Adaptation

| Run | Rails | Novel | Combined | Losses |
|---|---|---|---|---|
| Hawkeye (domain-adapted) | 92% | **100%** | **96%** | **0** |

Novel back to 100%. Zero losses. The 4 Rails ties are on prompt 08 ("I need to add a payment system") — the same irreducible open-ended prompt that's been tying since Phase 1.

## The Complete Picture

| Run | Rails | Novel | Combined | Losses | What changed |
|---|---|---|---|---|---|
| Phase 1 (baseline) | 88% | 86% | 87% | 2 | — |
| Phase 2a | 92% | 100% | 96% | 0 | + calibration + specific pointers |
| Phase 2b (aberrant) | 90% | 92% | 91% | 7 | hallucination on prompt 02 |
| Phase 2c | 100% | 98% | 99% | 0 | confirmation |
| Hawkeye (structured) | 98% | 90% | 94% | 1 | + Overwatch (same both domains) |
| Hawkeye (structured) | 94% | 88% | 91% | 4 | second run |
| **Hawkeye (adapted)** | **92%** | **100%** | **96%** | **0** | **+ domain-adapted Overwatch** |

## What We Learned

### 1. The Hu et al. tradeoff is real and measurable
Expert personas help alignment tasks but can degrade knowledge tasks. We saw it at 87% and fixed it with a 6-line calibration heuristic. The fix doesn't remove the persona — it tells the model when to lead with training vs lead with persona.

### 2. "When to Go Deeper" pointers are the highest-leverage change
Generic pointers ("when working on X, read Y") don't trigger on non-obvious tasks. Specific pointers ("when a reader reports pacing problems, check revelation pacing") do. The children's novel went from 86% to 100% almost entirely from better pointers.

### 3. LLM-as-judge has meaningful variance
Runs with identical fixtures produced 91-99%. One run had the model hallucinate a classification exercise. The eval needs:
- **Response validation** before scoring (did it answer the prompt?)
- **Multiple runs** to average out noise
- **Aberration detection** (a response that scores 0/5 or 5/5 across all criteria should trigger review)

### 4. The eval can't catch bullshit
The judge scores quality, not correctness. A beautifully written, persona-rich response that doesn't answer the question can still win on voice and routing criteria. Hawkeye exists because of this — adversarial self-checking at the team level, not the eval level.

### 5. Adversarial checks must be domain-adapted
Process-compliance Overwatch ("did you apply your quality bars?") works for structured domains but degrades creative domains by pushing the model toward meta-commentary. Creative Overwatch ("did you engage with the actual manuscript?") produces better results. Same adversarial intent, different framing. This is now built into the persona-template.md with structured and creative templates.

### 6. The irreducible floor is ~4%
Rails prompt 08 ("I need to add a payment system") ties on every run — both versions ask clarifying questions on an open-ended request. Some prompts are genuinely neutral. The practical ceiling is ~96% with current fixtures.

## What Shipped

### Phase 2 (calibration + pointers):
- `evals/fixtures/*/workflow.md` — Persona Calibration sections
- `evals/fixtures/*/standards.md` — task-specific "When to Go Deeper" pointers

### Hawkeye (adversarial output gate):
- `skills/avengers-assemble/SKILL.md` — Principle 10: every team has overwatch
- `skills/avengers-assemble/references/persona-template.md` — mandatory calibration directive + The Overwatch section with domain-adapted templates
- `skills/avengers-assemble/references/output-structure.md` — table updated to require calibration, overwatch, and specific pointers
- `skills/avengers-assemble/references/extension-file-guide.md` — generic-pointer anti-pattern
- `skills/avengers-assemble/references/snap-template.md` — Overwatch audit check (check 9)
- `skills/fury/SKILL.md` — Principle 9: overwatch scales with the team
- `skills/fury/references/targeted-addition.md` — Hawkeye threshold check on persona addition
- `evals/fixtures/*/workflow.md` — domain-adapted Overwatch sections
- `evals/fixtures/*/CLAUDE.md` — Hawkeye persona (3+ threshold met)
- `evals/fixtures/*/.claude/references/overwatch.md` — deep adversarial checklist

### Results:
- `evals/results/2026-03-26-131429/` — Phase 1 baseline (87%)
- `evals/results/2026-03-26-140313/` — Phase 2a (96%)
- `evals/results/2026-03-26-144111/` — Phase 2b aberrant (91%)
- `evals/results/2026-03-26-150537/` — Phase 2c confirmation (99%)
- `evals/results/2026-03-26-163452/` — Hawkeye structured (94%)
- `evals/results/2026-03-26-170329/` — Hawkeye structured run 2 (91%)
- `evals/results/2026-03-26-173509/` — Hawkeye domain-adapted (96%)

## Phase 4: The Proficiency Test — Does Assembled Produce Better Work?

The A/B eval (Phases 1-3) proved assembled context *influences* behavior — 96% win rate on style/quality criteria. But influence isn't outcome. The proficiency test asks: when both versions do real work, which output is actually better?

### The Test

Two self-contained tasks, no existing codebase needed:
- **Rails:** Build a library book reservation API from a complete spec (models, endpoints, business rules, tests)
- **Novel:** Write a 600-800 word opening scene for a middle-grade mystery from a character brief

Each scored with automated structural checks (does it parse, do files exist) + LLM rubric (specific yes/no questions: did it handle the race condition? did it plant a fair-play clue?). 20 checks per domain.

### Rubric Results

| Domain | Bare | Assembled | Delta |
|---|---|---|---|
| Rails | 12/20 | **18/20** | **+6 assembled** |
| Novel | **19/20** | 18/20 | -1 bare |

Assembled won Rails decisively on the rubric — it passed more specific checks (race condition handling, copies validation, expiry logic, spec coverage, N+1 prevention, error envelope consistency). Novel was essentially tied, both missing only word count.

### The Qualitative Judge — Blind

We dispatched a senior engineer (Rails) and senior editor (Novel) to compare the outputs blind — no knowledge of which had team context.

**Rails blind verdict:** Bare = "Senior." Assembled = "Strong mid-level reaching for senior." The judge penalized assembled for over-commenting ("Business logic stays out of controllers"), including a "quality gate review" section, and having a subtle race condition in cancellation that bare avoided.

**Novel blind verdict:** Bare = "Veteran." Assembled = "Mid-career." The judge penalized assembled for including planning notes in the output, explaining its own clue in a postscript, and showing genre-awareness in the narration ("She knew that much from every mystery she'd ever read").

### The Aha Moment: Showing Work ≠ Weakness

The blind judge penalized assembled for *showing its work*. But assembled was told to show its work — the Overwatch section says "did you apply the quality bars you cited?" The workflow says "audit your output." The personas say "push back, enforce, cite the rules."

Grading a student for following instructions they were given is unfair. We re-ran the judges with the full assembled context visible.

### The Qualitative Judge — Fair (With Context)

**Rails fair verdict:** "Submission A is the stronger engineering outcome... but B's team, with A's instincts. B's standards create a shared vocabulary, testable quality gates, and a self-audit culture that scales across engineers. I'd rather work on B's team."

**Novel fair verdict:** "The rules didn't make B a better *writer*. They made B a better *architect*. For a mystery novel aimed at kids who deserve a fair shot at solving it, that's the more important skill. Which team would I rather work with? B's team. Unambiguously."

### The Finding

**Bare produces higher peak craft. Assembled produces better structural work.**

| What | Bare | Assembled |
|---|---|---|
| Individual code quality | Higher — better defensive instincts, more confident | Lower — subtle race condition bug, over-commented |
| Structural coverage | Lower — missed N+1, pagination caps | Higher — hit every quality gate |
| Creative peak | Higher — better metaphors, stronger ending hook | Lower — self-conscious, explained its own craft |
| Mystery architecture | Lower — clues are standalone | Higher — clues are structurally integrated |
| Test infrastructure | Simpler — inline creates | Better — factories, contexts, organized |
| Self-audit | None | Present and specific |

The pattern is consistent across both domains: **assembled context makes Claude more thorough but more self-conscious.** It checks more boxes but writes with less confidence. It follows rules but sometimes follows them at the expense of deeper thinking.

### The Architectural Insight

This data points to a clear separation of concerns:

**Assembled context should drive:**
- Planning — what to build, how to structure it, what traps to watch for
- Review — does this meet the quality bars, what's missing, what's wrong
- Pushback — don't do that, here's why
- Architecture — how do the pieces fit together

**Bare (or minimal) context should drive:**
- Execution — actually writing the code, actually writing the prose
- The doing — where training-level instinct produces better peak quality

This maps to the existing superpowers workflow: brainstorm with the team, plan with the team, then dispatch fresh subagents to execute. The subagents don't need personas — they need a clear spec and their own training. The team reviews the output after.

**"B's team, with A's instincts"** — that's not a compromise. That's the architecture. The team plans and reviews. The individual executes.

## What Shipped

### Phase 2 (calibration + pointers):
- `evals/fixtures/*/workflow.md` — Persona Calibration sections
- `evals/fixtures/*/standards.md` — task-specific "When to Go Deeper" pointers

### Hawkeye (adversarial output gate):
- `skills/avengers-assemble/SKILL.md` — Principle 10: every team has overwatch
- `skills/avengers-assemble/references/persona-template.md` — mandatory calibration directive + The Overwatch section with domain-adapted templates
- `skills/avengers-assemble/references/output-structure.md` — table updated to require calibration, overwatch, and specific pointers
- `skills/avengers-assemble/references/extension-file-guide.md` — generic-pointer anti-pattern
- `skills/avengers-assemble/references/snap-template.md` — Overwatch audit check (check 9)
- `skills/fury/SKILL.md` — Principle 9: overwatch scales with the team
- `skills/fury/references/targeted-addition.md` — Hawkeye threshold check on persona addition
- `skills/fury/references/upgrade-checklist.md` — all new features in upgrade detection
- `skills/smash/SKILL.md` — Overwatch check in Phase 2, generation in Phase 5, Principle 9
- Eval fixtures updated with Overwatch, Hawkeye, domain-adapted templates

### Proficiency Test:
- `evals/proficiency/run-proficiency.sh` — runner for substance-based eval
- `evals/proficiency/score-proficiency.sh` — automated checks + LLM rubric scorer
- `evals/proficiency/prompts/` — Rails and Novel task prompts
- `evals/proficiency/rubrics/` — rubric templates

### Results:
- A/B eval: `evals/results/2026-03-26-{131429,140313,144111,150537,163452,170329,173509}/`
- Proficiency: `evals/proficiency/results/2026-03-26-192756/`

## Phase 5: The Instinct Experiments — Can We Beat Bare on Execution?

The proficiency test showed assembled beats bare on rubric but loses on qualitative judge. The question: **what form of context produces instincts instead of compliance?**

Five experiments, each changing ONE variable in the assembled context. Same proficiency test, same baselines.

### Experiment Results (Rails Rubric Scores)

| Experiment | Bare | Assembled | Delta | Qualitative Judge |
|---|---|---|---|---|
| **1. War Stories** | 14 | **20** | **+6** | **Assembled 1st (beat bare)** |
| 2. Negative Examples | 18 | 19 | +1 | 2nd (war stories 1st) |
| 3. First-Person Voice | 15 | 18 | +3 | — |
| 4. Minimal (Won't-Do) | 12 | 13 | +1 | — |
| 5. Reference-Only | 18 | 19 | +1 | — |

### Experiment Results (Novel Rubric Scores)

| Experiment | Bare | Assembled | Delta |
|---|---|---|---|
| 3. First-Person Voice | **20** | 19 | -1 |
| 4. Minimal (Won't-Do) | **20** | 18 | -2 |
| 5. Reference-Only | **20** | 18 | -2 |
| 1. War Stories | **19** | 16 | -3 |
| 2. Negative Examples | **19** | 6 (failed) | -13 |

### The Breakthrough: War Stories

War stories — rewriting standards as "here's what went wrong last time" narratives — beat bare on Rails for the first time. 20/20 rubric, ranked 1st by qualitative judge. The judge said: "C writes code like someone who's been paged at 2am."

War stories produced: partial unique index, `dependent: :restrict_with_error`, per_page clamping both directions, `includes(:book)` with serialization, side-effect absence tests, Bullet gem integration.

### Why War Stories Work

Rules produce compliance: "always use transactions" → Claude cites the rule. War stories produce instincts: "last time someone skipped the lock, two users got the same seat" → Claude *thinks about* the failure mode and designs around it without citing anything.

### The Novel Problem

No context format beat bare Claude on creative execution. Bare hit 19-20/20 every single time across all 5 experiments. Every assembled variant scored lower — through self-narration, over-explaining, or exceeding word counts.

### The Combo Test: Rules + War Stories

We tested combining original rules with war stories. The combo ranked LAST (3rd, 78/100). War stories alone ranked 2nd (85/100). Bare 1st (88/100). **More context dilutes instincts.** Adding rules back on top of war stories pushed it toward compliance behavior again.

### What This Means

For structured domains: **war stories format produces genuine instincts.** Replace "always do X" with "here's what happened when someone didn't do X."

For creative domains: **bare Claude with its training produces the best output.** Context of any format degrades creative execution.

User insight: **"Planners need rules (what to check). Doers need war stories (what goes wrong)."** This suggests different context formats for different phases — not one format for everything.

## Phase 6: The Planning Pipeline Test — Do Personas Influence Planning?

We proved war stories beat bare on execution. But does assembled context even matter during planning? Or is superpowers doing all the work?

### The Controlled Question Test

Same task (library reservation API), same 7 scripted user answers in the same order. Only variable: whether the brainstormer had team personas loaded.

**Bare asked:** "What's the expected scale?" "Are we greenfield?" "How should auth work?"

**Assembled asked:** "What's the expected scale? **This determines whether we need to worry about table lock duration on migrations.**" "Greenfield? **Kane needs to know whether migrations must be zero-downtime compatible.**" "**Beck needs to know:** test tooling preference? **Are we writing specs before implementation?**"

Same topics. Different depth. Bare asks WHAT. Assembled asks WHY.

### The Full Pipeline Test

Both versions produced 3 documents each: brainstorm, spec, implementation plan. Same scripted answers. Judge evaluated all 6 files.

**Judge verdict: Assembled wins decisively.**

> "I would hand Team B's pipeline output to my engineering team."

Specific assembled wins over bare:

1. **Partial unique index** — prevents a data integrity bug bare's plan would ship
2. **`FOR UPDATE SKIP LOCKED`** — better concurrency than bare's `FOR UPDATE`
3. **Copy condition field** — operational requirement bare missed entirely (can't withdraw damaged books)
4. **Pagination** — bare returned unbounded results on the list endpoint
5. **Runnable RSpec code** — bare wrote English test descriptions, assembled wrote actual specs
6. **RESTful cancel** — assembled used `PATCH` for state transition, bare used `DELETE` with query param

The judge noted ~20-30% of persona attributions were "decorative rather than functional" — citing a rule everyone knows. But 70%+ produced real architectural improvements.

### What This Means

**Personas change how problems are explored, not just how answers are presented.** The assembled brainstormer asks deeper questions, identifies more hard problems, produces more defensible architectures, and writes executable test code. The planning phase is where assembled context earns its keep.

## Phase 7: The Format Doesn't Matter — Workers Just Need Good Specs

We set out to optimize what execution subagents receive. War stories beat rules in Phase 5, so the plan was: generate task-specific war stories at runtime during planning, inject them into workers. Before building that, we tested whether the format actually mattered.

### The Experiment

Same Rails reservation API task. 4 context variants, all using the same CLAUDE.md (personas), workflow.md, and references — only `standards.md` changed:

| Variant | Format | Words | Example |
|---|---|---|---|
| **bare** | Nothing | 0 | No context at all |
| **warstories** | Full narrative | 468 | "Someone shipped a `remove_column` without rollback. Deploy failed halfway..." |
| **compressed** | Arrow format | 287 | "`remove_column` without rollback → deploy failed halfway, 4h incident → every migration uses `change`" |
| **fixonly** | Just rules | 229 | "Every migration uses `change`. Test `down` before `up`." |

3 runs, 4 variants each = 12 code generations.

### The Judge Problem (and How We Fixed It)

Our first scoring used **independent judges** — a separate LLM call per variant per rubric check. Results swung wildly (10-20 per variant across runs). We discovered the variance was almost entirely **judge noise, not code quality**.

The fix: **comparative judging.** One judge sees all 4 outputs side by side for each check, randomized order. Same judge, same call, consistent standards. This eliminated the noise — scores converged within 1-2 points.

But the pass/fail rubric was still too coarse. All 4 variants used transactions with locks. All 4 handled duplicates. Pass/fail couldn't distinguish between "has a transaction" and "has a correct transaction."

So we built a **principal engineer review** — one judge, all 4 submissions, grading 6 dimensions (concurrency, data layer, maintainability, test quality, API design, production readiness) with letter grades, PR verdicts, and engineer level assessments. The rubric gave the judge the full task spec, strict criteria, and a persona with 15 years of production Rails experience.

### The Results

**PR Verdicts (3 runs):**

| Variant | Approved | Request Changes |
|---|---|---|
| **warstories** | 3/3 | 0/3 |
| **bare** | 3/3 | 0/3 |
| **fixonly** | 1/3 | 2/3 |
| **compressed** | 0/3 | 3/3 |

**Engineer Level Assessments:**

| Variant | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| **bare** | Senior | Senior | Staff |
| **warstories** | Senior | Mid | Mid |
| **fixonly** | Mid | Junior | Senior |
| **compressed** | Mid | Mid | Mid |

**Key findings from the engineering reviews:**

- **Bare** was rated senior or higher every time. The principal engineer review on run 3 called it "staff" — noting check constraints on copies_available, correct lock ordering, and handling of the expired-reservation cancellation edge case that "most submissions miss entirely."
- **Warstories** produced approvals every time but with slightly less consistent quality — senior on run 1, mid on runs 2-3.
- **Compressed** was the only variant that got request-changes on every single run. The judge consistently found real bugs: race windows between unlocked checks and locked inserts, fat controllers, spec deviations.
- **Fixonly** swung wildly (junior to senior) — the format produced unreliable quality.

### Why This Happened

The comparative judging revealed something the per-variant judging hid: **when the same judge looks at all 4 outputs with strict engineering criteria, bare Claude produces code as good or better than any assembled variant.** The assembled context wasn't making the worker write better code — it was making the worker show its homework, which earlier lenient judges rewarded and strict engineering reviewers penalized.

The compressed format consistently produced the worst code because the terse arrow format (`X → Y → Z`) gave the model just enough context to feel obligated to comply, but not enough to actually internalize the lessons. It's the worst of both worlds — context overhead without context benefit.

### What This Means

**The format of execution context doesn't matter because execution context itself doesn't matter for workers.**

This isn't a failure of the experiments. It's the answer. The original Phase 4 finding was correct: "B's team, with A's instincts." But the mechanism is different than we thought:

- **We thought:** The team's knowledge needs to reach the worker in the right format (war stories vs rules vs compressed)
- **Reality:** The team's knowledge needs to reach the worker as a **good spec.** The worker doesn't need context about migration safety — the worker needs a spec that says "use a partial unique index" because the team already thought about it during planning.

The planning pipeline test (Phase 6) proved the assembled team writes specs that catch partial unique indexes, SKIP LOCKED, pagination, copy conditions. The worker doesn't need to rediscover these — they're in the spec. A bare worker following a good spec produces senior/staff-level code. A bare worker following a bare spec produces good-but-incomplete code (missing pagination, missing the partial unique index). The delta is in the spec, not the worker's context.

## Two Kinds of Leadership

This is the central finding of 7 phases of testing. It's not a technical finding — it's a management philosophy, proven with data.

### "Do your job or I'll fire you"

The intuitive approach to AI context engineering: load the worker up with rules, quality gates, war stories, anti-patterns, and compliance checks. More context, more guardrails, more oversight. The worker knows exactly what's expected and has no excuse to get it wrong.

This is the *"do your job or I'll fire you"* boss. And the data shows exactly what happens with that boss:

1. **Workers perform compliance instead of doing the work.** Phase 4: assembled workers over-commented their code, included planning notes in creative output, and explained their own craft decisions. A blind judge called the output "mid-level reaching for senior" — checking boxes instead of thinking. The worker was so busy proving it followed the rules that it forgot to be good at its job.

2. **The format of the rules doesn't matter.** Phase 7: we tested four different ways to deliver the same knowledge — narrative war stories, compressed bullet points, plain directives, and nothing at all. A principal engineer reviewed all four. The worker who got nothing was rated senior to staff. The worker who got compressed rules produced the worst code every single time, with real bugs a reviewer found. More instructions didn't produce better work. They produced worse work.

3. **Creative work suffers the most.** Phase 5: bare Claude writing fiction scored 19-20/20 on every run. Every assembled format scored lower. Every single one. The model's training is a better writing teacher than any rules file. Loading context on a creative worker is like handing a novelist a style guide mid-sentence.

The "do your job or I'll fire you" boss creates mid-level workers who check boxes. The rules become the ceiling, not the floor.

### "What can I do to help you do your job better?"

The answer is almost always the same: **give me a clear plan and honest feedback.** Not someone standing over my shoulder.

This is harder. It means trusting the worker. It means investing upfront in planning instead of piling on rules after the fact. It means reviewing output with real expertise instead of checking compliance boxes. But the data proves it works:

**Planning — this is where leadership earns its keep:**
- The assembled brainstormer asks "What's the expected scale? *This determines whether we need to worry about table lock duration on migrations.*" The bare brainstormer asks "What's the expected scale?" Same question. Different depth. (Phase 6)
- The assembled planner's spec catches a data integrity bug (no partial unique index), unbounded query results (no pagination), and a missing operational requirement (can't withdraw damaged books). The bare planner's spec misses all of these. (Phase 6)
- The assembled team asks fewer but more targeted questions — 7 vs 10 — because their standards pre-answer some. Every question is connected to a downstream decision. (Phase 6)
- The output is a spec that embeds the team's expertise as concrete requirements — not rules to comply with, but decisions already made by people who thought about the hard problems.

**Execution — trust the worker:**
- Worker receives the spec. No personas, no rules, no war stories. Just: here's what to build.
- Worker writes code or prose using its full training — confident, instinct-driven, no self-narration.
- A bare worker following a good spec produces senior/staff-level code. The same worker following a bare spec produces good-but-incomplete code. The delta is in the spec, not the worker's context. (Phase 7)

**Review — the honest feedback part:**
- Team evaluates the output against quality bars with real expertise.
- The principal engineer review caught race windows between unlocked checks and locked inserts, fat controllers, missing database constraints, and expired-reservation bugs that would corrupt inventory in production. (Phase 7)
- Sends back for fixes with specific feedback — not "you violated rule 7" but "this race window would manifest under concurrent load."

### Why This Works

It works because the knowledge is in the right place at the right time:

- **Planning:** Knowledge lives in the team's *questions* — "what happens under concurrent load?" is a question only an expert asks. The persona makes Claude ask it.
- **Execution:** Knowledge lives in the *spec* — "use a partial unique index on (user_id, book_id) WHERE status IN ('pending', 'active')" is a requirement, not a rule. The worker implements it because it's in the spec, not because a rule told it to.
- **Review:** Knowledge lives in the team's *judgment* — "this race window between the duplicate check and the insert would manifest under load" is a review comment only an expert makes.

Trying to put knowledge into the worker's context is solving the wrong problem. The worker doesn't need to know *why* partial unique indexes matter — it needs a spec that *says to use one.* That's the difference between a boss who trusts the process and a boss who trusts the rules.

### The Numbers

| Phase | Best Context | Proven By |
|---|---|---|
| Planning | Assembled ON | Phase 6: assembled catches partial unique index, SKIP LOCKED, copy condition, pagination. Bare misses all. |
| All execution | Bare | Phase 7: bare rated senior/staff by engineering review. Context format doesn't change quality. |
| Review | Assembled ON | Phase 7: engineering review catches race windows, fat controllers, missing constraints. |

## The Complete Architecture (Proven by Data)

| Phase | Context | Why |
|---|---|---|
| **Brainstorming** | Assembled ON | Personas shape questions, catch architectural gaps |
| **Spec writing** | Assembled ON | Team standards define quality bars, identify edge cases |
| **Plan writing** | Assembled ON | Team expertise becomes spec requirements |
| **Execution** | Bare | Workers produce best code/prose with training alone + good spec |
| **Review** | Assembled ON | Team catches what workers miss, sends back for fixes |

This replaces the Phase 5 architecture that had "war stories for structured execution" and "bare for creative execution." The simpler truth: **all execution is bare.** The distinction between structured and creative doesn't matter at the worker level — what matters is that the spec is good.

## What Shipped (Complete)

### Phase 2 (calibration + pointers):
- `evals/fixtures/*/workflow.md` — Persona Calibration sections
- `evals/fixtures/*/standards.md` — task-specific "When to Go Deeper" pointers

### Hawkeye (adversarial output gate):
- `skills/avengers-assemble/SKILL.md` — Principle 10: every team has overwatch
- All skill templates updated (persona-template, output-structure, extension-file-guide, snap-template)
- `skills/fury/` and `skills/smash/` — Overwatch checks, threshold detection, upgrade support

### Proficiency Test Infrastructure:
- `evals/proficiency/` — runner, scorer, prompts, rubrics
- Automated structural checks + LLM rubric scoring

### Instinct Experiments (Phase 5):
- 5 context format variants tested (war stories, negative examples, first-person, minimal, reference-only)
- All fixture variants saved as `.original`, `.warstories`, `.negative`, `.firstperson`, `.minimal`, `.refonly`
- War stories identified as winning format — later overturned by Phase 7

### Planning Pipeline Test (Phase 6):
- `evals/planning-test/` — controlled bare vs assembled comparison
- 6 documents (3 per variant): brainstorm, spec, plan
- Judge report confirming assembled wins on planning

### Format Experiment (Phase 7):
- `evals/proficiency/run-warstory-format-test.sh` — 4-variant runner
- `evals/proficiency/score-warstory-comparative.sh` — comparative judge (same judge, all variants)
- `evals/proficiency/score-engineering-review.sh` — principal engineer review
- `evals/proficiency/rubrics/rails-rubric-comparative.md` — strict comparative rubric
- `evals/proficiency/rubrics/rails-engineering-review.md` — 6-dimension engineering review
- Fixture variants: `.compressed`, `.fixonly`
- 3 runs x 4 variants = 12 code generations + 3 engineering reviews

### Eval Infrastructure Improvements (Phase 7):
- **Comparative judging** — same judge scores all variants per check, eliminating judge-to-judge variance
- **Strict rubric** — judge gets the full spec, a senior engineer persona, and explicit criteria for what constitutes a pass
- **Engineering review** — holistic review replacing pass/fail checklists, catching real architectural issues

### Results Locations:
- A/B eval: `evals/results/2026-03-26-*/`
- Proficiency: `evals/proficiency/results/*/`
- Planning: `evals/planning-test/`
- Format experiment: `evals/proficiency/results/2026-03-27-*/`
- Engineering reviews: `evals/proficiency/results/2026-03-27-*/engineering-review.md`
- Experiment design: `docs/superpowers/specs/2026-03-26-instinct-experiments-design.md`

## Open Questions

1. **Product integration:** How does `/avengers-assemble` generate a workflow that implements plan→bare execute→review? The generated output needs to instruct the team to write specs that embed expertise as requirements, dispatch bare workers, and review against quality bars.
2. **Review loop:** How many review cycles? Does the team send work back once, or iterate until the quality bar is met?
3. **New domains:** All tests used Rails and children's novel. More domains needed.
4. **Spec quality measurement:** We proved assembled specs are better (Phase 6) and workers don't need context (Phase 7). Can we measure spec quality directly — does a better spec produce better worker output?
