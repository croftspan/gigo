# Eval Results: Assembled vs Bare

Run: 2026-03-26-131429

## rails-api

- Assembled won: 44 / 50 (88%)
- Tied: 5
- Assembled lost: 1

## childrens-novel

- Assembled won: 43 / 50 (86%)
- Tied: 6
- Assembled lost: 1

## Combined

- Assembled won: 87 / 100 (87%)
- Tied: 11
- Assembled lost: 2

## Interpretation

Context is working. Assembled context wins 87% of criteria across both domains. The assembled team actively enforces quality bars, adopts persona voice, and routes through domain expertise. Phase 2 (active routing) may not be needed — the passive context is already highly effective.

## Notable Observations

- **Quality bar enforcement is the strongest signal.** The assembled version catches N+1 queries, pushes back on skipping tests, flags table-locking migrations, rejects deus ex machina, and enforces clue-pacing rules. The bare version rarely pushes back.
- **Persona voice is clearly different.** The assembled version references named authorities, applies specific philosophies, and speaks with the persona's perspective. The bare version gives generic Claude advice.
- **Specificity is near-perfect.** The assembled version references project-specific rules, anti-patterns, and quality bars by name. The bare version works from general knowledge only.
- **The 2 losses and 11 ties are on knowledge-retrieval tasks** — consistent with Hu et al. (2026) finding that persona context can slightly degrade factual tasks.

## Methodology

- 20 prompts (10 per domain) across 3 axes: quality bars (A), persona voice (B), routing (C)
- Each prompt run twice: bare (temp dir, no CLAUDE.md/.claude/) and assembled (temp dir with full context)
- LLM-as-judge with blinded randomized A/B ordering
- 5 scoring criteria per prompt (quality bar, persona voice, routing, specificity, pushback)
- Scored 0-3 per criteria with winner noted
