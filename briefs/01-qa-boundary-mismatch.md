# Brief: QA Boundary-Mismatch Taxonomy

## Origin

Competitive analysis of [revfactory/harness](https://github.com/revfactory/harness). Their `references/qa-agent-guide.md` contains a battle-tested taxonomy of integration bugs that static analysis misses — extracted from real project failures (SatangSlide). This is exactly the kind of non-derivable, hard-won knowledge GIGO's review pipeline should encode.

## What to Build

A reference file (`.claude/references/boundary-mismatch-patterns.md` or similar) that feeds into `gigo:verify` and `gigo:sweep` review criteria. Not a copy of Harness's guide — a GIGO-native version that fits our two-stage review pipeline and works across domains (not just Next.js/TypeScript).

## Key Patterns from Harness Worth Generalizing

1. **API response shape vs consumer type** — backend returns `{ data: [...] }`, frontend expects `T[]` directly. TypeScript generics mask this at compile time.
2. **Naming convention drift across boundaries** — `snake_case` in DB, `camelCase` in API, mismatch in frontend types. Each layer "correct" in isolation.
3. **File/route path vs link href** — page exists at `/dashboard/create`, link points to `/create`. File system and routing are separate namespaces nobody cross-checks.
4. **State machine completeness** — transition map defines `A → B → C`, code only implements `A → B`. Map exists, implementation is partial.
5. **Sync vs async response shape** — API returns `202 Accepted` with `{ status }`, consumer accesses `data.failedIndices` that only exists in the final async result.
6. **Existence vs connection** — "Does the API exist?" passes. "Does the API's response match what calls it?" fails. Most reviews check the former.

## Where It Lands in GIGO

- **Primary:** `gigo:verify` — the craft review stage should check boundary coherence, not just internal code quality. May need a new review criteria category or additions to `.claude/references/review-criteria.md` generation.
- **Secondary:** `gigo:sweep` — the quality auditor prompt could include boundary-mismatch checks. Cross-file coherence is exactly what single-file review misses.
- **Tertiary:** `gigo:spec` — planning should identify integration boundaries upfront so the execute phase can flag them for review.

## Constraints

- Must be domain-generalizable. Harness's guide is Next.js/TypeScript specific. GIGO serves any domain — the patterns should be expressed as abstract boundary types (API↔consumer, state-definition↔state-mutation, path-declaration↔path-reference) with domain-specific examples.
- Must fit the token economics. This is reference-tier content (loaded on demand), not rules-tier. No always-on cost.
- Must integrate with existing review criteria generation. `gigo:gigo` Step 6.5 already generates `review-criteria.md` from persona quality bars. Boundary-mismatch checks should either extend that generation or be a separate reference that review prompts pull from.
- Don't duplicate what linters/compilers already catch. Focus on the gaps — the things that pass `tsc`, pass `eslint`, pass `build`, but break at runtime.

## Open Questions

- Should boundary-mismatch checking be opt-in (only for projects with integration layers) or always-on in the review pipeline?
- Does `gigo:sweep` need a fourth auditor (integration auditor) alongside security, stubs, and quality? Or do boundary checks fold into the existing quality auditor?
- How do we detect which boundary types are relevant to a given project? (e.g., no API↔frontend checks for a CLI tool)
