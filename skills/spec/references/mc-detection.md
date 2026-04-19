# Mission-Control Detection, Preferences, and Source Path

Canonical reference for detecting mission-control (mc) availability, reading/writing the project's mc preference, and resolving the mc source repo path. Read by spec, execute, verify, and maintain when any of them needs to adapt behavior to mc state.

## Three-Check Detection

Runs per-invocation. Total cost < 100ms.

| Check | Mechanism | Cost |
|---|---|---|
| Skill availability | `"mission-control"` present in session's available skills list | < 1ms |
| Bin script availability | `command -v mc-init` returns success (exit 0) | < 50ms |
| Project initialized | `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` exists | < 10ms |

## Effective State

```
mc_available = skill_available AND mc_init_available
mc_active    = mc_available AND project_initialized
```

Three states (consumer-facing):
- **STATE_UNAVAILABLE** — `mc_available == false`. mc not installed at session level.
- **STATE_NOT_INITIALIZED** — `mc_available && !project_initialized`. mc installed but project not scaffolded.
- **STATE_ACTIVE** — `mc_active == true`. mc installed AND project scaffolded.

## Preference File

Path: `.claude/references/mission-control-preference.md` (project-local, never global).

Schema:
```markdown
---
mc-integration: enabled | disabled | never-ask
last-asked: <ISO-8601 UTC timestamp>
last-state-when-asked: STATE_UNAVAILABLE | STATE_NOT_INITIALIZED
tiebreak: tickets | plan | sequential   # set by execute when both vault/tickets/ AND plan.md exist
mc-source-path: /absolute/path/to/mission-control   # optional; overrides default
---

# Mission-Control Integration Preference

[Body documentation — see R2.1 for details.]
```

Behavior table (state × preference):

| `mc-integration` | State | Action |
|---|---|---|
| (file missing) | UNAVAILABLE | Prompt install+init |
| (file missing) | NOT_INITIALIZED | Prompt init |
| (file missing) | ACTIVE | mc-aware mode silently |
| `enabled` | UNAVAILABLE | Prompt |
| `enabled` | NOT_INITIALIZED | Prompt |
| `enabled` | ACTIVE | mc-aware mode silently |
| `never-ask` | UNAVAILABLE | v0.13 fallback silently |
| `never-ask` | NOT_INITIALIZED | v0.13 fallback silently |
| `never-ask` | ACTIVE | mc-aware mode silently |
| `disabled` | UNAVAILABLE | v0.13 fallback silently |
| `disabled` | NOT_INITIALIZED | v0.13 fallback silently |
| `disabled` | ACTIVE | v0.13 fallback silently (escape hatch) |

## Configurable Source Path (resolve_mc_source_path)

Resolution order:

1. Environment variable `GIGO_MC_SOURCE` — if set and path exists, use it.
2. Preference file field `mc-source-path` — if set and path exists, use it.
3. Default `~/projects/mission-control/` — fallback.

Do NOT hardcode the default anywhere else. All call sites go through this helper.

When resolution fails (none of the three paths exist), surface the clone-instructions error per §Conventions in the spec (with all three options: clone to default, set env var, set preference field).

## Mc-Init Invocation Procedure (R3.1.a)

Shared by all "install or init mc" paths. Steps:

1. **Pre-flight vault check:** test whether `$CLAUDE_PROJECT_DIR/vault/` exists. If yes, count tickets: `count = len(glob("$CLAUDE_PROJECT_DIR/vault/tickets/TCK-*.md")) - 1_if_TEMPLATE_present`.
2. **Branch on vault state:**
   - **Vault absent** → `bash("cd $CLAUDE_PROJECT_DIR && mc-init $CLAUDE_PROJECT_DIR")`.
   - **Vault exists, zero tickets** → announce to operator, run `bash("cd $CLAUDE_PROJECT_DIR && mc-init $CLAUDE_PROJECT_DIR --force")`. This rebuilds scaffolding only; no ticket data to destroy.
   - **Vault exists WITH ≥1 ticket** → DO NOT run `mc-init --force --yes`. This would DELETE the entire vault including tickets (verified against `mission-control/bin/mc-init` line 288: `shutil.rmtree(vault)`). Instead, ABORT with this message:

     > "Existing vault at `$CLAUDE_PROJECT_DIR/vault/` contains N ticket(s). `mc-init --force` would DELETE the entire vault including all tickets, logs, and verdicts.
     >
     > This retrofit path refuses to destroy operator data. Choose ONE of:
     >
     >   1. **Vault is already usable** — if `vault/_schema/ticket.md` exists, skip mc-init entirely (mc is already active). Re-run gigo:maintain; detection should report STATE_ACTIVE.
     >   2. **Rebuild scaffolding without losing tickets** — manually: move `vault/tickets/` aside, run `mc-init $CLAUDE_PROJECT_DIR --force`, restore `vault/tickets/`.
     >   3. **Fresh start** — back up `vault/` externally (e.g., `mv vault vault.bak`), then re-run this flow; detection will see an absent vault and run plain `mc-init`."
     >
     > Falling back to monolithic mode. No preference file written — re-run after choosing an option above.

     Execute writes the fallback to monolithic mode; does NOT write preference file (operator hasn't decided).
3. **Invoke `/mission-control init` skill** via Skill tool (only reached on the absent-vault or zero-tickets paths).
4. **Verify:** confirm `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` now exists. If missing, report mc-init failure to operator, fall back to monolithic mode.
5. **Preference update:** on success, if preference file missing, write `mc-integration: enabled`.

If mc-init exits non-zero at any step, surface stderr verbatim — do not hide mc failures.

## When to Read This

- **spec/SKILL.md Phase 5:** when deciding mc-mode (slice) vs monolithic fallback.
- **execute/SKILL.md Before-Starting:** when deciding mc-mode (ticket loop) vs plan.md fallback.
- **verify/SKILL.md start:** when deciding mc-mode (verdict files) vs human-readable fallback.
- **maintain/SKILL.md auto-detect:** when auto-suggesting the Add Mission-Control mode.
