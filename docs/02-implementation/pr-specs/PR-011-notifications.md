# PR-011: Notifications (Spec)

**Status:** Spec Only  
**Depends on:** PR-002  
**Last Reviewed:** 2025-12-30

## Goal

Deliver early "daily value" by reminding user about tasks with ETAs (24h/6h/overdue), with a path that works both locally and in Docker.

## User Value

- Users feel app helping them without needing integrations or RAG.
- Encourages regular usage (reminders + quick completion loop).

## Scope

### In

- Scheduling logic:
  - reminders at configured offsets (default 24h + 6h)
  - overdue alerts
  - quiet hours
  - dedup (don't spam same notification)
- Notification history persisted (so UI can show "what was sent").
- Delivery mechanism (pragmatic):
  - **Local run:** desktop notifications (e.g., `plyer`)
  - **Docker run:** provide an in-app notification channel (Web UI / API), with desktop as optional later
- Scheduler runs every 1-5 minutes (configurable).

### Out

- Mobile notifications (future).
- Multi-device sync (future).

## Mini-Specs

- Data model:
  - `notifications` table to persist delivery history (type, task_id, sent_at, channel, status, error).
- Scheduler:
  - in-process tick loop (APScheduler or background task), configurable interval (default 60s).
  - computes due reminders (24h/6h/overdue) for non-completed tasks with `eta`.
  - deduplication via persisted history (no repeated sends for same task/type).
- Delivery channels:
  - local dev: desktop notifications (e.g., `plyer`)
  - Docker: in-app notification feed (API-backed) as the reliable baseline
- UX:
  - quiet hours support (defer or suppress)
  - clear “why did I get this?” content (task title + due time + shortcut to open task)
- Tests:
  - time-based computations, deduplication, quiet hours, and Docker/local channel selection.

## References

- `docs/01-design/DESIGN_NOTIFICATIONS.md`
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md`
- `docs/01-design/REQUIREMENTS_AUDIT.md` (Docker notification constraints)

## Technical Design

### Scheduler Implementation

- **Background Worker:** Use `asyncio.create_task` or a separate process started on app startup.
- **Precision:** Run every 60 seconds.
- **Logic:**
  1. Query `tasks` where `status != 'completed'` and `eta` is not null.
  2. For each task, check if a notification of type (24h, 6h, overdue) has already been sent (check `notifications` table).
  3. If not sent and `now() >= eta - offset`, trigger delivery.
- **Delivery:**
  - `DesktopNotifier`: wrapper around `plyer` for local notifications.
  - `InAppNotifier`: inserts into `notifications` table with `status='unread'`.

### Notification Delivery Channels

- Implement a `NotificationService` that exposes a single “tick” operation:
  - query due tasks
  - compute which reminder types should fire
  - write delivery history (dedup)
  - dispatch via the configured channel(s)
- Implement channel adapters:
  - `DesktopNotifier` (local) wraps `plyer`
  - `InAppNotifier` persists a notification record for UI/TUI to display

## Acceptance Criteria

- [ ] Reminders fire at default offsets (24h/6h) and for overdue tasks.
- [ ] No duplicate notifications for the same task/type (dedup persisted).
- [ ] Quiet hours are respected (defer or suppress, per config).
- [ ] Docker mode uses in-app notifications as the baseline channel.
- [ ] Notification history is persisted and queryable (for UI/TUI listing).

## Test Plan

### Automated

- Unit (pure logic): given `(now, eta, offsets, history)` compute which notifications should fire.
- Integration (DB): history persistence prevents duplicates across ticks/restarts.
- Channel selection: local run uses desktop channel; Docker run uses in-app channel.
- Quiet hours: notifications are suppressed/deferred during quiet window.

### Manual

1. Create a task due in ~10 minutes; temporarily set schedule to `["10m"]` for testing.
2. Run scheduler job (or wait for interval).
3. Verify a notification appears and is recorded in history.
4. Mark task complete; ensure no further reminders fire.

## Notes / Risks / Open Questions

- Desktop notifications from Docker are non-trivial; plan for an "in-app notifications" channel as a reliable baseline.
