# /audit Command — Focused Parallel Auditors

**Problem:** gigo:verify runs two-stage review (spec compliance + craft quality) which catches structural issues, but misses what dedicated auditors find: security holes, leftover stubs, and code quality issues. Users report that "all checks pass" statements are nearly false 100% of the time when you run focused audits afterward.

**What it does:** A single `/audit` command that dispatches 3 parallel subagents, each with a narrow focus:

### 1. Security Audit
- Injection vulnerabilities (SQL, command, XSS)
- Auth/authz gaps
- Exposed secrets, hardcoded credentials
- OWASP top 10
- Insecure dependencies
- Missing input validation at system boundaries

### 2. Stub Check Audit
- TODO/FIXME/HACK comments
- Placeholder return values
- Hardcoded/mock data left in production code
- Empty catch blocks
- Console.log/print debugging left in
- Functions that return early with fake data
- "Not implemented" patterns

### 3. Code Quality Audit
- Dead code / unused imports
- Inconsistent patterns (mixed async styles, naming conventions)
- Missing error handling
- Test coverage gaps
- Copy-paste duplication
- Type safety issues (any types, missing null checks)

### Behavior
- All 3 agents dispatch in parallel (single message, 3 Agent tool calls)
- Each agent gets the diff or file list from the recent work (or full project if standalone)
- Each returns a findings list with file:line references and severity
- Lead consolidates into a single report grouped by severity (critical → low)
- Works standalone (`/audit`) or auto-runs after execute completes

### Design decisions to make
- New skill (`gigo:audit`) or extension of `gigo:verify`?
- Should it auto-run after execute, or always be manual?
- Does each auditor get its own prompt template in references/?
- How does it interact with the existing review-criteria.md?
- Should findings be written to a file or just presented in conversation?

### Evidence
- External user feedback: "Run separate agents for security, code quality, stub check — watch it find a list of items"
- Two-stage verify catches "did you build the right thing" and "is the work well-built" but not "is the work safe/complete/clean"
- Narrow-focus agents find more than one agent holding multiple lenses (same insight as the two-stage review finding)
