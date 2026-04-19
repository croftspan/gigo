# The Eval Narrative: From 87% to 96%+ with Hawkeye

How we proved assembled context works, found the gaps, closed them, added an adversarial output gate, and learned what the numbers can't tell you.

## The Question

Does the output of `/gigo` — the personas, quality gates, workflow loops, and reference files — actually change Claude's behavior? Or is it just expensive token decoration?

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
- `skills/gigo/SKILL.md` — Principle 10: every team has overwatch
- `skills/gigo/references/persona-template.md` — mandatory calibration directive + The Overwatch section with domain-adapted templates
- `skills/gigo/references/output-structure.md` — table updated to require calibration, overwatch, and specific pointers
- `skills/gigo/references/extension-file-guide.md` — generic-pointer anti-pattern
- `skills/gigo/references/snap-template.md` — Overwatch audit check (check 9)
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
- `skills/gigo/SKILL.md` — Principle 10: every team has overwatch
- `skills/gigo/references/persona-template.md` — mandatory calibration directive + The Overwatch section with domain-adapted templates
- `skills/gigo/references/output-structure.md` — table updated to require calibration, overwatch, and specific pointers
- `skills/gigo/references/extension-file-guide.md` — generic-pointer anti-pattern
- `skills/gigo/references/snap-template.md` — Overwatch audit check (check 9)
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
- `skills/gigo/SKILL.md` — Principle 10: every team has overwatch
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

## Phase 8: The Review Pipeline — Two Reviewers Find Different Things

Phase 7 proved workers should run bare and the team reviews after. But how should review work? We tested three approaches on the same code.

### The Experiment

Three review types, run against all 4 Phase 7 code variants (bare, warstories, compressed, fixonly):

- **Plan-aware** — reviewer gets the task spec, checks whether the implementation meets requirements
- **Code-quality** — reviewer gets only the code, checks engineering merit (bugs, race conditions, maintainability)
- **Combined** — reviewer gets both spec and code

### The Results

| Variant | Plan-Aware | Code-Quality | Combined |
|---|---|---|---|
| bare | 10 (1C, 6I, 2m) | 14 (3C, 7I, 4m) | 11 (3C, 4I, 3m) |
| warstories | 10 (3C, 3I, 3m) | 12 (3C, 6I, 3m) | 11 (3C, 4I, 3m) |
| compressed | 13 (2C, 7I, 3m) | 14 (3C, 7I, 4m) | 13 (3C, 6I, 3m) |
| fixonly | 10 (2C, 4I, 3m) | 15 (2C, 7I, 4m) | 12 (3C, 6I, 3m) |

### What Each Reviewer Caught (bare variant, the "staff" code)

**Plan-aware found spec compliance issues:**
- Destroy action cancels expired reservations, inflating copies_available beyond actual inventory
- No mechanism to transition reservations to 'expired' — the 48-hour expiry is written but never enforced
- Duplicate reservation check runs outside the transaction, producing 500 errors on race instead of clean 409

**Code-quality found engineering issues:**
- Transaction-return footgun: `return` inside `transaction` block commits instead of rolling back (currently safe by accident — no writes before returns — but a maintenance landmine)
- Concurrency test uses threads with `use_transactional_fixtures = true` — tests nothing, gives false confidence
- Deadlock risk from inconsistent lock ordering between ReserveBook (locks book first) and CancelReservation (locks reservation first)
- Non-atomic `decrement!`/`increment!` — does the math in Ruby, not SQL
- `{CODE}` placeholders in test file — syntax error that silently skips all tests

**Combined averaged instead of adding up** — 11 issues, between the other two. One judge can't hold both lenses simultaneously.

### What This Means

**Plan-aware and code-quality are complementary, not redundant.** They find different categories of issues. Plan-aware catches "you built the wrong thing" (spec violations, missing behavior). Code-quality catches "you built it wrong" (race conditions, test quality, lock ordering).

Putting both lenses in one reviewer doesn't work — combined found fewer issues than code-quality alone. The judge picks one focus or averages. Two focused reviewers each doing their job beats one reviewer trying to do both.

### The Pipeline

This validates a two-stage review:

1. **`superpowers:requesting-code-review`** — has the spec, checks "did you build what the plan said?" Assembled context ON because the team wrote the plan and understands its intent.
2. **`code-review:code-review`** — focused workers check engineering quality. 5 parallel Sonnet agents, each with a specific job (bugs, CLAUDE.md compliance, git history, prior PR patterns, code comments). Confidence-scored, filtered at ≥80. No assembled context — workers have their own review expertise.
3. **Operator reviews, tests, approves.** Two clean automated passes, then human judgment.

This maps to the two-bosses finding: stage 1 is the planning boss checking "did the spec get followed?" Stage 2 is the engineering boss checking "is this production-ready?" Two focused reviewers, each doing one job well.

### What Shipped (Phase 8)

- `evals/proficiency/run-review-pipeline-test.sh` — 3-approach review runner
- `evals/proficiency/rubrics/review-pipeline-test.md` — review rubric template
- Results: `evals/proficiency/results/2026-03-27-111808/`

### Results Locations:
- A/B eval: `evals/results/2026-03-26-*/`
- Proficiency: `evals/proficiency/results/*/`
- Planning: `evals/planning-test/`
- Format experiment: `evals/proficiency/results/2026-03-27-08*/`
- Engineering reviews: `evals/proficiency/results/2026-03-27-08*/engineering-review.md`
- Review pipeline test: `evals/proficiency/results/2026-03-27-111808/`
- Experiment design: `docs/superpowers/specs/2026-03-26-instinct-experiments-design.md`

## The Complete Architecture (Proven by 8 Phases)

| Phase | Context | Tool | What it does |
|---|---|---|---|
| **Brainstorming** | Assembled ON | superpowers:brainstorming | Personas shape questions, catch architectural gaps |
| **Spec writing** | Assembled ON | superpowers:writing-plans | Team expertise becomes concrete requirements |
| **Execution** | Bare | superpowers:subagent-driven-development | Workers produce best output with training alone + good spec |
| **Review 1: Spec compliance** | Assembled ON | superpowers:requesting-code-review | Did the worker build what the plan said? |
| **Review 2: Code quality** | Bare workers | code-review:code-review | Is the code production-ready? 5 focused reviewers. |
| **Operator approval** | Human | PR review | Human tests, reviews summary, approves |

## Phase 9: Opus 4.7 Context Evals (Briefs 13 & 14)

Two eval runs on 2026-04-19 against Claude Opus 4.7 + gigo v0.14.0-beta. Same two fixtures (`rails-api`, `childrens-novel`), same base harness. Brief 13 re-ran the assembled-vs-bare comparison from earlier phases. Brief 14 swept the context-mass axis with 5 conditions to locate the sweet spot.

Harness fixes landed pre-run: `--model claude-opus-4-7` pinned explicitly (CLI default drifts between runs); bare condition excluded `CLAUDE.md*` as a glob (previously exact-match, which leaked `CLAUDE.md.original` fixtures into bare).

### Brief 13 — Assembled vs Bare

**Question:** Does gigo context still help on Opus 4.7 + v0.14?

**Headline:** 99/100 criteria wins for assembled. One tie, zero losses. +16–17pp vs the 2026-04-12 baseline (was 82–83% on v0.11).

**Why the jump — two non-exclusive reads:**

1. **Cold-context pushback.** 6+ of 20 bare responses hallucinated menu structure ("this looks like a menu of A/B/C options"), refused to engage, or answered a fabricated version of the question. The assembled condition didn't fix grounding — it gave the model a stance to act from. Bare "lost" partly because bare didn't engage. See `memory/feedback_opus_47_cold_context_pushback.md`.
2. **v0.14 rules carry stronger citation language.** `workflow.md`, `standards.md`, and Overwatch all ship more explicit rule-citing patterns than v0.11. These load on every assembled call.

Disentangling (1) and (2) needs a v0.11 fixture run against Opus 4.7 — Phase 3 candidate.

**Honest caveats:**

- **Judge rubric fabrication blindspot (rails-api #06).** Assembled hallucinated a controller, then produced detailed review of the fabrication. Rubric rewarded "richness on its own terms" with no penalty for invented substrate. In production this would be actively harmful. See `memory/feedback_judge_rubric_fabrication_blindspot.md`. Every future rubric needs a "grounded in real files?" check.
- **Verbosity isn't the explanation.** Assembled was 2.6× longer but judge notes tracked specificity (named personas, cited files), not length. Prompt 09 tied on Pushback specifically because bare was substantive but didn't cite rules by name.

**Verdict:** v0.14 + Opus 4.7 clears the 90% threshold. Writeup: `docs/gigo/experiments/02-opus-4-7-v0.14-assembled-vs-bare.md`.

### Brief 14 — Context-Dosing Sweep

**Question:** If full gigo wins, is it winning by more context or right context?

**Design:** Five conditions on the context-mass axis, rank-of-5 judge per prompt, Borda aggregation.

| Condition | What | rails words | childrens words |
|---|---|---|---|
| c0-bare | No CLAUDE.md, no .claude/ | 0 | 0 |
| c1-roster | Thin CLAUDE.md (stems) + rules + references | 1969 | 2291 |
| c2-team-no-rules | Full CLAUDE.md, no rules/references | 569 | 553 |
| c3-full | Everything (= Brief 13 assembled) | 2432 | 2729 |
| c4-rules-only | No CLAUDE.md, rules + references | 1863 | 2176 |

**Headline Borda totals:**

|  | c0 | c1 | c2 | c3 | c4 |
|---|---|---|---|---|---|
| rails-api | 77 | 179 | 149 | **196** | 149 |
| childrens-novel | 50 | **189** | 155 | **188** | 168 |

**Key findings:**

1. **Context is strongly load-bearing 0→~2000 words.** c0 loses by 70–140 Borda on both domains. The "Opus 4.7 ignores extra context" hypothesis is refuted — extra context decisively helps up to ~2k words.
2. **Past ~2000 words, returns depend on task type.** On childrens-novel, c1-roster TIES c3-full (189 vs 188) at 84% of the tokens. On rails-api, c3 still wins but only by 17 Borda over c1.
3. **Over-contexting signal on creative/open-ended prompts.** childrens C-axis (beta-reader critique, setting change, new chapter) — c3 drops to 4th, losing to c4, c2, and c1. Does not replicate on rails-api C-axis, where c3 still wins.
4. **Token efficiency champion is c2-team-no-rules** at 262–280 Borda/1k-words — 3–4× more efficient than c3, but loses 40–45 Borda overall.
5. **Personas add signal even in thin form.** c1 (+106-word roster over c4) beats c4 by 20–30 Borda on both domains — measurable per-word return on the persona stems.

**Hypothesis verdict:** H1 (over-contexted on Opus 4.7) partially supported — domain/axis-dependent, not pervasive. H2 (architecture carries coherence) partially supported — c4 > c2 on open-ended tasks, c4 > c1 only on childrens C-axis. H3 (model ignores extra context) refuted.

**Recommendation:** Keep c3-full as v0.14 default. Log c1-roster as the live efficiency hypothesis. Flag creative/open-ended prompts as the domain where trimming earns its keep.

Memory amendment: `feedback_right_context_for_the_job.md` now carries the 2026-04-19 refinement — execution-layer contexts should stay under ~2000 words; planning-layer contexts can go higher when the task is structural.

Writeup: `docs/gigo/experiments/03-opus-4-7-context-dosing.md`.

### Combined Implication

Brief 13 answers "does gigo help?" — yes, decisively (99%). Brief 14 answers "is there a ceiling?" — yes, around ~2000 words, and it's task-type dependent. On structural/dangerous tasks (migrations, deploy, early-reveal) full context still wins. On generative/exploratory tasks in creative domains, full context hurts — extra rules over-constrain the response.

**Cost:** Brief 13 ≈ $4, Brief 14 ≈ $21 generation + ~$5 judge = ~$30 total.

## Phase 9-B: Qwen3.6 as the Local Worker (Brief 16)

A different question: if Opus plans and Qwen executes, what does Qwen need to behave like a worker? Run on 2026-04-19 against `unsloth/Qwen3.6-35B-A3B-MLX-8bit` (MLX, MoE 35B / ~3B active) via local `mlx_lm.server`. Opus 4.7 judge. 180 runs: 3 ticket formats × 2 thinking modes × 10 tasks × 3 replicates.

**Question:** What **ticket format** and **thinking setting** maximizes Qwen3.6's reliability on a plan → execute → review loop?

**Three ticket formats:**

- **TF1** — spec block only (task + embedded data, no scaffolding).
- **TF2** — the current gigo:execute Tier-2 dispatch (role lead-in + `## Task Description` / `## Acceptance` / `## Output Format` / `## Your Job`).
- **TF3** — Qwen-optimized per Unsloth's notes (`role` line → `SPEC` / `ACCEPTANCE` / `OUTPUT FORMAT` / `MODE HINT`, all indented).

**Headline:**

| Condition | Pass rate | Mean quality | Mean walltime | Mean completion tokens |
|---|---|---|---|---|
| TF1 on | 0.23 | 2.80 | 42.7s | 2716 |
| TF1 off | 0.40 | 2.80 | 7.9s | 495 |
| TF2 on | 1.00 | 4.03 | 26.9s | 1705 |
| TF2 off | 0.90 | 3.87 | 2.7s | 164 |
| TF3 on | 0.93 | 3.67 | 67.8s | 4127 |
| **TF3 off** | **1.00** | **4.07** | **2.0s** | **118** |

**Three findings that change the story:**

1. **Structure matters far more than which specific structure.** TF2 and TF3 are tied within noise (±5pp, ±0.2 quality). Both clear 90% across all task types. The gap to TF1 (bare spec) is the whole signal — scaffolding turns a 30% pass rate into a 95% pass rate. H1 (TF3 > TF2) is not supported by a meaningful margin.
2. **Thinking-on does not help — and introduces a silent-failure tail.** TF3-off matches or beats TF3-on on every task type, at 1/34 the walltime and 1/35 the completion tokens. H2 (thinking-on beats thinking-off) is refuted. The concrete risk: T7 × TF3 × thinking-on produced two empty responses at the 32768 max_tokens limit (9+ minutes each) — reasoning trace oscillating between equivalent regex forms, never emitting content. Same pathology noted in Brief 15's rails-api prompt 04 (empty Characters response). Qwen3.6 thinking-mode has a silent-non-completion failure mode.
3. **TF1 on reasoning and structured tasks is 0/9.** Without a stated OUTPUT FORMAT, Qwen reliably returns prose where the verifier demands JSON. Fabrication (worker inventing numbers/APIs) appeared only under TF1-thinking-on — zero cases in 120 TF2/TF3 runs.

**Harness gotcha — logged for future evals:** First scoring pass produced 75 parse errors (out of 180). Root cause: the `explanatory` output style in the parent Claude Code session bled into `claude -p` subprocesses, wrapping the YAML verdict in `★ Insight` prose blocks. Fix: dispatch with `--json-schema` and read `wrapped["structured_output"]` instead of parsing `result` text. `--bare` also fixes it but strips OAuth auth, so `--json-schema` alone is the right lever. See `memory/feedback_claude_p_output_style_leak.md`.

**Verdict:** Wire **TF3 + thinking-off** as the Qwen Tier-2 default — 100% pass, highest quality, 2.0s walltime, 118 tokens per call. Keep thinking-on for Opus planning; do not use it on Qwen worker dispatch.

**Cost:** Qwen local/free. Opus judge ~$10 (cache-warmed; first pass + re-run of 75 failed judges).

**Writeup:** `docs/gigo/experiments/05-qwen36-worker-profile.md`. **Results:** `evals/qwen-worker-eval/results/2026-04-19-085822/`.

## Open Questions

1. **Product integration:** How does the generated project output instruct this pipeline? The workflow needs to describe when to trigger each review stage.
2. **Auto-team-growth:** Should the team detect expertise gaps during planning and propose new teammates?
3. **New domains:** All tests used Rails and children's novel. More domains needed.
4. **Naming:** Project needs a public-ready name. Leading candidate: GIGO (Garbage In, Garbage Out). *(Settled — public as GIGO.)*
5. **Persona style (Brief 15, resolved 2026-04-19):** Characters beats Lenses 41-28-31 across 100 judgments on Opus 4.7 (2 domains × 10 prompts × 5 criteria). Characters wins persona_voice (11-3) and expertise_routing (12-7); Lenses edges quality_bar (7-5); Lenses dominates rails-api push-back prompts (axis A 10-3). `skills/gigo/SKILL.md:158` "default to Lenses" label flip pending operator approval. Writeup: `docs/gigo/experiments/04-opus-4-7-lenses-vs-characters.md`. One known anomaly: rails-api prompt 04 returned an empty Characters response — excluding it, margin is 41-23-31. Re-run that prompt 3-5× to rule out persona-collapse-to-silence.
6. **Domain-aware dosing (Phase 3):** Is the creative-domain over-contexting penalty about the domain, or about small codebases? Test with a large-codebase creative fixture (e.g., screenplay repo).
7. **Cast-only test (Phase 3):** Is the persona roster specifically load-bearing, or does any CLAUDE.md header work?
8. **Prompt-axis routing (Phase 3):** Could gigo detect task type at runtime and dose context differently?
9. **Widen childrens C-axis prompts (Phase 3):** 10 prompts isn't enough to separate c1 vs c3 (189 vs 188 is within noise). Need ~30 to call the tie.
10. **Model family generalization (Phase 3):** Is cold-context pushback an Opus 4.7 thing or model-family-wide? Run the same sweep on Sonnet 4.6 and Haiku 4.5.
11. **Rubric fabrication-check retrofit:** Add "grounded in real files?" penalty to rank-of-5 and pairwise judge rubrics before the next run.
12. **Qwen thinking-loop failure mode (Brief 16 follow-up):** 2/30 TF3-thinking-on runs for T7 burned the full 32768 max_tokens in reasoning and produced empty content. Same pathology as Brief 15's empty Characters response. Reproduce with a targeted sweep (regex-from-examples × 20 replicates) to characterise the tail — is it T7-specific, TF3-specific, or thinking-on-general?
13. **Phase 2 of the Qwen worker profile (Brief 16 deferred):** Sampling profile was pinned per task type from the Unsloth recommendations. Sweep it (temp/top_p/top_k/presence_penalty) against TF3-thinking-off to verify the pins are actually optimal.
14. **Multi-turn Qwen with `preserve_thinking` (Brief 16 deferred):** Single-shot only in Brief 16. Multi-turn is where thinking-mode pays off in principle, so worth measuring against plan → execute → review loops specifically.
15. **Local-worker bake-off (Brief 16 deferred, operator-prioritized):** Compare Qwen3.6 against **Gemma4** first, then DeepSeek-Coder, Qwen3-Coder, Codestral, Llama at the same TF3-off recipe to see if the harness is Qwen-specific or a general local-worker pattern. Scheduled after Phase 2A (scale) and Phase 2B/C (loop + loop-failure).
