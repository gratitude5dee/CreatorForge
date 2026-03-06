# Restart All Agents

Restart all agents in the fleet. Use with caution!

## Instructions

1. **Confirm the action** - This is a significant operation

2. **Get all agents** using `mcp__trinity__list_agents`

3. **Filter to running agents** (no point restarting stopped ones)

4. **Exclude trinity-system** (yourself - never restart yourself)

5. **For each agent**:
   - Stop the agent
   - Wait 2 seconds
   - Start the agent
   - Record success/failure

6. **Report results**:

```
## Fleet Restart Report
Generated: {timestamp}

### Summary
- Agents Restarted: X
- Successful: X
- Failed: X
- Skipped (stopped): X

### Results

| Agent | Previous | Stop | Start | Final |
|-------|----------|------|-------|-------|
| ... | running | OK | OK | running |
| ... | running | OK | FAIL | stopped |

### Failures
{Details of any failures}

### Notes
- Trinity-system was skipped (cannot restart self)
- {Any other notes}
```

## Warning

This operation will:
- Interrupt any active chat sessions
- Briefly make agents unavailable
- NOT reset context (context persists across restarts)

Only use this for:
- Platform maintenance
- After configuration changes
- When multiple agents are stuck
