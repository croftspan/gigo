# Plan — Worked Examples

Three examples at different scales showing how plans look in practice.

---

## Small Task

**User says:** "The login page is broken on mobile"

**Plan:**

```markdown
# Fix Mobile Login — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.

**Spec:** (inline — too small for a separate spec)

**Goal:** Fix login page rendering on mobile viewports

**Execution Pattern:** Supervisor

**Architecture:** CSS fix targeting responsive breakpoints in the login component

---

### Task 1: Diagnose and Fix Mobile Layout

**blocks:** []
**blocked-by:** []
**parallelizable:** false

**Files:**
- Modify: `src/components/Login.css`

- [ ] **Step 1:** Reproduce the bug at 375px and 414px viewport widths
- [ ] **Step 2:** Check the login component's responsive breakpoints — likely a CSS issue with fixed positioning on the modal or virtual keyboard pushing content
- [ ] **Step 3:** Fix the CSS — test on iOS Safari and Chrome Android (they handle viewport differently)
- [ ] **Step 4:** Verify login works on both iOS and Android at 375px and 414px widths
- [ ] **Step 5:** Commit

**Done when:** Login works on iOS Safari and Chrome Android at 375px and 414px widths. Virtual keyboard doesn't break layout.
```

---

## Fan-out/Fan-in Example

**User says:** "Draft a three-section market report on AI code tools, then merge into a single doc"

**Plan:**

```markdown
# Market Report — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.

**Spec:** (inline)

**Goal:** Produce a three-section market report on AI code tools

**Execution Pattern:** Fan-out/Fan-in

**Architecture:** Three parallel section drafts followed by a single merge pass that reconciles overlaps and adds a cross-section summary

---

### Task 1: Draft Section A — Market Overview

**blocks:** 4
**blocked-by:** []
**parallelizable:** true (with Tasks 2, 3)

- [ ] **Step 1:** Gather market size and growth data
- [ ] **Step 2:** Write the overview section (~600 words)
- [ ] **Step 3:** Commit

### Task 2: Draft Section B — Competitor Landscape

**blocks:** 4
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 3)

- [ ] **Step 1:** Research 5-8 competitors
- [ ] **Step 2:** Write the landscape section (~800 words)
- [ ] **Step 3:** Commit

### Task 3: Draft Section C — User Interviews

**blocks:** 4
**blocked-by:** []
**parallelizable:** true (with Tasks 1, 2)

- [ ] **Step 1:** Synthesize 10 user interviews into themes
- [ ] **Step 2:** Write the interviews section (~700 words)
- [ ] **Step 3:** Commit

### Task 4: Merge and Cross-Reference

**blocks:** []
**blocked-by:** 1, 2, 3
**parallelizable:** false

- [ ] **Step 1:** Merge the three sections into a single doc
- [ ] **Step 2:** Reconcile overlapping claims between sections
- [ ] **Step 3:** Write a cross-section summary
- [ ] **Step 4:** Commit

**Done when:** Single report doc exists with all three sections merged, overlaps reconciled, summary added.
```

---

## Pipeline Example

**User says:** "Synthesize 20 academic papers on distributed consensus into a single literature review"

**Plan:**

```markdown
# Literature Review — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.

**Spec:** (inline)

**Goal:** Produce a literature review covering 20 papers on distributed consensus

**Execution Pattern:** Pipeline

**Architecture:** Strict sequence: gather papers → extract claims → synthesize themes → write review. Each stage's output feeds the next.

---

### Task 1: Gather Papers

**blocks:** 2
**blocked-by:** []
**parallelizable:** false

- [ ] **Step 1:** Download 20 papers matching the search criteria
- [ ] **Step 2:** Commit bibliography

### Task 2: Extract Claims

**blocks:** 3
**blocked-by:** 1
**parallelizable:** false

- [ ] **Step 1:** Read each paper, extract 3-5 key claims per paper
- [ ] **Step 2:** Commit extracted claims table

### Task 3: Synthesize Themes

**blocks:** 4
**blocked-by:** 2
**parallelizable:** false

- [ ] **Step 1:** Cluster claims into 4-6 themes
- [ ] **Step 2:** Commit themes outline

### Task 4: Write Review

**blocks:** []
**blocked-by:** 3
**parallelizable:** false

- [ ] **Step 1:** Write the review section-by-section, one theme per section
- [ ] **Step 2:** Commit final review
```

---

## Medium Task

**User says:** "We need to add Stripe subscriptions with a free trial"

**Plan:**

```markdown
# Stripe Subscriptions — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-27-stripe-subscriptions-design.md`

**Goal:** Add Stripe subscription billing with free trial support

**Execution Pattern:** Supervisor

**Architecture:** Stripe Checkout for payment flow, webhooks for lifecycle events, subscription status gated on user model

**Tech Stack:** Stripe API, Node.js, PostgreSQL

---

### Task 1: Stripe Configuration

**blocks:** 2, 3, 4
**blocked-by:** []
**parallelizable:** false

**Files:**
- Create: `src/config/stripe.ts`
- Modify: `.env.example`

- [ ] **Step 1:** Add Stripe API keys to environment config
- [ ] **Step 2:** Create Stripe client configuration module
- [ ] **Step 3:** Define pricing plans and trial period constants
- [ ] **Step 4:** Commit

### Task 2: Checkout Flow

**blocks:** 5
**blocked-by:** 1
**parallelizable:** true (with Task 3)

**Files:**
- Create: `src/routes/checkout.ts`
- Create: `src/components/PricingPage.tsx`
- Test: `tests/routes/checkout.test.ts`

- [ ] **Step 1:** Write test for checkout session creation
- [ ] **Step 2:** Implement checkout route using Stripe Checkout
- [ ] **Step 3:** Build pricing page component
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit

### Task 3: Webhook Handler

**blocks:** 4, 5
**blocked-by:** 1
**parallelizable:** true (with Task 2)

**Files:**
- Create: `src/routes/webhooks.ts`
- Test: `tests/routes/webhooks.test.ts`

- [ ] **Step 1:** Write tests for webhook event handling
- [ ] **Step 2:** Implement handler for `customer.subscription.created`, `invoice.payment_failed`, `customer.subscription.deleted`
- [ ] **Step 3:** Add webhook signature verification
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit

*Risk: PCI compliance scope increases with embedded forms — Stripe Checkout avoids this*

### Task 4: User Subscription Model

**blocks:** 5
**blocked-by:** 1, 3
**parallelizable:** false

**Files:**
- Modify: `src/models/user.ts`
- Create: `src/middleware/subscriptionGate.ts`
- Test: `tests/middleware/subscriptionGate.test.ts`

- [ ] **Step 1:** Add subscription status fields to user model
- [ ] **Step 2:** Write test for feature gating middleware
- [ ] **Step 3:** Implement subscription gate middleware
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit

### Task 5: Billing Portal

**blocks:** []
**blocked-by:** 2, 3, 4
**parallelizable:** false

**Files:**
- Create: `src/routes/billing.ts`
- Create: `src/components/BillingPage.tsx`
- Test: `tests/routes/billing.test.ts`

- [ ] **Step 1:** Write test for portal session creation
- [ ] **Step 2:** Implement billing route using Stripe Customer Portal
- [ ] **Step 3:** Build billing page component
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit

**Done when:** User can sign up for trial, get charged after trial, upgrade/downgrade, and cancel.
```

---

## Large Task

**User says:** "I want to rebuild the entire frontend in a new framework"

**Plan (abbreviated — full plan would have detailed steps per task):**

```markdown
# Frontend Migration — Implementation Plan

> **For agentic workers:** Use gigo:execute to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Spec:** `docs/gigo/specs/2026-03-27-frontend-migration-design.md`

**Goal:** Migrate frontend from legacy framework to [chosen framework]

**Execution Pattern:** Supervisor

**Architecture:** Incremental migration using feature flags, both frontends run in parallel during cutover

**Tech Stack:** [Chosen framework], feature flags, existing API layer

---

## Phase 1: Foundation (unblocks everything)

**Execution Pattern:** Pipeline

### Task 1: Framework Spike

**blocks:** 2, 3
**blocked-by:** []
**parallelizable:** false

Validate the framework handles the most complex page. Set up build pipeline, linting, testing.

*Decision point: after the spike, confirm the framework handles the hardest use case before continuing.*

### Task 2: Build Infrastructure

**blocks:** 4, 5, 6
**blocked-by:** 1
**parallelizable:** false

CI/CD pipeline, dev server, test runner, linting config for the new framework.

## Phase 2: Core Pages (parallelizable)

**Execution Pattern:** Fan-out/Fan-in

### Task 3: Auth Flow Migration

**blocks:** 7
**blocked-by:** 2
**parallelizable:** true (with Tasks 4, 5)

Migrate login, signup, password reset.

### Task 4: Dashboard Migration

**blocks:** 7
**blocked-by:** 2
**parallelizable:** true (with Tasks 3, 5)

Migrate the page users see most.

### Task 5: Settings Migration

**blocks:** 7
**blocked-by:** 2
**parallelizable:** true (with Tasks 3, 4)

Migrate settings and account pages.

## Phase 3: Features (sequential, depends on Phase 2)

**Execution Pattern:** Supervisor

### Task 6: Remaining Pages

**blocks:** 7
**blocked-by:** 3, 4, 5
**parallelizable:** false

Migrate remaining feature pages and shared components.

*Risk: shared components may need redesign, not just migration.*

## Phase 4: Cutover

**Execution Pattern:** Supervisor

### Task 7: Parallel Run and Rollout

**blocks:** []
**blocked-by:** 6
**parallelizable:** false

Run both frontends with feature flags. Gradual rollout by route.

**Done when:** Old frontend fully retired. No feature regressions. All routes served by new framework.
```
