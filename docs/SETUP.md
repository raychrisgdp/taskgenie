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

# Install core dependencies (PR-001: Database & Configuration)
make dev

# For subsequent PRs, install specific dependencies:
# make pr002  # PR-002: Task CRUD API
# make pr003  # PR-003: LLM Chat Backbone
# make pr005  # PR-005: RAG Semantic Search
# make pr006  # PR-006: Gmail Integration
# make pr007  # PR-007: GitHub Integration
# make pr011  # PR-011: Notifications
# make install-all  # Install all dependencies

# Or manually install with extras:
# uv pip install -e ".[dev,pr002_api,pr003_llm,pr005_rag,pr006_gmail,pr007_github,pr011_notifications]"

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
# Install development dependencies (core + dev tools)
make dev

# Run linting
make lint

# Format code
make format

# Type checking
make typecheck

# Run tests
make test

# Run all checks
make check
```

## Configuration

TaskGenie supports multiple configuration sources with the following precedence (highest to lowest):

1. **Environment variables** (highest priority)
2. **`.env` file** (development convenience)
3. **`~/.taskgenie/config.toml`** (user configuration file)
4. **Built-in defaults** (lowest priority)

### Environment Variables

Set environment variables directly:

```bash
export APP_NAME=TaskGenie
export DATABASE_URL=sqlite+aiosqlite:///./data/taskgenie.db
export LLM_API_KEY=your-key-here
```

### .env File (Development)

Create a `.env` file in the project root:

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

### Config File (`~/.taskgenie/config.toml`)

For persistent user configuration, create `~/.taskgenie/config.toml`:

```toml
app_name = "TaskGenie"
app_version = "0.1.0"
debug = false
host = "127.0.0.1"
port = 8080

[database]
url = "sqlite+aiosqlite:///./data/taskgenie.db"

[llm]
provider = "openrouter"
api_key = "your-openrouter-api-key-here"
model = "anthropic/claude-3-haiku"

[gmail]
enabled = false
credentials_path = ""

[github]
token = ""
username = ""

[notifications]
enabled = true
schedule = ["24h", "6h"]
```

**Note:** You can override the config file location using the `TASKGENIE_CONFIG_FILE` environment variable.

### Data Directory

By default, TaskGenie stores data in `~/.taskgenie/`:

```
~/.taskgenie/
├── config.toml          # User configuration (optional)
├── data/
│   ├── taskgenie.db     # SQLite database
│   └── chroma/          # ChromaDB vector store
├── logs/                # Application logs
└── cache/
    └── attachments/     # Cached attachment content
```

Override the data directory using `TASKGENIE_DATA_DIR` environment variable.

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

## Database Setup

### Initial Setup

On first run, the database will be created automatically. To manually initialize or upgrade:

```bash
# Upgrade database to latest migration
uv run tgenie db upgrade

```

### Database Commands

```bash
# Upgrade to latest migration
uv run tgenie db upgrade

# Upgrade to specific revision
uv run tgenie db upgrade --rev <revision>

# Downgrade by one step
uv run tgenie db downgrade --rev -1

# Create a new migration
uv run tgenie db revision -m "Add new field" --autogenerate

# Dump database to SQL file
uv run tgenie db dump --out backup.sql

# Restore database from SQL file (WARNING: overwrites existing)
uv run tgenie db restore --in backup.sql

# Reset database (WARNING: deletes all data)
uv run tgenie db reset --yes
```

See `docs/02-implementation/MIGRATIONS.md` for detailed migration guide.

## Next Steps

1. ✅ Install dependencies: `uv pip install -e .`
2. ✅ Configure environment: Edit `.env` file or create `~/.taskgenie/config.toml`
3. ✅ Initialize database: `uv run tgenie db upgrade`
4. ✅ Start backend: `uv run python -m backend.main`
5. ✅ Test CLI: `uv run tgenie list`
6. ✅ Check health: `curl http://127.0.0.1:8080/health`
