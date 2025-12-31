# Review: `c/pr-001-db-config`

**Review Summary**

- Decision: needs work
- Risk: low
- Exec summary: Solid implementation of configuration, database, migrations, and CLI commands. All spec requirements met with good code quality and test coverage. Minor gaps in automated testing for FastAPI startup auto-migrations, and documentation beyond spec scope.
- Baseline: main 7e43b0a, target c/pr-001-db-config 4e0030f, merge base 7e43b0a, compare main...c/pr-001-db-config, files: 38 +10022/−135

**Key Recommendations (Top Priority)**

- Add automated test for AC1 that verifies FastAPI startup runs migrations automatically when DB doesn't exist.
- Update .env.example with all new environment variables introduced in this PR (TASKGENIE_DATA_DIR, TASKGENIE_CONFIG_FILE, DATABASE_URL).
- Consider whether .cursor/commands/ directory (4 markdown files) is in scope for PR-001 or should be moved to a separate infrastructure/tooling PR.

**Findings (ordered by severity)**

### Critical

- None.

### High

- None.

### Medium

- [Test-1][Medium][Test] tests/test_main.py – Missing automated test for AC1 "FastAPI startup automatically runs migrations". Current `test_backend_main_health_check` only verifies `/health` returns 200, not that migrations ran or tables were created.
  **Change:** Add test that creates fresh DB path, starts FastAPI via TestClient (triggers lifespan), verifies DB file created, and asserts all required tables exist (`tasks`, `attachments`, `notifications`, `chat_history`, `config`, `alembic_version`).
  **Validate:** Run `pytest tests/test_main.py::test_fastapi_lifespan_creates_db_and_runs_migrations` -v and verify it passes on fresh database.

### Low

- [Docs-1][Low][Docs] .cursor/commands/review.md, .cursor/commands/pr-desc.md, .cursor/commands/post-review.md, .cursor/commands/test-ac.md – Development tooling documentation not mentioned in PR-001 spec. Spec scope includes config, database, migrations, CLI, and docs for backup/restore/migrations.
  **Change:** Either remove .cursor/commands/ files from this PR or document justification for including development workflow tools in a database/config PR.
  **Validate:** Check PR-001 spec `Scope > In` section - does it mention development tooling or agent workflow documentation?

- [Env-1][Low][Env] .env.example – Environment variables TASKGENIE_DATA_DIR, TASKGENIE_CONFIG_FILE, DATABASE_URL are documented in AGENTS.md but .env.example is not created or updated in this PR.
  **Change:** Create or update .env.example with all configuration options from Settings class, marking required/optional and adding comments explaining purpose.
  **Validate:** Run `grep TASKGENIE_ DATABASE_URL LLM_ GMAIL_ GITHUB_ .env.example` and verify all environment variables from backend/config.py are documented.

**Strengths**

- Solid end-to-end implementation: configuration loading with correct precedence (env vars > .env > TOML > defaults), database initialization, Alembic migrations, CLI commands for all required operations.
- Proper SQLite foreign key handling in both runtime sessions (`get_db`) and Alembic migration connections (`run_async_migrations`).
- Clean project structure with clear separation of concerns: models, config, database, CLI, migrations.
- Good test coverage for configuration, database, CLI commands, and models with proper isolation using `tmp_path` and `monkeypatch`.
- Well-documented code with Google-style docstrings, type hints throughout, and clear inline comments.
- Makefile enhancements provide convenient targets for installing dependencies by PR number.

**Tests**

- Tests added/modified: 10 test files covering config, database, CLI commands, models, and backend main. Test coverage for all core functionality including migrations, backup/restore, configuration precedence.

**Questions for Author**

- Should .cursor/commands/ directory (review.md, pr-desc.md, post-review.md, test-ac.md) be part of PR-001, or moved to a separate infrastructure/development-tooling PR?
- Should .env.example be created/updated as part of this PR to document all environment variables?
- Is the missing integration test for AC1 (FastAPI startup auto-migrations) an intentional gap or oversight?

## Metrics Summary

| Metric | Count |
|--------|-------|
| Total Findings | 3 |
| Critical | 0 |
| High | 0 |
| Medium | 1 |
| Low | 2 |
| Files Changed | 38 |
| Lines Added | +10022 |
| Lines Removed | -135 |
| Spec Compliance Issues | 1 |
