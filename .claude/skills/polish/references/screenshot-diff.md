# Playwright MCP Integration — Screenshot & Diff

How the `/polish` skill uses the Playwright MCP tools for the screenshot-diff-iterate loop.

## Screenshot Workflow

### 1. Navigate to Target

```
browser_navigate(url: "http://localhost:8000/index.html")
```

For local files, start a server first:
```bash
cd <directory> && python3 -m http.server 8000 &
```

### 2. Resize for Each Viewport

Three captures per iteration:

```
browser_resize(width: 375, height: 812)    # Mobile (iPhone SE)
browser_take_screenshot()                    # Capture mobile

browser_resize(width: 768, height: 1024)   # Tablet (iPad)
browser_take_screenshot()                    # Capture tablet

browser_resize(width: 1440, height: 900)   # Desktop
browser_take_screenshot()                    # Capture desktop
```

### 3. Analyze Screenshots

After each screenshot, analyze the visual output against the spec criteria. Use `browser_snapshot` for DOM-level inspection when the screenshot isn't sufficient (e.g., checking actual computed font sizes, exact widths, overflow state).

```
browser_snapshot()  # Returns accessibility tree with element dimensions
```

## Diff Strategy

The diff is **spec-driven**, not pixel-driven. For each spec criterion:

1. **Check the criterion** against the screenshot/snapshot
2. **Pass or fail** — binary, no partial credit
3. **If fail:** describe the specific deviation (e.g., "stat cards overflow container at 375px, causing horizontal scroll")
4. **Prioritize:** layout breaks > readability issues > spacing polish > minor alignment

Don't chase pixel-perfection. Chase spec compliance.

## Fixing Issues

After identifying issues:

1. Read the relevant CSS/HTML files
2. Make the minimum change to fix the issue
3. Avoid side effects — check that fixes at one viewport don't break another
4. Re-screenshot all three viewports after fixes (not just the one you fixed)

## Loop Termination

**Exit successfully** when all spec criteria pass at all three viewports.

**Exit with report** after 5 iterations if issues remain. Common reasons for non-convergence:

- **Specificity wars:** A fix is overridden by a more specific selector. Solution: inspect with `browser_snapshot`, find the conflicting rule.
- **Contradictory spec:** The spec asks for incompatible things (e.g., fixed 800px container + no scroll at 375px without responsive override). Solution: surface to operator.
- **Structural issue:** The HTML structure doesn't support the desired layout. CSS can't fix this — needs restructuring. Solution: recommend to operator, don't attempt in polish loop.

## Tips

- `browser_snapshot` is more reliable than screenshots for checking computed values
- If checking hover states, use `browser_hover(element: "selector")` before screenshotting
- For pages with animations, use `browser_wait_for(time: 1000)` to let transitions settle
- Use `browser_console_messages` to check for JS errors that might affect layout
