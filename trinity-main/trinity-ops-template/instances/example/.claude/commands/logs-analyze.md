---
description: Analyze Trinity logs for errors and issues
allowed-tools: Bash
---

# Analyze Trinity Logs

Run the log analysis script to identify issues:

## Available Modes

```bash
# Overview of all log activity
./scripts/analyze-logs.sh summary

# Show recent errors only
./scripts/analyze-logs.sh errors

# Show recent warnings
./scripts/analyze-logs.sh warnings

# Authentication events (logins, failures)
./scripts/analyze-logs.sh auth

# Agent-specific activity
./scripts/analyze-logs.sh agents

# Timeline view of events
./scripts/analyze-logs.sh timeline

# Container health and restarts
./scripts/analyze-logs.sh containers
```

## Custom Line Count

Analyze more or fewer lines:

```bash
# Analyze last 5000 lines
./scripts/analyze-logs.sh errors 5000

# Analyze last 100 lines
./scripts/analyze-logs.sh summary 100
```

## What to Look For

1. **Errors**: Any error messages that indicate failures
2. **Auth failures**: Failed login attempts
3. **Container restarts**: Services that are unstable
4. **Agent errors**: Problems with specific agents

Report findings with:
- Number of errors/warnings found
- Most common error types
- Recommendations for resolution
