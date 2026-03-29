# Presence Overhaul Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-29-presence-overhaul-design.md`
**Design brief:** `~/.claude/plans/fluttering-percolating-beaver.md`

**Goal:** Rewrite GIGO's public-facing content to lead with the problem (CLAUDE.md rot), show the transformation (what you become), and eliminate repellent language.

**Architecture:** Content rewrite across 3 files + 1 CSS touch. The Voice persona in CLAUDE.md gets upgraded first to establish quality bars, then README and site content are rewritten to match.

---

### Task 1: Upgrade The Voice persona in CLAUDE.md

**blocks:** 2, 3
**blocked-by:** []
**parallelizable:** false

**Files:**
- Modify: `CLAUDE.md:49-55` (The Voice persona)
- Modify: `CLAUDE.md:3` ("proven" in project description)
- Modify: `CLAUDE.md:64` ("proven" in Conductor persona)

- [ ] **Step 1: Replace "proven" in CLAUDE.md line 3**

Change:
```
orchestrates the proven plan→execute→review pipeline
```
To:
```
orchestrates the validated plan→execute→review pipeline
```

- [ ] **Step 2: Replace "proven" in CLAUDE.md line 64**

Change:
```
The generated workflow produces the proven architecture without requiring the operator to understand why it works.
```
To:
```
The generated workflow produces the validated architecture without requiring the operator to understand why it works.
```

- [ ] **Step 3: Expand The Voice persona (lines 49-55)**

Replace the entire Voice section with:

```markdown
### The Voice — README & Developer Relations Architect

**Modeled after:** Kathy Sierra's "make the user awesome" — README makes the reader feel what having it is like
+ Stephanie Morillo's developer content strategy — structure for scanners first, readers second
+ Simon Sinek's "Start with Why" — lead with the problem people feel, not the solution you built
+ April Dunford's positioning discipline — frame around what the customer becomes, not what the product does
+ Joanna Wiebe's conversion copy rigor — every sentence survives the "so what?" test, voice-of-customer language not insider jargon
+ Harry Dry's transformation-first clarity — make it about them not you, no feature lists before the reader knows why they should care.

- **Owns:** README architecture, progressive disclosure, the 5-second test, scan-path design, emotional resonance before technical depth, transformation-first copy, the "so what?" test, positioning discipline, voice-of-customer language
- **Quality bar:** A stranger knows what problem this solves, what they become, and how to try it within 30 seconds. Every sentence survives "so what?" If you removed all feature language, the reader still wants it.
- **Won't do:** Leading with features over problems, walls of code before the reader cares, origin stories above the fold, feature lists before the reader knows the problem, insider jargon the customer wouldn't use, leading with credentials before the transformation
```

- [ ] **Step 4: Verify no other "proven" instances in CLAUDE.md**

Search CLAUDE.md for "proven" (case-insensitive). If any remain, replace with "validated."

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: expand The Voice with Dunford/Wiebe/Dry + replace proven with validated"
```

---

### Task 2: Rewrite README.md

**blocks:** 4
**blocked-by:** 1
**parallelizable:** true (with Task 3)

**Files:**
- Modify: `README.md` (full rewrite)

- [ ] **Step 1: Write the new README**

Full rewrite following spec R2 structure. The complete content:

```markdown
# 義剛 GIGO

Every Claude Code project starts the same way. You add rules, things work great. Next session you add more. A week later your CLAUDE.md is 200 lines of overlapping, stale guidance. Your AI output gets worse, not better.

[Research confirms it](https://arxiv.org/abs/2602.11988): bloated context reduces task success rates while increasing cost.

GIGO fixes this. Describe what you're building. GIGO researches the best practitioners in that field, real people with real philosophies, and assembles an expert team that plans, executes, and reviews your work. Your project gets sharper over time, not bigger.

---

## What You Get

Projects that improve with every session instead of rotting. Specs good enough that workers nail it on the first pass. Reviews that find almost nothing because the upstream process already caught it.

---

## Quick Start

\```bash
claude install @croftspan/gigo
\```

Open any project in Claude Code. Type `gigo`.

---

## How It Works

1. **Your expert team plans the work.** GIGO builds a team from real practitioners in your domain. They ask the hard questions, catch architectural gaps, and surface the edge cases you'd find at 2am.

2. **Their knowledge becomes a spec.** Not vague rules. Concrete requirements with specific conventions baked in. Error formats, naming schemes, output patterns. Everything a worker needs to get it right the first time.

3. **Workers execute from the spec.** They get the requirements, not the rules. First-pass quality validated across two completely different domains. Every run.

4. **Two reviewers catch what one misses.** Spec compliance and engineering quality as separate passes. Different lenses find different problems.

---

## The Seven Skills

| Skill | What it does |
|---|---|
| `gigo` | Builds your expert team from scratch |
| `gigo:maintain` | Adds expertise, audits for bloat, upgrades setups |
| `gigo:blueprint` | Turns ideas into specs and implementation plans |
| `gigo:execute` | Runs plans with agent teams. Workers get the spec, not the rules |
| `gigo:verify` | Two-stage review: spec compliance + engineering quality |
| `gigo:snap` | Session-end audit. Projects get sharper, not bigger |
| `gigo:eval` | Tests whether the expert knowledge actually improves output |

**Note:** The `gigo:eval` description changed from "Proves the assembled context actually improves output" to eliminate banned jargon ("assembled context", "Proves"). The spec says "keep table unchanged" but R4 says eliminate banned terms. R4 wins: banned terms in user-facing copy defeat the purpose of the overhaul. Task 3 Step 8 must also update the site skills table to match.

---

## Your Project Stays Lean

This is the problem GIGO was built to solve.

You set up a project. Add some rules. Things work great. Next session you add more. Fix a gotcha. Add a convention. A week later your CLAUDE.md is 200 lines. Some rules contradict each other. Some are stale. Some just repeat what Claude already knows.

Your AI output starts getting worse. More rules should help, right? But [research shows the opposite](https://arxiv.org/abs/2602.11988): bloated context files reduce success rates by 20%+ while increasing cost.

GIGO keeps your project lean. Rules that apply to every conversation stay short (under 60 lines each). Deep knowledge loads only when relevant. Zero cost when unused. At the end of every session, The Snap audits your project: removes what's stale, merges what overlaps, enforces line budgets.

Your project gets sharper over time, not bigger.

---

## See It In Action

**Clear technical brief:**

\```
You: "Building a real-time multiplayer game server. Rust.
      WebSocket connections, matchmaking, state sync."

GIGO: "Three on this one:

        The Network Architect
        Carl Lerche's Tokio-driven async pragmatism. The runtime
        is the foundation, get it right or nothing else matters.
        + Glenn Fiedler's game networking gospel. Client-side
        prediction, server authority, snapshot interpolation.
        + Sanjay Ghemawat's systems-level efficiency thinking.
        When you're processing thousands of connections per tick,
        allocation patterns are gameplay decisions.

        The Game State Engineer
        Gabriel Gambetta's client-server game architecture.
        The canonical breakdown of interpolation, prediction,
        and reconciliation. + Jon Blow's data-oriented design
        philosophy. ECS isn't a religion, but your state layout
        determines your tick budget. + Martin Kleppmann's
        distributed systems rigor. State sync is a distributed
        systems problem wearing a game costume.

        The Matchmaker
        Josh Menke's matchmaking philosophy (Halo, Call of Duty).
        Skill rating is easy, match quality is hard. + Raph
        Koster's theory of fun as a design constraint.
        Matchmaking that doesn't produce fun games is technically
        correct and functionally useless.

       Three distinct lenses. Each one disagrees with the others
       on where to spend complexity budget, which is exactly the
       tension you want. Lock it in, or adjustments?"
\```

**Vibes-only creative brief:**

\```
You: "I want to make a tabletop RPG. Something dark and weird,
      like if Miyazaki directed D&D."

GIGO: "Custom system, no safety net of an existing engine. That's
       more work but more control. Here's who I'd bring in:

        The Mythwright
        Fumito Ueda's design-through-absence. What you don't
        explain is more haunting than what you do. + Miyazaki's
        moral complexity. No pure villains, just beings with
        alien logic. + Kentaro Miura's capacity to make beauty
        feel precarious. Owns your setting, your tone, and the
        question 'does this feel wrong in the right way?'

        The Mechanist
        Vincent Baker's 'fiction first' engine philosophy.
        Apocalypse World proved mechanics should emerge from
        the narrative. + Luke Crane's conviction that the system
        should hurt. Advancement costs something. + Ben Milton's
        Knave-style minimalism. If a rule doesn't create a
        meaningful decision, cut it.

        The Dread Cartographer
        Grant Howitt's one-page game clarity. Honey Heist proved
        you can teach a game in minutes without losing depth.
        + Emmy Allen's Stygian Library approach to procedural
        wonder. Tables that generate mood, not just content.

       Want me to tell you more about any of them, swap someone
       out, or does this feel like the right team?"
\```

Same skill, different calibration. Software, fiction, game design, research, music, business.

---

## The Name

義剛 (Gigo), pronounced *ghee-goh* (義 *gi*, righteousness + 剛 *gō*, strong).

In computer science, GIGO means "Garbage In, Garbage Out."

---

Built at [Croftspan](https://croftspan.com). Apache 2.0.

[croftspan.github.io/gigo](https://croftspan.github.io/gigo/) · [Research](site/research/) · [Get Started](site/docs/getting-started.html) · [Skills](site/docs/skills.html)
```

- [ ] **Step 2: Language rules verification**

Scan the new README for:
- "proven" (case-insensitive). Must be zero.
- Em dashes (—). Must be zero.
- "assembled context", "context engineering", "two-tier architecture", "derivability testing", "token economics", "research-backed". Must be zero.

- [ ] **Step 3: The "so what?" test**

Read each section. For every sentence, ask "so what?" If the answer isn't clear, rewrite.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "feat: rewrite README, problem-first, transformation-focused"
```

---

### Task 3: Rewrite site/index.html

**blocks:** 4
**blocked-by:** 1
**parallelizable:** true (with Task 2)

**Files:**
- Modify: `site/index.html` (content rewrite)
- Modify: `site/css/style.css:774-777` (add animation-delay rules)

- [ ] **Step 1: Update meta tags**

Replace the page title, meta description, OG tags, and Twitter tags:

```html
<title>義剛 GIGO. Your AI setup is holding you back. Fix it.</title>
<meta name="description" content="CLAUDE.md files grow out of control. More rules make AI output worse. GIGO builds an expert team that keeps your project sharp.">

<!-- Open Graph -->
<meta property="og:title" content="義剛 GIGO. Your AI setup is holding you back. Fix it.">
<meta property="og:description" content="CLAUDE.md files grow out of control. More rules make AI output worse. GIGO builds an expert team that keeps your project sharp.">

<!-- Twitter Card -->
<meta name="twitter:title" content="義剛 GIGO. Your AI setup is holding you back. Fix it.">
<meta name="twitter:description" content="CLAUDE.md files grow out of control. More rules make AI output worse. GIGO builds an expert team that keeps your project sharp.">
```

Keep the existing og:image, og:url, og:type, twitter:card, and twitter:image tags unchanged.

- [ ] **Step 2: Rewrite hero section**

Replace the hero content (keep the `<section class="hero">` wrapper):

```html
<section class="hero">
  <div class="container">
    <h1><span class="brand-kanji">義剛</span> GIGO</h1>
    <p class="subtitle">Your AI setup is making your output worse. GIGO fixes it.</p>
    <p class="hero-desc">Every Claude Code project rots. Rules pile up, context bloats, and output quality drops. GIGO assembles an expert team that keeps your project sharp and your output consistent.</p>
    <div class="cta-group">
      <a href="docs/getting-started.html" class="btn btn-primary">Get Started</a>
      <a href="https://github.com/croftspan/gigo" target="_blank" rel="noopener" class="btn btn-secondary">View on GitHub</a>
    </div>
    <div class="install-cmd"><code>claude install @croftspan/gigo</code></div>
  </div>
</section>
```

- [ ] **Step 3: Add "The problem" section (NEW)**

Insert after the hero, before "How It Works":

```html
<!-- The Problem -->
<section class="section">
  <div class="container">
    <h2>The problem everyone hits</h2>
    <p>You set up a project. Add some rules. Things work great. Next session you add more. Fix a gotcha. Add a convention.</p>
    <p>A week later your CLAUDE.md is 200 lines. Some rules contradict each other. Some are stale. Some just repeat what Claude already knows.</p>
    <p>Your AI output starts getting worse. More rules should help, right? <a href="https://arxiv.org/abs/2602.11988" target="_blank" rel="noopener">Research shows the opposite</a>: bloated context files reduce success rates by 20%+ while increasing cost.</p>
  </div>
</section>
```

- [ ] **Step 4: Add "The transformation" section (NEW)**

Insert after "The problem", before "How It Works":

```html
<!-- The Transformation -->
<section class="section">
  <div class="container">
    <h2>What changes</h2>
    <p><strong>Without GIGO:</strong></p>
    <ul>
      <li>CLAUDE.md is 300 lines of overlapping, stale rules</li>
      <li>AI output is inconsistent. Sometimes great, sometimes garbage</li>
      <li>Every project setup is from scratch, trial and error</li>
      <li>Reviews catch things the AI should have gotten right</li>
    </ul>
    <p><strong>With GIGO:</strong></p>
    <ul>
      <li>Projects get sharper over time, not bloated</li>
      <li>Specs are good enough that workers nail it on the first pass</li>
      <li>Reviews find almost nothing because the upstream process caught it</li>
      <li>Works for any domain. Software, fiction, game design, research, music</li>
    </ul>
  </div>
</section>
```

- [ ] **Step 5: Rewrite "How It Works" step descriptions**

Keep the 4-step structure. Replace the step descriptions:

```html
<div class="how-it-works-step">
  <span class="step-number">1</span>
  <div class="step-label">Plan</div>
  <div class="step-desc">Your expert team asks the hard questions and catches what you&rsquo;d miss</div>
</div>
<div class="how-it-works-step">
  <span class="step-number">2</span>
  <div class="step-label">Spec</div>
  <div class="step-desc">Their knowledge becomes concrete requirements. Not vague rules. Specific decisions a worker can follow</div>
</div>
<div class="how-it-works-step">
  <span class="step-number">3</span>
  <div class="step-label">Execute</div>
  <div class="step-desc">Workers get the spec, not the rules. First-pass quality that sticks</div>
</div>
<div class="how-it-works-step">
  <span class="step-number">4</span>
  <div class="step-label">Review</div>
  <div class="step-desc">Two focused passes catch what one pass trying to do everything misses</div>
</div>
```

- [ ] **Step 6: Rewrite results section**

Replace the entire results section content:

```html
<!-- Results -->
<section class="section">
  <div class="container">
    <h2>Validated across two domains</h2>
    <p>Nine phases of controlled experiments. Blinded judging. Principal engineer reviews. Two completely different domains to make sure it wasn&rsquo;t a fluke.</p>

    <div class="results-highlight" style="grid-template-columns: repeat(3, 1fr);">
      <div class="results-stat">
        <span class="stat-number">97%</span>
        <span class="stat-label">of requirements met on the first pass. Zero fixes needed</span>
      </div>
      <div class="results-stat">
        <span class="stat-number">Senior+</span>
        <span class="stat-label">rated by principal engineers. Every run, not a best-of</span>
      </div>
      <div class="results-stat">
        <span class="stat-number">9 phases</span>
        <span class="stat-label">of controlled experiments across software and game design</span>
      </div>
    </div>

    <p>Built on research from <a href="https://arxiv.org/abs/2602.11988" target="_blank" rel="noopener">Gloaguen et al.</a> and <a href="https://arxiv.org/abs/2603.18507" target="_blank" rel="noopener">Hu et al.</a>, then validated with our own experiments. <a href="research/">Read the full research &rarr;</a></p>
  </div>
</section>
```

- [ ] **Step 7: Rewrite "Your Project Stays Lean" section**

Replace content:

```html
<!-- Stays Lean -->
<section class="section">
  <div class="container">
    <h2>Your project stays lean</h2>
    <p>This is the problem GIGO was built to solve. Most AI setups grow out of control. Every session adds rules, nothing gets removed. Within weeks your context files are hundreds of lines of overlapping, outdated guidance that makes output worse, not better.</p>
    <p>GIGO keeps it lean. Rules that apply to every conversation stay short (under 60 lines each). Deep knowledge loads only when relevant. Zero cost when unused.</p>
    <p>At the end of every session, The Snap audits your project: removes what&rsquo;s stale, merges what overlaps, enforces line budgets. Your project gets sharper over time, not bigger. <a href="docs/architecture.html">See how it works &rarr;</a></p>
  </div>
</section>
```

- [ ] **Step 8: Update skills table for language rules, keep name section unchanged**

Update the `gigo:eval` row in the site skills table to match the README:

Change:
```html
<tr><td><code>gigo:eval</code></td><td>Proves the context actually improves output</td></tr>
```
To:
```html
<tr><td><code>gigo:eval</code></td><td>Tests whether the expert knowledge actually improves output</td></tr>
```

Verify the "Why GIGO?" section is untouched.

- [ ] **Step 9: Add animation-delay rules to style.css**

Add after line 777 of `site/css/style.css`:

```css
  .section:nth-child(6) { animation-delay: 0.3s; }
  .section:nth-child(7) { animation-delay: 0.35s; }
```

- [ ] **Step 10: Language rules verification**

Scan site/index.html for:
- "proven" or "Proven" (case-insensitive). Must be zero.
- `&mdash;` or the literal — character. Must be zero.
- "assembled context", "context engineering", "two-tier", "derivability testing", "token economics", "research-backed". Must be zero.

- [ ] **Step 11: Commit**

```bash
git add site/index.html site/css/style.css
git commit -m "feat: rewrite site homepage, problem-first, transformation-focused"
```

---

### Task 4: Global Cleanup and Final Verification

**blocks:** []
**blocked-by:** 2, 3
**parallelizable:** false

**Files:**
- Verify: `CLAUDE.md`, `README.md`, `site/index.html`

- [ ] **Step 1: Global "proven" scan**

Search all three files for "proven" (case-insensitive). Must be zero hits.

- [ ] **Step 2: Global em dash scan**

Search README.md and site/index.html for em dashes (— or `&mdash;`). Must be zero. CLAUDE.md is exempt (persona convention).

- [ ] **Step 3: Global jargon scan**

Search README.md and site/index.html for: "assembled context", "context engineering", "two-tier architecture", "derivability testing", "token economics", "research-backed". Must be zero in user-facing copy.

- [ ] **Step 4: The 30-second test**

Read the README from the top. Can a stranger answer within 30 seconds:
1. What problem does this solve?
2. What do I become after using it?
3. How do I try it?

Read the site from the hero. Same three questions.

If any answer is unclear, fix the copy.

- [ ] **Step 5: Commit any fixes**

```bash
git add CLAUDE.md README.md site/index.html site/css/style.css
git commit -m "fix: final cleanup, language rules and 30-second test"
```

Only commit if there were fixes. If clean, skip.

---

**Risks:**
- Hero subtitle copy is creative work. "Your AI setup is making your output worse" is strong but negative. "CLAUDE.md rot is real. GIGO fixes it." assumes knowledge. The implementation should try variations and pick the one that passes the 30-second test without assuming the reader knows GIGO terminology. The spec leaves this to execution, which is correct.
- The transformation section before/after lists need to feel like real user pain, not marketing bullets. Use voice-of-customer language (what people actually say in Discord/Twitter about their AI setups), not polished copy.

**Done when:** All three files pass the language rules scan (zero "proven", zero em dashes in README/site, zero jargon). The 30-second test passes for both README and site. The Voice persona has all six authorities.
