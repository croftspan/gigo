# Feature Validation Suite — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-04-12-feature-validation-suite-design.md`

**Goal:** Build an automated test suite that validates 4 shipped features (boundary-mismatch detection, execution pattern catalog, phase selection matrix, Agent Teams cleanup) and runs a regression check against the existing eval baseline.

**Architecture:** Extends `evals/` with a new `validation/` directory for feature-specific tests and a new `fixtures/integration-api/` directory for seeded-defect testing. Each test script runs `claude -p` against a fixture, pipes output through an LLM judge, and reports pass/fail. The master runner aggregates all results.

**Tech Stack:** Bash scripts, Claude CLI (`claude -p`), JSON output parsing with `jq`

---

### Task 1: Fixture Source Files — Types and API Layer

**blocks:** 3, 4, 7
**blocked-by:** []
**parallelizable:** true (with Task 2)

**Files:**
- Create: `evals/fixtures/integration-api/src/types.ts`
- Create: `evals/fixtures/integration-api/src/api/tasks.ts`
- Create: `evals/fixtures/integration-api/src/api/projects.ts`

- [x] **Step 1: Create shared types**

Write `evals/fixtures/integration-api/src/types.ts` — the shared type definitions. Note: `created_at` is snake_case here (BM-2 setup — API will serialize as camelCase).

```typescript
export type TaskStatus = 'draft' | 'active' | 'paused' | 'completed' | 'archived';

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  project_id: string;
  assignee_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  status: 'creating' | 'ready' | 'archived';
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  total: number;
}

export interface PaginationParams {
  page: number;
  limit: number;
}
```

- [x] **Step 2: Create tasks API**

Write `evals/fixtures/integration-api/src/api/tasks.ts`. Contains BM-1 (returns envelope `{ data, total }`), BM-2 (serializes `createdAt` camelCase), and BM-6 (DELETE returns `{ deleted: true }` not the task object).

```typescript
import { Task, ApiResponse, PaginationParams } from '../types';

export async function getTasks(params: PaginationParams): Promise<ApiResponse<Task[]>> {
  const response = await fetch(`/api/tasks?page=${params.page}&limit=${params.limit}`);
  const tasks = await db.tasks.findMany({
    skip: (params.page - 1) * params.limit,
    take: params.limit,
  });
  const total = await db.tasks.count();

  return {
    data: tasks.map(task => ({
      id: task.id,
      title: task.title,
      description: task.description,
      status: task.status,
      project_id: task.project_id,
      assignee_id: task.assignee_id,
      createdAt: task.created_at,
      updatedAt: task.updated_at,
    })),
    total,
  };
}

export async function getTask(id: string): Promise<Task> {
  const task = await db.tasks.findUnique({ where: { id } });
  if (!task) throw new NotFoundError('Task not found');

  return {
    id: task.id,
    title: task.title,
    description: task.description,
    status: task.status,
    project_id: task.project_id,
    assignee_id: task.assignee_id,
    createdAt: task.created_at,
    updatedAt: task.updated_at,
  };
}

export async function createTask(data: {
  title: string;
  description: string;
  project_id: string;
}): Promise<Task> {
  const task = await db.tasks.create({
    data: { ...data, status: 'draft' },
  });
  return task;
}

export async function deleteTask(id: string): Promise<{ deleted: boolean }> {
  await db.tasks.delete({ where: { id } });
  return { deleted: true };
}
```

- [x] **Step 3: Create projects API**

Write `evals/fixtures/integration-api/src/api/projects.ts`. Contains BM-5 (POST returns 202 with `{ id, status: 'creating' }` — no `memberCount` field until status is `ready`).

```typescript
import { Project } from '../types';

export async function createProject(data: {
  name: string;
  description: string;
}): Promise<{ id: string; status: 'creating' }> {
  const project = await db.projects.create({
    data: { ...data, status: 'creating', memberCount: 0 },
  });

  backgroundQueue.enqueue('project:setup', { projectId: project.id });

  return {
    id: project.id,
    status: 'creating',
  };
}

export async function getProject(id: string): Promise<Project> {
  const project = await db.projects.findUnique({ where: { id } });
  if (!project) throw new NotFoundError('Project not found');

  return {
    id: project.id,
    name: project.name,
    description: project.description,
    memberCount: project.memberCount,
    status: project.status,
    created_at: project.created_at,
  };
}

export async function listProjects(): Promise<Project[]> {
  return db.projects.findMany({ orderBy: { created_at: 'desc' } });
}
```

- [x] **Step 4: Commit**

```bash
git add evals/fixtures/integration-api/src/types.ts \
        evals/fixtures/integration-api/src/api/tasks.ts \
        evals/fixtures/integration-api/src/api/projects.ts
git commit -m "evals: add integration-api fixture — types and API layer"
```

---

### Task 2: Fixture Source Files — Hooks, Components, Models

**blocks:** 3, 4, 7
**blocked-by:** []
**parallelizable:** true (with Task 1)

**Files:**
- Create: `evals/fixtures/integration-api/src/hooks/useTasks.ts`
- Create: `evals/fixtures/integration-api/src/hooks/useProjects.ts`
- Create: `evals/fixtures/integration-api/src/components/Sidebar.tsx`
- Create: `evals/fixtures/integration-api/src/app/dashboard/tasks/new/page.tsx`
- Create: `evals/fixtures/integration-api/src/models/task-status.ts`
- Create: `evals/fixtures/integration-api/src/models/task-service.ts`

- [x] **Step 1: Create useTasks hook**

Write `evals/fixtures/integration-api/src/hooks/useTasks.ts`. Contains consumer side of BM-1 (expects `Task[]` not envelope), BM-2 (accesses `task.created_at` but API sends `createdAt`), and BM-6 (accesses `response.task` after DELETE but API returns `{ deleted: true }`).

```typescript
import { useState, useEffect, useCallback } from 'react';
import { Task } from '../types';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export function useTasks(page: number = 1, limit: number = 25) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchJson<Task[]>(`/api/tasks?page=${page}&limit=${limit}`)
      .then(data => {
        setTasks(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err);
        setLoading(false);
      });
  }, [page, limit]);

  const sortedTasks = tasks.sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const deleteTask = useCallback(async (id: string) => {
    const response = await fetchJson<{ task: Task }>(`/api/tasks/${id}`, {
      method: 'DELETE',
    });
    setTasks(prev => prev.filter(t => t.id !== id));
    return response.task;
  }, []);

  return { tasks: sortedTasks, loading, error, deleteTask };
}
```

- [x] **Step 2: Create useProjects hook**

Write `evals/fixtures/integration-api/src/hooks/useProjects.ts`. Contains consumer side of BM-5 (immediately accesses `response.memberCount` after POST, but POST only returns `{ id, status: 'creating' }`).

```typescript
import { useState, useCallback } from 'react';
import { Project } from '../types';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  const createProject = useCallback(async (data: { name: string; description: string }) => {
    const response = await fetchJson<Project>('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    const newProject: Project = {
      id: response.id,
      name: data.name,
      description: data.description,
      memberCount: response.memberCount,
      status: response.status,
      created_at: new Date().toISOString(),
    };

    setProjects(prev => [newProject, ...prev]);
    return newProject;
  }, []);

  return { projects, loading, createProject };
}
```

- [x] **Step 3: Create Sidebar component**

Write `evals/fixtures/integration-api/src/components/Sidebar.tsx`. Contains BM-3 (links to `/tasks/new` but the actual page is at `/dashboard/tasks/new`).

```tsx
import React from 'react';
import Link from 'next/link';

interface SidebarProps {
  currentPath: string;
}

export function Sidebar({ currentPath }: SidebarProps) {
  const links = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/dashboard/tasks', label: 'Tasks' },
    { href: '/tasks/new', label: 'New Task' },
    { href: '/dashboard/projects', label: 'Projects' },
  ];

  return (
    <nav className="sidebar">
      <ul>
        {links.map(link => (
          <li key={link.href}>
            <Link
              href={link.href}
              className={currentPath === link.href ? 'active' : ''}
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

- [x] **Step 4: Create task creation page**

Write `evals/fixtures/integration-api/src/app/dashboard/tasks/new/page.tsx`. The actual page route — URL is `/dashboard/tasks/new`, not `/tasks/new` (BM-3 target).

```tsx
'use client';

import React, { useState } from 'react';
import { Sidebar } from '../../../../components/Sidebar';

export default function NewTaskPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, project_id: 'default' }),
    });
  };

  return (
    <div className="layout">
      <Sidebar currentPath="/dashboard/tasks/new" />
      <main>
        <h1>Create New Task</h1>
        <form onSubmit={handleSubmit}>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Task title" />
          <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" />
          <button type="submit">Create Task</button>
        </form>
      </main>
    </div>
  );
}
```

- [x] **Step 5: Create status model and service**

Write `evals/fixtures/integration-api/src/models/task-status.ts`. Defines 5 statuses and the transition map (BM-4 setup).

```typescript
export type TaskStatus = 'draft' | 'active' | 'paused' | 'completed' | 'archived';

export const VALID_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  draft: ['active'],
  active: ['paused', 'completed'],
  paused: ['active'],
  completed: ['archived'],
  archived: [],
};

export function canTransition(from: TaskStatus, to: TaskStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}
```

Write `evals/fixtures/integration-api/src/models/task-service.ts`. Contains BM-4 (only implements 3 of the 5 defined transitions: `draft→active`, `active→completed`, `active→paused`). Missing: `paused→active`, `completed→archived`.

```typescript
import { TaskStatus } from './task-status';

export class TaskService {
  async transition(taskId: string, newStatus: TaskStatus): Promise<void> {
    const task = await db.tasks.findUnique({ where: { id: taskId } });
    if (!task) throw new NotFoundError('Task not found');

    switch (task.status) {
      case 'draft':
        if (newStatus !== 'active') {
          throw new InvalidTransitionError(task.status, newStatus);
        }
        break;
      case 'active':
        if (newStatus !== 'completed' && newStatus !== 'paused') {
          throw new InvalidTransitionError(task.status, newStatus);
        }
        break;
      default:
        throw new InvalidTransitionError(task.status, newStatus);
    }

    await db.tasks.update({
      where: { id: taskId },
      data: { status: newStatus, updated_at: new Date().toISOString() },
    });
  }
}
```

- [x] **Step 6: Commit**

```bash
git add evals/fixtures/integration-api/src/hooks/ \
        evals/fixtures/integration-api/src/components/ \
        evals/fixtures/integration-api/src/app/ \
        evals/fixtures/integration-api/src/models/
git commit -m "evals: add integration-api fixture — hooks, components, models"
```

---

### Task 3: Fixture Assembly Files

**blocks:** 7
**blocked-by:** 1, 2
**parallelizable:** false

**Files:**
- Create: `evals/fixtures/integration-api/CLAUDE.md`
- Create: `evals/fixtures/integration-api/.claude/rules/standards.md`
- Create: `evals/fixtures/integration-api/.claude/rules/workflow.md`
- Create: `evals/fixtures/integration-api/.claude/rules/snap.md`
- Create: `evals/fixtures/integration-api/.claude/references/review-criteria.md`
- Create: `evals/fixtures/integration-api/.claude/references/integration-patterns.md`
- Create: `evals/fixtures/integration-api/DEFECT-MANIFEST.md`

- [x] **Step 1: Create CLAUDE.md**

Write `evals/fixtures/integration-api/CLAUDE.md`. 3 personas following existing fixture pattern (~62 lines).

```markdown
# TaskFlow — TypeScript Full-Stack Task Management

A Next.js app with typed API routes, React hooks, and a status-driven task model. TypeScript throughout.

## The Team

### Schema — The Integration Architect

**Modeled after:** Tanner Linsley's type-safe pragmatism — every API contract is a typed promise to the consumer
+ Kent C. Dodds's testing-trophy approach — integration tests over unit tests when boundaries matter most
+ Sandi Metz's interface clarity — if the consumer can misuse it, the interface is wrong.

- **Owns:** API contracts, type definitions, data flow across boundaries, serialization consistency
- **Quality bar:** Every API response shape matches its consumer's type expectation. Every naming convention is consistent or explicitly transformed at the boundary.
- **Won't do:** Implicit type coercion, untyped API responses, naming conventions that drift silently between layers

### Stack — The Frontend Engineer

**Modeled after:** Dan Abramov's composition-first approach — hooks compose, components render, neither does the other's job
+ Ryan Florence's route-centric thinking — the URL is the source of truth for what the user sees
+ Tanner Linsley's data-fetching patterns — every async operation has loading, error, and success states.

- **Owns:** Hooks, components, routing, state management, data-fetching lifecycle
- **Quality bar:** Every hook correctly handles loading, error, and success states. Every navigation link resolves to an actual page route.
- **Won't do:** Hooks that ignore error states, navigation links that assume route structure, components that fetch data directly

### Hawkeye — The Overwatch

**Modeled after:** Clint Barton's "I see better from a distance" detachment — step back from the work to see what's actually there
+ Nassim Taleb's via negativa — value comes from removing bullshit, not adding polish
+ Daniel Kahneman's pre-mortem technique — assume the output failed, then find why.

- **Owns:** Output verification, drift detection, quality-bar enforcement audit
- **Quality bar:** Every response survives the question "did you actually do what you claimed?"
- **Won't do:** Let persona language substitute for substance, let generic answers wear domain costumes, let references go unread

## Autonomy Model

- **Reading and exploring:** Full autonomy. Read any file.
- **Writing tests:** Full autonomy.
- **Modifying source code:** Propose changes with rationale. Wait for approval.
- **Deploying or committing:** Always ask first.

## Quick Reference

- **Type safety:** Every API response has a corresponding TypeScript type used by its consumer.
- **Naming consistency:** Pick snake_case or camelCase per layer, transform explicitly at boundaries.
- **Route integrity:** Every navigation link resolves to an actual page file.
- **Status completeness:** Every status in the model has transition logic in the service.
- **Line cap:** ~60 lines per rules file. Deep patterns go in `.claude/references/`.
```

- [x] **Step 2: Create rules files**

Write `evals/fixtures/integration-api/.claude/rules/standards.md`:

```markdown
# Standards — TaskFlow

## Quality Gates

- Every API endpoint's response type matches the type its consumer uses. No implicit shape assumptions.
- Naming conventions are consistent within a layer. Cross-layer transformations are explicit.
- Every navigation link resolves to an actual page route in the app directory.
- Every status defined in the model has transition logic in the service layer.
- Every hook handles loading, error, and success states for its API calls.

## Anti-Patterns

- **Untyped API responses.** `fetch(...).then(r => r.json())` without type validation is a runtime bug waiting to happen.
- **Silent naming drift.** `created_at` in the DB, `createdAt` in the API, `created_at` in the hook — pick one or transform explicitly.
- **Dead navigation links.** Links that point to routes that don't exist in the app directory.
- **Partial state machines.** Defining statuses without implementing all their transitions.

## When to Go Deeper

When reviewing cross-boundary data flow, read `.claude/references/review-criteria.md`.
When reviewing integration patterns, read `.claude/references/integration-patterns.md`.
```

Write `evals/fixtures/integration-api/.claude/rules/workflow.md`:

```markdown
# Workflow — TaskFlow

## The Loop

1. **Understand the ask.** Read the request. If unclear, ask one targeted question.
2. **Check boundaries first.** Before writing code, trace the data flow across layers. Does the API shape match the consumer's type? Does the naming stay consistent?
3. **Write the test first.** Cover the happy path and at least one error path.
4. **Implement.** Minimum code to pass the test.
5. **Verify.** Check cross-boundary coherence, not just single-file correctness.

## Overwatch

Before finalizing any response, step back and verify:
- Did you actually apply the quality bars you cited, or just name-drop them?
- Does your response address what was asked, or did you drift?
- Would removing the persona language change your answer? If not, the persona added nothing.
- Did you check the references you were told to check, or skip them?
```

Write `evals/fixtures/integration-api/.claude/rules/snap.md` — copy from the existing rails-api fixture's snap.md (already read in system context, same content applies).

- [x] **Step 3: Create reference files**

Write `evals/fixtures/integration-api/.claude/references/review-criteria.md`:

```markdown
## Spec Compliance Criteria

- Does every API endpoint's response shape match the type used by its consuming hook?
- Does every navigation link resolve to an actual page route?
- Does the status model's transition function handle all defined status values?

## Craft Review Criteria

- Are naming conventions consistent across type definitions, API serialization, and hook access patterns?
- Do hooks handle async responses at each lifecycle stage (pending, processing, ready) rather than assuming the final shape?
- When an API endpoint changes its response shape, are all consumers updated to match?
- Are type generics (fetchJson<T>) validated against actual API response structures, not assumed?
```

Write `evals/fixtures/integration-api/.claude/references/integration-patterns.md`:

```markdown
# Integration Patterns — TaskFlow

## Cross-Boundary Data Flow

Data flows through three layers: database → API → frontend hooks → components.

Each boundary is a potential mismatch point:
- **DB → API:** Field naming (snake_case to camelCase), response wrapping (raw vs envelope)
- **API → Hooks:** Response shape (what the API returns vs what the hook's generic type expects)
- **Hooks → Components:** Data availability (async fields that aren't populated yet)

## Async Response Lifecycle

API endpoints may return different shapes at different lifecycle stages:
- **Synchronous endpoints** (GET, DELETE): Response shape is fixed
- **Asynchronous endpoints** (POST that triggers background work): Initial response has a subset of fields. Full object available only after background processing completes.

Consumers must handle the lifecycle stage they're in, not assume the final shape.

## Status Machine Completeness

When a model defines N statuses, the service layer must handle transitions for all N statuses. A status that exists in the type but has no transition logic is a contract gap — code that tries to transition through it will fail at runtime.
```

- [x] **Step 4: Create DEFECT-MANIFEST.md**

Write `evals/fixtures/integration-api/DEFECT-MANIFEST.md`. This file is the test key — excluded from Claude's context during testing.

```markdown
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
```

- [x] **Step 5: Commit**

```bash
git add evals/fixtures/integration-api/CLAUDE.md \
        evals/fixtures/integration-api/.claude/ \
        evals/fixtures/integration-api/DEFECT-MANIFEST.md
git commit -m "evals: add integration-api fixture — assembly and defect manifest"
```

---

### Task 4: Judge Prompts and Rubric

**blocks:** 7, 8, 9
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2, 5)

**Files:**
- Create: `evals/validation/boundary-judge.md`
- Create: `evals/validation/boundary-mismatch-rubric.md`
- Create: `evals/validation/pattern-judge.md`
- Create: `evals/validation/matrix-judge.md`

- [x] **Step 1: Create boundary-mismatch judge prompt**

Write `evals/validation/boundary-judge.md`:

```markdown
# Boundary-Mismatch Detection Judge

You are scoring whether an integration audit identified specific known bugs in a codebase.

## The Audit Output

{AUDIT_OUTPUT}

## The Defect Manifest

{DEFECT_MANIFEST}

## Your Job

For each of the 6 defects listed in the Defect Manifest, determine whether the audit output identified that specific bug.

**Score YES if:**
- The audit describes the same mismatch (matching on concept, not exact wording)
- The audit identifies the correct files involved
- The audit explains why it would fail at runtime

**Score NO if:**
- The audit does not mention this bug at all
- The audit describes something different in the same files
- The audit mentions the files but misidentifies the actual mismatch

## Output

Respond with ONLY a JSON array. No other text, no markdown fences.

[
  { "defect": "BM-1", "detected": true, "evidence": "The audit noted that the API returns a wrapper object with data and total fields while the hook expects a direct array" },
  { "defect": "BM-2", "detected": false, "evidence": "" },
  { "defect": "BM-3", "detected": true, "evidence": "..." },
  { "defect": "BM-4", "detected": true, "evidence": "..." },
  { "defect": "BM-5", "detected": false, "evidence": "" },
  { "defect": "BM-6", "detected": true, "evidence": "..." }
]
```

- [x] **Step 2: Create boundary-mismatch rubric**

Write `evals/validation/boundary-mismatch-rubric.md`. This is the defect manifest reformatted for the judge — the content matches Task 3's DEFECT-MANIFEST.md but is structured as a rubric for scoring.

```markdown
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
```

- [x] **Step 3: Create execution pattern judge prompt**

Write `evals/validation/pattern-judge.md`:

```markdown
# Execution Pattern Judge

You are scoring whether a plan correctly identifies and applies an execution pattern.

## The Plan Output

{PLAN_OUTPUT}

## Expected Pattern

{EXPECTED_PATTERN}

## Your Job

Determine whether the plan uses the correct execution pattern for the task.

**Score YES if the plan:**
- Explicitly names the correct pattern (e.g., "Pipeline", "Fan-out/Fan-in", "Producer-Reviewer"), OR
- Describes the correct structure without naming it:
  - Pipeline: tasks run sequentially, each consuming the previous step's output
  - Fan-out/Fan-in: independent tasks run in parallel, results merged afterward
  - Producer-Reviewer: one phase generates output, a separate independent phase reviews/validates it

**Score NO if:**
- The plan uses a different execution shape (e.g., parallelizes a Pipeline task, serializes a Fan-out task)
- The plan ignores execution structure entirely (just lists steps without addressing dependencies)
- The plan defaults to generic sequential ordering without acknowledging the task's dependency shape

## Output

Respond with ONLY a JSON object. No other text, no markdown fences.

{ "pattern": "Pipeline", "correct": true, "evidence": "The plan describes sequential execution where each step depends on the previous step's output" }
```

- [x] **Step 4: Create phase selection matrix judge prompt**

Write `evals/validation/matrix-judge.md`:

```markdown
# Phase Selection Matrix Judge

You are scoring whether a response correctly identifies downstream effects of adding a new persona to a GIGO-assembled project.

## The Response

{RESPONSE}

## Expected Downstream Effects

5 effects that should be identified:

1. **review-criteria.md regeneration** — New quality bars about auth/SQL/input validation should become review criteria
2. **Rules line budget check** — Adding persona content may push rules files toward the ~60-line cap
3. **Snap audit updates** — Coverage check now includes security domain, calibration check covers one more persona
4. **New reference file** — Deep security knowledge (patterns, checklists) should go in a reference file, not rules
5. **Workflow "When to Go Deeper" pointer** — May need a pointer for security-related reviews

## Your Job

For each of the 5 expected effects, determine whether the response identifies it.

**Score YES if:**
- The response describes the same downstream effect (matching on concept, not exact wording)
- The response identifies the correct file or area that needs updating

**Score NO if:**
- The response does not mention this effect
- The response mentions the file but for a different reason

## Output

Respond with ONLY a JSON array. No other text, no markdown fences.

[
  { "effect": "review-criteria regeneration", "identified": true, "evidence": "Response mentions that review-criteria.md needs updating with the new security quality bars" },
  { "effect": "rules line budget", "identified": false, "evidence": "" },
  { "effect": "snap audit updates", "identified": true, "evidence": "..." },
  { "effect": "new reference file", "identified": true, "evidence": "..." },
  { "effect": "workflow pointer", "identified": false, "evidence": "" }
]
```

- [x] **Step 5: Commit**

```bash
git add evals/validation/boundary-judge.md \
        evals/validation/boundary-mismatch-rubric.md \
        evals/validation/pattern-judge.md \
        evals/validation/matrix-judge.md
git commit -m "evals: add judge prompts and rubric for feature validation"
```

---

### Task 5: Execution Pattern Prompts

**blocks:** 8
**blocked-by:** []
**parallelizable:** true (with Tasks 1-4)

**Files:**
- Create: `evals/prompts/execution-patterns.txt`

- [x] **Step 1: Create prompts file**

Write `evals/prompts/execution-patterns.txt`. Three prompts, one per pattern. Uses `P|` axis prefix matching existing format.

```
P|Plan how to execute this work: First migrate the database schema to add a status column to the orders table, then update the API endpoint to expose the new status field in the response, then update the request spec to cover the new field. Each step depends on the previous step completing successfully.
P|Plan how to execute this work: Audit this codebase for three independent concerns — check for security vulnerabilities in the authentication flow, identify any stub implementations that need completing, and review overall code quality against the project standards. These three audits are independent of each other and can happen simultaneously.
P|Plan how to execute this work: Write the new payment processing endpoint with full implementation including validation, error handling, and database operations. Then have the implementation independently reviewed against the API design spec and the project's quality gates to identify any issues before making revisions.
```

- [x] **Step 2: Commit**

```bash
git add evals/prompts/execution-patterns.txt
git commit -m "evals: add execution pattern planning prompts"
```

---

### Task 6: Boundary-Mismatch Test Script

**blocks:** 10
**blocked-by:** 1, 2, 3, 4
**parallelizable:** false

**Files:**
- Create: `evals/validation/run-boundary-test.sh`

- [x] **Step 1: Write the script**

Write `evals/validation/run-boundary-test.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$EVALS_DIR/fixtures/integration-api"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"
JUDGE_PROMPT="$SCRIPT_DIR/boundary-judge.md"
RUBRIC="$SCRIPT_DIR/boundary-mismatch-rubric.md"

mkdir -p "$RESULTS_DIR"

echo "=== Boundary-Mismatch Detection Test ==="
echo ""

# Copy fixture to temp dir, excluding DEFECT-MANIFEST.md
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

rsync -a --exclude='DEFECT-MANIFEST.md' "$FIXTURE_DIR/" "$TMPDIR/"

AUDIT_PROMPT='Review this codebase for integration issues. Examine how data flows between layers — API routes, frontend hooks, type definitions, navigation, state management. For each issue, identify: the files involved, the specific mismatch, and why it would fail at runtime despite passing TypeScript compilation. Focus on cross-boundary coherence, not single-file code quality.'

echo "Running audit..."
AUDIT_OUTPUT=$(cd "$TMPDIR" && claude -p "$AUDIT_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Claude invocation failed"
  echo '{ "status": "ERROR", "reason": "Claude invocation failed" }' > "$RESULTS_DIR/boundary-test.json"
  exit 1
}

AUDIT_TEXT=$(echo "$AUDIT_OUTPUT" | jq -r '.result // "ERROR: no result"')
echo "$AUDIT_OUTPUT" > "$RESULTS_DIR/boundary-audit-raw.json"

echo "Running judge..."
DEFECT_MANIFEST=$(cat "$FIXTURE_DIR/DEFECT-MANIFEST.md")
RUBRIC_TEXT=$(cat "$RUBRIC")
JUDGE_TEMPLATE=$(cat "$JUDGE_PROMPT")
JUDGE_INPUT="${JUDGE_TEMPLATE//\{AUDIT_OUTPUT\}/$AUDIT_TEXT}"
JUDGE_INPUT="${JUDGE_INPUT//\{DEFECT_MANIFEST\}/$RUBRIC_TEXT}"

JUDGE_OUTPUT=$(claude -p "$JUDGE_INPUT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Judge invocation failed"
  echo '{ "status": "ERROR", "reason": "Judge invocation failed" }' > "$RESULTS_DIR/boundary-test.json"
  exit 1
}

JUDGE_TEXT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')
echo "$JUDGE_TEXT" > "$RESULTS_DIR/boundary-judge-raw.json"

DETECTED=$(echo "$JUDGE_TEXT" | jq '[.[] | select(.detected == true)] | length' 2>/dev/null || echo 0)
TOTAL=6
THRESHOLD=4

echo ""
echo "Per-bug results:"
for i in $(seq 0 5); do
  DEFECT=$(echo "$JUDGE_TEXT" | jq -r ".[$i].defect // \"BM-$((i+1))\"" 2>/dev/null)
  STATUS=$(echo "$JUDGE_TEXT" | jq -r ".[$i].detected // false" 2>/dev/null)
  if [ "$STATUS" = "true" ]; then
    echo "  $DEFECT: DETECTED"
  else
    echo "  $DEFECT: MISSED"
  fi
done

echo ""
if [ "$DETECTED" -ge "$THRESHOLD" ]; then
  echo "Boundary-Mismatch Detection: $DETECTED/$TOTAL detected   [PASS ≥$THRESHOLD]"
  RESULT="PASS"
else
  echo "Boundary-Mismatch Detection: $DETECTED/$TOTAL detected   [FAIL ≥$THRESHOLD]"
  RESULT="FAIL"
fi

echo "{\"test\": \"boundary-mismatch\", \"detected\": $DETECTED, \"total\": $TOTAL, \"threshold\": $THRESHOLD, \"result\": \"$RESULT\"}" > "$RESULTS_DIR/boundary-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
```

- [x] **Step 2: Make executable and commit**

```bash
chmod +x evals/validation/run-boundary-test.sh
git add evals/validation/run-boundary-test.sh
git commit -m "evals: add boundary-mismatch test script"
```

---

### Task 7: Pattern Test Script

**blocks:** 10
**blocked-by:** 3, 4, 5
**parallelizable:** true (with Tasks 8, 9)

**Files:**
- Create: `evals/validation/run-pattern-test.sh`

- [x] **Step 1: Write the script**

Write `evals/validation/run-pattern-test.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$EVALS_DIR/fixtures/rails-api"
PROMPTS_FILE="$EVALS_DIR/prompts/execution-patterns.txt"
JUDGE_PROMPT="$SCRIPT_DIR/pattern-judge.md"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"

# The catalog lives in the GIGO plugin source
PATTERNS_REF="$(dirname "$EVALS_DIR")/skills/spec/references/execution-patterns.md"

mkdir -p "$RESULTS_DIR"

echo "=== Execution Pattern Catalog Test ==="
echo ""

EXPECTED_PATTERNS=("Pipeline" "Fan-out/Fan-in" "Producer-Reviewer")
CORRECT=0
TOTAL=3
PROMPT_NUM=0

# Create temp copy of fixture with execution-patterns.md injected
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cp -r "$FIXTURE_DIR"/* "$TMPDIR/" 2>/dev/null || true
cp -r "$FIXTURE_DIR"/.claude "$TMPDIR/" 2>/dev/null || true
mkdir -p "$TMPDIR/.claude/references"
cp "$PATTERNS_REF" "$TMPDIR/.claude/references/execution-patterns.md"

# Append execution-patterns pointer to existing "When to Go Deeper" section
echo 'When planning how to execute work, read `.claude/references/execution-patterns.md` — pick the pattern matching the task'"'"'s dependency shape before writing tasks.' >> "$TMPDIR/.claude/rules/standards.md"

JUDGE_TEMPLATE=$(cat "$JUDGE_PROMPT")

while IFS='|' read -r axis prompt; do
  PROMPT_NUM=$((PROMPT_NUM + 1))
  EXPECTED="${EXPECTED_PATTERNS[$((PROMPT_NUM - 1))]}"

  echo "Prompt $PROMPT_NUM (expected: $EXPECTED): $prompt"

  echo "  Running plan generation..."
  PLAN_OUTPUT=$(cd "$TMPDIR" && claude -p "$prompt" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
    echo "  ERROR: Claude invocation failed"
    echo "{\"prompt\": $PROMPT_NUM, \"expected\": \"$EXPECTED\", \"correct\": false, \"error\": \"invocation_failed\"}" > "$RESULTS_DIR/pattern-prompt-${PROMPT_NUM}.json"
    continue
  }

  PLAN_TEXT=$(echo "$PLAN_OUTPUT" | jq -r '.result // "ERROR: no result"')
  echo "$PLAN_OUTPUT" > "$RESULTS_DIR/pattern-plan-${PROMPT_NUM}-raw.json"

  echo "  Running judge..."
  JUDGE_INPUT="${JUDGE_TEMPLATE//\{PLAN_OUTPUT\}/$PLAN_TEXT}"
  JUDGE_INPUT="${JUDGE_INPUT//\{EXPECTED_PATTERN\}/$EXPECTED}"

  JUDGE_OUTPUT=$(claude -p "$JUDGE_INPUT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
    echo "  ERROR: Judge invocation failed"
    echo "{\"prompt\": $PROMPT_NUM, \"expected\": \"$EXPECTED\", \"correct\": false, \"error\": \"judge_failed\"}" > "$RESULTS_DIR/pattern-prompt-${PROMPT_NUM}.json"
    continue
  }

  JUDGE_TEXT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')
  IS_CORRECT=$(echo "$JUDGE_TEXT" | jq -r '.correct // false' 2>/dev/null || echo "false")

  if [ "$IS_CORRECT" = "true" ]; then
    echo "  Result: CORRECT"
    CORRECT=$((CORRECT + 1))
  else
    echo "  Result: INCORRECT"
  fi

  echo "$JUDGE_TEXT" > "$RESULTS_DIR/pattern-prompt-${PROMPT_NUM}.json"
  echo ""

done < "$PROMPTS_FILE"

THRESHOLD=3

if [ "$CORRECT" -ge "$THRESHOLD" ]; then
  echo "Execution Pattern Catalog: $CORRECT/$TOTAL patterns   [PASS $THRESHOLD/$TOTAL]"
  RESULT="PASS"
else
  echo "Execution Pattern Catalog: $CORRECT/$TOTAL patterns   [FAIL $THRESHOLD/$TOTAL]"
  RESULT="FAIL"
fi

echo "{\"test\": \"execution-patterns\", \"correct\": $CORRECT, \"total\": $TOTAL, \"threshold\": $THRESHOLD, \"result\": \"$RESULT\"}" > "$RESULTS_DIR/pattern-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
```

- [x] **Step 2: Make executable and commit**

```bash
chmod +x evals/validation/run-pattern-test.sh
git add evals/validation/run-pattern-test.sh
git commit -m "evals: add execution pattern test script"
```

---

### Task 8: Matrix Test Script

**blocks:** 10
**blocked-by:** 3, 4
**parallelizable:** true (with Tasks 7, 9)

**Files:**
- Create: `evals/validation/run-matrix-test.sh`

- [x] **Step 1: Write the script**

Write `evals/validation/run-matrix-test.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURE_DIR="$EVALS_DIR/fixtures/rails-api"
JUDGE_PROMPT="$SCRIPT_DIR/matrix-judge.md"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"

MATRIX_REF="$(dirname "$EVALS_DIR")/skills/maintain/references/change-impact-matrix.md"

mkdir -p "$RESULTS_DIR"

echo "=== Phase Selection Matrix Test ==="
echo ""

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cp -r "$FIXTURE_DIR"/* "$TMPDIR/" 2>/dev/null || true
cp -r "$FIXTURE_DIR"/.claude "$TMPDIR/" 2>/dev/null || true
mkdir -p "$TMPDIR/.claude/references"
cp "$MATRIX_REF" "$TMPDIR/.claude/references/change-impact-matrix.md"

SCENARIO_PROMPT='A new persona has been added to this project'"'"'s CLAUDE.md:

### Vault — The Security Auditor

**Modeled after:** Troy Hunt'"'"'s breach-first pragmatism + OWASP'"'"'s systematic methodology + Tanya Janca'"'"'s DevSecOps integration.

- **Owns:** Input validation, authentication flows, SQL injection prevention, dependency auditing
- **Quality bar:** Every endpoint validates authentication and authorization. No raw SQL. Input sanitization on all user-facing fields.
- **Won'"'"'t do:** Security theater — adding CSRF tokens to an API-only app, over-restricting dev environments

This persona was just added to CLAUDE.md. Without making any changes, analyze: what other files in the .claude/ directory need updating as a result? For each file, explain what change is needed and why.'

echo "Running scenario analysis..."
SCENARIO_OUTPUT=$(cd "$TMPDIR" && claude -p "$SCENARIO_PROMPT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Claude invocation failed"
  echo '{ "status": "ERROR", "reason": "Claude invocation failed" }' > "$RESULTS_DIR/matrix-test.json"
  exit 1
}

SCENARIO_TEXT=$(echo "$SCENARIO_OUTPUT" | jq -r '.result // "ERROR: no result"')
echo "$SCENARIO_OUTPUT" > "$RESULTS_DIR/matrix-scenario-raw.json"

echo "Running judge..."
JUDGE_TEMPLATE=$(cat "$JUDGE_PROMPT")
JUDGE_INPUT="${JUDGE_TEMPLATE//\{RESPONSE\}/$SCENARIO_TEXT}"

JUDGE_OUTPUT=$(claude -p "$JUDGE_INPUT" --output-format json --permission-mode bypassPermissions 2>/dev/null) || {
  echo "ERROR: Judge invocation failed"
  echo '{ "status": "ERROR", "reason": "Judge invocation failed" }' > "$RESULTS_DIR/matrix-test.json"
  exit 1
}

JUDGE_TEXT=$(echo "$JUDGE_OUTPUT" | jq -r '.result // "ERROR"' | sed 's/^```json//;s/^```//;/^$/d')
echo "$JUDGE_TEXT" > "$RESULTS_DIR/matrix-judge-raw.json"

IDENTIFIED=$(echo "$JUDGE_TEXT" | jq '[.[] | select(.identified == true)] | length' 2>/dev/null || echo 0)
TOTAL=5
THRESHOLD=3

echo ""
echo "Per-effect results:"
EFFECTS=("review-criteria regeneration" "rules line budget" "snap audit updates" "new reference file" "workflow pointer")
for i in $(seq 0 4); do
  STATUS=$(echo "$JUDGE_TEXT" | jq -r ".[$i].identified // false" 2>/dev/null)
  if [ "$STATUS" = "true" ]; then
    echo "  ${EFFECTS[$i]}: IDENTIFIED"
  else
    echo "  ${EFFECTS[$i]}: MISSED"
  fi
done

echo ""
if [ "$IDENTIFIED" -ge "$THRESHOLD" ]; then
  echo "Phase Selection Matrix: $IDENTIFIED/$TOTAL effects   [PASS ≥$THRESHOLD]"
  RESULT="PASS"
else
  echo "Phase Selection Matrix: $IDENTIFIED/$TOTAL effects   [FAIL ≥$THRESHOLD]"
  RESULT="FAIL"
fi

echo "{\"test\": \"phase-matrix\", \"identified\": $IDENTIFIED, \"total\": $TOTAL, \"threshold\": $THRESHOLD, \"result\": \"$RESULT\"}" > "$RESULTS_DIR/matrix-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
```

- [x] **Step 2: Make executable and commit**

```bash
chmod +x evals/validation/run-matrix-test.sh
git add evals/validation/run-matrix-test.sh
git commit -m "evals: add phase selection matrix test script"
```

---

### Task 9: Cleanup Verification Script

**blocks:** 10
**blocked-by:** []
**parallelizable:** true (with all other tasks)

**Files:**
- Create: `evals/validation/run-cleanup-verify.sh`

- [x] **Step 1: Write the script**

Write `evals/validation/run-cleanup-verify.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$EVALS_DIR")"
RESULTS_DIR="${1:-$EVALS_DIR/results/validation-$(date +%Y-%m-%d-%H%M%S)}"

mkdir -p "$RESULTS_DIR"

echo "=== Agent Teams Cleanup Verification ==="
echo ""

CHECKS_PASSED=0
CHECKS_TOTAL=5
DETAILS=""

# Check 1: No Tier 3 in execute SKILL.md production sections
TIER3_HITS=$(grep -c "Tier 3" "$PROJECT_DIR/skills/execute/SKILL.md" 2>/dev/null || echo 0)
if [ "$TIER3_HITS" -eq 0 ]; then
  echo "  Check 1: No 'Tier 3' in SKILL.md              [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 1, \"name\": \"no_tier3\", \"clean\": true},"
else
  echo "  Check 1: 'Tier 3' found in SKILL.md ($TIER3_HITS hits) [DIRTY]"
  DETAILS="$DETAILS{\"check\": 1, \"name\": \"no_tier3\", \"clean\": false, \"hits\": $TIER3_HITS},"
fi

# Check 2: No TeamCreate or team-scoped SendMessage in SKILL.md
TEAM_API_HITS=$(grep -cE "TeamCreate|SendMessage.*team" "$PROJECT_DIR/skills/execute/SKILL.md" 2>/dev/null || echo 0)
if [ "$TEAM_API_HITS" -eq 0 ]; then
  echo "  Check 2: No TeamCreate/SendMessage in SKILL.md [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 2, \"name\": \"no_team_api\", \"clean\": true},"
else
  echo "  Check 2: Team API refs in SKILL.md ($TEAM_API_HITS hits) [DIRTY]"
  DETAILS="$DETAILS{\"check\": 2, \"name\": \"no_team_api\", \"clean\": false, \"hits\": $TEAM_API_HITS},"
fi

# Check 3: No Tier 3 templates in teammate-prompts.md
TEMPLATE_HITS=$(grep -cE "Tier 3|team\.prompt|team\.template" "$PROJECT_DIR/skills/execute/references/teammate-prompts.md" 2>/dev/null || echo 0)
if [ "$TEMPLATE_HITS" -eq 0 ]; then
  echo "  Check 3: No Tier 3 templates in prompts         [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 3, \"name\": \"no_tier3_templates\", \"clean\": true},"
else
  echo "  Check 3: Tier 3 templates found ($TEMPLATE_HITS hits)  [DIRTY]"
  DETAILS="$DETAILS{\"check\": 3, \"name\": \"no_tier3_templates\", \"clean\": false, \"hits\": $TEMPLATE_HITS},"
fi

# Check 4: Design doc exists with status banner
DESIGN_DOC="$PROJECT_DIR/skills/execute/references/agent-teams-design.md"
if [ -f "$DESIGN_DOC" ]; then
  HAS_BANNER=$(head -10 "$DESIGN_DOC" | grep -ciE "not shipped|target.state" 2>/dev/null || echo 0)
  if [ "$HAS_BANNER" -gt 0 ]; then
    echo "  Check 4: Design doc exists with status banner    [CLEAN]"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    DETAILS="$DETAILS{\"check\": 4, \"name\": \"design_doc\", \"clean\": true},"
  else
    echo "  Check 4: Design doc exists but no status banner  [DIRTY]"
    DETAILS="$DETAILS{\"check\": 4, \"name\": \"design_doc\", \"clean\": false, \"reason\": \"no_banner\"},"
  fi
else
  echo "  Check 4: Design doc missing                     [DIRTY]"
  DETAILS="$DETAILS{\"check\": 4, \"name\": \"design_doc\", \"clean\": false, \"reason\": \"missing\"},"
fi

# Check 5: No AGENT_TEAMS env var in SKILL.md
ENV_HITS=$(grep -cE "AGENT_TEAMS|EXPERIMENTAL_AGENT" "$PROJECT_DIR/skills/execute/SKILL.md" 2>/dev/null || echo 0)
if [ "$ENV_HITS" -eq 0 ]; then
  echo "  Check 5: No AGENT_TEAMS env var in SKILL.md     [CLEAN]"
  CHECKS_PASSED=$((CHECKS_PASSED + 1))
  DETAILS="$DETAILS{\"check\": 5, \"name\": \"no_env_var\", \"clean\": true}"
else
  echo "  Check 5: AGENT_TEAMS env var found ($ENV_HITS hits) [DIRTY]"
  DETAILS="$DETAILS{\"check\": 5, \"name\": \"no_env_var\", \"clean\": false, \"hits\": $ENV_HITS}"
fi

echo ""
if [ "$CHECKS_PASSED" -eq "$CHECKS_TOTAL" ]; then
  echo "Agent Teams Cleanup: $CHECKS_PASSED/$CHECKS_TOTAL checks   [PASS $CHECKS_TOTAL/$CHECKS_TOTAL]"
  RESULT="PASS"
else
  echo "Agent Teams Cleanup: $CHECKS_PASSED/$CHECKS_TOTAL checks   [FAIL $CHECKS_TOTAL/$CHECKS_TOTAL]"
  RESULT="FAIL"
fi

echo "{\"test\": \"cleanup-verify\", \"passed\": $CHECKS_PASSED, \"total\": $CHECKS_TOTAL, \"result\": \"$RESULT\", \"details\": [$DETAILS]}" > "$RESULTS_DIR/cleanup-test.json"

[ "$RESULT" = "PASS" ] && exit 0 || exit 1
```

- [x] **Step 2: Make executable and commit**

```bash
chmod +x evals/validation/run-cleanup-verify.sh
git add evals/validation/run-cleanup-verify.sh
git commit -m "evals: add Agent Teams cleanup verification script"
```

---

### Task 10: Master Runner

**blocks:** []
**blocked-by:** 6, 7, 8, 9
**parallelizable:** false

**Files:**
- Create: `evals/validation/run-all.sh`

- [x] **Step 1: Write the script**

Write `evals/validation/run-all.sh`:

```bash
#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVALS_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
RESULTS_DIR="$EVALS_DIR/results/validation-$TIMESTAMP"

mkdir -p "$RESULTS_DIR"

echo "=== Feature Validation Suite ==="
echo "Results: $RESULTS_DIR"
echo ""

TESTS_PASSED=0
TESTS_TOTAL=5
RESULTS=()

# Test 1: Boundary-Mismatch Detection
echo "--- Test 1/5: Boundary-Mismatch Detection ---"
echo ""
if "$SCRIPT_DIR/run-boundary-test.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
BM_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/boundary-test.json" 2>/dev/null || echo "ERROR")
BM_SCORE=$(jq -r '"\(.detected)/\(.total)"' "$RESULTS_DIR/boundary-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("1. Boundary-Mismatch Detection:    $BM_SCORE detected   [$BM_RESULT ≥4]")
echo ""

# Test 2: Phase Selection Matrix
echo "--- Test 2/5: Phase Selection Matrix ---"
echo ""
if "$SCRIPT_DIR/run-matrix-test.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
MX_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/matrix-test.json" 2>/dev/null || echo "ERROR")
MX_SCORE=$(jq -r '"\(.identified)/\(.total)"' "$RESULTS_DIR/matrix-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("2. Phase Selection Matrix:         $MX_SCORE effects     [$MX_RESULT ≥3]")
echo ""

# Test 3: Execution Pattern Catalog
echo "--- Test 3/5: Execution Pattern Catalog ---"
echo ""
if "$SCRIPT_DIR/run-pattern-test.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
PT_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/pattern-test.json" 2>/dev/null || echo "ERROR")
PT_SCORE=$(jq -r '"\(.correct)/\(.total)"' "$RESULTS_DIR/pattern-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("3. Execution Pattern Catalog:      $PT_SCORE patterns    [$PT_RESULT 3/3]")
echo ""

# Test 4: Agent Teams Cleanup
echo "--- Test 4/5: Agent Teams Cleanup ---"
echo ""
if "$SCRIPT_DIR/run-cleanup-verify.sh" "$RESULTS_DIR" 2>&1; then
  TESTS_PASSED=$((TESTS_PASSED + 1))
fi
CL_RESULT=$(jq -r '.result // "ERROR"' "$RESULTS_DIR/cleanup-test.json" 2>/dev/null || echo "ERROR")
CL_SCORE=$(jq -r '"\(.passed)/\(.total)"' "$RESULTS_DIR/cleanup-test.json" 2>/dev/null || echo "?/?")
RESULTS+=("4. Agent Teams Cleanup:            $CL_SCORE checks      [$CL_RESULT 5/5]")
echo ""

# Test 5: Regression (assembled vs bare)
echo "--- Test 5/5: Regression Check ---"
echo ""
REGRESSION_DIR="$RESULTS_DIR/regression"
mkdir -p "$REGRESSION_DIR"

if "$EVALS_DIR/run-eval.sh" 2>&1; then
  LATEST_EVAL=$(ls -td "$EVALS_DIR/results/"* 2>/dev/null | grep -v validation | head -1)
  if [ -n "$LATEST_EVAL" ] && [ -d "$LATEST_EVAL" ]; then
    "$EVALS_DIR/score-eval.sh" "$LATEST_EVAL" 2>&1
    cp "$LATEST_EVAL/summary.md" "$REGRESSION_DIR/" 2>/dev/null || true

    WIN_PCT=$(grep -oE '[0-9]+%' "$LATEST_EVAL/summary.md" 2>/dev/null | tail -1 | tr -d '%' || echo 0)
    if [ "$WIN_PCT" -ge 90 ]; then
      TESTS_PASSED=$((TESTS_PASSED + 1))
      RG_RESULT="PASS"
    else
      RG_RESULT="FAIL"
    fi
    RESULTS+=("5. Regression (assembled vs bare): ${WIN_PCT}% wins        [$RG_RESULT ≥90%]")
  else
    RESULTS+=("5. Regression (assembled vs bare): ?% wins         [ERROR]")
  fi
else
  RESULTS+=("5. Regression (assembled vs bare): ?% wins         [ERROR]")
fi
echo ""

# Summary
echo "==========================================="
echo "=== Feature Validation Suite — Summary ==="
echo "==========================================="
echo ""

for line in "${RESULTS[@]}"; do
  echo "$line"
done

echo ""
echo "Overall: $TESTS_PASSED/$TESTS_TOTAL PASS"
echo ""
echo "Results saved to: $RESULTS_DIR"

# Save summary
{
  echo "# Feature Validation Suite Results"
  echo ""
  echo "Run: $TIMESTAMP"
  echo ""
  for line in "${RESULTS[@]}"; do
    echo "$line"
  done
  echo ""
  echo "Overall: $TESTS_PASSED/$TESTS_TOTAL PASS"
} > "$RESULTS_DIR/summary.md"

[ "$TESTS_PASSED" -eq "$TESTS_TOTAL" ] && exit 0 || exit 1
```

- [x] **Step 2: Make executable and commit**

```bash
chmod +x evals/validation/run-all.sh
git add evals/validation/run-all.sh
git commit -m "evals: add master runner for feature validation suite"
```

---

## Dependency Graph

```
Task 1 (types + API) ──┐
                        ├── Task 3 (assembly) ──┐
Task 2 (hooks + models)─┘                       │
                                                 ├── Task 6 (boundary test) ──┐
Task 4 (judges + rubric) ──────────────────────┬─┤                            │
                                                │ ├── Task 7 (pattern test) ──┤
Task 5 (pattern prompts) ──────────────────────┘ │                            ├── Task 10 (master runner)
                                                  ├── Task 8 (matrix test) ──┤
                                                  │                           │
Task 9 (cleanup verify) ─────────────────────────┴───────────────────────────┘
```

**Parallel waves:**
- Wave 1: Tasks 1, 2, 4, 5, 9 (all independent)
- Wave 2: Task 3 (needs 1 + 2)
- Wave 3: Tasks 6, 7, 8 (need 3 + 4; 7 also needs 5)
- Wave 4: Task 10 (needs 6-9)

## Risks

1. **Flaky boundary detection.** The audit prompt is open-ended — detection rate will vary across runs. The 4/6 threshold buffers this but can't eliminate it. If results are consistently borderline, consider tightening the audit prompt.

2. **Judge prompt variable substitution.** Bash `${TEMPLATE//\{VAR\}/value}` fails if the value contains special characters (newlines, backslashes, `$`). The audit output will likely contain code. If substitution breaks, switch to `sed` or write the judge input to a temp file.

3. **Regression test duration.** `run-eval.sh` runs 22 Claude invocations + 11 judge invocations. The full suite with regression takes ~30 minutes. Consider skipping regression in quick runs (`run-all.sh --skip-regression`).

## Done

The suite is done when `run-all.sh` executes end-to-end and produces a results directory with per-test JSON files and a summary. All 5 tests produce pass/fail verdicts. Individual test scripts are independently runnable.

<!-- approved: plan 2026-04-12T06:28:45 by:Eaven -->
