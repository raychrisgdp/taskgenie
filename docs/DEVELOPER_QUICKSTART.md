# Developer Quickstart (5 minutes)

Get a local dev environment running quickly. For full details, see `docs/SETUP.md`.

## Prerequisites

- Python 3.11+
- `uv` (`pip install uv`)

## Install

```bash
# Install dev dependencies (includes FastAPI, uvicorn, and test tools)
make dev

# Or manually:
# uv pip install -e ".[dev]"

# Copy environment file template
cp .env.example .env
# Edit .env with your configuration (optional for basic usage)
```

## Run (backend + CLI)

```bash
# Terminal 1: start API server (reads .env)
python -m backend.main

# Terminal 2: CLI (scaffolded; backend integration in progress)
uv run tgenie --help

# Health check (in another terminal)
curl http://127.0.0.1:8080/health

# OpenAPI (FastAPI Swagger UI)
xdg-open http://127.0.0.1:8080/docs  # Linux (use 'open' on macOS)
```

## Common dev commands

```bash
make dev
make lint
make format
make typecheck
make test
```

## Next reads

- `docs/SETUP.md`
- `docs/02-implementation/PR-PLANS.md`
- `docs/01-design/DESIGN_SUMMARY.md`
