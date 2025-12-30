# TaskGenie (personal-todo)

CLI-first, AI-native personal task manager. This repo is **implementation in progress**; the `docs/` folder contains the full design + PR plan.

## Naming

- **Repo/package name:** `personal-todo`
- **CLI name (preferred):** `tgenie` (also available as `taskgenie`)

## Quick Start

```bash
# Install uv
pip install uv

# Install dependencies (creates/uses a project venv)
uv pip install -e .

# Configure environment
cp .env.example .env
nano .env

# Start the backend API (serves /health)
uv run python -m backend.main

# In another terminal: run the CLI
uv run tgenie --help
```

## What’s Implemented Today

- FastAPI app with `GET /health`
- Settings via `.env` (`backend/config.py`)
- SQLAlchemy models + DB bootstrap on startup
- CLI entrypoint (`tgenie --help`)

## What’s Planned (See `docs/`)

- Interactive TUI (Textual) with chat as a primary workflow
- RAG-powered semantic search (ChromaDB)
- Desktop notifications, Gmail/GitHub integrations, web UI

## Development

```bash
make dev
make lint
make format
make typecheck
make test
```

## Docs

Start at `docs/INDEX.md`.

## License

MIT
