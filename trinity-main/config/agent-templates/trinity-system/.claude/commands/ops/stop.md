# Stop Agent

Stop a specific agent.

## Usage

```
/ops/stop <agent-name>
```

## Instructions

1. **Validate the agent name** - Check it exists using `mcp__trinity__get_agent`

2. **Check current status**:
   - If already stopped, report that no action is needed
   - If running, proceed to stop

3. **Stop the agent** using `mcp__trinity__stop_agent`

4. **Verify the stop**:
   - Confirm agent status is "stopped"

5. **Report the result**:

```
## Agent Stop: {agent-name}

**Previous Status**: {running/stopped}
**Stop Result**: {success/already stopped}
**Final Status**: {stopped}

{Any notes}
```

## Safety Checks

- Do NOT stop trinity-system (yourself)
- If agent is in the middle of a task, warn that it will be interrupted
- Report any errors clearly

## Arguments

The agent name should be provided after the command. For example:
- `/ops/stop research-agent`
- `/ops/stop content-production-writer`
