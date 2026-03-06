---
description: Start SSH tunnel to access Trinity services locally
allowed-tools: Bash
---

# Start SSH Tunnel

Create SSH tunnels to access remote Trinity services from your local machine.

## Start Tunnel

```bash
./scripts/tunnel.sh &
```

This creates tunnels based on your `.env` configuration:
- Frontend: `http://localhost:$TUNNEL_FRONTEND`
- Backend API: `http://localhost:$TUNNEL_BACKEND`
- MCP Server: `http://localhost:$TUNNEL_MCP`

## Access Services

Once the tunnel is running:
- Web UI: Open `http://localhost:11030` (or your configured port)
- API Docs: `http://localhost:11080/docs`
- MCP: `http://localhost:11085/mcp`

## Stop Tunnel

```bash
# Kill tunnel process
pkill -f "ssh.*$SSH_HOST.*-L"
```

## Troubleshooting

If tunnel fails:
1. Check SSH connectivity: `ssh $SSH_USER@$SSH_HOST`
2. Verify ports aren't in use locally
3. Check firewall rules on remote server

Report the tunnel URLs to the user so they know where to access services.
