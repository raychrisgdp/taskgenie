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
- [ ] Automated tests cover scheduling + dedup + quiet hours (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

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

### Manual Test Checklist

- [ ] A due task generates exactly one `due_24h`/`due_6h` notification across multiple ticks.
- [ ] Quiet hours suppress/defer notifications as configured.
- [ ] Overdue tasks generate an overdue notification (once).
- [ ] Docker mode uses to-in-app channel reliably (no desktop dependency).
- [ ] Notification history persists across restarts and remains queryable.
- [ ] Update `.env.example` to add `NOTIFICATIONS_ENABLED`, `NOTIFICATION_SCHEDULE` variables.

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Desktop notifications from Docker are non-trivial; plan for an "in-app notifications" channel as a reliable baseline.

---

## Skill Integration: task-workflow

### Notification Workflow Patterns

This PR should follow **task-workflow** skill patterns for notification operations:

**Notification Lifecycle Workflow**
```
┌──────────────┐
│  Task Due   │
│  (24h/6h)    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Notification    │
│ Service       │
│ Computes &     │
│ Dedups        │
└──────┬───────┘
       │
       ├──►────────────┐
       │             │
┌──────▼───┐   ┌────────────▼┐
│ Desktop   │   │ In-App      │
│ Notifier  │   │ Notifier     │
│ (plyer)   │   │ (DB)         │
└───────────┘   └──────────────┘
       │             │
       ▼             ▼
┌──────────────┐ ┌──────────────┐
│ User sees   │ │ UI displays   │
│ popup       │ │ notifications │
└──────────────┘ └──────────────┘
```

### Notification Types

| Type | Trigger | Timing | Channels |
|-------|----------|--------|-----------|
| `due_24h` | ETA - 24 hours | Desktop, In-App |
| `due_6h` | ETA - 6 hours | Desktop, In-App |
| `due_overdue` | ETA passed | Desktop, In-App |
| `completed` | Task marked done | In-App |

### Service Layer

```python
# backend/services/notification_service.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from backend.models.task import Task
from backend.models.notification import Notification


class NotificationService:
    """Service for notification management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.desktop_notifier = DesktopNotifier()
        self.in_app_notifier = InAppNotifier(db)

    async def compute_due_notifications(
        self, task: Task, now: datetime
    ) -> list[str]:
        """Compute which notifications should fire for a task."""
        if not task.eta or task.status == "completed":
            return []

        notifications = []
        time_diff = (task.eta - now).total_seconds()

        # 24 hours before
        if 82800 <= time_diff < 90000:  # 23-25 hours
            notifications.append("due_24h")

        # 6 hours before
        elif 18000 <= time_diff < 23400:  # 5.5-6.5 hours
            notifications.append("due_6h")

        # Overdue
        elif time_diff < 0:
            notifications.append("due_overdue")

        return notifications

    async def process_task(
        self, task: Task, now: datetime
    ) -> list[Notification]:
        """Process a task and create notifications if needed."""
        notification_types = await self.compute_due_notifications(task, now)

        created = []

        for notif_type in notification_types:
            # Check if already sent
            existing = await self.db.execute(
                select(Notification)
                    .where(
                        Notification.task_id == task.id,
                        Notification.type == notif_type,
                        Notification.status == "sent",
                    )
            ).scalar_one_or_none()

            if not existing:
                # Create notification
                notification = Notification(
                    task_id=task.id,
                    type=notif_type,
                    scheduled_for=task.eta,
                    status="pending",
                )
                self.db.add(notification)
                created.append(notification)

        if created:
            await self.db.commit()

        return created

    async def deliver_pending(self, now: datetime):
        """Deliver all pending notifications."""
        pending = await self.db.execute(
            select(Notification)
                .where(Notification.status == "pending")
                .where(Notification.scheduled_for <= now)
        ).scalars().all()

        delivered = []

        for notification in pending:
            # Check quiet hours
            if not self._is_quiet_hour(notification.scheduled_for):
                # Deliver via appropriate channel
                if self._use_desktop_notifications():
                    self.desktop_notifier.send(notification)
                else:
                    self.in_app_notifier.send(notification)

                notification.status = "sent"
                notification.sent_at = now
                notification.delivered_via = notification.delivery_channel
                delivered.append(notification)

        if delivered:
            await self.db.commit()

        return delivered

    def _use_desktop_notifications(self) -> bool:
        """Check if desktop notifications are available."""
        # Can check OS and whether running in Docker
        import platform
        if platform.system() == "Linux":
            # Check if running in Docker
            try:
                with open("/.dockerenv") as f:
                    # In Docker - use in-app notifications
                    return False
            except FileNotFoundError:
                # Not in Docker - use desktop
                return True
        return True

    def _is_quiet_hour(self, time: datetime) -> bool:
        """Check if current time is in quiet hours."""
        quiet_start = time.replace(hour=22, minute=0, second=0)  # 10 PM
        quiet_end = time.replace(hour=7, minute=0, second=0) + timedelta(days=1)  # 7 AM next day
        return quiet_start <= time <= quiet_end


notification_service = NotificationService
```

### Deduplication Strategy

```python
# Check notification history before creating new
existing = await db.execute(
    select(Notification)
        .where(
            Notification.task_id == task_id,
            Notification.type == "due_24h",
            Notification.status == "sent",
            Notification.sent_at >= datetime.now() - timedelta(hours=12)  # Don't repeat within 12h
        )
).scalar_one_or_none()

if not existing:
    # Create notification
    pass
```

### Testing Patterns

**Scheduler Logic Tests**
```python
# tests/test_services/test_notification_service.py
import pytest
from datetime import datetime, timedelta

class TestNotificationComputation:
    def test_due_24h_trigger(self):
        """Notification triggers 24 hours before due."""
        now = datetime(2025, 1, 15, 10, 0, 0)
        eta = datetime(2025, 1, 16, 10, 0, 0)  # 24 hours later

        task = Task(id="1", eta=eta)
        notifs = notification_service.compute_due_notifications(task, now)

        assert "due_24h" in notifs

    def test_due_6h_trigger(self):
        """Notification triggers 6 hours before due."""
        now = datetime(2025, 1, 15, 10, 0, 0)
        eta = datetime(2025, 1, 15, 16, 0, 0)  # 6 hours later

        task = Task(id="1", eta=eta)
        notifs = notification_service.compute_due_notifications(task, now)

        assert "due_6h" in notifs

    def test_overdue_trigger(self):
        """Notification triggers for overdue tasks."""
        now = datetime(2025, 1, 16, 0, 0, 0)
        eta = datetime(2025, 1, 15, 10, 0, 0)  # 1 hour ago

        task = Task(id="1", eta=eta)
        notifs = notification_service.compute_due_notifications(task, now)

        assert "due_overdue" in notifs

    def test_completed_no_notification(self):
        """Completed tasks don't trigger notifications."""
        now = datetime(2025, 1, 15, 10, 0, 0)
        eta = datetime(2025, 1, 14, 10, 0, 0)  # 1 day ago

        task = Task(id="1", eta=eta, status="completed")
        notifs = notification_service.compute_due_notifications(task, now)

        assert len(notifs) == 0
```

**Deduplication Tests**
```python
class TestNotificationDeduplication:
    @pytest.mark.asyncio
    async def test_same_notification_not_sent_twice(self, db_session):
        """Same notification type not sent twice within 12 hours."""
        # Create first notification
        notif1 = Notification(task_id="1", type="due_24h", status="sent")
        db_session.add(notif1)
        await db_session.commit()

        # Try to create again (should be skipped)
        notifs = await notification_service.process_task(
            task=Task(id="1", eta=datetime.utcnow() + timedelta(hours=24)),
            now=datetime.utcnow()
        )

        assert len(notifs) == 0  # Dedup should prevent second send
```

**Quiet Hours Tests**
```python
class TestQuietHours:
    def test_notification_suppressed_in_quiet_hours(self):
        """Notifications suppressed between 10 PM and 7 AM."""
        now = datetime(2025, 1, 15, 23, 0, 0)  # 11 PM - in quiet hours
        eta = datetime(2025, 1, 16, 0, 0, 0)  # Due in quiet hours

        is_quiet = notification_service._is_quiet_hour(now)

        assert is_quiet is True

    def test_notification_allowed_outside_quiet_hours(self):
        """Notifications allowed outside quiet hours."""
        now = datetime(2025, 1, 15, 9, 0, 0)  # 9 AM - outside quiet hours

        is_quiet = notification_service._is_quiet_hour(now)

        assert is_quiet is False
```

### Data Model

**Notification Fields**
```python
# backend/models/notification.py
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # due_24h, due_6h, due_overdue, completed
    scheduled_for = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed
    delivered_via = Column(String(20), nullable=True)  # desktop, in_app
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Error Handling

| Error | Recovery |
|-------|-----------|
| Desktop notify failed | Log error, deliver via in-app |
| In-app notify failed | Log error, mark notification as failed |
| Task already completed | Skip notification, mark as skipped |
| Scheduler stopped | Restart on next API call |

**See Also**
- Skill doc: `.opencode/skill/task-workflow/`
- Reference: docs/01-design/DESIGN_NOTIFICATIONS.md
