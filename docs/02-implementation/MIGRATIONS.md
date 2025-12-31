# Database Migrations Guide

This guide covers database migrations, backup, and restore procedures for TaskGenie.

## Overview

TaskGenie uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. The database is SQLite, stored by default at `~/.taskgenie/data/taskgenie.db`.

## Migration Commands

### Upgrade Database

Upgrade to the latest migration:

```bash
tgenie db upgrade
```

Upgrade to a specific revision:

```bash
tgenie db upgrade --rev <revision>
```

### Downgrade Database

Downgrade by one step:

```bash
tgenie db downgrade --rev -1
```

Downgrade to a specific revision:

```bash
tgenie db downgrade --rev <revision>
```

**Note:** SQLite has limited support for downgrades. Some operations (like dropping columns) cannot be easily reversed. Always backup before downgrading.

### Create New Migration

Create a new migration with auto-generation from model changes:

```bash
tgenie db revision -m "Add priority field" --autogenerate
```

Create an empty migration (for manual SQL):

```bash
tgenie db revision -m "Custom migration"
```

## Backup and Restore

### Backup Database

Dump the database to a SQL file:

```bash
tgenie db dump --out backup.sql
```

This creates a complete SQL dump of your database, including schema and data.

### Restore Database

Restore from a SQL file:

```bash
tgenie db restore --in backup.sql
```

**WARNING:** This will overwrite your existing database. You'll be prompted for confirmation unless the database doesn't exist.

### Manual Backup (Alternative)

You can also use SQLite's built-in tools:

```bash
# Simple file copy (SQLite supports this while running)
cp ~/.taskgenie/data/taskgenie.db ~/.taskgenie/data/taskgenie_backup_$(date +%Y%m%d).db

# Or use sqlite3 directly
sqlite3 ~/.taskgenie/data/taskgenie.db .dump > backup.sql
```

## Reset Database

Reset the database (deletes all data):

```bash
tgenie db reset --yes
```

**WARNING:** This permanently deletes the database file. Use with caution, typically only during development.

## Migration Workflow

### For Developers

1. **Make model changes** in `backend/models/`
2. **Create migration:**
   ```bash
   tgenie db revision -m "Description of changes" --autogenerate
   ```
3. **Review the generated migration** in `backend/migrations/versions/`
4. **Test the migration:**
   ```bash
   tgenie db upgrade
   ```
5. **Test downgrade** (if applicable):
   ```bash
   tgenie db downgrade --rev -1
   tgenie db upgrade
   ```

### For Users

1. **Upgrade on app update:**
   ```bash
   tgenie db upgrade
   ```

2. **Backup before major updates:**
   ```bash
   tgenie db dump --out backup_$(date +%Y%m%d).sql
   ```

## Migration Files

Migrations are stored in `backend/migrations/versions/` with names like:

- `001_initial_schema.py` - Initial schema
- `002_add_priority_field.py` - Example migration

Each migration file contains:
- `revision`: Unique identifier
- `down_revision`: Parent revision
- `upgrade()`: Function to apply migration
- `downgrade()`: Function to reverse migration

## Troubleshooting

### Migration Fails

If a migration fails:

1. Check the error message
2. Restore from backup if needed:
   ```bash
   tgenie db restore --in backup.sql
   ```
3. Fix the migration file
4. Try again

### Database Locked

If you see "database is locked" errors:

1. Ensure no other processes are using the database
2. Check for stale lock files (`.db-shm`, `.db-wal`)
3. Restart the application

### Foreign Key Errors

Foreign keys are enabled automatically. If you see foreign key constraint errors:

1. Check that referenced records exist
2. Verify foreign key relationships in models
3. Ensure migrations are applied in order

## Best Practices

1. **Always backup before migrations** in production
2. **Test migrations** in development first
3. **Review auto-generated migrations** before applying
4. **Keep migrations small** and focused on one change
5. **Document breaking changes** in migration messages
6. **Use transactions** for data migrations when possible

## Examples

### Example: Adding a New Field

1. Add field to model (`backend/models/task.py`):
   ```python
   category: Mapped[str | None] = mapped_column(String(50), nullable=True)
   ```

2. Create migration:
   ```bash
   tgenie db revision -m "Add category field to tasks" --autogenerate
   ```

3. Review and apply:
   ```bash
   tgenie db upgrade
   ```

### Example: Backup Before Update

```bash
# Create backup
tgenie db dump --out backup_$(date +%Y%m%d_%H%M%S).sql

# Upgrade
tgenie db upgrade

# If something goes wrong, restore
tgenie db restore --in backup_20250130_120000.sql
```

## See Also

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLite ALTER TABLE Limitations](https://www.sqlite.org/lang_altertable.html)
- `docs/01-design/DESIGN_DATA.md` - Database schema design
