# PR-013: Event System + Realtime Updates (Spec)

**Status:** Spec Only  
**Depends on:** PR-002, PR-004  
**Last Reviewed:** 2026-01-01

## Goal

Introduce a lightweight event system for task lifecycle events and realtime updates
for UI and agent hooks.

## User Value

- UIs can update in realtime without polling.
- Agent workflows can react to task and attachment changes.

## References

- `docs/01-design/DESIGN_ARCHITECTURE.md`
- `docs/01-design/DESIGN_DATA.md`

## Scope

### In

- Event schema and naming conventions (e.g., `task.created`, `task.updated`).
- Event emitter hooks in task and attachment services.
- Persistent event log for replay and SSE resume.
- SSE endpoint for realtime updates.
- Optional webhook delivery to configured endpoints.

### Out

- External message brokers (Kafka, SNS/SQS).
- Guaranteed delivery beyond basic retry/backoff.
- Multi-tenant or ACL-based event filtering.

## Mini-Specs

- `events` table with `id`, `type`, `payload`, `created_at`.
- `EventService.emit(type, payload)` used by task/attachment mutations.
- `GET /api/v1/events` SSE stream with `Last-Event-ID` support.
- Webhook dispatcher reads configured endpoints and retries on failure.

## User Stories

- As a user, my UI updates when tasks change without manual refresh.
- As a developer, I can subscribe to task lifecycle events.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- In-process event bus writes to the `events` table and publishes to subscribers.
- SSE stream reads from the event log and emits ordered events.
- Webhook dispatcher sends event payloads to configured endpoints.

### Data Model / Migrations

- `events` table for lightweight event storage and replay.

### API Contract

- `GET /api/v1/events` returns `text/event-stream` with `event:` and `data:` fields.
- Optional query params: `types=task.created,task.updated` for filtering.

### Background Jobs

- Webhook delivery worker with basic retry/backoff.

### Security / Privacy

- Event payloads include IDs and minimal metadata only.
- Webhook targets are allowlisted via config.

### Error Handling

- Failed webhook deliveries are logged and retried without blocking core flows.
- SSE clients can reconnect with `Last-Event-ID`.

### Implementation Notes

#### Event Batching for Efficiency

Aggregate high-frequency events to reduce processing overhead:

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from collections import defaultdict

@dataclass
class EventBatch:
    """Batched events for efficient processing."""
    events: List[dict]
    batch_id: str
    created_at: datetime
    target_sse_client_id: Optional[str] = None

class EventBatcher:
    """Event batching and debouncing for high-frequency events."""

    def __init__(
        self,
        batch_window_ms: int = 100,
        max_batch_size: int = 50
    ):
        self.batch_window_ms = batch_window_ms
        self.max_batch_size = max_batch_size
        self.batches: dict[str, EventBatch] = {}
        self.pending_events: defaultdict(list) = defaultdict(list)
        self.last_emit_time: dict[str, datetime] = {}

    async def emit(
        self,
        event_type: str,
        payload: dict,
        client_id: str | None = None
    ) -> str:
        """Emit event with batching."""
        event_id = str(uuid.uuid4())
        now = datetime.now()

        # Add to pending events
        self.pending_events[client_id].append({
            "id": event_id,
            "type": event_type,
            "payload": payload,
            "created_at": now
        })

        # Check if batch window expired
        last_emit = self.last_emit_time.get(client_id, now - timedelta(days=1))
        if (now - last_emit).total_seconds() >= self.batch_window_ms / 1000:
            await self._flush_batch(client_id)

        # Flush if batch size exceeded
        if len(self.pending_events[client_id]) >= self.max_batch_size:
            await self._flush_batch(client_id)

        return event_id

    async def _flush_batch(self, client_id: str) -> None:
        """Flush pending events as a batch."""
        if not self.pending_events[client_id]:
            return

        events = self.pending_events[client_id].copy()
        self.pending_events[client_id].clear()

        batch = EventBatch(
            events=events,
            batch_id=str(uuid.uuid4()),
            created_at=datetime.now()
        )

        # Store batch in memory (for SSE delivery)
        self.batches[f"{client_id}:{batch.batch_id}"] = batch

        # Emit batch event
        await self._emit_batch_event(client_id, batch)

        self.last_emit_time[client_id] = datetime.now()

        logger.info({
            "event": "event_batch_emitted",
            "client_id": client_id,
            "batch_size": len(events),
            "batch_id": batch.batch_id
        })

    async def _emit_batch_event(
        self,
        client_id: str,
        batch: EventBatch
    ) -> None:
        """Emit the batch metadata event."""
        # Store batch metadata in event log
        batch_event = {
            "id": str(uuid.uuid4()),
            "type": "event_batch",
            "payload": {
                "batch_id": batch.batch_id,
                "event_count": len(batch.events),
                "created_at": batch.created_at.isoformat()
            },
            "created_at": datetime.now().isoformat()
        }

        # Store in database
        await store_event(batch_event)

        # Emit to SSE clients
        await sse_broadcast(client_id, {
            "type": "batch",
            "data": batch
        })
```

#### Event Deduplication

Prevent duplicate events from being emitted:

```python
from hashlib import md5
from typing import Set

class EventDeduplicator:
    """Deduplicate events based on content hash."""

    def __init__(self, dedup_window_seconds: int = 10):
        self.dedup_window_seconds = dedup_window_seconds
        self.recent_hashes: Set[str] = set()

    async def emit_if_unique(
        self,
        event_type: str,
        payload: dict
    ) -> Optional[str]:
        """Emit event if not duplicate."""
        # Create content hash
        content = f"{event_type}:{json.dumps(payload, sort_keys=True)}"
        content_hash = md5(content.encode()).hexdigest()

        # Check if recently emitted
        if content_hash in self.recent_hashes:
            logger.debug({
                "event": "event_deduped",
                "type": event_type,
                "hash": content_hash
            })
            return None

        # Add to recent hashes
        self.recent_hashes.add(content_hash)

        # Clean old hashes (beyond window)
        if len(self.recent_hashes) > 1000:
            # Keep only recent 1000 hashes
            self.recent_hashes = set(list(self.recent_hashes)[-1000:])

        return await emit_event(event_type, payload)

    async def cleanup_old_hashes(self) -> int:
        """Clean old hashes from dedup window."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.dedup_window_seconds)

        self.recent_hashes = {
            h for h in self.recent_hashes
            # Assume hash includes timestamp for age tracking
        }

        logger.debug({
            "event": "event_dedup_cleanup",
            "cleaned_count": len(self.recent_hashes)
        })
```

#### Event Filtering and Routing

Filter events by type and content to reduce context noise:

```python
@dataclass
class EventFilter:
    """Event filtering rules for context optimization."""
    include_types: List[str] = field(default_factory=list)
    exclude_types: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)

    async def should_emit(
        self,
        event_type: str,
        payload: dict
    ) -> bool:
        """Check if event should be emitted to context."""
        # Check type filters
        if self.include_types and event_type not in self.include_types:
            return False

        if event_type in self.exclude_types:
            return False

        # Check content patterns
        payload_str = json.dumps(payload, sort_keys=True)

        for exclude in self.exclude_patterns:
            if exclude in payload_str:
                return False

        for include in self.include_patterns:
            if include not in payload_str:
                return False

        return True

# Example filters for agent context
AGENT_CONTEXT_FILTER = EventFilter(
    include_types=[
        "task.created",
        "task.updated",
        "attachment.created",
        "agent.run_started",
        "agent.run_completed"
    ],
    exclude_types=[
        # Exclude high-frequency noise
        "heartbeat",
        "ping",
        "debug"
    ],
    include_patterns=[
        # Only include events with agent-relevant content
        "task_id",
        "run_id",
        "agent_name"
    ]
)
```

#### Event Prioritization

Prioritize events for context loading (most relevant first):

```python
from enum import Enum
from typing import Callable

class EventPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5

def get_event_priority(
    event_type: str,
    payload: dict
) -> EventPriority:
    """Determine event priority based on type and content."""
    # Critical: errors, failures, security events
    if event_type in ["error", "failure", "security_alert"]:
        return EventPriority.CRITICAL

    # High: task completions, agent results
    if event_type in ["task.completed", "agent.run_completed"]:
        return EventPriority.HIGH

    # Medium: task updates, attachments
    if event_type in ["task.updated", "attachment.created", "attachment.updated"]:
        return EventPriority.MEDIUM

    # Low: informational events
    if event_type in ["heartbeat", "ping", "debug"]:
        return EventPriority.LOW

    # Default info
    return EventPriority.INFO

async def emit_with_priority(
    event_type: str,
    payload: dict
) -> str:
    """Emit event with priority metadata."""
    priority = get_event_priority(event_type, payload)

    event_id = await emit_event(
        event_type,
        {
            **payload,
            "priority": priority.value
        }
    )

    logger.info({
        "event": "event_emitted_with_priority",
        "type": event_type,
        "priority": priority.name,
        "event_id": event_id
    })

    return event_id
```

## Acceptance Criteria

### AC1: Event Emission

**Success Criteria:**
- [ ] Task create/update/delete emits the expected event types.
- [ ] Attachment create/delete emits events when applicable.

### AC2: SSE Streaming

**Success Criteria:**
- [ ] SSE endpoint streams events in order.
- [ ] Reconnect with `Last-Event-ID` resumes without duplicates.

### AC3: Webhook Delivery (Optional)

**Success Criteria:**
- [ ] Webhooks receive events when configured.
- [ ] Delivery failures are retried and logged.

## Test Plan

### Automated

- Unit tests for event emission and payloads.
- Integration tests for SSE streaming and resume behavior.
- Webhook dispatcher tests with mocked HTTP endpoints.

### Manual

- Create a task and observe SSE events in a terminal client.
- Configure a webhook endpoint and verify deliveries.

## Notes / Risks / Open Questions

- Decide how long to retain events in the log.
