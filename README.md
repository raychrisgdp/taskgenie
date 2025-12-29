# Personal TODO

CLI-first, AI-native personal task manager with RAG-powered search.

## Quick Start

```bash
# Install uv
pip install uv

# Install dependencies
uv pip install -e .

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start backend
uv run backend.main:main

# In another terminal, run CLI
uv run backend.cli.main:app
```

## Features

- ✅ CLI-first interface (Typer)
- ✅ AI-powered chat interface
- ✅ RAG semantic search across tasks and attachments
- ✅ Desktop notifications (plyer)
- ✅ Gmail integration (planned)
- ✅ GitHub integration (planned)
- ✅ BYOK + OpenRouter support
- ✅ Local-first with SQLite

## Commands

```bash
# List all tasks
todo list

# Add a new task
todo add "Review PR #123" --description "Fix authentication bug" --eta "2025-01-15"

# Start AI chat
todo chat

# Show configuration
todo config

# Start web UI
todo ui
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run linting
ruff check backend/

# Format code
ruff format backend/

# Run type checking
mypy backend/

# Run tests
pytest
```

## Configuration

Configuration is managed via `.env` file. Copy `.env.example` and customize.

See `PLAN.md` for detailed requirements and design documents.

## License

MIT
