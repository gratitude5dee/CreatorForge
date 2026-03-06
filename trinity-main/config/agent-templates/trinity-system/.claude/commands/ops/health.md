# Health Check Report

Perform a health check on all agents and identify any issues.

## Instructions

1. **Get all agents** using `mcp__trinity__list_agents`

2. **For each running agent, check**:
   - Container status (should be "running")
   - Context usage (warn if >90%, critical if >95%)
   - Last activity timestamp (warn if >30 minutes ago for running agents)

3. **Classify each agent's health**:
   - **Healthy**: Running, context <75%, recent activity
   - **Warning**: Context 75-90%, or idle >30 minutes
   - **Critical**: Context >90%, container errors, or stuck

4. **Generate a health report** with sections:

```
## Agent Health Report
Generated: {timestamp}

### Overall Health
{Overall status: Healthy / Degraded / Critical}

### Critical Issues (Immediate Attention Required)
{List any critical issues, or "None"}

### Warnings
{List any warnings, or "None"}

### Healthy Agents
{Count of healthy agents}

### Detailed Status

| Agent | Health | Issue | Recommendation |
|-------|--------|-------|----------------|
| ... | ... | ... | ... |
```

## Health Criteria

| Condition | Level | Action |
|-----------|-------|--------|
| Context >95% | Critical | Suggest session reset |
| Context 90-95% | Warning | Monitor closely |
| Context 75-90% | Warning | Consider reset soon |
| Container not running | Critical | Restart if expected to run |
| No activity >30 min (running) | Warning | Check if stuck |
| No activity >60 min (running) | Critical | Likely stuck, restart |

## Save Report

After generating the report:

1. Create directory if needed: `mkdir -p ~/reports/health`
2. Save with timestamp: `~/reports/health/YYYY-MM-DD_HHMM.md`
3. Confirm: "Report saved to ~/reports/health/YYYY-MM-DD_HHMM.md"

## Notes

- Skip trinity-system (yourself) from health checks
- Focus on actionable issues, not just status
- Provide specific recommendations for each issue
