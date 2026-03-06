# Pause Schedules

Pause one or more schedules to temporarily stop automated executions.

## Arguments

- `<agent-name>` (optional) - Only pause schedules for this agent
- `all` - Pause all schedules across all agents

## Instructions

### Pause All Schedules for an Agent

```bash
curl -X POST "http://backend:8000/api/ops/schedules/pause?agent_name={agent-name}" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

### Pause All Schedules (Platform-wide)

```bash
curl -X POST "http://backend:8000/api/ops/schedules/pause" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

## Response

The API returns:
```json
{
  "success": true,
  "message": "Paused X schedule(s)",
  "paused_count": X,
  "agent_filter": "agent-name or null"
}
```

## Report Format

```
## Schedules Paused
Timestamp: {timestamp}

Action: Paused {paused_count} schedule(s)
Scope: {agent_name or "All agents"}

### What This Means
- Paused schedules will NOT execute automatically
- Schedules remain configured and can be resumed
- Manual executions still possible via UI/API

### To Resume
Use `/ops/schedules/resume` or `/ops/schedules/resume {agent-name}`
```

## Use Cases

1. **Maintenance Window**: Pause all schedules before system updates
2. **Cost Control**: Stop automated tasks during cost review
3. **Debugging**: Pause specific agent's schedules while investigating issues
4. **Incident Response**: Quick way to halt all automation

## Caution

- This is an admin operation
- Does not affect currently running tasks
- Use `/ops/schedules/list` to verify which schedules are affected
