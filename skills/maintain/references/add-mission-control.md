# Add Mission-Control — Maintain Mode Procedure

New auto-detected mode in gigo:maintain for retrofitting mission-control onto an existing project. Mode is INFRASTRUCTURE — it does NOT trigger Targeted Addition (team composition), Health Check (rule audit), or Restructure (file reorg).

## Triggers

Explicit: `$ARGUMENTS` contains `add-mission-control`.

Auto-suggested: operator runs `gigo:maintain` with no args AND mc detection returns STATE_NOT_INITIALIZED or STATE_UNAVAILABLE AND no preference file exists. In this case, maintain offers it as a top-level option alongside Targeted Addition / Health Check / Restructure / Upgrade.

## Detection

Read `skills/spec/references/mc-detection.md` for the canonical detection algorithm and state definitions. Do NOT reimplement.

## Per-State Behavior

| State | Action |
|---|---|
| ACTIVE | Print: *"Mission-control already active in this project. Audit vault for issues? (Vault audit deferred to v2; for now, status report only.)"* Print `mc-ticket-status --json` summary. |
| NOT_INITIALIZED | Run the **Mc-Init Invocation Procedure** per `skills/spec/references/mc-detection.md`. Report what was created. On success, update preference file: `mc-integration: enabled`. |
| UNAVAILABLE | Resolve mc source path per `resolve_mc_source_path()` in `skills/spec/references/mc-detection.md`. Check `{mc-source}/install.sh` exists; if yes, invoke via Bash, then run the Mc-Init Invocation Procedure. If mc source missing, surface clone instructions (all three resolution options). |

## Install Instructions Template (UNAVAILABLE, source missing)

```
mission-control source repo not found at {resolved-path}.
(Resolution order: GIGO_MC_SOURCE env var → mc-source-path in preference file → default ~/projects/mission-control/)

To enable mission-control integration, choose ONE of:

  1. Clone to the default location:
       git clone <mc-repo-url> ~/projects/mission-control

  2. Clone elsewhere and point GIGO at it:
       export GIGO_MC_SOURCE=/your/path/to/mission-control
       (add to your shell profile for persistence)

  3. Set mc-source-path in .claude/references/mission-control-preference.md:
       mc-source-path: /your/path/to/mission-control

Then re-run /gigo:maintain add-mission-control.
```

(The mc repo URL is not hardcoded — operator must know where mc lives.)

## Post-Init Verification

After Mc-Init Invocation Procedure returns:

1. Confirm `$CLAUDE_PROJECT_DIR/vault/_schema/ticket.md` exists.
2. Confirm `$CLAUDE_PROJECT_DIR/vault/_governance/PROJECT_RULES.md` exists.
3. Confirm `$CLAUDE_PROJECT_DIR/CLAUDE.md` was augmented (check for `<!-- mission-control:begin -->` marker).

If any are missing, the init was partial. Report the specific missing artifact to the operator. Do not claim success.

## Coordination With Other Modes

Add Mission-Control does NOT:
- modify CLAUDE.md beyond what `/mission-control init` does (which is itself idempotent between `<!-- mission-control:begin -->` markers).
- touch team composition, persona files, or `.claude/references/review-criteria.md`.
- run Health Check or Restructure audits.

If the operator wants those, they can run `gigo:maintain` again in the appropriate mode after mc is initialized.

## Vault Audit

Deferred to v2. v1 reports "active" status without auditing vault contents.
