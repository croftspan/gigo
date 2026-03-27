# Overwatch — Deep Adversarial Checklist

## The Core Question

"Did you actually do what you claimed, or did you describe doing it?"

## Per-Domain Checks

### Concurrency Claims

- [ ] You said "every goroutine has a shutdown path" — did you trace each `go` statement to a cancellation mechanism?
- [ ] You said "no data races" — did you run or verify `-race` results, or assume?
- [ ] You designed a worker pool — what happens when a worker panics? Did you handle it or hope?
- [ ] You said "graceful shutdown" — did you verify in-progress tasks complete, or just cancel the context?

### Persistence Claims

- [ ] You said "crash-safe" — is there a test that kills the process mid-write?
- [ ] You said "atomic state transition" — did you check it's actually in a transaction?
- [ ] You designed recovery logic — what state does the queue recover TO? Is it documented?

### CLI Claims

- [ ] You said "pipe-friendly" — did you actually pipe the output through grep/jq?
- [ ] You said "no TTY assumptions" — did you check for ANSI codes or fixed-width formatting?
- [ ] Error messages — do they include enough context to debug, or just "error: failed"?

## Meta-Checks

- Did persona language substitute for actual analysis? ("The State Guardian would say..." isn't a review.)
- Did you reference a file you were told to check? If not, go back and check it.
- Is your recommendation different from what a generic senior Go developer would say? If not, the team added nothing.
