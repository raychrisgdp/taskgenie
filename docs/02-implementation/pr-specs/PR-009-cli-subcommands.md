# PR-009: CLI Subcommands (Secondary) (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-29

## Goal

Provide non-interactive commands for scripting and automation, while keeping the interactive TUI as the primary UX.

## User Value

- Users can automate workflows (`cron`, shell scripts, quick one-liners).
- Enables easy debugging of API behavior without the TUI.

## Scope

### In

- Subcommands (initial set):
  - `tgenie add`
  - `tgenie list`
  - `tgenie show`
  - `tgenie edit`
  - `tgenie done`
  - `tgenie delete`
- Output conventions:
  - human-friendly default
  - optional `--json` for scripting (recommended)

### Out

- Full import/export formats (can be added later).
- Power-user TUI features (PR-008 iteration).

## References

- `docs/01-design/DESIGN_CLI.md` (command UX and flags)
- `docs/01-design/API_REFERENCE.md` (API endpoints)
- `docs/01-design/DESIGN_TUI.md` (division of responsibilities: TUI vs subcommands, keybindings, screen layout)
- `docs/02-implementation/pr-specs/PR-008-interactive-tui.md` (TUI implementation)

## Technical Design

- Thin client: subcommands call the API, not the DB directly.
- Provide stable scripting behavior:
  - exit code `0` on success, non-zero on errors
  - `--json` prints machine-readable output only (no extra formatting)
- Prefer consistent flags across commands (e.g., `--status`, `--priority`, `--eta`).

## Acceptance Criteria

- [ ] Core subcommands work end-to-end against the API.
- [ ] `--json` output is valid and stable for scripting (where provided).
- [ ] Helpful errors on API-down or invalid arguments.

## Test Plan

### Automated

- Unit: argument parsing and output formatting.
- Integration: run command handlers against a test app/client.

### Manual

1. Start API.
2. Run:
   - `tgenie add "Test task"`
   - `tgenie list`
   - `tgenie show <id>`
   - `tgenie done <id>`
3. Stop API; verify commands fail with clear guidance.

## Notes / Risks / Open Questions

- Align `DESIGN_CLI.md` command examples with `tgenie` before implementation to avoid drift.
