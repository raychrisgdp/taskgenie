# PR-011: Notifications (Spec)

**Status:** Spec Only  
**Depends on:** PR-002 (agent notifications optional: PR-003B, PR-014)  
**Last Reviewed:** 2025-12-30

## Goal

Deliver reminders for tasks with ETAs (24h/6h/overdue) with a path that works locally
and in Docker.

## User Value

- Users get timely reminders without external integrations.
- Encourages regular task completion.

## References

- `docs/01-design/DESIGN_NOTIFICATIONS.md`
- `docs/01-design/DESIGN_BACKGROUND_JOBS.md`
- `docs/01-design/REQUIREMENTS_AUDIT.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/01-design/DESIGN_CLI.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Scheduler logic for reminders and overdue alerts.
- Quiet hours and deduplication.
- Persisted notification history for UI/TUI viewing.
- Delivery channels: local desktop notifications and in-app feed for Docker.
- Optional agent-run notifications (started/completed/failed) when agent system exists (requires PR-003B and PR-014).

### Out

- Mobile notifications.
- Multi-device sync.

## Mini-Specs

- `notifications` table to store delivery history and status.
- In-process scheduler tick (default 60s) to compute due reminders.
- Channel adapters for desktop (local) and in-app notifications.
- In-app API to list notifications for UI/TUI.
- Notification types for agent runs and tool failures (depends on PR-003B/PR-014).

## User Stories

- As a user, I get reminders before tasks are due and when they are overdue.
- As a user, I can see a history of notifications in the app.
- As a user, notifications respect quiet hours.
- As a user, I can see when an agent run completes or fails.

## UX Notes (if applicable)

- Notifications should explain why they fired (task title + due time).

## Technical Design

### Architecture

- Background task or scheduler runs on app startup and calls a `NotificationService`.
- `NotificationService` computes due reminders, persists history, and dispatches
  through configured channels.

### Data Model / Migrations

- `notifications` table: id, task_id, type, channel, status, error, sent_at,
  created_at.

### API Contract

- `GET /api/v1/notifications` returns recent notifications for UI/TUI.
- `PATCH /api/v1/notifications/{id}` marks as read (optional).

### Background Jobs

- In-process scheduler runs every 60s (configurable).

### Security / Privacy

- Do not log notification content beyond metadata.

### Error Handling

- Delivery failures are stored with error reason and do not stop the scheduler.

## Acceptance Criteria

### AC1: Scheduling and Overdue

**Success Criteria:**
- [ ] Reminders fire at configured offsets and for overdue tasks.

### AC2: Deduplication and History

**Success Criteria:**
- [ ] No duplicate notifications for the same task/type.
- [ ] Notification history is persisted and queryable.

### AC3: Delivery Channels

**Success Criteria:**
- [ ] Docker mode uses in-app notifications as the baseline channel.
- [ ] Local mode can use desktop notifications.

### AC4: Quiet Hours

**Success Criteria:**
- [ ] Quiet hours suppress or defer notifications per config.

## Test Plan

### Automated

- Unit tests for schedule computation and quiet hours.
- Integration tests for history persistence and dedup across restarts.
- Channel selection tests for local vs Docker mode.

### Manual

- Configure a short offset and verify reminders fire.
- Run in Docker and confirm in-app notifications appear.

## Notes / Risks / Open Questions

- Desktop notifications from Docker are unreliable; in-app feed is the baseline.
- Agent notifications depend on agent run APIs and may be staged after PR-003B.
