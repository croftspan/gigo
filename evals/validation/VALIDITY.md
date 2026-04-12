# Validation Suite — Validity Constraints

What these tests prove, what they don't, and what would make them stronger.

## What's Valid

**Blind auditor.** The boundary-mismatch test excludes DEFECT-MANIFEST.md from the fixture copy. The auditing Claude invocation has the assembled context (CLAUDE.md, review-criteria.md, integration-patterns.md) but not the answer key. A separate judge invocation scores detection against the rubric. The auditor doesn't know it's being tested or what the "right answers" are.

**Separate judge.** Every LLM-scored test uses a separate Claude invocation for judging. No self-grading.

**Deterministic cleanup test.** Feature 4 (Agent Teams cleanup) is pure grep. No LLM variance, no interpretation. Binary pass/fail.

## What's Questionable

**The builder is the tester.** The same session that built the features built the fixture, the bugs, the rubric, and the review-criteria.md that steers Claude toward those bug types. The review criteria are realistic (what gigo:gigo Step 6.5 would generate for a TypeScript full-stack project), but the bugs were chosen to match them. Real-world bugs wouldn't be this clean.

**No bare-vs-assembled comparison for features.** These tests prove features *activate* (the content gets read and applied when present). They do NOT prove features add value *beyond what bare Claude would do without them*. The boundary test shows 6/6 detection WITH assembled context. Whether bare Claude catches 6/6 WITHOUT the review criteria is an open question. Layer 2 (version A/B) was dropped during design because the 5-criteria judge can't reliably distinguish two assembled versions — but that means we can't quantify the incremental value.

**Content activation, not skill integration.** The pattern catalog test (Feature 3) and phase selection matrix test (Feature 2) test whether Claude reads and applies a reference file dropped in `.claude/references/`. They don't test whether the actual skill pipeline (`gigo:spec`, `gigo:maintain`) routes to those files correctly during real use.

**Perfect scores may mean easy tests.** 6/6, 5/5, 3/3, 5/5 across the board. The thresholds (4/6, 3/5, 3/3, 5/5) were set as floors. Perfect scores on first run could mean the features are excellent or the tests aren't hard enough. The boundary-mismatch bugs are deliberately obvious cross-file mismatches — they're the kind of thing any careful review would catch. The real value of BM detection is on subtle, non-obvious mismatches in large codebases.

**LLM variance.** Results will vary across runs. A 6/6 today could be 4/6 tomorrow. The thresholds buffer this, but a single run isn't statistically significant. Multiple runs would give a detection rate distribution.

## What Would Make This Stronger

1. **Bare control run.** Run the boundary-mismatch test WITHOUT review-criteria.md and integration-patterns.md. If bare Claude also catches 6/6, the assembled context isn't adding value. If it drops to 3/6, the feature earned its tokens. This is the single highest-value improvement.

2. **Harder bugs.** The current 6 bugs are textbook BM examples. Add subtler defects: a type that's technically compatible but semantically wrong, a naming convention that's inconsistent but only in one of five fields, a state machine gap that only manifests in a 3-step transition chain.

3. **Multiple runs.** Run each test 5x and report mean/variance. A feature that scores 6/6 once but averages 3.5/6 across runs is less reliable than one that consistently hits 5/6.

4. **Independent fixture builder.** Have someone who didn't build the features create the seeded-defect fixture. Eliminates the builder-is-tester bias.

5. **Skill integration tests.** Test Features 2 and 3 by invoking the actual skills (`gigo:spec`, `gigo:maintain`) rather than dropping reference files into a directory.
