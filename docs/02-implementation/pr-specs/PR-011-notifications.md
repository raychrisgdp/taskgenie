# PR-011: Notifications (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-29

## Goal

Deliver early “daily value” by reminding the user about tasks with ETAs (24h/6h/overdue), with a path that works both locally and in Docker.

## User Value

- Users feel the app helping them without needing integrations or RAG.
- Encourages regular usage (reminders + quick completion loop).

## Scope

### In

- Scheduling logic:
  - reminders at configured offsets (default 24h + 6h)
  - overdue alerts
  - quiet hours
  - dedup (don’t spam the same notification)
- Notification history persisted (so the UI can show “what was sent”).
- Delivery mechanism (pragmatic):
  - **Local run:** desktop notifications (e.g., `plyer`)
  - **Docker run:** provide an in-app notification channel (Web UI / API), with desktop as optional later

### Out

- Mobile notifications (future).
- Multi-device sync (future).

## References

- `docs/01-design/DESIGN_NOTIFICATIONS.md`
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md`
- `docs/01-design/REQUIREMENTS_AUDIT.md` (Docker notification constraints)

## User Stories

- As a user, I get reminders before tasks are due (24h/6h) and when they are overdue.
- As a user, I don’t get spammed (dedup + quiet hours).
- As a user running in Docker, I still see reminders (in-app channel).

## Technical Design

### Scheduler

- Run a periodic job (every 1–5 minutes) to compute due reminders.
- Use SQLite as the source of truth for what has already been sent.

### Storage

- Store a `notifications` table with:
  - `task_id`, `type`, `scheduled_for`, `sent_at`, `status`, `error`

### Delivery channels

- Local run: desktop notifications (plyer).
- Docker run: in-app notifications surfaced via API and rendered in UI(s).

### Dedup + quiet hours

- Dedup by `(task_id, type, scheduled_for)` to prevent repeats.
- Quiet hours delay delivery until the next allowed window.

## Acceptance Criteria

- [ ] Reminders trigger at 24h/6h offsets and for overdue tasks.
- [ ] Quiet hours are respected.
- [ ] Notification history is queryable (for UI and debugging).

## Test Plan

### Automated

- Unit: compute-next-notifications logic (boundary times, quiet hours, DST-safe behavior).
- Integration:
  1. Create task due in 24h → scheduler emits “due tomorrow”.
  2. Mark task done → scheduler does not notify again.
  3. Due time passes → overdue notification emitted once.

### Manual

1. Create a task due in ~10 minutes; temporarily set schedule to `["10m"]` for testing.
2. Run the scheduler job (or wait for interval).
3. Verify a notification appears and is recorded in history.
4. Mark task complete; ensure no further reminders fire.

## Notes / Risks / Open Questions

- Desktop notifications from Docker are non-trivial; plan for an “in-app notifications” channel as the reliable baseline.
