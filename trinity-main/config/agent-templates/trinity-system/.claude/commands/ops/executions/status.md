# Execution Status

Get detailed status of a specific execution.

## Arguments

- `<execution-id>` (required) - The execution ID to check

## Instructions

### Get Execution Details

```bash
curl -s "http://backend:8000/api/schedules/executions/{execution-id}" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | jq
```

Note: You may need to find the execution ID first using `/ops/executions/list`.

### Alternative: Get via Agent Executions

```bash
curl -s "http://backend:8000/api/agents/{agent-name}/executions?limit=10" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | jq
```

## Response Format

```json
{
  "id": "abc123",
  "schedule_id": "sched_xyz",
  "agent_name": "my-agent",
  "status": "success|failed|running",
  "started_at": "2025-01-15T10:00:00Z",
  "completed_at": "2025-01-15T10:02:30Z",
  "duration_ms": 150000,
  "message": "The task prompt that was sent",
  "response": "The agent's response (truncated)",
  "error": "Error message if failed",
  "triggered_by": "schedule|manual|api",
  "context_used": 45000,
  "context_max": 200000,
  "cost": 0.0034,
  "tool_calls": "[{\"name\": \"Read\", \"count\": 5}]"
}
```

## Report Format

```
## Execution Details
ID: {execution_id}

### Overview
- Agent: {agent_name}
- Status: {status}
- Triggered By: {triggered_by}
- Duration: {duration formatted}

### Timing
- Started: {started_at}
- Completed: {completed_at}

### Task
Message: {message}

### Result
{If success: response summary}
{If failed: error details}

### Resource Usage
- Context: {context_used}/{context_max} ({percentage}%)
- Cost: ${cost}
- Tool Calls: {parsed tool_calls summary}

### Recommendations
{Based on status and resource usage}
```

## Use Cases

1. **Failure Investigation**: Understand why a scheduled task failed
2. **Performance Analysis**: Check duration and resource usage
3. **Cost Attribution**: See cost for specific executions
4. **Debugging**: Review tool calls and context usage

## Notes

- `__manual__` as schedule_id indicates a manual/API-triggered task
- `execution_log` may contain full Claude Code transcript (JSON)
- Context usage near max indicates session may need reset
