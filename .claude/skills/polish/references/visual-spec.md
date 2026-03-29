# Visual Spec Format

A visual spec defines what a page should look like at each viewport. The `/polish` skill reads this spec and iterates until the page matches.

## Format

```markdown
## Visual Spec: [Page Name]

### Target
- URL or file path: [target]
- Serve locally: yes/no (if local HTML, polish will start a server)

### Layout
- Container: [max-width, alignment]
- Grid/flex behavior: [how elements arrange]
- Key elements: [list elements and their expected positions]

### Breakpoints
- Mobile (≤375px): [layout at this size]
- Tablet (≤768px): [layout at this size]
- Desktop (≥1024px): [layout at this size]

### Typography
- Body: [min size, font family]
- Headings: [hierarchy, sizes]
- Labels/captions: [min size]

### Copy Requirements
- [exact text requirements, tone rules, no-orphan rules]

### Quality Bars
- No horizontal scroll at any viewport
- All interactive elements have visible hover/focus states
- Text readable at min sizes specified above
- [project-specific bars]

### Acceptance Criteria (optional)
- [specific measurable criteria that define "done"]
```

## Example

```markdown
## Visual Spec: GIGO Product Site

### Target
- URL: file://docs/site/index.html
- Serve locally: yes

### Layout
- Container: max-width 800px, centered
- Stats row: flex, wrap on mobile, centered
- Nav TOC: flex-wrap, 8px gap, white background

### Breakpoints
- Mobile (≤375px): single column, stats stack vertically, nav wraps
- Tablet (≤768px): charts 1-column, stats 2-per-row
- Desktop (≥1024px): charts 2-column grid, stats row

### Typography
- Body: 14px Inter, line-height 1.65
- Headings: 20px semibold (h2), 15px semibold (h3)
- Labels: 11px uppercase, #64748b

### Copy Requirements
- Headline: "Claude Code Insights"
- No orphaned single words in headings
- Stats labels: uppercase, abbreviated

### Quality Bars
- No horizontal scroll at any viewport
- Stat cards don't overlap or clip
- Chart bars align with labels
- All text readable without zooming
```

## Tips

- Be specific about numbers (px values, colors) — vague specs produce vague iterations
- If you don't have a design system, at least specify min font sizes and max container widths
- The spec doesn't need to be perfect before starting — the loop will surface gaps
- If the operator provides inline instructions instead of a spec file, convert them to this format before starting the loop
