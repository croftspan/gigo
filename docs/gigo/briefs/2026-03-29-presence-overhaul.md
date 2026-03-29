# Presence Overhaul — README + Site Rewrite

## The Problem

Carlos (principal engineer, honest friend) gave us the brutal feedback: "I only kept reading because I know you." When we say "proven," people hear "pretentious." The site reads like a research paper defending itself instead of a tool showing you what you become.

### What's Wrong Now

1. **We're selling the mushroom, not the transformation.** The README and site talk about what GIGO is (skills, personas, two-tier architecture, eval phases) instead of what the user becomes (someone who ships better work with AI, whose projects don't rot, whose specs actually work on the first pass).

2. **"Proven" is a repellent.** Carlos: "usually when someone says something is proven it works basically like a repellent to me." Replace with "validated" or just show the results and let people draw their own conclusion.

3. **Jargon walls.** "Assembled context," "two-tier architecture," "context engineering," "derivability testing." These mean nothing to someone who just wants their Claude Code setup to produce better work. The Rancho principle: say what it does, not how it works.

4. **The origin story is buried.** GIGO started because CLAUDE.md files grow out of control. Every session adds rules, nothing gets removed, and within weeks your AI output gets worse, not better. That's the problem people FEEL. That's our "Little Mario." We mention it in one section but it's not the lead.

5. **Too much to read.** Homepage has 8 sections of equal weight. Research page is 400+ lines. Carlos stopped reading. A stranger won't even start.

6. **Data presented as grades, not achievements.** "14 to 20 out of 30" sounds like a C+. What it actually means: expert team catches what bare AI misses. First-pass quality so high the reviewers found nothing to fix.

## The Strategy

### The Transformation (what people become)

**Little Mario (before GIGO):**
- CLAUDE.md is 300 lines of overlapping, stale rules
- AI output is inconsistent. Sometimes great, sometimes garbage
- No idea if their context is helping or hurting
- Every project setup is from scratch, trial and error
- Reviews catch things the AI should have gotten right the first time

**The Flower (GIGO):**
- Seven skills that handle the full lifecycle
- Expert team researched from real practitioners
- Automatic cleanup that keeps the project lean
- Validated pipeline: plan, execute, review

**Big Mario (after GIGO):**
- AI output is consistent and high quality from the first pass
- Projects get sharper over time, not bloated
- Specs are good enough that workers nail it without hand-holding
- Reviews find almost nothing because the upstream process caught it
- Setup that works for any domain, not just code

### What to Lead With

The problem people feel: **"Your AI setup is making your output worse."**

Not "we have a research-backed context engineering framework." Not "7 skills for building expert teams." The problem. Then the transformation. Then how.

### Language Rules

| Don't say | Say instead |
|-----------|------------|
| proven | validated / tested / measured |
| assembled context | expert knowledge |
| context engineering | making AI output better |
| two-tier architecture | keeps your project lean |
| derivability testing | removes rules the AI doesn't need |
| personas | expert team members |
| token economics | (don't mention it) |
| research-backed | (just show the results) |
| em dashes | periods |

### The CLAUDE.md Story (expand this)

This is the core problem GIGO solves. Every Claude Code user feels it:

1. You set up a project. Add some rules. Things work great.
2. Next session you add more rules. Fix a gotcha. Add a convention.
3. A week later your CLAUDE.md is 200 lines. Some rules contradict each other. Some are stale. Some just repeat what Claude already knows.
4. Your AI output starts getting WORSE. More rules should help, right? But research shows the opposite: bloated context reduces success rates by 20%+.
5. GIGO fixes this. The Snap audits every session. Two-tier means deep knowledge loads only when needed. Your project gets sharper over time.

This is the "keeping your CLAUDE.md and .claude/ clean" story. It's how the project started. It should be front and center.

### Structure: README

1. **The problem** (2-3 sentences max). Your AI setup grows out of control. More rules make output worse.
2. **What you become** (2-3 sentences). Projects that get sharper over time. Specs that work on the first pass. Reviews that find nothing to fix.
3. **Quick start** (install command + one line)
4. **How it works** (4 bullets, transformation-focused, not feature-focused)
5. **See it in action** (the two examples, trimmed)
6. **The seven skills** (table, kept)
7. **Your project stays lean** (expanded, this is the CLAUDE.md story)

### Structure: Site Homepage

1. **Hero:** The problem + transformation in two lines. Not "Research the experts. Build the team." Instead: what you become.
2. **The problem:** 3-4 sentences about CLAUDE.md rot. Everyone who uses Claude Code knows this feeling.
3. **The transformation:** Before/after. Not features. What changes for you.
4. **Quick start:** Install + one command.
5. **How it works:** 4 steps, each one transformation-focused.
6. **Social proof:** Results presented as achievements, not grades. "First-pass quality so high reviewers found nothing to fix" not "97% convention compliance."

### What to Keep

- The two example briefs (game server + tabletop RPG). These are powerful. They show the transformation.
- The seven skills table. Clean, scannable.
- The name explanation. Short, meaningful.
- The research link (for people who want depth). But don't lead with it.

### What to Cut or Restructure

- "9 phases, hundreds of eval runs, 70M+ tokens" block. This is flexing, not helping. Move to the research page.
- Research-first framing everywhere. The research validates the approach. It's not the pitch.
- Separate "How It Works" from "The Research." Right now they're mixed.

### Carlos's Specific Feedback to Address

1. "the whole 'proven' stance is weird" → replace with validated, or just show results
2. "stating it's proven is pedantic and do no good for the solution" → lead with what it does, not that it's been studied
3. "I only kept reading because I know you" → the 5-second test must pass for strangers
4. "replace proven with validated" → global find-replace across all public-facing content

## Files to Modify

| File | What changes |
|------|-------------|
| `README.md` | Full rewrite following the structure above |
| `site/index.html` | Hero, problem, transformation sections rewritten |
| `site/docs/getting-started.html` | Review for jargon, simplify |
| `site/docs/skills.html` | Review for feature-first vs transformation-first language |
| `site/research/index.html` | Keep technical depth here, but frame it as "here's how we validated it" not "here's proof" |

## The Test

After rewrite, show the README to someone who doesn't know the project. Can they answer in 30 seconds:
1. What problem does this solve?
2. What do I become after using it?
3. How do I try it?

If any answer is unclear, the rewrite isn't done.
