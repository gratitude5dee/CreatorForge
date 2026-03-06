# List Executions

List recent task executions across all agents.

## Arguments

- `<agent-name>` (optional) - Only show executions for this agent
- `<hours>` (optional, default: 24) - Time window in hours

## Instructions

### List All Recent Executions

Get execution statistics for all agents in the last 24 hours:

```bash
curl -s "http://backend:8000/api/agents/stats?hours=24" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | jq
```

### List Executions for Specific Agent

```bash
curl -s "http://backend:8000/api/agents/{agent-name}/executions?limit=50" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | jq
```

## Response Format

The stats endpoint returns per-agent aggregates:
```json
{
  "agents": [
    {
      "name": "my-agent",
      "task_count_24h": 15,
      "success_count": 14,
      "failed_count": 1,
      "running_count": 0,
      "success_rate": 93.3,
      "total_cost": 0.0542,
      "last_execution_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

## Report Format

```
## Execution Summary
Generated: {timestamp}
Time Window: Last {hours} hours

### Platform Totals
- Total Executions: {sum of task_count}
- Success Rate: {weighted average}%
- Total Cost: ${sum of total_cost}

### By Agent
| Agent | Tasks | Success | Failed | Running | Rate | Cost |
|-------|-------|---------|--------|---------|------|------|
| {name} | {count} | {success} | {failed} | {running} | {rate}% | ${cost} |

### Recent Failures
{List agents with failed_count > 0 and their last failure details}

### Recommendations
- Agents with low success rates may need investigation
- High running counts may indicate stuck tasks
- Check `/ops/executions/status {execution_id}` for failure details
```

## Use Cases

1. **Daily Review**: Check platform activity and success rates
2. **Cost Tracking**: Monitor execution costs by agent
3. **Failure Detection**: Identify agents with recent failures
4. **Capacity Planning**: Understand execution patterns

## Save Report

After generating the report:

1. Create directory if needed: `mkdir -p ~/reports/executions`
2. Save with timestamp: `~/reports/executions/YYYY-MM-DD_HHMM.md`
3. Confirm: "Report saved to ~/reports/executions/YYYY-MM-DD_HHMM.md"

## Notes

- Execution history is retained for auditing
- Running status indicates task is currently executing
- Cost values require OpenTelemetry to be enabled
