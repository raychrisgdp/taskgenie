# PR-012: Deployment + Documentation (Spec)

**Status:** Spec Only  
**Depends on:** PR-010, PR-011  
**Last Reviewed:** 2025-12-29

## Goal

Make the system easy to run, upgrade, and back up:
- Docker Compose “just works”
- docs match reality
- data persistence is safe

## User Value

- Faster setup for new machines.
- Lower risk of data loss (clear volumes + backup instructions).

## Scope

### In

- Docker Compose configuration:
  - API service
  - persistent volume for SQLite DB and vector store
  - env var configuration
  - health checks
- Documentation updates:
  - setup instructions
  - backup/restore
  - “what works today” vs planned

### Out

- Cloud deployment (Kubernetes, etc.).
- Multi-user auth/HTTPS termination (future).

## Mini-Specs

- Docker Compose:
  - one-command local run with persisted data volumes.
- Environment docs:
  - `.env.example` and `docs/SETUP.md` aligned with the actual config keys.
- Developer ergonomics:
  - smoke checks (`/health`, basic task CRUD) documented.
- Docs hygiene:
  - docs link/name checks in CI (no `todo` command examples; consistent `tgenie` usage; no broken relative links).
- Release:
  - minimal “how to run” instructions and expected ports/paths.

## References

- `docs/SETUP.md`
- `docs/01-design/DESIGN_DATA.md` (data locations + backup)
- `docs/02-implementation/PR-PLANS.md` (current roadmap)

## Technical Design

### Docker Compose

- Define volumes for:
  - SQLite DB
  - vector store
  - attachment cache (if needed)
- Add health checks and clear env var configuration.

### Upgrade path

- When migrations exist:
  - document `tgenie db upgrade` for upgrades
  - document backup/restore workflows (SQL dump + restore)

## Acceptance Criteria

- [ ] `docker compose up` starts successfully and `/health` returns ok.
- [ ] Data persists across container restarts.
- [ ] Docs are accurate and consistent with the chosen CLI name and UX.

## Test Plan

### Automated

- Optional: CI smoke test that builds images and runs health check (if CI exists).

### Manual

1. `docker compose up -d`
2. Create a task (via TUI or API).
3. Restart containers; verify task persists.
4. Run `tgenie db upgrade` inside container context and verify no errors.

## Notes / Risks / Open Questions

- Keep local dev (no docker) and docker paths aligned to avoid “works on my machine” data-loss issues.
