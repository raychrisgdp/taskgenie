# PR-009: CLI Subcommands (Secondary) (Spec)

**Status:** Spec Only  
**Depends on:** PR-002, PR-003B, PR-014  
**Last Reviewed:** 2025-12-29

## Goal

Provide non-interactive commands for scripting while the TUI remains primary.

## User Value

- Users can automate workflows in shell scripts or cron.
- Developers can debug API behavior without the TUI.

## References

- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`
- `docs/01-design/DESIGN_TUI.md`
- `docs/02-implementation/pr-specs/PR-008-interactive-tui.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- `tgenie add|list|show|edit|done|delete` subcommands.
- `tgenie agent run` and `tgenie agent status` for autonomous workflows.
- Human-friendly output with optional `--json` for scripting.
- Commands call the API, not the DB directly.
- Stable exit codes and clear error messages.

### Out

- Import/export formats.
- Advanced TUI power-user features.

## Mini-Specs

- Typer-based CLI under `backend/cli/main.py`.
- Consistent flags across commands (status, priority, eta, tags).
- `--json` output for list/show/add/edit where useful.
- Exit codes for API errors and invalid args.
- `tgenie agent run "<goal>"` starts a run and returns a run ID.
- `tgenie agent status <run_id>` prints status (supports `--json`).

## User Stories

- As a user, I can add and list tasks from shell scripts.
- As a user, I can request machine-readable output with `--json`.
- As a user, I get clear errors when the API is down.
- As a user, I can run an agent goal from the CLI and check its status.

## UX Notes (if applicable)

- Keep output stable and minimal in `--json` mode.

## Technical Design

### Architecture

- Typer command group `tgenie` that delegates to a shared API client.
- Output formatter for human vs JSON output.

### Data Model / Migrations

- N/A.

### API Contract

- Uses PR-002 task endpoints.

### Background Jobs

- N/A.

### Security / Privacy

- N/A.

### Error Handling

- Non-zero exit codes on API/network errors.
- Actionable messages for 404/409/500 responses.

## Acceptance Criteria

### AC1: Core Subcommands

**Success Criteria:**
- [ ] Add/list/show/edit/done/delete work against the API.

### AC2: JSON Output

**Success Criteria:**
- [ ] `--json` output is valid JSON with no extra formatting.

### AC3: Errors and Exit Codes

**Success Criteria:**
- [ ] API errors and network failures return non-zero exit codes.

### AC4: Agent Run Commands

**Success Criteria:**
- [ ] `tgenie agent run` starts an agent run and returns a run ID.
- [ ] `tgenie agent status` returns the current state of a run.

## Test Plan

### Automated

- CLI runner tests for command behavior and JSON output.
- Mocked API failures to validate exit codes.
- Agent CLI tests with mocked agent service responses.

### Manual

- Run commands against a live API and verify output.

## Notes / Risks / Open Questions

- Ensure CLI flags align with TUI field names and API enums.
- Agent commands depend on PR-003B and PR-014 (agent run API contract).
