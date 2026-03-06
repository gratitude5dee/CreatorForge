---
description: Check Trinity instance status - containers, health, version
allowed-tools: Bash
---

# Check Trinity Instance Status

Run the status script to check the health of the Trinity instance:

```bash
# Update this path to match your trinity-ops location
./scripts/status.sh
```

This will show:
- Docker container status (trinity-* and agent-*)
- Health check results (backend, frontend, redis)
- Current git version

Report the results clearly to the user.
