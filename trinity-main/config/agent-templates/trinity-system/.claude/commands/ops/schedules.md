# Schedule Overview

Quick overview of all schedules across the platform.

## Instructions

1. **Get schedule summary** using the API:

```bash
curl -s "http://backend:8000/api/ops/schedules" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | jq '.summary'
```

2. **Generate a brief report**:

```
## Schedule Overview
Generated: {timestamp}

- Total Schedules: {total}
- Enabled: {enabled}
- Disabled: {disabled}
- Agents with Schedules: {agents_with_schedules}

For detailed information, use:
- `/ops/schedules/list` - Full schedule listing
- `/ops/schedules/pause` - Pause schedules
- `/ops/schedules/resume` - Resume schedules
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/ops/schedules/list` | Detailed schedule listing with execution history |
| `/ops/schedules/pause [agent]` | Pause all or agent-specific schedules |
| `/ops/schedules/resume [agent]` | Resume paused schedules |
| `/ops/executions/list` | View recent task executions |
| `/ops/executions/status <id>` | Get details of specific execution |

## Quick Actions

**Check if any schedules are failing:**
```bash
curl -s "http://backend:8000/api/ops/schedules" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | \
  jq '.schedules[] | select(.last_execution.status == "failed")'
```

**Emergency pause all:**
```bash
curl -X POST "http://backend:8000/api/ops/schedules/pause" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```
