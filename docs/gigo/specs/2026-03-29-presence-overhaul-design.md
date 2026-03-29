# Presence Overhaul: The Voice Upgrade + README/Site Rewrite

## Purpose

Rewrite GIGO's public-facing content to lead with the problem people feel (CLAUDE.md rot), show the transformation (what you become), and eliminate language that repels (jargon, "proven", defensive tone). Upgrade The Voice persona with copywriting authorities to sustain this voice going forward.

## Scope

Three files:
- `CLAUDE.md` (The Voice persona section + "proven" replacements in lines 3 and 64)
- `README.md` (full rewrite)
- `site/index.html` (content rewrite, keep design system)

Minor touch: `site/css/style.css` (add 2 animation-delay rules for new sections).

Deferred to follow-up: `site/docs/getting-started.html`, `site/docs/skills.html`, `site/research/index.html`.

## Requirements

### R1: Upgrade The Voice persona in CLAUDE.md

Expand the existing Voice persona entry (currently lines 49-55 of CLAUDE.md) with three new authorities while keeping the existing three.

**Additionally:** Replace "proven" with "validated" in CLAUDE.md line 3 (project description: "the proven plan→execute→review pipeline" becomes "the validated plan→execute→review pipeline") and line 64 (Conductor persona: "produces the proven architecture" becomes "produces the validated architecture"). These are auto-loaded into every conversation and must match the language rules.

**Existing authorities (keep):**
- Kathy Sierra's "make the user awesome"
- Stephanie Morillo's developer content strategy
- Simon Sinek's "Start with Why"

**New authorities (add):**
- April Dunford's positioning discipline (Obviously Awesome). Frame around what the customer becomes, not what the product does.
- Joanna Wiebe's conversion copy rigor (Copyhackers). Every sentence survives the "so what?" test. Voice-of-customer language, not insider jargon.
- Harry Dry's one-transformation-per-message clarity (Marketing Examples). Make it about them, not you. No feature lists before the reader knows why they should care.

**Updated fields:**

"Modeled after" block becomes:
```
**Modeled after:** Kathy Sierra's "make the user awesome" — README makes the reader feel what having it is like
+ Stephanie Morillo's developer content strategy — structure for scanners first, readers second
+ Simon Sinek's "Start with Why" — lead with the problem people feel, not the solution you built
+ April Dunford's positioning discipline — frame around what the customer becomes, not what the product does
+ Joanna Wiebe's conversion copy rigor — every sentence survives the "so what?" test, voice-of-customer language not insider jargon
+ Harry Dry's transformation-first clarity — make it about them not you, no feature lists before the reader knows why they should care.
```

"Owns" becomes: README architecture, progressive disclosure, the 5-second test, scan-path design, emotional resonance before technical depth, transformation-first copy, the "so what?" test, positioning discipline, voice-of-customer language

"Quality bar" becomes: A stranger knows what problem this solves, what they become, and how to try it within 30 seconds. Every sentence survives "so what?" If you removed all feature language, the reader still wants it.

"Won't do" becomes: Leading with features over problems, walls of code before the reader cares, origin stories above the fold, feature lists before the reader knows the problem, insider jargon the customer wouldn't use, leading with credentials before the transformation

### R2: Rewrite README.md

**New structure (in this order):**

1. **Title + problem statement.** 義剛 GIGO heading. Then 2-3 sentences about the core problem: CLAUDE.md grows out of control, more rules make AI output worse. This is the lead. Not features, not research credentials.

2. **What you become.** 2-3 sentences. Projects that get sharper over time. Specs that work on the first pass. Reviews that find almost nothing because the upstream process caught it.

3. **Quick start.** `claude install @croftspan/gigo` + "Open any project in Claude Code. Type `gigo`."

4. **How it works.** 4 numbered items, each transformation-focused:
   - Plan: expert team catches what you'd miss
   - Spec: knowledge becomes concrete requirements workers can follow without hand-holding
   - Execute: workers get the spec, produce first-pass quality that sticks
   - Review: two focused passes catch different things than one pass trying to do everything

5. **Seven skills.** Keep the existing table format and descriptions. No changes needed to the skill descriptions themselves.

6. **Your project stays lean.** Expand this section. Tell the CLAUDE.md rot story:
   - You set up a project, add rules, things work
   - Every session adds more, nothing gets removed
   - Within weeks it's hundreds of lines of overlapping, stale guidance
   - Research shows this makes output worse, not better (cite Gloaguen et al.)
   - GIGO fixes this: rules stay lean, deep knowledge loads only when needed, The Snap audits every session

7. **See it in action.** Keep both example briefs (game server + tabletop RPG). Keep the current format. Trim only if individual blocks are unnecessarily verbose. Keep the closing line about working across domains. Placed after the skills table and lean-project story so the core pitch (problem, transformation, how, skills, lean) isn't blocked by 75 lines of preformatted dialogue. The examples convert people who are already interested.

8. **The name.** Keep as-is: 義剛 pronunciation, dual meaning.

9. **Footer.** Keep: Built at Croftspan. Apache 2.0. Links to site pages.

### R3: Rewrite site/index.html

Keep: nav, footer, CSS references (`css/style.css`), JS references (`js/main.js`), skip-link, theme toggle, existing CSS classes and component patterns (step cards, stat blocks, table wrapper).

Change: section content, section count (6 current sections become 8), section order, hero text, meta description, OG tags, page title. New sections use the same `<section class="section"><div class="container">` wrapper pattern.

**New section structure:**

1. **Hero section.** Replace current hero text.
   - H1: 義剛 GIGO (keep)
   - Subtitle: Problem-first, not feature-first. Something like "Your AI setup is making your output worse." or "CLAUDE.md rot is real. GIGO fixes it." (exact copy to be written during implementation)
   - Hero description: What you become, not what the product does. 1-2 sentences.
   - CTA group: Keep Get Started + GitHub buttons
   - Install command: Keep

2. **The problem section.** NEW section. 3-4 sentences about CLAUDE.md rot. Every Claude Code user knows this feeling: you add rules, they pile up, output gets worse. Reference the research finding (bloated context reduces success rates) but don't lead with the citation.

3. **The transformation section.** NEW section. Before/after framing. Not features. What changes for the user. Use a simple two-list format: a "without" list and a "with" list, each 3-4 items. No new CSS needed. Use standard `<ul>` or `<p>` elements within the existing `.section > .container` wrapper. Do not attempt a side-by-side two-column layout (no CSS class exists for it in the current design system).

4. **How it works section.** Keep 4-step structure with step cards. Rewrite step descriptions to be transformation-focused (same language as README R2 item 4).

5. **Results section.** Replace "Tested. Proven. Published." header. New header frames results as achievements. Rewrite body text to present results confidently without defensive "we proved it" language. Keep the `results-highlight` stat block structure but rewrite the three stats as achievements, not grades:
   - Stat 1: Reframe "97%" from a score into an achievement statement (e.g., "First-pass quality so high reviewers found nothing to fix")
   - Stat 2: Reframe "Senior level output" from a grade into what it means for the user
   - Stat 3: Reframe "70M+ tokens burned proving it" into a validation-investment statement (e.g., "9 phases of controlled experiments across two domains"). If cutting stat 3 instead, also change the inline style from `grid-template-columns: repeat(3, 1fr)` to `repeat(2, 1fr)` to prevent a broken two-items-in-three-columns layout. Decision: keep three stats, reframe stat 3
   - Keep research paper links (Gloaguen et al. + Hu et al.). Keep "Read the full research" link.

6. **Your project stays lean section.** Keep and expand with CLAUDE.md rot story (same content as README R2 item 7).

7. **Seven skills section.** Keep table as-is.

8. **The name section.** Keep as-is.

**Meta tags update:**
- Page title: Replace "Research the experts. Build the team. Ship better work." with problem/transformation framing
- Meta description: Rewrite with problem-first language
- OG/Twitter tags: Match new title and description

### R4: Language rules (apply across all three files)

| Don't write | Write instead |
|-------------|--------------|
| proven | validated / tested / measured |
| assembled context | expert knowledge |
| context engineering | making AI output better |
| two-tier architecture | keeps your project lean |
| derivability testing | removes rules the AI doesn't need |
| personas (in user-facing copy) | expert team / expert team members |
| token economics | (omit) |
| research-backed | (just show results) |
| em dashes (—) | periods or commas |

Notes:
- "personas" is fine in CLAUDE.md (internal/developer-facing). The language rule applies to README and site copy where the audience is potential users.
- Em dashes are fine in CLAUDE.md persona descriptions (they follow the existing convention used by all other personas). The em-dash rule applies to README and site copy only.

### R5: Global cleanup

After all rewrites, scan all three files for:
- Any remaining "proven" (case-insensitive)
- Any em dashes (— or `&mdash;`)
- Any jargon terms from the language rules table that slipped through

## Conventions

- **Heading capitalization:** Match existing style in each file. README uses title case for section headers. Site uses sentence case for section headers per existing CSS.
- **Link format in README:** Relative paths for site pages (e.g., `site/research/`). Full URLs for external links.
- **HTML entities in site:** Use `&rsquo;` for curly apostrophes, `&ldquo;`/`&rdquo;` for curly quotes. No `&mdash;`.
- **Site section pattern:** Each content section uses `<section class="section"><div class="container">` wrapper. New sections follow this pattern.
- **Stat blocks in site:** Use `results-highlight` div with `results-stat` children containing `stat-number` and `stat-label` spans.
- **Step cards in site:** Use `how-it-works` div with `how-it-works-step` children containing `step-number`, `step-label`, `step-desc`.
- **Animation stagger in site:** The existing CSS (`site/css/style.css`) applies staggered `animation-delay` to `.section:nth-child(2)` through `:nth-child(5)`. With 7 content sections (up from 5), add `:nth-child(6)` and `:nth-child(7)` rules to `style.css` following the existing 0.1s increment pattern.
- **No feature-first copy.** Every section leads with the problem or transformation, then explains how. The "so what?" test: if a sentence describes a feature without connecting it to what the user becomes, rewrite it.

## What Success Looks Like

The 30-second test. A stranger who has never heard of GIGO reads the README or lands on the site. Within 30 seconds they can answer:
1. What problem does this solve? (Your AI setup grows out of control and makes output worse)
2. What do I become after using it? (Projects get sharper, specs work first pass, reviews find nothing)
3. How do I try it? (`claude install @croftspan/gigo`)

No sentence survives if the answer to "so what?" is unclear.

<!-- approved: spec 2026-03-29T05:10:20 by:Eaven -->
