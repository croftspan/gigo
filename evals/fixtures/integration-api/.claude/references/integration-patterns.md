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
