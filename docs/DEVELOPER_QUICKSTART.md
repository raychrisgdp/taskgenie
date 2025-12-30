# Developer Quickstart (5 minutes)

Get a local dev environment running quickly. For full details, see `docs/SETUP.md`.

## Prerequisites

- Python 3.11+
- `uv` (`pip install uv`)

## Install

```bash
uv pip install -e .
cp .env.example .env
```

## Run (backend + CLI)

```bash
# Terminal 1: start API server (reads .env)
uv run python -m backend.main

# Terminal 2: CLI (scaffolded; backend integration in progress)
uv run tgenie --help

# Health check
curl http://127.0.0.1:8080/health

# OpenAPI (FastAPI Swagger UI)
open http://127.0.0.1:8080/docs  # macOS (use xdg-open on Linux)
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
