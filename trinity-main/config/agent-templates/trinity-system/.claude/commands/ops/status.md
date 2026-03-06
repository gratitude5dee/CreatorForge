# Fleet Status Report

Generate a comprehensive status report for all agents in the Trinity platform.

## Instructions

1. **Get all agents** using `mcp__trinity__list_agents`

2. **For each agent, collect**:
   - Name and type
   - Status (running/stopped/error)
   - Context usage percentage (if available)
   - Last activity timestamp (if available)
   - System flag (is this the system agent?)

3. **Generate a markdown table** with columns:
   | Agent | Type | Status | Context | Last Activity |

4. **Add summary statistics**:
   - Total agents
   - Running agents
   - Stopped agents
   - Agents with high context (>75%)

5. **Format the report** like this:

```
## Fleet Status Report
Generated: {timestamp}

### Summary
- Total Agents: X
- Running: X
- Stopped: X
- High Context (>75%): X

### Agent Status

| Agent | Type | Status | Context | Last Activity |
|-------|------|--------|---------|---------------|
| ... | ... | ... | ... | ... |

### Notes
- {Any warnings or issues detected}
```

## Save Report

After generating the report:

1. Create directory if needed: `mkdir -p ~/reports/fleet`
2. Save with timestamp: `~/reports/fleet/YYYY-MM-DD_HHMM.md`
3. Confirm: "Report saved to ~/reports/fleet/YYYY-MM-DD_HHMM.md"

## Notes

- Skip the trinity-system agent from health checks (that's you!)
- Sort agents by status (running first, then stopped)
- Mark system agents with a badge
- Highlight any agents with context >90% as warnings
