# User Guide

**Status:** Spec (implementation in progress)  
**Last Reviewed:** 2025-12-30

This is the end-user workflow guide for TaskGenie. For installation and developer setup, see `docs/SETUP.md` and `docs/DEVELOPER_QUICKSTART.md`.

---

## Getting Started

1. Start the backend.
2. Launch the interactive UI:

```bash
tgenie
```

The interactive TUI is the primary UX. Subcommands exist for scripting.

---

## Daily Workflow (Interactive TUI)

### 1. Check what’s due

- Open `tgenie`
- Use the filter/search UI to view “due today”, “overdue”, or “high priority”

### 2. Capture tasks quickly

- Press `a` to add a task (title first; add description/ETA/priority as needed).

### 3. Work the list

- Use `e` to edit the selected task (status, ETA, description)
- Use `d` to mark done
- Use `x` to delete (confirm)

### 4. Ask the app (chat)

Chat is designed as a primary mode inside the TUI (for example: “What should I focus on today?”).

Session behavior (resume/new) is specified in `docs/01-design/DECISIONS.md`.

---

## Quick Commands (Scripting / One-shot)

```bash
# List tasks
tgenie list
tgenie list --status pending

# Add a task
tgenie add "Review PR #123" --description "Fix auth bug" --eta "tomorrow" --priority high

# Show/edit/done
tgenie show <task_id>
tgenie edit <task_id> --status in_progress
tgenie done <task_id>
```

See `docs/01-design/DESIGN_CLI.md` for the full command spec.

---

## Attachments (Gmail/GitHub/URLs)

Two primary workflows:

1. **Auto-detect from text**: include a URL in the task description; the system can detect it and create an attachment.
2. **Manual attach**:

```bash
tgenie attach <task_id> --type github --ref "https://github.com/org/repo/pull/123"
tgenie attach <task_id> --type gmail --ref "https://mail.google.com/mail/u/0/#inbox/..."
```

Attachment caching and normalization rules are specified in:
- `docs/01-design/INTEGRATION_GUIDE.md`
- `docs/01-design/DESIGN_DATA.md`

---

## Notifications

Notifications are designed around due-date reminders:
- default: 24h + 6h before ETA
- overdue reminders

Details: `docs/01-design/DESIGN_NOTIFICATIONS.md`

---

## Backup / Restore

Planned CLI surface:
- `tgenie db dump --out backup.sql`
- `tgenie db restore --in backup.sql`
- `tgenie db upgrade` (migrations)

SQLite fallback (works today as a concept/spec):

```bash
sqlite3 ~/.taskgenie/data/taskgenie.db .dump > backup.sql
sqlite3 ~/.taskgenie/data/taskgenie.db < backup.sql
```

Details: `docs/01-design/DESIGN_DATA.md`

---

## Observability

TaskGenie provides structured logging and telemetry for monitoring and debugging.

### Logging Configuration

Logs are written in JSON format (one JSON object per line) for easy parsing and analysis.

**Environment Variables:**

- `LOG_LEVEL`: Set the minimum log level (default: `INFO`). Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- `LOG_FILE_PATH`: Custom path for log file (default: `~/.taskgenie/logs/taskgenie.jsonl`).

**Example:**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Use custom log file location
export LOG_FILE_PATH=/var/log/taskgenie/app.jsonl
```

Logs include structured fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name (e.g., `backend.middleware`)
- `message`: Log message
- `request_id`: Request correlation ID (when available)
- `event`: Event type (e.g., `http_request`, `http_error`)

Sensitive data (passwords, API keys, email addresses) is automatically redacted.

### Telemetry Endpoint

The `/api/v1/telemetry` endpoint provides system health and metrics.

**Usage:**

```bash
curl http://127.0.0.1:8080/api/v1/telemetry
```

**Response:**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_s": 3600,
  "db": {
    "connected": true,
    "migration_version": "001"
  },
  "optional": {
    "event_queue_size": null,
    "agent_runs_active": null
  }
}
```

**Status Values:**
- `ok`: System is healthy (database connected)
- `degraded`: System is operational but database is unavailable

**Configuration:**

- `TELEMETRY_ENABLED`: Enable/disable telemetry endpoint (default: `true`). Set to `false` to disable.

**Note:** The telemetry endpoint always returns HTTP 200. Check the `status` field in the response to determine system health.

---

## Troubleshooting

See `docs/TROUBLESHOOTING.md`.
