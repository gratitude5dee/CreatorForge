---
description: Run comprehensive health check on Trinity instance
allowed-tools: Bash
---

# Health Check Trinity Instance

Run the comprehensive health check script:

```bash
# Update this path to match your trinity-ops location
./scripts/health-check.sh
```

This checks:
1. **Service Health** - Backend, Frontend, Redis, MCP, Vector
2. **Container Status** - All platform and agent containers
3. **Resource Usage** - Disk, Docker, log sizes
4. **Error Analysis** - Platform and agent error counts
5. **Fleet Health** - Agent context usage and issues

Report the results clearly to the user, highlighting any issues or warnings.
