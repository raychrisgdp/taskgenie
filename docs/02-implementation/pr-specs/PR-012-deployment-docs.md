# PR-012: Deployment + Documentation (Spec)

**Status:** Spec Only  
**Depends on:** PR-001 (backup/restore), PR-010, PR-011, PR-017 (backup/restore guidance)  
**Last Reviewed:** 2025-12-29

## Goal

Make the system easy to run, upgrade, and back up with reliable Docker and accurate
docs.

## User Value

- Faster setup on new machines.
- Lower risk of data loss via clear persistence and backup guidance.

## References

- `docs/SETUP.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/02-implementation/PR-PLANS.md`

## Docs Links

- `README.md`
- `docs/INDEX.md`
- `docs/USER_GUIDE.md`
- `docs/SETUP.md`
- `docs/01-design/DESIGN_DATA.md`
- `docs/02-implementation/PR-PLANS.md`

## Scope

### In

- Docker Compose configuration with persistent volumes and health checks.
- Environment variable documentation and `.env.example` alignment.
- Backup/restore and upgrade instructions.

### Out

- Kubernetes or cloud deployment.
- Multi-user auth and HTTPS termination.

## Mini-Specs

- Compose file for API service with volume mounts for DB and vector store.
- Health check on `/health` and clear port mappings.
- Docs updates for setup, backups, and upgrade path.

## User Stories

- As a user, I can start the app with `docker compose up` and keep my data.
- As a user, I can follow docs and get a working setup on a new machine.

## UX Notes (if applicable)

- N/A.

## Technical Design

### Architecture

- Docker Compose with a single API service and named volumes for data.
- Document environment variables and default ports.

### Data Model / Migrations

- N/A.

### API Contract

- N/A.

### Background Jobs

- N/A.

### Security / Privacy

- Document data locations and backup guidance to avoid accidental loss.

### Error Handling

- Health checks surface startup failures in Docker.

## Acceptance Criteria

### AC1: Docker Compose Boots Cleanly

**Success Criteria:**
- [ ] `docker compose up` starts successfully and `/health` returns OK.

### AC2: Data Persistence

**Success Criteria:**
- [ ] Data persists across container restarts.

### AC3: Docs Match Reality

**Success Criteria:**
- [ ] Setup and backup docs match actual commands, ports, and paths.

## Test Plan

### Automated

- Optional CI smoke test to build images and hit `/health`.

### Manual

- Run compose, create a task, restart, and verify data persists.
- Follow `docs/SETUP.md` and validate commands.

## Notes / Risks / Open Questions

- Keep docker and local paths aligned to avoid data-loss confusion.
