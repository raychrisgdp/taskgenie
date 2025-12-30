# TaskGenie (personal-todo) - Setup Instructions

**Status:** Spec Complete | Implementation In Progress  
**Last Reviewed:** 2025-12-30

## Prerequisites
- Python 3.11+
- `uv` (modern Python package manager)

## Installation

```bash
# Clone the repository (already done)
cd personal-todo

# Install uv if not already installed
pip install uv

# Install dependencies (this creates virtual environment)
uv pip install -e .

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
# Or use any editor
```

## Running the Application

The CLI is `tgenie`.

```bash
# Start the backend API server
uv run python -m backend.main

# Health check (in another terminal)
curl http://127.0.0.1:8080/health

# Run CLI commands (scaffolded; backend integration in progress)
uv run tgenie --help
uv run tgenie add "My first task"
uv run tgenie list
```

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run linting
ruff check backend/

# Format code
ruff format backend/

# Type checking
mypy backend/

# Run tests
pytest
```

## Configuration

Edit `.env` file to configure:

```env
APP_NAME=TaskGenie
APP_VERSION=0.1.0
DEBUG=true
HOST=127.0.0.1
PORT=8080
DATABASE_URL=sqlite+aiosqlite:///./data/taskgenie.db

# LLM Configuration
LLM_PROVIDER=openrouter
LLM_API_KEY=your-openrouter-api-key-here
LLM_MODEL=anthropic/claude-3-haiku

# Gmail (optional)
GMAIL_ENABLED=false
GMAIL_CREDENTIALS_PATH=

# GitHub (optional)
GITHUB_TOKEN=
GITHUB_USERNAME=

# Notifications
NOTIFICATIONS_ENABLED=true
NOTIFICATION_SCHEDULE=["24h","6h"]
```

## Project Structure

```
personal-todo/
├── .env                # Configuration (copy from .env.example)
├── .gitignore
├── pyproject.toml        # Dependencies and tooling config
├── README.md
├── backend/
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   ├── config.py           # Settings management
│   ├── database.py         # Database connection and setup
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/            # Business logic
│   └── cli/               # CLI commands
└── data/                   # SQLite database and ChromaDB vector store
```

## Next Steps

1. ✅ Install dependencies: `uv pip install -e .`
2. ✅ Configure environment: Edit `.env` file
3. ✅ Start backend: `uv run python -m backend.main`
4. ✅ Test CLI: `uv run tgenie list`
5. ✅ Check health: `curl http://127.0.0.1:8080/health`
