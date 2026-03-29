---
name: polish
description: "Autonomous UI polish loop — screenshots page at multiple viewports, compares against visual spec, fixes issues, re-screenshots until criteria met or 5 iterations. Internal tooling for GIGO's own site and docs."
disable-model-invocation: true
---

# Polish

Screenshot-diff-iterate loop for UI refinement. Replaces the manual "fix CSS, check browser, repeat" cycle that burned 320-minute sessions.

**This is internal tooling** for GIGO's own product site and docs. Not a public plugin skill.

---

## Before Starting

1. **Get the target.** The operator provides a URL or file path to polish.
2. **Get the spec.** Either:
   - Operator provides a visual spec inline or points to a file
   - Read `docs/gigo/ui-spec.md` if it exists
   - If no spec exists, ask: "What should this look like? Give me layout rules, breakpoints, and copy requirements — or I'll screenshot first and we'll build the spec from what's there."
3. **Branch.** If available, use worktree isolation (`isolation: "worktree"`) so failed iterations don't pollute main. If not, create a feature branch.

## The Loop

For each iteration (max 5):

### 1. Screenshot

Use Playwright MCP to capture the page at three viewports:

- **Mobile:** 375px wide (portrait phone)
- **Tablet:** 768px wide (landscape tablet)
- **Desktop:** 1440px wide (standard desktop)

```
browser_navigate → target URL
browser_resize → width, height
browser_take_screenshot → save/analyze
```

If the page is local HTML, serve it first (`python3 -m http.server`) or use a file:// URL.

### 2. Analyze

Compare each screenshot against the visual spec criteria. Check:

- **Layout:** Container widths, grid behavior, flex wrapping, element ordering
- **Spacing:** Margins, padding, gaps between elements (consistent with spec)
- **Responsiveness:** No horizontal scroll, elements reflow correctly at each breakpoint
- **Typography:** Font sizes readable (min 14px body, min 12px labels), hierarchy clear
- **Copy:** Text matches spec requirements, no orphaned words in headings
- **Interactive elements:** Hover states, focus indicators, cursor changes
- **Visual polish:** Alignment, color consistency, border radius consistency

### 3. Fix

If issues found:
- Make targeted CSS/HTML fixes — change the minimum needed to resolve the issue
- Don't refactor unrelated code during a polish pass
- Prefer CSS fixes over HTML restructuring when possible

### 4. Re-screenshot

After fixes, re-screenshot the same three viewports. Compare against the spec again.

### 5. Report or Continue

- **All criteria met:** Exit the loop. Report changes made with before/after descriptions.
- **Issues remain, iterations left:** Continue to next iteration.
- **5 iterations reached, issues remain:** Exit the loop. Report what was fixed, what remains, and why convergence failed.

---

## Convergence Criteria

The loop exits successfully when ALL of these pass at ALL three viewports:
- No horizontal scroll
- All layout rules from spec are satisfied
- Copy matches spec requirements
- No elements overlap or clip unexpectedly
- Text is readable at specified minimum sizes

## When It's Not Converging

If the same issue persists across 2+ iterations, stop and diagnose:
- Is the spec contradictory? (e.g., fixed width + no scroll at narrow viewport)
- Is the fix being overridden by another CSS rule? (specificity problem)
- Is this a fundamental layout issue that needs a structural change, not a CSS tweak?

Surface the diagnosis to the operator rather than burning more iterations.

---

## Output

When the loop completes, report:

```
## Polish Report: [page name]

**Iterations:** N of 5
**Result:** Converged | Partial (issues remaining)

### Changes Made
1. [viewport] [what changed] — [why]
2. ...

### Remaining Issues (if any)
1. [issue] — [why it didn't converge]

### Recommendations
- [anything that needs a structural change, not polish]
```

---

## References

- `references/visual-spec.md` — how to write visual specs (format, breakpoints, criteria)
- `references/screenshot-diff.md` — Playwright MCP integration details, diff strategy
