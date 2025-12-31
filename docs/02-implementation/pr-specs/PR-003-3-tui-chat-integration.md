# PR-003-3: TUI Chat Integration (Spec)

**Status:** Spec Only
**Depends on:** PR-002, PR-003-1, PR-003-2
**Last Reviewed:** 2025-12-31

## Goal

Integrate chat functionality into the interactive TUI from PR-008, connecting the chat panel to the streaming chat API from PR-003-2.

## User Value

- Users can chat with the AI assistant directly from the TUI
- Streaming responses provide real-time feedback
- Errors (missing API key, rate limits) show clear user-friendly messages

## Scope

### In

- Chat panel widget in TUI (Textual widget)
- Integration with streaming chat API endpoint
- Real-time rendering of SSE streams
- Error handling with user-friendly modals
- Chat history (in-memory for session)
- "No LLM configured" state (graceful degradation)

### Out

- RAG context injection (PR-005-2)
- Persistent chat history across sessions (future)
- Multi-turn conversation with context retention (future)
- Tool calling / agent actions (future)

## Mini-Specs

- Chat panel widget integrated into the PR-008 TUI
- SSE streaming client that incrementally renders tokens
- Clear error UX for API down / LLM not configured / rate limits
- In-memory session history (no persistence)

## References

- `docs/01-design/DESIGN_TUI.md` (layout + interaction patterns)
- `docs/01-design/DESIGN_CHAT.md` (chat UX + streaming expectations)
- `docs/01-design/API_REFERENCE.md` (chat endpoint contract)

## Technical Design

### Chat Panel Widget

**Layout**
```
┌─────────────────────────────────────────────────────────────┐
│ Chat                                                      │
│                                                            │
│ User: What tasks are due today?                             │
│                                                            │
│ Assistant: You have 3 tasks due today:                      │
│                                                            │
│ 1. [HIGH] Review PR #123                                   │
│    Fix authentication bug                                    │
│                                                            │
│ 2. [MED] Update documentation                              │
│                                                            │
│ 3. [LOW] Clean up old tasks                                │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
│                                                            │
├─────────────────────────────────────────────────────────────┤
│ [Type message...]                   [Send]  [Clear]         │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**
```python
# backend/cli/tui/widgets/chat_panel.py
from textual.widgets import TextArea, Button, Static
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
import httpx
from ..client import TaskAPIClient

class ChatMessage(Static):
    """Single chat message."""

    def __init__(self, role: str, content: str):
        super().__init__()
        self.role = role
        self.content = content

    def render(self):
        """Render message with role label."""
        label = {
            "user": "You",
            "assistant": "AI",
            "system": "System",
        }.get(self.role, self.role)

        # Use Rich markup for styling
        role_style = "bold blue" if self.role == "assistant" else "bold"
        return f"[{role_style}]{label}:[/] {self.content}"


class ChatPanel(Vertical):
    """Chat panel widget."""

    messages: reactive[list[dict]] = reactive([])

    DEFAULT_CSS = """
    ChatPanel {
        height: 1fr;
        border: solid $primary;
    }

    #chat-messages {
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }

    #chat-input {
        height: 3;
        padding: 0 1;
    }
    """

    def __init__(self, api_client: TaskAPIClient):
        super().__init__()
        self.api_client = api_client

    def compose(self):
        """Build chat UI."""
        yield Vertical(
            Static(id="chat-messages"),
            Horizontal(
                TextArea(
                    id="message-input",
                    placeholder="Type your message...",
                ),
                Button("Send", id="send-btn", variant="primary"),
                Button("Clear", id="clear-btn"),
                id="chat-input",
            ),
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "send-btn":
            await self._send_message()
        elif event.button.id == "clear-btn":
            self._clear_chat()

    async def on_text_area_submitted(self, event: TextArea.Submitted) -> None:
        """Handle Enter key in input."""
        await self._send_message()

    async def _send_message(self) -> None:
        """Send user message and stream response."""
        input_widget = self.query_one("#message-input", TextArea)
        message = input_widget.text.strip()

        if not message:
            return

        # Add user message
        self.messages.append({"role": "user", "content": message})
        input_widget.text = ""
        self._update_display()

        # Stream response
        response_content = await self._stream_response(message)

        # Add assistant message
        self.messages.append({"role": "assistant", "content": response_content})
        self._update_display()

    async def _stream_response(self, message: str) -> str:
        """Stream chat response from API."""
        messages_widget = self.query_one("#chat-messages", Static)

        # Add placeholder for streaming
        response_id = f"response-{len(self.messages)}"
        messages_widget.update(
            f"{messages_widget.render()}\n"
            f"[AI]: [dim]Streaming...[/dim]\n"
        )

        full_response = ""

        try:
            # Stream from API
            async with self.api_client.stream_chat(message) as response:
                buffer = ""
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        full_response += chunk

                        # Update display with streaming text
                        # (Note: Textual requires full re-render, optimize in future)
                        messages_widget.update(
                            messages_widget.render().replace("Streaming...", full_response)
                        )

        except httpx.ConnectError:
            self.app.notify(
                "Cannot connect to API. Ensure backend is running.",
                severity="error"
            )
            return "[Connection Error]"

        except ValueError as e:
            # Missing API key
            self.app.notify(
                f"LLM not configured: {e}",
                severity="error"
            )
            return "[LLM not configured]"

        except Exception as e:
            self.app.notify(
                f"Chat error: {e}",
                severity="error"
            )
            return f"[Error: {e}]"

        return full_response

    def _update_display(self) -> None:
        """Update chat display with all messages."""
        messages_widget = self.query_one("#chat-messages", Static)

        display = ""
        for msg in self.messages:
            role = "You" if msg["role"] == "user" else "AI"
            style = "bold blue" if msg["role"] == "assistant" else "bold"
            display += f"[{style}]{role}:[/] {msg['content']}\n\n"

        messages_widget.update(display)

    def _clear_chat(self) -> None:
        """Clear chat history."""
        self.messages.clear()
        self._update_display()
```

### API Client Streaming Support

**Add to TaskAPIClient**
```python
# backend/cli/tui/client.py
async def stream_chat(self, message: str, context: str | None = None):
    """Stream chat response."""
    body = {"message": message}
    if context:
        body["context"] = context

    async with self.client.stream(
        "POST",
        "/api/v1/chat",
        json=body,
        headers={"Accept": "text/event-stream"},
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            yield line
```

### Error Handling

**Error Modal**
```python
class LLMConfigError(ModalScreen):
    """Modal for missing LLM configuration."""

    def compose(self):
        yield Vertical(
            Static(
                "LLM is not configured.\n\n"
                "To enable chat:\n"
                "1. Get an API key from OpenRouter (openrouter.ai)\n"
                "2. Set LLM_API_KEY in .env or config file\n"
                "3. Restart the application",
                id="message"
            ),
            Horizontal(
                Button("Open Setup Guide", id="guide-btn"),
                Button("Close", id="close-btn", variant="primary"),
            ),
        )
```

### Main Screen Integration

**Add Chat Panel**
```python
# backend/cli/tui/screens/main.py
def compose(self):
    """Build screen layout."""
    with Horizontal(id="main-content"):
        # Existing: task list + detail
        yield TaskListView(id="task-list")
        yield TaskDetailPanel(id="task-detail")

    # New: chat panel below
    yield ChatPanel(id="chat-panel")
```

**TCSS Updates**
```css
/* Add chat panel styles */
#chat-panel {
    height: 30%;  /* Bottom 30% of screen */
}

/* Adjust task area for chat */
#main-content {
    height: 70%;  /* Top 70% of screen */
}
```

## Acceptance Criteria

- [ ] Chat panel widget exists with input + message display
- [ ] User messages appear immediately after sending
- [ ] AI responses stream in real-time (character-by-character)
- [ ] `[DONE]` marker stops streaming correctly
- [ ] Missing LLM API key shows clear error modal
- [ ] "No LLM configured" state doesn't crash app
- [ ] Chat history persists for session
- [ ] Clear button resets chat display
- [ ] Keyboard shortcut (Enter) sends message
- [ ] Automated tests cover widget behavior and keybindings (see Test Plan).
- [ ] Manual smoke checklist completed (see Test Plan).

## Test Plan

### Automated

**Widget Tests**
```python
# tests/test_tui/test_chat_panel.py
import pytest

class TestChatPanel:
    @pytest.mark.asyncio
    async def test_send_message_adds_user_msg(self):
        """Sending message adds user message."""
        async with ChatPanel(api_client=mock_client).run_test() as pilot:
            await pilot.press("a")  # Type 'a'
            await pilot.press("enter")

            messages = pilot.app.messages
            assert messages[-1] == {"role": "user", "content": "a"}

    @pytest.mark.asyncio
    async def test_streaming_updates_display(self):
        """Streaming updates display incrementally."""
        # Test with mocked streaming
        pass  # Requires complex mocking

    @pytest.mark.asyncio
    async def test_clear_button_resets_chat(self):
        """Clear button empties chat history."""
        async with ChatPanel(api_client=mock_client).run_test() as pilot:
            # Add message
            await pilot.press("h")
            await pilot.press("enter")
            assert len(pilot.app.messages) == 1

            # Clear
            await pilot.press("tab")  # Move to clear button
            await pilot.press("enter")

            assert len(pilot.app.messages) == 0
```

**Integration Tests**
```python
class TestChatIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_chat(self, api_server):
        """Full chat flow works."""
        async with TodoApp().run_test() as pilot:
            # Send message
            input_widget = pilot.app.query_one("#message-input")
            await pilot.press("S")
            await pilot.press("a")
            await pilot.press("y")
            await pilot.press("enter")

            # Verify request sent
            # (Check API server logs or mock)
```

### Manual

1. Start API server
2. Run `tgenie` (TUI with chat panel)
3. Type "What tasks are due today?" and press Enter
4. Verify:
   - User message appears immediately
   - AI response streams character-by-character
   - `[DONE]` stops streaming
   - Both messages remain visible
5. Test error case:
   - Remove `LLM_API_KEY` from `.env`
   - Restart app
   - Send message
   - Verify error modal appears with setup instructions

### Manual Test Checklist

- [ ] Chat panel renders and does not break existing task UI.
- [ ] Enter sends messages; Clear resets state.
- [ ] Streaming text updates incrementally and stops on `[DONE]`.
- [ ] API-down and missing-config errors show clear, actionable UI.
- [ ] Long responses remain usable (scroll or truncation behavior is acceptable).

### Run Commands

```bash
make test
# or
uv run pytest -v
```

## Notes / Risks / Open Questions

- Should chat history persist across TUI sessions?
- How should we handle long responses (scroll, truncate)?
- Should we add markdown rendering for code blocks?
- Is 30% screen height appropriate for chat panel?

## Dependencies

- PR-002 (Task CRUD API)
- PR-003-1 (LLM Provider Service)
- PR-003-2 (Streaming Chat API)
- PR-008 (Interactive TUI base)

## Future Enhancements

- Persistent chat history (save to DB)
- Context retention across turns
- Markdown rendering for code blocks
- RAG context injection (PR-005-2)
- Tool calling for task actions
