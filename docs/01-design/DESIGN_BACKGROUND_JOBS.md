# Background Jobs Design (No Queue for MVP)

**Status:** Spec Only  
**Last Reviewed:** 2025-12-29

## Goals

- Run periodic and asynchronous work without introducing a message queue for MVP.
- Keep behavior deterministic and debuggable (jobs and outcomes persisted in SQLite).
- Support local-first execution and Docker execution with minimal divergence.

## Non-Goals

- Distributed worker fleets, horizontal scaling, or exactly-once delivery guarantees.
- Running jobs across multiple nodes/containers simultaneously.

## Approach (MVP)

### Scheduler

- Use an in-process scheduler (APScheduler) started by the backend.
- Jobs run on an interval (e.g., every 1–5 minutes) and operate against SQLite.

### Persistence

- Persist job outcomes in SQLite tables (so UI and debugging can see what happened):
  - notification history / delivery attempts
  - attachment fetch attempts
  - embedding/indexing attempts

### “Queueing” without a queue

When many items need processing (e.g., 100 tasks due, 50 attachments to fetch), we “queue” by:
- selecting a batch from SQLite
- marking rows as “in_progress” with timestamps
- processing them in a controlled loop
- writing success/failure back to the DB

This is sufficient for a single-user instance and avoids Redis/Celery.

## Concurrency + Idempotency

- Jobs must be **idempotent** (safe to rerun).
- Use a simple lock to prevent overlapping runs:
  - DB lock row, or
  - process-level mutex (acceptable if single process), plus
  - “started_at / finished_at” timestamps for audit.

## Execution Options

### Default (recommended)

- Backend runs scheduler in-process (simplest operationally).

### Alternative (ops-friendly)

- Provide `tgenie worker` to run jobs in a separate process (systemd timer/cron).
- Useful if you don’t want the API process to own background work.

## Design References

- `docs/01-design/DESIGN_NOTIFICATIONS.md` (notification scheduling and UX)
- `docs/01-design/INTEGRATION_GUIDE.md` (provider pattern; fetch/caching)
- `docs/01-design/DESIGN_DATA.md` (storage, lifecycle)
