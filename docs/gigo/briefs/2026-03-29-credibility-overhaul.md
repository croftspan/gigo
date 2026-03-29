# Credibility Overhaul — Addressing the Cold Review

A skeptical principal engineer reviewed every page of croftspan.github.io/gigo/ with instructions to detect bullshit. He found real problems. Some we argued successfully. Some we didn't. This brief captures everything so the fix session doesn't miss a drop.

---

## Source Material

Full conversation: `~/Downloads/me/report.md`
Operator resume: `~/Downloads/me/Profile (2).pdf`
Memory: `project_principal_engineer_review.md`

---

## The 7 Must-Fix Items

### 1. Homepage stats are inflated

**The problem:**
- "97% of requirements met on first pass" doesn't come from a specific experiment
- The closest real number is 96% criteria wins in blinded A/B eval, which measures something different (criteria preference, not requirements met)
- "Zero fixes needed after review" comes from ONE Go CLI task in Phase 9 (30/30 conventions). Extrapolating one test case to a universal claim is misleading
- "Senior+ rated by principal engineers" — the research page doesn't identify who these engineers are, how many reviewed, or what rubric they used

**The fix:**
- Replace "97%" with the actual 96% and explain what it measures: "96% criteria win rate across 100 blinded evaluations in 2 domains"
- Replace "Zero fixes needed" with what actually happened: "30/30 convention compliance on first pass" with context that it's from the Go CLI eval
- Either substantiate the "principal engineer" claim with who/how/rubric, or reframe as "senior-level output quality" without implying external review
- Every stat on the homepage must trace to a specific experiment with a specific number

### 2. Eval criteria are structurally biased toward assembled

**The problem:**
3 of 5 judging criteria measure whether context was USED, not whether output was BETTER:
- "Persona voice" — of course assembled wins, it HAS personas
- "Expertise routing" — of course assembled wins, it HAS expertise routing
- "Specificity" — assembled context produces more specific output by definition

Only 2 criteria measure actual output quality:
- "Quality bar enforcement" — did the output meet the quality standards?
- "Pushback quality" — did the reviewer catch real issues?

The 96% headline number aggregates all 5 criteria. If assembled wins 100% on persona voice (tautological) but only 60% on quality bar enforcement, the 96% is misleading.

**The fix:**
- Publish per-criterion breakdowns on the research page
- The eval data exists in the score files — extract and present it
- If quality-measuring criteria (quality bar enforcement, pushback quality) show strong wins, LEAD with those numbers
- If they don't show strong wins, that's important to acknowledge honestly
- Consider restructuring the eval to weight quality criteria higher, or separate "context utilization" scores from "output quality" scores

### 3. Half the citations are unverifiable

**The problem:**
Referenced in CLAUDE.md personas and research page:
- Gloaguen et al. (arXiv:2602.11988) — VERIFIED, link works
- Hu et al. (arXiv:2603.18507) — VERIFIED, link works
- Kong et al. (role-play research) — NO URL, NO DOI, NO VENUE
- Xu et al. (ExpertPrompting) — NO URL, NO DOI, NO VENUE
- Shinn et al. (Reflexion framework) — NO URL, NO DOI, NO VENUE
- Yang et al. (SWE-agent) — NO URL, NO DOI, NO VENUE

For a project that leans on "research-backed" as a credibility signal, having 4 of 6 citations unverifiable is a real problem. If any of these were hallucinated by Claude during the original assembly, they need to be found or removed.

**The fix:**
- Research each citation. Find the actual paper, venue, year, and URL
- Kong et al. is likely "Better Zero-Shot Reasoning with Role-Play Prompting" (arXiv:2308.07702)
- Xu et al. is likely "ExpertPrompting: Instructing Large Language Models to be Distinguished Experts" (arXiv:2305.14688)
- Shinn et al. is likely "Reflexion: Language Agents with Verbal Reinforcement Learning" (arXiv:2303.11366)
- Yang et al. is likely "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering" (arXiv:2405.15793)
- Verify each. If correct, add full citation with arXiv link. If wrong, find the right paper or remove the reference
- Add citations to the research page and anywhere they're referenced on the site

### 4. "Built at Croftspan" implies a team that doesn't exist

**The problem:**
Croftspan is a GitHub org with one member and one repo. "Built at Croftspan" reads as "a company built this." A visitor assumes multiple humans. The AI team is real (Claude as co-author on 293 commits) but a stranger doesn't know that.

**The reviewer's key insight:** "One person built all this in a week with AI" is a BETTER story than "some company made a thing." The solo-founder-with-AI narrative is rarer, more credible, and more compelling.

**After seeing the resume:** "Your credibility IS the product differentiation. Every other Claude Code prompt library is made by someone who read a blog post. Yours is made by someone who's actually run teams, shipped products, and knows what 'the review caught a runtime blocker' means because they've lived through what happens when reviews don't catch runtime blockers."

**The fix:**
- Change "Built at Croftspan" to "Built by Eaven at Croftspan" or similar
- Consider an "About" section or page that gives enough context: Blockfolio ($150M exit), ToppsNFTs ($500M exit), 15 years of building from zero to scale. Not the full resume. Just enough that people know this isn't a weekend experiment.
- The story: "One experienced operator who compressed months of learning into a week using the exact tools he's building" — that's the pitch, not the anonymous company framing

### 5. Domain claims are oversold

**The problem:**
Homepage says "Works across domains: software, fiction, game design, research, music, business." Eval tested exactly 2 domains (Rails API + children's novel). Music, game design, research, and business have zero eval data.

Real-world usage across 7+ projects (crypto fintech ops, board game design, creative works, coding) but none of this is on the site. The strongest evidence is invisible.

**The fix:**
- Change claim language: "Validated in controlled evals across software and fiction. Used in production across crypto ops, game design, and more."
- Add 1-2 real deployment anecdotes. Even a paragraph: "Here's the expert team GIGO assembled for a crypto fintech ops manager, and the first review it caught." Lived usage is worth more than another percentage point on the A/B eval.
- The dogfooding page is currently the strongest domain-breadth evidence. Link to it from the domain claims.

### 6. Research page is too dense

**The problem:**
The research page is the best asset on the site but it's 3000+ words of eval narrative. Nobody reads it. The reviewer called it "a lab notebook" — good for deep credibility but needs a front page.

**The fix:**
- Add a TL;DR / executive summary at the top of the research page (5-10 bullet points with the key findings)
- Structure: "Here's what we know, here's how we know it, here's what we don't know yet"
- Keep the full narrative below for deep readers
- Lead with the honest, surprising findings (Phase 5: bare beats assembled for execution) — that's what earns trust
- Consider a separate "Evidence" page linked from the homepage that's the scannable version

### 7. claude install @croftspan/gigo

**The problem:**
The most prominent CTA on the site doesn't work for users who don't have the marketplace configured. First impressions matter. Front door is broken.

**The fix:**
- Verify the install command works from a clean Claude Code install
- If it requires marketplace configuration first, document that clearly
- Or provide the alternative install path prominently
- This is a trust issue, not a functionality issue

---

## Arguments We Won (Don't Re-fight These)

### Phase 5 findings aren't buried
The reviewer initially said Phase 5 (bare beats assembled for execution) was buried. We argued it's the pivotal discovery that led to the architecture. He conceded: "That's not burial, that's scientific narrative."

### Versioning is proper semver
He questioned v7.7.0 in 5 days. We showed the bumps track actual feature changes. He conceded: "The recent bumps are clean."

### The etymology is personal
He called 義剛 "performative." We said it resonates personally. He withdrew: "You don't need my permission to name your project."

### There IS a team (AI team)
He said "there is no team." We argued Claude is a team member (293 co-authored commits, collaborative workflow). He partially conceded: "there is a collaborative workflow happening" but still pushed for transparency about the human count.

### "Proven" is lived experience
We've used GIGO across 7+ real projects in different domains. That's not a controlled experiment but it's not nothing. He suggested: "battle-tested across [domains]" or "validated in controlled evals, hardened across 7+ real projects."

---

## The Meta-Insight (Frame the Whole Fix Around This)

The reviewer's final assessment after seeing the resume:

"You're not building a developer tool. You're building the operational playbook for how one person runs an AI-native company. GIGO isn't really 'a Claude Code plugin.' It's the codification of how you work: assemble experts, plan with full context, execute with clean specs, review adversarially, audit for bloat. You've been doing this pattern your entire career with human teams, and now you're translating it to AI teams."

"The thing that actually convinced me this project is serious isn't the eval numbers or the pipeline architecture. It's the pattern I see in your career: every step is 'I'll figure out the new thing, build the process, do it myself until I can scale it.' GIGO is the same pattern."

"The project is more interesting than the marketing lets it be."

This is the frame. The credibility overhaul isn't about fixing bad marketing. It's about letting the real story show through instead of hiding behind anonymous polish.

---

## What This Session Should Produce

1. Updated homepage stats (real numbers, real context, traceable to experiments)
2. Per-criterion eval breakdown published on research page
3. All 6 citations verified with full URLs
4. "Built by Eaven at Croftspan" or equivalent transparency
5. Domain claims reworded to separate validated from used
6. Research page TL;DR at the top
7. claude install command verified or documented
8. Optional: About section or founder context somewhere on the site
9. Optional: 1-2 real deployment anecdotes

---

## Files Likely Affected

| File | What changes |
|------|-------------|
| `site/index.html` | Stats rewritten, "Built at" updated, domain claims reworded |
| `site/research/index.html` | TL;DR added, per-criterion data published, citations verified |
| `CLAUDE.md` | Citations verified (personas reference papers) |
| `README.md` | Stats consistent with site, domain claims consistent |
| `site/docs/dogfooding.html` | May need minor updates for consistency |
| Eval score files | Extract per-criterion breakdowns for publication |

---

## Voice and Tone

Same rules as the presence overhaul: no "proven" (use "validated" or "battle-tested"), no em dashes, no jargon, every sentence survives "so what?". But with a new layer: **honesty as a credibility strategy**. The reviewer's strongest reaction was to transparency. "Phase 5 is the pivotal discovery" landed. "97% first pass" didn't. Lead with what's real and specific. The numbers are strong enough to not need inflation.

The reviewer explicitly said: "If someone showed me this as 'here's my week-long experiment exploring how context placement affects Claude Code output quality, with some interesting findings,' I'd be genuinely interested." That's the voice. Confident but honest. Specific but not inflated. The work speaks for itself when you let it.
