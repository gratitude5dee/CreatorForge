---
description: View and analyze Trinity logs
allowed-tools: Bash
---

# View Trinity Logs

## Quick Log Analysis

Run the log analysis script with different modes:

```bash
# Summary of log activity
./scripts/analyze-logs.sh summary

# Recent errors
./scripts/analyze-logs.sh errors

# Recent warnings
./scripts/analyze-logs.sh warnings

# Authentication events
./scripts/analyze-logs.sh auth

# Agent-specific logs
./scripts/analyze-logs.sh agents

# Timeline of events
./scripts/analyze-logs.sh timeline

# Container status
./scripts/analyze-logs.sh containers
```

## Direct Log Access

For specific container logs:

```bash
source .env

# Backend logs
sshpass -p "$SSH_PASSWORD" ssh $SSH_USER@$SSH_HOST \
  "echo '$SSH_PASSWORD' | sudo -S docker logs trinity-backend --tail 100"

# Agent logs
sshpass -p "$SSH_PASSWORD" ssh $SSH_USER@$SSH_HOST \
  "echo '$SSH_PASSWORD' | sudo -S docker logs agent-{name} --tail 100"
```

Report the findings clearly, highlighting any errors or issues that need attention.
