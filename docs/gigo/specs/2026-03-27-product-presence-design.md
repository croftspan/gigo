# GIGO Product Presence — Design Spec

## Overview

Complete reimagining of GIGO's public presence: README, GitHub Pages product site, and GitHub repository presentation. Three pillars:

1. **義剛** — the identity (righteousness + strength)
2. **GIGO** — the problem it solves (garbage context in = garbage output)
3. **Research-backed** — the method (published research + 9 phases of original empirical testing)

## Brand Identity

### Name Treatment

義剛 leads. GIGO follows. The Japanese meaning is the identity — discipline, righteousness, strength. The CS acronym is the problem statement — garbage in, garbage out. Both are true simultaneously. The project exists because garbage context produces garbage output, and it solves that problem with rigorous methodology.

### Tagline

"Only give them what they need for the job."

This is the core finding from 9 phases of testing, stated plainly. It works as brand, as methodology, and as technical principle.

### Visual Identity

Typography-driven. The kanji 義剛 is the mark. No illustrated mascot, no abstract logo. Clean, minimal, serious. Dark background, light text. The aesthetic communicates: this is research, not a side project.

Social preview image: 義剛 GIGO centered, tagline below, dark background. Created with artista.

### Voice

Direct. No hype. Let the data speak. The project's credibility comes from empirical evidence, not marketing language. When making a claim, cite the phase and the numbers. "Bare workers produce senior/staff-level code (Phase 7, 3/3 runs)" not "our revolutionary approach transforms AI output."

Anti-patterns:
- No "revolutionary," "game-changing," "next-generation"
- No startup-speak ("10x your productivity")
- No vague claims without data backing
- No self-congratulation

## Component 1: README.md

### Architecture

Progressive disclosure. Hooks in 5 seconds, proves value in 30, gets them running in 60.

### Structure

```
[Social preview image / hero]
[Badges: license, claude code version]

# 義剛 GIGO

Only give them what they need for the job.

## The Problem

Claude Code is powerful out of the box. But most projects get context
engineering wrong — they either give Claude nothing (and get generic output)
or give it everything (and get worse output that costs more).

We spent 9 experimental phases proving exactly where context helps and where
it hurts. Then we built a system that applies the findings automatically.

## See It In Action

[Terminal example 1: clear technical brief → peers who challenge]
[Terminal example 2: vague creative idea → guides who lead]

Same skill, different calibration. Works for anything — software, fiction,
game design, research, music, business.

## Quick Start

claude install @croftspan/gigo

Open any project. Say "gigo."

## The Seven Skills

[Table: gigo, maintain, plan, execute, review, snap, eval — one line each]

## Why This Works

### The core finding

Context helps when it shapes the questions. Context hurts when it shapes
the answers.

[3-beat summary:]
1. Architecture carries coherence (14→20 out of 30)
2. Personas add conventions on top (20→29)
3. Workers run bare + good spec = senior/staff code. Every time.

### The research

Built on published research — not intuition:
- Gloaguen et al. (2026): bloated context reduces success, increases cost 20%+
- Hu et al.: personas help alignment but hurt knowledge retrieval
- Kong et al. + Xu et al.: specific blended personas outperform generic roles
- Shinn et al.: reflection agents make better decisions
- Yang et al.: interface design matters more than the prompt

Then validated with 9 phases of original experiments across two domains
(Rails API + children's mystery novel), 50+ eval runs, comparative judging,
and principal engineer reviews.

### Convention compliance

30/30 conventions matched on first pass across two execution tiers.
Zero review fixes needed. The spec is what matters.

## Two Kinds of Leadership

[4-5 sentence teaser of the central insight]

The intuitive approach — load workers with rules, quality gates, and
compliance checks — produces mid-level output that checks boxes instead
of thinking.

The counterintuitive finding: plan with the full team, then send bare
workers a clear spec. They produce senior/staff-level code because the
team's expertise is baked into the spec as requirements, not loaded as
rules the worker has to perform against.

Read the full research narrative →

## The Name

義剛 (Gigo) — "righteousness" and "strong." In computer science, GIGO
means "Garbage In, Garbage Out." Both meanings apply. The project exists
because garbage context produces garbage output, and it solves that problem
with discipline.

---

Built at Croftspan. MIT License.
[Link to site] | [Link to research] | [Link to docs]
```

### Key Decisions

- **Problem-first.** Before features, before install, the reader feels the pain. "Most projects get context engineering wrong" — if they've experienced this, they're hooked.
- **Terminal examples stay.** The two existing examples (technical brief + "kids books idk") are the best demonstration of the skill's conversational intelligence. Refine language, keep the concept.
- **Data in the README is condensed.** The full tables, phase-by-phase results, and narrative all live on the site. The README gives you enough to believe it, then links to proof.
- **"Two Kinds of Leadership" is a teaser.** 4-5 sentences, then a link. This is the content people share — it lives on the site where it can breathe.
- **The Name section is last.** It's the emotional landing. After they understand the tool, they learn the meaning. Resonance after respect.
- **No install before understanding.** Quick Start comes after "See It In Action" and "The Problem" — they know what they're installing before they install it.

### Content Removed from README (Moved to Site)

- Full "Why this works" section with data tables → site /research
- "The architecture that won" table → site /research
- Pipeline coherence test details → site /eval-data
- Convention compliance full breakdown → site /eval-data
- Further reading links to repo files → site internal links
- "What the project files look like" section → site /docs/architecture

## Component 2: GitHub Pages Site

### Framework

Static HTML/CSS/JS. No framework, no build step, no dependencies.

Rationale:
- Claude Code writes vanilla HTML/CSS/JS natively — no framework abstractions to misinterpret
- Zero maintenance — no npm audit, no breaking upgrades, no build toolchain
- GitHub Pages deploys directly on push — no build step, no GitHub Actions needed
- Any page is one file — editable without understanding a component tree
- The site is 6-7 static pages, not an app — a framework is overhead without benefit

If interactive features are needed later (search, demos), vanilla JS handles them. No framework lock-in to escape.

### Site Structure

```
/ .......................... Landing page
/research .................. "Two Kinds of Leadership" — flagship article
/research/eval-data ........ Phase-by-phase results with raw numbers
/docs ...................... Documentation hub
/docs/getting-started ...... Install, first run, what happens next
/docs/skills ............... Each skill with usage examples
/docs/architecture ......... Two-tier system, the snap, line budgets
/docs/design-philosophy .... How and why this was built
```

### Landing Page (/)

Follows Evil Martians study findings (100+ dev tool landing pages analyzed):
- Centered layout, bold headline, supporting visual
- Dual CTAs: "Install" (primary) + "View on GitHub" (secondary)
- No salesy language
- Social proof through data, not testimonials

```
Structure:

[Hero]
義剛 GIGO
Only give them what they need for the job.
[Install button] [GitHub button]

[Problem — 3 beats]
1. Most AI context engineering is vibes-based
2. We ran 9 phases of experiments to prove what actually works
3. Then built a system that applies the findings automatically

[The Finding — visual/diagram]
Plan with experts → Embed expertise in the spec → Execute bare → Review with quality bars
(with the key numbers: 14→20→29, 30/30 conventions, senior/staff every time)

[The Research Foundation]
Built on 6 published papers + 9 phases of original experiments
[Brief citations with links]

[Quick Start]
Three steps to running

[Skills Overview]
Seven skills, one sentence each, link to docs

[The Name]
義剛 = righteousness + strength
GIGO = garbage in, garbage out
Both are true.

[Footer]
Built at Croftspan | MIT | Links
```

### Research Page (/research) — "Two Kinds of Leadership"

This is the flagship content. The piece that gets shared. Restructured from the eval narrative for a public audience.

**Not a docs page. Not a blog post. A research narrative.**

Structure:

```
# Two Kinds of Leadership
## What 9 experimental phases taught us about AI context engineering

The Question
→ Does assembled context actually change AI behavior, or is it expensive
  token decoration?

The Setup
→ Two domains, 20 prompts, 100 evaluations per run, blinded judging
→ Brief, accessible explanation of methodology

Phase 1: The Baseline (87%)
→ It works. But the pattern in the non-wins matches published research.
→ Hu et al. tradeoff: personas help alignment, hurt knowledge retrieval.

The Calibration (87% → 96%)
→ Two levers: persona calibration heuristic + task-specific pointers
→ 6 lines of code. 9 percentage points.

The Hallucination Problem
→ The eval scored beautiful garbage without blinking.
→ Led to the Overwatch system.

The Proficiency Test
→ "Bare produces higher peak craft. Assembled produces better structural work."
→ "B's team, with A's instincts" — the judge's verdict.

The Instinct Experiments
→ War stories produce instincts. Rules produce compliance.
→ But no format beat bare on creative work.

The Planning Pipeline
→ Assembled asks WHY. Bare asks WHAT.
→ Personas change how problems are explored, not just how answers are presented.

The Format Doesn't Matter
→ 4 formats, 3 runs, principal engineer reviews.
→ Bare rated senior/staff every time. The spec is what matters.

Two Kinds of Leadership (the synthesis)
→ "Do your job or I'll fire you" — the data showing it produces mid-level work
→ "What can I do to help you do your job better?" — the data showing it produces senior/staff work
→ The architecture: plan assembled, execute bare, review assembled.

The Complete Architecture
→ Table: phase / context / why
→ The numbers

The Research Foundation
→ Full citations: Gloaguen, Hu, Kong, Xu, Shinn, Yang
→ How each paper informed a specific design decision
→ Where our findings extend or challenge the published work

What This Means
→ For anyone building with AI agents, not just GIGO users
→ The principle is general: context shapes questions (good), context shapes answers (bad)
```

**Voice for this piece:** Third person, research-narrative style. "We tested..." "The data showed..." Not academic dry — engaging but grounded. Think Nate Silver's data journalism: rigorous findings told as a story.

### Eval Data Page (/research/eval-data)

For people who want the raw numbers. Phase-by-phase results tables, methodology details, links to the actual result files in the repo.

Not restructured — presented as reference data with brief context for each phase.

### Documentation Pages (/docs/*)

**Getting Started** — Install, what happens on first run (the conversational flow), what gets created (.claude/ directory), next steps (run gigo:blueprint on your first task).

**Skills** — Each of the seven skills with:
- What it does (one paragraph)
- When to use it (trigger conditions)
- Example invocation and output
- How it connects to the pipeline

**Architecture** — The two-tier system explained:
- Rules (auto-loaded) vs References (on-demand)
- The ~60 line cap and why
- The non-derivable rule
- The Snap and what it protects against
- "When to Go Deeper" pointers

**Design Philosophy** — Restructured from docs/design-philosophy.md:
- Origin at Croftspan
- Why blended philosophies
- The bloat problem and the research that confirmed it
- Why two tiers
- Why conversational
- Open questions

## Component 3: GitHub Repository Presence

### Repository Description

"義剛 GIGO — Assembles expert AI teams for any domain. Research-backed context engineering for Claude Code. 9 phases of eval data prove where context helps and where it hurts."

### Topics

```
claude-code
claude-code-skills
claude-code-plugins
ai-agents
context-engineering
prompt-engineering
developer-tools
claude
anthropic
ai-coding
llm-agents
research
eval
personas
```

### Social Preview Image

義剛 GIGO in clean typography. Dark background, light text. Tagline below: "Only give them what they need for the job." Created with artista.

Dimensions: 1280x640px (GitHub recommended).

### Repository Hygiene

- LICENSE file (MIT — already exists)
- CONTRIBUTING.md (brief — how to report issues, how skills are structured)
- Issue templates (bug report, feature request)
- GitHub Actions for site deployment (Next.js/static → GitHub Pages)

## Component 4: Content Strategy

### The Shareable Piece

"Two Kinds of Leadership" is designed to be shared independently of the tool. Someone reads it on HN or Twitter, finds the management insight compelling, discovers it came from an AI context engineering project, follows the link.

The piece works even if the reader never installs GIGO — the findings about planning vs execution context apply to anyone building with AI agents. That's the distribution advantage: the content is useful beyond the product.

### Research Credibility

Every claim in public-facing content cites either:
- A published paper (with arXiv link)
- A specific phase of our experiments (with methodology visible)
- Both

No uncited claims. No "we found that..." without pointing to the data. This is the differentiation from every other Claude Code skill project.

### SEO / Discoverability

GitHub Pages sites inherit github.io's high domain authority. The research page targets terms like "AI context engineering," "LLM agent context," "Claude Code best practices." The README targets "Claude Code skills," "Claude Code plugins," "AI coding assistant."

## Conventions

- **File naming:** kebab-case for all site pages and assets
- **Image format:** SVG for logos/icons, WebP for screenshots/demos, PNG fallback for social preview
- **Code examples in docs:** Real, runnable examples from the actual project — not fabricated demos
- **Citations:** Author et al. (year) inline, full reference with arXiv/DOI link at bottom of page
- **Voice:** Direct, data-backed, no hype. "We tested X. The result was Y." Not "Our revolutionary X transforms Y."
- **Dark mode:** Primary design target. Light mode supported but dark is the default.
- **Terminal examples:** Use the actual GIGO conversational style from real sessions, not idealized demos
- **Link structure:** All internal links use relative paths. External links open in new tab.
- **Commit messages:** `docs(site):` prefix for site content, `docs(readme):` for README changes, `feat(site):` for site infrastructure
- **Branch strategy:** Feature branch `product-presence`, PR to main when ready

## Dependencies

- **None.** Static HTML/CSS/JS — no build tools, no package.json, no node_modules.
- **artista:** For social preview image and any brand assets (invoked via skill, not a code dependency)
- **GitHub Pages:** Hosting (free, github.io domain authority). Deploys directly from branch — no build step.

## Source Material Pointers

Workers writing content for the site MUST read these source files — they contain the actual data, quotes, and findings that public content is built from:

- **Eval narrative (primary source):** `evals/EVAL-NARRATIVE.md` — all 7 phases with methodology, results, and analysis. This is the source of truth for "Two Kinds of Leadership."
- **Phase 9 integration test:** `evals/integration-test/` — convention compliance data (30/30), pipeline validation
- **Design philosophy:** `docs/design-philosophy.md` — origin story, Croftspan context, open questions
- **Current README:** `README.md` — the two terminal examples to preserve and refine
- **Existing spec:** `spec.md` — skill routing, pipeline architecture, persona structure

### Terminal Example Refinement

The two existing terminal examples (technical CLI brief + vague "kids books" idea) demonstrate GIGO's conversational calibration. Keep the concept and conversational tone. Refinements:
- Tighten language — remove any filler
- Ensure persona blends shown are real (named authorities with specific contributions)
- Make the contrast between "clear vision" and "vague idea" sharper
- Format for readability at GitHub's rendered markdown width

### Site Directory in Repo

Static HTML site lives at `site/` in the repo root. No build step — GitHub Pages serves these files directly.

```
site/
├── index.html                     (landing page)
├── research/
│   ├── index.html                 (Two Kinds of Leadership)
│   └── eval-data.html             (phase-by-phase results)
├── docs/
│   ├── getting-started.html
│   ├── skills.html
│   ├── architecture.html
│   └── design-philosophy.html
├── css/
│   └── style.css                  (shared stylesheet — dark-mode-first)
├── js/
│   └── main.js                    (minimal — nav, dark/light toggle if needed)
├── assets/
│   ├── social-preview.png         (1280x640, GitHub/Twitter/Slack previews)
│   └── favicon.svg
└── 404.html                       (custom 404)
```

Shared layout (nav, footer) is duplicated across HTML files rather than templated. This is intentional — no build step means no includes. For 8 pages this is manageable and any page can be edited in isolation.

## What's NOT in Scope

- Custom domain (can be added later, not blocking)
- Analytics / telemetry on the site
- Blog / changelog section (the research page handles thought leadership)
- Video demos or screencasts (terminal examples in text are sufficient for launch)
- Community features (Discord, discussions — premature before traction)
- Internationalization (English only for launch)
- Rewriting the eval narrative source file — it stays in repo as-is, the site gets a restructured version

## Success Criteria

1. A stranger understands what GIGO does within 5 seconds of landing on the README
2. A stranger understands why it works within 30 seconds (the data, not just claims)
3. Install to first run takes under 2 minutes
4. "Two Kinds of Leadership" is self-contained — shareable without needing to know GIGO exists
5. Every claim in public-facing content has a citation or data reference
6. The site deploys automatically on push to main via GitHub Actions
7. Social preview image renders correctly on GitHub, Twitter, Slack link previews
