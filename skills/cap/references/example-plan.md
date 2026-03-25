# Cap — Worked Examples

## Small Task

**User says:** "The login page is broken on mobile"

**Cap's plan:**
1. Check the login component's responsive breakpoints — likely a CSS issue at mobile widths
2. Test on iOS Safari and Chrome Android — they handle viewport differently
3. Watch for: fixed positioning on the modal, virtual keyboard pushing content
4. Done when: login works on both iOS and Android at 375px and 414px widths

## Medium Task

**User says:** "We need to add Stripe payments to the app"

**Cap asks:** "Are you adding one-time payments, subscriptions, or both?"

**User says:** "Subscriptions with a free trial"

**Cap's plan:**
1. Set up Stripe account and API keys — add to environment config
2. Create the pricing model — define plans, trial period, billing cycle
3. Build the checkout flow — Stripe Checkout or embedded form (Checkout is faster, embedded gives more control)
   - *Risk: PCI compliance scope increases with embedded forms*
4. Implement webhook handler — listen for `customer.subscription.created`, `invoice.payment_failed`, `customer.subscription.deleted`
   - *Blocks:* Steps 5-6 depend on this
5. Add subscription status to user model — gate features based on plan
6. Build the billing portal — let users manage their subscription via Stripe Customer Portal
7. Done when: user can sign up for trial, get charged after trial, upgrade/downgrade, and cancel

**Next steps:**
- "Your team has the expertise for this. Start with step 1 — the API keys unblock everything else."
- "Consider a `/fury` run if nobody on the team has Stripe experience."

## Large Task

**User says:** "I want to rebuild the entire frontend in a new framework"

**Cap asks:** "What's driving the rebuild — performance, developer experience, or something else?"

**Cap's plan:**

**Phase 1: Foundation (unblocks everything)**
- Choose framework and validate with a spike on the most complex page
- Set up build pipeline, linting, testing
- *Decision point: after the spike, confirm the framework handles your hardest use case*

**Phase 2: Core Pages (can parallelize)**
- Migrate auth flow (login, signup, password reset)
- Migrate dashboard (the page users see most)
- Migrate settings/account pages
- *These are independent — can run in parallel branches*

**Phase 3: Features (sequential, depends on Phase 2)**
- Migrate remaining feature pages
- Migrate shared components (modals, forms, tables)
- *Risk: shared components may need redesign, not just migration*

**Phase 4: Cutover**
- Run both frontends in parallel with feature flags
- Gradual rollout by route
- Done when: old frontend is fully retired, no feature regressions
