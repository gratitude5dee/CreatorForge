# Service Check

Request each agent to run a self-diagnostic to validate their runtime setup.

> **IMPORTANT**: This is a READ-ONLY service check. Agents must NOT modify any data in external systems. This is purely diagnostic validation.

## Instructions

1. **List all agents** using `mcp__trinity__list_agents`

2. **Filter to running agents** (skip stopped agents and trinity-system)

3. **For each running agent**, call it using `mcp__trinity__chat_with_agent` with this prompt:

```
Run a SERVICE CHECK self-diagnostic. This is READ-ONLY - do NOT modify any external data.

Validate your runtime setup by checking:

1. **MCP Servers**: List configured servers from .mcp.json. For each server:
   - Can you call a read-only/list operation? (e.g., list files, list items, get status)
   - Report: working / failing / not configured

2. **Credentials**: Check .env file exists and has expected variables.
   - Do NOT log credential values
   - Report: present / missing / partially configured

3. **Workspace**: Verify key files exist:
   - CLAUDE.md (your instructions)
   - template.yaml (your config)
   - Any domain-specific required files

4. **Tools**: Test that your core tools respond:
   - File operations (read a test file)
   - Any critical integrations

5. **Memory/State**: Check if persistent files are accessible:
   - memory/ directory (if used)
   - outputs/ directory (if used)

IMPORTANT CONSTRAINTS:
- DO NOT create, update, or delete any external resources
- DO NOT send messages, emails, or notifications
- DO NOT modify databases or APIs
- ONLY perform read/list/get operations
- If a tool only has write operations, skip it and note "write-only, skipped"

Respond with a brief JSON report:
{
  "agent": "your-name",
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "mcp_servers": {"configured": 2, "working": 2, "failed": 0},
    "credentials": "ok|missing|partial",
    "workspace": "ok|issues",
    "tools": "ok|some_failed|not_tested"
  },
  "issues": ["issue1", "issue2"],
  "notes": ["any relevant observations"]
}
```

4. **Collect all responses** and parse the JSON reports

5. **Generate consolidated report**:

```
## Service Check Report
Generated: {timestamp}

### Summary
- Agents Checked: {count}
- Healthy: {count}
- Degraded: {count}
- Unhealthy: {count}
- Skipped (not running): {count}

### Service Status

| Agent | Status | MCP | Creds | Workspace | Issues |
|-------|--------|-----|-------|-----------|--------|
| agent-a | healthy | 2/2 | ok | ok | 0 |
| agent-b | degraded | 1/2 | ok | ok | 1 |
| ... | ... | ... | ... | ... | ... |

### Issues Found

#### {agent-name} (degraded)
- MCP server `slack` not responding
- Recommendation: Check credentials or server status

#### {agent-name} (unhealthy)
- Missing CLAUDE.md
- Credentials file not found
- Recommendation: Reinitialize agent from template

### Healthy Agents
{List of agents with no issues}

### Notes
- This was a READ-ONLY diagnostic check
- No external systems were modified
- For write-operation validation, perform manual testing
```

## Status Classification

| Status | Criteria |
|--------|----------|
| **healthy** | All checks pass, all MCP servers working |
| **degraded** | Some non-critical issues (e.g., 1 MCP server down, optional files missing) |
| **unhealthy** | Critical issues (no credentials, required files missing, all MCP servers down) |

## Save Report

After generating the report:

1. Create directory if needed: `mkdir -p ~/reports/service-checks`
2. Save with timestamp: `~/reports/service-checks/YYYY-MM-DD_HHMM.md`
3. Confirm: "Report saved to ~/reports/service-checks/YYYY-MM-DD_HHMM.md"

## Notes

- Skip `trinity-system` (yourself) from checks
- Skip stopped agents - they can't run diagnostics
- Use `parallel=false` for chat calls to avoid overwhelming agents
- If an agent fails to respond, mark as "check failed" with timeout note
- Timeout: Allow up to 90 seconds per agent (MCP server checks can be slow)
- This check is safe to run frequently - it performs no mutations
