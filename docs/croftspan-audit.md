# Croftspan Audit — Mining the Real-World Test Case

Date: 2026-03-24

Croftspan is a real agency built on Claude Code over 24 PRs and months of accumulated institutional knowledge. This audit examines what worked, what didn't, and what the avengers-assemble skill should learn from it.

---

## What Croftspan Got Right

### 1. The Vault Pattern

`agency/vault/` is a scoped knowledge store:
- **Client-scoped:** `vault/clients/meridian-health/client-notes.md` — preferences, decisions, industry learnings per client
- **Service-scoped dev kits:** `vault/services/development/ruby-rails/` — 5 files per language (identity, stack, code-standards, testing, agent)

Each dev kit is a blended-philosophy pattern made concrete. The Ruby kit draws from DHH, 37signals, Sandi Metz, Kent Beck. This IS the avengers-assemble methodology, just built by hand before the skill existed.

**Skill lesson:** The reference tier should explicitly support client/project-scoped knowledge and reusable kits per domain. The vault pattern (context that accumulates per engagement) is a dimension the skill doesn't currently model.

### 2. Persona Architecture with DO/DON'T Examples

TEAM.md (414 lines) has deep persona profiles. The critical insight: personas include **real writing samples** showing what they sound like vs what AI slop sounds like. Lena's section has 4 DO messages and 2 DON'T messages. This is massively more useful than abstract descriptions.

**Skill lesson:** The persona template should push for concrete DO/DON'T examples. Real writing samples in references/ are worth 10x abstract descriptions in rules/.

### 3. The Anti-Slop Bible

STANDARDS.md has a 60-line "AI Slop (Zero Tolerance)" section:
- Banned phrases (30+): "delve into," "leverage," "seamless," "embark on a journey," etc.
- Banned punctuation: em dash as parenthetical (single most recognizable AI fingerprint), double hyphens, excessive exclamation points
- Banned patterns: the AI triplet (lists of 3 with identical grammatical structure), restating the prompt, excessive hedging, empty transitions

This is pure non-derivable knowledge that massively improves output quality.

**Skill lesson:** Every project should consider a domain-specific "banned list." Not just what to do — what to never do, and why it marks work as amateur.

### 4. Three Quality Gates

Studio self-check -> Vince adversarial review -> Operator human review. Vince always gets **fresh sessions** (no context carryover) so he's adversarial, not sympathetic.

**Skill lesson:** For projects with production pipelines, workflow.md should include a review pattern. Fresh-eyes review is universal, not Croftspan-specific.

### 5. Numbering Convention for Rules

`.claude/rules/01-stack.md` through `25-deliverable-standard.md`:
- 01-04: builder/developer rules
- 05: app architecture (institutional knowledge)
- 10-14: executive/business context
- 20-25: agency operations

Groups rules by context, makes it clear which rules apply to which mode of work.

**Skill lesson:** Suggest numbering conventions when the project has multiple distinct concerns.

### 6. Governance-to-Rules Pointer Pattern

Heavy docs live in `agency/governance/` (STANDARDS.md, TEAM.md, SERVICES.md — 1,900+ lines total). Rules files are one-liners that say "read X before Y." This is the two-tier architecture working exactly as designed.

Examples:
- Rule 22: "Read STANDARDS.md before producing any deliverable."
- Rule 25: "Read DELIVERABLE_STANDARD.md before production begins."
- Rule 21: "Only Lena and Marco post client-visible comments."

Lean pointers in rules, depth in references. Textbook.

### 7. Immutable Audit Trail

Decision records in `executive/decisions/` — every major decision with reasoning, alternatives, and revenue impact. Postmortems when things went wrong (`postmortem-seed-schema-mismatch.md`). This institutional memory prevents re-debating settled questions.

**Skill lesson:** Workflow should include a decisions/postmortem pattern for projects that make architectural or strategic choices.

---

## What Croftspan Got Wrong

### Critical: `05-app-architecture.md` is 138 lines (2.3x the cap)

This file loads on every conversation and contains:

| Section | Lines | Derivable? | Verdict |
|---|---|---|---|
| Data model chain | ~5 | No | Keep in rules |
| Authentication | ~5 | Partially | Keep — easy to get wrong |
| API layer patterns | ~10 | Partially | Keep the conventions, move examples to ref |
| Client Dashboard | ~8 | Yes | Move to references |
| Operator Dashboard | ~6 | Yes | Move to references |
| ActionCable | ~10 | Mix | Keep the two-stream pattern, move details |
| Agent Dispatch | ~15 | No | Keep — non-derivable orchestration logic |
| Client Intake | ~12 | Mix | Keep the flow, move implementation details |
| Time Estimation | ~10 | Mix | Keep pipeline, move details |
| Maintenance Mode | ~5 | No | Keep — intentional design difference |
| Gotchas | ~30 | No | KEEP — pure gold, prevents real bugs |

**Action:** Split into ~60 line rules file (non-derivable core + gotchas) + `.claude/references/app-architecture-deep.md` (derivable details, examples, dashboard specifics).

### Candidate for References: `11-schema-verification.md` (48 lines)

A verification protocol for writing specs/code that touches the data layer. But not every conversation touches the data layer. CSS work, documentation, frontend tweaks don't need 48 lines about "read db/schema.rb before writing anything."

**Action:** Move to `.claude/references/schema-verification.md` with a "When to Go Deeper" pointer: "When writing code that touches models, schema, or data layer, read references/schema-verification.md."

### Derivable Rules That Can Be Let Go

- **Rule 20 (API only):** "Use REST API, env vars available." Agent can figure this out from controllers and env setup.
- **Rule 23 (session discipline):** "500 turns, complete full task." This is agent dispatch config for headless sessions, not useful for interactive development.

### Agent-Specific vs Developer Rules

Rules 20-25 are for the headless agent dispatch system (Studio, Vince, Kai, Orchestrator). They tell agents how to behave when dispatched by the app. But when Eaven is working interactively in Claude Code, these rules load too — adding ~10 lines of irrelevant context about session discipline, auto-save routing, client communication protocols.

**Action:** These should either be scoped to agent dispatch (loaded by the dispatch system, not by `.claude/rules/`) or marked clearly so the interactive agent knows to ignore them.

### One-Liner Rules Could Consolidate

Rules 10, 12, 13, 20, 21, 22, 25 are each 1 line. That's 7 files for 7 lines of content. While individually they're lean, the file count itself adds cognitive overhead.

**Action:** Consolidate into 2-3 files by category: `agency-operations.md` (21, 22, 23, 24, 25), `executive-context.md` (10, 12, 13, 14).

### TEAM.md (414 lines) and SERVICES.md (738 lines) are Massive

These are correctly in `agency/governance/` (reference tier), not in rules. But they're read frequently by the production agents. SERVICES.md at 738 lines is especially heavy — it contains full agent instructions, pricing, and deliverable specs for every service type.

**Potential action:** Split SERVICES.md into `SERVICES.md` (catalog overview, tiers, policies) + per-service-type reference files. But this is a lower priority — it's already in the reference tier.

---

## Patterns Worth Extracting for the Skill

### The Dev Kit Pattern (Bruno's Brain)

Before writing any code in a language, Bruno loads 5 files:
1. `identity.md` — who Bruno is in this stack (blended philosophy)
2. `stack.md` — pinned versions, forbidden deps
3. `code-standards.md` — patterns and anti-patterns
4. `testing.md` — testing philosophy and approach
5. `agent.md` — how to operate (autonomy model, session behavior)

"New language arrives with no kit? The kit is the first deliverable, not the code." This is avengers-assemble in miniature — research the domain, build the expertise framework, THEN start working.

### The Persona Promotion Pipeline

Client-level persona -> `vault/080-PERSONAS/` staging -> TEAM.md permanent roster. Used on 3+ projects = promoted. This is how expertise accumulates without bloating.

### The Postmortem Pattern

`executive/decisions/postmortem-seed-schema-mismatch.md` — when an 11-error spec required 3 rounds of revision. This postmortem directly led to Rule 11 (schema verification). Failures become institutional knowledge.

### The Autonomy Model

Three tiers clearly defined in CLAUDE.md:
- **Autonomous:** bug fixes, tests, refactoring — just do it
- **Collaborative:** new features, schema changes — propose first
- **Always escalate:** blockers, gem conflicts, missing credentials

This is non-derivable and prevents both over-caution and recklessness.

---

## Croftspan as "Existing Project" Test Case

This project represents the hardest mode for the skill:
- 16 rules files (405 lines total, one at 138)
- 7 governance docs (~1,900 lines of deep reference material)
- A vault with client-specific and service-specific knowledge
- An executive advisory layer with 5 C-suite personas
- 10+ agency personas with deep voice profiles
- 24 PRs of accumulated institutional knowledge
- Multiple concerns: Rails app, agency operations, executive advisory, client delivery

What `/fury` walking into this would need to do:
1. Read everything — all rules, governance, vault structure
2. Flag the 138-line file as over cap
3. Identify derivable rules that can be let go
4. Recognize agent-specific vs interactive rules
5. See the consolidation opportunities in one-liner files
6. Acknowledge what's working — governance pointer pattern, vault, persona depth
7. Propose concrete changes without losing institutional knowledge

But this project wasn't built by `/avengers-assemble`. It grew organically. A truly new "existing project" mode needs to handle projects that have their own structure, conventions, and history — and improve them without destroying what works.

---

## Next Steps

1. Plan the croftspan-app cleanup using audit findings
2. Design the "existing project" mode for avengers-assemble based on what we learn
3. Build the mode into the skill files
4. Run `/fury` (or the new mode) on croftspan-app as the test case
