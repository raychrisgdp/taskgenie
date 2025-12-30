# Notification System Design

## Overview

The notification system ensures users never miss important task deadlines. It provides **timely, actionable desktop notifications** with the ability to directly interact with tasks.

## Notification Types

### 1. Deadline Reminders

**Triggers:**
- 24 hours before ETA (if task not complete)
- 6 hours before ETA (if task not complete)
- 1 hour before ETA (optional, user-configured)

**Example:**
```bash
┌─────────────────────────────────────┐
│ 🔔 Task Due Tomorrow                │
│                                 │
│ Review PR #123                    │
│ Due: Wed, Jan 15 at 2:00 PM    │
│ Priority: High                    │
│                                 │
│ [View Task] [Mark Done] [Snooze]│
└─────────────────────────────────────┘
```

### 2. Overdue Alerts

**Triggers:**
- Immediately when ETA passes (if task not complete)
- Recheck every hour until marked done or snoozed

**Example:**
```bash
┌─────────────────────────────────────┐
│ ⚠️ Task Overdue!                 │
│                                 │
│ Review PR #123                    │
│ Was due: Wed, Jan 15 at 2:00 PM  │
│ Status: Pending                    │
│                                 │
│ [View Task] [Mark Done] [Snooze 1hr]│
└─────────────────────────────────────┘
```

### 3. System Notifications

**Triggers:**
- Task created
- Task completed
- Attachment added
- Sync completed
- Error occurred

**Example:**
```bash
┌─────────────────────────────────────┐
│ ✅ Task Completed                 │
│                                 │
│ Review PR #123                    │
│ Marked done at 3:30 PM          │
│                                 │
│ [View Details] [Undo]           │
└─────────────────────────────────────┘
```

## Notification System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Scheduler Service                        │
│  ┌──────────────────────────────────────────────┐    │
│  │ Check every 5 minutes for due tasks   │    │
│  │ Query: WHERE eta <= NOW() + 24h     │    │
│  │ AND eta > NOW()                      │    │
│  │ AND status != 'completed'             │    │
│  │ AND notification_24h not sent       │    │
│  └──────────────────────────────────────────────┘    │
│                        │                              │
│                        ▼                              │
│  ┌──────────────────────────────────────────────┐    │
│  │ Check for overdue tasks             │    │
│  │ Query: WHERE eta < NOW()            │    │
│  │ AND status != 'completed'           │    │
│  │ AND last_notification > 1 hour ago   │    │
│  └──────────────────────────────────────────────┘    │
│                        │                              │
│                        ▼                              │
│  ┌──────────────────────────────────────────────┐    │
│  │ Send notification                   │    │
│  │ - Generate notification record        │    │
│  │ - Call desktop notify API          │    │
│  │ - Update sent_at timestamp        │    │
│  └──────────────────────────────────────────────┘    │
│                        │                              │
│                        ▼                              │
│              Desktop Notify (plyer)                      │
│                        │                              │
│                        ▼                              │
│                 User sees notification                      │
│                        │                              │
│                        ▼                              │
│  ┌──────────────────────────────────────────────┐    │
│  │ User clicks notification            │    │
│  │ - Open task detail page/web UI   │    │
│  │ - Update notification status      │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Database Schema (Notifications Table)

```sql
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    task_id VARCHAR(36) NOT NULL,
    type VARCHAR(20) NOT NULL,  -- due_24h, due_6h, overdue
    scheduled_at DATETIME NOT NULL,
    sent_at DATETIME,
    clicked_at DATETIME,
    action_taken VARCHAR(50),  -- 'viewed', 'completed', 'dismissed'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, sent, clicked, dismissed
    retry_count INT DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_task ON notifications(task_id);
```

## Scheduling Logic

### Python Implementation

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()

async def check_due_tasks():
    """Check for tasks needing notification"""
    now = datetime.utcnow()

    # Check 24h reminder
    tasks_24h = await db.fetch_tasks_due_between(
        start=now + timedelta(hours=24) - timedelta(minutes=5),
        end=now + timedelta(hours=24)
    )

    for task in tasks_24h:
        if not await notification_exists(task.id, 'due_24h'):
            await create_notification(task.id, 'due_24h', task.eta)

    # Check 6h reminder
    tasks_6h = await db.fetch_tasks_due_between(
        start=now + timedelta(hours=6) - timedelta(minutes=5),
        end=now + timedelta(hours=6)
    )

    for task in tasks_6h:
        if not await notification_exists(task.id, 'due_6h'):
            await create_notification(task.id, 'due_6h', task.eta)

    # Check overdue
    overdue_tasks = await db.fetch_overdue_tasks(limit=10)

    for task in overdue_tasks:
        last_notif = await db.get_last_notification(task.id)
        if not last_notif or (now - last_notif.sent_at) > timedelta(hours=1):
            await create_notification(task.id, 'overdue', now)

async def create_notification(task_id, notif_type, scheduled_at):
    """Create and send notification"""
    # Create DB record
    notif_id = await db.create_notification({
        'task_id': task_id,
        'type': notif_type,
        'scheduled_at': scheduled_at,
        'status': 'pending'
    })

    # Get task details
    task = await db.get_task(task_id)

    # Build notification content
    content = build_notification_content(task, notif_type)

    # Send via plyer
    from plyer import notification
    notification.notify(
        title=content['title'],
        message=content['message'],
        app_name='Personal TODO',
        app_icon='/path/to/icon.png',
        timeout=10
    )

    # Update as sent
    await db.update_notification(notif_id, {
        'sent_at': datetime.utcnow(),
        'status': 'sent'
    })

# Schedule to run every 5 minutes
scheduler.add_job(check_due_tasks, 'interval', minutes=5)
scheduler.start()
```

## Desktop Notification (plyer)

### Configuration

```python
from plyer import notification

def send_notification(task, notif_type):
    """Send desktop notification"""

    titles = {
        'due_24h': '🔔 Task Due Tomorrow',
        'due_6h': '⏰ Task Due in 6 Hours',
        'overdue': '⚠️ Task Overdue!',
        'created': '✅ Task Created',
        'completed': '✅ Task Completed'
    }

    messages = {
        'due_24h': f'{task.title}\nDue: {format_date(task.eta)}\nPriority: {task.priority}',
        'due_6h': f'{task.title}\nDue in 6 hours\nPriority: {task.priority}',
        'overdue': f'{task.title}\nWas due: {format_date(task.eta)}\nStatus: {task.status}',
        'created': f'Task: {task.title}\nETA: {format_date(task.eta)}',
        'completed': f'{task.title}\nCompleted at {format_datetime(datetime.now())}'
    }

    # Send notification with actions
    notification.notify(
        title=titles[notif_type],
        message=messages[notif_type],
        app_name='Personal TODO',
        app_icon='/app/icon.png',
        timeout=10,
        # Some OS support actions
        app_name='Personal TODO'
    )
```

### Action Buttons (Platform-specific)

#### Linux (libnotify)
```python
# Using notify-send for action buttons
import subprocess

def send_notification_with_actions(task):
    subprocess.run([
        'notify-send',
        '-a', 'Personal TODO',
        '-i', '/app/icon.png',
        f'Task Due Tomorrow',
        f'{task.title}\nDue: {task.eta}',
        '--action=action:view,View Task,http://localhost:8080/tasks/{task.id}',
        '--action=action:done,Mark Done,http://localhost:8080/api/tasks/{task.id}/done'
    ])
```

#### macOS (terminal-notifier)
```python
from pync import Notifier

def send_notification_with_actions(task):
    Notifier.notify(
        title='Task Due Tomorrow',
        message=f'{task.title}\nDue: {task.eta}',
        app_icon='/app/icon.png',
        open='http://localhost:8080/tasks/{task.id}',
        execute=['tgenie', 'done', task.id]
    )
```

#### Windows (win10toast)
```python
from win10toast import ToastNotifier

def send_notification_with_actions(task):
    toaster = ToastNotifier()
    toaster.show_toast(
        'Task Due Tomorrow',
        f'{task.title}\nDue: {task.eta}',
        duration='long',
        icon_path='/app/icon.png',
        threaded=True,
        on_click=lambda: open_browser(f'http://localhost:8080/tasks/{task.id}')
    )
```

## Notification Templates

### Due Tomorrow (24h)
```
Title: 🔔 Task Due Tomorrow

Body: {task_title}
Due: {day_of_week}, {month} {day} at {time}
Priority: {priority}

Actions:
  [View Task] → Opens task detail
  [Mark Done] → Marks task complete
  [Snooze] → Remind in 1 hour
```

### Due Soon (6h)
```
Title: ⏰ Task Due in 6 Hours

Body: {task_title}
Due: Today at {time}
Priority: {priority}

Actions:
  [View Task] → Opens task detail
  [Mark Done] → Marks task complete
  [Start Now] → Marks in progress, opens task
```

### Overdue
```
Title: ⚠️ Task Overdue!

Body: {task_title}
Was due: {day_of_week}, {month} {day} at {time}
Status: {status}

Actions:
  [View Task] → Opens task detail
  [Mark Done] → Marks task complete
  [Snooze 1hr] → Remind again in 1 hour
```

## User Preferences

### Configuration

```python
class NotificationConfig(BaseModel):
    enabled: bool = True
    schedule: List[str] = ["24h", "6h"]  # ["24h", "6h", "1h"]
    sound_enabled: bool = True
    sound_file: Optional[str] = None
    quiet_hours: Optional[Dict[str, str]] = None  # {"start": "22:00", "end": "08:00"}
    max_notifications_per_hour: int = 5
```

### Settings UI

```
🔔 Notifications
┌─────────────────────────────────────────────────────────┐
│ Enable notifications:  [☑️ Enabled]              │
│                                                   │
│ Remind me before tasks are due:                │
│ [☑️ 24 hours before]                              │
│ [☑️ 6 hours before]                               │
│ [☐ 1 hour before]                                 │
│                                                   │
│ Sound:  [☑️ Enabled]  [Default 🔔 ▼]        │
│                                                   │
│ Quiet hours:                                       │
│ [☐ Enabled]                                       │
│  From: [10:00 PM ▼]  To: [08:00 AM ▼]        │
│                                                   │
│ Maximum notifications: [10 per hour ▼]            │
│                                                   │
│ Test Notification: [Send Test]                      │
└─────────────────────────────────────────────────────────┘
```

## Notification History

### Database Query
```python
async def get_notification_history(limit=20):
    """Get recent notifications for user"""
    return await db.fetch("""
        SELECT n.*, t.title, t.eta, t.priority
        FROM notifications n
        JOIN tasks t ON n.task_id = t.id
        ORDER BY n.scheduled_at DESC
        LIMIT ?
    """, limit)
```

### History Display (Web UI)
```
Notification History
┌─────────────────────────────────────────────────────────┐
│  Today (5 notifications)                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 10:30 AM • 📅 Task Due Tomorrow          │  │
│  │ Review PR #123 [high]                        │  │
│  │ [View] [Mark Done]                              │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 2:00 PM • ⏰ Task Due in 6 Hours         │  │
│  │ Send project update [medium]                     │  │
│  │ [View] [Mark Done]                              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Error Handling & Retry

### Failed Notifications

```python
async def send_notification_with_retry(notif_id, max_retries=3):
    notif = await db.get_notification(notif_id)

    for attempt in range(max_retries):
        try:
            send_desktop_notification(notif)
            await db.update_notification(notif_id, {
                'status': 'sent',
                'sent_at': datetime.utcnow()
            })
            return
        except Exception as e:
            if attempt == max_retries - 1:
                await db.update_notification(notif_id, {
                    'status': 'failed',
                    'error_message': str(e)
                })
            else:
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
```

## Privacy Considerations

### Data Handling
- Task titles and metadata used in notifications
- No sensitive information exposed
- All notifications stored locally
- No cloud notification service (local only)

### Permissions
- Request desktop notification permission on first use
- Respect OS notification preferences
- Quiet hours honored

## Testing

### Test Scenarios

1. **Normal due reminder**
   - Create task due tomorrow
   - Wait 24h - 5min before due
   - Verify notification appears

2. **Overdue task**
   - Create task due 1 hour ago
   - Wait scheduler check (5min)
   - Verify overdue notification

3. **Multiple tasks**
   - Create 5 tasks due same time
   - Verify max_notifications_per_hour respected
   - Verify queueing behavior

4. **Action click**
   - Click notification action
   - Verify task updated or opened

5. **Quiet hours**
   - Set quiet hours 10PM-8AM
   - Create task due at midnight
   - Verify no notification during quiet hours
   - Verify notification at 8:05AM

## Future Enhancements

### Mobile Integration (Phase 3)
- Push notifications via Firebase/APNs
- Sync notification status across devices
- Mobile app action buttons

### Smart Reminders
- ML-based optimal reminder time
- Context-aware (location, calendar, etc.)
- Snooze learning (user patterns)

### Multi-Channel
- Email notifications
- Slack/Discord integration
- SMS for critical tasks
