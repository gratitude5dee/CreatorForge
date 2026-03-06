---
description: Rollback Trinity to a previous version
allowed-tools: Bash
---

# Rollback Trinity Instance

Use this command when you need to revert to a previous version after a failed update.

## Usage

```bash
./scripts/rollback.sh <backup-file> <git-commit>
```

## Steps

1. **List available backups and commits:**
   ```bash
   ./scripts/rollback.sh
   ```
   This shows available backup files and recent git commits.

2. **Execute rollback:**
   ```bash
   ./scripts/rollback.sh trinity-20260108-143022.db f6bb57f
   ```

3. **The script will:**
   - Verify the backup exists
   - Stop Trinity services
   - Save current state as a pre-rollback backup
   - Restore the specified database backup
   - Checkout the specified git commit
   - Rebuild Docker images
   - Restart services
   - Verify health

4. **After rollback:**
   - Test the application
   - When stable, return to main: `git checkout main`

## When to Use

- After a failed update
- When a new version has critical bugs
- When database migration caused issues

Report the rollback results clearly, including the version rolled back to and health status.
