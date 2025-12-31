# PR Specs Index

This folder contains one **spec** per planned PR, including:
- goal and scope
- acceptance criteria
- concrete test scenarios (automated + manual)

Design deep-dives live in `docs/01-design/` (notably `DESIGN_TUI.md`, `DESIGN_CHAT.md`, `DESIGN_DATA.md`, `DESIGN_NOTIFICATIONS.md`, `DESIGN_BACKGROUND_JOBS.md`).

## Specs

**Core PRs (12)**
- [PR-001-db-config.md](PR-001-db-config.md) - Database, config, migrations, backup/restore
- [PR-002-task-crud-api.md](PR-002-task-crud-api.md) - Task CRUD API *(enriched: api-testing)*
- ~~[PR-003-llm-chat-backbone.md](PR-003-llm-chat-backbone.md)~~ → **Split into PR-003-1/2/3**
- [PR-004-attachments-link-detection.md](PR-004-attachments-link-detection.md) - Attachments API + link detection *(enriched: task-workflow)*
- [PR-009-cli-subcommands.md](PR-009-cli-subcommands.md) - Non-interactive CLI subcommands *(enriched: task-workflow)*
- ~~[PR-005-rag-semantic-search.md](PR-005-rag-semantic-search.md)~~ → **Split into PR-005-1/2**
- [PR-006-gmail-integration.md](PR-006-gmail-integration.md) - Gmail URL/OAuth + content fetch/cache *(enriched: integration-setup)*
- [PR-007-github-integration.md](PR-007-github-integration.md) - GitHub URL fetch/cache *(enriched: integration-setup)*
- [PR-008-interactive-tui.md](PR-008-interactive-tui.md) - Interactive TUI (tasks MVP) *(enriched: tui-dev)*
- [PR-010-web-ui.md](PR-010-web-ui.md) - Web UI (tasks first, chat optional)
- [PR-011-notifications.md](PR-011-notifications.md) - Notifications scheduling + delivery + history
- [PR-012-deployment-docs.md](PR-012-deployment-docs.md) - Docker/deploy + docs

**Breakdown PRs (5)**
- [PR-003-1-llm-provider.md](PR-003-1-llm-provider.md) - LLM Provider Abstraction & Configuration
- [PR-003-2-streaming-chat-api.md](PR-003-2-streaming-chat-api.md) - Streaming Chat API Endpoint *(enriched: api-testing)*
- [PR-003-3-tui-chat-integration.md](PR-003-3-tui-chat-integration.md) - TUI Chat Integration *(enriched: tui-dev)*
- [PR-005-1-chromadb-embeddings.md](PR-005-1-chromadb-embeddings.md) - ChromaDB Setup & Embeddings Pipeline *(enriched: rag-testing)*
- [PR-005-2-semantic-search-rag.md](PR-005-2-semantic-search-rag.md) - Semantic Search API & RAG Context Injection *(enriched: rag-testing, context-optimization, context-compression)*

**Note:** PR-003 and PR-005 have been split into smaller PRs for focused development and parallel execution. See [SKILL_ENRICHMENT_SUMMARY.md](../SKILL_ENRICHMENT_SUMMARY.md) for details.
