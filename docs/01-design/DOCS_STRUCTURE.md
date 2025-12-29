# Documentation Structure

## Overview

All project documentation is organized in the `docs/` directory with a numbered prefix system for easy navigation.

## Directory Structure

```
docs/
├── 00-research/              # Market research and competitor analysis
├── 01-design/               # Detailed design documents
├── 02-implementation/        # Implementation plans and PR tracking
└── INDEX.md                  # This file - navigation hub
```

## Document Categories

### 00-research/
Market research, competitor analysis, and gap identification.

**Files:**
- `MARKET_RESEARCH.md` - Detailed analysis of 40+ open-source projects
- `COMPARISON_SUMMARY.md` - Quick reference with market gap analysis

### 01-design/
Technical design specifications and architecture decisions.

**Files:**
- `DESIGN_ARCHITECTURE.md` - System architecture, service boundaries
- `DESIGN_CLI.md` - CLI command design with examples
- `DESIGN_DATA.md` - Database schemas and data models
- `DESIGN_CHAT.md` - AI/chat flow, RAG integration
- `DESIGN_WEB.md` - Web UI pages and components
- `DESIGN_NOTIFICATIONS.md` - Notification system design
- `DESIGN_SUMMARY.md` - Executive summary

### 02-implementation/
Implementation plans, pull request tracking, and development roadmap.

**Files:**
- `PR-PLANS.md` - Detailed PR plan with 14 planned PRs

### INDEX.md
Main navigation index with links to all documents and quick start guide.

---

## Quick Reference

**For new developers:**
1. Start with `docs/00-research/` to understand the project vision
2. Read `docs/02-implementation/PR-PLANS.md` to see development roadmap
3. Consult `docs/01-design/` when implementing specific features

**For project maintainers:**
- Update `docs/02-implementation/PR-PLANS.md` as work progresses
- Update relevant design docs when architecture changes
- Keep `docs/INDEX.md` in sync with actual structure

---

## Document Index

See `docs/INDEX.md` for complete index of all documents.
