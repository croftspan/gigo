# Boundary Mismatch Patterns

A boundary mismatch is a bug where two representations of the same concept — maintained in different layers or files — disagree. Each side is correct in isolation. The bug only appears when they connect. These bugs pass build, lint, type-checking, and single-file code review. They break at runtime.

This reference defines the pattern categories and detection heuristics. Read by gigo:gigo Step 6.5 during assembly to generate project-specific review criteria.

---

## Pattern Categories

### BM-1: Shape Mismatch

**Definition:** Producer's output structure does not match consumer's expected structure.

**What to look for:** A function, API, or service returns data in one shape (e.g., wrapped in `{ data: [...] }`) while the consumer expects a different shape (e.g., unwrapped `T[]`). Type systems may mask this when generics or `any` types are involved.

**Examples:**
- Software: API returns `{ data: User[] }`, frontend destructures as `User[]` directly
- Software: CLI tool outputs JSON with a `results` wrapper, parser expects bare array
- Fiction: Character described as left-handed in chapter 3, uses right hand in chapter 12
- Research: Paper claims "significant at p<0.05" but cited study reports p=0.08

### BM-2: Convention Drift

**Definition:** Same concept named or formatted differently across layer boundaries.

**What to look for:** A field, variable, or concept uses one naming convention in its source layer and a different one where it's consumed, without a consistent transformation rule. Each layer follows its own convention correctly.

**Examples:**
- Software: Database column `user_name` (snake_case), API response field `userName` (camelCase), frontend prop `UserName` (PascalCase) — no serializer handling the transform
- Software: i18n key `error.not_found` in translation file, code references `error.notFound`
- Game design: Asset named `player_idle_01.png` in files, referenced as `playerIdle01` in code

### BM-3: Reference Mismatch

**Definition:** One layer references a path, ID, key, or name that does not exist in the target layer.

**What to look for:** A string literal or identifier in one file points to something in another file or system that has been renamed, moved, or never existed. Often caused by renaming in one place without updating references.

**Examples:**
- Software: Navigation links to `/dashboard/create`, actual page file is at `/dashboard/new`
- Software: Config key `redis.cache_ttl` referenced in code, config file has `redis.cacheTTL`
- Game design: Level data references `enemy_boss_phase2` sprite, asset folder has `boss_phase2_enemy`
- Fiction: Chapter 8 references "the letter from Madrid" — no letter scene exists

### BM-4: Contract Gap

**Definition:** A definition (state machine, interface, enum, schema) declares more states, variants, or methods than the implementation covers.

**What to look for:** A formal definition (type, enum, state diagram, interface) lists N possibilities, but the code handling those possibilities only covers N-M of them. The definition is correct; the implementation is incomplete.

**Examples:**
- Software: Enum defines `PENDING | APPROVED | REJECTED | EXPIRED`, switch statement handles 3 of 4
- Software: Interface declares 5 methods, implementing class has 4
- Game design: State machine defines transitions A→B→C→D, code implements A→B→C only
- Fiction: Outline lists 5 subplots, manuscript resolves 4

### BM-5: Temporal Shape Mismatch

**Definition:** Consumer accesses data fields from a response state that has not been reached yet.

**What to look for:** An async operation returns different shapes at different stages (e.g., `202 Accepted` with `{ status }` vs final `200 OK` with `{ status, results }`). The consumer accesses fields from the final shape on the intermediate response.

**Examples:**
- Software: Polling endpoint returns `{ status: "processing" }`, consumer accesses `response.data.failedIndices` (only present when status is "complete")
- Software: WebSocket sends partial updates during processing, handler assumes every message has the `summary` field from the final message
- Game design: Server sends `game_starting` event, client reads `scores` array (only present after `game_ended`)

### BM-6: False Positive Integration

**Definition:** A component exists and is reachable, but its actual interface does not match what callers expect.

**What to look for:** An integration test confirms "the endpoint responds" or "the component renders," but the response shape, props interface, or method signature has changed since the caller was written. Existence checks pass; behavior is wrong.

**Examples:**
- Software: API endpoint exists and returns 200, but response body changed from `{ users }` to `{ data: { users } }` — consumer gets `undefined`
- Software: React component accepts `onSubmit` prop, parent passes `onSave` — renders without error, callback never fires
- Research: Citation exists and is a real paper, but the cited claim is from a different paper

---

## Detection Heuristics

During assembly (gigo:gigo Step 6.5), use these heuristics to determine which patterns apply:

| Project has... | Check for... |
|---|---|
| API + consumer (frontend, mobile, CLI) | BM-1 (shape), BM-2 (naming), BM-6 (false positive) |
| Database + application layer | BM-2 (naming conventions across DB↔code) |
| Routing/navigation + page/view files | BM-3 (route references) |
| Config files + code that reads them | BM-3 (config key references) |
| State machines, enums, or formal interfaces | BM-4 (contract completeness) |
| Async operations (polling, webhooks, streaming) | BM-5 (temporal shapes) |
| Multi-service or microservice architecture | BM-1, BM-2, BM-6 (all cross-service boundaries) |
| i18n/localization | BM-2 (key naming), BM-3 (key existence) |
| Any multi-layer system | BM-6 (always relevant as a meta-check) |

**For non-software domains:** Identify the analogous boundaries (chapters↔character bible, rules↔implementation, claims↔citations) and map to the abstract pattern. BM-6 applies universally — "it exists" never guarantees "it connects correctly."

When generating criteria, produce 1-2 concrete, project-specific checks per relevant pattern. Use the project's actual layer names and technology (e.g., "Prisma model field names transform consistently to GraphQL response fields" not "naming is consistent").
