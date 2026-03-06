# List Schedules

List all schedules across all agents with detailed status information.

## Instructions

1. **Call the API** to get all schedules:

```bash
curl -s "http://backend:8000/api/ops/schedules" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY" | jq
```

2. **Parse the response** which includes:
   - `summary`: Total counts (enabled, disabled, agents with schedules)
   - `schedules`: Array of schedule objects with:
     - `id`, `name`, `agent_name`
     - `cron_expression` - The schedule pattern
     - `enabled` - Whether actively running
     - `next_run_at` - When it will next execute
     - `last_run_at` - When it last ran
     - `last_execution` - Details of most recent run (status, duration, error)

3. **Generate a formatted report**:

```
## Schedule Overview
Generated: {timestamp}

### Summary
- Total Schedules: {total}
- Enabled: {enabled}
- Disabled: {disabled}
- Agents with Schedules: {agents_with_schedules}

### Schedules by Agent

#### {agent_name}
| Schedule | Cron | Status | Next Run | Last Run | Last Status |
|----------|------|--------|----------|----------|-------------|
| {name} | {cron} | {enabled/disabled} | {next_run_at} | {last_run_at} | {success/failed} |

### Warnings
- Schedules on stopped agents will not execute
- Disabled schedules are paused until re-enabled
```

## Optional Filters

You can filter by agent:
```bash
curl -s "http://backend:8000/api/ops/schedules?agent_name=my-agent" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

Or only show enabled schedules:
```bash
curl -s "http://backend:8000/api/ops/schedules?enabled_only=true" \
  -H "Authorization: Bearer $TRINITY_MCP_API_KEY"
```

## Save Report

After generating the report:

1. Create directory if needed: `mkdir -p ~/reports/schedules`
2. Save with timestamp: `~/reports/schedules/YYYY-MM-DD_HHMM.md`
3. Confirm: "Report saved to ~/reports/schedules/YYYY-MM-DD_HHMM.md"

## Notes

- Schedules with `last_execution.error` indicate failures
- `next_run_at` being null means the schedule is disabled or cron is invalid
- Check if agent is running before expecting schedule execution
