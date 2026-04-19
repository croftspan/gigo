---
id: T9-summarize-pr-description
task_type: reasoning
spec_sentence: |
  Summarize the PR description below as exactly 3 bullet points that cover: what changed, why, and one risk or follow-up. Return only the bullets.
role: |
  You are summarizing a pull-request description for a release-notes digest.
spec: |
  Here is the PR description to summarize:

  ---

  ## Rework caching layer to use a write-through pattern

  This PR replaces the lazy-fill cache in `services/catalog/cache.py` with a
  write-through design. The old layer had three recurring incidents logged in Q1:
  (a) stale cache served after admin bulk-updates because invalidation only fired
  on the API path, (b) thundering-herd on cold keys during a deploy because every
  replica raced the origin, and (c) a subtle bug where negative-result caching
  masked real 404s after a product republish.

  The new design writes the cache on every mutation through a single
  `CachedCatalog` wrapper. Reads always hit the cache and fall back to the origin
  only on a cache miss that was not itself caused by a recent delete (tracked by
  a short-lived tombstone). Thundering-herd is handled by a per-key redis lock
  with a 1s timeout — one replica fills, others wait. Tombstones are 60 seconds
  long, which should cover any reasonable republish window.

  Perf impact: benchmarked on staging, p95 read latency dropped from 48ms to 11ms
  (k=100, n=10k). Write latency went up ~3ms due to the extra cache write, which
  the product team is fine with.

  Rollout plan: ship behind `CATALOG_CACHE_V2` flag, enable in staging for a week,
  then 10% of prod, then 100%. Old layer stays in the codebase for one release
  and will be removed in the next sprint.

  Known risk: the tombstone mechanism relies on redis time. If redis clocks drift
  more than ~60s across the cluster, we could serve stale for a window. Ops
  confirmed clocks are chrony-synced within 500ms, so this is theoretical but
  worth watching.

  Tested: unit tests added for the lock path and the tombstone TTL. Integration
  test exercises the admin-bulk-update case. Manual staging soak for 3 days —
  no stale-cache reports.

  ---
acceptance: |
  - Output is exactly 3 bullet points
  - Each bullet is one sentence
  - Bullet 1 states what changed (rework / write-through / cache)
  - Bullet 2 states why (at least one of the three incidents or motivations)
  - Bullet 3 states one risk or follow-up (tombstone/clock drift, staged rollout, or old layer removal)
  - Bullets are grounded in the text — no invented numbers, no invented systems
output_format: |
  - ONLY 3 markdown bullets, one per line, starting with "- "
  - No preamble, no heading, no trailing prose
mode_hint: |
  Be concrete — name the incident or the metric when you can.
verifier: T9.py
---
