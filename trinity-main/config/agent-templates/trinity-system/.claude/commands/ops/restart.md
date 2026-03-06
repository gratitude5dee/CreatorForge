# Restart Agent

Restart a specific agent by stopping and starting it.

## Usage

```
/ops/restart <agent-name>
```

## Instructions

1. **Validate the agent name** - Check it exists using `mcp__trinity__get_agent`

2. **Check current status** - Is it running, stopped, or in error state?

3. **If running**:
   - Stop the agent using `mcp__trinity__stop_agent`
   - Wait 2-3 seconds for clean shutdown
   - Verify it stopped

4. **Start the agent** using `mcp__trinity__start_agent`

5. **Verify the restart**:
   - Check agent is running
   - Confirm agent server is responding

6. **Report the result**:

```
## Agent Restart: {agent-name}

**Previous Status**: {running/stopped}
**Stop Result**: {success/failed}
**Start Result**: {success/failed}
**Final Status**: {running/stopped}

{Any notes or warnings}
```

## Safety Checks

- Do NOT restart trinity-system (yourself)
- If agent was stopped, just start it (no need to stop first)
- If restart fails, report the error clearly
- If agent has high context, note that restart will NOT reset context

## Arguments

The agent name should be provided after the command. For example:
- `/ops/restart research-agent`
- `/ops/restart content-production-writer`
