# Boundary-Mismatch Detection Rubric

6 seeded bugs, one per BM category. For each, the audit must identify the specific mismatch, not just mention the files.

## BM-1: Shape Mismatch
**What to detect:** `api/tasks.ts` returns `{ data: Task[], total: number }` (envelope). `hooks/useTasks.ts` expects `Task[]` (raw array via `fetchJson<Task[]>`). The hook assigns the envelope to the array state.
**Minimum evidence:** Must identify the wrapper/envelope vs direct array mismatch between API and hook.

## BM-2: Convention Drift
**What to detect:** `types.ts` uses `created_at` (snake_case). `api/tasks.ts` serializes as `createdAt` (camelCase). `hooks/useTasks.ts` accesses `task.created_at` which is undefined.
**Minimum evidence:** Must identify the snake_case/camelCase naming inconsistency across the boundary.

## BM-3: Reference Mismatch
**What to detect:** `components/Sidebar.tsx` links to `/tasks/new`. The page lives at `app/dashboard/tasks/new/page.tsx` → URL `/dashboard/tasks/new`.
**Minimum evidence:** Must identify the navigation path mismatch between the link and the actual page route.

## BM-4: Contract Gap
**What to detect:** `models/task-status.ts` defines transitions for all 5 statuses including `paused→active` and `completed→archived`. `models/task-service.ts` only implements transitions from `draft` and `active`.
**Minimum evidence:** Must identify that the service doesn't implement all transitions defined in the status model.

## BM-5: Temporal Shape Mismatch
**What to detect:** `api/projects.ts` POST returns `{ id, status: 'creating' }`. `hooks/useProjects.ts` accesses `response.memberCount` immediately — a field not present until status is `'ready'`.
**Minimum evidence:** Must identify that the hook accesses a field that doesn't exist in the creation response.

## BM-6: False Positive Integration
**What to detect:** `api/tasks.ts` DELETE returns `{ deleted: true }`. `hooks/useTasks.ts` expects `{ task: Task }` from the DELETE response for undo functionality.
**Minimum evidence:** Must identify that the DELETE response shape doesn't match what the hook expects.
