# PR-016: Observability Baseline (Spec)

**Status:** Spec Only  
**Depends on:** PR-001  
**Last Reviewed:** 2026-01-03

## Goal

Provide baseline observability with structured logs and a lightweight telemetry
endpoint.

## User Value

- Easier debugging of failures and performance issues.
- Clear visibility into DB health and migration status.

## References

- `docs/01-design/DESIGN_ARCHITECTURE.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_ARCHITECTURE.md`

## Scope

### In

- JSON structured logging for API + CLI output.
- Request correlation IDs (propagate via `X-Request-Id`).
- Request logging middleware for API routes.
- Telemetry endpoint with app + DB health basics.
- Log redaction for secrets, tokens, and emails.
- Document new env vars and telemetry usage in user docs.

### Out

- Distributed tracing or external exporters.
- Long-term metrics storage or dashboards.
- Authz/authn for telemetry (local-only MVP).

## Mini-Specs

- Logging is configured in a dedicated module (e.g., `backend/logging.py`) and used by
  both CLI and API startup.
- Log output is JSON lines with at minimum:
  - `timestamp` (ISO 8601, UTC)
  - `level` (e.g., INFO)
  - `logger`
  - `message`
  - `event` (e.g., `http_request`, `http_error`)
  - `request_id` (null outside request context)
  - Request logs additionally include `method`, `path`, `status`, `duration_ms`
- Request ID handling:
  - If `X-Request-Id` header is present and safe (length <= 128, ASCII), reuse it.
  - Otherwise generate a UUID4.
  - Always echo `X-Request-Id` in the response headers.
- Request logging middleware:
  - Logs a single `http_request` event per request.
  - Logs `http_error` with stack trace for unhandled exceptions.
  - Does not log request/response bodies.
- Redaction filter:
  - Key-based redaction for `authorization`, `token`, `api_key`, `password`, `secret`, `cookie`,
    `set-cookie`, `email` (case-insensitive).
  - Email addresses in string values are replaced with `[redacted-email]`.
  - If query params are logged, redact any sensitive keys.
- `GET /api/v1/telemetry` returns JSON metrics:
  - `status`: `ok` or `degraded`
  - `version` and `uptime_s`
  - `db.connected` (bool) and `db.migration_version` (string or null)
  - Optional metrics return `null` when unavailable:
    - `event_queue_size` (PR-013)
    - `agent_runs_active` (PR-014)

## User Stories

- As a developer, I can correlate logs by request ID.
- As a user, I can see a single endpoint with system health metrics.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- Logging config in `backend/logging.py` (or equivalent) with JSON formatter and redaction filter.
- Middleware attaches `request_id` to context and response headers.
- Telemetry route in a small API module (e.g., `backend/api/v1/telemetry.py`) and registered in `backend/main.py`.

### Configuration

- Add settings:
  - `log_level` (`LOG_LEVEL`): default `INFO`, `DEBUG` when `settings.debug=True`.
  - `telemetry_enabled` (`TELEMETRY_ENABLED`): default `True`.
  - `log_file_path` (`LOG_FILE_PATH`): default `{app_data_dir}/logs/taskgenie.jsonl`.
- When `log_file_path` is set, write logs to both stdout and the file (rotate to avoid unbounded growth).

### Data Model / Migrations

- N/A.

### API Contract

- `GET /api/v1/telemetry` returns JSON metrics (always 200; status reported in payload).
- Example response:
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "uptime_s": 1234,
    "db": {
      "connected": true,
      "migration_version": "b63be8e"
    },
    "optional": {
      "event_queue_size": null,
      "agent_runs_active": null
    }
  }
  ```

### Background Jobs

- N/A.

### Security / Privacy

- Telemetry excludes PII and content payloads (no task titles, notes, or file paths).
- Logs avoid request/response bodies and redact sensitive fields.

### Error Handling

- Telemetry endpoint degrades gracefully if optional subsystems are missing.
- If DB check fails, return `status="degraded"` and include a safe error string.

## Acceptance Criteria

### AC1: Structured Logging

**Success Criteria:**
- [ ] Logs are JSON and include `request_id` for API requests.
- [ ] `http_request` logs include `method`, `path`, `status`, and `duration_ms`.

### AC2: Telemetry Endpoint

**Success Criteria:**
- [ ] `/api/v1/telemetry` returns JSON with DB health and migration version.
- [ ] Optional metrics are present with `null` values when unavailable.

### AC3: Redaction

**Success Criteria:**
- [ ] Tokens and emails are redacted from logs.
- [ ] `X-Request-Id` is echoed in response headers.

## Test Plan

### Automated

- Unit tests for JSON log formatter and redaction filter.
- Middleware test for request ID propagation and request log fields.
- Integration tests for telemetry endpoint response shape and degraded status.

### Manual

- Trigger API requests and verify logs contain `request_id`.
- Call `/api/v1/telemetry` and verify metrics payload.

## Notes / Risks / Open Questions

- Confirm default for `TELEMETRY_ENABLED` in production (proposed: enabled by default).
