# Defect Manifest — Integration API Fixture

This file documents the 6 seeded boundary-mismatch bugs planted in this fixture.
**DO NOT include this file when running evaluations.** It is the answer key.

## BM-1: Shape Mismatch — API Envelope vs Direct Array

**Files:** `src/api/tasks.ts` (line ~13-25), `src/hooks/useTasks.ts` (line ~16)
**Bug:** `api/tasks.ts` `getTasks()` returns `{ data: Task[], total: number }` (an envelope).
`hooks/useTasks.ts` calls `fetchJson<Task[]>(...)` — expects a raw `Task[]`, not an envelope.
**Runtime effect:** `tasks` state gets set to the envelope object, not the array. `.sort()` call on line ~22 throws "tasks.sort is not a function".

## BM-2: Convention Drift — snake_case Type vs camelCase API

**Files:** `src/types.ts` (line ~10), `src/api/tasks.ts` (line ~20), `src/hooks/useTasks.ts` (line ~23)
**Bug:** `types.ts` defines `Task.created_at` (snake_case). `api/tasks.ts` serializes as `createdAt` (camelCase). `hooks/useTasks.ts` sorts by `task.created_at` — which is `undefined` because the API sent `createdAt`.
**Runtime effect:** Sort comparison uses `undefined`, all dates become `NaN`, sort order is arbitrary.

## BM-3: Reference Mismatch — Wrong Navigation Path

**Files:** `src/components/Sidebar.tsx` (line ~13), `src/app/dashboard/tasks/new/page.tsx`
**Bug:** Sidebar links to `href="/tasks/new"`. The actual page lives at `app/dashboard/tasks/new/page.tsx`, which maps to URL `/dashboard/tasks/new`.
**Runtime effect:** Clicking "New Task" navigates to `/tasks/new` — a 404 page.

## BM-4: Contract Gap — Incomplete State Machine

**Files:** `src/models/task-status.ts` (line ~3-8), `src/models/task-service.ts` (line ~7-20)
**Bug:** `task-status.ts` defines 5 statuses and a `VALID_TRANSITIONS` map showing `paused→active` and `completed→archived` as valid. `task-service.ts` only implements transitions from `draft` and `active` — the `default` case throws for any other current status.
**Runtime effect:** Calling `transition(id, 'active')` on a paused task throws `InvalidTransitionError` even though the status model says it's valid.

## BM-5: Temporal Shape Mismatch — Accessing Future Fields

**Files:** `src/api/projects.ts` (line ~6-14), `src/hooks/useProjects.ts` (line ~19-24)
**Bug:** `api/projects.ts` `createProject()` returns `{ id, status: 'creating' }` (202 response). `hooks/useProjects.ts` immediately accesses `response.memberCount` — a field that only exists on the full `Project` type returned by `getProject()` when status is `'ready'`.
**Runtime effect:** `newProject.memberCount` is `undefined`. UI shows "undefined members" or `NaN` if used in calculations.

## BM-6: False Positive Integration — Wrong Response Shape

**Files:** `src/api/tasks.ts` (line ~38-41), `src/hooks/useTasks.ts` (line ~26-30)
**Bug:** `api/tasks.ts` `deleteTask()` returns `{ deleted: true }`. `hooks/useTasks.ts` `deleteTask` callback calls `fetchJson<{ task: Task }>(...)` and returns `response.task` for undo functionality.
**Runtime effect:** `response.task` is `undefined`. Undo feature silently fails — no error thrown, but the deleted task data is lost.
