# Resume Schedules

Resume previously paused schedules to restore automated executions.

## Arguments

- `<agent-name>` (optional) - Only resume schedules for this agent
- `all` - Resume all disabled schedules across all agents

## Instructions

### Resume All Schedules for an Agent

```bash
curl -X POST "http://backend:8000/api/ops/schedules/resume?agent_name={agent-name}" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

### Resume All Schedules (Platform-wide)

```bash
curl -X POST "http://backend:8000/api/ops/schedules/resume" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

## Response

The API returns:
```json
{
  "success": true,
  "message": "Resumed X schedule(s)",
  "resumed_count": X,
  "agent_filter": "agent-name or null"
}
```

## Report Format

```
## Schedules Resumed
Timestamp: {timestamp}

Action: Resumed {resumed_count} schedule(s)
Scope: {agent_name or "All agents"}

### What This Means
- Resumed schedules will execute according to their cron patterns
- Next execution times have been recalculated
- All automation restored to normal operation

### Verification
Use `/ops/schedules/list` to confirm schedules are enabled
```

## Use Cases

1. **Post-Maintenance**: Resume schedules after system updates complete
2. **Issue Resolved**: Re-enable automation after debugging
3. **Selective Resume**: Only resume specific agent's schedules

## Notes

- Only resumes schedules that were previously enabled
- Does not affect schedules that were manually disabled by users
- Agent must be running for schedules to actually execute
