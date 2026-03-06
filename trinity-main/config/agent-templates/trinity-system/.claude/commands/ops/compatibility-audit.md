# Compatibility Audit

Audit all agents for Trinity compatibility by requesting self-diagnostics from each agent.

## Instructions

1. **List all agents** using `mcp__trinity__list_agents`

2. **Filter to running agents** (skip stopped agents and trinity-system)

3. **For each running agent**, call it using `mcp__trinity__chat_with_agent` with this prompt:

```
Run a Trinity compatibility self-diagnostic. Check your workspace for:

1. **Required Files**:
   - template.yaml (with name, display_name, description, resources)
   - CLAUDE.md (agent instructions)
   - .gitignore (excludes .mcp.json, .env, content/)

2. **Optional Files**:
   - .mcp.json.template (if using MCP servers)
   - .env.example (credential documentation)
   - dashboard.yaml (agent dashboard)

3. **Security**:
   - No secrets in committed files
   - .env and .mcp.json are gitignored

4. **Structure**:
   - content/ directory for large assets (if needed)
   - Proper .claude/ directory structure

Respond with a brief JSON report:
{
  "agent": "your-name",
  "compatible": true/false,
  "score": "X/10",
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2"]
}
```

4. **Collect all responses** and parse the JSON reports

5. **Generate consolidated report**:

```
## Trinity Compatibility Audit Report
Generated: {timestamp}

### Summary
- Agents Audited: {count}
- Fully Compatible: {count}
- Issues Found: {count}
- Skipped (not running): {count}

### Compatibility Scores

| Agent | Score | Compatible | Issues |
|-------|-------|------------|--------|
| ... | X/10 | Yes/No | {count} |

### Issues by Agent

#### {agent-name}
- **Score**: X/10
- **Issues**:
  - {issue1}
  - {issue2}
- **Recommendations**:
  - {rec1}

### Common Issues
{List issues that appear across multiple agents}

### Recommendations
{Top priority fixes across the fleet}
```

## Save Report

After generating the report:

1. Create directory if needed: `mkdir -p ~/reports/compliance`
2. Save with timestamp: `~/reports/compliance/YYYY-MM-DD_HHMM.md`
3. Confirm: "Report saved to ~/reports/compliance/YYYY-MM-DD_HHMM.md"

## Notes

- Skip `trinity-system` (yourself) - you don't need self-audit
- Skip stopped agents - they can't respond
- Use `parallel=false` for chat calls to avoid overwhelming agents
- If an agent fails to respond or returns invalid JSON, note it as "audit failed"
- Keep individual agent prompts concise to minimize token usage
- Timeout: Allow up to 60 seconds per agent response
