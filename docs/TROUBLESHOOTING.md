# Troubleshooting

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

The default is `DATABASE_URL=sqlite+aiosqlite:///./data/taskgenie.db`, which is relative to your current working directory.

- Run from repo root, or change `DATABASE_URL` to an absolute path.
- Ensure the `data/` directory exists and is writable.

## `NOTIFICATION_SCHEDULE` parsing errors

`NOTIFICATION_SCHEDULE` is a list setting. Use a JSON-like list in `.env`, for example:

```env
NOTIFICATION_SCHEDULE=["24h", "6h"]
```

## `tgenie` not found

- Ensure dependencies are installed: `uv pip install -e .`
- Use `uv run tgenie ...` to run the script in the project environment.

## Missing LLM credentials

- Most commands work without an API key, but LLM-backed features require `LLM_API_KEY` in `.env`.
- If you are using OpenRouter, set `LLM_PROVIDER=openrouter` and `LLM_API_KEY=...`.
