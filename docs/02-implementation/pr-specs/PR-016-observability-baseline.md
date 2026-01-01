# PR-016: Observability Baseline (Spec)

**Status:** Spec Only  
**Depends on:** PR-001  
**Last Reviewed:** 2026-01-01

## Goal

Provide baseline observability with structured logs and a lightweight telemetry
endpoint.

## User Value

- Easier debugging of failures and performance issues.
- Clear visibility into DB health and migration status.

## References

- `docs/01-design/DESIGN_ARCHITECTURE.md`

## Scope

### In

- JSON structured logging with correlation IDs.
- Request logging middleware for API routes.
- Telemetry endpoint with health and basic metrics.
- Log redaction for secrets and tokens.

### Out

- Full distributed tracing or external telemetry exporters.
- Long-term metrics storage.

## Mini-Specs

- Log format includes `request_id`, `event`, `duration_ms`, `status`.
- Middleware assigns request IDs and injects into logs.
- `GET /api/v1/telemetry` returns JSON metrics:
  - DB connectivity
  - migration version
  - event queue size (if PR-013 exists)
  - agent run counts (if PR-014 exists)
- Redact tokens and email addresses from logs.

## User Stories

- As a developer, I can correlate logs by request ID.
- As a user, I can see a single endpoint with system health metrics.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- Logging config in `backend/logging.py` (or equivalent) with JSON formatter.
- Middleware attaches `request_id` to context and response headers.

### Data Model / Migrations

- N/A.

### API Contract

- `GET /api/v1/telemetry` returns JSON metrics.

### Background Jobs

- N/A.

### Security / Privacy

- Telemetry excludes PII and content payloads.

### Error Handling

- Telemetry endpoint degrades gracefully if optional subsystems are missing.

## Acceptance Criteria

### AC1: Structured Logging

**Success Criteria:**
- [ ] Logs are JSON and include `request_id` for API requests.

### AC2: Telemetry Endpoint

**Success Criteria:**
- [ ] `/api/v1/telemetry` returns JSON with DB health and migration version.

### AC3: Redaction

**Success Criteria:**
- [ ] Tokens and emails are redacted from logs.

## Test Plan

### Automated

- Unit tests for log formatter and redaction.
- Integration tests for telemetry endpoint response shape.

### Manual

- Trigger API requests and verify logs contain `request_id`.
- Call `/api/v1/telemetry` and verify metrics payload.

## Notes / Risks / Open Questions

- Decide whether to expose telemetry in production by default.
