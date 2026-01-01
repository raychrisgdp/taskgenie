# PR Specs Index

This folder contains one **spec** per planned PR, including:
- goal and scope
- acceptance criteria
- concrete test scenarios (automated + manual)

Design deep-dives live in `docs/01-design/` (notably `DESIGN_TUI.md`, `DESIGN_CHAT.md`, `DESIGN_DATA.md`, `DESIGN_NOTIFICATIONS.md`, `DESIGN_BACKGROUND_JOBS.md`).

## Specs

- [PR-001-db-config.md](PR-001-db-config.md) - Database, config, migrations, backup/restore
- [PR-002-task-crud-api.md](PR-002-task-crud-api.md) - Task CRUD API
- [PR-003-llm-chat-backbone.md](PR-003-llm-chat-backbone.md) - LLM service + chat API + TUI chat wiring
- [PR-003B-agent-tool-calling.md](PR-003B-agent-tool-calling.md) - Tool-calling foundation for agents
- [PR-004-attachments-link-detection.md](PR-004-attachments-link-detection.md) - Attachments API + link detection
- [PR-005-rag-semantic-search.md](PR-005-rag-semantic-search.md) - ChromaDB/RAG + semantic search + chat context
- [PR-006-gmail-integration.md](PR-006-gmail-integration.md) - Gmail URL/OAuth + content fetch/cache
- [PR-007-github-integration.md](PR-007-github-integration.md) - GitHub URL fetch/cache
- [PR-008-interactive-tui.md](PR-008-interactive-tui.md) - Interactive TUI (tasks MVP)
- [PR-009-cli-subcommands.md](PR-009-cli-subcommands.md) - Non-interactive CLI subcommands
- [PR-010-web-ui.md](PR-010-web-ui.md) - Web UI (tasks first, chat optional)
- [PR-011-notifications.md](PR-011-notifications.md) - Notifications scheduling + delivery + history
- [PR-012-deployment-docs.md](PR-012-deployment-docs.md) - Docker/deploy + docs
- [PR-013-event-system.md](PR-013-event-system.md) - Event system + realtime updates
- [PR-014-multi-agent-orchestration.md](PR-014-multi-agent-orchestration.md) - Multi-agent orchestration
- [PR-015-agent-ux-panel.md](PR-015-agent-ux-panel.md) - TUI agent panel + controls
- [PR-016-observability-baseline.md](PR-016-observability-baseline.md) - Structured logging + telemetry
- [PR-017-db-config-followups.md](PR-017-db-config-followups.md) - DB config follow-ups
