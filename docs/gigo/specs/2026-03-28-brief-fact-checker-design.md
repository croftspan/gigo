# Brief Fact-Checker — Design Spec

A lightweight sanity check that runs at Phase 4.25 in the blueprint pipeline — after the design brief is written but before the operator approves it. It dispatches a subagent to explore the actual project and verify the brief's factual assumptions. Not adversarial; just codebase-aware.

## Guiding Constraints

- **No new skills.** This is a new phase within `gigo:blueprint`, not a separate skill.
- **Hub-and-spoke.** SKILL.md gets a short Phase 4.25 section (~20 lines). The prompt template lives in `skills/blueprint/references/fact-checker-prompt.md`.
- **Domain-agnostic.** Works for software, novels, board games, research — any project type. No code-specific language in the prompt template.
- **Always runs.** No skip logic, no opt-out. Runs on every brief regardless of task size.
- **Not the Challenger.** Does not challenge design decisions, suggest alternatives, or run adversarial passes. Checks facts only.

---

## What It Checks

Four categories of factual mismatch between the design brief and the actual project state:

### 1. Redundancy

Does the project already contain something that does what the brief proposes? Examples:
- "You're proposing a new event system, but `pkg/events/` already implements one"
- "Chapter 3 already introduces this character — the brief treats them as new"
- "The `dice-roller` module already handles this mechanic"

### 2. Wrong Assumptions

Does the brief assume patterns, tools, structures, or conventions that don't match the project? Examples:
- "The brief assumes BoltDB, but the project uses SQLite"
- "The brief assumes first-person narration, but existing chapters use third-person"
- "The brief assumes hex-grid movement, but the game uses square grids"

### 3. Missing Dependencies

Does the brief reference things that don't exist in the project? Examples:
- "The brief references `utils/validator.go` — this file doesn't exist"
- "The brief mentions a 'reputation system' — no such system exists in the project"
- "The brief depends on a `shuffle` function in the deck module — it's not there"

### 4. Internal Consistency

Does the brief contradict itself? Examples:
- "Section 2 says the feature is read-only, but Section 4 describes write operations"
- "The timeline says Chapter 5 happens before Chapter 3's events, but the plot summary reverses this"

---

## Dispatch Pattern

### Template Location

`skills/blueprint/references/fact-checker-prompt.md`

### Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{DESIGN_BRIEF}` | Plan file contents | The full text of the design brief |
| `{PROJECT_ROOT}` | Current working directory | The project directory for the subagent to explore |

### How to Dispatch

Use the Agent tool with `subagent_type: "Plan"`. This runs inside plan mode — only `Explore` and `Plan` subagent types are available. `Plan` is preferred because it inherits the parent model (the fact-checker needs reasoning capacity to compare a design brief against project contents, not just file search). Read `references/fact-checker-prompt.md`, fill `{DESIGN_BRIEF}` and `{PROJECT_ROOT}`, pass the filled template as the agent prompt.

The subagent uses read-only tools (Glob, Grep, Read, LS) to explore the project. It does not modify anything.

---

## Output Format

The subagent returns findings in this structure:

```markdown
## Fact-Check Results

- **[Category]:** [1-2 sentence description citing specific evidence from the project]
```

Or if clean:

```markdown
## Fact-Check Results

No issues found.
```

Categories are exactly one of: `Redundancy`, `Wrong Assumption`, `Missing Dependency`, `Inconsistency`.

Each finding must cite specific evidence — a file path, a section name, a location in the project. No vague claims. Each finding should include enough context that an operator unfamiliar with the project understands why the mismatch matters, not just what mismatched.

---

## Integration Into Blueprint Pipeline

### Position

Between Phase 4 (Present Design) and Phase 4.5 (Approve Design Brief). Numbered Phase 4.25.

### Flow

1. Phase 4 completes — design brief is written to plan file
2. **Phase 4.25:** Blueprint reads `references/fact-checker-prompt.md`, fills `{DESIGN_BRIEF}` from the plan file and `{PROJECT_ROOT}` from the working directory, dispatches subagent
3. Subagent explores the project, returns findings
4. Blueprint writes findings to the plan file under a `## Fact-Check Results` section
5. If findings exist: present them to the operator with the brief. Operator decides whether to revise the design (loop back to Phase 4) or proceed to approval (Phase 4.5)
6. If no issues: note "Fact-check passed" and proceed to Phase 4.5

### SKILL.md Change

Insert `### Phase 4.25: Fact-Check Design Brief` section between Phase 4 and Phase 4.5. The section:
- States the purpose (one sentence)
- Points to `references/fact-checker-prompt.md`
- Describes how to fill and dispatch
- Says to write results to the plan file
- Describes the proceed/revise decision

Target: ~20 lines. The procedure lives in the prompt template, not in SKILL.md.

---

## The Prompt Template

`skills/blueprint/references/fact-checker-prompt.md` instructs the subagent to:

1. Read the provided design brief
2. Explore the project at `{PROJECT_ROOT}` — scan structure, read key files, understand what exists
3. Check the four categories: redundancy, wrong assumptions, missing dependencies, internal consistency
4. For each finding: state the category, describe the mismatch, cite specific evidence, explain why it matters
5. If no issues: return "No issues found."

### Prompt Constraints

The prompt explicitly tells the subagent:
- Do NOT suggest alternative designs
- Do NOT challenge whether the approach is right — that's judgment, not fact-checking
- Do NOT review quality or engineering decisions
- Do NOT act as a second planner or adversarial reviewer
- Keep findings to genuine factual mismatches, not stylistic preferences
- Use neutral, domain-agnostic language throughout

### Domain-Agnostic Language Rules

The prompt template uses:
- "project" not "codebase"
- "existing work" not "existing code"
- "project contents" not "file structure" or "source tree"
- "proposed elements" not "proposed functions/classes"
- "location references" not "file:line references"

The subagent adapts its exploration to whatever the project contains — source code, manuscripts, game rules, research notes, data files.

---

## Conventions

- **Phase announcement:** Blueprint announces "Phase 4.25: Fact-checking design brief..." before dispatching
- **Findings header:** Always `## Fact-Check Results` in the plan file
- **Category labels:** Exactly one of: `Redundancy`, `Wrong Assumption`, `Missing Dependency`, `Inconsistency`
- **Evidence requirement:** Every finding cites a specific location in the project. No vague claims.
- **Clean result:** The exact phrase "No issues found." — not variations
- **Plan file placement:** Fact-check results go at the end of the design brief, before the Post-Approval section
- **Dispatch method:** Agent tool with `subagent_type: "Plan"` (required — runs in plan mode where only Explore/Plan types are available). Do NOT use `general-purpose`, `feature-dev:code-reviewer`, `code-review:code-review`, or any other agent type.
- **Small-task note:** Phase 4.25 always runs, even on small tasks where SKILL.md's scaling section says "skip to Phase 8 after approval." The fact-check is fast on short briefs and catches the exact kind of assumptions small tasks leave unexamined. The SKILL.md scaling section should note this exception.

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `skills/blueprint/SKILL.md` | Modify | Insert Phase 4.25 section (~20 lines) between Phase 4 and Phase 4.5 |
| `skills/blueprint/references/fact-checker-prompt.md` | Create | Prompt template for the fact-checker subagent (~40-50 lines) |

Additionally, within SKILL.md:
- The **Scale to the Task** section (small tasks) should note that Phase 4.25 always runs
- The **Phase announcement** line in the SKILL.md header should include Phase 4.25

No other files are affected. The blueprint skill's frontmatter and other reference files remain unchanged.

<!-- approved: spec 2026-03-29T04:45:00 by:Eaven -->
