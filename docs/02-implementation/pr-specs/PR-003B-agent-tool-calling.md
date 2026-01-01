# PR-003B: Agent Tool-Calling Foundation (Spec)

**Status:** Spec Only  
**Depends on:** PR-003, PR-002, PR-004  
**Last Reviewed:** 2026-01-01

## Goal

Enable tool-calling in chat so the assistant can take safe, auditable actions on
behalf of the user.

## User Value

- Users can ask the assistant to create/update tasks directly.
- The assistant can refresh attachments and fetch context on demand.

## References

- `docs/01-design/DESIGN_CHAT.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/01-design/API_REFERENCE.md`

## Scope

### In

- Tool schema definition and registry (name, description, parameters).
- Tool execution pipeline with validation, timeouts, and retries.
- Safe defaults: allowlist and confirmation for destructive actions.
- Initial tool set covers task CRUD and attachment list/create/delete.
- Semantic search tool is included if PR-005 exists.
- Tool execution logging with correlation IDs (no content logs).

### Out

- Multi-agent orchestration (PR-014).
- Long-running background tools and scheduling.
- Marketplace or dynamic tool discovery.

## Mini-Specs

- Tool schema defined in Pydantic and exported to JSON Schema for LLM providers.
- `ToolRegistry` for registering tools and validating args.
- `ToolExecutor` that runs tools, captures results, and maps errors.
- Confirmation gate for destructive tools (delete, overwrite).
- Tool results are appended to the chat stream before final model response.

## User Stories

- As a user, I can say "mark my task as done" and the assistant updates it.
- As a user, I can ask the assistant to refresh a GitHub attachment.
- As a developer, I can add a new tool with a schema and handler.

## UX Notes (if applicable)

- Destructive actions require explicit confirmation before execution.

## Technical Design

### Architecture

- `ToolDefinition` (schema + metadata) and `ToolHandler` (callable).
- Registry stores tools and exposes schema list to the LLM provider.
- Chat flow:
  1. Send messages + tool schema to LLM.
  2. If tool call returned, validate and execute tool.
  3. Append tool result and call LLM again for final response.

### Data Model / Migrations

- N/A (tool execution logs are structured logs, not persisted).

### API Contract

- `POST /api/v1/chat` accepts tool-enabled requests; tool calls are handled server-side.
- Optional `GET /api/v1/tools` returns tool schema for debugging.

### Background Jobs

- N/A (all tools execute inline in this PR).

### Security / Privacy

- Tool allowlist and confirmation for destructive operations.
- Tool execution logs contain metadata only (no user content or secrets).

### Error Handling

- Invalid tool args return a tool error message back to the model.
- Tool timeouts return a clear failure response without crashing chat.

### Implementation Notes

#### Consolidation Principle

Prefer single comprehensive tools over multiple narrow tools:

```python
# ❌ Anti-pattern: Multiple narrow tools
def get_task_by_id(task_id: str) -> Task:
    """Retrieve task by ID."""
    pass

def get_tasks_by_status(status: str) -> list[Task]:
    """Retrieve tasks by status."""
    pass

def get_tasks_due_before(date: datetime) -> list[Task]:
    """Retrieve tasks due before date."""
    pass

# ✅ Better: Single comprehensive tool
def query_tasks(
    filters: TaskFilters,
    limit: int = 50,
    sort: str = "eta_asc"
) -> TaskQueryResult:
    """
    Query tasks with flexible filtering.

    Use when:
    - User asks "What's due today?"
    - User asks "Show high-priority tasks"
    - User asks "List completed tasks"

    Args:
        filters: Filter criteria (status, priority, date_range, tags)
        limit: Max results to return (default 50)
        sort: Sort order (eta_asc, priority_desc, created_desc)

    Returns:
        TaskQueryResult with tasks, total count, and applied filters

    Consolidates: get_task_by_id, get_tasks_by_status, get_tasks_due_before
    """
    pass
```

#### Tool Description Engineering

Write descriptions that answer what, when, and what returns:

```python
@tool_definition(
    name="create_task",
    description="""
    Create a new task in the task manager.

    Use when:
    - User explicitly asks to create a task
    - User says "Add a task for X"
    - User needs to capture a quick action item

    The task will be created with 'pending' status and 'medium' priority by default.

    Args:
        title: Task title (required, 1-255 characters)
        description: Detailed description (optional, markdown supported)
        priority: Task priority (optional, one of: low, medium, high, critical)
        eta: Due date/time (optional, ISO 8601 format)
        tags: List of tags (optional, for categorization)

    Returns:
        Created task object with ID, timestamps, and initial state

    Errors:
        INVALID_TITLE: Title too long or contains invalid characters
        INVALID_PRIORITY: Priority value not in allowed set
        INVALID_ETA: Date format not parseable
    """
)
async def create_task(
    title: str,
    description: str | None = None,
    priority: str = "medium",
    eta: str | None = None,
    tags: list[str] | None = None
) -> dict:
    """Create a new task."""
    # Implementation...
```

## Acceptance Criteria

### AC1: Tool Schema and Registry

**Success Criteria:**
- [ ] Tools are defined with JSON Schema parameters.
- [ ] Tool registry exposes the schema list to the chat pipeline.

### AC2: Tool Execution Flow

**Success Criteria:**
- [ ] Tool calls are validated and executed with timeout handling.
- [ ] Tool results are included in the chat response flow.

### AC3: Safety and Confirmation

**Success Criteria:**
- [ ] Destructive tools require confirmation or are blocked by default.
- [ ] Tool errors are surfaced as readable assistant responses.

## Test Plan

### Automated

- Unit tests for tool schema validation and registry behavior.
- Integration tests for tool call -> execution -> response flow with mocked LLM.
- Safety tests for destructive tool confirmation gating.

### Manual

- Run chat and ask the assistant to create/update/complete a task.
- Attempt a destructive action and verify confirmation is required.

## Notes / Risks / Open Questions

- Decide whether tool execution logs should be persisted for audit (future).

### Response Format Optimization

Provide concise and detailed format options:

```python
from enum import Enum

class ResponseFormat(Enum):
    """Control response verbosity for token efficiency."""
    CONCISE = "concise"  # ID + status only
    STANDARD = "standard"   # Core fields (title, status, priority, eta)
    DETAILED = "detailed"  # Full object with all fields

@tool_definition(
    name="list_tasks",
    description=f"""
    Query tasks from the task manager.

    Use when:
    - User asks "What tasks do I have?"
    - User needs to see tasks by status/priority/date
    - User wants to review workload

    Args:
        filters: Filter criteria (optional)
        limit: Max results to return (default 50)
        format: Response format - 'concise', 'standard', or 'detailed'

        Use 'concise' for quick overviews or when user needs minimal info.
        Use 'standard' for most queries where full context needed.
        Use 'detailed' when user needs comprehensive view or all fields.

    Returns:
        Formatted task list based on requested format.

        'concise': Returns only task ID and status
        'standard': Returns title, status, priority, eta, created_at
        'detailed': Returns all fields including description, tags, attachments
    """
)
async def list_tasks(
    filters: dict | None = None,
    limit: int = 50,
    format: str = "standard"
) -> dict:
    """List tasks with format control."""
    # Implementation...
```

### Tool Definition Schema

Use consistent schema with naming conventions:

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str  # "string", "integer", "boolean", "array"
    description: str
    required: bool
    default: Optional[any] = None
    enum: Optional[List[str]] = None

class ToolDefinition(BaseModel):
    """Tool definition following JSON Schema."""
    name: str = Field(..., description="Tool identifier (verb_noun pattern)")
    description: str = Field(..., description="What tool does, when to use it, What it returns")
    parameters: ToolParameter | Field(..., description="Parameters schema")
    returns: dict = Field(
        default={"type": "object"},
        description="Return type and structure"
    )
    examples: Optional[List[dict]] = Field(
        None,
        description="Example usage patterns for agents"
    )

# Example: Create task tool
CREATE_TASK_TOOL = ToolDefinition(
    name="create_task",
    description=(
        "Create a new task. Use when user asks to add, create, "
        "or capture a task. Returns the created task with ID and timestamps."
    ),
    parameters=ToolParameter(
        name="args",
        type="object",
        description="Task creation parameters",
        required=True,
        properties={
            "title": {
                "type": "string",
                "description": "Task title (1-255 characters)"
            },
            "priority": {
                "type": "string",
                "description": "Task priority (default: medium)",
                "enum": ["low", "medium", "high", "critical"],
                "default": "medium"
            },
            "eta": {
                "type": "string",
                "description": "Due date/time (ISO 8601 format)"
            }
        }
    ),
    examples=[
        {
            "input": {"title": "Buy groceries", "priority": "high"},
            "output": {"id": "task-123", "status": "pending", "created_at": "2025-01-15T10:00:00Z"}
        }
    ]
)
```

### Error Message Design

Design error messages for agent recovery:

```python
class ToolError(Exception):
    """Tool error with actionable recovery guidance."""

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        recover_action: str | None = None
    ):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.recover_action = recover_action

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "code": self.code,
            "retryable": self.retryable,
            "recover_action": self.recover_action
        }

async def create_task(title: str, priority: str) -> dict:
    """Create a task with clear error handling."""
    if len(title) > 255:
        raise ToolError(
            code="INVALID_TITLE",
            message=f"Title too long: {len(title)} characters (max 255)",
            recover_action="Truncate title to 255 characters and retry"
        )

    if priority not in ["low", "medium", "high", "critical"]:
        raise ToolError(
            code="INVALID_PRIORITY",
            message=f"Invalid priority: {priority}",
            recover_action="Use one of: low, medium, high, critical"
        )

    # Implementation...

async def fetch_github_pr(owner: str, repo: str, number: int) -> dict:
    """Fetch GitHub PR with rate limit handling."""
    try:
        pr = await github_service.get_pr(owner, repo, number)
        return pr
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise ToolError(
                code="RATE_LIMITED",
                message="GitHub rate limit exceeded",
                retryable=True,
                recover_action="Wait 1 hour and retry, or configure GITHUB_TOKEN"
            )
        elif e.response.status_code == 403:
            raise ToolError(
                code="FORBIDDEN",
                message="Repository access forbidden",
                recover_action="Check repository permissions or verify GITHUB_TOKEN"
            )
        else:
            raise ToolError(
                code="FETCH_FAILED",
                message=f"Failed to fetch PR: {e}",
                retryable=True,
                recover_action=f"Check that {owner}/{repo}#{number} exists"
            )
```

### Async Tool Execution Patterns

Implement async tool patterns with timeout handling:

```python
import asyncio
from contextlib import asynccontextmanager

class AsyncToolExecutor:
    """Async tool execution with timeout and cancellation."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def execute(
        self,
        tool_name: str,
        tool_func: Callable,
        **kwargs
    ) -> dict:
        """Execute tool with timeout and error handling."""
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                tool_func(**kwargs),
                timeout=self.timeout
            )
            return {
                "status": "success",
                "result": result
            }

        except asyncio.TimeoutError:
            logger.warning({
                "event": "tool_timeout",
                "tool": tool_name,
                "timeout": self.timeout
            })
            return {
                "status": "timeout",
                "error": f"Tool execution timed out after {self.timeout}s",
                "recoverable": True
            }

        except ToolError as e:
            logger.warning({
                "event": "tool_error",
                "tool": tool_name,
                "code": e.code,
                "retryable": e.retryable
            })
            return {
                "status": "error",
                "error": e.message,
                "code": e.code,
                "retryable": e.retryable,
                "recover_action": e.recover_action
            }

        except Exception as e:
            logger.error({
                "event": "tool_unexpected_error",
                "tool": tool_name,
                "error": str(e)
            })
            return {
                "status": "error",
                "error": "Unexpected tool error",
                "recoverable": False
            }

# Usage
executor = AsyncToolExecutor(timeout=30.0)
result = await executor.execute(
    tool_name="create_task",
    tool_func=create_task,
    title="Buy groceries",
    priority="high"
)
```

### Tool Result Caching

Implement memoization for expensive tool calls:

```python
from functools import lru_cache
from typing import Optional
import hashlib

def cache_key(tool_name: str, **kwargs) -> str:
    """Generate stable cache key."""
    # Sort kwargs for consistent keys
    sorted_items = sorted(kwargs.items())
    key_str = f"{tool_name}:{sorted_items}"
    return hashlib.md5(key_str.encode()).hexdigest()

class CachedToolExecutor:
    """Tool executor with memoization."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[dict, float]] = {}

    async def execute(
        self,
        tool_name: str,
        tool_func: Callable,
        **kwargs
    ) -> dict:
        """Execute tool with caching."""
        key = cache_key(tool_name, **kwargs)

        # Check cache
        if key in self._cache:
            result, cached_at = self._cache[key]
            age_seconds = (datetime.now() - cached_at).total_seconds()

            if age_seconds < self.ttl_seconds:
                logger.debug({
                    "event": "tool_cache_hit",
                    "tool": tool_name,
                    "key": key
                })
                return result

        # Execute tool
        result = await tool_func(**kwargs)

        # Cache result
        self._cache[key] = (result, datetime.now())
        logger.debug({
            "event": "tool_cache_miss",
            "tool": tool_name,
            "key": key
        })

        return result

# Usage
executor = CachedToolExecutor(ttl_seconds=300)
await executor.execute(tool_name="list_tasks", tool_func=list_tasks, status="pending")
```

### Tool Composition and Chaining

Support sequential tool chaining for workflows:

```python
class ToolChainer:
    """Chain multiple tools in sequence."""

    def __init__(self):
        self.tools: dict[str, Callable] = {}

    async def chain(
        self,
        steps: List[dict]
    ) -> List[dict]:
        """
        Execute tools in sequence, passing outputs to next steps.

        Steps format:
        [
            {"tool": "get_task", "args": {"task_id": "$task_id"}},
            {"tool": "update_task", "args": {"task_id": "$task_id", "status": "completed"}}
        ]
        """
        context: dict = {}
        results: List[dict] = []

        for step in steps:
            tool_name = step["tool"]
            step_args = self._resolve_args(step["args"], context)

            result = await self.tools[tool_name](**step_args)
            results.append(result)

            # Update context for next step
            context.update(result.get("output", {}))

        return results

    def _resolve_args(self, args: dict, context: dict) -> dict:
        """Resolve argument references from previous step outputs."""
        resolved = {}
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("$"):
                ref_key = value[1:]  # Remove $ prefix
                resolved[key] = context.get(ref_key, value)
            else:
                resolved[key] = value
        return resolved

# Example workflow chain
workflow = ToolChainer()
results = await workflow.chain([
    {
        "tool": "create_task",
        "args": {"title": "Review PR #123"}
    },
    {
        "tool": "search_github_pr",
        "args": {"query": "PR #123"}  # Will get task_id from previous output
    },
    {
        "tool": "add_attachment",
        "args": {"task_id": "$task_id", "url": "$pr_url"}
    }
])
```
