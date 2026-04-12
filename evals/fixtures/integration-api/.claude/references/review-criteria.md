## Spec Compliance Criteria

- Does every API endpoint's response shape match the type used by its consuming hook?
- Does every navigation link resolve to an actual page route?
- Does the status model's transition function handle all defined status values?

## Craft Review Criteria

- Are naming conventions consistent across type definitions, API serialization, and hook access patterns?
- Do hooks handle async responses at each lifecycle stage (pending, processing, ready) rather than assuming the final shape?
- When an API endpoint changes its response shape, are all consumers updated to match?
- Are type generics (fetchJson<T>) validated against actual API response structures, not assumed?
