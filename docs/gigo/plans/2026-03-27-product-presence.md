# GIGO Product Presence — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-27-product-presence-design.md`

**Goal:** Complete reimagining of GIGO's public presence — README, GitHub Pages product site, GitHub repository presentation.

**Architecture:** Static HTML/CSS/JS site deployed to GitHub Pages. README as the hook, site as the depth. "Two Kinds of Leadership" as flagship shareable content. Three brand pillars: 義剛 (identity), GIGO (problem), research-backed (method).

**Tech Stack:** Static HTML, CSS (dark-mode-first), vanilla JS (minimal), GitHub Pages

---

## Phase 1: Foundation (site infrastructure + brand assets)

### Task 1: Site Scaffold and Shared CSS

**Persona:** The Artisan (Freiberg's micro-interaction perfectionism + Coursey's reductive discipline + Saarinen's conviction-driven design)
**blocks:** 3, 4, 5, 6, 7, 8, 9, 10
**blocked-by:** []
**parallelizable:** false

**Files:**
- Create: `site/css/style.css`
- Create: `site/js/main.js`
- Create: `site/assets/favicon.svg`
- Create: `site/404.html`

- [ ] **Step 1: Create `site/css/style.css` — dark-mode-first shared stylesheet**

Design system covering:
- CSS custom properties for colors, spacing, typography (dark theme as default, light theme via `[data-theme="light"]`)
- Color palette: near-black background (`#0a0a0a`), off-white text (`#e5e5e5`), accent for links/CTAs (muted blue or warm white — not neon), secondary text (`#888`)
- Typography: system font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`) for body. Monospace stack for code blocks. 義剛 kanji rendered at display size in the same stack (CJK characters render natively)
- Responsive breakpoints: mobile-first. Single column under 768px, constrained max-width (720px) for readability on wide screens
- Component styles: nav (minimal — logo + links, sticky), footer (Croftspan + license + links), section containers, code blocks (subtle border, slightly lighter background), data tables (clean borders, alternating rows), badge row, CTA buttons (primary filled, secondary outlined)
- Utility classes: `.visually-hidden`, `.container`, `.section`, `.badge-row`
- No animations except: smooth color transitions on theme toggle, subtle hover states on interactive elements
- Print stylesheet: hide nav/footer, light background, dark text

- [ ] **Step 2: Create `site/js/main.js` — minimal shared JS**

Only two features:
```javascript
// Dark/light theme toggle — persists to localStorage
const toggle = document.getElementById('theme-toggle');
if (toggle) {
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
}

// Mobile nav toggle
const navToggle = document.getElementById('nav-toggle');
const navMenu = document.getElementById('nav-menu');
if (navToggle && navMenu) {
  navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('open');
  });
}
```

- [ ] **Step 3: Create `site/assets/favicon.svg`**

Simple SVG favicon — the kanji 義 rendered as a minimal mark. Monochrome, works at 16x16 and 32x32.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle"
        font-family="sans-serif" font-size="28" fill="#e5e5e5">義</text>
</svg>
```

- [ ] **Step 4: Create `site/404.html`**

Minimal 404 page using shared CSS. 義剛 GIGO heading, "Page not found" message, link back to home. Includes the shared nav and footer layout.

- [ ] **Step 5: Verify local preview**

Run: `cd site && python3 -m http.server 8000`
Expected: 404.html renders correctly with dark theme, nav works, theme toggle persists across refresh.

- [ ] **Step 6: Commit**

```bash
git add site/
git commit -m "feat(site): scaffold static site — shared CSS, JS, favicon, 404"
```

---

### Task 2: Social Preview Image

**Persona:** The Signal (Rocha's first-impression philosophy) + The Artisan (visual quality)
**blocks:** 11
**blocked-by:** []
**parallelizable:** true (with Task 1)

**Files:**
- Create: `site/assets/social-preview.png`

- [ ] **Step 1: Generate social preview image using artista**

Invoke `/artista` with this brief:
- Dimensions: 1280x640px (GitHub recommended for social preview)
- Content: 義剛 GIGO centered, tagline "Only give them what they need for the job." below
- Style: Dark background (#0a0a0a or similar), light text (#e5e5e5), clean typography
- The kanji 義剛 should be prominent — this is the brand mark
- No illustrations, no icons, no gradients — typography only
- Professional, minimal, serious — communicates research, not a side project

- [ ] **Step 2: Verify dimensions and rendering**

Check that the image renders correctly as GitHub social preview (1280x640), Twitter card, and Slack link preview. The text should be legible at thumbnail sizes.

- [ ] **Step 3: Commit**

```bash
git add site/assets/social-preview.png
git commit -m "feat(site): add social preview image — 義剛 GIGO brand"
```

---

## Phase 2: Core Content (parallelizable — each task is an independent page)

### Task 3: Landing Page

**Persona:** The Signal (README-as-marketing, first-impression philosophy) + The Artisan (site engineering)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 4, 5, 6, 7, 8, 9)

**Files:**
- Create: `site/index.html`

- [ ] **Step 1: Create `site/index.html`**

Full landing page following the spec's structure. Sections in order:

1. **Hero:** 義剛 GIGO heading, tagline, dual CTAs (Install command + View on GitHub button)
2. **Problem — 3 beats:** Most AI context engineering is vibes-based / We ran 9 phases of experiments / Built a system that applies the findings
3. **The Finding — pipeline visual:** Plan with experts → Embed in spec → Execute bare → Review with quality bars. Key numbers: 14→20→29, 30/30 conventions, senior/staff every time. Use a horizontal flow diagram built with CSS (flexbox boxes with arrows), not an image.
4. **Research Foundation:** "Built on 6 published papers + 9 phases of original experiments." List each paper with one-line contribution and arXiv link where available:
   - Gloaguen et al. (2026) — bloated context reduces success rates, costs 20%+ more ([arXiv:2602.11988](https://arxiv.org/abs/2602.11988))
   - Hu et al. (2026) — personas help alignment but hurt knowledge retrieval
   - Kong et al. — role-play activates domain knowledge when personas are specific
   - Xu et al. — task-specific persona descriptions outperform generic ones
   - Shinn et al. — reflection agents make dramatically better decisions
   - Yang et al. — interface design between agent and tools matters more than the prompt
5. **Quick Start:** Three steps — `claude install @croftspan/gigo`, open any project, say "gigo"
6. **Skills Overview:** Seven skills, one sentence each, link to /docs/skills
7. **The Name:** 義剛 = righteousness + strength. GIGO = garbage in, garbage out. Both are true.
8. **Footer:** Built at Croftspan | MIT License | nav links

HTML should include:
- `<meta>` tags for Open Graph (og:title, og:description, og:image pointing to social-preview.png)
- `<meta>` tags for Twitter Card (twitter:card, twitter:title, twitter:description, twitter:image)
- Canonical URL meta tag
- Shared nav (logo + links to /research, /docs/getting-started, /docs/skills, GitHub)
- Link to `css/style.css` and `js/main.js`

- [ ] **Step 2: Verify local preview**

Run: `cd site && python3 -m http.server 8000`
Expected: Landing page renders with dark theme, all sections visible, responsive at 375px and 1440px, CTAs are prominent, pipeline diagram reads clearly.

- [ ] **Step 3: Commit**

```bash
git add site/index.html
git commit -m "docs(site): add landing page — hero, problem, finding, research, quick start"
```

---

### Task 4: "Two Kinds of Leadership" — Research Narrative

**Persona:** The Narrator (Cox's annotation-first principle + Dykes's data storytelling triangle + Cairo's truthfulness-first hierarchy)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 5, 6, 7, 8, 9)

**Files:**
- Create: `site/research/index.html`

**Source material — MUST READ before writing:**
- `evals/EVAL-NARRATIVE.md` (primary source — all phases, methodology, analysis, quotes)
- `docs/design-philosophy.md` (origin story, Croftspan context)

- [ ] **Step 1: Create `site/research/index.html`**

This is the flagship content piece. Restructure the eval narrative from `evals/EVAL-NARRATIVE.md` for a public audience. Voice: third-person research narrative ("We tested..." "The data showed..."). Engaging but grounded — think data journalism, not academic paper.

Structure (following spec exactly):

**Title:** "Two Kinds of Leadership"
**Subtitle:** "What 9 experimental phases taught us about AI context engineering"

**The Question** — Does assembled context actually change AI behavior, or is it expensive token decoration? (2-3 paragraphs setting up the stakes. Reference the Gloaguen et al. finding that bloated context reduces success rates — the conventional wisdom says more context = better, but research suggests otherwise.)

**The Setup** — Two fixture domains (Rails API, children's mystery novel), 20 prompts, 100 evaluations per run, blinded A/B judging. Explain methodology accessibly — the reader should understand how rigorous this was without needing a stats background.

**Phase 1: The Baseline (87%)** — Assembled context won 87% of evaluations. But the 13% non-wins clustered into a pattern matching Hu et al.'s finding: personas help alignment tasks, hurt knowledge retrieval tasks. Include the domain breakdown table (Rails 88%, Novel 86%).

**The Calibration (87% → 96%)** — Two levers: persona calibration heuristic (6 lines telling the model when to lead with training vs persona) and task-specific "When to Go Deeper" pointers. Children's novel went from 86% to 100%. "Six lines of code. Nine percentage points." Include the results table.

**The Hallucination Problem** — Phase 2b: the assembled version hallucinated a classification exercise. The eval scored it without blinking. "The judge scores quality, not correctness. A beautifully written, persona-rich response that doesn't answer the question can still win." This led to the Overwatch adversarial system. (This section matters because it shows honest reporting of failures, not just successes.)

**The Proficiency Test** — Phase 4: when both versions do real work, which output is actually better? Rails rubric: assembled 18/20, bare 12/20. But the blind qualitative judge rated bare as "senior" and assembled as "mid-level reaching for senior." The resolution: "B's team, with A's instincts." Include the table and the judge quotes.

**The Instinct Experiments** — Phase 5: war stories beat bare on Rails for the first time (20/20 rubric, ranked 1st). "C writes code like someone who's been paged at 2am." But no format beat bare on creative work. The combo test: rules + war stories ranked LAST. "More context dilutes instincts."

**The Planning Pipeline** — Phase 6: same task, scripted answers, only variable is whether brainstormer had personas. Bare asks "What's the expected scale?" Assembled asks "What's the expected scale? *This determines whether we need to worry about table lock duration on migrations.*" Same topics, different depth. Include the 6 specific assembled wins.

**The Format Doesn't Matter** — Phase 7: 4 formats, 3 runs, principal engineer reviews. Bare rated senior/staff every time. "We thought the team's knowledge needs to reach the worker in the right format. Reality: the team's knowledge needs to reach the worker as a good spec."

**Two Kinds of Leadership (the synthesis)** — This is the payoff section. Build it from the "Two Kinds of Leadership" section in the eval narrative (lines ~539-596). The "do your job or I'll fire you" boss vs "what can I do to help you do your job better?" Use the three numbered points for each approach, with data citations. End with: "The team plans and reviews. The individual executes. That's not a compromise. That's the architecture."

**The Complete Architecture** — Clean table: Phase / Context / Why. (Brainstorming: Assembled ON / Personas shape questions. Spec writing: Assembled ON / Standards define quality bars. Plan writing: Assembled ON / Expertise becomes requirements. Execution: Bare / Workers produce best code with training + good spec. Review: Assembled ON / Team catches what workers miss.)

**The Research Foundation** — Full citations with context. For each paper: what it found, how it informed a specific GIGO design decision, and where our findings extend or challenge it:
- Gloaguen et al. (arXiv:2602.11988) — validated the lean-context approach
- Hu et al. — predicted the persona tradeoff we measured
- Kong et al. + Xu et al. — informed the blended-persona design
- Shinn et al. — inspired the Overwatch reflection system
- Yang et al. — shaped the skill architecture

**What This Means** — For anyone building with AI agents. The principle is general: context shapes questions (good), context shapes answers (bad). The architecture is transferable: plan with expertise, execute with trust, review with judgment.

The page should include:
- Open Graph and Twitter Card meta tags (this page is designed to be shared)
- Shared nav and footer
- Clean typography optimized for long-form reading (max-width ~680px for the content column)
- Data tables styled for readability
- Pull quotes for key findings (styled distinctly from body text)
- "Back to top" link at the bottom

- [ ] **Step 2: Verify reading experience**

Run: `cd site && python3 -m http.server 8000`
Expected: Article reads well on desktop (centered, constrained width) and mobile (full width with padding). Tables are scrollable on mobile. Pull quotes are visually distinct. Estimated reading time: 15-20 minutes.

- [ ] **Step 3: Commit**

```bash
git add site/research/index.html
git commit -m "docs(site): add 'Two Kinds of Leadership' research narrative"
```

---

### Task 5: Eval Data Reference Page

**Persona:** The Narrator (Cairo's truthfulness-first — present data honestly, let it speak)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4, 6, 7, 8, 9)

**Files:**
- Create: `site/research/eval-data.html`

**Source material — MUST READ:** `evals/EVAL-NARRATIVE.md`

- [ ] **Step 1: Create `site/research/eval-data.html`**

Reference page for people who want the raw numbers. Not a narrative — a structured data presentation with brief context per phase.

Sections:

**Methodology** — Brief overview: fixture domains, prompt design (3 axes), blinded judging, 5 criteria per evaluation, scoring system. Enough for someone to assess rigor.

**Phase-by-phase results** — Each phase gets:
- Phase name and date
- What changed (the variable being tested)
- Results table
- Key finding (one sentence)
- Link to result files in the repo (e.g., `evals/results/2026-03-26-131429/`)

Phases to include:
1. Baseline (87%)
2. Calibration — 2a (96%), 2b aberrant (91%), 2c confirmation (99%)
3. Hawkeye — structured (94%, 91%), domain-adapted (96%)
4. Proficiency test — rubric scores + qualitative judge verdicts
5. Instinct experiments — 5 format variants, Rails + Novel results
6. Planning pipeline — bare vs assembled questions + judge verdict
7. Format experiment — 4 variants, PR verdicts, engineer level assessments
8. Review pipeline — plan-aware vs code-quality vs combined, issue counts
9. Integration test — convention compliance 30/30, pipeline validation

**The Complete Picture** — Summary table from the eval narrative (all runs, all results, what changed per run).

Include shared nav, footer, meta tags. Link back to /research for the narrative version.

- [ ] **Step 2: Commit**

```bash
git add site/research/eval-data.html
git commit -m "docs(site): add eval data reference — phase-by-phase results"
```

---

### Task 6: Getting Started Doc

**Persona:** The Signal (Rocha's friction-removal + Swyx's authenticity)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4, 5, 7, 8, 9)

**Files:**
- Create: `site/docs/getting-started.html`

- [ ] **Step 1: Create `site/docs/getting-started.html`**

Install and first-run guide. Sections:

**Install** — Two paths:
```bash
# From the Claude Code marketplace
claude install @croftspan/gigo

# Or manually
git clone https://github.com/croftspan/gigo.git
cp -r gigo/skills/ ~/.claude/skills/
```

**First Run** — What happens when you say "gigo" in a project:
1. GIGO checks for existing CLAUDE.md and .claude/ directory
2. If nothing exists → conversational kickoff: describe what you're building
3. GIGO researches authorities, proposes blended personas
4. You react and refine ("drop that one," "add a testing expert")
5. Lock it in → GIGO writes CLAUDE.md, .claude/rules/, .claude/references/

**What Gets Created** — Brief explanation of the two-tier architecture:
- `CLAUDE.md` — team roster, autonomy model (auto-loaded every conversation)
- `.claude/rules/` — standards, workflow, domain extensions (~60 line cap each)
- `.claude/references/` — deep knowledge, loaded on demand (zero token cost when unused)

**Next Steps** — After assembly:
- `gigo:blueprint` — turn your first task into a spec and implementation plan
- `gigo:execute` — run the plan with agent teams or subagents
- `gigo:verify` — two-stage code review
- `gigo:snap` — run at session end to audit and protect

**Requirements** — Claude Code CLI installed. That's it.

Include shared nav, footer, meta tags.

- [ ] **Step 2: Commit**

```bash
git add site/docs/getting-started.html
git commit -m "docs(site): add getting started guide — install, first run, next steps"
```

---

### Task 7: Skills Reference Doc

**Persona:** The Signal (Swyx's learn-in-public — show real examples, not idealized demos)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4, 5, 6, 8, 9)

**Files:**
- Create: `site/docs/skills.html`

**Source material — MUST READ:** `spec.md` (skill routing and trigger conditions)

- [ ] **Step 1: Create `site/docs/skills.html`**

Each of the seven skills with:

For each skill:
- **Name and one-line description**
- **When to use it** — trigger conditions (from spec.md)
- **What it does** — one paragraph
- **How it connects to the pipeline** — where it fits in plan→execute→review
- **Example** — real invocation showing the skill's conversational style

Skills in pipeline order:

1. **gigo** — Builds your expert team from scratch. Trigger: new project, no CLAUDE.md exists. Example: the "database migration CLI" conversation from the README.

2. **gigo:maintain** — Ongoing team maintenance. Trigger: need new expertise, want a checkup, project has grown. Four modes: targeted addition, health check, restructure, upgrade.

3. **gigo:blueprint** — Ideas to execution-ready plans. Trigger: you have a task, feature, or idea. Full arc: explore → clarify → propose approaches → design → spec → plan. Hard gate: no execution without approved plan.

4. **gigo:execute** — Runs approved plans. Trigger: plan exists and is approved. Three tiers: agent teams (parallel), subagents (sequential), inline. Workers run bare — they get the spec, not the personas.

5. **gigo:verify** — Two-stage code review. Trigger: task completed, code ready for review. Stage 1: spec compliance ("did you build the right thing?"). Stage 2: engineering quality ("is the code good?").

6. **gigo:snap** — Session-end audit. Trigger: wrapping up, saving progress. Two jobs: protect the project (audit rules for bloat/staleness), then capture learnings.

7. **gigo:eval** — Context effectiveness testing. Trigger: want to prove the setup works. Pipeline eval with comparative judging.

Include shared nav, footer, meta tags.

- [ ] **Step 2: Commit**

```bash
git add site/docs/skills.html
git commit -m "docs(site): add skills reference — seven skills with examples"
```

---

### Task 8: Architecture Doc

**Persona:** The Narrator (Dykes's structured storytelling — explain the system as a coherent narrative, not a feature list)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4, 5, 6, 7, 9)

**Files:**
- Create: `site/docs/architecture.html`

- [ ] **Step 1: Create `site/docs/architecture.html`**

The two-tier system and supporting architecture explained. Sections:

**The Problem** — Context files grow monotonically. Every session adds, nothing removes. Within weeks, 200+ lines of overlapping rules. Performance degrades. Gloaguen et al. confirmed: bloated context reduces success rates, increases cost 20%+.

**Two Tiers** — Rules (auto-loaded, lean, applies to all work) vs References (on-demand, deep, task-specific). Explain the key innovation: "When to Go Deeper" pointers that make the system task-aware.

**The ~60 Line Cap** — Why. Not arbitrary — research-informed. A 30-line file that nails the essentials outperforms a 100-line file that's thorough but dilutes attention.

**The Non-Derivable Rule** — Only write what Claude can't figure out by reading the project. Philosophy, quality bars, anti-patterns — yes. Directory structure, code patterns — never. Why: codebase overviews are actively harmful because they waste attention on information the agent would have found anyway.

**The Snap** — Named after Tony's snap, not Thanos's. Sacrificing what has to go so what matters survives. The 10-point audit. Why projects get sharper over time, not bigger.

**Persona Architecture** — Blended philosophies (2-3+ real authorities per persona). Alignment signal in rules, knowledge signal in references. The Hu et al. tradeoff and how the calibration heuristic addresses it.

**The Pipeline** — Plan assembled → execute bare → review assembled. Brief version of "Two Kinds of Leadership" with link to the full research narrative.

Include shared nav, footer, meta tags.

- [ ] **Step 2: Commit**

```bash
git add site/docs/architecture.html
git commit -m "docs(site): add architecture doc — two tiers, snap, pipeline"
```

---

### Task 9: Design Philosophy Doc

**Persona:** The Narrator (engaging origin story backed by data)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** true (with Tasks 3, 4, 5, 6, 7, 8)

**Files:**
- Create: `site/docs/design-philosophy.html`

**Source material — MUST READ:** `docs/design-philosophy.md`

- [ ] **Step 1: Create `site/docs/design-philosophy.html`**

Restructure `docs/design-philosophy.md` for the site. The content is already well-written — adapt it to HTML with the shared site styling. Sections (matching the source):

1. **The origin: dev kits that worked too well** — Croftspan context, how it started
2. **Why blended philosophies, not single authorities** — the breakthrough from modeling Croftspan's C-suite
3. **The bloat problem** — what happened, then Gloaguen et al. confirming it
4. **Why two tiers instead of one** — the attention cost argument
5. **Why conversational, not procedural** — early wizard approach vs current conversation
6. **What we'd still like to figure out** — persona interaction, cross-project learning, automated health checks

Preserve the direct, honest voice of the original. Don't add marketing polish — the origin story works because it's genuine.

Include shared nav, footer, meta tags.

- [ ] **Step 2: Commit**

```bash
git add site/docs/design-philosophy.html
git commit -m "docs(site): add design philosophy — origin, decisions, open questions"
```

---

## Phase 3: README (depends on site existing for links)

### Task 10: Rewrite README.md

**Persona:** The Signal (Rocha's first-impression philosophy + Asparouhova's community taxonomy + Swyx's authenticity) + The Narrator (data presentation) + The Voice (existing GIGO persona — progressive disclosure, scan-path design)
**blocks:** 11
**blocked-by:** 1
**parallelizable:** false (needs site URLs to link to, but can reference relative paths)

**Files:**
- Modify: `README.md`

**Source material — MUST READ:** Current `README.md`, `evals/EVAL-NARRATIVE.md` (for data points)

- [ ] **Step 1: Rewrite `README.md`**

Complete rewrite following the spec structure exactly. The README is the hook — it proves value fast and links to the site for depth.

Structure:

```markdown
<div align="center">

<img src="site/assets/social-preview.png" alt="義剛 GIGO" width="600">

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/claude--code-skills-blueviolet.svg)]()

</div>

# 義剛 GIGO

**Only give them what they need for the job.**
```

Then sections in order per spec:

1. **The Problem** — "Claude Code is powerful out of the box. But most projects get context engineering wrong..." (3-4 lines, direct)

2. **See It In Action** — The two terminal examples from the current README, refined:
   - Tighten language (remove filler)
   - Keep the contrast: clear technical brief → peers who challenge, vague creative idea → guides who lead
   - Keep the conversational GIGO voice
   - End with: "Same skill, different calibration. Works for anything — software, fiction, game design, research, music, business."

3. **Quick Start** — Three lines:
   ```
   claude install @croftspan/gigo
   ```
   Open any project. Say `gigo`.

4. **The Seven Skills** — Table, one line per skill (refine existing table)

5. **Why This Works** — Condensed version:
   - Core finding: "Context helps when it shapes the questions. Context hurts when it shapes the answers."
   - Three beats with numbers: architecture (14→20), conventions (20→29), bare workers + good spec = senior/staff
   - Research foundation: 6 published papers listed with one-line contributions
   - Convention compliance: 30/30 first pass, zero review fixes

6. **Two Kinds of Leadership** — 4-5 sentence teaser, link to site/research/

7. **The Name** — 義剛 (Gigo) meaning, GIGO CS meaning, "Both are true."

8. **Footer** — Built at Croftspan. MIT License. Links to site sections.

- [ ] **Step 2: Verify rendering**

View on GitHub or with `grip README.md` — check that:
- Social preview image renders centered
- Badges display correctly
- Terminal examples are readable
- Tables are clean
- Links point to correct site paths

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): complete reimagining — 義剛 brand, problem-first, research-backed"
```

---

## Phase 4: GitHub Presence (depends on site + README)

### Task 11: GitHub Repository Settings and Hygiene

**Persona:** The Signal (GitHub SEO, discoverability, community taxonomy)
**blocks:** []
**blocked-by:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
**parallelizable:** false

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`

- [ ] **Step 1: Create `CONTRIBUTING.md`**

Brief contributing guide:
- How to report issues (use templates)
- How skills are structured (SKILL.md as hub, references/ as spokes)
- The non-derivable rule for any rules contributions
- Link to architecture doc on the site
- Note: this is a skill ecosystem — contributions are skill improvements, not application code

- [ ] **Step 2: Create `.github/ISSUE_TEMPLATE/bug_report.md`**

```yaml
---
name: Bug Report
about: Something isn't working as expected
title: "[Bug] "
labels: bug
---

**Skill:** (which skill — gigo, maintain, plan, execute, review, snap, eval)

**What happened:**

**What you expected:**

**Steps to reproduce:**

**Claude Code version:**
```

- [ ] **Step 3: Create `.github/ISSUE_TEMPLATE/feature_request.md`**

```yaml
---
name: Feature Request
about: Suggest an improvement
title: "[Feature] "
labels: enhancement
---

**Which skill would this affect?**

**What problem does this solve?**

**What does your ideal solution look like?**
```

- [ ] **Step 4: Update GitHub repository settings via CLI**

```bash
# Update repo description
gh repo edit --description "義剛 GIGO — Assembles expert AI teams for any domain. Research-backed context engineering for Claude Code. 9 phases of eval data prove where context helps and where it hurts."

# Add topics
gh repo edit --add-topic claude-code,claude-code-skills,claude-code-plugins,ai-agents,context-engineering,prompt-engineering,developer-tools,claude,anthropic,ai-coding,llm-agents,research,eval,personas

# Set homepage to GitHub Pages URL
gh repo edit --homepage "https://eaven.github.io/gigo/"
```

- [ ] **Step 5: Enable GitHub Pages**

```bash
# Enable GitHub Pages from main branch, /site directory
gh api repos/croftspan/gigo/pages -X POST -f source.branch=main -f source.path=/site
```

If this fails (Pages may need to be enabled via web UI), note it as a manual step.

- [ ] **Step 6: Set social preview image**

Upload `site/assets/social-preview.png` as the repository social preview via GitHub web UI (Settings → Social preview). Note: this cannot be done via CLI — document as manual step.

- [ ] **Step 7: Commit**

```bash
git add CONTRIBUTING.md .github/
git commit -m "docs: add contributing guide and issue templates"
```

- [ ] **Step 8: Push and verify**

```bash
git push origin main
```

Verify:
- GitHub Pages site is live at https://eaven.github.io/gigo/
- Repository description shows correctly
- Topics are visible
- Social preview renders on link shares
- Issue templates appear when creating new issues

---

## Dependency Graph

```
Task 1 (scaffold) ──┬──→ Task 3 (landing page)     ──┐
                     ├──→ Task 4 (research narrative) ─┤
                     ├──→ Task 5 (eval data)          ─┤
                     ├──→ Task 6 (getting started)    ─┤
Task 2 (preview img)─├──→ Task 7 (skills doc)         ─┼──→ Task 11 (GitHub presence)
                     ├──→ Task 8 (architecture doc)   ─┤
                     ├──→ Task 9 (design philosophy)  ─┤
                     └──→ Task 10 (README)            ─┘
```

- Tasks 1 and 2 are parallel (no shared files)
- Tasks 3-9 are all parallel (each is an independent HTML file, all depend only on Task 1 for shared CSS)
- Task 10 depends on Task 1 (needs site structure for links)
- Task 11 depends on everything (final verification, GitHub settings reference the completed site)

## Risks

- **GitHub Pages from subdirectory:** GitHub Pages can serve from `/` or `/docs` on main branch. Serving from `/site` may require a custom GitHub Actions workflow instead of the built-in Pages setting. If the `/site` path doesn't work natively, create a simple `.github/workflows/deploy.yml` that copies `site/` contents to the deployment.
- **Social preview upload:** Cannot be automated via CLI — requires manual upload through GitHub web UI.
- **Shared layout duplication:** 8 HTML files with duplicated nav/footer. If the nav structure changes later, all 8 files need updating. Acceptable for launch — can add a simple build script (e.g., a shell script that injects shared partials) if maintenance becomes painful.
- **arXiv links:** Not all cited papers may have publicly accessible arXiv links. Hu et al., Kong et al., Xu et al. need specific arXiv IDs verified. If unavailable, cite by author/year with paper title instead of link.

## Done When

1. GitHub Pages site is live with all 8 pages rendering correctly
2. README is rewritten and renders correctly on GitHub
3. Repository description, topics, and homepage are set
4. Social preview image renders on GitHub, Twitter, and Slack link previews
5. "Two Kinds of Leadership" is a self-contained piece that can be shared independently
6. Every public claim has a citation or data reference
7. All pages work on mobile (375px) and desktop (1440px)
8. Dark mode is the default, light mode toggle works
