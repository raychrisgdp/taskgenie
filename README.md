# TaskGenie (personal-todo)

CLI-first, AI-native personal task manager. This repo is **implementation in progress**; the
`docs/` folder contains the full design + PR plan.

## Naming

- **Repo/package name:** `personal-todo`
- **CLI name (preferred):** `tgenie` (you can add a shell alias if you want)

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

## What You Can Do Right Now

- Start the FastAPI app and call `GET /health`.
- Configure settings via `.env` (`backend/config.py`).
- Use the CLI entrypoint (`tgenie --help`) to view placeholder commands.

## Try It Now

```bash
uv run python -m backend.main
curl http://127.0.0.1:8000/health

uv run tgenie --help
```

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

## Docs Map

- **Overview and hub:** [`docs/INDEX.md`](docs/INDEX.md)
- **Install and setup:** [`docs/SETUP.md`](docs/SETUP.md)
- **Developer quickstart:** [`docs/DEVELOPER_QUICKSTART.md`](docs/DEVELOPER_QUICKSTART.md)
- **User guide (spec):** [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)
- **AI agents and dev conventions:** [`AGENTS.md`](AGENTS.md)

## License

MIT
