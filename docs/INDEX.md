# TaskGenie Documentation Index

## Naming Conventions

- **CLI binary:** `tgenie` (interactive TUI planned; CLI scaffolding exists today)
- **Scripting:** `tgenie <command>` (e.g., `tgenie add`, `tgenie list`)
- **Alias (optional):** `taskgenie` (same CLI entrypoint)
- **Optional:** add a shell alias (user preference), e.g. `alias tg=tgenie`

## Quick Start

**New to the project?** Start here:
1. Read [Developer Quickstart](DEVELOPER_QUICKSTART.md) for a 5-minute run-through
2. Read [Setup Guide](SETUP.md) for installation and configuration
3. Explore [Research Phase](00-research/) to understand project vision
4. Review [Design Phase](01-design/) for technical specifications
5. Follow [Implementation Plans](02-implementation/PR-PLANS.md) for development roadmap

---

## Document Categories

### [00-research/](00-research/)
Market research, competitor analysis, and gap identification.

- [MARKET_RESEARCH.md](00-research/MARKET_RESEARCH.md) - Detailed analysis of 40+ open-source competitors
- [COMPARISON_SUMMARY.md](00-research/COMPARISON_SUMMARY.md) - Quick reference with market gap analysis

### [01-design/](01-design/)
Technical design specifications and architecture decisions.

- [DOCS_STRUCTURE.md](01-design/DOCS_STRUCTURE.md) - Documentation organization guide
- [DESIGN_ARCHITECTURE.md](01-design/DESIGN_ARCHITECTURE.md) - System architecture and service boundaries
- [DESIGN_TUI.md](01-design/DESIGN_TUI.md) - Interactive TUI (Textual) UX and structure
- [DESIGN_CLI.md](01-design/DESIGN_CLI.md) - CLI command design with examples
- [DESIGN_DATA.md](01-design/DESIGN_DATA.md) - Database schemas and data models
- [DESIGN_CHAT.md](01-design/DESIGN_CHAT.md) - AI/chat flow and RAG integration
- [DESIGN_WEB.md](01-design/DESIGN_WEB.md) - Web UI pages and components
- [DESIGN_NOTIFICATIONS.md](01-design/DESIGN_NOTIFICATIONS.md) - Notification system design
- [DESIGN_BACKGROUND_JOBS.md](01-design/DESIGN_BACKGROUND_JOBS.md) - Scheduler/jobs approach (no queue for MVP)
- [DESIGN_SUMMARY.md](01-design/DESIGN_SUMMARY.md) - Executive summary
- [API_REFERENCE.md](01-design/API_REFERENCE.md) - REST/WebSocket API specification
- [INTEGRATION_GUIDE.md](01-design/INTEGRATION_GUIDE.md) - Integration provider protocol
- [DECISIONS.md](01-design/DECISIONS.md) - Design decisions log
- [REQUIREMENTS_AUDIT.md](01-design/REQUIREMENTS_AUDIT.md) - Requirements and design audit

### [02-implementation/](02-implementation/)
Implementation plans, pull request tracking, and development roadmap.

- [PR-PLANS.md](02-implementation/PR-PLANS.md) - **START HERE** - Detailed PR plan with roadmap
- [pr-specs/INDEX.md](02-implementation/pr-specs/INDEX.md) - Specs + test scenarios for each PR
- [PLAN.md](02-implementation/PLAN.md) - Original project plan (condensed; Q&A archived)
- [PLAN_ARCHIVE.md](02-implementation/PLAN_ARCHIVE.md) - Archived planning Q&A / early questions
- [TESTING_GUIDE.md](02-implementation/TESTING_GUIDE.md) - Testing policy and examples

---

## Quick Links

### Setup
- [Setup Guide](SETUP.md) - Installation and configuration
- [Developer Quickstart](DEVELOPER_QUICKSTART.md) - 5-minute run-through
- [User Guide](USER_GUIDE.md) - Daily workflows (end-user)
- [Troubleshooting](TROUBLESHOOTING.md) - Common setup/runtime issues

### Architecture
- [System Architecture](01-design/DESIGN_ARCHITECTURE.md)
- [Data Models](01-design/DESIGN_DATA.md)

### API Design
- [API Reference](01-design/API_REFERENCE.md) ⭐ NEW
- [CLI Commands](01-design/DESIGN_CLI.md)
- [Chat Interface](01-design/DESIGN_CHAT.md)
- [Web UI Design](01-design/DESIGN_WEB.md)
- [Notifications](01-design/DESIGN_NOTIFICATIONS.md)

### Development
- [PR Plans](02-implementation/PR-PLANS.md) - Implementation roadmap
- [Testing Guide](02-implementation/TESTING_GUIDE.md) - Testing policy and examples

---

## Status

- **Project Status:** Phase 1 - Infrastructure Setup
- **Documentation Status:** Spec Complete (Implementation In Progress)
- **Last Reviewed:** 2025-12-30
- **Next Step:** Review PR plans and begin implementation

> **Note:** Documentation reflects design specifications. Implementation status tracked in [PR-PLANS.md](02-implementation/PR-PLANS.md).

---

## For Contributors

1. Read [PR Plans](02-implementation/PR-PLANS.md) before starting work
2. Pick a PR from the list
3. Create feature branch from `main`
4. Implement according to design documents
5. Include tests
6. Update status in PR-PLANS.md
7. Submit PR with clear description

---

## Project Stats

- **Total Planned PRs:** See [PR-PLANS.md](02-implementation/PR-PLANS.md) for current count
- **Estimated Effort:** ~130 hours (~16 weeks for one developer)
- **Current Status:** Planning phase complete, ready to implement
