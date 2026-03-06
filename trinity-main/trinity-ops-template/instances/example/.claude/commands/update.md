---
description: Update Trinity - backup, pull, rebuild, restart, verify
allowed-tools: Bash, Read
---

# Update Trinity Instance

Run the update procedure to deploy the latest Trinity version.

## Steps

1. **Run the update script:**
   ```bash
   # Update this path to match your trinity-ops location
   ./scripts/update.sh
   ```

2. **Wait for completion** - The script will:
   - Check current version and fetch updates
   - Backup database to `~/backups/`
   - Pull latest code (handles local changes with stash)
   - Rebuild Docker images (backend, frontend, mcp-server)
   - Restart services (preserves agent containers)
   - Verify health of all components
   - Show agent status

3. **Report results to user:**
   - Previous version → New version
   - Backup file location
   - Health status of all services
   - Any errors or warnings

## If Update Fails

Check the error output and either:
- Fix the issue and re-run
- Run rollback: `./scripts/rollback.sh <backup-file> <commit>`

## Post-Update Verification

After successful update, optionally verify:
- Web UI accessible (start tunnel first if needed)
- Agents still running
- Scheduled tasks intact
