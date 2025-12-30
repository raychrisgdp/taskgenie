# Troubleshooting

> Note: This repo currently ships a skeleton. Feature-specific sections apply once the relevant PRs are implemented (see `docs/02-implementation/PR-PLANS.md`).

## `uv: command not found`

- Install: `pip install uv`
- If installed but not found, ensure your Python scripts directory is on `PATH`.

## Python version errors (`requires-python >=3.11`)

- Verify: `python --version`
- Use Python 3.11+ and reinstall: `uv pip install -e .`

## `ModuleNotFoundError: No module named 'backend'`

- Run commands from the repo root (`personal-todo/`).
- Prefer: `uv run python -m backend.main` (not `python backend/main.py`).

## Port already in use (`[Errno 98] Address already in use`)

- Change `PORT` in `.env` (and restart the server), e.g. `PORT=8081`.
- Or stop the process currently using the port.

## Database file/path issues

Database wiring (migrations, tables, dump/restore) is planned in PR-001. Today, `DATABASE_URL` is reserved for that work.

The default is `DATABASE_URL=sqlite+aiosqlite:///./data/taskgenie.db`, which is relative to your current working directory.

- Run from repo root, or change `DATABASE_URL` to an absolute path.
- Ensure the `data/` directory exists and is writable.

## `NOTIFICATION_SCHEDULE` parsing errors

`NOTIFICATION_SCHEDULE` is a list setting parsed at settings-load time. Use a JSON-like list in `.env`, for example:

```env
NOTIFICATION_SCHEDULE=["24h", "6h"]
```

## `tgenie` not found

- Ensure dependencies are installed: `uv pip install -e .`
- Use `uv run tgenie ...` to run the script in the project environment.

## Missing LLM credentials

LLM-backed features are planned in PR-003. When implemented:

- Set `LLM_API_KEY` in `.env`.
- If you are using OpenRouter, set `LLM_PROVIDER=openrouter`.
